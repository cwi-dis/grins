__version__ = "$Id$"

from Channel import ChannelWindow
from AnchorDefs import *
import string
#from MMurl import urlopen
import MMurl
import StringStuff
import MMAttrdefs
import textex, win32con


[SINGLE, HTM, TEXT] = range(3)

class TextChannel(ChannelWindow):
	node_attrs = ChannelWindow.node_attrs + ['fgcolor', 'font', \
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
		
	def __repr__(self):
		return '<TextChannel instance, name=' + `self._name` + '>'

		
	def create_anchor_list(self, left, top, right, bottom, string):
		# Appends the button list of the anchors.
		self.taglist.append(left, top, right, bottom, string)

	def do_arm(self, node, same=0):
		if same and self.armed_display:
			return 1
		self.win = self.window
		self.window._align = ' '
		self.window._fgcolor = MMAttrdefs.getattr(node, 'fgcolor')
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
		str = self.getstring(node)
		
		#textex.SetScrollPos(self.window._hWnd, str)
		# Get the button list of the anchor
		self.id, str = textex.PrepareText(self.win._hWnd, self.create_anchor_list, self.id, str, 0, self._facename, self._pointsize,"")	
		#textex.SetScrollPos(self.window._hWnd, "")
		 
		if MMAttrdefs.getattr(node, 'noanchors'):
		    self.taglist = []
		else:	
			try:
				self.id<0
			except self.TextExcetion:
				print "Error in Prepare Text"			
			#append the _list of the displaylist which arming
			self.armed_display.writeText(self._facename, self._pointsize, self.id, str)	

		fix_anchorlist(node, self.taglist)
		buttons = []
		#create the new buttons for the anchors in 0-1 coordinates
		width, height = self.window._rect[2:]
		for (left, top, right, bottom, name, type) in self.taglist:
			box = float(left)/width, float(top)/height, float(right)/width, float(bottom)/height
			buttons.append((name, box, type))
			
		#get forground and hicolor color 
		self.armed_display.fgcolor(self.getbucolor(node))
		hicolor = self.gethicolor(node)
		#append anchor list
		for (name, box, type) in buttons:
			button = self.armed_display.newbutton(box)
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
			str = string.joinfields(node.GetValues(), '\n')
			#str = string.joinfields(node.GetValues(), ' ')
#			print "Text getString"
#			print "Fontname: ", self._facename, " PointSize: ", self._pointsize
			#return textex.PrepareText(self.win._hWnd, self.create_anchor_list, self.id, str, 0, self._facename, self._pointsize,"")
			return str
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
			#return textex.PrepareText(self.win._hWnd, self.create_anchor_list, self.id, filename, 1, self._facename, self._pointsize,"")
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
		print "IN TEXT CHANNEL PLAY"
		str = self.getstring(node)
		print str
		if self.window != None: 
			textex.SetScrollPos(self.window._hWnd, str)
		ChannelWindow.play(self, node)


	def stopplay(self, node):
		print "IN TEXT CHANNEL STOPPLAY"
		if self.window != None: 
			textex.SetScrollPos(self.window._hWnd, "")
		ChannelWindow.stopplay(self, node)

	def resize(self, arg, window, event, value):
		print "IN TEXT CHANNEL RESIZE"
		node = self._played_node
		if self._played_node != None:
			str = self.getstring(node)
		else:
			str = ""
		print "str-->", str
		if self.window != None: 
			textex.SetScrollPos(self.window._hWnd, str)
		ChannelWindow.resize(self, arg, window, event, value)		

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
	anchors = oldanchors[:]
	i = 0
	while i < len(anchors):
		aid, atype, args = a = anchors[i]
		if atype in [ATYPE_DEST, ATYPE_AUTO, ATYPE_COMP]:
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
