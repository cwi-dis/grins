import fxmllib, urllib, re

namere = re.compile(fxmllib._Name)

toc = 0				# produce Table of Contents in HTML table

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

import time

def prdtdtable(x, dtd):
	elems = x.elems.keys()
	elems.sort()
	if dtd.find('SMIL20.dtd') >= 0:
		title = 'SMIL 2.0 Language Profile DTD'
	elif dtd.find('SMIL20Basic.dtd') >= 0:
		title = 'SMIL 2.0 Basic Language Profile DTD'
	else:
		title = 'Unknown DTD'
	print '<html><head><title>%s</title></head><body>' % title
	if toc:
		print '<h1>%s</h1>' % title
		print '<h2>%s</h2>' % dtd
		print '<p>Last modified: %s</p>' % time.strftime('%a, %e %b %Y, %T %Z', time.localtime(time.time()))
		print '<h3>Table of Contents</h3>'
		print '<ul>'
		for elem in elems:
			print '<li><a href="#%s">%s</a></li>' % (elem, elem)
		print '</ul>'
	print '<table border="1" width="100%">'
	if not toc:
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
		content = ' | '.join(content.split('|'))
		content = ', '.join(content.split(','))
		pos = 0
		while 1:
			res = namere.search(content, pos)
			if res is None:
				break
			name = res.group(0)
			if x.elems.has_key(name):
				a = '<a href="#%s">%s</a>' % (name, name)
				content = content[:res.start(0)] + a + content[res.end(0):]
				pos = res.start(0) + len(a)
			else:
				pos = res.end(0)
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
				atype = '(' + ' | '.join(atype) + ')'
			if type(atype) is type(unicode('a')):
				atype = atype.encode('latin-1')
			if type(default) is type(unicode('a')):
				default = default.encode('latin-1')
			print '<tr><td>%s</td><td>%s</td><td>%s</td></tr>' % (attr, atype, default)
	print '</table></body></html>'

def prdtd(x, dtd):
	taglist = x.elems.keys()
	taglist.sort()
	for tag in taglist:
		nfa, attrdict, start, end, content = x.elems[tag]
		print '<!ELEMENT %s %s>' % (tag.encode('utf-8'), content.encode('utf-8'))
		print '<!ATTLIST %s' % tag.encode('utf-8')
		attrlist = attrdict.keys()
		attrlist.sort()
		for attr in attrlist:
			attype, atvalue, atstring = attrdict[attr]
			if type(attype) is type([]):
				attype = u'(' + u'|'.join(attype) + u')'
			if atstring is None:
				atstring = u''
			print '\t%s %s %s' % (attr.encode('utf-8'), attype.encode('utf-8'), atvalue.encode('utf-8'))
		print '>'

def main(dtd = "http://www.w3.org/2001/SMIL20/SMIL20.dtd", func = prdtdtable):
	x = fxmllib.CheckXMLParser()
	try:
		x.parse('''<?xml version="1.0" standalone="no"?>
<!DOCTYPE smil PUBLIC "-//W3C//DTD SMIL 2.0//EN" "%s">
<smil xmlns="http://www.w3.org/2001/SMIL20/Language"/>
''' % dtd)
	except fxmllib.Error, info:
		print str(info)
		if info.text is not None and info.offset is not None:
			i = info.text.rfind('\n', 0, info.offset) + 1
			j = info.text.find('\n', info.offset)
			if j == -1: j = len(info.text)
			print info.text[i:j]
			print ' '*(info.offset-i)+'^'
		return
	func(x, dtd)

if __name__ == '__main__':
	import sys, getopt

	opts, args = getopt.getopt(sys.argv[1:], 'dtc')
	if ('-d','') in opts:
		func = prdtd
	else:
		func = prdtdtable
	if ('-c', '') in opts:
		toc = 1
	if len(args) > 0:
		main(args[0], func = func)
	else:
		main(func = func)
