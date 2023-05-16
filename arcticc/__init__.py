__path__ = __import__("pkgutil").extend_path(__path__, __name__)

from man.arcticdb.import_utils import is_arcticdb_enabled as _is_rewriting_enabled

if _is_rewriting_enabled():
    import sys as _sys
    from man.arcticdb.import_utils import PatcherFinder as _PatcherFinder

    from arcticdb import *  # KEEP ME, so that from arcticc import blah works
    import man.arcticdb.python_exceptions as exceptions
    import man.arcticdb.config as config

    _sys.meta_path.insert(
        0,
        _PatcherFinder(
            old_name="arcticc",
            new_name="arcticdb",
            exclusions=("arcticc.pb2",),
            explicit_mappings={
                "arcticc.config": "man.arcticdb.config",
                "arcticc.exceptions": "man.arcticdb.python_exceptions",
                "arcticc.mongo_config_helper": "man.arcticdb.mongo_config_helper",
                "arcticc.toolbox.config": "man.arcticdb.mongo_config_helper",
                "arcticc.toolbox.storage": "man.arcticdb.toolbox.storage",
                "arcticc.version_store": "man.arcticdb.version_store",
                "arcticc.version_store.helper": "man.arcticdb.version_store.helper",
                "arcticc.pb_util": "man.arcticdb.pb_util",
            },
        ),
    )
