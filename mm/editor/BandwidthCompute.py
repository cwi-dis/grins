import Bandwidth

class BandwidthAccumulator:
	# Accumulated used bandwidth. The datastructure used is a
	# list of (starttime, bandwidth) tuples, sorted by _reverse_
	# starttime.
	#

	def __init__(self, maxbw):
		self.initialmax = maxbw
		self.used = [(0, 0, maxbw)]
		self.maxused = 0
		self.overflow = []
		
	def getmaxandused(self):
		return self.initialmax, self.maxused

	def _findslot(self, t0):
		"""Find the slot in which t0 falls"""
##		if t0 < 0:
##			raise 'Illegal t0', t0
		#
		# Search through the slots (ordered backward) until we
		# find the one in which t0 lies.
		#
		for i in range(len(self.used)):
			if self.used[i][0] <= t0:
				break
		else:
			self.used.append((t0, 0, self.initialmax))
			return len(self.used)-1
		return i

	def _find(self, t0, t1):
		"""Create a slot from t0 to t1, or possibly shorter,
		return the slot index and the new t1"""
		i = self._findslot(t0)
		t_i, bandwidth, maxbw = self.used[i]
		# If the slot doesn't start exactly at t0 we split it
		# in two.
		if t_i < t0:
			self.used[i:i] = [(t0, bandwidth, maxbw)]
		# Next, if the end time doesn't fit lower it. The higher
		# layers will handle the trailing end by iterating.
		if i > 0 and t1 > self.used[i-1][0]:
			t1 = self.used[i-1][0]
		# Finally, if the slot continues after t1 we create a new
		# slot.
		if i == 0 or t1 < self.used[i-1][0]:
			self.used[i:i] = [(t1, bandwidth, maxbw)]
			i = i + 1
		# Now slot i points to the (new) t0,t1 range.
		return i, t1

	def _findavailbw(self, t0):
		"""Return the available bandwidth at t0 and the time
		t1 at which that value may change"""
		i = self._findslot(t0)
		dummyt0, oldbw, maxbw = self.used[i]
		bw = maxbw - oldbw
		if bw < 0:
			bw = 0
		if i == 0:
			t1 = None
		else:
			t1 = self.used[i-1][0]
		return bw, t1

	def reserve(self, t0, t1, bandwidth, bwtype=1):
		boxes = []
		overflow = 0
		while 1:
			i, cur_t1 = self._find(t0, t1)
			t0_0, oldbw, maxbw = self.used[i]
			if bwtype <= 1 and bandwidth+oldbw > maxbw:
				curbwtype = bwtype + 2
			else:
				curbwtype = bwtype
			newbw = oldbw + bandwidth
			boxes.append((t0, cur_t1, oldbw, newbw,
				      curbwtype))
			self.used[i] = (t0, newbw, maxbw)
			if newbw > maxbw:
				# Compute how much too much we've used
				bottombw = max(oldbw, maxbw)
				overflow = overflow + (newbw-bottombw)*(cur_t1-t0)
			if newbw > self.maxused:
				self.maxused = newbw
			t0 = cur_t1
			if t0 >= t1:
				break
		return overflow, boxes

	def prearmreserve(self, t0, t1, size):
		# First pass: see whether we can do it. For each "slot"
		# we check the available bandwidth and see whether there
		# is enough before t1 passes
		overflow = 0
		size = float(size)
		sizeremain = size
		tcur = tnext = t0
		overall_t0 = overall_t1 = None
		while sizeremain > 0 and tnext < t1:
			availbw, tnext = self._findavailbw(tcur)
			if tnext > t1:
				tnext = t1
			size_in_slot = availbw*(tnext-tcur)
			if size_in_slot > 0:
				sizeremain = sizeremain - size_in_slot
			tcur = tnext
		if sizeremain > 0:
			# It didn't fit. We reserve continuous bandwidth
			# so the picture makes sense.
			if t1 == t0:
				t1 = t0 + 0.1
			dummy, boxes = self.reserve(t0, t1, size/(t1-t0), bwtype=2)
			return sizeremain, t0, t1, boxes
		# It did fit. Do the reservations.
		boxes = []
		while size > 0:
			if t0 >= t1:
				raise 'Bandwidth algorithm error'
			i, tnext = self._find(t0, t1)
			t0_0, oldbw, maxbw = self.used[i]
			bwfree = maxbw - oldbw
			size_in_slot = bwfree*(tnext-t0)
			if size_in_slot <= 0:
				t0 = tnext
				continue
			if size_in_slot > size:
				# Yes, everything fits. Compute end time
				# and possibly create new slot
				tnext = t0 + size/bwfree
				i, tnext = self._find(t0, tnext)
				size_in_slot = size
			boxes.append((t0, tnext, oldbw, maxbw, 0))
			if overall_t0 is None:
				overall_t0 = t0
			overall_t1 = tnext
			self.used[i] = t0, maxbw, maxbw
			if maxbw > self.maxused:
				self.maxused = maxbw
			size = int(size - size_in_slot)
			t0 = tnext
		return 0, overall_t0, overall_t1, boxes

def compute_bandwidth(root, seticons=1):
	"""Compute bandwidth usage of a tree. Sets error icons, and returns
	a tuple (bandwidth, prerolltime, delaycount, errorseconds, errorcount)"""
	import settings
	maxbandwidth = settings.get('system_bitrate')
	prerolltime = 0
	delaycount = 0
	errorcount = 0
	errorseconds = 0
	errornodes = {}
	#
	# Get list (sorted by begin time) of all bandwidth requirements
	#
	allbandwidthdata = []
	errorcount = _getallbandwidthdata(allbandwidthdata, root)
	allbandwidthdata.sort()
	#
	# Compute preroll time (prearms needed at t0==0)
	#
	i = 0
	while i<len(allbandwidthdata):
		t0, t1, node, prearm, bandwidth = allbandwidthdata[i]
		if t0 > 0:
			break
		if prearm:
			prerolltime = prerolltime + (prearm/float(maxbandwidth))
			allbandwidthdata[i] = t0, t1, node, 0, bandwidth
		i = i + 1
	#
	# Compute continuous media bandwidth
	#
	accum = BandwidthAccumulator(maxbandwidth)
	for t0, t1, node, prearm, bandwidth in allbandwidthdata:
		if bandwidth:
			overflow, dummy = accum.reserve(t0, t1, bandwidth)
			if overflow and seticons:
				msg = 'Uses %d bps more bandwidth than available'%overflow
				node.set_infoicon('bandwidthbad', msg)
				errornodes[node] = 1
				delaycount = delaycount + 1
##				print 'continuous overflow', overflow, node
				errorseconds = errorseconds + (overflow/maxbandwidth)
	#
	# Compute preroll bandwidth and internal RealPix bandwidth usage
	#
	for t0, t1, node, prearm, bandwidth in allbandwidthdata:
		if prearm:
			overflow, dummyt0, dummyt1, dummyboxes = accum.prearmreserve(0, t0, prearm)
			if overflow:
##				print 'preroll overflow', overflow, node
				errorseconds = errorseconds + (overflow/maxbandwidth)
				if seticons and not errornodes.has_key(node):
					msg = 'Needs at least %d more seconds to load'%round(0.5+overflow/maxbandwidth)
					node.set_infoicon('bandwidthbad', msg)
					errornodes[node] = 1
					delaycount = delaycount + 1
		if node.GetType() == 'ext' and \
		   node.GetChannelType() == 'RealPix':
			# Create the SlideShow if it somehow doesn't exist yet
			if not hasattr(node, 'slideshow'):
				import realnode
				node.slideshow = realnode.SlideShow(node)
			slack, errors = node.slideshow.computebandwidth()
			errorseconds = errorseconds + slack
			delaycount = delaycount + errors

	#
	# Finally show "bandwidth fine" icon on all nodes that deserve it
	#
	if seticons:
		for t0, t1, node, prearm, bandwidth in allbandwidthdata:
			if not errornodes.has_key(node):
				node.set_infoicon('bandwidthgood')
	
	return maxbandwidth, prerolltime, delaycount, errorseconds, errorcount
	
def _getallbandwidthdata(datalist, node):
	"""Recursively get all bandwidth usage info. Modifies first argument"""
	errorcount = 0
	try:
		this = _getbandwidthdata(node)
	except Bandwidth.Error, arg:
		node.set_infoicon('error', arg)
		this = None
		errorcount = 1
	if this:
		datalist.append(this)
	for child in node.children:
		errorcount = errorcount + _getallbandwidthdata(datalist, child)
	return errorcount
	
def _getbandwidthdata(node):
	"""Get bandwidth usage info for a single node"""
	if node.type != 'ext':
		return None
	if not node.WillPlay():
		return None
	t0, t1, dummy, dummy, dummy = node.GetTimes()
	prearm, bandwidth = Bandwidth.get(node, target=1)
	return t0, t1, node, prearm, bandwidth
        # t0 - start time.
	# t1 - stop time
	# prearm - number of bits that need to be downloaded before node can start
	# bandwidth - number of bits downloaded during play time (per second)
