__version__ = "$Id$"

#
# Selecter module - Handles hyperjumps and assigning contexts.
#

import MMAttrdefs
import Scheduler
from MMTypes import *
from MMExc import *                     # exceptions
import MMStates
import Hlinks
import windowinterface
import SR
import sys

class Selecter:
    def __init__(self):
        self.scheduler = Scheduler.Scheduler(self)

    #
    # State transitions.
    #
    def play(self, starttime = 0):
        if self.playing:
            raise 'Already playing'
        if sys.platform == 'wince':
            import settings
            if settings.get('skin'):
                windowinterface.HideMenuBar()
            else:
                windowinterface.ShowMenuBar()
        self.reset(starttime)
        self.sctx = self.scheduler.play(self.userplayroot, None, None, None, timestamp = 0)
        if not self.sctx:
            return
        self.playing = 1
        paused = self.scheduler.paused
        self.scheduler.paused = 0
        self.sctx.flushqueue(starttime)
        self.scheduler.paused = paused
        self.showstate()
    #
    def stop(self):
        if self.playing:
            self.scheduler.stop_all(self.scheduler.timefunc())
        else:
            self.fullreset()
        if sys.platform == 'wince':
            windowinterface.ShowMenuBar()

    def stopped(self):
        self.playing = 0
        self.showstate()
    #
    def reset(self, starttime = 0):
        self.scheduler.resettimer(starttime)
    #
    # Callback for anchor activations, called by channels.
    # Return 1 if the anchor fired, 0 if nothing happened.
    # XXXX This routine should also get a source-context arg.
    #
    def anchorfired(self, old_sctx, node, arg):
        #self.showpauseanchor(0) # also see Scheduler.py
        # Firing an anchor continues the player if it was paused.
        if self.scheduler.getpaused():
            self.toplevel.waspaused = 1
            self.pause(0)
        else:
            self.toplevel.waspaused = 0
        destlist = self.context.hyperlinks.findsrclinks(node)
        if not destlist:
            windowinterface.showmessage(
                    'No hyperlink source at this anchor')
            return 0
        root = node.GetRoot()
        for dest in destlist:
            if not self.context.isgoodlink(dest, root):
                continue
            if not self.gotoanchor(dest, arg):
                return 0
        return 1

    def gotoanchor(self, link, arg):
        anchor1 = link[Hlinks.ANCHOR1]
        show = MMAttrdefs.getattr(anchor1, 'show')
        sstate = MMAttrdefs.getattr(anchor1, 'sourcePlaystate')
        dstate = MMAttrdefs.getattr(anchor1, 'destinationPlaystate')
        if show == 'replace':
            # ignore sourcePlaystate
            ltype = Hlinks.TYPE_JUMP
            stype = Hlinks.A_SRC_PAUSE
        elif show == 'pause':
            # ignore sourcePlaystate
            ltype = Hlinks.TYPE_FORK
            stype = Hlinks.A_SRC_PAUSE
        elif show == 'new':
            ltype = Hlinks.TYPE_FORK
            if sstate == 'play':
                stype = Hlinks.A_SRC_PLAY
            elif sstate == 'pause':
                stype = Hlinks.A_SRC_PAUSE
            else:
                stype = Hlinks.A_SRC_STOP
        if dstate == 'play':
            dtype = Hlinks.A_DEST_PLAY
        else:
            dtype = Hlinks.A_DEST_PAUSE
        anchor2 = link[Hlinks.ANCHOR2]
        if MMAttrdefs.getattr(anchor1, 'external') or ltype != Hlinks.TYPE_JUMP or type(anchor2) is type(''):
            return self.toplevel.jumptoexternal(anchor1, anchor2, ltype, stype, dtype)
        return self.gotonode(anchor2, arg)

    def gotonode(self, seek_node, arg):
        # First check whether this is an indirect anchor
        if __debug__:
            if Scheduler.debugevents: print 'gotonode',seek_node,arg
        self.scheduler.setpaused(1)
        timestamp = self.scheduler.timefunc()
        sctx = self.scheduler.sctx_list[0]
        if seek_node.playing != MMStates.IDLE:
            # case 1, the target element is or has been active
            if seek_node.playing in (MMStates.PLAYED, MMStates.FROZEN):
                gototime = seek_node.time_list[0][0]
            else:
                gototime = seek_node.start_time
        else:
            # XXX
            x = seek_node
            path = []
            while x is not None:
                resolved = x.isresolved(sctx)
                path.append((x, resolved))
                if resolved is not None:
                    break
                x = x.GetSchedParent()
            path.reverse()
            for x, resolved in path:
                if x.playing in (MMStates.PLAYING, MMStates.PAUSED):
                    gototime = x.start_time
                elif x.playing in (MMStates.PLAYED, MMStates.FROZEN):
                    gototime = x.time_list[0][0]
                elif resolved is not None:
                    gototime = resolved
                else:
                    x.start_time = gototime
        self.scheduler.settime(gototime)
        if seek_node.GetType() == 'switch':
            x = seek_node.ChosenSwitchChild()
            if not x:
                x = seek_node.GetSchedParent()
        else:
            x = seek_node
        path = []
        while x is not None:
            path.append(x)
            x = x.GetSchedParent()
        path.reverse()
        sctx.gototime(path[0], gototime, timestamp, path)
        self.scheduler.setpaused(0, gototime)
        return 0

    #
    # sctx_empty is called from the scheduler when a context has become
    # empty.
    def sctx_empty(self, sctx, curtime):
        sctx.stop(curtime)
        self.sctx = None

def nodename(node):
    if node is None:
        return '<none>'
    str = MMAttrdefs.getattr(node, 'name')
    str = str + '#' + node.GetUID()
    return str
