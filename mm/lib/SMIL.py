SMIL_BASIC = 'text/smil-basic-layout'
SMILpubid = "-//W3C//DTD SMIL 1.0//EN"
SMILdtd = "http://www.w3.org/TR/REC-smil/SMIL10.dtd"
CMIFns = "http://www.cwi.nl/Chameleon/"

class SMIL:
	# some abbreviations
	__layouts = CMIFns + ' ' + 'layouts'
	__layout = CMIFns + ' ' + 'layout'
	__bag = CMIFns + ' ' 'bag'
	__cmif = CMIFns + ' ' 'cmif'
	__shell = CMIFns + ' ' 'shell'
	__socket = CMIFns + ' ' 'socket'
	__user_attributes = CMIFns + ' ' 'user-attributes'
	__u_group = CMIFns + ' ' 'u-group'

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
			   'z-index':'0'},
		'root-layout': {'background-color':'transparent',
				'height':'0',
				'id':None,
				'overflow':'hidden',
				'skip-content':'true',
				'title':None,
				'width':'0'},
		__layouts: {CMIFns+' ' 'id':None},
		__layout: {CMIFns+' ' 'id':None,
##			   CMIFns+' ' 'title':None,
			   CMIFns+' ' 'regions':None},
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
			__layout:None},
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
			__layout:None,},
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
		__bag: {CMIFns+' ' 'abstract':'',
			CMIFns+' ' 'author':'',
			CMIFns+' ' 'bag-index':None,
			CMIFns+' ' 'copyright':'',
			CMIFns+' ' 'id':None,
			CMIFns+' ' 'system-bitrate':None,
			CMIFns+' ' 'system-captions':None,
			CMIFns+' ' 'system-language':None,
			CMIFns+' ' 'system-overdub-or-caption':None,
			CMIFns+' ' 'system-required':None,
			CMIFns+' ' 'system-screen-depth':None,
			CMIFns+' ' 'system-screen-size':None,
			CMIFns+' ' 'title':None,
			CMIFns+' ' 'bag-index':None,
			__u_group:None,
			__layout:None},
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
			__layout:None},
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
			   CMIFns+' ' 'fragment-id':None},
		__user_attributes: {CMIFns+' ' 'id':None,
				    },
		__u_group: {CMIFns+' ' 'id':None,
			    CMIFns+' ' 'u_state':'RENDERED',
			    CMIFns+' ' 'title':None,
			    CMIFns+' ' 'override':'allowed',
			    },
		}

	__media_object = ['audio', 'video', 'text', 'img', 'animation',
			  'textstream', 'ref', __cmif, __shell, __socket]

	__at = None
	for __el in __media_object:
		if ' ' in __el:
			attributes[__el] = __at = {}
			for key, val in attributes['ref'].items():
				if ' ' in key:
					__at[key] = val
				else:
					__at[CMIFns+' '+key] = val
		else:
			attributes[__el] = attributes['ref']
	del __el, __at

	__schedule = ['par', 'seq', __bag] + __media_object
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
		__bag: __container_content,
		'switch': ['layout'] + __container_content,
		'ref': __assoc_link,
		'audio': __assoc_link,
		'img': __assoc_link,
		'video': __assoc_link,
		'text': __assoc_link,
		'animation': __assoc_link,
		'textstream': __assoc_link,
		__cmif: __assoc_link,
		__shell: __assoc_link,
		__socket: __assoc_link,
		'a': __schedule + ['switch'],
		'anchor': __empty,
		}

	# cleanup
	del __bag, __cmif, __shell, __socket, __user_attributes
	del __u_group, __media_object, __schedule, __container_content,
	del __assoc_link, __empty
	del __layouts, __layout
