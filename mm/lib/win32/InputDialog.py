__version__ = "$Id$"

import win32ui, win32con, win32api
from win32modules import cmifex, cmifex2

class InputDialog:
	def __init__(self, prompt, default, cb):
	#	attrs = {'dialogStyle': Xmd.DIALOG_FULL_APPLICATION_MODAL,
	#		 'colormap': toplevel._default_colormap,
	#		 'visual': toplevel._default_visual,
	#		 'depth': toplevel._default_visual.depth}
	#	self._form = toplevel._main.CreatePromptDialog(
	#					   'inputDialog', attrs)
	#	self._form.AddCallback('okCallback', self._ok, cb)
	#	self._form.AddCallback('cancelCallback', self._cancel, None)
	#	helpb = self._form.SelectionBoxGetChild(
	#					Xmd.DIALOG_HELP_BUTTON)
	#	helpb.UnmanageChild()
	#	sel = self._form.SelectionBoxGetChild(
	#				      Xmd.DIALOG_SELECTION_LABEL)
	#	sel.labelString = prompt
	#	text = self._form.SelectionBoxGetChild(Xmd.DIALOG_TEXT)
	#	text.value = default
	#	self._form.ManageChild()
		
		self.CancelCallback = cb
		self._controls = []

		self._nexty = 0

		w = 210
		h = 110
		x = (win32api.GetSystemMetrics(win32con.SM_CXSCREEN)-w)/2 
		y = (win32api.GetSystemMetrics(win32con.SM_CYSCREEN)-h)/2 

		par = win32ui.GetActiveWindow()
		form = cmifex2.CreateDialogbox(prompt,par,x,y,w,h,1,1)
		self._form = form

		x, y, w, h = form.GetClientRect()

		editx = 10
		edity = 10
		editw = w-20
		edith = 25

		self._nexty = self._nexty+y+10+edith+10

		obx = (w-160)/4
		oby = self._nexty
		obw = 80
		obh = 25

		cbx = w-80-(w-160)/4
		cby = self._nexty

		self._nexty = self._nexty+obh+10

		self._edit = cmifex2.CreateEdit(default, form, editx, edity,editw, edith,TRUE)
		self._controls.append(self._edit)

		okbutton = cmifex2.CreateButton("OK",form,obx,oby,obw,obh,('b',''))
		self._controls.append(okbutton)

		cancelbutton = cmifex2.CreateButton("Cancel",form,cbx,cby,obw,obh,('b',''))
		self._controls.append(cancelbutton)

		okbutton.HookMessage(self._ok, win32con.WM_LBUTTONDOWN)
		cancelbutton.HookMessage(self._cancel, win32con.WM_LBUTTONDOWN)
		self._edit.HookKeyStroke(self._ok,13)
		#form.HookMessage(self._resize_callback, win32con.WM_SIZE)
		self._window_type = SINGLE
		toplevel._subwindows.append(self)

	
	def _ok(self, params):
		if self.is_closed():
			return
		value = cmifex2.GetText(self._edit)
		self.close()
		if self.CancelCallback:
			func = self.CancelCallback
			func(value)

	def old_ok(self, w, client_data, call_data):
		if self.is_closed():
			return
		value = call_data.value
		self.close()
		if client_data:
			client_data(value)

	def _cancel(self, params):
		print "Cancel pressed"
		if self.is_closed():
			return
		self.close()
	
	
	def old_cancel(self, w, client_data, call_data):
		if self.is_closed():
			return
		self.close()

	#def setcursor(self, cursor):
	#	WIN32_windowbase._win_setcursor(self._form, cursor)

	def close(self):
		if self._form:
			toplevel._subwindows.remove(self)
			#self._form.UnmanageChild()
			#self._form.DestroyWidget()
			for control in self._controls:
				cmifex2.DestroyWindow(control)
				self._controls.remove(control)
			#cmifex2.DestroyWindow(self._form)
			if self._form:
				self._form.DestroyWindow()
			self._form = None

	def is_closed(self):
		return self._form is None

	def _resize_callback(self, params):
		x, y, w, h = self._form.GetClientRect()
		cmifex2.ResizeWindow(self._controls[0], w-10)
