"""Test ArcInfoDialog, editor specifics"""

__version__ = "$Id$"

import sys
import os

if os.name == 'posix':
	sys.path.append("../lib")
elif os.name == 'mac':
	sys.path.append("::lib")
# etc...


from ArcInfoDialog import ArcInfoDialog

class ArcInfoTest(ArcInfoDialog):
	__src_options = ['*Begin*', '*End*']
	__dst_options = ['*Begin*', '*End*']
	def __init__(self):
		ArcInfoDialog.__init__(self, 'ArcInfo test',
				       self.__src_options, 0,
				       self.__dst_options, 1,
				       2.5)
	def cancel_callback(self):
		import sys
		self.close()
		sys.exit(0)
	def ok_callback(self):
		self.apply_callback()
		self.cancel_callback()
	def apply_callback(self):
		print 'source position is', \
		      self.__src_options[self.src_getpos()]
		print 'dest position is', \
		      self.__dst_options[self.dst_getpos()]
		print 'delay is', self.delay_getvalue()
	def restore_callback(self):
		self.settitle('ArcInfo Restore test')
		self.src_setpos(0)
		self.dst_setpos(1)
		self.delay_setvalue(2.5)

import windowinterface
print 'Creating ArcInfoDialog...'
dialog = ArcInfoTest()
print 'Play with the controls and select "Apply" every time.'
print 'Select "Restore" to restore to initial setting'
print '(check that window title changes!)'
print 'When done, select "OK" or "Cancel".'
try:
	windowinterface.mainloop()
except SystemExit:
	pass
print 'exiting...'
