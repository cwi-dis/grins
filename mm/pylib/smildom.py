# SMIL-DOM + DOM-CORE Extensions
# Author: Kleanthis Kleanthous

import string

# Use DOM-CORE from 4DOM package
from Ft.Dom.Element import Element
from Ft.Dom.Document import Document


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
	# time types
	SMIL_TIME_INDEFINITE = 0
	SMIL_TIME_OFFSET = 1
	SMIL_TIME_SYNC_BASED = 2
	SMIL_TIME_EVENT_BASED = 3
	SMIL_TIME_WALLCLOCK = 4
	SMIL_TIME_MEDIA_MARKER = 5

	def getResolved(self):
		return 0
	def getResolvedOffset(self):
		return 0.0
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
class ElementTime:
	# restart types
	RESTART_ALWAYS = 0
	RESTART_NEVER = 1
	RESTART_WHEN_NOT_ACTIVE = 2

	# fill types
	FILL_REMOVE = 0
	FILL_FREEZE = 1

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

	def getRestart(self):
		return ElementTime.RESTART_ALWAYS
	def setRestart(self, restart):
		pass
	
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

	def getResolved(self):
		return 1


#############################################
class SMILMediaElement(SMILElement, ElementTime):
	pass

#############################################
class SMILSwitchElement(SMILElement):
	def getSelectedElement():
		return None

#############################################
class SMILAnimation(SMILElement, ElementTargetAttributes, ElementTime, ElementTimeControl):
	ADDITIVE_REPLACE = 0
	ADDITIVE_SUM = 1
	ACCUMULATE_NONE = 0
	ACCUMULATE_SUM  = 1
	
	def getAdditive(self):
		return 0
	def getAdditive(self, additive):
		pass

#############################################
class SMILAnimateElement(SMILAnimation):
	pass


#############################################
class SMILSetElement(SMILElement, ElementTimeControl, ElementTime, ElementTargetAttributes):
	pass

#############################################
class SMILAnimateColorElement(SMILAnimation):
	pass

#############################################
class SMILDocument(Document, ElementSequentialTimeContainer):
	pass


