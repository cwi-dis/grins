import os
debug = os.environ.has_key('CHANNELDEBUG')
from Channel import *
import string
import sys
import MMAttrdefs
from AnchorDefs import *


class CmifChannel(Channel):

	def __init__(self, name, attrdict, scheduler, ui):
		Channel.__init__(self, name, attrdict, scheduler, ui)
		self.stopped = 0
	
	def do_arm(self, node, same = 0):
		if node.GetType() == 'imm':
			cmds = node.GetValues()
		else:
			filename = self.getfileurl(node)
			try:
				fp = urlopen(filename)
			except IOError, msg:
				self.errormsg(node, filename + ':\n' + msg)
				cmds = []
			else:
				cmds = fp.readlines()
				fp.close()
		self.cmds = cmds
		return 1

	def do_play(self, node):
		cmds = self.cmds
		for cmd in cmds:
			if not cmd:
				continue
			fields = string.split(cmd)
			arg = cmd[len(fields[0]):]
			arg = string.strip(arg)
			if fields[0] == 'show':
			        self._player.cc_enable_ch(arg, 1)
			elif fields[0] == 'hide':
			        self._player.cc_enable_ch(arg, 0)
			elif fields[0] == 'stop':
				self._player.cc_stop()
				self.stopped = 1
			elif fields[0] == 'exit':
				self._player.toplevel.main.do_exit()
			else:
				print 'CmifChannel: bad cmd:', cmd
				return

	# redefine play so that we can implement "stop" properly
	def play(self, node):
		if debug:
			print 'CmifChannel.play('+`self`+','+`node`+')'
		self.stopped = 0
		self.play_0(node)
		self.do_play(node)
		if not self.stopped:
			self.armdone()
			self.playdone(0)
