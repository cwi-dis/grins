from Channel import ChannelWindow, MPEG, error
import urllib, MMurl
import mpegex, win32con
import win32ui, mmsystem
from MMExc import *			# exceptions
from AnchorDefs import *
import string
import MMAttrdefs
import timerex2, time

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


class VideoChannel(ChannelWindow):
	_window_type = MPEG
	node_attrs = ChannelWindow.node_attrs + \
		     ['bucolor', 'hicolor', 'scale', 'center',
		      'clipbegin', 'clipend']

	def __init__(self, name, attrdict, scheduler, ui):
		ChannelWindow.__init__(self, name, attrdict, scheduler, ui)
		self._armed_movieIndex = None
		self._play_movieIndex = None
		self._played_movieIndex = None
		self._armed_filename = ""
		self._play_filename = ""
		self._movieWindow = None
		self._filename=" "
		self.windc = None
		self._arm_anc_ls = []
		self._play_anc_ls = []
		self.timerID = 0
		self._start_time = None
		self._stop_time = None
		self._time_remain = None

	def __repr__(self):
		return '<MpegChannel instance, name=' + `self._name` + '>'

	def resize(self, arg, window, event, value):
		#print " -------------- MPEG RESIZE -----------------"
		if self._playstate == PLAYING or self._playstate == PLAYED:
			if self._armed_movieIndex!=None:
				mpegex.position(self._armed_movieIndex)
			if self._play_movieIndex!=None:
				mpegex.position(self._play_movieIndex)


			if self.armed_display:
				bgcolor = self.armed_display._bgcolor
				self.armed_display.close()
				self.armed_display = self.window.newdisplaylist(bgcolor)
				for a in self._arm_anc_ls:
					b = self.armed_display.newbutton((0,0,1,1))
					self.setanchor(a[A_ID], a[A_TYPE], b)
				self.armed_display._list.append(('video', self, self.test3))

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
				self.played_display._list.append(('video', self, self.test3))
				self.played_display.render()
		else:
			ChannelWindow.resize(self, arg, window, event, value)

	def do_arm(self, node, same=0):
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

		self.armed_display.fgcolor(self.getfgcolor(node))
		filename = self.getfileurl(node)
		#filename = urllib.url2pathname(filename)
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

		self._armed_filename = filename
		scale = MMAttrdefs.getattr(node, 'scale')
		self.armed_scale = scale
		center = MMAttrdefs.getattr(node, 'center')
		self.armed_center = center
		if self.armed_scale==None:
			self.armed_scale = 0.0
		if self.armed_center==None:
			self.armed_center = 0

		self.callback(0, 0, 0, MM_ARMDONE)
		self.armed_loop = self.getloop(node)
		self.armed_duration = MMAttrdefs.getattr(node, 'duration')
		if MMAttrdefs.getattr(node, 'clipbegin'):
			self.__begin = eval(MMAttrdefs.getattr(node, 'clipbegin'))
		else:
			self.__begin = 0
		if MMAttrdefs.getattr(node, 'clipend'):
			self.__end = eval(MMAttrdefs.getattr(node, 'clipend'))
		else:
			self.__end = 0
		print "self.__begin, self.__end--->",self.__begin, self.__end
		try:
			alist = node.GetRawAttr('anchorlist')
		except NoSuchAttrError:
			alist = []
		self._arm_anc_ls = []
		for a in alist:
			self._arm_anc_ls.append(a)
			b = self.armed_display.newbutton((0,0,1,1))
			#b.hiwidth(3)
			#b.hicolor(hicolor)
			self.setanchor(a[A_ID], a[A_TYPE], b)
		#self.window._hWnd.HookMessage(self.test3, 4000)
		self.armed_display._list.append(('video', self, self.test3))
		return 0

	def test(self, params):
		print "Parameters are:", params
		if params[2]==2002:
			#self.window._hWnd.ReleaseCapture()
			self.window._mouseLClick_callback(params)
		elif params[2]==2003:
			self.window._hWnd.ReleaseCapture()
			self.window._rdblclk_callback(params)


	def test2(self, params):
		#print "Parameters for test2 are:", params
		x = params[2]
		y = params[3]
		#print "x, y --->", x, y
		self.window._setcursor_callback((0,0,0,0,0,(x,y)))


	def test3(self, params):
		if self._playstate == PLAYING or self._playstate == PLAYED:
			if self._play_movieIndex!=None:
				#print "<------Video Update----->"
				mpegex.Update(self._play_movieIndex)


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

		from win32con import *
		#self.windc = self._movieWindow.GetWindow(GW_CHILD)
		#self.window._hWnd.HookMessage(self.test, WM_PARENTNOTIFY)
		self.window._hWnd.HookMessage(self.test2, UM_SETCURSOR)
		self._play_filename = self._armed_filename
		self._armed_filename = ""
		self.play_scale = self.armed_scale
		self.play_center = self.armed_center

		self._movieWindow.HookMessage(self._mmcallback, win32con.WM_TIMER)
		self._armed_movieIndex = mpegex.arm(self._movieWindow, self._play_filename, 0, self.play_scale, self.play_center,self.__begin, self.__end)
		if self._armed_movieIndex<0:
			print 'MCI failed to open movie file'
			print self._play_filename
			print 'Movie not armed'
			self.playdone(0)
			return

		self._play_movieIndex = self._armed_movieIndex
		self._armed_movieIndex = None
		self.play_duration = int(self.armed_duration*1000)

		if self.play_duration <= 0 or self.armed_duration==None:
			self.play_duration = mpegex.GetDuration(self._play_movieIndex)

		self.play_loop = self.armed_loop
		res = mpegex.play(self._play_movieIndex, 0)
		if self.play_duration > 0:
			self._time_remain = self.play_duration
			self._start_time = time.time()
			self.timerID = timerex2.SetTimer(self._movieWindow , self.play_duration)
		self.do_play(node)
		self.need_armdone = 1
		if  res <> 1:
			self.playdone(0)
		if self.play_loop == 0 and not self.play_duration:
			self.play_loop = 1
			self.playdone(0)

	def playdone(self, dummy):
		if self.timerID >0:
			timerex2.KillTimer(self._movieWindow , self.timerID)
			self.timerID = 0
		if self.need_armdone:
			self._armstate = ARMED
			self.armdone()
			self.need_armdone = 0
		self.play_loop = self.play_loop-1
		if self._play_movieIndex > -1:
			if self.play_loop:
				#self.play_loop = self.play_loop - 1
				if self.play_loop:
					mpegex.seekstart(self._play_movieIndex)
					mpegex.play(self._play_movieIndex, 0)
					if self.play_duration > 0:
						self._time_remain = self.play_duration
						self._start_time = time.time()
						self.timerID = timerex2.SetTimer(self._movieWindow , self.play_duration)
					return
				res = mpegex.stop(self._play_movieIndex)
				ChannelWindow.playdone(self, dummy)
				return
			#mpegex.seekstart(self._play_movieIndex)
			#mpegex.play(self._play_movieIndex, self.play_duration)
			ChannelWindow.playdone(self, dummy)
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
		print 'MCI NOTIFY MESSAGE, parmas:', params
		if self.timerID >0:
			timerex2.KillTimer(self._movieWindow , self.timerID)
			self.timerID = 0
		self.callback(0, 0, 0, MM_PLAYDONE)
		#else:
		#	if (params[2] == 1):
		#		self.callback(0, 0, 0, MM_PLAYDONE)

	def stopplay(self, node):
		if self.timerID>0:
			timerex2.KillTimer(self._movieWindow , self.timerID)
			self.timerID = 0
		self._played_movieIndex = self._play_movieIndex
		self._play_movieIndex = -1
		self._play_anc_ls = []
		if self._played_movieIndex <> None :
			res = mpegex.finished(self._played_movieIndex)
			#from win32con import *
			#self.window._hWnd.HookMessage(self.null_cal, WM_PARENTNOTIFY)
			self.window._hWnd.HookMessage(self.null_cal, UM_SETCURSOR)
			if res<0:
				self._movieWindow.MessageBox("Already Destroyed!", "Debug",  win32con.MB_OK|win32con.MB_ICONSTOP)
		self.need_armdone = 0
		self.play_loop = 1
		self.playdone(0)
		ChannelWindow.stopplay(self, node)


	def setpaused(self, paused):
		if self.timerID>0:
			timerex2.KillTimer(self._movieWindow , self.timerID)
			self.timerID = 0
		ChannelWindow.setpaused(self, paused)
		if self._paused:
			if self._play_movieIndex <> None:
				self._stop_time = time.time()
				self._time_remain = self._time_remain-int((self._stop_time-self._start_time)*1000)
				if self._time_remain <=0:
					self._time_remain = 1
				res = mpegex.stop(self._play_movieIndex)
		else:
			if self._playstate == PLAYING:
				if self._time_remain > 0:
						self._start_time = time.time()
						self.timerID = timerex2.SetTimer(self._movieWindow , self._time_remain)
				res = mpegex.play(self._play_movieIndex, self.play_duration-self._time_remain)
		return

