# This module is a collection of useful functions for working with events.

# TODO: the cancel button doesn't work yet.
# TODO: how do I reference other nodes?

import EventEditorDialog
import MMNode, windowinterface

CAUSES = [				# What causes the event
	# This list is incomplete
	'delay',
	'indefinite',		       
	'node',				# extrainfo is a pointer to an MMNode or string??
	'region',			# extrainfo is a pointer or string repr a region.
	'accesskey',			# extrainfo is the key pressed.
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


class EventStruct:
	# This encapsulates an event. An event is essentually a syncarc; this is a
	# copy of that syncarc which can return another syncarc.
	def __init__(self, syncarc, node=None, action=None):
		# if syncarc is None, make a new one. 
		# TODO: action is not a good name.. 
		self.cause = None
		self.clear_vars()
		if not syncarc:
			if action == 'endlist':
				a = 'end'
			else: # if action is None, for example.
				a = 'begin'
			self._syncarc = MMNode.MMSyncArc(node, a)
			self.set_cause('node')
			self.set_event('activateEvent')
			self.set_offset('0')
		else:
			self._syncarc = syncarc
			self.__init__set_vars()
			
	def get_value(self):
		# Returns the result of editing this syncarc.
		s = self._syncarc
		# Reset it.
		if s.isstart:
			action = "begin"
		elif s.isdur:
			action = "dur"
		elif s.ismin:
			action = "min"
		else:
			action = "end"

		c = self.get_cause()
		if c == 'indefinite':
			s.__init__(s.dstnode, action, delay=None)
			return s
		elif c == 'node':# and self._setnode:
			# The problem here is that I don't know how to map a name of a node to it's instance.
			print "TODO: don't know how to set node."
			s.__init__(s.dstnode, action, srcnode = s.srcnode, event=self.get_event(), delay=self.get_offset_number())
		elif c == 'region' and self._setregion:
			print "TODO: don't know how to set region."
		elif c == 'accesskey' and self._setkey:
			s.__init__(s.dstnode, action, accesskey=self._setkey, event=self.get_event(), delay=self.get_offset_number())
		elif c == 'marker' and self._setmarker:
			s.__init__(s.dstnode, action, marker=self._setmarker)
		elif c == 'delay':
			s.__init__(s.dstnode, action, srcnode='syncbase', delay=self.get_offset_number())
		elif c == 'wallclock':
			print "TODO: editing wallclock attributes."
			#s.__init__(s.dstnode, action,
		return self._syncarc

		if self._setevent:
			s.event = self._setevent
		if self._setoffset:
			s.delay = set.get_offset_number()


	def __init__set_vars(self):
		# Sets all the variables in this class.
		x = self._syncarc

		# The cause and the thing.
		if x.delay is None:
			self.cause = 'indefinite'
		elif x.wallclock is not None:
			self.cause = 'wallclock'
			self.delay = None
			self.thing = x.wallclock
		elif x.accesskey is not None:
			self.cause = 'accesskey'
			self.thing = x.accesskey
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

	def clear_vars(self):
		# Resets all the variables.
		self.event = None
		self.thing = None
		self._setcause = None	# These variables (_setx) override the defaults and will be committed.
		self._setevent = None
		self._setoffset = None
		#self._setthing = None
		self._setnode = None
		self._setregion = None
		self._setkey = None
		self._setmarker = None	# for later reference - a marker is a special element within the actual media.
					# e.g. a video could have markers at certain times.
		self._setwallclock = None
		if self.get_cause() == 'indefinite':
			self.delay = None
		else:
			self.delay = 0

	def as_string(self):
		# Must always return a string.
		c = self.get_cause()
		r = ""			# returnable value.
		s = self._syncarc
		if c == 'indefinite':
			return c
		elif c == 'marker':
			if s is None and self._setmarker is None:
				marker = "?"
			elif s is None and self._setmarker:
				marker = self._setmarker
			elif s.marker:
				marker = s.marker
			else:
				marker = ""
			return "marker('"+marker+"')"
		elif c == 'wallclock':
			if s is None and self._setwallclock:
				wc = self._setwallclock
			elif s is None and not self._setwallclock:
				wc = ""
			elif s.wallclock:
				wc = s.wallclock
			else:
				wc = ""
			return "wallclock( "+wc+" )"

		# Now for the offset things
		elif c == 'node':
			_, r, _, _ = self.get_thing_string()
			if r: r = r + '.' + self.get_event()
			else: r = self.get_event()
			##if isinstance(s, MMNode.MMSyncArc):
##				if isinstance(s.srcnode, MMNode.MMNode):
##					r = s.srcnode.GetName() + "." + self.get_event()
##				else:
##					r = s.srcnode + "." + self.get_event()
##			else:
##				r = 'unknown'
		elif c == 'region':
			_, r, _, _ = self.get_thing_string()
			if r: r = r + '.' + self.get_event()
			else: r = self.get_event()
##			if self._setregion:
##				r = self._setregion
##			elif isinstance(s, MMNode.MMSyncArc):
##				r = s.channel
##			else:
##				r = 'unknown'
		elif c == 'accesskey':
			if self._setkey:
				r = 'accesskey(' + self._setkey + ')'
			elif isinstance(self._syncarc, MMNode.MMSyncArc) and self._syncarc.accesskey:
				r = 'accesskey(' + self._syncarc.accesskey + ')'
			else:
				r = 'accesskey(?)'
		elif c == 'delay':
			d = self.get_offset()
			if d:
				return "Delay of " + d
			else:
				print "Got strange looking event: ", self._syncarc
				return "Error: strange event."
		else:
			print "ERROR: Unknown cause: ", c
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
		assert newcause in CAUSES
		self.clear_vars()
		self._setcause = newcause
	def get_event(self):
		# Only return the element which is in EVENTS_whatever list.
		if self._setevent:
			return self._setevent
		elif not self.event: # This should _never_ happen anyway..
					# if it does then there is something wrong with the event lists.
			return ""
		elif self.event.startswith('repeat'):
			# TODO: repeated times.
			return 'repeat'
		elif self.event.startswith('marker'):
			return 'marker'
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
			elif isinstance(self._syncarc, MMNode.MMSyncArc) and self._syncarc.srcnode:
				thing = self._syncarc.srcnode.GetName()
			else:
				thing = "SomeNode"
		elif c == 'region':
			print "TODO: display a region properly."
			name = "Region:"
			readonly = 1
			if self._setregion:
				thing = self._setregion
			elif isinstance(self._syncarc, MMNode.MMSyncArc):
				thing = self._syncarc.channel
			else:
				thing = "SomeRegion"
			#return ("Region:", repr(self._syncarc.channel), 0, 0)
		elif c == 'accesskey':
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
			if self._setwallclock:
				thing = self._setwallclock
			elif isinstance(self._syncarc, MMNode.MMSyncArc):
				thing = self._syncarc.wallclock
			else:
				thing = ""
			#return ("Clock time:", self._syncarc.wallclock, 0, 0)
		else:
			readonly = 1
			thing = ""
			name = ""
		if thing is None:
			thing = ""
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
		elif c == 'accesskey':
			self._setkey = newthing
		elif c in CAUSES:
			pass
		else:
			print "DEBUG: Unknown cause: ", c
		return None		# return an error otherwise.
	def get_offset(self):
		if self._setoffset:
			return self._setoffset
		if self._syncarc and self.get_cause() in ['node', 'accesskey', 'delay']: # TODO: check these.
			return `self._syncarc.delay`
		else:
			return None
	def get_offset_number(self):
		a = self.get_offset()
		if a:
			return float(a)
		else:
			return 0
	def set_offset(self, newoffset):
		if newoffset.isdigit():
			self._setoffset = newoffset
			return 1
		else:
			return 0
