__version__ = "$Id$"

bitrates = [
        (14400, '14.4K Modem'),
        (19200, '19.2K Connection'),
        (28800, '28.8K Modem'),
        (33600, '33.6K Modem'),
        (34400, '56K Modem'),
        (57600, '56K Single ISDN'),
        (115200, '112K Dual ISDN'),
        (262200, '256Kbps DSL/Cable'),
        (307200, '300Kbps DSL/Cable'),
        (524300, '512Kbps DSL/Cable'),
        (1544000, 'T1 / LAN'),
        (10485800, '10Mbps LAN'),
]

a2l = {}
l2a = {}
rates = []
names = []
for _a, _l in bitrates:
    a2l[_a] = _l
    l2a[_l] = _a
    rates.append(_a)
    names.append(_l)
