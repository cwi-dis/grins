__version__ = "$Id$"

from Channel import *
from windowinterface import UNIT_SCREEN

class BrushChannel(ChannelWindow):
    node_attrs = ChannelWindow.node_attrs + ['fgcolor']

    def do_arm(self, node, same=0):
        if same and self.armed_display:
            return 1
        color = MMAttrdefs.getattr(node, 'fgcolor')
        self.armed_display.drawfbox(color, (0,0,1,1), units = UNIT_SCREEN)
        return 1

    def do_updateattr(self, node, name, value):
        if name != 'fgcolor':
            return
        d = self.played_display.clone()
        d.drawfbox(value, (0,0,1,1), units = UNIT_SCREEN)
        d.render()
        self.played_display.close()
        self.played_display = d
