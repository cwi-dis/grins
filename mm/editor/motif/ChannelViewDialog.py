from ViewDialog import ViewDialog
import windowinterface
import WMEVENTS
import MMAttrdefs

begend = ('begin', 'end')

class ChannelViewDialog(ViewDialog):

	def __init__(self):
		ViewDialog.__init__(self, 'cview_')

	def show(self, title):
		self.load_geometry()
		x, y, w, h = self.last_geometry
		self.window = windowinterface.newcmwindow(x, y, w, h, title, pixmap=1, canvassize = (w, h))
		if self.waiting:
			self.window.setcursor('watch')
		self.window.register(WMEVENTS.Mouse0Press, self.mouse, None)
		self.window.register(WMEVENTS.ResizeWindow, self.resize, None)
		self.window.register(WMEVENTS.WindowExit, self.hide, None)

	def hide(self, *rest):
		self.save_geometry()
		self.window.close()
		self.window = None
		self.displist = self.new_displist = None

	def setcommands(self, commandlist, title):
		self.window.create_menu(commandlist, title = title)


class GOCommand:
	def __init__(self):
		self.commandlist = c = []
		c.append('h', 'Help...', (self.helpcall, ()))
		c.append('', 'Canvas', [
			('', 'Double height',
			 (self.canvascall, (windowinterface.DOUBLE_HEIGHT,))),
			('', 'Double width',
			 (self.canvascall, (windowinterface.DOUBLE_WIDTH,))),
			('', 'Reset',
			 (self.canvascall, (windowinterface.RESET_CANVAS,)))])
		c.append('n', 'New channel...',  (self.newchannelcall, ()))
		c.append('N', 'Next mini-document', (self.nextminicall, ()))
		c.append('P', 'Previous mini-document', (self.prevminicall, ()))
		c.append('',  'Ancestors', self.ancestors)
		c.append('', 'Siblings', self.siblings)
		c.append('', 'Descendants', self.descendants)
		c.append('T', 'Toggle unused channels', (self.toggleshowcall, ()))
		self.menutitle = 'Base ops'

	# from ChanelView
	def helpcall(self):
		import Help
		Help.givehelp(self.mother.window._hWnd,'Channel_view')


class ChannelBoxCommand:
	def __init__(self):
		c = self.commandlist
		c.append(None)
## 		c.append('i', '', (self.attrcall, ()))
		c.append('a', 'Channel attr...', (self.attrcall, ()))
		c.append('d', 'Delete channel',  (self.delcall, ()))
		c.append('m', 'Move channel', (self.movecall, ()))
		c.append('c', 'Copy channel', (self.copycall, ()))
		c.append(None)
		c.append('', 'Toggle on/off', (self.channel_onoff, ()))
		c.append(None)
		c.append('', 'Highlight window', (self.highlight, ()))
		c.append('', 'Unhighlight window', (self.unhighlight, ()))
		self.menutitle = 'Channel ' + self.name + ' ops'

class NodeBoxCommand:
	def __init__(self, mother, node):
		c = self.commandlist
		c.append(None)
		c.append('p', 'Play node...', (self.playcall, ()))
		c.append('G', 'Play from here...', (self.playfromcall, ()))
		c.append('f', 'Push focus', (self.focuscall, ()))
		c.append(None)
		c.append('s', 'Finish sync arc...', (self.newsyncarccall, ()))
		c.append('L', 'Finish hyperlink...', (self.hyperlinkcall, ()))
		c.append(None)
		c.append('i', 'Node info...', (self.infocall, ()))
		c.append('a', 'Node attr...', (self.attrcall, ()))
		c.append('e', 'Edit contents...', (self.editcall, ()))
		c.append('t', 'Edit anchors...', (self.anchorcall, ()))
		arcmenu = []
		for arc in MMAttrdefs.getattr(node, 'synctolist'):
			xuid, xside, delay, yside = arc
			try:
				xnode = node.MapUID(xuid)
			except NoSuchUIDError:
				# Skip sync arc from non-existing node
				continue
			if xnode.FindMiniDocument() is mother.viewroot:
				xname = MMAttrdefs.getattr(xnode, 'name')
				if not xname:
					xname = '#' + xuid
				arcmenu.append('', 'From %s of node "%s" to %s of self' % (begend[xside], xname, begend[yside]), (self.selsyncarc, (xnode, xside, delay, yside)))
		if arcmenu:
			c.append('', 'Select sync arc', arcmenu)
		self.menutitle = 'Node ' + self.name + ' ops'

class ArcBoxCommand:
	def __init__(self):
		c = self.commandlist
		c.append(None)
		c.append('i', 'Sync arc info...', (self.infocall, ()))
		c.append('d', 'Delete sync arc',  (self.delcall, ()))
		self.menutitle = 'Sync arc ' + self.name + ' ops'

