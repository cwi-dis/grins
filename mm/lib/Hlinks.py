#
# Hyperlink management module
#
# XXX It might be better to store ANCHOR1 and ANCHOR2 in a canonical order,
# this would make the search routines a lot easier (and we're doing more
# searching than changing, probably)

# Structure indices
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

class Hlinks:
	def init(self):
		self.links = []
		return self

	def __repr__(self):
		return '<Hlink instance, links=' + `self.links` + '>'

	def getall(self):
		return self.links

	def addlink(self, link):
		self.links.append(link)

	def dellink(self, link):
		try:
			self.links.remove(link)
		except ValueError:
			print 'dellink: try reverse link'
			self.links.remove(self.revlink(link))

	def addlinks(self, linklist):
		self.links = self.links + linklist
	#
	# Find a hyperlink with the specified anchor as source
	# Returns a list of all such links
	def findsrclink(self, anchor):
		rv = []
		for l in self.links:
			if l[ANCHOR1]==anchor and \
				  l[DIR] in (DIR_1TO2, DIR_2WAY):
				rv.append((l[TYPE], l[ANCHOR2]))
			if l[ANCHOR2]==anchor and \
				  l[DIR] in (DIR_2TO1, DIR_2WAY):
				rv.append((l[TYPE], l[ANCHOR1]))
		return rv
	# Find all links related to one or two nodes
	def findalllinks(self, a1, a2):
		rv = []
		if a1 == a2: return rv
		for l in self.links:
			if a1==l[ANCHOR1] and (a2==None or a2==l[ANCHOR2]):
				rv.append(l)
			elif a1==l[ANCHOR2] and (a2==None or a2==l[ANCHOR1]):
				rv.append(self.revlink(l))
		return rv

	# Reverse representation of a link
	def revlink(self, (a1, a2, dir, type)):
		if dir == DIR_1TO2:
			dir = DIR_2TO1
		elif dir == DIR_2TO1:
			dir = DIR_1TO2
		return (a2, a1, dir, type)
