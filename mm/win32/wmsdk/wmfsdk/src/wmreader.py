import wmfapi

# init COM libs
wmfapi.CoInitialize()

# temp debug: find the name of a guid
def findguid(guid):
    for s in dir(wmfapi):
		if s.find("WMMEDIA")>=0 or s.find("WMFORMAT")>=0:
			if guid==getattr(wmfapi,s):
				return s

class PyReaderCallback:
	def __init__(self):
		pass
	def OnStatus(self,status):
		print status
	def OnSample(self,*arg):
		print arg

reader = wmfapi.CreateReader(0)
readercbobj = wmfapi.CreatePyReaderCallback(PyReaderCallback())
reader.Open(r'D:\ufs\mm\cmif\win32\wmsdk\wmfsdk\src\test.wma',readercbobj)
readercbobj.WaitOpen()
noutputs = reader.GetOutputCount()
print 'media file has',noutputs,'stream(s)'

reader.Close()
del reader
del readercbobj

# on exit: release COM libs
wmfapi.CoUninitialize()