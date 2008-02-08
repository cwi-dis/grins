__version__ = "$Id$"

#
# WIN32 RealWindowChannel.
#

# @win32doc|RealWindowChannel

import Channel, RealChannel

realwindowchanneldebug=0

class RealWindowChannel(Channel.ChannelWindowAsync):
    def __init__(self, name, attrdict, scheduler, ui):
        self.need_armdone = 0
        self.__rc = None
        self.__rc_error = None
        Channel.ChannelWindowAsync.__init__(self, name, attrdict, scheduler, ui)

    def do_arm(self, node, same = 0):
        if realwindowchanneldebug:
            print 'do_arm', self, node
        if self.__rc is None or not self.__rc.prepare_player(node):
            if self.__rc_error:
                self.errormsg(node, self.__rc_error)
                self.__rc_error = ''
        return 1

    def do_show(self, pchan):
        if not Channel.ChannelWindowAsync.do_show(self, pchan):
            return 0
        try:
            self.__rc = RealChannel.RealChannel(self)
        except RealChannel.error, msg:
            # can't do RealMedia
##             self.__rc = 0 # don't try again
            if self.__rc_error is None:
                self.__rc_error = msg
            self.__rc = None
        return 1

    def do_hide(self):
        if self.__rc is not None:
            self.__rc.stopit()
            self.__rc.destroy()
            self.__rc = None
        Channel.ChannelWindowAsync.do_hide(self)

    def do_play(self, node, curtime):
        if realwindowchanneldebug:
            print 'do_play', self, node
        if self.__rc is not None:
            if self.__rc.playit(node, self._getoswindow(), self._getoswinpos()):
                return
        self.playdone(0, curtime)

    # toggles between pause and run
    def setpaused(self, paused, timestamp):
        Channel.ChannelWindowAsync.setpaused(self, paused, timestamp)
        if self.__rc is not None:
            self.__rc.pauseit(paused)

    def playstop(self, curtime):
        if self.__rc is not None:
            self.__rc.stopit()
        Channel.ChannelWindowAsync.playstop(self, curtime)

    def _getoswindow(self):
        if hasattr(self.window, "GetSafeHwnd"):
            # Windows
            return self.window.GetSafeHwnd()
        elif hasattr(self.window, "_mac_getoswindow"):
            # Macintosh
            return self.window._mac_getoswindow()
        elif hasattr(self.window, '_form'):
            # Motif
            wnd = self.window._topwindow._form
            return wnd.Window(), wnd.Display().GetDisplay()
        else:
            return None

    def _getoswinpos(self):
        if hasattr(self.window, "qdrect"):
            x0, y0, x1, y1 = self.window.qdrect()
            return ((x0, y0), (x1-x0, y1-y0))
        elif hasattr(self.window, '_rect'):
            x, y, w, h = self.window._rect
            return (x, y), (w, h)
        return None

    def play(self, node, curtime):
        if realwindowchanneldebug:
            print 'play', self, node
        if node.GetType() == 'anchor':
            self.play_anchor(node, curtime)
            return
        self.need_armdone = 0
        self.play_0(node, curtime)
        if self._is_shown and node.ShouldPlay() \
           and self.window and not self.syncplay:
            self.check_popup()
            if self.armed_display.is_closed():
                # assume that we are going to get a
                # resize event
                pass
            else:
                self.armed_display.render()
            if self.played_display:
                self.played_display.close()
            self.played_display = self.armed_display
            self.armed_display = None
            self.do_play(node, curtime)
            self.need_armdone = 1
        else:
            self.play_1(curtime)

    def playdone(self, outside_induced, curtime):
        if realwindowchanneldebug:
            print 'playdone', self
        if self._armstate != Channel.ARMED:
            self.need_armdone = 0
        if self.need_armdone:
            self.need_armdone = 0
            self.armdone()
        Channel.ChannelWindowAsync.playdone(self, outside_induced, curtime)
