__version__ = "$Id$"
from Channel import ChannelWindowAsync
import windowinterface
import time
import MMurl
import MMAttrdefs
import WMEVENTS
import os
from Carbon import Qt
from Carbon import QuickTime

QT_AVAILABLE = windowinterface._qtavailable()
if not QT_AVAILABLE:
    Qt = None

debug = 0 # os.environ.has_key('CHANNELDEBUG')

class VideoChannel(ChannelWindowAsync):
    node_attrs = ChannelWindowAsync.node_attrs + \
                 ['clipbegin', 'clipend', 'project_audiotype', 'project_videotype', 'project_targets',
                 'project_perfect', 'project_mobile']
    chan_attrs = ChannelWindowAsync.chan_attrs + ['fit']

    def __init__(self, name, attrdict, scheduler, ui):
        ChannelWindowAsync.__init__(self, name, attrdict, scheduler, ui)
        if debug: print 'VideoChannel: init', name
        self.arm_movie = None
        self.play_movie = None
        self.has_callback = 0
        self.idleprocactive = 0
        self._paused = 0
        if QT_AVAILABLE:
            Qt.EnterMovies()
        self.DBGcolor = (0xffff, 0, 0)
        self.__rc = None
        self.__extra_end_delay = 0
        self.__qid = None

    tmpfiles = []
    __callback_added = 0

    def getfileurl(self, node):
        # This method has all sorts of magic to write a
        # RealPix file "just in time".  If the node has
        # changed there is a tmpfile attribute.  Since the
        # node has changed internally, we must write a copy
        # and we'll use the tmpfile attribute for a file name.
        # If the node has no URL, there is no existing file
        # that we can use, so we invent a name and write the
        # file.
        url = ChannelWindowAsync.getfileurl(self, node)
        if not url or url[:5] == 'data:':
            if hasattr(node, 'rptmpfile') and node.rptmpfile[1] == url:
                url = node.rptmpfile[0]
            else:
                import tempfile, realsupport, MMurl
                f = MMurl.urlopen(url)
                head = f.read(4)
                if head != '<imf':
                    f.close()
                    # delete rptmpfile attr if it exists
                    node.rptmpfile = None
                    del node.rptmpfile
                    return url
                rp = realsupport.RPParser(url)
                rp.feed(head)
                rp.feed(f.read())
                f.close()
                rp.close()
                f = tempfile.mktemp('.rp')
                nurl = MMurl.pathname2url(f)
                node.rptmpfile = nurl, url
                realsupport.writeRP(f, rp, node, baseurl = url)
                if not self.__callback_added:
                    import windowinterface
                    windowinterface.addclosecallback(
                            _deltmpfiles, ())
                    VideoChannel.__callback_added = 1
                self.tmpfiles.append(f)
        return url

    def do_show(self, pchan):
        if not ChannelWindowAsync.do_show(self, pchan):
            return 0
        self.window.register(WMEVENTS.OSWindowChanged, self.oswindowchanged, None)
        return 1

    def do_arm(self, node, same=0):
        self.__ready = 0        # set when arm succeeded
        node.__type = ''
        if node.type != 'ext':
            self.errormsg(node, 'Node must be external.')
            return 1
        if debug: print 'VideoChannel: arm', node
        fn = self.getfileurl(node)
        if not fn:
            self.errormsg(node, 'No URL set on node.')
            return 1
        mtype = node.GetAttrDef('type', None)
        if not mtype:
            import urlcache
            mtype = urlcache.mimetype(fn)
        import string
        if mtype and (string.find(mtype, 'real') >= 0 or string.find(mtype, 'flash') >= 0):
            node.__type = 'real'
        self.prepare_armed_display(node)
        if node.__type == 'real':
            if self.__rc is None:
                import RealChannel
                try:
                    self.__rc = RealChannel.RealChannel(self)
                except RealChannel.error, msg:
                    # can't do RealVideo
##                     self.__rc = 0 # don't try again
                    self.errormsg(node, msg)
            if self.__rc:
                if self.__rc.prepare_player(node):
                    self.__ready = 1
            return 1
        if not QT_AVAILABLE:
            self.errormsg(node, "QuickTime not available.")
            return 1
        try:
            fn = MMurl.urlretrieve(fn)[0]
        except IOError, arg:
            if type(arg) == type(()):
                arg = arg[-1]
            self.errormsg(node, 'Cannot open: %s\n\n%s.'%(fn, arg))
        self.window._mac_setwin()

        try:
            movieResRef = Qt.OpenMovieFile(fn, 1)
        except (ValueError, Qt.Error), arg:
            if type(arg) == type(()):
                arg = arg[-1]
            self.errormsg(node, 'QuickTime cannot open: %s\n\n%s.'%(fn, arg))
            return 1
        try:
            self.arm_movie, d1, d2 = Qt.NewMovieFromFile(movieResRef, 0,
                            0)
##                     QuickTime.newMovieActive)
        except (ValueError, Qt.Error), arg:
            Qt.CloseMovieFile(movieResRef)
            if type(arg) == type(()):
                arg = arg[-1]
            self.errormsg(node, 'QuickTime cannot parse: %s\n\n%s.'%(fn, arg))
            return 1
        self.place_movie(node, self.arm_movie)
##         self.make_ready(self.arm_movie)
        self.__ready = 1
        return 1

    def make_ready(self, movie, node):
        # First convert begin/end to movie times
        clipbegin = self.getclipbegin(node, 'sec')
        clipend = self.getclipend(node, 'sec')
        clipdur = node.GetAttrDef('duration', None)
        if clipdur is not None:
            if not clipend or (clipbegin or 0) + clipdur < clipend:
                clipend = (clipbegin or 0) + clipdur
        dummy, (value, tbrate, base) = movie.GetMovieTime()
        movie_end = movie.GetMovieDuration()
        self.__extra_end_delay = 0
        if clipbegin:
            begin = int(clipbegin*tbrate)
        else:
            begin = 0
        if clipend:
            end = int(clipend*tbrate)
            if end > movie_end:
                self.__extra_end_delay = (end-movie_end) / tbrate
                end = movie_end
            dur = end - begin
        else:
            end = movie_end
            dur = end - begin
        t0 = self._scheduler.timefunc()
        start_time = node.get_start_time()
        self.__movieend = start_time + dur
        if t0 > start_time:
            extra_delay = int((t0-start_time)*tbrate)
        else:
            extra_delay = 0
        if debug: print "DBG: movie Rate, end,", tbrate, movie_end
        if debug: print "DBG: clip begin, end, dur", clipbegin, clipend, clipdur
        if debug: print "DBG: result begin, end, dur", begin, end, dur
        if debug: print "DBG: extra_delay, extra_end_delay", extra_delay, self.__extra_end_delay
        # Next preroll
        rate = movie.GetMoviePreferredRate()
        try:
            movie.PrerollMovie(begin, rate)
        except Qt.Error, arg:
            if arg[0] == -50:
                print 'Warning: error -50 from PrerollMovie(%d, %d)' % (begin, rate)
            else:
                raise
        # Now set active area
        movie.SetMovieActiveSegment(begin, dur)
        # And go to the beginning of it.
##         movie.GoToBeginningOfMovie()
        if extra_delay >= dur:
            # XXX Wrong. We should also eat into any subsequent iterations
            extra_delay = dur-1
        movie.SetMovieTimeValue(extra_delay)
##         movie.MoviesTask(0)

    def place_movie(self, node, movie):
        self.window._mac_setwin()
        grafport = self.window._mac_getoswindowport()
        movie.SetMovieGWorld(grafport, None)
        screenBox = self.window.qdrect()
        screenClip = self.window._mac_getclip()
        l, t, r, b = movie.GetMovieBox()
        if node:
            fit = MMAttrdefs.getattr(node, 'fit')
        else:
            # This happens during a resize: we don't know scale/center anymore.
            fit = 'hidden'
        if debug: print 'fit=', fit
        # Compute real scale for scale-to-fit
        sl, st, sr, sb = screenBox
        if debug: print 'movie', l, t, r, b
        if debug: print 'screen', sl, st, sr, sb
        if fit is not None and fit != 'hidden':
            if l == r:
                maxxscale = 1  # Empty window, so don't divide by 0
            else:
                maxxscale = float(sr-sl)/(r-l)
            if t == b:
                maxyscale = 1  # Empty window, so don't divide by 0
            else:
                maxyscale = float(sb-st)/(b-t)
            scale = min(maxxscale, maxyscale)
            if debug: print 'scale=', scale, maxxscale, maxyscale
            movieBox = sl, st, sl+int((r-l)*scale), sr+int((b-t)*scale)
            nMovieBox = self._scalerect(screenBox, movieBox, 0)
        else:
            nMovieBox = sl, st, sl + (r-l), st + (b-t)
        movie.SetMovieBox(nMovieBox)

        movie.SetMovieDisplayClipRgn(screenClip)
        if debug: print 'placed movie'

    def oswindowchanged(self, *args):
        if debug: print 'oswindowchanged'
        self.window._mac_setwin()
        grafport = self.window._mac_getoswindowport()
        if self.arm_movie:
            self.arm_movie.SetMovieGWorld(grafport, None)
        if self.play_movie:
            self.play_movie.SetMovieGWorld(grafport, None)

    def resize(self, arg, window, event, value):
        if debug: print 'resize'
        ChannelWindowAsync.resize(self, arg, window, event, value)
        if self.arm_movie:
            self.place_movie(None, self.arm_movie)
        if self.play_movie:
            self.place_movie(None, self.play_movie)
            self.window._mac_setredrawguarantee(self.play_movie.GetMovieBox())

    def redraw(self, rgn=None):
        # rgn (region to be redrawn, None for everything) ignored for now
        if debug: print 'redraw'
        if self.play_movie:
            self.place_movie(None, self.play_movie)
            self.play_movie.UpdateMovie()

    def _playsome(self):
        if debug: print 'VideoChannel: playsome'
        if not self.play_movie:
            return

        if self.play_movie.IsMovieDone():
            # XXX Should cater for self.extra_end_delay!
            self.__stoplooping()

    def __stopplay(self):
        self.__qid = None
        self.__stoplooping()

    def __stoplooping(self):
        if self.__qid is not None:
            self._scheduler.cancel(self.__qid)
            self.__qid = None
        if not self.play_movie:
            return
        self.play_movie.StopMovie()
##         self.play_movie = None
##         if self.window:
##             self.window.setredrawfunc(None)
##             self.window._mac_setredrawguarantee(None)
##         self.fixidleproc()
        self.playdone(0, self.__movieend)

    def do_play(self, node, curtime):
        self.__type = node.__type
        if not self.__ready:
            # arming failed, so don't even try playing
            self.playdone(0, curtime)
            return
        if node.__type == 'real':
            if not self.__rc or not self.__rc.playit(node, self._getoswindow(), self._getoswinpos()):
                self.playdone(0, curtime)
            return
        if not self.arm_movie:
            if self.play_movie:
                self.play_movie.StopMovie()
            self.play_movie = None
            self.playdone(0, curtime)
            return

        if debug: print 'VideoChannel: play', node
        self.play_movie = self.arm_movie
        self.arm_movie = None

        self.make_ready(self.play_movie, node)
        self.play_movie.SetMovieActive(1)
##         self.play_movie.MoviesTask(0)
        self.play_movie.StartMovie()
        self.window.setredrawfunc(self.redraw)
        self.window._mac_setredrawguarantee(self.play_movie.GetMovieBox())

        self.fixidleproc()

    def _scalerect(self, (sl, st, sr, sb), (ml, mt, mr, mb), center):
        maxwidth, maxheight = sr-sl, sb-st
        movwidth, movheight = mr-ml, mb-mt
        if movwidth > maxwidth:
            # Movie is too wide. Scale.
            movheight = movheight*maxwidth/movwidth
            movwidth = maxwidth
        if movheight > maxheight:
            # Movie is too high. Scale.
            movwidth = movwidth*maxheight/movheight
            movheight = maxheight
        if center:
            movleft = (maxwidth-movwidth)/2
            movtop = (maxheight-movheight)/2
        else:
            movleft = movtop = 0
        return sl+movleft, st+movtop, sl+movleft+movwidth, st+movtop+movheight

    # interface for anchor creation
    def defanchor(self, node, anchor, cb):
        windowinterface.showmessage('The whole item will be sensitive.')
        cb(anchor)

    def prepare_armed_display(self,node):
        self.armed_display._bgcolor=self.getbgcolor(node)
        self.armed_display.fgcolor(self.getbgcolor(node))

        # by default armbox is all the window
        armbox=(0.0,0.0,1.0,1.0)
        self.setArmBox(armbox)

    def do_hide(self):
        if self.window:
            self.window.setredrawfunc(None)
            self.window._mac_setredrawguarantee(None)
        if self.__qid is not None:
            # XXXX Is this correct?
            self._scheduler.cancel(self.__qid)
            self.__qid = None
        self.arm_movie = None
        if self.play_movie:
            self.play_movie.StopMovie()
            self.play_movie = None
            self.fixidleproc()
        if self.__rc:
            self.__rc.stopit()
            self.__rc.destroy()
            self.__rc = None
        ChannelWindowAsync.do_hide(self)

    def playstop(self, curtime):
        if debug: print 'VideoChannel: playstop'
        if self.__type == 'real':
            if self.__rc:
                self.__rc.stopit()
        elif self.play_movie:
            self.play_movie.StopMovie()
##             self.play_movie = None
##             self.fixidleproc()
        ChannelWindowAsync.playstop(self, curtime)

    def stopplay(self, node, curtime):
        if node.GetType() == 'anchor':
            self.stop_anchor(node, curtime)
            return
        if self.window:
            self.window.setredrawfunc(None)
            self.window._mac_setredrawguarantee(None)
        if self.play_movie:
            self.play_movie.StopMovie()
            self.play_movie = None
        self.fixidleproc()
        ChannelWindowAsync.stopplay(self, node, curtime)

    def fixidleproc(self):
        if self.window:
            self.window._set_movie_active(not not self.play_movie)
        wantone = not not ((not self._paused) and self.play_movie)
        if wantone == self.idleprocactive:
            return
        if wantone:
            self.__id = windowinterface.setidleproc(self._playsome)
        else:
            windowinterface.cancelidleproc(self.__id)
        self.idleprocactive = wantone

    def setpaused(self, paused, timestamp):
        self._paused = paused
        if self.__rc:
            self.__rc.pauseit(paused)
        if self.play_movie:
            if paused:
                self.play_movie.StopMovie()
            else:
                self.play_movie.StartMovie()
        self.fixidleproc()

    def _getoswindow(self):
        # XXXX Or getoswindowport??
        return self.window._mac_getoswindow()

    def _getoswinpos(self):
        x0, y0, x1, y1 = self.window.qdrect()
        return ((x0, y0), (x1-x0, y1-y0))


def _deltmpfiles():
    import os
    for f in VideoChannel.tmpfiles:
        try:
            os.unlink(f)
        except:
            pass
    VideoChannel.tmpfiles = []
