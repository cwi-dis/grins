__version__ = "$Id$"

import xmllib
import mimetypes
import MMNode, MMAttrdefs
from MMExc import *
import MMurl
from windowinterface import UNIT_PXL
from HDTL import HD, TL
import string
from AnchorDefs import *
from Hlinks import DIR_1TO2, TYPE_JUMP, TYPE_CALL, TYPE_FORK
import re
import os

error = 'SMILTreeRead.error'

SMILdtd = "http://dejavu.cs.vu.nl/~symm/validator/SMIL10.dtd"

LAYOUT_NONE = 0				# must be 0
LAYOUT_SMIL = 1
LAYOUT_UNKNOWN = -1

layout_name = 'SMIL'			# name of layout channel
SMIL_BASIC = 'text/smil-basic'

coordre = re.compile(r'^(?P<x>\d+%?),(?P<y>\d+%?),'
		     r'(?P<w>\d+%?),(?P<h>\d+%?)$')
idref = re.compile(r'id\((?P<id>' + xmllib._Name + r')\)')
clock_val = re.compile(r'(?:(?P<use_clock>' # hours:mins:secs[.fraction]
		       r'(?:(?P<hours>\d{2}):)?'
		       r'(?P<minutes>\d{2}):'
		       r'(?P<seconds>\d{2})'
		       r'(?P<fraction>\.\d+)?'
		       r')|(?P<use_timecount>' # timecount[.fraction]unit
		       r'(?P<timecount>\d+)'
		       r'(?P<units>\.\d+)?'
		       r'(?P<scale>h|min|s|ms)?)'
		       r')$')
id = re.compile(r'id\((?P<name>' + xmllib._Name + r')\)' # id(name)
		r'\((?P<event>[^)]+)\)'			# (event)
		r'(?:\+(?P<delay>.*))?$')		# +delay (optional)
clock = re.compile(r'(?P<name>local|remote):'
		   r'(?P<hours>\d+):'
		   r'(?P<minutes>\d{2}):'
		   r'(?P<seconds>\d{2})'
		   r'(?P<fraction>\.\d+)?'
		   r'(?:Z(?P<sign>[-+])(?P<ohours>\d{2}):(?P<omin>\d{2}))?$')
screen_size = re.compile(r'\d+X\d+$')
range = re.compile('^(?:'
		   '(?:(?P<npt>npt)=(?P<nptstart>[^-]*)-(?P<nptend>[^-]*))|'
		   '(?:(?P<smpte>smpte(?:-30-drop|-25)?)=(?P<smptestart>[^-]*)-(?P<smpteend>[^-]*))'
		   ')$')
smpte_time = re.compile(r'(?:(?:\d{2}:)?\d{2}:)?\d{2}(?P<f>\.\d{2})?$')

class SMILParser(xmllib.XMLParser):
	def __init__(self, context, verbose = 0):
		xmllib.XMLParser.__init__(self, verbose)
		self.__seen_smil = 0
		self.__in_smil = 0
		self.__in_head = 0
		self.__in_head_switch = 0
		self.__in_meta = 0
		self.__seen_body = 0
		self.__in_layout = LAYOUT_NONE
		self.__seen_layout = 0
		self.__in_a = None
		self.__context = context
		self.__root = None
		self.__container = None
		self.__node = None	# the media object we're in
		self.__channels = {}
		self.__width = self.__height = 0
		self.__layout = None
		self.__nodemap = {}
		self.__anchormap = {}
		self.__links = []
		self.par_attributes['sync'] = None # reset in case it changed
		self.__title = layout_name

	def GetRoot(self):
		if not self.__root:
			self.error('empty document')
		return self.__root

	def MakeRoot(self, type):
		self.__root = self.__context.newnodeuid(type, '1')
		return self.__root

	def SyncArc(self, node, attr, val):
		synctolist = node.attrdict.get('synctolist', [])
		if not synctolist:
			node.attrdict['synctolist'] = synctolist
		if attr == 'begin':
			yside = HD
		else:
			yside = TL
		try:
			name, counter, delay = self.__parsetime(val)
		except error, msg:
			self.syntax_error(msg)
			return
		if name is None:
			# relative to parent/previous/start
			parent = node.GetParent()
			if parent is None:
				self.syntax_error('sync arc to top-level node')
				return
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
				nm = n.attrdict.get('name')
				if nm is not None and nm == name:
					xnode = n
					break
			else:
				print 'warning: out of scope sync arc'
				if self.__nodemap.has_key(name):
					xnode = self.__nodemap[name]
				else:
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
					self.syntax_error('node name %s not unique'%val)
				self.__nodemap[val] = node
			elif attr == 'src':
				node.attrdict['file'] = val
			elif attr == 'begin' or attr == 'end':
				node.__syncarcs.append(attr, val)
			elif attr == 'dur':
				if attributes.has_key('begin') and \
				   attributes.has_key('end'):
					self.warning('ignoring dur attribute')
				else:
					try:
						node.attrdict['duration'] = self.__parsecounter(val, 0)
					except error, msg:
						self.syntax_error(msg)
			elif attr == 'repeat':
				try:
					repeat = string.atoi(val)
				except string.atoi_error:
					self.syntax_error('bad repeat attribute')
				else:
					if repeat < 0:
						self.warning('bad repeat value')
					else:
						node.attrdict['loop'] = repeat
			elif attr == 'bitrate':
				try:
					bitrate = string.atoi(val)
				except string.atoi_error:
					self.syntax_error('bad bitrate attribute')
				# XXXX bitrate is ignored
			elif attr == 'screen-size':
				if screen_size.match(val) is None:
					self.syntax_error('bad screen-size attribute')
				# XXXX screen-size is ignored
			elif attr == 'screen-depth':
				try:
					depth = string.atoi(val)
				except string.atoi_error:
					self.syntax_error('bad screen-depth attribute')
				# XXXX screen-depth is ignored

	def NewNode(self, mediatype, attributes):
		if not self.__in_smil:
			self.syntax_error('node not in smil')
			return
		if self.__in_layout:
			self.syntax_error('node in layout')
			return
		if self.__node:
			# the warning comes later from xmllib
			self.EndNode()
		if not attributes.has_key('src'):
			self.syntax_error('node without src attribute')
			return
		url = attributes['src']
		url = self.__context.findurl(url)

		# find out type of file
		subtype = None
		mtype = attributes.get('type')
		if mtype is None:
			# guess the type from the file extension
			mtype = mimetypes.guess_type(url)[0]
		if mtype is None and mediatype is None:
			# last resort: get file and see what type it is
			try:
				u = MMurl.urlopen(url)
			except:
				self.warning('cannot open file %s' % url)
				# we have no idea what type the file is
				mtype = 'text/plain'
			else:
				mtype = u.headers.type
				u.close()
		if mtype is not None:
			mtype = string.split(mtype, '/')
			if mediatype is not None and mtype[0] != mediatype:
				self.warning("file type doesn't match element")
			mediatype = mtype[0]
			subtype = mtype[1]

		# create the node
		if not self.__root:
			node = self.MakeRoot('ext')
		elif not self.__container:
			self.syntax_error('node not in container')
			return
		else:
			node = self.__context.newnode('ext')
			self.__container._addchild(node)
		self.__node = node
		self.AddAttrs(node, attributes, mediatype)
		node.__mediatype = mediatype, subtype

		# connect to channel
		if attributes.has_key('channel'):
			channel = attributes['channel']
		else:
			self.warning('node without channel attribute')
			channel = '<unnamed %d>'
			i = 0
			while self.__channels.has_key(channel % i):
				i = i + 1
			channel = channel % i
		else:
			if not self.__channels.has_key(channel):
				self.syntax_error('unknown channel')
		node.__channel = channel
		if mediatype in ('image', 'video'):
			ch = self.__channels.get(channel)
			if ch is None:
				self.__channels[channel] = ch = \
					{'minwidth': 0, 'minheight': 0,
					 'left': 0, 'top': 0,
					 'width': 0, 'height': 0,
					 'z-index': 0, 'scale': 'meet'}
			x, y, w, h = ch['left'], ch['top'], ch['width'], ch['height']
			# if we don't know the channel size and
			# position in pixels, we need to look at the
			# media objects to figure out the size to use.
			if w > 0 and h > 0 and \
			   type(w) == type(h) == type(0) and \
			   (x == y == 0 or type(x) == type(y) == type(0)) and \
			   ch['scale'] != 'visible':
				# size and position is given in pixels
				pass
			else:
				try:
					if mediatype == 'image':
						import img
						file = MMurl.urlretrieve(url)[0]
						rdr = img.reader(None, file)
						width = rdr.width
						height = rdr.height
						del rdr
					else:
						import mv
						# can't use urlopen + OpenFD:
						# mv.error: Illegal seek.
						file = MMurl.urlretrieve(url)[0]
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
					if ch['minwidth'] < width:
						ch['minwidth'] = width
					if ch['minheight'] < height:
						ch['minheight'] = height
					if ch['scale'] == 'visible':
						w = ch['width']
						if type(w) is type(0) and w < width:
							ch['width'] = width
						h = ch['height']
						if type(h) is type(0) and h < height:
							ch['height'] = height
		elif not self.__channels.has_key(channel):
			self.__channels[channel] = {'left':0, 'top':0,
						    'z-index':0, 'width':0,
						    'height':0,
						    'scale':'meet'}

		# range attribute for video
		range = attributes.get('range')
		if mediatype == 'video' and range is not None:
			try:
				start, end = self.__parserange(range)
			except error, msg:
				self.syntax_error(msg)
			else:
				import mv
				try:
					file = MMurl.urlretrieve(url)[0]
					movie = mv.OpenFile(file, mv.MV_MPEG1_PRESCAN_OFF)
					track = movie.FindTrackByMedium(mv.DM_IMAGE)
					rate = track.GetImageRate()
					del movie, track
				except:
					pass
				else:
					import smpte
					if rate == 30:
						cl = smpte.Smpte30
					elif rate == 25:
						cl = smpte.Smpte25
					elif rate == 24:
						cl = smpte.Smpte24
					else:
						cl = smpte.Smpte30Drop
					if start:
						start = cl(start).GetFrame()
					else:
						start = 0
					if end:
						end = cl(end).GetFrame()
					else:
						end = 0
					node.attrdict['range'] = start, end
		if self.__in_a:
			# deal with hyperlink
			href, ltype, id = self.__in_a[:3]
			try:
				anchorlist = node.__anchorlist
			except AttributeError:
				node.__anchorlist = anchorlist = []
			id = _uniqname(map(lambda a: a[2], anchorlist), id)
			anchorlist.append((0, len(anchorlist), id, ATYPE_WHOLE, []))
			self.__links.append((node.GetUID(), id, href, ltype))

	def EndNode(self):
		node = self.__node
		try:
			anchorlist = node.__anchorlist
		except AttributeError:
			pass
		else:
			alist = []
			anchorlist.sort()
			for a in anchorlist:
				alist.append(a[2:])
			node.attrdict['anchorlist'] = alist
		self.__node = None

	def NewContainer(self, type, attributes):
		if not self.__in_smil:
			self.syntax_error('%s not in smil' % type)
		if self.__in_layout:
			self.syntax_error('%s in layout' % type)
			return
		if not self.__root:
			node = self.MakeRoot(type)
		elif not self.__container:
			self.error('multiple elements in body')
			return
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
			except KeyError:
				continue
			except error, msg:
				self.syntax_error(msg)
			else:
				if width > self.__width:
					self.__width = width

			try:
				height = _minsize(attrdict['top'],
						  attrdict['height'],
						  attrdict['minheight'])
			except KeyError:
				continue
			except error, msg:
				self.syntax_error(msg)
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
		mediatype, subtype = node.__mediatype
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
			if subtype == 'plain':
				mtype = 'text'
			else:
				mtype = 'html'
		elif mediatype == 'cmif_cmif':
			mtype = 'cmif'
		elif mediatype == 'cmif_socket':
			mtype = 'socket'
		elif mediatype == 'cmif_shell':
			mtype = 'shell'
		else:
			mtype = mediatype
			print 'warning: unrecognized media type',mtype
		name = '%s %s' % (channel, mediatype)
		ctx = self.__context
		for key in channel, name:
			ch = ctx.channeldict.get(key)
			if ch is not None and ch['type'] == mtype:
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
			if mediatype in ('image', 'video', 'text'):
				# deal with channel with window
				if not self.__channels.has_key(channel):
					self.warning('no channel %s in layout' %
						     channel)
					self.__in_layout = LAYOUT_SMIL
					self.start_channel({'id': channel})
					self.__in_layout = LAYOUT_NONE
				attrdict = self.__channels[channel]
				if self.__layout is None:
					# create a layout channel
					layout = MMNode.MMChannel(ctx,
								  self.__title)
					ctx.channeldict[self.__title] = layout
					ctx.channelnames.insert(0, self.__title)
					ctx.channels.insert(0, layout)
					self.__layout = layout
					layout['type'] = 'layout'
					if self.__width == 0:
						self.__width = 640
					if self.__height == 0:
						self.__height = 480
					layout['winsize'] = \
						self.__width, self.__height
					layout['units'] = UNIT_PXL
				ch['base_window'] = self.__title
				if mediatype == 'text':
					ch['transparent'] = -1
				else:
					ch['transparent'] = 1
				ch['z'] = attrdict['z-index']
				x = attrdict['left']
				y = attrdict['top']
				w = attrdict['width']
				h = attrdict['height']
				scale = attrdict['scale']
				if scale == 'meet':
					ch['scale'] = 0
				elif scale == 'hidden':
					ch['scale'] = 1
				elif scale == 'slice':
					ch['scale'] = -1
				elif scale == 'visible':
					ch['scale'] = 1
				ch['center'] = 0
				# other scale options not implemented
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
## doesn't do any good for HTML channels
## 				# anchors should not be visible
## 				ch['hicolor'] = ch['bucolor'] = \
## 						MMAttrdefs.getdef('bgcolor')[1]
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
			src = node, aid
			if href[:1] == '#':
				if self.__anchormap.has_key(href[1:):
					dst = self.__anchormap[href[1:]]
				else:
					if self.__nodemap.has_key(href[1:]):
						dst = self.__nodemap[href[1:]]
					else:
						print 'warning: unknown node id',href[1:]
						continue
					else:
						dst = self.__wholenodeanchor(dst)
				hlinks.addlink((src, dst, DIR_1TO2, ltype))
			else:
				href, tag = MMurl.splittag(href)
				if '/' not in href:
					href = href + '/1'
				hlinks.addlink((src, (href, tag or ''), DIR_1TO2, ltype))

	# methods for start and end tags

	# smil contains everything
	smil_attributes = {'id':None}
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

	head_attributes = {'id':None}
	def start_head(self, attributes):
		if not self.__in_smil:
			self.syntax_error('head not in smil')
		self.__in_head = 1

	def end_head(self):
		self.__in_head = 0

	body_attributes = {'id':None}
	def start_body(self, attributes):
		if not self.__in_smil:
			self.syntax_error('body not in smil')
		if self.__seen_body:
			self.error('multiple body tags')
		self.__seen_body = 1
		self.__in_body = 1

	def end_body(self):
		self.__in_body = 0

	meta_attributes = {'name':None, 'content':None}
	def start_meta(self, attributes):
		if not self.__in_head:
			self.syntax_error('meta not in head')
			return
		if self.__in_head_switch or self.__in_layout:
			self.syntax_error('meta in layout')
			return
		if self.__in_meta:
			self.syntax_error('nested meta elements')
			return
		self.__in_meta = 1
		if attributes.has_key('name'):
			name = attributes['name']
		else:
			self.syntax_error('required attribute name missing in meta element')
			return
		if attributes.has_key('content'):
			content = attributes['content']
		else:
			self.syntax_error('required attribute content missing in meta element')
			return
		if name == 'sync':
			if content not in ('hard', 'soft'):
				self.syntax_error('illegal value for sync attribute')
				return
			self.par_attributes['sync'] = content
		if name == 'title':
			self.__title = content
		# we currently ignore all other meta element

	def end_meta(self):
		self.__in_meta = 0

	# layout section

	layout_attributes = {'id':None, 'type':SMIL_BASIC}
	def start_layout(self, attributes):
		if not self.__in_head:
			self.syntax_error('layout not in head')
		if self.__in_meta:
			self.syntax_error('layout in meta')
		if self.__seen_layout and not self.__in_head_switch:
			self.syntax_error('multiple layouts without switch')
		self.__seen_layout = 1
		if attributes['type'] == SMIL_BASIC:
			self.__in_layout = LAYOUT_SMIL
		else:
			self.__in_layout = LAYOUT_UNKNOWN

	def end_layout(self):
		self.__in_layout = LAYOUT_NONE

	channel_attributes = {'id':None, 'left':'0', 'top':'0', 'z-index':'0',
			      'width':'0', 'height':'0', 'scale':'meet'}
	def start_channel(self, attributes):
		if not self.__in_layout:
			self.syntax_error('channel not in layout')
			return
		if self.__in_layout != LAYOUT_SMIL:
			# ignore outside of smil-basic-layout
			return
		attrdict = {'left': 0,
			    'top': 0,
			    'z-index': 0,
			    'width': 0,
			    'height': 0,
			    'minwidth': 0,
			    'minheight': 0,}

		for attr in ('left', 'top', 'width', 'height'):
			val = attributes[attr]
			try:
				if val[-1] == '%':
					val = string.atof(val[:-1]) / 100.0
					if val < 0 or val > 1:
						self.syntax_error('channel with impossible size')
						if val < 0: val = 0.0
						else: val = 1.0
				else:
					val = string.atoi(val)
					if val < 0:
						self.syntax_error('channel with impossible size')
						val = 0
			except (string.atoi_error, string.atof_error):
				self.syntax_error('invalid channel attribute value')
				val = 0
			attrdict[attr] = val

		val = attributes['z-index']
		try:
			val = string.atoi(val)
		except string.atoi_error:
			self.syntax_error('invalid z-index value')
			val = 0
		if val < 0:
			self.syntax_error('channel with negative z-index')
			val = 0
		attrdict['z-index'] = val

		val = attributes['scale']
		if val not in ['meet', 'slice', 'fill', 'visible', 'hidden',
			       'auto', 'scroll']:
			self.syntax_error('illegal scale attribute')
		attrdict['scale'] = val

		val = attributes.get('id')
		if val is None:
			self.syntax_error('channel without id attribute')
			return
		attrdict['id'] = val
		if self.__channels.has_key(val):
			self.syntax_error('multiple channel tags for id=%s' % val)
		self.__channels[val] = attrdict

	def end_channel(self):
		pass

	# container nodes

	par_attributes = {'id':None, 'endsync':None, 'sync':None,
			  'dur':None, 'repeat':'1', 'fill':'remove',
			  'channel':None, 'begin':None, 'end':None,
			  'bitrate':None, 'language':None, 'screen-size':None,
			  'screen-depth':None}
	def start_par(self, attributes):
		# XXXX we ignore sync for now
		self.NewContainer('par', attributes)
		if not self.__container:
			return
		self.__container.__endsync = attributes.get('endsync')
		if self.__container.__endsync is not None and \
		   self.__container.attrdict.has_key('duration'):
			self.warning('ignoring dur attribute')
			del self.__container.attrdict['duration']

	def end_par(self):
		node = self.__container
		self.EndContainer()
		endsync = node.__endsync
		del node.__endsync
		if endsync is None:
			pass
		elif endsync == 'first':
			node.attrdict['terminator'] = 'FIRST'
		elif endsync == 'last':
			node.attrdict['terminator'] = 'LAST'
		else:
			res = idref.match(endsync)
			if res is None:
				self.syntax_error('bad endsync attribute')
				return
			id = res.group('id')
			for c in node.GetChildren():
				nm = c.attrdict.get('name')
				if nm is not None and nm == id:
					node.attrdict['terminator'] = id
					return
			else:
				# id not found among the children
				self.warning('unknown idref in endsync attribute')

	seq_attributes = {'id':None, 'dur':None, 'begin':None, 'end':None,
			  'repeat':'1', 'fill':'remove',
			  'bitrate':None, 'language':None,
			  'screen-size':None, 'screen-depth':None}
	def start_seq(self, attributes):
		self.NewContainer('seq', attributes)

	end_seq = EndContainer

	def start_bag(self, attributes):
		self.NewContainer('bag', attributes)

	end_bag = EndContainer

	switch_attributes = {'id':None, 'bitrate':None, 'language':None,
			     'screen-size':None, 'screen-depth':None}
	def start_switch(self, attributes):
		if self.__in_head:
			if self.__in_head_switch:
				self.syntax_error('switch within switch in head')
			if self.__in_meta:
				self.syntax_error('switch in meta')
			self.__in_head_switch = 1
		else:
			self.NewContainer('alt', attributes)

	def end_switch(self):
		self.__in_head_switch = 0
		if not self.__in_head:
			self.EndContainer()

	# media items

	basic_attributes = {'id':None, 'src':None, 'type':None, 'channel':None,
			    'dur':None, 'begin':None, 'end':None, 'repeat':'1',
			    'fill':'remove', 'bitrate':None, 'language':None,
			    'screen-size':None, 'screen-depth':None}
	ref_attributes = basic_attributes.copy()
	ref_attributes['range'] = None
	def start_ref(self, attributes):
		self.NewNode(None, attributes)

	def end_ref(self):
		self.EndNode()

	text_attributes = basic_attributes
	def start_text(self, attributes):
		self.NewNode('text', attributes)

	def end_text(self):
		self.EndNode()

	audio_attributes = ref_attributes
	def start_audio(self, attributes):
		self.NewNode('audio', attributes)

	def end_audio(self):
		self.EndNode()

	img_attributes = basic_attributes
	def start_img(self, attributes):
		self.NewNode('image', attributes)

	def end_img(self):
		self.EndNode()

	video_attributes = ref_attributes
	def start_video(self, attributes):
		self.NewNode('video', attributes)

	def end_video(self):
		self.EndNode()

	cmif_cmif_attributes = basic_attributes
	def start_cmif_cmif(self, attributes):
		self.NewNode('cmif_cmif', attributes)

	def end_cmif_cmif(self):
		self.EndNode()

	cmif_socket_attributes = basic_attributes
	def start_cmif_socket(self, attributes):
		self.NewNode('cmif_socket', attributes)

	def end_cmif_socket(self):
		self.EndNode()

	cmif_shell_attributes = basic_attributes
	def start_cmif_shell(self, attributes):
		self.NewNode('cmif_shell', attributes)

	def end_cmif_shell(self):
		self.EndNode()

	# linking

	a_attributes = {'id':None, 'href':None, 'show':'replace',
			'xml-link':'simple', 'inline':'true'}
	def start_a(self, attributes):
		if self.__in_a:
			self.syntax_error('nested a elements')
		if attributes.has_key('href'):
			href = attributes['href']
		else:
			self.syntax_error('anchor without HREF')
			return
		show = attributes['show']
		if show == 'replace':
			ltype = TYPE_JUMP
		elif show == 'pause':
			ltype = TYPE_CALL
		elif show == 'new':
			ltype = TYPE_FORK
		else:
			self.syntax_error('unknown show attribute value')
			ltype = TYPE_JUMP
		id = attributes.get('id')
		self.__in_a = href, ltype, id, self.__in_a

	def end_a(self):
		self.__in_a = self.__in_a[3]

	anchor_attributes = {'id':None, 'href':None, 'show':'replace',
			     'xml-link':'simple', 'inline':'true',
			     'coords':None, 'z-index':'0', 'begin':None,
			     'end':None, 'iid':None}
	def start_anchor(self, attributes):
		if self.__node is None:
			self.syntax_error('anchor not in media object')
			return
		if attributes.has_key('href'):
			href = attributes['href']
		else:
			#XXXX is this a document error?
## 			self.warning('required attribute href missing')
			href = None	# destination-only anchor
		uid = self.__node.GetUID()
		nname = self.__node.GetRawAttrDef('name', None)
		aname = attributes.get('id')
		show = attributes['show']
		if show == 'replace':
			ltype = TYPE_JUMP
		elif show == 'pause':
			ltype = TYPE_CALL
		elif show == 'new':
			ltype = TYPE_FORK
		else:
			self.syntax_error('unknown show attribute value')
			ltype = TYPE_JUMP
		atype = ATYPE_WHOLE
		aargs = []
		z = attributes['z-index']
		try:
			z = string.atoi(z)
		except string.atoi_error:
			self.syntax_error('invalid z-index value')
			z = 0
		if z < 0:
			self.syntax_error('anchor with negative z-index')
			z = 0
		coords = attributes.get('coords')
		if coords is not None:
## 			if attributes.has_key('shape') and attributes['shape'] != 'rect':
## 				self.syntax_error('unrecognized shape attribute')
## 				return
			atype = ATYPE_NORMAL
			res = coordre.match(coords)
			if not res:
				self.syntax_error('syntax error in coords attribute')
				return
			x, y, w, h = res.group('x', 'y', 'w', 'h')
			if x[-1] == '%':
				x = string.atoi(x[:-1]) / 100.0
			else:
				x = string.atoi(x)
			if y[-1] == '%':
				y = string.atoi(y[:-1]) / 100.0
			else:
				y = string.atoi(y)
			if w[-1] == '%':
				w = string.atoi(w[:-1]) / 100.0
			else:
				w = string.atoi(w)
			if h[-1] == '%':
				h = string.atoi(h[:-1]) / 100.0
			else:
				h = string.atoi(h)
			# x,y,w,h are now floating point if they were
			# percentages, otherwise they are ints.
			aargs = [x, y, w, h]
		try:
			anchorlist = self.__node.__anchorlist
		except AttributeError:
			self.__node.__anchorlist = anchorlist = []
		aid = _uniqname(map(lambda a: a[2], anchorlist), None)
		if attributes.has_key('iid'):
			aid = attributes['iid']
			atype = ATYPE_NORMAL
		elif nname is not None and aid[:len(nname)+1] == nname + '-':
			# undo CMIF encoding of anchor ID
			aid = aid[len(nname)+1:]
		if aname is not None:
			self.__anchormap[aname] = (uid, aid)
		anchorlist.append((z, len(anchorlist), aid, atype, aargs))
		if href is not None:
			self.__links.append((uid, (aid, atype, aargs),
					     href, ltype))

	def end_anchor(self):
		pass

	# other callbacks

	__whitespace = re.compile(xmllib._opS + '$')
	def handle_data(self, data):
		res = self.__whitespace.match(data)
		if not res:
			self.syntax_error('non-white space content')
		
	__doctype = re.compile('SYSTEM' + xmllib._S + '(?P<dtd>[^ \t\r\n]+)' +
			       xmllib._opS + '$')
	def handle_doctype(self, tag, data):
		if tag != 'smil':
			self.error('not a SMIL document')
		res = self.__doctype.match(data)
		if not res:
			self.syntax_error('invalid DOCTYPE')
			return
		dtd = res.group('dtd')
		if dtd[0] not in '\'"' or dtd[0] != dtd[-1] or \
		   dtd[1:-1] != SMILdtd:
			self.syntax_error('invalid DOCTYPE')
			return

	def handle_proc(self, name, data):
		self.warning('ignoring processing instruction %s' % name)

	# Example -- handle cdata, could be overridden
	def handle_cdata(self, data):
		self.warning('ignoring CDATA')

	# Example -- handle special instructions, could be overridden
	def handle_special(self, data):
		name = string.split(data)[0]
		self.warning('ignoring <!%s> tag' % name)

	# catch all

	def unknown_starttag(self, tag, attrs):
		self.warning('ignoring unknown start tag %s' % tag)

	def unknown_endtag(self, tag):
		self.warning('ignoring unknown end tag %s' % tag or '')

	def unknown_charref(self, ref):
		self.warning('ignoring unknown char ref %s' % ref)

	def unknown_entityref(self, ref):
		self.warning('ignoring unknown entity ref %s' % ref)

	# non-fatal syntax errors

	def syntax_error(self, msg):
		print 'warning: syntax error on line %d: %s' % (self.lineno, msg)

	def warning(self, message):
		print 'warning: %s on line %d' % (message, self.lineno)

	def error(self, message):
		raise MSyntaxError, 'error, line %d: %s' % (self.lineno, message)

	# helper methods

	def __parsecounter(self, value, maybe_relative):
		res = clock_val.match(value)
		if res:
			if res.group('use_clock'):
				h, m, s, f = res.group('hours', 'minutes',
						       'seconds', 'fraction')
				offset = 0
				if h is not None:
					offset = offset + string.atoi(h) * 3600
				m = string.atoi(m)
				if m >= 60:
					self.syntax_error('minutes out of range')
				s = string.atoi(s)
				if s >= 60:
					self.syntax_error('seconds out of range')
				offset = offset + m * 60 + s
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
					offset = offset / 1000.0
				# else already in seconds
			else:
				raise error, 'internal error'
			return offset
		if maybe_relative:
			if value in ('begin', 'end'):
				return value
		raise error, 'bogus presentation counter'

	def __parsetime(self, xpointer):
		offset = 0
		res = id.match(xpointer)
		if res is not None:
			name, event, delay = res.group('name', 'event', 'delay')
		else:
			res = clock.match(xpointer)
			if res is not None:
				# XXXX absolute time not implemented
				return None, 0, 0
			else:
				name, event, delay = None, None, xpointer
		if event is not None:
			counter = self.__parsecounter(event, 1)
			if counter == 'begin':
				counter = 0
			elif counter == 'end':
				counter = -1	# special event
			else:
				raise error, 'bogus presentation counter'
		else:
			counter = 0
		if delay is not None:
			delay = self.__parsecounter(delay, 0)
		else:
			delay = 0
		return name, counter, delay

	def __parserange(self, val):
		res = range.match(val)
		if res is None:
			raise error, 'bogus range parameter'
		if res.group('npt'):
			start, end = res.group('nptstart', 'nptend')
			if start:
				start = float(self.__parsecounter(start, 0))
			else:
				start = None
			if end:
				end = float(self.__parsecounter(end, 0))
			else:
				end = None
		else:
			import smpte
			smpteval = res.group('smpte')
			if smpteval == 'smpte':
				cl = smpte.Smpte30
			elif smpteval == 'smpte-25':
				cl = smpte.Smpte25
			elif smpteval == 'smpte-30-drop':
				cl = smpte.Smpte30Drop
			else:
				raise error, 'bogus range parameter'
			start, end = res.group('smptestart', 'smpteend')
			if start:
				res1 = smpte_time.match(start)
				if res1 is None:
					raise error, 'bogus range parameter'
				if not res1.group('f'):
					# smpte and we have different
					# ideas of which parts are
					# optional
					start = start + '.00'
				start = cl(start)
			else:
				start = None
			if end:
				res2 = smpte_time.match(end)
				if res2 is None:
					raise error, 'bogus range parameter'
				if not res1.group('f'):
					end = end + '.00'
				end = cl(end)
			else:
				end = None
		return start, end

	def __wholenodeanchor(self, node):
		try:
			anchorlist = node.__anchorlist
		except AttributeError:
			node.__anchorlist = anchorlist = []
		for a in anchorlist:
			if a[3] == ATYPE_DEST:
				break
		else:
			a = 0, len(anchorlist), '0', ATYPE_DEST, []
			anchorlist.append(a)
		return node.GetUID(), a[2]

	# the rest is to check that the nesting of elements is done
	# properly (i.e. according to the SMIL DTD)

	__media_object = ('audio', 'video', 'text', 'img', 'ref')
	__schedule = ('par', 'seq') + __media_object
	__container_content = __schedule + ('switch', 'a')
	__assoc_link = ('anchor',)
	__empty = ()
	__allowed_content = {
		'smil': ('head', 'body'),
		'head': ('layout', 'switch', 'meta'),
		'layout': ('channel',),
		'channel': __empty,
		'meta': __empty,
		'body': __container_content,
		'par': __container_content,
		'seq': __container_content,
		'switch': ('layout',) + __container_content,
		'ref': __assoc_link,
		'audio': __assoc_link,
		'img': __assoc_link,
		'video': __assoc_link,
		'text': __assoc_link,
		'a': __schedule + ('switch',),
		'anchor': __empty,
		}

	def finish_starttag(self, tag, attrs):
		if self.stack:
			ptag = self.stack[-1]
			if tag not in self.__allowed_content.get(ptag, ()):
				self.syntax_error('%s element not allowed inside %s' % (tag, ptag))
		elif tag != 'smil':
			self.syntax_error('outermost element must be "smil"')
		xmllib.XMLParser.finish_starttag(self, tag, attrs)

def ReadFile(url):
	if os.name == 'mac':
		import MacOS
		MacOS.splash(514)	# Show "loading document" splash screen
	rv = ReadFileContext(url, MMNode.MMNodeContext(MMNode.MMNode))
	if os.name == 'mac':
		MacOS.splash(515)	# and "Initializing document" (to be removed in mainloop)
	return rv

def ReadFileContext(url, context):
	import posixpath
	utype, str = MMurl.splittype(url)
	host, path = MMurl.splithost(str)
	dir = posixpath.dirname(path)
	if host:
		dir = '//%s%s' % (host, dir)
	if utype:
		dir = '%s:%s' % (utype, dir)
	context.setdirname(dir)
	p = SMILParser(context)
	u = MMurl.urlopen(url)
	p.feed(u.read())
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
				raise error, 'channel with impossible size'
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
			raise error, 'channel with impossible size'
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
