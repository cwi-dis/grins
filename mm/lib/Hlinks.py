#
# Hyperlink management module
#

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

	def getall(self):
		return self.links

	def addlink(self, link):
		self.links.append(link)

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
