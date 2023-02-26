import re
import glob
from typing import Set, Dict, DefaultDict, List, Pattern


class Run:
    def __init__(self, start: int):
        self.start = self.end = start

    def __repr__(self):
        return str(self.start) if self.start == self.end else f"*range({self.start}, {self.end + 1})"


class RunEncoder(List[Run]):
    def add(self, i: int):
        if len(self) == 0 or self[-1].end + 1 != i:
            self.append(Run(i))
        else:
            self[-1].end = i


class RunEncoderVerifyMode:
    def __init__(self):
        self.re = RunEncoder()
        self.check = []

    def add(self, i: int):
        self.re.add(i)
        self.check.append(i)

    def __repr__(self):
        expr = str(self.re)
        assert eval(expr) == self.check, f"{expr} != {self.check}"
        return expr


_LIB_NAME = re.compile("([^ ]+) in")
_KEY = re.compile(r"(?P<sym>.*):(?P<ver>\d+):0x[0-9a-f]+@")


def find(regex: Pattern, line: str, prefix: str, start: int):
    start = line.find(prefix, start)
    if start < 0:
        return None
    match = regex.match(line, start + len(prefix))
    assert match, "Bad log line: " + line
    return match


_SymVersDict = DefaultDict[str, List[RunEncoder]]
lib_sym_vers = DefaultDict[str, _SymVersDict](lambda: _SymVersDict(RunEncoderVerifyMode))


def parse(path):
    print("Parsing", path)
    higher_data: Set[str] = set()

    with open(path, "r") as f:
        for lno, line in enumerate(f):
            if lno % 100 == 0:
                print("\r", "Line", lno, end="")

            match = find(_LIB_NAME, line, "ReachabilityFailure for ", 44)
            if match:
                lib_name = match.group(1)
                msg_start = match.end() + 60

                match = find(_KEY, line, "Index has higher version data key d:", msg_start)
                if match:
                    higher_data.add(match.group("sym"))
                    continue

                match = find(_KEY, line, "Corrupted/missing index i:", msg_start)
                if match:
                    sym, ver = match.group("sym", "ver")
                    if sym in higher_data:
                        higher_data.remove(sym)
                        lib_sym_vers[lib_name][sym].add(int(ver))
    print("\rDone parsing", path)


for path in glob.glob("/tmp/cronlog*.log"):
    parse(path)

print(
    """

from ahl.mongo import NativeMongoose
from scripts.key_fixers import MongooseCopyDataFixer

nm=NativeMongoose("mktdatad")
"""
)

for lib, sym_vers in lib_sym_vers.items():
    default_dict_str = str(sym_vers)
    sv_str = default_dict_str[default_dict_str.find("{", 43) : -1]  # strip the defaultdict(...)
    print(f"fixer = MongooseCopyDataFixer(nm['{lib}'], dry_run=1)\nfixer.fix_lib_with_undo({sv_str})")
