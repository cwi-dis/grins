__version__ = "$Id$"

# Will develop a display list (equivalent) that is composed of
# aggregated editable geometric primitives rather than fixed
# primitives.

import windowinterface, WMEVENTS


from Widgets import *

class GeoWidget(Widget):
	# This is the new "display list", and can have the same potential functionality.
	# The motivation behind creating this class is to create a "display list" which
	# contains editable elements.
	# Currently, it requires the existing display list implementation to run.

	def __init__(self, root):
		# Root is the root window.
		Widget.__init__(self, root)
		self.widgets = []

	def AddWidget(self, widget):
		assert isinstance(widget, Widget)
		self.widgets.append(widget)
		widget.parent = self

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
		self.displist = self.root.newdisplaylist((50,50,50), windowinterface.UNIT_PXL)
		for i in self.widgets:
			i.displist = self.displist
			i.redraw()
		self.displist.render()



class Image(Widget):
	def redraw(self):
		print "TODO"

class Line(Widget):
	def redraw(self):
		self.displist.drawline(self.get_box())

class HLine3D(Widget):
	pass;

class Box(Widget):
	def redraw(self):
		self.displist.drawbox(self.get_box())

#class FBox(Widget):
#	pass;
FBox=Box # TODO

class Marker(Widget):
	pass;

#class Text(Widget):
#	pass;
Text=Box

class FPolygon(Widget):
	pass;

#class Box3D(Widget):
#	pass;
Box3D=Box

class Diamond(Widget):
	pass;

class FDiamond(Widget):
	pass;

class Diamond3D(Widget):
	pass;

class Arrow(Widget):
	pass;


