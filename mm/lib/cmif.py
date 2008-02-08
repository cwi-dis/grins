__version__ = "$Id$"

# A function to find a file in the "cmif search path".
# This search path is defined as follows:
# - if $CMIFPATH is set, use its colon-separated entries
# - else, if $CMIF is set, use it
# - else, use the built-in default

# WARNING WARNING WARNING WARNING WARNING WARNING WARNING WARNING WARNING
# *********  If you change this, also change ../lib/main.py   ***********
# WARNING WARNING WARNING WARNING WARNING WARNING WARNING WARNING WARNING

cmifpath = None

def findfile(name):
    global cmifpath
    import os
    if os.path.isabs(name):
        return name
    if cmifpath is None:
        if os.environ.has_key('CMIFPATH'):
            import string
            var = os.environ['CMIFPATH']
            cmifpath = string.splitfields(var, ':')
        elif os.environ.has_key('CMIF'):
            cmifpath = [os.environ['CMIF']]
        else:
            import sys
            cmifpath = [os.path.split(sys.executable)[0]]
            try:
                link = os.readlink(sys.executable)
            except (os.error, AttributeError):
                pass
            else:
                cmifpath.append(os.path.dirname(os.path.join(os.path.dirname(sys.executable), link)))
    for dir in cmifpath:
        fullname = os.path.join(dir, name)
        if os.path.exists(fullname):
            return fullname
    return name
