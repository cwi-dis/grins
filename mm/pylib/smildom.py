# SMIL-DOM + DOM-CORE Extensions
# Author: Kleanthis Kleanthous

import string

# Use DOM-CORE from 4DOM package
from Ft.Dom.Element import Element
from Ft.Dom.Document import Document
from Ft.Dom.NodeList import NodeList


# version = '0.0'

#############################################
class TreeStepper:
	def __init__(self, root):
		self.__node = self.__root = root
		self.__iter = self.__itForward
		self.__endNode = None
		self.__depth = -1


	def getTreeRepr(self):
		tab = '  '
		s = '<?xml version="1.0" encoding="ISO-8859-1"?>\n'
		while self.__nextIt():
			if self.__depth>0: sp = tab*self.__depth
			else: sp =''
			if self.__iter == self.__itForward:
				if self.__endNode and self.__endNode.hasChildNodes():
					s = s + '%s</%s>\n' % (sp, self.__endNode._get_nodeName())
				s = s + '%s%s\n' % (sp, self.__elrepr(self.__node))
			else:
				if self.__node.hasChildNodes():
					s = s + '%s</%s>\n' % (sp, self.__node._get_nodeName())
		return s


	def __nextIt(self):
		return self.__iter()

	def __itForward(self):
		node = self.__node._get_firstChild()
		if node:
			self.__node = node
			self.__endNode = None
			self.__depth = self.__depth + 1
			return 1
		else:
			node = 	self.__node._get_nextSibling()
			if node:
				self.__endNode = self.__node
				self.__node = node
				return 1
			else:
				self.__iter = self.__itBackward
				#self.__node = self.__node._get_parentNode()
				return 1

	def __itBackward(self):
		node = self.__node._get_nextSibling()
		if node:
			self.__node = node
			self.__iter = self.__itForward
			return 1
		else:
			node = self.__node._get_parentNode()
			if node:
				self.__node = node
				self.__depth = self.__depth - 1
				return node._get_parentNode() != None
			else:
				return 0

	def __elrepr(self, node):
		namedNodeMap = node._get_attributes()
		n = namedNodeMap._get_length()
		L = ['<',node._get_nodeName(),]
		for name, attr in namedNodeMap.items():
			L.append(' %s="%s"' % (name, attr._get_nodeValue()))
		if node.hasChildNodes():
			L.append('>')
		else:
			L.append('/>')
		return string.join(L,'')


#############################################
import xmllib

# XXX: hard code grins namespace for now
GRiNSns = "http://www.oratrix.com/"

class TreeBuilder(xmllib.XMLParser):
	def __init__(self):
		xmllib.XMLParser.__init__(self)
		self.__reset()

	def read(self, url):
		self.__startDocument()
		u = open(url)
		data = u.read()
		self.feed(data)
		self.close()
		return self.__doc

	def readString(self, data):
		self.__startDocument()
		self.feed(data)
		self.close()
		return self.__doc
	
	def getDocument(self):
		return self.__doc

	def __reset(self):
		self.__doc = None
		self.__currentParent = None
		self.__currentNode = None
		self.__withinElement = 0
		self.__stack = []

	def __startDocument(self):
		from Ft.Dom import implementation
		self.__doc =  implementation.createDocument('','','')
		self.__currentParent = self.__doc
		self.__currentNode = self.__doc
		self.__withinElement = 0
		self.__stack = []

	def unknown_starttag(self, tag, attrs):
		# XXX: hard code grins namespace for now
		for name, value in attrs.items():
			if name[:len(GRiNSns)+1] == GRiNSns + ' ':
				del attrs[name]
				attrs['GRiNS:' + name[len(GRiNSns)+1:]] = value
		elem = self.__doc.createElement(tag)
		for name, value in attrs.items():
			elem.setAttribute(name, value)
		# XXX: hard code grins namespace for now
		if tag=='smil':
			elem.setAttribute('xmlns:GRiNS', 'http://www.oratrix.com/')
		self.__currentParent.appendChild(elem)
		self.__push(self.__currentParent)
		self.__currentParent = elem
		self.__currentNode = elem
		self.__withinElement = 1
				
	def unknown_endtag(self, tag):
		self.__currentNode = self.__currentParent
		self.__currentParent = self.__pop()
		if self.__isempty():
			self.__withinElement = 0

	# stack interface
	def __push(self, node):
		self.__stack.append(node)
	def __pop(self):
		return  self.__stack.pop()
	def __isempty(self):
		return len(self.__stack) == 0


#############################################
# SMIL-DOM Interfaces
#############################################

class Time:
	def getResolved(self):
		return 0
	def getResolvedOffset(self):
		return 0.0

	# time types
	SMIL_TIME_INDEFINITE = 0
	SMIL_TIME_OFFSET = 1
	SMIL_TIME_SYNC_BASED = 2
	SMIL_TIME_EVENT_BASED = 3
	SMIL_TIME_WALLCLOCK = 4
	SMIL_TIME_MEDIA_MARKER = 5

	def getTimeType(self):
		return Time.SMIL_TIME_INDEFINITE

	def getOffset(self):
		return 0
	def setOffset(self, offset):
		pass

	def getBaseElement(self):
		return None
	def setBaseElement(self, baseElement):
		pass

	def getBaseBegin(self):
		return 0
	def setBaseBegin(self, baseBegin):
		pass
	
	def getEvent(self):
		return ''
	def setEvent(self, event):
		pass

	def getMarker(self):
		return ''
	def setMarker(self, marker):
		pass

#############################################
class TimeList:
	def item(self, index):
		return Time()
	def getLength(self):
		return 0

#############################################
class ElementTime:
	def getBegin(self):
		return TimeList()
	def setBegin(self, beginTimeList):
		pass
	def getEnd(self):
		return TimeList()
	def setEnd(self, endTimeList):
		pass

	def getDur(self):
		return 1.0
	def setDur(self, dur):
		pass

	# restart types
	RESTART_ALWAYS = 0
	RESTART_NEVER = 1
	RESTART_WHEN_NOT_ACTIVE = 2
	def getRestart(self):
		return ElementTime.RESTART_ALWAYS
	def setRestart(self, restart):
		pass
	
	# fill types
	FILL_REMOVE = 0
	FILL_FREEZE = 1
	def getFill(self):
		return ElementTime.FILL_REMOVE
	def setFill(self, fill):
		pass

	def getRepeatCount(self):
		return 0.0
	def setRepeatCount(self, repeatCount):
		pass

	def getRepeatDur(self):
		return 0.0
	def setRepeatDur(self, repeatDur):
		pass

	def beginElement(self):
		return 1
	def endElement(self):
		return 1
	def pauseElement(self):
		pass
	def resumeElement(self):
		pass
	def seekElement(self, seekTo):
		pass

#############################################
class ElementTimeContainer(ElementTime):
	def getTimeChildren(self):
		return NodeList()

	def getActiveChildrenAt(self, instant):
		return NodeList()

#############################################
class ElementSequentialTimeContainer(ElementTimeContainer):
	pass

#############################################
class ElementParallelTimeContainer(ElementTimeContainer):
	def getEndSync(self):
		return ''

	def setEndSync(self, endSync):
		pass

	def getImplicitDuration(self):
		return 0.0

#############################################
class ElementExclusiveTimeContainer(ElementTimeContainer):
	def getEndSync(self):
		return ''

	def setEndSync(self, endSync):
		pass

	def getPausedElements(self):
		return NodeList()

#############################################
class ElementTimeControl:
	def beginElement(self):
		return 1
	def beginElementAt(self, offset):
		return 1
	def endElement(self):
		return 1
	def endElementAt(self, offset):
		return 1

#############################################
class ElementTimeManipulation:
	def getSpeed(self):
		return 1.0
	def setSpeed(self, speed):
		pass

	def getAccelerate(self):
		return 1.0
	def setAccelerate(self, accelerate):
		pass

	def getDecelerate(self):
		return 1.0
	def setDecelerate(self, decelerate):
		pass

	def getAutoReverse(self):
		return (1==0)
	def setAutoReverse(self, autoReverse):
		pass

#############################################
class ElementSyncBehavior:
	def getSyncBehavior(self):
		return ''

	def getSyncTolerance(self):
		return 0.0

	def getDefaultSyncBehavior(self):
		return ""
	
	def getDefaultSyncTolerance(self):
		return 0.0

	def getSyncMaster(self):
		return (1==1)


#############################################
class ElementTargetAttributes:
	# attributeTypes
	ATTRIBUTE_TYPE_AUTO = 0
	ATTRIBUTE_TYPE_CSS = 1
	ATTRIBUTE_TYPE_XML = 2

	def getAttributeName(self):
		return ''
	def setAttributeName(self, attributeName):
		pass

	def getAttributeType(self):
		return ElementTargetAttributes.ATTRIBUTE_TYPE_AUTO
	def setAttributeType(self, attributeType):
		pass

#############################################
class ElementLayout:
	def getTitle(self):
		return ''
	def setTitle(self, title):
		pass
	def getBackgroundColor(self):
		return ''
	def setBackgroundColor(self, backgroundColor):
		pass
	def getHeight(self):
		return 0
	def setHeight(self, height):
		pass
	def getWidth(self):
		return 0
	def setWidth(self, width):
		pass

#############################################
class ElementTest:
	def getSystemBitrate(self):
		return 0
	def setSystemBitrate(self, systemBitrate):
		pass

	def getSystemCaptions(self):
		return (1!=0)
	def setSystemCaptions(self, systemCaptions):
		pass

	def getSystemLanguage(self):
		return ''
	def setSystemLanguage(self, systemLanguage):
		pass

	def getSystemRequired(self):
		return (1!=0)

	def getSystemScreenSize(self):
		return (1!=0)

	def getSystemScreenDepth(self):
		return (1!=0)

	def getSystemOverdubOrSubtitle(self):
		return ''

	def getSystemAudioDesc(self):
		return (1!=0)
	def setSystemAudioDesc(self, systemAudioDesc):
		return (1!=0)


#############################################
class SMILRegionInterface:
	def getRegion(self):
		return None # SMILRegionElement()
	def setRegion(self, region):
		pass


#############################################
# SMIL-DOM
#############################################

class SMILElement(Element):
	rwattrs = ('ID',)
	def __init__(self, ownerDocument, tagName, nodeName):
		Element.__init__(self, ownerDocument, nodeName, '', '',nodeName)
		self.__dict__['tagName'] = tagName

	def __getattr__(self, name):
		if name in self.rwattrs:
			func = getattr(self, '_get_' + name)
			return apply(func, ())
		else:
			if self.__dict__.has_key(name):
				return self.__dict__[name]
			raise AttributeError(name)

	def __setattr__(self, name, value):
		if name in self.rwattrs:
			self.setAttribute(name, value)
		else:
			return Element.__setattr__(self, name, value)

	def _get_ID(self):
		return self.getAttribute('ID')
	
	def _set_ID(self,ID):
		self.setAttribute('ID',ID)

#############################################
class SMILLayoutElement(SMILElement):
	rwattrs = ('TYPE',)
	def __init__(self, ownerDocument, nodeName='LAYOUT'):
		SMILElement.__init__(self, ownerDocument, 'LAYOUT', nodeName)

	def __setattr__(self, name, value):
		if name in rwattrs:
			self.setAttribute(name, value)
		else:
			return SMILElement.__setattr__(self, name, value)

	def _get_Type(self):
		return self.getAttribute('TYPE')

	def _set_Type(self,type):
		self.setAttribute('TYPE',type)

	def _get_Resolved(self):
		return 1

#############################################
class SMILRootLayoutElement(SMILElement, ElementLayout):
	pass

#############################################
class SMILTopLayoutElement(SMILElement, ElementLayout):
	pass

#############################################
class SMILRegionElement(SMILElement, ElementLayout):
	def getFit(self):
		return ''
	def setFit(self, fit):
		pass

	def getTop(self):
		return ''
	def setTop(self, top):
		pass

	def getZIndex(self):
		return 0
	def setZIndex(self, zIndex):
		pass

#############################################
class SMILMediaElement(SMILElement, ElementTime):
	def getAbstractAttr(self):
		return ''
	def setAbstractAttr(self, abstractAttr):
		pass

	def getAlt(self):
		return ''
	def setAlt(self, alt):
		pass

	def getAuthor(self):
		return ''
	def setAuthor(self, author):
		pass

	def getClipBegin(self):
		return ''
	def setClipBegin(self, clipBegin):
		pass

	def getClipEnd(self):
		return ''
	def setClipEnd(self, clipEnd):
		pass

	def getCopyright(self):
		return ''
	def setCopyright(self, copyright):
		pass

	def getLongdesc(self):
		return ''
	def setLongdesc(self, longdesc):
		pass

	def getPort(self):
		return ''
	def setPort(self, port):
		pass

	def getReadIndex(self):
		return ''
	def setReadIndex(self, readIndex):
		pass

	def getRtpformat(self):
		return ''
	def setRtpformat(self, rtpformat):
		pass

	def getSrc(self):
		return ''
	def setSrc(self, src):
		pass

	def getStripRepeat(self):
		return ''
	def setStripRepeat(self, stripRepeat):
		pass

	def getTitle(self):
		return ''
	def setTitle(self, title):
		pass

	def getTransport(self):
		return ''
	def setTransport(self, transport):
		pass

	def getType(self):
		return ''
	def setType(self, stype):
		pass

#############################################
class SMILRefElement(SMILMediaElement):
	pass

#############################################
class SMILSwitchElement(SMILElement):
	def getSelectedElement():
		return None

#############################################
class SMILAnimation(SMILElement, ElementTargetAttributes, ElementTime, ElementTimeControl):
	# additiveTypes
	ADDITIVE_REPLACE = 0
	ADDITIVE_SUM = 1
	def getAdditive(self):
		return SMILAnimation.ADDITIVE_REPLACE
	def setAdditive(self, additive):
		pass

	# accumulateTypes
	ACCUMULATE_NONE = 0
	ACCUMULATE_SUM  = 1

	def getAccumulate(self):
		return SMILAnimation.ACCUMULATE_NONE
	def setAccumulate(self, accumulate):
		pass

	# calcModeTypes
	CALCMODE_DISCRETE = 0
	CALCMODE_LINEAR = 1
	CALCMODE_PACED = 2
	CALCMODE_SPLINE = 3

	def getCalcMode(self):
		return SMILAnimation.CALCMODE_LINEAR
	def setCalcMode(self, calcMode):
		pass

	def getKeySplines(self):
		return ''
	def setKeySplines(self, keySplines):
		pass

	def getKeyTimes(self):
		return TimeList()
	def setKeyTimes(self, keyTimes):
		pass

	def getValues(self):
		return ''
	def setValues(self, values):
		pass

	def getFrom(self):
		return ''
	def setFrom(self, fromVal):
		pass

	def getTo(self):
		return ''
	def setTo(self, toVal):
		pass

	def getBy(self):
		return ''
	def setBy(self, byVal):
		pass

#############################################
class SMILAnimateElement(SMILAnimation):
	pass


#############################################
class SMILSetElement(SMILElement, ElementTimeControl, ElementTime, ElementTargetAttributes):
	def getTo(self):
		return ''
	def setTo(self, to):
		pass

#############################################
class SMILAnimateColorElement(SMILAnimation):
	pass

#############################################
class SMILAnimateMotionElement(SMILAnimateElement):
	def getPath(self):
		return ""
	def setPath(self, path):
		pass

	def getOrigin(self):
		return ""
	def setOrigin(self, origin):
		pass

#############################################
class SMILDocument(Document, ElementSequentialTimeContainer):
	pass


