# Node content editor.

import path
import gl
import fl
from FL import *
import string
import posix

import MMExc
import MMAttrdefs
import MMParser
import MMWrite

error = 'NodeEditorError'

channeleditors = {}

def InitEditors():
    # First try:
    try:
	f = open('.cmif_editors', 'r')
	_merge(f)
    except RuntimeError:
	pass
    # Second try:
    home = posix.environ['HOME']
    try:
	f = open(home + '.cmif_editors', 'r')
	_merge(f)
    except RuntimeError:
	pass
    # Third try:
    try:
	f = open('/ufs/guido/mm/demo/mm4/.cmif_editors', 'r')
	_merge(f)
    except RuntimeError:
	pass

def _merge(f):
    while 1:
	l = f.readline()
	if not l:
	    break
	l = l[:-1]
	fields = string.splitfields(l,':')
	if len(fields) <> 3:
	    raise error, 'Syntax error in editors file'
	if not fields[1]:		# Case 1: unlabeled command
	    if not channeleditors.has_key(fields[0]):
		channeleditors[fields[0]] = fields[2]
	    # Otherwise we skip this line, it was done already
	else:				# Case 2: labeled command
	    if not channeleditors.has_key(fields[0]):
		channeleditors[fields[0]] = {fields[1]:fields[2]}
	    elif not channeleditors[fields[0]].has_key(fields[1]):
		channeleditors[fields[0]][fields[1]] = fields[2]

def showeditor(node):
    if len(channeleditors) = 0:
	InitEditors()
    if node.GetType() <> 'ext':
	# Only extern nodes can be edited.
	gl.ringbell()
	return
    filename = MMAttrdefs.getattr(node,'file')
    try:
	chtype = _getchtype(node)
	editor = channeleditors[chtype]
	if type(editor) = type(''):
	    cmd = editor
	else:
	    cmd = _showmenu(editor)
	    if cmd = None:
		raise RuntimeError
	cmd = 'file='+filename+' ; '+cmd+' &'
	void = posix.system(cmd)
    except RuntimeError:
	gl.ringbell()

def _getchtype(node):
    chname = MMAttrdefs.getattr(node, 'channel')
    context = node.GetContext()
    return context.channeldict[chname]['type']

def _showmenu(menu):
    nkeys = len(menu)+1
    form = fl.make_form(NO_BOX,130,nkeys*30+10)
    void = form.add_box(UP_BOX,0,0,130,nkeys*30+10,'')
    cancel = form.add_button(RETURN_BUTTON,5,5,120,30,'Cancel')
    cancel.boxtype = FRAME_BOX
    pos = 35
    for i in menu.keys():
	void = form.add_button(NORMAL_BUTTON,5,pos,120,30,i)
	void.boxtype = FRAME_BOX
	pos = pos + 30
    form.show_form(PLACE_MOUSE,0,'')
    obj = fl.do_forms()
    choice = obj.label
    if menu.has_key(choice):
	return menu[choice]
    else:
	return None

def test():
    InitEditors()
    print channeleditors
