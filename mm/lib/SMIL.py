__version__ = "$Id$"

EVALcomment = ' Created with an evaluation copy of GRiNS '
SMIL_BASIC = 'text/smil-basic-layout'
SMILpubid = "-//W3C//DTD SMIL 1.0//EN"
SMILdtd = "http://www.w3.org/TR/REC-smil/SMIL10.dtd"
SMIL1 = 'http://www.w3.org/TR/REC-smil'
SMILBostonPubid = "-//W3C//DTD SMIL 2.0//EN"
SMILBostonDtd = "http://www.w3.org/TR/REC-smil/2000/SMIL20.dtd"
SMIL2 = 'http://www.w3.org/TR/REC-smil/2000/SMIL20'
GRiNSns = "http://www.oratrix.com/"
QTns = "http://www.apple.com/quicktime/resources/smilextensions"

import string

class SMIL:
	# some abbreviations
	__layouts = GRiNSns + ' ' + 'layouts'
	__layout = GRiNSns + ' ' + 'layout'
	__choice = GRiNSns + ' ' 'choice'
	__bag = GRiNSns + ' ' 'bag'
	__null = GRiNSns + ' ' 'null'
	__cmif = GRiNSns + ' ' 'cmif'
	__shell = GRiNSns + ' ' 'shell'
	__socket = GRiNSns + ' ' 'socket'

	# abbreviations for collections of attributes
	__Core = {'id':None,
		  'class':None,
		  'title':None,}
	__I18n = {'xml:lang':None,}
	__Test = {'system-bitrate':None,
		  'system-captions':None,
		  'system-language':None,
		  'system-overdub-or-caption':None,
		  'system-required':None,
		  'system-screen-depth':None,
		  'system-screen-size':None,
		  SMIL2+' '+'systemAudioDesc':None,
		  SMIL2+' '+'systemBitrate':None,
		  SMIL2+' '+'systemCaptions':None,
		  SMIL2+' '+'systemComponent':None,
		  SMIL2+' '+'systemCPU':None,
		  SMIL2+' '+'systemLanguage':None,
		  SMIL2+' '+'systemOperatingSystem':None,
		  SMIL2+' '+'systemOverdubOrSubtitle':None,
		  SMIL2+' '+'systemRequired':None,
		  SMIL2+' '+'systemScreenDepth':None,
		  SMIL2+' '+'systemScreenSize':None,}
	__basicTiming = {'begin':None,
			 'dur':None,
			 'end':None,
			 SMIL2+' '+'max':None,
			 SMIL2+' '+'min':None,
			 'repeat':None,
			 SMIL2+' '+'repeatCount':None,
			 SMIL2+' '+'repeatDur':None,
			 }
	__Timing = {'fill':None,
		    SMIL2+' '+'fillDefault':None,
		    SMIL2+' '+'restart':None,
		    SMIL2+' '+'restartDefault':None,
		    SMIL2+' '+'syncBehavior':None,
		    SMIL2+' '+'syncBehaviorDefault':None,
		    SMIL2+' '+'syncMaster':None,
		    SMIL2+' '+'syncTolerance':None,
		    SMIL2+' '+'syncToleranceDefault':None,
		    }
	__Timing.update(__basicTiming)

	# all allowed entities with all their attributes
	attributes = {
		'smil': {QTns+' ' 'time-slider':None,
			 QTns+' ' 'next':None,
			 QTns+' ' 'autoplay':None,
			 QTns+' ' 'chapter-mode':None,
			 QTns+' ' 'immediate-instantiation':None,
			 },
		'head': {},
		'body': {'abstract':'',
			 'author':'',
			 'copyright':'',
			 SMIL2+' '+'customTest':None,
			 __layout:None,
			 GRiNSns+' ' 'comment':None,
			 },
		'meta': {'content':None,
			 'name':None,
			 },
		'metadata': {},
		'layout': {'type':SMIL_BASIC,
			   },
		'root-layout': {'background-color':'transparent',
				SMIL2+' '+'backgroundColor':None,
				SMIL2+' '+'customTest':None,
				'height':'0',
				'skip-content':'true',
				'width':'0',
				},
		'viewport': {'background-color':'transparent',
				       'backgroundColor':None,
				       'customTest':None,
				       'height':'0',
				       'skip-content':'true',
				       'width':'0',
				       'close':'never',
				       'open':'always',
				       },
		'region': {'background-color':'transparent',
			   SMIL2+' '+'backgroundColor':None,
			   SMIL2+' '+'bottom':None,
			   SMIL2+' '+'customTest':None,
			   'fit':'hidden',
			   'height':None,
			   'left':None,
			   SMIL2+' '+'regAlign':None,
			   SMIL2+' '+'regPoint':None,
			   'right':None,
			   SMIL2+' '+'showBackground':None,
			   'skip-content':'true',
			   SMIL2+' '+'soundLevel':None,
			   'top':None,
			   'width':None,
			   'z-index':'0',
			   SMIL2+' '+'regionName': None,
			   GRiNSns+' ' 'border':None,
			   GRiNSns+' ' 'bucolor':None,
			   GRiNSns+' ' 'center':None,
			   GRiNSns+' ' 'comment':None,
			   GRiNSns+' ' 'drawbox':None,
			   GRiNSns+' ' 'duration':None,
			   GRiNSns+' ' 'fgcolor':None,
			   GRiNSns+' ' 'file':None,
			   GRiNSns+' ' 'font':None,
			   GRiNSns+' ' 'hicolor':None,
			   GRiNSns+' ' 'pointsize':None,
			   GRiNSns+' ' 'transparent':None,
			   GRiNSns+' ' 'type':None,
			   GRiNSns+' ' 'visible':None,
			   },
		'regPoint': {'bottom':None,
				       'customTest':None,
				       'left':None,
				       'regAlign':None,
				       'right':None,
				       'skip-content':'true',
				       'top':None,
				       },
		__layouts: {},
		__layout: {GRiNSns+' ' 'regions':None},
		'par': {'abstract':'',
			'author':'',
			'copyright':'',
			SMIL2+' '+'customTest':None,
			'endsync':None,
			'region':None,
			__layout:None,
			GRiNSns+' ' 'comment':None,
			},
##		'seq': {'abstract':'',
##			'author':'',
##			'copyright':'',
##			'customTest':None,
##			__layout:None,
##			GRiNSns+' ' 'comment':None,
##			},
		'switch': {__layout:None},
		'excl': {'abstract':'',
				   'author':'',
				   'copyright':'',
				   'customTest':None,
				   'endsync':None,
				   'region':None,
				   __layout:None,
				   GRiNSns+' ' 'comment':None,
				   },
		'priorityClass': {'higher':'pause',
					    'lower':'defer',
					    'pauseDisplay':None,
					    'peers':'stop',
					    },
		__choice: {GRiNSns+' ' 'abstract':'',
			   GRiNSns+' ' 'author':'',
			   GRiNSns+' ' 'choice-index':None,
			   GRiNSns+' ' 'comment':None,
			   GRiNSns+' ' 'copyright':'',
			   GRiNSns+' ' 'customTest':None,
			   __layout:None,
			   },
		'ref': {'abstract':'',
			'alt':None,
			'author':'',
			'clip-begin':None,
			'clip-end':None,
			SMIL2+' '+'clipBegin':None,
			SMIL2+' '+'clipEnd':None,
			'copyright':'',
			SMIL2+' '+'customTest':None,
			SMIL2+' '+'erase':None,
			'fill':None,
			'longdesc':None,
			SMIL2+' '+'mediaRepeat':None,
			'region':None,
			'src':None,
			SMIL2+' '+'tabindex':None,
			SMIL2+' '+'transIn':None,
			SMIL2+' '+'transOut':None,
			'type':None,
			# subregion positioning attributes
			SMIL2+' '+'bottom':None,
			SMIL2+' '+'left':None,
			SMIL2+' '+'right':None,
			SMIL2+' '+'top':None,
			SMIL2+' '+'fit':None,
			# registration point
			SMIL2+' '+'regPoint':None,
			SMIL2+' '+'regAlign':None,

			SMIL2+' '+'backgroundColor':None,
			__layout:None,
			GRiNSns+' ' 'bgcolor':None,
			GRiNSns+' ' 'comment':None,
			GRiNSns+' ' 'font':None,
			GRiNSns+' ' 'hicolor':None,
			GRiNSns+' ' 'pointsize':None,
			GRiNSns+' ' 'scale':None,
			GRiNSns+' ' 'captionchannel':None,
			GRiNSns+' ' 'project_audiotype':None,
			GRiNSns+' ' 'project_mobile':None,
			GRiNSns+' ' 'project_perfect':None,
			GRiNSns+' ' 'project_quality':None,
			GRiNSns+' ' 'project_targets':None,
			GRiNSns+' ' 'project_videotype':None,
			QTns+' ' 'immediate-instantiation':None,
			QTns+' ' 'bitrate':None,
			QTns+' ' 'system-mime-type-supported':None,
			QTns+' ' 'attach-timebase':None,
			QTns+' ' 'chapter':None,
			QTns+' ' 'composite-mode':None,
			},
		'brush': {'abstract':'',
				    'alt':None,
				    'author':'',
##				    'clip-begin':None,
##				    'clip-end':None,
##				    'clipBegin':None,
##				    'clipEnd':None,
				    'color':None,
				    'copyright':'',
				    'customTest':None,
				    'erase':None,
				    'fill':None,
				    'longdesc':None,
##				    'mediaRepeat':None,
				    'region':None,
				    'tabindex':None,
				    'transIn':None,
				    'transOut':None,
				    # subregion positioning attributes
				    'bottom':None,
				    'left':None,
				    'right':None,
				    'top':None,
				    'fit':None,
				    # registration point
				    'regPoint':None,
				    'regAlign':None,

				    'backgroundColor':None,
				    __layout:None,
				    GRiNSns+' ' 'bgcolor':None,
				    GRiNSns+' ' 'comment':None,
				    GRiNSns+' ' 'font':None,
				    GRiNSns+' ' 'hicolor':None,
				    QTns+' ' 'immediate-instantiation':None,
				    QTns+' ' 'bitrate':None,
				    QTns+' ' 'system-mime-type-supported':None,
				    QTns+' ' 'attach-timebase':None,
				    QTns+' ' 'chapter':None,
				    QTns+' ' 'composite-mode':None,
				    },
		'a': {SMIL2+' '+'accesskey':None,
		      SMIL2+' '+'actuate':None,
		      SMIL2+' '+'destinationLevel':None,
		      SMIL2+' '+'destinationPlaystate':None,
		      SMIL2+' '+'external':None,
		      'href':None,
		      'show':'replace',
		      SMIL2+' '+'sourceLevel':None,
		      SMIL2+' '+'sourcePlaystate':None,
		      SMIL2+' '+'tabindex':None,
		      SMIL2+' '+'target':None,
		      },
		'area': {SMIL2+' '+'accesskey':None,
				   SMIL2+' '+'actuate':None,
				   'alt':None,
				   'coords':None,
				   SMIL2+' '+'destinationLevel':None,
				   SMIL2+' '+'external':None,
				   SMIL2+' '+'fragment':None,
				   'href':None,
				   SMIL2+' '+'nohref':None,
				   SMIL2+' '+'shape':None,
				   'show':'replace',
				   'skip-content':'true',
				   SMIL2+' '+'sourceLevel':None,
				   SMIL2+' '+'sourcePlaystate':None,
				   SMIL2+' '+'tabindex':None,
				   SMIL2+' '+'target':None,
				   SMIL2+' '+'destinationPlaystate':None,
				   },
		'customAttributes': {},
		'customTest': {'defaultState':'false',
					 'override':'not-allowed',
					 'uid':None,
					 },
		'transition':{'type':None,
					'subtype':None,
					'dur':'1s',
					'startProgress':'0.0',
					'endProgress':'1.0',
					'direction':'forward',
					'fadeColor':None,
					'horzRepeat':'1',
					'vertRepeat':'1',
					'borderWidth':'0',
					'borderColor':None,
					'coordinated':'false',
					'clipBoundary':'children',
					},
		'transitionFilter': {'borderWidth':None,
					       'childrenClip':None,
					       'color':None,
					       'coordinated':None,
					       'customTest':None,
					       'horzRepeat':None,
					       'percentDone':None,
					       'skip-content':'true',
					       'subtype':None,
					       'type':None,
					       'vertRepeat':None,
					       },
		'prefetch': {'clip-begin':None,
				       'clip-end':None,
				       'src':None,
				       'mediaSize':None,
				       'mediaTime':None,
				       'bandwidth':None,
				       },
		}

	attributes['seq'] = attributes['body']
	attributes[__bag] = attributes[__choice]
	attributes['anchor'] = attributes['area']

	__media_object = ['audio', 'video', 'text', 'img', 'animation',
			  'textstream', 'ref', 'brush',
			  'prefetch',
			  __null, __cmif, __shell, __socket]

	__at = None
	for __el in __media_object:
		if attributes.has_key(__el):
			continue
		if __el[:len(GRiNSns)+1] == GRiNSns+' ':
			attributes[__el] = __at = {}
			for __key, __val in attributes['ref'].items():
				if ' ' in __key:
					__at[__key] = __val
					__at[GRiNSns+' '+string.split(__key,' ')[1]] = __val
				else:
					__at[GRiNSns+' '+__key] = __val
		else:
			attributes[__el] = attributes['ref']

	__animate_elements = ['animate', 'animateMotion',
			      'animateColor', 'set']
	__animate_attrs_core = {SMIL2+' '+'attributeName':'',
				SMIL2+' '+'attributeType':None,
##				SMIL2+' '+'autoReverse':'false',
				SMIL2+' '+'customTest':None,
				SMIL2+' '+'skip-content':None,
				SMIL2+' '+'targetElement': '',
				SMIL2+' '+'to':None,
				}
	__animate_attrs_extra = {SMIL2+' '+'accumulate':'none',
				 SMIL2+' '+'additive':'replace',
				 SMIL2+' '+'by':None,
				 SMIL2+' '+'calcMode':'linear',
				 SMIL2+' '+'from':None,
##				 SMIL2+' '+'keySplines':None,
##				 SMIL2+' '+'keyTimes':None,
				 SMIL2+' '+'values':None,
				 }
	attributes['animateMotion'] = __animate_attrs_core.copy()
	attributes['animateMotion'].update(__animate_attrs_extra)
	del attributes['animateMotion'][SMIL2+' '+'attributeName']
	del attributes['animateMotion'][SMIL2+' '+'attributeType']
	attributes['animateMotion'][SMIL2+' '+'calcMode'] = 'paced'
	attributes['animateMotion'][SMIL2+' '+'path'] = None
	attributes['animateMotion'][SMIL2+' '+'origin'] = None

	attributes['animate'] = __animate_attrs_core.copy()
	attributes['animate'].update(__animate_attrs_extra)

	attributes['animateColor'] = __animate_attrs_core.copy()
	attributes['animateColor'].update(__animate_attrs_extra)

	attributes['set'] = __animate_attrs_core.copy()

	del __animate_attrs_core, __animate_attrs_extra


	__schedule = ['par', 'seq', 'excl', __choice, __bag] + __media_object
	__container_content = __schedule + ['switch', 'a'] + __animate_elements
	__assoc_link = ['anchor', 'area'] + __animate_elements

	# Core, Test and I18n attribs are added to all elements in the language
	for __el in attributes.keys():
		if __el[:len(GRiNSns)+1] == GRiNSns+' ':
			for __key, __val in __Core.items() + __Test.items():
				if ' ' in __key:
					attributes[__el][__key] = __val
					attributes[__el][GRiNSns+' '+string.split(__key,' ')[1]] = __val
				else:
					attributes[__el][GRiNSns+' '+__key] = __val
##		elif __el[:len(SMIL2)+1] == SMIL2+' ':
##			for __key, __val in __Core.items() + __Test.items():
##				if ' ' in __key:
##					attributes[__el][__key] = __val
##				else:
##					attributes[__el][SMIL2+' '+__key] = __val
		else:
			attributes[__el].update(__Core)
			attributes[__el].update(__Test)
		attributes[__el].update(__I18n)

	# add basicTiming to certain elements
	for __el in ('animate', 'set',
		     'animateMotion', 'animateColor',
		     'area', 'anchor', 'transition',
		     'transitionFilter', 'prefetch'):
		attributes[__el].update(__basicTiming)

	# add Timing to certain other elements
	for __el in ('text', 'img', 'audio', 'animation', 'video', 'ref',
		     'textstream', 'brush', 'body', 'par', 'seq',
		     'excl', __choice):
		if __el[:len(GRiNSns)+1] == GRiNSns+' ':
			for __key, __val in __Timing.items():
				if ' ' in __key:
					attributes[__el][__key] = __val
					attributes[__el][GRiNSns+' '+string.split(__key,' ')[1]] = __val
				else:
					attributes[__el][GRiNSns+' '+__key] = __val
		else:
			attributes[__el].update(__Timing)

	# fix up SMIL 2.0 namespace
	for __el, __atd in attributes.items():
		if __el[:len(SMIL2)+1] == SMIL2+' ':
			# SMIL 2.0 element, all attribs must have NS prefix
			for __at, __vl in __atd.items():
				if ' ' not in __at:
					__atd[SMIL2+' '+__at] = __vl
					del __atd[__at]
		elif ' ' not in __el:
			# SMIL 1.0 element, make a SMIL 2.0 copy
			__atd = __atd.copy()
			attributes[SMIL2+' '+__el] = __atd
			for __at, __vl in __atd.items():
				if ' ' not in __at:
					__atd[SMIL2+' '+__at] = __vl
					del __atd[__at]
	del __el, __atd, __at, __vl, __key, __val

	# all entities with their allowed content
	# no allowed content is default, so we don't specify empty ones here
	entities = {
		'smil': ['head', 'body'],
		'head': ['layout', 'switch', 'meta', 'metadata',
			 'customAttributes', __layouts, 'transition'],
		'customAttributes': ['customTest'],
		'layout': ['region', 'root-layout', 'viewport', 'regPoint', 'switch'],
		'viewport': ['region', 'switch'],
		'region': ['region', 'switch'],
		__layouts: [__layout],
		'body': __container_content,
		'par': __container_content,
		'seq': __container_content,
		'excl': __container_content + ['priorityClass'],
		'priorityClass': __container_content + ['priorityClass'],
		__choice: __container_content,
		__bag: __container_content,
		'switch': ['layout', 'region', 'viewport'] + __container_content,
		'ref': __assoc_link,
		'audio': __assoc_link,
		'img': __assoc_link,
		'video': __assoc_link,
		'text': __assoc_link,
		'animation': __assoc_link,
		'textstream': __assoc_link,
		__null: __assoc_link,
		__cmif: __assoc_link,
		__shell: __assoc_link,
		__socket: __assoc_link,
		'a': __schedule + ['switch'],
		}

	# cleanup
	del __choice, __bag, __cmif, __shell, __socket, __null
	del __media_object, __schedule, __container_content,
	del __assoc_link
	del __layouts, __layout
	del __animate_elements
	del __I18n, __basicTiming, __Timing, __Core, __Test
