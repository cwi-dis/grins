__version__ = "$Id$"

from usercmd import *
from flags import *

from PlayerDialogBase import PlayerDialogBase, STOPPED, PAUSING, PLAYING

class PlayerDialog(PlayerDialogBase):
    adornments = {
            'shortcuts': {
                    'p': PLAY,
                    'P': PAUSE,
                    's': STOP,
                    ' ': MAGIC_PLAY,
                    },
            'menubar': [
                    (FLAG_ALL, 'File', [
                            (FLAG_ALL, 'Open...', OPEN),
                            (FLAG_ALL, 'Close Document', CLOSE),
                            (FLAG_ALL, None),
                            (FLAG_ALL, 'Preferences...', PREFERENCES),
                            (FLAG_ALL|FLAG_DBG, None),
                            (FLAG_ALL|FLAG_DBG, 'Debug', [
                                    (FLAG_ALL|FLAG_DBG, 'Trace', TRACE, 't'),
                                    (FLAG_ALL|FLAG_DBG, 'Debug', DEBUG),
                                    (FLAG_ALL|FLAG_DBG, 'Crash CMIF', CRASH),
                                    (FLAG_ALL|FLAG_DBG, 'Dump Scheduler Data', SCHEDDUMP),
                                    ]),
                            (FLAG_ALL, None),
                            (FLAG_ALL, 'Quit', EXIT),
                            ]),
                    (FLAG_ALL, 'View', [
                            (FLAG_ALL, 'View Source...', SOURCEVIEW),
                            ]),
                    (FLAG_ALL, 'Play', [
                            (FLAG_ALL, 'Play', PLAY, 't'),
                            (FLAG_ALL, 'Pause', PAUSE, 't'),
                            (FLAG_ALL, 'Stop', STOP, 't'),
                            (FLAG_BOSTON, None),
                            (FLAG_BOSTON, 'Custom Tests', USERGROUPS),
                            (FLAG_CMIF, 'Channels', CHANNELS),
                            ]),
                    (FLAG_ALL, 'Help', [
                            (FLAG_ALL, 'Help', HELP),
                            ]),
                    ],
            'toolbar': PlayerDialogBase.adornments['toolbar'],
            'close': [ CLOSE_WINDOW, CLOSE, EXIT, ],
            }
    adornments2 = {
            'shortcuts': {
                    'p': PLAY,
                    'P': PAUSE,
                    's': STOP,
                    ' ': MAGIC_PLAY,
                    },
            'close': [ CLOSE_WINDOW, ],
            }

    def __init__(self, coords, title):
        PlayerDialogBase.__init__(self, coords, title)
        self.__topcommandlist = []
        self.__has_window = 0

    def topcommandlist(self, list):
        if list != self.__topcommandlist:
            self.__topcommandlist = list
            self.setstate()

    def close(self):
        PlayerDialogBase.close(self)
        del self.__topcommandlist

    def show(self):
        if self.menu_created is None:
            self.__has_window = 1
            PlayerDialogBase.show(self)
        else:
            self.setchannels()

    def after_chan_show(self, channel=None):
        pass

    def setstate(self, state = None):
        commandlist = self.__topcommandlist + \
                      self.toplevel.main.commandlist
        savestoplist = self.stoplist
        saveplaylist = self.playlist
        savepauselist = self.pauselist
        self.stoplist = commandlist + self.stoplist
        self.playlist = commandlist + self.playlist
        self.pauselist = commandlist + self.pauselist

        PlayerDialogBase.setstate(self, state)

        self.stoplist = savestoplist
        self.playlist = saveplaylist
        self.pauselist = savepauselist

    def get_adornments(self, channel):
        if self.menu_created is not None or \
           self.__has_window:
            self.adornments2['flags'] = curflags()
            return self.adornments2
        self.menu_created = channel
        self.adornments['flags'] = curflags()
        return self.adornments
