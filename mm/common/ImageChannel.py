__version__ = "$Id$"

from Channel import *
from MMExc import *                     # exceptions
import windowinterface                  # for windowinterface.error
from MMurl import urlretrieve


class ImageChannel(ChannelWindow):
    node_attrs = ChannelWindow.node_attrs + ['project_quality']
    chan_attrs = ChannelWindow.chan_attrs + ['fit']

    def __init__(self, name, attrdict, scheduler, ui):
        ChannelWindow.__init__(self, name, attrdict, scheduler, ui)

    def do_arm(self, node, same=0):
        if same and self.armed_display:
            return 1
        if node.type != 'ext':
            self.errormsg(node, 'Node must be external.')
            return 1
        f = self.getfileurl(node)
        if not f:
            self.errormsg(node, 'No URL set on node.')
            return 1
        try:
            f = urlretrieve(f)[0]
        except IOError, arg:
            if type(arg) is type(self):
                arg = arg.strerror
            self.errormsg(node, 'Cannot open: %s\n\n%s.' % (f, arg))
            return 1
        # remember coordinates for anchor editing (and only for that!)
        fit = MMAttrdefs.getattr(node, 'fit')

        try:
            imbox = self.armed_display.display_image_from_file(
                            f, fit = fit, coordinates=self.getmediageom(node), units = windowinterface.UNIT_PXL, center = 0)
            self.armed_display.knowcmd('image')
        except (windowinterface.error, IOError), msg:
            if type(msg) is type(self):
                msg = msg.strerror
            elif type(msg) is type(()):
                msg = msg[1]
            self.errormsg(node, 'Cannot display: %s\n\n%s.' %(f, msg))
            return 1

        self.setArmBox(imbox)

        return 1

    def defanchor(self, node, anchor, cb):
        if not self.window:
            windowinterface.showmessage('The window is not visible.\nPlease make it visible and try again.')
            return
        if self._armstate != AIDLE:
            raise error, 'Arm state must be idle when defining an anchor'
        if self._playstate != PIDLE:
            raise error, 'Play state must be idle when defining an anchor'
        self._anchor_context = AnchorContext()
        self.startcontext(self._anchor_context)
        save_syncarm = self.syncarm
        self.syncarm = 1
        if hasattr(self, '_arm_imbox'):
            del self._arm_imbox
        self.arm(node)
        if not hasattr(self, '_arm_imbox'):
            self.syncarm = save_syncarm
            self.stopcontext(self._anchor_context, 0)
            windowinterface.showmessage("Can't display image, so can't edit anchors", parent = self.window)
            return
        save_syncplay = self.syncplay
        self.syncplay = 1
        self.play(node, 0)
        self._playstate = PLAYED
        self.syncarm = save_syncarm
        self.syncplay = save_syncplay
        self._anchor = anchor
        box = anchor.aargs
        self._anchor_cb = cb
        msg = 'Draw anchor in ' + self._name + '.'
        if box == []:
            self.window.create_box(msg, self._box_cb)
        else:
            f = self.getfileurl(node)
            try:
                f = urlretrieve(f)[0]
            except IOError:
                pass

            # convert coordinates to relative image size
            box = self.convertCoordinatesToRelatives(f, box)
            # convert coordinates from relative image to relative window size
            windowCoordinates = self.convertCoordinatesToWindow(box)

            shapeType = box[0]
            # for instance we manage only the rect shape
            if shapeType == 'rect':
                x = windowCoordinates[1]
                y = windowCoordinates[2]
                w = windowCoordinates[3] - x
                h = windowCoordinates[4] - y
                self.window.create_box(msg, self._box_cb, (x, y, w, h))
            else:
                print 'Shape type not supported yet for editing'

    def _box_cb(self, *box):
        self.stopcontext(self._anchor_context, 0)
        # for now, keep the compatibility with old structure
        if len(box) == 4:
            x, y, w, h = box
            winCoordinates = ['rect', x ,y ,x+w, y+h]

            # convert coordinates from window size to image size.
            relativeCoordinates = self.convertShapeRelWindowToRelImage(winCoordinates)
            from MMNode import MMAnchor
            arg = MMAnchor(self._anchor.aid, self._anchor.atype, relativeCoordinates, self._anchor.atimes, self._anchor.aaccess)
        else:
            arg = self._anchor
        apply(self._anchor_cb, (arg,))
        del self._anchor_cb
        del self._anchor_context
        del self._anchor

    def do_updateattr(self, node, name, value):
        self.do_update(node, animated=1)
        if name == 'file':
            cmd = self.update_display.getcmd('image')
            if cmd and self.played_display:
                self.played_display.updatecmd('image',cmd)
                self.played_display.render()

    # this method is a variation of do_arm method
    # most part of the do_arm can be reproduced by setting: animated=0
    # as such can be factored out if it survives the evolution
    def do_update(self, node, animated=1):
        if not self.window: return
        if self.update_display:
            self.update_display.close()
        bgcolor = self.getbgcolor(node, animated)
        self.update_display = self.window.newdisplaylist(bgcolor)

        f = self.getfileurl(node, animated)
        if not f: return

        if not f:
            self.errormsg(node, 'No URL set on node.')
            return 1
        try:
            f = urlretrieve(f)[0]
        except IOError, arg:
            if type(arg) is type(self):
                arg = arg.strerror
            self.errormsg(node, 'Cannot open: %s\n\n%s.' % (f, arg))
            return 1
        fit = MMAttrdefs.getattr(node, 'fit', animated)
        try:
            self._update_imbox = self.update_display.display_image_from_file(f, fit = fit,
                    coordinates=self.getmediageom(node), units = windowinterface.UNIT_PXL)
            self.update_display.knowcmd('image')
        except (windowinterface.error, IOError), msg:
            if type(msg) is type(self):
                msg = msg.strerror
            elif type(msg) is type(()):
                msg = msg[1]
            self.errormsg(node, 'Cannot display: %s\n\n%s.' %(f, msg))
            return 1
        self.update_display.fgcolor(self.getbgcolor(node, animated))
