__version__ = "$Id$"

EVALcomment = ' Created with an evaluation copy of GRiNS '
SMIL_BASIC = 'text/smil-basic-layout'
SMILpubid = '-//W3C//DTD SMIL 1.0//EN'
SMILdtd = 'http://www.w3.org/TR/REC-smil/SMIL10.dtd'
SMIL1 = 'http://www.w3.org/TR/REC-smil'
SMILBostonPubid = '-//W3C//DTD SMIL 2.0//EN'
SMILBostonDtd = 'http://www.w3.org/2001/SMIL20/SMIL20.dtd'
SMILBostonDtd = 'http://www.w3.org/2001/SMIL20/PR/SMIL20.dtd' # XXX to be removed
SMIL2 = 'http://www.w3.org/2001/SMIL20/'
SMIL2 = 'http://www.w3.org/2001/SMIL20/PR/' # XXX to be removed
# namespaces recognized by GRiNS
# the first one is the required default namespace, but SMIL1
# doesn't generate a warning
SMIL2ns = [
##	   'http://www.w3.org/2001/SMIL20/Language', # XXX to be uncommented
##	   'http://www.w3.org/2001/SMIL20/', # XXX to be uncommented
	   'http://www.w3.org/2001/SMIL20/PR/Language',
	   'http://www.w3.org/2001/SMIL20/PR/',
	   'http://www.w3.org/2001/SMIL20/Language', # XXX to be removed
	   'http://www.w3.org/2001/SMIL20/', # XXX to be removed
	   'http://www.w3.org/2001/SMIL20/WD/Language',
	   'http://www.w3.org/2001/SMIL20/WD/',
	   'http://www.w3.org/2000/SMIL20/CR/Language',
	   'http://www.w3.org/2000/SMIL20/CR/',
##	   'http://www.w3.org/TR/REC-smil/2000/SMIL20/LC/Language',
##	   'http://www.w3.org/TR/REC-smil/2000/SMIL20/LC/',
##	   'http://www.w3.org/TR/REC-smil/2000/SMIL20/Language',
##	   'http://www.w3.org/TR/REC-smil/2000/SMIL20',
	   SMIL1]
SMIL2DTDs = [SMILBostonDtd,
##	     'http://www.w3.org/2001/SMIL20/PR/SMIL20.dtd', # XXX to be uncommented
	     'http://www.w3.org/2001/SMIL20/SMIL20.dtd', # XXX to be removed
	     'http://www.w3.org/2001/SMIL20/WD/SMIL20.dtd',
	     'http://www.w3.org/2000/SMIL20/CR/SMIL20.dtd',
##	     'http://www.w3.org/TR/REC-smil/2000/SMIL20/SMIL20.dtd',
	     ]
GRiNSns = 'http://www.oratrix.com/'
QTns = 'http://www.apple.com/quicktime/resources/smilextensions'

# list elements here that are not valid in all namespaces with the
# namespaces they are valid in
limited = {
	# viewport was changed to topLayout after CR
	'viewport': SMIL2ns[6:],
	'topLayout': SMIL2ns[:8],
	}

ATTRIBUTES = {
	'abstract': ['MediaDescription'],
	'accelerate': ['TimeManipulations'],
	'accesskey': ['LinkingAttributes'],
	'actuate': ['LinkingAttributes'],
	'alt': ['MediaAccessibility', 'LinkingAttributes'],
	'author': ['MediaDescription'],
	'autoReverse': ['TimeManipulations'],
	'backgroundColor': ['HierarchicalLayout'],
	'begin': ['AccessKeyTiming', 'EventTiming', 'MediaMarkerTiming', 'MultiArcTiming', 'RepeatValueTiming', 'BasicInlineTiming', 'SyncbaseTiming', 'WallclockTiming'],
	'borderColor': ['TransitionModifiers'],
	'borderWidth': ['TransitionModifiers'],
	'bottom': ['HierarchicalLayout'],
	'clip-begin': ['MediaClipping', 'MediaClipMarkers'],
	'clip-end': ['MediaClipping', 'MediaClipMarkers'],
	'clipBegin': ['MediaClipping', 'MediaClipMarkers'],
	'clipEnd': ['MediaClipping', 'MediaClipMarkers'],
	'copyright': ['MediaDescription'],
	'customTest': ['CustomTestAttributes'],
	'decelerate': ['TimeManipulations'],
	'destinationLevel': ['LinkingAttributes'],
	'destinationPlaystate': ['LinkingAttributes'],
	'dur': ['BasicInlineTiming'],
	'end': ['AccessKeyTiming', 'EventTiming', 'MediaMarkerTiming', 'MultiArcTiming', 'RepeatValueTiming', 'BasicInlineTiming', 'SyncbaseTiming', 'WallclockTiming'],
	'endsync': ['TimeContainerAttributes', 'BasicTimeContainers'],
	'erase': ['MediaParam'],
	'external': ['LinkingAttributes'],
	'fill': ['TimeContainerAttributes', 'BasicTimeContainers'],
	'fillDefault': ['FillDefault'],
	'fit': ['HierarchicalLayout'],
	'fragment': ['ObjectLinking'],
	'height': ['HierarchicalLayout'],
	'horzRepeat': ['TransitionModifiers'],
	'left': ['HierarchicalLayout'],
	'longdesc': ['MediaAccessibility'],
	'max': ['MinMaxTiming'],
	'mediaRepeat': ['MediaParam'],
	'min': ['MinMaxTiming'],
	'readIndex': ['MediaAccessibility'],
	'regAlign': ['HierarchicalLayout'],
	'regPoint': ['HierarchicalLayout'],
	'region': ['BasicLayout'],
	'repeat': ['RepeatTiming'],
	'repeatCount': ['RepeatTiming'],
	'repeatDur': ['RepeatTiming'],
	'restart': ['RestartTiming'],
	'restartDefault': ['RestartDefault'],
	'right': ['HierarchicalLayout'],
	'sensitivity': ['MediaParam'],
	'show': ['LinkingAttributes'],
	'skip-content': ['SkipContentControl'],
	'soundLevel': ['AudioLayout'],
	'sourceLevel': ['LinkingAttributes'],
	'sourcePlaystate': ['LinkingAttributes'],
	'speed': ['TimeManipulations'],
	'syncBehavior': ['SyncBehavior'],
	'syncBehaviorDefault': ['SyncBehaviorDefault'],
	'syncMaster': ['SyncMaster'],
	'syncTolerance': ['SyncBehavior'],
	'syncToleranceDefault': ['SyncBehaviorDefault'],
	'system-bitrate': ['BasicContentControl'],
	'system-captions': ['BasicContentControl'],
	'system-language': ['BasicContentControl'],
	'system-overdub-or-caption': ['BasicContentControl'],
	'system-required': ['BasicContentControl'],
	'system-screen-depth': ['BasicContentControl'],
	'system-screen-size': ['BasicContentControl'],
	'systemAudioDesc': ['BasicContentControl'],
	'systemBitrate': ['BasicContentControl'],
	'systemCPU': ['BasicContentControl'],
	'systemCaptions': ['BasicContentControl'],
	'systemComponent': ['BasicContentControl'],
	'systemLanguage': ['BasicContentControl'],
	'systemOperatingSystem': ['BasicContentControl'],
	'systemOverdubOrSubtitle': ['BasicContentControl'],
	'systemRequired': ['BasicContentControl'],
	'systemScreenDepth': ['BasicContentControl'],
	'systemScreenSize': ['BasicContentControl'],
	'tabindex': ['LinkingAttributes'],
	'target': ['LinkingAttributes'],
	'timeAction': ['TimeContainerAttributes'],
	'timeContainer': ['TimeContainerAttributes'],
	'title': ['MediaDescription'],
	'top': ['HierarchicalLayout'],
	'transIn': ['BasicTransitions'],
	'transOut': ['BasicTransitions'],
	'vertRepeat': ['TransitionModifiers'],
	'width': ['HierarchicalLayout'],
	'xml:lang': ['MediaDescription'],
	'z-index': ['HierarchicalLayout'],
	}
ELEMENTS = {
	'BasicAnimation': {
		'animate': [
			'attributeName',
			'attributeType',
			'targetElement',
			'values',
			'calcMode',
			'accumulate',
			'additive',
			'from',
			'to',
			'by',
			'origin',
		],
		'set': [
			'attributeName',
			'attributeType',
			'targetElement',
			'values',
			'calcMode',
			'accumulate',
			'additive',
			'from',
			'to',
			'by',
			'origin',
		],
		'animateMotion': [
			'attributeName',
			'attributeType',
			'targetElement',
			'values',
			'calcMode',
			'accumulate',
			'additive',
			'from',
			'to',
			'by',
			'origin',
		],
		'animateColor': [
			'attributeName',
			'attributeType',
			'targetElement',
			'values',
			'calcMode',
			'accumulate',
			'additive',
			'from',
			'to',
			'by',
			'origin',
		],
	},
	'SplineAnimation': {
		'animate': [
			'calcMode',
			'keyTimes',
			'keySplines',
			'path',
		],
		'animateMotion': [
			'calcMode',
			'keyTimes',
			'keySplines',
			'path',
		],
		'animateColor': [
			'calcMode',
			'keyTimes',
			'keySplines',
			'path',
		],
	},
	'BasicContentControl': {
		'switch': [
		],
	},
	'CustomTestAttributes': {
		'customAttributes': [
		],
		'customTest': [
			'defaultState',
			'override',
			'uid',
		],
	},
	'PrefetchControl': {
		'prefetch': [
			'mediaSize',
			'mediaTime',
			'bandwidth',
		],
	},
	'BasicLayout': {
		'layout': [
			'type',
		],
		'region': [
			'backgroundColor',
			'background-color',
			'bottom',
			'fit',
			'height',
			'left',
			'regionName',
			'right',
			'showBackground',
			'top',
			'width',
			'z-index',
		],
		'root-layout': [
			'backgroundColor',
			'background-color',
			'height',
			'width',
		],
	},
	'MultiWindowLayout': {
		'topLayout': [
			'backgroundColor',
			'close',
			'height',
			'open',
			'width',
		],
		'layout': [
		],
	},
	'HierarchicalLayout': {
		'layout': [
		],
		'region': [
		],
		'regPoint': [
			'top',
			'bottom',
			'left',
			'right',
			'regAlign',
		],
	},
	'BasicLinking': {
		'a': [
			'href',
		],
		'area': [
			'href',
			'nohref',
			'shape',
			'coords',
		],
		'anchor': [
			'href',
			'nohref',
			'shape',
			'coords',
		],
	},
	'BasicMedia': {
		'ref': [
			'src',
			'type',
		],
		'audio': [
			'src',
			'type',
		],
		'video': [
			'src',
			'type',
		],
		'img': [
			'src',
			'type',
		],
		'text': [
			'src',
			'type',
		],
		'animation': [
			'src',
			'type',
		],
		'textstream': [
			'src',
			'type',
		],
	},
	'MediaParam': {
		'param': [
			'name',
			'value',
			'valuetype',
			'type',
		],
	},
	'BrushMedia': {
		'brush': [
			'color',
		],
	},
	'Metainformation': {
		'meta': [
			'content',
			'name',
		],
		'metadata': [
		],
	},
	'Structure': {
		'smil': [
			'id',
			'class',
##			'xml:lang',
			'title',
			'xmlns',
		],
		'head': [
			'id',
			'class',
##			'xml:lang',
			'title',
		],
		'body': [
			'id',
			'class',
##			'xml:lang',
			'title',
		],
	},
	'BasicTimeContainers': {
		'par': [
		],
		'seq': [
		],
	},
	'ExclTimeContainers': {
		'excl': [
			'fill',
			'endsync',
		],
		'priorityClass': [
		],
	},
	'BasicTransitions': {
		'transition': [
			'type',
			'subtype',
			'dur',
			'startProgress',
			'endProgress',
			'direction',
			'fadeColor',
		],
	},
	'InlineTransitions': {
		'transitionFilter': [
			'type',
			'subtype',
			'mode',
			'fadeColor',
			'begin',
			'dur',
			'end',
			'repeatCount',
			'repeatDur',
			'from',
			'to',
			'by',
			'values',
			'calcMode',
			'targetElement',
			'href',
		],
	},
}

class SMIL:
	# some abbreviations
	__layouts = GRiNSns + ' ' + 'layouts'
	__layout = GRiNSns + ' ' + 'layout'
	__null = GRiNSns + ' ' 'null'
	__assets = GRiNSns + ' ' 'assets'
	__viewinfo = GRiNSns + ' ' 'viewinfo'

	# abbreviations for collections of attributes
	__Core = {'alt':None,
		  'class':None,
		  'id':None,
		  'longdesc':None,
		  'title':None,
		  'xml:base':None,}
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
		  'systemOverdubOrSubtitle':None,
		  'systemRequired':None,
		  'systemScreenDepth':None,
		  'systemScreenSize':None,}
	__basicTiming = {'begin':None,
			 'dur':None,
			 'end':None,
			 'max':None,
			 'min':None,
			 'repeat':None,
			 'repeatCount':None,
			 'repeatDur':None,
			 }
	__Timing = {'fillDefault':None,
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
		'body': {'abstract':None,
			 'author':None,
			 'copyright':None,
			 'fill':None,
			 __layout:None,
			 GRiNSns+' ' 'hidden':None,
			 GRiNSns+' ' 'collapsed':None,
			 GRiNSns+' ' 'showtime':None,
			 GRiNSns+' ' 'comment':None,
			 GRiNSns+' ' 'thumbnail-scale':None,
			 GRiNSns+' ' 'thumbnail-icon':None,
			 GRiNSns+' ' 'project_default_region_image':None,
			 GRiNSns+' ' 'project_default_region_video':None,
			 GRiNSns+' ' 'project_default_region_sound':None,
			 GRiNSns+' ' 'project_default_region_text':None,
			 },
		'meta': {'content':None,
			 'name':None,
			 'skip-content':None,
			 },
		'metadata': {'skip-content':None,
			     },
		__assets: {'skip-content':None,
			     },
		'layout': {'customTest':None,
			   'type':None,
			   },
		'root-layout': {'background-color':None,
				'backgroundColor':None,
				'customTest':None,
				'height':None,
				'skip-content':None,
				'width':None,
				GRiNSns+' ' 'collapsed':None,
				},
		'topLayout': {'backgroundColor':None,
			      'customTest':None,
			      'height':None,
			      'skip-content':None,
			      'width':None,
			      'close':None,
			      'open':None,
			      # edit preferences of new layout view
			      GRiNSns+' ' 'showEditBackground':None,
			      GRiNSns+' ' 'editBackground':None,					 
			      GRiNSns+' ' 'traceImage':None,					 
			      GRiNSns+' ' 'collapsed':None,
			      },
		'region': {'background-color':None,
			   'backgroundColor':None,
			   'bottom':None,
			   'customTest':None,
			   'fit':None,
			   'height':None,
			   'left':None,
##			   'regAlign':None,
##			   'regPoint':None,
			   'regionName': None,
			   'right':None,
			   'showBackground':None,
			   'skip-content':None,
			   'soundLevel':None,
			   'top':None,
			   'width':None,
			   'z-index':None,
			   GRiNSns+' ' 'comment':None,
			   GRiNSns+' ' 'duration':None,
			   GRiNSns+' ' 'fgcolor':None,
			   GRiNSns+' ' 'file':None,
			   GRiNSns+' ' 'transparent':None,
			   GRiNSns+' ' 'type':None,
			   GRiNSns+' ' 'visible':None,
			   GRiNSns+' ' 'collapsed':None,

				# edit preferences of new layout view
				GRiNSns+' ' 'showEditBackground':None,
				GRiNSns+' ' 'editBackground':None,
			},
		'regPoint': {'bottom':None,
			     'customTest':None,
			     'left':None,
			     'regAlign':None,
			     'right':None,
			     'skip-content':None,
			     'top':None,
			     },
		__layouts: {},
		__layout: {GRiNSns+' ' 'regions':None},
		__viewinfo: {
				'view':None,
				'top': None,
				'left': None,
				'width': None,
				'height': None,
				},
		'par': {'abstract':None,
			'author':None,
			'copyright':None,
			'customTest':None,
			'endsync':None,
			'fill':None,
			'region':None,
			__layout:None,
			GRiNSns+' ' 'collapsed':None,
			GRiNSns+' ' 'showtime':None,
			GRiNSns+' ' 'comment':None,
			GRiNSns+' ' 'thumbnail-scale':None,
			GRiNSns+' ' 'thumbnail-icon':None,
			GRiNSns+' ' 'project_default_region_image':None,
			GRiNSns+' ' 'project_default_region_video':None,
			GRiNSns+' ' 'project_default_region_sound':None,
			GRiNSns+' ' 'project_default_region_text':None,
			},
		'seq': {'abstract':None,
			'author':None,
			'copyright':None,
			'customTest':None,
			'fill':None,
			'region':None,
			__layout:None,
			GRiNSns+' ' 'collapsed':None,
			GRiNSns+' ' 'showtime':None,
			GRiNSns+' ' 'comment':None,
			GRiNSns+' ' 'thumbnail-scale':None,
			GRiNSns+' ' 'thumbnail-icon':None,
			GRiNSns+' ' 'project_default_region':None,
			GRiNSns+' ' 'project_default_type':None,
			GRiNSns+' ' 'project_bandwidth_fraction':None,
			GRiNSns+' ' 'project_readonly':None,
			GRiNSns+' ' 'project_default_region_image':None,
			GRiNSns+' ' 'project_default_region_video':None,
			GRiNSns+' ' 'project_default_region_sound':None,
			GRiNSns+' ' 'project_default_region_text':None,
			},
		'switch': {'customTest':None,
			   __layout:None,
			   GRiNSns+' ' 'thumbnail-scale':None,
			   GRiNSns+' ' 'thumbnail-icon':None,
			   GRiNSns+' ' 'collapsed':None,
			   GRiNSns+' ' 'showtime':None,
			   },
		'excl': {'abstract':None,
			 'author':None,
			 'copyright':None,
			 'customTest':None,
			 'endsync':None,
			 'fill':None,
			 'region':None,
			 'skip-content':None,
			 __layout:None,
			 GRiNSns+' ' 'collapsed':None,
			 GRiNSns+' ' 'showtime':None,
			 GRiNSns+' ' 'comment':None,
			 GRiNSns+' ' 'thumbnail-scale':None,
			 GRiNSns+' ' 'thumbnail-icon':None,
			 GRiNSns+' ' 'project_default_region_image':None,
			 GRiNSns+' ' 'project_default_region_video':None,
			 GRiNSns+' ' 'project_default_region_sound':None,
			 GRiNSns+' ' 'project_default_region_text':None,
			 },
		'priorityClass': {'abstract':None,
				  'author':None,
				  'copyright':None,
				  'customTest':None,
				  'higher':'pause',
				  'lower':'defer',
				  'pauseDisplay':None,
				  'peers':'stop',
				  'skip-content':None,
				  GRiNSns+' ' 'thumbnail-scale':None,
				  GRiNSns+' ' 'thumbnail-icon':None,
				  GRiNSns+' ' 'collapsed':None,
				  GRiNSns+' ' 'showtime':None,
				  },
		'ref': {'abstract':None,
			'author':None,
			'clip-begin':None,
			'clip-end':None,
			'clipBegin':None,
			'clipEnd':None,
			'copyright':None,
			'customTest':None,
			'endsync':None,
			'erase':None,
			'fill':None,
			'mediaRepeat':None,
			'readIndex':None,
			'region':None,
			'sensitivity':None,
			'src':None,
			'tabindex':None,
			'transIn':None,
			'transOut':None,
			'type':None,
			# subregion positioning attributes
			'bottom':None,
			'height':None,
			'left':None,
			'right':None,
			'top':None,
			'width':None,
			'z-index':None,
			'fit':None,
			# registration point
			'regPoint':None,
			'regAlign':None,

			'backgroundColor':None,
			__layout:None,
			GRiNSns+' ' 'bgcolor':None,
			GRiNSns+' ' 'comment':None,
			GRiNSns+' ' 'scale':None,
			GRiNSns+' ' 'captionchannel':None,
			GRiNSns+' ' 'thumbnail-scale':None,
			GRiNSns+' ' 'thumbnail-icon':None,
			GRiNSns+' ' 'project_audiotype':None,
			GRiNSns+' ' 'project_convert':None,
			GRiNSns+' ' 'project_mobile':None,
			GRiNSns+' ' 'project_perfect':None,
			GRiNSns+' ' 'project_quality':None,
			GRiNSns+' ' 'project_targets':None,
			GRiNSns+' ' 'project_videotype':None,
			GRiNSns+' ' 'showtime':None,
			GRiNSns+' ' 'allowedmimetypes':None,
			QTns+' ' 'immediate-instantiation':None,
			QTns+' ' 'bitrate':None,
			QTns+' ' 'system-mime-type-supported':None,
			QTns+' ' 'attach-timebase':None,
			QTns+' ' 'chapter':None,
			QTns+' ' 'composite-mode':None,
			},
		'brush': {'abstract':None,
			  'author':None,
			  'color':None,
			  'copyright':None,
			  'customTest':None,
			  'endsync':None,
			  'erase':None,
			  'fill':None,
			  'readIndex':None,
			  'region':None,
			  'sensitivity':None,
			  'skip-content':None,
			  'tabindex':None,
			  'transIn':None,
			  'transOut':None,
			  # subregion positioning attributes
			  'bottom':None,
			  'height':None,
			  'left':None,
			  'right':None,
			  'top':None,
			  'width':None,
			  'z-index':None,
			  'fit':None,
			  # registration point
			  'regPoint':None,
			  'regAlign':None,

			  'backgroundColor':None,
			  __layout:None,
			  GRiNSns+' ' 'thumbnail-scale':None,
			  GRiNSns+' ' 'thumbnail-icon':None,
			  GRiNSns+' ' 'bgcolor':None,
			  GRiNSns+' ' 'comment':None,
			  GRiNSns+' ' 'showtime':None,
			  QTns+' ' 'immediate-instantiation':None,
			  QTns+' ' 'bitrate':None,
			  QTns+' ' 'system-mime-type-supported':None,
			  QTns+' ' 'attach-timebase':None,
			  QTns+' ' 'chapter':None,
			  QTns+' ' 'composite-mode':None,
			  },
		'param': {'customTest':None,
			  'name':None,
			  'skip-content':None,
			  'type':None,
			  'value':None,
			  'valuetype':None,
			  },
		'a': {'accesskey':None,
		      'actuate':None,
		      'customTest':None,
		      'destinationLevel':None,
		      'destinationPlaystate':None,
		      'external':None,
		      'href':None,
		      'show':None,
		      'sourceLevel':None,
		      'sourcePlaystate':None,
		      'tabindex':None,
		      'target':None,
		      },
		'area': {'accesskey':None,
			 'actuate':None,
			 'coords':None,
			 'customTest':None,
			 'destinationLevel':None,
			 'destinationPlaystate':None,
			 'external':None,
			 'fragment':None,
			 'href':None,
			 'nohref':None,
			 'shape':None,
			 'show':None,
			 'skip-content':None,
			 'sourceLevel':None,
			 'sourcePlaystate':None,
			 'tabindex':None,
			 'target':None,
			 },
		'customAttributes': {'skip-content':None,
				     },
		'customTest': {'defaultState':None,
			       'override':None,
			       'skip-content':None,
			       'uid':None,
			       },
		'transition':{'type':None,
			      'subtype':None,
			      'dur':None,
			      'startProgress':None,
			      'endProgress':None,
			      'direction':None,
			      'fadeColor':None,
			      'horzRepeat':None,
			      'vertRepeat':None,
			      'borderWidth':None,
			      'borderColor':None,
##			      'coordinated':None,
##			      'clipBoundary':None,
			      'skip-content':None,
			      'customTest':None,
			      },
		'prefetch': {'bandwidth':None,
			     'clip-begin':None,
			     'clip-end':None,
			     'clipBegin':None,
			     'clipEnd':None,
			     'customTest':None,
			     'mediaSize':None,
			     'mediaTime':None,
			     'skip-content':None,
			     'src':None,
			     GRiNSns+' ' 'showtime':None,
			     },
		}

	attributes['viewport'] = attributes['topLayout'].copy()
	attributes['anchor'] = attributes['area'].copy()

	__media_object = ['audio', 'video', 'text', 'img', 'animation',
			  'textstream', 'ref', 'brush',
			  'prefetch',
			  __null]

	__at = None
	for __el in __media_object:
		if attributes.has_key(__el):
			continue
		if __el[:len(GRiNSns)+1] == GRiNSns+' ':
			attributes[__el] = __at = {}
			for __key, __val in attributes['ref'].items():
				if ' ' in __key:
					__at[__key] = __val
					__at[GRiNSns+' '+__key.split(' ')[1]] = __val
				else:
					__at[GRiNSns+' '+__key] = __val
		else:
			attributes[__el] = attributes['ref']

	__animate_elements = ['animate', 'animateMotion',
			      'animateColor', 'set']
	__animate_attrs_core = {'attributeName':None,
				'attributeType':None,
				'customTest':None,
				'fill':None,
				'fillDefault':None,
				'skip-content':None,
				'targetElement': None,
				'to':None,
				}
	__animate_attrs_extra = {'accumulate':None,
				 'additive':None,
				 'by':None,
				 'calcMode':None,
				 'from':None,
				 'values':None,
				 }
	__timeManipulations = {'speed':None,
		    'accelerate':None,
		    'decelerate':None,
		    'autoReverse':None,
		    }

	__transitionFilter_transition = {'type':None,
					 'subtype':None,
					 'mode':None,
					 'fadeColor':None,
				}
	__transitionModifiers = {'horzRepeat':None,
				 'vertRepeat':None,
				 'borderWidth':None,
				 'borderColor':None,
				 }

	from settings import profileExtensions
	
	if profileExtensions.get('SplineAnimation'):
		__animate_attrs_extra['keySplines'] = None
		__animate_attrs_extra['keyTimes'] = None

	attributes['animateMotion'] = __animate_attrs_core.copy()
	attributes['animateMotion'].update(__animate_attrs_extra)
	attributes['animateMotion']['calcMode'] = None
	if profileExtensions.get('SplineAnimation'):
		attributes['animateMotion']['path'] = None
	attributes['animateMotion']['origin'] = None

	attributes['animate'] = __animate_attrs_core.copy()
	attributes['animate'].update(__animate_attrs_extra)

	attributes['animateColor'] = __animate_attrs_core.copy()
	attributes['animateColor'].update(__animate_attrs_extra)

	attributes['set'] = __animate_attrs_core.copy()

	if profileExtensions.get('InlineTransitions'):
		__animate_elements.append('transitionFilter')
		attributes['transitionFilter'] = __animate_attrs_core.copy()
		attributes['transitionFilter'].update(__animate_attrs_extra)
		attributes['transitionFilter'].update(__transitionFilter_transition)
		attributes['transitionFilter'].update(__transitionModifiers)
		del attributes['transitionFilter']['attributeName']
		del attributes['transitionFilter']['attributeType']

	del __animate_attrs_core, __animate_attrs_extra

	if profileExtensions.get('TimeManipulations'):
		# add TimeManipulations to certain elements
		for __el in __animate_elements:
			attributes[__el].update(__timeManipulations)

	# Abbreviations for collections of elements
	__Schedule = ['par', 'seq', 'excl']
	__MediaContent = ['text', 'img', 'audio', 'video', 'ref', 'animation', 'textstream', 'brush', 'param']
	__ContentControl = ['switch', 'prefetch']
	__LinkAnchor = ['a', 'area', 'anchor']
	__Animation = ['animate', 'set', 'animateMotion', 'animateColor']
	if profileExtensions.get('InlineTransitions'):__Animation.append('transitionFilter')

	__schedule = ['par', 'seq', 'excl'] + __media_object
	__container_content = __schedule + ['switch', 'a'] + __animate_elements + [__assets]
	__media_content = ['anchor', 'area', 'param', 'switch'] + __animate_elements

	# Core, Test and I18n attribs are added to all elements in the language
	for __el in attributes.keys():
		if __el[:len(GRiNSns)+1] == GRiNSns+' ':
			for __key, __val in __Core.items() + __Test.items():
				if ' ' in __key:
					attributes[__el][__key] = __val
					attributes[__el][GRiNSns+' '+__key.split(' ')[1]] = __val
				else:
					attributes[__el][GRiNSns+' '+__key] = __val
		else:
			attributes[__el].update(__Core)
			if __el not in ('head', 'meta', 'metadata',
					'body', 'customTest'):
				attributes[__el].update(__Test)
		attributes[__el].update(__I18n)

	# add basicTiming to certain elements
	for __el in ('a', 'animate', 'set',
		     'animateMotion', 'animateColor',
		     'area', 'anchor',
		     ):
		attributes[__el].update(__basicTiming)
	if profileExtensions.get('InlineTransitions'):
		attributes['transitionFilter'].update(__basicTiming)

	# add Timing to certain other elements
	for __el in ('text', 'img', 'audio', 'animation', 'video', 'ref',
		     'textstream', 'brush', 'body', 'par', 'seq',
		     'excl', 'prefetch'):
		if __el[:len(GRiNSns)+1] == GRiNSns+' ':
			for __key, __val in __Timing.items():
				if ' ' in __key:
					attributes[__el][__key] = __val
					attributes[__el][GRiNSns+' '+__key.split(' ')[1]] = __val
				else:
					attributes[__el][GRiNSns+' '+__key] = __val
		else:
			attributes[__el].update(__Timing)

	# fix up SMIL 2.0 namespace
	for __el, __atd in attributes.items():
		if ' ' not in __el and ':' not in __el:
			# SMIL 1.0 element, make a SMIL 2.0 copy
			__atd = __atd.copy()
			for __ns in SMIL2ns:
				attributes[__ns+' '+__el] = __atd
			for __at, __vl in __atd.items():
				if ' ' not in __at and ':' not in __at:
					for __ns in SMIL2ns:
						__atd[__ns+' '+__at] = __vl
##					del __atd[__at]
					if ATTRIBUTES.has_key(__at):
						for __sns in SMIL2ns:
							if __sns[-1:] != '/':
								continue
							for __ns in ATTRIBUTES[__at]:
								__atd[__sns + __ns+' '+__at] = __vl
					else:
						# make sure all attributes are represented in ATTRIBUTES
						ATTRIBUTES[__at] = []
					for __ns in ELEMENTS.keys():
						if ELEMENTS[__ns].has_key(__el) and __at in ELEMENTS[__ns][__el]:
							for __sns in SMIL2ns:
								if __sns[-1:] != '/':
									continue
								__atd[__sns + __ns+' '+__at] = __vl

	for __ns in ELEMENTS.keys():
		for __el in ELEMENTS[__ns].keys():
			if not attributes.has_key(__el):
				continue
			for __sns in SMIL2ns:
				if __sns[-1:] != '/':
					continue
				__atd = attributes[__el].copy()
				attributes[__sns + __ns+' '+__el] = __atd
				for __at in ELEMENTS[__ns][__el]:
					if __atd.has_key(__at):
						__atd[__sns + __ns + ' ' + __at] = __atd[__at]
			
	del __el, __atd, __at, __vl, __key, __val, __ns, __sns

	# all entities with their allowed content
	# no allowed content is default, so we don't specify empty ones here
	entities = {
		'smil': ['head', 'body'],
		'head': ['layout', 'switch', 'meta', 'metadata',
			 'customAttributes', __layouts, 'transition', __viewinfo],
		'customAttributes': ['customTest'],
		'layout': ['region', 'root-layout', 'topLayout', 'viewport', 'regPoint', 'switch'],
		'topLayout': ['region', 'switch'],
		'region': ['region', 'switch'],
		'transition': ['param'],
		__layouts: [__layout],
		'body': __container_content,
		'par': __container_content,
		'seq': __container_content,
		'excl': __container_content + ['priorityClass'],
		'priorityClass': __container_content,
		'switch': ['layout', 'region', 'topLayout', 'viewport'] + __container_content,
		'ref': __media_content,
		'audio': __media_content,
		'img': __media_content,
		'video': __media_content,
		'text': __media_content,
		'animation': __media_content,
		'textstream': __media_content,
		'brush': __media_content,
		__null: __media_content,
		'a': __schedule + ['switch'],
		__assets: __container_content,

##		'switch': __Schedule + __MediaContent + __ContentControl + __LinkAnchor + __Animation + ['priorityClass','layout'],
##		'customAttributes': ['customTest'],
##		'region': ['region'],
##		'topLayout': ['region'],
##		'layout': ['root-layout', 'region', 'topLayout', 'viewport', 'regPoint'],
##		'a': __Schedule + __MediaContent + __ContentControl + __Animation,
##		'area': ['animate', 'set'],
##		'anchor': ['animate', 'set'],
##		'text': ['param', 'area', 'anchor', 'switch'] + __Animation,
##		'img': ['param', 'area', 'anchor', 'switch'] + __Animation,
##		'audio': ['param', 'area', 'anchor', 'switch'] + __Animation,
##		'animation': ['param', 'area', 'anchor', 'switch'] + __Animation,
##		'video': ['param', 'area', 'anchor', 'switch'] + __Animation,
##		'ref': ['param', 'area', 'anchor', 'switch'] + __Animation,
##		'textstream': ['param', 'area', 'anchor', 'switch'] + __Animation,
##		'brush': ['param', 'area', 'anchor', 'switch'] + __Animation,
##		'smil': ['head', 'body'],
##		'head': ['meta', 'customAttributes', 'metadata', 'layout', 'switch', 'transition'],
##		'body': __Schedule + __MediaContent + __ContentControl + ['a'],
##		'par': __Schedule + __MediaContent + __ContentControl + ['a'] + __Animation,
##		'seq': __Schedule + __MediaContent + __ContentControl + ['a'] + __Animation,
##		'excl': __Schedule + __MediaContent + __ContentControl + ['a'] + __Animation + ['priorityClass'],
##		'priorityClass': __Schedule + __MediaContent + __ContentControl + ['a'] + __Animation,
		}
	entities['viewport'] = entities['topLayout'][:]

	# cleanup
	del __null
	del __media_object, __schedule, __container_content,
	del __media_content
	del __layouts, __layout
	del __animate_elements
	del __I18n, __basicTiming, __Timing, __Core, __Test

_modules = {
	# SMIL 2.0 Modules
	'AccessKeyTiming': 1,
	'AudioLayout': 1,
	'BasicAnimation': 1,
	'BasicContentControl': 1,
	'BasicInlineTiming': 1,
	'BasicLayout': 1,
	'BasicLinking': 1,
	'BasicMedia': 1,
	'BasicTimeContainers': 1,
	'BasicTransistions': 1,
	'BrushMedia': 1,
##	'CoordinatedTransitions': 1,
	'CustomTestAttributes': 1,
	'EventTiming': 1,
	'ExclTimeContainers': 1,
	'FillDefault': 1,
	'HierarchicalLayout': 1,
	'InlineTransitions': 1,
	'LinkingAttributes': 1,
	'MediaAccessibility': 1,
	'MediaClipMarkers': 0,
	'MediaClipping': 1,
	'MediaDescriptions': 1,
	'MediaMarkerTiming': 0,
	'MediaParam': 1,
	'Metainformation': 1,
	'MinMaxTiming': 1,
	'MultiArcTiming': 1,
	'MultiWindowLayout': 1,
	'ObjectLinking': 1,
	'PrefetchControl': 1,
##	'PrevTiming': 1,
	'RepeatTiming': 1,
	'RestartDefault': 1,
	'RestartTiming': 1,
	'SkipContentControl': 1,
	'SplineAnimation': 1,
	'Structure': 1,
	'SyncbaseTiming': 1,
	'SyncBehavior': 1,
	'SyncBehaviorDefault': 1,
	'SyncMaster': 0,
	'TimeContainerAttributes': 0,
	'TimeManipulations': 1,
	'TransitionModifiers': 1,
	'WallclockTiming': 1,

	# SMIL 2.0 Psuedo Modules
	'NestedTimeContainers': 1,
	'DeprecatedFeatures': 1,

	# SMIL 2.0 Module Collections
	'Language': 1,
	'HostLanguage': 1,
	'IntegrationSet': 1,
}

extensions = {
	# SMIL 1.0
	'http://www.w3.org/TR/REC-smil/': 1,
}

for _k, _v in _modules.items():
	for _ns in SMIL2ns:
		if _ns[-1] == '/':
			extensions[_ns + _k] = _v
del _k, _v, _ns, _modules
