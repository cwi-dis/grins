"""SMIL2 Timing Engine"""

# Author: Kleanthis Kleanthous.

version = '0.2'

# Based on:
# Synchronized Multimedia Integration Language (SMIL 2.0) Specification
# W3C Working Draft 01 March 2001

# This module assumes:
# 1. A separate DOM model for an XML language (SMIL, SVG, XHTML, MATHML, etc)
# 2. Imported SMIL elements or XML elements integrating time for this XML language should
#               inherit from TimeElement
#               implement the 'playable DOM interface'
#               implement the 'simple xml get protocol'

import time
import math

debug = 0

## #################
# dur arithmetic rules

# a time value can be 'unspecified', 'unresolved', 'indefinite', 'definite'

# time constants
unspecified = None
unresolved = 'unresolved'
indefinite = 'indefinite'
mediadur = 'media'

infinity = 'infinity'
minusinfinity = '-infinity'
epsilon = 0.0001 # smaller than time resolution of interest

def isdefinite(v):
    return v is not unresolved and v is not indefinite

def isunresolved(v):
    return v == unresolved

def isindefinite(v):
    return v == indefinite

def timemul(v1, v2):
    assert v1 is not None and v2 is not None, 'unspecified values'
    if v1 is unresolved or v2 is unresolved:
        return unresolved
    elif v1==0 or v2==0:
        return 0
    elif v1 is indefinite or v2 is indefinite:
        return indefinite
    else:
        return v1*v2

def timediv(v, a):
    assert v is not None, 'unspecified value'
    if v is unresolved:
        return unresolved
    elif v is indefinite:
        return indefinite
    else:
        return v/a

def timeadd(v1, v2):
    assert v1 is not None and v2 is not None, 'unspecified values'
    if v1 is unresolved or v2 is unresolved:
        return unresolved
    elif v1 is indefinite or v2 is indefinite:
        return indefinite
    else:
        return v1 + v2

def timesub(v1, v2):
    assert v1 is not None and v2 is not None, 'unspecified values'
    if v1 is unresolved or v2 is unresolved:
        return unresolved
    elif v1 is indefinite or v2 is indefinite:
        return indefinite
    else:
        return v1 - v2

def timemin(v1, v2):
    assert v1 is not None and v2 is not None, 'unspecified values'
    if v1 == 0 or v2 == 0:
        return 0
    elif v1 is indefinite and v2>0:
        return v2
    elif v2 is indefinite and v1>0:
        return v1
    elif v1 is unresolved and v2>0:
        return v2
    elif v2 is unresolved and v1>0:
        return v1
    elif v1 is unresolved and v2 is indefinite:
        return indefinite
    elif v2 is unresolved and v1 is indefinite:
        return indefinite
    return min(v1, v2)

def timemax(v1, v2):
    assert v1 is not None and v2 is not None, 'unspecified values'
    if v1 is minusinfinity:
        return v2
    elif v2 is minusinfinity:
        return v1
    if isdefinite(v1) and isdefinite(v2):
        return max(v1, v2)
    elif (isdefinite(v1) and v2 is indefinite) or (isdefinite(v1) and v1 is indefinite):
        return indefinite
    elif v1 is unresolved or v2 is unresolved:
        return unresolved

def timeLT(v1, v2):
    assert v1 is not None and v2 is not None, 'unspecified values'
    if v1 is minusinfinity and v2 is not minusinfinity:
        return 1
    elif v1 is minusinfinity or v2 is minusinfinity:
        return 0
    elif v1 is indefinite and v2 is indefinite:
        return 0
    elif isdefinite(v1) and v2 is indefinite:
        return 1
    elif isdefinite(v2) and v1 is indefinite:
        return 0
    elif v1 is unresolved or v2 is unresolved:
        return 0
    return v1<v2

def timeLE(v1, v2):
    assert v1 is not None and v2 is not None, 'unspecified values'
    if v1 is minusinfinity and v2 is not minusinfinity:
        return 1
    elif v1 is minusinfinity or v2 is minusinfinity:
        return 0
    elif v1 is indefinite and v2 is indefinite:
        return 0
    elif isdefinite(v1) and v2 is indefinite:
        return 1
    elif isdefinite(v2) and v1 is indefinite:
        return 0
    elif v1 is unresolved or v2 is unresolved:
        return 0
    return v1 <= v2

def timeGT(v1, v2):
    return not timeLE(v1, v2)

def timeGE(v1, v2):
    return not timeLT(v1, v2)

def timeEQ(v1, v2):
    return v1 == v2

## #################
# simple local time state keeper

class Timer:
    def __init__(self):
        self._ticking = 0
        self._localTime = 0.0
        self._lastTime = None

    def resetTimer(self):
        self._ticking = 0
        self._localTime = 0.0
        self._lastTime = None

    def isTicking(self):
        return self._ticking

    def startTimer(self, t=None):
        if t is not None:
            self.setTime(t)
        if not self._ticking:
            self._lastTime = time.time()
            self._ticking = 1

    def stopTimer(self, t=None):
        if self._ticking:
            self._updateTime()
            self._ticking = 0
        if t is not None:
            self._localTime = t

    def setTime(self, t):
        self._localTime = float(t)
        if self._ticking:
            self._lastTime = time.time()

    def incTime(self, dt):
        self._localTime = self._localTime + float(dt)
        if self._ticking:
            self._lastTime = time.time()

    def getTime(self):
        if self._ticking:
            self._updateTime()
            return self._localTime
        else:
            return self._localTime

    def _updateTime(self):
        self._localTime = self._localTime + time.time() - self._lastTime
        self._lastTime = time.time()


## #################
# simple delta timer queue for scheduling work

class DeltaQueue:
    def __init__(self, timefunct):
        self._queue = []
        self._indqueue = []
        self._timefunct = timefunct
        self._lasttime = timefunct()

    def schedule(self, when, what):
        self.cancel(what)
        tnow = self._timefunct()
        if self._queue:
            t, obj = self._queue[0]
            t = t - (tnow - self._lasttime)
            self._queue[0] = t, obj
        self._lasttime = tnow

        if not isdefinite(when):
            self._indqueue.append((indefinite, what))
            return

        t = 0.0
        for i in range(len(self._queue)):
            time0, dummy = self._queue[i]
            if t + time0 > when:
                self._queue[i] = time0 - when + t, dummy
                self._queue.insert(i, (when - t, what))
                return
            t = t + time0
        self._queue.append((when - t, what))

    def getExecList(self):
        tnow = self._timefunct()
        delta = tnow - self._lasttime
        self._lasttime = tnow
        el = []
        while self._queue:
            et, obj = self._queue[0]
            t = et - delta
            if t <= 0.0:
                del self._queue[0]
                el.append(obj)
                delta = delta - et
            else:
                self._queue[0] = t, obj
                break
        return el

    def isEmpty(self):
        return len(self._queue)==0 and len(self._indqueue)==0

    def clear(self):
        self._queue = []
        self._indqueue = []

    def getDelay(self):
        if self._queue:
            return self._queue[0][0]
        elif self._indqueue:
            return indefinite
        return None

    def cancel(self, what):
        for i in range(len(self._queue)):
            t, obj = self._queue[i]
            if obj == what:
                del self._queue[i]
                if i < len(self._queue):
                    tt, obj = self._queue[i]
                    self._queue[i] = tt + t, obj
                return
        for i in range(len(self._indqueue)):
            t, obj = self._indqueue[i]
            if obj == what:
                del self._indqueue[i]
                return

    def update(self, what, when):
        self.cancel(what)
        self.schedule(self, when, what)

## #################
# Mixin for the DOM model of the XML language (SMIL, SVG, XHTML, MATHML, etc)

class TimeNode:
    def __init__(self, ttype, timeroot):
        self.ttype = ttype # tag for elements and meta-tag for the rest
        self.timeroot = timeroot or self
        self.tparent = None
        self.tfirstchild = None
        self.tnextsibling = None
        self.tindex = 0

    def getTimeType(self):
        return self.ttype

    def getTimeRoot(self):
        return self.timeroot

    def getTimeParent(self):
        return self.tparent

    def getTimeParentOrRoot(self):
        if self.tparent is not None:
            return self.tparent
        return self.timeroot

    def getFirstTimeChild(self):
        return self.tfirstchild

    def getNextTimeSibling(self):
        return self.tnextsibling

    def getTimeIndex(self):
        return self.tindex

    # debug UID
    def getTimeUID(self):
        uid = '%d' % (self.tindex + 1)
        tparent = self.tparent
        while tparent is not None and tparent != self.timeroot:
            uid = '%d.%s' % (tparent.tindex+1, uid)
            tparent = tparent.tparent
        return '%s %s' % (self.getTimeType(), uid)

    def getPrevTimeSibling(self):
        if self.tparent is None:
            return None
        prev = None
        next = self.tparent.tfirstchild
        while next:
            if next == self:
                return prev
            prev = next
            next = next.tnextsibling
        assert 0, 'logic error in TimeNode.getPrevTimeSibling'

    def getTimeChildren(self):
        L = []
        node = self.tfirstchild
        while node:
            L.append(node)
            node = node.tnextsibling
        return L

    def getLastTimeChild(self):
        last = None
        node = self.tfirstchild
        while node:
            last = node
            node = node.tnextsibling
        return last

    def getFirstTimeChildByType(self, ttype):
        node = self.tfirstchild
        while node:
            if node.ttype == ttype:
                return node
            node = node.tnextsibling
        return None

    def getLastTimeChild(self):
        tlastchild = None
        tchild = self.tfirstchild
        while tchild is not None:
            tlastchild = tchild
            tchild = tchild.tnextsibling
        return tlastchild

    def appendTimeChild(self, node):
        tlastchild = None
        index = 0
        tchild = self.tfirstchild
        while tchild is not None:
            tlastchild = tchild
            tchild = tchild.tnextsibling
            index = index + 1
        if tlastchild is None:
            self.tfirstchild = node
        else:
            tlastchild.tnextsibling = node
        node.tparent = self
        node.tindex = index

    def getTimePath(self):
        tpath = [self,]
        tparent = self.tparent
        while tparent is not None:
            tpath.insert(0, tparent)
            tparent = tparent.tparent
        return tpath

    def getCommonAncestor(self, n1, n2):
        p1 = n1.getTimePath()
        p2 = n2.getTimePath()
        n = min(len(p1), len(p2))
        prev = p1[0]
        for i in range(1,n):
            if p1[i]!=p2[i]:
                return prev
            prev = p1[i]

    def hasTimeAncestor(self, node):
        tparent = self.tparent
        while tparent is not None:
            if tparent == node:
                return 1
            tparent = tparent.tparent
        return 0

## ###################
# SyncElement:
# Timegraph nodes are either a TimeElement or a SyncElement
# When a SyncElement receives a time change notification should
# 1. update its state
# 2. propagate change to dependants avoiding cycles (thats why we can put 1 before this)

class SyncElement:
    defaultunit = 's'
    def __init__(self, dstnode, dstattr):
        # the time element this sync will affect
        self._dstnode = dstnode

        # the attribute of the time element this sync will affect (incl. internal 'activeEnd')
        assert dstattr in ('begin', 'end', 'activeEnd'), 'syntax error'
        self._dstattr = dstattr

        # indirect specs for the source time element of this sync
        self._syncbase = None # 'id', 'prev', 'parent', 'self'
        self._baseparams = None # id when syncbase == 'id' otherwise ignore

        # the specifiers of the event that trigger this sync
        self._baseevent = None # 'begin', 'end', 'repeat', 'event'

        # when baseevent=='repeat' beaseeventparams is the repeat index
        # when baseevent=='event' baseeventparams is the dom2event name
        self._baseeventparams = None

        # event offset specifiers
        self._offset = None # (+|-)? clock-value | implicit-0 | indefinite
        self._units = None

        # event instances
        self._insttimes = []

        # prevent cycles flag
        self._visited = 0

        # offset-value or wallclock
        self._readonly = 0

    def clone(self):
        v = SyncElement(self._dstnode, self._dstattr)
        v._syncbase = self._syncbase
        v._baseparams = self._baseparams
        v._baseevent = self._baseevent
        v._baseeventparams = self._baseeventparams
        v._offset = self._offset
        v._units = self._units
        v._insttimes = self._insttimes.copy()
        v._readonly = self._readonly
        return v

    def __repr__(self):
        if self._baseparams is None:
            base = self._syncbase
        else:
            base = '%s(%s)' % (self._syncbase, `self._baseparams`)
        if self._baseeventparams is None:
            event = self._baseevent
        else:
            base = '%s(%s)' % (self._baseevent, `self._baseeventparams`)
        return '%s.%s + %s' % (base, event, `self._offset`)

    def reinterpret(self):
        # offset and units
        if self._offset is None:
            self._offset = 0.0
            parent = self._dstnode.getTimeParent()
            if parent:
                if parent.getTimeType() == 'excl':
                    self._offset = 'indefinite'
        if self._units is None:
            self._units = self.defaultunit

        # interpret syncbase: 'id', 'prev', 'implicit'
        if self._syncbase is None:
            self._syncbase = 'implicit'
        elif self._syncbase != 'prev': # its an id
            self._baseparams = self._syncbase
            self._syncbase = 'id'

        # interpret baseevent: 'begin', 'end', 'repeat', 'event', 'implicit'
        if self._baseevent is None:
            self._baseevent = 'implicit'
        elif self._baseevent not in ('begin', 'end', 'repeat'): # its an event
            self._baseparams = self._baseevent
            self._baseevent = 'event'
        # else nothing to do. (self._baseeventparams for repeat is the index if given)

        if self._syncbase == 'implicit':
            self.qualifyImplicitSyncBase()

    def qualifyImplicitSyncBase(self):
        if self._syncbase != 'implicit': return
        if self._baseevent == 'event':
            self._syncbase = 'self'
        elif self._baseevent == 'implicit': # only offset
            parent = self._dstnode.getTimeParent()
            if parent:
                ptype = parent.getTimeType()
                self._readonly = 1
                if ptype == 'par':
                    self._syncbase = 'parent'
                    self._baseevent = 'begin'
                elif ptype == 'seq':
                    if self._dstnode.getPrevTimeSibling() is None:
                        self._syncbase = 'parent'
                        self._baseevent = 'begin'
                    else:
                        self._syncbase = 'prev'
                        self._baseevent = 'end'
                elif ptype == 'excl':
                    self._syncbase = 'parent'
                    self._baseevent = 'begin'
                else:
                    assert 0, 'unknown container'
            else:
                # exception
                self._syncbase = 'dom'
                self._baseevent = 'beginElement'
        elif self._baseevent != self._dstattr: # 'begin', 'end', 'repeat'
            self._syncbase = 'self'
        else:
            assert 0, 'syntax error'

    # time change notification
    def addInstanceTime(self, t, params=None):
        if self._visited: return
        self._visited = 1
        valid = 0
        if self._baseevent == 'repeat':
            if self._baseeventparams is None: # repeat
                valid = 1
            elif self._baseeventparams == params: # repeat(index)
                valid = 1
        elif self._baseevent == 'event':
            event, evparams = params
            assert self._baseevent == 'event', 'logic error'
            valid = (self._baseeventparams == event)
        else:
            valid = 1
        if valid:
            # 1. update our state
            self._insttimes.append(t)
            # 2. propagate change to dependants
            if self._dstnode.isSyncSensitive(self._dstattr):
                self._dstnode.syncUpdate(self._dstattr)
        self._visited = 0

    def removeInstanceTime(self, t):
        assert len(self._insttimes) == 1 and t in self._insttimes, 'logic error'
        if self._visited: return
        self._visited = 1
        # 1. update our state
        self._insttimes = []
        # 2. propagate change to dependants
        if self._dstnode.isSyncSensitive(self._dstattr):
            self._dstnode.syncUpdate(self._dstattr)
        self._visited = 0

    def updateInstanceTime(self, t1, t2):
        assert len(self._insttimes) == 1 and self._insttimes[0]==t1, 'logic error'
        if self._visited: return
        self._visited = 1
        # 1. update our state
        self._insttimes[0] = t2
        # 2. propagate change to dependants
        if self._dstnode.isSyncSensitive(self._dstattr):
            self._dstnode.syncUpdate(self._dstattr)
        self._visited = 0

    def syncInstanceTimes(self):
        # we do it at real time
        return

    def convertTime(self, t):
        if self._syncbase == 'parent' or self._syncbase == 'self':
            return t
        srcnode = self.getSyncBase()
        if not srcnode: return t
        p1 = srcnode.getTimeParent()
        if p1 is None: p1 = srcnode
        p2 = self._dstnode.getTimeParent()
        if p2 is None: p2 = self._dstnode
        if p1 != p2:
            t = p2.document2simple(p1.simple2document(t))
        return t

    def isEventBased(self):
        return self._baseevent == 'event'

    def hasPendingEvents(self):
        return self._baseevent == 'event' and len(self._insttimes)==0

    def reset(self):
        if self._readonly: return
        if self._syncbase != 'parent' or self._baseevent != 'begin':
            self._insttimes = []

    def resetEvents(self, exclbegin=None):
        if self._readonly: return
        if self._baseevent in ('event', 'repeat'):
            if exclbegin is not None:
                insttimes = self._insttimes[:]
                self._insttimes = []
                for t in insttimes.items():
                    if t == exclbegin:
                        self._insttimes.append(t)
            else:
                self._insttimes = []

    def resetSyncBaseTimes(self, root):
        if self._readonly: return
        if self._syncbase == 'parent' and self._baseevent == 'begin':
            return
        if self._baseevent in ('begin', 'end'):
            src = self.getSyncBase()
            dst = self._dstnode
            if src and src.hasTimeAncestor(root) and dst.hasTimeAncestor(root):
                self._insttimes = []

    def getOffset(self, units='s'):
        if callable(self._offset):
            offset = self._offset()
        else:
            offset = self._offset
        if offset is not None:
            if offset == 'indefinite':
                return 'indefinite'
            if self._units == 'ms':
                val = 0.001*offset
            else:
                val = offset
            if units == 's':
                return val
            return 1000.0*val
        return self._default

    def getInstanceTimes(self):
        if self._syncbase == 'self' and self._baseevent == 'begin':
            return self._dstnode.getXMLAttr('begin').evaluate()
        else:
            return self._insttimes

    def getSyncBase(self):
        src = None
        if self._syncbase == 'id':
            src = self._dstnode.getDocument().getElementWithId(self._baseparams)
        elif self._syncbase == 'prev':
            src = self._dstnode.getPrevTimeSibling()
            if not src: src = self._dstnode.getTimeParent()
        elif self._syncbase == 'parent':
            src = self._dstnode.getTimeParent()
        elif self._syncbase == 'self':
            src = self._dstnode
        return src

    def createSyncArc(self):
        if self._syncbase == 'parent' and self._baseevent == 'begin':
            # implicit
            tparent = self._dstnode.getTimeParent()
            if tparent:
                ttype = tparent.getTimeType()
                if ttype == 'par':
                    self._insttimes.append(0.0)
                elif ttype == 'excl':
                    self._insttimes.append(0.0)
                elif ttype == 'seq': # first child only
                    self._insttimes.append(0.0)
        elif self._syncbase == 'self' and self._baseevent == 'begin':
            # implicit
            pass
        else:
            base = self.getSyncBase()
            if base: base.addSyncArc(self)

    def evaluate(self):
        L = []
        offset = self.getOffset()
        insttimes = self.getInstanceTimes()
        for t in insttimes:
            tc = self.convertTime(t)
            L.append(timeadd(tc,offset))
        return L

    #
    # interface of  sync arc
    #
    def arcrepr(self):
        return '%s.%s -> %s.%s' % (self.getSrcTimeElement().getTimeType(), self.getSrcEvent(),\
                self.getDstTimeElement().getTimeType(), self.getDstAttr())

    def getSrcTimeElement(self):
        return self._syncbase

    def getDstTimeElement(self):
        return self._dstnode

    def getSrcEvent(self):
        return self._baseevent

    def getDstAttr(self):
        return self._dstattr


## ###################
# TimeInterval: an element lifetime is a set of time intervals

class TimeInterval:
    def __init__(self, begin, aend):
        self.begin = begin
        self.aend = aend
        self.beginArcs = None
        self.endArcs = None
        self.readonly = 0

    def __repr__(self):
        if type(self.aend) == type(''):
            return '%s (%f, %s)' % (self.__class__.__name__, self.begin, self.aend)
        else:
            return '%s (%f, %f)' % (self.__class__.__name__, self.begin, self.aend)

    def getBegin(self): return self.begin
    def getActiveEnd(self): return self.aend
    def getActiveDur(self): return timesub(self.aend, self.begin)
    def getValues(self): return self.begin, self.aend

    def setAsCurrent(self, node):
        if self.readonly: return
        node._interval = self
        self.beginArcs = node.beginArcs
        self.endArcs = node.endArcs
        for arc in self.beginArcs:
            arc.addInstanceTime(self.begin)
        for arc in self.endArcs:
            arc.addInstanceTime(self.aend)

    def cancel(self):
        for arc in self.beginArcs:
            arc.removeInstanceTime(self.begin)
        for arc in self.endArcs:
            arc.removeInstanceTime(self.aend)

    def setReadOnly(self, f):
        self.readonly = f

    def updateValues(self, begin, aend):
        if not self.readonly:
            self.updateBegin(begin)
            self.updateActiveEnd(aend)

    def updateBegin(self, begin):
        if begin != self.begin and not self.readonly:
            oldval = self.begin
            self.begin = begin
            if self.beginArcs:
                for arc in self.beginArcs:
                    arc.updateInstanceTime(oldval, begin)

    def updateActiveEnd(self, aend):
        if self.aend != aend and not self.readonly:
            oldval = self.aend
            self.aend = aend
            if self.endArcs:
                for arc in self.endArcs:
                    arc.updateInstanceTime(oldval, aend)


## ###################
# Excl element queue

def priorityLT(n1, n2):
    return n1.getExclChildPriority() > n2.getExclChildPriority()

def priorityLE(n1, n2):
    return n1.getExclChildPriority() >= n2.getExclChildPriority()

def priorityGT(n1, n2):
    return n1.getExclChildPriority() < n2.getExclChildPriority()

def priorityGE(n1, n2):
    return n1.getExclChildPriority() <= n2.getExclChildPriority()

def priorityEQ(n1, n2):
    return n1.getExclChildPriority() == n2.getExclChildPriority()

# attached to excl elements

class ExclPauseQueue:
    def __init__(self):
        self.elements = []

    def clear(self):
        del self.elements
        self.elements = []

    def insertPaused(self, e):
        assert e.isActive() and not e.isTicking(), 'excl queue invariant violation'
        if not self.elements:
            self.elements.append(e)
            return
        if e in self.elements:
            self.elements.remove(e)
        n = len(self.elements)
        for i in range(n):
            if priorityLE(self.elements[i], e):
                self.elements.insert(i, e)
                break
        else:
            self.elements.append(e)

    def insertDeferred(self, e):
        assert not e.isActive(), 'excl queue invariant violation'
        if not self.elements:
            self.elements.append(e)
            return
        if e in self.elements:
            self.elements.remove(e)
        n = len(self.elements)
        for i in range(n):
            if priorityLT(self.elements[i], e):
                self.elements.insert(i, e)
                break
        else:
            self.elements.append(e)

    def getNext(self):
        if not self.elements:
            return None
        e = self.elements[0]
        self.elements = self.elements[1:]
        return e


## ###################
# SMIL2 Timing FSM

# Time element states
# main states: 'idle', 'active'
# 'idle' substates: 'waitinterval', 'waitbegin'
# 'active' substates: 'playing', 'paused'

# All states: 'idle.waitinterval', 'idle.waitbegin', 'ative.playing', 'active.paused'
# 'idle' can be further qualified as:
#       'reset' or 'aged', 'frozen' or 'removed', 'notplayed' or 'played', 'sensitive' or 'insensitive'
#  but since they are not othogonal and for simplicity we don't define other substates but state variables
#  'reset' is a well known substate of idle entered after a 'reset' operation

# state transition external events:
# DOMEvent, DOMCall

# state transition time completion events:
# beginInterval, repeat, endInterval

# state transition sync update events
# syncUpdate, newInterval, updateInterval

# wake up events
# timerEvent, childBegin, childEnd

# state transition invariants
# * element's life-cycle is: waitinterval (waitbegin ((active waitinterval?) | waitinterval))*
# * any element state can be transit (zero dur)
# * when the engine is intialized all elements are in 'idle.waitinterval.reset' state
# * when an element its not 'active' its children are in 'idle.waitinterval'
# * when an element enters 'active' or 'repeats' its children start from an 'idle.waitinterval.reset' state

# state transition invariants consequences and elaboration
# *     an element entering 'active' (idle.waitbegin -> active)
#   does a 'resetDescendants'
#               applies 'reset' on its children
#               clears descendants sync base times
#               clears its pause queue when 'excl'
#   does a 'prepareBegin'
#               clears its event-values, repeat-values, accesskey-values, DOM calls 'excluding current begin'
#               'synchronize' its schedule
#               prepare element to play (what specific is needed)

# * an element on 'repeat' (active -> active)
#   does a 'resetDescendants'
#               applies 'reset' on its children
#               clears descendants sync base times
#               clears its pause queue when 'excl'

# *     an element exiting 'active' (active -> idle.waitinterval)
#   does a 'fillOnEnd'
#               brings its children to 'idle.waitinterval'
#               applies fill behavior

# * an element in 'idle.waitinterval' on a 'new valid interval' transitions to 'waitbegin'
# * an element in 'idle.waitbegin' on 'begin completion' transitions to 'active'
# * an element in 'active' on 'active end completion' transitions to 'idle.waitinterval'


# implementation reminders
# * take into account time sampling, sync behavior and tolerance


# TimeElement state variable
IDLE, ACTIVE = 0, 1

# substate when IDLE
WAITINTERVAL, WAITBEGIN = 0, 1

# substate when ACTIVE
PAUSED, PLAYING = 0, 1

class TimeElement(TimeNode, Timer):
    def __init__(self, ttype, timeroot):
        TimeNode.__init__(self, ttype, timeroot)
        Timer.__init__(self)

        # timegraph sync arcs beginning from this element
        # their ends are SyncElements attached to the begin
        # or end list of another TimeElement
        self.beginArcs = []
        self.endArcs = []
        self.repeatArcs = []
        self.eventArcs = []

        # state indicator
        self._state = IDLE
        self._substate = WAITINTERVAL

        # current interval
        self._interval = None
        self._calcdur = None

        # state memory: active qualifiers
        self._repeattime = 0
        self._repeatindex = 0

        # state memory: idle qualifiers
        self._begincount = 0
        self._isfilled = 0

        # state memory: excl pause/defer queue
        if ttype == 'excl': self._pausequeue = ExclPauseQueue()
        else: self._pausequeue = None

        # implementation volatile artifacts
        self._timerid = None
        self._queue = None

        # implementation static artifacts
        self._ostimer = None

        # simulate inheritance
        # add custom behaviors based on time type (par, seq, excl, ref)
        self.setTimeBehavior(ttype)

    def timerepr(self):
        return '%s      o--[%s]--o      %s' % (`self.getXMLAttr('begin')`,self.getTimeUID(), `self.getCalcAttr('activeEnd')`)

    def timeevrepr(self):
        return '%s      o--[%s]--o      %s' % (`self.getXMLAttr('begin').evaluate()`,self.getTimeUID(), `self.getCalcAttr('activeEnd').evaluate()`)

    def arcsrepr(self):
        nodename = self.getTimeUID()
        b = '[%s].begin -->     %s' % (nodename, `self.beginArcs`)
        e = '[%s].end -->       %s' % (nodename, `self.endArcs`)
        r = '[%s].repeat -->    %s' % (nodename, `self.repeatArcs`)
        v = '[%s].event -->     %s' % (nodename, `self.eventArcs`)
        return b + '\n' + e + '\n' + r + '\n' + v + '\n'

    def setOsTimer(self, ostimer):
        self._ostimer = ostimer

    def reset(self):
        for el in self.getTimeChildren():
            el.reset()

        # element reset

        # transition to idle, waitinterval
        if self._state == ACTIVE:
            self.exitActiveAndNotify(self.getParentTime())
        else: # IDLE
            if self._substate == WAITBEGIN:
                self.cancelInterval()
            elif self._state == WAITINTERVAL:
                if self._isfilled:
                    self.removeObject()
                    self._isfilled = 0
        # assert state
        assert self._state == IDLE and self._substate == WAITINTERVAL, 'logic error'

        # reset any current interval
        self._calcdur = None
        self._interval = None

        # clear memory and resetRestart
        self._begincount = 0
        self._repeattime = 0
        self._repeatindex = 0
        if self._pausequeue:
            self._pausequeue.clear()

        # reset event-values, repeat-values, accesskey-values, DOM calls
        self.getXMLAttr('begin').resetEvents()
        self.getXMLAttr('end').resetEvents()

        # syncInstanceTimes
        self.getXMLAttr('begin').syncInstanceTimes()
        self.getXMLAttr('end').syncInstanceTimes()

        # resetSyncBaseTimes done by caller

        # reset implementation artifacts
        self.resetTimer()
        self.resetSchedule()

        # reset element specific resources
        self.resetObject()

    def resetDescendants(self):
        for el in self.getTimeChildren():
            el.reset()
        self.resetSyncBaseTimes(self)
        if self._pausequeue:
            self._pausequeue.clear()

    def remove(self):
        for el in self.getTimeChildren():
            el.remove()
        if self._isfilled:
            self.removeObject()
            self._isfilled = 0

    # resetSyncBaseTimes of this branch
    def resetSyncBaseTimes(self, root):
        for el in self.getTimeChildren():
            el.resetSyncBaseTimes(root)
        self.getXMLAttr('begin').resetSyncBaseTimes(root)
        self.getXMLAttr('end').resetSyncBaseTimes(root)

    def checkTiming(self):
        if self.get('max') is not None and self.get('min') is not None:
            if self.get('max') < self.get('min'):
                self.removeAttr('max')
                self.removeAttr('min')

    #
    # element life function
    #

    # interval time change notification
    def syncUpdate(self, event=None):
        restart = self.get('restart')
        dur = self.calcDur()
        now = self.getParentTime()
        if self._state == IDLE:
            if self._begincount == 0:
                interval = self.calcInterval(minusinfinity)
            elif restart != 'never':
                interval = self.calcInterval(now)
            else:
                interval = None
            if self._substate == WAITINTERVAL:
                if interval is not None:
                    self.onNewInterval(dur, interval)
            elif self._substate == WAITBEGIN:
                # but now we do have a previous interval
                if interval is not None:
                    # update intervals
                    begin, aend = self._interval.getValues()
                    nbegin, naend =  interval.getValues()
                    if nbegin != begin or naend != aend:
                        self._interval.updateValues(nbegin, naend)
                        if nbegin != begin:
                            self.scheduleBegin(nbegin)
                else:
                    self.cancelInterval()
        elif self._state == ACTIVE:
            # recalculate
            begin, aend = self._interval.getValues()
            interval = self.calcInterval(begin)
            if interval:
                nbegin, naend = interval.getValues()
                if nbegin > begin and timeLT(nbegin, aend) and timeGE(nbegin, now) and restart == 'always':
                    # we can restart
                    self._interval.updateValues(nbegin, naend)
                    self.exitActiveAndNotify(now)
                    self.syncUpdate()
                elif timeLE(naend, now):
                    # we should end immediately
                    self.exitActiveAndFill()
                    self.syncUpdate()
                elif naend != aend:
                    # just update
                    self._interval.updateActiveEnd(naend)
                    self.scheduleActiveEnd(naend)
        else:
            assert 0, 'logic error'

    # DOM event is set for this element
    # propagate the fact to depentants
    def onEvent(self, event, params=None):
        for arc in self.eventArcs:
            arc.addInstanceTime(self.getParentTime(), (event, params))

    # a child become active
    def onChildBegin(self, node):
        self.syncUpdate()

    # force children to evaluate their interval
    def wakeupChildren(self):
        for el in self.getTimeChildren():
            el.syncUpdate()

    def addSyncArc(self, syncelement):
        event = syncelement.getSrcEvent()
        if event == 'begin':
            self.beginArcs.append(syncelement)
        elif event == 'end':
            self.endArcs.append(syncelement)
        elif event == 'repeat':
            self.repeatArcs.append(syncelement)
        elif event == 'event':
            self.eventArcs.append(syncelement)

    #
    # wait begin
    #
    # event 'newInterval' set
    def onNewInterval(self, dur, interval):
        assert self._state == IDLE and self._substate == WAITINTERVAL, 'invalid transition'
        assert interval is not None, 'invalid transition'
        self._substate = WAITBEGIN
        self._calcdur = dur
        interval.setAsCurrent(self)
        self.scheduleBegin(interval.getBegin())

    # undo onNewInterval
    def cancelInterval(self):
        assert self._state == IDLE and self._substate == WAITBEGIN, 'invalid transition'
        self.resetSchedule()
        self._calcdur = None
        self._interval.cancel()
        self._substate = WAITINTERVAL
        self._interval = None

    #
    # enter active
    #
    # event 'beginInterval' set
    def onBeginInterval(self):
        assert self._state == IDLE and self._substate == WAITBEGIN and self._interval is not None, 'invalid transition'
        tparent = self.getTimeParent()

        # when time parent is excl we have to check whether we can interrupt playing
        if tparent and tparent.getTimeType() == 'excl':
            if not tparent.interruptAndApplyExclPolicy(self):
                # we can not interrupt playing
                # we have been put possibly in the queue as deferred
                if debug: print self.getTimeUID(), 'can not interrupt playing'
                return

        self._state = ACTIVE
        self._begincount = self._begincount + 1
        self._isfilled = 1

        self.prepareBegin()
        self.resetDescendants()

        # wake up parent
        if tparent: tparent.onChildBegin(self)

        # are we transit?
        # before scheduling anything check for not zero ad
        if self._interval.getActiveDur() == 0:
            self.exitActiveAndNotify(self._interval.getActiveEnd())
            return

        # position repeatindex and repeattime based on bt
        # schedule a repeat check
        bt, et = self._interval.getValues()
        now = self.getParentTime()
        if isdefinite(self._calcdur):
            self._repeatindex = 0
            self._repeattime = 0.0
            t = bt + self._calcdur
            while t<now:
                t = t + self._calcdur
                self._repeatindex = self._repeatindex + 1
                self._repeattime = self._repeattime + self._calcdur
            if timeLE(t,et):
                self.schedule(t-now, self.checkRepeat)

        # schedule end of interval
        self.schedule(self._interval.getActiveDur(), self.onEndInterval)

        # start local timer
        self.startTimer()
        self._substate = PLAYING
        self.beginObject()

        # wake up children
        self.wakeupChildren()

    # called when an element starts its active life
    def prepareBegin(self):
        # reset event-values, repeat-values, accesskey-values, DOM calls
        # but do not clear event for current begin of the interval
        self.getXMLAttr('begin').resetEvents(self._interval.getBegin())
        self.getXMLAttr('end').resetEvents()

        # syncInstanceTimes
        self.getXMLAttr('begin').syncInstanceTimes()
        self.getXMLAttr('end').syncInstanceTimes()

    def interruptAndApplyExclPolicy(self, new):
        assert self.getTimeType() == 'excl', 'logic error'
        playing = self.getPlayingChild()
        if playing is None:
            return 1
        if priorityEQ(new, playing):
            return self.applyPolicy('peers', new, playing)
        elif priorityGT(new, playingNode):
            return self.applyPolicy('higher', new, playing)
        elif priorityLT(new, playingNode):
            return self.applyPolicy('lower', new, playing)

    def applyPolicy(self, relation, new, playing):
        assert self.getTimeType() == 'excl', 'logic error'
        assert relation in ('peers', 'higher', 'lower'), 'invalid relation %s' % `relation`

        priorityClass = self.getPriorityClassElementFor(playing)
        if priorityClass is None:
            policy = 'stop'
        else:
            policy = priorityClass.get(relation)
        assert policy in ('stop', 'pause', 'defer', 'never',), 'invalid policy'

        if policy == 'stop':
            if debug: print playing.getTimeUID(), 'interrupted by', new.getTimeUID()
            playing.exitActiveAndNotify(self.getSimpleTime())
            return 1
        elif policy == 'pause':
            if debug: print playing.getTimeUID(), 'paused in favor of', new.getTimeUID()
            playing.pauseElement()
            self._pausequeue.insertPaused(playing)
            return 1
        elif policy == 'defer':
            if debug: print new.getTimeUID(), 'deferred'
            self._pausequeue.insertDeferred(new)
            return 0
        elif policy == 'never':
            if debug: print 'ignoring begin of', new.getTimeUID()
            return 0

    def getExclChildPriority(self):
        parent = self.getParent()
        if parent and parent.getType() == 'priorityClass':
            return parent.getIndex()
        return 0

    def getPlayingChild(self):
        for el in self.getTimeChildren():
            if el.isActive() and el.isTicking():
                return el
        return None

    def getPriorityClassElementFor(self, node):
        parent = node.getParent()
        if parent and parent.getType() == 'priorityClass':
            return parent
        return None

    #
    #  exit active
    #

    # event 'endInterval' set
    # called only on normal AD completion
    def onEndInterval(self):
        self.exitActive()
        self.fillOnEnd()

        # wake up parent
        # parent should call syncUpdate against self for recovering next intervals
        parent = self.getTimeParent()
        if parent: parent.onChildEnd(self)

    # always called on active exit
    def exitActive(self):
        assert self._state == ACTIVE, 'invalid transition'
        self.stopTimer()
        self._substate = PAUSED
        self._state = IDLE
        self._substate = WAITINTERVAL
        self.resetSchedule()
        self.endObject()
        self._interval.setReadOnly(1)

    # forced EndInterval: notify, exit and fill (usually by parent end)
    def exitActiveAndFill(self):
        self._interval.updateActiveEnd(self.getParentTime())
        self.exitActive()
        fill = self.get('fill')
        if fill != 'freeze':
            self.remove()

    # forced EndInterval: notify and exit (usually by a reset)
    def exitActiveAndNotify(self, aend):
        self._interval.updateActiveEnd(aend)
        self.exitActive()

    # called on normal AD completion
    def fillOnEnd(self):
        for el in self.getTimeChildren():
            el.endDescendants()
        fill = self.get('fill')
        if fill != 'freeze':
            self.remove()

    # drive all descendants to waitinterval state
    # forcing and end of interval and applying any fill
    def endDescendants(self):
        for el in self.getTimeChildren():
            el.endDescendants()
        # endDescendants operation
        if self._state == ACTIVE:
            self.exitActiveAndFill()
        else:
            if self._substate == WAITBEGIN:
                self.cancelInterval()
        assert self._state == IDLE and self._substate == WAITINTERVAL, 'logic error'

    #
    #  repeat
    #
    def checkRepeat(self):
        if self._state != ACTIVE:
            return
        t = self.getTime()
        if timeGE(t, self._interval.getActiveDur()):
            return
        insttime = t -  self._repeattime
        if insttime >= self._calcdur:
            self.onRepeat()
            t = self._calcdur -(insttime - self._calcdur)
            self.schedule(t, self.checkRepeat)
        else:
            self.schedule(self._calcdur - insttime, self.checkRepeat)

    # event 'repeat' set
    def onRepeat(self):
        self._repeatindex = self._repeatindex + 1
        self._repeattime = self._repeattime + self._calcdur

        # notify our repeat listeners
        for arc in self.repeatArcs:
            arc.addInstanceTime(self.getParentTime(), self._repeatindex)

        # self-similar mechanism
        self.resetDescendants()
        self.wakeupChildren()

    #
    #  This element DOM interface implementation
    #
    def beginElement(self):
        self.getXMLAttr('begin').addInstanceTime(0.0)
        return 1

    def beginElementAt(self, t):
        self.getXMLAttr('begin').addInstanceTime(t)
        return 1

    def endElement(self):
        self.getXMLAttr('end').addInstanceTime(self.getSimpleTime())
        return 1

    def endElementAt(self, t):
        self.getXMLAttr('end').addInstanceTime(t)
        return 1

    def pauseElement(self):
        for el in self.getTimeChildren():
            el.pauseElement()
        if self._state == ACTIVE and self._substate == PLAYING:
            self._substate = PAUSED
            self.stopTimer()
            self.pauseSchedule()

    def resumeElement(self):
        if self._state == ACTIVE and self._substate == PAUSED:
            self._substate = PLAYING
            self.startTimer()
            self.resumeSchedule()
        for el in self.getTimeChildren():
            el.resumeElement()

    def seekElement(self, seekTo):
        self.pauseElement()
        self.setTime(seekTo)
        self.resumeElement()

    def removeElement(self):
        self.remove()

    # wait for dur completion efficiently
    # out of smil timing model operation
    def freezeElement(self):
        if self._state == ACTIVE and self._substate == PLAYING:
            self._substate = PAUSED
            self.stopTimer()
            self.pauseSchedule()
        # exception: dissable resume
        self._state, self._substate  = IDLE, WAITINTERVAL

    def resetElement(self):
        self.reset()
        self.resetSyncBaseTimes(self)

    #
    #  Foreign object DOM interface or 'playable DOM interface'
    #  The smil2 time engine adds timing caps to any foreign object
    #  The foreign object should expose the following interface
    #  This is provided here as an adaptor
    #
    def resetObject(self):
        pass

    def beginObject(self):
        return 1

    def beginObjectAt(self, t):
        return 1

    def endObject(self):
        pass

    def endObjectAt(self, t):
        pass

    def pauseObject(self):
        pass

    def resumeObject(self):
        pass

    def seekObject(self, seekTo):
        pass

    def removeObject(self):
        pass

    def getObjectImplicitDur(self):
        return 0

    #
    # basic queries
    # (many but want to allow natural law of evolution select the survivals)
    #
    def getState(self):
        return self._state

    def getSubState(self):
        return self._state

    def isActive(self):
        return self._state == ACTIVE

    def isIdle(self):
        return self._state == IDLE

    def isWaitingBegin(self):
        return self._state == IDLE and self._substate == WAITBEGIN

    def isWaitingInterval(self):
        return self._state == IDLE and self._substate == WAITINTERVAL

    def isPostActive(self):
        return self._begincount > 0 and self._state == IDLE

    def isFilled(self):
        return self._isfilled

    def isFrozen(self):
        return self._begincount > 0 and self._state == IDLE and self._isfilled

    def isPlaying(self):
        return self._state == ACTIVE and self._substate == PLAYING

    def isPaused(self):
        return self._state == ACTIVE and self._substate == PAUSED

    def getCalcDur(self):
        if self._calcdur is None:
            return self.calcDur()
        return self._calcdur

    def getCalcRepeatCountDur(self):
        if self._calcdur is None:
            self.calcDur()
        repeatCount = self.get('repeatCount')
        return timemul(repeatCount, self.getCalcDur())

    def getBeginCount(self):
        return self._begincount

    def getInterval(self):
        return self._interval

    def getSimpleTime(self):
        t = self.getTime()
        if self._calcdur is indefinite or self == self.getTimeRoot():
            return t
        ad = self._interval.getActiveDur()
        if timeLT(ad, t):
            if self._state == ACTIVE:
                self.onEndInterval()
            self.setTime(ad)
            return self.getSimpleTime()
        insttime = t - self._repeattime
        if insttime > self._calcdur:
            self.checkRepeat()
            return self.getSimpleTime()
        if self.isFrozen() and insttime == 0.0:
            return self._calcdur
        if insttime == self._calcdur:
            return self._calcdur - epsilon
        return insttime

    def getParentTime(self):
        parent = self.getTimeParent() or self.getTimeRoot()
        return parent.getSimpleTime()

    def getEndSyncRule(self):
        obj = self.getXMLAttr('endsync')
        if obj.isEnumarated():
            rule = obj.getValue()
            params = None
        else:
            rule = 'id'
            params = obj.getValue()
            if self.getDocument().getElementWithId(params) is None:
                rule = 'last'
            else:
                found = 0
                for c in self.getTimeChildren():
                    if id == c.get('id'):
                        found = 1
                        break
                if not found: rule = 'last'
        return rule, params

    # argument what is 'begin' or 'end'
    def isSyncSensitive(self, what):
        assert what in ('begin', 'end'), 'invalid argument'
        if self._state == IDLE:
            if self._begincount == 0 or self.get('restart') != 'never':
                return 1
        elif self._state == ACTIVE and what == 'end':
            return 1
        return 0

    # resolve a begin or end time on an element but not both
    def getEventSensitivity(self):
        if self._state == IDLE:
            if self._begincount == 0 or self.get('restart') != 'never':
                return 'begin', 'end'
        elif self._state == ACTIVE:
            return 'end'
        assert 0, 'logic error'

    #
    #  timing calculations
    #
    def calcDur(self):
        endList = self.getXMLAttr('end')
        dur = self.get('dur')
        repeatDur = self.get('repeatDur')
        repeatCount = self.get('repeatCount')
        if dur is None and repeatDur is None and repeatCount is None and endList.isExplicit():
            calcdur = indefinite
        elif dur is not None:
            if dur is not indefinite:
                calcdur = float(dur)
            else:
                calcdur = indefinite
        elif dur is None:
            calcdur = self.calcImplicitDur()
        elif dur is mediadur:
            calcdur = self.calcImplicitDur()
        self._calcdur = self.applyTimeManipulations(calcdur)
        return self._calcdur

    def calcActiveEndSyncList(self):
        repeatDur = self.get('repeatDur')
        repeatCount = self.get('repeatCount')
        endSyncList = self.getXMLAttr('end')
        if not endSyncList.isExplicit():
            return self.calcActiveEndOffsetList(repeatCount, repeatDur)
        else:
            if dur is indefinite and repeatDur is None and repeatCount is None:
                return [('synclist', endSyncList),]
            else:
                return  [('synclist', endSyncList),] + self.calcActiveEndOffsetList(repeatCount, repeatDur)
        assert 0, 'calcActiveEndSyncList logic error'

    def calcActiveEndOffsetList(self, repeatCount, repeatDur):
        if repeatCount is None and repeatDur is None:
            return [('self', self.getCalcDur),]
        elif repeatDur is not None and repeatCount is None:
            return [('self', repeatDur),]
        elif repeatCount is not None:
            if repeatCount is indefinite:
                ed = [('self', indefinite),]
            else:
                ed = [('self', self.getCalcRepeatCountDur),]
            if repeatDur is not None:
                return [('self', repeatDur),] + ed
            return ed
        assert 0, 'calcActiveEndOffsetList logic error'

    def calcInterval(self, beginAfter = minusinfinity):
        if debug:
            print self.timeevrepr()
        beginList = self.getXMLAttr('begin')
        aendList = self.getCalcAttr('activeEnd')
        beginInstList = beginList.evaluate()
        aendInstList = aendList.evaluate()
        if not beginInstList:
            return None
        for begin in beginInstList:
            if not isdefinite(begin):
                return None
            if timeGE(begin, beginAfter):
                for aend in aendInstList:
                    comp = timeGE
                    # check for any degeneracy and break it (i.e. avoid infinite loop of zero dur intervals)
                    if self._interval is not None and self._interval.getActiveDur() == 0.0:
                        comp = timeGT
                    # a valid interval should end after parent begin
                    if comp(aend, timemax(begin, 0)):
                        # bound to (min, max)
                        mintime = self.get('min')
                        maxtime = self.get('max')
                        ad = timesub(aend, begin)
                        if mintime is not None and mintime>0 and  timeLT(ad, mintime):
                            aend = timeadd(begin, mintime)
                        if maxtime is not None and maxtime>0 and timeGT(ad, maxtime):
                            aend = timeadd(begin, maxtime)

                        # apply time manipulation
                        speed = self.get('speed')
                        if speed:
                            aend = timeadd(begin, timediv(ad, speed))
                        if self.get('autoReverse'):
                            aend = timeadd(begin, timemul(ad, 2.0))

                        # thats it.
                        return TimeInterval(begin, aend)
        return None

    def applyTimeManipulations(self, ad):
        speed = self.get('speed')
        if speed:
            ad = timediv(ad, speed)
        if self.get('autoReverse'):
            ad = timemul(ad, 2.0)
        return ad

    def matchesEndSyncRule(self, rule, id=None):
        now = self.getTime()
        if rule == 'first': result = 0
        else: result = 1
        for c in self.getTimeChildren():
            if rule == 'first':
                if c.getBeginCount()>0 and not c.isActive():
                    return 1
            elif rule == 'id':
                if id == c.get('id'):
                    return c.isPostActive()
            elif rule == 'last':
                if c.isActive() or c.isWaitingBegin():
                    return 0
            elif rule == 'all':
                if c.getBeginCount()==0 or c.isActive():
                    return 0
        return result

    #
    #  delta schedule interface
    #
    def schedule(self, delay, cb):
        if self._queue is None:
            self._queue = DeltaQueue(self.getTimeParentOrRoot().getTime)
        self._queue.schedule(delay, cb)
        if self._timerid is None:
            self._execSchedule()

    def cancel(self, cb):
        self._queue.cancel(cb)

    def pauseSchedule(self):
        if self._timerid is not None:
            timer = self.timeroot._ostimer
            timer.canceltimer(self._timerid)
            self._timerid = None

    def resumeSchedule(self):
        self._execSchedule()

    def resetSchedule(self):
        self.pauseSchedule()
        if self._queue:
            self._queue.clear()

    def _sleep(self, delay):
        if delay is None:
            self._timerid = None
        elif delay == indefinite:
            self._timerid = None
        else:
            timer = self.timeroot._ostimer
            self._timerid = timer.settimer(delay, (self._execSchedule, ()))

    def _execSchedule(self):
        self._timerid = None
        execList = self._queue.getExecList()
        for cmd in execList:
            cmd()
        delay = self._queue.getDelay()
        self._sleep(delay)

    def scheduleBegin(self, begin):
        if begin <= 0:
            self.setTime(-begin)
            self.onBeginInterval()
        else:
            self.schedule(begin, self.onBeginInterval)

    def scheduleActiveEnd(self, aend):
        now = self.getParentTime()
        after = timesub(aend, now)
        if after <= 0:
            self.cancel(self.onEndInterval)
            self.onEndInterval()
        else:
            self.schedule(after, self.onEndInterval)

    #
    # time conversion
    #
    def simple2ancestor(self, t, ancestor):
        if not isdefinite(t) or ancestor == self:
            return t
        c = self
        cs = t
        while c.tparent and c != ancestor:
            if c._interval is None:
                return unresolved
            ca = cs + c._repeattime
            ps = ca + c._interval.getBegin()
            c = c.tparent
            cs = ps
        return cs

    def ancestor2simple(self, t, ancestor):
        if not isdefinite(t) or ancestor == self:
            return t
        path = self.getTimePath()
        i = 0
        for c in path:
            i = i + 1
            if c == ancestor:
                break
        ps = t
        for c in path[i:]:
            if c._interval is None:
                return unresolved
            ca = ps - c._interval.getBegin()
            cs = ca - c._repeattime
            ps = cs
        return ps

    def simple2document(self, t):
        return self.simple2ancestor(t, self.getTimeRoot())

    def document2simple(self, t):
        return self.ancestor2simple(t, self.getTimeRoot())

    def active2document(self, t):
        return self.simple2document(t - self._repeattime)

    def document2active(self, t):
        return self._repeattime + self.document2simple(t)

    def active2parent(self, t):
        if self._interval is None:
            return unresolved
        return timeadd(self._interval.getBegin(), t)

    #
    #       polymorphic time behaviors according to time type
    #   i.e. simulate inheritance without defining a new class
    #
    def setTimeBehavior(self, ttype):
        if ttype == 'par':
            self.calcImplicitDur = self.calcParImplicitDur
            self.onChildEnd = self.onParChildEnd
        elif ttype == 'seq':
            self.calcImplicitDur = self.calcSeqImplicitDur
            self.onChildEnd = self.onSeqChildEnd
        elif ttype == 'excl':
            self.calcImplicitDur = self.calcExclImplicitDur
            self.onChildEnd = self.onExclChildEnd
        else:
            self.calcImplicitDur = self.calcRefImplicitDur
            self.onChildEnd = self.onRefChildEnd

    def calcRefImplicitDur(self):
        return self.getObjectImplicitDur()

    def onRefChildEnd(self, node):
        self.syncUpdate()
        node.syncUpdate()

    def calcParImplicitDur(self):
        idur = minusinfinity
        for el in self.getTimeChildren():
            interval = el.getInterval()
            if interval is not None:
                idur = timemax(idur, interval.getActiveEnd())
            else:
                return unresolved
        if idur == minusinfinity:
            return unresolved
        return idur

    def onParChildEnd(self, node):
        if self.get('dur') is not None:
            # ignore endsync
            node.syncUpdate()
            return
        if self.getXMLAttr('end').isExplicit() and self.get('dur') is None\
                and self.get('repeatDur') is None and self.get('repeatCount') is None:
            # ignore endsync
            node.syncUpdate()
            return

        rule, params = self.getEndSyncRule()
        matches = self.matchesEndSyncRule(rule, params)

        if self.get('dur') is None and matches:
            self.onEndInterval()
        else:
            node.syncUpdate()

        # optimization (out of timing model)
        if self.getTimeRoot() == self and matches:
            self.freezeElement()
        else:
            node.syncUpdate()

    def calcSeqImplicitDur(self):
        dur = 0
        last = self.getLastTimeChild()
        interval = last.getInterval()
        if interval is not None:
            return interval.getActiveEnd()
        return 'unresolved'

    def onSeqChildEnd(self, node):
        if node == self.getLastTimeChild():
            self.syncUpdate()
        else:
            node.syncUpdate()

    def calcExclImplicitDur(self):
        idur = minusinfinity
        for el in self.getTimeChildren():
            interval = el.getInterval()
            if interval is not None:
                idur = timemax(idur, interval.getActiveEnd())
            else:
                return unresolved
        return idur

    def onExclChildEnd(self, node):
        # check paused/deferred queue
        queueElement = self._pausequeue.getNext()
        if queueElement:
            if debug: print 'queueElement', queueElement.getTimeUID()
            if queueElement.isActive() and not queueElement.isTicking():
                # paused
                queueElement.resumeElement()
                if debug: print 'resuming element', queueElement.getTimeUID()
            else:
                # deferred
                if debug: print 'syncUpdate for deferred element',  queueElement.getTimeUID()
            queueElement.syncUpdate()
            return

        if self.get('dur') is not None:
            # ignore endsync
            node.syncUpdate()
            return

        if self.getXMLAttr('end').isExplicit() and self.get('dur') is None\
                and self.get('repeatDur') is None and self.get('repeatCount') is None:
            # ignore endsync
            node.syncUpdate()
            return

        rule, params = self.getEndSyncRule()
        matches = self.matchesEndSyncRule(rule, params)

        if self.get('dur') is None and matches:
            self.onEndInterval()
        else:
            node.syncUpdate()

        # optimization (out of timing model)
        if self.getTimeRoot() == self and matches:
            self.freezeElement()
        else:
            node.syncUpdate()
