from urllib import *

_OriginalFancyURLopener = FancyURLopener

_end_loop = '_end_loop'
class FancyURLopener(_OriginalFancyURLopener):
	def __init__(self, *args):
		apply(_OriginalFancyURLopener.__init__, (self,) + args)
		self.tempcache = {}

	def open_data(self, url, data=None):
		# ignore POSTed data
		#
		# syntax of data URLs:
		# dataurl   := "data:" [ mediatype ] [ ";base64" ] "," data
		# mediatype := [ type "/" subtype ] *( ";" parameter )
		# data      := *urlchar
		# parameter := attribute "=" value
		import StringIO, mimetools, time
		try:
			[type, data] = string.split(url, ',', 1)
		except ValueError:
			raise IOError, ('data error', 'bad data URL')
		if not type:
			type = 'text/plain;charset=US-ASCII'
		semi = string.rfind(type, ';')
		if semi >= 0 and '=' not in type[semi:]:
			encoding = type[semi+1:]
			type = type[:semi]
		else:
			encoding = ''
		msg = []
		msg.append('Date: %s'%time.strftime('%a, %d %b %Y %T GMT',
						    time.gmtime(time.time())))
		msg.append('Content-type: %s' % type)
		if encoding == 'base64':
			import base64
			data = base64.decodestring(data)
		else:
			data = unquote(data)
		msg.append('Content-length: %d' % len(data))
		msg.append('')
		msg.append(data)
		msg = string.join(msg, '\n')
		f = StringIO.StringIO(msg)
		headers = mimetools.Message(f, 0)
		f.fileno = None		# needed for addinfourl
		return addinfourl(f, headers, url)

	def http_error_default(self, url, fp, errcode, errmsg, headers):
		void = fp.read()
		fp.close()
		raise IOError, (errcode, 'http error: ' + errmsg, headers)

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
