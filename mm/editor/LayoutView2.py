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
		self.toplevel.player.show()
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


	def new_callback(self):
		if not self.editmgr.transaction():
			return		# Not possible at this time
		base = 'NEW SCREEN '
		i = 1
		name = base + `i`
		while self.context.layouts.has_key(name):
			i = i+1
			name = base + `i`
		self.__newlayout = 1
		self.asklayoutname(name)

	def newlayout_callback(self, name = None):
		editmgr = self.editmgr
		if not name or (not self.__newlayout and name == self.curlayout):
			editmgr.rollback()
			return
		if self.context.layouts.has_key(name):
			import windowinterface
			editmgr.rollback()
			windowinterface.showmessage('screen name already exists')
			return
		self.toplevel.setwaiting()
		if self.__newlayout:
			editmgr.addlayout(name)
		else:
			editmgr.setlayoutname(self.curlayout, name)
		self.curlayout = name
		editmgr.commit()

	def rename_callback(self):
		if not self.editmgr.transaction():
			return		# Not possible at this time
		self.__newlayout = 0
		self.asklayoutname(self.curlayout)

	def new_channel_callback(self):
		if not self.curlayout:
			return
		if not self.editmgr.transaction():
			return		# Not possible at this time
		channeldict = self.context.channeldict
		import ChannelMap
		base = 'NEW'
		i = 1
		name = base + `i`
		while channeldict.has_key(name):
			i = i+1
			name = base + `i`
		self.askchannelnameandtype(name,
					ChannelMap.getvalidchanneltypes(self.context))

