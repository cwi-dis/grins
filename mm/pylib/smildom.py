# DOM-CORE + SMIL-DOM
# Author: Kleanthis Kleanthous


# DOM core implementation is based on Apache XercesLib
# Apache XercesLib was originally based on IBM XML4C lib

version = '0.0'

#############################################
# constants

# node types

ELEMENT_NODE		 = 1
ATTRIBUTE_NODE       = 2
TEXT_NODE		     = 3
CDATA_SECTION_NODE   = 4
ENTITY_REFERENCE_NODE = 5
ENTITY_NODE		  = 6
PROCESSING_INSTRUCTION_NODE = 7
COMMENT_NODE		 = 8
DOCUMENT_NODE		= 9
DOCUMENT_TYPE_NODE   = 10
DOCUMENT_FRAGMENT_NODE = 11
NOTATION_NODE		= 12


# exception codes

INDEX_SIZE_ERR       = 1
DOMSTRING_SIZE_ERR   = 2
HIERARCHY_REQUEST_ERR = 3
WRONG_DOCUMENT_ERR   = 4
INVALID_CHARACTER_ERR = 5
NO_DATA_ALLOWED_ERR  = 6
NO_MODIFICATION_ALLOWED_ERR = 7
NOT_FOUND_ERR        = 8
NOT_SUPPORTED_ERR    = 9
INUSE_ATTRIBUTE_ERR  = 10
INVALID_STATE_ERR    = 11
SYNTAX_ERR	     = 12
INVALID_MODIFICATION_ERR    = 13
NAMESPACE_ERR	     = 14
INVALID_ACCESS_ERR   = 15
FEATURE_NOT_IMPLEMENTED_ERR    = 101


#############################################
# exceptions

class DOMException:
    def __init__(self, msg=''):
        self.__msg = msg
    def __repr__(self):
        return self.__msg

class IndexSizeException(DOMException):
	code = INDEX_SIZE_ERR
class DomstringSizeException(DOMException):
	code = DOMSTRING_SIZE_ERR
class HierarchyRequestException(DOMException):
	code = HIERARCHY_REQUEST_ERR
class WrongDocumentException(DOMException):
	code = WRONG_DOCUMENT_ERR
class InvalidCharacterException(DOMException):
	code = INVALID_CHARACTER_ERR
class NoDataAllowedException(DOMException):
	code = NO_DATA_ALLOWED_ERR
class NoModificationAllowedException(DOMException):
	code = NO_MODIFICATION_ALLOWED_ERR
class NotFoundException(DOMException):
	code = NOT_FOUND_ERR
class NotSupportedException(DOMException):
	code = NOT_SUPPORTED_ERR
class InuseAtrributeException(DOMException):
	code = INUSE_ATTRIBUTE_ERR
class InvalidStateException(DOMException):
	code = INVALID_STATE_ERR
class SyntaxException(DOMException):
	code = SYNTAX_ERR
class InvalidModificationException(DOMException):
	code = INVALID_MODIFICATION_ERR
class NamespaceException(DOMException):
	code = NAMESPACE_ERR
class InvalidAccessException(DOMException):
	code = INVALID_ACCESS_ERR
class FeatureNotImplementedException(DOMException):
	code = FEATURE_NOT_IMPLEMENTED_ERR

#############################################
# utilities

def isXMLName(name):
	return 1

def xmlEscape(data, entities = {}):
	data = data.replace("&", "&amp;")
	data = data.replace("<", "&lt;")
	data = data.replace(">", "&gt;")
	for chars, entity in entities.items():
		data = data.replace(chars, entity)        
	return data
		
#############################################
class Node:
	def __init__(self, ownerDocument = None, name = '', type = 0, isLeafNode = 0, initValue = '', \
			namespaceURI = '', qualifiedName = ''):
		
		self._ownerDocument = ownerDocument

		self._name = name

		self._type = type

		#
		self._value = initValue

		# tree refs
		self._parentNode = None
		self._nextSibling = None
		self._firstChild = None												   
		
		# cashed tree refs	
		self._lastChild = None
		self._previousSibling = None

		# if true, no children permitted
		self._isLeafNode = isLeafNode

		# 
		self._readOnly = 0

		# true if there is a reference to this node in a named node list.  
		# applies to attributes, notations, entities.
		self._owned = 0					

		# changes counter
		self._changes = 0

		# user hook
		self._userData = None

		# DOM 2
		self._namespaceURI = namespaceURI		# namespace URI of this node
		self._prefix = ''						# namespace prefix of this node
		self._localName = ''					# local part of qualified name


	def getNodeName(self):
		return self._name

	def getNodeType(self):
		return self._nType

	def getNodeValue(self):
		return self._value

	def getOwnerDocument(self):
		return self._ownerDocument

	def getParentNode(self):
		return self._parentNode

	def getFirstChild(self):
		return self._firstChild

	def getLastChild(self):
		return self._lastChild

	def getNextSibling(self):
		return self._nextSibling

	def getPreviousSibling(self):
		return self._previousSibling

	def getUserData(self):
		return self._userData

	def hasChildNodes(self):
		return self._firstChild != None

	# return an object exposing interface of NodeList
	def getChildNodes(self):
		return self

	def getAttributes(self):
		return None # will be overridden by Element

	def getNamespaceURI(self):
		return self._namespaceURI

	def getPrefix(self):
		return self._prefix

	def getLocalName(self):
		return self._localName

	def	insertBefore(self, newChild, refChild):
		return self._insertBefore(newChild, refChild)

	def	appendChild(self, newChild):
		return self._insertBefore(newChild, None)

	def	removeChild(self, oldChild):
		return self._removeChild(oldChild)

	def replaceChild(self, newChild, oldChild):
		self.__insertBefore(newChild, oldChild)
		return self._removeChild(oldChild)

	def setNodeValue(self, val):
		if self._readOnly:
			raise NoModificationAllowedException()
		self._value = val

	def setUserData(self, val):
		self._userData = val

	def setPrefix(self, prefix):
		raise FeatureNotImplementedException()
			
	def normalize(self):
		raise FeatureNotImplementedException()		

	def supports(self, feature, version):
		raise FeatureNotImplementedException()		

	def cloneNode(self, deep):
		return Node().__init_to(self, deep)

	# node list interface implementation
	def getLength(self):
		n = self._firstChild
		count = 0
		while n:
			count = count + 1
			n = n._nextSibling
		return count

	def item(self, index):
		n = self._firstChild
		i = 0
		while i<index and n:
			n = n._nextSibling
			i = i + 1
		return n
	
	######################################################
	# PRIVATE SECTION

	# type check replacement
	def _isAttr(self):return 0
	def _isCDATASection(self):return 0
	def _isDocumentFragment(self):return 0
	def _isDocument(self):return 0
	def _isDocumentType(self):return 0
	def _isElement(self):return 0
	def _isEntityReference(self):return 0
	def _isText(self):return 0

	def _setReadOnly(self, readOnly, deep):
		self._readOnly = readOnly
		if deep:
			kid = self._firstChild
			while kid:
				if not kid._isEntityReference():
					kid._setReadOnly(readOnly, true)
				kid = kid._nextSibling

	def _changed(self):
		n = self
		while n:
			n._changes = n._changes + 1
			n = n._parentNode

	# copy constructor
	def _init_to(self, other, deep):
		raise FeatureNotImplementedException()		

	def _isKidOK(self, parent, child):
		return 1

	def _insertBefore(self, newChild, refChild):
		if self._readOnly:
			raise NoModificationAllowedException()
		
		# check doc
		difdoc = newChild.getOwnerDocument() != self._ownerDocument
		isdocchild = self._isDocument() and newChild.getOwnerDocument() == self
		if difdoc and not isdocchild:
			raise WrongDocumentException()
		
		# prevent cycles
		issafe = 1
		n = self._parentNode
		while issafe and n:
			issafe = (newChild != n)
			n = n._parentNode
		if not issafe:
			raise HierarchyRequestException()
			
		# refChild must in fact be a child of this node (or None)
		if refChild and refChild._parentNode != self:
			raise NotFoundException()

		# XXX: no document fragment support yet
		if newChild._isDocumentFragment():
			raise FeatureNotImplementedException()		
		elif not self._isKidOK(self, newChild):
			raise FeatureNotImplementedException()
		else:
			oldparent = newChild._parentNode
			if oldparent:
				oldparent.__removeChild(newChild)

			if refChild:
				prev = refChild._previousSibling
			else:
				prev = self._lastChild

			# attach up
			newChild._parentNode = self

			# attach after
			newChild._previousSibling = prev
			if not prev:
				self._firstChild = newChild 
			else:
				prev._nextSibling = newChild
					 
			# attach before
			newChild._nextSibling = refChild
			if refChild:
				refChild._previousSibling = newChild
			else:
				self._lastChild = newChild								      			
		self._changed()
		return newChild

	def _removeChild(self, oldChild):
		if self._readOnly:
			raise NoModificationAllowedException()
		if oldChild and oldChild._parentNode != self:
			raise NotFoundException()
		
		# patch tree past oldChild
		prev = oldChild._previousSibling
		next = oldChild._nextSibling
		if prev:
			prev._nextSibling = next
		else:
			self._firstChild = next
		if next:
			next._previousSibling = prev
		else:
			self._lastChild = prev

		# remove oldChild's references to tree
		oldChild._parentNode = None
		oldChild._nextSibling = None
		oldChild._previousSibling = None

		self._changed()
		return oldChild

	def __repr__(self):
		return '[%s:%s]' % (self.getNodeName(), self.getNodeValue())



#############################################
class Element(Node):
	def __init__(self, ownerDocument = None, name = '', namespaceURI = '', qualifiedName=''):
		Node.__init__(self, ownerDocument, name, ELEMENT_NODE, 0)
		self._attributes = {}

	def getTagName(self):
		return self._name

	def getAttribute(self, name):
		node = self._attributes.get(name)
		if node: return node.getValue()
		return None

	def getAttributes(self):
		return self # XXX 

	def getAttributeNode(self, name):
		return self._attributes.get(name)

	def getElementsByTagName(self, name):
		raise FeatureNotImplementedException()		

	def setAttribute(self, name, value):
		self.__setAttribute(name, value)

	def setAttributeNode(self, newAttr):
		return self.__setAttributeNode(newAttr)

	def removeAttributeNode(self, oldAttr):
		return self.__removeAttributeNode(oldAttr)

	def removeAttribute(self, name):
		self.__removeAttribute(name)

	def getAttributeNS(self, namespaceURI, localName):
		return ''

	def setAttributeNS(self, namespaceURI, qualifiedName, value):
		pass

	def removeAttributeNS(self, namespaceURI, localName):
		pass

	def getAttributeNodeNS(self, namespaceURI, localName):
		return None

	def setAttributeNodeNS(self, newAttr):
		return None

	def getElementsByTagNameNS(self, namespaceURI, localName):
		return None

	def setNodeValue(self, val):
		raise NoModificationAllowedException()

	######################################################
	# PRIVATE SECTION

	def _isElement(self):
		return 1

	def __setAttribute(self, name, value):
		if self._readOnly:
			raise NoModificationAllowedException()
		newAttr = self._ownerDocument.createAttribute(name)
		newAttr.setNodeValue(value)
		newAttr._setOwnerElement(self) # DOM2
		# fix for named node map
		if self._attributes.has_key(name):
			oldAttr = self._attributes[name]
			oldAttr._setOwnerElement(None) # DOM2
		self._attributes[name] = newAttr

	def __removeAttribute(self, name):
		if self._readOnly:
			raise NoModificationAllowedException()
		a = self._attributes.get('name')
		if a:
			del self._attributes[name]
			a.setOwnerElement(None)

	def __removeAttributeNode(self, oldAttr):
		if self._readOnly:
			raise NoModificationAllowedException()
		a = self._attributes.get(oldAttr.getName())
		if a == oldAttr:
			del self._attributes[oldAttr.getName()]
			a.setOwnerElement(None)
			return a
		else:
			raise NotFoundException()

	def __setAttributeNode(self, newAttr):
		if self._readOnly:
			raise NoModificationAllowedException()
		if not newAttr.isAttr():
			raise WrongDocumentException()
		old = self._attributes.get(newAttr.getName())
		if old:
			old.setOwnerElement(None)
		# XXX: check NamedNodeMap implementation
		self._attributes[newAttr.getName()] = newAttr
		return old

	def __repr__(self):
		l = ["<", self._name]
		for name, node in self._attributes.items():
			l.append(' ')
			l.append(repr(node))
		if self.hasChildNodes():
			l.append('>')
		else:
			l.append('/>')
		import string
		return string.join(l, '')

#############################################
class Attr(Node):
	def __init__(self, ownerDocument, name):
		Node.__init__(self, ownerDocument, name, ELEMENT_NODE, 0)
		self._specified = 1
		self._ownerElement = None

	def getName(self):
		return self._name

	def getSpecified(self):
		return self._specified

	def getValue(self):
		return self._getValue()

 	def setValue(self, val):
		self._setValue(val)

 	def setSpecified(self, spec):
		self._specified = spec

	def getOwnerElement(self):
		return self._ownerElement

	# override node's method
	def getNodeValue(self):
		return self._getValue()

	# override node's method
	def setNodeValue(self, val):
		self._setValue(val)

	######################################################
	# PRIVATE SECTION

	def _isAttr(self):
		return 1

	def _setOwnerElement(self, ownerElem):
		self._ownerElement = ownerElem

	def _cloneNode(self, deep):
		return Attr()._init_to(self, deep)

	def _getValue(self):
		retString = ''
		n = self.getFirstChild()
		while n:
			retString = retString + n.getNodeValue()
			n = n.getNextSibling()
		return retString

	def _setValue(self, val):
		if self._readOnly:
			raise NoModificationAllowedException()
		kid = self.getFirstChild()
		while kid:
			self.removeChild(kid)
			kid = self.getFirstChild()
		if val:
			self.appendChild(self._ownerDocument.createTextNode(val))
		specified = 1
		self._changed()

	def __repr__(self):
		return self._name + '=\"' + self.getValue() + '\"'


#############################################
class CharacterData(Node):
	def __init__(self, ownerDocument, name, type, data):
		Node.__init__(self, ownerDocument, name, type, 1, data)

	def getData(self):
		return self._value

	def getLength(self):
		return len(self._value)

	def substringData(self, offset, count):
		return self._value[offset:(offset+count)]

	def appendData(self, arg):
		self._value = self._value + arg

	def insertData(self, offset, arg):
		pass

	def deleteData(self, offset, count):
		pass

	def replaceData(self, offset, count, arg):
		pass

	def setData(self, data):
		pass


#############################################
class Text(CharacterData):
	def __init__(self, ownerDoc, data):
		CharacterData.__init__(self, ownerDoc, "#text", TEXT_NODE, data)

	def splitText(self, offset):
		return ''

	##########################################
	# PRIVATE SECTION
	def _isText(self):
		return 1

	def _cloneNode(self, deep):
		return self._ownerDocument.createTextNode(self._value)

	def __repr__(self):
		return self._value

#############################################
class CDATASection(Text):
	def __init__(self, ownerDoc, data):
		Text.__init__(self, ownerDoc, data)
		self._name = '#cdata-section'
		self._type = CDATA_SECTION_NODE

	#########################################
	# PRIVATE SECTION
	def _isCDATASection(self):
		return 1

	def _cloneNode(self, deep):
		return CharacterData()._init_to(self, deep)

#############################################
class Comment(CharacterData):
	def __init__(self, ownerDoc, data):
		CharacterData.__init__(self, ownerDoc, '#comment', COMMENT_NODE, data)

	#########################################
	# PRIVATE SECTION
	def _isComment(self):
		return 1


#############################################
class Notation(Node):
	def __init__(self, ownerDoc, notationName):
		Node.__init__(self, ownerDoc, notationName, NOTATION_NODE, 1, '')

	#########################################
	# PRIVATE SECTION
	def _isNotation(self):
		return 1

#############################################
class ProcessingInstruction(Node):
	def __init__(self, ownerDoc = None, target = '', data = ''):
		Node.__init__(self,ownerDoc, target, PROCESSING_INSTRUCTION_NODE, 1, data)

	def getData(self):
		return self._value
	
	def getTarget(self):
		return self._name
	
	def setData(self, arg):
		if readOnly:
			raise NoModificationAllowedException()
		self._value = arg

	#########################################
	# PRIVATE SECTION
	def _isProcessingInstruction(self):
		return 1

	def _cloneNode(self, deep):
		return ProcessingInstruction()._init_to(self, deep)

#############################################
class Entity(Node):
	def __init__(self, ownerDoc, entityName):
		Node.__init__(self, ownerDoc, entityName, ENTITY_NODE, 0, '')
		self._publicId = ''
		self._systemId = ''
		self._notationName = ''

	def getNotationName(self):
		return self._notationName

	def getPublicId(self):
		return self._publicId

	def getSystemId(self):
		return self._systemId

	def setNodeValue(self, val):
		raise NoModificationAllowedException()

	def setNotationName(self, arg):
		self._notationName = arg

	def setPublicId(self, arg):
		self._publicId = arg

	def setSystemId(self, arg):
		self._systemId = arg

	#########################################
	# PRIVATE SECTION
	def _isEntity(self):
		return 1
	
	def _cloneNode(self, deep):
		return Entity()._init_to(self, deep)


#############################################
class EntityReference(Node):
	def __init__(self, ownerDoc, entityName):
		Node.__init__(self, ownerDoc, entityName, ENTITY_REFERENCE_NODE, 0, '')
		self._readOnly = 1
		self._entityChanges = -1

	def getChildNodes(self):
		self.__synchronize()
		return Node.getChildNodes(self)

	def getFirstChild(self):
		self.__synchronize()
		return Node.getFirstChild(self)

	def getLastChild(self):
		self.__synchronize()
		return Node.getFirstChild(self)


	def setNodeValue(self, val):
		raise NoModificationAllowedException()		

	def getLength(self):
		return Node.getLength(self)

	def item(self, index):
		self.__synchronize()
		return Node.item(self, index)

	#########################################
	# PRIVATE SECTION
	def _isEntityReference(self):
		return 1

	def _setReadOnly(self, readOnl, deep):
		if not self._readOnly:
			raise NoModificationAllowedException()
		Node._setReadOnly(self, readOnl, deep)

	def __synchronize():
		pass

#############################################
class DocumentType(Node):
	def __init__(self, qualifiedName='', publicId='', systemId='', ownerDoc = None, dtName = ''):
		if not qualifiedName:
			Node.__init__(self, ownerDoc, dtName, DOCUMENT_TYPE_NODE,0,'')
		else:
			Node.__init__(self, None, qualifiedName, DOCUMENT_TYPE_NODE,0,'')
		self._publicId = publicId
		self._systemId = systemId
		self._entities = {}
		self._notations = {}
		self._elements = {} # XDOM

	def getElements(self):
		return self._elements

	def getEntities(self):
		return self._elements

	def getNotations(self):
		return self._notations

	def setNodeValue(self, val):
		raise NoModificationAllowedException()		

	def getPublicId(self):
		return self._publicId

	def getSystemId(self):
		return self._systemId

	def getInternalSubset():
		raise FeatureNotImplementedException()		

	#########################################
	# PRIVATE SECTION
	def _isDocumentType(self):
		return 1
	
	def _setReadOnly(self, deep):
		Node._setReadOnly(self, deep)
		# set also entities and notations


#############################################
class DocumentFragment(Node):
	def __init__(self, masterDoc = None):
		Node.__init__(self, masterDoc, '#document-fragment', DOCUMENT_FRAGMENT_NODE, 0, '')

	def setNodeValue(self, val):
		raise NoModificationAllowedException()

	#########################################
	# PRIVATE SECTION
	def _isDocumentFragment(self):
		return 1
	
	def _cloneNode(self, deep):
		return DocumentFragment()._init_to(self, deep)

#############################################
class Document(Node):
	def __init__(self, namespaceURI = '', qualifiedName = '', doctype = None):
		Node.__init__(self, None, '#document', DOCUMENT_NODE, 0)
		self._docType = None
		self._docElement = None
		self._namePool = None
		self._iterators = None
		self._treeWalkers = None

	def createCDATASection(self, data):
		return CDATASection(self, data)

	def createComment(self, data):
		return Comment(self, data)

	def createDocumentFragment(self):
		return DocumentFragment(self)

	def createDocumentType(self, name):
		if not self._isXMLName(name):
			raise InvalidCharacterException()
		return DocumentType(self, name)

	def createElement(self, tagName):
		if not self._isXMLName(tagName):
			raise InvalidCharacterException()
		return Element(self, tagName)

	def createEntity(self, name):
		if not self._isXMLName(name):
			raise InvalidCharacterException()
		return Entity(self, name)

	def createEntityReference(self, name):
		if not self._isXMLName(name):
			raise InvalidCharacterException()
		return EntityReference(self, name)

	def createNotation(self, name):
		if not self._isXMLName(name):
			raise InvalidCharacterException()
		return Notation(self, name)

	def createProcessingInstruction(self, target, data):
		if not self._isXMLName(target):
			raise InvalidCharacterException()
		return ProcessingInstruction(self, target, data)

	def createTextNode(self, data):
		return Text(self, data);

	def createAttribute(self, name):
		if not self._isXMLName(name):
			raise InvalidCharacterException()
		return Attr(self,name)

	def getDoctype(self):
		return self._docType

	def getImplementation(self):
		class I:
			def hasFeature(self, feature, version=''): 
				return hasFeature(feature, version)
			def createDocumentType(self, qualifiedName, publicId, systemId):
				return createDocumentType(qualifiedName, publicId, systemId)
			def createDocument(self, namespaceURI = '', qualifiedName = '', doctype = None):
				return createDocument(namespaceURI, qualifiedName, doctype)
		return I()

	def getDocumentElement(self):
		return self._docElement

	def getElementsByTagName(self, tagname):
		return None

	# DOM 2
	def importNode(self, source, deep):
		return None

	def createElementNS(self, namespaceURI, qualifiedName):
		return None

	def createAttributeNS(self, namespaceURI, qualifiedName):
		return None

	def getElementsByTagNameNS(self, namespaceURI, localName):
		return None

	def getElementById(self, elementId):
		return None

	def indexofQualifiedName(self, qName):
		return -1

	def createNodeIterator(self, root, whatToShow, filter, entityReferenceExpansion):
		return None

	def createTreeWalker(self, root, whatToShow, filter, entityReferenceExpansion):
		return None

	def importNode(self, importedNode, deep):
		return None


	######################################################
	# PRIVATE SECTION

	def _isDocument(self):
		return 1

	def _isXMLName(self, name):
		return 1

	def __repr__(self):
		return '<DOM Document>'
		
	# override node's _insertBefore
	def _insertBefore(self, newChild, refChild):
		if (newChild._isElement() and self._docElement) or (newChild._isDocumentType() and self._docType):
			raise HierarchyRequestException()
		Node._insertBefore(self, newChild, refChild)
		if newChild._isElement():
			self._docElement = newChild
		elif newChild._isDocumentType():
			self._docType = newChild
		return 	newChild


#############################################
# implements a depth first walk
class TreeStepper:
	def __init__(self, root):
		self.__node = self.__root = root
		self.__iter = self.__itForward
		self.__endNode = None
		self.__depth = -1

	def __nextIt(self):
		return self.__iter()

	def __itForward(self):
		node = self.__node.getFirstChild()
		if node:
			self.__node = node
			self.__endNode = None
			self.__depth = self.__depth + 1
			return 1
		else:
			node = 	self.__node.getNextSibling()
			if node:
				self.__endNode = self.__node
				self.__node = node
				return 1
			else:
				self.__iter = self.__itBackward
				#self.__node = self.__node.getParentNode()
				return 1

	def __itBackward(self):
		node = self.__node.getNextSibling()
		if node:
			self.__node = node
			self.__iter = self.__itForward
			return 1
		else:
			node = self.__node.getParentNode()
			if node:
				self.__node = node
				self.__depth = self.__depth - 1
				return node.getParentNode() != None
			else:
				return 0

	def getTreeRepr(self):
		tab = '  '
		s = '<?xml version="1.0" encoding="ISO-8859-1"?>\n'
		while self.__nextIt():
			if self.__depth>0: sp = tab*self.__depth
			else: sp =''
			if self.__iter == self.__itForward:
				if self.__endNode and self.__endNode.hasChildNodes():
					s = s + '%s</%s>\n' % (sp, self.__endNode.getNodeName())
				s = s + '%s%s\n' % (sp, repr(self.__node))
			else:
				if self.__node.hasChildNodes():
					s = s + '%s</%s>\n' % (sp, self.__node.getNodeName())
		return s

	def printTreeRepr(self):
		tab = '  '
		print '<?xml version="1.0" encoding="ISO-8859-1"?>'
		while self.__nextIt():
			if self.__depth>0: sp = tab*self.__depth
			else: sp =''
			if self.__iter == self.__itForward:
				if self.__endNode and self.__endNode.hasChildNodes():
					print '%s</%s>' % (sp, self.__endNode.getNodeName())
				print '%s%s' % (sp, repr(self.__node))
			else:
				if self.__node.hasChildNodes():
					print '%s</%s>' % (sp, self.__node.getNodeName())

##################
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
		self.__doc = createDocument()
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
	def getId(self):
		return 0
	def setId(self, id):
		pass

#############################################
class SMILLayoutElement(SMILElement):
	def getType(self):
		return ''
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




#############################################
# DOMImplementation methods
#############################################

def hasFeature(feature, version=''):
	feature = feature.lower()
	version = version.lower()
	if feature=='xml':
		if not version or version=='1.0' or version == '2.0':
			return 1
	if feature=='traversal':
		return 1
	return 0

# DOM 2
def createDocumentType(qualifiedName, publicId, systemId):
	if not isXMLName(qualifiedName):
		raise InvalidCharacterException()
	return DocumentType(qualifiedName, publicId, systemId)

# DOM 2
def createDocument(namespaceURI = '', qualifiedName = '', doctype = None):
	return Document(namespaceURI, qualifiedName, doctype)

