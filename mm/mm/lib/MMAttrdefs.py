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
#'

from MMExc import *
import MMParser
import sys
import os
from stat import ST_MTIME
import marshal
from flags import *

verbose = 0

# Parse a file containing attribute definitions.
#
if __debug__:
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
				if typedef[0] in ('tuple', 'list',
						  'dict', 'namedict', 'attrdict'):
					xtypedef = 'enclosed', typedef
				defaultvalue = parser.getgenericvalue(
					usetypedef(xtypedef,
						   MMParser.MMParser.basicparsers))
				labeltext = parser.getstringvalue(None)
				displayername = parser.getnamevalue(None)
				helptext = parser.getstringvalue(None)
				inheritance = parser.getenumvalue(
					['raw', 'normal', 'inherited', 'channel', 'region'])
				xtypedef = 'enclosed', ('list', ('enum', ['advanced', 'template', 'g2_light', 'g2_pro','qt_light','qt_pro', 'g2', 'qt', 'smil10', 'smil2', 'cmif', 'snap', 'all']))
				flags = parser.getgenericvalue(
					usetypedef(xtypedef,
						MMParser.MMParser.basicparsers))
				parser.close()
				if dict.has_key(attrname):
					if verbose:
						print 'Warning: duplicate attr def', attrname

				# WARNING: HACK
				# for instance, the conversion is turn off for QuickTime docucment.
				# In order to supress a specific traitment, in future we should extend the attrdef management 
				import compatibility
				import features
				if compatibility.QT == features.compatibility and attrname == 'project_convert':
					defaultvalue = 0

				binary_flags = 0
				for fl in flags:
					if fl == 'advanced':
						binary_flags = binary_flags | FLAG_ADVANCED
					if fl == 'template':
						binary_flags = binary_flags | FLAG_TEMPLATE
					if fl == 'g2_light':
						binary_flags = binary_flags | FLAG_G2_LIGHT
					elif fl == 'g2_pro':
						binary_flags = binary_flags | FLAG_G2_PRO
					elif fl == 'qt_light':
						binary_flags = binary_flags | FLAG_QT_LIGHT
					elif fl == 'qt_pro':
						binary_flags = binary_flags | FLAG_QT_PRO
					elif fl == 'smil10':
						binary_flags = binary_flags | FLAG_SMIL_1_0
					elif fl == 'smil2':
						binary_flags = binary_flags | FLAG_BOSTON
					elif fl == 'cmif':
						binary_flags = binary_flags | FLAG_CMIF
					elif fl == 'g2':
						binary_flags = binary_flags | FLAG_G2
					elif fl == 'qt':
						binary_flags = binary_flags | FLAG_QT
					elif fl == 'all':
						binary_flags = binary_flags | FLAG_ALL

				dict[attrname] = typedef, defaultvalue, labeltext, \
					displayername, helptext, inheritance, binary_flags
		except EOFError:
			parser.reporterror(filename, 'Unexpected EOF', sys.stderr)
			raise EOFError
		except MSyntaxError, msg:
			if type(msg) is type(()):
				gotten, expected = msg
				msg = 'got "'+gotten+'", expected "'+expected+'"'
			parser.reporterror(filename,
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
			print 'Can\'t write compiled attributes to', filename_py
			print msg[1]
		if verbose:
			print 'Done.'
		return dict


# Map a typedef to a (func, arg) pair.
#
def usetypedef(typedef, mapping):
	type, rest = typedef
	func = mapping[type]
	arg = None
	if type == 'enum':
		arg = rest
	elif type == 'tuple':
		arg = []
		for td in rest:
			arg.append(usetypedef(td, mapping))
	elif type in ('list', 'dict', 'namedict', 'enclosed', 'optenclosed'):
		arg = usetypedef(rest, mapping)
	return func, arg


# Use the type definitions from the attrdefs table.
#
def useattrdefs(mapping):
	dict = {}
	for attrname in attrdefs.keys():
		dict[attrname] = usetypedef(attrdefs[attrname][0], mapping)
	return dict


# Functional interface to the attrdefs table.
#
_default = (('any', None), None, '', 'default', '',  'normal', FLAG_ALL)
def getdef(attrname):
	return attrdefs.get(attrname, _default)
#
def getnames():
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
def getattr(node, attrname, animated=0):
	if not animated and node is not None:
		if node.isCssAttr(attrname):
			return node.getCssAttr(attrname)
				
	if attrstats is not None:
		if attrstats.has_key(attrname):
			attrstats[attrname] = attrstats[attrname] + 1
		else:
			attrstats[attrname] = 1
	# Check the cache
	if not animated:
		if hasattr(node, 'attrcache'):
			if node.attrcache.has_key(attrname):
				return node.attrcache[attrname]
		else:
			node.attrcache = {}
	#
	attrdef = getdef(attrname)
	inheritance = attrdef[5]
	defaultvalue = attrdef[1]
	if inheritance == 'raw':
		attrvalue = node.GetRawAttrDef(attrname, defaultvalue, animated)
	elif inheritance == 'normal':
		attrvalue = node.GetAttrDef(attrname, defaultvalue, animated)
	elif inheritance == 'inherited':
		attrvalue = node.GetInherAttrDef(attrname, defaultvalue, animated)
	elif inheritance == 'channel':
		try:
			attrvalue = node.GetAttr(attrname)
		except NoSuchAttrError:
			ch = node.GetChannel()
			if ch is not None:
				attrvalue = ch.get(attrname, defaultvalue)
			else:
				attrvalue = defaultvalue
	elif inheritance == 'region':
		try:
			attrvalue = node.GetAttr(attrname)
		except NoSuchAttrError:
			ch = node.GetChannel()
			if ch is not None:
				region = ch.GetLayoutChannel()
				if region is not None:
					attrvalue = region.GetInherAttrDef(attrname, defaultvalue)
				else:
					attrvalue = defaultvalue
			else:
				attrvalue = defaultvalue
	else:
		raise CheckError, 'bad inheritance ' +`inheritance` + \
				' for attr ' + `attrname`
	if not animated:
		# Update the cache
		node.attrcache[attrname] = attrvalue
	#
	return attrvalue


# Clear the attribute caches for an entire tree
#
def flushcache(node):
	node.attrcache = {}
	node.fullduration = None
	for c in node.GetChildren():
		flushcache(c)


# Get the default value for a node's attribute, *ignoring* its own value
#
def getdefattr(node, attrname):
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
		ch = node.GetChannel()
		if ch is not None:
			return ch.get(attrname, defaultvalue)
		else:
			return defaultvalue
	elif inheritance == 'region':
##		ch = node.GetChannel()
##		if ch is not None:
##			region = ch.GetLayoutChannel()
##			if region is not None:
##				attrvalue = region.GetInherAttrDef(attrname, defaultvalue)
##			else:
##				attrvalue = defaultvalue
##		else:
##			attrvalue = defaultvalue
		return defaultvalue
	else:
		raise CheckError, 'bad inheritance ' +`inheritance` + \
				' for attr ' + `attrname`

def valuerepr(name, value):
	import MMWrite
	return MMWrite.valuerepr(value, getdef(name)[0])


def parsevalue(name, string, context):
	typedef = ('enclosed', getdef(name)[0])
	return MMParser.parsevalue('('+string+')', typedef, context)

def getattrtype(attrname):
	return getdef(attrname)[0][0]

# Initialize the attrdefs table.
#
def initattrdefs():
##	if os.name == 'mac':
##		# Mac-specific: try loading atc file from a resource
##		import Res
##		try:
##			atcres = Res.GetNamedResource('CMat', 'Attrdefs')
##		except Res.Error:
##			pass
##		else:
##			return marshal.loads(atcres.data)

	if __debug__:
		import cmif
		filename = os.path.join(os.path.dirname(cmif.__file__), 'Attrdefs')
##		filename = cmif.findfile(os.path.join('lib', 'Attrdefs'))
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
	import Attrdefs
	return Attrdefs.Attrdefs

# Call the initialization
#
if __name__ == '__main__':
	import cmif, os
	cmif.DEFAULTDIR=os.pardir
attrdefs = initattrdefs()

exists = attrdefs.has_key
