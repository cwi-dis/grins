__version__ = "$Id$"

# Will develop a display list (equivalent) that is composed of
# aggregated editable geometric primitives rather than fixed
# primitives.

import windowinterface, WMEVENTS
from AppDefaults import *

from Widgets import *

class GeoWidget(Widget):
	# This is the new "display list", and can have the same potential functionality.
	# The motivation behind creating this class is to create a "display list" which
	# contains editable elements.
	# Currently, it requires the existing display list implementation to run.

	def __init__(self, root):
		# Root is the root window.
		Widget.__init__(self, root)
		self.canvassize = 800, 200
		self.widgets = []

	def AddWidget(self, widget):
		assert isinstance(widget, Widget)
		self.widgets.append(widget)
		widget.parent = self
		return widget

	def DelWidget(self, widget):
		assert isinstance(widget, Widget)
		self.widgets.remove(widget)

	# Pretend to be a list.
	append=AddWidget
	def __setitem__(self, key, value):
		self.AddWidget(value)

	def __getitem__(self, key):
		return self.widgets[key]

	def redraw(self):
		# Handle display lists and so forth.
		# I may reuse the display list for small changes.
		x,y = self.canvassize
		self.root.window.setcanvassize((windowinterface.UNIT_PXL, x,y))
		self.displist = self.root.window.newdisplaylist((227,223,145), windowinterface.UNIT_PXL)
		for i in self.widgets:
			i.displist = self.displist
			i.redraw()
		self.displist.render()

	def notify_moveto(self, coords):
		# This is the upcall from widgets when they are moved.
		# set the canvas size.
		x,y = self.canvassize
		l,t,r,b = coords
		if r > x:
			x = r
		if b > y:
			y = b
		self.canvassize = x,y

class GeoClientWidget(Widget):
	# Common routines for all widgets.
	def moveto(self, coords):
		Widget.moveto(self, coords)
		self.parent.notify_moveto(coords)

class Image(GeoClientWidget):
	def redraw(self):
		print "TODO"

class Line(GeoClientWidget):
	def redraw(self):
		self.displist.drawline(self.get_box())

class HLine3D(GeoClientWidget):
	pass;

class Box(GeoClientWidget):
	color = (0,0,0)
	def redraw(self):
		self.displist.fgcolor(self.color)
		self.displist.drawbox(self.get_box())

	def set_color(self, color):
		self.color = color

class FBox(GeoClientWidget):
	color = (0,0,0)
	def redraw(self):
		self.displist.drawfbox(self.color, self.get_box())

	def set_color(self, color):
		self.color = color
#FBox=Box # Use this for debugging.

class Marker(GeoClientWidget):
	pass;

class Text(GeoClientWidget):
	text = "No text set."
	def set_text(self, text):
		self.text = text
	# fonts??
	def redraw(self):
		l,t,w,h = self.get_box()
		self.displist.usefont(f_channel)
		self.displist.fgcolor((0,0,0))
		self.displist.centerstring(l,t,l+w,t+h,self.text)

class FPolygon(GeoClientWidget):
	pass;

#class Box3D(GeoClientWidget):
#	pass;
Box3D=Box

class Diamond(GeoClientWidget):
	pass;

class FDiamond(GeoClientWidget):
	pass;

class Diamond3D(GeoClientWidget):
	pass;

class Arrow(GeoClientWidget):
	pass;


