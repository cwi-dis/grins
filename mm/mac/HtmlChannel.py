__version__ = "$Id$"

#
# Macintosh HTML channel.
#
import Channel
from AnchorDefs import *
import string
import MMAttrdefs
import sys
import windowinterface
import urllib
import htmlwidget
from TextChannel import getfont, mapfont
import WMEVENTS

error = 'HtmlChannel.error'

class HtmlChannel(Channel.ChannelWindow):
	node_attrs = Channel.ChannelWindow.node_attrs + ['fgcolor', 'font']

	def __init__(self, name, attrdict, scheduler, ui):
		Channel.ChannelWindow.__init__(self, name, attrdict, scheduler, ui)
		self.want_default_colormap = 1
		self.htmlw = None

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
		self.htmlw = htmlwidget.HTMLWidget(wd._wid, wd.qdrect(), self._name)
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

	def redraw(self):
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
		save_syncarm = self.syncarm
		self.syncarm = 1
		self.arm(node)
		save_synplay = self.syncplay
		self.syncplay = 1
		self.play(node)
		self.stopplay(node)
		self.syncarm = save_syncarm
		self.syncplay = save_synplay
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

##	_boldfonts = [('boldFont', 9.0),
##		      ('header1Font', 15.5),
##		      ('header2Font', 11.7),
##		      ('header3Font', 11.0),
##		      ('header4Font', 9.0),
##		      ('header5Font', 7.8),
##		      ('header6Font', 6.5)]
	
	def do_play(self, node):
		htmlw = self.htmlw
		self.played_url = self.url = self.armed_url
		self.played_str = self.armed_str

		fontspec = getfont(node)
		fontname, pointsize = mapfont(fontspec)
		fontobj = windowinterface.findfont(fontname, pointsize)
		num, face, size = fontobj._getinfo()
		htmlw.setfonts(num, None, size)

		bg = self.played_display._bgcolor
		fg = self.played_display._fgcolor
		an = self.window._convert_color(self.getbucolor(node))
		htmlw.setcolors(bg, fg, an)

		htmlw.insert_html(self.played_str, self.url)
		self.fixanchorlist(node)
		self.play_node = node

	def stopplay(self, node):
		Channel.ChannelWindow.stopplay(self, node)
		if self.htmlw:
			self.htmlw.insert_html('', '')
			
	def getstring(self, node):
		self.armed_url = ''
		if node.type == 'imm':
			return string.joinfields(node.GetValues(), '\n')
		elif node.type == 'ext':
			filename = self.getfileurl(node)
			try:
				fp = urllib.urlopen(filename)
			except IOError:
				return '<H1>Cannot Open</H1><P>'+ \
					  'Cannot open '+filename+':<P>'+ \
					  `(sys.exc_type, sys.exc_value)`+ \
					  '<P>\n'
			self.armed_url = fp.geturl()
			# use undocumented feature so we can cleanup
			if urllib._urlopener.tempcache is None:
				urllib._urlopener.tempcache = {}
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
		aname = href[5:]
		tp = self.findanchortype(aname)
		if tp == None:
			windowinterface.showmessage('Unknown CMIF anchor: '+aname)
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
			href = urllib.basejoin(self.url, href)
		else:
			href = self.url
		if list:
			href = addquery(href, list)
		self.url, tag = urllib.splittag(href)
		try:
			u = urllib.urlopen(self.url)
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
		self.htmlw.insert_html(newtext+footer, self.url)
##		self.htmlw.footerText = '<P>[<A HREF="'+self.armed_url+\
##			  '">BACK</A> to CMIF node]<P>'


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
	return urllib.urlopen(newurl).read()

	
# cleanup temporary files when we finish
windowinterface.addclosecallback(urllib.urlcleanup, ())
