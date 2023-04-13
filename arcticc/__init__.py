__path__ = __import__('pkgutil').extend_path(__path__, __name__)

import sys
import importlib
from dataclasses import dataclass


# Patch imports containing "old-style" references to arcticc to the Github repo ArcticDB
# This is because some naming changed as part of open-sourcing for cosmetic reasons.
# arcticc -> arcticdb


@dataclass
class PatcherLoader:
    old_path: str
    new_path: str

    def load_module(self, fullname):
        try:
            return sys.modules[fullname]
        except KeyError:
            pass
        patched_fullname = fullname.replace(self.old_path, self.new_path)
        try:
            m = importlib.import_module(patched_fullname)
        except Exception as e:
            # Re-raise, but replace any references to man.security_master with man.codex
            raise type(e)(str(e).replace(self.new_path, self.old_path))
        sys.modules[fullname] = m
        return m


class PatcherFinder:
    def find_module(self, fullname, path=None):
        if "arcticc" in fullname and "arcticcxx" not in fullname:
            return PatcherLoader(old_path="arcticc", new_path="arcticdb")
        return None


# Add the custom importer to the meta_path
sys.meta_path.append(PatcherFinder())

