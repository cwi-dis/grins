# Read attribute definitions from a file.
#
# Exported interface:
#
# attrdefs	A dictionary containing the raw attribute definitions
#		(initialized when this module is first imported).
#		The tuples are only 6 items, the name is not in there!
#
# usetypedef()	A function that maps a type definition to a (function,
#		argument) pair based upon a mapping of basic types.
#
# useattrdefs()	A function that calls usetypedef for all attributes
#		in attrdefs, for a given mapping, and returns a dictionary
#		containing all the results.
#
# getdef()	A function that returns an entry from attrdefs,
#		or invents something plausible if there is no entry.
#
# getnames()	A function that returns a sorted list of keys
#		in attrdefs.
#
# getattr()	A function that gets a node's attribute value, from
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
		value = node.GetInherAttrDef(attrname, None)
		if value = None:
			channelname = node.GetInherAttr('channel')
			channelattrdict = node.context.channeldict[channelname]
			if channelattrdict.has_key(attrname):
				value = channelattrdict[attrname]
			else:
				value = defaultvalue
	else:
		raise RuntimeError, 'bad inheritance ' +`inheritance` + \
				' for attr ' + `attrname`
	return value
