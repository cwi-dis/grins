__version__ = "$Id$"

# DirectShow support
import dshow

# we need const WM_USER
import win32con

# private graph notification message
WM_GRPAPHNOTIFY=win32con.WM_USER+101

# a composite interface to dshow infrastructure.
# gets its name from its main interface: IGraphBuilder
class GraphBuilder:
	def __init__(self):
		self._builder = None
		self._mc = None
		self._mp = None
		try:
			self._builder = dshow.CreateGraphBuilder()
		except dshow.error, arg:
			print arg
			self._builder = None

	def __del__(self):
		# seems that the destruction process is important
		# due to win32ui window message hooking
		del self._mc
		del self._mp
		if self._builder:
			self._builder.Release()

	def Release(self):
		pass

	def RenderFile(self,url):
		try:
			self._builder.RenderFile(url)
		except dshow.error, arg:
			print arg
			return 0
		self._mc = self._builder.QueryIMediaControl()
		self._mp = self._builder.QueryIMediaPosition()
		return 1

	def Run(self):
		if self._mc:self._mc.Run()
	def Stop(self):
		if self._mc:self._mc.Stop()
	def Pause(self):
		if self._mc:self._mc.Pause()

	def GetDuration(self):
		if not self._mp: return 0
		return self._mp.GetDuration()

	def SetPosition(self,pos):
		if self._mp: self._mp.SetCurrentPosition(pos)
	def GetPosition(self):
		if not self._mp: return 0
		try:
			return self._mp.GetCurrentPosition()
		except:
			return 0

	def SetStopTime(self,pos):
		if self._mp:self._mp.SetStopTime(pos)
	def GetStopTime(self):
		if not self._mp: return 0
		return self._mp.GetStopTime()

	def GetVideoWindow(self):
		try:
			return self._builder.QueryIVideoWindow()
		except dshow.error, arg:
			print arg
			return None

	def SetVisible(self,f):
		vw = self.GetVideoWindow()
		if vw:vw.SetVisible(f)
	def SetWindow(self,wnd,msgid=WM_GRPAPHNOTIFY):
		vw = self.GetVideoWindow()
		if vw:
			vw.SetOwner(wnd.GetSafeHwnd()) 
			mex = self._builder.QueryIMediaEventEx()
			mex.SetNotifyWindow(wnd.GetSafeHwnd(),msgid)

	def SetNotifyWindow(self,wnd,msgid=WM_GRPAPHNOTIFY):
		mex = self._builder.QueryIMediaEventEx()
		mex.SetNotifyWindow(wnd.GetSafeHwnd(),msgid)

	def GetWindowPosition(self):
		vw = self.GetVideoWindow()
		rc=(0,0,100,100)
		if vw:rc = vw.GetWindowPosition()
		return rc

	def SetWindowPosition(self,rc):
		vw = self.GetVideoWindow()
		if vw: vw.SetWindowPosition(rc)


