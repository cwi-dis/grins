__version__ = "$Id$"

#
# WIN32 Video channel.
#

""" @win32doc|NTVideoChannel
The NTVideoChannel extends ChannelWindowAsync

Nothing beyond the standard interface is required
from the window by this channel.

In this module ue use an object called GraphBuilder
that supports the interface:

interface IGraphBuilder:
	def RenderFile(self,fn):return 1

	def Run(self):pass
	def Stop(self):pass
	def Pause(self):pass

	def GetDuration(self):return 0
	def SetPosition(self,pos):pass
	def GetPosition(self,pos):return 0

	def SetVisible(self,f):pass
	def SetWindow(self,w):pass

Note that the same object is used for the SoundChannel
and MidiChannel and will be used for NetShow

For more on the DirectShow architecture see MS documentation.
"""

# the core
import Channel

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

# private message to redraw video after resize
WM_REDRAW=win32con.WM_USER+102

# channel types
[SINGLE, HTM, TEXT, MPEG] = range(4)

debug=0

class VideoChannel(Channel.ChannelWindowAsync):
	node_attrs = Channel.ChannelWindowAsync.node_attrs + \
		     ['bucolor', 'hicolor', 'scale', 'center',
		      'clipbegin', 'clipend']
	_window_type = MPEG

	def __init__(self, name, attrdict, scheduler, ui):
		Channel.ChannelWindowAsync.__init__(self, name, attrdict, scheduler, ui)
		
		# DirectShow Graph builder
		self._playBuilder=None
		self._playBegin=0
		self._playEnd=0

		# scheduler notification mechanism
		self.__qid=None
		
		# main thread monitoring fiber id
		self._fiber_id=0
		self.__playdone=1

		# keep last frame support
		self._bmp=None

		# release any resources on exit
		import windowinterface
		windowinterface.addclosecallback(self.release_res,())

	def __repr__(self):
		return '<VideoChannel instance, name=' + `self._name` + '>'

	def do_show(self, pchan):
		if not Channel.ChannelWindowAsync.do_show(self, pchan):
			return 0
		if self._playBuilder:
			self._playBuilder.SetWindow(self.window,WM_GRPAPHNOTIFY)
		if self.window:
			self.window.RedrawWindow()
		return 1

	def do_hide(self):
		self.release_res()
		Channel.ChannelWindowAsync.do_hide(self)

	def destroy(self):
		self.unregister_for_timeslices()
		self.release_res()
		Channel.ChannelWindowAsync.destroy(self)

	def release_res(self):
		if self._playBuilder:
			self._playBuilder.Stop()
			self._playBuilder.SetVisible(0)		
			self._playBuilder.SetWindowNull()
			self._playBuilder.Release()
			self._playBuilder=None
		
	def do_arm(self, node, same=0):
		if debug:print 'VideoChannel.do_arm('+`self`+','+`node`+'same'+')'
		if same and self.armed_display:
			return 1
		if node.type != 'ext':
			self.errormsg(node, 'Node must be external')
			return 1
		self.arm_display(node)
		if not self._playBuilder:
			self._playBuilder=DirectShowSdk.CreateGraphBuilder()
		if not self._playBuilder:
			self.showwarning(node,'System missing infrastructure to playback')
		return 1

	def do_play(self, node):
		if debug:print 'VideoChannel.do_play('+`self`+','+`node`+')'
		if not self._playBuilder:
			return

		url = MMurl.canonURL(self.getfileurl(node))
		if not self._playBuilder.RenderFile(url):
			print 'Failed to render',url
			return

		self.play_loop = self.getloop(node)

		# get duration in secs (float)
		# cancel pending event
		if self.__qid is not None:
			self._scheduler.cancel(self.__qid)
		duration = MMAttrdefs.getattr(node, 'duration')
		if duration > 0:
			self.__qid=self._scheduler.enter(duration, 0, self._stopplay, ())
			
		clip_begin = self.getclipbegin(node,'sec')
		clip_end = self.getclipend(node,'sec')
		self._playBuilder.SetPosition(int(clip_begin*1000))
		self._playBegin = int(clip_begin*1000)
		if clip_end:
			self._playBuilder.SetStopTime(int(clip_end*1000))
			self._playEnd = int(clip_end)*1000
		else:
			self._playEnd=self._playBuilder.GetDuration()

		if self.window and self.window.IsWindow():
			self.AdjustVideoSize(node)
			self._playBuilder.SetWindow(self.window,WM_GRPAPHNOTIFY)
			self.window.HookMessage(self.OnGraphNotify,WM_GRPAPHNOTIFY)
			self.window.HookMessage(self.redraw,WM_REDRAW)

		self._playBuilder.Run()
		self._playBuilder.SetVisible(1)
		self.register_for_timeslices()
		self.__playdone=0
		self.window.PostMessage(WM_REDRAW)


	def arm_display(self,node):
		if debug: print 'NTVideoChannel arm_display'

		# force backgroud color (there must be a better way)
		self.armed_display._bgcolor=self.getbgcolor(node)
		self.armed_display.clear(self.window.getgeometry())

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
		#self.armed_display.drawvideo(self.update)

	
	# Set video size from scale and center attributes
	def AdjustVideoSize(self,node):
		left,top,width,height=self._playBuilder.GetWindowPosition()
		left,top,right,bottom = self.window.GetClientRect()
		x,y,w,h=left,top,right-left,bottom-top

		scale = MMAttrdefs.getattr(node, 'scale')
		center = MMAttrdefs.getattr(node, 'center')

		if scale > 0:
			width = min(width * scale, w)
			height = min(height * scale, h)
			if center:
				x = x + (w - width) / 2
				y = y + (h - height) / 2
		else:
			# fit in window
			width = w
			height = h

		rcVideo=(x, y, width,height)
		self._playBuilder.SetWindowPosition(rcVideo)

	def redraw(self,params):
		if self.window:
			self.window.RedrawWindow()

	# scheduler callback, at end of duration
	def _stopplay(self):
		self.__qid = None
		self.__freeze()
		self.__playdone=1
		self.playdone(0)

	# Part of stop sequence. Stop and remove last frame 
	def stopplay(self, node):
		if self.__qid is not None:
			self._scheduler.cancel(self.__qid)
			self.__qid = None
		self.release_res()
		if self._bmp:self._bmp=None
		Channel.ChannelWindowAsync.stopplay(self, node)

	def playstop(self):
		Channel.ChannelWindowAsync.playstop(self)
		if self.window:
			self.window.RedrawWindow()

	# toggles between pause and run
	def setpaused(self, paused):
		self._paused = paused
		if self._playBuilder:
			if self._paused:
				self.__freeze()
				self._playBuilder.Pause()
			else:
				self._playBuilder.Run()


	# capture end of media
	def OnGraphNotify(self,params):
		if self._playBuilder and not self.__playdone:
			t_msec=self._playBuilder.GetPosition()
			if t_msec>=self._playEnd:self.OnMediaEnd()

	def OnMediaEnd(self):
		if debug: print 'VideoChannel: OnMediaEnd',`self`
		if not self._playBuilder:
			return		
		if self.play_loop:
			self.play_loop = self.play_loop - 1
			if self.play_loop: # more loops ?
				self._playBuilder.SetPosition(self._playBegin)
				self._playBuilder.Run()
				return
			# no more loops
			self.__freeze()
			self.__playdone=1
			# if event wait scheduler
			if self.__qid is not None:return
			# else end
			self.playdone(0)
			return
		# self.play_loop is 0 so repeat
		self._playBuilder.SetPosition(0)
		self._playBuilder.Run()

	def defanchor(self, node, anchor, cb):
		import windowinterface
		windowinterface.showmessage('The whole window will be hot.')
		cb((anchor[0], anchor[1], [0,0,1,1]))


############################### ui delays management
	def on_idle_callback(self):
		if self._playBuilder and not self.__playdone:
			t_msec=self._playBuilder.GetPosition()
			if t_msec>=self._playEnd:self.OnMediaEnd()

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

############################ 
# showwarning if the infrastucture is missing.
# The user should install Windows Media Player
# since then this infrastructure is installed

	def showwarning(self,node,inmsg):
		name = MMAttrdefs.getattr(node, 'name')
		if not name:
			name = '<unnamed node>'
		chtype = self.__class__.__name__[:-7] # minus "Channel"
		msg = 'Warning:\n%s\n' \
		      '%s node %s on channel %s' % (inmsg, chtype, name, self._name)
		parms = self.armed_display.fitfont('Times-Roman', msg)
		w, h = self.armed_display.strsize(msg)
		self.armed_display.setpos((1.0 - w) / 2, (1.0 - h) / 2)
		self.armed_display.fgcolor((255, 0, 0))		# red
		box = self.armed_display.writestr(msg)



############################# unused stuff but keep it for now
	# Make a copy of frame and keep it until stopplay is called
	def __freeze(self):
		return # bmp not used
		import win32mu,win32api
		if self.window and self.window.IsWindow():
			if self._bmp: 
				self._bmp.DeleteObject()
				del self._bmp
			win32api.Sleep(0)
			self._bmp=win32mu.WndToBmp(self.window)

	def update(self,dc):
		import win32mu
		if self._playBuilder and (self.__playdone or self._paused):
			self.window.RedrawWindow()
			if self._bmp: 
				win32mu.BitBltBmp(dc,self._bmp,self.window.GetClientRect())
