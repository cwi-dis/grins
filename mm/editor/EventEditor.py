__version__ = "$Id$"

# This module is a collection of useful functions for working with events.

# TODO: how do I reference other nodes?

import MMNode, windowinterface, SMILTreeWrite
from fmtfloat import fmtfloat

CAUSES = [				# What causes the event
	# This list is incomplete
	'delay',
	'indefinite',		       
	'node',				# extrainfo is a pointer to an MMNode or string??
	'region',			# extrainfo is a pointer or string repr a region.
	'accesskey',			# extrainfo is the key pressed.
	#'marker',			# er.. I admit that I don't understand this.
	'wallclock',			# extrainfo is the time.
	# What else??
	]

# Reference: pg 401 of the SMIL printout on my desk; or chapter 13.3.12 (events)
EVENTS_CNODE = [				# What the event actually is.
	'begin',
	'end',
	'repeat',			# what about it's integer argument??
	'focusInEvent',
	'focusOutEvent',		# NO OFFSET!
	'activateEvent',
	'beginEvent',
	'endEvent',			
	'repeatEvent',			# NO OFFSET!
	]

EVENTS_MNODE = EVENTS_CNODE+['marker']

EVENTS_REGION = [			# no offsets at all!
	#'activateEvent',
	#'focusInEvent',		# These have all been removed from SMIL2
	#'focusOutEvent',
	#'inBoundsEvent',
	#'outOfBoundsEvent',
	'topLayoutOpenEvent',
	'topLayoutCloseEvent',
	]


class EventStruct:
	# This encapsulates an event. An event is essentually a syncarc; this is a
	# copy of that syncarc which can return another syncarc.
	def __init__(self, syncarc, node=None, action=None):
		# if syncarc is None, make a new one. 
		self.cause = None
		self.clear_vars()
		self._node = node
		if not syncarc:
			if action == 'endlist':
				a = 'end'
			else: # if action is None, for example.
				a = 'begin'
			self._syncarc = MMNode.MMSyncArc(node, a)
			self.set_cause('delay')
			self.set_offset(0)
		else:
			self._syncarc = syncarc
			self.__init__set_vars()
			
	# we need this method so that the Apply button gets enabled and disabled properly
	def __cmp__(self, other):
		return cmp(self.__get_values(), other.__get_values())

	def __get_values(self):
		arc = self._syncarc
		return self._setnode or arc.srcnode, self._setcause or self.cause, self._setevent or self.event, self._setoffset or arc.delay, self._setrepeat or arc.get_repeat(), self._setwallclock or arc.wallclock, self._setregion or arc.channel, self._setmarker or arc.marker, self._setkey or arc.accesskey

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
			s.__init__(self._node, action, delay=None)
			return s
		elif c == 'node':# and self._setnode:
			# The problem here is that I don't know how to map a name of a node to it's instance.
			if self._setnode is not None:
				node = self._setnode
			else:
				node = s.srcnode
			if not node:
				print "TODO: No node!! (EventEditor)"
			e = self.get_event()
			if e.startswith('repeat') and e != 'repeatEvent':
				e = e + '(' + `self.get_repeat()` + ')'
			if e == 'marker':
				s.__init__(self._node, action, srcnode = node, marker = self.get_marker(),
					   delay=self.get_offset())
			else:
				s.__init__(self._node, action, srcnode = node, event=e, delay=self.get_offset())
		elif c == 'region':
			ch = self.get_region()
			channel = self._node.context.channeldict[ch]
			s.__init__(self._node, action, channel=channel, event=self.get_event(), delay = self.get_offset())
		elif c == 'accesskey' and self._setkey:
			s.__init__(self._node, action, accesskey=self._setkey, delay=self.get_offset())
		elif c == 'delay':
			s.__init__(self._node, action, srcnode='syncbase', delay=self.get_offset())
		elif c == 'wallclock':
			s.__init__(self._node, action, wallclock=self.get_wallclock(), delay=0)
		return self._syncarc

##		if self._setevent:
##			s.event = self._setevent
##		if self._setoffset:
##			s.delay = set.get_offset()


	def __init__set_vars(self):
		# Sets all the variables in this class.
		x = self._syncarc

		# The cause and the thing.
		if x.delay is None:
			self.cause = 'indefinite'
		elif x.wallclock is not None:
			self.cause = 'wallclock'
			self.delay = None
		elif x.accesskey is not None:
			self.cause = 'accesskey'
		elif x.marker is not None:
			self.cause = 'node'
			self.event = 'marker'
		elif x.channel is not None:
			self.cause = 'region'
		else:
			self.cause = 'node'
			if isinstance(x.srcnode, MMNode.MMNode):
				pass
			elif x.srcnode == 'syncbase':
				self.cause = 'delay'
			elif type(x.srcnode) is not type('') and x.srcnode != 'prev':
				print "DEBUG: EventEditor.__init_set_vars got strange looking event.", x.srcnode
		# The event.
		if self.cause == 'node' or self.cause == 'region':
			if not self.get_event()=='marker':
				self.event = x.event
				
		self._setnode = x.srcnode
		
	def clear_vars(self):
		# Resets all the variables.
		self.event = None
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
		self._setrepeat = None
		if self.get_cause() == 'indefinite':
			self.delay = None
		else:
			self.delay = 0

	def as_string(self):
		# Must always return a string.
		c = self.get_cause()
		r = ""			# returnable value.
##		s = self._syncarc
		if c == 'indefinite':
			return c
		elif c == 'wallclock':
			wc = self.get_wallclock()
			return SMILTreeWrite.wallclock2string(wc)
			
##			if s is None and self._setwallclock:
##				wc = SMILTreeWrite.wallclock2string(self._setwallclock)
##			elif s is None and not self._setwallclock:
##				wc = "wallclock(undefined)"
##			elif s.wallclock:
##				wc = SMILTreeWrite.wallclock2string(s.wallclock)
##			else:
##				wc = ""
##			return wc

		# Now for the offset things
		elif c == 'node':
			r = self.get_thing_string()[1]
			e = self.get_event()
			if r: r = r + '.' + e
			else: r = e
			if e.startswith('repeat') and e != 'repeatEvent':
				r = r + "(" + `self.get_repeat()` + ")"
			elif e.startswith('marker'):
				r = r + "(" + self.get_marker() + ')'
			##if isinstance(s, MMNode.MMSyncArc):
##				if isinstance(s.srcnode, MMNode.MMNode):
##					r = s.srcnode.GetName() + "." + self.get_event()
##				else:
##					r = s.srcnode + "." + self.get_event()
##			else:
##				r = 'unknown'
		elif c == 'region':
			r = self.get_region() + '.' + self.get_event()
		elif c == 'accesskey':
			if self._setkey:
				r = 'accesskey(' + self._setkey + ')'
			elif isinstance(self._syncarc, MMNode.MMSyncArc) and self._syncarc.accesskey:
				r = 'accesskey(' + self._syncarc.accesskey + ')'
			else:
				r = 'accesskey(?)'
		elif c == 'delay':
			d = self.get_offset()
			return "Delay of " + `d`
		else:
			print "ERROR: Unknown cause: ", c
		d = self.get_offset()
		if d is None:
			d = ''
		else:
			d = fmtfloat(d, suffix = 's', withsign = 1)
		return r+d
		
	def get_cause(self):
		if self._setcause:
			return self._setcause
		else:
			return self.cause

	def set_cause(self, newcause):
		assert newcause in CAUSES
		if newcause == 'node' and not self.has_node():
			# Then a node is required
			return
		self._setcause = newcause
		if newcause in ('node', 'delay', 'accesskey'):
			# Then time information is required.
			self.check_offset()
			if newcause == 'node':
				self.check_event()
			elif newcause == 'accesskey':
				self.check_key()
		elif newcause == 'region':
			self.check_region()
			self.check_offset()
			self.check_event()
			self.set_offset(0)

	def has_node(self):
		if self._setnode is not None:
			return 1
		if isinstance(self._syncarc.srcnode, MMNode.MMNode):
			return 1
		elif type(self._syncarc.srcnode) is type('') and self._syncarc.srcnode not in ('prev', 'syncbase'):
			return 1
		else:
			return 0

	def get_node(self):
		if self._setnode is not None:
			return self._setnode
		return self._syncarc.refnode()

	def set_node(self, newnode):
		oldnode = self._setnode
		if oldnode is None:
			oldnode = self._syncarc.srcnode
		if oldnode == newnode:
			return
		if newnode is None:
			self._setnode = None
			return
		self._setnode = newnode
		if not self.get_event():
			self.set_event('begin')

	def get_relative(self):
		if not self.has_node():
			return 0
		node = self._setnode
		if not node:
			node = self._syncarc.srcnode
		return not isinstance(node, MMNode.MMNode)

	def set_relative(self, relative):
		if not self.has_node():
			return 0
		node = self._setnode
		if not node:
			node = self._syncarc.srcnode
		if isinstance(node, MMNode.MMNode):
			if relative:
				savenode = self._syncarc.srcnode
				self._syncarc.srcnode = node
				self._setnode = self._syncarc.xpath()
				self._syncarc.srcnode = savenode
			# else already relative
		else:
			if not relative:
				savenode = self._syncarc.srcnode
				self._syncarc.srcnode = node
				self._setnode = self._syncarc.refnode()
				self._syncarc.srcnode = savenode
				if self._setnode is None:
					self._setnode = node
					return 0
		return 1

	def get_event(self):
		# Only return the element which is in EVENTS_whatever list.
		if self._setevent:
			return self._setevent
		elif not self.event: # This should _never_ happen anyway..
					# if it does then there is something wrong with the event lists.
			return ""
		elif self.event.startswith('repeat') and self.event != 'repeatEvent':
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

	def check_event(self):
		cause = self.get_cause()
		event = self.get_event()
		if cause == 'region':
			if event not in EVENTS_REGION:
				self._setevent = EVENTS_REGION[0]
		elif cause == 'node':
			if self.__isMediaNode():
				if event not in EVENTS_MNODE:
					self._set = EVENTS_MNODE[0]
			else:
				if event not in EVENTS_CNODE:
					self._setevent = EVENTS_CNODE[0]

	def set_event(self, newevent):
		assert newevent in EVENTS_MNODE or newevent in EVENTS_REGION
		self._setevent = newevent

	def __isMediaNode(self):
		node = self._setnode
		if type(node) is type(""):	
			node = self._syncarc.refnode()
		from MMTypes import mediatypes
		return node is not None and node.type in mediatypes
		
	def get_possible_events(self):
		cause = self.get_cause()
		if cause == 'node':
			if self.__isMediaNode():
				return EVENTS_MNODE
			else:
				return EVENTS_CNODE
				
		elif cause == 'region':
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
			name = "Source node:"
			if self._setnode:
				node = self._setnode
			else:
				node = self._syncarc.srcnode
			if isinstance(node, MMNode.MMNode):
				thing = node.GetName()
			elif type(node) is type('') and node not in ('prev','syncbase'):
				refnode = self._syncarc.refnode()
				if refnode is None:
					thing = 'Dangling node'
				else:
					thing = refnode.GetName()
			else:
				thing = "SomeNode"
		elif c == 'region':
			name = "Top Layout:"
			readonly = 1
			if self._setregion:
				thing = self._setregion
			elif isinstance(self._syncarc, MMNode.MMSyncArc):
				thing = self._syncarc.channel.name
			else:
				thing = "Unknown topLayout"
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
				thing = SMILTreeWrite.wallclock2string(self._setwallclock)
			elif isinstance(self._syncarc, MMNode.MMSyncArc):
				if self._syncarc.wallclock:
					thing = SMILTreeWrite.wallclock2string(self._syncarc.wallclock)
				else:
					thing = SMILTreeWrite.wallclock2string(self.get_wallclock())
			else:
				thing = ""
			#return ("Clock time:", self._syncarc.wallclock, 0, 0)
		elif c == 'region':
			return self.get_region()
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
		#if c == 'node':
		#	self._setnode = newthing
		#elif c == 'region':
		#	self._setregion = newthing
		if c == 'accesskey':
			self._setkey = newthing
		elif c in CAUSES:
			pass
		else:
			print "DEBUG: Unknown cause: ", c
			assert 0
		return None		# return an error otherwise.

	def get_offset(self):
		if self.get_cause() not in ['node', 'accesskey', 'delay', 'region']: # TODO: check these.
			return None
		if self._setoffset is not None:
			return self._setoffset
		if self._syncarc:
			if self._syncarc.delay:
				return self._syncarc.delay
			else:
				return 0
		else:
			return None

	def check_offset(self):
		if self._setoffset is None and self._syncarc.delay is None:
			self._setoffset = 0

	def set_offset(self, newoffset):
		if self.get_offset() != newoffset:
			self._setoffset = newoffset

	def get_repeat(self):
		if self._setrepeat is not None:
			return self._setrepeat
		event = self.get_event()
		if event and event.startswith("repeat") and event != "repeatEvent":
			a = self._syncarc.get_repeat()
			if a:
				return a
			else:
				return 1
		else:
			return None

	def set_repeat(self, repeat):
		if self.get_repeat() != repeat:
			self._setrepeat = repeat

	def get_wallclock(self):
		if self._setwallclock is not None:
			return self._setwallclock
		elif self._syncarc.wallclock is not None:
			return self._syncarc.wallclock
		else:
			return (None, None, None, 12, 0, 0.0, None, None, None)

	def set_wallclock(self, value):
		if self.get_wallclock() != value:
			self._setwallclock = value

	def get_region(self):
		if self._setregion:
			return self._setregion
		elif self._syncarc and self._syncarc.channel:
			return self._syncarc.channel.name
		else:
			return 'No viewports available'

	def check_region(self):
		if self._setregion is None and self._syncarc.channel is None:
			self._setregion = self.get_viewports()[0]

	def set_region(self, newregion):
		if self.get_region() == newregion:
			return
		if newregion is None:
			# Find the first topLayout.
			self._setregion = self.get_viewports()[0]
			return
		assert isinstance(newregion, type(""))
		self._setregion = newregion

	def get_viewports(self):
		if not self._node:
			# then we have a problem.
			assert 0
		viewports = self._node.context.getviewports()
		assert len(viewports) > 0
		names = []
		for i in viewports:
			names.append(i.name)
		return names

	def get_marker(self):
		if self._setmarker is not None:
			return self._setmarker
		else:
			if self._syncarc.marker:
				return self._syncarc.marker
			else:
				return "?"

	def set_marker(self, value):
		if self.get_marker() != value:
			self._setmarker = value

	def check_key(self):
		if self._setkey is None and self._syncarc.accesskey is None:
			self._setkey = 'a'
