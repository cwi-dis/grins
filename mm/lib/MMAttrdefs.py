__version__ = "$Id$"

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


from MMStat import _stat
from MMExc import *
import MMParser
import sys
import os
from stat import ST_MTIME
import marshal

verbose = 1

# Parse a file containing attribute definitions.
#
def readattrdefs(fp, filename):
	filename_py = filename + '.py'
	if verbose:
		print 'Reading attributes from', filename, '...'
	parser = MMParser.MMParser(fp, None)	# Note -- no context!
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
			if parser.peektoken() == ')':
				inheritance = 'normal'
			else:
				inheritance = parser.getenumvalue( \
				    ['raw', 'normal', 'inherited', 'channel'])
			parser.close()
			if dict.has_key(attrname):
			    if verbose:
				print 'Warning: duplicate attr def', attrname
			dict[attrname] = typedef, defaultvalue, labeltext, \
				displayername, helptext, inheritance
	except EOFError:
		parser.reporterror(filename, 'Unexpected EOF', sys.stderr)
		raise EOFError
	except MSyntaxError, msg:
		if type(msg) is type(()):
			gotten, expected = msg
			msg = 'got "'+gotten+'", expected "'+expected+'"'
		parser.reporterror(filename, \
				'Syntax error: ' + msg, sys.stderr)
		raise MSyntaxError, msg
	except MTypeError, msg:
		if type(msg) is type(()):
			gotten, expected = msg
			msg = 'got "'+gotten+'", expected "'+expected+'"'
		parser.reporterror(filename, 'Type error: ' + msg, sys.stderr)
		raise MTypeError, msg
	#
	try:
		sf = os.stat(filename)
		fpc = open(filename_py, 'w')
		import pprint
		if verbose:
		    print 'Writing compiled attributes to', filename_py
		fpc.write('mtime = %s\nAttrdefs = ' % sf[ST_MTIME])
		fpc.write(pprint.pformat(dict))
		fpc.write('\n')
		fpc.close()
	except IOError, msg:
		print 'Can\'t write compiled attributes to', filename_com
		print msg[1]
	if verbose:
	    print 'Done.'
	return dict


# Map a typedef to a (func, arg) pair.
#
def usetypedef(typedef, mapping):
	##_stat('MMAttrdefs.usetypedef')
	type, rest = typedef
	func = mapping[type]
	arg = None
	if type == 'enum':
		arg = rest
	elif type == 'tuple':
		arg = []
		for td in rest:
			arg.append(usetypedef(td, mapping))
	elif type in ('list', 'dict', 'namedict', 'enclosed'):
		arg = usetypedef(rest, mapping)
	return func, arg


# Use the type definitions from the attrdefs table.
#
def useattrdefs(mapping):
	##_stat('MMAttrdefs.useattrdefs')
	dict = {}
	for attrname in attrdefs.keys():
		dict[attrname] = usetypedef(attrdefs[attrname][0], mapping)
	return dict


# Functional interface to the attrdefs table.
#
def getdef(attrname):
	##_stat('MMAttrdefs.getdef')
	try:
		return attrdefs[attrname]
	except KeyError:
		# Undefined attribute -- fake something reasonable
		return (('any', None), None, '', 'default', '',  'normal')
#
def getnames():
	##_stat('MMAttrdefs.getnames')
	names = attrdefs.keys()
	names.sort()
	return names

def exists(attrname):
        return attrdefs.has_key(attrname)


# Hooks to gather statistics about attribute use via getattr()
#
attrstats = None
#
def startstats():
	global attrstats
	attrstats = {}
#
def stopstats():
	global attrstats
	a = attrstats
	attrstats = None
	return a
#
def showstats(a):
	import string
	names = a.keys()
	names.sort()
	for name in names:
		print string.ljust(name, 15), string.rjust(`a[name]`, 4)


# Get an attribute of a node according to the rules.
#
def getattr(node, attrname):
	##_stat('MMAttrdefs.getattr')
	if attrstats is not None:
		if attrstats.has_key(attrname):
			attrstats[attrname] = attrstats[attrname] + 1
		else:
			attrstats[attrname] = 1
	# Check the cache
	try:
		rv = node.attrcache[attrname]
		##_stat('cache hit: ' + attrname)
		return rv
	except (AttributeError, KeyError):
		##_stat('cache miss: ' + attrname)
		pass
	#
	attrdef = getdef(attrname)
	inheritance = attrdef[5]
	defaultvalue = attrdef[1]
	if inheritance == 'raw':
		attrvalue = node.GetRawAttrDef(attrname, defaultvalue)
	elif inheritance == 'normal':
		attrvalue = node.GetAttrDef(attrname, defaultvalue)
	elif inheritance == 'inherited':
		attrvalue = node.GetInherAttrDef(attrname, defaultvalue)
	elif inheritance == 'channel':
		try:
			attrvalue = node.GetInherAttr(attrname)
		except NoSuchAttrError:
			ch = node.GetChannel()
			try:
				attrvalue = ch[attrname]
			except (TypeError, KeyError):
				attrvalue = defaultvalue
	else:
		raise CheckError, 'bad inheritance ' +`inheritance` + \
				' for attr ' + `attrname`
	# Update the cache
	try:
		node.attrcache[attrname] = attrvalue
	except AttributeError:
		node.attrcache = {attrname: attrvalue}
	#
	return attrvalue


# Clear the attribute caches for an entire tree
#
def flushcache(node):
	node.attrcache = {}
	for c in node.GetChildren():
		flushcache(c)


# Get the default value for a node's attribute, *ignoring* its own value
#
def getdefattr(node, attrname):
	##_stat('MMAttrdefs.getdefattr')
	attrdef = getdef(attrname)
	inheritance = attrdef[5]
	defaultvalue = attrdef[1]
	if inheritance == 'raw':
		return defaultvalue
	elif inheritance == 'normal':
##		try:
##			return node.GetDefAttr(attrname)
##		except NoSuchAttrError:
		return defaultvalue
	elif inheritance == 'inherited':
		try:
			return node.GetDefInherAttr(attrname)
		except NoSuchAttrError:
			return defaultvalue
	elif inheritance == 'channel':
		try:
			return node.GetDefInherAttr(attrname)
		except NoSuchAttrError:
			ch = node.GetChannel()
			try:
				return ch[attrname]
			except KeyError:
				return defaultvalue
	else:
		raise CheckError, 'bad inheritance ' +`inheritance` + \
				' for attr ' + `attrname`

def valuerepr(name, value):
	##_stat('MMAttrdefs.valuerepr')
	import MMWrite
	return MMWrite.valuerepr(value, getdef(name)[0])


def parsevalue(name, string, context):
	##_stat('MMAttrdefs.parsevalue')
	import MMParser
	typedef = ('enclosed', getdef(name)[0])
	return MMParser.parsevalue('('+string+')', typedef, context)


# Initialize the attrdefs table.
#
def initattrdefs():
	if os.name == 'mac':
		# Mac-specific: try loading atc file from a resource
		import Res
		try:
			atcres = Res.GetNamedResource('CMat', 'Attrdefs')
		except Res.Error:
			pass
		else:
			return marshal.loads(atcres.data)

	import cmif
	filename = cmif.findfile(os.path.join('lib', 'Attrdefs'))
	try:
		fp = open(filename, 'r')
	except IOError:
		fp = None
	try:
		import Attrdefs
	except ImportError:
		pass
	else:
		if fp is None:
			return Attrdefs.Attrdefs
		sf = os.stat(filename)
		if Attrdefs.mtime == sf[ST_MTIME]:
			return Attrdefs.Attrdefs
	attrdefs = readattrdefs(fp, filename)
	fp.close()
	return attrdefs


# Call the initialization
#
attrdefs = initattrdefs()
