# MMRead -- Multimedia tree reading interface

# These routines raise an exception if the input is ill-formatted,
# but first they print a nicely formatted error message


from MMExc import *		# Exceptions
import MMParser
import MMNode
import sys


# Read a CMF file, given by filename
#
def ReadFile(filename):
	return ReadFileContext(filename, _newctx())

def ReadFileContext(filename, context):
	return ReadOpenFileContext(open(filename, 'r'), filename, context)


# Read a CMF file that is already open (for reading)
#
def ReadOpenFile(fp, filename):
	return ReadOpenFileContext(fp, filename, _newctx())

def ReadOpenFileContext(fp, filename, context):
	p = MMParser.MMParser().init(fp, context)
	return _readparser(p, filename)


# Read a CMF file from a string
#
def ReadString(string, name):
	return ReadString(string, name, _newctx())

def ReadStringContext(string, name, context):
	p = MMParser.MMParser().init(MMParser.StringInput(string), context)
	return _readparser(p, name)


# Private functions to read nodes

def _newctx():
	return MMNode.MMNodeContext().init(MMNode.MMNode)

def _readparser(p, filename):
	#
	# Read a single node (this is a whole tree!) from the file.
	# If an error occurs, format a nice error message, and
	# re-raise the exception.
	#
	try:
		root = p.getnode()
	except EOFError:
		p.reporterror(filename, 'Unexpected EOF', sys.stderr)
		raise EOFError
	except SyntaxError, msg:
		if type(msg) = type(()):
			gotten, expected = msg
			msg = 'got "'+gotten+'", expected "'+expected+'"'
		p.reporterror(filename, 'Syntax error: ' + msg, sys.stderr)
		raise SyntaxError, msg
	except TypeError, msg:
		if type(msg) = type(()):
			gotten, expected = msg
			msg = 'got "'+gotten+'", expected "'+expected+'"'
		p.reporterror(filename, 'Type error: ' + msg, sys.stderr)
		raise TypeError, msg
	#
	# Make sure that there is no garbage in the file after the node.
	#
	token = p.peektoken()
	if token <> '':
		msg = 'Node ends before EOF'
		p.reporterror(filename, msg, sys.stderr)
		raise SyntaxError, msg
	#
	# Move the style dictionary from the root attribute list
	# to the context.
	#
	try:
		root.context.addstyles(root.GetRawAttr('styledict'))
		root.DelAttr('styledict')
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
	#
	# Make sure that all channel names used in the document are
	# defined in the channel list.
	#
	usedchannelnames = root.GetSummary('channel')
	for cname in usedchannelnames:
		msg = ''
		if cname not in root.context.channelnames:
			msg = 'undefined channel name used: ' + `cname` + '\n'
			sys.stderr.write(msg)
		if msg:
			raise TypeError, msg
	#
	return root
