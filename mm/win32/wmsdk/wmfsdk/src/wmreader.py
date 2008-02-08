__version__ = "$Id$"

import wmfapi
large_int = wmfapi.large_int

# init COM libs
wmfapi.CoInitialize()


class DebugReaderAgent:
    def __init__(self):
        print 'ReaderAgent'
    def __del__(self):
        print '~ReaderAgent'
    def OnStatus(self,status):
        print wmfapi.wmt_status_str[status]
    def OnSample(self,msSampleTime,sampleBuf):
        print msSampleTime

class DebugReaderAgentAdvanced(DebugReaderAgent):
    def OnTime(self,msCurrTime):
        print 'OnTime',msCurrTime


# a very simple windows media audio player
class WMAPlayerAgent:
    def __init__(self):
        self._aout = None

    def OnStatus(self,status):
        pass

    def OnSample(self,msSampleTime,sampleBuf):
        if self._aout:
            header = self._aout.PrepareHeader(sampleBuf)
            self._aout.Write(header)

    def WaveOutOpen(self,wfx):
        import winmmapi
        self._aout = winmmapi.WaveOutOpen(wfx)

def printWMInfo(reader):
    nstreams = reader.GetOutputCount()
    print 'media has',nstreams,"output stream(s)"
    wmheader = reader.QueryIWMHeaderInfo()
    wmprofile = reader.QueryIWMProfile()
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
        try:
            nattrs  = wmheader.GetAttributeCount(i)
        except wmfapi.error, arg:
            print arg
            nattrs = 0
        for j in range(nattrs):
            attr = wmheader.GetAttributeByIndex(j,i)
            print wmfapi.wmt_attr_datatype_str[attr[0]],attr[1:]


rights = 0 # we don't use a rights manager
reader = wmfapi.CreateReader(rights)

agent = WMAPlayerAgent()
#agent = DebugReaderAgent()
#agent = DebugReaderAgentAdvanced()

readercbobj = wmfapi.CreatePyReaderCallback(agent)
#readercbobj = wmfapi.CreatePyReaderCallbackAdvanced(agent)

reader.Open(r'D:\ufs\mm\cmif\win32\wmsdk\wmfsdk\src\testdata\test.wma',readercbobj)
#reader.Open(r'D:\ufs\mm\cmif\win32\wmsdk\wmfsdk\src\testdata\msvideo.asf',readercbobj)
readercbobj.WaitOpen()

# print some info for windows media file
printWMInfo(reader)


# get output props of pin 0
nout = reader.GetOutputCount()
props = reader.GetOutputProps(0)

if nout==1 and agent.__class__ == WMAPlayerAgent:
    mt = props.GetMediaType()
    major, subtype = mt.GetType()
    if major==wmfapi.WMMEDIATYPE_Audio:
        wfx = mt.GetAsWaveFormatEx()
        agent.WaveOutOpen(wfx)

# start and duration are in cns == 100 ns
start = large_int(0)
dur = large_int(0)
reader.Start(start,dur,1.0)

# wait efficiently for completion
readercbobj.WaitForCompletion()
reader.Stop()

# no more python callbacks please
readercbobj.SetListener()

reader.Close()

del reader

# on exit: release COM libs
wmfapi.CoUninitialize()
