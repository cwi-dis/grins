# fastimp.py
import sys, imp, os

suffixes = map(lambda x: x[0], imp.get_suffixes())

cache = {}

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
	isabs = os.path.isabs
	for dir in sys.path:
		if not isabs(dir):
			try:
				# just try it for relative paths
				m = imp.find_module(module, [dir])
			except ImportError, msg:
				if msg[:16] == 'No module named ':
					# not found
					continue
				else:
					raise ImportError, msg
			else:
				return m
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
							cd[name[:-n]] = None
		if cd.has_key(module):
			return imp.find_module(module, [dir])
	raise ImportError, 'no module named %s' % module

def install():
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
