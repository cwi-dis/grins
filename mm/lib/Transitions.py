# Machine-independent part of transitions.
#
# This module creates a number of transition classes. Each transition class
# consists of a machine-dependent base class that handles a specific type of bitblit and
# a subclass (declared here) that does the actual computation.
#
# This module also contains the factory function that handles creating the
# classes.
#
# These transition classes are driven by a machine dependent module that knows
# how to obtain the parameters that that bitblitters want from the windowinterface
# objects.
#
# XXX To be done: drawing color outlines if wanted
# XXX To be done: implementing more than the default subtype for each transition

import math

TAN_PI_DIV_3 = math.tan(math.pi/3)

from TransitionBitBlit import BlitterClass, R1R2BlitterClass, R1R2OverlapBlitterClass, \
	RlistR2OverlapBlitterClass, PolyR2OverlapBlitterClass, R1R2R3R4BlitterClass, \
	FadeBlitterClass

class TransitionClass:

	def __init__(self, engine, dict):
		"""Initialize a transition. Engine is our machine-dependent engine (not
		used here but the blitter may want it) and dict is the MMNode transition
		object"""
		# This is funky but it works: we know that our subclasses will inherit
		# some for of BlitterClass.
		BlitterClass.__init__(self, engine, dict)
		self.ltrb = (0, 0, 0, 0)
		self.dict = dict
		
	def move_resize(self, ltrb):
		"""Called by the engine whenever the windowinterface code has resized
		or moved the window, or when a new window has joined the transition.
		Can be overridden by subclasses."""
		self.ltrb = ltrb
		
	def computeparameters(self, value):
		"""Compute a set of parameters (understandable to our blitter) that fully
		describe the state the display should be in. The engine is responsible for
		comparing this to the previous set and not doing an update if not needed."""
		return None
		

class NullTransition(TransitionClass, BlitterClass):
	pass
			
class BarWipeTransition(TransitionClass, R1R2BlitterClass):
	# Reveal the new image by sweeping a divider line from left to right

	def computeparameters(self, value):
		x0, y0, x1, y1 = self.ltrb
		# Assume left-to-right
		xpixels = int(value*(x1-x0)+0.5)
		xcur = x0+xpixels
		return ((x0, y0, xcur, y1), (xcur, y0, x1, y1))
			
class BoxWipeTransition(TransitionClass, R1R2OverlapBlitterClass):
	# Reveal the new image by an expanding box

	def computeparameters(self, value):
		x0, y0, x1, y1 = self.ltrb
		# Assume left-to-right
		xpixels = int(value*(x1-x0)+0.5)
		ypixels = int(value*(y1-y0)+0.5)
		xcur = x0+xpixels
		ycur = y0+ypixels
		return ((x0, y0, xcur, ycur), (x0, y0, x1, y1))
			
class FourBoxWipeTransition(TransitionClass, RlistR2OverlapBlitterClass):
	# Reveal the new image by 4 boxes growing from the corners to the center

	def computeparameters(self, value):
		x0, y0, x1, y1 = self.ltrb
		xmid = (x0+x1)/2
		ymid = (y0+y1)/2
		xpixels = int(value*(xmid-x0)+0.5)
		ypixels = int(value*(ymid-y0)+0.5)
		boxes = (
			(x0, y0, x0+xpixels, y0+ypixels),
			(x1-xpixels, y0, x1, y0+ypixels),
			(x0, y1-ypixels, x0+xpixels, y1),
			(x1-xpixels, y1-ypixels, x1, y1))
		return (boxes, (x0, y0, x1, y1))
			
class BarnDoorWipeTransition(TransitionClass, R1R2OverlapBlitterClass):
	# Reveal the new image by sweeping two divier lines from the center outward

	def computeparameters(self, value):
		x0, y0, x1, y1 = self.ltrb
		xmid = (x0+x1)/2
		xpixels = int(value*(xmid-x0)+0.5)
		return ((xmid-xpixels, y0, xmid+xpixels, y1), (x0, y0, x1, y1))
		
class DiagonalWipeTransition(TransitionClass, PolyR2OverlapBlitterClass):
	# Reveal the new image by sweeping a diagonal divider line

	def computeparameters(self, value):
		x0, y0, x1, y1 = self.ltrb
		xwidth = (x1-x0)
		xmin = x0 - 2*xwidth
		xcur = xmin + int(value*2*xwidth)
		poly = (
			(xcur, y0),
			(xcur+2*xwidth, y0),
			(xcur+xwidth, y1),
			(xcur, y1))
		return poly, self.ltrb

class TriangleWipeTransition(TransitionClass, PolyR2OverlapBlitterClass):
	# Reveal the new image by a triangle growing from the center outward
	
	def __init__(self, engine, dict):
		TransitionClass.__init__(self, engine, dict)
		self._recomputetop()
		
	def move_resize(self, ltrb):
		TransitionClass.move_resize(self, ltrb)
		self._recomputetop()
		
	def _recomputetop(self):
		x0, y0, x1, y1 = self.ltrb
		self.xmid = (x0+x1)/2
		self.ymid = (y0+y1)/2
		ytop = y1 + int(TAN_PI_DIV_3*(self.xmid-x0))
		self.range = ytop-self.ymid
		
	def computeparameters(self, value):
		totop = int(value*self.range)
		ytop = self.ymid - totop
		ybot = self.ymid + totop/2
		height = ybot - ytop
		base_div_2 = height / TAN_PI_DIV_3
		xleft = int(self.xmid - base_div_2)
		xright = int(self.xmid + base_div_2)
		points = (
			(xleft, ybot),
			(self.xmid, ytop),
			(xright, ybot))
		return points, self.ltrb
	
class MiscShapeWipeTransition(TransitionClass, R1R2OverlapBlitterClass):
	# Reveal the new image by a square growing from the center outward

	def computeparameters(self, value):
		x0, y0, x1, y1 = self.ltrb
		xmid = int((x0+x1+0.5)/2)
		ymid = int((y0+y1+0.5)/2)
		xc0 = int((x0+(1-value)*(xmid-x0))+0.5)
		yc0 = int((y0+(1-value)*(ymid-y0))+0.5)
		xc1 = int((xmid+value*(x1-xmid))+0.5)
		yc1 = int((ymid+value*(y1-ymid))+0.5)
		return ((xc0, yc0, xc1, yc1), (x0, y0, x1, y1))
	
class _MatrixTransitionClass(TransitionClass, RlistR2OverlapBlitterClass):
	# Generic subclass for all the matrix transitions

	def __init__(self, engine, dict):
		TransitionClass.__init__(self, engine, dict)
##XXXX It seems this is _not_ the intention of horzRepeat and vertRepeat
##		hr = dict.get('horzRepeat', 0)+1
##		vr = dict.get('vertRepeat', 0)+1
		hr = 8
		vr = 8
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
				
class SingleSweepWipeTransition(_MatrixTransitionClass):
	# Reveal the new images by sweeping over the matrix left-to-right, top-to-botton
		
	def computeparameters(self, value):
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
		
class SnakeWipeTransition(_MatrixTransitionClass):
	# Reveal the new image by sweeping left-to-right, then on the next line right-to-left, etc
		
	def computeparameters(self, value):
		index = int(value*self.hsteps*self.vsteps+0.5)
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
			if vindex % 2:
				idx = self.hsteps-i-1
			else:
				idx = i
			rect = (self.hboundaries[idx], ylasttop, self.hboundaries[idx+1], ylastbottom)
			rectlist.append(rect)
		return rectlist, self.ltrb
		
class ParallelSnakesWipeTransition(_MatrixTransitionClass):
	# Reveal the new image by sweeping left-to-right, then on the next line right-to-left, etc
	# And the same from bottom up
		
	def computeparameters(self, value):
		index = int(0.5*value*self.hsteps*self.vsteps+0.5)
		hindex = index % self.hsteps
		vindex = index / self.hsteps
		x0, y0, x1, y1 = self.ltrb
		rectlist = []
		for i in range(vindex):
			rect = (x0, self.vboundaries[i], x1, self.vboundaries[i+1])
			rectlist.append(rect)
			rect = (x0, self.vboundaries[self.vsteps-i-1], x1, self.vboundaries[self.vsteps-i])
			rectlist.append(rect)
		ylasttop = self.vboundaries[vindex]
		ylastbottom = self.vboundaries[vindex+1]
		ydowntop = self.vboundaries[self.vsteps-vindex-1]
		ydownbottom = self.vboundaries[self.vsteps-vindex]
		for i in range(hindex):
			if vindex % 2:
				idx = self.hsteps-i-1
			else:
				idx = i
			rect = (self.hboundaries[idx], ylasttop, self.hboundaries[idx+1], ylastbottom)
			rectlist.append(rect)
			rect = (self.hboundaries[idx], ydowntop, self.hboundaries[idx+1], ydownbottom)
			rectlist.append(rect)
		return rectlist, self.ltrb
		
class SpiralWipeTransition(_MatrixTransitionClass):
	# Reveal the new image by spiralling over the matrix
	
	def _recomputeboundaries(self):
		_MatrixTransitionClass._recomputeboundaries(self)
		self._xy_to_step = []
		xmax = self.hsteps-1
		ymax = self.vsteps-1
		ymax = 7
		xinc = 1
		yinc = 1
		x = 0
		y = 0
		skipfirstxmaxdecrement = 1
		while xmax >= 0 or ymax >= 0:
			for i in range(xmax):
				self._xy_to_step.append((x, y))
				x = x + xinc
			xinc = -xinc
			if skipfirstxmaxdecrement:
				skipfirstxmaxdecrement = 0
			else:
				xmax = xmax - 1
			for i in range(ymax):
				self._xy_to_step.append((x, y))
				y = y + yinc
			yinc = -yinc
			ymax = ymax - 1
		x = x - 1
		self._xy_to_step.append((x, y))
		self._xy_to_step.append((x, y))
		
	def computeparameters(self, value):
		index = int(value*self.hsteps*self.vsteps+0.5)
		rectlist = []
		for i in range(index):
			x, y = self._xy_to_step[i]
			rect = (self.hboundaries[x], self.vboundaries[y], 
					self.hboundaries[x+1], self.vboundaries[y+1])
			rectlist.append(rect)
		return rectlist, self.ltrb

class BoxSnakesWipeTransition(_MatrixTransitionClass):
	# Reveal the new image by spiralling over the matrix twice, top and bottom symmetric
	
	def _recomputeboundaries(self):
		_MatrixTransitionClass._recomputeboundaries(self)
		self._xy_to_step = []
		xmax = self.hsteps-1
		ymax = self.vsteps/2-1
		xinc = 1
		yinc = 1
		x = 0
		y = 0
		skipfirstxmaxdecrement = 1
		while xmax >= 0 or ymax >= 0:
			for i in range(xmax):
				self._xy_to_step.append((x, y))
				self._xy_to_step.append((x, self.vsteps-y-1))
				x = x + xinc
			xinc = -xinc
			if skipfirstxmaxdecrement:
				skipfirstxmaxdecrement = 0
			else:
				xmax = xmax - 1
			for i in range(ymax):
				self._xy_to_step.append((x, y))
				self._xy_to_step.append((x, self.vsteps-y-1))
				y = y + yinc
			yinc = -yinc
			ymax = ymax - 1
		x = x - 1
		self._xy_to_step.append((x, y))
		self._xy_to_step.append((x, self.vsteps-y-1))
		self._xy_to_step.append((x, y))
		self._xy_to_step.append((x, self.vsteps-y-1))
		for i in range(len(self._xy_to_step)):
			print i, self._xy_to_step[i]
		
	def computeparameters(self, value):
		index = int(value*self.hsteps*self.vsteps+0.5)
		rectlist = []
		for i in range(index):
			x, y = self._xy_to_step[i]
			rect = (self.hboundaries[x], self.vboundaries[y], 
					self.hboundaries[x+1], self.vboundaries[y+1])
			rectlist.append(rect)
		return rectlist, self.ltrb

class WaterfallWipeTransition(_MatrixTransitionClass):
	# Reveal the new image by a waterfall-like pattern over the matrix
	
	def computeparameters(self, value):
		totalsteps = self.hsteps + 2*(self.vsteps-1)
		curstep = int(value*totalsteps+0.5)
		rectlist = []
		startstep = 0
		for x in range(self.hsteps):
			thismaxy = min(self.vsteps, curstep-startstep)
			for y in range(thismaxy):
				rect = (self.hboundaries[x], self.vboundaries[y], 
					self.hboundaries[x+1], self.vboundaries[y+1])
				rectlist.append(rect)
			startstep = startstep + 2
		return rectlist, self.ltrb
		
class PushWipeTransition(TransitionClass, R1R2R3R4BlitterClass):
	# Push in the new image, pushing out the old one

	def computeparameters(self, value):
		x0, y0, x1, y1 = self.ltrb
		# Assume left-to-right
		xpixels = int(value*(x1-x0)+0.5)
		return ((x1-xpixels, y0, x1, y1), (x0, y0, x0+xpixels, y1),
				(x0, y0, x1-xpixels, y1), (x0+xpixels, y0, x1, y1) )
			
class SlideWipeTransition(TransitionClass, R1R2R3R4BlitterClass):
	# Slide the new image over the old one

	def computeparameters(self, value):
		x0, y0, x1, y1 = self.ltrb
		# Assume left-to-right
		xpixels = int(value*(x1-x0)+0.5)
		return ((x1-xpixels, y0, x1, y1), (x0, y0, x0+xpixels, y1), 
				(x0+xpixels, y0, x1, y1), (x0+xpixels, y0, x1, y1))
		
class FadeTransition(TransitionClass, FadeBlitterClass):
	# Fade the old image to the new one

	def computeparameters(self, value):
		return value
		
TRANSITIONDICT = {
	"barWipe" : BarWipeTransition,
	"boxWipe" : BoxWipeTransition,
	"fourBoxWipe" : FourBoxWipeTransition,
	"barnDoorWipe" : BarnDoorWipeTransition,
	"diagonalWipe" : DiagonalWipeTransition,
#	"bowTieWipe" : BowTieWipeTransition,
#	"miscDiagonalWipe" : MiscDiagonalWipeTransition,
#	"veeWipe" : VeeWipeTransition,
#	"barnVeeWipe" : BarnVeeWipeTransition,
	"miscShapeWipe" : MiscShapeWipeTransition,
	"triangleWipe" : TriangleWipeTransition,
#	"arrowHeadWipe" : ArrowHeadWipeTransition,
#	"pentagonWipe" : PentagonWipeTransition,
#	"hexagonWipe" : HexagonWipeTransition,
#	"ellipseWipe" : EllipseWipeTransition,
#	"eyeWipe" : EyeWipeTransition,
#	"roundRectWipe" : RoundRectWipeTransition,
#	"starWipe" : StarWipeTransition,
#	"clockWipe" : ClockWipeTransition,
#	"pinWheelWipe" : PinWheelWipeTransition,
	"singleSweepWipe" : SingleSweepWipeTransition,
#	"fanWipe" : FanWipeTransition,
#	"doubleFanWipe" : DoubleFanWipeTransition,
#	"doubleSweepWipe" : DoubleSweepWipeTransition,
#	"saloonDoorWipe" : SaloonDoorWipeTransition,
#	"windshieldWipe" : WindShieldWipeTransition,
	"snakeWipe" : SnakeWipeTransition,
	"spiralWipe" : SpiralWipeTransition,
	"parallelSnakesWipe" : ParallelSnakesWipeTransition,
	"boxSnakesWipe" : BoxSnakesWipeTransition,
	"waterfallWipe" : WaterfallWipeTransition,
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

