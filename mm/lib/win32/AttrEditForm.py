__version__ = "$Id$"


""" @win32doc|AttrEditForm

"""

import string
# std win32 modules
import win32ui,win32con,win32api
Sdk=win32ui.GetWin32Sdk()

# win32 lib modules
import win32mu,components,sysmetrics

# std mfc windows stuf
from pywin.mfc import window,object,docview,dialog
import afxres,commctrl

# GRiNS resource ids
import grinsRC

# App constants
import appcon
from win32mu import Point,Size,Rect # shorcuts
from appcon import UNIT_MM, UNIT_SCREEN, UNIT_PXL

error = 'lib.win32.AttrEditForm.error'

##################################################
# AttrEditor as a tab-dialog

class AttrCtrl:
	want_colon_after_label = 1
	want_default_help = 1

	def __init__(self,wnd,attr,resid):
		self._wnd=wnd
		self._attr=attr
		self._resid=resid
		self._initctrl=None

	def sethelp(self):
		if not self._initctrl: return
		if not hasattr(self._wnd,'_attrinfo'): return
		infoc=self._wnd._attrinfo
		a=self._attr
		hd=a.gethelpdata()
		if hd[1] and self.want_default_help:
			infoc.settext("%s (leave empty for %s)"%(hd[2], hd[1]))
		else:
			infoc.settext(hd[2])
	
	def getcurrent(self):
		return self._attr.getcurrent()

	def drawOn(self,dc):
		pass

	def enableApply(self):
		if not self._wnd._form: return
		if self._attr.getcurrent()!=self.getvalue():
			flag=1
		else:
			flag=0	
		self._wnd._form.enableApply(self._attr, flag)

# temp stuff not safe
def atoft(str):
	# convert string into tuple of floats
	return tuple(map(string.atof, string.split(str)))

def fttoa(t,n,prec):
	if not t or len(t) != n:
		return ''
	return ((' %%.%df' % prec) * n) % t

##################################
class OptionsCtrl(AttrCtrl):
	want_default_help = 0

	def __init__(self,wnd,attr,resid):
		AttrCtrl.__init__(self,wnd,attr,resid)
		self._attrname=components.Edit(wnd,resid[0])
		self._options=components.ComboBox(wnd,resid[1])

	def OnInitCtrl(self):
		self._initctrl=self
		self._attrname.attach_to_parent()
		self._options.attach_to_parent()
		label = self._attr.getlabel()
		if self.want_colon_after_label:
			label = label + ':'
		self._attrname.settext(label)
		list = self._attr.getoptions()
		val = self._attr.getcurrent()
		self.setoptions(list,val)
		self._wnd.HookCommand(self.OnCombo,self._resid[1])
	
	def setoptions(self,list,val):
		if val not in list:
			val = list[0]
		ix=list.index(val)
		if self._initctrl:
			self._options.resetcontent()
			self._options.setoptions(list)
			self._options.setcursel(ix)
		
	def setvalue(self, val):
		if not self._initctrl: return
		list = self._attr.getoptions()
		if val not in list:
			raise error, 'value not in list'
		ix=list.index(val)
		self._options.setcursel(ix)

	def getvalue(self):
		if self._initctrl:
			return self._options.getvalue() 
		return self._attr.getcurrent()

	def OnReset(self,id,code):
		if self._attr:
			self._attr.reset_callback()

	def OnCombo(self,id,code):
		self.sethelp()
		if code==win32con.CBN_SELCHANGE:
			self.enableApply()

class ChannelCtrl(OptionsCtrl):
	def OnInitCtrl(self):
		OptionsCtrl.OnInitCtrl(self)
		self._wnd.HookCommand(self.OnChannel,self._resid[2])

	def OnChannel(self,id,code):
		if self._attr:
			self._attr.channelprops()

class OptionsRadioCtrl(AttrCtrl):
	want_default_help = 0

	def __init__(self,wnd,attr,resid):
		AttrCtrl.__init__(self,wnd,attr,resid)
		self._attrname=components.Control(wnd,resid[0])
		n = len(self._attr.getoptions())
		self._radio=[]
		for ix in range(n):
			self._radio.append(components.RadioButton(wnd,resid[ix+1]))

	def OnInitCtrl(self):
		self._initctrl=self
		self._attrname.attach_to_parent()
		label = self._attr.getlabel()
		if self.want_colon_after_label:
			label = label + ':'
		self._attrname.settext(label)
		list = self._attr.getoptions()
		n = len(list)
		for ix in range(n):
			self._radio[ix].attach_to_parent()
			self._radio[ix].hookcommand(self._wnd,self.OnRadio)
		val = self._attr.getcurrent()
		self.setoptions(list,val)
	
	def setoptions(self,list,val):
		if val not in list:
			val = list[0]
		if self._initctrl:
			for i in range(len(list)):
				self._radio[i].settext(list[i])
				self._radio[i].setcheck(0)
			ix=list.index(val)
			self._radio[ix].setcheck(1)
		
	def setvalue(self, val):
		if not self._initctrl: return
		list = self._attr.getoptions()
		if val not in list:
			val = list[0]
		ix=list.index(val)
		for i in range(len(list)):
			self._radio[i].setcheck(0)
		self._radio[ix].setcheck(1)

	def getvalue(self):
		if self._initctrl:
			list = self._attr.getoptions()
			for ix in range(len(list)):
				if self._radio[ix].getcheck():
					return list[ix]	
		return self._attr.getcurrent()

	def OnReset(self,id,code):
		if self._attr:
			self._attr.reset_callback()
		
	def OnRadio(self,id,code):
		self.sethelp()
		if code==win32con.BN_CLICKED:
			self.enableApply()

class OptionsCheckCtrl(AttrCtrl):
	want_default_help = 0

	def __init__(self,wnd,attr,resid):
		AttrCtrl.__init__(self,wnd,attr,resid)
		self._attrname=components.Control(wnd,resid[0])
		n = len(self._attr.getoptions())
		self._check=[]
		for ix in range(n):
			self._check.append(components.CheckButton(wnd,resid[ix+1]))

	def OnInitCtrl(self):
		self._initctrl=self
		self._attrname.attach_to_parent()
		label = self._attr.getlabel()
		if self.want_colon_after_label:
			label = label + ':'
		self._attrname.settext(label)
		list = self._attr.getoptions()
		n = len(list)
		for ix in range(n):
			self._check[ix].attach_to_parent()
			self._check[ix].hookcommand(self._wnd,self.OnCheck)
		val = self._attr.getcurrent()
		self.setoptions(list,val)
	
	def setoptions(self,list,val):
		vals = string.split(val, ',')
		if self._initctrl:
			for i in range(len(list)):
				self._check[i].settext(list[i])
				self._check[i].setcheck(0)
			for val in vals:
				try:
					ix=list.index(val)
				except ValueError:
					pass
				else:
					self._check[ix].setcheck(1)
		
	def setvalue(self, val):
		if not self._initctrl:
			return
		list = self._attr.getoptions()
		if val not in list:
			val = list[0]
		ix=list.index(val)
		self._check[ix].setcheck(not self._check[ix].getcheck())

	def getvalue(self):
		if self._initctrl:
			list = self._attr.getoptions()
			values = []
			for ix in range(len(list)):
				if self._check[ix].getcheck():
					values.append(list[ix])
			return string.join(values, ',')
		return self._attr.getcurrent()

	def OnReset(self,id,code):
		if self._attr:
			self._attr.reset_callback()

	def OnCheck(self,id,code):
		self.sethelp()
		if code==win32con.BN_CLICKED:
			self.enableApply()

##################################
class FileCtrl(AttrCtrl):
	def __init__(self,wnd,attr,resid):
		AttrCtrl.__init__(self,wnd,attr,resid)
		self._attrname=components.Edit(wnd,resid[0])
		self._attrval=components.Edit(wnd,resid[1])

	def OnInitCtrl(self):
		self._initctrl=self
		self._attrname.attach_to_parent()
		self._attrval.attach_to_parent()
		label = self._attr.getlabel()
		if self.want_colon_after_label:
			label = label + ':'
		self._attrname.settext(label)
		self._attrval.settext(self._attr.getcurrent())
		self._wnd.HookCommand(self.OnEdit,self._resid[1])
		self._wnd.HookCommand(self.OnBrowse,self._resid[2])

	def setvalue(self, val):
		if self._initctrl:
			self._attrval.settext(val)
	def getvalue(self):
		if self._initctrl:
			return self._attrval.gettext()
		return self._attr.getcurrent()

	def OnBrowse(self,id,code):
		self._attr.browser_callback()

	def OnReset(self,id,code):
		if self._attr:self._attr.reset_callback()

	def OnEdit(self,id,code):
		if code==win32con.EN_SETFOCUS:
			self.sethelp()
		elif code==win32con.EN_CHANGE:
			if hasattr(self._wnd,'onAttrChange'):
				self._wnd.onAttrChange()
				self.enableApply()

# a file ctrl with icon buttons play and stop
# indented for continous media preview
class FileMediaCtrl(FileCtrl):
	def __init__(self,wnd,attr,resid):
		FileCtrl.__init__(self,wnd,attr,resid)
		self._iconplay=win32ui.GetApp().LoadIcon(grinsRC.IDI_PLAY)
		self._iconstop=win32ui.GetApp().LoadIcon(grinsRC.IDI_STOP)
		self._bplay=components.Button(wnd,resid[3])
		self._bstop=components.Button(wnd,resid[4])

	def OnInitCtrl(self):
		FileCtrl.OnInitCtrl(self)
		self._bplay.attach_to_parent()
		self._bstop.attach_to_parent()
		self._bplay.seticon(self._iconplay)
		self._bstop.seticon(self._iconstop)
		self._wnd.HookCommand(self.OnPlay,self._resid[3])
		self._wnd.HookCommand(self.OnStop,self._resid[4])

	def OnPlay(self,id,code):
		if hasattr(self._wnd,'OnPlay'):
			self._wnd.OnPlay()

	def OnStop(self,id,code):
		if hasattr(self._wnd,'OnStop'):
			self._wnd.OnStop()
	

	
##################################
class ColorCtrl(AttrCtrl):
	def __init__(self,wnd,attr,resid):
		AttrCtrl.__init__(self,wnd,attr,resid)
		self._attrname=components.Edit(wnd,resid[0])
		self._attrval=components.Edit(wnd,resid[1])

	def OnInitCtrl(self):
		self._initctrl=self
		self._attrname.attach_to_parent()
		self._attrval.attach_to_parent()
		label = self._attr.getlabel()
		if self.want_colon_after_label:
			label = label + ':'
		self._attrname.settext(label)
		self._attrval.settext(self._attr.getcurrent())
		self._wnd.HookCommand(self.OnEdit,self._resid[1])
		self._wnd.HookCommand(self.OnBrowse,self._resid[2])
		self.calcIndicatorRC()

	def calcIndicatorRC(self):
		place='edit'
		pos='bottom'
		l,t,r,b=self._wnd.GetWindowRect()
		if place=='button':
			s=components.Control(self._wnd,self._resid[2])
			s.attach_to_parent()
			lc,tc,rc,bc=s.getwindowrect()
		else:
			lc,tc,rc,bc=self._attrval.getwindowrect()
		if pos=='top':
			self._indicatorRC=(lc-l,tc-t-12,lc-l+rc-lc,tc-t-4)
		else:
			self._indicatorRC=(lc-l,bc-t+4,lc-l+rc-lc,bc-t+16)

	def drawOn(self,dc):
		rc=self._indicatorRC
		ct=self.getdispcolor()
		dc.FillSolidRect(rc, win32mu.RGB(ct))
		br=Sdk.CreateBrush(win32con.BS_SOLID,0,0)	
		dc.FrameRectFromHandle(rc,br)
		Sdk.DeleteObject(br)

	def invalidateInd(self):
		self._wnd.InvalidateRect(self._indicatorRC)

	def setvalue(self, val):
		if self._initctrl:
			self._attrval.settext(val)
			self.invalidateInd()

	def getvalue(self):
		if self._initctrl:
			return self._attrval.gettext()
		return self._attr.getcurrent()

	def OnReset(self,id,code):
		if self._attr:self._attr.reset_callback()

	def getdispcolor(self):
		colorstring = self._attrval.gettext()
		from colors import colors
		if colors.has_key(colorstring):
			return colors[colorstring]
		list = string.split(string.strip(colorstring))
		r = g = b = 0
		if len(list) == 3:
			try:
				r = string.atoi(list[0])
				g = string.atoi(list[1])
				b = string.atoi(list[2])
			except ValueError:
				pass
		return (r,g,b)

	def OnBrowse(self,id,code):
		if not self._initctrl: return
		r,g,b=self.getdispcolor()
		rv = self.ColorSelect(r, g, b)
		if rv != None:
			colorstring = "%d %d %d"%rv
			self._attrval.settext(colorstring)
			self.invalidateInd()
	
	def ColorSelect(self, r, g, b):
		dlg = win32ui.CreateColorDialog(win32api.RGB(r,g,b),win32con.CC_ANYCOLOR,self._wnd)
		if dlg.DoModal() == win32con.IDOK:
			newcol = dlg.GetColor()
			r, g, b = win32ui.GetWin32Sdk().GetRGBValues(newcol)
			return r, g, b
		return None

	def OnEdit(self,id,code):
		if code==win32con.EN_SETFOCUS:
			self.sethelp()
		elif code==win32con.EN_CHANGE:
			self.invalidateInd()
			self.enableApply()


##################################
class StringCtrl(AttrCtrl):
	def __init__(self,wnd,attr,resid):
		AttrCtrl.__init__(self,wnd,attr,resid)
		self._attrname=components.Edit(wnd,resid[0])
		self._attrval=components.Edit(wnd,resid[1])

	def OnInitCtrl(self):
		self._initctrl=self
		self._attrname.attach_to_parent()
		self._attrval.attach_to_parent()
		label = self._attr.getlabel()
		if self.want_colon_after_label:
			label = label + ':'
		self._attrname.settext(label)
		self.setvalue(self._attr.getcurrent())
		self._wnd.HookCommand(self.OnEdit,self._resid[1])

	def setvalue(self, val):
		if self._initctrl:
			val = string.join(string.split(val, '\n'), '\r\n')
			self._attrval.settext(val)

	def getvalue(self):
		if not self._initctrl:
			return self._attr.getcurrent()
		val = self._attrval.gettext()
		return string.join(string.split(val, '\r\n'), '\n')

	def OnReset(self,id,code):
		if self._attr:
			self._attr.reset_callback()

	def OnEdit(self,id,code):
		if code==win32con.EN_SETFOCUS:
			self.sethelp()
		elif code==win32con.EN_CHANGE:
			self.enableApply()

class TupleCtrl(AttrCtrl):
	def __init__(self,wnd,attr,resid):
		AttrCtrl.__init__(self,wnd,attr,resid)
		self._attrname=components.Edit(wnd,resid[0])
		self._nedit=len(resid)-1
		self._attrval=[]
		for i in range(self._nedit):
			self._attrval.append(components.Edit(wnd,resid[i+1]))

	def OnInitCtrl(self):
		self._initctrl=self
		self._attrname.attach_to_parent()
		label = self._attr.getlabel()
		if self.want_colon_after_label:
			label = label + ':'
		self._attrname.settext(label)
		for i in range(self._nedit):		
			self._attrval[i].attach_to_parent()
		strxy=self._attr.getcurrent()
		self.setvalue(strxy)
		for i in range(self._nedit):
			self._attrval[i].hookcommand(self._wnd,self.OnEdit)

	def setvalue(self, val):
		if self._initctrl:
			t=self.atoi_tuple(val)
			st=self.dtuple2stuple(t,self._nedit)
			default = string.split(self._attr.getdefault())
			for i in range(self._nedit):
				self._attrval[i].settext(st[i] or default[i])

	def getvalue(self):
		if not self._initctrl:
			return self._attr.getcurrent()
		default = string.split(self._attr.getdefault())
		st=[]
		for i in range(self._nedit):
			st.append(self._attrval[i].gettext() or default[i])
		return string.join(st)

	def OnReset(self,id,code):
		if self._attr:
			self._attr.reset_callback()

	def OnEdit(self,id,code):
		if code==win32con.EN_SETFOCUS:
			self.sethelp()
		elif code==win32con.EN_CHANGE:
			self.enableApply()
	
class IntTupleCtrl(TupleCtrl):
	def setvalue(self, val):
		if self._initctrl:
			st = string.split(val)
			if len(st) != self._nedit:
				st = string.split(self._attr.getdefault())
			for i in range(self._nedit):
				# this checks that the strings are all ints
				s = '%d' % string.atoi(st[i])
				self._attrval[i].settext(s)

class FloatTupleCtrl(TupleCtrl):
	def setvalue(self, val):
		if self._initctrl:
			st = string.split(val)
			if len(st) != self._nedit:
				st = string.split(self._attr.getdefault())
			for i in range(self._nedit):
				# this checks that the strings are all floats
				# and also normalizes them
				if st[i]:
					try:
						s = '%.2f' % string.atof(st[i])
					except string.atof_error:
						s = ''
					else:
						if s[-3:] == '.00':
							# remove trailing .00
							s = s[:-3]
				else:
					s = st[i]
				self._attrval[i].settext(s)
	
##################################
class AttrSheet(dialog.PropertySheet):
	def __init__(self,form):
		self._form=form
		import __main__
		dll=__main__.resdll
		dialog.PropertySheet.__init__(self,grinsRC.IDR_GRINSED,dll)
		self.HookMessage(self.onInitDialog,win32con.WM_INITDIALOG)
		self._apply=components.Button(self,afxres.ID_APPLY_NOW)

	def onInitDialog(self,params):
		self.HookCommand(self.onApply,afxres.ID_APPLY_NOW)
		self.HookCommand(self.onOK,win32con.IDOK)
		self.HookCommand(self.onCancel,win32con.IDCANCEL)
		self._apply.attach_to_parent()

	def onApply(self,id,code): 
		self._form.call('Apply')
		self.enableApply(0)

	def onOK(self,id,code): 
		self._form.call('OK')

	def onCancel(self,id,code):
		self._form.call('Cancel')

	def enableApply(self,flag):
		if self._apply:
			self._apply.enable(flag)
		
		
class AttrPage(dialog.PropertyPage):
	def __init__(self,form):
		self._form=form
		self._cd={}
		self._group=None
		self._tabix=-1
		self._title='Untitled page'
		self._initdialog=None
		self._attrinfo=components.Static(self,grinsRC.IDC_ATTR_INFO)
		
	def do_init(self):
		id=self.getpageresid()
		self.createctrls()
		import __main__
		dll=__main__.resdll
		dialog.PropertyPage.__init__(self,id,dll,grinsRC.IDR_GRINSED)
		
	def OnInitDialog(self):
		self._initdialog=self
		dialog.PropertyPage.OnInitDialog(self)
		self._attrinfo.attach_to_parent()
		for ctrl in self._cd.values():ctrl.OnInitCtrl()
		if self._group:
			self._group.oninitdialog(self)
		
	def OnPaint(self):
		dc, paintStruct = self.BeginPaint()
		self.drawOn(dc)
		self.EndPaint(paintStruct)

	def drawOn(self,dc):
		for ctrl in self._cd.values():
			ctrl.drawOn(dc)
						
	def setvalue(self, attr, val):
		if self._cd.has_key(attr): 
			self._cd[attr].setvalue(val)
	def getvalue(self, attr):
		if self._cd.has_key(attr):
			return self._cd[attr].getvalue()
	def setoptions(self,attr, list,val):
		if self._cd.has_key(attr):
			self._cd[attr].setoptions(list,val)
	
	def setgroup(self,group):
		self._group=group
	

	# override for not group attributes
	def createctrls(self):
		if not self._group:
			raise error, 'you must override createctrls for page',self
			return
		self._title=self._group.gettitle()
		self._cd=self._group.createctrls(self)
	
	# override for not group pages
	def getpageresid(self):
		if not self._group:
			raise error,'you must override getpageresid for page',self
			return -1
		return self._group.getpageresid() 

	def getctrl(self,aname):
		for a in self._cd.keys():
			if a.getname()==aname:
				return self._cd[a]
		return None

	def settabix(self,ix):
		self._tabix=ix
	def settabtext(self,tabctrl):
		if self._tabix<0:
			raise error,'tab index is uninitialized'
		tabctrl.SetItemText(self._tabix,self._title)

# On some pages we don't want the colon after the attribute name,
# because we put the attribute name on the groupbox, not before the editable
# field. These classes are there specifically to override this behaviour
# of adding a colon to the attribute name
class OptionsRadioNocolonCtrl(OptionsRadioCtrl):
	want_colon_after_label = 0

class OptionsCheckNocolonCtrl(OptionsCheckCtrl):
	want_colon_after_label = 0

class StringNocolonCtrl(StringCtrl):
	want_colon_after_label = 0

###############################	
class SingleAttrPage(AttrPage):
	# These map attribute names to (dialog-resource-id, constructor-function, control-ids)
	# tuples. For unknown attributes we default to "string".
	# The fact that we also have a mapping by name (in stead of by type
	# only) means we can have special-case dialogs for Windows while
	# the code will continue to work (with a boring popup menu)
	# for the other platforms.
	CTRLMAP_BYNAME = {
		'layout':		# Two radio buttons
			(grinsRC.IDD_EDITATTR_R2,
			 OptionsRadioNocolonCtrl,
			 (grinsRC.IDC_1,grinsRC.IDC_2,grinsRC.IDC_3)),
		'aspect':		# Two radio buttons
			(grinsRC.IDD_EDITATTR_R2,
			 OptionsRadioNocolonCtrl,
			 (grinsRC.IDC_1,grinsRC.IDC_2,grinsRC.IDC_3)),
		'visible':		# Three radio buttons
			(grinsRC.IDD_EDITATTR_R3,
			 OptionsRadioNocolonCtrl,
			 (grinsRC.IDC_1,grinsRC.IDC_2,grinsRC.IDC_3,grinsRC.IDC_4)),
		'drawbox':		# Three radio buttons
			(grinsRC.IDD_EDITATTR_R3,
			 OptionsRadioNocolonCtrl,
			 (grinsRC.IDC_1,grinsRC.IDC_2,grinsRC.IDC_3,grinsRC.IDC_4)),
		'popup':		# Three radio buttons
			(grinsRC.IDD_EDITATTR_R3,
			 OptionsRadioNocolonCtrl,
			 (grinsRC.IDC_1,grinsRC.IDC_2,grinsRC.IDC_3,grinsRC.IDC_4)),
		'transparent':	# Four radio buttons
			(grinsRC.IDD_EDITATTR_R4,
			 OptionsRadioNocolonCtrl,
			 (grinsRC.IDC_1,grinsRC.IDC_2,grinsRC.IDC_3,grinsRC.IDC_4,grinsRC.IDC_5)),
		'project_audiotype':	# Four radio buttons
			(grinsRC.IDD_EDITATTR_R4,
			 OptionsRadioNocolonCtrl,
			 (grinsRC.IDC_1,grinsRC.IDC_2,grinsRC.IDC_3,grinsRC.IDC_4,grinsRC.IDC_5)),
		'project_videotype':	# Four radio buttons
			(grinsRC.IDD_EDITATTR_R4,
			 OptionsRadioNocolonCtrl,
			 (grinsRC.IDC_1,grinsRC.IDC_2,grinsRC.IDC_3,grinsRC.IDC_4,grinsRC.IDC_5)),
		'project_targets':	# Six check buttons
			(grinsRC.IDD_EDITATTR_C6,
			 OptionsCheckNocolonCtrl,
			 (grinsRC.IDC_1,grinsRC.IDC_CHECK1,grinsRC.IDC_CHECK2,grinsRC.IDC_CHECK3,grinsRC.IDC_CHECK4,grinsRC.IDC_CHECK5,
			  grinsRC.IDC_CHECK6)),
		}
	CTRLMAP_BYTYPE = {
		'option':		# An option selected from a list (as a popup menu)
			(grinsRC.IDD_EDITATTR_O1,
			 OptionsCtrl,
			 (grinsRC.IDC_1,grinsRC.IDC_2)),
		'file':			# A file, with optional preview area
			(grinsRC.IDD_EDITATTR_F1,
			 FileCtrl,
			 (grinsRC.IDC_1,grinsRC.IDC_2,grinsRC.IDC_3)),
		'color':		# A color, with a color picker
			(grinsRC.IDD_EDITATTR_C1,
			 ColorCtrl,
			 (grinsRC.IDC_1,grinsRC.IDC_2,grinsRC.IDC_3)),
		'string':		# Default: a simple string field
			(grinsRC.IDD_EDITATTR_S1,
			 StringCtrl,
			 (grinsRC.IDC_11,grinsRC.IDC_12)),
		'text':
			(grinsRC.IDD_EDITATTR_E1,
			 StringNocolonCtrl,
			 (grinsRC.IDC_11,grinsRC.IDC_12)),
		}

	def __init__(self,form,attr):
		AttrPage.__init__(self,form)
		self._attr=attr

	def OnInitDialog(self):
		AttrPage.OnInitDialog(self)
		ctrl=self._cd[self._attr]
		ctrl.OnInitCtrl()
		ctrl.sethelp()

	def _getcontrolinfo(self):
		n = self._attr.getname()
		t = self._attr.gettype()
		if self.CTRLMAP_BYNAME.has_key(n):
			return self.CTRLMAP_BYNAME[n]
		if self.CTRLMAP_BYTYPE.has_key(t):
			return self.CTRLMAP_BYTYPE[t]
		return self.CTRLMAP_BYTYPE['string']

	def createctrls(self):
		a=self._attr
		self._title=a.getlabel()
		dialogresid, constructor, controlresids = self._getcontrolinfo()
		self._cd[a] = constructor(self, a, controlresids)

	def getpageresid(self):
		dialogresid, constructor, controlresids = self._getcontrolinfo()
		return dialogresid

##################################
class LayoutScale:
	def __init__(self, wnd, xs, ys, offset = (0,0)):
		self._wnd=wnd
		self._xscale=xs
		self._yscale=ys
		self._offset = offset
		
	# rc is a win32mu.Rect in pixels
	# return coord string in units
	def orgrect_str(self, rc, units):
		str_units=''
		if units == UNIT_PXL:
			scaledrc=self.scaleCoord(rc)
			box = scaledrc.tuple_ps()
			box = box[0]-self._offset[0], \
			      box[1]-self._offset[1], \
			      box[2], box[3]
			s='(%.0f,%.0f,%.0f,%.0f)' %  box
		elif units == UNIT_SCREEN:
			s='(%.2f,%.2f,%.2f,%.2f)' %  self._wnd.inverse_coordinates(rc.tuple_ps(),units=units)
		else:
			str_units='mm'
			scaledrc=self.scaleCoord(rc)
			s='(%.1f,%.1f,%.1f,%.1f)' % self._wnd.inverse_coordinates(scaledrc.tuple_ps(),units=units)
		return s, str_units

	# rc is a win32mu.Rect in pixels
	# we return box=(x,y,w,h) in units (in arg)
	def orgrect(self, rc, units):
		if units == UNIT_PXL:
			scaledrc=self.scaleCoord(rc)
			return scaledrc.tuple_ps()
		elif units == UNIT_SCREEN:
			return self._wnd.inverse_coordinates(rc.tuple_ps(),units=units)
		else:
			scaledrc=self.scaleCoord(rc)
			return self._wnd.inverse_coordinates(scaledrc.tuple_ps(),units=units)


	# box is in units and scaled
	# return original box
	def orgbox(self, box, units):
		if units == UNIT_SCREEN:
			return box
		elif units == UNIT_PXL:
			rc=Rect((box[0],box[1],box[0]+box[2],box[1]+box[3]))
			scaledrc=self.scaleCoord(rc)
			return scaledrc.tuple_ps()
		else:
			rc=Rect((box[0],box[1],box[0]+box[2],box[1]+box[3]))
			scaledrc=self.scaleCoord(rc)
			return scaledrc.tuple_ps()
	

	# box is in units and unscaled
	# return scaled in the same units
	def layoutbox(self,box,units):
		if not box: return box
		if units==UNIT_SCREEN:
			return box
		else:
			x=self._xscale
			y=self._yscale
			if units==UNIT_PXL:
				return (box[0]/x,box[1]/y,box[2]/x,box[3]/y)
			else:
				return (box[0]/x,box[1]/y,box[2]/x,box[3]/y)

	def scaleCoord(self,rc):
		l=rc.left*float(self._xscale)
		t=rc.top*float(self._yscale)
		w=rc.width()*float(self._xscale)
		h=rc.height()*float(self._yscale)
		return Rect((l,t,l+w,t+h))


##################################
# LayoutPage
import cmifwnd, _CmifView
import appcon, sysmetrics
import string
import DrawTk

class LayoutPage(AttrPage,cmifwnd._CmifWnd):
	def __init__(self,form):
		AttrPage.__init__(self,form)
		cmifwnd._CmifWnd.__init__(self)
		self._units=self._form.getunits()
		self._layoutctrl=None
		self._isintscale=1
		self._boxoff = 0, 0
		self._layoutctrl=None
			
	def OnInitDialog(self):
		AttrPage.OnInitDialog(self)
		self.HookMessage(self.onLButtonDown,win32con.WM_LBUTTONDOWN)
		self.HookMessage(self.onLButtonUp,win32con.WM_LBUTTONUP)
		self.HookMessage(self.onMouseMove,win32con.WM_MOUSEMOVE)
		preview=components.Control(self,grinsRC.IDC_PREVIEW)
		preview.attach_to_parent()
		l1,t1,r1,b1=self.GetWindowRect()
		l2,t2,r2,b2=preview.getwindowrect()
		self._layoutpos =(l2-l1,t2-t1)
		self._layoutsize = (r2-l1,b2-t1)
		self.createLayoutContext(self._form._winsize)
		self._layoutctrl=self.createLayoutCtrl()

		t=components.Static(self,grinsRC.IDC_SCALE1)
		t.attach_to_parent()
		if self._isintscale:
			t.settext('scale 1 : %.0f' % self._xscale)
		else:
			t.settext('scale 1 : %.1f' % self._xscale)
		self.create_box(self.getcurrentbox())

	# hack messages! 
	def onLButtonDown(self,params):
		self._layoutctrl._notifyListener('onLButtonDown',params)
		self._layoutctrl._notifyListener('onLButtonUp',params)
	def onLButtonUp(self,params):
		self._layoutctrl._notifyListener('onLButtonUp',params)
	def onMouseMove(self,params):
		pass #self._layoutctrl.notifyListener('onLButtonUp',params)

	def OnSetActive(self):
		if self._layoutctrl and not self._layoutctrl.in_create_box_mode():
			self.create_box(self.getcurrentbox())
		return self._obj_.OnSetActive()

	def OnKillActive(self): 
		return self._obj_.OnKillActive()

	def OnDestroy(self,params):
		if self._layoutctrl:
			self._layoutctrl.exit_create_box()

	def createLayoutCtrl(self):
		v=_CmifView._CmifPlayerView(docview.Document(docview.DocTemplate()))
		v.createWindow(self)
		x,y,w,h=self.getboundingbox()
		dw=2*win32api.GetSystemMetrics(win32con.SM_CXEDGE)
		dh=2*win32api.GetSystemMetrics(win32con.SM_CYEDGE)
		rc=(self._layoutpos[0],self._layoutpos[1],w+dw,h+dh)
		v.init(rc,'Untitled',units=UNIT_PXL)
		v.SetWindowPos(self.GetSafeHwnd(),rc,
			win32con.SWP_NOACTIVATE | win32con.SWP_NOZORDER)
		v.OnInitialUpdate()
		v.ShowWindow(win32con.SW_SHOW)
		v.UpdateWindow()	
		self.init_tk(v)
		return v
	
	def init_tk(self, v):
		v.drawTk.SetLayoutMode(0)
		self._scale=LayoutScale(v,self._xscale,self._yscale,self._boxoff)
		v.drawTk.SetScale(self._scale)

		(x,y,w,h),bunits=self._form.GetBBox()
		rc=(x,y,x+w,y+h)
		rc = v._convert_coordinates(rc, units = bunits)
		rc=self._scale.layoutbox(rc,UNIT_PXL)
		v.drawTk.SetBRect(rc)

		(x,y,w,h),bunits=self._form.GetCBox()
		rc=(x,y,x+w,y+h)
		rc = v._convert_coordinates(rc, units = bunits)
		rc=self._scale.layoutbox(rc,UNIT_PXL)
		v.drawTk.SetCRect(rc)

	def createLayoutContext(self,winsize=None,units=appcon.UNIT_PXL):
		if winsize:
			sw,sh=winsize
		else:
			sw,sh=sysmetrics.scr_width_pxl,sysmetrics.scr_height_pxl
		
		# try first an int scale
		n = max(1, (sw+self._layoutsize[0]-1)/self._layoutsize[0], 
			(sh+self._layoutsize[1]-1)/self._layoutsize[1])
		scale=float(n)
		self._xmax=int(sw/scale+0.5)
		self._ymax=int(sh/scale+0.5)
		self._isintscale=1
		if n!=1 and (self._xmax<3*self._layoutsize[0]/4 or self._ymax<3*self._layoutsize[1]/4):
			# try to find a better scale
			scale = max(1, float(sw)/self._layoutsize[0], float(sh)/self._layoutsize[1])
			self._xmax=int(sw/scale+0.5)
			self._ymax=int(sh/scale+0.5)
			self._isintscale=0
		
		# finally the exact scale:
		self._xscale=float(sw)/self._xmax
		self._yscale=float(sh)/self._ymax
	
	def getboundingbox(self):
		return (0,0,self._xmax,self._ymax)

	def create_box(self,box):
		self._layoutctrl.exit_create_box()
		if box and (box[2]==0 or box[3]==0):box=None
		# call create box against layout control but be modeless and cool!
		modeless=1;cool=1;
		self._layoutctrl.create_box('',self.update,box,self._units,modeless,cool)
		self.check_units()

	def check_units(self):
		units=self._form.getunits()
		if units!=self._units:
			self._units=units
			v=self._layoutctrl
			v.drawTk.SetUnits(self._units)
			v.InvalidateRect()
			if v._objects:
				drawObj=v._objects[0]
				rb=v.inverse_coordinates(drawObj._position.tuple_ps(), units = self._units)
				apply(self.update, rb)
				from __main__ import toplevel
				toplevel.settimer(0.1,(self._form._prsht.onApply,(0,0)))

			
	def setvalue(self, attr, val):
		if not self._initdialog: return
		self._cd[attr].setvalue(val)
		if self.islayoutattr(attr):
			self.setvalue2layout(val)
			

	######################
	# subclass overrides

	def getcurrentbox(self):
		lc=self.getctrl('base_winoff')
		val=lc.getcurrent()
		box=self.val2box(val)
		lbox=self._scale.layoutbox(box,self._units)
		return lbox

	def setvalue2layout(self,val):
		box=self.val2box(val)
		lbox=self._scale.layoutbox(box,self._units)
		self.create_box(lbox)
	
	def val2box(self,val):
		if not val:
			box=None
		else:
			lc=self.getctrl('base_winoff')
			box=atoft(val)
		return box
		
	def islayoutattr(self,attr):
		if self._group:
			return self._group.islayoutattr(attr)
		else:
			return 0

	# called back by create_box on every change
	# the user can press reset to cancel changes
	def update(self,*box):
		if self._initdialog:
			lc=self.getctrl('base_winoff')
			if not box:
				lc.setvalue('')
			else:	
				box=self._scale.orgbox(box,self._units)
				if self._units==UNIT_PXL:prec=0
				elif self._units==UNIT_SCREEN:prec=1
				else: prec=2
				a=fttoa(box,4,prec)
				lc.setvalue(a)


class PosSizeLayoutPage(LayoutPage):
	def __init__(self,form):
		LayoutPage.__init__(self,form)
		self._xy=None
		self._wh=None
		ch = form._node.parent.GetChannel()
		if ch.has_key('base_window'):
			self._boxoff = ch.get('base_winoff', (0,0,0,0))[:2]

	def getcurrentbox(self):
		attrnames = self._group._attrnames
		self._xy=self.getctrl(attrnames['xy'])
		self._wh=self.getctrl(attrnames['wh'])
		sxy=self._xy.getcurrent()
		if not sxy:sxy='0 0'
		swh=self._wh.getcurrent()
		if not swh:swh='0 0'
		val = sxy + ' ' + swh
		box=atoft(val)
		box = box[0]+self._boxoff[0], box[1]+self._boxoff[1], box[2], box[3]
		box=self._scale.layoutbox(box,self._units)
		return box

	def setvalue2layout(self,val):
		sxy=self._xy.getvalue()
		if not sxy:sxy='0 0'
		swh=self._wh.getvalue()
		if not swh:swh='0 0'
		val= sxy + ' ' + swh
		box=atoft(val)
		x, y = self._boxoff
		box = box[0]+x, box[1]+y, box[2], box[3]
		box=self._scale.layoutbox(box,self._units)
		self.create_box(box)

	# called back by create_box on every change
	# the user can press reset to cancel changes
	def update(self,*box):
		if self._initdialog:
			lc=self.getctrl('base_winoff')
			if not box:
				self._xy.setvalue('')
				self._wh.setvalue('')
			else:	
				box=self._scale.orgbox(box,self._units)
				x, y = self._boxoff
				box = box[0]-x, box[1]-y, box[2], box[3]
				if self._units==UNIT_PXL:prec=0
				elif self._units==UNIT_SCREEN:prec=1
				else: prec=2
				axy=fttoa(box[:2],2,prec)
				awh=fttoa(box[2:],2,prec)
				self._xy.setvalue(axy)
				self._wh.setvalue(awh)

############################
# Base class for media renderers

class Renderer:
	def __init__(self,wnd,rc,baseURL=''):
		self._wnd=wnd
		self._rc=rc
		self._baseURL=baseURL
		self._bgcolor=(0,0,0)

	def isstatic(self):
		return 0

	def needswindow(self):
		return 1

	def needsoswindow(self):
		return 0

	def urlqual(self,rurl):
		if not rurl:
			return rurl
		import MMurl
		return MMurl.canonURL(MMurl.basejoin(self._baseURL, rurl))

	def urlretrieve(self,url):
		if not url:return None
		import MMurl
		try:
			f = MMurl.urlretrieve(url)[0]
		except IOError, arg:
			f=None
		return f
	
	def isfile(self,f):
		try:list = win32api.FindFiles(f)
		except:return 0
		if not list or len(list) > 1:return 0
		return 1

	def update(self):
		self._wnd.InvalidateRect(self.inflaterc(self._rc))

	# borrow cmifwnd's _prepare_image but make some adjustments
	def adjustSize(self, size, crop = (0,0,0,0), scale = 0, center = 1):
		rc=win32mu.Rect(self._rc)
		return rc.adjustSize(size,crop,scale,center)

	def inflaterc(self,rc,dl=1,dt=1,dr=1,db=1):
		l,t,r,b=rc
		l=l-dl
		t=t-dt
		r=r+dr
		b=b+db
		return (l,t,r,b)

	def drawcroprect(self, dc, rc):
		if not rc: return
		win32mu.RectanglePath(dc, rc, rop=win32con.R2_NOTXORPEN,\
			pens=win32con.PS_DOT, penw=2, penc=win32api.RGB(0,0,0))		

	# overrides
	def load(self,f):
		pass

	def render(self,dc):
		pass

	def play(self):
		pass

	def pause(self):
		pass

	def stop(self):
		pass

	
###############################
from win32ig import win32ig

class ImageRenderer(Renderer):
	def __init__(self,wnd,rc,baseURL=''):
		Renderer.__init__(self,wnd,rc,baseURL)
		self._ig=-1
		self._adjrc=None
			
	def __del__(self):
		if self._ig>=0:
			win32ig.delete(self._ig)
	
	def isstatic(self):
		return 1

	def load(self,rurl):
		if self._ig>=0:
			win32ig.delete(self._ig)
			self._ig=-1
		if not rurl:
			self.update()
			return

		url=self.urlqual(rurl)
		f=self.urlretrieve(url)
		if not f or not self.isfile(f):
			self.update()
			return
		try:
			self._ig=win32ig.load(f)
		except:
			self._ig=-1
		if self._ig >= 0:
			self._imgsize=win32ig.size(self._ig)
##		else:
##			print 'failed to load',f
		self.update()

	def render(self,dc):
		if self._ig<0: return
		src_x, src_y, dest_x, dest_y, width, height,rcKeep = self.adjustSize(self._imgsize[:2])
		win32ig.render(dc.GetSafeHdc(),self._bgcolor,
			None, self._ig, src_x, src_y,dest_x, dest_y, width, height,rcKeep)
		br=Sdk.CreateBrush(win32con.BS_SOLID,0,0)	
		dc.FrameRectFromHandle((dest_x, dest_y, dest_x + width, dest_y+height),br)
		Sdk.DeleteObject(br)
		self._adjrc=(dest_x, dest_y,dest_x + width, dest_y + height)


#################################
DirectShowSdk=win32ui.GetDS()

class MediaRenderer(Renderer):
	def __init__(self,wnd,rc,baseURL=''):
		Renderer.__init__(self,wnd,rc,baseURL)
		self._builder=None
	
	def __del__(self):
		self.release()
		
	def isstatic(self):
		return 0

	def needswindow(self):
		return 1
			
	def release(self):
		if self._builder:
			self._builder.Stop()
			self._builder.Release()
			self._builder=None

	def load(self,rurl):
		self.release()
		try:
			self._builder = DirectShowSdk.CreateGraphBuilder()
		except:
			self._builder=None

		if not self._builder:
			self.update()
			return
		url=self.urlqual(rurl)
		import MMurl
		url = MMurl.unquote(url)
		if not self._builder.RenderFile(url):
			if self.needswindow():
				self.update()
			return
		if self.needswindow():
			left,top,width,height=self._builder.GetWindowPosition()
			src_x, src_y, dest_x, dest_y, width, height,rcKeep=\
				self.adjustSize((width,height))
			self._builder.SetWindowPosition((dest_x, dest_y, width, height))
			self._builder.SetWindow(self._wnd,win32con.WM_USER+101)
			self.update()
	

	def play(self):
		if not self._builder: return
		d=self._builder.GetDuration()
		t=self._builder.GetPosition()
		if t>=d:
			self._builder.SetPosition(0)
		self._builder.Run()

	def pause(self):
		if not self._builder: return
		self._builder.Pause()
	def stop(self):
		if not self._builder: return
		self._builder.Stop()


class VideoRenderer(MediaRenderer):
	def __init__(self,wnd,rc,baseURL=''):
		MediaRenderer.__init__(self,wnd,rc,baseURL)
	def needswindow(self):
		return 1

class AudioRenderer(MediaRenderer):
	def __init__(self,wnd,rc,baseURL=''):
		MediaRenderer.__init__(self,wnd,rc,baseURL)
	def needswindow(self):
		return 0


#################################
try:
	import rma
except ImportError:
	rma = None

class RealRenderer(Renderer):
	realengine=None
	def __init__(self,wnd,rc,baseURL=''):
		Renderer.__init__(self,wnd,rc,baseURL)
		self._rmaplayer=None
	
	# postpone real loading so that the user pay a delay
	# the first time he wants a real preview and only then
	def do_init(self):
		if rma and not RealRenderer.realengine:
			try:
				 RealRenderer.realengine = rma.CreateEngine()
			except:
				RealRenderer.realengine=None
		if RealRenderer.realengine and not self._rmaplayer:
			try:
				self._rmaplayer = RealRenderer.realengine.CreatePlayer()
			except:
				self._rmaplayer=None
	
	def __del__(self):
		self.release()
			
	def release(self):
		if self._rmaplayer:
			self.stop()
			self._rmaplayer = None

	def isstatic(self):
		return 0

	def load(self,rurl):
		self.do_init()
		if not self._rmaplayer:
			if self.needswindow():
				self.update()
			return
		if self.needswindow():
			self._rmaplayer.SetOsWindow(self._wnd.GetSafeHwnd())
		url=self.urlqual(rurl)
		import MMurl
		url = MMurl.unquote(url)
		self._rmaplayer.OpenURL(url)
		self._wnd.ShowWindow(win32con.SW_SHOW)
			
	def play(self):
		if self._rmaplayer:
			self._rmaplayer.Begin()
			
	def pause(self):
		if self._rmaplayer:
			self._rmaplayer.Pause()

	def stop(self):
		if self._rmaplayer:
			# stop requires to recreate player
			# in order to be confined
			self._rmaplayer.Pause()
			#self._rmaplayer.Seek(0)

class RealWndRenderer(RealRenderer):
	def __init__(self,wnd,rc,baseURL=''):
		RealRenderer.__init__(self,wnd,rc,baseURL)
	def needswindow(self):
		return 1
	def needsoswindow(self):
		return 1

class RealAudioRenderer(RealRenderer):
	def __init__(self,wnd,rc,baseURL=''):
		RealRenderer.__init__(self,wnd,rc,baseURL)
	def needswindow(self):
		return 0

# a ctrl resizeable in a special way for rma
class RealWndCtrl(components.WndCtrl):
	def prepare(self):
		self.HookMessage(self.onSize,win32con.WM_SIZE)
		l,t,r,b=self.GetWindowRect()
		lr,tr,rr,br=self.GetParent().GetWindowRect()
		self._rcref=win32mu.Rect((l-lr,t-tr,r-lr,b-tr))
		self._box=None

	def onSize(self,params):
		if not self._box:
			msg=win32mu.Win32Msg(params)		
			src_x, src_y, dest_x, dest_y, width, height,rcKeep=\
				self._rcref.adjustSize((msg.width(),msg.height()))
			self._box=(dest_x, dest_y, width, height)
		self.SetWindowPos(self.GetSafeHwnd(),self._box,
			win32con.SWP_NOACTIVATE | win32con.SWP_NOZORDER)


#################################

class PreviewPage(AttrPage):
	def __init__(self,form,mrenderer='image',aname='file'):
		AttrPage.__init__(self,form)
		self._prevrc=(20,20,100,100)
		self._aname=aname
		self._armed=0
		self._playing=0
		if mrenderer=='video':
			self._renderer=VideoRenderer(self,self._prevrc,self._form._baseURL)
		elif mrenderer=='audio':
			self._renderer=AudioRenderer(self,self._prevrc,self._form._baseURL)
		elif mrenderer=='realwnd':
			self._renderer=RealWndRenderer(self,self._prevrc,self._form._baseURL)
		elif mrenderer=='realaudio':
			self._renderer=RealAudioRenderer(self,self._prevrc,self._form._baseURL)
		else:
			self._renderer=ImageRenderer(self,self._prevrc,self._form._baseURL)

	def OnInitDialog(self):
		AttrPage.OnInitDialog(self)
		if self._renderer.isstatic():
			if self._renderer.needswindow():
				self.setRendererRc()
			c=self.getctrl(self._aname)
			rurl=string.strip(c.getvalue())
			self._renderer.load(rurl)
			self._armed=1

	def setRendererRc(self):
		preview=RealWndCtrl(self,grinsRC.IDC_PREVIEW)
		preview.attach_to_parent()
		if self._renderer.needsoswindow():
			preview.create_wnd_from_handle()
			preview.prepare()
			self._renderer._wnd=preview
		l1,t1,r1,b1=self.GetWindowRect()
		l2,t2,r2,b2=preview.getwindowrect()
		self._renderer._rc=(l2-l1,t2-t1,r2-l1,b2-t1)

	def OnDestroy(self,params):
		del self._renderer

	def OnSetActive(self):
		if self._playing:
			self._renderer.play()
		return self._obj_.OnSetActive()

	def OnKillActive(self):
		if self._playing:
			self._renderer.pause()
		return self._obj_.OnKillActive()

	def drawOn(self,dc):
		self._renderer.render(dc)
			
	def setvalue(self, attr, val):
		if not self._initdialog: return
		if self._cd.has_key(attr): 
			self._cd[attr].setvalue(val)
		if attr.getname()==self._aname:
			self._renderer.load(string.strip(val))

	def onAttrChange(self):
		if not self._initdialog: return
		c=self.getctrl(self._aname)
		rurl=string.strip(c.getvalue())
		self._renderer.load(rurl)
	
	def OnPlay(self):
		if not self._armed:
			if self._renderer.needswindow():
				self.setRendererRc()
			c=self.getctrl(self._aname)
			rurl=string.strip(c.getvalue())
			self._renderer.load(rurl)
			self._armed=1
		self._renderer.play()
		self._playing=1

	def OnStop(self):
		if self._playing:
			self._renderer.stop()
			self._playing=0

class ImagePreviewPage(PreviewPage):
	def __init__(self,form):
		PreviewPage.__init__(self,form,'image')
	def drawOn(self,dc):
		self._renderer.render(dc)
		rc=self._renderer._adjrc
		a=self._form.getattrbyname('crop')
		if not a: return
		val=a.getvalue()
		# parse a tuple for one more time!
		st = string.split(val)
		if len(st) != 4: return
		l,t,r,b=rc
		l=l+string.atoi(st[0])
		t=t+string.atoi(st[1])
		r=r-string.atoi(st[2])
		b=b-string.atoi(st[3])
		self._renderer.drawcroprect(dc,(l,t,r,b))

class VideoPreviewPage(PreviewPage):
	def __init__(self,form):
		PreviewPage.__init__(self,form,'video')	

class AudioPreviewPage(PreviewPage):
	def __init__(self,form):
		PreviewPage.__init__(self,form,'audio')	

class RealAudioPreviewPage(PreviewPage):
	def __init__(self,form):
		PreviewPage.__init__(self,form,'realaudio')	

class RealWndPreviewPage(PreviewPage):
	def __init__(self,form):
		PreviewPage.__init__(self,form,'realwnd')	

############################

from Attrgrs import attrgrs

attrgrsdict={}
for d in attrgrs:
	attrgrsdict[d['name']]=d


############################
# platform and implementation dependent group
# one per group
class AttrGroup:
	def __init__(self,data):
		self._data=data
		self._al=[]

	# decision interface (may be platform independent)
	def visit(self,al):
		# we want the list of attributes in al that occur in self._data['attrs'],
		# and we want it in the order of self._data['attrs'].
		attrs = self._data['attrs']
		# create a list of tuples of index into self._data['attrs'] plus element in al
		list = []
		for a in al:
			name = a.getname()
			if name in attrs:
				list.append((attrs.index(name), a))
		list.sort()
		self._al = []
		for i, a in list:
			self._al.append(a)

	def matches(self):
		if not self._data.has_key('match'):
			return len(self._al)==len(self._data['attrs'])
		if self._data['match']=='part':
			return len(self._al)>1
		elif self._data['match']=='first':
			fa=	self._data['attrs'][0]
			return (fa in self.alnames())
		else:
			return len(self._al)==len(self._data['attrs'])

	def alnames(self):
		l=[]
		for a in self._al:
			l.append(a.getname())
		return l
	def getattr(self,aname):
		for a in self._al:
			if a.getname()==aname:
				return a
		return None

	def gettitle(self):
		return self._data['title']

	def islayoutattr(self,attr):
		return 0

	def getpageclass(self):
		return AttrPage

	# auto create
	# override for special cases
	def createctrls(self,wnd):
		cd={}
		for ix in range(len(self._al)):
			a=self._al[ix]
			CtrlCl=self.getctrlclass(a)
			cd[a]=CtrlCl(wnd,a,self.getctrlids(ix+1))
		return cd

	special_attrcl={
		'system_captions':OptionsRadioCtrl,
		'system_overdub_or_caption':OptionsRadioCtrl,
		'layout':OptionsRadioCtrl,
		'visible':OptionsRadioCtrl,
		'drawbox':OptionsRadioCtrl,
		}

	def getctrlclass(self,a):
		n = a.getname()
		if AttrGroup.special_attrcl.has_key(n):
			return AttrGroup.special_attrcl[n]
		t = a.gettype()
		if t=='option':return OptionsCtrl
		elif t=='file': return FileCtrl
		elif t=='color': return ColorCtrl
		else: return StringCtrl
	
	# part of page initialization
	# do whatever not default
	def oninitdialog(self,wnd):
		pass
	
class StringGroup(AttrGroup):
	data = None
	def __init__(self,data = None):
		AttrGroup.__init__(self,data or self.data)

	def createctrls(self,wnd):
		cd={}
		for ix in range(len(self._al)):
			a=self._al[ix]
			cd[a]=StringCtrl(wnd,a,self.getctrlids(ix+1))
		return cd

	def getctrlids(self,ix):
		return getattr(grinsRC, 'IDC_%d' % (ix*10+1)), \
			   getattr(grinsRC, 'IDC_%d' % (ix*10+2))

	def getpageresid(self):
		return getattr(grinsRC, 'IDD_EDITATTR_S%d' % len(self._al))

	def oninitdialog(self,wnd):
		ctrl=components.Control(wnd,grinsRC.IDC_GROUP1)
		ctrl.attach_to_parent()
		ctrl.settext(self._data['title'])

class InfoGroup(StringGroup):
	data=attrgrsdict['infogroup']

class WebserverGroup(StringGroup):
	data=attrgrsdict['webserver']

class MediaserverGroup(StringGroup):
	data=attrgrsdict['mediaserver']

class DurationGroup(StringGroup):
	data=attrgrsdict['timing1']

class Duration2Group(StringGroup):
	data=attrgrsdict['timing2']

class DurationParGroup(AttrGroup):
	data=attrgrsdict['timingpar']

	def __init__(self):
		AttrGroup.__init__(self, self.data)

	def createctrls(self,wnd):
		cd={}
		for ix in range(len(self._al)):
			a=self._al[ix]
			if ix == 3:
				cd[a]=OptionsCtrl(wnd,a,(grinsRC.IDC_41,grinsRC.IDC_42))
			else:
				cd[a]=StringCtrl(wnd,a,self.getctrlids(ix+1))
		return cd

	def getctrlids(self,ix):
		return getattr(grinsRC, 'IDC_%d' % (ix*10+1)), \
			   getattr(grinsRC, 'IDC_%d' % (ix*10+2))

	def getpageresid(self):
		return getattr(grinsRC, 'IDD_EDITATTR_S%d' % len(self._al))

	def oninitdialog(self,wnd):
		ctrl=components.Control(wnd,grinsRC.IDC_GROUP1)
		ctrl.attach_to_parent()
		ctrl.settext(self._data['title'])
	def getpageresid(self):
		return grinsRC.IDD_EDITATTR_P4


# base_winoff
class LayoutGroup(AttrGroup):
	data=attrgrsdict['base_winoff']
	def __init__(self,data=None):
		if data:
			AttrGroup.__init__(self,data)
		else:
			AttrGroup.__init__(self,LayoutGroup.data)

	def getpageresid(self):
		return grinsRC.IDD_EDITATTR_LS1

	def createctrls(self,wnd):
		cd={}
		a=self.getattr('base_winoff')
		cd[a]=FloatTupleCtrl(wnd,a,(grinsRC.IDC_11,grinsRC.IDC_12,grinsRC.IDC_13,grinsRC.IDC_14,grinsRC.IDC_15))
		return cd

	def getpageclass(self):
		return LayoutPage

	def islayoutattr(self,attr):
		return (attr.getname()=='base_winoff')

# base_winoff, units
class LayoutGroupWithUnits(LayoutGroup):
	data=attrgrsdict['base_winoff_and_units']
	def __init__(self):
		LayoutGroup.__init__(self,LayoutGroupWithUnits.data)
	def getpageresid(self):
		return grinsRC.IDD_EDITATTR_LS1O1

	def createctrls(self,wnd):
		cd={}
		a=self.getattr('base_winoff')
		cd[a]=FloatTupleCtrl(wnd,a,(grinsRC.IDC_11,grinsRC.IDC_12,grinsRC.IDC_13,grinsRC.IDC_14,grinsRC.IDC_15))
		a=self.getattr('units')
		cd[a]=OptionsCtrl(wnd,a,(grinsRC.IDC_21,grinsRC.IDC_22))
		return cd

class SubregionGroup(AttrGroup):
	data=attrgrsdict['subregion']
	_attrnames = {'xy':'subregionxy',
		      'wh':'subregionwh',
		      'full':'displayfull',
		      'anchor':'subregionanchor'}

	def __init__(self):
		AttrGroup.__init__(self,self.data)

	def getpageresid(self):
		return grinsRC.IDD_EDITATTR_LS1O2

	def createctrls(self,wnd):
		cd={}
		a=self.getattr(self._attrnames['xy'])
		cd[a]=FloatTupleCtrl(wnd,a,(grinsRC.IDC_11,grinsRC.IDC_12,grinsRC.IDC_13))
		a=self.getattr(self._attrnames['wh'])
		cd[a]=FloatTupleCtrl(wnd,a,(grinsRC.IDC_11,grinsRC.IDC_14,grinsRC.IDC_15))
		a=self.getattr(self._attrnames['full'])
		cd[a]=OptionsRadioCtrl(wnd,a,(grinsRC.IDC_21,grinsRC.IDC_22,grinsRC.IDC_23))		
		a=self.getattr(self._attrnames['anchor'])
		cd[a]=OptionsCtrl(wnd,a,(grinsRC.IDC_31,grinsRC.IDC_32))		
		return cd

	def oninitdialog(self,wnd):
		ctrl=components.Control(wnd,grinsRC.IDC_11)
		ctrl.attach_to_parent()
		ctrl.settext(self._data['title'])

	def getpageclass(self):
		return PosSizeLayoutPage

	def islayoutattr(self,attr):
		return (attr.getname()==self._attrnames['xy']) or (attr.getname()==self._attrnames['wh'])

class ImgregionGroup(SubregionGroup):
	data=attrgrsdict['imgregion']
	_attrnames = {'xy':'imgcropxy',
		      'wh':'imgcropwh',
		      'full':'fullimage',
		      'anchor':'imgcropanchor'}

class SystemGroup(AttrGroup):
	data=attrgrsdict['system']
	def __init__(self):
		AttrGroup.__init__(self,self.data)

	def getpageresid(self):
		return grinsRC.IDD_EDITATTR_S1R3S5

	def getctrlids(self,ix):
		if ix == 2 or ix == 4:
			ids = getattr(grinsRC, 'IDC_%d' % (ix*10+1)),\
				getattr(grinsRC, 'IDC_%d' % (ix*10+2)),\
				getattr(grinsRC, 'IDC_%d' % (ix*10+3)),\
				getattr(grinsRC, 'IDC_%d' % (ix*10+4))
		else:
			ids = getattr(grinsRC, 'IDC_%d' % (ix*10+1)),\
					getattr(grinsRC, 'IDC_%d' % (ix*10+2))
		return ids

	def getpageclass(self):
		return AttrPage

class PreferencesGroup(SystemGroup):
	data=attrgrsdict['preferences']

	def getpageresid(self):
		return grinsRC.IDD_EDITATTR_S1R3S4

class NameGroup(AttrGroup):
	data=attrgrsdict['name']
	def __init__(self):
		AttrGroup.__init__(self,self.data)
	def getpageresid(self):
		return grinsRC.IDD_EDITATTR_S1O1C
	def getctrlids(self,ix):
		val = getattr(grinsRC, 'IDC_%d' % (ix*10+1)), \
		      getattr(grinsRC, 'IDC_%d' % (ix*10+2))
		if self._al[ix-1].getname() == 'channel':
			val = val + (getattr(grinsRC, 'IDC_%d' % (ix*10+3)),)
		return val
	def getpageclass(self):
		return AttrPage

	def getctrlclass(self,a):
		if a.getname() == 'channel':
			return ChannelCtrl
		return AttrGroup.getctrlclass(self,a)


class CNameGroup(NameGroup):
	data=attrgrsdict['.cname']
	def getpageresid(self):
		return grinsRC.IDD_EDITATTR_S1O1

class INameGroup(NameGroup):
	data=attrgrsdict['intname']
	def getpageresid(self):
		return grinsRC.IDD_EDITATTR_S1O2

class FileGroup(AttrGroup):
	data=attrgrsdict['file']
	def __init__(self):
		AttrGroup.__init__(self,FileGroup.data)
		self._preview=-1

	def canpreview(self):
		if self._preview>=0: 
			return self._preview
		self._preview=0 # init to no preview
		a=self.getattr('file')
		f=a.getcurrent()
		import mimetypes
		mtype = mimetypes.guess_type(f)[0]
		if mtype is None: 
			return 0
		mtype, subtype = string.split(mtype, '/')
		# create media type sig for renderer
		if mtype=='image':
			if string.find(subtype,'realpix')>=0:
				mtype='realwnd'
			self._preview=1
		elif mtype=='video':
			if string.find(subtype,'realvideo')>=0:
				mtype='realwnd'
			self._preview=1
		elif mtype=='audio':
			if string.find(subtype,'realaudio')>=0:
				mtype='realaudio'
			self._preview=1
		elif mtype=='text' and string.find(subtype,'realtext')>=0:
			self._preview=1
			mtype='realwnd'
		self._mtypesig=mtype
		return self._preview

	def getpageresid(self):
		if self.canpreview():
			if self._mtypesig=='image': 
				# static media
				return getattr(grinsRC, 'IDD_EDITATTR_PF1')
			else: 
				# continous media i.e play,stop
				return getattr(grinsRC, 'IDD_EDITATTR_MF1')	
		else:
			return getattr(grinsRC, 'IDD_EDITATTR_F1')

	def getpageclass(self):
		if not self.canpreview():
			return AttrPage
		if self._mtypesig=='image':
			return ImagePreviewPage
		elif self._mtypesig=='video':
			return VideoPreviewPage
		elif self._mtypesig=='audio':
			return AudioPreviewPage
		elif self._mtypesig=='realwnd':
			return RealWndPreviewPage
		elif self._mtypesig=='realaudio':
			return RealAudioPreviewPage
		else:
			return AttrPage

	def createctrls(self,wnd):
		cd={}
		a=self.getattr('file')
		if not self.canpreview():
			cd[a]=FileCtrl(wnd,a,(grinsRC.IDC_1,grinsRC.IDC_2,grinsRC.IDC_3))

		elif self._mtypesig=='image':
			# static media
			cd[a]=FileCtrl(wnd,a,(grinsRC.IDC_1,grinsRC.IDC_2,grinsRC.IDC_3))

		else:
			# continous media
			cd[a]=FileMediaCtrl(wnd,a,(grinsRC.IDC_1,grinsRC.IDC_2,grinsRC.IDC_3,
				grinsRC.IDC_4,grinsRC.IDC_5))
		return	cd


class FadeoutGroup(AttrGroup):
	data=attrgrsdict['fadeout']

	def __init__(self):
		AttrGroup.__init__(self,self.data)

	def getpageresid(self):
		return grinsRC.IDD_EDITATTR_FO1

	def createctrls(self,wnd):
		cd = {}
		a = self.getattr('fadeout')
		cd[a] = OptionsRadioCtrl(wnd,a,(grinsRC.IDC_11,grinsRC.IDC_12,grinsRC.IDC_13))
		a = self.getattr('fadeoutcolor')
		cd[a] = ColorCtrl(wnd,a,(grinsRC.IDC_21,grinsRC.IDC_22,grinsRC.IDC_23))
		a = self.getattr('fadeouttime')
		cd[a] = StringCtrl(wnd,a,(grinsRC.IDC_31,grinsRC.IDC_32))
		a = self.getattr('fadeoutduration')
		cd[a] = StringCtrl(wnd,a,(grinsRC.IDC_41,grinsRC.IDC_42))
		return cd

##	def oninitdialog(self,wnd):
##		ctrl=components.Control(wnd,grinsRC.IDC_GROUP1)
##		ctrl.attach_to_parent()
##		ctrl.settext(self._data['title'])

class WipeGroup(AttrGroup):
	data=attrgrsdict['wipe']

	def __init__(self):
		AttrGroup.__init__(self,self.data)

	def getpageresid(self):
		return grinsRC.IDD_EDITATTR_R24

	def createctrls(self,wnd):
		cd = {}
		a = self.getattr('wipetype')
		cd[a] = OptionsRadioNocolonCtrl(wnd,a,(grinsRC.IDC_11,grinsRC.IDC_12,grinsRC.IDC_13))
		a = self.getattr('direction')
		cd[a] = OptionsRadioNocolonCtrl(wnd,a,(grinsRC.IDC_21,grinsRC.IDC_22,grinsRC.IDC_23,grinsRC.IDC_24,grinsRC.IDC_25))
		return cd

############################
# platform dependent association
# what we have implemented, anything else goes as singleton
groupsui={
	'infogroup':InfoGroup,

	'base_winoff':LayoutGroup,
	'base_winoff_and_units':LayoutGroupWithUnits,
	'subregion':SubregionGroup,
	'imgregion':ImgregionGroup,

	'system':SystemGroup,
	'preferences':PreferencesGroup,
	'name':NameGroup,
	'.cname':CNameGroup,
	'intname':INameGroup,

	'timing1':DurationGroup,
	'timing2':Duration2Group,
	'timingpar':DurationParGroup,
	'webserver':WebserverGroup,
	'mediaserver':MediaserverGroup,
	'file':FileGroup,
	'fadeout':FadeoutGroup,
	'wipe':WipeGroup,
	}


###########################
from  GenFormView import GenFormView

class AttrEditForm(GenFormView):
	# class variables to store user preferences
	# None
	# Class constructor. Calls base constructor and nullify members
	def __init__(self,doc):
		GenFormView.__init__(self,doc,grinsRC.IDD_EDITATTR_SHEET)	
		self._title='Properties'
		self._attriblist=None
		self._cbdict=None
		self._initattr=None
		self._prsht=None;
		self._a2p={}
		self._pages=[]
		self._tid=None
		self._attrchanged={}

	# Creates the actual OS window
	def createWindow(self,parent):
		self._parent=parent
		import __main__
		dll=__main__.resdll
		prsht=AttrSheet(self)
		prsht.EnableStackedTabs(1)

		self.buildcontext()

		grattrl=[] # list of attr in groups (may be all)
		# create groups pages
		grattrl=self.creategrouppages()
		
		# create singletons not desrciped by groups
		for i in range(len(self._attriblist)):
			a=self._attriblist[i]
			if a not in grattrl:
				page=SingleAttrPage(self,a)
				self._a2p[a]=page
				self._pages.append(page)

		# init pages
		for page in self._pages:
			page.do_init()

		# add pages to the sheet in the correct group order
		l=self._pages
		self._pages=[]
		ix=0
		initindex = 0
		for i in range(len(self._attriblist)):
			a=self._attriblist[i]
			p=self._a2p[a]
			if p in l:
				p.settabix(ix)
				ix=ix+1
				self._pages.append(p)
				prsht.AddPage(p)
				l.remove(p)
		if self._initattr:
			p = self._a2p.get(self._initattr)
			if p:
				initindex = self._pages.index(p)
		self._initattr = None

		self.CreateWindow(parent)
		prsht.CreateWindow(self,win32con.DS_CONTEXTHELP | win32con.DS_SETFONT | win32con.WS_CHILD | win32con.WS_VISIBLE)
		self.HookMessage(self.onSize,win32con.WM_SIZE)		
		rc=self.GetWindowRect()
		prsht.SetWindowPos(0,(0,0,0,0),
			win32con.SWP_NOACTIVATE | win32con.SWP_NOSIZE)
		self._prsht=prsht

		tabctrl=prsht.GetTabCtrl()
		for page in self._pages:
			page.settabtext(tabctrl)

		prsht.SetActivePage(self._pages[initindex])
		prsht.RedrawWindow()

	def getcurattr(self):
		page = self._prsht.GetActivePage()
		if page:
			group = page._group
			if group:
				return group._al[0]
			else:
				return page._attr
		return None

	def setcurattr(self, attr):
		if not attr:
			return
		p = self._a2p.get(attr)
		if not p:
			return
		self._prsht.SetActivePage(p)

	def creategrouppages(self):
		grattrl=[]	 # all attr in groups
		l=self._attriblist[:]
		for grdict in attrgrs:
			grname=grdict['name']
			if not groupsui.has_key(grname): continue
			group=groupsui[grname]()
			group.visit(l)
			if group.matches():
				PageCl=group.getpageclass()
				grouppage=PageCl(self)
				self._pages.append(grouppage)
				grouppage.setgroup(group)
				for a in group._al:
					self._a2p[a]=grouppage
					grattrl.append(a)
					l.remove(a)
		return grattrl

	# XXX: either the help string (default value for units) must be corrected 
	#      or the attrdict.get calls in Channel.py and LayoutView.py and here
	def getunits(self,ch=None):
		if not ch:
			return self._channel.attrdict.get('units',appcon.UNIT_SCREEN)
		else:
			return ch.attrdict.get('units',appcon.UNIT_SCREEN)
			
	def buildcontext(self):
		self._channels={}
		self._channels_rc={}

		self._winsize=None
		self._layoutch=None
		
		a=self._attriblist[0]
		if hasattr(a.wrapper, 'toplevel') and a.wrapper.toplevel:
			channels = a.wrapper.toplevel.root.context.channels
			self._baseURL=a.wrapper.context.baseurl
			for ch in channels:
				self._channels[ch.name]=ch
				units=self.getunits(ch)
				t=ch.attrdict['type']
				if t=='layout' and ch.attrdict.has_key('winsize'):
					w,h=ch.attrdict['winsize']
					self._winsize=(w,h)
					self._channels_rc[ch.name]=((0,0,w,h),units)
					self._layoutch=ch
				elif ch.attrdict.has_key('base_winoff'):
					self._channels_rc[ch.name]=(ch.attrdict['base_winoff'],units)
				else:
					self._channels_rc[ch.name]=((0,0,0,0),0)
			
		if hasattr(a.wrapper,'node'):
			self._node=a.wrapper.node
			chname=self.getchannel(self._node)
			self._channel=self._channels[chname]
		else:
			self._node=None		

		if hasattr(a.wrapper,'channel'):
			self._channel=a.wrapper.channel

	
	def getchannel(self,node):
		if node.attrdict.has_key('channel'):
			return node.attrdict['channel']
		while node.parent:
			node=node.parent
			if node.attrdict.has_key('channel'):
				return node.attrdict['channel']
		return self._layoutch.name

	def GetBBox(self):
		if self._node:
			return self._channels_rc[self._channel.name]
		else:
			bw=self._channel.attrdict['base_window']
			return self._channels_rc[bw]

	def GetCBox(self):
		bw=self._channel.attrdict['base_window']
		return self._channels_rc[bw]
					
	def OnInitialUpdate(self):
		GenFormView.OnInitialUpdate(self)
		
	def onSize(self,params):
		msg=win32mu.Win32Msg(params)
		if msg.minimized(): return
		if not self._parent or not self._parent._obj_:return
		if not self._prsht or not self._prsht._obj_:return
		rc=self._prsht.GetWindowRect()
		frc=self._parent.CalcWindowRect(rc)
		mainframe=self._parent.GetMDIFrame()
		frc=mainframe.ScreenToClient(frc)
		rc=self._parent.GetWindowRect()
		rc=mainframe.ScreenToClient(rc)
#		frc=(30,4,frc[2]-frc[0]+36,frc[3]-frc[1]+4)
		dw=2*win32api.GetSystemMetrics(win32con.SM_CXEDGE)
		dh=2*win32api.GetSystemMetrics(win32con.SM_CYEDGE)
		frc=(rc[0],rc[1]%8,frc[2]-frc[0]+rc[0]+dw,frc[3]-frc[1] + rc[1]%8)
		self._parent.MoveWindow(frc) 

	# Called when the view is activated 
	def activate(self):
		pass

	# Called when the view is deactivated 
	def deactivate(self):
		pass

	# cmif general interface
	# Called by the core system to close this window
	def close(self):
		if hasattr(self,'GetParent'):
			self.GetParent().DestroyWindow()

	# Called by the core system to set the title of this window
	def settitle(self,title):
		self._title=title
		if hasattr(self,'GetParent'):
			if self.GetParent().GetSafeHwnd():
				self.GetParent().SetWindowText(title)

	# Called by the core system to show this window
	def show(self):
		self.pop() # for now

	# Called by the core system to bring to front this window
	def pop(self):
		childframe=self.GetParent()
		childframe.ShowWindow(win32con.SW_SHOW)
		frame=childframe.GetMDIFrame()
		frame.MDIActivate(childframe)

	# Called by the core system to hide this window
	def hide(self):
		self.ShowWindow(win32con.SW_HIDE)

	# Part of the closing mechanism
	# the parent frame delegates the responcibility to us
	def OnClose(self):
		self.call('Cancel')

	# Helper to call a callback given its string id
	def call(self,k):
		d=self._cbdict
		if d and d.has_key(k) and d[k]:
			apply(apply,d[k])				

	def getattrbyname(self,name):
		for a in self._attriblist:
			if a.getname()==name:
				return a
		return None

	def enableApply(self, attr, flag):
		if flag!=0: 
			self._attrchanged[attr]=1
		else:
			self._attrchanged[attr]=0
		nchanged=0
		for val in self._attrchanged.values():
			nchanged=nchanged+val
		if nchanged>0 and self._prsht:
			self._prsht.enableApply(1)
		elif self._prsht:
			self._prsht.enableApply(0)

	# cmif specific interface
	# Called by the core system to get a value from the list
	def getvalue(self,attrobj):
		if not self._obj_:
			raise error, 'os window not exists'
		if attrobj not in self._attriblist:
			raise error, 'item not in list'
		return self._a2p[attrobj].getvalue(attrobj)

	# Called by the core system to set a value on the list
	def setvalue(self,attrobj,newval):
		if attrobj not in self._attriblist:
			raise error, 'item not in list'
		self._a2p[attrobj].setvalue(attrobj,newval)

		# patch core's draw back
		if not self._tid:
			import __main__
			self._tid=__main__.toplevel.settimer(0.5,(self.onDirty,()))

	# Called by the core system to set attribute options
	def setoptions(self,attrobj,list,val):
		if not self._obj_:
			raise error, 'os window not exists'
		if attrobj not in self._attriblist:
			raise error, 'item not in list'
		t = attrobj.gettype()
		if t != 'option':
			raise error, 'item not an option'
		self._a2p[attrobj].setoptions(attrobj,list,val)

	def onDirty(self):
		self._tid=None
		self.buildcontext()

	def OnDestroy(self,params):
		if self._tid:
			import __main__
			__main__.toplevel.canceltimer(self._tid)
