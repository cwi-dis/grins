
import WMEVENTS
import win32ui, win32con
Sdk=win32ui.GetWin32Sdk()

# add missing const
win32con.MK_ALT = 0x20
from appcon import DROPEFFECT_NONE, DROPEFFECT_COPY, \
	DROPEFFECT_MOVE, DROPEFFECT_LINK, DROPEFFECT_SCROLL

# grins registered clipboard formats
CF_FILE = Sdk.RegisterClipboardFormat('FileName')
CF_NODE = Sdk.RegisterClipboardFormat('Node')
CF_TOOL = Sdk.RegisterClipboardFormat('Tool')
CF_NODEUID = Sdk.RegisterClipboardFormat('NodeUID')
CF_REGION = Sdk.RegisterClipboardFormat('Region')
CF_MEDIA = Sdk.RegisterClipboardFormat('Media')
CF_URL = Sdk.RegisterClipboardFormat('URL')

# map: format_name -> format_id (int)
formats = {'FileName':CF_FILE,
	'Node':CF_NODE,
	'Tool':CF_TOOL,
	'NodeUID':CF_NODEUID,
	'Region':CF_REGION,
	'Media':CF_MEDIA,
	'URL':CF_URL,}

# extract data from data object and return pair (format_name, data) 
# or None when not a grins format
def GetData(dataobj):
	for name, format in formats.items():
		data = dataobj.GetGlobalData(format)
		if data is not None:
			return name, data
	return None


class DropTarget:
	cfmap = {'FileName':CF_FILE}
	def __init__(self):
		self._isregistered=0
		self._dropmap={
			'FileName':(self.dragfile,self.dropfile),
			'URL': (self.dragurl, self.dropurl),
		}

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

	def getClipboardFormat(self,strFmt):
		if DropTarget.cfmap.has_key(strFmt):
			return DropTarget.cfmap[strFmt]
		cf= Sdk.RegisterClipboardFormat(strFmt)
		DropTarget.cfmap[strFmt]=cf
		return cf

	def OnDragEnter(self,dataobj,kbdstate,x,y):
		return self.OnDragOver(dataobj,kbdstate,x,y)

	def OnDragOver(self,dataobj,kbdstate,x,y):
		fmt_name, data = GetData(dataobj)
		callbacks = self._dropmap.get(fmt_name)
		if callbacks:
			dragcb = callbacks[0]
			return dragcb(dataobj, kbdstate, x, y)
		return DROPEFFECT_NONE
				
	def OnDrop(self,dataobj,effect,x,y):
		fmt_name, data = GetData(dataobj)
		callbacks = self._dropmap.get(fmt_name)
		if callbacks:
			dropcb = callbacks[1]
			return dropcb(dataobj, effect, x, y)
		return DROPEFFECT_NONE

	def OnDragLeave(self):
		pass

	def isControlPressed(self, kbdstate):
		return (kbdstate & win32con.MK_CONTROL)!=0
	def isShiftPressed(self, kbdstate):
		return (kbdstate & win32con.MK_SHIFT)!=0
	def isAltPressed(self, kbdstate):
		return (kbdstate & win32con.MK_ALT)!=0

	def dragfile(self,dataobj,kbdstate,x,y):
		filename=dataobj.GetGlobalData(CF_FILE)
		if filename:
			x,y=self._DPtoLP((x,y))
			x,y = self._pxl2rel((x, y),self._canvas)
			return self.onEventEx(WMEVENTS.DragFile,(x, y, filename))
		return 0

	def dropfile(self,dataobj,effect,x,y):
		filename=dataobj.GetGlobalData(CF_FILE)
		if filename:
			import longpath
			filename=longpath.short2longpath(filename)
			x,y=self._DPtoLP((x,y))
			x,y = self._pxl2rel((x, y),self._canvas)
			self.onEvent(WMEVENTS.DropFile,(x, y, filename))
			return 1
		return 0

	def dragurl(self,dataobj,kbdstate,x,y):
		url=dataobj.GetGlobalData(CF_URL)
		if url:
			x,y=self._DPtoLP((x,y))
			x,y = self._pxl2rel((x, y),self._canvas)
			return self.onEventEx(WMEVENTS.DragURL,(x, y, url))
		return 0

	def dropurl(self,dataobj,effect,x,y):
		url=dataobj.GetGlobalData(CF_URL)
		if url:
			x,y=self._DPtoLP((x,y))
			x,y = self._pxl2rel((x, y),self._canvas)
			self.onEvent(WMEVENTS.DropURL,(x, y, url))
			return 1
		return 0
