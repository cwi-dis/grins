__version__ = "$Id$"

# DirectShow support
import dshow

# DirectDraw support for MMStream
import ddraw

# we need const WM_USER
import win32con

# private graph notification message
WM_GRPAPHNOTIFY=win32con.WM_USER+101

import MMurl

# a composite interface to dshow infrastructure.
# gets its name from its main interface: IGraphBuilder
class GraphBuilder:
	def __init__(self):
		try:
			self._builder = dshow.CreateGraphBuilder()
		except dshow.error, arg:
			if __debug__:
				print arg
			self._builder = None
		self._rendered = 0

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

	def RenderFile(self, url, exporter=None):
		url = MMurl.canonURL(url)
		url = MMurl.unquote(url)
		try:
			self._builder.RenderFile(url)
		except dshow.error, arg:
			if __debug__:
				print arg
			self._rendered = 0
		else:
			self._rendered = 1
		if exporter and self._rendered:
			writer = exporter.getWriter()
			writer.redirectAudioFilter(self._builder)
		return self._rendered

	def RedirectAudioFilter(self, writer):
		if writer and self._rendered:
			writer.redirectAudioFilter(self._builder)
		
	def Run(self):
		if self._builder and self._rendered:
			mc = self._builder.QueryIMediaControl()
			mc.Run()
	def Stop(self):
		if self._builder and self._rendered:
			mc = self._builder.QueryIMediaControl()
			mc.Stop()
	def Pause(self):
		if self._builder and self._rendered:
			mc = self._builder.QueryIMediaControl()
			mc.Pause()

	def GetDuration(self):
		if self._builder and self._rendered:
			try:
				mp = self._builder.QueryIMediaPosition()
				return mp.GetDuration()
			except:
				return 100 # sometimes should be infinite
		return 1.0

	def SetPosition(self,pos):
		if self._builder and self._rendered:
			mp = self._builder.QueryIMediaPosition()
			mp.SetCurrentPosition(pos)
	def GetPosition(self):
		if self._builder and self._rendered:
			mp = self._builder.QueryIMediaPosition()
			return mp.GetCurrentPosition()
		return 0

	def SetStopTime(self,pos):
		if self._builder and self._rendered:
			mp = self._builder.QueryIMediaPosition()
			mp.SetStopTime(pos)
	def GetStopTime(self):
		if self._builder and self._rendered:
			mp = self._builder.QueryIMediaPosition()
			return mp.GetStopTime()
		return 0

	def GetVideoWindow(self):
		try:
			return self._builder.QueryIVideoWindow()
		except dshow.error, arg:
			if __debug__:
				print arg
			return None

	def SetVisible(self,f):
		vw = self.GetVideoWindow()
		if vw:vw.SetVisible(f)
	def SetWindow(self,wnd,msgid=WM_GRPAPHNOTIFY):
		vw = self.GetVideoWindow()
		if vw:
			hwnd = wnd.GetSafeHwnd()
			vw.SetOwner(hwnd) 
			mex = self._builder.QueryIMediaEventEx()
			mex.SetNotifyWindow(hwnd,msgid)

	def SetNotifyWindow(self,wnd,msgid=WM_GRPAPHNOTIFY):
		if self._builder and self._rendered:
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
		if not self._builder or not self._rendered: return []
		enumobj = self._builder.EnumFilters()
		f = enumobj.Next()
		filters = []
		while f:		
			fname = f.QueryFilterName()
			filters.insert(0,fname)
			f = enumobj.Next()
		return filters

	def IsASF(self):
		if not self._builder or not self._rendered: return 0
		enumobj = self._builder.EnumFilters()
		f = enumobj.Next()
		while f:		
			fname = f.QueryFilterName()
			if fname.find('ASF')>=0:
				return 1
			f = enumobj.Next()
		return 0
		
	def HasVideo(self):
		if not self._builder or not self._rendered: return None
		try:
			return self._builder.FindFilterByName('Video Renderer')
		except:
			return None
		
# a shortcut usefull when we want to know
# the type of an asf stream (video or audio)
def HasVideo(url):
	try:
		builder = GraphBuilder()
	except:
		if __debug__:
			print 'Missing DirectShow infrasrucrure'
		return None
	if not builder.RenderFile(url):
		return None
	return builder.HasVideo()

# Returns the size of a video	
def GetVideoSize(url):
	import urlcache
	cache = urlcache.urlcache[url]
	width, height = cache.get('width'), cache.get('height')
	if width is None or height is None:
		mtype = urlcache.mimetype(url)
		if mtype and mtype.find('quicktime') >= 0:
			import winqt
			if winqt.HasQtSupport():
				import MMurl
				try:
					filename = MMurl.urlretrieve(url)[0]
				except IOError:
					return 100, 100
				player = winqt.QtPlayer()
				player.open(url)
				width, height = player.getMovieRect()[2:]
		if width is None or height is None:
			try:
				builder = GraphBuilder()
			except:
				if __debug__:
					print 'Missing DirectShow infrasrucrure'
				return 100, 100

			if not builder.RenderFile(url):
				return 100, 100

			width, height = builder.GetWindowPosition()[2:]
		cache['width'] = width
		cache['height'] = height
	return width, height


# Returns the duration of the media file in secs	
def GetMediaDuration(url):
	try:
		builder = GraphBuilder()
	except:
		if __debug__:
			print 'Missing DirectShow infrasrucrure'
		return 0
	if not builder.RenderFile(url):
		return 0

	return builder.GetDuration()

# Returns frames per second or zero on failure	
def GetFrameRate(url):
	try:
		builder = dshow.CreateGraphBuilder()
	except:
		if __debug__:
			print 'Missing DirectShow infrasrucrure'
		return 0
	url = MMurl.canonURL(url)
	url = MMurl.unquote(url)
	try:
		builder.RenderFile(url)
	except:
		if __debug__:
			print 'Failed to render', url
		return 0
	try:
		bv = builder.QueryIBasicVideo()
	except: 
		if __debug__:
			print 'Failed to get frame rate of', url
		fr = 0
	else:
		fr = int(0.5 + 1.0/bv.GetAvgTimePerFrame())
		del bv
	return fr
	
class MMStream:
	def __init__(self, ddobj):
		mmstream = dshow.CreateMultiMediaStream()
		mmstream.Initialize()
		mmstream.AddPrimaryVideoMediaStream(ddobj)
		try:
			mmstream.AddPrimaryAudioMediaStream()
		except dshow.error, arg:
			if __debug__:
				print arg
		self._mmstream = mmstream
		self._mstream = None
		self._ddstream = None
		self._sample = None
		self._dds = None
		self._rect = None
		self._parsed = 0

	def __repr__(self):
		s = '<%s instance' % self.__class__.__name__
		filters = self.getFiltersNames()
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

	def getFiltersNames(self):
		if not self._parsed: return []
		fg = self._mmstream.GetFilterGraph()
		enumobj = fg.EnumFilters()
		f = enumobj.Next()
		filters = []
		while f:		
			fname = f.QueryFilterName()
			filters.insert(0,fname)
			f = enumobj.Next()
		return filters

	def open(self, url, exporter=None):
		mmstream = self._mmstream
		url = MMurl.canonURL(url)
		url = MMurl.unquote(url)
		try:
			mmstream.OpenFile(url)
		except:
			if __debug__:
				print 'failed to render', url
			self._parsed = 0
			return 0
		self._parsed = 1
		if exporter and self._parsed:
			fg = self._mmstream.GetFilterGraph()
			writer = exporter.getWriter()
			writer.redirectAudioFilter(fg, hint='0001')
		self._mstream = self._mmstream.GetPrimaryVideoMediaStream()
		self._ddstream = self._mstream.QueryIDirectDrawMediaStream()
		try:
			self._sample = self._ddstream.CreateSample()
		except dshow.error, arg:
			if __debug__:
				print arg
			return 0
		self._dds = ddraw.CreateSurfaceObject()
		self._rect = self._sample.GetSurface(self._dds)
		return 1

	def __del__(self):
		del self._dds
		del self._mstream
		del self._ddstream
		del self._sample
		del self._mmstream
			
	def run(self):
		if self._parsed:
			self._mmstream.SetState(1)

	def stop(self):
		if self._parsed:
			self._mmstream.SetState(0)
		
	def update(self):
		if not self._parsed: return 0
		return self._sample.Update()

	def seek(self, secs):
		if not self._parsed: return
		if secs==0.0:
			v = dshow.large_int(0)
		else:
			msecs = dshow.large_int(int(secs*1000+0.5))
			f = dshow.large_int('10000')
			v = msecs * f
		try:
			self._mmstream.Seek(v)
		except:
			if __debug__:
				print 'seek not supported for media type'

	def getDuration(self):
		if not self._parsed: return
		d = self._mmstream.GetDuration()
		f = dshow.large_int('10000')
		v = d / f
		secs = 0.001*float(v)
		return secs

	def getTime(self):
		if not self._parsed: return
		d = self._mmstream.GetTime()
		f = dshow.large_int('10000')
		v = d / f
		secs = 0.001*float(v)
		return secs


###################################
class VideoFormat:
	def __init__(self, name, descr, width, height, format):
		self.__name = name
		self.__descr = descr
		self.__width = width
		self.__height = height
		self.__format = format
		
	def getname(self):
		return self.__name
		
	def getdescr(self):
		return self.__descr
		
	def getsize(self):
		return self.__width, self.__height
		
	def getformat(self):
		return self.__format

class AudioFormat:
	def __init__(self, name, descr, nchannels, samplespersec, bitspersample, format):
		self.__name = name
		self.__descr = descr
		self.__nchannels = nchannels
		self.__samplespersec = samplespersec
		self.__bitspersample = bitspersample
		self.__format = format

	def __repr__(self):
		return self.__name

	def getname(self):
		return self.__name

	def getdescr(self):
		return self.__descr

	def getnchannels(self):
		return self.__nchannels

	def getsamplespersec(self):
		return self.__samplespersec

	def getbitspersample(self):
		return self.__bitspersample

	def getbytespersample(self):
		return self.__bitspersample/8

	def getformat(self):
		return self.__format

	def getnsamples(self, nbytes):
		return nbytes/self.getbytespersample()

class ReaderFilter:
	def __init__(self, driver, dispname):
		self._driver = driver
		self._dispname = dispname
		self._active = 0
		self._dataqueue = []
		self._properties = None
		self._time = 0

	def getProperties(self):
		return self._properties

	def isActive(self):
		return self._active

	def getTime(self):
		return self._time

	def OnSetMediaType(self, mt):
		props = None
		if mt.GetType() == 'audio':
			props = mt.GetAudioInfo()
		elif mt.GetType() == 'video':
			props = mt.GetVideoInfo()
		self._properties = props

	def OnActive(self):
		self._active = 1

	def OnInactive(self):
		self._active = 0

	def OnRenderSample(self, ms):
		if self._active and self._driver.isActive():
			data = ms.GetData()
			btime, etime = ms.GetTime()
			packet = btime, data
			self._dataqueue.append(packet)
			self._time = btime

	def readData(self):
		if not self.isActive():
			return self.__nextData()
		import win32ui
		while not self._dataqueue and self._active and self._driver.isActive():
			win32ui.PumpWaitingMessages(0,0)
		return self.__nextData()

	def readDataSamples(self):
		if not self.isActive():
			return self.__nextDataSamples()
		import win32ui
		while not self._dataqueue and self._active and self._driver.isActive():
			win32ui.PumpWaitingMessages(0,0)
		return self.__nextDataSamples()

	def __nextData(self):
		if self._dataqueue:
			data = self._dataqueue[0]
			self._dataqueue = self._dataqueue[1:]
			return data
		return self._time, None

	def __nextDataSamples(self):
		if self._dataqueue:
			data = self._dataqueue
			self._dataqueue = []
			return data
		return [(self._time, None),]

class AudioReaderFilter(ReaderFilter):
	def OnRenderSample(self, ms):
		if self._active and self._driver.isActive():
			data = ms.GetData()
			btime, etime = ms.GetTime()
			if len(data) > 9216:
				# split heuristics
				n = len(data)/4608
				n = 2*(n/2)
				dd = len(data)/n
				dt = (etime-btime)/n
				begin = 0
				begin_time = btime
				for i in range(n):
					if i<n-1: end = begin + dd
					else: end = len(data)
					packet = begin_time, data[begin:end]
					self._dataqueue.append(packet)
					begin = begin + dd
					begin_time = begin_time + dt
			else:
				packet = btime, data
				self._dataqueue.append(packet)
			self._time = btime
		
class MediaReader:
	def __init__(self, url):		
		self._filtergraph = None

		self._videofilter = None
		self._videopeer = None

		self._audiofilter = None
		self._audiopeer = None

		self._active = 0
		self._started = 0

		self._filtergraph = dshow.CreateGraphBuilder()
		url = MMurl.canonURL(url)
		url = MMurl.unquote(url)
		try:
			self._filtergraph.RenderFile(url)
		except dshow.error, arg:
			self._filtergraph = None
			if __debug__:
				print arg
		if self._filtergraph is None:
			raise IOError, "Cannot open: %s" % filename

		self._buildReaderFilterGraph(self._filtergraph)
		
	def __del__(self):
		if self._active: 
			self._stop()
		self._audiopeer = None
		self._audiofilter = None
		self._videopeer = None
		self._videofilter = None
		self._filtergraph = None

	def GetDuration(self):
		if self._filtergraph:
			mp = self._filtergraph.QueryIMediaPosition()
			return int(1000*mp.GetDuration()+0.5)
		return 0

	def GetAudioDuration(self): 
		return self.GetDuration()

	def GetVideoDuration(self): 
		return self.GetDuration()

	def GetTime(self):
		mp = self._filtergraph.QueryIMediaPosition()
		return int(1000.0*mp.GetCurrentPosition()+0.5)

	def isActive(self):
		if not self._active:
			return 0
		if self._filtergraph.WaitForCompletion(0)==0:
			return 1
		self._stop()
		self._active = 0
		return 0

	def HasAudio(self):
		return self._audiofilter is not None

	def HasVideo(self):
		return self._videofilter is not None

	def ReadAudio(self, frames=None):
		if not self._started:
			self._run()
		return self._audiofilter.readData()

	def ReadVideo(self):
		if not self._started:
			self._run()
		return self._videofilter.readData()

	def ReadAudioSamples(self, frames=None):
		if not self._started:
			self._run()
		return self._audiofilter.readDataSamples()

	def ReadVideoSamples(self):
		if not self._started:
			self._run()
		return self._videofilter.readDataSamples()

	def GetVideoFormat(self):
		import imgformat
		width, height, framerate, isrgb24 = self._videofilter.getProperties()
		return VideoFormat('dummy_format', 'Dummy Video Format', width, height, imgformat.bmprgble_noalign)

	def GetVideoFrameRate(self):
		width, height, framerate, isrgb24 = self._videofilter.getProperties()
		return framerate

	def GetAudioFormat(self):
		nChannels, nSamplesPerSec, bitsPerSample, isPCM = self._audiofilter.getProperties()
		return nChannels, nSamplesPerSec, bitsPerSample
		
	def GetAudioFormat(self):
		nChannels, nSamplesPerSec, bitsPerSample, isPCM = self._audiofilter.getProperties()
		return AudioFormat('', '', nChannels, nSamplesPerSec, bitsPerSample, 'WAVE_FORMAT_PCM')
			
	def GetAudioFrameRate(self):
		nChannels, nSamplesPerSec, bitsPerSample, isPCM = self._audiofilter.getProperties()
		return nSamplesPerSec

	def _run(self):
		self._active = 1
		mc = self._filtergraph.QueryIMediaControl()
		mc.Run()
		self._started = 1

	def _stop(self):
		self._active = 0
		mc = self._filtergraph.QueryIMediaControl()
		mc.Stop()

	def _buildReaderFilterGraph(self, fg):
		try:
			videorenderer = fg.FindFilterByName('Video Renderer')
		except:
			videorenderer = None
		
		if videorenderer:
			enumpins = videorenderer.EnumPins()
			pin = enumpins.Next()
			lastpin = pin.ConnectedTo()
			fg.RemoveFilter(videorenderer)

			# create wmv converter filter
			try:
				vpf = dshow.CreateFilter('Video Pipe')
			except dshow.error:
				if __debug__:
					print 'Video pipe filter not installed'
				raise dshow.error, 'Video pipe filter not installed'
		
			# set listener
			try:
				pipe = vpf.QueryIPipe()
			except:
				if __debug__:
					print 'Filter does not support IPipe'
				raise dshow.error, 'Filter does not support IPipe'

			self._videofilter = ReaderFilter(self, 'video filter')
			self._videopeer = dshow.CreatePyRenderingListener(self._videofilter)
			pipe.SetAdviceSink(self._videopeer)

			# add and connect wmv converter filter
			fg.AddFilter(vpf,'VPF')
			enumpins = vpf.EnumPins()
			pin = enumpins.Next()
			fg.Connect(lastpin, pin)

		# find audio renderer
		try:
			audiorenderer = fg.FindFilterByName('Default DirectSound Device')
		except:
			audiorenderer=None
		if not audiorenderer:
			try:
				audiorenderer = fg.FindFilterByName('Default WaveOut Device')
			except:
				audiorenderer = None
		if audiorenderer:
			enumpins = audiorenderer.EnumPins()
			pin = enumpins.Next()
			aulastpin = pin.ConnectedTo()
			fg.RemoveFilter(audiorenderer)
			try:
				apf = dshow.CreateFilter('Audio Pipe')
			except:
				if __debug__:
					print 'Audio pipe filter not installed'
				raise dshow.error, 'Audio pipe filter not installed'
			try:
				pipe = apf.QueryIPipe()
			except:
				if __debug__:
					print 'Filter does not support IPipe'
				raise dshow.error, 'Filter does not support IPipe'
			self._audiofilter = AudioReaderFilter(self, 'audio filter')
			self._audiopeer = dshow.CreatePyRenderingListener(self._audiofilter)
			pipe.SetAdviceSink(self._audiopeer)
			fg.AddFilter(apf,'APF')
			fg.Render(aulastpin)

