__version__ = "$Id$"

#
#       SVG Renderer
#

import svgdom
import svgpath

import string

class SVGRenderer:
    animateEl = ['animate', 'set', 'animateMotion', 'animateColor', 'animateTransform']
    filter = ['#comment', 'style', 'defs'] + animateEl
    def __init__(self, svgdoc, svggraphics):
        self.reset(svgdoc, svggraphics)
        self._verbose = 0

    def reset(self, svgdoc, svggraphics):
        self.svgdoc = svgdoc

        # svg graphics object
        self.graphics = svggraphics

        # svg graphics object stack
        # for save/restore graphics
        self._grstack = []

        # regions
        self.regions = []
        self.node2rgn = {}

    def __del__(self):
        #self.delAnchors()
        pass

    def getFilter(self): return SVGRenderer.filter
    def getWidth(self): return self._renderbox[2]
    def getHeight(self): return self._renderbox[3]
    def getSize(self): return self._renderbox[2:]
    def getRenderBox(self): return self._renderbox
    def getCTM(self): return self.graphics.ctm

    def getElementAt(self, pt):
        rgns = self.regions[:]
        rgns.reverse()
        for node, rgn in rgns:
            if self.graphics.inside(rgn, pt):
                return node
        return None

    def delRegions(self):
        for rgn in self.rgn2node.keys():
            self.graphics.delRegion(rgn)
        self.regions = []
        self.node2rgn = {}

    def appendRegion(self, node, rgn):
        self.regions.append((node, rgn))
        self.node2rgn[node] = rgn

    def render(self):
        self.graphics.onBeginRendering()
        iter = svgdom.DOMIterator(self.svgdoc, self, filter=SVGRenderer.filter)
        while iter.advance(): pass
        self.graphics.onEndRendering()

    #
    # DOMIterator listener interface
    #
    def startnode(self, node):
        if not node.isVisible():
            return
        node.setCTMProvider(self)
        eltype = node.getType()
        try:
            fo = getattr(self, eltype)
            fo(node)
        except AttributeError, arg:
            print arg
            if not hasattr(self, 'eltype'):
                self.svgelement(node)
            else:
                print arg

    def endnode(self, node):
        if not node.isVisible():
            return
        node.setCTMProvider(None)
        eltype = node.getType()
        if eltype in ('svg', 'g'):
            try:
                fo = getattr(self, 'end_' + eltype)
                fo(node)
            except AttributeError, arg:
                print 'failed to process element:', `eltype`
                print '(', arg, ')'

    #
    # Common behavior
    #
    def begingroup(self, node):
        self.saveGraphics()
        x, y = node.get('x'), node.get('y')
        self.graphics.applyTfList([('translate', [x, y]),])
        self.graphics.applyStyle(node.getStyle())
        self.graphics.applyTfList(node.getTransform())
        self.graphics.tkOnBeginContext()

    def endgroup(self, node):
        self.restoreGraphics()
        self.graphics.tkOnEndContext()

    def getViewboxTfList(self, size, viewbox, align, meetOrSlice):
        vw, vh = size
        x, y, w, h = viewbox
        xs, ys = vw/float(w), vh/float(h)
        tflist = []

        if align == 'none':
            tflist.append(('scale', [xs, ys]))
            if x or y:
                tflist.append(('translate', [-x, -y]))
            return tflist

        if meetOrSlice == 'meet':
            scale = min(xs, ys)
            xscale, yscale = scale, scale
        elif meetOrSlice == 'slice':
            scale = max(xs, ys)
            xscale, yscale = scale, scale

        dx, dy, dw, dh = xscale*x, yscale*y, xscale*w, yscale*h
        xalign, yalign = align[1:4], align[5:]
        if xalign == 'Min':
            dx = 0
        elif xalign == 'Mid':
            dx = vw/2 - dw/2
        elif xalign == 'Max':
            dx = vw - dw
        if yalign == 'Min':
            dy = 0
        elif yalign == 'Mid':
            dy = vh/2 - dh/2
        elif yalign == 'Max':
            dy = vh - dh

        tflist.append(('translate', [dx, dy]))
        tflist.append(('scale', [xscale, yscale]))
        if x or y:
            tflist.append(('translate', [-x, -y]))
        return tflist

    #
    # SVG elements processors
    #
    def svg(self, node):
        self.saveGraphics()
        x, y, w, h = node.get('x'), node.get('y'), node.get('width'), node.get('height')
        if not w or not h:
            w, h = node.getSize()
        self.graphics.tkClipBox((x, y, w, h))
        self.graphics.applyTfList([('translate', [x, y]),])

        viewbox = node.get('viewBox')
        if viewbox is not None:
            ar = node.get('preserveAspectRatio')
            if ar is None:
                align = 'xMidYMid'
                meetOrSlice = 'meet'
            else:
                align, meetOrSlice = ar
            tflist = self.getViewboxTfList((w, h), viewbox, align, meetOrSlice)
            self.graphics.applyTfList(tflist)
        self.graphics.applyStyle(node.getStyle())
        self.graphics.applyTfList(node.getTransform())
        self.graphics.tkOnBeginContext()

    def end_svg(self, node):
        self.restoreGraphics()
        self.graphics.tkOnEndContext()

    def g(self, node):
        self.saveGraphics()
        self.graphics.applyStyle(node.getStyle())
        self.graphics.applyTfList(node.getTransform())
        self.graphics.tkOnBeginContext()

    def end_g(self, node):
        self.restoreGraphics()
        self.graphics.tkOnEndContext()

    def rect(self, node):
        pos = node.get('x'), node.get('y')
        size = node.get('width'), node.get('height')
        rxy = node.get('rx'), node.get('ry')
        if self.node2rgn.get(node) is None:
            rgn = self.graphics.drawRect(pos, size, rxy, node.getStyle(), node.getTransform(), 1)
            self.appendRegion(node, rgn)
        else:
            self.graphics.drawRect(pos, size, rxy, node.getStyle(), node.getTransform())

    def circle(self, node):
        pos = node.get('cx'), node.get('cy')
        r = node.get('r')
        if self.node2rgn.get(node) is None:
            rgn = self.graphics.drawCircle(pos,  r, node.getStyle(), node.getTransform(), 1)
            self.appendRegion(node, rgn)
        else:
            self.graphics.drawCircle(pos,  r, node.getStyle(), node.getTransform())

    def ellipse(self, node):
        pos = node.get('cx'), node.get('cy')
        rxy = node.get('rx'), node.get('ry')
        if self.node2rgn.get(node) is None:
            rgn = self.graphics.drawEllipse(pos,  rxy, node.getStyle(), node.getTransform(), 1)
            self.appendRegion(node, rgn)
        else:
            self.graphics.drawEllipse(pos,  rxy, node.getStyle(), node.getTransform())

    def line(self, node):
        pt1 = node.get('x1'), node.get('y1')
        pt2 = node.get('x2'), node.get('y2')
        self.graphics.drawLine(pt1, pt2, node.getStyle(), node.getTransform())

    def polyline(self, node):
        points = node.get('points')
        self.graphics.drawPolyline(points, node.getStyle(), node.getTransform())

    def polygon(self, node):
        points = node.get('points')
        if self.node2rgn.get(node) is None:
            rgn = self.graphics.drawPolygon(points, node.getStyle(), node.getTransform(), 1)
            self.appendRegion(node, rgn)
        else:
            self.graphics.drawPolygon(points, node.getStyle(), node.getTransform())

    def path(self, node):
        d = node.get('d')
        self.graphics.drawPath(d, node.getStyle(), node.getTransform())

    def text(self, node):
        pos = node.get('x'), node.get('y')
        self.graphics.drawText(node.data, pos, node.getStyle(), node.getTransform())

    def use(self, node):
        if node.what is None:
            what = node.locateDef()
        if node.what is not None:
            self.begingroup(node)
            what = node.what
            self.startnode(what)
            iter = svgdom.DOMIterator(what, self)
            while iter.advance(): pass
            self.endnode(what)
            self.endgroup(node)

    def title(self, node):
        if self._verbose:
            print 'TITLE:', `node.data`

    def desc(self, node):
        if self._verbose:
            print 'DESC:', `node.data`

    def svgelement(self, node):
        print 'unprocessed element', node

    #
    #  Save and restore graphics for grouping elements
    #
    def saveGraphics(self):
        self._grstack.append(self.graphics.clone())

    def restoreGraphics(self):
        assert len(self._grstack)>0, 'unpaired save/restore graphics'
        self.graphics = self._grstack.pop()


####################################
# test

if __debug__:
    import wingdi
    import win32con

    def createDDSurface():
        # create a ddraw surface with this size
        import ddraw, winuser
        ddrawobj = ddraw.CreateDirectDraw()
        ddrawobj.SetCooperativeLevel(winuser.GetDesktopWindow().GetSafeHwnd(), ddraw.DDSCL_NORMAL)
        ddsd = ddraw.CreateDDSURFACEDESC()
        ddsd.SetFlags(ddraw.DDSD_CAPS)
        ddsd.SetCaps(ddraw.DDSCAPS_PRIMARYSURFACE)
        frontBuffer = ddrawobj.CreateSurface(ddsd)
        frontBuffer.GetPixelFormat()
        return ddrawobj, frontBuffer

    def Render(source, msecwait=3000):
        import svgwin, winuser, winkernel
        svgdoc = svgdom.SvgDocument(source)
        svggraphics = svgwin.SVGWinGraphics()
        ddrawobj, dds = createDDSurface()
        ddshdc = dds.GetDC()
        svggraphics.tkStartup(ddshdc)
        renderer = SVGRenderer(svgdoc, svggraphics)
        renderer.render()
        svggraphics.tkShutdown()
        dds.ReleaseDC(ddshdc)
        winkernel.Sleep(msecwait)
        winuser.GetDesktopWindow().RedrawWindow(None, 0, win32con.RDW_INVALIDATE | win32con.RDW_ERASE | win32con.RDW_ALLCHILDREN)
        del dds
        del ddrawobj


    svgSource = """<?xml version="1.0" standalone="no"?>
    <!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 20001102//EN"
      "http://www.w3.org/TR/2000/CR-SVG-20001102/DTD/svg-20001102.dtd">
    <svg width="12cm" height="5.25cm" viewBox="0 0 1200 400">
      <title>Example arcs01 - arc commands in path data</title>
      <desc>Picture of a pie chart with two pie wedges and
            a picture of a line with arc blips</desc>
      <rect x="1" y="1" width="1198" height="398"
            style="fill:none; stroke:blue; stroke-width:1"/>

      <path d="M300,200 h-150 a150,150 0 1,0 150,-150 z"
            style="fill:red; stroke:blue; stroke-width:5"/>
      <path d="M275,175 v-150 a150,150 0 0,0 -150,150 z"
            style="fill:yellow; stroke:blue; stroke-width:5"/>

      <path d="M600,350 l 50,-25
               a25,25 -30 0,1 50,-25 l 50,-25
               a25,50 -30 0,1 50,-25 l 50,-25
               a25,75 -30 0,1 50,-25 l 50,-25
               a25,100 -30 0,1 50,-25 l 50,-25"
            style="fill:none; stroke:red; stroke-width:5" />
    </svg>
    """

    #################

    if __name__ == '__main__':
        Render(svgSource, 5000)
        #svg = svgdom.SvgDocument(svgSource)
        #svg.write()
