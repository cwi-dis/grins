# License handling code, dummy for now
import string
import sys
from LicenseDialog import LicenseDialog

FEATURES={
	"save": 1,
	"editor": 1,	# Synonym
	"editdemo": 2,
	"player":4,
}

MAGIC=13

Error="license.error"

NOTYET="Not licensed yet"
EXPIRED="Your evaluation copy has expired"

class Features:
	def __init__(self, license, args):
		self.license = license
		self.args = args

	def __del__(self):
		apply(self.license._release, self.args)
		del self.license
		del self.args
	
class License:
	def __init__(self, features, newlicense=None):
		"""Obtain a license, and state that we need at least one
		of the features given"""
		if newlicense:
			lic = newlicense
		else:
			import settings
			lic = settings.get('license')
		self.__available_features, self.__licensee, self.__moredays = \
					   _parselicense(lic)
		for f in features:
			if self.have(f):
				break
		else:
			raise Error, "License not valid for this program"
			
		self.msg = ""
		if type(self.__moredays) == type(0):
			if self.__moredays < 0:
				raise Error, EXPIRED
			self.msg = "Evaluation copy, %d more days left"%self.__moredays
		if newlicense:
			import settings
			settings.set('license', newlicense)
			if not settings.save():
				import windowinterface
				windowinterface.showmessage(
					'Cannot save license! (File permission problems?)')

	def have(self, *features):
		"""Check whether we have the given features"""
		for f in features:
			if not f in self.__available_features:
				return 0
		return 1

	def need(self, *features):
		"""Obtain a locked license for the given features.
		The features are released when the returned object is
		freed"""
		if not apply(self.have, features):
			raise Error, "Required license feature not available"
		return Features(self, features)

	def userinfo(self):
		"""If this license is personal return the user name/company"""
		return self.__licensee

	def _release(self, features):
		pass

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
			
	def accept_license(self, newlicense=None):
		try:
			self.license = License(self.features, newlicense)
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
		if sys.platform=='win32':
			import windowinterface
			windowinterface.forceclose()
		else:
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
		import windowinterface
		windowinterface.InputDialog("Enter key:", "", self.ok_callback, (self.cb_quit, ()))

	def ok_callback(self, str):
		import settings
		import sys
		self.accept_license(str)
		self.setdialoginfo()

	def do_callback(self):
		license = self.license
		callback = self.callback
		del self.license
		del self.callback
		callback(license)

_CODEBOOK="ABCDEFGHIJKLMNOPQRSTUVWXYZ012345"
_DECODEBOOK={}
for _ch in range(len(_CODEBOOK)):
	_DECODEBOOK[_CODEBOOK[_ch]] = _ch

def _decodeint(str):
	value = 0
	shift = 0
	for ch in str:
		try:
			next = _DECODEBOOK[ch]
		except KeyError:
			raise Error, "Invalid license"
		value = value | (next << shift)
		shift = shift + 5
	return value

def _decodestr(str):
	rv = ''
	if (len(str)&1):
		raise Error, "Invalid license"
	for i in range(0, len(str), 2):
		rv = rv + chr(_decodeint(str[i:i+2]))
	return rv

def _decodedate(str):
	if len(str) != 5:
		raise Error, "Invalid license"
	yyyy= _decodeint(str[0:3])
	mm = _decodeint(str[3])
	dd = _decodeint(str[4])
	if yyyy < 3000:
		return yyyy, mm, dd
	return None

def _codecheckvalue(items):
	value = 1L
	fullstr = string.join(items, '')
	for i in range(len(fullstr)):
		thisval = (MAGIC+ord(fullstr[i])+i)
		value = value * thisval + ord(fullstr[i]) + i
	return int(value & 0xfffffL)

def _decodelicense(str):
	all = string.split(str, '-')
	check = all[-1]
	all = all[:-1]
	if not len(all) in (4,5) or all[0] != 'A':
		raise Error, "Invalid license"
	if _codecheckvalue(all) != _decodeint(check):
		raise Error, "Invalid license"
	uniqid = _decodeint(all[1])
	date = _decodedate(all[2])
	features = _decodeint(all[3])
	if len(all) > 4:
		user = _decodestr(all[4])
	else:
		user = ""
	return uniqid, date, features, user

def _parselicense(str):
	if not str:
		raise Error, ""
	uniqid, date, features, user = _decodelicense(str)
	if user:
		user = "Licensed to: " + user
	if date:
		import time
		t = time.time()
		values = time.localtime(t)
		today = mkdaynum(values[:3])
		expiry = mkdaynum(date)
		moredays = expiry - today
		if moredays == 0:
			moredays = 1	# Don't want to return zero
	fnames = []
	for name, value in FEATURES.items():
		if (features & value) == value:
			fnames.append(name)
	return fnames, user, moredays

def mkdaynum((year, month, day)):
	import calendar
	# Januari 1st, in 0 A.D. is arbitrarily defined to be day 1,
	# even though that day never actually existed and the calendar
	# was different then...
	days = year*365			# years, roughly
	days = days + (year+3)/4	# plus leap years, roughly
	days = days - (year+99)/100	# minus non-leap years every century
	days = days + (year+399)/400	# plus leap years every 4 centirues
	for i in range(1, month):
		if i == 2 and calendar.isleap(year):
			days = days + 29
		else:
			days = days + calendar.mdays[i]
	days = days + day
	return days
	
