# Convert externally visible representations of
# system test attribute values to internal ones
# and vice versa

import bitrates
import languages

# Per system test attribute we have a tuple
# with first an internal-to-external mapping and
# then an external-to-internal mapping.
_mappings = {
	'system_bitrate': (bitrates.a2l, bitrates.l2a),
	'system_language': (languages.a2l, languages.l2a),
}

_testname2ext = (
	('system_bitrate', 'Bitrate'),
	('system_language', 'Language'),
)
	

def getallexternal(attrname):
	if not _mappings.has_key(attrname):
		raise 'Unknown system test attribute', attrname
	a2l = _mappings[attrname][0]
	# Return them in ascending internal value order
	values = a2l.keys()
	values.sort()
	rv = []
	for v in values:
		rv.append(a2l[v])
	return rv

def int2extvalue(attrname, value):
	if not _mappings.has_key(attrname):
		raise 'Unknown system test attribute', attrname
	a2l = _mappings[attrname][0]
	if not a2l.has_key(value):
		raise 'Unknown value for system test attribute', (attrname, value)
	return a2l[value]

def ext2intvalue(attrname, value):
	if not _mappings.has_key(attrname):
		raise 'Unknown system test attribute', attrname
	l2a = _mappings[attrname][1]
	if not l2a.has_key(value):
		raise 'Unknown value for system test attribute', (attrname, value)
	return l2a[value]

def int2extattr(attrname):
	for i, e in _testname2ext:
		if i == attrname:
			return e
	raise 'Unknown system test attribute', attrname

def ext2intattr(extname):
	for i, e in _testname2ext:
		if e == attrname:
			return i
	raise 'Unknown system test external name', extname