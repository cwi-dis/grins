__version__ = "$Id$"

# Hyperlink management module

# An 'Hlinks' instance maintains a list of hyperlinks.
# Normally there is one such instance per context.

# This module doesn't care what an anchor is.  In practice, an anchor
# is a tuple (uid, aid) where uid is a unique node id and aid is an
# anchor id which is unique for that node.  (Uids are strings, while
# aids are numbers.)

# The collection of hyperlinks is stored as a list of 4-tuples
# (anchor1, anchor2, direction, type), where:
# anchor1 and anchor2 are anchors (see above);
# direction  is ->, <- or <->, using the DIR_* constants;
# type is jump, call or fork, using the TYPE_* constants.

# XXX It might be better to store ANCHOR1 and ANCHOR2 in a canonical order,
# this would make the search routines a lot easier (and we're doing more
# searching than changing, probably).  [I doubt it --Guido]

# Tuple indices (to avoid dependencies on the tuple definition in the code)
ANCHOR1 = 0
ANCHOR2 = 1
DIR     = 2
TYPE    = 3

# Link directions
DIR_1TO2 = 0
DIR_2TO1 = 1
DIR_2WAY = 2

# Types
TYPE_JUMP = 0
TYPE_CALL = 1
TYPE_FORK = 2

# The class
class Hlinks:

	# Initialize this instance
	def __init__(self):
		self.links = []

	# Return a string representation of this instance
	def __repr__(self):
		return '<Hlinks instance, links=' + `self.links` + '>'

	# Return the entire list of links (read-only)
	def getall(self):
		return self.links

	# Add a link
	def addlink(self, link):
		self.links.append(link)

	# Delete a link.
	# If the list does not exists, delete the reverse link
	def dellink(self, link):
		try:
			self.links.remove(link)
		except ValueError:
## 			print 'dellink: try reverse link'
			self.links.remove(self.revlink(link))

	# Add a list of links
	def addlinks(self, linklist):
		self.links = self.links + linklist

	# Find the hyperlinks with the specified anchor as source.
	# Returns a list of all such links
	def findsrclinks(self, anchor):
		rv = []
		for l in self.links:
			if l[ANCHOR1]==anchor and \
				  l[DIR] in (DIR_1TO2, DIR_2WAY):
				rv.append(l)
			elif l[ANCHOR2]==anchor and \
				  l[DIR] in (DIR_2TO1, DIR_2WAY):
				rv.append(self.revlink(l))
		return rv

	# Find the hyperlinks with the specified anchor as destination.
	# Returns a list of all such links
	def finddstlinks(self, anchor):
		rv = []
		for l in self.links:
			if l[ANCHOR2]==anchor and \
			   l[DIR] in (DIR_1TO2, DIR_2WAY):
				rv.append(l)
			elif l[ANCHOR1]==anchor and \
			     l[DIR] in (DIR_2TO1, DIR_2WAY):
				rv.append(self.revlink(l))
		return rv

	# Find all links related to one or two anchors.
	def findalllinks(self, a1, a2):
		rv = []
		if a1 == a2: return rv
		for l in self.links:
			if a1==l[ANCHOR1] and (a2 is None or a2==l[ANCHOR2]):
				rv.append(l)
			elif a1==l[ANCHOR2] and (a2 is None or a2==l[ANCHOR1]):
				rv.append(self.revlink(l))
		return rv

	# Find links selected by a predicate
	def selectlinks(self, pred):
		rv = []
		for l in self.links:
			if pred(l):
				rv.append(l)
		return rv

	# Reverse representation of a link
	def revlink(self, link):
		a1, a2, dir, type = link
		if dir == DIR_1TO2:
			dir = DIR_2TO1
		elif dir == DIR_2TO1:
			dir = DIR_1TO2
		return (a2, a1, dir, type)

	def findnondanglinganchordict(self):
		dict = {}
		for a1, a2, dir, type in self.links:
			dict[a1] = 1
			dict[a2] = 1
		return dict
