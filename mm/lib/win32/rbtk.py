# rbtk: rb toolkit


_rb_message = """\
Use left mouse button to draw a box.
Click `OK' when ready or `Cancel' to cancel."""
_rb_done = '_rb_done' # exception to stop create_box loop

import components
import DrawTk
from win32mu import Point,Rect
import win32ui,win32con
import __main__


class _rbtk:
	def __init__(self):
		self._next_create_box = []

	def create_box(self, msg, callback, box = None):

		# if we are in create box mode, queue request
		if self.in_create_box_mode():
			self.get_box_modal_wnd()._next_create_box.append((self, msg, callback, box))
			return

		# if we are closed call cancel
		if self.is_closed():
			apply(callback, ())
			return

		# set application in create box mode
		self.set_create_box_mode(self)
		self.pop()
	
		# set rel coord reference
		DrawTk.drawTk.SetRelCoordRef(self)
		
		# hold current display list and create new 
		# to be used during drawing
		self._rb_callback = callback		
		self._rb_dl = self._active_displist
		if self._rb_dl:
			d = self._rb_dl.clone()
		else:	
			d = self.newdisplaylist()

		# indicate drawing canvas
		canvas_color=(228,255,228)
		d.drawfbox(canvas_color,(0,0,1,1))

		# frame subwindows (fill them?)
		sw = self._subwindows[:]
		sw.reverse()
		for win in sw:
			b=win.getsizes()
			#d.drawfbox(win._bgcolor,b)
			d.drawbox(b)
			win.ShowWindow(win32con.SW_HIDE)

		d.fgcolor((255, 0, 0))
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
		
		# loop here dispatching messages until user
		# selects OK or CANCEL
		userResponse=self.RunModalLoop(0)


		# cleanup steps before callback
		
		# 1. restore mode
		self.set_create_box_mode(None)
		
		# 2. restore wnds state
		for w in self._subwindows:
			w.ShowWindow(win32con.SW_SHOW)

		# 3. restore display list
		if self._rb_dl and not self._rb_dl.is_closed():
			self._rb_dl.render()
		
		# 4. close draw display list
		self._rb_curdisp.close()

		# 5. get user object
		if len(self._objects):
			drawObj=self._objects[0]
			rb=self.get_relative_coords100(drawObj._position.tuple_ps())		
		self.DeleteContents()
				
		# call user selected callback
		if userResponse==win32con.IDOK:
			apply(self._rb_callback, rb)
		else:
			apply(self._rb_callback,())	

		# execute pending create_box calls
		next_create_box = self._next_create_box
		self._next_create_box = []
		for win, msg, cb, box in next_create_box:
			win.create_box(msg, cb, box)

	def notifyListener(self,key,params):
		if not self.in_create_box_mode(): return 0
		if key=='onLButtonDown':DrawTk.DrawLayer.onLButtonDown(self,params)
		elif key=='onLButtonUp':DrawTk.DrawLayer.onLButtonUp(self,params)
		elif key=='onMouseMove':DrawTk.DrawLayer.onMouseMove(self,params)
		elif key=='OnDraw':DrawTk.DrawLayer.DrawObjLayer(self,params)
		return 1

	def in_create_box_mode(self):
		return __main__.toplevel._in_create_box

	def set_create_box_mode(self,f):
		if f:
			__main__.toplevel._in_create_box=self
			self.setScrollMode(1) ## DO NOT RESIZE DURING rbMode
		else:
			__main__.toplevel._in_create_box=None
			self.setScrollMode(0) ## RESIZE ALLOWED

	def get_box_modal_wnd(self):
		return __main__.toplevel._in_create_box

	def OnNCHitTest_X(self,params):
		if not self._create_box_dlg: return
		msg=win32mu.Win32Msg(params)
		pt=win32mu.Point(msg.pos())
		if self._create_box_dlg:
			rc=win32mu.Rect(self._create_box_dlg.GetWindowRect())
			if rc.isPtInRect(pt):
				self.ReleaseCapture()
