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
		try:
			self._builder = dshow.CreateGraphBuilder()
		except dshow.error, arg:
			print arg
			self._builder = None

	def __repr__(self):
		s = '<%s instance' % self.__class__.__name__
		filters = self.GetFiltersNames()
		n = len(filters)
		if n: 
			s = s + ', filters = '
			s = s + "\'" + filters[0] + "\'"
		else:
			s = s + ', not rendered'
			
		for i in range(1,n):
			s = s + ", \'" + filters[i] + "\'"
		s = s + '>'
		return s

	def Release(self):
		pass

	def RenderFile(self,url):
		try:
			self._builder.RenderFile(url)
		except dshow.error, arg:
			print arg
			return 0
		return 1

	def Run(self):
		if self._builder:
			mc = self._builder.QueryIMediaControl()
			mc.Run()
	def Stop(self):
		if self._builder:
			mc = self._builder.QueryIMediaControl()
			mc.Stop()
	def Pause(self):
		if self._builder:
			mc = self._builder.QueryIMediaControl()
			mc.Pause()

	def GetDuration(self):
		if self._builder:
			mp = self._builder.QueryIMediaPosition()
			return mp.GetDuration()
		return 0

	def SetPosition(self,pos):
		if self._builder:
			mp = self._builder.QueryIMediaPosition()
			mp.SetCurrentPosition(pos)
	def GetPosition(self):
		if self._builder:
			mp = self._builder.QueryIMediaPosition()
			return mp.GetCurrentPosition()
		return 0

	def SetStopTime(self,pos):
		if self._builder:
			mp = self._builder.QueryIMediaPosition()
			mp.SetStopTime(pos)
	def GetStopTime(self):
		if self._builder:
			mp = self._builder.QueryIMediaPosition()
			return mp.GetStopTime()
		return 0

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

	# get all filter names of GraphBuilder graph
	# note: The file reader filter gets its name from the file
	def GetFiltersNames(self):
		if not self._builder: return
		enumobj = self._builder.EnumFilters()
		f = enumobj.Next()
		filters = []
		while f:		
			fname = f.QueryFilterName()
			filters.insert(0,fname)
			f = enumobj.Next()
		return filters

	def HasVideo(self):
		if not self._builder: return
		try:
			return self._builder.FindFilterByName('Video Renderer')
		except:
			return None
		
# a shortcut usefull when we want to know
# the type of an asf stream (video or audio)
def hasvideo(self,url):
	b = GraphBuilder()
	b.RenderFile(url)
	return b.HasVideo()!=None