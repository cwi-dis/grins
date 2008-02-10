__version__ = "$Id$"

# License dialog
import windowinterface
import components
import win32dialog
import grinsRC
import win32con
import win32ui
import win32mu
import compatibility

class LicenseDialog(win32dialog.ResDialog):
    def __init__(self):
        win32dialog.ResDialog.__init__(self, grinsRC.IDD_LICENSE)

        self.__enabled = {}

        self.__splash = components.WndCtrl(self, grinsRC.IDC_SPLASH)
        self.__label = components.Static(self,grinsRC.IDC_MESSAGE)

        self.__quit = components.Button(self,win32con.IDCANCEL)
        self.__buy = components.Button(self,grinsRC.IDUC_BUY)
        self.__eval = components.Button(self,grinsRC.IDUC_EVALLICENSE)
        self.__enterkey = components.Button(self,grinsRC.IDUC_ENTERKEY)
        self.__openfile = components.Button(self, grinsRC.IDUC_OPENFILE)
        self.__try = components.Button(self,win32con.IDOK)

        self.loadbmp()
        self.__initialized = 0

    def OnInitDialog(self):
        self.attach_handles_to_subwindows()
        self.__quit.hookcommand(self, self.On_quit)
        self.__buy.hookcommand(self, self.On_buy)
        self.__eval.hookcommand(self, self.On_eval)
        self.__enterkey.hookcommand(self, self.On_enterkey)
        self.__openfile.hookcommand(self, self.On_openfile)
        self.__try.hookcommand(self, self.On_try)
        self.__splash.create_wnd_from_handle()
        self.HookMessage(self.OnDrawItem,win32con.WM_DRAWITEM)
        rv = win32dialog.ResDialog.OnInitDialog(self)
        self.__initialized = 1
        self.setdialoginfo()
        return rv

    def show(self):
        self.DoModal()

    def close(self):
        if not self.__initialized:
            return
        self.EndDialog(win32con.IDCANCEL)

    def setdialoginfo(self):
        if not self.__initialized:
            return
        self.__try.enable(self.can_try)
        self.__eval.enable(self.can_eval)
        self.__label.settext(self.msg)

    # Redraw the bitmap. Somehow this can't be done automatically
    # because of our resource file structure.
    def OnDrawItem(self,params):
        lParam=params[3]
        sdk = win32ui.GetWin32Sdk()
        hdc=sdk.ParseDrawItemStruct(lParam)
        dc=win32ui.CreateDCFromHandle(hdc)
        rct=self.__splash.GetClientRect()
        try:
            win32mu.BitBltBmp(dc,self.__bmp,rct)
        except:
            print dc,self.__bmp,rct
            return
        br=sdk.CreateBrush(win32con.BS_SOLID,0,0)
        dc.FrameRectFromHandle(rct,br)
        sdk.DeleteObject(br)
        dc.DeleteDC()

    def loadbmp(self):
        import splashbmp, win32dialog
        self.__bmp = win32dialog.loadBitmapFromResId(splashbmp.getResId())

    # Callback glue methods.

    def On_quit(self, id, code):
        self.cb_quit()

    def On_buy(self, id, code):
        self.cb_buy()

    def On_eval(self, id, code):
        self.cb_eval()

    def On_enterkey(self, id, code):
        self.cb_enterkey()

    def On_openfile(self, id, code):
        self.cb_open()

    def On_try(self, id, code):
        self.cb_try()

EnterkeyDialog = win32dialog.EnterKeyDlg

## def EnterkeyDialog(ok_callback):
##     import windowinterface
##           windowinterface.InputDialog("Enter key:", "", ok_callback)
