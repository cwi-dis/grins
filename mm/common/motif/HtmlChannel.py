__version__ = "$Id$"

#
# XXXX This is an initial stab at a HTML channel.
#
import Channel
import string
import HTML
import MMAttrdefs
from MMExc import *
import sys
import windowinterface
import XHtml
import MMurl
import urlparse
from TextChannel import getfont, mapfont
import parsehtml
try:
	import Xrm
	has_xrm = 1
except ImportError:
	has_xrm = 0

error = 'HtmlChannel.error'

HtmlWidgets = {}

def actionhook(widget, client_data, action, event, plist):
	if widget.Class() is not Xm.DrawingArea or \
	   widget.Parent().Class() is not HTML.html:
		return
	ch = HtmlWidgets.get(widget.Parent())
	if ch is None:
		return
	ch.actionhook(client_data, action, event, plist)

import Xt, Xm
Xt.AddActionHook(actionhook, None)

class HtmlChannel(Channel.ChannelWindow):
	chan_attrs = Channel.ChannelWindow.chan_attrs + ['fgcolor']

	def __init__(self, name, attrdict, scheduler, ui):
		Channel.ChannelWindow.__init__(self, name, attrdict, scheduler, ui)
		self.want_default_colormap = 1
		self.htmlw = None
		self.play_node = None
		self.widget_name = normalize(name)
		self.backlist = []

	def do_show(self, pchan):
		#
		# Step 1 - Show the base window. This creates a drawingArea
		# that we don't use (except as a parent), but it doesn't harm
		# us either.
		#
		if not Channel.ChannelWindow.do_show(self, pchan):
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
		HtmlWidgets[self.htmlw] = self
		#
		# Set callbacks.
		#
		self.htmlw.AddCallback('anchorCallback', self.cbanchor, None)
		self.htmlw.AddCallback('submitFormCallback', self.cbform, None)
		self.htmlw.AddCallback('destroyCallback', self.cbdestroy, None)
		self.htmlw.AddCallback('linkCallback', self.cblink, None)

	def actionhook(self, cbarg, action, event, plist):
		if not self.play_node:
			return
		if not self.played_anchor:
			return
		if action == 'select-start':
			self.x = event.x
			self.y = event.y
			self.time = event.time
			return
		if action == 'extend-end':
			if not self.time:
				return
			if event.time - self.time >= 500:
				self.time = None
				return
			a = self.played_anchor
			self.anchor_triggered(self.play_node,
					      [(a.aid, a.atype)],
					      None)
		if action == 'extend-adjust':
			self.time = None
			return

	def cbdestroy(self, widget, userdata, calldata):
		del HtmlWidgets[widget]
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

	def do_arm(self, node, same=0):
		if not same:
			try:
				self.armed_str = self.getstring(node)
			except Channel.error, arg:
				self.armed_str = '<H1>Cannot Open</H1>\n'+arg+'\n<P>\n'
		if self._is_shown and not self.htmlw:
			self._after_creation()
		self.armed_anchor = None
		anchors = {}
		for c in node.GetSchedChildren():
			if c.GetType() != 'anchor':
				continue
			fragment = MMAttrdefs.getattr(c, 'fragment')
			if not fragment:
				continue
			if anchors.has_key(fragment):
				print 'fragment',fragment,'used in multiple anchors'
				# ignore all but first
			else:
				anchors[fragment] = c.GetUID()
		parser = parsehtml.Parser(anchors)
		parser.feed(self.armed_str)
		self.armed_str = parser.close()
		return 1

	_boldfonts = [('boldFont', 9.0),
		      ('header1Font', 15.5),
		      ('header2Font', 11.7),
		      ('header3Font', 11.0),
		      ('header4Font', 9.0),
		      ('header5Font', 7.8),
		      ('header6Font', 6.5)]

	def do_play(self, node, curtime):
		htmlw = self.htmlw
		self.played_url = self.url = self.armed_url
		utype, host, path, params, query, tag = urlparse.urlparse(self.url)
		self.played_str = self.armed_str
		self.played_anchor = self.armed_anchor
		self.backlist = []
		attrs = {}
		fontspec = getfont(node)
		fontname, pointsize = mapfont(fontspec)
		fontobj = windowinterface.findfont(fontname, 9)
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
		bg = self.played_display._gcattr.get('background')
		if bg is None:
			bg = self.window._convert_color((255,255,255))
		fg = self.played_display._gcattr['foreground']
		htmlw.ChangeColor(bg)
		attrs['background'] = bg
		attrs['foreground'] = fg
		attrs['anchorColor'] = self.window._convert_color(self.gethicolor(node))
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
		htmlw.SetText(self.played_str, '', '', 0, tag)
		htmlw.MapWidget()
		htmlw.UpdateDisplay()
		self.play_node = node

	def stopplay(self, node, curtime):
		if node.GetType() == 'anchor':
			self.stop_anchor(node, curtime)
			return
		Channel.ChannelWindow.stopplay(self, node, curtime)
		if self.htmlw:
			self.htmlw.UnmapWidget()
			self.htmlw.SetText('', '', '')
			self.play_node = None
			self.played_str = ''

	def defanchor(self, node, anchor, cb):
		# Anchors don't get edited in the HtmlChannel.  You
		# have to edit the text to change the anchor.  We
		# don't want a message, though, so we provide our own
		# defanchor() method.
		apply(cb, (anchor,))

	def cbanchor(self, widget, userdata, calldata):
		if widget is not self.htmlw:
			raise 'kaboo kaboo'
		if self.played_anchor:
			return
		href = calldata.href
		if href[:5] != 'cmif:':
			self.www_jump(href, 'GET', None, None)
		else:
			i = string.find(href, '?')
			if i > 0:
				list = map(lambda x:tuple(string.splitfields(x,'=',1)),
					   string.splitfields(href[i+1:], '&'))
				href = href[:i]
			else:
				list = None
			self.cbcmifanchor(href, list)
		try:
			# if this exists, we need it
			widget.SetAppSensitive()
		except TypeError:
			pass
		windowinterface.toplevel.setready()

	def cbform(self, widget, userdata, calldata):
		if widget is not self.htmlw:
			raise 'kaboo kaboo'
		if self.played_anchor:
			return
		href = calldata.href
		list = map(None,
			   calldata.attribute_names, calldata.attribute_values)
		if not href or href[:5] != 'cmif:':
			self.www_jump(href, calldata.method,
				      calldata.enctype, list)
		else:
			self.cbcmifanchor(href, list)
		windowinterface.toplevel.setready()

	def cbcmifanchor(self, href, list):
		uid = href[5:]
		try:
			node = self.play_node.GetContext().mapuid(uid)
		except:
			self.errormsg(self.play_node, 'Unknown anchor: '+uid)
			return
		# XXX we're losing the list arg here
		self.onclick(node)

	def resolveImage(self, widget, src, noload = 0):
		src = MMurl.basejoin(self.url, src)
		return XHtml.resolveImage(widget, src, noload)

	#
	# The stuff below has little to do with CMIF per se, it implements
	# a general www browser
	#
	footer = '<HR><A HREF="XXXX:play/node">BACK</A> to CMIF node<BR>\n' \
		 '<A HREF="XXXX:back">PREVIOUS</A> node'

	def www_jump(self, href, method, enctype, list):
		#
		# Check that we understand what is happening
		if method is not None:
			method = string.upper(method)
		if enctype is not None:
			print 'HtmlChannel: unknown enctype:', enctype
			return
		data = None
		href, tag = MMurl.splittag(href)
		if not href:
			if tag:
				self.htmlw.GotoId(self.htmlw.AnchorToId(tag))
			return
		if href == 'XXXX:back':
			if len(self.backlist) > 1:
				href, tag, data = self.backlist[-2]
				del self.backlist[-2:]
				self.url = ''
			else:
				href = 'XXXX:play/node'
		if href == 'XXXX:play/node':
			self.backlist = []
			self.url = self.played_url
			url, tag = MMurl.splittag(self.played_url)
			self.htmlw.SetText(self.played_str, '', '', 0, tag)
			return
		href = MMurl.basejoin(self.url, href)
		utype, rest = MMurl.splittype(href)
		if method not in (None, 'GET') and \
		   (utype != 'http' or method != 'POST'):
			print 'HtmlChannel: unknown method:', method
			print 'href:', href
			print 'method:', method
			print 'enctype:', enctype
			print 'list:', list
			return
		self._player.toplevel.setwaiting()
		if list:
			if method == 'POST':
				data = mkquery(list)
			else:
				href = addquery(href, list)
		self.url = href
		self.backlist.append((href, tag, data))
		try:
			fn, hdrs = MMurl.urlretrieve(href, data)
		except IOError:
			newtext = '<H1>Cannot Open</H1><P>'+ \
				  'Cannot open '+self.url+':<P>'+ \
				  `(sys.exc_type, sys.exc_value)`+ \
				  '<P>\n'
		else:
			if hdrs.has_key('Content-Location'):
				self.url = hdrs['Content-Location']
				self.backlist[-1] = self.url, tag, data
			if hdrs.type != 'text/html':
				import Hlinks
				anchor = self.url
				if tag:
					anchor = anchor + '#' + tag
				self._player.topleve.waspaused = 0
				self._player.toplevel.jumptoexternal(anchor, Hlinks.TYPE_JUMP)
				return
			else:
				newtext = open(fn, 'rb').read()
		self.htmlw.SetText(newtext, None, self.footer, 0, tag)

def addquery(href, list):
	if not list: return href
	query = mkquery(list)
	href = href + '?' + query
	return href

def mkquery(list):
	if len(list) == 1 and list[0][0] == 'isindex':
		query = encodestring(list[0][1])
	else:
		list = map(encodequery, list)
		list = map(lambda x:x[0]+'='+x[1], list)
		query = string.joinfields(list, '&')
	return query

def encodequery(query):
	name, value = query
	name = encodestring(name)
	value = encodestring(value)
	return (name, value)

def encodestring(s):
	return MMurl.quote(s or '')	# Catches None as well!

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
## 	if newname != name:
## 		print 'HtmlChannel: "%s" has resource name "%s"'%(
## 			name, newname)
	return newname
