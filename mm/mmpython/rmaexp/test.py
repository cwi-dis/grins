
import rma

engine = rma.CreateEngine()

player =  engine.CreatePlayer()


clientContext = rma.CreateClientContext()
adviseSink = rma.CreateClientAdviseSink()
errorSink = rma.CreateErrorSink()
siteSupplier = rma.CreateSiteSupplier()
authManager = rma.CreateAuthenticationManager()


class AdviseListener:
	def __init__(self):
		print 'AdviseListener'
	def __del__(self):
		print '~AdviseListener'
	def OnPresentationOpened(self):
		print 'OnPresentationOpened'
	def OnPresentationClosed(self):
		print 'OnPresentationClosed'
	def OnBegin(self,t):
		print 'OnBegin',t
	def OnStop(self):
		print 'OnStop'
	def OnStop(self):
		print 'OnPause'

adviseSink.SetPyListener(AdviseListener())

clientContext.AddInterface(adviseSink.QueryIUnknown())
clientContext.AddInterface(errorSink.QueryIUnknown())
clientContext.AddInterface(siteSupplier.QueryIUnknown())
clientContext.AddInterface(authManager.QueryIUnknown())

# not working yet
#player.AddAdviseSink(adviseSink)

player.SetClientContext(clientContext)

errorctrl = player.QueryIRMAErrorSinkControl()
errorctrl.AddErrorSink(errorSink)



# real audio
url1="file://D|/ufs/mm/cmif/mmpython/rmasdk/testdata/thanks3.ra"

# real video
url2="file://D|/ufs/mm/cmif/mmpython/rmasdk/testdata/test.rv"

# real text
url3="file://D|/ufs/mm/cmif/mmpython/rmasdk/testdata/news.rt"

# real pixel
url4="file:///D|/ufs/mm/cmif/mmpython/rmasdk/testdata/fadein.rp"


player.OpenURL(url1)

player.Begin()

