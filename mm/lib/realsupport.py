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
