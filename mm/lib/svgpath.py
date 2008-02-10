__version__ = '$Id$'

import string
import math
from fmtfloat import fmtfloat, round, trunc, getprec

class PathSeg:
    SVG_PATHSEG_UNKNOWN                      = 0
    SVG_PATHSEG_CLOSEPATH                    = 1
    SVG_PATHSEG_MOVETO_ABS                   = 2
    SVG_PATHSEG_MOVETO_REL                   = 3
    SVG_PATHSEG_LINETO_ABS                   = 4
    SVG_PATHSEG_LINETO_REL                   = 5
    SVG_PATHSEG_CURVETO_CUBIC_ABS            = 6
    SVG_PATHSEG_CURVETO_CUBIC_REL            = 7
    SVG_PATHSEG_CURVETO_QUADRATIC_ABS        = 8
    SVG_PATHSEG_CURVETO_QUADRATIC_REL        = 9
    SVG_PATHSEG_ARC_ABS                      = 10
    SVG_PATHSEG_ARC_REL                      = 11
    SVG_PATHSEG_LINETO_HORIZONTAL_ABS        = 12
    SVG_PATHSEG_LINETO_HORIZONTAL_REL        = 13
    SVG_PATHSEG_LINETO_VERTICAL_ABS          = 14
    SVG_PATHSEG_LINETO_VERTICAL_REL          = 15
    SVG_PATHSEG_CURVETO_CUBIC_SMOOTH_ABS     = 16
    SVG_PATHSEG_CURVETO_CUBIC_SMOOTH_REL     = 17
    SVG_PATHSEG_CURVETO_QUADRATIC_SMOOTH_ABS = 18
    SVG_PATHSEG_CURVETO_QUADRATIC_SMOOTH_REL = 19

    # order is important to current implementation
    commands = 'ZzMmLlCcQqAaHhVvSsTt'

    def __init__(self,segtype=''):
        self._x = 0
        self._y = 0
        self._x1 = 0
        self._y1 = 0
        self._x2 = 0
        self._y2 = 0
        self._r1 = 0
        self._r2 = 0
        self._angle = 0
        self._largeArcFlag = 0
        self._sweepFlag = 0
        self.setTypeFromLetter(segtype)

    def setType(self, seqtype):
        self._type = seqtype

    def getTypeAsLetter(self):
        if self._type == PathSeg.SVG_PATHSEG_UNKNOWN:
            return ''
        elif self._type==PathSeg.SVG_PATHSEG_CLOSEPATH:
            return 'z'
        elif self._type<=PathSeg.SVG_PATHSEG_CURVETO_QUADRATIC_SMOOTH_REL:
            return PathSeg.commands[self._type]
        else:
            return ''

    def setTypeFromLetter(self, letter):
        if not letter:
            self._type = PathSeg.SVG_PATHSEG_UNKNOWN
            return
        index = PathSeg.commands.find(letter)
        if index<0: self._type = PathSeg.SVG_PATHSEG_UNKNOWN
        elif letter == 'z' or letter == 'Z': self._type = PathSeg.SVG_PATHSEG_CLOSEPATH
        else: self._type = index

    def __repr__(self):
        t = self._type
        if t == PathSeg.SVG_PATHSEG_CLOSEPATH: return 'z'
        elif t == PathSeg.SVG_PATHSEG_MOVETO_ABS: return 'M %s %s' % (fmtfloat(self._x), fmtfloat(self._y))
        elif t == PathSeg.SVG_PATHSEG_MOVETO_REL: return 'm %s %s' % (fmtfloat(self._x), fmtfloat(self._y))
        elif t == PathSeg.SVG_PATHSEG_LINETO_ABS: return 'L %s %s' % (fmtfloat(self._x), fmtfloat(self._y))
        elif t == PathSeg.SVG_PATHSEG_LINETO_REL: return 'l %s %s' % (fmtfloat(self._x), fmtfloat(self._y))
        elif t == PathSeg.SVG_PATHSEG_CURVETO_CUBIC_ABS:
            return 'C %s %s %s %s %s %s' % (fmtfloat(self._x1), fmtfloat(self._y1),fmtfloat(self._x2), fmtfloat(self._y2), fmtfloat(self._x), fmtfloat(self._y))
        elif t == PathSeg.SVG_PATHSEG_CURVETO_CUBIC_REL:
            return 'c %s %s %s %s %s %s' % (fmtfloat(self._x1), fmtfloat(self._y1), fmtfloat(self._x2), fmtfloat(self._y2), fmtfloat(self._x), fmtfloat(self._y))
        elif t == PathSeg.SVG_PATHSEG_CURVETO_QUADRATIC_ABS:
            return 'Q %s %s %s %s %s %s' % (fmtfloat(self._x1), fmtfloat(self._y1), fmtfloat(self._x), fmtfloat(self._y))
        elif t == PathSeg.SVG_PATHSEG_CURVETO_QUADRATIC_REL:
            return 'q %s %s %s %s %s %s' % (fmtfloat(self._x1), fmtfloat(self._y1), fmtfloat(self._x), fmtfloat(self._y))
        elif t == PathSeg.SVG_PATHSEG_ARC_ABS:
            sweep = self._sweepFlag
            largeArc = self._largeArcFlag
            return 'A %s %s %s %d %d %s %s' % (fmtfloat(self._r1), fmtfloat(self._r2), fmtfloat(self._angle), largeArc, sweep, fmtfloat(self._x), fmtfloat(self._y))
        elif t == PathSeg.SVG_PATHSEG_ARC_REL:
            sweep = self._sweepFlag
            largeArc = self._largeArcFlag
            return 'a %s %s %s %d %d %s %s' % (fmtfloat(self._r1), fmtfloat(self._r2), fmtfloat(self._angle), largeArc, sweep, fmtfloat(self._x), fmtfloat(self._y))
        elif t == PathSeg.SVG_PATHSEG_LINETO_HORIZONTAL_ABS: return 'H %s' % fmtfloat(self._x)
        elif t == PathSeg.SVG_PATHSEG_LINETO_HORIZONTAL_REL: return 'h %s' % fmtfloat(self._x)
        elif t == PathSeg.SVG_PATHSEG_LINETO_VERTICAL_ABS: return 'V %s' % fmtfloat(self._y)
        elif t == PathSeg.SVG_PATHSEG_LINETO_VERTICAL_REL: return 'v %s' % fmtfloat(self._y)
        elif t == PathSeg.SVG_PATHSEG_CURVETO_CUBIC_SMOOTH_ABS:
            return 'S %s %s %s %s' % (fmtfloat(self._x2), fmtfloat(self._y2), fmtfloat(self._x), fmtfloat(self._y))
        elif t == PathSeg.SVG_PATHSEG_CURVETO_CUBIC_SMOOTH_REL:
            return 's %s %s %s %s' % ( fmtfloat(self._x2),  fmtfloat(self._y2),  fmtfloat(self._x),  fmtfloat(self._y))
        elif t == PathSeg.SVG_PATHSEG_CURVETO_QUADRATIC_SMOOTH_ABS:
            return 'T %s %s' % (fmtfloat(self._x), fmtfloat(self._y))
        elif t == PathSeg.SVG_PATHSEG_CURVETO_QUADRATIC_SMOOTH_REL:
            return 't %s %s' % (fmtfloat(self._x), fmtfloat(self._y))
        else:
            return ''

    def topxl(self):
        seg = PathSeg()
        seg._type = self._type
        seg._x = round(self._x)
        seg._y = round(self._y)
        seg._x1 = round(self._x1)
        seg._y1 = round(self._y1)
        seg._x2 = round(self._x2)
        seg._y2 = round(self._y2)
        seg._r1 = round(self._r1)
        seg._r2 = round(self._r2)
        seg._angle = self._angle
        seg._largeArcFlag  = self._largeArcFlag
        seg._sweepFlag  = self._sweepFlag
        return seg

    def translate(self, dx, dy):
        t = self._type
        if t == PathSeg.SVG_PATHSEG_MOVETO_ABS:
            self._x, self._y = self._x+dx, self._y+dy
        elif t == PathSeg.SVG_PATHSEG_LINETO_ABS:
            self._x, self._y = self._x+dx, self._y+dy
        elif t == PathSeg.SVG_PATHSEG_CURVETO_CUBIC_ABS:
            self._x1, self._y1 = self._x1+dx, self._y1+dy
            self._x2, self._y2 = self._x2+dx, self._y2+dy
            self._x, self._y = self._x+dx, self._y+dy
        elif t == PathSeg.SVG_PATHSEG_LINETO_HORIZONTAL_ABS:
            self._x = self._x+dx
        elif t == PathSeg.SVG_PATHSEG_LINETO_VERTICAL_ABS:
            self._y = self._y+dy

class SVGPath:
    def __init__(self,  node, attr, pathstr, defval=None):
        self._node = node
        self._attr = attr
        self._pathSegList = []
        self._prec = 0
        self.__constructors = {'z':self.__addClosePath,
                'm':self.__addMoveTo,
                'l':self.__addLineTo,
                'c':self.__addCurveTo,
                'q':self.__addQuadraticBezierCurveTo,
                'a':self.__addEllipticArc,
                'h':self.__addHorizontalLineTo,
                'v':self.__addVerticalLineTo,
                's':self.__addSmoothCurveTo,
                't':self.__addTruetypeQuadraticBezierCurveTo,
                }
        if pathstr:
            self.constructPathSegList(pathstr)

    def __repr__(self):
        s = ''
        first = 1
        lasttype = None
        for seg in self._pathSegList:
            if first:
                s = repr(seg)
                first = 0
            else:
                if lasttype and seg._type == lasttype:
                    s = s + ' ' + repr(seg)[2:]
                else:
                    s = s + ' ' + repr(seg)
                    lasttype = seg._type
        return s

    def clone(self):
        new = SVGPath(self._node, None, None)
        new._pathSegList = self._pathSegList[:]
        return new

    # required by all svgtypes
    def getValue(self):
        return self

    # required by all svgtypes
    def isDefault(self):
        return self._pathSegList is None or len(self._pathSegList)==0

    def evaluatePrec(self, token):
        self._prec = max(self._prec, getprec(token))

    def getPrecision(self):
        return self._prec

    # main method
    # create a path from a string description
    def constructPathSegList(self, pathstr):
        self._pathSegList = []
        commands = PathSeg.commands
        st = StringTokenizer(pathstr, commands)
        while st.hasMoreTokens():
            cmd = st.nextToken()
            while commands.find(cmd) < 0 and st.hasMoreTokens():
                cmd = st.nextToken()
            if commands.find(cmd) >= 0:
                if cmd == 'z' or cmd == 'Z':
                    self.__addCommand(cmd, None)
                else:
                    if st.hasMoreTokens():
                        params = st.nextToken()
                        self.__addCommand(cmd, params)

    def __addCommand(self, cmd, params):
        lcmd = cmd.lower()
        method = self.__constructors.get(lcmd)
        if method:
            apply(method, (cmd, params))
        else:
            raise AssertionError, 'Invalid path command'

    def __addClosePath(self, cmd, params):
        self._pathSegList.append(PathSeg('z'))

    def __addMoveTo(self, cmd, params):
        absolute = (cmd=='M')
        params = params.strip()
        self.__strip(params,',')
        delims = ' ,-\n\t\r'
        st = StringTokenizer(params, delims)
        counter = 0
        while st.hasMoreTokens():
            token = self.__getNextToken(st, delims, '0')
            x = string.atof(token)
            self.evaluatePrec(token)
            token = self.__getNextToken(st, delims, '0')
            y = string.atof(token)
            self.evaluatePrec(token)
            seg = PathSeg()
            seg._x = x
            seg._y = y
            if counter==0:
                if absolute: seg.setType(PathSeg.SVG_PATHSEG_MOVETO_ABS)
                else: seg.setType(PathSeg.SVG_PATHSEG_MOVETO_REL)
            else:
                if absolute: seg.setType(PathSeg.SVG_PATHSEG_LINETO_ABS)
                else: seg.setType(PathSeg.SVG_PATHSEG_LINETO_REL)
            self._pathSegList.append(seg)
            counter = counter + 1

    def __addLineTo(self, cmd, params):
        absolute = (cmd=='L')
        params = params.strip()
        self.__strip(params,',')
        delims = ' ,-\n\t\r'
        st = StringTokenizer(params, delims)
        while st.hasMoreTokens():
            token = self.__getNextToken(st, delims, '0')
            x = string.atof(token)
            self.evaluatePrec(token)
            token = self.__getNextToken(st, delims, '0')
            y = string.atof(token)
            self.evaluatePrec(token)
            seg = PathSeg()
            seg._x = x
            seg._y = y
            if absolute: seg.setType(PathSeg.SVG_PATHSEG_LINETO_ABS)
            else: seg.setType(PathSeg.SVG_PATHSEG_LINETO_REL)
            self._pathSegList.append(seg)

    def __addCurveTo(self, cmd, params):
        absolute = (cmd=='C')
        params = params.strip()
        self.__strip(params,',')
        delims = ' ,-\n\t\r'
        st = StringTokenizer(params, delims)
        while st.hasMoreTokens():
            token = self.__getNextToken(st, delims, '0')
            x1 = string.atof(token)
            self.evaluatePrec(token)
            token = self.__getNextToken(st, delims, '0')
            y1 = string.atof(token)
            self.evaluatePrec(token)
            token = self.__getNextToken(st, delims, '0')
            x2 = string.atof(token)
            self.evaluatePrec(token)
            token = self.__getNextToken(st, delims, '0')
            y2 = string.atof(token)
            self.evaluatePrec(token)
            token = self.__getNextToken(st, delims, '0')
            x = string.atof(token)
            self.evaluatePrec(token)
            token = self.__getNextToken(st, delims, '0')
            y = string.atof(token)
            self.evaluatePrec(token)
            seg = PathSeg()
            seg._x1 = x1
            seg._y1 = y1
            seg._x2 = x2
            seg._y2 = y2
            seg._x = x
            seg._y = y
            if absolute: seg.setType(PathSeg.SVG_PATHSEG_CURVETO_CUBIC_ABS)
            else: seg.setType(PathSeg.SVG_PATHSEG_CURVETO_CUBIC_REL)
            self._pathSegList.append(seg)

    def __addSmoothCurveTo(self, cmd, params):
        absolute = (cmd=='S')
        params = params.strip()
        self.__strip(params,',')
        delims = ' ,-\n\t\r'
        st = StringTokenizer(params, delims)
        while st.hasMoreTokens():
            token = self.__getNextToken(st, delims, '0')
            x2 = string.atof(token)
            self.evaluatePrec(token)
            token = self.__getNextToken(st, delims, '0')
            y2 = string.atof(token)
            self.evaluatePrec(token)
            token = self.__getNextToken(st, delims, '0')
            x = string.atof(token)
            self.evaluatePrec(token)
            token = self.__getNextToken(st, delims, '0')
            y = string.atof(token)
            self.evaluatePrec(token)
            seg = PathSeg()
            seg._x2 = x2
            seg._y2 = y2
            seg._x = x
            seg._y = y
            if absolute: seg.setType(PathSeg.SVG_PATHSEG_CURVETO_CUBIC_SMOOTH_ABS)
            else: seg.setType(PathSeg.SVG_PATHSEG_CURVETO_CUBIC_SMOOTH_REL)
            self._pathSegList.append(seg)

    def __addHorizontalLineTo(self, cmd, params):
        absolute = (cmd=='H')
        params = params.strip()
        self.__strip(params,',')
        delims = ' ,-\n\t\r'
        st = StringTokenizer(params, delims)
        while st.hasMoreTokens():
            token = self.__getNextToken(st, delims, '0')
            x = string.atof(token)
            self.evaluatePrec(token)
            seg = PathSeg()
            seg._x = x
            if absolute: seg.setType(PathSeg.SVG_PATHSEG_LINETO_HORIZONTAL_ABS)
            else: seg.setType(PathSeg.SVG_PATHSEG_LINETO_HORIZONTAL_REL)
            self._pathSegList.append(seg)

    def __addVerticalLineTo(self, cmd, params):
        absolute = (cmd=='V')
        params = params.strip()
        self.__strip(params,',')
        delims = ' ,-\n\t\r'
        st = StringTokenizer(params, delims)
        while st.hasMoreTokens():
            token = self.__getNextToken(st, delims, '0')
            y = string.atof(token)
            self.evaluatePrec(token)
            seg = PathSeg()
            seg._y = y
            if absolute: seg.setType(PathSeg.SVG_PATHSEG_LINETO_VERTICAL_ABS)
            else: seg.setType(PathSeg.SVG_PATHSEG_LINETO_VERTICAL_REL)
            self._pathSegList.append(seg)

    def __addEllipticArc(self, cmd, params):
        absolute = (cmd=='A')
        params = params.strip()
        self.__strip(params,',')
        delims = ' ,-\n\t\r'
        st = StringTokenizer(params, delims)
        while st.hasMoreTokens():
            # r1,r2,angle,largeArc,sweep,x,y
            token = self.__getNextToken(st, delims, '0')
            r1 = string.atof(token)
            self.evaluatePrec(token)
            token = self.__getNextToken(st, delims, '0')
            r2 = string.atof(token)
            self.evaluatePrec(token)
            token = self.__getNextToken(st, delims, '0')
            a = string.atof(token)
            token = self.__getNextToken(st, delims, '0')
            large = string.atoi(token)
            token = self.__getNextToken(st, delims, '0')
            sweep = string.atoi(token)
            token = self.__getNextToken(st, delims, '0')
            x = string.atof(token)
            token = self.__getNextToken(st, delims, '0')
            y = string.atof(token)
            seg = PathSeg()
            seg._r1 = r1
            seg._r2 = r2
            seg._angle = a
            seg._largeArcFlag = large
            seg._sweepFlag = sweep
            seg._x = x
            seg._y = y
            if absolute: seg.setType(PathSeg.SVG_PATHSEG_ARC_ABS)
            else: seg.setType(PathSeg.SVG_PATHSEG_ARC_REL)
            self._pathSegList.append(seg)

    def __addQuadraticBezierCurveTo(self, cmd, params):
        absolute = (cmd=='Q')
        params = params.strip()
        self.__strip(params,',')
        delims = ' ,-\n\t\r'
        st = StringTokenizer(params, delims)
        while st.hasMoreTokens():
            token = self.__getNextToken(st, delims, '0')
            x1 = string.atof(token)
            self.evaluatePrec(token)
            token = self.__getNextToken(st, delims, '0')
            y1 = string.atof(token)
            self.evaluatePrec(token)
            token = self.__getNextToken(st, delims, '0')
            x = string.atof(token)
            self.evaluatePrec(token)
            token = self.__getNextToken(st, delims, '0')
            y = string.atof(token)
            self.evaluatePrec(token)
            seg = PathSeg()
            seg._x1 = x1
            seg._y1 = y1
            seg._x = x
            seg._y = y
            if absolute: seg.setType(PathSeg.SVG_PATHSEG_CURVETO_QUADRATIC_ABS)
            else: seg.setType(PathSeg.SVG_PATHSEG_CURVETO_QUADRATIC_REL)
            self._pathSegList.append(seg)

    def __addTruetypeQuadraticBezierCurveTo(self, cmd, params):
        absolute = (cmd=='T')
        params = params.strip()
        self.__strip(params,',')
        delims = ' ,-\n\t\r'
        st = StringTokenizer(params, delims)
        while st.hasMoreTokens():
            token = self.__getNextToken(st, delims, '0')
            x = string.atof(token)
            self.evaluatePrec(token)
            token = self.__getNextToken(st, delims, '0')
            y = string.atof(token)
            self.evaluatePrec(token)
            seg = PathSeg()
            seg._x = x
            seg._y = y
            if absolute: seg.setType(PathSeg.SVG_PATHSEG_CURVETO_QUADRATIC_SMOOTH_ABS)
            else: seg.setType(PathSeg.SVG_PATHSEG_CURVETO_QUADRATIC_SMOOTH_REL)
            self._pathSegList.append(seg)

    def __strip(self, params, ch):
        ret = params
        while ret[0]==ch:ret = ret[1:]
        while ret[-1]==ch:ret = ret[:-1]

    def __getNextToken(self, st, delims, default):
        neg = 0
        try:
            token = st.nextToken()
            while st.hasMoreTokens() and delims.find(token)>=0:
                if token == '-': neg = 1
                else: neg = 0
                token = st.nextToken()
            if delims.find(token) >=0:
                token = default
        except:
            token = default
        if neg: token = '-' + token
        if token[-1]=='e' or token[-1]=='E':
            try:
                e = st.nextToken()
                e = e + st.nextToken()
                token = token + e
            except:
                token = token + '0'
        return token


    def createPath(self, path):
        points = []
        lastX = 0
        lastY = 0
        lastC = None
        startP = None
        isstart = 1
        for seg in self._pathSegList:
            if isstart:
                badCmds = 'HhVvZz'
                while badCmds.find(seg.getTypeAsLetter())>=0 and i<n:
                    print 'ignoring cmd ', seg.getTypeAsLetter()
                    continue
                if badCmds.find(seg.getTypeAsLetter())<0:
                    if seg._type != PathSeg.SVG_PATHSEG_MOVETO_ABS and \
                            seg._type != PathSeg.SVG_PATHSEG_MOVETO_REL:
                        print 'assuming abs moveto'
                    if seg._type == PathSeg.SVG_PATHSEG_MOVETO_REL:
                        lastX, lastY = lastX + seg._x, lastY + seg._y
                        startP = (lastX, lastY)
                        points.append(startP)
                        path.moveTo(startP)
                    else:
                        lastX, lastY = seg._x, seg._y
                        startP = (lastX, lastY)
                        points.append(startP)
                        path.moveTo(startP)
                isstart = 0
            else:
                if seg._type == PathSeg.SVG_PATHSEG_CLOSEPATH:
                    if startP:
                        lastX, lastY = startP
                        points.append(startP)
                        startP = None
                    lastC = None
                    isstart = 1
                    path.closePath()

                elif seg._type == PathSeg.SVG_PATHSEG_MOVETO_ABS:
                    lastX, lastY = seg._x, seg._y
                    points.append((lastX, lastY))
                    lastC = None
                    path.moveTo((lastX, lastY))

                elif seg._type == PathSeg.SVG_PATHSEG_MOVETO_REL:
                    lastX, lastY = lastX + seg._x, lastY + seg._y
                    points.append((lastX, lastY))
                    lastC = None
                    path.moveTo((lastX, lastY))

                elif seg._type == PathSeg.SVG_PATHSEG_LINETO_ABS:
                    lastX, lastY = seg._x, seg._y
                    points.append((lastX, lastY))
                    lastC = None
                    path.lineTo((lastX, lastY))

                elif seg._type == PathSeg.SVG_PATHSEG_LINETO_REL:
                    lastX, lastY = lastX + seg._x, lastY + seg._y
                    points.append((lastX, lastY))
                    lastC = None
                    path.lineTo((lastX, lastY))

                elif seg._type == PathSeg.SVG_PATHSEG_LINETO_HORIZONTAL_ABS:
                    lastX = seg._x
                    points.append((lastX, lastY))
                    lastC = None
                    path.lineTo((lastX, lastY))

                elif seg._type == PathSeg.SVG_PATHSEG_LINETO_HORIZONTAL_REL:
                    lastX = lastX + seg._x
                    points.append((lastX, lastY))
                    lastC = None
                    path.lineTo((lastX, lastY))

                elif seg._type == PathSeg.SVG_PATHSEG_LINETO_VERTICAL_ABS:
                    lastY = seg._y
                    points.append((lastX, lastY))
                    lastC = None
                    path.lineTo((lastX, lastY))

                elif seg._type == PathSeg.SVG_PATHSEG_LINETO_VERTICAL_REL:
                    lastY = lastY + seg._y
                    points.append((lastX, lastY))
                    lastC = None
                    path.lineTo((lastX, lastY))

                elif seg._type == PathSeg.SVG_PATHSEG_CURVETO_CUBIC_ABS:
                    path.curveTo((seg._x1, seg._y1), (seg._x2, seg._y2), (seg._x, seg._y))
                    lastC = seg._x2, seg._y2
                    lastX, lastY = seg._x, seg._y
                    points.append((lastX, lastY))

                elif seg._type == PathSeg.SVG_PATHSEG_CURVETO_CUBIC_REL:
                    path.curveTo((lastX + seg._x1, lastY + seg._y1),(lastX + seg._x2,lastY + seg._y2),(lastX + seg._x,lastY + seg._y))
                    lastC = lastX + seg._x2,lastY + seg._y2
                    lastX, lastY = lastX + seg._x,lastY + seg._y
                    points.append((lastX, lastY))

                elif seg._type == PathSeg.SVG_PATHSEG_CURVETO_CUBIC_SMOOTH_ABS:
                    if lastC is None:
                        lastC = lastX, lastY
                    x1, y1 = 2*lastX - lastC[0], 2*lastY - lastC[2]
                    path.curveTo((x1, y1),(seg._x2, seg._y2),(seg._x, seg._y))
                    lastC = seg._x2, seg._y2
                    lastX, lastY = seg._x, seg._y
                    points.append((lastX, lastY))

                elif seg._type == PathSeg.SVG_PATHSEG_CURVETO_CUBIC_SMOOTH_REL:
                    if lastC is None:
                        lastC = lastX, lastY
                    x1, y1 = 2*lastX - lastC[0], 2*lastY - lastC[2]
                    path.curveTo((x1, y1),(lastX + seg._x2, lastY + seg._y2),(lastX + seg._x, lastY + seg._y))
                    lastC = lastX + seg._x2, lastY + seg._y2
                    lastX, lastY = lastX + seg._x, lastY + seg._y
                    points.append((lastX, lastY))

                elif seg._type == PathSeg.SVG_PATHSEG_CURVETO_QUADRATIC_ABS:
                    path.quadTo((seg._x1, seg._y1), (seg._x, seg._y))
                    lastC = seg._x1, seg._y1
                    lastX, lastY = seg._x, seg._y
                    points.append((lastX, lastY))

                elif seg._type == PathSeg.SVG_PATHSEG_CURVETO_QUADRATIC_REL:
                    path.quadTo((lastX + seg._x1, lastY + seg._y1), (lastX + seg._x, lastY + seg._y))
                    lastC = lastX + seg._x1, lastY + seg._y1
                    lastX, lastY = lastX + seg._x, lastY + seg._y
                    points.append((lastX, lastY))

                elif seg._type == PathSeg.SVG_PATHSEG_CURVETO_QUADRATIC_SMOOTH_ABS:
                    if lastC is None:
                        lastC = lastX, lastY
                    nextC = 2*lastX - lastC[0], 2*lastY - lastC[1]
                    path.quadTo(nextC, (seg._x, seg._y))
                    lastC = nextC
                    lastX, lastY = seg._x, seg._y
                    points.append((lastX, lastY))

                elif seg._type == PathSeg.SVG_PATHSEG_CURVETO_QUADRATIC_SMOOTH_REL:
                    if lastC is None:
                        lastC = lastX, lastY
                    nextC = 2*lastX - lastC[0], 2*lastY - lastC[1]
                    path.quadTo(nextC, (lastX+seg._x, lastY+seg._y))
                    lastC = nextC
                    lastX, lastY = lastX+seg._x, lastY+seg._y
                    points.append((lastX, lastY))

                elif seg._type == PathSeg.SVG_PATHSEG_ARC_ABS:
                    angle = ((trunc(seg._angle)/360)/180.0)*math.pi
                    arcFlag = seg._largeArcFlag
                    sweepFlag = seg._sweepFlag
                    r1, r2 = seg._r1, seg._r2
                    if r1<0: r1 = -r1
                    if r2<0: r2 = -r2
                    if r1 == 0 or r2 == 0:
                        path.lineTo(seg._x, seg._y)
                    else:
                        path.arcTo((lastX, lastY), (seg._x, seg._y), r1, r2, angle, arcFlag, sweepFlag)
                    lastC = None
                    lastX, lastY = seg._x, seg._y
                    points.append((lastX, lastY))

                elif seg._type == PathSeg.SVG_PATHSEG_ARC_REL:
                    angle = ((trunc(seg._angle)/360)/180.0)*math.pi
                    arcFlag = seg._largeArcFlag
                    sweepFlag = seg._sweepFlag
                    r1, r2 = seg._r1, seg._r2
                    if r1<0: r1 = -r1
                    if r2<0: r2 = -r2
                    if r1 == 0 or r2 == 0:
                        path.lineTo(lastX + seg._x, lastY + seg._y)
                    else:
                        path.arcTo((lastX, lastY), (lastX + seg._x, lastY + seg._y), r1, r2, angle, arcFlag, sweepFlag)
                    lastC = None
                    lastX, lastY = lastX + seg._x, lastY + seg._y
                    points.append((lastX, lastY))
        return points


class StringTokenizer:
    def __init__(self, str, delim=' \t\n\r\f'):
        self.__str = str
        self.__delim = delim
        self.__pos = 0
        self.__maxpos = len(str)
    def hasMoreTokens(self):
        return (self.__pos < self.__maxpos)
    def nextToken(self):
        if self.__pos >= self.__maxpos:
            raise AssertionError
        start = self.__pos
        while self.__pos < self.__maxpos and self.__delim.find(self.__str[self.__pos])<0:
            self.__pos = self.__pos + 1
        if start == self.__pos and self.__delim.find(self.__str[self.__pos])>=0:
            self.__pos = self.__pos + 1
        return self.__str[start:self.__pos]

def tocomplex(pt):
    return complex(pt[0],pt[1])


class Path:
    SEG_MOVETO = 0
    SEG_LINETO = 1
    SEG_QUADTO = 2
    SEG_CUBICTO = 3
    SEG_CLOSE = 4

    def __init__(self, pathstr=''):
        self.__ptTypes = []  # types of linearized segments
        self.__ptCoords = [] # points of linearized segments

        self.__svgpath = None # the SVG path instance

        self.__segTypes = []  # types of SVG segments
        self.__segCoords = [] # points of SVG segments

        self.__length = 0
        self.__lenValues = [0,] # curve in parametric form

        if pathstr:
            self.__svgpath = SVGPath(None, None, pathstr)
            self.__svgpath.createPath(self)
            self.__length = self.__getLength()

    def constructFromSVGPathString(self, pathstr):
        self.__svgpath = SVGPath(None, None, pathstr)
        self._points = self.__svgpath.createPath(self)
        #self.__length = self.__getLength()

    def constructFromPoints(self, coords):
        n = len(coords)
        if n==0: return
        self.moveTo(coords[0])
        for i in range(1,n):
            self.lineTo(coords[i])
        #self.__length = self.__getLength()

    def getLengthValues(self):
        return self.__lenValues

    def getPoints(self):
        points = []
        n = len(self.__segCoords)
        if n==0: return points
        x, y = self.__segCoords[0]
        points.append(complex(x,y))
        for i in range(1,n):
            if self.__segTypes[i] != Path.SEG_MOVETO:
                x, y = self.__segCoords[i]
                points.append(complex(x,y))
        assert(len(points)==len(self.__lenValues))
        return points

    def getNumOfSegments(self):
        return len(self.__lenValues)-1

    def getSegment(self, index):
        ptlast = pt  = complex(0, 0)
        segtype = Path.SEG_LINETO
        segcounter = 0
        for i in range(len(self.__segCoords)):
            if self.__segTypes[i] == Path.SEG_MOVETO:
                x, y = self.__segCoords[i]
                pt = complex(x, y)
            elif self.__segTypes[i] == Path.SEG_LINETO:
                x, y = self.__segCoords[i]
                pt = complex(x, y)
                segtype = Path.SEG_LINETO
                if segcounter == index: break
                segcounter = segcounter + 1
            elif self.__segTypes[i] == Path.SEG_CUBICTO:
                x, y = self.__segCoords[i]
                pt = complex(x, y)
                segtype = Path.SEG_CUBICTO
                if segcounter == index: break
                segcounter = segcounter + 1
            ptlast = pt
        return ptlast, pt, segtype

    def translate(self, dx, dy):
        if self.__svgpath:
            for seg in self.__svgpath._pathSegList:
                seg.translate(dx, dy)
        coords = self.__ptCoords[:]
        self.__ptCoords = []
        for x, y in coords:
            self.__ptCoords.append((x+dx,y+dy))

    # main query method
    # get point at length s
    def getPointAtLength(self, s):
        n = len(self.__ptTypes)
        if n==0: return complex(0, 0)
        elif n==1: return tocomplex(self.__ptCoords[0])
        if s<=0: return tocomplex(self.__ptCoords[0])
        elif s>=self.__length: return tocomplex(self.__ptCoords[n-1])

        d = 0.0
        xq, yq = self.__ptCoords[0]
        for i in range(n):
            if self.__ptTypes[i] == Path.SEG_MOVETO:
                xp, yp =        self.__ptCoords[i]
            elif self.__ptTypes[i] == Path.SEG_LINETO:
                x, y = self.__ptCoords[i]
                dx = x - xp; dy = y - yp
                ds = math.sqrt(dx*dx+dy*dy)
                if s>=d and s <= (d + ds):
                    f = (s-d)/ds
                    xq, yq = xp + f*(x-xp), yp + f*(y-yp)
                    break
                d = d + ds
                xp, yp = x, y
        return complex(xq, yq)

    def getLength(self):
        return self.__length

    # compute length of path
    # (its an approximation since its done after linearization)
    def __getLength(self):
        d = 0.0
        n = len(self.__ptTypes)
        for i in range(n):
            if self.__ptTypes[i] == Path.SEG_MOVETO:
                xp, yp =        self.__ptCoords[i]
            elif self.__ptTypes[i] == Path.SEG_LINETO:
                x, y = self.__ptCoords[i]
                dx = x - xp; dy = y - yp
                d = d + math.sqrt(dx*dx+dy*dy)
                xp, yp = x, y
        return d

    def __repr__(self):
        return repr(self.__svgpath)

    #
    # SVG path callbacks
    #
    def moveTo(self, pt):
        n = len(self.__ptTypes)
        if n>0 and self.__ptTypes[n - 1] == Path.SEG_MOVETO:
            self.__ptCoords[n - 1] = pt
        else:
            self.__ptTypes.append(Path.SEG_MOVETO)
            self.__ptCoords.append(pt)

        n = len(self.__segTypes)
        if n>0 and self.__segTypes[n - 1] == Path.SEG_MOVETO:
            self.__segCoords[n - 1] = pt
        else:
            self.__segTypes.append(Path.SEG_MOVETO)
            self.__segCoords.append(pt)

    def lineTo(self, pt):
        n =  len(self.__ptCoords)
        if n == 0: xp, yp = 0, 0
        else: xp, yp =  self.__ptCoords[n-1]

        self.__ptTypes.append(Path.SEG_LINETO)
        self.__ptCoords.append(pt)

        self.__segTypes.append(Path.SEG_LINETO)
        self.__segCoords.append(pt)

        x, y = pt
        dx = x - xp; dy = y - yp
        self.__length = self.__length + math.sqrt(dx*dx+dy*dy)
        self.__lenValues.append(self.__length)

    def curveTo(self, pt1, pt2, pt):
        n =  len(self.__ptCoords)
        if n == 0: xp, yp = 0, 0
        else: xp, yp =  self.__ptCoords[n-1]

        pt0 = self.__ptCoords[n - 1]
        points = self.findCubicPoints(pt0, pt1, pt2, pt)
        n = len(points)
        if n==0: return
        for i in range(1,n):
            self.__ptTypes.append(Path.SEG_LINETO)
            self.__ptCoords.append(points[i])
            x, y = points[i]
            dx = x - xp; dy = y - yp
            self.__length = self.__length + math.sqrt(dx*dx+dy*dy)
            xp, yp = x, y

        self.__segTypes.append(Path.SEG_CUBICTO)
        self.__segCoords.append(pt)
        self.__lenValues.append(self.__length)

    def quadTo(self, pt1, pt):
        n =  len(self.__ptCoords)
        if n == 0: xp, yp = 0, 0
        else: xp, yp =  self.__ptCoords[n-1]
        self.curveTo((xp, yp), pt1, pt)

    def arcTo(self, pt1, pt, r1, r2, angle, arcFlag, sweepFlag):
        # XXX: not implemented here (see svgwin.py for an implementation)
        # draw a line instead
        self.moveTo(pt1)
        self.lineTo(pt)

    def closePath(self):
        if len(self.__ptCoords)>0:
            self.lineTo(self.__ptCoords[0])

    #
    # Helpers
    #
    def getCoords(self, i):
        return None

    def findCubicPoints(self, pt1, pt2, pt3, pt4, npoints=16):
        z1 = complex(pt1[0],pt1[1])
        z2 = complex(pt2[0],pt2[1])
        z3 = complex(pt3[0],pt3[1])
        z4 = complex(pt4[0],pt4[1])
        points = [pt1,]
        dt = 1.0/float(npoints-1.0)
        t = dt
        for i in range(1,npoints-1):
            t2 = t*t
            t3 = t2*t
            tc = 1.0 - t
            tc2 = tc*tc
            tc3 = tc2*tc
            z = tc3*z1+3*tc2*t*z2+3*tc*t2*z3+t3*z4
            points.append((z.real,z.imag))
            t = t + dt
        points.append(pt4)
        return points

    def findCubicPointsBySubdivision(self, pt1, pt2, pt3, pt4, niters=8):
        z1 = complex(pt1[0],pt1[1])
        z2 = complex(pt2[0],pt2[1])
        z3 = complex(pt3[0],pt3[1])
        z4 = complex(pt4[0],pt4[1])
        segs = [(z1, z2, z3, z4),]
        for i in range(niters):
            segsp = segs[:]
            segs = []
            for e in segsp:
                if type(e)==type((1,)):
                    lc, pt, rc  = self.subdivide(e)
                    segs.append(lc)
                    segs.append(pt)
                    segs.append(rc)
                else:
                    segs.append(e)
        points = [pt1,]
        for e in segs:
            if type(e)!=type((1,)):
                points.append((e.real,e.imag))
        points.append(pt4)
        return points

    def subdivide(self, c):
        z1,z2,z3,z4 = c
        z12 = 0.5*(z1 + z2)
        z23 = 0.5*(z2 + z3)
        z34 = 0.5*(z3 + z4)
        z123 = 0.5*(z12 + z23)
        z234 = 0.5*(z23 + z34)
        z1234 = 0.5*(z123 + z234)
        return (z1, z12, z123,z1234),z1234,(z1234,z234,z34,z4)

    def copy(self):
        # XXX: need implementation
        # newpath = Path(), init, etc
        return self
