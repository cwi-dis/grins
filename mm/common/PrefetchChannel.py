__version__ = "$Id$"

# the core
import Channel

# urlopen
import MMurl

# for timing support
import windowinterface
import time

# atoi, atof
import string

debug = 1

class PrefetchChannel(Channel.ChannelAsync):
    def __init__(self, name, attrdict, scheduler, ui):
        Channel.ChannelAsync.__init__(self, name, attrdict, scheduler, ui)
        self.__duration = None
        self.__fetching = None

    def __repr__(self):
        return '<PrefetchChannel instance, name=' + `self._name` + '>'

    #
    # Channel overrides
    #

    def do_hide(self):
        Channel.ChannelAsync.do_hide(self)

    def do_play(self, node, curtime):
        Channel.ChannelAsync.do_play(self, node, curtime)

        self.__initEngine(node)

        if not self.__ready():
            self.playdone(0, curtime)
            return

        self.__fetching = node

        # get timing
        self.__duration = node.GetAttrDef('duration', None)

        self.__startFetch()

    def setpaused(self, paused, timestamp):
        Channel.ChannelAsync.setpaused(self, paused, timestamp)
        self.__pauseFetch(paused)

    def stopplay(self, node, curtime):
        if node.GetType() == 'anchor':
            self.stop_anchor(node, curtime)
            return
        if self.__fetching:
            self.__stopFetch()
            self.__fetching = None
        Channel.ChannelAsync.stopplay(self, node, curtime)

    #
    # Fetch engine
    #

    def __initEngine(self, node):
        self.__fiber_id = None
        self.__start = None
        self.__pausedt = 0
        self.__urlopener = None
        self.__playdone = 0
        self.__mmmsg = None

        url = self.getfileurl(node)
        if not url:
            print 'No URL set on node'
            return
        self.__url = url

        self.__urlopener = MMurl.geturlopener()
        try:
            filename, mmmsg = self.__urlopener.begin_retrieve(url)
        except:
            print 'Warning: cannot open url %s' % url
            self.__urlopener = None
        else:
            self.__mmmsg = mmmsg
            val = mmmsg.get('content-length')
            if val:
                self.__content_length = string.atoi(val)
            self.__accept_ranges = mmmsg.get('accept-ranges')

    def __ready(self):
        return self.__urlopener!=None

    def __startFetch(self):
        self.__start = self.__fetching.get_start_time()
        if self.__start is None:
            print 'Warning: None start_time for node',self.__fetching
            self.__start = 0
        self.__urlopener.begin_retrieve(self.__url)
        self.__fetch()
        self.__register_for_timeslices()

    def __stopFetch(self):
        if self.__fetching:
            self.__unregister_for_timeslices()
            self.__urlopener=None

    def __pauseFetch(self, paused):
        if self.__fetching:
            if paused:
                self.__pausedt = time.time() - self.__start
                self.__unregister_for_timeslices()
            else:
                self.__start = time.time() - self.__pausedt
                self.__register_for_timeslices()

    def __fetch(self):
        dt = self._scheduler.timefunc() - self.__start
        if self.__urlopener and self._playstate == Channel.PLAYING:
            if not self.__urlopener.do_retrieve(self.__url, 1024):
                self.__urlopener.end_retrieve(self.__url)
                self.playdone(0, self._scheduler.timefunc())

    def __onFetchDur(self):
        if not self.__fetching:
            return
        self.playdone(0, self.__start+self.__duration)

    def onIdle(self):
        self.__fiber_id = None
        if self.__fetching:
            t_sec=self._scheduler.timefunc() - self.__start
            if self.__duration and t_sec>=self.__duration:
                self.__onFetchDur()
                self.__unregister_for_timeslices()
            else:
                self.__fetch()
                self.__register_for_timeslices()

    def __register_for_timeslices(self):
        if self.__fiber_id is None:
            self.__fiber_id = windowinterface.settimer(0.1, (self.onIdle,()))

    def __unregister_for_timeslices(self):
        if self.__fiber_id is not None:
            windowinterface.canceltimer(self.__fiber_id)
            self.__fiber_id = None
