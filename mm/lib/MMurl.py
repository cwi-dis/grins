__version__ = "$Id$"

from urllib import *

_OriginalFancyURLopener = FancyURLopener

_end_loop = '_end_loop'
class FancyURLopener(_OriginalFancyURLopener):
	def __init__(self, *args):
		apply(_OriginalFancyURLopener.__init__, (self,) + args)
		self.tempcache = {}

		# prefetch support
		self.__prefetchcache = {}
		self.__prefetchtempfiles = {}

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

	#
	# Prefetch section
	#
	# override retrieve for prefetch implementation
	def retrieve(self, url, filename=None, reporthook=None):
		"""retrieve(url) returns (filename, None) for a local object
		or (tempfilename, headers) for a remote object."""
		url = unwrap(url)
		if self.__prefetchcache.has_key(url):
			# complete prefetch first
			#print 'completing prefetch'
			self.__fin_retrieve(url)
		if self.__prefetchtempfiles.has_key(url):
			#print 'retrieving prefetched',self.__prefetchtempfiles[url]
			return self.__prefetchtempfiles[url]
		return _OriginalFancyURLopener.retrieve(self, url, filename, reporthook)

	# override cleanup for prefetch implementation
	def cleanup(self):
		for url, value in self.__prefetchcache:
			fp, tfp = value
			fp.close()
			tfp.close()
			if self.__prefetchtempfiles.has_key(url):
				os.unlink(self.__prefetchtempfiles[url])
		self.__prefetchcache = {}
		self.__prefetchtempfiles = {}
		_OriginalFancyURLopener.cleanup()
	
	# see retrieve for sign
	def begin_retrieve(self, url, filename=None, reporthook=None):
		url = unwrap(url)
		self.__clean_retrieve(url)
		type, url1 = splittype(url)
		if not filename and (not type or type == 'file'):
			try:
				fp = self.open_local_file(url1)
				hdrs = fp.info()
				del fp
				return url2pathname(splithost(url1)[1]), hdrs
			except IOError, msg:
				pass
		fp = self.open(url)
		headers = fp.info()
		if not filename:
			import tempfile
			garbage, path = splittype(url)
			garbage, path = splithost(path or "")
			path, garbage = splitquery(path or "")
			path, garbage = splitattr(path or "")
			suffix = os.path.splitext(path)[1]
			filename = tempfile.mktemp(suffix)
			self.__prefetchtempfiles[url] = filename
		tfp = open(filename, 'wb')
		self.__prefetchcache[url] = fp, tfp
		return filename, headers
	
	def do_retrieve(self, url, bs):
		if not self.__prefetchcache.has_key(url):
			return None
		fp, tfp = self.__prefetchcache[url]
		block = fp.read(bs)
		if block:
			tfp.write(block)
		return block!=None

	def end_retrieve(self, url):
		if not self.__prefetchcache.has_key(url):
			return None
		fp, tfp = self.__prefetchcache[url]
		del self.__prefetchcache[url]
		fp.close()
		tfp.close()

	def __fin_retrieve(self, url):
		if not self.__prefetchcache.has_key(url):
			return None
		fp, tfp = self.__prefetchcache[url]
		bs = 1024*8
		block = fp.read(bs)
		print 'read block'
		while block:
			tfp.write(block)
			block = fp.read(bs)
		del self.__prefetchcache[url]
		fp.close()
		tfp.close()

	def __clean_retrieve(self, url):
		if self.__prefetchtempfiles.has_key(url):
			file = self.__prefetchtempfiles[url]
			try:
				os.unlink(file)
			except:
				pass
			del self.__prefetchtempfiles[url]
		if self.tempcache and self.tempcache.has_key(url):
			# unlink will be called on __tempfiles on close
			del self.tempcache[url]

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
def geturlopener():
	global _urlopener
	if not _urlopener:
		_urlopener = FancyURLopener()
	return _urlopener

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
