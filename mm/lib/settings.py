__version__ = "$Id$"

# Module to handle various system attributes
import os
##import windowinterface

# some constants

# allow to manage all SMIL CSS constraints
# temporary constant: this constant will be remove as soon as it will be reliable
activeFullSmilCss = 0

# settings that cannot be changed when running
noprearm = 1				# don't prearm

# Defaults:
default_settings = {
##	'lightweight': 0,		# Lightweight version

	'system_bitrate': 56000,	# Fast modem
	'system_captions': 0,		# Don't show captions
	'system_language': 'en',	# English
	'system_overdub_or_caption': 'caption', # Captions preferred over overdub
## Special case, see get() routine
##	'system_screen_size': windowinterface.getscreensize(), # Size of screen
##	'system_screen_depth': windowinterface.getscreendepth(), # Depth of screen
	'system_required': [],		# Needs special handling in match...
	'system_audiodesc': 0,		# No audio description
	'system_operating_system': 'UNKNOWN',
	'system_cpu': 'UNKNOWN',
	'license': '',
	'license_user' : '',
	'license_organization' : '',
##	'compatibility': G2,		# Try to be compatible with...
	'cmif': 0,			# Show cmif-only attributes
	'debug': 0,			# Show debug commands
	'checkext': 1,			# Guess Mime type based on extension
	'no_canvas_resize': 1,	 # Don't resize canvas after window resize (X)
	'hierarchy_minimum_sizes': 0,	# Leaf nodes drawn using min. size
	'structure_name_size': 1,
	'root_expanded': 0,		# Root node always expanded
	'recent_documents':[],		# Recently used documents
	'thumbnail_size':10.0,		# Size of thumbnail (mm)
	'time_scale_factor': 1.0,	# Scale factor for sec to mm
	'show_links':1,			# Show hyperlink icons
	'no_initial_dialog': 0,		# Don't show initial dialog if true
	'RPthumbnails': 0,		# RealPix thumbnails in timeline view
	'cascade': 0,			# Cascade regions when no <layout>
# HierarchyView colors
	'structure_bgcolor': (150, 150, 150), # Light gray
	'structure_leafcolor': (255,255,222),
	'structure_darkleaf': (203,203,170),
	'structure_rpcolor': (196,159,127),
	'structure_darkrp': (196,159,127),
	'structure_slidecolor': (222,255,255),
	'structure_darkslide': (164,181,181),
	'structure_bagcolor': (148,117,166),
	'structure_darkbag': (131,119,137),
	'structure_altcolor': (184,95,95),
	'structure_darkalt': (157,108,108),
	'structure_parcolor': (79,156,130),
	'structure_darkpar': (91,126,114),
	'structure_seqcolor': (116,154,189),
	'structure_darkseq': (108,128,146),
	'structure_exclcolor': (148,117,166), # for now equal to bag colors
	'structure_darkexcl': (131,119,137),
	'structure_priocolor': (166,61,126),
	'structure_darkprio': (142,53,108),
	'structure_textcolor': (0, 0, 0), # Black
	'structure_ctextcolor': (50, 50, 50),	# Very dark gray
	'structure_expcolor': (200, 200, 200), # Open disclosure triangle
	'structure_colcolor': (200, 200, 200), # Closed disclosure triangle
	'structure_ecbordercolor': (40, 40, 40), # triangle border
	'structure_focusleft': (200, 200, 200),
	'structure_focustop': (200, 200, 200),
	'structure_focusright': (40, 40, 40),
	'structure_focusbottom': (40, 40, 40),
# ChannelView colors
	'timeline_bgcolor': (150, 150, 150), # Light gray
	'timeline_guttertop': (80, 80, 80),
	'timeline_gutterbottom': (175, 175, 175),
	'timeline_bordercolor': (75, 75, 75), # Dark gray
	'timeline_channelcolor': (240, 240, 240), # Very light gray
	'timeline_channeloffcolor': (160, 160, 160), # Darker gray
	'timeline_nodecolor': (255,255,222),
	'timeline_altnodecolor': (208, 182, 160),
	'timeline_nodeoffcolor': (200, 200, 200), # CHANNELOFFCOLOR
	'timeline_altnodeoffcolor': (160, 160, 160), # BGCOLOR
	'timeline_arrowcolor': (0, 0, 255), # Blue
	'timeline_textcolor': (0, 0, 0), # Black
	'timeline_focuscolor': (255, 0, 0), # Red (for sync arcs only now)
	'timeline_lockedcolor': (200, 255, 0), # Yellowish green
	'timeline_anchorcolor': (255, 127, 0), # Orange/pinkish
	# Focus color assignments (from light to dark gray)
	'timeline_focusleft': (200, 200, 200),
	'timeline_focustop': (200, 200, 200),
	'timeline_focusright': (40, 40, 40),
	'timeline_focusbottom': (40, 40, 40),
	# Arm colors
	'timeline_armactivecolor': (255, 255, 0),
	'timeline_arminactivecolor': (255, 200, 0),
	'timeline_armerrorcolor': (255, 0, 0),
	'timeline_playactivecolor': (0, 255, 0),
	'timeline_playinactivecolor': (0, 127, 0),
	'timeline_playerrorcolor': (255, 0, 0),
	# Locations on the net
	'templatedir_url': 'http://www.oratrix.com/indir/images',
	'defaultviews' : ['hierarchy'],	# Default views to open
	'showsource' : 0,	# Hidden preference to show source window in the player
}

user_settings = {}

# Which of these should match exactly:
EXACT=['system_captions', 'system_overdub_or_captions',
       'system_audiodesc']
LANGUAGE=['system_language']
ALL=['system_bitrate', 'system_captions', 'system_language',
     'system_overdub_or_caption', 'system_screen_size',
     'system_screen_depth', 'system_required', 'system_audiodesc',
     'system_operating_system', 'system_cpu']

NEEDS_RESTART=['cmif', 'vertical_structure', 'no_canvas_resize', 'root_expanded']

from SMIL import extensions

# Where is the preferences file:
if os.name == 'posix':
	PREFSFILENAME=os.environ['HOME']+'/.grins'
elif os.name == 'mac':
	import macfs, MACFS
	vrefnum, dirid = macfs.FindFolder(MACFS.kOnSystemDisk, 'pref', 1)
	import version
	prefname = version.macpreffilename
	fss = macfs.FSSpec((vrefnum, dirid, prefname))
	PREFSFILENAME=fss.as_pathname()
else:
	default_settings['html_control'] = 0	# which HTML control to use
	import cmif
	PREFSFILENAME=cmif.findfile('grprefs.txt')

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
		if name == 'system_screen_size':
			import windowinterface
			return windowinterface.getscreensize() # Size of screen
		if name == 'system_screen_depth':
			import windowinterface
			return windowinterface.getscreendepth() # Depth of screen

		real_value = default_settings.get(name)
		if real_value is None:
			print 'Warning: unknown system attribute', name
			return 0
		# return copy of mutable values if from default_settings
		rtype = type(real_value)
		if rtype is type([]):
			real_value = real_value[:]
		elif rtype is type({}):
			real_value = real_value.copy()
	return real_value
	
def has_key(name):
	if user_settings.has_key(name):
		return 1
	if default_settings.has_key(name):
		return 1
	return name == 'system_screen_size' or name == 'system_screen_depth'

def match(name, wanted_value):
	if name == 'system_operating_system':
		import opsys, string
		wanted_value = string.upper(wanted_value)
		return opsys.opsys.has_key(wanted_value) and opsys.opsys[wanted_value]
	if name == 'system_cpu':
		import opsys, string
		wanted_value = string.upper(wanted_value)
		return opsys.cpu.has_key(wanted_value) and opsys.cpu[wanted_value]
	if name == 'system_required':
		for v in wanted_value:
			if not extensions.get(wanted_value, 0):
				return 0
			return 1
	real_value = get(name)
	if name in EXACT:
		return (real_value == wanted_value)
	elif name in LANGUAGE:
		import string
		# Evaluates to "true" if one of the languages
		# indicated by user preferences exactly equals one of
		# the languages given in the value of this parameter,
		# or if one of the languages indicated by user
		# preferences exactly equals a prefix of one of the
		# languages given in the value of this parameter such
		# that the first tag character following the prefix is
		# "-".
		pref_langs = map(string.strip, string.split(real_value, ','))
		for lang in map(string.strip, string.split(wanted_value, ',')):
			for pref_lang in pref_langs:
				if pref_lang == lang:
					return 1
				plen = len(pref_lang)
				if pref_lang == lang[:plen] and \
				   lang[plen:plen+1] == '-':
					return 1
		return 0
	else:
		return (real_value >= wanted_value)

def getsettings():
	return ALL

_warned_already = 0
def set(setting, value):
	global _warned_already
	import windowinterface
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
		if not default_settings.has_key(name) or value != default_settings[name]:
			fp.write('%s = %s\n'%(name, `value`))
	fp.close()
	return 1
