from debug import debug
from Channel import *
import string
import sys
import MMAttrdefs
from AnchorDefs import *


class CmifChannel(Channel):

	# Inherit init method
	
	def __repr__(self):
		return '<CmifChannel instance, name=' + `self._name` + '>'

	def do_play(self, node):
		if node.GetType() <> 'imm':
			return
		cmds = node.GetValues()
		for cmd in cmds:
			if not cmd:
				continue
			fields = string.split(cmd)
			if fields[0] == 'show':
				for ch in fields[1:]:
					self._player.cc_enable_ch(ch, 1)
			elif fields[0] == 'hide':
				for ch in fields[1:]:
					self._player.cc_enable_ch(ch, 0)
##			elif fields[0] == 'stop':
##				self._player.cc_stop()
			else:
				print 'CmifChannel: bad cmd:', cmd
				return
