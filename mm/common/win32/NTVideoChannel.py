__version__ = "$Id$"

#
# WIN32 Video 
#

# the core
from Channel import *

# common component
import MediaChannel

# node attributes
import MMAttrdefs

# channel types
[SINGLE, HTM, TEXT, MPEG] = range(4)

debug=0

class VideoChannel(ChannelWindowAsync,MediaChannel.MediaChannel):
	node_attrs = ChannelWindowAsync.node_attrs + \
		     ['bucolor', 'hicolor', 'scale', 'center',
		      'clipbegin', 'clipend']
	_window_type = MPEG

	def __init__(self, name, attrdict, scheduler, ui):
		MediaChannel.MediaChannel.__init__(self)
		ChannelWindowAsync.__init__(self, name, attrdict, scheduler, ui)

	def __repr__(self):
		return '<VideoChannel instance, name=' + `self._name` + '>'

	def do_show(self, pchan):
		if not ChannelWindowAsync.do_show(self, pchan):
			return 0
		self.showit(self.window)
		return 1

	def do_hide(self):
		self.release_player()
		ChannelWindowAsync.do_hide(self)

	def destroy(self):
		self.unregister_for_timeslices()
		self.release_player()
		ChannelWindowAsync.destroy(self)
		
	def do_arm(self, node, same=0):
		if debug:print 'Videodo_arm('+`self`+','+`node`+'same'+')'
		if same and self.armed_display:
			return 1
		if node.type != 'ext':
			self.errormsg(node, 'Node must be external')
			return 1
		self.arm_display(node)
		if not self.prepare_player(node):
			self.showwarning(node,'System missing infrastructure to playback')
		return 1

	def do_play(self, node):
		if debug:print 'Videodo_play('+`self`+','+`node`+')'
		self.playit(node,self.window)

	# Part of stop sequence. Stop and remove last frame 
	def stopplay(self, node):
		self.stopit()
		#if hasattr(self,'_bmp') and self._bmp:self._bmp=None
		ChannelWindowAsync.stopplay(self, node)

	def playstop(self):
		ChannelWindowAsync.playstop(self)
		if self.window:
			self.window.RedrawWindow()

	# toggles between pause and run
	def setpaused(self, paused):
		self.pauseit(paused)

	def defanchor(self, node, anchor, cb):
		import windowinterface
		windowinterface.showmessage('The whole window will be hot.')
		cb((anchor[0], anchor[1], [0,0,1,1]))


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
		if not hasattr(self,'_bmp'):self._bmp=None
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
			if hasattr(self,'_bmp') and self._bmp: 
				win32mu.BitBltBmp(dc,self._bmp,self.window.GetClientRect())
