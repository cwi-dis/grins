__version__ = "$Id$"

#
# WIN32 Download Channel
#

# the core
import Channel

# canonURL
import MMurl

# CreateAsyncMonikerFile
import win32ui

# for demo we need: shell_execute
import windowinterface

class DownloadChannel(Channel.ChannelAsync):
	def __init__(self, name, attrdict, scheduler, ui):
		Channel.ChannelAsync.__init__(self, name, attrdict, scheduler, ui)
		self._asyncMonikerFile=None
		self._tmpfile=None

	def __repr__(self):
		return '<DownloadChannel instance, name=' + `self._name` + '>'

	def do_hide(self):
		self.release_res()
		Channel.ChannelAsync.do_hide(self)
	
	def release_res(self):
		if self._asyncMonikerFile:
			self._asyncMonikerFile.Abort()
			self._asyncMonikerFile=None
		
	def destroy(self):
		self.release_res()
		Channel.ChannelAsync.destroy(self)

	def do_arm(self, node, same=0):
		if same: return
		self.release_res()
		amf=win32ui.CreateAsyncMonikerFile()
		amf.SetStatusListener(self)
		url = MMurl.canonURL(self.getfileurl(node))
		self._asyncMonikerFile=amf
		self._asyncMonikerFile.Open(url)
		return 0

	def do_play(self, node):
		windowinterface.shell_execute(self._tmpfile)
		self.playdone(0)

	def stopplay(self, node):
		self.release_res()
		Channel.ChannelAsync.stopplay(self, node)

	def setpaused(self, paused):
		if self._asyncMonikerFile:
			if paused:
				self._asyncMonikerFile.Suspend()
			else:
				self._asyncMonikerFile.Resume()

	def OnProgress(self,progress,progressMax,status,statusText):
		if status==14:
			self._tmpfile=statusText
			print 'TEMPFILE:',self._tmpfile
		print progress,'/',progressMax,'status:',status,statusText

	def OnDownloadComplete(self):
		self.arm_1()

