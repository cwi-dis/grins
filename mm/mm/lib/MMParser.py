# Parser for CWI Multimedia Files


import MMNode
import regexp

SyntaxError = 'MMParser.SyntaxError'
CheckError = 'MMParser.CheckError'

expr = '0[xX][0-9a-fA-F]+|[0-9]+(\.[0-9]*)?([eE][-+]?[0-9]+)?'
matchnumber = regexp.compile(expr)

expr = '[a-zA-Z_][a-zA-Z0-9_]*'
matchname = regexp.compile(expr)

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
			raise SyntaxError, (t, 'node type')
		node = MMNode.MMNode()._init(type)
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
			self.expect(')')
		return node
	#
	def getattr(self):
		self.open()
		name = self.gettoken()
		if name in ('styledict', 'channeldict'):
			# Special syntax for style and channel dictionary:
			# each item is a named attribute list
			value = {}
			while self.more():
				self.open()
				name1 = self.gettoken()
				value1 = {}
				while self.more():
					name2, value2 = self.getattr()
					value1[name2] = value2
				value[name1] = value1
		elif name[-4:] = 'dict':
			# Special syntax for other dictionaries
			value = {}
			while self.more():
				name1, value1 = self.getattr()
				value[name1] = value1
		else:
			values = []
			while self.more():
				values.append(self.getvalue())
			if len(values) = 1 and \
				    name <> 'style' and name[-4:] <> 'list':
				value = values[0]
			else:
				value = values
		return name, value
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
	#
	def open(self):
		self.expect('(')
	#
	def expect(self, exp):
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
		# print 'next token:', token
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
			match = matchnumber.exec(line, i)
			if match:
				first, last = match[0]
				token = line[first : last]
				self.pos = last
				return token
			raise SyntaxError, 'number syntax error'
		if c in letters:
			match = matchname.exec(line, i)
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
