__version__ = "$Id$"

import xmllib
import MMNode, MMAttrdefs
from MMExc import *
from MMTypes import *
import MMurl
## from windowinterface import UNIT_PXL
from HDTL import HD, TL
import string
from AnchorDefs import *
from Hlinks import DIR_1TO2, TYPE_JUMP, TYPE_CALL, TYPE_FORK
import re
import os

error = 'SMILTreeRead.error'

SMILpubid = "-//W3C//DTD SMIL 1.0//EN"
SMILdtd = "http://www.w3.org/AudioVideo/Group/SMIL10.dtd"

LAYOUT_NONE = 0				# must be 0
LAYOUT_SMIL = 1
LAYOUT_UNKNOWN = -1

layout_name = ' SMIL '			# name of layout channel
SMIL_BASIC = 'text/smil-basic-layout'

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
## 		r'(?:\+(?P<delay>.*))?'			# +delay (optional)
		r'$')
clock = re.compile(r'(?P<name>local|remote):'
		   r'(?P<hours>\d+):'
		   r'(?P<minutes>\d{2}):'
		   r'(?P<seconds>\d{2})'
		   r'(?P<fraction>\.\d+)?'
		   r'(?:Z(?P<sign>[-+])(?P<ohours>\d{2}):(?P<omin>\d{2}))?$')
screen_size = re.compile(r'(?P<x>\d+)X(?P<y>\d+)$')
clip = re.compile('^(?:'
		   '(?:(?P<npt>npt)=(?P<nptclip>[^-]*))|'
		   '(?:(?P<smpte>smpte(?:-30-drop|-25)?)=(?P<smpteclip>[^-]*))'
		   ')$')
smpte_time = re.compile(r'(?:(?:\d{2}:)?\d{2}:)?\d{2}(?P<f>\.\d{2})?$')
namedecode = re.compile(r'(?P<name>.*)-\d+$')

colors = {
	'transparent': 'transparent',
	'inherit': 'inherit',

	# color values taken from HTML 4.0 spec
	'aqua': (0x00, 0xFF, 0xFF),
	'black': (0x00, 0x00, 0x00),
	'blue': (0x00, 0x00, 0xFF),
	'fuchsia': (0xFF, 0x00, 0xFF),
	'gray': (0x80, 0x80, 0x80),
	'green': (0x00, 0x80, 0x00),
	'lime': (0x00, 0xFF, 0x00),
	'maroon': (0x80, 0x00, 0x00),
	'navy': (0x00, 0x00, 0x80),
	'olive': (0x80, 0x80, 0x00),
	'purple': (0x80, 0x00, 0x80),
	'red': (0xFF, 0x00, 0x00),
	'silver': (0xC0, 0xC0, 0xC0),
	'teal': (0x00, 0x80, 0x80),
	'white': (0xFF, 0xFF, 0xFF),
	'yellow': (0xFF, 0xFF, 0x00),
	}
color = re.compile('(?:'
		   '#(?P<hex>[0-9a-fA-F]{3}|'		# #f00
			    '[0-9a-fA-F]{6})|'		# #ff0000
		   'rgb\((?: *(?P<ri>[0-9]+) *,'	# rgb(255, 0, 0)
			   ' *(?P<gi>[0-9]+) *,'
			   ' *(?P<bi>[0-9]+) *|'
			   ' *(?P<rp>[0-9]+) *% *,'	# rgb(100%, 0%, 0%)
			   ' *(?P<gp>[0-9]+) *% *,'
			   ' *(?P<bp>[0-9]+) *% *)\))$')

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
		self.__root_layout = None
		self.__container = None
		self.__node = None	# the media object we're in
		self.__regions = {}
		self.__width = self.__height = 0
		self.__layout = None
		self.__nodemap = {}
		self.__anchormap = {}
		self.__links = []
		self.par_attributes['sync'] = None # reset in case it changed
		self.__title = layout_name
		self.__base = ''
		self.__dict__['start_root-layout'] = self.start_0root_layout
		self.__dict__['end_root-layout'] = self.end_0root_layout
		self.__dict__['root-layout_attributes'] = self.root_layout_attributes

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
				print 'warning: out of scope sync arc from',\
				      node.attrdict.get('name','<unnamed>'),\
				      'to',name
				return
## 				if self.__nodemap.has_key(name):
## 					xnode = self.__nodemap[name]
## 				else:
## 					print 'warning: ignoring unknown node',\
## 					      name,'in syncarc'
## 					return
			if counter == -1:
				xside = TL
				counter = 0
			else:
				xside = HD
			synctolist.append((xnode.GetUID(), xside, delay + counter, yside))

	def AddAttrs(self, node, attributes):
		node.__syncarcs = []
		attrdict = node.attrdict
		for attr, val in attributes.items():
			if attr == 'id':
				if self.__nodemap.has_key(val):
					self.syntax_error('node id %s not unique'%val)
				else:
					self.__nodemap[val] = node
				res = namedecode.match(val)
				if res is not None:
					val = res.group('name')
				attrdict['name'] = val
			elif attr == 'src':
				attrdict['file'] = MMurl.basejoin(self.__base, val)
			elif attr == 'begin' or attr == 'end':
				node.__syncarcs.append(attr, val)
			elif attr == 'dur':
				if val == 'indefinite':
					attrdict['duration'] = -1
				else:
					try:
						attrdict['duration'] = self.__parsecounter(val, 0)
					except error, msg:
						self.syntax_error(msg)
			elif attr == 'repeat':
				if val == 'indefinite':
					attrdict['loop'] = 0
				else:
					try:
						repeat = string.atoi(val)
					except string.atoi_error:
						self.syntax_error('bad repeat attribute')
					else:
						if repeat <= 0:
							self.warning('bad repeat value')
						else:
							attrdict['loop'] = repeat
			elif attr == 'system-bitrate':
				try:
					bitrate = string.atoi(val)
				except string.atoi_error:
					self.syntax_error('bad bitrate attribute')
				else:
					attrdict['system_bitrate'] = bitrate
			elif attr == 'system-screen-size':
				res = screen_size.match(val)
				if res is None:
					self.syntax_error('bad screen-size attribute')
				else:
					attrdict['system_screen_size'] = \
						tuple(map(string.atoi,
							  res.group('x','y')))
			elif attr == 'system-screen-depth':
				try:
					depth = string.atoi(val)
				except string.atoi_error:
					self.syntax_error('bad screen-depth attribute')
				else:
					attrdict['system_screen_depth'] = depth
			elif attr == 'system-captions':
				if val == 'on':
					attrdict['system_captions'] = 1
				elif val == 'off':
					attrdict['system_captions'] = 0
				else:
					self.syntax_error('bad system-captions attribute')
			elif attr == 'system-language':
				attrdict['system_language'] = val
			elif attr == 'system-overdub-or-caption':
				if val in ('caption', 'overdub'):
					attrdict['system_overdub_or_caption'] = val
				else:
					self.syntax_error('bad system-overdub-or-caption attribute')
			elif attr == 'system-required':
				attrdict['system_required'] = val

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
		is_ext = attributes.has_key('src')
		if is_ext:
			url = attributes['src']
			url = MMurl.basejoin(self.__base, url)
			url = self.__context.findurl(url)
			nodetype = 'ext'
		else:
			nodetype = 'imm'
			self.__nodedata = []
			self.__data = []
			if not attributes.has_key('type'):
				self.syntax_error('neither src nor type attribute')
		self.__is_ext = is_ext

		# find out type of file
		subtype = None
		mtype = attributes.get('type')
# not allowed to look at extension...
## 		if mtype is None and is_ext:
## 			import mimetypes
## 			# guess the type from the file extension
## 			mtype = mimetypes.guess_type(url)[0]
		if mtype is None and mediatype is None and is_ext:
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

		if mtype is None and mediatype is None:
			# we've tried, but we just don't know what
			# we're dealing with
			self.syntax_error('unknown object type')
			return

		if mtype is not None:
			mtype = string.split(mtype, '/')
			if mediatype is not None and mtype[0] != mediatype:
				self.warning("file type doesn't match element")
			mediatype = mtype[0]
			subtype = mtype[1]

		if attributes['encoding'] not in ('base64', 'UTF'):
			self.syntax_error('bad encoding parameter')

		# create the node
		if not self.__root:
			node = self.MakeRoot(nodetype)
		elif not self.__container:
			self.syntax_error('node not in container')
			return
		else:
			node = self.__context.newnode(nodetype)
			self.__container._addchild(node)
		self.__node = node
		self.AddAttrs(node, attributes)
		node.__mediatype = mediatype, subtype
		self.__attributes = attributes

	def EndNode(self):
		node = self.__node
		attributes = self.__attributes
		self.__node = None
		del self.__attributes
		mediatype, subtype = node.__mediatype

		if not self.__is_ext:
			encoding = attributes['encoding']
			data = string.split(string.join(self.__nodedata, ''), '\n')
			for i in range(len(data)-1, -1, -1):
				tmp = string.join(string.split(data[i]))
				if tmp:
					data[i] = tmp
				else:
					del data[i]
			self.__data.append(string.join(data, '\n'))
			nodedata = string.join(self.__data, '')
## 			res = self.__whitespace.match(nodedata)
## 			if res is not None:
## 				self.syntax_error('no src attribute and no content data')
			if encoding == 'base64':
				# create data URL for base64 encoded data
				url = 'data:%s/%s;base64,%s' % (mediatype, subtype, nodedata)
				node.type = 'ext'
				node.attrdict['file'] = url
			else:
				# other data is immediate
				nodedata = string.split(nodedata, '\n')
				node.values = nodedata

		# connect to region
		if attributes.has_key('region'):
			region = attributes['region']
			if not self.__regions.has_key(region):
				self.syntax_error('unknown region')
		else:
			self.warning('node without region attribute')
			region = '<unnamed %d>'
			i = 0
			while self.__regions.has_key(region % i):
				i = i + 1
			region = region % i
		node.__region = region
		ch = self.__regions.get(region)
		if ch is None:
			self.__regions[region] = ch = \
					{'minwidth': 0, 'minheight': 0,
					 'left': 0, 'top': 0,
					 'width': 0, 'height': 0,
					 'z-index': 0, 'fit': 'meet',
					 'background-color': 'transparent'}
		if mediatype in ('image', 'video'):
			x, y, w, h = ch['left'], ch['top'], ch['width'], ch['height']
			# if we don't know the region size and
			# position in pixels, we need to look at the
			# media objects to figure out the size to use.
			if w > 0 and h > 0 and \
			   type(w) == type(h) == type(0) and \
			   (x == y == 0 or type(x) == type(y) == type(0)) and \
			   ch['fit'] != 'visible':
				# size and position is given in pixels
				pass
			elif node.attrdict.has_key('file'):
				url = self.__context.findurl(node.attrdict['file'])
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
					# want to make them at least visible...
					if ch['width'] == 0:
						ch['minwidth'] = 100
					if ch['height'] == 0:
						ch['minheight'] = 100
				else:
					node.__size = width, height
					if ch['minwidth'] < width:
						ch['minwidth'] = width
					if ch['minheight'] < height:
						ch['minheight'] = height
					if ch['fit'] == 'visible':
						w = ch['width']
						if type(w) is type(0) and w < width:
							ch['width'] = width
						h = ch['height']
						if type(h) is type(0) and h < height:
							ch['height'] = height
		elif mediatype == 'text':
			# want to make them at least visible...
			if ch['width'] == 0:
				ch['minwidth'] = 200
			if ch['height'] == 0:
				ch['minheight'] = 100

		# clip-* attributes for video
		clip_begin = attributes.get('clip-begin')
		if clip_begin:
			if clip.match(clip_begin):
				node.attrdict['clipbegin'] = clip_begin
			else:
				self.syntax_error('invalid clip-begin attribute')
		clip_end = attributes.get('clip-end')
		if clip_end:
			if clip.match(clip_end):
				node.attrdict['clipend'] = clip_end
			else:
				self.syntax_error('invalid clip-end attribute')

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
		self.AddAttrs(node, attributes)

	def EndContainer(self):
		self.__container = self.__container.GetParent()

	def Recurse(self, root, *funcs):
		for func in funcs:
			func(root)
		for node in root.GetChildren():
			apply(self.Recurse, (node,) + funcs)

	def FixSizes(self):
		# calculate minimum required size of top-level window
		for attrdict in self.__regions.values():
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

	def CreateLayout(self):
		bg = None
		if self.__root_layout is not None:
			attrs = self.__root_layout
			width = attrs['width']
			if width[-2:] == 'px':
				width = width[:-2]
			try:
				width = string.atoi(width)
			except string.atoi_error:
				self.syntax_error('root-layout width not an integer')
			else:
				if width < 0:
					self.syntax_error('root-layout width not a positive integer')
				elif width > 0:
					self.__width = width
			height = attrs['height']
			if height[-2:] == 'px':
				height = height[:-2]
			try:
				height = string.atoi(height)
			except string.atoi_error:
				self.syntax_error('root-layout height not an integer')
			else:
				if height < 0:
					self.syntax_error('root-layout height not a positive integer')
				elif height > 0:
					self.__height = height
			bg = attrs['background-color']
			bg = self.__convert_color(bg)
		ctx = self.__context
		layout = MMNode.MMChannel(ctx,
					  self.__title)
		ctx.channeldict[self.__title] = layout
		ctx.channelnames.insert(0, self.__title)
		ctx.channels.insert(0, layout)
		self.__layout = layout
		layout['type'] = 'layout'
		if bg is not None and \
		   bg != 'transparent' and \
		   bg != 'inherit':
			layout['bgcolor'] = bg
		if self.__width == 0:
			self.__width = 640
		if self.__height == 0:
			self.__height = 480
		layout['winsize'] = \
			self.__width, self.__height
		layout['units'] = 2 # UNIT_PXL

	def FixChannel(self, node):
		if node.GetType() not in leaftypes:
			return
		mediatype, subtype = node.__mediatype
		del node.__mediatype
		try:
			region = node.__region
			del node.__region
		except AttributeError:
			region = '<unnamed>'
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
		name = '%s %s' % (region, mediatype)
		ctx = self.__context
		for key in region, name:
			ch = ctx.channeldict.get(key)
			if ch is not None and ch['type'] == mtype:
				name = key
				break
		else:
			# there is no channel of the right name and type
			if not ctx.channeldict.has_key(region):
				name = region
			ch = MMNode.MMChannel(ctx, name)
			ctx.channeldict[name] = ch
			ctx.channelnames.append(name)
			ctx.channels.append(ch)
			ch['type'] = mtype
			if mediatype in ('image', 'video', 'text'):
				# deal with channel with window
				if not self.__regions.has_key(region):
					self.warning('no region %s in layout' %
						     region)
					self.__in_layout = LAYOUT_SMIL
					self.start_region({'id': region})
					self.__in_layout = LAYOUT_NONE
				attrdict = self.__regions[region]
				if self.__layout is None:
					# create a layout channel
					self.CreateLayout()
				ch['base_window'] = self.__title
				title = attrdict.get('title')
				if title is not None:
					ch['comment'] = title
				bg = attrdict['background-color']
				if bg == 'transparent':
					ch['transparent'] = 1
				else:
					ch['transparent'] = -1
					ch['bgcolor'] = bg
				ch['z'] = attrdict['z-index']
				x = attrdict['left']
				y = attrdict['top']
				w = attrdict['width']
				h = attrdict['height']
				fit = attrdict['fit']
				if fit == 'meet':
					ch['scale'] = 0
				elif fit == 'hidden':
					ch['scale'] = 1
				elif fit == 'slice':
					ch['scale'] = -1
				elif fit == 'visible':
					ch['scale'] = 1
				ch['center'] = 0
				# other fit options not implemented
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
				if self.__anchormap.has_key(href[1:]):
					dst = self.__anchormap[href[1:]]
				else:
					if self.__nodemap.has_key(href[1:]):
						dst = self.__nodemap[href[1:]]
						dst = self.__wholenodeanchor(dst)
					else:
						print 'warning: unknown node id',href[1:]
						continue
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
		# fill in defaults for seq
		attributes['repeat'] = '1'
		self.NewContainer('seq', attributes)

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

	meta_attributes = {'name':None, 'content':None, 'id':None}
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
		elif name == 'title':
			# make sure __title cannot be a SMIL region id
			self.__title = ' %s ' % content
		elif name == 'base':
			self.__base = content
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
		if attributes['type'] == SMIL_BASIC:
			if self.__seen_layout == LAYOUT_SMIL:
				# if we've seen SMIL_BASIC already,
				# ignore this one
				self.__in_layout = LAYOUT_UNKNOWN
			else:
				self.__in_layout = LAYOUT_SMIL
			self.__seen_layout = LAYOUT_SMIL
		else:
			self.__in_layout = LAYOUT_UNKNOWN
			if self.__seen_layout != LAYOUT_SMIL:
				self.__seen_layout = LAYOUT_UNKNOWN

	def end_layout(self):
		self.__in_layout = LAYOUT_NONE

	region_attributes = {'id':None, 'left':'0', 'top':'0', 'z-index':'0',
			      'width':'0', 'height':'0', 'fit':'meet',
			      'background-color':'transparent',
			      'skip-content':'true', 'title':None}
	def start_region(self, attributes):
		if not self.__in_layout:
			self.syntax_error('region not in layout')
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

		val = attributes.get('id')
		if val is None:
			self.syntax_error('region without id attribute')
			return
		if self.__regions.has_key(val):
			self.syntax_error('multiple region tags for id=%s' % val)
			return
		attrdict['id'] = val
		self.__regions[val] = attrdict

		for attr in ('left', 'top', 'width', 'height'):
			val = attributes[attr]
			try:
				if val[-1] == '%':
					val = string.atof(val[:-1]) / 100.0
					if val < 0 or val > 1:
						self.syntax_error('region with impossible size')
						if val < 0: val = 0.0
						else: val = 1.0
				else:
					if val[-2:] == 'px':
						val = val[:-2]
					val = string.atoi(val)
					if val < 0:
						self.syntax_error('region with impossible size')
						val = 0
			except (string.atoi_error, string.atof_error):
				self.syntax_error('invalid region attribute value')
				val = 0
			attrdict[attr] = val

		val = attributes['z-index']
		try:
			val = string.atoi(val)
		except string.atoi_error:
			self.syntax_error('invalid z-index value')
			val = 0
		if val < 0:
			self.syntax_error('region with negative z-index')
			val = 0
		attrdict['z-index'] = val

		val = attributes['fit']
		if val not in ['meet', 'slice', 'fill', 'visible', 'hidden',
			       'scroll']:
			self.syntax_error('illegal fit attribute')
		attrdict['fit'] = val

		val = self.__convert_color(attributes['background-color'])
		if val is not None:
			attrdict['background-color'] = val

		attrdict['title'] = attributes.get('title')

	def end_region(self):
		pass

	root_layout_attributes = {'background-color':'transparent',
				  'id':None, 'height':'0', 'width':'0',
				  'overflow':'hidden',
				  'skip-content':'true', 'title':None}
	def start_0root_layout(self, attributes):
		self.__root_layout = attributes

	def end_0root_layout(self):
		pass

	# container nodes

	par_attributes = {'title':None, 'id':None, 'endsync':None, 'sync':None,
			  'dur':None, 'repeat':'1',
			  'region':None, 'begin':None, 'end':None,
			  'author':'', 'copyright':'', 'abstract':'',
			  'system-bitrate':None, 'system-language':None,
			  'system-captions':None,
			  'system-overdub-or-caption':None,
			  'system-required':None, 'system-screen-size':None,
			  'system-screen-depth':None}
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

	seq_attributes = {'id':None, 'title':None, 'dur':None, 'begin':None,
			  'end':None, 'repeat':'1',
			  'author':'', 'copyright':'', 'abstract':'',
			  'system-bitrate':None, 'system-language':None,
			  'system-captions':None,
			  'system-overdub-or-caption':None,
			  'system-required':None, 'system-screen-size':None,
			  'system-screen-depth':None}
	def start_seq(self, attributes):
		self.NewContainer('seq', attributes)

	end_seq = EndContainer

	def start_bag(self, attributes):
		self.NewContainer('bag', attributes)

	end_bag = EndContainer

	switch_attributes = {'id':None,
			     'system-bitrate':None, 'system-language':None,
			     'system-captions':None,
			     'system-overdub-or-caption':None,
			     'system-required':None, 'system-screen-size':None,
			     'system-screen-depth':None}
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

	basic_attributes = {'id':None, 'src':None, 'type':None, 'region':None,
			    'dur':None, 'begin':None, 'end':None, 'repeat':'1',
			    'fill':None, 'encoding':'base64',
			    'alt':None, 'longdesc':None, 'title':None,
			    'clip-begin':None, 'clip-end':None,
			    'author':'', 'copyright':'', 'abstract':'',
			    'system-bitrate':None, 'system-language':None,
			    'system-captions':None,
			    'system-overdub-or-caption':None,
			    'system-required':None, 'system-screen-size':None,
			    'system-screen-depth':None}
	ref_attributes = basic_attributes.copy()
	def start_ref(self, attributes):
		self.NewNode(None, attributes)

	def end_ref(self):
		self.EndNode()

	text_attributes = basic_attributes
	text_attributes['encoding'] = 'UTF'
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

	animation_attributes = ref_attributes
	def start_animation(self, attributes):
		self.NewNode('animation', attributes)

	def end_animation(self):
		self.EndNode()

	textstream_attributes = ref_attributes
	textstream_attributes['encoding'] = 'UTF'
	def start_textstream(self, attributes):
		self.NewNode('textstream', attributes)

	def end_textstream(self):
		self.EndNode()

	cmif_cmif_attributes = basic_attributes
	cmif_cmif_attributes['encoding'] = 'UTF'
	def start_cmif_cmif(self, attributes):
		self.NewNode('cmif_cmif', attributes)

	def end_cmif_cmif(self):
		self.EndNode()

	cmif_socket_attributes = basic_attributes
	cmif_socket_attributes['encoding'] = 'UTF'
	def start_cmif_socket(self, attributes):
		self.NewNode('cmif_socket', attributes)

	def end_cmif_socket(self):
		self.EndNode()

	cmif_shell_attributes = basic_attributes
	cmif_shell_attributes['encoding'] = 'UTF'
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
			     'end':None, 'fragment-id':None}
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
		if attributes.has_key('fragment-id'):
			aid = attributes['fragment-id']
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
		if self.__node is None or self.__is_ext:
			res = self.__whitespace.match(data)
			if not res:
				self.syntax_error('non-white space content')
			return
		self.__nodedata.append(data)
		
	__doctype = re.compile('SYSTEM' + xmllib._S + '(?P<dtd>[^ \t\r\n]+)' +
			       xmllib._opS + '$')
	def handle_doctype(self, tag, pubid, syslit, data):
		if tag != 'smil':
			self.error('not a SMIL document')
		if pubid != SMILpubid or syslit != SMILdtd or data:
			self.syntax_error('invalid DOCTYPE')

	def handle_proc(self, name, data):
		self.warning('ignoring processing instruction %s' % name)

	# Example -- handle cdata, could be overridden
	def handle_cdata(self, cdata):
		if self.__node is None or self.__is_ext:
			self.warning('ignoring CDATA')
			return
		data = string.split(string.join(self.__nodedata, ''), '\n')
		for i in range(len(data)-1, -1, -1):
			tmp = string.join(string.split(data[i]))
			if tmp:
				data[i] = tmp
			else:
				del data[i]
		self.__data.append(string.join(data, '\n'))
		self.__nodedata = []
		self.__data.append(cdata)

## 	# Example -- handle special instructions, could be overridden
## 	def handle_special(self, data):
## 		name = string.split(data)[0]
## 		self.warning('ignoring <!%s> tag' % name)

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
			name, event = res.group('name', 'event')
			delay = None
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
			counter = 0
		if delay is not None:
			delay = self.__parsecounter(delay, 0)
		else:
			delay = 0
		return name, counter, delay

	def __parseclip(self, val):
		res = clip.match(val)
		if res is None:
			raise error, 'bogus clip parameter'
		if res.group('npt'):
			val = res.group('nptclip')
			if val:
				val = float(self.__parsecounter(val, 0))
			else:
				start = None
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
				raise error, 'bogus clip parameter'
			val = res.group('smpteclip')
			if val:
				res = smpte_time.match(val)
				if res is None:
					raise error, 'bogus clip parameter'
				if not res.group('f'):
					# smpte and we have different
					# ideas of which parts are
					# optional
					val = val + '.00'
				val = cl(val)
			else:
				val = None
		return val

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

	def __convert_color(self, val):
		if colors.has_key(val):
			return colors[val]
		res = color.match(val)
		if res is None:
			self.syntax_error('bad color specification')
			return
		else:
			hex = res.group('hex')
			if hex is not None:
				if len(hex) == 3:
					r = string.atoi(hex[0]*2, 16)
					g = string.atoi(hex[1]*2, 16)
					b = string.atoi(hex[2]*2, 16)
				else:
					r = string.atoi(hex[0:2], 16)
					g = string.atoi(hex[2:4], 16)
					b = string.atoi(hex[4:6], 16)
			else:
				r = res.group('ri')
				if r is not None:
					r = string.atoi(r)
					g = string.atoi(res.group('gi'))
					b = string.atoi(res.group('bi'))
				else:
					r = int(string.atof(res.group('rp')) * 255 / 100.0 + 0.5)
					g = int(string.atof(res.group('gp')) * 255 / 100.0 + 0.5)
					b = int(string.atof(res.group('bp')) * 255 / 100.0 + 0.5)
		if r > 255: r = 255
		if g > 255: g = 255
		if b > 255: b = 255
		return r, g, b

	# the rest is to check that the nesting of elements is done
	# properly (i.e. according to the SMIL DTD)

	__media_object = ('audio', 'video', 'text', 'img', 'animation',
			  'textstream', 'ref')
	__schedule = ('par', 'seq') + __media_object
	__container_content = __schedule + ('switch', 'a')
	__assoc_link = ('anchor',)
	__empty = ()
	__allowed_content = {
		'smil': ('head', 'body'),
		'head': ('layout', 'switch', 'meta'),
		'layout': ('region', 'root-layout',),
		'region': __empty,
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
		'animation': __assoc_link,
		'textstream': __assoc_link,
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
	data = u.read()
	p.feed(data)
	p.close()
	root = p.GetRoot()
	root.source = data
	return root

def ReadString(string, name):
	return ReadStringContext(string, name,
				 MMNode.MMNodeContext(MMNode.MMNode))

def ReadStringContext(string, name, context):
	p = SMILParser(context)
	p.feed(string)
	p.close()
	root = p.GetRoot()
	root.source = string
	return root

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
				raise error, 'region with impossible size'
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
			raise error, 'region with impossible size'
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
