__version__ = "$Id$"

import time
import math

###################
# dur arithmetic rules

def isdefinite(v):
	return v != 'unresolved' and v!= 'indefinite'

def durmul(v1, v2):
	if v1 == 'unresolved' or v2 == 'unresolved':
		return 'unresolved'
	elif v1==0 or v2==0:
		return 0
	elif v1=='indefinite' or v2=='indefinite':
		return 'indefinite'
	else:
		return v1*v2

def durdiv(v, a):
	if v == 'unresolved':
		return 'unresolved'
	elif v=='indefinite':
		return 'indefinite'
	else:
		return v/a

def duradd(v1, v2):
	if v1 == 'unresolved' or v2 == 'unresolved':
		return 'unresolved'
	elif v1=='indefinite' or v2=='indefinite':
		return 'indefinite'
	else:
		return v1 + v2

def dursub(v1, v2):
	if v1 == 'unresolved' or v2 == 'unresolved':
		return 'unresolved'
	elif v1=='indefinite' or v2=='indefinite':
		return 'indefinite'
	else:
		return v1 - v2

def durmin(v1, v2):
	if v1 == 0 or v2 == 0:
		return 0
	elif v1=='indefinite' and v2>0:
		return v2
	elif v2=='indefinite' and v1>0:
		return v1
	elif v1=='unresolved' and v2>0:
		return v2
	elif v2=='unresolved' and v1>0:
		return v1
	elif v1 == 'unresolved' and v2 == 'indefinite':
		return 'indefinite'
	elif v2 == 'unresolved' and v1 == 'indefinite':
		return 'indefinite'
	return min(v1, v2)

def durmax(v1, v2):
	if isdefinite(v1) and isdefinite(v2):
		return max(v1, v2)
	elif (isdefinite(v1) and v2=='indefinite') or (isdefinite(v1) and v1=='indefinite'):
		return 'indefinite'
	elif v1 == 'unresolved' or v2 == 'unresolved':
		return 'unresolved'

def durlt(v1, v2):
	if v1 == 'indefinite' and v2 == 'indefinite':
		return 'unresolved'
	elif isdefinite(v1) and v2 == 'indefinite':
		return 1
	elif isdefinite(v2) and v1 == 'indefinite':
		return 0
	elif v1 == 'unresolved' or v2 == 'unresolved':
		return 'unresolved'
	return v1<v2

def durle(v1, v2):
	if v1 == 'indefinite' and v2 == 'indefinite':
		return 'unresolved'
	elif isdefinite(v1) and v2 == 'indefinite':
		return 1
	elif isdefinite(v2) and v1 == 'indefinite':
		return 0
	elif v1 == 'unresolved' or v2 == 'unresolved':
		return 'unresolved'
	return v1<=v2

###################
# simple local time state keeper

class Timer:
	def __init__(self):
		self._ticking = 0
		self._localTime = 0
		self._lastTime = None

	def resetTimer(self):
		self._ticking = 0
		self._localTime = 0
		self._lastTime = None

	def isTicking(self):
		return self._ticking

	def startTimer(self, t=None):
		if t is not None:
			self.setTime(t)
		if not self._ticking:
			self._lastTime = time.time()
			self._ticking = 1

	def stopTimer(self, t=None):
		if self._ticking:
			self._updateTime()
			self._ticking = 0
		if t is not None:
			self._localTime = t

	def setTime(self, t):
		self._localTime = t
		if self._ticking:
			self._lastTime = time.time()

	def getTime(self):
		if self._ticking:
			self._updateTime()
			return self._localTime
		else:
			return self._localTime

	def _updateTime(self):
		self._localTime = self._localTime + time.time() - self._lastTime
		self._lastTime = time.time()


###################
# simple delta timer queue

class DeltaQueue:
	def __init__(self, timefunct):
		self._queue = []
		self._indqueue = []
		self._timefunct = timefunct
		self._lasttime = timefunct()

	def schedule(self, when, what):
		tnow = self._timefunct()
		if self._queue:
			t, obj = self._queue[0]
			t = t - (tnow - self._lasttime)
			self._queue[0] = t, obj
		self._lasttime = tnow

		if when == 'indefinite':
			self._indqueue.append(('indefinite', what))
			return

		t = 0
		for i in range(len(self._queue)):
			time0, dummy = self._queue[i]
			if t + time0 > when:
				self._queue[i] = time0 - when + t, dummy
				self._queue.insert(i, (when - t, what))
				return
			t = t + time0
		self._queue.append((when - t, what))

	def getExecList(self):
		tnow = self._timefunct()
		delta = tnow - self._lasttime
		self._lasttime = tnow
		el = []
		while self._queue:
			et, obj = self._queue[0]
			t = et - delta
			if t <= 0.0:
				del self._queue[0]
				el.append(obj)
				delta = delta - et
			else:
				self._queue[0] = t, obj
				break
		return el
	
	def isEmpty(self):
		return len(self._queue)==0 and len(self._indqueue)==0

	def clear(self):
		self._queue = []
		self._indqueue = []

	def getDelay(self):
		if self._queue:
			return self._queue[0][0]
		elif self._indqueue:
			return 'indefinite'
		return None

	def cancel(self, what):
		for i in range(len(self._queue)):
			t, obj = self._queue[i]
			if obj == what:
				del self._queue[i]
				if i < len(self._queue):
					tt, obj = self._queue[i]
					self._queue[i] = tt + t, obj
				return
		for i in range(len(self._indqueue)):
			t, obj = self._queue[i]
			if obj == what:
				del self._queue[i]
				return


###################
# SVG Sync Arcs

class SvgSyncArc:
	def __init__(self, srcnode, srcevent, dstnode, dstevent, attrobj):
		self.srcnode = srcnode
		self.srcevent = srcevent
		self.dstnode = dstnode
		self.dstevent = dstevent
		self.attrobj = attrobj

	def updateSyncVariant(self, tval, params=None):
		self.attrobj.setSyncBaseValue(tval, params)

class SvgActionArc:
	def __init__(self, src, dst, delay, action):
		self.src = src
		self.dst = dst
		self.delay = delay
		if action == 'begin':
			self.execute = self.begin
		elif action == 'freeze':
			self.execute = self.freeze
		elif action == 'remove':
			self.execute = self.remove
		elif action == 'dur':
			self.execute = self.dur
		else:
			assert 0, 'invalid ActionArc action'

	def getDelay(self):
		assert self.dst.getTimeParent() == self.src, 'invalid arc'
		seek = self.src.getTime()
		if durle(seek, self.delay):
			delay = dursub(self.delay, seek)
		else:
			delay = 0
		return delay

	def begin(self):
		assert self.dst.getTimeParent() == self.src, 'invalid begin arc'
		seek = self.src.getTime()
		if durle(seek, self.delay):
			advance = dursub(self.delay, seek)
		else:
			advance = dursub(seek, self.delay)
		self.dst.seekElement(advance)
		self.dst.beginElement()

	def freeze(self):
		self.dst.stopTimer(self.dst.getActiveDur())
		self.dst.endElement()

	def remove(self):
		self.dst.endElement()
		self.dst.removeElement()

	def dur(self):
		self.dst.endElement()
		self.dst.removeElement()

	def reread(self):
		self.delay = self.dst.get('begin') or 0

###################
# mixin for svg time hierarchy

class TimeNode:
	def __init__(self, ttype, timeroot):
		self.ttype = ttype # tag for elements and meta-tag for the rest
		self.timeroot = timeroot or self
		self.tparent = None
		self.tfirstchild = None
		self.tnextsibling = None

	def getTimeType(self):
		return self.ttype

	def getTimeRoot(self):
		return self.timeroot

	def getTimeParent(self):
		return self.tparent

	def getFirstTimeChild(self):
		return self.tfirstchild

	def getNextTimeSibling(self):
		return self.tnextsibling

	def getTimeChildren(self):
		L = []
		node = self.tfirstchild
		while node:
			L.append(node)
			node = node.tnextsibling
		return L

	def getFirstTimeChildByType(self, ttype):
		node = self.tfirstchild
		while node:
			if node.ttype == ttype:
				return node
			node = node.tnextsibling
		return None
	
	def getLastTimeChild(self):
		tlastchild = None
		tchild = self.tfirstchild
		while tchild is not None:
			tlastchild = tchild
			tchild = tchild.tnextsibling
		return tlastchild

	def appendTimeChild(self, node):
		tlastchild = self.getLastTimeChild()
		if tlastchild is None:
			self.tfirstchild = node
		else:
			tlastchild.tnextsibling = node
		node.tparent = self

###################
# mixin for svg time elements

class TimeElement(TimeNode, Timer):
	def __init__(self, ttype, timeroot):
		TimeNode.__init__(self, ttype, timeroot)
		Timer.__init__(self)		
		self._dur = 'indefinite'
		self._ad = 'indefinite'
		self._active = 0
		self._alive = 0
		self._repeatindex = 0
		self._syncnotify = 1

		self.beginSyncArcs = []
		self.endSyncArcs = []
		self.repeatSyncArcs = []
		self.eventSyncArcs = []

	def addSyncArc(self, arc):
		if arc.srcevent == 'begin':
			self.beginSyncArcs.append(arc)
		elif arc.srcevent == 'end':
			self.endSyncArcs.append(arc)
		elif arc.srcevent == 'repeat':
			self.repeatSyncArcs.append(arc)
		elif arc.srcevent == 'event':
			self.eventSyncArcs.append(arc)

	def calcBasicTiming(self):
		self._dur = self.calcDur()
		self._ad = self.calcActiveDur()
		
	#
	#  DOM interface implementation
	#  life-cycle: (reset, seek? , begin, (pause, resume)*, seek*, end,	remove)
	#
	def beginElement(self):
		if self.isActive():
			return 0
		self._active = 1
		self._alive = 1
		shed = self.getScheduler()
		if shed: shed.onBegin(self)
		self.startTimer()
		return 1

	def endElement(self):
		if not self.isActive():
			return 0
		self._active = 0
		shed = self.getScheduler()
		if shed: shed.onEnd(self)
		self.stopTimer()
		return 1

	def pauseElement(self):
		if self.isTicking():
			self.stopTimer()

	def resumeElement(self):
		if not self.isTicking() and self.isActive():
			self.startTimer()

	def seekElement(self, seekTo):
		self.setTime(seekTo)

	def repeatElement(self, iter):
		self._repeatindex = iter
		shed = self.getScheduler()
		if shed: shed.onRepeat(self, iter)

	def removeElement(self):
		assert not self._active, 'call endElement before removeElement'
		if not self.isAlive():
			return
		self._alive = 0

	def resetElement(self):
		self.resetTimer()
		self._dur = 'indefinite'
		self._ad = 'indefinite'
		self._active = 0
		self._alive = 0
		self._repeatindex = 0
		self._syncnotify = 1
		
	def enableSyncNotify(self, f):
		self._syncnotify = f

	#
	# basic queries
	#
	def isActive(self):
		return self._active

	def isAlive(self):
		return self._alive

	def isFrozen(self):
		return self._alive and not self._active

	def getDur(self):
		return self._dur

	def getActiveDur(self):
		return self._ad

	def getScheduler(self):
		if self.timeroot != self and self._syncnotify:
			return self.getTimeParent()
		return None

	def clipToAD(self, t):
		if not durlt(t, self._ad):
			return dursub(self._ad, 0.001)	 
		return t

	def clipToDur(self, t):
		if not durlt(t, self._dur):
			return dursub(self._dur, 0.001)	 
		if not durlt(t, 0):
			return 0	 
		return t

	def getDurInstanceTime(self):
		assert self._dur!=0, 'invalid time element call'
		repdur = self.clipToAD(self.getTime())
		if self._dur == 'indefinite':
			return 0, repdur
		repcount = repdur/float(self._dur)
		iter = math.floor(repcount)
		durinst = repdur - iter*self._dur
		if iter>0 and durinst==0.0 and self.isFrozen():
			return iter-1, self._dur
		if iter != self._repeatindex:
			self._repeatindex = iter
			self.repeatElement(iter)
		return iter, durinst
	
	# always resolved
	def calcDur(self):
		dur = self.get('dur')
		repeatDur = self.get('repeatDur')
		repeatCount = self.get('repeatCount')
		end = self.get('end')
		if dur is None:
			if end is not None:
				return 'indefinite'
			else:
				return self.calcImplicitDur()
		return dur

	# calculate AD using dur, repeatDur, repeatCount
	# dur is always resolved and thus AD is also always resolved
	# XXX: definition of durxxx has changed thus this needs fix
	def calcActiveDur(self):
		dur = self._dur
		repeatDur = self.get('repeatDur')
		repeatCount = self.get('repeatCount')
		if dur == 'indefinite':
			repeatCount = None
		elif dur == 0:
			repeatDur = repeatCount = None
		ad = dur
		if repeatDur is not None and repeatCount is not None:
			ad = durmin(durmul(repeatCount, dur), repeatDur)
		elif repeatDur is not None:
			ad = repeatDur
		elif repeatCount is not None:
			ad = durmul(repeatCount, dur)
		ad = self.applyMinMax(ad)
		ad = self.applyTimeManipulations(ad)
		return ad

	def applyTimeManipulations(self, ad):
		speed = self.get('speed')
		if speed:
			ad = durdiv(ad, speed)	
		if self.get('autoReverse')=='true':
			ad = durmul(ad, 2.0)
		return ad

	def applyMinMax(self, ad):
		mintime = self.get('min')
		if mintime is not None and mintime>0:
			ad = durmax(ad, mintime)
		maxtime =self.get('max')
		if maxtime is not None and maxtime>0:
			ad = durmin(ad, maxtime)
		return ad

	def calcImplicitDur(self):
		return 0

####################
# SVG time container

class SvgTimeContainer(TimeElement):
	def __init__(self, ttype, timeroot):
		TimeElement.__init__(self, ttype, timeroot)
		self._ostimer = None
		self._timerid = None

	def setOsTimer(self, ostimer):
		self._ostimer = ostimer
		
	#
	#  DOM interface implementation
	#  life-cycle: reset, seek? , begin, (pause, resume)*, seek*, end,	remove
	#
	def beginElement(self):
		if self.isActive():
			return 0
		TimeElement.beginElement(self)
		for el in self.getTimeChildren():
			el.resetElement()
			el.calcBasicTiming()
		self.prepareScheduler()
		self.schedule()
		return 1

	def endElement(self):
		if not self.isActive():
			return 0
		for el in self.getTimeChildren():
			if el.isActive():
				el.endElement()
		TimeElement.endElement(self)
		self.cancelSchedule()
		return 1

	def pauseElement(self):
		for el in self.getTimeChildren():
			el.pauseElement()
		TimeElement.pauseElement(self)
		self.cancelSchedule()

	def resumeElement(self):
		TimeElement.resumeElement(self)
		for el in self.getTimeChildren():
			el.resumeElement()
		self.schedule()

	def seekElement(self, seekTo):
		TimeElement.seekElement(self, seekTo)
		# seek children
		# ...
		if self.isActive():
			self.reschedule()

	def removeElement(self):
		assert not self.isActive(), 'end should be called before remove'
		if not self.isAlive():
			return
		for el in self.getTimeChildren():
			el.removeElement()
		TimeElement.removeElement(self)
		self.cleanupScheduler()

	def resetElement(self):
		TimeElement.resetElement(self)

	#
	#  event interface
	#
	def onBegin(self, node):
		pass

	def onEnd(self, node):
		pass

	def onRepeat(self, node, index):
		pass
	
	def onEvent(self, node, params):
		pass

	#
	#  schedule interface
	#
	def reschedule(self):
		self.cancelSchedule()
		self.schedule()
			
	def cancelSchedule(self):
		if self._timerid is not None:
			timer = self.timeroot._ostimer
			timer.canceltimer(self._timerid)
			self._timerid = None

	def sleep(self, delay):
		if delay is None:
			self._timerid = None
			self.stopTimer()
		elif delay == 'indefinite':
			self._timerid = None
		else:
			timer = self.timeroot._ostimer
			self._timerid = timer.settimer(delay, (self.schedule, ()))

	def prepareScheduler(self):
		pass

	def cleanupScheduler(self):
		pass

	def schedule(self):
		pass


####################
# SVG par container

class SvgPar(SvgTimeContainer):
	def __init__(self, ttype, timeroot):
		SvgTimeContainer.__init__(self, ttype, timeroot)

	#
	#  schedule interface
	#
	def prepareScheduler(self):
		self._queue = DeltaQueue(self.getTime)
		arcs = self.buildActionArcs()
		for arc in arcs:
			delay = arc.getDelay()
			if delay != 'unresolved':
				self._queue.schedule(delay, arc)

	def cleanupScheduler(self):
		del self._queue

	def schedule(self):
		execList = self._queue.getExecList()
		for cmd in execList:
			cmd.execute()
		delay = self._queue.getDelay()
		self.sleep(delay)

	def buildActionArcs(self):
		arcs = []
		for el in self.getTimeChildren():
			bt = el.get('begin') or 0 # media container
			arc = SvgActionArc(self, el, bt, 'begin')
			arcs.append(arc)

			delay =  duradd(bt, el.getActiveDur())
			fill = el.get('fill')
			if fill == 'freeze':
				arc = SvgActionArc(self, el, delay, 'freeze')
			else:
				arc = SvgActionArc(self, el, delay, 'remove')
			arcs.append(arc)
		return arcs

	def calcImplicitDur(self):
		dur = 0
		for el in self.getTimeChildren():
			tb = el.get('begin') or 0
			t = duradd(tb, el._ad)
			dur = durmax(dur, t)
		return dur

	#
	#	event interface (not implemented yet)
	#   use a rule based decision system for the effect of each event 
	#   (the effect may be none, a sync variant update and possibly a schedule)
	#
	def onBegin(self, node):
		for arc in node.beginSyncArcs:
			arc.updateSyncVariant(self.getTime())

	def onEnd(self, node):
		for arc in node.endSyncArcs:
			arc.updateSyncVariant(self.getTime())

	def onRepeat(self, node, index):
		for arc in node.repeatSyncArcs:
			arc.updateSyncVariant(self.getTime(), index)
	
	def onEvent(self, node, params):
		for arc in node.eventSyncArcs:
			arc.updateSyncVariant(self.getTime(), params)

