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

# This string is written at the start of a SMIL file.
SMILdecl = '''\
<?xml version="1.0" encoding="ISO-8859-1"?>
<!DOCTYPE smil PUBLIC "-//W3C//DTD SMIL 1.0//EN"
                      "http://www.w3.org/AudioVideo/Group/SMIL10.dtd">
'''

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
	return node.GetRawAttrDef(attr, None)

def getchname(writer, node):
	ch = node.GetChannel()
	if not ch:
		return None
# XXXX Removed: Sjoerd wants channel names on all nodes
##	if not writer.channels_defined.has_key(ch):
##		# Audio channels and such need not be named
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
	   (ptype == 'seq' and index > 0 and
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

#
# Mapping from SMIL attrs to functions to get them. Strings can be
# used as a shortcut for node.GetAttr
#
smil_attrs=[
	("id", getid),
	("channel", getchname),
	("src", lambda writer, node:getcmifattr(writer, node, "file")),
	("dur", lambda writer, node: getduration(writer, node, 'duration')),
	("begin", lambda writer, node: getsyncarc(writer, node, 0)),
	("end", lambda writer, node: getsyncarc(writer, node, 1)),
	("endsync", getterm),
	("repeat", lambda writer, node:getrepeat(writer, node)),
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
	return 'cmif_'+chtype

class SMILWriter:
	def __init__(self, node, fp, filename):
		self.__title = None
		self.root = node
		self.fp = fp

		self.ids_used = {}

		self.uid2name = {}
		self.calcnames1(node)

		self.ch2name = {}
		self.bases_used = {}
		self.calcchnames1(node)

		# second pass
		self.calcnames2(node)
		self.calcchnames2(node)

		# must come after second pass
		self.aid2name = {}
		self.calcanames(node)

		if len(self.bases_used) > 1:
			print '** Document uses multiple toplevel channels'
		
		self.tmpdirname = filename + '.data'

	def write(self):
		self.fp.write(SMILdecl)
		self.fp.write('<smil>\n')
		self.fp.push()
		self.fp.write('<head>\n')
		self.fp.push()
		self.fp.write('<meta name="sync" content="soft"/>\n')
		self.writelayout()
		if self.__title:
			self.fp.write('<meta name="title" content=%s/>\n' %
				      nameencode(self.__title))
		self.fp.pop()
		self.fp.write('</head>\n')
		self.fp.write('<body>\n')
		self.fp.push()
		self.writenode(self.root)
		self.fp.pop()
		self.fp.write('</body>\n')
		self.fp.pop()
		self.fp.write('</smil>\n')

	def calcnames1(self, node):
		"""Calculate unique names for nodes; first pass"""
		uid = node.GetUID()
		name = node.GetRawAttrDef('name', '')
		if name:
			name = identify(name)
			if not self.ids_used.has_key(name):
				self.ids_used[name] = 1
				self.uid2name[uid] = name
		if node.GetType() in interiortypes:
			for child in node.children:
				self.calcnames1(child)

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
			if ch.has_key('base_window'):
				base = ch['base_window']
				self.bases_used[base] = 1

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
			# remove base windows that aren't top-level
			if self.bases_used.has_key(ch.name) and \
			   ch.has_key('base_window'):
				del self.bases_used[ch.name]

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
		self.channels_defined = {}
		for ch in channels:
			dummy = mediatype(ch['type'], error=1)
			attrlist = ['<channel id=%s' %
				    nameencode(self.ch2name[ch])]
			# if toplevel window, define a channel elt, but
			# don't define coordinates (i.e., use defaults)
			if not ch.has_key('base_window'):
				if not self.__title:
					self.__title = ch.name
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
			if ch.has_key('scale'):
				scale = ch['scale']
			else:
				scale = 0
			if scale == 0:
				fit = 'meet'
			elif scale == -1:
				fit = 'slice'
			elif scale == 1:
				fit = 'hidden'
			else:
				fit = None
				print '** Channel uses unsupported scale value', name
			if fit is not None and fit != 'meet':
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
			self.channels_defined[ch] = 1
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
			for id, type, args in alist:
				if hlinks.finddstlinks((uid, id)):
					self.ids_used[name] = 1
					break

		imm_href = None
		if type == 'imm':
			data = string.join(x.GetValues(), '\n')
			if mtype != 'text':
				import base64
				data = base64.encodestring(data)
			elif '<' in data or '&' in data:
				# "quote" ]]> in string
				data = string.join(string.split(data, ']]>'),
						   ']]>]]<![CDATA[>')
				data = '<![CDATA[%s]]>\n' % data
			else:
				data = data + '\n'
## 			if chtype == 'html':
## 				suff = '.html'
## 			else:
## 				suff = '.txt'
## 			fname = self.smiltempfile(x, suff)
## 			fp = open(fname, 'w')
## 			data = string.join(x.GetValues(), '\n')
## 			if data[-1:] != '\n':
## 				data = data + '\n'
## 			fp.write(data)
## 			fp.close()
## 			imm_href = MMurl.pathname2url(fname)
		else:
			data = None

		for name, func in smil_attrs:
			if name == 'src' and type == 'imm':
				value = None
			else:
				value = func(self, x)
			if value:
				value = nameencode(value)
				attrlist.append('%s=%s'%(name, value))
		if interior:
			attrlist = string.join(attrlist, ' ')
			if not root or len(attrlist) > 1:
				root = 0
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
				lastslash = string.rfind('/', uid2)
				href = '%s#%s' % (uid2[:lastslash], uid2[lastslash+1:])
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
		if not os.path.exists(self.tmpdirname):
			os.mkdir(self.tmpdirname)
		filename = nodename + suffix
		return os.path.join(self.tmpdirname, filename)


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
			if rv and rv[-1] != '_':
				rv.append('_')
	# the first character must not be a digit
	if rv and rv[0] in string.digits:
		rv.insert(0, '_')
	return string.join(rv, '')

