import os
import MMNode
from ChannelMap import channelmap
from stat import ST_MTIME, ST_SIZE
import marshal
from MMTypes import *
from MMExc import *
import MMAttrdefs
import Timing
import SR

error = 'MMTree.error'

Version = 'PlayerCache 2.1'		# version of player file

def ReadFile(filename):
	try:
		stf = os.stat(filename)
	except os.error:
		raise error, 'cannot stat ' + filename
	context = MMNode.MMNodeContext(MMNode.MMNode)
	context.setdirname(os.path.dirname(filename))
	base = os.path.basename(filename)
	cache = cachename(filename)
	try:
		f = open(cache, 'rb')
	except IOError:
		raise error, 'cannot open ' + cache
	header = marshal.load(f)
	if header != (Version, base, stf[ST_MTIME], stf[ST_SIZE]):
		if header[0] != Version:
			raise error, 'version mismatch'
		if header[1] != base:
			print 'Warning: player file does not belong to CMIF file'
		elif header[2:] != (stf[ST_MTIME], stf[ST_SIZE]):
			print 'Warning: player file out of date'
	root = load(f, context)
	context.root = root
	root.sroffs = marshal.load(f)
	root.fildes = f
	context.addhyperlinks(root.attrdict['hyperlinks'])
	context.addchannels(root.attrdict['channellist'])
	del root.attrdict['hyperlinks']
	del root.attrdict['channellist']
	return root

def WriteFile(root, filename):
	global srrecs
	srrecs = []
	try:
		stf = os.stat(filename)
	except os.error:
		raise error, 'cannot stat ' + filename
	base = os.path.basename(filename)
	cache = cachename(filename)
	try:
		f = open(cache, 'wb')
	except IOError:
		raise error, 'cannot create ' + cache
	header = (Version, base, stf[ST_MTIME], stf[ST_SIZE])
	root.attrdict['hyperlinks'] = root.context.get_hyperlinks(root)
	clist = []
	for cname in root.context.channelnames:
		clist.append(cname, root.context.channeldict[cname]._getdict())
	root.attrdict['channellist'] = clist
	marshal.dump(header, f)
	targets = map(lambda x: ((x[2] == 1 and x[0]) or x[1])[0],
		      root.context.hyperlinks.links)
	dump(root, root, f, targets)
	sroffs = [0] * len(srrecs)
	sroff = f.tell()
	marshal.dump(sroffs, f)		# placeholder for now
	for i in range(len(srrecs)):
		sroffs[i] = f.tell()
		marshal.dump(srrecs[i], f)
	f.seek(sroff)
	marshal.dump(sroffs, f)
	del root.attrdict['hyperlinks']
	del root.attrdict['channellist']
	f.close()
	if os.name == 'mac':
		import macfs
		import macostools
		fss = macfs.FSSpec(cache)
		fss.SetCreatorType('CMIF', 'CMP ')
		macostools.touched(fss)

def cachename(filename):
	# return the name of the cache file for the given filename.
	import string
	cache = filename
	if string.lower(cache[-5:]) == '.cmif':
		cache = cache[:-5]
	return cache + '.cmp'

def attrnames(node):
	# return a list of attribute names that are valid for node.
	namelist = ['name', 'channel', 'comment']
	if node.GetType() == 'bag':
		namelist.append('bag_index')
	ctype = node.GetChannelType()
	if channelmap.has_key(ctype):
		cclass = channelmap[ctype]
		# Add the class's declaration of attributes
		namelist = namelist + cclass.node_attrs
		for name in cclass.chan_attrs:
			if name in namelist: continue
			if MMAttrdefs.getdef(name)[5] == 'channel':
				namelist.append(name)
		for name in cclass.node_attrs:
			if name in namelist: continue
			namelist.append(name)
	return namelist

# Internals to dump and restore nodes

def dump(node, mini, f, targets):
	newattrs = []
	if node.type in interiortypes:
		children = node.children
		extra = len(children)
		if node.type != 'bag':
			channels, err = node.GetAllChannels()
			if err:
				print 'Error: overlap in channels'
			node.attrdict['channels'] = channels
			newattrs.append('channels')
	else:
		extra = node.values
		children = []
	for name in attrnames(node):
		if not node.attrdict.has_key(name):
			node.attrdict[name] = MMAttrdefs.getattr(node, name)
			newattrs.append(name)
	parent = node.parent
	if parent is None or parent.type == 'bag':
		if parent is not None:
			node.attrdict['bag'] = parent.uid
		else:
			node.attrdict['bag'] = None
		newattrs.append('bag')
		mini = node
	node.attrdict['mini'] = mini.uid
	newattrs.append('mini')
	if node is mini or node.uid in targets or node.GetType() == 'bag':
		sractions, srevents = mini.GenAllSR(node)
		prearmlists = gen_prearms(mini)
		# convert MMNode instances to UIDs
		for i in range(len(sractions)):
			nevents, actions = sractions[i]
			newactions = []
			for a, n in actions:
				try:
					n = n.uid
				except AttributeError:
					pass
				newactions.append(a, n)
			sractions[i] = (nevents, newactions)
		newevents = {}
		for event, action in srevents.items():
			a, n = event
			try:
				n = n.uid
			except AttributeError:
				pass
			newevents[(a, n)] = action
		node.attrdict['sr_no'] = len(srrecs) # index of entry in list
		newattrs.append('sr_no')
		srrecs.append((sractions, newevents, prearmlists))
	try:
		node.attrdict['t0'] = node.t0
		node.attrdict['t1'] = node.t1
		newattrs.append('t0')
		newattrs.append('t1')
	except AttributeError:
		pass
	# dump the node and it's children
	marshal.dump((node.type, node.uid, node.attrdict, extra), f)
	for c in children:
		dump(c, mini, f, targets)
	# remove added attributes
	for name in newattrs:
		del node.attrdict[name]

def load(f, context):
	type, uid, attrdict, extra = marshal.load(f)
	node = newnodeuid(context, type, uid)
	node.attrdict = attrdict
	if node.type in interiortypes:
		children = []
		for i in range(extra):
			children.append(load(f, context))
		if node.type == 'bag':
			node.children = children
		else:
			node.channels = attrdict['channels']
			del attrdict['channels']
	else:
		node.values = extra
	node.mini = context.uidmap[attrdict['mini']]
	del attrdict['mini']
	try:
		node.t0 = attrdict['t0']
		node.t1 = attrdict['t1']
		del attrdict['t0']
		del attrdict['t1']
	except KeyError:
		pass
	try:
		bag = attrdict['bag']
	except KeyError:
		pass
	else:
		# node is a mini document
		if bag:
			node.bag = context.uidmap[bag]
		else:
			node.bag = None
		del attrdict['bag']
	try:
		node.sr_no = attrdict['sr_no']
	except KeyError:
		# not a hyperlink destination
		pass
	return node

def gen_prearms(node):
	#
	# Create channel lists
	#
	channelnames, err = node.GetAllChannels()
	if err:
		enode, echan = err
		ename = MMAttrdefs.getattr(enode, 'name')
		print 'Error: overlap in channels' + \
		      '\nchannels:' + (`echan`[1:-1]) + \
		      '\nparent node:' + ename
		return
	#
	# Create per-channel list of prearms
	#
	prearmlists = {}
	for ch in channelnames:
		prearmlists[ch] = []
	GenAllPrearms(node, prearmlists)
	node.EndPruneTree()
	Timing.needtimes(node)
	return prearmlists

def GenAllPrearms(node, prearmlists):
	nodetype = node.GetType()
	if nodetype == 'bag':
		return
	if nodetype in leaftypes:
		chan = MMAttrdefs.getattr(node, 'channel')
		prearmlists[chan].append((SR.PLAY_ARM, node.uid))
		return
	for child in node.wtd_children:
		GenAllPrearms(child, prearmlists)

# this gets called very often so had better be as fast as possible
def mapuid(context, uid):
	try:
		return context.uidmap[uid] # we know about the internals...
	except KeyError:
		return context.newnodeuid('xxx', uid)

def newnodeuid(context, type, uid):
	try:
		node = context.uidmap[uid] # we also know about the internals
	except KeyError:
		return context.newnodeuid(type, uid)
	else:
		node.type = type
		return node
