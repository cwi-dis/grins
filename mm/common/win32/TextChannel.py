from Channel import ChannelWindow
from AnchorDefs import *
import string
#from urllib import urlopen
import urllib, MMurl
import StringStuff
import MMAttrdefs
import win32con
import cmifex


[SINGLE, HTM, TEXT] = range(3)

class TextChannel(ChannelWindow):
	node_attrs = ChannelWindow.node_attrs + ['bucolor', 'hicolor',
						 'fgcolor', 'font',
						 'pointsize', 'noanchors']
	def __init__(self, name, attrdict, scheduler, ui):
		ChannelWindow.__init__(self, name, attrdict, scheduler, ui)
		self._visible = 1
		self._filename = ""
		self.id = -1
		self.taglist = []
		self.win = None
		self._facename = "Arial"
		self._pointsize = 12
		self.TextException = "Text Error:"
		self._window_type = TEXT
		self.str_loaded = 0

	def __repr__(self):
		return '<TextChannel instance, name=' + `self._name` + '>'


	def create_anchor_list(self, left, top, right, bottom, string1):
		# Appends the button list of the anchors.
		self.taglist.append(left, top, right-left, bottom-top, string1)


	def updatefixedanchors(self, node):
		#str = self.getstring(node)
		#parlist = extract_paragraphs(str)
		#taglist = extract_taglist(parlist)
		#fix_anchorlist(node, taglist)
		return 1


	def do_arm(self, node, same=0):
		if same and self.armed_display:
			return 1
		self.win = self.window
		self.window._align = ' '
		#self.window._fgcolor = MMAttrdefs.getattr(node, 'fgcolor')
		#self.window._bucolor = MMAttrdefs.getattr(node, 'bucolor')
		fgcolor = self.getfgcolor(node)
		bucolor = self.getbucolor(node)
		drawbox = MMAttrdefs.getattr(node, 'drawbox')                 ####
		#get the attributes of the font

		fontspec = getfont(node)
		fontname, pointsize = mapfont(fontspec)
		ps = getpointsize(node)
		self._facename = fontname
		if ps != 0:
			self._pointsize = ps
		else:
			self._pointsize = pointsize

		#get the text of the window
		str1 = self.getstring(node)

		#if not self.str_loaded:
		#	cmifex.SetScrollPos(self.window._hWnd, str1)
		#	self.str_loaded = 1
		# Get the button list of the anchor
		self.id, str1 = cmifex.PrepareText(self.win._hWnd, self.create_anchor_list, self.id, str1, 0, self._facename, self._pointsize,"")
		#cmifex.SetScrollPos(self.window._hWnd, "")

		if MMAttrdefs.getattr(node, 'noanchors'):
		    self.taglist = []
		else:
			try:
				self.id<0
			except self.TextExcetion:
				print "Error in Prepare Text"
			#append the _list of the displaylist which arming
			self.armed_display.writeText(self._facename, self._pointsize, self.id, str1, 0, 0)

		fix_anchorlist(node, self.taglist)
		buttons = []
		#create the new buttons for the anchors in 0-1 coordinates
		width, height = self.window._rect[2:]
		for (left, top, right, bottom, name, type) in self.taglist:
			box = float(left)/width, float(top)/height, float(right)/width, float(bottom)/height
			buttons.append((name, box, type))
			if not drawbox:
				self.armed_display.fgcolor(bucolor)
		#get forground and hicolor color
		hicolor = self.gethicolor(node)
		if drawbox:
			self.armed_display.fgcolor(bucolor)
		else:
			self.armed_display.fgcolor(self.getbgcolor(node))
		#append anchor list
		for (name, box, type) in buttons:
			button = self.armed_display.newbutton(box)
			if drawbox:
				button.hicolor(hicolor)
				button.hiwidth(3)
			self.setanchor(name, type, button)
		# Draw a little square if some text did not fit.
		#fits = 1
		#for pos in box:
		#	if pos > 1:
		#		fits = 0
		#if not fits:
		#	print "Doesnt Fit!!"
		#	#xywh = (1.0-margin, 1.0-margin, margin, margin)
		#	#self.armed_display.drawfbox(self.gethicolor(node), xywh)
		return 1

	def getstring(self, node):
		self.taglist=[]
		if node.type == 'imm':
			#if not external connect the lines of the text with '\n's
			str1 = string.joinfields(node.GetValues(), '\n')
			#str = string.joinfields(node.GetValues(), ' ')
#			print "Text getString"
#			print "Fontname: ", self._facename, " PointSize: ", self._pointsize
			#return cmifex.PrepareText(self.win._hWnd, self.create_anchor_list, self.id, str1, 0, self._facename, self._pointsize,"")
			return str1
		elif node.type == 'ext':
			#if external read the text from the file
			#filename = self.getfileurl(node)
			url = self.getfileurl(node)
			filename = MMurl.url2pathname(url)
			try:
				#fp = urlopen(filename)
				fp = open(filename)
			except IOError, msg:
				print 'Cannot open text file', `filename`,
				print ':', msg
				return ''
			text = fp.read()
			fp.close()
			self.filename = filename
			#return cmifex.PrepareText(self.win._hWnd, self.create_anchor_list, self.id, filename, 1, self._facename, self._pointsize,"")
			return text
		else:
			raise CheckError, \
				'gettext on wrong node type: ' +`node.type`

	def defanchor(self, node, anchor, cb):
		# Anchors don't get edited in the TextChannel.  You
		# have to edit the text to change the anchor.  We
		# don't want a message, though, so we provide our own
		# defanchor() method.
		apply(cb, (anchor,))

	def play(self, node):
		#print "IN TEXT CHANNEL PLAY"
		str1 = self.getstring(node)
		#print str, "-->", self.window
		ChannelWindow.play(self, node)
		if self.window != None:
			if self.window._transparent != 1:
				cmifex.SetScrollPos(self.window._hWnd, str1)


	def stopplay(self, node):
		#print "IN TEXT CHANNEL STOPPLAY", self.window
		ChannelWindow.stopplay(self, node)
		if self.window != None:
			if self.window._transparent != 1:
				cmifex.SetScrollPos(self.window._hWnd, "")

	def resize(self, arg, window, event, value):
		#print "IN TEXT CHANNEL RESIZE"
		node = self._played_node
		if self._played_node != None:
			str1 = self.getstring(node)
		else:
			str1 = ""
		#print "str-->", str
		if self.window != None:
			if self.window._transparent != 1:
				cmifex.SetScrollPos(self.window._hWnd, str1)
		ChannelWindow.resize(self, arg, window, event, value)
		return


def getfont(node):
	import MMAttrdefs
	return MMAttrdefs.getattr(node, 'font')

def getpointsize(node):
	import MMAttrdefs
	return MMAttrdefs.getattr(node, 'pointsize')


# XXX THIS IS A HACK
# When we have extracted the anchors from a node's paragraph list,
# add them to the node's anchor list.
# This should be done differently, and doesn't even use the edit mgr,
# but as a compatibility hack it's probably OK...

def fix_anchorlist(node, taglist):
	if not taglist:
		return
	import MMAttrdefs
	names_in_anchors = []
	names_in_taglist = []
	anchor_types = {}
	names_in_anchors = map(lambda item: item[4], taglist)
	oldanchors = MMAttrdefs.getattr(node, 'anchorlist')
	#modanchorlist(oldanchors)
	anchors = oldanchors[:]
	i = 0
	while i < len(anchors):
		aid, atype, args = a = anchors[i]
		if atype in [ATYPE_WHOLE, ATYPE_AUTO, ATYPE_COMP]:
			pass
		elif aid not in names_in_anchors:
			#print 'Remove text anchor from anchorlist:', a
			anchors.remove(a)
			i = i - 1	# compensate for later increment
		else:
			names_in_taglist.append(aid)
			anchor_types[aid] = atype
		i = i + 1
	for i in range(len(taglist)):
		item = taglist[i]
		name = item[4]
		if not anchor_types.has_key(name):
			#print 'Add text anchor to anchorlist:', name
			anchors.append(name, ATYPE_NORMAL, [])
			anchor_types[name] = ATYPE_NORMAL
		taglist[i] = taglist[i] + (anchor_types[name],)
	if anchors <> oldanchors:
		print 'New anchors:', anchors
		node.SetAttr('anchorlist', anchors)
		MMAttrdefs.flushcache(node)

# Map a possibly symbolic font name to a real font name and default point size

fontmap = {
	'':		('Times-Roman', 12),
	'default':	('Times-Roman', 12),
	'plain':	('Times-Roman', 12),
	'italic':	('Times-Italic', 12),
	'bold':		('Times-Bold', 12),
	'courier':	('Courier', 12),
	'bigbold':	('Times-Bold', 14),
	'title':	('Times-Bold', 24),
	'greek':	('Greek', 14),
	'biggreek':	('Greek', 17),
	}

def mapfont(fontname):
	if fontmap.has_key(fontname):
		return fontmap[fontname]
	else:
		return fontname, 12
