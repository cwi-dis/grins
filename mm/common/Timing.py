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
##		import windowinterface
##		windowinterface.showmessage('WARNING: circular timing dependencies.\n'+\
##			  '(ignoring sync arcs and trying again)')
##		prep1(node)
##		_do_times_work(node)
		print 'No endtime for', node
		node.t1 = node.t0 + 10.0
	if node.t1 == node.t0:
		node.t1 = node.t0 + 10
	propdown(node, node.t1, node.t0)

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
	node.counter = node.deps = None
	del node.counter
	del node.deps
	for c in node.GetChildren():
		cleanup(c)


# Return a node's nominal duration, in seconds, as a floating point value.
# Should only be applied to leaf nodes.
#
is_warned = 0

def getduration(node):
	import Duration
	d = Duration.get(node)
	if d > 0:
		return d
	if d < 0:
		print 'Duration < 0 for', node
		return 0
	return 0



###########################################################
# The rest of the routines here are for internal use only #
###########################################################


def prep1(node):
	node.counter = [0, 0]
	node.deps = [], []
	type = node.GetType()
	if type == 'seq': # XXX not right!
		xnode, xside = node, HD
		for c in node.GetSchedChildren(0):
			prep1(c)
			adddep(xnode, xside, 0, c, HD)
			xnode, xside = c, TL
		adddep(xnode, xside, 0, node, TL)
	elif type in ('par', 'switch', 'excl') or (type in leaftypes and node.GetSchedChildren(0)):
		for c in node.GetSchedChildren(0):
			prep1(c)
			adddep(node, HD, 0, c, HD)
			adddep(c, TL, 0, node, TL)
		# Make sure there is *some* path from head to tail
		dur = MMAttrdefs.getattr(node, 'duration')
		if dur >= 0:
			adddep(node, HD, dur, node, TL)
	else:
		adddep(node, HD, -1, node, TL)


def prep2(node, root):
	# XXX we only deal with a single offset syncarc; all others are ignored
	delay = None
	# We ask the node for its begindelay.
	# If we're computing timing with download lags we should also get the
	# lag (which has been computed before we're called), otherwise the lag will be
	# zero. 
	delay, downloadlag = node.GetDelays(timingtype)
	delay = delay + downloadlag
	parent = node.GetSchedParent(0)
	if delay > 0 and parent is not None:
		if parent.GetType() == 'seq':
			xnode = parent
			xside = HD
			for n in parent.GetSchedChildren(0):
				if n is node:
					break
				xnode = n
				xside = TL
		else:
			xnode = parent
			xside = HD
		adddep(xnode, xside, delay, node, HD)
	for c in node.GetSchedChildren(0):
		prep2(c, root)


# propdown - propagate timing down the tree again
def propdown(node, stoptime, dftstarttime=0):
	tp = node.GetType()
	# Assure we have a start time and stop time
	if not hasattr(node, 't0'):
		node.t0 = dftstarttime
	if not hasattr(node, 't1'):
		node.t1 = stoptime

	if node.GetFill() == 'remove':
		stoptime = node.t1

	node.t2 = stoptime

	if tp in ('par', 'switch', 'excl', 'prio') or tp in leaftypes:
		for c in node.GetSchedChildren(0):
			propdown(c, stoptime, node.t0)
	elif tp == 'seq': # XXX not right!
		children = node.GetSchedChildren(0)
		if not children:
			return
		nextstart = node.t0
		for i in range(len(children)):
			c = children[i]
			fill = c.GetFill()
			if fill == 'freeze':
				if i == len(children)-1:
					endtime = node.t2
				elif hasattr(children[i+1], 't0'):
					endtime = children[i+1].t0
				else:
					endtime = node.t2
			elif fill == 'hold':
				endtime = node.t2
			else:
				endtime = c.t1
			propdown(c, endtime, nextstart)
			nextstart = c.t1

def adddep(xnode, xside, delay, ynode, yside):
	ynode.counter[yside] = ynode.counter[yside] + 1
	if delay >= 0 and xside in (HD, TL):
		xnode.deps[xside].append((delay, ynode, yside))


def decrement(q, delay, node, side):
	if delay > 0:
		id = q.enter(delay, 0, decrement, (q, 0, node, side))
		return
	x = node.counter[side] - 1
	node.counter[side] = x
	if x > 0:
		return
	if x < 0:
		raise CheckError, 'counter below zero!?!?'
	if side == HD:
		node.t0 = q.timefunc()
	elif side == TL:
		node.t1 = q.timefunc()
	node.node_to_arm = None
	node.t0t1_inherited = node.GetFill() != 'remove'
	if node.GetType() not in interiortypes and side == HD and not node.GetSchedChildren(0):
		dt = getduration(node)
		id = q.enter(dt, 0, decrement, (q, 0, node, TL))
	for d, n, s in node.deps[side]:
		decrement(q, d, n, s)


class pseudotime:
	def __init__(self, t):
		self.t = t
	def __repr__(self):
		return '<pseudotime instance, t=' + `self.t` + '>'
	def timefunc(self):
		return self.t
	def delayfunc(self, delay):
		self.t = self.t + delay
