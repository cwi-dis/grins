from ViewDialog import ViewDialog
import windowinterface
import WMEVENTS
import MMAttrdefs
import UserCmd

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
		self.window.set_commandlist(commandlist)

class GOCommand:
	def __init__(self):
		self.commandlist = c = [
			(UserCmd.CANVAS_HEIGHT, (self.canvascall,
					(windowinterface.DOUBLE_HEIGHT,))),
			(UserCmd.CANVAS_WIDTH, (self.canvascall,
					(windowinterface.DOUBLE_WIDTH,))),
			(UserCmd.CANVAS_RESET, (self.canvascall,
					(windowinterface.RESET_CANVAS,))),

			(UserCmd.NEW_CHANNEL,  (self.newchannelcall, ())),

			(UserCmd.NEXT_MINIDOC, (self.nextminicall, ())),
			(UserCmd.PREV_MINIDOC, (self.prevminicall, ())),
##		c.append('',  'Ancestors', self.ancestors)
##		c.append('', 'Siblings', self.siblings)
##		c.append('', 'Descendants', self.descendants)
			(UserCmd.TOGGLE_UNUSED, (self.toggleshowcall, ()))]
		self.menutitle = 'Base ops'

class ChannelBoxCommand:
	def __init__(self):
		c = self.commandlist


		c.append(UserCmd.ATTRIBUTES, (self.attrcall, ()))
		c.append(UserCmd.DELETE,  (self.delcall, ()))
		c.append(UserCmd.MOVE_CHANNEL, (self.movecall, ()))
		c.append(UserCmd.COPY_CHANNEL, (self.copycall, ()))

		c.append(UserCmd.TOGGLE_ONOFF, (self.channel_onoff, ()))

##		c.append('', 'Highlight window', (self.highlight, ()))
##		c.append('', 'Unhighlight window', (self.unhighlight, ()))
		self.menutitle = 'Channel ' + self.name + ' ops'

class NodeBoxCommand:
	def __init__(self, mother, node):
		c = self.commandlist

		c.append(UserCmd.PLAYNODE, (self.playcall, ()))
		c.append(UserCmd.PLAYFROM, (self.playfromcall, ()))
		c.append(UserCmd.PUSHFOCUS, (self.focuscall, ()))

		c.append(UserCmd.FINISH_ARC, (self.newsyncarccall, ()))
		c.append(UserCmd.FINISH_LINK, (self.hyperlinkcall, ()))
		c.append(UserCmd.INFO, (self.infocall, ()))
		c.append(UserCmd.ATTRIBUTES, (self.attrcall, ()))
		c.append(UserCmd.CONTENT, (self.editcall, ()))
		c.append(UserCmd.ANCHORS, (self.anchorcall, ()))
##		arcmenu = []
##		for arc in MMAttrdefs.getattr(node, 'synctolist'):
##			xuid, xside, delay, yside = arc
##			try:
##				xnode = node.MapUID(xuid)
##			except NoSuchUIDError:
##				# Skip sync arc from non-existing node
##				continue
##			if xnode.FindMiniDocument() is mother.viewroot:
##				xname = MMAttrdefs.getattr(xnode, 'name')
##				if not xname:
##					xname = '#' + xuid
##				arcmenu.append('', 'From %s of node "%s" to %s of self' % (begend[xside], xname, begend[yside]), (self.selsyncarc, (xnode, xside, delay, yside)))
##		if arcmenu:
##			c.append('', 'Select sync arc', arcmenu)
##		self.menutitle = 'Node ' + self.name + ' ops'

class ArcBoxCommand:
	def __init__(self):
		c = self.commandlist
		c.append(None)
		c.append(UserCmd.INFO, (self.infocall, ()))
		c.append(UserCmd.DELETE,  (self.delcall, ()))
		self.menutitle = 'Sync arc ' + self.name + ' ops'

