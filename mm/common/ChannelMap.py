__version__ = "$Id$"

import compatibility
import features

# Table mapping channel types to channel classes.
# Edit this module to add new classes.
from sys import platform

# This code is here for freeze only:
def _freeze_dummy_func():
	import HtmlChannel
	import ImageChannel
	import LayoutChannel
	import MidiChannel
	import NullChannel
	import PseudoHtmlChannel
	import RealPixChannel
	import RealTextChannel
	import SoundChannel
	import TextChannel
	import VideoChannel
	import AnimateChannel
	import BrushChannel
	import PrefetchChannel

class ChannelMap:
	channelmap = {
		'null': 	'NullChannel',
		'text': 	'TextChannel',
		'sound':	'SoundChannel',
		'image': 	'ImageChannel',
		'video':	'VideoChannel',
		'html':		['HtmlChannel', 'PseudoHtmlChannel'],
		'layout':	'LayoutChannel',
		'RealPix':	'RealPixChannel',
		'RealText':	'RealTextChannel',
		'animate':	'AnimateChannel',
		'brush':	'BrushChannel',
		'prefetch':	'PrefetchChannel',
		}

	has_key = channelmap.has_key
	keys = channelmap.keys

	def __init__(self):
		self.channelmodules = {} # cache of imported channels

	def __getitem__(self, key):
		if self.channelmodules.has_key(key):
			return self.channelmodules[key]
		item = self.channelmap[key]
		if type(item) is type(''):
			item = [item]
		for chan in item:
			try:
				exec 'from %(chan)s import %(chan)s' % \
				     {'chan': chan}
			except ImportError, arg:
				if type(arg) is type(self):
					arg = arg.args[0]
				print 'Warning: cannot import channel %s: %s' % (chan, arg)
			else:
				mod = eval(chan)
				self.channelmodules[key] = mod
				return mod
		# no success, use NullChannel as backup
		exec 'from NullChannel import NullChannel'
		self.channelmodules[key] = NullChannel
		return NullChannel

	def get(self, key, default = None):
		if channelmap.has_key(key):
			return self.__getitem__(key)
		return default

channelmap = ChannelMap()


class InternalChannelMap(ChannelMap):
	channelmap = {
		'null': 	'NullChannel',
		'animate':	'AnimateChannel',
		}
	has_key = channelmap.has_key
	keys = channelmap.keys

internalchannelmap = InternalChannelMap()

	
channeltypes = ['null', 'text', 'image']
commonchanneltypes = ['text', 'image', 'sound', 'video', 'layout']
otherchanneltypes = []
channelhierarchy = {
    'text': ['text', 'html'],
    'image': ['image'],
    'sound': ['sound'],
    'movie': ['video'],
    'control': ['layout', 'null', 'animate', 'prefetch'],
    }
SMILchanneltypes = ['image', 'sound', 'video', 'text']
if features.compatibility == compatibility.G2:
	SMILchanneltypes = SMILchanneltypes+['RealPix', 'RealText']
	if platform == 'linux2':
		SMILchanneltypes = SMILchanneltypes+['RealAudio', 'RealVideo']
SMILextendedchanneltypes = ['html']
SMILBostonChanneltypes = ['brush', 'prefetch']

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
	'sound':	'S',
	'image': 	'I',
	'video':	'v',
	'html': 	'H',
	}

def getvalidchanneltypes(context):
	"""Return the list of channels to be shown in menus and such.
	Either the full list or the SMIL-supported list is returned."""
	import settings
	if settings.get('cmif'):
		return commonchanneltypes + otherchanneltypes
	rv = SMILchanneltypes
	import features
	if features.compatibility in (features.SMIL10, features.Boston):
		rv = rv + SMILextendedchanneltypes
	if context.attributes.get('project_boston'):
		rv = rv + SMILBostonChanneltypes
	if not features.lightweight:
		rv = rv + ['null']
	return rv

def isvisiblechannel(type):
	return type in ('text', 'image', 'video', 'html', 'layout', 'brush',
			'RealPix', 'RealText', 'RealVideo')
