__version__ = "$Id$"

#
#       SVG DOM
#

import string

import svgdtd

from svgtypes import *

import smiltime
import svganimators

class SvgNode:
    def __init__(self, type, document):
        self.type = type # tag for elements and meta-tag for the rest
        self.document = document # owner document
        self.parent = None
        self.firstchild = None
        self.nextsibling = None
        self.data = None
        self.cdata = None
        self.index = 0

        # for optimization when building tree (can be removed)
        self.lastchild = None

    def __repr__(self):
        if self.data is not None:
            data = string.strip(self.data)
            return '<%s instance, type=%s, data=%s>' % (self.__class__.__name__, self.type, `data`)
        else:
            return '<%s instance, type=%s>' % (self.__class__.__name__, self.type)

    def svgrepr(self):
        return ''

    def getType(self):
        return self.type

    def getDocument(self):
        return self.document

    def getParent(self):
        return self.parent

    def getFirstChild(self):
        return self.firstchild

    def getNextSibling(self):
        return self.nextsibling

    def getRoot(self):
        return self.document.getRoot()

    def getIndex(self):
        return self.index

    def getUID(self):
        uid = '%d' % (self.index + 1)
        parent = self.parent
        while parent is not None and parent != self.document:
            uid = '%d.%s' % (parent.index+1, uid)
            parent = parent.parent
        return uid

    def getChildren(self):
        L = []
        node = self.firstchild
        while node:
            L.append(node)
            node = node.nextsibling
        return L

    def getFirstChildByType(self, type):
        node = self.firstchild
        while node:
            if node.type == type:
                return node
            node = node.nextsibling
        return None

    def appendData(self, data):
        if self.data is None:
            self.data = data
        else:
            self.data = self.data + data

    def appendCData(self, cdata):
        if self.cdata is None:
            self.cdata = cdata
        else:
            self.cdata = self.cdata + cdata

    # on end_tag
    def setready(self):
        if self.data is not None:
            self.data = string.strip(self.data)
        if self.cdata is not None:
            self.cdata = string.strip(self.cdata)

    def getLastChild(self):
        return self.lastchild

    def appendChild(self, node):
        lastchild = self.lastchild
        if lastchild is None:
            self.firstchild = node
            node.index = 0
        else:
            lastchild.nextsibling = node
            node.index = lastchild.index + 1
        node.parent = self
        self.lastchild = node

    def getPath(self):
        path = [self,]
        parent = self.parent
        while parent is not None:
            path.insert(0, parent)
            parent = parent.parent
        return path

    def clone(self):
        new = self.__class__(self.type, self.document)
        new.parent = self.parent
        new.firstchild = self.firstchild
        new.nextsibling = self.nextsibling
        new.data = self.data
        new.cdata = self.cdata
        return new

    def isVisible(self):
        return 0

    def get(self, name, atype='XML'):
        return None

class SvgComment(SvgNode):
    def svgrepr(self):
        return '<!--' + self.data + '-->'

class SvgElement(SvgNode, smiltime.TimeElement):
    def __init__(self, type, document):
        SvgNode.__init__(self, type, document)
        self.attrdict = {}      # attributes of this Element

        # should be attrs of SvgStyleElement descendants
        self.style = None
        self.tflist = None
        self.istimeElement = 0

        self.ctm_provider = None

    def __repr__(self):
        if self.data is not None:
            data = string.strip(self.data)
            return '<%s instance, type=%s, attributes=%s, data=%s>' % (self.__class__.__name__, self.type, `self.attrdict`, `data`)
        else:
            return '<%s instance, type=%s, attributes=%s>' % (self.__class__.__name__, self.type, `self.attrdict`)

    def svgrepr(self):
        s = self.type + ' '
        for attr in self.attrdict.keys():
            val = self.attrdict.get(attr)
            if val is None:
                continue
            elif type(val) == type(''):
                default = svgdtd.SVG.attributes[self.type][attr]
                if val != default:
                    s = s + attr + '=\"' + val + '\" '
            else:
                try:
                    if not val.isDefault():
                        s = s + attr + '=\"' + repr(val) + '\" '
                except:
                    print self, attr, 'is not an svgtype object'
        return s[:-1]

    def setAttributes(self, attrdict):
        self.attrdict = attrdict.copy()
        for name, val in self.attrdict.items():
            if name != 'style':
                self.attrdict[name] = CreateSVGAttr(self, name, val)
        self.initAsTimeElement()
        self.parseStyle()

        id = self.get('id')
        if id is not None:
            self.document.addElementId(id, self)

        self.parseAttributes()

    # override for extra attributes parsing
    def parseAttributes(self):
        pass

    def createAttr(self, name, val):
        attr = CreateSVGAttr(self, name, val)
        self.attrdict[name] = attr
        return attr

    def removeAttr(self, name):
        if self.attrdict.has_key(name):
            del self.attrdict[name]

    def createStyleAttr(self, name, val):
        attr = CreateSVGAttr(self, name, val)
        self.attrdict['style']._styleprops[name] = attr
        return attr

    def getAttribute(self, attr):
        return self.attrdict.get(attr)

    def getCSSAttr(self, name, create = 1):
        style = self.attrdict.get('style')
        attr = style._styleprops.get(name)
        if create and attr is None and IsCSSAttr(name):
            attr = self.createStyleAttr(name, None)
        return attr

    def getXMLAttr(self, name, create = 1):
        attr = self.attrdict.get(name)
        if create and attr is None and not IsCSSAttr(name):
            attr = self.createAttr(name, None)
        return attr

    def getCalcAttr(self, name):
        return self.attrdict.get(name)

    def getAttrOfType(self, name, attrtype):
        if attrtype == 'auto' or attrtype is None:
            attr = self.getCSSAttr(name)
            if attr is None:
                attr = self.getXMLAttr(name)
            return attr
        elif attrtype == 'CSS':
            return self.getCSSAttr(name)
        elif attrtype == 'XML':
            return self.getXMLAttr(name)
        assert 0, 'invalid attribute type %s' % attrtype

    def parseStyle(self):
        val = self.attrdict.get('style')
        style = SVGStyle(self, 'style', val)

        classname = self.get('class')
        if classname is not None:
            styleobj = self.document.getClassStyle(classname)
            style.update(styleobj)

        self.attrdict['style'] = style

    def getStyle(self):
        return self.get('style')

    def getTransform(self):
        return self.get('transform')

    def get(self, name, atype='XML'):
        if atype == 'XML':
            attr = self.attrdict.get(name)
        elif atype == 'CSS':
            style = self.attrdict.get('style')
            attr = style._styleprops.get(name)
        if attr is None or type(attr) == type(''):
            return attr
        else:
            if isinstance(attr, Animateable):
                return attr.getPresentValue()
            else:
                return attr.getValue()

    def isVisible(self):
        if self.istimeElement:
            if self.type in svgdtd.SVG.timeEntities:
                return 0
        if self.document.hasTiming():
            tc = self.getTimeContainer()
            if tc:
                if tc.isActive() or tc.isFrozen():
                    vis = self.get('visibility', 'CSS')
                    return vis is None or vis == 'visible'
                else:
                    return 0
        vis = self.get('visibility', 'CSS')
        return vis is None or vis == 'visible'

    def initAsTimeElement(self):
        ttype = None
        tc = self.get('timeContainer')
        if self.type in ('animate','set','animateMotion','animateColor','animateTransform',):
            ttype = self.type
        elif self.type in ('seq','par','excl'):
            ttype = self.type
        elif tc is not None and tc in ('seq','par','excl'):
            ttype = tc
        if ttype is not None:
            smiltime.TimeElement.__init__(self, ttype, self.document.getTimeRoot())
            self.istimeElement = 1
            self.checkTiming()

    def isTimeElement(self):
        return self.istimeElement

    def getTimeContainer(self):
        if self.istimeElement:
            return self
        parent = self.parent
        while parent is not None and parent != self.document:
            if parent.istimeElement:
                return parent
            parent = parent.parent
        return None

    def isMouseSensitive(self):
        p = self.getParent()
        return p and p.getType() == 'a'

    def onClick(self):
        p = self.getParent()
        if p and p.getType() == 'a':
            # fire anchor
            # temp code to do something
            import sys
            if sys.platform == 'win32':
                import windowinterface
                windowinterface.shell_execute(p.get('xlink:href'),'open')

    def setCTMProvider(self, p):
        self.ctm_provider = p

    def getViewportToUserTM(self):
        if self.ctm_provider:
            tm = self.ctm_provider.getCTM()
            tm = tm.copy()
            tm.inverse()
            return tm
        return TM()

class SvgRect(SvgElement):
    def parseAttributes(self):
        # force xvg semantics for rect rx ry
        rx, ry = self.attrdict.get('rx'), self.attrdict.get('ry')
        if rx is not None and ry is not None:
            pass
        elif rx is not None:
            self.attrdict['ry'] = rx
        elif ry is not None:
            self.attrdict['rx'] = ry

class SvgCircle(SvgElement):
    def parseAttributes(self):
        pass

class SvgEllipse(SvgElement):
    def parseAttributes(self):
        pass

class SvgLine(SvgElement):
    def parseAttributes(self):
        pass

class SvgPolyline(SvgElement):
    def parseAttributes(self):
        pass

class SvgPolygon(SvgElement):
    def parseAttributes(self):
        pass

class SvgPath(SvgElement):
    def parseAttributes(self):
        pass

class SvgText(SvgElement):
    def parseAttributes(self):
        pass

class SvgG(SvgElement):
    def parseAttributes(self):
        pass

class SvgSvg(SvgElement):
    def parseAttributes(self):
        pass

    def getSize(self):
        w, h = self.get('width'), self.get('height')
        if not w or not h:
            vb = self.get('viewBox')
            if (w is None or h is None) and vb:
                # size not given
                w, h = vb[2:]
                if w>640 or h>480:
                    sx, sy = 640.0/float(w), 480.0/float(h)
                    scale = min(sx, sy)
                    w = int(w*scale+0.5)
                    h = int(h*scale+0.5)
            else:
                # percent of whatever available
                # needs fix: this assumes 100% for root SVG
                w, h = 640, 480
        return w, h

class SvgStyle(SvgElement):
    def parseAttributes(self):
        self.document.appendCSS(self)

    def setready(self):
        if self.cdata:
            self.textcssdefs = SVGTextCss(self, 'text/css', self.cdata)
        else:
            self.textcssdefs = None

    def svgrepr(self):
        textcssdefs = self.textcssdefs.getValue()
        s = '<style type=\"text/css\"><![CDATA[\n'
        for key, val in textcssdefs.items():
            s = s + '  .' + key + ' {' + repr(val) + '}\n'
        s = s + ']]></style>'
        return s

        if type == 'defs':
            self.defs.append(el)
        elif type == 'style':
            self.styles.append(el)


class SvgDefs(SvgElement):
    def parseAttributes(self):
        self.document.appendDefs(self)
        self.defs = {} # not seen yet

    def setready(self):
        node = self.firstchild
        while node:
            defid = node.get('id')
            if defid is not None:
                self.defs[defid] = node
            node = node.nextsibling

class SvgUse(SvgElement):
    def parseAttributes(self):
        # postpone finding use ref
        # we may be in defs
        self.what = None

    def locateDef(self):
        what = None
        href = self.get('xlink:href')
        if href:
            if href[0] == '#':
                what = self.document.getElementDef(href[1:])
        self.what = what

#
#  virtual svg time root
#

class TimeRoot(SvgElement):
    def __init__(self, type, document):
        SvgElement.__init__(self, type, document)
        smiltime.TimeElement.__init__(self, 'par', None)
        self.attrdict['dur'] = 'indefinite'

#
# Animate elements
#

class AnimateElement(SvgElement):
    def parseAttributes(self):
        self.animator = None
        self.targetAttr = None
        self.checkValues()

    def createAnimator(self):
        assert self._targetElement != None, 'invalid target element'
        return None

    def isVisible(self):
        return 0

    def checkValues(self):
        self._animtype = self.findAnimationType()
        assert self._animtype != 'invalid', 'invalid animation values'
        self._targetElement = self.findTargetElement()
        if self._targetElement is not None:
            name = self.attrdict.get('attributeName')
            attrtype = self.get('attributeType')

    def findAnimationType(self):
        pathstr = self.attrdict.get('path')
        if pathstr is not None:
            return 'path'

        values = self.attrdict.get('values')
        if values is not None:
            return 'values'

        v1 = self.attrdict.get('from')
        v2 = self.attrdict.get('to')
        dv = self.attrdict.get('by')

        # if we don't have 'values' then 'to' or 'by' must be given
        if not v2 and not dv:
            return 'invalid'

        if v1:
            if v2:
                return 'from-to'
            elif dv:
                return 'from-by'
        else:
            if v2:
                return 'to'
            elif dv:
                return 'by'

        return 'invalid'

    def findTargetElement(self):
        id = self.get('targetElement')
        if id is None:
            targetElement = self.getParent()
        else:
            targetElement = self.getDocument().getElementWithId(id)
        return targetElement

    enumattrs = ('calcMode', 'accumulate', 'additive', 'autoReverse')
    def copyAnimAttrs(self):
        d = {}
        for attr in self.enumattrs:
            d[attr] = self.get(attr)

        speed = self.get('speed')
        if speed is None: speed = 1.0
        if speed<=0:speed = 1.0
        d['speed'] = speed

        accelerate = self.get('accelerate')
        if accelerate is None: accelerate = 0
        accelerate = max(0, accelerate)

        decelerate = self.get('decelerate')
        if decelerate is None: decelerate = 0
        decelerate = max(0, decelerate)

        dt =  accelerate + decelerate
        if dt>1.0: accelerate = decelerate = 0
        d['accelerate'] = accelerate
        d['decelerate'] = decelerate
        return d

    def getValues(self, ValueClass):
        if self._animtype == 'values':
            values = self.attrdict.get('values')
            if values:
                values = values.strip()
            if values and values[-1] == ';':
                values = values[:-1]
            sl = string.split(values,';')
            L = []
            for substr in sl:
                if substr:
                    L.append(ValueClass(self, '', substr).getValue())
            return L
        elif self._animtype == 'from-to':
            return ValueClass(self, '', self.attrdict.get('from')).getValue(), ValueClass(self, '', self.attrdict.get('to')).getValue()
        elif self._animtype == 'from-by':
            v1 = ValueClass(self, '', self.attrdict.get('from')).getValue()
            dv = ValueClass(self, '', self.attrdict.get('by')).getValue()
            return v1, v1+dv
        elif self.__animtype == 'to':
            return  ValueClass(self, '', self.attrdict.get('to')).getValue()
        elif self._animtype == 'by':
            return 0, ValueClass(self, '', self.attrdict.get('by')).getValue()
        return None

    #
    #  Foreign object DOM interface
    #
    def resetObject(self):
        if self.animator:
            self.animator.reset()

    def beginObject(self):
        dur = self.getCalcDur()
        if self.animator and smiltime.isdefinite(dur):
            self.animator.prepareInterval(dur)
            self.targetAttr.appendAnimator(self.animator)

    def removeObject(self):
        if self.animator:
            self.targetAttr.removeAnimator(self.animator)
        smiltime.TimeElement.removeObject(self)


class SvgAnimate(AnimateElement):
    def parseAttributes(self):
        AnimateElement.parseAttributes(self)

    def createAnimator(self):
        assert self._targetElement != None, 'invalid target element'
        name = self.attrdict.get('attributeName')
        attrtype = self.get('attributeType')
        self.targetAttr = self._targetElement.getAttrOfType(name, attrtype)

        if self.targetAttr is not None:
            dict = self.copyAnimAttrs()
            dict['values'] = self.getValues(self.targetAttr.__class__)
            self.animator = svganimators.Animator(self, self.targetAttr, dict)


class SvgSet(AnimateElement):
    def parseAttributes(self):
        AnimateElement.parseAttributes(self)
        assert self._animtype == 'to', 'invalid animation values'

    def createAnimator(self):
        assert self._targetElement != None, 'invalid target element'

        name = self.attrdict.get('attributeName')
        attrtype = self.get('attributeType')
        self.targetAttr = self._targetElement.getAttrOfType(name, attrtype)

        if self.targetAttr is not None:
            AttrClass = self.targetAttr.__class__
            val = AttrClass(self, '', self.get('to')).getValue()

            dict = self.copyAnimAttrs()
            dict['values'] = (val, )
            dict['calcMode'] = 'discrete'
            self.animator = svganimators.SetAnimator(self, self.targetAttr, dict)

class SvgAnimateTransform(AnimateElement):
    def parseAttributes(self):
        AnimateElement.parseAttributes(self)

    def createAnimator(self):
        assert self._targetElement != None, 'invalid target element'

        name = self.attrdict.get('attributeName')
        attrtype = self.get('attributeType')
        assert name == 'transform', 'animateTransform with unknown attributeName %s' % name
        self.targetAttr = self._targetElement.getAttrOfType(name, attrtype)

        if self.targetAttr is not None:
            dict = self.copyAnimAttrs()
            tftype = dict['type'] = self.get('type')

            if tftype in ('rotate', 'skewX', 'skewY'):
                dict['values'] = self.getValues(SVGAngle)
                self.animator = svganimators.TransformAnimator(self, self.targetAttr, dict)
            elif tftype in ('translate', 'scale'):
                dict['values'] = self.getValues(SVGNumberList)
                self.animator = svganimators.VectorTransformAnimator(self, self.targetAttr, dict)
            else:
                assert 0, 'invalid animateTransform type %s' % tftype

class SvgAnimateMotion(AnimateElement):
    def parseAttributes(self):
        AnimateElement.parseAttributes(self)

    def createAnimator(self):
        assert self._targetElement != None, 'invalid target element'

        self.targetAttr = self._targetElement.getAttrOfType('transform', 'XML')

        if self.targetAttr is not None:
            dict = self.copyAnimAttrs()
            dict['rotate'] = self.get('rotate')

            import svgpath
            path = svgpath.Path()
            path.constructFromSVGPathString(self.get('path'))
            dict['path'] = path
            self.animator = svganimators.MotionAnimator(self, self.targetAttr, dict)

class SvgAnimateColor(AnimateElement):
    def parseAttributes(self):
        AnimateElement.parseAttributes(self)

    def createAnimator(self):
        assert self._targetElement != None, 'invalid target element'

        name = self.attrdict.get('attributeName')
        attrtype = self.get('attributeType')
        self.targetAttr = self._targetElement.getAttrOfType(name, attrtype)

        if self.targetAttr is not None:
            assert self.targetAttr.__class__ == SVGColor, 'animateColor on a not color attribute %s' % name
            dict = self.copyAnimAttrs()
            dict['values'] = self.getValues(SVGColor)
            self.animator = svganimators.ColorAnimator(self, self.targetAttr, dict)

####################3
class SvgView(SvgElement):
    def parseAttributes(self):
        pass

class SvgTspan(SvgElement):
    def parseAttributes(self):
        pass

class SvgForeignObject(SvgElement):
    def parseAttributes(self):
        pass

class SvgClipPath(SvgElement):
    def parseAttributes(self):
        pass

class SvgFeMergeNode(SvgElement):
    def parseAttributes(self):
        pass

class SvgLinearGradient(SvgElement):
    def parseAttributes(self):
        pass


class SvgSwitch(SvgElement):
    def parseAttributes(self):
        pass

class SvgFilter(SvgElement):
    def parseAttributes(self):
        pass

class SvgTref(SvgElement):
    def parseAttributes(self):
        pass

class SvgAltGlyphDef(SvgElement):
    def parseAttributes(self):
        pass

class SvgMask(SvgElement):
    def parseAttributes(self):
        pass

class SvgMpath(SvgElement):
    def parseAttributes(self):
        pass

class SvgFeDiffuseLighting(SvgElement):
    def parseAttributes(self):
        pass

class SvgFontFaceFormat(SvgElement):
    def parseAttributes(self):
        pass

class SvgScript(SvgElement):
    def parseAttributes(self):
        pass

class SvgFeComponentTransfer(SvgElement):
    def parseAttributes(self):
        pass

class SvgAltGlyphItem(SvgElement):
    def parseAttributes(self):
        pass

class SvgDesc(SvgElement):
    def parseAttributes(self):
        pass

class SvgColorProfile(SvgElement):
    def parseAttributes(self):
        pass

class SvgDefinitionSrc(SvgElement):
    def parseAttributes(self):
        pass

class SvgFeMerge(SvgElement):
    def parseAttributes(self):
        pass

class SvgFeComposite(SvgElement):
    def parseAttributes(self):
        pass

class SvgFeSpecularLighting(SvgElement):
    def parseAttributes(self):
        pass

class SvgFeFuncR(SvgElement):
    def parseAttributes(self):
        pass

class SvgFeDisplacementMap(SvgElement):
    def parseAttributes(self):
        pass

class SvgFeDistantLight(SvgElement):
    def parseAttributes(self):
        pass

class SvgFontFaceName(SvgElement):
    def parseAttributes(self):
        pass

class SvgSymbol(SvgElement):
    def parseAttributes(self):
        pass

class SvgFeConvolveMatrix(SvgElement):
    def parseAttributes(self):
        pass

class SvgFeFuncG(SvgElement):
    def parseAttributes(self):
        pass

class SvgFeSpotLight(SvgElement):
    def parseAttributes(self):
        pass

class SvgFePointLight(SvgElement):
    def parseAttributes(self):
        pass

class SvgFeFuncB(SvgElement):
    def parseAttributes(self):
        pass

class SvgFeFuncA(SvgElement):
    def parseAttributes(self):
        pass

class SvgMetadata(SvgElement):
    def parseAttributes(self):
        pass

class SvgGlyphRef(SvgElement):
    def parseAttributes(self):
        pass

class SvgRadialGradient(SvgElement):
    def parseAttributes(self):
        pass

class SvgFeImage(SvgElement):
    def parseAttributes(self):
        pass

class SvgFeColorMatrix(SvgElement):
    def parseAttributes(self):
        pass

class SvgVkern(SvgElement):
    def parseAttributes(self):
        pass

class SvgFeBlend(SvgElement):
    def parseAttributes(self):
        pass

class SvgFeFlood(SvgElement):
    def parseAttributes(self):
        pass

class SvgFontFaceUri(SvgElement):
    def parseAttributes(self):
        pass

class SvgPattern(SvgElement):
    def parseAttributes(self):
        pass

class SvgFeTurbulence(SvgElement):
    def parseAttributes(self):
        pass

class SvgTitle(SvgElement):
    def parseAttributes(self):
        pass

class SvgGlyph(SvgElement):
    def parseAttributes(self):
        pass

class SvgFeOffset(SvgElement):
    def parseAttributes(self):
        pass

class SvgFont(SvgElement):
    def parseAttributes(self):
        pass

class SvgAltGlyph(SvgElement):
    def parseAttributes(self):
        pass

class SvgMarker(SvgElement):
    def parseAttributes(self):
        pass

class SvgFontFaceSrc(SvgElement):
    def parseAttributes(self):
        pass

class SvgCursor(SvgElement):
    def parseAttributes(self):
        pass

class SvgMissingGlyph(SvgElement):
    def parseAttributes(self):
        pass

class SvgHkern(SvgElement):
    def parseAttributes(self):
        pass

class SvgImage(SvgElement):
    def parseAttributes(self):
        pass

class SvgTextPath(SvgElement):
    def parseAttributes(self):
        pass

class SvgStop(SvgElement):
    def parseAttributes(self):
        pass

class SvgFeMorphology(SvgElement):
    def parseAttributes(self):
        pass

class SvgFeTile(SvgElement):
    def parseAttributes(self):
        pass

class SvgA(SvgElement):
    def parseAttributes(self):
        pass
    def isVisible(self):
        return 0

class SvgFeGaussianBlur(SvgElement):
    def parseAttributes(self):
        pass

class SvgFontFace(SvgElement):
    def parseAttributes(self):
        pass

####################################

class SvgDocument(SvgNode):
    def __init__(self, source):
        SvgNode.__init__(self, '#document', self)

        # xml spec
        self.xmlversion = '1.0'
        self.xmlencoding = 'ISO-8859-1'
        self.xmlstandalone = 'no'

        # doctype
        self.doctypetag = 'svg'
        self.doctypepubid = svgdtd.SVGpubid
        self.doctypesyslit = svgdtd.SVGdtd
        self.doctypedata = None

        # set source
        self.source = None
        if source:
            source = string.join(string.split(source, '\r\n'), '\n')
            source = string.join(string.split(source, '\r'), '\n')
            self.source = source

        # document repository
        self.defs = []
        self.entitydefs = None
        self.styles = []
        self.ids = {}
        self.timeRoot = TimeRoot('#timeroot', self)

        # create DOM
        p = SvgDOMBuilder(self)
        p.feed(self.source)
        p.close()
        self.setready()

    def svgrepr(self):
        s = '<?xml version=\"' + self.xmlversion + '\" standalone=\"' + self.xmlstandalone + '\"?>\n'
        s = s + '<!DOCTYPE svg PUBLIC \"' + self.doctypepubid + '\"\n'
        s = s + '  \"' + self.doctypesyslit + '\">'
        return s

    def setDocType(self, tag, pubid, syslit, data):
        self.doctypetag, self.doctypepubid, self.doctypesyslit, self.doctypedata = tag, pubid, syslit, data
        if data:
            # parse any entities def
            self.entitydefs = SVGEntityDefs(self, 'entity', data).getValue()

    def getDocType(self):
        return self.doctypetag, self.doctypepubid, self.doctypesyslit, self.doctypedata

    def setXML(self, encoding, standalone='no'):
        self.xmlencoding, self.xmlstandalone = encoding, standalone

    def getXML(self, encoding, standalone='no'):
        return self.xmlencoding, self.xmlstandalone

    def getSrc(self, data):
        return self.source

    def getRoot(self):
        return self.getFirstChildByType('svg')

    def getSize(self):
        root =  self.getRoot()
        if root is not None:
            return root.getSize()
        return 0, 0

    def getDOMClassName(self, tag):
        if tag[0] == '#': # internal node
            tag = tag[1:]
        csname = 'Svg'+ tag[0].upper()
        n = len(tag)
        i = 1
        while i<n:
            if tag[i] == '-':
                i = i + 1
                csname = csname + tag[i].upper()
            else:
                csname = csname + tag[i]
            i = i + 1
        return csname

    def getDOMClass(self, tag):
        import svgdom # how we ref this module?
        csname = self.getDOMClassName(tag)
        elclass = getattr(svgdom, csname, SvgElement)
        if elclass == SvgElement:
            print 'missing DOM node for', `tag`
        return elclass

    def createElement(self, type):
        domclass = self.getDOMClass(type)
        return domclass(type, self)

    def createDOMIterator(self, root, listener, filter=None):
        return DOMIterator(root, listener, filter)

    def createDOMParamIterator(self, root, navigator, startnodecb, endnodecb=None, filter=None):
        return DOMParamIterator(root, navigator, startnodecb, endnodecb, filter)

    def setready(self):
        SvgNode.setready(self)
        if self.timeRoot.getFirstTimeChild() is not None:
            self.buildTimeGraph()

    #
    # document repository
    #
    def addElementId(self, id, el):
        self.ids[id] = el

    def getElementWithId(self, id):
        return self.ids.get(id)

    def appendDefs(self, el):
        self.defs.append(el)

    def appendCSS(self, el):
        self.styles.append(el)

    def getEntityDefs(self):
        return self.entitydefs

    def getClassStyle(self, classname):
        L = self.styles[:]
        L.reverse()
        cs = SVGStyle(None, None, None)
        for el in L:
            textcssdefs = el.textcssdefs.getValue()
            cst = textcssdefs.get(classname)
            if cst is not None:
                cs.update(cst)
        return cs

    def getElementDef(self, id):
        for el in self.defs:
            what = el.defs.get(id)
            if what: return what
        return None

    def appendTimeElement(self, el):
        self.timeRoot.appendTimeChild(el)

    def getTimeRoot(self):
        return self.timeRoot

    def hasTiming(self):
        return self.timeRoot.getFirstTimeChild() is not None

    #
    #  build directed time graph
    #
    def buildTimeGraph(self):
        self.buildTimeGraphCallback(self.timeRoot)
        iter = self.createDOMParamIterator(self.timeRoot, self, self.buildTimeGraphCallback)
        while iter.advance(): pass

    def buildTimeGraphCallback(self, node):
        # 1.
        attr = node.getXMLAttr('begin')
        if attr.isEmpty():
            e = SyncElement(node, 'begin')
            attr.append(e)
        attr.reinterpret()
        attr.createSyncArcs()

        # 2.
        attr = node.getXMLAttr('end')
        attr.reinterpret()
        attr = SyncElementList(node, 'activeEnd', None)
        aendList = node.calcActiveEndSyncList()
        for base, val in aendList:
            if base == 'self':
                e = SyncElement(node, 'activeEnd')
                e._syncbase = 'self'
                e._baseevent = 'begin'
                e._offset = val
                e._units = 's'
                attr.append(e)
            elif base == 'synclist':
                for other in val:
                    e = other.clone()
                    e._attr = 'activeEnd'
                    attr.append(e)
        node.attrdict['activeEnd'] = attr
        attr.createSyncArcs()

        # 3. and go!
        if isinstance(node, AnimateElement):
            node.createAnimator()

    #  navigator interface
    def getNavFirstChild(self, node):
        return node.getFirstTimeChild()

    def getNavNextSibling(self, node):
        return node.getNextTimeSibling()

    def getNavParent(self, node):
        return node.getTimeParent()

    #
    # write svg tree (print for now)
    #
    def write(self):
        iter = DOMIterator(self, self)
        self.writesp = ''
        self.writespincr = '   '
        print self.svgrepr()
        while iter.advance(): pass

    def startnode(self, node):
        tag = node.getType()
        if tag[0] == '#' or tag == 'style':
            # internal node
            if tag == '#comment':
                print self.writesp + node.svgrepr()
            else:
                print node.svgrepr()
        elif node.getFirstChild() is None and node.data is None:
            print self.writesp + '<' + node.svgrepr() + '/>'
        else:
            if node.data is not None:
                print self.writesp + '<' + node.svgrepr() + '>',
                if node.getFirstChild() is None:
                    print node.data,
                else:
                    print node.data
            else:
                print self.writesp + '<' + node.svgrepr() + '>'
            self.writesp = self.writesp + self.writespincr

    def endnode(self, node):
        tag = node.getType()
        if tag[0] == '#' or tag == 'style':
            # internal node
            pass
        elif node.getFirstChild() is None and node.data is None:
            pass
        else:
            self.writesp = self.writesp[:-len(self.writespincr)]
            if node.data is not None and node.getFirstChild() is None:
                print '</' + node.getType() + '>'
            else:
                print self.writesp + '</' + node.getType() + '>'

####################################
# SVG DOM Builder using xmllib.XMLParser

import xmllib

class SvgDOMBuilder(svgdtd.SVG, xmllib.XMLParser):
    def __init__(self, document):
        xmllib.XMLParser.__init__(self)
        self.__document = document
        self.__node = document
        self.__timenode = document.getTimeRoot()

    def handle_xml(self, encoding, standalone):
        self.__document.setXML(encoding, standalone)

    def handle_doctype(self, tag, pubid, syslit, data):
        self.__document.setDocType(tag, pubid, syslit, data)
        docentitydefs = self.__document.getEntityDefs()
        if docentitydefs is not None:
            xmllib.XMLParser.entitydefs.update(docentitydefs)

    def handle_data(self, data):
        tag = self.__node.getType()
        if tag in self.dataEntities:
            self.__node.appendData(data)

    def handle_cdata(self, data):
        tag = self.__node.getType()
        if tag in self.cdataEntities:
            self.__node.appendCData(data)

    def unknown_starttag(self, tag, attrs):
        partag = self.__node.getType()
        content = self.entities.get(partag)
        if content is None or tag not in content:
            self.syntax_error('%s not allowed in %s' % (tag, partag))
            return
        el = self.__document.createElement(tag)
        self.__node.appendChild(el)
        try:
            el.setAttributes(attrs)
        except AssertionError, arg:
            self.syntax_error(arg)
        self.__node = el

        # build time tree
        if el.isTimeElement():
            self.__timenode.appendTimeChild(el)
            self.__timenode = el

    def unknown_endtag(self, tag):
        if self.__node.isTimeElement():
            self.__timenode = self.__timenode.getTimeParent()
        self.__node.setready()
        self.__node = self.__node.getParent()

    def handle_comment(self, data):
        el = self.__document.createElement('#comment')
        self.__node.appendChild(el)
        el.appendData(data)

    def syntax_error(self, msg, lineno = None):
        msg = 'warning: syntax error on line %d: %s' % (lineno or self.lineno, msg)
        print msg

####################################
# DOM iterator

class DOMIterator:
    def __init__(self, root, listener, filter=None, trace=0):
        self.root = root
        self.listener = listener
        self.iter =  self.itForward
        self.node = root
        self.filter = filter
        self.trace = trace

    def advance(self):
        self.iter()
        return self.node != self.root

    def itForward(self):
        node = self.node.getFirstChild()
        if node:
            self.node = node
            self.startnode(node)
        elif self.node != self.root:
            node =  self.node.getNextSibling()
            if node:
                self.endnode(self.node)
                self.node = node
                self.startnode(node)
            else:
                self.endnode(self.node)
                self.iter = self.itBackward
                node = self.node.getParent()
                self.node = node
                if self.node != self.root:
                    self.endnode(self.node)

    def itBackward(self):
        node = self.node.getNextSibling()
        if node:
            # endnode on self.node already called
            self.iter = self.itForward
            self.node = node
            self.startnode(node)
        else:
            self.node = self.node.getParent()
            if self.node != self.root:
                self.endnode(self.node)

    def itFiltered(self):
        # self.node is in self.filter, bypass branch
        node = self.node.getNextSibling()
        if node:
            self.iter = self.itForward
            self.node = node
            self.startnode(node)
        else:
            self.iter = self.itBackward
            node = self.node.getParent()
            self.node = node
            if self.node != self.root:
                self.endnode(self.node)

    def startnode(self, node):
        if self.filter and node.getType() in self.filter:
            self.itFiltered()
        elif self.listener:
            if self.trace:
                print '<' + node.getType() + '>'
            self.listener.startnode(node)

    def endnode(self, node):
        if self.filter and node.getType() in self.filter:
            assert 0, 'endnode call on filtered node'
        elif self.listener:
            if self.trace:
                print '</' + node.getType() + '>'
            self.listener.endnode(node)


# like DOMIterator but generalized since it uses a navigator object
# class InterfaceNavigator:
#       def getNavFirstChild(self, node): return None
#       def getNavNextSibling(self, node): return None
#       def getNavParent(self, node): return None
class DOMParamIterator:
    def __init__(self, root, navigator, startnodecb, endnodecb=None, filter=None, trace=0):
        self.root = root
        self.navigator = navigator
        self.startnodecb = startnodecb
        self.endnodecb = endnodecb
        self.filter = filter
        self.trace = trace

        # internals
        self.iter =  self.itForward
        self.node = root

    def advance(self):
        self.iter()
        return self.node != self.root

    def itForward(self):
        node = self.navigator.getNavFirstChild(self.node)
        if node:
            self.node = node
            self.startnode(node)
        elif self.node != self.root:
            node = self.navigator.getNavNextSibling(self.node)
            if node:
                self.endnode(self.node)
                self.node = node
                self.startnode(node)
            else:
                self.endnode(self.node)
                self.iter = self.itBackward
                node = self.navigator.getNavParent(self.node)
                self.node = node
                if self.node != self.root:
                    self.endnode(self.node)

    def itBackward(self):
        node = self.navigator.getNavNextSibling(self.node)
        if node:
            # endnode on self.node already called
            self.iter = self.itForward
            self.node = node
            self.startnode(node)
        else:
            self.node = self.navigator.getNavParent(self.node)
            if self.node != self.root:
                self.endnode(self.node)

    def itFiltered(self):
        # self.node is in self.filter, bypass branch
        node = self.navigator.getNavNextSibling(self.node)
        if node:
            self.iter = self.itForward
            self.node = node
            self.startnode(node)
        else:
            self.iter = self.itBackward
            node = self.navigator.getNavParent(self.node)
            self.node = node
            if self.node != self.root:
                self.endnode(self.node)

    def startnode(self, node):
        if self.filter and node.getType() in self.filter:
            self.itFiltered()
        elif self.startnodecb:
            if self.trace:
                print '<' + node.getType() + '>'
            self.startnodecb(node)

    def endnode(self, node):
        if self.filter and node.getType() in self.filter:
            assert 0, 'endnode call on filtered node'
        elif self.endnodecb:
            if self.trace:
                print '</' + node.getType() + '>'
            self.endnodecb(node)


####################################
# Plays SVG animations

class SVGPlayer:
    def __init__(self, svgdoc, ostimer, rendercb, timeres=0.01):
        self._timeroot = svgdoc.getTimeRoot()
        self._ostimer = ostimer
        self._rendercb = rendercb
        self._timerid = None
        self._timeresolution = timeres
    #
    # extenal calls
    #
    def play(self):
        self._timeroot.resetElement()
        self._timeroot.setOsTimer(self._ostimer)
        self._timeroot.seekElement(0.0)
        self._timeroot.beginElement()
        self._timerid = self._ostimer.settimer(self._timeresolution, (self.timerCallback, ()))

    def stop(self):
        self._timeroot.endElement()
        self._timeroot.removeElement()
        if self._timerid is not None:
            self._ostimer.canceltimer(self._timerid)
            self._timerid = None

    def pause(self):
        self._timeroot.pauseElement()
        if self._timerid is not None:
            self._ostimer.canceltimer(self._timerid)
            self._timerid = None

    def resume(self):
        self._timeroot.resumeElement()
        if self._timerid is None:
            self._timerid = self._ostimer.settimer(self._timeresolution, (self.timerCallback, ()))

    #
    # timer rendering callback
    #
    def timerCallback(self):
        assert self._timerid is not None, 'smiltimer protocol violation'
        apply(apply, self._rendercb)
        self._timerid = None
        if self._timeroot.isTicking():
            self._timerid = self._ostimer.settimer(self._timeresolution, (self.timerCallback, ()))

####################################
# utilities

class DocCache:
    def __init__(self):
        self._stack = []
        self.capacity = 3

    def cache(self, url, doc):
        self._stack.append((url, doc))
        if len(self._stack) > self.capacity:
            self._stack = self._stack[1:]

    def hasdoc(self, url):
        for ref, doc in self._stack:
            if ref == url:
                return 1
        return 0

    def getDoc(self, url):
        for ref, doc in self._stack:
            if ref == url:
                return doc
        return None

    def clear(self):
        del self._stack
        self._stack = []


doccache = DocCache()

def GetSvgSizeFromSrc(source):
    svgdoc = SvgDocument(source)
    return svgdoc.getSize()

import MMurl

def GetSvgDocument(url):
    if doccache.hasdoc(url):
        svgdoc = doccache.getDoc(url)
    else:
        try:
            u = MMurl.urlopen(url)
        except IOError, arg:
            print 'Cannot resolve URL "%s": %s' % (url, arg)
            return None
        source = u.read()
        u.close()
        svgdoc = SvgDocument(source)
        doccache.cache(url, svgdoc)
    return svgdoc

def GetSvgSize(url):
    svgdoc = GetSvgDocument(url)
    if svgdoc is not None:
        return svgdoc.getSize()
    return 0, 0

####################################
# test

if __debug__:
    svgSource = """<?xml version="1.0" standalone="no"?>
    <svg width="600" height="600">
      <title> Simple shapes </title>
      <g transform="translate(150,150)" style="fill:red; stroke:navy; stroke-width:2; stroke-dasharray: 5 2;" >
        <circle cx="300" cy="30" r="20" transform="rotate(0)"/>
        <circle cx="300" cy="30" r="20" transform="rotate(10)"/>
        <circle cx="300" cy="30" r="20"  transform="rotate(20)" style="visibility:hidden"/>
        <circle cx="300" cy="30" r="20" transform="rotate(30)"/>
        <circle cx="300" cy="30" r="20"  transform="rotate(40)"/>
        <circle cx="300" cy="30" r="20"  transform="rotate(50)"/>
        <circle cx="300" cy="30" r="20" transform="rotate(60)" style="visibility:hidden" />
        <circle cx="300" cy="30" r="20" transform="rotate(70)"/>
        <circle cx="300" cy="30" r="20" transform="rotate(80)"/>
        <circle cx="300" cy="30" r="20" transform="rotate(90)"/>
        <rect x="300" y="30" width="20" height="20" transform="rotate(90)"/>
      </g>
    </svg>"""

    if __name__ == '__main__':
        #print GetSvgSizeFromSrc(svgSource)
        svg = SvgDocument(svgSource)
        svg.write()
