import time
import Qd
import QuickDraw
import mw_globals

class TransitionClass:
	def __init__(self, engine, dict):
		self.ltrb = (0, 0, 0, 0)
		self.dict = dict
		
	def move_resize(self, ltrb):
		self.ltrb = ltrb
		
	def computeparameters(self, value, oldparameters):
		pass
		
class BlitterClass:
	def updatebitmap(self, parameters, src1, src2, tmp, dst, dstrgn):
		pass
		
	def needtmpbitmap(self):
		return 0
		
	def _convertrect(self, ltrb):
		"""Convert an lrtb-style rectangle to the local convention"""
		return ltrb
		
class R1R2BlitterClass(BlitterClass):
	"""parameter is 2 rects, first copy rect2 from src2, then rect1 from src1"""
			
	def updatebitmap(self, parameters, src1, src2, tmp, dst, dstrgn):
		rect1, rect2 = parameters
		rect1 = self._convertrect(rect1)
		rect2 = self._convertrect(rect2)
		Qd.CopyBits(src2, dst, rect2, rect2, QuickDraw.srcCopy, dstrgn)
		Qd.CopyBits(src1, dst, rect1, rect1, QuickDraw.srcCopy, dstrgn)
		
class R1R2R3R4BlitterClass(BlitterClass):
	"""Parameter is 4 rects. Copy src1[rect1] to rect2, src2[rect3] to rect4"""

	def updatebitmap(self, parameters, src1, src2, tmp, dst, dstrgn):
		srcrect1, dstrect1, srcrect2, dstrect2 = parameters
		Qd.CopyBits(src2, dst, srcrect2, dstrect2, QuickDraw.srcCopy, dstrgn)
		Qd.CopyBits(src1, dst, srcrect1, dstrect1, QuickDraw.srcCopy, dstrgn)
		
class R1R2OverlapBlitterClass(BlitterClass):
	"""Like R1R2BlitterClass but rects may overlap, so copy via the temp bitmap"""
	
	def updatebitmap(self, parameters, src1, src2, tmp, dst, dstrgn):
		rect1, rect2 = parameters
		Qd.CopyBits(src2, tmp, rect2, rect2, QuickDraw.srcCopy, dstrgn)
		Qd.CopyBits(src1, tmp, rect1, rect1, QuickDraw.srcCopy, dstrgn)
		Qd.CopyBits(tmp, dst, self.ltrb, self.ltrb, QuickDraw.srcCopy, dstrgn)
			
	def needtmpbitmap(self):
		return 1

class RlistR2OverlapBlitterClass(BlitterClass):
	"""Like R1R2OverlapBlitterClass, but first item is a list of rects"""
		
	def updatebitmap(self, parameters, src1, src2, tmp, dst, dstrgn):
		rectlist, rect2 = parameters
		Qd.CopyBits(src2, tmp, rect2, rect2, QuickDraw.srcCopy, None)
		x0, y0, x1, y1 = self.ltrb
		rgn = Qd.NewRgn()
		for rect in rectlist:
			rgn2 = Qd.NewRgn()
			Qd.RectRgn(rgn2, rect)
			Qd.UnionRgn(rgn, rgn2, rgn)
			Qd.DisposeRgn(rgn2)
		Qd.CopyBits(src1, tmp, self.ltrb, self.ltrb, QuickDraw.srcCopy, rgn)
		Qd.DisposeRgn(rgn)
		Qd.CopyBits(tmp, dst, self.ltrb, self.ltrb, QuickDraw.srcCopy, dstrgn)
		
	def needtmpbitmap(self):
		return 1
	
class FadeBlitterClass(BlitterClass):
	"""Parameter is float in range 0..1, use this as blend value"""
	
	def updatebitmap(self, parameters, src1, src2, tmp, dst, dstrgn):
		value = parameters
		rgb = int(value*0xffff), int(value*0xffff), int(value*0xffff)
		Qd.OpColor(rgb)
		Qd.CopyBits(src2, tmp, self.ltrb, self.ltrb, QuickDraw.srcCopy, dstrgn)
		Qd.CopyBits(src1, tmp, self.ltrb, self.ltrb, QuickDraw.blend, dstrgn)
		Qd.CopyBits(tmp, dst, self.ltrb, self.ltrb, QuickDraw.srcCopy, dstrgn)
		
	def needtmpbitmap(self):
		return 1
	
class NullTransition(TransitionClass, BlitterClass):
	UNIMPLEMENTED=1
	
	def updatebitmap(self, parameters, src1, src2, tmp, dst, dstrgn):
		Qd.CopyBits(src1, dst, self.ltrb, self.ltrb, QuickDraw.srcCopy, dstrgn)
		if self.UNIMPLEMENTED:
			x0, y0, x1, y1 = self.ltrb
			Qd.MoveTo(x0, y0)
			Qd.LineTo(x1, y1)
			Qd.MoveTo(x0, y1)
			Qd.LineTo(x1, y0)
			Qd.MoveTo(x0, (y0+y1)/2)
			Qd.DrawString("%s %s"%(self.dict.get('trtype', '???'), self.dict.get('subtype', '')))
		
class BarWipeTransition(TransitionClass, R1R2BlitterClass):

	def computeparameters(self, value, oldparameters):
		x0, y0, x1, y1 = self.ltrb
		# Assume left-to-right
		xpixels = int(value*(x1-x0)+0.5)
		xcur = x0+xpixels
		return ((x0, y0, xcur, y1), (xcur, y0, x1, y1), )
			
class MiscShapeWipeTransition(TransitionClass, R1R2OverlapBlitterClass):

	def computeparameters(self, value, oldparameters):
		x0, y0, x1, y1 = self.ltrb
		xmid = int((x0+x1+0.5)/2)
		ymid = int((y0+y1+0.5)/2)
		xc0 = int((x0+(1-value)*(xmid-x0))+0.5)
		yc0 = int((y0+(1-value)*(ymid-y0))+0.5)
		xc1 = int((xmid+value*(x1-xmid))+0.5)
		yc1 = int((ymid+value*(y1-ymid))+0.5)
		return ((xc0, yc0, xc1, yc1), (x0, y0, x1, y1))
	
class SingleSweepWipeTransition(TransitionClass, RlistR2OverlapBlitterClass):

	def __init__(self, engine, dict):
		TransitionClass.__init__(self, engine, dict)
		x0, y0, x1, y1 = self.ltrb
		hr = dict.get('horzRepeat', 0)+1
		vr = dict.get('vertRepeat', 0)+1
		self.hsteps = hr
		self.vsteps = vr
		self._recomputeboundaries()
		
	def _recomputeboundaries(self):
		x0, y0, x1, y1 = self.ltrb
		self.hboundaries = []
		self.vboundaries = []
		hr = self.hsteps
		vr = self.vsteps
		for i in range(hr+1):
			self.hboundaries.append(x0 + int((x1-x0)*float(i)/hr + 0.5))
		for i in range(vr+1):
			self.vboundaries.append(y0 + int((y1-y0)*float(i)/vr + 0.5))
		
	def move_resize(self, ltrb):
		TransitionClass.move_resize(self, ltrb)
		self._recomputeboundaries()
		
	def computeparameters(self, value, oldparameters):
		index = int(value*self.hsteps*self.vsteps)
		hindex = index % self.hsteps
		vindex = index / self.hsteps
		x0, y0, x1, y1 = self.ltrb
		rectlist = []
		for i in range(vindex):
			rect = (x0, self.vboundaries[i], x1, self.vboundaries[i+1])
			rectlist.append(rect)
		ylasttop = self.vboundaries[vindex]
		ylastbottom = self.vboundaries[vindex+1]
		for i in range(hindex):
			rect = (self.hboundaries[i], ylasttop, self.hboundaries[i+1], ylastbottom)
			rectlist.append(rect)
		return rectlist, self.ltrb
				
class PushWipeTransition(TransitionClass, R1R2R3R4BlitterClass):

	def computeparameters(self, value, oldparameters):
		x0, y0, x1, y1 = self.ltrb
		# Assume left-to-right
		xpixels = int(value*(x1-x0)+0.5)
		return ((x1-xpixels, y0, x1, y1), (x0, y0, x0+xpixels, y1),
				(x0, y0, x1-xpixels, y1), (x0+xpixels, y0, x1, y1) )
			
class SlideWipeTransition(TransitionClass, R1R2R3R4BlitterClass):

	def computeparameters(self, value, oldparameters):
		x0, y0, x1, y1 = self.ltrb
		# Assume left-to-right
		xpixels = int(value*(x1-x0)+0.5)
		return ((x1-xpixels, y0, x1, y1), (x0, y0, x0+xpixels, y1), 
				(x0+xpixels, y0, x1, y1), (x0+xpixels, y0, x1, y1))
		
class FadeTransition(TransitionClass, FadeBlitterClass):

	def computeparameters(self, value, oldparameters):
		return value
		
TRANSITIONDICT = {
	"barWipe" : BarWipeTransition,
	"miscShapeWipe" : MiscShapeWipeTransition,
	"singleSweepWipe" : SingleSweepWipeTransition,
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
		dur = dict.get('dur', 1)
		self.windows = [window]
		self.starttime = time.time()	# Correct?
		self.duration = dur
		self.running = runit
		self.value = 0
		trtype = dict['trtype']
		subtype = dict.get('subtype')
		klass = TransitionFactory(trtype, subtype)
		self.transitiontype = klass(self, dict)
		self.dstrgn = None
		self.move_resize()
		self.currentparameters = None
		
		self.reverse = (dict['direction'] == 'reverse')
		if not self.reverse:
			self.startprogress = dict['startProgress']
			self.endprogress = dict['endProgress']
		else:
			self.startprogress = 1.0 - dict['endProgress']
			self.endprogress = 1.0 - dict['startProgress']
		# Now recompute starttime and "duration" based on these values
		self.duration = self.duration / (self.endprogress-self.startprogress)
		self.starttime = self.starttime - (self.startprogress*self.duration)
		
		mw_globals.toplevel.setidleproc(self._idleproc)
		
	def join(self, window):
		"""Join this (sub or super) window to an existing transition"""
		self.windows.append(window)
		self.move_resize()
		
	def endtransition(self):
		"""Called by upper layer (window) to tear down the transition"""
		if self.windows != None:
			mw_globals.toplevel.cancelidleproc(self._idleproc)
			self.windows = None
			self.transitiontype = None
		
	def need_tmp_wid(self):
		return self.transitiontype.needtmpbitmap()
		
	def move_resize(self):
		"""Internal: recompute the region and rect on which this transition operates"""
		if self.dstrgn:
			Qd.DisposeRgn(self.dstrgn)
		x0, y0, x1, y1 = self.windows[0].qdrect()
		self.dstrgn = Qd.NewRgn()
		for w in self.windows:
			rect = w.qdrect()
			newrgn = Qd.NewRgn()
			Qd.RectRgn(newrgn, rect)
			Qd.UnionRgn(self.dstrgn, newrgn, self.dstrgn)
			Qd.DisposeRgn(newrgn)
			nx0, ny0, nx1, ny1 = rect
			if nx0 < x0: x0 = nx0
			if ny0 < y0: y0 = ny0
			if nx1 > x1: x1 = nx1
			if ny1 > y1: y1 = ny1
		self.transitiontype.move_resize((x0, y0, x1, y1))
			
		
	def _idleproc(self):
		"""Called in the event loop to optionally do a recompute"""
		self.changed(0)
		
	def changed(self, mustredraw=1):
		"""Called by upper layer when it wants the destination bitmap recalculated. If
		mustredraw is true we should do the recalc even if the transition hasn't advanced."""
		if self.running:
			self.value = float(time.time() - self.starttime) / self.duration
			if self.reverse:
				self.value = 1 - self.value
			if self.value >= self.endprogress:
				self._cleanup()
				return
		self._doredraw(mustredraw)
		
	def settransitionvalue(self, value):
		"""Called by uppoer layer when it has a new percentage value"""
		self.value = value
		self._doredraw()
		
	def _cleanup(self):
		"""Internal function called when our time is up. Ask the upper layer (window)
		to tear us down"""
		wcopy = self.windows[:]
		for w in wcopy:
			w.endtransition()
		
	def _doredraw(self, mustredraw):
		"""Internal: do the actual computation, iff anything has changed since last time"""
		oldparameters = self.currentparameters
		self.currentparameters = self.transitiontype.computeparameters(self.value, oldparameters)
		if self.currentparameters == oldparameters and not mustredraw:
			return
		# All windows in the transition share their bitmaps, so we can pick any of them
		w = self.windows[0]
		dst = w._mac_getoswindowpixmap(mw_globals.BM_ONSCREEN)
		src_active = w._mac_getoswindowpixmap(mw_globals.BM_DRAWING)
		src_passive = w._mac_getoswindowpixmap(mw_globals.BM_PASSIVE)
		tmp = w._mac_getoswindowpixmap(mw_globals.BM_TEMP)
		w._mac_setwin(mw_globals.BM_ONSCREEN)
		Qd.RGBBackColor((0xffff, 0xffff, 0xffff))
		Qd.RGBForeColor((0, 0, 0))
		self.transitiontype.updatebitmap(self.currentparameters, src_active, src_passive, tmp, dst, 
			self.dstrgn)
