import imp
import sys

# Copied from: http://docs.python.org/library/imp.html
# One addition: namepath added to function call, and to imp.find_module call

# NOTE: name should be the module name (no .py extension) and namepath must be
#  a list, even if it is only one path.

def __import__(name, namepath, globals=None, locals=None, fromlist=None):
    # Fast path: see if the module has already been imported.
    try:
        return sys.modules[name]
    except KeyError:
        pass

    # If any of the following calls raises an exception,
    # there's a problem we can't handle -- let the caller handle it.

    fp, pathname, description = imp.find_module(name, namepath)

    try:
        return imp.load_module(name, fp, pathname, description)
    finally:
        # Since we may exit via an exception, close fp explicitly.
        if fp:
            fp.close()


