# std win32 modules
import win32ui,win32con,win32api

# win32 lib modules
import win32mu,components

# std mfc windows stuf
from pywin.mfc import window,object,docview,dialog
import afxres,commctrl

# GRiNS resource ids
import grinsRC

class ControlsDict:
	def __init__(self):
		self._subwnddict={}	
	def __nonzero__(self):return 1
	def __len__(self): return len(self._subwnddict)
	def __getitem__(self, key): return self._subwnddict[key]
	def __setitem__(self, key, item): self._subwnddict[key] = item
	def keys(self): return self._subwnddict.keys()
	def items(self): return self._subwnddict.items()
	def values(self): return self._subwnddict.values()
	def has_key(self, key): return self._subwnddict.has_key(key)

class DlgBar(window.Wnd,ControlsDict):
	AFX_IDW_DIALOGBAR=0xE805
	def __init__(self):
		AFX_IDW_DIALOGBAR=0xE805
		window.Wnd.__init__(self,win32ui.CreateDialogBar())
		ControlsDict.__init__(self)
	def create(self,frame,resid,align=afxres.CBRS_ALIGN_BOTTOM):
		self._obj_.CreateWindow(frame,resid,
			align,self.AFX_IDW_DIALOGBAR)

class ArcInfoForm(DlgBar):
	def __init__(self):
		DlgBar.__init__(self)
		self['Title']=components.Static(self,grinsRC.IDC_STATIC1)	
		self['From']=components.ComboBox(self,grinsRC.IDC_COMBO1)
		self['To']=components.ComboBox(self,grinsRC.IDC_COMBO2)
		self['Delay']=components.Edit(self,grinsRC.IDC_EDIT1)
		self['Cancel']=components.Button(self,win32con.IDCANCEL)
		self['Restore']=components.Button(self,grinsRC.IDUC_RESTORE)
		self['Apply']=components.Button(self,grinsRC.IDUC_APPLY)
		self['OK']=components.Button(self,win32con.IDOK)

	def create(self,frame):
		DlgBar.create(self,frame,grinsRC.IDD_ARC_INFO_BAR,afxres.CBRS_ALIGN_TOP)
		for i in self.keys():
			frame.HookCommand(self.onCmd,self[i]._id)
			self[i].attach_to_parent()
		self.setparams()
		frame.RecalcLayout()

	def onCmd(self,id,code):
		for i in self.keys():
			if id==self[i]._id:
				self[i].callcb()

	#########################################################
	# cmif specific interface
	def close(self):
		frame=self.GetParent()
		self.DestroyWindow()
		frame.RecalcLayout()

	def show(self):
		self.pop() # for now

	def pop(self):
		frame=self.GetParent()
		frame.MDIActivate()

	def hide(self):
		self.close()


	def do_init(self, title, srclist, srcinit, dstlist, dstinit, delay, adornments=None):
		self._title=title
		self._srclist=srclist
		self._srcinit=srcinit
		self._dstlist=dstlist
		self._dstinit=dstinit
		self._delay=delay
		self._adornments=adornments

		cbdict=adornments['callbacks']
		for k in self.keys():
			if k in cbdict.keys():
				self[k].setcb(cbdict[k])

	def setparams(self,params=None):
		self['Title'].settext(self._title)
		self['From'].initoptions(self._srclist,self._srcinit)
		self['To'].initoptions(self._dstlist,self._dstinit)
		self['Delay'].settext('%d' % self._delay)
				
	def settitle(self, title):
		self['Title'].settext(self._title)

	# Interface to the source list.
	def src_setpos(self, pos):
		self['From'].setcursel(pos)

	def src_getpos(self):
		return self['From'].getcursel()

	# Interface to the destination list.
	def dst_setpos(self, pos):
		self['To'].setcursel(pos)

	def dst_getpos(self):
		return self['To'].getcursel()

	# Interface to the delay value.
	def delay_setvalue(self, delay):
		self['Delay'].settext('%d' % self._delay)

	def delay_getvalue(self):
		return float(self['Delay'].gettext())
