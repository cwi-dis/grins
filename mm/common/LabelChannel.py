from Channel import ChannelWindow
from TextChannel import mapfont, extract_taglist, fix_anchorlist
from AnchorDefs import *
import string
import urllib
import MMAttrdefs

class LabelChannel(ChannelWindow):
	node_attrs = ChannelWindow.node_attrs + \
		     ['fgcolor', 'font', 'pointsize', 'bgimg', 'noanchors',
		      'textalign']

	def __repr__(self):
		return '<NewChannel instance, name=' + `self._name` + '>'

	def do_arm(self, node, same = 0):
		if same and self.armed_display:
			return 1
		img = MMAttrdefs.getattr(node, 'bgimg')
		if img:
			try:
				img = urllib.urlretrieve(img)[0]
			except IOError:
				pass
			try:
				box = self.armed_display.display_image_from_file(img)
			except (windowinterface.error, IOError), msg:
				if type(msg) == type(()):
					msg = msg[1]
				self.errormsg(node, img + ':\n' + msg)
		str = self.getstring(node)
		parlist = extract_paragraphs(str)
		if MMAttrdefs.getattr(node, 'noanchors'):
			taglist = []
		else:
			taglist = extract_taglist(parlist)
		fix_anchorlist(node, taglist)
		buttons = []
		if len(taglist) == 1:
			line0, char0, line1, char1, name, type = taglist[0]
			if line0 == 0 and char0 == 0 and \
			   line1 == len(parlist)-1 and \
			   char1 == len(parlist[-1]):
				taglist = []
				buttons.append(name, (0.0,0.0,1.0,1.0), type)
		fontspec = MMAttrdefs.getattr(node, 'font')
		fontname, pointsize = mapfont(fontspec)
		ps = MMAttrdefs.getattr(node, 'pointsize')
		if ps != 0:
			pointsize = ps
		baseline, fontheight, pointsize = \
			  self.armed_display.setfont(fontname, pointsize)
		width, height = self.armed_display.strsize(
			string.joinfields(parlist, '\n'))
		align = MMAttrdefs.getattr(node, 'textalign')
		if align == 'center':
			y = (1.0 - height) / 2.0 + baseline
			left = right = 0
			block = 1
		else:
			if string.find(align, 'top') >= 0:
				y = baseline
			elif string.find(align, 'bottom') >= 0:
				y = 1.0 - height + baseline
			else:
				y = (1.0 - height) / 2.0 + baseline
			left = string.find(align, 'left') >= 0
			right = string.find(align, 'right') >= 0
			if left and right:
				left = right = 0
			block = string.find(align, 'block') >= 0
			if left: block = 1
		if block:
			if left:
				x = 0.0
			elif right:
				x = 1.0 - width
			else:
				x = (1.0 - width) / 2.0
			self.armed_display.setpos(x, y)
		pline = pchar = 0
		# for each anchor...
		for line0, char0, line1, char1, name, type in taglist:
			if (line0, char0) >= (line1, char1):
				print 'Anchor without screenspace:', name
				continue
			# display lines before the anchor
			for line in range(pline, line0):
				if not block and pchar == 0:
					self.position(y, parlist[line], right)
				dummy = self.armed_display.writestr(
					parlist[line][pchar:] + '\n')
				pchar = 0
				y = y + fontheight
			# display text before the anchor
			if not block and pchar == 0:
				self.position(y, parlist[line0], right)
			dummy = self.armed_display.writestr(
				parlist[line0][pchar:char0])
			# display text in the anchor (if on multiple lines)
			pline, pchar = line0, char0
			for line in range(pline, line1):
				if not block and pchar == 0:
					self.position(y, parlist[line], right)
				box = self.armed_display.writestr(parlist[line][pchar:])
				buttons.append(name, box, type)
				dummy = self.armed_display.writestr('\n')
				pchar = 0
				y = y + fontheight
			# display text in anchor on last line of anchor
			if not block and pchar == 0:
				self.position(y, parlist[line1], right)
			box = self.armed_display.writestr(parlist[line1][pchar:char1])
			buttons.append(name, box, type)
			pline, pchar = line1, char1
		# display text after last anchor
		for line in range(pline, len(parlist)):
			if not block and pchar == 0:
				self.position(y, parlist[line], right)
			dummy = self.armed_display.writestr(
				parlist[line][pchar:] + '\n')
			pchar = 0
			y = y + fontheight
		# draw boxes for the anchors
		self.armed_display.fgcolor(self.gethicolor(node))
		for name, box, type in buttons:
			button = self.armed_display.newbutton(box)
			button.hiwidth(3)
			self.setanchor(name, type, button)
		return 1

	def position(self, y, line, right):
		w, h = self.armed_display.strsize(line)
		if right:
			x = 1.0 - w
		else:
			x = (1.0 - w) / 2.0
		self.armed_display.setpos(x, y)

	def getstring(self, node):
		if node.type == 'imm':
			return string.joinfields(node.GetValues(), '\n')
		elif node.type == 'ext':
			filename = self.getfilename(node)
			try:
				fp = urllib.urlopen(filename)
			except IOError, msg:
				print 'Cannot open text file', `filename`,
				print ':', msg
				return ''
			text = fp.read()
			fp.close()
			if text[-1:] == '\n':
				text = text[:-1]
			return text
		else:
			raise CheckError, \
				'gettext on wrong node type: ' +`node.type`

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
