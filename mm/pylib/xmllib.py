# A parser for XML, using the derived class as static DTD.

import regex
import string


# Regular expressions used for parsing

_S = '[ \t\r\n]+'
_opS = '[ \t\r\n]*'
_Name = '[a-zA-Z_:][-a-zA-Z0-9._:]*'
interesting = regex.compile('[&<]')
incomplete = regex.compile('&\(' + _Name + '\|#[0-9]*\|#x[0-9a-fA-F]*\)?\|'
			   '<\([a-zA-Z_:][^<>]*\|'
			      '/\([a-zA-Z_:][^<>]*\)?\|'
			      '![^<>]*\|'
			      '\?[^<>]*\)?')

ref = regex.compile('&\(' + _Name + '\|#[0-9]+\|#x[0-9a-fA-F]+\);')
entityref = regex.compile('&\(' + _Name + '\)[^-a-zA-Z0-9._:]')
charref = regex.compile('&#\([0-9]+[^0-9]\|x[0-9a-fA-F]+[^0-9a-fA-F]+\)')
space = regex.compile(_S)
newline = regex.compile('\n')

starttagopen = regex.compile('<' + _Name)
endtagopen = regex.compile('</')
starttagend = regex.compile(_opS + '\(/?\)>')
endbracket = regex.compile('>')
cdataopen = regex.compile('<!\[CDATA\[')
cdataclose = regex.compile('\]\]>')
special = regex.compile('<![^<>]*>')
procopen = regex.compile('<\?\(' + _Name + '\)' + _S)
procclose = regex.compile('\?>')
commentopen = regex.compile('<!--')
commentclose = regex.compile('-->')
doubledash = regex.compile('--')
tagfind = regex.compile(_Name)
attrfind = regex.compile(
    _S + '\(' + _Name + '\)'
    '\(' + _opS + '=' + _opS +
    '\(\'[^\']*\'\|"[^"]*"\|[-a-zA-Z0-9.:+*%?!()_#=~]+\)\)')


# XML parser base class -- find tags and call handler functions.
# Usage: p = XMLParser(); p.feed(data); ...; p.close().
# The dtd is defined by deriving a class which defines methods
# with special names to handle tags: start_foo and end_foo to handle
# <foo> and </foo>, respectively, or do_foo to handle <foo> by itself.
# (Tags are converted to lower case for this purpose.)  The data
# between tags is passed to the parser by calling self.handle_data()
# with some data as argument (the data may be split up in arbutrary
# chunks).  Entity references are passed by calling
# self.handle_entityref() with the entity reference as argument.

class XMLParser:

    # Interface -- initialize and reset this instance
    def __init__(self, verbose=0):
	self.verbose = verbose
	self.reset()

    # Interface -- reset this instance.  Loses all unprocessed data
    def reset(self):
	self.rawdata = ''
	self.stack = []
	self.lasttag = '???'
	self.nomoretags = 0
	self.literal = 0
	self.lineno = 1

    # For derived classes only -- enter literal mode (CDATA) till EOF
    def setnomoretags(self):
	self.nomoretags = self.literal = 1

    # For derived classes only -- enter literal mode (CDATA)
    def setliteral(self, *args):
	self.literal = 1

    # Interface -- feed some data to the parser.  Call this as
    # often as you want, with as little or as much text as you
    # want (may include '\n').  (This just saves the text, all the
    # processing is done by goahead().)
    def feed(self, data):
	self.rawdata = self.rawdata + data
	self.goahead(0)

    # Interface -- handle the remaining data
    def close(self):
	self.goahead(1)

    # Interface -- translate references
    def translate_references(self, data):
	newdata = ''
	i = 0
	while 1:
	    n = ref.search(data, i)
	    if n < 0:
		newdata = newdata + data[i:]
		return newdata
	    newdata = newdata + data[i:n]
	    str = ref.group(1)
	    if str[0] == '#':
		if str[1] == 'x':
		    newdata = newdata + chr(string.atoi(str[2:], 16))
		else:
		    newdata = newdata + chr(string.atoi(str[1:]))
	    else:
		try:
		    newdata = newdata + self.entitydefs[str]
		except KeyError:
		    # can't do it, so keep the entity ref in
		    newdata = newdata + '&' + str + ';'
	    i = n + ref.match(data, n)

    # Interface -- add an entity
    def add_entitydef(self, name, value):
	if self.entitydefs is XMLParser.entitydefs:
	    # copy class variable entitydefs to instance variable
	    entitydefs = {}
	    for k, v in self.entitydefs.items():
		entitydefs[k] = v
	    self.entitydefs = entitydefs
	self.entitydefs[name] = value
	
    # Internal -- handle data as far as reasonable.  May leave state
    # and data to be processed by a subsequent call.  If 'end' is
    # true, force handling all data as if followed by EOF marker.
    def goahead(self, end):
	rawdata = self.rawdata
	i = 0
	n = len(rawdata)
	while i < n:
	    if self.nomoretags:
		data = rawdata[i:n]
		self.handle_data(data)
		self.lineno = self.lineno + string.count(data, '\n')
		i = n
		break
	    j = interesting.search(rawdata, i)
	    if j < 0: j = n
	    if i < j:
		data = rawdata[i:j]
		self.handle_data(data)
		self.lineno = self.lineno + string.count(data, '\n')
	    i = j
	    if i == n: break
	    if rawdata[i] == '<':
		if starttagopen.match(rawdata, i) >= 0:
		    if self.literal:
			data = rawdata[i]
			self.handle_data(data)
			self.lineno = self.lineno + string.count(data, '\n')
			i = i+1
			continue
		    k = self.parse_starttag(i)
		    if k < 0: break
		    self.lineno = self.lineno + string.count(rawdata[i:k], '\n')
		    i = k
		    continue
		if endtagopen.match(rawdata, i) >= 0:
		    k = self.parse_endtag(i)
		    if k < 0: break
		    self.lineno = self.lineno + string.count(rawdata[i:k], '\n')
		    i =  k
		    self.literal = 0
		    continue
		if commentopen.match(rawdata, i) >= 0:
		    if self.literal:
			data = rawdata[i]
			self.handle_data(data)
			self.lineno = self.lineno + string.count(data, '\n')
			i = i+1
			continue
		    k = self.parse_comment(i)
		    if k < 0: break
		    self.lineno = self.lineno + string.count(rawdata[i:i+k], '\n')
		    i = i+k
		    continue
		if cdataopen.match(rawdata, i) >= 0:
		    k = self.parse_cdata(i)
		    if k < 0: break
		    self.lineno = self.lineno + string.count(rawdata[i:i+k], '\n')
		    i = i+k
		    continue
		if procopen.match(rawdata, i) >= 0:
		    k = self.parse_proc(i)
		    if k < 0: break
		    self.lineno = self.lineno + string.count(rawdata[i:i+k], '\n')
		    i = i+k
		    continue
		k = special.match(rawdata, i)
		if k >= 0:
		    if self.literal:
			data = rawdata[i]
			self.handle_data(data)
			self.lineno = self.lineno + string.count(data, '\n')
			i = i+1
			continue
		    self.handle_special(rawdata[i+2:k-1])
		    self.lineno = self.lineno + string.count(rawdata[i:i+k], '\n')
		    i = i+k
		    continue
	    elif rawdata[i] == '&':
		k = charref.match(rawdata, i)
		if k >= 0:
		    k = i+k
		    if rawdata[k-1] != ';': k = k-1
		    name = charref.group(1)[:-1]
		    self.handle_charref(name)
		    self.lineno = self.lineno + string.count(rawdata[i:k], '\n')
		    i = k
		    continue
		k = entityref.match(rawdata, i)
		if k >= 0:
		    k = i+k
		    if rawdata[k-1] != ';': k = k-1
		    name = entityref.group(1)
		    self.handle_entityref(name)
		    self.lineno = self.lineno + string.count(rawdata[i:k], '\n')
		    i = k
		    continue
	    else:
		raise RuntimeError, 'neither < nor & ??'
	    # We get here only if incomplete matches but
	    # nothing else
	    k = incomplete.match(rawdata, i)
	    if k < 0:
		data = rawdata[i]
		self.handle_data(data)
		self.lineno = self.lineno + string.count(data, '\n')
		i = i+1
		continue
	    j = i+k
	    if j == n:
		break # Really incomplete
	    self.syntax_error(self.lineno, 'bogus < or &')
	    data = rawdata[i:j]
	    self.handle_data(data)
	    self.lineno = self.lineno + string.count(data, '\n')
	    i = j
	# end while
	if end and i < n:
	    data = rawdata[i:n]
	    self.handle_data(data)
	    self.lineno = self.lineno + string.count(data, '\n')
	    i = n
	self.rawdata = rawdata[i:]
	# XXX if end: check for empty stack

    # Internal -- parse comment, return length or -1 if not terminated
    def parse_comment(self, i):
	rawdata = self.rawdata
	if rawdata[i:i+4] <> '<!--':
	    raise RuntimeError, 'unexpected call to handle_comment'
	j = commentclose.search(rawdata, i+4)
	if j < 0:
	    return -1
	if doubledash.search(rawdata, i+4) < j:
	    self.syntax_error(self.lineno, '`--\' in comment')
	self.handle_comment(rawdata[i+4: j])
	j = j+commentclose.match(rawdata, j)
	return j-i

    # Internal -- handle CDATA tag, return lenth or -1 if not terminated
    def parse_cdata(self, i):
	rawdata = self.rawdata
	if rawdata[i:i+9] <> '<![CDATA[':
	    raise RuntimeError, 'unexpected call to handle_cdata'
	j = cdataclose.search(rawdata, i+9)
	if j < 0:
	    return -1
	self.handle_cdata(rawdata[i+9:j])
	j = j+cdataclose.match(rawdata, j)
	return j-i

    def parse_proc(self, i):
	rawdata = self.rawdata
	j = procopen.match(rawdata, i)
	if j < 0:
	    raise RuntimeError, 'unexpected call to parse_proc'
	name = procopen.group(1)
	k = procclose.search(rawdata, i+j)
	if k < 0:
	    return -1
	self.handle_proc(name, rawdata[i+j:k])
	k = k+procclose.match(rawdata, k)
	return k-i

    # Internal -- handle starttag, return length or -1 if not terminated
    def parse_starttag(self, i):
	rawdata = self.rawdata
	# i points to start of tag
	j = endbracket.search(rawdata, i+1)
	if j < 0:
	    return -1
	# Now parse the data between i+1 and j into a tag and attrs
	attrdict = {}
	k = tagfind.match(rawdata, i+1)
	if k < 0:
	    raise RuntimeError, 'unexpected call to parse_starttag'
	k = i+1+k
	tag = string.lower(rawdata[i+1:k])
	self.lasttag = tag
	while k < j:
	    l = attrfind.match(rawdata, k)
	    if l < 0: break
	    attrname, rest, attrvalue = attrfind.group(1, 2, 3)
	    if not rest:
		self.syntax_error(self.lineno, 'no attribute value specified')
		attrvalue = attrname
	    elif attrvalue[:1] == "'" == attrvalue[-1:] or \
		 attrvalue[:1] == '"' == attrvalue[-1:]:
		attrvalue = attrvalue[1:-1]
	    else:
		self.syntax_error(self.lineno, 'attribute value not quoted')
	    attrname = string.lower(attrname)
	    if attrdict.has_key(attrname):
		self.syntax_error(self.lineno, 'attribute specified twice')
	    attrdict[attrname] = self.translate_references(attrvalue)
	    k = k + l
	self.finish_starttag(tag, attrdict)
	if starttagend.match(rawdata, k) > 0 and starttagend.group(1) == '/':
	    self.finish_endtag(tag)
	return j+1

    # Internal -- parse endtag
    def parse_endtag(self, i):
	rawdata = self.rawdata
	j = endbracket.search(rawdata, i+1)
	if j < 0:
	    return -1
	k = tagfind.match(rawdata, i+2)
	if k < 0:
	    self.syntax_error(self.lineno, 'no name specified in end tag')
	    tag = ''
	    k = 0
	else:
	    tag = string.lower(rawdata[i+2:i+2+k])
	if i+2+k != j and space.match(rawdata, i+2+k) != j-i-2-k:
	    self.syntax_error(self.lineno, 'end tag not well-formed')
	self.finish_endtag(tag)
	return j+1

    # Internal -- finish processing of start tag
    # Return -1 for unknown tag, 1 for balanced tag
    def finish_starttag(self, tag, attrs):
	self.stack.append(tag)
	try:
	    method = getattr(self, 'start_' + tag)
	except AttributeError:
	    self.unknown_starttag(tag, attrs)
	    return -1
	else:
	    self.handle_starttag(tag, method, attrs)
	    return 1

    # Internal -- finish processing of end tag
    def finish_endtag(self, tag):
	if not tag:
	    found = len(self.stack) - 1
	    if found < 0:
		self.unknown_endtag(tag)
		return
	else:
	    if tag not in self.stack:
		try:
		    method = getattr(self, 'end_' + tag)
		except AttributeError:
		    self.unknown_endtag(tag)
		return
	    found = len(self.stack)
	    for i in range(found):
		if self.stack[i] == tag: found = i
	while len(self.stack) > found:
	    tag = self.stack[-1]
	    try:
		method = getattr(self, 'end_' + tag)
	    except AttributeError:
		method = None
	    if method:
		self.handle_endtag(tag, method)
	    else:
		self.unknown_endtag(tag)
	    del self.stack[-1]

    # Overridable -- handle start tag
    def handle_starttag(self, tag, method, attrs):
	method(attrs)

    # Overridable -- handle end tag
    def handle_endtag(self, tag, method):
	method()

    # Example -- report an unbalanced </...> tag.
    def report_unbalanced(self, tag):
	if self.verbose:
	    print '*** Unbalanced </' + tag + '>'
	    print '*** Stack:', self.stack

    # Example -- handle character reference, no need to override
    def handle_charref(self, name):
	try:
	    if name[0] == 'x':
		n = string.atoi(name[1:], 16)
	    else:
		n = string.atoi(name)
	except string.atoi_error:
	    self.unknown_charref(name)
	    return
	if not 0 <= n <= 255:
	    self.unknown_charref(name)
	    return
	self.handle_data(chr(n))

    # Definition of entities -- derived classes may override
    entitydefs = \
	    {'lt': '<', 'gt': '>', 'amp': '&', 'quot': '"', 'apos': '\''}

    # Example -- handle entity reference, no need to override
    def handle_entityref(self, name):
	table = self.entitydefs
	if table.has_key(name):
	    self.handle_data(table[name])
	else:
	    self.unknown_entityref(name)
	    return

    # Example -- handle data, should be overridden
    def handle_data(self, data):
	pass

    # Example -- handle cdata, could be overridden
    def handle_cdata(self, data):
	pass

    # Example -- handle comment, could be overridden
    def handle_comment(self, data):
	pass

    # Example -- handle processing instructions, could be overridden
    def handle_proc(self, name, data):
	pass

    # Example -- handle special instructions, could be overridden
    def handle_special(self, data):
	pass

    # Example -- handle relatively harmless syntax errors, could be overridden
    def syntax_error(self, lineno, message):
	raise RuntimeError, 'Syntax error at line %d: %s' % (lineno, message)

    # To be overridden -- handlers for unknown objects
    def unknown_starttag(self, tag, attrs): pass
    def unknown_endtag(self, tag): pass
    def unknown_charref(self, ref): pass
    def unknown_entityref(self, ref): pass


class TestXMLParser(XMLParser):

    def __init__(self, verbose=0):
	self.testdata = ""
	XMLParser.__init__(self, verbose)

    def handle_data(self, data):
	self.testdata = self.testdata + data
	if len(`self.testdata`) >= 70:
	    self.flush()

    def flush(self):
	data = self.testdata
	if data:
	    self.testdata = ""
	    print 'data:', `data`

    def handle_cdata(self, data):
	self.flush()
	print 'cdata:', `data`

    def handle_proc(self, name, data):
	self.flush()
	print 'processing:',name,`data`

    def handle_special(self, data):
	self.flush()
	print 'special:',`data`

    def handle_comment(self, data):
	self.flush()
	r = `data`
	if len(r) > 68:
	    r = r[:32] + '...' + r[-32:]
	print 'comment:', r

    def syntax_error(self, lineno, message):
	print 'error at line %d:' % lineno, message

    def unknown_starttag(self, tag, attrs):
	self.flush()
	if not attrs:
	    print 'start tag: <' + tag + '>'
	else:
	    print 'start tag: <' + tag,
	    for name, value in attrs:
		print name + '=' + '"' + value + '"',
	    print '>'

    def unknown_endtag(self, tag):
	self.flush()
	print 'end tag: </' + tag + '>'

    def unknown_entityref(self, ref):
	self.flush()
	print '*** unknown entity ref: &' + ref + ';'

    def unknown_charref(self, ref):
	self.flush()
	print '*** unknown char ref: &#' + ref + ';'

    def close(self):
	XMLParser.close(self)
	self.flush()

def test(args = None):
    import sys

    if not args:
	args = sys.argv[1:]

    if args and args[0] == '-s':
	args = args[1:]
	klass = XMLParser
    else:
	klass = TestXMLParser

    if args:
	file = args[0]
    else:
	file = 'test.html'

    if file == '-':
	f = sys.stdin
    else:
	try:
	    f = open(file, 'r')
	except IOError, msg:
	    print file, ":", msg
	    sys.exit(1)

    data = f.read()
    if f is not sys.stdin:
	f.close()

    x = klass()
    for c in data:
	x.feed(c)
    x.close()


if __name__ == '__main__':
    test()
 
