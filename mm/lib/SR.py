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
[NO_EVENT, SCHED, SCHED_DONE, PLAY, PLAY_DONE, SCHED_STOP, PLAY_STOP,
        PLAY_ARM, ARM_DONE, SCHED_FINISH,
        LOOPSTART, LOOPSTART_DONE,
        LOOPEND, LOOPEND_DONE, LOOPRESTART, PLAY_OPTIONAL_ARM,
        SCHED_STOPPING, SCHED_START] = range(18)

## side_effects = (PLAY, PLAY_STOP, PLAY_ARM)

op_names = [ 'NO_EVENT', 'SCHED', 'SCHED_DONE', 'PLAY', 'PLAY_DONE',
             'SCHED_STOP', 'PLAY_STOP',
             'PLAY_ARM', 'ARM_DONE', 'SCHED_FINISH', 'LOOPSTART',
             'LOOPSTART_DONE', 'LOOPEND', 'LOOPEND_DONE', 'LOOPRESTART',
             'PLAY_OPTIONAL_ARM', 'SCHED_STOPPING', 'SCHED_START' ]

def ev2string(ev):
    try:
        opcode, node = ev
        return '%s(%s)' % (op_names[opcode], _getname(node))
    except:
        return 'ILL-FORMED-EVENT:'+`ev`

def _getname(node):
    return '%s#%s' % (node.GetAttrDef('name', ''), node.GetUID())

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
