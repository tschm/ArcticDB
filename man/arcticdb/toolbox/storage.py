class LibraryPath(object):
    @classmethod
    def from_string(cls, str):
        return cls(*str.split("."))

    def __init__(self, *parts):
        self.parts = parts

    def __str__(self):
        return ".".join(["{}".format(v) for v in self.parts])
