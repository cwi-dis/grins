__version__ = "$Id$"

from Channel import Channel, PLAYING
import string
from MMExc import *			# exceptions
import sys

class PythonChannel(Channel):
	def do_play(self, node):
		if node.GetType() <> 'imm':
			print 'PythonChannel: imm nodes only'
		cmds = node.GetValues()
		cmds = string.join(cmds, '\n')

		if self.seekargs and self.seekargs[0] is node:
			args = self.seekargs[2]
		else:
			args = ()
		self.seekargs = None

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
