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

	def __repr__(self):
		return '<SoundChannel instance, name=' + `self._name` + '>'
	
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
	def __init__(self, srcurl):
		self._data = None
		self._waveout = None
		self._wfx = None

		u = MMurl.urlopen(srcurl)
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
			self.read_mp3_audio(u, atype)
		else:
			self.read_basic_audio(u, atype)

		cbwnd = windowinterface.getmainwnd()
		self.hook_callbacks(cbwnd)
		self._waveout = winmm.WaveOutOpen(self._wfx, cbwnd.GetSafeHwnd())

	def read_basic_audio(self, u, atype):
		try:
			rdr = audio.reader(u, [audio.format.linear_16_mono], [8000, 11025, 16000, 22050, 32000, 44100], filetype = atype)
			fmt = rdr.getformat()
			bytesperframe = fmt.getblocksize() / fmt.getfpb()
			nchan = fmt.getnchannels()
			frate = rdr.getframerate()
			totframes = rdr.getnframes()
		except (audio.Error, IOError, EOFError), msg:
			u.close()
			raise error, msg
		self._data, dummy = rdr.readframes(totframes)
		u.close()

		# nChannels, nSamplesPerSec, nAvgBytesPerSecond, BlockAlign, wBitsPerSample
		wfx = nchan, frate, frate*bytesperframe, bytesperframe, bytesperframe*8
		can_play = winmm.WaveOutQuery(wfx)
		if not can_play:
			raise error, 'The device cant play audio format.'

		# device can play data with format
		self._wfx = wfx

	def read_mp3_audio(self, u, atype):
		# create mp3 decoder
		try:
			decoder = winmm.CreateMp3Decoder()
		except winmm.error, msg:
			u.close()
			raise error, 'CreateMp3Decoder() failed'

		# size of buffer holding encoded data
		decode_buf_size = 8192	

		# limit decode size so that we don't break audio subsystem
		# decode/add more when some have been played
		max_data_buf_size = 500000 # upper bound size of decoded data

		# read first chunk to read header
		data = u.read(decode_buf_size)
		wfx = decoder.GetWaveFormat(data)
		can_play = winmm.WaveOutQuery(wfx)
		if not can_play:
			# resample with proposed frequency
			decoder.Reset()		
			if wfx[1] == 48000:
				nSamplesPerSec = 44100
			else:
				nSamplesPerSec = 22050
			wfx = decoder.GetWaveFormat(data, nSamplesPerSec)
			can_play = winmm.WaveOutQuery(wfx)
			if not can_play:
				u.close()
				raise error, 'The device cant play audio format.'
		
		# device can play data with format
		self._wfx = wfx

		# decode some
		self._data = ''
		status = len(data)
		while status > 0 and len(self._data) < max_data_buf_size:
			decdata, done, inputpos, status = decoder.DecodeBuffer(data)
			if done>0:
				self._data = self._data + decdata[:done]
			while not status:
				decdata, done, status, status = decoder.DecodeBuffer()
				if done>0:
					self._data = self._data + decdata[:done]
			if status > 0:
				status = status - 1
			data = data[decode_buf_size - status:]
			newdata =  u.read(decode_buf_size - status)
			if not newdata:
				break
			data = data + newdata
			status = len(data)
		u.close()

	def play(self):
		if self._waveout:
			self._waveout.PlayChunk(self._data)
		
	def pause(self):
		if self._waveout:
			self._waveout.Pause()

	def restart(self):
		if self._waveout:
			self._waveout.Restart()
	
	def stop(self):
		if self._waveout:
			self._waveout.Reset()
			self._waveout.Close()

	def hook_callbacks(self, wnd):
		wnd.HookMessage(self.OnOpen, MM_WOM_OPEN)
		wnd.HookMessage(self.OnClose, MM_WOM_CLOSE)
		wnd.HookMessage(self.OnDone, MM_WOM_DONE)

	def OnOpen(self, params):
		pass #print 'OnOpen', params

	def OnClose(self, params):
		pass #print 'OnClose', params

	def OnDone(self, params):
		pass #print 'OnDone', params


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


