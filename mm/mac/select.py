#
# select workaround for MacCmif
#

import time

def select(ifdlist, ofdlist, efdlist, timeout=None):
	if timeout == None and (ifdlist or ofdlist or efdlist):
		raise 'Select without timeout', (ifdlist, ofdlist, efdlist)
	if timeout > 0:
		time.sleep(timeout)
	return [], [], []
	
