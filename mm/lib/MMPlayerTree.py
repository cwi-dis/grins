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

Version = 'PlayerCache 1.0'		# version of player file

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
		else:
			print 'Warning: player file out of date'
	root = load(f, context)
	f.close()
	context.addhyperlinks(root.attrdict['hyperlinks'])
	context.addchannels(root.attrdict['channellist'])
	del root.attrdict['hyperlinks']
	del root.attrdict['channellist']
	return root

def WriteFile(root, filename):
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
	del root.attrdict['hyperlinks']
	del root.attrdict['channellist']
	f.close()

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
	if not parent or parent.type == 'bag':
		if parent:
			node.attrdict['bag'] = parent.uid
		else:
			node.attrdict['bag'] = None
		newattrs.append('bag')
		mini = node
	node.attrdict['mini'] = mini.uid
	newattrs.append('mini')
	if node is mini or node.uid in targets:
		sractions, srevents = mini.GenAllSR(node)
		node.attrdict['prearmlists'] = gen_prearms(mini)
		newattrs.append('prearmlists')
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
		node.attrdict['sractions'] = sractions
		node.attrdict['srevents'] = newevents
		newattrs.append('sractions')
		newattrs.append('srevents')
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
	node.mini = mapuid(context, attrdict['mini'])
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
			node.bag = mapuid(context, bag)
		else:
			node.bag = None
		del attrdict['bag']
	try:
		sractions = attrdict['sractions']
		srevents = attrdict['srevents']
		node.prearmlists = attrdict['prearmlists']
	except KeyError:
		pass
	else:
		# node is either a mini document or a hyperlink target
		del attrdict['sractions']
		del attrdict['srevents']
		del attrdict['prearmlists']
		for nevents, actions in sractions:
			for j in range(len(actions)):
				a, n = actions[j]
				if a not in (SR.SYNC, SR.SYNC_DONE):
					actions[j] = a, mapuid(context, n)
		node.sractions = sractions
		node.srevents = {}
		for event, action in srevents.items():
			a, n = event
			if a not in (SR.SYNC, SR.SYNC_DONE):
				n = mapuid(context, n)
			node.srevents[(a, n)] = action
		for list in node.prearmlists.values():
			for i in range(len(list)):
				a, n = list[i]
				list[i] = a, mapuid(context, n)
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

def mapuid(context, uid):
	try:
		return context.mapuid(uid)
	except NoSuchUIDError:
		return context.newnodeuid('xxx', uid)

def newnodeuid(context, type, uid):
	try:
		node = context.mapuid(uid)
	except NoSuchUIDError:
		return context.newnodeuid(type, uid)
	else:
		node.type = type
		return node
