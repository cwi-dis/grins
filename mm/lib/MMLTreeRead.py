import xmllib
import MMNode
from windowinterface import UNIT_PXL
from HDTL import HD, TL
import string

error = 'MMLTreeRead.error'

LAYOUT_NONE = 0				# must be 0
LAYOUT_MML = 1
LAYOUT_UNKNOWN = -1

class MMLParser(xmllib.XMLParser):
	def __init__(self, context, verbose = 0):
		xmllib.XMLParser.__init__(self, verbose)
		self.__seen_mml = 0
		self.__in_mml = 0
		self.__in_layout = LAYOUT_NONE
		self.__context = context
		self.__root = None
		self.__container = None
		self.__channels = {}
		self.__width = self.__height = 0
		self.__layout = None
		self.__nodemap = {}

	def GetRoot(self):
		if not self.__root:
			raise error, 'empty document'
		return self.__root

	def MakeRoot(self, type):
		self.__root = self.__context.newnodeuid(type, '1')
		return self.__root

	def SyncArc(self, node, attr, val):
		try:
			synctolist = node.attrdict['synctolist']
		except KeyError:
			node.attrdict['synctolist'] = synctolist = []
		if attr == 'begin':
			yside = HD
		else:
			yside = TL
		name, counter, delay = _parsetime(val)
		if name is None:
			# relative to parent/previous
			parent = node.GetParent()
			ptype = parent.GetType()
			if ptype == 'seq':
				xnode = None
				for n in parent.GetChildren():
					if n is node:
						break
					xnode = n
				else:
					raise error, 'node not in parent'
				if xnode is None:
					# first, relative to parent
					xside = HD # rel to start of parent
					xnode = parent
				else:
					# not first, relative to previous
					xside = TL # rel to end of previous
			else:
				xside = HD # rel to start of parent
				xnode = parent
			synctolist.append((xnode.GetUID(), xside, delay, yside))
		else:
			# relative to other node
			for n in node.GetParent().GetChildren():
				if n.attrdict.has_key('name') and \
				   n.attrdict['name'] == val:
					xnode = n
					break
			else:
				print 'warning: out of scope sync arc'
				try:
					xnode = self.__nodemap[name]
				except KeyError:
					print 'warning: ignoring unknown node in syncarc'
					return
			if counter == -1:
				xside = TL
				counter = 0
			else:
				xside = HD
			synctolist.append((xnode.GetUID(), xside, delay + counter, yside))

	def AddAttrs(self, node, attributes):
		node.__syncarcs = []
		for attr, val in attributes:
			val = self.translate_references(val)
			if attr == 'id':
				node.attrdict['name'] = val
				if self.__nodemap.has_key(val):
					print 'warning: node name %s not unique'%val
				self.__nodemap[val] = node
			elif attr == 'href':
				node.attrdict['file'] = val
			elif attr == 'channel':
				# deal with channel later
				node.__channel = val
			elif attr == 'begin' or attr == 'end':
				node.__syncarcs.append(attr, val)
			elif attr == 'dur':
				node.attrdict['duration'] = _parsecounter(val, 0)

	def NewNode(self, mediatype, attributes):
		if not self.__container:
			raise error, 'node not in container'
		node = self.__context.newnode('ext')
		node.attrdict['transparent'] = -1
		self.AddAttrs(node, attributes)
		self.__container._addchild(node)
		node.__mediatype = mediatype

	def NewContainer(self, type, attributes):
		if not self.__in_mml:
			raise error, '%s not in mml' % type
		if self.__in_layout:
			raise error, '%s in layout' % type
		if not self.__root:
			node = self.MakeRoot(type)
		elif not self.__container:
			raise error, '%s not in container' % type
		else:
			node = self.__context.newnode(type)
			self.__container._addchild(node)
		self.__container = node
		self.AddAttrs(node, attributes)

	def EndContainer(self):
		self.__container = self.__container.GetParent()

	def Recurse(self, root, *funcs):
		for func in funcs:
			func(root)
		for node in root.GetChildren():
			apply(self.Recurse, (node,) + funcs)

	def FixSyncArcs(self, node):
		for attr, val in node.__syncarcs:
			self.SyncArc(node, attr, val)
		del node.__syncarcs

	def FixChannel(self, node):
		if node.GetType() != 'ext':
			return
		mediatype = node.__mediatype
		del node.__mediatype
		try:
			channel = node.__channel
			del node.__channel
		except AttributeError:
			channel = '<unnamed>'
		if mediatype == 'audio':
			mtype = 'sound'
		elif mediatype == 'image':
			mtype = 'image'
		elif mediatype == 'video':
			mtype = 'mpeg'
		elif mediatype == 'text':
			mtype = 'html'
		elif mediatype == 'cmif_cmif':
			mtype = 'cmif'
		elif mediatype == 'cmif_shell':
			mtype = 'shell'
		else:
			mtype = mediatype
			print 'warning: unrecognized media type',mtype
		name = '%s %s' % (channel, mediatype)
		ctx = self.__context
		for key in channel, name:
			if ctx.channeldict.has_key(key):
				ch = ctx.channeldict[key]
				if ch['type'] == mtype:
					name = key
					break
		else:
			if not ctx.channeldict.has_key(channel):
				name = channel
			ch = MMNode.MMChannel(ctx, name)
			ctx.channeldict[name] = ch
			ctx.channelnames.append(name)
			ctx.channels.append(ch)
			ch['type'] = mtype
			if mediatype in ('image', 'video', 'text'):
				# deal with channel with window
				if not self.__channels.has_key(channel):
					self.__in_layout = LAYOUT_MML
					self.start_channel([('name', channel)])
					self.__in_layout = LAYOUT_NONE
				attrdict = self.__channels[channel]
				if self.__layout is None:
					# create a layout channel
					layout = MMNode.MMChannel(ctx,
								  'layout')
					ctx.channeldict['layout'] = layout
					ctx.channelnames.insert(0, 'layout')
					ctx.channels.insert(0, layout)
					self.__layout = layout
					layout['type'] = 'layout'
					if self.__width == 0:
						self.__width = 640
					if self.__height == 0:
						self.__height = 480
					layout['winpos'] = 0, 0
					layout['winsize'] = \
						self.__width, self.__height
					layout['units'] = UNIT_PXL
				ch['base_window'] = 'layout'
				x = attrdict['x']
				y = attrdict['y']
				w = attrdict['w']
				h = attrdict['h']
				if type(x) is type(0):
					x = float(x) / self.__width
				if type(y) is type(0):
					y = float(y) / self.__height
				if type(w) is type(0):
					w = float(w) / self.__width
					if w == 0:
						w = 1.0 - x
				if type(h) is type(0):
					h = float(h) / self.__height
					if h == 0:
						h = 1.0 - y
				ch['base_winoff'] = x, y, w, h
		node.attrdict['channel'] = name

	def syntax_error(self, lineno, msg):
		print 'warning: syntax error on line %d: %s' % (lineno, msg)

	# methods for start and end tags

	# mml contains everything
	def start_mml(self, attributes):
		if self.__seen_mml:
			raise error, 'more than 1 mml tag'
		self.__seen_mml = 1
		self.__in_mml = 1

	def end_mml(self):
		self.__in_mml = 0
		if not self.__root:
			raise error, 'empty document'
		self.Recurse(self.__root, self.FixChannel, self.FixSyncArcs)

	# layout section

	def start_layout(self, attributes):
		if not self.__in_mml:
			raise error, 'layout not in mml'
		self.__in_layout = LAYOUT_UNKNOWN
		for attr, val in attributes:
			val = self.translate_references(val)
			if attr == 'type' and val == 'text/mml-basic-layout':
				self.__in_layout = LAYOUT_MML
				break

	def end_layout(self):
		self.__in_layout = LAYOUT_NONE

	def start_channel(self, attributes):
		if not self.__in_layout:
			raise error, 'channel not in layout'
		if self.__in_layout != LAYOUT_MML:
			# ignore outside of mml-basic-layout
			return
		attrdict = {'x': 0,
			    'y': 0,
			    'z': 0,
			    'w': 0,
			    'h': 0}
		for attr, val in attributes:
			val = self.translate_references(val)
			if attr in ('x', 'y', 'w', 'h'):
				try:
					if val[-1] == '%':
						val = string.atof(val[:-1]) / 100.0
					else:
						val = string.atoi(val)
				except string.error:
					self.syntax_error(self.lineno, 'invalid channel attribute value')
					val = 0
			elif attr == 'z':
				try:
					val = string.atoi(val)
				except string.error:
					self.syntax_error(self.lineno, 'invalid channel attribute value')
					val = 0
			attrdict[attr] = val
		if attrdict.has_key('name'):
			self.__channels[attrdict['name']] = attrdict
		else:
			raise error, 'channel without name attribute'
		x = attrdict['x']
		y = attrdict['y']
		w = attrdict['w']
		h = attrdict['h']
		if type(x) is type(0):
			if type(w) is type(0.0):
				w = int(x*w)
			if self.__width < x+w:
				self.__width = x+w
		elif type(w) is type(0):
			if self.__width < w:
				self.__width = w
		if type(y) is type(0):
			if type(h) is type(0.0):
				h = int(y*h)
			if self.__height < y+h:
				self.__height = y+h
		elif type(h) is type(0):
			if self.__height < h:
				self.__height = h

	def end_channel(self):
		pass

	# container nodes

	def start_par(self, attributes):
		self.NewContainer('par', attributes)

	end_par = EndContainer

	def start_seq(self, attributes):
		self.NewContainer('seq', attributes)

	end_seq = EndContainer

	def start_bag(self, attributes):
		self.NewContainer('bag', attributes)

	end_bag = EndContainer

	def start_switch(self, attributes):
		self.NewContainer('alt', attributes)

	end_switch = EndContainer

	# media items

	def start_text(self, attributes):
		self.NewNode('text', attributes)

	def end_text(self):
		pass

	def start_audio(self, attributes):
		self.NewNode('audio', attributes)

	def end_audio(self):
		pass

	def start_img(self, attributes):
		self.NewNode('image', attributes)

	def end_img(self):
		pass

	def start_video(self, attributes):
		self.NewNode('video', attributes)

	def end_video(self):
		pass

	def start_cmif_cmif(self, attributes):
		self.NewNode('cmif_cmif', attributes)

	def end_cmif_cmif(self):
		pass

	def start_cmif_shell(self, attributes):
		self.NewNode('cmif_shell', attributes)

	def end_cmif_shell(self):
		pass

def ReadFile(filename):
	return ReadFileContext(filename, MMNode.MMNodeContext(MMNode.MMNode))

def ReadFileContext(filename, context):
	import os
	context.setdirname(os.path.dirname(filename))
	p = MMLParser(context)
	p.feed(open(filename).read())
	p.close()
	return p.GetRoot()

import regex
counter_val = regex.symcomp('\(\(\(<hours>[0-9][0-9]\):\)?'
			    '\(<minutes>[0-9][0-9]\):\)?'
			    '\(<seconds>[0-9][0-9]\)'
			    '\(<fraction>\.[0-9]*\)?')
id = regex.symcomp('id(\(<name>' + xmllib._Name + '\))'
		   '\((\(<value>[^)]*\))\)?'
		   '\(+\(<delay>.*\)\)?')

def _parsecounter(value, maybe_relative):
	j = counter_val.match(value)
	if j > 0 and j == len(value):
		h, m, s, f = counter_val.group('hours', 'minutes',
					       'seconds', 'fraction')
		offset = 0
		if h is not None:
			offset = offset + string.atoi(h) * 3600
		if m is not None:
			offset = offset + string.atoi(m) * 60
		offset = offset + string.atoi(s)
		if f is not None:
			offset = offset + string.atof(f + '0')
		return offset
	if maybe_relative:
		if value == 'start':
			return 'start'
		if value == 'end':
			return 'end'
	raise error, 'bogus presentation counter'

def _parsetime(xpointer):
	name = value = delay = None
	offset = 0
	i = id.match(xpointer)
	if i > 0:
		name, value, delay = id.group('name', 'value', 'delay')
	else:
		delay = xpointer
	if value is not None:
		counter = _parsecounter(value, 1)
		if counter == 'start':
			counter = 0
		elif counter == 'end':
			counter = -1		# special value
		else:
			raise error, 'bogus presentation counter'
	else:
		counter = 0
	if delay is not None:
		if delay[0] == '(' and delay[-1] == ')':
			delay = delay[1:-1]
			print 'warning: bracketed delay in time expression', xpointer
		delay = _parsecounter(delay, 0)
	else:
		delay = 0
	return name, counter, delay
