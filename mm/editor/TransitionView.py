__version__ = "$Id$"

from TransitionViewDialog import TransitionViewDialog
from ViewDialog import ViewDialog
import AttrEdit
from usercmd import *

class TransitionView(TransitionViewDialog, ViewDialog):
    def __init__(self, toplevel):
        self.toplevel = toplevel
        self.root = toplevel.root
        self.context = self.root.context
        self.editmgr = self.context.editmgr
        TransitionViewDialog.__init__(self)

    def fixtitle(self):
        pass

    def destroy(self):
        self.hide()
        TransitionViewDialog.destroy(self)

    def show(self):
        if self.is_showing():
            TransitionViewDialog.show(self)
            return
        self.commit()
        TransitionViewDialog.show(self)
        self.editmgr.register(self)

    def hide(self):
        if not self.is_showing():
            return
        self.editmgr.unregister(self)
        TransitionViewDialog.hide(self)

    def transaction(self,type):
        return 1                # It's always OK to start a transaction

    def rollback(self):
        pass

    def commit(self, type=None):
        transitions = self.context.transitions
        trnames = transitions.keys()
        trnames.sort()
        selection = self.getgroup()
        if selection is not None:
            if transitions.has_key(selection):
                selection = trnames.index(selection)
            else:
                selection = None
        self.setgroups(trnames, selection)

    def kill(self):
        self.destroy()

    def new_callback(self):
        if not self.editmgr.transaction():
            return
        name = self._findfreename()
        self.editmgr.addtransition(name, {'trtype':'fade', 'startProgress': 0.0, 'endProgress': 1.0,})
        self.editmgr.commit()
        AttrEdit.showtransitionattreditor(self.toplevel, name)

    def _findfreename(self):
        if not self.context.transitions.has_key('New Transition'):
            return 'New Transition'
        i = 1
        while 1:
            name = 'New Transition %d'%i
            if not self.context.transitions.has_key(name):
                return name
            i = i + 1

    def edit_callback(self):
        sel = self.getgroup()
        if sel is None:
            # nothing selected
            raise 'Edit with no selection'
        trdict = self.context.transitions.get(sel)
        if trdict is None:
            # unknown transition (internal error?)
            raise 'Edit with unknown selection'
        AttrEdit.showtransitionattreditor(self.toplevel, sel)

    def delete_callback(self):
        sel = self.getgroup()
        if sel is None:
            # nothing selected
            return
        if not self.editmgr.transaction():
            return
        self.editmgr.deltransition(sel)
        self.editmgr.commit()
