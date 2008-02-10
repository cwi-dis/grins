__version__ = "$Id$"

# Convert externally visible representations of
# system test attribute values to internal ones
# and vice versa

import bitrates
import languages

# Per system test attribute we have a tuple
# with first an internal-to-external mapping and
# then an external-to-internal mapping.

def _revdict(dict):
    rv = {}
    for k, v in dict.items():
        rv[v] = k
    return rv

_bool_a2l = {
        0: "off",
        1: "on"
}

_bool_l2a = _revdict(_bool_a2l)

_ooc_a2l = {
        "overdub": "Overdub preferred",
        "caption": "Caption preferred",
}

_ooc_l2a = _revdict(_ooc_a2l)

_ssc_a2l = {
        (300, 200) : "Handheld (300x200)",
        (640, 480) : "Small (640x480)",
        (800, 600) : "Medium (800x600)",
        (1024, 768): "Standard (1024x768)",
        (1280, 1024): "Large (1280x1024)",
        (1600, 1024): "Superwide (1600x1024)",
}

_ssc_l2a = _revdict(_ssc_a2l)

_ssd_a2l = {
        1: "Black/white",
        8: "8 bit",
        24: "24 bit",
}

_ssd_l2a = _revdict(_ssd_a2l)


_os_a2l = {
        'win32': 'Windows',
        'win9x': 'Windows 95/98/ME',
        'winnt': 'Windows NT',
        'wince': 'Windows CE',
        'linux': 'Linux',
        'macos': 'Mac OS',
        'palmos': 'Palm OS'
}

_os_l2a = _revdict(_os_a2l)

_cpu_a2l = {
        'x86': 'Intel *86/Pentium',
        'ppc': 'PowerPC'
}

_cpu_l2a = _revdict(_cpu_a2l)

_mappings = {
        'system_bitrate': (bitrates.a2l, bitrates.l2a),
        'system_language': (languages.a2l, languages.l2a),
        'system_audiodesc': (_bool_a2l, _bool_l2a),
        'system_captions': (_bool_a2l, _bool_l2a),
        'system_overdub_or_caption': (_ooc_a2l, _ooc_l2a),
        'system_screen_size': (_ssc_a2l, _ssc_l2a),
        'system_screen_depth': (_ssd_a2l, _ssd_l2a),
        'system_operating_system': (_os_a2l, _os_l2a),
        'system_cpu': (_cpu_a2l, _cpu_l2a),
        'system_required': ({}, {}),
        'system_component': ({}, {}),

}

_testname2ext = (
        ('system_bitrate', 'Bitrate'),
        ('system_language', 'Language'),
        ('system_audiodesc', 'Audio descriptions'),
        ('system_captions', 'Captions'),
        ('system_overdub_or_caption', 'Caption/overdub preference'),
        ('system_screen_size', 'Screen size'),
        ('system_screen_depth', 'Screen depth'),
        ('system_operating_system', 'Operating system'),
        ('system_cpu', 'Processor'),
        ('system_required', 'Required extensions'),
        ('system_component', 'Required components'),
)

def getallexternal(attrname):
    if not _mappings.has_key(attrname):
        raise 'Unknown system test attribute', attrname
    a2l = _mappings[attrname][0]
    # Languages we sort in order of externally visible
    # name
    if attrname == 'system_language':
        rv = a2l.values()
        rv.sort()
        return rv
    # Return the rest in ascending internal value order
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
        ext = 'Current system default (%s)'%(value,)
        a2l[value] = ext
        l2a = _mappings[attrname][1]
        l2a[ext] = value
    return a2l[value]

def ext2intvalue(attrname, value):
    if not _mappings.has_key(attrname):
        raise 'Unknown system test attribute', attrname
    l2a = _mappings[attrname][1]
    if not l2a.has_key(value):
        print 'Unknown value for system test attribute', (attrname, value)
        assert 0
        value = a2l.keys[0]
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
