__version__ = "$Id$"

EVALcomment = ' Created with an evaluation copy of GRiNS '
SMIL_BASIC = 'text/smil-basic-layout'
SMILpubid = "-//W3C//DTD SMIL 1.0//EN"
SMILdtd = "http://www.w3.org/TR/REC-smil/SMIL10.dtd"
SMILBostonPubid = "-//W3C//DTD SMIL 2.0//EN"
SMILBostonDtd = "http://www.w3.org/TR/REC-smil/SMIL20.dtd"
GRiNSns = "http://www.oratrix.com/"
QTns = "http://www.apple.com/quicktime/resources/smilextensions"

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
		  'systemAudioDesc':None,
		  'systemBitrate':None,
		  'systemCaptions':None,
		  'systemComponent':None,
		  'systemCPU':None,
		  'systemLanguage':None,
		  'systemOperatingSystem':None,
		  'systemOverdubOrCaption':None,
		  'systemOverdubOrSubtitle':None,
		  'systemRequired':None,
		  'systemScreenDepth':None,
		  'systemScreenSize':None,}
	__basicTiming = {'begin':None,
			 'dur':None,
			 'end':None,}
	__Timing = {'fill':None,
		    'fillDefault':None,
		    'max':None,
		    'min':None,
		    'repeat':None,
		    'repeatCount':None,
		    'repeatDur':None,
		    'restart':None,
		    'restartDefault':None,
		    'syncBehavior':None,
		    'syncBehaviorDefault':None,
		    'syncMaster':None,
		    'syncTolerance':None,
		    'syncToleranceDefault':None,
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
			 'customTest':None,
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
				'backgroundColor':None,
				'customTest':None,
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
			   'backgroundColor':None,
			   'bottom':None,
			   'customTest':None,
			   'fit':'hidden',
			   'height':None,
			   'left':None,
			   'regAlign':None,
			   'regPoint':None,
			   'right':None,
			   'showBackground':None,
			   'skip-content':'true',
			   'soundLevel':None,
			   'top':None,
			   'width':None,
			   'z-index':'0',
			   'regionName': None,
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
			'customTest':None,
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
			'clipBegin':None,
			'clipEnd':None,
			'copyright':'',
			'customTest':None,
			'erase':None,
			'fill':None,
			'longdesc':None,
			'mediaRepeat':None,
			'region':None,
			'src':None,
			'tabindex':None,
			'transIn':None,
			'transOut':None,
			'type':None,
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
##			  'clip-begin':None,
##			  'clip-end':None,
##			  'clipBegin':None,
##			  'clipEnd':None,
			  'color':None,
			  'copyright':'',
			  'customTest':None,
			  'erase':None,
			  'fill':None,
			  'longdesc':None,
##			  'mediaRepeat':None,
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
		'a': {'accesskey':None,
		      'actuate':None,
		      'destinationLevel':None,
		      'destinationPlaystate':None,
		      'external':None,
		      'href':None,
		      'show':'replace',
		      'sourceLevel':None,
		      'sourcePlaystate':None,
		      'tabindex':None,
		      'target':None,
		      },
		'area': {'accesskey':None,
			 'actuate':None,
			 'alt':None,
			 'coords':None,
			 'destinationLevel':None,
			 'external':None,
			 'fragment':None,
			 'href':None,
			 'nohref':None,
			 'shape':None,
			 'show':'replace',
			 'skip-content':'true',
			 'sourceLevel':None,
			 'sourcePlaystate':None,
			 'tabindex':None,
			 'target':None,
			 'destinationPlaystate':None,
			 },
		'customAttributes': {},
		'customTest': {'defaultState':'false',
			       'override':'not-allowed',
			       'uid':None,
			       },
		'transition':{'type':None,
			      'subtype':None,
			      'startProgress':'0.0',
			      'endProgress':'1.0',
			      'direction':'forward',
			      'horzRepeat':'0',
			      'vertRepeat':'0',
			      'borderWidth':'0',
			      'color':'black',
			      'multiElement':'false',
			      'childrenClip':'false',
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
			  'textstream', 'ref', 'brush', 'prefetch',  __null, __cmif,
			  __shell, __socket]
	__at = None
	for __el in __media_object:
		if attributes.has_key(__el):
			continue
		if ' ' in __el:
			attributes[__el] = __at = {}
			for key, val in attributes['ref'].items():
				if ' ' in key:
					__at[key] = val
				else:
					__at[GRiNSns+' '+key] = val
		else:
			attributes[__el] = attributes['ref']
	del __el, __at

	__animate_elements = ['animate',  'animateMotion', 'animateColor', 'set',]
	__animate_attrs_core = {'attributeName':'',
				'attributeType':None,
				'autoReverse':'false',
				'customTest':None,
				'skip-content':None,
				'targetElement': '',
				'to':None,
				}
	__animate_attrs_extra = {'accumulate':'none',
				 'additive':'replace',
				 'by':None,
				 'calcMode':'linear',
				 'from':None,
				 'keySplines':None,
				 'keyTimes':None,
				 'values':None,
				 }
	attributes['animateMotion'] = __animate_attrs_core.copy()
	attributes['animateMotion'].update(__animate_attrs_extra)
	del attributes['animateMotion']['attributeName']
	del attributes['animateMotion']['attributeType']
	attributes['animateMotion']['calcMode'] = 'paced'
	attributes['animateMotion']['path'] = None
	attributes['animateMotion']['origin'] = None

	attributes['animate'] = __animate_attrs_core.copy()
	attributes['animate'].update(__animate_attrs_extra)

	attributes['animateColor'] = attributes['animate']
	attributes['animateColor'].update(__animate_attrs_extra)

	attributes['set'] = __animate_attrs_core.copy()

	del __animate_attrs_core, __animate_attrs_extra


	__schedule = ['par', 'seq', 'excl', __choice, __bag] + __media_object
	__container_content = __schedule + ['switch', 'a'] + __animate_elements
	__assoc_link = ['anchor', 'area'] + __animate_elements

	# Core and Test is added to all elements in the language
	for __el in attributes.keys():
		if ' ' in __el:
			for __key, __val in __Core.items():
				attributes[__el][GRiNSns+' '+__key] = __val
			for __key, __val in __Test.items():
				attributes[__el][GRiNSns+' '+__key] = __val
		else:
			attributes[__el].update(__Core)
			attributes[__el].update(__Test)
		attributes[__el].update(__I18n)

	for __el in ('animate','set','animateMotion','animateColor','area','anchor','transition','transitionFilter'):
		attributes[__el].update(__basicTiming)
	for __el in ('text','img','audio','animation','video','ref','textstream','brush','body','par','seq','excl',__choice):
		if ' ' in __el:
			for __key, __val in __Timing.items():
				attributes[__el][GRiNSns+' '+__key] = __val
		else:
			attributes[__el].update(__Timing)

	# all entities with their allowed content
	# no allowed content is default, so we don't specify empty ones here
	entities = {
		'smil': ['head', 'body'],
		'head': ['layout', 'switch', 'meta', 'metadata',
			 'customAttributes', __layouts, 'transition'],
		'customAttributes': ['customTest'],
		'layout': ['region', 'root-layout', 'viewport', 'regPoint','switch'],
		'viewport': ['region','switch'],
		'region': ['region','switch'],
		__layouts: [__layout],
		'body': __container_content,
		'par': __container_content,
		'seq': __container_content,
		'excl': __container_content + ['priorityClass'],
		'priorityClass': __container_content + ['priorityClass'],
		__choice: __container_content,
		__bag: __container_content,
		'switch': ['layout','region','viewport'] + __container_content,
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
	del __choice, __bag, __cmif, __shell, __socket
	del __media_object, __schedule, __container_content,
	del __assoc_link
	del __layouts, __layout
	del __animate_elements
