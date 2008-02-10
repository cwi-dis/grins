
import os

import wmfapi
import dshow


# init COM libs
# not needed if run from pythonwin
wmfapi.CoInitialize()

# convert any audio file to windows media format (asf or wma)
def convertaudiofile(url, dstdir, file, node):
    # ignore suggested extension and make our own
    file = os.path.splitext(file)[0] + '.wma'
    fullpath = os.path.join(dstdir, file)

    profman = wmfapi.CreateProfileManager()

    # set an apropriate system profile
    # or a create a new one
    profile = profman.LoadSystemProfile(10)

    # find audio pin
    writer = wmfapi.CreateWriter()
    writer.SetProfile(profile)
    npins = writer.GetInputCount()
    audiopinix = -1
    audiopinmt = None
    audiopinprops = None
    print 'profile pins:'
    for i in range(npins):
        pinprop = writer.GetInputProps(i)
        pintype = pinprop.GetType()
        if pintype == wmfapi.WMMEDIATYPE_Audio:
            audiopinix = i
            audiopinprops = pinprop
            audiopinmt = pinprop.GetMediaType()
    if audiopinix>=0:
        print 'audiopin is pin ',audiopinix
    else:
        print 'no audio pin'
        return None

    writer.SetOutputFilename(fullpath);

    b = dshow.CreateGraphBuilder()
    import MMurl
    url = MMurl.canonURL(url)
    url = MMurl.unquote(url)
    b.RenderFile(url)
    # find renderer
    try:
        aurenderer=b.FindFilterByName('Default DirectSound Device')
    except:
        aurenderer=None
    if not aurenderer:
        try:
            aurenderer=b.FindFilterByName('Default WaveOut Device')
        except:
            aurenderer=None
    if not aurenderer:
        return None
    enumpins=aurenderer.EnumPins()
    pin=enumpins.Next()
    aulastpin=pin.ConnectedTo()
    b.RemoveFilter(aurenderer)
    try:
        f = dshow.CreateFilter('Audio Windows Media Converter')
    except:
        print 'Audio windows media converter filter is not installed'
        return None
    b.AddFilter(f,'AWMC')
    b.Render(aulastpin)
    try:
        wmconv=f.QueryIWMConverter()
    except:
        print 'Filter does not support interface IWMConverter'
        return
    try:
        uk=writer.QueryIUnknown()
    except:
        print 'WMWriter QueryIUnknown failed'
        return
    wmconv.SetWMWriter(uk)

    try:
        uk = audiopinprops.QueryIUnknown()
    except:
        print 'WMInputMediaProps QueryIUnknown failed'
        return
    wmconv.SetAudioInputProps(audiopinix,uk)

    # media properties and converting is
    # managed by our dshow filter
    mc = b.QueryIMediaControl()
    mc.Run()
    import sys
    if sys.platform=='win32':
        # remove messages in queue
        import win32ui
        while b.WaitForCompletion(0)==0:
            win32ui.PumpWaitingMessages()
        mc.Stop()
        win32ui.PumpWaitingMessages()
    else:
        b.WaitForCompletion()
        mc.Stop()

#inputfile='D:\\ufs\\mm\\cmif\\Build\\common\\testdoc\\testdata.aiff'
inputfile='d:\\ufs\\mm\\cmif\\win32\\DXMedia\\bin\\218.au'
outputdir='d:\\ufs\\mm\\cmif\\win32\\DXMedia\\bin'

convertaudiofile(inputfile,outputdir,'xxx.wma',None)


# on exit: release COM libs
# not needed if run from pythonwin
wmfapi.CoUninitialize()
