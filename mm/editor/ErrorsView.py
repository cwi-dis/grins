__version__ = "$Id$"

from ErrorsViewDialog import ErrorsViewDialog
import AttrEdit
from usercmd import *

class ErrorsView(ErrorsViewDialog):
    def __init__(self, toplevel):
        self.toplevel = toplevel
        self.root = toplevel.root
        self.context = self.root.context
        self.editmgr = self.context.editmgr
        ErrorsViewDialog.__init__(self)

        self._selectedError     = None
        self._listener = None

    def fixtitle(self):
        pass

    def destroy(self):
        self.hide()
        ErrorsViewDialog.destroy(self)

    def show(self):
        if self.is_showing():
            ErrorsViewDialog.show(self)
            self.updateErrors()
            return
        ErrorsViewDialog.show(self)
        self.editmgr.register(self)
        self.updateErrors()

    def hide(self):
        if not self.is_showing():
            return
        self.editmgr.unregister(self)
        ErrorsViewDialog.hide(self)

    def transaction(self,type):
        return 1                # It's always OK to start a transaction

    def rollback(self):
        pass

    def updateErrors(self):
        parseErrors = self.context.getParseErrors()
        if parseErrors != None:
            self.setErrorList(parseErrors.getErrorList())

    def commit(self, type=None):
        pass

    def kill(self):
        self.destroy()

    def setListener(self, listener):
        self._listener = listener

    def removeListener(self, listener):
        if listener == self._listener:
            self._listener = None

    def onItemSelected(self, lineNumber, pop=0):
        self._selectedError = lineNumber
        if self._listener != None:
            self._listener.onSelectError(lineNumber, pop)

    def getSelectedError(self):
        if self._selectedError != None:
            return self._selectedError
