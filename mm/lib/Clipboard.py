__version__ = "$Id$"

# Clipboard module.
#
# There is one *global* clipboard object, but it is implemented as a class,
# so you can create multiple instances if you wish.
#
# Unfortunately, there is no link with the X clipboard facility (yet).
#
# The clipboard is typed: you always specify a type string and a data object.
# Standard type strings are:
#
# type		data type
#
# 'text'	string (plain ASCII text)
# 'node'	MM subtree (must not have a parent)
# ''		None (meaning the clipboard is empty)
#
# To implement Cut/Copy/Paste of MM nodes:
#
# 'Cut':	use x.Extract() to remove the node from its tree,
#		then call setclip('node', x)
# 'Copy':	use y = x.DeepCopy() to make a copy of the tree,
#		then call setclip('node', y)
# 'Paste':	insert the actual contents from the clipboard in the tree,
#		then *copy* it back to the clipboard:
#		type, x = getclip(); setclip(type, x.DeepCopy())

class Clipboard:

	def __init__(self):
		self.__type = ''
		self.__data = None
		self.__owned = 0

	def __repr__(self):
		return '<Clipboard instance, type=' + `self.type` + '>'

	def setclip(self, type, data, owned=0):
		if self.__owned:
			self.clearclip()
		self.__type = type
		self.__data = data
		self.__owned = owned

	def getclip(self):
		return self.__type, self.__data
		
	def getclipcopy(self):
		type, data = self.getclip()
		if type == 'node':
			new_data = data.DeepCopy()
		elif type == 'multinode':
			new_data = []
			for d in data:
				new_data.append(d.DeepCopy())
		# We return the old one and put the new one on the clipboard
		self.setclip(type, new_data, owned=1)
		return type, data

	def clearclip(self):
		if self.__owned:
			if hasattr(self.__data, 'Destroy'):
				self.__data.Destroy()
			elif type(self.__data) in (type(()), type([])):
				for i in self.__data:
					if hasattr(i, 'Destroy'):
						i.Destroy()
			self.__owned = 0
		self.__type = ''
		self.__data = None