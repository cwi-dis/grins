# License dialog
import windowinterface


class LicenseDialog:
	def __init__(self):
		pass

	def show(self):
		pass
		
	def close(self):
		pass
			
	def setdialoginfo(self):
		if self.can_try:
			self.cb_try()
		else:
			self.cb_enterkey()
