__version__ = "$Id$"

#
# WIN32 Video channel.
#

from Channel import *

# node attributes
import MMAttrdefs

# url parsing
import os, ntpath, urllib, MMurl

# std win32 libs 
import win32ui,win32con

# DirectShow support
DirectShowSdk=win32ui.GetDS()

# private graph notification message
WM_GRPAPHNOTIFY=win32con.WM_USER+101

# channel types
[SINGLE, HTM, TEXT, MPEG] = range(4)

debug=0

class VideoChannel(ChannelWindow):
	node_attrs = ChannelWindow.node_attrs + \
		     ['bucolor', 'hicolor', 'scale', 'center',
		      'clipbegin', 'clipend']
	_window_type = MPEG
	def __init__(self, name, attrdict, scheduler, ui):
		ChannelWindow.__init__(self, name, attrdict, scheduler, ui)
		
		# DirectShow Graph builders
		self._builders={}

		# active builder from self._builders
		self._playBuilder=None

		# scheduler notification mechanism
		self.__qid=None
		
		# main thread monitoring fiber id
		self._fiber_id=0

	def __repr__(self):
		return '<VideoChannel instance, name=' + `self._name` + '>'

	def do_show(self, pchan):
		if not ChannelWindow.do_show(self, pchan):
			return 0
		for b in self._builders.values():
			b.SetWindow(self.window,WM_GRPAPHNOTIFY)
		return 1

	# the current ChannelWindow.do_hide implementation 
	# destroy the window
	def do_hide(self):
		for b in self._builders.values():
			b.Stop()
			b.SetVisible(0)		
			b.SetWindowNull()
			#b.Release()
		#self._builders.clear()
		self._playBuilder=None
		ChannelWindow.do_hide(self)

	def destroy(self):
		self.unregister_for_timeslices()
		for b in self._builders.values():
			b.Stop()
			b.SetVisible(0)
			b.SetWindowNull()
			#b.Release()
		self._playBuilder=None
		self._builders.clear()
		ChannelWindow.destroy(self)

	def do_arm(self, node, same=0):
		if debug:print 'VideoChannel.do_arm('+`self`+','+`node`+'same'+')'
		self.arm_display(node)
		if node in self._builders.keys():		
			return 1
		if node.type != 'ext':
			self.errormsg(node, 'Node must be external')
			return 1
		fn = self.getfileurl(node)
		fn = MMurl.urlretrieve(fn)[0]
		fn = self.toabs(fn)
		builder=DirectShowSdk.CreateGraphBuilder()
		if builder:
			builder.RenderFile(fn)
			self._builders[node]=builder
		else:
			print 'Failed to create GraphBuilder'
		return 1

	# Async Channel play
	def play(self, node):
		if debug:print 'VideoChannel.play('+`self`+','+`node`+')'
		self.play_0(node)
		if not self._is_shown or not node.IsPlayable() \
		   or self.syncplay:
			self.play_1()
			return
		if not self.nopop:
			self.window.pop()
		if self.played_display:
			self.played_display.close()
		self.played_display = self.armed_display
		self.armed_display = None
		if self._is_shown:
			self.played_display.render()
			self.do_play(node)
		self.armdone()

	def do_play(self, node):
		if debug:print 'VideoChannel.do_play('+`self`+','+`node`+')'
		if node not in self._builders.keys():
			print 'node not armed'
			self.playdone(0)
			return

		self.play_loop = self.getloop(node)

		# get duration in secs (float)
		# cancel pending event
		if self.__qid is not None:
			self._scheduler.cancel(self.__qid)
		duration = MMAttrdefs.getattr(node, 'duration')
		if duration > 0:
			self.__qid=self._scheduler.enter(duration, 0, self._stopplay, ())

		self._playBuilder=self._builders[node]
		self._playBuilder.SetPosition(0)
		if self.window and self.window.IsWindow():
			self._playBuilder.SetWindow(self.window,WM_GRPAPHNOTIFY)
			self.window.HookMessage(self.OnGraphNotify,WM_GRPAPHNOTIFY)
		self._playBuilder.Run()
		self._playBuilder.SetVisible(1)
		self.register_for_timeslices()

		if self.play_loop == 0 and duration == 0:
			self.playdone(0)

	def arm_display(self,node):
		drawbox = MMAttrdefs.getattr(node, 'drawbox')
		if drawbox:
			self.armed_display.fgcolor(self.getbucolor(node))
		else:
			self.armed_display.fgcolor(self.getbgcolor(node))
		hicolor = self.gethicolor(node)
		for a in node.GetRawAttrDef('anchorlist', []):
			atype = a[A_TYPE]
			if atype not in SourceAnchors or atype == ATYPE_AUTO:
				continue
			b = self.armed_display.newbutton((0,0,1,1))
			b.hiwidth(3)
			if drawbox:
				b.hicolor(hicolor)
			self.setanchor(a[A_ID], a[A_TYPE], b)

	def __stop(self):
		if self._playBuilder:
			#self._playBuilder.Pause()
			# pause instead of stopping in order
			# to keep video frame ?

			self._playBuilder.Stop()
			self._playBuilder.SetVisible(0)
			self._playBuilder=None
			if self.window:
				self.window.update()
		# keep anchors and background
		#if self.played_display:
		#	self.played_display.close()
				
	# scheduler callback, at end of duration
	def _stopplay(self):
		self.__qid = None
		self.__stop()
		self.playdone(0)

	# part of stop sequence
	def stopplay(self, node):
		if self.__qid is not None:
			self._scheduler.cancel(self.__qid)
			self.__qid = None
		self.__stop()
		ChannelWindow.stopplay(self, node)

	# toggles between pause and run
	def setpaused(self, paused):
		self._paused = paused
		if self._playBuilder:
			if self._paused:
				self._playBuilder.Pause()
			else:
				self._playBuilder.Run()


	# capture end of media
	def OnGraphNotify(self,params):
		if self._playBuilder:
			duration=self._playBuilder.GetDuration()
			t_msec=self._playBuilder.GetPosition()
			if t_msec>=duration:self.OnMediaEnd()

	def OnMediaEnd(self):
		if debug: print 'VideoChannel: OnMediaEnd',`self`
		if not self._playBuilder:
			return		
		if self.play_loop:
			self.play_loop = self.play_loop - 1
			if self.play_loop: # more loops
				self._playBuilder.SetPosition(0)
				self._playBuilder.Run()
				return
			# no more loops
			self.__stop()
			# if event wait scheduler
			if self.__qid is not None:return
			# else end
			self.playdone(0)
			return


	def defanchor(self, node, anchor, cb):
		import windowinterface
		windowinterface.showmessage('The whole window will be hot.')
		cb((anchor[0], anchor[1], [0,0,1,1]))

	def islocal(self,url):
		utype, url = MMurl.splittype(url)
		host, url = MMurl.splithost(url)
		return not utype and not host

	def toabs(self,url):
		if not self.islocal(url):
			return url
		filename=MMurl.url2pathname(MMurl.splithost(url)[1])
		if os.path.isfile(filename):
			if not os.path.isabs(filename):
				filename=os.path.join(os.getcwd(),filename)
				filename=ntpath.normpath(filename)	
		return filename

	# ui delays management
	def on_idle_callback(self):
		if self._playBuilder:
			if self._playBuilder.IsCompleteEvent():
				self.OnMediaEnd()
			else: # not actualy needed but I am burned!
				duration=self._playBuilder.GetDuration()
				t_msec=self._playBuilder.GetPosition()
				if t_msec>=duration:self.OnMediaEnd()

	def is_callable(self):
		return self._playBuilder
	def register_for_timeslices(self):
		if self._fiber_id: return
		import windowinterface
		self._fiber_id=windowinterface.register((self.is_callable,()),(self.on_idle_callback,()))
	def unregister_for_timeslices(self):
		if not self._fiber_id: return
		import windowinterface
		windowinterface.unregister(self._fiber_id)
		self._fiber_id=0