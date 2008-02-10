__version__ = "$Id$"

#
#       SVGChannel
#

from Channel import Channel

class SVGChannel(Channel):
    def getaltvalue(self, node):
        return 0
