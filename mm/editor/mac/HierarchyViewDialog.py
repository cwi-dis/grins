__version__ = "$Id$"

# HierarchyView dialog - Mac version
# XXXX Note: the separation isn't correct: there are still things in HierarchyView
# that really belong here...

from ViewDialog import ViewDialog
from usercmd import *
import windowinterface
import WMEVENTS
import MenuTemplate

class HierarchyViewDialog(ViewDialog):

    interior_popupmenu = MenuTemplate.POPUP_HVIEW_STRUCTURE
    leaf_popupmenu = MenuTemplate.POPUP_HVIEW_LEAF
    slide_popupmenu = MenuTemplate.POPUP_HVIEW_SLIDE
    transition_popupmenu = MenuTemplate.POPUP_HVIEW_TRANS
    event_popupmenu_source = MenuTemplate.POPUP_EVENT_SOURCE
    event_popupmenu_dest = MenuTemplate.POPUP_EVENT_DEST
    multi_popupmenu = MenuTemplate.POPUP_MULTI # For multiple selections.

    def __init__(self):
        ViewDialog.__init__(self, 'hview_')

    def show(self):
        if self.is_showing():
            self.window.pop(poptop=1)
            return
        title = 'Structure View (' + self.toplevel.basename + ')'
        self.load_geometry()
        if self.last_geometry:
            x, y, w, h = self.last_geometry
        else:
            x, y, w, h = -1, -1, -1, -1
        adornments = {'doubleclick': ATTRIBUTES}
        self.window = windowinterface.newcmwindow(x, y, w, h, title, pixmap=1,
                 units=windowinterface.UNIT_PXL,
                commandlist=self.commands, canvassize = (w, h), adornments=adornments)
        self.window.set_toggle(THUMBNAIL, self.thumbnails)
        self.window.register(WMEVENTS.Mouse0Release, self.mouse0release, None)
        self.window.register(WMEVENTS.Mouse0Press, self.mouse, None)
        self.window.register(WMEVENTS.ResizeWindow, self.redraw, None)
        self.window.register(WMEVENTS.WindowExit, self.hide, None)
        self.window.register(WMEVENTS.DropFile, self.dropfile, None)
        self.window.register(WMEVENTS.DropURL, self.dropfile, None)
        self.window.register(WMEVENTS.DragFile, self.dragfile, None)

    def hide(self, *rest):
        self.save_geometry()
        self.window.close()
        self.window = None
        self.displist = None
        self.new_displist = None

    def getparentwindow(self):
        return None

    def fixtitle(self):
        if self.is_showing():
            title = 'Structure View (' + self.toplevel.basename + ')'
            self.window.settitle(title)

    def settoggle(self, command, onoff):
        self.window.set_toggle(command, onoff)

    def setcommands(self, commandlist):
        self.window.set_commandlist(commandlist)

    def setpopup(self, template):
        self.window.setpopupmenu(template)

    def setstate(self):
        w = self.window
        w.set_toggle(THUMBNAIL, self.thumbnails)
        w.set_toggle(PLAYABLE, self.showplayability)
        w.set_toggle(TIMESCALE, self.root.showtime == 'focus')
        if self.get_selected_widget() is None:
            w.set_toggle(LOCALTIMESCALE, 0)
            w.set_toggle(CORRECTLOCALTIMESCALE, 0)
        else:
            n = self.get_selected_node()
            w.set_toggle(LOCALTIMESCALE, n.showtime == 'focus')
            w.set_toggle(CORRECTLOCALTIMESCALE, n.showtime in ('cfocus', 'bwstrip'))
        w.set_toggle(TOGGLE_BWSTRIP, self.root.showtime == 'bwstrip')

    def helpcall(self):
        import Help
        Help.givehelp('Hierarchy')

    # this method is called when the mouse is dragged
    # begin != 0 means that you start the drag, otherwise, assume that the drag is finished
    # on some plateform (at least Windows), it allows to tell to the system to continue to
    # send the event even if the mouse go outside the window (during dragging)
    def mousedrag(self, begin):
        pass
