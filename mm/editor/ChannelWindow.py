# Generic channel window

import gl, GL, DEVICE
import fl

from Dialog import GLDialog

class ChannelWindow(GLDialog):

	def init(self, (name, attrdict, channel)):
		self.name = name
		self.attrdict = attrdict
		self.channel = channel
		self.node = None
		return GLDialog.init(self, name)

	def show(self):
		if self.is_showing():
			self.pop()
			return
		GLDialog.show(self)
		# Use RGB mode
		gl.RGBmode()
		gl.gconfig()
		fl.qdevice(DEVICE.RIGHTMOUSE)

	def load_geometry(self):
		# Get the window size
		if self.attrdict.has_key('winsize'):
			width, height = self.attrdict['winsize']
		else:
			width, height = 0, 0
		# Get the window position
		if self.attrdict.has_key('winpos'):
			h, v = self.attrdict['winpos']
		else:
			h, v = -1, -1
		self.last_geometry = h, v, width, height

	def save_geometry(self):
		self.get_geometry() # Make sure last_geometry is up-to-date
		if self.last_geometry:
			h, v, width, height = self.last_geometry
			# XXX transaction!
			self.attrdict['winpos'] = h, v
			self.attrdict['winsize'] = width, height

	def mouse(self, (dev, val)):
		if dev == DEVICE.RIGHTMOUSE:
			if self.node == None:
				self.channelmenu()
			else:
				self.nodemenu()

	def channelmenu(self):
		global cmenu
		if cmenu == None:
			cmenu = make_cmenu()
		self.domenu(cmenu)

	def domenu(self, (menu, actions)):
		i = gl.dopup(menu)
		if 0 < i <= len(actions):
			actions[i-1](self)

	def nodemenu(self):
		global nmenu
		if nmenu == None:
			nmenu = make_nmenu()
		self.domenu(nmenu)

cmenu = None
nmenu = None

def newmenu(title):
	menu, actions = gl.newpup(), []
	gl.addtopup(menu, title + '%t', 0)
	return menu, actions

def addtomenu((menu, actions), text, func):
	gl.addtopup(menu, text, 0)
	actions.append(func)

def make_cmenu():
	mdef = newmenu('Channel Menu')
	addtomenu(mdef, 'Channel attr...', do_channel_attr)
	return mdef

def make_nmenu():
	mdef = newmenu('Channel + Node Menu')
	addtomenu(mdef, 'Channel attr...%l', do_channel_attr)
	addtomenu(mdef, 'Play node...%l', do_node_play)
	addtomenu(mdef, 'Node info...', do_node_info)
	addtomenu(mdef, 'Node attr...', do_node_attr)
	addtomenu(mdef, 'Edit contents...', do_node_edit)
	addtomenu(mdef, 'Edit anchors...%l', do_node_anchors)
	addtomenu(mdef, 'Push focus', do_node_focus)
	return mdef

def do_channel_attr(cwin):
	import AttrEdit
	AttrEdit.showchannelattreditor(cwin.channel.player.context, cwin.name)

def do_node_play(cwin):
	cwin.channel.player.playsubtree(cwin.node)

def do_node_info(cwin):
	import NodeInfo
	NodeInfo.shownodeinfo(cwin.channel.player.toplevel, cwin.node)

def do_node_attr(cwin):
	import AttrEdit
	AttrEdit.showattreditor(cwin.node)

def do_node_edit(cwin):
	import NodeEdit
	NodeEdit.showeditor(cwin.node)

def do_node_anchors(cwin):
	import AnchorEdit
	AnchorEdit.showanchoreditor(cwin.channel.player.toplevel, cwin.node)

def do_node_focus(cwin):
	cwin.channel.player.toplevel.blockview.globalsetfocus(cwin.node)
	cwin.channel.player.toplevel.channelview.globalsetfocus(cwin.node)

# XXX should add "Hide channel"?
