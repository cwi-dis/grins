SMIL_BASIC = 'text/smil-basic-layout'
SMILpubid = "-//W3C//DTD SMIL 1.0//EN"
SMILdtd = "http://www.w3.org/TR/REC-smil/SMIL10.dtd"
GRiNSns = "http://www.oratrix.com/"

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
	__user_attributes = GRiNSns + ' ' 'user-attributes'
	__u_group = GRiNSns + ' ' 'u-group'

	# all allowed entities with all their attributes
	attributes = {
		'smil': {'id':None},
		'head': {'id':None},
		'body': {'id':None},
		'meta': {'content':None,
			 'id':None,
			 'name':None},
		'layout': {'id':None,
			   'type':SMIL_BASIC},
		'region': {'background-color':'transparent',
			   'fit':'hidden',
			   'height':'0',
			   'id':None,
			   'left':'0',
			   'skip-content':'true',
			   'title':None,
			   'top':'0',
			   'width':'0',
			   'z-index':'0',
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
		'root-layout': {'background-color':'transparent',
				'height':'0',
				'id':None,
				'overflow':'hidden',
				'skip-content':'true',
				'title':None,
				'width':'0'},
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
			'id':None,
			'region':None,
			'repeat':'1',
			'system-bitrate':None,
			'system-captions':None,
			'system-language':None,
			'system-overdub-or-caption':None,
			'system-required':None,
			'system-screen-depth':None,
			'system-screen-size':None,
			'title':None,
			__u_group:None,
			__layout:None,
			GRiNSns+' ' 'comment':None,
			},
		'seq': {'abstract':'',
			'author':'',
			'begin':None,
			'copyright':'',
			'dur':None,
			'end':None,
			'id':None,
			'repeat':'1',
			'system-bitrate':None,
			'system-captions':None,
			'system-language':None,
			'system-overdub-or-caption':None,
			'system-required':None,
			'system-screen-depth':None,
			'system-screen-size':None,
			'title':None,
			__u_group:None,
			__layout:None,
			GRiNSns+' ' 'comment':None,
			},
		'switch': {'id':None,
			   'system-bitrate':None,
			   'system-captions':None,
			   'system-language':None,
			   'system-overdub-or-caption':None,

			   'system-required':None,
			   'system-screen-depth':None,
			   'system-screen-size':None,
			   __u_group:None,
			   __layout:None},
		__choice: {GRiNSns+' ' 'abstract':'',
			   GRiNSns+' ' 'author':'',
			   GRiNSns+' ' 'choice-index':None,
			   GRiNSns+' ' 'copyright':'',
			   GRiNSns+' ' 'id':None,
			   GRiNSns+' ' 'system-bitrate':None,
			   GRiNSns+' ' 'system-captions':None,
			   GRiNSns+' ' 'system-language':None,
			   GRiNSns+' ' 'system-overdub-or-caption':None,
			   GRiNSns+' ' 'system-required':None,
			   GRiNSns+' ' 'system-screen-depth':None,
			   GRiNSns+' ' 'system-screen-size':None,
			   GRiNSns+' ' 'title':None,
			   __u_group:None,
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
			'id':None,
			'longdesc':None,
			'region':None,
			'repeat':'1',
			'src':None,
			'system-bitrate':None,
			'system-captions':None,
			'system-language':None,
			'system-overdub-or-caption':None,
			'system-required':None,
			'system-screen-depth':None,
			'system-screen-size':None,
			'title':None,
			'type':None,
			__u_group:None,
			__layout:None,
			GRiNSns+' ' 'bgcolor':None,
			GRiNSns+' ' 'comment':None,
			GRiNSns+' ' 'font':None,
			GRiNSns+' ' 'hicolor':None,
			GRiNSns+' ' 'pointsize':None,
			GRiNSns+' ' 'scale':None,
			},
		'a': {'href':None,
		      'id':None,
		      'show':'replace',
		      'title':None},
		'anchor': {'begin':None,
			   'coords':None,
			   'end':None,
			   'href':None,
			   'id':None,
			   'show':'replace',
			   'skip-content':'true',
			   'title':None,
			   GRiNSns+' ' 'fragment-id':None},
		__user_attributes: {GRiNSns+' ' 'id':None,
				    },
		__u_group: {GRiNSns+' ' 'id':None,
			    GRiNSns+' ' 'u-state':'RENDERED',
			    GRiNSns+' ' 'title':None,
			    GRiNSns+' ' 'override':'allowed',
			    },
		}
	attributes[__bag] = attributes[__choice]

	__media_object = ['audio', 'video', 'text', 'img', 'animation',
			  'textstream', 'ref', __null, __cmif, __shell,
			  __socket]

	__at = None
	for __el in __media_object:
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

	__schedule = ['par', 'seq', __choice, __bag] + __media_object
	__container_content = __schedule + ['switch', 'a']
	__assoc_link = ['anchor']
	__empty = []

	# all entities with their allowed content
	entities = {
		'smil': ['head', 'body'],
		'head': ['layout', 'switch', 'meta', __user_attributes, __layouts],
		__user_attributes: [__u_group,],
		__u_group: __empty,
		'layout': ['region', 'root-layout'],
		'region': __empty,
		'meta': __empty,
		__layouts: [__layout],
		'body': __container_content,
		'par': __container_content,
		'seq': __container_content,
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
		'anchor': __empty,
		}

	# cleanup
	del __choice, __bag, __cmif, __shell, __socket, __user_attributes
	del __u_group, __media_object, __schedule, __container_content,
	del __assoc_link, __empty
	del __layouts, __layout
