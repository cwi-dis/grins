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

class GlobalClipboard:

	def __init__(self):
		self.type = ''
		self.data = None

	def __repr__(self):
		return '<GlobalClipboard instance, type=' + `self.type` + '>'

	def setclip(self, type, data):
		self.type = type
		self.data = data

	def getclip(self):
		return self.type, self.data

theClipboard = GlobalClipboard()

getclip = theClipboard.getclip
setclip = theClipboard.setclip
