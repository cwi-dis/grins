#
# select workaround for MacCmif
#

import Evt

def select(ifdlist, ofdlist, efdlist, timeout=None):
	if timeout == None and (ifdlist or ofdlist or efdlist):
		raise 'Select without timeout', (ifdlist, ofdlist, efdlist)
	if timeout > 0:
		dummy, (what, msg, when, where, modifiers) = Evt.WaitNextEvent(0, 0)
		stop_when = when + int(timeout*60)
		while when < stop_when:
			dummy, (what, msg, when, where, modifiers) = Evt.WaitNextEvent(0,
					stop_when-when)
	return [], [], []
	
