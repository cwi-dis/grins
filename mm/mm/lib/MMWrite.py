# MMWrite -- Multimedia tree writing interface


from MMExc import *		# Exceptions


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
	_writeattrdict(x.GetAttrDict(), None, fp)
	fp.write(')')
	if type in ('seq', 'par', 'grp'):
		for child in x.GetChildren():
			fp.write('\n')
			_writenode(child, fp)
	elif type = 'imm':
		for value in x.GetValues():
			fp.write(' ')
			_writeany(value, None, fp)
	elif type = 'ext':
		pass
	else:
		raise RuntimeError, 'bad node type in _writenode'
	fp.write(')')


# Attribute-specific writers.
#
# These all have three arguments: the value, some parameter, and the file.
# The parameter may be a dummy, or a (func, arg) pair, or perhaps a list
# of (func, arg) pairs.
#
def _writegeneric(value, (func, arg), fp):
	func(value, arg, fp)
#
def _writeint(value, dummy, fp):
	fp.write(`int(value)`)
#
def _writefloat(value, dummy, fp):
	fp.write(`float(value)`)
#
def _writestring(value, dummy, fp):
	fp.write(`value`)
#
def _writename(value, dummy, fp):
	fp.write(value)
#
def _writeuid(value, dummy, fp):
	fp.write(`value`)
#
def _writebool(value, dummy, fp):
	if value:
		fp.write('1')
	else:
		fp.write('0')
#
def _writeenum(value, dummy, fp):
	fp.write(value)
#
def _writetuple(value, funcarglist, fp):
	if len(value) <> len(funcarglist):
		raise CheckError, '_writetuple() with non-matching length'
	sep = ''
	for i in range(len(funcarglist)):
		fp.write(sep)
		sep = ' '
		func, arg = funcarglist[i]
		func(value[i], arg, fp)
#
def _writelist(value, (func, arg), fp):
	sep = ''
	for v in value:
		fp.write(sep)
		sep = ' '
		func(v, arg, fp)
#
def _writedict(value, (func, arg), fp):
	keys = value.keys()
	keys.sort()
	for key in keys:
		fp.write('(' + `key` + ' ')
		func(value[key], arg, fp)
		fp.write(')\n')
#
def _writenamedict(value, (func, arg), fp):
	keys = value.keys()
	keys.sort()
	for key in keys:
		fp.write('(' + key + ' ')
		func(value[key], arg, fp)
		fp.write(')\n')
#
def _writeattrdict(value, dummy, fp):
	keys = value.keys()
	keys.sort()
	for key in keys:
		_writeattr(key, value[key], fp)
#
def _writeattr(name, value, fp): # Subroutine to write an attribute-value pair
	fp.write('(' + name + ' ')
	if _attrwriters.has_key(name):
		func, arg = _attrwriters[name]
	else:
		func, arg = _writeany, None
	func(value, arg, fp)
	fp.write(')\n')
#
def _writeenclosed(value, (func, arg), fp):
	fp.write('(')
	func(value, arg, fp)
	fp.write(')')
#
def _writetype(value, dummy, fp):
	type, arg = value
	fp.write('(' + type)
	if type = 'enum':
		for name in arg: fp.write(' ' + name)
	elif type = 'tuple':
		for t in arg:
			fp.write(' ')
			_writetype(t, None, fp)
	elif type in ('list', 'dict', 'namedict', 'enclosed'):
		_writetype(arg, None, fp)
	fp.write(')')
#
def _writeany(value, dummy, fp):
	if type(value) in (type(0), type(0.0), type('')):
		fp.write(`value`)
	elif type(value) = type({}):
		fp.write('(')
		_writedict(value, (_writeany, dummy), fp)
		fp.write(')')
	elif type(value) in (type(()), type([])):
		fp.write('(')
		_writelist(value, (_writeany, None), fp)
		fp.write(')')
	else:
		raise AssertError, 'writing unexpected value'


# Table mapping all the basic types to the functions to write them
#
_basicwriters = { \
	'int': _writeint, \
	'float': _writefloat, \
	'string': _writestring, \
	'name': _writename, \
	'uid': _writeuid, \
	'bool': _writebool, \
	'enum': _writeenum, \
	'tuple': _writetuple, \
	'list': _writelist, \
	'dict': _writedict, \
	'namedict': _writenamedict, \
	'attrdict': _writeattrdict, \
	'enclosed': _writeenclosed, \
	'type': _writetype, \
	'any': _writeany, \
	}


# Dictionary mapping attribute names to writing functions.
#
import MMAttrdefs
_attrwriters = MMAttrdefs.useattrdefs(_basicwriters)
