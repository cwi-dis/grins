from Channel import Channel

class NullChannel(Channel):
	def __repr__(self):
		return '<NullChannel instance, name=' + `self._name` + '>'
