
import WMEVENTS, win32con

class DropTarget:
	def __init__(self):
		self._isregistered=0

	def registerDropTarget(self):
		if not self._isregistered:
			if hasattr(self,'RegisterDropTarget'):
				self.RegisterDropTarget()
				print 'RegisterDropTarget',self
			else:
				pass
				#self.DragAcceptFiles(1)
				#self.HookMessage(self.onDropFiles,win32con.WM_DROPFILES)
			self._isregistered=1
		
	def revokeDropTarget(self):
		if self._isregistered:
			if hasattr(self,'RevokeDropTarget'):
				self.RevokeDropTarget()
			else:
				pass #self.DragAcceptFiles(0)
			self._isregistered=0

	def OnDragEnter(self,filename,kbdstate,x,y):
		#print 'OnDragEnter',filename,kbdstate,x,y
		return self.OnDragOver(filename,kbdstate,x,y)

	def OnDragOver(self,filename,kbdstate,x,y):
		x,y=self._DPtoLP((x,y))
		x,y = self._inverse_coordinates((x, y),self._canvas)
		return self.onEventEx(WMEVENTS.DragFile,(x, y, filename))

	def OnDrop(self,filename,effect,x,y):
		print 'OnDrop',filename,effect,x,y
		if filename:
			import longpath
			filename=longpath.short2longpath(filename)
			x,y=self._DPtoLP((x,y))
			x,y = self._inverse_coordinates((x, y),self._canvas)
			self.onEvent(WMEVENTS.DropFile,(x, y, filename))
			return 1
		return 0

	def OnDragLeave(self):
		#print 'OnDragLeave'
		pass
