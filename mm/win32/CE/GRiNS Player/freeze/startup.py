__version__ = "$Id$"

import sys
sys.path[:] = [r'\Program Files\GRiNS\bin\wince']

# Global Application Objects
if __name__ == '__main__':
    toplevel = None
    resdll = None
else:
    import __main__
    __main__.toplevel = None
    __main__.resdll = None

import grinsNL_CE
