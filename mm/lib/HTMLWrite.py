__version__ = "$Id$"

# HTMLWrite - Write out layout information in HTML for embedded G2 player


from MMExc import *		# Exceptions
from MMNode import alltypes, leaftypes, interiortypes
import MMCache
import MMAttrdefs
import Hlinks
from AnchorDefs import *
import string
import os
import MMurl
import regsub
import re


def nameencode(value):
	"""Quote a value"""
	value = string.join(string.split(value,'&'),'&amp;')
	value = string.join(string.split(value,'>'),'&gt;')
	value = string.join(string.split(value,'<'),'&lt;')
	value = string.join(string.split(value,'"'),'&quot;')
##	if '&' in value:
##		value = regsub.gsub('&', '&amp;', value)
##	if '>' in value:
##		value = regsub.gsub('>', '&gt;', value)
##	if '<' in value:
##		value = regsub.gsub('<', '&lt;', value)
##	if '"' in value:
##		value = regsub.gsub('"', '&quot;', value)
	return '"' + value + '"'

# CMIF channel types that have a visible representation
visible_channel_types={
	'text':1,
	'image':1,
	'video': 1,
	'movie':1,
	'mpeg':1,
	'html':1,
	'label':1,
	'RealPix':1,
	'RealText':1,
	'RealVideo':1,
}

# This string is written at the start of a SMIL file.
EVALcomment = '<!-- Created with an evaluation copy of GRiNS -->\n'

nonascii = re.compile('[\200-\377]')

isidre = re.compile('^[a-zA-Z_][-A-Za-z0-9._]*$')

# A fileish object with indenting
class IndentedFile:
	def __init__(self, fp):
		self.fp = fp
		self.level = 0
		self.bol = 1

	def push(self):
		self.level = self.level + 2

	def pop(self):
		self.level = self.level - 2

	def write(self, data):
		lines = string.split(data, '\n')
		if not lines:
			return
		for line in lines[:-1]:
			if self.bol:
				if self.level:
					self.fp.write(' '*self.level)
				self.bol = 0
			if line:
				self.fp.write(line)
			self.fp.write('\n')
			self.bol = 1

		line = lines[-1]
		if line:
			if self.bol:
				if self.level:
					self.fp.write(' '*self.level)
				self.bol = 0
			self.fp.write(line)

	def writeline(self, data):
		self.write(data)

	def writelines(self, data):
		self.write(string.join(data, '\n'))

	def close(self):
		self.fp.close()



# Write a node to a CMF file, given by filename

Error = 'Error'

def WriteFile(root, filename, smilurl, embed=0, embedlayout=0, evallicense = 0):
	fp = IndentedFile(open(filename, 'w'))
	try:
		writer = HTMLWriter(root, fp, filename, smilurl, embed, embedlayout, evallicense)
	except Error, msg:
		from windowinterface import showmessage
		showmessage(msg, mtype = 'error')
		return
	writer.write()
	if os.name == 'mac':
		import macfs
		import macostools
		fss = macfs.FSSpec(filename)
		fss.SetCreatorType('MOSS', 'TEXT')
		macostools.touched(fss)

import FtpWriter
def WriteFTP(root, filename, smilurl, ftpparams, embed=0, embedlayout=0, evallicense = 0):
	# XXXX For the moment (to be fixed):
	host, user, passwd, dir = ftpparams
	try:
		ftp = FtpWriter.FtpWriter(host, filename, user=user, passwd=passwd, dir=dir, ascii=1)
		fp = IndentedFile(ftp)
		try:
			writer = HTMLWriter(root, fp, filename, smilurl, embed, embedlayout, evallicense)
		except Error, msg:
			from windowinterface import showmessage
			showmessage(msg, mtype = 'error')
			return
		writer.write()
	except FtpWriter.all_errors, msg:
		from windowinterface import showmessage
		showmessage('FTP upload failed:\n' + msg, mtype = 'error')
		return

import StringIO
class MyStringIO(StringIO.StringIO):
	def close(self):
		pass

def WriteString(root, smilurl, embed=0, embedlayout=0):
	fp = IndentedFile(MyStringIO())
	writer = HTMLWriter(root, fp, '<string>', smilurl, embed, embedlayout)
	writer.write()
	return fp.fp.getvalue()


class HTMLWriter:
	def __init__(self, node, fp, filename, smilurl, embed = 0, embedlayout = 0, evallicense = 0):
		self.__embed = embed
		self.__embedlayout = embedlayout
		self.evallicense = evallicense
		self.smilurl = smilurl

		self.__isopen = 0
		self.__stack = []

		self.root = node
		self.fp = fp
		self.__title = node.GetContext().gettitle()

		self.ids_used = {}

##		self.layout2name = {}
##		self.calclayoutnames(node)

		self.ch2name = {}
		self.top_levels = []
		self.calcchnames1(node)

##		self.uid2name = {}
##		self.calcnames1(node)

##		# second pass
##		self.calcnames2(node)
##		self.calcchnames2(node)

##		# must come after second pass
##		self.aid2name = {}
##		self.calcanames(node)

		if len(self.top_levels) > 1:
			print '** Document uses multiple toplevel channels'
			self.uses_cmif_extension = 1

##		self.syncidscheck(node)

	def push(self):
		if self.__isopen:
			self.fp.write('>\n')
			self.__isopen = 0
		self.fp.push()

	def pop(self):
		fp = self.fp
		if self.__isopen:
##			fp.write('/>\n')
			fp.write('>\n')
			self.__isopen = 0
			del self.__stack[-1]
		fp.pop()
		fp.write('</%s>\n' % self.__stack[-1])
		del self.__stack[-1]

	def close(self):
		fp = self.fp
		if self.__isopen:
##			fp.write('/>\n')
			fp.write('>\n')
			self.__isopen = 0
			del self.__stack[-1]
		while self.__stack:
			self.pop()
		fp.close()

	def writetag(self, tag, attrs = None):
		if attrs is None:
			attrs = []
		write = self.fp.write
		if self.__isopen:
##			write('/>\n')
			write('>\n')
			self.__isopen = 0
			del self.__stack[-1]
		write('<' + tag)
		for attr, val in attrs:
			write(' %s=%s' % (attr, nameencode(val)))
		self.__isopen = 1
		self.__stack.append(tag)
		
	def writedata(self, data):
		if self.__isopen:
			self.fp.write('>\n')
			self.__isopen = 0
		self.fp.write(data)

	def writecomment(self, comment):
		if self.__isopen:
			self.fp.write('>\n')
			self.__isopen = 0
		self.fp.write('<!-- %s -->\n'%comment)
		
	def write(self):
		import version
		ctx = self.root.GetContext()
		fp = self.fp
##		fp.write(HTMLdecl) -- Don't: I think the embed/applet stuff is non-standard
		if self.evallicense:
			fp.write(EVALcomment)
##		if not self.uses_cmif_extension:
##			fp.write(doctype)
		attrlist = []
		self.writetag('html', attrlist)
		self.push()
		self.writetag('head')
		self.push()
		if self.__title:
			self.writetag('title')
			self.push()
			self.writedata(self.__title)
			self.pop()
		self.writetag('meta', [('name', 'generator'),
				       ('content','GRiNS %s'%version.version)])
		self.pop() # End of head
		self.writetag('body')
		self.push()
		if self.__title:
			self.writetag('h1')
			self.push()
			self.writedata(self.__title)
			self.pop()
		self.writetag('p')
		self.push()
		self.writedata("This presentation uses G2. You don't have it? You're hosed....\n")
		self.pop()
		
		playername = "clip_1"
		
		if self.__embed:
			if self.__embedlayout:
				channels = self.get_visible_channels()
				for region, x, y, w, h in channels:
					if not w or not h:
						self.writecomment('Region %s used for non-visible media only, skipped'%region)
						continue
					self.writecomment('Object for region %s, position %d, %d'%(region, x, y))
					self.writetag('p')
					self.push()
					self.writeobject(w, h, [
						('controls', 'ImageWindow'),
						('console', playername),
						('autostart', 'false'),
						('region', region),
						('src', self.smilurl)])
					self.pop()
				self.writecomment('Object for control panel')
				self.writetag('p')
				self.push()
				self.writeobject(275, 125, [
					('controls', 'All'),
					('console', playername)])
				self.pop()
			else:
				# First create an output area. Optional: don't do this if there are
				# only non-visible media (and, hence, no toplevel layout channel)
				if self.top_levels:
					if len(self.top_levels) > 1:
						raise Error, "Multiple toplevel windows"
					w, h = self.top_channel_size(self.top_levels[0])
					if not w or not h:
						raise Error, "Zero-sized presentation window"
					self.writecomment('Object for output window')
					self.writetag('p')
					self.push()
					self.writeobject(w, h, [
						('controls', 'ImageWindow'),
						('console', playername),
						('autostart', 'false'),
						('src', self.smilurl)])
					self.pop()
				else:
					self.writecomment('No visible media, hence no output window')
				self.writecomment('Object for control panel')
				self.writetag('p')
				self.push()
				self.writeobject(275, 125, [
					('controls', 'All'),
					('console', playername)])
				self.pop()
					
		else:
			self.writetag('p')
			self.push()
			self.writedata('Imagine an link here.\n')
			self.pop()
			
##		self.writelayout()
##		self.writeusergroups()
##		self.writegrinslayout()
		self.pop() # End of body
		self.close()
		
	def get_visible_channels(self):
		if not self.top_levels:
			return []
		if len(self.top_levels) > 1:
			raise Error, "Multiple toplevel windows"
		top_w, top_h = self.top_channel_size(self.top_levels[0])
		if not top_w or not top_h:
			raise Error, "Zero-sized presentation window"
		rv = []
		for ch in self.root.GetContext().channels:
			if not visible_channel_types.has_key(ch['type']):
				continue
			name = self.ch2name[ch]
			x, y, w, h = self.channel_pos(ch, top_w, top_h)
			rv.append(name, x, y, w, h)
		return rv
		
	def writeobject(self, width, height, arglist):
		self.writetag('object', [
			('classid', 'clsid:CFCDAA03-8BE4-11cf-B84B-0020AFBBCCFA'),
			('width', `width`),
			('height', `height`)])
		self.push()
		for arg, val in arglist:
			self.writetag('param', [(arg, val)])
		# Trick: if the browser understands the object tag but not the embed
		# tag (inside it) it will quietly skip it.
		arglist = arglist[:]
		arglist.append(('width', `width`))
		arglist.append(('height', `height`))
		arglist.append(('type', 'audio/x-pn-realaudio-plugin'))
		arglist.append(('nojava', 'true'))
		self.writetag('embed', arglist)
		self.pop()
		
	def calcchnames1(self, node):
		"""Calculate unique names for channels; first pass"""
		context = node.GetContext()
		channels = context.channels
		for ch in channels:
			name = identify(ch.name)
			if not self.ids_used.has_key(name):
				self.ids_used[name] = 0
				self.ch2name[ch] = name
			else:
				raise Error, "Duplicate region name"
			if not ch.has_key('base_window') and \
			   ch['type'] not in ('sound', 'shell', 'python',
					      'null', 'vcr', 'socket', 'cmif',
					      'midi', 'external'):
				# top-level channel with window
				self.top_levels.append(ch)
				if not self.__title:
					self.__title = ch.name
		if not self.__title and channels:
			# no channels with windows, so take very first channel
			self.__title = channels[0].name
			
	def channel_pos(self, ch, basewidth, baseheight):
		if not ch.has_key('base_winoff'):
			return None, None, None, None
		units = ch.get('units', 2)
		x, y, w, h = ch['base_winoff']
		if units == 0:
			# convert mm to pixels
			# (assuming 100 dpi)
			x = int(x / 25.4 * 100.0 + .5)
			y = int(y / 25.4 * 100.0 + .5)
			w = int(w / 25.4 * 100.0 + .5)
			h = int(h / 25.4 * 100.0 + .5)
		if units == 1:
			x = x * basewidth + .5
			y = y * baseheight + .5
			w = w * basewidth + .5
			h = h * baseheight + .5
		# else: units are already in pixels
		return int(x), int(y), int(w), int(h)

	def top_channel_size(self, ch):
		if not ch.has_key('winsize'):
			return None, None
		units = ch.get('units', 0)
		w, h = ch['winsize']
		if units == 0:
			# convert mm to pixels
			# (assuming 100 dpi)
			w = int(w / 25.4 * 100.0 + .5)
			h = int(h / 25.4 * 100.0 + .5)
		if units == 1:
			raise Error, "Cannot use relative coordinates for toplevel window"
		# else: units are already in pixels
		return int(w), int(h)

	def XXXXwritelayout(self):
		"""Write the layout section"""
		self.writetag('layout') # default: type="text/smil-basic-layout"
		self.push()
		channels = self.root.GetContext().channels
		if len(self.top_levels) == 1:
			attrlist = []
			ch = self.top_levels[0]
			if ch['type'] == 'layout':
				attrlist.append(('id', self.ch2name[ch]))
			title = ch.get('title')
			if title:
				attrlist.append(('title', title))
			elif self.ch2name[ch] != ch.name:
				attrlist.append(('title', ch.name))
			if ch.get('transparent', 0) == 1:
				# background-color="transparent" is default
				pass
			elif ch.has_key('bgcolor'):
				attrlist.append(('background-color', '#%02x%02x%02x' % ch['bgcolor']))
			if ch.has_key('winsize'):
				units = ch.get('units', 0)
				w, h = ch['winsize']
				if units == 0:
					# convert mm to pixels
					# (assuming 100 dpi)
					w = int(w / 25.4 * 100.0 + .5)
					h = int(h / 25.4 * 100.0 + .5)
					units = 2
				if units == 1:
					attrlist.append(('width', '%d%%' % int(w * 100 + .5)))
					attrlist.append(('height', '%d%%' % int(h * 100 + .5)))
				else:
					attrlist.append(('width', '%d' % int(w + .5)))
					attrlist.append(('height', '%d' % int(h + .5)))
			self.writetag('root-layout', attrlist)
		for ch in channels:
			mtype, xtype = mediatype(ch['type'], error=1)
			isvisual = mtype in ('img', 'video', 'text')
			if len(self.top_levels) == 1 and \
			   ch['type'] == 'layout' and \
			   not ch.has_key('base_window'):
				# top-level layout channel has been handled
				continue
			attrlist = [('id', self.ch2name[ch])]
			title = ch.get('title')
			if title:
				attrlist.append(('title', title))
			elif self.ch2name[ch] != ch.name:
				attrlist.append(('title', ch.name))
			# if toplevel window, define a region elt, but
			# don't define coordinates (i.e., use defaults)
			if ch.has_key('base_window') and \
			   ch.has_key('base_winoff'):
				x, y, w, h = ch['base_winoff']
				units = ch.get('units', 2)
				if units == 0:		# UNIT_MM
					# convert mm to pixels (assuming 100 dpi)
					x = int(x / 25.4 * 100 + .5)
					y = int(y / 25.4 * 100 + .5)
					w = int(w / 25.4 * 100 + .5)
					h = int(h / 25.4 * 100 + .5)
				elif units == 1:	# UNIT_SCREEN
					if x+w >= 1.0: w = 0
					if y+h >= 1.0: h = 0
				elif units == 2:	# UNIT_PXL
					x = int(x)
					y = int(y)
					w = int(w)
					h = int(h)
				for name, value in [('left', x), ('top', y), ('width', w), ('height', h)]:
					if not value:
						continue
					if type(value) is type(0.0):
						value = '%d%%' % int(value*100)
					else:
						value = '%d' % value
					attrlist.append((name, value))
			if isvisual:
				z = ch.get('z', 0)
				if z > 0:
					attrlist.append(('z-index', "%d" % z))
				scale = ch.get('scale', 0)
				if scale == 0:
					fit = 'meet'
				elif scale == -1:
					fit = 'slice'
				elif scale == 1:
					fit = 'hidden'
				else:
					fit = None
					print '** Channel uses unsupported scale value', name
				if fit is not None and fit != 'hidden':
					attrlist.append(('fit', fit))

				# SMIL says: either background-color
				# or transparent; if different, set
				# GRiNS attributes
			# We have the following possibilities:
			#		no bgcolor	bgcolor set
			#transp -1	no attr		b-g="bg"
			#transp  0	GR:tr="0"	GR:tr="0" b-g="bg"
			#transp  1	b-g="trans"	b-g="trans" (ignore bg)
				transparent = ch.get('transparent', 0)
				bgcolor = ch.get('bgcolor')
				if transparent == 0:
					# non-SMIL extension:
					# permanently visible region
					attrlist.append(('%s:transparent' % NSprefix,
							 '0'))
				if bgcolor is not None:
					attrlist.append(('background-color',
							 "#%02x%02x%02x" % bgcolor))
				# Since background-color="transparent" is the
				# default, we don't need to actually write that
##				if transparent == 1:
##					attrlist.append(('background-color',
##							 'transparent'))
##					# having a bg color on a transparent
##					# region is nonsense...
####					if bgcolor is not None:
####						attrlist.append(('%s:bgcolor' % NSprefix,
####								 "#%02x%02x%02x" % bgcolor))
				if ch.get('center', 1):
					attrlist.append(('%s:center' % NSprefix, '1'))
				if ch.get('drawbox', 1):
					attrlist.append(('%s:drawbox' % NSprefix, '1'))

			for key, val in ch.items():
				if key not in cmif_chan_attrs_ignore:
					attrlist.append(('%s:%s' % (NSprefix, key), MMAttrdefs.valuerepr(key, val)))
			self.writetag('region', attrlist)
		self.pop()

namechars = string.letters + string.digits + '_-.'

def identify(name):
	"""Turn a CMIF name into an identifier"""
	rv = []
	for ch in name:
		if ch in namechars:
			rv.append(ch)
		else:
			if rv and rv[-1] != '-':
				rv.append('-')
	# the first character must not be a digit
	if rv and rv[0] in string.digits:
		rv.insert(0, '_')
	return string.join(rv, '')
