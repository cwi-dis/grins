__version__ = "$Id$"

from Channel import ChannelWindow, FALSE
import urllib
import midiex, win32con
import win32ui, mmsystem
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
		self._play_soundIndex = None
		self._played_soundIndex = None
		self._filename = ""
		self._soundWindow = None

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
		filename = urllib.url2pathname(filename)
		print filename
		#if (self._armed_soundIndex <> None) : 
		#the previously armed node was not played
		# do clean up
		#	midiex.finished(self._armed_soundIndex) 
		
		self._filename = filename
		self._soundWindow.HookMessage(self._mmcallback, mmsystem.MM_MCINOTIFY)
		self.callback(0, 0, 0, MM_ARMDONE)		
		return 0
	#	return self.syncarm

	def play(self, node):
		res = 0
		self.need_armdone = 0
		self.play_0(node)
		if not self._is_shown or self.syncplay:
			self.play_1()
			return
		if not self.nopop:
			self.window.pop()
		if self.armed_display.is_closed():
			# assume that we are going to get a
			# resize event
			pass
#		else:
#			self.armed_display.render()
#		if self.played_display:
#			self.played.display.close()
		self.played_display = self.armed_display
		self.armed_display = None
		self._armed_soundIndex = midiex.prepare(self._soundWindow, self._filename)
		if self._armed_soundIndex<0:
			print 'MCI failed to open sound file'
		self._play_soundIndex = self._armed_soundIndex
		self._armed_soundIndex = None
		print self._filename
		print 'INDEX TO PLAY IS'
		print self._play_soundIndex
		res = midiex.play(self._play_soundIndex)
		self._filename =""                      #filename played, playdone follows
		self.do_play(node)
		self.need_armdone = 1
		if res <> 1:
			print self._filename + " Not Played!"
			self.playdone(0)
		
	def playdone(self, dummy):
		if self.need_armdone:
			self.armdone()
			self.need_armdone = 0
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
		#win32ui.MessageBox(mes, "Debug", win32con.MB_OK)
		if params[2] == 1:
			self.callback(0, 0, 0, MM_PLAYDONE)

	def stopplay(self, node):
		ChannelWindow.stopplay(self, node)
		self._played_soundIndex = self._play_soundIndex
		if self._played_soundIndex <> None :
			res = midiex.finished(self._played_soundIndex)
		#if res<0:         returned value is not designed to be either 0 or 1
		#self._soundWindow.MessageBox("Already Destroyed!", "Debug",  win32con.MB_OK|win32con.MB_ICONSTOP)
		

	def setpaused(self, paused):
		ChannelWindow.setpaused(self, paused)
		if self._paused:
			if self._play_soundIndex <> None :
				res = midiex.stop(self._play_soundIndex)
		else:
			if self._playstate == PLAYING:
				res = midiex.play(self._play_soundIndex)
		return



