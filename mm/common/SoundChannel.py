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


import posix
from stat import ST_SIZE
import string


# Don't import 'al' here; this makes it possible to use the CMIF editor
# on workstations without audio, as long as the document has no sound...
import AL
import aiff


from MMExc import *
import MMAttrdefs

from Channel import Channel


class SoundChannel() = Channel():
	#
	# Declaration of attributes that are relevant to this channel,
	# respectively to nodes belonging to this channel.
	#
	chan_attrs = []
	node_attrs = ['file']
	#
	def init(self, (name, attrdict, player)):
		self = Channel.init(self, (name, attrdict, player))
		self.info = self.prep = None
		self.rate = 0.0
		return self
	#
	def getduration(self, node):
		# NB This never uses the 'duration' attribute!
		filename = self.getfilename(node)
		try:
			return getduration(filename)
		except:
			print 'cannot get duration for sound file ' + filename
			return 0.0
	#
	def play(self, (node, callback, arg)):
		filename = self.getfilename(node)
		try:
			self.info = getinfo(filename)
			self.prep = prepare(self.info)
		except '':
			self.info = self.prep = None
			print 'cannot open sound file ' + filename
			callback(arg)
			return
		self.framestodo = self.info[2] # nsampframes
		self.qid = \
		    self.player.enter(0.001, 0, self._poll, (callback, arg))
	#
	def _poll(self, cb_arg):
		self.qid = None
		f, nchannels, nsampframes, sampwidth, samprate, format = \
			self.info
		port, offset, blocksize = self.prep
		framewidth = nchannels * sampwidth
		sampspersec = nchannels * samprate
		#fillable = port.getfillable()
		FRAC = 0.1 # Fraction of a second to read at once
		while self.framestodo > 0 and \
				port.getfillable() >= FRAC*sampspersec:
			# Read another FRAC sec of sound and send it
			framestofill = \
			    min(int(FRAC*sampspersec), self.framestodo)
			nbytes = framestofill * framewidth
			data = f.read(nbytes)
			if len(data) < nbytes:
				print 'short read from sound file'
			if data = '':
				self.framestodo = 0
			else:
				self.framestodo = self.framestodo - \
					len(data) / framewidth
				# XXX hope it's a whole multiple...
			if self.rate > 1.0:
				# Use only part of the data when
				# playing at high speed.
				todo = int(len(data)/self.rate)
				# Round down to whole number of frames!
				todo = (todo / framewidth) * framewidth
				data = data[:todo]
			port.writesamps(data)
		if self.framestodo + port.getfilled() > 0:
			self.qid = \
				self.player.enter(0.1, 0, self._poll, cb_arg)
		else:
			self.stop()
			callback, arg = cb_arg
			callback(arg)
	#
	def setrate(self, rate):
		self.rate = rate
	#
	def stop(self):
		if self.prep <> None:
			port, offset, blocksize = self.prep
			port.closeport()
			restore()
			self.info = self.prep = None
		if self.qid <> None:
			self.player.cancel(self.qid)
			self.qid = None
	#
	def reset(self):
		pass
	#
	# Internal methods.
	#
	def getfilename(self, node):
		# XXX Doesn't use self...
		if node.type = 'imm':
			return string.join(node.GetValues())
		elif node.type = 'ext':
			return MMAttrdefs.getattr(node, 'file')
	#


def getduration(filename):
	f, nchannels, nsampframes, sampwidth, samprate, format = \
		getinfo(filename)
	duration = nsampframes / samprate
	return duration


def getinfo(filename):
	f = open(filename, 'r')
	magic = f.read(4)
	# Look for AIFF header as produced by recordaiff
	if magic = 'FORM':
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
		if magic = '0008':
			samprate = 8000.0
		elif magic = '0016':
			samprate = 16000.0
		elif magic = '0032':
			samprate = 32000.0
		else:
			# Assume old-fashioned file without header
			samprate = 8000.0
			offset = 0
		st = posix.stat(filename)
		size = st[ST_SIZE]
		nchannels = 1
		sampwidth = 1
		nsampframes = size - offset
		format = ''
	#
	return f, nchannels, nsampframes, sampwidth, samprate, format


def prepare(f, nchannels, nsampframes, sampwidth, samprate, format):
	import al
	if format = 'FORM':
		type, size = aiff.read_chunk_header(f)
		if type <> 'SSND':
			raise aiff.Error, 'no SSND header where expected'
		offset, blocksize = aiff.read_ssnd_chunk(f)
	else:
		offset, blocksize = 0, 0
	# Set sampling rate (can't be done at the port level)
	# First get the new old sampling rate for restore()
	al.getparams(AL.DEFAULT_DEVICE, sound_params)
	pv = [AL.OUTPUT_RATE, int(samprate)]
	al.setparams(AL.DEFAULT_DEVICE, pv)
	# Compute queue size such that it can contain QSECS seconds of sound.
	# Making it larger reduces the risk of running out of data,
	# but increases the response time for pause commands.
	QSECS = 0.3
	queuesize = int(samprate * nchannels * QSECS)
	# Create a config object
	config = al.newconfig()
	config.setchannels(nchannels)
	config.setwidth(sampwidth)
	config.setqueuesize(queuesize)
	# Create a port object
	port = al.openport('SoundChannel', 'w', config)
	# The file is positioned at the start of the sample,
	# but the first 'offset' bytes must be skipped.
	return port, offset, blocksize


# Save sound channel parameters for restore()
#
sound_params = [AL.OUTPUT_RATE, 0]


# Restore sound channel parameters
#
def restore():
	if sound_params[1] <> 0:
		import al
		al.setparams(AL.DEFAULT_DEVICE, sound_params)
