__version__ = "$Id$"

import Bandwidth

# Indicators for bandwidth type. STREAM is allocated first, then PREROLL.
STREAM=0
PREROLL=1

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
		# Find the slot in which t0 falls
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
		# Create a slot from t0 to t1, or possibly shorter,
		# return the slot index and the new t1
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
		# Return the available bandwidth at t0 and the time
		# t1 at which that value may change
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

	def reserve(self, t0, t1, bits, minbps, maxbps):
		boxes = []
		overflow = 0
		count = 0
		while 1:
			count = count + 1
			if count > 100:
				print 'BandwidthReserve: computation did not converge:', t0, t1, bits
				break
			i, cur_t1 = self._find(t0, t1)
			t0_0, oldusedbps, maxusedbps = self.used[i]
			#
			# Check how much bandwidth we're going to use.
			# We always used minbps (even if it doesn't fit)
			# We never use more than maxbps
			#
			availbps = maxusedbps - oldusedbps
			if availbps < minbps:
				usedbps = minbps
			elif availbps < maxbps:
				usedbps = availbps
			else:
				usedbps = maxbps
			#
			# There's one exception to "never using more than maxbps": if we
			# are close to the deadline we will use anything.
			#
			if t1-t0 < 1.0 or cur_t1 >= t1:
				usedbps = bits/(t1-t0)
			if usedbps <= 0:
				t0 = cur_t1
				continue
			#
			# Next check whether we have room to spare, because we have
			# more aggregate bandwidth than we have bits for. We solve this
			# by lowering cur_t1. The _find call will split the bandwidth slot.
			#
			if bits < (cur_t1-t0)*usedbps:
				cur_t1 = t0 + (bits/usedbps)
				i, cur_t1 = self._find(t0, cur_t1)
				t0_0, oldusedbps, maxusedbps = self.used[i]
			newusedbps = oldusedbps + usedbps
			if newusedbps > maxusedbps:
				tp = 'overflow'
				if newusedbps - maxusedbps > overflow:
					overflow = newusedbps - maxusedbps
			else:
				tp = None
			# Note that the boxes are for drawing only. Hence we clamp them
			# to the [0..maxusedbps] range
			box_lobps = oldusedbps
			box_hibps = newusedbps
			if box_hibps > maxusedbps:
				box_hibps = maxusedbps
				box_lobps = maxusedbps - usedbps
			if box_lobps < 0:
				box_lobps = 0
			boxes.append((t0, cur_t1, box_lobps, box_hibps, tp))
			self.used[i] = (t0, newusedbps, maxusedbps)
			
			bits = bits - (usedbps*(cur_t1-t0)+0.99)
			if bits < 0x7fffffff:
				# Prefer ints
				bits = round(bits)
			assert (bits >= -1)
##			if t1-t0 < 1.0 or cur_t1 >= t1:
##				assert(bits == 0)

##			if newbw > maxbw:
##				# Compute how much too much we've used
##				bottombw = max(oldbw, maxbw)
##				overflow = overflow + (newbw-bottombw)*(cur_t1-t0)
			if newusedbps > self.maxused:
				self.maxused = newusedbps
			t0 = cur_t1
			if bits <= 0:
				break
		return overflow, boxes

	def overflowdelay(self, t0, bits, minbps, maxbps):
		##import pdb ; pdb.set_trace() #DBG
		count = 0
		t1 = t0
		while bits > 0:
			count = count + 1
			if count > 100:
				print 'OverflowDelay: computation did not converge:', bits
				return t1-t0
			# See how many seconds we minimally need
			minmax_t1 = t1 + (bits/maxbps)
			# Grab the next slot
			i, next_t1 = self._find(t1, minmax_t1)
			t0_0, oldusedbps, maxusedbps = self.used[i]
			availbps = maxusedbps - oldusedbps
			# See how much bandwidth we're going to use here
			if availbps < minbps:
				usedbps = minbps
			elif availbps < maxbps:
				usedbps = availbps
			else:
				usedbps = maxbps
			# See if this is sufficient
			bits_thisslot = (next_t1-t1) * usedbps + 0.99
			if bits_thisslot > bits:
				t1 = t1 + (bits / usedbps)
				break
			# Otherwise we try again
			bits = bits - bits_thisslot
			if bits < 0x7fffffff:
				# Prefer ints
				bits = round(bits)
			t1 = next_t1
		delay = t1 - t0
		# Round up to something reasonable
		if delay > 0x7fffffff:
			pass
		elif delay > 10:
			delay = int(delay + 1)
		elif delay > 0.1:
			delay = int(delay*10+1) / 10.0
		else:
			delay = delay * 1.01
		return delay

	def getstallinfo(self):
		totaloverflowseconds = 0
		stalls = []
		t1 = self.used[0][0]
		for t0, usedbps, maxbps in self.used:
			if usedbps > maxbps:
				overflowbps = (usedbps-maxbps)
				overflowbits = overflowbps * (t1-t0)
				overflowseconds = overflowbits / self.initialmax
				totaloverflowseconds = totaloverflowseconds + overflowseconds
				stalls.append((t1, overflowseconds, 'stall'))
			t1 = t0
		return totaloverflowseconds, stalls
		
##	def prearmreserve(self, t0, t1, size):
##		# First pass: see whether we can do it. For each "slot"
##		# we check the available bandwidth and see whether there
##		# is enough before t1 passes
##		size = float(size)
##		sizeremain = size
##		tcur = tnext = t0
##		overall_t0 = overall_t1 = None
##		while sizeremain > 0 and tnext < t1:
##			availbw, tnext = self._findavailbw(tcur)
##			if tnext > t1:
##				tnext = t1
##			size_in_slot = availbw*(tnext-tcur)
##			if size_in_slot > 0:
##				sizeremain = sizeremain - size_in_slot
##			tcur = tnext
##		if sizeremain > 0:
##			# It didn't fit. We reserve continuous bandwidth
##			# so the picture makes sense.
##			if t1 == t0:
##				t1 = t0 + 0.1
##			dummy, boxes = self.reserve(t0, t1, size/(t1-t0), bwtype=2)
##			return sizeremain, t0, t1, boxes
##		# It did fit. Do the reservations.
##		boxes = []
##		while size > 0:
##			if t0 >= t1:
##				raise 'Bandwidth algorithm error'
##			i, tnext = self._find(t0, t1)
##			t0_0, oldbw, maxbw = self.used[i]
##			bwfree = maxbw - oldbw
##			size_in_slot = bwfree*(tnext-t0)
##			if size_in_slot <= 0:
##				t0 = tnext
##				continue
##			if size_in_slot > size:
##				# Yes, everything fits. Compute end time
##				# and possibly create new slot
##				tnext = t0 + size/bwfree
##				i, tnext = self._find(t0, tnext)
##				size_in_slot = size
##			boxes.append((t0, tnext, oldbw, maxbw, 0))
##			if overall_t0 is None:
##				overall_t0 = t0
##			overall_t1 = tnext
##			self.used[i] = t0, maxbw, maxbw
##			if maxbw > self.maxused:
##				self.maxused = maxbw
##			size = int(size - size_in_slot)
##			t0 = tnext
##		return 0, overall_t0, overall_t1, boxes

def compute_bandwidth(root, seticons=1, storetiming=None):
	# Compute bandwidth usage of a tree. Sets error icons, and returns
	# a tuple (bandwidth, prerolltime, delaycount, errorseconds, errorcount)
	assert(not storetiming) # Not implemented in this version yet
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
	# Skip the streaming data (which is now at the front)
	while i < len(allbandwidthdata) and allbandwidthdata[i][0] == STREAM:
		i = i + 1
	# Compute prearms for t0=0
	while i<len(allbandwidthdata):
##		t0, t1, node, prearm, bandwidth = allbandwidthdata[i]
		tp, t0, t1, node, bits, minbps, maxbps = allbandwidthdata[i]
		if t0 > 0 or t1 > 0:
			break
		if bits:
			prerolldur = bits/float(maxbandwidth)
			prerollbox = (-prerolltime-prerolldur, -prerolltime, 0, 
				maxbandwidth, 'preroll')
			node.add_bandwidthboxes([prerollbox])
			prerolltime = prerolltime + prerolldur
			allbandwidthdata[i] = tp, t0, t1, node, 0, minbps, maxbps
		i = i + 1
	#
	# Compute continuous media bandwidth
	#
	accum = BandwidthAccumulator(maxbandwidth)
##	for t0, t1, node, prearm, bandwidth in allbandwidthdata:
	for tp, t0, t1, node, bits, minbps, maxbps in allbandwidthdata:
		if bits:
			overflow, boxes = accum.reserve(t0, t1, bits, minbps, maxbps)
			node.add_bandwidthboxes(boxes)
			if overflow and seticons:
				if tp == STREAM:
					if overflow > 1000000:
						overflow = '%d Mbps'%(overflow/1000000)
					elif overflow > 1000:
						overflow = '%d Kbps'%(overflow/1000)
					else:
						overflow = '%d bps'%overflow
					msg = 'Uses %s more bandwidth than available.'%overflow
					node.set_infoicon('bandwidthbad', msg)
				else:
					from fmtfloat import fmtfloat
					bwdelay = accum.overflowdelay(t1, overflow, minbps, maxbps)
					if bwdelay < 2:
						ss = ""
					else:
						ss = "s"
					msg = 'Needs %s second%s longer to load.\nShall I add an extra begin delay?'%(fmtfloat(bwdelay, prec = 1), ss)
					node.set_infoicon('bandwidthbad', msg, fixcallback=(node.fixdelay_callback, (bwdelay,)))
				errornodes[node] = 1
				delaycount = delaycount + 1

##	#
##	# Finally show "bandwidth fine" icon on all nodes that deserve it
##	#
##	if seticons:
##		for tp, t0, t1, node, bits, minbps, maxbps in allbandwidthdata:
##			if not errornodes.has_key(node):
##				node.set_infoicon('bandwidthgood')
	errorseconds, stalls = accum.getstallinfo()
	return maxbandwidth, prerolltime, delaycount, errorseconds, errorcount, stalls
	
def _getallbandwidthdata(datalist, node):
	# Recursively get all bandwidth usage info. Modifies first argument
	errorcount = 0
	node.set_bandwidthboxes([])
	try:
		_getbandwidthdatainto(datalist, node)
	except Bandwidth.Error, arg:
		node.set_infoicon('error', arg)
		errorcount = 1
	for child in node.children:
		errorcount = errorcount + _getallbandwidthdata(datalist, child)
	return errorcount
	
def _getbandwidthdatainto(datalist, node):
	# Get bandwidth usage info for a single node
	if node.type != 'ext':
		return
	if not node.WillPlay():
		return
	t0, t1, dummy, dummy, dummy = node.GetTimes()
	prerollbits, prerollseconds, prerollbps, streambps = Bandwidth.getstreamdata(node, target=1)
	rv = []
	if prerollbits:
		datalist.append((PREROLL, 0, t0, node, prerollbits, 0, prerollbps))
	if streambps:
		# First we subtract the preroll from the end
		if prerollseconds:
			t1 = t1 - prerollseconds
		# If there's anything left we add it as continuous bandwidth
		if t1 > t0:
			totalbits = streambps*(t1-t0)
			datalist.append((STREAM, t0, t1, node, totalbits, streambps, streambps))
	return rv
