__version__ = "$Id$"

# Module to handle various system attributes
import os
import sys
##import windowinterface

# Minimal EditMgr-like registry
# XXXX This interface is a bit silly. Transactions are
# optional, if you call transaction() you must also
# call commit(), but if you leave them both out the
# set() and friends will call them for you.
_registry=[]
_in_transaction = 0

# some constants

# enable or disable language extensions
profileExtensions = {
	'InlineTransitions': 1,
	'SplineAnimation': 1,
	'SyncMaster': 0,
	'TimeContainerAttributes': 0,
	'TimeManipulations': 1,
}

# settings that cannot be changed when running
noprearm = 1				# don't prearm

# Defaults:
default_settings = {
##	'lightweight': 0,		# Lightweight version

	'system_bitrate': 56000,	# Fast modem
	'system_captions': 0,		# Don't show captions
	'system_language': 'en',	# English
	'system_overdub_or_caption': 'subtitle', # Subtitles preferred over overdub
## Special case, see get() routine
##	'system_screen_size': windowinterface.getscreensize(), # Size of screen
##	'system_screen_depth': windowinterface.getscreendepth(), # Depth of screen
	'system_required': (),		# Needs special handling in match...
	'system_component': (),		# Needs special handling in match...
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
	'showhidden': 0,		# Show override="hidden" custom tests
	'hierarchy_minimum_sizes': 0,	# Leaf nodes drawn using min. size
	'structure_name_size': 1,
	'structure_thumbnails': 1,	# Display image thumbnails by default
	'structure_tickdistance':5,	# Min distance between tick in timeline
	'root_expanded': 0,		# Root node always expanded
	'recent_documents':[],		# Recently used documents
	'thumbnail_size':10.0,		# Size of thumbnail (mm)
	'time_scale_factor': 1.0,	# Scale factor for sec to mm
	'show_links':1,			# Show hyperlink icons
	'initial_dialog': 1,		# Show initial dialog if true
	'RPthumbnails': 0,		# RealPix thumbnails in timeline view
	'cascade': 0,			# Cascade regions when no <layout>
	'no_image_cache': 0,		# Don't cache images (or info about them)
	'noskip': 0,			# Don't skip initial part of continuous media
	'vertical_icons': 1,		# Display icons vertically in Structure View
	'vertical_spread': 1,		# Fill vertical free space in Structure View
# HierarchyView colors
	'structure_bgcolor': (150, 150, 150), # Background of Structure View
	'structure_leafcolor': (255,255,222), # Unselected playable leaf nodes
	'structure_darkleaf': (203,203,170), # Unselected unplayable leaf nodes
	'structure_commentcolor': (203,203,170), # Comment nodes
	'structure_foreigncolor': (255,222,255), # Playable foreign nodes
	'structure_darkforeign': (181,164,181),	# Unplayable foreign nodes
	'structure_rpcolor': (196,159,127), # Playable RealPix nodes (G2 only)
	'structure_darkrp': (196,159,127), # Unplayable RealPix nodes (G2 only)
	'structure_slidecolor': (222,255,255), # Playable RealPix slide (G2 only)
	'structure_darkslide': (164,181,181), # Unplayable RealPix slide (G2 only)
	'structure_altcolor': (184,95,95), # Playable switch node
	'structure_darkalt': (157,108,108), # Unplayable switch node
	'structure_parcolor': (79,156,130), # Playable par node
	'structure_darkpar': (91,126,114), # Unplayable par node
	'structure_seqcolor': (116,154,189), # Playable seq node
	'structure_darkseq': (108,128,146), # Unplayable seq node
	'structure_exclcolor': (148,117,166), # Playable excl node
	'structure_darkexcl': (131,119,137), # Unplayable excl node
	'structure_priocolor': (166,61,126), # Playable prio node
	'structure_darkprio': (142,53,108), # Unplayable prio node
	'structure_textcolor': (0, 0, 0), # Most text
	'structure_ctextcolor': (50, 50, 50),	# Region names
	'structure_expcolor': (200, 200, 200), # Open disclosure triangle (not used?)
	'structure_colcolor': (200, 200, 200), # Collision color (not used?)
	'structure_fillcolor': (255,255,222), # Fill bar color in media node
	'structure_freezecolor': (200, 200, 200), # Freeze color in media node
	'structure_repeatcolor': (100, 100, 100), # Repeat color in media node
	'structure_trunccolor': (255,0,0), # Indication that node is truncated
	'structure_ecbordercolor': (40, 40, 40), # triangle border (not used?)
	'structure_focusleft': (200, 200, 200),	# left edge of 3D focus border
	'structure_focustop': (200, 200, 200), # top edge of 3D focus border
	'structure_focusright': (40, 40, 40), # right edge of 3D focus border
	'structure_focusbottom': (40, 40, 40), # bottom edge of 3D focus border
	'structure_dropcolor': (0, 0, 0), # drop target border color

	'structure_bandwidthfree': (150, 150, 150),
	'structure_bandwidthok': (0, 100, 0),
	'structure_bandwidthnotok': (100, 0, 0),
	'structure_bandwidthmaybeok': (100, 60, 0),
	'structure_bandwidthokfocus': (0, 200, 0),
	'structure_bandwidthnotokfocus': (200, 0, 0),
	'structure_bandwidthmaybeokfocus': (200, 120, 0),
	'structure_bwprerollcolor': (255, 160, 0),
	'structure_bwmaystallcolor': (255, 160, 0),
	'structure_bwstallcolor': (255, 0, 0),

	# Locations on the net
	'templatedir_url': 'http://www.oratrix.com/indir/images',
	'openviews' : [('structure', (-1, -1, -1, -1))],	# Default views to open
	'saveopenviews': 0,
	'showsource' : 0,	# Hidden preference to show source window in the player

	# The temporal view
	'temporal_barwidth': 5,		# width of the sync bars
	'temporal_channelwidth':100,	# Width of the channels. If channels are made Hierarchical, this may change.
	'temporal_nodestart': 102,	# Where the first bar is
	'temporal_nodeend' : 1000,	# Where the last bar is.
	'temporal_backgroundcolor' : (227,223,145),	# The color of the background
	'temporal_channelcolor': (232, 193,152),	# Color of the channels
	'temporal_channelheight': 16,	# Height of the channels
	'temporal_nodecolor': (205,207,194),		# the color of each node
	'temporal_parcolor': (79,156,130),
	'temporal_seqcolor': (116,154,189),
	'temporal_exclcolor': (148,117,166),
	'temporal_priocolor': (166,61,126),
	'temporal_switchcolor': (148,117,166),
	'temporal_timescale': 5,	# pixels per second.
	'temporal_fillcolor': (150,150,150), # The color a node is for it's fill segment.
	
	# Attribute editor prefs
	'show_all_attributes' : 1,
	'enable_template': 0,
	'registered': 'notyet',
}

# Set cpu/os type
if sys.platform == 'win32':
	default_settings['system_cpu'] = 'x86'
	default_settings['system_operating_system'] = 'win32'
	default_settings['savedir'] = 'Desktop'
elif sys.platform == 'mac':
	default_settings['system_cpu'] = 'ppc'
	default_settings['system_operating_system'] = 'macos'
	default_settings['savedir'] = '???'
else:
	default_settings['savedir'] = os.getenv('HOME')
# Don't set for other platforms (yet)

user_settings = {}

# Which of these should match exactly:
EXACT=['system_captions', 'system_overdub_or_caption',
       'system_audiodesc']
LANGUAGE=['system_language']
ALL=['system_bitrate', 'system_captions', 'system_language',
     'system_overdub_or_caption', 'system_screen_size',
     'system_screen_depth', 'system_required', 'system_audiodesc',
     'system_operating_system', 'system_cpu', 'system_component']

NEEDS_RESTART=['cmif', 'vertical_structure', 'no_canvas_resize', 'root_expanded']

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
	if not user_settings:
		# no change
		return
	if not transaction(auto=1):
		return
	user_settings = {}
	commit(auto=1)

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

components = ['http://www.oratrix.com/GRiNS/smil2.0']

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
		from SMIL import extensions
		for v in wanted_value:
			if not extensions.get(v, 0):
				return 0
		return 1
	if name == 'system_component':
		if wanted_value:
			for val in wanted_value.split():
				if val not in components:
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
	if user_settings.get(setting) == value:
		# no change
		return
	if not transaction(auto=1):
		return
	if setting in NEEDS_RESTART and value != get(setting) and not _warned_already:
		_warned_already = 1
		windowinterface.showmessage('You have to restart GRiNS for some of these changes to take effect.')
	user_settings[setting] = value
	commit(auto=1)

def delete(setting):
	if user_settings.has_key(setting):
		if not transaction(auto=1):
			return
		del user_settings[setting]
		commit(auto=1)

def save():
	import windowinterface
	if hasattr(windowinterface, 'is_embedded') and windowinterface.is_embedded():
		# don't save when embedded
		return 1
	try:
		fp = open(PREFSFILENAME, 'w')
	except IOError:
		return 0
	for name, value in user_settings.items():
		if not default_settings.has_key(name) or value != default_settings[name]:
			fp.write('%s = %s\n'%(name, `value`))
	fp.close()
	return 1

def register(listener):
	if not listener in _registry:
		_registry.append(listener)

def unregister(listener):
	while listener in _registry:
		_registry.remove(listener)

def transaction(auto=0):
	global _in_transaction
	if auto and _in_transaction:
		return 1
	if not auto:
		if _in_transaction:
			raise 'recursive preference transaction'
		_in_transaction = 1
	for listener in _registry:
		if not listener.transaction('preference'):
			return 0
	return 1

def commit(auto=0):
	global _in_transaction
	if auto and _in_transaction:
		return
	if not auto and not _in_transaction:
		raise 'Not in preference transaction'
	_in_transaction = 0
	for listener in _registry:
		listener.commit('preference')
