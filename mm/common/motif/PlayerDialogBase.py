__version__ = "$Id$"

import windowinterface
from usercmd import *
from flags import *
import playbutton, playbuttonunselect
import pausebutton, pausebuttonunselect
import stopbutton, stopbuttonunselect

STOPPED, PAUSING, PLAYING = range(3)

class PlayerDialogBase:
    adornments = {
            'toolbar': [
                    (FLAG_ALL,
                     {'label': playbuttonunselect.reader(),
                      'labelInsensitive': playbuttonunselect.reader(),
                      'select': playbutton.reader(),
                      'selectInsensitive': playbutton.reader(),
                      }, PLAY, 't'),
                    (FLAG_ALL,
                     {'label': pausebuttonunselect.reader(),
                      'labelInsensitive': pausebuttonunselect.reader(),
                      'select': pausebutton.reader(),
                      'selectInsensitive': pausebutton.reader(),
                      }, PAUSE, 't'),
                    (FLAG_ALL,
                     {'label': stopbuttonunselect.reader(),
                      'labelInsensitive': stopbuttonunselect.reader(),
                      'select': stopbutton.reader(),
                      'selectInsensitive': stopbutton.reader(),
                      }, STOP, 't'),
                    ],
            }

    def __init__(self, coords, title):
        """Create the Player dialog.

        Create the dialog window (non-modal, so does not grab
        the cursor) but do not pop it up (i.e. do not display
        it on the screen).

        Arguments (no defaults):
        coords -- the coordinates (x, y, width, height) of the
                control panel in mm
        title -- string to be displayed as window title
        """

        self._window = None
        self.__title = title
        self.__coords = coords
        self.__state = -1
        self.__channels = []
        self.__channeldict = {}
        self.menu_created = None

    def close(self):
        """Close the dialog and free resources."""
        if self._window is not None:
            self._window.close()
            self._window = None
        del self.__channels
        del self.__channeldict
        del self.menu_created

    def preshow(self):
        """Called before showing the channels."""
        pass

    def show(self, subwindowof=None):
        """Show the control panel."""

        if self._window is not None:
            self._window.pop()
            return
        self.__state = -1
        if self.__coords:
            x, y = self.__coords[:2]
        else:
            x = y = None
        if subwindowof is not None:
            raise 'kaboo kaboo'
        self.adornments['flags'] = curflags()
        self._window = w = windowinterface.newwindow(
                x, y, 0, 0, self.__title, resizable = 0,
                adornments = self.adornments,
                commandlist = self.stoplist)
        if self.__channels:
            self.setchannels()

    def hide(self):
        """Hide the control panel."""

        if self._window is None:
            return
        self._window.close()
        self._window = None

    def settitle(self, title):
        """Set (change) the title of the window.

        Arguments (no defaults):
        title -- string to be displayed as new window title.
        """
        self.__title = title
        if self._window is not None:
            self._window.settitle(title)

    def setchannels(self, channels = None):
        """Set the list of channels.

        Arguments (no defaults):
        channels -- a list of tuples (name, onoff) where name
                is the channel name which is to be presented
                to the user, and onoff indicates whether the
                channel is on or off (1 if on, 0 if off)
        """

        if channels is None:
            channels = self.__channels
        else:
            self.__channels = channels
        self.__channeldict = {}
        menu = []
        for i in range(len(channels)):
            channel, onoff = channels[i]
            self.__channeldict[channel] = i
            if self.menu_created is not None and \
               channel == self.menu_created._name:
                continue
            menu.append((channel, (channel,), 't', onoff))
        if self.menu_created is not None:
            w = self.menu_created.window
        else:
            w = self._window
        if w is not None:
            w.set_dynamiclist(CHANNELS, menu)

    def setchannel(self, channel, onoff):
        """Set the on/off status of a channel.

        Arguments (no defaults):
        channel -- the name of the channel whose status is to
                be set
        onoff -- the new status
        """

        i = self.__channeldict.get(channel)
        if i is None:
            raise RuntimeError, 'unknown channel'
        if self.__channels[i][1] == onoff:
            return
        self.__channels[i] = channel, onoff
        self.setchannels()

    def setstate(self, state = None):
        """Set the playing state of the control panel.

        Arguments (no defaults):
        state -- the new state:
                STOPPED -- the player is in the stopped state
                PLAYING -- the player is in the playing state
                PAUSING -- the player is in the pausing state
        """

        if state is None:
            state = self.__state
        ostate = self.__state
        self.__state = state
        w = self._window
        if w is None and self.menu_created is not None:
            if hasattr(self.menu_created, 'window'):
                w = self.menu_created.window
        if w is not None:
            if state == STOPPED:
                w.set_commandlist(self.stoplist)
            if state == PLAYING:
                w.set_commandlist(self.playlist)
            if state == PAUSING:
                w.set_commandlist(self.pauselist)
            self.setchannels()
            if state != ostate:
                w.set_toggle(PLAY, state != STOPPED)
                w.set_toggle(PAUSE, state == PAUSING)
                w.set_toggle(STOP, state == STOPPED)

    def getgeometry(self):
        """Get the coordinates of the control panel.

        The return value is a tuple giving the coordinates
        (x, y, width, height) in mm of the player control
        panel.
        """

        if self._window is not None:
            return self._window.getgeometry(windowinterface.UNIT_PXL)
