# License handling code, dummy for now
import string
import sys

FEATURES={
	"save": 1,
	"editdemo": 2,
	"player":4,
}

MAGIC=13

Error="license.error"

NOTYET="Not licensed yet"

class Features:
	def __init__(self, license, args):
		self.license = license
		self.args = args

	def __del__(self):
		apply(self.license._release, self.args)
		del self.license
		del self.args
	
class License:
	def __init__(self, features):
		"""Obtain a license, and state that we need at least one
		of the features given"""
		self.__available_features, self.__licensee = \
					   _getlicense()
		for f in features:
			if self.have(f):
				break
		else:
			raise Error, "License not valid for this program"
		

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

class WaitLicense:
	def __init__(self, callback, features):
		self.callback = callback
		self.features = features
		self.secondtime = 0
		self.dialog = None
		if self.get_or_ask():
			self.do_callback()

	def get_or_ask(self):
		try:
			self.license = License(self.features)
		except Error, arg:
			import windowinterface
			if self.secondtime or arg != NOTYET:
				windowinterface.showmessage("%s\nSee www.oratrix.com for details."%arg)
			self.secondtime = 1
			self.dialog = windowinterface.InputDialog(
				'Enter license key:',
				'',
				self.ok_callback,
				(self.cancel_callback, ()))
			return 0
		return 1

	def cancel_callback(self):
		import sys
		if sys.platform=='win32':
			import windowinterface
			windowinterface.forceclose()
		else:
			sys.exit(0)

	def ok_callback(self, str):
		import settings
		import sys
		if sys.platform!='win32':
			del self.dialog
		settings.set('license', str)
		if self.get_or_ask():
			# The license appears ok. Save it.
			if not settings.save():
				windowinterface.showmessage(
					'Cannot save license, sorry...')
			self.do_callback()

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

def _getlicense():
	"""Obtain the license information"""
	str = ''
	try:
		import staticlicense
	except ImportError:
		pass
	else:
		if 'staticlicense' in dir(staticlicense):
			str = staticlicense.staticlicense
	if not str:
		import settings
		str = settings.get('license')
	if not str:
		raise Error, NOTYET
	uniqid, date, features, user = _decodelicense(str)
	if date:
		import time
		t = time.time()
		values = time.localtime(t)
		if values[:3] > date:
			raise Error, "License expired %d/%02.2d/%02.2d"%date
		if not user:
			user = "Temporary license until %d/%02.2d/%02.2d"%date
## 		import windowinterface
## 		msg = 'Temporary license, valid until %d/%02.2d/%02.2d.\n'%date
## 		msg = msg + 'Do you want to replace it with a full license?'
## 		ok = windowinterface.showquestion(msg)
## 		if ok:
## 			raise Error, ""
	fnames = []
	for name, value in FEATURES.items():
		if (features & value) == value:
			fnames.append(name)
	return fnames, user
