# Table mapping channel types to channel classes.
# Edit this module to add new classes.

from NullChannel import NullChannel
from TextChannel import TextChannel
from SoundChannel import SoundChannel
from ImageChannel import ImageChannel
from MovieChannel import MovieChannel
from ShellChannel import ShellChannel

channelmap = { \
	'null': 	NullChannel, \
	'text': 	TextChannel, \
	'sound':	SoundChannel, \
	'image': 	ImageChannel, \
	'movie': 	MovieChannel, \
	'shell': 	ShellChannel, \
	}

channeltypes = ['null', 'text', 'image']
ct = channelmap.keys()
ct.sort()
for t in ct:
	if t not in channeltypes:
		channeltypes.append(t)
del ct, t
