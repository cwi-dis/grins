__version__ = "$Id$"

import windowinterface

channeleditors = {}

def _inventname(ch):		# Invent file name from channel name
	import os
	for i in range(1,99):
		fn = ch + '.' + `i`
		if not os.path.exists(fn):
			return fn
	return fn

def _do_convert(node, fn):	# Convert imm node to ext
	em = node.GetContext().geteditmgr()
	if not em.transaction():
		return
	values = node.GetValues()
	f = open(fn, 'w')
	for i in values:
		f.write(i+'\n')
	f.close()
	em.setnodevalues(node,[])
	em.setnodetype(node,'ext')
	em.setnodeattr(node,'file',fn)
	em.commit()

class _Convert:
	def __init__(self, node):
		self.node = node
		windowinterface.FileDialog(
			'This is an internal node. Convert to external?',
			'.', '*', _inventname(node.GetChannelName()),
			self.ok, None, existing = 1)

	def ok(self, file):
		import os
		if os.path.exists(file):
			windowinterface.showmessage(
				'File already exists. Overwrite?',
				mtype = 'question', title = 'Overwrite?',
				callback = (self.convert, (file,)))
			return 1	# don't remove dialog
		self.convert(file)

	def convert(self, file):
		_do_convert(self.node, file)
		showeditor(self.node)

def _merge(f, filename):	# Merge editors file into data structures
	import string
	while 1:
		l = f.readline()
		if not l:
			break
		l = l[:-1]
		fields = string.splitfields(l,'@@')
		# Skip blank lines and comments
		if fields == [''] or fields[0][:1] == '#': continue
		if len(fields) <> 3:
			print 'Bad line in', `filename` + ':', l
			continue
		
		try:
			fil = open(fields[2], 'r')
		except IOError:
			_del_cll(fields[2],fields[0])
			continue

		fil.close()

		if not channeleditors.has_key(fields[0]):
			channeleditors[fields[0]] = {fields[1]:fields[2]}
		elif not channeleditors[fields[0]].has_key(fields[1]):
			channeleditors[fields[0]][fields[1]] = fields[2]

def _do_edit(cmd, filename):
	import os
	#cmd = 'file=%s; %s &' % (filename, cmd)
	cmd = '%s %s' % (cmd, filename)
	import win32api
	try:
		win32api.WinExec(cmd)
	except win32api.error, e:	
		print "Shell Channel, WinExec Error: ", e
	#void = os.system(cmd)

def _showmenu(menu, filename, type=None):	# Show (modal) editor choice dialog
	keys = menu.keys()
	keys.sort()
	list = []
	for key in keys:
		list.append(key, (_do_edit, (menu[key], filename)))
	list.append('New Application...', (brs_cll, (filename, type)))
	list.append(None)
	list.append('Delete Editor', (del_cll, (type,)))
	list.append('Cancel', None)
	w = windowinterface.Dialog(list, title = 'Choose',
				   prompt = 'Choose an editor:', grab = 1,
				   vertical = 0)
	w._hWnd.HookKeyStroke(helpcall,104)

# Added lines

def helpcall(params):
	import Help, win32ui
	Help.givehelp(win32ui.GetActiveWindow(), 'Edit Contents Dialog')


def yes_cl(type, name, filename):
	import cmif, os, string
	
	dirs = [cmif.findfile('editor')]
	for dirname in dirs:
		filname = os.path.join(dirname, '.win32_cmif_editors')
		try:
			f = open(filname, 'r')
		except IOError:
			continue
		str = type+'@@'+name+'@@'+filename #+ '\n'
		lines = f.readlines()
		f.close()
		
		try:
			f = open(filname, 'a')
		except IOError:
			continue
	
		if not str+'\n' in lines:
			f.write(str+'\n')
			fields = string.splitfields(str,'@@')
			if not channeleditors.has_key(fields[0]):
				channeleditors[fields[0]] = {fields[1]:fields[2]}
			elif not channeleditors[fields[0]].has_key(fields[1]):
				channeleditors[fields[0]][fields[1]] = fields[2]

		f.close()


def _del_cll(cmd, type):
	import string, cmif, os
	lis = string.splitfields(cmd, '\\')
	lis2 = string.splitfields(lis[len(lis)-1], '.')
	name = lis2[0]
	dirs = [cmif.findfile('editor')]
	for dirname in dirs:
		filname = os.path.join(dirname, '.win32_cmif_editors')
		try:
			f = open(filname, 'r')
		except IOError:
			continue
		str = type+'@@'+name+'@@'+cmd #+ '\n'
		#import pdb
		#pdb.set_trace()
		lines = f.readlines()
		f.close()
		
		try:
			f = open(filname, 'w')
		except IOError:
			continue
		f.write("")
		f.close()
		
		try:
			f = open(filname, 'a')
		except IOError:
			continue
		
		for l in lines:
			lis = string.splitfields(l, '@@')
			if lis[0]!=type or lis[1]!=name or lis[2]!=cmd+'\n':
				f.write(l)
			else:
				fields = string.splitfields(str,'@@')
				if channeleditors.has_key(fields[0]):
					if channeleditors[fields[0]].has_key(fields[1]):
						del channeleditors[fields[0]][fields[1]]

		f.close()


def del_cll(type):
	#import cmif, os, Htmlex, string
	#id, cmd, ext = Htmlex.FDlg("Choose an Application...", " ", "All Files|*.*||")
	ls = []
	if channeleditors.has_key(type):
		ls = channeleditors[type].keys()
		ls.append('Cancel')
	if ls:
		answer = windowinterface.multchoice('Editors in use:', ls, 0)
		if ls[answer] != 'Cancel':
			cmd = channeleditors[type][ls[answer]]
			_del_cll(cmd,type)
	#else:
	#	windowinterface.showmessage(
	#		'There are not active\n  editors for '+type, 
	#		grab = 1,mtype = 'information')


def brs_cll(filename, type):
	import os, Htmlex, string
	id, cmd, ext = Htmlex.FDlg("Choose an Application...", " ", "All Files|*.*||")
	print "cmd--->", cmd
	lis = string.splitfields(cmd, '\\')
	lis2 = string.splitfields(lis[len(lis)-1], '.')
	print lis2
	if type:
		#lst = [('Yes', (yes_cl,(type,lis2[0],cmd))),('No', None)]
		#wi = windowinterface.Dialog(lst, title = 'Question',
		#		   prompt = 'Do you want to add \n this editor to the \n existing editors ?\n', grab = 1,
		#		   vertical = 0)
		if id == 0: return
		windowinterface.showmessage(
			'Do you want to add \n this editor to the \n existing editors ?\n', grab = 1,
			mtype = 'question', callback = (yes_cl,(type,lis2[0],cmd)))
	if id == 0: return
	cmd = '%s %s' % (cmd, filename)
	import win32api
	try:
		win32api.WinExec(cmd)
	except win32api.error, e:	
		print "Shell Channel, WinExec Error: ", e
	#cmd = 'file=%s; %s &' % (filename, cmd)
	#cmd = '%s %s' % (cmd, filename)
	#void = os.system(cmd)

# End of added lines


# InitEditors - Initialize the module.
def InitEditors():
	# XXX Should add the directory where the .cmif file resides...
	# XXX (toplevel.dirname)
	import cmif, os
	#dirs = ['.', os.environ['HOME'], cmif.findfile('editor')]
	dirs = [cmif.findfile('editor')]
	for dirname in dirs:
		#filename = os.path.join(dirname, '.cmif_editors')
		filename = os.path.join(dirname, '.win32_cmif_editors')
		try:
			f = open(filename, 'r')
		except IOError:
			continue
		_merge(f, filename)
		f.close()

_LocalError = '_LocalError'

# showeditor - Show the editor (or selector) for a given node
def showeditor(node):
	if len(channeleditors) == 0:
		InitEditors()	
	if node.GetType() == 'imm':
		dummy = _Convert(node)
		return
	if node.GetType() <> 'ext':
		windowinterface.showmessage(
			'NodeEdit.showeditor: Only extern nodes can be edited',
			mtype = 'error')
		return
	
	import MMAttrdefs, MMurl
	url = MMAttrdefs.getattr(node,'file')
	utype, url = MMurl.splittype(url)
	if utype:
		windowinterface.showmessage(
			'NodeEdit.showeditor: cannot edit URL',
			mtype = 'warning')
		return
	filename = MMurl.url2pathname(url)
		
	#added lines
	import string
	print filename, node.GetContext().dirname
	if node.GetContext().dirname != None:
		filename = node.GetContext().dirname+filename
	print filename
	ls = string.splitfields(filename,'/')
	ls2 = []
	flag = 1
	print ls
	for word in ls:
		if len(word)==0:
			continue
		if flag==1:
			try:
				ind = string.index(word,'|')
			except ValueError:
				flag = 0
				continue
			else:
				if ind == 1:
					word = word[0]+':'
					ls2.append(word)
					flag = 0
					continue
		ls2.append(word)

	filename = string.joinfields(ls2, '\\')
	print filename		
	#end of added lines
	
	chtype = node.GetChannelType()
	import os
	if chtype == 'html' and not channeleditors.has_key('html'):
	    chtype = 'text'
	#if not channeleditors.has_key(chtype):
	#	cmd = _showmenu({}, filename, chtype)
	#	#windowinterface.showmessage(
	#	#	'NodeEdit.showeditor: no editors for chtype ' + chtype,
	#	#	mtype = 'warning')
	#	return
	if channeleditors.has_key(chtype):
		editor = channeleditors[chtype]
	else:
		editor = {}
	if type(editor) is type(''):
		_do_edit(editor, filename)
	else:
		cmd = _showmenu(editor, filename, chtype)

# Simple test program. Only tests editor file parsing.
def test():
	InitEditors()
	print channeleditors
