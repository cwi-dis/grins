import sys, img, imgformat

def main():
	if len(sys.argv) != 2:
		print 'Usage:',sys.argv[0] or 'python mksplash.py','img-file'
		sys.exit(1)
	rdr = img.reader(imgformat.rgb, sys.argv[1])
	width = rdr.width
	height = rdr.height
	data = rdr.read()
	f = open('splashimg.py', 'w')
	f.write('''\
__version__ = "$Id$"

import imgformat, base64

class reader:
	def __init__(self):
		self.width = %(width)d
		self.height = %(height)d
		self.format = imgformat.rgb
		self.format_choices = (imgformat.rgb,)

	def read(self):
		return ''' % vars())
	f.write("'''\\\n")
	n = 0
	for i in xrange(len(data)):
		c = data[i]
		if c >= '\200':
			c = '\\%03o' % ord(c)
		elif c == "'":
			c = "\\'"
		elif c == '\\':
			c = '\\\\'
		elif c >= ' ':
			c = c
		elif c == '\n':
			c = '\\n'
		elif c == '\f':
			c = '\\f'
		elif c == '\b':
			c = '\\b'
		elif c == '\t':
			c = '\\t'
		elif c == '\r':
			c = '\\r'
		else:
			nc = data[i+1:i+2]
			if '0' <= nc <= '7':
				c = '\\%03o' % ord(c)
			else:
				c = '\\%o' % ord(c)
		f.write(c)
		n = n + len(c)
		if n >= 72:
			f.write('\\\n')
			n = 0
	f.write("'''\n")

main()
