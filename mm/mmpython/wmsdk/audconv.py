# convert audio to real 
# use in lib/realconvert.py context
# valid for win32
# use when realconvert.convertaudiofile fails to parse audio

def convertaudiofile(u, srcurl, dstdir, file, node, progress = None):
	import producer, MMAttrdefs, MMurl
	global engine
	u.close()
	fin = MMurl.urlretrieve(srcurl)[0]
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
	ts.RemoveAllTargetAudiences()
	if node is not None:
		cp.SetTitle(MMAttrdefs.getattr(node, 'title'))
		cp.SetAuthor(MMAttrdefs.getattr(node, 'author'))
		cp.SetCopyright(MMAttrdefs.getattr(node, 'copyright'))
		ts.SetAudioContent(MMAttrdefs.getattr(node, 'project_audiotype'))
		target = MMAttrdefs.getattr(node, 'project_targets')
		for i in range(6):
			if (1 << i) & target:
				ts.AddTargetAudience(i)
		if not target:
			ts.AddTargetAudience(producer.ENC_TARGET_28_MODEM)
	else:
		# we don't know nothin' about the node so use some defaults
		cp.SetTitle('')
		cp.SetAuthor('')
		cp.SetCopyright('')
		ts.SetAudioContent(producer.ENC_AUDIO_CONTENT_VOICE)
		ts.AddTargetAudience(producer.ENC_TARGET_28_MODEM)
		ts.SetVideoQuality(producer.ENC_VIDEO_QUALITY_NORMAL)
	cp.SetPerfectPlay(1)
	cp.SetMobilePlay(0)
	cp.SetSelectiveRecord(0)
	cp.SetDoOutputServer(0)
	cp.SetDoOutputFile(1)
	cp.SetOutputFilename(fullpath)

	# prepare filter graph
	try:
		import dshow
	except ImportError:
		return file
	b = dshow.CreateGraphBuilder()
	b.RenderFile(fin)

	try:
		renderer=b.FindFilterByName('Default DirectSound Device')
	except:
		try:
			renderer=b.FindFilterByName('Default WaveOut Device')
		except:
			return file

	# replace audio renderer with aud2rm filter
	enumpins=renderer.EnumPins()
	pin=enumpins.Next()
	lastpin=pin.ConnectedTo()
	b.RemoveFilter(renderer)
	try:
		af = dshow.CreateFilter('Audio Real Media Converter')
	except:
		return file

	b.AddFilter(af,'ARMC')
	b.Render(lastpin)

	try:
		rconv=af.QueryIRealConverter()
	except:
		print 'Filter does not support interface IRealConverter'
		return file
	try:
		ukeng=engine.QueryInterfaceUnknown()
	except:
		print 'RMABuildEngine QueryInterfaceUnknown failed'
		return file
	rconv.SetInterface(ukeng,'IRMABuildEngine')
	try:
		uk=audiopin.QueryInterfaceUnknown()
	except:
		print 'RMAInputPin QueryInterfaceUnknown failed'
		return file
	rconv.SetInterface(uk,'IRMAInputPin')

	# PinProperties,MediaSample,PrepareToEncode,Encode, DoneEncoding
	# are all managed by our dshow filter

	# do encoding
	mc = b.QueryIMediaControl()
	mp = b.QueryIMediaPosition()
	dur = int(1000*mp.GetDuration()+0.5) # dur in msec
	mc.Run()
	
	import sys
	if sys.platform=='win32':
		# remove messages in queue
		# dispatch only paint message
		import win32ui
		import windowinterface
		win32ui.PumpWaitingMessages(0,0)
		windowinterface.setwaiting()
		while b.WaitForCompletion(0)==0:
			now=int(1000*mp.GetCurrentPosition()+0.5)
			if progress:
				apply(progress[0], progress[1] + (now, dur))
			win32ui.PumpWaitingMessages(0,0)
			windowinterface.setwaiting()
		mc.Stop()
		win32ui.PumpWaitingMessages(0,0)
		windowinterface.setready()
	else:
		b.WaitForCompletion()
		mc.Stop()
	
	del b
				
	return file

