import re, string

class Error(Exception):
    """Error class; raised when a syntax error is encountered.
       Instance variables are:
       lineno: line at which error was found;
       offset: offset into data where error was found;
       text: data in which error was found.
       If these values are unknown, they are set to None."""
    lineno = offset = text = None
    def __init__(self, *args):
        self.args = args
        if len(args) > 1:
            self.lineno = args[1]
            if len(args) > 2:
                self.text = args[2]
                if len(args) > 3:
                    self.offset = args[3]

    def __str__(self):
        msg = 'Syntax error'
        if self.lineno is not None:
            msg = '%s at line %d' % (msg, self.lineno)
        return '%s: %s' % (msg, self.args[0])

_S = '[ \t\r\n]+'			# white space
_opS = '[ \t\r\n]*'			# optional white space
_Name = '[a-zA-Z_:][-a-zA-Z0-9._:]*'    # valid XML name
_QStr = "(?:'[^']*'|\"[^\"]*\")"        # quoted XML string
_Char = u'[]\\\\\x09\x0A\x0D -[^-\uD7FF\uE000-\uFFFD\u10000-\u10FFFF]' # legal characters

comment = re.compile('<!--(?P<comment>(?:[^-]|-[^-])*)-->')
space = re.compile(_S)
interesting = re.compile('[&<]')
amp = re.compile('&')
name = re.compile('^'+_Name+'$')
names = re.compile('^'+_Name+'(?:'+_S+_Name+')*$')

ref = re.compile('&(?:(?P<name>'+_Name+')|#(?P<char>(?:[0-9]+|x[0-9a-fA-F]+)));')
entref = re.compile('(?:&#(?P<char>(?:[0-9]+|x[0-9a-fA-F]+))|%(?P<pname>'+_Name+'));')
_attrre = _S+'(?P<attrname>'+_Name+')'+_opS+'='+_opS+'(?P<attrvalue>'+_QStr+')'
attrfind = re.compile(_attrre)
starttag = re.compile('<(?P<tagname>'+_Name+')(?P<attrs>(?:'+_attrre+')*)'+_opS+'(?P<slash>/?)>')
endtag = re.compile('</(?P<tagname>'+_Name+')'+_opS+'>')

illegal = re.compile(r'(?:\]\]>|'+u'[^]\\\\\x09\x0A\x0D -[^-\uD7FF\uE000-\uFFFD\u10000-\u10FFFF])')
illegal1 = re.compile(u'[^]\\\\\x09\x0A\x0D -[^-\uD7FF\uE000-\uFFFD\u10000-\u10FFFF]')

cdata = re.compile('<!\\[CDATA\\[(?P<cdata>(?:[^]]|\\](?!\\]>)|\\]\\](?!>))*)\\]\\]>')

_SystemLiteral = '(?P<syslit>'+_QStr+')'
_PublicLiteral = '(?P<publit>"[-\'()+,./:=?;!*#@$_%% \n\ra-zA-Z0-9]*"|' \
                            "'[-()+,./:=?;!*#@$_%% \n\ra-zA-Z0-9]*')"
_ExternalId = '(?:SYSTEM|PUBLIC'+_S+_PublicLiteral+')'+_S+_SystemLiteral
externalid = re.compile(_ExternalId)
doctype = re.compile('<!DOCTYPE'+_S+'(?P<docname>'+_Name+')(?:'+_S+_ExternalId+')?'+_opS+'(?:\\[(?P<data>(?:'+_S+'|%'+_Name+';|'+comment.pattern+'|<(?:![^-]|[^!])(?:[^\'">]|\'[^\']*\'|"[^"]*")*>)*)\\]'+_opS+')?>')

xmldecl = re.compile('<\?xml'+_S+
                     'version'+_opS+'='+_opS+'(?P<version>'+_QStr+')'+
                     '(?:'+_S+'encoding'+_opS+'='+_opS+
                        "(?P<encoding>'[A-Za-z][-A-Za-z0-9._]*'|"
                        '"[A-Za-z][-A-Za-z0-9._]*"))?'
                     '(?:'+_S+'standalone'+_opS+'='+_opS+
                        '(?P<standalone>\'(?:yes|no)\'|"(?:yes|no)"))?'+
                     _opS+'\?>')
pidecl = re.compile('<\\?(?![xX][mM][lL][ \t\r\n?])(?P<name>'+_Name+')(?:'+_S+'(?P<data>(?:[^?]|\\?(?!>))*))?\\?>')

# XML NAMESPACES
_NCName = '[a-zA-Z_][-a-zA-Z0-9._]*'    # XML Name, minus the ":"
ncname = re.compile(_NCName + '$')
qname = re.compile('(?:(?P<prefix>' + _NCName + '):)?' # optional prefix
                   '(?P<local>' + _NCName + ')$')
xmlns = re.compile('xmlns(?::(?P<ncname>' + _NCName + '))?$')

# DOCTYPE
_Nmtoken = '[-a-zA-Z0-9._:]+'
nmtoken = re.compile('^'+_Nmtoken+'$')
nmtokens = re.compile('^'+_Nmtoken+'(?:'+_S+_Nmtoken+')*$')
element = re.compile('<!ELEMENT'+_S+'(?P<name>'+_Name+')'+_S+r'(?P<content>EMPTY|ANY|\()')
dfaelem0 = re.compile(_opS+r'(?P<token>\(|'+_Name+')')
dfaelem1 = re.compile(_opS+r'(?P<token>[)|,])')
dfaelem2 = re.compile(r'(?P<token>[+*?])')
mixedre = re.compile(r'\('+_opS+'#PCDATA'+'(('+_opS+r'\|'+_opS+_Name+')*'+_opS+r'\)\*|'+_opS+r'\))')
paren = re.compile('[()]')
attdef = re.compile(_S+'(?P<atname>'+_Name+')'+_S+'(?P<attype>CDATA|ID(?:REFS?)?|ENTIT(?:Y|IES)|NMTOKENS?|NOTATION'+_S+r'\('+_opS+_Name+'(?:'+_opS+r'\|'+_opS+_Name+')*'+_opS+r'\)|\('+_opS+_Nmtoken+'(?:'+_opS+r'\|'+_opS+_Nmtoken+')*'+_opS+r'\))'+_S+'(?P<atvalue>#REQUIRED|#IMPLIED|(?:#FIXED'+_S+')?(?P<atstring>'+_QStr+'))')
attlist = re.compile('<!ATTLIST'+_S+'(?P<elname>'+_Name+')(?P<atdef>(?:'+attdef.pattern+')*)'+_opS+'>')
_EntityVal = '"(?:[^"&%]|'+ref.pattern+'|%'+_Name+';)*"|' \
             "'(?:[^'&%]|"+ref.pattern+"|%'+_Name+';)*'"
entity = re.compile('<!ENTITY'+_S+'(?:%'+_S+'(?P<pname>'+_Name+')'+_S+'(?P<pvalue>'+_EntityVal+'|'+_ExternalId+')|(?P<ename>'+_Name+')'+_S+'(?P<value>'+_EntityVal+'|'+_ExternalId+'(?:'+_S+'NDATA'+_S+_Name+')?))'+_opS+'>')
notation = re.compile('<!NOTATION'+_S+_Name+_S+'(?:SYSTEM'+_S+_SystemLiteral+'|PUBLIC'+_S+_PublicLiteral+_SystemLiteral+'?)'+_opS+'>')
peref = re.compile('%(?P<name>'+_Name+');')
ignore = re.compile(r'<!\[|\]\]>')
bracket = re.compile('[<>]')
conditional = re.compile(r'<!\['+_opS+'(?:(?P<inc>INCLUDE)|(?P<ign>IGNORE))'+_opS+r'\[')

class XMLParser:
    """XML document parser."""
    def __init__(self, xmlns = 1):
        self.__xmlns = xmlns            # whether or not to parse namespaces
	self.reset()

    def reset(self):
        """Reset parser to pristine state."""
	self.docname = None
	self.rawdata = []
        self.entitydefs = {             # & entities defined in DTD
            'lt': '&#60;',		# <
            'gt': '&#62;',		# >
            'amp': '&#38;',		# &
            'apos': '&#39;',		# '
            'quot': '&#34;',		# "
            }
        self.pentitydefs = {}           # % entities defined in DTD
        self.elems = {}                 # elements and their content/attrs
        self.baseurl = '.'              # base URL for external DTD
        self.ids = {}                   # IDs encountered in document

    def feed(self, data):
        """Feed data to parser."""
	self.rawdata.append(data)

    def close(self):
        """End of data, finish up parsing."""
	data = string.join(self.rawdata, '')
	self.rawdata = []
	self.parse(data)

    def __parse_textdecl(self, data):
        # Figure out the encoding of a file by looking at the first
        # few bytes and the <?xml?> tag that may come at the very
        # beginning of the file.
        # This will convert the data to unicode from whatever format
        # it was originally.
        i = 0
	if data[:2] == '\254\255':
	    enc = 'utf-16-be'
	    i = 2
	elif data[:2] == '\255\254':
	    enc = 'utf-16-le'
	    i = 2
        elif data[:4] == '\x00\x3C\x00\x3F':
            enc = 'utf-16-be'
        elif data[:4] == '\x3C\x00\x3F\x00':
            enc = 'utf-16-le'
        else:
            enc = None             # unknowns as yet
        if enc:
            try:
                data = unicode(data[i:], enc)
            except UnicodeError:
                self.__error("data cannot be converted to Unicode", data, i, fatal = 1)
            i = 0
        self.__encoding = 'utf-8'
	# optional XMLDecl
	res = xmldecl.match(data, i)
	if res is not None:
	    version, encoding, standalone = res.group('version',
						      'encoding',
						      'standalone')
	    if version[1:-1] != '1.0':
		self.__error('only XML version 1.0 supported', data, res.start('version'), fatal = 1)
            if encoding:
                encoding = encoding[1:-1]
                if enc and enc != encoding.lower() and \
                   enc[:6] != encoding.lower():
                    self.__error("declared encoding doesn't match actual encoding", data, res.start('encoding'), fatal = 1)
                self.__encoding = encoding.lower()
            elif enc:
                self.__encoding = enc
            else:
                self.__encoding = 'utf-8'
            if standalone:
                standalone = standalone[1:-1]
            self.handle_xml(encoding, standalone)
	    i = res.end(0)
        try:
            data = unicode(data[i:], self.__encoding)
        except UnicodeError:
            self.__error("data cannot be converted to Unicode", data, i, fatal = 1)
        return data
        
    def parse(self, data):
        """Parse the data as an XML document."""
        data = self.__parse_textdecl(data)
	# (Comment | PI | S)*
	i = self.__parse_misc(data, 0)
	# doctypedecl?
	res = doctype.match(data, i)
	if res is not None:
	    docname, publit, syslit, docdata = res.group('docname', 'publit',
							'syslit', 'data')
	    self.docname = docname
            if publit: publit = publit[1:-1]
            if syslit: syslit = syslit[1:-1]
	    self.handle_doctype(docname, publit, syslit, docdata)
	    i = res.end(0)
	# (Comment | PI | S)*
	i = self.__parse_misc(data, i)
	# the document itself
	res = starttag.match(data, i)
	if res is None:
	    self.__error('no elements in document', data, i, fatal = 1)
	i = res.end(0)
	tagname, slash = res.group('tagname', 'slash')
	if self.docname and tagname != self.docname:
	    self.__error('starttag does not match DOCTYPE', data, res.start('tagname'), fatal = 0)
	val = self.__parse_attrs(tagname, data, res.start('tagname'), res.span('attrs'), None)
        if val is None:
            return
        nstag, attrs, namespaces = val
	self.finish_starttag(nstag, attrs)
	if not slash:
	    i = self.__parse_content(data, i, tagname, namespaces)
	    if i is None:
		return
	    if type(i) is type(res):
		res = i
	    else:
		res = endtag.match(data, i)
	    if res is None:
		self.__error('end tag missing', data, i, fatal = 0)
            elif res.group('tagname') != tagname:
		self.__error("end tag doesn't match start tag", data, res.start('tagname'), fatal = 0)
	    i = res.end(0)
        self.finish_endtag(nstag)
	i = self.__parse_misc(data, i)
	if i != len(data):
	    self.__error('garbage at end of document', data, i, fatal = 0)

    def __parse_misc(self, data, i):
        # match any number of whitespace, processing instructions and comments
	matched = 1
	while matched:
	    matched = 0
	    res = comment.match(data, i)
	    if res is not None:
		matched = 1
                c0, c1 = res.span('comment')
                ires = illegal1.search(data, c0, c1)
                if ires is not None:
                    self.__error('illegal characters in comment', data, ires.start(0), fatal = 0)
		self.handle_comment(data[c0:c1])
		i = res.end(0)
	    res = pidecl.match(data, i)
	    if res is not None:
		matched = 1
                c0, c1 = res.span('data')
                ires = illegal1.search(data, c0, c1)
                if ires is not None:
                    self.__error('illegal characters in Processing Instruction', data, ires.start(0), fatal = 0)
		self.handle_proc(res.group('name'), res.group('data') or '')
		i = res.end(0)
	    res = space.match(data, i)
	    if res is not None:
		matched = 1
		i = res.end(0)
	return i

    def __update_state(self, dfa, states, tagname):
        # update the list of states in the dfa.  If tagname is None,
        # we're looking for the final state, so return a list of all
        # states reqchable using epsilon transitions
        nstates = []
        seenstates = {}
        while states:
            s = states[0]
            seenstates[s] = 1
            del states[0]
            if tagname is not None and dfa[s].has_key(tagname):
                nstates = dfa[s][tagname][:]
            else:
                for s in dfa[s].get('', []):
                    if not seenstates.has_key(s):
                        states.append(s)
        if tagname is None:
            nstates = seenstates.keys()
        states[:] = nstates # change in-line

    def __parse_content(self, data, i, ptagname, namespaces, states = None):
        # parse the content of an element (i.e. the string between
        # start tag and end tag)
	datalen = len(data)
        if self.elems.has_key(ptagname):
            content, attributes, start, end = self.elems[ptagname][:4] # content model
            if states == None:
                states = [start]
        else:
            content = None              # unknown content model
	while i < datalen:
	    matched = 0
	    res = interesting.search(data, i)
	    if res is None:
		j = datalen
	    else:
		j = res.start(0)
	    if j > i:
                res = illegal.search(data, i, j)
                if res is not None:
                    self.__error("illegal data content in element `%s'" % ptagname, data, i, fatal = 0)
                res = space.match(data, i, j)
                isspace = res is not None and res.span(0) == (i,j)
                if content is not None and content != '#PCDATA' and type(content) is not type([]):
                    if isspace:
                        # don't pass white space to empty element
                        pass
                    else:
                        self.__error("no character data allowed in element `%s'" % ptagname, data, i, fatal = 0)
                elif content is None:
                    # always pass all data if no DTD
                    isspace = 0
		matched = 1
                if not isspace:
                    self.handle_data(data[i:j])
		i = j
	    res = starttag.match(data, i)
	    if res is not None:
		tagname, slash = res.group('tagname', 'slash')
                if content == 'EMPTY' or content == '#PCDATA':
                    self.__error("empty element `%s' has content" % ptagname, data, res.start(0), fatal = 0)
                elif content == 'ANY':
                    # always OK
                    pass
                elif type(content) is type([]) and content and type(content[0]) is not type({}):
                    # mixed
                    if tagname not in content:
                        self.__error("illegal content in element `%s'" % ptagname, data, res.start(0), fatal = 0)
                elif content is not None:
                    self.__update_state(content, states, tagname)
                    if not states:
                        self.__error("illegal content for element `%s'" % ptagname, data, i)
		val = self.__parse_attrs(tagname, data, res.start('tagname'), res.span('attrs'), namespaces)
		if val is None:
		    return
		i = res.end(0)
                nstag, attrs, subnamespaces = val
		self.finish_starttag(nstag, attrs)
		if not slash:
		    i = self.__parse_content(data, i, tagname, subnamespaces)
		    if i is None:
			return
		    if type(i) is type(res):
			res = i
		    else:
			res = endtag.match(data, i)
		    if res is None:
			self.__error('end tag missing', data, i, fatal = 0)
		    elif res.group('tagname') != tagname:
			self.__error("end tag doesn't match start tag", data, res.start('tagname'), fatal = 0)
		    i = res.end(0)
                self.finish_endtag(nstag)
                continue
	    res = endtag.match(data, i)
	    if res is not None:
                if type(content) is type([]) and content and type(content[0]) is type({}):
                    self.__update_state(content, states, None)
                    if end not in states:
                        self.__error("content of element `%s' doesn't match content model" % ptagname, data, i, fatal = 0)
		return res
	    res = comment.match(data, i)
	    if res is not None:
                c0, c1 = res.span('comment')
                ires = illegal1.search(data, c0, c1)
                if ires is not None:
                    self.__error('illegal characters in comment', data, ires.start(0), fatal = 0)
		self.handle_comment(data[c0:c1])
		i = res.end(0)
                continue
	    res = ref.match(data, i)
	    if res is not None:
		name = res.group('name')
		if name:
		    if self.entitydefs.has_key(name):
			val = self.entitydefs[name]
                        del self.entitydefs[name] # to break recursion
			n = self.__parse_content(val, 0, ptagname, namespaces, states)
                        self.entitydefs[name] = val
			if n is None:
			    return
			if type(n) is type(res) or n != len(val):
                            if type(n) is type(res):
                                n = res.start(0)
			    self.__error('misformed entity value', data, n)
		    else:
                        if self.docname:
                            self.__error("unknown entity reference `&%s;' in element `%s'" % (name, ptagname), data, i)
                        self.data = data
                        self.offset = res.start('name')
                        self.lineno = string.count(data, '\n', 0, self.offset)
                        self.unknown_entityref(name)
		else:
		    str = self.__parse_charref(res.group('char'), data, res.start(0))
		    if str is None:
			return
		    self.handle_data(str)
		i = res.end(0)
                continue
	    res = pidecl.match(data, i)
	    if res is not None:
		matched = 1
		self.handle_proc(res.group('name'), res.group('data') or '')
		i = res.end(0)
	    res = cdata.match(data, i)
	    if res is not None:
		matched = 1
		self.handle_cdata(res.group('cdata'))
		i = res.end(0)
	    if not matched:
		self.__error("no valid content in element `%s'" % ptagname, data, i)
		return
	return i

    def __check_attr(self, tagname, attrname, value, attributes, data, attrstart):
        # check that the attribute attrname on element tagname is of
        # the correct type with a legal value
        # return the normalized value (i.e. white space collapsed if
        # appropriate)
        # XXX this method needs work to be complete
        attype, atvalue, atstring = attributes[attrname]
        if atvalue[:6] == '#FIXED':
            if value != atstring:
                self.__error("attribute `%s' in element `%s' does not have correct value" % (attrname, tagname), data, attrstart, fatal = 0)
        if attype == 'CDATA':
            return value                # always OK and don't change value
        value = string.join(string.split(value)) # normalize value first
        if type(attype) is type([]):    # enumeration
            if value not in attype:
                self.__error("attribute `%s' in element `%s' not valid" % (attrname, tagname), data, attrstart, fatal = 0)
            return value
        if attype == 'ID':
            if name.match(value) is None:
                self.__error("attribute `%s' in element `%s' is not an ID" % (attrname, tagname), data, attrstart, fatal = 0)
            if self.ids.has_key(value):
                self.__error("attrbute `%s' in element `%s' is not unique" %  (attrname, tagname), data, attrstart, fatal = 0)
            self.ids[value] = 1
            return value
        if attype == 'IDREF':
            if name.match(value) is None:
                self.__error("attrbute `%s' in element `%s' is not an IDREF" % (attrname, tagname), data, attrstart, fatal = 0)
            # XXX should check ID exists
            return value
        if attype == 'IDREFS':
            if names.match(value) is None:
                self.__error("attrbute `%s' in element `%s' is not an IDREFS" % (attrname, tagname), data, attrstart, fatal = 0)
            # XXX should check IDs exist
            return value
        if attype == 'NMTOKEN':
            if nmtoken.match(value) is None:
                self.__error("attrbute `%s' in element `%s' is not a NMTOKEN" % (attrname, tagname), data, attrstart, fatal = 0)
            return value
        if attype == 'NMTOKENS':
            if nmtokens.match(value) is None:
                self.__error("attrbute `%s' in element `%s' is not a NMTOKENS" % (attrname, tagname), data, attrstart, fatal = 0)
            return value
        if attype == 'ENTITY':
            if name.match(value) is None:
                self.__error("attrbute `%s' in element `%s' is not an ENTITY" % (attrname, tagname), data, attrstart, fatal = 0)
            # XXX should check ENTITY exists
            return value
        if attype == 'ENTITIES':
            if names.match(value) is None:
                self.__error("attrbute `%s' in element `%s' is not an ENTITIES" % (attrname, tagname), data, attrstart, fatal = 0)
            # XXX should check ENTITIES exist
            return value
        # XXX other types?
        return value

    def __parse_attrs(self, tagname, data, tagstart, span, namespaces):
        # parse the string between the tag name and closing bracket
        # for attribute=value pairs
	i, dataend = span
	attrlist = []
        namespace = None
        reqattrs = {}                   # attributes that are #REQUIRED
        if self.elems.has_key(tagname):
            attributes = self.elems[tagname][1]
            for key, (attype, atvalue, atstring) in attributes.items():
                if atvalue == '#REQUIRED':
                    reqattrs[key] = 1
            attrseen = {}               # attributes that we've seen
        else:
            attributes = None
	while i < dataend:
	    res = attrfind.match(data, i, dataend)
	    if res is None:
                # couldn't match any attributes, but there is more
                # string to parse: complain and ignore rest of string
		self.__error('bad attributes', data, i, fatal = 0)
		return
            start, end = res.span('attrvalue')
            value = self.__parse_attrval(data, (start+1, end-1))
	    if value is None:
                # bad attribute value: ignore, but continue parsing
                i = res.end(0)
		continue
	    name = res.group('attrname')
            if reqattrs.has_key(name):
                del reqattrs[name]      # seen this #REQUIRED attribute
            attrstart = res.start('attrname')
            if attributes is not None:
                if attributes.has_key(name):
                    attrseen[name] = 1
                    value = self.__check_attr(tagname, name, value, attributes, data, attrstart)
                else:
                    self.__error("unknown attribute `%s' on element `%s'" % (name, tagname), data, attrstart, fatal = 0)
            i = res.end(0)
            if self.__xmlns:
                res = xmlns.match(name)
                if res is not None:
                    # namespace declaration
                    ncname = res.group('ncname')
                    if namespace is None:
                        namespace = {}
                    namespace[ncname or ''] = value or None
                    continue
            attrlist.append((name, value, attrstart))
        if reqattrs:
            # there are #REQUIRED attributes that we haven't seen
            reqattrs = reqattrs.keys()
            reqattrs.sort()
            if len(reqattrs) > 1:
                s = 's'
            else:
                s = ''
            reqattrs = string.join(reqattrs, "', `")
            self.__error("required attribute%s `%s' of element `%s' missing" % (s, reqattrs, tagname), data, dataend, fatal =  0)
        if attributes is not None:
            # fill in missing attributes that have a default value
            for key, (attype, atvalue, atstring) in attributes.items():
                if atstring is not None and not attrseen.has_key(key):
                    attrlist.append((key, atstring, dataend))
        if namespace is not None:
            namespaces = (namespace, namespaces)
        if namespaces is not None:
            res = qname.match(tagname)
            if res is not None:
                prefix, nstag = res.group('prefix', 'local')
                if prefix is None: prefix = ''
                ns = None
                n = namespaces
                while n is not None:
                    d, n = n
                    if d.has_key(prefix):
                        ns = d[prefix]
                        break
                else:
                    if prefix != '':
                        ns = self.__namespaces.get(prefix)
                if ns is not None:
                    tagname = ns + ' ' + nstag
                elif prefix != '':
                    self.__error("unknown namespace prefix `%s'" % prefix, data, tagstart, fatal = 0)
            else:
                self.__error("badly formed tag name `%s'" % tagname, data, tagstart, fatal = 0)
        attrdict = {}                   # collect attributes/values
        for attr, value, attrstart in attrlist:
            if namespaces is not None:
                res = qname.match(attr)
                if res is not None:
                    prefix, nsattr = res.group('prefix', 'local')
                    if prefix:
                        ans = None
                        n = namespaces
                        while n is not None:
                            d, n = n
                            if d.has_key(prefix):
                                ans = d[prefix]
                                break
                        else:
                            if prefix != '':
                                ans = self.__namespaces.get(prefix)
                        if ans is not None:
                            attr = ans + ' ' + nsattr
                        elif prefix != '':
                            self.__error("unknown namespace prefix `%s'" % prefix, data, attrstart, fatal = 0)
                else:
                    self.__error("badly formed attribute name `%s'" % attr, data, attrstart, fatal = 0)
            if attrdict.has_key(attr):
                self.__error("duplicate attribute name `%s'" % attr, data, attrstart, fatal = 0)
            attrdict[attr] = value
	return tagname, attrdict, namespaces

    def __parse_attrval(self, data, span = None):
        # parse an attribute value, replacing entity and character
        # references with their values
        if span is None:
            i = 0
            dataend = len(data)
        else:
            i, dataend = span
	newval = []
	while i < dataend:
	    res = interesting.search(data, i, dataend)
	    if res is None:
		newval.append(data[i:dataend])
		break
            j = res.start(0)
            if data[j] == '<':
                self.__error("no `<' allowed in attribute value", data, j, fatal = 0)
            if j > i:
                newval.append(data[i:j])
	    res = ref.match(data, j, dataend)
	    if res is None:
		self.__error('illegal attribute value', data, j, fatal = 0)
                newval.append(data[j])  # the &
                i = j + 1               # continue searching after the &
		continue
	    i = res.end(0)
	    name = res.group('name')
	    if name:
                # entity referenvce (e.g. "&lt;")
		if self.entitydefs.has_key(name):
		    val = self.entitydefs[name]
                    del self.entitydefs[name]
		    nval = self.__parse_attrval(val)
                    self.entitydefs[name] = val
		    if nval is None:
			return
		    newval.append(nval)
		else:
		    self.__error("reference to unknown entity `%s'" % name, data, res.start(0), fatal = 0)
                    newval.append('&%s;' % name)
	    else:
		val = self.__parse_charref(res.group('char'), data, res.start(0))
		if val is None:
		    newval.append('&#%s;' % res.group('char'))
                    continue
		newval.append(val)
	return string.join(newval, '')

    def __parse_charref(self, name, data, i):
        # parse a character reference (e.g. "%#38;")
        # the "name" arg is just part between # and ;
	if name[0] == 'x':
            # e.g. &#x26;
	    n = string.atoi(name[1:], 16)
	else:
            # e.g. &#38;
	    n = string.atoi(name)
        if n:
            # convert number to string of bytes
            c = ''
            while n:
                c = chr(n & 0xFF) + c
                n = n >> 8
        else:
            # &#0; or &#x0;
            c = '\0'
        try:
            # convert from file's encoding to unicode
            c = unicode(c, self.__encoding)
        except UnicodeError:
            self.__error('bad character reference', data, i, fatal = 0)
            return
        if illegal1.search(c):
            self.__error('bad character reference', data, i, fatal = 0)
        return c

    def parse_dtd(self, data, internal = 1):
        """Parse the DTD.
           Argument is a string containing the full DTD.
           Optional argument internal is true (default) if the DTD is
           internal."""
        i = 0
        matched = 1
        ilevel = 0                      # nesting level of ignored sections
        while i < len(data) and matched:
            matched = i                 # remember where we were
            i = self.__parse_misc(data, i)
            matched = i > matched       # matched anything?
            res = peref.match(data, i)
            if res is not None:
                matched = 1
                name = res.group('name')
                if self.pentitydefs.has_key(name):
                    val = self.pentitydefs[name]
                    encoding = None
                    if type(val) is type(()):
                        publit, syslit = val
                        if syslit:
                            import urllib
                            syslit = urllib.basejoin(self.baseurl, syslit)
                            baseurl = self.baseurl
                            self.baseurl = syslit
                            val = self.read_external(syslit)
                            encoding = self.__encoding
                            val = self.__parse_textdecl(val)
                        else:
                            val = ''
                    self.parse_dtd(val, internal)
                    if encoding is not None:
                        self.__encoding = encoding
                        self.baseurl = baseurl
                else:
                    self.__error("unknown entity `%%%s;'" % name, data, i, fatal = 0)
                i = res.end(0)
            res = element.match(data, i)
            if res is not None:
                matched = 1
                name, content = res.group('name', 'content')
                i = res.end(0)
                if self.elems.has_key(name):
                    # XXX is this an error?
                    self.__error('non-unique element name declaration', data, i, fatal = 0)
                else:
                    if content[0] == '(':
                        i = res.start('content')
                        j, content, start, end = self.__dfa(data, i)
                        contentstr = data[i:j]
                        i = j
                    else:
                        contentstr = content
                        start = end = 0
                    self.elems[name] = (content, {}, start, end, contentstr)
                res = space.match(data, i)
                if res is not None:
                    i = res.end(0)
                if data[i:i+1] != '>':
                    self.__error('bad DOCTYPE', data, i)
                    return
                i = i+1
            res = attlist.match(data, i)
            if res is not None:
                matched = 1
                elname, atdef = res.group('elname', 'atdef')
                if not self.elems.has_key(elname):
                    self.__error('attribute declaration for non-existing element', data, i)
                else:
                    ares = attdef.match(atdef)
                    while ares is not None:
                        atname, attype, atvalue, atstring = ares.group('atname', 'attype', 'atvalue', 'atstring')
                        if atstring:
                            atstring = atstring[1:-1] # remove quotes
                            atstring = self.__parse_attrval(atstring)
                        if attype[0] == '(':
                            attype = map(string.strip, string.split(attype[1:-1], '|'))
                            if atstring is not None and atstring not in attype:
                                self.__error("default value for attribute `%s' on element `%s' not listed as possible value" % (atname, elname), data, i)
                        self.elems[elname][1][atname] = attype, atvalue, atstring
                        ares = attdef.match(atdef, ares.end(0))
                i = res.end(0)
            res = entity.match(data, i)
            if res is not None:
                matched = 1
                pname, name = res.group('pname', 'ename')
                if pname:
                    pvalue = res.group('pvalue')
                    if self.pentitydefs.has_key(pname):
                        # first definition counts
                        pass
                    elif pvalue[0] in ('"',"'"):
                        pvalue = pvalue[1:-1]
                        cres = entref.search(pvalue)
                        while cres is not None:
                            chr, nm = cres.group('char', 'pname')
                            if chr:
                                repl = self.__parse_charref(cres.group('char'), data, i)
                            elif self.pentitydefs.has_key(nm):
                                repl = self.pentitydefs[nm]
                            else:
                                self.__error("unknown entity `%s' referenced" % nm, data, i)
                                repl = '%%%s;' % nm
                            pvalue = pvalue[:cres.start(0)] + repl + pvalue[cres.end(0):]
                            cres = entref.search(pvalue, cres.start(0)+len(repl))
                        self.pentitydefs[pname] = pvalue
                    else:
                        r = externalid.match(pvalue)
                        publit, syslit = r.group('publit', 'syslit')
                        if publit: publit = publit[1:-1]
                        if syslit: syslit = syslit[1:-1]
                        self.pentitydefs[pname] = publit, syslit
                else:
                    value = res.group('value')
                    if self.entitydefs.has_key(name):
                        self.__error('non-unique entity declaration', data, i)
                    elif value[0] in ('"',"'"):
                        value = value[1:-1]
                        cres = entref.search(value)
                        while cres is not None:
                            chr, nm = cres.group('char', 'pname')
                            if chr:
                                repl = self.__parse_charref(cres.group('char'), data, i)
                            elif self.pentitydefs.has_key(nm):
                                repl = self.pentitydefs[nm]
                            else:
                                self.__error("unknown entity `%s' referenced" % nm, data, i)
                                repl = '%%%s;' % nm
                            value = value[:cres.start(0)] + repl + value[cres.end(0):]
                            cres = entref.search(value, cres.start(0)+len(repl))
                        self.entitydefs[name] = value
                    else:
                        # XXX needs to do something with external entity
                        pass
                i = res.end(0)
            if not internal:
                if data[i:i+1] == '<':
                    hlevel = 1
                    j = i+1
                    while hlevel > 0:
                        res = bracket.search(data, j)
                        if res is None:
                            self.__error("unexpected EOF", data, i, fatal = 1)
                        if data[res.start(0)] == '<':
                            hlevel = hlevel + 1
                        else:
                            hlevel = hlevel - 1
                        j = res.end(0)
                    k = i+1
                    res = peref.search(data, k, j-1)
                    while res is not None:
                        pname = res.group('name')
                        if self.pentitydefs.has_key(pname):
                            val = self.pentitydefs[pname]
                            if type(val) is not type(()):
                                data = data[:res.start(0)] + val + data[res.end(0):]
                                j = j - len(res.group(0)) + len(val)
                            else:
                                k = res.end(0)
                        else:
                            k = res.end(0)
                        res = peref.search(data, k, j-1)
                res = conditional.match(data, i)
                if res is not None:
                    inc, ign = res.group('inc', 'ign')
                    i = res.end(0)
                    if ign:
                        level = 1
                        while level > 0:
                            res = ignore.search(data, i)
                            if res.start(0) == '<':
                                level = level + 1
                            else:
                                level = level - 1
                            i = res.end(0)
                    elif inc:
                        ilevel = ilevel + 1
                if ilevel and data[i:i+3] == ']]>':
                    i = i+3
                    ilevel = ilevel - 1
        if i < len(data):
            self.__error('error while parsing DOCTYPE', data, i)

    def __dfa(self, data, i):
        res = mixedre.match(data, i)
        if res is not None:
            mixed = res.group(0)
            if mixed[-1] == '*':
                mixed = map(string.strip, string.split(mixed[1:-2], '|'))
            else:
                mixed = '#PCDATA'
            return res.end(0), mixed, 0, 0
        dfa = []
        i, start, end = self.__dfa1(data, i, dfa)
##        import pprint
##        pprint.pprint(dfa)
##        print start, end
        return i, dfa, start, end

    def __dfa1(self, data, i, dfa):
        res = dfaelem0.match(data, i)
        if res is None:
            self.__error("syntax error in element content: `(' or Name expecter", data, i, fatal = 1)
        token = res.group('token')
        if token == '(':
            i, start, end = self.__dfa1(data, res.end(0), dfa)
            res = dfaelem1.match(data, i)
            if res is None:
                self.__error("syntax error in element content: `)', `|', or `,' expected", data, i, fatal = 1)
            token = res.group('token')
            sep = token
            while token in (',','|'):
                if sep != token:
                    self.__error("syntax error in element content: `%s' or `)' expected" % sep, data, i, fatal = 1)
                i, nstart, nend = self.__dfa1(data, res.end(0), dfa)
                res = dfaelem1.match(data, i)
                if res is None:
                    self.__error("syntax error in element content: `%s' or `)' expected" % sep, data, i, fatal = 1)
                token = res.group('token')
                if sep == ',':
                    # concatenate DFAs
                    e = dfa[end].get('', [])
                    e.append(nstart)
                    dfa[end][''] = e
                    end = nend
                else:
                    # make parallel
                    s = len(dfa)
                    dfa.append({'': [start, nstart]})
                    e = dfa[end].get('', [])
                    e.append(len(dfa))
                    dfa[end][''] = e
                    e = dfa[nend].get('', [])
                    e.append(len(dfa))
                    dfa[nend][''] = e
                    start = s
                    end = len(dfa)
                    dfa.append({})
            # token == ')'
            i = res.end(0)
        else:
            # it's a Name
            start = len(dfa)
            dfa.append({token: [start+1]})
            end = len(dfa)
            dfa.append({})
            i = res.end(0)
        res = dfaelem2.match(data, i)
        if res is not None:
            token = res.group('token')
            s = len(dfa)
            e = s+1
            if token == '+':
                dfa.append({'': [start]})
            else:
                dfa.append({'': [start, e]})
            dfa.append({})
            l = dfa[end].get('', [])
            dfa[end][''] = l
            if token != '?':
                l.append(start)
            l.append(e)
            start = s
            end = e
            i = res.end(0)
        return i, start, end

    def parse_doctype(self, tag, publit, syslit, data):
        """Parse the DOCTYPE."""
        if data:
            self.parse_dtd(data)
        if syslit:
            import urllib
            syslit = urllib.basejoin(self.baseurl, syslit)
            baseurl = self.baseurl
            self.baseurl = syslit
            external = self.read_external(syslit)
            encoding = self.__encoding
            external = self.__parse_textdecl(external)
            self.parse_dtd(external, 0)
            self.__encoding = encoding
            self.baseurl = baseurl

    def __error(self, message, data = None, i = None, fatal = 1):
        if data is not None and i is not None:
            self.lineno = lineno = string.count(data, '\n', 0, i) + 1
        else:
            self.lineno = None
        self.data = data
        self.offset = i
        if fatal:
            raise Error(message, lineno, data, i)
        self.syntax_error(message)

    # Overridable -- handle xml processing instruction
    def handle_xml(self, encoding, standalone):
        pass

    # Overridable -- handle DOCTYPE
    def handle_doctype(self, tag, publit, syslit, data):
        self.parse_doctype(tag, publit, syslit, data)

    # Example -- read external file referenced from DTD with a SystemLiteral
    def read_external(self, name):
        return ''

    # Example -- handle comment, could be overridden
    def handle_comment(self, data):
        pass

    # Example -- handle processing instructions, could be overridden
    def handle_proc(self, name, data):
        pass

    # Example -- handle data, should be overridden
    def handle_data(self, data):
        pass

    # Example -- handle cdata, should be overridden
    def handle_cdata(self, data):
        pass

    elements = {}                       # dict: tagname -> (startfunc, endfunc)
    def finish_starttag(self, tagname, attrs):
        method = self.elements.get(tagname, (None, None))[0]
        if method is None:
            self.unknown_starttag(tagname, attrs)
        else:
            self.handle_starttag(tagname, method, attrs)

    def finish_endtag(self, tagname):
        method = self.elements.get(tagname, (None, None))[1]
        if method is None:
            self.unknown_endtag(tagname)
        else:
            self.handle_endtag(tagname, method)

    # Overridable -- handle start tag
    def handle_starttag(self, tagname, method, attrs):
        method(tagname, attrs)

    # Overridable -- handle end tag
    def handle_endtag(self, tagname, method):
        method(tagname)

    # To be overridden -- handlers for unknown objects
    def unknown_starttag(self, tagname, attrs):
        pass
        
    def unknown_endtag(self, tagname):
        pass

    def unknown_entityref(self, name):
        self.__error('reference to unknown entity', self.data, self.offset)

    # Example -- handle relatively harmless syntax errors, could be overridden
    def syntax_error(self, message):
        raise Error(message, self.lineno, self.data, self.offset)

class TestXMLParser(XMLParser):

    def __init__(self, xmlns = 1):
        self.testdata = ""
        XMLParser.__init__(self, xmlns)

    def handle_xml(self, encoding, standalone):
        self.flush()
        print 'xml: encoding = %s standalone = %s' % (encoding, standalone)

    def read_external(self, name):
        print 'reading %s' % name
        try:
            import urllib
            if type(name) is type(u'a'):
                name = name.encode('latin-1')
            u = urllib.urlopen(name)
            data = u.read()
            u.close()
        except 'x':
            return ''
        return data

    def handle_doctype(self, tag, publit, syslit, data):
        self.flush()
        print 'DOCTYPE: %s %s' % (tag, `data`)
        self.parse_doctype(tag, publit, syslit, data)

    def handle_comment(self, data):
        self.flush()
        r = `data`
        if len(r) > 68:
            r = r[:32] + '...' + r[-32:]
        print 'comment: %s' % r

    def handle_proc(self, name, data):
        self.flush()
        print 'processing: %s %s' % (name,`data`)

    def handle_data(self, data):
        self.testdata = self.testdata + data
        if len(`self.testdata`) >= 70:
            self.flush()

    def handle_cdata(self, data):
        self.flush()
        print 'cdata: %s' % `data`

    def flush(self):
        data = self.testdata
        if data:
            self.testdata = ""
            print 'data: %s ' % `data`

##    def syntax_error(self, message):
##        if self.lineno is not None:
##            print 'Syntax error at line %d: %s' % (self.lineno, message)
##        else:
##            print 'Syntax error: %s' % message

    def unknown_starttag(self, tag, attrs):
        self.flush()
        if not attrs:
            print 'start tag: <%s>' % tag
        else:
            print 'start tag: <%s' % tag,
            for name, value in attrs.items():
                print '%s = "%s"' % (name.encode('latin-1'), value.encode('latin-1')),
            print '>'

    def unknown_endtag(self, tag):
        self.flush()
        print 'end tag: </%s>' % tag

    def unknown_entityref(self, name):
        self.flush()
        print '&%s;' % name

def test(args = None):
    import sys, getopt
    from time import time

    if not args:
        args = sys.argv[1:]

    opts, args = getopt.getopt(args, 'stn')
    klass = TestXMLParser
    do_time = 0
    namespace = 1
    for o, a in opts:
        if o == '-s':
            klass = XMLParser
        elif o == '-t':
            do_time = 1
        elif o == '-n':
            namespace = 0

    if args:
        file = args[0]
    else:
        file = 'test.xml'

    if file == '-':
        f = sys.stdin
        url = '.'
    else:
        try:
            f = open(file, 'r')
        except IOError, msg:
            print file, ":", msg
            sys.exit(1)
        import urllib
        url = urllib.pathname2url(file)

    data = f.read()
    if f is not sys.stdin:
        f.close()

    x = klass(xmlns = namespace)
    x.baseurl = url
    t0 = time()
    try:
        x.parse(data)
    except Error, info:
        print str(info)
        if info.text is not None and info.offset is not None:
            i = string.rfind(info.text, '\n', 0, info.offset) + 1
            j = string.find(info.text, '\n', info.offset)
            if j == -1: j = len(info.text)
            try:
                print info.text[i:j]
            except UnicodeError:
                print `info.text[i:j]`
            else:
                print ' '*(info.offset-i)+'^'
    t1 = time()
    if do_time:
        print 'total time: %g' % (t1-t0)

if __name__ == '__main__':
    test()
