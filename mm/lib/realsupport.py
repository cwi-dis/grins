import xmllib, string

class RTParser(xmllib.XMLParser):
	topelement = 'window'
	attributes = {
		'window': {'type':'generic',
			   'duration':None,
			   'endtime': None, # obsolete name for duration
			   'width':None,
			   'height':None,
			   'bgcolor':None,
			   'scrollrate':None,
			   'crawlrate':None,
			   'link':'blue',
			   'underline_hyperlinks':'true',
			   'wordwrap':'true',
			   'loop':'true',
			   'extraspaces':'use',},
		'time': {'begin':None,
			 'end':None,},
		'clear': {},
		'pos': {'x':'0',
			'y':'0',},
		'tu': {'color':None,},
		'tl': {'color':None,},
		'p': {},
		'br': {},
		'ol': {},
		'ul': [],
		'li': {},
		'hr': {},
		'center': {},
		'pre': {},
		'b': {},
		'i': {},
		's': {},
		'u': {},
		'font': {'charset':'us-ascii',
			 'color':None,
			 'bgcolor':None, # obsolete name for color
			 'face':'Times New Roman',
			 'size':'+0',},
		'a': {'href':None,
		      'target':None,},
		'required': {},
		}
	__empty = []
	__all = ['time', 'clear', 'pos', 'tu', 'tl', 'p', 'br', 'ol', 'ul',
		 'li', 'hr', 'center', 'pre', 'b', 'i', 's', 'u', 'font',
		 'a', 'required', ]
	entities = {
		topelement: __all,
		'a': __all,
		'b': __all,
		'br': __empty,
		'center': __all,
		'clear': __empty,
		'font': __all,
		'hr': __empty,
		'i': __all,
		'li': __all,
		'ol': __all,
		'p': __all,
		'pos': __empty,
		'required': __all,
		's': __all,
		'time': __empty,
		'tl': __all,
		'tu': __all,
		'u': __all,
		'ul': __all,
		}

	def __init__(self, file = None):
		self.elements = {
			'window': (self.start_window, None),
			}
		self.__file = file or '<unknown file>'
		xmllib.XMLParser.__init__(self, accept_unquoted_attributes = 1,
					  accept_utf8 = 1, map_case = 1)

	def start_window(self, attributes):
		duration = attributes.get('duration') or attributes.get('endtime')
		if duration is None:
			duration = 60
		else:
			try:
				duration = decode_duration(duration)
			except ValueError:
				self.syntax_error('badly formatted duration attribute')
				duration = 60
		type = string.lower(attributes.get('type'))
		if type in ('tickertape', 'marquee'):
			defwidth = 500
			defheight = 30
		else:
			defwidth = 320
			defheight = 180
		width = attributes.get('width')
		if width is None:
			width = defwidth
		else:
			try:
				width = string.atoi(string.strip(width))
			except string.atoi_error:
				self.syntax_error('badly formatted width attribute')
				width = defwidth
		height = attributes.get('height')
		if height is None:
			height = defheight
		else:
			try:
				height = string.atoi(string.strip(height))
			except string.atoi_error:
				self.syntax_error('badly formatted height attribute')
				height = defheight
		self.duration = duration
		self.width = width
		self.height = height

	def syntax_error(self, msg):
		print 'Warning: syntax error in file %s, line %d: %s' % (self.__file, self.lineno, msg)

	# the rest is to check that the nesting of elements is done
	# properly (i.e. according to the SMIL DTD)
	def finish_starttag(self, tagname, attrdict, method):
		if len(self.stack) > 1:
			ptag = self.stack[-2][2]
			if tagname not in self.entities.get(ptag, ()):
				self.syntax_error('%s element not allowed inside %s' % (self.stack[-1][0], self.stack[-2][0]))
		elif tagname != self.topelement:
			self.syntax_error('outermost element must be "%s"' % self.topelement)
		xmllib.XMLParser.finish_starttag(self, tagname, attrdict, method)

class RPParser(xmllib.XMLParser):
	topelement = 'imfl'
	attributes = {
		'head': {'aspect':'true',
			 'author':'',
			 'bitrate':None,
			 'copyright':'',
			 'duration':None,
			 'height':None,
			 'maxfps':None,
			 'preroll':None,
			 'timeformat':None,
			 'title':'',
			 'url':None,
			 'width':None,},
		'image': {'handle':None,
			  'name':None,},
		'fill': {'color':None,
			 'dsth':'0',
			 'dstw':'0',
			 'dstx':'0',
			 'dsty':'0',
			 'start':None,},
		'fadein': {'aspect':None,
			   'dsth':'0',
			   'dstw':'0',
			   'dstx':'0',
			   'dsty':'0',
			   'duration':None,
			   'maxfps':None,
			   'srch':'0',
			   'srcw':'0',
			   'srcx':'0',
			   'srcy':'0',
			   'start':None,
			   'target':None,
			   'url':None,},
		'fadeout': {'color':None,
			    'dsth':'0',
			    'dstw':'0',
			    'dstx':'0',
			    'dsty':'0',
			    'duration':None,
			    'maxfps':None,
			    'start':None,},
		'crossfade': {'aspect':None,
			      'dsth':'0',
			      'dstw':'0',
			      'dstx':'0',
			      'dsty':'0',
			      'duration':None,
			      'maxfps':None,
			      'srch':'0',
			      'srcw':'0',
			      'srcx':'0',
			      'srcy':'0',
			      'start':None,
			      'target':None,
			      'url':None,},
		'wipe': {'aspect':None,
			 'direction':None,
			 'dsth':'0',
			 'dstw':'0',
			 'dstx':'0',
			 'dsty':'0',
			 'duration':None,
			 'maxfps':None,
			 'srch':'0',
			 'srcw':'0',
			 'srcx':'0',
			 'srcy':'0',
			 'start':None,
			 'target':None,
			 'type':None,
			 'url':None,},
		'viewchange': {'dsth':'0',
			       'dstw':'0',
			       'dstx':'0',
			       'dsty':'0',
			       'duration':None,
			       'maxfps':None,
			       'srch':'0',
			       'srcw':'0',
			       'srcx':'0',
			       'srcy':'0',
			       'start':None,},
		}
	__empty = []
	entities = {
		topelement: ['head', 'image', 'fill', 'fadein', 'fadeout',
			     'crossfade', 'wipe', 'viewchange',],
		'head': __empty,
		'image': __empty,
		'fill': __empty,
		'fadein': __empty,
		'fadeout': __empty,
		'crossfade': __empty,
		'wipe': __empty,
		'viewchange': __empty,
		}

	def __init__(self, file = None):
		self.elements = {
			'head': (self.start_head, None),
			}
		self.__file = file or '<unknown file>'
		xmllib.XMLParser.__init__(self, accept_utf8 = 1)

	def start_head(self, attributes):
		duration = attributes.get('duration')
		if duration is None:
			self.syntax_error('required attribute duration missing in head element')
			duration = 0
		else:
			try:
				duration = decode_duration(duration)
			except ValueError:
				self.syntax_error('badly formatted duration attribute')
				duration = 0
		width = attributes.get('width')
		if width is None:
			self.syntax_error('required attribute width missing in head element')
			width = 100
		else:
			try:
				width = string.atoi(string.strip(width))
			except string.atoi_error:
				self.syntax_error('badly formatted width attribute')
				width = 100
		height = attributes.get('height')
		if height is None:
			self.syntax_error('required attribute height missing in head element')
			height = 100
		else:
			try:
				height = string.atoi(string.strip(height))
			except string.atoi_error:
				self.syntax_error('badly formatted height attribute')
				height = 100
		bitrate = attributes.get('bitrate')
		if bitrate is None:
			self.syntax_error('required attribute bitrate missing in head element')
			bitrate = 64000
		else:
			try:
				bitrate = string.atoi(string.strip(bitrate))
			except string.atoi_error:
				self.syntax_error('badly formatted bitrate attribute')
				bitrate = 64000
		self.duration = duration
		self.width = width
		self.height = height
		self.bitrate = bitrate

	def syntax_error(self, msg):
		print 'Warning: syntax error in file %s, line %d: %s' % (self.__file, self.lineno, msg)

	# the rest is to check that the nesting of elements is done
	# properly (i.e. according to the SMIL DTD)
	def finish_starttag(self, tagname, attrdict, method):
		if len(self.stack) > 1:
			ptag = self.stack[-2][2]
			if tagname not in self.entities.get(ptag, ()):
				self.syntax_error('%s element not allowed inside %s' % (self.stack[-1][0], self.stack[-2][0]))
		elif tagname != self.topelement:
			self.syntax_error('outermost element must be "%s"' % self.topelement)
		xmllib.XMLParser.finish_starttag(self, tagname, attrdict, method)

import re
durre = re.compile(r'\s*(?:(?P<days>\d+):(?:(?P<hours>\d+):(?:(?P<minutes>\d+):)?)?)?(?P<seconds>\d+(\.\d+)?)\s*')

def decode_duration(str):
	res = durre.match(str)
	if res is None:
		raise ValueError('badly formatted duration string')
	days, hours, minutes, seconds = res.group('days', 'hours', 'minutes', 'seconds')
	if days is None:
		days = 0
	else:
		days = string.atoi(days, 10)
	if hours is None:
		hours = 0
	else:
		hours = string.atoi(hours, 10)
	hours = hours + 24 * days
	if minutes is None:
		minutes = 0
	else:
		minutes = string.atoi(minutes, 10)
	minutes = minutes + 60 * hours
	seconds = string.atof(seconds)
	return seconds + 60 * minutes

def rmff(file, data):
	from StringIO import StringIO
	from chunk import Chunk
	import struct
	info = {}
	fp = StringIO(data)
	chunk = Chunk(fp)
	if chunk.getname() != '.RMF':
		print '%s: not a RealMedia file' % file
		return
	object_version = struct.unpack('>h', chunk.read(2))[0]
	if object_version != 0 and object_version != 1:
		print '%s: unknown .RMF version' % file
	else:
		file_version, num_headers = struct.unpack('>ll', chunk.read(8))
##		print 'file version', `file_version`
##		print 'num headers', `num_headers`
	for i in range(num_headers):
		chunk.close()
		chunk = Chunk(fp)
		name = chunk.getname()
		if name == 'PROP':
			object_version = struct.unpack('>h', chunk.read(2))[0]
			if object_version != 0:
				print '%s: unknown PROP version' % file
			else:
				max_bit_rate, avg_bit_rate, max_packet_size, avg_packet_size, num_packets, duration, preroll, index_offset, data_offset, num_streams, flags = struct.unpack('>lllllllllhh', chunk.read(40))
##				print 'max_bit_rate', `max_bit_rate`
##				print 'avg_bit_rate', `avg_bit_rate`
##				print 'max_packet_size', `max_packet_size`
##				print 'avg_packet_size', `avg_packet_size`
##				print 'num_packets', `num_packets`
##				print 'duration', `duration`
##				print 'preroll', `preroll`
##				print 'index_offset', `index_offset`
##				print 'data_offset', `data_offset`
##				print 'num_streams', `num_streams`
##				print 'flags', `flags`
				info['duration'] = float(duration)/1000
				info['bitrate'] = avg_bit_rate
				info['max_bit_rate'] = max_bit_rate
				info['avg_bit_rate'] = avg_bit_rate
		elif name == 'MDPR':
			object_version = struct.unpack('>h', chunk.read(2))[0]
			if object_version != 0:
				print '%s: unknown MDPR version' % file
			else:
				stream_number, max_bit_rate, avg_bit_rate, max_packet_size, avg_packet_size, start_time, preroll, duration, stream_name_size = struct.unpack('>hlllllllb', chunk.read(31))
				if stream_name_size > 0:
					stream_name = chunk.read(stream_name_size)
				else:
					stream_name = ''
				mime_type_size = struct.unpack('>b', chunk.read(1))[0]
				if mime_type_size > 0:
					mime_type = chunk.read(mime_type_size)
				else:
					mime_type = ''
				type_specific_len = struct.unpack('>l', chunk.read(4))[0]
				if type_specific_len > 0:
					type_specific_data = chunk.read(type_specific_len)
				else:
					type_specific_data = ''
##				print 'stream_number', `stream_number`
##				print 'max_bit_rate', `max_bit_rate`
##				print 'avg_bit_rate', `avg_bit_rate`
##				print 'max_packet_size', `max_packet_size`
##				print 'start_time', `start_time`
##				print 'preroll', `preroll`
##				print 'duration', `duration`
##				print 'stream_name_size', `stream_name_size`
##				print 'stream_name', `stream_name`
##				print 'mime_type_size', `mime_type_size`
##				print 'mime_type', `mime_type`
##				print 'type_specific_len', `type_specific_len`
##				print 'type_specific_data', `type_specific_data`
				if mime_type == 'video/x-pn-realvideo' and \
				   type_specific_len == 34:
					width, height = struct.unpack('>hh', type_specific_data[12:16])
					info['width'] = width
					info['height'] = height
		elif name == 'CONT':
			object_version = struct.unpack('>h', chunk.read(2))[0]
			if object_version != 0:
				print '%s: unknown CONT version' % file
			else:
				title_len = struct.unpack('>h', chunk.read(2))[0]
				title = chunk.read(title_len)
				author_len = struct.unpack('>h', chunk.read(2))[0]
				if author_len > 0:
					author = chunk.read(author_len)
				else:
					author = ''
				copyright_len = struct.unpack('>h', chunk.read(2))[0]
				if copyright_len > 0:
					copyright = chunk.read(copyright_len)
				else:
					copyright = ''
				comment_len = struct.unpack('>h', chunk.read(2))[0]
				if comment_len > 0:
					comment = chunk.read(comment_len)
				else:
					comment = ''
##				print 'title_len', `title_len`
##				print 'title', `title`
##				print 'author_len', `author_len`
##				print 'author', `author`
##				print 'copyright_len', `copyright_len`
##				print 'copyright', `copyright`
##				print 'comment_len', `comment_len`
##				print 'comment', `comment`
		elif name == 'DATA':
			object_version = struct.unpack('>h', chunk.read(2))[0]
			if object_version != 0:
				print '%s: unknown DATA version' % file
			else:
				num_packets, next_data_header = struct.unpack('>ll', chunk.read(8))
##				print 'num_packets', `num_packets`
##				print 'next_data_header', `next_data_header`
		elif name == 'INDX':
			object_version = struct.unpack('>h', chunk.read(2))[0]
			if object_version != 0:
				print '%s: unknown INDX version' % file
			else:
				num_indices, stream_number, next_index_header = struct.unpack('>lhl', chunk.read(10))
##				print 'num_indices', `num_indices`
##				print 'stream_number', `stream_number`
##				print 'next_index_header', `next_index_header`
	return info

cache = {}
import MMurl

def getinfo(file):
	if cache.has_key(file):
		return cache[file]
	try:
		data = open(MMurl.urlretrieve(file)[0], 'rb').read()
	except:
		cache[file] = info = {}
		return info
	if data[:5] == '<imfl':
		# RealPix
		rp = RPParser(file)
		rp.feed(data)
		rp.close()
		info = {'width': rp.width,
			'height': rp.height,
			'duration': rp.duration,
			'bitrate': rp.bitrate,}
	elif string.lower(data[:7]) == '<window':
		# RealText
		rp = RTParser(file)
		rp.feed(data)
		rp.close()
		info = {'width': rp.width,
			'height': rp.height,
			'duration': rp.duration,}
	elif data[:4] == '.RMF':
		# RealMedia
		info = rmff(file, data)
	elif data[:4] == '.ra\375':
		# RealAudio
		info = {}
	else:
		# unknown format
		info = {}
	cache[file] = info
	return info
