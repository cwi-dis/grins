
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

engine=None

def convertaudiofilex(url, dstdir, file, node):
    global engine
    # ignore suggested extension and make our own
    file = os.path.splitext(file)[0] + '.ra'
    fullpath = os.path.join(dstdir, file)
    if engine is None:
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
    engine.SetDoMultiRateEncoding(1)
    cp = engine.GetClipProperties()
    ts = engine.GetTargetSettings()
    if node is not None:
        import MMAttrdefs
        cp.SetTitle(MMAttrdefs.getattr(node, 'title'))
        cp.SetAuthor(MMAttrdefs.getattr(node, 'author'))
        cp.SetCopyright(MMAttrdefs.getattr(node, 'copyright'))
        ts.SetVideoQuality(MMAttrdefs.getattr(node, 'project_videotype'))
        ts.RemoveAllTargetAudiences()
        target = MMAttrdefs.getattr(node, 'project_targets')
        for i in range(5):
            if (1 << i) & target:
                ts.AddTargetAudience(i)
        if not target:
            ts.AddTargetAudience(producer.ENC_TARGET_28_MODEM)
    else:
        # we don't know nothin' about the node so use some defaults
        cp.SetTitle('')
        cp.SetAuthor('')
        cp.SetCopyright('')
        # XXX: for testing incr caps
        #ts.AddTargetAudience(producer.ENC_TARGET_28_MODEM)
        ts.AddTargetAudience(producer.ENC_TARGET_DUAL_ISDN)
        ts.SetAudioContent(producer.ENC_AUDIO_CONTENT_VOICE)
    cp.SetPerfectPlay(1)
    cp.SetMobilePlay(0)
    cp.SetSelectiveRecord(0)
    cp.SetDoOutputServer(0)
    cp.SetDoOutputFile(1)
    cp.SetOutputFilename(fullpath)

    import dshow, MMurl
    b = dshow.CreateGraphBuilder()
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
        return
    enumpins=aurenderer.EnumPins()
    pin=enumpins.Next()
    aulastpin=pin.ConnectedTo()
    b.RemoveFilter(aurenderer)
    try:
        f = dshow.CreateFilter('Audio Real Media Converter')
    except:
        print 'Audio real media converter filter is not installed'
        return
    b.AddFilter(f,'ARMC')
    b.Render(aulastpin)
    try:
        rconv=f.QueryIRealConverter()
    except:
        print 'Filter does not support interface IRealConverter'
        return
    try:
        uk=engine.QueryInterfaceUnknown()
    except:
        print 'RMABuildEngine QueryInterfaceUnknown failed'
        return
    rconv.SetInterface(uk,'IRMABuildEngine')

    try:
        uk=audiopin.QueryInterfaceUnknown()
    except:
        print 'RMAInputPin QueryInterfaceUnknown failed'
        return
    rconv.SetInterface(uk,'IRMAInputPin')

    # PinProperties,MediaSample,PrepareToEncode,Encode, DoneEncoding
    # are all managed by our dshow filter

    mc = b.QueryIMediaControl()
    mc.Run()
    import sys
    if sys.platform=='win32':
        # remove messages in queue
        # dispatch only paint message
        import win32ui
        while b.WaitForCompletion(0)==0:
            win32ui.PumpWaitingMessages()
        mc.Stop()
        win32ui.PumpWaitingMessages()
    else:
        b.WaitForCompletion()
        mc.Stop()

inputfile='D:\\ufs\\mm\\cmif\\Build\\common\\testdoc\\testdata.aiff'
outputdir='d:\\ufs\\mm\\cmif\\win32\\DXMedia\\bin'

convertaudiofilex(inputfile,outputdir,'xxx.ra',None)
