__version__ = "$Id$"

import xmllib
import MMNode, MMAttrdefs
from MMExc import *
from MMTypes import *
import MMurl
from HDTL import HD, TL
import string
from AnchorDefs import *
from Hlinks import DIR_1TO2, TYPE_JUMP, TYPE_CALL, TYPE_FORK
import re
import os, sys
from SMIL import *
import settings
import features
import compatibility
import ChannelMap

error = 'SMILTreeRead.error'

LAYOUT_NONE = 0				# must be 0
LAYOUT_SMIL = 1
LAYOUT_UNKNOWN = -1

layout_name = ' SMIL '			# name of layout channel

coordre = re.compile(r'^(?P<x0>\d+%?),(?P<y0>\d+%?),'
		     r'(?P<x1>\d+%?),(?P<y1>\d+%?)$')
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
		  '(?:(?P<smpte>smpte(?:-30-drop|-25)?)=(?P<smpteclip>[^-]*))|'
		  '(?P<clock>'+clock_val.pattern+')'
		  ')$')
smpte_time = re.compile(r'(?:(?:\d{2}:)?\d{2}:)?\d{2}(?P<f>\.\d{2})?$')
namedecode = re.compile(r'(?P<name>.*)-\d+$')
_token = '[^][\001-\040()<>@,;:\\"/?=\177-\377]+' # \000 also not valid
dataurl = re.compile('data:(?P<type>'+_token+'/'+_token+')?'
		     '(?P<params>(?:;'+_token+'=(?:'+_token+'|"[^"\\\r\177-\377]*(?:\\.[^"\\\r\177-\377]*)*"))*)'
		     '(?P<base64>;base64)?'
		     ',(?P<data>.*)', re.I)

del _token

from colors import colors
color = re.compile('(?:'
		   '#(?P<hex>[0-9a-fA-F]{3}|'		# #f00
			    '[0-9a-fA-F]{6})|'		# #ff0000
		   'rgb\((?: *(?P<ri>[0-9]+) *,'	# rgb(255, 0, 0)
			   ' *(?P<gi>[0-9]+) *,'
			   ' *(?P<bi>[0-9]+) *|'
			   ' *(?P<rp>[0-9]+) *% *,'	# rgb(100%, 0%, 0%)
			   ' *(?P<gp>[0-9]+) *% *,'
			   ' *(?P<bp>[0-9]+) *% *)\))$')

smil_node_attrs = [
	'region', 'clip-begin', 'clip-end', 'endsync', 'choice-index',
	'bag-index', 'type',
	]

class SMILParser(SMIL, xmllib.XMLParser):
	__warnmeta = 0		# whether to warn for unknown meta properties

	def __init__(self, context, printfunc = None, new_file = 0, check_compatibility = 0):
		self.elements = {
			'smil': (self.start_smil, self.end_smil),
			'head': (self.start_head, self.end_head),
			'meta': (self.start_meta, self.end_meta),
			'layout': (self.start_layout, self.end_layout),
			GRiNSns+' '+'user-attributes': (self.start_user_attributes, self.end_user_attributes),
			GRiNSns+' '+'u-group': (self.start_u_group, self.end_u_group),
			'region': (self.start_region, self.end_region),
			'root-layout': (self.start_root_layout, self.end_root_layout),
			GRiNSns+' '+'layouts': (self.start_layouts, self.end_layouts),
			GRiNSns+' '+'layout': (self.start_Glayout, self.end_Glayout),
			'body': (self.start_body, self.end_body),
			'par': (self.start_par, self.end_par),
			'seq': (self.start_seq, self.end_seq),
			'switch': (self.start_switch, self.end_switch),
			GRiNSns+' '+'choice': (self.start_choice, self.end_choice),
			GRiNSns+' '+'bag': (self.start_choice, self.end_choice),
			'ref': (self.start_ref, self.end_ref),
			'text': (self.start_text, self.end_text),
			'audio': (self.start_audio, self.end_audio),
			'img': (self.start_img, self.end_img),
			'video': (self.start_video, self.end_video),
			'animation': (self.start_animation, self.end_animation),
			'textstream': (self.start_textstream, self.end_textstream),
			GRiNSns+' '+'socket': (self.start_socket, self.end_socket),
			GRiNSns+' '+'shell': (self.start_shell, self.end_shell),
			GRiNSns+' '+'cmif': (self.start_cmif, self.end_cmif),
			'a': (self.start_a, self.end_a),
			'anchor': (self.start_anchor, self.end_anchor),
			}
		xmllib.XMLParser.__init__(self)
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
		self.__regions = {}	# mapping from region id to chan. attrs
		self.__region2channel = {} # mapping from region to channels
		self.__ids = {}		# collect all id's here
		self.__width = self.__height = 0
		self.__root_width = self.__root_height = 0 # w,h in root-layout
		self.__layout = None
		self.__nodemap = {}
		self.__idmap = {}
		self.__anchormap = {}
		self.__links = []
		self.__title = None
		self.__base = ''
		self.__printfunc = printfunc
		self.__printdata = []
		self.__u_groups = {}
		self.__layouts = {}
		self.__realpixnodes = []
		self.__new_file = new_file
		self.__check_compatibility = check_compatibility
		if new_file and type(new_file) == type(''):
			self.__base = new_file
		self.__validchannels = {'undefined':0}
		for chtype in ChannelMap.getvalidchanneltypes():
			self.__validchannels[chtype] = 1

	def close(self):
		xmllib.XMLParser.close(self)
		if self.__printfunc is not None and self.__printdata:
			data = string.join(self.__printdata, '\n')
			# first 30 lines should be enough
			data = string.split(data, '\n')
			if len(data) > 30:
				data = data[:30]
				data.append('. . .')
			self.__printfunc(string.join(data, '\n'))
			self.__printdata = []

	def GetRoot(self):
		if not self.__root:
			self.error('empty document', self.lineno)
		return self.__root

	def MakeRoot(self, type):
		self.__root = self.__context.newnodeuid(type, '1')
		self.__root.SMILidmap = self.__idmap
		return self.__root

	def SyncArc(self, node, attr, val):
		synctolist = node.attrdict.get('synctolist', [])
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
			if yside == HD:
				node.attrdict['begin'] = delay
				return
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
					self.error('node not in parent', self.lineno)
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
			xnode = self.__nodemap.get(name)
			if xnode is None:
				self.warning('ignoring sync arc from %s to unknown node' % node.attrdict.get('name','<unnamed>'))
				return
			for n in GetTemporalSiblings(node):
				if n is xnode:
					break
			else:
				self.warning('out of scope sync arc from %s to %s' % (node.attrdict.get('name','<unnamed>'), xnode.attrdict.get('name','<unnamed>')))
				return
			if counter == -1:
				xside = TL
				counter = 0
			else:
				xside = HD
			synctolist.append((xnode.GetUID(), xside, delay + counter, yside))
		node.attrdict['synctolist'] = synctolist

	def AddAttrs(self, node, attributes):
		node.__syncarcs = []
		node.__anchorlist = []
		attrdict = node.attrdict
		for attr, val in attributes.items():
			if attr == 'id':
				self.__nodemap[val] = node
				self.__idmap[val] = node.GetUID()
				res = namedecode.match(val)
				if res is not None:
					val = res.group('name')
				attrdict['name'] = val
			elif attr == 'src':
				# Special case: # is used as a placeholder for empty URL fields
				if val != '#':
					attrdict['file'] = MMurl.basejoin(self.__base, val)
			elif attr == 'begin' or attr == 'end':
				node.__syncarcs.append((attr, val))
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
							self.warning('bad repeat value', self.lineno)
						elif repeat != 1:
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
			elif attr == 'u-group':
				if self.__u_groups.has_key(val):
					attrdict['u_group'] = val
				else:
					self.syntax_error("unknown u-group `%s'" % val)
			elif attr == 'layout':
				if self.__layouts.has_key(val):
					attrdict['layout'] = val
				else:
					self.syntax_error("unknown layout `%s'" % val)
			elif attr == 'title':
				attrdict['title'] = val
			elif attr == 'fill':
				if val in ('freeze', 'remove'):
					attrdict['fill'] = val
				else:
					self.syntax_error("bad fill attribute")
			elif compatibility.QT == features.compatibility and \
				self.addQTAttr(attr, val, node):
				pass
			elif attr not in smil_node_attrs:
				# catch all
				try:
					attrdict[attr] = parseattrval(attr, val, self.__context)
				except:
					pass
		if attrdict.has_key('fill') and \
		   attrdict['fill'] == 'freeze' and \
		   not attrdict.has_key('duration'):
			del attrdict['fill']			

	def addQTAttr(self, key, val, node):
		attrdict = node.attrdict
		if key == 'immediate-instantiation': 
			internalval = self.parseEnumValue(val, {'false':0,'true':1},key, 'immediateinstantiationmedia')
			attrdict['immediateinstantiationmedia'] = internalval
			return 1
		elif key == 'bitrate':
			internalval = self.parseIntValue(val, key, 'bitratenecessary')
			attrdict['bitratenecessary'] = internalval
			return 1
		elif key == 'system-mime-type-supported':
			internalval = val
			attrdict['systemmimetypesupported'] = internalval
			return 1
		elif key == 'attach-timebase': 
			internalval = self.parseEnumValue(val, {'false':0,'true':1},key, 'attachtimebase')
			attrdict['attachtimebase'] = internalval
			return 1
		elif key == 'chapter':
			internalval = val
			attrdict['qtchapter'] = internalval
			return 1
		elif key == 'composite-mode':
			internalval = val
			attrdict['qtcompositemode'] = internalval
			return 1
		
		return 0
				
	def parseEnumValue(self, val, dict, smilattributename, internalattributename):
		if dict.has_key(val):
			return dict[val]
		else:
			self.syntax_error('invalid '+smilattributename+' value')
			return MMAttrdefs.getdefattr(None, internalattributename)

	def parseIntValue(self, val, smilattributename, internalattributename):
		intvalue = 0
		try:
			intvalue = string.atoi(val)
		except string.atoi_error:
			self.syntax_error('invalid '+smilattributename+' value')
			intvalue = MMAttrdefs.getdefattr(None, internalattributename)
			
		return intvalue
			
	def NewNode(self, tagname, attributes):
		# mimetype -- the MIME type of the node as specified in attr
		# mtype -- the MIME type of the node as calculated
		# mediatype, subtype -- mtype split into parts
		# tagname -- the tag name in the SMIL file (None for "ref")
		# nodetype -- the CMIF node type (imm/ext/...)
		for key, val in attributes.items():
			if key[:len(GRiNSns)+1] == GRiNSns + ' ':
				del attributes[key]
				attributes[key[len(GRiNSns)+1:]] = val
			if key[:len(QTns)+1] == QTns + ' ':
				del attributes[key]
				attributes[key[len(QTns)+1:]] = val

		id = attributes.get('id')
		if id is not None:
			res = xmllib.tagfind.match(id)
			if res is None or res.end(0) != len(id):
				self.syntax_error("illegal ID value `%s'" % id)
			if self.__ids.has_key(id):
				self.syntax_error('non-unique id %s' % id)
			self.__ids[id] = 0
		if not self.__in_smil:
			self.syntax_error('node not in smil')
			return
		if self.__in_layout:
			self.syntax_error('node in layout')
			return
		if self.__node:
			# the warning comes later from xmllib
			self.EndNode()
		url = attributes.get('src')
		data = None
		mtype = None
		nodetype = 'ext'
		self.__is_ext = 1
		if not url:
			url = None
		if url == '#':
			url = None
		elif url[:1] == '#':
			# just a #name URL, not valid here
			self.syntax_error('no proper src attribute')
			url = None
		elif url is not None:
			url, tag = MMurl.splittag(url)
			url = MMurl.basejoin(self.__base, url)
			url = self.__context.findurl(url)
			res = dataurl.match(url)
			if res is not None and res.group('base64') is None:
				mtype = res.group('type') or 'text/plain'
				data = string.split(MMurl.unquote(res.group('data')), '\n')
				nodetype = 'imm'
				del attributes['src']
		else:
			# remove if immediate data allowed
			self.syntax_error('no src attribute')

##			nodetype = 'imm'
##			self.__is_ext = 0
##			self.__nodedata = []
##			self.__data = []
##			if not attributes.has_key('type'):
##				self.syntax_error('no type attribute')

		# find out type of file
		subtype = None
		mimetype = attributes.get('type')
		if mimetype is not None:
			mtype = mimetype
# not allowed to look at extension...
		if mtype is None and url is not None and settings.get('checkext'):
 			import MMmimetypes
 			# guess the type from the file extension
 			mtype = MMmimetypes.guess_type(url)[0]
		if url is not None and mtype is None and \
		   (tagname is None or tagname == 'text'):
			# last resort: get file and see what type it is
			try:
				u = MMurl.urlopen(url)
			except:
				self.warning('cannot open file %s' % url, self.lineno)
				# we have no idea what type the file is
			else:
				mtype = u.headers.type
				u.close()

		mediatype = tagname
		if mtype is not None:
			mtype = string.split(mtype, '/')
##			if tagname is not None and mtype[0]!=tagname and \
##			   (tagname[:5]!='cmif_' or mtype!=['text','plain']):
##				self.warning("file type doesn't match element", self.lineno)
			if tagname is None or tagname[:5] != 'cmif_':
				mediatype = mtype[0]
				subtype = mtype[1]
			

		# now determine channel type
		if subtype is not None and \
		   string.find(string.lower(subtype), 'real') >= 0:
			# if it's a RealMedia type, use tag to determine chtype
			if tagname == 'audio':
				chtype = 'RealAudio'
			elif tagname == 'image' or tagname == 'animation':
				chtype = 'RealPix'
			elif tagname == 'text' or tagname == 'textstream':
				chtype = 'RealText'
			else:
				if mediatype == 'audio':
					chtype = 'RealAudio'
				elif mediatype == 'image':
					chtype = 'RealPix'
				elif mediatype == 'text':
					chtype = 'RealText'
				else:
					chtype = 'RealVideo'

		elif mediatype == 'audio':
			chtype = 'sound'
		elif mediatype == 'image':
			chtype = 'image'
		elif mediatype == 'video':
			chtype = 'video'
		elif mediatype == 'text':
			if subtype == 'plain':
				chtype = 'text'
			else:
				chtype = 'html'
		elif mediatype == 'application' and \
		     subtype == 'x-shockwave-flash':
			chtype = 'RealVideo'
		elif mediatype == 'cmif_cmif':
			chtype = 'cmif'
		elif mediatype == 'cmif_socket':
			chtype = 'socket'
		elif mediatype == 'cmif_shell':
			chtype = 'shell'
		elif mediatype is None:
			chtype = 'undefined'
		else:
			chtype = 'undefined'
			prtype = mediatype
			if subtype:
				prtype = prtype+'/'+subtype
			self.warning('unrecognized media type %s' % prtype)

		# map channel type to something we can deal with
		# this should loop at most twice (RealPix->RealVideo->video)
		while not self.__validchannels.has_key(chtype):
			if chtype == 'RealVideo':
				chtype = 'video'
			elif chtype == 'RealPix':
				chtype = 'RealVideo'
			elif chtype == 'RealAudio':
				chtype = 'sound'
			elif chtype == 'RealText':
				chtype = 'video'
			elif chtype == 'html':
				chtype = 'text'

## 		if attributes['encoding'] not in ('base64', 'UTF'):
## 			self.syntax_error('bad encoding parameter')

		# create the node
		if not self.__root:
			# "can't happen"
			node = self.MakeRoot(nodetype)
		elif not self.__container:
			self.syntax_error('node not in container')
			return
		else:
			node = self.__context.newnode(nodetype)
			self.__container._addchild(node)
		if data is not None:
			node.values = data
		self.__node = node
		self.AddAttrs(node, attributes)
		node.__chantype = chtype
		node.__mediatype = mediatype, subtype
		self.__attributes = attributes
		if mimetype is not None:
			node.attrdict['mimetype'] = mimetype

	def EndNode(self):
		node = self.__node
		try:
			attributes = self.__attributes
		except AttributeError:
			# Some error occurred in the handling of the start tag.
			return
		self.__node = None
		del self.__attributes
		mediatype, subtype = node.__mediatype
		mtype = node.__chantype

		if not self.__is_ext:
			# don't warn since error message already printed
## 			encoding = attributes['encoding']
			data = string.split(string.join(self.__nodedata, ''), '\n')
			for i in range(len(data)-1, -1, -1):
				tmp = string.join(string.split(data[i]))
				if tmp:
					data[i] = tmp
				else:
					del data[i]
			self.__data.append(string.join(data, '\n'))
			nodedata = string.join(self.__data, '')
			res = self.__whitespace.match(nodedata)
			if res is not None:
				self.syntax_error('no src attribute and no content data')
			if mediatype != 'text' and mediatype[:5] != 'cmif_':
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
			region = 'unnamed region'
		node.__region = region
		ch = self.__regions.get(region)
		if ch is None:
			self.__regions[region] = ch = \
					{'minwidth': 0, 'minheight': 0,
					 'left': 0, 'top': 0,
					 'width': 0, 'height': 0,
					 'z-index': 0, 'fit': 'hidden',
					 'background-color': 'transparent'}
		width = height = 0
		if self.__width > 0 and self.__height > 0:
			# we don't have to calculate minimum sizes
			pass
		elif mtype in ('image', 'movie', 'video', 'mpeg', 'RealPix', 'RealText', 'RealVideo'):
			x, y, w, h = ch['left'], ch['top'], ch['width'], ch['height']
			# if we don't know the region size and
			# position in pixels, we need to look at the
			# media objects to figure out the size to use.
			if w > 0 and h > 0 and \
			   type(w) == type(h) == type(0) and \
			   (x == y == 0 or type(x) == type(y) == type(0)):
				# size and position is given in pixels
				pass
			elif node.attrdict.has_key('file'):
				url = self.__context.findurl(node.attrdict['file'])
				try:
					import Sizes
					width, height = Sizes.GetSize(url, mediatype, subtype)
				except:
					# want to make them at least visible...
					width = 100
					height = 100
				else:
					node.__size = width, height
		elif mtype in ('text', 'label', 'html', 'graph'):
			# want to make them at least visible...
			width = 200
			height = 100
		if ch['minwidth'] < width:
			ch['minwidth'] = width
		if ch['minheight'] < height:
			ch['minheight'] = height

		# clip-* attributes for video
		clip_begin = attributes.get('clip-begin')
		if clip_begin:
			res = clip.match(clip_begin)
			if res:
				node.attrdict['clipbegin'] = clip_begin
				if res.group('clock'):
					self.syntax_error('invalid clip-begin attribute; should be "npt=<time>"')
			else:
				self.syntax_error('invalid clip-begin attribute')
		clip_end = attributes.get('clip-end')
		if clip_end:
			res = clip.match(clip_end)
			if res:
				node.attrdict['clipend'] = clip_end
				if res.group('clock'):
					self.syntax_error('invalid clip-end attribute; should be "npt=<time>"')
			else:
				self.syntax_error('invalid clip-end attribute')

		if self.__in_a:
			# deal with hyperlink
			href, ltype, id = self.__in_a[:3]
			if id is not None and not self.__idmap.has_key(id):
				self.__idmap[id] = node.GetUID()
			anchorlist = node.__anchorlist
			id = _uniqname(map(lambda a: a[2], anchorlist), id)
			anchorlist.append((0, len(anchorlist), id, ATYPE_WHOLE, [], (0, 0)))
			self.__links.append((node.GetUID(), id, href, ltype))

	def NewContainer(self, type, attributes):
		if not self.__in_smil:
			self.syntax_error('%s not in smil' % type)
		if self.__in_layout:
			self.syntax_error('%s in layout' % type)
			return
		if not self.__root:
			node = self.MakeRoot(type)
		elif not self.__container:
			self.error('multiple elements in body', self.lineno)
			return
		else:
			node = self.__context.newnode(type)
			self.__container._addchild(node)
		self.__container = node
		node.__chanlist = {}
		self.AddAttrs(node, attributes)

	def EndContainer(self, type):
		if self.__container is None or \
		   self.__container.GetType() != type:
			# erroneous end tag; error message from xmllib
			return
		self.__container = self.__container.GetParent()

	def Recurse(self, root, *funcs):
		for func in funcs:
			func(root)
		for node in root.GetChildren():
			apply(self.Recurse, (node,) + funcs)

##	def FixRoot(self):
##		root = self.__root
##		if len(root.children) != 1 or root.attrdict or \
##		   root.__syncarcs or root.__anchorlist or \
##		   root.children[0].GetType() in leaftypes:
##			return
##		child = root.children[0]
##		# copy stuff over from child to root
##		root.type = child.type
##		root.attrdict = child.attrdict.copy()
##		root.children[:] = child.children # deletes root.children[0]
##		child.children[:] = []
##		for c in root.children:
##			c.parent = root
##		root.__syncarcs = child.__syncarcs
##		root.values = child.values
##		try:
##			root.__mediatype = child.__mediatype
##			root.__region = child.__region
##		except AttributeError:
##			pass
##		try:
##			root.__size = child.__size
##		except AttributeError:
##			pass
##		try:
##			root.__chantype = child.__chantype
##		except AttributeError:
##			pass
##		root.__anchorlist = child.__anchorlist
##		root.setgensr()

	def FixSizes(self):
		# calculate minimum required size of top-level window
		if self.__width > 0 and self.__height > 0:
			# there was a root-layout tag which specified the size
			return
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
		from windowinterface import UNIT_PXL
		bg = None
		attrs = self.__root_layout
		name = None
		if attrs is not None:
			bg = attrs['background-color']
			bg = self.__convert_color(bg)
			if not self.__title:
				self.__title = attrs.get('title')
			if not self.__title:
				self.__title = attrs.get('id')
			name = attrs.get('id')
		if not self.__title:
			self.__title = layout_name
		if not name:
			name = self.__title
		self.__base_win = name
		ctx = self.__context
		layout = MMNode.MMChannel(ctx, name)
		ctx.channeldict[name] = layout
		ctx.channelnames.insert(0, name)
		ctx.channels.insert(0, layout)
		self.__layout = layout
		layout['type'] = 'layout'
		if bg is not None and \
		   bg != 'transparent' and \
		   bg != 'inherit':
			layout['bgcolor'] = bg
		elif features.compatibility == compatibility.G2:
			layout['bgcolor'] = 0,0,0
		else:
			layout['bgcolor'] = 255,255,255
		if self.__width == 0:
			self.__width = 640
		if self.__height == 0:
			self.__height = 480
		layout['winsize'] = \
			self.__width, self.__height
		layout['units'] = UNIT_PXL

	def FixBaseWindow(self):
		if self.__layout is None:
			return
		for ch in self.__context.channels:
			if ch is self.__layout:
				continue
			ch['base_window'] = self.__base_win

	def __fillchannel(self, ch, attrdict, mtype):
		from windowinterface import UNIT_PXL, UNIT_SCREEN
		attrdict = attrdict.copy() # we're going to change this...
		if attrdict.has_key('type'): del attrdict['type']
		if mtype in ('text', 'image', 'movie', 'video', 'mpeg',
			     'html', 'label', 'graph', 'layout', 'RealPix','RealText', 'RealVideo'):
			# deal with channel with window
			ch['drawbox'] = 0
			if attrdict.has_key('id'): del attrdict['id']
			title = attrdict.get('title')
			if title is not None:
				if title != ch.name:
					ch['title'] = title
				del attrdict['title']
			bg = attrdict['background-color']
			del attrdict['background-color']
			if compatibility.G2 == features.compatibility:
				ch['transparent'] = -1
				if bg != 'transparent':
					ch['bgcolor'] = bg
					ch['transparent'] = 0
				elif mtype in ('text', 'RealText'):
					ch['bgcolor'] = 255,255,255
				else:
					ch['bgcolor'] = 0,0,0
			elif compatibility.QT == features.compatibility:
				ch['transparent'] = 1
				ch['fgcolor'] = 255,255,255 
				
			elif bg == 'transparent':
				ch['transparent'] = 1
			else:
				ch['transparent'] = -1
				ch['bgcolor'] = bg
			ch['z'] = attrdict['z-index']
			del attrdict['z-index']
			x = attrdict['left']; del attrdict['left']
			y = attrdict['top']; del attrdict['top']
			w = attrdict['width']; del attrdict['width']
			h = attrdict['height']; del attrdict['height']
			fit = attrdict['fit']; del attrdict['fit']
			if fit == 'hidden':
				ch['scale'] = 1
			elif fit == 'meet':
				ch['scale'] = 0
			elif fit == 'slice':
				ch['scale'] = -1
			ch['center'] = 0
			# other fit options not implemented

			# check types of x,y,w,h: if all the
			# same, set units appropriately, else
			# convert all to relative (float).  if
			# there was a root-layout, and it
			# contained sizes, convert relative
			# sizes to absolute sizes first.
			if type(x) is type(0.0) and self.__root_width:
				x = int(x * self.__root_width + .5)
			if type(w) is type(0.0) and self.__root_width:
				w = int(w * self.__root_width + .5)
			if type(y) is type(0.0) and self.__root_height:
				y = int(y * self.__root_height + .5)
			if type(h) is type(0.0) and self.__root_height:
				h = int(h * self.__root_height + .5)
			thetype = None # type of 1st elem != 0
			broken = 0
			for val in x, y, w, h:
				if val == 0:
					continue
				if thetype is None:
					thetype = type(val)
					continue
				elif type(val) is thetype:
					continue
				broken = 1
				break
			else:
				# all the same type or 0
				if thetype is type(0):
					units = UNIT_PXL
				else:
					units = UNIT_SCREEN
				ch['units'] = units
				if w == 0 and self.__width != 0:
					if units == UNIT_PXL:
						w = self.__width - x
					else:
						w = 1.0 - x
				if h == 0 and self.__height != 0:
					if units == UNIT_PXL:
						h = self.__height - y
					else:
						h = 1.0 - y
			if broken:
				# we only get here if there
				# are multiple values != 0 of
				# different types
				# not all the same units, convert
				# everything to relative sizes
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
				ch['units'] = UNIT_SCREEN
			ch['base_winoff'] = x, y, w, h
		# keep all attributes that we didn't use
		for attr, val in attrdict.items():
			if attr not in ('minwidth', 'minheight',
					'skip-content') and \
			   not self.attributes['region'].has_key(attr):
				ch[attr] = parseattrval(attr, val, self.__context)

	def MakeChannels(self):
		ctx = self.__context
		if self.__layout is None:
			self.CreateLayout()
		for region, attrdict in self.__regions.items():
			chtype = attrdict.get('type')
			if chtype is None or not ChannelMap.channelmap.has_key(chtype):
				continue
			name = attrdict.get('id')
			if ctx.channeldict.has_key(name):
				name = name + ' %d'
				i = 0
				while ctx.channeldict.has_key(name % i):
					i = i + 1
				name = name % i
			ch = MMNode.MMChannel(ctx, name)
			ctx.channeldict[name] = ch
			ctx.channelnames.append(name)
			ctx.channels.append(ch)
			ch['type'] = chtype
			if not self.__region2channel.has_key(region):
				self.__region2channel[region] = []
			self.__region2channel[region].append(ch)
			self.__fillchannel(ch, attrdict, chtype)
			
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
		attrdict = self.__regions.get(region, {})
		mtype = node.__chantype
		del node.__chantype
		if mtype == 'undefined':
			return
		ctx = self.__context
		# find a channel of the right type that represents
		# this node's region
		name = None
		for ch in self.__region2channel.get(region, []):
			if ch['type'] == mtype:
				# found existing channel of correct type
				name = ch.name
				# check whether channel can be used
				# we can only use a channel if it isn't used
				# by another node parallel to this one
				par = node.GetParent()
				while par is not None:
					if par.__chanlist.has_key(name):
						if par.GetType() == 'par':
							# conflict
							name = None
							break
						else:
							# no conflict
							break
					par = par.GetParent()
				if name is not None:
					break
		# either we use name or name is None and we have to
		# create a new channel
		if not name:
			name = attrdict.get('id', region)
			if ctx.channeldict.has_key(name):
				name = name + ' %d'
				i = 0
				while ctx.channeldict.has_key(name % i):
					i = i + 1
				name = name % i
		ch = ctx.channeldict.get(name)
		if ch is None:
			# there is no channel of the right name and type
			ch = MMNode.MMChannel(ctx, name)
			if region != '<unnamed>':
				if not self.__region2channel.has_key(region):
					self.__region2channel[region] = []
				self.__region2channel[region].append(ch)
			ctx.channeldict[name] = ch
			ctx.channelnames.append(name)
			ctx.channels.append(ch)
			ch['type'] = mtype
			if mtype in ('image', 'movie', 'video', 'mpeg',
				     'text', 'label', 'html', 'graph', 'RealPix', 'RealText', 'RealVideo'):
				if not self.__regions.has_key(region):
					self.warning('no region %s in layout' %
						     region, self.lineno)
					self.__in_layout = LAYOUT_SMIL
					self.start_region({'id': region})
					self.__in_layout = LAYOUT_NONE
				# we're going to change this locally...
				attrdict = self.__regions[region]
				self.__fillchannel(ch, attrdict, mtype)
		node.attrdict['channel'] = name
		par = node.GetParent()
		while par is not None:
			par.__chanlist[name] = 0
			par = par.GetParent()
		if compatibility.G2 == features.compatibility:
			if mtype == 'RealPix':
				self.__realpixnodes.append(node)

	def FixLayouts(self):
		if not self.__layouts:
			return
		layouts = self.__context.layouts
		for layout, regions in self.__layouts.items():
			channellist = []
			for region in regions:
				channels = self.__region2channel.get(region)
				if channels is None:
					continue
				channellist = channellist + channels
			layouts[layout] = channellist

	def FixLinks(self):
		hlinks = self.__context.hyperlinks
		for node, aid, url, ltype in self.__links:
			# node is either a node UID (int in string
			# form) or a node id (anything else)
			try:
				string.atoi(node)
			except string.atoi_error:
				if not self.__nodemap.has_key(node):
					self.warning('unknown node id %s' % node)
					continue
				node = self.__nodemap[node].GetUID()
			if type(aid) is type(()):
				aid, atype, args = aid
			src = node, aid
			href, tag = MMurl.splittag(url)
			if not href:
				if self.__anchormap.has_key(tag):
					dst = self.__anchormap[tag]
				else:
					if self.__nodemap.has_key(tag):
						dst = self.__nodemap[tag]
						dst = self.__destanchor(dst)
					else:
						self.warning("unknown node id `%s'" % tag)
						continue
				hlinks.addlink((src, dst, DIR_1TO2, ltype))
			else:
				hlinks.addlink((src, url, DIR_1TO2, ltype))

	def CleanChanList(self, node):
		if node.GetType() not in leaftypes:
			del node.__chanlist

	def FixAnchors(self, node):
		anchorlist = node.__anchorlist
		if anchorlist:
			alist = []
			anchorlist.sort()
			for a in anchorlist:
				alist.append(a[2:])
			node.attrdict['anchorlist'] = alist
		del node.__anchorlist
		
	def parseQTAttributeOnSmilElement(self, attributes):
		for key, val in attributes.items():
			if key == 'time-slider':
				internalval = self.parseEnumValue(val, {'false':0,'true':1},key, 'qttimeslider')
				self.__context.attributes['qttimeslider'] = internalval
				del attributes[key]
			elif key == 'autoplay':
				internalval = self.parseEnumValue(val, {'false':0,'true':1}, key, 'autoplay')
				self.__context.attributes['autoplay'] = internalval
				del attributes[key]
			elif key == 'chapter-mode':
				internalval = self.parseEnumValue(val, {'all':0,'clip':1}, key, 'qtchaptermode')
				self.__context.attributes['qtchaptermode'] = internalval
				del attributes[key]
			elif key == 'next':
				if val is not None:
					val = MMurl.basejoin(self.__base, val)
					val = self.__context.findurl(val)
					self.__context.attributes['qtnext'] = val
				del attributes[key]
			elif key == 'immediate-instantiation':
				internalval = self.parseEnumValue(val, {'false':0,'true':1}, key, 'immediateinstantiation')
				self.__context.attributes['immediateinstantiation'] = internalval
				del attributes[key]
		
	# methods for start and end tags

	# smil contains everything
	def start_smil(self, attributes):
		for key, val in attributes.items():
			if key[:len(GRiNSns)+1] == GRiNSns + ' ':
				del attributes[key]
				attributes[key[len(GRiNSns)+1:]] = val
			if key[:len(QTns)+1] == QTns + ' ':
				del attributes[key]
				attributes[key[len(QTns)+1:]] = val
		if features.compatibility == features.QT:
			self.parseQTAttributeOnSmilElement(attributes)
		id = attributes.get('id')
		if id is not None:
			res = xmllib.tagfind.match(id)
			if res is None or res.end(0) != len(id):
				self.syntax_error("illegal ID value `%s'" % id)
			if self.__ids.has_key(id):
				self.syntax_error('non-unique id %s' % id)
			self.__ids[id] = 0
		if self.__seen_smil:
			self.error('more than 1 smil tag', self.lineno)
		self.__seen_smil = 1
		self.__in_smil = 1
		# fill in defaults for seq
		attributes['repeat'] = '1'
		self.NewContainer('seq', attributes)

	def end_smil(self):
		from realnode import SlideShow
		self.__in_smil = 0
		if not self.__root:
			self.error('empty document', self.lineno)
##		self.FixRoot()
		self.FixSizes()
		self.MakeChannels()
		self.Recurse(self.__root, self.FixChannel, self.FixSyncArcs)
		self.Recurse(self.__root, self.CleanChanList)
		self.FixLayouts()
		self.FixBaseWindow()
		self.FixLinks()
		self.Recurse(self.__root, self.FixAnchors)
		for node in self.__realpixnodes:
			node.slideshow = SlideShow(node, self.__new_file)
		del self.__realpixnodes

	# head/body sections

	def start_head(self, attributes):
		for key, val in attributes.items():
			if key[:len(GRiNSns)+1] == GRiNSns + ' ':
				del attributes[key]
				attributes[key[len(GRiNSns)+1:]] = val
		id = attributes.get('id')
		if id is not None:
			res = xmllib.tagfind.match(id)
			if res is None or res.end(0) != len(id):
				self.syntax_error("illegal ID value `%s'" % id)
			if self.__ids.has_key(id):
				self.syntax_error('non-unique id %s' % id)
			self.__ids[id] = 0
		if not self.__in_smil:
			self.syntax_error('head not in smil')
		self.__in_head = 1

	def end_head(self):
		self.__in_head = 0
		if self.__root_layout is not None:
			self.CreateLayout()

	def start_body(self, attributes):
		for key, val in attributes.items():
			if key[:len(GRiNSns)+1] == GRiNSns + ' ':
				del attributes[key]
				attributes[key[len(GRiNSns)+1:]] = val
		id = attributes.get('id')
		if id is not None:
			res = xmllib.tagfind.match(id)
			if res is None or res.end(0) != len(id):
				self.syntax_error("illegal ID value `%s'" % id)
			if self.__ids.has_key(id):
				self.syntax_error('non-unique id %s' % id)
			self.__ids[id] = 0
		if not self.__in_smil:
			self.syntax_error('body not in smil')
		if self.__seen_body:
			self.error('multiple body tags', self.lineno)
		self.__seen_body = 1
		self.__in_body = 1

	def end_body(self):
		self.__in_body = 0

	def start_meta(self, attributes):
		for key, val in attributes.items():
			if key[:len(GRiNSns)+1] == GRiNSns + ' ':
				del attributes[key]
				attributes[key[len(GRiNSns)+1:]] = val
		id = attributes.get('id')
		if id is not None:
			res = xmllib.tagfind.match(id)
			if res is None or res.end(0) != len(id):
				self.syntax_error("illegal ID value `%s'" % id)
			if self.__ids.has_key(id):
				self.syntax_error('non-unique id %s' % id)
			self.__ids[id] = 0
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
			name = string.lower(attributes['name'])
		else:
			self.syntax_error('required attribute name missing in meta element')
			return
		if attributes.has_key('content'):
			content = attributes['content']
		else:
			self.syntax_error('required attribute content missing in meta element')
			return
		if name == 'title':
			# make sure __title cannot be a SMIL region id
			self.__context.settitle(content)
##			if content[:1] == content[-1:] == ' ':
##				self.__title = content
##			else:
##				self.__title = ' %s ' % content
		elif name == 'base':
			self.__context.setbaseurl(content)
##			self.__base = content
		elif name in ('pics-label', 'PICS-label'):
			pass
		elif name[:9] == 'template_':
			# We use these meta names for storing information such as snapshot
			# and description in templates. Don't import them.
			pass
		elif name == 'project_links':
			# space-separated list of external anchors
			self.__context.externalanchors = string.split(content)
		elif name == 'generator':
			if self.__check_compatibility:
				import DefCompatibilityCheck, windowinterface, version
				if not DefCompatibilityCheck.isCompatibleVersion(content):
					if windowinterface.GetOKCancel('This document was created by '+content+'\n'+'GRiNS '+version.version+' may be able to read the document, but some features may be lost\n\nDo you wish to continue?',parent=None):
						raise UserCancel
		else:
			if self.__warnmeta:
				self.warning('unrecognized meta property', self.lineno)
			# XXXX <meta> document attributes are always stored as strings, in stead
			# of passing through the Attrdefs mechanism. Too much work to fix, for now.
			self.__context.attributes[name] = content

	def end_meta(self):
		self.__in_meta = 0

	# layout section

	def start_layout(self, attributes):
		for key, val in attributes.items():
			if key[:len(GRiNSns)+1] == GRiNSns + ' ':
				del attributes[key]
				attributes[key[len(GRiNSns)+1:]] = val
		id = attributes.get('id')
		if id is not None:
			res = xmllib.tagfind.match(id)
			if res is None or res.end(0) != len(id):
				self.syntax_error("illegal ID value `%s'" % id)
			if self.__ids.has_key(id):
				self.syntax_error('non-unique id %s' % id)
			self.__ids[id] = 0
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
			self.setliteral()

	def end_layout(self):
		self.__in_layout = LAYOUT_NONE

	def start_region(self, attributes):
		if not self.__in_layout:
			self.syntax_error('region not in layout')
			return
		if self.__in_layout != LAYOUT_SMIL:
			# ignore outside of smil-basic-layout
			return

		id = None
		attrdict = {'left': 0,
			    'top': 0,
			    'z-index': 0,
			    'width': 0,
			    'height': 0,
			    'minwidth': 0,
			    'minheight': 0,}

		for attr, val in attributes.items():
			if attr[:len(GRiNSns)+1] == GRiNSns + ' ':
				attr = attr[len(GRiNSns)+1:]
			if attr == 'id':
				attrdict[attr] = id = val
				res = xmllib.tagfind.match(id)
				if res is None or res.end(0) != len(id):
					self.syntax_error("illegal ID value `%s'" % id)
				if self.__ids.has_key(id):
					self.syntax_error('non-unique id %s' % id)
				self.__ids[id] = 0
				self.__regions[id] = attrdict
			elif attr in ('left', 'top', 'width', 'height'):
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
			elif attr == 'z-index':
				try:
					val = string.atoi(val)
				except string.atoi_error:
					self.syntax_error('invalid z-index value')
					val = 0
				if val < 0:
					self.syntax_error('region with negative z-index')
					val = 0
				attrdict['z-index'] = val
			elif attr == 'fit':
				if val not in ('meet', 'slice', 'fill',
					       'hidden', 'scroll'):
					self.syntax_error('illegal fit attribute')
				elif val in ('fill', 'scroll'):
					self.warning('fit="%s" value not implemented' % val, self.lineno)
				attrdict['fit'] = val
			elif attr == 'background-color':
				val = self.__convert_color(val)
				if val is not None:
					attrdict['background-color'] = val
			elif attr == 'type':
				# map channel type to something we can deal with
				# this should loop at most twice (RealPix->RealVideo->video)
				while not self.__validchannels.has_key(val):
					if val == 'RealVideo':
						val = 'video'
					elif val == 'RealPix':
						val = 'RealVideo'
					elif val == 'RealAudio':
						val = 'sound'
					elif val == 'RealText':
						val = 'video'
					elif val == 'html':
						val = 'text'
				attrdict[attr] = val
			else:
				# catch all
				attrdict[attr] = val

		if id is None:
			self.syntax_error('region without id attribute')

	def end_region(self):
		pass

	def start_root_layout(self, attributes):
		for key, val in attributes.items():
			if key[:len(GRiNSns)+1] == GRiNSns + ' ':
				del attributes[key]
				attributes[key[len(GRiNSns)+1:]] = val
		id = attributes.get('id')
		if id is not None:
			res = xmllib.tagfind.match(id)
			if res is None or res.end(0) != len(id):
				self.syntax_error("illegal ID value `%s'" % id)
			if self.__ids.has_key(id):
				self.syntax_error('non-unique id %s' % id)
			self.__ids[id] = 0
		self.__root_layout = attributes
		width = attributes['width']
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
				self.__root_width = self.__width = width
		height = attributes['height']
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
				self.__root_height = self.__height = height

	def end_root_layout(self):
		pass

	def start_user_attributes(self, attributes):
		for key, val in attributes.items():
			if key[:len(GRiNSns)+1] == GRiNSns + ' ':
				del attributes[key]
				attributes[key[len(GRiNSns)+1:]] = val
		id = attributes.get('id')
		if id is not None:
			res = xmllib.tagfind.match(id)
			if res is None or res.end(0) != len(id):
				self.syntax_error("illegal ID value `%s'" % id)
			if self.__ids.has_key(id):
				self.syntax_error('non-unique id %s' % id)
			self.__ids[id] = 0

	def end_user_attributes(self):
		self.__context.addusergroups(self.__u_groups.items())

	def start_u_group(self, attributes):
		for key, val in attributes.items():
			if key[:len(GRiNSns)+1] == GRiNSns + ' ':
				del attributes[key]
				attributes[key[len(GRiNSns)+1:]] = val
		id = attributes.get('id')
		if id is not None:
			res = xmllib.tagfind.match(id)
			if res is None or res.end(0) != len(id):
				self.syntax_error("illegal ID value `%s'" % id)
			if self.__ids.has_key(id):
				self.syntax_error('non-unique id %s' % id)
			self.__ids[id] = 0
		title = attributes.get('title', '')
		u_state = attributes['u-state']
		override = attributes['override']
		self.__u_groups[id] = title, u_state == 'RENDERED', override == 'allowed'

	def end_u_group(self):
		pass

	def start_layouts(self, attributes):
		for key, val in attributes.items():
			if key[:len(GRiNSns)+1] == GRiNSns + ' ':
				del attributes[key]
				attributes[key[len(GRiNSns)+1:]] = val
		id = attributes.get('id')
		if id is not None:
			res = xmllib.tagfind.match(id)
			if res is None or res.end(0) != len(id):
				self.syntax_error("illegal ID value `%s'" % id)
			if self.__ids.has_key(id):
				self.syntax_error('non-unique id %s' % id)
			self.__ids[id] = 0

	def end_layouts(self):
		pass

	def start_Glayout(self, attributes):
		for key, val in attributes.items():
			if key[:len(GRiNSns)+1] == GRiNSns + ' ':
				del attributes[key]
				attributes[key[len(GRiNSns)+1:]] = val
		id = attributes.get('id')
		if id is None:
			self.syntax_error('GRiNS layout without id attribute')
			return
		res = xmllib.tagfind.match(id)
		if res is None or res.end(0) != len(id):
			self.syntax_error("illegal ID value `%s'" % id)
		if self.__ids.has_key(id):
			self.syntax_error('non-unique id %s' % id)
		self.__ids[id] = 0
		regions = attributes.get('regions')
		if regions is None:
			self.syntax_error('required attribute regions missing in GRiNS layout element')
			return
		self.__layouts[id] = string.split(regions)

	def end_Glayout(self):
		pass
		
	# container nodes

	def start_par(self, attributes):
		for key, val in attributes.items():
			if key[:len(GRiNSns)+1] == GRiNSns + ' ':
				del attributes[key]
				attributes[key[len(GRiNSns)+1:]] = val
		id = attributes.get('id')
		if id is not None:
			res = xmllib.tagfind.match(id)
			if res is None or res.end(0) != len(id):
				self.syntax_error("illegal ID value `%s'" % id)
			if self.__ids.has_key(id):
				self.syntax_error('non-unique id %s' % id)
			self.__ids[id] = 0
		# XXXX we ignore sync for now
		self.NewContainer('par', attributes)
		if not self.__container:
			return
		self.__container.__endsync = attributes.get('endsync')
## 		if self.__container.__endsync is not None and \
## 		   self.__container.attrdict.has_key('duration'):
## 			self.warning('ignoring dur attribute', self.lineno)
## 			del self.__container.attrdict['duration']

	def end_par(self):
		node = self.__container
		self.EndContainer('par')
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
			if self.__nodemap.has_key(id):
				child = self.__nodemap[id]
				if child in node.GetChildren():
					node.attrdict['terminator'] = child.GetRawAttr('name')
					return
			# id not found among the children
			self.warning('unknown idref in endsync attribute', self.lineno)

	def start_seq(self, attributes):
		for key, val in attributes.items():
			if key[:len(GRiNSns)+1] == GRiNSns + ' ':
				del attributes[key]
				attributes[key[len(GRiNSns)+1:]] = val
		id = attributes.get('id')
		if id is not None:
			res = xmllib.tagfind.match(id)
			if res is None or res.end(0) != len(id):
				self.syntax_error("illegal ID value `%s'" % id)
			if self.__ids.has_key(id):
				self.syntax_error('non-unique id %s' % id)
			self.__ids[id] = 0
		self.NewContainer('seq', attributes)

	def end_seq(self):
		self.EndContainer('seq')

	def start_choice(self, attributes):
		for key, val in attributes.items():
			if key[:len(GRiNSns)+1] == GRiNSns + ' ':
				del attributes[key]
				attributes[key[len(GRiNSns)+1:]] = val
		id = attributes.get('id')
		if id is not None:
			res = xmllib.tagfind.match(id)
			if res is None or res.end(0) != len(id):
				self.syntax_error("illegal ID value `%s'" % id)
			if self.__ids.has_key(id):
				self.syntax_error('non-unique id %s' % id)
			self.__ids[id] = 0
		self.NewContainer('bag', attributes)
		self.__container.__choice_index = attributes.get('choice-index')
		if self.__container.__choice_index is None:
			self.__container.__choice_index = attributes.get('bag-index')

	def end_choice(self):
		node = self.__container
		self.EndContainer('bag')
		choice_index = node.__choice_index
		del node.__choice_index
		if choice_index is None:
			return
		res = idref.match(choice_index)
		if res is None:
			self.syntax_error('bad choice-index attribute')
			return
		id = res.group('id')
		if self.__nodemap.has_key(id):
			child = self.__nodemap[id]
			if child in node.GetChildren():
				node.attrdict['bag_index'] = child.GetRawAttr('name')
				return
		# id not found among the children
		self.warning('unknown idref in choice-index attribute', self.lineno)

	def start_switch(self, attributes):
		for key, val in attributes.items():
			if key[:len(GRiNSns)+1] == GRiNSns + ' ':
				del attributes[key]
				attributes[key[len(GRiNSns)+1:]] = val
		id = attributes.get('id')
		if id is not None:
			res = xmllib.tagfind.match(id)
			if res is None or res.end(0) != len(id):
				self.syntax_error("illegal ID value `%s'" % id)
			if self.__ids.has_key(id):
				self.syntax_error('non-unique id %s' % id)
			self.__ids[id] = 0
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
			self.EndContainer('alt')

	# media items

	def start_ref(self, attributes):
		self.NewNode(None, attributes)

	def end_ref(self):
		self.EndNode()

	def start_text(self, attributes):
		self.NewNode('text', attributes)

	def end_text(self):
		self.EndNode()

	def start_audio(self, attributes):
		self.NewNode('audio', attributes)

	def end_audio(self):
		self.EndNode()

	def start_img(self, attributes):
		self.NewNode('image', attributes)

	def end_img(self):
		self.EndNode()

	def start_video(self, attributes):
		self.NewNode('video', attributes)

	def end_video(self):
		self.EndNode()

	def start_animation(self, attributes):
		self.NewNode('animation', attributes)

	def end_animation(self):
		self.EndNode()

	def start_textstream(self, attributes):
		self.NewNode('textstream', attributes)

	def end_textstream(self):
		self.EndNode()

	def start_cmif(self, attributes):
		self.NewNode('cmif_cmif', attributes)

	def end_cmif(self):
		self.EndNode()

	def start_socket(self, attributes):
		self.NewNode('cmif_socket', attributes)

	def end_socket(self):
		self.EndNode()

	def start_shell(self, attributes):
		self.NewNode('cmif_shell', attributes)

	def end_shell(self):
		self.EndNode()

	# linking

	def start_a(self, attributes):
		for key, val in attributes.items():
			if key[:len(GRiNSns)+1] == GRiNSns + ' ':
				del attributes[key]
				attributes[key[len(GRiNSns)+1:]] = val
		id = attributes.get('id')
		if id is not None:
			res = xmllib.tagfind.match(id)
			if res is None or res.end(0) != len(id):
				self.syntax_error("illegal ID value `%s'" % id)
			if self.__ids.has_key(id):
				self.syntax_error('non-unique id %s' % id)
			self.__ids[id] = 0
		if self.__in_a:
			self.syntax_error('nested a elements')
		href = attributes.get('href')
		if not href:
			self.syntax_error('anchor with empty HREF or without HREF')
			return
		if href[:1] != '#':
			# external link
			href = string.join(string.split(href, ' '), '%20')
			href = MMurl.basejoin(self.__base, attributes['href'])
			if href not in self.__context.externalanchors:
				self.__context.externalanchors.append(href)
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
		self.__in_a = href, ltype, id, self.__in_a

	def end_a(self):
		if self.__in_a is None:
			# </a> without <a>
			# error message will be taken care of by XMLparser.
			return
		self.__in_a = self.__in_a[3]

	def start_anchor(self, attributes):
		for key, val in attributes.items():
			if key[:len(GRiNSns)+1] == GRiNSns + ' ':
				del attributes[key]
				attributes[key[len(GRiNSns)+1:]] = val
		id = attributes.get('id')
		if id is not None:
			res = xmllib.tagfind.match(id)
			if res is None or res.end(0) != len(id):
				self.syntax_error("illegal ID value `%s'" % id)
			if self.__ids.has_key(id):
				self.syntax_error('non-unique id %s' % id)
			self.__ids[id] = 0
		if self.__node is None:
			self.syntax_error('anchor not in media object')
			return
		if id is not None:
			self.__idmap[id] = self.__node.GetUID()
		href = attributes.get('href') # None is dest only anchor
## 		if href is None:
## 			#XXXX is this a document error?
## 			self.warning('required attribute href missing', self.lineno)
		if href is not None and href[:1] != '#':
			href = MMurl.basejoin(self.__base, href)
			href = string.join(string.split(href, ' '), '%20')
			if href not in self.__context.externalanchors:
				self.__context.externalanchors.append(href)
		uid = self.__node.GetUID()
		nname = self.__node.GetRawAttrDef('name', None)
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
			x0, y0, x1, y1 = res.group('x0', 'y0', 'x1', 'y1')
			if (x0[-1]=='%') != (x1[-1]=='%') or\
			   (y0[-1]=='%') != (y1[-1]=='%'):
				self.warning('Cannot mix pixels and percentages in anchor',
					self.lineno)
			if x0[-1] == '%':
				x0 = string.atoi(x0[:-1]) / 100.0
			else:
				x0 = string.atoi(x0)
			if y0[-1] == '%':
				y0 = string.atoi(y0[:-1]) / 100.0
			else:
				y0 = string.atoi(y0)
			if x1[-1] == '%':
				x1 = string.atoi(x1[:-1]) / 100.0
			else:
				x1 = string.atoi(x1)
			if y1[-1] == '%':
				y1 = string.atoi(y1[:-1]) / 100.0
			else:
				y1 = string.atoi(y1)
			if x1 <= x0 or y1 <= y0:
				self.warning('Anchor coordinates incorrect. XYWH-style?.',
					self.lineno)
##					x1 = x1 + x0
##					y1 = y1 + y0
			# x,y,w,h are now floating point if they were
			# percentages, otherwise they are ints.
			aargs = [x0, y0, x1-x0, y1-y0]
		begin = attributes.get('begin')
		if begin is not None:
			try:
				begin = self.__parsecounter(begin, 0)
			except error, msg:
				self.syntax_error(msg)
				begin = None
			else:
				atype = ATYPE_NORMAL
		end = attributes.get('end')
		if end is not None:
			try:
				end = self.__parsecounter(end, 0)
			except error, msg:
				self.syntax_error(msg)
				end = None
			else:
				atype = ATYPE_NORMAL
		# extension: accept z-index attribute
		z = attributes.get('z-index', '0')
		try:
			z = string.atoi(z)
		except string.atoi_error:
			self.syntax_error('invalid z-index value')
			z = 0
		if z < 0:
			self.syntax_error('anchor with negative z-index')
			z = 0
		anchorlist = self.__node.__anchorlist
		aid = _uniqname(map(lambda a: a[2], anchorlist), None)
		if attributes.has_key('fragment-id'):
			aid = attributes['fragment-id']
			atype = ATYPE_NORMAL
		elif nname is not None and id is not None and \
		     id[:len(nname)+1] == nname + '-':
			# undo CMIF encoding of anchor ID
			aid = id[len(nname)+1:]
		elif id is not None:
			aid = id
		if id is not None:
			self.__anchormap[id] = (uid, aid)
		anchorlist.append((z, len(anchorlist), aid, atype, aargs, (begin or 0, end or 0)))
		if href is not None:
			self.__links.append((uid, (aid, atype, aargs),
					     href, ltype))

	def end_anchor(self):
		pass

	# other callbacks

	__whitespace = re.compile(xmllib._opS + '$')
	def handle_data(self, data):
		if self.__node is None or self.__is_ext:
			if self.__in_layout != LAYOUT_UNKNOWN:
				res = self.__whitespace.match(data)
				if not res:
					self.syntax_error('non-white space content')
			return
		self.__nodedata.append(data)

	__doctype = re.compile('SYSTEM' + xmllib._S + '(?P<dtd>[^ \t\r\n]+)' +
			       xmllib._opS + '$')
	def handle_doctype(self, tag, pubid, syslit, data):
		if tag != 'smil':
			self.error('not a SMIL document', self.lineno)
		if pubid != SMILpubid or syslit != SMILdtd or data:
			self.syntax_error('invalid DOCTYPE')

	def handle_proc(self, name, data):
		self.warning('ignoring processing instruction %s' % name, self.lineno)

	# Example -- handle cdata, could be overridden
	def handle_cdata(self, cdata):
		if self.__node is None or self.__is_ext:
			if self.__in_layout != LAYOUT_UNKNOWN:
				self.warning('ignoring CDATA', self.lineno)
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

	# catch all

	def unknown_starttag(self, tag, attrs):
		self.warning('ignoring unknown start tag %s' % tag, self.lineno)

	def unknown_endtag(self, tag):
		self.warning('ignoring unknown end tag %s' % (tag or ''), self.lineno)

	def unknown_charref(self, ref):
		self.warning('ignoring unknown char ref %s' % ref, self.lineno)

	def unknown_entityref(self, ref):
		self.warning('ignoring unknown entity ref %s' % ref, self.lineno)

	# non-fatal syntax errors

	def syntax_error(self, msg):
		msg = 'warning: syntax error on line %d: %s' % (self.lineno, msg)
		if self.__printfunc is not None:
			self.__printdata.append(msg)
		else:
			print msg

	def warning(self, message, lineno = None):
		if lineno is None:
			msg = 'warning: %s' % message
		else:
			msg = 'warning: %s on line %d' % (message, lineno)
		if self.__printfunc is not None:
			self.__printdata.append(msg)
		else:
			print msg

	def error(self, message, lineno = None):
		if self.__printfunc is None and self.__printdata:
			msg = string.join(self.__printdata, '\n') + '\n'
		else:
			msg = ''
		if lineno is None:
			message = 'error: %s' % message
		else:
			message = 'error, line %d: %s' % (lineno, message)
		raise MSyntaxError, msg + message

	def fatalerror(self):
		type, value, traceback = sys.exc_info()
		if self.__printfunc is not None:
			msg = 'Fatal error while parsing at line %d: %s' % (self.lineno, str(value))
			if self.__printdata:
				data = string.join(self.__printdata, '\n')
				# first 30 lines should be enough
				data = string.split(data, '\n')
				if len(data) > 30:
					data = data[:30]
					data.append('. . .')
			else:
				data = []
			data.insert(0, msg)
			self.__printfunc(string.join(data, '\n'))
			self.__printdata = []
		raise MSyntaxError # re-raise
	
	def goahead(self, end):
		try:
			xmllib.XMLParser.goahead(self, end)
		# we should catch only parsing error
		# there is an other type of except --> Abort
		# this last except haven't be catched in this module
		except (error, RuntimeError, MSyntaxError):
			self.fatalerror()
			
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
		elif res.group('clock'):
			val = res.group('clock')
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

	def __destanchor(self, node):
		anchorlist = node.__anchorlist
		for a in anchorlist:
			if a[3] == ATYPE_DEST:
				break
		else:
			a = 0, len(anchorlist), '0', ATYPE_DEST, [], (0, 0)
			anchorlist.append(a)
		return node.GetUID(), a[2]

	def __convert_color(self, val):
		val = string.lower(val)
		if colors.has_key(val):
			return colors[val]
		if val in ('transparent', 'inherit'):
			return val
		res = color.match(val)
		if res is None:
			self.syntax_error('bad color specification')
			return 'transparent'
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
	def finish_starttag(self, tagname, attrdict, method):
		if len(self.stack) > 1:
			ptag = self.stack[-2][2]
			if tagname not in self.entities.get(ptag, ()):
				self.syntax_error('%s element not allowed inside %s' % (self.stack[-1][0], self.stack[-2][0]))
		elif tagname != 'smil':
			self.syntax_error('outermost element must be "smil"')
		xmllib.XMLParser.finish_starttag(self, tagname, attrdict, method)
		
class SMILMetaCollector(xmllib.XMLParser):
	"""Collect the meta attributes from a smil file"""
	
	def __init__(self, file=None):
		self.meta_data = {}
		self.elements = {
			'meta': (self.start_meta, None)
		}
		self.__file = file or '<unknown file>'
		xmllib.XMLParser.__init__(self)

	def start_meta(self, attributes):
		name = attributes.get('name')
		content = attributes.get('content')
		if name and content:
			self.meta_data[name] = content
			
	def syntax_error(self, msg):
		print 'warning: syntax error on line %d: %s' % (self.lineno, msg)
		
def ReadMetaData(file):
	p = SMILMetaCollector(file)
	fp = open(file)
	p.feed(fp.read())
	p.close()
	return p.meta_data
	
def ReadFile(url, printfunc = None, new_file = 0, check_compatibility = 0):
	if os.name == 'mac':
		import splash
		splash.splash('loaddoc')	# Show "loading document" splash screen
	rv = ReadFileContext(url, MMNode.MMNodeContext(MMNode.MMNode), printfunc, new_file, check_compatibility)
	if os.name == 'mac':
		splash.splash('initdoc')	# and "Initializing document" (to be removed in mainloop)
	return rv

def ReadFileContext(url, context, printfunc = None, new_file = 0, check_compatibility = 0):
	p = SMILParser(context, printfunc, new_file, check_compatibility)
	u = MMurl.urlopen(url)
	if not new_file:
		baseurl = u.geturl()
		i = string.rfind(baseurl, '/')
		if i >= 0:
			baseurl = baseurl[:i+1]	# keep the slash
		else:
			baseurl = None
		context.setbaseurl(baseurl)
	data = u.read()
	u.close()
	# convert Windows CRLF sequences to LF
	data = string.join(string.split(data, '\r\n'), '\n')
	# then convert Macintosh CR to LF
	data = string.join(string.split(data, '\r'), '\n')
	p.feed(data)
	p.close()
	root = p.GetRoot()
	root.source = data
	return root

def ReadString(string, name, printfunc = None, check_compatibility = 0):
	return ReadStringContext(string, name,
				 MMNode.MMNodeContext(MMNode.MMNode),
				 printfunc, check_compatibility)

def ReadStringContext(string, name, context, printfunc = None, check_compatibility = 0):
	p = SMILParser(context, printfunc, check_compatibility)
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

def GetTemporalSiblings(node):
	"""Get siblings of a node, ignoring <switch> nodes"""
	parent = node.GetParent()
	while parent and parent.GetType() == 'alt':
		parent = parent.parent
	siblings = []
	possible = parent.GetChildren()[:]
	while possible:
		this = possible[0]
		del possible[0]
		if this.GetType() == 'alt':
			possible = possible + this.GetChildren()
		siblings.append(this)
	return siblings

def parseattrval(name, string, context):
	if MMAttrdefs.getdef(name)[0][0] == 'string':
		return string
	return MMAttrdefs.parsevalue(name, string, context)


