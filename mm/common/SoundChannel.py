# Sound channel
#
# This doesn't have its own control window; use "apanel" instead.
#
# We assume AIFF sound files have a limited format:
# - one FORM chunk, containing:
#	- the AIFF id
#	- one COMM chunk
#	- one SSND chunk followed by all data


import os
from stat import ST_SIZE
import string


# Don't import 'al' here; this makes it possible to use the CMIF editor
# on workstations without audio, as long as the document has no sound...
import AL
import aiff

MAXQSIZE = 100*1024		# Max audio-queue size=100K

from MMExc import *
import MMAttrdefs
from ArmStates import *

from Channel import Channel

class csfile:
	def open(self, fname, mode):
		self.cached = ''
		self.f = open(fname, mode)
		return self

	def __repr__(self):
		return '<csfile instance, f=' + `self.f` + '>'

	def seek(self, arg):
		self.cached = ''
		return self.f.seek(arg)

	def read(self, n):
		if n <= len(self.cached):
			rv = self.cached[:n]
			self.cached = self.cached[n:]
			self.f.seek(n, 1)
			return rv
		if self.cached:
			rv1 = self.cached
			self.cached = ''
			self.f.seek(len(rv1),1)
			return rv1 + self.read(n-len(rv1))
		self.cached = ''
		return self.f.read(n)

	def readahead(self, n):
		self.cached = self.f.read(n)
		self.f.seek(-len(self.cached), 1)

	def close(self):
		self.f.close()
			

def armdone(arg):
	pass
def stopped(arg):
	pass

class SoundChannel(Channel):
	#
	# Declaration of attributes that are relevant to this channel,
	# respectively to nodes belonging to this channel.
	#
	chan_attrs = []
	node_attrs = ['file']
	#
	def init(self, (name, attrdict, player)):
		self = Channel.init(self, name, attrdict, player)
		self.info = self.port = None
		self.rate = 0.0
		self.cancelled_qid = 0
		self.armed_node = None
		self.armed_info = None
		self.node = None
		#DEBUG: to spoof Jack's scheduler
		self.dummy_event_id = None
		import mm, soundchannel
		self.threads = mm.init(soundchannel.init(), \
			  0, self.deviceno, None)
##		print 'SoundChannel.init: self.threads = ' + `self.threads`
		return self
	#
	def __repr__(self):
		return '<SoundChannel instance, name=' + `self.name` + '>'
	#
	def getduration(self, node):
		# NB This never uses the 'duration' attribute!
		filename = self.getfilename(node)
		try:
			return duration_cache.get(filename)
		except IOError:
			print 'cannot get duration for sound file ' + filename
			return MMAttrdefs.getattr(node, 'duration')
	#
	def arm(self, node):
		if not self.is_showing():
			return
		filename = self.getfilename(node)
		try:
			import glwindow, mm
			glwindow.devregister(`self.deviceno`+':'+`mm.armdone`,\
				  armdone, 0)
			glwindow.devregister(`self.deviceno`+':'+`mm.stopped`,\
				  stopped, 0)
			self.armed_info = getinfo(filename)
			prepare(self.armed_info)	# Do a bit of readahead
			f, nchannels, nsampframes, sampwidth, samprate, format = self.armed_info
##			print 'SoundChannel.arm: self.threads = ' + `self.threads`
			self.threads.arm(f.f, 0, 0, \
				  {'nchannels': int(nchannels), \
				   'nsampframes': int(nsampframes), \
				   'sampwidth': int(sampwidth), \
				   'samprate': int(samprate), \
				   'format': format, \
				   'offset': int(f.f.tell())}, \
				  None)
		except IOError:
			self.armed_info = None
			print 'cannot open sound file ' + filename
			return
		self.armed_node = node
		
	def play(self, (node, callback, arg)):
		self.node = node
		self.cb = (callback, arg)
		self.dummy_event_id = None

		if not self.is_showing():
			# Don't play it, but still let the duration pass
			dummy = self.player.enter(node.t1-node.t0, 0, \
				self.done, None)
			return

		node.setarmedmode(ARM_PLAYING)

		if self.armed_node <> node:
			print 'SoundChannel: not the armed node'
			self.arm(node)
			
		if not self.armed_info:		# If the arm failed...
			self.done(None)
			return

		self.old_info = self.info
		self.info = self.armed_info
		
		self.armed_node = None
		self.armed_info = None
		
##		print 'SoundChannel.play: self.threads = ' + `self.threads`
		import glwindow, mm
		glwindow.devregister(`self.deviceno`+':'+`mm.playdone`, \
			  self.done, None)
		glwindow.devregister(`self.deviceno`+':'+`mm.stopped`, \
			  stopped, 0)
		#DEBUG: enter something in queue to fool scheduler
		self.dummy_event_id = self.player.enter(1000000, 1, self.done, None)
		self.threads.play()
		dummy = \
		   self.player.enter(0.001, 1, self.player.opt_prearm, node)
	#DEBUG: remove dummy entry from queue and call proper done method
	def done(self, arg):
		if self.dummy_event_id:
			try:
				self.player.cancel(self.dummy_event_id)
			except ValueError:
				# probably already removed by someone else
				pass
			self.dummy_event_id = None
		if not self.node:
			# apparantly someone has already called stop()
			return
		Channel.done(self, arg)
		
	#
	def setrate(self, rate):
##		print 'SoundChannel.setrate: self.threads = ' + `self.threads`
		self.threads.setrate(rate)
	#
	def stop(self):
		if self.node:
			self.node.setarmedmode(ARM_DONE)
			self.node = None
##		print 'SoundChannel.stop: self.threads = ' + `self.threads`
		self.threads.stop()
	#
	def reset(self):
		pass
	#
	# Internal methods.
	#
	def getfilename(self, node):
		return aiffcache.get(MMAttrdefs.getattr(node, 'file'))
	#
	def destroy(self):
##		print 'SoundChannel.destroy: self.threads = ' + `self.threads`
		self.threads = None
		Channel.destroy(self)

def getduration(filename):
	f, nchannels, nsampframes, sampwidth, samprate, format = \
		getinfo(filename)
	duration = float(nsampframes) / samprate
	return duration


def getinfo(filename):
	f = csfile().open(filename, 'r')
	try:
		a = aiff.Aiff().init(f, 'rf')
	except EOFError:
		print 'EOF on sound file', filename
		return f, 1, 0, 1, 8000, 'eof'
	except aiff.Error, msg:
		print 'error in sound file', filename, ':', msg
		return f, 1, 0, 1, 8000, 'error'
	return f, a.nchannels, a.nsampframes, a.sampwidth, a.samprate, 'AIFF'

def prepare(f, nchannels, nsampframes, sampwidth, samprate, format):
	pass



# External interface to restore the original sampling rate.
# This must work even when called from a "finally" handler in main().
# (Now abused to just clean up the aiff temporary file cache.)
#
def restore():
	cleanup()


# Cache durations

import FileCache

duration_cache = FileCache.FileCache().init(getduration)


# Cache conversions to AIFF files

import pipes

toaiff = {}

t = pipes.Template().init()
t.append('sox -t au - -t aiff -r 8000 -', '--')
toaiff['au'] = t

t = pipes.Template().init()
t.append('sox -t hcom - -t aiff -r 22050 -', '--')
toaiff['hcom'] = t

t = pipes.Template().init()
t.append('sox -t voc - -t aiff -r 11025 -', '--')
toaiff['voc'] = t

t = pipes.Template().init()
t.append('sox -t wav - -t aiff -', '--')
toaiff['wav'] = t

t = pipes.Template().init()
t.append('sox -t 8svx - -t aiff -r 16000 -', '--')
toaiff['8svx'] = t

t = pipes.Template().init()
t.append('sox -t sndt - -t aiff -r 16000 -', '--')
toaiff['sndt'] = t

t = pipes.Template().init()
t.append('sox -t sndr - -t aiff -r 16000 -', '--')
toaiff['sndr'] = t

uncompress = pipes.Template().init()
uncompress.append('uncompress', '--')

temps = []

def makeaiff(filename):
	import sndhdr
	import tempfile
	import os
	compressed = 0
	if filename[-2:] == '.Z':
		temp = tempfile.mktemp()
		temps.append(temp)
		sts = uncompress.copy(filename, temp)
		if sts:
			print 'uncompress of', filename, 'failed.'
			return filename
		filename = temp
		compressed = 1
	try:
		type = sndhdr.whathdr(filename)
		if type:
			type = type[0] # All we're interested in
	except IOError:
		type = None
	if type and toaiff.has_key(type):
		temp = tempfile.mktemp()
		temps.append(temp)
		sts = toaiff[type].copy(filename, temp)
		if sts:
			print 'conversion of', filename, 'failed.'
			return filename
		if compressed:
			os.unlink(filename)
			temps.remove(filename)
		filename = temp
	return filename

def rmcache(original, cached):
	if cached != original:
		try:
			os.unlink(cached)
		except os.error:
			pass

def cleanup():
	import os
	aiffcache.flushall()
	for tempname in temps:
		try:
			os.unlink(tempname)
		except (os.error, IOError):
			pass
	temps[:] = []

aiffcache = FileCache.FileCache().init(makeaiff, rmcache)
