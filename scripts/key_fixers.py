import time
import boto3
import os
import traceback
from typing import Set, Dict, TextIO, Generic, TypeVar, Optional, Callable, Any, Iterable
from difflib import SequenceMatcher
from io import StringIO
from subprocess import run, DEVNULL, PIPE

from arcticc.version_store import NativeVersionStore
from arcticc.pb2.s3_storage_pb2 import Config
from arcticc.pb2.encoding_pb2 import VariantCodec
from arcticc.toolbox.storage import *
from arcticcxx.tools import ReachabilityChecker
from arcticcxx_toolbox.codec import decode_segment, encode_segment


def mem_seg_to_dataframe(msh):
    cols = {f: msh[f] for f in msh.field_names if f != "stream_id"}
    return pd.DataFrame(cols, columns=cols.keys())


_SM = SequenceMatcher(autojunk=False)


def compact_diff(a: str, b: str):  # Bash brace expansion-ish diff string
    _SM.set_seqs(a, b)
    buf = StringIO()
    opcodes = _SM.get_opcodes()
    for tag, i1, i2, j1, j2 in opcodes:
        if tag == "equal":
            buf.write(a[i1:i2])
        else:
            buf.write("{")
            buf.write(a[i1:i2])
            buf.write(",")
            buf.write(b[j1:j2])
            buf.write("}")
    return buf.getvalue()


def open_private_file_for_writing(path: str, *, trunc: bool, mode=0o600, **kwargs):
    desc = os.open(path, flags=os.O_WRONLY | os.O_CREAT | (os.O_TRUNC if trunc else 0), mode=mode)
    return open(desc, "w" if trunc else "a", **kwargs)


class Undo(NamedTuple):
    source: str  # S3 path
    backup: str
    discard_backup: bool  # False = discard source

    _DISCARD_LOOKUP = dict(source=False, backup=True)


FixLibArg = TypeVar("FixLibArg", covariant=True)
ArgForSymbol = TypeVar("ArgForSymbol")


class FixerBase(Generic[FixLibArg]):
    """
    Provides boto3 API and automatic undo facilities for building scripts that manipulates keys.

    The static methods are also useful in other tests/scripts.
    """

    undo_script: Optional[TextIO] = None
    undo_script_name: str
    _undo: List[Undo]

    def __init__(self, lib: NativeVersionStore, dry_run=1):
        self.lib = lib
        self.dry_run = dry_run
        self.lt = get_library_tool(lib)
        self.rc = ReachabilityChecker(lib._library, lambda x: print(x))

        s3_cfg = self.s3_cfg = self.get_primary_store_cfg(lib)
        self.bucket = self.s3_bucket(s3_cfg)
        self._undo = []
        self.undo_script_name = os.path.abspath(self.__class__.__name__ + "_undo.sh")

    # ================ S3 stuff ================
    @staticmethod
    def get_primary_store_cfg(lib: NativeVersionStore):
        stor_cfg = lib.lib_cfg().storage_by_id[lib.lib_cfg().lib_desc.storage_ids[0]].config
        s3_cfg = Config()
        assert stor_cfg.Unpack(s3_cfg)
        return s3_cfg

    @staticmethod
    def s3_bucket(s3_cfg: Config):
        s3 = boto3.resource(
            service_name="s3",
            endpoint_url="http://" + s3_cfg.endpoint,
            aws_access_key_id=s3_cfg.credential_name,
            aws_secret_access_key=s3_cfg.credential_key,
        )
        bucket = s3.Bucket(s3_cfg.bucket_name)
        assert any(bucket.objects.limit(1)), "Empty bucket: " + bucket  # Also checks the creds are valid
        return bucket

    # ================ Undo log ================

    _out = run('s5cmd cp -h | grep -- "--raw"', shell=True, stdout=DEVNULL, stderr=PIPE)
    HAS_S5CMD = _out.returncode == 0 and not _out.stderr
    if not HAS_S5CMD:
        print("s5cmd is missing or too old. The undo script probably won't work on this box.")
    del _out

    def start_undo_script(self):
        s3 = self.s3_cfg
        # Append into the same file
        script = open_private_file_for_writing(self.undo_script_name, trunc=False, mode=0o700, encoding="utf-8")
        script.write(
            f"""#!/bin/bash
            function restore() {{
            S5CMD_VERSION=v2.0.0 AWS_ACCESS_KEY_ID={s3.credential_name} AWS_SECRET_ACCESS_KEY={s3.credential_key} \\
            s5cmd --endpoint-url=http://{s3.endpoint} cp --raw s3://{s3.bucket_name}/{{$1,$2}}
            }}\n"""
        )
        print("Appending to undo script at", self.undo_script_name)
        return script

    def _undo_log(self, *, source: Union[Key, str], backup: Union[Key, str], discard: str):
        """
        Writes the undo script that copies backup to source. However, if the fix_lib call is successful, the parameter
        named by `discard` will be removed.
        """
        source_path = source if isinstance(source, str) else self.lt.get_key_path(source)
        backup_path = backup if isinstance(backup, str) else self.lt.get_key_path(backup)
        self._undo.append(Undo(source_path, backup_path, Undo._DISCARD_LOOKUP[discard]))
        if self.undo_script:
            self._append_undo_script(source_path, backup_path)

    def _append_undo_script(self, source_path: str, backup_path: str):
        self.undo_script.write(f"restore '{backup_path}' '{source_path}'\n")
        self.undo_script.flush()

    def _do_undo(self):
        if self.dry_run == -1 or (self.dry_run == 0 and input("Do you want to attempt automatic undo? [y/N]") == "y"):
            # Only need to restore the undo entries of the backup type because we have not got to "_delete()"
            for undo in self._undo:
                if undo.discard_backup:
                    print("Restoring", undo.source)
                    self.bucket.Object(undo.source).copy({"Bucket": self.bucket.name, "Key": undo.backup})

    def _do_discard(self, override: Iterable[Undo] = None):
        undo = override if override is not None else self._undo
        if self.dry_run <= 0:
            print("Operation success. Deleting backups")
            for batch in range(0, len(undo), 1000):
                objs = [{"Key": k.backup if k.discard_backup else k.source} for k in undo[batch : batch + 1000]]
                self.bucket.delete_objects(Delete={"Objects": objs, "Quiet": False})
        else:
            print("Dry-run. Not deleting backups: ", undo)

    # ================ Business API ================
    def fix_lib(self, arg: FixLibArg):
        """Override to implement the fixing logic"""
        raise NotImplemented

    def fix_lib_with_undo(self, arg: FixLibArg):
        """Wraps `fix_lib()` with undo logging, backup auto-delete and auto undo on exception."""
        self._undo.clear()
        try:
            with self.start_undo_script() as self.undo_script:
                self.fix_lib(arg)
        except:
            traceback.print_exc()
            self._do_undo()
            raise KeyboardInterrupt from None  # Terminates scripts but not interactive sessions

        self._do_discard()

    # ================ Primitives for sub-types to use ================
    def backup_segment_before_modification(self, key: Key):
        ks: KeySegmentPair = self.lt.read(key)
        ks.key = ks.key._replace(id=ks.key.id + "_bak")
        self._undo_log(source=key, backup=ks.key, discard="backup")
        self._write(ks)
        return ks.segment

    def _move_data_python(self, src: Key, dst: Key):
        # lt has no move primitive, so we have to copy:
        start = time.time() * 1000
        print("  Copying", compact_diff(str(src), str(dst)), end=": ")
        ksp: KeySegmentPair = self.lt.read(src)
        ksp.key = dst
        print(len(ksp.segment.bytes), end=" bytes in ")
        self._undo_log(source=src, backup=dst, discard="source")
        self._write(ksp)
        print(int(time.time() * 1000 - start))

    def _write(self, ksp: KeySegmentPair):
        if self.dry_run <= 0:
            self.lt.write(ksp)

    def _move_data_boto3(self, src: Key, dst: Key):
        start = time.time() * 1000
        src_path = self.lt.get_key_path(src)
        dst_path = self.lt.get_key_path(dst)
        self._undo_log(source=src_path, backup=dst_path, discard="source")
        print("  Copying", compact_diff(src_path, dst_path), end=": ")
        if self.dry_run <= 0:
            self.bucket.Object(dst_path).copy({"Bucket": self.bucket.name, "Key": src_path})
        else:
            print("would copy ", self.bucket.Object(src_path).content_length, end=" ")
        print("in ", int(time.time() * 1000 - start))

    move_data = _move_data_boto3

    _LZ4 = VariantCodec()  # Needed by encode_segment()
    _LZ4.lz4.acceleration = 1  # Match default_codecs.hpp

    def modify_index_key(self, idx_key: Key, callback: Callable[[Key, MemSegmentHelper], Any], *, move_data):
        """
        Parameters
        ----------
        idx_key
            The key to modify
        callback
            Will be handed the decoded segment of the index key to modify
        move_data
            If true, data keys will be renamed/moved to reflect the changes to the index
        """
        print("Working on", idx_key)
        segment = self.backup_segment_before_modification(idx_key)
        seg_in_mem = decode_segment(segment)
        seg_helper = MemSegmentHelper(segment.header, seg_in_mem)

        if move_data:
            src_data_keys = df_to_keys(idx_key.id, mem_seg_to_dataframe(seg_helper))

        callback(idx_key, seg_helper)

        if move_data:
            dst_data_keys = df_to_keys(idx_key.id, mem_seg_to_dataframe(seg_helper))
            mover = getattr(self, move_data) if isinstance(move_data, str) else self.move_data
            for src, dst in zip(src_data_keys, dst_data_keys):
                if src != dst:
                    mover(src, dst)

        segment = encode_segment(seg_in_mem, self._LZ4)
        self._write(KeySegmentPair(idx_key, segment))


class PerSymbolFixerBase(FixerBase[Dict[str, ArgForSymbol]]):
    """Common pattern where the fix works on a per-symbol basis"""

    def fix_symbol(self, symbol: str, args: ArgForSymbol):
        """Override to implement per-symbol fix logic"""
        raise NotImplemented

    def fix_lib(self, syms_and_args: Dict[str, ArgForSymbol]):
        """
        By default, iterate the argument and call `fix_symbol()`. Then run the ReachabilityChecker to ensure the output
        is valid.

        Can override this if the script doesn't work on a per-symbol basis.
        """
        snapshots: Set[str] = set()
        for sym, args in syms_and_args.items():
            self.fix_symbol(sym, args)
            assert self.rc.walk_version_tree(sym), f"Re-written {sym} is still invalid"
            for v in self.lib.list_versions(sym):
                snapshots.update(v["snapshots"])

        for snap in snapshots:
            assert self.rc.walk_snapshot_tree(snap), f"Snapshot {snap} is still invalid"


class MongooseCopyDataFixer(PerSymbolFixerBase[Set[int]]):
    _KEY_MARKER = 504  # The Jira ID. To make these keys easy to identify

    def fix_symbol(self, symbol: str, versions: Set[int]):
        print(f">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>\nFixing {symbol} versions {versions}")
        idxes: List[Key] = self.lt.find_keys_for_id(KeyType.TABLE_INDEX, symbol)
        for idx_key in idxes:
            if idx_key.version_id in versions:
                self.modify_index_key(idx_key, self._update_idx_key, move_data=True)
                versions.remove(idx_key.version_id)
            else:
                print(f"Not asked to process {idx_key}")
        assert not versions, f"Failed to find {versions} for symbol {symbol}"

    def _update_idx_key(self, idx_key: Key, seg_helper: MemSegmentHelper):
        # Changes via the seg_helper modifies the C++ SegmentInMemory directly:
        seg_helper["version_id"].fill(idx_key.version_id)
        seg_helper["creation_ts"].fill(int(time.time() * 1000) * 1000000 + self._KEY_MARKER)
