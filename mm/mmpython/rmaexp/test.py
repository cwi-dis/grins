
import rma

engine = rma.CreateEngine()

context = rma.CreateClientContext()
print context
cobj = rma.CreateClientAdviseSink()
print cobj
errorSink = rma.CreateErrorSink()
print errorSink
cobj = rma.CreateSiteSupplier()
print cobj
cobj = rma.CreateAuthenticationManager()
print cobj


player =  engine.CreatePlayer()

player.SetClientContext(context)

errorctrl = player.QueryIRMAErrorSinkControl()
print errorctrl

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

