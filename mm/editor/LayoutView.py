__version__ = "$Id$"

from LayoutViewDialog import LayoutViewDialog
from usercmd import *

ALL_LAYOUTS = 'All combined'

class LayoutView(LayoutViewDialog):
	def __init__(self, toplevel):
		self.toplevel = toplevel
		self.root = toplevel.root
		self.context = self.root.context
		self.editmgr = self.context.editmgr
		self.curlayout = ALL_LAYOUTS
		self.curchannel = None
		self.curother = None
		LayoutViewDialog.__init__(self)

	def fixtitle(self):
		pass			# for now...
	def get_geometry(self):
		pass
	def save_geometry(self):
		pass

	def destroy(self):
		self.hide()
		LayoutViewDialog.destroy(self)

	def show(self):
		if self.is_showing():
			return
		self.fill()
		LayoutViewDialog.show(self)
		self.editmgr.register(self)

	def hide(self):
		if not self.is_showing():
			return
		self.editmgr.unregister(self)
		self.toplevel.player.setlayout(None, None)
		LayoutViewDialog.hide(self)
		self.toplevel.showstate(self, 0)

	def transaction(self):
		return 1		# It's always OK to start a transaction

	def rollback(self):
		pass

	def commit(self):
		self.fill()

	def kill(self):
		self.destroy()

	def fill(self):
		layouts = self.context.layouts.keys()
		layouts.sort()
		layouts.append(ALL_LAYOUTS)
		if self.curlayout is not None and \
		   self.curlayout != ALL_LAYOUTS and \
		   not self.context.layouts.has_key(self.curlayout):
			self.curlayout = None
		self.setlayoutlist(layouts, self.curlayout)
		chanlist = []
		layout = {}
		if self.curlayout is not None:
			if self.curlayout == ALL_LAYOUTS:
				channels = self.context.channels
			else:
				channels = self.context.layouts[self.curlayout]
			for ch in channels:
				chanlist.append(ch.name)
				layout[ch.name] = 0
			chanlist.sort()
		if self.curchannel is not None:
			if self.curlayout is None or \
			   not layout.has_key(self.curchannel):
				self.curchannel = None
		self.setchannellist(chanlist, self.curchannel)
		ochanlist = []
		curother = None
		for ch in self.context.channels:
			if not layout.has_key(ch.name):
				ochanlist.append(ch.name)
				if self.curother is not None and \
				   ch.name == self.curother:
					curother = ch.name
		ochanlist.sort()
		self.curother = curother
		self.setotherlist(ochanlist, curother)
		commandlist = [NEW_LAYOUT(callback = (self.new_callback, ())),
			       CLOSE_WINDOW(callback = (self.hide, ()))]
		if self.curlayout is not None and \
		   self.curlayout != ALL_LAYOUTS:
			commandlist.append(DELETE(callback = (self.delete_callback, ())))
			commandlist.append(NEW_CHANNEL(callback = (self.new_channel_callback, ())))
			commandlist.append(RENAME(callback = (self.rename_callback, ())))
			if self.curchannel is not None:
				commandlist.append(REMOVE_CHANNEL(callback = (self.remove_callback, ())))
			if self.curother is not None:
				commandlist.append(ADD_CHANNEL(callback = (self.add_callback, ())))
		elif self.curlayout == ALL_LAYOUTS:
			commandlist.append(NEW_CHANNEL(callback = (self.new_channel_callback, ())))
		if self.curchannel is not None:
			commandlist.append(ATTRIBUTES(callback = (self.attr_callback, ())))
		self.setcommandlist(commandlist)
		self.toplevel.player.setlayout(self.curlayout, self.curchannel)

	def new_callback(self):
		if not self.editmgr.transaction():
			return		# Not possible at this time
		base = 'NEW'
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
			editmgr.rollback()
			windowinterface.showmessage('layout name already exists')
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
		from ChannelMap import commonchanneltypes, otherchanneltypes
		base = 'NEW'
		i = 1
		name = base + `i`
		while channeldict.has_key(name):
			i = i+1
			name = base + `i`
		self.askchannelnameandtype(name,
					commonchanneltypes + otherchanneltypes)

	def newchannel_callback(self, name = None, type = None):
		editmgr = self.editmgr
		if not name:
			editmgr.rollback()
			return
		context = self.context
		if context.channeldict.has_key(name):
			editmgr.rollback()
			return
		self.toplevel.setwaiting()
		root = None
		for key, val in context.channeldict.items():
			if val.get('base_window') is None:
				# we're looking at a top-level channel
				if root is None:
					# first one
					root = key
				else:
					# multiple top-level channels
					root = ''
		editmgr.addchannel(name, len(self.context.channels), type)
		ch = context.channeldict[name]
		if root:
			ch['base_window'] = root
		if self.curlayout != ALL_LAYOUTS:
			editmgr.addlayoutchannel(self.curlayout, ch)
		self.curchannel = name
		editmgr.commit()

	def delete_callback(self):
		if self.curlayout is None:
			return
		editmgr = self.editmgr
		if not editmgr.transaction():
			return		# Not possible at this time
		self.toplevel.setwaiting()
		editmgr.dellayout(self.curlayout)
		self.curlayout = None
		editmgr.commit()

	def remove_callback(self):
		if self.curlayout is None or self.curchannel is None:
			return
		editmgr = self.editmgr
		if not editmgr.transaction():
			return		# Not possible at this time
		self.toplevel.setwaiting()
		editmgr.dellayoutchannel(self.curlayout,
				self.context.channeldict[self.curchannel])
		self.curchannel = None
		editmgr.commit()

	def attr_callback(self):
		if self.curlayout is None or self.curchannel is None:
			return
		self.toplevel.setwaiting()
		import AttrEdit
		AttrEdit.showchannelattreditor(self.toplevel,
				self.context.channeldict[self.curchannel])

	def add_callback(self):
		if self.curlayout is None or self.curother is None:
			return
		editmgr = self.editmgr
		if not editmgr.transaction():
			return		# Not possible at this time
		self.toplevel.setwaiting()
		editmgr.addlayoutchannel(self.curlayout, self.context.channeldict[self.curother])
		self.curchannel = self.curother
		self.curother = None
		editmgr.commit()
