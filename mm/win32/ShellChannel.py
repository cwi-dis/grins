
import os
debug = os.environ.has_key('CHANNELDEBUG')
from Channel import Channel
import string
import os
import urllib
import win32api, win32con

[ WINNT, WIN95] = range(2)

class ShellChannel(Channel):
	def __init__(self, name, attrdict, scheduler, ui):
		self.pid = None
		self.success = None
		Channel.__init__(self, name, attrdict, scheduler, ui)

	def __repr__(self):
		return '<ShellChannel instance, name=' + `self._name` + '>'

	def do_play(self, node):
		self.pid = None
		type = node.GetType()
		if type == 'imm':
			list = node.GetValues()
			#cmd = string.joinfields(list, '\n') + '\n'
			cmd = string.joinfields(list, ' ') 

			#prog = '/bin/sh'
			#argv = ['sh', '-c', cmd]
			#print cmd
			
			argv = []
			argv.append(cmd) 
			#print 'cmd is'
			prog =""
 			#prog = self.getfileurl(node)
			#prog = urllib.url2pathname(prog)
		else:
			#prog = self.getfileurl(node)
			#prog = urllib.url2pathname(prog)
			prog =""
			argv = [prog]
		self.pid = startprog(prog, argv)

	def playdone(self, dummy):
		if debug:
			print 'ShellChannel.playdone('+`self`+')'
		self.pid = None
		Channel.playdone(self, dummy)

	def playstop(self):
		if debug:
			print 'ShellChannel.playstop('+`self`+')'
		self.pid = None
		Channel.playstop(self)

def startprog(prog, argv):
	l = win32api.GetVersionEx()
	osVersion = win32api.HIWORD(l[2])
	print argv[0]

	com = argv[0]
	#if osVersion == WINNT:
	#	com = "start "+ argv[0]

	win32api.WinExec(com, win32con.SW_SHOWNORMAL)

	return 0
	#return os.system(com)
		