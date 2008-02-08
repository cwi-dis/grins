
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

def convertvideofile(url, dstdir, file, node):
    import producer
    global engine
    # ignore suggested extension and make our own
    file = os.path.splitext(file)[0] + '.rm'
    fullpath = os.path.join(dstdir, file)
    if engine is None:
        engine = producer.CreateRMBuildEngine()
    for pin in engine.GetPins():
        if pin.GetOutputMimeType() == producer.MIME_REALVIDEO:
            videopin = pin
        elif pin.GetOutputMimeType() == producer.MIME_REALAUDIO:
            audiopin = pin
    engine.SetDoOutputMimeType(producer.MIME_REALAUDIO, 0)
    engine.SetDoOutputMimeType(producer.MIME_REALVIDEO, 1)
    engine.SetDoOutputMimeType(producer.MIME_REALEVENT, 0)
    engine.SetDoOutputMimeType(producer.MIME_REALIMAGEMAP, 0)
    engine.SetDoOutputMimeType(producer.MIME_REALPIX, 0)
    engine.SetRealTimeEncoding(0)
    engine.SetDoMultiRateEncoding(1)
    cp = engine.GetClipProperties()
    ts = engine.GetTargetSettings()
    if node is not None:
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
        #ts.SetVideoQuality(producer.ENC_VIDEO_QUALITY_NORMAL)
        ts.SetVideoQuality(producer.ENC_VIDEO_QUALITY_SMOOTH_MOTION)
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
    renderer=b.FindFilterByName('Video Renderer')
    enumpins=renderer.EnumPins()
    pin=enumpins.Next()
    lastpin=pin.ConnectedTo()
    b.RemoveFilter(renderer)
    try:
        vf = dshow.CreateFilter('Video Real Media Converter')
    except:
        print 'Video real media converter filter is not installed'
        return
    b.AddFilter(vf,'VRMC')
    b.Render(lastpin)

    try:
        aurenderer=b.FindFilterByName('Default DirectSound Device')
    except:
        aurenderer=None
    if not aurenderer:
        try:
            aurenderer=b.FindFilterByName('Default WaveOut Device')
        except:
            aurenderer=None
    if aurenderer:
        enumpins=aurenderer.EnumPins()
        pin=enumpins.Next()
        lastpin=pin.ConnectedTo()
        b.RemoveFilter(aurenderer)
        try:
            af = dshow.CreateFilter('Audio Real Media Converter')
        except:
            aurenderer=None
        else:
            b.AddFilter(af,'ARMC')
            b.Render(lastpin)

    try:
        vrconv=vf.QueryIRealConverter()
    except:
        print 'Filter does not support interface IRealConverter'
        return
    try:
        ukeng=engine.QueryInterfaceUnknown()
    except:
        print 'RMABuildEngine QueryInterfaceUnknown failed'
        return
    vrconv.SetInterface(ukeng,'IRMABuildEngine')

    try:
        ukpin=videopin.QueryInterfaceUnknown()
    except:
        print 'RMAInputPin QueryInterfaceUnknown failed'
        return
    vrconv.SetInterface(ukpin,'IRMAInputPin')


    if aurenderer:
        try:
            arconv=af.QueryIRealConverter()
        except:
            aurenderer=None
        else:
            arconv.SetInterface(ukeng,'IRMABuildEngine')

    if aurenderer:
        try:
            ukpin=audiopin.QueryInterfaceUnknown()
        except:
            aurenderer=None
        else:
            arconv.SetInterface(ukpin,'IRMAInputPin')

    if aurenderer:
        engine.SetDoOutputMimeType(producer.MIME_REALAUDIO, 1)
        ts.SetAudioContent(producer.ENC_AUDIO_CONTENT_VOICE)

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
    del b

#inputfile='D:\\ufs\\mm\\cmif\\Build\\common\\testdoc\\testdatampg.mpg'
inputfile='D:\\ufs\\mm\\cmif\\win32\\DXMedia\\bin\\ms.avi'
#inputfile='D:\\ufs\\mmback\\mpeg\\bloem.mpg'
outputdir='d:\\ufs\\mm\\cmif\\win32\\DXMedia\\bin'

convertvideofile(inputfile,outputdir,'xxx.rm',None)
