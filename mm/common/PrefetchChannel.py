__version__ = "$Id$"


# the core
import Channel

# canonURL
import MMurl


class PrefetchChannel(Channel.ChannelAsync):
	def __init__(self, name, attrdict, scheduler, ui):
		Channel.ChannelAsync.__init__(self, name, attrdict, scheduler, ui)

	def __repr__(self):
		return '<PrefetchChannel instance, name=' + `self._name` + '>'

	def do_hide(self):
		Channel.ChannelAsync.do_hide(self)
	
		
	def destroy(self):
		Channel.ChannelAsync.destroy(self)

	def do_arm(self, node, same=0):
		if same: return
		url = self.getfileurl(node)
		if not url:
			self.errormsg(node, 'No URL set on node')
			return 1
		url = MMurl.canonURL(url)
		return 0

	def do_play(self, node):
		self.playdone(0)

	def stopplay(self, node):
		Channel.ChannelAsync.stopplay(self, node)

	def setpaused(self, paused):
		pass

	def OnProgress(self,progress,progressMax,status,statusText):
		if status==14:
			self._tmpfile=statusText
			print 'TEMPFILE:',self._tmpfile
		print progress,'/',progressMax,'status:',status,statusText

	def OnDownloadComplete(self):
		self.arm_1()

