import os
import sys
import importlib
from typing import Iterable, Dict


class PatcherFinder(importlib.abc.MetaPathFinder):
    """Rewrites imports by replacing an "old_name" with a "new_name".

    It is important that instances of this finder sit at the head of sys.meta_path in case the "old_name" package is
    also available on a user's path.

    We use this to intercept arcticc imports and redirect them to the new ArcticDB project.

    This is configurable in two ways:

    - Exclusions: Names to exclude entirely from the remapping process
    - Explicit mappings: Explicit replacement of one module with another
    """

    def __init__(
        self, old_name, new_name, exclusions: Iterable[str] = tuple(), explicit_mappings: Dict[str, str] = None
    ):
        self.old_name = old_name
        self.new_name = new_name
        self.exclusions = exclusions
        self.explicit_mappings = dict() if explicit_mappings is None else explicit_mappings

    def __repr__(self):
        return f"PatcherFinder({self.old_name}, {self.new_name}, exclusions={self.exclusions}, explicit_mappings={self.explicit_mappings})"

    def __str__(self):
        return f"PatcherFinder[{self.old_name} -> {self.new_name}]"

    def find_module(self, fullname, path=None):
        if fullname in self.explicit_mappings:
            return self
        if fullname.startswith(self.old_name + ".") and all(e not in fullname for e in self.exclusions):
            return self
        return None

    def load_module(self, fullname):
        try:
            return sys.modules[fullname]
        except KeyError:
            pass

        if fullname in self.explicit_mappings:
            patched_fullname = self.explicit_mappings[fullname]
        else:
            patched_fullname = fullname.replace(self.old_name, self.new_name, 1)

        try:
            m = importlib.import_module(patched_fullname)
        except Exception as e:
            raise type(e)(str(e).replace(self.new_name, self.old_name, 1))

        sys.modules[fullname] = m

        # ensure single copy of sub-modules
        current_modules = dict(sys.modules)
        for k, v in current_modules.items():
            patched_name = k.replace(patched_fullname, fullname, 1)  # arcticdb.blah -> arcticc.blah
            if patched_name not in current_modules:
                sys.modules[patched_name] = v
        return m


ever_printed = False


def is_arcticdb_enabled():
    setting = os.getenv("MAN_ARCTICDB_USE_ARCTICDB", "false")
    print(f'MAN_ARCTICDB_USE_ARCTICDB={os.getenv("MAN_ARCTICDB_USE_ARCTICDB", "")}')
    result = setting.lower() in ("true", "1", "on")
    global ever_printed
    if not ever_printed:
        ever_printed = True
        if result:
            print("Using public ArcticDB. Set env var MAN_ARCTICDB_USE_ARCTICDB=false to use arcticc", file=sys.stderr)
        else:
            print(
                "Using internal arcticc. Set env var MAN_ARCTICDB_USE_ARCTICDB=true to use public ArcticDB",
                file=sys.stderr,
            )
    return result


ARCTICC_RENAMER = PatcherFinder(
    old_name="arcticc",
    new_name="arcticdb",
    exclusions=("arcticc.pb2",),
    explicit_mappings={
        "arcticc.config": "man.arcticdb.config",
        "arcticc.exceptions": "man.arcticdb.python_exceptions",
        "arcticc.mongo_config_helper": "man.arcticdb.mongo_config_helper",
        "arcticc.toolbox.config": "man.arcticdb.mongo_config_helper",
        "arcticc.toolbox": "man.arcticdb.toolbox",
        "arcticc.toolbox.storage": "man.arcticdb.toolbox.storage",
        "arcticc.toolbox.loader": "man.arcticdb.toolbox.loader",
        "arcticc.version_store": "man.arcticdb.version_store",
        "arcticc.version_store.helper": "man.arcticdb.version_store.helper",
        "arcticc.pb_util": "man.arcticdb.pb_util",
    },
)

ARCTICCXX_RENAMER = PatcherFinder(
    old_name="arcticcxx",
    new_name="arcticdb_ext",
    exclusions=(),
    explicit_mappings={"arcticcxx.exceptions": "man.arcticdb.cpp_exceptions"},
)
