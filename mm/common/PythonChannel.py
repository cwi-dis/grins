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

		namespace = {
			"channel": self,
			"player": self._player,
			"node": node,
			"toplevel": self._player.toplevel,
			"anchors": node.GetRawAttrDef('anchorlist', []),
			"args":args}
		try:
			exec cmds in namespace, namespace
		except:
			# XXXX Should be done in editor only, and after
			# asking the user whether this is ok.
			print "EXCEPTION IN PYTHONCHANNEL NODE", \
			      node.GetAttrDef('name', '<unnamed node>')
			if __debug__:
				import pdb
				pdb.post_mortem(sys.exc_traceback)
			else:
				import traceback
				apply(traceback.print_exception,
				      sys.exc_info())


	def play_1(self):
		# It could be we jumped away so are not playing anymore
		if self._playstate == PLAYING:
			Channel.play_1(self)
