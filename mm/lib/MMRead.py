__version__ = "$Id$"

# MMRead -- Multimedia tree reading interface

# These routines raise an exception if the input is ill-formatted,
# but first they print a nicely formatted error message


from MMExc import *		# Exceptions
import MMParser
import MMNode
import MMCache
import sys


# Read a CMF file, given by filename
#
def ReadFile(filename):
	return ReadFileContext(filename, _newctx())

def ReadFileContext(filename, context):
	import os
	context.setdirname(os.path.dirname(filename))
	root = MMCache.loadcache(filename, context)
	if root:
		_fixcontext(root)
		return root
	# no cache file, parse the file and create the cache (if possible)
	root = ReadOpenFileContext(open(filename, 'r'), filename, context)
	import MMWrite
	MMWrite.fixroot(root)
	MMCache.dumpcache(root, filename)
	MMWrite.unfixroot(root)
	return root


# Read a CMF file that is already open (for reading)
#
def ReadOpenFile(fp, filename):
	return ReadOpenFileContext(fp, filename, _newctx())

def ReadOpenFileContext(fp, filename, context):
	p = MMParser.MMParser(fp, context)
	return _readparser(p, filename)


# Read a CMF file from a string
#
def ReadString(string, name):
	return ReadStringContext(string, name, _newctx())

def ReadStringContext(string, name, context):
	import StringIO
	p = MMParser.MMParser(StringIO.StringIO(string), context)
	return _readparser(p, name)


# Private functions to read nodes

def _newctx():
	return MMNode.MMNodeContext(MMNode.MMNode)

def _readparser(p, filename):
	#
	# Read a single node (this is a whole tree!) from the file.
	# If an error occurs, format a nice error message, and
	# re-raise the exception as an MSyntaxError.
	#
	try:
		root = p.getnode()
	except EOFError:
		tb = sys.exc_traceback
		p.reporterror(filename, 'Unexpected EOF', sys.stderr)
		raise MSyntaxError, 'Unexpected EOF', tb
	except MSyntaxError, msg:
		if hasattr(sys, 'exc_info'):
			tb = sys.exc_info()[2]
		else:
			tb = sys.exc_traceback
		if type(msg) is type(()):
			gotten, expected = msg
			msg = 'got "'+gotten+'", expected "'+expected+'"'
		p.reporterror(filename, 'Syntax error: ' + msg, sys.stderr)
		raise MSyntaxError, msg, tb
	except MTypeError, msg:
		if hasattr(sys, 'exc_info'):
			tb = sys.exc_info()[2]
		else:
			tb = sys.exc_traceback
		if type(msg) is type(()):
			gotten, expected = msg
			msg = 'got "'+gotten+'", expected "'+expected+'"'
		p.reporterror(filename, 'Type error: ' + msg, sys.stderr)
		raise MSyntaxError, msg, tb
	#
	# Make sure that there is no garbage in the file after the node.
	#
	token = p.peektoken()
	if token <> '':
		msg = 'Node ends before EOF'
		p.reporterror(filename, msg, sys.stderr)
		raise MSyntaxError, msg
	#
	_fixcontext(root)
	return root

def _fixcontext(root):
##	#
##	# Move the style dictionary from the root attribute list
##	# to the context.
##	#
##	try:
##		root.context.addstyles(root.GetRawAttr('styledict'))
##		root.DelAttr('styledict')
##	except NoSuchAttrError:
##		pass
	#
	# Move the hyperlink list from the root attribute list
	# to the context.
	#
	try:
		root.context.addhyperlinks(root.GetRawAttr('hyperlinks'))
		root.DelAttr('hyperlinks')
	except NoSuchAttrError:
		pass
	#
	# Move the channel list from the root attribute list
	# to the context.
	#
	try:
		root.context.addchannels(root.GetRawAttr('channellist'))
		root.DelAttr('channellist')
	except NoSuchAttrError:
		pass
