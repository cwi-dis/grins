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
ITEM_BALLOONHELP=8 # NOT YET

ITEMLIST_ALL=ITEMrange(ITEM_SPLASH, ITEM_BALLOONHELP)

class LicenseDialog(windowinterface.MACDialog):
	def __init__(self):
		windowinterface.MACDialog.__init__(self, "License", ID_DIALOG_LICENSE,
				ITEMLIST_ALL, cancel=ITEM_QUIT)
			
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
			
	def _optenable(self, onoff, item):
		tp, h, rect = self.dialog.GetDialogItem(item)
		ctl = h.as_Control()
		if onoff:
			ctl.HiliteControl(0)
		else:
			ctl.HiliteControl(255)
