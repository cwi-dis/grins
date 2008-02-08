__version__ = "$Id$"

# Interface to calculate the timing of a (sub)tree

import time
import sched
import MMAttrdefs
from MMExc import *
from MMTypes import *
from HDTL import HD, TL

real_interiortypes = ('par', 'seq', 'switch', 'excl')

# Yuck, global variable.
timingtype = 'virtual'

# Calculate the nominal times for each node in the given subtree.
# When the function is done, each node has two instance variables
# 't0' and 't1' that give the begin and end time of the node.
# By definition, 't0' for the given root is zero; its 't1' value
# gives the total duration.
#
# This takes sync arcs within the subtree into account, but ignores
# sync arcs with one end outside the given subtree.
#
# Any circularities in the sync arcs are detected and "reported"
# as exceptions.

def computetimes(node, which):
    global timingtype
    timingtype = which
    node.t1 = 0
    del node.t1



    prepare(node)
    _do_times_work(node)
    if not hasattr(node, 't1'):
## XXXX The most common cause for this, nowadays, is an interior node
##      with indefinite duration, so we don't show the warning but set
##      a random time.
##         import windowinterface
##         windowinterface.showmessage('WARNING: circular timing dependencies.\n'+\
##               '(ignoring sync arcs and trying again)')
##         prep1(node)
##         _do_times_work(node)
        if __debug__:
            print 'No endtime for', node
        node.t1 = node.t0 + 10.0
    propdown(node, node, node.t1, node.t0)
    node.t2 = node.t1
    propdown2(node, node, node.t2, node.t0)

def _do_times_work(node):
    pt = pseudotime(0.0)
    q = sched.scheduler(pt.timefunc, pt.delayfunc)
    node.counter[HD] = 1
    decrement(q, 0, node, HD)
    q.run()

# Interface to the prep1() and prep2() functions; these are also used
# by the player (which uses a different version of decrement()).
# This adds instance variables 'counter' and 'deps' to each node,
# with meanings that can be deduced from the code below. :-) :-) :-)
#
def prepare(node):
    prep1(node)
    prep2(node, node)
    if node.counter[HD] <> 0:
        raise CheckError, 'head of node has dependencies!?!'


# Interface to clean up the mess left behind by prepare().
#
# Calling this can never really hurt,
# ***however***, if you repeatedly call changedtimes(),
# it is faster not to call cleanup() in between!
#
# It does *not* remove t0 and t1, by the way...
#
def cleanup(node):
    node.counter = node.deps = node.hasterm = None
    del node.counter
    del node.deps
    del node.hasterm
    for c in node.GetChildren():
        cleanup(c)


# Return a node's nominal duration, in seconds, as a floating point value.
# Should only be applied to leaf nodes.
#
is_warned = 0

def getduration(node):
    import Duration
    d = Duration.get(node)
    if d < 0:
        if __debug__:
            print 'Duration < 0 for', node
        return 0
    return d



## #########################################################
# The rest of the routines here are for internal use only #
## #########################################################


def prep1(node):
    node.counter = [0, 0]
    node.deps = [], []
    node.hasterm = 0
    type = node.GetType()
    dur = node.GetAttrDef('duration', None)
    if dur is None and not node.GetChildren():
        dur = node.GetAttrDef('empty_duration', None)
    if dur is not None and dur >= 0:
        adddep(node, HD, dur, node, TL, 'TERM')
    elif type in playabletypes:
        dur = getduration(node)
        if dur >= 0:
            adddep(node, HD, dur, node, TL, 'TERM')
    if type == 'seq': # XXX not right!
        xnode, xside = node, HD
        for c in node.GetSchedChildren(0):
            if not c.ShouldPlay():
                continue
            prep1(c)
            adddep(xnode, xside, 0, c, HD)
            xnode, xside = c, TL
        adddep(xnode, xside, 0, node, TL)
    elif type in ('par', 'switch', 'excl') or (type in playabletypes and node.GetSchedChildren(0)):
        term = node.GetTerminator()
        for c in node.GetSchedChildren(0):
            if not c.ShouldPlay():
                continue
            prep1(c)
            adddep(node, HD, 0, c, HD)
            if term == 'FIRST':
                adddep(c, TL, 0, node, TL, 'FIRST')
            elif term == MMAttrdefs.getattr(c, 'name'):
                node.hasterm = 1
                adddep(c, TL, 0, node, TL, 'TERM')
            else:
                adddep(c, TL, 0, node, TL)
    else:
        adddep(node, HD, None, node, TL)


def prep2(node, root):
    # XXX we only deal with a single syncarc; all others are ignored
    # If we're computing timing with download lags we should also get the
    # lag (which has been computed before we're called), otherwise the lag will be
    # zero.
    for arc in node.GetBeginList():
        if arc.srcnode == 'syncbase':
            parent = node.GetSchedParent(1)
            # in case the root of the tree we're interested in is a switch
            if parent is None or parent.IsAncestorOf(root):
                if root is node:
                    parent = None
                else:
                    parent = root
            if parent is None:
                # ignore syncarcs from outside our subtree
                continue
            if parent.GetType() == 'seq':
                xnode = parent
                xside = HD
                for n in parent.GetSchedChildren(0):
                    if n is node:
                        break
                    if not n.ShouldPlay():
                        continue
                    xnode = n
                    xside = TL
            else:
                xnode = parent
                xside = HD
            adddep(xnode, xside, arc.delay, node, HD)
            break
        if arc.srcnode is None or arc.srcnode == 'prev':
            # can't deal with this at the moment
            continue
        srcnode = arc.refnode()
        if srcnode is None:
            continue
        # srcnode is a MMNode instance
        if arc.event in ('begin','end'):
            if srcnode.CommonAncestor(root) is not root:
                # out of scope
                continue
            if arc.event == 'begin':
                xside = HD
            else:
                xside = TL
            adddep(srcnode, xside, arc.delay, node, HD)
            break
    for c in node.GetSchedChildren(0):
        if c.ShouldPlay():
            prep2(c, root)


# propdown - propagate timing down the tree again
def propdown(root, node, stoptime, dftstarttime=0):
    tp = node.GetType()
    # Assure we have a start time and stop time
    if not hasattr(node, 't0'):
        node.t0 = dftstarttime
    if not hasattr(node, 't1') or node.t1 > stoptime:
        node.t1 = stoptime

    dur = node.GetAttrDef('duration', None)
    if dur is None and not node.GetChildren():
        dur = node.GetAttrDef('empty_duration', None)
    if dur is not None and dur >= 0 and node.t0 + dur < stoptime:
        stoptime = node.t1 = node.t0 + dur

    children = node.GetSchedChildren(0)

    if tp in ('par', 'switch', 'excl', 'prio') or tp in playabletypes:
        term = node.GetTerminator()
        if term == 'LAST':
            stoptime = node.t0
        elif term == 'FIRST':
            stoptime = -1
        elif term == 'ALL':
            stoptime = node.t0
        for c in children:
            if not c.ShouldPlay():
                if term == 'ALL':
                    stoptime = -1
                continue
            if term in ('LAST', 'ALL'):
                if hasattr(c, 't1') and ((stoptime >= 0 and c.t1 > stoptime) or c.t1 < 0):
                    stoptime = c.t1
            elif term == 'FIRST':
                if hasattr(c, 't1') and stoptime >= 0 and c.t1 < stoptime:
                    stoptime = c.t1
            elif term == MMAttrdefs.getattr(c, 'name'):
                propdown(root, c, stoptime, node.t0)
                stoptime = c.t1
                children.remove(c) # propagated this one already
                break
        if dur is not None and dur >= 0 and node.t0 + dur < stoptime:
            stoptime = node.t0 + dur
        node.t1 = stoptime
        for c in children:
            if c.ShouldPlay():
                propdown(root, c, stoptime, node.t0)
    elif tp == 'seq': # XXX not right!
        if not children:
            return
        nextstart = node.t0
        for i in range(len(children)):
            c = children[i]
            if not c.ShouldPlay():
                continue
            if i == len(children)-1:
                endtime = node.t1
            elif hasattr(children[i+1], 't0'):
                endtime = children[i+1].t0
            else:
                endtime = node.t1
            if dur is not None and dur >= 0 and node.t0 + dur < endtime:
                endtime = node.t0 + dur
            propdown(root, c, endtime, nextstart)
            nextstart = c.t1

def propdown2(root, node, stoptime, dftstarttime=0):
    tp = node.GetType()
    if node.GetFill() == 'remove':
        stoptime = min(node.t1, stoptime)

    node.t2 = stoptime

    children = node.GetSchedChildren(0)
    if tp in ('par', 'switch', 'excl', 'prio') or tp in playabletypes:
        for c in children:
            if c.ShouldPlay():
                propdown2(root, c, stoptime, node.t0)
    elif tp == 'seq': # XXX not right!
        if not children:
            return
        nextstart = node.t0
        for i in range(len(children)):
            c = children[i]
            if not c.ShouldPlay():
                continue
            fill = c.GetFill()
            if fill in ('freeze', 'transition', 'hold'):
                # not correct for transition
                if i == len(children)-1:
                    endtime = node.t2
                elif hasattr(children[i+1], 't0'):
                    endtime = children[i+1].t0
                else:
                    endtime = node.t2
            elif fill == 'hold':
                endtime = node.t2
            else:           # fill == 'remove'
                endtime = c.t1
            propdown2(root, c, endtime, nextstart)
            nextstart = c.t1

def adddep(xnode, xside, delay, ynode, yside, terminating = None):
    ynode.counter[yside] = ynode.counter[yside] + 1
    if delay is not None and xside in (HD, TL):
        xnode.deps[xside].append((delay, ynode, yside, terminating))


def decrement(q, delay, node, side, term = None):
    if delay != 0:
        id = q.enter(delay, 0, decrement, (q, 0, node, side, term))
        return
    x = node.counter[side] - 1
    if x < 0:
        return
##         raise CheckError, 'counter below zero!?!?'
    if x == 0 and side == HD:
        node.t0 = q.timefunc()
    elif side == TL:
        if term == 'FIRST':
            t = q.timefunc()
            if not hasattr(node, 't1') or t < node.t1:
                node.t1 = t
                x = 0
            else:
                x = 1
        elif not node.hasterm or term == 'TERM':
            node.t1 = q.timefunc()
            if node.hasterm:
                x = 0
        elif node.hasterm:
            x = 1
    node.counter[side] = x
    if x > 0:
        return
    if node.GetType() not in interiortypes and side == HD and not node.GetSchedChildren(1):
        dt = getduration(node)
##         if dt == 0 and node.GetSchedParent().GetType() == 'seq':
##             dt = 5
        id = q.enter(dt, 0, decrement, (q, 0, node, TL))
    for d, n, s, t in node.deps[side]:
        decrement(q, d, n, s, t)


class pseudotime:
    def __init__(self, t):
        self.t = t
    def __repr__(self):
        return '<pseudotime instance, t=' + `self.t` + '>'
    def timefunc(self):
        return self.t
    def delayfunc(self, delay):
        self.t = self.t + delay
