# This module is a collection of useful functions for working with events.

import EventEditorDialog, grinsRC, components
import MMNode

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
	'indefinite',		       
	'node',				# extrainfo is a pointer to an MMNode or string??
	'region',			# extrainfo is a pointer or string repr a region.
	'prev',
	'accessKey',			# extrainfo is the key pressed.
	'marker',			# er.. I admit that I don't understand this.
	'wallclock',			# extrainfo is the time.
	]

EVENTS_NODE = [				# What the event actually is.
	# This list is incomplete
	'.begin',
	'.end',
	'.repeat',			# what about it's integer argument??
	'.click',
	'.activateEvent',
	'.This list has not yet been completed yet.',
	]

EVENTS_REGION = [
	# This list is incomplete
	'.mouseIn',
	'.mouseOut',
	'This list has not been written yet.'
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

	def done(self):
		# callback for when the user has finished.
		# TODO: put all the instance variables back into the syncarc and return it (?)
		print "Done."
		return 1		# return 0 if you do not want to close the dialog.


class EventStruct:
	# This encapsulates an event.
	def __init__(self, syncarc):
		self._syncarc = syncarc
		self.cause = None
		self.event = None
		self.delay = None
		self.thing = None
		self._setcause = None	# These variables (_setx) override the defaults and will be committed.
		self._setevent = None
		self._setdur = None
		
		self.set_vars()

	def get_value(self):
		# Returns the result of editing this syncarc.
		if self._setcause or self._setevent or self._setdur:
			print "ERROR: Code not written yet - actual changes to events."
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
			self.cause = 'node'
			if isinstance(x.srcnode, MMNode.MMNode):
				self.thing = x.srcnode.GetName()
			else:
				self.thing = x.srcnode
		# The event.
		if self.cause == 'node' or self.cause == 'region':
			self.event = x.event

	def as_string(self):
		return repr(self._syncarc)
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
		else:
			return self.event
	def get_event_index(self):
		# return the current event index from the list of possible events.
		if not self.event:
			return None
		else:
			try:
				return self.get_possible_events().index(self.get_event())
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
		# returns a tuple of (string, Bool isnumber, Bool readonly)
		# isnumber is if the string is a number.
		# readonly is if this should be editable in the dialog/
		return ("Test string", 0, 0)
