__path__ = __import__("pkgutil").extend_path(__path__, __name__)

from arcticdb import *

import sys
import importlib
import importlib.machinery
import importlib.abc
import importlib.util


# Patch imports containing "old-style" references to arcticc to the Github repo ArcticDB
# This is because some naming changed as part of open-sourcing for cosmetic reasons.
# arcticc -> arcticdb


class PatcherLoader(importlib.abc.Loader):

    def __init__(self, old_path: str, new_path: str):
        self.old_path = old_path
        self.new_path = new_path

    def create_module(self, spec):
        try:
            return sys.modules[spec.name]
        except KeyError:
            pass
        m = self._patched_module(spec.name)
        sys.modules[spec.name] = m

        # # ensure single copy of sub-modules
        # current_modules = dict(sys.modules)
        # for k, v in current_modules.items():
        #     patched_name = k.replace(m.__name__, spec.name, 1)  # arcticdb.blah -> arcticc.blah
        #     if m.__name__ not in k or patched_name in current_modules:
        #         continue
        #     sys.modules[patched_name] = v
        return m

    def exec_module(self, module):
        m = self._patched_module(module.__name__)
        assert not isinstance(m.__loader__, PatcherLoader), "Infinite recursion!"
        m.__loader__.exec_module(m)

    def _patched_module(self, name):
        patched_fullname = name.replace(self.old_path, self.new_path, 1)
        try:
            m = importlib.import_module(patched_fullname)
        except Exception as e:
            raise type(e)(str(e).replace(self.new_path, self.old_path, 1))
        return m


class PatcherFinder(importlib.abc.MetaPathFinder):

    def __init__(self, old_path, new_path, exclusions=None):
        if exclusions is None:
            exclusions = []
        self.patcher_loader = PatcherLoader(old_path=old_path, new_path=new_path)
        self.old_name = old_path
        self.new_name = new_path
        self.exclusions = exclusions

    def find_spec(self, fullname, path, target=None):
        if self.old_name in fullname and not any(e in fullname for e in self.exclusions):
            return importlib.util.spec_from_loader(fullname, self.patcher_loader)
        return None


_old_path = "arcticc"
_new_path = "arcticdb"
_exclusions = ("arcticcxx", "arcticdb_ext")

sys.meta_path.append(PatcherFinder(old_path=_old_path, new_path=_new_path, exclusions=_exclusions))
