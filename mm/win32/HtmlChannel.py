#
# XXXX This is an initial stab at a HTML channel.
#
import Channel
from AnchorDefs import *
import string
import MMAttrdefs
import sys
import windowinterface
from windowinterface import SINGLE, TEXT, HTM, MPEG
from windowinterface import TRUE, FALSE
import urllib
import Htmlex, win32con, cmifex
#from TextChannel import getfont, mapfont

# arm states
AIDLE = 1
ARMING = 2
ARMED = 3
# play states
PIDLE = 1
PLAYING = 2
PLAYED = 3

class HtmlChannel(Channel.ChannelWindow):
	node_attrs = Channel.ChannelWindow.node_attrs + ['fgcolor', 'font']

	def __init__(self, name, attrdict, scheduler, ui):
		Channel.ChannelWindow.__init__(self, name, attrdict, scheduler, ui)
		self.whandle = None
		self._visible = TRUE
		self.retrieved_url = None
		self._window_type = HTM

	def do_show(self):
		if not Channel.ChannelWindow.do_show(self):
			return 0
		###self.window._hWnd.HookMessage(self._catch, win32con.WM_PAINT)
		res = Htmlex.CreateViewer(self.window._hWnd)
		Htmlex.CreateCallback(self.cbcmifanchor, self.window._hWnd)
		windowinterface.setcursor('watch')
		if not res :
			print 'Failed to create viewer'
			return 0
		return 1

	def __repr__(self):
		return '<HtmlChannel instance, name=' + `self._name` + '>'
		
	def do_arm(self, node, same=0):
		#print 'Entering do_arm'
	    #if not same:
		self.armed_str = self.getstring(node)
		print 'url is: '
		print self.armed_url
		return 1

	def play(self, node):
		self.need_armdone = 0
		self.play_0(node)
		if not self._is_shown:
			self.play_1()
			return
		if not self.nopop:
			self.window.pop()
		if self.armed_display.is_closed():
			# assume that we are going to get a
			# resize event
			pass
		self.played_display = self.armed_display
		self.armed_display = None
		self.do_play(node)
		self.need_armdone = 1
			
	def do_play(self, node):
		self.url = self.armed_url
		self.played_str = self.armed_str
		url = Htmlex.RetrieveUrl(self.window._hWnd, self.url)
		#url = Htmlex.RetrieveUrl(self.whandle, self.url)
		self.play_node = node
		self.play_1()


	def stopplay(self, node):
		Channel.ChannelWindow.stopplay(self, node)
		
	def getstring(self, node):
		if node.type == 'imm':
			self.armed_url = ''
			return string.joinfields(node.GetValues(), '\n')
		elif node.type == 'ext':
			filename = self.getfileurl(node)
			#self.armed_url = filename
			try:
				#fp = urllib.urlopen(filename)
				filename = urllib.url2pathname(filename)			
				fp = open(filename)
			except IOError:
				return '<H1>Cannot Open</H1><P>'+ \
					  'Cannot open '+filename+':<P>'+ \
					  `(sys.exc_type, sys.exc_value)`+ \
					  '<P>\n'
			self.armed_url = filename
			# use undocumented feature so we can cleanup
			#Comment out by Achilleas 16/1/97
			#if urllib._urlopener.tempcache is None:
			#	urllib._urlopener.tempcache = {}
			#	# cleanup temporary files when we finish
			#	windowinterface.addclosecallback(
			#		urllib.urlcleanup, ())
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
		windowinterface.setcursor('watch')
		apply(cb, (anchor,))

	def cbanchor(self, widget, userdata, calldata):
		if widget <> self.htmlw:
			raise 'kaboo kaboo'
		href = calldata.href
		if href[:5] <> 'cmif:':
			self.www_jump(href, 'GET', None, None)
			return
		self.cbcmifanchor(href, None)


	def _catch(self, params):
		cmifex.BeginPaint(self.window._hWnd, 0)
		print "Container HOOKED"
		cmifex.EndPaint(self.window._hWnd, 0)

	#def cbcmifanchor(self, href, list):
	def cbcmifanchor(self, string):
		aname = string
		#print "-------- ", aname
		list = []   #no arguments
		tp = self.findanchortype(aname)
		if tp == None:
			print "Unknown Type for CMIF Anchor, Html Channel ++++++++"
			return
		if tp == ATYPE_PAUSE:
			f = self.pause_triggered
		else:
			f = self.anchor_triggered

		windowinterface.setcursor('watch')
		f(self.play_node, [(aname, tp)], list)
		windowinterface.setcursor('')

	def findanchortype(self, name):
		alist = MMAttrdefs.getattr(self.play_node, 'anchorlist')
		for aid, atype, args in alist:
			if aid == name:
				return atype
		return None
	
	#
	# The stuff below has little to do with CMIF per se, it implements
	# a general www browser
	#
	
	
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
	file = urllib.url2pathname(newurl)
	return open(file).read()
	#return urllib.urlopen(newurl).read()

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
