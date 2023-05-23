__path__ = __import__("pkgutil").extend_path(__path__, __name__)

from man.arcticdb.import_utils import is_arcticdb_enabled as _is_rewriting_enabled
from man.arcticdb.import_utils import ARCTICC_RENAMER

if _is_rewriting_enabled():
    IS_ARCTICDB_ENABLED = True
    from arcticdb import *  # KEEP ME, so that from arcticc import blah works

    import sys as _sys

    _sys.meta_path.insert(0, ARCTICC_RENAMER)
else:
    IS_ARCTICDB_ENABLED = False
