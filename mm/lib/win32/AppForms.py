__version__ = "$Id$"


# the application uses the objects defined here
# to create FormViews

# Public Objects
# class Window(_WindowHelpers, _MenuSupport):

# Private Mixin Objects:
# class _WindowHelpers:

# Private Objects:
# class _AltSubWindow(_SubWindow):
# class _SubWindow(_Widget, _WindowHelpers):
# class _AlternateSubWindow(_Widget):

# note:
# instances of Window are directly created by windowinterface.Window 
#	Window is a form view window: cmifex2.CreateDialogbox

# Window.SubWindow creates instances of _SubWindow. _SubWindow has the 'create' methods of Window
# Window.AlternateSubWindow creates instances of _AlternateSubWindow 
#	Child Windows: cmifex2.CreateContainerbox


import win32con, win32api, win32ui

from Widgets import *
from Widgets import _Widget,_MenuSupport

from win32modules import cmifex2
from appcon import *
import win32mu

toplevel= None # set by AppTopLevel


##################################################################
class _WindowHelpers:
	def __init__(self):
		self._fixkids = []
		self._fixed = FALSE
		self._children = []

	def close(self):
		self._fixkids = None
		for w in self._children[:]:
			w.close()

	# items with which a window can be filled in
	def Label(self, text, **options):
		return apply(Label, (self, text), options)
	def Button(self, label, callback, **options):
		return apply(Button, (self, label, callback), options)
	def OptionMenu(self, label, optionlist, startpos, cb, **options):
		return apply(OptionMenu,
			     (self, label, optionlist, startpos, cb),
			     options)
	def PulldownMenu(self, menulist, **options):
		return apply(PulldownMenu, (self, menulist), options)

	def Selection(self, listprompt, itemprompt, itemlist, initial, sel_cb,
		      **options):
		return apply(Selection,
			     (self, listprompt, itemprompt, itemlist, initial, sel_cb),
			     options)
	def List(self, listprompt, itemlist, sel_cb, **options):
		return apply(List,
			     (self, listprompt, itemlist, sel_cb), options)
	def TextInput(self, prompt, inittext, chcb, accb, **options):
		return apply(TextInput,
			     (self, prompt, inittext, chcb, accb), options)
	def TextEdit(self, inittext, cb, **options):
		return apply(TextEdit, (self, inittext, cb), options)
	def Separator(self, **options):
		return apply(Separator, (self,), options)
	def ButtonRow(self, buttonlist, **options):
		return apply(ButtonRow, (self, buttonlist), options)
	def Slider(self, prompt, minimum, initial, maximum, cb, **options):
		return apply(Slider,
			     (self, prompt, minimum, initial, maximum, cb),
			     options)
	def Canvas(self, **options):
		from WindowCanvas import Canvas
		return apply(Canvas, (self,), options)
	def SubWindow(self, **options):
		return apply(_SubWindow, (self,), options)
	def AlternateSubWindow(self, **options):
		return apply(_AlternateSubWindow, (self,), options)


##################################################################
class Window(_WindowHelpers,_MenuSupport):
	def __init__(self, title, resizable = 0, grab = 0,
		     Name = 'windowShell', Class = None, **options):
		attrs = {}
		if not title:
			title = ''
		self._title = title
		wattrs = {'title': title,
			  'minWidth': 60, 'minHeight': 60}
		if grab:
			for key, val in wattrs.items():
				attrs[key] = val
			try:
				self.deleteCallback = options['deleteCallback']
			except KeyError:
				pass
		else:
			wattrs['iconName'] = title
			try:
				self.deleteCallback = options['deleteCallback']
			except KeyError:
				pass
		self._showing = FALSE
		self._not_shown = []
		self._shown = []
		_WindowHelpers.__init__(self)
		_MenuSupport.__init__(self)

		par = None
		self._par_wnd = None

		self._wnd = cmifex2.CreateDialogbox(" ", self._par_wnd, 0, 0, 400, 400, 0, grab)
		cmifex2.SetCaption(self._wnd,self._title)
		toplevel._subwindows.append(self)
		self._window_type = SINGLE
		self._align = ''
		self._wnd.HookMessage(self._closeclb, win32con.WM_CLOSE)
		if grab:
			self._wnd.HookMessage(self._focusclb, win32con.WM_KILLFOCUS)
		print self._wnd # delay needed but why? 

	def _focusclb(self, params):
		if params[2] == 0:
			res = 0
		else:
			res = self._wnd.IsChild(params[2])
		if res != 1:
			self._wnd.SetFocus()
	
	def _closeclb(self, params):
			self._wnd.HookMessage(None, win32con.WM_KILLFOCUS)
		#global _in_create_box
		#if _in_create_box==self:
		#	_in_create_box = None
		
		#if _in_create_box != None:
		#	cmifex2.SetFlag(1)
		#else:
		#	cmifex2.SetFlag(0)
			if type(self.deleteCallback) is StringType:
				if self.deleteCallback == 'hide':
					self.hide()
				elif self.deleteCallback == 'close':
					self.close()
				return
			
			try:
				func, a = self.deleteCallback
			except AttributeError:
				pass
			else:
				apply(func, a)
	
	def __repr__(self):
		s = '<Window instance at %x' % id(self)
		if hasattr(self, '_title'):
			s = s + ', title=' + `self._title`
		if self.is_closed():
			s = s + ' (closed)'
		elif self._showing:
			s = s + ' (showing)'
		s = s + '>'
		return s

	def close(self):
		#global _in_create_box
		#if _in_create_box==self:
		#	_in_create_box = None

		try:
			#form = self._form
			form = self._wnd
		except AttributeError:
			return
		try:
			shell = self._shell
		except AttributeError:
			shell = None
		toplevel._subwindows.remove(self)
	#	del self._form
	#	del self._wnd
	#	form.DestroyWidget()
	#	del form
		if shell:
			#shell.UnmanageChild()
			#shell.DestroyWidget()
			del self._shell
			del shell
		_WindowHelpers.close(self)
		_MenuSupport.close(self)
		#cmifex2.DestroyWindow(form)
		if form:
			if cmifex2.IsWin(form) != 0:
				form.DestroyWindow()
				#cmifex2.DestroyWindow(form)
		form= None
		del form
		del self._wnd

	def is_closed(self):
		#return not hasattr(self, '_form')
		return not self._showing

	def setcursor(self, cursor):
		win32mu.SetCursor(cursor)

	def fix(self):
		for w in self._fixkids:
			w.fix()
		#self._form.ManageChild()
		#try:
		#	self._shell.RealizeWidget()
		#except AttributeError:
		#	pass
		self._fixed = TRUE

	def _showme(self, w):
		if self.is_closed():
			return
		#if self.is_showing():
		if not self._showing:
		#	if not w._form.IsSubclass(Xm.Gadget):
		#		w._form.MapWidget()
			return
		elif w in self._not_shown:
			self._not_shown.remove(w)
		elif w not in self._shown:
			self._shown.append(w)
		w._form.ShowWindow(win32con.SW_SHOW)

	def _hideme(self, w):
		if self.is_closed():
			return
		#if self.is_showing():
		if not self._showing:
		#	if not w._form.IsSubclass(Xm.Gadget):
		#		w._form.UnmapWidget()
			return	
		elif w in self._shown:
			self._shown.remove(w)
		elif w not in self._not_shown:
			self._not_shown.append(w)
		w._form.ShowWindow(win32con.SW_HIDE)


	def show(self):
		if not self._fixed:
			self.fix()
		self._showing = TRUE
		for w in self._not_shown:
			if not w.is_closed():
				w._form.ShowWindow(win32con.SW_HIDE)
		for w in self._shown:
			w._form.ShowWindow(win32con.SW_SHOW)
		self._not_shown = []
		self._shown = []
		self._wnd.ShowWindow(win32con.SW_SHOW)
		self._fixkids = []

	def hide(self):
		self._showing = FALSE
		if self._wnd:
			self._wnd.ShowWindow(win32con.SW_HIDE)

	def is_showing(self):
		return self._showing

	def settitle(self, title):
		if self._title != title:
			self._title = title
			self._wnd.SetWindowText(title)

	def getgeometry(self):
		if self.is_closed():
			raise error, 'window already closed'
		x, y, w1, h1 = self._wnd.GetWindowPlacement()[4]
		x1, y1, w, h = self._wnd.GetClientRect()
		return x / toplevel._hmm2pxl, y / toplevel._vmm2pxl, \
		       w / toplevel._hmm2pxl, h / toplevel._vmm2pxl

	def pop(self):
		pass

	def _delete_callback(self, widget, client_data, call_data):
		if type(client_data) is StringType:
			if client_data == 'hide':
				self.hide()
			elif client_data == 'close':
				self.close()
			else:
				raise error, 'bad deleteCallback argument'
			return
		func, args = client_data
		apply(func, args)


class WindowV(Window):
	def __init__(self,view):
		attrs = {}
		self._title = ''
		self._showing = FALSE
		self._not_shown = []
		self._shown = []
		_WindowHelpers.__init__(self)
		_MenuSupport.__init__(self)

		self._par_wnd = view

		self._wnd = view 
		toplevel._subwindows.append(self)
		self._window_type = SINGLE
		self._align = ''

##################################################################
class _SubWindow(_Widget, _WindowHelpers):
	def __init__(self, parent, name = 'windowSubwindow', **options):
		attrs = {}
		self._attachments(attrs, options)
		
		left = attrs['left']
		top = attrs['top']
		width = attrs['right']
		height = attrs['bottom']
		
		if hasattr(parent,'_wnd'):obj=parent._wnd
		else: obj=parent
		self._wnd = cmifex2.CreateContainerbox(obj,left,top,width,height)
				
		_WindowHelpers.__init__(self)
		_Widget.__init__(self, parent, self._wnd)
		parent._fixkids.append(self)
		self._window_type = SINGLE
		self._align = ''

	def __repr__(self):
		return '<_SubWindow instance at %x>' % id(self)

	def close(self):
		_Widget.close(self)
		_WindowHelpers.close(self)

	def fix(self):
		for w in self._fixkids:
			w.fix()
		self._fixed = TRUE

	def show(self):
		_Widget.show(self)
		if self._fixed:
			self._fixkids = []


##################################################################
class _AltSubWindow(_SubWindow):
	def __init__(self, parent, name, **options):
		self._parent = parent
		attrib = {}
		self._attachments(attrib, options)

		lft = attrib['left']
		tp = attrib['top']
		wth = attrib['right']
		hght = attrib['bottom']
		_SubWindow.__init__(self, parent, name = name, left = lft, top = tp, right = wth, bottom = hght)
		self._window_type = SINGLE

	def show(self):
		for w in self._parent._windows:
			w.hide()
		_SubWindow.show(self)


##################################################################
class _AlternateSubWindow(_Widget):
	def __init__(self, parent, name = 'windowAlternateSubwindow',
		     **options):
		attrs = {'allowOverlap': TRUE}
		self._attachments(attrs, options)

		left = attrs['left']
		top = attrs['top']
		width = attrs['right']
		height = attrs['bottom']

		self._wnd = cmifex2.CreateContainerbox(parent._wnd,left,top,width,height)
		
		
		self._windows = []
		_Widget.__init__(self, parent, self._wnd)
		parent._fixkids.append(self)
		self._fixkids = []
		self._children = []
		self._window_type = SINGLE
		self._align = ''

	def __repr__(self):
		return '<_AlternateSubWindow instance at %x>' % id(self)

	def close(self):
		_Widget.close(self)
		self._windows = None
		self._fixkids = None

	def SubWindow(self, name = 'windowSubwindow', **options):
		attrib = {}
		self._attachments(attrib, options)

		lft = attrib['left']
		tp = attrib['top']
		wth = attrib['right']
		hght = attrib['bottom']
		widget = _AltSubWindow(self, name = name, left = lft, top = tp, right = wth, bottom = hght)
		for w in self._windows:
			w.hide()
		self._windows.append(widget)
		return widget

	def fix(self):
		for w in self._fixkids:
			w.fix()


