"""Test NodeInfoDialog, editor specifics"""

__version__ = "$Id$"

import sys
import os

if os.name == 'posix':
	sys.path.append("../lib")
elif os.name == 'mac':
	sys.path.append("::lib")
# etc...
import MMTypes


from NodeInfoDialog import NodeInfoDialog

class NodeInfoTest(NodeInfoDialog):
	__channels = ['channel 1', 'channel 2', 'channel 3',
		      'channel with a long name',
		      'channel with an even longer name']
	__types = MMTypes.alltypes

	def __init__(self):
		NodeInfoDialog.__init__(self, 'NodeInfo test',
					self.__channels, 3,
					self.__types, 1,
					'node name',
					'/this/is/a/file/name',
					[],
					[])

	def cancel_callback(self):
		import sys
		self.close()
		sys.exit(0)

	def apply_callback(self):
		pass

	def ok_callback(self):
		self.apply_callback()
		self.cancel_callback()

	def restore_callback(self):
		self.settitle('NodeInfo Restore test')
		self.settype(1)
		self.setname('node name')
		self.setfilename('/this/is/a/file/name')
		self.ext_group_show()

import windowinterface
print 'Creating NodeInfoDialog...'
dialog = NodeInfoTest()
print 'Play with the controls and select "Apply" every time.'
print 'Select "Restore" to restore to initial setting'
print '(check that window title changes!)'
print 'When done, select "OK" or "Cancel".'
try:
	windowinterface.mainloop()
except SystemExit:
	pass
print 'exiting...'
