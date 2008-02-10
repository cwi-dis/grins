__version__ = "$Id$"

# Dialog for the Errors View.
# The Errors View is a window that displays a list of source errors

import windowinterface
from usercmd import *
import ViewDialog

class ErrorsViewDialog(ViewDialog.ViewDialog):
    def __init__(self):
        ViewDialog.ViewDialog.__init__(self, 'errorsview_')
        self.__window = None
        self.__callbacks={
                 }

    def destroy(self):
        if self.__window is None:
            return
        self.removeListener()
        if hasattr(self.__window,'_obj_') and self.__window._obj_:
            self.__window.close()
        self.__window = None

    def show(self):
        self.assertwndcreated()
        if self.__window != None:
            self.__window.setListener(self)

    def pop(self):
        if self.__window != None:
            self.__window.pop()

    def is_showing(self):
        if self.__window is None:
            return 0
        return self.__window.is_showing()

    def hide(self):
        if self.__window is not None:
            self.__window.close()
            self.__window = None

    def get_geometry(self):
        if self.__window:
            self.last_geometry = self.__window.getgeometry(windowinterface.UNIT_PXL)
            return self.last_geometry

    def setErrorList(self, errorList):
        if self.__window != None:
            self.__window.setErrorList(errorList)

#### support win32 model
    def createviewobj(self):
        if self.__window: return
        f=self.toplevel.window
        w=f.newviewobj('erview_')
        w.set_cmddict(self.__callbacks)
        self.__window = w

    def assertwndcreated(self):
        if self.__window is None or not hasattr(self.__window,'GetSafeHwnd'):
            self.createviewobj()
        if self.__window.GetSafeHwnd()==0:
            f=self.toplevel.window
            f.showview(self.__window,'erview_', self.last_geometry)
#                       self.__window.show()

    def getwindow(self):
        return self.__window
