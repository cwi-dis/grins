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
LAYOUT_EXTENDED = 2
LAYOUT_UNKNOWN = -1			# must be < 0

CASCADE = 1	# cascade regions for nodes without region attr

layout_name = ' SMIL '			# name of layout channel

_opS = xmllib._opS

#coordre = re.compile(_opS + r'(?P<x0>\d+%?)' + _opS + r',' +
#		     _opS + r'(?P<y0>\d+%?)' + _opS + r',' +
#		     _opS + r'(?P<x1>\d+%?)' + _opS + r',' +
#		     _opS + r'(?P<y1>\d+%?)' + _opS + r'$')
coordre = re.compile(_opS + r'(?P<x>\d+%?)' + _opS )
coordrewithsep = re.compile(_opS + r',' + _opS + r'(?P<x>\d+%?)' + _opS )

idref = re.compile(r'id\(' + _opS + r'(?P<id>' + xmllib._Name + r')' + _opS + r'\)')
clock_val = (_opS +
	     r'(?:(?P<use_clock>'	# full/partial clock value
	     r'(?:(?P<hours>\d+):)?'		# hours: (optional)
	     r'(?P<minutes>[0-5][0-9]):'	# minutes:
	     r'(?P<seconds>[0-5][0-9])'      	# seconds
	     r'(?P<fraction>\.\d+)?'		# .fraction (optional)
	     r')|(?P<use_timecount>' # timecount value
	     r'(?P<timecount>\d+)'		# timecount
	     r'(?P<units>\.\d+)?'		# .fraction (optional)
	     r'(?P<metric>h|min|s|ms)?)'	# metric (optional)
	     r')' + _opS)
syncbase = re.compile('id' + _opS + r'\(' + _opS + '(?P<name>' + xmllib._Name + ')' + _opS + r'\)' + # id(name)
		      _opS +
		      r'\(' + _opS + r'(?P<event>[^)]*[^) \t\r\n])' + _opS + r'\)' + # (event)
		      '$')
offsetvalue = re.compile('(?P<sign>[-+])?' + clock_val + '$')
syncbase2 = re.compile(	# ((id-ref/prev ".")? event-ref/begin/end)? (offset)?
	_opS +
	r'(?P<event>' + xmllib._Name + r')' +			# ID-ref
	_opS +
	r'(?P<offset>(?:[-+])' + clock_val + r')?$'		# offset
	)
mediamarker = re.compile(		# id-ref ".marker(" name ")"
	_opS +
	r'(?P<id>' + xmllib._Name + r')\.'			# ID-ref "."
	r'marker\(' + _opS + r'(?P<markername>' + xmllib._Name + r')' + _opS + r'\)' + _opS + r'$'	# "marker(...)"
	)
wallclock = re.compile(			# "wallclock(" wallclock-value ")"
	r'wallclock\((?P<wallclock>[^()]+)\)$'
	)
wallclockval = re.compile(
	r'(?:(?P<year>\d{4})-(?P<month>\d{2})-(?P<day>\d{2})T)?'	# date (optional)
	r'(?P<hour>\d{2}):(?P<min>\d{2})(?::(?P<sec>\d{2}(?:\.\d+)?))?'	# time (required)
	r'(?:(?P<Z>Z)|(?P<tzsign>[-+])(?P<tzhour>\d{2}):(?P<tzmin>\d{2}))?$'	# timezone (optional)
	)
##clock = re.compile(r'(?P<name>local|remote):'
##		   r'(?P<hours>\d+):'
##		   r'(?P<minutes>\d{2}):'
##		   r'(?P<seconds>\d{2})'
##		   r'(?P<fraction>\.\d+)?'
##		   r'(?:Z(?P<sign>[-+])(?P<ohours>\d{2}):(?P<omin>\d{2}))?$')
screen_size = re.compile(_opS + r'(?P<x>\d+)' + _opS + r'[xX]' +
			 _opS + r'(?P<y>\d+)' + _opS + r'$')
clip = re.compile(_opS + r'(?:'
		  # npt=...
		   '(?:(?P<npt>npt)' + _opS + r'=' + _opS + r'(?P<nptclip>[^-]*))|'
		  # smpte/smpte-25/smpte-30-drop=...
		   '(?:(?P<smpte>smpte(?:-30-drop|-25)?)' + _opS + r'=' + _opS + r'(?P<smpteclip>[^-]*))|'
		  # clock value
		   '(?P<clock>'+clock_val+')'
		   ')' + _opS + r'$')
smpte_time = re.compile(r'(?:(?:\d{2}:)?\d{2}:)?\d{2}(?P<f>\.\d{2})?' + _opS + r'$')
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
		   'rgb' + _opS + r'\(' +		# rgb(R,G,B)
			   _opS + '(?:(?P<ri>[0-9]+)' + _opS + ',' + # rgb(255,0,0)
			   _opS + '(?P<gi>[0-9]+)' + _opS + ',' +
			   _opS + '(?P<bi>[0-9]+)|' +
			   _opS + '(?P<rp>[0-9]+)' + _opS + '%' + _opS + ',' + # rgb(100%,0%,0%)
			   _opS + '(?P<gp>[0-9]+)' + _opS + '%' + _opS + ',' +
			   _opS + '(?P<bp>[0-9]+)' + _opS + '%)' + _opS + r'\))$')

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
			'userAttributes': (self.start_user_attributes, self.end_user_attributes),
			'uGroup': (self.start_u_group, self.end_u_group),
			'region': (self.start_region, self.end_region),
			'root-layout': (self.start_root_layout, self.end_root_layout),
			'viewport': (self.start_viewport, self.end_viewport),
			GRiNSns+' '+'layouts': (self.start_layouts, self.end_layouts),
			GRiNSns+' '+'layout': (self.start_Glayout, self.end_Glayout),
			'body': (self.start_body, self.end_body),
			'par': (self.start_par, self.end_par),
			'seq': (self.start_seq, self.end_seq),
			'switch': (self.start_switch, self.end_switch),
			'excl': (self.start_excl, self.end_excl),
			GRiNSns+' '+'choice': (self.start_choice, self.end_choice),
			GRiNSns+' '+'bag': (self.start_choice, self.end_choice),
			'ref': (self.start_ref, self.end_ref),
			'text': (self.start_text, self.end_text),
			'audio': (self.start_audio, self.end_audio),
			'img': (self.start_img, self.end_img),
			'video': (self.start_video, self.end_video),
			'animation': (self.start_animation, self.end_animation),
			'textstream': (self.start_textstream, self.end_textstream),
			'brush': (self.start_brush, self.end_brush),
			GRiNSns+' '+'socket': (self.start_socket, self.end_socket),
			GRiNSns+' '+'shell': (self.start_shell, self.end_shell),
			GRiNSns+' '+'cmif': (self.start_cmif, self.end_cmif),
			'a': (self.start_a, self.end_a),
			'anchor': (self.start_anchor, self.end_anchor),
			'area': (self.start_area, self.end_area),
			'animate': (self.start_animate, self.end_animate),
			'set': (self.start_set, self.end_set),
			'animateMotion': (self.start_animatemotion, self.end_animatemotion),
			'animateColor': (self.start_animatecolor, self.end_animatecolor),
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
		self.__viewport = None
		self.__tops = {}
		self.__topchans = []
		self.__container = None
		self.__node = None	# the media object we're in
		self.__regions = {}	# mapping from region id to chan. attrs
		self.__region2channel = {} # mapping from region to channels
		self.__region = None	# keep track of nested regions
		self.__regionlist = []
		self.__childregions = {}
		self.__topregion = {}
		self.__ids = {}		# collect all id's here
		self.__nodemap = {}
		self.__idmap = {}
		self.__anchormap = {}
		self.__links = []
		self.__base = ''
		self.__printfunc = printfunc
		self.__printdata = []
		self.__u_groups = {}
		self.__layouts = {}
		self.__realpixnodes = []
		self.__animatenodes = []
		self.__new_file = new_file
		self.__check_compatibility = check_compatibility
		self.__regionno = 0
		self.__defleft = 0
		self.__deftop = 0
		if new_file and type(new_file) == type(''):
			self.__base = new_file
		self.__validchannels = {'undefined':0}
		for chtype in ChannelMap.getvalidchanneltypes(context):
			self.__validchannels[chtype] = 1
		for chtype in ChannelMap.SMILBostonChanneltypes:
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
		boston = None
		beginlist = node.attrdict.get('beginlist', [])
		endlist = node.attrdict.get('endlist', [])
		if attr == 'begin':
			list = beginlist
		else:
			list = endlist
		val = string.strip(val)
		res = syncbase.match(val)
		if res is not None:
			# SMIL 1.0 begin value
			name = res.group('name')
			delay = self.__parsecounter(res.group('event'), 1)
			xnode = self.__nodemap.get(name)
			if xnode is None:
				self.warning('ignoring sync arc from %s to unknown node' % node.attrdict.get('name','<unnamed>'))
				return
			for n in GetTemporalSiblings(node):
				if n is xnode:
					break
			else:
				self.warning('out of scope sync arc from %s to %s' % (node.attrdict.get('name','<unnamed>'), xnode.attrdict.get('name','<unnamed>')))
##				return
			if delay == 'begin' or delay == 'end':
				event = delay
				delay = 0.0
			else:
				event = 'begin'
			list.append(MMNode.MMSyncArc(node, attr, srcnode=xnode,event=event,delay=delay))
		elif val == 'indefinite':
			boston = 'indefinite'
			list.append(MMNode.MMSyncArc(node, attr))
		else:
			vals = string.split(val, ';')
			if len(vals) > 1:
				boston = 'multiple %s values' % attr
			for val in vals:
				val = string.strip(val)
				try:
					offset = self.__parsecounter(val, withsign = 1)
				except error:
					pass
				else:
					list.append(MMNode.MMSyncArc(node, attr, delay=offset))
##					node.attrdict['begin'] = offset
					continue
				res = syncbase2.match(val)
				if res is not None:
					if not boston:
						boston = '%s-value' % attr
					name = res.group('event')
					if name[:5] == 'prev.':
						event = name[5:]
						name = 'prev'
					elif name[-6:] == '.begin':
						name = name[:-6]
						event = 'begin'
					elif name[-4:] == '.end':
						name = name[:-4]
						event = 'end'
					elif '.' not in name:
						event = name
						name = None
					else:
						name = string.split(name, '.')
						if len(name) != 2:
							self.syntax_error("can't resolve name")
							continue
						name, event = name
					offsetstr = res.group('offset')
					if offsetstr:
						offset = self.__parsecounter(offsetstr, withsign = 1)
					else:
						offset = 0
					if name == 'prev':
						xnode = 'prev'
					elif name is None:
						xnode = node
					else:
						xnode = self.__nodemap.get(name)
						if xnode is None:
							self.warning('ignoring sync arc from unknown node %s to %s' % (name, node.attrdict.get('name','<unnamed>')))
							continue
					list.append(MMNode.MMSyncArc(node, attr, srcnode=xnode,event=event,delay=offset))
					continue
				res = mediamarker.match(val)
				if res is not None:
					if not boston:
						boston = 'marker'
					name = res.group('id')
					xnode = self.__nodemap.get(name)
					if xnode is None:
						self.warning('ignoring sync arc from unknown node %s to %s' % (name, node.attrdict.get('name','<unnamed>')))
						continue
					marker = res.group('markername')
					list.append(MMNode.MMSyncArc(node, attr, srcnode=xnode, marker=marker, delay=0.0))
					continue
				res = wallclock.match(val)
				if res is not None:
					if not boston:
						boston = 'wallclock time'
					wc = string.strip(res.group('wallclock'))
					res = wallclockval.match(wc)
					if res is None:
						self.syntax_error('bad wallclock value')
						continue
					yr,mt,dy,hr,mn,tzhr,tzmn = map(lambda v: v and string.atoi(v), res.group('year','month','day','hour','min','tzhour','tzmin'))
					sc, tzsg = res.group('sec', 'tzsign')
					if sc is not None:
						sc = string.atof(sc)
					if res.group('Z') is not None:
						tzhr = tzmn = 0
						tzsg = '+'
					print 'wallclock',yr,mt,dy,hr,mn,sc,tzsg,tzhr,tzmn
##					list.append(MMNode.MMSyncArc(node, attr, wallclock = XXX))
					continue
				self.syntax_error('unrecognized %s value' % attr)
		if boston:
			if self.__context.attributes.get('project_boston') == 0:
				self.syntax_error('%s not compatible with SMIL 1.0' % boston)
			self.__context.attributes['project_boston'] = 1
		if beginlist:
			node.attrdict['beginlist'] = beginlist
		if endlist:
			node.attrdict['endlist'] = endlist

	def AddAttrs(self, node, attributes):
		node.__syncarcs = []
		node.__anchorlist = []
		attrdict = node.attrdict
		for attr, val in attributes.items():
			val = string.strip(val)
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
				node.__syncarcs.append((attr, val, self.lineno))
			elif attr == 'dur':
				if val == 'indefinite':
					attrdict['duration'] = -1
				else:
					try:
						attrdict['duration'] = self.__parsecounter(val)
					except error, msg:
						self.syntax_error(msg)
			elif attr == 'repeat' or attr == 'repeatCount':
				if attr == 'repeatCount':
					if self.__context.attributes.get('project_boston') == 0:
						self.syntax_error('%s attribute not compatible with SMIL 1.0' % attr)
					self.__context.attributes['project_boston'] = 1
				ignore = attr == 'repeat' and attrdict.has_key('loop')
				if val == 'indefinite':
					repeat = 0
				else:
					try:
						# fractional values are actually allowed in repeatCount
						repeat = string.atof(val)
					except string.atof_error:
						self.syntax_error('bad repeat attribute')
					else:
						if repeat <= 0:
							self.syntax_error('bad %s value' % attr)
							ignore = 1
						elif attr == 'repeat' and '.' in val:
							self.syntax_error('fractional repeat value not allowed')
							ignore = 1
				if not ignore:
					attrdict['loop'] = repeat
			elif attr == 'repeatDur':
				if self.__context.attributes.get('project_boston') == 0:
					self.syntax_error('%s attribute not compatible with SMIL 1.0' % attr)
				self.__context.attributes['project_boston'] = 1
				if val == 'indefinite':
					attrdict['repeatdur'] = -1
				else:
					try:
						attrdict['repeatdur'] = self.__parsecounter(val)
					except error, msg:
						self.syntax_error(msg)
			elif attr == 'restart':
				if self.__context.attributes.get('project_boston') == 0:
					self.syntax_error('%s attribute not compatible with SMIL 1.0' % attr)
				self.__context.attributes['project_boston'] = 1
				if val in ('always', 'whenNotActive', 'never'):
					attrdict['restart'] = val
				else:
					self.syntax_error('bad restart attribute')
			elif attr == 'system-bitrate':
				try:
					bitrate = string.atoi(val)
				except string.atoi_error:
					self.syntax_error('bad bitrate attribute')
				else:
					if not attrdict.has_key('system_bitrate'):
						attrdict['system_bitrate'] = bitrate
			elif attr == 'systemBitrate':
				if self.__context.attributes.get('project_boston') == 0:
					self.syntax_error('%s attribute not compatible with SMIL 1.0' % attr)
				self.__context.attributes['project_boston'] = 1
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
					if not attrdict.has_key('system_screen_size'):
						attrdict['system_screen_size'] = tuple(map(string.atoi, res.group('x','y')))
			elif attr == 'systemScreenSize':
				if self.__context.attributes.get('project_boston') == 0:
					self.syntax_error('%s attribute not compatible with SMIL 1.0' % attr)
				self.__context.attributes['project_boston'] = 1
				res = screen_size.match(val)
				if res is None:
					self.syntax_error('bad screen-size attribute')
				else:
					attrdict['system_screen_size'] = tuple(map(string.atoi, res.group('x','y')))
			elif attr == 'system-screen-depth':
				try:
					depth = string.atoi(val)
				except string.atoi_error:
					self.syntax_error('bad screen-depth attribute')
				else:
					if not attrdict.has_key('system_screen_depth'):
						attrdict['system_screen_depth'] = depth
			elif attr == 'systemScreenDepth':
				if self.__context.attributes.get('project_boston') == 0:
					self.syntax_error('%s attribute not compatible with SMIL 1.0' % attr)
				self.__context.attributes['project_boston'] = 1
				try:
					depth = string.atoi(val)
				except string.atoi_error:
					self.syntax_error('bad screen-depth attribute')
				else:
					attrdict['system_screen_depth'] = depth
			elif attr == 'system-captions':
				if val == 'on':
					if not attrdict.has_key('system_captions'):
						attrdict['system_captions'] = 1
				elif val == 'off':
					if not attrdict.has_key('system_captions'):
						attrdict['system_captions'] = 0
				else:
					self.syntax_error('bad system-captions attribute')
			elif attr == 'systemCaptions':
				if self.__context.attributes.get('project_boston') == 0:
					self.syntax_error('%s attribute not compatible with SMIL 1.0' % attr)
				self.__context.attributes['project_boston'] = 1
				if val == 'on':
					attrdict['system_captions'] = 1
				elif val == 'off':
					attrdict['system_captions'] = 0
				else:
					self.syntax_error('bad system-captions attribute')
##			elif attr == 'system-audiodesc':
##				if val == 'on':
##					if not attrdict.has_key('system_audiodesc'):
##						attrdict['system_audiodesc'] = 1
##				elif val == 'off':
##					if not attrdict.has_key('system_audiodesc'):
##						attrdict['system_audiodesc'] = 0
##				else:
##					self.syntax_error('bad system-audiodesc attribute')
			elif attr == 'systemAudioDesc':
				if self.__context.attributes.get('project_boston') == 0:
					self.syntax_error('%s attribute not compatible with SMIL 1.0' % attr)
				self.__context.attributes['project_boston'] = 1
				if val == 'on':
					attrdict['system_audiodesc'] = 1
				elif val == 'off':
					attrdict['system_audiodesc'] = 0
				else:
					self.syntax_error('bad system-audiodesc attribute')
			elif attr == 'system-language':
				if not attrdict.has_key('system_language'):
					attrdict['system_language'] = val
			elif attr == 'systemLanguage':
				if self.__context.attributes.get('project_boston') == 0:
					self.syntax_error('%s attribute not compatible with SMIL 1.0' % attr)
				self.__context.attributes['project_boston'] = 1
				attrdict['system_language'] = val
			elif attr == 'system-overdub-or-caption':
				if val in ('caption', 'overdub'):
					if not attrdict.has_key('system_overdub_or_caption'):
						attrdict['system_overdub_or_caption'] = val
				else:
					self.syntax_error('bad system-overdub-or-caption attribute')
			elif attr == 'systemOverdubOrSubtitle':
				if self.__context.attributes.get('project_boston') == 0:
					self.syntax_error('%s attribute not compatible with SMIL 1.0' % attr)
				self.__context.attributes['project_boston'] = 1
				if val in ('subtitle', 'overdub'):
					if val == 'subtitle':
						val = 'overdub'
					attrdict['system_overdub_or_caption'] = val
				else:
					self.syntax_error('bad systemOverdubOrSubtitle attribute')
			elif attr == 'system-required':
				if not attrdict.has_key('system_required'):
					attrdict['system_required'] = val
			elif attr == 'systemRequired':
				if self.__context.attributes.get('project_boston') == 0:
					self.syntax_error('%s attribute not compatible with SMIL 1.0' % attr)
				self.__context.attributes['project_boston'] = 1
				attrdict['system_required'] = val
			elif attr == 'uGroup':
				if self.__context.attributes.get('project_boston') == 0:
					self.syntax_error('%s attribute not compatible with SMIL 1.0' % attr)
				self.__context.attributes['project_boston'] = 1
				if self.__u_groups.has_key(val):
					attrdict['u_group'] = val
				else:
					self.syntax_error("unknown uGroup `%s'" % val)
			elif attr == 'layout':
				if self.__layouts.has_key(val):
					attrdict['layout'] = val
				else:
					self.syntax_error("unknown layout `%s'" % val)
			elif attr == 'title':
				attrdict['title'] = val
			elif attr == 'fill':
				if node.type in interiortypes or \
				   val in ('hold', 'transition'):
					if self.__context.attributes.get('project_boston') == 0:
						self.syntax_error('%s attribute not compatible with SMIL 1.0' % attr)
					self.__context.attributes['project_boston'] = 1
				if val in ('freeze', 'remove', 'hold', 'transition'):
					attrdict['fill'] = val
				else:
					self.syntax_error("bad fill attribute")
			elif attr == 'color' and node.__chantype == 'brush':
				fg = self.__convert_color(val)
				if type(fg) != type(()):
					self.syntax_error("bad color attribute")
				else:
					attrdict['fgcolor'] = fg
			elif compatibility.QT == features.compatibility and \
				self.addQTAttr(attr, val, node):
				pass
			elif attr not in smil_node_attrs:
				# catch all
				try:
					attrdict[attr] = parseattrval(attr, val, self.__context)
				except:
					pass
		# We added fill="freeze" for G2 player.  Now remove it.
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
		self.__fix_attributes(attributes)
		id = self.__checkid(attributes)
		if not self.__in_smil:
			self.syntax_error('node not in smil')
			return
		if self.__in_layout:
			self.syntax_error('node in layout')
			return
		if self.__node:
			# the warning comes later from xmllib
			self.EndNode()
		if tagname != 'brush':
			url = attributes.get('src')
		else:
			url = None
		data = None
		mtype = None
		nodetype = 'ext'
		self.__is_ext = 1
		if not url:
			url = None
		if url == '#':
			url = None
		elif url and url[:1] == '#':
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
				if mtype == 'text/plain':
					data = string.split(MMurl.unquote(res.group('data')), '\n')
					nodetype = 'imm'
					del attributes['src']
		elif tagname != 'brush':
			# remove if immediate data allowed
			self.syntax_error('no src attribute')

##			nodetype = 'imm'
##			self.__is_ext = 0
##			self.__nodedata = []
##			self.__data = []
##			if not attributes.has_key('type'):
##				self.syntax_error('no type attribute')

		if tagname == 'brush':
			chtype = 'brush'
			mediatype = subtype = None
			mimetype = None
		else:
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
##				if tagname is not None and mtype[0]!=tagname and \
##				   (tagname[:5]!='cmif_' or mtype!=['text','plain']):
##					self.warning("file type doesn't match element", self.lineno)
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

##	 		if attributes['encoding'] not in ('base64', 'UTF'):
## 				self.syntax_error('bad encoding parameter')

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
		node.__chantype = chtype
		self.AddAttrs(node, attributes)
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
			if CASCADE:
				region = 'unnamed region %d' % self.__regionno
				self.__regionno = self.__regionno + 1
			else:
				region = 'unnamed region'
		node.__region = region
		ch = self.__regions.get(region)
		if ch is None:
			# create a region for this node
			self.__in_layout = self.__seen_layout
			ch = {}
			for key, val in self.attributes['region'].items():
				if val is not None:
					ch[key] = val
			ch['id'] = region
			ch['left'] = '%dpx' % self.__defleft
			ch['top'] = '%dpx' % self.__deftop
			self.__defleft = self.__defleft + 20
			self.__deftop = self.__deftop + 10
			self.start_region(ch, checkid = 0)
			self.end_region()
			self.__in_layout = LAYOUT_NONE
			ch = self.__regions[region]
		width = height = 0
		l = ch.get('left')
		w = ch.get('width')
		r = ch.get('right')
		t = ch.get('top')
		h = ch.get('height')
		b = ch.get('bottom')
		if l is not None and w is not None and r is not None:
			del ch['right']
			r = None
		if t is not None and h is not None and b is not None:
			del ch['bottom']
			b = None
		top = self.__topregion.get(node.__region)
		if self.__tops[top]['width'] > 0 and \
		   self.__tops[top]['height'] > 0:
			# we don't have to calculate minimum sizes
			pass
		elif (type(l) is type(0)) + (type(w) is type(0)) + (type(r) is type(0)) >= 2 and \
		     (type(t) is type(0)) + (type(h) is type(0)) + (type(b) is type(0)) >= 2:
			# size and position is given in pixels
			pass
		elif mtype in ('image', 'movie', 'video', 'mpeg',
			       'RealPix', 'RealText', 'RealVideo'):
			# if we don't know the region size and
			# position in pixels, we need to look at the
			# media objects to figure out the size to use.
			if node.attrdict.has_key('file'):
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
		elif mtype in ('text', 'label', 'html', 'graph', 'brush'):
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

	def NewAnimateNode(self, tagname, attributes):
		# mimetype -- the MIME type of the node as specified in attr
		# mediatype, subtype -- mtype split into parts
		# tagname -- the tag name in the SMIL file (None for "ref")
		# nodetype -- the CMIF node type (imm/ext/...)

		self.__fix_attributes(attributes)
		id = self.__checkid(attributes)

		if not self.__in_smil:
			self.syntax_error('node not in smil')
			return
		if self.__in_layout:
			self.syntax_error('node in layout')
			return
		
		# find target node (explicit or implicit)
		targetnode = None
		targetid = attributes.get('targetElement')
		if not targetid:
			targetid = attributes.get('href')
		if targetid:
			if self.__nodemap.has_key(targetid):
				targetnode = self.__nodemap[targetid]
		elif self.__node:
			targetnode = self.__node
		else:
			self.syntax_error('the target element of "%s" is unspecified' % tagname)
			return
			
		# keep most common attr version
		aname = attributes.get('attribute')
		if aname:
			attributes['attributeName']	= aname
			del attributes['attribute']

		# create the node
		node = self.__context.newnode('imm')
		self.AddAttrs(node, attributes)
		if self.__node:
			self.__node._addchild(node)
		else:
			self.__container._addchild(node)

		# + what AddAttrs has not translated to grins conventions
		attributeName = attributes.get('attributeName')
		if attributeName and attributeName == 'src':
			node.attrdict['attributeName'] = 'file'
			
		node.attrdict['type'] = 'animate'
		node.attrdict['tag'] = tagname
		node.attrdict['mimetype'] = 'animate/%s' % tagname

		# synthesize a name for the channel
		# intrenal for now so no conflicts
		chname = 'animate%s' % node.GetUID()
		node.attrdict['channel'] = chname


		# add this node to the tree if it is possible 
		# else keep it for later fix
		if targetnode:
			node.targetnode = targetnode
		elif targetid:
			node.__targetid = targetid
			self.__animatenodes.append(node)
		
		# add to context an internal channel for this node
		self.__context.addinternalchannels( [(chname, node.attrdict), ] )


	def EndAnimateNode(self):
		pass

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
		for t in self.__tops.keys():
			self.__calcsize1(t)
			w = self.__tops[t]['width']
			h = self.__tops[t]['height']
			for r in self.__childregions[t]:
				self.__calcsize2(t, r, w, h)

	def __calcsize1(self, region):
		minwidth = minheight = 0
		for r in self.__childregions[region]:
			w, h = self.__calcsize1(r)
			if w > minwidth:
				minwidth = w
			if h > minheight:
				minheight = h
		if self.__tops.has_key(region):
			if self.__tops[region]['width'] == 0:
				self.__tops[region]['width'] = minwidth
			if self.__tops[region]['height'] == 0:
				self.__tops[region]['height'] = minheight
			minwidth = self.__tops[region]['width']
			minheight = self.__tops[region]['height']
		else:
			attrdict = self.__regions[region]
			if attrdict.get('minwidth', 0) < minwidth:
				attrdict['minwidth'] = minwidth
			if attrdict.get('minheight', 0) < minheight:
				attrdict['minheight'] = minheight
			minwidth = _minsize(attrdict.get('left'),
					    attrdict.get('width'),
					    attrdict.get('right'),
					    attrdict.get('minwidth', 0))
			minheight = _minsize(attrdict.get('top'),
					     attrdict.get('height'),
					     attrdict.get('bottom'),
					     attrdict.get('minheight', 0))
		return minwidth, minheight

	def __calcsize2(self, top, region, width, height):
		from windowinterface import UNIT_PXL, UNIT_SCREEN
		attrdict = self.__regions[region]
		l = attrdict.get('left')
		w = attrdict.get('width')
		r = attrdict.get('right')
		t = attrdict.get('top')
		h = attrdict.get('height')
		b = attrdict.get('bottom')
		# if size of root-layout specified, convert to pixels
		if self.__tops[top]['declwidth']:
			if type(l) is type(0.0):
				l = int(l * width + .5)
				attrdict['left'] = l
			if type(w) is type(0.0):
				w = int(w * width + .5)
				attrdict['width'] = w
			if type(r) is type(0.0):
				r = int(r * width + .5)
				attrdict['right'] = r
		if self.__tops[top]['declheight']:
			if type(t) is type(0.0):
				t = int(t * height + .5)
				attrdict['top'] = t
			if type(h) is type(0.0):
				h = int(h * height + .5)
				attrdict['height'] = h
			if type(b) is type(0.0):
				b = int(b * height + .5)
				attrdict['bottom'] = b
		#
		thetype = None # type of 1st elem != 0
		for val in l, w, r, t, h, b:
			if val == 0 or val is None:
				continue
			if thetype is None:
				thetype = type(val)
				continue
			elif type(val) is thetype:
				continue
			# we only get here if there are multiple
			# values != 0 of different types
			# not all the same units, convert everything
			# to relative sizes
			if type(l) is type(0):
				l = float(l) / width
			if type(w) is type(0):
				w = float(w) / width
			if type(r) is type(0):
				r = float(r) / width
			if type(t) is type(0):
				t = float(t) / height
			if type(h) is type(0):
				h = float(h) / height
			if type(b) is type(0):
				b = float(b) / height
			attrdict['units'] = units = UNIT_SCREEN
			break
		else:
			# all the same type or 0/None
			if thetype is type(0.0):
				units = UNIT_SCREEN
			else:
				units = UNIT_PXL
			attrdict['units'] = units
		# change things around so that l,w and t,h are defined
		# if fewer than two of l,w,r and t,h,b are defined, fill
		# in defaults: l==t==0, w and h rest of available space
		if l is None:
			if w is None:
				if r is None:
					l = 0
					if units == UNIT_PXL:
						w = width
					else:
						w = 1.0
				else:
					l = 0
					w = r
					r = None
			else:
				if r is None:
					l = 0
				else:
					l = r - w
					r = None
		else:
			if w is None:
				if r is None:
					if units == UNIT_PXL:
						w = width - l
					else:
						w = 1.0 - l
				else:
					w = r - l
					r = None
			else:
				if r is not None:
					r = None
		if t is None:
			if h is None:
				if b is None:
					t = 0
					if units == UNIT_PXL:
						h = height
					else:
						h = 1.0
				else:
					t = 0
					h = b
					b = None
			else:
				if b is None:
					t = 0
				else:
					t = b - h
					b = None
		else:
			if h is None:
				if b is None:
					if units == UNIT_PXL:
						h = height - t
					else:
						h = 1.0 - t
				else:
					h = b - t
					b = None
			else:
				if b is not None:
					b = None
		attrdict['left'] = l
		attrdict['width'] = w
		if attrdict.has_key('right'):
			del attrdict['right']
		attrdict['top'] = t
		attrdict['height'] = h
		if attrdict.has_key('bottom'):
			del attrdict['bottom']

		if type(w) is type(0.0):
			w = int(w * width + .5)
		if type(h) is type(0.0):
			h = int(h * height + .5)
		
		for r in self.__childregions[region]:
			self.__calcsize2(top, r, w, h)

	def FixSyncArcs(self, node):
		save_lineno = self.lineno
		for attr, val, lineno in node.__syncarcs:
			self.lineno = lineno
			self.SyncArc(node, attr, val)
		self.lineno = save_lineno
		del node.__syncarcs

	def CreateLayout(self, attrs, isroot = 1):
		from windowinterface import UNIT_PXL
		bg = None
		name = None
		if attrs is not None:
			bg = attrs.get('backgroundColor')
			if bg is None:
				bg = attrs['background-color']
			bg = self.__convert_color(bg)
			name = attrs.get('id')
		top = name
		if not name:
			name = layout_name # only for anonymous root-layout
		ctx = self.__context
		layout = MMNode.MMChannel(ctx, name)
		if not self.__region2channel.has_key(top):
			self.__region2channel[top] = []
		self.__region2channel[top].append(layout)
		self.__topchans.append(layout)
		ctx.channeldict[name] = layout
		ctx.channelnames.insert(0, name)
		ctx.channels.insert(0, layout)
		if isroot:
			self.__base_win = name
		layout['type'] = 'layout'
		if bg is not None and \
		   bg != 'transparent' and \
		   bg != 'inherit':
			layout['bgcolor'] = bg
		else:
			layout['bgcolor'] = 0,0,0
		if isroot:
			top = None
		else:
			top = name
		if self.__tops[top]['width'] == 0:
			self.__tops[top]['width'] = 640
		if self.__tops[top]['height'] == 0:
			self.__tops[top]['height'] = 480
		layout['winsize'] = self.__tops[top]['width'], self.__tops[top]['height']
		layout['units'] = UNIT_PXL

	def FixBaseWindow(self):
		if not self.__topchans:
			return
		for ch in self.__context.channels:
			if ch in self.__topchans:
				continue
			# old 03-07-2000
			#if ch.has_key('base_window'):
			#	basewin = ch['base_window']
			#	basechans = self.__region2channel.get(basewin)
			#	if len(basechans) == 0:
			#		raise error, 'no base channels?'
			#	elif len(basechans) == 1:
			#		ch['base_window'] = basechans[0].name
			#	else:
			#		raise error, 'not implemented yet'
			#else:
			#	ch['base_window'] = self.__base_win
			#end old

			# new 03-07-2000
			if not ch.has_key('base_window'):
				ch['base_window'] = self.__base_win
			# end new

	def __fillchannel(self, ch, attrdict, mtype):
		attrdict = attrdict.copy() # we're going to change this...
		if attrdict.has_key('type'):
			del attrdict['type']
		if attrdict.has_key('base_window'):
			ch['base_window'] = attrdict['base_window']
			del attrdict['base_window']
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
			bg = attrdict['backgroundColor']
			del attrdict['backgroundColor']
			if features.compatibility == features.G2:
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
			ch['units'] = attrdict['units']; del attrdict['units']
			fit = attrdict['fit']; del attrdict['fit']
			if fit == 'hidden':
				ch['scale'] = 1
			elif fit == 'meet':
				ch['scale'] = 0
			elif fit == 'slice':
				ch['scale'] = -1
			ch['center'] = 0
			# other fit options not implemented

			ch['base_winoff'] = x, y, w, h
		# keep all attributes that we didn't use
		for attr, val in attrdict.items():
			if attr not in ('minwidth', 'minheight', 'units',
					'skip-content') and \
			   not self.attributes['region'].has_key(attr):
				ch[attr] = parseattrval(attr, val, self.__context)

	# old 03-07-2000
	# def MakeChannels(self):
	# end old
	# new 03-07-2000
	def __makeLayoutChannels(self):	
	# end new
		ctx = self.__context
		for top in self.__tops.keys():
			self.CreateLayout(self.__tops[top]['attrs'], top is None)
		for region in self.__regionlist:
			attrdict = self.__regions[region]
			# old 03-07-2000 --> now, all region are 'layout channel'
			#chtype = attrdict.get('type')
			#if chtype is None or not ChannelMap.channelmap.has_key(chtype):
			#	continue
			#end
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
			# old 03-07-2000
#			ch['type'] = chtype
			# end old
			# new 03-07-2000
			ch['type'] = 'layout'
			# end new
			
			# old 03-07-2000
#			if not self.__region2channel.has_key(region):
#			 	self.__region2channel[region] = []
#			self.__region2channel[region].append(ch)

			# self.__fillchannel(ch, attrdict, chtype)
			# end old
			# new 03-07-2000
			self.__fillchannel(ch, attrdict, 'layout')
			# end new
			
	def FixChannel(self, node):
		if node.GetType() not in leaftypes:
			return
		if MMAttrdefs.getattr(node, 'type') == 'animate':
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
			
		# if 'name' <> None, we can re-use the channel named 'name'

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
		# there is no channel of the right name and type, then we create a new channel
		if ch is None:
			ch = MMNode.MMChannel(ctx, name)
			# old 03-07-2000
			# actualy the region can be 'unnamed' only after a error (if the region doesn't exist)
			# if region != '<unnamed>':
			#	if not self.__region2channel.has_key(region):
			#		self.__region2channel[region] = []
			#	self.__region2channel[region].append(ch)
			ctx.channeldict[name] = ch
			ctx.channelnames.append(name)
			ctx.channels.append(ch)
			ch['type'] = mtype
			if mtype in ('image', 'movie', 'video', 'mpeg',
				     'text', 'label', 'html', 'graph', 'RealPix', 'RealText', 'RealVideo'):
		############################### WARNING ##################################
		################# to move the test : doesn't work clearly ################
		##########################################################################
				if not self.__regions.has_key(region):
					self.warning('no region %s in layout' %
						     region, self.lineno)
					self.__in_layout = self.__seen_layout
					self.start_region({'id': region})
					self.end_region()
					self.__in_layout = LAYOUT_NONE
		##########################################################################
				# we're going to change this locally...
				attrdict = self.__regions[region]
				
				# new 03-07-2000
				# add the new region in channel tree
				attrdict['base_window'] = region
				
				# for instance, we set z-index value to -1 in order to have to folow rule:.
				# if a LayoutChannel and XXChannel are sibling, LayoutChannel
				# is always in front of XXChannel
				attrdict['z-index'] = -1

				self.__fillchannel(ch, attrdict, mtype)
					
				if not self.__region2channel.has_key(region):
					self.__region2channel[region] = []
				self.__region2channel[region].append(ch)
				# end new
				
		node.attrdict['channel'] = name
		
		# complete chanlist
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
		
	def FixAnimateTargets(self):
		for node in self.__animatenodes:
			targetid = node.__targetid
			if self.__nodemap.has_key(targetid):
				targetnode = self.__nodemap[targetid]
				node.targetnode = targetnode
				del node.__targetid
		del self.__animatenodes
			
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

	def __fix_attributes(self, attributes):
		for key, val in attributes.items():
			if key[:len(GRiNSns)+1] == GRiNSns + ' ':
				del attributes[key]
				attributes[key[len(GRiNSns)+1:]] = val
			if key[:len(QTns)+1] == QTns + ' ':
				del attributes[key]
				attributes[key[len(QTns)+1:]] = val
		if features.compatibility == features.QT:
			self.parseQTAttributeOnSmilElement(attributes)

	def __checkid(self, attributes):
		id = attributes.get('id')
		if id is not None:
			res = xmllib.tagfind.match(id)
			if res is None or res.end(0) != len(id):
				self.syntax_error("illegal ID value `%s'" % id)
			if self.__ids.has_key(id):
				self.syntax_error('non-unique id %s' % id)
			self.__ids[id] = 0
		return id

	def __mkid(self, tag):
		# create an ID for an element that doesn't have one
		# note that we create an ID that is not legal XML, so
		# we shouldn't have to worry about clashes
		id = tag
		i = 0
		nn = '%s %d' % (id, i)
		while self.__ids.has_key(nn):
			i = i + 1
			nn = '%s %d' % (id, i)
		self.__ids[nn] = 0
		return nn

	# methods for start and end tags

	# smil contains everything
	def start_smil(self, attributes):
		for attr in attributes.keys():
			if attr != 'id' and \
			   self.attributes['body'].get(attr) != attributes[attr]:
				if self.__context.attributes.get('project_boston') == 0:
					self.syntax_error('body attribute %s not compatible with SMIL 1.0' % attr)
				self.__context.attributes['project_boston'] = 1
				break
		self.__fix_attributes(attributes)
		id = self.__checkid(attributes)
		if self.__seen_smil:
			self.error('more than 1 smil tag', self.lineno)
		self.__seen_smil = 1
		self.__in_smil = 1
		self.NewContainer('seq', attributes)

	def end_smil(self):
		from realnode import SlideShow
		self.__in_smil = 0
		if not self.__root:
			self.error('empty document', self.lineno)
		if not self.__tops.has_key(None) and \
		   not self.__context.attributes.get('project_boston'):
			attrs = {}
			for key, val in self.attributes['root-layout'].items():
				if val is not None:
					attrs[key] = val
			self.__tops[None] = {'width':0,
					     'height':0,
					     'declwidth':0,
					     'declheight':0,
					     'attrs':attrs}
			if not self.__childregions.has_key(None):
				self.__childregions[None] = []
##		self.FixRoot()
		self.FixSizes()
		self.__makeLayoutChannels()
		self.Recurse(self.__root, self.FixChannel, self.FixSyncArcs)
		self.Recurse(self.__root, self.CleanChanList)
		self.FixLayouts()
		self.FixBaseWindow()
		self.FixLinks()
		self.Recurse(self.__root, self.FixAnchors)
		for node in self.__realpixnodes:
			node.slideshow = SlideShow(node, self.__new_file)
		del self.__realpixnodes
		self.FixAnimateTargets()

	# head/body sections

	def start_head(self, attributes):
		self.__fix_attributes(attributes)
		id = self.__checkid(attributes)
		if not self.__in_smil:
			self.syntax_error('head not in smil')
		self.__in_head = 1

	def end_head(self):
		self.__in_head = 0

	def start_body(self, attributes):
		if not self.__seen_layout:
			self.__seen_layout = LAYOUT_SMIL
		self.__fix_attributes(attributes)
		if not self.__in_smil:
			self.syntax_error('body not in smil')
		if self.__seen_body:
			self.error('multiple body tags', self.lineno)
		self.__seen_body = 1
		self.__in_body = 1
		self.AddAttrs(self.__root, attributes)

	def end_body(self):
		self.end_seq()
		self.__in_body = 0

	def start_meta(self, attributes):
		self.__fix_attributes(attributes)
		id = self.__checkid(attributes)
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
			self.__context.settitle(content)
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
		elif name == 'project_boston':
			content = content == 'on'
			boston = self.__context.attributes.get('project_boston')
			if boston is not None and content != boston:
				self.syntax_error('conflicting project_boston attribute')
			self.__context.attributes['project_boston'] = content
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
		self.__fix_attributes(attributes)
		id = self.__checkid(attributes)
		if not self.__in_head:
			self.syntax_error('layout not in head')
		if self.__in_meta:
			self.syntax_error('layout in meta')
		if self.__seen_layout and not self.__in_head_switch:
			self.syntax_error('multiple layouts without switch')
		if attributes['type'] == SMIL_BASIC:
			if self.__seen_layout > 0:
				# if we've seen SMIL_BASIC/SMIL_EXTENDED
				# already, ignore this one
				self.__in_layout = LAYOUT_UNKNOWN
			else:
				self.__in_layout = LAYOUT_SMIL
			self.__seen_layout = LAYOUT_SMIL
		elif attributes['type'] == SMIL_EXTENDED:
			if self.__in_head_switch and \
			   self.__context.attributes.get('project_boston') == 0:
				# ignre text/smil-extended-layout if we're
				# specifically using SMIL 1.0 and we're
				# inside a switch (if we're not in a switch
				# we'll complain below)
				self.__in_layout = LAYOUT_UNKNOWN
				if not self.__seen_layout:
					self.__seen_layout = LAYOUT_UNKNOWN
				self.setliteral()
				return
			if self.__context.attributes.get('project_boston') == 0:
				self.syntax_error('layout type %s not compatible with SMIL 1.0' % SMIL_EXTENDED)
			self.__context.attributes['project_boston'] = 1
			if self.__seen_layout > 0:
				# if we've seen SMIL_BASIC/SMIL_EXTENDED
				# already, ignore this one
				self.__in_layout = LAYOUT_UNKNOWN
			else:
				self.__in_layout = LAYOUT_EXTENDED
			self.__seen_layout = LAYOUT_EXTENDED
		else:
			self.__in_layout = LAYOUT_UNKNOWN
			if not self.__seen_layout:
				self.__seen_layout = LAYOUT_UNKNOWN
			self.setliteral()

	def end_layout(self):
		self.__in_layout = LAYOUT_NONE

	def start_region(self, attributes, checkid = 1):
		if not self.__in_layout:
			self.syntax_error('region not in layout')
			return
		if self.__in_layout != LAYOUT_SMIL and \
		   self.__in_layout != LAYOUT_EXTENDED:
			# ignore outside of smil-basic-layout/smil-extended-layout
			return
		from windowinterface import UNIT_PXL
		id = None
		attrdict = {'z-index': 0,
			    'minwidth': 0,
			    'minheight': 0,}

		for attr, val in attributes.items():
			if attr[:len(GRiNSns)+1] == GRiNSns + ' ':
				attr = attr[len(GRiNSns)+1:]
			val = string.strip(val)
			if attr == 'id':
				attrdict[attr] = id = val
				if checkid:
					res = xmllib.tagfind.match(id)
					if res is None or res.end(0) != len(id):
						self.syntax_error("illegal ID value `%s'" % id)
				if self.__ids.has_key(id):
					self.syntax_error('non-unique id %s' % id)
				self.__ids[id] = 0
				self.__regions[id] = attrdict
			elif attr in ('left', 'width', 'right', 'top', 'height', 'bottom'):
				# XXX are bottom and right allowed in SMIL-Boston basic layout?
				if attr in ('bottom', 'right'):
					if self.__context.attributes.get('project_boston') == 0:
						self.syntax_error('%s attribute not compatible with SMIL 1.0' % attr)
					self.__context.attributes['project_boston'] = 1
				try:
					if val[-1] == '%':
						val = string.atof(val[:-1]) / 100.0
						if attr in ('width','height') and val < 0:
							self.syntax_error('region with negative %s' % attr)
							val = 0.0
					else:
						if val[-2:] == 'px':
							val = val[:-2]
						val = string.atoi(val)
						if attr in ('width','height') and val < 0:
							self.syntax_error('region with negative %s' % attr)
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
			elif attr == 'backgroundColor':
				if self.__context.attributes.get('project_boston') == 0:
					self.syntax_error('%s attribute not compatible with SMIL 1.0' % attr)
				self.__context.attributes['project_boston'] = 1
				val = self.__convert_color(val)
				if val is not None:
					attrdict['backgroundColor'] = val
			elif attr == 'background-color':
				# backgroundColor overrides background-color
				if not attrdict.has_key('backgroundColor'):
					val = self.__convert_color(val)
					if val is not None:
						attrdict['backgroundColor'] = val
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
		if attrdict.has_key('left') and attrdict.has_key('right') and attrdict.has_key('width'):
			del attrdict['right']
		if attrdict.has_key('top') and attrdict.has_key('bottom') and attrdict.has_key('height'):
			del attrdict['bottom']

		if id is None:
			self.syntax_error('region without id attribute')
			return

		if self.__region is not None:
			if self.__viewport is None:
				self.syntax_error('no nested regions allowed in root-layout windows')
			if self.__context.attributes.get('project_boston') == 0:
				self.syntax_error('nested regions not compatible with SMIL 1.0')
			self.__context.attributes['project_boston'] = 1
			pregion = self.__region[0]
			attrdict['base_window'] = pregion
			self.__childregions[pregion].append(id)
		elif self.__viewport is not None:
			attrdict['base_window'] = self.__viewport
			self.__childregions[self.__viewport].append(id)
		else:
			if not self.__tops.has_key(None):
				attrs = {}
				for key, val in self.attributes['root-layout'].items():
					if val is not None:
						attrs[key] = val
				self.__tops[None] = {'width':0,
						     'height':0,
						     'declwidth':0,
						     'declheight':0,
						     'attrs':attrs}
				self.__childregions[None] = []
			self.__childregions[None].append(id)

		self.__region = id, self.__region
		self.__regionlist.append(id)
		self.__childregions[id] = []
		self.__topregion[id] = self.__viewport # None if not in viewport

	def end_region(self):
		if self.__region is None:
			# </region> without <region>
			# error message will be taken care of by XMLparser.
			return
		self.__region = self.__region[1]

	def start_root_layout(self, attributes):
		if self.__in_layout != LAYOUT_SMIL and \
		   self.__in_layout != LAYOUT_EXTENDED:
			# ignore outside of smil-basic-layout/smil-extended-layout
			return
		self.__fix_attributes(attributes)
		id = self.__checkid(attributes)
		self.__root_layout = attributes
		width = attributes['width']
		if width[-2:] == 'px':
			width = width[:-2]
		try:
			width = string.atoi(width)
		except string.atoi_error:
			self.syntax_error('root-layout width not an integer')
			width = 0
		else:
			if width < 0:
				self.syntax_error('root-layout width not a positive integer')
				width = 0
		height = attributes['height']
		if height[-2:] == 'px':
			height = height[:-2]
		try:
			height = string.atoi(height)
		except string.atoi_error:
			self.syntax_error('root-layout height not an integer')
			height = 0
		else:
			if height < 0:
				self.syntax_error('root-layout height not a positive integer')
				height = 0
		self.__tops[None] = {'width':width,
				     'height':height,
				     'declwidth':width,
				     'declheight':height,
				     'attrs':attributes}
		if not self.__childregions.has_key(None):
			self.__childregions[None] = []

	def end_root_layout(self):
		pass

	def start_viewport(self, attributes):
		if self.__in_layout != LAYOUT_SMIL and \
		   self.__in_layout != LAYOUT_EXTENDED:
			# ignore outside of smil-basic-layout/smil-extended-layout
			return
		if self.__in_layout != LAYOUT_EXTENDED:
			self.syntax_error('viewport not allowed in layout type %s' % SMIL_BASIC)
		if self.__context.attributes.get('project_boston') == 0:
			self.syntax_error('viewport not compatible with SMIL 1.0')
		self.__context.attributes['project_boston'] = 1
		self.__fix_attributes(attributes)
		id = self.__checkid(attributes)
		if id is None:
			id = self.__mkid('viewport')
			attributes['id'] = id
		self.__viewport = id
		self.__childregions[id] = []
		width = attributes['width']
		if width[-2:] == 'px':
			width = width[:-2]
		try:
			width = string.atoi(width)
		except string.atoi_error:
			self.syntax_error('root-layout width not an integer')
			width = 0
		else:
			if width < 0:
				self.syntax_error('root-layout width not a positive integer')
				width = 0
		height = attributes['height']
		if height[-2:] == 'px':
			height = height[:-2]
		try:
			height = string.atoi(height)
		except string.atoi_error:
			self.syntax_error('root-layout height not an integer')
			height = 0
		else:
			if height < 0:
				self.syntax_error('root-layout height not a positive integer')
				height = 0
		self.__tops[id] = {'width':width,
				   'height':height,
				   'declwidth':width,
				   'declheight':height,
				   'attrs':attributes}

	def end_viewport(self):
		self.__viewport = None

	def start_user_attributes(self, attributes):
		if self.__context.attributes.get('project_boston') == 0:
			self.syntax_error('userAttributes not compatible with SMIL 1.0')
		self.__context.attributes['project_boston'] = 1
		self.__fix_attributes(attributes)
		id = self.__checkid(attributes)

	def end_user_attributes(self):
		self.__context.addusergroups(self.__u_groups.items())

	def start_u_group(self, attributes):
		self.__fix_attributes(attributes)
		id = self.__checkid(attributes)
		title = attributes.get('title', '')
		u_state = attributes['uState']
		override = attributes.get('override', 'allowed')
		self.__u_groups[id] = title, u_state == 'RENDERED', override == 'allowed'

	def end_u_group(self):
		pass

	def start_layouts(self, attributes):
		self.__fix_attributes(attributes)
		id = self.__checkid(attributes)

	def end_layouts(self):
		pass

	def start_Glayout(self, attributes):
		self.__fix_attributes(attributes)
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

	def start_parexcl(self, ntype, attributes):
		self.__fix_attributes(attributes)
		id = self.__checkid(attributes)
		# XXXX we ignore sync for now
		self.NewContainer(ntype, attributes)
		if not self.__container:
			return
		self.__container.__endsync = attributes.get('endsync')
		self.__container.__lineno = self.lineno
## 		if self.__container.__endsync is not None and \
## 		   self.__container.attrdict.has_key('duration'):
## 			self.warning('ignoring dur attribute', self.lineno)
## 			del self.__container.attrdict['duration']

	def end_parexcl(self, ntype):
		node = self.__container
		self.EndContainer(ntype)
		endsync = node.__endsync
		del node.__endsync
		if endsync is None:
			pass
		elif endsync == 'first':
			node.attrdict['terminator'] = 'FIRST'
		elif endsync == 'last':
			node.attrdict['terminator'] = 'LAST'
		elif endsync == 'all':
			node.attrdict['terminator'] = 'ALL'
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
			self.warning('unknown idref in endsync attribute', node.__lineno)
		del node.__lineno

	def start_par(self, attributes):
		self.start_parexcl('par', attributes)

	def end_par(self):
		self.end_parexcl('par')

	def start_seq(self, attributes):
		self.__fix_attributes(attributes)
		id = self.__checkid(attributes)
		self.NewContainer('seq', attributes)

	def end_seq(self):
		self.EndContainer('seq')

	def start_excl(self, attributes):
		self.start_parexcl('excl', attributes)

	def end_excl(self):
		self.end_parexcl('excl')

	def start_choice(self, attributes):
		self.__fix_attributes(attributes)
		id = self.__checkid(attributes)
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
		self.__fix_attributes(attributes)
		id = self.__checkid(attributes)
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

	def start_brush(self, attributes):
		if self.__context.attributes.get('project_boston') == 0:
			self.syntax_error('brush element not compatible with SMIL 1.0')
		self.__context.attributes['project_boston'] = 1
		self.NewNode('brush', attributes)

	def end_brush(self):
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
		self.__fix_attributes(attributes)
		id = self.__checkid(attributes)
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

	# parse coordonnees of a shape
	# all string can't be specify in only one regular expression, because we don't know the number of points
	# Instead, there is a first regular expression which parse the first number, then a second which parse
	# the separateur caractere and the next number
	# return value: list of numbers (values expressed in pourcent or pixel)
	# or None if error
	
	def __parseCoords(self, data):
		l = []
		res = coordre.match(data)
		if not res:
			self.syntax_error('syntax error in coords attribute')
			return
		endParse = res.end()
		x = res.group('x')
		
		inPourcent = x[-1]=='%'
		
		if x[-1] == '%':
			value = string.atoi(x[:-1]) / 100.0
		else:
			value = string.atoi(x)
		l.append(value)	
	
		while (endParse < len(data)):
			res = coordrewithsep.match(data[endParse:])
			if not res:
				self.syntax_error('syntax error in coords attribute')
				return
			startParse = endParse+res.start()
			endParse = endParse+res.end()
			# test in order to avoid an infinite loop
			if startParse == endParse:
				self.syntax_error('internal error !')
				return
					
			x = res.group('x')
			
			if (x[-1] == '%') != inPourcent:
				self.warning('Cannot mix pixels and percentages in anchor',
					self.lineno)

			if x[-1] == '%':
				value = string.atoi(x[:-1]) / 100.0
			else:
				value = string.atoi(x)
			l.append(value)	

		return l
		
	def start_anchor(self, attributes):
		self.__fix_attributes(attributes)
		id = self.__checkid(attributes)
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

		# coord and shape parsing
		
		# shape attribute
		shape = attributes.get('shape')
		if shape == None or shape == 'rect':
			ashapetype = A_SHAPETYPE_RECT
		elif shape == 'poly':
			ashapetype = A_SHAPETYPE_POLY
		elif shape == 'circle':
			ashapetype = A_SHAPETYPE_CIRCLE
		else:
			ashapetype = A_SHAPETYPE_RECT
			self.syntax_error('Unknow shape type '+shape)
			
		# coords attribute
		coords = attributes.get('coords')
		l = None
		if coords is not None:
			l = self.__parseCoords(coords)
		
		if l is not None:
			atype = ATYPE_NORMAL
			if ashapetype == A_SHAPETYPE_RECT:
				error = 0
				if len(l) != 4:
					self.syntax_error('Invalid number of coordinate values in anchor')
					error = 1
				if not error:
					x0, y0, x1, y1 = l[:]					
					if x1 <= x0 or y1 <= y0:
						self.warning('Anchor coordinates incorrect. XYWH-style?.',
							self.lineno)
						error = 1
				
				if not error:
					# x,y,w,h are now floating point if they were
					# percentages, otherwise they are ints.

					# for instance, keep the compatibility
					aargs = [x0, y0, x1-x0, y1-y0]
#					aargs = [ashapetype, x0, y0, x1-x0, y1-y0]
			elif ashapetype == A_SHAPETYPE_POLY:
				error = 0
				if (len(l) < 4) or (len(l) & 1):
					self.syntax_error('Invalid number of coordinate values in anchor')
					error = 1				
				if not error:	
					# if the last coordinate is equal than first coordinate, we supress the last						
					if l[-2] == l[0] and l[-1] == l[1]:
						l = l[:-2]
						if len(l) < 4:
							self.syntax_error('Invalid number of coordinate values in anchor')
							error = 1										
				if not error:
					aargs = [ashapetype,]+l
			elif ashapetype == A_SHAPETYPE_CIRCLE:
				error = 0
				if len(l) != 3:
					self.syntax_error('Invalid number of coordinate values in anchor')
					error = 1
				if not error:
					cx, cy, rd = l[:]					
					aargs = [ashapetype, cx, cy, rd]
											
		begin = attributes.get('begin')
		if begin is not None:
			try:
				begin = self.__parsecounter(begin)
			except error, msg:
				self.syntax_error(msg)
				begin = None
			else:
				atype = ATYPE_NORMAL
		end = attributes.get('end')
		if end is not None:
			try:
				end = self.__parsecounter(end)
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
		if attributes.has_key('fragment'):
			aid = attributes['fragment']
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

	def start_area(self, attributes):
		if self.__context.attributes.get('project_boston') == 0:
			self.syntax_error('area not compatible with SMIL 1.0')
		self.__context.attributes['project_boston'] = 1
		self.start_anchor(attributes)

	def end_area(self):
		self.end_anchor()

	def start_animate(self, attributes):
		if self.__context.attributes.get('project_boston') == 0:
			self.syntax_error('animate not compatible with SMIL 1.0')
		self.__context.attributes['project_boston'] = 1
		self.NewAnimateNode('animate', attributes)

	def end_animate(self):
		self.EndAnimateNode()

	def start_set(self, attributes):
		if self.__context.attributes.get('project_boston') == 0:
			self.syntax_error('set not compatible with SMIL 1.0')
		self.__context.attributes['project_boston'] = 1
		self.NewAnimateNode('set', attributes)

	def end_set(self):
		self.EndAnimateNode()

	def start_animatemotion(self, attributes):
		if self.__context.attributes.get('project_boston') == 0:
			self.syntax_error('animateMotion not compatible with SMIL 1.0')
		self.__context.attributes['project_boston'] = 1
		self.NewAnimateNode('animateMotion', attributes)

	def end_animatemotion(self):
		self.EndAnimateNode()

	def start_animatecolor(self, attributes):
		if self.__context.attributes.get('project_boston') == 0:
			self.syntax_error('animateColor not compatible with SMIL 1.0')
		self.__context.attributes['project_boston'] = 1
		self.NewAnimateNode('animateColor', attributes)

	def end_animatecolor(self):
		self.EndAnimateNode()

	# other callbacks

	__whitespace = re.compile(_opS + '$')
	def handle_data(self, data):
		if self.__node is None or self.__is_ext:
			if self.__in_layout != LAYOUT_UNKNOWN:
				res = self.__whitespace.match(data)
				if not res:
					self.syntax_error('non-white space content')
			return
		self.__nodedata.append(data)

	__doctype = re.compile('SYSTEM' + xmllib._S + '(?P<dtd>[^ \t\r\n]+)' +
			       _opS + '$')
	def handle_doctype(self, tag, pubid, syslit, data):
		if tag != 'smil':
			self.error('not a SMIL document', self.lineno)
		if data:
			self.syntax_error('invalid DOCTYPE')
			return
		if pubid == SMILpubid and syslit == SMILdtd:
			# SMIL version 1.0
			self.__context.attributes['project_boston'] = 0
		elif pubid == SMILBostonPubid and syslit == SMILBostonDtd:
			# SMIL Boston
			self.__context.attributes['project_boston'] = 1

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

	def __parsecounter(self, value, maybe_relative = 0, withsign = 0):
		res = offsetvalue.match(value)
		if res:
			sign = res.group('sign')
			if sign and not withsign:
				self.syntax_error('no sign allowed')
				sign = None
			if sign:
				if self.__context.attributes.get('project_boston') == 0:
					self.syntax_error('sign not compatible with SMIL 1.0')
				self.__context.attributes['project_boston'] = 1
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
				tc, f, sc = res.group('timecount', 'units', 'metric')
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
			if sign and sign == '-':
				offset = -offset
			return offset
		if maybe_relative:
			if value in ('begin', 'end'):
				return value
		raise error, 'bogus presentation counter'

##	def __parsetime(self, xpointer):
##		offset = 0
##		res = syncbase.match(xpointer)
##		if res is not None:
##			name, event = res.group('name', 'event')
##			delay = None
##		else:
####			res = clock.match(xpointer)
####			if res is not None:
####				# XXXX absolute time not implemented
####				return None, 0, 0
####			else:
##			name, event, delay = None, None, xpointer
##		if event is not None:
##			counter = self.__parsecounter(event, 1)
##			if counter == 'begin':
##				counter = 0
##			elif counter == 'end':
##				counter = -1	# special event
##		else:
##			counter = 0
##		if delay is not None:
##			delay = self.__parsecounter(delay)
##		else:
##			delay = 0
##		return name, counter, delay

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
				val = float(self.__parsecounter(val))
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

def _minsize(start, extent, end, minsize):
	# Determine minimum size for parent window given that it
	# has to contain a subwindow with the given start/extent/end
	# values.  Start and extent can be integers or floats.  The
	# type determines whether they are interpreted as pixel values
	# or as fractions of the top-level window.
	# end is only used if extent is None.
	if start == 0:
		# make sure this is a pixel value
		start = 0
##	if extent is None and (type(start) is type(end) or start == 0):
##		extent = end - start
##		end = None
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
		elif type(extent) is type(0):
			# extent is pixel value
			if extent == 0:
				extent = minsize
			return start + extent
		elif type(end) is type(0.0):
			# no extent, end is fraction
			return int((start + minsize) / end + 0.5)
		elif type(end) is type(0):
			# no extent, end is pixel value
			return end
		else:
			# no extent and no end
			return start + minsize
	elif type(start) is type(0.0):
		# start is fraction
		if start == 1:
			raise error, 'region with impossible size'
		if type(extent) is type(0):
			# extent is pixel value
			if extent == 0:
				extent = minsize
			return int(extent / (1 - start) + 0.5)
		elif type(extent) is type(0.0):
			# extent is fraction
			if minsize > 0 and extent > 0:
				return int(minsize / extent + 0.5)
			return 0
		elif type(end) is type(0):
			# no extent, end is pixel value
			return end
		elif type(end) is type(0.0):
			# no extent, end is fraction
			if minsize > 0 and end > start:
				return int(minsize / (end - start) + 0.5)
			return 0
		else:
			# no extent and no end
			return int(minsize / (1 - start) + 0.5)
	elif type(end) is type(0):
		# no start, end is pixel value
		return end
	elif type(end) is type(0.0):
		# no start, end is fraction
		if end <= 0:
			return 0
		if type(extent) is type(0):
			# extent is pixel value
			if extent == 0:
				extent = minsize
			return int(extent / end + 0.5)
		elif type(extent) is type(0.0):
			# extent is fraction
			return int(minsize / end + 0.5)
	elif type(extent) is type(0):
		return extent
	elif type(extent) is type(0.0) and extent > 0:
		return int(minsize / extent + 0.5)
	return minsize

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


