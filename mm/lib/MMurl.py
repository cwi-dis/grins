from urllib import *

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

	# Error 301 -- also relocated (permanently)
	http_error_301 = http_error_302

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
		b = w.ButtonRow([('Cancel', (self.cancelcb, ()))],
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
