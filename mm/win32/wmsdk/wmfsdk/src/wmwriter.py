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

import dshow

try:
    import wmfapi
except ImportError:
    wmfapi = None
else:
    wmfapi.CoInitialize()

class WMWriter:
    def __init__(self, exporter, dds, profile=20):
        self._exporter = exporter
        self._dds = dds
        self._writer = None
        self._filename = None
        self._sample = None
        self._lasttm = 0
        self._writing = 0
        if not wmfapi:
            return
        profman = wmfapi.CreateProfileManager()
        prof = profman.LoadSystemProfile(profile)
        writer = wmfapi.CreateDDWriter(prof)
        wmtype = wmfapi.CreateDDVideoWMType(self._dds)
        writer.SetVideoFormat(wmtype)
        self._writer = writer
        self._audiopeer = dshow.CreatePyRenderingListener(self)

        #audiofile = r'D:\ufs\mm\cmif\bin\win32\examples\168.au'
        #self.setAudioFormatFromFile(audiofile)

    def setOutputFilename(self, filename):
        self._filename = filename
        if self._writer:
            self._writer.SetOutputFilename(filename)

    def beginWriting(self):
        if self._writer:
            self._writer.BeginWriting()
            self._sample = self._writer.AllocateDDSample(self._dds)
            self._lasttm = 0
            self._writing = 1

    def endWriting(self):
        if self._writer:
            self._writer.Flush()
            self._writer.EndWriting()
            self._writing = 0

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

    #
    #  Audio section
    #

    # implement method of IRendererAdviceSink for audio
    def OnRenderSample(self, ms):
        if self._writing:
            self._writer.WriteDSAudioSample(ms, self._audiotm)

    # implement method of IRendererAdviceSink for audio
    def OnActive(self):
        self._audiotm = self._lasttm

    # set the audio format to that of the audio/video file
    def setAudioFormatFromFile(self, filename):
        dummy  = AudioFormatSetter(self._writer, filename)

    # alter filter graph so that audio samples are feeded to the writer
    def redirectAudioFilter(self, fg, hint=None):
        # find renderer
        try:
            aurenderer = fg.FindFilterByName('Default DirectSound Device')
        except:
            aurenderer=None
        if not aurenderer:
            try:
                aurenderer=fg.FindFilterByName('Default WaveOut Device')
            except:
                aurenderer=None
        if not aurenderer and hint:
            try:
                aurenderer=fg.FindFilterByName(hint)
            except:
                aurenderer=None
        if not aurenderer:
            print 'Audio renderer not found'
            return None

        enumpins=aurenderer.EnumPins()
        pin=enumpins.Next()
        aulastpin=pin.ConnectedTo()
        fg.RemoveFilter(aurenderer)
        try:
            f = dshow.CreateFilter('Audio Windows Media Converter')
        except:
            print 'Audio windows media converter filter is not installed'
            return None

        try:
            wmconv=f.QueryIWMConverter()
        except:
            print 'Filter does not support interface IWMConverter'
            return
        wmconv.SetAdviceSink(self._audiopeer)

        fg.AddFilter(f,'AWMC')

        fg.Render(aulastpin)

        return fg

## #####################
class AudioFormatSetter:
    def __init__(self, writer, filename):
        self._audiopeer = dshow.CreatePyRenderingListener(self)
        self._writer = writer
        # this call will set indirectly self._writer format
        fg = self.__createFilterGraph(filename)

    def __createFilterGraph(self, url):
        fg = dshow.CreateGraphBuilder()
        import MMurl
        url = MMurl.canonURL(url)
        url = MMurl.unquote(url)
        fg.RenderFile(url)

        # find renderer
        try:
            aurenderer=fg.FindFilterByName('Default DirectSound Device')
        except:
            aurenderer=None
        if not aurenderer:
            try:
                aurenderer=fg.FindFilterByName('Default WaveOut Device')
            except:
                aurenderer=None
        if not aurenderer:
            print 'Audio renderer not found'
            return None

        enumpins=aurenderer.EnumPins()
        pin=enumpins.Next()
        aulastpin=pin.ConnectedTo()
        fg.RemoveFilter(aurenderer)
        try:
            f = dshow.CreateFilter('Audio Windows Media Converter')
        except:
            print 'Audio windows media converter filter is not installed'
            return None

        try:
            wmconv=f.QueryIWMConverter()
        except:
            print 'Filter does not support interface IWMConverter'
            return
        wmconv.SetAdviceSink(self._audiopeer)

        fg.AddFilter(f,'AWMC')

        fg.Render(aulastpin)

        return fg

    def OnSetMediaType(self, mt):
        self._writer.SetDSAudioFormat(mt)


## #####################
class WMVideoConverter:
    def __init__(self):
        self._writing = 0
        self._active = 0

    def convert(self, input, dstdir, filename, profilenum=20):
        if self._writing: return
        file = os.path.splitext(filename)[0] + '.wmv'
        output = os.path.join(dstdir, file)

        self._writer = self.createWMWriter(profilenum)
        self._writer.SetOutputFilename(output)
        self.findPins(self._writer)

        self._videopeer = dshow.CreatePyRenderingListener(self)

        self._audiofilter = Filter(self, self._writer, self._audiopinix, self._audiopinprops)
        self._audiopeer = dshow.CreatePyRenderingListener(self._audiofilter)

        # this call will set indirectly self._writer format
        fg = self.createFilterGraph(input)
        if not fg:
            return None

        mc = fg.QueryIMediaControl()
        mc.Run()
        import win32ui
        while fg.WaitForCompletion(0)==0:
            win32ui.PumpWaitingMessages()
        mc.Stop()
        win32ui.PumpWaitingMessages()

        return output

    def createWMWriter(self, profilenum):
        profman = wmfapi.CreateProfileManager()
        profile = profman.LoadSystemProfile(profilenum)
        writer = wmfapi.CreateWriter()
        writer.SetProfile(profile)
        return writer

    def findPins(self, writer):
        npins = writer.GetInputCount()
        self._audiopinix = -1
        self._audiopinprops = None
        self._videopinix = -1
        self._videopinprops = None
        for i in range(npins):
            pinprop = writer.GetInputProps(i)
            pintype = pinprop.GetType()
            if pintype == wmfapi.WMMEDIATYPE_Audio:
                self._audiopinix = i
                self._audiopinprops = pinprop
                print 'audio',i
            elif pintype == wmfapi.WMMEDIATYPE_Video:
                self._videopinix = i
                self._videopinprops = pinprop
                print 'video', i

    def createFilterGraph(self, url):
        fg = dshow.CreateGraphBuilder()
        import MMurl
        url = MMurl.canonURL(url)
        url = MMurl.unquote(url)
        fg.RenderFile(url)

        # find video renderer filter and remove it
        renderer=fg.FindFilterByName('Video Renderer')
        enumpins=renderer.EnumPins()
        pin=enumpins.Next()
        lastpin=pin.ConnectedTo()
        fg.RemoveFilter(renderer)

        # create wmv converter filter
        try:
            vf = dshow.CreateFilter('Video Windows Media Converter')
        except:
            print 'Video windows media converter filter is not installed'
            return None

        # set listener
        try:
            wmconv=vf.QueryIWMConverter()
        except:
            print 'Filter does not support interface IWMConverter'
            return None
        wmconv.SetAdviceSink(self._videopeer)

        # add and connect wmv converter filter
        fg.AddFilter(vf,'VWMC')
        enumpins=vf.EnumPins()
        pin=enumpins.Next()
        fg.Connect(lastpin, pin)


        # find audio renderer
        try:
            aurenderer=fg.FindFilterByName('Default DirectSound Device')
        except:
            aurenderer=None
        if not aurenderer:
            try:
                aurenderer=fg.FindFilterByName('Default WaveOut Device')
            except:
                aurenderer=None
        if aurenderer:
            enumpins=aurenderer.EnumPins()
            pin=enumpins.Next()
            aulastpin=pin.ConnectedTo()
            fg.RemoveFilter(aurenderer)
            try:
                f = dshow.CreateFilter('Audio Windows Media Converter')
            except:
                print 'Audio windows media converter filter is not installed'
                return None

            try:
                wmconv=f.QueryIWMConverter()
            except:
                print 'Filter does not support interface IWMConverter'
                return
            wmconv.SetAdviceSink(self._audiopeer)

            fg.AddFilter(f,'AWMC')

            fg.Render(aulastpin)

        return fg

    def isWriting(self):
        return self._writing

    def isActive(self):
        return self._active

    def OnSetMediaType(self, mt):
        print 'OnSetMediaType video'
        self._videopinprops.SetDSMediaType(mt)
        self._writer.SetInputProps(self._videopinix, self._videopinprops)

    def OnActive(self):
        self._writer.BeginWriting()
        self._writing = self._active = 1

    def OnInactive(self):
        self._writer.Flush()
        self._writer.EndWriting()
        self._writing = self._active = 0

    def OnRenderSample(self, ms):
        if self._writing:
            self._writer.WriteDSSample(self._videopinix, ms)

## #####################
class WMAudioConverter:
    def __init__(self):
        self._writing = 0

    def convert(self, input, dstdir, filename, profilenum=10):
        if self._writing: return
        file = os.path.splitext(filename)[0] + '.wma'
        output = os.path.join(dstdir, file)

        self._peer = dshow.CreatePyRenderingListener(self)
        self._writer = self.createWMWriter(profilenum)
        self._writer.SetOutputFilename(output)
        self._audiopinix, self._audiopinprops = self.getAudioPin(self._writer)

        # this call will set indirectly self._writer format
        fg = self.createFilterGraph(input)
        if not fg:
            return None

        mc = fg.QueryIMediaControl()
        mc.Run()
        import win32ui
        while fg.WaitForCompletion(0)==0:
            win32ui.PumpWaitingMessages()
        mc.Stop()
        win32ui.PumpWaitingMessages()

        return output

    def createWMWriter(self, profilenum):
        profman = wmfapi.CreateProfileManager()
        profile = profman.LoadSystemProfile(profilenum)
        writer = wmfapi.CreateWriter()
        writer.SetProfile(profile)
        return writer

    def getAudioPin(self, writer):
        npins = writer.GetInputCount()
        audiopinix = -1
        audiopinprops = None
        for i in range(npins):
            pinprop = writer.GetInputProps(i)
            pintype = pinprop.GetType()
            if pintype == wmfapi.WMMEDIATYPE_Audio:
                audiopinix = i
                audiopinprops = pinprop
                break
        return audiopinix, audiopinprops

    def createFilterGraph(self, url):
        fg = dshow.CreateGraphBuilder()
        import MMurl
        url = MMurl.canonURL(url)
        url = MMurl.unquote(url)
        fg.RenderFile(url)

        # find renderer
        try:
            aurenderer=fg.FindFilterByName('Default DirectSound Device')
        except:
            aurenderer=None
        if not aurenderer:
            try:
                aurenderer=fg.FindFilterByName('Default WaveOut Device')
            except:
                aurenderer=None
        if not aurenderer:
            print 'Audio renderer not found'
            return None

        enumpins=aurenderer.EnumPins()
        pin=enumpins.Next()
        aulastpin=pin.ConnectedTo()
        fg.RemoveFilter(aurenderer)
        try:
            f = dshow.CreateFilter('Audio Windows Media Converter')
        except:
            print 'Audio windows media converter filter is not installed'
            return None

        try:
            wmconv=f.QueryIWMConverter()
        except:
            print 'Filter does not support interface IWMConverter'
            return
        wmconv.SetAdviceSink(self._peer)

        fg.AddFilter(f,'AWMC')

        fg.Render(aulastpin)

        return fg

    def OnSetMediaType(self, mt):
        self._audiopinprops.SetDSMediaType(mt)
        self._writer.SetInputProps(self._audiopinix, self._audiopinprops)

    def OnActive(self):
        self._writer.BeginWriting()
        self._writing = 1

    def OnInactive(self):
        self._writer.Flush()
        self._writer.EndWriting()
        self._writing = 0

    def OnRenderSample(self, ms):
        if self._writing:
            self._writer.WriteDSSample(self._audiopinix, ms)

## #####################
class Filter:
    def __init__(self, converter, writer, pinix, pinprops):
        self._converter = converter
        self._writer = writer
        self._pinix = pinix
        self._pinprops = pinprops
        self._active = 0

    def isActive(self):
        return self._active

    def OnSetMediaType(self, mt):
        self._pinprops.SetDSMediaType(mt)
        self._writer.SetInputProps(self._pinix, self._pinprops)

    def OnActive(self):
        self._active = 1

    def OnInactive(self):
        self._active = 0

    def OnRenderSample(self, ms):
        if self._active and self._converter.isWriting():
            self._writer.WriteDSSample(self._pinix, ms)
