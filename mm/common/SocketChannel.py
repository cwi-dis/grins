__version__ = "$Id$"

from Channel import *
import string
import sys
import windowinterface
import MMAttrdefs
import socket
from AnchorDefs import *


class SocketChannel(Channel):
	chan_attrs = Channel.chan_attrs + ['port', 'nonlocal', \
		  'mcgroup', 'mcttl']
	node_attrs = Channel.node_attrs + ['duration']

	def __init__(self, name, attrdict, scheduler, ui):
		Channel.__init__(self, name, attrdict, scheduler, ui)
		self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		if hasattr(socket, 'SO_REUSEPORT'):
			self.socket.setsockopt(socket.SOL_SOCKET,
					       socket.SO_REUSEPORT, 1)
		if attrdict.has_key('port'):
			port = attrdict['port']
		else:
			port = 7000
		try:
			self.socket.bind(('', port))
		except socket.error, arg:
			windowinterface.showmessage('Cannot open socket '+`port`+': '+\
				  `arg`)
			self.socket = None
			return
		windowinterface.select_setcallback(self.socket,
						   self.socket_ready, ())
		self.anchorlist = None
		self.hostaddr = socket.gethostbyname(socket.gethostname())
		self.nonlocalonly = 0
		if attrdict.has_key('nonlocal'):
			self.nonlocalonly = attrdict['nonlocal']
		if attrdict.has_key('mcttl'):
			ttl = attrdict['mcttl']
		else:
			ttl = 3
		if attrdict.has_key('mcgroup'):
			mcgroup = attrdict['mcgroup']
			addgroup(self.socket, mcgroup, ttl)
		return

	def destroy(self):
		if self.socket:
			windowinterface.select_setcallback(self.socket,
							   None, ())
			self.socket.close()
		del self.socket
		Channel.destroy(self)

	def socket_ready(self):
		rv, (shost, sport) = self.socket.recvfrom(10000)
		if self.nonlocalonly and shost == self.hostaddr:
			return
		fields = string.split(rv)
		cmd = fields[0]
		if cmd == 'anchor':
			if not self._played_node:
				windowinterface.showmessage('SocketChannel: no node playing\n')
				return
			if len(fields) == 2:
				name = fields[1]
				for nm, tp, bt in self._played_anchors:
					if nm == name:
						self._playcontext.anchorfired(\
						    self._played_node, \
						    [(nm,tp)], None)
						return
			windowinterface.showmessage('SocketChannel: no such anchor\n'+
				  rv)
		else:
			windowinterface.showmessage('SocketChannel: unknown command\n'+
				  rv)

	def do_arm(self, node, same=0):
		alist =  MMAttrdefs.getattr(node, 'anchorlist')
		for a in alist:
			self.setanchor(a[A_ID], a[A_TYPE], None)
		return 1

	def do_play(self, node):
		if not self.socket:
			return
		if node.GetType() <> 'imm':
			return
		cmds = node.GetValues()
		for cmd in cmds:
			if not cmd:
				continue
			fields = string.split(cmd)
			if fields[0] == 'send':
				if len(fields) < 3:
					print 'SocketChannel: bad cmd:', cmd
					return
				host = fields[1]
				try:
					port = eval(fields[2])
				except:
					print 'SocketChannel: bad port:', fields[2]
					return
				data = string.join(fields[3:])
				self.socket.sendto(data, (host, port))
			else:
				print 'SocketChannel: bad cmd:', cmd
				return


	def playstop(self):
		self.anchorlist = None
		Channel.playstop(self)
#
# Helper routines for multicast support.

import regsub
import IN
import struct
#
# Convert dotted-form inet address to binary
def dotted_to_binary(addr):
	group_bytes = eval(regsub.gsub('\.', ',', addr))
	group_addr = 0
	for i in group_bytes: group_addr = (group_addr<<8) | i
	return group_addr

def addgroup(sock, mcaddr, ttl):
	iface = socket.gethostbyname(socket.gethostname())
	iface = dotted_to_binary(iface)
	group = dotted_to_binary(mcaddr)
	sock.setsockopt(IN.IPPROTO_IP, IN.IP_ADD_MEMBERSHIP, \
		  struct.pack('ll', group, iface))
	sock.setsockopt(IN.IPPROTO_IP, IN.IP_MULTICAST_TTL, \
		  chr(ttl))

