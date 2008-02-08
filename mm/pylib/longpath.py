# Convert pathnames containing DOS-compatible bits to NT
# pathnames. The file must exist for this to work.
# Jack Jansen, jack@oratrix.nl
#
# XXXX Does not handle . and .. in pathname

# Check for UNC names (\\server\share\subdirectory\filename)
# and do not call FindFiles against them.

import os
import win32api

def short2longpath(pathname):
    """Convert DOS pathname to full NT pathname."""
    dir, file = os.path.split(pathname)
    if not file:
        return dir
    longfile = _short2longfile(pathname)
    longdir = short2longpath(dir)
    return os.path.join(longdir, longfile)

def _short2longfile(pathname):
    # if we can't figure out the long name, just return the short
    try:
        list = win32api.FindFiles(pathname)
    except:
        list = []
    if not list or len(list) > 1:
        return pathname
    return list[0][8]


# There is a win32 function called 'PathIsUNC' but is
# available only on machines with IE4/5 or on Win2k.
# Here just check the first two chars.
def pathIsUNC(pathname):
    if pathname[0:2]=='\\\\':
        return 1
    else:
        return 0


if __debug__:
    if __name__ == '__main__':
        while 1:
            x = raw_input()
            print short2longpath(x)
