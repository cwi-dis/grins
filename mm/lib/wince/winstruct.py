__version__ = "$Id$"

def loword(v):
	return v & 0xFFFF

def hiword(v):
	return (v >> 16) & 0xFFFF

def RGB((r, g, b)):
	return (r & 0xFF) | (g & 0xFF) << 8 | (b & 0xFF) << 16

def ltrb(rc):
	return rc[0], rc[1], rc[0] + rc[2], rc[1] + rc[3]

def xywh(rc):
	return rc[0], rc[1], rc[2] - rc[0], rc[3] - rc[1]

class winmsg:
	def __init__(self,params):
		self._hwnd,self._message,self._wParam,self._lParam,self._time,self._pt=params
	def pos(self):
		return loword(self._lParam), hiword(self._lParam)
	def id(self):
		return loword(self._wParam); 


