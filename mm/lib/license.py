# License handling code, dummy for now

FEATURES=["save", "editdemo", "player"]

Error="license.error"

class Features:
	def __init__(self, license, args):
		self.license = license
		self.args = args

	def __del__(self):
		apply(self.license._release, self.args)
		del self.license
		del self.args
	
class License:
	def __init__(self):
		"""Obtain a license, and state that we are potentially
		interested (at some point) in the features given"""
		self.__available_features = FEATURES

	def have(self, *features):
		"""Check whether we have the given features"""
		for f in features:
			if not f in self.__available_features:
				return 0
		return 1

	def need(self, *features):
		"""Obtain a locked license for the given features.
		The features are released when the returned object is
		freed"""
		if not apply(self.have, features):
			raise Error, "Required license feature not available"
		return Features(self, features)

	def _release(self, features):
		pass
	
