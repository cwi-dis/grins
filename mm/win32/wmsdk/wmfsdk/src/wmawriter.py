__version__ = "$Id$"


import wmfapi
large_int = wmfapi.large_int


# init COM libs
wmfapi.CoInitialize()

# temp debug: find the name of a guid
def findguid(guid):
    for s in dir(wmfapi):
        if s.find("WMMEDIA")>=0 or s.find("WMFORMAT")>=0:
            if guid==getattr(wmfapi,s):
                return s

profman = wmfapi.CreateProfileManager()
nprofiles = profman.GetSystemProfileCount()
print nprofiles,'system profiles:'
for ix in range(nprofiles):
    prof = profman.LoadSystemProfile(ix)
    print ix, prof.GetName()

# find audio pin
prof = profman.LoadSystemProfile(10)
writer = wmfapi.CreateWriter()
writer.SetProfile(prof)
npins = writer.GetInputCount()
audiopinix = -1
audiopinmt = None
audiopinprops = None
print 'profile pins:'
for i in range(npins):
    pinprop = writer.GetInputProps(i)
    pintype = pinprop.GetType()
    print i,'\t', findguid(pintype)
    if pintype == wmfapi.WMMEDIATYPE_Audio:
        audiopinix = i
        audiopinprops = pinprop
        audiopinmt = pinprop.GetMediaType()
if audiopinix>=0:
    print 'audiopin is pin ',audiopinix

writer.SetOutputFilename(r'D:\ufs\mm\cmif\win32\wmsdk\wmfsdk\src\testdata\test.wma');

# read header and set audiopinmt
import avi
avi.AVIFileInit()
avifile = avi.AVIFileOpen(r'D:\ufs\mm\cmif\win32\DXMedia\bin\yyy.wav')
avistream = avifile.GetStream()
avifsize = avistream.FormatSize()
wfx = avistream.ReadFormat(avifsize)
fmt = wfx.GetMembers()
bps = fmt[3]
aviinfo = avistream.ReadInfo()

audiopinmt.SetType(wmfapi.WMMEDIATYPE_Audio,wmfapi.WMMEDIASUBTYPE_PCM)
audiopinmt.SetSampleSize(aviinfo.GetSampleSize())
audiopinmt.SetFormat(wmfapi.WMFORMAT_WaveFormatEx,wfx.GetBuffer())
audiopinprops.SetMediaType(audiopinmt)

writer.SetInputProps(audiopinix,audiopinprops)

nSamples = avistream.End()
print nSamples,'samples in avi'
curSample = avistream.Start()
tmsec = 0
ms2cns = large_int(10000)

writer.BeginWriting()
samplesToRead = 1024
while curSample < nSamples:
    data, bytes, nsamples = avistream.Read(curSample,samplesToRead)
    sample = writer.AllocateSample(bytes)
    sample.SetBuffer(data)
    tmsec = tmsec + bytes*1000/bps
    tcnsec = large_int(tmsec)*ms2cns
    curSample = curSample + nsamples
    writer.WriteSample(audiopinix,tcnsec,0,sample)

writer.Flush()
writer.EndWriting()

del avistream
del avifile
avi.AVIFileExit()

# on exit: release COM libs
wmfapi.CoUninitialize()
