"""Dialog for the Assets View.

"""

__version__ = "$Id$"

import windowinterface
from usercmd import *

class AssetsViewDialog:
	def __init__(self):
		self.__window = None
		self.__callbacks={
##			'New':(self.new_callback, ()),
##			'Edit':(self.edit_callback, ()),
##			'Delete':(self.delete_callback, ()),
			'setview': self.setview_callback,
			'select': self.select_callback,
			'sort': self.sort_callback,
			'startdrag': self.startdrag_callback,
			 }

	def destroy(self):
		if self.__window is None:
			return
		if hasattr(self.__window,'_obj_') and self.__window._obj_:
			self.__window.close()
		self.__window = None

	def show(self):
		self.assertwndcreated()	
		self.__window.show()

	def is_showing(self):
		if self.__window is None:
			return 0
		return self.__window.is_showing()

	def hide(self):
		if self.__window is not None:
			self.__window.close()
			self.__window = None
			f=self.toplevel.window

	def setlistheaders(self, headerlist):
		self.__window.setColumns(headerlist)

	def setlistdata(self, data):
		self.__window.setItems(data)
		self.__window.rebuildList()

	def setviewbutton(self, which):
		self.__window.setView(which)

	def setcommandlist(self, commandlist):
		self.__window.set_commandlist(commandlist)

	def getselection(self):
		return self.__window.getSelected()

	def dodragdrop(self, type, value):
		rv = self.__window.doDragDrop(type, value)
		if rv == windowinterface.DROPEFFECT_MOVE:
			return 'move'
		elif rv == windowinterface.DROPEFFECT_COPY:
			return 'copy'
		else:
			return None

#### support win32 model
	def createviewobj(self):
		if self.__window: return
		f=self.toplevel.window
		w=f.newviewobj('aview_')
		w.set_cmddict(self.__callbacks)
		self.__window = w

	def assertwndcreated(self):
		if self.__window is None or not hasattr(self.__window,'GetSafeHwnd'):
			self.createviewobj()
		if self.__window.GetSafeHwnd()==0:
			f=self.toplevel.window
			f.showview(self.__window,'aview_')
			self.__window.show()

	def getwindow(self):
		return self.__window
