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

	# all allowed entities with all their attributes
	attributes = {
		'smil': {'id':None,
			QTns+' ' 'time-slider':None,
			QTns+' ' 'next':None,
			QTns+' ' 'autoplay':None,
			QTns+' ' 'chapter-mode':None,
			QTns+' ' 'immediate-instantiation':None,
			},
		'head': {'id':None},
		'body': {'abstract':'',
			 'author':'',
			 'begin':None,
			 'copyright':'',
			 'dur':None,
			 'end':None,
			 'fill':None,
			 'fillDefault':None,
			 'id':None,
			 'max':None,
			 'min':None,
			 'repeat':None,
			 'repeatCount':None,
			 'repeatDur':None,
			 'restart':None,
			 'system-bitrate':None,
			 'system-captions':None,
			 'system-language':None,
			 'system-overdub-or-caption':None,
			 'system-required':None,
			 'system-screen-depth':None,
			 'system-screen-size':None,
			 'systemAudioDesc':None,
			 'systemBitrate':None,
			 'systemCaptions':None,
			 'systemLanguage':None,
			 'systemOverdubOrCaption':None,
			 'systemOverdubOrSubtitle':None,
			 'systemRequired':None,
			 'systemScreenDepth':None,
			 'systemScreenSize':None,
			 'title':None,
			 'customTest':None,
			 __layout:None,
			 GRiNSns+' ' 'comment':None,
			 },
		'meta': {'content':None,
			 'id':None,
			 'name':None},
		'metadata': {'id':None,
			     },
		'layout': {'id':None,
			   'type':SMIL_BASIC},
		'root-layout': {'background-color':'transparent',
				'backgroundColor':None,
				'height':'0',
				'id':None,
				'overflow':'hidden',
				'skip-content':'true',
				'title':None,
				'width':'0'},
		'viewport': {'background-color':'transparent',
			     'backgroundColor':None,
			     'height':'0',
			     'id':None,
			     'skip-content':'true',
			     'title':None,
			     'width':'0',
			     'close':'never',
			     'open':'always',
			     },
		'region': {'background-color':'transparent',
			   'backgroundColor':None,
			   'showBackground':'always',
			   'bottom':None,
			   'fit':'hidden',
			   'height':None,
			   'id':None,
			   'left':None,
			   'skip-content':'true',
			   'right':None,
			   'title':None,
			   'top':None,
			   'width':None,
			   'z-index':'0',
			   'soundLevel':None,
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
		__layouts: {GRiNSns+' ' 'id':None},
		__layout: {GRiNSns+' ' 'id':None,
##			   GRiNSns+' ' 'title':None,
			   GRiNSns+' ' 'regions':None},
		'par': {'abstract':'',
			'author':'',
			'begin':None,
			'copyright':'',
			'dur':None,
			'end':None,
			'endsync':None,
			'fill':None,
			'fillDefault':None,
			'id':None,
			'max':None,
			'min':None,
			'region':None,
			'repeat':None,
			'repeatCount':None,
			'repeatDur':None,
			'restart':None,
			'system-bitrate':None,
			'system-captions':None,
			'system-language':None,
			'system-overdub-or-caption':None,
			'system-required':None,
			'system-screen-depth':None,
			'system-screen-size':None,
			'systemAudioDesc':None,
			'systemBitrate':None,
			'systemCaptions':None,
			'systemLanguage':None,
			'systemOverdubOrCaption':None,
			'systemOverdubOrSubtitle':None,
			'systemRequired':None,
			'systemScreenDepth':None,
			'systemScreenSize':None,
			'title':None,
			'customTest':None,
			__layout:None,
			GRiNSns+' ' 'comment':None,
			},
##		'seq': {'abstract':'',
##			'author':'',
##			'begin':None,
##			'copyright':'',
##			'dur':None,
##			'end':None,
##			'fill':None,
##			'fillDefault':None,
##			'id':None,
##			'max':None,
##			'min':None,
##			'repeat':None,
##			'repeatCount':None,
##			'repeatDur':None,
##			'restart':None,
##			'system-bitrate':None,
##			'system-captions':None,
##			'system-language':None,
##			'system-overdub-or-caption':None,
##			'system-required':None,
##			'system-screen-depth':None,
##			'system-screen-size':None,
##			'systemAudioDesc':None,
##			'systemBitrate':None,
##			'systemCaptions':None,
##			'systemLanguage':None,
##			'systemOverdubOrCaption':None,
##			'systemOverdubOrSubtitle':None,
##			'systemRequired':None,
##			'systemScreenDepth':None,
##			'systemScreenSize':None,
##			'title':None,
##			'customTest':None,
##			__layout:None,
##			GRiNSns+' ' 'comment':None,
##			},
		'switch': {'id':None,
			   'system-bitrate':None,
			   'system-captions':None,
			   'system-language':None,
			   'system-overdub-or-caption':None,
			   'system-required':None,
			   'system-screen-depth':None,
			   'system-screen-size':None,
			   'systemAudioDesc':None,
			   'systemBitrate':None,
			   'systemCaptions':None,
			   'systemLanguage':None,
			   'systemOverdubOrCaption':None,
			   'systemOverdubOrSubtitle':None,
			   'systemRequired':None,
			   'systemScreenDepth':None,
			   'systemScreenSize':None,
			   'customTest':None,
			   __layout:None},
		'excl': {'abstract':'',
			 'author':'',
			 'begin':None,
			 'copyright':'',
			 'dur':None,
			 'end':None,
			 'endsync':None,
			 'fill':None,
			 'fillDefault':None,
			 'id':None,
			 'max':None,
			 'min':None,
			 'region':None,
			 'repeat':None,
			 'repeatCount':None,
			 'repeatDur':None,
			 'restart':None,
			 'system-bitrate':None,
			 'system-captions':None,
			 'system-language':None,
			 'system-overdub-or-caption':None,
			 'system-required':None,
			 'system-screen-depth':None,
			 'system-screen-size':None,
			 'systemAudioDesc':None,
			 'systemBitrate':None,
			 'systemCaptions':None,
			 'systemLanguage':None,
			 'systemOverdubOrCaption':None,
			 'systemOverdubOrSubtitle':None,
			 'systemRequired':None,
			 'systemScreenDepth':None,
			 'systemScreenSize':None,
			 'title':None,
			 'customTest':None,
			 __layout:None,
			 GRiNSns+' ' 'comment':None,
			 },
		'priorityClass': {'abstract':'',
				  'author':'',
				  'copyright':'',
				  'higher':'pause',
				  'id':None,
				  'lower':'defer',
				  'pauseDisplay':None,
				  'peers':'stop',
				  'title':None,
				  },
		__choice: {GRiNSns+' ' 'abstract':'',
			   GRiNSns+' ' 'author':'',
			   GRiNSns+' ' 'choice-index':None,
			   GRiNSns+' ' 'copyright':'',
			   GRiNSns+' ' 'id':None,
			   GRiNSns+' ' 'restart':None,
			   GRiNSns+' ' 'system-bitrate':None,
			   GRiNSns+' ' 'system-captions':None,
			   GRiNSns+' ' 'system-language':None,
			   GRiNSns+' ' 'system-overdub-or-caption':None,
			   GRiNSns+' ' 'system-required':None,
			   GRiNSns+' ' 'system-screen-depth':None,
			   GRiNSns+' ' 'system-screen-size':None,
			   GRiNSns+' ' 'systemAudioDesc':None,
			   GRiNSns+' ' 'systemBitrate':None,
			   GRiNSns+' ' 'systemCaptions':None,
			   GRiNSns+' ' 'systemLanguage':None,
			   GRiNSns+' ' 'systemOverdubOrCaption':None,
			   GRiNSns+' ' 'systemOverdubOrSubtitle':None,
			   GRiNSns+' ' 'systemRequired':None,
			   GRiNSns+' ' 'systemScreenDepth':None,
			   GRiNSns+' ' 'systemScreenSize':None,
			   GRiNSns+' ' 'title':None,
			   GRiNSns+' ' 'customTest':None,
			   __layout:None,
			   GRiNSns+' ' 'comment':None,
			   },
		'ref': {'abstract':'',
			'alt':None,
			'author':'',
			'begin':None,
			'clip-begin':None,
			'clip-end':None,
			'copyright':'',
			'dur':None,
			'end':None,
			'fill':None,
			'fillDefault':None,
			'id':None,
			'longdesc':None,
			'max':None,
			'min':None,
			'region':None,
			'repeat':None,
			'repeatCount':None,
			'repeatDur':None,
			'restart':None,
			'src':None,
			'system-bitrate':None,
			'system-captions':None,
			'system-language':None,
			'system-overdub-or-caption':None,
			'system-required':None,
			'system-screen-depth':None,
			'system-screen-size':None,
			'systemAudioDesc':None,
			'systemBitrate':None,
			'systemCaptions':None,
			'systemLanguage':None,
			'systemOverdubOrCaption':None,
			'systemOverdubOrSubtitle':None,
			'systemRequired':None,
			'systemScreenDepth':None,
			'systemScreenSize':None,
			'title':None,
			'transIn':None,
			'transOut':None,
			'type':None,
			'customTest':None,
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
			  'begin':None,
			  'color':None,
			  'copyright':'',
			  'dur':None,
			  'end':None,
			  'fill':None,
			  'fillDefault':None,
			  'id':None,
			  'longdesc':None,
			  'max':None,
			  'min':None,
			  'region':None,
			  'repeat':None,
			  'repeatCount':None,
			  'repeatDur':None,
			  'restart':None,
			  'system-bitrate':None,
			  'system-captions':None,
			  'system-language':None,
			  'system-overdub-or-caption':None,
			  'system-required':None,
			  'system-screen-depth':None,
			  'system-screen-size':None,
			  'systemAudioDesc':None,
			  'systemBitrate':None,
			  'systemCaptions':None,
			  'systemLanguage':None,
			  'systemOverdubOrCaption':None,
			  'systemOverdubOrSubtitle':None,
			  'systemRequired':None,
			  'systemScreenDepth':None,
			  'systemScreenSize':None,
			  'title':None,
			  'customTest':None,
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
		'a': {'href':None,
		      'id':None,
		      'sourcePlaystate':None,
		      'destinationPlaystate':'play',
		      'show':'replace',
		      'title':None},
		'anchor': {'begin':None,
			   'coords':None,
			   'shape':None,
			   'end':None,
			   'href':None,
			   'id':None,
			   'sourcePlaystate':None,
		           'destinationPlaystate':'play',
			   'show':'replace',
			   'skip-content':'true',
			   'title':None,
			   'fragment':None},
		'area': {'begin':None,
			 'coords':None,
			 'shape':None,
			 'end':None,
			 'href':None,
			 'id':None,
			 'sourcePlaystate':None,
		         'destinationPlaystate':'play',
			 'show':'replace',
			 'skip-content':'true',
			 'title':None,
			 'fragment':None,
			 },
		'customAttributes': {'id':None,
				     'title':None,
				     },
		'customTest': {'defaultState':'false',
			       'id':None,
			       'override':'not-allowed',
			       'title':None,
			       'uid':None,
			       },
		'transition':{'id':None,
				'type':None,
				'subtype':None,
				'dur':'1s',
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
		'prefetch': {'id':None,
			'begin':None,
			'clip-begin':None,
			'clip-end':None,
			'dur':None,
			'end':None,
			'src':None,
			'mediaSize':None,
			'mediaTime':None,
			'bandwidth':None,
			},

		}
	attributes['seq'] = attributes['body']
	attributes[__bag] = attributes[__choice]

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
	__animate_attrs = {'accelerate':'0',
			   'accumulate':'none',
			   'additive':'replace',
			   'attributeName':'',
			   'attributeType':None,
			   'autoReverse':'false',
			   'begin':None,
			   'by':None,
			   'calcMode':'linear',
			   'decelerate':'0',
			   'dur':None,
			   'end':None,
			   'fill':None,
			   'fillDefault':None,
			   'from':None,
			   'id':None,
			   'keySplines':None,
			   'keyTimes':None,
			   'max':None,
			   'min':None,
			   'origin':None,
			   'path':None,
			   'repeatCount':None,
			   'repeatDur':None,
			   'restart':None,
			   'speed':'1',
			   'targetElement': '',
			   'to':None,
			   'values':None,
			   }
	attributes['animateMotion'] = __animate_attrs.copy()
	del attributes['animateMotion']['attributeName']
	del attributes['animateMotion']['attributeType']
	attributes['animateMotion']['calcMode'] = 'paced'

	del __animate_attrs['path'], __animate_attrs['origin']
	attributes['animate'] = __animate_attrs.copy()
	attributes['animateColor'] = attributes['animate']

	del __animate_attrs['calcMode'], __animate_attrs['values'],
	del __animate_attrs['keyTimes'], __animate_attrs['keySplines']
	del __animate_attrs['from'], __animate_attrs['by'],
	del __animate_attrs['additive'], __animate_attrs['accumulate'],
	attributes['set'] = __animate_attrs.copy()
	del __animate_attrs


	__schedule = ['par', 'seq', 'excl', __choice, __bag] + __media_object
	__container_content = __schedule + ['switch', 'a'] + __animate_elements
	__assoc_link = ['anchor', 'area'] + __animate_elements

	# all entities with their allowed content
	# no allowed content is default, so we don't specify empty ones here
	entities = {
		'smil': ['head', 'body'],
		'head': ['layout', 'switch', 'meta', 'metadata',
			 'customAttributes', __layouts, 'transition'],
		'customAttributes': ['customTest'],
		'layout': ['region', 'root-layout', 'viewport', 'regPoint'],
		'viewport': ['region'],
		'region': ['region'],
		__layouts: [__layout],
		'body': __container_content,
		'par': __container_content,
		'seq': __container_content,
		'excl': __container_content + ['priorityClass'],
		'priorityClass': __container_content + ['priorityClass'],
		__choice: __container_content,
		__bag: __container_content,
		'switch': ['layout'] + __container_content,
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
