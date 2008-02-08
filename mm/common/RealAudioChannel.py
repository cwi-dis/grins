__version__ = "$Id$"

#
# WIN32 RealAudioChannel.
#

# @win32doc|RealAudioChannel

import Channel, RealChannel

class RealAudioChannel(Channel.ChannelAsync):
    def __init__(self, name, attrdict, scheduler, ui):
        self.need_armdone = 0
        self.__rc = None
        self.__rc_error = None
        Channel.ChannelAsync.__init__(self, name, attrdict, scheduler, ui)

    def do_show(self, pchan):
        if not Channel.ChannelAsync.do_show(self, pchan):
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
        Channel.ChannelAsync.do_hide(self)

    def do_arm(self, node, same = 0):
        if self.__rc is None or not self.__rc.prepare_player(node):
            if self.__rc_error:
                self.errormsg(node, self.__rc_error)
                self.__rc_error = ''
        return 1

    def do_play(self, node, curtime):
        if self.__rc is not None:
            if self.__rc.playit(node, self._getoswindow(), self._getoswinpos()):
                return
        self.playdone(0, curtime)

    # toggles between pause and run
    def setpaused(self, paused, timestamp):
        Channel.ChannelAsync.setpaused(self, paused, timestamp)
        if self.__rc is not None:
            self.__rc.pauseit(paused)

    def playstop(self, curtime):
        if self.__rc is not None:
            self.__rc.stopit()
        Channel.ChannelAsync.playstop(self, curtime)
