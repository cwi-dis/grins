import os, sys

if not os.environ.has_key('CMIF'):
	os.environ['CMIF'] = '/ufs/sjoerd/src/mm'
CMIF = os.environ['CMIF']
if (CMIF + '/lib') not in sys.path:
	sys.path.append(CMIF + '/lib')

def getviewroot(node):
	parent = node.parent
	while parent and parent.type != 'bag':
		node = parent
		parent = node.parent
	return node

# recurse through the complete CMIF hierarchy and call func on each node.
def recur(root, func, arg):
	func(root, arg)
	for node in root.GetChildren():
		recur(node, func, arg)

# remove attr if its value is empty
def chkattr(node, attr):
	try:
		val = node.GetAttr(attr)
	except:
		return
	if not val:
		node.DelAttr(attr)

# remove sync arcs of which the other end doesn't exist or is in a
# different minidocument.
def cleansyncarcs(node, attr):
	from MMNode import leaftypes
	try:
		val = node.GetAttr(attr)
	except:
		return			# no such attribute
	dellist = []
	for i in range(len(val)):
		xuid, xside, delay, yside = val[i]
		try:
			xnode = node.MapUID(xuid)
		except:
			# dangling sync arc: remove
			dellist.append(i)
		else:
			root = getviewroot(node)
			if root.IsAncestorOf(xnode) and \
			   xnode.GetType() in leaftypes and \
			   xnode.GetChannel():
				pass
			else:
				# other end in other minidoc: remove
				dellist.append(i)
	# actually remove them, start at the end
	dellist.reverse()
	for i in dellist:
		del val[i]
	if val:
		# there are sync arcs left
		if dellist:
			# we have changed the list
			node.SetAttr(attr, val)
	else:
		# no sync arcs left
		node.DelAttr(attr)

def cleanup(file):
	import MMTree
	root = MMTree.ReadFile(file)
	recur(root, chkattr, 'anchorlist')
	recur(root, cleansyncarcs, 'synctolist')
	dir, base = os.path.split(file)
	file = os.path.join(dir, 'new.' + base)
	try:
		MMTree.WriteFile(root, file)
	except IOError:
		MMTree.WriteFile(root, os.path.join('/usr/tmp', 'new.' + base))

if __name__ == '__main__'  or sys.argv[0] == __name__:
	for arg in sys.argv[1:]:
		cleanup(arg)
