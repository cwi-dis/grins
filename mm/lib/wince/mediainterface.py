__version__ = "$Id$"

class Image:
	def __init__(self):
		pass

	def get_size(self):
		return 100, 100

	def getbpp(self):
		return 24

def get_image(filename):
	return Image()
