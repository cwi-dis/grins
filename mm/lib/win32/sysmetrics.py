__version__ = "$Id$"

import win32ui,win32api,win32con

afx=win32ui.GetAfx()
sdk=win32ui.GetWin32Sdk()

from appcon import UNIT_MM, UNIT_SCREEN, UNIT_PXL

def GetSystemMetrics():
	cxframe=win32api.GetSystemMetrics(win32con.SM_CXFRAME)
	cyframe=win32api.GetSystemMetrics(win32con.SM_CYFRAME)
	cxborder=win32api.GetSystemMetrics(win32con.SM_CXBORDER)
	cyborder=win32api.GetSystemMetrics(win32con.SM_CYBORDER)
	cycaption=win32api.GetSystemMetrics(win32con.SM_CYCAPTION)
	return cxframe,cyframe,cxborder,cyborder,cycaption

def GetDeviceCaps():
	wnd=sdk.GetDesktopWindow()
	dc = wnd.GetDC();
	width_pxl=dc.GetDeviceCaps(win32con.HORZRES)
	height_pxl=dc.GetDeviceCaps(win32con.VERTRES)

	#Number of pxl per logical inch
	dpi_x=dc.GetDeviceCaps(win32con.LOGPIXELSX)
	dpi_y=dc.GetDeviceCaps(win32con.LOGPIXELSY)

	#width_mm=dc.GetDeviceCaps(win32con.HORZSIZE)
	#height_mm=dc.GetDeviceCaps(win32con.VERTSIZE)
	# or compute them (not the same, why?)
	width_mm=(float(width_pxl)*25.4) / dpi_x
	height_mm=(float(height_pxl)*25.4) / dpi_y

	depth=dc.GetDeviceCaps(win32con.BITSPIXEL)
	wnd.ReleaseDC(dc)
	return width_pxl,height_pxl,width_mm,height_mm,dpi_x,dpi_y,depth


[scr_width_pxl,scr_height_pxl,scr_width_mm,scr_height_mm,dpi_x,dpi_y,depth]=GetDeviceCaps()	
[cxframe,cyframe,cxborder,cyborder,cycaption]=GetSystemMetrics()
pixel_per_mm_x = float(scr_width_pxl) / scr_width_mm
pixel_per_mm_y = float(scr_height_pxl) / scr_height_mm
mm_per_point = 25.4 / 96			# 1 inch == 96 points == 25.4 mm


def mm2pxl_x(x):
	return int((float(x)/scr_width_mm)*scr_width_pxl)
def mm2pxl_y(y):
	return int((float(y)/scr_height_mm)*scr_height_pxl)
def mm2pxl(x,y):
	return int((float(x)/scr_width_mm)*width_pxl),int((float(y)/scr_height_mm)*scr_height_pxl)

def pxl2mm_x(x):
	return (float(x)/scr_width_pxl)*scr_width_mm
def pxl2mm_y(y):
	return (float(y)/scr_height_pxl)*scr_height_mm
def pxl2mm(x,y):
	return (float(x)/scr_width_pxl)*scr_width_mm,(float(y)/scr_height_pxl)*scr_height_mm

def in2pxl_x(x):
	return int(x*dpi_x)
def in2pxl_y(y):
	return int(y*dpi_y)
def in2pxl(x,y):
	return int(x*dpi_x),int(y*dpi_y)

def pxl2in_x(x):
	return float(x)/dpi_x
def pxl2in_y(y):
	return float(y)/dpi_y
def pxl2in(x,y):
	return float(x)/dpi_x,float(y)/dpi_y

def to_pixels(x,y,w,h,units):
	if x==None: x=0
	if y==None: y=0
	if units == UNIT_MM:
		if x is not None:
			x = int(float(x) * pixel_per_mm_x + 0.5)
		if y is not None:
			y = int(float(y) * pixel_per_mm_y + 0.5)
		w = int(float(w) * pixel_per_mm_x + 0.5)
		h = int(float(h) * pixel_per_mm_y + 0.5)
	elif units == UNIT_SCREEN:
		if x is not None:
			x = int(float(x) * scr_width_pxl + 0.5)
		if y is not None:
			y = int(float(y) * scr_height_pxl + 0.5)
		w = int(float(w) * scr_width_pxl + 0.5)
		h = int(float(h) * scr_height_pxl + 0.5)
	elif units == UNIT_PXL:
		if x is not None:
			x = int(x)
		if y is not None:
			y = int(y)
		w = int(w)
		h = int(h)
	else:
		raise error, 'bad units specified'
	return (x,y,w,h)

def size2pix(size,units):
	width,height=size
	if units == UNIT_MM:
		width = int(float(width) * pixel_per_mm_x + 0.5)
		height = int(float(height) * pixel_per_mm_y + 0.5)
	elif units == UNIT_SCREEN:
		width = int(float(width) * scr_width_pxl + 0.5)
		height = int(float(height) * scr_height_pxl + 0.5)
	elif units == UNIT_PXL:
		width = int(width)
		height = int(height)
	else:
		raise error, 'bad units specified'
	return (width,height)

