from Channel import ChannelWindow, MPEG, error
import urllib, MMurl
import win32con
import win32ui, mmsystem
from MMExc import *			# exceptions
from AnchorDefs import *
from win32modules import mpegex

debug = 1

MM_ARMDONE = 1
MM_PLAYDONE = 2
UM_SETCURSOR = 2001

# arm states
AIDLE = 1
ARMING = 2
ARMED = 3
# play states
PIDLE = 1
PLAYING = 2
PLAYED = 3

[SINGLE, HTM, TEXT, MPEG] = range(4)


class MpegChannel(ChannelWindow):
	_window_type = MPEG

	def __init__(self, name, attrdict, scheduler, ui):
		ChannelWindow.__init__(self, name, attrdict, scheduler, ui)
		self._armed_movieIndex = None
		self._play_movieIndex = None
		self._played_movieIndex = None
		self._filename = ""
		self._movieWindow = None
		self._filename=" "
		self.windc = None
		self._arm_anc_ls = []
		self._play_anc_ls = []

	def __repr__(self):
		return '<MpegChannel instance, name=' + `self._name` + '>'

	def resize(self, arg, window, event, value):
		print " -------------- MPEG RESIZE -----------------"
		if self._playstate == PLAYING or self._playstate == PLAYED:
			if self._play_movieIndex!=None:
				mpegex.position(self._play_movieIndex)
			if self._armed_movieIndex!=None:
				mpegex.position(self._armed_movieIndex)

			if self.armed_display:
				bgcolor = self.armed_display._bgcolor
				self.armed_display.close()
				self.armed_display = self.window.newdisplaylist(bgcolor)
				for a in self._arm_anc_ls:
					b = self.armed_display.newbutton((0,0,1,1))
					self.setanchor(a[A_ID], a[A_TYPE], b)

			if self.played_display:
				bgcolor = self.played_display._bgcolor
				self.played_display.close()
				self.played_display = self.window.newdisplaylist(bgcolor)
				for a in self._play_anc_ls:
					b = self.played_display.newbutton((0,0,1,1))
					self.setanchor(a[A_ID], a[A_TYPE], b)
				node = self._played_node
				import MMAttrdefs
				self._anchors = {}
				self._played_anchors = self._armed_anchors[:]
				durationattr = MMAttrdefs.getattr(node, 'duration')
				self._has_pause = (durationattr < 0)
				for (name, type, button) in self._played_anchors:
					if type == ATYPE_PAUSE:
						f = self.pause_triggered
						self._has_pause = 1
					else:
						f = self._playcontext.anchorfired
					self._anchors[button] = f, (node, [(name, type)], None)
				self.played_display.render()
		else:
			ChannelWindow.resize(self, arg, window, event, value)

	def do_arm(self, node, same=0):
		print 'Entering mpeg DoArm '
		if self.window == None:
			win32ui.MessageBox("Window not Created yet!!", "Debug", win32con.MB_OK|win32con.MB_ICONSTOP)
			return 1
		else:
			self._movieWindow = self.window._hWnd
		if node.type != 'ext':
			self.errormsg(node, 'Node must be external')
			return 1
		self._armed_anchors = [] # may have been skipped in self.arm_0
		if self.armed_display:
			self.armed_display.close()
		bgcolor = self.getbgcolor(node)
		self.armed_display = self.window.newdisplaylist(bgcolor)
		item = self.armed_display._list[0]
		#if item[0]=='clear':
		#	i = self.armed_display._list.index(item)
		#	self.armed_display._list[i] = ('video',)
		self.armed_display.fgcolor(self.getfgcolor(node))
		filename = self.getfileurl(node)
		filename = MMurl.url2pathname(filename)
		print filename
		#if self._armed_movieIndex != None :
			#the previously armed node was not played
			# do clean up
			#mpegex.finished(self._armed_movieIndex)
		self._filename = filename
		#self._armed_movieIndex = mpegex.arm(self._movieWindow, self._filename, 0)
		#if self._armed_movieIndex<0:
		#	errormsg = "Movie Error, Code: "+`self._armed_movieIndex`
		#	print 'MCI failed to open movie file'
		#	print 'Movie not armed'
		#	return 1
		#self._movieWindow.HookMessage(self._mmcallback, mmsystem.MM_MCINOTIFY)
		self.callback(0, 0, 0, MM_ARMDONE)

		try:
			alist = node.GetRawAttr('anchorlist')
			modanchorlist(alist)
		except NoSuchAttrError:
			alist = []
		self._arm_anc_ls = []
		for a in alist:
			self._arm_anc_ls.append(a)
			b = self.armed_display.newbutton((0,0,1,1))
			#b.hiwidth(3)
			#b.hicolor(hicolor)
			self.setanchor(a[A_ID], a[A_TYPE], b)

		return 0
	#	return self.syncarm

	def test(self, params):
		#print "Parameters are:", params
		if params[2] in range(2):
			if params[2]==0:
				#self.window._hWnd.ReleaseCapture()
				self.window._mouseLClick_callback(params)
			elif params[2]==1:
				self.window._hWnd.ReleaseCapture()
				self.window._rdblclk_callback(params)


	def test2(self, params):
		#print "Parameters for test2 are:", params
		x = params[2]
		y = params[3]
		#print "x, y --->", x, y
		self.window._setcursor_callback((0,0,0,0,0,(x,y)))



	def null_cal(self, params):
		pass

	#
	# It appears that there is a bug in the cl mpeg decompressor
	# which disallows the use of two mpeg decompressors in parallel.
	#
	# Redefining play() and playdone() doesn't really solve the problem,
	# since two mpeg channels will still cause trouble,
	# but it will solve the common case of arming the next file while
	# the current one is playing.
	#
	# XXXX This problem has to be reassesed with the 5.2 cl. See also
	# the note in mpegchannelmodule.c
	#
	def play(self, node):
		res = 0
		self.need_armdone = 0
		self.play_0(node)
		if not self._is_shown or self.syncplay:
			self.play_1()
			return
		if not self.nopop:
			self.window.pop()
		if self.played_display:
			self.played.display.close()
		if self.armed_display.is_closed():
			# assume that we are going to get a
			# resize event
			pass
		else:
			self.armed_display.render()
		self.played_display = self.armed_display
		self.armed_display = None
		self._play_anc_ls = self._arm_anc_ls

		self._armed_movieIndex = mpegex.arm(self._movieWindow, self._filename, 0)
		from win32con import *
		#self.windc = self._movieWindow.GetWindow(GW_CHILD)
		#self.window._hWnd.HookMessage(self.test, WM_PARENTNOTIFY)
		self.window._hWnd.HookMessage(self.test2, UM_SETCURSOR)
		#if self._armed_movieIndex<0:
		#	errormsg = "Movie Error, Code: "+`self._armed_movieIndex`
		#	print 'MCI failed to open movie file'
		#	print 'Movie not armed'
		#	return

		self._movieWindow.HookMessage(self._mmcallback, mmsystem.MM_MCINOTIFY)
		if self._play_movieIndex>=0:
			mpegex.stop(self._play_movieIndex)
			mpegex.finished(self._play_movieIndex)
		self._play_movieIndex = self._armed_movieIndex
		self._armed_movieIndex = None
		res = mpegex.play(self._play_movieIndex)
		#self._filename =""                      #filename played, playdone follows
		self.do_play(node)
		self.need_armdone = 1
		if  res <> 1:
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
		print 'MCI NOTIFY MESSAGE, parmas:', params
		if (params[2] == 1):
			self.callback(0, 0, 0, MM_PLAYDONE)

	def stopplay(self, node):
		ChannelWindow.stopplay(self, node)
		self._played_movieIndex = self._play_movieIndex
		self._play_movieIndex = None
		print 'PLAYED INDEX:'
		print self._played_movieIndex
		self._play_anc_ls = []
		if self._played_movieIndex <> None :
			res = mpegex.finished(self._played_movieIndex)
			#from win32con import *
			#self.window._hWnd.HookMessage(self.null_cal, WM_PARENTNOTIFY)
			self.window._hWnd.HookMessage(self.null_cal, UM_SETCURSOR)
			if res<0:
				self._movieWindow.MessageBox("Already Destroyed!", "Debug",  win32con.MB_OK|win32con.MB_ICONSTOP)


	def setpaused(self, paused):
		ChannelWindow.setpaused(self, paused)
		if self._paused:
			if self._play_movieIndex <> None:
				res = mpegex.stop(self._play_movieIndex)
		else:
			if self._playstate == PLAYING:
				res = mpegex.play(self._play_movieIndex)
		return
