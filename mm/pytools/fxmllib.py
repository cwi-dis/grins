__version__ = "$Id$"

import re, string
import sys                              # need for CanonXMLParser

class Error(Exception):
    """Error class; raised when a syntax error is encountered.
       Instance variables are:
       lineno: line at which error was found;
       offset: offset into data where error was found;
       text: data in which error was found.
       If these values are unknown, they are set to None."""
    lineno = offset = text = filename = None
    def __init__(self, *args):
        self.args = args
        if len(args) > 1:
            self.lineno = args[1]
            if len(args) > 2:
                self.text = args[2]
                if len(args) > 3:
                    self.offset = args[3]
                    if len(args) > 4:
                        self.filename = args[4]

    def __str__(self):
        if self.filename:
            if self.lineno:
                msg = '"%s", line %d: ' % (self.filename, self.lineno)
            else:
                msg = '"%s": ' % self.filename
        elif self.lineno:
            msg = 'line %d: ' % self.lineno
        else:
            msg = ''
        return '%sSyntax error: %s' % (msg, self.args[0])

# The character sets below are taken directly from the XML spec.
_BaseChar = u'\u0041-\u005A\u0061-\u007A\u00C0-\u00D6\u00D8-\u00F6\u00F8-\u00FF' \
            u'\u0100-\u0131\u0134-\u013E\u0141-\u0148\u014A-\u017E' \
            u'\u0180-\u01C3\u01CD-\u01F0\u01F4-\u01F5\u01FA-\u0217' \
            u'\u0250-\u02A8\u02BB-\u02C1\u0386\u0388-\u038A\u038C' \
            u'\u038E-\u03A1\u03A3-\u03CE\u03D0-\u03D6\u03DA\u03DC\u03DE' \
            u'\u03E0\u03E2-\u03F3\u0401-\u040C\u040E-\u044F\u0451-\u045C' \
            u'\u045E-\u0481\u0490-\u04C4\u04C7-\u04C8\u04CB-\u04CC' \
            u'\u04D0-\u04EB\u04EE-\u04F5\u04F8-\u04F9\u0531-\u0556\u0559' \
            u'\u0561-\u0586\u05D0-\u05EA\u05F0-\u05F2\u0621-\u063A' \
            u'\u0641-\u064A\u0671-\u06B7\u06BA-\u06BE\u06C0-\u06CE' \
            u'\u06D0-\u06D3\u06D5\u06E5-\u06E6\u0905-\u0939\u093D' \
            u'\u0958-\u0961\u0985-\u098C\u098F-\u0990\u0993-\u09A8' \
            u'\u09AA-\u09B0\u09B2\u09B6-\u09B9\u09DC-\u09DD\u09DF-\u09E1' \
            u'\u09F0-\u09F1\u0A05-\u0A0A\u0A0F-\u0A10\u0A13-\u0A28' \
            u'\u0A2A-\u0A30\u0A32-\u0A33\u0A35-\u0A36\u0A38-\u0A39' \
            u'\u0A59-\u0A5C\u0A5E\u0A72-\u0A74\u0A85-\u0A8B\u0A8D' \
            u'\u0A8F-\u0A91\u0A93-\u0AA8\u0AAA-\u0AB0\u0AB2-\u0AB3' \
            u'\u0AB5-\u0AB9\u0ABD\u0AE0\u0B05-\u0B0C\u0B0F-\u0B10' \
            u'\u0B13-\u0B28\u0B2A-\u0B30\u0B32-\u0B33\u0B36-\u0B39\u0B3D' \
            u'\u0B5C-\u0B5D\u0B5F-\u0B61\u0B85-\u0B8A\u0B8E-\u0B90' \
            u'\u0B92-\u0B95\u0B99-\u0B9A\u0B9C\u0B9E-\u0B9F\u0BA3-\u0BA4' \
            u'\u0BA8-\u0BAA\u0BAE-\u0BB5\u0BB7-\u0BB9\u0C05-\u0C0C' \
            u'\u0C0E-\u0C10\u0C12-\u0C28\u0C2A-\u0C33\u0C35-\u0C39' \
            u'\u0C60-\u0C61\u0C85-\u0C8C\u0C8E-\u0C90\u0C92-\u0CA8' \
            u'\u0CAA-\u0CB3\u0CB5-\u0CB9\u0CDE\u0CE0-\u0CE1\u0D05-\u0D0C' \
            u'\u0D0E-\u0D10\u0D12-\u0D28\u0D2A-\u0D39\u0D60-\u0D61' \
            u'\u0E01-\u0E2E\u0E30\u0E32-\u0E33\u0E40-\u0E45\u0E81-\u0E82' \
            u'\u0E84\u0E87-\u0E88\u0E8A\u0E8D\u0E94-\u0E97\u0E99-\u0E9F' \
            u'\u0EA1-\u0EA3\u0EA5\u0EA7\u0EAA-\u0EAB\u0EAD-\u0EAE\u0EB0' \
            u'\u0EB2-\u0EB3\u0EBD\u0EC0-\u0EC4\u0F40-\u0F47\u0F49-\u0F69' \
            u'\u10A0-\u10C5\u10D0-\u10F6\u1100\u1102-\u1103\u1105-\u1107' \
            u'\u1109\u110B-\u110C\u110E-\u1112\u113C\u113E\u1140\u114C' \
            u'\u114E\u1150\u1154-\u1155\u1159\u115F-\u1161\u1163\u1165' \
            u'\u1167\u1169\u116D-\u116E\u1172-\u1173\u1175\u119E\u11A8' \
            u'\u11AB\u11AE-\u11AF\u11B7-\u11B8\u11BA\u11BC-\u11C2\u11EB' \
            u'\u11F0\u11F9\u1E00-\u1E9B\u1EA0-\u1EF9\u1F00-\u1F15' \
            u'\u1F18-\u1F1D\u1F20-\u1F45\u1F48-\u1F4D\u1F50-\u1F57\u1F59' \
            u'\u1F5B\u1F5D\u1F5F-\u1F7D\u1F80-\u1FB4\u1FB6-\u1FBC\u1FBE' \
            u'\u1FC2-\u1FC4\u1FC6-\u1FCC\u1FD0-\u1FD3\u1FD6-\u1FDB' \
            u'\u1FE0-\u1FEC\u1FF2-\u1FF4\u1FF6-\u1FFC\u2126\u212A-\u212B' \
            u'\u212E\u2180-\u2182\u3041-\u3094\u30A1-\u30FA\u3105-\u312C' \
            u'\uAC00-\uD7A3'
_Ideographic = u'\u4E00-\u9FA5\u3007\u3021-\u3029'
_CombiningChar = u'\u0300-\u0345\u0360-\u0361\u0483-\u0486\u0591-\u05A1\u05A3-\u05B9' \
                 u'\u05BB-\u05BD\u05BF\u05C1-\u05C2\u05C4\u064B-\u0652\u0670' \
                 u'\u06D6-\u06DC\u06DD-\u06DF\u06E0-\u06E4\u06E7-\u06E8' \
                 u'\u06EA-\u06ED\u0901-\u0903\u093C\u093E-\u094C\u094D' \
                 u'\u0951-\u0954\u0962-\u0963\u0981-\u0983\u09BC\u09BE\u09BF' \
                 u'\u09C0-\u09C4\u09C7-\u09C8\u09CB-\u09CD\u09D7\u09E2-\u09E3' \
                 u'\u0A02\u0A3C\u0A3E\u0A3F\u0A40-\u0A42\u0A47-\u0A48' \
                 u'\u0A4B-\u0A4D\u0A70-\u0A71\u0A81-\u0A83\u0ABC\u0ABE-\u0AC5' \
                 u'\u0AC7-\u0AC9\u0ACB-\u0ACD\u0B01-\u0B03\u0B3C\u0B3E-\u0B43' \
                 u'\u0B47-\u0B48\u0B4B-\u0B4D\u0B56-\u0B57\u0B82-\u0B83' \
                 u'\u0BBE-\u0BC2\u0BC6-\u0BC8\u0BCA-\u0BCD\u0BD7\u0C01-\u0C03' \
                 u'\u0C3E-\u0C44\u0C46-\u0C48\u0C4A-\u0C4D\u0C55-\u0C56' \
                 u'\u0C82-\u0C83\u0CBE-\u0CC4\u0CC6-\u0CC8\u0CCA-\u0CCD' \
                 u'\u0CD5-\u0CD6\u0D02-\u0D03\u0D3E-\u0D43\u0D46-\u0D48' \
                 u'\u0D4A-\u0D4D\u0D57\u0E31\u0E34-\u0E3A\u0E47-\u0E4E\u0EB1' \
                 u'\u0EB4-\u0EB9\u0EBB-\u0EBC\u0EC8-\u0ECD\u0F18-\u0F19\u0F35' \
                 u'\u0F37\u0F39\u0F3E\u0F3F\u0F71-\u0F84\u0F86-\u0F8B' \
                 u'\u0F90-\u0F95\u0F97\u0F99-\u0FAD\u0FB1-\u0FB7\u0FB9' \
                 u'\u20D0-\u20DC\u20E1\u302A-\u302F\u3099\u309A'
_Digit = u'\u0030-\u0039\u0660-\u0669\u06F0-\u06F9\u0966-\u096F\u09E6-\u09EF' \
         u'\u0A66-\u0A6F\u0AE6-\u0AEF\u0B66-\u0B6F\u0BE7-\u0BEF' \
         u'\u0C66-\u0C6F\u0CE6-\u0CEF\u0D66-\u0D6F\u0E50-\u0E59' \
         u'\u0ED0-\u0ED9\u0F20-\u0F29'
_Extender = u'\u00B7\u02D0\u02D1\u0387\u0640\u0E46\u0EC6\u3005\u3031-\u3035' \
            u'\u309D-\u309E\u30FC-\u30FE'

if 0:
    _BaseChar = 'A-Za-z'
    _Ideographic = ''
    _Digit = '0-9'
    _CombiningChar = ''
    _Extender = ''

_cleanre = re.compile(r'\(\?P<')
def cleanre(re):
    while 1:
        res = _cleanre.search(re)
        if res is None:
            return re
        i = re.find('>', res.end(0))
        re = re[:res.start(0)] + '(?:' + re[i+1:]

_Letter = _BaseChar + _Ideographic
_NameChar = '-' + _Letter + _Digit + '._:' + _CombiningChar + _Extender

_S = '[ \t\r\n]+'                       # white space
_opS = '[ \t\r\n]*'                     # optional white space
_Name = '['+_Letter+'_:]['+_NameChar+']*' # XML Name
_QStr = "(?:'[^']*'|\"[^\"]*\")"        # quoted XML string
_Char = u'\x09\x0A\x0D\x20-\uD7FF\uE000-\uFFFD' # legal characters

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

illegal = re.compile(r'\]\]>')
illegal1 = re.compile('[^'+_Char+']')

cdata = re.compile('<!\\[CDATA\\[(?P<cdata>(?:[^]]|\\](?!\\]>)|\\]\\](?!>))*)\\]\\]>')

_SystemLiteral = '(?P<syslit>'+_QStr+')'
_PublicLiteral = '(?P<publit>"[-\'()+,./:=?;!*#@$_%% \n\ra-zA-Z0-9]*"|' \
                            "'[-()+,./:=?;!*#@$_%% \n\ra-zA-Z0-9]*')"
_ExternalId = '(?:SYSTEM|PUBLIC'+_S+_PublicLiteral+')'+_S+_SystemLiteral
externalid = re.compile(_ExternalId)
ndata = re.compile(_S+'NDATA'+_S+'(?P<name>'+_Name+')')
doctype = re.compile('<!DOCTYPE'+_S+'(?P<docname>'+_Name+')(?:'+_S+_ExternalId+')?'+_opS+'(?:\\[(?P<data>(?:'+_S+'|%'+_Name+';|'+comment.pattern+'|<(?:![^-]|[^!])(?:[^\'">]|\'[^\']*\'|"[^"]*")*>)*)\\]'+_opS+')?>')

xmldecl = re.compile('<\?xml'+
                     _S+'version'+_opS+'='+_opS+'(?P<version>'+_QStr+')'+
                     '(?:'+_S+'encoding'+_opS+'='+_opS+
                        "(?P<encoding>'[A-Za-z][-A-Za-z0-9._]*'|"
                        '"[A-Za-z][-A-Za-z0-9._]*"))?'
                     '(?:'+_S+'standalone'+_opS+'='+_opS+
                        '(?P<standalone>\'(?:yes|no)\'|"(?:yes|no)"))?'+
                     _opS+'\?>')
textdecl = re.compile('<\?xml'
                      '(?:'+_S+'version'+_opS+'='+_opS+'(?P<version>'+_QStr+'))?'+
                      '(?:'+_S+'encoding'+_opS+'='+_opS+
                      "(?P<encoding>'[A-Za-z][-A-Za-z0-9._]*'|"
                      '"[A-Za-z][-A-Za-z0-9._]*"))?'+
                      _opS+'\?>')
pidecl = re.compile('<\\?(?![xX][mM][lL][ \t\r\n?])(?P<name>'+_Name+')(?:'+_S+'(?P<data>(?:[^?]|\\?(?!>))*))?\\?>')

# XML NAMESPACES
_NCName = '['+_Letter+'_]['+'-' + _Letter + _Digit + '._' + _CombiningChar + _Extender+']*'    # XML Name, minus the ":"
ncname = re.compile(_NCName + '$')
qname = re.compile('(?:(?P<prefix>' + _NCName + '):)?' # optional prefix
                   '(?P<local>' + _NCName + ')$')
xmlns = re.compile('xmlns(?::(?P<ncname>' + _NCName + '))?$')

# DOCTYPE
_Nmtoken = '['+_NameChar+']+'
nmtoken = re.compile('^'+_Nmtoken+'$')
nmtokens = re.compile('^'+_Nmtoken+'(?:'+_S+_Nmtoken+')*$')
element = re.compile('<!ELEMENT'+_S+'(?P<name>'+_Name+')'+_S+r'(?P<content>EMPTY|ANY|\()')
dfaelem0 = re.compile(_opS+r'(?P<token>\(|'+_Name+')')
dfaelem1 = re.compile(_opS+r'(?P<token>[)|,])')
dfaelem2 = re.compile(r'(?P<token>[+*?])')
mixedre = re.compile(r'\('+_opS+'#PCDATA'+'(('+_opS+r'\|'+_opS+_Name+')*'+_opS+r'\)\*|'+_opS+r'\))')
paren = re.compile('[()]')
attdef = re.compile(_S+'(?P<atname>'+_Name+')'+_S+'(?P<attype>CDATA|ID(?:REFS?)?|ENTIT(?:Y|IES)|NMTOKENS?|NOTATION'+_S+r'\((?P<notation>'+_opS+_Name+'(?:'+_opS+r'\|'+_opS+_Name+')*'+_opS+r')\)|\('+_opS+_Nmtoken+'(?:'+_opS+r'\|'+_opS+_Nmtoken+')*'+_opS+r'\))'+_S+'(?P<atvalue>#REQUIRED|#IMPLIED|(?:#FIXED'+_S+')?(?P<atstring>'+_QStr+'))')
attlist = re.compile('<!ATTLIST'+_S+'(?P<elname>'+_Name+')(?P<atdef>(?:'+attdef.pattern+')*)'+_opS+'>')
_EntityVal = '"(?:[^"&%]|'+cleanre(ref.pattern)+'|%'+_Name+';)*"|' \
             "'(?:[^'&%]|"+cleanre(ref.pattern)+"|%"+_Name+";)*'"
entity = re.compile('<!ENTITY'+_S+'(?:%'+_S+'(?P<pname>'+_Name+')'+_S+'(?P<pvalue>'+_EntityVal+'|'+cleanre(_ExternalId)+')|(?P<ename>'+_Name+')'+_S+'(?P<value>'+_EntityVal+'|'+cleanre(_ExternalId)+'(?:'+_S+'NDATA'+_S+_Name+')?))'+_opS+'>')
notation = re.compile('<!NOTATION'+_S+'(?P<name>'+_Name+')'+_S+'(?P<value>SYSTEM'+_S+cleanre(_SystemLiteral)+'|PUBLIC'+_S+cleanre(_PublicLiteral)+'(?:'+_S+cleanre(_SystemLiteral)+')?)'+_opS+'>')
peref = re.compile('%(?P<name>'+_Name+');')
ignore = re.compile(r'<!\[|\]\]>')
bracket = re.compile('[<>\'"%]')
conditional = re.compile(r'<!\['+_opS+'(?:(?P<inc>INCLUDE)|(?P<ign>IGNORE))'+_opS+r'\[')

class XMLParser:
    """XMLParser([ xmlns ]) -> instance

       XML document parser.
       There is one optional argument:
       xmlns: understand XML Namespaces (default is 1)."""

    def __init__(self, xmlns = 1):
        self.__xmlns = xmlns            # whether or not to parse namespaces
        self.reset()

    def reset(self):
        """reset()

           Reset parser to pristine state."""
        self.docname = None             # The outermost element in the document (according to the DTD)
        self.rawdata = []
        self.entitydefs = {             # & entities defined in DTD (plus the default ones)
            'lt': '&#60;',              # <
            'gt': '&#62;',              # >
            'amp': '&#38;',             # &
            'apos': '&#39;',            # '
            'quot': '&#34;',            # "
            }
        self.pentitydefs = {}           # % entities defined in DTD
        self.elems = {}                 # elements and their content/attrs
        self.baseurl = '.'              # base URL for external DTD
        self.ids = {}                   # IDs encountered in document
        self.notation = {}              # NOTATIONs
        self.doctype = None

    def feed(self, data):
        """feed(data)

           Feed data to parser."""
        self.rawdata.append(data)

    def close(self):
        """close()

           End of data, finish up parsing."""
        # Actually, this is where we start parsing.
        data = ''.join(self.rawdata)
        self.rawdata = []
        self.parse(data)

    def __parse_textdecl(self, data, document = 0):
        # Figure out the encoding of a file by looking at the first
        # few bytes and the <?xml?> tag that may come at the very
        # beginning of the file.
        # This will convert the data to unicode from whatever format
        # it was originally.
        i = 0
        if data[:2] == '\376\377':
            # UTF-16, big-endian
            enc = 'utf-16-be'
            i = 2
        elif data[:2] == '\377\376':
            # UTF-16, little-endian
            enc = 'utf-16-le'
            i = 2
        elif data[:4] == '\x00\x3C\x00\x3F':
            # UTF-16, big-endian
            enc = 'utf-16-be'
        elif data[:4] == '\x3C\x00\x3F\x00':
            # UTF-16, little-endian
            enc = 'utf-16-le'
        else:
            enc = None                  # unknowns as yet
        if enc:
            try:
                data = unicode(data[i:], enc)
            except UnicodeError:
                self.__error("data cannot be converted to Unicode", data, i, self.baseurl, fatal = 1)
            i = 0
        # optional XMLDecl
        if document:
            res = xmldecl.match(data, i)
        else:
            res = textdecl.match(data, i)
        if res is not None:
            if document:
                version, encoding, standalone = res.group('version',
                                                          'encoding',
                                                          'standalone')
            else:
                version, encoding = res.group('version', 'encoding')
                standalone = None
            if version is not None and version[1:-1] != '1.0':
                self.__error('only XML version 1.0 supported', data, res.start('version'), self.baseurl, fatal = 1)
            if encoding:
                encoding = encoding[1:-1]
                if enc and enc != encoding.lower() and \
                   enc[:6] != encoding.lower():
                    self.__error("declared encoding doesn't match actual encoding", data, res.start('encoding'), self.baseurl, fatal = 1)
                enc = encoding.lower()
            if standalone:
                standalone = standalone[1:-1]
##            self.handle_xml(encoding, standalone)
            i = res.end(0)
        if enc is None:
            # default is UTF 8
            enc = 'utf-8'
        if type(data) is not type(u'a'):
            try:
                data = unicode(data[i:], enc)
            except UnicodeError:
                self.__error("data cannot be converted to Unicode", data, i, self.baseurl, fatal = 1)
        else:
            data = data[i:]
        return data

    def __normalize_linefeed(self, data):
        # normalize line endings: first \r\n -> \n, then \r -> \n
        return u'\n'.join(u'\n'.join(data.split(u'\r\n')).split(u'\r'))

    def __normalize_space(self, data):
        # normalize white space: tab, linefeed and carriage return -> space
        data = ' '.join(data.split('\t'))
        data = ' '.join(data.split('\n'))
        data = u' '.join(data.split('\r'))
        return data

    def parse(self, data):
        """parse(data)

           Parse the data as an XML document."""
        from time import time
        t0 = time()
        data = self.__parse_textdecl(data, 1)
        data = self.__normalize_linefeed(data)
        # (Comment | PI | S)*
        i = self.__parse_misc(data, 0)
        # doctypedecl?
        res = doctype.match(data, i)
        if res is not None and self.doctype is None:
            docname, publit, syslit, docdata = res.group('docname', 'publit',
                                                        'syslit', 'data')
            self.docname = docname
            if publit: publit = ' '.join(publit[1:-1].split(None))
            if syslit: syslit = syslit[1:-1]
            self.handle_doctype(docname, publit, syslit, docdata)
            i = res.end(0)
        elif self.doctype:
            # do as if there was a <!DOCTYPE> declaration
            self.handle_doctype(None, '', self.doctype, '')
        else:
            # self.doctype == '' or no DOCTYPE
            # ignore DOCTYPE
            self.doctype = None
        t1 = time()
        # (Comment | PI | S)*
        i = self.__parse_misc(data, i)
        # the document itself
        res = starttag.match(data, i)
        if res is None:
            self.__error('no elements in document', data, i, self.baseurl, fatal = 1)
        i = res.end(0)
        tagname, slash = res.group('tagname', 'slash')
        if self.docname and tagname != self.docname:
            self.__error('starttag does not match DOCTYPE', data, res.start('tagname'), self.baseurl, fatal = 0)
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
                self.__error('end tag missing', data, i, self.baseurl, fatal = 0)
            elif res.group('tagname') != tagname:
                self.__error("end tag doesn't match start tag", data, res.start('tagname'), self.baseurl, fatal = 0)
            i = res.end(0)
        self.finish_endtag(nstag)
        i = self.__parse_misc(data, i)
        if i != len(data):
            self.__error('garbage at end of document', data, i, self.baseurl, fatal = 0)
        t2 = time()
        return t0, t1, t2

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
                    self.__error('illegal characters in comment', data, ires.start(0), self.baseurl, fatal = 0)
                self.handle_comment(data[c0:c1])
                i = res.end(0)
            res = pidecl.match(data, i)
            if res is not None:
                matched = 1
                c0, c1 = res.span('data')
                ires = illegal1.search(data, c0, c1)
                if ires is not None:
                    self.__error('illegal characters in Processing Instruction', data, ires.start(0), self.baseurl, fatal = 0)
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
        # states reachable using epsilon transitions
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

    def __check_dfa(self, dfa, initstate, tagname, data, i):
        states = [initstate]
        possibles = {}
        seenstates = {}
        while states:
            s = states[0]
            seenstates[s] = 1
            del states[0]
            for tag in dfa[s].keys():
                if tag and possibles.has_key(tag):
                    self.__error("non-deterministic content model for `%s'" % tagname, data, i, self.baseurl, fatal = 0)
                possibles[tag] = 1
            for s in dfa[s].get('', []):
                if not seenstates.has_key(s):
                    states.append(s)

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
                    self.__error("illegal data content in element `%s'" % ptagname, data, i, self.baseurl, fatal = 0)
                skip = 0
                complain = 0
                if content is not None:
                    res = space.match(data, i, j)
                    isspace = res is not None and res.span(0) == (i,j)
                    if content == 'EMPTY':
                        complain = 1
                        skip = 1
                    elif not isspace and  type(content) is type([]) and content and type(content[0]) is type({}):
                        complain = 1
                    if complain:
                        self.__error("no character data allowed in element `%s'" % ptagname, data, i, self.baseurl, fatal = 0)
                matched = 1
                if not skip:
                    self.handle_data(data[i:j])
                i = j
            res = starttag.match(data, i)
            if res is not None:
                tagname, slash = res.group('tagname', 'slash')
                if content == 'EMPTY' or content == '#PCDATA':
                    self.__error("empty element `%s' has content" % ptagname, data, res.start(0), self.baseurl, fatal = 0)
                elif content == 'ANY':
                    # always OK
                    pass
                elif type(content) is type([]) and content and type(content[0]) is not type({}):
                    # mixed
                    if tagname not in content:
                        self.__error("illegal content in element `%s'" % ptagname, data, res.start(0), self.baseurl, fatal = 0)
                elif content is not None:
                    self.__update_state(content, states, tagname)
                    if not states:
                        self.__error("illegal content for element `%s'" % ptagname, data, i, self.baseurl)
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
                        self.__error('end tag missing', data, i, self.baseurl, fatal = 0)
                    elif res.group('tagname') != tagname:
                        self.__error("end tag doesn't match start tag", data, res.start('tagname'), self.baseurl, fatal = 0)
                    i = res.end(0)
                self.finish_endtag(nstag)
                matched = 1
            res = endtag.match(data, i)
            if res is not None:
                if type(content) is type([]) and content and type(content[0]) is type({}):
                    self.__update_state(content, states, None)
                    if end not in states:
                        self.__error("content of element `%s' doesn't match content model" % ptagname, data, i, self.baseurl, fatal = 0)
                return res
            res = comment.match(data, i)
            if res is not None:
                c0, c1 = res.span('comment')
                ires = illegal1.search(data, c0, c1)
                if ires is not None:
                    self.__error('illegal characters in comment', data, ires.start(0), self.baseurl, fatal = 0)
                self.handle_comment(data[c0:c1])
                i = res.end(0)
                matched = 1
            res = ref.match(data, i)
            if res is not None:
                name = res.group('name')
                if name:
                    if self.entitydefs.has_key(name):
                        sval = val = self.entitydefs[name]
                        baseurl = self.baseurl
                        if type(val) is type(()):
                            if val[2] is not None:
                                apply(self.handle_ndata, val)
                                val = None
                            else:
                                val = self.__read_pentity(val[0], val[1])
                        if val is not None:
                            del self.entitydefs[name] # to break recursion
                            n = self.__parse_content(val, 0, ptagname, namespaces, states)
                            self.entitydefs[name] = sval # restore value
                        if val is not None:
                            if n is None:
                                self.baseurl = baseurl
                                return
                            if type(n) is type(res) or n != len(val):
                                if type(n) is type(res):
                                    n = res.start(0)
                                self.__error('misformed entity value', data, n, self.baseurl, fatal = 0)
                        self.baseurl = baseurl
                    else:
                        if self.docname:
                            self.__error("unknown entity reference `&%s;' in element `%s'" % (name, ptagname), data, i, self.baseurl, fatal = 0)
                        self.data = data
                        self.offset = res.start('name')
                        self.lineno = data.count('\n', 0, self.offset)
                        self.unknown_entityref(name)
                else:
                    str = self.__parse_charref(res.group('char'), data, res.start(0))
                    if str is None:
                        return
                    self.handle_data(str)
                i = res.end(0)
                matched = 1
            res = pidecl.match(data, i)
            if res is not None:
                matched = 1
                c0, c1 = res.span('data')
                ires = illegal1.search(data, c0, c1)
                if ires is not None:
                    self.__error('illegal characters in Processing Instruction', data, ires.start(0), self.baseurl, fatal = 0)
                self.handle_proc(res.group('name'), res.group('data') or '')
                i = res.end(0)
            res = cdata.match(data, i)
            if res is not None:
                matched = 1
                c0, c1 = res.span('cdata')
                ires = illegal1.search(data, c0, c1)
                if ires is not None:
                    self.__error('illegal characters in CDATA section', data, ires.start(0), self.baseurl, fatal = 0)
                self.handle_cdata(res.group('cdata'))
                i = res.end(0)
            if not matched:
                self.__error("no valid content in element `%s'" % ptagname, data, i, self.baseurl)
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
                self.__error("attribute `%s' in element `%s' does not have correct value" % (attrname, tagname), data, attrstart, self.baseurl, fatal = 0)
        if attype == 'CDATA':
            return value                # always OK and don't change value
        if type(attype) is type([]):    # enumeration
            if value not in attype:
                self.__error("attribute `%s' in element `%s' not valid" % (attrname, tagname), data, attrstart, self.baseurl, fatal = 0)
            return value
        if type(attype) is type(()):
            if value not in attype[1]:
                self.__error("attribute `%s' in element `%s' not valid" % (attrname, tagname), data, attrstart, self.baseurl, fatal = 0)
            return value
        if attype == 'ID':
            if name.match(value) is None:
                self.__error("attribute `%s' in element `%s' is not an ID" % (attrname, tagname), data, attrstart, self.baseurl, fatal = 0)
            if self.ids.has_key(value):
                self.__error("attrbute `%s' in element `%s' is not unique" %  (attrname, tagname), data, attrstart, self.baseurl, fatal = 0)
            self.ids[value] = 1
            return value
        if attype == 'IDREF':
            if name.match(value) is None:
                self.__error("attrbute `%s' in element `%s' is not an IDREF" % (attrname, tagname), data, attrstart, self.baseurl, fatal = 0)
            # XXX should check ID exists
            return value
        if attype == 'IDREFS':
            if names.match(value) is None:
                self.__error("attrbute `%s' in element `%s' is not an IDREFS" % (attrname, tagname), data, attrstart, self.baseurl, fatal = 0)
            # XXX should check IDs exist
            return value
        if attype == 'NMTOKEN':
            if nmtoken.match(value) is None:
                self.__error("attrbute `%s' in element `%s' is not a NMTOKEN" % (attrname, tagname), data, attrstart, self.baseurl, fatal = 0)
            return value
        if attype == 'NMTOKENS':
            if nmtokens.match(value) is None:
                self.__error("attrbute `%s' in element `%s' is not a NMTOKENS" % (attrname, tagname), data, attrstart, self.baseurl, fatal = 0)
            return value
        if attype == 'ENTITY':
            if name.match(value) is None:
                self.__error("attrbute `%s' in element `%s' is not an ENTITY" % (attrname, tagname), data, attrstart, self.baseurl, fatal = 0)
            # XXX should check ENTITY exists
            return value
        if attype == 'ENTITIES':
            if names.match(value) is None:
                self.__error("attrbute `%s' in element `%s' is not an ENTITIES" % (attrname, tagname), data, attrstart, self.baseurl, fatal = 0)
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
                self.__error('bad attributes', data, i, self.baseurl, fatal = 0)
                return
            name = res.group('attrname')
            if reqattrs.has_key(name):
                del reqattrs[name]      # seen this #REQUIRED attribute
            if attributes is not None and attributes.has_key(name):
                attype = attributes[name][0]
            else:
                attype = None
            start, end = res.span('attrvalue')
            value = self.__parse_attrval(data, attype, span = (start+1, end-1))
            if value is None:
                # bad attribute value: ignore, but continue parsing
                i = res.end(0)
                continue
            attrstart = res.start('attrname')
            if attributes is not None:
                if attributes.has_key(name):
                    attrseen[name] = 1
                    value = self.__check_attr(tagname, name, value, attributes, data, attrstart)
                else:
                    self.__error("unknown attribute `%s' on element `%s'" % (name, tagname), data, attrstart, self.baseurl, fatal = 0)
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
            reqattrs = "', `".join(reqattrs)
            self.__error("required attribute%s `%s' of element `%s' missing" % (s, reqattrs, tagname), data, dataend, self.baseurl, fatal =  0)
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
                if ns is not None:
                    tagname = ns + ' ' + nstag
                elif prefix != '':
                    self.__error("unknown namespace prefix `%s'" % prefix, data, tagstart, self.baseurl, fatal = 0)
            else:
                self.__error("badly formed tag name `%s'" % tagname, data, tagstart, self.baseurl, fatal = 0)
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
                        if ans is not None:
                            attr = ans + ' ' + nsattr
                        elif prefix != '':
                            self.__error("unknown namespace prefix `%s'" % prefix, data, attrstart, self.baseurl, fatal = 0)
                else:
                    self.__error("badly formed attribute name `%s'" % attr, data, attrstart, self.baseurl, fatal = 0)
            if attrdict.has_key(attr):
                self.__error("duplicate attribute name `%s'" % attr, data, attrstart, self.baseurl, fatal = 0)
            attrdict[attr] = value
        return tagname, attrdict, namespaces

    def __parse_attrval(self, data, attype, span = None):
        # parse an attribute value, replacing entity and character
        # references with their values
        if span is None:
            i = 0
            dataend = len(data)
        else:
            i, dataend = span
        res = illegal1.search(data, i, dataend)
        if res is not None:
            self.__error("illegal characters in attribute value", data, res.start(0), self.baseurl, fatal = 0)
        newval = []
        while i < dataend:
            res = interesting.search(data, i, dataend)
            if res is None:
                str = data[i:dataend]
                if attype is None or attype == 'CDATA':
                    str = self.__normalize_space(str)
                newval.append(str)
                break
            j = res.start(0)
            if data[j] == '<':
                self.__error("no `<' allowed in attribute value", data, j, self.baseurl, fatal = 0)
            if j > i:
                str = data[i:j]
                if attype is None or attype == 'CDATA':
                    str = self.__normalize_space(str)
                newval.append(str)
            res = ref.match(data, j, dataend)
            if res is None:
                self.__error('illegal attribute value', data, j, self.baseurl, fatal = 0)
                newval.append(data[j])  # the &
                i = j + 1               # continue searching after the &
                continue
            i = res.end(0)
            name = res.group('name')
            if name:
                # entity reference (e.g. "&lt;")
                if self.entitydefs.has_key(name):
                    val = self.entitydefs[name]
                    if type(val) is type(()):
                        self.__error("no external parsed entity allowed in attribute value", data, res.start(0), self.baseurl, fatal = 1)
                    del self.entitydefs[name]
                    nval = self.__parse_attrval(val, attype)
                    self.entitydefs[name] = val
                    if nval is None:
                        return
                    newval.append(nval)
                else:
                    self.__error("reference to unknown entity `%s'" % name, data, res.start(0), self.baseurl, fatal = 0)
                    newval.append('&%s;' % name)
            else:
                val = self.__parse_charref(res.group('char'), data, res.start(0))
                if val is None:
                    newval.append('&#%s;' % res.group('char'))
                    continue
                newval.append(val)
        str = ''.join(newval)
        if attype is not None and attype != 'CDATA':
            str = ' '.join(str.split(None))
        return str

    def __parse_charref(self, name, data, i):
        # parse a character reference (e.g. "%#38;")
        # the "name" arg is just part between # and ;
        if name[0] == 'x':
            # e.g. &#x26;
            n = int(name[1:], 16)
        else:
            # e.g. &#38;
            n = int(name)
        try:
            c = unichr(n)
        except ValueError:
            self.__error('bad character reference', data, i, self.baseurl, fatal = 0)
            return
        if illegal1.search(c):
            self.__error('bad character reference', data, i, self.baseurl, fatal = 0)
        return c

    def __read_pentity(self, publit, syslit):
        import urllib
        syslit = urllib.basejoin(self.baseurl, syslit)
        baseurl = self.baseurl
        self.baseurl = syslit
        val = self.read_external(publit, syslit)
        val = self.__parse_textdecl(val)
        return self.__normalize_linefeed(val)

    def parse_dtd(self, data, internal = 1):
        """parse_dtd(data[, internal ])

           Parse the DTD.
           This method is called by the parse_doctype method and is
           provided so that parse_doctype can be overridden.
           Argument is a string containing the full DTD.
           Optional argument internal is true (default) if the DTD is
           internal."""
        i = 0
        matched = 1
        ilevel = 0                      # nesting level of ignored sections
        while i < len(data) and matched:
            matched = 0
            res = peref.match(data, i)
            if res is not None:
                matched = 1
                name = res.group('name')
                if self.pentitydefs.has_key(name):
                    val = self.pentitydefs[name]
                    baseurl = self.baseurl
                    if type(val) is type(()):
                        val = self.__read_pentity(val[0], val[1])
                    self.parse_dtd(val, internal)
                    self.baseurl = baseurl
                else:
                    self.__error("unknown entity `%%%s;'" % name, data, i, self.baseurl, fatal = 0)
                i = res.end(0)
            res = element.match(data, i)
            if res is not None:
                matched = 1
                name, content = res.group('name', 'content')
                i = res.end(0)
                elemval = (None, {}, None, None, None)
                if self.elems.has_key(name):
                    elemval = self.elems[name]
                    if elemval[0] is not None:
                        # XXX is this an error?
                        self.__error('non-unique element name declaration', data, i, self.baseurl, fatal = 0)
                    elif content == 'EMPTY':
                        # check for NOTATION on EMPTY element
                        for atname, (attype, atvalue, atstring) in elemval[1].items():
                            if type(attype) is type(()) and attype[0] == 'NOTATION':
                                self.__error("NOTATION not allowed on EMPTY element", data, i, self.baseurl)
                if content[0] == '(':
                    i = res.start('content')
                    j, content, start, end, str = self.__dfa(data, i)
                    if type(content) is type([]) and content and type(content[0]) is type({}):
                        self.__check_dfa(content, start, name, data, i)
                    contentstr = str # data[i:j]
                    i = j
                else:
                    contentstr = content
                    start = end = 0
                self.elems[name] = (content, elemval[1], start, end, contentstr)
                res = space.match(data, i)
                if res is not None:
                    i = res.end(0)
                if data[i:i+1] != '>':
                    self.__error('bad DOCTYPE', data, i, self.baseurl)
                    return
                i = i+1
            res = attlist.match(data, i)
            if res is not None:
                matched = 1
                elname, atdef = res.group('elname', 'atdef')
                if not self.elems.has_key(elname):
                    self.elems[elname] = (None, {}, None, None, None)
                ares = attdef.match(atdef)
                while ares is not None:
                    atname, attype, atvalue, atstring = ares.group('atname', 'attype', 'atvalue', 'atstring')
                    if attype[0] == '(':
                        attype = map(string.strip, attype[1:-1].split('|'))
                    elif attype[:8] == 'NOTATION':
                        if self.elems[elname][0] == 'EMPTY':
                            self.__error("NOTATION not allowed on EMPTY element", data, ares.start('attype'), self.baseurl)
                        atnot = map(string.strip, ares.group('notation').split('|'))
                        attype = ('NOTATION', atnot)
                    if atstring:
                        atstring = atstring[1:-1] # remove quotes
                        atstring = self.__parse_attrval(atstring, attype)
                        if attype != 'CDATA':
                            atstring = ' '.join(atstring.split(None))
                        else:
                            atstring = ' '.join(atstring.split('\t'))
                    if type(attype) is type([]):
                        if atstring is not None and atstring not in attype:
                            self.__error("default value for attribute `%s' on element `%s' not listed as possible value" % (atname, elname), data, i, self.baseurl)
                    elif type(attype) is type(()):
                        if atstring is not None and atstring not in attype[1]:
                            self.__error("default value for attribute `%s' on element `%s' not listed as possible value" % (atname, elname), data, i, self.baseurl)
                    if not self.elems[elname][1].has_key(atname):
                        # first definition counts
                        self.elems[elname][1][atname] = attype, atvalue, atstring
                    ares = attdef.match(atdef, ares.end(0))
                i = res.end(0)
            res = entity.match(data, i)
            if res is not None:
                matched = 1
                pname, name = res.group('pname', 'ename')
                if pname:
                    pvalue = res.group('pvalue')
                    if pvalue[0] in ('"',"'"):
                        c0, c1 = res.span('pvalue')
                        ires = illegal1.search(data, c0+1, c1-1)
                        if ires is not None:
                            self.__error("illegal characters in entity value", data, ires.start(0), self.baseurl, fatal = 0)
                    if self.pentitydefs.has_key(pname):
                        # first definition counts
                        pass
                    elif pvalue[0] in ('"',"'"):
                        pvalue = pvalue[1:-1]
                        pvalue = self.__normalize_space(pvalue)
                        cres = entref.search(pvalue)
                        while cres is not None:
                            chr, nm = cres.group('char', 'pname')
                            if chr:
                                repl = self.__parse_charref(cres.group('char'), data, i)
                            elif self.pentitydefs.has_key(nm):
                                repl = self.pentitydefs[nm]
                            else:
                                self.__error("unknown entity `%s' referenced" % nm, data, i, self.baseurl)
                                repl = '%%%s;' % nm
                            if type(repl) is type(()):
                                baseurl = self.baseurl
                                repl = self.__read_pentity(repl[0], repl[1])
                                self.baseurl = baseurl
                            pvalue = pvalue[:cres.start(0)] + repl + pvalue[cres.end(0):]
                            cres = entref.search(pvalue, cres.start(0)+len(repl))
                        self.pentitydefs[pname] = pvalue
                    else:
                        r = externalid.match(pvalue)
                        publit, syslit = r.group('publit', 'syslit')
                        if publit: publit = ' '.join(publit[1:-1].split(None))
                        if syslit: syslit = syslit[1:-1]
                        self.pentitydefs[pname] = publit, syslit
                else:
                    value = res.group('value')
                    if value[0] in ('"',"'"):
                        c0, c1 = res.span('value')
                        ires = illegal1.search(data, c0+1, c1-1)
                        if ires is not None:
                            self.__error("illegal characters in entity value", data, ires.start(0), self.baseurl, fatal = 0)
                    if self.entitydefs.has_key(name):
                        # use first definition
                        pass
                    elif value[0] in ('"',"'"):
                        value = value[1:-1]
                        value = self.__normalize_space(value)
                        cres = entref.search(value)
                        while cres is not None:
                            chr, nm = cres.group('char', 'pname')
                            if chr:
                                repl = self.__parse_charref(cres.group('char'), data, i)
                            elif self.pentitydefs.has_key(nm):
                                repl = self.pentitydefs[nm]
                                if type(repl) is type(()):
                                    baseurl = self.baseurl
                                    repl = self.__read_pentity(repl[0], repl[1])
                                    self.baseurl = baseurl
                            else:
                                self.__error("unknown entity `%s' referenced" % nm, data, i, self.baseurl)
                                repl = '%%%s;' % nm
                            value = value[:cres.start(0)] + repl + value[cres.end(0):]
                            cres = entref.search(value, cres.start(0)+len(repl))
                        self.entitydefs[name] = value
                    else:
                        r = externalid.match(value)
                        publit, syslit = r.group('publit', 'syslit')
                        if publit: publit = ' '.join(publit[1:-1].split(None))
                        if syslit: syslit = syslit[1:-1]
                        r1 = ndata.match(value, r.end(0))
                        if r1 is not None:
                            ndataname = r1.group('name')
                        else:
                            ndataname = None
                        self.entitydefs[name] = publit, syslit, ndataname
                i = res.end(0)
            res = notation.match(data, i)
            if res is not None:
                matched = 1
                name, value = res.group('name', 'value')
                if not self.notation.has_key(name):
                    self.notation[name] = value
                i = res.end(0)
            j = i                       # remember where we were
            i = self.__parse_misc(data, i)
            matched = matched or i > j  # matched anything?
            if not internal:
                if data[i:i+1] == '<':
                    hlevel = 1
                    quote = None
                    j = i+1
                    while hlevel > 0:
                        res = bracket.search(data, j)
                        if res is None:
                            self.__error("unexpected EOF", data, i, self.baseurl, fatal = 1)
                        j = res.end(0)
                        c = data[res.start(0)]
                        if c == '<':
                            hlevel = hlevel + 1
                        elif quote and c == quote:
                            quote = None
                        elif c in ('"', "'"):
                            quote = c
                        elif c == '>':
                            hlevel = hlevel - 1
                        elif hlevel == 1 and not quote:
                            # only expand parsed entities at lowest level
                            res = peref.match(data, res.start(0))
                            if res is not None:
                                pname = res.group('name')
                                if self.pentitydefs.has_key(pname):
                                    repl = self.pentitydefs[pname]
                                    if type(repl) is type(()):
                                        baseurl = self.baseurl
                                        repl = self.__read_pentity(repl[0], repl[1])
                                        self.baseurl = baseurl
                                    data = data[:res.start(0)] + ' ' + repl + ' ' + data[res.end(0):]
                                    j = res.start(0) + len(repl) + 2
                                else:
                                    j = res.end(0)
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
            self.__error('error while parsing DOCTYPE', data, i, self.baseurl)

    def __dfa(self, data, i):
        res = mixedre.match(data, i)
        if res is not None:
            mixed = str = res.group(0)
            if mixed[-1] == '*':
                mixed = map(string.strip, mixed[1:-2].split('|'))
            else:
                mixed = '#PCDATA'
            return res.end(0), mixed, 0, 0, str
        dfa = []
        i, start, end, str = self.__dfa1(data, i, dfa)
        return i, dfa, start, end, str

    def __dfa1(self, data, i, dfa):
        res = dfaelem0.match(data, i)
        if res is None:
            self.__error("syntax error in element content: `(' or Name expecter", data, i, self.baseurl, fatal = 1)
        token = res.group('token')
        if token == '(':
            i, start, end, str = self.__dfa1(data, res.end(0), dfa)
            res = dfaelem1.match(data, i)
            if res is None:
                self.__error("syntax error in element content: `)', `|', or `,' expected", data, i, self.baseurl, fatal = 1)
            token = res.group('token')
            sep = token
            while token in (',','|'):
                if sep != token:
                    self.__error("syntax error in element content: `%s' or `)' expected" % sep, data, i, self.baseurl, fatal = 1)
                str = str + sep
                i, nstart, nend, nstr = self.__dfa1(data, res.end(0), dfa)
                str = str + nstr
                res = dfaelem1.match(data, i)
                if res is None:
                    self.__error("syntax error in element content: `%s' or `)' expected" % sep, data, i, self.baseurl, fatal = 1)
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
            str = '(' + str + ')'
        else:
            # it's a Name
            str = token
            start = len(dfa)
            dfa.append({token: [start+1]})
            end = len(dfa)
            dfa.append({})
            i = res.end(0)
        res = dfaelem2.match(data, i)
        if res is not None:
            token = res.group('token')
            if str[-1] != ')':
                str = '(' + str + ')'
            str = str + token
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
        return i, start, end, str

    def parse_doctype(self, tag, publit, syslit, data):
        """parse_doctype(tag, publit, syslit, data)

           Parse the DOCTYPE.

           This method is called by the handle_doctype callback method
           and is provided so that handle_doctype can be overridden.
           The arguments are:
           tag: the name of the outermost element of the document;
           publit: the Public Identifier of the DTD (or None);
           syslit: the System Literal of the DTD (or None);
           data: the internal subset of the DTD (or None)."""
        if data:
            self.parse_dtd(data)
        if syslit:
            import urllib
            syslit = urllib.basejoin(self.baseurl, syslit)
            baseurl = self.baseurl
            self.baseurl = syslit
            external = self.read_external(publit, syslit)
            external = self.__parse_textdecl(external)
            external = self.__normalize_linefeed(external)
            self.parse_dtd(external, 0)
            self.baseurl = baseurl

    def __error(self, message, data = None, i = None, filename = None, fatal = 1):
        # called for all syntax errors
        # this either raises an exception (Error) or calls
        # self.syntax_error which may be overridden
        if data is not None and i is not None:
            self.lineno = lineno = data.count('\n', 0, i) + 1
        else:
            self.lineno = None
        self.data = data
        self.offset = i
        self.filename = filename
        if fatal:
            raise Error(message, lineno, data, i, filename)
        self.syntax_error(message)

    # Overridable -- handle xml processing instruction
    def handle_xml(self, encoding, standalone):
        pass

    # Overridable -- handle DOCTYPE
    def handle_doctype(self, tag, publit, syslit, data):
        if self.doctype is not None:
            syslit = self.doctype
        self.parse_doctype(tag, publit, syslit, data)

    # Example -- read external file referenced from DTD with a SystemLiteral
    def read_external(self, publit, syslit):
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
        self.__error('reference to unknown entity', self.data, self.offset, self.baseurl)

    # Example -- handle relatively harmless syntax errors, could be overridden
    def syntax_error(self, message):
        raise Error(message, self.lineno, self.data, self.offset, self.filename)

class TestXMLParser(XMLParser):

    def __init__(self, xmlns = 1):
        self.testdata = ""
        XMLParser.__init__(self, xmlns)

    def handle_xml(self, encoding, standalone):
        self.flush()
        print 'xml: encoding = %s standalone = %s' % (encoding, standalone)

    def read_external(self, publit, syslit):
        print 'reading %s' % name
        try:
            import urllib
            u = urllib.urlopen(syslit)
            data = u.read()
            u.close()
        except 'x':
            return ''
        return data

    def handle_doctype(self, tag, publit, syslit, data):
        self.flush()
        print 'DOCTYPE: %s %s' % (tag, `data`)
        XMLParser.handle_doctype(self, tag, publit, syslit, data)

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
                print '%s = "%s"' % (name.encode('latin-1'), `value`),
            print '>'

    def unknown_endtag(self, tag):
        self.flush()
        print 'end tag: </%s>' % tag

    def unknown_entityref(self, name):
        self.flush()
        print '&%s;' % name

class CanonXMLParser(XMLParser):
    __cache = {}

    def read_external(self, publit, syslit):
        if publit and self.__cache.has_key(publit):
            return self.__cache[publit]
        try:
            import urllib
            u = urllib.urlopen(syslit)
            data = u.read()
            u.close()
        except 'x':
            return ''
        if publit:
            self.__cache[publit] = data
        return data

    def handle_data(self, data):
        sys.stdout.write(self.encode(data))

    def handle_cdata(self, data):
        sys.stdout.write(self.encode(data))

    def handle_proc(self, name, data):
        sys.stdout.write('<?%s %s?>' % (name.encode('utf-8'), data.encode('utf-8')))

    def unknown_starttag(self, tag, attrs):
        sys.stdout.write('<%s' % tag.encode('utf-8'))
        attrlist = attrs.items()
        attrlist.sort()
        for name, value in attrlist:
            sys.stdout.write(' %s="%s"' % (name.encode('utf-8'), self.encode(value)))
        sys.stdout.write('>')

    def unknown_endtag(self, tag):
        sys.stdout.write('</%s>' % tag.encode('utf-8'))

    def unknown_entityref(self, name):
        print '&%s;' % name.encode('utf-8')

    def encode(self, data):
        for c, tr in [('&', '&amp;'),
                      ('>', '&gt;'),
                      ('<', '&lt;'),
                      ('"', '&quot;'),
                      ('\t', '&#9;'),
                      ('\n', '&#10;'),
                      ('\r', '&#13;')]:
            data = tr.join(data.split(c))
        return data.encode('utf-8')

class CheckXMLParser(XMLParser):
    __cache = {}

    def read_external(self, publit, syslit):
        if publit and self.__cache.has_key(publit):
            return self.__cache[publit]
        try:
            import urllib
            u = urllib.urlopen(syslit)
            data = u.read()
            u.close()
        except 'x':
            return ''
        if publit:
            self.__cache[publit] = data
        return data

def test(args = None):
    import sys, getopt

    if not args:
        args = sys.argv[1:]

    opts, args = getopt.getopt(args, 'cstnvCd:')
    klass = TestXMLParser
    do_time = 0
    namespace = 1
    verbose = 0
    doctype = None
    for o, a in opts:
        if o == '-c':
            klass = CanonXMLParser
        elif o == '-C':
            klass = CheckXMLParser
        elif o == '-s':
            klass = XMLParser
        elif o == '-t':
            do_time = 1
        elif o == '-n':
            namespace = 0
        elif o == '-v':
            verbose = 1
        elif o == '-d':
            doctype = a

    if not args:
        args = ['test.xml']

    for file in args:
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
        x.doctype = doctype
        if verbose:
            print '==============',file
        try:
            t0, t1, t2 = x.parse(data)
        except Error, info:
            do_time = 0                 # can't print times now
            print str(info)
            if info.text is not None and info.offset is not None:
                i = info.text.rfind('\n', 0, info.offset) + 1
                j = info.text.find('\n', info.offset)
                if j == -1: j = len(info.text)
                try:
                    print info.text[i:j]
                except UnicodeError:
                    print `info.text[i:j]`
                else:
                    print ' '*(info.offset-i)+'^'
        if klass is CanonXMLParser and (verbose or len(args) > 1):
            sys.stdout.write('\n')
        if do_time:
            print 'total time: %g' % (t2-t0)
            print 'parse DTD: %g' % (t1-t0)
            print 'parse body: %g' %(t2-t1)

if __name__ == '__main__':
    test()
