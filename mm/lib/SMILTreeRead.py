__version__ = "$Id$"

import xmllib
import MMNode, MMAttrdefs
from MMExc import *
from MMTypes import *
import MMurl
import string
#from Hlinks import DIR_1TO2, TYPE_JUMP, TYPE_CALL, TYPE_FORK
from Hlinks import *
import re
import os, sys
from SMIL import *
import settings
import features
import compatibility
import ChannelMap
import EditableObjects
import parseutil
import colors
import urlcache
from Owner import OWNER_DOCUMENT
import time

if __debug__:
	parsedebug = 0

error = 'SMILTreeRead.error'

LAYOUT_NONE = 0				# must be 0
LAYOUT_SMIL = 1
LAYOUT_UNKNOWN = -1			# must be < 0
 
CASCADE = settings.get('cascade')	# cascade regions if no <layout>

layout_name = ' SMIL '			# name of layout channel

_opS = xmllib._opS
_S = xmllib._S

coordre = re.compile(r'(((?P<pixel>\d+)(?!\.|%|\d))|((?P<percent>\d+(\.\d+)?)%))$')

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
syncbase = re.compile(r'id\(' + _opS + '(?P<name>' + xmllib._Name + ')' + _opS + r'\)' + # id(name)
		      _opS +
		      r'(?:\(' + _opS + r'(?P<event>[^)]*[^) \t\r\n])' + _opS + r'\))?' + # (event)
		      _opS +
		      '$')
offsetvalue = re.compile('(?P<sign>[-+])?' + clock_val + '$')
# SMIL 2.0 syncbase without the offset
mediamarker = re.compile(		# id-ref ".marker(" name ")"
	_opS +
	r'(?P<id>' + xmllib._Name + r')\.'			# ID-ref "."
	r'marker\(' + _opS + r'(?P<markername>[^ \t\r\n()]+)' + _opS + r'\)' + _opS + r'$'	# "marker(...)"
	)
accesskey = re.compile(			# "accesskey(" character ")"
	_opS +
	r'(?P<accesskey>access[kK]ey)\((?P<character>.)\)' +
	_opS + r'$'
	)
wallclock = re.compile(			# "wallclock(" wallclock-value ")"
	r'wallclock\((?P<wallclock>[^()]+)\)$'
	)
wallclockval = re.compile(
	r'(?P<date>(?P<year>\d{4})-(?P<month>\d{2})-(?P<day>\d{2})T?)?'	# date (optional)
	r'(?P<time>(?P<hour>\d{2}):(?P<min>\d{2})(?::(?P<sec>\d{2}(?:\.\d+)?))?)?'	# time (optional)
	r'(?:(?P<Z>Z)|(?P<tzsign>[-+])(?P<tzhour>\d{2}):(?P<tzmin>\d{2}))?$'	# timezone (optional)
	)
xpathre = re.compile(			# e.g. "xpath(../../following-sibling::media[2]/*[1])"
	r'xpath\((?P<xpath>[^()]+)\)'
	)
screen_size = re.compile(_opS + r'(?P<y>\d+)' + _opS + r'[xX]' +
			 _opS + r'(?P<x>\d+)' + _opS + r'$')
clip = re.compile(_opS + r'(?:'
		  # npt=...
		   '(?:(?P<npt>npt)' + _opS + r'=' + _opS + r'(?P<nptclip>[^-]*))|'
		  # smpte/smpte-25/smpte-30-drop=...
		   '(?:(?P<smpte>smpte(?:-30-drop|-25)?)' + _opS + r'=' + _opS + r'(?P<smpteclip>[^-]*))|'
		  # clock value
		   '(?P<clock>'+clock_val+')|'
		  # marker=
		   '(?:(?P<marker>marker)' + _opS + '=' + _opS +'(?P<markerclip>[^()<> \t\r\n]+))'
		   ')' + _opS + r'$')
smpte_time = re.compile(r'(?:(?:\d{2}:)?\d{2}:)?\d{2}(?P<f>\.\d{2})?' + _opS + r'$')
namedecode = re.compile(r'(?P<name>.*)-\d+$')
_token = '[^][\001-\040()<>@,;:\\"/?=\177-\377]+' # \000 also not valid
dataurl = re.compile('data:(?P<type>'+_token+'/'+_token+')?'
		     '(?P<params>(?:;'+_token+'=(?:'+_token+'|"[^"\\\r\177-\377]*(?:\\.[^"\\\r\177-\377]*)*"))*)'
		     '(?P<base64>;base64)?'
		     ',(?P<data>.*)', re.I)
percent = re.compile('^([0-9]?[0-9]|100)%$')

del _token

_comma_sp = _opS + '(' + _S + '|,)' + _opS
_fp = r'(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)'
controlpt = re.compile('^'+_opS+_fp+_comma_sp+_fp+_comma_sp+_fp+_comma_sp+_fp+_opS+'$')
fpre = re.compile('^' + _fp + '$')
fppairre = re.compile(_opS+r'\('+_opS+'-?'+_fp+'%?'+_comma_sp+'-?'+_fp+'%?'+_opS+r'\)'+_opS+'$')
fppairre_bad = re.compile(_opS+'-?'+_fp+'%?'+_comma_sp+'-?'+_fp+'%?'+_opS+'$') # like fppairre but without ()
smil_node_attrs = [
	'region', 'clip-begin', 'clip-end', 'endsync', 
	'type', 'clipBegin', 'clipEnd',
	]

class SMILParser(SMIL, xmllib.XMLParser):
	__warnmeta = 0		# whether to warn for unknown meta properties

	# enumeration values for parseEnumValue
	__truefalse = {'false': 0, 'true': 1}
	__onoff = {'off': 0, 'on': 1}
	__enumattrs = {
		'accumulate': ['none', 'sum'],
		'actuate': ['onLoad', 'onRequest'],
		'additive': ['replace', 'sum'],
		'attach-timebase': __truefalse,
		'attributeType': ['CSS', 'XML', 'auto'],
		'autoReverse': __truefalse,
		'autoplay': __truefalse,
		'chapter-mode': {'all':0,'clip':1},
		'clipBoundary': ['parent', 'children'],
		'close': ['onRequest', 'whenNotActive'],
		'collapsed': __truefalse,
		'coordinated': __truefalse,
		'defaultState': __truefalse,
		'destinationPlaystate': ['play', 'pause'],
		'direction': ['forward', 'reverse'],
		'erase': ['never', 'whenDone'],
		'external': __truefalse,
		'fill': ['freeze', 'remove', 'hold', 'transition', 'auto', 'default'],
		'fillDefault': ['freeze', 'remove', 'hold', 'transition', 'auto', 'inherit'],
		'fit': ['meet', 'slice', 'fill', 'hidden', 'scroll'],
		'immediate-instantiation': __truefalse,
		'immediate-instantiation': __truefalse,
		'mode': ['in', 'out'],
		'open': ['onStart', 'whenActive'],
		'origin': ['parent', 'element'],
		'override': ['visible', 'hidden'],
		'previewShowOption': ['always', 'onSelected'],
		'regAlign': ['topLeft', 'topMid', 'topRight', 'midLeft', 'center', 'midRight', 'bottomLeft', 'bottomMid', 'bottomRight'],
		'reliable': __truefalse,
		'resizeBehavior': ['percentOnly', 'zoom'],
		'sendTo': {'_rpcontextwin':'rpcontextwin', '_rpbrowser':'rpbrowser', 'osdefaultbrowser':'osdefaultbrowser', 'rpengine':'rpengine'},
		'shape': ['rect', 'poly', 'circle'],
		'show': ['replace', 'pause', 'new'],
		'showAnimationPath': __truefalse,
		'showBackground': ['always', 'whenActive'],
		'showEditBackground': __truefalse,
		'sourcePlaystate': ['play', 'pause', 'stop'],
		'syncBehavior': ['canSlip', 'locked', 'independent', 'default'],
		'syncBehaviorDefault': ['canSlip', 'locked', 'independent', 'inherit'],
		'syncMaster': __truefalse,
		'system-captions': __onoff,
		'systemAudioDesc': __onoff,
		'systemCaptions': __onoff,
		'time-slider': __truefalse,
		}

	def __init__(self, context, printfunc = None, new_file = 0, check_compatibility = 0, progressCallback=None):
		self._elements = {
			'smil': (self.start_smil, self.end_smil),
			'head': (self.start_head, self.end_head),
			'meta': (self.start_meta, self.end_meta),
			'metadata': (self.start_metadata, self.end_metadata),
			'layout': (self.start_layout, self.end_layout),
			'customAttributes': (self.start_custom_attributes, self.end_custom_attributes),
			'customTest': (self.start_custom_test, self.end_custom_test),
			'region': (self.start_region, self.end_region),
			'root-layout': (self.start_root_layout, self.end_root_layout),
			'topLayout': (self.start_viewport, self.end_viewport),
			'viewport': (self.start_viewport, self.end_viewport),
			GRiNSns+' '+'layouts': (self.start_layouts, self.end_layouts),
			GRiNSns+' '+'layout': (self.start_Glayout, self.end_Glayout),
			GRiNSns+' '+'viewinfo': (self.start_viewinfo, self.end_viewinfo),
			'body': (self.start_body, self.end_body),
			'par': (self.start_par, self.end_par),
			'seq': (self.start_seq, self.end_seq),
			'switch': (self.start_switch, self.end_switch),
			'excl': (self.start_excl, self.end_excl),
			'priorityClass': (self.start_prio, self.end_prio),
			'ref': (self.start_ref, self.end_ref),
			'text': (self.start_text, self.end_text),
			'audio': (self.start_audio, self.end_audio),
			'img': (self.start_img, self.end_img),
			'video': (self.start_video, self.end_video),
			'animation': (self.start_animation, self.end_animation),
			'textstream': (self.start_textstream, self.end_textstream),
			'brush': (self.start_brush, self.end_brush),
			'a': (self.start_a, self.end_a),
			'anchor': (self.start_anchor, self.end_anchor),
			'area': (self.start_area, self.end_area),
			'animate': (self.start_animate, self.end_animate),
			'set': (self.start_set, self.end_set),
			'animateMotion': (self.start_animatemotion, self.end_animatemotion),
			'animateColor': (self.start_animatecolor, self.end_animatecolor),
			'transitionFilter': (self.start_transitionfilter, self.end_transitionfilter),
			'param': (self.start_param, self.end_param),
			'transition': (self.start_transition, self.end_transition),
			'regPoint': (self.start_regpoint, self.end_regpoint),
			'prefetch': (self.start_prefetch, self.end_prefetch),
			GRiNSns + ' ' + 'assets': (self.start_assets, self.end_assets),
			}
		self.__encoding = 'utf-8'
		xmllib.XMLParser.__init__(self, complain_foreign_namespace = 0)
		self.__seen_smil = 0
		self.__in_smil = 0
		self.__in_head = 0
		self.__in_head_switch = 0
		self.__in_meta = 0
		self.__seen_body = 0
		self.__in_body = 0
		self.__in_layout = LAYOUT_NONE
		self.__seen_layout = 0
		self.__has_layout = 0
		self.__seen_root_layout = 0
		self.__in_a = None
		self.__context = context
		self.__root = None
		self.__rootLayout = None
		self.__viewport = None
		self.__container = None
		self.__node = None	# the media object we're in
		self.__regionnames = {}	# mapping from regionName to list of id
		self.__region = None	# keep track of nested regions
		self.__elementindex = 0
		self.__ids = {}		# collect all id's here
		self.__nodemap = {}	# mapping from ID to MMNode instance
		self.__idmap = {}
		self.__links = []
		self.__base = ''
		self.__printfunc = printfunc
		self.__printdata = []
		self.__custom_tests = {}
		self.__layouts = {}
		self.__transitions = {}
		self.__animatenodes = []
		self.__new_file = new_file
		self.__check_compatibility = check_compatibility
		self.__generator = ''
		self.__regionno = 0
		self.__defleft = 0
		self.__deftop = 0
		self.__in_metadata = 0
		self.__metadata = []
		self.__errorList = []
		self.__viewinfo = []
		self.__progressCallback = progressCallback # tuple of (callback fnc, interval of time updated (max))
		self.__progressTimeToUpdate = 0	# next time to update the progress bar (if progresscallback is not none
		self.__nlines = 0		# number of lines. Useful to determine the progress value
		self.__animateParSet = {}
		self.__have_accesskey = 0
		self.__readskin()

		if new_file and type(new_file) is type(''):
			self.__base = new_file
		self.__validchannels = {'undefined':0}
		for chtype in ChannelMap.getvalidchanneltypes(context):
			self.__validchannels[chtype] = 1
		for chtype in ChannelMap.SMILBostonChanneltypes:
			self.__validchannels[chtype] = 1

	def feed(self, data):
		self.__nlines = data.count('\n')
		xmllib.XMLParser.feed(self, data)

	def close(self):
		xmllib.XMLParser.close(self)
		# XXX for now all documents are converted to SMIL 2.0 documents
		self.__context.attributes['project_boston'] = 1
		
		# Show the parse errors to the user:
		if self.__printfunc is not None and self.__printdata:
			data = '\n'.join(self.__printdata)
			# first 30 lines should be enough
			data = data.split('\n')
			if len(data) > 30:
				data = data[:30]
				data.append('. . .')
			self.__printfunc('\n'.join(data))
			self.__printdata = []
		self._elements = {}

	def GetRoot(self):
		if not self.__root:
			self.error('empty document', self.lineno)
		return self.__root

	def GetErrorList(self):
		return self.__errorList
	
	def MakeRoot(self, type, mayexist = 0):
		if mayexist and self.__root:
			return self.__root
		self.__root = self.__context.newnodeuid(type, '1')
		self.__root.addOwner(OWNER_DOCUMENT)
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
		val = val.strip()
		res = syncbase.match(val)
		if res is not None:
			# SMIL 1.0 begin value
			name = res.group('name')
			event = res.group('event')
			if event:
				try:
					delay = parseutil.parsecounter(event, maybe_relative = 1, syntax_error = self.syntax_error, context = self.__context)
				except parseutil.error:
					return
			else:
				delay = 0
			xnode = self.__nodemap.get(name)
			if xnode is None:
				self.syntax_error('sync arc from  unknown node to %s' % node.attrdict.get('name','<unnamed>'))
				return
			if not node.GetSchedParent().IsTimeChild(xnode):
				self.syntax_error('out of scope sync arc from %s to %s' % (xnode.attrdict.get('name','<unnamed>'), node.attrdict.get('name','<unnamed>')))
				if not features.editor:
					return
			if delay == 'begin' or delay == 'end':
				event = delay
				delay = 0.0
			else:
				event = 'begin'
			if settings.MODULES['DeprecatedFeatures']:
				list.append(MMNode.MMSyncArc(node, attr, srcnode=xnode,event=event,delay=delay))
		else:
			vals = val.split(';')
			if len(vals) > 1:
				if not settings.MODULES['MultiArcTiming']:
					return
				boston = 'multiple %s values' % attr
			for val in vals:
				val = val.strip()
				if not val:
					self.syntax_error('illegal empty value in %s attribute' % attr)
					continue
				if val == 'indefinite':
					if not boston:
						boston = 'indefinite'
					if settings.MODULES['BasicInlineTiming']:
						list.append(MMNode.MMSyncArc(node, attr))
					continue
				try:
					offset = parseutil.parsecounter(val, withsign = 1, syntax_error = self.syntax_error, context = self.__context)
				except parseutil.error:
					if val[0] in '-+' + string.digits:
						self.syntax_error('%s value starting with sign or digit must be offset value' % attr)
						continue
				else:
					if settings.MODULES['BasicInlineTiming']:
						list.append(MMNode.MMSyncArc(node, attr, srcnode='syncbase', delay=offset))
					if val[0] in '-+' and not boston:
						boston = 'signed clock value'
					continue

				res = wallclock.match(val)
				if res is not None:
					if not boston:
						boston = 'wallclock time'
					wc = res.group('wallclock').strip()
					res = wallclockval.match(wc)
					if res is None:
						self.syntax_error('bad wallclock value')
						continue
					date = res.group('date')
					time = res.group('time')
					if date is None and time is None:
						self.syntax_error('bad wallclock value')
						continue
					if date is not None:
						yr,mt,dy = map(lambda v: v and int(v), res.group('year','month','day'))
					else:
						yr = mt = dy = None
					if time is None:
						hr = mn = sc = 0
						if date[-1] == 'T':
							self.syntax_error('bad wallclock value')
							continue
					else:
						if date is not None and date[-1] != 'T':
							self.syntax_error('bad wallclock value')
							continue
						hr,mn = map(lambda v: v and int(v), res.group('hour','min'))
						sc = res.group('sec')
						if sc is not None:
							sc = float(sc)
						else:
							sc = 0
					tzsg = res.group('tzsign')
					tzhr,tzmn = map(lambda v: v and int(v), res.group('tzhour','tzmin'))
					if res.group('Z') is not None:
						tzhr = tzmn = 0
						tzsg = '+'
					if settings.MODULES['WallclockTiming']:
						list.append(MMNode.MMSyncArc(node, attr, wallclock = (yr,mt,dy,hr,mn,sc,tzsg,tzhr,tzmn), delay = 0))
					continue
				if val[:9] == 'wallclock':
					self.syntax_error('bad wallclock value')
					continue

				tokens = filter(None, map(string.strip, tokenize(val)))
				ok = 1
				i = 0
				while i < len(tokens):
					# this can't match the first
					# time round because of part
					# above
					if tokens[i] in ('-', '+'):
						try:
							offset = parseutil.parsecounter(''.join(tokens[i:]), withsign = 1, syntax_error = self.syntax_error, context = self.__context)
						except parseutil.error:
							self.syntax_error('bad offset value or unescaped - in identifier')
							if tokens[i] == '-':
								# try to fix it
								tokens[i-1:i+2] = [''.join(tokens[i-1:i+2])]
								continue
							ok = 0
							break
						del tokens[i:]
						val = ''.join(tokens)
						break
					i = i + 1
				else:
					offset = None
				if not ok:
					continue

				# XXXX No longer pertinent -mjvdg
				if tokens[0] == 'prev':
					if len(tokens) != 3 or tokens[1] != '.' or tokens[2] not in ('begin', 'end'):
						self.syntax_error('bad sync-to-prev value')
						continue
					list.append(MMNode.MMSyncArc(node, attr, srcnode = 'prev', event = tokens[2], delay = offset or 0))
					if not boston:
						boston = 'prev value'
					continue

				res = accesskey.match(val)
				if res is not None:
					if not boston:
						boston = 'accesskey'
					char = res.group('character')
					nsdict = self.getnamespace()
					if res.group('accesskey') == 'accessKey':
						for ns in nsdict.values():
							if ns in limited['viewport']:
								break
						else:
							self.syntax_error('accessKey deprecated in favor of accesskey')
					else:
						for ns in nsdict.values():
							if ns in limited['topLayout']:
								break
						else:
							self.syntax_error('accesskey not available in old namespace')
					if settings.MODULES['AccessKeyTiming']:
						list.append(MMNode.MMSyncArc(node, attr, accesskey=char, delay=offset or 0))
						self.__have_accesskey = self.__have_accesskey + 1
					continue

				if '.' not in tokens:
					# event value
					# XXX this includes things like
					# repeat(3)
					event = ''.join(''.join(tokens).split('\\'))
					if (event[:7] == 'repeat(' and settings.MODULES['RepeatValueTiming']) or \
					   (event in ('begin', 'end') and settings.MODULES['SyncbaseTiming']) or \
					   (event[:7] not in ('repeat(', 'begin', 'end') and settings.MODULES['EventTiming']):
						list.append(MMNode.MMSyncArc(node, attr, srcnode = node, event = event, delay = offset or 0))
					if not boston:
						boston = 'event value'
					continue

				if tokens[0] == 'xpath' and tokens[1] == '(' and tokens[3] == ')':
					tokens[0:4] = [''.join(tokens[0:4])]

				if tokens[0] == '.' or tokens[1] != '.':
					self.syntax_error('bad event specification')
					continue

				if tokens[-1] in ('begin', 'end') and tokens[-2] == '.':
					if len(tokens) != 3:
						self.syntax_error('bad syncbase value')
						continue
					name = ''.join(tokens[0].split('\\'))
					event = tokens[2] # tokens[-1]
				else:
					try:
						i = tokens.index('marker')
					except ValueError:
						# definitely not a marker value
						pass
					else:
						if 0 < i < len(tokens)-1 and tokens[i-1] == '.' and tokens[i+1] == '(':
							res = mediamarker.match(val)
							if res is not None:
								if offset is not None:
									self.syntax_error('no offset allowed with media marker')
									continue

								if not boston:
									boston = 'marker'
								name = res.group('id')
								xnode = self.__nodemap.get(name)
								if xnode is None:
									self.warning('ignoring sync arc from unknown node %s to %s' % (name, node.attrdict.get('name','<unnamed>')))
									continue
								if xnode.type != 'ext':
									self.warning('ignoring marker value from non-media element')
									continue
								marker = res.group('markername')
								if settings.MODULES['MediaMarkerTiming']:
									list.append(MMNode.MMSyncArc(node, attr, srcnode=xnode, marker=marker, delay=offset or 0))
								continue
							self.syntax_error('bad marker value')
							continue
					if '.' in tokens[2:]:
						self.syntax_error('bad event specification')
						continue
					name = ''.join(tokens[0].split('\\'))
					event = ''.join(''.join(tokens[2:]).split('\\'))

				if not boston:
					boston = 'SMIL-2.0 time value'
				xanchor = xchan = None
				res = xpathre.match(name)
				if res is not None:
					xnode = res.group('xpath') # GRiNS extension
				else:
					xnode = self.__nodemap.get(name)
				if xnode is None:
					xchan = self.__context.channeldict.get(name)
					if xchan is None:
						self.warning('ignoring sync arc from unknown element %s to %s' % (name, node.attrdict.get('name','<unnamed>')))
						continue
					if event[:8] == 'viewport' or event[:9] == 'topLayout':
						nsdict = self.getnamespace()
						if event[:8] == 'viewport':
							event = 'topLayout' + event[8:]
							for ns in nsdict.values():
								if ns in limited['viewport']:
									break
							else:
								self.syntax_error('viewport deprecated in favor of topLayout')
						else:
							for ns in nsdict.values():
								if ns in limited['topLayout']:
									break
							else:
								self.syntax_error('topLayout not available in old namespace')
				if (event[:7] == 'repeat(' and settings.MODULES['RepeatValueTiming']) or \
				   (event in ('begin', 'end') and settings.MODULES['SyncbaseTiming']) or \
				   (event[:7] not in ('repeat(', 'begin', 'end') and settings.MODULES['EventTiming']):
					list.append(MMNode.MMSyncArc(node, attr, srcnode=xnode,channel=xchan,event=event,delay=offset or 0))
				continue
		if boston:
			if self.__context.attributes.get('project_boston') == 0:
				self.syntax_error('%s not compatible with SMIL 1.0' % boston)
				if not features.editor:
					return
			self.__context.attributes['project_boston'] = 1
		if beginlist:
			node.attrdict['beginlist'] = beginlist
		if endlist:
			node.attrdict['endlist'] = endlist

	def AddTestAttrs(self, attrdict, attributes):
		# order is important: the hyphenated version of a test
		# attribute must come before the new camelCase
		# version.
		for attr in ('system-bitrate', 'systemBitrate'):
			if attributes.has_key(attr):
				val = attributes[attr]
				del attributes[attr]
				boston = '-' not in attr
				if boston and self.__context.attributes.get('project_boston') == 0:
					self.syntax_error('%s attribute not compatible with SMIL 1.0' % attr)
				if boston and features.editor:
					self.__context.attributes['project_boston'] = 1
				if not boston or self.__context.attributes.get('project_boston'):
					try:
						bitrate = int(val)
					except ValueError:
						self.syntax_error('bad %s attribute value' % attr)
					else:
						if not attrdict.has_key('system_bitrate'):
							attrdict['system_bitrate'] = bitrate
		for attr in ('system-screen-size', 'systemScreenSize'):
			if attributes.has_key(attr):
				val = attributes[attr]
				del attributes[attr]
				boston = '-' not in attr
				if boston and self.__context.attributes.get('project_boston') == 0:
					self.syntax_error('%s attribute not compatible with SMIL 1.0' % attr)
				if boston and features.editor:
					self.__context.attributes['project_boston'] = 1
				if not boston or self.__context.attributes.get('project_boston'):
					res = screen_size.match(val)
					if res is None:
						self.syntax_error('bad %s attribute value' % attr)
					else:
						if not attrdict.has_key('system_screen_size'):
							attrdict['system_screen_size'] = tuple(map(int, res.group('x','y')))
		for attr in ('system-screen-depth', 'systemScreenDepth'):
			if attributes.has_key(attr):
				val = attributes[attr]
				del attributes[attr]
				boston = '-' not in attr
				if boston and self.__context.attributes.get('project_boston') == 0:
					self.syntax_error('%s attribute not compatible with SMIL 1.0' % attr)
				if boston and features.editor:
					self.__context.attributes['project_boston'] = 1
				if not boston or self.__context.attributes.get('project_boston'):
					try:
						depth = int(val)
					except ValueError:
						self.syntax_error('bad %s attribute value' % attr)
					else:
						if not attrdict.has_key('system_screen_depth'):
							attrdict['system_screen_depth'] = depth
		for attr in ('system-captions', 'systemCaptions'):
			if attributes.has_key(attr):
				boston = '-' not in attr
				if boston and self.__context.attributes.get('project_boston') == 0:
					self.syntax_error('%s attribute not compatible with SMIL 1.0' % attr)
				if boston and features.editor:
					self.__context.attributes['project_boston'] = 1
				if not boston or self.__context.attributes.get('project_boston'):
					val = self.parseEnumValue(attr, attributes[attr])
					if val is not None:
						attrdict['system_captions'] = val
				del attributes[attr]
		if attributes.has_key('systemAudioDesc'):
			if self.__context.attributes.get('project_boston') == 0:
				self.syntax_error('%s attribute not compatible with SMIL 1.0' % attr)
			if features.editor:
				self.__context.attributes['project_boston'] = 1
			if self.__context.attributes.get('project_boston'):
				val = self.parseEnumValue('systemAudioDesc', attributes['systemAudioDesc'])
				if val is not None:
					attrdict['system_audiodesc'] = val
			del attributes['systemAudioDesc']
		for attr in ('system-language', 'systemLanguage'):
			if attributes.has_key(attr):
				val = attributes[attr]
				del attributes[attr]
				boston = '-' not in attr
				if boston and self.__context.attributes.get('project_boston') == 0:
					self.syntax_error('%s attribute not compatible with SMIL 1.0' % attr)
				if boston and features.editor:
					self.__context.attributes['project_boston'] = 1
				if not boston or self.__context.attributes.get('project_boston'):
					if not attrdict.has_key('system_language'):
						attrdict['system_language'] = val
		if attributes.has_key('systemCPU'):
			val = attributes['systemCPU']
			del attributes['systemCPU']
			if self.__context.attributes.get('project_boston') == 0:
				self.syntax_error('%s attribute not compatible with SMIL 1.0' % attr)
			if features.editor:
				self.__context.attributes['project_boston'] = 1
			if self.__context.attributes.get('project_boston'):
				attrdict['system_cpu'] = val.lower()
		if attributes.has_key('systemOperatingSystem'):
			val = attributes['systemOperatingSystem']
			del attributes['systemOperatingSystem']
			if self.__context.attributes.get('project_boston') == 0:
				self.syntax_error('%s attribute not compatible with SMIL 1.0' % attr)
			if features.editor:
				self.__context.attributes['project_boston'] = 1
			if self.__context.attributes.get('project_boston'):
				attrdict['system_operating_system'] = val.lower()
		if attributes.has_key('system-overdub-or-caption'):
			val = attributes['system-overdub-or-caption']
			del attributes['system-overdub-or-caption']
			if val in ('caption', 'overdub'):
				if val == 'caption':
					val = 'subtitle'
				attrdict['system_overdub_or_caption'] = val
			else:
				self.syntax_error('bad system-overdub-or-caption attribute value')
		if attributes.has_key('systemOverdubOrSubtitle'):
			val = attributes['systemOverdubOrSubtitle']
			del attributes['systemOverdubOrSubtitle']
			if self.__context.attributes.get('project_boston') == 0:
				self.syntax_error('%s attribute not compatible with SMIL 1.0' % attr)
			if features.editor:
				self.__context.attributes['project_boston'] = 1
			if self.__context.attributes.get('project_boston'):
				if val in ('subtitle', 'overdub'):
					attrdict['system_overdub_or_caption'] = val
				else:
					self.syntax_error('bad systemOverdubOrSubtitle attribute value')
		nsdict = self.getnamespace()
		for attr in ('system-required', 'systemRequired'):
			if attributes.has_key(attr):
				val = attributes[attr]
				del attributes[attr]
				boston = '-' not in attr
				if boston and self.__context.attributes.get('project_boston') == 0:
					self.syntax_error('%s attribute not compatible with SMIL 1.0' % attr)
				if boston and features.editor:
					self.__context.attributes['project_boston'] = 1
				if not boston or self.__context.attributes.get('project_boston'):
					list = map(string.strip, val.split('+'))
					# len(list) >= 1, even if val == ''
					if not list or (len(list) == 1 and list[0] == ''):
						self.syntax_error('%s attribute value should not be empty' % attr)
						list = []
					elif len(list) > 1:
						if self.__context.attributes.get('project_boston') == 0:
							self.syntax_error('%s attribute value not compatible with SMIL 1.0' % attr)
							if not features.editor:
								list = []
						else:
							self.__context.attributes['project_boston'] = 1
					val = []
					for v in list:
						nsuri = nsdict.get(v)
						if not nsuri:
							self.syntax_error('no namespace declaration for %s in effect in %s attribute' % (v, attr))
						else:
							val.append(nsuri)
					if not attrdict.has_key('system_required') and list:
						attrdict['system_required'] = val
		if attributes.has_key('systemComponent'):
			val = attributes['systemComponent']
			del attributes['systemComponent']
			if self.__context.attributes.get('project_boston') == 0:
				self.syntax_error('%s attribute not compatible with SMIL 1.0' % attr)
			if features.editor:
				self.__context.attributes['project_boston'] = 1
			if self.__context.attributes.get('project_boston'):
				attrdict['system_component'] = val.split()
		if attributes.has_key('customTest'):
			val = attributes['customTest']
			del attributes['customTest']
			if self.__context.attributes.get('project_boston') == 0:
				self.syntax_error('%s attribute not compatible with SMIL 1.0' % attr)
			if features.editor:
				self.__context.attributes['project_boston'] = 1
			if self.__context.attributes.get('project_boston'):
				attrdict['u_group'] = []
				for v in map(string.strip, val.split('+')):
					if self.__custom_tests.has_key(v):
						attrdict['u_group'].append(v)
					else:
						self.syntax_error("unknown customTest `%s'" % v)

	def AddAnimateAttrs(self, attrdict, attributes):
			if self.__context.attributes.get('project_boston') == 0 and not features.editor:
				# we've already warned about the element, so no need to warn about the attributes
				return
			if attributes.has_key('fadeColor'):
				fc = self.__convert_color(attributes['fadeColor'], 'fadeColor')
				if fc is None:
					pass # error already given
				elif type(fc) is not type(()):
					self.syntax_error("bad fadeColor attribute")
				else:
					attrdict['fadeColor'] = fc
				del attributes['fadeColor']
			for attr in ('by', 'from', 'to', 'values', 'path', 'subtype', 'attributeName', 'targetElement'):
				if attributes.has_key(attr):
					attrdict[attr] = attributes[attr]
					del attributes[attr]
			for attr in ('horzRepeat', 'vertRepeat', 'borderWidth'):
				if not attributes.has_key(attr):
					continue
				val = attributes[attr]
				try:
					if val and val[0] in '-+':
						raise ValueError('no sign allowed')
					val = int(val)
				except ValueError:
					self.syntax_error("error parsing value of `%s' attribute" % attr)
				else:
					attrdict[attr] = val
				del attributes[attr]
			if attributes.has_key('mode'):
				val = self.parseEnumValue('mode', attributes['mode'])
				if val is not None:
					attrdict['mode'] = val
				del attributes['mode']
			if attributes.has_key('origin'):
				val = self.parseEnumValue('origin', attributes['origin'])
				if val is not None:
					attrdict['origin'] = val
				del attributes['origin']
			if attributes.has_key('attributeType'):
				val = self.parseEnumValue('attributeType', attributes['attributeType'])
				if val is not None:
					attrdict['attributeType'] = val
				del attributes['attributeType']
			if attributes.has_key('calcMode'):
				val = attributes['calcMode']
				if val in ('discrete', 'linear', 'paced'):
					attrdict['calcMode'] = val
				elif val == 'spline':
					if not settings.MODULES['SplineAnimation']:
						self.warning('non-standard value for attribute calcMode', self.lineno)
					attrdict['calcMode'] = val
				else:
					self.syntax_error("bad %s attribute" % attr)
				del attributes['calcMode']
			if attributes.has_key('keySplines'):
				val = attributes['keySplines']
				vals = val.split(';')
				for v in vals:
					if not controlpt.match(v):
						self.syntax_error("bad keySplines attribute")
						break
				else:
					attrdict['keySplines'] = val
				del attributes['keySplines']
			if attributes.has_key('keyTimes'):
				val = attributes['keyTimes']
				vals = val.split(';')
				if attrdict.has_key('keySplines') and len(vals) != len(attrdict['keySplines'].split(';'))+1:
					self.syntax_error("bad keyTimes attribute (wrong number of control points)")
				else:
					keyTimes = []
					for v in vals:
						v = v.strip()
						if not fpre.match(v):
							self.syntax_error("bad keyTimes attribute")
							break
						keyTimes.append(float(v))
					else:
						attrdict['keyTimes'] = keyTimes
				del attributes['keyTimes']
			if attributes.has_key('accumulate'):
				val = self.parseEnumValue('accumulate', attributes['accumulate'])
				if val is not None:
					attrdict['accumulate'] = val
				del attributes['accumulate']
			if attributes.has_key('additive'):
				val = self.parseEnumValue('additive', attributes['additive'])
				if val is not None:
					attrdict['additive'] = val
				del attributes['additive']
			if attributes.has_key('borderColor'):
				val = attributes['borderColor']
				if val == 'blend':
					attrdict['borderColor'] = (-1,-1,-1)
				else:
					val = self.__convert_color(val, 'borderColor')
					if type(val) is type(''):
						self.syntax_error('bad borderColor attribute value')
					elif val is not None:
						attrdict['borderColor'] = val
				del attributes['borderColor']
			if attributes.has_key('borderWidth'):
				val = attributes['borderWidth']
				try:
					width = int(val)
				except ValueError:
					self.syntax_error('bad borderWidth attribute')
				else:
					attrdict['borderWidth'] = width
				del attributes['borderWidth']
								
	def addQTAttr(self, attrdict, attributes):
		if attributes.has_key('immediate-instantiation'):
			val = self.parseEnumValue('immediate-instantiation', attributes['immediate-instantiation'])
			if val is not None:
				attrdict['immediateinstantiationmedia'] = val
			del attributes['immediate-instantiation']
		if attributes.has_key('bitrate'):
			try:
				val = int(attributes['bitrate'])
			except ValueError:
				self.syntax_error("invalid `%s' value" % 'bitrate')
			else:
				attrdict['bitratenecessary'] = val
			del attributes['bitrate']
		if attributes.has_key('system-mime-type-supported'):
			attrdict['systemmimetypesupported'] = attributes['system-mime-type-supported']
			del attributes['system-mime-type-supported']
		if attributes.has_key('attach-timebase'):
			val = self.parseEnumValue('attach-timebase', attributes['attach-timebase'])
			if val is not None:
				attrdict['immediateinstantiationmedia'] = val == 'true'
			del attributes['attach-timebase']
		if attributes.has_key('chapter'):
			attrdict['qtchapter'] = attributes['chapter']
			del attributes['chapter']
		if attributes.has_key('composite-mode'):
			attrdict['qtcompositemode'] = attributes['composite-mode']
			del attributes['composite-mode']

	def AddCoreAttrs(self, attrdict, attributes):
		for attr in ('alt', 'longdesc', 'title'):
			if attributes.has_key(attr):
				attrdict[attr] = attributes[attr]
				del attributes[attr]
		if attributes.has_key('class'):
			if self.__context.attributes.get('project_boston') == 0:
				self.syntax_error('%s attribute not compatible with SMIL 1.0' % attr)
				if features.editor:
					self.__context.attributes['project_boston'] = 1
			if self.__context.attributes.get('project_boston'):
				attrdict[attr] = attributes['class']
			del attributes['class']
		if attributes.has_key('xml:lang'):
			if self.__context.attributes.get('project_boston') == 0:
				self.syntax_error('%s attribute not compatible with SMIL 1.0' % attr)
				if features.editor:
					self.__context.attributes['project_boston'] = 1
			if self.__context.attributes.get('project_boston'):
				attrdict['xmllang'] = attributes['xml:lang']
			del attributes['xml:lang']

	def AddAttrs(self, node, attributes):
		node.__syncarcs = []
		attrdict = node.attrdict
		self.AddTestAttrs(attrdict, attributes)
		self.AddCoreAttrs(attrdict, attributes)
		if node.type == 'animate':
			self.AddAnimateAttrs(attrdict, attributes)
		if compatibility.QT == features.compatibility:
			self.addQTAttr(attrdict, attributes)
		for attr, val in attributes.items():
			val = val.strip()
			func = self.__parseattrdict.get(attr)
			if func is not None:
				func(self, node, attr, val, attrdict)
			else:
				# catch all
				# this should not be used for normal operation
				try:
					attrdict[attr] = parseattrval(attr, val, self.__context)
				except:
					self.syntax_error("couldn't parse `%s' value" % attr)

	def __do_id(self, node, attr, val, attrdict):
		self.__nodemap[val] = node
		self.__idmap[val] = node.GetUID()
		res = namedecode.match(val)
		if res is not None:
			val = res.group('name')
		attrdict['name'] = val

	def __do_literal(self, node, attr, val, attrdict):
		if val:
			attrdict[attr] = val

	def __do_src(self, node, attr, val, attrdict):
		# Special case: # is used as a placeholder for empty URL fields
		if val != '#':
			attrdict['file'] = MMurl.basejoin(self.__base, val)

	def __do_sync(self, node, attr, val, attrdict):
		pnode = node.GetSchedParent()
		if attr == 'begin' and \
		   pnode is not None and \
		   pnode.type == 'seq' and \
		   (offsetvalue.match(val) is None or
		    val[0] == '-'):
			self.syntax_error('bad begin attribute for child of seq node')
			# accept anyway ...
			node.set_infoicon('error', 'bad begin attribute for child of seq node')
		node.__syncarcs.append((attr, val, self.lineno))

	def __do_dur(self, node, attr, val, attrdict):
		if val == 'indefinite':
			attrdict['duration'] = -1
		elif val == 'media':
			if node.type in mediatypes:
				attrdict['duration'] = -2
			else:
				self.syntax_error("no `media' value allowed on dur attribute on non-media elements")
		else:
			try:
				attrdict['duration'] = parseutil.parsecounter(val, syntax_error = self.syntax_error, context = self.__context)
			except parseutil.error, msg:
				self.syntax_error(msg)

	def __do_minmax(self, node, attr, val, attrdict):
		if self.__context.attributes.get('project_boston') == 0:
			self.syntax_error('%s attribute not compatible with SMIL 1.0' % attr)
			if not features.editor:
				return
		self.__context.attributes['project_boston'] = 1
		if val == 'media':
			if node.type in mediatypes:
				attrdict[attr] = -2
			else:
				self.syntax_error("no `media' value allowed on %s attribute on non-media elements" % attr)
		elif val == 'indefinite':
			if attr == 'max':
				attrdict[attr] = -1
			else:
				self.syntax_error("no `indefinite' value allowed on min attribute")
		else:
			try:
				attrdict[attr] = parseutil.parsecounter(val, syntax_error = self.syntax_error, context = self.__context)
			except parseutil.error, msg:
				self.syntax_error(msg)
			else:
				if attr == 'min' and \
				   attrdict[attr] == 0:
					del attrdict[attr]

	def __do_repeatCount(self, node, attr, val, attrdict):
		if attr == 'repeatCount':
			if self.__context.attributes.get('project_boston') == 0:
				self.syntax_error('%s attribute not compatible with SMIL 1.0' % attr)
				if not features.editor:
					return
			self.__context.attributes['project_boston'] = 1
		ignore = attr == 'repeat' and attrdict.has_key('loop')
		if val == 'indefinite':
			repeat = 0
		else:
			try:
				# fractional values are actually allowed in repeatCount
				repeat = float(val)
			except ValueError:
				self.syntax_error('bad repeat attribute')
				ignore = 1
			else:
				if repeat <= 0:
					self.syntax_error('bad %s value' % attr)
					ignore = 1
				elif attr == 'repeat' and '.' in val:
					self.syntax_error('fractional repeat value not allowed')
					ignore = 1
		if not ignore:
			attrdict['loop'] = repeat

	def __do_repeatDur(self, node, attr, val, attrdict):
		if self.__context.attributes.get('project_boston') == 0:
			self.syntax_error('%s attribute not compatible with SMIL 1.0' % attr)
			if not features.editor:
				return
		self.__context.attributes['project_boston'] = 1
		if val == 'indefinite':
			attrdict['repeatdur'] = -1
		else:
			try:
				attrdict['repeatdur'] = parseutil.parsecounter(val, syntax_error = self.syntax_error, context = self.__context)
			except parseutil.error, msg:
				self.syntax_error(msg)

	def __do_restart(self, node, attr, val, attrdict):
		if self.__context.attributes.get('project_boston') == 0:
			self.syntax_error('%s attribute not compatible with SMIL 1.0' % attr)
			if not features.editor:
				return
		self.__context.attributes['project_boston'] = 1
		if val in ('always', 'whenNotActive', 'never', 'default'):
			attrdict['restart'] = val
		else:
			self.syntax_error('bad %s attribute' % attr)

	def __do_restartDefault(self, node, attr, val, attrdict):
		if self.__context.attributes.get('project_boston') == 0:
			self.syntax_error('%s attribute not compatible with SMIL 1.0' % attr)
			if not features.editor:
				return
		self.__context.attributes['project_boston'] = 1
		if val in ('always', 'whenNotActive', 'never', 'inherit'):
			attrdict['restartDefault'] = val
		else:
			self.syntax_error('bad %s attribute' % attr)

	def __do_prefetch(self, node, attr, val, attrdict):
		if self.__context.attributes.get('project_boston') == 0:
			self.syntax_error('%s attribute not compatible with SMIL 1.0' % attr)
			if not features.editor:
				return
		self.__context.attributes['project_boston'] = 1
		try:
			if val[-1:]=='%':
				p = float(val[:-1])
			elif attr in ('mediaSize', 'bandwidth'):
				p = float(val)
			elif attr == 'mediaTime':
				p = parseutil.parsecounter(val, syntax_error = self.syntax_error, context = self.__context) 
			attrdict[attr] = val;	
		except ValueError:
			self.syntax_error('bad %s attribute' % attr)
		except parseutil.error, msg:
			self.syntax_error(msg)

	def __do_index(self, node, attr, val, attrdict):
		if self.__context.attributes.get('project_boston') == 0:
			self.syntax_error('%s attribute not compatible with SMIL 1.0' % attr)
			if not features.editor:
				return
		self.__context.attributes['project_boston'] = 1
		try:
			index = int(val)
			if index < 0:
				raise ValueError, 'negative value'
		except ValueError:
			self.syntax_error('bad %s attribute' % attr)
		else:
			attrdict[attr] = index

	def __do_sensitivity(self, node, attr, val, attrdict):
		if self.__context.attributes.get('project_boston') == 0:
			self.syntax_error('%s attribute not compatible with SMIL 1.0' % attr)
			if not features.editor:
				return
		self.__context.attributes['project_boston'] = 1
		if val == 'opaque':
			attrdict['sensitivity'] = 0
		elif val == 'transparent':
			attrdict['sensitivity'] = 100
		else:
			res = percent.match(val)
			if res is None:
				self.syntax_error('bad sensitivity attribute value')
			else:
				attrdict['sensitivity'] = int(val[:-1])

	def __do_transition(self, node, attr, val, attrdict):
		if self.__context.attributes.get('project_boston') == 0:
			self.syntax_error('%s attribute not compatible with SMIL 1.0' % attr)
			if not features.editor:
				return
		self.__context.attributes['project_boston'] = 1
		transitions = []
		warned = 0
		for val in map(string.strip, val.split(';')):
			if self.__transitions.has_key(val):
				transitions.append(val)
			elif not warned:
				self.syntax_error("invalid transition specified in %s attribute" % attr)
				warned = 1
		attrdict[attr] = transitions

	def __do_layout(self, node, attr, val, attrdict):
		if self.__layouts.has_key(val):
			attrdict['layout'] = val
		else:
			self.syntax_error("unknown layout `%s'" % val)

	def __do_fill(self, node, attr, val, attrdict):
		val = self.parseEnumValue(attr, val)
		if val is not None:
			if node.type in interiortypes or \
			   val in ('hold', 'transition', 'auto', 'default'):
				if self.__context.attributes.get('project_boston') == 0:
					self.syntax_error('%s attribute not compatible with SMIL 1.0' % attr)
					if not features.editor:
						return
				self.__context.attributes['project_boston'] = 1
			attrdict['fill'] = val

	def __do_mediaRepeat(self, node, attr, val, attrdict):
		if self.__context.attributes.get('project_boston') == 0:
			self.syntax_error('%s attribute not compatible with SMIL 1.0' % attr)
			if not features.editor:
				return
		self.__context.attributes['project_boston'] = 1
		if val in ('strip', 'preserve'):
			attrdict['mediaRepeat'] = val
		else:
			self.syntax_error("bad %s attribute" % attr)

	def __do_color(self, node, attr, val, attrdict):
		if node.__chantype != 'brush':
			return
		fg = self.__convert_color(val, attr)
		if fg is None:
			pass # error already given
		elif type(fg) is not type(()):
			self.syntax_error("bad %s attribute" % attr)
		else:
			attrdict['fgcolor'] = fg

	def __do_subposition(self, node, attr, val, attrdict):
		if node is not None or attr in ('bottom', 'right'):
			if self.__context.attributes.get('project_boston') == 0:
				self.syntax_error('%s attribute not compatible with SMIL 1.0 in media object' % attr)
				if not features.editor:
					return
			self.__context.attributes['project_boston'] = 1
		if val == 'auto':
			# "auto" is equivalent to no attribute
			return
		try:
			if val[-1:] == '%':
				val = float(val[:-1]) / 100.0
			else:
				if val[-2:] == 'px':
					val = val[:-2]
				val = int(val)
		except ValueError:
			self.syntax_error('invalid value for (sub)region attribute %s' % attr)
		else:
			if attr in ('widht', 'height') and val < 0:
				self.syntax_error('invalid value for (sub)region attribute %s' % attr)
			else:
				attrdict[attr] = val

	def __do_backgroundColor(self, node, attr, val, attrdict):
		if self.__context.attributes.get('project_boston') == 0:
			self.syntax_error('%s attribute not compatible with SMIL 1.0 in media object' % attr)
			if not features.editor:
				return
		self.__context.attributes['project_boston'] = 1
		bg = self.__convert_color(val, attr)
		if bg is None:
			pass
		elif bg == 'transparent':
			attrdict['transparent'] = 1
			attrdict['bgcolor'] = 0,0,0
		elif bg != 'inherit':
			attrdict['transparent'] = 0
			attrdict['bgcolor'] = bg
		else:
			# for inherit value, we assume there is no transparent and bgcolor attribute
			pass

	def __do_z_index(self, node, attr, val, attrdict):
		if node is not None:
			if self.__context.attributes.get('project_boston') == 0:
				self.syntax_error('%s attribute not compatible with SMIL 1.0 in media object' % attr)
				if not features.editor:
					return
			self.__context.attributes['project_boston'] = 1
		try:
			val = int(val)
		except ValueError:
			self.syntax_error('bad %s attribute value' % attr)
		else:
			if val < 0:
				self.syntax_error('negative %s attribute value not allowed' % attr)
			else:
				attrdict['z'] = val

	def __do_regPoint(self, node, attr, val, attrdict):
		if self.__context.attributes.get('project_boston') == 0:
			self.syntax_error('%s attribute not compatible with SMIL 1.0' % attr)
			if not features.editor:
				return
		self.__context.attributes['project_boston'] = 1
		if not self.__context.regpoints.has_key(val):
			self.syntax_error("the registration point %s doesn't exist" % val)
		else:
			attrdict['regPoint'] = val

	def __do_speed(self, node, attr, val, attrdict):
		if self.__context.attributes.get('project_boston') == 0:
			self.syntax_error('%s attribute not compatible with SMIL 1.0' % attr)
			if not features.editor:
				return
		self.__context.attributes['project_boston'] = 1
		try:
			speed = float(val)
		except ValueError:
			self.syntax_error('bad speed attribute')
		else:
			attrdict['speed'] = speed

	def __do_enum(self, node, attr, val, attrdict):
		val = self.parseEnumValue(attr, val)
		if val is not None:
			attrdict[attr] = val

	def __do_enumBoston(self, node, attr, val, attrdict):
		if self.__context.attributes.get('project_boston') == 0:
			self.syntax_error('%s attribute not compatible with SMIL 1.0' % attr)
			if not features.editor:
				return
		self.__context.attributes['project_boston'] = 1
		self.__do_enum(node, attr, val, attrdict)

	def __do_syncTolerance(self, node, attr, val, attrdict):
		if self.__context.attributes.get('project_boston') == 0:
			self.syntax_error('%s attribute not compatible with SMIL 1.0' % attr)
			if not features.editor:
				return
		self.__context.attributes['project_boston'] = 1
		if (attr == 'syncTolerance' and val == 'default') or \
		   (attr == 'syncToleranceDefault' and val == 'inherit'):
			val = -1
		else:
			try:
				val = parseutil.parsecounter(val, syntax_error = self.syntax_error, context = self.__context)
			except parseutil.error, msg:
				self.syntax_error(msg)
				val = None
		if val is not None:
			attrdict[attr] = val

	def __do_accelerate(self, node, attr, val, attrdict):
		if self.__context.attributes.get('project_boston') == 0:
			self.syntax_error('%s attribute not compatible with SMIL 1.0' % attr)
			if not features.editor:
				return
		self.__context.attributes['project_boston'] = 1
		try:
			val = float(val)
		except ValueError:
			self.syntax_error('bad %s attribute' % attr)
		else:
			if 0 <= val <= 1:
				attrdict[attr] = val
				if attrdict.get('accelerate', 0) + attrdict.get('decelerate', 0) > 1:
					self.syntax_error('accelerate + decelerate > 1')
			else:
				self.syntax_error("`%s' attribute value out of allowed range" % attr)

	def __do_default_region(self, node, attr, val, attrdict):
		region = self.__selectregion(val)
		attrdict['project_default_region'] = region

	def __do_bandwidth_fraction(self, node, attr, val, attrdict):
		try:
			if val[-1]=='%':
				p = float(val[:-1])/100.0
			else:
				p = float(val)
			attrdict[attr] = p
		except ValueError:
			self.syntax_error('bad %s attribute' % attr)

	def __do_default_duration(self, node, attr, val, attrdict):
		if val == 'indefinite':
			attrdict[attr] = -1
		else:
			try:
				attrdict[attr] = parseutil.parsecounter(val, syntax_error = self.syntax_error, context = self.__context)
			except parseutil.error, msg:
				self.syntax_error(msg)

	def __do_collapsed(self, node, attr, val, attrdict):
		collapsed = self.parseEnumValue(attr, val)
		if collapsed is not None:
			node.collapsed = collapsed

	def __do_showtime(self, node, attr, val, attrdict):
		if val in ('focus', 'cfocus', 'bwstrip'):
			# ignore in player
			if features.editor:
				node.showtime = val
		else:
			self.syntax_error('bad %s attribute' % attr)

	def __do_timezoom(self, node, attr, val, attrdict):
		try:
			node.min_pxl_per_sec = float(val)
		except ValueError:
			self.syntax_error('invalid timezoom attribute value')

	def __do_allowedmimetypes(self, node, attr, val, attrdict):
		attrdict[attr] = map(string.strip, val.split(','))

	def __do_forcechild(self, node, attr, val, attrdict):
		node.__forcechild = val, self.lineno

	def __do_skip_content(self, node, attr, val, attrdict):
		if val in ('true', 'false'):
			attrdict['skip_content'] = val == 'true'
		else:
			self.syntax_error('bad %s attribute' % attr)

	def __do_thumbnailIcon(self, node, attr, val, attrdict):
		attrdict['thumbnail_icon'] = MMurl.basejoin(self.__base, val)

	def __do_thumbnailScale(self, node, attr, val, attrdict):
		attrdict['thumbnail_scale'] = val == 'true'

	def __do_emptyIcon(self, node, attr, val, attrdict):
		attrdict['empty_icon'] = MMurl.basejoin(self.__base, val)

	def __do_emptyText(self, node, attr, val, attrdict):
		attrdict['empty_text'] = val

	def __do_emptyColor(self, node, attr, val, attrdict):
		val = self.__convert_color(val, attr)
		if val is not None:
			attrdict['empty_color'] = val

	def __do_emptyDur(self, node, attr, val, attrdict):
		try:
			attrdict['empty_duration'] = parseutil.parsecounter(val, syntax_error = self.syntax_error, context = self.__context)
		except parseutil.error, msg:
			self.syntax_error(msg)

	def __do_nonEmptyIcon(self, node, attr, val, attrdict):
		attrdict['non_empty_icon'] = MMurl.basejoin(self.__base, val)

	def __do_nonEmptyText(self, node, attr, val, attrdict):
		attrdict['non_empty_text'] = val

	def __do_nonEmptyColor(self, node, attr, val, attrdict):
		val = self.__convert_color(val, attr)
		if val is not None:
			attrdict['non_empty_color'] = val

	def __do_dropIcon(self, node, attr, val, attrdict):
		attrdict['dropicon'] = MMurl.basejoin(self.__base, val)

	def __do_opacity(self, node, attr, val, attrdict):
		try:
			if val[-1] == '%':
				val = float(val[:-1]) / 100.0
				if val < 0 or val > 1:
					self.syntax_error('%s value out of range' % attr)
					val = None
			else:
				self.syntax_error('only percentage values allowed on %s attribute' % attr)
				val = None
		except ValueError:
			self.syntax_error('invalid %s attribute value' % attr)
			val = None
		if val is not None:
			attrdict[attr] = val

	def __do_chromaKey(self, node, attr, val, attrdict):
		ck = self.__convert_color(val, attr)
		if ck is None:
			pass # error already given
		elif type(ck) is not type(()):
			self.syntax_error("bad %s attribute" % attr)
		else:
			attrdict[attr] = ck

	def __do_xmlbase(self, node, attr, val, attrdict):
		# XXX need to implement
		pass

	def __do_pass(self, node, attr, val, attrdict):
		pass

	__parseattrdict = {
		'abstract': __do_literal,
		'accelerate': __do_accelerate,
		'allowedmimetypes': __do_allowedmimetypes,
		'author': __do_literal,
		'autoReverse': __do_enumBoston,
		'backgroundColor': __do_backgroundColor,
		'backgroundOpacity': __do_opacity,
		'bandwidth': __do_prefetch,
		'begin': __do_sync,
		'bottom': __do_subposition,
		'chromaKey': __do_chromaKey,
		'chromaKeyOpacity': __do_opacity,
		'chromaKeyTolerance': __do_chromaKey,
		'collapsed': __do_collapsed,
		'color': __do_color,
		'copyright': __do_literal,
		'decelerate': __do_accelerate,
		'dropIcon': __do_dropIcon,
		'dur': __do_dur,
		'emptyColor': __do_emptyColor,
		'emptyDur': __do_emptyDur,
		'emptyIcon': __do_emptyIcon,
		'emptyText': __do_emptyText,
		'end': __do_sync,
		'erase': __do_enumBoston,
		'fill': __do_fill,
		'fillDefault': __do_enumBoston,
		'fit': __do_enumBoston,
		'height': __do_subposition,
		'id': __do_id,
		'layout': __do_layout,
		'left': __do_subposition,
		'max': __do_minmax,
		'mediaOpacity': __do_opacity,
		'mediaRepeat': __do_mediaRepeat,
		'mediaSize': __do_prefetch,
		'mediaTime': __do_prefetch,
		'min': __do_minmax,
		'nonEmptyColor': __do_nonEmptyColor,
		'nonEmptyIcon': __do_nonEmptyIcon,
		'nonEmptyText': __do_nonEmptyText,
		'previewShowOption': __do_enum,
		'project_bandwidth_fraction': __do_bandwidth_fraction,
		'project_default_duration': __do_default_duration,
		'project_default_duration_image': __do_default_duration,
		'project_default_duration_text': __do_default_duration,
		'project_default_region': __do_default_region,
		'project_default_type': __do_literal,
		'project_forcechild': __do_forcechild,
		'readIndex': __do_index,
		'regAlign': __do_enumBoston,
		'regPoint': __do_regPoint,
		'repeat': __do_repeatCount,
		'repeatCount': __do_repeatCount,
		'repeatDur': __do_repeatDur,
		'restart': __do_restart,
		'restartDefault': __do_restartDefault,
		'right': __do_subposition,
		'sensitivity': __do_sensitivity,
		'showAnimationPath': __do_enum,
		'showtime': __do_showtime,
		'skip-content': __do_skip_content,
		'speed': __do_speed,
		'src': __do_src,
		'syncBehavior': __do_enumBoston,
		'syncBehaviorDefault': __do_enumBoston,
		'syncMaster': __do_enumBoston,
		'syncTolerance': __do_syncTolerance,
		'syncToleranceDefault': __do_syncTolerance,
		'tabindex': __do_index,
		'thumbnailIcon': __do_thumbnailIcon,
		'thumbnailScale': __do_thumbnailScale,
		'timezoom': __do_timezoom,
		'top': __do_subposition,
		'transIn': __do_transition,
		'transOut': __do_transition,
		'width': __do_subposition,
		'xml:base': __do_xmlbase,
		'z-index': __do_z_index,
		}
	for __attr in smil_node_attrs:
		__parseattrdict[__attr] = __do_pass
	del __attr

	def parseEnumValue(self, attr, val, default = None):
		if val is None:
			return default
		values = self.__enumattrs[attr]
		if type(values) is type({}):
			if values.has_key(val):
				return values[val]
			valid = values.keys()
		else:
			if val in values:
				return val
			valid = values
		valid.sort()
		self.syntax_error("invalid `%s' value (valid values are: %s)" % (attr, ', '.join(valid)))
		return default

	def NewNode(self, tagname, attributes):
		# mimetype -- the MIME type of the node as specified in attr
		# mtype -- the MIME type of the node as calculated
		# mediatype, subtype -- mtype split into parts
		# tagname -- the tag name in the SMIL file (None for "ref")
		# nodetype -- the CMIF node type (imm/ext/...)
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
					data = MMurl.unquote(res.group('data'))
					# Convert any line ending to \n
					data = '\n'.join(data.split('\r\n'))
					data = '\n'.join(data.split('\r'))
					data = data.split('\n')
					nodetype = 'imm'
					del attributes['src']
		elif tagname != 'brush':
			self.syntax_error('no src attribute')

		if tagname == 'brush':
			nodetype = 'brush'
			chtype = 'brush'
			mediatype = subtype = None
			mimetype = None
		elif tagname == 'prefetch':
			nodetype = 'prefetch'
			chtype = 'prefetch'
			mediatype = subtype = None
			mimetype = None
		else:
			# find out type of file
			subtype = None
			mimetype = attributes.get('type')
			if mimetype is not None:
				if len(mimetype.split('/')) != 2:
					self.syntax_error('bad MIME type')
					mimetype = None
				else:
					mtype = mimetype
	# not allowed to look at extension...
			if url is not None and mtype is None:
				mtype = urlcache.mimetype(url)
				if mtype is None:
					# we have no idea what type the file is
					self.warning('cannot determine type of file %s' % url, self.lineno)

			mediatype = tagname
			if mtype is not None:
				mtype = mtype.split('/')
##				if tagname is not None and mtype[0]!=tagname and \
##				   (tagname[:5]!='cmif_' or mtype!=['text','plain']):
##					self.warning("file type doesn't match element", self.lineno)
				if tagname is None or tagname[:5] != 'cmif_':
					mediatype = mtype[0]
					subtype = mtype[1]


			# now determine channel type
			if subtype is not None and \
			   subtype.lower().find('real') >= 0:
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
				if subtype == 'svg-xml':
					chtype = 'svg'
				else:
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

			if attributes.has_key('iwidth'):
				try:
					width = int(attributes['iwidth'])
				except ValueError:
					self.syntax_error('invalid iwidth attribute value')
				else:
					urlcache.urlcache[url]['width'] = width
			if attributes.has_key('iheight'):
				try:
					height = int(attributes['iheight'])
				except ValueError:
					self.syntax_error('invalid iheight attribute value')
				else:
					urlcache.urlcache[url]['height'] = height
			if attributes.has_key('idur'):
				try:
					height = float(attributes['idur'])
				except ValueError:
					self.syntax_error('invalid idur attribute value')
				else:
					urlcache.urlcache[url]['duration'] = height

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
		self.__container = node
		node.__chantype = chtype

		# XXX The background color shouldn't be set by default from the parser:
		# XXX deal with inherit value. This part should be clean at some point, but you'll have
		# XXX to take into account the bgcolor code is not localize, and we have to keep as well the
		# XXX compatibility with G2 version, ...
		if node.attrdict.has_key('transparent'):
			del node.attrdict['transparent']

		# for SMIL 2, the default bgcolor is transparent
		if self.__context.attributes.get('project_boston') != 0:
			if not attributes.has_key('backgroundColor'):
				attributes['backgroundColor'] = 'transparent'
				
		node.__endsync = attributes.get('endsync')
		node.__lineno = self.lineno
		# and also, so other people can use it:
##		node.char_positions = (self.lineno, self.lineno+1)

		if url and features.editor and features.EXPORT_REAL in features.feature_set:
			import urlparse
			utype, host, path, params, query, fragment = urlparse.urlparse(url)
			if utype == 'file':
				path, query = MMurl.splitquery(path)
			if query:
				rpcontexturl = rpcontextwidth = rpcontextheight = None
				if '&' in query:
					queries = query.split('&')
				elif ';' in query:
					queries = query.split(';')
				else:
					queries = [query]
				nqueries = []
				for query in queries:
					qa = query.split('=', 1)
					if len(qa) == 2:
						q, a = qa
						if q == 'rpcontexturl':
							rpcontexturl = a
						elif q == 'rpcontextwidth':
							try:
								rpcontextwidth = int(a)
							except:
								pass
						elif q == 'rpcontextheight':
							try:
								rpcontextheight = int(a)
							except:
								pass
						else:
							nqueries.append(query)
				query = '&'.join(nqueries)
				if rpcontexturl:
					anchor = self.__context.newnode('anchor')
					anchor.__syncarcs = []
					node._addchild(anchor)
					self.__links.append((anchor, rpcontexturl))
					anchor.attrdict['external'] = 1
					anchor.attrdict['sendTo'] = 'rpcontextwin'
					anchor.attrdict['actuate'] = 'onLoad'
					if rpcontextwidth is not None:
						anchor.attrdict['contextwidth'] = rpcontextwidth
					if rpcontextheight is not None:
						anchor.attrdict['contextheight'] = rpcontextheight
				url = urlparse.urlunparse((utype, host, path, params, query, fragment))
				attributes['src'] = url
		self.AddAttrs(node, attributes)
		node.__mediatype = mediatype, subtype
		self.__attributes = attributes
		if mimetype is not None:
			node.SetAttr('mimetype', mimetype)
			
		# XXX we store the channel determinated by the previous code
		# but at some point, we should leave MMNode determinate itself the
		# right channel type.
#		node.SetChannelType(chtype)

		# for SMIL 1, we have to define all the time transparent
		# note : don't make this before addattrs to avoid warnings
		if self.__context.attributes.get('project_boston') == 0:
			node.attrdict['transparent'] = 1
			if node.attrdict.has_key('bgcolor'):
				del node.attrdict['bgcolor']

	def __newTopRegion(self, id = None):
		if self.__rootLayout is None:
			if features.editor and features.MULTIPLE_TOPLAYOUT not in features.feature_set and len(self.__context.getviewports()) > 0:
				self.unsupportedfeature_error("multiple top layouts")
			if id is None:
				id = self.__mkid('viewport')
			self.__rootLayout = self.__context.newviewport(id, -1, 'layout')
			self.__rootLayout.addOwner(OWNER_DOCUMENT)

	def __selectregion(self, region):
		# Select the region to play on.
		# This takes regionName attributes and test attributes
		# into consideration and returns the name of the selected
		# region.

		# experimental code for switch layout

		# first, find all elements in the layout section may be mapped
		# note that the region names are in document order
		regionIdList = self.__regionnames.get(region, [])

		# resolve the conflict according to the system caption test
		for regId in regionIdList:
			# get the first found

			preg = self.__context.channeldict.get(regId)
			all = settings.getsettings()
			allmatch = 1
			while preg is not None:
				notmatch = 0
				for setting in all:		
					settingvalue = preg.get(setting)
					if settingvalue is not None:
						ok = settings.match(setting,settingvalue)
						if not ok:
							notmatch = 1
							break
				if notmatch:
					allmatch = 0
					break

				# also check parent region/viewport
				preg = preg.GetParent()
			# if all parent match with system attribute, keep this region
			if allmatch:
				return regId

		# end experimental code for switch layout

		if not self.__context.channeldict.has_key(region):
			self.syntax_error('unknown region')
			region = 'unnamed region'
		return region

	def EndNode(self):
		self.__container = self.__container.GetParent()
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
		self.__fixendsync(node)

		# connect to region
		if attributes.has_key('region'):
			region = attributes['region']
			region = self.__selectregion(region)
		else:
			if CASCADE and not self.__has_layout:
				region = 'unnamed region %d' % self.__regionno
				self.__regionno = self.__regionno + 1
			else:
				region = 'unnamed region'
		node.__region = region
		node.attrdict['channel'] = region
		
		ch = self.__context.channeldict.get(region)
		if ch is None:
			# create a region for this node
			ch = self.__context.newchannel(region, -1, 'layout')
			ch['left'] = self.__defleft
			ch['top'] = self.__deftop
			self.__context.cssResolver.setRawAttrs(ch.getCssId(), [('left', self.__defleft), ('top', self.__deftop)])
			if CASCADE and not self.__has_layout:
				self.__defleft = self.__defleft + 20
				self.__deftop = self.__deftop + 10
			# make it a child of the root-layout
			self.__newTopRegion()
			self.__rootLayout._addchild(ch)

		if ChannelMap.isvisiblechannel(mtype):
			# create here all positioning nodes and initialize them
			cssResolver = self.__context.cssResolver				
			subRegCssId = node.getSubRegCssId()
			mediaCssId = node.getMediaCssId()

			attrList = []
			for attr in ['left', 'width', 'right', 'top', 'height', 'bottom']:
				if node.attrdict.has_key(attr):
					attrList.append((attr, node.attrdict[attr]))
			cssResolver.setRawAttrs(subRegCssId, attrList)

			attrList = []
			for attr in ['regAlign', 'regPoint', 'fit']:
				if node.attrdict.has_key(attr):
					attrList.append((attr, node.attrdict[attr]))
			cssResolver.setRawAttrs(mediaCssId, attrList)
												
		clip_begin = attributes.get('clipBegin')
		if clip_begin:
			attr = 'clipBegin'
			if self.__context.attributes.get('project_boston') == 0:
				self.syntax_error('clipBegin attribute not compatible with SMIL 1.0')
				if not features.editor:
					clip_begin = None
				else:
					self.__context.attributes['project_boston'] = 1
		else:
			attr = 'clip-begin'
			clip_begin = attributes.get('clip-begin')
		if clip_begin:
			res = clip.match(clip_begin)
			if res:
				node.attrdict['clipbegin'] = ''.join(clip_begin.split())
				if res.group('clock') and \
				   not self.__context.attributes.get('project_boston'):
					self.syntax_error('invalid clip-begin attribute; should be "npt=<time>"')
					del node.attrdict['clipbegin']
				elif res.group('marker'):
					if not self.__context.attributes.get('project_boston'):
						self.syntax_error('%s marker value not compatible with SMIL 1.0' % attr)
						if not features.editor:
							del node.attrdict['clipbegin']
						else:
							self.__context.attributes['project_boston'] = 1
					elif not settings.MODULES['MediaClipMarkers']:
						clip_begin = None
			else:
				self.syntax_error('invalid clip-begin attribute')
		clip_end = attributes.get('clipEnd')
		if clip_end:
			attr = 'clipEnd'
			if self.__context.attributes.get('project_boston') == 0:
				self.syntax_error('clipEnd attribute not compatible with SMIL 1.0')
				if not features.editor:
					clip_end = None
				else:
					self.__context.attributes['project_boston'] = 1
		else:
			attr = 'clip-end'
			clip_end = attributes.get('clip-end')
		if clip_end:
			res = clip.match(clip_end)
			if res:
				node.attrdict['clipend'] = ''.join(clip_end.split())
				if res.group('clock') and \
				   not self.__context.attributes.get('project_boston'):
					self.syntax_error('invalid clip-end attribute; should be "npt=<time>"')
					del node.attrdict['clipend']
				elif res.group('marker'):
					if not self.__context.attributes.get('project_boston'):
					     self.syntax_error('%s marker value not compatible with SMIL 1.0' % attr)
					     if not features.editor:
						     del node.attrdict['clipbegin']
					     else:
						     self.__context.attributes['project_boston'] = 1
					elif not settings.MODULES['MediaClipMarkers']:
						clip_end = None
			else:
				self.syntax_error('invalid clip-end attribute')
		if self.__in_a:
			# deal with hyperlink
			href, attrdict, id = self.__in_a[:-1]
			if id is not None and not self.__idmap.has_key(id):
				self.__idmap[id] = node.GetUID()
			# create the anchor node
			anchor = self.__context.newnode('anchor')
			node._addchild(anchor)
			anchor.attrdict.update(attrdict)
			anchor.__syncarcs = []
			self.__links.append((anchor, href))

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
		if type in ('par', 'seq', 'excl'):
			node.__forcechild = None, 0
		self.__container = node
		self.AddAttrs(node, attributes)

	def EndContainer(self, type):
		if self.__container is None or \
		   self.__container.GetType() != type:
			# erroneous end tag; error message from xmllib
			return
		self.__container = self.__container.GetParent()

	def NewAnimateNode(self, tagname, attributes):
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
		
		if tagname != 'animateMotion' and tagname != 'transitionFilter' and\
			not attributes.has_key('attributeName'):
			self.syntax_error('required attribute attributeName missing in %s element' % tagname)
			attributes['attributeName'] = ''

		# guess attr type
		attributeName = attributes.get('attributeName')
		attrtype = 'string'
		if tagname == 'animateMotion':
			attrtype = 'position'
		elif tagname == 'animateColor':
			attrtype = 'color'
		elif attributeName in ('left', 'top', 'width', 'height','right','bottom'):
			attrtype = 'coord'
		elif attributeName == 'z-index':
			attrtype = 'int'
		elif attributeName == 'soundLevel':
			attrtype = 'coord' # similar
			
		# check animation type and values
		animtype = None
		if attributes.has_key('path'):
			animtype = 'path'
			if tagname != 'animateMotion':
				self.syntax_error("invalid attribute in %s element" % tagname)
			# check path	
		elif attributes.has_key('values'):
			animtype = 'values'
			val = attributes['values']
			vals = val.split(';')
			if tagname == 'animateMotion':
				nvals = []
				for v in vals:
					if v and not fppairre.match(v):
						if fppairre_bad.match(v):
							if self.__generator.find('grins') < 0:
								self.syntax_error("missing parentheses on animateMotion values")
							v = '('+v+')'
						else:
							self.syntax_error("invalid motion values")
							del attributes['values']
							break
					nvals.append(v)
				else:
					attributes['values'] = ';'.join(nvals)
			elif tagname == 'animateColor':
				for v in vals:
					if v and not self.__convert_color(v, 'values'):
						self.syntax_error("invalid color values")
						del attributes['values']
						break
			elif attrtype == 'coord':
				for v in vals:
					if v and not coordre.match(v):
						self.syntax_error("invalid %s values" % attributeName)
						del attributes['values']
						break
			elif attrtype == 'int':
				for v in vals:
					try: 
						if v:
							v = int(v)
					except ValueError:
						self.syntax_error('invalid %s values' % attributeName)
						del attributes['values']
					break
		else:
			# check attribute values for validity
			for attr in ('from', 'to', 'by'):
				val = attributes.get(attr)
				if val is None:
					continue
				if tagname == 'animateMotion' and not fppairre.match(val):
					if fppairre_bad.match(val):
						if self.__generator.find('grins') < 0:
							self.syntax_error("missing parentheses in %s value" % attr)
						# fix up value since we know how
						attributes[attr] = '(' + val + ')'
					else:
						self.syntax_error("invalid %s value" % attr)
						del attributes[attr]
				elif tagname == 'animateColor' and not self.__convert_color(val, attr):
					self.syntax_error("invalid %s value" % attr)
					del attributes[attr]
				elif attrtype == 'coord' and not coordre.match(val):
					self.syntax_error("invalid %s value" % attr)
					del attributes[attr]
				elif attrtype == 'int':
					try:
						v = int(val)
					except ValueError:
						self.syntax_error('invalid %s value' % attr)
						del attributes[attr]

			# remaining attributes are valid, now determine animation type
			v1 = attributes.get('from')
			v2 = attributes.get('to')
			dv = attributes.get('by')
			if v2 or dv:
				if v1:
					if v2:			
						animtype = 'from-to'
					else:
						animtype = 'from-by'
				else:
					if v2:			
						animtype = 'to'
					else:
						animtype = 'by'
		if animtype is None:
			self.syntax_error('invalid values in %s element' % tagname)

		# create the node
		node = self.__context.newnode('animate')

		self.__container._addchild(node)
		self.AddAttrs(node, attributes)

		an = node.attrdict.get('attributeName')
		if an == 'soundLevel':
			minval = maxval = 1.0
			values = []
			s = node.attrdict.get('from')
			if s: 
				values.append(s)
			s = node.attrdict.get('to')
			if s: 
				values.append(s)
			sl = node.attrdict.get('values')
			if sl: 
				sl = sl.split(';')
				for s in sl:
					values.append(s)
			for s in values:
				if s:
					val = self.__parsePercent(s, 'values')
					if val is not None:
						minval = min(minval, val)
						maxval = max(maxval, val)
			self.__context.updateSoundLevelInfo('anim', 1)
			self.__context.updateSoundLevelInfo('min', minval)
			self.__context.updateSoundLevelInfo('max', maxval)

		node.attrdict['atag'] = tagname
		node.attrdict['mimetype'] = 'animate/%s' % tagname

		# synthesize a name for the channel
		# intrenal for now so no conflicts
#		chname = 'animate%s' % node.GetUID()
#		node.attrdict['channel'] = chname


		# add this node to the tree if it is possible
		# else keep it for later fix
		node.targetnode = None
		if targetnode:	
			node.targetnode = targetnode
		elif targetid:
			node.__targetid = targetid
			self.__animatenodes.append((node, self.lineno))

		# add to context an internal channel for this node
#		self.__context.addinternalchannels( [(chname, 'animate', node.attrdict), ] )

		editGroup = attributes.get('editGroup')
		if features.editor and editGroup is not None:
			# A animpar mmnode instance will be created from FixAnimatePar method
			parset = self.__animateParSet.get(editGroup)
			if parset is None:
				animatePar = []
				self.__animateParSet[editGroup] = animatePar, self.__container
			else:
				animatePar, ct = parset
			animatePar.append((node, self.lineno))
		self.__container = node
				
	def EndAnimateNode(self):
		self.__container = self.__container.GetParent()

	def Recurse(self, root, *funcs):
		if root.type != 'foreign':
			for func in funcs:
				func(root)
		for node in root.GetChildren():
			if node.type == 'comment':
				continue
			apply(self.Recurse, (node,) + funcs)

	def FixAssets(self, root):
		is_assets = root.type == 'assets'
		for node in root.GetChildren()[:]:
			if is_assets:
				node.Extract()
				self.__context.addasset(node)
			else:
				self.FixAssets(node)
		if is_assets:
			# remove and destroy node
			root.Extract()
			root.Destroy()

	def FixForceChild(self, node):
		if node.GetType() not in ('par', 'excl', 'seq'):
			return
		forcechild, lineno = node.__forcechild
		del node.__forcechild
		if forcechild is None:
			return
		if forcechild == '':
			self.syntax_error('empty project_forcechild attribute not allowed', lineno)
			return
		if not self.__nodemap.has_key(forcechild):
			self.syntax_error('unknown name for project_forcechild attribute', lineno)
			return
		asset = self.__nodemap[forcechild]
		if asset not in self.__context.getassets():
			self.syntax_error('project_forcechild attribute does not refer to an asset', lineno)
			return
		node.attrdict['project_forcechild'] = asset.GetUID()

	def FixSizes(self):
		self.__cssIdTmpList = []
		self.Recurse(self.__root, self.__fixMediaPos)
			
	def __fixMediaPos(self, node):
		if node.GetType() not in mediatypes:
			return
		channel = node.GetChannel()
		if channel is None:
			return
		if not ChannelMap.isvisiblechannel(channel.get('type')):
			return

		region = channel.GetLayoutChannel()
		if region is None:
			return
		regCssId = region.getCssId()
		if regCssId is None:
			return
		cssResolver = self.__context.cssResolver
		subRegCssId = node.getSubRegCssId()
		mediaCssId = node.getMediaCssId()
		if subRegCssId is None or mediaCssId is None:
			return
		self.__cssIdTmpList.append(subRegCssId)
		self.__cssIdTmpList.append(mediaCssId)
		cssResolver.link(subRegCssId, regCssId)	
		cssResolver.link(mediaCssId, subRegCssId)			

	def FixSyncArcs(self, node):
		save_lineno = self.lineno
		for attr, val, lineno in node.__syncarcs:
			self.lineno = lineno
			self.SyncArc(node, attr, val)
		self.lineno = save_lineno
		del node.__syncarcs

	def FixAnimatePar(self):
		# for each set
		for editGroup, (animatepar, container) in self.__animateParSet.items():
			errorMsg = None
			keyTimes = None
			posValues = None
			widthValues = None
			heightValues = None
			bgcolorValues = None
			end = None
			for node, lineno in animatepar:
				attributes = node.attrdict
				
				tagName = attributes.get('atag')
				
				# check/finish parsing attributes. Accept only one partern
				# key times
				times = attributes.get('keyTimes')
				if times is not None:
					if len(times) < 2:
						errorMsg = 'bad keyTimes attribute'
						break
					if keyTimes is None:
						keyTimes = times
					else:
						# times has to be the same
						if len(times) != len(keyTimes):
							errorMsg = 'imcompatible keyTimes attribute'
							break
						for ind in range(len(times)):
							if times[ind] != keyTimes[ind]:
								errorMsg = 'imcompatible keyTimes attribute'
								break
						if errorMsg:
							break
				else:
					# no key times
					errorMsg = 'no keyTimes attribute'
					break

				if keyTimes is not None:
					keyTimesLen = len(keyTimes)

				# values				
				values = attributes.get('values')
				if values is not None:
					if tagName == 'animateMotion':
						if posValues is not None:
							# already exist
							errorMsg = 'duplicated animateMotion'
							break
						try:
							pos = self.__strToPosList(values)
						except:
							errorMsg = 'bad values attribute'
							break
						if len(pos) != keyTimesLen:
							# invalid size
							errorMsg = 'incompatible values number'
							break
						posValues = pos
					elif tagName == 'animateColor' and attributes.get('attributeName') == 'backgroundColor':
						if bgcolorValues is not None:
							# already exist
							errorMsg = 'duplicated animateColor'
							break
						try:
							bgcolor = self.__strToColorList(values)
						except:
							errorMsg = 'bad values attribute'
							break
						if len(bgcolor) != keyTimesLen:
							# invalid size
							errorMsg = 'incompatible values number'
							break
						bgcolorValues = bgcolor
					elif tagName == 'animate':
						attributeName = attributes.get('attributeName')
						if attributeName == 'width':							
							if widthValues is not None:
								# already exist
								errorMsg = 'duplicated animate width'
								break
							try:
								width = self.__strToIntList(values)
							except:
								errorMsg = 'bad values attribute'
								break
							if len(width) != keyTimesLen:
								# invalid size
								errorMsg = 'incompatible values number'
								break
							widthValues = width
						elif attributeName == 'height':							
							if heightValues is not None:
								# already exist
								errorMsg = 'duplicated animate height'
								break
							try:
								height = self.__strToIntList(values)
							except:
								errorMsg = 'bad values attribute'
								break
							if len(height) != keyTimesLen:
								# invalid size
								errorMsg = 'incompatible values number'
								break
							heightValues = height
						else:
							# no supported attribute name
							errorMsg = 'attributeName not supported'
							break
					else:
						# no supported tag, shouldn't happen
						errorMsg = 'animate type not supported'
						break
				else:
					# no values
					errorMsg = 'no values attribute'
					break
				
				# end attribute
				# XXX to do

			# for accept only animate group containing all geometry attributes
			if not errorMsg and not (posValues and widthValues and heightValues):
				errorMsg = 'incompatible set of attributes'
			
			if errorMsg:
				self.syntax_error('bad group of animate nodes:%s' % errorMsg, lineno)
			else:
				ctx = self.__context
				# transfert the set of animate nodes to a animpar node 
				for node, lineno in animatepar:
					node.Extract()

				# create the node
				node = ctx.newnode('animpar')
				container._addchild(node)

				if not features.SEPARATE_ANIMATE_NODE in features.feature_set:
					container.attrdict['animated'] = 1
				
				attrdict = node.attrdict
				
				leftValues = []
				topValues = []
				if posValues is not None:
					for pos in posValues:
						left, top = pos
						leftValues.append(left)
						topValues.append(top)

				animvals = []
				for time in keyTimes:
					animvals.append((time, {}))
				
				for values, aname in ((leftValues, 'left'), (topValues, 'top'), \
								  (widthValues, 'width'), (heightValues, 'height'),
								  (bgcolorValues, 'bgcolor')):
					if values is not None:
						for ind in range(len(values)):
							t, v = animvals[ind]
							v[aname] = values[ind]
								
				attrdict['animvals'] = animvals

		del self.__animateParSet

	def FixBaseWindow(self):
		xCurrent = 0
		yCurrent = 0
		for ch in self.__context.getviewports():
			ch['winpos'] = (xCurrent, yCurrent)
			xCurrent = xCurrent+20
			yCurrent = yCurrent+20

			cssId = ch.getCssId()
			self.__context.cssResolver.setRawAttrs(cssId, [('width', ch.get('width')),
								       ('height',ch.get('height'))])
			# if not width or height specified, guess it
			width, height = self.__context.cssResolver.getPxGeom(ch.getCssId())
			# always fix the pixel geometry value for viewport.
			self.__context.cssResolver.setRawAttrs(cssId, [('width', width),
								       ('height', height)])
##			ch['width'] = width
##			ch['height'] = height

		# cleanup
		for cssId in self.__cssIdTmpList:
			self.__context.cssResolver.unlink(cssId)
		self.__cssIdTmpList = None

	def FixLayouts(self):
		if not self.__layouts:
			return
		layouts = self.__context.layouts
		for layout, regions in self.__layouts.items():
			layouts[layout] = regions

	def FixLinks(self):
		hlinks = self.__context.hyperlinks
		for node, url in self.__links:
			href, tag = MMurl.splittag(url)
			if not href:
				# link intra document
				if not self.__nodemap.has_key(tag):
					self.warning("unknown node id `%s'" % tag)
					continue
				hlinks.addlink((node, self.__nodemap[tag], DIR_1TO2))
			else:
				# external link
				hlinks.addlink((node, url, DIR_1TO2))

	def FixAnimateTargets(self):
		for node, lineno in self.__animatenodes:
			targetid = node.__targetid
			del node.__targetid
			mmobj = None
			if self.__nodemap.has_key(targetid):
				node.targetnode =  self.__nodemap.get(targetid)
			elif self.__context.channeldict.has_key(targetid):
				node.targetnode = self.__context.channeldict.get(targetid)
			else:
				self.warning("unknown targetElement `%s'" % targetid, lineno)
		del self.__animatenodes

	def parseQTAttributeOnSmilElement(self, attributes):
		for key, val in attributes.items():
			if key == 'time-slider':
				internalval = self.parseEnumValue(key, val)
				if internalval is not None:
					self.__context.attributes['qttimeslider'] = internalval
				del attributes[key]
			elif key == 'autoplay':
				internalval = self.parseEnumValue(key, val)
				if internalval is not None:
					self.__context.attributes['autoplay'] = internalval
				del attributes[key]
			elif key == 'chapter-mode':
				internalval = self.parseEnumValue(key, val)
				if internalval is not None:
					self.__context.attributes['qtchaptermode'] = internalval
				del attributes[key]
			elif key == 'next':
				if val is not None:
					val = MMurl.basejoin(self.__base, val)
					val = self.__context.findurl(val)
					self.__context.attributes['qtnext'] = val
				del attributes[key]
			elif key == 'immediate-instantiation':
				internalval = self.parseEnumValue(key, val)
				if internalval is not None:
					self.__context.attributes['immediateinstantiation'] = internalval
				del attributes[key]

	# methods for start and end tags

	__keep_ns = {GRiNSns:0, QTns:0, RP9ns:0}
	__smil2_ns = {}
	for __x in SMIL2ns: __smil2_ns[__x] = 0
	del __x
	def __fix_attributes(self, ns, tagname, attributes):
		# fix up attributes by removing namespace qualifiers.
		# this also tests for the attributes that are
		# specified in multiple namespaces.
		if ns:
			if self.__keep_ns.has_key(ns): # ns in (GRiNSns, QTns, RP9ns)
				pass
			elif self.__smil2_ns.has_key(ns): # ns in SMIL2ns
				ns = ''
			else:
				mod = ''
				for sns in SMIL2ns:
					if ns[:len(sns)] == sns:
						mod = ns[len(sns):]
						ns = ''
						break
		if ns:
			tag = ns + ' ' + tagname
		else:
			tag = tagname
		for key, val in attributes.items():
			# re-encode attribute value using document encoding
			try:
				uval = unicode(val, self.__encoding)
			except UnicodeError:
				self.syntax_error("bad encoding for attribute value")
				del attributes[key]
				continue
			except LookupError:
				self.syntax_error("unknown encoding")
				del attributes[key]
				continue
			try:
				val = uval.encode('iso-8859-1')
			except UnicodeError:
				self.syntax_error("character not in Latin1 character range")
				del attributes[key]
				continue

			nsattr = key.split(' ')
			mod = ''
			if len(nsattr) == 2:
				ans, attr = nsattr
				if self.__keep_ns.has_key(ans): # ans in (GRiNSns, QTns, RP9ns)
					pass
				elif self.__smil2_ns.has_key(ans): # ans in SMIL2ns
					ans = ''
				else:
					mod = ''
					for sns in SMIL2ns:
						if ans[:len(sns)] == sns:
							mod = ans[len(sns):]
							ans = ''
							break
			else:
				ans = ''
				attr = key
			if self._attributes.has_key(tagname):
				adict = self._attributes[tagname]
			else:
				adict = self._attributes.get(tag, {})
			if ans:
				if not adict.has_key(ans + ' ' + attr):
					self.syntax_error("unknown attribute `%s' in namespace `%s' on element `%s'" % (attr, ans, tagname))
					del attributes[key]
					continue
			else:
				if not adict.has_key(attr) and (not ns or not adict.has_key(ns+' '+attr)):
					self.syntax_error("unknown attribute `%s' on element `%s'" % (attr, tagname))
					del attributes[key]
					continue
			if mod:
				mods = ATTRIBUTES.get(attr)
				if type(mods) is type({}):
					tags = mods.get(mod, [])
					if tags is not None and tagname not in tags:
						self.syntax_error("attribute `%s' on element `%s' not in module `%s'" % (attr, tagname, mod))
						del attributes[key]
						continue
				else:
					if mod not in mods:
						self.syntax_error("attribute `%s' on element `%s' not in module `%s'" % (attr, tagname, mod))
						del attributes[key]
						continue

			mods = ATTRIBUTES.get(attr)
			if not ns and not ' ' in tagname and not ans and mods:
				if type(mods) is type({}):
					for mod, elems in mods.items():
						if settings.MODULES.get(mod) and (elems is None or tagname in elems):
							break
					else:
						# silently ignore attribute in unsupported module
						if not features.editor:
							self.warning("Ignoring attribute `%s' in element `%s' in unsupported module%s %s" % (key, tagname, (len(mods) > 1 and 's') or '', ' '.join(mods.keys())), self.lineno)
						if __debug__:
							print 'silently ignore attribute',tagname,key,ans,mods
						del attributes[key]
						continue
				else:
					for mod in mods:
						if settings.MODULES.get(mod):
							break
					else:
						# silently ignore attribute in unsupported module
						if not features.editor:
							self.warning("Ignoring attribute `%s' in element `%s' in unsupported module%s %s" % (key, tagname, (len(mods) > 1 and 's') or '', ' '.join(mods)), self.lineno)
						if __debug__:
							print 'silently ignore attribute',tagname,key,ans,mods
						del attributes[key]
						continue

			if attr != key and attributes.has_key(attr):
				self.syntax_error("duplicate attribute `%s' in different namespaces" % attr)
				del attributes[key]
				continue
			del attributes[key]
			attributes[attr] = val

	def __checkid(self, attributes, defaultPrefixId='id', checkid = 1):
		# Check the ID of an element.  This checks that the ID
		# is valid syntactically, and that the ID is unique.
		id = attributes.get('id')
		if id is not None:
			if checkid:
				res = xmllib.tagfind.match(id)
				if res is None or res.end(0) != len(id):
					self.syntax_error("illegal ID value `%s'" % id)
			if self.__ids.has_key(id):
				self.syntax_error('non-unique id %s' % id)
				id = self.__mkid(defaultPrefixId)
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
		if __debug__:
			if parsedebug: print 'start smil', attributes
		ns = self.getnamespace().get('')
		if ns is None or ns == SMIL1:
			self.__context.attributes['project_boston'] = 0
		elif ns in SMIL2ns:
			self.__context.attributes['project_boston'] = 1
		if self.__context.attributes.get('project_boston') == 0:
			for attr in attributes.keys():
				if attr != 'id':
					self.syntax_error('body attribute %s not compatible with SMIL 1.0' % attr)
					if not features.editor:
						del attributes[attr]
					else:
						self.__context.attributes['project_boston'] = 1
		id = self.__checkid(attributes)
		if self.__seen_smil:
			self.error('more than 1 smil tag', self.lineno)
		self.__seen_smil = 1
		self.__in_smil = 1
		if features.compatibility == features.QT:
			self.parseQTAttributeOnSmilElement(attributes)
		self.NewContainer('seq', attributes)
		self.__set_defaultregpoints()
		
	def __check_accesskey(self, node, keys, attr, event):
		newarcs = []
		list = node.attrdict.get(attr, [])
		for arc in list:
			if arc.accesskey is not None:
				self.__have_accesskey = self.__have_accesskey - 1
				for k, a in keys:
					if arc.accesskey == k:
						newarc = MMNode.MMSyncArc(node, event, srcnode = a, event = 'activateEvent', delay = arc.delay)
						newarcs.append(newarc)
		if newarcs:
			node.attrdict[attr] = list + newarcs

	def __fix_accesskey(self, node, keys):
		if self.__have_accesskey <= 0:
			return
		self.__check_accesskey(node, keys, 'beginlist', 'begin')
		self.__check_accesskey(node, keys, 'endlist', 'end')
		for c in node.GetChildren():
			self.__fix_accesskey(c, keys)

	def __readskin(self):
		import parseskin
		import Sizes
		self.__skin = None
		skin = settings.get('skin')
		if not skin:
			return
		try:
			f = MMurl.urlopen(skin)
			dict = parseskin.parsegskin(f)
			f.close()
		except parseskin.error, msg:
			self.warning('error parsing skin description file')
			return
		if dict.has_key('image'):
			image = MMurl.basejoin(skin, dict['image'])
			width, height = Sizes.GetSize(image)
			if width == 0 or height == 0:
				self.warning('error getting skin image dimensions')
				return
			dict['width'] = width
			dict['height'] = height
		settings.read_components_from_skin(dict)
		if dict.has_key('display'):
			apply(settings.setScreenSize, dict['display'][1][2:4])
		self.__skin = dict

	def __fixskin(self):
		dict = self.__skin
		if not dict or not dict.has_key('image'): # presence of image implies presence of display
			return
		skin = settings.get('skin')
		ctx = self.__context
		oldroot = self.__root
		vp = ctx.getviewports()[0] # we already know there's exactly one
		top = ctx.newviewport('The Skin', -1, 'layout')
		top.addOwner(OWNER_DOCUMENT)
		reg = ctx.newchannel('Skin Image', -1, 'layout')
		top._addchild(reg)
		root = ctx.newnode('par')
		root.__forcechild = None, 0
		img = ctx.newnode('ext')
		root._addchild(img)
		img.attrdict['file'] = MMurl.basejoin(skin, dict['image'])
		width = dict['width']
		height = dict['height']
		top['width'] = reg['width'] = width
		top['height'] = reg['height'] = height
		ctx.cssResolver.setRawAttrs(top.getCssId(), [('width', width), ('height', height)])
		ctx.cssResolver.setRawAttrs(reg.getCssId(), [('width', width), ('height', height)])
		ctx.cssResolver.setRawAttrs(img.getSubRegCssId(), [])
		ctx.cssResolver.setRawAttrs(img.getMediaCssId(), [])
		img.attrdict['duration'] = -1
		img.attrdict['channel'] = 'Skin Image'
		if dict.has_key('displayimage'):
			import Sizes
			image = MMurl.basejoin(skin, dict['displayimage'])
			width, height = Sizes.GetSize(image)
			if width == 0 or height == 0:
				self.warning('error getting skin displayimage dimensions')
			else:
				r = ctx.newnode('par')
				r.__forcechild = None, 0
				r._addchild(oldroot)
				i = ctx.newnode('ext')
				r._addchild(i)
				i.attrdict['file'] = MMurl.basejoin(skin, dict['displayimage'])
				i.attrdict['regAlign'] = 'center'
				i.attrdict['regPoint'] = 'center'
				i.attrdict['channel'] = 'Skin Area'
				coords = dict['display'][1]
				i.attrdict['width'] = width
				i.attrdict['left'] = (coords[2] - width) / 2
				i.attrdict['height'] = height
				i.attrdict['top'] = (coords[3] - height) / 2
				cssattrs = [('left',(coords[2] - width) / 2), ('width', width), ('top', (coords[3] - height) / 2), ('height', height)]
				ctx.cssResolver.setRawAttrs(i.getSubRegCssId(), cssattrs)
				ctx.cssResolver.setRawAttrs(i.getMediaCssId(), cssattrs)
				r.SMILidmap = oldroot.SMILidmap
				del oldroot.SMILidmap
				oldroot = r
		beginlist = []
		endlist = []
		keys = []		# list of accesskey keys
		for key, val in dict.items():
			if key in ('image', 'width', 'height', 'component', 'displaybgcolor', 'displayimage'):
				continue
			if key == 'display':
				coords = val[1]
				lcd = ctx.newchannel('Skin Area', -1, 'layout')
				reg._addchild(lcd)
				lcd['left'] = coords[0]
				lcd['top'] = coords[1]
				lcd['width'] = coords[2]
				lcd['height'] = coords[3]
				lcd['showBackground'] = 'whenActive'
				lcd['bgcolor'] = dict.get('displaybgcolor', vp.attrdict.get('bgcolor') or (0,0,0))
				lcd['transparent'] = 0
				settings.setScreenSize(coords[2], coords[3])
				ctx.cssResolver.setRawAttrs(lcd.getCssId(), [('left', coords[0]), ('top', coords[1]), ('width', coords[2]), ('height', coords[3])])
				if settings.get('centerskin') and (vp.has_key('width') or vp.has_key('height')):
					lcd2 = ctx.newchannel('Display Area', -1, 'layout')
					lcd._addchild(lcd2)
					cssattrs = []
					if vp.has_key('width'):
						lcd2['width'] = vp['width']
						lcd2['left'] = (coords[2] - vp['width']) / 2
						cssattrs.append(('width', vp['width']))
						cssattrs.append(('left', (coords[2] - vp['width']) / 2))
					if vp.has_key('height'):
						lcd2['height'] = vp['height']
						lcd2['top'] = (coords[3] - vp['height']) / 2
						cssattrs.append(('height', vp['height']))
						cssattrs.append(('top', (coords[3] - vp['height']) / 2))
					lcd2['transparent'] = 1
					ctx.cssResolver.setRawAttrs(lcd2.getCssId(), cssattrs)
					lcd = lcd2
				continue
			# key in ['open','play','pause','stop','exit','skin','tab','key']
			for val in val:
				a = ctx.newnode('anchor')
				a.attrdict['tabindex'] = -1 # keep out of tabbing order
				if val[0] == 'rocker':
					arc = MMNode.MMSyncArc(a, 'begin', accesskey = val[1], delay = 0)
					a.attrdict['beginlist'] = [arc]
					a.attrdict['actuate'] = 'onLoad'
				else:
					a.attrdict['ashape'] = val[0]
					coords = val[1]
					if val[0] == 'rect':
						a.attrdict['acoords'] = [coords[0],coords[1],coords[0]+coords[2],coords[1]+coords[3]]
					else:
						a.attrdict['acoords'] = coords
				img._addchild(a)
				if key in ('play', 'toggle'):
					arc = MMNode.MMSyncArc(oldroot, 'begin', srcnode = a, event = 'activateEvent', delay = 0)
					beginlist.append(arc)
				elif key in ('stop', 'toggle'):
					arc = MMNode.MMSyncArc(oldroot, 'end', srcnode = a, event = 'activateEvent', delay = 0)
					endlist.append(arc)
				elif key in ('pause', 'open', 'exit', 'tab', 'activate', 'skin'):
					self.__links.append((a, 'grins:%s()' % key))
				elif key == 'key':
					keys.append((val[2], a))
		if keys:
			self.__fix_accesskey(oldroot, keys)
		arc = MMNode.MMSyncArc(oldroot, 'begin', srcnode = 'syncbase', delay = 0)
		beginlist.append(arc)
		oldroot.attrdict['beginlist'] = beginlist
		oldroot.attrdict['endlist'] = endlist
		oldroot.attrdict['restart'] = 'whenNotActive'
		oldroot.removeOwner(OWNER_DOCUMENT)
		root._addchild(oldroot)
		assets = []
		for c in oldroot.children:
			if c.type == 'assets':
				assets.append(c)
			for c in assets:
				c.Extract()
				root._addchild(c)
		root.SMILidmap = oldroot.SMILidmap
		del oldroot.SMILidmap
		self.__root = root
		for r in vp.GetChildren()[:]:
			r.Extract()
			lcd._addchild(r)
		vp.Destroy()

	def end_smil(self):
		ctx = self.__context
		if __debug__:
			if parsedebug: print 'end smil'
		self.__in_smil = 0
		if not self.__root:
			self.error('empty document', self.lineno)
		if not ctx.attributes.get('project_boston') and \
		   not ctx.getviewports():
			self.__newTopRegion()
		self.Recurse(self.__root, self.FixSyncArcs)
		if not features.editor and self.__skin and len(ctx.getviewports()) == 1:
			self.__fixskin()
		self.FixLayouts()
		self.FixSizes()
		self.FixBaseWindow()
		self.FixLinks()
		self.FixAnimateTargets()
		self.FixAnimatePar()
		self.FixAssets(self.__root)
		self.Recurse(self.__root, self.FixForceChild)
		metadata = ''.join(self.__metadata)
		ctx.metadata = metadata
		if self.__viewinfo:
			ctx.setviewinfo(self.__viewinfo)
		MMAttrdefs.flushcache(self.__root)

	# head/body sections

	def start_head(self, attributes):
		if __debug__:
			if parsedebug: print 'start head', attributes
		id = self.__checkid(attributes)
		if not self.__in_smil:
			self.syntax_error('head not in smil')
		self.__in_head = 1

	def end_head(self):
		if __debug__:
			if parsedebug: print 'end head'
		self.__in_head = 0
		if self.__transitions:
			self.__context.addtransitions(self.__transitions.items())

	def start_body(self, attributes):
		if __debug__:
			if parsedebug: print 'start body', attributes
		self.__has_layout = self.__seen_layout > 0
		if not self.__seen_layout:
			self.__seen_layout = LAYOUT_SMIL
		if not self.__in_smil:
			self.syntax_error('body not in smil')
		if self.__seen_body:
			self.error('multiple body tags', self.lineno)
		self.__seen_body = 1
		self.__in_body = 1
		self.__hidden_body = attributes.get('hidden', 'false') == 'true'
		self.AddAttrs(self.__root, attributes)

	def end_body(self):
		if __debug__:
			if parsedebug: print 'end body'
		self.end_seq()
		self.__in_body = 0
		if self.__hidden_body:
			assets = []
			for c in self.__root.children:
				if c.type == 'assets':
					assets.append(c)
			if len(self.__root.children) == len(assets) + 1:
				for c in assets:
					c.Extract()
				root = self.__root
				self.__root = root.children[0] # only remaining child
				self.__root.Extract()
				self.__root.SMILidmap = root.SMILidmap
				del root.SMILidmap
				root.Destroy()
				for c in assets:
					c.AddToTree(self.__root, -1)
		if hasattr(features, 'trial') and features.trial:
			# set a cap on the duration
			if self.__root.attrdict.get('duration', 61) > 60:
				self.__root.attrdict['duration'] = 60

	def start_meta(self, attributes):
		if __debug__:
			if parsedebug: print 'start meta', attributes
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
			name = attributes['name'].lower()
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
			# and description in templates.
			if not self.__new_file:
				# opening an existing file, keep the property
				self.__context.attributes[name] = content
		elif name == 'project_links':
			# space-separated list of external anchors
			self.__context.externalanchors = content.split()
		elif name == 'generator':
			if self.__check_compatibility:
				import DefCompatibilityCheck, windowinterface, version
				if not DefCompatibilityCheck.isCompatibleVersion(content):
					if windowinterface.GetOKCancel('This document was created by "'+content+'"\n\n'+'GRiNS '+version.version+' may be able to read the document, but some features may be lost\n\nDo you wish to continue?',parent=None):
						raise UserCancel
					self.__context.enableSave = 1
			self.__generator = content.lower()
		elif name == 'project_boston':
			content = content == 'on'
			boston = self.__context.attributes.get('project_boston')
			if boston is not None and content != boston:
				self.syntax_error('conflicting project_boston attribute')
			self.__context.attributes['project_boston'] = content
		elif name == 'customcolors':
			color_list = []
			for color in map(string.strip, content.split(',')):
				if color == '':
					color_list.append(None)
				else:
					color = self.__convert_color(color, 'customcolors')
					if color is None:
						break
					color_list.append(color)
			else:
				# all colors were recognized as colors
				self.__context.color_list = color_list
		else:
			if self.__warnmeta:
				self.warning('unrecognized meta property', self.lineno)
			# XXXX <meta> document attributes are always stored as strings, in stead
			# of passing through the Attrdefs mechanism. Too much work to fix, for now.
			self.__context.attributes[name] = content

	def end_meta(self):
		if __debug__:
			if parsedebug: print 'end meta'
		self.__in_meta = 0

	def start_metadata(self, attributes):
		if __debug__:
			if parsedebug: print 'start metadata', attributes
		if self.__context.attributes.get('project_boston') == 0:
			self.syntax_error('metadata element not compatible with SMIL 1.0')
		self.__context.attributes['project_boston'] = 1
		id = self.__checkid(attributes)
		self.setliteral()
		self.__in_metadata = 1

	def end_metadata(self):
		if __debug__:
			if parsedebug: print 'end metadata'
		self.__in_metadata = 0

	# layout section
	def __set_defaultregpoints(self):
		self.__context.addRegpoint('topLeft', {'top':0,'left':0}, 1)
		self.__context.addRegpoint('topMid', {'top':0.0,'left':0.5}, 1)
		self.__context.addRegpoint('topRight', {'top':0.0,'left':1.0}, 1)
		self.__context.addRegpoint('midLeft', {'top':0.5,'left':0.0}, 1)
		self.__context.addRegpoint('center', {'top':0.5,'left':0.5}, 1)
		self.__context.addRegpoint('midRight', {'top':0.5,'left':1.0}, 1)
		self.__context.addRegpoint('bottomLeft', {'top':1.0,'left':0.0}, 1)
		self.__context.addRegpoint('bottomMid', {'top':1.0,'left':0.5}, 1)
		self.__context.addRegpoint('bottomRight', {'top':1.0,'left':1.0}, 1)

	def start_layout(self, attributes):
		if __debug__:
			if parsedebug: print 'start layout', attributes
		id = self.__checkid(attributes)
		if not self.__in_head:
			self.syntax_error('layout not in head')
		if self.__in_meta:
			self.syntax_error('layout in meta')
		if self.__seen_layout and not self.__in_head_switch:
			self.syntax_error('multiple layouts without switch')
		if attributes.get('type', SMIL_BASIC) == SMIL_BASIC:
			if self.__seen_layout > 0:
				# if we've seen SMIL_BASIC/SMIL_EXTENDED
				# already, ignore this one
				self.__in_layout = LAYOUT_UNKNOWN
			else:
				self.__in_layout = LAYOUT_SMIL
			self.__seen_layout = LAYOUT_SMIL
		else:
			self.__in_layout = LAYOUT_UNKNOWN
			if not self.__seen_layout:
				self.__seen_layout = LAYOUT_UNKNOWN
			self.setliteral()

	def end_layout(self):
		if __debug__:
			if parsedebug: print 'end layout'
		self.__in_layout = LAYOUT_NONE

	def __parsePercent(self, val, attr):
		try:
			if val[-1:] == '%':
				val = float(val[:-1]) / 100.0
				if val < 0:
					self.syntax_error('volume with negative %s' % attr)
					val = None
			else:
				self.syntax_error('only relative volume is allowed on %s attribute' % attr)
				val = None
		except ValueError:
			self.syntax_error('invalid %s attribute value' % attr)
			val = None
		return val

	def start_region(self, attributes, checkid = 1):
		if __debug__:
			if parsedebug: print 'start region', attributes
		if not self.__in_layout:
			self.syntax_error('region not in layout')
			return
		if self.__in_layout != LAYOUT_SMIL:
			# ignore outside of smil-basic-layout/smil-extended-layout
			return
		id = self.__checkid(attributes, checkid = checkid)
		# experimental code for switch layout
		self.__elementindex = self.__elementindex+1
		
		if id is None:
			id = '_#internalid%d' % self.__elementindex
			if self.__ids.has_key(id):
				# "cannot happen"
				self.syntax_error('non-unique id %s' % id)
			self.__ids[id] = 0

		# end experimental code for switch layout

		ch = self.__context.newchannel(id, -1, 'layout')
		cssAttrs = []

		self.AddCoreAttrs(ch, attributes)
		self.AddTestAttrs(ch, attributes)

		bg = None		# backgroundColor needs some special handling

		for attr, val in attributes.items():
			if attr == 'id':
				# already dealt with
				pass
			elif attr == 'regionName':
				res = xmllib.tagfind.match(val)
				if res is None or res.end(0) != len(val):
					self.syntax_error("illegal regionName value `%s'" % val)
				else:
					if not self.__regionnames.has_key(val):
						self.__regionnames[val] = []
					self.__regionnames[val].append(id)
					ch['regionName'] = val
			elif attr in ('left', 'width', 'right', 'top', 'height', 'bottom'):
				self.__do_subposition(None, attr, val, ch)
				if ch.has_key(attr):
					cssAttrs.append((attr, ch[attr]))
			elif attr == 'z-index':
				self.__do_z_index(None, attr, val, ch)
			elif attr == 'fit':
				self.__do_enum(None, attr, val, ch)
			elif attr == 'backgroundColor':
				if self.__context.attributes.get('project_boston') == 0:
					self.syntax_error('%s attribute not compatible with SMIL 1.0' % attr)
					if not features.editor:
						continue
				self.__context.attributes['project_boston'] = 1
				bg = self.__convert_color(val, attr)
			elif attr == 'background-color':
				# backgroundColor overrides background-color
				val = self.__convert_color(val, attr)
				if val is not None and bg is None:
					bg = val
			elif attr == 'editBackground':
				res = re.match(' *(?P<r>[0-9]+) +(?P<g>[0-9]+) +(?P<b>[0-9]+)', val) # backward compatibility hack
				if res is not None:
					val = int(res.group('r')), int(res.group('g')), int(res.group('b'))
				else:
					val = self.__convert_color(val, attr)
				if val is not None:
					ch['editBackground'] = val
			elif attr == 'showEditBackground':
				if val in ('0','off'): # backward compatibility hack
					val = 0
				elif val in ('1', 'on'): # backward compatibility hack
					val = 1
				else:
					val = self.parseEnumValue('showEditBackground', val)
				if val is not None:
					ch['showEditBackground'] = val
			elif attr == 'showBackground':
				if self.__context.attributes.get('project_boston') == 0:
					self.syntax_error('%s attribute not compatible with SMIL 1.0' % attr)
					if not features.editor:
						continue
				self.__context.attributes['project_boston'] = 1
				val = self.parseEnumValue('showBackground', val)
				if val is not None:
					ch['showBackground'] = val
			elif attr == 'soundLevel':
				if self.__context.attributes.get('project_boston') == 0:
					self.syntax_error('%s attribute not compatible with SMIL 1.0' % attr)
					if not features.editor:
						continue
				self.__context.attributes['project_boston'] = 1
				val = self.__parsePercent(val, attr)
				if val is not None:
					ch[attr] = val
				self.__context.updateSoundLevelInfo('minmax', val)
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
				ch['chsubtype'] = val
			elif attr == 'collapsed':
				val = self.parseEnumValue(attr, val)
				if val is not None:
					ch.collapsed = val
			elif attr == 'previewShowOption':
				val = self.parseEnumValue(attr, val)
				if val is not None:
					ch[attr] = val
			elif attr == 'xml:lang':
				ch['xmllang'] = val
			elif attr == 'opacity':
				try:
					if val[-1] == '%':
						val = float(val[:-1]) / 100.0
						if val < 0 or val > 1:
							self.syntax_error('opacity value out of range')
							val = None
					else:
						self.syntax_error('only percentage values allowed on %s attribute' % attr)
						val = None
				except ValueError:
					self.syntax_error('invalid %s attribute value' % attr)
					val = None
				if val is not None:
					ch[attr] = val
			else:
				# catch all
				ch[attr] = val
		
		self.__context.cssResolver.setRawAttrs(ch.getCssId(), cssAttrs)

		if bg is not None:
			if bg == 'transparent':
				ch['transparent'] = 1
				ch['bgcolor'] = 0,0,0
			elif bg != 'inherit':
				ch['transparent'] = 0
				ch['bgcolor'] = bg
			else:
				# for inherit value, there is no transparent and bgcolor attribute
				if ch.has_key('transparent'):
					del ch['transparent']
				if ch.has_key('bgcolor'):
					del ch['bgcolor']

		if self.__region is not None:
			if self.__context.attributes.get('project_boston') == 0:
				self.syntax_error('nested regions not compatible with SMIL 1.0')
			self.__context.attributes['project_boston'] = 1
			self.__region._addchild(ch)
		elif self.__viewport is not None:
			self.__viewport._addchild(ch)
		else:
			self.__newTopRegion(id)
			self.__rootLayout._addchild(ch)
		self.__region = ch

	def end_region(self):
		if __debug__:
			if parsedebug: print 'end region'
		if self.__region is None:
			# </region> without <region>
			# error message will be taken care of by XMLparser.
			return
		self.__region = self.__region.GetParent()
		if self.__region.getClassName() == 'Viewport':
			self.__region = None

	def start_root_layout(self, attributes):
		if __debug__:
			if parsedebug: print 'start root_layout', attributes
		if self.__in_layout != LAYOUT_SMIL:
			# ignore outside of smil-basic-layout/smil-extended-layout
			return

		if self.__seen_root_layout:
			self.syntax_error('multiple root-layout elements')
			return
		self.__seen_root_layout = 1

		id = self.__checkid(attributes,'viewport')
		if id is None:
			id = self.__mkid('viewport')

		if self.__rootLayout is not None:
			topLayout = self.__rootLayout
		else:
			if features.editor and features.MULTIPLE_TOPLAYOUT not in features.feature_set and len(self.__context.getviewports()) > 0:
				self.unsupportedfeature_error("multiple top layouts")
			topLayout = self.__context.newviewport(id, -1, 'layout')
			topLayout.addOwner(OWNER_DOCUMENT)
			self.__rootLayout = topLayout
		self.__do_viewport(topLayout, attributes)

	def end_root_layout(self):
		if __debug__:
			if parsedebug: print 'end root_layout'

	def start_viewport(self, attributes):
		if __debug__:
			if parsedebug: print 'start viewport', attributes
		if self.__in_layout != LAYOUT_SMIL:
			# ignore outside of smil-basic-layout/smil-extended-layout
			return
		if self.__context.attributes.get('project_boston') == 0:
			self.syntax_error('viewport not compatible with SMIL 1.0')
			if not features.editor:
				self.setliteral()
				return
		self.__context.attributes['project_boston'] = 1
		id = self.__checkid(attributes,'viewport')
		if id is None:
			id = self.__mkid('viewport')

		if features.editor and features.MULTIPLE_TOPLAYOUT not in features.feature_set and (len(self.__context.getviewports()) > 0 or self.__rootLayout is not None):
			self.unsupportedfeature_error("multiple top layouts")

		topLayout = self.__context.newviewport(id, -1, 'layout')
		topLayout.addOwner(OWNER_DOCUMENT)
		self.__viewport = topLayout
		self.__do_viewport(topLayout, attributes)

	def __do_viewport(self, topLayout, attributes):
		topLayout['transparent'] = 0

		self.AddTestAttrs(topLayout, attributes)
		self.AddCoreAttrs(topLayout, attributes)

		cssAttrs = []

		if not settings.get('centerskin'):
			scrw, scrh = settings.get('system_screen_size')
			changed = 0
			try:
				width = int(attributes.get('width'))
			except:
				width = None
			if width is not None and width > scrw:
				attributes['width'] = `scrw`
				changed = 1
			try:
				height = int(attributes.get('height'))
			except:
				height = None
			if height is not None and height > scrh:
				attributes['height'] = `scrh`
				changed = 1
			if width is not None and height is not None and changed:
				xsc = float(width) / scrw
				ysc = float(height) / scrh
				if xsc > ysc:
					attributes['height'] = `int(height / xsc + .5)`
				elif xsc < ysc:
					attributes['width'] = `int(width / ysc + .5)`

		for attr,val in attributes.items():
			if attr in ('open', 'close'):
				val = self.parseEnumValue(attr, val)
				if val is not None:
					topLayout[attr] = val
			elif attr in ('height', 'width'):
				if val[-2:] == 'px':
					val = val[:-2]
				try:
					val = int(val)
				except ValueError:
					self.syntax_error('viewport %s not a pixel value'%attr)
					val = None
				else:
					if val < 0:
						self.syntax_error('viewport %s not a positive value'%attr)
						val = None
				if val is not None:
					topLayout[attr] = val
					cssAttrs.append((attr, val))
			elif attr in ('background-color', 'backgroundColor'):
				val = self.__convert_color(val, attr)
				if attr == 'backgroundColor' or not topLayout.has_key('bgcolor'):
					if val is not None and \
					   val != 'transparent' and \
					   val != 'inherit':
						topLayout['bgcolor'] = val
					else:
						topLayout['bgcolor'] = 0,0,0
			elif attr == 'resizeBehavior':
				val = self.parseEnumValue(attr, val)
				if val is not None:
					topLayout[attr] = val
			elif attr == 'editBackground':
				res = re.match(' *(?P<r>[0-9]+) +(?P<g>[0-9]+) +(?P<b>[0-9]+)', val) # backward compatibility hack
				if res is not None:
					val = int(res.group('r')), int(res.group('g')), int(res.group('b'))
				else:
					val = self.__convert_color(val, attr)
				if val is not None:
					topLayout[attr] = val
			elif attr == 'showEditBackground':
				if val in ('0','off'): # backward compatibility hack
					val = 0
				elif val in ('1', 'on'): # backward compatibility hack
					val = 1
				else:
					val = self.parseEnumValue(attr, val)
				if val is not None:
					topLayout[attr] = val
			elif attr == 'collapsed':
				val = self.parseEnumValue(attr, val)
				if val is not None:
					topLayout.collapsed = val
			elif attr == 'traceImage':
				if val:
					topLayout['traceImage'] = MMurl.basejoin(self.__base, val)
			elif attr == 'previewShowOption':
				val = self.parseEnumValue(attr, val)
				if val is not None:
					topLayout[attr] = val
##			else:
##				# catch all
##				attrdict[attr] = val
		self.__context.cssResolver.setRawAttrs(topLayout.getCssId(), cssAttrs)

	def end_viewport(self):
		if __debug__:
			if parsedebug: print 'end viewport'
		self.__viewport = None

	def start_regpoint(self, attributes):
		if __debug__:
			if parsedebug: print 'start regpoint', attributes
		if self.__in_layout != LAYOUT_SMIL:
			# ignore outside of smil-basic-layout/smil-extended-layout
			return
		if self.__context.attributes.get('project_boston') == 0:
			self.syntax_error('regPoint not compatible with SMIL 1.0')
			if not features.editor:
				self.setliteral()
				return
		self.__context.attributes['project_boston'] = 1
		# default values
		attrdict = {'regAlign': 'topLeft'}

		id = self.__checkid(attributes)
		if id is None:
			self.warning("no id specified for regPoint element")

		for attr, val in attributes.items():
			if attr == 'id':
				pass	# dealt with already
			elif attr in ('top', 'bottom', 'left', 'right'):
				# for instance, we assume that we can't specify in the same time
				# a top and bottom, a left and right attribute. The SMIL Boston specication
				# is not clear yet about this
				if (attrdict.has_key('top') and attr == 'bottom') or \
				   (attrdict.has_key('bottom') and attr == 'top'):
					self.syntax_error("you can't specify both top and bottom attributes")
				elif (attrdict.has_key('left') and attr == 'right') or \
				     (attrdict.has_key('right') and attr == 'left'):
					self.syntax_error("you can't specify both left and right attributes")
				else:
					try:
						if val[-1] == '%':
							val = float(val[:-1]) / 100.0
						else:
							if val[-2:] == 'px':
								val = val[:-2]
							val = int(val)
						attrdict[attr] = val
					except ValueError:
						self.syntax_error('invalid regPoint attribute value')
			elif attr == 'regAlign':
				val = self.parseEnumValue(attr, val)
				if val is not None:
					attrdict[attr] = val
		if id is not None:
			self.__context.addRegpoint(id, attrdict)

	def end_regpoint(self):
		if __debug__:
			if parsedebug: print 'end regpoint'
		pass

	def start_custom_attributes(self, attributes):
		if __debug__:
			if parsedebug: print 'start custom_attributes', attributes
		if self.__context.attributes.get('project_boston') == 0:
			self.syntax_error('customAttributes not compatible with SMIL 1.0')
			if not features.editor:
				self.setliteral()
				return
		self.__context.attributes['project_boston'] = 1
		id = self.__checkid(attributes)

	def end_custom_attributes(self):
		if __debug__:
			if parsedebug: print 'end custom_attributes'
		if self.__context.attributes.get('project_boston') == 0:
			return
		if not self.__custom_tests:
			self.syntax_error('customAttributes element must contain customTest elements')
		self.__context.addusergroups(self.__custom_tests.items())

	def start_custom_test(self, attributes):
		if __debug__:
			if parsedebug: print 'start custom_test', attributes
		id = self.__checkid(attributes)
		title = attributes.get('title', '')
		u_state = None
		if attributes.has_key('defaultState'):
			u_state = self.parseEnumValue('defaultState', attributes['defaultState'])
		override = None
		if attributes.has_key('override'):
			override = self.parseEnumValue('override', attributes['override'])
		uid = attributes.get('uid', '')
		self.__custom_tests[id] = title, not not u_state, override or 'hidden', uid

	def end_custom_test(self):
		if __debug__:
			if parsedebug: print 'end custom_test'
		pass

	def start_transition(self, attributes):
		if __debug__:
			if parsedebug: print 'start transition', attributes
		id = self.__checkid(attributes)
		dict = {}
		if not attributes.has_key('type'):
			self.syntax_error("required attribute `type' missing in transition element")
			attributes['type'] = 'fade'
		self.AddCoreAttrs(dict, attributes)
		self.AddTestAttrs(dict, attributes)
		for name, value in attributes.items():
			if name == 'id':
				continue
			if name == 'type':
				name = 'trtype'
			elif name == 'subtype':
				pass	# any value is ok
			elif name == 'dur':
				try:
					value = parseutil.parsecounter(value, syntax_error = self.syntax_error, context = self.__context)
				except parseutil.error, msg:
					self.syntax_error(msg)
					continue
			elif name == 'borderColor' and value == 'blend':
				value = (-1,-1,-1)
			elif name in ('borderColor', 'fadeColor'):
				value = self.__convert_color(value, name)
				if value is None:
					continue
			elif name == 'skip-content':
				continue
			elif name == 'coordinated':
				value = self.parseEnumValue(name, value)
				if value is None:
					continue
			elif name == 'clipBoundary':
				value = self.parseEnumValue(name, value)
				if value is None:
					continue
			elif name in ('startProgress', 'endProgress'):
				try:
					value = float(value)
				except:
					self.syntax_error("error parsing value of `%s' attribute" % name)
					continue
			elif name == 'direction':
				value = self.parseEnumValue(name, value)
				if value is None:
					continue
			elif name in ('horzRepeat', 'vertRepeat', 'borderWidth'):
				try:
					value = int(value)
				except:
					self.syntax_error("error parsing value of `%s' attribute" % name)
					continue
			else:
				try:
					value = parseattrval(name, value, self.__context)
				except:
					self.syntax_error("error parsing value of `%s' attribute" % name)
					continue
			dict[name] = value
		self.__transitions[id] = dict

	def end_transition(self):
		if __debug__:
			if parsedebug: print 'end transition'
		pass

	def start_layouts(self, attributes):
		if __debug__:
			if parsedebug: print 'start layouts', attributes
		id = self.__checkid(attributes)

	def end_layouts(self):
		if __debug__:
			if parsedebug: print 'end layouts'
		pass

	def start_Glayout(self, attributes):
		if __debug__:
			if parsedebug: print 'start Glayout', attributes
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
		self.__layouts[id] = regions.split()

	def end_Glayout(self):
		if __debug__:
			if parsedebug: print 'end Glayout'
		pass

	def start_viewinfo(self, attributes):
		if __debug__:
			if parsedebug: print 'start viewinfo', attributes
		viewname = attributes.get('view')
		t = attributes.get('top')
		l = attributes.get('left')
		w = attributes.get('width')
		h = attributes.get('height')
		if not viewname or not t or not l or not w or not h:
			self.syntax_error('GRiNS viewinfo misses required attributes')
			return
		try:
			t = int(t)
			l = int(l)
			w = int(w)
			h = int(h)
		except:
			self.syntax_error('error parsing GRiNS viewinfo attribute')
			return
		self.__viewinfo.append((viewname, (l, t, w, h)))

	def end_viewinfo(self):
		if __debug__:
			if parsedebug: print 'end viewinfo'
		pass

	# container nodes

	def start_parexcl(self, ntype, attributes):
		if __debug__:
			if parsedebug: print 'start parexcl', attributes
		id = self.__checkid(attributes)
		# XXXX we ignore sync for now
		self.NewContainer(ntype, attributes)
		if not self.__container:
			return
		self.__container.__endsync = attributes.get('endsync')
		self.__container.__lineno = self.lineno

	def end_parexcl(self, ntype):
		if __debug__:
			if parsedebug: print 'end parexcl'
		node = self.__container
		self.EndContainer(ntype)
		self.__fixendsync(node)

	def __fixendsync(self, node):
		endsync = node.__endsync
		del node.__endsync
		if endsync is not None and node.type in mediatypes:
			if self.__context.attributes.get('project_boston') == 0:
				self.syntax_error("endsync attribute on media element not compatible with SMIL 1.0", node.__lineno)
				if not features.editor:
					return
			self.__context.attributes['project_boston'] = 1
		if endsync is None:
			pass
		elif endsync == 'first':
			node.attrdict['terminator'] = 'FIRST'
		elif endsync == 'last':
			node.attrdict['terminator'] = 'LAST'
		elif endsync == 'all':
			if self.__context.attributes.get('project_boston') == 0:
				self.syntax_error("endsync attribute value `all' not compatible with SMIL 1.0", node.__lineno)
			self.__context.attributes['project_boston'] = 1
			node.attrdict['terminator'] = 'ALL'
		elif endsync == 'media':
			if node.type in ('par', 'excl'):
				self.syntax_error("endsync attribute value `media' not allowed in par and excl", node.__lineno)
			else:
				node.attrdict['terminator'] = 'MEDIA'
		elif endsync == '':
			self.syntax_error("empty endsync attribute value not allowed")
		else:
			res = idref.match(endsync)
			if res is None:
				# SMIL 2 version of endsync Id-value
				if endsync[0] == '\\':
					endsync = endsync[1:]
				id = endsync
				if self.__context.attributes.get('project_boston') == 0:
					self.syntax_error('endsync attribute value not compatible with SMIL 1.0', node.__lineno)
					if not features.editor:
						return
				self.__context.attributes['project_boston'] = 1
			else:
				id = res.group('id')
			if self.__nodemap.has_key(id):
				child = self.__nodemap[id]
				if node.IsTimeChild(child):
					node.attrdict['terminator'] = child.GetRawAttr('name')
					return
			# id not found among the children
			self.warning('unknown idref in endsync attribute', node.__lineno)
		del node.__lineno

	def start_par(self, attributes):
		if __debug__:
			if parsedebug: print 'start par', attributes
		if not settings.MODULES['NestedTimeContainers']:
			if len(filter(lambda x: x.GetType() in ('par','seq'), self.__container.GetPath())) >= 2:
				self.__unsupmods = ['NestedTimeContainers']
				self.unknown_starttag('par', attributes)
				return
		self.start_parexcl('par', attributes)

	def end_par(self):
		if __debug__:
			if parsedebug: print 'end par'
		if self.__container.GetType() == 'foreign':
			self.__container = self.__container.GetParent()
			return
		self.end_parexcl('par')

	def start_seq(self, attributes):
		if __debug__:
			if parsedebug: print 'start seq', attributes
		if not settings.MODULES['NestedTimeContainers']:
			if len(filter(lambda x: x.GetType() in ('par','seq'), self.__container.GetPath())) >= 2:
				self.__unsupmods = ['NestedTimeContainers']
				self.unknown_starttag('seq', attributes)
				return
		id = self.__checkid(attributes)
		self.NewContainer('seq', attributes)

	def end_seq(self):
		if __debug__:
			if parsedebug: print 'end seq'
		if self.__container.GetType() == 'foreign':
			self.__container = self.__container.GetParent()
			return
		self.EndContainer('seq')

	def start_assets(self, attributes):
		if __debug__:
			if parsedebug: print 'start assets', attributes
		id = self.__checkid(attributes)
		# Note that the "assets" nodetype is not known by the
		# rest of GRiNS. The assets nodes will be extracted and
		# destroyed later in FixAssets()
		self.NewContainer('assets', attributes)

	def end_assets(self):
		if __debug__:
			if parsedebug: print 'end assets'
		self.EndContainer('assets')

	def start_excl(self, attributes):
		if __debug__:
			if parsedebug: print 'start excl', attributes
		self.start_parexcl('excl', attributes)

	def end_excl(self):
		if __debug__:
			if parsedebug: print 'end excl'
		node = self.__container
		self.end_parexcl('excl')
		has_prio = has_nonprio = 0
		for c in node.children:
			if c.type == 'prio':
				has_prio = 1
			elif c.type != 'comment':
				has_nonprio = 1
		if has_prio and has_nonprio:
			self.syntax_error('cannot mix priorityClass and other children in excl element')

	__prioattrs = {'higher': ('stop', 'pause'),
		       'peers': ('stop', 'pause', 'defer', 'never'),
		       'lower': ('defer', 'never'),
		       'pauseDisplay': ('disable', 'hide', 'show'),
		       }
	def start_prio(self, attributes):
		if __debug__:
			if parsedebug: print 'start prio', attributes
		id = self.__checkid(attributes)
		if not self.__in_smil:
			self.syntax_error('priorityClass not in smil')
		if self.__in_layout:
			self.syntax_error('priorityClass in layout')
			return
		if self.__container.type not in ('excl', 'prio'):
			return
		node = self.__context.newnode('prio')
		self.__container._addchild(node)
		self.__container = node
		node.__chanlist = {}
		node.__syncarcs = []
		attrdict = node.attrdict
		for attr, val in attributes.items():
			val = val.strip()
			if attr == 'id':
				self.__nodemap[val] = node
				self.__idmap[val] = node.GetSchedParent().GetUID()
				res = namedecode.match(val)
				if res is not None:
					val = res.group('name')
				attrdict['name'] = val
			elif self.__prioattrs.has_key(attr):
				if val in self.__prioattrs[attr]:
					attrdict[attr] = val
				else:
					self.syntax_error("illegal value for `%s' attribute" % attr)
			elif attr in ('abstract', 'copyright', 'title'):
				if val:
					attrdict[attr] = val

	def end_prio(self):
		if __debug__:
			if parsedebug: print 'end prio'
		self.__container = self.__container.GetParent()

	def start_switch(self, attributes):
		if __debug__:
			if parsedebug: print 'start switch', attributes
		id = self.__checkid(attributes)
		if self.__in_head:
			if self.__in_head_switch:
				self.syntax_error('switch within switch in head')
			if self.__in_meta:
				self.syntax_error('switch in meta')
			self.__in_head_switch = 1
		else:
			self.NewContainer('switch', attributes)

	def end_switch(self):
		if __debug__:
			if parsedebug: print 'end switch'
		self.__in_head_switch = 0
		if not self.__in_head:
			self.EndContainer('switch')

	# media items

	def start_ref(self, attributes):
		if __debug__:
			if parsedebug: print 'start ref', attributes
		self.NewNode(None, attributes)

	def end_ref(self):
		if __debug__:
			if parsedebug: print 'end ref'
		self.EndNode()

	def start_text(self, attributes):
		if __debug__:
			if parsedebug: print 'start text', attributes
		self.NewNode('text', attributes)

	def end_text(self):
		if __debug__:
			if parsedebug: print 'end text'
		self.EndNode()

	def start_audio(self, attributes):
		if __debug__:
			if parsedebug: print 'start audio', attributes
		self.NewNode('audio', attributes)

	def end_audio(self):
		if __debug__:
			if parsedebug: print 'end audio'
		self.EndNode()

	def start_img(self, attributes):
		if __debug__:
			if parsedebug: print 'start img', attributes
		self.NewNode('image', attributes)

	def end_img(self):
		if __debug__:
			if parsedebug: print 'end img'
		self.EndNode()

	def start_video(self, attributes):
		if __debug__:
			if parsedebug: print 'start video', attributes
		self.NewNode('video', attributes)

	def end_video(self):
		if __debug__:
			if parsedebug: print 'end video'
		self.EndNode()

	def start_animation(self, attributes):
		if __debug__:
			if parsedebug: print 'start animation', attributes
		self.NewNode('animation', attributes)

	def end_animation(self):
		if __debug__:
			if parsedebug: print 'end animation'
		self.EndNode()

	def start_textstream(self, attributes):
		if __debug__:
			if parsedebug: print 'start textstream', attributes
		self.NewNode('textstream', attributes)

	def end_textstream(self):
		if __debug__:
			if parsedebug: print 'end textstream'
		self.EndNode()

	def start_brush(self, attributes):
		if __debug__:
			if parsedebug: print 'start brush', attributes
		if self.__context.attributes.get('project_boston') == 0:
			self.syntax_error('brush element not compatible with SMIL 1.0')
			if not features.editor:
				self.setliteral()
				return
		self.__context.attributes['project_boston'] = 1
		self.NewNode('brush', attributes)

	def end_brush(self):
		if __debug__:
			if parsedebug: print 'end brush'
		if self.__context.attributes.get('project_boston') == 0:
			return
		self.EndNode()

	# linking

	def start_a(self, attributes):
		if __debug__:
			if parsedebug: print 'start a', attributes
		id = self.__checkid(attributes)
		if self.__in_a:
			self.syntax_error('nested a elements')
		href = attributes.get('href')
		if not href:
			self.syntax_error('anchor with empty HREF or without HREF')
			return
		if href[:1] != '#':
			# external link
			href = '%20'.join(href.split(' '))
			href = MMurl.basejoin(self.__base, attributes['href'])
			if href not in self.__context.externalanchors:
				self.__context.externalanchors.append(href)
		elif features.editor and features.INTERNAL_LINKS not in features.feature_set:
			self.unsupportedfeature_error('internal hyperlinks not supported')

		attrdict = {}
		self.AddLinkAttrs(attrdict, attributes)
		self.__in_a = href, attrdict, id, self.__in_a

	def end_a(self):
		if __debug__:
			if parsedebug: print 'end a'
		if self.__in_a is None:
			# </a> without <a>
			# error message will be taken care of by XMLparser.
			return
		self.__in_a = self.__in_a[-1]

	# parse coordonnees of a shape
	# all string can't be specify in only one regular expression, because we don't know the number of points
	# Instead, there is a first regular expression which parse the first number, then a second which parse
	# the separateur caractere and the next number
	# return value: list of numbers (values expressed in percent or pixel)
	# or None if error

	def __parseCoords(self, data):
		if data is None:
			return
		l = []
		for val in map(string.strip, data.split(',')):
			res = coordre.match(val)
			if res is None:
				self.syntax_error('syntax error in coords attribute')
				return
			pixelvalue, percentvalue = res.group('pixel', 'percent')
			if pixelvalue is not None:
				value = int(pixelvalue)
			else:
				value = float(percentvalue) / 100.0
			l.append(value)
		return l

	def AddLinkAttrs(self, attrdict, attributes):
		attr = 'show'
		if attributes.has_key(attr):
			val = attributes[attr]
			del attributes[attr]
			val = self.parseEnumValue(attr, val)
			if val is not None:
				attrdict[attr] = val
		for attr in ('sourcePlaystate', 'destinationPlaystate', 'external', 'actuate', 'sendTo'):
			if attributes.has_key(attr):
				val = attributes[attr]
				del attributes[attr]
				if self.__context.attributes.get('project_boston') == 0:
					self.syntax_error('%s attribute not compatible with SMIL 1.0' % attr)
				if features.editor:
					self.__context.attributes['project_boston'] = 1		
				if self.__context.attributes.get('project_boston'):
					val = self.parseEnumValue(attr, val)
					if val is not None:
						attrdict[attr] = val
		for attr in ('sourceLevel', 'destinationLevel'):
			if attributes.has_key(attr):
				val = attributes[attr]
				del attributes[attr]
				if self.__context.attributes.get('project_boston') == 0:
					self.syntax_error('%s attribute not compatible with SMIL 1.0' % attr)
				if features.editor:
					self.__context.attributes['project_boston'] = 1		
				if self.__context.attributes.get('project_boston'):
					val = self.__parsePercent(val, attr)
					if val is not None:
						attrdict[attr] = val
		attr = 'accesskey'
		if attributes.has_key(attr):
			val = attributes[attr]
			del attributes[attr]
			if self.__context.attributes.get('project_boston') == 0:
				self.syntax_error('%s attribute not compatible with SMIL 1.0' % attr)
			if features.editor:
				self.__context.attributes['project_boston'] = 1		
			if self.__context.attributes.get('project_boston'):
				if len(val) != 1:
					self.syntax_error('accesskey should be single character')
				else:
					attrdict[attr] = val
		attr = 'tabindex'
		if attributes.has_key(attr):
			val = attributes[attr]
			del attributes[attr]
			self.__do_index(None, attr, val, attrdict)
		attr = 'target'
		if attributes.has_key(attr):
			val = attributes[attr]
			del attributes[attr]
			if self.__context.attributes.get('project_boston') == 0:
				self.syntax_error('%s attribute not compatible with SMIL 1.0' % attr)
			if features.editor:
				self.__context.attributes['project_boston'] = 1		
			if self.__context.attributes.get('project_boston'):
				attrdict[attr] = val

	def start_anchor(self, attributes):
		if __debug__:
			if parsedebug: print 'start anchor', attributes
		id = self.__checkid(attributes)
		if self.__node is None:
			self.syntax_error('anchor not in media object')
			return

		# create the anchor node
		node = self.__context.newnode('anchor')
		self.__container._addchild(node)
		self.__container = node
		node.__syncarcs = []

		if id is not None:
			self.__nodemap[id] = node
			self.__idmap[id] = node.GetUID()
			val = id
			res = namedecode.match(val)
			if res is not None:
				val = res.group('name')
			node.attrdict['name'] = val

		self.AddTestAttrs(node.attrdict, attributes)

		nohref = attributes.get('nohref')
		if nohref is not None:
			if nohref != 'nohref':
				self.syntax_error("illegal value for `nohref` attribute")
				nohref = None
		if not nohref:
			href = attributes.get('href') # None is dest only anchor
		else:
			href = None
		if href is not None and href[:1] != '#':
			href = MMurl.basejoin(self.__base, href)
			href = '%20'.join(href.split(' '))
			if href not in self.__context.externalanchors:
				self.__context.externalanchors.append(href)
		elif href is not None and features.editor and features.INTERNAL_LINKS not in features.feature_set:
			self.unsupportedfeature_error('internal hyperlinks not supported')

		# show, sourcePlaystate and destinationPlaystate parsing
		self.AddLinkAttrs(node.attrdict, attributes)

		# shape attribute
		shape = None
		if attributes.has_key('shape'):
			if self.__context.attributes.get('project_boston') == 0:
				self.syntax_error('shape attribute not compatible with SMIL 1.0')
			if features.editor:
				self.__context.attributes['project_boston'] = 1		
			shape = self.parseEnumValue('shape', attributes['shape'])
			if shape is not None:
				node.attrdict['ashape'] = shape

		# coords attribute
		coords = self.__parseCoords(attributes.get('coords'))

		if coords is not None:
			error = 0
			if shape is None or shape == 'rect':
				if len(coords) != 4:
					self.syntax_error('Invalid number of coordinate values in anchor')
					error = 1
			elif shape == 'poly':
				if (len(coords) < 6) or (len(coords) & 1):
					self.syntax_error('Invalid number of coordinate values in anchor')
					error = 1
				else:
					# if the last coordinate is equal to the first coordinate, we supress the last
					if coords[-2:] == coords[:2]:
						del coords[-2:]
			else:		# shape == 'circle'
				if len(coords) != 3:
					self.syntax_error('Invalid number of coordinate values in anchor')
					error = 1

			if not error:
				node.attrdict['acoords'] = coords

		for attr in ('begin', 'end'):
			val = attributes.get(attr)
			if val is not None:
				node.__syncarcs.append((attr, val, self.lineno))

		if attributes.has_key('fragment'):
			node.attrdict['fragment'] = attributes['fragment']

		if href is not None:
			self.__links.append((node, href))

	def end_anchor(self):
		if __debug__:
			if parsedebug: print 'end anchor'
		self.__container = self.__container.GetParent()

	def start_area(self, attributes):
		if __debug__:
			if parsedebug: print 'start area', attributes
		if self.__context.attributes.get('project_boston') == 0:
			self.syntax_error('area not compatible with SMIL 1.0')
			if not features.editor:
				self.setliteral()
				return
		self.__context.attributes['project_boston'] = 1
		self.start_anchor(attributes)

	def end_area(self):
		if __debug__:
			if parsedebug: print 'end area'
		if self.__context.attributes.get('project_boston') == 0:
			return
		self.end_anchor()

	def start_animate(self, attributes):
		if __debug__:
			if parsedebug: print 'start animate', attributes
		if self.__context.attributes.get('project_boston') == 0:
			self.syntax_error('animate not compatible with SMIL 1.0')
			if not features.editor:
				self.setliteral()
				return
		self.__context.attributes['project_boston'] = 1
		self.NewAnimateNode('animate', attributes)

	def end_animate(self):
		if __debug__:
			if parsedebug: print 'end animate'
		if self.__context.attributes.get('project_boston') == 0:
			return
		self.EndAnimateNode()

	def start_prefetch(self, attributes):
		if __debug__:
			if parsedebug: print 'start prefetch', attributes
		if self.__context.attributes.get('project_boston') == 0:
			self.syntax_error('animate not compatible with SMIL 1.0')
			if not features.editor:
				self.setliteral()
				return
		self.__context.attributes['project_boston'] = 1
		self.NewNode('prefetch', attributes)

	def end_prefetch(self):
		if __debug__:
			if parsedebug: print 'end prefetch'
		if self.__context.attributes.get('project_boston') == 0:
			return
		self.EndNode()

	def start_set(self, attributes):
		if __debug__:
			if parsedebug: print 'start set', attributes
		if self.__context.attributes.get('project_boston') == 0:
			self.syntax_error('set not compatible with SMIL 1.0')
			if not features.editor:
				self.setliteral()
				return
		self.__context.attributes['project_boston'] = 1
		self.NewAnimateNode('set', attributes)

	def end_set(self):
		if __debug__:
			if parsedebug: print 'end set'
		if self.__context.attributes.get('project_boston') == 0:
			return
		self.EndAnimateNode()

	def start_animatemotion(self, attributes):
		if __debug__:
			if parsedebug: print 'start animatemotion', attributes
		if self.__context.attributes.get('project_boston') == 0:
			self.syntax_error('animateMotion not compatible with SMIL 1.0')
			if not features.editor:
				self.setliteral()
				return
		self.__context.attributes['project_boston'] = 1
		self.NewAnimateNode('animateMotion', attributes)

	def end_animatemotion(self):
		if __debug__:
			if parsedebug: print 'end animatemotion'
		if self.__context.attributes.get('project_boston') == 0:
			return
		self.EndAnimateNode()

	def start_transitionfilter(self, attributes):
		if __debug__:
			if parsedebug: print 'start transitionfilter', attributes
		if self.__context.attributes.get('project_boston') == 0:
			self.syntax_error('animateMotion not compatible with SMIL 1.0')
			if not features.editor:
				self.setliteral()
				return
		self.__context.attributes['project_boston'] = 1
		value = attributes.get('type')
		if value:
			attributes['trtype'] = value
			del attributes['type']
		value = attributes.get('subType')
		if value:
			self.syntax_error('transitionFilter attribute subType should be subtype')
			attributes['subtype'] = value
			del attributes['subType']

		value = attributes.get('fadeColor')
		if value:
			attributes['fadeColor'] = value
		self.NewAnimateNode('transitionFilter', attributes)

	def end_transitionfilter(self):
		if __debug__:
			if parsedebug: print 'end transitionfilter'
		if self.__context.attributes.get('project_boston') == 0:
			return
		self.EndAnimateNode()

	def start_animatecolor(self, attributes):
		if __debug__:
			if parsedebug: print 'start animatecolor', attributes
		if self.__context.attributes.get('project_boston') == 0:
			self.syntax_error('animateColor not compatible with SMIL 1.0')
			if not features.editor:
				self.setliteral()
				return
		self.__context.attributes['project_boston'] = 1
		self.NewAnimateNode('animateColor', attributes)

	def end_animatecolor(self):
		if __debug__:
			if parsedebug: print 'end animatecolor'
		if self.__context.attributes.get('project_boston') == 0:
			return
		self.EndAnimateNode()

	def start_param(self, attributes):
		if __debug__:
			if parsedebug: print 'start param', attributes
		if self.__context.attributes.get('project_boston') == 0:
			self.syntax_error('param not compatible with SMIL 1.0')
			if not features.editor:
				self.setliteral()
				return
		self.__context.attributes['project_boston'] = 1
		id = self.__checkid(attributes)
		vtype = attributes.get('valuetype', 'data')
		if vtype not in ('data', 'ref', 'object'):
			self.syntax_error('illegal value for valuetype attribute')
			return
		value = attributes.get('value')
		name = attributes.get('name')
		if not name:
			return
		if vtype != 'data':
			return
		if name == 'fgcolor':
			fg = self.__convert_color(value, name)
			if fg is not None:
				self.__node.attrdict[name] = fg
		# Real extensions
		if name == 'bitrate':
			try:
				bitrate = int(value)
			except:
				self.syntax_error('bad value for bitrate param value')
			else:
				self.__node.attrdict['strbitrate'] = bitrate
		if name == 'reliable':
			reliable = self.parseEnumValue(name, value)
			if reliable is not None:
				self.__node.attrdict['reliable'] = reliable

	def end_param(self):
		if __debug__:
			if parsedebug: print 'end param'
		pass			# XXX needs to be implemented

	# other callbacks

	def handle_xml(self, encoding, standalone):
		if not encoding:
			encoding = 'utf-8'
		self.__encoding = encoding.lower()

	__whitespace = re.compile(_opS + '$')
	def handle_data(self, data):
		if self.__in_metadata:
			self.__metadata.append(data)
			return
		if self.__in_layout != LAYOUT_UNKNOWN:
			res = self.__whitespace.match(data)
			if not res:
				self.syntax_error("non-white space content `%s'" % data)

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
		elif pubid == SMILBostonPubid and syslit in SMIL2DTDs:
			# SMIL Boston
			self.__context.attributes['project_boston'] = 1

	def handle_proc(self, name, data):
		self.warning('ignoring processing instruction %s' % name, self.lineno)

	def handle_comment(self, data):
		if data == EVALcomment:
			return
		if self.__container is not None:
			node = self.__context.newnode('comment')
			self.__container._addchild(node)
			node.values = data.split('\n')
		else:
			self.__context.comment = self.__context.comment + data

	# Example -- handle cdata, could be overridden
	def handle_cdata(self, cdata):
		if self.__in_layout != LAYOUT_UNKNOWN:
			self.warning('ignoring CDATA', self.lineno)

	# catch all

	def unknown_starttag(self, tag, attrs):
		if not features.editor:
			if self.__unsupmods:
				self.warning("Ignoring element `%s' in unsupported module%s %s" % (tag, (len(self.__unsupmods) > 1 and 's') or '', ' '.join(self.__unsupmods)), self.lineno)
			else:
				self.warning("Ignoring unknown element `%s'" % tag, self.lineno)
		if __debug__:
			if parsedebug: print 'start foreign', tag, attrs
		if self.__in_body:
			node = self.__context.newnode('foreign')
			self.__container._addchild(node)
			node.attrdict.update(attrs)
			tag = tag.split()
			node.attrdict['elemname'] = tag[-1]
			if len(tag) == 2:
				node.attrdict['namespace'] = tag[0]
			self.__container = node

	def unknown_charref(self, ref):
		self.warning('ignoring unknown char ref %s' % ref, self.lineno)

	def unknown_entityref(self, ref):
		self.warning('ignoring unknown entity ref %s' % ref, self.lineno)

	# non-fatal errors

	def syntax_error(self, msg, lineno = None):
		line = lineno or self.lineno
		msg = 'syntax error on line %d: %s' % (line, msg)
		if self.__printfunc is not None:
			self.__printdata.append(msg)
			if __debug__:
				if parsedebug: print msg
		else:
			print msg
		if line is not None:
			line = line-1
		self.__errorList.append((msg, line))
		
	def warning(self, message, lineno = None):
		if lineno is None:
			msg = 'warning: %s' % message
		else:
			msg = 'warning: %s on line %d' % (message, lineno)
		if self.__printfunc is not None:
			self.__printdata.append(msg)
			if __debug__:
				if parsedebug: print msg
		else:
			print msg
		line = lineno
		if line is not None:
			line = lineno-1
		self.__errorList.append((msg, line))

	# fatal errors
	
	def error(self, message, lineno = None):
		if self.__printfunc is None and self.__printdata:
			msg = '\n'.join(self.__printdata) + '\n'
		else:
			msg = ''
		if lineno is None:
			message = 'Unrecoverable error: %s' % message
		else:
			message = 'Unrecoverable error, line %d: %s' % (lineno, message)
		msg = msg + message
		if __debug__:
			if parsedebug: print msg
		line = lineno
		if line is not None:
			line = lineno-1
		self.__errorList.insert(0,(msg, line))
		raise MSyntaxError, msg

	def unsupportedfeature_error(self, message, lineno=None):
		if features.editor and features.UNSUPPORTED_ERROR in features.feature_set:
			self.error('%s not supported in this version.\nYou can use the GRiNS PRO version.' % message, lineno)
		
	def fatalerror(self):
		type, value, traceback = sys.exc_info()
		if self.__printfunc is not None:
			msg = 'unrecoverable error while parsing at line %d: %s' % (self.lineno, str(value))
			if self.__printdata:
				data = '\n'.join(self.__printdata)
				# first 30 lines should be enough
				data = data.split('\n')
				if len(data) > 30:
					data = data[:30]
					data.append('. . .')
			else:
				data = []
			data.insert(0, msg)
			self.__printfunc('\n'.join(data))
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

	def __convert_color(self, val, attr = None):
		try:
			return colors.convert_color(val)
		except colors.error, msg:
			if attr:
				msg = msg + " for attribute `%s'" % attr
			self.syntax_error(msg)
			return None

	def __strToIntList(self, str):
		vl = []
		for s in str.split(';'):
			if s: 
				vl.append(int(s))
		return vl	

	def __strToPosList(self, str):
		vl = []
		for s in str.split(';'):
			if s: 
				pair = self.__getNumPair(s)
				if pair:
					vl.append(pair)
		return vl	

	def __getNumPair(self, str):
		if not str: return None
		str = str.strip()
		if str[:1] == '(' and str[-1:] == ')':
			str = str[1:-1].strip()
		import tokenizer
		sl = tokenizer.splitlist(str, delims=' ,\t\n\r')
		if len(sl)==2:
			x, y = sl
			return int(x), int(y)
		return None

	def __strToColorList(self, str):
		vl = map(self.__convert_color, str.split(';'))
		return vl

	# the rest is to check that the nesting of elements is done
	# properly (i.e. according to the SMIL DTD)
	def finish_starttag(self, tagname, attrdict, method):
		self.__updateProgressHandler()
		nstag = tagname.split(' ')
		if len(nstag) == 2 and \
		   (nstag[0] in [SMIL1]+SMIL2ns or settings.extensions.has_key(nstag[0])):
			ns, tagname = nstag
		else:
			ns = ''
		if limited.has_key(tagname) and ns not in limited[tagname]:
			self.syntax_error("element `%s' not allowed in namespace `%s'" % (tagname, ns))
		attributes = self._attributes.get(tagname, {})
		if len(self.stack) > 1:
			ptag = self.stack[-2][2]
			nstag = ptag.split(' ')
			if len(nstag) == 2 and \
			   nstag[0] in [SMIL1]+SMIL2ns:
				pns, ptag = nstag
			else:
				pns = ''
			if self.entities.has_key(ptag):
				# parent is SMIL 1.0 entity
				content = self.entities[ptag]
			elif pns and self.entities.has_key(pns + ' ' + ptag):
				content = self.entities[pns + ' ' + ptag]
			else:
				content = []
			if tagname not in content and (not ns or (ns+' '+tagname) not in content):
				self.syntax_error('%s element not allowed inside %s' % (self.stack[-1][0], self.stack[-2][0]))
		elif tagname != 'smil' and len(nstag) == 2 and nstag[1] == 'smil':
			# SMIL in unrecognized namespace
			self.error("element `smil' in unrecognized namespace `%s'" % nstag[0])
		elif tagname != 'smil':
			self.error('outermost element must be "smil"', self.lineno)
		elif ns and self.getnamespace().get('', '') != ns:
			self.error('outermost element must be "smil" with default namespace declaration', self.lineno)
		elif ns and ns == SMIL1:
			pass
		elif ns and ns not in SMIL2ns and ns[-8:] != 'Language':
			self.warning('default namespace should be "%s"' % SMIL2ns[0], self.lineno)
		self.__fix_attributes(ns, tagname, attrdict)
		if self._elements.has_key(tagname):
			method = self._elements[tagname][0]
		if method is not None and (ns or ' ' not in tagname):
			for module in ELEMENTS.get(tagname, []):
				if settings.MODULES.get(module):
					break
			else:
				method = None
				self.__unsupmods = ELEMENTS.get(tagname, [])
		xmllib.XMLParser.finish_starttag(self, tagname, attrdict, method)

	def unknown_endtag(self, tagname):
		self.__updateProgressHandler()
		nstag = tagname.split(' ')
		if len(nstag) == 2 and \
		   (nstag[0] in [SMIL1]+SMIL2ns or settings.extensions.has_key(nstag[0])):
			ns, tagname = nstag
		else:
			ns = ''
		if self._elements.has_key(tagname):
			method = self._elements[tagname][1]
		else:
			method = None
		if method is not None and (ns or ' ' not in tagname):
			for module in ELEMENTS.get(tagname, []):
				if settings.MODULES.get(module):
					break
			else:
				method = None
		if method is not None:
			self.handle_endtag(tagname, method)
		elif self.__in_body and self.__container is not None and self.__container.GetType() == 'foreign':
			self.__container = self.__container.GetParent()

	# update progress bar if needed
	def __updateProgressHandler(self):
		if self.__progressCallback is not None:
			callback, intervalTime = self.__progressCallback
			if intervalTime <= 0 or time.time() > self.__progressTimeToUpdate:
				# determine the next time to update
				if intervalTime > 0:
					self.__progressTimeToUpdate = time.time()+intervalTime
				if self.__nlines:
					# update the handler. 
					callback(float(self.lineno)/self.__nlines)

class SMILMetaCollector(xmllib.XMLParser):
	# Collect the meta attributes from a smil file

	def __init__(self, file=None):
		self.meta_data = {}
		self._elements = {
			'meta': (self.start_meta, None)
		}
		self.__file = file or '<unknown file>'
		self.__encoding = 'utf-8'
		xmllib.XMLParser.__init__(self)

	def close(self):
		xmllib.XMLParser.close(self)
		self.elements = None

	def start_meta(self, attributes):
		if __debug__:
			if parsedebug: print 'start meta', attributes
		name = attributes.get('name')
		content = attributes.get('content')
		if name and content:
			self.meta_data[name] = content

	def syntax_error(self, msg):
		print 'warning: syntax error on line %d: %s' % (self.lineno, msg)

	def handle_xml(self, encoding, standalone):
		if not encoding:
			encoding = 'utf-8'
		self.__encoding = encoding.lower()

	def finish_starttag(self, tagname, attrdict, method):
		nstag = tagname.split(' ')
		if len(nstag) == 2 and \
		   (nstag[0] in [SMIL1, GRiNSns]+SMIL2ns or settings.extensions.has_key(nstag[0])):
			ns, tagname = nstag
		else:
			ns = ''
		if self._elements.has_key(tagname):
			method = self._elements[tagname][0]
			# only fix attrs when we're actuall interested in them
			if method is not None:
				self.__fix_attributes(ns, tagname, attrdict)
		xmllib.XMLParser.finish_starttag(self, tagname, attrdict, method)

	def __fix_attributes(self, ns, tagname, attributes):
		# fix up attributes by removing namespace qualifiers.
		for key, val in attributes.items():
			# re-encode attribute value using document encoding
			try:
				uval = unicode(val, self.__encoding)
			except UnicodeError:
				self.syntax_error("bad encoding for attribute value")
				del attributes[key]
				continue
			except LookupError:
				self.syntax_error("unknown encoding")
				del attributes[key]
				continue
			try:
				val = uval.encode('iso-8859-1')
			except UnicodeError:
				self.syntax_error("character not in Latin1 character range")
				del attributes[key]
				continue

			nsattr = key.split(' ')
			if len(nsattr) == 2:
				ans, attr = nsattr
				if ans in (GRiNSns, QTns, RP9ns):
					pass
				elif ans in SMIL2ns:
					pass
				else:
					for sns in SMIL2ns:
						if ans[:len(sns)] == sns:
							# recognized
							break
					else:
						# not recognized
						attr = key
			else:
				# keep the same
				attr = key

			if attr != key:
				# fix up attribute
				del attributes[key]
				attributes[attr] = val

def ReadMetaData(file):
	p = SMILMetaCollector(file)
	fp = open(file)
	p.feed(fp.read())
	p.close()
	return p.meta_data

def ReadFile(url, printfunc = None, new_file = 0, check_compatibility = 0, progressCallback=None):
	if os.name == 'mac':
		import splash
		splash.splash('loaddoc')	# Show "loading document" splash screen
	rv = ReadFileContext(url, MMNode.MMNodeContext(EditableObjects.EditableMMNode), printfunc, new_file, check_compatibility, progressCallback)
	if os.name == 'mac':
		splash.splash('initdoc')	# and "Initializing document" (to be removed in mainloop)
	return rv

def ReadFileContext(url, context, printfunc = None, new_file = 0, check_compatibility = 0, progressCallback=None):
	p = SMILParser(context, printfunc = printfunc, new_file = new_file, check_compatibility = check_compatibility, progressCallback = progressCallback)
	u = MMurl.urlopen(url)
	if not new_file:
		baseurl = u.geturl()
		i = baseurl.rfind('/')
		if i >= 0:
			baseurl = baseurl[:i+1]	# keep the slash
		else:
			baseurl = None
		context.setbaseurl(baseurl)
	data = u.read()
	u.close()
	# convert Windows CRLF sequences to LF
	data = '\n'.join(data.split('\r\n'))
	# then convert Macintosh CR to LF
	data = '\n'.join(data.split('\r'))
##	import profile
##	if sys.platform == 'wince':
##		import winkernel
##		timer = winkernel.GetTickCount
##	else:
##		timer = None
##	pr = profile.Profile(timer)
##	root = pr.runcall(__doParse, p, data)
##	pr.dump_stats('profile.stats')
	root = __doParse(p, data)
	# XXX keep the original source for the player
	# note: for the editor, always saving the source on the root is not pertinent (
	# it doesn't reflect the real status of the document). Therefore, to the editor
	# the only source to keep is: the source which has generated an error (see MMErrors)
	# XXX: to improve
	root.source = data
	return root

def __doParse(parser, data):
	try:
##		from time import time
##		t0 = time()
		parser.feed(data)
		parser.close()
##		t1 = time()
##		print 'parsed in %g' % (t1-t0)
		root = parser.GetRoot()
		context = root.GetContext()			
	except MSyntaxError:
		# a fatal errors has been occured
		# in this, case the root node is not valid, and we create a fake node just to have
		# the minimum required by TopLevel
		root = parser.MakeRoot('seq', 1)
		context = root.GetContext()
		errors = MMNode.MMErrors('fatal')
		errors.setSource(data)
		errorList = parser.GetErrorList()
		errors.setErrorList(errorList)
		context.setParseErrors(errors)
	else:
		# no fatal error, check if normal errors
		context = root.GetContext()
		errorList = parser.GetErrorList()
		if len(errorList) > 0:
			# there are at least one normal error
			errors = MMNode.MMErrors('normal')
			errors.setSource(data)
			errors.setErrorList(errorList)
			context.setParseErrors(errors)
		else:
			# no error, so raz error variable
			context.setParseErrors(None)

	return root		
	
def ReadString(string, name, printfunc = None, check_compatibility = 0, progressCallback=None):
	return ReadStringContext(string, name,
				 MMNode.MMNodeContext(EditableObjects.EditableMMNode),
				 printfunc, check_compatibility, progressCallback)

def ReadStringContext(string, name, context, printfunc = None, check_compatibility = 0, progressCallback=None):
	p = SMILParser(context, printfunc = printfunc, check_compatibility = check_compatibility, progressCallback = progressCallback)
	root = __doParse(p, string)
	return root

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

def parseattrval(name, string, context):
	if MMAttrdefs.getdef(name)[0][0] == 'string':
		return string
	return MMAttrdefs.parsevalue(name, string, context)

def tokenize(str):
	tokens = []		# collect them here
	t = []			# collect each token here
	escape = 0
	parens = 0
	for c in str:
		if c == '\\':
			t.append(c)
			escape = 1
		elif escape or (parens and c not in '()'):
			t.append(c)
			escape = 0
		elif c in '-+. ()':
			if c == '(':
				parens = parens + 1
			elif c == ')':
				parens = parens - 1
			if t:
				tokens.append(''.join(t))
			tokens.append(c)
			t = []
		else:
			t.append(c)
	if t:
		tokens.append(''.join(t))
	return tokens
