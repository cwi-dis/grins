# MMRead -- Multimedia tree reading interface

# These routines raise an exception if the input is ill-formatted,
# but first they print a nicely formatted error message


# Read a CMF file, given by filename
#
def ReadFile(filename):
	return _readopenfile(open(filename, 'r'), filename)


# Read a CMF file that is already open (for reading)
#
def ReadOpenFile(arg):
	if type(arg) = type(()):
		fp, filename = arg
	else:
		fp, filename = arg, '<file>'
	return _readopenfile(fp, filename)


# Read a CMF file from a string
#
def ReadString(arg):
	import MMParser
	if type(arg) = type(()):
		string, filename = arg
	else:
		string = arg
		filename = '<string>'
	p = MMParser.MMParser().init(MMParser.StringInput(string))
	return _readparser(p, filename)


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
	token = p.gettoken()
	if token:
		msg = 'Node ends before EOF'
		p.reporterror(filename, msg, sys.stderr)
		raise MMParser.SyntaxError, msg
	return node
