"""Dialog for the NodeInfo dialog.

There are three different types of NodeInfo dialogs.  Only one of
these can be displayed at any one time, but it must be possible to
switch between the three.  This is always done under program control.
Apart from the variable part, there is also a constant part.  This
constant part is described first, the three different variable parts
are described after that.

The constant part of the dialog consists of the following items:
- An editable text field with a `Name:' label.  There is no callback
  associated with this text field, but it must be possible to read the
  text.
- A list of items of which one is always selected, and which does not
  change over time.  There is a label `Type:' associated with this
  list.  When the user changes the current selection, a callback must
  be called.  Also, it must be possible to set the current selection
  under program control.
- A list if items of which one is always selected, but which can be
  changed under program control.  When the user changes the current
  selection, a callback must be called.  Also, it must be possible to
  set the current selection under program control.
- Buttons, each with their own callback: `Cancel', `Restore', `Apply',
  `OK', `Node attr...', `Channel attr...', and `Anchors...'.

The three variable parts are known as external, immediate, and
interior.  A description of each follows.

The external part consists of an interface to show and select a file
name (actually: a URL) and a button `Edit contents...'.  [ In Motif,
there is an editable text field and a `Browser...' button. ]  When the
file name is changed, a callback is called.  There is also a callback
for the browser button (although that could conceivably be changed so
that the browser is called from within NodeInfoDialog instead of from
the parent class).

The immediate part consists of an editable text area.  There are no
callbacks associated with this text area, but it must be possible to
read the text.

The internal part consists of a list of items.  It must be possible to
select one item and get the selection programmatically.  There must be
an interface to 'open' the selection (double clicking, `Open...'
button, whatever) at which time a callback is called.

"""

""" @win32doc|NodeInfoDialog
This class represents the interface between the NodeInfo platform independent
class and its implementation NodeInfoForm in lib/win32/NodeInfoForm.py which 
implements the actual dialog.

"""

__version__ = "$Id$"


class NodeInfoDialog:
	def __init__(self, title, channelnames, initchannel, types, inittype,
		     name, filename, children, immtext):
		"""Create the NodeInfo dialog.

		Create the dialog window (non-modal, so does not grab
		the cursor) and pop it up (i.e. display it on the
		screen).

		Arguments (no defaults):
		title -- string to be displayed as window title
		channelnames -- list of strings, one of which is
			always selected
		initchannel -- 0 <= initchannel < len(channelnames) --
			the initial selection of the channelnames
		types -- list of strings, one of which is always
			selected
		inittype -- 0 <= inittype < len(types) -- the initial
			selection of the types
		name -- string, the initial value for the name field
		filename -- string, the initial value for the file
			name field, to be displayed as the file name
			in the exterior part
		children -- list of strings -- the list of strings to
			be displayed in the interior part
		immtext -- list of strings or a single string with
			embedded linefeeds -- the text to be displayed
			in the immediate part
		"""
		adornments = {
			'form_id':'node_info',
			'callbacks':{
				'Channel':(self.channel_callback, ()),
				'Type':(self.type_callback, ()),
				'Cancel':(self.cancel_callback, ()),
				'Restore':(self.restore_callback, ()),
				'NodeAttr':(self.attributes_callback, ()),
				'ChanAttr':(self.chattrs_callback, ()),
				'Anchors':(self.anchors_callback, ()),
				'Apply':(self.apply_callback, ()),
				'OK':(self.ok_callback, ()),
				'URL':(self.file_callback, ()),
				'CallEditor':(self.conteditor_callback, ()),
				'Browse':(self.browser_callback, ()),
				'EdBrowse':(self.browserfile_callback,()),
				'OpenChild':(self.openchild_callback, ())
				}
			}

		formid=adornments['form_id']
		toplevel_window=self.toplevel.window
		fs=toplevel_window.getformserver()
		w=fs.newformobj(formid)
		w.do_init(title, channelnames, initchannel, types, inittype,
		     name, filename, children, immtext,adornments)
		fs.showform(w,formid)
		self.__window=w

		w.setdata()
		w.enable_cbs()

	def close(self):
		"""Close the dialog and free resources."""
		self.__window.close()
		del self.__window

	def pop(self):
		"""Pop the dialog window to the foreground."""
		self.__window.pop()

	def settitle(self, title):
		"""Set (change) the title of the window.

		Arguments (no defaults):
		title -- string to be displayed as new window title.
		"""
		self.__window.settitle(title)

	# Interface to the list of channel names.  This part consists
	# of a label and a list of strings of which one is always the
	# current selection.  Only one element of the list needs to be
	# visible (the current selection) but it must be possible to
	# choose from the list.
	def setchannelnames(self, channelnames, initchannel):
		"""Set the list of strings and the initial selection.

		Arguments (no defaults):
		channelnames -- list of strings
		initchannel -- 0 <= initchannel < len(channelnames) --
			the initial selection
		"""
		self.__window.setchannelnames(channelnames, initchannel)

	def getchannelname(self):
		"""Get the string which is the current selection."""
		return self.__window.getchannelname()

	def askchannelname(self, default):
		import windowinterface
		windowinterface.InputDialog('Name for new channel',
					    default,
					    self.newchan_callback,
					    cancelCallback = (self.newchan_callback, ()),
					    parent = self.__window)

	# Interface to the list of node types.  This part consists of
	# a label and a list of strings of which one is always the
	# current selection.  Only one element of the list needs to be
	# visible (the current selection) but it must be possible to
	# choose from the list.
	def settypes(self, types, inittype):
		"""Set the list of strings and the initial selection.

		Arguments (no defaults):
		types -- list of strings
		inittype -- 0 <= inittype < len(types) -- the initial
			selection
		"""
		self.__window.settypes(types, inittype)

	def gettype(self):
		"""Get the string which is the current selection."""
		return self.__window.gettype()

	def settype(self, inittype):
		"""Set the current selection.

		Arguments (no defaults):
		inittype -- 0 <= inittype < len(types) -- the new
			current selection
		"""
		self.__window.settype(inittype)

	# Interface to the name field.  This part consists of an
	# editable text field.
	def setname(self, name):
		"""Set the value of the name field.

		Arguments (no defaults):
		name -- string
		"""
		self.__window.setname(name)

	def getname(self):
		"""Return the current value of the name field."""
		return self.__window.getname()

	# The following methods choose between the three variable
	# parts.  One of the parts is active (the others need not be
	# shown), and when one of the parts is made the active part,
	# the others are automatically made inactive (possibly
	# hidden).
	# In Motif, this is done by using the same screen area for the
	# three parts.
	def imm_group_show(self):
		"""Make the immediate part visible."""
		self.__window.imm_group_show()

	def int_group_show(self):
		"""Make the interior part visible."""
		self.__window.int_group_show()

	def ext_group_show(self):
		"""Make the external part visible."""
		self.__window.ext_group_show()

	# Interface to the external part.  This part consists of a
	# text field with a URL (with or without the protocol, and if
	# without protocol, absolute or relative) and a `Browser...'
	# button which triggers a callback function.
	def setfilename(self, filename):
		"""Set the value of the filename (URL).

		Arguments (no defaults):
		filename -- string giving the URL
		"""
		self.__window.setfilename(filename)

	def getfilename(self):
		"""Return the value of the filename text field."""
		return self.__window.getfilename()

	# Interface to the interior part.  This part consists of a
	# list of strings and an interface to select one item in the
	# list.
	def setchildren(self, children, initchild):
		"""Set the list of children.

		Arguments (no defaults):
		children -- list of strings
		initchild -- 0 <= initchild < len(children) or None --
			the initial selection (no selection igf None)
		"""
		self.__window.setchildren(children, initchild)

	def getchild(self):
		"""Return the index of the current selection or None."""
		return self.__window.getchild()

	# Interface to the immediate part.  This part consists of an
	# editable text area.  There are no callbacks.
	def settext(self, immtext):
		"""Set the current text.

		Arguments (no defaults):
		immtext -- list of strings or a single string with
			embedded linefeeds
		"""
		self.__window.settext(immtext)

	def gettext(self):
		"""Return the current text as one string."""
		return self.__window.gettext()

	def gettextlines(self):
		"""Return the current text as a list of strings."""
		return self.__window.gettextlines()

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

	def channel_callback(self):
		pass

	def type_callback(self):
		pass

	def attributes_callback(self):
		pass

	def chattrs_callback(self):
		pass

	def anchors_callback(self):
		pass

	def file_callback(self):
		pass

	def conteditor_callback(self):
		pass

	def browser_callback(self):
		pass

	def openchild_callback(self):
		pass
