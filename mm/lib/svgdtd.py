__version__ = "$Id$"

#
#	SVG DTD
#

SVGpubid = "-//W3C//DTD SVG 20001102//EN"
SVGdtd = "http://www.w3.org/TR/2000/CR-SVG-20001102/DTD/svg-20001102.dtd"
SVGns = "http://www.w3.org/2000/svg"

NSSVGprefix = 'svg'
xmlnsSVG = 'xmlns:%s' % NSSVGprefix

smil2extensions = 1

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
		'stroke-antialiasing': None,
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

	attrset['%rectAttrs'] =	{'x': '0',
		'y': '0',
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
		'begin': None,
		'end': None,
		'min': None,
		'max': None,
		'restart': 'always',
		'repeatCount': None,
		'repeatDur': None,
		'fill': 'remove','smil:fill':'remove',}
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

	if smil2extensions:
		attrset['%timeManipulations'] = {'speed':None,
		    'accelerate':None,
		    'decelerate':None,
		    'autoReverse':None,}
		attrset['%timeIntegration'] = {'timeContainer':'none',
		    'timeAction':'intrinsic',}
		attrset['%timeContainers'] = {'endsync':None,}
		attrset['%extraTiming'] = {'fillDefault':None,
		    'restart':None,
		    'restartDefault':None,
		    'syncBehavior':None,
		    'syncBehaviorDefault':None,
		    'syncMaster':None,
		    'syncTolerance':None,
		    'syncToleranceDefault':None,}

	##############
	# attributes
	attributes = {
		'svg': {'width': None, 
			'height': None, 
			'viewBox': None,
			'preserveAspectRatio': None,
			'zoomAndPan': 'magnify',
			'x': '0',
			'y': '0',
			'contentScriptType': 'text/ecmascript',
			'contentStyleType': 'text/css',
			'%presentAttrsAllEx': None,
			'%graphicsElementEvents': None,
 			'%documentEvents': None,},
		'g': {'transform': None,
			'%presentAttrsAllEx': None,
			'%graphicsElementEvents': None,},
		'defs': {'transform': None,
			'%presentAttrsAllEx': None,
			'%graphicsElementEvents': None,},
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
			'cx': '0',
			'cy': '0',
			'r': None,
			},
		'ellipse':{'%shapeAttrs': None,
			'cx': '0',
			'cy': '0',
			'rx': None,
			'ry': None,
			},
		'line':{'%pathAttrs': None,
			'x1': '0',
			'y1': '0',
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
			'x': '0',
			'y': '0',
			'textLength': None,
			'lengthAdjust': None,
			'%textAttrs': None,
			'%presentAttrsTextElements': None},
		'tspan':{'rotate': None,
			'x': '0',
			'y': '0',
			'dx': None,
			'dy': None,
			'textLength': None,
			'lengthAdjust': None,
			'%textAttrs': None,},
		'tref':{'rotate': None,
			'xlink:href': None,
			'%xlinkRefAttrs': None,
			'x': '0',
			'y': '0',
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
			'x': '0',
			'y': '0',
			'dx': None,
			'dy': None,
			'%textAttrs': None,},
		'altGlyphDef':{},
		'altGlyphItem':{},
		'glyphRef':{'xlink:href': None,
			'%xlinkRefAttrs': None,
			'glyphRef': None,
			'format': None,
			'x': '0',
			'y': '0',
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
			'origin': 'default', },
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
			'x': '0',
			'y': '0',
			'width': None,
			'height': None,
			'%presentAttrsAllEx': None,
			'%graphicsElementEvents': None,},
		}
  	
	##############
	# all elements with their allowed content
	# elements without an entry are leaf elements
	entities = {}

	__dtm = ['desc', 'title', 'metadata']

	__animations = ['animate','set','animateMotion','animateColor','animateTransform',]
	__timeContainers = ['par', 'seq', 'excl',]

	__core = __dtm + __animations
	if smil2extensions:
		for name in __timeContainers:
			__core.append(name)

	__lineArt = ['path','text','rect','circle','ellipse','line','polyline','polygon',]
	
	__controlsCore = ['use','image','svg','g','switch','a','foreignObject',]

	__fe = ['feSpotLight', 'feBlend', 'feColorMatrix', 'feFuncR','feFuncG',
			'feFuncB','feFuncA','feConvolveMatrix','feDisplacementMap','feGaussianBlur',
			'feMergeNode','feMorphology', 'feOffset','feTile', 'feTurbulence',]

	__feanim = ['animate','set',]

	__svg = ['desc', 'title', 'metadata', 'defs',
             'path', 'text', 'rect', 'circle', 'ellipse', 'line', 'polyline', 'polygon',
             'use','image','svg','g','view','switch','a','altGlyphDef',
             'script','style','symbol','marker','clipPath','mask',
             'linearGradient','radialGradient','pattern','filter','cursor','font',
             'animate','set','animateMotion','animateColor','animateTransform',
             'color-profile','font-face']
	if smil2extensions:
		for name in __timeContainers:
			__svg.append(name)

	entities['#document'] = ['svg', ]
	entities['svg'] = __svg      	
	entities['g'] = __svg      	
	entities['defs'] = __svg      	
	entities['symbol'] = __svg 
	entities['marker'] = __svg  
	entities['pattern'] = __svg  
	entities['mask'] = __svg  
	entities['a'] = __svg  
	entities['glyph'] = __svg  
	entities['missing-glyph'] = __svg  
                   
	entities['use'] = __core
	entities['image'] = __core
	entities['switch'] = __core + __lineArt + __controlsCore
	for name in __lineArt:
		entities[name] = __core
	entities['text'] = __core + ['tspan', 'tref', 'textPath', 'altGlyph', 'a',]
	entities['tspan'] = __dtm + ['tspan', 'tref', 'altGlyph', 'a', 'animate', 'set', 'animateColor']
	entities['tref'] = __dtm + ['animate', 'set', 'animateColor']
	entities['textPath'] = entities['tspan']
	entities['altGlyphDef'] = ['glyphRef', 'altGlyphItem', ]
	entities['altGlyphItem'] = ['glyphRef']

	entities['linearGradient'] = __dtm + ['stop','animate','set','animateTransform']
	entities['radialGradient'] = entities['linearGradient']
	entities['stop'] = ['animate','set','animateColor', ]

	entities['clipPath'] = __core + __lineArt + ['use', ]
	entities['filter'] = __dtm + ['feBlend','feFlood',
		'feColorMatrix','feComponentTransfer',
		'feComposite','feConvolveMatrix','feDiffuseLighting','feDisplacementMap',
		'feGaussianBlur','feImage','feMerge',
		'feMorphology','feOffset','feSpecularLighting',
		'feTile','feTurbulence',] + ['animate','set',]

	temp = ['animate','set',]
	entities['feDistantLight'] = temp[:]
	for name in __fe:
		entities[name] = __feanim
	entities['feComponentTransfer'] = ['feFuncR','feFuncG','feFuncB','feFuncA',]
	entities['feDiffuseLighting'] = __feanim + ['feDistantLight','fePointLight','feSpotLight', 'animateColor',]
	entities['feFlood'] = __feanim + ['animateColor',]
	entities['feImage'] = __feanim + ['animateTransform',]
	entities['feMerge'] = ['feMergeNode', ]
	entities['feSpecularLighting'] = entities['feDiffuseLighting']

	entities['view'] = __dtm
	for name in __animations:
		if name == 'animateMotion':
			entities[name] = __dtm + ['mpath',]
		else:
			entities[name] = __dtm
	entities['mpath'] = __dtm	
	entities['font'] = __dtm	+ ['font-face', 'missing-glyph', 'glyph', 'hkern', 'vkern', ]
	entities['font-face'] = __dtm	+ ['font-face-src', 'definition-src', ]
	entities['font-face-src'] = ['font-face-uri', 'font-face-name', ]
	entities['font-face-uri'] = ['font-face-format', ]

	if smil2extensions:
		for name in __timeContainers:
			entities[name] = __svg

	dataEntities = ['title', 'desc', 'text', ]
	cdataEntities = ['style', ]
	timeEntities = __animations + __timeContainers

	##############
	# update element sets with std collections
	# build entities entries with their allowed content
	for __el in attributes.keys():
		attributes[__el]['id'] = None
		for attr in attributes[__el].keys():
			if attr[0]=='%': # attr set macro
				attributes[__el].update(attrset[attr])
				del attributes[__el][attr]
			
	if smil2extensions:
		del attrset['%animTimingAttrs']['fill']
		for __el in attributes.keys():
			if entities.get(__el) and 'set' in entities[__el]:
				attributes[__el].update(attrset['%animTimingAttrs'])
				attributes[__el].update(attrset['%extraTiming'])

	del __el

	##############
	if smil2extensions:
		for name in __animations:
			attributes[name].update(attrset['%timeManipulations'])
		for name in ('svg', 'g'):
			attributes[name].update(attrset['%timeIntegration'])
			attributes[name].update(attrset['%timeContainers'])
		for name in __timeContainers:
			attributes[name] = attrset['%animationCore'].copy()
			attributes[name].update(attrset['%timeContainers'])
	##############
	# cleanup
	del __dtm
	del __animations
	del __timeContainers
	del __core
	del __lineArt
	del __controlsCore
	del __fe
	del __feanim
	del __svg
	presentationAttrs = attrset['%presentAttrsAllEx'].copy()
	del attrset


##############
# CAD helpers

def GetDOMClassName(tag):
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

def PrintDOMClasses():
	svgelements = SVG.attributes.keys()
	exltags = ()
	for tag in svgelements:
		if tag not in exltags:
			csname = GetDOMClassName(tag)
			print 'class '+ csname + '(SvgElement):'
			print '\tdef parseAttributes(self):'		
			print '\t\tSvgElement.parseAttributes(self)'		
			print ''	

def PrintDOMAttrs():
	svgelements = SVG.attributes.keys()
	exltags = ['animate','set','animateMotion','animateColor','animateTransform',]
	attrdict = {}
	for tag in svgelements:
		if tag not in exltags:
			attrs = SVG.attributes[tag]
			for name, defval in attrs.items():
				attrdict[name] = defval
	print '# svg attribute defs'
	print 'SVGAttrdefs = {',
	keys = attrdict.keys()
	keys.sort()
	for name in keys:
		defval = attrdict[name]
		entry = '\t%s: (stringtype, %s),' % (`name`, `defval`)
		print entry
	print '\t}',

if __debug__:
	def PrintSelDOMAttrs():
		elements = ['svg',]
		attrdict = {}
		for tag in elements:
			attrs = SVG.attributes[tag]
			for name, defval in attrs.items():
				attrdict[name] = defval
		print '# svg attribute defs'
		print 'SVGAttrdefs = {',
		keys = attrdict.keys()
		keys.sort()
		for name in keys:
			defval = attrdict[name]
			entry = '\t%s: (stringtype, %s),' % (`name`, `defval`)
			print entry
		print '\t}',

	if __name__ == '__main__':
		PrintSelDOMAttrs()
