__version__ = "$Id$"

import xmllib

import string

# Partial SVG parser

####################################
# partial svg dtd

SVGpubid = "-//W3C//DTD SVG 20001102//EN"
SVGdtd = "http://www.w3.org/TR/2000/CR-SVG-20001102/DTD/svg-20001102.dtd"

class SVGAttrdefs:
	pass

class SVG:
	# collections of attributes
	attrset = {}
	
	# attrset['%stdAttrs'] = {'id': None,}
	attrset['%langSpaceAttrs'] = {'xml:lang': None,
		'xml:space': None,}
	attrset['%styleAttrs'] = {'class':None,
		  'style':None,}
	attrset['%testAttrs'] = {'requiredFeatures': None,
		'requiredExtensions': None,
		'systemLanguage': None,
		'externalResourcesRequired': None,}

	temp =  attrset['%langSpaceAttrs'].copy()
	temp.update(attrset['%testAttrs'])
	temp.update(attrset['%styleAttrs'])
	attrset['%styleAttrsEx'] = temp
	del temp

	attrset['%presentAttrsContainers'] = {'enable-background': None,}
	attrset['%presentAttrsFeFlood'] = {'flood-color': None,
		'flood-opacity': None,}
	attrset['%presentAttrsFillStroke'] = {'fill': None,
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
	attrset['%presentAttrsFontSpecification'] = {'font-family': None,
		'font-size': None,
		'font-size-adjust': None,
		'font-stretch': None,
		'font-style': None,
		'font-variant': None,
		'font-weight': None,}
	attrset['%presentAttrsGradients'] = {'stop-color': None,
		'stop-opacity': None,}

	temp = attrset['%presentAttrsGradients'].copy()
	temp.update(attrset['%styleAttrsEx'])
	attrset['%presentAttrsGradientsEx'] = temp
	del temp

	attrset['%presentAttrsGraphics'] = {'clip-path':None,
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
	attrset['%presentAttrsImages'] = {'color-profile': None,}
	attrset['%presentAttrsLightingEffects'] = {'lighting-color': None,}
	attrset['%presentAttrsMarkers'] = {'marker-start': None,
		'marker-mid': None,
		'marker-end': None,}
	attrset['%presentAttrsTextContentElements'] = {'alignment-baseline': None,
		'baseline-shift': None,
		'direction': None,
		'glyph-orientation-horizontal': None,
		'glyph-orientation-vertical': None,
		'kerning': None,
		'letter-spacin': None,
		'text-decoration': None,
		'unicode-bidi': None,
		'word-spacing': None,}
	attrset['%presentAttrsTextElements'] = {'dominant-baseline': None,
		'text-anchor': None,
		'writing-mode': None,}
	attrset['%presentAttrsViewports'] = {'clip': None,
		'overflow': None,}
	temp = attrset['%presentAttrsContainers'].copy()
	temp.update(attrset['%presentAttrsFeFlood'])
	temp.update(attrset['%presentAttrsFillStroke'])
	temp.update(attrset['%presentAttrsFontSpecification'])
	temp.update(attrset['%presentAttrsGradients'])
	temp.update(attrset['%presentAttrsGraphics'])
	temp.update(attrset['%presentAttrsImages'])
	temp.update(attrset['%presentAttrsLightingEffects'])
	temp.update(attrset['%presentAttrsMarkers'])
	temp.update(attrset['%presentAttrsTextContentElements'])
	temp.update(attrset['%presentAttrsTextElements'])
	temp.update(attrset['%presentAttrsViewports'])
	attrset['%presentAttrsAll'] = temp.copy()

	temp.update(attrset['%testAttrs'])
	temp.update(attrset['%langSpaceAttrs'])
	temp.update(attrset['%styleAttrs'])
	attrset['%presentAttrsAllEx'] = temp
	del temp

	attrset['%xlinkRefAttrs'] = {'xlink:type': 'simple',
		'xlink:role': None,
		'xlink:arcrole': None,
		'xlink:title': None,
		'xlink:show': 'embed',
		'xlink:actuate': 'onLoad',}

	attrset['%rectAttrs'] =	{'x': None,
		'y': None,
		'width': None,
		'height': None,}

	temp  = {'result': None,}
	temp.update(attrset['%rectAttrs'])
	attrset['%filterPrimitiveAttrs'] = temp
	del temp	

	attrset['%componentTransferFunctionAtrs'] = {'type': None,
		'tableValues': None,
		'slope': None,
		'intercept': None,
		'amplitude': None,
		'exponent': None,
		'offset': None,
		}

	attrset['%documentEvents'] = {}
	attrset['%graphicsElementEvents'] = {}		
	attrset['%animationEvents'] = {}
  
	# animation
	attrset['%animTimingAttrs'] = {'dur': None,
		'end': None,
		'min': None,
		'max': None,
		'restart': 'always',
		'repeatCount': None,
		'repeatDur': None,
		'fill': 'remove',}
	attrset['%animValueAttrs'] = {'values': None,
		'keyTimes': None,
		'keySplines': None,
		'from': None,
		'to': None,
		'by': None,}
	temp = {'xlink:href': None, }
	temp.update(attrset['%testAttrs'])
	temp.update(attrset['%xlinkRefAttrs'])
	temp.update(attrset['%animationEvents'])
	temp.update(attrset['%animTimingAttrs'])
	attrset['%animationCore'] = temp
	del temp

	# logical groups
	# %shapeAttrs
	temp = {'transform': None}
	temp.update(attrset['%testAttrs'])
	temp.update(attrset['%langSpaceAttrs'])
	temp.update(attrset['%styleAttrs'])
	temp.update(attrset['%presentAttrsFillStroke'])
	temp.update(attrset['%presentAttrsGraphics'])
	temp.update(attrset['%graphicsElementEvents'])
	attrset['%shapeAttrs'] = temp.copy()

	# %pathAttrs
	temp.update(attrset['%presentAttrsMarkers'])
	attrset['%pathAttrs'] = temp
	del temp

	# %textAttrs
	temp = {}
	temp.update(attrset['%testAttrs'])
	temp.update(attrset['%langSpaceAttrs'])
	temp.update(attrset['%styleAttrs'])
	temp.update(attrset['%presentAttrsFillStroke'])
	temp.update(attrset['%presentAttrsGraphics'])
	temp.update(attrset['%graphicsElementEvents'])
	temp.update(attrset['%presentAttrsFontSpecification'])
	temp.update(attrset['%presentAttrsTextContentElements'])
	attrset['%textAttrs'] = temp
	del temp

	##############
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
			'%presentAttrsAllEx': None,
			'%graphicsElementEvents': None,
 			'%documentEvents': None,
			'$content': 'allElements'},
		'g': {'transform': None,
			'%presentAttrsAllEx': None,
			'%graphicsElementEvents': None,
			'$content': 'allElements'},
		'defs': {'transform': None,
			'%presentAttrsAllEx': None,
			'%graphicsElementEvents': None,
			'$content': 'allElements',},
		'desc': {'%langSpaceAttrs': None,
			'%styleAttrs': None,},
		'title': {'%langSpaceAttrs': None,
			'%styleAttrs': None,},
		'symbol': {'viewBox': None,
			'preserveAspectRatio': None,
			'externalResourcesRequired': None,
			'%langSpaceAttrs': None,
			'%styleAttrs': None,
			'%presentAttrsAll': None,
			'%graphicsElementEvents': None,},
		'use': {'transform': None,
			'%rectAttrs': None,
			'xlink:href': None, 
			'%xlinkRefAttrs': None,
			'%presentAttrsAllEx': None,
			'%graphicsElementEvents': None,},
		'image': {'transform': None,
			'preserveAspectRatio': None,
			'%rectAttrs': None,
			'xlink:href': None, 
			'%xlinkRefAttrs': None,
			'%testAttrs': None,
			'%langSpaceAttrs': None,
			'%styleAttrs': None,
			'%presentAttrsGraphics': None,
			'%presentAttrsImages': None,
			'%presentAttrsViewports': None,
			'%graphicsElementEvents': None,},
		'switch': {'transform': None,
			'%testAttrs': None,
			'%langSpaceAttrs': None,
			'%styleAttrs': None,
			'%presentAttrsAll': None,
			'%graphicsElementEvents': None,},
		'style': {'xml:space': 'preserve',
			'type': None,
			'media': None,
			'title': None,
			},
		'path':{'%pathAttrs': None,
			'd': None,
			'pathLength': None,},
		'rect':{'%shapeAttrs': None,
			'%rectAttrs': None,
			'rx': None,
			'ry': None,},
		'circle':{'%shapeAttrs': None,
			'cx': None,
			'cy': None,
			'r': None,
			},
		'ellipse':{'%shapeAttrs': None,
			'cx': None,
			'cy': None,
			'rx': None,
			'ry': None,
			},
		'line':{'%pathAttrs': None,
			'x1': None,
			'y1': None,
			'x2': None,
			'y2': None,
			},
		'polyline':{'%pathAttrs': None,
			'points': None,
			},
		'polygon':{'%pathAttrs': None,
			'points': None,
			},
		'text':{'transform': None,
			'x': None,
			'y': None,
			'textLength': None,
			'lengthAdjust': None,
			'%textAttrs': None,
			'%presentAttrsTextElements': None},
		'tspan':{'rotate': None,
			'x': None,
			'y': None,
			'dx': None,
			'dy': None,
			'textLength': None,
			'lengthAdjust': None,
			'%textAttrs': None,},
		'tref':{'rotate': None,
			'xlink:href': None,
			'%xlinkRefAttrs': None,
			'x': None,
			'y': None,
			'dx': None,
			'dy': None,
			'textLength': None,
			'lengthAdjust': None,
			'%textAttrs': None},
		'textPath':{'startOffset': None,
			'textLength': None,
			'lengthAdjust': None,
			'method': None,
			'spacing': None,
			'xlink:href': None,
			'%xlinkRefAttrs': None,
			'%textAttrs': None,},
		'altGlyph':{'rotate': None,
			'xlink:href': None,
			'%xlinkRefAttrs': None,
			'glyphRef': None,
			'format': None,
			'x': None,
			'y': None,
			'dx': None,
			'dy': None,
			'%textAttrs': None,},
		'altGlyphDef':{},
		'altGlyphItem':{},
		'glyphRef':{'xlink:href': None,
			'%xlinkRefAttrs': None,
			'glyphRef': None,
			'format': None,
			'x': None,
			'y': None,
			'dx': None,
			'dy': None,
			'%styleAttrs': None, 
			'%presentAttrsFontSpecification': None},

		# markers
		'marker': {'viewBox': None,
			'preserveAspectRatio': None,
			'refX': None,
			'refY': None,
			'markerUnits': None,
			'markerWidth': None,
			'markerHeight': None,
			'orient': None,
			'%presentAttrsAllEx': None,},

		# color
		'color-profile': {'xlink:href': None,
			'%xlinkRefAttrs': None,
			'local': None,
			'name': None,
			'rendering-intent': 'auto',},

		# gradients
		'linearGradient': {'xlink:href': None,
			'%xlinkRefAttrs': None,
			'gradientUnits': None,
			'gradientTransform': None,
			'x1': None,
			'y1': None,
			'x2': None,
			'y2': None,
			'spreadMethod': None,
			'%presentAttrsGradientsEx': None,},
		'radialGradient': {'xlink:href': None,
			'%xlinkRefAttrs': None,
			'gradientUnits': None,
			'gradientTransform': None,
			'cx': None,
			'cy': None,
			'r': None,
			'fx': None,
			'fy': None,
			'spreadMethod': None,
			'%presentAttrsGradientsEx': None,},
		'stop': {'offset': None, 
			'%presentAttrsGradients': None, 
			'%styleAttrs': None},

		'pattern': {'xlink:href': None,
			'%xlinkRefAttrs': None,
			'viewBox': None,
			'preserveAspectRatio': None,
			'patternUnits': None,
			'patternContentUnits': None,
			'patternTransform': None,
			'%rectAttrs': None,
			'%presentAttrsAllEx': None,},

		# clipping
		'clipPath': {'%shapeAttrs': None,
			'%presentAttrsFontSpecification': None, 
			'%presentAttrsTextContentElements': None, 
			'%presentAttrsTextElements': None, 
			'transform': None,
			'clipPathUnits': None,},
		'mask': {'transform': None,
			'maskUnits': None,
			'maskContentUnits': None,
			'%rectAttrs': None,
			'%presentAttrsAllEx': None,},

		# filters
		'filter': {'xlink:href': None,
			'%xlinkRefAttrs': None,
			'%langSpaceAttrs': None,
			'externalResourcesRequired': None,
			'%styleAttrs': None,
			'%presentAttrsAll': None, 
			'filterUnits': None,
			'primitiveUnits': None,
			'%rectAttrs': None,
			'filterRes': None,},
		'feDistantLight': {'azimuth': None, 'elevation': None,},
		'fePointLight': {'x': None, 'y': None, 'z': None,},
		'feSpotLight': {'x': None, 'y': None, 'z': None,
			'pointsAtX': None, 'pointsAtY': None, 'pointsAtZ': None,
			'specularExponent': None, 'limitingConeAngle': None,},
		'feBlend': {'%filterPrimitiveAttrs': None, 'in': None, 'in2': None, 'mode': 'normal',},
		'feColorMatrix': {'%filterPrimitiveAttrs': None, 'in': None, 'type': 'matrix', 'values': None,},
		'feComponentTransfer': {'%filterPrimitiveAttrs': None, 'in': None},
		'feFuncR': {'%componentTransferFunctionAtrs': None},
		'feFuncG': {'%componentTransferFunctionAtrs': None},
		'feFuncB': {'%componentTransferFunctionAtrs': None},
		'feFuncA': {'%componentTransferFunctionAtrs': None},
		'feComposite': {'%filterPrimitiveAttrs': None, 'in': None, 'in2': None, 'operator': 'over',
			'k1': None, 'k2': None, 'k3': None, 'k4': None},
		'feConvolveMatrix': {'%filterPrimitiveAttrs': None, 'in': None, 
			'order': None, 
			'kernelMatrix': None, 
			'divisor': None, 
			'bias': None, 
			'targetX': None, 
			'targetY': None, 
			'edgeMode': 'duplicate', 
			'kernelUnitLength': None, 
			'preserveAlpha': None, },
		'feDiffuseLighting': {'%styleAttrs': None,
			'%presentAttrsLightingEffects': None,
			'%filterPrimitiveAttrs': None, 'in': None,
			'surfaceScale': None,
			'diffuseConstant': None,},
		'feDisplacementMap': {'%filterPrimitiveAttrs': None, 'in': None, 'in2': None, 
			'scale': None,
			'xChannelSelector': 'A',
			'yChannelSelector': 'A',},
		'feFlood': {'%filterPrimitiveAttrs': None, 'in': None,
			'%styleAttrs': None,
			'%presentAttrsFeFlood': None,}, 
		'feGaussianBlur': {'%filterPrimitiveAttrs': None, 'in': None, 'stdDeviation': None,},
		'feImage': {'%filterPrimitiveAttrs': None,
			'xlink:href': None,
			'%xlinkRefAttrs': None,
			'%langSpaceAttrs': None,
			'externalResourcesRequired': None,
			'%styleAttrs': None,
			'%presentAttrsAll': None,
			'transform': None,},
		'feMerge': {'%filterPrimitiveAttrs': None,}, 
		'feMergeNode': {'in': None,}, 
		'feMorphology': {'%filterPrimitiveAttrs': None, 'in': None, 
			'operator': 'erode', 'radius': None,},
		'feOffset': {'%filterPrimitiveAttrs': None, 'in': None, 
			'dx': None, 'dy': None,},
		'feSpecularLighting': {'%styleAttrs': None,
			'%presentAttrsLightingEffects': None,
			'%filterPrimitiveAttrs': None, 'in': None,
			'surfaceScale': None,
			'specularConstant': None,
			'specularExponent': None,},
		'feTile': {'%filterPrimitiveAttrs': None, 'in': None, },
		'feTurbulence': {'%filterPrimitiveAttrs': None,
			'baseFrequency': None, 'numOctaves': None, 
			'seed': None, 'stitchTiles': 'noStitch', 'type': 'turbulence',},

		# interactivity
		'cursor': {'xlink:href': None, '%xlinkRefAttrs': None,
			'%testAttrs': None,
			'externalResourcesRequired': None,
			'x': None, 'y': None,},

		# linking
		'a': {'xlink:href': None, '%xlinkRefAttrs': None,
			'%styleAttrsEx': None,
			'%presentAttrsAll': None,
			'transform': None,
			'%graphicsElementEvents': None,
			'target': None,},
		'view': {'externalResourcesRequired': None,
			'viewBox': None,
			'preserveAspectRatio': None,
			'zoomAndPan': 'magnify',
			'viewTarget': None, },
		
		# fonts
		'font': {'%styleAttrsEx': None,
			'%presentAttrsAll': None,
			'horiz-origin-x': None,
			'horiz-origin-y': None,
			'vert-origin-x': None,
			'vert-origin-y': None,
			'horiz-adv-x': None,
			'vert-adv-y': None,},
		'glyph': {'%styleAttrsEx': None,
			'%presentAttrsAll': None,
			'unicode': None, 
			'glyph-name': None, 
			'd': None, 
			'orientation': None, 
			'arabic-form': None, 
			'lang': None, 
			'vert-origin-x': None, 
			'vert-origin-y': None, 
			'horiz-adv-x': None, 
			'vert-adv-y': None,},
		'missing-glyph': {'%styleAttrsEx': None,
			'%presentAttrsAll': None,
			'd': None, 
			'vert-origin-x': None, 
			'vert-origin-y': None, 
			'horiz-adv-x': None, 
			'vert-adv-y': None,},
		'hkern': {'u1': None, 'g1': None, 'u2': None, 'g2': None, 'k': None,},
		'vkern': {'u1': None, 'g1': None, 'u2': None, 'g2': None, 'k': None,},
		'font-face': {'font-family': None,
			'font-style': None, 'font-variant': None, 'font-weight': None,
			'font-stretch': None, 'font-size': None, 'unicode-range': None,
			'units-per-em': None, 'panose-1': None, 'stemv': None,
			'stemh': None, 'slope': None, 'cap-height': None,
			'x-height': None, 'accent-height': None, 'ascent': None,
			'descent': None, 'widths': None, 'bbox': None,
			'ideographic': None, 'alphabetic': None, 
			'mathematical': None, 'hanging': None,
			'v-ideographic': None, 'v-alphabetic': None, 
			'v-mathematical': None, 'v-hanging': None, 
			'underline-position': None, 'underline-thickness': None, 
			'strikethrough-position': None, 'strikethrough-thickness': None,
			'overline-position': None, 'overline-thickness': None},
		'font-face-src': {},
		'font-face-uri': {'xlink:href': None, '%xlinkRefAttrs': None},
		'font-face-format': {},
		'font-face-name': {'name': None},
		'definition-src': {'xlink:href': None, '%xlinkRefAttrs': None},

		# animation
		'animate': {'%animationCore': None,
			'attributeName': None, 
			'attributeType': None,
			'calcMode': 'linear', 
			'additive': 'replace', 
			'accumulate': 'none', 
			'%animValueAttrs': None,},
		'set': {'%animationCore': None,
			'attributeName': None, 
			'attributeType': None,
			'to': None,},
		'animateMotion': {'%animationCore': None,
			'additive': 'replace', 
			'accumulate': 'none', 
			'%animValueAttrs': None,
			'calcMode': 'paced', 
			'path': None, 
			'keyPoints': None, 
			'rotate': None, 
			'origin': None, },
		'animateColor': {'%animationCore': None,
			'attributeName': None, 
			'attributeType': None,
			'%animValueAttrs': None, 
			'calcMode': 'linear', 
			'additive': 'replace', 
			'accumulate': 'none',},
		'animateTransform': {'%animationCore': None,
			'attributeName': None, 
			'attributeType': None,
			'%animValueAttrs': None, 
			'calcMode': 'linear', 
			'additive': 'replace', 
			'accumulate': 'none', 
			'type': 'translate',},
		'mpath': {'%xlinkRefAttrs': None,
			'xlink:href': None, 
			'externalResourcesRequired': None, },

		# scripting
		'script': {'xlink:href': None,
			'%xlinkRefAttrs': None,
			'externalResourcesRequired': None,
			'type': None,},

		# extensibility
		'metadata': {},
		'foreignObject':{'transform': None,
			'x': None,
			'y': None,
			'width': None,
			'height': None,
			'%presentAttrsAllEx': None,
			'%graphicsElementEvents': None,},
		}
  	
	##############
	# collections of elements contents
	elemset = {}
	elemset['allElements'] = attributes.keys()


	##############
	# all elements with their allowed content
	# elements without an entry are leaf elements
	entities = {}

	# update element sets with std collections
	# build entities entries with their allowed content
	for __el, __elattrs in attributes.items():
		attributes[__el]['id'] = None
		for attr in __elattrs.keys():
			if attr[0]=='%': # attr set macro
				attributes[__el].update(attrset[attr])
				del __elattrs[attr]
			elif attr[0]=='$': # content macro
				entities[__el] = elemset[__elattrs[attr]]
				del __elattrs[attr]
		del attr
	del __el, __elattrs

	##############
	# cleanup
	del attrset
	del elemset

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
	units = val[-2:]
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

