# QuickTime to RealMedia video converter

# file to be converted
# the output will be in the same dir with extension .rm
QtMovieToConvert = r'D:\ufs\mm\cmif\win32\Qt\media\Sample.mov'

import Qt

import os, sys
sys.path.append(r'D:\ufs\mm\cmif\lib\win32')
import winqt
import winqtcon

import win32ui, win32api, win32con
Afx=win32ui.GetAfx()
Sdk=win32ui.GetWin32Sdk()

import ddraw

from pywin.mfc import window

try:
	import producer
except ImportError:
	producer = None
	raise ImportError('no RealMedia codecs')

dir = r'D:\ufs\mm\cmif\bin\win32\Producer-SDK'
if os.path.exists(dir):
	producer.SetDllAccessPath(
	'DT_Plugins=%s\000' % os.path.join(dir, 'Plugins') +
	'DT_Codecs=%s\000' % os.path.join(dir, 'Codecs') +
	'DT_EncSDK=%s\000' % os.path.join(dir, 'Tools') +
	'DT_Common=%s\000' % os.path.join(dir, 'Common'))
else:
	raise ImportError('no RealMedia codecs')

engine = producer.CreateRMBuildEngine()

class RealVideoConverter:
	global engine, videopin, audiopin
	if engine is None:
		engine = producer.CreateRMBuildEngine()
	for pin in engine.GetPins():
		if pin.GetOutputMimeType() == producer.MIME_REALVIDEO:
			videopin = pin
		elif pin.GetOutputMimeType() == producer.MIME_REALAUDIO:
			audiopin = pin
	
	IDLE, ENCODING, DONE = 0, 1, 2
	
	def __init__(self, filename):
		self.outfilename = os.path.splitext(filename)[0] + '.rm'
		self.prepareEngine(self.outfilename)
		self.video_sample = None
		self.state = self.IDLE

	def __del__(self):
		self.video_sample = None
		
	def prepareEngine(self, outfilename):
		engine.SetDoOutputMimeType(producer.MIME_REALAUDIO, 0)
		engine.SetDoOutputMimeType(producer.MIME_REALVIDEO, 1)
		engine.SetDoOutputMimeType(producer.MIME_REALEVENT, 0)
		engine.SetDoOutputMimeType(producer.MIME_REALIMAGEMAP, 0)
		engine.SetDoOutputMimeType(producer.MIME_REALPIX, 0)

		cp = engine.GetClipProperties()
		cp.SetTitle('')
		cp.SetAuthor('')
		cp.SetCopyright('')
		cp.SetPerfectPlay(1)
		cp.SetMobilePlay(0)
		cp.SetSelectiveRecord(0)
		cp.SetDoOutputServer(0)
		cp.SetDoOutputFile(1)
		cp.SetOutputFilename(outfilename)

		ts = engine.GetTargetSettings()
		ts.RemoveAllTargetAudiences()
		ts.AddTargetAudience(producer.ENC_TARGET_DUAL_ISDN)
		ts.SetVideoQuality(producer.ENC_VIDEO_QUALITY_NORMAL)

		engine.SetDoMultiRateEncoding(0)
		engine.SetRealTimeEncoding(0)

	def setVideoProperties(self, width, height, framerate):
		props = videopin.GetPinProperties()
		props.SetVideoSize(width, height)
		props.SetVideoFormat(producer.ENC_VIDEO_FORMAT_RGB24)
		props.SetCroppingEnabled(0)
		props.SetFrameRate(framerate)
		self.video_sample = engine.CreateMediaSample()
	
	def prepareToEncode(self):
		if self.state == self.IDLE:
			print 'start encoding'
			self.video_sample = engine.CreateMediaSample()
			engine.PrepareToEncode()
			self.state = self.ENCODING

	def doneEncoding(self):
		if self.state == self.ENCODING:
			engine.DoneEncoding()
			self.state = self.DONE

	def isDone(self):
		return self.state == self.DONE

	def encode(self, data, sampletime):
		if self.isDone(): 
			return
		if sampletime < 0:
			flags = producer.MEDIA_SAMPLE_END_OF_STREAM
		else:
			flags = producer.MEDIA_SAMPLE_SYNCH_POINT
		self.video_sample.SetBuffer(data, sampletime, flags)
		videopin.Encode(self.video_sample)
		if sampletime < 0:
			self.doneEncoding()
			print 'done encoding', self.outfilename
			return

class MfcOsWnd(window.Wnd):
	"""Generic MfcOsWnd class"""
	def __init__ (self):
		window.Wnd.__init__(self,win32ui.CreateWnd())
		self._clstyle=0
		self._style=0
		self._exstyle=0
		self._icon=0
		self._cursor=0
		self._brush=0

	def setClstyle(self,clstyle):
		self._clstyle=clstyle

	def setStyle(self,style):
		self._style=style

	def setExstyle(self,exstyle):
		self._exstyle=exstyle

	def setIcon(self,icon):
		self._icon=icon

	def setIconApplication(self):
		self._icon=Afx.GetApp().LoadIcon(win32con.IDI_APPLICATION)

	def setStandardCursor(self,cursor):
		self._cursor=Afx.GetApp().LoadStandardCursor(cursor)

	def setStockBrush(self,idbrush):
		self._brush=Sdk.GetStockObject(idbrush)
	def setBrush(self,brush):
		self._brush=brush

	def create(self,title='untitled',x=0,y=0,width=200,height=150,parent=None,id=0):
		# register
		strclass=Afx.RegisterWndClass(self._clstyle,self._cursor,self._brush,self._icon)
		# create
		self.CreateWindowEx(self._exstyle,strclass,title,self._style,
			(x, y, width, height),parent,id)

class ToplevelWnd(MfcOsWnd):
	"""Generic ToplevelWnd class"""
	def __init__ (self):
		MfcOsWnd.__init__(self)
		self._clstyle=win32con.CS_DBLCLKS
		self._style=win32con.WS_OVERLAPPEDWINDOW | win32con.WS_CLIPCHILDREN
		self._exstyle=win32con.WS_EX_CLIENTEDGE

	def setClientRect(self, w, h):
		l1, t1, r1, b1 = self.GetWindowRect()
		l2, t2, r2, b2 = self.GetClientRect()
		dxe = dye = 0
		if (self._exstyle & win32con.WS_EX_CLIENTEDGE):
			dxe = 2*win32api.GetSystemMetrics(win32con.SM_CXEDGE)
			dye = 2*win32api.GetSystemMetrics(win32con.SM_CYEDGE)
		wi = (r1-l1) - (r2-l2)
		wp = w + wi + dxe
		hi = (b1-t1) - (b2-t2)
		hp = h + hi + dye
		flags=win32con.SWP_NOMOVE | win32con.SWP_NOZORDER 		
		self.SetWindowPos(0, (0,0,wp,hp), flags)

class QTWnd(MfcOsWnd):
	TIMER_TICK = 100

	def __init__ (self, bgcolor = (255, 0, 255)):
		MfcOsWnd.__init__(self, )
		self._clstyle=win32con.CS_DBLCLKS
		self._style = win32con.WS_CHILD |win32con.WS_CLIPSIBLINGS
		self.port = None
		self.movie = None
		self.ctrl = None
		self.__timer_id = 0

		self.__ddraw = None
		self.__frontBuffer = None
		self.__backBuffer = None
		self.__clipper = None
		self.__bgcolor = bgcolor

		self.__movieBuffer = None

		# movie position and size
		self._movieRect = 40, 30, 200, 240
		self.sampletime = 0
		self._converter = None

	def OnCreate(self, params):
		# back buffer size
		w, h = self.GetClientRect()[2:]

		self.__ddraw = ddraw.CreateDirectDraw()
		
		self.__ddraw.SetCooperativeLevel(self.GetSafeHwnd(), ddraw.DDSCL_NORMAL)

		ddsd = ddraw.CreateDDSURFACEDESC()
		ddsd.SetFlags(ddraw.DDSD_CAPS)
		ddsd.SetCaps(ddraw.DDSCAPS_PRIMARYSURFACE)
		self.__frontBuffer = self.__ddraw.CreateSurface(ddsd)

		ddsd = ddraw.CreateDDSURFACEDESC()
		ddsd.SetFlags(ddraw.DDSD_WIDTH | ddraw.DDSD_HEIGHT | ddraw.DDSD_CAPS)
		ddsd.SetCaps(ddraw.DDSCAPS_OFFSCREENPLAIN)
		ddsd.SetSize(w,h)
		self.__backBuffer = self.__ddraw.CreateSurface(ddsd)

		self.__clipper = self.__ddraw.CreateClipper(self.GetSafeHwnd())
		self.__frontBuffer.SetClipper(self.__clipper)
		self._pxlfmt = self.__frontBuffer.GetPixelFormat()
		
		# clear back buffer
		ddcolor = self.__backBuffer.GetColorMatch(self.__bgcolor or (255, 255, 255) )
		self.__backBuffer.BltFill((0, 0, w, h), ddcolor)

		self.qtplayer = winqt.QtPlayer()
		info = self.qtplayer.openForEncoding(QtMovieToConvert, self.__ddraw)
		if info is not None:
			width, height, framerate = info
			self._converter = RealVideoConverter(QtMovieToConvert)
			self._converter.setVideoProperties(width, height, framerate)
			self._converter.prepareToEncode()
			self._converter.encode(self.qtplayer.getDataAsRGB24(), 0)
			self.sampletime = 0

		self.HookMessage(self.OnTimer,win32con.WM_TIMER)
		self.__timer_id = self.SetTimer(1, self.TIMER_TICK)
	
	def OnTimer(self, params):
		if self._converter and not self._converter.isDone():
			self._converter.encode(self.qtplayer.getDataAsRGB24(), self.sampletime)
			self.sampletime = self.qtplayer.nextVideoData(self.sampletime)

		# back buffer size
		sd = self.__backBuffer.GetSurfaceDesc()
		w, h = sd.GetSize()

		# clear back buffer
		ddcolor = self.__backBuffer.GetColorMatch(self.__bgcolor or (255, 255, 255) )
		self.__backBuffer.BltFill((0, 0, w, h), ddcolor)

		# plot movie buffer to back buffer
		if self.qtplayer._dds:
			flags = ddraw.DDBLT_WAIT
			mx, my, mw, mh = self._movieRect
			self.__backBuffer.Blt((mx, my, mx+mw, my+mh), self.qtplayer._dds, (0, 0, mw, mh), flags)

		# flip
		rcFront = self.GetClientRect()
		rcFront = self.ClientToScreen(rcFront)
		rcBack = (0, 0, w, h)
		self.__frontBuffer.Blt(rcFront, self.__backBuffer, rcBack)
			
							
	def OnDestroy(self, params):
		if self.__timer_id:
			self.KillTimer(self.__timer_id)

		# 
		self._converter = None

		# real globals
		audiopin = None
		videopin = None
		engine = None

		# Qt cleanup
		self.qtplayer = None

		# DD cleanup
		del self.__movieBuffer
		del self.__frontBuffer
		del self.__backBuffer
		del self.__clipper
		del self.__ddraw

	def OnPaint(self):
		dc, paintStruct = self.BeginPaint()
		self.EndPaint(paintStruct)
			

def __test():
	wnd = ToplevelWnd()
	wnd.setStockBrush(win32con.WHITE_BRUSH)
	wnd.setStandardCursor(win32con.IDC_ARROW)
	wnd.create('GRiNS Lab',win32con.CW_USEDEFAULT,win32con.CW_USEDEFAULT,400,300)

	w = 400
	h = 300
	wnd.setClientRect(w, h)

	childwnd = QTWnd()
	childwnd.setStockBrush(win32con.WHITE_BRUSH)
	childwnd.setStandardCursor(win32con.IDC_ARROW)
	childwnd.create('qtchannel',0,0,w,h, wnd)

	wnd.ShowWindow(win32con.SW_SHOW)
	childwnd.ShowWindow(win32con.SW_SHOW)
	wnd.UpdateWindow()

if __name__ == '__main__':
	__test()


