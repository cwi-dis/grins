__version__ = "$Id$"

"""
System configuration profiles
0 Dial-up Modems - ISDN Multiple Bit Rate Video
1 Intranet - High Speed LAN Multiple Bit Rate Video
2 28.8, 56, and 100 Multiple Bit Rate Video
3 6.5 voice audio
4 16 AM Radio
5 28.8 FM Radio Mono
6 28.8 FM Radio Stereo
7 56 Dial-up High Quality Stereo
8 64 Near CD Quality Audio
9 96 CD Quality Audio
10 128 CD Quality Audio
11 28.8 Video - Voice
12 28.8 Video - Audio Emphasis
13 28.8 Video for Web Server
14 56 Dial-up Modem Video
15 56 Dial-up Video for Web Server
16 100 Video
17 250 Video
18 512 Video
19 1Mb Video
20 3Mb Video
"""

try:
    import wmfapi
except ImportError:
    wmfapi = None

class WMWriter:
    def __init__(self, dds, profile=20):
        self._dds = dds
        self._writer = None
        self._filename = None
        self._sample = None
        self._lasttm = 0
        if not wmfapi:
            return
        profman = wmfapi.CreateProfileManager()
        prof = profman.LoadSystemProfile(profile)
        writer = wmfapi.CreateDDWriter(prof)
        wmtype = wmfapi.CreateDDVideoWMType(self._dds)
        writer.SetVideoFormat(wmtype)
        self._writer = writer

    def setOutputFilename(self, filename):
        self._filename = filename
        if self._writer:
            self._writer.SetOutputFilename(filename)

    def beginWriting(self):
        if self._writer:
            self._writer.BeginWriting()
            self._sample = self._writer.AllocateDDSample(self._dds)
            self._lasttm = 0

    def endWriting(self):
        if self._writer:
            self._writer.Flush()
            self._writer.EndWriting()

    def update(self, now):
        now = int(1000.0*now+0.5)
        now = 100*(now/100)
        if not self._writer: return
        t = self._lasttm
        while t <= now:
            self._writer.WriteVideoSample(t, self._sample)
            t = t + 100
        self._sample = self._writer.AllocateDDSample(self._dds)
        self._lasttm = now
