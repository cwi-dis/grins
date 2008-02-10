__version__ = "$Id$"

import MMAttrdefs
import windowinterface
from Hlinks import ANCHOR1, ANCHOR2, DIR_1TO2

class LinkEditLight:
    def __init__(self, toplevel):
        self.toplevel = toplevel
        self.context = toplevel.root.GetContext()
        self.editmgr = toplevel.editmgr
        self.make_interesting()

    def hide(self):
        pass

    def show(self, node = None, aid = None):
        pass

    def is_showing(self):
        return 0

    def fixtitle(self):
        pass

    def destroy(self):
        self.interesting = []
        self.toplevel = None
        self.context = None
        self.editmgr = None

    def make_interesting(self):
        self.interesting = []
        self.__make_interesting(self.toplevel.root)

    def __make_interesting(self, node):
        uid = node.GetUID()
        hlinks = self.context.hyperlinks
        for c in node.GetChildren():
            if c.GetType() == 'anchor':
                if not hlinks.findsrclinks(c):
                    self.interesting.append(c)
            else:
                self.__make_interesting(c)

    def set_interesting(self, anchor):
        self.interesting.append(anchor)

    def has_interesting(self):
        return not not self.interesting

    # Make sure all anchors in 'interesting' actually exist
    def fixinteresting(self):
        findsrclinks = self.context.hyperlinks.findsrclinks
        root = self.toplevel.root
        for anchor in self.interesting[:]:
            if anchor.GetRoot() is not root or findsrclinks(anchor):
                self.interesting.remove(anchor)

    def islinksrc(self, node):
        hlinks = self.context.hyperlinks
        if hlinks.findsrclinks(node): # unlikely...
            return 1
        for c in node.GetChildren():
            if c.GetType() == 'anchor' and hlinks.findsrclinks(c):
                return 1
        return 0

    # Method to return a whole-node anchor for a node, or optionally
    # create one.
    def findwholenodeanchor(self, node):
        for c in node.GetChildren():
            if c.GetType() != 'anchor':
                continue
            if MMAttrdefs.getattr(c, 'ashape') != 'rect':
                # only rectangular anchors can be whole-node anchors
                continue
            if c.GetAttrDef('acoords', None) is not None:
                # no coordinates allowed on whole-node anchors
                continue
            if c.GetAttrDef('beginlist', None) or \
               c.GetAttrDef('endlist', None):
                # no timing allowed on whole-node anchors
                continue
            if MMAttrdefs.getattr(c, 'actuate') != 'onRequest':
                # only user-clickable anchors count
                continue
            return c
        return None

    def wholenodeanchor(self, node, extended = 0, notransaction = 0, create = 1, interesting = 1):
        c = self.findwholenodeanchor(node)
        if c is not None:
            if not create:
                return c
            windowinterface.showmessage("Such an anchor already exists on this node.")
            return None

        if not create:
            return None

        return self.createanchor(node, notransaction, interesting)

    def createanchor(self, node, notransaction = 0, interesting = 1, extended = 0):
        em = self.editmgr
        if not notransaction and not em.transaction():
            return None
        # create the anchor
        anchor = node.GetContext().newnode('anchor')
        # and insert it into the tree
        em.addnode(node, -1, anchor)
        if extended:
            em.setnodeattr(anchor, 'show', 'new')
            em.setnodeattr(anchor, 'sourcePlaystate', 'play')
            if extended == 1:
                em.setnodeattr(anchor, 'sendTo', 'osdefaultbrowser')
            else:
                em.setnodeattr(anchor, 'actuate', 'onLoad')
                em.setnodeattr(anchor, 'external', 1)
                if extended == 2:
                    em.setnodeattr(anchor, 'sendTo', 'rpcontextwin')
                elif extended == 3:
                    em.setnodeattr(anchor, 'sendTo', 'rpbrowser')
        else:
            em.setnodeattr(anchor, 'show', 'replace')
        if not notransaction:
            em.commit()
        if interesting:
            self.interesting.append(anchor)
        return anchor

    def finish_link(self, node, notransaction = 0):
        self.fixinteresting()
        if not self.interesting:
            windowinterface.showmessage('No reasonable sources for link.')
            return
        if len(self.interesting) == 1:
            srcanchor = self.interesting[0]
        else:
            anchors = ['Cancel']
            for a in self.interesting:
                anchors.append(self.makename(a))
            i = windowinterface.multchoice('Choose source anchor',
                      anchors, 0)
            if i == 0:
                return
            srcanchor = self.interesting[i-1]
        em = self.editmgr
        if not notransaction and not em.transaction():
            return
        self.interesting.remove(srcanchor)
        if node in self.interesting: # unlikely...
            self.interesting.remove(node)
        link = srcanchor, node, DIR_1TO2
        em.addlink(link)
        if not notransaction:
            em.commit()

    def makename(self, anchor):
        if type(anchor) is type(''):
            return anchor
        aname = MMAttrdefs.getattr(anchor, 'name')
        if anchor.GetType() == 'anchor':
            nname = MMAttrdefs.getattr(anchor.GetParent(), 'name')
            if nname and aname:
                return '%s in %s' % (aname, nname)
            if nname:
                return 'nameless anchor in %s' % nname
            if not aname:
                return 'nameless anchor in nameless node'
        if aname:
            return aname
        return 'nameless node'
