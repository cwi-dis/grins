# This module is a collection of useful functions for working with events.

import EventEditorDialog
import MMNode, windowinterface

# An event struct is a temporary representation of an event; it is intended to be used
 # with the dialog and is only passed between functions as a copy or representation of
# the event. It looks like the following:

# ( cause, event, extrainfo, offset)
# where cause is one of the CAUSES in the list below,
# event is one of the EVENTS in the list below,
# extrainfo depends on the event
# offset is an integer.

# This is the list of node clauses. Note that they are also hard-coded into
# win32/AttrEditForm.py

CAUSES = [				# What causes the event
	# This list is incomplete
	'delay',
	'indefinite',		       
	'node',				# extrainfo is a pointer to an MMNode or string??
	'region',			# extrainfo is a pointer or string repr a region.
	'prev',
	'accessKey',			# extrainfo is the key pressed.
	'marker',			# er.. I admit that I don't understand this.
	'wallclock',			# extrainfo is the time.
	# What else??
	]

# Reference: pg 401 of the SMIL printout on my desk; or chapter 13.3.12 (events)
EVENTS_NODE = [				# What the event actually is.
	'begin',
	'end',
	'repeat',			# what about it's integer argument??
	'click',
	'focusInEvent',
	'focusOutEvent',		# NO OFFSET!
	'activateEvent',
	'beginEvent',
	'endEvent',			
	'repeatEvent',			# NO OFFSET!
	]

EVENTS_REGION = [			# no offsets at all!
	'activateEvent',
	'focusInEvent',		# I'm not sure about these.
	'focusOutEvent',
	'inBoundsEvent',
	'outOfBoundsEvent',
	]

def syncarc2string(a):
	# This should really be in the MMSyncArc class.
	# This should also not be used. It needs to be fixed up a bit.
##	s = ['unknown event.']
##	if a.wallclock is not None:
##		yr,mt,dy,hr,mn,sc,tzsg,tzhr,tzmn = a.wallclock
##		if yr is not None:
##			date = '%04d-%02d-%02dT' % (yr, mt, dy)
##		else:
##			date = ''
##		time = '%02d:%02d:%05.2f' % (hr, mn, sc)
##		if tzhr is not None:
##			tz = '%s%02d:%02d' % (tzsg, tzhr, tzmn)
##		else:
##			tz = ''
##		s.append('wallclock(' + date + time + tz + ')')
##		continue
##	if a.marker is not None:
##		s.append('')
##		continue
##	if a.delay is None:
##		s.append('indefinite')
##		continue
##	if a.channel is not None:
##		s.append('')
##		continue
##	if a.accesskey is not None:
##		s.append('accesskey(%s)' % a.accesskey)
##		continue
##	if a.srcnode == 'syncbase':
##		s.append('%gs' % a.delay)
##	elif a.srcnode == 'prev':
##		s.append('prev.%s+%gs' % (a.event, a.delay))
##	else:
##		s.append('Yes, there is an event here, but I dont know what it is.')
##		continue
##	return s[0]
	return "This is an event."

def eventstruct2string(a):
	# Converts a event struct to a string.
	print "TODO."

def eventstruct2syncarc(a):
	# Creates a new syncarc given the information supplied in eventstruct.
	pass

def syncarc2eventstruct(a):
	# Converts the given syncarc into an event structure
	pass
	
def showeventeditor(syncarc):
	# Edits that specific syncarc.
	print "TODO - show event editor.", toplevel, syncarc

def newevent():
	# Pops up the window and returns a new syncarc (or None if the user cancels.)
	print "DEBUG: newevent not implemented", toplevel

class EventEditor(EventEditorDialog.EventEditorDialog):
	# This isn't a view - it's a modal dialog for an eventstruct
	# It lives as long as it's dialog box is showing.

	def __init__(self, parent=None):
		EventEditorDialog.EventEditorDialog.__init__(self, parent)
		# Map the resource id's. 
		#self.set_fields()

	def set_eventstruct(self, eventstruct):
		self._eventstruct = eventstruct

	def get_eventstruct(self):
		return self._eventstruct

#	def set_fields(self):
#		# Sets all the fields of this dialog to their values.
#		self._cause = "region"
#		self._event = "click"

##	def done(self):
##		# callback for when the user has finished.
##		# TODO: put all the instance variables back into the syncarc and return it (?)
##		print "Done."
##		return 1		# return 0 if you do not want to close the dialog.


class EventStruct:
	# This encapsulates an event.
	def __init__(self, syncarc):
		# if syncarc is None, make a new one. 
		self._syncarc = syncarc
		self.cause = None
		self.event = None
		self.delay = None
		self.thing = None
		self._setcause = None	# These variables (_setx) override the defaults and will be committed.
		self._setevent = None
		self._setoffset = None
		#self._setthing = None
		self._setnode = None
		self._setregion = None
		self._setkey = None
		self._setwallclock = None
		if self._syncarc:
			self.set_vars()
		else:
			self.set_cause('node')
			self.set_event('activateEvent')
			self.set_offset('0')

	def get_value(self):
		# Returns the result of editing this syncarc.
		if not self._syncarc:
			print "ERROR: this code is not complete. I can't find a node to make a syncarc on."
			assert 0
			# TODO: here, make a new syncarc.
		s = self._syncarc
		if self._setcause:
			c = self._setcause
			if c == 'indefinite':
				s.delay = None
			elif c == 'marker':
				print "TODO: marker code not written."
			elif c == 'prev':
				s.srcnode = 'prev'
			else:
				print "ERROR: unknown event cause."
		if self._setevent:
			s.event = self._setevent
		if self._setoffset:
			s.delay = int(self._setoffset)
		c = self.get_cause()
		if c == 'node' and self._setnode:
			print "TODO: don't know how to set node."
		elif c == 'region' and self._setregion:
			print "TODO: don't know how to set region."
		elif c == 'accessKey' and self._setkey:
			s.accesskey = self._setkey
		#elif c == '
		#
		return self._syncarc

	def set_vars(self):
		# Sets all the variables in this class.
		x = self._syncarc

		# The cause and the thing.
		if self.cause:
			assert 0
		elif x.delay is None:
			self.cause == 'indefinite'
		elif x.wallclock is not None:
			self.cause = 'wallclock'
			self.delay = None
			self.thing = x.wallclock
		elif x.accesskey is not None:
			self.cause = 'accessKey'
			self.thing = x.accesskey
		elif x.srcnode == 'prev':
			self.cause = 'prev'
			self.thing = None
		elif x.marker is not None:
			self.cause = 'marker'
			self.event = None
			self.thing = x.marker
		elif x.channel is not None:
			self.cause = 'region'
			self.thing = x.channel
		else:
			# TODO: more work needed here.
			self.cause = 'node'
			if isinstance(x.srcnode, MMNode.MMNode):
				self.thing = x.srcnode.GetName()
			else:
				self.cause = 'delay'
		# The event.
		if self.cause == 'node' or self.cause == 'region':
			self.event = x.event

	def as_string(self):
		# Must always return a string.
		c = self.get_cause()
		r = ""			# returnable value.
		s = self._syncarc
		if c == 'indefinite':
			return c
		elif c == 'marker':
			return "TODO: marker"	# TODO!!
		elif c == 'wallclock':
			return "TODO: wallclock"
		# Now for the offset things
		elif c == 'node':
			_, r, _, _ = self.get_thing_string()
			r = r + '.' + self.get_event()
			##if isinstance(s, MMNode.MMSyncArc):
##				if isinstance(s.srcnode, MMNode.MMNode):
##					r = s.srcnode.GetName() + "." + self.get_event()
##				else:
##					r = s.srcnode + "." + self.get_event()
##			else:
##				r = 'unknown'
		elif c == 'region':
			_, r, _, _ = self.get_thing_string()
			r = r + '.' + self.get_event()
##			if self._setregion:
##				r = self._setregion
##			elif isinstance(s, MMNode.MMSyncArc):
##				r = s.channel
##			else:
##				r = 'unknown'
		elif c == 'prev':
			if self._setevent:
				r = 'prev' + self._setevent
			elif isinstance(s, MMNode.MMSyncArc):
				r = 'prev' + "." + s.event
			else:
				r = 'prev'
		elif c == 'accessKey':
			if self._setkey:
				r = 'accessKey(' + self._setkey + ')'
			elif isinstance(self._syncarc, MMNode.MMSyncArc):
				r = 'accessKey(' + self._syncarc.accesskey + ')'
			else:
				r = 'accessKey(?)'
		elif c == 'delay':
			d = self.get_offset()
			if d:
				return "Delay of " + d
			else:
				print "Got strange looking event: ", self._syncarc
				return "Error: strange event."
		d = self.get_offset()
		if d == "0" or d is None:
			return r
		elif not d.startswith('-'):
			d = "+"+d
		return r+d
		
	def get_cause(self):
		if self._setcause:
			return self._setcause
		else:
			return self.cause
	def set_cause(self, newcause):
		self._setcause = newcause
	def get_event(self):
		if self._setevent:
			return self._setevent
		elif self.event.startswith('repeat'):
			# TODO: repeated times.
			return 'repeat'
		else:
			return self.event
	def get_event_index(self):
		# return the current event index from the list of possible events.
		e = self.get_event()
		if not e:
			return None
		else:
			try:
				return self.get_possible_events().index(e)
			except Exception:
				return None
	def set_event(self, newevent):
		self._setevent = newevent
	def get_possible_events(self):
		if self.get_cause() == 'node':
			return EVENTS_NODE
		elif self.get_cause() == 'region':
			return EVENTS_REGION
		else:
			return None
	def get_thing_string(self):
		# returns a tuple of (name string, value string, Bool isnumber, Bool readonly)
		# isnumber is if the string is a number.
		# readonly is if this should be editable in the dialog/
		c = self.get_cause()
		readonly = 0
		number = 0
		name = ""
		thing = ""
		if c == 'node':
			readonly = 1
			name = "Node:"
			if self._setnode:
				thing = self._setnode
			elif isinstance(self._syncarc, MMNode.MMSyncArc):
				thing = self._syncarc.srcnode.GetName()
			else:
				thing = "Unknown"
		elif c == 'region':
			print "TODO: display a region properly."
			name = "Region:"
			readonly = 1
			if self._setregion:
				thing = self._setregion
			elif isinstance(self._syncarc, MMNode.MMSyncArc):
				thing = self._syncarc.channel
			else:
				thing = "unknown"
			#return ("Region:", repr(self._syncarc.channel), 0, 0)
		elif c == 'accessKey':
			name = "Key:"
			if self._setkey:
				thing = self._setkey
			elif isinstance(self._syncarc, MMNode.MMSyncArc):
				thing = self._syncarc.accesskey
			else:
				thing = ""
			#return ("Key:", self._syncarc.accesskey, 0, 0)
		elif c == 'wallclock':
			name = "Wallclock:"
			if self._setthing:
				thing = self._setthing
			elif isinstance(self._syncarc, MMNode.MMSyncArc):
				thing = self._syncarc.wallclock
			else:
				thing = ""
			#return ("Clock time:", self._syncarc.wallclock, 0, 0)
		else:
			readonly = 1
			thing = ""
			name = ""
		return (name, thing, number, readonly)
	def set_thing_string(self, newthing):
		# TODO: do some sanity checking here.
		c = self.get_cause()
		if c == 'node':
			self._setnode = newthing
		elif c == 'region':
			self._setregion = newthing
		elif c == 'wallclock':
			self._setwallclock = newthing
		elif c == 'accessKey':
			self._setkey = newthing
		else:
			print "DEBUG: Unknown cause: ", c
		return None		# return an error otherwise.
	def get_offset(self):
		if self._setoffset:
			return self._setoffset
		if self._syncarc and self.get_cause() in ['node', 'prev', 'accessKey', 'delay']: # TODO: check these.
			return `self._syncarc.delay`
		else:
			return None
	def set_offset(self, newoffset):
		if newoffset.isdigit():
			self._setoffset = newoffset
			return 1
		else:
			return 0
