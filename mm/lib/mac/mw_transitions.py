import time
import Qd
import QuickDraw
import mw_globals

class TransitionClass:
	def __init__(self, engine, ltrb, dict):
		self.ltrb = ltrb
		self.dict = dict
##		self.initial_update = 1
		
	def _computeparameters(self, value, oldparameters):
		pass
		
	def _updatebitmap(self, parameters, src1, src2, tmp, dst):
##		self.initial_update = 0
		pass
		
	def _needtmpbitmap(self):
		return 0
		
class NullTransition(TransitionClass):
	UNIMPLEMENTED=0
	
	def _updatebitmap(self, parameters, src1, src2, tmp, dst):
		Qd.CopyBits(src1, dst, self.ltrb, self.ltrb, QuickDraw.srcCopy, None)
		if self.UNIMPLEMENTED:
			x0, y0, x1, y1 = self.ltrb
			Qd.MoveTo(x0, y0)
			Qd.LineTo(x1, y1)
			Qd.MoveTo(x0, y1)
			Qd.LineTo(x1, y0)
		
class EdgeWipeTransition(TransitionClass):
	# Wipes. Parameters are two ltrb tuples
	def _computeparameters(self, value, oldparameters):
		x0, y0, x1, y1 = self.ltrb
		# Assume left-to-right
		xpixels = int(value*(x1-x0)+0.5)
		xcur = x0+xpixels
		return ((x0, y0, xcur, y1), (xcur, y0, x1, y1), )
		
	def _updatebitmap(self, parameters, src1, src2, tmp, dst):
		rect1, rect2 = parameters
		Qd.CopyBits(src2, dst, rect2, rect2, QuickDraw.srcCopy, None)
		Qd.CopyBits(src1, dst, rect1, rect1, QuickDraw.srcCopy, None)
			
class IrisWipeTransition(TransitionClass):
	def _computeparameters(self, value, oldparameters):
		x0, y0, x1, y1 = self.ltrb
		xmid = int((x0+x1+0.5)/2)
		ymid = int((y0+y1+0.5)/2)
		xc0 = int((x0+(1-value)*(xmid-x0))+0.5)
		yc0 = int((y0+(1-value)*(ymid-y0))+0.5)
		xc1 = int((xmid+value*(x1-xmid))+0.5)
		yc1 = int((ymid+value*(y1-ymid))+0.5)
		return ((xc0, yc0, xc1, yc1), (x0, y0, x1, y1))

	def _updatebitmap(self, parameters, src1, src2, tmp, dst):
		rect1, rect2 = parameters
		Qd.CopyBits(src2, tmp, rect2, rect2, QuickDraw.srcCopy, None)
		Qd.CopyBits(src1, tmp, rect1, rect1, QuickDraw.srcCopy, None)
		Qd.CopyBits(tmp, dst, self.ltrb, self.ltrb, QuickDraw.srcCopy, None)
			
	def _needtmpbitmap(self):
		return 1
		
		
class RadialWipeTransition(NullTransition):
	UNIMPLEMENTED=1
	
class MatrixWipeTransition(NullTransition):
	UNIMPLEMENTED=1
	
class PushWipeTransition(TransitionClass):
	# Parameters are src1-ltrb, dst1-ltrb, src2-ltrb, dst2-ltrb
	def _computeparameters(self, value, oldparameters):
		x0, y0, x1, y1 = self.ltrb
		# Assume left-to-right
		xpixels = int(value*(x1-x0)+0.5)
		return ((x1-xpixels, y0, x1, y1), (x0, y0, x0+xpixels, y1),
				(x0, y0, x1-xpixels, y1), (x0+xpixels, y0, x1, y1) )

	def _updatebitmap(self, parameters, src1, src2, tmp, dst):
		srcrect1, dstrect1, srcrect2, dstrect2 = parameters
		Qd.CopyBits(src2, dst, srcrect2, dstrect2, QuickDraw.srcCopy, None)
		Qd.CopyBits(src1, dst, srcrect1, dstrect1, QuickDraw.srcCopy, None)
			
class SlideWipeTransition(TransitionClass):
	# Parameters are src1-ltrb, dst1-ltrb, 2-ltrb
	def _computeparameters(self, value, oldparameters):
		x0, y0, x1, y1 = self.ltrb
		# Assume left-to-right
		xpixels = int(value*(x1-x0)+0.5)
		return ((x1-xpixels, y0, x1, y1), (x0, y0, x0+xpixels, y1), (x0+xpixels, y0, x1, y1), )

	def _updatebitmap(self, parameters, src1, src2, tmp, dst):
		srcrect1, dstrect1, rect2 = parameters
		Qd.CopyBits(src2, dst, rect2, rect2, QuickDraw.srcCopy, None)
		Qd.CopyBits(src1, dst, srcrect1, dstrect1, QuickDraw.srcCopy, None)
		
class FadeTransition(TransitionClass):
	def _computeparameters(self, value, oldparameters):
		return int(value*0xffff), int(value*0xffff), int(value*0xffff)
		
	def _updatebitmap(self, parameters, src1, src2, tmp, dst):
		Qd.OpColor(parameters)
		Qd.CopyBits(src2, tmp, self.ltrb, self.ltrb, QuickDraw.srcCopy, None)
		Qd.CopyBits(src1, tmp, self.ltrb, self.ltrb, QuickDraw.blend, None)
		Qd.CopyBits(tmp, dst, self.ltrb, self.ltrb, QuickDraw.srcCopy, None)
		
	def _needtmpbitmap(self):
		return 1
	
TRANSITIONDICT = {
	"edgeWipe" : EdgeWipeTransition,
	"irisWipe" : IrisWipeTransition,
	"radialWipe" : RadialWipeTransition,
	"matrixWipe" : MatrixWipeTransition,
	"pushWipe" : PushWipeTransition,
	"slideWipe" : SlideWipeTransition,
	"fade" : FadeTransition,
}

def TransitionFactory(trtype, subtype):
	"""Return the class that implements this transition. Incomplete, only looks
	at type right now"""
	if TRANSITIONDICT.has_key(trtype):
		return TRANSITIONDICT[trtype]
	return NullTransition

class TransitionEngine:
	def __init__(self, window, inout, runit, dict):
##		print 'transition', self, window, time.time(), dict
		dur = dict.get('dur', 1)
		self.window = window
		self.starttime = time.time()	# Correct?
		self.duration = dur
		self.running = runit
		self.value = 0
		ltrb = window.qdrect()
		trtype = dict['trtype']
		subtype = dict.get('subtype')
		klass = TransitionFactory(trtype, subtype)
		self.transitiontype = klass(self, ltrb, dict)
		self.currentparameters = None
		# xxx startpercent/endpercent
		# xxx transition type, etc
		mw_globals.toplevel.setidleproc(self._idleproc)
		
	def endtransition(self):
		"""Called by upper layer (window) to tear down the transition"""
##		print 'endtransition', self, time.time()
		mw_globals.toplevel.cancelidleproc(self._idleproc)
		self.window = None
		self.transitiontype = None
		
	def need_tmp_wid(self):
		return self.transitiontype._needtmpbitmap()
		
	def _idleproc(self):
		"""Called in the event loop to optionally do a recompute"""
		self.changed(0)
		
	def changed(self, mustredraw=1):
		"""Called by upper layer when it wants the destination bitmap recalculated. If
		mustredraw is true we should do the recalc even if the transition hasn't advanced."""
		if self.running:
			self.value = float(time.time() - self.starttime) / self.duration
			if self.value >= 0.5:
				pass # DBG
			if self.value >= 1.0:
				self._cleanup()
				return
		self._updatebitmap(mustredraw)
		
	def settransitionvalue(self, value):
		"""Called by uppoer layer when it has a new percentage value"""
		self.value = value / 100.0
		self._updatebitmap()
		
	def _cleanup(self):
		"""Internal function called when our time is up. Ask the upper layer (window)
		to tear us down"""
		if self.window:
			self.window.endtransition()
		
	def _updatebitmap(self, mustredraw):
		"""Internal: do the actual computation, iff anything has changed since last time"""
		oldparameters = self.currentparameters
		self.currentparameters = self.transitiontype._computeparameters(self.value, oldparameters)
		if self.currentparameters == oldparameters and not mustredraw:
			return
##		print self.currentparameters
		dst = self.window._mac_getoswindowpixmap(0)
		src_active = self.window._mac_getoswindowpixmap(1)
		src_passive = self.window._mac_getoswindowpixmap(2)
		tmp = self.window._mac_getoswindowpixmap(3)
		self.window._mac_setwin(0)
		print 'TRANS', src_active, src_passive, dst, self.window
		print 'TRANSARGS', self.currentparameters
		Qd.RGBBackColor((0xffff, 0xffff, 0xffff))
		Qd.RGBForeColor((0, 0, 0))
		self.transitiontype._updatebitmap(self.currentparameters, src_active, src_passive, tmp, dst)
