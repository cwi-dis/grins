__version__ = "$Id$"

import xmllib
import MMNode, MMAttrdefs
from windowinterface import UNIT_PXL
from HDTL import HD, TL
import string
from AnchorDefs import *
from Hlinks import DIR_1TO2, TYPE_JUMP, TYPE_CALL, TYPE_FORK
import regex

error = 'MMLTreeRead.error'

LAYOUT_NONE = 0				# must be 0
LAYOUT_MML = 1
LAYOUT_UNKNOWN = -1

coordre = regex.compile('^ *\([0-9.]+%?\)[ ,]+\([0-9.]+%?\)[ ,]+'
			'\([0-9.]+%?\)[ ,]+\([0-9.]+%?\) *$')

class MMLParser(xmllib.XMLParser):
	def __init__(self, context, verbose = 0):
		xmllib.XMLParser.__init__(self, verbose)
		self.__seen_mml = 0
		self.__in_mml = 0
		self.__in_head = 0
		self.__seen_body = 0
		self.__in_layout = LAYOUT_NONE
		self.__in_a = None
		self.__context = context
		self.__root = None
		self.__container = None
		self.__channels = {}
		self.__width = self.__height = 0
		self.__layout = None
		self.__nodemap = {}
		self.__links = []
		self.__hlink_src = self.__hlink_dst = None
		self.__in_hlink = 0

	def GetRoot(self):
		if not self.__root:
			self.error('empty document')
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
					self.error('node not in parent')
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
		for attr, val in attributes.items():
			if attr == 'id':
				node.attrdict['name'] = val
				if self.__nodemap.has_key(val):
					self.warning('node name %s not unique'%val)
				self.__nodemap[val] = node
			elif attr == 'href':
				node.attrdict['file'] = val
			elif attr == 'loc':
				# deal with channel later
				node.__channel = val
			elif attr == 'begin' or attr == 'end':
				node.__syncarcs.append(attr, val)
			elif attr == 'dur':
				node.attrdict['duration'] = _parsecounter(val, 0)

	def NewNode(self, mediatype, attributes):
		if not self.__container:
			self.error('node not in container')
		node = self.__context.newnode('ext')
		node.attrdict['transparent'] = -1
		self.AddAttrs(node, attributes)
		self.__container._addchild(node)
		node.__mediatype = mediatype
		try:
			channel = attributes['loc']
		except KeyError:
			self.syntax_error(self.lineno, 'node without loc attribute')
		else:
			if not self.__channels.has_key(channel):
				self.syntax_error(self.lineno, 'unknown loc')
		if self.__in_a:
			# deal with hyperlink
			href, ltype, id = self.__in_a
			try:
				anchorlist = node.attrdict['anchorlist']
			except KeyError:
				node.attrdict['anchorlist'] = anchorlist = []
			id = _uniqname(map(lambda a: a[A_ID], anchorlist), id)
			anchorlist.append((id, ATYPE_WHOLE, []))
			self.__links.append((node.GetUID(), id, href, ltype))

	def NewContainer(self, type, attributes):
		if not self.__in_mml:
			self.error('%s not in mml' % type)
		if self.__in_layout:
			self.error('%s in layout' % type)
		if not self.__root:
			node = self.MakeRoot(type)
		elif not self.__container:
			self.error('%s not in container' % type)
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
			mtype = 'video'
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
			# there is no channel of the right name and type
			if not ctx.channeldict.has_key(channel):
				name = channel
			ch = MMNode.MMChannel(ctx, name)
			ctx.channeldict[name] = ch
			ctx.channelnames.append(name)
			ctx.channels.append(ch)
			ch['type'] = mtype
			if mediatype == 'image':
				ch['scale'] = 1
			if mediatype in ('image', 'video', 'text'):
				# deal with channel with window
				if not self.__channels.has_key(channel):
					self.warning('no tuner %s in layout' %
						     channel)
					self.__in_layout = LAYOUT_MML
					self.start_tuner({'loc': channel})
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
				w = attrdict['width']
				h = attrdict['height']
				if type(x) is type(0):
					x = float(x) / self.__width
				if type(w) is type(0):
					if w == 0:
						# rest of window
						w = 1.0 - x
					else:
						w = float(w) / self.__width
				if type(y) is type(0):
					y = float(y) / self.__height
				if type(h) is type(0):
					if h == 0:
						# rest of window
						h = 1.0 - y
					else:
						h = float(h) / self.__height
				ch['base_winoff'] = x, y, w, h
				# anchors should not be visible
				ch['hicolor'] = ch['bucolor'] = \
						MMAttrdefs.getdef('bgcolor')[1]
		node.attrdict['channel'] = name

	def FixLinks(self):
		hlinks = self.__context.hyperlinks
		for node, aid, href, ltype in self.__links:
			# node is either a node UID (int in string
			# form) or a node id (anything else)
			try:
				string.atoi(node)
			except string.atoi_error:
				if not self.__nodemap.has_key(node):
					print 'warning: unknown node id',node
					continue
				node = self.__nodemap[node].GetUID()
			if type(aid) is type(()):
				aid, atype, args = aid
				n = self.__context.uidmap[node]
				try:
					anchorlist = n.attrdict['anchorlist']
				except KeyError:
					n.attrdict['anchorlist'] = anchorlist = []
				aid = _uniqname(map(lambda a: a[A_ID], anchorlist), aid)
				anchorlist.append((aid, atype, args))
			src = node, aid
			if href[:1] == '#':
				try:
					dst = self.__nodemap[href[1:]]
				except KeyError:
					print 'warning: unknown node id',href[1:]
					continue
				hlinks.addlink((src, _wholenodeanchor(dst),
						DIR_1TO2, ltype))
			else:
				href, tag = urllib.splittag(href)
				hlinks.addlink((src, (href, tag), DIR_1TO2, ltype))

	# methods for start and end tags

	# mml contains everything
	mml_attributes = ['lipsync', 'id']
	def start_mml(self, attributes):
		if self.__seen_mml:
			self.error('more than 1 mml tag')
		self.__seen_mml = 1
		self.__in_mml = 1

	def end_mml(self):
		self.__in_mml = 0
		if not self.__root:
			self.error('empty document')
		self.Recurse(self.__root, self.FixChannel, self.FixSyncArcs)
		self.FixLinks()

	# head/body sections

	head_attributes = ['id']
	def start_head(self, attributes):
		self.__in_head = 1

	def end_head(self):
		self.__in_head = 0

	body_attributes = ['id']
	def start_body(self, attributes):
		if not self.__in_mml:
			self.error('body not in mml')
		if self.__seen_body:
			self.error('multiple body tags')
		self.__seen_body = 1

	def end_body(self):
		pass

	# layout section

	layout_attributes = ['type']
	def start_layout(self, attributes):
		if not self.__in_mml:
			self.error('layout not in mml')
		if not self.__in_head:
			self.warning('layout not in head')
		self.__in_layout = LAYOUT_UNKNOWN
		if attributes.has_key('type') and \
		   attributes['type'] == 'text/mml-basic':
			self.__in_layout = LAYOUT_MML

	def end_layout(self):
		self.__in_layout = LAYOUT_NONE

	tuner_attributes = ['loc', 'x', 'y', 'z', 'width', 'height']
	def start_tuner(self, attributes):
		if not self.__in_layout:
			self.error('tuner not in layout')
		if self.__in_layout != LAYOUT_MML:
			# ignore outside of mml-basic-layout
			return
		attrdict = {'x': 0,
			    'y': 0,
			    'z': 0,
			    'width': 0,
			    'height': 0}
		for attr, val in attributes.items():
			if attr in ('x', 'y', 'width', 'height'):
				try:
					if val[-1] == '%':
						val = string.atof(val[:-1]) / 100.0
						if val < 0 or val > 1:
							self.error('tuner with impossible size')
					else:
						val = string.atoi(val)
						if val < 0:
							self.error('tuner with impossible size')
				except (string.atoi_error, string.atof_error):
					self.syntax_error(self.lineno, 'invalid tuner attribute value')
					val = 0
			elif attr == 'z':
				try:
					val = string.atoi(val)
				except string.atoi_error:
					self.syntax_error(self.lineno, 'invalid tuner attribute value')
					val = 1
				if val <= 0:
					self.error('tuner with negative z')
				val = val - 1 # MML def is 1, CMIF def is 0
			elif attr == 'loc':
				pass
			else:
				self.warning('unknown attribute in tuner tag')
			attrdict[attr] = val
		if attrdict.has_key('loc'):
			loc = attrdict['loc']
			if self.__channels.has_key(loc):
				self.warning('multiple tuner tags for loc=%s' % loc)
			self.__channels[attrdict['loc']] = attrdict
		else:
			self.error('tuner without loc attribute')

		# calculate minimum required size of top-level window
		x = attrdict['x']
		y = attrdict['y']
		w = attrdict['width']
		h = attrdict['height']
		width = _minsize(x, w)
		if width > self.__width:
			self.__width = width
		height = _minsize(y, h)
		if height > self.__height:
			self.__height = height

	def end_tuner(self):
		pass

	# container nodes

	par_attributes = ['id', 'endsync', 'lipsync', 'pace', 'dur', 'begin', 'end']
	def start_par(self, attributes):
		self.NewContainer('par', attributes)

	end_par = EndContainer

	seq_attributes = ['id', 'dur', 'begin', 'end']
	def start_seq(self, attributes):
		self.NewContainer('seq', attributes)

	end_seq = EndContainer

	def start_bag(self, attributes):
		self.NewContainer('bag', attributes)

	end_bag = EndContainer

	switch_attributes = ['id']
	def start_switch(self, attributes):
		if not self.__in_head:
			self.NewContainer('alt', attributes)

	def end_switch(self):
		if not self.__in_head:
			self.EndContainer(self)

	# media items

	text_attributes = ['id', 'href', 'type', 'loc', 'dur', 'begin', 'end']
	def start_text(self, attributes):
		self.NewNode('text', attributes)

	def end_text(self):
		pass

	audio_attributes = text_attributes
	def start_audio(self, attributes):
		self.NewNode('audio', attributes)

	def end_audio(self):
		pass

	img_attributes = text_attributes
	def start_img(self, attributes):
		self.NewNode('image', attributes)

	def end_img(self):
		pass

	video_attributes = text_attributes
	def start_video(self, attributes):
		self.NewNode('video', attributes)

	def end_video(self):
		pass

	cmif_cmif_attributes = text_attributes
	def start_cmif_cmif(self, attributes):
		self.NewNode('cmif_cmif', attributes)

	def end_cmif_cmif(self):
		pass

	cmif_shell_attributes = text_attributes
	def start_cmif_shell(self, attributes):
		self.NewNode('cmif_shell', attributes)

	def end_cmif_shell(self):
		pass

	# linking

	a_attributes = ['href', 'show']
	def start_a(self, attributes):
		try:
			href = attributes['href']
		except KeyError:
			self.warning('anchor without HREF')
			return
		try:
			show = attributes['show']
		except KeyError:
			show = 'replace'
		show = string.lower(show)
		if show == 'replace':
			ltype = TYPE_JUMP
		elif show == 'pause':
			ltype = TYPE_CALL
		elif show == 'new':
			ltype = TYPE_FORK
		else:
			self.warning('unknown show attribute value')
			ltype = TYPE_JUMP
		try:
			id = attributes['id']
		except KeyError:
			id = None
		self.__in_a = href, ltype, id

	def end_a(self):
		self.__in_a = None

	hlink_attributes = ['show']
	def start_hlink(self, attributes):
		if self.__in_hlink:
			self.syntax_error(self.lineno, 'recursive hlink')
			return
		try:
			show = string.lower(attributes['show'])
		except KeyError:
			show = 'replace'
		if show == 'replace':
			ltype = TYPE_JUMP
		elif show == 'pause':
			ltype = TYPE_CALL
		elif show == 'new':
			ltype = TYPE_FORK
		else:
			self.warning('unknown show attribute value')
			ltype = TYPE_JUMP
		self.__in_hlink = 1
		self.__hlink_type = ltype

	def end_hlink(self):
		sattr = self.__hlink_src
		dattr = self.__hlink_dst
		self.__in_hlink = 0
		self.__hlink_src = self.__hlink_dst = None
		if not sattr:
			self.warning('source anchor missing')
			return
		if not dattr:
			self.warning('destination anchor missing')
			return
		snode = sattr['href'][1:] # remove leading '#'
		stype = ATYPE_WHOLE
		sargs = []
		if sattr.has_key('shape') and sattr.has_key('coords'):
			stype = ATYPE_NORMAL
			if string.lower(sattr['shape']) != 'rect':
				self.warning('unknown shape attribute')
				return
			coords = sattr['coords']
			if coordre.match(coords) < 0:
				self.warning('syntax error in coords attribute')
				return
			x, y, w, h = coordre.group(1, 2, 3, 4)
			try:
				if x[-1] == '%':
					x = string.atof(x[:-1]) / 100.0
				else:
					x = string.atoi(x)
				if y[-1] == '%':
					y = string.atof(y[:-1]) / 100.0
				else:
					y = string.atoi(y)
				if w[-1] == '%':
					w = string.atof(w[:-1]) / 100.0
				else:
					w = string.atoi(w)
				if h[-1] == '%':
					h = string.atof(h[:-1]) / 100.0
				else:
					h = string.atoi(h)
			except (string.atoi_error, string.atof_error):
				self.warning('syntax error in coords attribute')
				return
			sargs = [x, y, w, h]
		if sattr.has_key('id'):
			sid = sattr['id']
		else:
			sid = None
		self.__links.append((snode, (sid, stype, sargs), dattr['href'],
				     self.__hlink_type))

	anchor_attributes = ['href', 'role', 'time', 'shape', 'coords']
	def start_anchor(self, attributes):
		if not self.__in_hlink:
			self.error('anchor not in hlink')
		try:
			role = string.lower(attributes['role'])
		except KeyError:
			self.warning('required attribute role missing')
			return
		try:
			href = attributes['href']
		except KeyError:
			self.warning('required attribute href missing')
			return
		if role == 'src':
			if self.__hlink_src:
				self.warning('multiple source anchors')
				return
			if href[:1] != '#':
				self.warning('source anchor does not point to document')
				return
			self.__hlink_src = attributes
		elif role == 'dst':
			if self.__hlink_dst:
				self.warning('multiple destination anchors')
				return
			self.__hlink_dst = attributes
		else:
			self.warning('unkown role attribute value')

	def end_anchor(self):
		pass

	# catch all

	def unknown_starttag(self, tag, attrs):
		self.warning('ignoring unknown start tag %s' % tag)

	def unknown_endtag(self, tag):
		pass

	def unknown_charref(self, ref):
		self.warning('ignoring unknown char ref %s' % ref)

	def unknown_entityref(self, ref):
		self.warning('ignoring unknown entity ref %s' % ref)

	# non-fatal syntax errors

	def syntax_error(self, lineno, msg):
		print 'warning: syntax error on line %d: %s' % (lineno, msg)

	def warning(self, message):
		print 'warning: %s on line %d' % (message, self.lineno)

	def error(self, message):
		raise error, 'error, line %d: %s' % (self.lineno, message)

def ReadFile(filename):
	return ReadFileContext(filename, MMNode.MMNodeContext(MMNode.MMNode))

def ReadFileContext(filename, context):
	import os
	context.setdirname(os.path.dirname(filename))
	p = MMLParser(context)
	p.feed(open(filename).read())
	p.close()
	return p.GetRoot()

def _minsize(start, extent):
	# Determine minimum size for top-level window given that it
	# has to contain a subwindow with the given start and extent
	# values.  Start and extent can be integers or floats.  The
	# type determines whether they are interpreted as pixel values
	# or as fractions of the top-level window.
	if type(start) is type(0):
		# start is pixel value
		if type(extent) is type(0.0):
			# extent is fraction
			if extent == 0 or (extent == 1 and start > 0):
				raise error, 'tuner with impossible size'
			if extent == 1:
				return 0
			return int(start / (1 - extent) + 0.5)
		else:
			# extent is pixel value
			if extent == 0:
				# extent == 0 means rest of window
				extent = 1 # make sure there is a rest
			return start + extent
	else:
		# start is fraction
		if start == 1:
			raise error, 'tuner with impossible size'
		if type(extent) is type(0):
			# extent is pixel value
			return int(extent / (1 - start) + 0.5)
		else:
			# extent is fraction
			return 0

def _uniqname(namelist, defname):
	if defname is not None and defname not in namelist:
		return defname
	if defname is None:
		maxid = 0
		for id in namelist:
			try:
				id = eval('0+'+id)
			except:
				pass
			if type(id) is type(0) and id > maxid:
				maxid = id
		return `maxid+1`
	id = 0
	while ('%s_%d' % (defname, id)) in namelist:
		id = id + 1
	return '%s_%d' % (defname, id)

def _wholenodeanchor(node):
	try:
		anchorlist = node.attrdict['anchorlist']
	except KeyError:
		node.attrdict['anchorlist'] = anchorlist = []
	for a in anchorlist:
		if a[A_TYPE] == ATYPE_DEST:
			break
	else:
		a = '0', ATYPE_DEST, []
		anchorlist.append(a)
	return node.GetUID(), a[A_ID]

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
