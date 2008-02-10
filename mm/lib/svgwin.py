__version__ = "$Id$"

#
#       Windows SVG module
#

import svggraphics
import svgtypes

import wingdi

import win32con

import math

class SVGWinGraphics(svggraphics.SVGGraphics):
    #
    #  platform toolkit interface
    #
    # called to intialize platform toolkit before rendering
    def tkStartup(self, params):
        hdc = params
        self.dc = wingdi.CreateDCFromHandle(hdc)

        # context vars
        self.tk = Tk()
        self.saveidorg = self.tk.saveid = self.dc.SaveDC()
        self._tkstack = []

        self.dc.SetGraphicsMode(win32con.GM_ADVANCED)
        self.dc.SetBkMode(win32con.TRANSPARENT)
        self.dc.SetTextAlign(win32con.TA_BASELINE)

    # called to dispose platform toolkit objects after rendering
    def tkShutdown(self):
        self.dc.SetGraphicsMode(win32con.GM_COMPATIBLE)
        self.dc.SetMapMode(win32con.MM_TEXT)
        self.dc.RestoreDC(self.tk.saveid)
        self.dc.Detach()

    # we start rendering
    def tkOnBeginRendering(self):
        self.dc.SetMapMode(win32con.MM_ISOTROPIC)
        vcx, vcy = self.dc.GetViewportExtEx()
        if vcy<0: vcy = -vcy
        self.dc.SetWindowExtEx((vcx, vcy))
        self.dc.SetViewportExtEx((vcx, vcy))
        self.dc.SetViewportOrgEx((0, 0))

    # we finished rendering
    def tkOnEndRendering(self):
        pass

    def delRegion(self, rgn):
        rgn.DeleteObject()

    def inside(self, rgn, pt):
        return rgn.PtInRegion(pt)

    # new graphics context
    # self state reflects this new context
    def tkOnBeginContext(self):
        # push current tkctx
        self.saveTk()

        # save dc and hold its id for restore
        self.tk.saveid = self.dc.SaveDC()

        # establish tk pen
        stroke = self.getStyleAttr('stroke')
        strokeWidth = self.getStyleAttr('stroke-width')
        if stroke is not None and stroke!='none':
            self.tk.pen = wingdi.ExtCreatePen(strokeWidth, stroke)
            self.dc.SelectObject(self.tk.pen)

        # establish tk brush
        fill = self.getStyleAttr('fill')
        if fill is not None and fill != 'none':
            self.tk.brush = wingdi.CreateSolidBrush(fill)
            self.dc.SelectObject(self.tk.brush)

        # establish tk font
        fontFamily = self.getStyleAttr('font-family')
        fontSize = self.getStyleAttr('font-size')
        if fontFamily is not None:
            self.tk.font = wingdi.CreateFontIndirect({'name': fontFamily, 'height':fontSize,  'outprecision':win32con.OUT_OUTLINE_PRECIS, })
            self.dc.SelectObject(self.tk.font)

        # establish tk transform
        self.dc.SetWorldTransform(self.ctm.getElements())

    # end of context
    # self state reflects the restored context
    def tkOnEndContext(self):
        # restore dc to its previous state before deleting objects
        self.dc.RestoreDC(self.tk.saveid)

        if self.tk.pen:
            wingdi.DeleteObject(self.tk.pen)

        if self.tk.brush:
            wingdi.DeleteObject(self.tk.brush)

        if self.tk.font:
            wingdi.DeleteObject(self.tk.font)

        # restore previous tk
        self.restoreTk()

        # establish tk transform
        self.dc.SetWorldTransform(self.ctm.getElements())

    # init toolkit objects for 'other'
    def tkInitInstance(self, other):
        other.dc = self.dc
        other.tk = self.tk
        other._tkstack = self._tkstack

    def tkClipBox(self, clipbox):
        if clipbox is not None:
            tmprev = svgtypes.TM(self.dc.GetWorldTransform())
            self.dc.SetWorldTransform(self.ctm.getElements())
            x, y, w, h = clipbox
            ltrb = x, y, x+w, y+h
            tm = svgtypes.TM(self.dc.GetWorldTransform())
            ltrb = tm.URtoDR(ltrb)
            self.dc.SetWorldTransform([1, 0, 0, 1, 0, 0])
            rgn = wingdi.CreateRectRgn(ltrb)
            self.dc.SelectClipRgn(rgn)
            rgn.DeleteObject()
            self.dc.SetWorldTransform(tmprev.getElements())

    #
    #  platform line art interface
    #
    def beginDraw(self, style, tflist):
        if tflist:
            tm = self.ctm.copy()
            tm.applyTfList(tflist)
            self.dc.SetWorldTransform(tm.getElements())

    def endDraw(self, style, tflist):
        # fill should be painted first, then the stroke, and then the marker symbols
        fill = self.getStyleAttr('fill', style)
        stroke = self.getStyleAttr('stroke', style)
        fillRule = self.getStyleAttr('fill-rule', style)

        # fill attrs
        brush = None
        rop = None
        if fill is not None and fill != 'none':
            contextFill = self.getStyleAttr('fill')
            if contextFill != fill:
                brush = wingdi.CreateSolidBrush(fill)
                brush = self.dc.SelectObject(brush)
            try:
                if stroke and stroke != 'none':
                    # keep path for stroke
                    dcid = self.dc.SaveDC()
                    if fillRule == 'nonzero':
                        self.dc.SetPolyFillMode(win32con.WINDING)
                    else:
                        self.dc.SetPolyFillMode(win32con.ALTERNATE)
                    self.dc.FillPath()
                    self.dc.RestoreDC(dcid)
                else:
                    if fillRule == 'nonzero':
                        self.dc.SetPolyFillMode(win32con.WINDING)
                    else:
                        self.dc.SetPolyFillMode(win32con.ALTERNATE)
                    self.dc.FillPath()
            except wingdi.error, arg:
                print arg,  style, tflist
            if brush:
                wingdi.DeleteObject(self.dc.SelectObject(brush))

        # stroke attrs
        pen = None
        strokeWidth = self.getStyleAttr('stroke-width', style)
        if stroke is not None and stroke!='none':
            contextStroke = self.getStyleAttr('stroke')
            contextStrokeWidth = self.getStyleAttr('stroke-width')
            strokeMiterlimit = self.getStyleAttr('stroke-miterlimit', style)
            if strokeMiterlimit:
                oldStrokeMiterlimit = self.dc.SetMiterLimit(strokeMiterlimit)
            if contextStroke != stroke or contextStrokeWidth != strokeWidth:
                pen = wingdi.ExtCreatePen(strokeWidth, stroke)
                pen = self.dc.SelectObject(pen)
            try:
                self.dc.StrokePath()
            except wingdi.error, arg:
                print arg,  style, tflist
            if pen:
                wingdi.DeleteObject(self.dc.SelectObject(pen))
            if strokeMiterlimit:
                self.dc.SetMiterLimit(oldStrokeMiterlimit)

        if tflist:
            self.dc.SetWorldTransform(self.ctm.getElements())

    def getDeviceRegion(self):
        dcid = self.dc.SaveDC()
        rgn = self.dc.PathToRegion()
        self.dc.RestoreDC(dcid)
        return rgn

    def drawRect(self, pos, size, rxy, style, tflist, a = 0):
        self.beginDraw(style, tflist)
        self.dc.BeginPath()
        ltrb = pos[0], pos[1], pos[0]+size[0], pos[1]+size[1]
        rx, ry = rxy
        if rx is None or ry is None:
            self.dc.Rectangle(ltrb)
        else:
            self.dc.RoundRect(ltrb, rxy)
        self.dc.EndPath()
        if a: rgn = self.getDeviceRegion()
        else: rgn = None
        self.endDraw(style, tflist)
        return rgn

    def drawCircle(self, center, r, style, tflist, a = 0):
        self.beginDraw(style, tflist)
        self.dc.BeginPath()
        ltrb = center[0]-r, center[1]-r, center[0]+r, center[1]+r
        self.dc.Ellipse(ltrb)
        self.dc.EndPath()
        if a: rgn = self.getDeviceRegion()
        else: rgn = None
        self.endDraw(style, tflist)
        return rgn

    def drawEllipse(self, center, rxy, style, tflist, a = 0):
        self.beginDraw(style, tflist)
        self.dc.BeginPath()
        ltrb = center[0]-rxy[0], center[1]-rxy[1], center[0]+rxy[0], center[1]+rxy[1]
        self.dc.Ellipse(ltrb)
        self.dc.EndPath()
        if a: rgn = self.getDeviceRegion()
        else: rgn = None
        self.endDraw(style, tflist)
        return rgn

    def drawLine(self, pt1, pt2, style, tflist, a = 0):
        self.beginDraw(style, tflist)
        self.dc.BeginPath()
        self.dc.MoveToEx(pt1)
        self.dc.LineTo(pt2)
        self.dc.EndPath()
        self.endDraw(style, tflist)

    def drawPolyline(self, points, style, tflist, a = 0):
        self.beginDraw(style, tflist)
        self.dc.BeginPath()
        self.dc.Polyline(points)
        self.dc.EndPath()
        self.endDraw(style, tflist)

    def drawPolygon(self, points, style, tflist, a = 0):
        self.beginDraw(style, tflist)
        self.dc.BeginPath()
        self.dc.Polygon(points)
        self.dc.EndPath()
        if a: rgn = self.getDeviceRegion()
        else: rgn = None
        self.endDraw(style, tflist)
        return rgn

    def drawText(self, text, pos, style, tflist, a = 0):
        if tflist:
            tm = self.ctm.copy()
            tm.applyTfList(tflist)
            self.dc.SetWorldTransform(tm.getElements())

        font = None
        fontFamily = self.getStyleAttr('font-family', style)
        fontSize = self.getStyleAttr('font-size', style)
        if fontFamily is not None:
            contextFontFamily = self.getStyleAttr('font-family')
            contextFontSize = self.getStyleAttr('font-size')
            if contextFontFamily != fontFamily or contextFontSize != fontSize:
                fontSizeObj = self.getStyleAttrObj('font-size', style)
                dsize =  fontSize # fontSizeObj.getDeviceValue(self.ctm, 'h')
                font = wingdi.CreateFontIndirect({'name': fontFamily, 'height':dsize, 'outprecision':win32con.OUT_OUTLINE_PRECIS})
                self.dc.SelectObject(font)

        fill = self.getStyleAttr('fill', style)
        stroke = self.getStyleAttr('stroke', style)

        # whats the default?
        if fill is None and stroke is None:
            # text will be invisible
            # make it visible as black
            fill = 0, 0, 0
            oldcolor = self.dc.SetTextColor(fill)
            self.dc.TextOut(pos, text)
            self.dc.SetTextColor(oldcolor)

        elif fill is not None:
            oldcolor = self.dc.SetTextColor(fill)
            self.dc.TextOut(pos, text)
            self.dc.SetTextColor(oldcolor)

        pen = None
        strokeWidth = self.getStyleAttr('stroke-width', style)
        if stroke:
            # create path
            self.dc.BeginPath()
            self.dc.TextOut(pos, text)
            self.dc.EndPath()

            # stroke path
            contextStroke = self.getStyleAttr('stroke')
            contextStrokeWidth = self.getStyleAttr('stroke-width')
            if contextStroke != stroke or contextStrokeWidth != strokeWidth:
                pen = wingdi.ExtCreatePen(strokeWidth, stroke)
                pen = self.dc.SelectObject(pen)
            self.dc.StrokePath()
            if pen:
                wingdi.DeleteObject(self.dc.SelectObject(pen))

        if font:
            wingdi.DeleteObject(self.dc.SelectObject(font))
        if tflist:
            self.dc.SetWorldTransform(self.ctm.getElements())

    def computeArcCenter(self, x1, y1, rx, ry, a, x2, y2, fa, fs):
        cos = math.cos(a)
        sin = math.sin(a)
        x1p, y1p = 0.5*(x1-x2)*cos + 0.5*(y1-y2)*sin, -0.5*sin*(x1-x2)+0.5*cos*(y1-y2)

        rx2, ry2 = rx*rx, ry*ry
        x1p2, y1p2 = x1p*x1p, y1p*y1p
        r2 = x1p2/float(rx2) + y1p2/float(ry2)
        if r2>1:
            rx, ry = math.sqrt(r2)*rx, math.sqrt(r2)*ry
            rx2, ry2 = rx*rx, ry*ry
        sq2 = (rx2*ry2 - rx2*y1p2 -ry2*x1p2)/(rx2*y1p2+ry2*x1p2)
        if sq2 < 0: sq2 = 0.0
        sq = math.sqrt(sq2)
        if fa == fs: sq = -sq
        cxp, cyp = sq*rx*y1p/float(ry), -sq*ry*x1p/float(rx)
        cx, cy = cxp*cos - cyp*sin + 0.5*(x1+x2), cxp*sin + cyp*cos + 0.5*(y1+y2)
        return cx, cy

    def saveTk(self):
        assert self.tk.saveid != 0, 'invalid tk'
        self._tkstack.append(self.tk.getHandles())
        self.tk.reset()

    def restoreTk(self):
        assert len(self._tkstack)>0, 'unpaired save/restore tk'
        self.tk.setHandles(self._tkstack.pop())

    def drawPath(self, path, style, tflist, a = 0):
        self.beginDraw(style, tflist)

        prec = path.getPrecision()
        if prec>=3:
            scale = 0.001
            saround = self.scale1000AndRound
        elif prec==2:
            scale = 0.01
            saround = self.scale100AndRound
        elif prec==1:
            scale = 0.1
            saround = self.scale10AndRound
        elif prec==0:
            scale = 1.0
            saround = self.scale1AndRound

        self.dc.BeginPath()
        oldtf = self.dc.GetWorldTransform()
        tm = svgtypes.TM(oldtf)
        tm.scale([scale, scale])
        self.dc.SetWorldTransform(tm.getElements())
        self.drawPathSegList(path._pathSegList, saround)
        self.dc.EndPath()
        self.dc.SetWorldTransform(oldtf)

        self.endDraw(style, tflist)

    def scale1000AndRound(self, x):
        return int(math.floor(1000.0*x + 0.5))
    def scale100AndRound(self, x):
        return int(math.floor(100.0*x + 0.5))
    def scale10AndRound(self, x):
        return int(math.floor(10.0*x + 0.5))
    def scale1AndRound(self, x):
        return int(x) # x is actually an int

    # XXX: use PolyDraw to speed up
    def drawPathSegList(self, pathSegList, saround):
        PathSeg = svgtypes.PathSeg
        lastX = 0
        lastY = 0
        lastC = None
        isstart = 1
        for seg in pathSegList:
            if isstart:
                badCmds = 'HhVvZz'
                if badCmds.find(seg.getTypeAsLetter())>=0:
                    print 'ignoring cmd ', seg.getTypeAsLetter()
                    continue
                if badCmds.find(seg.getTypeAsLetter())<0:
                    if seg._type != PathSeg.SVG_PATHSEG_MOVETO_ABS and \
                            seg._type != PathSeg.SVG_PATHSEG_MOVETO_REL:
                        print 'assuming abs moveto'
                    if seg._type == PathSeg.SVG_PATHSEG_MOVETO_REL:
                        lastX, lastY = lastX + seg._x, lastY + seg._y
                        self.dc.MoveToEx((saround(lastX), saround(lastY)))
                    else:
                        lastX, lastY = seg._x, seg._y
                        self.dc.MoveToEx((saround(lastX), saround(lastY)))
                isstart = 0
            else:
                if seg._type == PathSeg.SVG_PATHSEG_CLOSEPATH:
                    self.dc.CloseFigure()
                    lastX = 0
                    lastY = 0
                    lastC = None
                    isstart = 1

                elif seg._type == PathSeg.SVG_PATHSEG_MOVETO_ABS:
                    lastX, lastY = seg._x, seg._y
                    lastC = None
                    self.dc.MoveToEx((saround(lastX), saround(lastY)))

                elif seg._type == PathSeg.SVG_PATHSEG_MOVETO_REL:
                    if seg._x != 0 or seg._y != 0:
                        lastX, lastY = lastX + seg._x, lastY + seg._y
                        lastC = None
                        self.dc.MoveToEx((saround(lastX), saround(lastY)))

                elif seg._type == PathSeg.SVG_PATHSEG_LINETO_ABS:
                    if seg._x != lastX or seg._y != lastY:
                        lastX, lastY = seg._x, seg._y
                        lastC = None
                        self.dc.LineTo((saround(seg._x), saround(seg._y)))

                elif seg._type == PathSeg.SVG_PATHSEG_LINETO_REL:
                    lastX, lastY = lastX + seg._x, lastY + seg._y
                    lastC = None
                    self.dc.LineTo((saround(lastX), saround(lastY)))

                elif seg._type == PathSeg.SVG_PATHSEG_LINETO_HORIZONTAL_ABS:
                    lastX = seg._x
                    lastC = None
                    self.dc.LineTo((saround(lastX), saround(lastY)))

                elif seg._type == PathSeg.SVG_PATHSEG_LINETO_HORIZONTAL_REL:
                    lastX = lastX + seg._x
                    lastC = None
                    self.dc.LineTo((saround(lastX), saround(lastY)))

                elif seg._type == PathSeg.SVG_PATHSEG_LINETO_VERTICAL_ABS:
                    lastY = seg._y
                    lastC = None
                    self.dc.LineTo((saround(lastX), saround(lastY)))

                elif seg._type == PathSeg.SVG_PATHSEG_LINETO_VERTICAL_REL:
                    lastY = lastY + seg._y
                    lastC = None
                    self.dc.LineTo((saround(lastX), saround(lastY)))

                elif seg._type == PathSeg.SVG_PATHSEG_CURVETO_CUBIC_ABS:
                    x1, y1, x2, y2, x, y = seg._x1, seg._y1, seg._x2, seg._y2, seg._x, seg._y
                    bl = [(saround(x1),saround(y1)), (saround(x2),saround(y2)), (saround(x),saround(y))]
                    self.dc.PolyBezierTo(bl)
                    lastC = seg._x2,seg._y2
                    lastX, lastY = seg._x, seg._y

                elif seg._type == PathSeg.SVG_PATHSEG_CURVETO_CUBIC_REL:
                    x1, y1, x2, y2, x, y = lastX + seg._x1, lastY + seg._y1, lastX + seg._x2, lastY + seg._y2, lastX + seg._x, lastY + seg._y
                    bl = [(saround(x1),saround(y1)), (saround(x2),saround(y2)), (saround(x),saround(y))]
                    self.dc.PolyBezierTo(bl)
                    lastC = lastX + seg._x2,lastY + seg._y2
                    lastX, lastY = lastX + seg._x,lastY + seg._y

                elif seg._type == PathSeg.SVG_PATHSEG_CURVETO_CUBIC_SMOOTH_ABS:
                    if lastC is None:
                        lastC = lastX, lastY
                    x1, y1 = 2*lastX - lastC[0], 2*lastY - lastC[1]
                    bl = [(saround(x1), saround(y1)),(saround(seg._x2), saround(seg._y2)),(saround(seg._x), saround(seg._y))]
                    self.dc.PolyBezierTo(bl)
                    lastC = seg._x2, seg._y2
                    lastX, lastY = seg._x, seg._y

                elif seg._type == PathSeg.SVG_PATHSEG_CURVETO_CUBIC_SMOOTH_REL:
                    if lastC is None:
                        lastC = lastX, lastY
                    x1, y1 = 2*lastX - lastC[0], 2*lastY - lastC[1]
                    bl = [(saround(x1), saround(y1)),(saround(lastX + seg._x2), saround(lastY + seg._y2)),(saround(lastX + seg._x), saround(lastY + seg._y))]
                    self.dc.PolyBezierTo(bl)
                    lastC = lastX + seg._x2, lastY + seg._y2
                    lastX, lastY = lastX + seg._x, lastY + seg._y

                elif seg._type == PathSeg.SVG_PATHSEG_CURVETO_QUADRATIC_ABS:
                    bl = [(saround(lastX), saround(lastY)),(saround(seg._x1), saround(seg._y1)),(saround(seg._x), saround(seg._y))]
                    self.dc.PolyBezierTo(bl)
                    lastC = seg._x1, seg._y1
                    lastX, lastY = seg._x, seg._y

                elif seg._type == PathSeg.SVG_PATHSEG_CURVETO_QUADRATIC_REL:
                    bl = [(saround(lastX), saround(lastY)),(saround(lastX + seg._x1), saround(lastY + seg._y1)),(saround(lastX + seg._x), saround(lastY + seg._y))]
                    self.dc.PolyBezierTo(bl)
                    lastC = lastX + seg._x1, lastY + seg._y1
                    lastX, lastY = lastX + seg._x, lastY + seg._y

                elif seg._type == PathSeg.SVG_PATHSEG_CURVETO_QUADRATIC_SMOOTH_ABS:
                    if lastC is None:
                        lastC = lastX, lastY
                    nextC = 2*lastX - lastC[0], 2*lastY - lastC[1]
                    bl = [(saround(lastX), saround(lastY)),(saround(nextC[0]), saround(nextC[1])),(saround(seg._x), saround(seg._y))]
                    self.dc.PolyBezierTo(bl)
                    lastC = nextC
                    lastX, lastY = seg._x, seg._y

                elif seg._type == PathSeg.SVG_PATHSEG_CURVETO_QUADRATIC_SMOOTH_REL:
                    if lastC is None:
                        lastC = lastX, lastY
                    nextC = 2*lastX - lastC[0], 2*lastY - lastC[1]
                    bl = [(saround(lastX), saround(lastY)),(saround(nextC[0]), saround(nextC[1])),(saround(lastX+seg._x), saround(lastY+seg._y))]
                    self.dc.PolyBezierTo(bl)
                    lastC = nextC
                    lastX, lastY = lastX+seg._x, lastY+seg._y

                elif seg._type == PathSeg.SVG_PATHSEG_ARC_ABS:
                    angle = int(seg._angle)/360
                    angle = (angle/180.0)*math.pi
                    fa = seg._largeArcFlag
                    fs = seg._sweepFlag
                    r1, r2 = seg._r1, seg._r2
                    if r1<0: r1 = -r1
                    if r2<0: r2 = -r2
                    if r1 == 0 or r2 == 0:
                        self.dc.LineTo((saround(seg._x), saround(seg._y)))
                    else:
                        if fs:
                            olddir = self.dc.SetArcDirection(win32con.AD_CLOCKWISE)
                        else:
                            olddir = self.dc.SetArcDirection(win32con.AD_COUNTERCLOCKWISE)
                        cx, cy = self.computeArcCenter(lastX, lastY, r1, r2, angle, seg._x, seg._y, fa, fs)
                        if angle:
                            tm = svgtypes.TM()
                            tm.translate([cx, cy])
                            tm.rotate([angle])
                            tm.inverse()
                            x1, y1 = tm.UPtoDP((lastX, lastY))
                            x2, y2 = tm.UPtoDP((seg._x, seg._y))

                            oldtf = self.dc.GetWorldTransform()
                            tm = self.ctm.copy()
                            tm.applyTfList([('translate',[cx, cy]), ('rotate',[angle,]),])
                            self.dc.SetWorldTransform(tm.getElements())
                            rc = -r1, -r2, r1, r2
                            self.dc.Arc(rc, (x1, y1), (x2, y2))
                            self.dc.SetWorldTransform(oldtf)
                            self.dc.MoveToEx((saround(seg._x), saround(seg._y)))
                        else:
                            rc = cx-r1, cy-r2, cx+r1, cy+r2
                            x1, y1 = lastX, lastY
                            x2, y2 = seg._x, seg._y
                            self.dc.ArcTo(rc, (saround(x1), saround(y1)), (saround(x2), saround(y2)))
                        self.dc.SetArcDirection(olddir)
                    lastC = None
                    lastX, lastY = seg._x, seg._y

                elif seg._type == PathSeg.SVG_PATHSEG_ARC_REL:
                    angle = seg._angle
                    while angle < 0:
                        angle = angle + 360
                    while angle >= 360:
                        angle = angle - 360
                    angle = (angle/180.0)*math.pi
                    fa = seg._largeArcFlag
                    fs = seg._sweepFlag
                    r1, r2 = seg._r1, seg._r2
                    if r1<0: r1 = -r1
                    if r2<0: r2 = -r2
                    if r1 == 0 or r2 == 0:
                        self.dc.LineTo((saround(lastX + seg._x), saround(lastY + seg._y)))
                    else:
                        if fs:
                            olddir = self.dc.SetArcDirection(win32con.AD_CLOCKWISE)
                        else:
                            olddir = self.dc.SetArcDirection(win32con.AD_COUNTERCLOCKWISE)
                        cx, cy = self.computeArcCenter(lastX, lastY, r1, r2, angle, lastX + seg._x, lastY + seg._y, fa, fs)
                        if angle:
                            tm = svgtypes.TM()
                            tm.translate([cx, cy])
                            tm.rotate([angle])
                            tm.inverse()
                            x1, y1 = tm.UPtoDP((lastX, lastY))
                            x2, y2 = tm.UPtoDP((lastX + seg._x, lastY + seg._y))

                            oldtf = self.dc.GetWorldTransform()
                            tm = self.ctm.copy()
                            tm.applyTfList([('translate',[cx, cy]), ('rotate',[angle,]),])
                            self.dc.SetWorldTransform(tm.getElements())
                            rc = -r1, -r2, r1, r2
                            self.dc.Arc(rc, (saround(x1), saround(y1)), (saround(x2), saround(y2)))
                            self.dc.SetWorldTransform(oldtf)
                            self.dc.MoveToEx((saround(lastX + seg._x), saround(lastY + seg._y)))
                        else:
                            rc = cx-r1, cy-r2, cx+r1, cy+r2
                            x1, y1 = lastX, lastY
                            x2, y2 = lastX + seg._x, lastY + seg._y
                            self.dc.ArcTo(rc, (saround(x1), saround(y1)), (saround(x2), saround(y2)))
                        self.dc.SetArcDirection(olddir)
                    lastC = None
                    lastX, lastY = lastX + seg._x, lastY + seg._y


######################
class Tk:
    def __init__(self):
        self.pen = 0
        self.brush = 0
        self.font = 0
        self.saveid = 0 # previous SaveDC id

    def setDefaults(self):
        self.pen = wingdi.GetStockObject(win32con.BLACK_PEN)
        self.brush = wingdi.GetStockObject(win32con.WHITE_BRUSH)
        self.font = wingdi.GetStockObject(win32con.SYSTEM_FONT)

    def reset(self):
        self.pen, self.brush, self.font, self.saveid = 0, 0, 0, 0

    def getHandles(self):
        return self.pen, self.brush, self.font, self.saveid

    def setHandles(self, ht):
        self.pen, self.brush, self.font, self.saveid = ht
