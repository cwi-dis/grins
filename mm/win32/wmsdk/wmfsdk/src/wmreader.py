import wmfapi

# init COM libs
wmfapi.CoInitialize()


class ReaderAgent:
	def __init__(self):
		print 'ReaderAgent'
	def __del__(self):
		print '~ReaderAgent'
	def OnStatus(self,status):
		if status==1:
			print 'WMT_OPENED'
		elif status == 11:
			print 'WMT_STARTED'
		elif status == 6:
			print 'WMT_END_OF_STREAMING'
		elif status == 4:
			print 'WMT_EOF'
		else:
			print 'status=',status
	def OnSample(self,msSampleTime):
		print msSampleTime


rights = 0 # we don't use a rights manager
reader = wmfapi.CreateReader(rights)

readercbobj = wmfapi.CreatePyReaderCallback(ReaderAgent())

reader.Open(r'D:\ufs\mm\cmif\win32\wmsdk\wmfsdk\src\test.wma',readercbobj)
readercbobj.WaitOpen()
noutputs = reader.GetOutputCount()
print 'media file has',noutputs,'stream(s)'

reader.Start(0,0,1.0)

# wait efficiently for completion
readercbobj.WaitForCompletion()

# no more python callbacks please
readercbobj.SetListener()

reader.Close()

del reader

# on exit: release COM libs
wmfapi.CoUninitialize()