"""Dialog for the Attribute Editor.

The Attribute editor dialog consists of four buttons that are always
present (`Cancel', `Restore', `Apply', and `OK'), and a row of
attribute editor fields.  The number and type of these fields are
determined at run time, but there are only a limited number of
different types.  The fields are represented by instances of
sub-classes of the AttrEditorDialogField.  A list of these instances
is passed to the constructor of the AttrEditorDialog class.

Each of the attribute editor fields has a label with the name of the
attribute, an interface to edit the value (the interface depends on
the type of the value), and a `Reset' button.  There are two callbacks
associated with an attribute editor field, one to get help, and one
that is called when the `Reset' button is pressed.  There are also
some methods to get and set the current value of the attribute.

The base class of the AttrEditorDialogField class must provide some
methods also.

"""

__version__ = "$Id$"

import Dlg
import Qd
import string
import windowinterface
import WMEVENTS

def ITEMrange(fr, to): return range(fr, to+1)
# Dialog info
ID_DIALOG_NODEATTR=523

ITEM_SELECT=1
ITEM_INFO=2
ITEM_RESET=3

ITEM_CANCEL=4
ITEM_RESTORE=5
ITEM_APPLY=6
ITEM_OK=7

LAST_COMMON_ITEM=7
ITEMLIST_COMMON=ITEMrange(ITEM_SELECT, ITEM_OK)

# Variant items
ITEM_STRING=8

ITEM_FILE_BROWSE=9

ITEM_OPTION=10

ITEMLIST_NOTCOMMON=ITEMrange(ITEM_STRING, ITEM_OPTION)
ITEMLIST_STRING=[ITEM_STRING]
ITEMLISTNOT_STRING=[ITEM_FILE_BROWSE, ITEM_OPTION]
ITEMLIST_OPTION=[ITEM_OPTION]
ITEMLISTNOT_OPTION=[ITEM_FILE_BROWSE, ITEM_STRING]
ITEMLIST_FILE=[ITEM_STRING, ITEM_FILE_BROWSE]
ITEMLISTNOT_FILE=[ITEM_OPTION]

ITEMLIST_ALL=ITEMrange(ITEM_SELECT, ITEM_OPTION)

class AttrEditorDialog(windowinterface.MACDialog):
	def __init__(self, title, attriblist):
		"""Create the AttrEditor dialog.

		Create the dialog window (non-modal, so does not grab
		the cursor) and pop it up (i.e. display it on the
		screen).

		Arguments (no defaults):
		title -- string to be displayed as the window title
		attriblist -- list of instances of subclasses of
			AttrEditorDialogField
		"""
		windowinterface.MACDialog.__init__(self, title, ID_DIALOG_NODEATTR,
				ITEMLIST_ALL, default=ITEM_OK, cancel=ITEM_CANCEL)

		self._option = windowinterface.SelectWidget(self._dialog, ITEM_OPTION,
				[], None)

		self._attrfields = attriblist[:]
		self._cur_attrfield = None
		browser_values = []
		for a in self._attrfields:
			label = a._createwidget(self)
			browser_values.append(label)
		tp, h, rect = self._dialog.GetDialogItem(ITEM_SELECT)
		self._attrbrowser = self._window.ListWidget(rect, browser_values)
		self._selectattr(0)
		
		self.show()
##		w = windowinterface.Window(title, resizable = 1,
##				deleteCallback = (self.cancel_callback, ()))
##		self.__window = w
##		buttons = w.ButtonRow(
##			[('Cancel', (self.cancel_callback, ())),
##			 ('Restore', (self.restore_callback, ())),
##			 ('Apply', (self.apply_callback, ())),
##			 ('OK', (self.ok_callback, ())),
##			 ],
##			left = None, right = None, bottom = None, vertical = 0)
##		sep = w.Separator(left = None, right = None, bottom = buttons)
##		form = w.SubWindow(left = None, right = None, top = None,
##				   bottom = sep)
##		height = 1.0 / len(attriblist)
##		helpb = rstb = wdg = None # "upstairs neighbors"
##		self.__buttons = []
##		for i in range(len(attriblist)):
##			a = attriblist[i]
##			bottom = (i + 1) *  height
##			helpb = form.Button(a.getlabel(),
##					    (a.help_callback, ()),
##					    left = None, top = helpb,
##					    right = 0.5, bottom = bottom)
##			rstb = form.Button('Reset',
##					   (a.reset_callback, ()),
##					   right = None, top = rstb,
##					   bottom = bottom)
##			wdg = a._createwidget(self, form,
##					      left = helpb, right = rstb,
##					      top = wdg, bottom = bottom)
##		w.show()

	def close(self):
		self._option.delete()
		del self._attrbrowser
		del self._attrfields
		windowinterface.MACDialog.close(self)

	def do_itemhit(self, item, event):
		if item == ITEM_SELECT:
			(what, message, when, where, modifiers) = event
			Qd.SetPort(self._dialog)
			where = Qd.GlobalToLocal(where)
			item, is_double = self._attrbrowser.click(where, modifiers)
			self._selectattr(item)		
		elif item == ITEM_RESET:
			if self._cur_attrfield:
				self._cur_attrfield.reset_callback()
		elif item == ITEM_STRING:
			pass
		elif item == ITEM_FILE_BROWSE:
			if self._cur_attrfield:
				self._cur_attrfield._file_browse_click()
		elif item == ITEM_OPTION:
			if self._cur_attrfield:
				self._cur_attrfield._option_click()
		elif item == ITEM_CANCEL:
			self.cancel_callback()
		elif item == ITEM_OK:
			self.ok_callback()
		elif item == ITEM_RESTORE:
			self.restore_callback()
		elif item == ITEM_APPLY:
			self.apply_callback()
		else:
			print 'Unknown NodeAttrDialog item', item, 'event', event

	def _selectattr(self, item):
		if self._cur_attrfield:
			if self._cur_attrfield == self._attrfields[item]:
				return
			self._cur_attrfield._save()
		else:
			if item == None:
				return
		self._cur_attrfield = None

		if item != None:
			self._cur_attrfield = self._attrfields[item] # XXXX?
			self._cur_attrfield._show()
		
	# Callback functions.  These functions should be supplied by
	# the user of this class (i.e., the class that inherits from
	# this class).
	def cancel_callback(self):
		pass

	def restore_callback(self):
		pass

	def apply_callback(self):
		pass

	def ok_callback(self):
		pass

class AttrEditorDialogField:
	def _createwidget(self, parent):
		self.__parent = parent
		label = self.getlabel()
		value = self.getcurrent()
		return '%s=%s' % (label, value)

##	def _createwidget(self, parent, form, left, right, top, bottom):
##		"""Create the widgets for this attribute.  (internal method)
##
##		Arguments (no defaults):
##		parent -- instance of AttrEditorDialog
##		form -- X_window widget of which we create a child widget
##		left, right, bottom, top -- neighbors
##		"""
##		t = self.gettype()
##		self.__type = t
##		self.__parent = parent
##		if t == 'option':
##			# attribute value is one of a list of choices (option menu)
##			list = self.getoptions()
##			val = self.getcurrent()
##			if val not in list:
##				val = list[0]
##			self.__list = list
##			if len(list) > 30:
##				# list too long for option menu
##				self.__type = 'option-button'
##				w = form.Button(val,
##						(self.__option_callback, ()),
##						left = left, right = right,
##						bottom = bottom, top = top)
##				self.__label = val
##			else:
##				self.__type = 'option-menu'
##				w = form.OptionMenu(None, list,
##						    list.index(val), None,
##						    top = top, bottom = bottom,
##						    left = left, right = right)
##		elif t == 'file':
##			w = form.SubWindow(top = top, bottom = bottom,
##					   left = left, right = right)
##			brwsr = w.Button('Browser...',
##					 (self.browser_callback, ()),
##					 top = None, bottom = None,
##					 right = None)
##			txt = w.TextInput(None, self.getcurrent(), None, None,
##					  top = None, bottom = None,
##					  left = None, right = brwsr)
##			self.__text = txt
##		else:
##			w = form.TextInput(None, self.getcurrent(), None, None,
##					   top = top, bottom = bottom,
##					   left = left, right = right)
##		self.__widget = w
##		return w

	def _save(self):
		pass # Save values from dialog items
		
	def _show(self):
		t = self.gettype()
		value = self.getcurrent()
		explanation = self.gethelptext()
		if t == 'file':
			toshow=ITEMLIST_FILE
			tohide=ITEMLISTNOT_FILE
			# XXXX
		elif t == 'option':
			list = self.getoptions()
			toshow=ITEMLIST_OPTION
			tohide=ITEMLISTNOT_OPTION
			# XXXX
		else:
			toshow=ITEMLIST_STRING
			tohide=ITEMLISTNOT_STRING
			# XXXX
		self.__parent._hideitemlist(tohide)
		if t == 'option':
			list = self.getoptions()
			if value in list:
				value = list.index(value)
			else:
				value = None
			self.__parent._option.setitems(list, value)
		else:
			self.__parent._setlabel(ITEM_STRING, value)
		self.__parent._setlabel(ITEM_INFO, explanation)
		self.__parent._showitemlist(toshow)
		
	def close(self):
		"""Close the instance and free all resources."""
		t = self.__type
		if t == 'option-button':
			del self.__list
			del self.__label
		elif t == 'option-menu':
			del self.__list
		elif t == 'file':
			del self.__text
		del self.__widget
		del self.__type

	def _option_click(self):
		pass
		
	def _file_browse_click(self):
		pass
		
	def __option_callback(self):
		"""Callback called when a new option is to be selected."""
		_MySelectionDialog(self.getlabel(), self.__label,
				   self.getoptions(),
				   self.__option_done_callback)

	def __option_done_callback(self, value):
		"""Callback called when a new option was selected."""
		self.__widget.setlabel(value)
		self.__label = value

	def getvalue(self):
		"""Return the current value of the attribute.

		The return value is a string giving the current value.
		"""
		t = self.__type
		if t == 'option-button':
			return self.__label
		if t == 'option-menu':
			return self.__widget.getvalue()
		if t == 'file':
			return self.__text.gettext()
		return self.__widget.gettext()

	def setvalue(self, value):
		"""Set the current value of the attribute.

		Arguments (no defaults):
		value -- string giving the new value
		"""
		t = self.__type
		if t == 'option-button':
			if not value:
				value = self.__list[0]
			self.__widget.setlabel(value)
			self.__label = value
		elif t == 'option-menu':
			if not value:
				value = self.__list[0]
			self.__widget.setvalue(value)
		elif t == 'file':
			self.__text.settext(value)
		else:
			self.__widget.settext(value)

	def recalcoptions(self):
		"""Recalculate the list of options and set the value."""
		if self.__type[:6] == 'option':
			val = self.getcurrent()
			list = self.getoptions()
			if self.__type == 'option-button':
				self.__widget.setlabel(val)
				self.__label = val
			else:
				if list != self.__list:
					self.__widget.setoptions(
						list, list.index(val))
				else:
					self.__widget.setvalue(val)
			self.__list = list

	# Methods to be overridden by the sub class.
	def gettype(self):
		"""Return the type of the attribute as a string.

		Valid types are:
		option -- attribute value is one of a fixed set of
			values
		file -- attribute is a file name (an interface to a
			file dialog is a good idea)
		string -- attribute is a string
		int -- attribute is a string representing an integer
		float -- attribute is a string representing a float

		`option' and `file' must be handled differently from
		the others, the others can all be handled as a string.
		An attribute field of type `option' must have a
		getoptions method that returns a list of strings
		giving all the possible values.
		An attribute field of type `file' may invoke a
		callback browser_callback that pops up a file browser.
		"""
		return 'type'

	def getlabel(self):
		"""Return the label for the attribute field."""
		return 'Button Label'

	def getcurrent(self):
		"""Return the current value of the attribute as a string."""
		return 'current value'

	def reset_callback(self):
		"""Callback called when the `Reset' button is pressed."""
		pass

	def help_callback(self):
		"""Callback called when help is requested."""
		pass

class _MySelectionDialog(windowinterface.SelectionDialog):
	def __init__(self, label, current, options, callback):
		self.OkCallback = callback
		windowinterface.SelectionDialog.__init__(
			self, 'Choose from', label, options, current)

	def OkCallback(self, value):
		pass

	def NomatchCallback(self, value):
		return '%s is not a valid choice' % value
