import WIN32_windowbase
from WIN32_windowbase import TRUE, FALSE, SINGLE, win32Cursors

import win32con, win32api, win32ui, cmifex, cmifex2
import CloseDialogRC, WMEVENTS
from pywin.mfc import dialog

WM_MAINLOOP = 200

from types import *
import math
#from math import *

[SAVE_CMIF, OPEN_FILE] = range(2)
UNIT_MM, UNIT_SCREEN, UNIT_PXL = 0, 1, 2
[_X, _Y, _WIDTH, _HEIGHT] = range(4)
_def_useGadget = 1

_rb_message = """\
Use left mouse button to draw a box.
Click `OK' when ready or `Cancel' to cancel."""
_rb_done = '_rb_done'			# exception to stop create_box loop
_in_create_box = None



toplevel = None

# size of arrow head
ARR_LENGTH = 18
ARR_HALFWIDTH = 5
ARR_SLANT = float(ARR_HALFWIDTH) / float(ARR_LENGTH)

class _Toplevel(WIN32_windowbase._Toplevel):
	def newwindow(self, x, y, w, h, title, visible_channel = TRUE, type_channel = SINGLE, units = UNIT_MM, pixmap = 0, menubar = None, canvassize = None):
	#UNITS ARE ignored
## 		if ((pixmap is None) or (pixmap == 0)):
## 			pixmap = toplevel._depth <= 8
		#return _Window(self, x, y, w, h, title, 0, pixmap)
		global toplevel
		if toplevel == None:
			toplevel = self
		return _Window(self, x, y, w, h, title, visible_channel, type_channel, 0, pixmap, 0, units, menubar, canvassize)


	def newcmwindow(self, x, y, w, h, title, visible_channel = TRUE, type_channel = SINGLE, units = UNIT_MM, pixmap = 0, menubar = None, canvassize = None):
	#UNITS ARE ignored
## 		if ((pixmap is None) or (pixmap == 0)):
## 			pixmap = toplevel._depth <= 8
		#return _Window(self, x, y, w, h, title, 1, pixmap)
		return _Window(self, x, y, w, h, title, visible_channel, type_channel, 1, pixmap, 0, units, menubar, canvassize)


	def getsize(self):
		return toplevel._mscreenwidth, toplevel._mscreenheight

class _Window(WIN32_windowbase._Window):
	def __init__(self, parent, x, y, w, h, title, visible, type_channel, defcmap=0,pixmap, transparent=0, units = UNIT_MM, menubar = None, canvassize = None):
		#WIN32_windowbase._Window.__init__(self, parent, x, y, w, h, title, defcmap, pixmap)
		self._canv = None
		WIN32_windowbase._Window.__init__(self, parent, x, y, w, h, title, visible, type_channel, defcmap, pixmap,
			transparent, units, menubar, canvassize)
		self.arrowcache = {}

		self.box_created = 0     # indicates wheather box has been created or not
		self.box_started = 0     # indicates wheather create_box procedure has begun

		self._next_create_box = []

		self._old_callbacks = {}

	def close(self):
		self.arrowcache = {}
		WIN32_windowbase._Window.close(self)

	def newdisplaylist(self, *bgcolor):
		if bgcolor != ():
			bgcolor = bgcolor[0]
		else:
			bgcolor = self._bgcolor
		return _DisplayList(self, bgcolor)


	#################################
	# overridden settitle
	# by MUADDIB
	# did not exist
	#################################
	def settitle(self, title):
		if self._hWnd != None:
			if self._title != title:
				self._title = title
				self._hWnd.SetWindowText(title)

	def create_box(self, msg, callback, box = None):

		global _in_create_box


		if _in_create_box:
			_in_create_box._next_create_box.append((self, msg, callback, box))
			return
		if self.is_closed():
			apply(callback, ())
			return

		_in_create_box = self
		self.pop()

		import win32con
		for win in self._subwindows :
			win._hWnd.ShowWindow(win32con.SW_HIDE)

		if msg:
			msg = msg + '\n\n' + _rb_message
		else:
			msg = _rb_message

		self._rb_dl = self._active_displist
		if self._rb_dl:
			d = self._rb_dl.clone()
		else:
			d = self.newdisplaylist()
		#self._rb_transparent = []
		#sw = self._subwindows[:]
		#sw.reverse()
		#r = Xlib.CreateRegion()
		#for win in sw:
		#	if not win._transparent:
		#		# should do this recursively...
		#		self._rb_transparent.append(win)
		#		win._transparent = 1
		#		d.drawfbox(win._bgcolor, win._sizes)
				#apply(r.UnionRectWithRegion, win._rect)
		#ls = []
		#top_w, c_name  = self.find_topwin_channel(box)
		#print top_w, c_name
		#self.find_channels(top_w.hierarchyview.root,ls,c_name)
		#print ls
		#tmp = []
		#tmp = self.find_windows(top_w,ls)
		#if tmp == []:
		tmp = self._subwindows
		#print tmp

		#for win in self._subwindows:
		for win in tmp:
			b = win._sizes
			if b != (0, 0, 1, 1):
				d.drawbox(b)
		self._rb_display = d.clone()
		d.fgcolor((255, 0, 0))
		if box:
			d.drawbox(box)
		#if box:
		#	x, y, w, h = box
		#	self.DrawRectangle((x, y, x+w, y+h))

		#if self._rb_transparent:
		#	self._mkclip()
		#	self._do_expose(r)
		#	self._rb_reg = r
		d.render()
		self._rb_curdisp = d
		#self._rb_dialog = showmessage(
		#	msg, mtype = 'message', grab = 0,
		#	callback = (self._rb_done, ()),
		#	cancelCallback = (self._rb_cancel, ()))


		self._rb_dialog = dialog.Dialog(CloseDialogRC.IDD_CREATE_BOX)
		self._rb_dialog.HookCommand(self._rb_cancel, win32con.IDCANCEL)
		self._rb_dialog.HookCommand(self._rb_done, win32con.IDOK)
		self._rb_dialog.CreateWindow()
		label = self._rb_dialog.GetDlgItem(CloseDialogRC.IDC_BOX_LABEL)
		label.SetWindowText(msg)

		wind = self
		while wind._parent != toplevel:
			wind = wind._parent

		wli, wti, wri, wbi = wind._hWnd.GetWindowPlacement()[4]
		wl, wt, wr, wb = (wli, wti, wri, wbi)

		if wl-310<0:
			if wr+320<cmifex.GetScreenWidth():
				wl = wr+320
			else:
				if wt-210>0:
					wt = wt-210
				elif wb+210<cmifex.GetScreenHeight():
					wt = wb+10
				wl = 310

		if wt+200>cmifex.GetScreenHeight() and wt==wti:
			wt = wt - 210

		self._rb_dialog.MoveWindow((wl-310, wt, wl-10, wt+200))
		self._rb_dialog.ShowWindow(win32con.SW_SHOW)
		self._rb_callback = callback
		#form = self._form
		form = self._hWnd

		#form.AddEventHandler(X.ButtonPressMask, FALSE,
		#		     self._start_rb, None)
		#form.AddEventHandler(X.ButtonMotionMask, FALSE,
		#		     self._do_rb, None)
		#form.AddEventHandler(X.ButtonReleaseMask, FALSE,
		#		     self._end_rb, None)
		#form.HookMessage(self._start_rb, win32con.WM_LBUTTONDOWN)
		#form.HookMessage(self._end_rb, win32con.WM_LBUTTONUP)


		#save existing message handlers (callbacks)
		for k in self._callbacks.keys():
			self._old_callbacks[k] = self._callbacks[k]

		# enable mouse events
		form.HookMessage(self._do_rb, win32con.WM_MOUSEMOVE)
		#form.HookMessage(self._end_rb, win32con.WM_LBUTTONUP)
		self.register(WMEVENTS.Mouse0Press, self._start_rb, None)
		self.register(WMEVENTS.Mouse0Release, self._end_rb, None)



		#cursor = form.Display().CreateFontCursor(Xcursorfont.crosshair)
		#form.GrabButton(X.AnyButton, X.AnyModifier, TRUE,
		#		X.ButtonPressMask | X.ButtonMotionMask
		#			| X.ButtonReleaseMask,
		#		X.GrabModeAsync, X.GrabModeAsync, form, cursor)

		#v = form.GetValues(['foreground', 'background'])
		#v['foreground'] = v['foreground'] ^ v['background']
		#v['function'] = X.GXxor
		#v['line_style'] = X.LineOnOffDash
		#v['line_style'] = X.LineOnOffDash
		#self._gc_rb = form.GetGC(v)
		#self._gc_rb = self._hWnd.GetDC()

#		print "---START OF create_box---"
#		print "box--->", box

		if box:
			x, y, w, h = self._convert_coordinates(box)
			#wx, wy, ww, wh = self._hWnd.GetClientRect()
			#x = int(box[0]*ww)
			#y = int(box[1]*wh)
			#w = int(box[2]*ww)
			#h = int(box[3]*wh)
			#print "x, y, w, h--->", x, y, w, h
			if w < 0:
				x, w = x + w, -w
			if h < 0:
				y, h = y + h, -h
#			print "x, y, w, h is now--->", x, y, w, h
			self._rb_box = x, y, w, h
			self._rb_start_x = x
			self._rb_start_y = y
			self._rb_width = w
			self._rb_height = h
		else:
			self._rb_start_x, self._rb_start_y, self._rb_width, \
					  self._rb_height = self._rect
			self._rb_box = self._rect
#			print "self._rect of create_box--->", self._rect
		#Htmlex.SetCursor(self._hWnd, 2)
		cmifex.SetCursor(win32Cursors['hand'])
		self._cur_cur = 2
#		print "---END OF create_box---"


	def find_topwin_channel(self, box):
		import TopLevel
		found = 0
		top_w = None
		c_name = None
		for top in TopLevel.opentops:
			for i in top.views[0].channels.keys():
				if hasattr(top.views[0].channels[i],'window'):
					if hasattr(top.views[0].channels[i].window,'_hWnd'):
						if top.views[0].channels[i].window==self:
							found = 1
							top_w = top
							break

			if found:
				break

		sub = None
		for win in self._subwindows:
			b = win._sizes
			if b != (0, 0, 1, 1):
				if b == box:
					sub = win

		for i in top_w.views[0].channels.keys():
			if hasattr(top_w.views[0].channels[i],'window'):
				if hasattr(top_w.views[0].channels[i].window,'_hWnd'):
					if top_w.views[0].channels[i].window==sub:
						c_name = top_w.views[0].channels[i]._name
						break
		return top_w, c_name

	def find_channels(self, node, ls, name):
		for c_list in node.GetAllChannels():
			if c_list != None:
				if name in c_list and len(c_list)>1:
					for item in c_list:
						if item not in ls:
							ls.append(item)
		for n in node.GetChildren():
			self.find_channels(n,ls,name)

	def find_windows(self, top, ls):
		import TopLevel
		tmp = []
		for i in top.views[0].channels.keys():
			if hasattr(top.views[0].channels[i],'window'):
				if top.views[0].channels[i]._name in ls and \
					top.views[0].channels[i].window in self._subwindows:
						tmp.append(top.views[0].channels[i].window)
		return tmp



	def hitarrow(self, point, src, dst):
		# return 1 iff (x,y) is within the arrow head
		sx, sy = self._convert_coordinates(src)
		dx, dy = self._convert_coordinates(dst)
		x, y = self._convert_coordinates(point)
		lx = dx - sx
		ly = dy - sy
		if lx == ly == 0:
			angle = 0.0
		else:
			angle = math.atan2(lx, ly)
		cos = math.cos(angle)
		sin = math.sin(angle)
		# translate
		x, y = x - dx, y - dy
		# rotate
		nx = x * cos - y * sin
		ny = x * sin + y * cos
		# test
		if ny > 0 or ny < -ARR_LENGTH:
			return FALSE
		if nx > -ARR_SLANT * ny or nx < ARR_SLANT * ny:
			return FALSE
		return TRUE


	def newwindow(self, coordinates, transparent = 0, type_channel, pixmap = 0, z=0):
		win = _SubWindow(self, coordinates, transparent, type_channel, 0, pixmap, z)
		win._window_state = HIDDEN
		return win

	#def newwindow(self, coordinates, pixmap = 0, transparent = 0, type_channel = SINGLE):
	#	return _SubWindow(self, coordinates, 0, pixmap, transparent, type_channel)

	def newcmwindow(self, coordinates, transparent = 0, type_channel, pixmap = 0, z=0):
		win = _SubWindow(self, coordinates, transparent, type_channel, 1, pixmap, z)
		win._window_state = HIDDEN
		return win

	#def newcmwindow(self, coordinates, pixmap = 0, transparent = 0, type_channel = SINGLE):
	#	return _SubWindow(self, coordinates, 1, pixmap, transparent, type_channel)



	#def newwindow(self, coordinates, pixmap = 0, transparent = 0, type_channel = SINGLE):
	#	return _SubWindow(self, coordinates, 0, pixmap, transparent, type_channel)
	#	#return _Window(self, coordinates, 0, pixmap, transparent, type_channel)

	#def newcmwindow(self, coordinates, pixmap = 0, transparent = 0, type_channel = SINGLE):
	#	return _SubWindow(self, coordinates, 1, pixmap, transparent, type_channel)

	# have to override these for create_box
	def _input_callback(self, form, client_data, call_data):
		if _in_create_box:
			return
		WIN32_windowbase._Window._input_callback(self, form, client_data,
						     call_data)

	def _resize_callback(self, params):
		self.arrowcache = {}
		w = _in_create_box
		if w:
			raised = 1
			next_create_box = w._next_create_box
			w._next_create_box = []
			w._rb_cancel(0,0)
			w._next_create_box[0:0] = next_create_box

		WIN32_windowbase._Window._resize_callback(self, params)

		if w:
			w._rb_end()

	def _delete_callback(self, form, client_data, call_data):
		self.arrowcache = { }
		w = _in_create_box
		if w:
			raised = 1
			next_create_box = w._next_create_box
			w._next_create_box = []
			w._rb_cancel(0,0)
			w._next_create_box[0:0] = next_create_box


		WIN32_windowbase._Window._delete_callback(self, form, client_data,
						      call_data)
		if w:
			w._rb_end()

	# supporting methods for create_box
	def _rb_finish(self):
		#Htmlex.SetCursor(self._hWnd, 0)
		cmifex.SetCursor(0)
		global _in_create_box
		_in_create_box = None
		#if self._rb_transparent:
		#	for win in self._rb_transparent:
		#		win._transparent = 0
			#self._mkclip()
			#self._do_expose(self._rb_reg)
			#del self._rb_reg
		#del self._rb_transparent
		form = self._hWnd
		#form.RemoveEventHandler(X.ButtonPressMask, FALSE,
		#			self._start_rb, None)
		#form.RemoveEventHandler(X.ButtonMotionMask, FALSE,
		#			self._do_rb, None)
		#form.RemoveEventHandler(X.ButtonReleaseMask, FALSE,
		#			self._end_rb, None)
		#form.UngrabButton(X.AnyButton, X.AnyModifier)


		#self._rb_dialog.close()
		self._rb_dialog.DestroyWindow()
		self._rb_dialog = None

		if self._rb_dl and not self._rb_dl.is_closed():
			self._rb_dl.render()
		self._rb_display.close()
		self._rb_curdisp.close()
		#del self._rb_callback
		del self._rb_dialog
		del self._rb_dl
		del self._rb_display
		#del self._gc_rb
		# show all hidden windows since drawing is done
		for win in self._subwindows :
			win._hWnd.ShowWindow(win32con.SW_SHOW)

	def _rb_cvbox(self):
		x0 = self._rb_start_x
		y0 = self._rb_start_y
		x1 = x0 + self._rb_width
		y1 = y0 + self._rb_height
		if x1 < x0:
			x0, x1 = x1, x0
		if y1 < y0:
			y0, y1 = y1, y0
		x, y, width, height = self._rect

		if self._parent != toplevel:
			x = 0
			y = 0

		if x0 < x: x0 = x
		if x0 >= x + width: x0 = x + width - 1
		if x1 < x: x1 = x
		if x1 >= x + width: x1 = x + width - 1
		if y0 < y: y0 = y
		if y0 >= y + height: y0 = y + height - 1
		if y1 < y: y1 = y
		if y1 >= y + height: y1 = y + height - 1
		return float(x0 - x) / (width - 1), \
		       float(y0 - y) / (height - 1), \
		       float(x1 - x0) / (width - 1), \
		       float(y1 - y0) / (height - 1)


	def _null_rb(self, params):
		return


	def _rb_done(self, par1, par2):
#		print 'Create box done'
		self.unregister(WMEVENTS.Mouse0Release)
		self.unregister(WMEVENTS.Mouse0Press)
		self._hWnd.HookMessage(self._null_rb, win32con.WM_MOUSEMOVE)

		callback = self._rb_callback
		self._rb_finish()
#		print 'BOX IS:'
#		print self._rb_cvbox()
#		print self._rect
		apply(callback, self._rb_cvbox())

#		print 'BEFORE RESTORING :'
#		print self._old_callbacks
#		print self._callbacks
		#restore message handlers (callbacks)
		for k in self._old_callbacks.keys():
			self._callbacks[k] = self._old_callbacks[k]
#		print 'restoring------------', self._callbacks
		for k in self._old_callbacks.keys():
			del self._old_callbacks[k]

		self.box_created = 1
		self._rb_end()

	def _rb_cancel(self, par1, par2):
		callback = self._rb_callback
		self._rb_finish()
		apply(callback, ())
		self.box_created = 1
		self._rb_end()

	def _rb_end(self):
		#execute pending create_box calls
		next_create_box = self._next_create_box
		self._next_create_box = []
		for win, msg, cb, box in next_create_box:
			win.create_box(msg, cb, box)


	def _rb_draw(self, flag=0):
		x = self._rb_start_x
		y = self._rb_start_y
		w = self._rb_width
		h = self._rb_height
		if w < 0:
			x, w = x + w, -w
		if h < 0:
			y, h = y + h, -h
		if flag==1:
			cmifex.DrawRectangle(self._hWnd, (x, y, x+w, y+h), self._bgcolor, " ")
		else:
			cmifex.DrawRectangle(self._hWnd, (x, y, x+w, y+h), (0,0,0), "d")
		#self.DrawRectangle((x, y, x+w, y+h))


	def DrawRectangle(self, rect):
		x0, y0, x1, y1 = rect
		cmifex.BeginPaint(self._hWnd, 0)
		dcd = self._hWnd.GetDC()
		#dcd = dc
		col = win32api.RGB(255, 255, 255)
		dcd.FillSolidRect(self._hWnd.GetClientRect(), col)
		dcd.MoveTo(x0, y0)
		dcd.LineTo(x0, y1)
		dcd.LineTo(x1, y1)
		dcd.LineTo(x1, y0)
		dcd.LineTo(x0, y0)
		self._hWnd.ReleaseDC(dcd)
		cmifex.EndPaint(self._hWnd, 0)




	def _rb_constrain(self, event):
		#print "---START OF _rb_constrain---"
		x, y, w, h = self._rect
		if self._parent != toplevel:
			x = 0
			y = 0
		#print "x, y, w, h--->", x, y, w, h
		t0 = event[0]
		t1 = event[1]
		if event[0] < x:
			#event[0] = x
			t0 = x
		if event[0] >= x + w:
			#event[0] = x + w - 1
			t0 = x + w -1
		if event[1] < y:
			#event[1] = y
			t1 = y
		if event[1] >= y + h:
			#event[1] = y + h - 1
			t1 = y + h -1

		#print "event--->", event
		#print "---END OF _rb_constrain---"
		return (t0, t1)


	def _rb_common(self, event):
		#print "---START OF _rb_common---"
		if not hasattr(self, '_rb_cx'):
			a = []
			ev = 0
			val = []
			val.append(event[0])
			val.append(event[1])
			val.append(a)
			self._start_rb(0, self._hWnd, ev, val)
		#self._rb_draw()
		event = self._rb_constrain(event)
		if self._rb_cx and self._rb_cy:
			#print '_rb_cx and  _rb_cy EXIST'
			x, y, w, h = self._rect
			if self._parent != toplevel:
				x = 0
				y = 0
			dx = event[0] - self._rb_last_x
			dy = event[1] - self._rb_last_y
			self._rb_last_x = event[0]
			self._rb_last_y = event[1]
			self._rb_start_x = self._rb_start_x + dx
			if self._rb_start_x + self._rb_width > x + w:
				self._rb_start_x = x + w - self._rb_width
			if self._rb_start_x < x:
				self._rb_start_x = x
			self._rb_start_y = self._rb_start_y + dy
			if self._rb_start_y + self._rb_height > y + h:
				self._rb_start_y = y + h - self._rb_height
			if self._rb_start_y < y:
				self._rb_start_y = y
		else:
			#print '_rb_cx and  _rb_cy DO NOT EXIST'
			if not self._rb_cx:
				self._rb_width = event[0] - self._rb_start_x
				#print 'EVENT[0], START_X IS:', event[0], self._rb_start_x
				#print 'WIDTH IS:', self._rb_width
			if not self._rb_cy:
				self._rb_height = event[1] - self._rb_start_y
		self._rb_box = 1
		#print '_rb_common--->', self._rb_start_x, self._rb_start_y, self._rb_width, self._rb_height
		#print "---END OF _rb_common---"


	def convert_to_client(self, params):
		px, py = params[5]
		x0, y0, w0, h0 = self._hWnd.GetWindowPlacement()[4]
		x1, y1, z1, w1 = self._hWnd.ScreenToClient((px, py, px, py))
		return (x1, y1, z1, w1)

	#def _start_rb(self, w, data, event):
	#def _start_rb(self, params):
	def _start_rb(self, dummy, window, ev, val):
#		print '---START OF start_rb---'
		# called on mouse press
		if  not _in_create_box:
			return
		point = (val[0], val[1])
#		print "point--->", point
		vl = self._convert_coordinates(point)
		#wx, wy, ww, wh = self._hWnd.GetClientRect()
		#vl = (int(point[0]*ww), int(point[1]*wh))

#		print "vl--->", vl

		#Just examine the case where we have 'nested' windows
		#That happens when an anchor lies on a child window
		#then we refer to the child window
		#parent = self._hWnd.GetParent()
		#x1 = 0
		#if (parent <> None):
		#	x1, x2, x3, x4 = parent.GetWindowPlacement()[4]
		#	print 'PARENT EXISTS:'
		#	print parent.GetWindowPlacement()[4]
		#print x1

		px = vl[0]
		#px = px - x1
		py = vl[1]


		self.box_started = 1
		import Htmlex
		#Htmlex.SetCursor(self._hWnd, 2)
		event=(px, py)
		#event = (vl[0], vl[1])

		self._rb_display.render()
		self._rb_curdisp.close()
		event = self._rb_constrain(event)
#		print "final value of event", event
		if self._rb_box:
			x = self._rb_start_x
			y = self._rb_start_y
			w = self._rb_width
			h = self._rb_height
#			print 'START X, START Y, W, H :', x, y, w, h
			if w < 0:
				x, w = x + w, -w
			if h < 0:
				y, h = y + h, -h
			if x + w/4 < event[0] < x + w*3/4:
				#print 'X-------------- took value'
				self._rb_cx = 1
			else:
				self._rb_cx = 0
				if event[0] >= x + w*3/4:
					x, w = x + w, -w
			if y + h/4 < event[1] < y + h*3/4:
				#print 'Y-------------- took value'
				self._rb_cy = 1
			else:
				self._rb_cy = 0
				if event[1] >= y + h*3/4:
					y, h = y + h, -h
			if self._rb_cx and self._rb_cy:
				self._rb_last_x = event[0]
				self._rb_last_y = event[1]
				self._rb_start_x = x
				self._rb_start_y = y
				self._rb_width = w
				self._rb_height = h
			else:
				if not self._rb_cx:
					self._rb_start_x = x + w
					self._rb_width = event[0] - self._rb_start_x
				if not self._rb_cy:
					self._rb_start_y = y + h
					self._rb_height = event[1] - self._rb_start_y
#				print 'else of self._rb_cx and self._rb_cy --->', self._rb_start_x, self._rb_start_y, self._rb_width, self._rb_height

			if self._rb_cx or self._rb_cy:
				if self._rb_cx and self._rb_cy:
					self._cur_cur = win32Cursors['g_hand'] #hand
				elif self._rb_cx and self._rb_height>0:
					self._cur_cur = win32Cursors['dstrech'] #drag down
				elif self._rb_cx and self._rb_height<0:
					self._cur_cur = win32Cursors['ustrech'] #drag up
				elif self._rb_cy and self._rb_width>0:
					self._cur_cur = win32Cursors['rstrech'] #drag right
				elif self._rb_cy and self._rb_width<0:
					self._cur_cur = win32Cursors['lstrech'] #drag left
			else:
				if self._rb_width>0 and self._rb_height>0:
					self._cur_cur = win32Cursors['drstrech'] #drag right bottom corner
				if self._rb_width>0 and self._rb_height<0:
					self._cur_cur = win32Cursors['urstrech'] #drag right top corner
				if self._rb_width<0 and self._rb_height>0:
					self._cur_cur = win32Cursors['dlstrech'] #drag left bottom corner
				if self._rb_width<0 and self._rb_height<0:
					self._cur_cur = win32Cursors['ulstrech'] #drag left top corner
			#Htmlex.SetCursor(self._hWnd, self._cur_cur)
			cmifex.SetCursor(self._cur_cur)
		else:
			self._rb_start_x = event[0]
			self._rb_start_y = event[1]
			self._rb_width = self._rb_height = 0
			self._rb_cx = self._rb_cy = 0
#			print 'else of if box--->', self._rb_start_x, self._rb_start_y, self._rb_width, self._rb_height
		self._rb_draw()
#		print '---END OF start_rb---'

	#def _do_rb(self, w, data, event):
	def _do_rb(self, params):
		#print "---START OF _do_rb---"
		#print "params--->", params
		# called on mouse drag
		#Htmlex.SetCursor(self._hWnd, self._cur_cur)
		cmifex.SetCursor(self._cur_cur)
		if  not _in_create_box:
			return
		if (params[2] == 1):
			self._hWnd.SetCapture()
			self._rb_draw(1)
			if self._rb_display:
				self._rb_display._render(self._hWnd, 1)
			t = self.convert_to_client(params)
			event = (t[0], t[1])
			self._rb_common(event)
			self._rb_draw()
		#print "---END OF _do_rb---"


	#def _end_rb(self, w, data, event):
	#def _end_rb(self, params):
	def _end_rb(self, dummy, window, ev, val):
		# called on mouse release
		self._hWnd.ReleaseCapture()
#		print "---START OF _end_rb---"
		self._cur_cur = 2
		if  not _in_create_box:
			return
		#t = self.convert_to_client(params)
		#event = (t[0], t[1])

		#x, y, w, h = self._convert_coordinates(box)
		#wx, wy, ww, wh = self._hWnd.GetClientRect()

		vl = self._convert_coordinates((val[0],val[1]))
#		print "vl--->", vl

        #Just examine the case where we have 'nested' windows
		#That happens when an anchor lies on a child window
		#then we refer to the child window
		#parent = self._hWnd.GetParent()
		#x1 = 0
		#if (parent <> None):
		#	x1, x2, x3, x4 = parent.GetWindowPlacement()[4]
		#	print 'PARENT EXISTS:'
		#	print parent.GetWindowPlacement()[4]
		#print x1

		px = vl[0]
		#px = px - x1
		py = vl[1]

		event = (px, py)

		self._rb_common(event)
		self._rb_curdisp = self._rb_display.clone()
		self._rb_curdisp.fgcolor((255, 0, 0))
		self._rb_curdisp.drawbox(self._rb_cvbox())
		self._rb_display.render()
		self._rb_curdisp.render()
		#self.box_created = 1
		#Htmlex.SetCursor(self._hWnd, 0)
		cmifex.SetCursor(0)
		#del self._rb_cx
		#del self._rb_cy
#		print "---END OF _end_rb---"

class _SubWindow(WIN32_windowbase._BareSubWindow, _Window):
	# assistant comments for finding the proper order of the constructor's args
	#pass
	#win = _SubWindow(self, coordinates, transparent, type_channel, 1, pixmap)
	def __init__(self, parent, coordinates, transparent, type_channel, defcmap, pixmap, z=0):
		#WIN32_windowbase._BareSubWindow.__init__(self, parent, coordinates, defcmap, pixmap, transparent)
		WIN32_windowbase._BareSubWindow.__init__(self, parent, coordinates, transparent, type_channel, defcmap, pixmap, z)
		self.arrowcache = {}
		self._next_create_box = []
		if parent._transparent:
			self._transparent = parent._transparent
		else:
			if transparent not in (-1, 0, 1):
				raise error, 'invalid value for transparent arg'
			self._transparent = transparent

class _DisplayList(WIN32_windowbase._DisplayList):
	def _do_render(self, entry, region):
		cmd = entry[0]
		w = self._window
		#gc = w._gc
		if cmd == 'fpolygon':
			fg = entry[1] #gc.foreground
			#gc.foreground = entry[1]
			cmifex.FillPolygon(self._window._hWnd, entry[2], fg)
			#gc.foreground = fg
		elif cmd == '3dbox':
			cl, ct, cr, cb = entry[1]
			l, t, w, h = entry[2]
			r, b = l + w, t + h
			l = l+1
			t = t+1
			r = r-1
			b = b-1
			l1 = l - 1
			t1 = t - 1
			r1 = r
			b1 = b
			ll = l + 2
			tt = t + 2
			rr = r - 2
			bb = b - 3
			fg = cl #gc.foreground
			#gc.foreground = cl
			ls = [(l1,t1),(ll,tt),(ll,bb),(l1,b1)]
			cmifex.FillPolygon(self._window._hWnd, ls, fg)
			fg = ct
			ls = [(l1,t1),(r1,t1),(rr,tt),(ll,tt)]
			cmifex.FillPolygon(self._window._hWnd, ls, fg)
			fg = cr
			ls = [(r1,t1),(r1,b1),(rr,bb),(rr,tt)]
			cmifex.FillPolygon(self._window._hWnd, ls, fg)
			fg = cb
			ls = [(l1,b1),(ll,bb),(rr,bb),(r1,b1)]
			cmifex.FillPolygon(self._window._hWnd, ls, fg)
			#gc.foreground = fg
		elif cmd == 'diamond':
			fg = self._fgcolor
			x, y, w, h = entry[1]

			d, m = divmod(w,2)
			if m==1:
				w = w+1

			d, m = divmod(h,2)
			if m==1:
				h = h+1

			ls = [(x, y + h/2), (x + w/2, y), (x + w, y + h/2), (x + w/2, y + h), (x, y + h/2)]
			cmifex.DrawLines(self._window._hWnd, ls, fg)
		elif cmd == 'fdiamond':
			fg = entry[1] #gc.foreground
			#gc.foreground = entry[1]
			x, y, w, h = entry[2]

			d, m = divmod(w,2)
			if m==1:
				w = w+1

			d, m = divmod(h,2)
			if m==1:
				h = h+1

			ls = [(x, y + h/2), (x + w/2, y), (x + w, y + h/2), (x + w/2, y + h), (x, y + h/2)]
			cmifex.FillPolygon(self._window._hWnd, ls,	fg)
			#gc.foreground = fg
		elif cmd == '3ddiamond':
			cl, ct, cr, cb = entry[1]
			l, t, w, h = entry[2]

			d, m = divmod(w,2)
			if m==1:
				w = w+1

			d, m = divmod(h,2)
			if m==1:
				h = h+1

			r = l + w
			b = t + h
			x = l + w/2
			y = t + h/2
			n = int(3.0 * w / h + 0.5)
			ll = l + n
			tt = t + 3
			rr = r - n
			bb = b - 3
			fg = cl #gc.foreground
			#gc.foreground = cl
			ls = [(l, y), (x, t), (x, tt), (ll, y)]
			cmifex.FillPolygon(self._window._hWnd, ls, fg)
			fg = ct
			ls = [(x, t), (r, y), (rr, y), (x, tt)]
			cmifex.FillPolygon(self._window._hWnd, ls,	fg)
			fg = cr
			ls = [(r, y), (x, b), (x, bb), (rr, y)]
			cmifex.FillPolygon(self._window._hWnd, ls,	fg)
			fg = cb
			ls = [(l, y), (ll, y), (x, bb), (x, b)]
			cmifex.FillPolygon(self._window._hWnd, ls,	fg)
			#gc.foreground = fg
		elif cmd == 'arrow':
			fg = entry[1] #gc.foreground
			#gc.foreground = entry[1]
			#apply(gc.DrawLine, entry[2])
			cmifex.DrawLine(self._window._hWnd, entry[2], fg)
			cmifex.FillPolygon(self._window._hWnd, entry[3], fg)
			#gc.foreground = fg
		else:
			WIN32_windowbase._DisplayList._do_render(self, entry, region)

	def clone(self):
		w = self._window
		new = _DisplayList(w, self._bgcolor)
		# copy all instance variables
		new._list = self._list[:]
		new._font = self._font
		if self._rendered:
			new._cloneof = self
			new._clonestart = len(self._list)
			new._clonedata = self._fgcolor, self._font
		for key, val in self._optimdict.items():
			new._optimdict[key] = val
		return new

	def drawfpolygon(self, color, points):
		if self._rendered:
			raise error, 'displaylist already rendered'
		w = self._window
		color = w._convert_color(color)
		p = []
		for point in points:
			p.append(w._convert_coordinates(point))
		self._list.append('fpolygon', color, p)
		self._optimize(1)

	def draw3dbox(self, cl, ct, cr, cb, coordinates):
		if self._rendered:
			raise error, 'displaylist already rendered'
		window = self._window
		coordinates = window._convert_coordinates(coordinates)
		cl = window._convert_color(cl)
		ct = window._convert_color(ct)
		cr = window._convert_color(cr)
		cb = window._convert_color(cb)
		self._list.append('3dbox', (cl, ct, cr, cb), coordinates)
		self._optimize(1)

	def drawdiamond(self, coordinates):
		if self._rendered:
			raise error, 'displaylist already rendered'
		coordinates = self._window._convert_coordinates(coordinates)
		self._list.append('diamond', coordinates)
		self._optimize()

	def drawfdiamond(self, color, coordinates):
		if self._rendered:
			raise error, 'displaylist already rendered'
		window = self._window
		x, y, w, h = coordinates
		if w < 0:
			x, w = x + w, -w
		if h < 0:
			y, h = y + h, -h
		coordinates = window._convert_coordinates((x, y, w, h))
		color = window._convert_color(color)
		self._list.append('fdiamond', color, coordinates)
		self._optimize(1)

	def draw3ddiamond(self, cl, ct, cr, cb, coordinates):
		if self._rendered:
			raise error, 'displaylist already rendered'
		window = self._window
		cl = window._convert_color(cl)
		ct = window._convert_color(ct)
		cr = window._convert_color(cr)
		cb = window._convert_color(cb)
		coordinates = window._convert_coordinates(coordinates)
		self._list.append('3ddiamond', (cl, ct, cr, cb), coordinates)
		self._optimize(1)

	def drawarrow(self, color, src, dst):
		if self._rendered:
			raise error, 'displaylist already rendered'
		window = self._window
		color = self._window._convert_color(color)
		try:
			nsx, nsy, ndx, ndy, points = window.arrowcache[(src,dst)]
		except KeyError:
			sx, sy = src
			dx, dy = dst
			nsx, nsy = window._convert_coordinates((sx, sy))
			ndx, ndy = window._convert_coordinates((dx, dy))
			if nsx == ndx and sx != dx:
				if sx < dx:
					nsx = nsx - 1
				else:
					nsx = nsx + 1
			if nsy == ndy and sy != dy:
				if sy < dy:
					nsy = nsy - 1
				else:
					nsy = nsy + 1
			lx = ndx - nsx
			ly = ndy - nsy
			if lx == ly == 0:
				angle = 0.0
			else:
				angle = math.atan2(ly, lx)
			rotation = math.pi + angle
			cos = math.cos(rotation)
			sin = math.sin(rotation)
			points = [(ndx, ndy)]
			points.append(int(round(ndx + ARR_LENGTH*cos + ARR_HALFWIDTH*sin)),
				      int(round(ndy + ARR_LENGTH*sin - ARR_HALFWIDTH*cos)))
			points.append(int(round(ndx + ARR_LENGTH*cos - ARR_HALFWIDTH*sin)),
				      int(round(ndy + ARR_LENGTH*sin + ARR_HALFWIDTH*cos)))
			window.arrowcache[(src,dst)] = nsx, nsy, ndx, ndy, points
		self._list.append('arrow', color, (nsx, nsy, ndx, ndy), points)
		self._optimize(1)

toplevel = _Toplevel()
from WIN32_windowbase import *

class FileDialog:
	def __init__(self, prompt, directory, filter, file, cb_ok, cb_cancel, existing = 0):
		import os

		self.cb_ok = cb_ok
		self.cb_cancel = cb_cancel

#		print 'PARAMETERS ARE:----------------'
#		print 'prompt-directory-filter-file'
#		print prompt, "  ",  directory, "  ", filter, " ", file

		self._form = None

		# formerly the class converted the given filter to a format understandable by the extension
		# module Htmlex (see the following lines)
		# currently we rely on the functions that call the class to provide the filter in a proper format
		# Example of proper format : file type 1 (*.1)|*.1|file type 2 (*.2)|*.2|...|filetype n (*.n)|*.n||

		#import string
		if not filter or filter=='*':
			filter = 'All files *.*|*.*||'
		else:
			filter = 'smil files (*.smi;*.smil)|*.smi;*.smil|cmif files (*.cmif)|*.cmif|All files *.*|*.*||'

		self.filter = filter
		if file == None or file == '':
			file = ' '
		if directory == None or directory == '' or directory=='.':
			directory = ' '
		if prompt == None or prompt == '':
			prompt=' '
## XXXX Note by Jack: I assume this code can be removed: file dialogs use local filename
## XXXX conventions...
##		import nturl2path
##		directory = nturl2path.url2pathname(directory)
##		file = nturl2path.url2pathname(file)
		if existing == OPEN_FILE:
			#id, flname, directory, fltr = cmifex2.CreateFileOpenDlg(prompt,file,directory,fltr)
#			print 'GIVEN TO F DIALOG: ', file, '---', filter
			#id, flname, fltr =  Htmlex.FDlg(prompt, file, filter)
			id, flname, fltr = cmifex2.CreateFileOpenDlg(prompt,file,filter)
			directory, name = os.path.split(flname)
#			print id, flname, directory, fltr
		#if type == SAVE_CMIF:
		else:
			id, flname, fltr = cmifex2.CreateFileSaveDlg(prompt,file,filter)
			l = len(flname)
			tmp = flname[(l-5):]
			import string, os
			tmp = string.lower(tmp)
			if (tmp != '.cmif'):
				flname = flname #+ '.cmif'

		if id==1:
			self._ok_callback(flname, directory, fltr)
		else:
			self._cancel_callback()

		del self

	def close(self):
		if self._form:
			toplevel._subwindows.remove(self)
			#self._form.UnmanageChild()
			#self._form.DestroyWidget()
			self._dialog = None
			self._form = None

	def setcursor(self, cursor):
		WIN32_windowbase._win_setcursor(self._form, cursor)

	def is_closed(self):
		return self._form is None

	def _cancel_callback(self):
#		print "Cancel button pressed!!!"
		self.close()


	def old_cancel_callback(self, *rest):
		if self.is_closed():
			return
		must_close = TRUE
		try:
			if self.cb_cancel:
				ret = self.cb_cancel()
				if ret:
					if type(ret) is StringType:
						showmessage(ret, mtype = 'error')
					must_close = FALSE
					return
		finally:
			if must_close:
				self.close()

	def _ok_callback(self, file, directory, pattern):
		import string
		file = string.lower(file)
		filename = file
		dir = directory
		filter = pattern

		if (self.cb_ok!=None):
			ret = self.cb_ok(filename)
			if ret:
#				print "ret-->", ret;
				if type(ret) is StringType:
					win32ui.MessageBox(ret, "Warning !", win32con.MB_OK)
				return


	def old_ok_callback(self, widget, client_data, call_data):
		if self.is_closed():
			return
		import os
		filename = call_data.value
		dir = call_data.dir
		filter = call_data.pattern
		filename = os.path.join(dir, filename)
		if not os.path.isfile(filename):
			if os.path.isdir(filename):
				filter = os.path.join(filename, filter)
				self._dialog.FileSelectionDoSearch(filter)
				return
		if self.cb_ok:
			ret = self.cb_ok(filename)
			if ret:
				if type(ret) is StringType:
					showmessage(ret, mtype = 'error')
				return
		self.close()

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
#		print attrs
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

	def setcursor(self, cursor):
		WIN32_windowbase._win_setcursor(self._form, cursor)

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
#		print params
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



class SelectionMenuDialog:
	def __init__(self, listprompt, selectionprompt, itemlist, default, parent=None):
		attrs = {'textString': default}
		if hasattr(self, 'NomatchCallback'):
			attrs['mustMatch'] = TRUE
		if listprompt:
			attrs['listLabelString'] = listprompt
		if selectionprompt:
			attrs['selectionLabelString'] = selectionprompt
#		print attrs

		self._menuselection = None

		self._menuid = None;

		self._menus = {}

		if default:
			itemlist.append(default)

		menu, menuid = cmifex2.GetMenu(parent)

		if menu == 0:
			menu = cmifex2.CreateMenu()

		self._menus[menuid] = itemlist

		submenu = cmifex2.CreateMenu()

		for item in itemlist:
			cmifex2.AppendMenu(submenu, item, -1)

		if not listprompt:
			listprompt = "Selection"

		cmifex2.PopupAppendMenu(menu, submenu, listprompt)
		cmifex2.SetMenu(parent,menu)
		parent.HookMessage(self._menu2_callback, win32con.WM_INITMENUPOPUP)
		parent.HookMessage(self._menu_callback, win32con.WM_COMMAND)

	def _nomatch_callback(self, widget, client_data, call_data):
		if self.is_closed():
			return
		ret = self.NomatchCallback(call_data.value)
		if ret and type(ret) is StringType:
			showmessage(ret, mtype = 'error')


	def _menu_callback(self, params):
		item = params[2]-1
		if self._menus.has_key(self._menuselection):
			l = self._menus[self._menuselection]
			str = l[item]
			try:
				func = self.OkCallback
			except AttributeError:
				pass
			else:
				ret = func(str)
				if ret:
					if type(ret) is StringType:
						win32ui.MessageBox(ret, "Error !", win32con.MB_OK)
					return



	def _menu2_callback(self, params):
		self._menuselection = params[3]



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
#		print "Cancel pressed"
		if self.is_closed():
			return
		self.close()


	def old_cancel(self, w, client_data, call_data):
		if self.is_closed():
			return
		self.close()

	def setcursor(self, cursor):
		WIN32_windowbase._win_setcursor(self._form, cursor)

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

[TOP, CENTER, BOTTOM] = range(3)
[VERTICAL, HORIZONTAL] = range(2)

class _MenuSupport:
	'''Support methods for a pop up menu.'''
	def __init__(self):
		self._menu = None

	def close(self):
		'''Close the menu.'''
		self.destroy_menu()

	def create_menu(self, list, title = None):
		'''Create a popup menu.

		TITLE is the title of the menu.  If None or '', the
		menu will not have a title.  LIST is a list with menu
		entries.  Each entry is either None to get a
		separator, a string to get a label, or a tuple of two
		elements.  The first element is the label in the menu,
		the second argument is either a callback which is
		called when the menu entry is selected or a list which
		defines a cascading submenu.  A callback is either a
		callable object or a tuple consisting of a callable
		object and a tuple.  If the callback is just a
		callable object, it is called without arguments; if
		the callback is a tuple consisting of a callable
		object and a tuple, the object is called using apply
		with the tuple as argument.'''

		#if self._form.IsSubclass(Xm.Gadget):
		#	raise error, 'cannot create popup menus on gadgets'
		self.destroy_menu()
		#menu = self._form.CreatePopupMenu('dialogMenu',
		#		{'colormap': toplevel._default_colormap,
		#		 'visual': toplevel._default_visual,
		#		 'depth': toplevel._default_visual.depth})
		#if title:
		#	list = [title, None] + list
		#WIN32_windowbase._create_menu(menu, list, toplevel._default_visual,
		#			  toplevel._default_colormap)
		if title:
			list = [title, list]
		menu = cmifex2.CreateMenu()
		WIN32_windowbase._create_menu(menu, list)
		self._menu = menu
		#self._form.AddEventHandler(X.ButtonPressMask, FALSE,
		#			   self._post_menu, None)

	def destroy_menu(self):
		'''Destroy the pop up menu.

		This function is called automatically when a new menu
		is created using create_menu, or when the window
		object is closed.'''

		menu = self._menu
		self._menu = None
		#if menu:
			#self._form.RemoveEventHandler(X.ButtonPressMask, FALSE,
			#			      self._post_menu, None)
			#menu.DestroyWidget()

	# support methods, only used by derived classes
	def _post_menu(self, w, client_data, call_data):
		if not self._menu:
			return
		#if call_data.button == X.Button3:
		#	self._menu.MenuPosition(call_data)
		#	self._menu.ManageChild()

	def _destroy(self):
		self._menu = None

class _Widget(_MenuSupport):
	'''Support methods for all window objects.'''
	def __init__(self, parent, widget):
		self._parent = parent
		parent._children.append(self)
		self._showing = TRUE
		self._form = widget
		#widget.ManageChild()
		_MenuSupport.__init__(self)
		#self._form.AddCallback('destroyCallback', self._destroy, None)
		#if widget:
		#	widget.HookMessage(self._destroy, win32con.WM_DESTROY)

	def __repr__(self):
		return '<_Widget instance at %x>' % id(self)

	def close(self):
		'''Close the window object.'''
		try:
			form = self._form
		except AttributeError:
			pass
		else:
			#del self._form
			_MenuSupport.close(self)
			#cmifex2.DestroyWindow(form)
			#form.DestroyWindow()
			#form.DestroyWidget()
		if self._parent:
			#cmifex2.DestroyMenu(self._parent._hWnd)
			self._parent._children.remove(self)
		self._parent = None
		return

	def is_closed(self):
		'''Returns true if the window is already closed.'''
		return not hasattr(self, '_form')

	def _showme(self, w):
		self._parent._showme(w)

	def _hideme(self, w):
		self._parent._hideme(w)

	def show(self):
		'''Make the window visible.'''
		self._parent._showme(self)
		self._showing = TRUE

	def hide(self):
		'''Make the window invisible.'''
		self._parent._hideme(self)
		self._showing = FALSE

	def is_showing(self):
		'''Returns true if the window is visible.'''
		return self._showing

	# support methods, only used by derived classes
	def _attachments(self, attrs, options):
		'''Calculate the attachments for this window.'''
		for pos in ['left', 'top', 'right', 'bottom']:
			#attachment = pos + 'Attachment'
			#try:
			#	widget = options[pos]
			#except:
			#	pass
			#else:
			#	if type(widget) in (FloatType, IntType):
			#		attrs[attachment] = \
			#			Xmd.ATTACH_POSITION
			#		attrs[pos + 'Position'] = \
			#			int(widget * 100 + .5)
			#	elif widget:
			#		attrs[pos + 'Attachment'] = \
			#			  Xmd.ATTACH_WIDGET
			#		attrs[pos + 'Widget'] = widget._form
			#	else:
			#		attrs[pos + 'Attachment'] = \
			#			  Xmd.ATTACH_FORM
			if options.has_key(pos):
				attrs[pos] = options[pos]


	def _destroy(self, params):
		'''Destroy callback.'''
		#try:
		#	form = self._form
		#except AttributeError:
		#	return
		if hasattr(self, '_form'):
			form = self._form
			del self._form
			#cmifex2.DestroyWindow(form)
			if form:
				form.DestroyWindow()
			if self._parent:
				#if self._menu:
				#	 cmifex2.DestroyMenu(self._parent._hWnd)
				self._parent._children.remove(self)
			self._parent = None
			_MenuSupport._destroy(self)

class Label(_Widget):
	'''Label window object.'''
	def __init__(self, parent, text, justify = 'center', useGadget = _def_useGadget,
		     name = 'windowLabel', **options):
		'''Create a Label subwindow.

		PARENT is the parent window, TEXT is the text for the
		label.  OPTIONS is an optional dictionary with
		options.  The only options recognized are the
		attachment options.'''
#		print "Label control", parent, text, options
		attrs = {}
		self._attachments(attrs, options)
		#if useGadget:
		#	label = Xm.LabelGadget
		#else:
		#	label = Xm.Label
		#label = parent._form.CreateManagedWidget(name, label, attrs)
		left = attrs['left']
		top = attrs['top']
		width = attrs['right']
		height = attrs['bottom']

		label = cmifex2.CreateStatic(text,parent._hWnd,left,top,width,height,justify)
		#self._form = label
		#label.labelString = text
		self._text = text
		_Widget.__init__(self, parent, label)

	def __repr__(self):
		return '<Label instance at %x, text=%s>' % (id(self), self._text)

	def setlabel(self, text):
		'''Set the text of the label to TEXT.'''
		#self._form.labelString = text
		self._text = text
		cmifex2.SetCaption(self._form, text)

class Button(_Widget):
	'''Button window object.'''
	def __init__(self, parent, label, callback, useGadget = _def_useGadget,
		     name = 'windowButton', **options):
		'''Create a Button subwindow.

		PARENT is the parent window, LABEL is the label on the
		button, CALLBACK is the callback function that is
		called when the button is activated.  The callback is
		a tuple consiting of a callable object and an argument
		tuple.'''
		self._text = label
		attrs = {'labelString': label}
		self._attachments(attrs, options)
		#if useGadget:
		#	button = Xm.PushButtonGadget
		#else:
		#	button = Xm.PushButton
		#button = parent._form.CreateManagedWidget(name, button, attrs)
		self._cb = callback
		left = attrs['left']
		top = attrs['top']
		width = attrs['right']
		height = attrs['bottom']

		#button = cmifex2.CreateContainerbox(parent._hWnd,left,top,width,height)

		button = cmifex2.CreateButton(label,parent._hWnd,left,top,width,height,('b',' '))
		if callback:
			#button.AddCallback('activateCallback',
			#		   self._callback, callback)
			#button.HookMessage(self._callback, win32con.WM_LBUTTONDOWN)
			pass
		#button.HookMessage(self._callback, win32con.WM_COMMAND)
		button.HookMessage(self._callback, win32con.WM_LBUTTONUP)
		_Widget.__init__(self, parent, button)

	def __repr__(self):
		return '<Button instance at %x, text=%s>' % (id(self), self._text)

	def setlabel(self, text):
		#self._form.labelString = text
		self._text = text
		cmifex2.SetCaption(self._form, text)

	def setsensitive(self, sensitive):
		#self._form.sensitive = sensitive
		self._form.EnableWindow(sensitive)
		return

	def _callback(self, params):
		#global _in_create_box
		#if _in_create_box == None or self._parent==_in_create_box:
			#print "level 1"
			if self.is_closed():
				return
			#print "level 2"
			#val = win32api.HIWORD(params[2])

			#if val == win32con.BN_CLICKED:
			#	print "level 3"
			#	if self._cb:
			#		apply(self._cb[0], self._cb[1])
			if self._cb:
				apply(self._cb[0], self._cb[1])
			self._form.ReleaseCapture()



class OptionMenu(_Widget):
	'''Option menu window object.'''
	def __init__(self, parent, label, optionlist, startpos, cb,
		     useGadget = _def_useGadget, name = 'windowOptionMenu',
		     **options):
		'''Create an option menu window object.

		PARENT is the parent window, LABEL is a label for the
		option menu, OPTIONLIST is a list of options, STARTPOS
		gives the initial selected option, CB is the callback
		that is to be called when the option is changed,
		OPTIONS is an optional dictionary with options.
		If label is None, the label is not shown, otherwise it
		is shown to the left of the option menu.
		The optionlist is a list of strings.  Startpos is the
		index in the optionlist of the initially selected
		option.  The callback is either None, or a tuple of
		two elements.  If None, no callback is called when the
		option is changed, otherwise the the first element of
		the tuple is a callable object, and the second element
		is a tuple giving the arguments to the callable
		object.'''

		attrs = {}
		if 0 <= startpos < len(optionlist):
			pass
		else:
			raise error, 'startpos out of range'
		self._useGadget = useGadget
		#initbut = self._do_setoptions(parent, optionlist,
		#			      startpos)
		#attrs = {'menuHistory': initbut,
		#	 'subMenuId': self._omenu,
		#	 'colormap': toplevel._default_colormap,
		#	 'visual': toplevel._default_visual,
		#	 'depth': toplevel._default_visual.depth}
		self._attachments(attrs, options)
		#option = parent._form.CreateOptionMenu(name, attrs)

		left = attrs['left']
		top = attrs['top']
		width = attrs['right']
		height = attrs['bottom']

		option = cmifex2.CreateContainerbox(parent._hWnd,left,top,width,25)

		if label is None:
			#option.OptionLabelGadget().UnmanageChild()

			self._combo = cmifex2.CreateCombobox(" ",option,0,0,width,height,(0,'dr',1))
			self._text = '<None>'
		else:
			#option.labelString = label
			#print parent._hWnd
			cmifex2.CreateStatic(label,option,0,0,cmifex2.GetStringLength(parent._hWnd,label),25,'left')
			l1 = cmifex2.GetStringLength(parent._hWnd,label)
			self._combo = cmifex2.CreateCombobox(" ",option,cmifex2.GetStringLength(parent._hWnd,label),0,width-cmifex2.GetStringLength(parent._hWnd,label),height,(0,'dr',1))
			self._text = label
		initbut = self._do_setoptions(parent, optionlist,
					      startpos)
		self._callback = cb
		option.HookMessage(self._cb, win32con.WM_COMMAND)
		_Widget.__init__(self, parent, option)

	def __repr__(self):
		return '<OptionMenu instance at %x, label=%s>' % (id(self), self._text)

	def close(self):
		_Widget.close(self)
		self._callback = self._value = self._optionlist = \
				 self._buttons = None

	def getpos(self):
		'''Get the index of the currently selected option.'''
		return self._value

	def getvalue(self):
		'''Get the value of the currently selected option.'''
		return self._optionlist[self._value]

	def setpos(self, pos):
		'''Set the currently selected option to the index given by POS.'''
		if pos == self._value:
			return
		#self._form.menuHistory = self._buttons[pos]
		if pos in self._buttons:
			cmifex2.Set(self._combo,self._buttons.index(pos))
			self._value = pos

	def setsensitive(self, pos, sensitive):
		if sensitive==0:
			if pos in self._buttons:
				cmifex2.DeleteToPos(self._combo,self._buttons.index(pos))
				self._buttons.remove(pos)
		else:
			if not pos in self._buttons:
				if 0 <= pos < len(self._optionlist):
					self._buttons.append(pos)
					self._buttons.sort()
					p = self._buttons.index(pos)
					cmifex2.InsertToPos(self._combo,p,self._optionlist[pos])
		#if 0 <= pos < len(self._buttons):
		#	#self._buttons[pos].sensitive = sensitive
		#	pass
		#else:
		#	raise error, 'pos out of range'

	def setvalue(self, value):
		'''Set the currently selected option to VALUE.'''
		self.setpos(self._optionlist.index(value))

	def setoptions(self, optionlist, startpos):
		'''Set new options.

		OPTIONLIST and STARTPOS are as in the __init__ method.'''

		if optionlist != self._optionlist:
			#if self._useGadget:
			#	createfunc = self._omenu.CreatePushButtonGadget
			#else:
			#	createfunc = self._omenu.CreatePushButton
			# reuse old menu entries or create new ones
			cmifex2.Reset(self._combo)
			self._buttons = []
			for i in range(len(optionlist)):
				item = optionlist[i]
				#if i == len(self._buttons):
				#	button = createfunc(
				#		'windowOptionButton',
				#		{'labelString': item})
				#	button.AddCallback('activateCallback',
				#			   self._cb, i)
				#	button.ManageChild()
				#	self._buttons.append(button)
				#else:
				#	button = self._buttons[i]
				#	button.labelString = item
				self._buttons.append(i)
				cmifex2.Add(self._combo,item)
			# delete superfluous menu entries
			#n = len(optionlist)
			#while len(self._buttons) > n:
			#	self._buttons[n].DestroyWidget()
			#	del self._buttons[n]
			tmp = []
			for item in optionlist:
				tmp.append(item)
			#self._optionlist = optionlist
			self._optionlist = tmp
		# set the start position
		self.setpos(startpos)

	def _do_setoptions(self, form, optionlist, startpos):
		if 0 <= startpos < len(optionlist):
			pass
		else:
			raise error, 'startpos out of range'
		#menu = form.CreatePulldownMenu('windowOption',
		#		{'colormap': toplevel._default_colormap,
		#		 'visual': toplevel._default_visual,
		#		 'depth': toplevel._default_visual.depth})
		#self._omenu = menu
		tmp = []
		for item in optionlist:
			tmp.append(item)
		#self._optionlist = optionlist
		self._optionlist = tmp
		self._value = startpos
		self._buttons = []
		#if self._useGadget:
		#	createfunc = menu.CreatePushButtonGadget
		#else:
		#	createfunc = menu.CreatePushButton
		for i in range(len(optionlist)):
			item = optionlist[i]
		#	button = createfunc('windowOptionButton',
		#			    {'labelString': item})
		#	button.AddCallback('activateCallback', self._cb, i)
		#	button.ManageChild()
		#	if startpos == i:
		#		initbut = button
		#	self._buttons.append(button)
			self._buttons.append(i)
			cmifex2.Add(self._combo,item)
		#return initbut
		cmifex2.Set(self._combo,startpos)
		return startpos

	def _cb(self, params):
		if self.is_closed():
			return
		val = win32api.HIWORD(params[2])
		if val == win32con.LBN_SELCHANGE or val == win32con.CBN_SELCHANGE:
			#self._value = value
			self._value = self._buttons[cmifex2.GetPos(self._combo)]
			if self._callback:
				f, a = self._callback
				apply(f, a)
		else:
			return

	def _destroy(self, widget, value, call_data):
		_Widget._destroy(self, widget, value, call_data)
		#del self._omenu
		del self._optionlist
		del self._buttons
		del self._callback

class PulldownMenu(_Widget):
	'''Menu bar window object.'''
	def __init__(self, parent, menulist, useGadget = _def_useGadget,
		     name = 'menuBar', **options):
		'''Create a menu bar window object.

		PARENT is the parent window, MENULIST is a list giving
		the definition of the menubar, OPTIONS is an optional
		dictionary of options.
		The menulist is a list of tuples.  The first elements
		of the tuples is the name of the pulldown menu, the
		second element is a list with the definition of the
		pulldown menu.'''

		attrs = {}
		#self._attachments(attrs, options)
		#if useGadget:
		#	cascade = Xm.CascadeButtonGadget
		#else:
		#	cascade = Xm.CascadeButton
		#menubar = parent._form.CreateMenuBar(name, attrs)
		self._callback_dict = {}
		menuid = 0
		menubar = cmifex2.CreateMenu()
		buttons = []
		for item, list in menulist:
			#menu = menubar.CreatePulldownMenu('windowMenu',
			#	{'colormap': toplevel._default_colormap,
			#	 'visual': toplevel._default_visual,
			#	 'depth': toplevel._default_visual.depth})
			#button = menubar.CreateManagedWidget(
			#	'windowMenuButton', cascade,
			#	{'labelString': item,
			#	 'subMenuId': menu})
			#WIN32_windowbase._create_menu(menu, list,
			#			  toplevel._default_visual,
			#			  toplevel._default_colormap)
			menu = cmifex2.CreateMenu()
			temp = WIN32_windowbase._create_menu(menu, list, menuid,self._callback_dict)
			if temp:
				menuid = temp[0]
				dict2 = temp[1]
				dkeys = dict2.keys()
				for k in dkeys:
					if not self._callback_dict.has_key(k):
						self._callback_dict[k] = dict2[k]
			cmifex2.PopupAppendMenu(menubar, menu, item)
			#buttons.append(button)
		_Widget.__init__(self, parent, None)
		self._buttons = buttons
		self._menu = menubar
		#cmifex2.SetMenu(parent._hWnd,menubar)
		parent._hWnd.HookMessage(self._menu_callback, win32con.WM_COMMAND)


	def __repr__(self):
		return '<PulldownMenu instance at %x>' % id(self)

	def _menu_callback(self, params):
		if params[3] != 0:
			return
#		print "menu-->", params
		item = params[2]
		if self._callback_dict.has_key(item):
			try:
				f, a = self._callback_dict[item]
			except AttributeError:
				pass
			else:
				apply(f, a)


	def close(self):
		_Widget.close(self)
		self._buttons = None

	def setmenu(self, pos, list):
		if not 0 <= pos < len(self._buttons):
			raise error, 'position out of range'
		button = self._buttons[pos]
		#menu = self._form.CreatePulldownMenu('windowMenu',
		#		{'colormap': toplevel._default_colormap,
		#		 'visual': toplevel._default_visual,
		#		 'depth': toplevel._default_visual.depth})
		#WIN32_windowbase._create_menu(menu, list,
		#			  toplevel._default_visual,
		#			  toplevel._default_colormap)
		#omenu = button.subMenuId
		#button.subMenuId = menu
		#omenu.DestroyWidget()

	def _destroy(self, widget, value, call_data):
		_Widget._destroy(self, widget, value, call_data)
		del self._buttons

# super class for Selection and List
class _List:
	def __init__(self, list, itemlist, initial, sel_cb):
		self._list = list
		#list.ListAddItems(itemlist, 1)
		for item in itemlist:
			cmifex2.Add(list,item)
		self._itemlist = itemlist
		self._cb = None
		if type(sel_cb) is ListType:
			if len(sel_cb) >= 1 and sel_cb[0]:
				#list.AddCallback('singleSelectionCallback',
				#		 self._callback, sel_cb[0])
				self._cb = sel_cb[0]
			if len(sel_cb) >= 2 and sel_cb[1]:
				#list.AddCallback('defaultActionCallback',
				#		 self._callback, sel_cb[1])
				self._cb = sel_cb[1]
		elif sel_cb:
			#list.AddCallback('singleSelectionCallback',
			#		 self._callback, sel_cb)
			self._cb = sel_cb

		if itemlist:
			self.selectitem(initial)



	def close(self):
		self._itemlist = None
		self._list = None

	def getselected(self):
		#pos = self._list.ListGetSelectedPos()
		pos = cmifex2.GetPos(self._list)
		if pos>=0:
			#return pos[0] - 1
			return pos #- 1
		else:
			return None

	def getlistitem(self, pos):
		return self._itemlist[pos]

	def getlist(self):
		return self._itemlist

	def addlistitem(self, item, pos):
		if pos < 0:
			pos = len(self._itemlist)
		#self._list.ListAddItem(item, pos + 1)
		self._itemlist.insert(pos, item)
		cmifex2.InsertToPos(self._list,pos,item)

	def addlistitems(self, items, pos):
		if pos < 0:
			pos = len(self._itemlist)
		#self._list.ListAddItems(items, pos + 1)
		for item in items:
			cmifex2.InsertToPos(self._list,pos,item)
			pos = pos +1
		self._itemlist[pos:pos] = items

	def dellistitem(self, pos):
		del self._itemlist[pos]
		#self._list.ListDeletePos(pos + 1)
		cmifex2.DeleteToPos(self._list,pos)


	def dellistitems(self, poslist):
		#self._list.ListDeletePositions(map(lambda x: x+1, poslist))
		list = poslist[:]
		list.sort()
		list.reverse()
		for pos in list:
			del self._itemlist[pos]
			cmifex2.DeleteToPos(self._list,pos)

	def replacelistitem(self, pos, newitem):
		self.replacelistitems(pos, [newitem])

	def replacelistitems(self, pos, newitems):
		self._itemlist[pos:pos+len(newitems)] = newitems
		#self._list.ListReplaceItemsPos(newitems, pos + 1)
		for item in newitems:
			cmifex2.ReplaceToPos(self._list,pos,item)
			pos = pos +1

	def delalllistitems(self):
		self._itemlist = []
		#self._list.ListDeleteAllItems()
		cmifex2.Reset(self._list)

	def selectitem(self, pos):
		if pos is None:
			#self._list.ListDeselectAllItems()
			cmifex2.Set(self._list,-1)
			self._list.SendMessage(win32con.WM_LBUTTONDBLCLK,0,0)
			return
		if pos < 0:
			pos = len(self._itemlist) - 1
		#self._list.ListSelectPos(pos + 1, TRUE)
		cmifex2.Set(self._list,pos)
		self._list.SendMessage(win32con.WM_LBUTTONDBLCLK,0,0)

	def is_visible(self, pos):
#		print "pos -->>>", pos
	#	if pos < 0:
	#		pos = len(self._itemlist) - 1
	#	top = self._list.topItemPosition - 1
	#	vis = self._list.visibleItemCount
	#	return top <= pos < top + vis
		return 1

	def scrolllist(self, pos, where):
		#if pos < 0:
		#	pos = len(self._itemlist) - 1
		#if where == TOP:
		#	self._list.ListSetPos(pos + 1)
		#elif where == BOTTOM:
		#	self._list.ListSetBottomPos(pos + 1)
		#elif where == CENTER:
		#	vis = self._list.visibleItemCount
		#	toppos = pos - vis / 2 + 1
		#	if toppos + vis > len(self._itemlist):
		#		toppos = len(self._itemlist) - vis + 1
		#	if toppos <= 0:
		#		toppos = 1
		#	self._list.ListSetPos(toppos)
		#else:
		#	raise error, 'bad argument for scrolllist'
		pass


	def _callback(self, params):
		if self.is_closed():
			return
		if self._cb:
			f, a = self._cb
			apply(f, a)
		else:
			return



	def _destroy(self):
		del self._itemlist
		del self._list

class Selection(_Widget, _List):
	def __init__(self, parent, listprompt, itemprompt, itemlist, initial, sel_cb,
		     name = 'windowSelection', **options):
		attrs = {}
		self._attachments(attrs, options)
		#selection = parent._form.CreateSelectionBox(name, attrs)
		#for widget in Xmd.DIALOG_APPLY_BUTTON, \
		#    Xmd.DIALOG_CANCEL_BUTTON, Xmd.DIALOG_DEFAULT_BUTTON, \
		#   Xmd.DIALOG_HELP_BUTTON, Xmd.DIALOG_OK_BUTTON, \
		#    Xmd.DIALOG_SEPARATOR:
		#	selection.SelectionBoxGetChild(widget).UnmanageChild()
		#w = selection.SelectionBoxGetChild(Xmd.DIALOG_LIST_LABEL)

		left = attrs['left']
		top = attrs['top']
		width = attrs['right']
		height = attrs['bottom']

		self._list = None
		self._listlabel = None
		self._editlabel = None
		self._edit = None
		self._sel_cb = None
		selection = cmifex2.CreateContainerbox(parent._hWnd,left,top,width,height)
		if listprompt is None:
			#w.UnmanageChild()
			top = 0
			self._text = '<None>'
		else:
			#w.labelString = listprompt
			self._listlabel = cmifex2.CreateStatic(listprompt,selection,0,0,width,25,'left')
			top = 25
			height = height - 25
			self._text = listprompt
		#w = selection.SelectionBoxGetChild(Xmd.DIALOG_SELECTION_LABEL)

		if itemprompt is None:
			#w.UnmanageChild()
			list = cmifex2.CreateListbox(" ",selection,0,top,width,height-25,0)
			top = top + height - 25
#			print "No item label"
		else:
			#w.labelString = itemprompt
			list = cmifex2.CreateListbox(" ",selection,0,top,width,height-50,0)
			top = top + height - 50
			self._editlabel = cmifex2.CreateStatic(itemprompt,selection,0,top,width,25,'left')
			top = top + 25
		#list = selection.SelectionBoxGetChild(Xmd.DIALOG_LIST)
		#list.selectionPolicy = Xmd.SINGLE_SELECT
		#list.listSizePolicy = Xmd.CONSTANT
		self._edit = cmifex2.CreateEdit(" ",selection,0,top,width,25,TRUE)
		try:
			cb = options['enterCallback']
		except KeyError:
			pass
		else:
			#txt = selection.SelectionBoxGetChild(Xmd.DIALOG_TEXT)
			#txt.AddCallback('activateCallback', self._callback, cb)
			self._sel_cb = cb
			self._edit.HookMessage(self.sel_callback, win32con.WM_KEYUP)
		_List.__init__(self, list, itemlist, initial, sel_cb)
		_Widget.__init__(self, parent, selection)
		str = cmifex2.Get(self._list)
		if str!='':
			cmifex2.SetCaption(self._edit,str)
		#self._list.HookMessage(self._callback, win32con.WM_LBUTTONDBLCLK)
		#self._list.HookMessage(self._callback, win32con.WM_KEYUP)
		self._list.HookMessage(self._callback, win32con.WM_LBUTTONUP)



	def __repr__(self):
		return '<Selection instance at %x; label=%s>' % (id(self), self._text)


	def _callback(self, params):
		if self.is_closed():
			return
		val = params[1]
		if val == win32con.WM_LBUTTONDBLCLK or (val == win32con.WM_KEYUP and params[2] == 13):
			#print "selection _callback"
			str = cmifex2.Get(self._list)
			#print str
			if str!='':
				cmifex2.SetCaption(self._edit,str)
			else:
				cmifex2.SetCaption(self._edit,'')
				return
			_List._callback(self,params)
		elif val == win32con.WM_LBUTTONUP:
				val = win32api.LOWORD(params[2])

				str = cmifex2.Get(self._list)
				#print str
				_List._callback(self,params)
				if str:
					cmifex2.SetCaption(self._edit,str)
				else:
					return
				self._list.ReleaseCapture()
				return



	def sel_callback(self, params):
		if self.is_closed():
			return
		val = params[1]
		if val == win32con.WM_KEYUP and params[2] == 13:
			if self._sel_cb:
				f, a = self._sel_cb
				apply(f, a)
			else:
				return
		else:
			return


	def close(self):
		_List.close(self)
		_Widget.close(self)

	def setlabel(self, label):
		#w = self._form.SelectionBoxGetChild(Xmd.DIALOG_LIST_LABEL)
		#w.labelString = label
		if self._listlabel:
			cmifex2.SetCaption(self._listlabel, label)
			self._text = label

	def getselection(self):
		#text = self._form.SelectionBoxGetChild(Xmd.DIALOG_TEXT)
		#if hasattr(text, 'TextFieldGetString'):
		#	return text.TextFieldGetString()
		#else:
		#	return text.TextGetString()
		text = cmifex2.GetText(self._edit)
		print "--------->", text
		return text

	def _destroy(self, widget, value, call_data):
		_Widget._destroy(self, widget, value, call_data)
		_List._destroy(self)

	def seteditable(self, editable):
		#text = self._form.SelectionBoxGetChild(Xmd.DIALOG_TEXT)
		#text.editable = editable
		self._edit.EnableWindow(editable)


class List(_Widget, _List):
	def __init__(self, parent, listprompt, itemlist, sel_cb,
		     rows = 10, useGadget = _def_useGadget,
		     name = 'windowList', **options):
		#attrs = {'resizePolicy': parent.resizePolicy}
		attrs = {}
		self._attachments(attrs, options)

		left = attrs['left']
		top = attrs['top']
		width = attrs['right']
		height = attrs['bottom']

		self._list = None
		self._listlabel = None
		form = cmifex2.CreateContainerbox(parent._hWnd,left,top,width,height)

		if listprompt is not None:
		#	if useGadget:
		#		labelwidget = Xm.LabelGadget
		#	else:
		#		labelwidget = Xm.Label
		#	form = parent._form.CreateManagedWidget(
		#		'windowListForm', Xm.Form, attrs)
		#	label = form.CreateManagedWidget(name + 'Label',
		#			labelwidget,
		#			{'topAttachment': Xmd.ATTACH_FORM,
		#			 'leftAttachment': Xmd.ATTACH_FORM,
		#			 'rightAttachment': Xmd.ATTACH_FORM})
		#	self._label = label
		#	label.labelString = listprompt
		#	attrs = {'topAttachment': Xmd.ATTACH_WIDGET,
		#		 'topWidget': label,
		#		 'leftAttachment': Xmd.ATTACH_FORM,
		#		 'rightAttachment': Xmd.ATTACH_FORM,
		#		 'bottomAttachment': Xmd.ATTACH_FORM,
		#		 'visibleItemCount': rows,
		#		 'selectionPolicy': Xmd.SINGLE_SELECT}
		#	try:
		#		attrs['width'] = options['width']
		#	except KeyError:
		#		pass
		#	if parent.resizePolicy == Xmd.RESIZE_ANY:
		#		attrs['listSizePolicy'] = \
		#					Xmd.RESIZE_IF_POSSIBLE
		#	else:
		#		attrs['listSizePolicy'] = Xmd.CONSTANT
		#	list = form.CreateScrolledList(name, attrs)
		#	list.ManageChild()
			self._listlabel = cmifex2.CreateStatic(listprompt,form,0,0,width,25,'center')
			list = cmifex2.CreateListbox(" ",form,0,25,width,height-25,0)
		#	widget = form
			self._text = listprompt
		else:
			attrs['visibleItemCount'] = rows
		#	attrs['selectionPolicy'] = Xmd.SINGLE_SELECT
		#	if parent.resizePolicy == Xmd.RESIZE_ANY:
		#		attrs['listSizePolicy'] = \
		#					Xmd.RESIZE_IF_POSSIBLE
		#	else:
		#		attrs['listSizePolicy'] = Xmd.CONSTANT
		#	try:
		#		attrs['width'] = options['width']
		#	except KeyError:
		#		pass
		#	list = parent._form.CreateScrolledList(name, attrs)
		#	widget = list
			list = cmifex2.CreateListbox(" ",form,0,0,width,height,0)
			self._text = '<None>'
		widget = form
		_List.__init__(self, list, itemlist, None, sel_cb)
		_Widget.__init__(self, parent, widget)
		#self._list.HookMessage(self._callback, win32con.WM_LBUTTONDBLCLK)
		#self._list.HookMessage(self._callback, win32con.WM_KEYUP)
		self._list.HookMessage(self._callback, win32con.WM_LBUTTONUP)



	def __repr__(self):
		return '<List instance at %x; label=%s>' % (id(self), self._text)


	def _callback(self, params):
		self._list.ReleaseCapture()
		if self.is_closed():
			return
		val = params[1]
		if val == win32con.WM_LBUTTONUP or (val == win32con.WM_KEYUP and params[2] == 13):
			str = cmifex2.Get(self._list)
			if not str:
				return
			_List._callback(self,params)
		else:
			return



	def close(self):
		_List.close(self)
		_Widget.close(self)

	def setlabel(self, label):
		#try:
		#	self._label.labelString = label
		#except AttributeError:
		#	raise error, 'List created without label'
		#else:
		#	self._text = label
		if self._listlabel:
			cmifex2.SetCaption(self._listlabel,label)
			self._text = label
		else:
			return

	def _destroy(self, widget, value, call_data):
		#try:
		#	del self._label
		#except AttributeError:
		#	pass
		_Widget._destroy(self, widget, value, call_data)
		_List._destroy(self)

class TextInput(_Widget):
	def __init__(self, parent, prompt, inittext, chcb, accb,
		     useGadget = _def_useGadget, name = 'windowTextfield',
		     **options):
		attrs = {}
		self._attachments(attrs, options)
		#if prompt is not None:
		#	if useGadget:
		#		labelwidget = Xm.LabelGadget
		#	else:
		#		labelwidget = Xm.Label
		#	form = parent._form.CreateManagedWidget(
		#		name + 'Form', Xm.Form, attrs)
		#	label = form.CreateManagedWidget(
		#		name + 'Label', labelwidget,
		#		{'topAttachment': Xmd.ATTACH_FORM,
		#		 'leftAttachment': Xmd.ATTACH_FORM,
		#		 'bottomAttachment': Xmd.ATTACH_FORM})
		#	self._label = label
		#	label.labelString = prompt
		#	attrs = {'topAttachment': Xmd.ATTACH_FORM,
		#		 'leftAttachment': Xmd.ATTACH_WIDGET,
		#		 'leftWidget': label,
		#		 'bottomAttachment': Xmd.ATTACH_FORM,
		#		 'rightAttachment': Xmd.ATTACH_FORM}
		#	widget = form
		#else:
		#	form = parent._form
		#	widget = None
		#try:
		#	attrs['columns'] = options['columns']
		#except KeyError:
		#	pass
		#attrs['value'] = inittext
		try:
			attrs['editable'] = options['editable']
		except KeyError:
			pass
		#text = form.CreateTextField(name, attrs)
		#text.ManageChild()
		#if not widget:
		#	widget = text
		if attrs.has_key('editable'):
			editable = attrs['editable']
		else:
			editable = TRUE

		left = attrs['left']
		top = attrs['top']
		width = attrs['right']
		height = attrs['bottom']

		text = cmifex2.CreateContainerbox(parent._hWnd,left,top,width,height)

		if prompt is None:
			if (inittext==None or inittext==''):
				inittext= ' '
			self._edit = cmifex2.CreateEdit(inittext,text,0,0,width,height,editable)
			self._label = None
		else:
#			print cmifex2.GetStringLength(text, prompt)
			self._label = cmifex2.CreateStatic(prompt,text,0,0,cmifex2.GetStringLength(text, prompt),25,'left')
			self._edit = cmifex2.CreateEdit(inittext,text,cmifex2.GetStringLength(text, prompt),0,width-cmifex2.GetStringLength(text, prompt),height,editable)

		widget = text

		if chcb:
			#text.AddCallback('valueChangedCallback',
			#		 self._callback, chcb)
			self._ch_cb = chcb
		else:
			self._ch_cb = None
		if accb:
			#text.AddCallback('activateCallback',
			#		 self._callback, accb)
			self._ac_cb = accb
		else:
			self._ac_cb = None

		self._text = text
		_Widget.__init__(self, parent, widget)
		#print '-----------------------------', self._edit
		#print '-----------------------------', self._callback
		#self._edit.HookMessage(self._callback, win32con.WM_SETFOCUS)
		self._edit.HookMessage(self._callback, win32con.WM_KILLFOCUS)


	def __repr__(self):
		return '<TextInput instance at %x>' % id(self)

	def close(self):
		_Widget.close(self)
		self._text = None

	def setlabel(self, label):
		if not hasattr(self, '_label'):
			raise error, 'TextInput create without label'
		#self._label.labelString = label
		cmifex2.SetCaption(self._label,label)

	def gettext(self):
		#return self._text.TextFieldGetString()
		if self._form:
			return cmifex2.GetText(self._edit)
		else:
			return ''

	def settext(self, text):
		#self._text.value = text
		if self._form:
			cmifex2.SetCaption(self._edit,text)

	def _callback(self, params):
		if self.is_closed():
			return
		if params[1] == win32con.WM_KILLFOCUS:
			if self._ch_cb:
				func, arg = self._ch_cb
			else:
				return
		else:
			res = cmifex2.Changed(self._form)
			if res !=0:
				if self._ac_cb:
					func, arg = self._ac_cb
				else:
					return
			else:
				return
		apply(func, arg)

	def seteditable(self, editable):
		self._form.EnableWindow(editable)

	def _destroy(self, widget, value, call_data):
		_Widget._destroy(self, widget, value, call_data)
		try:
			del self._label
		except AttributeError:
			pass
		del self._text

class TextEdit(_Widget):
	def __init__(self, parent, inittext, cb, name = 'windowText',
		     **options):
		#attrs = {'editMode': Xmd.MULTI_LINE_EDIT,
		attrs = {'editable': TRUE,
				 'rows': 10}
		for option in ['editable', 'rows', 'columns']:
			try:
				attrs[option] = options[option]
			except KeyError:
				pass
		if not attrs['editable']:
			attrs['cursorPositionVisible'] = FALSE
		self._attachments(attrs, options)
		#text = parent._form.CreateScrolledText(name, attrs)

		editable = attrs['editable']

		left = attrs['left']
		top = attrs['top']
		width = attrs['right']
		height = attrs['bottom']
#		print  parent._hWnd,left,top,width,height,editable
		str1 = 'klh'
		text = cmifex2.CreateMultiEdit(str1,parent._hWnd,left,top,width,height,editable)
		self._cb = None

		if cb:
			#text.AddCallback('activateCallback', self._callback,
			#		 cb)
			self._cb = cb
		_Widget.__init__(self, parent, text)
		self.settext(inittext)
		text.HookMessage(self._callback, win32con.WM_SETFOCUS)


	def __repr__(self):
		return '<TextEdit instance at %x>' % id(self)


	def settext(self, text):
		if type(text) is ListType:
			text = string.join(text, '\n')
		# convert to Windows end-of-line conventions
		text = string.join(string.split(text, '\n'), '\r\n')
		cmifex2.SetCaption(self._form,text)
		self._linecache = None

	def gettext(self):
		if self._form:
			text = cmifex2.GetText(self._form)
			# convert from Windows end-of-line conventions
			return string.join(string.split(text, '\r\n'), '\n')
		else:
			return ''


	def getlines(self):
		text = self.gettext()
		text = string.splitfields(text, '\n')
		if len(text) > 0 and text[-1] == '':
			del text[-1]
		return text

	def _mklinecache(self):
		text = self.getlines()
		self._linecache = c = []
		pos = 0
		for line in text:
			c.append(pos)
			pos = pos + len(line) + 1

	def getline(self, line):
		lines = self.getlines()
		if line < 0 or line >= len(lines):
			line = len(lines) - 1
		return lines[line]

	def scrolltext(self, line, where):
		if not self._linecache:
			self._mklinecache()
		if line < 0 or line >= len(self._linecache):
			line = len(self._linecache) - 1
		if where == TOP:
			pass
		else:
			rows = self._form.rows
			if where == BOTTOM:
				line = line - rows + 1
			elif where == CENTER:
				line = line - rows/2 + 1
			else:
				raise error, 'bad argument for scrolltext'
			if line < 0:
				line = 0
		#self._form.TextSetTopCharacter(self._linecache[line])

	def selectchars(self, line, start, end):
		if not self._linecache:
			self._mklinecache()
		if line < 0 or line >= len(self._linecache):
			line = len(self._linecache) - 1
		pos = self._linecache[line]
		#self._form.TextSetSelection(pos + start, pos + end, 0)
		cmifex2.Select(self._form, pos + start, pos + end)

	def _callback(self, params):
		if self.is_closed():
			return
		if self._cb:
			func, arg = self._cb
			apply(func, arg)
		res = cmifex2.Changed(self._form)

	def seteditable(self, editable):
		self._form.EnableWindow(editable)

	def _destroy(self, widget, value, call_data):
		_Widget._destroy(self, widget, value, call_data)
		del self._linecache

class Separator(_Widget):
	def __init__(self, parent, useGadget = _def_useGadget,
		     name = 'windowSeparator', **options):
		attrs = {}
		self._attachments(attrs, options)
		#if useGadget:
		#	separator = Xm.SeparatorGadget
		#else:
		#	separator = Xm.Separator
		#separator = parent._form.CreateManagedWidget(name, separator,
		#					     attrs)
		left = attrs['left']
		top = attrs['top']
		width = attrs['right']
		height = attrs['bottom']

		separator = cmifex2.CreateSeparator(parent._hWnd,left,top,width,height,0)
		_Widget.__init__(self, parent, separator)

	def __repr__(self):
		return '<Separator instance at %x>' % id(self)

class ButtonRow(_Widget):
	def __init__(self, parent, buttonlist,
		     vertical = 1, callback = None,
		     buttontype = 'pushbutton', useGadget = _def_useGadget,
		     name = 'windowRowcolumn', **options):
		#attrs = {'entryAlignment': Xmd.ALIGNMENT_CENTER,
		#	 'traversalOn': FALSE}
		#if not vertical:
		#	attrs['orientation'] = Xmd.HORIZONTAL
##		#	attrs['packing'] = Xmd.PACK_COLUMN
		self._cb = callback
		#if useGadget:
		#	separator = Xm.SeparatorGadget
		#	cascadebutton = Xm.CascadeButtonGadget
		#	pushbutton = Xm.PushButtonGadget
		#	togglebutton = Xm.ToggleButtonGadget
		#else:
		#	separator = Xm.Separator
		#	cascadebutton = Xm.CascadeButton
		#	pushbutton = Xm.PushButton
		#	togglebutton = Xm.ToggleButton
		attrs = {}
		self._attachments(attrs, options)
		#rowcolumn = parent._form.CreateManagedWidget(name, Xm.RowColumn, attrs)

		left = attrs['left']
		top = attrs['top']
		width = attrs['right']
		height = attrs['bottom']

		rowcolumn = cmifex2.CreateContainerbox(parent._hWnd,left,top,width,height)

		if vertical:
			#max = 0
			#length = 0
			#for entry in buttonlist:
			#	if type(entry) is TupleType:
			#		label = entry[0]
			#	else:
			#		label = entry
			#	length = cmifex2.GetStringLength(rowcolumn,label)
			#	if length>max:
			#		max = length
			#width = max+5
			width = width - 10

		left = top = 0
		self._buttons = []
		self._callbks = {}
		for entry in buttonlist:
			if entry is None:
				#if vertical:
				#	attrs = {'orientation': Xmd.HORIZONTAL}
				#else:
				#	attrs = {'orientation': Xmd.VERTICAL}
				#dummy = rowcolumn.CreateManagedWidget(
				#	'buttonSeparator', separator, attrs)
				if vertical:
					cmifex2.CreateSeparator(rowcolumn,left+5,top+5,width,height,0)
					top = top + 10
				else:
					cmifex2.CreateSeparator(rowcolumn,left+5,top+5,width,height,1)
					left = left + 10
				continue
			btype = buttontype
			if type(entry) is TupleType:
				label, callback = entry[:2]
				if len(entry) > 2:
					btype = entry[2]
			else:
				label, callback = entry, None
			if type(callback) is ListType:
			#	menu = rowcolumn.CreateMenuBar('submenu', {})
			#	submenu = menu.CreatePulldownMenu(
			#		'submenu',
			#		{'colormap': toplevel._default_colormap,
			#		'visual': toplevel._default_visual,
			#		 'depth': toplevel._default_visual.depth})
			#	button = menu.CreateManagedWidget(
			#		'submenuLabel', cascadebutton,
			#		{'labelString': label,
			#		 'subMenuId': submenu})
			#	WIN32_windowbase._create_menu(submenu, callback,
			#		  toplevel._default_visual,
			#		  toplevel._default_colormap)
			#	menu.ManageChild()
				continue
			if callback and type(callback) is not TupleType:
				callback = (callback, (label,))
			if btype[0] in ('b', 'p'): # push button
				#gadget = pushbutton
				battrs = {}
				callbackname = 'activateCallback'
			elif btype[0] == 't': # toggle button
				#gadget = togglebutton
				#battrs = {'indicatorType': Xmd.N_OF_MANY}
				callbackname = 'valueChangedCallback'
			elif btype[0] == 'r': # radio button
				#gadget = togglebutton
				#battrs = {'indicatorType': Xmd.ONE_OF_MANY}
				callbackname = 'valueChangedCallback'
			else:
				raise error, 'bad button type'
			#battrs['labelString'] = label
			#button = rowcolumn.CreateManagedWidget('windowButton',
			#		gadget, battrs)
			if not vertical:
				if label:
					width = cmifex2.GetStringLength(rowcolumn,label)+10
				else:
					width = 10

			button = cmifex2.CreateButton(label,rowcolumn,left+5,top+5,width,20,(btype[0],'right'))
			if callback or self._cb:
			#	button.AddCallback(callbackname,
			#			   self._callback, callback)
			#	button.HookMessage(self._callback, win32con.WM_LBUTTONDOWN)
				pass

			#self._buttons.append(button.GetSafeHwnd())
			self._buttons.append(button)
			if callback:
				self._callbks[button.GetSafeHwnd()] = (callback,btype[0])
			else:
				self._callbks[button.GetSafeHwnd()] = (None,None)

			if vertical:
				top = top + 25
			else:
				left = left + width+5

		rowcolumn.HookMessage(self._callback, win32con.WM_COMMAND)
		_Widget.__init__(self, parent, rowcolumn)


	def __repr__(self):
		return '<ButtonRow instance at %x>' % id(self)

	def close(self):
		_Widget.close(self)
		self._buttons = None
		self._cb = None

	def hide(self, button = None):
		if button is None:
			_Widget.hide(self)
			return
		if not 0 <= button < len(self._buttons):
			raise error, 'button number out of range'
		#self._buttons[button].UnmanageChild()
		self._buttons[button].ShowWindow(win32con.SW_HIDE)


	def show(self, button = None):
		if button is None:
			_Widget.show(self)
			return
		if not 0 <= button < len(self._buttons):
			raise error, 'button number out of range'
		#self._buttons[button].ManageChild()
		self._buttons[button].ShowWindow(win32con.SW_SHOW)

	def getbutton(self, button):
		if not 0 <= button < len(self._buttons):
			raise error, 'button number out of range'
		#return self._buttons[button].set
		return self._buttons[button]

	def setbutton(self, button, onoff = 1):
		if not 0 <= button < len(self._buttons):
			raise error, 'button number out of range'
		button = self._buttons[button]
		#button.set = onoff
		cmifex2.CheckButton(button,onoff)

	def setsensitive(self, button, sensitive):
		if not 0 <= button < len(self._buttons):
			raise error, 'button number out of range'
		#self._buttons[button].sensitive = sensitive
		self._buttons[button].EnableWindow(sensitive)

	def _callback(self, params):
		#global _in_create_box
		#if _in_create_box == None or self._parent==_in_create_box:
			if self.is_closed():
				return

			val = win32api.HIWORD(params[2])
			if val == win32con.BN_CLICKED:
				if self._cb:
					apply(self._cb[0], self._cb[1])

				val = params[3]
				callback, type = self._callbks[val]
				if type == 'r':
					for bt in self._buttons:
						cb, tp = self._callbks[bt.GetSafeHwnd()]
						if tp == 'r' and bt.GetSafeHwnd() != val:
							self.setbutton(self._buttons.index(bt),0)
						elif bt.GetSafeHwnd() == val:
							self.setbutton(self._buttons.index(bt),1)

				if callback:
					apply(callback[0], callback[1])

	def _popup(self, widget, submenu, call_data):
		submenu.ManageChild()

	def _destroy(self, widget, value, call_data):
		_Widget._destroy(self, widget, value, call_data)
		del self._buttons
		del self._cb

class Slider(_Widget):
	def __init__(self, parent, prompt, minimum, initial, maximum, cb,
		     vertical = 0, showvalue = 1, name = 'windowScale',
		     **options):
		#if vertical:
		#	orientation = Xmd.VERTICAL
		#else:
		#	orientation = Xmd.HORIZONTAL
		#self._orientation = orientation
		orientation = self._orientation = vertical
		range = maximum - minimum
		if range < 0:
			range = -range
			minimum, maximum = maximum, minimum
		self._factor = range/100
		direction, min, init, max, decimal, factor = \
			   self._calcrange(minimum, initial, maximum)
		attrs = {'minimum': min,
			 'maximum': max,
			 'processingDirection': direction,
			 'decimalPoints': decimal,
			 'orientation': orientation,
			 'showValue': showvalue,
			 'value': init}
		self._attachments(attrs, options)

		if not vertical:
			vertical = 0

		left = attrs['left']
		top = attrs['top']
		width = attrs['right']
		height = attrs['bottom']
		self._slider = None
		self._sliderlabel = None

		#scale = parent._form.CreateScale(name, attrs)
		scale = cmifex2.CreateContainerbox(parent._hWnd,left,top,width,height)


		if prompt is None:
			#for w in scale.GetChildren():
			#	if w.Name() == 'Title':
			#		w.UnmanageChild()
			#		break
			self._slider = cmifex2.CreateSlider(" ",scale,0,0,width-50,height,vertical)
			self._edit = cmifex2.CreateEdit(" ",scale,width-45,0,40,25,0)
		else:
			#scale.titleString = prompt
			self._sliderlabel = cmifex2.CreateStatic(prompt,scale,0,0,width,25,'left')
			self._slider = cmifex2.CreateSlider(prompt,scale,0,25,width-50,height-25,vertical)
			self._edit = cmifex2.CreateEdit(" ",scale,width-45,25,40,25,0)

		self._cb = None

		if cb:
			#scale.AddCallback('valueChangedCallback',
			#		  self._callback, cb)
			self._cb = cb
		self._slider.HookMessage(self._callback, win32con.WM_LBUTTONUP)

		self.setrange(minimum, maximum)
		self.setvalue(initial)

		_Widget.__init__(self, parent, scale)


	def __repr__(self):
		return '<Slider instance at %x>' % id(self)

	def getvalue(self):
		#return self._form.ScaleGetValue() / self._factor
		return cmifex2.GetPosition(self._slider) * self._factor

	def setvalue(self, value):
		value = int(value / self._factor + .5)
		#self._form.ScaleSetValue(value)
		cmifex2.SetPosition(self._slider, value)
		if self._factor<1:
			value2 = value * self._factor
			cmifex2.SetCaption(self._edit, `value2`)
		else:
			cmifex2.SetCaption(self._edit, `value`)

	def setrange(self, minimum, maximum):
		direction, minimum, initial, maximum, decimal, factor = \
			   self._calcrange(minimum, self.getvalue(), maximum)
		#self._form.SetValues({'minimum': minimum,
		#		      'maximum': maximum,
		#		      'processingDirection': direction,
		#		      'decimalPoints': decimal,
		#		      'value': initial})
		cmifex2.SetRange(self._slider,minimum,maximum)

	def getrange(self):
		return self._minimum, self._maximum
		#return cmifex2.GetRange(self._slider)*int(self._factor)

	def _callback(self, params):
		self.setvalue(self.getvalue())
		if self.is_closed():
			return
		if self._cb:
			apply(self._cb[0], self._cb[1])
		self._slider.ReleaseCapture()

	def _calcrange(self, minimum, initial, maximum):
		self._minimum, self._maximum = minimum, maximum
		range = maximum - minimum
		direction = 1
		if range < 0:
			#f self._orientation == Xmd.VERTICAL:
			#	direction = Xmd.MAX_ON_BOTTOM
			#else:
			#	direction = Xmd.MAX_ON_LEFT
			range = -range
			minimum, maximum = maximum, minimum
		#else:
		#	if self._orientation == Xmd.VERTICAL:
		#		direction = Xmd.MAX_ON_TOP
		#	else:
		#		direction = Xmd.MAX_ON_RIGHT
		decimal = 0
		factor = 1.0
		if FloatType in [type(minimum), type(maximum)]:
			factor = 1.0
		#while 0 < range <= 10:
		#	range = range * 10
		#	decimal = decimal + 1
		#	factor = factor * 10
		factor = range/100
		self._factor = factor
		return direction, int(minimum / factor + .5), \
		       int(initial / factor + .5), \
		       int(maximum / factor + .5), decimal, factor

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
		return apply(SubWindow, (self,), options)
	def AlternateSubWindow(self, **options):
		return apply(AlternateSubWindow, (self,), options)

class SubWindow(_Widget, _WindowHelpers):
	def __init__(self, parent, name = 'windowSubwindow', **options):
		#attrs = {'resizePolicy': parent.resizePolicy}
		#self.resizePolicy = parent.resizePolicy
		attrs = {}
		self._attachments(attrs, options)

		left = attrs['left']
		top = attrs['top']
		width = attrs['right']
		height = attrs['bottom']

		#form = parent._form.CreateManagedWidget(name, Xm.Form, attrs)

		form = cmifex2.CreateContainerbox(parent._hWnd,left,top,width,height)

		if not hasattr(self, '_hWnd'):
			self._hWnd = form

		_WindowHelpers.__init__(self)
		_Widget.__init__(self, parent, form)
		parent._fixkids.append(self)
		self._window_type = SINGLE
		self._align = ''

	def __repr__(self):
		return '<SubWindow instance at %x>' % id(self)

	def close(self):
		_Widget.close(self)
		_WindowHelpers.close(self)

	def fix(self):
		for w in self._fixkids:
			w.fix()
		#self._form.ManageChild()
		self._fixed = TRUE

	def show(self):
		_Widget.show(self)
		if self._fixed:
			#for w in self._fixkids:
			#	if w.is_showing():
			#		w.show()
			#	else:
			#		w.hide()
			self._fixkids = []

class _AltSubWindow(SubWindow):
	def __init__(self, parent, name, **options):
		self._parent = parent
		#SubWindow.__init__(self, parent, left = None, right = None,
		#		   top = None, bottom = None, name = name)
		attrib = {}
		self._attachments(attrib, options)

		lft = attrib['left']
		tp = attrib['top']
		wth = attrib['right']
		hght = attrib['bottom']
		SubWindow.__init__(self, parent, name = name, left = lft, top = tp, right = wth, bottom = hght)
		self._window_type = SINGLE

	def show(self):
		for w in self._parent._windows:
			w.hide()
		SubWindow.show(self)

class AlternateSubWindow(_Widget):
	def __init__(self, parent, name = 'windowAlternateSubwindow',
		     **options):
		#attrs = {'resizePolicy': parent.resizePolicy,
		#	 'allowOverlap': TRUE}
		#self.resizePolicy = parent.resizePolicy

		attrs = {'allowOverlap': TRUE}
		self._attachments(attrs, options)

		left = attrs['left']
		top = attrs['top']
		width = attrs['right']
		height = attrs['bottom']

		#form = parent._form.CreateManagedWidget(name, Xm.Form, attrs)

		form = cmifex2.CreateContainerbox(parent._hWnd,left,top,width,height)

		if not hasattr(self, '_hWnd'):
			self._hWnd = form

		self._windows = []
		_Widget.__init__(self, parent, form)
		parent._fixkids.append(self)
		self._fixkids = []
		self._children = []
		self._window_type = SINGLE
		self._align = ''

	def __repr__(self):
		return '<AlternateSubWindow instance at %x>' % id(self)

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
		#for w in self._windows:
		#	w._form.ManageChild()

class Window(_WindowHelpers, _MenuSupport):
	def __init__(self, title, resizable = 0, grab = 0,
		     Name = 'windowShell', Class = None, havpar=1, **options):
		#if not resizable:
		#	self.resizePolicy = Xmd.RESIZE_NONE
		#else:
		#	self.resizePolicy = Xmd.RESIZE_ANY
		attrs = {}
		if not title:
			title = ''
		self._title = title
		#wattrs = {'title': title,
		#	  'minWidth': 60, 'minHeight': 60,
		#	  'colormap': toplevel._default_colormap,
		#	  'visual': toplevel._default_visual,
		#	  'depth': toplevel._default_visual.depth}
		wattrs = {'title': title,
			  'minWidth': 60, 'minHeight': 60}
		#attrs = {'allowOverlap': FALSE,
		#	 'resizePolicy': self.resizePolicy}
		#if not resizable:
		#	attrs['noResize'] = TRUE
		#	attrs['resizable'] = FALSE
		if grab:
			#global _in_create_box
			#_in_create_box = self
			#attrs['dialogStyle'] = \
			#		     Xmd.DIALOG_FULL_APPLICATION_MODAL
			for key, val in wattrs.items():
				attrs[key] = val
			#self._form = toplevel._main.CreateFormDialog(
			#	'grabDialog', attrs)

			try:
				self.deleteCallback = options['deleteCallback']
			except KeyError:
				pass
		else:
			wattrs['iconName'] = title
			#self._shell = toplevel._main.CreatePopupShell(Name,
			#	Xt.ApplicationShell, wattrs)
			#self._form = self._shell.CreateManagedWidget(
			#	'windowForm', Xm.Form, attrs)
			try:
				self.deleteCallback = options['deleteCallback']
			except KeyError:
				pass
			#else:
			#	self._shell.AddWMProtocolCallback(
			#		toplevel._delete_window,
			#		self._delete_callback,
			#		deleteCallback)
			#	self._shell.deleteResponse = Xmd.DO_NOTHING
		self._showing = FALSE
		self._not_shown = []
		self._shown = []
		_WindowHelpers.__init__(self)
		_MenuSupport.__init__(self)

		par = None
		self._par_hWnd = None
##XXXX ARGH!
## 		if havpar==1:
## 			found = 0
## 			par = win32ui.GetActiveWindow()
## 			import TopLevel
## 			for top in TopLevel.opentops:
## 				if hasattr(top, 'views'):
## 					for vi in top.views:
## 						if hasattr(vi,'window'):
## 							if hasattr(vi.window,'_hWnd'):
## 								if vi.window._hWnd==par:
## 									found = 1
## 									self._par_hWnd = top.window._hWnd
## 									break
## 					if found:
## 						break

## 					for i in top.views[0].channels.keys():
## 						if hasattr(top.views[0].channels[i],'window'):
## 							if hasattr(top.views[0].channels[i].window,'_hWnd'):
## 								if top.views[0].channels[i].window._hWnd==par:
## 									found = 1
## 									self._par_hWnd = top.window._hWnd
## 									break

## 					if found:
## 						break

## 			if not found and grab:
## 				self._par_hWnd = par
## 			elif not found:
## 				for wind in toplevel._subwindows:
## 					if hasattr(wind, '_hWnd'):
## 						if  wind._hWnd == par:
## 							if hasattr(wind, '_par_hWnd'):
## 								self._par_hWnd = wind._par_hWnd
## 							else:
## 								self._par_hWnd = par
## 							break


		#import whrandom
		#xpoint = whrandom.randint(2,toplevel._screenwidth-200)
		#ypoint = whrandom.randint(2,toplevel._screenheight-300)
		#self._hWnd = cmifex2.CreateDialogbox(" ", par, xpoint, ypoint, 400, 400, 0)
		self._hWnd = cmifex2.CreateDialogbox(" ", self._par_hWnd, 0, 0, 400, 400, 0, grab)
		cmifex2.SetCaption(self._hWnd,self._title)
		toplevel._subwindows.append(self)
		self._window_type = SINGLE
		self._align = ''
		self._hWnd.HookMessage(self._closeclb, win32con.WM_CLOSE)
		if grab:
			self._hWnd.HookMessage(self._focusclb, win32con.WM_KILLFOCUS)

	def _focusclb(self, params):
		if params[2] == 0:
			res = 0
		else:
			res = self._hWnd.IsChild(params[2])
		if res != 1:
			self._hWnd.SetFocus()

	def _closeclb(self, params):
			self._hWnd.HookMessage(None, win32con.WM_KILLFOCUS)
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
			form = self._hWnd
		except AttributeError:
			return
		try:
			shell = self._shell
		except AttributeError:
			shell = None
		toplevel._subwindows.remove(self)
	#	del self._form
	#	del self._hWnd
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
		del self._hWnd

	def is_closed(self):
		#return not hasattr(self, '_form')
		return not self._showing

	def setcursor(self, cursor):
		#WIN32_windowbase._win_setcursor(self._form, cursor)
		WIN32_windowbase._win_setcursor(self._hWnd, cursor)

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
		#try:
		#	self._shell.Popup(0)
		#except AttributeError:
		#	pass
		self._showing = TRUE
		for w in self._not_shown:
		#	if not w.is_closed() and \
		#	   not w._form.IsSubclass(Xm.Gadget):
		#		w._form.UnmapWidget()
			if not w.is_closed():
				w._form.ShowWindow(win32con.SW_HIDE)
		for w in self._shown:
		#	if not w.is_closed() and \
		#	   not w._form.IsSubclass(Xm.Gadget):
		#		w._form.MapWidget()
			w._form.ShowWindow(win32con.SW_SHOW)
		self._not_shown = []
		self._shown = []
		self._hWnd.ShowWindow(win32con.SW_SHOW)
		#for w in self._fixkids:
		#	if w.is_showing():
		#		w.show()
		#	else:
		#		w.hide()
		self._fixkids = []

	def hide(self):
		#try:
		#	self._shell.Popdown()
		#except AttributeError:
		#	pass
		self._showing = FALSE
		if self._hWnd:
			self._hWnd.ShowWindow(win32con.SW_HIDE)

	def is_showing(self):
		return self._showing

	def settitle(self, title):
		if self._title != title:
			#try:
			#	self._shell.title = title
			#	self._shell.iconName = title
			#except AttributeError:
			#	self._form.dialogTitle = title
			self._title = title
			self._hWnd.SetWindowText(title)
			#cmifex2.SetCaption(self._hWnd, title)

	def getgeometry(self):
		if self.is_closed():
			raise error, 'window already closed'
#		x, y  = self._form.TranslateCoords(0, 0)
#		val = self._form.GetValues(['width', 'height'])
#		w = val['width']
#		h = val['height']
		x, y, w1, h1 = self._hWnd.GetWindowPlacement()[4]
		x1, y1, w, h = self._hWnd.GetClientRect()
		return x / toplevel._hmm2pxl, y / toplevel._vmm2pxl, \
		       w / toplevel._hmm2pxl, h / toplevel._vmm2pxl
#		return self._sizes

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

def Dialog(list, title = '', prompt = None, grab = 1, vertical = 1, canclose=TRUE):
	w = Window(title, grab = grab, havpar=0)
	options = {'top': None, 'left': None, 'right': None, 'bottom':None}

	constant = 3*win32api.GetSystemMetrics(win32con.SM_CXBORDER)+win32api.GetSystemMetrics(win32con.SM_CYCAPTION)+ 20
	constant2 = 2*win32api.GetSystemMetrics(win32con.SM_CYBORDER)+10
	_w = constant2
	_h = constant
	vbw = 0
	vbh = 0
	hbw = 0
	lbh = 25
	max = 0

	ls = list

	if vertical == 1:
		length = 0
		for item in ls:
			if item:
				label = item[0]
				if label:
					length = cmifex2.GetStringLength(w._hWnd,label)
				if length>vbw:
					vbw = length
		vbw = vbw + 30
		max = vbw
		_h = _h + len(ls)*20 + (len(ls)-1)*5
	else:
		length = 0
		for item in ls:
			if item:
				label = item[0]
				if label:
					length = cmifex2.GetStringLength(w._hWnd,label)
					hbw = hbw + length + 15
			else:
				hbw = hbw + 15
		max = hbw
		_h = _h + 30

	if prompt:
		ls = string.splitfields(prompt ,'\n')
		maxline = 0;
		for line in ls:
			if (line==None or line==''):
				line=' '
			length = cmifex2.GetStringLength(w._hWnd,line)
			if length>maxline:
				maxline = length
		lbh = (len(ls)+1)*15
		_h = _h + lbh
		if max<maxline + 10:
			max = maxline + 10

	_w = _w + max

#	if prompt:
#		l = apply(w.Label, (prompt,), options)
#		options['top'] = l

	options['left'] = 0
	options['top'] = 0
	options['right'] = max
	options['bottom'] = lbh

	if prompt:
		l = apply(w.Label, (prompt,), options)


	options['left'] = 0
	options['top'] = lbh
	options['right'] = max
	options['bottom'] = _h - lbh - constant

	options['vertical'] = vertical
	if grab:
		if canclose:
			options['callback'] = (lambda w: w.close(), (w,))
	b = apply(w.ButtonRow, (list,), options)
	w.buttons = b
	cmifex2.ResizeWindow(w._hWnd, _w, _h)
	w.show()
	return w

_end_loop = '_end_loop'			# exception for ending a loop

class _Question:
	def __init__(self, text):
		self.looping = FALSE
		self.answer = None
		showmessage(text, mtype = 'question',
			    callback = (self.callback, (TRUE,)),
			    cancelCallback = (self.callback, (FALSE,)))

	def run(self):
		try:
			self.looping = TRUE
			Xt.MainLoop()
		except _end_loop:
			pass
		return self.answer

	def callback(self, answer):
		self.answer = answer
		if self.looping:
			raise _end_loop

#def showquestion(text):
#	return _Question(text).run()

def showquestion(text):
	return _Question(text).answer

class _MultChoice:
	def __init__(self, prompt, msg_list, defindex):
		self.looping = FALSE
		self.answer = 0
		self.selection_made = 0
		self.msg_list = msg_list
		list = []
		_cb = None
		for msg in msg_list:
			if msg != 'Cancel':
				list.append(msg, (self.callback, (msg,)), 'r')
			else:
				_cb = (self.callback, ('Cancel',))
		self.dialog = Dialog(list, title = None, prompt = prompt,
				     grab = TRUE, vertical = TRUE, canclose = FALSE)
		showmessage("Select an item and press 'OK'.\nThe first item is the default",
					mtype = 'information', cancelCallback = _cb, grab=0)
		#if not self.selection_made:
		self.dialog.close()

	def run(self):
		try:
			self.looping = TRUE
#			Xt.MainLoop()
		except _end_loop:
			pass
#		return self.answer
		return 2

	def callback(self, msg):
		for i in range(len(self.msg_list)):
			if msg == self.msg_list[i]:
				self.answer = i
				if msg != 'Cancel':
					self.selection_made = 1
				#if self.looping:
				#	raise _end_loop
				return

#def multchoice(prompt, list, defindex):
#	return _MultChoice(prompt, list, defindex).run()

def multchoice(prompt, list, defindex):
	return _MultChoice(prompt, list, defindex).answer

def textwindow(text):
	w = Window('Source', resizable = 1, deleteCallback = 'hide', havpar = 0)
	t = w.TextEdit(self.root.source, None, editable = 0, top = 35, left = 0, right = 80*7, bottom = 300, rows = 30, columns = 80)
	b = w.ButtonRow([('Close', (w.hide, ()))], top = 5, left = 5, right = 150, bottom = 30, vertical = 0)
	cmifex2.ResizeWindow(w._hWnd, 80*7+20, 380)
	w.show()
	return w

fonts = WIN32_windowbase.fonts

WIN32_windowbase.toplevel = toplevel

newwindow = toplevel.newwindow

newcmwindow = toplevel.newcmwindow

close = toplevel.close

addclosecallback = toplevel.addclosecallback

setcursor = toplevel.setcursor

getsize = toplevel.getsize

usewindowlock = toplevel.usewindowlock

settimer = toplevel.settimer

select_setcallback = toplevel.select_setcallback

mainloop = toplevel.mainloop

getscreensize = toplevel.getscreensize

getscreendepth = toplevel.getscreendepth

canceltimer = toplevel.canceltimer

lopristarting = WIN32_windowbase.lopristarting
