__version__ = "$Id$"

from urllib import *
import os
if os.name == 'mac':
	import ic
	import macfs
	try:
		_mac_icinstance = ic.IC()
	except:
		_mac_icinstance = None
	
	def _mac_setcreatortype(filename):
		if not _mac_icinstance:
			return
		try:
			# Get current creator/type of the file
			fss = macfs.FSSpec(filename)
			cr, tp = fss.GetCreatorType()
			# Check whether actual type matches expected type.
			# XXXX Note: the mapping here is done on filename extension.
			# it would be better to do it on the basis of the mimetype, but
			# IC doesn't have that interface.
			descr = _mac_icinstance.mapfile(filename)
			wtd_tp = descr[1]
			wtd_cr = descr[2]
			if tp == wtd_tp:
				return
			# They're different. Try setting it correctly.
			fss.SetCreatorType(wtd_cr, wtd_tp)
		except:
			# Any errors are ignored.
			pass

_OriginalFancyURLopener = FancyURLopener

_end_loop = '_end_loop'
class FancyURLopener(_OriginalFancyURLopener):
	def __init__(self, *args):
		apply(_OriginalFancyURLopener.__init__, (self,) + args)
		self.tempcache = {}

	def http_error_default(self, url, fp, errcode, errmsg, headers):
		void = fp.read()
		fp.close()
		raise IOError, (errcode, 'http error: ' + errmsg, headers)

	def retrieve(self, url, filename=None, reporthook=None):
		filename, headers = _OriginalFancyURLopener.retrieve(self, url, filename, reporthook)
		if os.name == 'mac':
			_mac_setcreatortype(filename)
		return filename, headers
    			
	def http_error_302(self, url, fp, errcode, errmsg, headers):
		# XXX The server can force infinite recursion here!
		if headers.has_key('location'):
			newurl = headers['location']
		elif headers.has_key('uri'):
			newurl = headers['uri']
		else:
			return
		void = fp.read()
		fp.close()
		fp = self.open(newurl)
		h = fp.info()
		if not h.has_key('Content-Location') and \
		   not h.has_key('Content-Base'):
			h.dict['content-location'] = newurl
			h.headers.append('Content-Location: %s\r\n' % newurl)
		return fp

	def prompt_user_passwd(self, host, realm):
		import windowinterface
		try:
			w = windowinterface.Window('passwd', grab = 1)
		except AttributeError:
			return _OriginalFancyURLopener.prompt_user_passwd(self, host, realm)
		l = w.Label('Enter username and password for %s at %s' % (realm, host))
		t1 = w.TextInput('User:', '', None, (self.usercb, ()),
				 top = l, left = None, right = None)
		t2 = w.TextInput('Passwd:', '', None, (self.passcb, ()),
				 modifyCB = self.modifycb,
				 top = t1, left = None, right = None)
		b = w.ButtonRow([('OK', (self.do_return, ())),
				 ('Cancel', (self.cancelcb, ()))],
				vertical = 0,
				top = t2, left = None, right = None, bottom = None)
		self.userw = t1
		self.passwdw = t2
		self.passwd = []
		self.user = ''
		self.password = ''
		w.show()
		try:
			windowinterface.mainloop()
		except _end_loop:
			pass
		w.hide()
		w.close()
		del self.userw, self.passwdw
		return self.user, self.password

	def modifycb(self, text):
		if text:
			if text == '\b':
				if self.passwd:
					del self.passwd[-1]
				return ''
			self.passwd.append(text)
			return '*' * len(text)

	def usercb(self):
		self.user = self.userw.gettext()
		if self.password:
			self.do_return()
		else:
			self.passwdw.setfocus()

	def passcb(self):
		self.password = string.joinfields(self.passwd, '')
		if self.user:
			self.do_return()
		else:
			self.userw.setfocus()

	def cancelcb(self):
		self.user = self.password = None
		self.do_return()

	def do_return(self):
		raise _end_loop

_urlopener = None
def urlopen(url, data=None):
	global _urlopener
	if not _urlopener:
		_urlopener = FancyURLopener()
	if data is None:
		return _urlopener.open(url)
	else:
		return _urlopener.open(url, data)
def urlretrieve(url, filename=None):
	global _urlopener
	if not _urlopener:
		_urlopener = FancyURLopener()
	if filename:
		return _urlopener.retrieve(url, filename)
	else:
		return _urlopener.retrieve(url)
def urlcleanup():
	if _urlopener:
		_urlopener.cleanup()

import urlparse
basejoin = urlparse.urljoin # urljoin works better...
del urlparse

def guessurl(filename):
	import os
	# convert filename to URL
	utype, url = splittype(filename)
	if utype is not None and utype in ('http', 'file', 'ftp', 'rtsp'):
		# definitely a URL
		return filename
	if os.sep in filename:
		# probably a file name
		return pathname2url(filename)
	# possibly a relative URL
	return filename

_pathname2url = pathname2url
def pathname2url(path):
	url = _pathname2url(path)
	type, rest = splittype(url)
	if not type and rest[:1] == '/':
		if rest[:3] == '///':
			url = 'file:' + url
		else:
			url = 'file://' + url
	return url

def canonURL(url):
	type, rest = splittype(url)
	if not type or type == 'file':
		# if no type it's a file URL
		if rest[:1] != '/':
			# make absolute pathname
			import os
			url = canonURL(basejoin(pathname2url(os.getcwd())+'/',rest))
		elif rest[:3] == '///':
			url = 'file:' + rest
		else:
			url = 'file://' + rest
	return url
