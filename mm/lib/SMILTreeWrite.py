__version__ = "$Id$"

# MMWrite -- Multimedia tree writing interface


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

from SMIL import *

# This string is written at the start of a SMIL file.
SMILdecl = '<?xml version="1.0" encoding="ISO-8859-1"?>\n'
NSdecl = '<?xml:namespace ns="%s" prefix="cmif"?>\n' % CMIFns
doctype = '<!DOCTYPE smil PUBLIC "%s"\n\
                      "%s">\n' % (SMILpubid,SMILdtd)

nonascii = re.compile('[\200-\377]')

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

def WriteFile(root, filename):
	fp = IndentedFile(open(filename, 'w'))
	writer = SMILWriter(root, fp, filename)
	writer.write()
	fp.close()

#
# Functions to encode data items
#
def getid(writer, node):
	uid = node.GetUID()
	name = writer.uid2name[uid]
	if writer.ids_used[name]:
		return name

def getcmifattr(writer, node, attr):
	val = node.GetRawAttrDef(attr, None)
	if val is not None:
		val = str(val)
	return val

def getchname(writer, node):
	ch = node.GetChannel()
	if not ch:
		return None
# XXXX Removed: Sjoerd wants region names on all nodes
##	if not writer.regions_defined.has_key(ch):
##		# Audio regions and such need not be named
##		return None
	return writer.ch2name[ch]

def getduration(writer, node, attr):
	duration = node.GetRawAttrDef(attr, 0)
	if duration == 0:
		return None
	if duration < 0:		# infinite duration...
		return 'indefinite'
	else:
		duration = '%.3f' % duration
		if duration[-4:] == '.000':
			duration = duration[:-4]
		return duration + 's'
		
def getsyncarc(writer, node, isend):
	allarcs = node.GetRawAttrDef('synctolist', [])
	arc = None
	for srcuid, srcside, delay, dstside in allarcs:
		if dstside == isend:
			if arc:
				print '** Multiple syncarcs to', \
				      node.GetRawAttrDef('name', '<unnamed>'),\
				      node.GetUID()
			else:
				arc = srcuid, srcside, delay, dstside
	if not arc:
		return
	if not writer.uid2name.has_key(srcuid):
		print '** Syncarc with unknown source to', \
		      node.GetRawAttrDef('name', '<unnamed>'),\
		      node.GetUID()
		return
	srcuid, srcside, delay, dstside = arc
	if delay < 0:
		print '** Negative delay for', \
		      node.GetRawAttrDef('name', '<unnamed>'),\
		      node.GetUID()
		return
	parent = node.GetParent()
	ptype = parent.GetType()
	siblings = parent.GetChildren()
	index = siblings.index(node)
	if not srcside and \
	   (srcuid == parent.GetUID() and
	    (ptype == 'par' or (ptype == 'seq' and index == 0))) or \
	   (srcside and ptype == 'seq' and index > 0 and
	    srcuid == siblings[index-1].GetUID()):
		# sync arc from parent/previous node
		rv = '%.3fs' % delay
	else:
		srcname = writer.uid2name[srcuid]
		rv = 'id(%s)'%srcname
		if srcside:
			rv = rv+'(end)'
			if delay:
				print '** Delay required with end syncarc',\
				      node.GetRawAttrDef('name', '<unnamed>'),\
				      node.GetUID()
## 			rv = rv+'+%.3f'%delay
		else:
			rv = rv+'(%.3fs)' % delay
	return rv

def getterm(writer, node):
	terminator = node.GetRawAttrDef('terminator', 'LAST')
	if terminator == 'LAST':
		return
	if terminator == 'FIRST':
		return 'first'
	for child in node.children:
		if child.GetRawAttrDef('name', '') == terminator:
			return 'id(%s)' % writer.uid2name[child.GetUID()]
	print '** Terminator attribute refers to unknown child in', \
	      node.GetRawAttrDef('name', '<unnamed>'),\
	      node.GetUID()

def getrepeat(writer, node):
	value = node.GetRawAttrDef('loop', 1)
	if value == 1:
		return
	elif value == 0:
		return 'indefinite'
	else:
		return `value`

def getcaptions(writer, node):
	value = node.GetRawAttrDef('system_captions', None)
	if value is not None:
		if value:
			return 'on'
		else:
			return 'off'

def getscreensize(writer, node):
	value = node.GetRawAttrDef('system_screen_size', None)
	if value is not None:
		return '%dX%d' % value

def getbagindex(writer, node):
	if node.GetType() != 'bag':
		return
	bag_index = node.GetRawAttrDef('bag_index', None)
	if bag_index is None:
		return
	for child in node.children:
		if child.GetRawAttrDef('name', '') == bag_index:
			return 'id(%s)' % writer.uid2name[child.GetUID()]
	print '** Bag-index attribute refers to unknown child in', \
	      node.GetRawAttrDef('name', '<unnamed>'),\
	      node.GetUID()

#
# Mapping from SMIL attrs to functions to get them. Strings can be
# used as a shortcut for node.GetAttr
#
smil_attrs=[
	("id", getid),
	("region", getchname),
	("src", lambda writer, node:getcmifattr(writer, node, "file")),
	("dur", lambda writer, node: getduration(writer, node, 'duration')),
	("begin", lambda writer, node: getsyncarc(writer, node, 0)),
	("end", lambda writer, node: getsyncarc(writer, node, 1)),
	("endsync", getterm),
	("repeat", lambda writer, node:getrepeat(writer, node)),
	("system-bitrate", lambda writer, node:getcmifattr(writer, node, "system_bitrate")),
	("system-captions", getcaptions),
	("system-language", lambda writer, node:getcmifattr(writer, node, "system_language")),
	("system-overdub-or-captions", lambda writer, node:getcmifattr(writer, node, "system_overdub_or_captions")),
	("system-required", lambda writer, node:getcmifattr(writer, node, "system_required")),
	("system-screen-size", getscreensize),
	("system-screen-depth", lambda writer, node:getcmifattr(writer, node, "system_screen_depth")),
	("cmif:bag-index", getbagindex),
]

# Mapping from CMIF channel types to smil media types
smil_mediatype={
	'text':'text',
	'sound':'audio',
	'image':'img',
	'video': 'video',
	'movie':'video',
	'mpeg':'video',
	'html':'text',
	'label':'text',
	'midi':'audio'
}

def mediatype(chtype, error=0):
	if smil_mediatype.has_key(chtype):
		return smil_mediatype[chtype]
	if error and chtype != 'layout':
		print '** Unimplemented channel type', chtype
	return 'cmif:'+chtype

class SMILWriter(SMIL):
	def __init__(self, node, fp, filename):
		self.uses_cmif_extension = 0
		self.root = node
		self.fp = fp
		self.__title = None

		self.ids_used = {}

		self.ch2name = {}
		self.top_levels = []
		self.calcchnames1(node)

		self.uid2name = {}
		self.calcnames1(node)

		# second pass
		self.calcnames2(node)
		self.calcchnames2(node)

		# must come after second pass
		self.aid2name = {}
		self.calcanames(node)

		if len(self.top_levels) > 1:
			print '** Document uses multiple toplevel channels'
			self.uses_cmif_extension = 1
		
		dir, file = os.path.split(filename) # get parent dir
		file, ext = os.path.splitext(file) # and base name
		rel = file + '.dir'	# relative name of data directory
		abs = os.path.join(dir, rel) # possibly absolute name of same
		self.tmpdirname = abs, rel # record both names

	def write(self):
		fp = self.fp
		fp.write(SMILdecl)
		if self.uses_cmif_extension:
			fp.write(NSdecl)
		fp.write(doctype)
		fp.write('<smil>\n')
		fp.push()
		fp.write('<head>\n')
		fp.push()
## 		fp.write('<meta name="sync" content="soft"/>\n')
		if self.__title:
			self.fp.write('<meta name="title" content=%s/>\n' %
				      nameencode(self.__title))
		self.writelayout()
		fp.pop()
		fp.write('</head>\n')
		fp.write('<body>\n')
		fp.push()
		self.writenode(self.root, root = 1)
		fp.pop()
		fp.write('</body>\n')
		fp.pop()
		fp.write('</smil>\n')

	def calcnames1(self, node):
		"""Calculate unique names for nodes; first pass"""
		uid = node.GetUID()
		name = node.GetRawAttrDef('name', '')
		if name:
			name = identify(name)
			if not self.ids_used.has_key(name):
				self.ids_used[name] = 1
				self.uid2name[uid] = name
		ntype = node.GetType()
		if ntype in interiortypes:
			for child in node.children:
				self.calcnames1(child)
		if ntype == 'bag':
			self.uses_cmif_extension = 1

	def calcnames2(self, node):
		"""Calculate unique names for nodes; second pass"""
		uid = node.GetUID()
		name = node.GetRawAttrDef('name', '')
		if not self.uid2name.has_key(uid):
			isused = name != ''
			if isused:
				name = identify(name)
			else:
				name = 'node'
			# find a unique name by adding a number to the name
			i = 0
			nn = '%s-%d' % (name, i)
			while self.ids_used.has_key(nn):
				i = i+1
				nn = '%s-%d' % (name, i)
			name = nn
			self.ids_used[name] = isused
			self.uid2name[uid] = name
		if node.GetType() in interiortypes:
			for child in node.children:
				self.calcnames2(child)

	def calcchnames1(self, node):
		"""Calculate unique names for channels; first pass"""
		context = node.GetContext()
		channels = context.channels
		for ch in channels:
			name = identify(ch.name)
			if not self.ids_used.has_key(name):
				self.ids_used[name] = 0
				self.ch2name[ch] = name
			if not ch.has_key('base_window') and \
			   ch['type'] not in ('sound', 'shell', 'python',
					      'null', 'vcr', 'socket', 'cmif',
					      'midi', 'external'):
				# top-level channel with window
				self.top_levels.append(ch)
				if not self.__title:
					self.__title = ch.name
			# also check if we need to use the CMIF extension
			if not self.uses_cmif_extension and \
			   not smil_mediatype.has_key(ch['type']) and \
			   ch['type'] != 'layout':
				self.uses_cmif_extension = 1
		if not self.__title and channels:
			# no channels with windows, so take very first channel
			self.__title = channels[0].name

	def calcchnames2(self, node):
		"""Calculate unique names for channels; second pass"""
		context = node.GetContext()
		channels = context.channels
		for ch in channels:
			if not self.ch2name.has_key(ch):
				name = identify(ch.name)
				i = 0
				nn = '%s-%d' % (name, i)
				while self.ids_used.has_key(nn):
					i = i+1
					nn = '%s-%d' % (name, i)
				name = nn
				self.ids_used[name] = 0
				self.ch2name[ch] = name

	def calcanames(self, node):
		"""Calculate unique names for anchors"""
		uid = node.GetUID()
		alist = node.GetAttrDef('anchorlist', [])
		for id, type, args in alist:
			aid = (uid, id)
			if type in SourceAnchors:
				aname = '%s-%s' % (self.uid2name[uid], id)
				if self.ids_used.has_key(aname):
					i = 0
					nn = '%s-%d' % (aname, i)
					while self.ids_used.has_key(nn):
						i = i+1
						nn = '%s-%d' % (aname, i)
					aname = nn
				self.aid2name[aid] = aname
				self.ids_used[aname] = 0
		if node.GetType() in interiortypes:
			for child in node.children:
				self.calcanames(child)

	def writelayout(self):
		"""Write the layout section"""
		self.fp.write('<layout>\n') # default: type="text/smil-basic-layout"
		self.fp.push()
		channels = self.root.GetContext().channels
		self.regions_defined = {}
		if len(self.top_levels) == 1:
			attrlist = ['<root-layout']
			ch = self.top_levels[0]
			if ch['type'] == 'layout':
				attrlist.append('id=%s' % nameencode(self.ch2name[ch]))
			attrlist.append('title=%s' % nameencode(ch.name))
			if ch.get('transparent', 0) == 1:
				# background-color="transparent" is default
				pass
			elif ch.has_key('bgcolor'):
				attrlist.append('background-color="#%02x%02x%02x"' % ch['bgcolor'])
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
					attrlist.append('width="%d%%"' % int(w * 100 + .5))
					attrlist.append('height="%d%%"' % int(h * 100 + .5))
				else:
					attrlist.append('width="%d"' % int(w + .5))
					attrlist.append('height="%d"' % int(h + .5))
			attrs = string.join(attrlist, ' ')
			attrs = attrs + '/>\n'
			self.fp.write(attrs)
		for ch in channels:
			dummy = mediatype(ch['type'], error=1)
			if len(self.top_levels) == 1 and \
			   ch['type'] == 'layout' and \
			   not ch.has_key('base_window'):
				# top-level layout channel has been handled
				continue
			attrlist = ['<region id=%s title=%s' %
				    (nameencode(self.ch2name[ch]),
				     nameencode(ch.name))]
			# if toplevel window, define a region elt, but
			# don't define coordinates (i.e., use defaults)
			if ch.has_key('base_window') and \
			   ch.has_key('base_winoff'):
				x, y, w, h = ch['base_winoff']
				if x+w >= 1.0: w = 0
				if y+h >= 1.0: h = 0
				data = ('left', x), ('top', y), ('width', w), ('height', h)
				for name, value in data:
					value = int(value*100)
					if value:
						attrlist.append('%s="%d%%"'%
								(name, value))
			if ch.has_key('z') and ch['z'] > 0:
				attrlist.append('z-index="%d"' % ch['z'])
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
				attrlist.append('fit="%s"' % fit)

			if ch.has_key('transparent') and \
			   ch['transparent'] == 1:
				# background-color="transparent" is default
				pass
			elif ch.has_key('bgcolor'):
				attrlist.append('background-color="#%02x%02x%02x"' % ch['bgcolor'])

## 			if len(attrlist) == 1:
## 				# Nothing to define
## 				continue
			self.regions_defined[ch] = 1
			attrs = string.join(attrlist, ' ')
			attrs = attrs + '/>\n'
			self.fp.write(attrs)
		self.fp.pop()
		self.fp.write('</layout>\n')
			
			
			
	def writenode(self, x, root = 0):
		"""Write a node (possibly recursively)"""
		type = x.GetType()
		if type == 'bag':
			print '** Choice node', \
			      x.GetRawAttrDef('name', '<unnamed>'),\
			      x.GetUID()

		interior = (type in interiortypes)
		if interior:
			if type == 'bag':
				mtype = 'cmif:bag'
			elif type == 'alt':
				mtype = 'switch'
			else:
				mtype = type
		else:
			chtype = x.GetChannelType()
			if not chtype:
				chtype = 'unknown'
			mtype = mediatype(chtype)

		attrlist = ['<%s'%mtype]
		if not interior and chtype in ('label', 'text'):
			attrlist.append('type="text/plain"')

		# if node used as destination, make sure it's id is written
		uid = x.GetUID()
		name = self.uid2name[uid]
		if not self.ids_used[name]:
			alist = x.GetAttrDef('anchorlist', [])
			hlinks = x.GetContext().hyperlinks
			for id, atype, args in alist:
				if hlinks.finddstlinks((uid, id)):
					self.ids_used[name] = 1
					break

		imm_href = None
## 		if type == 'imm':
## 			data = string.join(x.GetValues(), '\n')
## 			if mtype != 'text' and mtype[:5] != 'cmif:':
## 				# binary data, use base64 encoding
## 				import base64
## 				data = base64.encodestring(data)
## 			elif '<' in data or '&' in data:
## 				# text data containing < or &: use
## 				# <!{CDATA[...]]>
## 				# "quote" ]]> in string
## 				data = string.join(string.split(data, ']]>'),
## 						   ']]>]]<![CDATA[>')
## 				data = '<![CDATA[%s]]>\n' % data
## 			else:
## 				# other text data, can go as is
## 				data = data + '\n'
## 		else:
## 			data = None
		if type == 'imm':
			if chtype == 'html':
				mime = 'text/html'
			else:
				mime = ''
			data = string.join(x.GetValues(), '\n')
			if nonascii.search(data):
				mime = mime + ';charset=ISO-8859-1'
			imm_href = 'data:%s,%s' % (mime, MMurl.quote(data))
		data = None

		for name, func in smil_attrs:
			if name == 'src' and type == 'imm':
				value = imm_href
			else:
				value = func(self, x)
			if value:
				value = nameencode(value)
				attrlist.append('%s=%s'%(name, value))
		if interior:
			if root and (len(attrlist) > 1 or type != 'seq'):
				root = 0
			attrlist = string.join(attrlist, ' ')
			if not root:
				self.fp.write(attrlist+'>\n')
				self.fp.push()
			for child in x.GetChildren():
				self.writenode(child)
			if not root:
				self.fp.pop()
				self.fp.write('</%s>\n'%mtype)
		elif type in ('imm', 'ext'):
			attrlist = string.join(attrlist, ' ')
			self.writemedianode(x, attrlist, mtype, data)
		else:
			raise CheckError, 'bad node type in writenode'

	def writemedianode(self, x, attrlist, mtype, data):
		# XXXX Not correct for imm
		pushed = 0		# 1 if has whole-node source anchor
		hassrc = 0		# 1 if has other source anchors
		alist = x.GetAttrDef('anchorlist', [])
		# deal with whole-node source anchors
		for id, type, args in alist:
			if type == ATYPE_WHOLE:
				links = x.GetContext().hyperlinks.findsrclinks((x.GetUID(), id))
				if links:
					if pushed:
						print '** Multiple whole-node anchors', \
						      x.GetRawAttrDef('name', '<unnamed>'), \
						      x.GetUID()
					a1, a2, dir, ltype = links[0]
					self.fp.write('<a %s>\n' % self.linkattrs(a2, ltype))
					self.fp.push()
					pushed = pushed + 1
			elif type in SourceAnchors:
				hassrc = 1
		self.fp.write(attrlist)
		if not hassrc and not data:
			# if no source anchors, make empty element
			self.fp.write('/')
		self.fp.write('>\n')
		if data:
			self.fp.push()
			if data[:9] == '<![CDATA[':
				data = string.split(data, '\n')
				self.fp.write(data[0])
				level = self.fp.level
				self.fp.level = 0
				for line in data[1:]:
					self.fp.write(line)
				self.fp.level = level
			else:
				self.fp.write(data)
			self.fp.pop()
		if hassrc:
			self.fp.push()
			for id, type, args in alist:
				if type in SourceAnchors and \
				   type != ATYPE_WHOLE:
					self.writelink(x, id, type, args)
			self.fp.pop()
		if data or hassrc:
			self.fp.write('</%s>\n'%mtype)
		for i in range(pushed):
			self.fp.pop()
			self.fp.write('</a>\n')

	def linkattrs(self, a2, ltype):
		attrs = []
		if ltype == Hlinks.TYPE_CALL:
			attrs.append('show="pause"')
		elif ltype == Hlinks.TYPE_FORK:
			attrs.append('show="new"')
		# else show="replace" (default)
		uid2, aid2 = a2
		if '/' in uid2:
			if aid2:
				href = '%s#%s' % a2
			else:
				lastslash = string.rfind(uid2, '/')
				base, tag = uid2[:lastslash], uid2[lastslash+1:]
				if tag == '1':
					href = base
				else:
					href = '%s#%s' % (base, tag)
		else:
			href = '#' + self.uid2name[uid2]
		attrs.append('href=%s' % nameencode(href))
		return string.join(attrs)

	def writelink(self, x, id, atype, args):
		items = ["<anchor"]
		aid = (x.GetUID(), id)
		items.append('id=%s' % nameencode(self.aid2name[aid]))

		links = x.GetContext().hyperlinks.findsrclinks(aid)
		if len(links) > 1:
			print '** Multiple links on anchor', \
			      x.GetRawAttrDef('name', '<unnamed>'), \
			      x.GetUID()
		if links:
			a1, a2, dir, ltype = links[0]
			items.append(self.linkattrs(a2, ltype))
		if atype == ATYPE_NORMAL:
			ok = 0
			if len(args) == 4:
				x, y, w, h = tuple(args)
				try:
					x = int(x*100)
					y = int(y*100)
					w = int(w*100)
					h = int(h*100)
				except TypeError:
					pass
				else:
					ok = 1
			if ok:
				if (x, y, w, h) != (0,0,100,100):
					items.append('coords="%d%%,%d%%,%d%%,%d%%"'%
						     (x,y,w,h))
			elif args:
				print '** Unparseable args on', aid, args
			else:
				items.append('fragment-id=%s'%nameencode(id))

		self.fp.write(string.join(items) + '/>\n')

	def smiltempfile(self, node, suffix = '.html'):
		"""Return temporary file name for node"""
		nodename = self.uid2name[node.GetUID()]
		if not os.path.exists(self.tmpdirname[0]):
			os.mkdir(self.tmpdirname[0])
		filename = nodename + suffix
		return os.path.join(self.tmpdirname[1], filename)


def nameencode(value):
	"""Quote a value"""
	if '&' in value:
		value = regsub.gsub('&', '&amp;', value)
	if '>' in value:
		value = regsub.gsub('>', '&gt;', value)
	if '<' in value:
		value = regsub.gsub('<', '&lt;', value)
	if '"' in value:
		value = regsub.gsub('"', '&quot;', value)
	return '"' + value + '"'

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

