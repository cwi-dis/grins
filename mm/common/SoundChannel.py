# Sound channel
#
# This doesn't have its own control window; use "apanel" instead.
#
# We assume AIFF sound files have a limited format:
# - one FORM chunk, containing:
#	- the AIFF id
#	- one COMM chunk
#	- one SSND chunk followed by all data
#
# We also support sound files created by our tools on the 4D/25.


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

from Channel import Channel

class csfile():
	def open(self, fname, mode):
		self.cached = ''
		self.f = open(fname, mode)
		return self

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
			

class SoundChannel(Channel):
	#
	# Declaration of attributes that are relevant to this channel,
	# respectively to nodes belonging to this channel.
	#
	chan_attrs = ['visible']
	node_attrs = ['file', 'arm_duration']
	#
	def init(self, (name, attrdict, player)):
		self = Channel.init(self, name, attrdict, player)
		self.info = self.port = None
		self.rate = 0.0
		self.cancelled_qid = 0
		self.armed_node = None
		self.armed_info = None
		return self
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
			self.armed_info = getinfo(filename)
			prepare(self.armed_info)	# Do a bit of readahead
		except IOError:
			self.armed_info = None
			print 'cannot open sound file ' + filename
			return
		self.armed_node = node
		
	def play(self, (node, callback, arg)):
		if not self.is_showing():
			#callback(arg)
			# XXX Try by Jack to get Guido's timing model:
			self.player.enter(node.t1-node.t0, 0,  callback, arg)
			return
		if self.armed_node <> node:
			print 'SoundChannel: not the armed node'
			self.arm(node)
			
		if not self.armed_info:		# If the arm failed...
			callback(arg)
			return

		self.old_info = self.info
		self.info = self.armed_info
		
		self.armed_node = None
		self.armed_info = None
		
		self.framestodo = self.info[2] # nsampframes
		if self.port == None or self.old_info[1] <> self.info[1] \
			  or self.old_info[3] <> self.info[3] \
			  or self.old_info[4] <> self.info[4]:
			self.port, self.config = openport(self.info)
	        dummy = self.player.enter(0.001, 0, self._poll, (callback, arg))
		dummy = self.player.enter(0.001, 1, self.player.opt_prearm, node)
	#
	def readsamples(self, f, nsamples, width, chunk):
		data = f.read(nsamples*width)
		if len(data) < nsamples*width:
			print 'short read from sound file, got', len(data), \
				  'wanted',nsamples*width
		if self.rate > 1.0:
			ndata = ''
			while len(data):
				ndata = ndata + data[:int(chunk)*width]
				data = data[int(chunk*self.rate)*width:]
			data = ndata
		return data		
			
	def _poll(self, cb_arg):
		self.cb_arg = cb_arg
		self.qid = None
		f, nchannels, nsampframes, sampwidth, samprate, format = \
			self.info
		framewidth = nchannels * sampwidth
		sampspersec = nchannels * samprate
		framestofill = min(self.port.getfillable(), self.framestodo)
		data = self.readsamples(f, framestofill, framewidth, sampspersec/30)
		if self.showing:
			self.port.writesamps(data)
		else:
			self.port.writesamps('\0'*len(data))
		self.framestodo = self.framestodo - framestofill
		duration = self.port.getfilled()/float(sampspersec)
		duration = duration - 0.5
		duration = max(duration, 0.2)
		if self.framestodo + self.port.getfilled() > 0:
			self.qid = self.player.enter(duration, 0, \
				  self._poll, cb_arg)
		else:
			self.stop()
			callback, arg = cb_arg
			callback(arg)

	def unfill(self):
		import al
		f, nchannels, nsampframes, sampwidth, samprate, format = \
			self.info
		port = self.port
		filled = int(port.getfilled() * self.rate)
		port.closeport()
		self.framestodo = self.framestodo + filled
		self.port = al.openport('SoundChannel', 'w', self.config)
		f.seek(-filled*nchannels*sampwidth, 1)
		
	#
	def setrate(self, rate):
		if self.qid:
			self.unfill()		
			self.player.cancel(self.qid)
			self.qid = None
			self.cancelled_qid = 1
		self.rate = rate
		if self.rate and self.cancelled_qid:
			self.qid = self.player.enter(0, 0, self._poll, self.cb_arg)
			self.cancelled_qid = 0
	#
	def stop(self):
		if (self.port <> None and self.armed_info == None) or self.qid:
			self.port.closeport()
			restore()
			self.info = self.port = None
		if self.qid <> None:
			self.player.cancel(self.qid)
			self.qid = None
		self.cancelled_qid = 0
	#
	def reset(self):
		pass
	#
	# Internal methods.
	#
	def getfilename(self, node):
		return MMAttrdefs.getattr(node, 'file')
	#


def getduration(filename):
	f, nchannels, nsampframes, sampwidth, samprate, format = \
		getinfo(filename)
	duration = nsampframes / samprate
	return duration


def getinfo(filename):
	f = csfile().open(filename, 'r')
	magic = f.read(4)
	# Look for AIFF header as produced by recordaiff
	if magic == 'FORM':
		totalsize = aiff.read_long(f)
		aiff.read_form_chunk(f)
		type, size = aiff.read_chunk_header(f)
		if type <> 'COMM':
			raise aiff.Error, 'no COMM chunk where expected'
		nchannels, nsampframes, sampwidth, samprate = \
			aiff.read_comm_chunk(f)
		sampwidth = sampwidth / 8 # Convert to bytes now
		format = 'FORM'
	else:
		# Look for old-fashioned header
		offset = 4
		if magic == '0008':
			samprate = 8000.0
		elif magic == '0016':
			samprate = 16000.0
		elif magic == '0032':
			samprate = 32000.0
		else:
			# Assume old-fashioned file without header
			samprate = 8000.0
			offset = 0
		st = os.stat(filename)
		size = st[ST_SIZE]
		nchannels = 1
		sampwidth = 1
		nsampframes = size - offset
		format = ''
	#
	return f, nchannels, nsampframes, sampwidth, samprate, format

def prepare(f, nchannels, nsampframes, sampwidth, samprate, format):
	if format == 'FORM':
		type, size = aiff.read_chunk_header(f)
		if type <> 'SSND':
			raise aiff.Error, 'no SSND header where expected'
		offset, blocksize = aiff.read_ssnd_chunk(f)
	else:
		offset, blocksize = 0, 0
	# For unknown reasons you get a queue that is bigger than you ask
	# for. For that reason, we read a little more ahead
	f.readahead(MAXQSIZE*sampwidth*nchannels)

def openport(f, nchannels, nsampframes, sampwidth, samprate, format):
	import al
	# Set sampling rate (can't be done at the port level)
	# First get the new old sampling rate for restore()
	al.getparams(AL.DEFAULT_DEVICE, sound_params)
	pv = [AL.OUTPUT_RATE, int(samprate)]
	al.setparams(AL.DEFAULT_DEVICE, pv)
	# Compute queue size such that it can contain QSECS seconds of sound,
	# but it shouldn't be bigger than 100K
	QSECS = 10.0
	queuesize = int(min(samprate * nchannels * QSECS, MAXQSIZE))
	# Create a config object
	config = al.newconfig()
	config.setchannels(nchannels)
	config.setwidth(sampwidth)
	config.setqueuesize(queuesize)
	# Create a port object
	port = al.openport('SoundChannel', 'w', config)
	# XXXX Comment by Guido, unintellegible by Jack (and not true in the
	# XXXX source code):
	# The file is positioned at the start of the sample,
	# but the first 'offset' bytes must be skipped.
	return port, config


# Save sound channel parameters for restore()
#
sound_params = [AL.OUTPUT_RATE, 0]


# Restore sound channel parameters
#
def restore():
	if sound_params[1] <> 0:
		import al
		al.setparams(AL.DEFAULT_DEVICE, sound_params)


# Cache durations

import FileCache
duration_cache = FileCache.FileCache().init(getduration)
