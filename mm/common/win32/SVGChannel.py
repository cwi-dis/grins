__version__ = "$Id$"

#
#	SVGChannel
#

import Channel
import MMurl

import svgdom

import windowinterface

import MMAttrdefs

class SVGChannel(Channel.ChannelWindow):
	def __init__(self, name, attrdict, scheduler, ui):
		Channel.ChannelWindow.__init__(self, name, attrdict, scheduler, ui)
		self.svgdstrect = None
		self.svgsrcrect = None
		self.svgorgsize = None
		self.svgdds = None
		self.svgplayer = None
		self.svgbgcolor = 255, 255, 255
		 
	def __repr__(self):
		return '<SVGChannel instance, name=' + `self._name` + '>'
	
	def do_hide(self):
		Channel.ChannelWindow.do_hide(self)

	def destroy(self):
		del self.svgdds
		Channel.ChannelWindow.destroy(self)
	
	def do_arm(self, node, same=0):
		if node.type != 'ext':
			self.errormsg(node, 'Node must be external')
			return 1
		
		url = self.getfileurl(node)
		if not url:
			self.errormsg(node, 'No URL set on node')
			return 1
		
		if svgdom.doccache.hasdoc(url):
			svgdoc = svgdom.doccache.getDoc(url)
		else:
			try:
				u = MMurl.urlopen(url)
			except IOError, arg:
				if type(arg) is type(self):
					arg = arg.strerror
				self.errormsg(node, 'Cannot resolve URL "%s": %s' % (f, arg))
				return 1
			
			source = u.read()
			u.close()
			svgdoc = svgdom.SvgDocument(source)
			svgdom.doccache.cache(url, svgdoc)
		
		self.svgbgcolor = self.getbgcolor(node)
		if self.window and svgdoc:
			coordinates = self.getmediageom(node)
			self.svgdstrect = left, top, width, height = self.window._convert_coordinates(coordinates)
			self.svgorgsize = svgdom.GetSvgDocSize(svgdoc)
			self.svgsrcrect = 0, 0, width, height # promise for svg scaling
			self.svgdds = self.window.createDDS(width, height)
			self.renderOn(self.svgdds, svgdoc, update=0)
			if svgdoc.hasTiming():
				rendercb = (self.renderOn, (self.svgdds, svgdoc))
				self.svgplayer = svgdom.SVGPlayer(svgdoc, windowinterface.toplevel, rendercb)
			fit = MMAttrdefs.getattr(node, 'fit')
			self.window.setmediadisplayrect(self.svgdstrect)
			self.window.setmediafit(fit)
		return 1

	def do_play(self, node):
		if self.window and self.svgdds:
			self.window.setredrawdds(self.svgdds, self.svgdstrect, self.svgsrcrect)
			self.window.update(self.window.getwindowpos())
			if self.svgplayer:
				self.svgplayer.play()

	def stopplay(self, node):
		if self.window:
			self.window.setredrawdds(None)
			if self.svgplayer:
				self.svgplayer.stop()
				self.svgplayer = None
			self.svgdds = None
		Channel.ChannelWindow.stopplay(self, node)
	
	def setpaused(self, paused):
		Channel.ChannelWindow.setpaused(self, paused)
		if self.svgplayer:
			if paused:
				self.svgplayer.pause()
			else:
				self.svgplayer.resume()
						
	def renderOn(self, dds, svgdoc, update = 1):
		import svgrender, svgwin
		svggraphics = svgwin.SVGWinGraphics()
		sw, sh = self.svgorgsize
		if sw and sh:
			dw, dh = self.svgdstrect[2:]
			sx, sy = dw/float(sw), dh/float(sh)
			svggraphics.applyTfList([('scale',[sx, sy]),])
		ddshdc = dds.GetDC()
		svggraphics.tkStartup(ddshdc)
		renderer = svgrender.SVGRenderer(svgdoc, svggraphics, self.svgdstrect, self.svgbgcolor)
		renderer.render()
		svggraphics.tkShutdown()
		dds.ReleaseDC(ddshdc)
		if update:
			self.window.update(self.window.getwindowpos())

###################################
# SVG channel alt using an OS window and Adobe's SVG viewer

# flag indicating SVG support
import windowinterface

class SVGOsChannel(Channel.ChannelWindow):
	HAS_SVG_SUPPORT = windowinterface.HasSvgSupport()
	def __init__(self, name, attrdict, scheduler, ui):
		Channel.ChannelWindow.__init__(self, name, attrdict, scheduler, ui)

	def __repr__(self):
		return '<SVGChannel instance, name=' + `self._name` + '>'
	
	def do_hide(self):
		if self.window and hasattr(self.window,'DestroySvgCtrl'):
			self.window.DestroySvgCtrl()
		Channel.ChannelWindow.do_hide(self)

	def destroy(self):
		if self.window and hasattr(self.window,'DestroySvgCtrl'):
			self.window.DestroySvgCtrl()
		Channel.ChannelWindow.destroy(self)
	
	def do_arm(self, node, same=0):
		if node.type != 'ext':
			self.errormsg(node, 'Node must be external')
			return 1
		f = self.getfileurl(node)
		if not f:
			self.errormsg(node, 'No URL set on node')
			return 1
		try:
			f = MMurl.urlretrieve(f)[0]
		except IOError, arg:
			if type(arg) is type(self):
				arg = arg.strerror
			self.errormsg(node, 'Cannot resolve URL "%s": %s' % (f, arg))
			return 1
		
		if self.HAS_SVG_SUPPORT: 
			if self.window:
				self.window.CreateOSWindow(svg=1)
				if not self.window.HasSvgCtrl():
					try:
						self.window.CreateSvgCtrl()
					except:
						self.errormsg(node, 'Failed to create SVG control.\nCheck that the control has been installed properly')
					else:
						self.window.SetSvgSrc(f)
		else:
			self.errormsg(node, 'No SVG support detected on this system')
		return 1

	def stopplay(self, node):
		if self.window and hasattr(self.window,'DestroySvgCtrl'):
			self.window.DestroySvgCtrl()
		Channel.ChannelWindow.stopplay(self, node)
		

