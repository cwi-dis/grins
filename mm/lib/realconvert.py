__version__ = "$Id$"

import os, sys
import MMurl
import urlparse

def identicalfiles(srcurl, fullpath):
	if os.path.exists(fullpath):
		scheme, netloc, url, params, query, fragment = urlparse.urlparse(srcurl)
		if (not scheme or scheme == 'file') and (not netloc or netloc == 'localhost'):
			srcurl = MMurl.canonURL(srcurl)
			dsturl = MMurl.canonURL(MMurl.pathname2url(fullpath))
			if srcurl == dsturl:
				return 1
	return 0

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

def convertaudiofile(u, srcurl, dstdir, file, node, progress = None):
	import MMAttrdefs, audio, audio.format
	global engine, audiopin
	# ignore suggested extension and make our own
	file = os.path.splitext(file)[0] + '.ra'
	fullpath = os.path.join(dstdir, file)
	if identicalfiles(srcurl, fullpath):
		# src and dst files are the same, don't do anything
		u.close()
		if __debug__:
			print 'src and dst files are identical',fullpath
		return file
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
	# ignore suggested extension and make our own
	file = os.path.splitext(file)[0] + '.jpg'
	fullpath = os.path.join(dstdir, file)
	if identicalfiles(srcurl, fullpath):
		# src and dst files are the same, don't do anything
		u.close()
		if __debug__:
			print 'src and dst files are identical',fullpath
		return file
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

def converttextfile(u, srcurl, dstdir, file, node):
	import MMAttrdefs, windowinterface
	import colors
	# ignore suggested extension and make our own
	file = os.path.splitext(file)[0] + '.rt'
	fullpath = os.path.join(dstdir, file)
	if identicalfiles(srcurl, fullpath):
		# src and dst files are the same, don't do anything
		u.close()
		if __debug__:
			print 'src and dst files are identical',fullpath
		return file
	data = u.read()
	u.close()
	f = open(fullpath, 'w')
	f.write('<window')
	if node is not None:
		dur = MMAttrdefs.getattr(node, 'duration')
		if dur:
			f.write(' duration="%g"' % dur)
		ch = node.GetChannel()
		color = ch.get('bgcolor')
		if color is not None:
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

if sys.platform == 'win32':
	_org_convertaudiofile = convertaudiofile
def _win_convertaudiofile(u, srcurl, dstdir, file, node, progress = None):
	if u.headers.subtype in ('basic', 'x-aiff', 'x-wav'):
		return _org_convertaudiofile(u, srcurl, dstdir, file, node, progress)
	u.close()

	try:
		import win32dxm
		reader = win32dxm.MediaReader(srcurl)
	except:
		return

	import MMAttrdefs
	global engine, audiopin

	try:
		# ignore suggested extension and make our own
		file = os.path.splitext(file)[0] + '.ra'
		fullpath = os.path.join(dstdir, file)
		if identicalfiles(srcurl, fullpath):
			# src and dst files are the same, don't do anything
			u.close()
			if __debug__:
				print 'src and dst files are identical',fullpath
			return file
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
		cp.SetOutputFilename(fullpath)
	
		fmt = reader.GetAudioFormat()
		pp = audiopin.GetPinProperties()
		pp.SetNumChannels(fmt.getnchannels())
		pp.SetSampleRate(fmt.getsamplespersec())
		pp.SetSampleSize(fmt.getbitspersample())

		engine.PrepareToEncode()
		ms = engine.CreateMediaSample()

		try:
			nbytes = audiopin.GetSuggestedInputSize()
			nbps = fmt.getbitspersample() / 8
			inputsize_frames = nbytes / nbps

			done = 0
			flags = 0
			time, data = reader.ReadAudio(inputsize_frames)
			if not data:
				done = 1
			if progress:
				dur = reader.GetDuration()
			while not done:
				data_list = reader.ReadAudioSamples(inputsize_frames)
				for i in range(len(data_list)):
					next_time, next_data = data_list[i]
					if not next_data:
						done = 1
						flags = producer.MEDIA_SAMPLE_END_OF_STREAM
					ms.SetBuffer(data, time, flags)
					audiopin.Encode(ms)
					time = next_time
					data = next_data
				if progress:
					now = reader.GetTime()
					apply(progress[0], progress[1] + (now, dur))
		finally:
			engine.DoneEncoding()
		return file
	except producer.error, arg:
		import windowinterface
		windowinterface.showmessage("RealEncoder error: %s"%(arg,))

def _win_convertvideofile(u, srcurl, dstdir, file, node, progress = None):
	if u.headers.subtype.find('quicktime') >=0:
		return _other_convertvideofile(u, srcurl, dstdir, file, node, progress)
	u.close()

	global engine
	import MMAttrdefs
	try:
		import win32dxm
		reader = win32dxm.MediaReader(srcurl)
	except:
		return
	try:
		# ignore suggested extension and make our own
		file = os.path.splitext(file)[0] + '.rm'
		fullpath = os.path.join(dstdir, file)
		if identicalfiles(srcurl, fullpath):
			# src and dst files are the same, don't do anything
			u.close()
			if __debug__:
				print 'src and dst files are identical',fullpath
			return file
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
			if video_fmt.getformat() == imgformat.bmprgble_noalign:
				prod_format = producer.ENC_VIDEO_FORMAT_RGB24
			else:
				raise 'Unsupported video source format', video_fmt.getformat()
			w, h = video_fmt.getsize()
			video_props.SetVideoSize(w, h)
			video_props.SetVideoFormat(prod_format)
			video_props.SetCroppingEnabled(0)
			video_sample = engine.CreateMediaSample()

		if has_audio:
			audio_fmt = reader.GetAudioFormat()
			audio_props = audiopin.GetPinProperties()
			audio_props.SetSampleRate(audio_fmt.getsamplespersec())
			audio_props.SetNumChannels(audio_fmt.getnchannels())
			audio_props.SetSampleSize(audio_fmt.getbitspersample())
			audio_sample = engine.CreateMediaSample()
			
		audio_failed = 0
		engine.PrepareToEncode()
		# Put the rest inside a try/finally, so a KeyboardInterrupt will cleanup
		# the engine.
		try:
			if has_audio:
				nbytes = audiopin.GetSuggestedInputSize()
				nbps = audio_fmt.getbitspersample() / 8
				audio_inputsize_frames = nbytes / nbps

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
				dur = reader.GetDuration()
			while not audio_done or not video_done:
				if not audio_done:
					audio_data_list = reader.ReadAudioSamples(audio_inputsize_frames)
					for i in range(len(audio_data_list)):
						next_audio_time, next_audio_data = audio_data_list[i]
						if not next_audio_data:
							audio_done = 1
							audio_flags = producer.MEDIA_SAMPLE_END_OF_STREAM
						audio_sample.SetBuffer(audio_data, audio_time, audio_flags)
						try:
							audiopin.Encode(audio_sample)
						except producer.error, arg:
							print 'Audio sample:', arg, audio_time, audio_flags
							audio_failed = 1
							audio_done = 1
						audio_time = next_audio_time
						audio_data = next_audio_data
				if not video_done:
					video_data_list = reader.ReadVideoSamples()
					for i in range(len(video_data_list)):
						next_video_time, next_video_data = video_data_list[i]
						if not next_video_data:
							video_done = 1
							video_flags = producer.MEDIA_SAMPLE_END_OF_STREAM
						video_sample.SetBuffer(video_data, video_time, video_flags)
						videopin.Encode(video_sample)
						video_time = next_video_time
						video_data = next_video_data
				if progress:
					now = reader.GetTime()
					apply(progress[0], progress[1] + (now, dur))
		finally:
			engine.DoneEncoding()
		
		if audio_failed:
			import windowinterface
			windowinterface.showmessage('Converted video only: could not handle audio')
		return file
	except producer.error, arg:
		import windowinterface
		windowinterface.showmessage("RealEncoder error: %s"%(arg,))

def _other_convertvideofile(u, srcurl, dstdir, file, node, progress = None):
	global engine
	import MMAttrdefs
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
		if identicalfiles(srcurl, fullpath):
			# src and dst files are the same, don't do anything
			u.close()
			if __debug__:
				print 'src and dst files are identical',fullpath
			return file
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
			elif video_fmt.getformat() == imgformat.bmprgble_noalign:
				prod_format = producer.ENC_VIDEO_FORMAT_RGB24
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
	convertaudiofile = _win_convertaudiofile
else:
	convertvideofile = _other_convertvideofile

if producer is None:
	# dummies if we can't import producer
	def convertaudiofile(u, srcurl, dstdir, file, node, progress = None):
		u.close()
		return None
	def convertvideofile(u, srcurl, dstdir, file, node, progress = None):
		u.close()
		return None
