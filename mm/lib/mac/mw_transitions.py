import time
import Qd
import mw_globals
import math
import Transitions
	
class TransitionEngine:
	def __init__(self, window, inout, runit, dict):
		dur = dict.get('dur', 1)
		self.exclude_first_window = 0
		# if this is a multieElt transition with clipChildren we should not
		# include the parent in the clip.
		if dict.get('multiElement') and dict.get('childrenClip'):
			self.exclude_first_window = 1
		self.windows = [window]
		self.starttime = time.time()	# Correct?
		self.duration = dur
		self.running = runit
		self.value = 0
		trtype = dict['trtype']
		subtype = dict.get('subtype')
		klass = Transitions.TransitionFactory(trtype, subtype)
		self.transitiontype = klass(self, dict)
		self.dstrgn = None
		self.move_resize()
		self.currentparameters = None
		
##		self.reverse = (dict['direction'] == 'reverse')
		self.reverse = 0
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
		
	def join(self, window, ismaster):
		"""Join this (sub or super) window to an existing transition"""
		if ismaster:
			self.windows.insert(0, window)
		else:
			self.windows.append(window)
		self.move_resize()
		
	def endtransition(self):
		"""Called by upper layer (window) to tear down the transition"""
		if self.windows != None:
			# Show final result (saves us a redraw in window code)
			self.value = 1.0
			self._doredraw(0)
			# Tear down our datastructures
			mw_globals.toplevel.cancelidleproc(self._idleproc)
			self.windows = None
			self.transitiontype = None
		
	def need_tmp_wid(self):
		return self.transitiontype.needtmpbitmap()
		
	def move_resize(self):
		"""Internal: recompute the region and rect on which this transition operates"""
		if self.dstrgn:
			Qd.DisposeRgn(self.dstrgn)
		exclude_first_window = self.exclude_first_window
		x0, y0, x1, y1 = self.windows[0].qdrect()
		self.dstrgn = Qd.NewRgn()
		print 'move_resize', self, (x0, y0, x1, y1)
		for w in self.windows:
			rect = w.qdrect()
			if exclude_first_window:
				exclude_first_window = 0
				print 'dont include', rect
			else:
				print 'include', rect
				newrgn = Qd.NewRgn()
				Qd.RectRgn(newrgn, rect)
				Qd.UnionRgn(self.dstrgn, newrgn, self.dstrgn)
				Qd.DisposeRgn(newrgn)
			nx0, ny0, nx1, ny1 = rect
			if nx0 < x0: 
				x0 = nx0
			if ny0 < y0: 
				y0 = ny0
			if nx1 > x1:
				x1 = nx1
			if ny1 > y1:
				y1 = ny1
		print 'transition size now', (x0, y0, x1, y1), self
		self.transitiontype.move_resize((x0, y0, x1, y1))
			
	def ismaster(self, window):
		return window == self.windows[0]
		
	def _idleproc(self):
		"""Called in the event loop to optionally do a recompute"""
		self.changed(0)
		
	def changed(self, mustredraw=1):
		"""Called by upper layer when it wants the destination bitmap recalculated. If
		mustredraw is true we should do the recalc even if the transition hasn't advanced."""
		if self.running:
			self.value = float(time.time() - self.starttime) / self.duration
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
		self.currentparameters = self.transitiontype.computeparameters(self.value)
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
