__version__ = "$Id$"

import rma

import MMurl, urllib

import win32ui, win32api

class RMDuration:
	def __init__(self, url):
		self.dur = 0
		url = MMurl.canonURL(url)
		url = MMurl.unquote(url)
		self._engine = rma.CreateEngine()
		self._player = self._engine.CreatePlayer(-1,((-1,-1), (-1,-1)), 1)
		self._player.SetStatusListener(self)
		self._player.OpenURL(url)

	def calcDur(self):
		self._player.Begin()
		repeat = 0
		while not self.dur and repeat<40:
			win32ui.PumpWaitingMessages(0,0)
			win32api.Sleep(50)
			repeat = repeat + 1
		self._player.Stop()

	def OnPosLength(self, pos, len):
		self.dur = len/1000.0

	def getDur(self):
		return self.dur 

# policy:
# if realsupport fails try get dur from Real Player
def get(url):
	import realsupport
	info = realsupport.getinfo(url)
	dur = info.get('duration', 0)
	if not dur:
		try:
			rmadur = RMDuration(url)
			rmadur.calcDur()
			dur = rmadur.getDur()
		except rma.error:
			return 0
	return dur
