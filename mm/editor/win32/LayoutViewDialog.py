__version__ = "$Id$"

import windowinterface
from usercmd import *

class LayoutViewDialog:
	def __init__(self):
		self.__window=None

	def createviewobj(self):
		w=windowinterface.newviewobj('lview_')
		self.__window = w

		self.__layoutlist=w._layoutlist
		self.__layoutlist.setcb((self.__layoutcb, ()))

		self.__channellist=w._channellist
		self.__channellist.setcb((self.__channelcb, ()))

		self.__otherlist=w._otherlist
		self.__otherlist.setcb((self.__othercb, ()))

	def destroy(self):
		if self.__window is None:
			return 
		self.__window.close()
		self.__window = None
		del self.__layoutlist
		del self.__channellist
		del self.__otherlist

	def show(self):
		self.assertwndcreated()	
		windowinterface.showview(self.__window,'lview_')

	def is_showing(self):
		if self.__window is None:
			return 0
		return self.__window.is_showing()

	def hide(self):
		if self.__window is not None:
			self.__window.hide()

	def assertwndcreated(self):
		if self.__window is None or not hasattr(self.__window,'GetSafeHwnd'):
			self.createviewobj()
		if self.__window.GetSafeHwnd()==0:
			windowinterface.createview(self.__window)	

	def setlayoutlist(self, layouts, cur):
		# the core should be corected but 
		# in order to proceed let fill the hole here
		self.assertwndcreated()
		if layouts != self.__layoutlist.getlist():
			self.__layoutlist.delalllistitems()
			self.__layoutlist.addlistitems(layouts, 0)
		if cur is not None:
			self.__layoutlist.selectitem(layouts.index(cur))
		else:
			self.__layoutlist.selectitem(None)

	def setchannellist(self, channels, cur):
		if channels != self.__channellist.getlist():
			self.__channellist.delalllistitems()
			self.__channellist.addlistitems(channels, 0)
		if cur is not None:
			self.__channellist.selectitem(channels.index(cur))
		else:
			self.__channellist.selectitem(None)

	def setotherlist(self, channels, cur):
		if channels != self.__otherlist.getlist():
			self.__otherlist.delalllistitems()
			self.__otherlist.addlistitems(channels, 0)
		if cur is not None:
			self.__otherlist.selectitem(channels.index(cur))

	def layoutname(self):
		return self.__layoutlist.getselection()

	def __layoutcb(self):
		sel = self.__layoutlist.getselected()
		if sel is None:
			self.curlayout = None
		else:
			self.curlayout = self.__layoutlist.getlistitem(sel)
		self.fill()

	def __channelcb(self):
		sel = self.__channellist.getselected()
		if sel is None:
			self.curchannel = None
		else:
			self.curchannel = self.__channellist.getlistitem(sel)
		self.fill()

	def __othercb(self):
		sel = self.__otherlist.getselected()
		if sel is None:
			self.curother = None
		else:
			self.curother = self.__otherlist.getlistitem(sel)
		self.fill()

	def setwaiting(self):
		windowinterface.setcursor('watch')
		#self.__window.setcursor('watch')

	def setready(self):
		windowinterface.setcursor('')
		#self.__window.setcursor('')

	def setcommandlist(self, commandlist):
		self.__window.set_commandlist(commandlist)

	def asklayoutname_X(self, default):
		windowinterface.InputDialog('Name for layout',
					    default,
					    self.newlayout_callback,
					    cancelCallback = (self.newlayout_callback, ()),
					    parent = self.__window)
	def asklayoutname(self, default):
		w=windowinterface.LayoutNameDlg()
		w.show()

	def askchannelnameandtype_X(self, default, types):
		w = windowinterface.Window('newchanneldialog', grab = 1,
					   parent = self.__window)
		self.__chanwin = w
		t = w.TextInput('Name for channel', default, None, None, left = None, right = None, top = None)
		self.__chantext = t
		o = w.OptionMenu('Choose type', types, 0, None, top = t, left = None, right = None)
		self.__chantype = o
		b = w.ButtonRow([('Cancel', (self.__okchannel, (0,))),
				 ('OK', (self.__okchannel, (1,)))],
				vertical = 0,
				top = o, left = None, right = None, bottom = None)
		w.show()

	def askchannelnameandtype(self, default, types):
		w=windowinterface.NewChannelDlg()
		w.show()

	def __okchannel(self, ok = 0):
		if ok:
			name = self.__chantext.gettext()
			type = self.__chantype.getvalue()
		else:
			name = type = None
		self.__chanwin.close()
		del self.__chantext
		del self.__chantype
		del self.__chanwin
		# We can't call this directly since we're still in
		# grab mode.  We must first return from this callback
		# before we're out of that mode, so we must schedule a
		# callback in the very near future.
		windowinterface.settimer(0.00001, (self.newchannel_callback, (name, type)))
