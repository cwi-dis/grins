__version__ = "$Id$"

# MMWrite -- Multimedia tree writing interface


from MMExc import *		# Exceptions
from MMNode import alltypes, leaftypes, interiortypes
import MMCache
import MMAttrdefs
import Hlinks
import AnchorDefs
import string
import os
import urllib
import regsub

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
	writer = MMLWriter(root, fp, filename)
	writer.write()
	fp.write('\n')
	fp.close()

#
# Functions to encode data items
#
def getid(writer, node):
	uid = node.GetUID()
	return writer.uid2name[uid]

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
	duration = node.GetRawAttrDef(attr, -1)
	if duration == -1:
		return None
	sign, value = encodeduration(duration)
	if sign != '+':
		print '** Illegal duration', \
		      node.GetRawAttrDef('name', '<unnamed>'),\
		      node.GetUID()
	return value
		
def encodeduration(duration):
	if not duration:
		return '+', 0
	if duration < 0:
		sign = '-'
		duration = -duration
	else:
		sign = '+'
	secs = duration % 60
	rest = int(secs/60)
	hrs, mins = rest / 60, rest % 60
	return sign, '%02d:%02d:%06.03f'%(hrs, mins, secs)

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
	srcuid, srcside, delay, dstside = arc
	srcname = writer.uid2name[srcuid]
	rv = 'id(%s)'%srcname
	if srcside:
		rv = rv+'(end)'
	else:
		rv = rv+'(begin)'
	sign, delay = encodeduration(delay)
	if delay:
		rv = rv + sign + delay
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

#
# Mapping from MML attrs to functions to get them. Strings can be
# used as a shortcut for node.GetAttr
#
mml_attrs=[
	("id", getid),
	("loc", getchname),
	("href", lambda writer, node:getcmifattr(writer, node, "file")),
	("dur", lambda writer, node: getduration(writer, node, 'duration')),
	("begin", lambda writer, node: getsyncarc(writer, node, 0)),
	("end", lambda writer, node: getsyncarc(writer, node, 1)),
	("endsync", getterm),
	("repeat", lambda writer, node:getcmifattr(writer, node, "loop")),
]

# Mapping from CMIF channel types to mml media types
mml_mediatype={
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
	if mml_mediatype.has_key(chtype):
		return mml_mediatype[chtype]
	if error and chtype != 'layout':
		print '** Unimplemented channel type', chtype
	return 'cmif_'+chtype

class MMLWriter:
	def __init__(self, node, fp, filename):
		self.root = node
		self.fp = fp

		self.names_used = {'':1}
		self.uid2name = {}
		self.calcnames(node)

		self.chnames_used = {'':1}
		self.ch2name = {}
		self.bases_used = {}
		self.calcchnames(node)
		if len(self.bases_used) > 1:
			print '** Document uses multiple toplevel channels'
		
		self.tmpdirname = filename + '.data'

	def write(self):
		self.fp.write('<mml lipsync="false">\n')
		self.fp.push()
		self.fp.write('<head>\n')
		self.fp.push()
		self.writelayout()
		self.fp.pop()
		self.fp.write('</head>\n')
		self.fp.write('<body>\n')
		self.fp.push()
		self.writenode(self.root)
		self.writelinks()
		self.fp.pop()
		self.fp.write('</body>\n')
		self.fp.pop()
		self.fp.write('</mml>\n')

	def calcnames(self, node):
		"""Calculate unique names for nodes"""
		uid = node.GetUID()
		name = identify(node.GetRawAttrDef('name', ''))
		if self.names_used.has_key(name):
			if not name:
				name = 'node'
			name = '%s_%s'%(name, uid)
		if self.names_used.has_key(name):
			raise 'DuplicateNameError', name
		self.names_used[name] = 1
		self.uid2name[uid] = name
		if node.GetType() in interiortypes:
			for child in node.children:
				self.calcnames(child)

	def calcchnames(self, node):
		"""Calculate unique names for channels"""
		context = node.GetContext()
		channels = context.channels
		for ch in channels:
			name = identify(ch.name)
			if self.chnames_used.has_key(name):
				num = 1
				while 1:
					nn = '%s_%d'%(name, num)
					if not self.chnames_used.has_key(nn):
						name = nn
						break
					num = num + 1
			self.chnames_used[name] = 1
			self.ch2name[ch] = name

			if ch.has_key('base_window'):
				base = ch['base_window']
				self.bases_used[base] = 1

	def writelayout(self):
		"""Write the layout section"""
		self.fp.write('<layout type="text/mml-basic">\n')
		self.fp.push()
		channels = self.root.GetContext().channels
		self.channels_defined = {}
		for ch in channels:
			dummy = mediatype(ch['type'], error=1)
			attrlist = ['<tuner id=%s' %
				    nameencode(self.ch2name[ch])]
			# if toplevel window, define a tuner elt, but
			# don't define coordinates (i.e., use defaults)
			if ch.has_key('base_window') and \
			   ch.has_key('base_winoff'):
				x, y, w, h = ch['base_winoff']
				data = ('x', x), ('y', y), ('width', w), ('height', h)
				for name, value in data:
					value = int(value*100)
					if value:
						attrlist.append('%s="%d%%"'%
								(name, value))
			if ch.has_key('z'):
				# CMIF default is 0, MML default is 1
				attrlist.append('z="%d"' % (ch['z'] + 1))
## 			if len(attrlist) == 1:
## 				# Nothing to define
## 				continue
			self.channels_defined[ch] = 1
			attrs = string.join(attrlist, ' ')
			attrs = attrs + '/>\n'
			self.fp.write(attrs)
		self.fp.pop()
		self.fp.write('</layout>\n')
			
			
			
	def writenode(self, x):
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

		imm_href = None
		if type == 'imm':
			if chtype == 'label':
				sep = '</p>\n<p>'
			else:
				sep = '\n'
			fname = self.mmltempfile(x)
			fp = open(fname, 'w')
			data = string.join(x.GetValues(), sep)
			if data[-1] != '\n':
				data = data + '\n'
			if chtype == 'text':
				data = string.join(string.split(data, '\n\n'),
						   '</p>\n<p>')
			if chtype in ('text', 'label'):
				data = '<p>%s</p>\n' % data
			fp.write(data)
			fp.close()
			imm_href = urllib.pathname2url(fname)
		elif type == 'ext':
			if chtype == 'label':
				try:
					fp = open(MMAttrdefs.getattr(x, 'file'))
				except IOError:
					pass
				else:
					data = fp.readlines()
					fp.close()
					if data and data[-1] == '':
						del data[-1]
					fname = self.mmltempfile(x)
					fp = open(fname, 'w')
					fp.write('<p>')
					fp.write(string.join(data, '</p>\n<p>'))
					fp.write('</p>\n')
					imm_href = urllib.pathname2url(fname)
			if chtype == 'text':
				try:
					fp = open(MMAttrdefs.getattr(x, 'file'))
				except IOError:
					pass
				else:
					data = fp.read()
					fp.close()
					data = string.join(string.split(data,
									'\n\n'),
							   '</p>\n<p>')
					fname = self.mmltempfile(x)
					fp = open(fname, 'w')
					fp.write('<p>')
					fp.write(data)
					fp.write('</p>\n')
					imm_href = urllib.pathname2url(fname)
		attrlist = ['<%s'%mtype]
		for name, func in mml_attrs:
			if name == 'href' and imm_href:
				value = imm_href
			else:
				value = func(self, x)
			if value:
				value = nameencode(value)
				attrlist.append('%s=%s'%(name, value))
		attrlist = string.join(attrlist, ' ')

		if interior:
			self.fp.write(attrlist+'>\n')
			self.fp.push()
			for child in x.GetChildren():
				self.writenode(child)
			self.fp.pop()
			self.fp.write('</%s>\n'%mtype)
		elif type in ('imm', 'ext'):
			# XXXX Not correct for imm
			self.fp.write(attrlist+'/>\n')
		else:
			raise CheckError, 'bad node type in writenode'

	def writelinks(self):
		context = self.root.GetContext()
		links = context.hyperlinks
		linklist = links.getall()
		for a1, a2, dir, type in linklist:
			if dir == Hlinks.DIR_1TO2:
				self.writelink(a1, a2, type)
			elif dir == Hlinks.DIR_2TO1:
				self.writelink(a2, a1, type)
			else:
				self.writelink(a1, a2, type)
				self.writelink(a2, a1, type)

	def writelink(self, a1, a2, type):
		items = ["<hlink"]
		if type == Hlinks.TYPE_CALL:
			items.append('replace="pause"')
		elif type == Hlinks.TYPE_FORK:
			items.append('replace="new"')
		self.fp.write(string.join(items, ' ') + '>\n')
		self.fp.push()
		self.writeanchor(a1, "src")
		self.writeanchor(a2, "dst")
		self.fp.pop()
		self.fp.write('</hlink>\n')

	def writeanchor(self, anchor, role):
		# XXXX external anchor handling is broken
		context = self.root.GetContext()
		items = ["<anchor"]
		items.append('role="%s"'%role)
		uid, aid = anchor
		if '/' in uid:
			# External. Try to convert
			lastslash = string.rfind('/', uid)
			href = uid[:lastslash] + '#' + uid[lastslash+1:]
		else:
			# Internal
			href = '#' + self.uid2name[uid]
		items.append('href="%s"'%href)
		tp, args = self.getanchor(uid, aid, href)
		# First fixup unimplemented tps
		if tp == AnchorDefs.ATYPE_AUTO:
			print "** unsupported auto anchor on", href
			tp = AnchorDefs.ATYPE_DEST
		if tp == AnchorDefs.ATYPE_PAUSE:
			print "** unsupported pausing anchor on", href
			tp = AnchorDefs.ATYPE_NORMAL
		if tp == AnchorDefs.ATYPE_COMP:
			print "** unsupported comp anchor on", href
			tp = AnchorDefs.ATYPE_DEST
		if tp == AnchorDefs.ATYPE_ARGS:
			print "** unsupported args anchor on", href
			tp = AnchorDefs.ATYPE_DEST # XXXX ATYPE_WHOLE
		if tp == AnchorDefs.ATYPE_DEST:
			pass
## XXXX Not yet
##		elif tp == AnchorDefs.ATYPE_WHOLE:
##			pass
		elif tp == AnchorDefs.ATYPE_NORMAL:
			# XXXX Hack: see if these are coordinates
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
					print "** Document uses coords attribute in anchor"
					items.append('shape="rect"')
					items.append('coords="%d%%,%d%% %d%%,%d%%"'%
						     (x,y,w,h))
			elif args:
				print '** Unparseable args on', href, args
		self.fp.write(string.join(items, ' ')+'/>\n')

	def getanchor(self, uid, aid, href):
		context = self.root.GetContext()
		node = context.mapuid(uid)
		alist = node.GetAttrDef('anchorlist', [])
		for id, type, args in alist:
			if id == aid:
				return type, args
		print '** undefined anchor', href, aid
		return AnchorDefs.ATYPE_DEST, []

	def mmltempfile(self, node):
		"""Return temporary file name for node"""
		nodename = self.uid2name[node.GetUID()]
		if not os.path.exists(self.tmpdirname):
			os.mkdir(self.tmpdirname)
		filename = nodename + '.html'
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
	name = string.lower(name)
	rv = ''
	for ch in name:
		if ch in namechars:
			rv = rv + ch
		else:
			if rv and rv[-1] != '_':
				rv = rv + '_'
	return rv

