SMIL_BASIC = 'text/smil-basic-layout'
SMILpubid = "-//W3C//DTD SMIL 1.0//EN"
SMILdtd = "http://www.w3.org/TR/REC-smil/SMIL10.dtd"
CMIFns = "http://www.cwi.nl/Chameleon/"

class SMIL:
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
## 			'sync':None,
			'system-bitrate':None,
			'system-captions':None,
			'system-language':None,
			'system-overdub-or-caption':None,
			'system-required':None,
			'system-screen-depth':None,
			'system-screen-size':None,
			'title':None},
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
			'title':None},
		'switch': {'id':None,
			   'system-bitrate':None,
			   'system-captions':None,
			   'system-language':None,
			   'system-overdub-or-caption':None,
			   'system-required':None,
			   'system-screen-depth':None,
			   'system-screen-size':None},
		'ref': {'abstract':'',
			'alt':None,
			'author':'',
			'begin':None,
			'clip-begin':None,
			'clip-end':None,
			'copyright':'',
			'dur':None,
## 			'encoding':'base64',
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
			'type':None},
		'a': {'href':None,
		      'id':None,
		      'show':'replace',
		      'title':None},
		'anchor': {'begin':None,
			   'coords':None,
			   'end':None,
## 			   'fragment-id':None,
			   'href':None,
			   'id':None,
			   'show':'replace',
			   'skip-content':'true',
			   'title':None},
		}
	__bag_attributes = {'abstract':'',
			    'author':'',
			    'bag-index':None,
			    'copyright':'',
			    'id':None,
			    'system-bitrate':None,
			    'system-captions':None,
			    'system-language':None,
			    'system-overdub-or-caption':None,
			    'system-required':None,
			    'system-screen-depth':None,
			    'system-screen-size':None,
			    'title':None}
	__user_attributes_attributes = {'id':None,
					}
	__u_group_attributes = {'id':None,
				'u_state':'RENDERED',
				'title':None,
				'override':'allowed',
				}

	attributes['ref'] = attributes['ref']
	attributes['text'] = attributes['ref'].copy()
	attributes['text']['encoding'] = 'UTF'
	attributes['audio'] = attributes['ref']
	attributes['img'] = attributes['ref']
	attributes['video'] = attributes['ref']
	attributes['animation'] = attributes['ref']
	attributes['textstream'] = attributes['ref'].copy()
	attributes['textstream']['encoding'] = 'UTF'

	__media_object = ['audio', 'video', 'text', 'img', 'animation',
			  'textstream', 'ref']
	__schedule = ['par', 'seq'] + __media_object
	__container_content = __schedule + ['switch', 'a']
	__assoc_link = ['anchor']
	__empty = []
	entities = {
		'smil': ['head', 'body'],
		'head': ['layout', 'switch', 'meta'],
		'layout': ['region', 'root-layout'],
		'region': __empty,
		'meta': __empty,
		'body': __container_content,
		'par': __container_content,
		'seq': __container_content,
		'switch': ['layout'] + __container_content,
		'ref': __assoc_link,
		'audio': __assoc_link,
		'img': __assoc_link,
		'video': __assoc_link,
		'text': __assoc_link,
		'animation': __assoc_link,
		'textstream': __assoc_link,
		'a': __schedule + ['switch'],
		'anchor': __empty,
		}

	def init_cmif_namespace(self, prefix):
		self.attributes[prefix + ':cmif'] = d = {}
		for key, val in self.attributes['text'].items():
			d[prefix + ':' + key] = val
		self.attributes[prefix + ':socket'] = d = {}
		for key, val in self.attributes['text'].items():
			d[prefix + ':' + key] = val
		self.attributes[prefix + ':shell'] = d = {}
		for key, val in self.attributes['text'].items():
			d[prefix + ':' + key] = val
		self.attributes[prefix + ':bag'] = d = {}
		for key, val in self.__bag_attributes.items():
			d[prefix + ':' + key] = val

		for tag in ('cmif', 'socket', 'shell'):
			key = '%s:%s' % (prefix, tag)
			self.__media_object.append(key)
			self.entities[key] = self.__assoc_link
			self.__schedule.append(key)
			self.__container_content.append(key)
			self.entities['a'].append(key)
			self.entities['switch'].append(key)
		self.__schedule.append(prefix + ':bag')
		self.__container_content.append(prefix + ':bag')
		self.entities['a'].append(prefix + ':bag')
		self.entities['switch'].append(prefix + ':bag')
		self.entities[prefix + ':bag'] = self.__container_content

		self.attributes[prefix + ':user_attributes'] = d = {}
		for key, val in self.__user_attributes_attributes.items():
			d[prefix + ':' + key] = val
		u_group = '%s:u_group' % prefix
		self.attributes[u_group] = d = {}
		for key, val in self.__u_group_attributes.items():
			d['%s:%s' % (prefix, key)] = val
		self.entities['head'].append('%s:user_attributes' % prefix)
		self.entities['%s:user_attributes' % prefix] = [u_group]
		for tag in ['par', 'seq', '%s:bag' % prefix, 'switch'] + self.__media_object:
			self.attributes[tag][u_group] = None
