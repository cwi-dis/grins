from Channel import ChannelWindow
#from TextChannel import mapfont, extract_taglist, fix_anchorlist
from TextChannel import mapfont, fix_anchorlist
#from TextChannel import mapfont
from AnchorDefs import *
import string
import MMurl
import MMAttrdefs
import gifex
import os

[SINGLE, HTM, TEXT] = range(3)

class LabelChannel(ChannelWindow):
	node_attrs = ChannelWindow.node_attrs + \
		     ['bucolor', 'hicolor', 'fgcolor', 'font', 'pointsize',
		      'textalign', 'bgimg', 'scale', 'center', 'noanchors']

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
		return '<LabelChannel instance, name=' + `self._name` + '>'


	def updatefixedanchors(self, node):
		#str = self.getstring(node)
		#parlist = extract_paragraphs(str)
		#taglist = extract_taglist(parlist)
		#fix_anchorlist(node, taglist)
		return 1

	def create_anchor_list(self, left, top, right, bottom, string1):
		# Appends the button list of the anchors.
		self.taglist.append(left, top, right-left, bottom-top, string1)



	def do_arm(self, node, same = 0):
		self.win = self.window
		if same and self.armed_display:
			return 1
		#get the image id
		fgcolor = self.getfgcolor(node)
		bucolor = self.getbucolor(node)
		drawbox = MMAttrdefs.getattr(node, 'drawbox')    #####
		img = MMAttrdefs.getattr(node, 'bgimg')
		#most of the labelchannels become same with an imagechannel
		#and they take their functionality
		if img:
			of = None
			isgif = 0
			result = None
			try:
				img = MMurl.urlretrieve(img)[0]
				result = gifex.TestGIF(img)
				if result[0]==1:
					nf = img + ".bmp"
					gifex.ReadGIF(img,nf)
					of = img
					img = nf
					isgif = 1
			except IOError:
				pass
			scale = MMAttrdefs.getattr(node, 'scale')
			#crop = MMAttrdefs.getattr(node, 'crop')
			center = MMAttrdefs.getattr(node, 'center')
			try:
				box = self.armed_display.display_image_from_file(img, scale = MMAttrdefs.getattr(node, 'scale'), center = MMAttrdefs.getattr(node, 'center'))
				if isgif:
					import win32api
					win32api.DeleteFile(img)
					img = of
			except (windowinterface.error, IOError), msg:
				if type(msg) is type(self):
					msg = msg.strerror
				elif type(msg) is type(()):
					msg = msg[1]
				self.errormsg(node, img + ':\n' + msg)

		#same as the text channel
		self.window._fgcolor = MMAttrdefs.getattr(node, 'fgcolor')
		fontspec = MMAttrdefs.getattr(node, 'font')
		fontname, pointsize = mapfont(fontspec)
		ps = MMAttrdefs.getattr(node, 'pointsize')
		if ps != 0:
			self._pointsize  = ps
		else:
			self._pointsize = pointsize

		align = MMAttrdefs.getattr(node, 'textalign')
		# Default align for labelchannel. Align for labelchannel
		# must contain always a proper string.
		if align == "":
			align = "top,left"
		self.window._align = align

		# Same jobs as in textchannel
		self.id, str = self.getstring(node)

		if MMAttrdefs.getattr(node, 'noanchors'):
		    self.taglist = []
		else:
			try:
				self.id<0
			except self.TextExcetion:
				print "Error in Prepare Text"
			self.armed_display.writeText(self._facename, self._pointsize, self.id, str, 0, 0)

		fix_anchorlist(node, self.taglist)

		buttons = []

		width, height = self.window._rect[2:]
		for (left, top, right, bottom, name, type) in self.taglist:
			#print "Left: ", left, " Right: ", right, " Top: ", top, " Bottom: ", bottom
			box = float(left)/width, float(top)/height, float(right)/width, float(bottom)/height
			#print "Box: ", box
			buttons.append((name, box, type))
			if not drawbox:                              ##
				self.armed_display.fgcolor(bucolor)      ##
			#print buttons
			# update loop invariants
		# draw boxes for the anchors
		if drawbox:                                ##
			self.armed_display.fgcolor(bucolor)    ##
		else:                                      ##
			self.armed_display.fgcolor(self.getbgcolor(node))
		hicolor = self.gethicolor(node)
		for name, box, type in buttons:
			button = self.armed_display.newbutton(box)
			button.hicolor(hicolor)
			button.hiwidth(3)
			self.setanchor(name, type, button)

		return 1

	# Not used
	def position(self, y, line, right):
		w, h = self.armed_display.strsize(line)
		if right:
			x = 1.0 - w
		else:
			x = (1.0 - w) / 2.0
		self.armed_display.setpos(x, y)

	def getstring(self, node):
		self.taglist=[]
		if node.type == 'imm':
			str = string.joinfields(node.GetValues(), '\n')
			str2 = cmifex.PrepareText(self.window._hWnd, self.create_anchor_list, self.id, str, 0, self._facename, self._pointsize,self.window._align)
			return str2
		elif node.type == 'ext':
			#filename = self.getfileurl(node)
			url = self.getfileurl(node)
			filename = MMurl.url2pathname(url)
			self._filename = filename
			try:
				#fp = urlopen(filename)
				fp = open(filename)
			except IOError, msg:
				print 'Cannot open text file', `filename`,
				print ':', msg
				return ''
			#text = fp.read()
			fp.close()
			self.filename = filename
			str2 = cmifex.PrepareText(self.window._hWnd, self.create_anchor_list, self.id, filename, 1, self._facename, self._pointsize,self.window._align)
			return str2
		else:
			raise CheckError, \
				'gettext on wrong node type: ' +`node.type`

# Not used
def extract_paragraphs(text):
	lines = string.splitfields(text, '\n')
	for lineno in range(len(lines)):
		line = lines[lineno]
		if '\t' in line: line = string.expandtabs(line, 8)
		i = len(line) - 1
		while i >= 0 and line[i] == ' ': i = i - 1
		line = line[:i+1]
		lines[lineno] = line
	return lines



