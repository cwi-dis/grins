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
		windowinterface.settimevirtual(1)
		self.starttime = windowinterface.getcurtime()
		print 'starttime=', self.starttime
		
		self._progress = windowinterface.ProgressDialog("Exporting", self.cancel_callback)
		self._progress.set('Exporting document to WMP...')
		
		# XXX: temp until set progress is enabled
		self._progress._dialog.OnCancel = self.cancel_callback 
		
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
			else:
				self.writer.update(timestamp-self.starttime)
		else:
			self.topwindow = window
			print 'Begin export', self.filename, 'using profile', self.profile
			self.writer = wmwriter.WMWriter(self, window.getDrawBuffer(), self.profile)
			self.writer.setOutputFilename(self.filename)
			self.writer.beginWriting()

	def finished(self):
		if self.writer:
			self.writer.endWriting()
			print 'End export', self.writer._filename
			self.writer = None
			self.topwindow = None
		if self._progress:
			del self._progress
		stoptime = windowinterface.getcurtime()
		windowinterface.settimevirtual(0)
		
	def cancel_callback(self):
		self.player.stop()
		windowinterface.showmessage('Export interrupted.')
