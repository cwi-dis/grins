import EventEditor, components
import win32dialog, win32con, grinsRC, windowinterface

class EventEditorDialog(win32dialog.ResDialog):
	resource = grinsRC.IDD_EVENT
	def __init__(self, parent=None):
		win32dialog.ResDialog.__init__(self, self.resource, parent)
		self._causewidget = components.ComboBox(self, grinsRC.IDC_EVENTCAUSE1)
		self._eventwidget = components.ComboBox(self, grinsRC.IDC_EVENTTYPE)
		self._textwidget = components.Edit(self, grinsRC.IDC_THINGVALUE)
		self._thingnamewidget = components.Edit(self, grinsRC.IDC_THINGNAME) # static text box.
		self._resultwidget = components.Edit(self, grinsRC.IDC_EDIT3)
		self._offsetwidget = components.Edit(self, grinsRC.IDC_EDIT2)

	def show(self):
		if self.DoModal() == 1:	# returns either 1 or 2 (!)
			return 1
		else:
			return 0
#		self.done()

	def OnInitDialog(self):
		self.attach_handles_to_subwindows()
		self._causewidget.resetcontent()
		map(self._causewidget.addstring, EventEditor.CAUSES)
		x = self._eventstruct.get_cause()
		if x:
			try:
				self._causewidget.setcursel(EventEditor.CAUSES.index(x))
			except ValueError:
				print "Error: unknown event cause:", x
				#windowinterface.showmessage("Unknown event cause.", mtype="error")
		else:
			print "Warning: Event cause is None."
		self.set_eventwidget()
		self.set_offsetwidget()
		self._causewidget.hookcommand(self, self._causewidgetcallback)
		self._eventwidget.hookcommand(self, self._eventwidgetcallback)
		self._textwidget.hookcommand(self, self._textwidgetcallback)
		self._offsetwidget.hookcommand(self, self._offsetwidgetcallback)
		return win32dialog.ResDialog.OnInitDialog(self)

	def set_eventwidget(self):
		# Sets the value of the event widget.
		self._eventwidget.resetcontent()
		l = self._eventstruct.get_possible_events()
		if l:
			map(self._eventwidget.addstring, l)
		i = self._eventstruct.get_event_index()
		if i:
			self._eventwidget.setcursel(i)
		else:
			print "DEBUG: event widget has no index."
		self.set_textwidget()
			
	def set_textwidget(self):
		name, string, isnumber, isreadonly = self._eventstruct.get_thing_string()
		if isreadonly or string is None:
			self._textwidget.setmodify(1)
		else:
			self._textwidget.setmodify(0)
		if string:
			self._textwidget.settext(string)
		else:
			self._textwidget.settext("")
		self._thingnamewidget.settext(name)
		self.set_resultwidget()
	def set_resultwidget(self):
		self._resultwidget.settext(self._eventstruct.as_string())
	def set_offsetwidget(self):
		# TODO:
		r = self._eventstruct.get_offset()
		if r:
			self._offsetwidget.setmodify(1)
			self._offsetwidget.settext(r)
		else:
			self._offsetwidget.settext("")
			self._offsetwidget.setmodify(0)

	def _causewidgetcallback(self, id, code):
		if code == win32con.CBN_SELCHANGE:
			s = self._causewidget.getvalue()
			self._eventstruct.set_cause(s)
			self.set_eventwidget()
	def _eventwidgetcallback(self, id, code):
		if code == win32con.CBN_SELCHANGE:
			s = self._eventwidget.getvalue()
			self._eventstruct.set_event(s)
			self.set_textwidget()
	def _textwidgetcallback(self, id, code):
		print "DEBUG: _textwidgetcallback: code is: ", code
		if code != win32con.EN_CHANGE:
			return
		t = self._textwidget.gettext()
		error = self._eventstruct.set_thing_string(t)
		if error:
			windowinterface.showmessage(error, mtype="error")
	def _offsetwidgetcallback(self, id, code):
		#if code != win32con.EN_CHANGE:
		#	return
		if not self._eventstruct.set_offset(self._offsetwidget.gettext()):
			# In theory this will never happen - the widget is numeric only.
			windowinterface.showmessage("Offset must be a number.", self)

	#def OnOK(self):
	#	if self.done():
	#		print "Closing."
	#		self.close()
