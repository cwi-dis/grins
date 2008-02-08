__version__ = "$Id$"

from Channel import Channel

class SocketChannel(Channel):
    def __repr__(self):
        return '<Dummy SocketChannel instance, name=' + `self._name` + '>'
