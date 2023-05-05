__path__ = __import__("pkgutil").extend_path(__path__, __name__)

import sys as _sys
from arcticdb_ext import *
from man.arcticdb.import_utils import PatcherFinder as _PatcherFinder

_sys.meta_path.append(_PatcherFinder(old_name="arcticcxx", new_name="arcticdb_ext"))
