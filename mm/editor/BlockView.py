# Hierarchy window (for historic reasons called "Block View")

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
import string


# XXX Test for forms 1.5 compat:
forms_v20 = 1
try:
    dummy = fl.get_rgbmode
except AttributeError:
    forms_v20 = 0

if forms_v20:
    del dummy
##  print 'using FORMS 2.0'
else:
    print 'BlockView: no FORMS 2.0 -- will this still work?'


# Parametrization of the lay-out
LMARG = 10	# left margin width
RMARG = 10	# right margin width
TMARG = 5 	# top margin width (half as wide)
BMARG = 5 	# bottom margin width (half as wide)
MMARG = 5 	# margin between title button and real buttons
BH = 20   	# the height of the open/close button and title
BW = 10   	# width of open/close button
MENUH = 20	# Height of menu bar
ZOOMW = 20	# Width of zoo buttons


# Special color assignments
BAGCOLOR = 60
LEAFCOLOR = 61
fl.mapcolor(BAGCOLOR, 152, 174, 200)
fl.mapcolor(LEAFCOLOR, 200, 174, 152)


class BlockView(ViewDialog, BasicDialog):
    #
    # init() method compatible with the other views.
    #
    def init(self, toplevel):
	self = ViewDialog.init(self, 'blockview_')
	self.toplevel = toplevel
	self.root = self.toplevel.root
	self.editmgr = self.root.context.editmgr
	width, height = MMAttrdefs.getattr(self.root, 'blockview_winsize')
	title = 'Hierarchy (' + toplevel.basename + ')'
	self = BasicDialog.init(self, width, height, title)
	self.changing_node = None
	return self.new(width, height, self.root)

    def fixtitle(self):
	self.settitle('Hierarchy (' + self.toplevel.basename + ')')

    def __repr__(self):
	return '<BlockView instance, root=' + `self.root` + '>'

    def show(self):
	if self.is_showing():
	    self.pop()
	    return
	self.editmgr.register(self)
	BasicDialog.show(self)

    def hide(self):
	if not self.is_showing():
	    return
	self.editmgr.unregister(self)
	BasicDialog.hide(self)
	self.toplevel.checkviews()

    def transaction(self):
	return 1

    def commit(self):
	modnode = self.rootview
	self.form.freeze_form()
	self.rmBlockview(modnode)
	self.mkBlockview(modnode.bv_xywh, modnode)
	self.fixfocus()
	self.presentlabels(modnode)
	self.setfocus(self.focus)
	self.form.unfreeze_form()

    def rollback(self):
	pass

    def kill(self):
	self.destroy()
    #
    # new makes an object of type 'blockview'
    #
    # it does:
    #	0. initializes some state
    #	1. makes the form
    #	2. initializes the command dict / command callbak
    #	3. initializes the 'change focus' button
    #	4. initializes the commandarea (Help, File, ...)
    #	5. sets up the blockview
    #	6. set the focus to the root.
    #
    def new(self, w, h, root):
	h = h - MENUH
	self._init(w, h)
	area = self.form.add_box(UP_BOX, 0, 0, w, h, '')

	if forms_v20:
	    commands=self.form.add_input(HIDDEN_INPUT, 0, 0, 1, 1, '')
	    commands.set_call_back(self._command_callback, 0)
	    commands.set_input_return(1)
	else:
	    commands=self.form.add_default(ALWAYS_DEFAULT, 0, 0, w, h, '')
	    commands.set_call_back(self._command_callback, 0)

	focus = self.form.add_button(HIDDEN_BUTTON, 0, 0, w, h, '')
	focus.set_call_back(self._change_focus_callback, 0)

	self.addmenus(0, h, w, MENUH)
	self.rootview = root
	self._initcommanddict()
	self.mkBlockview((0, 0, w, h), root)
	self.presentlabels(root)
	self.setfocus(root)

	return self
    #
    # addtocommand adds a command to the commanddictionary.
    # Anybody can submit their own commands
    #
    def addtocommand(self, key, func):
	self.commanddict[key] = func

    # XXX The menu definitions should be done in such a way that
    # XXX you only need to edit a single line to change a shortcut!

    def addmenus(self, x, y, w, h):
	f = self.form
	menubar = f.add_box(FLAT_BOX, x, y, w, h, '')
	zoominbut = f.add_button(NORMAL_BUTTON, x+w-ZOOMW, y, ZOOMW, h, 'Z')
	zoominbut.set_call_back(self._button_callback, 'Z')
	zoomoutbut = f.add_button(NORMAL_BUTTON, x+w-2*ZOOMW, y, ZOOMW, h, 'z')
	zoomoutbut.set_call_back(self._button_callback, 'z')
	w = w-2*ZOOMW

	edit_menu = f.add_menu(PUSH_MENU, x, y, w/3, h, 'Edit')
	edit_menu.set_menu('m Insert before...|n Insert after...|u Insert child...%l|S Insert seq parent|P Insert par parent|B Insert bag parent%l|d Delete')
	cmdmap = 'mnuSPBd'
	edit_menu.set_call_back(self._menu_callback, cmdmap);
	clipboard_menu = f.add_menu(PUSH_MENU, x+w/3, y, w/3, h, 'Clipboard')
	clipboard_menu.set_menu('M Paste before|N Paste after|U Paste child%l|D Cut|C Copy')
	cmdmap = 'MNUDC'
	clipboard_menu.set_call_back(self._menu_callback, cmdmap);
	operation_menu = f.add_menu(PUSH_MENU, x+2*w/3, y, w/3, h, 'Operation')
	operation_menu.set_menu('h Help...|p Play node...|Z Zoom in|z Zoom out%l|i Node info...|a Node attr...|e Edit contents...|t Edit anchors...%l|f Push focus')
	cmdmap = 'hpZziaetf'
	operation_menu.set_call_back(self._menu_callback, cmdmap);
    #
    # submit a number to default commands.
    #
    def _initcommanddict(self):
	# Edit menu
	self.addtocommand('m', InsertBeforeNode)
	self.addtocommand('n', InsertAfterNode)
	self.addtocommand('u', InsertChildNode)
	self.addtocommand('d', DeleteNode)
	self.addtocommand('S', InsertSeqParent)
	self.addtocommand('P', InsertParParent)
	self.addtocommand('B', InsertBagParent)

	# Clipboard menu
	self.addtocommand('M', CInsertBeforeNode)
	self.addtocommand('N', CInsertAfterNode)
	self.addtocommand('U', CInsertChildNode)
	self.addtocommand('D', CDeleteNode)
	self.addtocommand('C', CopyNode)

	# Operations menu
	self.addtocommand('h', helpfunc)
	self.addtocommand('p', playfunc)
	self.addtocommand('Z', zoomfunc)
	self.addtocommand('z', unzoomfunc)
	self.addtocommand('i', infofunc)
	self.addtocommand('a', attreditfunc)
	self.addtocommand('e', conteditfunc)
	self.addtocommand('t', anchorfunc)
	self.addtocommand('f', focusfunc)
    #

    # blockview gets a region in the form where it recursively
    #  places a node in this region; (x, y, w, h).
    #
    def mkBlockview(self, (x, y, w, h), node):
	type = node.GetType()

	obj = self.form.add_box(FRAME_BOX, x, y, w, h, '')
	if type in leaftypes:
	    obj.col1 = LEAFCOLOR
	elif type == 'bag':
	    obj.col1 = BAGCOLOR

	node.bv_form = self.form
	node.bv_obj = obj

	kids = node.GetChildren()
	node.bv_xywh = (x, y, w, h)
	if type in interiortypes:
	    # Create the open/close button:
	    bx = x + LMARG
	    by = y + h - TMARG - BH
	    o=self.form.add_button(NORMAL_BUTTON, bx, by, BW, BH, '')
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
		if type != 'par': # sequential or bag node
		    h = h / len(kids)
		    dx, dy = 0, h
		else: # parallel node
		    w = w / len(kids)
		    dx, dy = w, 0
		toosmall = ((h < TMARG+BMARG+BH) or  (w < LMARG+RMARG+BW))
		if toosmall:
		    node.bv_openclose.col1 = GL.RED
		    node.bv_toosmall = 1
		    # x, y = 0, 0
		    # w, h = 1, 1
		elif self.isclosedlocal(node):
		    o = node.bv_openclose
		    o.col1, o.col2 = o.col2, o.col1
		else:
		    x, y = x+LMARG, y+BMARG
		    # w, h = w-LMARG-RMARG, h-TMARG-BMARG
		    w, h = w-RMARG, h-TMARG
		if not self.isclosedlocal(node):
		    if node.GetType() != 'par':
			# Y points up, first node comes last!
			kids = kids[:]
			kids.reverse()
		    for child in kids:
			self.mkBlockview((x, y, w, h), child)
			x, y = x + dx, y + dy

    #
    # delete all the objects (made by blockview) form the node
    #
    def rmBlockview(self, node):
	try:
	    node.bv_obj.delete_object()
	    del node.bv_obj
	    node.bv_openclose.delete_object()
	    del node.bv_openclose
	    node.bv_labeltext.delete_object()
	    del node.bv_labeltext
	except AttributeError:
	    pass
	for child in node.GetChildren():
	    self.rmBlockview(child)
    #
    # getfocus - Called by other modules to get our focus
    #
    def getfocus(self):
	return self.focus
    #
    # fixfocus: called to move focus up if it becomes invisible.
    #
    def fixfocus(self):
	focus = self.focus
	if focus == self.root or not self.isclosed(focus):
	    self.setfocus(focus)
	    return
	parent = focus.GetParent()
	while self.isclosed(parent):
	    focus = parent
	    if focus == self.root:
		break
	    parent = focus.GetParent()
	self.setfocus(focus)
    #
    # presentlabels: sets the appropiate labels in the FORMS object.
    #
    def presentlabels(self, node):
	type = node.GetType()
	if type in leaftypes:
	    name = MMAttrdefs.getattr(node, 'name')
	    if node.bv_obj.w <= node.bv_obj.h:
		words = string.split(name)
		name = string.joinfields(words, '\n')
	    node.bv_obj.label = name
	    return
	label = MMAttrdefs.getattr(node, 'name')
	node.bv_labeltext.label = label
	node.bv_obj.label = ''
	num = 1
	if not self.isclosedlocal(node):
	    for child in node.GetChildren():
		self.presentlabels(child)
    #
    # change_focus_callback
    # called when user clicks on a node to grab the focus
    # the argument is the class 'blockview' itself.
    #
    def _change_focus_callback(self, obj, args):
	gl.winset(self.form.window) # XXX Funny, but seem to need this
	mx, my = fl.get_mouse()   # XXXX Too late, wrong mouse pos...
	node = self._find_node(self.rootview, (mx, my))
	if node == None:
	    print 'no node'
	    raise 'block view'
	self.globalsetfocus(node)
    #
    def globalsetfocus(self, node):
	if not self.is_showing():
	    return # Silently
	while node:
	    try:
		void = node.bv_obj.boxtype
		break
	    except AttributeError:
		node = node.GetParent()
	else:
	    gl.ringbell()
	    print 'BlockViewglobalsetfocus: sorry, cannot set focus'
	    return
	self.form.freeze_form()
	gl.winset(self.form.window)
	self.focus.bv_obj.boxtype = FRAME_BOX
	self.focus = node
	self.fixfocus()
	self.form.unfreeze_form()
    #
    # setfocus
    #
    def setfocus(self, node):
	node.bv_obj.boxtype = UP_BOX
	self.focus = node
    #
    # _init: initialize state
    #
    def _init(self, w, h):
	self.w, self.h = w, h
	self.focus = None
	self.commanddict = {}
    #
    # _find_node: given a mouse positioin, find the corresponding node
    # in the (possibly folded) tree
    #
    def _find_node(self, node, (x, y)):
	if self.isclosedlocal(node): return node

	for child in node.GetChildren():
	    if self._in_bounds(child, (x, y)) <> None:
		return  self._find_node(child, (x, y))
	return node
    #
    def _menu_callback(self, obj, args):
	index = obj.get_menu()
	if index:
	    self._do_command(args[index-1])
    #
    # command_callback: read which key is clicked and executes
    # the associated command.
    #
    def _command_callback(self, obj, args):
	if forms_v20:
	    key = obj.get_input()
	    obj.set_input('')
	else:
	    key = obj.get_default()
	self._do_command(key)
    #
    # button_callback: one of the buttons has been pressed
    #
    def _button_callback(self, obj, key):
	self._do_command(key)
    def _do_command(self, key):
	if self.commanddict.has_key(key):
	    self.commanddict[key](self)
	else:
	    gl.ringbell()

    def _openclose_callback(self, obj, node):
	if node.bv_toosmall: return
	node.bv_form.freeze_form()

	self.rmBlockview(node)
	node.SetAttr('closed', not node.GetRawAttrDef('closed', 0))
	self.mkBlockview(node.bv_xywh, node)
	self.fixfocus()
	node.bv_obj.show_object()		# show this node
	node.bv_openclose.show_object()		# show roundbutton
	node.bv_labeltext.show_object()
	self.presentlabels(node)

	node.bv_form.unfreeze_form()		

    def _in_bounds(self, node, (x, y)):
	o = node.bv_obj
	if  x > o.x and x < o.x+o.w and y > o.y and y < o.y+o.h:
	    return node
	else:
	    return None
    #
    # GetNewNode - Get new node
    #
    def GetNewNode(self):
	type = self.focus.GetType()
	child = self.root.context.newnode(type)
	return child
    #
    def fromclipboard(self):
	type, data = Clipboard.getclip()
	if type <> 'node' or data == None:
	    return None
	if data.context is not self.root.context:
	    data = data.CopyIntoContext(self.root.context)
	else:
	    Clipboard.setclip(type, data.DeepCopy())
	return data

    def toclipboard(self, node):
	if node == None:
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
	return node.GetRawAttrDef('closed', 0)
    #
    # isclosed - Is node closed, not knowing about ancestors?
    #
    def isclosed(self, node):
	if node <> self.root:
	    if self.isclosed(node.GetParent()):
		return 1
	return self.isclosedlocal(node)


def helpfunc(bv):
    import Help
    Help.givehelp('Hierarchy')

def attreditfunc(bv):
    import AttrEdit
    AttrEdit.showattreditor(bv.focus)


def conteditfunc(bv):
    import NodeEdit
    NodeEdit.showeditor(bv.focus)


# copy the focus node to the clipboard

def CopyNode(bv):
    node = bv.focus
    if node == None:
	gl.ringbell()
	return
    Clipboard.setclip('node', node.DeepCopy())


# delete the focussed node.
# focus switches to parent.

def _DeleteNode(bv, cb):
    node = bv.focus
    if node == bv.rootview:
	# This would crash
	fl.show_message('Please zoom out first', '', '')
	return
    em = bv.editmgr
    parent = node.GetParent()
    if parent == None:
	fl.show_message('sorry, cannot delete root', '', '')
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
    if nf == len(children)-1:
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
def DeleteNode(bv):
    _DeleteNode(bv, 0)
def CDeleteNode(bv):
    _DeleteNode(bv, 1)


# Insert a node before/after the focus.
# The node is created with the same type as the focus.
# Use Node Info to change this.

def _doInsertNode(bv, after, cb):
    node = bv.focus
    parent = node.GetParent()
    if parent == None:
	fl.show_message('You can\'t insert before/after the root', '', '')
	return
    if node == bv.rootview:
	# This would crash
	fl.show_message('Please zoom out first', '', '')
	return

    em = bv.editmgr
    if not em.transaction(): return

    kids = parent.GetChildren()
    i = kids.index(node)
    if after:
	i = i + 1

    if cb:
	newnode = bv.fromclipboard()
    else:
	newnode = bv.GetNewNode()
    if newnode == None:
	gl.ringbell()
	node.context.editmgr.rollback()
	return
    em.addnode(parent, i, newnode)
    bv.focus = newnode

    bv.changing_node = parent
    node.context.editmgr.commit()
    bv.changing_node = None
    if not cb:
	import NodeInfo
	NodeInfo.shownodeinfo(bv.toplevel, newnode)

def InsertBeforeNode(bv):
    _doInsertNode(bv, 0, 0)
def CInsertBeforeNode(bv):
    _doInsertNode(bv, 0, 1)
def InsertAfterNode(bv):
    _doInsertNode(bv, 1, 0)
def CInsertAfterNode(bv):
    _doInsertNode(bv, 1, 1)

def _doInsertParent(bv, type):
    node = bv.focus
    parent = node.GetParent()
    if parent == None:
	# This should really be allowed, but it's too hard
	fl.show_message('You can\'t insert above the root', '', '')
	return
    if node == bv.rootview:
	# The new node would be invisible at first
	fl.show_message('Please zoom out first', '', '')
	return

    em = bv.editmgr
    if not em.transaction(): return

    siblings = parent.GetChildren()
    index = siblings.index(node)
    em.delnode(node)
    newnode = bv.root.context.newnode(type)
    em.addnode(parent, index, newnode)
    em.addnode(newnode, 0, node)

    bv.focus = newnode

    bv.changing_node = parent
    em.commit()
    bv.changing_node = None

def InsertSeqParent(bv):
    _doInsertParent(bv, 'seq')
def InsertParParent(bv):
    _doInsertParent(bv, 'par')
def InsertBagParent(bv):
    _doInsertParent(bv, 'bag')


# Add a child node to a (possibly empty) seq/par node.

def _InsertChildNode(bv, cb):
    parent = bv.focus

    if (not parent.GetType() in interiortypes) or bv.isclosedlocal(parent):
	gl.ringbell()
	return

    em = bv.editmgr
    if not em.transaction(): return

    if cb:
	newnode = bv.fromclipboard()
    else:
	newnode = bv.GetNewNode()
    if newnode == None:
	gl.ringbell()
	node.context.editmgr.rollback()
	return
    em.addnode(parent, 0, newnode)

    bv.changing_node = parent
    bv.focus = newnode
    parent.context.editmgr.commit()
    bv.changing_node = None
    if not cb:
	import NodeInfo
	NodeInfo.shownodeinfo(bv.toplevel, newnode)

def InsertChildNode(bv):
    _InsertChildNode(bv, 0)
def CInsertChildNode(bv):
    _InsertChildNode(bv, 1)


def unzoomfunc(bv):
    if bv.rootview == bv.root:
	gl.ringbell()
	return

    bv.form.freeze_form()

    bv.rmBlockview(bv.rootview)		# get rid of all FORMS objects
    #
    bv.mkBlockview((0, 0, bv.w, bv.h), bv.rootview.GetParent())
    bv.fixfocus()
    bv.presentlabels(bv.rootview.GetParent())
    bv.setfocus(bv.focus)
    bv.form.unfreeze_form()
    bv.rootview = bv.rootview.GetParent()

def zoomfunc(bv):
    node = bv.focus

    while node.GetParent() <> bv.rootview:
	node = node.GetParent()
	if node == None:
	    gl.ringbell()
	    return

    nObj = node.GetParent().bv_obj
    x, y, w, h = nObj.x, nObj.y, nObj.w, nObj.h

    bv.form.freeze_form()
    bv.rmBlockview(bv.rootview)		# get rid of all FORMS objects
    #
    bv.mkBlockview((x, y, w, h), node)
    bv.fixfocus()
    bv.presentlabels(node)
    bv.setfocus(bv.focus)
    bv.form.unfreeze_form()
    bv.rootview = node


def infofunc(bv):
    node = bv.focus
    import NodeInfo
    NodeInfo.shownodeinfo(bv.toplevel, node)

def playfunc(bv):
    node = bv.focus
    bv.toplevel.player.playsubtree(node)

def anchorfunc(bv):
    node = bv.focus
    import AnchorEdit
    AnchorEdit.showanchoreditor(bv.toplevel, node)

def focusfunc(bv):
    bv.toplevel.channelview.globalsetfocus(bv.focus)


# This is mostly Jack's code, so...
# Local variables:
# py-indent-offset: 4
# end:
