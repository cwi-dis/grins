__version__ = "$Id$"

import os, sys

verbose = 0
changed = 0

try:
	CMIF = os.environ['CMIF']
except KeyError:
	os.environ['CMIF'] = CMIF = '/ufs/sjoerd/src/mm'
if os.path.join(CMIF, 'common') not in sys.path:
	sys.path.insert(0, os.path.join(CMIF, 'lib'))
	sys.path.insert(0, os.path.join(CMIF, 'common'))
	sys.path.insert(0, os.path.join(CMIF, 'editor'))

from AnchorDefs import *

# recurse through the complete CMIF hierarchy and call func on each node.
def recur(root, func, arg):
	func(root, arg)
	for node in root.GetChildren():
		recur(node, func, arg)

# remove attr if its value is empty
def chkattr(node, attr):
	global changed
	try:
		val = node.GetAttr(attr)
	except:
		return
	if not val:
		if verbose:
			print 'deleting attribute',attr,'from node',node
		node.DelAttr(attr)
		changed = 1

# remove sync arcs of which the other end doesn't exist or is in a
# different minidocument.
def cleansyncarcs(node, attr):
	global changed
	from MMNode import leaftypes
	try:
		val = node.GetAttr(attr)
	except:
		return			# no such attribute
	root = node.FindMiniDocument()

	dellist = []
	for i in range(len(val)):
		xuid, xside, delay, yside = val[i]
		try:
			xnode = node.MapUID(xuid)
		except:
			# dangling sync arc: remove
			dellist.append(i)
		else:
			if xnode.FindMiniDocument() is root:
				if xnode.GetType() not in leaftypes:
					print 'Warning: sync arc to non-leaf node'
				elif xnode.GetChannel():
					print 'Warning: sync arc to channel-less node'
			else:
				# other end in other minidoc: remove
				dellist.append(i)
	# actually remove them, start at the end
	dellist.reverse()
	for i in dellist:
		if verbose:
			print 'deleting syncarc'
		del val[i]
	if val:
		# there are sync arcs left
		if dellist:
			# we have changed the list
			node.SetAttr(attr, val)
			changed = 1
	else:
		# no sync arcs left
		node.DelAttr(attr)
		changed = 1

def isbadlink(root, link):
	(uid1, aid1), (uid2, aid2), dir, type = link
	srcok = dstok = 0
	context = root.context
	uidmap = context.uidmap
	if uidmap.has_key(uid1):
		node = uidmap[uid1]
		if node.GetRoot() == root:
			alist = node.GetAttrDef('anchorlist', [])
			for a in alist:
				if aid1 == a[A_ID]:
					srcok = 1
					break
	if uidmap.has_key(uid2):
		node = uidmap[uid2]
		if node.GetRoot() == root:
			alist = node.GetAttrDef('anchorlist', [])
			for a in alist:
				if aid2 == a[A_ID]:
					dstok = 1
					break
	return not srcok and not dstok

def cleanlinks(root):
	global changed
	hyperlinks = root.context.hyperlinks
	badlinks = hyperlinks.selectlinks(lambda link, root = root: isbadlink(root, link))
	for link in badlinks:
		if verbose:
			print 'deleting link',`link`
		hyperlinks.dellink(link)
	if badlinks:
		changed = 1

def cleanup(file):
	global changed
	changed = 0
	import MMTree
	root = MMTree.ReadFile(file)
	recur(root, chkattr, 'anchorlist')
	recur(root, cleansyncarcs, 'synctolist')
	cleanlinks(root)
	if not changed:
		return
	dir, base = os.path.split(file)
	file = os.path.join(dir, 'new.' + base)
	try:
		MMTree.WriteFile(root, file)
	except IOError:
		MMTree.WriteFile(root, os.path.join('/usr/tmp', 'new.' + base))

if __name__ == '__main__'  or sys.argv[0] == __name__:
	import getopt
	global verbose
	opts, args = getopt.getopt(sys.argv[1:], 'v')
	if ('-v', '') in opts:
		verbose = 1
	for arg in args:
		cleanup(arg)
