__version__ = "$Id$"

# experimental layout view

import ViewDialog
import windowinterface
import win32ui, win32api, win32con, appcon

from usercmd import *
IMPL_AS_FORM=1

class LayoutViewDialog2(ViewDialog.ViewDialog):

    def __init__(self):
        ViewDialog.ViewDialog.__init__(self, 'layoutview_')
        self.__window=None

    def createviewobj(self):
        f=self.toplevel.window

        # create an new view : return an instance of _LayoutView
        w=f.newviewobj('lview2_')

        # get a handle for each control created from _LayoutView class and associate a callback
        # note: if you modify the key names, you also have to modify them in _LayoutView class
#               self.__viewportSelCtrl=w['ViewportSel']
#               self.__viewportSelCtrl.setcb((self._viewportSelCb, ()))

#               self.__regionSelCtrl=w['RegionSel']
#               self.__regionSelCtrl.setcb((self._regionSelCb, ()))

        self.previousCtrl=w.getPreviousComponent()

        # for now, avoid to define one handler by ctrl
        self.dialogCtrl=w.getDialogComponent()

        # tree control
        self.treeCtrl = w.getTreeComponent()

        self.__window = w


    def destroy(self):
        if self.__window is None:
            return
        if hasattr(self.__window,'_obj_') and self.__window._obj_:
            self.__window.close()
        self.__window = None
        #del self.__viewportSelCtrl
        #del self.__regionSelCtrl

    def show(self):
        self.load_geometry()
        self.assertwndcreated()
        self.__window.show()

        # key time slider
        self.keyTimeSliderCtrl = self.__window.getKeyTimeSlider()


    def is_showing(self):
        if self.__window is None:
            return 0
        return self.__window.is_showing()

    def hide(self):
        self.save_geometry()
        if self.__window is not None:
            self.__window.close()
            self.__window = None
            f=self.toplevel.window
            f.set_toggle(LAYOUTVIEW,0)

    def get_geometry(self):
        if self.__window:
            self.last_geometry = self.__window.getgeometry(windowinterface.UNIT_PXL)
            return self.last_geometry

    def setcommands(self, commandlist, title):
        self.__window.set_commandlist(commandlist)
#               self.window.set_dynamiclist(ANCESTORS, self.baseobject.ancestors)
#               self.window.set_dynamiclist(SIBLINGS, self.baseobject.siblings)

    def settoggle(self, command, onoff):
        self.__window.set_toggle(command, onoff)

    def assertwndcreated(self):
        if self.__window is None or not hasattr(self.__window,'GetSafeHwnd'):
            self.createviewobj()
        if self.__window.GetSafeHwnd()==0:
            f=self.toplevel.window
            if IMPL_AS_FORM: # form
                f.showview(self.__window,'lview2_', self.last_geometry)
                self.__window.show()
            else:# dlgbar
                self.__window.create(f)
                f.set_toggle(LAYOUTVIEW,1)

    def setwaiting(self):
        windowinterface.setwaiting()

    def setready(self):
        windowinterface.setready()

    def setcommandlist(self, commandlist):
        if self.__window:
            self.__window.set_commandlist(commandlist)

    # specific win32 dialog box

    def chooseBgColor(self, currentBg):
        r, g, b = currentBg or (255, 255, 255)
        dlg = win32ui.CreateColorDialog(win32api.RGB(r,g,b),win32con.CC_ANYCOLOR,self.__window)
        if dlg.DoModal() == win32con.IDOK:
            newcol = dlg.GetColor()
            rgb = win32ui.GetWin32Sdk().GetRGBValues(newcol)
            return rgb

        return None

    def askname(self, default, title, applyCallback,  cancelCallBack = None):
        w=windowinterface.InputDialog(title,
                                    default,
                                    applyCallback,
                                    cancelCallback = cancelCallBack,
                                    parent = self.__window)

    def zoomIn(self, factor=None):
        if self.__window is not None:
            self.__window.zoomIn(factor)

    def zoomOut(self, factor=None):
        if self.__window is not None:
            self.__window.zoomOut(factor)


    def zoomReset(self):
        if self.__window is not None:
            self.__window.zoomReset()
