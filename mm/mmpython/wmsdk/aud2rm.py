
import dshow
import os
engine=None

def convertaudiofilex(u, dstdir, file, node):
	import producer
	global engine
	if os.environ.has_key('REAL_PRODUCER'):
		producer.SetDllCategoryPaths(os.environ['REAL_PRODUCER'])
	# ignore suggested extension and make our own
	file = os.path.splitext(file)[0] + '.ra'
	fullpath = os.path.join(dstdir, file)
	if engine is None:
		engine = producer.CreateRMBuildEngine()
	for pin in engine.GetPins():
		if pin.GetOutputMimeType() == producer.MIME_REALAUDIO:
			audiopin = pin
	engine.SetDoOutputMimeType(producer.MIME_REALAUDIO, 1)
	engine.SetDoOutputMimeType(producer.MIME_REALVIDEO, 0)
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
			ts.AddTargetAudience(producer.ENC_TARGET_28_MODEM)
	else:
		# we don't know nothin' about the node so use some defaults
		cp.SetTitle('')
		cp.SetAuthor('')
		cp.SetCopyright('')
		ts.AddTargetAudience(producer.ENC_TARGET_28_MODEM)
		ts.SetAudioContent(producer.ENC_AUDIO_CONTENT_VOICE)
	cp.SetPerfectPlay(1)
	cp.SetMobilePlay(0)
	cp.SetSelectiveRecord(0)
	cp.SetDoOutputServer(0)
	cp.SetDoOutputFile(1)
	cp.SetOutputFilename(fullpath)

	b = dshow.CreateGraphBuilder()
	b.RenderFile(u)
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
		return
	enumpins=aurenderer.EnumPins()
	pin=enumpins.Next()
	aulastpin=pin.ConnectedTo()
	b.RemoveFilter(aurenderer)
	try:
		f = dshow.CreateFilter('Audio Real Media Converter')
	except:
		print 'Audio real media converter filter is not installed'
		return
	b.AddFilter(f,'ARMC')
	b.Render(aulastpin)
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
		uk=audiopin.QueryInterfaceUnknown()
	except:
		print 'RMAInputPin QueryInterfaceUnknown failed'
		return
	rconv.SetInterface(uk,'IRMAInputPin')

	# PinProperties,MediaSample,PrepareToEncode,Encode, DoneEncoding
	# are all managed by our dshow filter

	mc = b.QueryIMediaControl()
	mc.Run()
	b.WaitForCompletion()
	mc.Stop()

inputfile='D:\\ufs\\mm\\cmif\\Build\\common\\testdoc\\testdata.aiff'
outputdir='d:\\ufs\\mm\\cmif\\win32\\DXMedia\\bin'
os.environ['REAL_PRODUCER']='c:\\Program Files\\RealSDK\\Producer\\BIN\\'

convertaudiofilex(inputfile,outputdir,'xxx.ra',None)