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

MAXQSIZE = 100*1024		# Max audio-queue size=100K

from MMExc import *
import MMAttrdefs

from Channel import Channel
		

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
	def init(self, name, attrdict, scheduler, ui):
		self = Channel.init(self, name, attrdict, scheduler, ui)
		self.info = self.port = None
		self.rate = 0.0
		self.cancelled_qid = 0
		self.armed_node = None
		self.armed_info = None
		self.skipped_arm = 0
		self.node = None
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
		import SoundDuration
		filename = self.getfilename(node)
		try:
			return SoundDuration.get(filename)
		except IOError:
			print 'cannot open sound file to get duration:',
			print `filename`
			return MMAttrdefs.getattr(node, 'duration')
	#
	def arm(self, node):
		import SoundDuration
		if not self.is_showing():
			self.skipped_arm = 1
			return
		filename = self.getfilename(node)
		try:
			import glwindow, mm
			glwindow.devregister(`self.deviceno`+':'+`mm.armdone`,\
				  armdone, 0)
			glwindow.devregister(`self.deviceno`+':'+`mm.stopped`,\
				  stopped, 0)
			self.armed_info = SoundDuration.getinfo(filename)
			prepare(self.armed_info)	# Do a bit of readahead
			f, nchannels, nsampframes, sampwidth, samprate, format = self.armed_info
##			print 'SoundChannel.arm: self.threads = ' + `self.threads`
			self.threads.arm(f, 0, 0, \
				  {'nchannels': int(nchannels), \
				   'nsampframes': int(nsampframes), \
				   'sampwidth': int(sampwidth), \
				   'samprate': int(samprate), \
				   'format': format, \
				   'offset': int(f.tell())}, \
				  None)
		except IOError:
			self.armed_info = None
			print 'cannot open sound file ' + filename
			return
		self.armed_node = node

	def did_prearm(self):
		return (self.armed_node <> None) or self.skipped_arm
		
	def play(self, node, callback, arg):
		self.node = node
		self.cb = (callback, arg)
		self.skipped_arm = 0

		if not self.is_showing():
			# Don't play it, but still let the duration pass
			import Duration

			self.armed_node = None
			self.armed_info = None
			duration = Duration.get(node)
			dummy = self.scheduler.enter(duration, 0, \
				self.done, None)
			return


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
		self.threads.play()
		self.scheduler.arm_ready(self.name)
	#
	#DEBUG: remove dummy entry from queue and call proper done method
	def done(self, arg):
		if not self.node:
			# apparently someone has already called stop()
			return
		Channel.done(self, arg)
		self.node = None
		
	#
	def setrate(self, rate):
##		print 'SoundChannel.setrate: self.threads = ' + `self.threads`
		self.threads.setrate(rate)
	#
	def stop(self):
##		print 'SoundChannel.stop: self.threads = ' + `self.threads`
		if self.node:
			self.node = None
			self.threads.stop()
	#
	def reset(self):
		pass
	#
	# Internal methods.
	#
	def getfilename(self, node):
		return aiffcache.get(Channel.getfilename(self, node))
	#
	def destroy(self):
##		print 'SoundChannel.destroy: self.threads = ' + `self.threads`
		self.threads.close()
		self.threads = None
		Channel.destroy(self)


def prepare((f, nchannels, nsampframes, sampwidth, samprate, format)):
	pass



# External interface to restore the original sampling rate.
# This must work even when called from a "finally" handler in main().
# (Now abused to just clean up the aiff temporary file cache.)
#
def restore():
	cleanup()


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

import FileCache
aiffcache = FileCache.FileCache().init(makeaiff, rmcache)
