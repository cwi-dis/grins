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
# mixin for svg time hierarchy

class TimeNode:
	def __init__(self, ttype, tdocument):
		self.ttype = ttype # tag for elements and meta-tag for the rest
		self.tdocument = tdocument # owner document
		self.tparent = None
		self.tfirstchild = None
		self.tnextsibling = None

	def getTimeType(self):
		return self.ttype

	def getTimeDocument(self):
		return self.tdocument

	def getTimeParent(self):
		return self.tparent

	def getFirstTimeChild(self):
		return self.tfirstchild

	def getNextTimeSibling(self):
		return self.tnextsibling

	def getTimeRoot(self):
		return self.tdocument.getTimeRoot()

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
	def __init__(self, ttype, tdocument):
		TimeNode.__init__(self, ttype, tdocument)
		Timer.__init__(self)		
		self._dur = 'indefinite'
		self._ad = 'indefinite'
		self._active = 0
		self._frozen = 0
		self._repeat = 0
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
		
	def resetInstance(self):
		self.resetTimer()
		self._dur = 'indefinite'
		self._ad = 'indefinite'
		self._active = 0
		self._frozen = 0
		self._repeat = 0
		self._syncnotify = 1

	#
	#  DOM interface implementation
	#
	def beginElement(self):
		if self.isActive():
			return 0
		self._active = 1
		timeroot = self.tdocument.getTimeRoot()
		if timeroot != self and self._syncnotify:
			timeroot.onBeginEvent(self)
		return 1

	def endElement(self):
		if not self.isActive():
			return 0
		timeroot = self.tdocument.getTimeRoot()
		if timeroot != self and self._syncnotify:
			timeroot.onEndEvent(self)
		self.resetInstance()
		return 1

	def pauseElement(self):
		if self.isTicking():
			self.stopTimer()

	def resumeElement(self):
		if not self.isTicking():
			self.startTimer()

	def seekElement(self, seekTo):
		self.setTime(seekTo)

	def repeatElement(self, iter):
		self._repeat = iter
		timeroot = self.tdocument.getTimeRoot()
		if timeroot != self and self._syncnotify:
			timeroot.onRepeatEvent(self, iter)

	def freezeElement(self):
		self._frozen = 1
	
	def enableSyncNotify(self, f):
		self._syncnotify = f
	#
	# basic queries
	#
	def isActive(self):
		return self._active

	def isFrozen(self):
		return self._frozen

	def getDur(self):
		return self._dur

	def getActiveDur(self):
		return self._ad

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
		if iter>0 and durinst==0.0 and self._frozen:
			return iter-1, self._dur
		if iter != self._repeat:
			self._repeat = iter
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
				# implicit dur
				if self.getTimeType() == 'par':
					return self.calcParDur()
				elif self.getTimeType() == 'seq':
					return self.calcSeqDur()
				return 0
		return dur

	# calculate AD using dur, repeatDur, repeatCount
	# dur is always resolved and thus AD is also always resolved
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

	def calcParDur(self):
		dur = 0
		for el in self.getTimeChildren():
			tb = el.get('begin') or 0
			t = duradd(tb, el._ad)
			dur = durmax(dur, t)
		return dur

	def calcSeqDur(self):
		return 0

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

	def updateDependant(self, tval, params=None):
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
		elif action == 'end':
			self.execute = self.end
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
		self.dst.startTimer(advance)
		self.dst.beginElement()

	def freeze(self):
		self.dst.stopTimer(self.dst.getActiveDur())
		self.dst.freezeElement()

	def end(self):
		self.dst.stopTimer()
		self.dst.endElement()

	def dur(self):
		self.dst.stopTimer()
		self.dst.endElement()

	def reread(self):
		self.delay = self.dst.get('begin') or 0

###################
# SVG media time container

class SvgTimeRoot(TimeElement):
	animations = ('SvgAnimate','SvgSet','SvgAnimateMotion','SvgAnimateColor','SvgAnimateTransform',)
	def __init__(self, ttype, tdocument):
		TimeElement.__init__(self, ttype, tdocument)
		self._children = []
		self._arcs = []
		self._queue = None

		self._ostimer = None
		self._timerid = None

		self._pauselist = []
	
	#
	#  directed time graph building
	#
	def onDocLoad(self):
		self.buildTimeGraph()
		self._queue = DeltaQueue(self.getTime)
		self._children = self.getTimeChildren()
		self.buildActionArcs()

	def buildTimeGraph(self):
		doc = self.getTimeDocument()
		iter = doc.createDOMNavigator(self, self, self.buildTimeGraphCallback)
		while iter.advance(): pass
		iter = doc.createDOMNavigator(self, self, self.resolveTimeGraphRefs)
		while iter.advance(): pass

	def buildTimeGraphCallback(self, node):
		node.calcBasicTiming()
		node.createSyncArcs()
		if node.__class__.__name__ in  self.animations:
			node.createAnimator()

	def resolveTimeGraphRefs(self, node):
		bt = node.get('begin') or 0
		if isdefinite(bt):
			for arc in node.beginSyncArcs:
				arc.updateDependant(bt)
		et = node.get('end')
		if isdefinite(et):
			for arc in node.endSyncArcs:
				arc.updateDependant(et)

	def buildActionArcs(self):
		for el in self._children:
			bt = el.get('begin') or 0 # media container
			arc = SvgActionArc(self, el, bt, 'begin')
			self._arcs.append(arc)

			delay =  duradd(bt, el.getActiveDur())
			fill = el.get('fill')
			if fill == 'freeze':
				arc = SvgActionArc(self, el, delay, 'freeze')
			else:
				arc = SvgActionArc(self, el, delay, 'end')
			self._arcs.append(arc)

	#
	#  DOM interface implementation
	#
	def beginElement(self):
		if self.isActive():
			return 0
		assert self._ostimer is not None, 'SVG TimeRoot needs a timer'
		TimeElement.beginElement(self)
		self.calculateTiming()
		self.scheduleActionArcs()
		self.startTimer()
		self.evaluate()
		return 1

	def endElement(self):
		if not self.isActive():
			return 0
		for el in self._children:
			if el.isActive() or el.isFrozen():
				el.enableSyncNotify(0)
				el.endElement()
		TimeElement.endElement(self)
		self.cancelOsTimer()
		self._ostimer = None
		self._queue.clear()
		self._timerid = None
		self._pauselist = []
		return 1

	def pauseElement(self):
		if not self.isTicking():
			return
		self.cancelOsTimer()
		TimeElement.pauseElement(self)
		for el in self._children:
			if el.isTicking():
				el.pauseElement()
				self._pauselist.append(el)

	def resumeElement(self):
		if self.isTicking():
			return
		TimeElement.resumeElement(self)
		for el in self._pauselist:
			el.resumeElement()
		self._pauselist = []
		self.evaluate()

	def seekElement(self, seekTo):
		self.setTime(seekTo)
		if self.isTicking():
			self.cancelOsTimer()
			self.evaluate()

	#
	#  event interface
	#
	def onBeginEvent(self, node):
		for arc in node.beginSyncArcs:
			arc.updateDependant(self.getTime())

	def onEndEvent(self, node):
		for arc in node.endSyncArcs:
			arc.updateDependant(self.getTime())

	def onRepeatEvent(self, node, index):
		for arc in node.repeatSyncArcs:
			arc.updateDependant(self.getTime(), index)
		
	#
	#  navigator interface
	#
	def getNavFirstChild(self, node):
		return node.getFirstTimeChild()

	def getNavNextSibling(self, node):
		return node.getNextTimeSibling()

	def getNavParent(self, node):
		return node.getTimeParent()

	#
	#  implementation specific interface
	#
	def calculateTiming(self):
		doc = self.getTimeDocument()
		iter = doc.createDOMNavigator(self, self, self.calculateTimingCallback)
		while iter.advance(): pass

	def calculateTimingCallback(self, node):
		node.calcBasicTiming()

	def scheduleActionArcs(self):
		for arc in self._arcs:
			delay = arc.getDelay()
			if delay != 'unresolved':
				self._queue.schedule(delay, arc)
		
	def get(self, attr):
		return None

	def setOsTimer(self, ostimer):
		self._ostimer = ostimer

	def cancelOsTimer(self):
		if self._timerid is not None:
			self._ostimer.canceltimer(self._timerid)
			self._timerid = None

	def stopAllTimers(self):
		self.stopTimer()
		for el in self._children:
			if el.isTicking():
				el.stopTimer()
		
	def evaluate(self):
		el = self._queue.getExecList()
		for arc in el:
			arc.execute()
		delay = self._queue.getDelay()
		if delay == 'indefinite':
			delay = 1.0
		self._timerid = None
		if delay is not None and self._ostimer is not None:
			self._timerid = self._ostimer.settimer(delay, (self.evaluate, ()))
		else:
			self.stopAllTimers()
			

