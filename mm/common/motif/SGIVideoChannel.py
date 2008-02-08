__version__ = "$Id$"

import Channel
import MMAttrdefs
from MMExc import *                     # exceptions
import windowinterface
import MMurl
import mv
import Xlib
import string
import settings

_mvmap = {}                     # map of MVid to channel

def _selcb():
    while mv.PendingEvents():
        event = mv.NextEvent()
        if event[0] == mv.MV_EVENT_STOP:
            if _mvmap.has_key(event[1]):
                _mvmap[event[1]].stopped()

windowinterface.select_setcallback(mv.GetEventFD(), _selcb, ())
mv.SetSelectEvents(mv.MV_EVENT_MASK_STOP)

class VideoChannel(Channel.ChannelWindowAsync):
    node_attrs = Channel.ChannelWindowAsync.node_attrs + [
            'clipbegin', 'clipend',
            'project_audiotype', 'project_videotype', 'project_targets',
            'project_perfect', 'project_mobile']
    chan_attrs = Channel.ChannelWindowAsync.chan_attrs + ['fit']

    def __init__(self, name, attrdict, scheduler, ui):
        Channel.ChannelWindowAsync.__init__(self, name, attrdict, scheduler, ui)
        self.__context = None
        self.played_movie = self.armed_movie = None
        self.__stopped = 0
        self.__qid = None

    def getaltvalue(self, node):
        url = self.getfileurl(node)
        i = string.rfind(url, '.')
        if i > 0:
            suff = url[i:]
            return suff in ('.mpg', '.mpv', '.qt', '.avi')
        return 0

    def do_show(self, pchan):
        if not Channel.ChannelWindowAsync.do_show(self, pchan):
            return 0
        window = self.window
        widget = window._form
        if widget.IsRealized():
            self.__ginitCB(widget, window._visual, None)
        else:
            widget.AddCallback('ginitCallback', self.__ginitCB,
                               window._visual)
        return 1

    def __ginitCB(self, widget, visual, calldata):
        self.__context = widget.CreateContext(visual, None, 1)

    def do_hide(self):
        if self.played_movie:
            movie = self.played_movie
            self.played_movie = None
            movie.Stop()
            if self.played_flag:
                d = movie.GetEstMovieDuration(1000)
            else:
                d = movie.GetMovieDuration(1000)
            d = d / 1000.0
            if hasattr(movie, 'GetCurrentTime'):
                t = movie.GetCurrentTime(1000) / 1000.0
            else:
                # if no GetCurrentTime, act as if at end
                t = d
            looplimit = movie.GetPlayLoopLimit()
            loopcount = movie.GetPlayLoopCount()
            movie.UnbindOpenGLWindow()
            del _mvmap[movie]
            if self.__qid is None and \
               looplimit != mv.MV_LIMIT_FOREVER and \
               self._playstate == Channel.PLAYING:
                t = d-t # time remaining in current loop
                if looplimit > 1:
                    # add time of remaining loops
                    t = (looplimit - loopcount - 1) * d + t
                self._qid = self._scheduler.enter(
                        t, 0, self.playdone, (0,t))
        if self.__context:
            self.__context.DestroyContext()
            self.__context = None
        Channel.ChannelWindowAsync.do_hide(self)

    def do_arm(self, node, same=0):
        if same and self.armed_display:
            return 1
        if node.type != 'ext':
            self.errormsg(node, 'Node must be external.')
            return 1
        url = self.getfileurl(node)
        if not url:
            self.errormsg(node, 'No URL set on node.')
            return 1
        try:
            f, hdr = MMurl.urlretrieve(url)
        except IOError, arg:
            self.errormsg(node, 'Cannot open: %s\n\n%s.' % (url, arg[1]))
            return 1
        if string.find(hdr.subtype, 'real') >= 0:
            self.errormsg(node, 'No playback support for RealVideo in this version.')
            return 1
        if not mv.IsMovieFile(f):
            self.errormsg(node, 'Not a movie: %s' % url)
            return 1
        if MMAttrdefs.getattr(node, 'clipbegin') or \
           MMAttrdefs.getattr(node, 'clipend'):
            flag = 0
        else:
            flag = mv.MV_MPEG1_PRESCAN_OFF
        flag = 0        # MV_MPEG1_PRESCAN_OFF does not work well
        self.armed_flag = flag
        try:
            self.armed_movie = movie = mv.OpenFile(f, flag)
        except mv.error, msg:
            self.errormsg(node, 'Cannot open: %s\n\n%s.' % (url, msg))
            return 1
        _mvmap[movie] = self
        movie.SetPlaySpeed(1)
        fit = MMAttrdefs.getattr(node, 'fit')
        self.armed_fit = fit
        x, y, w, h = self.window._rect
        track = movie.FindTrackByMedium(mv.DM_IMAGE)
        if fit is None or fit == 'hidden':
            width = track.GetImageWidth()
            height = track.GetImageHeight()
            self.armed_size = width, height
            width = min(width, w)
            height = min(height, h)
            movie.SetViewSize(width, height)
            width, height = movie.QueryViewSize(width, height)
            imbox = 0, 0, float(width)/w, float(height)/h
            y = self.window._form.height - y - height
            movie.SetViewOffset(x, y, mv.DM_TRUE)
        else:
            imbox = 0, 0, 1, 1
            movie.SetViewSize(w, h)
            # X coordinates don't work, so use GL coordinates
            movie.SetViewOffset(x,
                                self.window._form.height - y - h,
                                mv.DM_TRUE)
            self.armed_size = None
        self.__begin = self.getclipbegin(node, 'sec')
        self.__end = self.getclipend(node, 'sec')
        if not self.__end:
            self.__end = movie.GetMovieDuration(1000) / 1000.0
        self.__mediadur = self.__end - self.__begin
        bg = self.getbgcolor(node)
        movie.SetViewBackground(bg)
        self.armed_bg = self.window._convert_color(bg)

        self.armed_display.fgcolor(self.getbgcolor(node))

        self.setArmBox(imbox)
        return 1

    def do_play(self, node, curtime):
        window = self.window
        self.played_movie = movie = self.armed_movie
        self.armed_movie = None
        start_time = node.get_start_time()
        if movie is None:
            self.playdone(0, curtime)
            return
        self.played_fit = self.armed_fit
        self.played_size = self.armed_size
        self.played_bg = self.armed_bg
        self.played_flag = self.armed_flag
        if self.__begin:
            movie.SetStartTime(long(self.__begin * 1000L), 1000)
        t0 = self._scheduler.timefunc()
        if t0 > start_time and not settings.get('noskip'):
            if __debug__:
                print 'skipping',start_time,t0,t0-start_time
            late = t0 - start_time
            if late > self.__mediadur:
                self.playdone(0, max(curtime, start_time + self.__mediadur))
                return
            movie.SetCurrentTime(long((self.__begin + late) * 1000L), 1000)
        if self.__end:
            movie.SetEndTime(long(self.__end * 1000L), 1000)
        window.setredrawfunc(self.redraw)
        try:
            movie.BindOpenGLWindow(self.window._form, self.__context)
        except mv.error, msg:
            name = MMAttrdefs.getattr(node, 'name')
            if not name:
                name = '<unnamed node>'
            self.errormsg(node, 'Cannot play movie.')
            self.playdone(0, curtime)
            return
        movie.Play()
        self.__stopped = 0
        r = Xlib.CreateRegion()
        r.UnionRectWithRegion(0, 0, window._form.width, window._form.height)
        r.SubtractRegion(window._region)
        window._topwindow._do_expose(r)

    def playstop(self, curtime):
        if self.__qid:
            self._scheduler.cancel(self.__qid)
            self.__qid = None
        if self.played_movie:
            self.played_movie.Stop()
        self.playdone(1, curtime)

    def stopplay(self, node, curtime):
        if node.GetType() == 'anchor':
            self.stop_anchor(node, curtime)
            return
        if node and self._played_node is not node:
##             print 'node was not the playing node '+`self,node,self._played_node`
            return
        Channel.ChannelWindowAsync.stopplay(self, node, curtime)
        if self.played_movie:
            self.played_movie.UnbindOpenGLWindow()
            del _mvmap[self.played_movie]
            self.played_movie = None
        window = self.window
        if window:
            window.setredrawfunc(None)
            window._topwindow._do_expose(window._region)

    def setpaused(self, paused, timestamp):
        if self.played_movie:
            if paused:
                self.played_movie.Stop()
                if paused == 'hide':
                    self.played_movie.UnbindOpenGLWindow()
                self.__stopped = 1
            else:
                if self._paused == 'hide':
                    self.played_movie.BindOpenGLWindow(self.window._form, self.__context)
                self.played_movie.Play()
                self.__stopped = 0
        self._paused = paused

    def redraw(self, rgn=None):
        # rgn (region to be redrawn, None for everything) ignored for now
        if self.played_movie:
            self.played_movie.ShowCurrentFrame()

    def resize(self, arg, window, event, value):
        x, y, w, h = window._rect
        movie = self.played_movie
        if not movie:
            return
        fit = self.played_fit
        if fit is None or fit == 'hidden':
            width, height = self.played_size
            width = min(width, w)
            height = min(height, h)
            movie.SetViewSize(width, height)
            width, height = movie.QueryViewSize(width, height)
            movie.SetViewOffset(x + (w - width) / 2,
                                self.window._form.height - y - (h + height) / 2,
                                mv.DM_TRUE)
        else:
            movie.SetViewSize(w, h)
            movie.SetViewOffset(x,
                                self.window._form.height - y - h,
                                mv.DM_TRUE)
            self.armed_size = None
        movie.ShowCurrentFrame()

    def stopped(self):
        if not self.__stopped:
            if self.__qid:
                return
            node = self._played_node
            start_time = node.get_start_time()
            self.playdone(0, start_time + self.__mediadur)

    # Convert pixel offsets into relative offsets.
    # If the offsets are in the range [0..1], we don't need to do
    # the conversion since the offsets are already fractions of
    # the image.
#       def convert_args(self, file, args):
#               need_conversion = 1
#               for a in args:
#                       if a != int(a): # any floating point number
#                               need_conversion = 0
#                               break
#               if not need_conversion:
#                       return args
#               if args == (0, 0, 1, 1) or args == [0, 0, 1, 1]:
            # special case: full image
#                       return args
#               import Sizes
#               xsize, ysize = Sizes.GetSize(file)
#               return float(args[0]) / float(xsize), \
#                      float(args[1]) / float(ysize), \
#                      float(args[2]) / float(xsize), \
#                      float(args[3]) / float(ysize)
