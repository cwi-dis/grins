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
		formid='attr_edit'

		toplevel_window=self.wrapper.toplevel.window
		fs=toplevel_window.getformserver()
		w=fs.newformobj(formid)
		w._title=title
		w._attriblist=attriblist
		w._cbdict={
			'Cancel':(self.cancel_callback, ()),
			'Restore':(self.restore_callback, ()),
			'Apply':(self.apply_callback, ()),
			'OK':(self.ok_callback, ()),
			}
		for a in attriblist:
			a.attach_ui(w)
		self.__window=w
		fs.showform(w,formid)
		

	def close(self):
		"""Close the dialog and free resources."""
		if self.__window:
			self.__window.close()
		self.__window=None

	def pop(self):
		"""Pop the dialog window to the foreground."""
		if self.__window:
			self.__window.pop()

	def settitle(self, title):
		"""Set (change) the title of the window.

		Arguments (no defaults):
		title -- string to be displayed as new window title
		"""
		if self.__window:
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
	def attach_ui(self, form):
		"""Set context for this attribute.  (internal method)

		Arguments (no defaults):
		form -- instance of AttrEditorForm
		"""
		if hasattr(self,'__form'):
			raise error, 'cmifcore-win32 name conflict'
		self.__form=form

	def close(self):
		"""Close the instance and free all resources."""
		# nothing to free
		pass

	def getvalue(self):
		"""Return the current value of the attribute.

		The return value is a string giving the current value.
		"""
		return self.__form.getvalue(self)

	def setvalue(self, value):
		"""Set the current value of the attribute.

		Arguments (no defaults):
		value -- string giving the new value
		"""
		self.__form.setvalue(self,value)

	def recalcoptions(self):
		"""Recalculate the list of options and set the value."""
		self.__form.setoptions(self,self.getoptions(), self.getcurrent())


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

