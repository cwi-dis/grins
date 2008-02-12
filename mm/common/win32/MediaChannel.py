__version__ = "$Id$"

# @win32doc|MediaChannel

# This module encapsulates a sufficient part
# of the DirectShow infrastructure to
# implement win32 audio and video media channels.

# Any media type supported by Windows Media Player is also supported by
# this module: (.avi,.asf,.rmi,.wav,.mpg,.mpeg,.m1v,.mp2,.mpa,.mpe,.mid,
# .rmi,.qt,.aif,.aifc,.aiff,.mov,.au,.snd)

# Note that DirectShow builds a graph of filters
# appropriate to parse-render each media type from those filters
# available on the machine. A new parsing filter installed enhances
# the media types that can be played both by GRiNS and Windows MediaPlayer.

# node attributes
import MMAttrdefs

# URL module
import MMurl, urllib

# use: addclosecallback, genericwnd, register, unregister
import windowinterface

# DirectShow support
import win32dxm

# QuickTime support
import winqt

# we need const WM_USER
import win32con

import settings

# private graph notification message
WM_GRPAPHNOTIFY=win32con.WM_USER+101

# private redraw message
WM_REDRAW=win32con.WM_USER+102

class error(Exception):
    pass

class MediaChannel:
    def __init__(self, channel):

        # DirectShow Graph builders
        self.__channel = channel
        self.__armBuilder=None
        self.__playBuilder=None
        self.__playBegin=0
        self.__playEnd=0
        self.__armFileHasBeenRendered=0
        self.__playFileHasBeenRendered=0

        # main thread monitoring fiber id
        self.__fiber_id=None
        self.__playdone=1

        # notification mechanism for not window channels
        self.__notifyWindow = None
        self.__window = None

    def release_player(self):
        if self.__playBuilder:
            self.__playBuilder=None
        if self.__notifyWindow and self.__notifyWindow.IsWindow():
            self.__notifyWindow.DestroyWindow()
        self.__notifyWindow=None

    def release_armed_player(self):
        if self.__armBuilder:
            self.__armBuilder=None

    def release_res(self):
        self.release_armed_player()
        self.release_player()
        self.__channel = None

    # We must start downloading here,
    # show a message on the media subwindow
    # and return immediately.
    # For local files we don't have to do anything.
    # Do not use  MMurl.urlretrieve since as it
    # is now implemented blocks the application.
    def prepare_player(self, node = None, window=None):
        self.release_armed_player()
        try:
            self.__armBuilder = win32dxm.GraphBuilder()
        except:
            self.__armBuilder=None

        if not self.__armBuilder:
            raise error, 'Cannot create GraphBuilder to render item.'

        url=self.__channel.getfileurl(node)
        if not url:
            raise error, 'No URL on node.'

        if MMurl.urlretrieved(url):
            url = MMurl.urlretrieve(url)[0]

        if not self.__armBuilder.RenderFile(url, self.__channel._exporter):
            self.__armFileHasBeenRendered=0
            raise error, 'Cannot render: '+url

        self.__sync = node.GetSyncBehavior(), node.GetSyncTolerance(), MMAttrdefs.getattr(node, 'syncMaster')
        if self.__sync[0] == 'locked' and self.__sync[1] < 0:
            self.__sync = 'canSlip', self.__sync[1], self.__sync[2]
        self.__armFileHasBeenRendered=1
        return 1


    def playit(self, node, curtime, window = None, start_time = 0):
        if not self.__armBuilder:
            return 0

        self.release_player()
        self.__playBuilder=self.__armBuilder
        self.__armBuilder=None
        if not self.__armFileHasBeenRendered:
            self.__playFileHasBeenRendered=0
            return 0
        self.__playFileHasBeenRendered=1
        self.__start_time = start_time

        # get duration in secs (float)
        duration = node.GetAttrDef('duration', None)
        clip_begin = self.__channel.getclipbegin(node,'sec')
        clip_end = self.__channel.getclipend(node,'sec')
        self.__playBegin = clip_begin

        if duration is not None and duration >= 0:
            if not clip_end:
                clip_end = self.__playBegin + duration
            else:
                clip_end = min(clip_end, self.__playBegin + duration)
        if clip_end:
            self.__playBuilder.SetStopTime(clip_end)
            self.__playEnd = clip_end
        else:
            self.__playEnd = self.__playBuilder.GetDuration()

        t0 = self.__channel._scheduler.timefunc()
        syncBehavior, syncTolerance, syncMaster = self.__sync
        if syncBehavior == 'locked' and t0 > start_time + syncTolerance and not self.__channel._exporter:
            if syncMaster:
                self.__channel._scheduler.settime(self.__start_time)
            elif not settings.get('noskip'):
                if __debug__:
                    print 'skipping',start_time,t0,t0-start_time
                mediadur = self.__playEnd - self.__playBegin
                late = t0 - start_time
                if late > mediadur:
                    self.__channel.playdone(0, start_time + mediadur)
                    return 1
                clip_begin = clip_begin + late
        self.__playBuilder.SetPosition(clip_begin)

        if window:
            self.adjustMediaWnd(node,window, self.__playBuilder)
            self.__playBuilder.SetWindow(window,WM_GRPAPHNOTIFY)
            window.HookMessage(self.OnGraphNotify,WM_GRPAPHNOTIFY)
        elif not self.__notifyWindow:
            self.__notifyWindow = windowinterface.genericwnd()
            self.__notifyWindow.create()
            self.__notifyWindow.HookMessage(self.OnGraphNotify,WM_GRPAPHNOTIFY)
            self.__playBuilder.SetNotifyWindow(self.__notifyWindow,WM_GRPAPHNOTIFY)
        self.__playdone=0
        self.__playBuilder.Run()
        self.__register_for_timeslices()
        return 1

    def pauseit(self, paused):
        if self.__playBuilder:
            if paused:
                self.__playBuilder.Pause()
                self.__unregister_for_timeslices()
            else:
                self.__playBuilder.Run()
                self.__register_for_timeslices()

    def stopit(self):
        if self.__playBuilder:
            self.__playBuilder.Stop()
            self.__unregister_for_timeslices()

    def freezeit(self):
        if self.__playBuilder:
            self.__playBuilder.Pause()
            self.__unregister_for_timeslices()

    def showit(self,window):
        if self.__playBuilder:
            self.__playBuilder.SetVisible(1)

    def destroy(self):
        self.__unregister_for_timeslices()
        self.release_player()

    def setsoundlevel(self, lev, maxlev=1):
        # set sound level but do not apply
        print 'setsoundlevel', lev, maxlevel

    def updatesoundlevel(self, lev, maxlev):
        # apply sound level
        print 'updatesoundlevel', lev, maxlevel

    # Set Window Media window size from fit and center, and coordinates attributes
    def adjustMediaWnd(self,node,window,builder):
        if not window: return
        builder.SetWindowPosition(self.__channel.getMediaWndRect())

    def paint(self):
        if not hasattr(self.__channel,'window'): return
        window = self.__channel.window
        if window and self.__playFileHasBeenRendered:
            window.paint()

    # capture end of media
    def OnGraphNotify(self,params):
        if self.__playBuilder and not self.__playdone:
            t=self.__playBuilder.GetPosition()
            if t>=self.__playEnd:self.OnMediaEnd()

    def OnMediaEnd(self):
        if not self.__playBuilder:
            return
        self.__playdone=1
        self.__channel.playdone(0, self.__start_time + self.__playEnd - self.__playBegin)

    def onIdle(self):
        if self.__playBuilder and not self.__playdone:
            t_sec = self.__playBuilder.GetPosition()
            t = self.__channel._scheduler.timefunc() - self.__start_time + self.__playBegin
            syncBehavior, syncTolerance, syncMaster = self.__sync
            if t_sec >= self.__playEnd:
                self.OnMediaEnd()
            elif syncBehavior == 'locked' and not (t_sec - syncTolerance < t < t_sec + syncTolerance):
                # we're out of sync
                if syncMaster:
                    # we're the master: adjust the system clock
                    self.__channel._scheduler.settime(t_sec + self.__start_time - self.__playBegin)
                else:
                    # we're a slave: reposition ourselves
                    self.__playBuilder.Pause()
                    self.__playBuilder.SetPosition(t)
                    self.__playBuilder.Run()
            self.paint()

    def __register_for_timeslices(self):
        if self.__fiber_id is None:
            self.__fiber_id = windowinterface.setidleproc(self.onIdle)

    def __unregister_for_timeslices(self):
        if self.__fiber_id is not None:
            windowinterface.cancelidleproc(self.__fiber_id)
            self.__fiber_id = None


###################################

class VideoStream:
    def __init__(self, channel):
        self.__channel = channel
        self.__mmstream = None
        self.__window = None
        self.__playBegin=0
        self.__playEnd=0
        self.__playdone=1
        self.__fiber_id=None
        self.__rcMediaWnd = None
        self.__qid = self.__dqid = None

    def destroy(self):
        if self.__window:
            self.__window.removevideo()
        del self.__mmstream
        self.__mmstream = None

    def prepare_player(self, node, window):
        if not window:
            raise error, 'No window to render in.'
        ddobj = window._topwindow.getDirectDraw()
        self.__mmstream = win32dxm.MMStream(ddobj)

        url=self.__channel.getfileurl(node)
        if not url:
            raise error, 'No URL on node.'

        if MMurl.urlretrieved(url):
            url = MMurl.urlretrieve(url)[0]

        if not self.__mmstream.open(url, self.__channel._exporter):
            raise error, 'Cannot render: %s'% url

        self.__sync = node.GetSyncBehavior(), node.GetSyncTolerance(), MMAttrdefs.getattr(node, 'syncMaster')

        return 1

    def playit(self, node, curtime, window, start_time = 0):
        if not window: return 0
        if not self.__mmstream: return 0

        self.__pausedelay = 0
        self.__pausetime = 0
        self.__start_time = start_time
        duration = node.GetAttrDef('duration', None)
        clip_begin = self.__channel.getclipbegin(node,'sec')
        clip_end = self.__channel.getclipend(node,'sec')
        self.__playBegin = clip_begin

        if duration is not None and duration >= 0:
            if not clip_end:
                clip_end = clip_begin + duration
            else:
                clip_end = min(clip_end, clip_begin + duration)
        if clip_end:
            self.__playEnd = clip_end
        else:
            self.__playEnd = self.__mmstream.getDuration()

        t0 = self.__channel._scheduler.timefunc()
        syncBehavior, syncTolerance, syncMaster = self.__sync
        if syncBehavior == 'locked' and t0 > start_time + syncTolerance and not self.__channel._exporter:
            if syncMaster:
                self.__channel._scheduler.settime(self.__start_time)
            elif not settings.get('noskip'):
                if __debug__: print 'skipping',start_time,t0,t0-start_time
                mediadur = self.__playEnd - self.__playBegin
                late = t0 - start_time
                if late > mediadur:
                    self.__channel.playdone(0, start_time + mediadur)
                    return 1
                clip_begin = clip_begin + late
        self.__mmstream.seek(clip_begin)

        self.__playdone=0

        window.setvideo(self.__mmstream._dds, self.__channel.getMediaWndRect(), self.__mmstream._rect)
        self.__window = window
        self.__mmstream.run()
        self.__mmstream.update()
        self.__window.update()
        self.__register_for_timeslices()

        return 1

    def stopit(self):
        if self.__dqid:
            try:
                self.__channel._scheduler.cancel(self.__dqid)
            except:
                pass
            self.__dqid = None
        if self.__qid:
            try:
                self.__channel._scheduler.cancel(self.__qid)
            except:
                pass
            self.__qid = None
        if self.__mmstream:
            self.__mmstream.stop()
            self.__unregister_for_timeslices()

    def pauseit(self, paused):
        if self.__mmstream:
            t0 = self.__channel._scheduler.timefunc()
            if paused:
                if self.__dqid:
                    try:
                        self.__channel._scheduler.cancel(self.__dqid)
                    except:
                        pass
                    self.__dqid = None
                if self.__qid:
                    try:
                        self.__channel._scheduler.cancel(self.__qid)
                    except:
                        pass
                    self.__qid = None
                self.__mmstream.stop()
                self.__unregister_for_timeslices()
                self.__pausetime = t0
            else:
                self.__pausedelay = self.__pausedelay + t0 - self.__pausetime
                self.__mmstream.run()
                self.__register_for_timeslices()

    def freezeit(self):
        if self.__mmstream:
            self.__mmstream.stop()
            self.__unregister_for_timeslices()

    def onMediaEnd(self):
        if not self.__mmstream:
            return
        self.__playdone=1
        self.__channel.playdone(0, self.__start_time + self.__playEnd - self.__playBegin)

    def onIdle(self):
        if self.__mmstream and not self.__playdone:
            running = self.__mmstream.update()
            t_sec = self.__mmstream.getTime()
            if self.__window:
                self.__window.update(self.__window.getwindowpos())
            t = self.__channel._scheduler.timefunc() - self.__start_time + self.__playBegin
            syncBehavior, syncTolerance, syncMaster = self.__sync
            if not running or t_sec >= self.__playEnd:
                self.onMediaEnd()
            elif syncBehavior == 'locked' and not (t_sec - syncTolerance < t < t_sec + syncTolerance):
                # we're out of sync
                if syncMaster:
                    # we're the master: adjust the system clock
                    self.__channel._scheduler.settime(t_sec + self.__start_time - self.__playBegin)
                else:
                    # we're a slave: reposition ourselves
                    self.__mmstream.stop()
                    self.__mmstream.seek(t)
                    self.__mmstream.run()

    def __register_for_timeslices(self):
        if self.__fiber_id is None:
            self.__fiber_id = windowinterface.setidleproc(self.onIdle)

    def __unregister_for_timeslices(self):
        if self.__fiber_id is not None:
            windowinterface.cancelidleproc(self.__fiber_id)
            self.__fiber_id = None

##################################################
HasQtSupport = winqt.HasQtSupport

class QtChannel:
    def __init__(self, channel):
        self.__channel = channel
        self.__qtplayer = None

        self.__playBegin = 0
        self.__playEnd = 0
        self.__playdone = 1

        self.__fiber_id = None
        self.__qid = self.__dqid = None

        # video sig
        self.__window = None
        self.__rcMediaWnd = None

    def destroy(self):
        if self.__window:
            self.__window.removevideo()
        del self.__qtplayer

    def prepare_player(self, node, window = None):
        self.__qtplayer = winqt.QtPlayer()

        url = self.__channel.getfileurl(node)
        if not url:
            raise error, 'No URL on node.'

        try:
            fn = MMurl.urlretrieve(url)[0]
        except IOError, arg:
            if type(arg) == type(()):
                arg = arg[-1]
            raise error, 'Cannot open: %s\n\n%s.'% (url, arg)

        if not self.__qtplayer.open(fn, exporter = self.__channel._exporter, asaudio = window is None):
            raise error, 'Cannot render: %s'% url
        if window:
            ddobj = window._topwindow.getDirectDraw()
            self.__qtplayer.createVideoDDS(ddobj)
        self.__sync = node.GetSyncBehavior(), node.GetSyncTolerance(), MMAttrdefs.getattr(node, 'syncMaster')
        return 1

    def playit(self, node, curtime, window = None, start_time = 0):
        if not self.__qtplayer:
            return 0

        self.__pausedelay = 0
        self.__pausetime = 0
        self.__start_time = start_time
        duration = node.GetAttrDef('duration', None)
        clip_begin = self.__channel.getclipbegin(node,'sec')
        clip_end = self.__channel.getclipend(node,'sec')
        self.__playBegin = clip_begin

        if duration is not None and duration >= 0:
            if not clip_end:
                clip_end = clip_begin + duration
            else:
                clip_end = min(clip_end, clip_begin + duration)
        if clip_end:
            self.__playEnd = clip_end
        else:
            self.__playEnd = self.__qtplayer.getDuration()

        t0 = self.__channel._scheduler.timefunc()
        syncBehavior, syncTolerance, syncMaster = self.__sync
        if syncBehavior == 'locked' and t0 > start_time + syncTolerance and not self.__channel._exporter:
            if syncMaster:
                self.__channel._scheduler.settime(self.__start_time)
            elif not settings.get('noskip'):
                if __debug__: print 'skipping',start_time,t0,t0-start_time
                mediadur = self.__playEnd - self.__playBegin
                late = t0 - start_time
                if late > mediadur:
                    self.__channel.playdone(0, start_time + mediadur)
                    return 1
                clip_begin = clip_begin + late
        self.__qtplayer.seek(clip_begin)

        self.__playdone=0

        if window:
            self.__window = window
            window.setvideo(self.__qtplayer._dds, self.__channel.getMediaWndRect(), self.__qtplayer._rect)
        self.__qtplayer.run()
        self.__qtplayer.update()
        if window:
            window.update()
        self.__register_for_timeslices()

        return 1

    def stopit(self):
        if self.__dqid:
            try:
                self.__channel._scheduler.cancel(self.__dqid)
            except:
                pass
            self.__dqid = None
        if self.__qid:
            try:
                self.__channel._scheduler.cancel(self.__qid)
            except:
                pass
            self.__qid = None
        if self.__qtplayer:
            self.__qtplayer.stop()
            self.__unregister_for_timeslices()

    def pauseit(self, paused):
        if self.__qtplayer:
            t0 = self.__channel._scheduler.timefunc()
            if paused:
                if self.__dqid:
                    try:
                        self.__channel._scheduler.cancel(self.__dqid)
                    except:
                        pass
                    self.__dqid = None
                if self.__qid:
                    try:
                        self.__channel._scheduler.cancel(self.__qid)
                    except:
                        pass
                    self.__qid = None
                self.__qtplayer.stop()
                self.__unregister_for_timeslices()
                self.__pausetime = t0
            else:
                self.__pausedelay = self.__pausedelay + t0 - self.__pausetime
                self.__qtplayer.run()
                self.__register_for_timeslices()

    def freezeit(self):
        if self.__qtplayer:
            self.__qtplayer.stop()
            self.__unregister_for_timeslices()

    def onMediaEnd(self):
        if not self.__qtplayer:
            return
        self.__playdone=1
        self.__channel.playdone(0, self.__start_time + self.__playEnd - self.__playBegin)

    def onIdle(self):
        if self.__qtplayer and not self.__playdone:
            running = self.__qtplayer.update()
            t_sec = self.__qtplayer.getTime()
            if self.__window:
                self.__window.update(self.__window.getwindowpos())
            t = self.__channel._scheduler.timefunc() - self.__start_time + self.__playBegin
            syncBehavior, syncTolerance, syncMaster = self.__sync
            if not running or t_sec >= self.__playEnd:
                self.onMediaEnd()
            elif syncBehavior == 'locked' and not (t_sec - syncTolerance < t < t_sec + syncTolerance):
                # we're out of sync
                if syncMaster:
                    # we're the master: adjust the system clock
                    self.__channel._scheduler.settime(t_sec + self.__start_time - self.__playBegin)
                else:
                    # we're a slave: reposition ourselves
                    self.__qtplayer.stop()
                    self.__qtplayer.seek(t)
                    self.__qtplayer.run()

    def __register_for_timeslices(self):
        if self.__fiber_id is None:
            self.__fiber_id = windowinterface.setidleproc(self.onIdle)

    def __unregister_for_timeslices(self):
        if self.__fiber_id is not None:
            windowinterface.cancelidleproc(self.__fiber_id)
            self.__fiber_id = None


##################################################
import dsound
import MMurl
import math

class DirectSound:
    def __init__(self):
        import win32ui
        hwnd = win32ui.GetMainFrame().GetSafeHwnd()
        self._dsound = dsound.CreateDirectSound()
        self._dsound.SetCooperativeLevel(hwnd, dsound.DSSCL_NORMAL)
        dsbdesc = dsound.CreateDSBufferDesc()
        dsbdesc.SetFlags(dsound.DSBCAPS_PRIMARYBUFFER)
        self._primarysb = self._dsound.CreateSoundBuffer(dsbdesc)

        # increase and restore volume on exit?
        # ...

    def __del__(self):
        del self._primarysb
        del self._dsound

    def createBufferFromFile(self, filename):
        dsbdesc = dsound.CreateDSBufferDesc()
        dsbdesc.SetFlags(dsound.DSBCAPS_CTRLDEFAULT)
        sb = None
        try:
            sb = self._dsound.CreateSoundBufferFromFile(dsbdesc, filename)
        except dsound.error, arg:
            print arg
            sb = None
        return sb


class DSPlayer:
    directSound = None
    dsrefcount = 0
    def __init__(self, channel):
        self.__channel = channel
        self._sound = None
        if self.directSound is None:
            DSPlayer.directSound    = DirectSound()
        DSPlayer.dsrefcount = DSPlayer.dsrefcount + 1

    def prepare_player(self, node):
        f = self.__channel.getfileurl(node)
        if not f:
            self.__channel.errormsg(node, 'No URL set on node.')
            raise error, 'No URL set on node.'
            return 0
        try:
            f = MMurl.urlretrieve(f)[0]
        except IOError, arg:
            if type(arg) is type(self):
                # XXXX This does not look correct...
                arg = arg.strerror
            raise error, 'Cannot open: %s\n\n%s.' % (f, arg)
            return 0
        self._sound = DSPlayer.directSound.createBufferFromFile(f)
        return 1

    def playit(self, node, curtime, start_time=0):
        #print 'playit', node, start_time
        if self._sound:
            a = self.getAttenuation(self._soundLevel, self._soundLevelMax)
            self._sound.SetVolume(a)
            self._sound.SetCurrentPosition(0)
            self._sound.Play()
            return 1 # OK
        return 0 # FAILED

    def stopit(self):
        if self._sound:
            self._sound.Stop()
        #print 'stopit'

    def destroy(self):
        del self._sound
        self._sound = None
        DSPlayer.dsrefcount = DSPlayer.dsrefcount - 1
        if DSPlayer.dsrefcount == 0:
            DSPlayer.directSound = None
        #print 'destroy'

    def pauseit(self, paused):
        if self._sound:
            if paused:
                self._sound.Stop()
            else:
                self._sound.Play()

    def setsoundlevel(self, lev, maxlev):
        self._soundLevel = lev
        self._soundLevelMax = maxlev
        # do not apply

    def updatesoundlevel(self, lev, maxlev):
        a = self.getAttenuation(lev, maxlev)
        if self._sound:
            self._sound.SetVolume(a)

    def getAttenuation(self, soundLevel, soundLevelMax):
        soundLevelMax = max(soundLevel, soundLevelMax)
        if soundLevel <= 0.0:
            return dsound.DSBVOLUME_MIN
        ratio = soundLevelMax/float(soundLevel)
        return int(-1000.0*math.log10(ratio)/math.log10(2))
