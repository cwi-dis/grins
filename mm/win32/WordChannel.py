
import os
debug = os.environ.has_key('CHANNELDEBUG')
from Channel import Channel
import string
import os, sys
import urllib
import wordC

from windowinterface import *

class WordChannel(Channel):
	def __init__(self, name, attrdict, scheduler, ui):
		self.word = None
		self.success = None
		Channel.__init__(self, name, attrdict, scheduler, ui)

	def __repr__(self):
		return '<WordChannel instance, name=' + `self._name` + '>'

	def do_play(self, node):
		self.word = None
		type = node.GetType()
		if type == 'imm':
			list = node.GetValues()		
			prog = string.joinfields(list, ' ') 			
		else:
			prog = self.getfileurl(node)
			print "Prog: ", prog
			prog = urllib.url2pathname(prog)
		print "Program: ", prog
		self.word = wordC.Word(1, prog)
				

	def playdone(self, dummy):
		if debug:
			print 'WordChannel.playdone('+`self`+')'
		#Just for the review
		#self.word = None
		Channel.playdone(self, dummy)

	def playstop(self):
		if debug:
			print 'WordChannel.playstop('+`self`+')'
		self.word = None
		Channel.playstop(self)
	