def findfile(name):
	import os
	if os.environ.has_key('CMIF'):
		CMIF = os.environ['CMIF']
	else:
		CMIF = '/ufs/guido/mm/demo' # Traditional default
	return os.path.join(CMIF, name)
