__version__ = "$Id$"

#
# Definition of scheduler events.
#
# A single scheduler record looks like ([list of prereqs], [list of actions])
# Each prereq and each action look like (opcode, node-uid)
#
# All SCHED* events are internal scheduler events, and all PLAY* things
# are sent to channels (or come from channels)
# All *DONE events are 'upcalls'.
# The *STOP events have no corresponding upcalls.
#
[NO_EVENT, SCHED, SCHED_DONE, PLAY, PLAY_DONE, SCHED_STOP, PLAY_STOP,\
	  SYNC, SYNC_DONE, PLAY_ARM, ARM_DONE, SCHED_FINISH, BAG_START, \
	  BAG_STOP, BAG_DONE, TERMINATE, LOOPSTART, LOOPSTART_DONE, \
	  LOOPEND, LOOPEND_DONE, LOOPRESTART, PLAY_OPTIONAL_ARM] = range(22)

## side_effects = (PLAY, PLAY_STOP, PLAY_ARM)

op_names = [ 'NO_EVENT', 'SCHED', 'SCHED_DONE', 'PLAY', 'PLAY_DONE', \
	  'SCHED_STOP', 'PLAY_STOP', 'SYNC', 'SYNC_DONE', \
	  'PLAY_ARM', 'ARM_DONE', 'SCHED_FINISH', 'BAG_START', \
	  'BAG_STOP', 'BAG_DONE', 'TERMINATE', 'LOOPSTART', 'LOOPSTART_DONE', \
	  'LOOPEND', 'LOOPEND_DONE', 'LOOPRESTART', 'PLAY_OPTIONAL_ARM']

def ev2string(ev):
	try:
		opcode, node = ev
		if opcode == SYNC:
			delay, node = node
			if type(node) == type(0):
				return 'SYNC(%e, %d)' % (delay, node)
			return 'SYNC(%e, %s)' % (delay, _getname(node))
		if opcode == SYNC_DONE and type(node) == type(0):
			return 'SYNC_DONE(%d)' % node
		name = _getname(node)
		return op_names[opcode] + '(' + name + ')'
	except:
		return 'ILL-FORMED-EVENT:'+`ev`
		
def _getname(node):
	uid = node.GetUID()
	name = node.GetAttrDef('name', '') + '#' + uid
	return name

def evlist2string(evlist):
	first = 1
	str = ''
	for ev in evlist:
		if not first:
			str = str + ', '
		first = 0
		str = str + ev2string(ev)
	return str

def sr2string((prereq, actions)):
	return evlist2string(prereq) + ':\t' + evlist2string(actions)


