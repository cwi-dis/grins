# SGI image library interface

# This now uses caching.
# For now, the cache assumes that you don't modify the files.
# If that is a problem, it should be fixed by recording the mtime
# of files with the cached value -- NOT by telling the users to
# avoid modifying files.  (For now I'm just lazy.)

# TO CONVERVE SPACE IN /usr/tmp, THE MAIN PROGRAM MUST CALL
# zapcache() when it is done!

import sys, posix, path, string, tempfile

ISTAT = '/usr/sbin/istat'
HERE = '/ufs/guido/mm/demo/mm4/'
SHOWIMG = HERE + 'showimg'
PREPIMG = HERE + 'prepimg'
SHOWPREP = HERE + 'showprep'
TMPDIR = '/usr/tmp'

cache = {}

def cachefile(file):
	if cache.has_key(file) and path.exists(cache[file]):
		return cache[file]
	tmpfile = tempfile.mktemp()
	# Put the entry in the cache before running the command,
	# so zapcache will remove halfway-finined entries
	cache[file] = tmpfile
	sts = posix.system(PREPIMG + ' ' + file + ' ' + tmpfile)
	if sts:
		try:
			posix.unlink(tmpfile)
			del cache[file]
		except posix.error:
			pass
		raise RuntimeError, 'file caching failed'
	return cache[file]

def zapcache():
	for file in cache.keys():
		try:
			posix.unlink(cache[file])
			del cache[file]
		except posix.error:
			pass

statcache = {}

def istat(filename):
	if statcache.has_key(filename):
		return statcache[filename]
	p = posix.popen(ISTAT + ' ' + filename, 'r')
	dummy = p.readline()
	line = p.readline()
	if not line:
		raise IOError, 'bad file for istat: ' + filename
	w = string.split(line)
	# xsize, ysize, zsize, min, max, bpp, type, storage, name
	statcache[filename] = retval = \
		eval(w[0]), eval(w[1]), eval(w[2]), \
		eval(w[3]), eval(w[4]), eval(w[5]), \
		w[6], w[7], w[8]
	return retval

def imgsize(filename):
	return istat(filename)[:2]

class _showimg:
	def init(self, (filename, xy)):
		tempname = cachefile(filename)
		cmd = 'exec ' + SHOWPREP + ' ' + tempname
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
	zapcache()
