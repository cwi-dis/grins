# Table mapping channel types to channel classes.
# Edit this module to add new classes.

from NullChannel import NullChannel
from TextChannel import TextChannel
from SoundChannel import SoundChannel
from ImageChannel import ImageChannel
from MovieChannel import MovieChannel
from ShellChannel import ShellChannel
from PythonChannel import PythonChannel
from VcrChannel import VcrChannel
from SocketChannel import SocketChannel
from MpegChannel import MpegChannel
from CmifChannel import CmifChannel
from LayoutChannel import LayoutChannel
from NTextChannel import NTextChannel
from MidiChannel import MidiChannel
try:
	from HtmlChannel import HtmlChannel
except ImportError:
	from PseudoHtmlChannel import HtmlChannel
	print 'WARNING: cheap plastic imitation of HTML channel loaded'
from GraphChannel import GraphChannel

channelmap = {
	'null': 	NullChannel,
	'text': 	TextChannel,
	'sound':	SoundChannel,
	'image': 	ImageChannel,
	'movie': 	MovieChannel,
	'python': 	PythonChannel,
	'shell': 	ShellChannel,
	'vcr':		VcrChannel,
	'socket':	SocketChannel,
	'mpeg':		MpegChannel,
	'cmif':		CmifChannel,
	'html':		HtmlChannel,
	'ntext':	NTextChannel,
	'graph':	GraphChannel,
	'layout':	LayoutChannel,
	'midi':		MidiChannel,
	}

channeltypes = ['null', 'text', 'image']
commonchanneltypes = ['text', 'image', 'sound', 'movie', 'layout']
otherchanneltypes = []
channelhierarchy = [
    ('text', ['ntext', 'text', 'html']),
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
	'ntext':	't',
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
