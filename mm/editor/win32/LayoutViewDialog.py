__version__ = "$Id$"

# @win32doc|LayoutViewDialog
# This class represents the interface between the LayoutView platform independent
# class and its implementation class _LayoutView in lib/win32/_LayoutView.py which
# implements the actual view.

import windowinterface
from usercmd import *
IMPL_AS_FORM=1

class LayoutViewDialog:
    def __init__(self):
        self.__window=None

    def createviewobj(self):
        f=self.toplevel.window

        w=f.newviewobj('lview_')

        self.__layoutlist=w['LayoutList']
        self.__layoutlist.setcb((self.__layoutcb, ()))

        self.__channellist=w['ChannelList']
        self.__channellist.setcb((self.__channelcb, ()))

        self.__otherlist=w['OtherList']
        self.__otherlist.setcb((self.__othercb, ()))

        self.__window = w

    def destroy(self):
        if self.__window is None:
            return
        if hasattr(self.__window,'_obj_') and self.__window._obj_:
            self.__window.close()
        self.__window = None
        del self.__layoutlist
        del self.__channellist
        del self.__otherlist

    def show(self):
        self.assertwndcreated()
        self.__window.show()

    def is_showing(self):
        if self.__window is None:
            return 0
        return self.__window.is_showing()

    def hide(self):
        if self.__window is not None:
            self.__window.close()
            self.__window = None
            f=self.toplevel.window
            f.set_toggle(LAYOUTVIEW,0)


    def assertwndcreated(self):
        if self.__window is None or not hasattr(self.__window,'GetSafeHwnd'):
            self.createviewobj()
        if self.__window.GetSafeHwnd()==0:
            f=self.toplevel.window
            if IMPL_AS_FORM: # form
                f.showview(self.__window,'lview_')
                self.__window.show()
            else:# dlgbar
                self.__window.create(f)
                f.set_toggle(LAYOUTVIEW,1)

    def setlayoutlist(self, layouts, cur):
        # the core should be corected but
        # in order to proceed let fill the hole here
        self.assertwndcreated()
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

    def layoutname(self):
        return self.__layoutlist.getselection()

    def __layoutcb(self):
        sel = self.__layoutlist.getselected()
        if sel is None:
            self.curlayout = None
        else:
            self.curlayout = self.__layoutlist.getlistitem(sel)
        self.fill()

    def __channelcb(self):
        sel = self.__channellist.getselected()
        if sel is None:
            self.curchannel = None
        else:
            self.curchannel = self.__channellist.getlistitem(sel)
        self.fill()

    def __othercb(self):
        sel = self.__otherlist.getselected()
        if sel is None:
            self.curother = None
        else:
            self.curother = self.__otherlist.getlistitem(sel)
        self.fill()

    def setwaiting(self):
        windowinterface.setwaiting()

    def setready(self):
        windowinterface.setready()

    def setcommandlist(self, commandlist):
        self.__window.set_commandlist(commandlist)

    def asklayoutname(self, default):
        w=windowinterface.LayoutNameDlg('Name for layout',
                                    default,
                                    self.newlayout_callback,
                                    cancelCallback = (self.newlayout_callback, ()),
                                    parent = self.__window)
        w.show()


    def askchannelnameandtype(self, default, types):
        w=windowinterface.NewChannelDlg('newchanneldialog',default,grab = 1,
                                   parent = self.__window)
        self.__chanwin = w
        self.__chantext=w._chantext
        self.__chantype=w._chantype
        self.__chantype._optionlist=types[:]
        w._cbd_ok=(self.__okchannel, (1,))
        w._cbd_cancel=(self.__okchannel, (0,))
        w.show()

    def __okchannel(self, ok = 0):
        if ok:
            name = self.__chantext.gettext()
            type = self.__chantype.getvalue()
        else:
            name = type = None
        self.__chanwin.close() # <- end of grab mode
        del self.__chantext
        del self.__chantype
        del self.__chanwin
        apply(apply,(self.newchannel_callback, (name, type)))

        # if in grab mode:
        #       We can't call this directly since we're still in
        #       grab mode.  We must first return from this callback
        #       before we're out of that mode, so we must schedule a
        #       callback in the very near future.
        #       windowinterface.settimer(0.00001, (self.newchannel_callback, (name, type)))
