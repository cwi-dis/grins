__version__ = "$Id$"

import windowinterface
try:
    import rma
except ImportError:
    # no Real support available
    rma = None
import MMurl
import os
if os.name == 'mac':
    from Carbon import Evt
    NEEDTICKER = 1
elif os.name == 'posix':
    NEEDTICKER = 1
else:
    NEEDTICKER = 0

class error(Exception):
    pass

realenginedebug=0

import settings
import MMAttrdefs

class RealEngine:
    # This class holds the RMA engine and a useage counter. This counter is
    # needed because on the mac (and maybe on unix) whenever any player is active
    # we should periodically pass events to the engine to keep it ticking.
    # XXXX Eventually we should probably also pass redraw events and such.
    def __init__(self):
        self.usagecount = 0
        self.engine = rma.CreateEngine()
        self.__tid = None
        windowinterface.addclosecallback(self.close, ())

    def close(self):
        self.engine = None
        if self.usagecount and NEEDTICKER:
            windowinterface.cancelidleproc(self.__tid)

    def __del__(self):
        self.close()

    def CreatePlayer(self, window, winpossize, windowless):
        if windowless:
            return self.engine.CreatePlayer(0, ((-1,-1),(-1, -1)), 1)
        if window is None:
            return self.engine.CreatePlayer()
        else:
            return self.engine.CreatePlayer(window, winpossize)

    def startusing(self):
        if NEEDTICKER and self.usagecount == 0:
            self._startticker()
        self.usagecount = self.usagecount + 1

    def stopusing(self):
        if self.usagecount <= 0:
            raise error, 'RealEngine usage count <= 0 (internal error).'
        self.usagecount = self.usagecount - 1
        if NEEDTICKER and self.usagecount == 0:
            self._stopticker()

    def _startticker(self):
        self.__tid = windowinterface.setidleproc(self._tick)

    def _stopticker(self):
        windowinterface.cancelidleproc(self.__tid)

    def _tick(self):
        if os.name == 'mac':
            # XXXX Mac-specific
            self.engine.EventOccurred((0, 0, Evt.TickCount(), (0, 0), 0))
        elif os.name == 'posix':
            self.engine.EventOccurred((0, 0, 0, (0, 0), 0))
        else:
            raise error, 'Unknown environment in _tick (internal error).'


class RealChannel:
    __engine = None
    __has_rma_support = rma is not None

    def __init__(self, channel):
        if not self.__has_rma_support:
            raise error, "No RealPlayer playback support in this version."
        self.__channel = channel
        self.__rmaplayer = None
        self.__qid = None
        self.__using_engine = 0
        self.__reporteddur = None

        if self.__engine is None:
            try:
                RealChannel.__engine = RealEngine()
            except:
                RealChannel.__has_rma_support = 0
                raise error, "Cannot initialize RealPlayer playback. RealPlayer installation problem?"

    def destroy(self):
        if self.__qid:
            self.__channel._scheduler.cancel(self.__qid)
        self.__qid = None
        del self.__channel

    def release_player(self):
        if realenginedebug: print 'release_player'
        self.__rmaplayer = None

    def prepare_player(self, node = None):
        if not self.__has_rma_support:
            return 0
        return 1

    def __createplayer(self, node):
        if not self.__has_rma_support:
            return 0
        if self.__rmaplayer is None:
            try:
                self.__rmaplayer = apply(self.__engine.CreatePlayer, self.__winpos)
            except:
                self.__channel.errormsg(node, 'Cannot initialize RealPlayer playback.')
                return 0
        return 1

    def playit(self, node, window = None, winpossize=None, url=None, windowless=0, start_time=0):
        self.__winpos = window, winpossize, windowless
        if not self.__createplayer(node):
            return 0
        duration = self.__channel.getduration(node)
        self.__start_time = start_time
        if url is None:
            url = self.__channel.getfileurl(node)
        if not url:
            self.__channel.errormsg(node, 'No URL set on node.')
            return 0
        url = MMurl.canonURL(url)
        mediarepeat = MMAttrdefs.getattr(node, 'mediaRepeat')
        if mediarepeat != 'preserve': # i.e. mediarepeat=='strip'
            if '?' in url:
                url = url + '&mediaRepeat=%s' % mediarepeat
            else:
                url = url + '?mediaRepeat=%s' % mediarepeat
##         try:
##             u = MMurl.urlopen(url)
##         except:
##             self.errormsg(node, 'Cannot open '+url)
##             return 0
##         else:
##             u.close()
##             del u
        self.__url = url
        self.__rmaplayer.SetStatusListener(self)
        if windowless:
            self.__rmaplayer.SetPyVideoRenderer(self.__channel.getRealVideoRenderer())
        if duration > 0:
            self.__qid = self.__channel._scheduler.enterabs(start_time + duration, 0,
                                               self.__stop, (start_time + duration,))
        self.__playdone_called = 0
        # WARNING: RealMedia player doesn't unquote, so we must do it
        url = MMurl.unquote(url)
        if realenginedebug:
            print 'RealChannel.playit', self, `url`
        self._playargs = (node, window, winpossize, url, windowless, start_time)
        try:
            self.__rmaplayer.OpenURL(url)
        except rma.error:
            raise error, "Cannot open: %s" % url

        t0 = self.__channel._scheduler.timefunc()
        if t0 > start_time:
            self.__spark = 1
        else:
            self.__spark = 0
            try:
                self.__rmaplayer.Begin()
            except rma.error:
                raise error, "Cannot open: %s" % url
        self.__engine.startusing()
        self.__using_engine = 1
        return 1

    def OnPresentationOpened(self):
        if not self.__spark: return
        node = self._playargs[0]
        t0 = self.__channel._scheduler.timefunc()
        if t0 > self._playargs[5] and not settings.get('noskip'):
            if not __debug__:
                print 'RealChannel: skipping',node.get_start_time(),t0,t0-node.start_time
            try:
                self.__rmaplayer.Seek(int((t0-node.get_start_time())*1000))
            except rma.error, arg:
                print arg
        else:
            windowinterface.settimer(0.1,(self.__rmaplayer.Begin,()))
            self.__spark = 0

    def OnPostSeek(self, oldTime, newTime):
        if self.__spark:
            windowinterface.settimer(0.1,(self.__rmaplayer.Begin,()))
            self.__spark = 0

    def OnPosLength(self, posmsec, durmsec):
        self.__reporteddur = 0.001*durmsec

    def replay(self):
        if not self._playargs:
            return
        node, window, winpossize, url, windowless, start_time = self._playargs
        temp = self.__rmaplayer
        self.__rmaplayer = None
        self.__createplayer(node)
        self.__rmaplayer.SetStatusListener(self)
        if windowless:
            self.__rmaplayer.SetPyVideoRenderer(self.__channel.getRealVideoRenderer())
        else:
            if window is not None:
                self.__rmaplayer.SetOsWindow(window)
            if winpossize is not None:
                pos, size = winpossize
                self.__rmaplayer.SetPositionAndSize(pos, size)
        self.__rmaplayer.OpenURL(url)
        self.__rmaplayer.Begin()


    def __stop(self, endtime):
        self.__qid = None
        if self.__rmaplayer:
            if realenginedebug:
                print 'RealChannel.__stop', self
            self.__rmaplayer.Stop()
            # This may cause OnStop to be called, and it may not....
            if not self.__playdone_called:
                self.__channel.playdone(0, endtime)
                self.__playdone_called = 1
        else:
            self.__channel.playdone(0, endtime)

    def OnStop(self):
        if realenginedebug:
            print 'RealChannel.OnStop', self
        if self.__qid is None:
            if not self.__playdone_called:
                self.__channel.playdone(0, self.__start_time + self.__rmaplayer.GetCurrentPlayTime())
                self.__playdone_called = 1

    def ErrorOccurred(self,str):
        if realenginedebug:
            print 'RealChannel.ErrorOccurred', self
        windowinterface.settimer(0.1,(self.__channel.errormsg,(None,'RealPlayer error: %s.' % str)))

    def pauseit(self, paused):
        if self.__rmaplayer:
            if realenginedebug:
                print 'RealChannel.pauseit', self, paused
            try:
                if paused:
                    self.__rmaplayer.Pause()
                else:
                    self.__rmaplayer.Begin()
            except rma.error, arg:
                windowinterface.settimer(0.1,(self.__channel.errormsg,(None,'RealPlayer error: %s.'%arg)))

    def stopit(self):
        if self.__rmaplayer:
            if realenginedebug:
                print 'RealChannel.stopit', self
            if self.__qid:
                self.__channel._scheduler.cancel(self.__qid)
            self.__qid = 0
            self.__rmaplayer.Stop()
            if self.__using_engine:
                self.__engine.stopusing()
            self.__using_engine = 0
            self.__rmaplayer = None

    def freezeit(self):
        if self.__rmaplayer:
            if realenginedebug:
                print 'RealChannel.freezeit', self
            if self.__qid:
                self.__channel._scheduler.cancel(self.__qid)
            self.__qid = 0
            try:
                self.__rmaplayer.Pause()
            except rma.error, arg:
                windowinterface.settimer(0.1,(self.__channel.errormsg,(None,'RealPlayer error: %s.'%arg)))
