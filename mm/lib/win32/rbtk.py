__version__ = "$Id$"

# rbtk: rb toolkit

# This module contains the interface functions 
# between a window and the draw toolkit


_rb_message = """\
Use left mouse button to draw a box.
Click `OK' when ready or `Cancel' to cancel."""
_rb_done = '_rb_done' # exception to stop create_box loop

import components
import DrawTk
from win32mu import Point,Rect
import win32ui,win32con,win32api
import appcon
import __main__
from appcon import UNIT_MM, UNIT_SCREEN, UNIT_PXL

class _rbtk:
	def __init__(self):
		self._next_create_box = []

	# Called by the core system to create or resize a box
	def create_box(self, msg, callback, box = None, units = appcon.UNIT_SCREEN):
		#print "Creating box in:",self._title
		#print 'active_displist=',self._active_displist

		# if we are in create box mode, queue request
		if self.in_create_box_mode():
			self.get_box_modal_wnd()._next_create_box.append((self, msg, callback, box, units))
			return

		# if we are closed call cancel
		if self.is_closed():
			apply(callback, ())
			return

		if box:
			# convert box to relative sizes if necessary
			box = self._inverse_coordinates(self._convert_coordinates(box, units = units))

		# set application in create box mode
		self.getgrinsframe().showChilds(0)
		self.set_create_box_mode(self)
		self.pop() # bring to top
	

		# set rel coord reference
		DrawTk.drawTk.SetRelCoordRef(self)
		
		# hold current display list and create new 
		# to be used during drawing
		self._rb_dl = self._active_displist
		if self._rb_dl:
			d = self._rb_dl.clone()
		else:	
			d = self.newdisplaylist()

		# indicate drawing canvas
		#canvas_color=(228,255,228)
		#d.drawfbox(canvas_color,(0,0,1,1))
		d.drawbox((0.01,0.01,0.99,0.99))

		# frame subwindows (fill them?)
		sw = self._subwindows[:]
		sw.reverse()
		for win in sw:
			b=win.getsizes()
			#d.drawfbox(win._bgcolor,b)
			d.drawbox(b)
		self._topwindow.ShowWindows(win32con.SW_HIDE)

		#d.fgcolor((255, 0, 0))
		if box:
			# add the rect obj
			box_pxl=self.get_pixel_coords(box)
			l,t,w,h=box_pxl
			rectObj=DrawTk.DrawRect(Rect((l,t,l+w,t+h)))
			self.Add(rectObj)
			
			# select tool 'select' and select obj
			DrawTk.drawTk.SelectTool('select')

			# simulate a user selection of the obj 
			drawTool = DrawTk.drawTk.GetCurrentTool()
			point=Point((l+w/2,t+h/2))
			drawTool.onLButtonDown(self,0,point)
			drawTool.onLButtonUp(self,0,point)
		else:
			DrawTk.drawTk.SelectTool('rect')
			DrawTk.drawTk.LimitRects(1)

		d.render()
		self._rb_curdisp = d

		f=self._topwindow._parent
		components.CreateBoxBar(f,msg,
			callback = (self.EndModalLoop, (win32con.IDOK,)),
			cancelCallback = (self.EndModalLoop, (win32con.IDCANCEL,)))	
	
		# clip cursor
		#win32api.ClipCursor(self.GetWindowRect())
		
		# loop here dispatching messages until user
		# selects OK or CANCEL
		userResponse=self.RunModalLoop(0)


		# cleanup steps before callback
		
		# 1. restore mode
		self.set_create_box_mode(None)
		self.getgrinsframe().showChilds(1)

		# 2. restore wnds state
		self._topwindow.ShowWindows(win32con.SW_SHOW)

		# 3. restore display list
		if self._rb_dl and not self._rb_dl.is_closed():
			self._rb_dl.render()
		
		# 4. close draw display list
		self._rb_curdisp.close()

		# 5. get user object
		if len(self._objects):
			drawObj=self._objects[0]
			rb=self.get_relative_coords100(drawObj._position.tuple_ps(), units = units)	
		self.DeleteContents()
				
		# call user selected callback
		if userResponse==win32con.IDOK:
			apply(callback, rb)
		else:
			apply(callback,())	

		# execute pending create_box calls
		next_create_box = self._next_create_box
		self._next_create_box = []
		for win, msg, cb, box, units in next_create_box:
			win.create_box(msg, cb, box, units)

	# Notify the toolkit about mouse and paint messages
	def notifyListener(self,key,params):
		if not self.in_create_box_mode(): return 0
		if key=='onLButtonDown':DrawTk.DrawLayer.onLButtonDown(self,params)
		elif key=='onLButtonUp':DrawTk.DrawLayer.onLButtonUp(self,params)
		elif key=='onMouseMove':DrawTk.DrawLayer.onMouseMove(self,params)
		elif key=='OnDraw':DrawTk.DrawLayer.DrawObjLayer(self,params)
		return 1

	# returns true if we are in create box mode 
	def in_create_box_mode(self):
		return __main__.toplevel._in_create_box

	# Set/remove create box mode
	def set_create_box_mode(self,f):
		if f:
			__main__.toplevel._in_create_box=self
			self.setScrollMode(1) ## DO NOT RESIZE DURING rbMode
		else:
			__main__.toplevel._in_create_box=None
			self.setScrollMode(0) ## RESIZE ALLOWED

	# returns the modal window while in create box mode
	def get_box_modal_wnd(self):
		return __main__.toplevel._in_create_box

	# Hide/Show all windows except self.
	def ShowWindows(self,f):
		if self.get_box_modal_wnd()!=self and self._topwindow!=self:
			self.ShowWindow(f)
		for w in self._subwindows:
			w.ShowWindows(f)
