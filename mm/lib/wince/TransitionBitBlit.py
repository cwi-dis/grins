__version__ = "$Id$"

# BitBlitter base classes for machine-independent transition classes.
# See comment at the beginning of Transitions for an explanation of the overall
# architecture.

import wingdi
import wincon 

class BlitterClass:
	SHOW_UNIMPLEMENTED_TRANSITION_NAME=1
	
	def __init__(self, engine, dict):
		self._engine = engine
		self._dict = dict
	
	def updatebitmap(self, parameters, src1, src2, tmp, dst, dstrgn):
		# Called by the engine when the parameters have changed and the
		# destination bitmap has to be recomputed. Also called for other redraw reasons.
		pass
					
	def needtmpbitmap(self):
		# Return true if this blitter needs the temporary bitmap.
		return 1
		
	def _convertrect(self, ltrb):
		# Convert an lrtb-style rectangle to the local convention
		l,t,r,b = ltrb
		return l,t,r-l,b-t
	
	def isempty(self, ltrb):
		l,t,r,b = ltrb
		return r==l or b==t

	def getDC(self, dds):
		hdc = dds.GetDC()
		if not hdc: return None
		return wingdi.CreateDCFromHandle(hdc)

	def releaseDC(self, dds, dc):
		if dc:
			hdc = dc.Detach()
			dds.ReleaseDC(hdc)

	# we don't have support for CreatePolygonRgn under CE
	def createRegion(self, pointlist):
		npl = []
		l, t, r, b = 10000, 10000, -10000, -10000
		for p in pointlist:
			x = int(p[0]+0.5)
			y = int(p[1]+0.5)
			l, r = min(l, x), max(r, x) 
			t, b = min(t, y), max(b, y) 
			#npl.append((x,y))
		rgn = None
		try:
			#rgn = wingdi.CreatePolygonRgn(npl)
			rgn = wingdi.CreateRectRgn((l, t, r, b))
		except wingdi.error, arg:
			print arg
			rgn = None
		return rgn

class R1R2BlitterClass(BlitterClass):
	# parameter is 2 rects, first copy rect2 from src2, then rect1 from src1
	def updatebitmap(self, parameters, src1, src2, tmp, dst, dstrgn):
		rect1, rect2 = parameters
		wingdi.BitBltDIBSurface(src2, dst, rect2, rect2)
		wingdi.BitBltDIBSurface(src1, dst, rect1, rect1)
		
class R1R2R3R4BlitterClass(BlitterClass):
	# Parameter is 4 rects. Copy src1[rect1] to rect2, src2[rect3] to rect4
	def updatebitmap(self, parameters, src1, src2, tmp, dst, dstrgn):
		srcrect1, dstrect1, srcrect2, dstrect2 = parameters
		wingdi.BitBltDIBSurface(src1, dst, srcrect1, dstrect1)
		wingdi.BitBltDIBSurface(src2, dst, srcrect2, dstrect2)
		
class R1R2OverlapBlitterClass(BlitterClass):
	# Like R1R2BlitterClass but rects may overlap, so copy via the temp bitmap
	def updatebitmap(self, parameters, src1, src2, tmp, dst, dstrgn):
		rect1, rect2 = parameters
		wingdi.BitBltDIBSurface(src2, tmp, rect2, rect2)
		wingdi.BitBltDIBSurface(src1, tmp, rect1, rect1)
		wingdi.BitBltDIBSurface(tmp, dst, self.ltrb, self.ltrb)
				
class RlistR2OverlapBlitterClass(BlitterClass):
	# Like R1R2OverlapBlitterClass, but first item is a list of rects
	def updatebitmap(self, parameters, src1, src2, tmp, dst, dstrgn):
		rectlist, rect2 = parameters
		wingdi.BitBltDIBSurface(src2, tmp, rect2, rect2)
		x0, y0, x1, y1 = self.ltrb
		for rect in rectlist:
			wingdi.BitBltDIBSurface(src1, tmp, rect, rect)
		wingdi.BitBltDIBSurface(tmp, dst, self.ltrb, self.ltrb)
	
class PolyR2OverlapBlitterClass(BlitterClass):
	# Like R1R2OverlapBlitterClass, but first item is a polygon (list of points)
	def updatebitmap(self, parameters, src1, src2, tmp, dst, dstrgn):
		pointlist, rect2 = parameters
		wingdi.BitBltDIBSurface(src2, tmp, rect2, rect2)
		if pointlist:
			rgn = self.createRegion(pointlist)
			wingdi.BitBltDIBSurface(src1, tmp, self.ltrb, self.ltrb, rgn)
			if rgn: rgn.DeleteObject()
		wingdi.BitBltDIBSurface(tmp, dst, self.ltrb, self.ltrb)

class PolylistR2OverlapBlitterClass(BlitterClass):
	# Like PolyR2OverlapBlitterClass, but first item is a list of polygons
		
	def updatebitmap(self, parameters, src1, src2, tmp, dst, dstrgn):
		pointlist, rect2 = parameters
		wingdi.BitBltDIBSurface(src2, tmp, rect2, rect2)
		if pointlist:
			rgn = self.createRegion(pointlist[0])
			if rgn:
				for pl in pointlist[1:]:
					newrgn = self.createRegion(pl)
					if newrgn:
						rgn.CombineRgn(rgn,newrgn, wincon.RGN_OR)
						newrgn.DeleteObject()
				wingdi.BitBltDIBSurface(src1, tmp, self.ltrb, self.ltrb, rgn)
				rgn.DeleteObject()
		wingdi.BitBltDIBSurface(tmp, dst, self.ltrb, self.ltrb)

	
class FadeBlitterClass(BlitterClass):
	# Parameter is float in range 0..1, use this as blend value
	def updatebitmap(self, parameters, src1, src2, tmp, dst, dstrgn):
		value = parameters
		try:
			wingdi.BltBlendDIBSurface(src2, src1, dst, value)
		except wingdi.error, arg:
			print arg


