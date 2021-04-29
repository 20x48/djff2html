try:
    from .j import generate, escape
    from .v import __version__
except ImportError:
    from j import generate, escape
    from v import __version__

__author__ = '20x48'