__path__ = __import__("pkgutil").extend_path(__path__, __name__)

from man.arcticdb.import_utils import is_arcticdb_enabled as _is_arcticdb_enabled
from man.arcticdb.import_utils import ARCTICCXX_RENAMER

if _is_arcticdb_enabled():
    IS_ARCTICDB_EXT_ENABLED = True
    import sys as _sys

    from arcticdb_ext import *  # KEEP ME, so that from arcticcxx import blah works

    _sys.meta_path.insert(0, ARCTICCXX_RENAMER)
else:
    IS_ARCTICDB_EXT_ENABLED = False
