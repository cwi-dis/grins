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
from HtmlChannel import HtmlChannel
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
	'graph':	GraphChannel,
	}

channeltypes = ['null', 'text', 'image']
commonchanneltypes = ['text', 'image', 'sound', 'movie']
otherchanneltypes = []
ct = channelmap.keys()
ct.sort()
for t in ct:
	if t not in channeltypes:
		channeltypes.append(t)
	if t not in commonchanneltypes:
		otherchanneltypes.append(t)
del ct, t
