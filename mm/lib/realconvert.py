__version__ = "$Id$"

import os, sys

try:
	import producer
except ImportError:
	producer = None
	if sys.platform == 'win32' or sys.platform == 'mac':
		# fatal error on Mac and Windows
		raise ImportError('no RealProducer SDK')
else:
	import cmif
	if sys.platform == 'mac':
		# Newer SDK version with different paths
		dllpath = cmif.findfile('enceng60.dll')
		dir = os.path.split(dllpath)[0]
		if not dir:
			dir = os.getcwd()
		producer.SetDllAccessPath(
				'DT_Plugins=%s\000' % dir +
				'DT_Codecs=%s\000' % dir +
				'DT_EncSDK=%s\000' % dir +
				'DT_Common=%s\000' % dir)
	else:
		dir = cmif.findfile('Producer-SDK')
		if os.path.exists(dir):
			producer.SetDllAccessPath(
				'DT_Plugins=%s\000' % os.path.join(dir, 'Plugins') +
				'DT_Codecs=%s\000' % os.path.join(dir, 'Codecs') +
				'DT_EncSDK=%s\000' % os.path.join(dir, 'Tools') +
				'DT_Common=%s\000' % os.path.join(dir, 'Common'))
		else:
			raise ImportError('no RealMedia codecs')

engine = None
audiopin = None

def convertaudiofile(u, dstdir, file, node, progress = None):
	import MMAttrdefs, audio, audio.format
	global engine, audiopin
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
	cp = engine.GetClipProperties()
	ts = engine.GetTargetSettings()
	ts.RemoveAllTargetAudiences()
	if node is not None:
		cp.SetTitle(MMAttrdefs.getattr(node, 'title'))
		cp.SetAuthor(MMAttrdefs.getattr(node, 'author'))
		cp.SetCopyright(MMAttrdefs.getattr(node, 'copyright'))
		cp.SetPerfectPlay(MMAttrdefs.getattr(node, 'project_perfect'))
		cp.SetMobilePlay(MMAttrdefs.getattr(node, 'project_mobile'))
		ts.SetAudioContent(MMAttrdefs.getattr(node, 'project_audiotype'))
		target = MMAttrdefs.getattr(node, 'project_targets')
		ntargets = 0
		for i in range(6):
			if (1 << i) & target:
				ts.AddTargetAudience(i)
				ntargets = ntargets + 1
		if ntargets == 0:
			ts.AddTargetAudience(producer.ENC_TARGET_28_MODEM)
			ntargets = ntargets + 1
	else:
		# we don't know nothin' about the node so use some defaults
		cp.SetTitle('')
		cp.SetAuthor('')
		cp.SetCopyright('')
		cp.SetPerfectPlay(1)
		cp.SetMobilePlay(0)
		ts.SetAudioContent(producer.ENC_AUDIO_CONTENT_VOICE)
		ts.AddTargetAudience(producer.ENC_TARGET_28_MODEM)
		ts.SetVideoQuality(producer.ENC_VIDEO_QUALITY_NORMAL)
		ntargets = 1
	engine.SetDoMultiRateEncoding(ntargets != 1)
	cp.SetSelectiveRecord(0)
	cp.SetDoOutputServer(0)
	cp.SetDoOutputFile(1)

	if u.headers.subtype == 'basic':
		atype = 'au'
	elif u.headers.subtype == 'x-aiff':
		atype = 'aiff'
	elif u.headers.subtype == 'x-wav':
		atype = 'wav'
	elif u.headers.subtype == 'mpeg':
		u.close()
		return None
	else:
		atype = 'au'		# XXX not correct
	try:
		rdr = audio.reader(u, [audio.format.linear_16_mono, audio.format.linear_16_stereo], [8000, 11025, 16000, 22050, 32000, 44100], filetype = atype)
		fmt = rdr.getformat()
		bytesperframe = fmt.getblocksize() / fmt.getfpb()
		nchan = fmt.getnchannels()
		frate = rdr.getframerate()
		totframes = rdr.getnframes()
	except (audio.Error, IOError, EOFError), msg:
		print 'error in sound file:', msg
		return

	cp.SetOutputFilename(fullpath)
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
		if progress:
			apply(progress[0], progress[1] + (fread, totframes))
		while nframes < nframestoread:
			try:
				d, n = rdr.readframes(nframestoread - nframes)
			except (audio.Error, IOError, EOFError), msg:
				print 'error in sound file:', msg
				d = ''
				n = 0
				file = None
			if not d:
				flags = flags | producer.MEDIA_SAMPLE_END_OF_STREAM
				data = data + '\0' * (inputsize - len(data))
				break
			data = data + d
			nframes = nframes + n
		ms.SetBuffer(data, int(1000.0 * fread / frate), flags) # XXX what is the unit for the timestamp?
		fread = fread + nframes
		audiopin.Encode(ms)

	engine.DoneEncoding()
	u.close()

	if not file:
		try:
			os.unlink(fullpath)
		except:
			pass

	return file


def convertimagefile(u, srcurl, dstdir, file, node):
	import MMurl
	# ignore suggested extension and make our own
	file = os.path.splitext(file)[0] + '.jpg'
	fullpath = os.path.join(dstdir, file)
	import imgjpeg, imgconvert
	if u is not None:
		u.close()
	f, hdr = MMurl.urlretrieve(srcurl)
	wt = imgjpeg.writer(fullpath)
	wt.restart_interval = 1
	if node is not None:
		if type(node) == type({}):
			quality = node.get('project_quality')
		else:
			quality = node.GetAttrDef('project_quality', None)
		if quality:
			wt.quality = quality
	if hdr.subtype == 'jpeg':
		# special-case code for JPEG images so that we don't loose info
		rdr = imgjpeg.reader(f)
		wt.copy(rdr)
		if os.name == 'mac':
			import macfs
			import macostools
			fss = macfs.FSSpec(fullpath)
			fss.SetCreatorType('ogle', 'JPEG')
			macostools.touched(fss)
		return file
	if sys.platform == 'win32':
		import __main__
		import imgformat
		from win32ig import win32ig
		doc = __main__.toplevel.getActiveDocFrame()
		img = __main__.toplevel._image_handle(f, doc)
		if __main__.toplevel._image_depth(f, doc) != 24:
			win32ig.color_promote(img, 3) # IG_PROMOTE_TO_24
		width, height = __main__.toplevel._image_size(f, doc)
		data = win32ig.read(img)
		srcfmt = imgformat.bmprgble_noalign
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
	wt.write(data)
	if os.name == 'mac':
		import macfs
		import macostools
		fss = macfs.FSSpec(fullpath)
		fss.SetCreatorType('ogle', 'JPEG')
		macostools.touched(fss)
	return file

def converttextfile(u, dstdir, file, node):
	import MMAttrdefs, windowinterface
	import colors
	# ignore suggested extension and make our own
	file = os.path.splitext(file)[0] + '.rt'
	fullpath = os.path.join(dstdir, file)
	data = u.read()
	u.close()
	f = open(fullpath, 'w')
	f.write('<window')
	if node is not None:
		dur = MMAttrdefs.getattr(node, 'duration')
		if dur:
			f.write(' duration="%g"' % dur)
		ch = node.GetChannel()
		color = ch.get('bgcolor', (0,0,0))
		if color != (255,255,255):
			if colors.rcolors.has_key(color):
				color = colors.rcolors[color]
			else:
				color = '#%02x%02x%02x' % color
			f.write(' bgcolor="%s"' % color)
		geom = ch.get('base_winoff')
		units = ch.get('units', windowinterface.UNIT_SCREEN)
		if geom and units == windowinterface.UNIT_PXL:
			f.write(' width="%d" height="%d"' % (geom[2], geom[3]))
	f.write('>\n')
	f.write(data)
	f.write('</window>\n')
	f.close()
	if os.name == 'mac':
		import macfs
		import macostools
		fss = macfs.FSSpec(fullpath)
		fss.SetCreatorType('PNst', 'PNRA')
		macostools.touched(fss)
	return file


def _win_convertvideofile(u, srcurl, dstdir, file, node, progress = None):
	global engine
	import MMAttrdefs, MMurl
	u.close()
	try:
		import dshow
	except ImportError:
		return
	fin = MMurl.urlretrieve(srcurl)[0]
	# ignore suggested extension and make our own
	file = os.path.splitext(file)[0] + '.rm'
	fullpath = os.path.join(dstdir, file)
	if engine is None:
		engine = producer.CreateRMBuildEngine()
	for pin in engine.GetPins():
		if pin.GetOutputMimeType() == producer.MIME_REALVIDEO:
			videopin = pin
		elif pin.GetOutputMimeType() == producer.MIME_REALAUDIO:
			audiopin = pin
	engine.SetDoOutputMimeType(producer.MIME_REALAUDIO, 0)
	engine.SetDoOutputMimeType(producer.MIME_REALVIDEO, 1)
	engine.SetDoOutputMimeType(producer.MIME_REALEVENT, 0)
	engine.SetDoOutputMimeType(producer.MIME_REALIMAGEMAP, 0)
	engine.SetDoOutputMimeType(producer.MIME_REALPIX, 0)
	engine.SetRealTimeEncoding(0)
	cp = engine.GetClipProperties()
	ts = engine.GetTargetSettings()
	ts.RemoveAllTargetAudiences()
	if node is not None:
		cp.SetTitle(MMAttrdefs.getattr(node, 'title'))
		cp.SetAuthor(MMAttrdefs.getattr(node, 'author'))
		cp.SetCopyright(MMAttrdefs.getattr(node, 'copyright'))
		cp.SetPerfectPlay(MMAttrdefs.getattr(node, 'project_perfect'))
		cp.SetMobilePlay(MMAttrdefs.getattr(node, 'project_mobile'))
		ts.SetVideoQuality(MMAttrdefs.getattr(node, 'project_videotype'))
		ts.SetAudioContent(MMAttrdefs.getattr(node, 'project_audiotype'))
		target = MMAttrdefs.getattr(node, 'project_targets')
		ntargets = 0
		for i in range(6):
			if (1 << i) & target:
				ts.AddTargetAudience(i)
				ntargets = ntargets + 1
		if ntargets == 0:
			ts.AddTargetAudience(producer.ENC_TARGET_28_MODEM)
			ntargets = ntargets + 1
	else:
		# we don't know nothin' about the node so use some defaults
		cp.SetTitle('')
		cp.SetAuthor('')
		cp.SetCopyright('')
		cp.SetPerfectPlay(1)
		cp.SetMobilePlay(0)
		ts.AddTargetAudience(producer.ENC_TARGET_28_MODEM)
		ntargets = 1
		ts.SetVideoQuality(producer.ENC_VIDEO_QUALITY_NORMAL)
	engine.SetDoMultiRateEncoding(ntargets != 1)
	cp.SetSelectiveRecord(0)
	cp.SetDoOutputServer(0)
	cp.SetDoOutputFile(1)
	cp.SetOutputFilename(fullpath)

	# prepare filter graph
	b = dshow.CreateGraphBuilder()
	try:
		b.RenderFile(fin)
	except dshow.error, arg:
		del b
		return

	renderer=b.FindFilterByName('Video Renderer')
	enumpins=renderer.EnumPins()
	pin=enumpins.Next()
	lastpin=pin.ConnectedTo()
	b.RemoveFilter(renderer)
	try:
		vf = dshow.CreateFilter('Video Real Media Converter')
	except:
		print 'Video real media converter filter is not installed'
		return file
	b.AddFilter(vf,'VRMC')
	enumpins=vf.EnumPins()
	pin=enumpins.Next()
	b.Connect(lastpin,pin)
	#b.Render(lastpin)

	try:
		rconv=vf.QueryIRealConverter()
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
		uk=videopin.QueryInterfaceUnknown()
	except:
		print 'RMAInputPin QueryInterfaceUnknown failed'
		return file
	rconv.SetInterface(uk,'IRMAInputPin')

	# we are ready for video, check for audio
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
	# replace audio renderer with aud2rm filter
	if aurenderer:
		enumpins=aurenderer.EnumPins()
		pin=enumpins.Next()
		lastpin=pin.ConnectedTo()
		b.RemoveFilter(aurenderer)
		try:
			af = dshow.CreateFilter('Audio Real Media Converter')
		except:
			aurenderer=None
		else:
			b.AddFilter(af,'ARMC')
			enumpins=af.EnumPins()
			pin=enumpins.Next()
			b.Connect(lastpin,pin)
			#b.Render(lastpin)

	# set engine and audio pin
	if aurenderer:
		try:
			arconv=af.QueryIRealConverter()
		except:
			aurenderer=None
		else:
			arconv.SetInterface(ukeng,'IRMABuildEngine')
	if aurenderer:
		try:
			uk=audiopin.QueryInterfaceUnknown()
		except:
			aurenderer=None
		else:
			arconv.SetInterface(uk,'IRMAInputPin')

	# enable audio
	if aurenderer:
		engine.SetDoOutputMimeType(producer.MIME_REALAUDIO, 1)
		ts.SetAudioContent(producer.ENC_AUDIO_CONTENT_VOICE)

	# PinProperties,MediaSample,PrepareToEncode,Encode, DoneEncoding
	# are all managed by our dshow filter

	# do encoding
	mc = b.QueryIMediaControl()
	mp = b.QueryIMediaPosition()
	dur = int(1000*mp.GetDuration()+0.5) # dur in msec
	mc.Run()
	
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

def _other_convertvideofile(u, srcurl, dstdir, file, node, progress = None):
	global engine
	import MMAttrdefs, MMurl
	u.close()
	try:
		import videoreader
	except ImportError:
		return
	try:
		reader = videoreader.reader(srcurl)
		if not reader:
			return
		# ignore suggested extension and make our own
		file = os.path.splitext(file)[0] + '.rm'
		fullpath = os.path.join(dstdir, file)
		if engine is None:
			engine = producer.CreateRMBuildEngine()
		videopin = None
		audiopin = None
		has_video = reader.HasVideo()
		has_audio = reader.HasAudio()
		if not has_video:
			import windowinterface
			windowinterface.showmessage("Warning: no video track found in %s"%srcurl)
		for pin in engine.GetPins():
			if pin.GetOutputMimeType() == producer.MIME_REALVIDEO:
				videopin = pin
			elif pin.GetOutputMimeType() == producer.MIME_REALAUDIO:
				audiopin = pin
		warning = ''
		if has_video and not videopin: 
			has_video = 0
			warning = 'Video conversion support appears to be missing!\n'
		if has_audio and not audiopin: 
			warning = 'Audio conversion support appears to be missing!\n'
			has_audio = 0
		if warning:
			import windowinterface
			windowinterface.showmessage('Warning:\n'+warning)
		if not (has_audio or has_video):
			return
		engine.SetDoOutputMimeType(producer.MIME_REALAUDIO, has_audio)
		engine.SetDoOutputMimeType(producer.MIME_REALVIDEO, has_video)
		engine.SetDoOutputMimeType(producer.MIME_REALEVENT, 0)
		engine.SetDoOutputMimeType(producer.MIME_REALIMAGEMAP, 0)
		engine.SetDoOutputMimeType(producer.MIME_REALPIX, 0)
		engine.SetRealTimeEncoding(0)
		cp = engine.GetClipProperties()
		ts = engine.GetTargetSettings()
		ts.RemoveAllTargetAudiences()
		if node is not None:
			cp.SetTitle(MMAttrdefs.getattr(node, 'title'))
			cp.SetAuthor(MMAttrdefs.getattr(node, 'author'))
			cp.SetCopyright(MMAttrdefs.getattr(node, 'copyright'))
			cp.SetPerfectPlay(MMAttrdefs.getattr(node, 'project_perfect'))
			cp.SetMobilePlay(MMAttrdefs.getattr(node, 'project_mobile'))
			if has_video:
				ts.SetVideoQuality(MMAttrdefs.getattr(node, 'project_videotype'))
			if has_audio:
				ts.SetAudioContent(MMAttrdefs.getattr(node, 'project_audiotype'))
			target = MMAttrdefs.getattr(node, 'project_targets')
			ntargets = 0
			for i in range(6):
				if (1 << i) & target:
					ts.AddTargetAudience(i)
					ntargets = ntargets + 1
			if ntargets == 0:
				ts.AddTargetAudience(producer.ENC_TARGET_28_MODEM)
				ntargets = ntargets + 1
		else:
			# we don't know nothin' about the node so use some defaults
			cp.SetTitle('')
			cp.SetAuthor('')
			cp.SetCopyright('')
			cp.SetPerfectPlay(1)
			cp.SetMobilePlay(0)
			ts.AddTargetAudience(producer.ENC_TARGET_28_MODEM)
			ntargets = 1
			if has_video:
				ts.SetVideoQuality(producer.ENC_VIDEO_QUALITY_NORMAL)
			if has_audio:
				ts.SetAudioContent(producer.ENC_AUDIO_CONTENT_VOICE)
		engine.SetDoMultiRateEncoding(ntargets != 1)
		cp.SetSelectiveRecord(0)
		cp.SetDoOutputServer(0)
		cp.SetDoOutputFile(1)
		cp.SetOutputFilename(fullpath)
		
		if has_video:
			import imgformat
			video_props = videopin.GetPinProperties()
			video_props.SetFrameRate(reader.GetVideoFrameRate())
			video_fmt = reader.GetVideoFormat()
			# XXXX To be done better
			if video_fmt.getformat() == imgformat.macrgb:
				prod_format = producer.ENC_VIDEO_FORMAT_BGR32_NONINVERTED
			else:
				raise 'Unsupported video source format', video_fmt.getformat()
			w, h = video_fmt.getsize()
			video_props.SetVideoSize(w, h)
			video_props.SetVideoFormat(prod_format)
			video_props.SetCroppingEnabled(0)
	
			video_sample = engine.CreateMediaSample()
			
			
		if has_audio:
			audio_fmt = reader.GetAudioFormat()
			encoding = audio_fmt.getencoding()
			if not encoding in ('linear-excess', 'linear-signed'):
				has_audio = 0
				engine.SetDoOutputMimeType(producer.MIME_REALAUDIO, 0)
				import windowinterface
				windowinterface.showmessage('Converting video only: cannot handle %s audio\n(linear audio only)'%encoding)
		if has_audio:
			audio_props = audiopin.GetPinProperties()
			audio_props.SetSampleRate(reader.GetAudioFrameRate())
			audio_props.SetNumChannels(audio_fmt.getnchannels())
			audio_props.SetSampleSize(audio_fmt.getbps())
	
			audio_sample = engine.CreateMediaSample()
			
		engine.PrepareToEncode()
		# Put the rest inside a try/finally, so a KeyboardInterrupt will cleanup
		# the engine.
		try:
			if has_audio:
				nbytes = audiopin.GetSuggestedInputSize()
				nbpf = audio_fmt.getblocksize() / audio_fmt.getfpb()
				audio_inputsize_frames = nbytes / nbpf
				
	
			audio_done = video_done = 0
			audio_flags = video_flags = 0
			audio_time = video_time = 0
			audio_data = video_data = None
			if has_audio:
				audio_time, audio_data = reader.ReadAudio(audio_inputsize_frames)
			if not audio_data:
				audio_done = 1
			if has_video:
				video_time, video_data = reader.ReadVideo()
			if not video_data:
				video_done = 1
			if progress:
				dur = max(reader.GetVideoDuration(), reader.GetAudioDuration())
				now = 0
			while not audio_done or not video_done:
				if not audio_done:
					next_audio_time, next_audio_data = reader.ReadAudio(audio_inputsize_frames)
					if not next_audio_data:
						audio_done = 1
						audio_flags = producer.MEDIA_SAMPLE_END_OF_STREAM
					audio_sample.SetBuffer(audio_data, audio_time, audio_flags)
					audiopin.Encode(audio_sample)
					audio_time = next_audio_time
					audio_data = next_audio_data
					if audio_time > now:
						now = audio_time
				if not video_done:
					next_video_time, next_video_data = reader.ReadVideo()
					if not next_video_data:
						video_done = 1
						video_flags = producer.MEDIA_SAMPLE_END_OF_STREAM
					video_sample.SetBuffer(video_data, video_time, video_flags)
					videopin.Encode(video_sample)
					video_time = next_video_time
					video_data = next_video_data
					if video_time > now:
						now = video_time
				if progress:
					apply(progress[0], progress[1] + (now, dur))
		finally:
			engine.DoneEncoding()
		if os.name == 'mac':
			import macfs
			import macostools
			fss = macfs.FSSpec(fullpath)
			fss.SetCreatorType('PNst', 'PNRA')
			macostools.touched(fss)
		return file
	except producer.error, arg:
		import windowinterface
		windowinterface.showmessage("RealEncoder error: %s"%(arg,))

if sys.platform == 'win32':
	convertvideofile = _win_convertvideofile
else:
	convertvideofile = _other_convertvideofile

if producer is None:
	# dummies if we can't import producer
	def convertaudiofile(u, dstdir, file, node, progress = None):
		u.close()
		return None
	def convertvideofile(u, srcurl, dstdir, file, node, progress = None):
		u.close()
		return None
