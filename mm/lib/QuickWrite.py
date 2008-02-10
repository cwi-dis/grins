__version__ = "$Id$"

import marshal
import MMNode

class QuickWriter:
    def __init__(self, node, fp):
        self.__root = node
        self.__ctx = node.GetContext()
        self.__fp = fp
        self.writeusergroups()
        self.writeregpoints()
        self.writelayout()
        self.writetransitions()
        self.writenode(node)
        self.writelinks()

    def writeusergroups(self):
        marshal.dump(self.__ctx.usergroups, self.__fp)

    def writeregpoints(self):
        regpoints = self.__ctx.regpoints
        marshal.dump(len(regpoints), self.__fp)
        for name, r in regpoints.items():
            marshal.dump((name, r.isdef, r.attrdict), self.__fp)

    def writelayout(self):
        viewports = self.__ctx.getviewports()
        marshal.dump(len(viewports), self.__fp)
        for v in viewports:
            marshal.dump(v.name, self.__fp)
            marshal.dump(v.attrdict, self.__fp)
            self.writeregions(v)

    def writeregions(self, ch):
        regions = []
        for r in ch.GetChildren():
            if r['type'] == 'layout':
                regions.append(r)
        marshal.dump(len(regions), self.__fp)
        for r in regions:
            marshal.dump(r.name, self.__fp)
            marshal.dump(r.attrdict, self.__fp)
            self.writeregions(r)

    def writetransitions(self):
        marshal.dump(self.__ctx.transitions, self.__fp)

    def fixsynclist(self, list):
        nlist = []
        for arc in list:
            if arc.isstart:
                action = 'begin'
            elif arc.ismin:
                action = 'min'
            elif arc.isdur:
                action = 'dur'
            else:
                action = 'end'
            src = arc.srcnode
            if isinstance(src, MMNode.MMNode):
                src = '#' + src.GetUID()
            chan = arc.channel
            if chan is not None:
                chan = chan.name
            nlist.append((action, src, chan, arc.event, arc.marker, arc.wallclock, arc.accesskey, arc.delay))
        return nlist

    def writenode(self, node):
        children = node.GetChildren()
        if hasattr(node, 'min_pxl_per_sec'):
            min_pxl_per_sec = node.min_pxl_per_sec
        else:
            min_pxl_per_sec = None
        marshal.dump((node.GetType(), node.GetUID(), node.GetValues(), node.collapsed, node.showtime, min_pxl_per_sec, len(children)), self.__fp)
        attrdict = node.attrdict.copy()
        beginlist = attrdict.get('beginlist')
        endlist = attrdict.get('endlist')
        if beginlist is not None:
            attrdict['beginlist'] = self.fixsynclist(beginlist)
        if endlist is not None:
            attrdict['endlist'] = self.fixsynclist(endlist)
        marshal.dump(attrdict, self.__fp)
        for c in children:
            self.writenode(c)

    def writelinks(self):
        links = []
        for a1, a2, dir in self.__ctx.hyperlinks.getall():
            if type(a1) is not type(''):
                a1 = '#' + a1.GetUID()
            if type(a2) is not type(''):
                a2 = '#' + a2.GetUID()
            links.append((a1, a2, dir))
        marshal.dump(links, self.__fp)

def WriteFile(root, filename):
    fp = open(filename, 'wb')
    q = QuickWriter(root, fp)
    fp.close()
