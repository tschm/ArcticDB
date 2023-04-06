try:
    from ahl.pkglib.setuptools import setup
except ImportError:
    print("AHL Package Utilities are not available."
          " Please run \"easy_install ahl.pkglib\"")
    import sys
    sys.exit(1)

if __name__ == "__main__":
    setup()
