# Calculate the difference between requested and assigned window
# origin.  This differs per window manager, e.g., for twm it's (1,21)
# but for 4Dwm  it's (0,0).  Apparently they disagree about whether
# the preferred size includes or excludes the frame added by the
# window manager.  This wouldn't be a big problem, except that if you
# repeatedly close a window and reopen it at its last position, it
# tends to drift away.
#
# The computed values are returned by the function calcwmcorr().
# We invert the y value because this is used by a module that deals in
# X coordinates, where (0,0) is top left, while in GL (0,0) is bottom left.
#
# The first time the function is called, it pops up a tiny window near
# the lower left corner (at (100, 100) to be precose), and immediately
# removes it.


# Function to do the actual calculation

def _calcwmcorr():
	import gl
	gl.foreground()
	gl.prefposition(100, 101, 100, 101) # x1, x2, y1, y2
	wid = gl.winopen('')
	x, y = gl.getorigin()
	gl.winclose(wid)
	return x-100, 100-y


# Variable caching the result

_wmcorr = None


# Public interface

def calcwmcorr():
	global _wmcorr
	if _wmcorr == None:
		_wmcorr = _calcwmcorr()
	return _wmcorr
