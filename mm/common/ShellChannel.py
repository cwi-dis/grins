# Shell channel

# This lets you run a shell command.

import time
import os
import string
from Channel import Channel
import MMAttrdefs


class ShellChannel(Channel):

	# Declaration of attributes that are relevant to this channel,
	# respectively to nodes belonging to this channel.

	chan_attrs = []
	node_attrs = ['duration', 'file']

	def init(self, name, attrdict, player):
		self.pid = None
		return Channel.init(self, name, attrdict, player)

	def __repr__(self):
		return '<ShellChannel instance, name=' + `self.name` + '>'

	def play(self, node, callback, arg):
		self.pid = None
		if self.is_showing():
			type = node.GetType()
			if type == 'imm':
				list = node.GetValues()
				cmd = string.joinfields(list, '\n') + '\n'
				prog = '/bin/sh'
				argv = ['sh', '-c', cmd]
			else:
				prog = \
				    self.player.toplevel.getattr(node, 'file')
				argv = [prog]
			self.pid = startprog(prog, argv)
		Channel.play(self, node, callback, arg)

	def done(self, dummy):
		if self.pid:
			try:
				pid, sts = os.waitpid(self.pid, 1)
			except os.error, msg:
				print 'waitpid:', msg
				pid, sts = 0, 0
			if pid == 0:
				# Try again in a second
				self.qid = \
					self.player.enter(1, 0, self.done, 0)
				return
			if sts <> 0:
				print 'Exit status:', hex(sts)
		self.pid = None
		Channel.done(self, dummy)

	def stop(self):
		if self.pid:
			try:
				os.kill(self.pid, 15)
				time.millisleep(300)
				pid, sts = os.waitpid(self.pid, 1)
				if pid == 0:
					time.millisleep(700)
					pid, sts = os.waitpid(self.pid, 1)
				if pid == 0:
					os.kill(self.pid, 9)
					pid, sts = os.waitpid(self.pid, 0)
			except os.error, msg:
				print 'kill:', msg
		self.pid = None
		Channel.stop(self)


def startprog(prog, argv):
	try:
		pid = os.fork()
	except os.error, msg:
		print 'fork:', msg
		return None
	if pid == 0: # Child
		os.exec(prog, argv)
		# Not reached
	else: # Parent
		return pid
