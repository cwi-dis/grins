import fl
#from GL import *
#from gl import *
from figures import *
#import DEVICE
from ArcEdit import *
import MMAttrdefs
import Timing

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
	#	5. set the focus to the root.
	#

	def new (self, (w, h, root, debug)) :
		self._init(w, h)
		self.debug = debug
		#
		area = box().new(FOCUS_BOX,0,0,w,h,'')

		self.root = root
		self.rootview = root
		self._initcommanddict()
		self.channellist = []
		self.arrowlist = []
	 	duration = self.calcDuration(root) # for channel headers
		self.channellist.sort()
		self.nrchannels = len(self.channellist)
		self.chanboxes = []
		self.thermleft = w - THERMW
		w = w / 2
		self.unitwidth = (w - THERMW) / self.nrchannels
		self.unitheight = (h - HDR_SIZE) / root.t1
		self.thermo = thermo().new(self.thermleft + XMARG, YMARG, THERMW - XMARG * 2, h - HDR_SIZE - YMARG * 2)
		self.currenttime = root.t0
		self.dividor = w
		xi = w + XMARG
		wi = self.unitwidth - XMARG*2
		hi = HDR_SIZE - YMARG*2
		yi = h - YMARG - hi
		li = h - YMARG*2 - hi
		for i in range(self.nrchannels):
			self.chanboxes.append(diamond().new(xi,yi,wi,hi,li,self.channellist[i]))
			xi = xi + self.unitwidth
		self.mkView((0,0,w,h,h-HDR_SIZE),root)
		self.mkArrows(root)
		self.focus = root
		self.setfocus(root)
		self.locked_focus = None
		return self

	def recalc(self):
		# XXX This should be called in response to commit...
		Timing.calctimes(self.root)
		self.unitheight = (self.h - HDR_SIZE) / self.root.t1
		self.re_mkView((0,0,self.w / 2,self.h,self.h-HDR_SIZE),self.root)
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
#TMP		self.addtocommand('d', deleteNode, 'delete node')
		self.addtocommand('h', helpfunc, 'help message')
		self.addtocommand('i', infofunc, 'open node info window')
		self.addtocommand('l', lock_focus, 'lock current focus')
#TMP		self.addtocommand('p', addParallel, 'add parallel node')
		self.addtocommand('r', redrawfunc, 'redraw')
#TMP		self.addtocommand('s', addSequential, 'add sequential node')
		self.addtocommand('t', add_arrow, 'add timing arc')
		self.addtocommand('u', unlock_focus, 'unfocus locked focus')
#TMP		self.addtocommand('u', unzoomfunc, 'unzoom node')
#TMP		self.addtocommand('z', zoomfunc, 'zoom node')
	#

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
		node.blockobj = blobj
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
		node.channelobj = chobj
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
		kids = node.GetChildren()
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
		chobj = node.channelobj
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
			j = self.add_arrow_at(self.root.MapUID(uid), node, frompos, delay, topos)
		for i in node.GetChildren():
			self.mkArrows(i)
	#
	# delete all the objects (made by channelview) form the node
	#
	def rmView (self, node) :
		node.blockobj.hidden = 1
		del node.blockobj
		node.channelobj.hidden = 1
		del node.channelobj
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
	#	self.form.freeze_form()

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

		if node.blockobj.boxtype <> FG_BOX:
			return
		if mx<self.dividor or node.GetType() not in ('seq','par','grp'):
			if self.focus <> None:
				self.unfocus(self.focus)
				self.redraw_node(self.focus)
			self.setfocus (node)
			self.redraw_node(node)
			for arrow in self.arrowlist:
				arrow.draw()
	#	self.form.unfreeze_form ()
	def add_focus(self, (mx, my)):
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
			node1 = self._find_node2(self.root, (node.blockobj.x,node.blockobj.y),(self.focus.blockobj.x,self.focus.blockobj.y))
			if node1 = None:
				raise 'view'
			if node1.blockobj.boxtype <> FG_BOX:
				return
			self.unfocus(self.focus)
			self.redraw_node(self.focus)
			self.setfocus(node1)
			self.redraw_node(node1)
			for arrow in self.arrowlist:
				arrow.draw()
	def lock_focus(self):
		if self.locked_focus = self.focus:
			return
		if self.locked_focus <> None:
			fl.show_message ('There is already a locked focus','','')
			return
		node = self.focus
		if node = None:
			return
		if node.blockobj.boxtype <> FOCUS_BOX:
			return
		node.blockobj.boxtype = LOCK_BOX
		self.lockchanfocus(node)
		self.locked_focus = node
		self.focus = None
		self.redraw_node(node)
		for arrow in self.arrowlist:
			arrow.draw()
	def unlock_focus(self):
		node = self.locked_focus
		if node = None:
			return
		node.blockobj.boxtype = FG_BOX
		self.unfocuschan(node)
		self.locked_focus = None
		self.redraw_node(node)
		for arrow in self.arrowlist:
			arrow.draw()
	#
	# setfocus
	#
	def setfocus (self, node) :
		node.blockobj.boxtype = FOCUS_BOX
		if node <> self.root:
			self.setchanfocus (node)
		self.focus = node
	def setchanfocus(self, node):
		if node.GetType() in ('seq','par','grp'):
			for child in node.GetChildren():
				self.setchanfocus(child)
		else:
			node.channelobj.boxtype = FOCUS_BOX
	def unfocus (self, node) :
		node.blockobj.boxtype = FG_BOX
		if node <> self.root:
			self.unchanfocus (node)
		self.focus = node
	def unchanfocus(self, node):
		if node.GetType() in ('seq','par','grp'):
			for child in node.GetChildren():
				self.unchanfocus(child)
		else:
			node.channelobj.boxtype = FG_BOX
	def lockchanfocus(self, node):
		if node.GetType() in ('seq','par','grp'):
			for child in node.GetChildren():
				self.lockchanfocus(child)
		else:
			node.channelobj.boxtype = LOCK_BOX
	def unfocuschan(self, node):
		if node.GetType() in ('seq','par','grp'):
			for child in node.GetChildren():
				self.unfocuschan(child)
		else:
			node.channelobj.boxtype = FG_BOX
	#
	# timing arcs
	#
	def add_arrow(self):
		if self.locked_focus = None:
			fl.show_message ('There is no locked focus','','')
			return
		if self.focus = None:
			fl.show_message ('There is no focus','','')
			return
		self.add_arrow_at(self.locked_focus, self.focus, 1, 0.0, 0).draw()

	def add_arrow_at(self, (src, dst, f, d, t)):
		fro = src.channelobj
		too = dst.channelobj
		frx = fro.x + fro.w / 2
		fry = fro.y
		if f = 0:
			fry = fry + fro.h
		tox = too.x + too.w / 2
		toy = too.y
		if t = 0:
			toy = toy + too.h
		arcinfo = (src.GetUID(), f, d, t)
		arclist = MMAttrdefs.getattr(dst, 'synctolist')
		if not arcinfo in arclist:
			arclist1 = arclist[0:len(arclist)]
			arclist1.append(arcinfo)
			dst.SetAttr('synctolist', arclist1)
		thisarc = (view, dst, arcinfo)
		arr = arrow().new(frx, fry, tox, toy, thisarc, src, dst)
		self.arrowlist.append(arr)
		return(arr)

	def mod_arrow(self, arr):
		fro = arr.src.channelobj
		too = arr.dst.channelobj
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
		showarceditor(arrow)
	def setarcvalues(self, (arrow, newinfo)):
		view, dst, arcinfo = arrow.arc
		arrow.arc = (view, dst, newinfo)
		arclist = MMAttrdefs.getattr(dst, 'synctolist')
		arclist.remove(arcinfo)
		arclist.append(newinfo)
		dst.SetAttr('synctolist', arclist)
	#def deletearc(self, arrow):
	#	view, dst, arcinfo = arrow.arc
	#	arclist = MMAttrdefs.getattr(dst, 'synctolist')
	#	arclist.remove(arcinfo)
	#	dst.SetAttr('synctolist', arclist)
	#	arrow.hidden = 1
	#	del arrow
	#	self.redraw(self)
	def diamhit(self, diam):
		i = self.chanboxes.index(diam)
		name = self.channellist[i]
		AttrEdit.showchannelattreditor(self.root.context, name)


	#
	# _init : initialize state
	#
	def _init (self, (w, h)) :
		self.w, self.h = w, h
		self.focus = 0
		self.commanddict = {}
	#	self.form = 0
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
		if self.commanddict.has_key (key) :
			self.commanddict[key][0](self)
		else :
			fl.show_message ('What does this mean?','','')






	def _in_bounds (self, (node, (x, y))) :
		o = node.channelobj
		if x > o.x and x < o.w+o.x and y > o.y and y < o.h+o.y:
			return node
		return self._in_bounds_bl(node, (x, y))

	def _in_bounds_bl(self, (node, (x, y))):
		o = node.blockobj
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
		o = node.blockobj
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
		node.blockobj.draw()
		node.channelobj.draw()
		for child in node.GetChildren():
			self.redraw_node(child)

	def setcurrenttime(self, curtim):
		self.currenttime = curtim
		self.thermo.draw(curtim * self.unitheight)

def helpfunc (bv) :
	dict = bv.commanddict
	print 'known commands :'
	for c in dict.keys () :
		print '      ' + c + ': ' + dict[c][1]

import AttrEdit

def attreditfunc (bv) :
	node = bv.focus
	if node = None:
		fl.show_message ('No node selected','','')
		return
	AttrEdit.showattreditor (bv.focus)
def channeleditfunc(bv):
	node = bv.focus
	if node = None:
		fl.show_message ('No node selected','','')
		return
	if node.GetType() in ['seq','par','grp']:
		fl.show_message('Not a single node selected','','')
		return
	name = node.GetInherAttrDef('channel', '?')
	AttrEdit.showchannelattreditor(bv.root.context, name)

import NodeInfo

def infofunc(bv):
	node = bv.focus
	if node = None:
		fl.show_message ('No node selected','','')
		return
	NodeInfo.shownodeinfo(node)


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
