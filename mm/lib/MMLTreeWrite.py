__version__ = "$Id$"

# MMWrite -- Multimedia tree writing interface


from MMExc import *		# Exceptions
from MMNode import alltypes, leaftypes, interiortypes
import MMCache
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
	if not writer.channels_defined.has_key(ch):
		# Audio channels and such need not be named
		return None
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
	sign, delay = encodeduration(delay)
	if delay:
		rv = rv + sign + '(%s)'%delay
	return rv
			
	
#
# Mapping from MML attrs to functions to get them. Strings can be
# used as a shortcut for node.GetAttr
#
mml_attrs=[
	("id", lambda writer, node:getid(writer, node)),
	("channel", lambda writer, node:getchname(writer, node)),
	("href", lambda writer, node:getcmifattr(writer, node, "file")),
	("dur", lambda writer, node: getduration(writer, node, 'duration')),
	("begin",  lambda writer, node: getsyncarc(writer, node, 0)),
	("end",  lambda writer, node: getsyncarc(writer, node, 1)),
]

# Mapping from CMIF channel types to mml media types
mml_mediatype={
	'text':'text',
	'sound':'audio',
	'image':'img',
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
		self.fp.write('<!doctype mml system>\n')
		self.fp.write('<mml>\n')
		self.fp.push()
		self.writelayout()
		self.writenode(self.root)
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
		self.fp.write('<layout type="text/mml-basic-layout">\n')
		self.fp.push()
		channels = self.root.GetContext().channels
		self.channels_defined = {}
		for ch in channels:
			dummy = mediatype(ch['type'], error=1)
			attrlist = ['<channel name=%s' %
				    nameencode(self.ch2name[ch])]
			if not ch.has_key('base_window'):
				continue	# Skip toplevel windows
			if not ch.has_key('base_winoff'):
				continue
			x, y, w, h = ch['base_winoff']
			data = ('x', x), ('y', y), ('w', w), ('h', h)
			for name, value in data:
				value = int(value*100)
				if value:
					attrlist.append('%s="%d%%"'%
							(name, value))
			if len(attrlist) == 1:
				# Nothing to define
				continue
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
			chtype = type
		else:
			chtype = x.GetChannelType()
			if not chtype:
				chtype = 'unknown'
			chtype = mediatype(chtype)

		if type == 'imm':
			fname = self.mmltempfile(x)
			fp = open(fname, 'w')
			data = string.join(x.GetValues(), '\n')
			if data[-1] != '\n':
				data = data + '\n'
			fp.write(data)
			fp.close()
			imm_href = urllib.pathname2url(fname)
		else:
			imm_href = None
		attrlist = ['<%s'%chtype]
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
			self.fp.write('</%s>\n'%chtype)
		elif type in ('imm', 'ext'):
			# XXXX Not correct for imm
			self.fp.write(attrlist+'/>\n')
		else:
			raise CheckError, 'bad node type in writenode'

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

