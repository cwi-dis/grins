from debug import debug
from Channel import *
import string
import sys
import MMAttrdefs
from AnchorDefs import *


class CmifChannel(Channel):

	def init(self, name, attrdict, scheduler, ui):
		self = Channel.init(self, name, attrdict, scheduler, ui)
		self.stopped = 0
		return self
	
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
			elif fields[0] == 'stop':
				self._player.cc_stop()
				self.stopped = 1
			elif fields[0] == 'exit':
				import windowinterface
				windowinterface.enterevent(None,
						       EVENTS.WindowExit, None)
			else:
				print 'CmifChannel: bad cmd:', cmd
				return

	# redefine play so that we can implement "stop" properly
	def play(self, node):
		if debug:
			print 'CmifChannel.play('+`self`+','+`node`+')'
		self.play_0(node)
		self.do_play(node)
		if not self.stopped:
			self.armdone()
			self.playdone(0)
