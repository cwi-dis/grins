# Read attribute definitions from a file.
#
# Exported interface (in reverse order of importance :-( ):
#
# attrdefs	A dictionary containing the raw attribute definitions
#		(initialized when this module is first imported).
#		The tuples are only 6 items, the name is not in there!
#
# valuerepr(name, value)
#		Return a string representation of an attribute.
#
# parsevalue(name, string, context)
#		Parse a string into an attribute value.
#
# usetypedef(typedef, mapping)
#		A function that maps a type definition to a (function,
#		argument) pair based upon a mapping of basic types.
#
# useattrdefs(mapping)
#		A function that calls usetypedef for all attributes
#		in attrdefs, for a given mapping, and returns a dictionary
#		containing all the results.
#
# getdef(name)	A function that returns an entry from attrdefs,
#		or invents something plausible if there is no entry.
#
# getnames()	A function that returns a sorted list of keys
#		in attrdefs.
#
# getdefattr(node, name)
#		A function that gets the default value for a node's
#		attribute, *ignoring* the node's raw attribute list.
#
# getattr(node, name)
#		A function that gets a node's attribute value, from
#		the node or from several defaults, guided by the
#		attribute definition.  If this fails your tree is broken!


from MMExc import *
import MMParser
import sys


# The file from which the attribute definitions are read.
#
ATTRDEFS = '/ufs/guido/mm/demo/lib/Attrdefs'


# Parse a file containing attribute definitions.
#
def readattrdefs(filename):
	fp = open(filename, 'r')
	parser = MMParser.MMParser().init(fp, None)	# Note -- no context!
	dict = {}
	#
	try:
		while parser.peektoken():
			parser.open()
			attrname = parser.getnamevalue(None)
			typedef = parser.gettypevalue(None)
			xtypedef= typedef
			if typedef[0] in ('tuple', 'list', \
					  'dict', 'namedict', 'attrdict'):
				xtypedef = 'enclosed', typedef
			defaultvalue = parser.getgenericvalue( \
				usetypedef(xtypedef, \
					   MMParser.MMParser.basicparsers))
			labeltext = parser.getstringvalue(None)
			displayername = parser.getnamevalue(None)
			helptext = parser.getstringvalue(None)
			if parser.peektoken() = ')':
				inheritance = 'normal'
			else:
				inheritance = parser.getenumvalue( \
				    ['raw', 'normal', 'inherited', 'channel'])
			parser.close()
			if dict.has_key(attrname):
				print 'Warning: duplicate attr def', attrname
			dict[attrname] = typedef, defaultvalue, labeltext, \
				displayername, helptext, inheritance
	except EOFError:
		parser.reporterror(filename, 'Unexpected EOF', sys.stderr)
		raise EOFError
	except SyntaxError, msg:
		if type(msg) = type(()):
			gotten, expected = msg
			msg = 'got "'+gotten+'", expected "'+expected+'"'
		parser.reporterror(filename, \
				'Syntax error: ' + msg, sys.stderr)
		raise SyntaxError, msg
	except TypeError, msg:
		if type(msg) = type(()):
			gotten, expected = msg
			msg = 'got "'+gotten+'", expected "'+expected+'"'
		parser.reporterror(filename, 'Type error: ' + msg, sys.stderr)
		raise TypeError, msg
	#
	return dict


# Map a typedef to a (func, arg) pair.
#
def usetypedef(typedef, mapping):
	type, rest = typedef
	func = mapping[type]
	arg = None
	if type = 'enum':
		arg = rest
	elif type = 'tuple':
		arg = []
		for td in rest:
			arg.append(usetypedef(td, mapping))
	elif type in ('list', 'dict', 'namedict', 'enclosed'):
		arg = usetypedef(rest, mapping)
	return func, arg


# Use the type definitions from the attrdefs table.
#
def useattrdefs(mapping):
	dict = {}
	for attrname in attrdefs.keys():
		dict[attrname] = usetypedef(attrdefs[attrname][0], mapping)
	return dict


# Initialize the attrdefs table.
#
attrdefs = readattrdefs(ATTRDEFS)


# Functional interface to the attrdefs table.
#
def getdef(attrname):
	if attrdefs.has_key(attrname):
		return attrdefs[attrname]
	# Undefined attribute -- fake something reasonable
	return (('any', None), None, '', 'default', '',  'normal')
#
def getnames():
	names = attrdefs.keys()
	names.sort()
	return names


# Get an attribute of a node according to the rules.
#
def getattr(node, attrname):
	attrdef = getdef(attrname)
	inheritance = attrdef[5]
	defaultvalue = attrdef[1]
	if inheritance = 'raw':
		return node.GetRawAttrDef(attrname, defaultvalue)
	elif inheritance = 'normal':
		return node.GetAttrDef(attrname, defaultvalue)
	elif inheritance = 'inherited':
		return node.GetInherAttrDef(attrname, defaultvalue)
	elif inheritance = 'channel':
		try:
			return node.GetInherAttr(attrname)
		except NoSuchAttrError:
			try:
				cname = node.GetInherAttr('channel')
				attrdict = node.context.channeldict[cname]
				return attrdict[attrname]
			except:
				return defaultvalue
	else:
		raise RuntimeError, 'bad inheritance ' +`inheritance` + \
				' for attr ' + `attrname`


# Get the default value for a node's attribute, *ignoring* its own value
#
def getdefattr(node, attrname):
	attrdef = getdef(attrname)
	inheritance = attrdef[5]
	defaultvalue = attrdef[1]
	if inheritance = 'raw':
		return defaultvalue
	elif inheritance = 'normal':
		try:
			return node.GetDefAttr(attrname)
		except NoSuchAttrError:
			return defaultvalue
	elif inheritance = 'inherited':
		try:
			return node.GetDefInherAttr(attrname)
		except NoSuchAttrError:
			return defaultvalue
	elif inheritance = 'channel':
		try:
			return node.GetDefInherAttr(attrname)
		except NoSuchAttrError:
			try:
				cname = node.GetInherAttr('channel')
				attrdict = node.context.channeldict[cname]
				return attrdict[attrname]
			except:
				return defaultvalue
	else:
		raise RuntimeError, 'bad inheritance ' +`inheritance` + \
				' for attr ' + `attrname`

def valuerepr(name, value):
	import MMWrite
	return MMWrite.valuerepr(value, getdef(name)[0])


def parsevalue(name, string, context):
	import MMParser
	typedef = ('enclosed', getdef(name)[0])
	return MMParser.parsevalue('('+string+')', typedef, context)
