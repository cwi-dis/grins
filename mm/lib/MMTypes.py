__version__ = "$Id$"

mediatypes = ['imm', 'ext', 'brush']
leafcontroltypes = ['prefetch', 'animate']
leaftypes = mediatypes + leafcontroltypes
bagtypes = ['bag']
interiortypes = ['seq', 'par', 'alt', 'excl', 'prio'] + bagtypes
playabletypes = leaftypes + bagtypes
alltypes = leaftypes + interiortypes
