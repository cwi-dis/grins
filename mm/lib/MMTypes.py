__version__ = "$Id$"

leaftypes = ['imm', 'ext']
bagtypes = ['bag']
interiortypes = ['seq', 'par', 'alt', 'excl', 'prio'] + bagtypes
playabletypes = leaftypes + bagtypes
alltypes = leaftypes + interiortypes
