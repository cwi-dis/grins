__version__ = "$Id$"

from UsergroupViewDialog import UsergroupViewDialog, UsergroupEditDialog
from usercmd import *

class UsergroupView(UsergroupViewDialog):
	def __init__(self, toplevel):
		self.toplevel = toplevel
		self.root = toplevel.root
		self.context = self.root.context
		self.editmgr = self.context.editmgr
		UsergroupViewDialog.__init__(self)
		self.editors = {}

	def fixtitle(self):
		pass
	def get_geometry(self):
		pass
	def save_geometry(self):
		pass

	def destroy(self):
		self.hide()
		UsergroupViewDialog.destroy(self)

	def show(self):
		if self.is_showing():
			return
		self.commit()
		UsergroupViewDialog.show(self)
		self.editmgr.register(self)

	def hide(self):
		if not self.is_showing():
			return
		self.editmgr.unregister(self)
		UsergroupViewDialog.hide(self)
		self.toplevel.showstate(self, 0)

	def transaction(self):
		return 1		# It's always OK to start a transaction

	def rollback(self):
		pass

	def commit(self):
		usergroups = self.context.usergroups
		for key in self.editors.keys():
			if not usergroups.has_key(key):
				self.editors[key].close()
		ugroups = usergroups.keys()
		ugroups.sort()
		selection = self.getgroup()
		if selection is not None:
			if usergroups.has_key(selection):
				selection = ugroups.index(selection)
			else:
				selection = None
		self.setgroups(ugroups, selection)

	def kill(self):
		self.destroy()

	def new_callback(self):
		UsergroupEdit(self)

	def edit_callback(self):
		ugroup = self.getgroup()
		if ugroup is None:
			# nothing selected
			return
		val = self.context.usergroups.get(ugroup)
		if val is None:
			# unknown group (internal error?)
			return
		editor = self.editors.get(ugroup)
		if editor is not None:
			editor.restore_callback()
			editor.show()
		else:
			title, state, override = val
			editor = UsergroupEdit(self, ugroup, title, state, override)
			self.editors[ugroup] = editor

	def delete_callback(self):
		ugroup = self.getgroup()
		if ugroup is None:
			# nothing selected
			return
		if not self.editmgr.transaction():
			return
		self.editmgr.delusergroup(ugroup)
		self.editmgr.commit()

class UsergroupEdit(UsergroupEditDialog):
	def __init__(self, parent, ugroup = '', title = '', ustate = 'RENDERED', override = 'allowed'):
		self.__parent = parent
		self.__usergroups = parent.context.usergroups
		self.__ugroup = ugroup
		self.__editmgr = parent.editmgr
		self.__editmgr.register(self)
		UsergroupEditDialog.__init__(self, ugroup, title, ustate, override)

	def transaction(self):
		return 1		# It's always OK to start a transaction

	def rollback(self):
		pass

	def commit(self):
		if self.__parent is not None:
			self.restore_callback()

	def kill(self):
		self.close()

	def close(self):
		self.__editmgr.unregister(self)
		UsergroupEditDialog.close(self)
		if self.__ugroup != '':
			del self.__parent.editors[self.__ugroup]
		self.__parent = None
		del self.__usergroups
		del self.__ugroup
		del self.__editmgr

	def cancel_callback(self):
		self.close()

	def restore_callback(self):
		if self.__ugroup == '':
			val = None
		else:
			val = self.__usergroups.get(self.__ugroup)
		if val is None:
			title, ustate, override = '', 'RENDERED', 'allowed'
		else:
			title, ustate, override = val
		self.setstate(self.__ugroup, title, ustate, override)

	def apply_callback(self):
		self.do_apply()

	def do_apply(self):
		ugroup, title, ustate, override = self.getstate()
		if not ugroup:
			self.showmessage('User group name is required')
			return 0
		if not self.__editmgr.transaction():
			return 0
		if self.__ugroup != '':
			# we're editing an existing one
			if not self.__usergroups.has_key(self.__ugroup):
				# hmm, it didn't exist after all
				self.showmessage('internal error')
				self.__editmgr.rollback()
				return 0
			if self.__ugroup != ugroup and \
			   self.__usergroups.has_key(ugroup):
				# trying to rename to existing name
				self.showmessage('Non-unique user group name')
				self.__editmgr.rollback()
				return 0
			self.__editmgr.delusergroup(self.__ugroup)
			del self.__parent.editors[self.__ugroup]
		elif self.__usergroups.has_key(ugroup):
			# this is a new one, but the name already exists
			self.showmessage('Non-unique user group name')
			self.__editmgr.rollback()
			return 0
		self.__editmgr.addusergroup(ugroup, (title, ustate, override))
		self.__ugroup = ugroup
		self.__parent.editors[self.__ugroup] = self
		self.__editmgr.commit()
		return 1

	def ok_callback(self):
		if self.do_apply():
			self.close()
