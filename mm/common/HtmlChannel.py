#
# XXXX This is an initial stab at a HTML channel.
#
import Channel
from AnchorDefs import *
import string
import HTML
import MMAttrdefs
import sys
import windowinterface
import urllib

if windowinterface.Version <> 'X':
	print 'HtmlChannel: Cannot work without X (use CMIF_USE_X=1)'
	raise ImportError

error = 'HtmlChannel.error'

class HtmlChannel(Channel.ChannelWindow):

        # HTML Channels get colorized thru X resources.
	# XXXX Hope this doesn't break any Channel.py code...
        node_attrs = Channel.ChannelWindow.node_attrs[:]
	node_attrs.remove('bgcolor')
	node_attrs.remove('hicolor')

	def __init__(self, name, attrdict, scheduler, ui):
		Channel.ChannelWindow.__init__(self, name, attrdict, scheduler, ui)
		self.want_default_colormap = 1
		self.htmlw = None
		self.widget_name = normalize(name)

	def do_show(self):
		#
		# Step 1 - Show the base window. This creates a drawingArea
		# that we don't use (except as a parent), but it doesn't harm
		# us either.
		#
		if not Channel.ChannelWindow.do_show(self):
			return 0

		if self.window:
			self._after_creation()
		return 1

	def _after_creation(self):
		#
		# Step 2 - Create a values dictionary with width/height
		# for use when we create the HTML widget.
		#
		wd = self.window
		wh = wd._form.GetValues(['width', 'height'])
		wh['visual'] = wd._visual
		#
		# Create the widget
		#
		self.htmlw = self.window._form.CreateManagedWidget(
			self.widget_name, HTML.html, wh)
		#
		# Set callbacks.
		#
		self.htmlw.AddCallback('anchorCallback', self.cbanchor, None)
		self.htmlw.AddCallback('submitFormCallback', self.cbform, None)
		self.htmlw.AddCallback('destroyCallback', self.cbdestroy, None)

	def cbdestroy(self, widget, userdata, calldata):
		self.htmlw = None

	def _box_callback(self, *pgeom):
		if pgeom:
			x, y, w, h = pgeom
			Channel.ChannelWindow._box_callback(self, x, y, w, h)
		else:
			Channel.ChannelWindow._box_callback(self)
		self._after_creation()

	def resize(self, arg, window, event, value):
		wh = self.window._form.GetValues(['width', 'height'])
		self.htmlw.SetValues(wh)
		

	def __repr__(self):
		return '<HtmlChannel instance, name=' + `self._name` + '>'

	def updatefixedanchors(self, node):
		if self._armstate != Channel.AIDLE or \
		   self._playstate != Channel.PIDLE:
			if self._played_node == node:
				# Ok, all is well, we've played it.
				return 1
			windowinterface.showmessage('Cannot recompute anchorlist (channel busy)')
			return 1
		windowinterface.setcursor('watch')
		context = Channel.AnchorContext()
		self.startcontext(context)
		self.syncarm = 1
		self.arm(node)
		self.syncplay = 1
		self.play(node)
		self.stopplay(node)
		self.syncarm = 0
		self.syncplay = 0
		windowinterface.setcursor('')
		return 1

#	def seekanchor(self, node, aid, args):
#		windowinterface.showmessage('JUMP:'+`aid`+`args`)
		
	def do_arm(self, node):
		self.armed_str = self.getstring(node)
		if self._is_shown and not self.htmlw:
			self._after_creation()
		return 1
		
	def do_play(self, node):
		self.url = self.armed_url
		arg = {'text': self.armed_str, 'headerText':'',
		       'footerText':''}
		self.htmlw.SetValues(arg)
		self.fixanchorlist(node)
		self.play_node = node

	def stopplay(self, node):
		Channel.ChannelWindow.stopplay(self, node)
		self.htmlw.SetValues({'text': '', 'headerText':'',
				      'footerText':''})

	def getstring(self, node):
		if node.type == 'imm':
			self.armed_url = ''
			return string.joinfields(node.GetValues(), '\n')
		elif node.type == 'ext':
			filename = self.getfilename(node)
			self.armed_url = filename
			try:
				fp = urllib.urlopen(filename)
			except IOError:
				return '<H1>Cannot Open</H1><P>'+ \
					  'Cannot open '+filename+':<P>'+ \
					  `(sys.exc_type, sys.exc_value)`+ \
					  '<P>\n'
			text = fp.read()
			fp.close()
			if text[-1:] == '\n':
				text = text[:-1]
			return text
		else:
			raise CheckError, \
				'gettext on wrong node type: ' +`node.type`


	def defanchor(self, node, anchor, cb):
		# Anchors don't get edited in the HtmlChannel.  You
		# have to edit the text to change the anchor.  We
		# don't want a message, though, so we provide our own
		# defanchor() method.
		apply(cb, (anchor,))

	def cbanchor(self, widget, userdata, calldata):
		if widget <> self.htmlw:
			raise 'kaboo kaboo'
		rawevent, elid, text, href = HTML.anchor_cbarg(calldata)
		if href[:5] <> 'cmif:':
			self.www_jump(href, 'GET', None, None)
			return
		self.cbcmifanchor(href, None)

	def cbform(self, widget, userdata, calldata):
		if widget <> self.htmlw:
			raise 'kaboo kaboo'
		rawevent, href, method, enctype, list = \
			  HTML.form_cbarg(calldata)
		if not href or href[:5] <> 'cmif:':
			self.www_jump(href, method, enctype, list)
			return
		self.cbcmifanchor(href, list)

	def cbcmifanchor(self, href, list):
		aname = href[5:]
		tp = self.findanchortype(aname)
		if tp == None:
			windowinterface.showmessage('Unknown CMIF anchor: '+aname)
			return
		if tp == ATYPE_PAUSE:
			f = self.pauseanchor_triggered
		else:
			f = self.anchor_triggered
		f(self.play_node, [(aname, tp)], list)

	def findanchortype(self, name):
		alist = MMAttrdefs.getattr(self.play_node, 'anchorlist')
		for aid, atype, args in alist:
			if aid == name:
				return atype
		return None

	def fixanchorlist(self, node):
		allanchorlist = HTML.GetHRefs(self.htmlw)
		anchorlist = []
		for a in allanchorlist:
			if a[:5] == 'cmif:':
				anchorlist.append(a[5:])
		if len(anchorlist) == 0:
			return
		nodeanchorlist = MMAttrdefs.getattr(node, 'anchorlist')[:]
		oldanchorlist = map(lambda x:x[0], nodeanchorlist)
		newanchorlist = []
		for a in anchorlist:
			if a not in oldanchorlist:
				newanchorlist.append(a)
		if not newanchorlist:
			return
		for a in newanchorlist:
			nodeanchorlist.append(a, ATYPE_NORMAL, [])
		node.SetAttr('anchorlist', nodeanchorlist)
		MMAttrdefs.flushcache(node)

	#
	# The stuff below has little to do with CMIF per se, it implements
	# a general www browser
	#
	def www_jump(self, href, method, enctype, list):
		#
		# Check that we understand what is happening
		if enctype <> None:
			print 'HtmlChannel: unknown enctype:', enctype
			return
		if method not in (None, 'GET'):
			print 'HtmlChannel: unknown method:', method
			print 'href:', href
			print 'method:', method
			print 'enctype:', enctype
			print 'list:', list
			return
		if href:
			href = urllib.basejoin(self.url, href)
		else:
			href = self.url
		if list:
			href = addquery(href, list)
		self.url, tag = urllib.splittag(href)
		try:
			newtext = urlget(self.url)
		except IOError:
			newtext = '<H1>Cannot Open</H1><P>'+ \
				  'Cannot open '+self.url+':<P>'+ \
				  `(sys.exc_type, sys.exc_value)`+ \
				  '<P>\n'
		self.htmlw.text = newtext
##		self.htmlw.footerText = '<P>[<A HREF="'+self.armed_url+\
##			  '">BACK</A> to CMIF node]<P>'

def addquery(href, list):
	if not list: return href
	if len(list) == 1 and list[0][0] == 'isindex':
		query = encodestring(list[0][1])
	else:
		list = map(encodequery, list)
		list = map(lambda x:x[0]+'='+x[1], list)
		query = string.joinfields(list, '&')
	href = href + '?' + query
	return href

def encodequery(query):
	name, value = query
	name = encodestring(name)
	value = encodestring(value)
	return (name, value)

def encodestring(s):
	if not s: return ''		# Catches None as well!
	r = ''
	for c in s:
		r = r + encoding[c]
	return r

encoding = {}
for i in range(256):
	encoding[chr(i)] = '%%%02X' % i
for c in string.letters + string.digits + ',.-_':
	encoding[c] = c
encoding[' '] = '+'

#
# Get the data-behind-the-URL
#
def urlget(newurl):
	return urllib.urlopen(newurl).read()

#
# Turn a CMIF channel name into a name acceptable for an X widget
#
def normalize(name):
	# Step one - remove everything except letters and digits
	newname = ''
	for c in name:
		if not c in string.letters + string.digits:
			c = ' '
		newname = newname + c
	# Split in words
	words = string.split(newname)
	# uncapitalize first word
	word = words[0]
	newname = string.lower(word[0]) + word[1:]
	# capitalize other words
	for word in words[1:]:
		word = string.upper(word[0]) + word[1:]
		newname = newname + word
	if newname <> name:
		print 'HtmlChannel: "%s" has resource name "%s"'%(
			name, newname)
	return newname
	
