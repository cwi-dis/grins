"""Dialog for the Usergroup View.

The Usergroup View is a window that displays a list of user groups and
gives the ability to edit these user groups.

"""

__version__ = "$Id$"

import windowinterface
from usercmd import *
IMPL_AS_FORM=1

class UsergroupViewDialog:
	def __init__(self):
		self.__window = None
		self.__callbacks={
			'New':(self.new_callback, ()),
			'Edit':(self.edit_callback, ()),
			'Delete':(self.delete_callback, ()),
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

#### support win32 model
	def createviewobj(self):
		if self.__window: return
		f=self.toplevel.window
		w=f.newviewobj('ugview_')
		w.set_cmddict(self.__callbacks)
		self.__window = w

	def assertwndcreated(self):
		if self.__window is None or not hasattr(self.__window,'GetSafeHwnd'):
			self.createviewobj()
		if self.__window.GetSafeHwnd()==0:
			f=self.toplevel.window
			if IMPL_AS_FORM: # form
				f.showview(self.__window,'ugview_')
				self.__window.show()
			else: # dlgbar
				f=self.toplevel.window
				self.__window.create(f)

	def getwindow(self):
		return self.__window

#### data interchange
	def getgroup(self):
		"""Return name of currently selected user group."""
		if not self.__window:self.createviewobj()
		return self.__window.getgroup()

	def setgroups(self, ugroups, pos):
		"""Set the list of user groups.

		Arguments (no defaults):
		ugroups -- list of strings giving the names of the user groups
		pos -- None or index in ugroups list--the initially
			selected element in the list
		"""
		if not self.__window:self.createviewobj()
		self.__window.setgroups(ugroups, pos)


class UsergroupEditDialog:
	def __init__(self, ugroup, title, ustate, override):
		"""Create the UsergroupEdit dialog.

		Create the dialog window (non-modal, so does not grab
		the cursor) and pop it up.
		"""
		cbdict = {
			'Cancel':(self.cancel_callback, ()),
			'Restore':(self.restore_callback, ()),
			'Apply':(self.apply_callback, ()),
			'OK':(self.ok_callback, ()),
			}
		w=self.getparent().getwindow()
		self.__window=w=windowinterface.UsergroupEditDialog(w)
		w.do_init(ugroup, title, ustate, override, cbdict)
		w.show()

	def showmessage(self, text):
		windowinterface.showmessage(text, parent = self.__window)

	def show(self):
		"""Show the dialog (pop it up again)."""
		self.__window.show()

	def close(self):
		"""Close the dialog."""
		self.__window.close()
		self.__window = None

	def setstate(self, ugroup, title, ustate, override):
		"""Set the values in the dialog.

		Arguments (no defaults):
		ugroup -- string name of the user group
		title -- string title of the user group
		ustate -- string 'RENDERED' or 'NOT RENDERED'
		override -- string 'allowed' or 'not allowed'
		"""
		self.__window.setstate(ugroup, title, ustate, override)

	def getstate(self):
		"""Return the current values in the dialog."""
		return self.__window.getstate()
