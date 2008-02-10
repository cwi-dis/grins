
import os

import wmfapi
import dshow


# init COM libs
# not needed if run from pythonwin
wmfapi.CoInitialize()

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

class WMVideoConverter:
    def __init__(self):
        self._writing = 0
        self._active = 0

    def isWriting(self):
        return self._writing

    def isActive(self):
        return self._active

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

    def OnSetMediaType(self, mt):
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


input=r'D:\ufs\mm\cmif\win32\wmsdk\wmfsdk\src\testdata\ms.avi'
outputdir=r'D:\ufs\mm\cmif\win32\wmsdk\wmfsdk\src\testdata'

converter = WMVideoConverter()
converter.convert(input, outputdir,'testwmvconv.wmv')
del converter

# on exit: release COM libs
# not needed if run from pythonwin
wmfapi.CoUninitialize()
