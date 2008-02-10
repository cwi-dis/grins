__version__ = "$Id$"

# Parser for CWI Multimedia Interchange Files (CMIF, extension .cmif)
# TODO: If you're using anything in here which creates an MMNode,
# please create instead, an EditableMMNode from either editor/EditableObjects.py
# or grins/EditableObjects.py.

from MMExc import *             # Exceptions
from MMTypes import *


from string import letters, digits

# Parser for CMIF files.
# Conceivably subclassing from this class might make sense.
# After initializing the parser once, it is possible to
# use it to get multiple objects from an input source
# by calling the reset() method in between calls to getnode()
# or other get*() methods.  (This resets the scanner except for the
# current line number.)

class MMParser:
    #
    def __init__(self, input, context):
        from tokenize import tokenprog
        self.tokenprog = tokenprog
        import re
        self.lf = re.compile('^[\r\n]*$')
        #
        # 'input' should have a parameterless method readline()
        # which returns the next line, including trailing '\n',
        # or the empty string if there is no more data.
        # An open file will do nicely, as does an instance
        # of StringIO.StringIO.
        #
        self.input = input
        self.lineno = 0
        #
        # 'context' should have a method newnodeuid()
        # which creates a new, empty node.
        # An instance of MMNode.MMNode (or a subclass thereof)
        # will do fine.
        # XXX Better: pass the node-creating function itself!
        #
        self.context = context
        #
        # Initialize the table of attribute parsers.
        # XXX This should become an argument in the future!
        #
        self.attrparsers = {}
##         if context is not None:
##             self.attrparsers = makeattrparsers(MMParser)
##         else:
##             # MMParser called from MMAttrdefs!!!
##             self.attrparsers = {}
        #
        # Reset the scanner interface.
        #
        self.reset()
        #
    #
    def __repr__(self):
        return '<MMParser instance, context=' + `self.context` + '>'
    #
    def reset(self):
        self.nextline = ''
        self.pos = 0
        self.tokstart = 0
        self.eofseen = 0
        self.pushback = None
    #
    # Parse a node.  This is highly recursive.
    #
    def getnode(self):
        self.open()
        type = self.gettoken()
        if type not in alltypes:
            raise MSyntaxError, (type, 'node type')
        uid = self.getuidvalue(None)
        node = self.context.newnodeuid(type, uid)
        self.open()
        attrdict = self.getattrdictvalue(None)
        self.close()
        node.attrdict = attrdict
        if type in interiortypes:
            while self.more():
                child = self.getnode()
                node._addchild(child)
        elif type == 'imm':
            while self.more():
                value = self.getanyvalue(None)
                node._addvalue(value)
        self.close()
        return node
    #
    # Attribute-specific parsers.
    #
    # These raise an exception if the type isn't right.
    # These do NOT eat the next token, even if it is ')'.
    #
    # All must have an argument, even if unused,
    # so they can be passed to others as (func, arg) pair,
    # callable as func(self, arg).
    #
    def getgenericvalue(self, (func, arg)):
        return func(self, arg)
    #
    def getintvalue(self, dummy):
        t = self.getobject()
        if t in ('+', '-'):
            sign = t
            t = self.getobject()
        else:
            sign = ''
        if t[0] in digits:
            if '.' in t or 'e' in t or 'E' in t:
                raise MTypeError, 'int'
            return int(eval(sign + t))
        raise MTypeError, (t, 'int')
    #
    def getfloatvalue(self, dummy):
        t = self.getobject()
        if t in ('+', '-'):
            sign = t
            t = self.getobject()
        else:
            sign = ''
        if t[0] in digits or (t[0] == '.' and t[1] in digits):
            return float(eval(sign + t))
        raise MTypeError, (t, 'float')
    #
    def getstringvalue(self, dummy):
        t = self.getobject()
        if t[0] in ('\'', '"'): return eval(t)
        raise MTypeError, (t, 'string')
    #
    def getnamevalue(self, dummy):
        t = self.getobject()
        if t[0] in letters: return t
        if t[0] in ('\'', '"'): return eval(t)
        raise MTypeError, (t, 'name')
    #
    def getuidvalue(self, dummy):
        t = self.getobject()
        if t[0] in letters or t[0] in digits: return t
        if t[0] in ('\'', '"'): return eval(t)
        raise MTypeError, (t, 'uid')
    #
    def getboolvalue(self, dummy):
        t = self.getobject()
        false = '0', 'n', 'no',  'f', 'off', 'false'
        true  = '1', 'y', 'yes', 't', 'on', 'true'
        if t in false: return 0
        if t in true: return 1
        raise MTypeError, (t, 'bool')
    #
    def getenumvalue(self, list):
        t = self.getobject()
        if t in list: return t
        raise MTypeError, (t, 'enum' + `list`)
    #
    def gettuplevalue(self, funcarglist):
        tuple = ()
        for func, arg in funcarglist:
            v = func(self, arg)
            if v is None and func == self.basicparsers['optenclosed']:
                continue
            tuple = tuple + (v,)
        return tuple
    #
    def getlistvalue(self, (func, arg)):
        list = []
        while self.more():
            v = func(self, arg)
            list.append(v)
        return list
    #
    def getdictvalue(self, (func, arg)):
        dict = {}
        while self.more():
            self.open()
            key = self.getstringvalue(None)
            if dict.has_key(key):
                raise MTypeError, (key, 'duplicate key string')
            dict[key] = func(self, arg)
            self.close()
        return dict
    #
    def getnamedictvalue(self, (func, arg)):
        dict = {}
        while self.more():
            self.open()
            key = self.getnamevalue(None)
            if dict.has_key(key):
                raise MTypeError, (key, 'duplicate key name')
            dict[key] = func(self, arg)
            self.close()
        return dict
    #
    def getattrdictvalue(self, dummy):
        dict = {}
        while self.more():
            key, val = self.getattr()
            if dict.has_key(key):
                raise MTypeError, (key, 'duplicate attr name')
            dict[key] = val
        return dict
    #
    # Subroutine to get a single (attrname, value) pair.
    #
    def getattr(self):
        self.open()
        name = self.gettoken()
        if name[0] not in letters:
            raise MSyntaxError, (name, 'attr name')
        if not self.attrparsers.has_key(name):
            import MMAttrdefs
            if MMAttrdefs.attrdefs.has_key(name):
                self.attrparsers[name] = MMAttrdefs.usetypedef(MMAttrdefs.attrdefs[name][0], MMParser.basicparsers)
            else:
                print 'Warning: unrecognized attr', name
                if name[-4:] == 'dict':
                    # Default syntax for dictionaries
                    value = \
                        self.getnamedictvalue( \
                            (MMParser.getanyvalue, None))
                elif name[-4:] == 'list':
                    # Default syntax for lists
                    value = self.getlistvalue( \
                            (MMParser.getanyvalue, None))
                else:
                    # Default syntax for other things
                    # (returned as lists if more than one item,
                    # else as single value)
                    value = self.getlistvalue( \
                            (MMParser.getanyvalue, None))
                    if len(value) == 1:
                        value = value[0]
        if self.attrparsers.has_key(name):
            func, arg = self.attrparsers[name]
            value = func(self, arg)
        self.close()
        return name, value
    #
# BOGUS! Should reset tokenizer first...
#       def getunionvalue(self, funcarglist):
#               for func, arg in funcarglist:
#                       try:
#                               return func(self, arg)
#                       except MTypeError:
#                               pass
#               raise MTypeError, 'union'
    #
    def getoptenclosedvalue(self, (func, arg)):
        t = self.peektoken()
        if t == '(':
            return self.getenclosedvalue((func, arg))

    def getenclosedvalue(self, (func, arg)):
        self.open()
        v = func(self, arg)
        self.close()
        return v
    #
    def gettypevalue(self, dummy):
        self.open()
        type = self.getnamevalue(None)
        arg = None
        if type == 'int':
            pass
        elif type == 'float':
            pass
        elif type == 'string':
            pass
        elif type == 'name':
            pass
        elif type == 'uid':
            pass
        elif type == 'bool':
            pass
        elif type == 'enum':
            arg = self.getlistvalue((MMParser.getnamevalue, None))
        elif type == 'tuple':
            arg = self.getlistvalue((MMParser.gettypevalue, None))
        elif type == 'list':
            arg = self.gettypevalue(None)
        elif type == 'dict':
            arg = self.gettypevalue(None)
        elif type == 'namedict':
            arg = self.gettypevalue(None)
        elif type == 'attrdict':
            pass
        elif type == 'enclosed':
            arg = self.gettypevalue(None)
        elif type == 'optenclosed':
            arg = self.gettypevalue(None)
        elif type == 'type':
            pass
        elif type == 'any':
            pass
        # XXX union?
        else:
            raise MTypeError, (type, 'type name')
        self.close()
        return type, arg
    #
    def getanyvalue(self, dummy):
        t = self.gettoken()
        if t[0] in letters:
            return t
        if t[0] in digits:
            return eval(t)
        if t == '-':
            t = self.gettoken()
            if not t[0] in digits:
                raise MSyntaxError, ('-'+t, 'value')
            return -eval(t)
        if t[0] == '\'':
            return eval(t)
        if t[0] == '"':
            return eval(t)
        if t[0] == '(':
            value = self.getlistvalue((MMParser.getanyvalue, None))
            self.close()
            return value
        raise MSyntaxError, (t, 'value')
    #
    # Initialize the mapping from type names to type parsers.
    # This is an attribute of the class, not of its instances!
    #
    basicparsers = { \
            'int': getintvalue, \
            'float': getfloatvalue, \
            'string': getstringvalue, \
            'name': getnamevalue, \
            'uid': getuidvalue, \
            'bool': getboolvalue, \
            'enum': getenumvalue, \
            'tuple': gettuplevalue, \
            'list': getlistvalue, \
            'dict': getdictvalue, \
            'namedict': getnamedictvalue, \
            'attrdict': getattrdictvalue, \
            'enclosed': getenclosedvalue, \
            'optenclosed':getoptenclosedvalue, \
            'type': gettypevalue, \
            'any': getanyvalue, \
            }
    #
    # Shorthands for frequently occurring parsing operations
    #
    def getobject(self):
        t = self.gettoken()
        if t in ('(', ')'):
            raise MSyntaxError, (t, 'object')
        return t
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
            raise MSyntaxError, (t, exp)
    #
    def more(self):
        if self.peektoken() == ')':
            return 0
        else:
            return 1
    #
    def peektoken(self):
        if self.pushback is None:
            self.pushback = self.getnexttoken()
        return self.pushback
    #
    def gettoken(self):
        if self.pushback is not None:
            token = self.pushback
            self.pushback = None
        else:
            token = self.getnexttoken()
        #print '#gettoken', token
        if token == '':
            raise EOFError
        return token
    #
    def ungettoken(self, token):
        if self.pushback is not None:
            raise AssertError, 'more than one ungettoken'
        # print 'pushback:', token
        self.pushback = token
    #
    # The real work of getting a token is done here.
    # This is the first place place to look if you think
    # the parser is too slow.
    #
    def getnexttoken(self):
        while 1:
            while 1:
                res = self.tokenprog.match(self.nextline, self.pos)
                if res is not None:
                    break
                #
                # End of line hit
                #
                if self.eofseen:
                    self.nextline = ''
                else:
                    self.nextline = self.input.readline()
                self.pos = self.tokstart = 0
                if not self.nextline:
                    if self.eofseen:
                        raise EOFError
                    self.eofseen = 1
                    return ''
                self.lineno = self.lineno + 1
                #
                # Read continuation lines if any
                #
                while self.nextline[-2:] == '\\\n':
                    self.nextline = self.nextline[:-2]
                    cont = self.input.readline()
                    if not cont:
                        break
                    self.nextline = self.nextline + cont
                    self.lineno = self.lineno + 1
                    if len(cont) < 2:
                        break
            #
            # Found a token
            #
            self.tokstart, self.pos = res.regs[3]
            token = self.nextline[self.tokstart:self.pos]
            if not self.lf.match(token): return token
    #
    # Default error handlers.
    #
    def reporterror(self, filename, message, fp):
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
            if i >= self.tokstart:
                n = max(1, self.pos - i)
                fp.write('^'*n)
                break
            elif line[i] == '\t':
                fp.write('\t')
            elif ' ' <= line[i] < '\177':
                fp.write(' ')
        fp.write('\n')
    #


# Create a table of attribute parsers using the given parser class.
# In the future this will be done based upon a description of the
# attributes read from a file.

def makeattrparsers(cl):
    import MMAttrdefs
    return MMAttrdefs.useattrdefs(cl.basicparsers)


# Parse a value from a string using a given typedef

def parsevalue(string, typedef, context):
    import MMAttrdefs
    import StringIO
    fp = StringIO.StringIO(string)
    parser = MMParser(fp, context)
    parserdef = MMAttrdefs.usetypedef(typedef, MMParser.basicparsers)
    value = parser.getgenericvalue(parserdef)
    if parser.peektoken() <> '':
        raise MSyntaxError, 'excess input'
    return value


# Test driver for tokenizer
#
if __debug__:
    def testtokenizer():
        import sys
        p = MMParser(sys.stdin)
        try:
            while 1: p.gettoken()
        except EOFError:
            print 'EOF'
        except MSyntaxError, msg:
            p.reporterror('<stdin>', 'Syntax error: ' + msg, sys.stderr)


# Test driver for parser
#
if __debug__:
    def testparser():
        import sys
        import MMNode
        context = MMNode.MMNodeContext(MMNode.MMNode)
        p = MMParser(sys.stdin, context)
        try:
            x = p.getnode()
        except EOFError:
            print 'unexpected EOF at line', p.lineno
            return
        except MSyntaxError, msg:
            if type(msg) is type(()):
                gotten, expected = msg
                msg = 'got ' + `gotten` + ', expected ' + `expected`
            p.reporterror('<stdin>', 'Syntax error: ' + msg, sys.stderr)
            return
        import MMWrite
        MMWrite.WriteOpenFile(x, sys.stdout)
