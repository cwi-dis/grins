# SGI image library interface

import sys, posix, string

ISTAT = '/usr/sbin/istat'
SHOWIMG = './showimg' # Special version!

def istat(filename):
	p = posix.popen(ISTAT + ' ' + filename, 'r')
	dummy = p.readline()
	line = p.readline()
	if not line:
		raise RuntimeError, 'bad file for istat: ' + filename
	w = string.split(line)
	# xsize, ysize, zsize, min, max, bpp, type, storage, name
	return	eval(w[0]), eval(w[1]), eval(w[2]), \
		eval(w[3]), eval(w[4]), eval(w[5]), \
		w[6], w[7], w[8]

def imgsize(filename):
	return istat(filename)[:2]

class _showimg():
	def init(self, (filename, xy)):
		cmd = 'exec showimg ' + filename
		if xy:
			x, y = xy
			cmd = cmd + ' ' + `x` + ' ' + `y`
		self.pipe = posix.popen(cmd, 'r')
		line = self.pipe.readline()
		line = string.strip(line)
		self.pid = string.atoi(line)
		return self
	def kill(self):
		posix.kill(self.pid, 15)
		dummy = self.pipe.close()
		del self.pid, self.pipe

def showimg(filename, xy):
	return _showimg().init(filename, xy)

def test(filename):
	import time
	xsize, ysize = imgsize(filename)
	scrwidth, scrheight = 1280, 1024
	x = (scrwidth - xsize) / 2
	y = (scrheight - ysize) / 2
	#
	print 'Starting...'
	a = showimg(filename, (x, y))
	print 'Started; sleep 3 sec...'
	time.sleep(3)
	print 'Killing...'
	a.kill()
	print 'Done.'
