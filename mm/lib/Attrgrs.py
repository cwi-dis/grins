__version__ = "$Id$"

# Each group is a dictionary with entries:
# unique name 'name'
# display title 'title'
# attributes 'attrs'
# optional match method 'match'

# The order of groups in the attrgrs list is important (first is visited first for match)
# All attributes not in complete groups will be displayed on their own page
# unless we specify a different match condition ('part', 'first' default is: 'all')

attrgrs=(
	{'name':'general',
	'title': 'General',
	'attrs':[
		'name',
##		'.type',
		'title',
		'alt',
		'author',
		'copyright',
		'.begin1',
		'duration',
		]},

	{'name':'subregion',
	'title':'Destination rendering',
	'attrs':[
		'subregionxy',
		'subregionwh',
		'displayfull',
		'aspect',
		'project_quality',
		'project_convert',
		]},

	{'name':'subregion1',
	'title':'Destination rendering',
	'attrs':[
		'subregionxy',
		'subregionwh',
		'displayfull',
		'aspect',
		'project_quality',
		]},

	{'name':'subregion2',
	'title':'Destination rendering',
	'attrs':[
		'subregionxy',
		'subregionwh',
		'displayfull',
		]},

	{'name':'base_winoff_and_units',
	'title':'Position and size',
	'attrs':[
		'base_winoff',
		'units',
		'z',
		]},

	{'name':'base_winoff',
	'title':'Position and size',
	'attrs':[
		'base_winoff',
		'z',
		]},

	{'name':'system2',
	'title':'System properties',
	'attrs':[
		'system_bitrate',
		'system_captions',
		'system_language',
		'system_overdub_or_caption',
		'system_required',
		'system_screen_depth',
		'system_screen_size',
		'system_operating_system',
		'system_cpu',
		'system_audiodesc',
		'u_group',
		'system_component',
		]},

	{'name':'system3',
	'title':'System properties',
	'attrs':[
		'system_bitrate',
		'system_captions',
		'system_language',
		'system_overdub_or_caption',
		'system_required',
		'system_screen_depth',
		'system_screen_size',
		'system_operating_system',
		'system_cpu',
		'system_audiodesc',
		'system_component',
		]},

	{'name':'system',
	'title': 'System properties',
	'attrs':[
		'system_bitrate',
		'system_captions',
		'system_language',
		'system_overdub_or_caption',
		'system_required',
		'system_screen_depth',
		'system_screen_size',
		]},

	{'name':'preferences2',
	'title': 'Previewer switch settings',
	'attrs':[
		'system_bitrate',
		'system_captions',
		'system_language',
		'system_overdub_or_caption',
		'system_audiodesc',
		'showhidden',
		]},

	{'name':'preferences',
	'title': 'Ambulant preferences',
	'attrs':[
		'system_bitrate',
		'system_captions',
		'system_language',
		'system_overdub_or_caption',
		]},

	{'name':'preferencesPro',
	'title': 'Ambulant preferences',
	'attrs':[
		'default_sync_behavior_locked',
		'default_sync_tolerance',
		'enable_template',
		'saveopenviews',
		'initial_dialog',
		]},

	{'name':'snapsystem',
	'title': 'System',
	'attrs':[
		'system_bitrate',
		'system_language',
		]},

	{'name':'transition',
	'title': 'Transition',
	'attrs':[
		'transIn',
		'transOut',
		]},

	{'name':'.cname',
	'title':'General',
	'attrs':[
		'.cname',
		'title',
		'alt',
		'longdesc',
		'regionName',
		]},

	{'name':'.cname2',
	'title':'General',
	'attrs':[
		'.cname',
		'title',
		'alt',
		'longdesc',
		]},

	{'name':'name',
	'title':'General',
	'attrs':[
		'name',
		'channel',
		'.type',
		]},

	{'name':'intname',
	'title':'General',
	'attrs':[
		'name',
		'.type',
		]},

	{'name':'infofilegroup',
	'title': 'Info',
	'attrs':[
		'name',
		'title',
		'abstract',
		'alt',
		'longdesc',
		'author',
		'copyright',
		'file',
		]},

	{'name':'infofile1group',
	'title': 'Info',
	'attrs':[
		'name',
		'title',
		'alt',
		'longdesc',
		'file',
		]},

	{'name':'infogroup',
	'title': 'Info',
	'match': 'first',
	'attrs':[
		'name',
		'title',
		'abstract',
		'alt',
		'longdesc',
		'author',
		'copyright',
		]},

	{'name':'docinfo',
	 'title':'Info',
	 'attrs':['title',
		  'author',
		  'copyright',
##		  'comment',
		  ],
	 },

	# active duration group with endsync, clip, and erase
	{'name':'activeduration1',
	'title':'Active duration',
	'attrs':[
		'fill', 'fillDefault',
		'duration',
		'min', 'max',
		'loop', # repeatcount
		'repeatdur',
		'terminator',
		'clipbegin',
		'clipend',
		'erase',
		]},

	# active duration group with endsync and erase
	{'name':'activeduration4',
	'title':'Active duration',
	'attrs':[
		'fill', 'fillDefault',
		'duration',
		'min', 'max',
		'loop', # repeatcount
		'repeatdur',
		'terminator',
		'erase',
		]},

	# active duration group with endsync
	{'name':'activeduration3',
	'title':'Active duration',
	'attrs':[
		'fill', 'fillDefault',
		'duration',
		'min', 'max',
		'loop', # repeatcount
		'repeatdur',
		'terminator',
		]},

	# active duration group without endsync
	{'name':'activeduration2',
	'title':'Active duration',
	'attrs':[
		'fill', 'fillDefault',
		'duration',
		'min', 'max',
		'loop', # repeatcount
		'repeatdur',
		]},

	# active duration group without endsync and without fill/filldefault
	{'name':'activeduration',
	'title':'Active duration',
	'attrs':[
		'duration',
		'min', 'max',
		'loop', # repeatcount
		'repeatdur',
		]},
	
	{'name':'timingsb',
	'title':'Timing',
	'attrs':[
		'duration',
		'loop',
		'repeatdur',
		'begin',
		]},

	{'name':'timingpar',
	'title':'Timing',
	'attrs':[
		'duration',
		'loop',
		'begin',
		'terminator',
		]},

	{'name':'timing1',
	'title':'Timing',
	'attrs':[
		'duration',
		'loop',
		'begin',
		]},

	{'name':'timingfadeout',
	'title':'Transition',
	'attrs':[
		'tduration',
		'start',
		'fadeout',
		'fadeoutcolor',
		'fadeouttime',
		'fadeoutduration',
		'tag',
		]},

	{'name':'timing4',
	'title':'Transition',
	'attrs':[
		'tag',
		'start',
		'tduration',
		'color',
		]},

	{'name':'timing3',
	'title':'Transition',
	'attrs':[
		'tag',
		'start',
		'tduration',
		]},

	{'name':'timing3c',
	'title':'Transition',
	'attrs':[
		'tag',
		'start',
		'color',
		]},

	{'name':'timing2',
	'title':'Transition',
	'attrs':[
		'tag',
		'start',
		]},

	{'name':'synchronization',
	'title':'Synchronization',
	'attrs':['syncMaster',
		 'syncBehavior',
		 'syncBehaviorDefault',
		 'syncTolerance',
		 'syncToleranceDefault',
		 ]},

	{'name':'server',
	 'title':'Upload server',
	 'attrs':['project_ftp_host_media',
		  'project_ftp_user_media',
		  'project_ftp_dir_media',
		  'project_smil_url',
		  'project_ftp_host',
		  'project_ftp_user',
		  'project_ftp_dir',
		  'project_web_url',
		  ],
	 },

 	{'name':'webserver',
	'title':'Webserver',
	'attrs':[
		'project_ftp_host',
		'project_ftp_dir',
		'project_ftp_user'
		]},

  	{'name':'mediaserver',
	'title':'Mediaserver',
	'attrs':[
		'project_ftp_host_media',
		'project_ftp_dir_media',
		'project_ftp_user_media',
		'project_smil_url',
		]},

	{'name':'brush',
	'title':'Media',
	'attrs':[
		'fgcolor',
		'readIndex',
		'sensitivity',
		'erase',
		]},

	{'name':'media',
	'title':'Media',
	'attrs':[
		'file',
		'clipbegin',
		'clipend',
		'readIndex',
		'sensitivity',
		'erase',
		]},

	{'name':'file',
	'title':'URL',
	'attrs':[
		'file',
		]},

	{'name':'imgregion',
	'title':'Source area',
	'attrs':[
		'imgcropxy',
		'imgcropwh',
		'fullimage',
		]},

	{'name':'wipe',
	'title':'Wipe',
	'attrs':['wipetype',
		'direction',
		]},

	{'name':'convert5',
	'title':'Conversion',
	'attrs':[
		'project_targets',
		'project_videotype',
		'project_audiotype',
		'project_mobile',
		'project_perfect',
		'project_convert',
		]},

	{'name':'convert4',
	'title':'Conversion',
	'attrs':[
		'project_targets',
		'project_audiotype',
		'project_mobile',
		'project_perfect',
		'project_convert',
		]},

	{'name':'convert3',
	'title':'Conversion',
	'attrs':[
		'project_targets',
		'project_videotype',
		'project_audiotype',
		]},

	{'name':'convert2',
	'title':'Conversion',
	'attrs':[
		'project_targets',
		'project_audiotype',
		]},

	{'name':'convert1',
	'title':'Conversion',
	'attrs':[
		'project_convert',
		'project_quality',
		]},

	{'name':'clip',
	'title':'Clip',
	'attrs':[
		'clipbegin',
		'clipend',
		]},
		
	{'name':'bandwidth',
	'title':'Bandwidth',
	'attrs':[
		'bitrate',
		'maxfps',
		'preroll',
		]},

	{'name':'qtpreferences',
	'title':'QuickTime preferences',
	'attrs':[
		'autoplay',
		'qtnext',
		'qttimeslider',
		'qtchaptermode',
		'immediateinstantiation',
		]},

	{'name':'qtmediapreferences',
	'title':'QuickTime properties',
	'attrs':[
		'immediateinstantiationmedia',
		'bitratenecessary',
		'systemmimetypesupported',
		'attachtimebase',
		'qtchapter',
		'qtcompositemode',
		]},

	{'name':'animateValues',
	'title':'Values',
	'match': 'first',
	'attrs':[
		'from',
		'to',
		'by',
		'values',
		'additive',
		'accumulate',
		]},

	{'name':'animateTargetSet',
	 'title':'Animate target',
	 'attrs':['atag',
		  'targetElement',
		  'attributeName',
		  'attributeType',
		  'to',
		  ]},

	{'name':'animateTarget',
	 'title':'Animate target',
	 'attrs':['atag',
		  'targetElement',
		  'attributeName',
		  'attributeType',
		  ]},

	{'name':'animateTargetMotion',
	 'title':'Animate target',
	 'attrs':['atag',
		  'targetElement',
		  'path',
		  'origin',
		  ]},

	{'name':'timeManipulation',
	'title':'Time manipulations',
	'attrs':[
		'speed',
		'accelerate',
		'decelerate',
		'autoReverse',
		]},
	
	{'name':'calcMode',
	'title':'Calculation mode',
	'attrs':[
		'calcMode',
		'keyTimes',
		'keySplines',
		]},
	
	{'name':'transitionType',
	'title':'Transition type',
	'attrs':[
		'trname',
		'trtype',
		'subtype',
		]},

	{'name':'transitionRepeat',
	'title':'Repeat',
	'attrs':[
		'horzRepeat',
		'vertRepeat',
		]},

	{'name':'transitionTiming',
	'title':'Transition timing',
	'attrs':[
		'startProgress',
		'endProgress',
		'dur',
		]},

	{'name':'machine',
	'title':'Machine properties',
	'attrs':[
		'system_operating_system',
		'system_cpu',
		]},

	{'name':'Layout1',
	'title':'Subregion',
	'attrs':[
		'cssbgcolor',
		'regPoint','regAlign',
		'fit','z',
		'channel',
		]},

	{'name':'Layout2Real',
	'title':'Subregion',
	'attrs':[
		'cssbgcolor',
		'fit','z',
		'soundLevel',
		'showBackground',
		'opacity',
		]},

	{'name':'Layout2',
	'title':'Subregion',
	'attrs':[
		'cssbgcolor',
		'fit','z',
		'soundLevel',
		'showBackground',
		]},

	{'name':'Geometry',
	'title':'Geometry',
	'attrs':[
		'left', 'width', 'right',
		'top', 'height', 'bottom',
		]},

	{'name':'Layout3',
	'title':'Top Layout',
	'attrs':[
		'cssbgcolor',
		'width', 'height',
		'open', 'close',
		'traceImage',
		]},

	{'name':'regionname',
	'title':'General',
	'attrs':[
		'.cname',
		'regionName', 
		]},

	{'name':'viewportname',
	'title':'General',
	'attrs':[
		'.cname',
		]},

	{'name':'CssBackgroundColor',
	'title':'Background color',
	'attrs':[
		'cssbgcolor',
		]},

	{'name':'beginlist2',
	'title':'Begin',
	'attrs':['beginlist',
		 'restart', 'restartDefault',
		]},

	{'name':'beginlist',
	 'title':'Begin',
	 'attrs':['beginlist',],
	 },

	{'name':'endlist',
	 'title':'End',
	 'attrs':['endlist',],
	 },

	{'name':'containerlayout',
	'title':'Default layout',
	'attrs':[
		'project_default_region_image',
		'project_default_region_video',
		'project_default_region_sound',
		'project_default_region_text',
		]},

	{'name':'inlineTransition',
	 'title':'Transition',
	 'attrs':['trtype', 'subtype', 'mode', 'fadeColor',],
	 },

	{'name':'miscellaneous',
	 'title':'Miscellaneous',
	 'attrs':['backgroundOpacity',
		  'chromaKey',
		  'chromaKeyOpacity',
		  'chromaKeyTolerance',
		  'mediaOpacity',
		  'reliable',
		  'strbitrate',
		  'sensitivity',
		  ],
	 },

	{'name':'miscellaneous2',
	 'title':'Miscellaneous',
	 'attrs':['backgroundOpacity',
		  'chromaKey',
		  'chromaKeyOpacity',
		  'chromaKeyTolerance',
		  'mediaOpacity',
		  'reliable',
		  'sensitivity',
		  ],
	 },

	{'name':'prio',
	 'title':'Priorities',
	 'attrs':['higher',
		  'lower',
		  'peers',
		  'pauseDisplay',
		  ],
	 },

	{'name':'foreign',
	 'title':'Foreign object',
	 'attrs':['elemname',
		  'namespace',
		  ],
	 },

	{'name':'genanchor',
	 'title':'Anchor settings',
	 'attrs':['.href',
		  'show',
		  'sourcePlaystate',
		  'destinationPlaystate',
		  'sendTo',
		  'accesskey',
		  'actuate',
		  ],
	 },

	{'name':'specanchor',
	 'title':'More anchor settings',
	 'attrs':['acoords',
		  'ashape',
		  'fragment',
		  'tabindex',
		  'external',
		  'sourceLevel',
		  'destinationLevel',
		  'target',
		  ],
	 },

	{'name':'empty',
	 'title':'Empty settings',
	 'attrs':['empty_icon',
		  'empty_text',
		  'empty_color',
		  'empty_duration',
		  ],
	 },

	{'name':'nonempty',
	 'title':'Non-empty settings',
	 'attrs':['non_empty_icon',
		  'non_empty_text',
		  'non_empty_color',
		  ],
	 },

	{'name':'template1',
	 'title':'Template settings',
	 'attrs':['thumbnail_icon',
		  'thumbnail_scale',
		  'dropicon',
		  'project_forcechild',
		  'project_default_duration',
		  ],
	 },

	{'name':'template2',
	 'title':'Template settings',
	 'attrs':['thumbnail_icon',
		  'thumbnail_scale',
		  'dropicon',
		  'project_autoroute',
		  'project_default_duration',
		  ],
	 },

	{'name':'template',
	 'title':'Template settings',
	 'attrs':['thumbnail_icon',
		  'thumbnail_scale',
		  'dropicon',
		  ],
	 },

	{'name':'doctemplate',
	 'title':'Template settings',
	 'attrs':['template_name',
		  'template_description',
		  'template_snapshot',
		  ],
	 },
	)
