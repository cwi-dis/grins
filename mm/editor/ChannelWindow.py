# Generic channel window

import gl, GL, DEVICE
import fl

from Dialog import GLDialog

ChannelWinDict = {}

class ChannelWindow(GLDialog):

	def init(self, name, attrdict, channel):
		global ChannelWinDict
		self.name = name
		self.attrdict = attrdict
		self.channel = channel
		self.node = None
		self.cmenu = None
		self.nmenu = None
		self.sqq_square = None
		ChannelWinDict[name] = self
		return GLDialog.init(self, name)

	def __repr__(self):
		return '<ChannelWindow instance, name=' + `self.name` + '>'

	def show(self):
		if self.is_showing():
			self.pop()
			return
		pwid = 0
		if self.attrdict.has_key('base_window'):
			pname = self.attrdict['base_window']
			try:
				pchan = ChannelWinDict[pname]
				pwid = pchan.wid
			except:
				pass
		pgeom = None
		if self.attrdict.has_key('base_winoff'):
			pgeom = self.attrdict['base_winoff']
		if pwid and pgeom == None:
			# Place interactively
			if self.attrdict.has_key('winsize'):
				w, h = self.attrdict['winsize']
			else:
				w, h = 0, 0
			import AdefDialog
			pchan.pop()
			keep_mouse = pchan.mouse
			pchan.mouse = pchan.sqqmouse
			pchan.sqqstart((0,0,w,h))
			AdefDialog.window(self.name)
			sq = pchan.sqqend()
			pchan.mouse = keep_mouse
			# Now convert from GL coordinates to X precentages
			pgeom = pchan.sqconvert(sq)
			self.attrdict['base_winoff'] = pgeom
		if pgeom:
			if pgeom[0] < 0 or pgeom[0] > 1 or \
				  pgeom[1] < 0 or pgeom[1] > 1 or \
				  pgeom[2] < 0 or pgeom[1] > 1 or \
				  pgeom[3] < 0 or pgeom[3] > 1:
				print 'Warning: channel',self.name,
				print 'extends outside parent window'
		GLDialog.setparent(self, pwid, pgeom)
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

	def mouse(self, dev, val):
		if dev == DEVICE.RIGHTMOUSE:
			if self.node == None:
				self.channelmenu()
			else:
				self.nodemenu()
		else:
			self.sqqmouse(dev, val)

	def channelmenu(self):
		if self.cmenu == None:
			self.cmenu = make_cmenu(self.name)
		self.domenu(self.cmenu)

	def domenu(self, mdef):
		menu, actions = mdef
		i = gl.dopup(menu)
		if 0 < i <= len(actions):
			actions[i-1](self)

	def nodemenu(self):
		if self.nmenu == None:
			self.nmenu = make_nmenu(self.name)
		self.domenu(self.nmenu)

	# Stuff to allow input of squares by the user
	def sqqstart(self, sq):
		if self.sqq_square:
			raise 'sqqstart while already querying'
		if not sq:
			sq = [0,0,0,0]
		self.sqq_square = sq[0], sq[1], sq[2], sq[3]
		fl.qdevice(DEVICE.MIDDLEMOUSE)
		self.sqqredraw()

	def sqqend(self):
		rv = self.sqq_square
		self.sqq_square = None
		self.sqqredraw()
		return rv

	def sqqredraw(self):
		gl.drawmode(GL.PUPDRAW)
		gl.color(0)
		gl.clear()
		if self.sqq_square:
			gl.mapcolor(1, 255, 0, 0)	# Always use red...
			gl.color(1)
			x0, y0, x1, y1 = self.sqq_square
			gl.bgnclosedline()
			gl.v2i(x0, y0)
			gl.v2i(x0, y1)
			gl.v2i(x1, y1)
			gl.v2i(x1, y0)
			gl.endclosedline()
		gl.drawmode(GL.NORMALDRAW)

	def sqqmouse(self, dev, val):
		if not self.sqq_square:
			return
		if val == 1:
			# Mouse down.
			mx, my = fl.get_mouse()
			mx, my = int(mx), int(my)
			if dev == DEVICE.MIDDLEMOUSE:
				# Drag mode: drag fixed-size square around
				self.sqq_dragmode = 1
				x0, y0, x1, y1 = self.sqq_square
				w, h = abs(x0-x1), abs(y0-y1)
				self.sqq_square = mx, my, mx+w, my+h
			else:
				# Resize mode: make square at this corner
				self.sqq_dragmode = 0
				self.sqq_square = mx, my, mx+4, my+4
			self.sqqredraw()
			self.sqqloop()
		else:
			raise 'Mouse-up event without mouse-down?'

	def sqqloop(self):
		om = fl.get_mouse()
		while 1:
			if fl.qtest():
				dev, val = fl.qread()
				if dev not in (DEVICE.MIDDLEMOUSE, \
					  DEVICE.LEFTMOUSE) or val == 1:
					print 'sqqloop: drop event', dev, val
				else:
					return
			else:
				gl.gsync()
			m = fl.get_mouse()
			if m <> om:
				self.sqqnewxy(m)
			
	def sqqnewxy(self, m):
		mx, my = m
		if not self.sqq_square:
			raise 'Mouse-move event while not sq-querying?'
		mx, my = int(mx), int(my)
		x0, y0, x1, y1 = self.sqq_square
		if self.sqq_dragmode:
			w, h = abs(x0-x1), abs(y0-y1)
			self.sqq_square = mx, my, mx+w, my+h
		else:
			self.sqq_square = x0, y0, mx, my
		self.sqqredraw()

	# sqconvert converts GL xyxy to X-style (0,0 top left) percentages
	def sqconvert(self, sq):
		x0, y0, x1, y1 = sq
		gl.winset(self.wid)
		w, h = gl.getsize()
		if x0 > x1: x0, x1 = x1, x0
		if y0 > y1: y0, y1 = y1, y0
		if x0 < 0: x0 = 0
		if y0 < 0: y0 = 0
		if x1 > w: x1 = w
		if y1 > h: y1 = h
		x0 = float(x0)/w
		x1 = float(x1)/w
		y0 = (h - float(y0))/h
		y1 = (h - float(y1))/h
		return x0, y1, x1-x0, y0-y1
		


def newmenu(title):
	menu, actions = gl.newpup(), []
	gl.addtopup(menu, title + '%t', 0)
	return menu, actions

def addtomenu((menu, actions), text, func):
	gl.addtopup(menu, text, 0)
	actions.append(func)

def make_cmenu(name):
	mdef = newmenu(name +' Menu')
	addtomenu(mdef, 'Channel attr...', do_channel_attr)
	return mdef

def make_nmenu(name):
	mdef = newmenu(name + ' Node Menu')
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
	cwin.channel.player.toplevel.hierarchyview.globalsetfocus(cwin.node)
	cwin.channel.player.toplevel.channelview.globalsetfocus(cwin.node)

# XXX should add "Hide channel"?
