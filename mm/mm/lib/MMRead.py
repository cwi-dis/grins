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
	return _readopenfile(open(filename, 'r'), filename)


# Read a CMF file that is already open (for reading)
#
def ReadOpenFile(fp, filename):
	return _readopenfile(fp, filename)


# Read a CMF file from a string
#
def ReadString(string, name):
	p = MMParser.MMParser().init(MMParser.StringInput(string), _newctx())
	return _readparser(p, name)


# Private functions to read nodes


def _readopenfile(fp, filename):
	p = MMParser.MMParser().init(fp, _newctx())
	return _readparser(p, filename)

def _newctx():
	return MMNode.MMNodeContext().init(MMNode.MMNode)

def _readparser(p, filename):
	try:
		node = p.getnode()
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
	token = p.peektoken()
	if token <> '':
		msg = 'Node ends before EOF'
		p.reporterror(filename, msg, sys.stderr)
		raise SyntaxError, msg
	#
	try:
		node.context.addstyles(node.GetRawAttr('styledict'))
		node.DelAttr('styledict')
	except NoSuchAttrError:
		pass
	#
	return node
