# Node content editor.
# Jack Jansen, November 1991.

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

import NodeEditForm

error = 'NodeEditorError'
formdone = 'Form Done'

channeleditors = {}

def _inventname(ch):		# Invent file name from channel name
    for i in range(1,99):
	fn = ch + '.' + `i`
	if not _file_exists(fn):
	    return fn
    return fn

def _file_exists(fn):		# Return true if file exists
    import posix
    try:
	void = posix.stat(fn)
	return 1
    except posix.error:
	return 0

def _do_convert(node, fn):	# Convert imm node to ext
    em = node.GetContext().geteditmgr()
    if not em.transaction(): return
    values = node.GetValues()
    f = open(fn, 'w')
    for i in values:
	f.write(i+'\n')
    f.close()
    em.setnodevalues(node,[])
    em.setnodetype(node,'ext')
    em.setnodeattr(node,'file',fn)
    em.commit()


#
# This class handles the dialog that asks for the file name to convert
# to. It needs a bit of work, since it is modal but doesn't lock out
# events for other forms at the moemnt.
# Usage: call init() to create everything and work() to do the dialog.
#
class _convert_dialog():
    def init(self, node):
	self.node = node
	self.doconvert = 0
	self.form = NodeEditForm.mk_form_convertform(self)
	self.errgroup = self.form.bgn_group()
	dummy = NodeEditForm.mk_form_err(self,self.form)
	self.form.end_group()
	self.errgroupshown = 0
	self.errgroup.hide_object()
	chname = MMAttrdefs.getattr(node, 'channel')
	self.input_filename.set_input(_inventname(chname))
	return self
    def work(self):
	self.form.show_form(PLACE_MOUSE,FALSE,'')
	try:
	    while 1:
		fl.do_forms()
	except formdone:
	    pass
	self.form.hide_form()
	return self.doconvert
    def callback_input(self,dummy):
	if self.errgroupshown:
	    self.errgroupshown = 0
	    self.errgroup.hide_object()
    def callback_cancel(self,dummy):
	raise formdone
    def callback_browser(self,dummy):
	fn = self.input_filename.get_input()
	dir, file = path.split(fn)
	result = fl.file_selector('Select file', dir, '*', file)
	if result:
	    self.input_filename.set_input(result)
    def callback_convert(self,(obj,value)):
	fn = self.input_filename.get_input()
	if obj == self.button_convert and _file_exists(fn):
	    self.errgroup.show_object()
	    self.errgroupshown = 1
	    return
	_do_convert(self.node, fn)
	self.doconvert = 1
	raise formdone

def _convert(node):	# Do conversion dialog and conversion itself
    dialog = _convert_dialog().init(node)
    rv = dialog.work()
    return rv

def _merge(f, filename):	# Merge editors file into data structures
    while 1:
	l = f.readline()
	if not l:
	    break
	l = l[:-1]
	fields = string.splitfields(l,':')
	# Skip blank lines and comments
	if fields = [''] or fields[0][:1] = '#': continue
	if len(fields) <> 3:
	    print 'Bad line in', `filename` + ':', l
	    continue
	if not fields[1]:		# Case 1: unlabeled command
	    if not channeleditors.has_key(fields[0]):
		channeleditors[fields[0]] = fields[2]
	    # Otherwise we skip this line, it was done already
	else:				# Case 2: labeled command
	    if not channeleditors.has_key(fields[0]):
		channeleditors[fields[0]] = {fields[1]:fields[2]}
	    elif not channeleditors[fields[0]].has_key(fields[1]):
		channeleditors[fields[0]][fields[1]] = fields[2]

def _getchtype(node):	# Get channel type for given node
    chname = MMAttrdefs.getattr(node, 'channel')
    context = node.GetContext()
    return context.channeldict[chname]['type']

def _showmenu(menu):	# Show (modal) editor choice dialog
    nkeys = len(menu)+1
    form = fl.make_form(NO_BOX,130,nkeys*30+10)
    void = form.add_box(UP_BOX,0,0,130,nkeys*30+10,'')
    cancel = form.add_button(RETURN_BUTTON,5,5,120,30,'Cancel')
    cancel.boxtype = FRAME_BOX
    pos = 35
    keys = menu.keys()
    keys.sort()
    for i in keys:
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


# InitEditors - Initialize the module.
def InitEditors():
    dirs = ['.', posix.environ['HOME'], '/ufs/guido/mm/demo/mm4']
    for dirname in dirs:
    	filename = path.join(dirname, '.cmif_editors')
    	try:
    		f = open(filename, 'r')
    	except:
    		continue
	_merge(f, filename)
	f.close()

# showeditor - Show the editor (or selector) for a given node
def showeditor(node):
    if len(channeleditors) = 0:
	InitEditors()
    if node.GetType() = 'imm':
	done = _convert(node)
	if not done: return
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

# Simple test program. Only tests editor file parsing.
def test():
    InitEditors()
    print channeleditors
