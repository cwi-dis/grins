__version__ = "$Id$"

import windowinterface

class AnchorEditorDialog:
	def __init__(self, title, typelabels, list, initial):
		self.__window = w = windowinterface.Window(
			title, resizable = 1,
			deleteCallback = (self.cancel_callback, ()))

		buttons = w.ButtonRow(
			[('Cancel', (self.cancel_callback, ())),
			 ('Restore', (self.restore_callback, ())),
			 ('Apply', (self.apply_callback, ())),
			 ('OK', (self.ok_callback, ()))],
			bottom = None, left = None, right = None, vertical = 0)
		self.__composite = w.Label('Composite:', useGadget = 0,
					   bottom = buttons, left = None,
					   right = None)
		self.__type_choice = w.OptionMenu('Type:', typelabels, 0,
						  (self.type_callback, ()),
						  bottom = self.__composite,
						  left = None, right = None)
		self.__buttons = w.ButtonRow(
			[('New', (self.add_callback, ())),
			 ('Edit...', (self.edit_callback, ())),
			 ('Delete', (self.delete_callback, ())),
			 ('Export...', (self.export_callback, ()))],
			top = None, right = None)
		self.__anchor_browser = w.Selection(
			None, 'Id:', list, initial, (self.anchor_callback, ()),
			top = None, left = None, right = self.__buttons,
			bottom = self.__type_choice,
			enterCallback = (self.id_callback, ()))
		w.show()

	def close(self):
		# after this none of the methods may be called again
		self.__window.close()
		# delete some attributes so that GC can collect them
		del self.__window
		del self.__composite
		del self.__type_choice
		del self.__buttons
		del self.__anchor_browser

	def pop(self):
		self.__window.pop()

	def settitle(self, title):
		self.__window.settitle(title)

	def composite_hide(self):
		self.__composite.hide()

	def composite_show(self):
		self.__composite.show()

	def composite_setlabel(self, label):
		self.__composite.setlabel(label)

	def type_choice_hide(self):
		self.__type_choice.hide()

	def type_choice_show(self):
		self.__type_choice.show()

	def type_choice_setchoice(self, choice):
		self.__type_choice.setpos(choice)

	def type_choice_getchoice(self):
		return self.__type_choice.getpos()

	def type_choice_setsensitive(self, pos, sensitive):
		self.__type_choice.setsensitive(pos, sensitive)

	def edit_setsensitive(self, sensitive):
		self.__buttons.setsensitive(1, sensitive)

	def delete_setsensitive(self, sensitive):
		self.__buttons.setsensitive(2, sensitive)

	def export_setsensitive(self, sensitive):
		self.__buttons.setsensitive(3, sensitive)

	def selection_seteditable(self, editable):
		self.__anchor_browser.seteditable(editable)

	def selection_setlist(self, list, initial):
		self.__anchor_browser.delalllistitems()
		self.__anchor_browser.addlistitems(list, -1)
		self.__anchor_browser.selectitem(initial)

	def selection_setselection(self, pos):
		self.__anchor_browser.selectitem(pos)

	def selection_getselection(self):
		return self.__anchor_browser.getselected()

	def selection_append(self, item):
		self.__anchor_browser.addlistitem(item, -1)

	def selection_gettext(self):
		return self.__anchor_browser.getselection()

	def selection_replaceitem(self, pos, item):
		self.__anchor_browser.replacelistitem(pos, item)

	def selection_deleteitem(self, pos):
		self.__anchor_browser.dellistitem(pos)

	#
	# callbacks -- to be overridden
	#

	def cancel_callback(self):
		pass

	def restore_callback(self):
		pass

	def apply_callback(self):
		pass

	def ok_callback(self):
		pass

	def add_callback(self):
		pass

	def edit_callback(self):
		pass

	def delete_callback(self):
		pass

	def export_callback(self):
		pass

	def anchor_callback(self):
		pass

	def id_callback(self):
		pass

	def type_callback(self):
		pass
