"""mac_image - Helper routines (hacks) for images"""

__version__ = "$Id$"

import imgformat
from Carbon import Qd
import time
import struct
import MacOS

_fmt_to_mac = {
	imgformat.macrgb16 : (16, 16, 3, 5, 2),
	imgformat.macrgb : (16, 32, 3, 8, 4),
}

def mkpixmap(w, h, fmt, data):
	"""kludge a pixmap together"""
	fmtinfo = _fmt_to_mac[fmt]
	
	rv = struct.pack("lHhhhhhh",
		id(data)+MacOS.string_id_to_buffer,
		w*fmtinfo[4] + 0x8000,
		0, 0, h, w,
		0,
		0) + struct.pack("lllhhhhlll", 
		0, # XXXX?
		72<<16, 72<<16,
		fmtinfo[0], fmtinfo[1],
		fmtinfo[2], fmtinfo[3],
		0, 0, 0)
##	print 'Our pixmap, size %d:'%len(rv)
##	dumppixmap(rv)
	return Qd.RawBitMap(rv)
	
def mkbitmap(w, h, fmt, data):
	if fmt != imgformat.xbmpacked:
		raise imgformat.error, 'Incorrect format for mkbitmap: %s'%fmt
	rv = struct.pack("lhhhhh",
		id(data)+MacOS.string_id_to_buffer,
		(w+7)/8,
		0, 0, h, w)
	return Qd.RawBitMap(rv)
		

def dumppixmap(data):
	baseAddr, \
		rowBytes, \
		t, l, b, r, \
		pmVersion, \
		packType, packSize, \
		hRes, vRes, \
		pixelType, pixelSize, \
		cmpCount, cmpSize, \
		planeBytes, pmTable, pmReserved \
			= struct.unpack("lHhhhhhhlllhhhhlll", data)
	print 'Base:       0x%x'%baseAddr
	print 'rowBytes:   %d (0x%x)'%(rowBytes&0x3fff, rowBytes)
	print 'rect:       %d, %d, %d, %d'%(t, l, b, r)
	print 'pmVersion:  0x%x'%pmVersion
	print 'packing:    %d %d'%(packType, packSize)
	print 'resolution: %f x %f'%(float(hRes)/0x10000, float(vRes)/0x10000)
	print 'pixeltype:  %d, size %d'%(pixelType, pixelSize)
	print 'components: %d, size %d'%(cmpCount, cmpSize)
	print 'planeBytes: %d (0x%x)'%(planeBytes, planeBytes)
	print 'pmTable:    0x%x'%pmTable
	print 'pmReserved: 0x%x'%pmReserved
	for i in range(0, len(data), 16):
		for j in range(16):
			if i + j < len(data):
				print '%02.2x'%ord(data[i+j]),
		print