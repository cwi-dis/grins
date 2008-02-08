__version__ = "$Id$"

# This module converts windows media audio to real audio
# It uses wmfapi.pyd and producer.pyd
# The wmf runtime must be present
# The convertion is done calling:
#       convertWma2ra(infile, outfile)


# windows media format SDK
import wmfapi
large_int = wmfapi.large_int


# init real producer
import os
import producer

dir = os.path.split(producer.__file__)[0]
dir = os.path.join( dir, "Producer-SDK")
if os.path.exists(dir):
    producer.SetDllAccessPath(
            'DT_Plugins=%s\000' % os.path.join(dir, 'Plugins') +
            'DT_Codecs=%s\000' % os.path.join(dir, 'Codecs') +
            'DT_EncSDK=%s\000' % os.path.join(dir, 'Tools') +
            'DT_Common=%s\000' % os.path.join(dir, 'Common'))
else:
    raise ImportError('no RealMedia codecs')



# AudioFormat helper abstraction class
# (encapsulates the win32 WAVEFORMATEX struct)

# AudioFormat needs a 7-elem tuple of:
# format type (WAVEFORMATEX specific - not used)
# number of channels (i.e. mono, stereo...)
# SamplesPerSec sample rate
# nAvgBytesPerSec: for buffer estimation
# nBlockAlign: block size of data
# BitsPerSample: number of bits per sample of mono data
# internal: WAVEFORMATEX specific - the count in bytes of the size of the format

class AudioFormat:
    def __init__(self, attrs):
        self._formatTag, self._nChannels, self._nSamplesPerSec,\
        self._nAvgBytesPerSec, self._nBlockAlign,\
        self._bitsPerSample, self._cbSize = attrs

    def getblocksize(self):
        return self._nBlockAlign

    def getbps(self):
        return self._bitsPerSample

    def getnchannels(self):
        return self._nChannels

    def getframerate(self):
        return self._nSamplesPerSec



# converter and wm reader callback agent class

class Wma2raConverterAgent:
    def __init__(self):
        pass

    def prepareToEncode(self, fmt, outfile):
        engine = producer.CreateRMBuildEngine()
        for pin in engine.GetPins():
            if pin.GetOutputMimeType() == producer.MIME_REALAUDIO:
                audiopin = pin
        engine.SetDoOutputMimeType(producer.MIME_REALAUDIO, 1)
        engine.SetDoOutputMimeType(producer.MIME_REALVIDEO, 0)
        engine.SetDoOutputMimeType(producer.MIME_REALEVENT, 0)
        engine.SetDoOutputMimeType(producer.MIME_REALIMAGEMAP, 0)
        engine.SetDoOutputMimeType(producer.MIME_REALPIX, 0)
        engine.SetRealTimeEncoding(0)
        cp = engine.GetClipProperties()
        ts = engine.GetTargetSettings()
        ts.RemoveAllTargetAudiences()

        cp.SetTitle('')
        cp.SetAuthor('')
        cp.SetCopyright('')
        cp.SetPerfectPlay(1)
        cp.SetMobilePlay(0)
        ts.SetAudioContent(producer.ENC_AUDIO_CONTENT_VOICE)
        ts.AddTargetAudience(producer.ENC_TARGET_28_MODEM)
        ts.SetVideoQuality(producer.ENC_VIDEO_QUALITY_NORMAL)

        ntargets = 1
        engine.SetDoMultiRateEncoding(ntargets != 1)
        cp.SetSelectiveRecord(0)
        cp.SetDoOutputServer(0)
        cp.SetDoOutputFile(1)
        cp.SetOutputFilename(outfile)

        pp = audiopin.GetPinProperties()
        pp.SetNumChannels(fmt.getnchannels())
        pp.SetSampleRate(fmt.getframerate())
        pp.SetSampleSize(fmt.getbps())

        engine.PrepareToEncode()

        self._ms = engine.CreateMediaSample()
        self._inputsize = audiopin.GetSuggestedInputSize()

        self._engine = engine
        self._audiopin = audiopin
        self._frate = fmt.getframerate()
        self._fread = 0

    def     doneEncoding(self):
        if self._engine:
            self._engine.DoneEncoding()

    def OnStatus(self,status):
        pass

    def OnSample(self, msSampleTime, sampleBuf):
        buf = sampleBuf
        l = len(buf)
        nb = l / self._inputsize
        ix = 0
        for b in range(nb):
            self._ms.SetBuffer(buf[ix:ix+self._inputsize], msSampleTime + int(1000.0 * ix / self._frate), 0)
            self._audiopin.Encode(self._ms)
            self._fread = self._fread + self._inputsize
            ix = ix + self._inputsize
        if ix < l:
            self._ms.SetBuffer(buf[ix:l], msSampleTime + int(1000.0 * ix / self._frate), 0)
            self._audiopin.Encode(self._ms)


# display some info for a wm file
def WMFileReport(reader):
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
            print wmfapi.wmt_attr_datatype_str[attr[0]],attr[1:]



# the control convert wma to ra function

def convertWma2ra(infile, outfile):

    # create wm reader
    rights = 0 # we don't use a rights manager for now
    reader = wmfapi.CreateReader(rights)

    # create our specific callback agent
    # this time will be a ra converter
    agent = Wma2raConverterAgent()
    readercbobj = wmfapi.CreatePyReaderCallback(agent)

    # open wm file passing reader callback
    reader.Open(infile, readercbobj)
    readercbobj.WaitOpen()

    # print some info for windows media file
    print 'Converting file',infile
    WMFileReport(reader)

    # we can accept only one audio stream
    nout = reader.GetOutputCount()
    if nout!=1:
        reader.Close()
        return None

    # get output props of pin 0
    props = reader.GetOutputProps(0)

    # init our converter agent
    mt = props.GetMediaType()
    major, subtype = mt.GetType()
    if major==wmfapi.WMMEDIATYPE_Audio:
        wfx = mt.GetAsWaveFormatEx()
        audfmt = AudioFormat(wfx.GetMembers())
        agent.prepareToEncode(audfmt, outfile)
    else:
        reader.Close()
        return None

    # start and duration are in cns == 100 ns
    start = large_int(0)
    dur = large_int(0)
    reader.Start(start,dur,1.0)

    # wait efficiently for completion
    readercbobj.WaitForCompletion()

    reader.Stop()

    agent.doneEncoding()

    # no more python callbacks please
    readercbobj.SetListener()

    del reader

    return outfile


if __name__ == '__main__':
    infile = r'D:\ufs\mm\cmif\win32\wmsdk\wmfsdk\src\testdata\test.wma'
    outfile = r'D:\ufs\mm\cmif\win32\wmsdk\wmfsdk\src\testdata\test.ra'
    wmfapi.CoInitialize() # init com libs if the calling process has not
    convertWma2ra(infile, outfile)
    wmfapi.CoUninitialize()
