__version__ = "$Id$"

import xmllib
import MMNode, MMAttrdefs
from windowinterface import UNIT_PXL
from HDTL import HD, TL
import string
from AnchorDefs import *
from Hlinks import DIR_1TO2, TYPE_JUMP, TYPE_CALL, TYPE_FORK
import re

error = 'MMLTreeRead.error'

LAYOUT_NONE = 0				# must be 0
LAYOUT_SMIL = 1
LAYOUT_UNKNOWN = -1

coordre = re.compile('^ *(?P<x>[0-9.]+%?)[ ,]+(?P<y>[0-9.]+%?)[ ,]+'
			'(?P<w>[0-9.]+%?)[ ,]+(?P<h>[0-9.]+%?) *$')
idref = re.compile('id\((?P<id>' + xmllib._Name + ')\)')

class SMILParser(xmllib.XMLParser):
	def __init__(self, context, verbose = 0):
		xmllib.XMLParser.__init__(self, verbose)
		self.__seen_smil = 0
		self.__in_smil = 0
		self.__in_head = 0
		self.__in_head_switch = 0
		self.__seen_body = 0
		self.__in_layout = LAYOUT_NONE
		self.__seen_layout = 0
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

	def AddAttrs(self, node, attributes, ntype):
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
				if attributes.has_key('begin') and \
				   attributes.has_key('end'):
					self.warning('ignoring dur attribute')
				else:
					node.attrdict['duration'] = _parsecounter(val, 0)
			elif attr == 'repeat':
				try:
					repeat = string.atoi(val)
				except string.atoi_error:
					self.syntax_error(self.lineno,
							  'bad repeat attribute')
				else:
					if repeat < 0:
						self.warning('bad repeat value')
					else:
						node.attrdict['loop'] = repeat

	def NewNode(self, mediatype, attributes):
		if not self.__container:
			self.error('node not in container')
		if attributes.has_key('type'):
			mtype = string.split(attributes['type'], '/')[0]
			if mediatype is not None and mtype != mediatype:
				self.warning("type attribute doesn't match element")
			mediatype = mtype
		if mediatype is None:
			self.error('node of unknown type')
		node = self.__context.newnode('ext')
		node.attrdict['transparent'] = -1
		self.AddAttrs(node, attributes, mediatype)
		self.__container._addchild(node)
		node.__mediatype = mediatype
		try:
			channel = attributes['loc']
		except KeyError:
			self.warning('node without loc attribute')
			channel = '<unnamed>'
		else:
			if not self.__channels.has_key(channel):
				self.syntax_error(self.lineno, 'unknown loc')
		if not attributes.has_key('href'):
			self.syntax_error(self.lineno, 'node without href attribute')
		elif mediatype == 'image':
			import img, urllib
			file = attributes['href']
			try:
				file = urllib.urlretrieve(file)[0]
				rdr = img.reader(None, file)
				width = rdr.width
				height = rdr.height
				del rdr
			except:
				pass
			else:
				if self.__channels.has_key(channel):
					ch = self.__channels[channel]
				else:
					self.__channels[channel] = ch = \
						{'minwidth': 0, 'minheight': 0,
						 'left': 0, 'top': 0,
						 'width': 0, 'height': 0}
				node.__size = width, height
				if ch['minwidth'] < width:
					ch['minwidth'] = width
				if ch['minheight'] < height:
					ch['minheight'] = height
		elif mediatype == 'video':
			import urllib
			file = attributes['href']
			try:
				import mv
				file = urllib.urlretrieve(file)[0]
				movie = mv.OpenFile(file,
						    mv.MV_MPEG1_PRESCAN_OFF)
				track = movie.FindTrackByMedium(mv.DM_IMAGE)
				width = track.GetImageWidth()
				height = track.GetImageHeight()
				del movie, track
			except:
				pass
			else:
				node.__size = width, height
				if self.__channels.has_key(channel):
					ch = self.__channels[channel]
				else:
					self.__channels[channel] = ch = \
						{'minwidth': 0, 'minheight': 0,
						 'left': 0, 'top': 0,
						 'width': 0, 'height': 0}
				if ch['minwidth'] < width:
					ch['minwidth'] = width
				if ch['minheight'] < height:
					ch['minheight'] = height
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
		if not self.__in_smil:
			self.warning('%s not in smil' % type)
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
		self.AddAttrs(node, attributes, type)

	def EndContainer(self):
		self.__container = self.__container.GetParent()

	def Recurse(self, root, *funcs):
		for func in funcs:
			func(root)
		for node in root.GetChildren():
			apply(self.Recurse, (node,) + funcs)

	def FixSizes(self):
		# calculate minimum required size of top-level window
		for attrdict in self.__channels.values():
			try:
				width = _minsize(attrdict['left'],
						 attrdict['width'],
						 attrdict['minwidth'])
			except error, msg:
				self.syntax_error(self.lineno, msg)
			else:
				if width > self.__width:
					self.__width = width

			try:
				height = _minsize(attrdict['top'],
						  attrdict['height'],
						  attrdict['minheight'])
			except error, msg:
				self.syntax_error(self.lineno, msg)
			else:
				if height > self.__height:
					self.__height = height
		
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
			if mediatype in ('image', 'video'):
				ch['scale'] = 1
			if mediatype in ('image', 'video', 'text'):
				# deal with channel with window
				if not self.__channels.has_key(channel):
					self.warning('no tuner %s in layout' %
						     channel)
					self.__in_layout = LAYOUT_SMIL
					self.start_tuner({'id': channel})
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
				x = attrdict['left']
				y = attrdict['top']
				w = attrdict['width']
				h = attrdict['height']
				if type(x) is type(0):
					x = float(x) / self.__width
				if type(w) is type(0):
					if w == 0:
						try:
							width = node.__size[0]
						except AttributeError:
							# rest of window
							w = 1.0 - x
						else:
							w = float(width) / self.__width
					else:
						w = float(w) / self.__width
				if type(y) is type(0):
					y = float(y) / self.__height
				if type(h) is type(0):
					if h == 0:
						try:
							height = node.__size[1]
						except AttributeError:
							# rest of window
							h = 1.0 - y
						else:
							h = float(height) / self.__height
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
				import urllib
				href, tag = urllib.splittag(href)
				if '/' not in href:
					href = href + '/1'
				hlinks.addlink((src, (href, tag or ''), DIR_1TO2, ltype))

	# methods for start and end tags

	# smil contains everything
	smil_attributes = ['id', 'lipsync']
	def start_smil(self, attributes):
		if self.__seen_smil:
			self.error('more than 1 smil tag')
		self.__seen_smil = 1
		self.__in_smil = 1

	def end_smil(self):
		self.__in_smil = 0
		if not self.__root:
			self.error('empty document')
		self.FixSizes()
		self.Recurse(self.__root, self.FixChannel, self.FixSyncArcs)
		self.FixLinks()

	# head/body sections

	head_attributes = ['id']
	def start_head(self, attributes):
		if not self.__in_smil:
			self.warning('head not in smil')
		self.__in_head = 1

	def end_head(self):
		self.__in_head = 0

	body_attributes = ['id']
	def start_body(self, attributes):
		if not self.__in_smil:
			self.warning('body not in smil')
		if self.__seen_body:
			self.error('multiple body tags')
		self.__seen_body = 1
		self.__in_body = 1

	def end_body(self):
		self.__in_body = 0

	# layout section

	layout_attributes = ['id', 'type']
	def start_layout(self, attributes):
		if not self.__in_head:
			self.warning('layout not in head')
		if self.__seen_layout and not self.__in_head_switch:
			self.warning('multiple layouts without switch')
		self.__seen_layout = 1
		self.__in_layout = LAYOUT_UNKNOWN
		if attributes.has_key('type') and \
		   attributes['type'] == 'text/smil-basic':
			self.__in_layout = LAYOUT_SMIL

	def end_layout(self):
		self.__in_layout = LAYOUT_NONE

	tuner_attributes = ['id', 'left', 'top', 'z', 'width', 'height']
	def start_tuner(self, attributes):
		if not self.__in_layout:
			self.error('tuner not in layout')
		if self.__in_layout != LAYOUT_SMIL:
			# ignore outside of smil-basic-layout
			return
		attrdict = {'left': 0,
			    'top': 0,
			    'z': 0,
			    'width': 0,
			    'height': 0,
			    'minwidth': 0,
			    'minheight': 0,}
		seen_id = 0
		for attr, val in attributes.items():
			if attr in ('left', 'top', 'width', 'height'):
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
				val = val - 1 # SMIL def is 1, CMIF def is 0
			elif attr == 'id':
				seen_id = 1
				if self.__channels.has_key(val):
					self.warning('multiple tuner tags for id=%s' % val)
				self.__channels[val] = attrdict
			else:
				self.warning('unknown attribute in tuner tag')
			attrdict[attr] = val
		if not seen_id:
			self.error('tuner without id attribute')

	def end_tuner(self):
		pass

	# container nodes

	par_attributes = ['id', 'endsync', 'lipsync',
			  'dur', 'begin', 'end', 'repeat']
	def start_par(self, attributes):
		# XXXX we ignore lipsync for now
		self.NewContainer('par', attributes)
		if attributes.has_key('endsync'):
			self.__container.__endsync = attributes['endsync']

	def end_par(self):
		node = self.__container
		self.EndContainer()
		try:
			endsync = node.__endsync
		except AttributeError:
			return
		del node.__endsync
		if endsync == 'first':
			node.attrdict['terminator'] = 'FIRST'
		elif endsync == 'last':
			node.attrdict['terminator'] = 'LAST'
		else:
			res = idref.match(endsync)
			if res is None:
				self.warning('bad endsync attribute')
				return
			id = res.group('id')
			for c in node.GetChildren():
				if c.attrdict.has_key('name') and \
				   c.attrdict['name'] == id:
					node.attrdict['terminator'] = id
					return
			else:
				# id not found among the children
				self.warning('unknown idref in endsync attribute')

	seq_attributes = ['id', 'dur', 'begin', 'end', 'repeat']
	def start_seq(self, attributes):
		self.NewContainer('seq', attributes)

	end_seq = EndContainer

	def start_bag(self, attributes):
		self.NewContainer('bag', attributes)

	end_bag = EndContainer

	switch_attributes = ['id']
	def start_switch(self, attributes):
		if self.__in_head:
			if self.__in_head_switch:
				self.error('switch within switch in head')
			self.__in_head_switch = 1
		else:
			self.NewContainer('alt', attributes)

	def end_switch(self):
		self.__in_head_switch = 0
		if not self.__in_head:
			self.EndContainer(self)

	# media items

	ref_attributes = ['id', 'href', 'type', 'loc', 'dur', 'begin', 'end', 'repeat']
	def start_ref(self, attributes):
		self.NewNode(None, attributes)

	def end_ref(self):
		pass

	text_attributes = ref_attributes
	def start_text(self, attributes):
		self.NewNode('text', attributes)

	def end_text(self):
		pass

	audio_attributes = ref_attributes
	def start_audio(self, attributes):
		self.NewNode('audio', attributes)

	def end_audio(self):
		pass

	img_attributes = ref_attributes
	def start_img(self, attributes):
		self.NewNode('image', attributes)

	def end_img(self):
		pass

	video_attributes = ref_attributes
	def start_video(self, attributes):
		self.NewNode('video', attributes)

	def end_video(self):
		pass

	cmif_cmif_attributes = ref_attributes
	def start_cmif_cmif(self, attributes):
		self.NewNode('cmif_cmif', attributes)

	def end_cmif_cmif(self):
		pass

	cmif_shell_attributes = ref_attributes
	def start_cmif_shell(self, attributes):
		self.NewNode('cmif_shell', attributes)

	def end_cmif_shell(self):
		pass

	# linking

	a_attributes = ['id', 'href', 'show']
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

	hlink_attributes = ['id', 'show']
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
		if sattr.has_key('coords'):
			if sattr.has_key('shape') and sattr['shape'] != 'rect':
				self.warning('unrecognized shape attribute')
				return
			stype = ATYPE_NORMAL
			coords = sattr['coords']
			res = coordre.match(coords)
			if not res:
				self.warning('syntax error in coords attribute')
				return
			x, y, w, h = res.group('x', 'y', 'w', 'h')
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

	anchor_attributes = ['id', 'href', 'role']
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
	p = SMILParser(context)
	p.feed(open(filename).read())
	p.close()
	return p.GetRoot()

def _minsize(start, extent, minsize):
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
				return minsize
			size = int(start / (1 - extent) + 0.5)
			if minsize > 0 and extent > 0:
				size = max(size, int(minsize/extent + 0.5))
			return size
		else:
			# extent is pixel value
			if extent == 0:
				extent = minsize
			return start + extent
	else:
		# start is fraction
		if start == 1:
			raise error, 'tuner with impossible size'
		if type(extent) is type(0):
			# extent is pixel value
			if extent == 0:
				extent = minsize
			return int(extent / (1 - start) + 0.5)
		else:
			# extent is fraction
			if minsize > 0 and extent > 0:
				return int(minsize / extent + 0.5)
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

counter_val = re.compile('((?P<use_clock>'
				'((?P<hours>[0-9][0-9]):)?'
				'(?P<minutes>[0-9][0-9]):'
				'(?P<seconds>[0-9][0-9])'
				'(?P<fraction>\.[0-9]+)?'
			 ')|(?P<use_timecount>'
				'(?P<timecount>[0-9]+)'
				'(?P<units>\.[0-9]+)?'
				'(?P<scale>h|min|s|ms)?)'
			 ')$')

def _parsecounter(value, maybe_relative):
	res = counter_val.match(value)
	if res:
		if res.group('use_clock'):
			h, m, s, f = res.group('hours', 'minutes',
					       'seconds', 'fraction')
			offset = 0
			if h is not None:
				offset = offset + string.atoi(h) * 3600
			if m is not None:
				offset = offset + string.atoi(m) * 60
			offset = offset + string.atoi(s)
			if f is not None:
				offset = offset + string.atof(f + '0')
		elif res.group('use_timecount'):
			tc, f, sc = res.group('timecount', 'units', 'scale')
			offset = string.atoi(tc)
			if f is not None:
				offset = offset + string.atof(f)
			if sc == 'h':
				offset = offset * 3600
			elif sc == 'min':
				offset = offset * 60
			elif sc == 'ms':
				offset = float(offset) / 1000
			# else already in seconds
		else:
			raise error, 'internal error'
		return offset
	if maybe_relative:
		if value in ('begin', 'end', 'ready'):
			return value
	raise error, 'bogus presentation counter'

id = re.compile('id\((?P<name>' + xmllib._Name + ')\)'
		'(\((?P<value>[^)]*)\))?'
		'(\+(?P<delay>.*))?$')

def _parsetime(xpointer):
	offset = 0
	res = id.match(xpointer)
	if res:
		name, value, delay = res.group('name', 'value', 'delay')
	else:
		name, value, delay = None, None, xpointer
	if value is not None:
		counter = _parsecounter(value, 1)
		if counter == 'begin':
			counter = 0
		elif counter == 'end':
			counter = -1	# special value
		elif counter == 'ready':
			counter = 0	# treat "ready" as "begin" for now
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
