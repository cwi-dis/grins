# Convert pathnames containing DOS-compatible bits to NT
# pathnames. The file must exist for this to work.
# Jack Jansen, jack@oratrix.nl
#
# XXXX Does not handle . and .. in pathname
#
import os
import win32api

def short2longpath(pathname):
	"""Convert DOS pathname to full NT pathname."""
	dir, file = os.path.split(pathname)
	if not file:
		return dir
	longfile = _short2longfile(pathname)
	longdir = short2longpath(dir)
	return os.path.join(longdir, longfile)
	
def _short2longfile(pathname):
	list = win32api.FindFiles(pathname)
	if not list:
		raise IOError, "No files match %s"%pathname
	if len(list) > 1:
		raise IOError, "Multiple files match %s"%pathname
	return list[0][8]
	
if __name__ == '__main__':
	while 1:
		x = raw_input()
		print short2longpath(x)
		