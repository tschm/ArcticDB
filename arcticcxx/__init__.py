__path__ = __import__("pkgutil").extend_path(__path__, __name__)

from man.arcticdb.import_utils import is_arcticdb_enabled as _is_arcticdb_enabled

if _is_arcticdb_enabled():
    import sys as _sys
    from man.arcticdb.import_utils import PatcherFinder as _PatcherFinder

    from arcticdb_ext import *  # KEEP ME, so that from arcticcxx import blah works

    _sys.meta_path.insert(
        0,
        _PatcherFinder(
            old_name="arcticcxx",
            new_name="arcticdb_ext",
            exclusions=(),
            explicit_mappings={"arcticcxx.exceptions": "man.arcticdb.cpp_exceptions"},
        ),
    )
