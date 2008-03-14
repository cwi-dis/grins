__version__ = "$Id$"

mediatypes = ['imm', 'ext', 'brush']    # types that want a region
leafcontroltypes = ['prefetch', 'animate', 'state'] # pseudo-media
interiortypes = ['seq', 'par', 'switch', 'excl', 'prio']
playabletypes = mediatypes + leafcontroltypes # types that can be played
playtypes = playabletypes + ['anchor']  # types that can be played on a channel (anchor is special case)
termtypes = ['par', 'excl'] + mediatypes # types that can have a terminator attribute
alltypes = playtypes + interiortypes    # everything
