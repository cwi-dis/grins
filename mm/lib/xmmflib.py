__version__ = "$Id$"

import xmllib, parseutil

class XMMFParser(xmllib.XMLParser):
    topelement = 'xmmf'
    attributes = {
            topelement: {'id':None,
                         'xmlns':None,},
            'head': {'id':None,},
            'metadata': {'id':None,},
            'body': {'id':None,},
            'marker': {'id':None,
                       'begin':None,
                       'dur':None,
                       'end':None,},
            }
    entities = {
            topelement: ['head', 'body',],
            'head': ['metadata',],
            'body': ['marker',],
            }

    def __init__(self, file = None, printfunc = None):
        self.elements = {
                'marker': (self.start_marker, None),
                }
        self.__file = file or '<unknown file>'
        self.__printdata = []
        self.__printfunc = printfunc
        self.markers = {}
        xmllib.XMLParser.__init__(self)

    def start_marker(self, attributes):
        id = attributes.get('id')
        if id is None:
            self.syntax_error("Required attribute `id' missing")
            return
        begin = attributes.get('begin')
        if begin is not None:
            begin = parseutil.parsecounter(begin, syntax_error = self.syntax_error)
        else:
            begin = 0
        dur = attributes.get('dur')
        if dur is not None:
            dur = parseutil.parsecounter(dur, syntax_error = self.syntax_error)
        else:
            dur = 0
        end = attributes.get('end')
        if end is not None:
            end = parseutil.parsecounter(end, syntax_error = self.syntax_error)
        else:
            end = 0
        self.markers[id] = (begin, dur, end)

    def syntax_error(self, msg):
        if self.__printfunc is None:
            print 'Warning: syntax error in file %s, line %d: %s' % (self.__file, self.lineno, msg)
        else:
            self.__printdata.append('Warning: syntax error on line %d: %s' % (self.lineno, msg))

    def unknown_entityref(self, name):
        pass

    def close(self):
        xmllib.XMLParser.close(self)
        if self.__printfunc is not None and self.__printdata:
            data = string.join(self.__printdata, '\n')
            # first 30 lines should be enough
            data = string.split(data, '\n')
            if len(data) > 30:
                data = data[:30]
                data.append('. . .')
            self.__printfunc(string.join(data, '\n'))
            self.__printdata = []
        self.elements = None
        self.__printdata = None
        self.__printfunc = None

    # the rest is to check that the nesting of elements is done
    # properly
##     def finish_starttag(self, tagname, attrdict, method):
##         if len(self.stack) > 1:
##             ptag = self.stack[-2][2]
##             if tagname not in self.entities.get(ptag, ()):
##                 if not self.entities.get(ptag):
##                     # missing close tag of empty element, just remove the entry from the stack
##                     del self.stack[-2]
##                 else:
##                     self.syntax_error('%s element not allowed inside %s' % (self.stack[-1][0], self.stack[-2][0]))
##         elif tagname != self.topelement:
##             self.syntax_error('outermost element must be "%s"' % self.topelement)
##         xmllib.XMLParser.finish_starttag(self, tagname, attrdict, method)

    def finish_starttag(self, tagname, attrdict, method):
        nstag = tagname.split(' ')
        if len(nstag) != 2 or nstag[0] != 'http://www.w3.org/2001/Note/xmmf':
            self.syntax_error("no or unrecognized namespace for element `%s'" % nstag[-1])
            return
        ns, tagname = nstag
        d = {}
        for key, val in attrdict.items():
            nstag = key.split(' ')
            if len(nstag) == 2 and nstag[0] != 'http://www.w3.org/2001/Note/xmmf':
                self.syntax_error("unrecognized namespace for attribute `%s' in element `%s'" % (nstag[-1], tagname))
                continue
            key = nstag[-1]
            if d.has_key(key):
                self.syntax_error("attribute `%s' occurs with and without namespace qualifier" % key)
            else:
                d[key] = val
        attrdict = d

        if len(self.stack) > 1:
            ptag = self.stack[-2][2]
            nstag = ptag.split(' ')
            if len(nstag) == 2 and nstag[0] == 'http://www.w3.org/2001/Note/xmmf':
                pns, ptag = nstag
            else:
                pns = ''
            if self.entities.has_key(ptag):
                # parent is XMMF entity
                content = self.entities[ptag]
            else:
                content = []
            if tagname in content:
                pass
            else:
                self.syntax_error('%s element not allowed inside %s' % (self.stack[-1][0], self.stack[-2][0]))
        elif tagname != 'xmmf':
            self.error('outermost element must be "xmmf"', self.lineno)
        elif ns and self.getnamespace().get('', '') != ns:
            self.error('outermost element must be "xmmf" with default namespace declaration', self.lineno)
        elif ns and ns != 'http://www.w3.org/2001/Note/xmmf':
            self.syntax_error('default namespace should be "%s"' % 'http://www.w3.org/2001/Note/xmmf', self.lineno)
        if method is None and self.elements.has_key(tagname):
            method = self.elements[tagname][0]
            if ns:
                self.elements[ns + ' ' + tagname] = self.elements[tagname]
        xmllib.XMLParser.finish_starttag(self, tagname, attrdict, method)
