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
import __main__
from appcon import UNIT_MM, UNIT_SCREEN, UNIT_PXL
import appcon

class _rbtk:
	def __init__(self):
		pass

	# Called by the core system to create or resize a box
	def create_box(self, msg, callback, box = None, units = UNIT_SCREEN, modeless=0, coolmode=0):
		self.assert_not_in_create_box()

		# for modal boxes cancel is async, so:
		if __main__.toplevel._in_create_box and not __main__.toplevel._in_create_box.is_closed():
			__main__.toplevel._in_create_box.cancel_create_box()
##		if self.in_create_box_mode():
##			apply(callback, ())
##			return
					
		# if we are closed call cancel
		if self.is_closed():
			apply(callback, ())
			return


		self._rb_modeless=modeless
		self._rb_callback=callback
		self._rb_units=units
		self._rb_box=box
		self._coolmode=coolmode

		if box:
			# convert box to relative sizes if necessary
			box = self._inverse_coordinates(self._convert_coordinates(box, units = units))

		# set application in create box mode
		if not modeless:
			self.getgrinsframe().showChilds(0)
			self.pop() # bring to top
		self.set_create_box_mode(self)
	

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
		#d.drawbox((0.001,0.001,0.999,0.999))

		# frame subwindows
		sw = self._subwindows[:]
		sw.reverse()
		for win in sw:
			b=win.getsizes()
			if b != (0, 0, 1, 1):
				d.drawbox(b)
		self._topwindow.ShowWindows(win32con.SW_HIDE)

		if box:
			# add the rect obj
			box_pxl=self.get_pixel_coords(box)
			l,t,w,h=box_pxl
			rectObj=DrawTk.DrawRect(Rect((l,t,l+w,t+h)),units=units)
			self.Add(rectObj)
			
			# select tool 'select' and select obj
			DrawTk.drawTk.SelectTool('select')

			# simulate a user selection of the obj 
			drawTool = DrawTk.drawTk.GetCurrentTool()
			point=Point((l+w/2,t+h/2))
			if not self._coolmode:
				drawTool.onLButtonDown(self,0,point)
				drawTool.onLButtonUp(self,0,point)
		else:
			DrawTk.drawTk.SelectTool('rect', units = units)
			DrawTk.drawTk.LimitRects(1)

		d.render()
		self._rb_curdisp = d

		if not modeless:
			# display dlg (bar) with OK and CANCEL
			f=self._topwindow._parent
			components.CreateBoxBar(f,msg,
				callback = (self.EndModalLoop, (win32con.IDOK,)),
				cancelCallback = (self.EndModalLoop, (win32con.IDCANCEL,)))	
			# loop here dispatching messages until the user or the system
			# directly or indirectly calls self.EndModalLoop with OK or CANCEL arg.
			# The mechanism is actually a simple and clean callback mechanism
			userResponse=self.RunModalLoop(0)
			self._rb_finish(userResponse)
		

	def _rb_finish(self,userResponse):
		# 1. restore mode
		self.set_create_box_mode(None)
		if not self._rb_modeless:
			self.getgrinsframe().showChilds(1)

		# 2. restore wnds state
			self._topwindow.ShowWindows(win32con.SW_SHOW)

		# 3. restore display list
		if self._rb_dl and not self._rb_dl.is_closed():
			self._rb_dl.render()
		
		# 4. close draw display list
		self._rb_curdisp.close()

		# 5. get user object
		if self._objects:
			drawObj=self._objects[0]
			rb=self.get_relative_coords100(drawObj._position.tuple_ps(), units = self._rb_units)
		else:
			rb=()
		self.DeleteContents()
				
		# callback with the box or () according to self.EndModalLoop argument
		if userResponse==win32con.IDOK:
			apply(self._rb_callback, rb)
		else:
## Comment by Jack: I don't fully understand what Kleanthis intended here,
## but a cancel is a cancel and we always call the callback with empty argument.
## Hope this doesn't break anything else.
## 			# for modeless boxes do here what we should
## 			# have done on every change.
## 			if self._rb_modeless and self._rb_dirty(rb):
## 				apply(self._rb_callback, rb)
## 			else:	
## 				apply(self._rb_callback,())
			if not self._coolmode:
				apply(self._rb_callback, ())
			else:
 				if self._rb_modeless and self._rb_dirty(rb):
 					apply(self._rb_callback, rb)
 				else:	
 					apply(self._rb_callback,())
			

	def cancel_create_box(self):
		"""Cancel create_box"""
		if not self.in_create_box_mode():
			raise 'Not in_create_box mode', self
		mw=self.get_box_modal_wnd()
		if self._rb_modeless:
			mw._rb_finish(win32con.IDCANCEL)
		else:
			mw.PostMessage(appcon.WM_USER_CREATE_BOX_CANCEL)	
			
		
	def return_create_box(self):
		"""Return create_box"""
		if not self.in_create_box_mode():
			raise 'Not _in_create_box', self
		mw=self.get_box_modal_wnd()
		if self._rb_modeless:
			mw._rb_finish(win32con.IDOK)
		else:
			mw.PostMessage(appcon.WM_USER_CREATE_BOX_OK)

	def _rb_dirty(self,box):
		if not self._rb_box and box: return 1
		for i in range(4):
			if self._rb_box[i]!=box[i]:
				return 1
		return 0
					
	def assert_not_in_create_box(self):
		if self.in_create_box_mode():
			self.get_box_modal_wnd().cancel_create_box()

	def onCreateBoxOK(self,params):
		self.EndModalLoop(win32con.IDOK)

	def onCreateBoxCancel(self,params):
		self.EndModalLoop(win32con.IDCANCEL)

	# Notify the toolkit about mouse and paint messages
	def notifyListener(self,key,params):
		if not self.in_create_box_mode(): return 0
		if key=='onLButtonDown':DrawTk.DrawLayer.onLButtonDown(self,params)
		elif key=='onMouseMove':DrawTk.DrawLayer.onMouseMove(self,params)
		elif key=='OnDraw':DrawTk.DrawLayer.DrawObjLayer(self,params)
		elif key=='onLButtonUp':
			DrawTk.DrawLayer.onLButtonUp(self,params)
			if self._rb_modeless:
				# If this is a modeless resize check whether something changed.
				if self._objects:
					drawObj=self._objects[0]
					rb=self.get_relative_coords100(drawObj._position.tuple_ps(), units = self._rb_units)
					if self._rb_dirty(rb) and not self._coolmode:
						self._rb_finish(win32con.IDOK)
		return 1

	# returns true if we are in create box mode 
	def in_create_box_mode(self):
		return __main__.toplevel._in_create_box is self

	def in_modal_create_box_mode(self):
		mw=__main__.toplevel._in_create_box
		if not mw: return 0
		return (not mw._rb_modeless) 

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
