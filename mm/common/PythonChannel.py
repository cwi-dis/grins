from Channel import Channel, PLAYING
import string
from MMExc import *			# exceptions
import sys

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
		try:
			exec cmds in namespace, namespace
		except:
			# XXXX Should be done in editor only, and after
			# asking the user whether this is ok.
			print "EXCEPTION IN PYTHONCHANNEL NODE"
			import pdb
			pdb.post_mortem(sys.exc_traceback)
			

	def play_1(self):
		# It could be we jumped away so are not playing anymore
		if self._playstate == PLAYING:
			Channel.play_1(self)
