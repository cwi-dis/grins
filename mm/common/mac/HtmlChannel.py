__version__ = "$Id$"

#
# Macintosh HTML channel.
#
import Channel
import string
import MMAttrdefs
import sys
import windowinterface
import MMurl
import urlparse
import htmlwidget
from TextChannel import getfont, mapfont
import WMEVENTS

error = 'HtmlChannel.error'

class HtmlChannel(Channel.ChannelWindow):
	chan_attrs = Channel.ChannelWindow.chan_attrs + ['fgcolor']

	def __init__(self, name, attrdict, scheduler, ui):
		Channel.ChannelWindow.__init__(self, name, attrdict, scheduler, ui)
		self.want_default_colormap = 1
		self.htmlw = None
		self.played_str = ()

	def do_show(self, pchan):
		#
		# Step 1 - Show the base window. 
		#
		if not Channel.ChannelWindow.do_show(self, pchan):
			return 0

		if self.window:
			self._after_creation()
		return 1

	def do_hide(self):
		if self.htmlw:
			self.htmlw.close()
			self.htmlw = None
		self.window.unregister(WMEVENTS.WindowActivate)
		self.window.unregister(WMEVENTS.WindowDeactivate)
		self.window.setredrawfunc(None)
		self.window.setclickfunc(None)
		Channel.ChannelWindow.do_hide(self)

	def _after_creation(self):
		#
		# Step 2 - Create a values dictionary with width/height
		# for use when we create the HTML widget.
		#
		wd = self.window
		#
		# Create the widget
		#
		self.htmlw = htmlwidget.HTMLWidget(wd._mac_getoswindow(), wd.qdrect(), self._name)
		bg = wd._bgcolor
		fg = wd._fgcolor
		an = fg # Not needed anyway, and we have to provide something...
		self.htmlw.setcolors(bg, fg, an)
		#
		# Set callbacks.
		#
		wd.setredrawfunc(self.redraw)
		wd.setclickfunc(self.click)
		wd.register(WMEVENTS.WindowActivate, self.activate, 0)
		wd.register(WMEVENTS.WindowDeactivate, self.deactivate, 0)
		self.htmlw.setanchorcallback(self.cbanchor)
##		self.htmlw.AddCallback('submitFormCallback', self.cbform, None)
##		self.htmlw.AddCallback('destroyCallback', self.cbdestroy, None)
##		self.htmlw.AddCallback('linkCallback', self.cblink, None)

	def redraw(self, rgn=None):
		# rgn (region to be redrawn, None for everything) ignored for now
		if self.htmlw:
			self.htmlw.do_update()
			
	def click(self, down, where, event):
		if self.htmlw:
			self.htmlw.do_click(down, where, event)
	
	def activate(self, *args):
		if self.htmlw:
			self.htmlw.do_activate()
			
	def deactivate(self, *args):
		if self.htmlw:
			self.htmlw.do_deactivate()
			
	def resize(self, arg, window, event, value):
		wd = self.window
		self.htmlw.do_moveresize(wd.qdrect())
		

	def __repr__(self):
		return '<HtmlChannel instance, name=' + `self._name` + '>'

	def do_arm(self, node, same=0):
		if not same:
			try:
				self.armed_str = self.getstring(node)
			except Channel.error, arg:
				self.armed_str = '<H1>Cannot Open</H1>\n'+arg+'\n<P>\n'
		if self._is_shown and not self.htmlw:
			self._after_creation()
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

##	_boldfonts = [('boldFont', 9.0),
##		      ('header1Font', 15.5),
##		      ('header2Font', 11.7),
##		      ('header3Font', 11.0),
##		      ('header4Font', 9.0),
##		      ('header5Font', 7.8),
##		      ('header6Font', 6.5)]
	
	def do_play(self, node, curtime):
		htmlw = self.htmlw
		self.played_url = self.url = self.armed_url
		utype, host, path, params, query, tag = urlparse.urlparse(self.url)
		self.played_str = self.armed_str

		fontspec = getfont(node)
		fontname, pointsize = mapfont(fontspec)
		fontobj = windowinterface.findfont(fontname, pointsize)
		num, face, size = fontobj._getinfo()
		htmlw.setfonts(num, None, size)

		bg = self.played_display._bgcolor
		fg = self.played_display._fgcolor
		an = self.window._convert_color(self.gethicolor(node))
		htmlw.setcolors(bg, fg, an)
		
		htmlw.insert_html(self.played_str, self.url, tag)
		self.play_node = node

	def stopplay(self, node, curtime):
		if node.GetType() == 'anchor':
			self.stop_anchor(node, curtime)
			return
		Channel.ChannelWindow.stopplay(self, node, curtime)
		if self.htmlw:
			self.htmlw.insert_html('', '')
			
	def defanchor(self, node, anchor, cb):
		# Anchors don't get edited in the HtmlChannel.  You
		# have to edit the text to change the anchor.  We
		# don't want a message, though, so we provide our own
		# defanchor() method.
		apply(cb, (anchor,))

	def cbanchor(self, href):
		if href[:5] <> 'cmif:':
			self.www_jump(href, 'GET', None, None)
			return
		self.cbcmifanchor(href, None)

	def cbform(self, widget, userdata, calldata):
		if widget <> self.htmlw:
			raise 'kaboo kaboo'
		href = calldata.href
		list = map(lambda a,b: (a,b),
			   calldata.attribute_names, calldata.attribute_values)
		if not href or href[:5] <> 'cmif:':
			self.www_jump(href, calldata.method,
				      calldata.enctype, list)
			return
		self.cbcmifanchor(href, list)

	def cbcmifanchor(self, href, list):
		uid = href[5:]
		try:
			node = self.play_node.GetContext().mapuid(uid)
		except:
			self.errormsg(self.play_node, 'Unknown anchor: '+uid)
			return
		# XXX we're losing the list arg here
		self.onclick(node)

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
			if href == 'XXXX:play/node':
				self.htmlw.insert_html(self.played_str, self.played_url)
				self.url = self.played_url
				return
			href = MMurl.basejoin(self.url, href)
		else:
			href = self.url
		if list:
			href = addquery(href, list)
		utype, host, path, params, query, tag = urlparse.urlparse(href)
		self.url = urlparse.urlunparse((utype, host, path, params, query, ''))
		## XXXX do something with the tag
		try:
			u = MMurl.urlopen(self.url)
## Old code:
##			if u.headers.maintype == 'image':
##				newtext = '<IMG SRC="%s">\n' % self.url
##			else:
##				newtext = u.read()
## New code:
			if u.headers.type != 'text/html':
				import Hlinks
				anchor = self.url
				if tag:
					anchor = anchor + '#' + tag
				self._player.toplevel.waspaused = 0
				self._player.toplevel.jumptoexternal(anchor, Hlinks.TYPE_JUMP)
				return
			newtext = u.read()
		except IOError:
			newtext = '<H1>Cannot Open</H1><P>'+ \
				  'Cannot open '+self.url+':<P>'+ \
				  `(sys.exc_type, sys.exc_value)`+ \
				  '<P>\n'
		footer = '<HR>[<A HREF="XXXX:play/node">BACK</A> to CMIF node]'
		self.htmlw.insert_html(newtext+footer, self.url)
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
	return MMurl.quote(s or '')	# Catches None as well!
