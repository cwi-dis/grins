__version__ = "$Id$"

#
#	SVGChannel
#

import Channel
import MMurl

# flag indicating SVG support
import windowinterface
HAS_SVG_SUPPORT = windowinterface.HasSvgSupport()

class SVGChannel(Channel.ChannelWindow):
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
		
		if HAS_SVG_SUPPORT: 
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
		

