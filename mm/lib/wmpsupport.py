# Initial stab at Windows Media Player export

import windowinterface
import wmwriter

class Exporter:
	def __init__(self, filename, player, profile=20):
		self.filename = filename
		self.player = player
		self.writer = None
		self.profile = profile
		self.topwindow = None
		self.completed = 0
		windowinterface.settimevirtual(1)
		self.starttime = windowinterface.getcurtime()
		print 'starttime=', self.starttime
		self.progress = windowinterface.ProgressDialog("Exporting", self.cancel_callback, None, 0)
		self.progress.set('Exporting document to WMP...')
		self.player.exportplay(self)
		
	def __del__(self):
		del self.writer
		del self.player
		del self.topwindow
		
	def getWriter(self):
		return self.writer

	def changed(self, topchannel, window, event, timestamp):
		"""Callback from the player: the bits in the window have changed"""
		if self.topwindow:
			if self.topwindow != window:
				print "Cannot export multiple topwindows"
				return
			elif self.writer and self.progress:
				dt = timestamp-self.starttime
				self.writer.update(dt)
				if self.progress:
					self.progress.set('Exporting document to WMP...', int(dt*100)%100, 100, int(dt*100)%100, 100)
		else:
			self.topwindow = window
			print 'Begin export', self.filename, 'using profile', self.profile
			self.writer = wmwriter.WMWriter(self, window.getDrawBuffer(), self.profile)
			self.writer.setOutputFilename(self.filename)
			self.writer.beginWriting()

	def finished(self):
		if self.progress:
			self.progress.set('Encoding document for WMP...', 100, 100, 100, 100)
		if self.writer:
			self.writer.endWriting()
			print 'End export', self.writer._filename
			self.writer = None
			self.topwindow = None
		if self.progress:
			del self.progress
			self.progress = None
		stoptime = windowinterface.getcurtime()
		windowinterface.settimevirtual(0)
		
	def cancel_callback(self):
		if self.progress:
			del self.progress
			self.progress = None
		self.player.stop()
		windowinterface.showmessage('Export interrupted.')
