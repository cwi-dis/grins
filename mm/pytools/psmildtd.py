import fxmllib, urllib

class FancyURLopener(urllib.FancyURLopener):
	def prompt_user_passwd(self, host, realm):
		"""Override this in a GUI environment!"""
		import getpass, sys
		try:
			stdout = sys.stdout
			try:
				sys.stdout = sys.stderr
				user = raw_input("Enter username for %s at %s: " % (realm,
										    host))
				passwd = getpass.getpass("Enter password for %s in %s at %s: " %
							 (user, realm, host))
			finally:
				sys.stdout = stdout
			return user, passwd
		except KeyboardInterrupt:
			print
			return None, None

# Shortcut for basic usage
_urlopener = None
def urlopen(url, data=None):
	"""urlopen(url [, data]) -> open file-like object"""
	global _urlopener
	if not _urlopener:
		_urlopener = FancyURLopener()
	if data is None:
		return _urlopener.open(url)
	else:
		return _urlopener.open(url, data)

class SMILParser(fxmllib.XMLParser):
	def read_external(self, name):
		import urllib
		if type(name) is type(unicode('a')):
			name = name.encode('latin-1')
		u = urlopen(name)
		data = u.read()
		u.close()
		return data

import string, time

def main(dtd = "http://www.w3.org/AudioVideo/Group/DTD/SMIL20.dtd"):
	x = SMILParser()
	try:
		x.parse('''<?xml version="1.0" encoding="latin-1" standalone="no"?>
<!DOCTYPE smil PUBLIC "-//W3C//DTD SMIL 2.0//EN" "%s">
<smil xmlns="http://www.w3.org/2000/SMIL20/CR/Language"/>
''' % dtd)
	except fxmllib.Error, info:
		print str(info)
		if info.text is not None and info.offset is not None:
			i = string.rfind(info.text, '\n', 0, info.offset) + 1
			j = string.find(info.text, '\n', info.offset)
			if j == -1: j = len(info.offset)
			print info.text[i:j]
			print ' '*(info.offset-i)+'^'
		return

	elems = x.elems.keys()
	elems.sort()
	if string.find(dtd, 'SMIL20.dtd') >= 0:
		title = 'SMIL 2.0 Language Profile DTD'
	elif string.find(dtd, 'SMIL20Basic.dtd') >= 0:
		title = 'SMIL 2.0 Basic Language Profile DTD'
	else:
		title = 'Unknown DTD'
	print '<html><head><title>%s</title></head><body>' % title
	print '<table border="1" width="100%">'
	print '<caption>'
	print '%s<br>' % title
	print '%s<br>' % dtd
	print 'Last modified: %s' % time.strftime('%a, %e %b %Y, %T %Z', time.localtime(time.time()))
	print '</caption>'
	for elem in elems:
		dfa, attrs, start, end, content = x.elems[elem]
		if type(elem) is type(unicode('a')):
			elem = elem.encode('latin-1')
		if type(content) is type(unicode('a')):
			content = content.encode('latin-1')
		content = string.join(string.split(content,'|'), ' | ')
		content = string.join(string.split(content,','), ', ')
		attrnames = attrs.keys()
		attrnames.sort()
		print '<tr>'
		print '<td rowspan="%d" valign="top"><strong><a name="%s">%s</a></strong></td>' % (len(attrnames)+1, elem, elem)
		print '<td colspan="3" align="justify"><em>%s</em></td>' % content
		print '</tr>'
		for attr in attrnames:
			atype, default, atstring = attrs[attr]
			if type(attr) is type(unicode('a')):
				attr = attr.encode('latin-1')
			if type(atype) is type([]):
				atype = '(' + string.join(atype, ' | ') + ')'
			if type(atype) is type(unicode('a')):
				atype = atype.encode('latin-1')
			if type(default) is type(unicode('a')):
				default = default.encode('latin-1')
			print '<tr><td>%s</td><td>%s</td><td>%s</td></tr>' % (attr, atype, default)
	print '</table></body></html>'

if __name__ == '__main__':
	import sys
	if len(sys.argv) > 1:
		main(sys.argv[1])
	else:
		main()
