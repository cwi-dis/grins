__version__ = "$Id$"

#
#	SVG DOM
#

import string

import svgdtd

class SvgNode:
	def __init__(self, type, document):
		self.type = type # tag for elements and meta-tag for the rest
		self.document = document # owner document
		self.parent = None
		self.children = []
		self.data = None

	def getType(self):
		return self.type

	def getDocument(self):
		return self.document

	def getParent(self):
		return self.parent

	def getChildren(self):
		return self.children

	def getRoot(self):
		return self.document.getRoot()

	def getFirstChildByType(self, type):
		for child in self.children:
			if child.type == type:
				return child
		return None
	
	def setParent(self, parent):
		self.parent = parent
		parent.children.append(self)

	def appendData(self, data):
		if self.data is None:
			self.data = data
		else:
			self.data = self.data + data

class SvgDocument(SvgNode):
	def __init__(self, source):
		SvgNode.__init__(self, '#document', self)
			
		# xml spec
		self.xmlversion = '1.0'
		self.xmlencoding = 'ISO-8859-1'
		self.xmlstandalone = 'no'

		# doctype
		self.doctypetag = 'svg'
		self.doctypepubid = svgdtd.SVGpubid
		self.doctypesyslit = svgdtd.SVGdtd
		self.doctypedata = None
		
		# set source
		self.source = None
		if source:
			# convert Windows CRLF sequences to LF
			source = string.join(string.split(source, '\r\n'), '\n')
			# then convert Macintosh CR to LF
			source = string.join(string.split(source, '\r'), '\n')
			self.source = source

		# create DOM
		p = SvgDOMBuilder(self)
		p.feed(self.source)
		p.close()
		
	def setDocType(self, tag, pubid, syslit, data):
		self.doctypetag, self.doctypepubid, self.doctypesyslit, self.doctypedata = tag, pubid, syslit, data

	def getDocType(self):
		return self.doctypetag, self.doctypepubid, self.doctypesyslit, self.doctypedata

	def setXML(self, encoding, standalone='no'):
		self.xmlencoding, self.xmlstandalone = encoding, standalone

	def getXML(self, encoding, standalone='no'):
		return self.xmlencoding, self.xmlstandalone

	def getSrc(self, data):
		return self.source

	def getRoot(self):
		return self.getFirstChildByType('svg')
			
	def createElement(self, type):
		return SvgElement(type, self)

class SvgElement(SvgNode):
	def __init__(self, type, document):
		SvgNode.__init__(self, type, document)
		self.attrdict = {}	# Attributes of this Element

	def __repr__(self):
		if self.data is not None:
			data = string.strip(self.data)
			return '<%s instance, type=%s, attributes=%s, data=%s>' % (self.__class__.__name__, self.type, `self.attrdict`, `data`)
		else:
			return '<%s instance, type=%s, attributes=%s>' % (self.__class__.__name__, self.type, `self.attrdict`)

	def setAttributes(self, attrdict):
		self.attrdict = attrdict.copy()

	def getAttribute(self, attr):
		return self.attrdict.get(attr)

####################################
# SVG DOM Builder using xmllib.XMLParser

import xmllib

class SvgDOMBuilder(svgdtd.SVG, xmllib.XMLParser):
	def __init__(self, document):
		xmllib.XMLParser.__init__(self)
		self.__document = document
		self.__node = document

	def handle_xml(self, encoding, standalone):
		self.__document.setXML(encoding, standalone)

	def handle_doctype(self, tag, pubid, syslit, data):
		self.__document.setDocType(tag, pubid, syslit, data)

	def handle_data(self, data):
		tag = self.__node.getType()
		if tag in self.dataEntities:
			self.__node.appendData(data)

	def unknown_starttag(self, tag, attrs):
		partag = self.__node.getType()
		content = self.entities.get(partag)
		if partag!='#document' and (content is None or tag not in content):
			self.syntax_error('%s not allowed in %s' % (tag, partag))
			return
		el = self.__document.createElement(tag)
		el.setParent(self.__node)
		el.setAttributes(attrs)
		self.__node = el

	def unknown_endtag(self, tag):
		self.__node = self.__node.getParent()
			
	def syntax_error(self, msg, lineno = None):
		msg = 'warning: syntax error on line %d: %s' % (lineno or self.lineno, msg)
		print msg


####################################
# utilities

def GetSvgSizeFromSrc(source):
	from svgtypes import SVGLength
	svg = SvgDocument(source)
	root =  svg.getRoot()
	if not root:
		return 0, 0
	strwidth = root.getAttribute('width')
	strheight = root.getAttribute('height')
	width = SVGLength(strwidth).getLength()
	height = SVGLength(strheight).getLength()
	if not width or not height:
		width, height = 0, 0
	return width, height

def GetSvgSize(url):
	import MMurl
	try:
		u = MMurl.urlopen(url)
	except:
		print 'warning: cannot open file %s' % url
		return 0, 0
	source = u.read()
	u.close()
	return GetSvgSizeFromSrc(source)



####################################
# test

svgSource = """<?xml version="1.0" standalone="no"?>
<svg width="600" height="600">
  <title> Simple shapes </title>
  <g transform="translate(150,150)" style="fill:red; stroke:navy; stroke-width:2; stroke-dasharray: 5 2;" >
    <circle cx="300" cy="30" r="20" transform="rotate(0)"/>
    <circle cx="300" cy="30" r="20" transform="rotate(10)"/>
    <circle cx="300" cy="30" r="20"  transform="rotate(20)" style="visibility:hidden"/>
    <circle cx="300" cy="30" r="20" transform="rotate(30)"/>
    <circle cx="300" cy="30" r="20"  transform="rotate(40)"/>
    <circle cx="300" cy="30" r="20"  transform="rotate(50)"/>
    <circle cx="300" cy="30" r="20" transform="rotate(60)" style="visibility:hidden" />
    <circle cx="300" cy="30" r="20" transform="rotate(70)"/>
    <circle cx="300" cy="30" r="20" transform="rotate(80)"/>
    <circle cx="300" cy="30" r="20" transform="rotate(90)"/>
  </g>
</svg>"""

if __name__ == '__main__':
    print GetSvgSizeFromSrc(svgSource)
