__version__ = "$Id$"

# HierarchyView dialog - Version for standard windowinterface
# XXXX Note: the separation isn't correct: there are still things in
# HierarchyView that really belong here...

# ' to un-confuse Emacs :-)

from ViewDialog import ViewDialog
import windowinterface
import WMEVENTS
from usercmd import *
from flags import *

class HierarchyViewDialog(ViewDialog):
    adornments = {
            'shortcuts': {'d': DELETE,
                          'x': CUT,
                          'c': COPY,
                          'p': PLAYNODE,
                          'G': PLAYFROM,
                          'a': ATTRIBUTES,
                          'e': CONTENT,
                          'T': CREATEANCHOR,
                          'L': FINISH_LINK,
                          },
            'menubar': [
                    (FLAG_ALL, 'Close', [
                            (FLAG_ALL, 'Close', CLOSE_WINDOW),
                            ]),
                    (FLAG_ALL, 'Edit', [
                            (FLAG_ALL, 'Cut', CUT),
                            (FLAG_ALL, 'Copy', COPY),
                            (FLAG_BOSTON, 'Convert to SMIL 2.0', RPCONVERT),
                            (FLAG_PRO, 'Convert to RealPix', CONVERTRP),
                            (FLAG_ALL, 'Paste', [
                                    (FLAG_ALL, 'Before', PASTE_BEFORE),
                                    (FLAG_ALL, 'After', PASTE_AFTER),
                                    (FLAG_ALL, 'Within', PASTE_UNDER),
                                    ]),
                            (FLAG_ALL, 'Delete', DELETE),
                            (FLAG_ALL, None),
                            (FLAG_ALL, 'New Node', [
                                    (FLAG_ALL, 'Before', NEW_BEFORE),
                                    (FLAG_ALL, 'After', NEW_AFTER),
                                    (FLAG_ALL, 'Within', NEW_UNDER),
                                    (FLAG_ALL, None),
                                    (FLAG_ALL, 'Seq Parent', NEW_SEQ),
                                    (FLAG_ALL, 'Par Parent', NEW_PAR),
                                    (FLAG_ALL, 'Switch Parent', NEW_SWITCH),
                                    ]),
                            (FLAG_ALL, None),
                            (FLAG_ALL, 'Properties...', ATTRIBUTES),
                            (FLAG_ALL, 'Edit Content...', CONTENT),
                            ]),
                    (FLAG_ALL, 'Preview', [
                            (FLAG_ALL, 'Preview Node', PLAYNODE),
                            (FLAG_ALL, 'Preview from Node', PLAYFROM),
                            ]),
                    (FLAG_ALL, 'Linking', [
                            (FLAG_ALL, 'Create Simple Anchor', CREATEANCHOR),
                            (FLAG_ALL, 'Finish Hyperlink to Selection', FINISH_LINK),
                            ]),
                    (FLAG_ALL, 'View', [
                            (FLAG_ALL, 'Expand/Collapse', EXPAND),
                            (FLAG_ALL, 'Expand All', EXPANDALL),
                            (FLAG_ALL, 'Collapse All', COLLAPSEALL),
                            (FLAG_ALL, None),
                            (FLAG_ALL, 'Image Thumbnails', THUMBNAIL, 't'),
                            (FLAG_ALL, 'Show Playable', PLAYABLE, 't'),
                            (FLAG_ALL, 'Check Bandwidth Usage', COMPUTE_BANDWIDTH),
                            (FLAG_ALL, 'Show Time in Structure', [
                                    (FLAG_ALL, 'Whole Document, Adaptive', TIMESCALE, 't'),
                                    (FLAG_ALL, 'Selection Only, Adaptive', LOCALTIMESCALE, 't'),
                                    (FLAG_ALL, 'Selection Only, Fixed', CORRECTLOCALTIMESCALE, 't'),
                                    (FLAG_ALL, 'Zoom in timeline', ZOOMIN),
                                    (FLAG_ALL, 'Zoom out timeline', ZOOMOUT),
                                    (FLAG_ALL, 'Reset timeline zoom', ZOOMRESET),
                                    ]),
                            ]),
                    (FLAG_ALL, 'Help', [
                            (FLAG_ALL, 'Help...', HELP),
                            ]),
                    ],
            'toolbar': None, # no images yet...
            'close': [ CLOSE_WINDOW, ],
            }

    interior_popupmenu = (
            (FLAG_ALL, 'New Node Before', NEW_BEFORE),
            (FLAG_ALL, 'New Node After', NEW_AFTER),
            (FLAG_ALL, 'New Node Within', NEW_UNDER),
            (FLAG_ALL, None),
            (FLAG_PRO, 'Convert to RealPix', CONVERTRP),
            (FLAG_PRO, None),
            (FLAG_ALL, 'Cut', CUT),
            (FLAG_ALL, 'Copy', COPY),
            (FLAG_ALL, 'Delete', DELETE),
            (FLAG_ALL, None),
            (FLAG_ALL, 'Paste Before', PASTE_BEFORE),
            (FLAG_ALL, 'Paste After', PASTE_AFTER),
            (FLAG_ALL, 'Paste Within', PASTE_UNDER),
            (FLAG_ALL, None),
            (FLAG_ALL, 'Preview Node', PLAYNODE),
            (FLAG_ALL, 'Preview from Node', PLAYFROM),
            (FLAG_ALL, None),
            (FLAG_ALL, 'Expand/Collapse', EXPAND),
            (FLAG_ALL, 'Expand All', EXPANDALL),
            (FLAG_ALL, 'Collapse All', COLLAPSEALL),
            (FLAG_ALL, None),
            (FLAG_ALL, 'Create Simple Anchor', CREATEANCHOR),
            (FLAG_ALL, 'Finish Hyperlink', FINISH_LINK),
            (FLAG_ALL, None),
            (FLAG_ALL, 'Properties...', ATTRIBUTES),
            )

    leaf_popupmenu = (
            (FLAG_ALL, 'New Node Before', NEW_BEFORE),
            (FLAG_ALL, 'New Node After', NEW_AFTER),
            (FLAG_BOSTON, None),
            (FLAG_BOSTON, 'Convert to SMIL 2.0', RPCONVERT),
            (FLAG_ALL, None),
            (FLAG_ALL, 'Cut', CUT),
            (FLAG_ALL, 'Copy', COPY),
            (FLAG_ALL, 'Delete', DELETE),
            (FLAG_ALL, None),
            (FLAG_ALL, 'Paste Before', PASTE_BEFORE),
            (FLAG_ALL, 'Paste After', PASTE_AFTER),
            (FLAG_ALL, None),
            (FLAG_ALL, 'Preview Node', PLAYNODE),
            (FLAG_ALL, 'Preview from Node', PLAYFROM),
            (FLAG_ALL, None),
            (FLAG_ALL, 'Create Simple Anchor', CREATEANCHOR),
            (FLAG_ALL, 'Finish Hyperlink', FINISH_LINK),
            (FLAG_ALL, None),
            (FLAG_ALL, 'Properties...', ATTRIBUTES),
            (FLAG_ALL, 'Edit Content...', CONTENT),
            )

    slide_popupmenu = (
            (FLAG_ALL, 'New Node Before', NEW_BEFORE),
            (FLAG_ALL, 'New Node After', NEW_AFTER),
            (FLAG_ALL, None),
            (FLAG_ALL, 'Cut', CUT),
            (FLAG_ALL, 'Copy', COPY),
            (FLAG_ALL, 'Delete', DELETE),
            (FLAG_ALL, None),
            (FLAG_ALL, 'Paste Before', PASTE_BEFORE),
            (FLAG_ALL, 'Paste After', PASTE_AFTER),
            (FLAG_ALL, None),
            (FLAG_ALL, 'Properties...', ATTRIBUTES),
            (FLAG_ALL, 'Edit Content...', CONTENT),
            )

    transition_popupmenu = (
            (FLAG_ALL, 'Transition', TRANSITION),
            )

    event_popupmenu_source = (
            (FLAG_ALL, 'Find event destination', FIND_EVENT_SOURCE),
            )

    event_popupmenu_dest = (
            (FLAG_ALL, 'Find event source', FIND_EVENT_SOURCE),
            (FLAG_ALL, 'Properties...', ATTRIBUTES),
            )

    multi_popupmenu = (
            (FLAG_ALL, 'Cut', CUT),
            (FLAG_ALL, 'Copy', COPY),
            (FLAG_ALL, None,),
            (FLAG_ALL, 'Delete', DELETE),
            (FLAG_ALL, None,),
            (FLAG_ALL, 'Event source', CREATE_EVENT_SOURCE),
            (FLAG_ALL, None,),
            (FLAG_ALL, 'Properties...', ATTRIBUTES),
            )

    def __init__(self):
        ViewDialog.__init__(self, 'hview_')

    # transf from HierarchyView
    def helpcall(self):
        import Help
        Help.givehelp('Hierarchy')

    def show(self):
        if self.is_showing():
            self.window.pop(poptop = 1)
            return
        import settings
        title = 'Structure View (%s)' % self.toplevel.basename
        self.load_geometry()
        if self.last_geometry:
            x, y, w, h = self.last_geometry
        else:
            x, y, w, h = -1, -1, -1, -1
        if w < 0: w = 300
        if h < 0: h = 300
        self.adornments['flags'] = curflags()
        self.window = windowinterface.newcmwindow(x, y, w, h, title,
                        pixmap = 1, units = windowinterface.UNIT_PXL,
                        adornments = self.adornments,
                        canvassize = (w, h),
                        commandlist = self.commands)
        self.window.set_toggle(THUMBNAIL, self.thumbnails)
        self.window.register(WMEVENTS.Mouse0Press, self.mouse, None)
        self.window.register(WMEVENTS.Mouse0Release, self.mouse0release, None)
        self.window.register(WMEVENTS.ResizeWindow, self.redraw, None)
        self.window.register(WMEVENTS.DropFile, self.dropfile, None)
        self.window.register(WMEVENTS.DropURL, self.dropfile, None)

    def hide(self, *rest):
        self.save_geometry()
        self.window.close()
        self.window = None
        self.displist = None
        self.new_displist = None

    def fixtitle(self):
        if self.is_showing():
            title = 'Structure View (' + self.toplevel.basename + ')'
            self.window.settitle(title)

    def settoggle(self, command, onoff):
        self.window.set_toggle(command, onoff)

    def setcommands(self, commandlist):
        self.window.set_commandlist(commandlist)
        self.window.set_dynamiclist(TRANSITION, self.translist or [])

    def setpopup(self, template):
        self.window.setpopupmenu(template, curflags())

    def setstate(self):
        w = self.window
        w.set_toggle(THUMBNAIL, self.thumbnails)
        w.set_toggle(PLAYABLE, self.showplayability)

    def getparentwindow(self):
        # Used by machine-independent code to pass as parent
        # parameter to dialogs
        return self.window

    # this method is called when the mouse is dragged
    # begin != 0 means that you start the drag, otherwise, assume that the drag is finished
    # on some plateform (at least Windows), it allows to tell to the system to continue to
    # send the event even if the mouse go outside the window (during dragging)
    def mousedrag(self, begin):
        pass
