__version__ = "$Id$"

import win32ui, win32con, win32api
from win32modules import cmifex, cmifex2

class SelectionDialog:
	def __init__(self, listprompt, selectionprompt, itemlist, default, parent=None):
		self._controls = []
	#	attrs = {'dialogStyle': Xmd.DIALOG_FULL_APPLICATION_MODAL,
	#		 'colormap': toplevel._default_colormap,
	#		 'visual': toplevel._default_visual,
	#		 'depth': toplevel._default_visual.depth,
	#		 'textString': default,
	#		 'autoUnmanage': FALSE}
		attrs = {'textString': default}

		if hasattr(self, 'NomatchCallback'):
			attrs['mustMatch'] = TRUE
		if listprompt:
			attrs['listLabelString'] = listprompt
		if selectionprompt:
			attrs['selectionLabelString'] = selectionprompt
		print attrs
	#	form = toplevel._main.CreateSelectionDialog('selectDialog',
	#						    attrs)
	#	self._form = form
	#	form.AddCallback('okCallback', self._ok_callback, None)
	#	form.AddCallback('cancelCallback', self._cancel_callback, None)
	#	if hasattr(self, 'NomatchCallback'):
	#		form.AddCallback('noMatchCallback',
	#				 self._nomatch_callback, None)
	#	for b in [Xmd.DIALOG_APPLY_BUTTON, Xmd.DIALOG_HELP_BUTTON]:
	#		form.SelectionBoxGetChild(b).UnmanageChild()
	#	list = form.SelectionBoxGetChild(Xmd.DIALOG_LIST)
	#	list = []
	#	list.ListAddItems(itemlist, 1)
	#	form.ManageChild()
		
		self._nexty = 0

		
		w = 350
		h = 320 
		x = (win32api.GetSystemMetrics(win32con.SM_CXSCREEN)-w)/2 
		y = (win32api.GetSystemMetrics(win32con.SM_CYSCREEN)-h)/2 
		
		self._form = form = cmifex2.CreateDialogbox(listprompt,0,x,y,w,h,1,0)

		x, y, w, h = form.GetClientRect()

		textx = 10
		texty = 10
		textw = w-20
		texth = 20

		self._nexty = self._nexty+y+texty+texth+10

		combox = 10
		comboy = self._nexty
		combow = w-20
		comboh = h-self._nexty-45
		
		self._nexty = self._nexty+comboh+10

		obx = (w-160)/4
		oby = self._nexty
		obw = 80
		obh = 25

		cbx = w-80-(w-160)/4
		cby = self._nexty

		self._nexty = self._nexty+obh+10

		text = cmifex2.CreateStatic(selectionprompt,form,textx,texty,textw,texth,'left')
		self._controls.append(text)

		self._combo = cmifex2.CreateCombobox(" ", form, combox, comboy,combow, comboh,(1,' ',0))
		self._controls.append(self._combo)

		okbutton = cmifex2.CreateButton("OK",form,obx,oby,obw,obh,('b',' '))
		self._controls.append(okbutton)

		cancelbutton = cmifex2.CreateButton("Cancel",form,cbx,cby,obw,obh,('b',' '))
		self._controls.append(cancelbutton)

		for item in itemlist:
			cmifex2.Add(self._combo,item)
			
		cmifex2.SetCaption(self._combo,default)

		okbutton.HookMessage(self._ok_callback, win32con.WM_LBUTTONDOWN)
		cancelbutton.HookMessage(self._cancel_callback, win32con.WM_LBUTTONDOWN)

		self._window_type = SINGLE
		toplevel._subwindows.append(self)

	#def setcursor(self, cursor):
	#	WIN32_windowbase._win_setcursor(self._form, cursor)

	def is_closed(self):
		return self._form is None

	def close(self):
		if self._form:
			toplevel._subwindows.remove(self)
			#self._form.UnmanageChild()
			#self._form.DestroyWidget()
			for control in self._controls:
				#cmifex2.DestroyWindow(control)
				control.DestroyWindow()
				self._controls.remove(control)
			#cmifex2.DestroyWindow(self._form)
			if self._form:
				self._form.DestroyWindow()
			self._form = None

	def _nomatch_callback(self, widget, client_data, call_data):
		if self.is_closed():
			return
		ret = self.NomatchCallback(call_data.value)
		if ret and type(ret) is StringType:
			showmessage(ret, mtype = 'error')

	
	
	
	def _ok_callback(self, params):
		print params
		if self.is_closed():
			return
		str = cmifex2.GetText(self._combo)
		try:
			func = self.OkCallback
		except AttributeError:
			pass
		else:
			ret = func(str)
			if ret:
				if type(ret) is StringType:
					showmessage(ret, mtype = 'error')
				return
		self.close()
	
	
	
	def old_ok_callback(self, widget, client_data, call_data):
		if self.is_closed():
			return
		try:
			func = self.OkCallback
		except AttributeError:
			pass
		else:
			ret = func(call_data.value)
			if ret:
				if type(ret) is StringType:
					showmessage(ret, mtype = 'error')
				return
		self.close()

	
	def _cancel_callback(self, params):
		if self.is_closed():
			return
		try:
			func = self.CancelCallback
		except AttributeError:
			pass
		else:
			ret = func()
			if ret:
				if type(ret) is StringType:
					showmessage(ret, mtype = 'error')
				return
		self.close()
	
	
	def old_cancel_callback(self, widget, client_data, call_data):
		if self.is_closed():
			return
		try:
			func = self.CancelCallback
		except AttributeError:
			pass
		else:
			ret = func()
			if ret:
				if type(ret) is StringType:
					showmessage(ret, mtype = 'error')
				return
		self.close()
