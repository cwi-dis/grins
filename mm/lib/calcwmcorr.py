# Calculate the difference between requested and assigned window origin.
# This differs per window manager, e.g., for twm it's (1,21) but for 4Dwm
# it's (0,0).
# We invert the y value because this is used by a module that deals in
# X coordinates, where (0,0) is top left, while in GL (0,0) is bottom left.

import gl
gl.foreground()
gl.prefposition(100, 101, 100, 101) # x1, x2, y1, y2
wid = gl.winopen('')
x, y = gl.getorigin()
gl.winclose(wid)
WMCORR = x-100, 100-y
print 'WMCORR=' + `WMCORR[0]` + ',' + `WMCORR[1]`
