__version__ = "$Id$"

import Channel
import MMAttrdefs
import MMurl

# for timer support
import windowinterface

# audio modules
import audio, audio.format

# wince playback module
import winmm

error = 'SoundChannel.error'

class SoundChannel(Channel.ChannelAsync):
	node_attrs = Channel.ChannelAsync.node_attrs + ['duration']

	def __init__(self, name, attrdict, scheduler, ui):
		Channel.ChannelAsync.__init__(self, name, attrdict, scheduler, ui)
		self.__audio_player = None

	def do_hide(self):
		if self.__audio_player:
			self.__audio_player.stop()
			self.__audio_player = None
		Channel.ChannelAsync.do_hide(self)

	def do_play(self, node, curtime):
		Channel.ChannelAsync.do_play(self, node, curtime)

		if node.type != 'ext':
			self.errormsg(node, 'Node must be external.')
			self.playdone(0, curtime)
			return

		f = self.getfileurl(node)
		if not f:
			self.errormsg(node, 'No URL set on node.')
			self.playdone(0, curtime)
		
		try:
			self.__audio_player = AudioPlayer(f)
		except (error, winmm.error), msg:
			print msg
			self.__audio_player = None
			self.playdone(0, curtime)
			return
		self.__audio_player.play()

	def setpaused(self, paused, timestamp):
		Channel.ChannelAsync.setpaused(self, paused, timestamp)
		if self.__audio_player:
			if paused:
				self.__audio_player.pause()
			else:
				self.__audio_player.restart()

	def stopplay(self, node, curtime):
		if self.__audio_player:
			self.__audio_player.stop()
			self.__audio_player = None
		Channel.ChannelAsync.stopplay(self, node, curtime)


##################
MM_WOM_OPEN = 0x3BB
MM_WOM_CLOSE = 0x3BC
MM_WOM_DONE = 0x3BD

class AudioPlayer:
	buffers_start = 50
	buffers_low = 25
	buffers_hi = 30
	wavehdr_size = 4800
	decode_buf_size = 8192

	def __init__(self, srcurl):
		self._waveout = None
		self._wavhdrs = []
		self._wfx = None

		self._rdr = None
		self._u = None
		self._rest = ''
		self.decoder = None

		try:
			u = MMurl.urlopen(srcurl)
		except IOError:
			raise error, 'Cannot open file.'
		if u.headers.maintype != 'audio':
			u.close()
			raise error, 'Not an audio file.'
		if u.headers.subtype == 'basic':
			atype = 'au'
		elif u.headers.subtype == 'x-aiff':
			atype = 'aiff'
		elif u.headers.subtype == 'x-wav':
			atype = 'wav'
		elif u.headers.subtype in ('mp3', 'mpeg', 'x-mp3'):
			atype = 'mp3'
		else:
			atype = 'au'

		if atype == 'mp3':
			self.read_more = self.read_more_mp3_audio
			self.read_mp3_audio(u, atype)
		else:
			self.read_more = self.read_more_basic_audio
			self.read_basic_audio(u, atype)

		cbwnd = windowinterface.getmainwnd()
		self.hook_callbacks(cbwnd)
		self._waveout = winmm.WaveOutOpen(self._wfx, cbwnd.GetSafeHwnd())
		
		self._waveout.Pause()
		for hdr in self._wavhdrs:
			hdr.PrepareHeader(self._waveout)
			self._waveout.Write(hdr)

	def __del__(self):
		if self._u is not None:
			self._u.close()
		if self._waveout is not None:
			for hdr in self._wavhdrs:
				hdr.UnprepareHeader(self._waveout)
		del self._wavhdrs
		self.decoder = None

	def read_basic_audio(self, u, atype):
		try:
			rdr = audio.reader(u, [audio.format.linear_16_mono], [8000, 11025, 16000, 22050, 32000, 44100], filetype = atype)
# to figure out the number of channels of the source file:
##			r = rdr
##			while hasattr(r, '_rdr'):
##				r = r._rdr
##			ochans = r.getformat().getnchannels()
			fmt = rdr.getformat()
			bytesperframe = fmt.getblocksize() / fmt.getfpb()
			nchan = fmt.getnchannels()
			frate = rdr.getframerate()
			totframes = rdr.getnframes()
		except (audio.Error, IOError, EOFError), msg:
			u.close()
			raise error, msg

		# nChannels, nSamplesPerSec, nAvgBytesPerSecond, BlockAlign, wBitsPerSample
		wfx = nchan, frate, frate*bytesperframe, bytesperframe, bytesperframe*8
		can_play = winmm.WaveOutQuery(wfx)
		if not can_play:
			u.close()
			raise error, 'The device cant play audio format.'
		
		# device can play data with format
		self._wfx = wfx
		self._u = u
		self._rdr = rdr

		frames = AudioPlayer.wavehdr_size/bytesperframe
		while len(self._wavhdrs) < AudioPlayer.buffers_start:
			data, dummy = self._rdr.readframes(frames)
			if not data:
				self._u.close()
				self._u = None 
				break
			hdr = winmm.CreateWaveHdr(data)
			self._wavhdrs.append(hdr)

	def read_more_basic_audio(self):
		if self._waveout is None:
			return
		fmt = self._rdr.getformat()
		bytesperframe = fmt.getblocksize() / fmt.getfpb()
		frames = AudioPlayer.wavehdr_size/bytesperframe
		while len(self._wavhdrs) < AudioPlayer.buffers_hi:
			data, dummy = self._rdr.readframes(frames)
			if not data: 
				self._u.close()
				self._u = None
				break
			hdr = winmm.CreateWaveHdr(data)
			self._wavhdrs.append(hdr)
			hdr.PrepareHeader(self._waveout)
			self._waveout.Write(hdr)

	def read_mp3_audio(self, u, atype):
		# create mp3 decoder
		try:
			self.decoder = decoder = winmm.CreateMp3Decoder()
		except winmm.error, msg:
			self.decoder = None
			raise error, 'CreateMp3Decoder() failed'

		# size of buffer holding encoded data
		decode_buf_size = AudioPlayer.decode_buf_size	

		# read first chunk to read header
		data = u.read(decode_buf_size)
		wfx = decoder.GetWaveFormat(data)
			
# to figure out the number of channels of the source file:
##		ochans = wfx[0]
		can_play = winmm.WaveOutQuery(wfx)
		if not can_play:
			raise error, 'The device cant play audio format.'
			
		# device can play data with format
		self._wfx = wfx
		self._u = u

		# decode some
		
		# the following loop may break because
		# a) of no more data, or
		# b) len(self._wavhdrs) >= AudioPlayer.buffers_start
		
		# before the loop exits, the 'data' buffer is filled
		# a) an empty 'data' buffer means no more data
		# b) filled or half-filled 'data' buffer will be decoded 
		# by 'read_more_mp3_audio' next time
		# c) exception to (b): when self._u has been closed 
		# the 'data' buffer if not empty contains useless data (filler byte or garbage)
			
		decbuf = ''
		status = len(data)
		while status > 0 and len(self._wavhdrs) < AudioPlayer.buffers_start:

			# decode as much as possible from 'data' buffer
			decdata, done, inputpos, status = decoder.DecodeBuffer(data)
			if done>0:
				decbuf = decbuf + decdata[:done]
			while not status:
				decdata, done, status, status = decoder.DecodeBuffer()
				if done>0:
					decbuf = decbuf + decdata[:done]
			if status > 0:
				status = status - 1
			data = data[decode_buf_size - status:]
			
			# re-fill 'data' buffer
			newdata =  u.read(decode_buf_size - status)
			if not newdata:
				self._u.close()
				self._u = None
				# break though 'data' may contain encoded bytes;
				# if they could be decoded they would have been 
				# decoded by the first section of this loop
				break
			data = data + newdata
			status = len(data)

			# if 'decbuf' is sufficiently large send it to the device 
			if len(decbuf) >= AudioPlayer.wavehdr_size:
				wavhdr = winmm.CreateWaveHdr(decbuf)
				self._wavhdrs.append(wavhdr)
				decbuf = ''
		
		# send half-filled buffer to the device 
		if len(decbuf):
			wavhdr = winmm.CreateWaveHdr(decbuf)
			self._wavhdrs.append(wavhdr)
		
		# hold any remaining encoded data
		self._rest = data		

	def read_more_mp3_audio(self):
		if self._waveout is None or self.decoder is None:
			return
		decoder = self.decoder
		
		# size of buffer holding encoded data
		decode_buf_size = AudioPlayer.decode_buf_size	

		decbuf = ''
		data = self._rest
		status = len(data)
		while status > 0 and len(self._wavhdrs) < AudioPlayer.buffers_hi:

			# decode as much as possible from 'data' buffer
			decdata, done, inputpos, status = decoder.DecodeBuffer(data)
			if done>0:
				decbuf = decbuf + decdata[:done]
			while not status:
				decdata, done, status, status = decoder.DecodeBuffer()
				if done>0:
					decbuf = decbuf + decdata[:done]
			if status > 0:
				status = status - 1
			data = data[decode_buf_size - status:]

			# fill  'data' buffer
			newdata =  self._u.read(decode_buf_size - status)
			if not newdata:
				self._u.close()
				self._u = None
				break
			data = data + newdata
			status = len(data)

			# if 'decbuf' is sufficiently large send it to the device 
			if len(decbuf) >= AudioPlayer.wavehdr_size:
				hdr = winmm.CreateWaveHdr(decbuf)
				self._wavhdrs.append(hdr)
				hdr.PrepareHeader(self._waveout)
				self._waveout.Write(hdr)
				decbuf = ''

		# send any half-filled buffer to the device 
		if len(decbuf):
			hdr = winmm.CreateWaveHdr(decbuf)
			self._wavhdrs.append(hdr)
			hdr.PrepareHeader(self._waveout)
			self._waveout.Write(hdr)

		# hold any remaining encoded data
		self._rest = data		

	def play(self):
		if self._waveout:
			self._waveout.Restart()
		
	def pause(self):
		if self._waveout:
			self._waveout.Pause()

	def restart(self):
		if self._waveout:
			self._waveout.Restart()
	
	def stop(self):
		if self._waveout:
			self._waveout.Reset()
			for hdr in self._wavhdrs:
				hdr.UnprepareHeader(self._waveout)
			self._wavhdrs = []
			self._waveout.Close()
			self._waveout = None
		if self._u:
			self._u.close()
			self._u = None

	def hook_callbacks(self, wnd):
		wnd.HookMessage(self.OnOpen, MM_WOM_OPEN)
		wnd.HookMessage(self.OnClose, MM_WOM_CLOSE)
		wnd.HookMessage(self.OnDone, MM_WOM_DONE)

	def OnOpen(self, params):
		pass #print 'OnOpen', params

	def OnClose(self, params):
		pass #print 'OnClose', params

	def OnDone(self, params):
		hwnd, message, wParam, lParam, time, pt = params
		if len(self._wavhdrs):
			hdr = self._wavhdrs[0]
			del self._wavhdrs[0]
			waveout = winmm.WaveOutFromHandle(wParam)
			hdr.UnprepareHeader(waveout)
			waveout.Detach()
		if len(self._wavhdrs) < AudioPlayer.buffers_low and self._u is not None:
			self.read_more()


#########################################
# The simplest possible form of SoundChannel
# uses only winmm.SndPlaySound
# you can't do many things with it

class TestSoundChannel(Channel.ChannelAsync):
	def __init__(self, name, attrdict, scheduler, ui):
		Channel.ChannelAsync.__init__(self, name, attrdict, scheduler, ui)
		self.__playing = None
		self.__audio_player = None

	def __repr__(self):
		return '<SoundChannel instance, name=' + `self._name` + '>'
	
	def do_play(self, node, curtime):
		Channel.ChannelAsync.do_play(self, node, curtime)

		if node.type != 'ext':
			self.errormsg(node, 'Node must be external.')
			return 1
		f = self.getfileurl(node)
		if not f:
			self.errormsg(node, 'No URL set on node.')
			return 1
		
		try:
			f = MMurl.urlretrieve(f)[0]
		except IOError, arg:
			if type(arg) is type(self):
				arg = arg.strerror
			self.errormsg(node, 'Cannot open: %s\n\n%s.' % (f, arg))
			return 1
		try:
			winmm.SndPlaySound(f)
		except winmm.error, arg:
			print arg
			self.playdone(0, curtime)
			return
		else:
			self.__playing = node

	def setpaused(self, paused, timestamp):
		Channel.ChannelAsync.setpaused(self, paused, timestamp)
		if paused:
			winmm.SndStopSound()
		else:
			self.do_play(self.__playing, timestamp)

	def stopplay(self, node, curtime):
		if self.__playing:
			winmm.SndStopSound()
			self.__playing = None
		Channel.ChannelAsync.stopplay(self, node, curtime)


