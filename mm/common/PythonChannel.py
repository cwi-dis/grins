from Channel import Channel
import string
from MMExc import *			# exceptions

class PythonChannel(Channel):
	def __repr__(self):
		return '<PythonChannel instance, name=' + `self._name` + '>'

	def seekanchor(self, node, aid, args):
		self.seekargs = args
		
	def do_play(self, node):
		if node.GetType() <> 'imm':
			print 'PythonChannel: imm nodes only'
		cmds = node.GetValues()
		cmds = string.join(cmds, '\n')

		try:
			args = self.seekargs
			self.seekargs = ()
		except AttributeError:
			args = ()

		try:
			alist = node.GetRawAttr('anchorlist')
		except NoSuchAttrError:
			alist = []
			
		namespace = {
			"channel": self,
			"player": self._player,
			"node": node,
			"toplevel": self._player.toplevel,
			"anchors": alist,
			"args":args}
		
		exec cmds in namespace, namespace
