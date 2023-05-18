from typing import Union

import pandas as pd

from arcticdb.version_store._store import VersionedItem
from arcticdb.version_store._common import TimeFrame
from arcticdb.version_store._normalization import NPDDataFrame


class VersionLoader(object):
    def __init__(self, native_version_store):
        self.native_version_store = native_version_store

    def write_version(self, stream_id: str, dataframe: Union[TimeFrame, pd.DataFrame], version_id, metadata=None):
        vs = self.native_version_store
        proto_cfg = vs._lib_cfg.lib_desc.version.write_options
        dynamic_strings = vs.resolve_defaults("dynamic_strings", proto_cfg, False)
        pickle_on_failure = vs.resolve_defaults("pickle_on_failure", proto_cfg, False)
        udm, item, norm_meta = vs._try_normalize(
            stream_id, dataframe, metadata, pickle_on_failure, dynamic_strings, None
        )

        if isinstance(item, NPDDataFrame):
            vit = self.native_version_store.version_store.write_dataframe_specific_version(
                stream_id, item, norm_meta, udm, version_id
            )
            return VersionedItem(
                symbol=vit.symbol,
                library=self.native_version_store._library.library_path,
                version=vit.version,
                metadata=metadata,
                data=dataframe,
                host=self.native_version_store.env,
            )
