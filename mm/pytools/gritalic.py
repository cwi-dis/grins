# gritalic - Italicize the "i" in GRiNS
import re

_find_italic = re.compile('GR<[iI]>i</[iI]>NS')
_find_nonitalic = re.compile('GRiNS')

def italic(str):
    """Replace GRiNS by GR<i>i</i>NS"""
    return _find_nonitalic.sub('GR<i>i</i>NS', str, 9999)

def nonitalic(str):
    """Replace GR<i>i</i>NS by GRiNS"""
    return _find_italic.sub('GRiNS', str, 9999)

# Test code, run as main program to use
if __name__ == '__main__':
    import sys
    print 'ARGS:'
    for i in sys.argv[1:]: print i
    print 'ITALIC:'
    for i in sys.argv[1:]: print italic(i)
    print 'NONITALIC:'
    for i in sys.argv[1:]: print nonitalic(i)
