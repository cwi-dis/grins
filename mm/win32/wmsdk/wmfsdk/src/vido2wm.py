
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

# convert any video file to windows media format (asf or wmv)
def convertvideofile(infile, dstdir, file, node):
	# ignore suggested extension and make our own
	file = os.path.splitext(file)[0] + '.wmv'
	fullpath = os.path.join(dstdir, file)

	profman = wmfapi.CreateProfileManager()

	# set an apropriate system profile
	# or a create a new one
	profile = profman.LoadSystemProfile(0)

	# find audio pin
	writer = wmfapi.CreateWriter()
	writer.SetProfile(profile)
	npins = writer.GetInputCount()
	audiopinix = -1
	audiopinprops = None
	videopinix = -1
	videopinprops = None
	for i in range(npins):
		pinprop = writer.GetInputProps(i)
		pintype = pinprop.GetType()
		if pintype == wmfapi.WMMEDIATYPE_Audio:
			audiopinix = i
			audiopinprops = pinprop
		elif pintype == wmfapi.WMMEDIATYPE_Video:
			videopinix = i
			videopinprops = pinprop
			
	if videopinix<0:
		print 'no video pin'
		return None

	writer.SetOutputFilename(fullpath);
	print 'output file', fullpath

	b = dshow.CreateGraphBuilder()
	b.RenderFile(infile)
	renderer=b.FindFilterByName('Video Renderer')
	enumpins=renderer.EnumPins()
	pin=enumpins.Next()
	lastpin=pin.ConnectedTo()
	b.RemoveFilter(renderer)
	try:
		vf = dshow.CreateFilter('Video Windows Media Converter')
	except:
		print 'Video windows media converter filter is not installed'
		return None
	b.AddFilter(vf,'VWMC')
	enumpins=vf.EnumPins()
	pin=enumpins.Next()
	b.Connect(lastpin,pin)
	
	try:
		vmconv=vf.QueryIWMConverter()
	except:
		print 'Filter does not support interface IWMConverter'
		return None
	vmconv.SetAdviceSink(renderingReader)	
		
	try:
		ukwriter=writer.QueryIUnknown()
	except:
		print 'WMWriter QueryIUnknown failed'
		return None
	vmconv.SetWMWriter(ukwriter)

	mc = b.QueryIMediaControl()
	mc.Run()

	import win32ui
	while b.WaitForCompletion(0)==0:
		win32ui.PumpWaitingMessages()
	mc.Stop()
	win32ui.PumpWaitingMessages()

	return fullpath

inputfile = r'D:\ufs\mm\cmif\win32\wmsdk\wmfsdk\src\testdata\ms.avi'
outputdir = r'D:\ufs\mm\cmif\win32\wmsdk\wmfsdk\src\testdata'

convertvideofile(inputfile,outputdir,'ms.wmv',None)


# on exit: release COM libs
# not needed if run from pythonwin
wmfapi.CoUninitialize()