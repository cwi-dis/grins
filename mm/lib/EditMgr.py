__version__ = "$Id$"

# Edit Manager.
# Amazing as it may seem, this module is not dependent on window software!

# Edit manager interface -

## The edit manager is responsible for taking and recording changes made
## by different parts of the system in a fashion that allows undo's,
## redo's and safe changes to the MMNode (and other) structures.

## It works (currently) as follows:
##     * A specific view wants to make a change to the structure. em
##     is an instance of the editmanager.
##     * That view calls em.transaction() to tell everybody in
##     em.registry that it wants an exclusive lock on making changes.
##     * The view does it's stuff to the data structures through calls
##     to methods of em.
##     * the view calls em.commit(). commit will record the changes
##     and let all views know that the document has changed.

## A better scheme would be as follows:
##        - The edit manager solely records changes to models.
##     - When undoing, the edit manager blindly interprets the
##     transaction list to undo the changes made to objects.
##     - Each model has an interface for calls from the edit
##     manager, views and controllers.

##     When a view wants to make a change:
##        1) A controller calls a change() method on a certain Model.
##     2) The model sets a lock on itself or it's container (if multitasking)
##     3) The model records the change with the edit manager.
##     4) The model makes the change to itself or it's parent.
##     5) The model tells all of it's views that it has changed.
##     6) The model releases the lock and returns.

##     In this case, the Edit manager would be more of a transaction
##     manager, that records a list of undoable transactions to the
##     document.


import MMExc
from Owner import *
import features
import Clipboard

class EditMgr(Clipboard.Clipboard):
    #
    # Initialization.
    #
    def __init__(self, toplevel):
        self.reset()
        self.toplevel = toplevel
        Clipboard.Clipboard.__init__(self)

    def setRoot(self, root):
        self.root = root
        self.context = self.root.context

    def __repr__(self):
        return '<EditMgr instance, context=' + `self.context` + '>'

    def reset(self):
        self.root = self.context = None
        self.busy = 0
        self.history = []
        self.future = []
        self.registry = []
        self.focus_registry = []
        self.focus = []         # the focus is always a list of items
        self.focus_busy = 0

        self.playerstate_registry = []
        self.playerstate = None, None
        self.playerstate_busy = 0

        # These variables are optimisations in the HierarchyView. When a node is changed
        # here, the HierarchyView can decide whether to redraw itself.
        # These are cascading variables - the higher variables override the lower variables.
        self.structure_changed = 0 # Has the structure of the nodes changed?
        self.attrs_changed = 0  # Or maybe only the structure of the nodes.

        self.clipboard_registry = []

        # if the context is changed there are some special treatment to do during commit
        self.__newRoot = None
        self.__errorstateChanged = 0

    def destroy(self):
        for x in self.registry[:]:
            x.kill()
        self.reset()

    def __delete(self, list):
        # hook to delete (destroy) instances in list
        for trans in list:
            for action in trans:
                cmd = action[0]
                func = getattr(self, 'clean_'+cmd)
                apply(func, action[1:])
    #
    # Dependent client interface.
    #
    def register(self, x, want_focus=0, want_playerstate=0, want_clipboard=0):
        self.registry.append(x)
        if want_focus:
            self.focus_registry.append(x)
        if want_playerstate:
            self.playerstate_registry.append(x)
        if want_clipboard:
            self.clipboard_registry.append(x)

    def registerfirst(self, x, want_focus=0, want_playerstate=0, want_clipboard=0):
        self.registry.insert(0, x)
        if want_focus:
            self.focus_registry.insert(0, x)
        if want_playerstate:
            self.playerstate_registry.insert(0, x)
        if want_clipboard:
            self.clipboard_registry.insert(0, x)

    def unregister(self, x):
        for i in range(len(self.registry)):
            if self.registry[i] is x:
                del self.registry[i]
                break
##         self.registry.remove(x)
        if x in self.focus_registry:
            self.focus_registry.remove(x)
        if x in self.playerstate_registry:
            self.playerstate_registry.remove(x)
        if x in self.clipboard_registry:
            self.clipboard_registry.remove(x)

    def is_registered(self, x):
        return x in self.registry

    #
    # Mutator client interface -- transactions.
    # This calls the dependent clients' callbacks.
    #
    def __start_transaction(self, type, undo=0):
        done = []
        for x in self.registry[:]:
            if not x.transaction(type):
                for x in done:
                    x.rollback()
                return 0
            done.append(x)
        self.undostep = []
        if undo:
            self.future.append(self.undostep)
        else:
            self.history.append(self.undostep)
        self.busy = 1
        return 1

    def transaction(self, type=None):
        if self.busy: raise MMExc.AssertError, 'recursive transaction'

        if self.context == None:
            # the document is probably not open
            return 0

        # allow transaction only the document is valid, or if the transaction come from the source view
        # note: this test can't be done from the source view which may be closed
        if type != 'source' and not self.context.isValidDocument():
            import windowinterface
            windowinterface.showmessage('You should first fix the parsing errors in the source view.',
                                        mtype = 'error')
            return 0

        self.__delete(self.future)
        self.future = []

        return self.__start_transaction(type)

    def commit(self, type=None):
        if not self.busy: raise MMExc.AssertError, 'invalid commit'
        import MMAttrdefs
        # test if the root node has changed

        if type is None:
            if self.structure_changed:
                type = 'STRUCTURE_CHANGED'
            elif self.attrs_changed:
                type = 'ATTRS_CHANGED'

        if not self.__newRoot:
            # the root node hasn't changed (the document hasn't been reloaded)
            # normal treatment
            MMAttrdefs.flushcache(self.root)

            self.context.changedtimes(self.root)
            self.root.clear_infoicon()
            self.root.ResetPlayability()
            for x in self.registry[:]:
                x.commit(type)
        else:
            # the root node has changed (the document has been reloaded)
            # special treatment
            self.toplevel.changeRoot(self.__newRoot)
            self.__newRoot = None

        # if the error state has changed, update also the views and commandlist
        if self.__errorstateChanged:
            self.toplevel.updateViewsOnErrors()
            self.toplevel.updateCommandlistOnErrors()
            self.__errorstateChanged = 0

        self.busy = 0
        del self.undostep # To frustrate invalid addstep calls
        self.structure_changed = 0
        self.attrs_changed = 0
        self.next_focus = []

    def rollback(self):
        if not self.busy: raise MMExc.AssertError, 'invalid rollback'
        # undo changes made in this transaction
        actions = self.undostep
        self.__do_undo(actions)
        for x in self.registry[:]:
            x.rollback()
        self.busy = 0
        del self.undostep # To frustrate invalid addstep calls
        self.next_focus = []

    #
    # player state interface
    #
    def setplayerstate(self, state, parameters):
        if (state, parameters) == self.playerstate:
            return
        if self.playerstate_busy: raise MMExc.AssertError, 'recursive playerstate'
        self.playerstate_busy = 1
        self.playerstate = (state, parameters)
        for client in self.playerstate_registry:
            client.playerstatechanged(state, parameters)
        self.playerstate_busy = 0

    def getplayerstate(self):
        return self.playerstate

    #
    # Focus interface
    #
    def setglobalfocus(self, focuslist):
        # set the global focus to the given list of items
        # Quick return if this product does not have a shared focus
        if not features.UNIFIED_FOCUS in features.feature_set:
            return
        if focuslist == self.focus:
            return
        if self.focus_busy: raise MMExc.AssertError, 'recursive focus'
        self.focus_busy = 1
        self.focus = focuslist
        if not self.busy:
            # delay calling this until commit
            for client in self.focus_registry:
                client.globalfocuschanged(focuslist)
        self.focus_busy = 0

    def addglobalfocus(self, list):
        # add items in list to global focus
        if not features.UNIFIED_FOCUS in features.feature_set:
            return
        if self.focus_busy: raise MMExc.AssertError, 'recursive focus'
        self.focus_busy = 1
        changed = 0
        for item in list:
            if item not in self.focus:
                self.focus.append(item)
                changed = 1
        if not self.busy:
            # delay calling this until commit
            for client in self.focus_registry:
                client.globalfocuschanged(self.focus)
        self.focus_busy = 0

    def delglobalfocus(self, list):
        # remove items in list from global focus
        if not features.UNIFIED_FOCUS in features.feature_set:
            return
        if self.focus_busy: raise MMExc.AssertError, 'recursive focus'
        self.focus_busy = 1
        changed = 0
        for item in list:
            if item in self.focus:
                self.focus.remove(item)
                changed = 1
        if not self.busy:
            # delay calling this until commit
            for client in self.focus_registry:
                client.globalfocuschanged(self.focus)
        self.focus_busy = 0

    def getglobalfocus(self):
        return self.focus

    # Note: we do NOT override clearclip() here, so the clearclip is
    # not forwarded to the registered listeners. This is intentional:
    # a clearclip() is an administrative call for using during cleanup
    # and not for general use.

    #
    # UNDO interface -- this code isn't ready yet.
    #
    def __do_undo(self, actions):
        # After undo/redo we set the focus to something sensible. That is handled
        # here.
        for i in range(len(actions)-1,-1,-1):
            action = actions[i]
            cmd = action[0]
            func = getattr(self, 'undo_'+cmd)
            apply(func, action[1:])

    def undo(self):
        if self.busy: raise MMExc.AssertError, 'undo while busy'
        if not self.history:
            return 0
        step = self.history[-1]
        if not self.__start_transaction(None, 1):
            return 0
        del self.history[-1]
        self.next_focus = []
        self.__do_undo(step)
        nextfocusvalue = self.next_focus
        self.setglobalfocus(nextfocusvalue)
        self.commit()
        return 1

    def redo(self):
        if self.busy: raise MMExc.AssertError, 'redo while busy'
        if not self.future:
            return 0
        step = self.future[-1]
        if not self.__start_transaction(None):
            return 0
        del self.future[-1]
        self.next_focus = []
        self.__do_undo(step)
        nextfocusvalue = self.next_focus
        self.commit()
        self.setglobalfocus(nextfocusvalue)
        return 1

    # XXX The undo/redo business is unfinished.
    # E.g., What to do if the user undoes a few steps,
    # then makes new changes, then wants to redo?
    # Also the commit/rollback stuff isn't watertight
    # (ideally rollback must be able to roll back even if
    # an arbitrary keyboard interrupt hit).
    #
    def addstep(self, *step):
        # This fails if we're not busy because self.undostep is deleted
        self.undostep.append(step)

    #
    # Mutator client interface -- tree mutations.
    #
    # Node operations
    #
    def delnode(self, node):
        self.structure_changed = 1
        parent = node.GetParent()
        i = parent.GetChildren().index(node)
        self.addstep('delnode', parent, i, node)

        node.removeOwner(OWNER_DOCUMENT)

        node.Extract()
        sibs = parent.GetChildren()
        if i < len(sibs):
            # select next sibling
            self.next_focus = [sibs[i]]
        elif len(sibs) > 0:
            # select previous sibling
            self.next_focus = [sibs[-1]]
        else:
            # select parent
            self.next_focus = [parent]

    def undo_delnode(self, parent, i, node):
        self.addnode(parent, i, node)

    def clean_delnode(self, parent, i, node):
        self.__clean_node(node)

    def addnode(self, parent, i, node):
        self.structure_changed = 1
        self.addstep('addnode', node)

        node.addOwner(OWNER_DOCUMENT)

        node.AddToTree(parent, i)

        self.next_focus = [node]

    def undo_addnode(self, node):
        self.delnode(node)

    def clean_addnode(self, node):
        pass

    def setnodetype(self, node, type):
        self.attrs_changed = 1
        oldtype = node.GetType()
        self.addstep('setnodetype', node, oldtype)
        node.SetType(type)
        self.next_focus = [node]

    def undo_setnodetype(self, node, oldtype):
        self.setnodetype(node, oldtype)

    def clean_setnodetype(self, node, oldtype):
        pass

    def setnodeattr(self, node, name, value):
        self.attrs_changed = 1
        oldvalue = node.GetRawAttrDef(name, None)
        self.addstep('setnodeattr', node, name, oldvalue)
        if value is not None:
            node.SetAttr(name, value)
        else:
            node.DelAttr(name)

        self.next_focus = [node]

    def undo_setnodeattr(self, node, name, oldvalue):
        self.setnodeattr(node, name, oldvalue)

    def clean_setnodeattr(self, node, name, oldvalue):
        pass

    def setnodevalues(self, node, values):
        # The node values are for immediate nodes where the data (instead of a url)
        # is stored in MMNode.values[]
        self.addstep('setnodevalues', node, node.GetValues())
        node.SetValues(values)
        self.next_focus = [node]

    def undo_setnodevalues(self, node, oldvalues):
        # XXX Shouldn't this be (self, node, oldvalues)??
        self.setnodevalues(node, oldvalues)

    def clean_setnodevalues(self, node, oldvalues):
        pass

    #
    # Sync arc operations
    #
    def addsyncarc(self, node, attr, arc, pos = -1):
        self.attrs_changed = 1
        list = node.GetRawAttrDef(attr, [])[:]
        if arc in list:
            return
        if pos >= 0:
            list.insert(pos, arc)
        else:
            list.append(arc)
        node.SetAttr(attr, list)
        self.addstep('addsyncarc', node, attr, arc, pos)
        self.next_focus = [node]

    def undo_addsyncarc(self, node, attr, arc, pos):
        self.delsyncarc(node, attr, arc)

    def clean_addsyncarc(self, node, attr, arc, pos):
        pass

    def delsyncarc(self, node, attr, arc):
        self.attrs_changed = 1
        list = node.GetRawAttrDef(attr, [])[:]
        for i in range(len(list)):
            if list[i] == arc:
                break
        else:
            raise MMExc.AssertError, 'bad delsyncarc call'
        del list[i]
        if list:
            node.SetAttr(attr, list)
        else:
            node.DelAttr(attr)
        self.addstep('delsyncarc', node, attr, arc, i)
        self.next_focus = [node]

    def undo_delsyncarc(self, node, attr, arc, i):
        self.addsyncarc(node, attr, arc, i)

    def clean_delsyncarc(self, node, attr, arc, i):
        pass

    #
    # Hyperlink operations
    #
    def addlink(self, link):
        #print "DEBUG: addlink; link is: ", link
        # Link is a tuple of (srcanchor, dstanchor, direction, jump_type, src_stop, dest_play)
        # where:
        # srcanchor is this link's source
        # dstanchor is this link's destination
        # For the other attributes, see documentation in Hlinks.py.
        #
        # The anchors (srcanchor, dstanchor) are tuples of (uid, aid)
        # where uid is the unique node id
        # and aid is the anchor id.
        self.attrs_changed = 1
        self.addstep('addlink', link)
        self.context.hyperlinks.addlink(link)
##         self.next_focus = []    # this object cannot have focus (yet)

    def undo_addlink(self, link):
        self.dellink(link)

    def clean_addlink(self, link):
        pass

    def dellink(self, link):
        self.attrs_changed = 1
        self.addstep('dellink', link)
        self.context.hyperlinks.dellink(link)
##         self.next_focus = []    # this object cannot have focus (yet)

    def undo_dellink(self, link):
        self.addlink(link)

    def clean_dellink(self, link):
        pass

    def addexternalanchor(self, url):
        self.attrs_changed = 1
        self.addstep('addexternalanchor', url)
        # context.externalanchors is a list.
        self.context.externalanchors.append(url)
##         self.next_focus = []    # this object cannot have focus (yet)

    def undo_addexternalanchor(self, url):
        self.delexternalanchor(url)

    def clean_addexternalanchor(self, url):
        pass

    def delexternalanchor(self, url):
        self.attrs_changed = 1
        self.addstep('delexternalanchor', url)
        self.context.externalanchors.remove(url)
##         self.next_focus = []    # this object cannot have focus (yet)

    def undo_delexternalanchor(self, url):
        self.addexternalanchor(url)

    def clean_delexternalanchor(self, url):
        pass

    #
    # Channel operations
    #
    def addchannel(self, parent, i, channel):
        self.addstep('addchannel', channel)

        channel.addOwner(OWNER_DOCUMENT)

        if parent != None:
            self.setchannelattr(channel.name, 'base_window', parent.name)
            channel.Move(i)
        self.next_focus = [channel]

    def undo_addchannel(self, channel):
        self.delchannel(channel)

    def clean_addchannel(self, channel):
        pass

    # Not currently used.
    def copychannel(self, name, i, orig):
        self.attrs_changed = 1
        c = self.context.getchannel(name)
        if c is not None:
            raise MMExc.AssertError, \
                    'duplicate channel name in copychannel'
        c = self.context.getchannel(orig)
        if c is None:
            raise MMExc.AssertError, \
                    'unknown orig channel name in copychannel'
        self.addstep('copychannel', name)
        self.context.copychannel(name, i, orig)
        self.next_focus = [self.context.getchannel(name)]

    # Not currently used.
    def undo_copychannel(self, name):
        self.delchannel(name)

    # Not currently used.
    def clean_copychannel(self, name):
        pass

    # Not currently used.
    def movechannel(self, name, i):
        self.attrs_changed = 1
        old_i = self.context.channelnames.index(name)
        self.addstep('movechannel', name, old_i)
        self.context.movechannel(name, i)
        self.next_focus = [self.context.getchannel(name)]

    # Not currently used.
    def undo_movechannel(self, name, old_i):
        self.movechannel(name, old_i)

    # Not currently used.
    def clean_movechannel(self, name, old_i):
        pass

    def delchannel(self, channel):
        if not channel is None and channel.isDefault():
            # can't delete the default region
            return
        parent = channel.GetParent()
        i = -1
        if parent:
            i = parent.GetChildren().index(channel)
        self.addstep('delchannel', parent, i, channel)

        channel.removeOwner(OWNER_DOCUMENT)

        channel.Extract()

        if parent:
            sibs = parent.GetChildren()
            if i < len(sibs):
                # select next sibling
                self.next_focus = [sibs[i]]
            elif len(sibs) > 0:
                # select previous sibling
                self.next_focus = [sibs[-1]]
            else:
                # select parent
                self.next_focus = [parent]
        else:
            # a top layout has been removed
            self.next_focus = []

    def undo_delchannel(self, parent, i, channel):
        self.addchannel(parent, i, channel)

    def clean_delchannel(self, parent, i, channel):
        self.__clean_node(channel)

    def setchannelname(self, name, newname):
        self.attrs_changed = 1
        if newname == name:
            return # No change
        c = self.context.getchannel(name)
        if c is None:
            raise MMExc.AssertError, \
                      'unknown channel name in setchannelname'
        self.addstep('setchannelname', name, newname)
        self.context.setchannelname(name, newname)
        self.next_focus = [self.context.getchannel(newname)]

    def undo_setchannelname(self, oldname, name):
        self.setchannelname(name, oldname)

    def clean_setchannelname(self, oldname, name):
        pass

    def setchannelattr(self, name, attrname, value):
        defaultRegion = self.context.getDefaultRegion()
        if defaultRegion is not None and defaultRegion.name == name:
            # can't edit the default region
            return

        self.attrs_changed = 1
        c = self.context.getchannel(name)
        if c is None:
            raise MMExc.AssertError, \
                      'unknown channel name in setchannelattr'
        if c.has_key(attrname):
            oldvalue = c[attrname]
        else:
            oldvalue = None
        if value == oldvalue:
            return
        self.addstep('setchannelattr', name, attrname, oldvalue)
        if value is None:
            del c[attrname]
        else:
            c[attrname] = value
        self.next_focus = [c]

    def undo_setchannelattr(self, name, attrname, oldvalue):
        self.setchannelattr(name, attrname, oldvalue)

    def clean_setchannelattr(self, name, attrname, oldvalue):
        pass

    #
    # Layout operations
    #
    def addlayout(self, name):
        if self.context.layouts.has_key(name):
            raise MMExc.AssertError, \
                  'duplicate layout name in addlayout'
        self.addstep('addlayout', name)
        self.context.addlayout(name)
##         self.next_focus = []    # This object cannot have focus (yet)

    def undo_addlayout(self, name):
        self.dellayout(name)

    def clean_addlayout(self, name):
        pass

    def dellayout(self, name):
        layout = self.context.layouts.get(name)
        if layout is None:
            raise MMExc.AssertError, 'unknown layout in dellayout'
        self.addstep('dellayout', name, layout)
        self.context.dellayout(name)
##         self.next_focus = []    # This object cannot have focus (yet)

    def undo_dellayout(self, name, layout):
        self.addlayout(name)
        for channel in layout:
            self.addlayoutchannel(name, channel)

    def clean_dellayout(self, name, layout):
        pass

    def addlayoutchannel(self, name, channel):
        layout = self.context.layouts.get(name)
        if layout is None:
            raise MMExc.AssertError, \
                  'unknown layout in addlayoutchannel'
        if channel in layout:
            raise MMExc.AssertError, \
                  'channel already in layout in addlayoutchannel'
        self.addstep('addlayoutchannel', name, channel)
        self.context.addlayoutchannel(name, channel)
        self.next_focus = []    # This object cannot have focus (yet)

    def undo_addlayoutchannel(self, name, channel):
        self.dellayoutchannel(name, channel)

    def clean_addlayoutchannel(self, name, channel):
        pass

    def dellayoutchannel(self, name, channel):
        layout = self.context.layouts.get(name)
        if layout is None:
            raise MMExc.AssertError, \
                  'unknown layout in addlayoutchannel'
        if channel not in layout:
            raise MMExc.AssertError, \
                  'channel not in layout in dellayoutchannel'
        self.addstep('dellayoutchannel', name, channel)
        self.context.dellayoutchannel(name, channel)
        self.next_focus = []    # This object cannot have focus (yet)

    def undo_dellayoutchannel(self, name, channel):
        self.addlayoutchannel(name, channel)

    def clean_dellayoutchannel(self, name, channel):
        pass

    def setlayoutname(self, name, newname):
        if newname == name:
            return          # no change
        if not self.context.layouts.has_key(name):
            raise MMExc.AssertError, \
                  'unknown layout name in setlayoutname'
        if self.context.layouts.has_key(newname):
            raise MMExc.AssertError, \
                  'name already in use in setlayoutname'
        self.addstep('setlayoutname', name, newname)
        self.context.setlayoutname(name, newname)
        self.next_focus = []    # This object cannot have focus (yet)

    def undo_setlayoutname(self, oldname, name):
        self.setlayoutname(name, oldname)

    def clean_setlayoutname(self, oldname, name):
        pass

    #
    # User group operations
    #
    def addusergroup(self, name, value):
        if self.context.usergroups.has_key(name):
            raise MMExc.AssertError, \
                  'duplicate usergroup name in addusergroup'
        self.addstep('addusergroup', name)
        self.context.addusergroup(name, value)
##         self.next_focus = []    # This object cannot have focus (yet)

    def undo_addusergroup(self, name):
        self.delusergroup(name)

    def clean_addusergroup(self, name):
        pass

    def delusergroup(self, name):
        usergroup = self.context.usergroups.get(name)
        if usergroup is None:
            raise MMExc.AssertError, 'unknown usergroup in delusergroup'
        self.addstep('delusergroup', name, usergroup)
        self.context.delusergroup(name)
##         self.next_focus = []    # This object cannot have focus (yet)

    def undo_delusergroup(self, name, usergroup):
        self.addusergroup(name, usergroup)

    def setusergroupname(self, name, newname):
        if newname == name:
            return          # no change
        if not self.context.usergroups.has_key(name):
            raise MMExc.AssertError, \
                  'unknown usergroup name in setusergroupname'
        if self.context.usergroups.has_key(newname):
            raise MMExc.AssertError, \
                  'name already in use in setusergroupname'
        self.addstep('setusergroupname', name, newname)
        self.context.setusergroupname(name, newname)
##         self.next_focus = []    # This object cannot have focus (yet)

    def clean_delusergroup(self, name, usergroup):
        pass

    def undo_setusergroupname(self, oldname, name):
        self.setusergroupname(name, oldname)

    def clean_setusergroupname(self, oldname, name):
        pass

    #
    # Transitions operations
    #
    def addtransition(self, name, value):
        self.attrs_changed = 1
        if self.context.transitions.has_key(name):
            raise MMExc.AssertError, \
                  'duplicate transition name in addtransition'
        self.addstep('addtransition', name)
        self.context.addtransition(name, value)
##         self.next_focus = []    # This object cannot have focus (yet)

    def undo_addtransition(self, name):
        self.deltransition(name)

    def clean_addtransition(self, name):
        pass

    def deltransition(self, name):
        self.attrs_changed = 1
        transition = self.context.transitions.get(name)
        if transition is None:
            raise MMExc.AssertError, 'unknown transition in deltransition'
        self.addstep('deltransition', name, transition)
        self.context.deltransition(name)
##         self.next_focus = []    # This object cannot have focus (yet)

    def undo_deltransition(self, name, transition):
        self.attrs_changed = 1
        self.addtransition(name, transition)
        for key, val in transition.items():
            self.settransitionvalue(name, key, val)

    def clean_deltransition(self, name, transition):
        pass

    def settransitionname(self, name, newname):
        self.attrs_changed = 1
        if newname == name:
            return          # no change
        if not self.context.transitions.has_key(name):
            raise MMExc.AssertError, \
                  'unknown transition name in settransitionname'
        if self.context.transitions.has_key(newname):
            raise MMExc.AssertError, \
                  'name already in use in settransitionname'
        self.addstep('settransitionname', name, newname)
        self.context.settransitionname(name, newname)
##         self.next_focus = []    # This object cannot have focus (yet)

    def undo_settransitionname(self, oldname, name):
        self.settransitionname(name, oldname)

    def clean_settransitionname(self, oldname, name):
        pass

    def settransitionvalue(self, name, key, value):
        self.attrs_changed = 1
        if not self.context.transitions.has_key(name):
            raise MMExc.AssertError, \
                  'unknown transition name in settransitionname'
        dict = self.context.transitions[name]
        oldvalue = dict.get(key)
        if oldvalue == value:
            return
        dict[key] = value
        if value is None:
            del dict[key]
        self.addstep('settransitionvalue', name, key, oldvalue)
##         self.next_focus = []    # This object cannot have focus (yet)

    def undo_settransitionvalue(self, name, key, oldvalue):
        self.settransitionvalue(name, key, oldvalue)

    def clean_settransitionvalue(self, name, key, oldvalue):
        pass

    #
    # Document operations
    #
    def deldocument(self, root):
        self.addstep('deldocument', root)
        self.next_focus = []    # This object cannot have focus (yet)

    def adddocument(self, root):
        self.addstep('adddocument', root)
        self.__newRoot = root
        self.next_focus = []    # This object cannot have focus (yet)

    def undo_deldocument(self, root):
        self.adddocument(root)

    def undo_adddocument(self, root):
        self.deldocument(root)

    def clean_deldocument(self, root):
        pass

    def clean_adddocument(self, root):
        # destroy the root only if it's not the current root
        if root is not self.root:
            self.toplevel.destroyRoot(root)

    #
    # parsestatus operations
    #
    def delparsestatus(self, parsestatus):
        self.addstep('delparsestatus', parsestatus)
        self.__errorstateChanged = 1
        if self.context != None:
            self.context.setParseErrors(None)
        self.next_focus = []    # This object cannot have focus (yet)

    def addparsestatus(self, parsestatus):
        self.addstep('addparsestatus', parsestatus)
        self.__errorstateChanged = 1
        if self.context != None:
            self.context.setParseErrors(parsestatus)
        self.next_focus = []    # This object cannot have focus (yet)

    def undo_delparsestatus(self, parsestatus):
        self.addparsestatus(parsestatus)

    def undo_addparsestatus(self, parsestatus):
        self.delparsestatus(parsestatus)

    def clean_delparsestatus(self, parsestatus):
        pass

    def clean_addparsestatus(self, parsestatus):
        pass

    #
    # asset operations
    #
    def addasset(self, asset):
        self.addstep('addasset', asset)

        asset.addOwner(OWNER_ASSET)

        self.context.addasset(asset)
        self.next_focus = []    # This object cannot have focus (yet)

    def delasset(self, asset):
        self.addstep('delasset', asset)

        asset.removeOwner(OWNER_ASSET)

        self.context.delasset(asset, self.toplevel.root)
        self.next_focus = []    # This object cannot have focus (yet)

    def undo_addasset(self, asset):
        self.delasset(asset)

    def undo_delasset(self, asset):
        self.addasset(asset)

    def clean_addasset(self, asset):
        pass

    def clean_delasset(self, asset):
        self.__clean_node(asset)

    #
    # Clipboard interface
    #

    def setclip(self, data):
        # save the old content
        olddata = Clipboard.Clipboard.getclip(self)
        self.addstep('setclip', olddata)

        # the old content is take out from the clipboard, and its content is not
        # restored into the document. So we can remove the all associated references
        for node in olddata:
            self.clearRefs(node)

        Clipboard.Clipboard.setclip(self, data)
        for client in self.clipboard_registry:
            client.clipboardchanged()

    def undo_setclip(self, olddata):
        self.restoreclip(olddata)

    def clean_setclip(self, data):
        for node in data:
            self.__clean_node(node)

    def restoreclip(self, data):
        # save the old content
        olddata = Clipboard.Clipboard.getclip(self)
        self.addstep('restoreclip', olddata)

        # the new content is take out from the clipboard to be restored into the document
        # the old content is restored into the clipboard
        # So, we don't have to clear any reference there

        # change the clipboard content, but don't clear the reference of the
        # data which is restored into the document
        Clipboard.Clipboard.setclip(self, data)
        for client in self.clipboard_registry:
            client.clipboardchanged()

    def undo_restoreclip(self, olddata):
        self.setclip(olddata)

    def clean_restoreclip(self, data):
        for node in data:
            self.__clean_node(node)

    #
    # Clean up management
    #

    # clear all references that refer the current node
    # Node can be any reference node being a part of the document
    def clearRefs(self, nodeRef):
        if hasattr(nodeRef, 'ClearRefs'):
            rootList = []

            # body root
            rootList.append(self.root)

            # viewports root
            viewportList = self.context.getviewports()
            for viewport in viewportList:
                rootList.append(viewport)

            # all root elements of the clipboard itself
            data = self.getclip()
            for node in data:
                rootList.append(node)

            # all root elements of the asset view
            # XXX todo

            nodeRef.ClearRefs(self, rootList)

    # before to destroy any node (may be copied in the clipboard and asset view), we want to make sure that the node being destroyed
    # won't be ever used anymore
    def __clean_node(self, node):
        if node.GetParent() != None or node.getOwner() != OWNER_NONE:
            # this node is either:
            # - part of another tree. So we can't destroy it
            # - belong to either the document, clipboard or assets view
            # So we can't destroy it
            return

        # this node can be destroyed only if there is no other instance in the history list
        for actions in self.history:
            for action in actions:
                cmd = action[0]
                if cmd in ('delnode','delchannel') and action[3] is node:
                    return
                elif cmd == 'delasset' and action[1] is node:
                    return
                elif cmd in ('restoreclip', 'setclip'):
                    nlist = action[1]
                    for n in nlist:
                        if n is node:
                            return

        # destroy forever
        # Note: if the node may be already destroyed. A same occurence may be several times in the list being destroyed
        # in this case, the Destroy method mustn't cause any crash
        node.Destroy()
