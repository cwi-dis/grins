__version__ = "$Id$"

from AssetsViewDialog import AssetsViewDialog
from usercmd import *

class AssetsView(AssetsViewDialog):
	def __init__(self, toplevel):
		self.toplevel = toplevel
		self.root = toplevel.root
		self.context = self.root.context
		self.editmgr = self.context.editmgr
		AssetsViewDialog.__init__(self)

	def fixtitle(self):
		pass
	def get_geometry(self):
		pass
	def save_geometry(self):
		pass

	def destroy(self):
		self.hide()
		AssetsViewDialog.destroy(self)

	def show(self):
		if self.is_showing():
			AssetsViewDialog.show(self)
			return
##		self.commit()
		AssetsViewDialog.show(self)
##		self.editmgr.register(self)

	def hide(self):
		if not self.is_showing():
			return
##		self.editmgr.unregister(self)
		AssetsViewDialog.hide(self)

	def transaction(self,type):
		return 1		# It's always OK to start a transaction

	def rollback(self):
		pass

##	def commit(self, type=None):
##		transitions = self.context.transitions
##		trnames = transitions.keys()
##		trnames.sort()
##		selection = self.getgroup()
##		if selection is not None:
##			if transitions.has_key(selection):
##				selection = trnames.index(selection)
##			else:
##				selection = None
##		self.setgroups(trnames, selection)

	def kill(self):
		self.destroy()

