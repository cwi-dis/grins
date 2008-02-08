# Dialog for the Player control panel.

# The PlayerDialog is a window that displays VCR-like controls to
# control the player plus an interface to turn channels on and off and
# an interface to turn options on and off.

# @win32doc|PlayerDialog
# A PlayerDialog instance manages commands related
# to play. This instance indirectly passes information to
# the windows interface through the get_adornments method
# called by the channel module.

__version__ = "$Id$"


import windowinterface
from usercmd import *

STOPPED, PAUSING, PLAYING = range(3)

class PlayerDialog:
    adornments = {}
    def __init__(self, coords, title):
        # Create the Player dialog.

        # Create the dialog window (non-modal, so does not grab
        # the cursor) but do not pop it up (i.e. do not display
        # it on the screen).

        # Arguments (no defaults):
        # coords -- the coordinates (x, y, width, height) of the
        #       control panel in mm
        # title -- string to be displayed as window title

        self.__window = None
        self.__title = title
        self.__coords = coords
        self.__state = -1
        self.__channels = []
        self.__channeldict = {}
        self.__strid='player'
        self.__cmdtgt='pview_'

    def close(self):
        # Close the dialog and free resources.
        if self.__window is not None:
            # must be corrected together with show
            #self.__window.close()
            self.__window.set_commandlist(None,self.__cmdtgt)
            self.__window = None
        del self.__channels
        del self.__channeldict

    def show(self, subwindowof=None):
        # Show the control panel.
        if self.__window is not None:
            self.__window.pop()
            return
        if subwindowof is not None:
            raise 'kaboo kaboo'

        self.__window = self.toplevel.window
        self.__window.set_commandlist(self.stoplist,self.__cmdtgt)

        if self.__channels:self.setchannels()

    def hide(self):
        # Hide the control panel.

        if self.__window is None:
            return

        #self.__window.close()
#               self.__window.set_commandlist(None,self.__cmdtgt)
        self.toplevel.setplayerstate(STOPPED)
        self.__window = None

    def settitle(self, title):
        # Set (change) the title of the window.

        # Arguments (no defaults):
        # title -- string to be displayed as new window title.
        self.__title = title
        if self.__window is not None:
            self.__window.settitle(title)

    def setchannels(self, channels=None):
        # Set the list of channels.

        # Arguments (no defaults):
        # channels -- a list of tuples (name, onoff) where name
        #       is the channel name which is to be presented
        #       to the user, and onoff indicates whether the
        #       channel is on or off (1 if on, 0 if off)
        if channels is None:
            channels = self.__channels
        else:
            self.__channels = channels

        self.__channeldict = {}
        menu = []
        for i in range(len(channels)):
            channel, onoff = channels[i]
            self.__channeldict[channel] = i
            menu.append((channel, (channel,), 't', onoff))
        w = self.__window
        if w is not None:
            w.set_dynamiclist(CHANNELS, menu)

    def setchannel(self, channel, onoff):
        # Set the on/off status of a channel.

        # Arguments (no defaults):
        # channel -- the name of the channel whose status is to
        #       be set
        # onoff -- the new status

        i = self.__channeldict.get(channel)
        if i is None:
            raise RuntimeError, 'unknown channel'
        if self.__channels[i][1] == onoff:
            return
        self.__channels[i] = channel, onoff
        self.setchannels(self.__channels)

    def setstate(self, state):
        self.toplevel.setplayerstate(state)
        # Set the playing state of the control panel.

        # Arguments (no defaults):
        # state -- the new state:
        #       STOPPED -- the player is in the stopped state
        #       PLAYING -- the player is in the playing state
        #       PAUSING -- the player is in the pausing state
##         ostate = self.__state
        self.__state = state


#               w = self.__window
#               if w is not None:
#                       if state == STOPPED:
#                               w.set_commandlist(self.stoplist,self.__cmdtgt)
#                       if state == PLAYING:
#                               w.set_commandlist(self.playlist,self.__cmdtgt)
#                       if state == PAUSING:
#                               w.set_commandlist(self.pauselist,self.__cmdtgt)
#                       if state != ostate:
#                               w.set_toggle(PLAY, state == PLAYING)
#                               w.set_toggle(PAUSE, state == PAUSING)
#                               w.set_toggle(STOP, state == STOPPED)
        self.setchannels(self.__channels)

    def getgeometry(self):
        # Get the coordinates of the control panel.

        # The return value is a tuple giving the coordinates
        # (x, y, width, height) in mm of the player control
        # panel.
        pass

    def get_adornments(self, channel):
        self.inst_adornments = {
                'close': [ CLOSE_WINDOW, ],
                'frame':self.toplevel.window,
                'view':self.__cmdtgt,
                }
        return self.inst_adornments
