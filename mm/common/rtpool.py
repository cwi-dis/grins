#
# Module rtpool.
# Keeps a pool of actions and durations and returns the best fitting one.
#
error = 'rtpool.error'

class rtpool:
	def init(self):
		self.pool = []
		return self

	def __repr__(self):
		return '<rtpool instance, pool=' + `self.pool` + '>'

	def flush(self):
		self.pool = []

	def enter(self, ev):
		duration = ev[1]
		for i in range(len(self.pool)):
			if self.pool[i][1] > duration:
				break
		else:
			i = len(self.pool)
		self.pool.insert(i, ev)
		return ev

	def cancel(self, ev):
		self.pool.remove(ev)

	def shortest(self):
		if not self.pool:
			raise error, 'Event pool is empty'
		return self.pool[0][1]

	def empty(self):
		return not self.pool

	#
	# Actually, this is far-from-best fit:-)
	# We return the first event due that fits.
	#
	def bestfit(self, now, duration):
		rv = None
		for i in range(len(self.pool)):
			if self.pool[i][1] < duration:
				if not rv or self.pool[i][0] <= rv[0]:
					rv = self.pool[i]
					rvind = i
		if rv:
			del self.pool[rvind]
			return rv
		return None
		
