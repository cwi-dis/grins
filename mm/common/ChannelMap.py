__version__ = "$Id$"

# Table mapping channel types to channel classes.
# Edit this module to add new classes.

class ChannelMap:
	channelmap = {
		'null': 	'NullChannel',
		'text': 	'TextChannel',
		'sound':	'SoundChannel',
		'image': 	'ImageChannel',
		'movie': 	'MovieChannel',
		'python': 	'PythonChannel',
		'shell': 	'ShellChannel',
		'vcr':		'VcrChannel',
		'socket':	'SocketChannel',
		'video':	'VideoChannel',
		'mpeg':		'VideoChannel',
		'cmif':		'CmifChannel',
		'html':		['HtmlChannel', 'PseudoHtmlChannel'],
		'label':	'LabelChannel',
		'graph':	'GraphChannel',
		'layout':	'LayoutChannel',
		'midi':		[ 'MidiChannel', 'SoundChannel' ],
		'word':		'WordChannel',
		'external':	'ExternalChannel',
		}

	has_key = channelmap.has_key
	keys = channelmap.keys

	def __init__(self):
		self.channelmodules = {} # cache of imported channels

	def __getitem__(self, key):
		try:
			return self.channelmodules[key]
		except KeyError:
			pass
		item = self.channelmap[key]
		if type(item) is type(''):
			item = [item]
		for chan in item:
			try:
				exec 'from %(chan)s import %(chan)s' % \
				     {'chan': chan}
			except ImportError, arg:
				print 'Warning: cannot import channel %s: %s' % (chan, arg)
			else:
				mod = eval(chan)
				self.channelmodules[key] = mod
				return mod
		# no success, use NullChannel as backup
		exec 'from NullChannel import NullChannel'
		self.channelmodules[key] = NullChannel
		return NullChannel

channelmap = ChannelMap()

channeltypes = ['null', 'text', 'image']
commonchanneltypes = ['text', 'image', 'sound', 'video', 'layout']
otherchanneltypes = []
channelhierarchy = [
    ('text', ['label', 'text', 'html']),
    ('image', ['image', 'graph']),
    ('sound', ['sound']),
    ('movie', ['video', 'movie', 'mpeg', 'vcr']),
    ('control', ['layout', 'cmif', 'socket', 'shell', 'python', 'external',
		 'null']),
    ('ole', ['word']),
    ]

ct = channelmap.keys()
ct.sort()
for t in ct:
	if t not in channeltypes:
		channeltypes.append(t)
	if t not in commonchanneltypes:
		if t not in ('mpeg', 'movie'): # deprecated
			otherchanneltypes.append(t)
del ct, t

shortcuts = {
	'null': 	'0',
	'text': 	'T',
	'label':	'L',
	'sound':	'S',
	'image': 	'I',
	'video':	'v',
	'movie': 	'M',
	'python': 	'P',
	'shell': 	'!',
	'vcr': 		'V',
	'socket': 	's',
	'mpeg': 	'm',
	'cmif': 	'C',
	'html': 	'H',
	'graph': 	'G',
	'word':		'W',
	'external':	'X',
	}
