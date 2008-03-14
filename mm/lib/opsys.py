__version__ = "$Id$"

opsys = {
    'AIX': 0,
    'BEOS': 0,
    'BSDI': 0,
    'DARWIN': 0,
    'DGUX': 0,
    'FREEBSD': 0,
    'HPUX': 0,
    'IRIX': 0,
    'L4ENV': 0,
    'LINUX': 0,
    'MACOS': 0,
    'NCR': 0,
    'NEC': 0,
    'NETBSD': 0,
    'NEXTSTEP': 0,
    'NTO': 0,
    'OPENBSD': 0,
    'OPENVMS': 0,
    'OS2': 0,
    'OSF': 0,
    'PALMOS': 0,
    'QNX': 0,
    'SINIX': 0,
    'RHAPSODY': 0,
    'SCO': 0,
    'SOLARIS': 0,
    'SONY': 0,
    'SUNOS': 0,
    'UNIXWARE': 0,
    'WIN16': 0,
    'WIN32': 0,
    'WIN9X': 0,
    'WINNT': 0,
    'WINCE': 0,
    'UNKNOWN': 1,
    }
cpu = {
    'ALPHA': 0,
    'ARM': 0,
    'ARM32': 0,
    'HPPA': 0,
    'HPPA1.1': 0,
    'IA64': 0,
    'M68K': 0,
    'MIPS': 0,
    'PPC': 0,
    'RS6000': 0,
    'S390': 0,
    'S390X': 0,
    'SPARC': 0,
    'VAX': 0,
    'X86': 0,
    'X86-64': 0,
    'UNKNOWN': 1,
    }

import os, sys

# XXX cpu checks should be done better
try:
    uname = os.uname()
except AttributeError:
    uname = None

if uname is not None and uname[4] in ('i686', 'i386'):
    cpu['X86'] = 1
    cpu['UNKNOWN'] = 0
elif uname is not None and cpu.has_key(uname[4].upper()):
    cpu[uname[4].upper()] = True
    cpu['UNKNOWN'] = 0
elif sys.platform == 'win32':
    cpu['X86'] = 1
    cpu['UNKNOWN'] = 0
elif sys.platform == 'win16':
    cpu['X86'] = 1
    cpu['UNKNOWN'] = 0
if uname is not None and opsys.has_key(uname[0].upper()):
    opsys[uname[0].upper()] = 1
    opsys['UNKNOWN'] = 0
elif sys.platform == 'win32':
    opsys['WIN32'] = 1
    if os.name == 'nt':
        opsys['WINNT'] = 1
    else:
        opsys['WIN9X'] = 1
    opsys['UNKNOWN'] = 0
elif sys.platform == 'win16':
    opsys['WIN16'] = 1
    opsys['UNKNOWN'] = 0
