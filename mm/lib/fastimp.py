__version__ = "$Id$"

# fastimp.py
import sys, imp, os

suffixes = map(lambda x: x[0], imp.get_suffixes())

cache = {}
modcache = {}
absdirs = {}

def fast__import__(name, globals=None, locals=None, fromlist=None):
    # Fast path: see if the module has already been imported.
    # Use try--except on the assumption that most of the time the
    # module has already been imported.
    try:
        return sys.modules[name]
    except KeyError:
	pass

    # If any of the following calls raises an exception,
    # there's a problem we can't handle -- let the caller handle it.

    # See if it's a built-in module.
    m = imp.init_builtin(name)
    if m:
        return m

    # See if it's a frozen module.
    m = imp.init_frozen(name)
    if m:
        return m

    # Search the default path (i.e. sys.path).
    fp, pathname, (suffix, mode, type) = fast_find_module(name)

    # See what we got.
    try:
        if type == imp.C_EXTENSION:
            return imp.load_dynamic(name, pathname)
        if type == imp.PY_SOURCE:
            return imp.load_source(name, pathname, fp)
        if type == imp.PY_COMPILED:
            return imp.load_compiled(name, pathname, fp)

        # Shouldn't get here at all.
        raise ImportError, '%s: unknown module type (%d)' % (name, type)
    finally:
        # Since we may exit via an exception, close fp explicitly.
        fp.close()

def fast_find_module(module):
	global path, stat, modcache
	npath = tuple(sys.path)
	if npath != path and (len(npath) <= len(path) or
			      npath[:len(path)] != path):
		print 'path changed'
		# sys.path has changed by something other than
		# extending at the end, so invalidate the cache
		path = tuple(sys.path)
		modcache = {}
	path = npath

	if absdirs:
		nstat = os.stat(os.curdir)
		if nstat != stat:
			print 'dir changed'
			# directory has changed, invalidate cache
			stat = nstat
			modcache = {}
			for dir in absdirs.keys():
				try:
					del cache[dir]
				except KeyError:
					pass

	isabs = os.path.isabs
	
	try:
		dir = modcache[module]
	except KeyError:
		pass
	else:
		try:
			return imp.find_module(module, [dir])
		except ImportError, msg:
			if msg[:16] == 'No module named ':
				# not found, remove from cache
				del modcache[module]
			else:
				# some other reason
				raise ImportError, msg
	for dir in sys.path:
		if not isabs(dir):
			absdirs[dir] = 0

		try:
			cd = cache[dir]
		except KeyError:
			cache[dir] = cd = {}
			try:
				names = os.listdir(dir)
			except os.error:
				pass
			else:
				for name in names:
					for suff in suffixes:
						n = len(suff)
						if name[-n:] == suff:
							nm = name[:-n]
							cd[nm] = 0
							if not modcache.has_key(nm):
								modcache[nm] = dir
		if cd.has_key(module):
			try:
				m = imp.find_module(module, [dir])
			except ImportError, msg:
				if msg[:16] == 'No module named ':
					# not found
					del cd[module]
					try:
						del modcache[module]
					except KeyError:
						pass
					continue
				else:
					raise ImportError, msg
			else:
				return m
	raise ImportError, 'no module named %s' % module

def install():
	global path, stat, modcache
	path = tuple(sys.path)		# save a copy of sys.path
	stat = os.stat(os.curdir)
	modcache = {}
	import __builtin__
	__builtin__.__import__ = fast__import__

def testmain():
	install()
	test()

def test():
	import time
	t0 = time.time()
	import Tkinter
	t1 = time.time()
	print t1-t0

if __name__ == '__main__':
	testmain()
