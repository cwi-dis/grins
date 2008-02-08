__version__ = "$Id$"

import wmfapi
large_int = wmfapi.large_int

# init COM libs
wmfapi.CoInitialize()

class WMCopyAgent:
    def __init__(self):
        print 'WMCopyAgent'
        self._readerAdvanced = None
        self._writerAdvanced = None
        self._isEOF = 0

    def __del__(self):
        print '~WMCopyAgent'

    def OnStatus(self,status):
        if status == wmfapi.WMT_STARTED:
            self._readerAdvanced.DeliverTime(qwTime);
        elif status == wmfapi.WMT_EOF:
            self._isEOF = 1

    def OnStreamSampleXXX(self):
        self._writerAdvanced.WriteStreamSample()

    def OnTime(self,qwTime):
        if not self._isEOF:
            qwTime = qwTime + 1000 * 10000;
            readerAdvanced.DeliverTime(qwTime)


def printWMInfo(reader):
    nstreams = reader.GetOutputCount()
    print 'media has',nstreams,"output stream(s)"
    wmheader = reader.QueryIWMHeaderInfo()
    for i in range(nstreams):
        print 'stream',i,'info:'
        props = reader.GetOutputProps(i)
        mt = props.GetMediaType()
        major, subtype = mt.GetType()
        if major == wmfapi.WMMEDIATYPE_Audio:
            print 'WMMEDIATYPE_Audio'
        elif major == wmfapi.WMMEDIATYPE_Video:
            print 'WMMEDIATYPE_Video'
        elif major == wmfapi.WMMEDIATYPE_Script:
            print 'WMMEDIATYPE_Script'
        nattrs  = wmheader.GetAttributeCount(i)
        for j in range(nattrs):
            attr = wmheader.GetAttributeByIndex(j,i)
            print wmt_attr_datatype[attr[0]],attr[1:]


rights = 0 # we don't use a rights manager
reader = wmfapi.CreateReader(rights)
readerAdvanced = reader.QueryIWMReaderAdvanced()

agent = WMCopyAgent()
readercbobj = wmfapi.CreatePyReaderCallbackAdvanced(agent)

reader.Open(r'D:\ufs\mm\cmif\win32\wmsdk\wmfsdk\src\test.wma',readercbobj)
readercbobj.WaitOpen()

# print some info for windows media file
printWMInfo(reader)

profile = reader.QueryIWMProfile()

readerAdvanced.SetManualStreamSelection(1)

nstreams = profile.GetStreamCount()
for i in range(nstreams):
    stream = profile.GetStream(i)
    streamNum = stream.GetStreamNumber()
    readerAdvanced.SetReceiveStreamSamples(streamNum,1)

# Turn on the user clock
readerAdvanced.SetUserProvidedClock(1)

writer = wmfapi.WMCreateWriter()
writerAdvanced = writer.QueryIWMWriterAdvanced()
writer.SetProfile(profile)
outfile = r'D:\ufs\mm\cmif\win32\wmsdk\wmfsdk\src\testdata\copy.wma'
writer.SetOutputFilename(outfile)

ninputs = writer.GetInputCount()
for i in range(ninputs):
    writer.SetInputProps(i)

reader.Start(0,0,1.0,0)

# wait efficiently for completion
readercbobj.WaitForCompletion()

reader.Stop()

# no more python callbacks please
readercbobj.SetListener()

reader.Close()

del reader

# on exit: release COM libs
wmfapi.CoUninitialize()
