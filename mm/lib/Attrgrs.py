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
	{'name':'subregion',
	'title':'Destination rendering',
	'attrs':[
		'subregionxy',
		'subregionwh',
		'displayfull',
		'subregionanchor',
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

	{'name':'subregion4',
	'title':'Destination rendering',
	'attrs':[
		'subregionxy',
		'subregionwh',
		'displayfull',
		'subregionanchor',
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
		'imgcropanchor',
		]},

	{'name':'imgregion1',
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

	)


