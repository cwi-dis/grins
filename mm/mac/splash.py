import MacOS

firsttime = 1

RESOURCE_ID={
	'loadprog': 513,
	'loaddoc': 514,
	'initdoc': 515
}

def splash(arg=0, version=None):
	global firsttime
	if not firsttime:
		return
	if version and not arg:
		return
	if not arg:
		MacOS.splash()
		firsttime = 0
	else:
		MacOS.splash(RESOURCE_ID[arg])
		

def unsplash():
	pass
	
