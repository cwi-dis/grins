__version__ = "$Id$"

from Channel import *
import features
import settings

#
# This rather boring channel is used for laying-out other channels
#
class LayoutChannel(ChannelWindow):

    def __init__(self, name, attrdict, scheduler, ui):
        ChannelWindow.__init__(self, name, attrdict, scheduler, ui)
        self.is_layout_channel = 1
        self._activeMediaNumber = 0
        self.__activeVisibleChannelDict = {}

    def do_arm(self, node, same=0):
        print 'LayoutChannel: cannot play nodes on a layout channel'
        return 1

    def getMMChannel(self):
        # todo: to optimize
        return self._player.context.channeldict.get(self._name)

    def create_window(self, pchan, pgeom, units = None):
        mmchan = self.getMMChannel()

        transparent = mmchan.GetInherAttrDef('transparent', 0)
        if transparent:
            bgcolor = None
        else:
            bgcolor = mmchan.GetInherAttrDef('bgcolor', settings.get('bgcolor'))

        self._curvals['transparent'] = (transparent, 0)
        self._curvals['bgcolor'] = (bgcolor, settings.get('bgcolor'))

        if pchan:
            z = self._attrdict.get('z', 0)
            self._curvals['z'] = (z, 0)
            if self.want_default_colormap:
                self.window = pchan.window.newcmwindow(pgeom,
                                transparent = transparent,
                                z = z,
                                units = units,
                                bgcolor = bgcolor)
            else:
                self.window = pchan.window.newwindow(pgeom,
                                transparent = transparent,
                                z = z,
                                units = units,
                                bgcolor = bgcolor)
        else:
            # no basewindow, create a top-level window
            adornments = self._player.get_adornments(self)
            if self._player._exporter:
                adornments['exporting'] = 1
            units = self._attrdict.get('units',
                                       windowinterface.UNIT_MM)

            width, height = self.cssResolver.getPxGeom(self._attrdict._cssId)
            self._wingeom = width, height

            units = windowinterface.UNIT_PXL

            self._curvals['winsize'] = ((width, height), (50,50))
            x, y = self._attrdict.get('winpos', (None, None))
            title = mmchan.GetAttrDef('title', self._name)
            if features.editor:
                title = 'Previewer: %s' % title
            if self.want_default_colormap:
                self.window = windowinterface.newcmwindow(x, y,
                        width, height, title,
                        units = units, adornments = adornments,
                        commandlist = self.commandlist,
                        bgcolor = bgcolor)
            else:
                self.window = windowinterface.newwindow(x, y,
                        width, height, title,
                        units = units, adornments = adornments,
                        commandlist = self.commandlist,
                        bgcolor = bgcolor)
            if self._player._exporter:
                self._player._exporter.createWriter(self.window)
            self.event((self._attrdict, 'topLayoutOpenEvent'))
        if self._attrdict.has_key('fgcolor'):
            self.window.fgcolor(self._attrdict['fgcolor'])
        self._curvals['fgcolor'] = self._attrdict.get('fgcolor'), None
        self.window.register(WMEVENTS.ResizeWindow, self.resize, None)
        self.window.register(WMEVENTS.Mouse0Press, self.mousepress, None)
        self.window.register(WMEVENTS.Mouse0Release, self.mouserelease,
                             None)
        self.window.register(WMEVENTS.KeyboardInput, self.keyinput, None)

    # notes:
    # unlike base ChannelWindow class, we can have pchan = None. It means that
    # it's the main window. In this case, we don't need to determinate self._wingeom because
    # it not used in create_window. It's not a good design, but for now it works.
    def do_show(self, pchan):
        if debug:
            print 'ChannelLayout.do_show('+`self`+')'

        if pchan:
            # parent is not None, so it's not the main window

            self._wingeom = pgeom = self.cssResolver.getPxGeom(self._attrdict._cssId)
            self._curvals['base_winoff'] = pgeom, None

        units = windowinterface.UNIT_PXL
        self.create_window(pchan, self._wingeom, units)

        return 1

    def do_hide(self):
        ChannelWindow.do_hide(self)

    def play(self, node, curtime):
        print "can't play LayoutChannel"

    # A channel pass active (when one more media play inside).
    # We have to update the visibility of all channels
    def childToActiveState(self):
        ch = self
        while ch != None:
            ch._activeMediaNumber = ch._activeMediaNumber+1
            ch.show(1)
            ch = ch._get_parent_channel()

    # A channel pass inactive (when one more media play inside).
    # We have to update the visibility of all channels
    def childToInactiveState(self):
        ch = self
        while ch != None:
            ch._activeMediaNumber = ch._activeMediaNumber-1
            if ch._activeMediaNumber <= 0:
                ch.hide(0)
            ch = ch._get_parent_channel()


    # specific methods for viewport (root channel)
    #
    #

    def addActiveVisibleChannel(self, channel, node):
        self.__activeVisibleChannelDict[channel] = node

    def removeActiveVisibleChannel(self, channel):
        del self.__activeVisibleChannelDict[channel]

    # return the list of the renderer which overlaps 'rendererToCheck'
    def getOverlapRendererList(self, rendererToCheck, nodeToCheck):
        overLapList = []
        xR, yR, wR, hR = rendererToCheck.getabswingeom()

        for renderer,node in self.__activeVisibleChannelDict.items():
            # determinate absolute pixel positioning relative to the viewport
            x, y, w, h = renderer.getabswingeom()

            # to do: optimized
            if x < xR+wR and xR < x+w and y < yR+hR and yR < y+h:
                # overlap
                overLapList.append((renderer, node))

        return overLapList
