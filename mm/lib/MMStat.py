__version__ = "$Id$"

# Keep statistics -- a counter per key.
# Just put calls to _stat() with a unique argument in your code and
# call _prstats() when the program exits.
# (Once such calls are there, they may also be used to save a trace
# of the program...)
#
_stats = {}
#
def _stat(key):
    if _stats.has_key(key):
        _stats[key] = _stats[key] + 1
    else:
        _stats[key] = 1
#
def _prstats():
    from string import rjust
    print '### Statistics ###'
    list = []
    for key in _stats.keys():
        list.append((_stats[key], key))
    list.sort()
    list.reverse()
    for count, key in list:
        print '#', rjust(`count`, 5), key
