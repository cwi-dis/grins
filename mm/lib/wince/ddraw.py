
# ddraw interface

error = 'error'


def CreateSurface(wnd, w, h):
	return DirectDrawSurface(wnd, w, h)

class DirectDrawSurface:
	def __init__(self, wnd, w, h):
		pass

	def BltFill(self, rc, color):
		pass

	def Blt(self, rc_dest, dds, rc_src, flags=None):
		pass

	def BltBlend(self, dds_dest, dds_src, value):
		pass

	def GetDC(self):
		return None

	def ReleasetDC(self, dc):
		return None

	def SetColorKey(self, color):
		pass

	def GetSize(self):
		return 100, 100