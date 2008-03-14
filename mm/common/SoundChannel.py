__version__ = "$Id$"

# XXXX Still needs some work, esp. in the callback time calc section
#
from Channel import ChannelAsync, PLAYING
import MMAttrdefs
import windowinterface
import time
import audio, audio.dev, audio.merge, audio.convert
import MMurl
import os
import string
import settings

debug = os.environ.has_key('CHANNELDEBUG')

# This should be a channel option
SECONDS_TO_BUFFER=4

class SoundChannel(ChannelAsync):
    node_attrs = ChannelAsync.node_attrs + [
            'clipbegin', 'clipend',
            'project_audiotype', 'project_targets',
            'project_perfect', 'project_mobile']

    # shared between all instances
    __playing = 0                   # # of active channels

    def __init__(self, name, attrdict, scheduler, ui):
        ChannelAsync.__init__(self, name, attrdict, scheduler, ui)
        if debug: print 'SoundChannel: init', name
        self.arm_fp = None
        self.play_fp = None
        self.__qid = None
        self.__evid = []
        self.__rc = None
        self.__playing = None

    def do_show(self, pchan):
        if not ChannelAsync.do_show(self, pchan):
            return 0
        # we can only be shown if we can play
        return player is not None or self.__rc is not None

    def getaltvalue(self, node):
        # Determine playability. Expensive, but this method is only
        # called when needed (i.e. the node is within a switch).
        fn = self.getfileurl(node)
        if not fn:
            return 0
        try:
            fn, hdr = MMurl.urlretrieve(fn)
        except (IOError, EOFError, audio.Error):
            return 0
        if string.find(hdr.type, 'real') >= 0:
            if self.__rc is None:
                try:
                    from RealChannel import RealChannel
                    self.__rc = RealChannel(self)
                except:
                    pass
            if self.__rc:
                return 1
            return 0
        try:
            fp = audio.reader(fn)
        except (IOError, EOFError, audio.Error):
            return 0
        return 1

    def do_arm(self, node, same=0):
        self.__ready = 0
        node.__type = ''
        if node.type != 'ext':
            self.errormsg(node, 'Node must be external.')
            return 1
        if debug: print 'SoundChannel: arm', node
        fn = self.getfileurl(node)
        if not fn:
            self.errormsg(node, 'No URL set on node.')
            return 1
        mtype = node.GetAttrDef('type', None)
        if not mtype:
            import urlcache
            mtype = urlcache.mimetype(fn)
        if mtype and string.find(mtype, 'real') >= 0:
            node.__type = 'real'
            if self.__rc is None:
                import RealChannel
                try:
                    self.__rc = RealChannel.RealChannel(self)
                except RealChannel.error, msg:
                    # can't do RealAudio
##                     self.__rc = 0 # don't try again
                    self.errormsg(node, msg)
            if self.__rc:
                if self.__rc.prepare_player(node):
                    self.__ready = 1
            return 1
        if player is None:
            return 1
        try:
            fn = MMurl.urlretrieve(fn)[0]
            self.arm_fp = audio.reader(fn)
            rate = self.arm_fp.getframerate()
        except IOError:
            self.errormsg(node, 'Cannot open audio file: %s' % fn)
            self.arm_fp = None
            self.armed_duration = 0
            return 1
        except EOFError:
            self.errormsg(node, 'Unexpected EOF in audio file: %s' % fn)
            self.arm_fp = None
            self.armed_duration = 0
            return 1
        except audio.Error, msg:
            self.errormsg(node, 'Error in audio file: %s\n\n%s.' % (fn, msg))
            self.arm_fp = None
            self.armed_duration = 0
            return 1
        self.armed_duration = duration = node.GetAttrDef('duration', None)
        begin = int(self.getclipbegin(node, 'sec') * rate + .5)
        end = int(self.getclipend(node, 'sec') * rate + .5)
        if begin or end or duration:
            if duration is not None and duration > 0:
                duration = int(duration * rate + .5)
                if not end or (begin or 0) + duration < end:
                    end = (begin or 0) + duration
            if begin or (end and end < self.arm_fp.getnframes()):
                from audio.select import select
                self.arm_fp = select(self.arm_fp, [(begin, end)])
        soundAlign = MMAttrdefs.getattr(node, 'soundAlign')
        if soundAlign != 'both':
            from audio.convert import onechannel
            self.arm_fp = onechannel(self,arm_fp, soundAlign)
        self.armed_markers = {}
        for mid, mpos, mname in self.arm_fp.getmarkers() or []:
            self.armed_markers[mname] = mpos
        self.__ready = 1
        return 1

    def __marker(self, node, marker):
        if self._played_node == node:
            node.marker(self._scheduler.timefunc(), marker)

    def do_play(self, node, curtime):
        self.__playing = node
        self.__type = node.__type
        start_time = node.get_start_time()
        if not self.__ready:
            # arming failed, so don't even try playing
            self.playdone(0, curtime)
            return
        if node.__type == 'real':
            if not self.__rc or not self.__rc.playit(node, start_time = start_time):
                self.playdone(0, curtime)
            return
        if not self.arm_fp or player is None:
##             print 'SoundChannel: not playing'
            self.play_fp = None
            self.arm_fp = None
            self.playdone(0, curtime)
            return

        if debug: print 'SoundChannel: play', node
        self.play_fp = self.arm_fp
        self.play_markers = self.armed_markers
        self.arm_fp = None
        self.armed_markers = {}
        rate = self.play_fp.getframerate()
        for arc in node.sched_children:
            mark = arc.marker
            if mark is None or not self.play_markers.has_key(mark):
                continue
            t = self.play_markers[mark] / float(rate) + (arc.delay or 0)
            arc.dstnode.parent.scheduled_children = arc.dstnode.parent.scheduled_children + 1
            if t <= 0:
                self._playcontext.trigger(arc)
            else:
                qid = self._scheduler.enter(t, 0, self._playcontext.trigger, (arc,))
                self.__evid.append(qid)
        for marker, t in self.play_markers.items():
            qid = self._scheduler.enter(t, 0, self.__marker, (node, marker))
            self.__evid.append(qid)
        t0 = self._scheduler.timefunc()
        mediadur = float(self.play_fp.getnframes()) / rate
        if t0 > start_time and not settings.get('noskip'):
            late = t0 - start_time
            if late > mediadur:
                self.playdone(0, max(curtime, start_time + mediadur))
                return
            from audio.select import select
            if __debug__: print 'skipping',start_time,t0,late
            self.play_fp = select(self.play_fp, [(int((late)*rate+.5), None)])
        try:
            player.play(self.play_fp, (self.my_playdone, (max(start_time + mediadur, curtime),)))
        except audio.Error, msg:
            print 'error reading file %s: %s' % (self.getfileurl(node), msg)
            self.playdone(0, curtime)
            return

    def my_playdone(self, curtime):
        if debug: print 'SoundChannel: playdone',`self`
        if self.play_fp:
            self.play_fp = None
            if self.__qid is not None:
                return
            self.playdone(0, curtime)

    def playstop(self, curtime):
        if debug: print 'SoundChannel: playstop'
        if self.__playing:
            if self.__type == 'real':
                if self.__rc:
                    self.__rc.stopit()
            else:
                for qid in self.__evid:
                    try:
                        self._scheduler.cancel(qid)
                    except:
                        pass
                self.__evid = []
                if self.__qid is not None:
                    self._scheduler.cancel(self.__qid)
                    self.__qid = None
                if self.play_fp:
                    player.stop(self.play_fp)
                    self.play_fp = None
            self.__playing = None
        #
        # There is a race here: the stopit() call above may have resulted in
        # a playdone() call (as happens on the Mac) and it may not.
        # We only call playdone if we see it hasn't happened yet.
        if self._playstate == PLAYING:
            self.playdone(1, curtime)

    def setpaused(self, paused, timestamp):
        if debug: print 'setpaused', paused
        if self.__rc:
            self.__rc.pauseit(paused)
        if player is not None:
            player.setpaused(paused)
        self._paused = paused

    def do_hide(self):
        if self.play_fp:
            player.stop(self.play_fp)
            nframes = self.play_fp.getnframes()
            if nframes == 0:
                nframes = 1
            rate = self.play_fp.getframerate()
            self.play_fp = None
            if self.__qid is not None:
                return
            t = self._played_node.get_start_time() + float(nframes) / rate
            self.__qid = self._scheduler.enterabs(t, 0, self.playdone, (0, t))
        if self.__rc:
            self.__rc.stopit()
            self.__rc.destroy()
            self.__rc = None
        ChannelAsync.do_hide(self)

class Player:
    def __init__(self):
        global SECONDS_TO_BUFFER
        # __merger, __converter, __tid, and __data are all None/'',
        # or none of them are.
        self.__pausing = 0      # whether we're pausing
        self.__port = audio.dev.writer(qsize = SECONDS_TO_BUFFER*48000) # Worst-case queuesize
        SECONDS_TO_BUFFER = float(self.__port.getfillable()) / 48000
        self.__merger = None    # merged readers
        self.__converter = None # merged readers, converted to port
        self.__tid = None       # timer id
        self.__framerate = 0
        self.__readsize = 0
        self.__timeout = 0
        self.__callbacks = []   # callbacks that we have to do
        self.__data = ''        # data already read but not yet played
        self.__framesread = 0   # total # of frames read
        self.__frameswritten = 0 # total # of frames written
        self.__nframes = 0      # number of frames in __data
        self.__prevpos = []     # list of previous positions

    def __read(self):
        converter = self.__converter
        self.__prevpos.append((self.__framesread, converter.getpos()))
        self.__data, self.__nframes = converter.readframes(self.__readsize)
        self.__framesread = self.__framesread + self.__nframes

    def __write(self):
        self.__port.writeframes(self.__data)
        self.__frameswritten = self.__frameswritten + self.__nframes
        self.__data = ''
        self.__nframes = 0

    def __stop(self):
        filled = self.__port.getfilled()
        self.__port.stop()
        played = self.__frameswritten - filled
        while 1:
            nframes, pos = self.__prevpos[-1]
            del self.__prevpos[-1]
            if nframes <= played:
                break
        self.__converter.setpos(pos)
        self.__framesread = played
        self.__frameswritten = played
        self.__nframes = 0
        n = played - nframes
        if n > 0:
            dummy, nframes = self.__converter.readframes(n)

    def __call(self):
        callbacks = self.__callbacks
        self.__callbacks = []
        for rdr, cb in callbacks:
            if self.__merger:
                self.__merger.delete(rdr)
            if cb:
                apply(cb[0], cb[1])

    def __callback(self, rdr, arg):
        self.__callbacks.append((rdr, arg))

    def play(self, rdr, cb):
        merger = self.__merger
        if not merger:
            merger = audio.merge.merge()
        else:
            if self.__tid:
                windowinterface.canceltimer(self.__tid)
                self.__tid = None
            self.__stop()
        try:
            # the call to merger.add could fail...
            merger.add(rdr, (self.__callback, (rdr, cb,)))
            if not self.__merger:
                self.__merger = merger
                self.__converter = audio.convert.convert(self.__merger,
                                         self.__port.getformats(),
                                         self.__port.getframerates())
                self.__framerate = self.__converter.getframerate()
                self.__readsize = int(SECONDS_TO_BUFFER*self.__framerate/2)
                if self.__readsize < 1024: # arbitrary minimum
                    self.__readsize = 1024
                self.__port.setformat(self.__converter.getformat())
                self.__port.setframerate(self.__converter.getframerate())
                fillable = self.__port.getfillable()
                if fillable < self.__readsize:
                    self.__readsize = fillable
                self.__timeout = 0.5 * self.__readsize / self.__framerate
                self.__prevpos = []
                self.__framesread = self.__frameswritten = 0
        finally:
            if self.__merger:
                self.__read()
                self.__playsome()

    def stop(self, rdr):
        for i in range(len(self.__callbacks)):
            if self.__callbacks[i][0] is rdr:
                del self.__callbacks[i]
                break
        if self.__merger:
            if self.__tid:
                windowinterface.canceltimer(self.__tid)
                self.__tid = None
            self.__stop()
            self.__merger.delete(rdr)
            self.__read()
            self.__playsome()

    def setpaused(self, paused):
        if (not self.__pausing) == (not paused):
            return
        self.__pausing = paused
        if not self.__merger:
            return
        if paused:
            self.__stop()
            self.__read()
            if self.__tid:
                windowinterface.canceltimer(self.__tid)
                self.__tid = None
        else:
            self.__playsome()

    def __playsome(self):
        self.__tid = None
        port = self.__port
        while 1:
            if not self.__data:
                port.wait()
                self.__merger = None
                self.__converter = None
                self.__call()
                return
            self.__write()
            self.__call()
            self.__read()
            if not self.__data:
                timeout = float(port.getfilled())/self.__framerate - 0.1
                if timeout > 0:
                    self.__tid = windowinterface.settimer(
                            timeout, (self.__playsome, ()))
                    return
                # else we go back into the loop to stop
                # playing immediately
            else:
                timeout = float(port.getfilled()/2)/self.__framerate
                self.__tid = windowinterface.settimer(timeout,
                                        (self.__playsome, ()))
                return

try:
    player = Player()
except:
    player = None
