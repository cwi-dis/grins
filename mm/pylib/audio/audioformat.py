__version__ = "$Id$"

mono = 'mono'
left = 'left'
right = 'right'

class AudioFormat:
	def __init__(self, name, descr, channels, encoding, blocksize, fpb):
		self.__name = name
		self.__descr = descr
		self.__channels = channels
		self.__encoding = encoding
		self.__blocksize = blocksize
		self.__fpb = fpb

	def __repr__(self):
		return self.__name

	def getname(self):
		return self.__name

	def getdescr(self):
		return self.__descr

	def getnchannels(self):
		return len(self.__channels)

	def getencoding(self):
		return self.__encoding

	def getblocksize(self):
		return self.__blocksize

	def getfpb(self):
		return self.__fpb

class AudioFormatLinear(AudioFormat):
	def __init__(self, name, descr, channels, encoding,
		     blocksize, fpb, bps):
		AudioFormat.__init__(self, name, descr, channels, encoding,
				     blocksize, fpb)
		self.__bps = bps

	def getbps(self):
		return self.__bps

ulaw_mono = AudioFormat(
	'ulaw_mono',
	'U-law, mono',
	[mono],
	'u-law',
	blocksize = 1,
	fpb = 1)
ulaw_stereo = AudioFormat(
	'ulaw_stereo',
	'U-law, stereo, left channel first',
	[left, right],
	'u-law',
	blocksize = 2,
	fpb = 1)

dvi_mono = AudioFormat(
	'dvi_mono',
	'DVI ADPCM, mono',
	[mono],
	'dvi-adpcm',
	blocksize = 1,
	fpb = 2)
dvi_stereo = AudioFormat(
	'dvi_stereo',
	'DVI APDCM, stereo, left channel first',
	[left, right],
	'dvi-adpcm',
	blocksize = 2,
	fpb = 2)

linear_8_mono_signed = AudioFormatLinear(
	'linear_8_mono_signed',
	"linear, 8 bps, 2's complement, mono",
	[mono],
	'linear-signed',
	blocksize = 1,
	fpb = 1,
	bps = 8)
linear_8_mono_excess = AudioFormatLinear(
	'linear_8_mono_excess',
	'linear, 8 bps, excess-128, mono',
	[mono],
	'linear-excess',
	blocksize = 1,
	fpb = 1,
	bps = 8)
linear_16_mono_big = AudioFormatLinear(
	'linear_16_mono_big',
	'linear 16 bps, big-endian, mono',
	[mono],
	'linear-big',
	blocksize = 2,
	fpb = 1,
	bps = 16)
linear_16_mono_little = AudioFormatLinear(
	'linear_16_mono_little',
	'linear 16 bps, little-endian, mono',
	[mono],
	'linear-little',
	blocksize = 2,
	fpb = 1,
	bps = 16)
linear_8_stereo_signed = AudioFormatLinear(
	'linear_8_stereo_signed',
	"linear, 8 bps, 2's complement, stereo, left channel first",
	[left, right],
	'linear-signed',
	blocksize = 2,
	fpb = 1,
	bps = 8)
linear_8_stereo_excess = AudioFormatLinear(
	'linear_8_stereo_excess',
	"linear, 8 bps, excess-128, stereo, left channel first",
	[left, right],
	'linear-excess',
	blocksize = 2,
	fpb = 1,
	bps = 8)
linear_16_stereo_big = AudioFormatLinear(
	'linear_16_stereo_big',
	'linear 16 bps, big-endian, stereo, left channel first',
	[left, right],
	'linear-big',
	blocksize = 4,
	fpb = 1,
	bps = 16)
linear_16_stereo_little = AudioFormatLinear(
	'linear_16_stereo_little',
	'linear 16 bps, little-endian, stereo, left channel first',
	[left, right],
	'linear-little',
	blocksize = 4,
	fpb = 1,
	bps = 16)

import struct
x = struct.unpack('h', '\x12\x34')[0]
if x == 0x1234:
	endian = 'big'
else:
	endian = 'little'
del x, struct

if endian == 'big':
	linear_16_stereo = linear_16_stereo_big
	linear_16_mono = linear_16_mono_big
else:
	linear_16_stereo = linear_16_stereo_little
	linear_16_mono = linear_16_mono_little
