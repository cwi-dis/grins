import xmllib, string, re

colors = {
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
# see SMILTreeRead for a more elaborate version
color = re.compile('#(?P<hex>[0-9a-fA-F]{3}|'		# #f00
		   '[0-9a-fA-F]{6})$')			# #ff0000

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
				duration = decode_time(duration)
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
			 'timeformat':'milliseconds',
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
			'image': (self.start_image, None),
			'fill': (self.start_fill, None),
			'fadein': (self.start_fadein, None),
			'fadeout': (self.start_fadeout, None),
			'crossfade': (self.start_crossfade, None),
			'wipe': (self.start_wipe, None),
			'viewchange': (self.start_viewchange, None),
			}
		self.tags = []
		self.__images = {}
		self.__file = file or '<unknown file>'
		xmllib.XMLParser.__init__(self, accept_utf8 = 1)

	def close(self):
		xmllib.XMLParser.close(self)
		self.tags.sort(self.__tagsort)
		prevstart = 0
		for tag in self.tags:
			start = tag['start']
			tag['start'] = start - prevstart
			prevstart = start

	def __tagsort(self, tag1, tag2):
		return cmp(tag1['start'], tag2['start'])

	def start_head(self, attributes):
		self.timeformat = attributes['timeformat']
		duration = attributes.get('duration')
		if duration is None:
			self.syntax_error('required attribute duration missing in head element')
			duration = 0
		else:
			try:
				duration = decode_time(duration, self.timeformat)
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
		self.aspect = string.lower(attributes['aspect'])
		self.author = attributes.get('author')
		self.copyright = attributes.get('copyright')
		maxfps = attributes.get('maxfps')
		if maxfps is not None:
			try:
				self.maxfps = string.atoi(maxfps)
			except string.atoi_error:
				self.syntax_error('badly formatted maxfps attribute')
				self.maxfps = None
		else:
			self.maxfps = None
		preroll = attributes.get('preroll')
		if preroll is not None:
			try:
				self.preroll = string.atof(preroll)
			except string.atof_error:
				self.syntax_error('badly formatted preroll attribute')
				self.preroll = None
		else:
			self.preroll = None
		self.title = attributes.get('title')
		self.url = attributes.get('url')

	def start_image(self, attributes):
		handle = attributes.get('handle')
		name = attributes.get('name')
		if handle is None or name is None:
			self.syntax_error("required attribute `name' and/or `handle' missing")
			return
		if self.__images.has_key(handle):
			self.syntax_error("image `handle' not unique")
			return
		self.__images[handle] = name

	def start_fill(self, attributes):
		destrect = self.__rect('dst', attributes)
		color = self.__color(attributes)
		start = self.__time('start', attributes)
		self.tags.append({'tag': 'fill', 'color': color, 'subregion': destrect, 'start': start})

	def start_fadein(self, attributes):
		self.__fadein_or_crossfade_or_wipe('fadein', attributes)

	def start_fadeout(self, attributes):
		destrect = self.__rect('dst', attributes)
		color = self.__color(attributes)
		start = self.__time('start', attributes)
		duration = self.__time('duration', attributes)
		maxfps = attributes.get('maxfps', self.maxfps)
		self.tags.append({'tag': 'fadeout', 'color': color, 'subregion': destrect, 'start': start, 'duration': duration, 'maxfps': maxfps})

	def start_crossfade(self, attributes):
		self.__fadein_or_crossfade_or_wipe('crossfade', attributes)

	def start_wipe(self, attributes):
		self.__fadein_or_crossfade_or_wipe('wipe', attributes)

	def start_viewchange(self, attributes):
		destrect = self.__rect('dst', attributes)
		duration = self.__time('duration', attributes)
		maxfps = attributes.get('maxfps', self.maxfps)
		srcrect = self.__rect('src', attributes)
		start = self.__time('start', attributes)
		self.tags.append({'tag': 'viewchange', 'imgcrop': srcrect, 'subregion': dstrect, 'start': start, 'duration': duration, 'maxfps': maxfps})

	def __fadein_or_crossfade_or_wipe(self, tag, attributes):
		aspect = (attributes.get('aspect', self.aspect) == 'true')
		dstrect = self.__rect('dst', attributes)
		duration = self.__time('duration', attributes)
		maxfps = attributes.get('maxfps', self.maxfps)
		srcrect = self.__rect('src', attributes)
		start = self.__time('start', attributes)
		target = attributes.get('target')
		if target is None:
			self.syntax_error("require attribute `target' missing")
		elif not self.__images.has_key(target):
			self.syntax_error("unknown `target' attribute")
		url = attributes.get('url')
		attrs = {'tag': tag, 'file': self.__images.get(target), 'imgcrop': srcrect, 'subregion': dstrect, 'aspect': aspect, 'start': start, 'duration': duration, 'maxfps': maxfps, 'href': url}
		if tag == 'wipe':
			type = attributes.get('type')
			if type is None:
				self.syntax_error("required attributes `type' missing")
			elif type not in ('push', 'normal'):
				self.syntax_error("unknown `type' attribute")
				type = None
			if type is None: # provide default
				type = 'normal'
			attrs['wipetype'] = type
		self.tags.append(attrs)

	def __rect(self, str, attributes):
		x = attributes.get(str+'x', '0')
		y = attributes.get(str+'y', '0')
		h = attributes.get(str+'h', '0')
		w = attributes.get(str+'w', '0')
		try:
			x = string.atoi(x)
		except string.atoi_error:
			self.syntax_error("attribute `%sx' is not an integer" % str)
			x = 0
		try:
			y = string.atoi(y)
		except string.atoi_error:
			self.syntax_error("attribute `%sy' is not an integer" % str)
			y = 0
		try:
			w = string.atoi(w)
		except string.atoi_error:
			self.syntax_error("attribute `%sw' is not an integer" % str)
			w = 0
		try:
			h = string.atoi(h)
		except string.atoi_error:
			self.syntax_error("attribute `%sh' is not an integer" % str)
			h = 0
		return x, y, w, h

	# see SMILTreeRead.SMILParser.__convert_color for a more
	# elaborate version
	def __color(self, attributes):
		val = attributes.get('color')
		if val is None:
			return
		if colors.has_key(val):
			return colors[val]
		res = color.match(val)
		if res is None:
			self.syntax_error('bad color specification')
			return
		else:
			hex = res.group('hex')
			if len(hex) == 3:
				r = string.atoi(hex[0]*2, 16)
				g = string.atoi(hex[1]*2, 16)
				b = string.atoi(hex[2]*2, 16)
			else:
				r = string.atoi(hex[0:2], 16)
				g = string.atoi(hex[2:4], 16)
				b = string.atoi(hex[4:6], 16)
		return r, g, b

	def __time(self, attr, attributes):
		time = attributes.get(attr)
		if time is None:
			self.syntax_error("required attributes `%s' missing" % attr)
			return 0
		try:
			time = decode_time(time, self.timeformat)
		except ValueError, msg:
			self.syntax_error(msg)
			return 0
		return time

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

coordnames = 'x','y','w','h'
def writecoords(f, str, coords):
	if not coords:
		return
	for i in range(4):
		c = coords[i]
		if c != 0:
			f.write(' %s%s="%d"' % (str, coordnames[i], c))

def writeRP(file, rp):
	from SMILTreeWrite import nameencode

	f = open(file, 'w')
	f.write('<imfl>\n')
	f.write('  <head')
	sep = ' '
	if rp.title is not None:
		f.write(sep+'title=%s' % nameencode(rp.title))
		sep = '\n        '
	if rp.author is not None:
		f.write(sep+'author=%s' % nameencode(rp.author))
		sep = '\n        '
	if rp.copyright is not None:
		f.write(sep+'copyright=%s' % nameencode(rp.copyright))
		sep = '\n        '
	f.write(sep+'timeformat="dd:hh:mm:ss.xyz"')
	sep = '\n        '
	f.write(sep+'duration="%g"' % rp.duration)
	f.write(sep+'bitrate="%d"' % rp.bitrate)
	f.write(sep+'width="%d"' % rp.width)
	f.write(sep+'height="%d"' % rp.height)
	defaspect = (rp.aspect == 'true')
	if not defaspect:
		f.write(sep+'aspect="false"')
	if rp.preroll is not None:
		f.write(sep+'preroll="%g"' % rp.preroll)
	if rp.url:
		f.write(sep+'url=%s' % nameencode(rp.url))
	if rp.maxfps is not None:
		f.write(sep+'maxfps="%d"' % rp.maxfps)
	f.write('/>\n')
	images = {}
	handle = 0
	for attrs in rp.tags:
		if attrs.get('tag', 'fill') in ('fadein', 'crossfade', 'wipe'):
			file = attrs.get('file')
			if file and not images.has_key(file):
				handle = handle + 1
				images[file] = handle
	for name, handle in images.items():
		f.write('  <image handle="%d" name=%s/>\n' % (handle, nameencode(name)))
	start = 0
	for attrs in rp.tags:
		tag = attrs.get('tag', 'fill')
		f.write('  <%s' % tag)
		start = start + attrs.get('start', 0)
		f.write(' start="%g"' % start)
		if tag != 'fill':
			f.write(' duration="%g"' % attrs.get('duration', 0))
		if tag in ('fill', 'fadeout'):
			color = attrs.get('color', (0,0,0))
			for name, val in colors.items():
				if color == val:
					color = name
					break
			else:
				color = '#%02x%02x%02x' % color
			f.write(' color="%s"' % color)
		else:
			if tag != 'viewchange':
				file = attrs.get('file')
				if file:
					f.write(' target="%d"' % images[file])
##				else:
##					# file attribute missing
				aspect = attrs.get('aspect', defaspect)
				if aspect != defaspect:
					f.write(' aspect="%s"' % ['false','true'][aspect])
				url = attrs.get('href')
				if url:
					f.write(' url=%s' % nameencode(url))
			writecoords(f, 'src', attrs.get('imgcrop'))
		writecoords(f, 'dst', attrs.get('subregion'))
		if tag != 'fill':
			maxfps = attrs.get('maxfps')
			if maxfps is not None:
				f.write(' maxfps="%d"' % maxfps)
		f.write('/>\n')
	f.write('</imfl>\n')
	f.close()

import re
durre = re.compile(r'\s*(?:(?P<days>\d+):(?:(?P<hours>\d+):(?:(?P<minutes>\d+):)?)?)?(?P<seconds>\d+(\.\d+)?)\s*')

def decode_time(str, fmt = 'dd:hh:mm:ss.xyz'):
	if fmt == 'milliseconds':
		try:
			ms = string.atoi(str)
		except string.atoi_error:
			raise ValueError('badly formatted duration string')
		return ms / 1000.0	# convert milliseconds to seconds
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

def rmff(file, fp):
	from StringIO import StringIO
	from chunk import Chunk
	import struct
	info = {}
	size, object_version = struct.unpack('>lh', fp.read(6))
	if object_version != 0 and object_version != 1:
		print '%s: unknown .RMF version' % file
		return info
	else:
		file_version, num_headers = struct.unpack('>ll', fp.read(8))
	for i in range(num_headers):
		chunk = Chunk(fp, align = 0, inclheader = 1)
		name = chunk.getname()
		if name == 'PROP':
			object_version = struct.unpack('>h', chunk.read(2))[0]
			if object_version != 0:
				print '%s: unknown PROP version' % file
			else:
				max_bit_rate, avg_bit_rate, max_packet_size, avg_packet_size, num_packets, duration, preroll, index_offset, data_offset, num_streams, flags = struct.unpack('>lllllllllhh', chunk.read(40))
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
		elif name == 'DATA':
			break		# we've seen enough
##			object_version = struct.unpack('>h', chunk.read(2))[0]
##			if object_version != 0:
##				print '%s: unknown DATA version' % file
##			else:
##				num_packets, next_data_header = struct.unpack('>ll', chunk.read(8))
		elif name == 'INDX':
			object_version = struct.unpack('>h', chunk.read(2))[0]
			if object_version != 0:
				print '%s: unknown INDX version' % file
			else:
				num_indices, stream_number, next_index_header = struct.unpack('>lhl', chunk.read(10))
		chunk.close()
	return info

cache = {}
import MMurl

def getinfo(file, fp = None):
	if cache.has_key(file):
		return cache[file]
	if fp is None:
		try:
			fp = MMurl.urlopen(file)
		except:
			cache[file] = info = {}
			return info
	head = fp.read(4)
	if head == '<imf':
		# RealPix
		rp = RPParser(file)
		rp.feed(head)
		rp.feed(fp.read())
		rp.close()
		info = {'width': rp.width,
			'height': rp.height,
			'duration': rp.duration,
			'bitrate': rp.bitrate,}
	elif string.lower(head) == '<win':
		# RealText
		rp = RTParser(file)
		rp.feed(head)
		rp.feed(fp.read())
		rp.close()
		info = {'width': rp.width,
			'height': rp.height,
			'duration': rp.duration,}
	elif head == '.RMF':
		# RealMedia
		info = rmff(file, fp)
	elif head == '.ra\375':
		# RealAudio
		info = {}
	else:
		# unknown format
		info = {}
	fp.close()
	cache[file] = info
	return info
