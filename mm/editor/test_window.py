"""Test windowinterface drawing, editor specifics"""
import sys
import os

if os.name == 'posix':
	sys.path.append("../lib")
	import X_window
	window = X_window
elif os.name == 'mac':
	sys.path.append("::lib")
	import mac_window
	window = mac_window
# etc...

#
# Create a window
#
print "Creating a window 1x1cm from topleft, 10x10cm in size"

w = window.newwindow(10, 10, 100, 100, "Test window")

print "Creating a greyish background with some shapes"

dl = w.newdisplaylist((200,200,200))

print "A red house"
dl.drawfpolygon((255, 0, 0),
		[(0.1, 0.1), (0.15, 0.05), (0.2, 0.1), (0.2, 0.2), (0.1,0.2)])

print "A greyish 3d-box"
dl.draw3dbox((244, 244, 244), (204, 204, 204), (40, 40, 40), (91, 91, 91),
	     (0.3, 0.1, 0.1, 0.1))

print "A diamond"
dl.drawdiamond((0.5, 0.1, 0.1, 0.1))

print "A blue diamond:-)"
dl.drawfdiamond((0,0,255), (0.7, 0.1, 0.1, 0.1))

print "A greyish 3d-diamond"
dl.draw3ddiamond((244, 244, 244), (204, 204, 204), (40, 40, 40), (91, 91, 91),
	     (0.1, 0.3, 0.1, 0.1))

print "A green arrow"
dl.drawarrow((0,255,0), (0.1, 0.5), (0.9, 0.5))

print "Rendering it"
dl.render()

print "RUN!"
# Doesn't work: window.addclosecallback(sys.exit, (0,))
window.mainloop()
