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
		'mpeg':		'MpegChannel',
		'cmif':		'CmifChannel',
		'html':		['HtmlChannel', 'PseudoHtmlChannel'],
		'label':	'LabelChannel',
		'graph':	'GraphChannel',
		'layout':	'LayoutChannel',
		'midi':		'MidiChannel',
		}

	has_key = channelmap.has_key
	keys = channelmap.keys

	def __getitem__(self, key):
		item = self.channelmap[key]
		if type(item) == type(''):
			item = [item]
		for chan in item:
			try:
				exec 'from %(chan)s import %(chan)s' % \
				     {'chan': chan}
			except ImportError, arg:
				print 'Warning: cannot import channel %s: %s' % (chan, arg)
			else:
				return eval(chan)
		# no success, use NullChannel as backup
		exec 'from NullChannel import NullChannel'
		return NullChannel

channelmap = ChannelMap()

channeltypes = ['null', 'text', 'image']
commonchanneltypes = ['text', 'image', 'sound', 'movie', 'layout']
otherchanneltypes = []
channelhierarchy = [
    ('text', ['label', 'text', 'html']),
    ('image', ['image', 'graph']),
    ('sound', ['sound']),
    ('movie', ['movie', 'mpeg', 'vcr']),
    ('control', ['layout', 'cmif', 'socket', 'shell', 'python', 'null']),
    ]

ct = channelmap.keys()
ct.sort()
for t in ct:
	if t not in channeltypes:
		channeltypes.append(t)
	if t not in commonchanneltypes:
		otherchanneltypes.append(t)
del ct, t

shortcuts = {
	'null': 	'0',
	'text': 	'T',
	'label':	'L',
	'sound':	'S',
	'image': 	'I',
	'movie': 	'M',
	'python': 	'P',
	'shell': 	'!',
	'vcr': 		'V',
	'socket': 	's',
	'mpeg': 	'm',
	'cmif': 	'C',
	'html': 	'H',
	'graph': 	'G',
	}
