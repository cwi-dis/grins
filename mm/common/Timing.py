__version__ = "$Id$"

# Interface to calculate the timing of a (sub)tree

import time
import sched
import MMAttrdefs
from MMExc import *
from MMTypes import *
from HDTL import HD, TL

real_interiortypes = ('par', 'seq')


# The routine 'changedtimes' signifies that the timing might have changed
# (but is not needed at the moment), and the routine 'needtimes' signifies
# that somebody needs correct timing (possibly resulting in a recalc).
# Finally, 'do_times' does the actual calculation.
# As an option, 'hastimes' can be used to check whether the timings
# are correct (this is used to set the 'calculate times' button).

def changedtimes(node):
	try:
		del node.initial_arms
	except (KeyError, AttributeError): # initial_arms does not exist
		pass
	for child in node.GetChildren():
		changedtimes(child)

def hastimes(node):
	try:
		if node.initial_arms is not None:
			return 1
	except AttributeError: # initial_arms does not exist
		pass
	return 0

def needtimes(node):
	try:
		if node.initial_arms is not None:
			return # The cached value is valid
	except AttributeError: # initial_arms does not exist
		pass
	do_times(node)


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

def do_times(node):
	t0 = time.time()
## 	print 'do_times...'
	
	# These globals are used only while in do_times();
	# they are changed by decrememt()
	
	global getd_times # Used to calculate time spent in getduration()
	getd_times = 0
	
	global last_node # Keeps track of the last node played per channel
	last_node = {}
	
	global initial_arms # Keeps track of the first node played per channel
	initial_arms = []

	node.t1 = 0
	del node.t1
	
	prepare(node)
	_do_times_work(node)
	try:
		void = node.t1
	except AttributeError:
		import windowinterface
		windowinterface.showmessage('WARNING: circular timing dependencies.\n'+\
			  '(ignoring sync arcs and trying again)')
		prep1(node)
		_do_times_work(node)
	t1 = time.time()
	propdown(node, node.t1)
	t2 = time.time()

	node.initial_arms = initial_arms

## 	print 'done in', round(t2-t0, 3), 'sec.'
## 	print '(of which', round(getd_times, 3), 'sec. in getduration()',
## 	print 'and', round(t2-t1, 3), 'sec. in propdown)'

def _do_times_work(node):
	pt = pseudotime(0.0)
	q = sched.scheduler(pt.timefunc, pt.delayfunc)
	node.counter[HD] = 1
	decrement(q, 0, node, HD)
	q.run()

# Interface to get the "initial arms" nodes of a tree.
# Call only after needtimes has calculated them.

def getinitial(node):
	return node.initial_arms # AttributeError here if called at wrong time


# Interface to the prep1() and prep2() functions; these are also used
# by the player (which uses a different version of decrement()).
# This adds instance variables 'counter' and 'deps' to each node,
# with meanings that can be deduced from the code below. :-) :-) :-)
#
def prepare(node):
## 	print '\tprepare...'
	t0 = time.time()
	prep1(node)
	t1 = time.time()
	prep2(node, node)
	t2 = time.time()
## 	print '\tdone in', round(t1-t0, 3), '+', round(t2-t1, 3),
## 	print '=', round(t2-t0, 3), 'sec'
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
	type = node.GetType()
	if type in interiortypes:
		for c in node.GetChildren():
			cleanup(c)


# Return a node's nominal duration, in seconds, as a floating point value.
# Should only be applied to leaf nodes.
#
from AnchorDefs import A_TYPE, ATYPE_PAUSE, ATYPE_ARGS
#
is_warned = 0

def getduration(node):
	global is_warned
	import Duration
	d = Duration.get(node)
	node.timing_discont = 0
	if d > 0:
		return d
	# Check for pausing anchor
	try:
		alist = node.GetRawAttr('anchorlist')
	except NoSuchAttrError:
		alist = None
	if alist: # Not None and not []
		for a in alist:
			if a[A_TYPE] in (ATYPE_PAUSE, ATYPE_ARGS):
				if not is_warned:
					print 'Warning: document contains (obsolete) pausing anchors'
					is_warned = 1
				break
	if d < 0:
	        node.timing_discont = 9.9
		return 10
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
		for c in node.GetChildren():
			prep1(c)
			adddep(xnode, xside, 0, c, HD)
			xnode, xside = c, TL
		adddep(xnode, xside, 0, node, TL)
	elif type == 'par':
		for c in node.GetChildren():
			prep1(c)
			adddep(node, HD, 0, c, HD)
			adddep(c, TL, 0, node, TL)
		# Make sure there is *some* path from head to tail
		adddep(node, HD, MMAttrdefs.getattr(node, 'duration'), node, TL)
	elif type in bagtypes:
		adddep(node, HD, 0, node, TL)
	else:
		# Special case -- delay -1 means execute leaf node
		# of leaf node when playing
		if hasattr(node, 'prearm_event'):
			del node.prearm_event
		adddep(node, HD, -1, node, TL)


def prep2(node, root):
##	if not node.GetSummary('synctolist'): return
	arcs = MMAttrdefs.getattr(node, 'synctolist')
	for arc in arcs:
		xuid, xside, delay, yside = arc
		try:
			xnode = node.MapUID(xuid)
		except NoSuchUIDError:
			# Skip sync arc from non-existing node
			continue
		# skip out-of-minidocument sync arcs
		if xnode.FindMiniDocument() is node.FindMiniDocument():
			adddep(xnode, xside, delay, node, yside)
	#
	if node.GetType() in real_interiortypes:
		for c in node.GetChildren(): prep2(c, root)


# propdown - propagate timing down the tree again
def propdown(node, stoptime):
	tp = node.GetType()
	if not node.t0t1_inherited:
		stoptime = node.t1
	if tp == 'par':
		for c in node.GetChildren():
			propdown(c, stoptime)
	elif tp == 'seq': # XXX not right!
		children = node.GetChildren()
		if not children:
			return
		lastchild = children[-1]
		children = children[:-1]
		for c in children:
			propdown(c, c.t1)
		propdown(lastchild, stoptime)
	elif node.t0t1_inherited:
		node.t1 = stoptime


def adddep(xnode, xside, delay, ynode, yside):
	ynode.counter[yside] = ynode.counter[yside] + 1
	if delay >= 0:
		xnode.deps[xside].append(delay, ynode, yside)


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
	if node.GetType() in interiortypes:
		node.t0t1_inherited = 1
	elif side == HD:
		t0 = time.time()
		dt = getduration(node)
		node.t0t1_inherited = (dt == 0 and len(node.deps[TL]) <= 1)
			# Don't mess if it has timing deps
		t1 = time.time()
		global getd_times
		getd_times = getd_times + (t1-t0)
		id = q.enter(dt, 0, decrement, (q, 0, node, TL))
		if node.GetChannel():
			cname = node.GetChannelName()
			if node.GetRawAttrDef('arm_duration', -1) >= 0:
				if last_node.has_key(cname):
					ln = last_node[cname]
					ln.node_to_arm = node
				else:
					global initial_arms
					initial_arms.append(node)
			last_node[cname] = node
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
