__version__ = "$Id$"

import imgformat
import struct

_bigendian = struct.pack('i', 1)[0] == '\0'

class reader:
	def __init__(self):
		self.width = 16
		self.height = 16
		format = imgformat.colormap
		self.format = format
		self.format_choices = (format,)
		import imgcolormap
		if _bigendian:
			self.colormap = imgcolormap.new('''\
\0\1\1\1\0\0\0\377\0\0\377\377\0\4\4\4''')
		else:
			self.colormap = imgcolormap.new('''\
\1\1\1\0\377\0\0\0\377\377\0\0\4\4\4\0''')
		self.transparent = 0
		self.top = 0
		self.left = 0
		self.aspect = 0

	def read(self):
		return '''\
\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\
\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\
\0\0\0\0\0\0\0\0\0\0\0\0\0\0\3\3\3\3\3\0\0\0\0\0\0\0\0\0\0\3\1\2\1\2\1\3\
\0\0\0\0\0\0\0\0\0\3\2\1\2\1\2\3\0\0\0\0\0\0\0\0\0\3\1\2\1\2\1\3\0\0\0\0\
\0\0\0\0\0\3\2\1\2\1\2\3\0\0\0\0\0\0\0\0\0\3\1\2\1\2\1\3\0\0\0\0\0\0\0\0\
\0\0\3\3\3\3\3\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\
\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\
\0\0\0\0'''
