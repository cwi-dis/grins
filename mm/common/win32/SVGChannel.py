__version__ = "$Id$"

#
#	SVGChannel
#

import Channel
import MMurl

class SVGChannel(Channel.ChannelWindow):
	def __init__(self, name, attrdict, scheduler, ui):
		Channel.ChannelWindow.__init__(self, name, attrdict, scheduler, ui)
		self.svgdstrect = None
		self.svgsrcrect = None
		self.svgdds = None

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
		
		try:
			u = MMurl.urlopen(url)
		except IOError, arg:
			if type(arg) is type(self):
				arg = arg.strerror
			self.errormsg(node, 'Cannot resolve URL "%s": %s' % (f, arg))
			return 1

		source = u.read()
		u.close()
		
		if self.window and source:
			coordinates = self.getmediageom(node)
			self.svgdstrect = left, top, width, height = self.window._convert_coordinates(coordinates)
			self.svgsrcrect = 0, 0, width, height
			self.svgdds = self.window.createDDS(width, height)
			self.renderOn(self.svgdds, source)
		return 1

	def do_play(self, node):
		if self.window and self.svgdds:
			self.window.setredrawdds(self.svgdds, self.svgdstrect, self.svgsrcrect)
			self.window.update(self.svgdstrect)

	def stopplay(self, node):
		if self.window:
			self.window.setredrawdds(None)
			self.svgdds = None
		Channel.ChannelWindow.stopplay(self, node)
		
	def renderOn(self, dds, source):
		import svgdom, svgrender, svgwin
		svgdoc = svgdom.SvgDocument(source)
		svggraphics = svgwin.SVGWinGraphics()
		ddshdc = dds.GetDC()
		svggraphics.tkStartup(ddshdc)
		renderer = svgrender.SVGRenderer(svgdoc, svggraphics)
		renderer.render()
		svggraphics.tkShutdown()
		dds.ReleaseDC(ddshdc)


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
		

