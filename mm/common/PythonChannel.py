# Python channel

# This lets you execute Python commands.

import sys
import string
from Channel import Channel
import MMAttrdefs


class PythonChannel(Channel):

	# Declaration of attributes that are relevant to this channel,
	# respectively to nodes belonging to this channel.

	chan_attrs = ['startupfile']
	node_attrs = ['duration', 'file']

	def init(self, name, attrdict, player):
		self = Channel.init(self, name, attrdict, player)
		self.reset()
		return self

	def __repr__(self):
		return '<PythonChannel instance, name=' + `self.name` + '>'

	def reset(self):
		self.node = None
		self.env = {}
		self.env['player'] = self.player
		self.env['toplevel'] = self.player.toplevel
		self.env['root'] = self.player.root
		self.env['context'] = self.player.root.context
		self.env['node'] = None
		if self.attrdict.has_key('startupfile'):
			startupfile = self.attrdict['startupfile']
			startupfile = \
				self.player.toplevel.findfile(startupfile)
			try:
				execfile(startupfile, self.env)
			except:
				print 'PythonChannel:', startupfile,
				print '***exception***:',
				print sys.exc_type + ':', sys.exc_value

	def play(self, node, callback, arg):
		if self.is_showing():
			type = node.GetType()
			if type == 'imm':
				list = node.GetValues()
				cmd = string.joinfields(list, '\n') + '\n'
				file = '<commands>'
			else:
				file = MMAttrdefs.getattr(node, 'file')
				cmd = 'execfile(' + `file` + ')\n'
			self.env['node'] = node
			try:
				exec(cmd, self.env)
			except:
				print 'PythonChannel:', file,
				print '***exception***:',
				print sys.exc_type + ':', sys.exc_value
			self.env['node'] = None
		Channel.play(self, node, callback, arg)

	def done(self, dummy):
		Channel.done(self, dummy)
		self.node = None

##	def stop(self):
##		Channel.stop(self)
