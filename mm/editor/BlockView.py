import fl
from FL import *
import gl
import GL
import MMAttrdefs
import glwindow
from Dialog import BasicDialog
from ViewDialog import ViewDialog
from MMNode import alltypes, leaftypes, interiortypes
import Clipboard

# XXX Test for forms 1.5 compat:
try:
    dummy = fl.get_rgbmode
    forms_v20 = 1
    del dummy
    print 'using FORMS 2.0'
except:
    forms_v20 = 0
    print 'no FORMS 2.0'


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
LMARG = 10 # left margin width
RMARG = 10 # right margin width
TMARG = 5 # top margin width (half as wide)
BMARG = 5 # bottom margin width (half as wide)
MMARG = 5 # margin between title button and real buttons
BH=20	# the height of the open/close button and title
BW=10   # width of open/close button

MENUH = 20	# Height of menu bar

class BlockView () = ViewDialog(), BasicDialog () :
	#
	# init() method compatible with the other views.
	#
	def init(self, toplevel):
		self = ViewDialog.init(self, 'blockview_')
		self.toplevel = toplevel
		self.root = self.toplevel.root
		self.editmgr = self.root.context.editmgr
		width, height = \
			MMAttrdefs.getattr(self.root, 'blockview_winsize')
		self = BasicDialog.init(self, (width, height, 'Hierarchy'))
		self.changing_node = None
		return self.new(width, height, self.root)
	def show(self):
		if self.showing: return
#		try:
#			self.form.doublebuf = 1
#		except:
#			pass # Old versions of Python don't accept this...
		self.editmgr.register(self)
		BasicDialog.show(self)
	def hide(self):
		if not self.showing: return
		self.editmgr.unregister(self)
		BasicDialog.hide(self)
		self.toplevel.checkviews()
	def transaction(self):
		return 1
	def commit(self):
		modnode = self.rootview
		self.form.freeze_form ()
		self.rmBlockview (modnode)
		self.mkBlockview(modnode.bv_xywh, modnode)
		self.fixfocus()
		self.presentlabels (modnode)
		self.setfocus(self.focus)
		self.form.unfreeze_form ()
	def rollback(self):
		pass
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
		h = h - MENUH
		self._init(w, h)
		area = self.form.add_box (UP_BOX, 0, 0, w, h, '')

		if forms_v20:
		    commands=self.form.add_input(HIDDEN_INPUT,0,0,1,1,'')
		    commands.set_call_back(self._command_callback, 0)
		    commands.set_input_return(1)
		else:
		    commands=self.form.add_default(ALWAYS_DEFAULT,0,0,w,h,'')
		    commands.set_call_back(self._command_callback, 0)

		focus = self.form.add_button(HIDDEN_BUTTON, 0, 0, w, h, '')
		focus.set_call_back(self._change_focus_callback, 0)
		
		self.addmenus(0,h,w,MENUH)
		self.rootview = root
		self._initcommanddict()
		self.mkBlockview((0, 0, w,h), root)
		self.presentlabels(root)
		self.setfocus(root)

		return self
	#
	# addtocommand adds a command to the commanddictionary.
	# Anybody can submit their own commands
	#
	def addtocommand(self, (key, func)) :
		self.commanddict[key] = func
	def addmenus(self, (x,y,w,h)):
		f = self.form
		menubar = f.add_box(FLAT_BOX,x,y,w,h,'')

		edit_menu = f.add_menu(PUSH_MENU,x,y,w/3,h,'Edit')
		edit_menu.set_menu('i Insert before|a Insert after|u Insert child%l|d Delete')
		cmdmap = 'iaud'
		edit_menu.set_call_back(self._menu_callback,cmdmap);
		clipboard_menu = f.add_menu(PUSH_MENU,x+w/3,y,w/3,h,'Clipboard')
		clipboard_menu.set_menu('I Paste before|A Paste after|U Paste as child%l|D Cut|C Copy')
		cmdmap = 'IAUDC'
		clipboard_menu.set_call_back(self._menu_callback,cmdmap);
		operation_menu = f.add_menu(PUSH_MENU,x+2*w/3,y,w/3,h,'Operation')
		operation_menu.set_menu('h Help|p Play|+ Zoom|- Unzoom%l|o Open info|e Open attr|E Edit contents')
		cmdmap = 'hp+-oeE'
		operation_menu.set_call_back(self._menu_callback,cmdmap);
	#
	# submit a number to default commands.
	#
	def _initcommanddict(self) :
		self.addtocommand('e', attreditfunc)
		self.addtocommand('E', conteditfunc)
		self.addtocommand('a', InsertAfterNode)
		self.addtocommand('i', InsertBeforeNode)
		self.addtocommand('u', InsertChildNode)
		self.addtocommand('d', DeleteNode)
		self.addtocommand('A', CInsertAfterNode)
		self.addtocommand('I', CInsertBeforeNode)
		self.addtocommand('U', CInsertChildNode)
		self.addtocommand('D', CDeleteNode)
		self.addtocommand('C', CopyNode)
		self.addtocommand('h', helpfunc)
		self.addtocommand('o', infofunc)
		self.addtocommand('p', playfunc)
		self.addtocommand('-', unzoomfunc)
		self.addtocommand('+', zoomfunc)
	#

	# blockview gets a region in the form where it recursively
	#  places a node in this region; (x, y, w, h).
	#
	def mkBlockview(self, ((x, y, w, h), node)) :
		type = node.GetType()

		obj = self.form.add_box (FRAME_BOX, x, y, w, h, '')

		node.bv_form 	= self.form
		node.bv_obj	= obj
	
		kids = node.GetChildren()
		if type in interiortypes:
			node.bv_xywh    = (x,y,w,h)
			# Create the open/close button:
			bx = x + LMARG
			by = y + h - TMARG - BH
			o=self.form.add_button(NORMAL_BUTTON,bx,by,BW,BH,'')
			o.boxtype = BORDER_BOX
			o.set_call_back(self._openclose_callback, node)
			o.col2 = GL.YELLOW
			node.bv_toosmall = 0
			o.set_button(0)
			node.bv_openclose	= o
			# Create the title text:
			bx = x + LMARG + BW
			by = y + h - TMARG - BH
			bw = w - LMARG - RMARG - BW
			o = self.form.add_text(NORMAL_TEXT, bx, by, bw, BH, '')
			o.align = ALIGN_CENTER
			node.bv_labeltext = o
			# Create childrens' boxes
			if kids:
			    h = h - TMARG - BMARG - MMARG - BH
			    w = w - LMARG - RMARG
			    if type = 'seq':
				    h = h / len(kids)
				    dx, dy = 0, h
			    else: 				 # parallel node
				    w = w / len(kids)
				    dx, dy = w, 0
			    toosmall = ((h < TMARG+BMARG+BH) or \
					(w < LMARG+RMARG+BW))
			    if toosmall:
				node.bv_openclose.col1 = GL.RED
				node.bv_toosmall = 1
				# x, y = 0, 0
				# w, h = 1, 1
			    elif self.isclosedlocal(node):
				o = node.bv_openclose
				o.col1, o.col2 = o.col2, o.col1
			    else:
				x,y = x+LMARG,y+BMARG
				# w,h = w-LMARG-RMARG,h-TMARG-BMARG
				w,h = w-RMARG,h-TMARG
			    if not self.isclosedlocal(node):
				if node.GetType() = 'seq':
				    kids = kids[:]
				    kids.reverse()
				for child in kids :
				    self.mkBlockview(((x, y, w, h), child))
				    x, y = x + dx, y + dy

	#
	# delete all the objects (made by blockview) form the node
	#
	def rmBlockview (self, node) :
		try:
		    node.bv_obj.delete_object ()
		    del node.bv_obj
		    node.bv_openclose.delete_object ()
		    del node.bv_openclose
		    node.bv_labeltext.delete_object()
		    del node.bv_labeltext
		except NameError:
		    pass
		except AttributeError: # new style exceptions
		    pass
		for child in node.GetChildren () :
		    self.rmBlockview (child)
	#
	# fixfocus: called to move focus up if it becomes invisible.
	#
	def fixfocus(self):
		focus = self.focus
		if focus = self.root or not self.isclosed(focus):
		    self.setfocus(focus)
		    return
		parent = focus.GetParent()
		while self.isclosed(parent):
		    focus = parent
		    if focus = self.root:
			break
		    parent = focus.GetParent()
		self.setfocus(focus)
	#
	# presentlabels : sets the appropiate labels in the FORMS object.
	#
	def presentlabels (self, node) :
		if len(node.GetChildren ()) = 0 :
			node.bv_obj.label = MMAttrdefs.getattr(node, 'name')
			return
		node.bv_labeltext.label = MMAttrdefs.getattr(node, 'name')
		node.bv_obj.label = ''
		num = 1
		if not self.isclosedlocal(node):
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

		gl.winset(self.form.window)
		mx, my = fl.get_mouse ()

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
		self.focus = None
		self.commanddict = {}
	#
	# _find_node : given a mouse positioin, find the corresponding node
	# in the (possibly folded) tree
	#
	def _find_node (self, (node, (x, y))) :
		if self.isclosedlocal(node) : return node

		for child in node.GetChildren () :
			if self._in_bounds (child, (x, y)) <> None :
				return  self._find_node (child, (x, y))
		return node
	#
	def _menu_callback(self, (obj,args)):
		index = obj.get_menu()
		if index:
		    self._do_command(args[index-1])
	#
	# command_callback : read which key is clicked and executes
	# the associated command.
	#
	def _command_callback(self, (obj, args)) :
		if forms_v20:
		    key = obj.get_input()
		    obj.set_input('')
		else:
		    key = obj.get_default()
		self._do_command(key)
	def _do_command(self,key):
		if self.commanddict.has_key (key) :
			self.commanddict[key](self)
		else :
			if fl.show_question ('Unknown command',key, \
						'Do you want help?'):
			    self.toplevel.help.givehelp('Hierarchy', \
					'Commands')

	def _openclose_callback (self, (obj, node)) :
		if node.bv_toosmall: return
		node.bv_form.freeze_form ()

		self.rmBlockview(node)
		node.SetAttr('closed', not node.GetRawAttrDef('closed',0))
		self.mkBlockview(node.bv_xywh,node)
		self.fixfocus()
		node.bv_obj.show_object ()		# show this node
		node.bv_openclose.show_object ()	# show roundbutton
		node.bv_labeltext.show_object()
		self.presentlabels (node)

		node.bv_form.unfreeze_form ()		
		
	def _in_bounds (self, (node, (x, y))) :
		o = node.bv_obj
		if  x > o.x and x < o.x+o.w and y > o.y and y < o.y+o.h :
			return node
		else :
			return None
	#
	# GetNewNode - Get new node
	#
	def GetNewNode(self) :
		type = self.focus.GetType()
		child = self.root.context.newnode(type)
		return child
	#
	def fromclipboard(self):
		type, data = Clipboard.getclip()
		if type <> 'node' or data = None:
			return None
		Clipboard.setclip(type, data.DeepCopy())
		return data
	def toclipboard(self, node):
		if node = None:
			type, data = '', None
		else:
			type, data = 'node', node
		Clipboard.setclip(type, data)

	#
	# isclosedlocal - Is node closed, knowing that ancestors are open?
	#
	def isclosedlocal(self, node):
		try:
		    if node.bv_toosmall:
			return 1
		except AttributeError:
		    pass
		return node.GetRawAttrDef('closed',0)
	#
	# isclosed - Is node closed, not knowing about ancestors?
	#
	def isclosed(self, node):
		if node <> self.root:
		    if self.isclosed(node.GetParent()):
			return 1
		return self.isclosedlocal(node)

def helpfunc (bv) :
	bv.toplevel.help.givehelp('Hierarchy')

import AttrEdit

def attreditfunc (bv) :
	AttrEdit.showattreditor (bv.focus)

import NodeEdit

def conteditfunc (bv) :
	NodeEdit.showeditor (bv.focus)


# copy the focus node to the clipboard

def CopyNode(bv):
	node = bv.focus
	if node = None:
		gl.ringbell()
		return
	Clipboard.setclip('node', node.DeepCopy())

#
# delete the focussed node.
# focus switches to parent.
# 
def _DeleteNode (bv,cb) :
	node = bv.focus
	em = bv.editmgr
	parent = node.GetParent ()
	if parent = None :
		fl.show_message ('sorry, cannot delete root','','')
		return
	#
	if not em.transaction():
	    print 'Sorry, no trans'
	    return
	#
	# Find out new focus. 
	# Order of tries: next sibling; previous sibling; parent
	#
	children = parent.GetChildren()
	nf = children.index(node)
	if nf = len(children)-1:
		nf = nf - 1
	#
	# And zap the node and move to the clipboard
	#
	bv.form.freeze_form()
	bv.rmBlockview(node)
	em.delnode(node)
	if cb:
	    bv.toclipboard(node)
	# (Don't ever call node.Delete(), it would break UNDO...)
	#
	if nf >= 0:
		bv.focus = children[nf]
	else:
		bv.focus = parent
	#
	bv.changing_node = parent
	bv.form.unfreeze_form()
	node.context.editmgr.commit()
	bv.changing_node = None
def DeleteNode (bv):
	_DeleteNode(bv,0)
def CDeleteNode (bv):
	_DeleteNode(bv,1)
#
# Insert a node before/after the focus. The node will be sequential without
# children, by default. Use Node Info to change this.
#
def _doInsertNode (bv, after, cb) :
	node = bv.focus
	parent = node.GetParent()
	em = bv.editmgr
	if parent = None : return

	if not em.transaction(): return

	kids = parent.GetChildren()
	i = kids.index(node)
	if after:
		i = i + 1
	
	if cb:
	    newnode = bv.fromclipboard()
	else:
	    newnode = bv.GetNewNode()
	if newnode = None:
	    gl.ringbell()
	    node.context.editmgr.rollback()
	    return
	em.addnode(parent, i, newnode)
	bv.focus = newnode

	bv.changing_node = parent
	node.context.editmgr.commit()
	bv.changing_node = None
	if not cb: NodeInfo.shownodeinfo(newnode)
def InsertBeforeNode(bv):
	_doInsertNode(bv, 0, 0)
def CInsertBeforeNode(bv):
	_doInsertNode(bv, 0, 1)
def InsertAfterNode(bv):
	_doInsertNode(bv, 1, 0)
def CInsertAfterNode(bv):
	_doInsertNode(bv, 1, 1)

#
# Add a child node to a (possibly empty) seq/par node.
#
def _InsertChildNode (bv,cb) :
	parent = bv.focus
	em = bv.editmgr

	if (not parent.GetType() in interiortypes) or bv.isclosedlocal(parent):
	    gl.ringbell()
	    return
	if not em.transaction(): return

	if cb:
	    newnode = bv.fromclipboard()
	else:
	    newnode = bv.GetNewNode()
	if newnode = None:
	    gl.ringbell()
	    node.context.editmgr.rollback()
	    return
	em.addnode(parent, 0, newnode)

	bv.changing_node = parent
	bv.focus = newnode
	parent.context.editmgr.commit()
	bv.changing_node = None
	if not cb: NodeInfo.shownodeinfo(newnode)

def InsertChildNode(bv):
	_InsertChildNode(bv,0)
def CInsertChildNode(bv):
	_InsertChildNode(bv,1)
#
def unzoomfunc (bv) :
	if bv.rootview = bv.root : return

	bv.form.freeze_form ()

	bv.rmBlockview (bv.rootview)		# get rid of all FORMS objects
	#
	bv.mkBlockview((0, 0, bv.w, bv.h), bv.rootview.GetParent())
	bv.fixfocus()
	bv.presentlabels (bv.rootview.GetParent())
	bv.setfocus(bv.focus)
	bv.form.unfreeze_form ()
	bv.rootview = bv.rootview.GetParent ()

def zoomfunc (bv) :
	node = bv.focus

	while node.GetParent() <> bv.rootview :
		node = node.GetParent()
		if node = None :
		    gl.ringbell()
		    return

	nObj = node.GetParent().bv_obj
	x, y, w, h = nObj.x, nObj.y, nObj.w, nObj.h

	bv.form.freeze_form ()
	bv.rmBlockview (bv.rootview)		# get rid of all FORMS objects
	#
	bv.mkBlockview((x, y, w, h), node)
	bv.fixfocus()
	bv.presentlabels (node)
	bv.setfocus(bv.focus)
	bv.form.unfreeze_form ()
	bv.rootview = node

import NodeInfo

def infofunc(bv):
	node = bv.focus
	NodeInfo.shownodeinfo(node)

def playfunc(bv):
	node = bv.focus
	bv.toplevel.player.playsubtree(node)
