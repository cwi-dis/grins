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
		self.dialog = windowinterface.FileDialog(
			'This is an internal node. Convert to external?',
			'.', '*', _inventname(node.GetChannelName()),
			self.ok, None)

	def ok(self, file):
		import os
		if os.path.exists(file):
			windowinterface.showmessage(
				'File already exists. Overwrite?',
				type = 'question', title = 'Overwrite?',
				callback = (self.convert, (file,)))
			return 1	# don't remove dialog
		self.convert(file)

	def convert(self, file):
		self.dialog.close()
		_do_convert(self.node, file)
		showeditor(self.node)

def _merge(f, filename):	# Merge editors file into data structures
	import string
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
	i = windowinterface.multchoice('Choose an editor:', keys, len(keys)-1)
	if 0 <= i < len(keys)-1:
		return menu[keys[i]]
	else:
		return None

# InitEditors - Initialize the module.
def InitEditors():
	# XXX Should add the directory where the .cmif file resides...
	# XXX (toplevel.dirname)
	import cmif, os
	dirs = ['.', os.environ['HOME'], cmif.findfile('editor')]
	for dirname in dirs:
		filename = os.path.join(dirname, '.cmif_editors')
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
		print 'NodeEdit.showeditor: Only extern nodes can be edited'
		windowinterface.beep()
		return
	import MMAttrdefs
	filename = MMAttrdefs.getattr(node,'file')
	chtype = node.GetChannelType()
	try:
		import os
		if chtype == 'html' and not channeleditors.has_key('html'):
		    chtype = 'text'
		if not channeleditors.has_key(chtype):
			print 'NodeEdit.showeditor: no editors for chtype', chtype
			raise _LocalError
		editor = channeleditors[chtype]
		if type(editor) == type(''):
			cmd = editor
		else:
			cmd = _showmenu(editor)
			if cmd == None:
				print 'NodeEdit.showeditor: no editor chosen'
				raise _LocalError
		cmd = 'file='+filename+' ; '+cmd+' &'
		void = os.system(cmd)
	except _LocalError:
		windowinterface.beep()

# Simple test program. Only tests editor file parsing.
def test():
	InitEditors()
	print channeleditors
