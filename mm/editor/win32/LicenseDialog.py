# License dialog
import windowinterface
import components
import grinsRC
import win32con

class LicenseDialog(components.ResDialog):
	def __init__(self):
		components.ResDialog.__init__(self, grinsRC.IDD_LICENSE)

		self.__enabled = {}

		self.__label = components.Static(self,grinsRC.IDC_MESSAGE)		

		self.__quit = components.Button(self,win32con.IDCANCEL)
		self.__buy = components.Button(self,grinsRC.IDUC_BUY)
		self.__eval = components.Button(self,grinsRC.IDUC_EVALLICENSE)
		self.__enterkey = components.Button(self,grinsRC.IDUC_ENTERKEY)
		self.__try = components.Button(self,win32con.IDOK)

		self.__initialized = 0

	def OnInitDialog(self):
		self.attach_handles_to_subwindows()
		self.__quit.hookcommand(self, self.On_quit)
		self.__buy.hookcommand(self, self.On_buy)
		self.__eval.hookcommand(self, self.On_eval)
		self.__enterkey.hookcommand(self, self.On_enterkey)
		self.__try.hookcommand(self, self.On_try)
		rv = components.ResDialog.OnInitDialog(self)
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

	# Callback glue methods.

	def On_quit(self, id, code):
		self.cb_quit()

	def On_buy(self, id, code):
		self.cb_buy()

	def On_eval(self, id, code):
		self.cb_eval()

	def On_enterkey(self, id, code):
		self.cb_enterkey()

	def On_try(self, id, code):
		self.cb_try()
