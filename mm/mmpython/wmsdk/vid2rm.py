
import dshow
import os
engine=None

def convertvideofile(u, dstdir, file, node):
	import producer
	global engine
	if os.environ.has_key('REAL_PRODUCER'):
		producer.SetDllCategoryPaths(os.environ['REAL_PRODUCER'])
	# ignore suggested extension and make our own
	file = os.path.splitext(file)[0] + '.rm'
	fullpath = os.path.join(dstdir, file)
	if engine is None:
		engine = producer.CreateRMBuildEngine()
	for pin in engine.GetPins():
		if pin.GetOutputMimeType() == producer.MIME_REALVIDEO:
			videopin = pin
	engine.SetDoOutputMimeType(producer.MIME_REALAUDIO, 0)
	engine.SetDoOutputMimeType(producer.MIME_REALVIDEO, 1)
	engine.SetDoOutputMimeType(producer.MIME_REALEVENT, 0)
	engine.SetDoOutputMimeType(producer.MIME_REALIMAGEMAP, 0)
	engine.SetDoOutputMimeType(producer.MIME_REALPIX, 0)
	engine.SetRealTimeEncoding(0)
	engine.SetDoMultiRateEncoding(1)
	cp = engine.GetClipProperties()
	ts = engine.GetTargetSettings()
	if node is not None:
		cp.SetTitle(MMAttrdefs.getattr(node, 'title'))
		cp.SetAuthor(MMAttrdefs.getattr(node, 'author'))
		cp.SetCopyright(MMAttrdefs.getattr(node, 'copyright'))
		ts.SetVideoQuality(MMAttrdefs.getattr(node, 'project_videotype'))
		ts.RemoveAllTargetAudiences()
		target = MMAttrdefs.getattr(node, 'project_targets')
		for i in range(5):
			if (1 << i) & target:
				ts.AddTargetAudience(i)
		if not target:
			#ts.AddTargetAudience(producer.ENC_TARGET_28_MODEM)
			ts.AddTargetAudience(producer.ENC_TARGET_56_MODEM)
	else:
		# we don't know nothin' about the node so use some defaults
		cp.SetTitle('')
		cp.SetAuthor('')
		cp.SetCopyright('')
		ts.AddTargetAudience(producer.ENC_TARGET_28_MODEM)
		ts.SetVideoQuality(producer.ENC_VIDEO_QUALITY_NORMAL)
	cp.SetPerfectPlay(1)
	cp.SetMobilePlay(0)
	cp.SetSelectiveRecord(0)
	cp.SetDoOutputServer(0)
	cp.SetDoOutputFile(1)
	cp.SetOutputFilename(fullpath)

	b = dshow.CreateGraphBuilder()
	b.RenderFile(u)
	renderer=b.FindFilterByName('Video Renderer')
	enumpins=renderer.EnumPins()
	pin=enumpins.Next()
	lastpin=pin.ConnectedTo()
	b.RemoveFilter(renderer)
	try:
		f = dshow.CreateFilter('Video Real Media Converter')
	except:
		print 'Video real media converter filter is not installed'
		return
	b.AddFilter(f,'VRMC')
	b.Render(lastpin)
	try:
		rconv=f.QueryIRealConverter()
	except:
		print 'Filter does not support interface IRealConverter'
		return
	try:
		uk=engine.QueryInterfaceUnknown()
	except:
		print 'RMABuildEngine QueryInterfaceUnknown failed'
		return
	rconv.SetInterface(uk,'IRMABuildEngine')

	try:
		uk=videopin.QueryInterfaceUnknown()
	except:
		print 'RMAInputPin QueryInterfaceUnknown failed'
		return
	rconv.SetInterface(uk,'IRMAInputPin')

	try:
		aurenderer=b.FindFilterByName('Default DirectSound Device')
	except:
		aurenderer=None
	if not aurenderer:
		try:
			aurenderer=b.FindFilterByName('Default WaveOut Device')
		except:
			aurenderer=None
	if aurenderer:
		b.RemoveFilter(aurenderer)

	# PinProperties,MediaSample,PrepareToEncode,Encode, DoneEncoding
	# are all managed by our dshow filter

	mc = b.QueryIMediaControl()
	mc.Run()
	b.WaitForCompletion()
	mc.Stop()

inputfile='D:\\ufs\\mm\\cmif\\Build\\common\\testdoc\\testdatampg.mpg'
#inputfile='D:\\ufs\\mm\\cmif\\win32\\DXMedia\\bin\\hokey.avi'
#inputfile='D:\\ufs\\mmback\\mpeg\\7closet.mpg'
outputdir='d:\\ufs\\mm\\cmif\\win32\\DXMedia\\bin'
os.environ['REAL_PRODUCER']='c:\\Program Files\\RealSDK\\Producer\\BIN\\'

convertvideofile(inputfile,outputdir,'xxx.rm',None)