__version__ = "$Id$"

# Will develop a display list (equivalent) that is composed of
# aggregated editable geometric primitives rather than fixed
# primitives.

# Note: this is now badly designed. The optimisation self.change_objects breaks the working of
# this class by appending directly to the underlying display list without regard for the
# z-order of the widgets.

import windowinterface, WMEVENTS
from AppDefaults import *

from Widgets import *

class GeoWidget(Widget):
    # This is the new "display list", and can have the same potential functionality.
    # The motivation behind creating this class is to create a "display list" which
    # contains editable elements.
    # Currently, it requires the existing display list implementation to run.

    def __init__(self, mother):
        # Root is the root window.
        Widget.__init__(self, mother)
        self.canvassize = 800, 200
        self.change_objects = []
        self.need_redraw = 0
        self.widgets = []
        self.displist = None

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

        # << This is a hack:
        bob = len(self.change_objects)
        if not self.need_redraw and self.displist and bob != 0 and bob < 100:
            #print "DEBUG: geom using hack."
            self.displist, displist = self.displist.clone(), self.displist
            for i in self.change_objects:
                i.displist = self.displist
                i.redraw()
            self.displist.render()
            displist.close()
            self.change_objects = []
            return
        # >> end of hack.

        #print "DEBUG: geom completely redrawing."
        x,y = self.canvassize
        self.mother.window.setcanvassize((windowinterface.UNIT_PXL, x,y))
        # Fixing the color of the background will break things. Sorry, but I'm lazy (-anonymous developer :-).
        self.displist = self.mother.window.newdisplaylist(settings.get('temporal_backgroundcolor'), windowinterface.UNIT_PXL)
        for i in self.widgets:
            i.displist = self.displist
            i.redraw()
        self.displist.render()
        self.need_redraw = 0
        self.change_objects = []

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
        self.need_redraw = 1

    def getgeometry(self):
        return self.mother.window.getgeometry()

    def redraw_all(self):
        self.need_redraw = 1

class GeoClientWidget(Widget):
    # Common routines for all widgets.
    def moveto(self, coords):
        Widget.moveto(self, coords)
        self.parent.notify_moveto(coords)
    def need_redraw(self):
        self.parent.change_objects.append(self)

class Image(GeoClientWidget):
    filename = None
    def redraw(self):
        if self.filename:
            self.displist.display_image_from_file(
                    self.filename,
                    center = 1,
                    coordinates = self.get_box(),
                    fit = 'meetBest'
                    )
        else:
            self.displist.drawfbox((128,128,128), self.get_box())
    def set_file(self, filename):
        self.filename = filename

class Line(GeoClientWidget):
    color=(0,0,0)
    def redraw(self):
        x,y,w,h = self.get_box()
        self.displist.drawline(self.color, [(x,y), (x+w, y+h)])

class HLine3D(GeoClientWidget):
    # Horizontal lines only.
    color = (0,0,0)
    color2 = (128,128,128)
    def set_color(self, color1, color2):
        self.color = color1
        self.color2 = color2
    def redraw(self):
        x,y,w,h = self.get_box()
        self.displist.draw3dhline(self.color, self.color2, x, x+w, y)

class Box(GeoClientWidget):
    color = (0,0,0)
    def redraw(self):
        self.displist.fgcolor(self.color)
        self.displist.drawbox(self.get_box())

    def set_color(self, color):
        if color != self.color:
            self.color = color
            self.parent.change_objects.append(self)

class FBox(GeoClientWidget):
    color = (0,0,0)
    def redraw(self):
        self.displist.drawfbox(self.color, self.get_box())

    def set_color(self, color):
        if color != self.color:
            self.color = color
            self.parent.change_objects.append(self)
#FBox=Box # Use this for debugging.

class Marker(GeoClientWidget):
    #print "TODO"
    pass

class Text(GeoClientWidget):
    # TODO: support different fonts and stuff.
    def __init__(self, mother):
        GeoClientWidget.__init__(self, mother)
        self.textalign = 'c'
        self.text = "--"
    def set_text(self, text):
        if text != self.text:
            self.text = text
            self.parent.change_objects.append(self)
    # fonts??
    def redraw(self):
        l,t,w,h = self.get_box()
        self.displist.usefont(f_channel)
        self.displist.fgcolor((0,0,0))
        if self.textalign == 'c':
            self.displist.centerstring(l,t,l+w,t+h,self.text)
        elif self.textalign == 'l':
            self.displist.setpos(l, t+h)
            self.displist.writestr(self.text)

    def align(self, bob):
        if bob != self.textalign:
            self.textalign = bob
            self.parent.change_objects.append(self)

    def get_height(self):
        return 12;

class FPolygon(GeoClientWidget):
    pass;

class Box3D(GeoClientWidget):
    def set_color(self, color1, color2, color3, color4):
        self.color1 = color1
        self.color2 = color2
        self.color3 = color3
        self.color4 = color4
    def redraw(self):
        self.displist.draw3dbox(self.color1, self.color2, self.color3, self.color4, self.get_box())

class Diamond(GeoClientWidget):
    pass;

class FDiamond(GeoClientWidget):
    pass;

class Diamond3D(GeoClientWidget):
    pass;

class Arrow(GeoClientWidget):
    def redraw(self):
        x,y,w,h = self.get_box()
        self.displist.drawarrow(self.color, (x,y), (x+w,y+h))
