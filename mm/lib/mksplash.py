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
	f.write("'")
	for i in xrange(len(data)):
		c = data[i]
		if c >= '\200':
			f.write('\\%03o' % ord(c))
		elif c == "'":
			f.write("\\'")
		elif c == '\\':
			f.write('\\\\')
		elif c >= ' ':
			f.write(c)
		elif c == '\n':
			f.write('\\n')
		elif c == '\f':
			f.write('\\f')
		elif c == '\b':
			f.write('\\b')
		elif c == '\t':
			f.write('\\t')
		elif c == '\r':
			f.write('\\r')
		else:
			nc = data[i+1:i+2]
			if '0' <= nc <= '7':
				f.write('\\%03o' % ord(c))
			else:
				f.write('\\%o' % ord(c))
	f.write("'\n")

main()
