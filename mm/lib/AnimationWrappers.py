__version__ = "$Id$"

import string

import MMAttrdefs

from fmtfloat import fmtfloat, round

import colors
import tokenizer

debug = 0

# abstraction of animation target
# represents MMNode and MMRegion targets
# makes explicit what is needed by AnimationTarget
class AnimationTarget:
    def __init__(self, node):
        animparent = None
        target = None
        if hasattr(node, 'targetnode'):
            target = node.targetnode
        if target is None:
            target = node.GetParent()
        self._root = node.GetRoot()
        self._mmobj = target

    # return the underlying MMObj
    def getMMObj(self):
        return self._mmobj

    def getRoot(self):
        return self._root

    def getContext(self):
        return self._root.GetContext()

    # return animationNode.targetnode or None
    def getTargetNode(self):
        if self._isRegion():
            return None
        return self._mmobj

    # return dom values
    def getDomValues(self):
        if self._isRegion():
            try:
                rc = self._mmobj.getPxGeom()
            except:
                rc = None
            color = self._mmobj.get('bgcolor')
        else:
            try:
                rc = self._mmobj.getPxGeom()
            except:
                rc = None
            color = self._mmobj.attrdict.get('bgcolor')
        return rc, color

    # return targetElement attribute
    def getUID(self):
        if self._isRegion():
            return self._mmobj.GetUID()
        return self._mmobj.GetRawAttrDef('name', None)

    def _isRegion(self):
        return self._mmobj.getClassName() in ('Region', 'Viewport')

    def __getSelfAnimations(self, parent, children):
        uid = self.getUID()
        for node in parent.GetChildren():
            ntype = node.GetType()
            if ntype == 'animate':
                anim = None
                if node.targetnode == self._mmobj:
                    anim = node
                elif node.GetParent() == self._mmobj:
                    anim = node
                else:
                    te = MMAttrdefs.getattr(node, 'targetElement')
                    if te and te == uid:
                        anim = node
                if anim is not None and anim not in children:
                    children.append(anim)
            self.__getSelfAnimations(node, children)

class AnimationDefaultWrapper:
    def __init__(self, animnode):
        self._animateNode = animnode
        self._times = times = []
        self._animateMotionValues = animateMotionValues = []
        self._animateWidthValues = animateWidthValues = []
        self._animateHeightValues = animateHeightValues = []
        self._animateColorValues = animateColorValues = []

        self._target = AnimationTarget(animnode) # animation target
        self._domrect, self._domcolor = self._target.getDomValues()

        self._animateMotion = None
        self._animateWidth = None
        self._animateHeight = None
        self._animateColor = None

    def initAnimatorData(self):
        pass

    def createAnimators(self):
        import svgpath
        import Animators

        self.initAnimatorData()
        dur = 1.0
        times = self._times

        # animateMotion
        if len(self._animateMotionValues) >= 2:
            path = svgpath.Path()
            path.constructFromPoints(self._animateMotionValues)
            domval = complex(self._domrect[0],self._domrect[1])
            self._animateMotion = Animators.MotionAnimator('position', domval, path, dur, mode='linear', times=times)
        else:
            self._animateMotion = None

        # animate width and height
        if len(self._animateWidthValues) >= 2:
            self._animateWidth = Animators.Animator('width', self._domrect[2], self._animateWidthValues, dur, mode='linear', times=times)
        else:
            self._animateWidth = None

        if len(self._animateHeightValues) >= 2:
            self._animateHeight = Animators.Animator('height', self._domrect[3], self._animateHeightValues, dur, mode='linear', times=times)
        else:
            self._animateHeight = None

        # animate color
        if len(self._animateColorValues) >= 2:
            try:
                self._animateColor = Animators.ColorAnimator('backgroundColor', self._domcolor, self._animateColorValues, dur, mode='linear', times=times)
            except:
                self._animateColor = None

    def updateAnimators(self):
        self.createAnimators()

    def getDomRect(self):
        return self._domrect

    def getDomColor(self):
        self._domcolor

    def getDomPos(self):
        return self._domrect[:2]

    def getDomWidth(self):
        return self._domrect[2]

    def getDomHeight(self):
        return self._domrect[3]

    def getRectAt(self, keyTime):
        x, y = self.getPosAt(keyTime)
        w = self.getWidthAt(keyTime)
        h = self.getHeightAt(keyTime)
        return x, y, w, h

    def getColorAt(self, keyTime):
        if self._animateColor is not None and len(self._animateColorValues) > 0 and keyTime >= 0:
            if keyTime >= 1:
                return self._animateColorValues[-1]
            return self._animateColor.getValue(keyTime)
        return AnimationDefaultWrapper.getDomColor(self)

    def getPosAt(self, keyTime):
        if self._animateMotion is not None and len(self._animateMotionValues) > 0 and keyTime >= 0:
            if keyTime >= 1:
                return self._animateMotionValues[-1]
            z = self._animateMotion.getValue(keyTime)
            left, top = self._animateMotion.convert(z)
            left = round(int(left))
            top = round(int(top))
            return left, top
        return AnimationDefaultWrapper.getDomPos(self)

    def getWidthAt(self, keyTime):
        if self._animateWidth is not None and len(self._animateWidthValues) > 0 and keyTime >= 0:
            if keyTime >= 1:
                return self._animateWidthValues[-1]
            return round(int(self._animateWidth.getValue(keyTime)))
        return AnimationDefaultWrapper.getDomWidth(self)

    def getHeightAt(self, keyTime):
        if self._animateHeight is not None and len(self._animateHeightValues) > 0 and keyTime >= 0:
            if keyTime >= 1:
                return self._animateHeightValues[-1]
            return round(int(self._animateHeight.getValue(keyTime)))
        return AnimationDefaultWrapper.getDomHeight(self)

    def getKeyTimeList(self):
        return self._times

    def _intListToStr(self, sl):
        str = ''
        for val in sl:
            str = str + '%d;' % val
        return str[:-1]

    def _posListToStr(self, sl):
        str = ''
        for point in sl:
            str = str + '%d %d;' % point
        return str[:-1]

    def _colorListToStr(self, sl):
        str = ''
        for rgb in sl:
            if colors.rcolors.has_key(rgb):
                s = colors.rcolors[rgb]
            else:
                s = '#%02x%02x%02x' % rgb
            str = str + s + ';'
        return str[:-1]

    def _strToIntList(self, str):
        sl = string.split(str,';')
        vl = []
        for s in sl:
            if s:
                vl.append(string.atoi(s))
        return vl

    def _strToPosList(self, str):
        sl = string.split(str,';')
        vl = []
        for s in sl:
            if s:
                pair = self._getNumPair(s)
                if pair:
                    vl.append(pair)
        return vl

    def _getNumPair(self, str):
        if not str: return None
        str = string.strip(str)
        sl = tokenizer.splitlist(str, delims=' ,')
        if len(sl)==2:
            x, y = sl
            return string.atoi(x), string.atoi(y)
        return None

    def _strToColorList(self, str):
        vl = []
        try:
            vl = map(convert_color, string.split(str,';'))
        except ValueError:
            pass
        return vl

    def isAnimatedAttribute(self, attrName):
        return 0

    # have to be called from inside a transaction
    def insertKeyTime(self, editmgr, tp, duplicateKey=0):
        return 0

    def removeKeyTime(self, editmgr, index):
        return 0

    def changeKeyTime(self, editmgr, index, time):
        return 0

class AnimationParWrapper(AnimationDefaultWrapper):
    def __init__(self, animnode):
        AnimationDefaultWrapper.__init__(self, animnode)

    def initAnimatorData(self):
        animnode = self._animateNode
        animvals = animnode.GetAttrDef('animvals', [])

        if debug:
            print 'Create animator, animvals=',animvals

        self._times = times = []
        self._animateMotionValues = animateMotionValues = []
        self._animateWidthValues = animateWidthValues = []
        self._animateHeightValues = animateHeightValues = []
        self._animateColorValues = animateColorValues = []

        # XXX check that the list of values are consistents
        for time, vals in animvals:
            times.append(time)
            left = vals.get('left')
            top = vals.get('top')
            if left is not None and top is not None:
                animateMotionValues.append((left, top))
            width = vals.get('width')
            if width is not None:
                animateWidthValues.append(width)
            height = vals.get('height')
            if height is not None:
                animateHeightValues.append(height)
            bgcolor = vals.get('bgcolor')
            if bgcolor is not None:
                animateColorValues.append(bgcolor)

        if debug:
            print '**************************'
            print 'Create animator, values='
            print 'animateMotion:',animateMotionValues
            print 'animateWidth:',animateWidthValues
            print 'animateHeight:',animateHeightValues
            print 'animateColor:',animateColorValues
            print '**************************'

    #
    # editing operations
    #

    # have to be called from inside a transaction
    def insertKeyTime(self, editmgr, tp, duplicateKey=0):
        animateNode = self._animateNode
        animvals = animateNode.GetAttrDef('animvals', None)
        index = -1
        if animvals is not None:
            index = 0
            for time, vals in animvals:
                if time > tp:
                    break
                index = index+1
            if index > 0 and index < len(animvals):
                # can only insert a key between the first and the end
                if duplicateKey is not None and duplicateKey >= 0:
                    # duplicate a key value
                    time, vals = animvals[duplicateKey]
                    newvals = vals.copy()
                else:
                    # interpolate values at this time
                    left, top, width, height = self.getRectAt(tp)
#                                               bgcolor = self.animationWrapper.getColorAt(tp)
                    newvals = {'left':left, 'top':top, 'width':width, 'height':height}
                animateNode._currentTime = tp
                canimvals = [] # don't modify the original to make undo/redo working
                for t, v in animvals:
                    canimvals.append((t, v.copy()))

                canimvals.insert(index, (tp, newvals))
                editmgr.setnodeattr(animateNode, 'animvals', canimvals)

        return index

    def removeKeyTime(self, editmgr, index):
        animateNode = self._animateNode
        animvals = animateNode.GetAttrDef('animvals', [])
        if index > 0 and index < len(animvals)-1:

            canimvals = [] # don't modify the original to make undo/redo working
            for t, v in animvals:
                canimvals.append((t, v.copy()))

            # can only remove a key between the first and the end
            del canimvals[index]
            editmgr.setnodeattr(animateNode, 'animvals', canimvals)
            return 1

        return 0

    def changeKeyTime(self, editmgr, index, time):
        animateNode = self._animateNode
        animvals = animateNode.GetAttrDef('animvals', [])

        canimvals = [] # don't modify the original to make undo/redo working
        for t, v in animvals:
            canimvals.append((t, v.copy()))

        oldtime, vals = canimvals[index]
        canimvals[index] = (time, vals)
        editmgr.setnodeattr(animateNode, 'animvals', canimvals)

        return 1

    def changeAttributeValue(self, editmgr, attrName, attrValue, currentTimeValue, listener):
        animateNode = self._animateNode

        animvals = animateNode.GetAttrDef('animvals', [])
        canimvals = [] # don't modify the original to make undo/redo working
        for t, v in animvals:
            canimvals.append((t, v.copy()))

        keyTimeList = self.getKeyTimeList()
        keyTimeIndex = listener.getKeyForThisTime(keyTimeList, currentTimeValue, round=1)
        if keyTimeIndex is None:
            keyTimeIndex = self.insertKeyTime(editmgr, currentTimeValue)
            animvals = animateNode.GetAttrDef('animvals', [])
            self._times = []
            for time, vals in animvals:
                self._times.append(time)

            canimvals = animateNode.attrdict.get('animvals')

        time, vals = canimvals[keyTimeIndex]
        vals[attrName] = attrValue
        editmgr.setnodeattr(animateNode, 'animvals', canimvals)

        return 1

    def isAnimatedAttribute(self, attrName):
        return attrName in ('left', 'top', 'width', 'height')

class AnimationMotionWrapper(AnimationDefaultWrapper):
    def isAnimatedAttribute(self, attrName):
        return attrName in ('left', 'top')

    def changeAttributeValue(self, editmgr, attrName, attrValue, currentTimeValue, listener):
        # XXX to do
        return 0

class AnimationKeyTimesMotionWrapper(AnimationMotionWrapper):
    def initAnimatorData(self):
        animateNode = self._animateNode
        self._times = animateNode.GetAttrDef('keyTimes', [])
        strValues = animateNode.GetAttrDef('values', '')

        self._animateMotionValues = self._strToPosList(strValues)

    #
    # editing operations
    #

    # have to be called from inside a transaction
    def insertKeyTime(self, editmgr, tp, duplicateKey=0):
        animateNode = self._animateNode
        strValues = animateNode.GetAttrDef('values', '')
        animateMotionValues = self._strToPosList(strValues)

        index = 0
        for time in self._times:
            if time > tp:
                break
            index = index+1
        if index > 0 and index < len(animateMotionValues):
            # can only insert a key between the first and the end
            if duplicateKey is not None and duplicateKey >= 0:
                # duplicate a key value
                value = animateMotionValues[duplicateKey]
            else:
                # interpolate values at this time
                value = self.getPosAt(tp)

            animateMotionValues.insert(index, value)
            self._times.insert(index, tp)

            strValues = self._posListToStr(animateMotionValues)

            editmgr.setnodeattr(animateNode, 'values', strValues)
            editmgr.setnodeattr(animateNode, 'keyTimes', self._times)

        return index

    def removeKeyTime(self, editmgr, index):
        animateNode = self._animateNode
        strValues = animateNode.GetAttrDef('values', '')
        animateMotionValues = self._strToPosList(strValues)

        if index > 0 and index < len(animateMotionValues)-1:
            del animateMotionValues[index]
            del self._times[index]
            strValues = self._posListToStr(animateMotionValues)
            editmgr.setnodeattr(animateNode, 'values', strValues)
            editmgr.setnodeattr(animateNode, 'keyTimes', self._times)
            return 1

        return 0

    def changeKeyTime(self, editmgr, index, time):
        animateNode = self._animateNode
        times = self._times
        if index > 0 and index < len(times)-1:
            times[index] = time
            editmgr.setnodeattr(animateNode, 'keyTimes', times)
            return 1

        return 0

    def changeAttributeValue(self, editmgr, attrName, attrValue, currentTimeValue, listener):
        animateNode = self._animateNode
        strValues = animateNode.GetAttrDef('values', '')
        animateMotionValues = self._strToPosList(strValues)

        keyTimeList = self.getKeyTimeList()
        keyTimeIndex = listener.getKeyForThisTime(keyTimeList, currentTimeValue, round=1)
        if keyTimeIndex is None:
            keyTimeIndex = self.insertKeyTime(editmgr, currentTimeValue)
            strValues = animateNode.GetAttrDef('values', '')
            animateMotionValues = self._strToPosList(strValues)
        left, top = animateMotionValues[keyTimeIndex]
        if attrName == 'left':
            left = attrValue
        elif attrName == 'top':
            top = attrValue
        animateMotionValues[keyTimeIndex] = left, top

        strValues = self._posListToStr(animateMotionValues)
        editmgr.setnodeattr(animateNode, 'values', strValues)
        editmgr.setnodeattr(animateNode, 'keyTimes', self._times)

        return 1

def makeAnimationWrapper(animnode):
    type = animnode.GetType()
    if type == 'animpar':
        return AnimationParWrapper(animnode)
    elif type == 'animate':
        tagName = animnode.attrdict.get('atag')
        if tagName is None:
            # fail
            return AnimationDefaultWrapper(animnode)
        if tagName == 'animateMotion':
            attrdict = animnode.attrdict
            # check attributes if compatible with the editing mode
            # XXX to do
            for attrName, attrValue in attrdict.items():
                if attrName == 'keyTimes':
                    return AnimationKeyTimesMotionWrapper(animnode)
                elif attrName == 'path':
                    # not supported for now
                    return AnimationDefaultWrapper(animnode)
            return AnimationMotionWrapper(animnode)

    return AnimationDefaultWrapper(animnode)

############################
# should go normally to parse utilities
# copy/paste form SMILTreeRead

def convert_color(val):
    from colors import colors
    from SMILTreeRead import color
    import SystemColors
    val = val.lower()
    if colors.has_key(val):
        return colors[val]
    if val in ('transparent', 'inherit'):
        return val
    if SystemColors.colors.has_key(val):
        return SystemColors.colors[val]
    res = color.match(val)
    if res is None:
        self.syntax_error('bad color specification')
        return None
    hex = res.group('hex')
    if hex is not None:
        if len(hex) == 3:
            r = string.atoi(hex[0]*2, 16)
            g = string.atoi(hex[1]*2, 16)
            b = string.atoi(hex[2]*2, 16)
        else:
            r = string.atoi(hex[0:2], 16)
            g = string.atoi(hex[2:4], 16)
            b = string.atoi(hex[4:6], 16)
    else:
        r = res.group('ri')
        if r is not None:
            r = string.atoi(r)
            g = string.atoi(res.group('gi'))
            b = string.atoi(res.group('bi'))
        else:
            r = int(string.atof(res.group('rp')) * 255 / 100.0 + 0.5)
            g = int(string.atof(res.group('gp')) * 255 / 100.0 + 0.5)
            b = int(string.atof(res.group('bp')) * 255 / 100.0 + 0.5)
    if r > 255: r = 255
    if g > 255: g = 255
    if b > 255: b = 255
    return r, g, b
