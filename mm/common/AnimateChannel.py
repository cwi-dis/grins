__version__ = "$Id$"

#
# Animate Channel (Virtual)
#

# This channel is also a kind of a player as are the other channels.
# It belongs to the 'control' family of channels (python, socket, etc)
# It is not actually very different from a python channel.
# It also executes a kind of a script.
# The script it executes is build from the animate elements of the document.
# The special thing with this one is that it has no effect by itself.
# Its effect comes from the script's target channel.
# It acts on its target channel by changing its attributes.
# The strong relation with its target channel and the fact
# that is an async channel is what makes it special.

import Channel
import MMAttrdefs
import Animators

# for timer support
import windowinterface

debug = 0
USE_IDLE_PROC=hasattr(windowinterface, 'setidleproc')

class AnimateChannel(Channel.ChannelAsync):
    node_attrs = ['targetElement','attributeName',
            'attributeType','additive','accumulate',
            'calcMode', 'values', 'keyTimes',
            'keySplines', 'from', 'to', 'by',
            'path', 'origin',]

    def __init__(self, name, attrdict, scheduler, ui):
        Channel.ChannelAsync.__init__(self, name, attrdict, scheduler, ui)
        self.__duration = None
        self.__animating = None
        self.__curloop = 0
        self.__moreloops = 0
        self.__effAnimator = None

    def __repr__(self):
        return '<AnimateChannel instance, name=' + `self._name` + '>'

    #
    # Channel overrides
    #

    def do_play(self, node, curtime):
        Channel.ChannelAsync.do_play(self, node, curtime)

        self.__initEngine(node)

        if not self.__ready():
            self.playdone(0, curtime)
            return

        # take into account accumulation effect
        # self.__curloop  is the zero based loop counter
        if node.looping_body_self:
            if hasattr(node.looping_body_self, 'loopcount'):
                self.__curloop = 1 + node.looping_body_self.loopcount
            else:
                self.__curloop = 0

        # do we have more loops?
        self.__moreloops = node.curloopcount != 0

        self.__animating = node

        # get duration in secs (float)
        self.__duration = self.__animator.getTimeManipulatedDur()

        self.__startAnimate()

    def setpaused(self, paused, timestamp):
        Channel.ChannelAsync.setpaused(self, paused, timestamp)
        self.__pauseAnimate(paused)

    def playstop(self, curtime):
        if debug: print 'playstop'
        self.__stopAnimate()
        Channel.ChannelAsync.playstop(self, curtime)

    def stopplay(self, node, curtime):
        if debug: print 'stopplay'
        if node.GetType() == 'anchor':
            self.stop_anchor(node, curtime)
            return
        self.__stopAnimate()
        self.__removeAnimate()
        Channel.ChannelAsync.stopplay(self, node, curtime)

    #
    # Animation engine
    #

    def __initEngine(self, node):
        self.__animator = None
        self.__effAnimator = None

        self.__fiber_id = None
        self.__playdone = 0
        self.__targetChannel = None
        self.__lastvalue = None
        self.__start = None
        self._pausedt = 0

        if not hasattr(self._player,'_animateContext'):
            self._player._animateContext = Animators.AnimateContext(self._player)
        ctx = self._player._animateContext

        parser = Animators.AnimateElementParser(node, ctx, self._playcontext)
        self.__animator = parser.getAnimator()
        if self.__animator:
            # find and apply parent speed
            speed = node.GetParent().GetRawAttrDefProduct('speed', 1.0)
            self.__animator._setSpeed(speed)
            # get the effective animator of the attribute
            self.__effAnimator = ctx.getEffectiveAnimator(
                    parser.getTargetNode(),
                    parser.getGrinsAttrName(),
                    parser.getDOMValue())

    def __ready(self):
        return  self.__animator!=None and self.__effAnimator!=None

    def __getTargetChannel(self):
        if self.__targetChannel:
            return self.__targetChannel
        targnode = self.__effAnimator.getTargetNode()
        if targnode is None:
            return None
        if targnode.getClassName() in ('Region', 'Viewport'):
            regionName = targnode.GetUID()
            self.__targetChannel = self._player.getchannelbyname(regionName)
        else:
            if targnode.GetType() == 'anchor': # area
                parentnode = targnode.GetParent()
                self.__targetChannel = self._player.getRenderer(parentnode)
            else:
                self.__targetChannel = self._player.getRenderer(targnode)
        return self.__targetChannel

    def __startAnimate(self):
        self.__start = self.__animating.get_start_time()
        if self.__start is None:
            print 'Warning: None start_time for node',self.__animating
            self.__start = 0

        self.__effAnimator.onAnimateBegin(self.__getTargetChannel(), self.__animator)

        # take into account accumulation effect
        for i in range(self.__curloop):
            self.__animator.setToEnd()

        self.__animate()
        self.__register_for_timeslices()

    def __stopAnimate(self):
        if self.__animating:
            self.__unregister_for_timeslices()
            val = self.__animator.setToEnd()
            if self.__effAnimator:
                if self.__lastvalue != val:
                    self.__effAnimator.update(self.__getTargetChannel())
                    self.__lastvalue = val
            self.__animating = None

    def __removeAnimate(self):
        if self.__effAnimator:
            if debug: print 'removeAnimate'
            update = not self.__animator.isAccumulating()
            if self.__animator.isAccumulating() and self.__moreloops: update = 0
            else: update = 1
            self.__effAnimator.onAnimateEnd(self.__getTargetChannel(), self.__animator, update=update)
            self.__effAnimator = None

    def __pauseAnimate(self, paused):
        if self.__animating:
            if paused:
                self.__unregister_for_timeslices()
            else:
                self.__register_for_timeslices()

    def __animate(self):
        try:
            dt = self._scheduler.timefunc() - self.__start
        except TypeError, arg:
            print arg
            self.playdone(0, 0)
            return
        if self.__duration>0:
            dt = dt - self.__duration * int(float(dt) / self.__duration)
        val = self.__animator.getValue(dt)
        if self.__effAnimator:
            # update always for now
            # for discrete animations the window does not exist at startup
            if 1: # or self.__lastvalue != val:
                self.__effAnimator.update(self.__getTargetChannel())
                self.__lastvalue = val

    def __onAnimateDur(self):
        if not self.__animating:
            return
        # set to the end for the benefit of freeze and repeat
        val = self.__animator.setToEnd()
        if self.__effAnimator:
            if self.__lastvalue != val:
                self.__effAnimator.update(self.__getTargetChannel())
                self.__lastvalue = val
        self.playdone(0, self.__start+self.__duration)

    def __onIdle(self):
        if not USE_IDLE_PROC:
            self.__fiber_id = None
        if self.__animating:
            t_sec=self._scheduler.timefunc() - self.__start
            # end-point exclusive model
            if self.__duration>0 and t_sec>=self.__duration:
                self.__unregister_for_timeslices()
                self.__onAnimateDur()
            else:
                self.__animate()
                if not USE_IDLE_PROC:
                    self.__register_for_timeslices()
            windowinterface.sleep(0)

    def __register_for_timeslices(self):
        if self.__fiber_id is None:
            if USE_IDLE_PROC:
                self.__fiber_id = windowinterface.setidleproc(self.__onIdle)
            else:
                self.__fiber_id = windowinterface.settimer(0.05, (self.__onIdle,()))

    def __unregister_for_timeslices(self):
        if self.__fiber_id is not None:
            if USE_IDLE_PROC:
                windowinterface.cancelidleproc(self.__fiber_id)
            else:
                windowinterface.canceltimer(self.__fiber_id)
            self.__fiber_id = None
