__version__ = "$Id$"

# Node types.

ELEMENT                = ELEMENT_NODE                = 1
ATTRIBUTE              = ATTRIBUTE_NODE              = 2
TEXT                   = TEXT_NODE                   = 3
CDATA_SECTION          = CDATA_SECTION_NODE          = 4
ENTITY_REFERENCE       = ENTITY_REFERENCE_NODE       = 5
ENTITY                 = ENTITY_NODE                 = 6
PROCESSING_INSTRUCTION = PROCESSING_INSTRUCTION_NODE = 7
COMMENT                = COMMENT_NODE                = 8
DOCUMENT               = DOCUMENT_NODE               = 9
DOCUMENT_TYPE          = DOCUMENT_TYPE_NODE          = 10
DOCUMENT_FRAGMENT      = DOCUMENT_FRAGMENT_NODE      = 11
NOTATION               = NOTATION_NODE               = 12                      


class Node: pass
class Document(Node):

	def __init__(self, root):
		self.root = root

	def getDocumentElement(self):
		return self.root

	def createElement(self, tagName) :
	# channels, hyperlinks, elements
		nwnode = self.root.context.newnode(tagName)
		print 'nwnode ', nwnode
		return nwnode

	def createAttribute(self, name) :
		nwAttribute = Attr(name)
		return nwAttribute


class NamedNodeMap:
	def __init__(self, content=None):
		if content:
			self.__content=content
		else:
			self.__content = {}
	def getNamedItem(self, name): 
		return self.__content[name]
	def setNamedItem(self, node): 
		self.__content[node._get_nodeName()] = node
	def removeNamedItem(self, name):
		del self.__content[name]
	def item(self, index=0):
		if index >= 0 and index < len(self.__content):
			return self.__content.values()[index]
		else:
			return None
class NodeList:
	def __init__(self, nl=None) :
		if nl:
			self.__content = nl
		else:
			self.__content = [] 

	def item(self, index=0) :
		if index >= 0 and index < len(self.__content):
			return self.__content[index]
		else:
			return None	

	def _get_length(self) :
		return long(len(self.__content))

class Node: 
	def __init__(self,type=None):
		self.attrdict= {}
		self.__type = type
	def _get_nodeName(self): return self._get_name()
	def _get_nodeValue(self): return self._get_value()
	def _get_nodeType(self): return type

	
	def _get_attributes(self):
		nnm = NamedNodeMap()
		for a in self.attrdict.items() :
			if a[1]: # skip empty attributes
				attr = Attr(a[0],str(a[1]))
				nnm.setNamedItem(attr)
		return nnm
	def _get_childNodes(self): return NodeList()
	def _get_previousSibling(self): return None
	def _get_nextSibling(self): return None
	def insertBefore(self, newChild, refChild): 
		return None
	def replaceChild(self, newChild, oldChild): return None
	def removeChild(self, oldChild): return None
	def appendChild(self, newChild): return None
	

class Element(Node):
	def __init__(self, name=None):
		Node.__init__(self, ELEMENT_NODE)
		self.__name = name
		self.ex = 'Not implemented yet'
	def __repr__(self):
		return '<Element instance, tag=%s>'%self._get_tagName()
	# Element interface:
	def _get_tagName(self):
		return self.__name or self._get_nodeName()

	def getAttribute(self, name):
		return self._get_attributes().getNamedItem(name)._get_value()
	def getAttributeNode(self, name):
		return self._get_attributes().getNamedItem(name)
	def setAttribute(self,name,value):
		self.attrdict[name] = value
	def removeAttribute(self, name):
		raise self.ex
	def getAttributeNode(self, name):
		if attrdict.has_key(name):
			return self.attrdict[name]
		else:
			return None
	def setAttributeNode(self, attr):
		raise self.ex
	def removeAttributeNode(self, attr):
		raise self.ex
	def getElementsByTagName(self, name):
		raise self.ex
	def normalize():
		raise self.ex
	
	# Misc:
	
	# using dom interface
	def toxml(self, level=0, tab="  ", eol="\n"):
		  tag = self._get_tagName()
		  s = level*tab + '<' + tag
		  nnm = self._get_attributes()
		  i = 0
		  while nnm and nnm.item(i):
			  attr = nnm.item(i)
			  n = attr._get_name()
			  v = attr._get_value()
			  s = s + ' %s="%s"'%(n,v)
			  i = i+1
		  len = 0
		  nl = self._get_childNodes()
		  if nl: len = nl._get_length()
		  if len == 0:
			  return s + "/>" + eol
		  s = s + '>' + eol
		  for i in range(len):
			  child = nl.item(i)
			  s = s + level*tab
			  s = s + child.toxml(level+1, tab, eol)
		  s = s + level*tab + '</' + tag + '>' + eol
		  return s              

	def bak__cmp__(self,other) :
		# compares using attribute uid
		print "Element compare", self
		print "Element compare", len(self.attrdict)
		print "Element compare", self.getAttribute('uid')
		uidSelf = int(self.getAttribute('uid'))
		uidOther = int(self.getAttribute('uid'))
		if uidSelf < uidOther : 
			return -1
		elif uidSelf == uidOther :
			return 0
		elif uidSelf > uidOther :
			return 1


class Attr(Node):
	def __init__(self, name, value=None):
		Node.__init__(self, ATTRIBUTE_NODE)
		self.__name = name
		self.__value = value
		if value: 
			self.__specified = 1
		else:
			self.__specified = 0

	def __repr__(self):
		return '<Attr instance, name=%s, value=%s'\
		       %(self._get_name(), self._get_value())
	# Overide XML-Node implementation
	def _get_nodeName(self): return self._get_name()
	def _get_nodeValue(self): return self._get_value()

	# XML-Attr implementation
	def _get_name(self): return self.__name
	def _get_specified(self): return self.__specified
	def _get_value(self): return self.__value
