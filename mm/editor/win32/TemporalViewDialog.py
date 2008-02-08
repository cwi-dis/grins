__version__ = "$Id$"

from ViewDialog import ViewDialog
import WMEVENTS, windowinterface
import MMAttrdefs
from usercmd import *
from MenuTemplate import *

class TemporalViewDialog(ViewDialog):
    adornments = {}

    def __init__(self):
        ViewDialog.__init__(self, 'tview_')

        # Sjoerd won't mind if I borrow these.
        # Node popup menus.
        self.menu_no_nodes = POPUP_HVIEW_NONE
        self.menu_interior_nodes = POPUP_HVIEW_STRUCTURE
        self.menu_leaf_nodes = POPUP_HVIEW_LEAF
        self.menu_multiple_nodes = None
        # Channel popup menus.
        self.menu_no_channel = POPUP_CVIEW_NONE
        self.menu_viewport = POPUP_CVIEW_CHANNEL
        self.menu_channel = POPUP_CVIEW_CHANNEL
        self.menu_multiple_channels = None

    def show(self):
        if self.is_showing() and self.window:
            self.window.pop(poptop=1)
            return
        title = 'Temporal View (' + self.toplevel.basename + ')'
        self.load_geometry()
        x,y,w,h = self.last_geometry
        toplevel_window = self.toplevel.window
        self.window = toplevel_window.newview(x,y,w,h,title,
                                              adornments = self.adornments,
                                              canvassize = (w,h),
                                              commandlist = self.commands,
                                              strid='tview_' # I don't understand this one -mjvdg
                                              )
        self._reg_events()

    def hide(self, *rest):
        self.save_geometry()
        self.window.close()
        self.window = None

    def _reg_events(self):
        self.window.register(WMEVENTS.Mouse0Press, self.ev_mouse0press, None)
#               self.window.register(WMEVENTS.Mouse0Release, self.ev_mouse0release, None)
        self.window.register(WMEVENTS.Mouse2Press, self.ev_mouse2press, None)
#               self.window.register(WMEVENTS.Mouse2Release, self.ev_mouse2release, None)

##         self.window.register(WMEVENTS.WindowExit, self.ev_exit, None)

        self.window.register(WMEVENTS.PasteFile, self.ev_pastefile, None)
        self.window.register(WMEVENTS.DragFile, self.ev_dragfile, None)
        self.window.register(WMEVENTS.DropFile, self.ev_dropfile, None)
        self.window.register(WMEVENTS.DragNode, self.ev_dragnode, None)
        self.window.register(WMEVENTS.DropNode, self.ev_dropnode, None)

    def setcommands(self, commandlist):
        self.window.set_commandlist(commandlist)

    def setpopup(self, template):
        self.window.setpopupmenu(template)
