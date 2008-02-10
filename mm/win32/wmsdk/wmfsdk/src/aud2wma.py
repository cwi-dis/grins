
import os

import wmfapi
import dshow

# init COM libs
# not needed if run from pythonwin
wmfapi.CoInitialize()

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
        import MMurl
        fg = dshow.CreateGraphBuilder()
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


input = r'D:\ufs\mm\cmif\win32\wmsdk\wmfsdk\src\testdata\test.au'
outputdir = r'D:\ufs\mm\cmif\win32\wmsdk\wmfsdk\src\testdata'

converter = WMAudioConverter()
converter.convert(input,outputdir,'testwmaconv.wma')
del converter

# on exit: release COM libs
# not needed if run from pythonwin
wmfapi.CoUninitialize()
