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

	def createElement(self, tagName, defIndex=0, defChannelType='layout') :
		""" 
		Creates Elements in three diffrent types:
		- channels	: tagName = 'channel', 
					name='_changeMe', 	# change this after creation!
					index=0, 		# (add 1st)  
					type='layout' 		# change this after creation!
		- hyperlinks
		- elements	: tagName = elementname
		"""
	# channels, hyperlinks, elements
		if tagName == 'channel' :
			# every channel has a name and a type. createElement only has only one argument which
			# is reserverd for the elementname 'channel' (which indicates you want to create
			# a channel)  Obviously this conflicts. 
			# We solve this by first creating an Elementobject with 2 default attributes, 'name' 
			# and 'type' with both a defaultvalue wich should be changed by the user.
			# If and only if both name and type are changed the channel (Element) could be added 
			# to the tree (--> root.firstChild = context),  otherwise an exception is raised
			#
			#	the appendChild (and similar) function scans for elements with special 
			#	tagnames ('channel', 'hyperlink') and handles them diffrently

			nwChannel = Element(tagName)
			nwChannel.setAttribute('name', '')
			nwChannel.setAttribute('type', '')
			return nwChannel
		elif tagName == 'link':
			print "Document.createElement() creating link ..."
			# hyperlink
			nwLink = Element(tagName)
			return nwLink
		else:
			nwNode = self.root.context.newnode(tagName)
			print 'nwNode ', nwNode
			return nwNode

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
		if self.__content.has_key(name):
			return self.__content[name]
		else:
			return None
	def setNamedItem(self, node): 
		self.__content[node._get_nodeName()] = node
	def removeNamedItem(self, name):
		if self.__content.has_key(name):
			delnode = self.getNamedItem(name)
			del self.__content[name]
			return delnode
		else:
			return None
	def item(self, index=0):
		if index >= 0 and index < len(self.__content):
			return self.__content.values()[index]
		else:
			return None

	def _get_length(self) :
		return len(self.__content)
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
	def _get_nodeType(self): return self.__type
        def _get_parentNode(self) : return None
	def _get_childNodes(self): return NodeList()
	def _get_firstChild(self) :
		children = self._get_childNodes()
		len = children._get_length()
		if len > 0:
			return children.item(0)
		else:
			return None
	def _get_lastChild(self) :
		children = self._get_childNodes()
		len = children._get_length()
		if len > 0:
			result = children.item(int(len-1))
			return result
		else:
			return None

	def _get_previousSibling(self): 
		siblings = _get_parentNode()._get_childNodes()
		len = siblings._get_length()
		i = 0
		while i < len:
			if i > 1 and siblings.item(i)==self:	# found ourselves in parent.children
				return sibling.item(i-1) 
			i = i + 1
		return None
	
	def _get_nextSibling(self): 
		siblings = _get_parentNode()._get_childNodes()
		len = siblings._get_length()
		i = 0
		while i < len:
			if i < len-1 and siblings.item(i)==self:	# found ourselves in parent.children
				return sibling.item(i+1) 
			i = i + 1
		return None
	
	def _get_attributes(self):
		nnm = NamedNodeMap()
		for a in self.attrdict.items() :
			if a[1]: # skip empty attributes
				attr = Attr(a[0],str(a[1]))
				nnm.setNamedItem(attr)
		return nnm

	def _get_ownerDocument(self): return None	

	def insertBefore(self, newChild, refChild): return None

	def replaceChild(self, newChild, oldChild): 
		self.insertBefore(newChild, oldChild)	# insert before oldChild
		self.removeChild(oldChild)		# remove oldChild
		return oldChild
				
	def removeChild(self, oldChild): return None

	def appendChild(self, newChild):
		return self.insertBefore(newChild, None)

        def hasChildNodes(self):
		len = self._get_childNodes()._get_length()
                if len:
                        return 1
                else:
                        return 0
        def cloneNode(self): return None
	

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
		result  = self.getAttributeNode(name)._get_value()
		return result 
	def getAttributeNode(self, name):
		return self._get_attributes().getNamedItem(name)
	def setAttribute(self,name,value):
		self.attrdict[name] = value
	def removeAttribute(self, name):
		raise self.ex
	def setAttributeNode(self, attr):
		return self.setAttribute(attr._get_name(), attr._get_value())
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
