__version__ = "$Id$"

from ParamgroupViewDialog import ParamgroupViewDialog
from ViewDialog import ViewDialog
import AttrEdit
from usercmd import *

class ParamgroupView(ParamgroupViewDialog, ViewDialog):
    def __init__(self, toplevel):
        self.toplevel = toplevel
        self.root = toplevel.root
        self.context = self.root.context
        self.editmgr = self.context.editmgr
        ParamgroupViewDialog.__init__(self)

    def fixtitle(self):
        pass

    def destroy(self):
        self.hide()
        ParamgroupViewDialog.destroy(self)

    def show(self):
        if self.is_showing():
            ParamgroupViewDialog.show(self)
            return
        self.commit()
        ParamgroupViewDialog.show(self)
        self.editmgr.register(self)

    def hide(self):
        if not self.is_showing():
            return
        self.editmgr.unregister(self)
        ParamgroupViewDialog.hide(self)

    def transaction(self,type):
        return 1        # It's always OK to start a transaction

    def rollback(self):
        pass

    def commit(self, type=None):
        paramgroups = self.context.paramgroups
        trnames = paramgroups.keys()
        trnames.sort()
        selection = self.getgroup()
        if selection is not None:
            if paramgroups.has_key(selection):
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
        self.editmgr.addparamgroup(name, {'trtype':'fade', 'startProgress': 0.0, 'endProgress': 1.0,})
        self.editmgr.commit()
        AttrEdit.showparamgroupattreditor(self.toplevel, name)

    def _findfreename(self):
        if not self.context.paramgroups.has_key('New Paramgroup'):
            return 'New Paramgroup'
        i = 1
        while 1:
            name = 'New Paramgroup %d'%i
            if not self.context.paramgroups.has_key(name):
                return name
            i = i + 1

    def edit_callback(self):
        sel = self.getgroup()
        if sel is None:
            # nothing selected
            raise 'Edit with no selection'
        trdict = self.context.paramgroups.get(sel)
        if trdict is None:
            # unknown paramgroup (internal error?)
            raise 'Edit with unknown selection'
        AttrEdit.showparamgroupattreditor(self.toplevel, sel)

    def delete_callback(self):
        sel = self.getgroup()
        if sel is None:
            # nothing selected
            return
        if not self.editmgr.transaction():
            return
        self.editmgr.delparamgroup(sel)
        self.editmgr.commit()
