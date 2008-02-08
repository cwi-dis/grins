__version__ = "$Id$"

def what(file):
    if type(file) == type(''):
        pos = -1
        file = open(file, 'rb')
        h = file.read(512)
    else:
        # assume it's a file object
        pos = file.tell()
        h = file.read(512)
    try:
        for tf in tests:
            res = tf(h, file)
            if res:
                return res
    finally:
        if pos >= 0:
            file.seek(pos)
        else:
            file.close()
    return None

tests = []

def test_aifc(h, f):
    if h[:4] <> 'FORM':
        return None
    if h[8:12] == 'AIFC':
        return 'aifc'
    elif h[8:12] == 'AIFF':
        return 'aiff'
    else:
        return None
tests.append(test_aifc)

def test_au(h, f):
    if h[:4] in ('.snd', 'dns.'):
        return 'au'
    return None
tests.append(test_au)

def test_hcom(h, f):
    if h[65:69] == 'FSSD' and h[128:132] == 'HCOM':
        return 'hcom'
    return None
tests.append(test_hcom)

def test_voc(h, f):
    if h[:20] == 'Creative Voice File\032':
        return 'voc'
    return None
tests.append(test_voc)

def test_wav(h, f):
    # 'RIFF' <len> 'WAVE' 'fmt ' <len>
    if h[:4] == 'RIFF' and h[8:12] == 'WAVE' and h[12:16] == 'fmt ':
        return 'wav'
    return None
tests.append(test_wav)

def test_8svx(h, f):
    if h[:4] == 'FORM' and h[8:12] == '8SVX':
        return '8svx'
    return None
tests.append(test_8svx)

def test_sndt(h, f):
    if h[:5] == 'SOUND':
        return 'sndt'
    return None
tests.append(test_sndt)

def test_sndr(h, f):
    if h[:2] == '\0\0':
        rate = get_short_le(h[2:4])
        if 4000 <= rate <= 25000:
            return 'sndr'
tests.append(test_sndr)

#---------------------------------------------#
# Subroutines to extract numbers from strings #
#---------------------------------------------#

def get_long_be(s):
    return (ord(s[0])<<24) | (ord(s[1])<<16) | (ord(s[2])<<8) | ord(s[3])

def get_long_le(s):
    return (ord(s[3])<<24) | (ord(s[2])<<16) | (ord(s[1])<<8) | ord(s[0])

def get_short_be(s):
    return (ord(s[0])<<8) | ord(s[1])

def get_short_le(s):
    return (ord(s[1])<<8) | ord(s[0])
