__version__ = "$Id$"

import windowinterface
from usercmd import *
import Qd

def ITEMrange(fr, to): return range(fr, to+1)

ID_DIALOG_LAYOUT=526

ITEM_LAYOUT_LIST=4
ITEM_LAYOUT_NEW=5
ITEM_LAYOUT_RENAME=6
ITEM_LAYOUT_DELETE=7

ITEM_CHANNEL_LIST=8
ITEM_CHANNEL_NEW=9
ITEM_CHANNEL_REMOVE=10
ITEM_CHANNEL_ATTRS=11

ITEM_OCHANNEL_LIST=12
ITEM_OCHANNEL_ADD=13

ITEMLIST_ALL=ITEMrange(1, ITEM_OCHANNEL_ADD)

ITEM_TO_COMMAND={
	ITEM_LAYOUT_NEW: NEW_LAYOUT,
	ITEM_LAYOUT_RENAME: RENAME,
	ITEM_LAYOUT_DELETE: DELETE,
	ITEM_CHANNEL_NEW: NEW_CHANNEL,
	ITEM_CHANNEL_REMOVE: REMOVE_CHANNEL,
	ITEM_CHANNEL_ATTRS: ATTRIBUTES,
	ITEM_OCHANNEL_ADD: ADD_CHANNEL,
}

class LayoutViewDialog(windowinterface.MACDialog):
	
	def __init__(self):
		windowinterface.MACDialog.__init__(self, 'Layout', ID_DIALOG_LAYOUT,
				ITEMLIST_ALL, cmdbuttons=ITEM_TO_COMMAND)
		self.__layoutlist = self._window.ListWidget(ITEM_LAYOUT_LIST)
		self.__channellist = self._window.ListWidget(ITEM_CHANNEL_LIST)
		self.__otherlist = self._window.ListWidget(ITEM_OCHANNEL_LIST)

	def destroy(self):
		self.close()
		del self.__layoutlist
		del self.__channellist
		del self.__otherlist
			
	def do_itemhit(self, item, event):
		if item == ITEM_LAYOUT_LIST:
			self._listclick(event, self.__layoutlist, self.__layoutcb, ())
		elif item == ITEM_CHANNEL_LIST:
			self._listclick(event, self.__channellist, self.__channelcb, ())
		elif item == ITEM_OCHANNEL_LIST:
			self._listclick(event, self.__otherlist, self.__othercb, ())
		else:
			print 'LayoutViewDialog: unexpected item/event:', item, event
		return 1

	def _listclick(self, event, list, cbfunc, cbarg):
		(what, message, when, where, modifiers) = event
		Qd.SetPort(self._window._wid)
		where = Qd.GlobalToLocal(where)
		old_select = list.getselect()
		item, is_double = list.click(where, modifiers)
		if old_select != item:
			apply(cbfunc, cbarg)

	def setlayoutlist(self, layouts, cur):
		if layouts != self.__layoutlist.get():
			self.__layoutlist.set(layouts)
		if cur is not None:
			self.__layoutlist.select(layouts.index(cur))
		else:
			self.__layoutlist.select(None)

	def setchannellist(self, channels, cur):
		if channels != self.__channellist.get():
			self.__channellist.set(channels)
		if cur is not None:
			self.__channellist.select(channels.index(cur))
		else:
			self.__channellist.select(None)

	def setotherlist(self, channels, cur):
		if channels != self.__otherlist.get():
			self.__otherlist.set(channels)
		if cur is not None:
			self.__otherlist.select(channels.index(cur))
		else:
			self.__otherlist.select(None)

	def __layoutcb(self):
		sel = self.__layoutlist.getselect()
		if sel is None:
			self.curlayout = None
		else:
			self.curlayout = self.__layoutlist.getitem(sel)
		self.fill()

	def __channelcb(self):
		sel = self.__channellist.getselect()
		if sel is None:
			self.curchannel = None
		else:
			self.curchannel = self.__channellist.getitem(sel)
		self.fill()

	def __othercb(self):
		sel = self.__otherlist.getselect()
		if sel is None:
			self.curother = None
		else:
			self.curother = self.__otherlist.getitem(sel)
		self.fill()

	def setwaiting(self):
		pass

	def setready(self):
		pass

	def setcommandlist(self, commandlist):
		self._window.set_commandlist(commandlist)

	def asklayoutname(self, default):
		windowinterface.InputDialog('Name for layout',
					    default,
					    self.newlayout_callback,
					    cancelCallback = (self.newlayout_callback, ()))

	def askchannelnameandtype(self, default, types):
		w = windowinterface.NewChannelDialog("New channel", default, types, 
					self.__okchannel, self.__okchannel)
		w.show()
		w.rungrabbed()

	def __okchannel(self, name=None, type=None):
		print 'OKCHANNEL', name, type
##		self.__chanwin.close()
##		del self.__chanwin
##		# We can't call this directly since we're still in
##		# grab mode.  We must first return from this callback
##		# before we're out of that mode, so we must schedule a
##		# callback in the very near future.
##		windowinterface.settimer(0.00001, (self.newchannel_callback, (name, type)))
		self.newchannel_callback(name, type)
