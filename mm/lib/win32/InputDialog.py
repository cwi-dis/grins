__version__ = "$Id$"

import win32ui, win32con, win32api
from win32modules import cmifex2
from appcon import *
import win32mu

toplevel=None # set by AppTopLevel

class InputDialog:
	def __init__(self, prompt, default, cb, cancelCallback = None):
		self.OkCallback = cb
		self.CancelCallback = cancelCallback
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
		self._window_type = SINGLE
		toplevel._subwindows.append(self)


	def _ok(self, params):
		if self.is_closed():
			return
		value = cmifex2.GetText(self._edit)
		self.close()
		if self.OkCallback:
			self.OkCallback(value)
			self.OkCallback = None

	def _cancel(self, params):
		if self.is_closed():
			return
		if self.CancelCallback:
			apply(apply, self.CancelCallback)
			self.CancelCallback = None
		self.close()


	def setcursor(self, cursor):
		keys = win32Cursors.keys()
		if cursor in keys:
			win32mu.SetCursor(win32Cursors[cursor])
		else:
			win32mu.SetCursor(ARROW)

	def close(self):
		if self._form:
			if self in toplevel._subwindows: toplevel._subwindows.remove(self)
			for control in self._controls:
				cmifex2.DestroyWindow(control)
				self._controls.remove(control)
			if self._form:
				self._form.DestroyWindow()
			self._form = None

	def is_closed(self):
		return self._form is None

	def _resize_callback(self, params):
		x, y, w, h = self._form.GetClientRect()
		cmifex2.ResizeWindow(self._controls[0], w-10)

