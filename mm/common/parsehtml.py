__version__ = "$Id$"

from sgmllib import SGMLParser
import sys
import string

class Parser(SGMLParser):
    # empty elements
    __emptytags = ['area', 'base', 'basefont', 'br', 'col', 'frame', 'hr',
                   'img', 'input', 'isindex', 'link', 'meta', 'param']

    # some abbreviations
    __heading = ('h1', 'h2', 'h3', 'h4', 'h5', 'h6')
    __list = ('ul', 'ol', 'dir', 'menu')
    __preformatted = ('pre',)
    __block = ('p', 'dl', 'div', 'noscript', 'blockquote',
               'form', 'hr', 'table', 'fieldset', 'address') + \
               __heading + __list + __preformatted
    __fontstyle = ('tt', 'i', 'b', 'big', 'small')
    __phrase = ('em', 'strong', 'dfn', 'code', 'samp', 'kbd', 'var',
                'cite', 'abbr', 'acronym')
    __special = ('a', 'img', 'object', 'br', 'script', 'map', 'q', 'sub',
                 'sup', 'span', 'bdo')
    __formctrl = ('input', 'select', 'textarea', 'label', 'button')
    __inline = __fontstyle + __phrase + __special + __formctrl
    __flow = __block + __inline
    __html_content = ('head', 'body')
    __head_content = ('title', 'base')
    __head_misc = ('script', 'style', 'meta', 'link', 'object')
    __tr = ('tr',)

    # elements with optional endtags and their allowed contents
    __optionalend = {'body': __block + ('script', 'ins', 'del'),
                     'colgroup': ('col',),
                     'dd': __flow,
                     'dt': __inline,
                     'head': __head_content + __head_misc,
                     'html': __html_content,
                     'li': __flow,
                     'option': (),
                     'p': __inline,
                     'tbody': __tr,
                     'td': __flow,
                     'tfoot': __tr,
                     'th': __flow,
                     'thead': __tr,
                     'tr': ('th', 'td'),
                     }

    def __init__(self, iddict = []):
        SGMLParser.__init__(self, 0)
        self.__iddict = iddict

    def reset(self):
        SGMLParser.reset(self)
        self.__data = []
        self.__stack = []

    def handle_data(self, data):
        self.__data.append(data)

    def unknown_starttag(self, tag, attrs):
        while self.__stack and \
              self.__optionalend.has_key(self.__stack[-1]):
            if tag in self.__optionalend[self.__stack[-1]]:
                break
            else:
                self.unknown_endtag(self.__stack[-1])
        id = None
        name = None
        for i in range(len(attrs)-1, -1, -1):
            a, v = attrs[i]
            if (a == 'id' or (tag == 'a' and a == 'name')) and \
               self.__iddict.has_key(v):
                del attrs[i]
                if tag == 'a':
                    for j in range(len(attrs)):
                        if attrs[j][0] == 'href':
                            del attrs[j]
                            break
                    attrs.append(('href', 'cmif:%s'%self.__iddict[v]))
                else:
                    id = self.__iddict[v]
                break
            elif a == 'id':
                del attrs[i]
                name = v
        attrlist = ['<' + tag]
        for (a, v) in attrs:
            v = string.join(string.split(v, '"'), '&quot;')
            attrlist.append('%s="%s"' % (a, v))
        self.__data.append(string.join(attrlist))
        self.__data.append('>')
        if tag not in self.__emptytags:
            self.__stack.append(tag)
        if id:
            self.__data.append('<a href="cmif:%s"'%id)
            if name:
                self.__data.append(' name="%s"'%name)
            self.__data.append('>')
            self.__stack.append('a')
        elif name:
            self.__data.append('<a name="%s"> </a>'%name)

    def unknown_endtag(self, tag):
        while self.__stack and self.__stack[-1] != tag:
            self.__data.append('</%s>' % self.__stack[-1])
            del self.__stack[-1]
        self.__data.append('</%s>'%tag)
        if self.__stack and self.__stack[-1] == tag:
            del self.__stack[-1]

    def close(self):
        SGMLParser.close(self)
        return string.join(self.__data, '')

if __debug__:
    def test():
        import sys

        args = sys.argv[1:]
        if args:
            file = args[0]
        else:
            file = '-'
        if file == '-':
            f = sys.stdin
        else:
            f = open(file)
        data = f.read()
        x = Parser()
        x.feed(data)
        print x.close()

    if __name__ == '__main__':
        test()
