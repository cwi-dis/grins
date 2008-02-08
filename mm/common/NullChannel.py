__version__ = "$Id$"

from Channel import Channel

class NullChannel(Channel):
    def getaltvalue(self, node):
        return 0
