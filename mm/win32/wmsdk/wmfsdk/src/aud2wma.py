
import os

import wmfapi
import dshow

# init COM libs
# not needed if run from pythonwin
wmfapi.CoInitialize()

class RenderingReader:
	def __init__(self):
		print 'RenderingReader'
		self._start = None
	def __del__(self):
		print '~RenderingReader'

	def OnSetMediaType(self):
		print 'OnSetMediaType'

	def OnActive(self):
		print 'OnActive'

	def OnInactive(self):
		print 'OnInactive'

	def OnRenderSample(self):
		import time
		if self._start is None:
			self._start	 = time.time()
			print 'OnRenderSample', 0
		else:
			print 'OnRenderSample', time.time()-self._start


renderingReader = dshow.CreatePyRenderingListener(RenderingReader())

# convert any audio file to windows media format (asf or wma)
def convertaudiofile(infile, dstdir, file, node):
	# ignore suggested extension and make our own
	file = os.path.splitext(file)[0] + '.wma'
	fullpath = os.path.join(dstdir, file)

	profman = wmfapi.CreateProfileManager()

	# set an apropriate system profile
	# or a create a new one
	profile = profman.LoadSystemProfile(10)

	# find audio pin
	writer = wmfapi.CreateWriter()
	writer.SetProfile(profile)
	npins = writer.GetInputCount()
	audiopinix = -1
	audiopinmt = None
	audiopinprops = None
	print 'profile pins:'
	for i in range(npins):
		pinprop = writer.GetInputProps(i)
		pintype = pinprop.GetType()
		if pintype == wmfapi.WMMEDIATYPE_Audio:
			audiopinix = i
			audiopinprops = pinprop
			audiopinmt = pinprop.GetMediaType()
	if audiopinix>=0:
		print 'audiopin is pin ',audiopinix
	else:
		print 'no audio pin'
		return None

	writer.SetOutputFilename(fullpath);

	b = dshow.CreateGraphBuilder()
	b.RenderFile(infile)
	# find renderer
	try:
		aurenderer=b.FindFilterByName('Default DirectSound Device')
	except:
		aurenderer=None
	if not aurenderer:
		try:
			aurenderer=b.FindFilterByName('Default WaveOut Device')
		except:
			aurenderer=None
	if not aurenderer:
		print 'Audio renderer not found'
		return None

	# if is asf stream remove script 
	try:
		scriptrenderer=b.FindFilterByName('Internal Script Command Renderer')
	except:
		scriptrenderer=None
	else:
		b.RemoveFilter(scriptrenderer)

	enumpins=aurenderer.EnumPins()
	pin=enumpins.Next()
	aulastpin=pin.ConnectedTo()
	b.RemoveFilter(aurenderer)
	try:
		f = dshow.CreateFilter('Audio Windows Media Converter')
	except:
		print 'Audio windows media converter filter is not installed'
		return None
	try:
		wmconv=f.QueryIWMConverter()
	except:
		print 'Filter does not support interface IWMConverter'
		return
	wmconv.SetAdviceSink(renderingReader)	
	try:
		uk=writer.QueryIUnknown()
	except:
		print 'WMWriter QueryIUnknown failed'
		return
	wmconv.SetWMWriter(uk)

	b.AddFilter(f,'AWMC')
	b.Render(aulastpin)

	# media properties and converting is 
	# managed by our dshow filter
	mc = b.QueryIMediaControl()
	mc.Run()
	import win32ui
	while b.WaitForCompletion(0)==0:
		win32ui.PumpWaitingMessages()
	mc.Stop()
	win32ui.PumpWaitingMessages()
	del mc
	del b


infile = r'D:\ufs\mm\cmif\win32\wmsdk\wmfsdk\src\testdata\test.au'
outdir = r'D:\ufs\mm\cmif\win32\wmsdk\wmfsdk\src\testdata'

convertaudiofile(infile,outdir,'test.wma',None)

del renderingReader

# on exit: release COM libs
# not needed if run from pythonwin
wmfapi.CoUninitialize()