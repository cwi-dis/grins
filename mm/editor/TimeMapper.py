# TimeMapper maps times to pixels and the reverse.

Error = 'TimeMapper.Error'
import features

class TimeMapper:
	def __init__(self):
		self.collecting = 1
		self.dependencies = []
		self.collisions = []
		self.collisiondict = {}
		self.minpos = {}
		
	def adddependency(self, t0, t1, minpixeldistance):
		if not self.collecting:
			raise Error, 'Adding dependency while not collecting data anymore'
		self.dependencies.append((t1, t0, minpixeldistance))
		self.collisiondict[t0] = 0
		self.collisiondict[t1] = 0
		
	def addcollision(self, time, minpixeldistance):
		if not self.collecting:
			raise Error, 'Adding collision while not collecting data anymore'
		self.collisions.append((time, minpixeldistance))
		self.collisiondict[time] = 0
		
	def calculate(self):
		if not self.collecting:
			raise Error, 'Calculate called while not collecting data'
		self.collecting = 0
		self.dependencies.sort()
		self.collisions.sort()
		print 'DEPENDENCIES'
		for item in self.dependencies:
			print '\t%f\t%f\t%d'%item
		print 'COLLISIONS'
		for item in self.collisions:
			print '\t%f\t%d'%item
		for time, pixels in self.collisions:
			oldpixels = self.collisiondict[time]
			if pixels > oldpixels:
				self.collisiondict[time] = pixels
##		# XXX is this correct, or should we have added those to the collisions?
##		for t1, t0, pixels in self.dependencies:
##			if t0 == t1:
##				self.collisiondict[t0] = self.collisiondict[t0] + pixels
		self.times = self.collisiondict.keys()
		self.times.sort()
		minpos = 0
		for t in self.times:
			self.minpos[t] = minpos
			minpos = minpos + self.collisiondict[t] + 1
		for t1, t0, pixels in self.dependencies:
			t0maxpos = self.minpos[t0] + self.collisiondict[t0]
			t1minpos = t0maxpos + pixels
			if t1minpos > self.minpos[t1]:
				self.minpos[t1] = t1minpos
		print 'RANGES'
		for t in self.times:
			print t, self.minpos[t], self.minpos[t] + self.collisiondict[t]
		
	def pixel2time(self):
		if self.collecting:
			raise Error, 'pixel2time called while still collecting data'
		raise Error, 'Pixel2time not implemented yet'
		return 0
		
	def time2pixel(self, time, align='left'):
		if self.collecting:
			raise Error, 'time2pixel called while still collecting data'
		if not self.minpos.has_key(time):
			raise Error, 'Interpolating time not implemented yet'
		pos = self.minpos[time]
		if align == 'right':
			pos = pos + self.collisiondict[time]
		return pos
