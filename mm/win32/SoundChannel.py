from Channel import ChannelWindow, FALSE
import urllib, MMurl
import midiex, win32con
import win32ui, mmsystem
import string
import MMAttrdefs
import dsoundex

error = 'Channel.error'

debug = 1

MM_ARMDONE = 1
MM_PLAYDONE = 2

# arm states
AIDLE = 1
ARMING = 2
ARMED = 3
# play states
PIDLE = 1
PLAYING = 2
PLAYED = 3

class SoundChannel(ChannelWindow):
	_visible = FALSE

	def __init__(self, name, attrdict, scheduler, ui):
		ChannelWindow.__init__(self, name, attrdict, scheduler, ui)
		self._armed_soundIndex = None
		self._play_soundIndex = -1
		self._played_soundIndex = None
		self._armed_filename = ""
		self._play_filename = ""
		self._soundWindow = None
		self._tp = None

	def __repr__(self):
		return '<SoundChannel instance, name=' + `self._name` + '>'

	def do_arm(self, node, same=0):
		if self.window == None:
			win32ui.MessageBox("Window not Created yet!!", "Debug", win32con.MB_OK|win32con.MB_ICONSTOP)
			return 1
		else:
			self._soundWindow = self.window._hWnd
		if node.type != 'ext':
			self.errormsg(node, 'Node must be external')
			return 1
		filename = self.getfileurl(node)
		tmp = []
		tmp = string.splitfields(filename, '\\')
		tmp = string.splitfields(tmp[-1], '.')
		if len(tmp)>1:
			ext = tmp[-1]
		else:
			ext = None
		try:
			filename = MMurl.urlretrieve(filename)[0]
		except IOError:
			filename = MMurl.url2pathname(filename)
		tmp = []
		tmp = string.splitfields(filename, '\\')
		tmp = string.splitfields(tmp[-1], '.')
		if ext != None and ext != tmp[-1]:
			import os
			newfilename = filename + '.' + ext
			try:
				os.rename(filename,newfilename)				
			except:
				pass
			filename = newfilename
		#filename = urllib.url2pathname(filename)
		
		self._armed_filename = filename

		self._tp = string.upper(ext)

		self.armed_loop = self.getloop(node)
		self.armed_duration = MMAttrdefs.getattr(node, 'duration')
		if self.armed_duration < 0:
			self.armed_duration = 0.0
		self.callback(0, 0, 0, MM_ARMDONE)		
		return 0

	def play(self, node):
		res = 0
		self.need_armdone = 0
		self.play_0(node)
		if not self._is_shown or self.syncplay:
			self.play_1()
			return
		self._play_filename = self._armed_filename
		if self._tp == 'WAV':
			self._armed_soundIndex = dsoundex.Create(self._soundWindow, self._play_filename)
		else:
			self._armed_soundIndex = midiex.prepare(self._soundWindow, self._play_filename)
		self._soundWindow.HookMessage(self._mmcallback, mmsystem.MM_MCINOTIFY)
		if self._armed_soundIndex<0:
			print 'MCI failed to open sound file-->', self._play_filename
			self.playdone(0)
			return
		self._play_soundIndex = self._armed_soundIndex
		self._armed_soundIndex = None
		self.play_duration = int(self.armed_duration*1000)
		self.play_loop = self.armed_loop
		if self._tp == 'WAV':
			dsoundex.Play(self._play_soundIndex)
			res = 1
		else:
			res = midiex.play(self._play_soundIndex, self.play_duration)
		self.do_play(node)
		self.need_armdone = 1
		if res <> 1:
			print self._filename + " Not Played!"
			self.playdone(0)
		
	def playdone(self, dummy):
		if self.need_armdone:
			self.armdone()
			self.need_armdone = 0
		if self._play_soundIndex > -1:
			if self.play_loop:
				self.play_loop = self.play_loop - 1
				if self.play_loop:
					if self._tp != 'WAV':
						midiex.stop(self._play_soundIndex)
						midiex.seekstart(self._play_soundIndex)
						midiex.play(self._play_soundIndex, self.play_duration)
					else:
						dsoundex.Pause(self._play_soundIndex)
						dsoundex.SeekStart(self._play_soundIndex)
						dsoundex.Play(self._play_soundIndex)
					return
				ChannelWindow.playdone(self, dummy)
				return
			if self._tp != 'WAV':
				midiex.stop(self._play_soundIndex)
				midiex.seekstart(self._play_soundIndex)
				midiex.play(self._play_soundIndex, self.play_duration)
			else:
				dsoundex.Pause(self._play_soundIndex)
				dsoundex.SeekStart(self._play_soundIndex)
				dsoundex.Play(self._play_soundIndex)
		else:
			ChannelWindow.playdone(self, dummy)
		

	
	def callback(self, dummy1, dummy2, event, value):
		if debug:
			print 'ChannelWindow.callback'+`self,dummy1,dummy2,event,value`
		if value == MM_PLAYDONE:
			if self._playstate == PLAYING:
				self.playdone(0)
			elif self._playstate != PIDLE:
				raise error, 'playdone event when not playing'
		elif value == MM_ARMDONE:
			if self._armstate == ARMING:
				self.arm_1()
			elif self._armstate != AIDLE:
				raise error, 'armdone event when not arming'
		else:
			raise error, 'unrecognized event '+`value`

	def _mmcallback(self, params):
		if params[2] == 1:
			self.callback(0, 0, 0, MM_PLAYDONE)

	def stopplay(self, node):
		self._played_soundIndex = self._play_soundIndex
		self._play_soundIndex = -1
		if self._played_soundIndex >= 0:
			if self._tp == 'WAV':
				dsoundex.Pause(self._played_soundIndex)
				dsoundex.SeekStart(self._played_soundIndex)
				dsoundex.Close(self._played_soundIndex)
			else:
				midiex.seekstart(self._played_soundIndex)
				res = midiex.finished(self._played_soundIndex)
		self.play_loop = 1
		self.need_armdone = 0
		self.playdone(0)
		ChannelWindow.stopplay(self, node)
		#if res<0:         returned value is not designed to be either 0 or 1
		#self._soundWindow.MessageBox("Already Destroyed!", "Debug",  win32con.MB_OK|win32con.MB_ICONSTOP)
		

	def setpaused(self, paused):
		ChannelWindow.setpaused(self, paused)
		if self._paused:
			if self._play_soundIndex >= 0:
				if self._tp == 'WAV':
					dsoundex.Pause(self._play_soundIndex)
				else:
					res = midiex.stop(self._play_soundIndex)
		else:
			if self._playstate == PLAYING and self._play_soundIndex >= 0:
				if self._tp == 'WAV':
					dsoundex.Play(self._play_soundIndex)
				else:
					res = midiex.play(self._play_soundIndex, -self.play_duration)
		return



