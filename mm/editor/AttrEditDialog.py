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

import windowinterface

class AttrEditorDialog:
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

		w = windowinterface.Window(title, resizable = 1,
				deleteCallback = (self.cancel_callback, ()))
		self.__window = w
		buttons = w.ButtonRow(
			[('Cancel', (self.cancel_callback, ())),
			 ('Restore', (self.restore_callback, ())),
			 ('Apply', (self.apply_callback, ())),
			 ('OK', (self.ok_callback, ())),
			 ],
			left = None, right = None, bottom = None, vertical = 0)
		sep = w.Separator(left = None, right = None, bottom = buttons)
		form = w.SubWindow(left = None, right = None, top = None,
				   bottom = sep)
		height = 1.0 / len(attriblist)
		helpb = rstb = wdg = None # "upstairs neighbors"
		self.__buttons = []
		for i in range(len(attriblist)):
			a = attriblist[i]
			bottom = (i + 1) *  height
			helpb = form.Button(a.getlabel(),
					    (a.help_callback, ()),
					    left = None, top = helpb,
					    right = 0.5, bottom = bottom)
			rstb = form.Button('Reset',
					   (a.reset_callback, ()),
					   right = None, top = rstb,
					   bottom = bottom)
			wdg = a._createwidget(self, form,
					      left = helpb, right = rstb,
					      top = wdg, bottom = bottom)
		w.show()

	def close(self):
		"""Close the dialog and free resources."""
		self.__window.close()
		for b in self.__buttons:
			del b.__button
			del b.__label
		del self.__buttons
		del self.__window

	def pop(self):
		"""Pop the dialog window to the foreground."""
		self.__window.pop()

	def settitle(self, title):
		"""Set (change) the title of the window.

		Arguments (no defaults):
		title -- string to be displayed as new window title
		"""
		self.__window.settitle(title)

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
	def _createwidget(self, parent, form, left, right, top, bottom):
		"""Create the widgets for this attribute.  (internal method)

		Arguments (no defaults):
		parent -- instance of AttrEditorDialog
		form -- X_window widget of which we create a child widget
		left, right, bottom, top -- neighbors
		"""
		t = self.gettype()
		self.__type = t
		if t == 'option':
			# attribute value is one of a list of choices (option menu)
			list = self.getoptions()
			val = self.getcurrent()
			self.__list = list
			if len(list) > 30:
				# list too long for option menu
				self.__type = 'option-button'
				w = form.Button(val,
						(self.__option_callback, ()),
						left = left, right = right,
						bottom = bottom, top = top)
				self.__label = val
			else:
				self.__type = 'option-menu'
				w = form.OptionMenu(None, list,
						    list.index(val), None,
						    top = top, bottom = bottom,
						    left = left, right = right)
		elif t == 'file':
			w = form.SubWindow(top = top, bottom = bottom,
					   left = left, right = right)
			brwsr = w.Button('Browser...',
					 (self.browser_callback, ()),
					 top = None, bottom = None,
					 right = None)
			txt = w.TextInput(None, self.getcurrent(), None, None,
					  top = None, bottom = None,
					  left = None, right = brwsr)
			self.__text = txt
		else:
			w = form.TextInput(None, self.getcurrent(), None, None,
					   top = top, bottom = bottom,
					   left = left, right = right)
		self.__widget = w
		return w

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
