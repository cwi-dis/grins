__version__ = "$Id$"

# License dialog
import windowinterface

def ITEMrange(fr, to): return range(fr, to+1)

ID_DIALOG_LICENSE=529
ITEM_SPLASH=1
ITEM_MESSAGE=2
ITEM_TRY=3
ITEM_BUY=4
ITEM_EVAL=5
ITEM_ENTERKEY=6
ITEM_QUIT=7
ITEM_NOTE=8
ITEM_OPEN=9
ITEMLIST_LICENSE_ALL=ITEMrange(ITEM_SPLASH, ITEM_OPEN)

ID_DIALOG_ENTERKEY=531
ITEM_OK=1
ITEM_CANCEL=2
ITEM_NAME=3
ITEM_ORGANIZATION=4
ITEM_KEY=5
ITEMLIST_ENTERKEY_ALL=ITEMrange(ITEM_OK, ITEM_KEY)


class LicenseDialog(windowinterface.MACDialog):
    def __init__(self):
        windowinterface.MACDialog.__init__(self, "License", ID_DIALOG_LICENSE,
                        ITEMLIST_LICENSE_ALL, cancel=ITEM_QUIT)

    def close(self):
        windowinterface.MACDialog.close(self)

    def setdialoginfo(self):

        self._setlabel(ITEM_MESSAGE, self.msg)

        self._setsensitive([ITEM_TRY], self.can_try)
        self._setsensitive([ITEM_EVAL], self.can_eval)

    def do_itemhit(self, n, event):
        if n == ITEM_QUIT:
            self.cb_quit()
        elif n == ITEM_TRY:
            self.cb_try()
        elif n == ITEM_BUY:
            self.cb_buy()
        elif n == ITEM_EVAL:
            self.cb_eval()
        elif n == ITEM_ENTERKEY:
            self.cb_enterkey()
        elif n == ITEM_OPEN:
            self.cb_open()
        else:
            print 'Unknown LicenseDialog item', n
        return 1

    def _optenable(self, onoff, item):
        ctl = self.dialog.GetDialogItemAsControl(item)
        if onoff:
            ctl.ActivateControl()
        else:
            ctl.DeactivateControl()

class EnterkeyDialog(windowinterface.MACDialog):
    def __init__(self, ok_callback, user='', org='', license=''):
        windowinterface.MACDialog.__init__(self, "License", ID_DIALOG_ENTERKEY,
                        ITEMLIST_ENTERKEY_ALL, cancel=ITEM_CANCEL, default=ITEM_OK)
        self.ok_callback = ok_callback
        self._setlabel(ITEM_NAME, user)
        self._setlabel(ITEM_ORGANIZATION, org)
        self._setlabel(ITEM_KEY, license)
        self.setdialoginfo()
        self.show()

    def close(self):
        del self.ok_callback
        windowinterface.MACDialog.close(self)

    def setdialoginfo(self):
##         nameok = self._getlabel(ITEM_NAME) or self._getlabel(ITEM_ORGANIZATION)
        keyok = self._getlabel(ITEM_KEY)
        self._setsensitive([ITEM_OK], keyok)

    def do_itemhit(self, n, event):
        if n == ITEM_OK:
            name = self._getlabel(ITEM_NAME)
            org = self._getlabel(ITEM_ORGANIZATION)
            key = self._getlabel(ITEM_KEY)
            self.ok_callback(key, name, org)
            self.close()
        elif n == ITEM_CANCEL:
            self.close()
        elif n in (ITEM_NAME, ITEM_ORGANIZATION, ITEM_KEY):
            self.setdialoginfo()
        else:
            print "Unknown EnterkeyItem", n
        return 1
