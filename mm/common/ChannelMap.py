# Table mapping channel types to channel classes.
# Edit this module to add new classes.

from NullChannel import NullChannel
from TextChannel import TextChannel
from SoundChannel import SoundChannel
from ImageChannel import ImageChannel
from MovieChannel import MovieChannel

channelmap = { \
	'null': 	NullChannel, \
	'text': 	TextChannel, \
	'sound':	SoundChannel, \
	'image': 	ImageChannel, \
	'movie': 	MovieChannel, \
	}
