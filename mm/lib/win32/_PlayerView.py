__version__ = "$Id$"

# win32 constants
import win32con

# app constants
from appcon import *

# kick toplevel.serve_events()
import __main__

# win32 structures helpers
import win32mu

# base class and mixins
from win32dlview import DisplayListView
import win32window

# ddraw.error
import ddraw

class _PlayerView(DisplayListView, win32window.DDWndLayer):
	def __init__(self,doc,bgcolor=None):
		DisplayListView.__init__(self,doc)
		self._canclose=1
		self._tid=None
		self.__lastMouseMoveParams = None

		self._usesLightSubWindows = 1

		win32window.DDWndLayer.__init__(self, self, bgcolor)

		self._viewport = None
		self.__wmwriter = None

	def init(self, rc, title='View', units= UNIT_MM, adornments=None, canvassize=None, commandlist=None, bgcolor=None):
		DisplayListView.init(self, rc, title=title, units=units, adornments=adornments, canvassize=canvassize,
			commandlist=commandlist, bgcolor=bgcolor)
		x, y, w, h = rc
		self._viewport = win32window.Viewport(self, 0, 0, w, h, bgcolor)

	def newwindow(self, coordinates, pixmap = 0, transparent = 0, z = 0, type_channel = SINGLE, units = None, bgcolor=None):
		return self._viewport.newwindow(coordinates, pixmap, transparent, z, type_channel, units, bgcolor)

	def closeViewport(self, viewport):
		DisplayListView.close(self)

	def OnCreate(self,params):
		DisplayListView.OnCreate(self, params)
		if self._usesLightSubWindows:
			self.createDDLayer()

	def OnDestroy(self, msg):		
		if self._usesLightSubWindows:
			self.destroyDDLayer()
		DisplayListView.OnDestroy(self, msg)

	def OnInitialUpdate(self):
		DisplayListView.OnInitialUpdate(self)
		self.HookMessage(self.onCreateBoxOK,WM_USER_CREATE_BOX_OK)
		self.HookMessage(self.onCreateBoxCancel,WM_USER_CREATE_BOX_CANCEL)

	# Do not close and recreate topwindow, due to flushing screen
	# and loose of focus. 
	# Nobody would excpect to destroy a window by resizing it!
	def close(self):
		if self._canclose:
			DisplayListView.close(self)
					
	# The response of the view for the WM_SIZE (Resize) message						
	def onSize(self,params):
		msg=win32mu.Win32Msg(params)
		if msg.minimized(): return

		# This historic function does not need to be
		# called since the channels are now destroyed
		# and re-created. The effect of calling it is
		# a flickering screen 
#		self._do_resize(msg.width(),msg.height())
		
		# destroy displists while dragging?
		# i.e repaint previous content while dragging?
		# Its a preference. 
#		self._destroy_displists_tree()

		# after _do_resize because it uses old self._rect
		self._rect=0,0,msg.width(),msg.height()
		self.fitCanvas(msg.width(),msg.height())

		# Do not use PostMessage. ChannelWindow.resize
		# fails to save_geometry if the sys attribute
		# 'Show Window Contents While Dragging' is set
		# since then this function is called to often
#		self.PostMessage(win32con.WM_USER)
		from __main__ import toplevel
		if self._tid:
			toplevel.canceltimer(self._tid)
		self._tid=toplevel.settimer(0.2,(self.onPostResize,()))

	def onPostResize(self,params=None):
		self._tid=None
		self._canclose=0
		if not self._usesLightSubWindows: 
			self._resize_tree()
		self._canclose=1

	def OnDraw(self, dc):
		if self.in_create_box_mode() and self.get_box_modal_wnd()==self:
			self.notifyListener('OnDraw',dc)
			return
		if not self._usesLightSubWindows:
			DisplayListView.OnDraw(self,dc)
		else:
			self.update()

	def onMouseEvent(self, point, ev):
		cont, stop = 0, 1	
		if not self._usesLightSubWindows:
			if DisplayListView.onMouseEvent(self, point, ev):
				return stop
		action =  self._viewport.onMouseEvent(point, ev)

		# kick immediate responses
		__main__.toplevel.serve_events()

		return action

	def updateMouseCursor(self):
		self.onMouseMove()

	def onMouseMove(self, params=None):
		if not params and not self.__lastMouseMoveParams:
			return
		if not params: params = self.__lastMouseMoveParams
		else: self.__lastMouseMoveParams = params
		
		if not self._usesLightSubWindows or self.in_create_box_mode():
			DisplayListView.onMouseMove(self, params)
		
		msg=win32mu.Win32Msg(params)
		flags = 0
		point=msg.pos()
		point = self._DPtoLP(point)
		
		self._viewport.onMouseMove(flags, point)

	def OnEraseBkgnd(self,dc):
		if not self._usesLightSubWindows or not self._active_displist:
			return DisplayListView.OnEraseBkgnd(self,dc)
		win32mu.DrawRectangle(dc, self.GetClientRect(), self._bgcolor or (255, 255, 255))
		return 1
		
	def update(self, rc=None):
		if not self._ddraw or not self._frontBuffer or not self._backBuffer:
			return
		if self._frontBuffer.IsLost():
			if not self._frontBuffer.Restore():
				# we can't do anything for this
				# system is busy with video memory
				self.InvalidateRect(self.GetClientRect())
				return
		if self._backBuffer.IsLost():
			if not self._backBuffer.Restore():
				# and for this either
				# system should be out of memory
				self.InvalidateRect(self.GetClientRect())
				return
		
		# do we have anything to update?
		if rc and (rc[2]==0 or rc[3]==0): 
			return 

		self.paint(rc)

		if rc is None:
			rcBack = self.GetClientRect()
		else:
			rcBack = rc[0], rc[1], rc[0]+rc[2], rc[1]+rc[3]
		
		rcFront = self.ClientToScreen(rcBack)
		try:
			self._frontBuffer.Blt(rcFront, self._backBuffer, rcBack)
		except ddraw.error, arg:
			print arg
	
	def getDrawBuffer(self):
		return self._backBuffer

	def getContextOsWnd(self):
		return self

	def getwindowpos(self, rel=None):
		return self._rect

	def paint(self, rc=None):
		if rc is None:
			rcPaint = self.GetClientRect()
		else:
			rcPaint = rc[0], rc[1], rc[0]+rc[2], rc[1]+rc[3] 
		if self._convbgcolor == None:
			self._convbgcolor = self._backBuffer.GetColorMatch(self._bgcolor or (255, 255, 255) )
		try:
			self._backBuffer.BltFill(rcPaint, self._convbgcolor)
		except ddraw.error, arg:
			print arg
			return

		if self._viewport:	
			self._viewport.paint(rc)
	
	def beginExport(self):
		print 'beginExport', self._title
		if self.__wmwriter:
			return
		x, y, w, h = self.GetClientRect()
		filename = '%s.wmv' % self._title
		self.__wmwriter = WMWriter(self, w, h, filename)
		self.__wmwriter.beginWriting()

	def endExport(self):
		print 'endExport', self._title
		if self.__wmwriter:
			self.__wmwriter.endWriting()
			self.__wmwriter = None
			
##################################
# This is temporary here for testing

import time
import windowinterface


"""
System profiles
0 Dial-up Modems - ISDN Multiple Bit Rate Video
1 Intranet - High Speed LAN Multiple Bit Rate Video
2 28.8, 56, and 100 Multiple Bit Rate Video
3 6.5 voice audio
4 16 AM Radio
5 28.8 FM Radio Mono
6 28.8 FM Radio Stereo
7 56 Dial-up High Quality Stereo
8 64 Near CD Quality Audio
9 96 CD Quality Audio
10 128 CD Quality Audio
11 28.8 Video - Voice
12 28.8 Video - Audio Emphasis
13 28.8 Video for Web Server
14 56 Dial-up Modem Video
15 56 Dial-up Video for Web Server
16 100 Video
17 250 Video
18 512 Video
19 1Mb Video
20 3Mb Video
"""
# select profile
SYSTEM_PROFILE  = 18
		
class WMWriter:
	def __init__(self, ctx, w, h, filename):
		import wmfapi
		profman = wmfapi.CreateProfileManager()
		prof = profman.LoadSystemProfile(SYSTEM_PROFILE) 
		writer = wmfapi.CreateDDWriter(prof)
		writer.SetOutputFilename(filename)
		rgbfmt = self.__getFormat(ctx._pxlfmt)
		wmtype = wmfapi.CreateVideoWMType(w, h, rgbfmt)
		writer.SetVideoFormat(wmtype)
		
		self._writer = writer
		self._w, self._h = w, h
		self._dds = ctx.CreateSurface(w, h)
		self._ctx = ctx
		self._timerid = 0

	def beginWriting(self):
		self.__start = time.time()
		self._writer.BeginWriting()
		self.write(self, first=1)

	def endWriting(self):
		if self._timerid:
			windowinterface.canceltimer(self._timerid)
			self._timerid = 0
		self.write(settimer=0)
		self._writer.Flush()
		self._writer.EndWriting()

	def write(self, settimer=1, first=0):
		dds = self._ctx.getDrawBuffer()
		if first:
			msecs = 0
		else:
			secs = time.time() - self.__start
			msecs = int(secs*1000.0+0.5)
		try:
			rc = 0, 0, self._w, self._h
			self._dds.Blt(rc, dds, rc)
		except ddraw.error, arg:
			print arg
			return
		self._writer.WriteDDSurface(self._dds.GetBuffer(), msecs)
		self._dds.ReleaseBuffer()
		if settimer:
			self._timerid = windowinterface.settimer(0.1,(self.write,()))

	def __getFormat(self, pxlfmt):
		screenBPP = pxlfmt[0]
		if screenBPP==32:
			rgbfmt = 'RGB32'
		elif screenBPP==24:
			rgbfmt = 'RGB24'
		elif screenBPP==16:
			rgbfmt = 'RGB%d%d%d' % pxlfmt[1:]
		else:
			import wmfapi
			raise wmfapi.error
		return rgbfmt
