# License dialog
import string
import sys
from licparser import *
from LicenseDialog import LicenseDialog, EnterkeyDialog


class WaitLicense(LicenseDialog):
	def __init__(self, callback, features):
		self.can_try = 0
		self.can_eval = 0
		
		self.callback = callback
		self.features = features
		self.secondtime = 0
		self.dialog = None
		if self.accept_license():
			self.do_callback()
		else:
			LicenseDialog.__init__(self)
			self.setdialoginfo()
			self.show()
			
	def accept_license(self, newlicense=None, user="", organization=""):
		try:
			self.license = License(self.features, newlicense, user, organization)
			if not self.license.msg:
				return 1	# Everything fine, permanent license
			# Evaluation license 
			self.msg = self.license.msg
			self.can_try = 1
			self.can_eval = 0
		except Error, arg:
			self.msg = arg
			self.can_try = 0
			if arg == EXPIRED:
				self.can_eval = 0
			else:
				self.can_eval = 1
		return 0

	def cb_quit(self):
		self.close()
		import sys
		sys.exit(0)
			
	def cb_try(self):
		self.close()
		self.do_callback()
		
	def cb_buy(self):
		import Help
		Help.givehelp('buy')
		
	def cb_eval(self):
		import Help
		Help.givehelp('eval')
		
	def cb_enterkey(self):
##		import windowinterface
##		windowinterface.InputDialog("Enter key:", "", self.ok_callback, (self.cb_quit, ()))
		import settings
		EnterkeyDialog(self.ok_callback, user=settings.get('license_user'), org=settings.get('license_organization'))

	def ok_callback(self, str, name=None, organization=None):
		str = string.strip(str)
		if self.accept_license(str, name, organization):
			self.close()
			self.do_callback()
		else:
			self.setdialoginfo()

	def do_callback(self):
		license = self.license
		callback = self.callback
		del self.license
		del self.callback
		callback(license)
