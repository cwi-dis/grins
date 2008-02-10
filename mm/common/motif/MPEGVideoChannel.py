__version__ = "$Id$"

from ChannelThread import ChannelWindowThread
import MMurl
from MMExc import *                     # exceptions


class VideoChannel(ChannelWindowThread):
    node_attrs = ChannelWindowThread.node_attrs + [
            'clipbegin', 'clipend',
            'project_audiotype', 'project_videotype', 'project_targets',
            'project_perfect', 'project_mobile']
    chan_attrs = ChannelWindowThread.chan_attrs + ['fit', 'project_videotype', 'project_targets']

    def threadstart(self):
        import mpegchannel
        return mpegchannel.init()

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
            filename = MMurl.urlretrieve(url)[0]
            fp = open(filename, 'rb')
        except IOError, msg:
            self.errormsg(node, 'Cannot open: %s\n\n%s.' % (url, msg[1]))
            return 1
        try:
            import MMAttrdefs
            fit = MMAttrdefs.getattr(node, 'fit')
            if fit == 'hidden':
                scale = 1.0
            else:
                scale = 0.0
            arminfo = {'scale': scale,
                       'bgcolor': self.getbgcolor(node),
                       }
            self.threads.arm(fp, 0, 0, arminfo, None,
                      self.syncarm)
        except RuntimeError, msg:
            if type(msg) is type(self):
                msg = msg.args[0]
            print 'Bad mpeg file', `url`, msg
            return 1

        self.armed_display.fgcolor(self.getbgcolor(node))
        return self.syncarm

    #
    # It appears that there is a bug in the cl mpeg decompressor
    # which disallows the use of two mpeg decompressors in parallel.
    #
    # Redefining play() and playdone() doesn't really solve the problem,
    # since two mpeg channels will still cause trouble,
    # but it will solve the common case of arming the next file while
    # the current one is playing.
    #
    # XXXX This problem has to be reassesed with the 5.2 cl. See also
    # the note in mpegchannelmodule.c
    #
    def play(self, node, curtime):
        if node.GetType() == 'anchor':
            self.play_anchor(node, curtime)
            return
        self.need_armdone = 0
        self.play_0(node, curtime)
        if not self._is_shown or self.syncplay:
            self.play_1(curtime)
            return
        if not self.nopop:
            self.window.pop()
        if self.armed_display.is_closed():
            # assume that we are going to get a
            # resize event
            pass
        else:
            self.armed_display.render()
        if self.played_display:
            self.played.display.close()
        self.played_display = self.armed_display
        self.armed_display = None
        thread_play_called = 0
        if self.threads.armed:
            w = self.window
            w.setredrawfunc(self.do_redraw)
            try:
                w._gc.SetRegion(w._clip)
                w._gc.foreground = w._convert_color(self.getbgcolor(node))
            except AttributeError:
                pass
            print 'should skip',self._scheduler.timefunc()-node.get_start_time()
            self.threads.play()
            thread_play_called = 1
        if self._is_shown:
            self.do_play(node, curtime)
        self.need_armdone = 1
        if not thread_play_called:
            self.playdone(0, curtime)

    def playdone(self, outside_induced, curtime):
        if self.need_armdone:
            self.armdone()
            self.need_armdone = 0
        ChannelWindowThread.playdone(self, outside_induced, curtime)

    def defanchor(self, node, anchor, cb):
        import windowinterface
        windowinterface.showmessage('The whole item will be sensitive.')
        cb(anchor)

    def stoparm(self):
        self.need_armdone = 0
        ChannelWindowThread.stoparm(self)

    # Convert pixel offsets into relative offsets.
    # If the offsets are in the range [0..1], we don't need to do
    # the conversion since the offsets are already fractions of
    # the image.
    def convert_args(self, file, args):
        need_conversion = 1
        for a in args:
            if a != int(a): # any floating point number
                need_conversion = 0
                break
        if not need_conversion:
            return args
        if args == (0, 0, 1, 1) or args == [0, 0, 1, 1]:
            # special case: full image
            return args
        import Sizes
        xsize, ysize = Sizes.GetSize(file)
        return float(args[0]) / float(xsize), \
               float(args[1]) / float(ysize), \
               float(args[2]) / float(xsize), \
               float(args[3]) / float(ysize)
