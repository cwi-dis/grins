# Read attribute definitions from a file.
#
# Exported interface:
#
# attrdefs	a dictionary containing the raw attribute definitions
#		(initialized when this module is first imported)
#
# usetypedef()	a function that maps a type definition to a (function,
#		argument) pair based upon a mapping of basic types
#
# useattrdefs()	a function that calls usetypedef for all attributes
#		in attrdefs, for a given mapping, and returns a dictionary
#		containing all the results
#
# getdef()	a function that returns an entry from attrdefs,
#		or invents something plausible if there is no entry
#
# getnames()	a function that returns a sorted list of keys
#		in attrdefs.
#
# In the future there will be an interface to read attribute definitions
# from other files as well; attribute definitions will be channel-specific.


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
			parser.close()
			if dict.has_key(attrname):
				print 'Warning: duplicate attr def', attrname
			dict[attrname] = typedef, defaultvalue, \
					 labeltext, displayername, helptext
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
	# Undefuned attribute -- fake something reasonable
	return (attrname, ('any', None), None, '', 'default', '')
#
def getnames():
	names = attrdefs.keys()
	names.sort()
	return names
