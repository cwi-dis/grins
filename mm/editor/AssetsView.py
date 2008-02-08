__version__ = "$Id$"

from AssetsViewDialog import AssetsViewDialog
from ViewDialog import ViewDialog
from usercmd import *
import MMNode
from MMTypes import *
import MMAttrdefs
import MMurl
import urlparse
import posixpath
import string
import usercmd
import windowinterface

class AssetsView(AssetsViewDialog, ViewDialog):
    COLUMNLIST={
            'all':[
                    ('left', 120, 'Name'),
                    ('left', 70, 'Type'),
                    ('right', 50, 'Used'),
                    ('left', 200, 'URL'),
            ],
            'template':[
                    ('left', 120, 'Name'),
                    ('left', 70, 'Type'),
                    ('left', 200, 'URL'),
            ],
            'clipboard':[
                    ('left', 120, 'Name'),
                    ('left', 70, 'Type'),
            ],
    }

    def __init__(self, toplevel):
        self.toplevel = toplevel
        self.root = toplevel.root
        self.context = self.root.context
        self.editmgr = self.context.editmgr
        self.whichview = 'template'
        AssetsViewDialog.__init__(self)

    def fixtitle(self):
        pass

    def destroy(self):
        self.hide()
        AssetsViewDialog.destroy(self)

    def show(self):
        if self.is_showing():
            AssetsViewDialog.show(self)
            return
        AssetsViewDialog.show(self)
        self.editmgr.register(self, want_clipboard=1)
        self.setview(self.whichview)

    def hide(self):
        if not self.is_showing():
            return
        self.editmgr.unregister(self)
        AssetsViewDialog.hide(self)

    def transaction(self,type):
        return 1                # It's always OK to start a transaction

    def rollback(self):
        pass

    def commit(self, type=None):
        # This isn't really needed always, but who cares.
        self.setview(self.whichview)

    def clipboardchanged(self):
        self.setview(self.whichview)

    def kill(self):
        self.destroy()

    def setview(self, which):
        self.whichview = which
        self.setviewbutton(which)
        self.setlistheaders(self.COLUMNLIST[which])
        if which == 'all':
            self.listdata = self.getallassets()
            cmdlist = []
        elif which == 'template':
            self.listdata = self.gettemplateassets()
            cmdlist = [
                    usercmd.CUT(callback=(self.callback_cut, ())),
                    usercmd.COPY(callback=(self.callback_copy, ())),
                    usercmd.PASTE(callback=(self.callback_paste, ())),
                    usercmd.DELETE(callback=(self.callback_delete, ())),
            ]
        else:
            self.listdata = self.getclipboard()
            cmdlist = []
        # Sort
        list = map(lambda x: (x[2],) + x, self.listdata)
        list.sort()
        self.listdata = map(lambda x:x[1:], list)
        # Remove first field
        listdata = map(lambda x:x[1:], self.listdata)
        self.setlistdata(listdata)
        self.setcommandlist(cmdlist)

    def callback_cut(self):
        i = self.getselection()
        if i < 0:
            print "No selection"
            return
        item = self.listdata[i][0]
        if not self.editmgr.transaction():
            print "No transaction"
            return
        self.editmgr.delasset(item)
        self.editmgr.setclip([item])
        self.editmgr.commit()

    def callback_paste(self):
        data = self.editmgr.getclip()
        if not type(data) in (type(()), type([])):
            print 'cannot paste', (tp, data)
            return
        for d in data:
            if not hasattr(d, 'getClassName'):
                print 'Focus items should have getClassName() method'
                return
            if not d.getClassName() == 'MMNode':
                print 'cannot paste', (tp, data)
                return

        if not self.editmgr.transaction():
            print 'No transaction'
            return
        data = self.editmgr.getclipcopy()
        for node in data:
            self.editmgr.addasset(node)
        self.editmgr.commit()

    def callback_copy(self):
        i = self.getselection()
        if i < 0:
            print "No selection"
            return
        item = self.listdata[i][0]
        if not self.editmgr.transaction():
            print 'No transaction'
            return
        self.editmgr.setclip([item])
        self.editmgr.commit()

    def callback_delete(self):
        i = self.getselection()
        if i < 0:
            print "No selection"
            return
        item = self.listdata[i][0]
        if not self.editmgr.transaction():
            print "No transaction"
            return
        self.editmgr.delasset(item)
        self.editmgr.commit()
        # XXX item.Destroy() ???

    def startdrag_callback(self, index):
        if self.whichview == 'clipboard':
            return 0
        if index < 0 or index > len(self.listdata):
            windowinterface.beep()
            return 0
        if self.whichview == 'all':
            url = self.listdata[index][5]
            action = self.dodragdrop('URL', url)
            # We don't remove URLs from the all media view
            return 1
        if self.whichview == 'template':
            iteminfo = self.listdata[index][0]
            if type(iteminfo) == type(''):
                # String means it's a url
                value = self.listdata[index][4]
                tp = 'URL'
            elif hasattr(iteminfo, 'getClassName') and iteminfo.getClassName() == 'MMNode':
                value = iteminfo
                tp = 'NodeUID'
            else:
                windowinterface.beep()
                return 0
##             print 'AssetsView.dodragdrop', tp, value
            action = self.dodragdrop(tp, value)
##             print 'AssetsView.dodragdrop ->', action
            if action == 'move':
                # We should remove the item
##                 print 'AssetView: Removing item', index
                item = self.listdata[index][0]
                if not self.editmgr.transaction():
                    print "No transaction"
                    return 0
                self.editmgr.delasset(item)
                self.editmgr.commit()
            elif action == 'copy' and tp == 'NodeUID':
##                 print 'AssetView: duplicating item', index
                item = self.listdata[index][0]
                newitem = item.DeepCopy()
                if not self.editmgr.transaction():
                    print "No transaction"
                    newitem.Destroy()
                    return 0
                self.editmgr.delasset(item)
                self.editmgr.addasset(newitem)
                self.editmgr.commit()
            # Otherwise there's nothing to do for us.
            return 1
        print 'Unknown self.whichview', self.whichview
        return None, None

    def gettemplateassets(self):
        assetlist = []
        for node in self.context.getassets():
            # XXX Logic is suboptimal: we consider all ext
            # nodes without ids and with URLs as pure media items,
            # all others as clippings.
            tp = node.GetType()
            if tp == 'ext':
                url = node.GetRawAttrDef('file', '')
            else:
                url = ''
            name = MMAttrdefs.getattr(node, 'name')
            icon = node.getIconName(wantmedia=1)
            if tp == 'ext' and url and not name:
                pathname = urlparse.urlparse(url)[2]
                name = posixpath.split(pathname)[1]
                name = MMurl.unquote(name)
                node = icon # XXXX dirty trick: string first elt flags url.
            else:
                pathname = ''
            assetlist.append((node, icon, name, icon, url))
        return assetlist

    def getallassets(self):
        assetdict = {}
        # First add the template assets
        for node in self.context.getassets():
            if node.getClassName() == 'MMNode':
                self._getallassetstree(node, assetdict, intree=0)
        # and now add the used assets
        self._getallassetstree(self.root, assetdict)
        assetlist = []
        # For now we ignore the nodes
        for url, v in assetdict.items():
            mimetype, nodelist = v
            pathname = urlparse.urlparse(url)[2]
            shortname = posixpath.split(pathname)[1]
            assetlist.append((nodelist, mimetype, shortname, mimetype, `len(nodelist)`, url))
        return assetlist

    def _getallassetstree(self, node, dict, intree=1):
        rv = []
        tp = node.GetType()
        if tp == 'ext':
            url = node.GetRawAttrDef('file','')
            if url:
                mimetype = node.getIconName(wantmedia=1)
                if intree:
                    if dict.has_key(url):
                        mimetype, nodelist = dict[url]
                        nodelist.append(node)
                    else:
                        dict[url] = mimetype, [node]
                else:
                    # Not in tree, so we're picking up from the
                    # template assests list. Don't store the nodes.
                    if not dict.has_key(url):
                        dict[url] = mimetype, []
        if tp in interiortypes:
            for ch in node.GetChildren():
                self._getallassetstree(ch, dict)

    def getclipboard(self):
        data = self.editmgr.getclip()
        rv = []
        for n in data:
            className = n.getClassName()
            iconname = n.getIconName(wantmedia=1)
            if className == 'MMNode':
                name = MMAttrdefs.getattr(n, 'name')
            elif className in ('Region','Viewport'):
                name = n.name
            else:
                name = ''
            rv.append((None, iconname, name, iconname))

        return rv

    # Callbacks from the UI
    def setview_callback(self, which):
        self.setview(which)

    def select_callback(self, number):
        if self.whichview == 'all':
            self._showselection(number)

    def _showselection(self, number):
        # Tell other views about our selection
        if number < 0 or number > len(self.listdata):
            return # Do nothing. XXXX Or deselect??
        nodelist = self.listdata[number][0]
        self.editmgr.setglobalfocus(nodelist)

    def sort_callback(self, column):
        print 'sort', column

    # drag/drop destination callbacks
    def dragitem(self, x, y, flavor, object):
        if self.whichview != 'template':
            return None
        if flavor in ('FileName', 'URL'):
            return 'link'
        if flavor == 'NodeUID':
            contextid, nodeuid = object
            if contextid != id(self.context):
                return None
            return 'copy'
##         if flavor == 'Region':
##             return 'copy'
        return None

    def dropitem(self, x, y, flavor, object):
        if self.whichview != 'template':
            return None
        if flavor == 'FileName':
            object = MMurl.pathname2url(object)
            flavor = 'URL'
        if flavor == 'URL':
            url = self.context.relativeurl(object)
            node = self.context.newnode('ext')
            node.SetAttr('file', url)
        if flavor == 'NodeUID':
            contextid, nodeuid = object
            if contextid != id(self.context):
                return None
            node = self.context.mapuid(nodeuid)
            node = node.DeepCopy()
        # Put it in the asset container
        if not self.editmgr.transaction():
            print 'No transaction'
            node.Destroy()
            return None
        self.editmgr.addasset(node)
        self.editmgr.commit()
        return 'copy'
