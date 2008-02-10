__version__ = "$Id$"

import windowinterface
import wmwriter

def haswmpruntimecomponents():
    try:
        import wmfapi
        dummy = wmfapi.CreateProfileManager()
    except:
        return 0
    return 1

msgUnresolvedDur =\
"""Warning: Document duration is unresolved.
Only an initial part of the document will be exported.
The progress dialog may not be dismissed automatically.
When you don't see any progress activity, please press Cancel to stop."""


class Exporter:
    def __init__(self, filename, player, profile=15):
        self.filename = filename
        self.player = player
        self.writer = None
        self.profile = profile
        self.topwindow = None
        self.completed = 0

        # set avgTimePerFrame to something good enough for non-video presentations
        self.avgTimePerFrame = 500 # msec

        self.parent = windowinterface.getmainwnd()
        self.progress = windowinterface.ProgressDialog("Exporting", self.cancel_callback, self.parent, 0, 1)
        self.progress.set('Exporting document to WMP...')

        self.timefunc = self.player.scheduler.timefunc
        self.player.exportplay(self)

    def __del__(self):
        del self.writer
        del self.player
        del self.topwindow

    def createWriter(self, window):
        if self.topwindow:
            print "Cannot export multiple topwindows"
            return
        self.topwindow = window

        if self._hasvideo():
            self.avgTimePerFrame = 100
        self.fulldur = self.player.userplayroot.calcfullduration()
        if self.fulldur is None or self.fulldur<0:
            windowinterface.showmessage(msgUnresolvedDur, mtype = 'warning', parent=self.parent)

        self.writer = wmwriter.WMWriter(self, window.getDrawBuffer(), self.profile, self.avgTimePerFrame)
        self._setAudioFormat()
        self.writer.setOutputFilename(self.filename)
        self.writer.beginWriting()

    def getWriter(self):
        return self.writer

    def changed(self, topchannel, window, event, timestamp):
        # Callback from the player: the bits in the window have changed
        if self.topwindow:
            if self.topwindow != window:
                return
            elif self.writer and self.progress:
                dt = self.timefunc()
                self.writer.update(dt)
                if self.progress:
                    p = self._getprogress(dt)
                    self.progress.set('Exporting document to WMP...', p, 100, p, 100)

    def audiofragment(self, af):
        dt = self.timefunc()
        if self.progress:
            p = self._getprogress(dt)
            self.progress.set('Exporting document to WMP...', p, 100, p, 100)

    def finished(self):
        if self.progress:
            self.progress.set('Encoding document for WMP...', 100, 100, 100, 100)
        if self.writer:
            self.writer.endWriting()
            self.writer = None
            self.topwindow = None
        windowinterface.sleep(1)
        if self.progress:
            del self.progress
            self.progress = None
        stoptime = windowinterface.getcurtime()
        windowinterface.settimevirtual(0)

    def cancel_callback(self):
        if self.progress:
            del self.progress
            self.progress = None
        self.player.stop()
        windowinterface.showmessage('Export interrupted.', parent=self.parent)

    def fail_callback(self):
        if self.progress:
            del self.progress
            self.progress = None
        self.player.stop()
        windowinterface.showmessage('Export failed.', parent=self.parent)

    def _getNodesOfType(self, ntype, node, urls):
        if node.GetType()=='ext':
            chan = self.player.getchannelbynode(node)
            chtype = chan._attrdict.get('type')
            if chtype == ntype:
                urls.append(chan.getfileurl(node))
        for child in node.GetSchedChildren():
            self._getNodesOfType(ntype, child, urls)

    def _setAudioFormat(self):
        urls = []
        self._getNodesOfType('sound', self.player.userplayroot, urls)
        if urls:
            self.writer.setAudioFormatFromFile(urls[0])

    def _getprogress(self, dt):
        if self.fulldur is not None and self.fulldur>0:
            return 100.0*dt/self.fulldur
        # dur unresolved
        # give the illusion that is resolved
        # using a converging sequence
        d = 15
        i = 1
        p = 0
        while 1:
            f = 100.0/pow(2.0,i)
            if dt<d*i:
                return int(p + f*((dt-d*(i-1))/d))
            else:
                p = p + f
            i = i + 1

    def _hasvideo(self):
        urls = []
        self._getNodesOfType('video', self.player.userplayroot, urls)
        return len(urls)!=0
