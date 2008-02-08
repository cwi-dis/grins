__version__ = "$Id$"

import windowinterface
from usercmd import *

class LayoutViewDialog:
    def __init__(self):
        w = windowinterface.Window('LayoutDialog', resizable = 1,
                                   deleteCallback = [CLOSE_WINDOW])
        self.__window = w
        w1 = w.SubWindow(left = None, top = None, bottom = None, right = 0.33)
        w2 = w.SubWindow(left = w1, top = None, bottom = None, right = 0.67)
        w3 = w.SubWindow(left = w2, top = None, bottom = None, right = None)
        b1 = w1.ButtonRow([('New...', NEW_LAYOUT),
                           ('Rename...', RENAME),
                           ('Delete', DELETE),
                           ],
                          vertical = 0,
                          left = None, right = None, bottom = None)
        l1 = w1.List('Screens', [], (self.__layoutcb, ()),
                     top = None, left = None, right = None, bottom = b1)
        self.__layoutlist = l1
        b2 = w2.ButtonRow([('New...', NEW_REGION),
                           ('Remove', REMOVE_REGION),
                           ('Properties...', ATTRIBUTES),
                           ],
                          vertical = 0,
                          left = None, right = None, bottom = None)
        l2 = w2.List('Channels in screen', [], (self.__channelcb, ()),
##                  tooltip = 'List of channels used in selected screen',
                     top = None, left = None, right = None, bottom = b2)
        self.__channellist = l2
        b3 = w3.ButtonRow([('Add', ADD_REGION),
                           ],
                          vertical = 0,
                          left = None, right = None, bottom = None)
        l3 = w3.List('Remaining channels', [], (self.__othercb, ()),
##                  tooltip = 'List of channels not used in current screen',
                     top = None, left = None, right = None, bottom = b3)
        self.__otherlist = l3

    def destroy(self):
        if self.__window is None:
            return
        self.__window.close()
        self.__window = None
        del self.__layoutlist
        del self.__channellist
        del self.__otherlist

    def show(self):
        self.__window.show()

    def is_showing(self):
        if self.__window is None:
            return 0
        return self.__window.is_showing()

    def hide(self):
        if self.__window is not None:
            self.__window.hide()

    def setlayoutlist(self, layouts, cur):
        if layouts != self.__layoutlist.getlist():
            self.__layoutlist.delalllistitems()
            self.__layoutlist.addlistitems(layouts, 0)
        if cur is not None:
            self.__layoutlist.selectitem(layouts.index(cur))
        else:
            self.__layoutlist.selectitem(None)

    def setchannellist(self, channels, cur):
        if channels != self.__channellist.getlist():
            self.__channellist.delalllistitems()
            self.__channellist.addlistitems(channels, 0)
        if cur is not None:
            self.__channellist.selectitem(channels.index(cur))
        else:
            self.__channellist.selectitem(None)

    def setotherlist(self, channels, cur):
        if channels != self.__otherlist.getlist():
            self.__otherlist.delalllistitems()
            self.__otherlist.addlistitems(channels, 0)
        if cur is not None:
            self.__otherlist.selectitem(channels.index(cur))
        else:
            self.__otherlist.selectitem(None)

    def __layoutcb(self):
        self.toplevel.setwaiting()
        sel = self.__layoutlist.getselected()
        if sel is None:
            self.curlayout = None
        else:
            self.curlayout = self.__layoutlist.getlistitem(sel)
        self.fill()

    def __channelcb(self):
        self.toplevel.setwaiting()
        sel = self.__channellist.getselected()
        if sel is None:
            self.curchannel = None
        else:
            self.curchannel = self.__channellist.getlistitem(sel)
        self.fill()

    def __othercb(self):
        self.toplevel.setwaiting()
        sel = self.__otherlist.getselected()
        if sel is None:
            self.curother = None
        else:
            self.curother = self.__otherlist.getlistitem(sel)
        self.fill()

    def setcommandlist(self, commandlist):
        self.__window.set_commandlist(commandlist)

    def asklayoutname(self, default):
        windowinterface.InputDialog('Screen name',
                                    default,
                                    self.newlayout_callback,
                                    cancelCallback = (self.newlayout_callback, ()),
                                    parent = self.__window)

    def askchannelnameandtype(self, default, types):
        w = windowinterface.Window('newchanneldialog', grab = 1,
                                   parent = self.__window)
        self.__chanwin = w
        t = w.TextInput('Name for channel', default, None, None, left = None, right = None, top = None)
        self.__chantext = t
        o = w.OptionMenu('Choose type', types, 0, None, top = t, left = None, right = None)
        self.__chantype = o
        b = w.ButtonRow([('Cancel', (self.__okchannel, (0,))),
                         ('OK', (self.__okchannel, (1,)))],
                        vertical = 0,
                        top = o, left = None, right = None, bottom = None)
        w.show()

    def __okchannel(self, ok = 0):
        if ok:
            name = self.__chantext.gettext()
            type = self.__chantype.getvalue()
        else:
            name = type = None
        self.__chanwin.close()
        del self.__chantext
        del self.__chantype
        del self.__chanwin
        # We can't call this directly since we're still in
        # grab mode.  We must first return from this callback
        # before we're out of that mode, so we must schedule a
        # callback in the very near future.
        windowinterface.settimer(0.00001, (self.newchannel_callback, (name, type)))
