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
  `OK', `Node attr...', and `Anchors...'.

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

__version__ = "$Id$"

import windowinterface, cmifex2, win32api, win32con

DEFAULT_EDIT_WIDTH = 120

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
		self.__window = w = windowinterface.Window(
			title, resizable = 1,
			deleteCallback = (self.cancel_callback, ()))

		#top = w.SubWindow(left = None, right = None, top = None)

		#self.__channel_select = top.OptionMenu('Channel:',
		#			channelnames, initchannel,
		#			(self.channel_callback, ()),
		#			right = None, top = None)
		#self.__type_select = top.OptionMenu('Type:', types, inittype,
		#				  (self.type_callback, ()),
		#				  right = self.__channel_select,
		#				  top = None)
		#self.__name_field = top.TextInput('Name:', name, None, None,
		#				left = None, top = None,
		#				right = self.__type_select)
		#butt = w.ButtonRow(
		#	[('Cancel', (self.cancel_callback, ())),
		#	 ('Restore', (self.restore_callback, ())),
		#	 ('Node attr...', (self.attributes_callback, ())),
		#	 ('Anchors...', (self.anchors_callback, ())),
		#	 ('Apply', (self.apply_callback, ())),
		#	 ('OK', (self.ok_callback, ()))],
		#	bottom = None, left = None, right = None, vertical = 0)

		#midd = w.SubWindow(top = top, bottom = butt, left = None,
		#		   right = None)

		#alter = midd.AlternateSubWindow(top = None, bottom = None,
		#				right = None, left = None)
		#self.__imm_group = alter.SubWindow()
		#self.__ext_group = alter.SubWindow()
		#self.__int_group = alter.SubWindow()

		#self.__file_input = self.__ext_group.TextInput('URL:',
		#		filename,
		#		(self.file_callback, ()), None,
		#		top = None, left = None, right = None)
		#butt = self.__ext_group.ButtonRow(
		#	[('Edit contents...', (self.conteditor_callback, ())),
		#	 ('Browser...', (self.browser_callback, ()))],
		#	top = self.__file_input, left = None, right = None,
		#	vertical = 0)

		#butt = self.__int_group.ButtonRow(
		#	[('Open...', (self.openchild_callback, ()))],
		#	left = None, right = None, bottom = None, vertical = 0)
		#self.__children_browser = self.__int_group.List('Children:',
		#		children,
		#		[None, (self.openchild_callback, ())],
		#		top = None, left = None, right = None,
		#		bottom = butt)

		#label = self.__imm_group.Label('Contents:',
		#		top = None, left = None, right = None)
		#self.__text_browser = self.__imm_group.TextEdit(immtext, None,
		#			top = label, left = None,
		#			right = None, bottom = None)

		#if immtext:
		#	self.__imm_group.show()
		#elif children:
		#	self.__int_group.show()
		#else:
		#	self.__ext_group.show()


		constant = 3*win32api.GetSystemMetrics(win32con.SM_CXBORDER)+win32api.GetSystemMetrics(win32con.SM_CYCAPTION)+5
		constant2 = 2*win32api.GetSystemMetrics(win32con.SM_CYBORDER)+5
		self._w = constant2
		self._h = constant
		hbw = 0
		eb1w = 0
		eb2w = 0
		lb1w = 0
		lb2w = 0
		topw = 0
		toph = 0
		midw = 0
		midh = 155
		max = 0
		btm = 0


		ls = [('Cancel', (self.cancel_callback, ())),
			 ('Restore', (self.restore_callback, ())),
			 ('Node attr...', (self.attributes_callback, ())),
			 ('Channel attr...', (self.chattrs_callback, ())),
			 ('Anchors...', (self.anchors_callback, ())),
			 ('Apply', (self.apply_callback, ())),
			 ('OK', (self.ok_callback, ())),
			 ('Help', (self.helpcall, ()))]

		length = 0
		for item in ls:
			label = item[0]
			if (label==None or label==''):
				label=' '
			length = cmifex2.GetStringLength(self.__window._hWnd,label)
			hbw = hbw + length + 15
		max = hbw
		self._h = self._h + 30

		ls = channelnames

		length = 0
		for item in ls:
			label = item
			if (label==None or label==''):
				label=' '
			length = cmifex2.GetStringLength(self.__window._hWnd,label)
			if length>lb2w:
				lb2w = length
		lb2w = lb2w + cmifex2.GetStringLength(self.__window._hWnd,'Channel: ')+30


		ls = types

		length = 0
		for item in ls:
			label = item
			if (label==None or label==''):
				label=' '
			length = cmifex2.GetStringLength(self.__window._hWnd,label)
			if length>lb1w:
				lb1w = length
		lb1w = lb1w + cmifex2.GetStringLength(self.__window._hWnd,'Type: ')+30

		if (name==None or name==''):
			name = ' '
		#print '---------window----------', self.__window._hWnd, 'name: ', name


		eb1w = cmifex2.GetStringLength(self.__window._hWnd,name) + cmifex2.GetStringLength(self.__window._hWnd,'Name: ') + 10

		if (eb1w < DEFAULT_EDIT_WIDTH):
			eb1w = DEFAULT_EDIT_WIDTH

		if max<lb1w+lb2w+eb1w+20:
			max = lb1w+lb2w+eb1w+20

		toph = 30

		self._h = self._h + toph + 160

		ls = [('Edit contents...', (self.conteditor_callback, ())),
			 ('Browser...', (self.browser_callback, ()))]

		length = 0
		for item in ls:
			label = item[0]
			if (label==None or label==''):
				label=' '
			length = cmifex2.GetStringLength(self.__window._hWnd,label)
			midw = midw + length + 15

		if max<midw:
			max = midw

		midw = max
		topw = max
		self._w = self._w + max + 10

		top = w.SubWindow(left = 5, right = topw, top = 3, bottom = 30)

		self.__name_field = top.TextInput('Name: ', name, None, None,
						left = 0, right = eb1w, top = 0, bottom = 25, editable = 1)

		self.__type_select = top.OptionMenu('Type: ', types, inittype,
						  (self.type_callback, ()),
						  left = eb1w+5, right = lb1w, top = 0, bottom = 125)

		self.__channel_select = top.OptionMenu('Channel: ',
					channelnames, initchannel,
					(self.channel_callback, ()),
					left = eb1w+lb1w+10, right = lb2w, top = 0, bottom = 125)

		butt = w.ButtonRow(
			[('Cancel', (self.cancel_callback, ())),
			 ('Restore', (self.restore_callback, ())),
			 ('Node attr...', (self.attributes_callback, ())),
			 ('Channel attr...', (self.chattrs_callback, ())),
			 ('Anchors...', (self.anchors_callback, ())),
			 ('Apply', (self.apply_callback, ())),
			 ('OK', (self.ok_callback, ())),
			 ('Help', (self.helpcall, ()))],
			left = 5, right = max, top = 185, bottom = 30, vertical = 0)

		midd = w.SubWindow(left = 5, right = midw, top = 30, bottom = 155)

		alter = midd.AlternateSubWindow(left = 0, right = midw, top = 0, bottom = 155)
		self.__imm_group = alter.SubWindow(left = 0, right = midw, top = 0, bottom = 155)
		self.__ext_group = alter.SubWindow(left = 0, right = midw, top = 0, bottom = 155)
		self.__int_group = alter.SubWindow(left = 0, right = midw, top = 0, bottom = 155)

		self.__file_input = self.__ext_group.TextInput('URL:',
				filename,
				(self.file_callback, ()), None,
				left = 0, right = midw, top = 0, bottom = 25)
		butt = self.__ext_group.ButtonRow(
			[('Edit contents...', (self.conteditor_callback, ())),
			 ('Browser...', (self.browser_callback, ()))],
			left = 0, right = midw, top = 25, bottom = 30,
			vertical = 0)

		butt = self.__int_group.ButtonRow(
			[('Open...', (self.openchild_callback, ()))],
			left = 0, right = midw, top = 125, bottom = 30, vertical = 0)
		self.__children_browser = self.__int_group.List('Children:',
				children,
				[None, (self.openchild_callback, ())],
				left = 0, right = midw, top = 0, bottom = 125)

		label = self.__imm_group.Label('Contents:',
				left = 0, right = midw, top = 0, bottom = 25)
		self.__text_browser = self.__imm_group.TextEdit(immtext, None,
					left = 0, right = midw, top = 25, bottom = 130)

		if immtext:
			self.__imm_group.show()
			w._not_shown.append(self.__int_group)
			w._not_shown.append(self.__ext_group)
		elif children:
			self.__int_group.show()
			w._not_shown.append(self.__imm_group)
			w._not_shown.append(self.__ext_group)
		else:
			self.__ext_group.show()
			w._not_shown.append(self.__int_group)
			w._not_shown.append(self.__imm_group)

		cmifex2.ResizeWindow(w._hWnd, self._w, self._h)
		self.__window._hWnd.HookKeyStroke(self.helpcall,104)
		w.show()


	def helpcall(self, params=None):
		import Help
		Help.givehelp(self.__window._hWnd, 'Node Info Dialog')


	def close(self):
		"""Close the dialog and free resources."""
		self.__window.close()
		del self.__window
		del self.__channel_select
		del self.__type_select
		del self.__name_field
		del self.__imm_group
		del self.__ext_group
		del self.__int_group
		del self.__file_input
		del self.__children_browser
		del self.__text_browser

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
		self.__channel_select.setoptions(channelnames, initchannel)

	def getchannelname(self):
		"""Get the string which is the current selection."""
		return self.__channel_select.getvalue()

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
		self.__type_select.setoptions(types, inittype)

	def gettype(self):
		"""Get the string which is the current selection."""
		return self.__type_select.getvalue()

	def settype(self, inittype):
		"""Set the current selection.

		Arguments (no defaults):
		inittype -- 0 <= inittype < len(types) -- the new
			current selection
		"""
		self.__type_select.setpos(inittype)

	# Interface to the name field.  This part consists of an
	# editable text field.
	def setname(self, name):
		"""Set the value of the name field.

		Arguments (no defaults):
		name -- string
		"""
		self.__name_field.settext(name)

	def getname(self):
		"""Return the current value of the name field."""
		return self.__name_field.gettext()

	# The following methods choose between the three variable
	# parts.  One of the parts is active (the others need not be
	# shown), and when one of the parts is made the active part,
	# the others are automatically made inactive (possibly
	# hidden).
	# In Motif, this is done by using the same screen area for the
	# three parts.
	def imm_group_show(self):
		"""Make the immediate part visible."""
		self.__imm_group.show()

	def int_group_show(self):
		"""Make the interior part visible."""
		self.__int_group.show()

	def ext_group_show(self):
		"""Make the external part visible."""
		self.__ext_group.show()

	# Interface to the external part.  This part consists of a
	# text field with a URL (with or without the protocol, and if
	# without protocol, absolute or relative) and a `Browser...'
	# button which triggers a callback function.
	def setfilename(self, filename):
		"""Set the value of the filename (URL).

		Arguments (no defaults):
		filename -- string giving the URL
		"""
		self.__file_input.settext(filename)

	def getfilename(self):
		"""Return the value of the filename text field."""
		return self.__file_input.gettext()

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
		self.__children_browser.delalllistitems()
		self.__children_browser.addlistitems(children, -1)
		if children:
			self.__children_browser.selectitem(initchild)

	def getchild(self):
		"""Return the index of the current selection or None."""
		return self.__children_browser.getselected()

	# Interface to the immediate part.  This part consists of an
	# editable text area.  There are no callbacks.
	def settext(self, immtext):
		"""Set the current text.

		Arguments (no defaults):
		immtext -- list of strings or a single string with
			embedded linefeeds
		"""
		self.__text_browser.settext(immtext)

	def gettext(self):
		"""Return the current text as one string."""
		return self.__text_browser.gettext()

	def gettextlines(self):
		"""Return the current text as a list of strings."""
		return self.__text_browser.getlines()

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
