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
from TextChannel import getfont, mapfont
try:
	import Xrm
	has_xrm = 1
except ImportError:
	has_xrm = 0

if windowinterface.Version <> 'X':
	print 'HtmlChannel: Cannot work without X (use CMIF_USE_X=1)'
	raise ImportError

error = 'HtmlChannel.error'

class HtmlChannel(Channel.ChannelWindow):
	node_attrs = Channel.ChannelWindow.node_attrs + ['bucolor', 'hicolor',
							 'fgcolor', 'font']

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

	def do_hide(self):
		if self.htmlw:
			self.htmlw.DestroyWidget()
		Channel.ChannelWindow.do_hide(self)

	def _after_creation(self):
		#
		# Step 2 - Create a values dictionary with width/height
		# for use when we create the HTML widget.
		#
		wd = self.window
		try:
			x, y, w, h = wd._rect
		except AttributeError:
			wh = wd._form.GetValues(['width', 'height'])
			wh['visual'] = wd._visual
		else:
			wh = {'width': w, 'height': h, 'x': x, 'y': y,
			      'visual': wd._topwindow._visual}
		wh['mappedWhenManaged'] = 0
		wh['resolveImageFunction'] = self.resolveImage
		wh['resolveDelayedImage'] = self.resolveImage
		#
		# Create the widget
		#
		self.htmlw = wd._form.CreateManagedWidget(
			self.widget_name, HTML.html, wh)
		#
		# Set callbacks.
		#
		self.htmlw.AddCallback('anchorCallback', self.cbanchor, None)
		self.htmlw.AddCallback('submitFormCallback', self.cbform, None)
		self.htmlw.AddCallback('destroyCallback', self.cbdestroy, None)
		self.htmlw.AddCallback('linkCallback', self.cblink, None)

	def cbdestroy(self, widget, userdata, calldata):
		widget.FreeImageInfo()
		if widget is self.htmlw:
			self.htmlw = None

	def cblink(self, widget, userdata, calldata):
		href = calldata.href
		if href:
			self.url = href

	def _box_callback(self, *pgeom):
		if pgeom:
			x, y, w, h = pgeom
			Channel.ChannelWindow._box_callback(self, x, y, w, h)
		else:
			Channel.ChannelWindow._box_callback(self)
		self._after_creation()

	def resize(self, arg, window, event, value):
		wd = self.window
		try:
			x, y, w, h = wd._rect
		except AttributeError:
			wh = wd._form.GetValues(['width', 'height'])
		else:
			wh = {'width': w, 'height': h, 'x': x, 'y': y}
		self.htmlw.SetValues(wh)
		

	def __repr__(self):
		return '<HtmlChannel instance, name=' + `self._name` + '>'

	def updatefixedanchors(self, node):
		if self._armstate != Channel.AIDLE or \
		   self._playstate != Channel.PIDLE:
			if self._played_node is node:
				# Ok, all is well, we've played it.
				return 1
			if self.window:
				grab = self.window
			else:
				grab = 1
			windowinterface.showmessage('Cannot recompute anchorlist (channel busy)', grab = grab)
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
		
	def do_arm(self, node, same=0):
	        if not same:
			self.armed_str = self.getstring(node)
		if self._is_shown and not self.htmlw:
			self._after_creation()
		return 1

	_boldfonts = [('boldFont', 9.0),
		      ('header1Font', 15.5),
		      ('header2Font', 11.7),
		      ('header3Font', 11.0),
		      ('header4Font', 9.0),
		      ('header5Font', 7.8),
		      ('header6Font', 6.5)]
	
	def do_play(self, node):
		import Xm
		htmlw = self.htmlw
		self.played_url = self.url = self.armed_url
		self.played_str = self.armed_str
		attrs = {}
		fontspec = getfont(node)
		fontname, pointsize = mapfont(fontspec)
		fontobj = windowinterface.findfont(fontname, 9)
		attrs['font'] = fontobj._font
		i = string.find(fontname, '-')
		if i > 0: fontname = fontname[:i]
		basefontname = fontname
		fontname = fontname + '-Bold'
		for attr, pointsize in self._boldfonts:
			fontobj = windowinterface.findfont(fontname, pointsize)
			attrs[attr] = fontobj._font
		fontname = basefontname + '-Italic'
		try:
			fontobj = windowinterface.findfont(fontname, 9)
		except windowinterface.error:
			fontname = basefontname + '-Oblique'
			fontobj = windowinterface.findfont(fontname, 9)
		attrs['italicFont'] = fontobj._font
		bg = self.played_display._gcattr['background']
		fg = self.played_display._gcattr['foreground']
		htmlw.ChangeColor(bg)
		attrs['background'] = bg
		attrs['foreground'] = fg
		attrs['anchorColor'] = self.window._convert_color(self.getbucolor(node))
		attrs['activeAnchorFG'] = self.window._convert_color(self.gethicolor(node))
		attrs['activeAnchorBG'] = bg
		htmlw.SetValues(attrs)
		for w in htmlw.children:
			w.background = bg
			w.ChangeColor(bg)
			w.foreground = fg
			if w.Class() is Xm.ScrollBar:
				w.troughColor = bg
		if has_xrm:
			db = htmlw.ScreenDatabase()
			db.PutStringResource(
				'*%s*background' % self.widget_name,
				'#%02x%02x%02x' % self.getbgcolor(node))
			db.PutStringResource(
				'*%s*foreground' % self.widget_name,
				'#%02x%02x%02x' % self.getfgcolor(node))
		htmlw.SetText(self.armed_str, '', '')
		htmlw.MapWidget()
		htmlw.UpdateDisplay()
		self.fixanchorlist(node)
		self.play_node = node

	def stopplay(self, node):
		Channel.ChannelWindow.stopplay(self, node)
		if self.htmlw:
			self.htmlw.UnmapWidget()
			self.htmlw.SetText('', '', '')

	def getstring(self, node):
		if node.type == 'imm':
			self.armed_url = ''
			return string.joinfields(node.GetValues(), '\n')
		elif node.type == 'ext':
			filename = self.getfileurl(node)
			self.armed_url = filename
			try:
				fp = urlopen(filename)
			except IOError:
				return '<H1>Cannot Open</H1><P>'+ \
					  'Cannot open '+filename+':<P>'+ \
					  `(sys.exc_type, sys.exc_value)`+ \
					  '<P>\n'
			self.armed_url = fp.geturl()
			# use undocumented feature so we can cleanup
			if _urlopener.tempcache is None:
				_urlopener.tempcache = {}
				# cleanup temporary files when we finish
				windowinterface.addclosecallback(
					urlcleanup, ())
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
		if widget is not self.htmlw:
			raise 'kaboo kaboo'
		href = calldata.href
		if href[:5] <> 'cmif:':
			self.www_jump(href, 'GET', None, None)
			return
		self.cbcmifanchor(href, None)

	def cbform(self, widget, userdata, calldata):
		if widget is not self.htmlw:
			raise 'kaboo kaboo'
		href = calldata.href
		list = map(None,
			   calldata.attribute_names, calldata.attribute_values)
		if not href or href[:5] <> 'cmif:':
			self.www_jump(href, calldata.method,
				      calldata.enctype, list)
			return
		self.cbcmifanchor(href, list)

	def cbcmifanchor(self, href, list):
		aname = href[5:]
		tp = self.findanchortype(aname)
		if tp is None:
			windowinterface.showmessage('Unknown CMIF anchor: '+aname, grab = self.window)
			return
		if tp == ATYPE_PAUSE:
			f = self.pause_triggered
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
		allanchorlist = self.htmlw.GetHRefs()
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
		if enctype is not None:
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
			if href == 'XXXX:play/node':
				self.url = self.played_url
				self.htmlw.SetText(self.played_str, '', '')
				return
			href = urllib.basejoin(self.url, href)
		else:
			href = self.url
		self._player.toplevel.setwaiting()
		if list:
			href = addquery(href, list)
		self.url, tag = urllib.splittag(href)
		try:
			u = urlopen(self.url)
			if u.headers.maintype == 'image':
				newtext = '<IMG SRC="%s">\n' % self.url
			else:
				newtext = u.read()
		except IOError:
			newtext = '<H1>Cannot Open</H1><P>'+ \
				  'Cannot open '+self.url+':<P>'+ \
				  `(sys.exc_type, sys.exc_value)`+ \
				  '<P>\n'
		footer = '<HR>[<A HREF="XXXX:play/node">BACK</A> to CMIF node]'
		self.htmlw.SetText(newtext, None, footer, 0, tag)
##		self.htmlw.footerText = '<P>[<A HREF="'+self.armed_url+\
##			  '">BACK</A> to CMIF node]<P>'
		self._player.toplevel.setready()

	def resolveImage(self, widget, src, noload = 0):
		import X
		src = urllib.basejoin(self.url, src)
		try:
			return image_cache[src]
		except KeyError:
			pass
		if noload:
			return None
		try:
			filename, info = urlretrieve(src)
		except IOError:
			return None
		import img, imgformat
		visual = widget.visual
		if visual.c_class == X.TrueColor and visual.depth == 8:
			format = windowinterface.toplevel.myxrgb8
		else:
			format = imgformat.xcolormap
		try:
			reader = img.reader(format, filename)
		except:
			return
		if hasattr(reader, 'transparent') and hasattr(reader, 'colormap'):
			reader.colormap[reader.transparent] = windowinterface.toplevel._colormap.QueryColor(widget.background)[1:4]
		if format is imgformat.xcolormap:
			colors = map(None, reader.colormap)
		else:
			colors = range(256)
			colors = map(None, colors, colors, colors)
		dict = {'width': reader.width, 'height': reader.height,
			'image_data': reader.read(), 'colors': colors}
		image_cache[src] = dict
		return dict

image_cache = {}

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
	return urllib.quote(s or '')	# Catches None as well!

#
# Get the data-behind-the-URL
#
def urlget(newurl):
	return urlopen(newurl).read()

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

_end_loop = '_end_loop'
class HtmlUrlOpener(urllib.FancyURLopener):
	def prompt_user_passwd(self, host, realm):
		try:
			w = windowinterface.Window('passwd', grab = 1)
		except AttributeError:
			return urllib.FancyURLopener.prompt_user_passwd(self, host, realm)
		import Xt
		l = w.Label('Enter username and password for %s at %s' % (realm, host))
		t1 = w.TextInput('User:', '', None, (self.usercb, ()),
				 top = l, left = None, right = None)
		t2 = w.TextInput('Passwd:', '', None, (self.passcb, ()),
				 top = t1, left = None, right = None)
		b = w.ButtonRow([('Cancel', (self.cancelcb, ()))],
				vertical = 0,
				top = t2, left = None, right = None, bottom = None)
		t2._text.AddCallback('modifyVerifyCallback', self.modifycb, None)
		self.userw = t1
		self.passwdw = t2
		self.passwd = []
		self.user = ''
		self.password = ''
		w.show()
		self.looping = 1
		while self.looping:
			Xt.DispatchEvent(Xt.NextEvent())
		w.hide()
		w.close()
		del self.userw, self.passwdw
		return self.user, self.password

	def modifycb(self, w, client_data, call_data):
		if call_data.text:
			if call_data.text == '\b':
				if self.passwd:
					del self.passwd[-1]
				call_data.text = ''
				return
			self.passwd.append(call_data.text)
			call_data.text = '*' * len(call_data.text)

	def usercb(self):
		self.user = self.userw.gettext()
		if self.password:
			self.do_return()
		else:
			import Xmd
			self.passwdw._text.ProcessTraversal(Xmd.TRAVERSE_CURRENT)

	def passcb(self):
		self.password = string.joinfields(self.passwd, '')
		if self.user:
			self.do_return()
		else:
			import Xmd
			self.userw._text.ProcessTraversal(Xmd.TRAVERSE_CURRENT)

	def cancelcb(self):
		self.user = self.password = None
		self.do_return()

	def do_return(self):
		self.looping = 0

_urlopener = None
def urlopen(url):
	global _urlopener
	if not _urlopener:
		_urlopener = HtmlUrlOpener()
	return _urlopener.open(url)

def urlretrieve(url, filename = None):
	global _urlopener
	if not _urlopener:
		_urlopener = HtmlUrlOpener()
	if filename:
		return _urlopener.retrieve(url, filename)
	else:
		return _urlopener.retrieve(url)

def urlcleanup():
	if _urlopener:
		_urlopener.cleanup()
