#
# XXXX This is an initial stab at a HTML channel.
#
from Channel import ChannelWindow
from AnchorDefs import *
from debug import debug
import string
import HTML
import MMAttrdefs
import sys
import windowinterface
import urllib

if windowinterface.Version <> 'X':
	print 'HtmlChannel: Cannot work without X (use CMIF_USE_X=1)'
	raise ImportError

class HtmlChannel(ChannelWindow):

	def init(self, name, attrdict, scheduler, ui):
		self = ChannelWindow.init(self, name, attrdict, scheduler, ui)
		self.want_default_colormap = 1
		self.htmlw = None
		if name[0] >= 'A' and name[0] <= 'Z':
			print 'HtmlChannel: Uppercase names are prone to disappointing results'
		return self

	def do_show(self):
		#
		# Step 1 - Show the base window. This creates a drawingArea
		# that we don't use (except as a parent), but it doesn't harm
		# us either.
		#
		print 'DOSHOW'
		if not ChannelWindow.do_show(self):
			return 0
		print 'DOIESHOW'
		#
		# Step 2 - Create a values dictionary with width/height
		# for use when we create the HTML widget.
		#
		wd = self.window
		print 'WINDOW=', wd
		wh = wd._form.GetValues(['width', 'height'])
		print 'GO FOR IT'
		#
		# Create the widget
		#
		self.htmlw = self.window._form.CreateManagedWidget('h', HTML.html, wh)
		#
		# Set callbacks.
		#
		self.htmlw.AddCallback('anchorCallback', self.cbanchor, None)
		self.htmlw.AddCallback('submitFormCallback', self.cbform, None)
		return 1

	def resize(self, arg, window, event, value):
		# XXXX For reasons unknown, this one does not seem to work...
		print 'RESIZE'
		wh = self.window._form.GetValues(['width', 'height'])
		self.htmlw._form.SetValues(wh)
		

	def __repr__(self):
		return '<HtmlChannel instance, name=' + `self._name` + '>'

	def updatefixedanchors(self, node):
		if self._armstate != AIDLE:
			raise error, 'Arm state must be idle when defining an anchor'
		if self._playstate != PIDLE:
			raise error, 'Play state must be idle when defining an anchor'
		windowinterface.setcursor('watch')
		context = AnchorContext().init()
		self.startcontext(context)
		self.syncarm = 1
		self.arm(node)
		self.syncplay = 1
		self.play(node)
		self._playstate = PLAYED
		self.syncarm = 0
		self.syncplay = 0
		return 1

	def seekanchor(self, node, aid, args):
		windowinterface.showmessage('JUMP:'+`aid`+`args`)
		
	def do_arm(self, node):
		print 'DO_ARM'
		self.armed_str = self.getstring(node)
		return 1
		
	def do_play(self, node):
		print 'DO_PLAY'
		self.url = self.armed_url
		print 'URL=', self.url
		arg = {'text': self.armed_str, 'headerText':'',
		       'footerText':''}
		self.htmlw.SetValues(arg)
		self.fixanchorlist(node)
		self.play_node = node

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


	def defanchor(self, node, anchor):
		# Anchors don't get edited in the HtmlChannel.  You
		# have to edit the text to change the anchor.  We
		# don't want a message, though, so we provide our own
		# defanchor() method.
		return anchor

	def cbanchor(self, widget, userdata, calldata):
		if widget <> self.htmlw:
			raise 'kaboo kaboo'
		rawevent, elid, text, href = HTML.anchor_cbarg(calldata)
		print 'ANCHORFIRED', (elid, text, href)
		if href[:5] <> 'cmif:':
			self.www_jump(href, 'GET', None, None)
			return
		self.cbcmifanchor(href, None)

	def cbform(self, widget, userdata, calldata):
		if widget <> self.htmlw:
			raise 'kaboo kaboo'
		rawevent, href, method, enctype, list = \
			  HTML.form_cbarg(calldata)
		print 'FORMFIRED', (href, method, enctype, list)
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
		print 'FIXANCHORLIST'
		allanchorlist = HTML.GetHRefs(self.htmlw)
		print len(allanchorlist), 'anchors'
		anchorlist = []
		for a in allanchorlist:
			if a[:5] == 'cmif:':
				anchorlist.append(a[5:])
		print len(anchorlist), 'cmif-anchors'
		if len(anchorlist) == 0:
			return
		nodeanchorlist = MMAttrdefs.getattr(node, 'anchorlist')[:]
		oldanchorlist = map(lambda x:x[0], nodeanchorlist)
		newanchorlist = []
		for a in anchorlist:
			if a not in oldanchorlist:
				newanchorlist.append(a)
		if not newanchorlist:
			print 'Nothing to fix'
			return
		for a in newanchorlist:
			print 'Add anchor', a
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
			return
		href = urljoin(self.url, href)
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
		self.htmlw.footerText = '<P>[<A HREF="'+self.armed_url+\
			  '">BACK</A> to CMIF node]<P>'

#
# Given a base URL and a HREF return the URL of the new document
#
def urljoin(base, href):
	print 'urljoin', (base, href)
	type, path = urllib.splittype(href)
	if type:
		print '->', href
		return href
	host, path = urllib.splithost(path)
	basetype, basepath = urllib.splittype(base)
	basehost, basepath = urllib.splithost(basepath)
	type = basetype or 'file'
	if path[:1] != '/':
		i = string.rfind(basepath, '/')
		if i < 0: basepath = '/'
		else: basepath = basepath[:i+1]
		path = basepath + path
	if not host: host = basehost
	if host:
		print '->',type + '://' + host + path
		return type + '://' + host + path
	else:
		print '->', type + ':' + path
		return type + ':' + path

def addquery(href, list):
	if not list: return href
	if len(list) == 1 and list[0][0] == 'isindex':
		query = list[0][1]
	else:
		list = map(lambda x:x[0]+'='+x[1], list)
		query = string.joinfields(list, '&')
	href = href + '?' + query
	return href

#
# Get the data-behind-the-URL
#
def urlget(newurl):
	return urllib.urlopen(newurl).read()
