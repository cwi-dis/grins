
# A class with this interface can be set as 
# an AsyncMonikerFile status listener
class PrintListener:
	def __init__(self):
		print 'PrintListener'
	def __del__(self):
		print '~PrintListener'
	def OnProgress(self,progress,progressMax,status,statusText):
		print progress,'/',progressMax,'status:',status,statusText
	def OnDownloadComplete(self):
		print 'DownloadComplete'

import win32ui
amf=win32ui.CreateAsyncMonikerFile()
amf.SetStatusListener(PrintListener())

# For testing we don't use temp cashe
# and we explicitly specify the cashe file
amf.SaveAs("flash.zip")
amf.Open("http://www.cwi.nl/~jack/flash.zip")


# local test:
#amf.SaveAs("Jourdan.zip")
#amf.Open("file://F|\\SMIL\\Jourdan.zip")

