# MMRead -- Multimedia tree reading interface

# These routines raise an exception if the input is ill-formatted,
# but first they print a nicely formatted error message


from MMNode import NoSuchAttrError


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
	import MMParser
	p = MMParser.MMParser().init(MMParser.StringInput(string))
	return _readparser(p, name)


# Private functions to read nodes


def _readopenfile(fp, filename):
	import MMParser
	p = MMParser.MMParser().init(fp)
	return _readparser(p, filename)

def _readparser(p, filename):
	import sys
	import MMParser
	try:
		node = p.getnode()
	except EOFError:
		p.reporterror(filename, 'Unexpected EOF', sys.stderr)
		raise EOFError
	except MMParser.SyntaxError, msg:
		if type(msg) = type(()):
			gotten, expected = msg
			msg = 'got ' + `gotten` + ', expected ' + `expected`
		p.reporterror(filename, 'Syntax error: ' + msg, sys.stderr)
		raise MMParser.SyntaxError, msg
	except MMParser.TypeError, msg:
		if type(msg) = type(()):
			gotten, expected = msg
			msg = 'got ' + `gotten` + ', expected ' + `expected`
		p.reporterror(filename, 'Type error: ' + msg, sys.stderr)
		raise MMParser.TypeError, msg
	token = p.gettoken()
	if token:
		msg = 'Node ends before EOF'
		p.reporterror(filename, msg, sys.stderr)
		raise MMParser.SyntaxError, msg
	try:
		node.context.addstyles(node.GetRawAttr('styledict'))
		node.DelAttr('styledict')
	except NoSuchAttrError:
		pass
	return node
