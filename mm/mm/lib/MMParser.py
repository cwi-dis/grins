# Parser for CWI Multimedia Files


import MMNode
import regexp

SyntaxError = 'MMParser.SyntaxError'
CheckError = 'MMParser.CheckError'
TypeError = 'MMParser.TypeError'

expr = '0[xX][0-9a-fA-F]+|[0-9]+(\.[0-9]*)?([eE][-+]?[0-9]+)?'
matchnumber = regexp.compile(expr).exec

expr = '[a-zA-Z_][a-zA-Z0-9_]*'
matchname = regexp.compile(expr).exec

letters = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_'
digits = '0123456789'

class MMParser():
	#
	def init(self, input):
		#
		# 'input' should have a parameterless method readline()
		# which returns the next line, including trailing '\n',
		# or the empty string if there is no more data.
		# An open file will do nicely.
		#
		self.input = input
		self.reset()
		self.context = MMNode.MMNodeContext().init(MMNode.MMNode)
		self.attrparsers = {}
		self.attrparsers['styledict'] = \
		self.attrparsers['channeldict'] = \
			MMParser.getnamedictvalue, \
				(MMParser.getattrdictvalue, None)
		self.attrparsers['style'] = \
			MMParser.getlistvalue, (MMParser.getnamevalue, None)
		self.attrparsers['channel'] = \
		self.attrparsers['type'] = \
			MMParser.getnamevalue, None
		self.attrparsers['scrollbars'] = \
			MMParser.gettuplevalue, \
				((MMParser.getboolvalue, None),)*2
		self.attrparsers['winsize'] = \
			MMParser.gettuplevalue, \
				((MMParser.getintvalue, None),)*2
		self.attrparsers['winpos'] = \
			MMParser.gettuplevalue, \
				((MMParser.getintvalue, None),)*2
		self.attrparsers['font'] = \
			MMParser.getstringvalue, None
		return self
	#
	def reset(self):
		self.nextline = ''
		self.pos = 0
		self.lineno = 0
		self.eofseen = 0
		self.pushback = ''
	#
	def getnode(self):
		self.open()
		type = self.gettoken()
		if type not in ('seq', 'par', 'grp', 'imm', 'ext'):
			raise SyntaxError, (type, 'node type')
		if self.peektoken() = '(':
			# XXX Temporary hack to accomodate old syntax (no uid)
			uid = self.context.newuid()
		else:
			uid = self.getuid()
		node = self.context.newnodeuid(type, uid)
		self.open()
		while self.more():
			name, value = self.getattr()
			node._setattr(name, value)
		if type in ('seq', 'par', 'grp'):
			while self.more():
				child = self.getnode()
				node._addchild(child)
		elif type = 'imm':
			while self.more():
				value = self.getvalue()
				node._addvalue(value)
		else:
			# External node
			self.close()
		return node
	#
	def getattr(self):
		self.open()
		name = self.gettoken()
		if name[:1] not in letters:
			raise SyntaxError, (name, 'name')
		if self.attrparsers.has_key(name):
			func, arg = self.attrparsers[name]
			value = func(self, arg)
		elif name[-4:] = 'dict':
			# Default syntax for dictionaries
			value = \
			    self.getnamedictvalue(MMParser.getanyvalue, None)
		elif name[-4:] = 'list':
			# Default syntax for lists
			value = self.getlistvalue(MMParser.getanyvalue, None)
		else:
			# Default syntax for other things
			# (returned as lists if more than one item,
			# else as single value)
			value = self.getlistvalue(MMParser.getanyvalue, None)
			if len(value) = 1:
				value = value[0]
		self.close()
		return name, value
	#
	# Experimental attr-specific parsers
	# These raise an exception if the type isn't right
	# These do NOT eat the next token, even if it is ')'
	#
	def getintvalue(self, dummy):
		t = self.needtoken()
		if t[0] in digits:
			if '.' in t or 'e' in t or 'E' in t:
				raise TypeError, 'int'
			return int(eval(t))
		raise TypeError, (t, 'int')
	#
	def getfloatvalue(self, dummy):
		t = self.needtoken()
		if t[0] in digits: return float(eval(t))
		raise TypeError, (t, 'float')
	#
	def getstringvalue(self, dummy):
		t = self.needtoken()
		if t[0] = '\'': return eval(t)
		raise TypeError, (t, 'string')
	#
	def getnamevalue(self, dummy):
		t = self.needtoken()
		if t[0] in letters: return t
		raise TypeError, (t, 'name')
	#
	def getboolvalue(self, dummy):
		t = self.needtoken()
		false = '0', 'n', 'no',  'f', 'off'
		true  = '1', 'y', 'yes', 't', 'on'
		if t in false: return 0
		if t in true: return 1
		raise TypeError, (t, 'bool')
	#
	def getenumvalue(self, list):
		t = self.needtoken()
		if t in list: return t
		raise TypeError, (t, 'enum' + `list`)
	#
	def getlistvalue(self, (func, arg)):
		list = []
		while self.more():
			v = func(self, arg)
			list.append(v)
		self.ungettoken(')')
		return list
	#
	def getdictvalue(self, (func, arg)):
		dict = {}
		while self.more():
			self.open()
			key = self.getstringvalue(None)
			if dict.has_key(key):
				raise TypeError, (t, 'duplicate key string')
			dict[key] = func(self, arg)
			self.close()
		self.ungettoken(')')
		return dict
	#
	def getnamedictvalue(self, (func, arg)):
		dict = {}
		while self.more():
			self.open()
			key = self.getnamevalue(None)
			if dict.has_key(key):
				raise TypeError, (t, 'duplicate key name')
			dict[key] = func(self, arg)
			self.close()
		self.ungettoken(')')
		return dict
	#
	def getattrdictvalue(self, dummy):
		dict = {}
		while self.more():
			key, val = self.getattr()
			if dict.has_key(key):
				raise TypeError, (t, 'duplicate attr name')
			dict[key] = val
		self.ungettoken(')')
		return dict
	#
	def gettuplevalue(self, funcarglist):
		tuple = ()
		for func, arg in funcarglist:
			v = func(self, arg)
			tuple = tuple + (v,)
		return tuple
	#
# BOGUS! Should reset tokenizer first...
#	def getunionvalue(self, funcarglist):
#		for func, arg in funcarglist:
#			try:
#				return func(self, arg)
#			except TypeError:
#				pass
#		raise TypeError, 'union'
	#
	def getenclosedvalue(self, (func, arg)):
		self.open()
		v = func(self, arg)
		self.close()
		return v
	#
	def getanyvalue(self, dummy):
		return self.getvalue()
	#
	def needtoken(self):
		t = self.gettoken()
		if t = '': raise EOFError
		if t in ('(', ')'): raise SyntaxError, (t, 'value')
		return t
	#
	# End experiments
	#
	def getvalue(self):
		t = self.gettoken()
		if t = '':
			raise EOFError
		if t[0] in letters:
			return t
		if t[0] in digits:
			return eval(t)
		if t[0] = '\'':
			return eval(t)
		if t[0] = '(':
			values = []
			while self.more():
				values.append(self.getvalue())
			return values
		raise SyntaxError, (t, 'value')
	#
	def getuid(self):
		t = self.gettoken()
		if t = '':
			raise EOFError
		if t[0] in letters or t[0] in digits:
			return t
		if t[0] = '\'':
			return eval(t)
		raise SyntaxError, (t, 'value')
	#
	def open(self):
		self.expect('(')
	#
	def close(self):
		self.expect(')')
	#
	def expect(self, exp):
		#print '#expect', exp
		t = self.gettoken()
		if t <> exp:
			raise SyntaxError, (t, exp)
	#
	def more(self):
		if self.peektoken() = ')':
			void = self.gettoken()
			return 0
		else:
			return 1
	#
	def peektoken(self):
		if not self.pushback:
			self.pushback = self.getnexttoken()
		return self.pushback
	#
	def gettoken(self):
		if self.pushback:
			token = self.pushback
			self.pushback = ''
		else:
			token = self.getnexttoken()
		#print '#gettoken', token
		return token
	#
	def ungettoken(self, token):
		if self.pushback:
			raise RuntimeError, 'more than one ungettoken'
		# print 'pushback:', token
		self.pushback = token
	#
	def getnexttoken(self):
		#
		# Look for the start of a token (returns if EOF hit)
		#
		while 1:
			#
			# Read next line if necessary
			#
			if self.pos >= len(self.nextline):
				if self.eofseen:
					self.nextline = ''
				else:
					self.nextline = self.input.readline()
				self.pos = 0
				if not self.nextline:
					if self.eofseen:
						raise EOFError
					self.eofseen = 1
					return ''
				self.lineno = self.lineno + 1
				#
				# Read continuation lines if any
				#
				while self.nextline[-2:] = '\\\n':
					self.nextline = self.nextline[:-2]
					cont = self.input.readline()
					if not cont:
						break
					self.nextline = self.nextline + cont
					self.lineno = self.lineno + 1
					if len(cont) < 2:
						break
			#
			# Skip whitespace and comments
			#
			i, n = self.pos, len(self.nextline)
			while i < n and self.nextline[i] in ' \t\n\f\v':
				i = i+1
			if i < n and self.nextline[i] = '#':
				i = n
			self.pos = i
			if i < n:
				break
		#
		# Process the token
		#
		line = self.nextline
		i, n = self.pos, len(line)
		c = line[i]
		if c = '\'':
			i = i+1
			while i < n:
				c = line[i]
				i = i+1
				if c = '\'':
					token = line[self.pos : i]
					self.pos = i
					return token
				if c = '\\':
					i = i+1
			raise SyntaxError, 'unterminated string'
		if c in digits:
			match = matchnumber(line, i)
			if match:
				first, last = match[0]
				token = line[first : last]
				self.pos = last
				return token
			raise SyntaxError, 'number syntax error'
		if c in letters:
			match = matchname(line, i)
			if match:
				first, last = match[0]
				token = line[first : last]
				self.pos = last
				return token
		self.pos = i+1
		return c
	#
	def reporterror(self, (filename, message, fp)):
		fp.write(filename)
		fp.write(':' + `self.lineno` + ': ')
		fp.write(message)
		fp.write('\n')
		self.printerrorline(fp)
	#
	def printerrorline(self, fp):
		line = self.nextline
		fp.write(line)
		if line[-1:] <> '\n':
			fp.write('\n')
		for i in range(len(line)):
			if i >= self.pos:
				fp.write('^')
				break
			if line[i] = '\t':
				fp.write('\t')
			elif ' ' <= line[i] < '\177':
				fp.write(' ')
		fp.write('\n')
	#


class StringInput():
	#
	def init(self, string):
		self.string = string
		self.pos = 0
		return self
	#
	def readline(self):
		string = self.string
		i = self.pos
		n = len(string)
		while i < n:
			if string[i] = '\n':
				i = i+1
				break
			i = i+1
		string = string[self.pos : i]
		self.pos = i
		return string
	#


# Test driver for tokenizer
#
def testtokenizer():
	import sys
	p = MMParser().init(sys.stdin)
	try:
		while 1: p.gettoken()
	except EOFError:
		pass
	except SyntaxError, msg:
		p.reporterror('<stdin>', 'Syntax error: ' + msg, sys.stderr)


# Test driver for parser
#
def testparser():
	import sys
	p = MMParser().init(sys.stdin)
	try:
		x = p.getnode()
	except EOFError:
		print 'unexpected EOF at line', p.lineno
		return
	except SyntaxError, msg:
		if type(msg) = type(()):
			gotten, expected = msg
			msg = 'got ' + `gotten` + ', expected ' + `expected`
		p.reporterror('<stdin>', 'Syntax error: ' + msg, sys.stderr)
		return
	import MMWrite
	MMWrite.WriteOpenFile(x, sys.stdout)
