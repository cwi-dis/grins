# MMWrite -- Multimedia tree writing interface


# Exceptions

AssertError = 'MMTree.AssertError'


# Write a node to a CMF file, given by filename

def WriteFile(root, filename):
	WriteOpenFile(root, open(filename, 'w'))


# Write a node to a CMF file that is already open (for writing)

def WriteOpenFile(root, fp):
	root.attrdict['styledict'] = root.context.styledict
	_writenode(root, fp)
	del root.attrdict['styledict']
	fp.write('\n')


# Private functions to write nodes to a file.


# Write a node
#
def _writenode(x, fp):
	type = x.GetType()
	uid = x.GetUID()
	fp.write('(' + type + ' ' + `uid` + ' (')
	_writedict(x.GetAttrDict(), fp)
	fp.write(')')
	if type in ('seq', 'par', 'grp'):
		for child in x.GetChildren():
			fp.write('\n')
			_writenode(child, fp)
	elif type = 'imm':
		for value in x.GetValues():
			fp.write(' ')
			_writevalue(value, fp)
	elif type = 'ext':
		pass
	else:
		raise RuntimeError, 'bad node type in _writenode'
	fp.write(')')


# Write a dictionary, without outer parentheses.
# XXX This assumes the keys are identifiers
#
def _writedict(dict, fp):
	keys = dict.keys()
	keys.sort()
	for key in keys:
		fp.write('(' + key)
		val = dict[key]
		if type(val) in (type(()), type([])):
			for v in val:
				fp.write(' ')
				_writevalue(v, fp)
		elif type(val) = type({}):
			_writedict(val, fp)
		else:
			fp.write(' ')
			_writevalue(dict[key], fp)
		fp.write(')\n')


# Write an arbitrary value (really one of a few known types)
# XXX This doesn't distinguish between names and strings
#
def _writevalue(value, fp):
	if type(value) in (type(0), type(0.0), type('')):
		fp.write(`value`)
	elif type(value) = type({}):
		fp.write('(')
		_writedict(value, fp)
		fp.write(')')
	elif type(value) in (type(()), type([])):
		fp.write('(')
		for v in value:
			_writevalue(v, fp)
		fp.write(')')
	elif value = None:
		fp.write('()')
	else:
		raise AssertError, 'writing unexpected value'

