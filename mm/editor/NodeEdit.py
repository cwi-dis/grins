# Node content editor.
# Jack Jansen, November 1991.

import os
import gl
import fl
from FL import *
import string
import os
import flp

import MMExc
import MMAttrdefs
import MMParser
import MMWrite

error = 'NodeEditorError'
_LocalError = '_LocalError'
formdone = 'Form Done'

formdef = None

channeleditors = {}

def _inventname(ch):		# Invent file name from channel name
    for i in range(1,99):
	fn = ch + '.' + `i`
	if not _file_exists(fn):
	    return fn
    return fn

def _file_exists(fn):		# Return true if file exists
    import os
    try:
	void = os.stat(fn)
	return 1
    except os.error:
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
# to.
# Usage: call init() to create everything and work() to do the dialog.
#
class _convert_dialog:
    def init(self, node):
    	global formdef
	self.node = node
	self.doconvert = 0
	if formdef == None:
	    formdef = flp.parse_form('NodeEditForm', 'form')
	flp.create_full_form(self, formdef)
	self.err_groupshown = 0
	self.err_group.hide_object()
	chname = node.GetChannelName()
	self.input_filename.set_input(_inventname(chname))
	self.input_filename.set_input_return(1)
	return self
    def __repr__(self):
	return '<_convert_dialog instance, node=' + `self.node` + '>'
    def work(self):
	fl.deactivate_all_forms()
	self.form.show_form(PLACE_MOUSE,FALSE,'')
	try:
	    while 1:
		fl.do_forms()
	except formdone:
	    pass
	self.form.hide_form()
	fl.activate_all_forms()
	return self.doconvert
    def callback_input(self,*dummy):
	if self.err_groupshown:
	    self.err_groupshown = 0
	    self.err_group.hide_object()
    def callback_cancel(self,*dummy):
	raise formdone
    def callback_browser(self,*dummy):
	fn = self.input_filename.get_input()
	dir, file = os.path.split(fn)
	result = fl.file_selector('Select file', dir, '*', file)
	if result:
	    self.input_filename.set_input(result)
    def callback_convert(self,obj,value):
	fn = self.input_filename.get_input()
	if obj == self.button_convert and _file_exists(fn):
	    self.err_group.show_object()
	    self.err_groupshown = 1
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
	if fields == [''] or fields[0][:1] == '#': continue
	if len(fields) <> 3:
	    print 'Bad line in', `filename` + ':', l
	    continue
	if not channeleditors.has_key(fields[0]):
	    channeleditors[fields[0]] = {fields[1]:fields[2]}
	elif not channeleditors[fields[0]].has_key(fields[1]):
	    channeleditors[fields[0]][fields[1]] = fields[2]

def _showmenu(menu):	# Show (modal) editor choice dialog
    keys = menu.keys()
    keys.sort()
    keys.append('Cancel')
    import dialogs
    i = dialogs.multchoice('', keys, len(keys)-1)
    if 0 <= i < len(keys)-1:
	return menu[keys[i]]
    else:
	return None

# InitEditors - Initialize the module.
def InitEditors():
    # XXX Should add the directory where the .cmif file resides...
    # XXX (toplevel.dirname)
    import cmif
    dirs = ['.', os.environ['HOME'], cmif.findfile('mm4')]
    for dirname in dirs:
    	filename = os.path.join(dirname, '.cmif_editors')
    	try:
    		f = open(filename, 'r')
    	except IOError:
    		continue
	_merge(f, filename)
	f.close()

# showeditor - Show the editor (or selector) for a given node
def showeditor(node):
    if len(channeleditors) == 0:
	InitEditors()
    if node.GetType() == 'imm':
	done = _convert(node)
	if not done: return
    if node.GetType() <> 'ext':
	# Only extern nodes can be edited.
	gl.ringbell()
	return
    filename = MMAttrdefs.getattr(node,'file')
    chtype = node.GetChannelType()
    try:
	if not channeleditors.has_key(chtype): raise _LocalError
	editor = channeleditors[chtype]
	if type(editor) == type(''):
	    cmd = editor
	else:
	    cmd = _showmenu(editor)
	    if cmd == None:
		raise _LocalError
	cmd = 'file='+filename+' ; '+cmd+' &'
	void = os.system(cmd)
    except _LocalError:
	gl.ringbell()

# Simple test program. Only tests editor file parsing.
def test():
    InitEditors()
    print channeleditors

# This is mostly Jack's code, so...
# Local variables:
# py-indent-offset: 4
# end:
