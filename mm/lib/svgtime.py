__version__ = "$Id$"

import time
import math

###################
# dur arithmetic rules

# a time value can be 'unspecified', 'unresolved', 'indefinite', 'definite'

# time constants
unspecified = None
unresolved = 'unresolved'
indefinite = 'indefinite'
mediadur = 'media'

infinity = 'infinity'
minusinfinity = '-infinity'
epsilon = 0.0001

def isdefinite(v):
	return v is not unresolved and v is not indefinite

def isunresolved(v):
	return v == unresolved

def isindefinite(v):
	return v == indefinite

def timemul(v1, v2):
	assert v1 is not None and v2 is not None, 'unspecified values'
	if v1 is unresolved or v2 is unresolved:
		return unresolved
	elif v1==0 or v2==0:
		return 0
	elif v1 is indefinite or v2 is indefinite:
		return indefinite
	else:
		return v1*v2

def timediv(v, a):
	assert v is not None, 'unspecified value'
	if v is unresolved:
		return unresolved
	elif v is indefinite:
		return indefinite
	else:
		return v/a

def timeadd(v1, v2):
	assert v1 is not None and v2 is not None, 'unspecified values'
	if v1 is unresolved or v2 is unresolved:
		return unresolved
	elif v1 is indefinite or v2 is indefinite:
		return indefinite
	else:
		return v1 + v2

def timesub(v1, v2):
	assert v1 is not None and v2 is not None, 'unspecified values'
	if v1 is unresolved or v2 is unresolved:
		return unresolved
	elif v1 is indefinite or v2 is indefinite:
		return indefinite
	else:
		return v1 - v2

def timemin(v1, v2):
	assert v1 is not None and v2 is not None, 'unspecified values'
	if v1 == 0 or v2 == 0:
		return 0
	elif v1 is indefinite and v2>0:
		return v2
	elif v2 is indefinite and v1>0:
		return v1
	elif v1 is unresolved and v2>0:
		return v2
	elif v2 is unresolved and v1>0:
		return v1
	elif v1 is unresolved and v2 is indefinite:
		return indefinite
	elif v2 is unresolved and v1 is indefinite:
		return indefinite
	return min(v1, v2)

def timemax(v1, v2):
	assert v1 is not None and v2 is not None, 'unspecified values'
	if isdefinite(v1) and isdefinite(v2):
		return max(v1, v2)
	elif (isdefinite(v1) and v2 is indefinite) or (isdefinite(v1) and v1 is indefinite):
		return indefinite
	elif v1 is unresolved or v2 is unresolved:
		return unresolved

def timeLT(v1, v2):
	assert v1 is not None and v2 is not None, 'unspecified values'
	if v1 is indefinite and v2 is indefinite:
		return 0
	elif isdefinite(v1) and v2 is indefinite:
		return 1
	elif isdefinite(v2) and v1 is indefinite:
		return 0
	elif v1 is unresolved or v2 is unresolved:
		return 0
	return v1<v2

def timeLE(v1, v2):
	assert v1 is not None and v2 is not None, 'unspecified values'
	if v1 is indefinite and v2 is indefinite:
		return 0
	elif isdefinite(v1) and v2 is indefinite:
		return 1
	elif isdefinite(v2) and v1 is indefinite:
		return 0
	elif v1 is unresolved or v2 is unresolved:
		return 0
	return v1 <= v2

def timeGT(v1, v2):
	return not timeLE(v1, v2)

def timeGE(v1, v2):
	return not timeLT(v1, v2)

def timeEQ(v1, v2):
	return v1 == v2

###################
# simple local time state keeper

class Timer:
	def __init__(self):
		self._ticking = 0
		self._localTime = 0.0
		self._lastTime = None

	def resetTimer(self):
		self._ticking = 0
		self._localTime = 0.0
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
		self._localTime = float(t)
		if self._ticking:
			self._lastTime = time.time()

	def incTime(self, dt):
		self._localTime = self._localTime + float(dt)
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

		if when == indefinite:
			self._indqueue.append((indefinite, what))
			return

		t = 0.0
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
			return indefinite
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

	def getTimeParentOrRoot(self):
		if self.tparent is not None:
			return self.tparent
		return self.timeroot

	def getFirstTimeChild(self):
		return self.tfirstchild

	def getNextTimeSibling(self):
		return self.tnextsibling

	def getPrevTimeSibling(self):
		if self.tparent is None:
			return None
		prev = None
		next = self.tparent.tfirstchild
		while next:
			if next == self:
				return prev
			prev = next
			next = next.tnextsibling
		assert 0, 'logic error in TimeNode.getPrevTimeSibling'

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

	def getTimePath(self):
		tpath = [self,]
		tparent = self.tparent
		while tparent is not None:
			tpath.insert(0, parent)
			tparent = tparent.tparent
		return tpath
		
	def getCommonAncestor(self, n1, n2):
		p1 = n1.getTimePath()
		p2 = n2.getTimePath()
		n = min(len(p1), len(p2))
		prev = p1[0]
		for i in range(1,n):
			if p1[i]!=p2[i]:
				return prev
			prev = p1[i]
				
###################
# mixin for svg time elements
# common behavior (leaf time nodes)?

# states : 'idle', 'waitinterval', 'waitbegin', 'active'
# active conceptual substates: 'playing', 'paused'
# life states: 'waitinterval', 'waitbegin', 'active'
# all life states can be transit (zero dur)

# element's life-cycle:
# waitinterval (waitbegin active waitinterval)*

# Implementation note:
# spec states mapping to ours:
# specStartup : transition from idle to waitbegin on a startup event, compute first interval
# specWaitingToBeginCurrentInterval: waitbegin
# specActiveTime: active 
# specEndOfAnInterval: waitinterval, enter state and compute the next one and notify dependents 
# specPostActive: waitinterval, perform any fill and wait for any next interval 

# state transition external events:
# startup, syncUpdate, parentRepeat, parentEnd, documentEnd

# state transition time completion events:
# begin, dur, end

# state transition attrs beyond state variables
# calcIntervalResult

# implrem: take into account time sampling


timestates = ['idle', 'waitbegin', 'active', 'postactive']
IDLE, WAITINTERVAL, WAITBEGIN, ACTIVE = None, 1, 2, 3

class TimeElement(TimeNode, Timer):
	def __init__(self, ttype, timeroot):
		TimeNode.__init__(self, ttype, timeroot)
		Timer.__init__(self)
		self.beginSyncArcs = []
		self.endSyncArcs = []
		self.repeatSyncArcs = []
		self.eventSyncArcs = []
		self._restart = self.get('restart') or 'always'

		self._state = None
		self._dur = None
		self._isfilled = 0
		self._syncnotify = 1
		self._repeatindex = 0
		self._repeattime = 0
		self._interval = None
		self._ad = None
		self._begincount = 0
		self._ostimer = None
		self._timerid = None
		self._queue = None

	def setOsTimer(self, ostimer):
		self._ostimer = ostimer

	def addSyncArc(self, arc):
		srcevent = arc.getSrcEvent()
		if srcevent == 'begin':
			self.beginSyncArcs.append(arc)
		elif srcevent == 'end':
			self.endSyncArcs.append(arc)
		elif srcevent == 'repeat':
			self.repeatSyncArcs.append(arc)
		elif srcevent == 'event':
			self.eventSyncArcs.append(arc)
	
	#
	#  states and transitions
	#
	# while in idle state make possibly a transition to waiting
	def startupTransition(self, complete=1):
		assert self._state is None, 'invalid transition'
		self._state = WAITINTERVAL
		self._dur = self.calcDur()
		self._interval = self.getNextInterval()
		if complete: self.completeStartupState()
	def completeStartupTransition(self):
		if self._interval is not None:
			self.enterWaitBeginState()

	def enterWaitBeginState(self):
		assert self._state == WAITINTERVAL and self._interval is not None, 'invalid transition'
		self._state = WAITBEGIN
		bt, et = self._interval
		self._ad = timesub(et,bt)
		if bt <= 0:
			self.setTime(-bt)
			self.enterActiveState()
		else:
			self.schedule(bt, self.enterActiveState)
			
	def enterActiveState(self):
		assert self._state == WAITBEGIN and self._interval is not None, 'invalid transition'
		self._state = ACTIVE
		self._isfilled = 1
		self._begincount = self._begincount + 1
		bt, et = self._interval

		# schedule a repeat check
		# update repeatindex and repeat time
		now = self.getParentTime()
		if isdefinite(self._dur):
			self._repeatindex = 0
			self._repeattime = 0.0
			t = bt + self._dur
			while t<now:
				t = t + self._dur
				self._repeatindex = self._repeatindex + 1
				self._repeattime = self._repeattime + self._dur
			if timeLE(t,et):
				self.schedule(t-now, self.onCheckRepeat)

		# schedule end
		self.schedule(self._ad, self.endOfIntervalTransition)
		
		# start local timer
		self.startTimer()

		# update begin dependants
		for arc in self.beginSyncArcs:
			arc.addInstanceTime(bt)
		parent = self.getTimeParent()
		if parent: parent.onChildBegin(self)

	def onCheckRepeat(self):
		if self._state != ACTIVE:
			return
		t = self.getTime()
		if timeGE(t, self._ad):
			return
		insttime = t - 	self._repeattime
		if insttime >= self._dur:
			self.doRepeat()
			t = self._dur -(insttime - self._dur)
			self.schedule(t, self.onCheckRepeat)
		else:
			self.schedule(self._dur - insttime, self.onCheckRepeat)

	def doRepeat(self):
		self._repeatindex = self._repeatindex + 1
		self._repeattime = self._repeattime + self._dur
		for arc in self.repeatSyncArcs:
			arc.addInstanceTime(self.getParentTime(), self._repeatindex)
		parent = self.getTimeParent()
		if parent: parent.onChildRepeat(self, self._repeatindex)

		# self-similar mechanism
		for el in self.getTimeChildren():
			el.resetElement()
			el.startupTransition()

	# while executing this the element is postactive 
	# can transition to waiting or remain in postactive
	def endOfIntervalTransition(self):
		assert self._state == ACTIVE, 'invalid transition'
		self._state = WAITINTERVAL
		self.stopTimer()
		self.resetSchedule()

		fill = self.get('fill')
		if fill != 'freeze':
			self.removeElement()

		bt, et = self._interval
		for arc in self.endSyncArcs:
			arc.addInstanceTime(self.getParentTime())
		parent = self.getTimeParent()
		if parent: parent.onChildEnd(self)

		# search for next interval
		nextinterval = self.getNextInterval(et)
		if nextinterval is not None:
			self._interval = nextinterval
			self.enterWaitBeginState()
		else:
			self.enterPostActiveState()

	# on parent repeat
	def forceEndOfIntervalTransition(self):
		assert self._state == ACTIVE, 'invalid transition'
		self._state = None
		self.stopTimer()
		self.resetSchedule()
		self.removeElement()
		for arc in self.endSyncArcs:
			arc.addInstanceTime(self.getParentTime())

	# optimization: enter postactive state when nothing will happen
	def freezeTransition(self):
		for el in self.getTimeChildren():
			el.freezeTransition()
		self.stopTimer()
		self.resetSchedule()
		if self.isWaiting() or self.isActive():
			self.enterPostActiveState()

	def enterPostActiveState(self):
		self._state = WAITINTERVAL
									
	# same as resetElement
	def enterNoneState(self):
		self.resetElement()

	#
	#  DOM interface implementation
	#
	def beginElement(self):
		if self.isActive():
			return 0
		self.startTimer()
		return 1

	def endElement(self):
		self.stopTimer()
		self.resetSchedule()
		for el in self.getTimeChildren():
			el.endElement()
		return 1

	def pauseElement(self):
		for el in self.getTimeChildren():
			el.pauseElement()
		if self.isTicking():
			self.stopTimer()
			self.pauseSchedule()

	def resumeElement(self):
		if not self.isTicking() and self.isActive():
			self.startTimer()
			self.resumeSchedule()
		for el in self.getTimeChildren():
			el.resumeElement()

	def seekElement(self, seekTo):
		self.setTime(seekTo)
		# seek children
		# ...

	def removeElement(self):
		if not self.isFilled():
			return
		for el in self.getTimeChildren():
			el.resetElement()
		self._isfilled = 0

	def resetElement(self):
		for el in self.getTimeChildren():
			el.resetElement()
		if self.isActive():
			self.forceEndOfIntervalTransition()
		if self.isFilled():
			self.removeElement()
		self.resetTimer()
		self.resetSchedule()
		self._state = None
		self._dur = None
		self._isfilled = 0
		self._syncnotify = 1
		self._repeatindex = 0
		self._repeattime = 0
		self._interval = None
		self._ad = None
		self._begincount = 0
		self._timerid = None
		beginList = self.getXMLAttr('begin')
		beginList.reset()
		endList = self.getXMLAttr('end')
		endList.reset()
		
	def enableSyncNotify(self, f):
		self._syncnotify = f			

	#
	# basic queries
	#
	def getState(self):
		return self._state

	def isActive(self):
		return self._state == ACTIVE

	def isPostActive(self):
		return self._state == WAITINTERVAL

	def isWaiting(self):
		return self._state == WAITBEGIN

	def isFilled(self):
		return self._isfilled

	def isFrozen(self):
		return self._begincount > 0 and self._state in (WAITBEGIN, WAITINTERVAL) and self._isfilled

	def getDur(self):
		return self._dur

	def getBeginCount(self):
		return self._begincount

	def getInterval(self):
		return self._interval

	def getSimpleTime(self):
		t = self.getTime()
		if self._dur is indefinite or self == self.getTimeRoot():
			return t
		tb, te = self._interval
		ad = timesub(te,tb)
		if timeLT(ad, t):
			if self._state == ACTIVE:
				self.endOfIntervalTransition()
			self.setTime(ad)
			return self.getSimpleTime()
		insttime = t - self._repeattime
		if insttime > self._dur:
			self.onCheckRepeat()
			return self.getSimpleTime()
		if self.isFrozen() and insttime == 0.0:
			return self._dur
		if insttime == self._dur:
			return self._dur - epsilon
		return insttime

	def getParentTime(self):
		parent = self.getTimeParent() or self.getTimeRoot()
		return parent.getSimpleTime()
	#
	#  calc simple duration
	#
	def calcDur(self):
		endList = self.getXMLAttr('end')
		dur = self.get('dur')
		repeatDur = self.get('repeatDur')
		repeatCount = self.get('repeatCount')
		if dur is None and repeatDur is None and repeatCount is None and endList.isExplicit():
			calcdur = indefinite
		elif dur is not None:
			if dur is not indefinite:
				calcdur = float(dur)
			else:
				calcdur = indefinite
		elif dur is None:
			calcdur = self.calcImplicitDur()
		elif dur is mediadur:
			calcdur = self.calcImplicitDur()
		return self.applyTimeManipulations(calcdur)

	def calcImplicitDur(self):
		return 0.0

	#
	#  calc active duration
	#
	def calcActiveDur(self, begin, end):
		dur = self._dur
		repeatDur = self.get('repeatDur')
		repeatCount = self.get('repeatCount')

		ad = None
		if dur is indefinite and repeatDur is None and repeatCount is None and end is not None:
			if isdefinite(end):
				ad = timesub(end, begin)
			else:
				ad = end
		elif end is None or end is indefinite:
			ad = self.calcIntermActiveDur(dur, repeatCount, repeatDur)
		else:
			assert end is not indefinite, 'end is not indefinite'
			assert dur is not None or repeatDur is not None or repeatCount is not None, 'none of dur, repeatDur, repeatCount specified'
			ad = timemin(self.calcIntermActiveDur(dur, repeatCount, repeatDur), timesub(end, begin))
		assert ad is not None, 'active dur algorithm error'
		
		ad = self.applyMinMax(ad)
		ad = self.applyTimeManipulations(ad)
		return ad 

	def calcActiveEnd(self, begin, end):
		ad = self.calcActiveDur(begin, end)
		return timeadd(begin, ad)

	def calcIntermActiveDur(self, dur, repeatCount, repeatDur):
		if dur == 0.0:
			iad = 0.0
		elif repeatCount is None and repeatDur is None:
			iad = dur
		elif repeatDur is not None and repeatCount is None:
			iad = repeatDur
		elif repeatCount is not None:
			if repeatCount is indefinite:
				ed = indefinite
			else:
				if self.isActive() and isdefinite(dur):
					# make a prediction
					insttime = self.getTime() - self._repeattime
					remaining = repeatCount - (self._repeatindex + insttime/dur)
					ed = self.getTime() + remaining * dur
				else:
					ed = timemul(repeatCount, dur)
			iad = ed
			if repeatDur is not None:
				iad = timemin(repeatDur, ied)
		return iad

	def applyMinMax(self, ad):
		mintime = self.get('min')
		if mintime is not None and mintime>0:
			ad = timemax(ad, mintime)
		maxtime =self.get('max')
		if maxtime is not None and maxtime>0:
			ad = timemin(ad, maxtime)
		return ad

	def applyTimeManipulations(self, ad):
		speed = self.get('speed')
		if speed:
			ad = timediv(ad, speed)	
		if self.get('autoReverse'):
			ad = timemul(ad, 2.0)
		return ad

	def calcBegin(self):
		if self.isActive():
			parent = self.getTimeParent()
			if not parent:
				return 0
			return parent.getTime() - self.getTime()
		else:
			bt = self.get('begin')
			if bt is not None:
				return bt
			else:
				parent = self.getTimeParent()
				if not parent:
					return 0
				if isinstance(parent, SvgPar):
					return 0
				else:
					# child of seq or excl
					return unresolved
	
	def getNextInterval(self, beginAfter = minusinfinity):
		beginList = self.getXMLAttr('begin')
		endList = self.getXMLAttr('end')
		beginList.beginIteration()
		endList.beginIteration()
		while 1:
			tempBegin = beginList.getNextGE(beginAfter)
			if tempBegin is None:
				return None
			if not endList.isExplicit():
				tempEnd = self.calcActiveEnd(tempBegin, None)
			else:
				tempEnd = endList.getNextGE(tempBegin)
				if tempEnd == tempBegin:
					tempEnd = endList.getNextGT(tempEnd)
				if tempEnd is None:
					if endList.hasPendingEvents():
						tempEnd = unresolved
					else:
						return None
				tempEnd = self.calcActiveEnd(tempBegin, tempEnd)
			if tempEnd > 0:
				return tempBegin, tempEnd
			elif self._restart == 'never':
				return None
			else:
				beginAfter = tempEnd

	# resolve a begin or end time on an element but not both 
	def getEventSensitivity(self):
		if not self.getTimeParentOrRoot().isActive():
			return None
		if not self.isActive():
			return 'begin'
		else:
			if self._restart == 'always':
				return 'begin'
			elif self._restart in ('never', 'whenNotActive'):
				return 'end'

	#
	#  delta schedule interface
	#	
	def schedule(self, delay, cb):
		if self._queue is None:
			self._queue = DeltaQueue(self.getTimeParentOrRoot().getTime)		
		self._queue.schedule(delay, cb)
		if self._timerid is None:
			self._execSchedule()

	def pauseSchedule(self):
		if self._timerid is not None:
			timer = self.timeroot._ostimer
			timer.canceltimer(self._timerid)
			self._timerid = None

	def resumeSchedule(self):
		self._execSchedule()

	def resetSchedule(self):
		self.pauseSchedule()
		if self._queue:
			self._queue.clear()		

	def _sleep(self, delay):
		if delay is None:
			self._timerid = None
		elif delay == indefinite:
			self._timerid = None
		else:
			timer = self.timeroot._ostimer
			self._timerid = timer.settimer(delay, (self._execSchedule, ()))

	def _execSchedule(self):
		self._timerid = None
		execList = self._queue.getExecList()
		for cmd in execList:
			cmd()
		delay = self._queue.getDelay()
		self._sleep(delay)


	#
	# time conversion
	#
	def simple2ancestor(self, t, ancestor):
		if not isdefinite(t) or ancestor == self:
			return t			
		c = self
		cs = t
		while c.tparent and c != ancestor:
			if c._interval is None:
				return unresolved
			ca = cs + c._repeattime
			ps = ca + c._interval[0]
			c = c.tparent
			cs = ps
		return cs

	def ancestor2simple(self, t, ancestor):
		if not isdefinite(t) or ancestor == self:
			return t	
		path = self.getTimePath()
		i = 0
		for c in path:
			i = i + 1
			if c == ancestor:
				break
		ps = t
		for c in path[i:]:
			if c._interval is None:
				return unresolved
			ca = ps - c._interval[0]
			cs = ca - c._repeattime
			ps = cs
		return ps

	def simple2document(self, t):
		return self.simple2ancestor(t, self.getTimeRoot())

	def document2simple(self, t):
		return self.ancestor2simple(t, self.getTimeRoot())

	def active2document(self, t):
		return self.simple2document(t - self._repeattime)

	def document2active(self, t):
		return self._repeattime + self.document2simple(t)

####################
# time container

class TimeContainer(TimeElement):
	def __init__(self, ttype, timeroot):
		TimeElement.__init__(self, ttype, timeroot)

	#
	#  child notifications
	#
	def onChildBegin(self, node):
		pass

	def onChildEnd(self, node):
		pass

	def onChildRepeat(self, node, index):
		pass
	
	def onChildEvent(self, node, params):
		pass

	def matchesEndSyncRule(self, rule, id=None):
		now = self.getTime()
		if rule == 'first':
			result = 0
		else:
			result = 1
		for c in self.getTimeChildren():
			if rule == 'first':
				if c.getBeginCount()>0 and not c.isActive():
					return 1

			elif rule == 'id':
				if id == c.get('id'):
					return c.getBeginCount()>0 and not c.isActive()

			elif rule == 'last':
				if c.isActive() or c.getNextInterval(now) is not None:
					return 0

			elif rule == 'all':
				if c.isActive() or not c.getBeginCount()>0 or c.getNextInterval(now) is not None:
					return 0
		return result

####################
# par container

class Par(TimeContainer):
	def __init__(self, ttype, timeroot):
		TimeContainer.__init__(self, ttype, timeroot)
		
	def startupTransition(self, complete=1):
		assert self._state is None, 'invalid transition'
		for arc in self.beginSyncArcs:
			arc.addInstanceTime(0.0)
		for el in self.getTimeChildren():
			el.startupTransition(0)
		TimeElement.startupTransition(self, 0)
		if complete: self.completeStartupTransition()
	def completeStartupTransition(self):
		TimeElement.completeStartupTransition(self)
		for el in self.getTimeChildren():
			el.completeStartupTransition()
			
	def calcImplicitDur(self):
		dur = 0
		for el in self.getTimeChildren():
			interval = el.getInterval()
			if interval is not None:
				bt, et = interval
				dur = timemax(dur, et)
		return dur

	def beginElement(self):
		self.resetElement()
		beginList = self.getXMLAttr('begin')
		arc = beginList.addSync(self, 'begin')
		arc.addInstanceTime(0)
		self.startupTransition()
		return 1

	def onChildEnd(self, node):
		matches = self.matchesEndSyncRule('last')
		if self.getTimeRoot() == self and matches:
			self.freezeTransition()
		elif self.get('dur') is None and matches:
			self.endOfIntervalTransition()







