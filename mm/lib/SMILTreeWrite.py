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

NSprefix = 'GRiNS'
# This string is written at the start of a SMIL file.
SMILdecl = '<?xml version="1.0" encoding="ISO-8859-1"?>\n'
doctype = '<!DOCTYPE smil PUBLIC "%s"\n\
                      "%s">\n' % (SMILpubid,SMILdtd)
xmlns = 'xmlns:%s' % NSprefix

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

def WriteFile(root, filename, cleanSMIL = 0):
	fp = IndentedFile(open(filename, 'w'))
	writer = SMILWriter(root, fp, filename, cleanSMIL)
	writer.write()
	if os.name == 'mac':
		import macfs
		import macostools
		fss = macfs.FSSpec(filename)
		fss.SetCreatorType('GRIN', 'TEXT')
		macostools.touched(fss)

import StringIO
class MyStringIO(StringIO.StringIO):
	def close(self):
		pass

def WriteString(root, cleanSMIL = 0):
	fp = IndentedFile(MyStringIO())
	writer = SMILWriter(root, fp, '<string>', cleanSMIL)
	writer.write()
	return fp.fp.getvalue()

#
# Functions to encode data items
#
def getid(writer, node):
	uid = node.GetUID()
	name = writer.uid2name[uid]
	if writer.ids_used[name]:
		return name

def getcmifattr(writer, node, attr):
	val = MMAttrdefs.getattr(node, attr)
	if val is not None:
		val = str(val)
	return val

def getrawcmifattr(writer, node, attr):
	val = node.GetRawAttrDef(attr, None)
	if val is not None:
		val = str(val)
	return val

def getmimetype(writer, node):
	if node.GetType() not in leaftypes:
		return
	val = node.GetRawAttrDef('mimetype', None)
	if val is not None:
		return val
	chtype = node.GetChannelType()
	if chtype in ('label', 'text'):
		return 'text/plain'

def getchname(writer, node):
	ch = node.GetChannel()
	if not ch:
		return None
	return writer.ch2name[ch]

def getduration(writer, node, attr):
	duration = MMAttrdefs.getattr(node, attr)
	if not duration:		# 0 or None
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
	if srcside == 0 and \
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
		for s in siblings:
			if srcuid == s.GetUID():
				# in scope
				break
		else:
			# out of scope
			rv = fixsyncarc(writer, node, srcuid, srcside,
					delay, dstside, rv)
	return rv

def fixsyncarc(writer, node, srcuid, srcside, delay, dstside, rv):
	if dstside != 0 or srcside != 0:
		print '** Out of scope syncarc to',\
		      node.GetRawAttrDef('name', '<unnamed>'),\
		      node.GetUID()
		return rv
	srcnode = node.GetContext().mapuid(srcuid)
	a = node.CommonAncestor(srcnode)
	x = srcnode
	while x is not a:
		p = x.GetParent()
		t = p.GetType()
		if t != 'par' and (t != 'seq' or x is not p.GetChild(0)):
			print '** Out of scope syncarc to',\
			      node.GetRawAttrDef('name', '<unnamed>'),\
			      node.GetUID()
			return rv
		for xuid, xside, xdelay, yside in MMAttrdefs.getattr(x, 'synctolist'):
			if yside == 0 and xdelay != 0:
				# too compicated
				print '** Out of scope syncarc to',\
				      node.GetRawAttrDef('name', '<unnamed>'),\
				      node.GetUID()
				return rv
		x = p
	x = node
	while x is not a:
		p = x.GetParent()
		t = p.GetType()
		if t != 'par' and (t != 'seq' or x is not p.GetChild(0)):
			print '** Out of scope syncarc to',\
			      node.GetRawAttrDef('name', '<unnamed>'),\
			      node.GetUID()
			return rv
		for xuid, xside, xdelay, yside in MMAttrdefs.getattr(x, 'synctolist'):
			if yside == 0 and xdelay != 0 and x is not node:
				# too compicated
				print '** Out of scope syncarc to',\
				      node.GetRawAttrDef('name', '<unnamed>'),\
				      node.GetUID()
				return rv
		x = p
	print '*  Fixing out of scope syncarc to',\
	      node.GetRawAttrDef('name', '<unnamed>'),\
	      node.GetUID()
	return '%.3fs' % delay

def getterm(writer, node):
	terminator = MMAttrdefs.getattr(node, 'terminator')
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
	value = MMAttrdefs.getattr(node, 'loop')
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

def getugroup(writer, node):
	if not node.GetContext().usergroups:
		return
	u_group = MMAttrdefs.getattr(node, 'u_group')
	if u_group == 'undefined':
		return
	return writer.ugr2name[u_group]

def getlayout(writer, node):
	if not node.GetContext().layouts:
		return
	layout = MMAttrdefs.getattr(node, 'layout')
	if layout == 'undefined':
		return
	return writer.layout2name[layout]

#
# Mapping from SMIL attrs to functions to get them. Strings can be
# used as a shortcut for node.GetAttr
#
smil_attrs=[
	("id", getid),
	("title", lambda writer, node:getcmifattr(writer, node, "title")),
	("region", getchname),
	("src", lambda writer, node:getcmifattr(writer, node, "file")),
	("type", getmimetype),
	("author", lambda writer, node:getcmifattr(writer, node, "author")),
	("copyright", lambda writer, node:getcmifattr(writer, node, "copyright")),
	("abstract", lambda writer, node:getcmifattr(writer, node, "abstract")),
	("dur", lambda writer, node: getduration(writer, node, 'duration')),
	("begin", lambda writer, node: getsyncarc(writer, node, 0)),
	("end", lambda writer, node: getsyncarc(writer, node, 1)),
	("clip-begin", lambda writer, node: getcmifattr(writer, node, 'clipbegin')),
	("clip-end", lambda writer, node: getcmifattr(writer, node, 'clipend')),
	("endsync", getterm),
	("repeat", lambda writer, node:getrepeat(writer, node)),
	("system-bitrate", lambda writer, node:getrawcmifattr(writer, node, "system_bitrate")),
	("system-captions", getcaptions),
	("system-language", lambda writer, node:getrawcmifattr(writer, node, "system_language")),
	("system-overdub-or-captions", lambda writer, node:getrawcmifattr(writer, node, "system_overdub_or_captions")),
	("system-required", lambda writer, node:getrawcmifattr(writer, node, "system_required")),
	("system-screen-size", getscreensize),
	("system-screen-depth", lambda writer, node:getrawcmifattr(writer, node, "system_screen_depth")),
	("choice-index", getbagindex),
	("u-group", getugroup),
	("layout", getlayout),
]
cmif_node_attrs_ignore = [
	'arm_duration', 'styledict', 'name', 'bag_index', 'anchorlist',
	'channel', 'file', 'duration', 'system_bitrate', 'system_captions',
	'system_language', 'system_overdub_or_captions', 'system_required',
	'system_screen_size', 'system_screen_depth', 'layout',
	'clipbegin', 'clipend', 'u_group', 'loop', 'synctolist',
	'author', 'copyright', 'abstract', 'mimetype', 'terminator',
	]
cmif_chan_attrs_ignore = [
	'id', 'title', 'base_window', 'base_winoff', 'z', 'scale',
	'transparent', 'bgcolor', 'winpos', 'winsize', 'rect', 'center',
	'drawbox', 'units',
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
	'midi':'audio',
	'RealAudio':'audio',
	'RealPix':'img',
	'RealText':'text',
	'RealVideo':'video',
	'unknown': 'ref',
}

def mediatype(chtype, error=0):
	if smil_mediatype.has_key(chtype):
		return smil_mediatype[chtype], smil_mediatype[chtype]
	if error and chtype != 'layout':
		print '** Unimplemented channel type', chtype
	return '%s:%s' % (NSprefix, chtype), '%s %s' % (GRiNSns, chtype)

class SMILWriter(SMIL):
	def __init__(self, node, fp, filename, cleanSMIL = 0):
		self.__cleanSMIL = cleanSMIL	# if set, no GRiNS namespace

		self.__isopen = 0
		self.__stack = []

		self.uses_cmif_extension = 0
		self.root = node
		self.fp = fp
		self.__title = node.GetContext().gettitle()

		self.ids_used = {}

		self.ugr2name = {}
		self.calcugrnames(node)

		self.layout2name = {}
		self.calclayoutnames(node)

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

	def push(self):
		if self.__isopen:
			self.fp.write('>\n')
			self.__isopen = 0
		self.fp.push()

	def pop(self):
		fp = self.fp
		if self.__isopen:
			fp.write('/>\n')
			self.__isopen = 0
			del self.__stack[-1]
		fp.pop()
		fp.write('</%s>\n' % self.__stack[-1][0])
		del self.__stack[-1]

	def close(self):
		fp = self.fp
		if self.__isopen:
			fp.write('/>\n')
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
			write('/>\n')
			self.__isopen = 0
			del self.__stack[-1]
		if self.__stack and self.__stack[-1][1]:
			hasprefix = 1
		else:
			hasprefix = 0
		if not hasprefix and not self.__cleanSMIL:
			for attr, val in attrs:
				if attr == xmlns:
					hasprefix = 1
					break
				if attr[:len(NSprefix)] == NSprefix:
					attrs.insert(0, (xmlns, GRiNSns))
					hasprefix = 1
					break
		if not hasprefix:
			if tag[:len(NSprefix)] == NSprefix:
				if self.__cleanSMIL:
					# ignore this tag
					# XXX is this correct?
					return
				attrs.insert(0, (xmlns, GRiNSns))
				hasprefix = 1
		write('<' + tag)
		for attr, val in attrs:
			if not self.__cleanSMIL or \
			   (attr[:len(NSprefix)] != NSprefix and
			    attr != xmlns):
				write(' %s=%s' % (attr, nameencode(val)))
		self.__isopen = 1
		self.__stack.append((tag, hasprefix))

	def write(self):
		import version
		ctx = self.root.GetContext()
		fp = self.fp
		fp.write(SMILdecl)
		fp.write(doctype)
		attrlist = []
		if self.uses_cmif_extension:
			attrlist.append((xmlns, GRiNSns))
		self.writetag('smil', attrlist)
		self.push()
		self.writetag('head')
		self.push()
##		self.writetag('meta', [('name', 'sync'), ('content', 'soft')])
		if self.__title:
			self.writetag('meta', [('name', 'title'),
					       ('content', self.__title)])
		self.writetag('meta', [('name', 'generator'),
				       ('content','GRiNS %s'%version.version)])
		if ctx.baseurl and ctx.baseurlset:
			self.writetag('meta', [('name', 'base'),
					       ('content', ctx.baseurl)])
		for key, val in ctx.attributes.items():
			self.writetag('meta', [('name', key),
					       ('content', val)])
		self.writelayout()
		self.writeusergroups()
		self.writegrinslayout()
		self.pop()
		self.writetag('body')
		self.push()
		self.writenode(self.root, root = 1)
##		self.pop()
##		self.pop()
		self.close()

	def calcugrnames(self, node):
		"""Calculate unique names for usergroups"""
		usergroups = node.GetContext().usergroups
		if not usergroups:
			return
		self.uses_cmif_extension = 1
		for ugroup in usergroups.keys():
			name = identify(ugroup)
			if self.ids_used.has_key(name):
				i = 0
				nn = '%s-%d' % (name, i)
				while self.ids_used.has_key(nn):
					i = i+1
					nn = '%s-%d' % (name, i)
				name = nn
			self.ids_used[name] = 1
			self.ugr2name[ugroup] = name

	def calclayoutnames(self, node):
		"""Calculate unique names for layouts"""
		layouts = node.GetContext().layouts
		if not layouts:
			return
		self.uses_cmif_extension = 1
		for layout in layouts.keys():
			name = identify(layout)
			if self.ids_used.has_key(name):
				i = 0
				nn = '%s-%d' % (name, i)
				while self.ids_used.has_key(nn):
					i = i+1
					nn = '%s-%d' % (name, i)
				name = nn
			self.ids_used[name] = 1
			self.layout2name[layout] = name

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
		alist = MMAttrdefs.getattr(node, 'anchorlist')
		for id, type, args in alist:
			aid = (uid, id)
			if type in SourceAnchors:
				if isidre.match(id) is None or \
				   self.ids_used.has_key(id):
					aname = '%s-%s' % (self.uid2name[uid], id)
				else:
					aname = id
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

	def writeusergroups(self):
		u_groups = self.root.GetContext().usergroups
		if not u_groups:
			return
		self.writetag('%s:user-attributes' % NSprefix)
		self.push()
		for key, val in u_groups.items():
			attrlist = []
			attrlist.append(('id', self.ugr2name[key]))
			title, u_state, override = val
			if title:
				attrlist.append(('title', title))
			if u_state != 'RENDERED':
				attrlist.append(('u-state', u_state))
			if override != 'allowed':
				attrlist.append(('override', override))
			self.writetag('%s:u-group' % NSprefix, attrlist)
		self.pop()

	def writegrinslayout(self):
		layouts = self.root.GetContext().layouts
		if not layouts:
			return
		self.writetag('%s:layouts' % NSprefix)
		self.push()
		for name, chans in layouts.items():
			channames = []
			for ch in chans:
				channames.append(self.ch2name[ch])
			self.writetag('%s:layout' % NSprefix,
				      [('id', self.layout2name[name]),
				       ('regions', string.join(channames))])
		self.pop()

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
				mtype = '%s:choice' % NSprefix
				xtype = '%s choice' % GRiNSns
			elif type == 'alt':
				xtype = mtype = 'switch'
			else:
				xtype = mtype = type
		else:
			chtype = x.GetChannelType()
			if not chtype:
				chtype = 'unknown'
			mtype, xtype = mediatype(chtype)

		attrlist = []

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
		if type == 'imm':
			if chtype == 'html':
				mime = 'text/html'
			else:
				mime = ''
			data = string.join(x.GetValues(), '\n')
			if nonascii.search(data):
				mime = mime + ';charset=ISO-8859-1'
			imm_href = 'data:%s,%s' % (mime, MMurl.quote(data))

		attributes = self.attributes[xtype]
		for name, func in smil_attrs:
			if name == 'src' and type == 'imm':
				value = imm_href
			else:
				value = func(self, x)
			# gname is the attribute name as recorded in attributes
			# name is the attribute name as recorded in SMIL file
			gname = '%s %s' % (GRiNSns, name)
			if attributes.has_key(gname):
				name = '%s:%s' % (NSprefix, name)
			else:
				gname = name
			# only write attributes that have a value and are
			# legal for the type of node
			# other attributes are caught below
			if value and attributes.has_key(gname) and \
			   value != attributes[gname]:
				attrlist.append((name, value))
		for key, val in x.GetAttrDict().items():
			if key[-7:] != '_winpos' and \
			   key[-8:] != '_winsize' and \
			   key not in cmif_node_attrs_ignore:
				attrlist.append(('%s:%s' % (NSprefix, key),
						 MMAttrdefs.valuerepr(key, val)))
		if interior:
			if root and (attrlist or type != 'seq'):
				root = 0
			if not root:
				self.writetag(mtype, attrlist)
				self.push()
			for child in x.GetChildren():
				self.writenode(child)
			if not root:
				self.pop()
		elif type in ('imm', 'ext'):
			self.writemedianode(x, attrlist, mtype)
		else:
			raise CheckError, 'bad node type in writenode'

	def writemedianode(self, x, attrlist, mtype):
		# XXXX Not correct for imm
		pushed = 0		# 1 if has whole-node source anchor
		hassrc = 0		# 1 if has other source anchors
		alist = MMAttrdefs.getattr(x, 'anchorlist')
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
					self.writetag('a', self.linkattrs(a2, ltype))
					self.push()
					pushed = pushed + 1
			elif type in SourceAnchors:
				hassrc = 1
		self.writetag(mtype, attrlist)
		if hassrc:
			self.push()
			for id, type, args in alist:
				if type in SourceAnchors and \
				   type != ATYPE_WHOLE:
					self.writelink(x, id, type, args)
			self.pop()
		for i in range(pushed):
			self.pop()

	def linkattrs(self, a2, ltype):
		attrs = []
		if ltype == Hlinks.TYPE_CALL:
			attrs.append(('show', "pause"))
		elif ltype == Hlinks.TYPE_FORK:
			attrs.append(('show', "new"))
		# else show="replace" (default)
		uid2, aid2 = a2
		if '/' in uid2:
			if aid2:
				href, tag = a2
			else:
				lastslash = string.rfind(uid2, '/')
				href, tag = uid2[:lastslash], uid2[lastslash+1:]
				if tag == '1':
					tag = None
		else:
			href = ''
			tag = self.uid2name[uid2]
		if tag:
			href = href + '#' + tag
		attrs.append(('href', href))
		return attrs

	def writelink(self, x, id, atype, args):
		attrlist = []
		aid = (x.GetUID(), id)
		attrlist.append(('id', self.aid2name[aid]))

		links = x.GetContext().hyperlinks.findsrclinks(aid)
		if len(links) > 1:
			print '** Multiple links on anchor', \
			      x.GetRawAttrDef('name', '<unnamed>'), \
			      x.GetUID()
		if links:
			a1, a2, dir, ltype = links[0]
			attrlist[len(attrlist):] = self.linkattrs(a2, ltype)
		if atype == ATYPE_NORMAL:
			ok = 0
			if len(args) == 4:
				x, y, w, h = tuple(args)
				try:
					x = int(x*100 + 0.5)
					y = int(y*100 + 0.5)
					w = int(w*100 + 0.5)
					h = int(h*100 + 0.5)
				except TypeError:
					pass
				else:
					ok = 1
			if ok:
				if x < 0: x = 0
				if y < 0: y = 0
				if w > 100: w = 100
				if h > 100: h = 100
				x0, y0, x1, y1 = x, y, x+w, y+h
				if (x0, y0, x1, y1) != (0,0,100,100):
					attrlist.append(('coords',
							 "%d%%,%d%%,%d%%,%d%%"%
							 (x0,y0,x1,y1)))
			elif args:
				print '** Unparseable args on', aid, args
			else:
				attrlist.append(('%s:fragment-id' % NSprefix,
						 id))
		self.writetag('anchor', attrlist)

	def smiltempfile(self, node, suffix = '.html'):
		"""Return temporary file name for node"""
		nodename = self.uid2name[node.GetUID()]
		if not os.path.exists(self.tmpdirname[0]):
			os.mkdir(self.tmpdirname[0])
		filename = nodename + suffix
		return os.path.join(self.tmpdirname[1], filename)


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

