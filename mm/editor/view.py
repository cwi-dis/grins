import fl
import gl
#from GL import *
#from gl import *
from figures import *
#import DEVICE
from ArcEdit import *
import MMAttrdefs
#import Timing

# the view class.
#
# There are two methods :
#	1. new (w, h, root) which returns the form and a box which
#	   acts as a "canvas" over the form. w, h are the width and height.
#	2. view(form, (x, y, w, h), node) which makes the channelview.
#	   node is a node in the tree.

# some constants that can be used to expiriment with how the
# blocks are placed on top of each other.
#
XMARG = 10 # margin width
YMARG = 5 # two time the  margin width
THERMW = 50
HDR_SIZE = 100 # header size for diamonds
B=5	# the size of the round button

# Some special constants
F_NONE = 0 # No focus
F_NODE = 1 # Focus on node
F_CHAN = 2 # Focus on channel
F_ARC  = 3 # Focus on timing arc

class view () :
	#
	# new makes an object of type 'channelview'
	#
	# if does :
	#	0. initializes some state
	#	1. makes the form
	#	2. initializes the command dict / command callbak
	#	3. initializes the commandarea (Help, File, ...)
	#	4. sets up the channelview
	#

	def new (self, (w, h, toplevel, debug)) :
		self._init(w, h)
		self.debug = debug
		#
		area = box().new(FOCUS_BOX,0,0,w,h,'')

		self.toplevel = toplevel
		self.root = root = toplevel.root
		self.editmgr = root.context.geteditmgr()
		self.editmgr.register(self)
		self.rootview = root
		self._initcommanddict()
		self.channellist = []
		self.arrowlist = []
#		Timing.calctimes(root)
	 	duration = self.calcDuration(root) # for channel headers
#		self.channellist.sort()
		self.channellist = root.context.channelnames
		self.nrchannels = len(self.channellist)
		self.chanboxes = []
		self.thermleft = w - THERMW
		w = w / 2
		self.unitwidth = (w - THERMW) / max(1, self.nrchannels)
		self.unitheight = (h - HDR_SIZE) / max(1.0, root.t1)
		self.thermo = thermo().new(self.thermleft + XMARG, \
			YMARG, THERMW - XMARG * 2, h - HDR_SIZE - YMARG * 2)
		self.currenttime = 0
		self.dividor = w
		xi = w + XMARG
		wi = self.unitwidth - XMARG*2
		hi = HDR_SIZE - YMARG*2
		yi = h - YMARG - hi
		li = h - YMARG*2 - hi
		for i in range(self.nrchannels):
			self.chanboxes.append(diamond().\
				new(xi,yi,wi,hi,li,self.channellist[i]))
			xi = xi + self.unitwidth
		self.mkView((0,0,w,h,h-HDR_SIZE),root)
		self.mkArrows(root)
		self.focuskind = F_NONE
		self.focus = None
		self.locked_focus = None
		return self

	def transaction(self):
		return 1 # always allow transactions
	def commit(self):
#XXX how long takes a redraw?
		self.redrawfunc()
	def rollback(self):
		return # can we do something useful?

	def recalc(self):
#		Timing.calctimes(self.root)
		self.unitheight = (self.h - HDR_SIZE) / max(1.0, self.root.t1)
		for i in range(self.nrchannels):
			self.chanboxes[i].label = self.channellist[i]
		self.re_mkView((0,0,self.w / 2,self.h,self.h-HDR_SIZE),\
			self.root)
		for arrow in self.arrowlist:
			self.mod_arrow(arrow)

	#
	# addtocommand adds a command to the commanddictionary.
	# Anybody can submit their own commands
	#
	def addtocommand(self, (key, func, helpstr)) :
		self.commanddict[key] = (func, helpstr)

	#
	# submit a number to default commands.
	#
	def _initcommanddict(self) :
		self.addtocommand('a', attreditfunc, 'attribute editor')
		self.addtocommand('c', channeleditfunc, 'channel editor')
		self.addtocommand('d', deletearrow, 'delete timing arc')
		self.addtocommand('h', helpfunc, 'help message')
		self.addtocommand('l', lock_focus, 'lock current focus')
		self.addtocommand('m', modify_arrow, 'modify timing arc')
		self.addtocommand('o', infofunc, 'open node info window')
		self.addtocommand('p', play_focus, 'play current focus')
		self.addtocommand('r', redrawfunc, 'redraw')
		self.addtocommand('t', add_arrow, 'add timing arc')
		self.addtocommand('u', unlock_focus, 'unfocus locked focus')
	#

	def pupmenu(self, (x, y)):
		menu = gl.newpup()
		gl.addtopup(menu, 'menu %t', 0)
		gl.addtopup(menu, '%l', 0)
		gl.addtopup(menu, 'help %x3', 0)
		if self.focuskind <> F_NONE:
			gl.addtopup(menu, 'edit %x1', 0)
		if self.focuskind = F_NODE:
			gl.addtopup(menu, 'info %x5', 0)
			gl.addtopup(menu, 'play %x6', 0)
			if self.locked_focus <> None:
				gl.addtopup(menu, 'add arc %x8', 0)
		if self.focuskind = F_ARC:
			gl.addtopup(menu, 'delete %x2', 0)
		if self.focuskind = F_NODE:
			gl.addtopup(menu, 'lock %x4', 0)
		if self.locked_focus <> None:
			gl.addtopup(menu, 'unlock %x9', 0)
		gl.addtopup(menu, 'redraw %x7', 0)
		val = gl.dopup(menu)
		gl.freepup(menu)
		if val = 1:
			attreditfunc(self)
		elif val = 2:
			deletearrow(self)
		elif val = 3:
			helpfunc(self)
		elif val = 4:
			lock_focus(self)
		elif val = 5:
			infofunc(self)
		elif val = 6:
			play_focus(self)
		elif val = 7:
			redrawfunc(self)
		elif val = 8:
			add_arrow(self)
		elif val = 9:
			unlock_focus(self)

	# calcDuration calculates the duration of each node, moreover it
	# maintains a list of channels used.

	def calcDuration(self, node):
		type = node.GetType()
		node.duration = 0

		text = node.GetInherAttrDef('channel', '?'+type+'?')
		if text[:1] <> '?':
			if text not in self.channellist:
				self.channellist.append(text)

		kids = node.GetChildren()
		if type in ('seq','par','grp') and len(kids) > 0:
			for child in kids :
				newduration = self.calcDuration(child)
				if type in ('seq','grp'):
					node.duration = node.duration + newduration
				else:
					if newduration > node.duration:
						node.duration = newduration
		else:
			node.duration = node.GetAttrDef(('duration', 2))
		return node.duration

	# channelview gets a region in the form where it recursively
	#  places a node in this region; (x, y, w, h).
	#

	def mkView(self, ((x,y,w,h,h1), node)):
		text = node.GetInherAttrDef('channel', '?')
		name = node.GetAttrDef('name', 'NoName')
		type = node.GetType()
		kids = node.GetChildren()
		blobj = box().new(FOCUS_BOX,x,y,w,h,'')
		blobj.label = name
		blobj.boxtype = FG_BOX
		blobj.hidden = 1 - self.debug
		node.ch_blockobj = blobj
		if type in ('seq','par','grp'):
			text = ''
			left = self.dividor
			right = self.nrchannels * self.unitwidth + self.dividor
			kind = BG_BOX
		else:
			index = self.channellist.index(text)
			left = self.unitwidth * index + XMARG + self.dividor
			right = self.unitwidth * (index + 1) - XMARG + self.dividor
			kind = FG_BOX
		top = h1 - YMARG
		duration = node.t1 - node.t0
		bottom = top - self.unitheight * duration + YMARG * 2
		if bottom > top:
			bottom = top
		chobj = box().new(FOCUS_BOX,left,bottom,right-left,top-bottom,'')
		if type in ('seq','par','grp'):
			chobj.hidden = 1
		chobj.label = name
		chobj.boxtype = kind
		chobj.x = left
		chobj.w = right - left
		chobj.y = bottom
		chobj.h = top - bottom
		node.ch_channelobj = chobj
		if type in ('seq','par','grp') and len(kids) > 0:
                        if type in ('grp', 'seq') :
				y = y + h
                                h = h / len(kids)
                                dx, dy = 0, -h
				y = y - h
                        else:                            # parallel node
                                w = w / len(kids)
                                dx, dy = w, 0
                        x,y,w,h = x+XMARG,y+YMARG,w-2*XMARG,h-2*YMARG


			for child in kids :
				childh1 = h1 - (child.t0 - node.t0) * self.unitheight
				self.mkView((x,y,w,h,childh1), child)
				x, y = x + dx, y + dy

	def re_mkView(self, ((x,y,w,h,h1), node)):
		text = node.GetInherAttrDef('channel', '?')
		type = node.GetType()
		name = node.GetAttrDef('name', 'NoName')
		kids = node.GetChildren()
		try:
			blobj = node.ch_blockobj
		except NameError:	# a newly created node!
			blobj = box().new(FOCUS_BOX,x,y,w,h,'')
			blobj.boxtype = FG_BOX
			blobj.hidden = 1 - self.debug
			node.ch_blockobj = blobj
		blobj.label = name
		if type in ('seq','par','grp'):
			left = self.dividor
			right = self.nrchannels * self.unitwidth + self.dividor
		else:
			index = self.channellist.index(text)
			left = self.unitwidth * index + XMARG + self.dividor
			right = self.unitwidth * (index + 1) - XMARG + self.dividor
		top = h1 - YMARG * 2
		duration = node.t1 - node.t0
		bottom = top - self.unitheight * duration + YMARG * 2
		if bottom > top:
			bottom = top
		try:
			chobj = node.ch_channelobj
		except NameError:	# a newly created node!
			chobj = box().new(FOCUS_BOX,left,bottom,right-left,top-bottom,'')
			node.ch_channelobj = chobj
		if type in ('seq','par','grp'):
			chobj.hidden = 1
			kind = BG_BOX
		else:
			kind = FG_BOX
		chobj.boxtype = kind
		chobj.label = name
		chobj.x = left
		chobj.w = right - left
		chobj.y = bottom
		chobj.h = top - bottom
		if type in ('seq','par','grp') and len(kids) > 0:
                        if type in ('grp', 'seq') :
				y = y + h
                                h = h / len(kids)
                                dx, dy = 0, -h
				y = y - h
                        else:                            # parallel node
                                w = w / len(kids)
                                dx, dy = w, 0
                        x,y,w,h = x+XMARG,y+YMARG,w-2*XMARG,h-2*YMARG


			for child in kids :
				childh1 = h1 - (child.t0 - node.t0) * self.unitheight
				self.re_mkView((x,y,w,h,childh1), child)
				x, y = x + dx, y + dy

	def mkArrows(self, node):
		synclist = MMAttrdefs.getattr(node, 'synctolist')
		for i in synclist:
			uid, frompos, delay, topos = i
			j = self.add_arrow_at(self.root.MapUID(uid), node, frompos, delay, topos, 0)
		for i in node.GetChildren():
			self.mkArrows(i)
	#
	# delete all the objects (made by channelview) form the node
	#
	def rmView (self, node) :
		node.ch_blockobj.hidden = 1
		del node.ch_blockobj
		node.ch_channelobj.hidden = 1
		del node.ch_channelobj
		for child in node.GetChildren () :
			self.rmView(child)
	#
	# change_focus_callback
	# called when user clicks on a node to grab the focus
	# the argument is the class 'channelview' itself.
	#
	def setbase(self, (x, y)):
		self.xbase = x
		if self.debug = 0:
			self.xbase = x - self.dividor
		self.ybase = y

	def change_focus (self, (mx, my)) :
		mx, my = mx - self.xbase, my - self.ybase
		for arrow in self.arrowlist:
			if arrow.hotspot(mx, my) = 1:
				self.arrowhit(arrow)
				return
		for diam in self.chanboxes:
			if diam.hotspot(mx, my) = 1:
				self.diamhit(diam)
		node = self._find_node (self.root, (mx, my))
		if node = None:
			return

		if node.ch_blockobj.boxtype <> FG_BOX:
			return
		if mx<self.dividor or node.GetType() not in ('seq','par','grp'):
			self.dounfocus()
			self.setfocus (node)
			self.redraw_node(node)
			for arrow in self.arrowlist:
				arrow.draw()

	def add_focus(self, (mx, my)):
		if self.focuskind <> F_NODE:
			fl.show_message ('No node selected yet','','')
			return
		if self.focus = None:
			self.change_focus(mx, my)
			return
		mx, my = mx - self.xbase, my - self.ybase
		if mx<self.dividor:	# in block view
			return
		node = self._find_node (self.root, (mx, my))
		if node = None:
			return
		if node.GetType() not in ('seq','par','grp'):
			node1 = self._find_node2(self.root, (node.ch_blockobj.x,node.ch_blockobj.y),(self.focus.ch_blockobj.x,self.focus.ch_blockobj.y))
			if node1 = None:
				raise 'view'
			if node1.ch_blockobj.boxtype <> FG_BOX:
				return
			self.unfocus(self.focus)
			self.redraw_node(self.focus)
			self.setfocus(node1)
			self.redraw_node(node1)
			for arrow in self.arrowlist:
				arrow.draw()
	def lock_focus(self):
		if self.focuskind <> F_NODE:
			fl.show_message ('No node selected yet','','')
			return
		if self.locked_focus = self.focus:
			return
		if self.locked_focus <> None:
			fl.show_message ('There is already a locked focus','','')
			return
		node = self.focus
		if node = None:
			return
		if node.ch_blockobj.boxtype <> FOCUS_BOX:
			return
		node.ch_blockobj.boxtype = LOCK_BOX
		self.lockchanfocus(node)
		self.locked_focus = node
		self.focus = None
		self.focuskind = F_NONE
		self.redraw_node(node)
		for arrow in self.arrowlist:
			arrow.draw()
	def unlock_focus(self):
		node = self.locked_focus
		if node = None:
			return
		node.ch_blockobj.boxtype = FG_BOX
		self.unfocuschan(node)
		self.locked_focus = None
		self.redraw_node(node)
		for arrow in self.arrowlist:
			arrow.draw()
	#
	# setfocus
	#
	def dounfocus(self):
		if self.focuskind = F_ARC:
			self.focus.kind = NORM_ARROW
			self.focus.draw()
			self.focus = None
		elif self.focuskind = F_CHAN:
			self.focus.kind = NORM_CHAN
			self.focus.redraw()
			self.focus = None
		elif self.focuskind = F_NODE:
			self.unfocus(self.focus)
			self.redraw_node(self.focus)
		self.focuskind = F_NONE
		self.focus = None
	def setfocus (self, node) :
		self.dounfocus()
		node.ch_blockobj.boxtype = FOCUS_BOX
		if node <> self.root:
			self.setchanfocus (node)
		self.focus = node
		self.focuskind = F_NODE
	def setchanfocus(self, node):
		if node.GetType() in ('seq','par','grp'):
			for child in node.GetChildren():
				self.setchanfocus(child)
		else:
			node.ch_channelobj.boxtype = FOCUS_BOX
	def unfocus (self, node) :
		if node = None:
			return
		node.ch_blockobj.boxtype = FG_BOX
		if node <> self.root:
			self.unchanfocus (node)
		self.focus = node
	def unchanfocus(self, node):
		if node.GetType() in ('seq','par','grp'):
			for child in node.GetChildren():
				self.unchanfocus(child)
		else:
			node.ch_channelobj.boxtype = FG_BOX
	def lockchanfocus(self, node):
		if node.GetType() in ('seq','par','grp'):
			for child in node.GetChildren():
				self.lockchanfocus(child)
		else:
			node.ch_channelobj.boxtype = LOCK_BOX
	def unfocuschan(self, node):
		if node.GetType() in ('seq','par','grp'):
			for child in node.GetChildren():
				self.unfocuschan(child)
		else:
			node.ch_channelobj.boxtype = FG_BOX
	#
	# timing arcs
	#
	def add_arrow(self):
		if not self.editmgr.transaction():
			fl.show_message('Not able to add timing arc','','')
			return
		if self.locked_focus = None:
			fl.show_message ('There is no locked focus','','')
			return
		if self.focuskind <> F_NODE:
			fl.show_message ('There is no focus on a node','','')
			return
		self.add_arrow_at(self.locked_focus, self.focus, 1, 0.0, 0, 1).draw()
		self.editmgr.commit()

	def add_arrow_at(self, (src, dst, f, d, t, newarc)):
		fro = src.ch_channelobj
		too = dst.ch_channelobj
		frx = fro.x + fro.w / 2
		fry = fro.y
		if f = 0:
			fry = fry + fro.h
		tox = too.x + too.w / 2
		toy = too.y
		if t = 0:
			toy = toy + too.h
		srcuid = src.GetUID()
		dstuid = dst.GetUID()
		arcinfo = (srcuid, f, d, t)
		if newarc:
			self.editmgr.addsyncarc(src, f, d, dst, t)
		thisarc = (self, dst, arcinfo)
		arr = arrow().new(frx, fry, tox, toy, thisarc, src, dst)
		self.arrowlist.append(arr)
		return(arr)

	def mod_arrow(self, arr):
		fro = arr.src.ch_channelobj
		too = arr.dst.ch_channelobj
		view, dst, info = arr.arc
		uid, f, delay, t = info
		frx = fro.x + fro.w / 2
		fry = fro.y
		if f = 0:
			fry = fry + fro.h
		tox = too.x + too.w / 2
		toy = too.y
		if t = 0:
			toy = toy + too.h
		arr.repos(frx, fry, tox, toy)

	def arrowhit(self, arrow):
		self.dounfocus()
		self.focus = arrow
		self.focuskind = F_ARC
		arrow.kind = FOCUS_ARROW
		arrow.draw()
	def setarcvalues(self, (arrow, newinfo)):
		if not self.editmgr.transaction():
			fl.show_message('Can not modify arc now','','')
			return
		view, dst, arcinfo = arrow.arc
		arrow.arc = view, dst, newinfo
		src = arrow.src
		srcuid, f, d, t = newinfo
		dstuid = dst.GetUID()
		self.editmgr.setsyncarcdelay(src, f, d, dst, t)
		self.editmgr.commit()
#XXX how long takes a redraw?
		self.redrawfunc()
	def deletearc(self):
		if self.focus = None:
			return
		if not self.editmgr.transaction():
			fl_show_message('Can not delete arc now','','')
			return
		arrow = self.focus
		view, dst, arcinfo = arrow.arc
		src = arrow.src
		srcuid, f, d, t = arcinfo
		dstuid = dst.GetUID()
		self.editmgr.delsyncarc(src, f, d, dst, t)
		self.editmgr.commit()
		arrow.hidden = 1
		del arrow
		self.redrawfunc()
		self.focuskind = F_NONE
		self.focus = None
	def diamhit(self, diam):
		self.dounfocus()
		i = self.chanboxes.index(diam)
		name = self.channellist[i]
		self.focus = self.chanboxes[i]
		self.focus.kind = FOCUS_CHAN
		self.focus.redraw()
		self.focuskind = F_CHAN


	#
	# _init : initialize state
	#
	def _init (self, (w, h)) :
		self.w, self.h = w, h
		self.focus = 0
		self.commanddict = {}
		self.root = 0
	#
	# _find_node : given a mouse positioin, find the corresponding node
	# in the (possibly folded) tree
	#
	def _find_node (self, (node, (x, y))) :
		type = node.GetType()
		kids = node.GetChildren()
		if type in ('seq','par','grp') and len(kids) > 0:
			for child in kids:
				if self._in_bounds (child, (x, y)) <> None :
					n = self._find_node(child, (x,y))
					if n <> None:
						return n
			if self._in_bounds_bl(node, (x, y)):
				return node
			return None
		return node
	#
	# _find_node2: given two sets of coordinates, find the node that
	# encompasses both
	#
	def _find_node2(self, (node, (x1, y1), (x2, y2))):
		type = node.GetType()
		kids = node.GetChildren()
		if type in ('seq','par','grp') and len(kids) > 0:
			for child in kids:
				if self._in_bounds2(child,(x1,y1),(x2,y2)) <> None:
					return self._find_node2(child,(x1,y1),(x2,y2))
		return node
	#
	# acto on the (alpha) key clicked and execute
	# the associated command.
	#
	def command(self, key):
		print key
		if self.commanddict.has_key (key) :
			self.commanddict[key][0](self)
		else :
			fl.show_message ('What does this mean?','','')


	def modify_arrow(self):
		if self.focuskind <> F_ARC:
			return
		showarceditor(self.focus)



	def _in_bounds (self, (node, (x, y))) :
		o = node.ch_channelobj
		if x > o.x and x < o.w+o.x and y > o.y and y < o.h+o.y:
			return node
		return self._in_bounds_bl(node, (x, y))

	def _in_bounds_bl(self, (node, (x, y))):
		o = node.ch_blockobj
		if x > o.x and x < o.w+o.x and y > o.y and y < o.h+o.y:
			return node
		return None

	def _in_bounds2(self, (node, (x1,y1), (x2,y2))):
		xl = x1
		yl = y1
		xu = x2
		yu = y2
		if xl > xu:
			xl = x2
			xu = x1
		if yl > yu:
			yl = y2
			yu = y1
		o = node.ch_blockobj
		if xl > o.x and xu < o.w+o.x and yl > o.y and yu < o.h+o.y:
			return node
		return None

	def redraw(self):
		clear_window()
		for i in range(self.nrchannels):
			self.chanboxes[i].draw()
		self.redraw_node(self.root)
		for arrow in self.arrowlist:
			arrow.draw()
		self.thermo.draw(self.currenttime * self.unitheight)

	def redrawfunc(self):
		self.recalc()
		self.redraw()

	def redraw_node(self, node):
		node.ch_blockobj.draw()
		node.ch_channelobj.draw()
		for child in node.GetChildren():
			self.redraw_node(child)

	def setcurrenttime(self, curtim):
		self.currenttime = curtim
		self.thermo.draw(curtim * self.unitheight)

	def play_focus(self):
		if self.focuskind <> F_NODE:
			fl.show_message ('Can only play a node', '', '(yet)')
			return
		self.toplevel.player.playsubtree(self.focus)

def helpfunc (bv) :
	dict = bv.commanddict
	print 'known commands :'
	for c in dict.keys () :
		print '      ' + c + ': ' + dict[c][1]

import AttrEdit

def attreditfunc (bv) :
	if bv.focuskind = F_NODE:
		AttrEdit.showattreditor (bv.focus)
	elif bv.focuskind = F_CHAN:
		channeleditfunc(bv)
	elif bv.focuskind = F_ARC:
		modify_arrow(bv)
	else:
		fl.show_message ('No node selected','','')
def channeleditfunc(bv):
	if bv.focuskind = F_CHAN:
		name = bv.focus.label
	elif bv.focuskind = F_NODE:
		node = bv.focus
		if node.GetType() in ['seq','par','grp']:
			fl.show_message('Not a single node selected','','')
			return
		name = node.GetInherAttrDef('channel', '?')
	else:
		fl.show_message('Not a node or channel selected','','')
		return
	AttrEdit.showchannelattreditor(bv.root.context, name)
#
# delete the focussed node.
# focus switches to parent.
# 




def lock_focus(self):
	self.lock_focus()
def unlock_focus(self):
	self.unlock_focus()
def add_arrow(self):
	self.add_arrow()
def redrawfunc(self):
	self.redrawfunc()
def modify_arrow(self):
	if self.focuskind <> F_ARC:
		fl.show_message ('No arc selected','','')
		return
	self.modify_arrow()
def deletearrow(self):
	if self.focuskind <> F_ARC:
		fl.show_message ('No arc selected','','')
		return
	self.deletearc()

def play_focus(self):
	self.play_focus()

import NodeInfo

def infofunc (bv) :
	if bv.focuskind <> F_NODE:
		fl.show_message ('No node selected','','')
		return
	NodeInfo.shownodeinfo(bv.focus)
