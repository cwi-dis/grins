__version__ = "$Id$"

#
# WIN32 Video channel.
#

""" @win32doc|NTVideoChannel
The NTVideoChannel extends the ChannelWindow
(although it repeats the ChannelWindowAsync implementation)

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


We have implemented such an object using the win32 DirectShow Sdk
We get the module from the module server by calling:
DirectShowSdk=win32ui.GetDS()
and from the module returned, we request an object 
with the above interface with the call
builder=DirectShowSdk.CreateGraphBuilder()

Note that the same object is used for the SoundChannel
and MidiChannel

For more on the DirectShow architecture see MS documentation.
"""


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
# private message to redraw video after resize
WM_REDRAW=win32con.WM_USER+102

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
		self._playDuration=0

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
		if not ChannelWindow.do_show(self, pchan):
			return 0
		for b in self._builders.values():
			b.SetWindow(self.window,WM_GRPAPHNOTIFY)
		if self.window:
			self.window.RedrawWindow()
		return 1

	# the current ChannelWindow.do_hide implementation 
	# destroy the window
	def do_hide(self):
		self.release_res()
		ChannelWindow.do_hide(self)

	def destroy(self):
		self.unregister_for_timeslices()
		self.release_res()
		ChannelWindow.destroy(self)

	def release_res(self):
		for b in self._builders.values():
			b.Stop()
			b.SetVisible(0)		
			b.SetWindowNull()
			b.Release()
		del self._builders
		self._builders={}
		self._playBuilder=None
		
	def do_arm(self, node, same=0):
		if debug:print 'VideoChannel.do_arm('+`self`+','+`node`+'same'+')'
		if same and self.armed_display:
			return 1
		if node.type != 'ext':
			self.errormsg(node, 'Node must be external')
			return 1

		self.arm_display(node)

		if node in self._builders.keys():		
			return 1
		fn = self.getfileurl(node)
		fn = MMurl.urlretrieve(fn)[0]
		fn = self.toabs(fn)
		builder=DirectShowSdk.CreateGraphBuilder()
		if builder:
			if not builder.RenderFile(fn):
				print 'Failed to render',fn
				builder=None
			self._builders[node]=builder
		else:
			print 'Failed to create GraphBuilder'
		return 1

	# Async Channel play
	def play(self, node):
		if debug:print 'VideoChannel.play('+`self`+','+`node`+')'
		self.play_0(node)
	
		if debug: print 'self._is_shown',self._is_shown,'node.IsPlayable()',node.IsPlayable(),'self.syncplay',self.syncplay
		if not self._is_shown or not node.IsPlayable() or not self.window:
			self.play_1()
			return

		if self._is_shown and node.IsPlayable() and self.window:
			self.check_popup()
			self.set_arm_display()
			if not self.syncplay:
				self.do_play(node)
				self.armdone()
			else: # replaynode call, due to resize or other reason
				if not self._playBuilder:
					if node in self._builders.keys():
						self._playBuilder=self._builders[node]
				if not self._playBuilder:
					self.play_1()
					return	
				self._playBuilder.SetWindow(self.window,WM_GRPAPHNOTIFY)
				self._playBuilder.SetVisible(1)
				self.__freeze()
				self.play_1()

				# redraw video after resizing
				self.window.PostMessage(WM_REDRAW)


	def do_play(self, node):
		if debug:print 'VideoChannel.do_play('+`self`+','+`node`+')'
		if node not in self._builders.keys():
			print 'node not armed'
			self.__playdone=1
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
		if not self._playBuilder:
			self.__playdone=1
			self.playdone(0)
			return
			
		self._playBuilder.SetPosition(0)
		self._playDuration=self._playBuilder.GetDuration()
		if self.window and self.window.IsWindow():
			self._playBuilder.SetWindow(self.window,WM_GRPAPHNOTIFY)
			self.window.HookMessage(self.OnGraphNotify,WM_GRPAPHNOTIFY)
			self.window.HookMessage(self.redraw,WM_REDRAW)
		self._playBuilder.Run()
		self._playBuilder.SetVisible(1)
		self.register_for_timeslices()
		self.__playdone=0
		self.window.PostMessage(WM_REDRAW)


#		if self.play_loop == 0 and duration == 0:
#			self.__playdone=1
#			self.playdone(0)


	def arm_display(self,node):
		if debug: print 'NTVideoChannel arm_display'
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
		self.armed_display.drawvideo(self.update)

	def set_arm_display(self):
		if self.armed_display and self.armed_display.is_closed():
			# assume that we are going to get a
			# resize event
			pass
		else:
			self.armed_display.render()
		if hasattr(self,'played_display') and self.played_display:
			self.played_display.close()
		self.played_display = self.armed_display
		self.armed_display = None
	
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
		if self._playBuilder:
			self._playBuilder.Stop()
			self._playBuilder.SetVisible(0)
			self._playBuilder.SetWindowNull()
			for n in self._builders.keys():
				if self._builders[n]==self._playBuilder:
					del self._builders[n]
					break
			self._playBuilder.Release()
			self._playBuilder=None
		if self._bmp:self._bmp=None
		ChannelWindow.stopplay(self, node)

	def playstop(self):
		ChannelWindow.playstop(self)
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
			if t_msec>=self._playDuration:self.OnMediaEnd()

	def OnMediaEnd(self):
		if debug: print 'VideoChannel: OnMediaEnd',`self`
		if not self._playBuilder:
			return		
		if self.play_loop:
			self.play_loop = self.play_loop - 1
			if self.play_loop: # more loops ?
				self._playBuilder.SetPosition(0)
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
			if t_msec>=self._playDuration:self.OnMediaEnd()

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


	################################# general url stuff
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
