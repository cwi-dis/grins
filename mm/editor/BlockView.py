import fl
from FL import *
import MMAttrdefs
import glwindow
from Dialog import BasicDialog

# the block view class.
# *** Hacked by --Guido ***
#
# There are two methods :
#	1. new (w, h, root) which returns the form and a box which
#	   acts as a "canvas" over the form. w, h are the width and height.
#	2. blockview(form, (x, y, w, h), node) which makes the blockview.
#	   node is a node in the tree.

#
# We use the FRAME_BOX because it looks good. :-)
#
# 

# TODO :
#
#	1. Get and use defaults ! [Need the interface to the default
#	   database].
#
#	2. Fill in the duration on SEQ children. This is trivial as
#	   as soon as we figure out how do calculate the duration !
#

##################### CLASS DEFINITION : blockview 
#

# some constants that can be used to expiriment with how the
# blocks are placed on top of each other.
#
XMARG = 10 # margin width
YMARG = 5 # two time the  margin width
B=5	# the size of the roundbutton

class BlockView () = BasicDialog () :
	#
	# init() method compatible with the other views.
	#
	def init(self, root):
		self.root = root
		width, height = \
			MMAttrdefs.getattr(root, 'blockview_winsize')
		self = BasicDialog.init(self, (width, height, 'Hierarchy'))
		return self.new(width, height, root)
	#
	# Extend basic show/hide methods.
	#
	def show(self):
		width, height = \
			MMAttrdefs.getattr(self.root, 'blockview_winsize')
		h, v = MMAttrdefs.getattr(self.root, 'blockview_winpos')
		self.last_geometry = h, v, width, height
		BasicDialog.show(self)
	#
	def hide(self):
		BasicDialog.hide(self)
		h, v, width, height = self.last_geometry
		self.root.SetAttr('blockview_winpos', (h, v))
		self.root.SetAttr('blockview_winsize', (width, height))
	#
	# new makes an object of type 'blockview'
	#
	# if does :
	#	0. initializes some state
	#	1. makes the form
	#	2. initializes the command dict / command callbak
	#	3. initializes the 'change focus' button
	#	4. initializes the commandarea (Help, File, ...)
	#	5. sets up the blockview
	#	6. set the focus to the root.
	#
	def new (self, (w, h, root)) :
		self._init(w, h)
		area = self.form.add_box (UP_BOX, 0, 0, w, h, '')

		commands=self.form.add_default(ALWAYS_DEFAULT,0,0,w,h,'')
		commands.set_call_back(self._command_callback, 0)

		focus = self.form.add_button(HIDDEN_BUTTON, 0, 0, w, h, '')
		focus.set_call_back(self._change_focus_callback, 0)
		
		self.rootview = root
		self._initcommanddict()
		self.mkBlockview((0, 0, w,h), root)
		self.fixlabels ()
		self.presentlabels(root)
		self.setfocus(root)

		return self
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
		self.addtocommand('d', deleteNode, 'delete node')
		self.addtocommand('h', helpfunc, 'help message')
		self.addtocommand('p', addParallel, 'add parallel node')
		self.addtocommand('r',  rotatefunc, 'rotate node')
		self.addtocommand('s', addSequential, 'add sequential node')
		self.addtocommand('u', unzoomfunc, 'unzoom node')
		self.addtocommand('z', zoomfunc, 'zoom node')
	#

	# blockview gets a region in the form where it recursively
	#  places a node in this region; (x, y, w, h).
	#
	def mkBlockview(self, ((x, y, w, h), node)) :
		type = node.GetType()

		obj = self.form.add_box (UP_BOX, x, y, w, h, '')
		obj.boxtype = FRAME_BOX

		node.bv_OC 	= 1		# block open/closed toggle
		node.bv_form 	= self.form
		node.bv_obj	= obj
	
		kids = node.GetChildren()
		if type in ('seq','par','grp') and len(kids) > 0:
			o=self.form.add_roundbutton(NORMAL_BUTTON,x+B,y+h-3*B,B,B,'')
			o.set_call_back(self._openclose_callback, node)
			o.col1, o.col2 = 1, 2
			node.bv_openclose	= o

			if type in ('grp', 'seq') :
				h = h / len(kids)
				dx, dy = 0, h
			else: 				 # parallel node
				w = w / len(kids)
				dx, dy = w, 0
			x,y,w,h = x+XMARG,y+YMARG,w-2*XMARG,h-2*YMARG
			num = 1
			if node.GetType() = 'seq':
				kids = kids[:]
				kids.reverse()
			for child in kids :
				self.mkBlockview(((x, y, w, h), child))
				x, y = x + dx, y + dy
				num = num + 1

	#
	# delete all the objects (made by blockview) form the node
	#
	def rmBlockview (self, node) :
		if node.GetType () in ('seq', 'par', 'grp'):
			node.bv_openclose.hide_object ()	# rm_object()
			del node.bv_openclose
		node.bv_obj.hide_object ()	# should be rm_object()
		del node.bv_obj
		for child in node.GetChildren () :
			self.rmBlockview (child)
	#
	# fixlabels : sets the labels of the complete tree
	# should be called after any structural mutation.
	#
	def fixlabels (self) :
		self._fixlabels (self.root, '')
	#
	# _fixlabels : rucrsivley sets the labels
	#
	def _fixlabels (self, (node, label)) :
		node.bv_label = label
		num = 1
		for child in node.GetChildren () :
			if label = '' :
				labelc = `num`
			else :
				labelc = label + '.' + `num`
			num = num + 1
			self._fixlabels (child, labelc)
	#
	# presentlabels : sets the appropiate labels in the FORMS object.
	#
	def presentlabels (self, node) :
		if node.bv_OC = 0 or len(node.GetChildren ()) = 0 :
			node.bv_obj.label = node.bv_label
			return
		node.bv_obj.label = ''
		num = 1
		for child in node.GetChildren () :
			self.presentlabels (child)
	#
	# change_focus_callback
	# called when user clicks on a node to grab the focus
	# the argument is the class 'blockview' itself.
	#
	def _change_focus_callback (self, (obj, args)) :
		self.form.freeze_form()
		self.focus.bv_obj.boxtype = FRAME_BOX

		import gl
		gl.winset(self.form.window)
		mx, my = fl.get_mouse ()
		print 'mx =', mx, '; my =', my

		node = self._find_node (self.rootview, (mx, my))
		if node = None :
			print 'no node'
			raise 'block view'

		self.setfocus (node)
		self.form.unfreeze_form ()
	#
	# setfocus
	#
	def setfocus (self, node) :
		node.bv_obj.boxtype = UP_BOX
		self.focus = node
	#
	# _init : initialize state
	#
	def _init (self, (w, h)) :
		self.w, self.h = w, h
		self.focus = 0
		self.commanddict = {}
		self.form = 0
		self.root = 0
	#
	# _find_node : given a mouse positioin, find the corresponding node
	# in the (possibly folded) tree
	#
	def _find_node (self, (node, (x, y))) :
		if node.bv_OC = 0 : return node

		for child in node.GetChildren () :
			if self._in_bounds (child, (x, y)) <> None :
				return  self._find_node (child, (x, y))
		return node
	#
	# command_callback : read which key is clicked and executes
	# the associated command.
	#
	def _command_callback(self, (obj, args)) :
		key = obj.get_default()
		print key
		if self.commanddict.has_key (key) :
			self.commanddict[key][0](self)
		else :
			fl.show_message ('What is :',key,'')

	def _openclose_callback (self, (obj, node)) :
		node.bv_form.freeze_form ()

		node.bv_OC = (not node.bv_OC)		# toggle open/close
		obj.col1, obj.col2 = obj.col2, obj.col1 # swap: red <--> green
		self._openclose (node, node.bv_OC)	# recursive
		node.bv_obj.show_object ()		# show this node
		node.bv_openclose.show_object ()	# show roundbutton
		self.presentlabels (node)

		node.bv_form.unfreeze_form ()		
		
	def _openclose (self, (node, toggle)) :
		if toggle <> 0 :
			node.bv_obj.show_object ()
			if node.GetType () in ('seq', 'par', 'grp') :
				node.bv_openclose.show_object ()
				if node.bv_OC = 0 : return
		else :
			node.bv_obj.hide_object ()
			if node.GetType () in ('seq', 'par', 'grp') :
				node.bv_openclose.hide_object ()
		
		for child in node.GetChildren () :
			self._openclose (child, toggle)
		
	def _in_bounds (self, (node, (x, y))) :
		o = node.bv_obj
		if  x > o.x and x < o.x+o.w and y > o.y and y < o.y+o.h :
			return node
		else :
			return None

def helpfunc (bv) :
	dict = bv.commanddict
	print 'known commands :'
	for c in dict.keys () :
		print '      ' + c + ': ' + dict[c][1]

import AttrEdit

def attreditfunc (bv) :
	AttrEdit.showattreditor (bv.focus)

#
# delete the focussed node.
# focus switches to parent.
# 
def deleteNode (bv) :
	node = bv.focus
	
	parent = node.GetParent ()
	if parent = None :
		fl.show_message ('sorry, cannot delete root','','')
		return
	pObj = parent.bv_obj
	x, y, w, h = pObj.x, pObj.y, pObj.w, pObj.h

	node.Extract ()
	bv.form.freeze_form ()
	bv.rmBlockview (parent)	# yes, from the parent !
	node.Destroy ()
	#
	bv.mkBlockview((x, y,w,h),parent)
	bv.fixlabels ()
	bv.presentlabels (parent)
	bv.setfocus(parent)
	#
	# if an interior node has no children the delete it as well.
	# this is questionable ....
	#
	if len (parent.GetChildren()) = 0 : deleteNode(bv)
	#
	bv.form.unfreeze_form ()

def mkNode(node) :
	context = node.GetContext()
	child = context.newnode('imm')
	return child
	
def addChild (node) :
	child = mkNode(node)
	child.AddToTree(node,100000) # at the end of the children
	return child

#
# rotate a node around with its right anscestor.
#

def rotatefunc (bv) :
	node = bv.focus
	parent = node.GetParent()
	if parent = None : return
	
	nObj = parent.bv_obj
	x, y, w, h = nObj.x, nObj.y, nObj.w, nObj.h
	kids = parent.GetChildren()
	
	if parent.GetChild(len(kids) - 1) = node :
		kids[1:] = kids [0:len(kids)-1]
		kids[0] = node
	else :
		for i in range(0, len(kids)) :
			if kids[i] = node :
				kids[i], kids[i+1] = kids[i+1], kids[i]
				break
	bv.form.freeze_form ()
	bv.rmBlockview (parent)		# get rid of all FORMS objects
	#
	bv.mkBlockview((x, y, w, h), parent)
	bv.fixlabels ()
	bv.presentlabels (parent)
	bv.setfocus(node)
	bv.form.unfreeze_form ()

#
# add a sequential node to the focus.
# The stratagy is :
#	0. if the focus is a paralle node-> change the focus to sequntial
#	1. if the focus is a sequential node-> add node to the focus' children
#	2. if the focus is a leaf (call it 'a')-> make a tree: ; (a, b)
#		in which ; is a sequential node, and 'b' is a new node.
#

def addSequential (bv) :
	node = bv.focus

	nObj = node.bv_obj
	x, y, w, h = nObj.x, nObj.y, nObj.w, nObj.h
	bv.form.freeze_form ()
	bv.rmBlockview (node)		# get rid of all FORMS objects

	# case 0
	if node.GetType () = 'par' :
		node.SetType('seq')
		#
		bv.mkBlockview((x, y, w, h), node)
		bv.fixlabels ()
		bv.presentlabels (node)
		bv.setfocus(node)
		bv.form.unfreeze_form ()
	# case 1
	elif len(node.GetChildren()) > 0 :
		#
		child = addChild(node)
		#
		bv.mkBlockview((x, y, w, h),node)
		bv.fixlabels ()
		bv.presentlabels (node)
		bv.setfocus(child)
		bv.form.unfreeze_form ()
	# case 2
	else :
		#
		seq = mkNode (node)
		seq.SetType('seq')
		parent = node.GetParent ()
		if parent = None :
			seq.AddToTree(node, 0)
		else :
			for i in range (len(parent.GetChildren ())) :
				if node = parent.GetChild(i) : break
			node.Extract ()
			seq.AddToTree(parent, i)
			node.AddToTree(seq, 0)
		#
		child = addChild (seq)
		#
		bv.mkBlockview((x, y, w, h), seq)
		bv.fixlabels ()
		bv.presentlabels (seq)
		bv.setfocus(child)
		bv.form.unfreeze_form ()

#
# add a parallel node to the focus.
# The stratagy is :
#	0. if the focus is a seq node-> change the focus to par
#	1. if the focus is a parallel node-> add node to the focus' children
#	2. if the focus is a leaf (call it 'a')-> make a tree: | (a, b)
#		in which ; is a parallel node, and 'b' is a new node.
#

def addParallel (bv) :
	node = bv.focus

	nObj = node.bv_obj
	x, y, w, h = nObj.x, nObj.y, nObj.w, nObj.h

	bv.form.freeze_form ()
	bv.rmBlockview (node)		# get rid of all FORMS objects

	# case 0.
	if node.GetType () = 'seq' :
		node.SetType('par')
		#
		bv.mkBlockview((x, y, w, h), node)
		bv.presentlabels (node)
		bv.setfocus(node)
		bv.form.unfreeze_form ()
	# case 1
	elif len(node.GetChildren()) > 0 :
		#
		child = addChild(node)
		#
		bv.mkBlockview((x, y, w, h), node)
		bv.fixlabels ()
		bv.presentlabels (node)
		bv.setfocus(child)
		bv.form.unfreeze_form ()
	# case 2
	else :
		#
		par = mkNode (node)
		par.SetType('par')
		parent = node.GetParent ()		
		if parent = None :
			par.AddToTree(node, 0)
		else :
			for i in range (len(parent.GetChildren ())) :
				if node = parent.GetChild(i) : break
			node.Extract ()
			par.AddToTree(parent, i)
			node.AddToTree(par, 0)
		#
		child = addChild (par)
		#
		bv.mkBlockview((x, y, w, h), par)
		bv.fixlabels ()
		bv.presentlabels (parent)
		bv.setfocus(child)
		bv.form.unfreeze_form ()

def unzoomfunc (bv) :
	if bv.rootview = bv.root : return

	bv.form.freeze_form ()

	bv.rmBlockview (bv.rootview)		# get rid of all FORMS objects
	#
	bv.mkBlockview((0, 0, bv.w, bv.h), bv.rootview.GetParent())
	bv.fixlabels ()
	bv.presentlabels (bv.rootview.GetParent())
	bv.setfocus(bv.focus)
	bv.form.unfreeze_form ()
	bv.rootview = bv.rootview.GetParent ()

def zoomfunc (bv) :
	node = bv.focus

	while node.GetParent() <> bv.rootview :
		node = node.GetParent()
		if node = None : return

	nObj = node.GetParent().bv_obj
	x, y, w, h = nObj.x, nObj.y, nObj.w, nObj.h

	bv.form.freeze_form ()
	bv.rmBlockview (bv.rootview)		# get rid of all FORMS objects
	#
	bv.mkBlockview((x, y, w, h), node)
	bv.presentlabels (node)
	bv.setfocus(bv.focus)
	bv.form.unfreeze_form ()
	bv.rootview = node
