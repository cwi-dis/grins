__version__ = "$Id$"

import sys

[A_L, A_R]=range(2)
	
def __getCoeffSeg(xOrigSeg, yOrigSeg, xDestSeg, yDestSeg):
	if xDestSeg == xOrigSeg:
		a = 99999999
	else:
		a = float(yDestSeg-yOrigSeg)/float(xDestSeg-xOrigSeg)
	b = yOrigSeg-a*xOrigSeg

	return a,b

def __changeRepere(xOrig, yOrig, x, y):
	return x-xOrig,y-yOrig

def insideRect(xSrc, ySrc, x1Rect, y1Rect, x2Rect, y2Rect):
	return x1Rect <= xSrc < x2Rect and y1Rect <= ySrc < y2Rect

def insideCircle(xSrc, ySrc, xCenter, yCenter, radius):
	import math
	m1=ySrc-yCenter
	m1 = m1*m1
	m2 = xSrc-xCenter
	m2 = m2*m2
	distance = math.sqrt(m1+m2)
	return distance < radius

def insideEllipse(xSrc, ySrc, xCenter, yCenter, xRadius, yRadius):
	import math
	
	if xRadius == 0 or yRadius == 0:		
		return 0
	
	d1 = xSrc-xCenter
	m1 = d1*d1
	d2 = ySrc-yCenter
	m2 = d2*d2
	distance = math.sqrt(m1+m2)
	if d1 == 0:
		return 1
	angle = math.atan(float(d2)/d1)
	if d1 == 0:
		if d1 > 0:
			angle = math.pi/2
		else:
			angle = -math.pi/2
		
	m1 = xRadius*math.sin(angle)
	m1 = m1*m1
	m2 = yRadius*math.cos(angle)
	m2 = m2*m2
	er = float(xRadius*yRadius)/math.sqrt(m1+m2)
	
	return distance < er
	
def insidePoly(xSrc, ySrc, xyList):
		
	if len(xyList) < 6 or len(xyList)%2 != 0:
		print 'Warning: inside: not a polygon'
		return 0
		
	xOrigSeg, yOrigSeg  = __changeRepere(xSrc, ySrc, xyList[0], xyList[1])
	if xOrigSeg < 0:
		areaOrig = A_L
	# right
	else:
		areaOrig = A_R

	rotInd = 0
	indPoint = 2
	while indPoint < len(xyList)+2:
		if indPoint < len(xyList):
			xDestSeg, yDestSeg  = __changeRepere(xSrc, ySrc, xyList[indPoint], xyList[indPoint+1])
		else:
			xDestSeg, yDestSeg  = __changeRepere(xSrc, ySrc, xyList[0], xyList[1])
		
		if xDestSeg < 0:
			areaDest = A_L
		# right
		else:
			areaDest = A_R

		a, b = __getCoeffSeg(xOrigSeg, yOrigSeg, xDestSeg, yDestSeg)

		if areaOrig == areaDest:
			pass
	
		if b >= 0:
			if areaOrig == A_L:
				if areaDest == A_R:
					rotInd = rotInd+1					
			elif areaDest == A_L:
				rotInd = rotInd-1

		# print 'rotInd=',rotInd
		# next segment
		xOrigSeg, yOrigSeg  = xDestSeg, yDestSeg
		areaOrig = areaDest
		indPoint = indPoint+2
							
	return rotInd != 0
		

# FOR TEST
#try:
#	print insidePoly( 0.5, 2, [0,1,1,3,3,3,1,2,3,1]) # return : 1
#	print insidePoly( 3, 5, [2,3,9,8,2,8,9,3])       # return : 0
#	print insidePoly( 5, 7, [2,3,9,8,2,8,9,3])	 # return : 1
#except:
#	print sys.exc_type, sys.exc_value	
#sys.stdin.read(1)
