__version__ = "$Id$"

# DirectShow support
import dshow

# DirectDraw support for MMStream
import ddraw

# we need const WM_USER
import win32con

import MMurl

# private graph notification message
WM_GRPAPHNOTIFY=win32con.WM_USER+101

# a composite interface to dshow infrastructure.
# gets its name from its main interface: IGraphBuilder
class GraphBuilder:
    def __init__(self):
        try:
            self._builder = dshow.CreateGraphBuilder()
        except dshow.error, arg:
            print arg
            self._builder = None
        self._rendered = 0

    def __repr__(self):
        s = '<%s instance' % self.__class__.__name__
        filters = self.GetFiltersNames()
        n = len(filters)
        if n:
            s = s + ', filters = '
            s = s + "\'" + filters[0] + "\'"
        else:
            s = s + ', not rendered'

        for i in range(1,n):
            s = s + ", \'" + filters[i] + "\'"
        s = s + '>'
        return s

    def Release(self):
        pass

    def RenderFile(self, url, exporter=None):
        url = MMurl.canonURL(url)
        url = MMurl.unquote(url)
        try:
            self._builder.RenderFile(url)
        except dshow.error, arg:
            print arg
            self._rendered = 0
        else:
            self._rendered = 1
            if exporter:
                writer = exporter.getWriter()
                if writer:
                    writer.redirectAudioFilter(self._builder)
        return self._rendered

    def Run(self):
        if self._builder and self._rendered:
            mc = self._builder.QueryIMediaControl()
            mc.Run()
    def Stop(self):
        if self._builder and self._rendered:
            mc = self._builder.QueryIMediaControl()
            mc.Stop()
    def Pause(self):
        if self._builder and self._rendered:
            mc = self._builder.QueryIMediaControl()
            mc.Pause()

    def GetDuration(self):
        if self._builder and self._rendered:
            try:
                mp = self._builder.QueryIMediaPosition()
                return mp.GetDuration()
            except:
                return 100 # sometimes should be infinite
        return 1.0

    def SetPosition(self,pos):
        if self._builder and self._rendered:
            mp = self._builder.QueryIMediaPosition()
            mp.SetCurrentPosition(pos)
    def GetPosition(self):
        if self._builder and self._rendered:
            mp = self._builder.QueryIMediaPosition()
            return mp.GetCurrentPosition()
        return 0

    def SetStopTime(self,pos):
        if self._builder and self._rendered:
            mp = self._builder.QueryIMediaPosition()
            mp.SetStopTime(pos)
    def GetStopTime(self):
        if self._builder and self._rendered:
            mp = self._builder.QueryIMediaPosition()
            return mp.GetStopTime()
        return 0

    def GetVideoWindow(self):
        try:
            return self._builder.QueryIVideoWindow()
        except dshow.error, arg:
            print arg
            return None

    def SetVisible(self,f):
        vw = self.GetVideoWindow()
        if vw:vw.SetVisible(f)
    def SetWindow(self,wnd,msgid=WM_GRPAPHNOTIFY):
        vw = self.GetVideoWindow()
        if vw:
            hwnd = wnd.GetSafeHwnd()
            vw.SetOwner(hwnd)
            mex = self._builder.QueryIMediaEventEx()
            mex.SetNotifyWindow(hwnd,msgid)

    def SetNotifyWindow(self,wnd,msgid=WM_GRPAPHNOTIFY):
        if self._builder and self._rendered:
            mex = self._builder.QueryIMediaEventEx()
            mex.SetNotifyWindow(wnd.GetSafeHwnd(),msgid)

    def GetWindowPosition(self):
        vw = self.GetVideoWindow()
        rc=(0,0,100,100)
        if vw:rc = vw.GetWindowPosition()
        return rc

    def SetWindowPosition(self,rc):
        vw = self.GetVideoWindow()
        if vw: vw.SetWindowPosition(rc)

    # get all filter names of GraphBuilder graph
    # note: The file reader filter gets its name from the file
    def GetFiltersNames(self):
        if not self._builder or not self._rendered: return []
        enumobj = self._builder.EnumFilters()
        f = enumobj.Next()
        filters = []
        while f:
            fname = f.QueryFilterName()
            filters.insert(0,fname)
            f = enumobj.Next()
        return filters

    def IsASF(self):
        if not self._builder or not self._rendered: return 0
        enumobj = self._builder.EnumFilters()
        f = enumobj.Next()
        while f:
            fname = f.QueryFilterName()
            if fname.find('ASF')>=0:
                return 1
            f = enumobj.Next()
        return 0

    def HasVideo(self):
        if not self._builder or not self._rendered: return None
        try:
            return self._builder.FindFilterByName('Video Renderer')
        except:
            return None

# a shortcut usefull when we want to know
# the type of an asf stream (video or audio)
def HasVideo(url):
    try:
        builder = GraphBuilder()
    except:
        print 'Missing DirectShow infrasrucrure'
        return None
    if not builder.RenderFile(url):
        return None
    return builder.HasVideo()

# Returns the size of a video
def GetVideoSize(url):
    try:
        builder = GraphBuilder()
    except:
        print 'Missing DirectShow infrasrucrure'
        return 100, 100

    if not builder.RenderFile(url):
        return 100, 100

    return builder.GetWindowPosition()[2:]


# Returns the duration of the media file in secs
def GetMediaDuration(url):
    try:
        builder = GraphBuilder()
    except:
        print 'Missing DirectShow infrasrucrure'
        return 0
    if not builder.RenderFile(url):
        return 0

    return builder.GetDuration()


class MMStream:
    def __init__(self, ddobj):
        mmstream = dshow.CreateMultiMediaStream()
        mmstream.Initialize()
        mmstream.AddPrimaryVideoMediaStream(ddobj)
        mmstream.AddPrimaryAudioMediaStream()
        self._mmstream = mmstream
        self._mstream = None
        self._ddstream = None
        self._sample = None
        self._dds = None
        self._rect = None
        self._parsed = 0

    def __repr__(self):
        s = '<%s instance' % self.__class__.__name__
        filters = self.getFiltersNames()
        n = len(filters)
        if n:
            s = s + ', filters = '
            s = s + "\'" + filters[0] + "\'"
        else:
            s = s + ', not rendered'

        for i in range(1,n):
            s = s + ", \'" + filters[i] + "\'"
        s = s + '>'
        return s

    def getFiltersNames(self):
        if not self._parsed: return []
        fg = self._mmstream.GetFilterGraph()
        enumobj = fg.EnumFilters()
        f = enumobj.Next()
        filters = []
        while f:
            fname = f.QueryFilterName()
            filters.insert(0,fname)
            f = enumobj.Next()
        return filters

    def open(self, url, exporter=None):
        mmstream =      self._mmstream
        try:
            self._mmstream.OpenFile(url)
        except:
            print 'failed to render', url
            self._parsed = 0
            return 0
        self._parsed = 1
        if exporter:
            fg = self._mmstream.GetFilterGraph()
            writer = exporter.getWriter()
            if writer:
                writer.redirectAudioFilter(fg, hint='0001')
        self._mstream = self._mmstream.GetPrimaryVideoMediaStream()
        self._ddstream = self._mstream.QueryIDirectDrawMediaStream()
        self._sample = self._ddstream.CreateSample()
        self._dds = ddraw.CreateSurfaceObject()
        self._rect = self._sample.GetSurface(self._dds)
        return 1

    def __del__(self):
        del self._mstream
        del self._ddstream
        del self._sample
        del self._mmstream

    def run(self):
        if self._parsed:
            self._mmstream.SetState(1)

    def stop(self):
        if self._parsed:
            self._mmstream.SetState(0)

    def update(self):
        if not self._parsed: return 0
        return self._sample.Update()

    def seek(self, secs):
        if not self._parsed: return
        if secs==0.0:
            v = dshow.large_int(0)
        else:
            msecs = dshow.large_int(int(secs*1000+0.5))
            f = dshow.large_int('10000')
            v = msecs * f
        try:
            self._mmstream.Seek(v)
        except:
            print 'seek not supported for media type'

    def getDuration(self):
        if not self._parsed: return
        d = self._mmstream.GetDuration()
        f = dshow.large_int('10000')
        v = d / f
        secs = 0.001*float(v)
        return secs

    def getTime(self):
        if not self._parsed: return
        d = self._mmstream.GetTime()
        f = dshow.large_int('10000')
        v = d / f
        secs = 0.001*float(v)
        return secs
