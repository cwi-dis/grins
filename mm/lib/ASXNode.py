__version__ = "$Id$"

from MMExc import *

class ASXNode:
    def __init__(self, type):
        # ASSERT type in alltypes
        self.type = type
        self.attrdict = {}
        self.parent = None
        self.children = []
        self.data = ''

    #
    # Friends-private methods to build a tree
    #
    def _addchild(self, child):
        # ASSERT self.type in interiortypes
        child.parent = self
        self.children.append(child)

    def _setattr(self, name, value):
        # ASSERT not self.attrdict.has_key(name)
        self.attrdict[name] = value

    def _add_data(self, data):
        # ASSERT self.type accepts data
        import string
        data = string.join(data.split('\r\n'), ' ')
        data = string.join(data.split('\r'), ' ')
        data = string.join(data.split('\t'), ' ')
        l = data.split(' ')
        for s in l:
            if s: self.data = self.data + ' ' + s

    #
    # Public methods for read-only access
    #
    def GetType(self):
        return self.type

    def GetParent(self):
        return self.parent

    def GetRoot(self):
        root = None
        x = self
        while x is not None:
            root = x
            x = x.parent
        return root

    def GetPath(self):
        # return inclusive path from root to self (in that order)
        path = []
        x = self
        while x is not None:
            path.append(x)
            x = x.parent
        path.reverse()
        return path

    def IsAncestorOf(self, x):
        while x is not None:
            if self is x: return 1
            x = x.parent
        return 0

    def CommonAncestor(self, x):
        p1 = self.GetPath()
        p2 = x.GetPath()
        n = min(len(p1), len(p2))
        i = 0
        while i < n and p1[i] == p2[i]: i = i+1
        if i == 0: return None
        else: return p1[i-1]

    def GetChildren(self):
        return self.children

    def GetChild(self, i):
        return self.children[i]

    def GetChildrenOfType(self, type):
        children = []
        for node in self.children:
            if node.GetType() == type:
                children.append(node)
        return children

    def GetChildOfType(self, type):
        for node in self.children:
            if node.GetType() == type:
                return node
        return None

    def GetData(self):
        return self.data

    def GetAttrDict(self):
        return self.attrdict

    def GetAttr(self, name):
        if self.attrdict.has_key(name):
            return self.attrdict[name]
        raise NoSuchAttrError, 'in GetAttr'

    def GetAttrDef(self, name, default):
        return self.attrdict.get(name, default)

    def GetInherAttr(self, name):
        x = self
        while x is not None:
            if x.attrdict and x.attrdict.has_key(name):
                return x.attrdict[name]
            x = x.parent
        raise NoSuchAttrError, 'in GetInherAttr()'

    def GetDefInherAttr(self, name):
        x = self.parent
        while x is not None:
            if x.attrdict and x.attrdict.has_key(name):
                return x.attrdict[name]
            x = x.parent
        raise NoSuchAttrError, 'in GetInherDefAttr()'

    def GetInherAttrDef(self, name, default):
        x = self
        while x is not None:
            if x.attrdict and x.attrdict.has_key(name):
                return x.attrdict[name]
            x = x.parent
        return default

    def GetASXInfo(self):
        infodict = {
                'title':'',
                'author':'',
                'copyright':'',
                'abstract': '',
                }
        for t in infodict.keys():
            cnode = self.GetChildOfType(t)
            if cnode: infodict[t] = cnode.GetData()
        infodict['banner'] = self.GetChildOfType('banner')
        infodict['moreinfo'] = ''
        n = self.GetChildOfType('moreinfo')
        if n: infodict['moreinfo'] = n.GetAttr('href')
        return infodict

    def Dump(self):
        print '*** Dump of', self.type, 'node', self, '***'
        attrnames = self.attrdict.keys()
        attrnames.sort()
        for name in attrnames:
            print 'Attr', name + ':', `self.attrdict[name]`
        if self.data:
            print self.GetType(), ': ', self.data
        if self.children:
            print 'Children:',
            for child in self.children:
                print child.GetType(),
            print
            for child in self.children:
                child.Dump()
