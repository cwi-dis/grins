from Channel import Channel
import string

class PythonChannel(Channel):
	def __repr__(self):
		return '<PythonChannel instance, name=' + `self._name` + '>'

	def do_play(self, node):
		if node.GetType() <> 'imm':
			print 'PythonChannel: imm nodes only'
		cmds = node.GetValues()
		cmds = string.join(cmds, '\n')
		exec cmds
