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

##	{'name':'subregion3',
##	'title':'Destination rendering',
##	'attrs':[
##		'left',
##		'width',
##		'top',
##		'height',
##		'scale',
##		]},

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

	{'name':'preferences',
	'title': 'GRiNS preferences',
	'attrs':[
		'system_bitrate',
		'system_captions',
		'system_language',
		'system_overdub_or_caption',
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
		'type',
		'title',
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

	{'name':'infogroup',
	'title': 'Info',
	'match': 'first',
	'attrs':[
		'title',
		'abstract',
		'alt',
		'longdesc',
		'author',
		'copyright',
		'comment'
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

	{'name':'fadeout',
	'title':'Fadeout',
	'attrs':['fadeout',
		'fadeoutcolor',
		'fadeouttime',
		'fadeoutduration',
		]},

	{'name':'wipe',
	'title':'Wipe',
	'attrs':['wipetype',
		'direction',
		]},

	{'name':'anchorlist',
	'title':'Anchors',
	'attrs':[
		'.anchorlist',
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

	{'name':'animateAttribute',
	'title':'Target attribute',
	'attrs':[
		'attributeName',
		'attributeType',
		]},

	{'name':'animateValues',
	'title':'Values',
	'match': 'first',
	'attrs':[
		'from',
		'to',
		'by',
		'values',
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

	{'name':'CssBackgroundColor',
	'title':'Background color',
	'attrs':[
		'cssbgcolor',
		]},
	)


