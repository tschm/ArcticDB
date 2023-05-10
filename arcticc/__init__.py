__path__ = __import__("pkgutil").extend_path(__path__, __name__)

import sys as _sys
from man.arcticdb.import_utils import PatcherFinder as _PatcherFinder

from arcticdb import *  # KEEP ME, so that from arcticcxx import blah works

_sys.meta_path.append(_PatcherFinder(old_name="arcticc", new_name="arcticdb", exclusions=("arcticcxx",)))
