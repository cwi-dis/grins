__version__ = "$Id$"

import windowinterface, WMEVENTS
from usercmd import *
import EasyDialogs

class TopLevelDialog:
    def __init__(self):
        self._do_show()

    def _do_show(self):
        if self.window is not None:
            return
        self.window = windowinterface.windowgroup(self.basename, self.commandlist)

    def show(self):
        self._do_show()

    def hide(self):
        if self.window is None:
            return
        self.window.close()
        self.window = None

    def setbuttonstate(self, command, showing):
        self.window.set_toggle(command, showing)

    def setsettingsdict(self, dict):
        pass

    def showsource(self, source = None, optional=0):
        if optional and self.source and self.source.is_closed():
            self.source = None
            return
        if source is None:
            if self.source is not None:
                if not self.source.is_closed():
                    self.source.close()
                self.source = None
            return
        if self.source is not None:
            self.source.settext(source)
            self.source.show()
            return
        self.source = windowinterface.textwindow(source)

    # set the list of command specific to the system
    def set_commandlist(self):
        pass

    def setcommands(self, commandlist):
        self.window.set_commandlist(commandlist)
