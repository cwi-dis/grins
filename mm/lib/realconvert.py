__version__ = "$Id$"

import os

engine = None
audiopin = None

def convertaudiofile(u, dstdir, file, node):
	import producer, MMAttrdefs, audio, audio.format
	global engine, audiopin
	if os.environ.has_key('REAL_PRODUCER'):
		producer.SetDllCategoryPaths(os.environ['REAL_PRODUCER'])
	# ignore suggested extension and make our own
	file = os.path.splitext(file)[0] + '.ra'
	fullpath = os.path.join(dstdir, file)
	if engine is None:
		engine = producer.CreateRMBuildEngine()
	if audiopin is None:
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
		ts.SetAudioContent(producer.ENC_AUDIO_CONTENT_VOICE)
		ts.AddTargetAudience(producer.ENC_TARGET_28_MODEM)
		ts.SetVideoQuality(producer.ENC_VIDEO_QUALITY_NORMAL)
	cp.SetPerfectPlay(1)
	cp.SetMobilePlay(0)
	cp.SetSelectiveRecord(0)
	cp.SetDoOutputServer(0)
	cp.SetDoOutputFile(1)
	cp.SetOutputFilename(fullpath)

	if u.headers.subtype == 'basic':
		atype = 'au'
	elif u.headers.subtype == 'x-aiff':
		atype = 'aiff'
	elif u.headers.subtype == 'x-wav':
		atype = 'wav'
	else:
		atype = 'au'		# XXX not correct
	rdr = audio.reader(u, [audio.format.linear_16_mono, audio.format.linear_16_stereo], [8000, 11025, 16000, 22050, 32000, 44100], filetype = atype)
	fmt = rdr.getformat()
	bytesperframe = fmt.getblocksize() / fmt.getfpb()
	nchan = fmt.getnchannels()
	frate = rdr.getframerate()

	pp = audiopin.GetPinProperties()
	pp.SetNumChannels(fmt.getnchannels())
	pp.SetSampleRate(frate)
	pp.SetSampleSize(fmt.getbps())

	engine.PrepareToEncode()

	ms = engine.CreateMediaSample()

	inputsize = audiopin.GetSuggestedInputSize()

	nframestoread = inputsize / bytesperframe
	flags = 0
	fread = 0
	while (flags & producer.MEDIA_SAMPLE_END_OF_STREAM) == 0:
		nframes = 0
		data = ''
		while nframes < nframestoread:
			d, n = rdr.readframes(nframestoread - nframes)
			if not d:
				flags = flags | producer.MEDIA_SAMPLE_END_OF_STREAM
				data = data + '\0' * (inputsize - len(data))
				break
			data = data + d
			nframes = nframes + n
		ms.SetBuffer(data, 1000 * fread / frate, flags) # XXX what is the unit for the timestamp?
		fread = fread + nframes
		audiopin.Encode(ms)

	engine.DoneEncoding()

	return file


def convertimagefile(u, srcurl, dstdir, file, node):
	import MMAttrdefs, urllib, sys
	# ignore suggested extension and make our own
	file = os.path.splitext(file)[0] + '.jpg'
	fullpath = os.path.join(dstdir, file)
	import imgjpeg, imgconvert
	u.close()
	f = urllib.urlretrieve(srcurl)[0]
	wt = imgjpeg.writer(fullpath)
	if sys.platform == 'win32':
		import __main__
		import imgformat
		from win32ig import win32ig
		img = __main__.toplevel._image_cache.get(f)
		if img is None:
			img = win32ig.load(f)
		width, height, depth = win32ig.size(img)
		data = win32ig.read(img)
		srcfmt = imgformat.bmprgbbe_noalign
	else:
		import img
		rdr = img.reader(wt.format_choices[0], f)
		width = rdr.width
		height = rdr.height
		data = rdr.read()
		srcfmt = rdr.format
	imgconvert.setquality(0)
	wt = imgconvert.stackwriter(srcfmt, wt)
	wt.width = width
	wt.height = height
	wt.restart_interval = 1
	if node is not None:
		quality = MMAttrdefs.getattr(node, 'project_quality')
		if quality:
			wt.quality = quality
	wt.write(data)
	return file

def converttextfile(u, dstdir, file, node):
	import MMAttrdefs
	from colors import colors
	# ignore suggested extension and make our own
	file = os.path.splitext(file)[0] + '.rt'
	fullpath = os.path.join(dstdir, file)
	data = u.read()
	f = open(fullpath, 'w')
	f.write('<window')
	if node is not None:
		dur = MMAttrdefs.getattr(node, 'duration')
		if dur:
			f.write(' duration="%g"' % dur)
		ch = node.GetChannel()
		color = ch.get('bgcolor', (0,0,0))
		if color != (255,255,255):
			for name, val in colors.items():
				if color == val:
					color = name
					break
			else:
				color = '#%02x%02x%02x' % color
			f.write(' bgcolor="%s"' % color)
	f.write('>\n')
	f.write(data)
	f.write('</window>\n')
	f.close()
	return file


def convertvideofile(u, srcurl, dstdir, file, node):
	import producer, MMAttrdefs, urllib
	global engine
	u.close()
	fin = urllib.urlretrieve(srcurl)[0]
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
	ts.RemoveAllTargetAudiences()
	if node is not None:
		cp.SetTitle(MMAttrdefs.getattr(node, 'title'))
		cp.SetAuthor(MMAttrdefs.getattr(node, 'author'))
		cp.SetCopyright(MMAttrdefs.getattr(node, 'copyright'))
		ts.SetVideoQuality(MMAttrdefs.getattr(node, 'project_videotype'))
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
		return
	b = dshow.CreateGraphBuilder()
	b.RenderFile(fin)
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

	# find default audio renderer filter
	try:
		aurenderer=b.FindFilterByName('Default DirectSound Device')
	except:
		aurenderer=None
	if not aurenderer:
		try:
			aurenderer=b.FindFilterByName('Default WaveOut Device')
		except:
			aurenderer=None
	# remove audio renderer filter for now
	# should be replaced by our audio real converter filter
	if aurenderer:
		b.RemoveFilter(aurenderer)

	# PinProperties,MediaSample,PrepareToEncode,Encode, DoneEncoding
	# are all managed by our dshow filter

	# do encoding
	mc = b.QueryIMediaControl()
	mc.Run()
	b.WaitForCompletion()
	mc.Stop()
	del b
	return file
