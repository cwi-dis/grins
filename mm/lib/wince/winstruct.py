__version__ = "$Id$"

def loword(v):
	return v & 0xFFFF

def hiword(v):
	return (v >> 16) & 0xFFFF

def RGB((r, g, b)):
	return (r & 0xFF) | (g & 0xFF) << 8 | (b & 0xFF) << 16


class winmsg:
	def __init__(self,params):
		self._hwnd,self._message,self._wParam,self._lParam,self._time,self._pt=params
	def pos(self):
		return loword(self._lParam), hiword(self._lParam)
	def id(self):
		return loword(self._wParam); 

def normalize(ltrb):
	l, t, r, b = ltrb	
	return min(l, r), min(b, t), max(l, r), max(b, t)

def ltrb(rc):
	return rc[0], rc[1], rc[0] + rc[2], rc[1] + rc[3]

def xywh(rc):
	return rc[0], rc[1], rc[2] - rc[0], rc[3] - rc[1]

def rectOr(ltrb1, ltrb2):
	l1, t1, r1, b1 = normalize(ltrb1)	
	l2, t2, r2, b2 = normalize(ltrb2)
	return min(l1, l2), min(t1, t2), max(r1, r2), max(b1, b2)

def rectAnd(ltrb1, ltrb2):
	l1, t1, r1, b1 = normalize(ltrb1)	
	l2, t2, r2, b2 = normalize(ltrb2)
	l, r = max(l1, l2), min(r1, r2)
	if l >= r: return None
	t, b = max(t1, t2), min(b1, b2)
	if t >= b: return None
	return l, t, r, b

def rectEqualSize(ltrb1, ltrb2):
	l1, t1, r1, b1 = normalize(ltrb1)	
	l2, t2, r2, b2 = normalize(ltrb2)
	return r1-l1 == r2-l2 and b1-t1 == b2-t2

def inflate(ltrb, dx = 1, dy = 1):
	l, t, r, b = normalize(ltrb)
	return l-dx, t-dy, r+dx, b+dy 

def setorigin(ltrb, pt):
	x, y = pt
	l, t, r, b = normalize(ltrb)
	return l-x, t-y, r-x, b-y 	
