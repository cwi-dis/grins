__version__ = "$Id$"

import windowinterface
import wmwriter
	
def haswmpruntimecomponents():
	try:
		import wmfapi
		dummy = wmfapi.CreateProfileManager()
	except:
		return 0
	return 1

class Exporter:
	def __init__(self, filename, player, profile=19):
		self.filename = filename
		self.player = player
		self.writer = None
		self.profile = profile
		self.topwindow = None
		self.completed = 0

		self.progress = windowinterface.ProgressDialog("Exporting", self.cancel_callback, None, 0)
		self.progress.set('Exporting document to WMP...')

		self.timefunc = self.player.scheduler.timefunc
		self.player.exportplay(self)
		
	def __del__(self):
		del self.writer
		del self.player
		del self.topwindow
	
	def createWriter(self, window):
		self.topwindow = window
		self.writer = wmwriter.WMWriter(self, window.getDrawBuffer(), self.profile)
		self._setAudioFormat()
		self.writer.setOutputFilename(self.filename)
		self.writer.beginWriting()
		
	def getWriter(self):
		return self.writer

	def changed(self, topchannel, window, event, timestamp):
		"""Callback from the player: the bits in the window have changed"""
		if self.topwindow:
			if self.topwindow != window:
				print "Cannot export multiple topwindows"
			elif self.writer and self.progress:
				dt = self.timefunc()
				self.writer.update(dt)
				if self.progress:
					self.progress.set('Exporting document to WMP...', int(dt*100)%100, 100, int(dt*100)%100, 100)

	def audiofragment(self, af):
		dt = self.timefunc()
		if self.progress:
			self.progress.set('Exporting document to WMP...', int(dt*100)%100, 100, int(dt*100)%100, 100)
		
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

	def fail_callback(self):
		if self.progress:
			del self.progress
			self.progress = None
		self.player.stop()
		windowinterface.showmessage('Export failed.')

	def _getNodesOfType(self, ntype, node, urls):
		if node.GetType()=='ext':
			chan = self.player.getchannelbynode(node)
			chtype = chan._attrdict.get('type')
			if chtype == ntype:
				urls.append(chan.getfileurl(node))
		for child in node.GetSchedChildren():
			self._getNodesOfType(ntype, child, urls)
					
	def _setAudioFormat(self):
		urls = []
		self._getNodesOfType('sound', self.player.userplayroot, urls)
		if urls:
			self.writer.setAudioFormatFromFile(urls[0])

