
import WMEVENTS, win32con

class DropTarget:
	def __init__(self):
		self._isregistered=0
		self._dropmap={'FileName':(self.dragfile,self.dropfile)}

	def registerDropTarget(self):
		if not self._isregistered:
			if hasattr(self,'RegisterDropTarget'):
				self.RegisterDropTarget()
			self._isregistered=1
		
	def revokeDropTarget(self):
		if self._isregistered:
			if hasattr(self,'RevokeDropTarget'):
				self.RevokeDropTarget()
			self._isregistered=0

	def OnDragEnter(self,dataobj,kbdstate,x,y):
		return self.OnDragOver(dataobj,kbdstate,x,y)

	def OnDragOver(self,dataobj,kbdstate,x,y):
		for fmt in self._dropmap.keys():
			cb=	self._dropmap[fmt][0]
			res = cb(dataobj,kbdstate,x,y)
			if res: return res
				
	def OnDrop(self,dataobj,effect,x,y):
		for fmt in self._dropmap.keys():
			cb=	self._dropmap[fmt][1]
			res = cb(dataobj,effect,x,y)
			if res: return res
		return 0

	def OnDragLeave(self):
		pass

	def dragfile(self,dataobj,kbdstate,x,y):
		filename=dataobj.GetGlobalData('FileName')
		if filename:
			x,y=self._DPtoLP((x,y))
			x,y = self._inverse_coordinates((x, y),self._canvas)
			return self.onEventEx(WMEVENTS.DragFile,(x, y, filename))
		return 0

	def dropfile(self,dataobj,effect,x,y):
		filename=dataobj.GetGlobalData('FileName')
		if filename:
			import longpath
			filename=longpath.short2longpath(filename)
			x,y=self._DPtoLP((x,y))
			x,y = self._inverse_coordinates((x, y),self._canvas)
			self.onEvent(WMEVENTS.DropFile,(x, y, filename))
			return 1
		return 0
