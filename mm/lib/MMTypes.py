__version__ = "$Id$"

mediatypes = ['imm', 'ext', 'brush']
leafcontroltypes = ['prefetch', 'animate']
leaftypes = mediatypes + leafcontroltypes
bagtypes = ['bag']
interiortypes = ['seq', 'par', 'switch', 'excl', 'prio'] + bagtypes
playabletypes = leaftypes + bagtypes
partypes = ['par'] + leaftypes
alltypes = leaftypes + interiortypes
