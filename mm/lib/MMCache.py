# Cache parsing results of CMIF files

from MMNode import interiortypes
import marshal
import os
from stat import ST_MTIME, ST_SIZE
import string
import MMAttrdefs

# Load the cached version of filename, if valid, else None

def loadcache(filename, context):
	try:
		stf = os.stat(filename)
	except os.error:
		print 'Can\'t stat', filename
		return None
	base = os.path.basename(filename)
	cache = cachename(filename)
	try:
		f = open(cache, 'rb')
	except IOError:
		print 'Can\'t open CMIF cache file', cache
		return None
	header = marshal.load(f)
	if header <> ('MMCache 1.0', base, stf[ST_MTIME], stf[ST_SIZE]):
		print 'CMIF cache file', cache, 'out of date'
		return None
	print 'Loading CMIF cache file', cache
	return load(f, context)

# Dump a node to the cached version of filename

def dumpcache(root, filename):
	try:
		stf = os.stat(filename)
	except os.error:
		print 'Can\'t stat', filename
		return 
	base = os.path.basename(filename)
	cache = cachename(filename)
	print 'Writing CMIF cache', cache
	try:
		f = open(cache, 'wb')
	except IOError, msg:
		print cache, ': failed to write CMIF cache:', msg
		return
	header = ('MMCache 1.0', base, stf[ST_MTIME], stf[ST_SIZE])
	marshal.dump(header, f)
	dump(root, f)
	f.close()
	print 'Successfully wrote CMIF cache', cache

# Compute the name of the cached version of filename

def cachename(filename):
	cache = filename
	if string.lower(cache[-5:]) == '.cmif': cache = cache[:-5]
	return cache + '.cmc'

# Load a node from a cache file -- recursive

def load(f, context):
	type, uid, attrdict, extra = marshal.load(f)
	node = context.newnodeuid(type, uid)
	for k in attrdict.keys():
	    if not MMAttrdefs.exists(k):
		print 'Warning: deleted unknown attribute', k
		del attrdict[k]
	node.attrdict = attrdict
	if type in interiortypes:
		for i in range(extra):
			node._addchild(load(f, context))
	elif type == 'imm':
		node.values = extra
	return node

# Dump a node to a cache file -- recursive

def dump(node, f):
	if node.type in interiortypes:
		children = node.children
		extra = len(children)
	else:
		extra = node.values
		children = []
	marshal.dump((node.type, node.uid, node.attrdict, extra), f)
	for c in children:
		dump(c, f)
