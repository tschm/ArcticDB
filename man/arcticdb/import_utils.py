import sys
import importlib


class PatcherFinder(importlib.abc.MetaPathFinder):

    def __init__(self, old_name, new_name, exclusions=tuple()):
        self.old_name = old_name
        self.new_name = new_name
        self.exclusions = exclusions

    def find_module(self, fullname, path=None):
        if self.old_name in fullname and all(e not in fullname for e in self.exclusions):
            return self
        return None

    def load_module(self, fullname):
        try:
            return sys.modules[fullname]
        except KeyError:
            pass
        patched_fullname = fullname.replace(self.old_name, self.new_name)
        try:
            m = importlib.import_module(patched_fullname)
        except Exception as e:
            raise type(e)(str(e).replace(self.new_name, self.old_name))
        sys.modules[fullname] = m

        # ensure single copy of sub-modules
        current_modules = dict(sys.modules)
        for k, v in current_modules.items():
            patched_name = k.replace(patched_fullname, fullname, 1)  # arcticdb.blah -> arcticc.blah
            if patched_name not in current_modules:
                sys.modules[patched_name] = v
        return m
