# Initial stab at Windows Media Player export

import windowinterface
import wmwriter

class Exporter:
	def __init__(self, filename, player, profile=20):
		self.filename = filename
		self.player = player
		self.writer = None
		self.profile = profile
		self.aborted = 0
		self.completed = 0
		self.topwindow = None
		windowinterface.settimevirtual(1)
		self.starttime = windowinterface.getcurtime()
		print 'starttime=', self.starttime
		self.player.exportplay(self)
		
	def _cleanup(self):
		self.player = None
		self.topwindow = None
		
	# we have to locate audio nodes and find their audio format
	def setcontext(self, context):
		pass 

	def getWriter(self):
		return self.writer

	def changed(self, topchannel, window, event, timestamp):
		"""Callback from the player: the bits in the window have changed"""
		if self.topwindow:
			if self.topwindow != window:
				print "Cannot export multiple topwindows"
				# self.cancel_callback() # XXX Or schedule with timer? We're in a callback...
				return
			else:
				self.writer.update(timestamp-self.starttime)
		elif not self.completed:
			self.topwindow = window
			print 'Begin export', self.filename, 'using profile', self.profile
			self.writer = wmwriter.WMWriter(self, window.getDrawBuffer(), self.profile)
			self.writer.setOutputFilename(self.filename)
			self.writer.beginWriting()

	def audiofragment(self):
		"""XXXX This needs work"""
		pass
		
	def finished(self, aborted):
		if self.writer:
			self.writer.endWriting()
			print 'End export', self.writer._filename
			self.writer = None
			self.topwindow = None
		self.completed = 1
		if aborted:
			self.aborted = 1
		stoptime = windowinterface.getcurtime()
		windowinterface.settimevirtual(0)
		
	def cancel_callback(self):
		self.aborted = 1
		self.player.stop()
		self._cleanup()
