# Interface to calculate the timing of a (sub)tree

import sched

import MMAttrdefs
from MMExc import *

from ChannelMap import channelmap

HD, TL = 0, 1


# Calculate the nominal times for each node in the given subtree.
# When the function is done, each node has two instance variables
# 't0' and 't1' that give the begin and end time of the node.
# By definition, 't0' for the given root is zero; its 't1' value
# gives the total duration.
#
# This takes sync arcs within the subtree into account, but ignores
# sync arcs with one end outside the given subtree.
#
# XXX For now, all sync arcs must actually point in the given subtree.
#
# Any circularities in the sync arcs are detected and "reported"
# as exceptions.
#
def calctimes(root):
	prepare(root)
	if root.counter[HD] <> 0:
		raise RuntimeError, 'head of root has dependencies!?!'
	pt = pseudotime().init(0.0)
	q = sched.scheduler().init(pt.timefunc, pt.delayfunc)
	root.counter[HD] = 1
	decrement(q, (0, root, HD))
	q.run()
	cleanup(root)


# Interface to the prep1() and prep2() functions; these are also used
# by the player.
#
def prepare(root):
	prep1(root)
	prep2(root)


# Interface to clean up the mess left behind by prep1() and prep2().
#
def cleanup(node):
	del node.counter
	del node.deps
	type = node.GetType()
	if type in ('seq', 'par'):
		for c in node.GetChildren():
			self.cleanup(c)


def prep1(node):
	node.counter = [0, 0]
	node.deps = [], []
	type = node.GetType()
	if type = 'seq':
		xnode, xside = node, HD
		for c in node.GetChildren():
			prep1(c)
			adddep(xnode, xside, 0, c, HD)
			xnode, xside = c, TL
		adddep(xnode, xside, 0, node, TL)
	elif type = 'par':
		for c in node.GetChildren():
			prep1(c)
			adddep(node, HD, 0, c, HD)
			adddep(c, TL, 0, node, TL)
	else:
		# Special case -- delay -1 means execute leaf node
		# of leaf node when playing
		adddep(node, HD, -1, node, TL)


def prep2(node):
	arcs = MMAttrdefs.getattr(node, 'synctolist')
	for arc in arcs:
		print 'sync arc:', arc, 'to:', node.GetUID()
		xuid, xside, delay, yside = arc
		xnode = node.MapUID(xuid)
		adddep(xnode, xside, delay, node, yside)
	#
	if node.GetType() in ('seq', 'par'):
		for c in node.GetChildren(): prep2(c)


def adddep(xnode, xside, delay, ynode, yside):
	ynode.counter[yside] = ynode.counter[yside] + 1
	if delay >= 0:
		xnode.deps[xside].append(delay, ynode, yside)


def decrement(q, (delay, node, side)):
	if delay > 0:
		id = q.enter(delay, 0, decrement, (q, (0, node, side)))
		return
	x = node.counter[side] - 1
	node.counter[side] = x
	if x > 0:
		return
	if x < 0:
		raise RuntimeError, 'counter below zero!?!?'
	if side = HD:
		node.t0 = q.timefunc()
	elif side = TL:
		node.t1 = q.timefunc()
	if node.GetType() not in ('seq', 'par'):
		if side = HD:
			dt = getduration(node)
			id = q.enter(dt, 0, decrement, (q, (0, node, TL)))
	for arg in node.deps[side]:
		decrement(q, arg)


class pseudotime():
	def init(self, t):
		self.t = t
		return self
	def timefunc(self):
		return self.t
	def delayfunc(self, delay):
		self.t = self.t + delay
		print 'delay', delay, '-->', self.t


# Return a node's nominal duration, in seconds, as a floating point value.
# Should only be applied to leaf nodes.
#
def getduration(node):
	if node.GetType() not in ('imm', 'ext', 'grp'):
		raise RuntimeError, 'Timing.getduration() on non-leaf'
	cname = MMAttrdefs.getattr(node, 'channel')
	cattrs = node.context.channeldict[cname]
	ctype = cattrs['type']
	cclass = channelmap[ctype]
	instance = cclass() # XXX Not initialized!  Walking on thin ice here...
	return instance.getduration(node)
