from debug import debug
from Channel import *
import string
import sys
import dialogs
import MMAttrdefs
import socket
from AnchorDefs import *


class SocketChannel(Channel):
	chan_attrs = Channel.chan_attrs + ['port']
	
	def init(self, name, attrdict, scheduler, ui):
		self = Channel.init(self, name, attrdict, scheduler, ui)
		self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		if attrdict.has_key('port'):
			port = attrdict['port']
		else:
			port = 7000
		self.socket.bind(('', port))
		toplevel = self._player.toplevel
		toplevel.select_setcallback(self.socket, self.socket_ready, ())
		self.anchorlist = None
		return self

	def __repr__(self):
		return '<SocketChannel instance, name=' + `self._name` + '>'

	def socket_ready(self, *dummy):
		rv = self.socket.recv(10000)
		print 'SocketChannel: recv:', rv
		fields = string.split(rv)
		cmd = fields[0]
		if cmd == 'anchor':
			if len(fields) == 2:
				name = fields[1]
				for a in self.anchorlist:
					if a[A_ID] == name:
						self._playcontext.anchorfired(\
						    self._played_node, [a])
						return
			dialogs.showmessage('SocketChannel: no such anchor\n'+
				  rv)
		else:
			dialogs.showmessage('SocketChannel: unknown command\n'+
				  rv)

	def do_arm(self, node):
		return 1

	def do_play(self, node):
		self.anchorlist = node.GetRawAttr('anchorlist')
		modanchorlist(self.anchorlist)

	def playstop(self):
		self.anchorlist = None
		Channel.playstop(self)
