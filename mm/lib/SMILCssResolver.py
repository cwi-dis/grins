__version__ = "$Id$"

def convertToPx(value, containersize):
    if type(value) == type(0):
        return value
    elif type(value) == type(0.0):
        return int(value*containersize)
    else:
        return None

class SMILCssResolver:
    def __init__(self, documentContext):
        self.rootNode = None
        self.nodeGeomChangedList = []
        self.rawAttributesChangedList = []
        self.documentContext = documentContext
        self.mm2css = {} # map: mmobj -> cssobj

    def newRootNode(self, mmobj=None):
        node = RootNode(self, mmobj)
        self.rootNode = node
        self.mm2css[mmobj] = node
        self.nodeGeomChangedList = []
        self.rawAttributesChangedList = []
        return node

    def updateAll(self):
        self.nodeGeomChangedList = []
        self.rawAttributesChangedList = []
        self.rootNode.updateAll()
        self._updateListeners()

    def getDocumentContext(self):
        return self.documentContext

    def setRawAttrs(self, region, attrList):
        region.setRawAttrs(attrList)

    def copyRawAttrs(self, srcNode, destNode):
        destNode.copyRawAttrs(srcNode)

    def changeRawAttr(self, node, name, value):
        self.nodeGeomChangedList = []
        self.rawAttributesChangedList = []
        node.changeRawValue(name, value)
        self._updateListeners()

    def getRawAttr(self, node, name):
        return node.getRawAttr(name)

    def getAttr(self, node, name):
        return node.getAttr(name)

    def changePxValue(self, node, name, value):
        self.nodeGeomChangedList = []
        self.rawAttributesChangedList = []
        node.changePxValue(name, value)
        self._updateListeners()

    def _updateListeners(self):
        for listener, geom in self.nodeGeomChangedList:
            listener(geom)
        for listener, attrname, value in self.rawAttributesChangedList:
            listener(attrname, value)

    def newRegion(self, mmobj=None):
        node = RegionNode(self, mmobj)
        self.mm2css[mmobj] = node
        return node

    def link(self, node, container):
        if container is None or node is None:
            # nothing to do
            return
        node.link(container)

    def unlink(self, node):
        if node is None:
            return
        node.unlink()

    def newMedia(self, defaultSizeHandler, mmobj=None):
        node = MediaNode(self, defaultSizeHandler, mmobj)
        return node

    def removeRegion(self, region, container):
        container.removeRegion(region)

    def setGeomListener(self, node, listener):
        node.setGeomListener(listener)

    def setRawPosAttrListener(self, node, listener):
        node.setRawPosAttrListener(listener)

    def removeListener(self, node, listener):
        node.removeListener(listener)

    def getPxGeom(self, node):
        return node.getPxGeom()

    def getPxAbsGeom(self, node):
        return node.getPxAbsGeom()

    def _onPxValuesChanged(self, node, geom):
        if node.pxValuesListener is not None:
            self.nodeGeomChangedList.append((node.pxValuesListener, geom))

    def _onRawValuesChanged(self, node, attrname, value):
        if node.rawValuesListener is not None:
            self.rawAttributesChangedList.append((node.rawValuesListener, attrname, value))

    def getCssObj(self, mmobj):
        return self.mm2css.get(mmobj)

# ###############################################################################
# Region hierarchy
# ###############################################################################

class Node:
    def __init__(self, context, mmobj=None):
        self.children = []
        self.container = None
        self.context = context
        self.pxValuesListener = None
        self.rawValuesListener = None
        self.mmobj = mmobj
        self.media = None

        self.left = None
        self.width = None
        self.right = None
        self.top = None
        self.height = None
        self.bottom = None

        self.pxleft = None
        self.pxwidth = None
        self.pxtop = None
        self.pxheight = None

        self.pxValuesHasChanged = 0

        self.isInit = 0
        self.isRoot = 0

        # common attributes for media and region
        self.regAlign = None
        self.regPoint = None
        self.fit = None

    def copyRawAttrs(self, srcNode):
        self.regAlign = srcNode.regAlign
        self.regPoint = srcNode.regPoint
        self.fit = srcNode.fit

    def changeRawAttr(self, name, value):
        if name in ['left', 'width', 'right', 'top', 'height', 'bottom']:
            self.changeRawValues(name, value)
        elif name in ['regAlign', 'regPoint', 'fit']:
            self.changeAlignAttr(name, value)

    def move(self, pos):
        self.left, self.top, self.width, self.height = int(pos[0]), int(pos[1]), self.pxwidth, self.pxheight
        #x, y, w, h = int(pos[0]), int(pos[1]), self.pxwidth, self.pxheight
        #self.changeRawAttr('left', x)
        #self.changeRawAttr('top', y)
        #self.changeRawAttr('width', w)
        #self.changeRawAttr('height', h)

    def link(self, container):
        # if already link, unlink before
        if self.container is not None:
            print 'SMILCssResolver: Warning: node is already linked'
            self.unlink()
        self.container = container
        container.children.append(self)
        if container is self:
            raise 'SmilCssResolver: link failed: container is child ',container

    def unlink(self):
        self.isInit = 0
        try:
            self.container.children.remove(self)
        except:
            pass
        self.container = None

    def setRawPosAttrListener(self, listener):
        self.rawValuesListener = listener

    def setGeomListener(self, listener):
        self.pxValuesListener = listener

    def _toUnInitState(self):
        self.isInit = 0
        for child in self.children:
            if child.isInit:
                child._toUnInitState()

    def _toInitState(self):
        if self.isInit:
            # already in init state. do nothing
            return

        if self.container is None:
            self.isInit = 1
            self.dump()
            raise 'SmilCssResolver: init failed, no root node'

        self.container._toInitState()
        self.update()
        self.isInit = 1

    def isInitState(self):
        return self.isInit

    def getPxGeom(self):
        self._toInitState()
        return self._getPxGeom()

    def getPxAbsGeom(self):
        self._toInitState()
        left, top, width, height = self._getPxGeom()
        pleft, ptop, pwidth, pheight = self.container.getPxAbsGeom()
        return pleft+left, ptop+top, width, height

    def _setRawAttr(self, name, value):
        if name == 'regPoint':
            self.regPoint = value
        elif name == 'regAlign':
            self.regAlign = value
        elif name == 'fit':
            self.fit = value

    def _getRawAttr(self, name):
        if name == 'regPoint':
            return self.regPoint
        elif name == 'regAlign':
            return self.regAlign
        elif name == 'fit':
            return self.fit

        return None

    def getAttr(self, name):
        self._toInitState()
        if name == 'regPoint':
            return self.getRegPoint()
        elif name == 'regAlign':
            return self.getRegAlign()
        elif name == 'fit':
            return self.getFit()

        return None

    def changeAlignAttr(self, name, value):
        self._toInitState()
        self.setAlignAttr(name, value)

        self.pxleft, self.pxwidth, self.pxtop, self.pxheight = self._getMediaSpaceArea()
        self._onGeomChanged()

    def getAbsPos(self):
        assert self.container, 'Node not linked'
        X, Y = self.container.getAbsPos()
        x, y = self.pxleft, self.pxtop
        return X+x, Y+y

    def getRoot(self):
        node = self
        while node.container:
            node = node.container
        return node

    def __dump(self):
        print self.__class__.__name__, self.mmobj, self.getPxGeom(), 'fit=',self.fit, 'media=',self.media
        for child in self.children:
            child.__dump()

    def dump(self):
        print '------------------------------'
        self.__dump()

class RegionNode(Node):
    def update(self):
        self.pxleft, self.pxwidth = self._resolveCSS2Rule(self.left, self.width, self.right, self.container.pxwidth)
        if self.pxwidth <= 0: self.pxwidth = 1
        self.pxtop, self.pxheight = self._resolveCSS2Rule(self.top, self.height, self.bottom, self.container.pxheight)
        if self.pxheight <= 0: self.pxheight = 1
        self._onGeomChanged()

    def updateTree(self):
        self.update()
        for child in self.children:
            child.updateTree()

    def setRawAttrs(self, attrList):
        for name, value in attrList:
            if name == 'left':
                self.left = value
            elif name == 'top':
                self.top = value
            elif name == 'width':
                if value is not None and value <= 0: value = 1
                self.width = value
            elif name == 'height':
                if value is not None and value <= 0: value = 1
                self.height = value
            elif name == 'right':
                self.right = value
            elif name =='bottom':
                self.bottom = value
            else:
                Node._setRawAttr(self, name, value)

        self._toUnInitState()

    def getRawAttr(self, name):
        if name == 'left':
            return self.left
        elif name == 'top':
            return self.top
        elif name == 'width':
            return self.width
        elif name == 'height':
            return self.height
        elif name == 'right':
            return self.right
        elif name =='bottom':
            return self.bottom
        else:
            return Node._getRawAttr(self, name)

    def copyRawAttrs(self, srcNode):
        Node.copyRawAttrs(self,srcNode)
        self.left = srcNode.left
        self.width = srcNode.width
        self.right = srcNode.right
        self.top = srcNode.top
        self.height = srcNode.height
        self.bottom = srcNode.bottom

        self._toUnInitState()

    def _resolveCSS2Rule(self, beginValue, sizeValue, endValue, containersize):
        pxbegin = None
        pxsize = None
        if beginValue is None:
            if sizeValue is None:
                if endValue is None:
                    pxbegin = 0
                    pxsize = containersize
                else:
                    pxsize = containersize-convertToPx(endValue, containersize)
                    pxbegin = 0
            elif endValue is None:
                pxbegin = 0
                pxsize = convertToPx(sizeValue,containersize)
            else:
                pxsize = convertToPx(sizeValue, containersize)
                pxbegin = containersize-pxsize-convertToPx(endValue, containersize)
        elif sizeValue is None:
            if endValue is None:
                pxbegin = convertToPx(beginValue, containersize)
                pxsize = containersize-pxbegin
            else:
                pxbegin = convertToPx(beginValue, containersize)
                pxsize = containersize-pxbegin-convertToPx(endValue, containersize)
        elif endValue is None:
            pxbegin = convertToPx(beginValue, containersize)
            pxsize = convertToPx(sizeValue, containersize)
        else:
            pxbegin = convertToPx(beginValue, containersize)
            pxsize = convertToPx(sizeValue, containersize)

        return pxbegin, pxsize

    def _updatePxOnContainerWidthChanged(self):
        self._toInitState()
        self.pxValuesHasChanged = 0

        containersize = self.container.pxwidth
        pxleft, pxwidth = self._resolveCSS2Rule(self.left, self.width, self.right, containersize)

        if pxleft != self.pxleft:
            self.pxleft = pxleft
            self._onChangePxValue('left',pxleft)
        if pxwidth != self.pxwidth:
            self._onChangePxValue('width',pxwidth)
            self.pxwidth = pxwidth

            if self.pxValuesHasChanged:
                self._onGeomChanged()

            for child in self.children:
                child._updatePxOnContainerWidthChanged()
            # the commit is already done
            return

        if self.pxValuesHasChanged:
            self._onGeomChanged()

    def _updatePxOnContainerHeightChanged(self):
        self._toInitState()
        self.pxValuesHasChanged = 0

        containersize = self.container.pxheight
        pxtop, pxheight = self._resolveCSS2Rule(self.top, self.height, self.bottom, containersize)
        if pxtop != self.pxtop:
            self.pxtop = pxtop
            self._onChangePxValue('top',pxtop)
        if pxheight != self.pxheight:
            self._onChangePxValue('height',pxheight)
            self.pxheight = pxheight

            if self.pxValuesHasChanged:
                self._onGeomChanged()

            for child in self.children:
                child._updatePxOnContainerHeightChanged()
            # the commit is already done
            return

        if self.pxValuesHasChanged:
            self._onGeomChanged()

    # change an attribute value as spefified in the document
    # determinate new pixel values (left/width/top and height)
    # determinate recursively all changement needed in children as well
    # for each pixel value changed, the callback onChangePxValue is called
    def changeRawValues(self, name, value):
        self._toInitState()
        self.pxValuesHasChanged = 0

        if name in ('left', 'width', 'right'):
            if name == 'left':
                self.left = value
            elif name == 'width':
                if value is not None and value <= 0: value = 1
                self.width = value
            elif name == 'right':
                self.right = value

            pxleft, pxwidth = self._resolveCSS2Rule(self.left, self.width, self.right, self.container.pxwidth)
            if pxleft != self.pxleft:
                self._onChangePxValue('left',pxleft)
                self.pxleft = pxleft
            if pxwidth != self.pxwidth:
                self._onChangePxValue('width',pxwidth)
                if pxwidth <= 0: pxwidth = 1
                self.pxwidth = pxwidth

                if self.pxValuesHasChanged:
                    self._onGeomChanged()

                for child in self.children:
                    child._updatePxOnContainerWidthChanged()
                # the commit is already done
                return

        elif name in ('top', 'height', 'bottom'):
            if name == 'top':
                self.top = value
            elif name == 'height':
                if value is not None and value <= 0: value = 1
                self.height = value
            elif name == 'bottom':
                self.bottom = value

            pxtop, pxheight = self._resolveCSS2Rule(self.top, self.height, self.bottom, self.container.pxheight)
            if pxtop != self.pxtop:
                self._onChangePxValue('top',pxtop)
                self.pxtop = pxtop
            if pxheight != self.pxheight:
                self._onChangePxValue('height',pxheight)
                if pxheight <= 0: pxheight = 1
                self.pxheight = pxheight

                if self.pxValuesHasChanged:
                    self._onGeomChanged()

                for child in self.children:
                    child._updatePxOnContainerHeightChanged()
                return

        if self.pxValuesHasChanged:
            self._onGeomChanged()

    def changeAlignAttr(self, name, value):
        self._toInitState()
        if name == 'regPoint':
            self.regPoint = value
        elif name == 'regAlign':
            self.regAlign = value
        elif name == 'fit':
            self.fit = value

        # for now, in this case update all children
        for child in self.children:
            child._updateRawOnContainerWidthChanged()

    def _updateRawOnContainerWidthChanged(self):
        self._toInitState()
        if type(self.left) is type(0.0):
            self.left = float(self.pxleft)/self.container.pxwidth
            self._onChangeRawValue('left',self.left)
        elif type(self.width) is type(0.0):
            self.width = float(self.pxwidth)/self.container.pxwidth
            self._onChangeRawValue('width',self.width)
            for child in self.children:
                child._updateRawOnContainerWidthChanged()
        elif type(self.right) is type(0.0):
            self.right = float(self.container.pxwidth-self.pxleft-self.pxwidth)/self.container.pxwidth
            self._onChangeRawValue('right',self.right)

    def _updateRawOnContainerHeightChanged(self):
        self._toInitState()
        if type(self.top) is type(0.0):
            self.top = float(self.pxtop)/self.container.pxheight
            self._onChangeRawValue('top',self.top)
        elif type(self.height) is type(0.0):
            self.height = float(self.pxheight)/self.container.pxheight
            self._onChangeRawValue('height',self.height)
            for child in self.children:
                child._updateRawOnContainerHeightChanged()
        elif type(self.bottom) is type(0.0):
            self.bottom = float(self.container.pxheight-self.pxtop-self.pxheight)/self.container.pxheight
            self._onChangeRawValue('bottom',self.bottom)

    # change an pixel value only (left/width/top and height)
    # according to the changement modify the raw values in order to keep all constraint valid
    # for each raw value changed, the callback onChangeRawValue is called
    def changePxValue(self, name, value):
        self._toInitState()
        self.pxValuesHasChanged = 0

        if name == 'left':
            offset = value-self.pxleft
            self.pxleft = value
            if type(self.left) == type(None) and type(self.right) == type(None):
                self.left = value
                self._onChangeRawValue('left',self.left)
            else:
                if type(self.left) is type(0.0):
                    self.left = float(value)/self.container.pxwidth
                    self._onChangeRawValue('left',self.left)
                elif type(self.left) is type(0):
                    self.left = value
                    self._onChangeRawValue('left',self.left)
                if type(self.right) is type(0.0):
                    self.right = float(self.right-offset)/self.container.pxwidth
                    self._onChangeRawValue('right',self.right)
                elif type(self.right) is type(0):
                    self.right = self.right-offset
                    self._onChangeRawValue('right',self.right)

        elif name == 'width':
            if value <= 0: value = 1
            offset = value-self.pxwidth
            self.pxwidth = value
            if type(self.right) is not type(None) and \
                    type(self.width) is type(None):
                if type(self.right) is type(0.0):
                    self.right = float(self.right-offset)/self.container.pxwidth
                    self._onChangeRawValue('right',self.right)
                elif type(self.right) is type(0):
                    self.right = self.right-offset
                    self._onChangeRawValue('right',self.right)
            else:
                if type(self.width) is type(0.0):
                    self.width = float(value)/self.container.pxwidth
                    self._onChangeRawValue('width',self.width)
                else:
                    self.width = value
                    self._onChangeRawValue('width',self.width)
                if type(self.width) != type(None) and type(self.right) != type(None):
                    if type(self.left) == type(None):
                        if type(self.right) is type(0.0):
                            self.right = float(self.right-offset)/self.container.pxwidth
                            self._onChangeRawValue('right',self.right)
                        elif type(self.right) is type(0):
                            self.right = self.right-offset
                            self._onChangeRawValue('right',self.right)
                    else:
                        self.right = None
                        self._onChangeRawValue('right',self.right)

            for child in self.children:
                child._updateRawOnContainerWidthChanged()

        elif name == 'top':
            offset = value-self.pxtop
            self.pxtop = value
            if type(self.top) == type(None) and type(self.bottom) == type(None):
                self.top = value
                self._onChangeRawValue('top',self.top)
            else:
                if type(self.top) is type(0.0):
                    self.top = float(value)/self.container.pxheight
                    self._onChangeRawValue('top',self.top)
                elif type(self.top) is type(0):
                    self.top = value
                    self._onChangeRawValue('top',self.top)
                if type(self.bottom) is type(0.0):
                    self.bottom = float(self.bottom-offset)/self.container.pxheight
                    self._onChangeRawValue('bottom',self.bottom)
                elif type(self.bottom) is type(0):
                    self.bottom = self.bottom-offset
                    self._onChangeRawValue('bottom',self.bottom)

        elif name == 'height':
            if value <= 0: value = 1
            offset = value-self.pxheight
            self.pxheight = value
            if type(self.bottom) is not type(None) and \
                    type(self.height) is type(None):
                if type(self.bottom) is type(0.0):
                    self.bottom = float(self.bottom-offset)/self.container.pxheight
                    self._onChangeRawValue('bottom',self.bottom)
                elif type(self.bottom) is type(0):
                    self.bottom = self.bottom-offset
                    self._onChangeRawValue('bottom',self.bottom)
            else:
                if type(self.height) is type(0.0):
                    self.height = float(value)/self.container.pxheight
                    self._onChangeRawValue('height',self.height)
                else:
                    self.height = value
                    self._onChangeRawValue('height',self.height)
                if type(self.height) != type(None) and type(self.bottom) != type(None):
                    if type(self.top) == type(None):
                        if type(self.bottom) is type(0.0):
                            self.bottom = float(self.bottom-offset)/self.container.pxheight
                            self._onChangeRawValue('bottom',self.bottom)
                        elif type(self.bottom) is type(0):
                            self.bottom = self.bottom-offset
                            self._onChangeRawValue('bottom',self.bottom)
                    else:
                        self.bottom = None
                        self._onChangeRawValue('bottom',self.bottom)

            for child in self.children:
                child._updateRawOnContainerHeightChanged()

        if self.pxValuesHasChanged:
            self._onGeomChanged()

    def _onChangeRawValue(self, name, value):
        self.context._onRawValuesChanged(self, name, value)

    def _onChangePxValue(self, name, value):
        self.pxValuesHasChanged = 1

    def _onGeomChanged(self):
        self.context._onPxValuesChanged(self, self._getPxGeom())

    def _getPxGeom(self):
        return self.pxleft, self.pxtop, self.pxwidth, self.pxheight

    def getFit(self):
        if self.fit is not None:
            return self.fit
        else:
            # default value: hidden
            # todo: get value from mmattrdef
            return 'hidden'

    def getRegPoint(self):
        if self.regPoint is not None:
            return self.regPoint
        else:
            # default value: topleft
            # todo: get value from mmattrdef
            return 'topLeft'

    def getRegAlign(self):
        if self.regAlign is not None:
            return self.regAlign

        # if no regAlign defined here, the default come from regPoint
        return None

    def _minsize(self, start, extent, end, minsize):
        # Determine minimum size for parent window given that it
        # has to contain a subwindow with the given start/extent/end
        # values.  Start and extent can be integers or floats.  The
        # type determines whether they are interpreted as pixel values
        # or as fractions of the top-level window.
        # end is only used if extent is None.
        if start == 0:
            # make sure this is a pixel value
            start = 0
##     if extent is None and (type(start) is type(end) or start == 0):
##         extent = end - start
##         end = None
        if type(start) is type(0):
            # start is pixel value
            if type(extent) is type(0.0):
                # extent is fraction
                if extent == 0 or (extent == 1 and start > 0):
                    print 'region with impossible size'
                    return minsize
                if extent == 1:
                    return minsize
                size = int(start / (1 - extent) + 0.5)
                if minsize > 0 and extent > 0:
                    size = max(size, int(minsize/extent + 0.5))
                return size
            elif type(extent) is type(0):
                # extent is pixel value
                if extent == 0:
                    extent = minsize
                return start + extent
            elif type(end) is type(0.0):
                if end == 1.0:
                    return minsize
                # no extent, end is fraction
                return int((start + minsize) / (1 - end) + 0.5)
            elif type(end) is type(0):
                # no extent, end is pixel value
                # warning end is relative to the parent end egde
                return start + minsize + end
            else:
                # no extent and no end
                return start + minsize
        elif type(start) is type(0.0):
            # start is fraction
            if start == 1:
                # region with impossible size
                return minsize
            if type(extent) is type(0):
                # extent is pixel value
                if extent == 0:
                    extent = minsize
                return int(extent / (1 - start) + 0.5)
            elif type(extent) is type(0.0):
                # extent is fraction
                if minsize > 0 and extent > 0:
                    return int(minsize / extent + 0.5)
                return 0
            elif type(end) is type(0):
                # no extent, end is pixel value
                return int ((minsize + end) / (1 - start) + 0.5)
            elif type(end) is type(0.0):
                # no extent, end is fraction
                if (start+end) == 1.0:
                    return minsize
                return int(minsize / (1 - start - end) + 0.5)
            else:
                # no extent and no end
                return int(minsize / (1 - start) + 0.5)
        elif type(end) is type(0):
            # no start, end is pixel value
            # warning end is relative to the parent end egde
            return end + minsize
        elif type(end) is type(0.0):
            # no start, end is fraction
            if end <= 0:
                return minsize
            if type(extent) is type(0):
                # extent is pixel value
                if extent == 0:
                    extent = minsize
                return int(extent / end + 0.5)
            elif type(extent) is type(0.0):
                # extent is fraction
                return int(minsize / end + 0.5)
        elif type(extent) is type(0):
            return extent
        elif type(extent) is type(0.0) and extent > 0:
            return int(minsize / extent + 0.5)
        return minsize

    def guessSize(self):
        minWidth = 100
        minHeight = 100
        for child in self.children:
            widthChild, heightChild = child.guessSize()
            width = self._minsize(self.left, self.width,
                            self.right,widthChild)
            if width > minWidth:
                minWidth = width
            height = self._minsize(self.top, self.height,
                            self.bottom, heightChild)
            if height > minHeight:
                minHeight = height

        return minWidth, minHeight



class RootNode(RegionNode):
    def __init__(self, context, mmobj=None):
        self.__oldpxsize = None
        RegionNode.__init__(self, context, mmobj)

    def copyRawAttrs(self, srcNode):
        self.pxwidth = srcNode.pxwidth
        self.pxheight = srcNode.pxheight

        self._toUnInitState()

    def setRawAttrs(self, attrList):
        for name, value in attrList:
            if name == 'width':
                self.pxwidth = value
            elif name == 'height':
                self.pxheight = value

        self._toUnInitState()

    def getRawAttr(self, name):
        if name == 'width':
            return self.pxwidth
        elif name == 'height':
            return self.pxheight

        return None

    def updateAll(self):
        self._onGeomChanged()
        for child in self.children:
            child.update()

    def updateTree(self):
        for child in self.children:
            child.updateTree()

    def getAbsPos(self):
        return 0, 0

    def _onGeomChanged(self):
        self.context._onPxValuesChanged(self, self._getPxGeom())

    def _getPxGeom(self):
        return (self.pxwidth, self.pxheight)

    def getPxAbsGeom(self):
        self._toInitState()
        return 0, 0, self.pxwidth, self.pxheight

    def _toInitState(self):
        if self.pxwidth is None or self.pxheight is None:
            self.pxwidth, self.pxheight = self.guessSize()
        import features
        if features.editor:
            import settings
            skin = settings.get('skin') or ''
            if self.__oldpxsize is None:
                # remember initial values
                self.__oldpxsize = self.pxwidth, self.pxheight
            else:
                # first reset to initial values
                self.pxwidth, self.pxheight = self.__oldpxsize
                self._toUnInitState()
            if skin:
                # In the editor, if there is a skin,
                # scale down the viewport to the size
                # of the skin displayable area.
                import MMurl, parseskin
                try:
                    f = MMurl.urlopen(skin)
                    dict = parseskin.parsegskin(f)
                    f.close()
                except parseskin.error, msg:
                    pass
                else:
                    if dict.has_key('display'):
                        width, height = dict['display'][1][2:4]
                        if self.pxwidth > width or self.pxheight > height:
                            from fmtfloat import round
                            scale = min(float(width) / self.pxwidth, float(height) / self.pxheight)
                            self.pxwidth = round(self.pxwidth * scale)
                            self.pxheight = round(self.pxheight * scale)
                            self._toUnInitState()

        self.isInit = 1

class MediaNode(Node):
    def __init__(self, context, defaultSizeHandler, mmobj=None):
        Node.__init__(self, context, mmobj)
        self.alignHandler = None
        self.intrinsicWidth = None
        self.intrinsicHeight = None
        self.defaultSizeHandler = defaultSizeHandler
        self.mmRegPoint = None # allow for a private instance
        self.dx, self.dy = 0, 0 # allow for offsets

    def copyRawAttrs(self, srcNode):
        Node.copyRawAttrs(self,srcNode)
        self.intrinsicWidth = srcNode.intrinsicWidth
        self.intrinsicHeight = srcNode.intrinsicHeight

        self._toUnInitState()

    def __checkIntrinsicSize(self):
        # check invalid value to avoid a crash
        # shouldn't happend. If happend, assume no intrinsic size
        if self.intrinsicWidth is not None and self.intrinsicWidth <= 0:
#                       print 'Error: SMILCssResolver, intrinsic media width = ',self.intrinsicWidth
            self.intrinsicWidth = None
            self.intrinsicHeight = None
        if self.intrinsicHeight is not None and self.intrinsicHeight <= 0:
#                       print 'Error: SMILCssResolver, intrinsic media height = ',self.intrinsicHeight
            self.intrinsicWidth = None
            self.intrinsicHeight = None

    def update(self):
        # get the intrinsic size
        # note: for optimization, the defaultSizeHandler method has a cache
        self.intrinsicWidth, self.intrinsicHeight = self.defaultSizeHandler(None, None)
        self.__checkIntrinsicSize()

        self.pxleft, self.pxtop, self.pxwidth, self.pxheight = self._getMediaSpaceArea()
        if self.pxwidth <= 0: self.pxwidth = 1
        if self.pxheight <= 0: self.pxheight = 1
        self._onGeomChanged()

    def updateTree(self):
        self.update()

    def getMMRegPoint(self):
        if self.mmRegPoint:
            return self.mmRegPoint
        regPoint = self.getRegPoint()
        mmregpoint = self.context.getDocumentContext().GetRegPoint(regPoint)
        if mmregpoint is None:
            # if no regpoint defined, return the default regpoint ('topLeft'): it avoids a crahes
            mmregpoint=self.context.getDocumentContext().GetRegPoint('topLeft')
        return mmregpoint

    def move(self, pos):
        self.dx = int(pos[0])
        self.dy = int(pos[1])

    def isDOMRegPoint(self):
        return self.dx==0 and self.dy==0

    # return the tuple x,y alignment in pourcent value
    # alignOveride is an optional overide id
    def _getxyAlign(self, alignOveride=None):
        alignId = None
        if alignOveride is None:
            alignId = self.getregalign()
        else:
            alignId = alignOveride

        from RegpointDefs import alignDef
        xy = alignDef.get(alignId)
        if xy is None:
            # impossible value, avoid a crash if bug
            xy = (0.0, 0.0)
        return xy

    def guessSize(self):
        # get the intrinsic size
        # note: for optimization, the defaultSizeHandler method has a cache
        self.intrinsicWidth, self.intrinsicHeight = self.defaultSizeHandler(None, None)
        self.__checkIntrinsicSize()

        # if no intrinsic size, return a default value
        if self.intrinsicHeight is None or self.intrinsicWidth is None:
            return 100,100

        regPointObject = self.getMMRegPoint()
        regAlign = self._getRegAlign(regPointObject)

        # convert regalignid to pourcent value
        regAlignX, regAlignY = self._getxyAlign(regAlign)

        # convert value to pixel, relative to the media
        regAlignW1 = int (regAlignX * self.intrinsicWidth + 0.5)
        regAlignW2 = int ((1-regAlignX) * self.intrinsicWidth + 0.5)

        regAlignH1 = int (regAlignY * self.intrinsicHeight + 0.5)
        regAlignH2 = int ((1-regAlignY) * self.intrinsicHeight + 0.5)

        width = self._minsizeRp(regPointObject['left'],
                                 regPointObject['right'],
                                 regAlignW1, regAlignW2, self.intrinsicWidth)

        height = self._minsizeRp(regPointObject['top'],
                                regPointObject['bottom'],
                                regAlignH1, regAlignH2, self.intrinsicHeight)

        return width, height

    # Determine the minimum size for the container  the regpoint/regalign
    # wR1 is the size from container left edge to regpoint.
    # wR2 is the size from regpoint to container right edge)
    # wR1 and wR2 are in pourcent (float) or pixel (integer). You can't have the both in the same time
    # wM1 is the size from media left edge to alignPoint
    # wM2 is the size from alignpoint to media right edge
    # wM1 and wM2 are pixel only (integer). You have to specify the both in the same time
    def _minsizeRp(self, wR1, wR2, wM1, wM2, minsize):

        # for now. Avoid to have in some case some to big values
        MAX_REGION_SIZE = 5000

        if wR1 is not None and wR2 is not None:
            # conflict regpoint attribute
            return minsize

        if wM1 is None or wM2 is None:
            # bad parameters
            return minsize

        # first constraint
        newsize = minsize
        if type(wR1) is type (0.0):
            if wR1 == 1.0:
                # regpoint with impossible alignment, return minsize
                return minsize
            wN = int (wM2 / (1-wR1) + 0.5)
            if wN > newsize:
                newsize = wN
        elif type(wR1) is type (0):
            wN = wR1 + wM2
            if wN > newsize:
                newsize = wN
        elif type(wR2) is type (0.0):
            if wR2 == 0.0:
                # the media will stay invisible whichever the value
                # we keep the same size
                pass
            else:
                wN = int(wM2 / wR2 + 0.5)
                # test if the size is acceptable
                if wN > MAX_REGION_SIZE:
                    wN = MAX_REGION_SIZE
                if wN > newsize:
                    newsize = wN
        elif type(wR2) is type (0):
            # keep the same size
            pass
        else:
            # no constraint
            pass

        # second constraint
        if type(wR2) is type (0.0):
            if wR2 == 1.0:
                # regpoint with impossible alignment, return minsize
                return minsize
            wN = int(wM1 / (1.0-wR2) + 0.5)
            if wN > newsize:
                newsize = wN
        elif type(wR2) is type (0):
            # don't change anything
            pass
        elif type(wR1) is type (0.0):
            if wR1 == 0.0:
                # the media will stay invisible whichever the value
                # we keep the same size
                pass
            else:
                wN = int(wM1 / wR1 + 0.5)
                # test if the size is acceptable
                if wN > MAX_REGION_SIZE:
                    wN = MAX_REGION_SIZE
                if wN > newsize:
                    newsize = wN
        elif type(wR1) is type (0):
            wN = wR1 + wM1
            if wN > newsize:
                newsize = wN
        else:
            # no constraint
            pass

        return newsize

    def setRawAttrs(self, attrList):
        for name, value in attrList:
            Node._setRawAttr(self, name, value)

        self._toUnInitState()

    def getRawAttr(self, name):
        if name == 'width':
            return self.intrinsicWidth
        elif name == 'height':
            return self.intrinsicHeight
        else:
            return Node._getRawAttr(self, name)

    def _updateOnContainerHeightChanged(self):
        self._toInitState()
        self.pxleft, self.pxwidth, self.pxtop, self.pxheight = self._getMediaSpaceArea()
        self._onGeomChanged()

    def _updateOnContainerWidthChanged(self):
        self._toInitState()
        self.pxleft, self.pxwidth, self.pxtop, self.pxheight = self._getMediaSpaceArea()
        self._onGeomChanged()

    def _updatePxOnContainerHeightChanged(self):
        self._updateOnContainerHeightChanged()

    def _updateRawOnContainerHeightChanged(self):
        self._updateOnContainerHeightChanged()

    def _updatePxOnContainerWidthChanged(self):
        self._updateOnContainerWidthChanged()

    def _updateRawOnContainerWidthChanged(self):
        self._updateOnContainerWidthChanged()


    # get the space display area of media according to registration points /alignement and fit attribute
    # return pixel values
    def _getMediaSpaceArea(self):
        # if no intrinsic size, the size area is the entire region
        if self.intrinsicHeight is None or self.intrinsicWidth is None:
            return 0, 0, self.container.pxwidth, self.container.pxheight

        # get fit attribute
        fit = self.getFit()

        # get regpoint
        # for now, regpoint come from directly MMContext.
        # It's not a problem as long as regpoint element is not animable
        regPointObject = self.getMMRegPoint()

        regpoint_x = regPointObject.getx(self.container.pxwidth)
        regpoint_y = regPointObject.gety(self.container.pxheight)

        # get regalign
        regalign = self._getRegAlign(regPointObject)

        # this algorithm depends of fit attribute
        if fit is None or fit == 'hidden':
            area_height = self.intrinsicHeight
            area_width = self.intrinsicWidth

        elif fit == 'meet':
            if regalign in ('topLeft', 'topMid', 'topRight'):
                area_height = self.container.pxheight-regpoint_y
            if regalign in ('topLeft', 'midLeft', 'bottomLeft'):
                area_width = self.container.pxwidth-regpoint_x
            if regalign in ('topMid', 'center', 'bottomMid'):
                area_width = self.container.pxwidth-regpoint_x
                if regpoint_x < area_width:
                    area_width = regpoint_x
                area_width = area_width*2
            if regalign in ('topRight', 'midRight', 'bottomRight'):
                area_width = regpoint_x
            if regalign in ('midLeft', 'midRight', 'center'):
                area_height = self.container.pxheight-regpoint_y
                if regpoint_y < area_height:
                    area_height = regpoint_y
                area_height = area_height*2
            if regalign in ('bottomLeft', 'bottomMid', 'bottomRight'):
                area_height = regpoint_y

            media_ratio = float(self.intrinsicWidth)/float(self.intrinsicHeight)
            # print 'ratio=',media_ratio
            if area_height*media_ratio > area_width:
                area_height = int(area_width/media_ratio)
            else:
                area_width = int(area_height*media_ratio)

        elif fit == 'slice':
            if regalign in ('topLeft', 'topMid', 'topRight'):
                area_height = self.container.pxheight-regpoint_y
            if regalign in ('topLeft', 'midLeft', 'bottomLeft'):
                area_width = self.container.pxwidth-regpoint_x
            if regalign in ('topMid', 'center', 'bottomMid'):
                area_width = self.container.pxwidth-regpoint_x
                if regpoint_x > area_width:
                    area_width = regpoint_x
                area_width = area_width*2
            if regalign in ('topRight', 'midRight', 'bottomRight'):
                area_width = regpoint_x
            if regalign in ('midLeft', 'midRight', 'center'):
                area_height = self.container.pxheight-regpoint_y
                if regpoint_y > area_height:
                    area_height = regpoint_y
                area_height = area_height*2
            if regalign in ('bottomLeft', 'bottomMid', 'bottomRight'):
                area_height = regpoint_y

            media_ratio = float(self.intrinsicWidth)/float(self.intrinsicHeight)
            # print 'ratio=',media_ratio
            if area_height*media_ratio < area_width:
                area_height = area_width/media_ratio
            else:
                area_width = area_height*media_ratio

        elif fit == 'fill':
            if regalign in ('topLeft', 'topMid', 'topRight'):
                area_height = self.container.pxheight-regpoint_y
            if regalign in ('topLeft', 'midLeft', 'bottomLeft'):
                area_width = self.container.pxwidth-regpoint_x
            if regalign in ('topMid', 'center', 'bottomMid'):
                area_width = self.container.pxwidth-regpoint_x
                area_width = area_width*2
            if regalign in ('topRight', 'midRight', 'bottomRight'):
                area_width = regpoint_x
            if regalign in ('midLeft', 'midRight', 'center'):
                area_height = self.container.pxheight-regpoint_y
                area_height = area_height*2
            if regalign in ('bottomLeft', 'bottomMid', 'bottomRight'):
                area_height = regpoint_y

        elif fit == 'scroll':
            area_height = self.intrinsicHeight
            area_width = self.intrinsicWidth

        if regalign in ('topLeft', 'topMid', 'topRight'):
            area_top = regpoint_y
        if regalign in ('topLeft', 'midLeft', 'bottomLeft'):
            area_left = regpoint_x
        if regalign in ('topMid', 'center', 'bottomMid'):
            area_left = regpoint_x-(area_width/2)
        if regalign in ('topRight', 'midRight', 'bottomRight'):
            area_left = regpoint_x-area_width
        if regalign in ('midLeft', 'midRight', 'center'):
            area_top = regpoint_y-(area_height/2)
        if regalign in ('bottomLeft', 'bottomMid', 'bottomRight'):
            area_top = regpoint_y-area_height

        #
        # end of positioning algorithm

        # print 'area geom = ',area_left, area_top, area_width, area_height

        # avoid crashes
        if area_width <= 0: area_width = 1
        if area_height <= 0: area_height = 1

        return int(area_left), int(area_top), int(area_width), int(area_height)

    def getFit(self):
        if self.fit is not None:
            return self.fit
        else:
            region = self.__getRegion()
            if region is not None:
                return region.getFit()

    def __getRegion(self):
        subreg = self.container
        if self.container is not None:
            return subreg.container

        return None

    def getRegPoint(self):
        if self.regPoint is not None:
            return self.regPoint
        else:
            region = self.__getRegion()
            if region is not None:
                return region.getRegPoint()

        # we shouldn't pass here
        return 'topLeft'

    def getRegAlign(self):
        regPointObject = self.getMMRegPoint()
        return self._getRegAlign(regPointObject)

    def _getRegAlign(self, regPointObject):
        if self.regAlign is not None:
            return self.regAlign
        else:
            # default value
            regAlign = 'topLeft'
            region = self.__getRegion()
            if region is not None:
                regAlign = region.getRegAlign()
                if regAlign is None:
                    regAlign = regPointObject.getregalign()

        return regAlign

    def _onChangePxValue(self, name, value):
        self.pxValuesHasChanged = 1

    def _onGeomChanged(self):
        self.context._onPxValuesChanged(self, self._getPxGeom())

    def _getPxGeom(self):
        return self.pxleft+self.dx, self.pxtop+self.dy, self.pxwidth, self.pxheight
