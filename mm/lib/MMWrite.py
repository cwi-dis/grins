# MMWrite -- Multimedia tree writing interface


from MMExc import *		# Exceptions
from MMNode import alltypes, leaftypes, interiortypes


# Write a node to a CMF file, given by filename

def WriteFile(root, filename):
	WriteOpenFile(root, open(filename, 'w'))


# Write a node to a CMF file that is already open (for writing)

def WriteOpenFile(root, fp):
	root.attrdict['styledict'] = root.context.styledict
	root.attrdict['hyperlinks'] = root.context.hyperlinks.getall()
	clist = []
	for cname in root.context.channelnames:
		clist.append(cname, root.context.channeldict[cname])
	root.attrdict['channellist'] = clist
	writenode(root, fp)
	del root.attrdict['styledict']
	del root.attrdict['hyperlinks']
	del root.attrdict['channellist']
	fp.write('\n')


# Private functions to write nodes to a file.


# Write a node
#
def writenode(x, fp):
	type = x.GetType()
	uid = x.GetUID()
	fp.write('(' + type + ' ' + `uid` + ' (')
	writeattrdict(x.GetAttrDict(), None, fp)
	fp.write(')')
	if type in interiortypes:
		for child in x.GetChildren():
			fp.write('\n')
			writenode(child, fp)
	elif type == 'imm':
		for value in x.GetValues():
			fp.write('\n')
			writeany(value, None, fp)
	elif type == 'ext':
		pass
	else:
		raise CheckError, 'bad node type in writenode'
	fp.write(')')


# Attribute-specific writers.
#
# These all have three arguments: the value, some parameter, and the file.
# The parameter may be a dummy, or a (func, arg) pair, or perhaps a list
# of (func, arg) pairs.
#
def writegeneric(value, (func, arg), fp):
	func(value, arg, fp)
#
def writeint(value, dummy, fp):
	fp.write(`int(value)`)
#
def writefloat(value, dummy, fp):
	fp.write(`float(value)`)
#
def writestring(value, dummy, fp):
	fp.write(`value`)
#
import string
namechars = string.letters + string.digits + '_'
def writename(value, dummy, fp):
	needquote = 0
	if value == '':
		needquote = 1
	else:
		for c in value:
			if c not in namechars:
				needquote = 1
				break
	if needquote:
		value = `value`
	fp.write(value)
#
def writeuid(value, dummy, fp):
	fp.write(`value`)
#
def writebool(value, dummy, fp):
	if value:
		fp.write('on')
	else:
		fp.write('off')
#
def writeenum(value, dummy, fp):
	writename(value, None, fp)
#
def writetuple(value, funcarglist, fp):
	if len(value) <> len(funcarglist):
		raise CheckError, 'writetuple() with non-matching length'
	for i in range(len(funcarglist)):
		fp.write(' ')
		func, arg = funcarglist[i]
		func(value[i], arg, fp)
#
def writelist(value, (func, arg), fp):
	for v in value:
		fp.write(' ')
		func(v, arg, fp)
#
def writedict(value, (func, arg), fp):
	keys = value.keys()
	keys.sort()
	for key in keys:
		fp.write('(' + `key` + ' ')
		func(value[key], arg, fp)
		fp.write(')\n')
#
def writenamedict(value, (func, arg), fp):
	keys = value.keys()
	keys.sort()
	for key in keys:
		fp.write('(')
		writename(key, None, fp)
		fp.write(' ')
		func(value[key], arg, fp)
		fp.write(')\n')
#
def writeattrdict(value, dummy, fp):
	keys = value.keys()
	keys.sort()
	for key in keys:
		writeattr(key, value[key], fp)
#
def writeattr(name, value, fp): # Subroutine to write an attribute-value pair
	fp.write('(')
	writename(name, None, fp)
	fp.write(' ')
	if attrwriters.has_key(name):
		func, arg = attrwriters[name]
	else:
		func, arg = writeany, None
	func(value, arg, fp)
	fp.write(')\n')
#
def writeenclosed(value, (func, arg), fp):
	fp.write('(')
	func(value, arg, fp)
	fp.write(')')
#
def writetype(value, dummy, fp):
	type, arg = value
	fp.write('(' + type)
	if type == 'enum':
		for name in arg:
			fp.write(' ')
			writename(name)
	elif type == 'tuple':
		for t in arg:
			fp.write(' ')
			writetype(t, None, fp)
	elif type in ('list', 'dict', 'namedict', 'enclosed'):
		writetype(arg, None, fp)
	fp.write(')')
#
def writeany(value, dummy, fp):
	if type(value) in (type(0), type(0.0), type('')):
		fp.write(`value`)
	elif type(value) == type({}):
		fp.write('(')
		writedict(value, (writeany, dummy), fp)
		fp.write(')')
	elif type(value) in (type(()), type([])):
		fp.write('(')
		writelist(value, (writeany, None), fp)
		fp.write(')')
	else:
		print 'Cannot write value:', value
		raise AssertError, 'writing unexpected value'


# Table mapping all the basic types to the functions to write them
#
basicwriters = { \
	'int': writeint, \
	'float': writefloat, \
	'string': writestring, \
	'name': writename, \
	'uid': writeuid, \
	'bool': writebool, \
	'enum': writeenum, \
	'tuple': writetuple, \
	'list': writelist, \
	'dict': writedict, \
	'namedict': writenamedict, \
	'attrdict': writeattrdict, \
	'enclosed': writeenclosed, \
	'type': writetype, \
	'any': writeany, \
	}


# Dictionary mapping attribute names to writing functions.
#
import MMAttrdefs
attrwriters = MMAttrdefs.useattrdefs(basicwriters)


# Interface to return a string representation of a value given a typedef.
#
def valuerepr(value, typedef):
	fp = StringOutputNoNL().init()
	writerdef = MMAttrdefs.usetypedef(typedef, basicwriters)
	writegeneric(value, writerdef, fp)
	return fp.get()

class StringOutputNoNL:
	def init(self):
		self.buf = ''
		return self
	def __repr__(self):
		return '<StringOutputNoNL instance, buf=' + `self.buf` + '>'
	def write(self, str):
		if str[-1:] == '\n': str = str[:-1]
		self.buf = self.buf + str
	def get(self):
		return self.buf
