# Define a 16x16 cursor looking like a watch

watch = [ \
	0x07e0, \
	0x07e0, \
	0x0c30, \
	0x1cb8, \
	0x389c, \
	0x308c, \
	0x308d, \
	0x378f, \
	0x378d, \
	0x300c, \
	0x300c, \
	0x1818, \
	0x1c38, \
	0x0e70, \
	0x07e0, \
	0x07e0, \
	]

watch.reverse() # Turn it upside-down

def defwatch(index):
	import gl
	gl.defcursor(index, watch*8)

def test():
	import gl
	gl.foreground()
	gl.winopen('test watchcursor')
	defwatch(1)
	gl.setcursor(1, 0, 0)
	import time
	time.sleep(10)
