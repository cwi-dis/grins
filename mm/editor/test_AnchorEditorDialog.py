"""Test AnchorEditorDialog, editor specifics"""

__version__ = "$Id$"

import sys
import os

if os.name == 'posix':
	sys.path.append("../lib")
elif os.name == 'mac':
	sys.path.append("::lib")
	sys.path.append("::mac")
	sys.path.insert(0, ":mac")
# etc...


from AnchorEditDialog import AnchorEditorDialog

class AnchorEditorTest(AnchorEditorDialog):
	__typelabels = ['dest only', 'normal', 'pausing', 'auto-firing',
			'composite', 'with arguments']
	__names = ['name 1', 'name 2', 'name 3']
	def __init__(self):
		AnchorEditorDialog.__init__(self, 'AnchorEditor test',
					    self.__typelabels,
					    self.__names, None)
		self.__setfocus()
	def cancel_callback(self):
		import sys
		print 'Cancel pressed'
		self.close()
		sys.exit(0)
	def apply_callback(self):
		print 'Apply pressed'
		print 'Type choice is', \
		      self.__typelabels[self.type_choice_getchoice()]
		print 'Selection is', self.selection_getselection()
	def ok_callback(self):
		import sys
		print 'OK pressed'
		self.close()
		sys.exit(0)
	def restore_callback(self):
		self.settitle('AnchorEditor Restore test')
		self.__names = ['new name 1','new name 2']
		self.selection_setlist(self.__names, None)
		self.__setfocus()
	def id_callback(self):
		id = self.selection_gettext()
		focus = self.selection_getselection()
		print 'New id for current choice:', id
		print '(old id is %s)' % self.__names[focus]
		self.__names[focus] = id
		self.selection_replaceitem(focus, id)
		self.selection_setselection(focus)
	def __setfocus(self):
		focus = self.selection_getselection()
		if focus is None:
			self.edit_setsensitive(0)
			self.delete_setsensitive(0)
			self.selection_seteditable(0)
			self.export_setsensitive(0)
			self.type_choice_hide()
			self.composite_hide()
		else:
			self.edit_setsensitive(1)
			self.delete_setsensitive(1)
			self.selection_seteditable(1)
			self.export_setsensitive(1)
			self.type_choice_show()
			self.composite_show()
			self.type_choice_setchoice(5 - focus % 6)
			self.type_choice_setsensitive(1, 1)
			self.type_choice_setsensitive(0, focus % 2)
			self.type_choice_setsensitive(3, 1)
			self.type_choice_setsensitive(2, focus % 2)
			self.type_choice_setsensitive(5, 1)
			self.type_choice_setsensitive(4, focus % 2)
	def anchor_callback(self):
		focus = self.selection_getselection()
		if focus is None:
			print 'No new selection'
		else:
			print 'New selection is', self.__names[focus]
		self.__setfocus()
	def delete_callback(self):
		focus = self.selection_getselection()
		print 'Deleting', self.__names[focus]
		del self.__names[focus]
		self.selection_deleteitem(focus)
		self.selection_setselection(None)
		self.__setfocus()
	def add_callback(self):
		maxid = 0
		for id in self.__names:
			try:
				id = eval('0+'+id)
			except:
				pass
			if type(id) is type(0) and id > maxid:
				maxid = id
		name = `maxid + 1`
		print 'Adding',name
		self.__names.append(name)
		self.selection_append(name)
		focus = len(self.__names) - 1
		self.selection_setselection(focus)
		self.__setfocus()
	def type_callback(self):
		print 'New type',\
		      self.__typelabels[self.type_choice_getchoice()]
	def edit_callback(self):
		print 'Edit button pressed'
	def export_callback(self):
		print 'Export button pressed'
			
import windowinterface
print 'Creating AnchorEditorDialog...'
dialog = AnchorEditorTest()
print 'Play with the controls and select "Apply" every time.'
print 'Select "Restore" to restore to initial setting'
print '(check that window title changes!)'
print 'When done, select "OK" or "Cancel".'
try:
	windowinterface.mainloop()
except SystemExit:
	pass
print 'exiting...'
