__version__ = "$Id$"

#
#	SVG DOM
#

import string

import svgdtd

from svgtypes import *

class SvgNode:
	def __init__(self, type, document):
		self.type = type # tag for elements and meta-tag for the rest
		self.document = document # owner document
		self.parent = None
		self.firstchild = None
		self.nextsibling = None
		self.data = None
		self.cdata = None

		# for optimization when building tree (can be removed)
		self.lastchild = None

	def __repr__(self):
		if self.data is not None:
			data = string.strip(self.data)
			return '<%s instance, type=%s, data=%s>' % (self.__class__.__name__, self.type, `data`)
		else:
			return '<%s instance, type=%s>' % (self.__class__.__name__, self.type)

	def svgrepr(self):
		return ''

	def getType(self):
		return self.type

	def getDocument(self):
		return self.document

	def getParent(self):
		return self.parent

	def getFirstChild(self):
		return self.firstchild

	def getNextSibling(self):
		return self.nextsibling

	def getRoot(self):
		return self.document.getRoot()

	def getChildren(self):
		L = []
		node = self.firstchild
		while node:
			L.append(node)
			node = node.nextsibling
		return L

	def getFirstChildByType(self, type):
		node = self.firstchild
		while node:
			if node.type == type:
				return node
			node = node.nextsibling
		return None
	
	def appendData(self, data):
		if self.data is None:
			self.data = data
		else:
			self.data = self.data + data

	def appendCData(self, cdata):
		if self.cdata is None:
			self.cdata = cdata
		else:
			self.cdata = self.cdata + cdata

	# on end_tag
	def setready(self):
		if self.data is not None:
			self.data = string.strip(self.data)
		if self.cdata is not None:
			self.cdata = string.strip(self.cdata)

	def getLastChild(self, scan=0):
		if not scan:
			return self.lastchild
		lastchild = None
		child = self.firstchild
		while child:
			lastchild = child
			child = child.nextsibling
		
	def appendChild(self, node):
		lastchild = self.getLastChild()
		if lastchild is None:
			self.firstchild = node
		else:
			lastchild.nextsibling = node
		node.parent = self
		self.lastchild = node # opt while building only
			
	def clone(self):
		new = self.__class__(self.type, self.document)
		new.parent = self.parent
		new.firstchild = self.firstchild
		new.nextsibling = self.nextsibling
		new.data = self.data
		new.cdata = self.cdata
		return new

class SvgComment(SvgNode):
	def svgrepr(self):
		return '<!--' + self.data + '-->'
				
class SvgElement(SvgNode):
	def __init__(self, type, document):
		SvgNode.__init__(self, type, document)
		self.attrdict = {}	# Attributes of this Element
		self.errorstr = None

		# should be attrs of SvgStyleElement descendants
		self.style = None
		self.tflist = None

	def __repr__(self):
		if self.data is not None:
			data = string.strip(self.data)
			return '<%s instance, type=%s, attributes=%s, data=%s>' % (self.__class__.__name__, self.type, `self.attrdict`, `data`)
		else:
			return '<%s instance, type=%s, attributes=%s>' % (self.__class__.__name__, self.type, `self.attrdict`)

	def svgrepr(self):
		s = self.type + ' '
		for attr in self.attrdict.keys():
			val = self.attrdict.get(attr)
			if val is None:
				continue
			elif type(val) == type(''):
				default = svgdtd.SVG.attributes[self.type][attr]
				if val != default:
					s = s + attr + '=\"' + val + '\" '
			else:
				try:
					if not val.isDefault():
						s = s + attr + '=\"' + repr(val) + '\" '
				except:
					print self, attr, 'is not an svgtype object'
		return s[:-1]

	def seterror(self, str):
		self.errorstr = str

	def poperror(self):
		str = self.errorstr
		self.errorstr = None
		return str

	def setAttributes(self, attrdict):
		self.attrdict = attrdict.copy()
		self.parseTransform()
		self.parseStyle()
		self.parseAttributes()

	def getAttribute(self, attr):
		return self.attrdict.get(attr)

	def parseAttributes(self):
		pass
	
	def parseStyle(self):
		self.style = None
		cssclass = self.attrdict.get('class')
		if cssclass is not None:
			stylenode = self.document.getStyleElement()
			cssdef = stylenode.textcssdefs.getValue().get(cssclass)
			if cssdef is not None:
				self.style = cssdef.getValue().copy()
		val = self.attrdict.get('style')
		if val:
			val = string.strip(val)
			style = SVGStyle(self, val)
			if self.style is not None:
				self.style.update(style.getValue())
			else:
				self.style = style.getValue()

	def parseTransform(self):
		val = self.attrdict.get('transform')
		if val:
			val = string.strip(val)
			tfl = SVGTransformList(self, val)
			self.tflist = tfl.getValue()
		
	def getStyle(self):
		return self.style

	def getTransform(self):
		return self.tflist

	def get(self, name):
		val = self.attrdict.get(name)
		if val is None:
			return None
		elif type(val) == type(''):
			return val
		else:
			return val.getValue()

	def clone(self):
		new = SvgNode.clone(self)
		if self.style:
			new.style = self.style.copy()
		if self.tflist:
			new.transform = self.tflist[:]
		return new

class SvgRect(SvgElement):
	def parseAttributes(self):
		x, y = self.attrdict.get('x'), self.attrdict.get('y')
		self.attrdict['x'] = SVGCoordinate(self, x, 0)
		self.attrdict['y'] = SVGCoordinate(self, y, 0)

		width, height = self.attrdict.get('width'), self.attrdict.get('height')
		self.attrdict['width'] = SVGLength(self, width)
		self.attrdict['height'] = SVGLength(self, height)

		rx, ry = self.attrdict.get('rx'), self.attrdict.get('ry')
		if rx is not None and ry is not None:
			self.attrdict['rx'] = SVGLength(self, rx)
			self.attrdict['ry'] = SVGLength(self, ry)
		elif rx is not None:
			self.attrdict['rx'] = SVGLength(self, rx)
			self.attrdict['ry'] = SVGLength(self, rx)
		elif ry is not None:
			self.attrdict['rx'] = SVGLength(self, ry)
			self.attrdict['ry'] = SVGLength(self, ry)
		
class SvgCircle(SvgElement):
	def parseAttributes(self):
		cx, cy = self.attrdict.get('cx'), self.attrdict.get('cy')
		self.attrdict['cx'] = SVGCoordinate(self, cx, 0)
		self.attrdict['cy'] = SVGCoordinate(self, cy, 0)

		r = self.attrdict.get('r')
		self.attrdict['r'] = SVGLength(self, r)

class SvgEllipse(SvgElement):
	def parseAttributes(self):
		cx, cy = self.attrdict.get('cx'), self.attrdict.get('cy')
		self.attrdict['cx'] = SVGCoordinate(self, cx, 0)
		self.attrdict['cy'] = SVGCoordinate(self, cy, 0)

		rx, ry = self.attrdict.get('rx'), self.attrdict.get('ry')
		self.attrdict['rx'] = SVGLength(self, rx)
		self.attrdict['ry'] = SVGLength(self, rx)

		cx = self.getCoordinate('cx', 0)
		cy = self.getCoordinate('cy', 0)

class SvgLine(SvgElement):
	def parseAttributes(self):
		x1, y1 = self.attrdict.get('x1'), self.attrdict.get('y1')
		self.attrdict['x1'] = SVGCoordinate(self, x1, 0)
		self.attrdict['y1'] = SVGCoordinate(self, y1, 0)

		x2, y2 = self.attrdict.get('x2'), self.attrdict.get('y2')
		self.attrdict['x2'] = SVGCoordinate(self, x2)
		self.attrdict['y2'] = SVGCoordinate(self, y2)

class SvgPolyline(SvgElement):
	def parseAttributes(self):
		points = self.attrdict.get('points')
		self.attrdict['points'] = SVGPoints(self, points)

class SvgPolygon(SvgElement):
	def parseAttributes(self):
		points = self.attrdict.get('points')
		self.attrdict['points'] = SVGPoints(self, points)

class SvgPath(SvgElement):
	def parseAttributes(self):
		d = self.attrdict.get('d')
		self.attrdict['d'] = SVGPath(d)
		
class SvgText(SvgElement):
	def parseAttributes(self):
		x, y = self.attrdict.get('x'), self.attrdict.get('y')
		self.attrdict['x'] = SVGCoordinate(self, x, 0)
		self.attrdict['y'] = SVGCoordinate(self, y, 0)

		textLength, lengthAdjust = self.attrdict.get('textLength'), self.attrdict.get('lengthAdjust')
		self.attrdict['textLength'] = SVGLength(self, textLength)
		self.attrdict['lengthAdjust'] = SVGLength(self, lengthAdjust)

class SvgG(SvgElement):
	def parseAttributes(self):
		pass

class SvgSvg(SvgElement):
	def parseAttributes(self):
		width, height = self.attrdict.get('width'), self.attrdict.get('height')
		self.attrdict['width'] = SVGLength(self, width)
		self.attrdict['height'] = SVGLength(self, height)

		viewBox = self.attrdict.get('viewBox')
		if viewBox is not None:
			self.attrdict['viewBox'] = SVGNumberList(self, viewBox)
				
	def getSize(self):
		return self.get('width'), self.get('height')

	def getViewBox(self):
		return self.get('viewBox')


class SvgStyle(SvgElement):
	def parseAttributes(self):
		pass
	def setready(self):
		if self.cdata:
			self.textcssdefs = SVGTextCss(self, self.cdata)
		else:
			self.textcssdefs = None

	def svgrepr(self):
		textcssdefs = self.textcssdefs.getValue()
		s = '<style type=\"text/css\"><![CDATA[\n'
		for key, val in textcssdefs.items():
			s = s + '  .' + key + ' {' + repr(val) + '}\n'
		s = s + ']]></style>'
		return s

class SvgDefs(SvgElement):
	def parseAttributes(self):
		pass
	def setready(self):
		self.defs = {}
		node = self.firstchild
		while node:
			defid = node.getAttribute('id')
			if defid is not None:
				self.defs[defid] = node	
			node = node.nextsibling

class SvgUse(SvgElement):
	def parseAttributes(self):
		what = None
		href = self.getAttribute('xlink:href')
		if href is not None:
			if href[0] == '#':
				what = self.document.getElementDef(href[1:])
		self.what = what

class SvgView(SvgElement):
	def parseAttributes(self):
		pass

class SvgTspan(SvgElement):
	def parseAttributes(self):
		pass

class SvgForeignObject(SvgElement):
	def parseAttributes(self):
		pass

class SvgClipPath(SvgElement):
	def parseAttributes(self):
		pass

class SvgFeMergeNode(SvgElement):
	def parseAttributes(self):
		pass

class SvgLinearGradient(SvgElement):
	def parseAttributes(self):
		pass

class SvgAnimateTransform(SvgElement):
	def parseAttributes(self):
		pass

class SvgSwitch(SvgElement):
	def parseAttributes(self):
		pass

class SvgFilter(SvgElement):
	def parseAttributes(self):
		pass

class SvgTref(SvgElement):
	def parseAttributes(self):
		pass

class SvgAltGlyphDef(SvgElement):
	def parseAttributes(self):
		pass

class SvgMask(SvgElement):
	def parseAttributes(self):
		pass

class SvgMpath(SvgElement):
	def parseAttributes(self):
		pass

class SvgFeDiffuseLighting(SvgElement):
	def parseAttributes(self):
		pass

class SvgFontFaceFormat(SvgElement):
	def parseAttributes(self):
		pass

class SvgScript(SvgElement):
	def parseAttributes(self):
		pass

class SvgFeComponentTransfer(SvgElement):
	def parseAttributes(self):
		pass

class SvgAltGlyphItem(SvgElement):
	def parseAttributes(self):
		pass

class SvgDesc(SvgElement):
	def parseAttributes(self):
		pass

class SvgColorProfile(SvgElement):
	def parseAttributes(self):
		pass

class SvgDefinitionSrc(SvgElement):
	def parseAttributes(self):
		pass

class SvgFeMerge(SvgElement):
	def parseAttributes(self):
		pass

class SvgFeComposite(SvgElement):
	def parseAttributes(self):
		pass

class SvgFeSpecularLighting(SvgElement):
	def parseAttributes(self):
		pass

class SvgFeFuncR(SvgElement):
	def parseAttributes(self):
		pass

class SvgFeDisplacementMap(SvgElement):
	def parseAttributes(self):
		pass

class SvgAnimateColor(SvgElement):
	def parseAttributes(self):
		pass

class SvgFeDistantLight(SvgElement):
	def parseAttributes(self):
		pass

class SvgFontFaceName(SvgElement):
	def parseAttributes(self):
		pass

class SvgSymbol(SvgElement):
	def parseAttributes(self):
		pass

class SvgFeConvolveMatrix(SvgElement):
	def parseAttributes(self):
		pass

class SvgFeFuncG(SvgElement):
	def parseAttributes(self):
		pass

class SvgFeSpotLight(SvgElement):
	def parseAttributes(self):
		pass

class SvgFePointLight(SvgElement):
	def parseAttributes(self):
		pass

class SvgFeFuncB(SvgElement):
	def parseAttributes(self):
		pass

class SvgFeFuncA(SvgElement):
	def parseAttributes(self):
		pass

class SvgMetadata(SvgElement):
	def parseAttributes(self):
		pass

class SvgGlyphRef(SvgElement):
	def parseAttributes(self):
		pass

class SvgRadialGradient(SvgElement):
	def parseAttributes(self):
		pass

class SvgFeImage(SvgElement):
	def parseAttributes(self):
		pass

class SvgAnimateMotion(SvgElement):
	def parseAttributes(self):
		pass

class SvgSet(SvgElement):
	def parseAttributes(self):
		pass

class SvgFeColorMatrix(SvgElement):
	def parseAttributes(self):
		pass

class SvgVkern(SvgElement):
	def parseAttributes(self):
		pass

class SvgFeBlend(SvgElement):
	def parseAttributes(self):
		pass

class SvgFeFlood(SvgElement):
	def parseAttributes(self):
		pass

class SvgFontFaceUri(SvgElement):
	def parseAttributes(self):
		pass

class SvgPattern(SvgElement):
	def parseAttributes(self):
		pass

class SvgFeTurbulence(SvgElement):
	def parseAttributes(self):
		pass

class SvgTitle(SvgElement):
	def parseAttributes(self):
		pass

class SvgGlyph(SvgElement):
	def parseAttributes(self):
		pass

class SvgFeOffset(SvgElement):
	def parseAttributes(self):
		pass

class SvgFont(SvgElement):
	def parseAttributes(self):
		pass

class SvgAnimate(SvgElement):
	def parseAttributes(self):
		pass

class SvgAltGlyph(SvgElement):
	def parseAttributes(self):
		pass

class SvgMarker(SvgElement):
	def parseAttributes(self):
		pass

class SvgFontFaceSrc(SvgElement):
	def parseAttributes(self):
		pass

class SvgCursor(SvgElement):
	def parseAttributes(self):
		pass

class SvgMissingGlyph(SvgElement):
	def parseAttributes(self):
		pass

class SvgHkern(SvgElement):
	def parseAttributes(self):
		pass

class SvgImage(SvgElement):
	def parseAttributes(self):
		pass

class SvgTextPath(SvgElement):
	def parseAttributes(self):
		pass

class SvgStop(SvgElement):
	def parseAttributes(self):
		pass

class SvgFeMorphology(SvgElement):
	def parseAttributes(self):
		pass

class SvgFeTile(SvgElement):
	def parseAttributes(self):
		pass

class SvgA(SvgElement):
	def parseAttributes(self):
		pass

class SvgFeGaussianBlur(SvgElement):
	def parseAttributes(self):
		pass

class SvgFontFace(SvgElement):
	def parseAttributes(self):
		pass

####################################

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
		
		# other instance variables
		self.defs = []
		self.entitydefs = None

		# create DOM
		p = SvgDOMBuilder(self)
		p.feed(self.source)
		p.close()

	def svgrepr(self):
		s = '<?xml version=\"' + self.xmlversion + '\" standalone=\"' + self.xmlstandalone + '\"?>\n'
		s = s + '<!DOCTYPE svg PUBLIC \"' + self.doctypepubid + '\"\n' 
		s = s + '  \"' + self.doctypesyslit + '\">'
		return s

	def setDocType(self, tag, pubid, syslit, data):
		self.doctypetag, self.doctypepubid, self.doctypesyslit, self.doctypedata = tag, pubid, syslit, data
		if data:
			# parse any entities def
			self.entitydefs = SVGEntityDefs(self, data).getValue()

	def getEntityDefs(self):
		return self.entitydefs

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
		
	def getStyleElement(self):
		root = self.getFirstChildByType('svg')
		if root:
			return root.getFirstChildByType('style')	
		return None

	def getElementDef(self, id):
		for el in self.defs:
			what = el.defs.get(id)
			if what: return what
		return None
	
	def getDOMClassName(self, tag):
		if tag[0] == '#': # internal node
			tag = tag[1:]
		csname = 'Svg'+ tag[0].upper()
		n = len(tag)
		i = 1
		while i<n:
			if tag[i] == '-':
				i = i + 1
				csname = csname + tag[i].upper()
			else:
				csname = csname + tag[i]
			i = i + 1
		return csname
		
	def getDOMClass(self, tag):
		import svgdom # how we ref this module?
		csname = self.getDOMClassName(tag)
		elclass = getattr(svgdom, csname, SvgElement)
		if elclass == SvgElement:
			print 'missing DOM node for', `tag`
		return elclass

	def createElement(self, type):
		domclass = self.getDOMClass(type)
		el = domclass(type, self)
		if type == 'defs':
			self.defs.append(el)
		return el

	# 
	# write svg tree (print for now)
	# 
	def write(self):
		iter = DOMIterator(self, self)
		self.writesp = ''
		self.writespincr = '   '
		print self.svgrepr()
		while iter.advance(): pass

	def startnode(self, node):
		tag = node.getType()
		if tag[0] == '#' or tag == 'style':
			# internal node
			if tag == '#comment':
				print self.writesp + node.svgrepr()
			else:
				print node.svgrepr()
		elif node.getFirstChild() is None and node.data is None:
			print self.writesp + '<' + node.svgrepr() + '/>'
		else:
			if node.data is not None:
				print self.writesp + '<' + node.svgrepr() + '>',
				if node.getFirstChild() is None:
					print node.data,
				else:
					print node.data
			else:
				print self.writesp + '<' + node.svgrepr() + '>' 
			self.writesp = self.writesp + self.writespincr

	def endnode(self, node):
		tag = node.getType()
		if tag[0] == '#' or tag == 'style':
			# internal node
			pass
		elif node.getFirstChild() is None and node.data is None:
			pass
		else:
			self.writesp = self.writesp[:-len(self.writespincr)]
			if node.data is not None and node.getFirstChild() is None:
				print '</' + node.getType() + '>'
			else:
				print self.writesp + '</' + node.getType() + '>'

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
		docentitydefs = self.__document.getEntityDefs()
		if docentitydefs is not None:
			xmllib.XMLParser.entitydefs.update(docentitydefs)

	def handle_data(self, data):
		tag = self.__node.getType()
		if tag in self.dataEntities:
			self.__node.appendData(data)

	def handle_cdata(self, data):
		tag = self.__node.getType()
		if tag in self.cdataEntities:
			self.__node.appendCData(data)

	def unknown_starttag(self, tag, attrs):
		#print tag, attrs
		partag = self.__node.getType()
		content = self.entities.get(partag)
		if content is None or tag not in content:
			self.syntax_error('%s not allowed in %s' % (tag, partag))
			return
		el = self.__document.createElement(tag)
		self.__node.appendChild(el)
		el.setAttributes(attrs)
		self.__node = el
		msg = el.poperror()
		if msg:
			self.syntax_error(msg)

	def unknown_endtag(self, tag):
		self.__node.setready()
		self.__node = self.__node.getParent()
	
	def handle_comment(self, data):
		el = self.__document.createElement('#comment')
		self.__node.appendChild(el)
		el.appendData(data)
			
	def syntax_error(self, msg, lineno = None):
		msg = 'warning: syntax error on line %d: %s' % (lineno or self.lineno, msg)
		print msg

####################################
# DOM iterator

class DOMIterator:
	def __init__(self, root, listener, filter=None, trace=0):
		self.root = root
		self.listener = listener
		self.iter =  self.itForward
		self.node = root
		self.filter = filter
		self.trace = trace

	def advance(self):
		self.iter()
		return self.node != self.root

	def itForward(self):
		node = self.node.getFirstChild()
		if node:
			self.node = node
			self.startnode(node)
		elif self.node != self.root:
			node = 	self.node.getNextSibling()
			if node:
				self.endnode(self.node)
				self.node = node
				self.startnode(node)
			else:
				self.endnode(self.node)
				self.iter = self.itBackward
				node = self.node.getParent()
				self.node = node
				if self.node != self.root:
					self.endnode(self.node)
		
	def itBackward(self):
		node = self.node.getNextSibling()
		if node:
			# endnode on self.node already called
			self.iter = self.itForward
			self.node = node
			self.startnode(node)
		else:
			self.node = self.node.getParent()
			if self.node != self.root:
				self.endnode(self.node)

	def itFiltered(self):
		# self.node is in self.filter, bypass branch
		node = self.node.getNextSibling()
		if node:
			self.iter = self.itForward
			self.node = node
			self.startnode(node)
		else:
			self.iter = self.itBackward
			node = self.node.getParent()
			self.node = node
			if self.node != self.root:
				self.endnode(self.node)
			
	def startnode(self, node):
		if self.filter and node.getType() in self.filter:
			 self.itFiltered()
		elif self.listener:
			if self.trace:
				print '<' + node.getType() + '>'
			self.listener.startnode(node)

	def endnode(self, node):
		if self.filter and node.getType() in self.filter:
			 assert 0, 'endnode call on filtered node' 
		elif self.listener:
			if self.trace:
				print '</' + node.getType() + '>'
			self.listener.endnode(node)

####################################
# utilities

def GetSvgSizeFromSrc(source):
	svg = SvgDocument(source)
	root =  svg.getRoot()
	if not root or root.getType()!='svg':
		return 0, 0
	width, height = root.getSize()
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
    <rect x="300" y="30" width="20" height="20" transform="rotate(90)"/>
  </g>
</svg>"""

if __name__ == '__main__':
    #print GetSvgSizeFromSrc(svgSource)
	svg = SvgDocument(svgSource)
	svg.write()


