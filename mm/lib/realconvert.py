__version__ = "$Id$"

import os

engine = None
audiopin = None

def convertaudiofile(u, dstdir, file, node, isaudio = 1):
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
	if node is not None:
		cp.SetTitle(MMAttrdefs.getattr(node, 'title'))
		cp.SetAuthor(MMAttrdefs.getattr(node, 'author'))
		cp.SetCopyright(MMAttrdefs.getattr(node, 'copyright'))
		if isaudio:
			ts.SetAudioContent(MMAttrdefs.getattr(node, 'project_audiotype'))
		else:
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
	import MMAttrdefs, urllib
	from win32ig import win32ig
	# ignore suggested extension and make our own
	file = os.path.splitext(file)[0] + '.jpg'
	fullpath = os.path.join(dstdir, file)
	import imgformat, imgjpeg, imgconvert
	u.close()
	import __main__
	f = urllib.urlretrieve(srcurl)[0]
	img = __main__.toplevel._image_cache.get(f)
	if img is None:
		img = win32ig.load(f)
	width, height, depth = win32ig.size(img)
	data = win32ig.read(img)
	wt = imgjpeg.writer(fullpath)
	imgconvert.setquality(0)
	wt = imgconvert.stackwriter(imgformat.bmprgbbe_noalign, wt)
	wt.width = width
	wt.height = height
	wt.restart_interval = 1
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
