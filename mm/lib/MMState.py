from lxml import etree
import MMurl
import StringIO
import settings

class error(Exception):
    pass

class MMState:
    def __audioDesc(self, dummy):
        return settings.get('system_audiodesc') == 1

    def __bitrate(self, dummy):
        return settings.get('system_bitrate')

    def __captions(self, dummy):
        return settings.get('system_captions') == 1

    def __component(self, dummy, url):
        return url in settings.components

    def __customTest(self, dummy, name):
        val = self.__context.usergroups.get(name)
        if val is not None and val[1] != 'RENDERED':
            return False
        return True

    def __CPU(self, dummy):
        return settings.get('system_cpu')

    def __language(self, dummy, lang):
        return settings.match('system_language', lang)

    def __operatingSystem(self, dummy):
        return settings.get('system_operating_system')

    def __overdubOrSubtitle(self, dummy):
        return settings.get('system_overdub_or_caption')

    def __required(self, dummy, url):
        return settings.match('system_required', [url])

    def __screenDepth(self, dummy):
        return settings.get('system_screen_depth')

    def __screenHeight(self, dummy):
        return settings.get('system_screen_size')[1]

    def __screenWidth(self, dummy):
        return settings.get('system_screen_size')[0]

    def __init__(self, context, inline = None, url = None):
        self.__context = context
        self.__url = url
        self.__inline = inline
        ns = etree.FunctionNamespace(None)
        ns['smil-audioDesc'] = self.__audioDesc
        ns['smil-bitrate'] = self.__bitrate
        ns['smil-captions'] = self.__captions
        ns['smil-component'] = self.__component
        ns['smil-customTest'] = self.__customTest
        ns['smil-CPU'] = self.__CPU
        ns['smil-language'] = self.__language
        ns['smil-operatingSystem'] = self.__operatingSystem
        ns['smil-overdubOrSubtitle'] = self.__overdubOrSubtitle
        ns['smil-required'] = self.__required
        ns['smil-screenDepth'] = self.__screenDepth
        ns['smil-screenHeight'] = self.__screenHeight
        ns['smil-screenWidth'] = self.__screenWidth

    def start(self):
        self.__tree = None
        if self.__url:
            try:
                f = open(MMurl.urlretrieve(url)[0], 'r')
            except:
                pass
            else:
                try:
                    self.__tree = etree.parse(f)
                except:
                    self.__tree = None
                f.close()
        if self.__tree is None and self.__inline:
            try:
                self.__tree = etree.parse(StringIO.StringIO(self.__inline))
            except:
                self.__tree = None
        if self.__tree is None:
            self.__tree = etree.parse(StringIO.StringIO('<data/>'))

    def expr(self, expression):
        try:
            r = self.__tree.xpath(expression)
        except:
            return None
        if r == True:
            return True
        if r == False:
            return False
        return None

    def interpolate(self, s):
        new = []
        i = s.find('{')
        while i >= 0:
            new.append(s[:i])
            expr = []
            braces = 0
            for c in s[i+1:]:
                if c == '{':
                    braces = braces + 1
                elif c == '}':
                    braces = braces - 1
                    if braces < 0:
                        break
                expr.append(c)
            expr = ''.join(expr)
            try:
                v = self.__tree.xpath(expr)
            except:
                v = '{%s}' % expr
            if type(v) is type([]) and len(v) == 1:
                v = v[0].text
            if type(v) not in (type(''), type(u''), type(0), type(0.0)):
                raise error, "value attribute must evaluate to a string"
            new.append(str(v))
            s = s[i+len(expr)+2:]
            i = s.find('{')
        new.append(s)
        return ''.join(new)
        
    def setvalue(self, ref, value):
        try:
            e = self.__tree.xpath(ref)
        except:
            e = []                      # trigger below error
        if len(e) != 1:
            raise error, "ref attribute must evaluate to a single node"
        e = e[0]
        try:
            v = self.__tree.xpath(value)
        except:
            v = ()                      # trigger below error
        if type(v) not in (type(''), type(u''), type(0), type(0.0)):
            raise error, "value attribute must evaluate to a string"
        e.text = str(v)
        return e

    def newvalue(self, ref, where, name, value):
        try:
            e = self.__tree.xpath(ref)
        except:
            e = []                      # trigger below error
        if len(e) != 1:
            raise error, "ref attribute must evaluate to a single node"
        e = e[0]
        try:
            v = self.__tree.xpath(value)
        except:
            v = ()                      # trigger below error
        if type(v) not in (type(''), type(u''), type(0), type(0.0)):
            raise error, "value attribute must evaluate to a string"
        n = etree.Element(name)
        n.text = str(v)
        p = e.getparent()
        if where == 'child':
            e.append(n)
        else:
            i = 0
            while p[i] is not e:
                i = i + 1
            if where == 'before':
                p.insert(i, n)
            else:
                p.insert(i + 1, n)
        return e

    def delvalue(self, ref):
        try:
            e = self.__tree.xpath(ref)
        except:
            e = []                      # trigger below error
        if len(e) != 1:
            raise error, "ref attribute must evaluate to a single node"
        e = e[0]
        p = e.getparent()
        p.remove(e)
        return p

    def send(self, ref, action, method, replace, target):
##         import windowinterface
##         windowinterface.showmessage('send not yet implemented', mtype = 'warning')
##         return

        if not action:
            raise error, "no action"
        action = MMurl.basejoin(self.__context.baseurl, action)
        if method == 'put' or method == 'post':
            try:
                e = self.__tree.xpath(ref or '/*')
            except:
                e = []                  # trigger below error
            if len(e) != 1:
                raise error, "ref attribute must evaluate to a single node"
            e = e[0]
            data = etree.tostring(e, pretty_print = True)
            fp = MMurl.urlopen(action, data, method.upper())
        else:
            fp = MMurl.urlopen(action)
        newdata = fp.read()
        fp.close()
        if method == 'put':
            # not replacing anything
            return

        if replace == 'instance':
            if target is not None:
                try:
                    e = self.__tree.xpath(target)
                except:
                    e = []              # trigger below error
                if len(e) != 1:
                    raise error, "ref attribute must evaluate to a single node"
                e = e[0]
            else:
                e = self.__tree.xpath('/*')[0]
        elif replace == 'all':
            e = self.__tree.xpath('/*')[0]
        else:
            e = None
        if e is not None:
            tree = etree.parse(StringIO(newdata))
            p = e.getparent()
            if p is None:
                # root node: replace whole instance
                self.__tree = tree
            else:
                i = p.index(e)
                del p[i]
                p.insert(i, tree)

    def matches(self, ref, node):
        print ref, node
        try:
            e = self.__tree.xpath(ref)
        except:
            print 'False'
            return False
        print e
        return node in e
