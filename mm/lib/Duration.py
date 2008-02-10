__version__ = "$Id$"

# Get the duration of a node.
# This module knows which channel types need special treatment.

import MMAttrdefs
import ChannelMap
from sys import platform
import urlcache
import string

def getintrinsicduration(node, wanterror):
    if node.GetType() not in ('ext', 'imm'):
        # catch all for brush, prefetch, etc.
        return 0
    url = node.GetFile()
    cache = urlcache.urlcache[url]
    dur = cache.get('duration')
    if dur is not None:
        return dur
    # we hadn't cached the duration, do the hard work
    # first figure out MIME type
    mtype = urlcache.mimetype(url)
    if mtype is None:
        # MIME type can't be found
        return 0
    maintype, subtype = mtype.split('/')
    # now figure out duration depending on type
    if string.find(subtype, 'real') >= 0 or string.find(subtype, 'shockwave') >= 0:
        if platform == 'win32':
            import RealDuration
            try:
                dur = RealDuration.get(url)
            except IOError, msg:
                if wanterror:
                    raise IOError, msg
                if __debug__:
                    print url, msg
                return 0
        else:
            import realsupport
            info = realsupport.getinfo(url)
            dur = info.get('duration', 0)
    elif maintype == 'video':
        import VideoDuration
        try:
            dur = VideoDuration.get(url)
        except IOError, msg:
            if wanterror:
                raise IOError, msg
            if __debug__:
                print url, msg
            return 0
    elif maintype == 'audio':
        import SoundDuration
        try:
            dur = SoundDuration.get(url)
        except IOError, msg:
            if wanterror:
                raise IOError, msg
            if __debug__:
                print url, msg
            return 0
##     elif maintype == 'image' and subtype == 'svg-xml':
##         dur = -1
    elif maintype in ('image', 'text'):
        # static media doesn't have a duration
        dur = 0
    else:
        # unknown object type
        dur = 0
    cache['duration'] = dur
    return dur

def get(node, ignoreloop=0, wanterror=0, ignoredur=0):
    # we try to follow smil-timing.html#Timing-ComputingActiveDur
    # closely (including variable names :-)
    if ignoredur:
        p0 = None
    else:
        p0 = node.GetAttrDef('duration', None)
    if p0 is None:
        p0 = getintrinsicduration(node, wanterror)
        try:
            clipbegin = node.GetClip('clipbegin', 'sec')
        except ValueError:
            clipbegin = 0
        try:
            clipend = node.GetClip('clipend', 'sec')
        except ValueError:
            clipend = 0
        if clipend:
            p0 = min(p0, clipend)
        p0 = max(p0 - clipbegin, 0)
    if ignoreloop:
        repeatCount = None
    else:
        repeatCount = node.GetAttrDef('loop', None)
    if repeatCount is None:
        p1 = -1
    elif repeatCount == 0:
        p1 = -1
    else:
        p1 = p0 * repeatCount
    if ignoreloop:
        repeatDur = None
    else:
        repeatDur = node.GetAttrDef('repeatdur', None)
    if repeatDur is None:
        p2 = -1
    else:
        p2 = repeatDur
    if p0 == 0:
        IAD = 0
    elif repeatCount is None and repeatDur is None:
        IAD = p0
    else:
        # IAD = min(p1, p2, indefinite)
        if p1 < 0:
            IAD = p2
        elif p2 < 0:
            IAD = p1
        else:
            IAD = min(p1, p2)
    return IAD
