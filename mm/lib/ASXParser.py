__version__ = "$Id$"

# ASX parser


# ASX validation should be complete.
# Only trivial semantics are implemented for now.
# The semantics implementation can follow 
# the pattern used for SMIL docs in GRiNS.


# import Sjoerd's XMLParser 
import xmllib


#########################################
# the definition of the ASX document type
class ASXdoc:
	attributes = {
		'asx':{'version':'3.0','previewmode':'no','bannerbar':'auto',},
		'entry': {'clientskip':'yes','skipifref':'no'},
		'event':{'name':'','whendone':'NEXT',},
		'entryref': {'href':None,'clientbind':'yes','clientskip':'yes'},
		'ref':{'href':None},
		'duration':{'value':None},
		'previewduration':{'value':None},
		'starttime':{'value':None},
		'repeat':{'count':'1'},
		'startmarker':{'number':'#','name':''},
		'endmarker':{'number':'#','name':''},
		'banner':{'href':None},
		'moreinfo':{'href':'URL','target':'frame'},
		'logo':{'href':None,'style':'MARK'},
		'base':{'href':'URL'},
		'abstract':{},
		'title':{},
		'author':{},
		'copyright':{},
		}

	__asxChilds=['abstract','author',
		'banner','base',
		'copyright','duration',
		'entry','entryref',
		'logo','moreinfo',
		'previewduration','repeat',
		'title','event']
	__entryChilds=['abstract','author',
		'copyright','duration',
		'endmarker','logo',
		'moreinfo','previewduration',
		'ref','startmarker',
		'starttime','title',
		'banner',]
	__durEntries=['duration','previewduration',
		'startmarker','endmarker','starttime',]
	__empty=[]

	entities = {
		'asx': __asxChilds,
		'entry': __entryChilds,
		'entryref': __empty,

		'ref': __durEntries,
		'event':['entry','entryref'],
		'repeat': ['entry','entryref'],

		'startmarker': __empty,
		'endmarker': __empty,
		'starttime': __empty,
		'duration': __empty,
		'previewduration': __empty,

		'banner': ['abstract','moreinfo',],
		'moreinfo':__empty,
		'abstract': __empty,
		'title':__empty,
		'author': __empty,
		'copyright': __empty,
		'logo': __empty,
		'base': __empty,
		}
	del __asxChilds, __entryChilds, __durEntries, __empty
	
#########################################
# Experimental for semantics impl. Not used yet
class MediaInfo:
	def __init__(self):
		self.author=''
		self.title=''
		self.abstract=''
		self.copyright=''
		self.banner=''
		self.logo=''
		self.moreinfo=''
		self.ref=None

# Experimental for semantics impl. Not used yet
class Root(MediaInfo):
	def __init__(self, version='3.0', previewmode='no', bannerbar='auto'):

		self.entry=None

		self.duration=None
		self.repeat='1'

		self.base=''
		self.entryref=None
		self.previewduration=None
		self.event=None

		self.version=version
		self.previewmode=previewmode
		self.bannerbar=bannerbar

# Experimental for semantics impl. Not used yet
class Entry(MediaInfo):
	def __init__(self, clientskip='yes', skipifref='no'):
		self.duration=None
		self.startmarker=None
		self.endmarker=None
		self.previewduration=None
		self.starttime=None

		self.clientskip=clientskip
		self.skipifref=skipifref


#########################################
# The ASXParser
class ASXParser(ASXdoc, xmllib.XMLParser):
	def __init__(self):
		xmllib.XMLParser.__init__(self, accept_unquoted_attributes = 1,
					  accept_utf8 = 1, map_case = 1)
		self.elements={
			'entry':(self.start_entry,self.end_entry),
			'ref':(self.start_ref,None),
			'entryref':(self.start_entryref,None),
			'duration':(self.start_duration,None),
			}
		self._playlist=[]
		self.__in_entry=0
	
	def read(self, url):
		import MMurl
		u = MMurl.urlopen(url)
		data = u.read()
		self.feed(data)

	def start_entry(self,attrs):
		self.__in_entry=1
	def end_entry(self):
		self.__in_entry=0

	def start_ref(self,attrs):
		if self.__in_entry:
			self._playlist.append(attrs.get('href'))

	def start_entryref(self,attrs):
		asx_ref_url=attrs.get('href')
		# macro-replace entryref with asx_ref_url
		p = ASXParser()
		p.read(asx_ref_url)
		self._playlist.append(p._playlist)

	def start_duration(self,attrs):
		value=attrs.get('value')
		print 'duration=',self.decode_duration(value),'secs'
		
	def finish_starttag(self, tagname, attrdict, method):
		if len(self.stack) > 1:
			ptag = self.stack[-2][2]
			if tagname not in self.entities.get(ptag, ()):
				self.syntax_error('%s element not allowed inside %s' % (self.stack[-1][0], self.stack[-2][0]))
		elif tagname != 'asx':
			self.syntax_error('outermost element must be "asx"')
		xmllib.XMLParser.finish_starttag(self, tagname, attrdict, method)

	def unknown_starttag(self, tag, attrs):
		if not self.attributes.has_key(tag): 
			print 'unknown tag: <' + tag + '>'
			return
		ad=self.attributes.get(tag)
		if attrs:
			for name, value in attrs.items():
				ad[name]=value
				
	def unknown_endtag(self, tag):
		if not self.attributes.has_key(tag): 
			print 'unknown end tag: <' + tag + '>'

	import re
	durre = re.compile(r'\s*(((?P<hours>\d+):)?(?P<minutes>\d+):)?(?P<seconds>\d+(\.\d+)?)\s*')
	def decode_duration(self, str):
		res = self.durre.match(str)
		if res is None:
			raise ValueError('badly formatted asx duration string')
		hours, minutes, seconds= res.group('hours', 'minutes', 'seconds')

		import string
		if hours is None:hours = 0
		else:hours = string.atoi(hours, 10)

		if minutes is None:minutes = 0
		else:minutes = string.atoi(minutes, 10)

		minutes = minutes + 60 * hours
		seconds = string.atof(seconds)
		return seconds + 60 * minutes

