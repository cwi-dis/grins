from Channel import Channel

class PythonChannel(Channel):
	def __repr__(self):
		return '<PythonChannel instance, name=' + `self._name` + '>'
