#
# Midi channel
#
# XXXX Misses PLAYDONE handling.
#
import os
debug = os.environ.has_key('CHANNELDEBUG')
from Channel import Channel
import string
import os
import windowinterface
import sys
import select

sys.path.append('/ufs/jack/src/python/Extensions/midi/build.irix5')
sys.path.append('/ufs/jack/src/python/Extensions/midi/Lib')
try:
    import sgimidi
    import midi
    import midifile
    import MIDIevents
    import MIDInames
    import SGIMIDI
except ImportError:
    sgimidi = None
    midi = None
    midifile = None
    
class MidiChannel(Channel):
	def __init__(self, name, attrdict, scheduler, ui):
		Channel.__init__(self, name, attrdict, scheduler, ui)
		self.port = None
		self.arm_data = []
		self.play_data = []
		self.has_callback = 0

	def __repr__(self):
		return '<MidiChannel instance, name=' + `self._name` + '>'

	def _openport(self):
	        if self.port:
		    return 1
		if not sgimidi:
		    print 'Error: Midi not available'
		    return 0
		self.cfg = sgimidi.newconfig()
##		cfg.setparams([SGIMIDI.MI_STAMPING, SGIMIDI.MIDELTASTAMP,
##			       SGIMIDI.MI_BLOCKING, SGIMIDI.MINONBLOCKING])
		self.cfg.setparams([SGIMIDI.MI_STAMPING, SGIMIDI.MIRELSTAMP])
		self.port = sgimidi.openport('w', self.cfg)
		return 1

	def do_arm(self, node, same=0):
	        if not self._openport():
		    return 1
		if node.type != 'ext':
		    self.errormsg(node, 'Node must be external')
		    return 1
		if same and self.arm_data:
		    return 1
		fn = self.getfilename(node)
		#
		# Read the midifile, mixing all tracks
		#
		try:
		    fp = open(fn, 'rb')
		except IOError:
		    print 'Cannot open midi file', fn
		    self.armed_data = []
		    self.armed_duration = 0
		    return
		mf = midifile.MidiInputFile(fp)
		reader = midi.MixerSource(mf.tracks)

		list = []
		tempo = 810810
		tc_lost = 0

		total_time = 0
		while 1:
		    try:
			tc, ev, args = reader.get_event()
		    except EOFError:
			break
		    tc = (float(tc)/mf.division) * tempo/1000000.0

		    if ev == MIDIevents.MF_TEMPO:
			tempo = args[0]
			tc_lost = tc_lost + tc
		    elif MIDInames.ismeta(ev) or ev == MIDIevents.SEX:
			tc_lost = tc_lost + tc
		    else:
			tc = tc + tc_lost
			tc_lost = 0
			total_time = total_time + tc
			list.append(total_time, ev, args)
		self.arm_data = list
		self.armed_duration = total_time
		return 1

	def install_callback(self):
	    if self.has_callback or not self.port: return
	    windowinterface.select_setcallback(self.port, self._playsome,
					       (), 2)
	    self.has_callback = 1
	    
	def unstall_callback(self):
	    if not self.has_callback or not self.port: return
	    windowinterface.select_setcallback(self.port, None, (), 2)
	    self.has_callback = 0
	    
	def _playsome(self):
	        i = 0
		if debug:
		    print 'Midichannel: events to do:', len(self.play_data)
		while i < len(self.play_data):
		    d1, ok, d2 = select.select([], [self.port], [], 0)
		    if ok == [self.port]:
			self.port.send([self.play_data[i]])
		    else:
			break
		    i = i + 1
		if debug:
		    print 'Midichannel: did', i, 'of', len(self.play_data)
		del self.play_data[:i]
		if not self.play_data:
		    self.unstall_callback()
		    
	def do_play(self, node):
	        if not self.port:
		    return
	        self.play_data = self.arm_data
		self.arm_data = []
		self.install_callback()
		self._playsome()

	def playstop(self):
	        if not self.port:
		    return
		if debug: print 'MidiChannel: playstop'
		self.unstall_callback()
		self.data = []
		Channel.playstop(self)

	def setpaused(self, paused):
	    if paused:
		self.unstall_callback()
	    else:
		self.install_callback()
	    Channel.setpaused(self, paused)
	    
