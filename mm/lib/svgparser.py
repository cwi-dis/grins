__version__ = "$Id$"

import xmllib

import string

# Partial SVG parser

####################################
# partial svg dtd

SVGpubid = "-//W3C//DTD SVG 20001102//EN"
SVGdtd = "http://www.w3.org/TR/2000/CR-SVG-20001102/DTD/svg-20001102.dtd"

class SVG:
	# collections of attributes
	__stdAttrs = {'id': None,} 
	__langSpaceAttrs = {'xml:lang': None,
		'xml:space': None,}
	__styleAttrs = {'class':None,
		  'style':None,}
	__testAttrs = {
		'requiredFeatures': None,
		'requiredExtensions': None,
		'systemLanguage': None,
		'externalResourcesRequired': 'false',}
	__presentAttrsContainers = {'enable-background': None,}
	__presentAttrsFeFlood = {'flood-color': None,
		'flood-opacity': None,}
	__presentAttrsFillStroke = {'fill': None,
		'fill-opacity': None,
		'fill-rule': None,
		'stroke': None,
		'stroke-dasharray': None,
		'stroke-dashoffset': None,
		'stroke-linecap': None,
		'stroke-linejoin': None,
		'stroke-miterlimit': None,
		'stroke-opacity': None,
		'stroke-width': None,}
	__presentAttrsFontSpecification = {'font-family': None,
		'font-size': None,
		'font-size-adjust': None,
		'font-stretch': None,
		'font-style': None,
		'font-variant': None,
		'font-weight': None,}
	__presentAttrsGradients = {'stop-color': None,
		'stop-opacity': None,}
	__presentAttrsGraphics = {'clip-path':None,
		'clip-rule': None,
		'color': None,
		'color-interpolation': None,
		'color-rendering': None,
		'cursor': None,
		'display': None,
		'filter': None,
		'image-rendering': None,
		'mask': None,
		'opacity': None,
		'pointer-events': None,
		'shape-rendering': None,
		'text-rendering': None,
		'visibility': None,}
	__presentAttrsImages = {'color-profile': None,}
	__presentAttrsLightingEffects = {'lighting-color': None,}
	__presentAttrsMarkers = {'marker-start': None,
		'marker-mid': None,
		'marker-end': None,}
	__presentAttrsTextContentElements = {'alignment-baseline': None,
		'baseline-shift': None,
		'direction': None,
		'glyph-orientation-horizontal': None,
		'glyph-orientation-vertical': None,
		'kerning': None,
		'letter-spacin': None,
		'text-decoration': None,
		'unicode-bidi': None,
		'word-spacing': None,}
	__presentAttrsTextElements = {'dominant-baseline': None,
		'text-anchor': None,
		'writing-mode': None,}
	__presentAttrsViewports = {'clip': None,
		'overflow': None,}
	__presentAttrsAll = __presentAttrsContainers.copy()
	__presentAttrsAll.update(__presentAttrsFeFlood)
	__presentAttrsAll.update(__presentAttrsFillStroke)
	__presentAttrsAll.update(__presentAttrsFontSpecification)
	__presentAttrsAll.update(__presentAttrsGradients)
	__presentAttrsAll.update(__presentAttrsGraphics)
	__presentAttrsAll.update(__presentAttrsImages)
	__presentAttrsAll.update(__presentAttrsLightingEffects)
	__presentAttrsAll.update(__presentAttrsMarkers)
	__presentAttrsAll.update(__presentAttrsTextContentElements)
	__presentAttrsAll.update(__presentAttrsTextElements)
	__presentAttrsAll.update(__presentAttrsViewports)
	__graphicsElementEvents = {}		
	__documentEvents = {}

	# attributes
	attributes = {
		'svg': {'width': None, 
			'height': None, 
			'viewBox': None,
			'preserveAspectRatio': None,
			'zoomAndPan': 'magnify',
			'x': 0,
			'y': 0,
			'contentScriptType': 'text/ecmascript',
			'contentStyleType': 'text/css',
			},
		'g': {'transform': None,},
		'defs': {'transform': None,},
		'title': {},
		'desc': {},
		'symbol': {'viewBox': None,
			'preserveAspectRatio': None,},
		'use': {'transform': None,
			'x': None,
			'y': None, 
			'width': None, 
			'height': None,},
		'image': {'transform': None,
			'preserveAspectRatio': None,
			'x': None,
			'y': None, 
			'width': None, 
			'height': None,},
		'switch': {'transform': None,},
		'path':{'transform': None,
			'd': None,
			'pathLength': None,
			},
		'rect':{'transform': None,
			'x': None,
			'y': None,
			'width': None,
			'height': None,
			'rx': None,
			'ry': None,
			},
		'circle':{'transform': None,
			'cx': None,
			'cy': None,
			'r': None,
			},
		'ellipse':{'transform': None,
			'cx': None,
			'cy': None,
			'rx': None,
			'ry': None,
			},
		'line':{'transform': None,
			'x1': None,
			'y1': None,
			'x2': None,
			'y2': None,
			},
		'polyline':{'transform': None,
			'points': None,
			},
		'polygon':{'transform': None,
			'points': None,
			},
		'metadata': {'id': None,},
		'foreignObject':{'transform': None,
			'x': None,
			'y': None,
			'width': None,
			'height': None,
			},
	}
  
	# element sets
	__groupingElements = ['svg', 'g']
	__controlElements = ['defs', 'symbol', 'use', 'switch',]
	__infoElements = ['title', 'desc',]
	
	__basicElements = ['rect', 'circle', 'ellipse', 'line', 'polyline', 'polygon',]
	__lineArtElements = ['path', ] +  __basicElements
	__imageElements = ['image', ]
	__foreignElements = ['foreignObject', ]
	
	__pathElements = ['path', 'line', 'polyline', 'polygon', ]
	__presentElements = __groupingElements + __controlElements + __foreignElements
	__graphicsElements = __presentElements + __lineArtElements +  __imageElements


	# overall subsets
	__styleElements = __graphicsElements + __infoElements
	__resourceElements = __graphicsElements # + ...
	__allElements = __styleElements # + ...

	# update element sets with std collections

	# common attributes
	for __el in attributes.keys():
		attributes[__el].update(__stdAttrs)
	
	for __el in __styleElements:
		attributes[__el].update(__langSpaceAttrs)
		attributes[__el].update(__styleAttrs)
	
	for __el in __resourceElements:
		attributes[__el].update(__testAttrs)


	# event attributes
	attributes['svg'].update(__documentEvents)

	for __el in __graphicsElements:
		attributes[__el].update(__graphicsElementEvents)


	# presentation attributes
	for __el in __presentElements:
		attributes[__el].update(__presentAttrsAll)

	for __el in __pathElements:
		attributes[__el].update(__presentAttrsMarkers)

	for __el in __lineArtElements:
		attributes[__el].update(__presentAttrsGraphics)
		attributes[__el].update(__presentAttrsFillStroke)

	for __el in __imageElements:
		attributes[__el].update(__presentAttrsGraphics)
		attributes[__el].update(__presentAttrsImages)
		attributes[__el].update(__presentAttrsViewports)

	# allowed content sets
	__svgchildren = __allElements

	# all entities with their allowed content
	# no allowed content is default, so we don't specify empty ones here
	entities = {
		'svg': __svgchildren,
		'g': __svgchildren,
		'defs': __svgchildren,
		'symbol': __svgchildren,
		}

	# cleanup
	del __stdAttrs
	del __langSpaceAttrs
	del __styleAttrs
	del __testAttrs

	del __presentAttrsContainers
	del __presentAttrsFeFlood
	del __presentAttrsFillStroke
	del __presentAttrsFontSpecification
	del __presentAttrsGradients
	del __presentAttrsGraphics
	del __presentAttrsImages
	del __presentAttrsLightingEffects
	del __presentAttrsMarkers
	del __presentAttrsTextContentElements
	del __presentAttrsTextElements
	del __presentAttrsViewports
	del __presentAttrsAll

	del __documentEvents
	del __graphicsElementEvents

	del __groupingElements
	del __controlElements
	del __pathElements
	del __basicElements
	del __lineArtElements
	del __imageElements
	del __infoElements
	del __foreignElements

	del __presentElements
	del __graphicsElements

	del __styleElements
	del __resourceElements
	del __allElements

	del __svgchildren

####################################
# partial svgparser

class SvgParser(SVG, xmllib.XMLParser):
	def __init__(self, document):
		self.elements = {
			'svg': (self.start_svg, self.end_svg),
			'g': (self.start_g, self.end_g),
			}
		xmllib.XMLParser.__init__(self)
		self.__document = document
		self.__container = document
		self.__node = document

	def handle_xml(self, encoding, standalone):
		self.__document.setXML(encoding, standalone)

	def handle_doctype(self, tag, pubid, syslit, data):
		self.__document.setDocType(tag, pubid, syslit, data)

	def start_svg(self, attributes):
		self.start_container('svg', attributes)
					 
	def end_svg(self):
		self.end_container('svg')
		
	def start_g(self, attributes):
		self.start_container('g', attributes)
					 
	def end_g(self):
		self.end_container('g')

	def handle_data(self, data):
		if self.__node:
			self.__node.appendData(data)

	def unknown_starttag(self, tag, attrs):
		pass

	def unknown_endtag(self, tag):
		pass

	def start_container(self, tag, attrs):
		el = self.__document.createElement(tag)
		if self.__container:
			el.setParent(self.__container)
		el.setAttributes(attrs)
		self.__node = el

	def end_container(self, tag):
		if self.__container is None or self.__container.getType() != tag:
			# erroneous end tag; error message from xmllib
			return
		self.__container = self.__container.getParent()
		self.__node = self.__container

	def start_leaf(self, tag, attrs):
		pass

	def end_leaf(self, tag):
		pass

	def syntax_error(self, msg, lineno = None):
		msg = 'warning: syntax error on line %d: %s' % (lineno or self.lineno, msg)
		print msg

####################################
# partial svgdom

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
		if not self.data:
			self.data = data
		else:
			self.data = self.data + data

class SvgDocument(SvgNode):
	def __init__(self, source):
		SvgNode.__init__(self, 'document', self)
			
		# xml spec
		self.xmlversion = '1.0'
		self.xmlencoding = 'ISO-8859-1'
		self.xmlstandalone = 'no'

		# doctype
		self.doctypetag = 'svg'
		self.doctypepubid = SVGpubid
		self.doctypesyslit = SVGdtd
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
		p = SvgParser(self)
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
		return '<%s instance, type=%s, attributes=%s>' % (self.__class__.__name__, self.type, `self.attrdict`)

	def setAttributes(self, attrdict):
		self.attrdict = attrdict.copy()

	def getAttribute(self, attr):
		return self.attrdict.get(attr)

####################################
# utilities

unitstopx = {'px':1.0, 'pt':1.25, 'pc':15.0, 'mm':3.543307, 'cm':35.43307, 'in':90.0}

def topxl(val):
	if not val:
		return None
	val = string.strip(val)
	if not val:
		return None
	val = string.lower(val)
	if val[-1] in string.digits:
		return string.atoi(val)
	units = val[-2]
	factor = unitstopx.get(units) 
	if factor is None:
		print 'warning: bad units'
		return string.atoi(val)
	return int(factor*string.atof(val[:-2])+0.5)

def GetSvgSizeFromSrc(source):
	svg = SvgDocument(source)
	root =  svg.getRoot()
	if not root:
		return 0, 0
	strwidth = root.getAttribute('width')
	strheight = root.getAttribute('height')
	if not strwidth or not strheight:
		width, height = 0, 0
	else:
		width = topxl(strwidth)
		height = topxl(strheight)
		if width is None or height is None:
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
    <circle cx="300" cy="30" r="20"  transform="rotate(20)" style="visibility:hidden" />
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

