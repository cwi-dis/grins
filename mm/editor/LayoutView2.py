# experimental layout view

from LayoutViewDialog2 import LayoutViewDialog2
from usercmd import *

ALL_LAYOUTS = '(All Channels)'

class LayoutView2(LayoutViewDialog2):
	def __init__(self, toplevel):
		self.toplevel = toplevel
		self.root = toplevel.root
		self.context = self.root.context
		self.editmgr = self.context.editmgr
		LayoutViewDialog2.__init__(self)

	def fixtitle(self):
		pass			# for now...
	def get_geometry(self):
		pass
	def save_geometry(self):
		pass

	def destroy(self):
		self.hide()
		LayoutViewDialog2.destroy(self)

	def show(self):
		if self.is_showing():
			LayoutViewDialog2.show(self)
			return
		LayoutViewDialog2.show(self)
#		self.editmgr.register(self)

	def hide(self):
		if not self.is_showing():
			return
#		self.editmgr.unregister(self)
		LayoutViewDialog2.hide(self)

	def transaction(self):
		return 1		# It's always OK to start a transaction

	def rollback(self):
		pass

	def commit(self):
		self.fill()

	def kill(self):
		self.destroy()

	#
	# interface implementation of 'previous control callback' 
	#

	def onRegionSelected(self):
		print 'onRegionSelected callback : not implemented'

	def onRegionMoved(self):
		print 'onRegionMoved callback : not implemented'

	def onRegionResized(self):
		print 'onRegionResized callback : not implemented'
				
	#
	# end interface implementation of 'previous control callback' 
	#

