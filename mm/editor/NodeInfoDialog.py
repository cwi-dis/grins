import windowinterface

class NodeInfoDialog:
	def __init__(self, title, channelnames, initchannel, types, inittype,
		     name, filename, children, immtext):

		self.__window = w = windowinterface.Window(
			title, resizable = 1,
			deleteCallback = (self.cancel_callback, ()))

		top = w.SubWindow(left = None, right = None, top = None)

		self.__channel_select = top.OptionMenu('Channel:',
					channelnames, initchannel,
					(self.channel_callback, ()),
					right = None, top = None)
		self.__type_select = top.OptionMenu('Type:', types, inittype,
						  (self.type_callback, ()),
						  right = self.__channel_select,
						  top = None)
		self.__name_field = top.TextInput('Name:', name, None, None,
						left = None, top = None,
						right = self.__type_select)
		butt = w.ButtonRow(
			[('Cancel', (self.cancel_callback, ())),
			 ('Restore', (self.restore_callback, ())),
			 ('Node attr...', (self.attributes_callback, ())),
			 ('Anchors...', (self.anchors_callback, ())),
			 ('Apply', (self.apply_callback, ())),
			 ('OK', (self.ok_callback, ()))],
			bottom = None, left = None, right = None, vertical = 0)

		midd = w.SubWindow(top = top, bottom = butt, left = None,
				   right = None)

		alter = midd.AlternateSubWindow(top = None, bottom = None,
						right = None, left = None)
		self.__imm_group = alter.SubWindow()
		self.__ext_group = alter.SubWindow()
		self.__int_group = alter.SubWindow()

		self.__file_input = self.__ext_group.TextInput('File:', filename,
				(self.file_callback, ()), None,
				top = None, left = None, right = None)
		butt = self.__ext_group.ButtonRow(
			[('Edit contents...', (self.conteditor_callback, ())),
			 ('Browser...', (self.browser_callback, ()))],
			top = self.__file_input, left = None, right = None,
			vertical = 0)

		butt = self.__int_group.ButtonRow(
			[('Open...', (self.openchild_callback, ()))],
			left = None, right = None, bottom = None, vertical = 0)
		self.__children_browser = self.__int_group.List('Children:',
				children,
				[None, (self.openchild_callback, ())],
				top = None, left = None, right = None,
				bottom = butt)

		label = self.__imm_group.Label('Contents:',
				top = None, left = None, right = None)
		self.__text_browser = self.__imm_group.TextEdit(immtext, None,
					top = label, left = None,
					right = None, bottom = None)

		if immtext:
			self.__imm_group.show()
		elif children:
			self.__int_group.show()
		else:
			self.__ext_group.show()

		w.show()

	def pop(self):
		self.__window.pop()

	def settitle(self, title):
		self.__window.settitle(title)

	def close(self):
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

	def setchannelnames(self, channelnames, initchannel):
		self.__channel_select.setoptions(channelnames, initchannel)

	def getchannelname(self):
		return self.__channel_select.getvalue()

	def settypes(self, types, inittype):
		self.__type_select.setoptions(types, inittype)

	def gettype(self):
		return self.__type_select.getvalue()

	def settype(self, inittype):
		self.__type_select.setpos(inittype)

	def setname(self, name):
		self.__name_field.settext(name)

	def getname(self):
		return self.__name_field.gettext()

	def imm_group_show(self):
		self.__imm_group.show()

	def int_group_show(self):
		self.__int_group.show()

	def ext_group_show(self):
		self.__ext_group.show()

	def setfilename(self, filename):
		self.__file_input.settext(filename)

	def getfilename(self):
		return self.__file_input.gettext()

	def setchildren(self, children, initchild):
		self.__children_browser.delalllistitems()
		self.__children_browser.addlistitems(children, -1)
		if children:
			self.__children_browser.selectitem(initchild)

	def getchild(self):
		return self.__children_browser.getselected()

	def gettext(self):
		return self.__text_browser.gettext()

	def gettextlines(self):
		return self.__text_browser.getlines()

	def settext(self, immtext):
		self.__text_browser.settext(immtext)

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

	def channel_callback(self):
		pass

	def type_callback(self):
		pass

	def attributes_callback(self):
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
