import EventEditor, components
import win32dialog, win32con, grinsRC

class EventEditorDialog(win32dialog.ResDialog):
	resource = grinsRC.IDD_EVENT
	def __init__(self, parent=None):
		win32dialog.ResDialog.__init__(self, self.resource, parent)
		self._causewidget = components.ComboBox(self, grinsRC.IDC_EVENTCAUSE1)
		self._eventwidget = components.ComboBox(self, grinsRC.IDC_EVENTTYPE)
		self._textwidget = components.Edit(self, grinsRC.IDC_EDIT3)

	def show(self):
		self.DoModal()
		self.done()

	def OnInitDialog(self):
		self.attach_handles_to_subwindows()
		self._causewidget.resetcontent()
		self._causewidget.setcursel(0)
		map(self._causewidget.addstring, EventEditor.CAUSES)
		self._causewidget.setcursel(EventEditor.CAUSES.index(self._eventstruct.get_cause()))
		self.set_eventwidget()
		self._causewidget.hookcommand(self, self._causewidgetcallback)
		self._eventwidget.hookcommand(self, self._eventwidgetcallback)
		self._textwidget.hookcommand(self, self._textwidgetcallback)

		d = self._eventstruct._syncarc
		self._textwidget.settext("DEBUG:"+d.event+" from: "+repr(d.srcnode))
		
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

	def set_textwidget(self):
		string, isnumber, isreadonly = self._eventstruct.get_thing_string()
		if isreadonly or string is None:
			self._textwidget.setmodify(1)
		else:
			self._textwidget.setmodify(0)
		if string:
			self._textwidget.settext(string)
		else:
			self._textwidget.settext("")

	def _causewidgetcallback(self, id, code):
		s = self._causewidget.getvalue()
		self._eventstruct.set_cause(s)
		self.set_eventwidget()

	def _eventwidgetcallback(self, id, code):
		s = self._eventwidget.getvalue()
		self._eventstruct.set_event(s)
		self.set_textwidget()

	def _textwidgetcallback(self, id, code):
		print "Callback."

	#def OnOK(self):
	#	if self.done():
	#		print "Closing."
	#		self.close()
