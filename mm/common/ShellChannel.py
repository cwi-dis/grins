__version__ = "$Id$"

import os
debug = os.environ.has_key('CHANNELDEBUG')
from Channel import Channel
import string
import os

class ShellChannel(Channel):
	def __init__(self, name, attrdict, scheduler, ui):
		self.pid = None
		Channel.__init__(self, name, attrdict, scheduler, ui)

	def do_play(self, node):
		self.pid = None
		type = node.GetType()
		if type == 'imm':
			list = node.GetValues()
			cmd = string.joinfields(list, '\n') + '\n'
			prog = '/bin/sh'
			argv = ['sh', '-c', cmd]
		else:
			import MMurl
			prog = self.getfileurl(node)
			prog = MMurl.urlretrieve(prog)[0]
			argv = [prog]
		self.pid = startprog(prog, argv)

	def playdone(self, dummy):
		if debug:
			print 'ShellChannel.playdone('+`self`+')'
		if self.pid:
			try:
				pid, sts = os.waitpid(self.pid, 0100)
			except os.error, msg:
				print 'waitpid:', msg[1]
				pid, sts = 0, 0
			if pid == 0:
				# Try again in a second
				self._qid = self._scheduler.enter(1, 0, \
					self.playdone, (0,))
				return
			if sts <> 0:
				print 'Exit status:', hex(sts)
		self.pid = None
		Channel.playdone(self, dummy)

	def playstop(self):
		if debug:
			print 'ShellChannel.playstop('+`self`+')'
		if self.pid:
			import time
			try:
				os.kill(self.pid, 15)
				time.sleep(0.300)
				pid, sts = os.waitpid(self.pid, 1)
				if pid == 0:
					time.sleep(0.700)
					pid, sts = os.waitpid(self.pid, 1)
				if pid == 0:
					os.kill(self.pid, 9)
					pid, sts = os.waitpid(self.pid, 0)
			except os.error, msg:
				print 'kill:', msg[1]
		self.pid = None
		Channel.playstop(self)

def startprog(prog, argv):
	try:
		pid = os.fork()
	except os.error, msg:
		print 'fork:', msg[1]
		return None
	except AttributeError:
		print 'ShellChannel cannot work on this system'
		return None
	if pid == 0: # Child
		os.execv(prog, argv)
		# Not reached
	else: # Parent
		return pid
