__version__ = "$Id$"

mediatypes = ['imm', 'ext', 'brush']
leafcontroltypes = ['prefetch', 'animate']
leaftypes = mediatypes + leafcontroltypes
interiortypes = ['seq', 'par', 'switch', 'excl', 'prio']
playabletypes = leaftypes
partypes = ['par'] + leaftypes
alltypes = leaftypes + interiortypes
