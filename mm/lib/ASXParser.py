__version__ = "$Id$"

# ASX parser


# ASX validation should be complete.
# Only trivial semantics are implemented for now.
# The semantics implementation can follow 
# the pattern used for SMIL docs in GRiNS.


# import Sjoerd's XMLParser 
import xmllib

from ASXNode import *

#########################################
# the definition of the ASX document type
class ASXdoc:
	# all allowed entities with all their attributes
	attributes = {
		'asx':{'version':'3.0','previewmode':'no','bannerbar':'auto',},
		'entry': {'clientskip':'yes','skipifref':'no'},
		'entryref': {'href':None,'clientbind':'yes','clientskip':'yes'},
		'event':{'name':'','whendone':'NEXT',},
		'ref':{'href':None},
		'duration':{'value':None},
		'previewduration':{'value':None},
		'starttime':{'value':None},
		'repeat':{'count':'1'},
		'startmarker':{'number':'#','name':''},
		'endmarker':{'number':'#','name':''},
		'banner':{'href':None},
		'moreinfo':{'href':'URL','target':'frame','style':'','banner':''},
		'logo':{'href':None,'style':'MARK'},
		'base':{'href':'URL'},
		'abstract':{},
		'title':{},
		'author':{},
		'copyright':{},
		'param':{'name':'','value':''}
		}

	# some abbreviations
	__asxChilds=['abstract','author',
		'banner','base',
		'copyright','duration',
		'entry','entryref',
		'logo','moreinfo',
		'previewduration','repeat',
		'title','event','param'] 
	__entryChilds=['abstract','author',
		'copyright','duration',
		'endmarker','logo',
		'moreinfo','previewduration',
		'ref','startmarker',
		'starttime','title',
		'banner','param','base']
	__durEntries=['duration','previewduration',
		'startmarker','endmarker','starttime',]
	__empty=[]

	# all entities with their allowed content
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
		'moreinfo':['abstract',],
		'abstract': __empty,
		'title':__empty,
		'author': __empty,
		'copyright': __empty,
		'logo': __empty,
		'base': __empty,
		'param': __empty
		}
	del __asxChilds, __entryChilds, __durEntries, __empty
	

#########################################
# The ASXParser
class ASXParser(ASXdoc, xmllib.XMLParser):
	def __init__(self):
		xmllib.XMLParser.__init__(self, accept_unquoted_attributes = 1,
					  accept_utf8 = 1, map_case = 1)
		self.elements={
			'asx':(self.start_asx,self.end_asx),
			'entry':(self.start_entry,self.end_entry),
			'duration':(self.start_duration,self.end_duration),
			'ref':(self.start_ref,self.end_ref),
			'entryref':(self.start_entryref,self.end_entryref),
			'banner':(self.start_banner,self.end_banner),
			'abstract':(self.start_abstract,self.end_abstract),
			'title':(self.start_title,self.end_title),
			'moreinfo':(self.start_moreinfo,self.end_moreinfo),
			'logo':(self.start_logo,self.end_logo),
			'author':(self.start_author,self.end_author),
			'copyright':(self.start_copyright,self.end_copyright),
			}
		self.__root = None
		self.__seen_asx = 0
		self.__in_asx = 0
		self.__in_entry=0
		self.__node = None

		self._playlist=[]
	
	def read(self, url):
		import MMurl
		u = MMurl.urlopen(url)
		data = u.read()
		self.feed(data)

	def __error(self, message, lineno = None):
		if lineno is None:
			message = 'error: %s' % message
		else:
			message = 'error, line %d: %s' % (lineno, message)
		raise MSyntaxError, msg + message

	# asx contains everything
	def start_asx(self, attrs):
		if self.__seen_asx:
			self.__error('more than 1 asx tag', self.lineno)
		self.__seen_asx = 1
		self.__in_asx = 1
		self.__newContainer('asx', attrs)

	def end_asx(self):
		self.__in_asx = 0
		if not self.__root:
			self.error('empty document', self.lineno)
		self.__root.Dump()

	# asx par media container
	def start_entry(self,attrs):
		self.__in_entry=1
		self.__newContainer('entry',attrs)

	def end_entry(self):
		self.__in_entry=0
		self.__endContainer('entry')

	def start_duration(self,attrs):
		#value=attrs.get('value')
		#print 'duration=',self.__decode_duration(value),'secs'
		self.__newNode('duration', attrs)
	def end_duration(self,attrs):
		self.__endNode()

	def start_ref(self, attrs):
		self.__newNode('ref', attrs)
		# temp
		if self.__in_entry:
			self._playlist.append(attrs.get('href'))

	def end_ref(self):
		self.__endNode()

	def start_entryref(self,attrs):
		# macro-replace entryref with asx_ref_url
		#asx_ref_url=attrs.get('href')
		#p = ASXParser()
		#p.read(asx_ref_url)
		#self._playlist.append(p._playlist)
		pass

	def end_entryref(self,attrs):
		pass

	# advertising banner  
	# the href attr is the banner image (194x32 pixels)
	def start_banner(self, attrs):
		self.__newContainer('banner', attrs)
	def end_banner(self):
		self.__endContainer('banner')

	# tooltip
	def start_abstract(self, attrs):
		self.__newNode('abstract', attrs)
	def end_abstract(self):
		self.__endNode()

	def start_title(self, attrs):
		self.__newNode('title', attrs)
	def end_title(self):
		self.__endNode()

	def start_moreinfo(self, attrs):
		self.__newNode('moreinfo', attrs)
	def end_moreinfo(self):
		self.__endNode()

	def start_logo(self, attrs):
		self.__newNode('logo', attrs)
	def end_logo(self):
		self.__endNode()

	def start_author(self, attrs):
		self.__newNode('author', attrs)
	def end_author(self):
		self.__endNode()

	def start_copyright(self, attrs):
		self.__newNode('copyright', attrs)
	def end_copyright(self):
		self.__endNode()

	def handle_data(self, data):
		if self.__node:
			self.__node._add_data(data)

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
	def __decode_duration(self, str):
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

	def __newContainer(self, type, attrs):
		if not self.__in_asx:
			self.syntax_error('%s not in asx' % type)
		if not self.__root:
			node = ASXNode(type)
			self.__root = node
		elif not self.__container:
			self.error('multiple elements in body', self.lineno)
			return
		else:
			node = ASXNode(type)
			self.__container._addchild(node)
		self.__container = node
		self.__addAttrs(node, attrs)

	def __endContainer(self, type):
		if self.__container is None or \
		   self.__container.GetType() != type:
			# erroneous end tag; error message from xmllib
			return
		self.__container = self.__container.GetParent()

	def __addAttrs(self, node, attrs):
		attrdict = node.attrdict
		# just copy for now
		for attr, val in attrs.items():
			node._setattr(attr, val)

	def __newNode(self, tagname, attrs):
		if not self.__in_asx:
			self.syntax_error('node not in asx')
			return
		if self.__node:
			# the warning comes later from xmllib
			self.__endNode()
		# create the node
		if not self.__container:
			self.syntax_error('node not in container')
			return
		else:
			node = ASXNode(tagname)
			self.__container._addchild(node)
		self.__node = node
		self.__addAttrs(node, attrs)

	def __endNode(self):
		self.__node = None

BEGIN_ASF = """
<smil xmlns:GRiNS="http://www.oratrix.com/">
  <head>
    <layout>
      <root-layout id="playerWindow" width="400" height="300"/>
      <region id="videoRegion" width="400" height="300" GRiNS:type="video"/>
    </layout>
  </head>
  <body>
    <par id="ASXPresentation">
      <seq id="Playlist">
"""

END_ASF = """
      </seq>
    </par>
  </body>
</smil>

"""


# an asx file is a sequence of parallel nodes (<entry> ... </entry>)
# in the most general case for each parallel node we may have 5 channels active:
#  channel 1, video or sound, the actual presentation
#  channel 2: text channel, sequence of doc or entry info strings
#  channel 3: image channel, advertising banner below presentation with a link and tooltip
#  channel 4: text channel, static presentation title
#  channel 5: image channel, image displayed while buffering
# note: 4 and 5 may be ignored

def asx2smil(filename):
	parser = ASXParser()
	parser.read(filename)
	str = BEGIN_ASF
	for e in parser._playlist:
		str = str + '<video region="videoRegion" src="%s"/>\n' % e
	str = str + END_ASF
	return str

