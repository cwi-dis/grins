__version__ = "$Id$"

# Module to handle various system attributes
import os
import windowinterface


# Defaults:
default_settings = {
	'system_bitrate': 14400,	# Slow modem
	'system_captions': 0,		# Don't show captions
	'system_language': '',		# No language preference
	'system_overdub_or_caption': 'caption', # Captions preferred over overdub
	'system_screen_size': windowinterface.getscreensize(), # Size of screen
	'system_screen_depth': windowinterface.getscreendepth(), # Depth of screen
	'system_required': (),		# Needs special handling in match...
	'license': '',
	'cmif': 0,			# Show cmif-only attributes
	'checkext': 1,			# Guess Mime type based on extension
	'vertical_structure': 1,	# Orientation of Structure View
	'no_canvas_resize': 0, # Don't resize canvas after window resize (X)
	'hierarchy_minimum_sizes': 0,	# Leaf nodes drawn using min. size
	'root_expanded': 1,		# Root node always expanded
	'recent_documents':[],	# Recently used documents
}

user_settings = {}

# Which of these should match exactly:
EXACT=['system_captions', 'system_language', 'system_overdub_or_captions']
ELEMENT=['system_required']
ALL=['system_bitrate', 'system_captions', 'system_language',
     'system_overdub_or_caption', 'system_screen_size',
     'system_screen_depth', 'system_required']
     
NEEDS_RESTART=['cmif', 'vertical_structure', 'no_canvas_resize', 'root_expanded']

# Where is the preferences file:
if os.name == 'posix':
	PREFSFILENAME=os.environ['HOME']+'/.grins'
elif os.name == 'mac':
	import macfs, MACFS
	vrefnum, dirid = macfs.FindFolder(MACFS.kOnSystemDisk, 'pref', 1)
	fss = macfs.FSSpec((vrefnum, dirid, 'GRiNS Preferences'))
	PREFSFILENAME=fss.as_pathname()
else:
	default_settings['html_control'] = 0	# which HTML control to use
	PREFSFILENAME='grprefs.txt'

def restore():
	global user_settings
	user_settings = {}
	if os.path.exists(PREFSFILENAME):
		execfile(PREFSFILENAME, user_settings)
	# Remove __globals__ and such from the user_settings dict
	for k in user_settings.keys():
		if k[:2] == '__':
			del user_settings[k]
		
restore()

def factory_defaults():
	global user_settings
	user_settings = {}
	
def get(name):
	real_value = user_settings.get(name)
	if real_value is None:		
		real_value = default_settings.get(name)
		if real_value is None:
			print 'Warning: unknown system attribute', name
			return 0
	return real_value

def match(name, wanted_value):
	real_value = get(name)
	if name in EXACT:
		return (real_value == wanted_value)
	elif name in ELEMENT:
		return (wanted_value in real_value)
	else:
		return (real_value >= wanted_value)

def getsettings():
	return ALL
	
_warned_already = 0
def set(setting, value):
	global _warned_already
	if setting in NEEDS_RESTART and value != get(setting) and not _warned_already:
		_warned_already = 1
		windowinterface.showmessage('You have to restart GRiNS for some of these changes to take effect')
	user_settings[setting] = value
	
def save():
	needrestart = 0
	try:
		fp = open(PREFSFILENAME, 'w')
	except IOError:
		return 0
	for name, value in user_settings.items():
		fp.write('%s = %s\n'%(name, `value`))
	fp.close()
	return 1
	
	
