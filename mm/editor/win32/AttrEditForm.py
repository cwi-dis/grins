__version__ = "$Id$"

# @win32doc|AttrEditForm

import string
# std win32 modules
import win32ui,win32con,win32api
Sdk=win32ui.GetWin32Sdk()
Afx=win32ui.GetAfx()

# win32 lib modules
import win32mu,components,sysmetrics
import win32dialog

# std mfc windows stuf
from pywinlib.mfc import window,object,docview,dialog
import afxres,commctrl

# GRiNS resource ids
import grinsRC

# App constants
import appcon
from win32mu import Point,Size,Rect # shorcuts
from appcon import UNIT_MM, UNIT_SCREEN, UNIT_PXL

# input validators
import settings
import features
if settings.user_settings.get('use_input_validators'):
	ENABLE_VALIDATORS = 1
else:
	ENABLE_VALIDATORS = 0

# Other parts of GRiNS.
import EventEditor

error = components.error

##################################################
# AttrEditor as a tab-dialog

class AttrCtrl:
	want_label = 1
	want_colon_after_label = 1
	want_default_help = 1

	def __init__(self,wnd,attr,resid,residToHide=()):
		self._wnd=wnd
		self._attr=attr
		self._resid=resid
		self._initctrl=None
		self._validator=None
		self._listeners=[]
		self._ctrlToHide = []
		for resid in residToHide:
			self._ctrlToHide.append(components.Edit(wnd, resid))

	def getvalue(self):
		raise error, 'you have to implement method \'getvalue\' for %s' % self.__class__.__name__

	def setvalue(self,newval):
		raise error, 'you have to implement method \'setvalue\' for %s' % self.__class__.__name__

	def setoptions(self,list,val):
		raise error, 'you have to implement method \'setoptions\' for %s' % self.__class__.__name__

	def sethelp(self):
		if not self._initctrl: return
		if not hasattr(self._wnd,'_attrinfo'): return
		if not hasattr(self._attr,'wrapper'): return # already closed
		infoc=self._wnd._attrinfo
		help = self.gethelp()
		if help:
			infoc.settext(help)
	
	def getcurrent(self):
		return self._attr.getcurrent()

	def drawOn(self,dc):
		pass

	def enableApply(self,flag=-1):
		if not self._wnd._form: return
		if flag>=0:
			self._wnd._form.enableApply(self._attr, flag)
		else:	
			if self._attr.getcurrent()!=self.getvalue():
				flag=1
			else:
				flag=0	
			self._wnd._form.enableApply(self._attr, flag)

		
	def OnKeyDown(self,params):
		vk = params[2]
		if self._validator:
			return self._validator.onKey(vk,'')
		else:
			return 1

	def OnInitCtrl(self):
		for ctrl in self._ctrlToHide:
			if not self._attr.mustshow():			
				ctrl.attach_to_parent()
				ctrl.hide()
			
	def gethelp(self):
		try:
			hd=self._attr.gethelpdata()
		except:
			if __debug__:
				print 'gethelp on', self._attr, 'failed'
		else:
			# only give default if wanted and not already there
			if hd[1] and self.want_default_help and hd[2].lower().find('default') < 0:
				return "%s (default: %s)"%(hd[2], hd[1])
			else:
				return hd[2]

	def settooltips(self,tooltipctrl):
		pass

	def addlistener(self,obj):
		if hasattr(obj,'onevent'):
			self._listeners.append(obj)

	def notifylisteners(self,event):
		for obj in self._listeners:
			obj.onevent(self._attr, event)

# temp stuff not safe
def atoft(str):
	# convert string into tuple of floats
	try:
		return tuple(map(string.atof, string.split(str)))
	except ValueError:
		return ()

def fttoa(t,n,prec):
	if not t or len(t) != n:
		return ''
	return ((' %%.%df' % prec) * n) % t

##################################
class OptionsCtrl(AttrCtrl):
	want_default_help = 0

	def __init__(self,wnd,attr,resid, residToHide=()):
		AttrCtrl.__init__(self,wnd,attr,resid, residToHide)
		self._attrname=components.Edit(wnd,resid[0])
		self._options=components.ComboBox(wnd,resid[1])

	def OnInitCtrl(self):
		AttrCtrl.OnInitCtrl(self)
		self._initctrl=self
		self._attrname.attach_to_parent()
		self._options.attach_to_parent()
		if self.want_label:
			label = self._attr.getlabel()
			if self.want_colon_after_label:
				label = label + ':'
			self._attrname.settext(label)
		list = self._attr.getoptions()
		val = self._attr.getcurrent()
		self.setoptions(list,val)
		self._wnd.HookCommand(self.OnCombo,self._resid[1])
		if not self._attr.mustshow():
			self._attrname.hide()
			self._options.hide()
	
	def enable(self, enable):
		self._options.enable(enable)

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

	def OnCombo(self,id,code):
		self.sethelp()
		if code==win32con.CBN_SELCHANGE:
			self.enableApply()

	def settooltips(self,tooltipctrl):
		tooltipctrl.AddTool(self._wnd.GetDlgItem(self._resid[1]),self.gethelp(),None,0)

class TransitionCtrl(OptionsCtrl):	
	def OnInitCtrl(self):
		OptionsCtrl.OnInitCtrl(self)
		self._wnd.HookCommand(self.OnTransition,self._resid[2])
		self._properties = components.Button(self._wnd,self._resid[2])
		self._properties.attach_to_parent()
		self.updateproperties()
		if not self._attr.mustshow():
			self._properties.hide()

	def OnTransition(self,id,code):
		if self._attr:
			self._attr.transitionprops()
	
	def OnCombo(self,id,code):
		OptionsCtrl.OnCombo(self,id,code)
		if code==win32con.CBN_SELCHANGE:
			self.updateproperties()
			if hasattr(self._attr, 'optioncb'):
				self._attr.optioncb()

	def updateproperties(self):
		if self._attr and self.hastransitionprops():
			self._properties.enable(1)
		else:
			self._properties.enable(0)

	def hastransitionprops(self):
		if self._attr: 
			return self._attr.wrapper.context.transitions.has_key(self._attr.getvalue())
		return None

	def settooltips(self,tooltipctrl):
		OptionsCtrl.settooltips(self,tooltipctrl)
		tooltipctrl.AddTool(self._wnd.GetDlgItem(self._resid[2]),'Properties of transition',None,0)

class ChannelCtrl(OptionsCtrl):	
	def OnInitCtrl(self):
		OptionsCtrl.OnInitCtrl(self)
		self._wnd.HookCommand(self.OnChannel,self._resid[2])
		self._properties = components.Button(self._wnd,self._resid[2])
		self._properties.attach_to_parent()
		self.updateproperties()
		if not self._attr.mustshow():
			self._properties.hide()

	def OnChannel(self,id,code):
		if self._attr:
			self._attr.channelprops()
	
	def OnCombo(self,id,code):
		OptionsCtrl.OnCombo(self,id,code)
		if code==win32con.CBN_SELCHANGE:
			self.updateproperties()
			if hasattr(self._attr, 'optioncb'):
				self._attr.optioncb()

	def updateproperties(self):
		if self._attr and self.haschannelprops():
			self._properties.enable(1)
		else:
			self._properties.enable(0)

	def haschannelprops(self):
		if self._attr: 
			return self._attr.wrapper.context.getchannel(self._attr.getvalue())
		return None

	def settooltips(self,tooltipctrl):
		OptionsCtrl.settooltips(self,tooltipctrl)
		tooltipctrl.AddTool(self._wnd.GetDlgItem(self._resid[2]),'Properties of channel',None,0)

class ChannelNolabelCtrl(ChannelCtrl):
	want_label = 0

class RegionDefaultCtrl(ChannelCtrl):
	def OnChannel(self,id,code):
		if self._attr:
			self._attr.channelprops()
	
	def haschannelprops(self):
		if self._attr:
			regionName = self._attr.getShowedValue()
			return self._attr.wrapper.context.getchannel(regionName)
		return None

	def settooltips(self,tooltipctrl):
		OptionsCtrl.settooltips(self,tooltipctrl)
		tooltipctrl.AddTool(self._wnd.GetDlgItem(self._resid[2]),'Default region',None,0)

class OptionsRadioCtrl(AttrCtrl):
	want_default_help = 0

	def __init__(self,wnd,attr,resid, residToHide=()):
		AttrCtrl.__init__(self,wnd,attr,resid, residToHide)
		self._attrname=components.Control(wnd,resid[0])
		list = self._attr.getoptions()
		n = len(list)
		self._radio=[]
		if n>len(resid)-1:
			print 'Warning: More options than radio buttons',attr.getname(),n,len(resid)-1,list
			
		for ix in range(len(resid)-1):
			self._radio.append(components.RadioButton(wnd,resid[ix+1]))

	def OnInitCtrl(self):
		AttrCtrl.OnInitCtrl(self)
		self._initctrl=self
		self._attrname.attach_to_parent()
		if self.want_label:
			label = self._attr.getlabel()
			if self.want_colon_after_label:
				label = label + ':'
			self._attrname.settext(label)			
		list = self._attr.getoptions()
		n = len(list)
		n = min(n,len(self._resid)-1)
		for ix in range(n):
			self._radio[ix].attach_to_parent()
			self._radio[ix].hookcommand(self._wnd,self.OnRadio)
		for ix in range(len(list),len(self._resid)-1):
			self._radio[ix].attach_to_parent()
			self._radio[ix].hide()
		val = self._attr.getcurrent()
		self.setoptions(list,val)
		if not self._attr.mustshow():
			self._attrname.hide()
			for rc in self._radio:
				rc.hide()

	
	def enable(self, enable):
		for ctrl in self._radio:
			ctrl.enable(enable)

	def setoptions(self,list,val):
		if val not in list:
			val = list[0]
		if self._initctrl:
			n = len(list)
			n = min(n,len(self._resid)-1)
			for i in range(n):
				if self.want_label:
					self._radio[i].settext(list[i])
				self._radio[i].setcheck(0)
			ix=list.index(val)
			if ix<n:
				self._radio[ix].setcheck(1)
		
	def setvalue(self, val):
		if not self._initctrl: return
		list = self._attr.getoptions()
		if val not in list:
			val = list[0]
		ix=list.index(val)
		n = len(list)
		n = min(n,len(self._resid)-1)
		for i in range(n):
			self._radio[i].setcheck(0)
		self._radio[ix].setcheck(1)

	def getvalue(self):
		if self._initctrl:
			list = self._attr.getoptions()
			n = len(list)
			n = min(n,len(self._resid)-1)
			for ix in range(n):
				if self._radio[ix].getcheck():
					return list[ix]	
		return self._attr.getcurrent()

	def OnRadio(self,id,code):
		self.sethelp()
		if code==win32con.BN_CLICKED:
			self.enableApply()

	def settooltips(self,tooltipctrl):
		list = self._attr.getoptions()
		n = len(list)
		for ix in range(min(n,len(self._resid)-1)):
			tooltipctrl.AddTool(self._wnd.GetDlgItem(self._resid[ix+1]),self.gethelp(),None,0)

class OptionsCheckCtrl(AttrCtrl):
	want_default_help = 0

	def __init__(self,wnd,attr,resid):
		AttrCtrl.__init__(self,wnd,attr,resid)
		self._check = components.CheckButton(wnd, resid[0])

	def OnInitCtrl(self):
		self._initctrl=self
		self._check.attach_to_parent()
		if self.want_label:
			label = self._attr.getlabel()
			self._check.settext(label)			
		self._check.hookcommand(self._wnd,self.OnCheck)
		val = self._attr.getcurrent()
		self._check.setcheck(val=='on')
		if not self._attr.mustshow():
			self._check.hide()

	
	def enable(self, enable):
		self._check.enable(enable)

	def setvalue(self, val):
		if not self._initctrl: return
		self._check.setcheck(val=='on')

	def getvalue(self):
		if self._initctrl:
			return ['off','on'][self._check.getcheck()]
		return self._attr.getcurrent()

	def OnCheck(self,id,code):
		self.sethelp()
		if code==win32con.BN_CLICKED:
			self.enableApply()

	def settooltips(self,tooltipctrl):
		tooltipctrl.AddTool(self._wnd.GetDlgItem(self._resid[0]),self.gethelp(),None,0)

class OptionsCheckMultipleCtrl(AttrCtrl):
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
		if self.want_label:
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
		if not self._attr.mustshow():
			self._attrname.hide()
			for cc in self._check:
				cc.hide()
	
	def enable(self, enable):
		for ctrl in self._check:
			ctrl.enable(enable)

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

	def OnCheck(self,id,code):
		self.sethelp()
		if code==win32con.BN_CLICKED:
			self.enableApply()

	def settooltips(self,tooltipctrl):
		list = self._attr.getoptions()
		n = len(list)
		for ix in range(min(n,len(self._resid)-1)):
			tooltipctrl.AddTool(self._wnd.GetDlgItem(self._resid[ix+1]),self.gethelp(),None,0)

##################################
class FileCtrl(AttrCtrl):
	def __init__(self,wnd,attr,resid):
		AttrCtrl.__init__(self,wnd,attr,resid)
		self._attrname=components.Edit(wnd,resid[0])
		self._attrval=components.Edit(wnd,resid[1])
		self._browser=components.Button(wnd,resid[2])

	def OnInitCtrl(self):
		self._initctrl=self
		self._attrname.attach_to_parent()
		self._attrval.attach_to_parent()
		self._browser.attach_to_parent()
		if self.want_label:
			label = self._attr.getlabel()
			if self.want_colon_after_label:
				label = label + ':'
			self._attrname.settext(label)
		self.setvalue(self._attr.getcurrent())
		self._wnd.HookCommand(self.OnEdit,self._resid[1])
		self._wnd.HookCommand(self.OnBrowse,self._resid[2])
		if not self._attr.mustshow():
			self._attrname.hide()
			self._attrval.hide()
			self._browser.hide()

	def enable(self, enable):
		self._attrval.enable(enable)

	def setvalue(self, val):
		if self._initctrl:
			if val:
				url = self._attr.wrapper.context.findurl(val)
				import urlparse
				scheme, netloc, url, params, query, fragment = urlparse.urlparse(url)
				if not scheme or scheme == 'file':
					import MMurl
					val = MMurl.url2pathname(url)
			self._attrval.settext(val)

	def getvalue(self):
		if not self._initctrl:
			return self._attr.getcurrent()
		val = self._attrval.gettext()
		if '\\' in val:
			import MMurl
			url = MMurl.pathname2url(val)
			val = self._attr.wrapper.context.relativeurl(url)
		return val

	def OnBrowse(self,id,code):
		self._attr.browser_callback()

	def OnEdit(self,id,code):
		if code==win32con.EN_SETFOCUS:
			self.sethelp()
		elif code==win32con.EN_CHANGE:
			if hasattr(self._wnd,'onAttrChange'):
				self._wnd.onAttrChange()
			self.enableApply()

	def settooltips(self,tooltipctrl):
		tooltipctrl.AddTool(self._wnd.GetDlgItem(self._resid[1]),self.gethelp(),None,0)
		tooltipctrl.AddTool(self._wnd.GetDlgItem(self._resid[2]),'Choose File for URL',None,0)

class FileNolabelCtrl(FileCtrl):
	want_label = 0

# a file ctrl with icon buttons play, pause and stop
# indented for continous media preview
class FileMediaCtrl(FileCtrl):
	def __init__(self,wnd,attr,resid):
		FileCtrl.__init__(self,wnd,attr,resid)
		self._iconplay=win32ui.GetApp().LoadIcon(grinsRC.IDI_PLAY)
		self._iconpause=win32ui.GetApp().LoadIcon(grinsRC.IDI_PAUSE)
		self._iconstop=win32ui.GetApp().LoadIcon(grinsRC.IDI_STOP)
		self._bplay=components.Button(wnd,resid[3])
		self._bpause=components.Button(wnd,resid[4])
		self._bstop=components.Button(wnd,resid[5])

	def OnInitCtrl(self):
		FileCtrl.OnInitCtrl(self)
		self._bplay.attach_to_parent()
		self._bpause.attach_to_parent()
		self._bstop.attach_to_parent()
		self._bplay.seticon(self._iconplay)
		self._bpause.seticon(self._iconpause)
		self._bstop.seticon(self._iconstop)
		self._wnd.HookCommand(self.OnPlay,self._resid[3])
		self._wnd.HookCommand(self.OnPause,self._resid[4])
		self._wnd.HookCommand(self.OnStop,self._resid[5])
		self.setstate('stop')
		if not self._attr.mustshow():
			self._bplay.hide()
			self._bpause.hide()
			self._bstop.hide()


	def enable(self, enable):
		FileCtrl.enable(self, enable)
		if enable:
			self.setstate('stop')
		else:
			self.OnStop()
			self._bplay.enable(0)
			self._bpause.enable(0)
			self._bstop.enable(0)

	def OnPlay(self,id,code):
		if hasattr(self._wnd,'OnPlay'):
			self.setstate('play')
			self._wnd.OnPlay()

	def OnPause(self,id,code):
		if hasattr(self._wnd,'OnPause'):
			self.setstate('pause')
			self._wnd.OnPause()

	def OnStop(self,id,code):
		if hasattr(self._wnd,'OnStop'):
			self.setstate('stop')
			self._wnd.OnStop()
	
	def setstate(self,state):
		if state=='stop': # stopped
			self._bplay.enable(1)
			self._bpause.enable(0)
			self._bstop.enable(0)
		elif state=='play': # playing
			self._bplay.enable(0)
			self._bpause.enable(1)
			self._bstop.enable(1)
		elif state=='pause': # pausing
			self._bplay.enable(1)
			self._bpause.enable(0)
			self._bstop.enable(1)

	def settooltips(self,tooltipctrl):
		FileCtrl.settooltips(self,tooltipctrl)
		tooltipctrl.AddTool(self._wnd.GetDlgItem(self._resid[3]),'Play',None,0)
		tooltipctrl.AddTool(self._wnd.GetDlgItem(self._resid[4]),'Pause',None,0)
		tooltipctrl.AddTool(self._wnd.GetDlgItem(self._resid[5]),'Stop',None,0)
			
	
class ElementSelCtrl(AttrCtrl):
	def __init__(self,wnd,attr,resid):
		AttrCtrl.__init__(self,wnd,attr,resid)
		self._attrname=components.Edit(wnd,resid[0])
		self._attrval=components.Edit(wnd,resid[1])

	def OnInitCtrl(self):
		self._initctrl=self
		self._attrname.attach_to_parent()
		self._attrval.attach_to_parent()
		if self.want_label:
			label = self._attr.getlabel()
			if self.want_colon_after_label:
				label = label + ':'
			self._attrname.settext(label)
		self._attrval.settext(self._attr.getcurrent())
		self._wnd.HookCommand(self.OnEdit,self._resid[1])
		self._wnd.HookCommand(self.OnBrowse,self._resid[2])
		self._attrval.enable(0)
		if not self._attr.mustshow():
			self._attrname.hide()
			self._attrval.hide()

	def enable(self, enable):
		self._attrval.enable(enable)

	def setvalue(self, val):
		if self._initctrl:
			self._attrval.enable(1)
			self._attrval.settext(val)
			self._attrval.enable(0)

	def getvalue(self):
		if self._initctrl:
			return self._attrval.gettext()
		return self._attr.getcurrent()

	def OnBrowse(self,id,code):
		parent = self._wnd._form
		mmnode = self._wnd._form._node
		selected = self._attrval.gettext()
		target = self.locateTarget(mmnode, selected)
		dlg = win32dialog.SelectElementDlg(parent, mmnode.GetRoot(), target)
		if dlg.show():
			mmnode.targetnode = dlg.getmmobject()
			id = self.getUID(mmnode.targetnode)
			self.setvalue(id)

	def locateTarget(self, node, name):
		target = node.targetnode
		if not target and name:
			target = node.GetRoot().GetChildByName(name)
			if not target:
				target = node.GetContext().getchannel(name)
		return target

	def getUID(self, node):
		if node is None:
			name = ''
		elif node.getClassName() in ('Region', 'Viewport'):
			name = node.GetUID()
		else:
			name = node.GetRawAttrDef('name', '')
		return name or ''

	def OnEdit(self,id,code):
		if code==win32con.EN_SETFOCUS:
			self.sethelp()
		elif code==win32con.EN_CHANGE:
			if hasattr(self._wnd,'onAttrChange'):
				self._wnd.onAttrChange()
			self.enableApply()

	def settooltips(self,tooltipctrl):
		tooltipctrl.AddTool(self._wnd.GetDlgItem(self._resid[1]),self.gethelp(),None,0)
		tooltipctrl.AddTool(self._wnd.GetDlgItem(self._resid[2]),'Choose target element',None,0)

class ElementSelNolabelCtrl(ElementSelCtrl):
	want_label = 0

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
		if self.want_label:
			label = self._attr.getlabel()
			if self.want_colon_after_label:
				label = label + ':'
			self._attrname.settext(label)
		self._attrval.settext(self._attr.getcurrent())
		self._wnd.HookCommand(self.OnEdit,self._resid[1])
		self._wnd.HookCommand(self.OnBrowse,self._resid[2])
		self.calcIndicatorRC()
		if self._validator:
			self._attrval.hookmessage(self.OnKeyDown,win32con.WM_KEYDOWN)
		if not self._attr.mustshow():
			# XXXX May also need to disable the color well...
			self._attrname.hide()
			self._attrval.hide()

	def enable(self, enable):
		self._attrval.enable(enable)

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
		if ct == None:
			# do not draw when transparent color
			return
		for c in ct:
			if not (0 <= c <= 255):
				return
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

	def getdispcolor(self):
		colorstring = self._attrval.gettext()
		from colors import colors
		if colors.has_key(colorstring):
			return colors[colorstring]
		list = string.split(string.strip(colorstring))
		default = self._attr.getdefaultvalue()
		# this is for CssColorAttrEditorField
		if len(default) == 2 and len(default[1]) == 3:
			default = default[1]
		r, g, b = default
		if len(list) == 3:
			try:
				r = string.atoi(list[0])
				g = string.atoi(list[1])
				b = string.atoi(list[2])
			except ValueError:
				pass
		return (r,g,b)

	def convertcolor(self, rv):
		from colors import rcolors
		if rcolors.has_key(rv):
			return rcolors[rv]
		return "%d %d %d"%rv
				
	def OnBrowse(self,id,code):
		if not self._initctrl: return
		r,g,b=self.getdispcolor()
		rv = self.ColorSelect(r, g, b)
		if rv != None:
			colorstring = self.convertcolor(rv)
			self._attrval.settext(colorstring)
			self.invalidateInd()
	
	def ColorSelect(self, r, g, b):
		dlg = win32ui.CreateColorDialog(win32api.RGB(r,g,b),win32con.CC_ANYCOLOR,self._wnd)
		color_list = self._wnd._form._color_list
		dlg.SetCustomColors(color_list)
		if dlg.DoModal() == win32con.IDOK:
			func = self._wnd._form._cbdict.get('SetCustomColors')
			if func is not None:
				colorlist = dlg.GetSavedCustomColors()
				func(colorlist)
			self._wnd._form._color_list = colorlist
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

	def OnKeyDown(self,params):
		vk = params[2]
		p1,p2=self._attrval.getsel()
		if p1<p2: pos=p1
		else: pos=p2
		if self._validator:
			return self._validator.onKey(vk,self._attrval.gettext(),pos)
		else:
			return 1

	def settooltips(self,tooltipctrl):
		tooltipctrl.AddTool(self._wnd.GetDlgItem(self._resid[1]),self.gethelp(),None,0)
		tooltipctrl.AddTool(self._wnd.GetDlgItem(self._resid[2]),'Pick color from color dialog',None,0)

class CssColorCtrl(ColorCtrl):
	def __init__(self,wnd,attr,resid):
		ColorCtrl.__init__(self, wnd, attr, resid)
		self._radioColor = components.RadioButton(wnd,resid[3])
		self._radioTransparent = components.RadioButton(wnd,resid[4])
		self._radioInherit = components.RadioButton(wnd,resid[5])
		self.currentValue = self._attr.getcurrent()
		self.__setting = 0

	def OnInitCtrl(self):
		self._initctrl=self
		self._attrname.attach_to_parent()
		self._attrval.attach_to_parent()
		self._radioTransparent.attach_to_parent()
		self._radioInherit.attach_to_parent()
		self._radioColor.attach_to_parent()
		if self.want_label:
			label = self._attr.getlabel()
			if self.want_colon_after_label:
				label = label + ':'
			self._attrname.settext(label)

		self.calcIndicatorRC()

		self.setvalue(self.currentValue)		

		self._wnd.HookCommand(self.OnEdit,self._resid[1])
		self._wnd.HookCommand(self.OnBrowse,self._resid[2])
		if self._validator:
			self._attrval.hookmessage(self.OnKeyDown,win32con.WM_KEYDOWN)
			
		self._wnd.HookCommand(self.onColorCheck,self._resid[3])
		self._wnd.HookCommand(self.onTransparentCheck,self._resid[4])
		self._wnd.HookCommand(self.onInheritCheck,self._resid[5])

		if not self._attr.mustshow():
			self._radioColor.hide()
			self._radioTransparent.hide()
			self._radioInherit.hide()

	def setvalue(self, val):
		self.__setting = 1
		self.currentValue = val
		if self._initctrl:
			if val == 'transparent':			
				self.enable(0)
				self._radioTransparent.setcheck(1)
				self._radioInherit.setcheck(0)
				self._radioColor.setcheck(0)
			elif val == 'inherit':
				self.enable(0)
				self._radioInherit.setcheck(1)
				self._radioTransparent.setcheck(0)
				self._radioColor.setcheck(0)
			else:
				self.enable(1)
				self._radioColor.setcheck(1)
				self._radioTransparent.setcheck(0)
				self._radioInherit.setcheck(0)
			self.__updateText()
			self.invalidateInd()
		self.__setting = 0

	def getvalue(self):
		return self.currentValue

	def OnEdit(self,id,code):
		if code==win32con.EN_SETFOCUS:
			self.sethelp()
		elif code==win32con.EN_CHANGE:
			if not self.__setting:
				self.invalidateInd()
				self.currentValue = self._attrval.gettext()
				self.enableApply()

	def getdispcolor(self):
		if self.currentValue in ('','transparent'):
			return None
		if self.currentValue  == 'inherit':
			color = self._attr.getInheritedValue()
		else:
			color = ColorCtrl.getdispcolor(self)
		return color
			
	def OnBrowse(self,id,code):
		if not self._initctrl: return
		dispcolor = self.getdispcolor()
		if dispcolor is None:
			dispcolor = ColorCtrl.getdispcolor(self)
		r, g, b = dispcolor
		rv = self.ColorSelect(r, g, b)
		if rv != None:
			self._radioTransparent.setcheck(0)
			self._radioInherit.setcheck(0)
			self._radioColor.setcheck(1)
			self.enable(1)
			colorstring = self.convertcolor(rv)		
			self._attrval.settext(colorstring)
			self.currentValue = colorstring
			self.invalidateInd()

	def onColorCheck(self, id, code):
		self.enable(1)
		self.currentValue = self._attrval.gettext()
		if self.currentValue == '':
			self.currentValue = 'transparent'
		self.invalidateInd()
		self.enableApply()
		self.sethelp()
		
	def onTransparentCheck(self, id, code):
		self.enable(0)
		self.currentValue = 'transparent'
		self.__updateText()
		self.invalidateInd()
		self.enableApply()
		self.sethelp()

	def onInheritCheck(self, id, code):
		self.enable(0)
		self.currentValue = 'inherit'
		self.__updateText()
		self.invalidateInd()
		self.enableApply()
		self.sethelp()

	def __updateText(self):
		value = self.currentValue
		if value is None or value == 'transparent':
			txt = ''
		elif value == 'inherit':
			color = self._attr.getInheritedValue()
			if color is None:
				txt = ''
			else:
				txt = self.convertcolor(self.getdispcolor())
		else:
			txt = value
		self.__setting = 1
		self._attrval.settext(txt)
		self.__setting = 0

		
	def settooltips(self,tooltipctrl):
		ColorCtrl.settooltips(self, tooltipctrl)
		tooltipctrl.AddTool(self._wnd.GetDlgItem(self._resid[3]),'Non-transparent color',None,0)
		tooltipctrl.AddTool(self._wnd.GetDlgItem(self._resid[4]),self._getTransparentHelp(),None,0)
		tooltipctrl.AddTool(self._wnd.GetDlgItem(self._resid[5]),self._getInheritHelp(),None,0)
		
class NodeCssColorCtrl(CssColorCtrl):

	def _getTransparentHelp(self):
		return 'Transparent (overrides region default)'

	def _getInheritHelp(self):
		return 'Inherit the color from the region'
		
	def gethelp(self):
		if self.currentValue == 'transparent':
			return self._getTransparentHelp()
		elif self.currentValue == 'inherit':
			return self._getInheritHelp()
		return ColorCtrl.gethelp(self) + '  (overrides region default)'

class RegionCssColorCtrl(CssColorCtrl):

	def _getTransparentHelp(self):
		return 'Transparent'

	def _getInheritHelp(self):
		return 'Inherit the color from the parent region'
		
	def gethelp(self):
		if self.currentValue == 'transparent':
			return self._getTransparentHelp()
		elif self.currentValue == 'inherit':
			return self._getInheritHelp()
		return ColorCtrl.gethelp(self)

# Ctrl representing a css pos value
class CssPosCtrl(AttrCtrl):
	def __init__(self,wnd,attr,resid):
		AttrCtrl.__init__(self, wnd, attr, resid)
		self._ctrlValue = components.Edit(wnd,resid[1])
		self._ctrlUnit = components.ComboBox(wnd,resid[2])
		self.currentValue = self._attr.getcurrent()
		self._currentUnit = 'auto'
		self.__fieldModified = 0
		self.__isValueSetting = 0
		self.__lastValue = None
		self.__initPercentValue = None
		
	def OnInitCtrl(self):
		self._initctrl=self
		self._ctrlValue.attach_to_parent()
		self._ctrlUnit.attach_to_parent()

		self._ctrlUnit.resetcontent()
		self._ctrlUnit.setoptions(['auto', 'pixel', 'percent'])
		self.setvalue(self._attr.getcurrent())
		self._wnd.HookCommand(self.OnEdit,self._resid[1])
		self._wnd.HookCommand(self.OnCombo,self._resid[2])

		if not self._attr.mustshow():
			self._ctrlValue.hide()
			self._ctrlUnit.hide()

	
	def enable(self, enable):
		self._ctrlValue.enable(enable)
		self._ctrlUnit.enable(enable)

	# put value into the field. val is the representation of the value
	def setvalue(self, val):
		if not self._initctrl: return
		self.__initPercentValue = None
		if val =='':
			self.__setUnit('auto')
		elif '%' not in val:
			self.__setUnit('pixel')
		else:
			val = val[:-1]
			self.__setUnit('percent')
			self.__initPercentValue = val
		self.__setValue(val)
		self.__fieldModified = 0

	def __setUnit(self, unit):
		self._currentUnit = unit
		if unit == 'auto':
			self._ctrlUnit.setcursel(0)
		elif unit == 'percent':
			self._ctrlUnit.setcursel(2)
		else:
			self._ctrlUnit.setcursel(1)

	def __setValue(self, value):
		self.__isValueSetting = 1
		self._ctrlValue.settext(value)
		self.__isValueSetting = 0
		
	# get value from the field. return a string representation of the value
	def getvalue(self):
		if self._initctrl:
			val = self._ctrlValue.gettext()
			unit = self._ctrlUnit.getvalue()
			if val != '' and unit == 'percent':
				val = val+'%'
			return string.join(string.split(val, '\r\n'), '\n')
				
		return self._attr.getcurrent()

	def OnCombo(self,id,code):
		self.sethelp()
		if code==win32con.CBN_SELCHANGE:
			pSize = self._attr.getParentSize()
			unit = self._ctrlUnit.getvalue()
			if self._currentUnit == unit:
				return
			self.enableApply()
			if unit == 'auto':
				self.__setValue('')
				self._currentUnit = 'auto'
			elif unit == 'pixel':
				if not self.__fieldModified or (self.__lastValue is None and self._currentUnit == 'auto'):
					val = self._attr.getCurrentPxValue()
					value = `val`
					self.__setValue(value)
					self.__lastValue = value
				elif self._currentUnit == 'auto':
					self.__setValue(self.__lastValue)					
				self._currentUnit = 'pixel'
			elif unit == 'percent':
				if not self.__fieldModified or (self.__lastValue is None and self._currentUnit == 'auto'):
					if self.__initPercentValue is not None:
						# keep the initial percent value. Otherwise, the conversion from pixel may be slitly different.
						value = self.__initPercentValue
					else:
						val = self._attr.getCurrentPxValue()
						# convert to float
						val = (float(val)/pSize)*100
						value = fmtfloat(val, prec = 2)
					self.__setValue(value)
					self.__lastValue = value
				elif self._currentUnit == 'auto':
					self.__setValue(self.__lastValue)					
				self._currentUnit = 'percent'

	def OnEdit(self,id,code):
		if code==win32con.EN_SETFOCUS:
			self.sethelp()
		elif code==win32con.EN_CHANGE:
			if self.__isValueSetting:
				return
			val = self._ctrlValue.gettext()
			unit = self._ctrlUnit.getvalue()
			if val == '':
				# force auto value
				self.__setUnit('auto')		
				self.__lastValue = None
			elif unit == 'auto' and val != '':
				# force to pixel value
				self.__setUnit('pixel')		
				self.__lastValue = val
			elif unit == 'pixel' and val[-1] == '%':
				val = val[:-1]
				self.__setValue(val)
				self.__lastValue = val
				# force to percent value
				self.__setUnit('percent')
			elif val[-1] == '%':
				val = val[:-1]
				self.__setValue(val)					
				self.__lastValue = val
			else:
				self.__lastValue = val				
			self.enableApply()
			self.__fieldModified = 1
	
##################################
class StringCtrl(AttrCtrl):
	def __init__(self,wnd,attr, resid, residToHide = ()):
		AttrCtrl.__init__(self,wnd,attr,resid, residToHide)
		self._attrname=components.Edit(wnd,resid[0])
		self._attrval=components.Edit(wnd,resid[1])

	def OnInitCtrl(self):
		AttrCtrl.OnInitCtrl(self)
		self._initctrl=self
		self._attrname.attach_to_parent()
		self._attrval.attach_to_parent()
		if self.want_label:
			label = self._attr.getlabel()
			if self.want_colon_after_label:
				label = label + ':'
			self._attrname.settext(label)
		self.setvalue(self._attr.getcurrent())
		self._wnd.HookCommand(self.OnEdit,self._resid[1])
		if not self._attr.mustshow():
			self._attrname.hide()
			self._attrval.hide()

	def enable(self, enable):
		self._attrval.enable(enable)

	def setvalue(self, val):
		if self._initctrl:
			val = string.join(string.split(val, '\n'), '\r\n')
			self._attrval.settext(val)

	def getvalue(self):
		if not self._initctrl:
			return self._attr.getcurrent()
		val = self._attrval.gettext()
		return string.join(string.split(val, '\r\n'), '\n')

	def OnEdit(self,id,code):
		if code==win32con.EN_SETFOCUS:
			self.sethelp()
		elif code==win32con.EN_CHANGE:
			self.enableApply()

	def settooltips(self,tooltipctrl):
		tooltipctrl.AddTool(self._wnd.GetDlgItem(self._resid[1]),self.gethelp(),None,0)

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
		if self.want_label:
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
		if not self._attr.mustshow():
			self._attrname.hide()
			for ne in self._attrval:
				ne.hide()

	def enable(self, enable):
		for c in self._attrval:
			c.enable(enable)

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
		is_default = 1		# all values are empty
		st=[]
		for i in range(self._nedit):
			v = self._attrval[i].gettext()
			if v:
				is_default = 0
			st.append(v or default[i])
		if is_default:
			return ''
		return string.join(st)

	def OnEdit(self,id,code):
		if code==win32con.EN_SETFOCUS:
			self.sethelp()
		elif code==win32con.EN_CHANGE:
			self.notifylisteners('change')
			self.enableApply()

	def settooltips(self,tooltipctrl):
		for i in range(self._nedit):
			tooltipctrl.AddTool(self._wnd.GetDlgItem(self._resid[i+1]),self.gethelp(),None,0)
	
class IntTupleCtrl(TupleCtrl):
	def setvalue(self, val):
		if self._initctrl:
			st = string.split(val)
			is_default = len(st) != self._nedit
			for i in range(self._nedit):
				# this checks that the strings are all ints
				if is_default:
					s = ''
				else:
					s = '%d' % string.atoi(st[i])
				self._attrval[i].settext(s)

class IntTupleNolabelCtrl(IntTupleCtrl):
	want_label = 0

class SystemScreenSizeCtrl(IntTupleNolabelCtrl):
	def __init__(self,wnd,attr,resid):
		IntTupleCtrl.__init__(self,wnd,attr,resid)
		self.__wlabel = components.Edit(wnd, grinsRC.IDC_WIDTHL)
		self.__hlabel = components.Edit(wnd, grinsRC.IDC_HEIGHTL)

	# in this case, the help doesn't depend only of data, but also of this control.
	# to not affect any other plateform the help is set here
	def OnInitCtrl(self):
		IntTupleCtrl.OnInitCtrl(self)
		self.__wlabel.attach_to_parent()
		self.__hlabel.attach_to_parent()
		if not self._attr.mustshow():
			self.__wlabel.hide()
			self.__hlabel.hide()

	def sethelp(self):
		if not self._initctrl: return
		self._wnd._attrinfo.settext(self.gethelp())

	def gethelp(self):
		return "Play node only if screen bigger or equal than the specified pixel value (leave height and width empty for Not set)"
	
	def setvalue(self, val):
		if not self._initctrl:
			return
		if val == '':
			for i in range(self._nedit):
				self._attrval[i].settext('')
		else:
			IntTupleCtrl.setvalue(self,val)

	def getvalue(self):
		if not self._initctrl:
			return self._attr.getcurrent()
		default = string.split(self._attr.getdefault())
		st=[]
		for i in range(self._nedit):
			st.append(self._attrval[i].gettext())
		strval = string.strip(string.join(st))
		return strval

	def settooltips(self,tooltipctrl):
		for i in range(self._nedit):
			tooltipctrl.AddTool(self._wnd.GetDlgItem(self._resid[i+1]),self.gethelp(),None,0)
	
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

from fmtfloat import fmtfloat
import parseutil

RADIO,EVENT,TEXT,OFFSET,RESULT,REPEAT,RELATIVE,THINGBUTTON = 0x01,0x02,0x04,0x08,0x10,0x20,0x40,0x80

class EventCtrl(AttrCtrl):
	# This is the base class for an editor for the 'begin' and 'end'tabs.
	__radiobuttons = {
		grinsRC.IDC_RDELAY: 'delay',
		grinsRC.IDC_RNODE: 'node',
		grinsRC.IDC_RLAYOUT: 'region',
		grinsRC.IDC_RINDEFINITE: 'indefinite',
		grinsRC.IDC_RACCESSKEY: 'accesskey',
		grinsRC.IDC_RWALLCLOCK: 'wallclock',
		}

	def __init__(self, wnd, attr, resid):
		#'wnd': <AttrEditForm.SingleAttrPage instance at 1cabbe8>,
		#'attr': <TimelistAttrEditorField instance, name=beginlist>, 
		#'resid': a list of win32 resources; not used.
		AttrCtrl.__init__(self, wnd, attr, resid)
		#self._attrname=components.Control(wnd,grinsRC.IDC_EVENTLASSOO)
		#self._nedit=len(resid)-1 - how can an int have a length?
		self._attrval=[]

		# State variables:
		self._eventstruct = None	# This is the currently edited struct.
		self.selected_radiobutton = 'delay'
		self.dont_update = 0
		
		self._list = components.ListBox(wnd, grinsRC.IDC_EVENTLIST)
		self._addbutton = components.Button(wnd, grinsRC.IDC_NEWBUTTON)
		self._deletebutton = components.Button(wnd, grinsRC.IDC_DELETEBUTTON)

		self._eventwidget = components.ComboBox(self._wnd, grinsRC.IDC_EVENTTYPE)
		self._textwidget = components.Edit(self._wnd, grinsRC.IDC_THINGVALUE)
		self._thingbutton = components.Edit(self._wnd, grinsRC.IDC_THINGBUTTON)
		self._thingnamewidget = components.Edit(self._wnd, grinsRC.IDC_THINGNAME) # static text box.
		self._resultwidget = components.Edit(self._wnd, grinsRC.IDC_EVENTLASSOO)
		self._offsetwidget = components.Edit(self._wnd, grinsRC.IDC_EDITOFFSET)
		self._repeatwidget = components.Edit(self._wnd, grinsRC.IDC_EDITREPEAT)
		#self._repeatlabel = components.Static(self._wnd, grinsRC.IDC_REPEATLABEL)
		self._relative = components.CheckButton(wnd, grinsRC.IDC_RELATIVE)
		self._radiobuttonwidgets = {}
		for k,v in self.__radiobuttons.items():
			new = components.RadioButton(self._wnd, k)
			self._radiobuttonwidgets[v] = new

		self._node = self._wnd._form._node	# MMNode. Needed for creating new nodes.
					# now that also feels like a hack. Oh well.

	def OnInitCtrl(self):
		self._initctrl=self

		#self._attrname.attach_to_parent()
		self._list.attach_to_parent()
		self._addbutton.attach_to_parent()
		self._deletebutton.attach_to_parent()
		self._eventwidget.attach_to_parent()
		self._textwidget.attach_to_parent()
		self._thingnamewidget.attach_to_parent()
		self._thingbutton.attach_to_parent()
		self._resultwidget.attach_to_parent()
		self._offsetwidget.attach_to_parent()
		self._repeatwidget.attach_to_parent()
		#self._repeatlabel.attach_to_parent()
		self._relative.attach_to_parent()
		for b in self._radiobuttonwidgets.values():
 			b.attach_to_parent()
			b.hookcommand(self._wnd, self._radiobuttoncallback)

		# do this before setting the callback functions
		bob = self._attr.getcurrent()
		self.setvalue(self._attr.getcurrent())
		self.update()

		# Top half of window.
		self._list.hookcommand(self._wnd, self._listcallback)
		self._wnd.HookCommand(self.OnNew, grinsRC.IDC_NEWBUTTON)
		self._wnd.HookCommand(self.OnDelete, grinsRC.IDC_DELETEBUTTON)

		# Bottom half of window
		#self._causewidget.hookcommand(self, self._causewidgetcallback)
		self._eventwidget.hookcommand(self._wnd, self._eventwidgetcallback)
		self._textwidget.hookcommand(self._wnd, self._textwidgetcallback)
		self._offsetwidget.hookcommand(self._wnd, self._offsetwidgetcallback)
		self._repeatwidget.hookcommand(self._wnd, self._repeatwidgetcallback)
		self._thingbutton.hookcommand(self._wnd, self._thingbuttoncallback)
		self._relative.hookcommand(self._wnd, self._relativecallback)
		# XXXX No needshow() yet: this has to be done
		# differently, as we want to show some of the controls.

	def update(self, flags = RADIO|EVENT|TEXT|OFFSET|RESULT|REPEAT|RELATIVE|THINGBUTTON):
		# Updates all the widgets.
		if self.dont_update:
			return		# If I don't do this, the widgets refresh themselves ad inifinitium.
		self.dont_update = 1
		self.resetlist()
		self.initevent(flags)
		self.dont_update = 0

	def initevent(self, flags = RADIO|EVENT|TEXT|OFFSET|RESULT|REPEAT|RELATIVE|THINGBUTTON):
		if flags & RADIO:
			self.set_radiobuttons()
		if flags & EVENT:
			self.set_eventwidget()
		if flags & TEXT:
			self.set_textwidget()
		if flags & OFFSET:
			self.set_offsetwidget()
		if flags & RESULT:
			self.set_resultwidget()
		if flags & REPEAT:
			self.set_repeatwidget()
		if flags & RELATIVE:
			self.set_relative()
		if flags & THINGBUTTON:
			self.set_thingbutton()

	def sethelp(self):
		print "TODO: sethelp."

	def OnNew(self, id, code):
		# Callback from the "add" button, which I renamed to "new"
		# self._node should be an MMNode
		if self._node is None:
			print "ERROR: I cannot create this! I have no node."
			return
		n = EventEditor.EventStruct(None, node = self._node, action = self._attr.getname())
		self._value.append(n)
		self._eventstruct = n
		self.enableApply()
		self.update()
		self._list.setcursel(len(self._value)-1) # select new list element
		self._deletebutton.enable(1)

	def OnDelete(self, id, code):
		# callback for the "delete" button
		a = self._list.getselected()
		if 0 <= a < len(self._value):
			#self._list.deletestring(a)
			del self._value[a]
			if 0 <= a < len(self._value):
				self._eventstruct = self._value[a]
			else:
				self._eventstruct = None
			self.resetlist()
			self.initevent()
			self.enableApply()
			# delete only from the list; this will later be converted to a lack of syncarc.
		else:
			print "DEBUG: weirdly selected list member: ", a

	def enable(self, enable):
		pass

	def resetlist(self):
		sel = self._list.getcursel()
		self._list.resetcontent()
		for i in range(0, len(self._value)):
			self._list.insertstring(i, self._value[i].as_string())
		if 0 <= sel < len(self._value):
			self._list.setcursel(sel)
			self._deletebutton.enable(1)
		else:
			self._deletebutton.enable(0)

	def setvalue(self, val):
		if type(val) is type(()):
			self._node, self._value = val	# store for later use.
		elif type(val) is type([]):
			self._value = val
		else:
			print "ERROR: ListCtrl.setvalue received an invalid value."
			return
			
		if self._initctrl:
			# we have to update _eventstruct according to the selected item
			# otherwise, the wrong structure will be updated after a first apply
			selNumber = self._list.getcursel()
			if 0 <= selNumber < len(self._value):
				self._eventstruct = self._value[selNumber]
			else:
				self._eventstruct = None
			# reset UI
			self.dont_update = 1
			self.resetlist()
			self.initevent()
			self.dont_update = 0

	def getvalue(self):
		return self._value
		#return (self._node, self._value)

	def settooltips(self,tooltipctrl):
		for (idc, desc) in self._tooltips:
			tooltipctrl.AddTool(self._wnd.GetDlgItem(idc), desc, None, 0)

	def clear_radiobuttons(self):
		# Yes, this is a hack. The radio buttons wouldn't behave so I'm using brute force.
		for i in self._radiobuttonwidgets.values():
			i.enable(1)
			i.setcheck(0)

	def set_radiobuttons(self):
		if not self._eventstruct:
			self.clear_radiobuttons()
			for button in self._radiobuttonwidgets.values():
				button.enable(0)
		else:
			# Disable radiobuttons if there is no node..
			cause = self._eventstruct.get_cause()
			self.clear_radiobuttons() # fix a stupid bug by brute force.
			self._radiobuttonwidgets[cause].setcheck(1)
##			if not self._eventstruct.has_node() and cause == 'node':
##				self._thingbuttoncallback(None, win32con.BN_CLICKED)
			if self._node:
				pnode = self._node.GetParent()
				if self._attr.getname() == 'beginlist' and pnode and pnode.GetType() == 'seq':
					# Children of sequence nodes can only have
					# delays
					for k in self._radiobuttonwidgets.keys():
						self._radiobuttonwidgets[k].enable(k == 'delay')
					


	def set_relative(self):
		if not self._eventstruct:
			self._relative.enable(1)
			self._relative.setcheck(0)
			self._relative.enable(0)
		else:
			cause = self._eventstruct.get_cause()
			if cause == 'node' and self._eventstruct.has_node():
				self._relative.enable(1)
				relative = self._eventstruct.get_relative()
				self._relative.setcheck(relative)
				if relative and self._eventstruct._setnode is None and self._eventstruct._syncarc.refnode() is None:
					self._relative.enable(0)
			else:
				self._relative.enable(0)
				self._relative.setcheck(0)

	def set_thingbutton(self):
		if not self._eventstruct:
			self._thingbutton.enable(0)
		else:
			cause = self._eventstruct.get_cause()
			self._thingbutton.enable(cause in ('wallclock', 'region', 'node'))

	def set_eventwidget(self):
		# Sets the value of the event widget.
		if not self._eventstruct:
			self._eventwidget.resetcontent()
			self._eventwidget.enable(0)
			return
		
		l = self._eventstruct.get_possible_events()
		self._eventwidget.resetcontent()
		if l is not None:
			self._eventwidget.enable(1)
			map(self._eventwidget.addstring, l)
		else:
			self._eventwidget.enable(0)
			
		i = self._eventstruct.get_event_index()
		if i is not None:
			self._eventwidget.setcursel(i)
			
	def set_textwidget(self):
		if not self._eventstruct:
			self._textwidget.settext("")
			self._textwidget.enable(0)
			return
		name, string, isnumber, isreadonly = self._eventstruct.get_thing_string()
		if isreadonly or string is None or self._eventstruct.get_cause()=='wallclock':
			self._textwidget.enable(0)
		else:
			self._textwidget.enable(1)
		if string:
			self._textwidget.settext(string)
		else:
			self._textwidget.settext("")
		self._thingnamewidget.settext(name)

	def set_resultwidget(self):
		return
		if not self._eventstruct:
			self._resultwidget.settext("")
		else:
			self._resultwidget.settext(self._eventstruct.as_string())

	def set_offsetwidget(self):
		if not self._eventstruct:
			self._offsetwidget.settext("")
			self._offsetwidget.enable(0)
			return
		r = self._eventstruct.get_offset()
		if r is not None:
			self._offsetwidget.enable(1)
			self._offsetwidget.settext(fmtfloat(r))
		else:
			self._offsetwidget.settext("")
			self._offsetwidget.enable(0)

	def set_repeatwidget(self):
		# Only for event widgets or markers.
		if not self._eventstruct or self._eventstruct.get_cause() != 'node':
			self.__setrepeatwidget_clear()
		else:
			event = self._eventstruct.get_event()
			if event.startswith('repeat') and event != 'repeatEvent':
				i = self._eventstruct.get_repeat()
				if i:
					#self._repeatlabel.settext("Repeat:")
					self._repeatwidget.settext(`i`)
					self._repeatwidget.enable(1)
				else:
					self.__setrepeatwidget_clear()
			elif event == 'marker':
				i = self._eventstruct.get_marker()
				if i:
					#self._repeatlabel.settext("Marker:")
					self._repeatwidget.settext(i)
					self._repeatwidget.enable(1)				
				else:
					self.__setrepeatwidget_clear()
			else:
				self.__setrepeatwidget_clear()

	def __setrepeatwidget_clear(self):
		#self._repeatlabel.settext("")
		self._repeatwidget.settext("")
		self._repeatwidget.enable(0)

	def _listcallback(self, id, code):
		if code != win32con.CBN_SELCHANGE:
			return
		i = self._list.getselected()
		if 0 <= i < len(self._value):
			self._eventstruct = self._value[i]
			self.dont_update = 1
			self.initevent()
			self.dont_update = 0
			self._deletebutton.enable(1)
		else:
			print "error: weirdly selected list member: ", i
			self._deletebutton.enable(0)

##	def _causewidgetcallback(self, id, code):
##		if not self._eventstruct:
##			return		
##		if code == win32con.CBN_SELCHANGE:
##			s = self._causewidget.getvalue()
##			self._eventstruct.set_cause(s)
##			self.set_eventwidget()

	def _eventwidgetcallback(self, id, code):
		if not self._eventstruct:
			return
		if code == win32con.CBN_SELCHANGE:
			s = self._eventwidget.getvalue()
			self._eventstruct.set_event(s)
			self.enableApply()
			self.update()

	def _textwidgetcallback(self, id, code):
		if not self._eventstruct:
			return
		if code != win32con.EN_CHANGE:
			return
		t = self._textwidget.gettext()
		error = self._eventstruct.set_thing_string(t)
		if error:
			print "ERROR:", error
		self.enableApply()
		self.update(RADIO|EVENT|OFFSET|RESULT|REPEAT|THINGBUTTON)

	def _offsetwidgetcallback(self, id, code):
		if not self._eventstruct:
			return
		if code != win32con.EN_CHANGE:
			return
		t = self._offsetwidget.gettext()
		if t:
			try:
				self._eventstruct.set_offset(parseutil.parsecounter(self._offsetwidget.gettext(), withsign = 1))
			except parseutil.error, msg:
##				win32dialog.showmessage(msg, parent=self._wnd._form)
				return
		else:
			self._eventstruct.set_offset(None)
		self.enableApply()
		self.update(RADIO|EVENT|TEXT|RESULT|REPEAT|THINGBUTTON)

	def _radiobuttoncallback(self, id, code):
		if code == win32con.BN_CLICKED and self._eventstruct:
			newcause = self.__radiobuttons[id]
			if self._radiobuttonwidgets[newcause].getcheck():
				if newcause == 'node' and not self._eventstruct.has_node():

					dlg = win32dialog.SelectElementDlg(self._wnd._form, self._node.GetRoot(),
						self._node, filter = 'node',
						title='Source node for event:')
					if dlg.show():
						self._eventstruct.set_node(dlg.getmmobject())
				self._eventstruct.set_cause(newcause)
				self.enableApply()
				self.update()
				self.selected_radiobutton = newcause

	def _repeatwidgetcallback(self, id, code):
		if code == win32con.EN_CHANGE and self._eventstruct:
			e = self._eventstruct.get_event()
			if e.startswith('repeat') and e != 'repeatEvent':
				t = self._repeatwidget.gettext()
				if t:
					try:
						self._eventstruct.set_repeat(int(self._repeatwidget.gettext()))
					except ValueError:
						win32dialog.showmessage("Repeat count must be a number.", parent=self._wnd._form)
						return
				else:
					self._eventstruct.set_repeat(1)
			elif e=='marker':
				self._eventstruct.set_marker(self._repeatwidget.gettext())
			self.enableApply()	
			self.update(RADIO|EVENT|TEXT|OFFSET|RESULT|THINGBUTTON)

	def _thingbuttoncallback(self, id, code):
		if code == win32con.BN_CLICKED and self._eventstruct:
			c = self._eventstruct.get_cause()
			if c == 'wallclock':
				# TODO: more than just the wallclock.
				dialog = win32dialog.WallclockDialog(parent=self._wnd._form)
				dialog.setvalue(self._eventstruct.get_wallclock())
				dialog.show()
				self._eventstruct.set_wallclock(dialog.getvalue())
			elif c == 'region':
				# Pop up a region select dialog.
				dlg = win32dialog.SelectElementDlg(self._wnd._form, self._node.GetRoot(),
					self._eventstruct.get_region() or '', filter = 'topLayout')
				if dlg.show():
					self._eventstruct.set_region(dlg.getmmobject().name)
			elif c == 'node':
				# Pop up a node select dialog.
				dftselect = self._eventstruct.get_node()
				if not dftselect:
					dftselect = self._node
				dlg = win32dialog.SelectElementDlg(self._wnd._form, self._node.GetRoot(),
					dftselect, filter = 'node', title='Source node for this event')
				if dlg.show():
					self._eventstruct.set_node(dlg.getmmobject())
					self._eventstruct.check_event()
					self.update()
			self.enableApply()
			self.update()

	def _thingbuttondialogcallback(self, region):
		self._eventstruct.set_region(region)

	def _relativecallback(self, id, code):
		if code != win32con.BN_CLICKED:
			return
		relative = self._relative.getcheck()
		if not self._eventstruct.set_relative(relative):
			self._relative.setcheck(not relative)
		self.enableApply()

class BeginEventCtrl(EventCtrl):
	_tooltips = [
		(grinsRC.IDC_EVENTLIST, 'If specified, playback of the object is delayed until any of these events fire'),
		(grinsRC.IDC_NEWBUTTON, 'Add a new begin event'), 
		(grinsRC.IDC_DELETEBUTTON, 'Remove the selected begin event'),

		(grinsRC.IDC_EVENTTYPE, 'Source object and source event determine when the current event fires'),
		(grinsRC.IDC_THINGVALUE, 'Source object and source event determine when the current event fires'),
		(grinsRC.IDC_THINGBUTTON, 'Select source object'),
		(grinsRC.IDC_EDITOFFSET, 'Delay event by this number of seconds (negative values allowed)'),
		(grinsRC.IDC_EDITREPEAT, 'Event fires on this repeat iteration or marker'),
		(grinsRC.IDC_RDELAY, 'This event fires after the delay'),
		(grinsRC.IDC_RNODE, 'This event fires relative tto an event on another node'),
		(grinsRC.IDC_RLAYOUT, 'This event fires relative to an event on a region'),
		(grinsRC.IDC_RINDEFINITE, 'This event never fires.\nIf this is the only event, the node will never start'),
		(grinsRC.IDC_RACCESSKEY, 'This event fires when the user presses the specified key on the keyboard'),
		(grinsRC.IDC_RWALLCLOCK, 'This event fires at a certain time of day'),
		(grinsRC.IDC_RELATIVE, 'Refer to other node by relative path in stead of name'),
		]

class EndEventCtrl(EventCtrl):
	_tooltips = [
		(grinsRC.IDC_EVENTLIST, 'If specified, playback of the object is terminated when any of these events fire'),
		(grinsRC.IDC_NEWBUTTON, 'Add a new end event'), 
		(grinsRC.IDC_DELETEBUTTON, 'Remove the selected end event'),

		(grinsRC.IDC_EVENTTYPE, 'Source object and source event determine when the current event fires'),
		(grinsRC.IDC_THINGVALUE, 'Source object and source event determine when the current event fires'),
		(grinsRC.IDC_THINGBUTTON, 'Select source object'),
		(grinsRC.IDC_EDITOFFSET, 'Delay event by this number of seconds (negative values allowed)'),
		(grinsRC.IDC_EDITREPEAT, 'Event fires on this repeat iteration or marker'),
		(grinsRC.IDC_RDELAY, 'This event fires after the delay'),
		(grinsRC.IDC_RNODE, 'This event fires relative tto an event on another node'),
		(grinsRC.IDC_RLAYOUT, 'This event fires relative to an event on a region'),
		(grinsRC.IDC_RINDEFINITE, 'This event never fires.\nIf this is the only event, the node will never start'),
		(grinsRC.IDC_RACCESSKEY, 'This event fires when the user presses the specified key on the keyboard'),
		(grinsRC.IDC_RWALLCLOCK, 'This event fires at a certain time of day'),
		(grinsRC.IDC_RELATIVE, 'Refer to other node by relative path in stead of name'),
		]


class HrefCtrl(AttrCtrl):
	def __init__(self, wnd, attr, resid):
		AttrCtrl.__init__(self, wnd, attr, resid)
		self.__nohref = components.RadioButton(wnd,resid[1])
		self.__internal = components.RadioButton(wnd,resid[2])
		self.__external = components.RadioButton(wnd,resid[3])
		self.__browse = components.Button(wnd,resid[4])
		self.__url = components.Edit(wnd,resid[5])
		self.__browseurl = components.Button(wnd,resid[6])
		self.__node = None
		self.__string = ''
		self.__curval = 0	# "impossible" value (important for first setvalue() call)
		self.__OnRadioIgnore = 0

	def OnInitCtrl(self):
		val = self._attr.getcurrent()
		self.__nohref.attach_to_parent()
		self.__nohref.hookcommand(self._wnd,self.OnRadio)
		self.__internal.attach_to_parent()
		self.__internal.hookcommand(self._wnd,self.OnRadio)
		self.__external.attach_to_parent()
		self.__external.hookcommand(self._wnd,self.OnRadio)
		self.__browse.attach_to_parent()
		self._wnd.HookCommand(self.OnBrowse,self._resid[4])
		if features.INTERNAL_LINKS not in features.feature_set:
			self.__internal.hide()
			self.__browse.hide()
		self.__url.attach_to_parent()
		self._wnd.HookCommand(self.OnEdit,self._resid[5])
		self.__browseurl.attach_to_parent()
		self._wnd.HookCommand(self.OnBrowseURL,self._resid[6])
		if val is None:
			self.__node = None
			self.__string = ''
		elif type(val) is type(''):
			self.__node = None
			self.__string = val
		else:
			self.__node = val
			self.__string = ''
		self._initctrl = self
		self.setvalue(val)

	def setvalue(self, val, settext = 1):
		if val == self.__curval:
			return
		self.__curval = val
		if not self._initctrl:
			return
		try:
			self.__OnRadioIgnore = 1
			if settext:
				if type(val) is type(''):
					url = self._attr.wrapper.context.findurl(val)
					import urlparse
					scheme, netloc, url, params, query, fragment = urlparse.urlparse(url)
					if not scheme or scheme == 'file':
						import MMurl
						val = MMurl.url2pathname(url)
					self.__url.settext(val)
				else:
					self.__url.settext('')
			if val is None:
				self.__nohref.setcheck(1)
				self.__internal.setcheck(0)
				self.__external.setcheck(0)
			elif type(val) is type(''):
				self.__nohref.setcheck(0)
				self.__internal.setcheck(0)
				self.__external.setcheck(1)
			else:
				self.__nohref.setcheck(0)
				self.__internal.setcheck(1)
				self.__external.setcheck(0)
		finally:
			self.__OnRadioIgnore = 0

	def getvalue(self):
		if self.__curval == 0:
			# not initialized
			return self._attr.getcurrent()
		return self.__curval

	def OnRadio(self,id,code):
		if self.__OnRadioIgnore:
			return
		self.sethelp()
		if code==win32con.BN_CLICKED:
			if self.__nohref.getcheck():
				val = None
			elif self.__internal.getcheck():
				val = self.__node
				if val is None:
					self.OnBrowse(id,code)
					val = self.__curval
			else:
				val = self.__string
			self.setvalue(val)
			self.enableApply()

	def OnBrowseURL(self,id,code):
		self._attr.browser_callback()

	def OnBrowse(self,id,code):
		val = self.__curval
		if val is type(''):
			val = None
		if val is None:
			val = self.__node
		parent = self._wnd._form
		mmnode = self._wnd._form._node
		dlg = win32dialog.SelectElementDlg(parent, mmnode.GetRoot(), val, 'node')
		if dlg.show():
			val = dlg.getmmobject()
			self.__node = val
			self.setvalue(val)
			self.enableApply()

	def OnEdit(self,id,code):
		if self.__OnRadioIgnore:
			return
		if code==win32con.EN_SETFOCUS:
			self.sethelp()
		elif code==win32con.EN_CHANGE:
			self.setvalue(self.__url.gettext(), 0)
			self.enableApply()

	def settooltips(self,tooltipctrl):
		tooltipctrl.AddTool(self._wnd.GetDlgItem(self._resid[1]),'No hyperlink',None,0)
		tooltipctrl.AddTool(self._wnd.GetDlgItem(self._resid[2]),'Internal hyperlink',None,0)
		tooltipctrl.AddTool(self._wnd.GetDlgItem(self._resid[3]),'External hyperlink',None,0)
		tooltipctrl.AddTool(self._wnd.GetDlgItem(self._resid[4]),'Select destination of internal hyperlnk',None,0)
		tooltipctrl.AddTool(self._wnd.GetDlgItem(self._resid[5]),'URL of external hyperlink',None,0)

##################################
# StringOptionsCtrl can be used as a StringCtrl but the user 
# can optionally select the string from a drop down list
class StringOptionsCtrl(AttrCtrl):
	def __init__(self,wnd,attr,resid,options=[]):
		AttrCtrl.__init__(self,wnd,attr,resid)
		self._attrname=components.Edit(wnd,resid[0])
		self._attrval=components.ComboBox(wnd,resid[1])
		self._options=options
		self._queryctrl='e'
		
	def OnInitCtrl(self):
		self._initctrl=self
		self._attrname.attach_to_parent()
		self._attrval.attach_to_parent()
		if self.want_label:
			label = self._attr.getlabel()
			if self.want_colon_after_label:
				label = label + ':'
			self._attrname.settext(label)
		if len(self._options):
			self._attrval.initoptions(self._options)
		self.setvalue(self._attr.getcurrent())
		self._wnd.HookCommand(self.OnCombo,self._resid[1])
		if not self._attr.mustshow():
			self.attrname.hide()
			self._attrval.hide()


	def enable(self, enable):
		self._attrval.enable(enable)

	def setvalue(self, val):
		if self._initctrl:
			self._attrval.setedittext(val)

	def getvalue(self):
		if not self._initctrl:
			return self._attr.getcurrent()
		if self._queryctrl=='e':
			val = self._attrval.getedittext()
		elif self._queryctrl=='o':
			sel=self._attrval.getcursel()
			if self and sel>=0:
				val=self._attrval.gettext(sel)
			else:
				val=''
		return val

	def OnCombo(self,id,code):
		self.sethelp()
		if code==win32con.CBN_SELCHANGE:
			self._queryctrl='o'
			self.enableApply()
		elif code==win32con.CBN_EDITCHANGE:
			self._queryctrl='e'
			self.enableApply()

	def settooltips(self,tooltipctrl):
		tooltipctrl.AddTool(self._wnd.GetDlgItem(self._resid[1]),self.gethelp(),None,0)

class HtmlTemplateCtrl(StringOptionsCtrl):
	def __init__(self,wnd,attr,resid):
		import compatibility
		# for instance, only embedded_player is supported in QuickTime version
		if compatibility.QT == features.compatibility:
			options=['embedded_player.html']
		else:
			options=['external_player.html','embedded_player.html']
		self._options = options
		StringOptionsCtrl.__init__(self,wnd,attr,resid,options)

	def setvalue(self, val):
		if not self._initctrl: return
		if val not in self._options:
			ix = -1
		else:
			ix=self._options.index(val)
		self._attrval.setcursel(ix)

	def getvalue(self):
		if self._initctrl:
			return self._attrval.getvalue() 
		return self._attr.getcurrent()
	
##################################
class AttrSheet(dialog.PropertySheet):
	def __init__(self,form):
		self._form=form
		self._showAll = None
		self._followSelection = None
		import __main__
		dll=__main__.resdll
		dialog.PropertySheet.__init__(self,grinsRC.IDR_GRINSED,dll)
		self.HookMessage(self.onInitDialog,win32con.WM_INITDIALOG)
		self._apply=components.Button(self,afxres.ID_APPLY_NOW)
		self.HookMessage(self.onSize,win32con.WM_SIZE)

	def onInitDialog(self,params):
		self.HookCommand(self.onApply,afxres.ID_APPLY_NOW)
		self.HookCommand(self.onOK,win32con.IDOK)
		self.HookCommand(self.onCancel,win32con.IDCANCEL)
		self._apply.attach_to_parent()

		self.createButtons()

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
		# XXXX (Jack) Shouldn't we enable/disable OK as well?

	def createButtons(self):
		l,t,r,b = self.GetDlgItem(win32con.IDOK).GetWindowRect()
		h = b-t
		if self._form._has_showAll:
			ctrl = components.CheckButton(self,101)
			if settings.get('enable_template'):
				name = 'Builder/Advanced'
			else:
				name = 'Advanced'
			ctrl.create(components.CHECKBOX(), (0,0,116,h), name)
			ctrl.setcheck(self._form._showAll_initial)
			self.HookCommand(self.onShowAll, 101)
			self._showAll = ctrl

		if self._form._has_followSelection:
			ctrl = components.CheckButton(self,102)
			ctrl.create(components.CHECKBOX(), (0,0,100,h), 'Follow selection')
			ctrl.setcheck(self._form._followSelection_initial)
			ctrl.hookmessage(self.onFollowSelection, win32con.WM_LBUTTONDOWN)
			self._followSelection = ctrl
		
		# set button font
		lf = {'name':'', 'pitch and family':win32con.FF_SWISS,'charset':win32con.ANSI_CHARSET}
		d = Sdk.EnumFontFamiliesEx(lf)
		logfont = None
		if d.has_key('Tahoma'): # win2k
			logfont = {'name':'Tahoma', 'height': 11, 'weight': win32con.FW_MEDIUM, 'charset':win32con.ANSI_CHARSET}
		elif d.has_key('Microsoft Sans Serif'): # not win2k
			logfont = {'name':'Microsoft Sans Serif', 'height': 11, 'weight': win32con.FW_MEDIUM, 'charset':win32con.ANSI_CHARSET}
		if logfont:
			if self._showAll:
				self._showAll.setfont(logfont)
			if self._followSelection:
				self._followSelection.setfont(logfont)

	def fixbuttonstate(self, showall, follow, okstate):
		if self._showAll:
			self._showAll.setcheck(showall)
		if self._followSelection:
			self._followSelection.setcheck(follow)
		self.enableApply(okstate)

	def onShowAll(self, id, code):
		self._form.call('Showall')

	def onFollowSelection(self, params):
		self._form.call('Followselection')
		
	def onSize(self, params):
		flags = win32con.SWP_NOSIZE | win32con.SWP_NOZORDER | win32con.SWP_NOACTIVATE
		msg = win32mu.Win32Msg(params)
		if self._showAll:
			l, t, r, b = self._showAll.getwindowrect()
			w, h = r-l, b-t
			dh = 6
			self._showAll.setwindowpos(0, (6 ,msg.height()-h-dh, w+4, msg.height()-dh), flags)
		if self._followSelection:
			l, t, r, b = self._followSelection.getwindowrect()
			w, h = r-l, b-t
			dh = 6
			if self._showAll:
				left = w+24
			else:
				left = 6
			self._followSelection.setwindowpos(0, (left,msg.height()-h-dh, w+w+4, msg.height()-dh), flags)
		
class AttrPage(dialog.PropertyPage):
	enabletooltips = 1
	def __init__(self,form):
		self._form=form
		self._cd={}
		self._group=None
		self._tabix=-1
		self._title='Untitled page'
		self._initdialog=None
		self._attrinfo=components.Static(self,grinsRC.IDC_ATTR_INFO)
		if AttrPage.enabletooltips:
			self._tooltipctrl=win32ui.CreateToolTipCtrl()
		else:
			self._tooltipctrl=None
		
	def do_init(self):
		id=self.getpageresid()
		self.createctrls()
		import __main__
		dll=__main__.resdll
		# Create a new dialog box for this attribute.
		dialog.PropertyPage.__init__(self,id,dll,grinsRC.IDR_GRINSED)
		
	def do_close(self):
		self._form = None
		# XXXX More may be needed...

	def OnInitDialog(self):
		if not self._form:
			# Closing down the property sheet
			return 0
		self._initdialog=self
		dialog.PropertyPage.OnInitDialog(self)
		self._attrinfo.attach_to_parent()
		for ctrl in self._cd.values():
			ctrl.OnInitCtrl()
			ctrl.addlistener(self)
		if self._group:
			self._group.oninitdialog(self)
		if self._tooltipctrl:
			self._tooltipctrl.CreateWindow(self,0)
			self._tooltipctrl.Activate(1)
			self.SetToolTipCtrl(self._tooltipctrl)
			self.settooltips()
		return 1
		
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
	
	def settooltips(self):
		if self._tooltipctrl:
			for ctrl in self._cd.values():
				ctrl.settooltips(self._tooltipctrl)

	# interface of listeners
	def onevent(self,attr,event):
		pass

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
class OptionsNocolonCtrl(OptionsCtrl):
	want_colon_after_label = 0

class OptionsRadioNocolonCtrl(OptionsRadioCtrl):
	want_colon_after_label = 0

class StringNocolonCtrl(StringCtrl):
	want_colon_after_label = 0

# On some pages we don't want to change the label, since the pages were
# designed with labels
class FloatTupleNolabelCtrl(FloatTupleCtrl):
	want_label = 0

class OptionsNolabelCtrl(OptionsCtrl):
	want_label = 0

class OptionsRadioNolabelCtrl(OptionsRadioCtrl):
	want_label = 0

class OptionsCheckNolabelCtrl(OptionsCheckCtrl):
	want_label = 0

class OptionsCheckMultipleNolabelCtrl(OptionsCheckMultipleCtrl):
	want_label = 0

class StringNolabelCtrl(StringCtrl):
	want_label = 0

class ColorNolabelCtrl(ColorCtrl):
	want_label = 0

class EmptyAttrPage(AttrPage):
	def __init__(self, form):
		AttrPage.__init__(self, form)
		self._title = 'No properties'
		self._attr = None

	def getpageresid(self):
		return grinsRC.IDD_EDITATTR_EMPTY

	def createctrls(self):
		return {}

###############################	
class SingleAttrPage(AttrPage):
	# These map attribute names to (dialog-resource-id, constructor-function, control-ids)
	# tuples. For unknown attributes we default to "string".
	# The fact that we also have a mapping by name (in stead of by type
	# only) means we can have special-case dialogs for Windows while
	# the code will continue to work (with a boring popup menu)
	# for the other platforms.
	CTRLMAP_BYNAME = {
##		'layout':		# Two radio buttons
##			(grinsRC.IDD_EDITATTR_R2,
##			 OptionsRadioNocolonCtrl,
##			 (grinsRC.IDC_1,grinsRC.IDC_2,grinsRC.IDC_3)),
		'aspect':		# Two radio buttons
			(grinsRC.IDD_EDITATTR_R2,
			 OptionsRadioNocolonCtrl,
			 (grinsRC.IDC_1,grinsRC.IDC_2,grinsRC.IDC_3)),
		'visible':		# Three radio buttons
			(grinsRC.IDD_EDITATTR_R3,
			 OptionsRadioNocolonCtrl,
			 (grinsRC.IDC_1,grinsRC.IDC_2,grinsRC.IDC_3,grinsRC.IDC_4)),
		'popup':		# Three radio buttons
			(grinsRC.IDD_EDITATTR_R3,
			 OptionsRadioNocolonCtrl,
			 (grinsRC.IDC_1,grinsRC.IDC_2,grinsRC.IDC_3,grinsRC.IDC_4)),
		'reliable':
			(grinsRC.IDD_EDITATTR_CK1,
			 OptionsCheckCtrl,
			 (grinsRC.IDC_1,)),
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
			 OptionsCheckMultipleNolabelCtrl,
			 (grinsRC.IDC_1,grinsRC.IDC_CHECK1,grinsRC.IDC_CHECK2,grinsRC.IDC_CHECK3,grinsRC.IDC_CHECK4,grinsRC.IDC_CHECK5,
			  grinsRC.IDC_CHECK6)),
		'base_window':		# Drop down list plus Properties button
			(grinsRC.IDD_EDITATTR_CH1,
			 ChannelCtrl,
			 (grinsRC.IDC_1,grinsRC.IDC_2,grinsRC.IDC_3)),
		'channel':		# Drop down list plus Properties button
			(grinsRC.IDD_EDITATTR_CH1,
			 ChannelCtrl,
			 (grinsRC.IDC_1,grinsRC.IDC_2,grinsRC.IDC_3)),
		'captionchannel':	# Drop down list plus Properties button
			(grinsRC.IDD_EDITATTR_CH1,
			 ChannelCtrl,
			 (grinsRC.IDC_1,grinsRC.IDC_2,grinsRC.IDC_3)),
		'project_html_page':	# A string field with a drop down selection list
			(grinsRC.IDD_EDITATTR_D1,
			 HtmlTemplateCtrl,
			 (grinsRC.IDC_11,grinsRC.IDC_12)),
		'targetElement':	# A string field with a browse element button
			(grinsRC.IDD_EDITATTR_F1,
			 ElementSelCtrl,
			 (grinsRC.IDC_1,grinsRC.IDC_2, grinsRC.IDC_3)),
		'additive':		# Two radio buttons
			(grinsRC.IDD_EDITATTR_R2,
			 OptionsRadioNocolonCtrl,
			 (grinsRC.IDC_1,grinsRC.IDC_2,grinsRC.IDC_3)),
		'accumulate':		# Two radio buttons
			(grinsRC.IDD_EDITATTR_R2,
			 OptionsRadioNocolonCtrl,
			 (grinsRC.IDC_1,grinsRC.IDC_2,grinsRC.IDC_3)),

		}
	CTRLMAP_BYTYPE = {
		'option':		# An option selected from a list (as a popup menu)
			(grinsRC.IDD_EDITATTR_O1,
			 OptionsCtrl,
			 (grinsRC.IDC_1,grinsRC.IDC_2)),
		'bool':			# A check button
			(grinsRC.IDD_EDITATTR_CK1,
			 OptionsCheckCtrl,
			 (grinsRC.IDC_1,)),
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
##		'timelist':		# A list of events.
##			(grinsRC.IDD_EDITATTR_2LIST,
##			 ListCtrl,
##			 (grinsRC.IDC_LIST4, grinsRC.IDC_BUTTON7, grinsRC.IDC_BUTTON8, grinsRC.IDC_BUTTON9,)),
##			  #grinsRC.IDC_LIST3, grinsRC.IDC_BUTTON4, grinsRC.IDC_BUTTON5, grinsRC.IDC_BUTTON6)),
		}

	def __init__(self,form,attr):
		AttrPage.__init__(self,form)
		self._attr=attr

	def OnInitDialog(self):
		if not AttrPage.OnInitDialog(self):
			return
		ctrl=self._cd[self._attr]
		ctrl.OnInitCtrl()
		ctrl.sethelp()

	def _getcontrolinfo(self):
		n = self._attr.getname()
		t = self._attr.gettype()
		# manage special cases
##		if n=='layout' and len(self._attr.getoptions())>2:
##			if self.CTRLMAP_BYTYPE.has_key(t):
##				return self.CTRLMAP_BYTYPE[t]
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
			box = scaledrc.xywh_tuple()
			box = box[0]-self._offset[0], \
			      box[1]-self._offset[1], \
			      box[2], box[3]
			s='(%.0f,%.0f,%.0f,%.0f)' %  box
		elif units == UNIT_SCREEN:
			s='(%.2f,%.2f,%.2f,%.2f)' %  self._wnd.inverse_coordinates(rc.xywh_tuple(),units=units)
		else:
			str_units='mm'
			scaledrc=self.scaleCoord(rc)
			s='(%.1f,%.1f,%.1f,%.1f)' % self._wnd.inverse_coordinates(scaledrc.xywh_tuple(),units=units)
		return s, str_units

	# rc is a win32mu.Rect in pixels
	# we return box=(x,y,w,h) in units (in arg)
	def orgrect(self, rc, units):
		if units == UNIT_PXL:
			scaledrc=self.scaleCoord(rc)
			return scaledrc.xywh_tuple()
		elif units == UNIT_SCREEN:
			return self._wnd.inverse_coordinates(rc.xywh_tuple(),units=units)
		else:
			scaledrc=self.scaleCoord(rc)
			return self._wnd.inverse_coordinates(scaledrc.xywh_tuple(),units=units)


	# box is in units and scaled
	# return original box
	def orgbox(self, box, units):
		if units == UNIT_SCREEN:
			return box
		elif units == UNIT_PXL:
			rc=Rect((box[0],box[1],box[0]+box[2],box[1]+box[3]))
			scaledrc=self.scaleCoord(rc)
			return scaledrc.xywh_tuple()
		else:
			rc=Rect((box[0],box[1],box[0]+box[2],box[1]+box[3]))
			scaledrc=self.scaleCoord(rc)
			return scaledrc.xywh_tuple()
	

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
import winlayout
import appcon, sysmetrics
import string

class LayoutPage(AttrPage):
	def __init__(self,form):
		AttrPage.__init__(self, form)
		self._units = self._form.getunits()
		self._layoutctrl = None
		self._isintscale = 1
		self._boxoff = 0, 0
		self._inupdate = 0
			
	def OnInitDialog(self):
		if not AttrPage.OnInitDialog(self):
			return
		self.HookMessage(self.onLButtonDown, win32con.WM_LBUTTONDOWN)
		self.HookMessage(self.onLButtonUp, win32con.WM_LBUTTONUP)
		self.HookMessage(self.onMouseMove, win32con.WM_MOUSEMOVE)
		preview = components.Control(self, grinsRC.IDC_PREVIEW)
		preview.attach_to_parent()
		l1, t1, r1, b1 = self.GetWindowRect()
		l2, t2, r2, b2 = preview.getwindowrect()
		self._layoutpos = l2-l1, t2-t1
		self._layoutsize = r2-l2, b2-t2

		import MMAttrdefs
		pnode = self._form._node.parent
		w, h = MMAttrdefs.getattr(pnode, 'size')
		self.findLayoutScale((w, h))

		self._layoutctrl = self.createLayoutCtrl()

		t = components.Static(self,grinsRC.IDC_SCALE1)
		t.attach_to_parent()
		if self._isintscale:
			t.settext('scale 1 : %.0f' % self._xscale)
		else:
			t.settext('scale 1 : %.1f' % self._xscale)
		self.create_box(self.getcurrentbox())

	# update layout control that the mouse is outside its region
	def onLButtonDown(self,params):
		if self._layoutctrl:
			self._layoutctrl.onNCLButton(params)
	def onLButtonUp(self,params):
		if self._layoutctrl:
			self._layoutctrl.onNCLButton(params)
	def onMouseMove(self,params):
		if self._layoutctrl:
			self._layoutctrl.onNCLButton(params)

	def OnSetActive(self):
		if self._layoutctrl:
			self.create_box(self.getcurrentbox())
		return self._obj_.OnSetActive()

	def OnKillActive(self): 
		return self._obj_.OnKillActive()

	def OnDestroy(self,params):
		pass

	def createLayoutCtrl(self):
		v = winlayout.LayoutOsWndCtrl(self, self._xscale)
		x, y, w, h = self.getboundingbox()
		dw = 2*win32api.GetSystemMetrics(win32con.SM_CXEDGE)
		dh = 2*win32api.GetSystemMetrics(win32con.SM_CYEDGE)
		rc = self._layoutpos[0], self._layoutpos[1], w+dw, h+dh
		v.createWindow(self, rc, (255,255,255))
		self.initLayoutCtrl(v)
		return v
	
	def initLayoutCtrl(self, v):
		self._scale = LayoutScale(v, self._xscale, self._yscale, self._boxoff)
		# add regions of interest to layout control

	def findLayoutScale(self, winsize = None, units = appcon.UNIT_PXL):
		if winsize:
			sw, sh = winsize
		else:
			sw, sh = sysmetrics.scr_width_pxl, sysmetrics.scr_height_pxl
		
		# try first an int scale
		n = max(1, (sw+self._layoutsize[0]-1)/self._layoutsize[0], 
			(sh+self._layoutsize[1]-1)/self._layoutsize[1])
		scale = float(n)
		self._xmax = int(sw/scale+0.5)
		self._ymax = int(sh/scale+0.5)
		self._isintscale = 1
		if n!=1 and (self._xmax<3*self._layoutsize[0]/4 or self._ymax<3*self._layoutsize[1]/4):
			# try to find a better scale
			scale = max(1, float(sw)/self._layoutsize[0], float(sh)/self._layoutsize[1])
			self._xmax = int(sw/scale+0.5)
			self._ymax = int(sh/scale+0.5)
			self._isintscale = 0
		
		# finally the exact scale:
		self._xscale = float(sw)/self._xmax
		self._yscale = float(sh)/self._ymax
	
	def getboundingbox(self):
		return  0, 0, self._xmax, self._ymax

	def create_box(self,box):
		self._layoutctrl.removeObjects()
		self._layoutctrl.update()
		if box and (box[2]==0 or box[3]==0):
			box = None
		if box is None:
			self._layoutctrl.selectTool('shape')
		else:
			self._layoutctrl.setObject(box)
			self._layoutctrl.selectTool('select')

	def setvalue(self, attr, val):
		if not self._initdialog: return
		self._cd[attr].setvalue(val)
		if self.islayoutattr(attr):
			self.setvalue2layout(val)
			

	######################
	# subclass overrides

	def getcurrentbox(self, saved=1):
		lc = self.getctrl('base_winoff')
		if saved:
			val = lc.getcurrent()
		else:
			val = lc.getvalue()
		box = self.val2box(val)
		lbox = self._scale.layoutbox(box,self._units)
		return lbox

	def setvalue2layout(self,val):
		box = self.val2box(val)
		lbox = self._scale.layoutbox(box, self._units)
		self.create_box(lbox)
	
	def val2box(self,val):
		if not val:
			box = None
		else:
			box = atoft(val)
		return box
		
	def islayoutattr(self,attr):
		if self._group:
			return self._group.islayoutattr(attr)
		else:
			return 0

	# called back by create_box on every change
	# the user can press reset to cancel changes
	def updateBox(self, *box):
		if self._initdialog:
			self._inupdate=1
			lc=self.getctrl('base_winoff')
			if not box:
				lc.setvalue('')
			else:	
				box=self._scale.orgbox(box, self._units)
				if self._units==UNIT_PXL:prec=0
				elif self._units==UNIT_SCREEN:prec=1
				else: prec=2
				a=fttoa(box,4,prec)
				lc.setvalue(a)
			self._inupdate=0

	def onevent(self,attr,event):
		if self._inupdate: return
		if attr.getname()=='base_winoff':
			self.create_box(self.getcurrentbox(0))


class PosSizeLayoutPage(LayoutPage):
	def __init__(self,form):
		LayoutPage.__init__(self, form)
		self._xy=None
		self._wh=None
		ch = form._node.parent.GetChannel()
		if ch and ch.has_key('base_window'):
			self._boxoff = ch.get('base_winoff', (0,0,0,0))[:2]

	def getcurrentbox(self,saved=1):
		attrnames = self._group._attrnames
		self._xy=self.getctrl(attrnames['xy'])
		self._wh=self.getctrl(attrnames['wh'])
		if saved:
			sxy=self._xy.getcurrent()
			if not sxy:sxy='0 0'
			swh=self._wh.getcurrent()
			if not swh:swh='0 0'
		else:
			sxy=self._xy.getvalue()
			if not sxy:sxy='0 0'
			swh=self._wh.getvalue()
			if not swh:swh='0 0'	
		val = sxy + ' ' + swh
		box=atoft(val)
		if len(box)==4:
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
	def updateBox(self,*box):
		if self._initdialog:
			self._inupdate=1
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
				grp = self._group
				a = grp.getattr(grp._attrnames['full'])
				a.setvalue('off')
			self._inupdate=0

	def onevent(self,attr,event):
		if self._inupdate: return
		attrname = attr.getname()
		if attrname=='subregionxy' or attrname=='subregionwh' or \
		   attrname=='imgcropxy' or attrname=='imgcropwh':
			self.create_box(self.getcurrentbox(0))
			grp = self._group
			a = grp.getattr(grp._attrnames['full'])
			a.setvalue('off')

class SubImgLayoutPage(PosSizeLayoutPage):
	def __init__(self, form):
		LayoutPage.__init__(self,form)
		self._xy=None
		self._wh=None

	def OnInitDialog(self):
		if not AttrPage.OnInitDialog(self):
			return
		tag = None
		file = None
		for a in self._form._attriblist:
			if a.getname() == 'tag':
				tag = a.getvalue()
			if a.getname() == 'file':
				file = a
			if tag is not None and file is not None:
				break
		self.HookMessage(self.onLButtonDown,win32con.WM_LBUTTONDOWN)
		self.HookMessage(self.onLButtonUp,win32con.WM_LBUTTONUP)
		self.HookMessage(self.onMouseMove,win32con.WM_MOUSEMOVE)
		preview=components.Control(self,grinsRC.IDC_PREVIEW)
		preview.attach_to_parent()
		l1,t1,r1,b1=self.GetWindowRect()
		l2,t2,r2,b2=preview.getwindowrect()
		self._layoutpos =(l2-l1,t2-t1)
		self._layoutsize = (r2-l2,b2-t2)
		if tag == 'viewchange':
			import MMAttrdefs
			pnode = self._form._node.parent
			w, h = MMAttrdefs.getattr(pnode, 'size')
		else:
			if file is not None:
				f = file.getvalue()
			else:
				f = None
			if f:
				import Sizes
				url = a.wrapper.getcontext().findurl(f)
				w, h = Sizes.GetSize(url)
				if w == 0 or h == 0:
					w, h = self._layoutsize
			else:
				w, h = self._layoutsize
		self.__bbox = w,h
		self.findLayoutScale((w,h))
		self._layoutctrl=self.createLayoutCtrl()

		t=components.Static(self,grinsRC.IDC_SCALE1)
		t.attach_to_parent()
		if self._isintscale:
			t.settext('scale 1 : %.0f' % self._xscale)
		else:
			t.settext('scale 1 : %.1f' % self._xscale)
		self.create_box(self.getcurrentbox())
		if tag != 'viewchange' and file and not features.lightweight:
			url = a.wrapper.getcontext().findurl(f)
			self.loadimg(url)

	def initLayoutCtrl(self, v):
		self._scale = LayoutScale(v, self._xscale, self._yscale, self._boxoff)
		# add regions of interest to layout control

	def loadimg(self,url):
		import MMurl
		try:
			f = MMurl.urlretrieve(url)[0]
		except IOError, arg:
			print 'failed to retrieve',url
			return
		if self._layoutctrl:
			self._layoutctrl.setImage(f, fit='fill', mediadisplayrect = None)
		
############################
# Base class for media renderers

class Renderer:
	def __init__(self,wnd,rc,baseURL=''):
		self._wnd=wnd
		self._rc=rc
		self._baseURL=baseURL
		self._bgcolor=(0,0,0)

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
	def adjustSize(self, size):
		rc=win32mu.Rect(self._rc)
		return rc.adjustSize(size)

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

	# has finished playing?
	def ismediaend(self):
		return 0

	# has duration?
	def isstatic(self):
		return 0

	# nees surface to draw?
	def needswindow(self):
		return 1
	
	# needs its os window?
	def needsoswindow(self):
		return 0

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
		except error:
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

###############################
import svgdom

class SvgRenderer(Renderer):
	def __init__(self,wnd,rc,baseURL=''):
		Renderer.__init__(self,wnd,rc,baseURL)
		self._svgdoc = None
		self._svgplayer = None
		self._adjrc = None
			
	def __del__(self):
		if self._svgplayer:
			self._svgplayer.stop()
			del self._svgplayer
		del self._svgdoc
	
	def isstatic(self):
		return 1

	def load(self, rurl):
		self._svgdoc = None
		if self._svgplayer:
			self._svgplayer.stop()
			self._svgplayer = None
		if rurl:
			url = self.urlqual(rurl)
			import urlcache
			mtype = urlcache.mimetype(url)
			if mtype is not None: 
				mtype, subtype = string.split(mtype, '/')
				if mtype == 'image' and subtype == 'svg-xml':
					self._svgdoc = svgdom.GetSvgDocument(url)
					src_x, src_y, dest_x, dest_y, width, height,rcKeep = self.adjustSize(self._svgdoc.getSize())
					self._adjrc = dest_x, dest_y,dest_x + width, dest_y + height
					if self._svgdoc.hasTiming():
						rendercb = (self.renderSvgOffscreenOn, (self._svgdoc, None, (dest_x, dest_y, width, height)))
						from windowinterface import toplevel
						self._svgplayer = svgdom.SVGPlayer(self._svgdoc, toplevel, rendercb, 0.1)
						self._svgplayer.play()
		self.update()

	def render(self, dc):
		if self._svgdoc is None: return
		l, t, r, b = self._adjrc
		self.renderSvgOffscreenOn(self._svgdoc, dc, (l, t, r-l, b-t))

	def renderSvgOn(self, svgdoc, hdc, dstrect):
		if svgdoc is None or not hdc: return
		import svgrender, svgwin
		svggraphics = svgwin.SVGWinGraphics()
		sw, sh = svgdoc.getSize()
		if sw and sh:
			dx, dy, dw, dh = dstrect
			sx, sy = dw/float(sw), dh/float(sh)
			svggraphics.applyTfList([('translate',[dx, dy]), ('scale',[sx, sy]),])
		svggraphics.tkStartup(hdc)
		renderer = svgrender.SVGRenderer(svgdoc, svggraphics)
		renderer.render()
		svggraphics.tkShutdown()

	def renderSvgOffscreenOn(self, svgdoc, dc, dstrect):
		if dc is None:
			try:
				dc = self._wnd.GetDC()
			except:
				return
			else:
				releaseDC = 1
		else:
			releaseDC = 0
		l, t, w, h = dstrect
		bmp = win32ui.CreateBitmap()
		try:
			bmp.CreateCompatibleBitmap(dc, w, h)
		except:
			print 'failed to create compatible bitmap'
			return
		dcc = dc.CreateCompatibleDC()
		dcc.OffsetViewportOrg((0, 0))
		dcc.SetWindowOrg((0,0))
		oldBitmap = dcc.SelectObject(bmp)
		dcc.FillSolidRect((0, 0, w, h), win32api.RGB(255,255,255))
		br=Sdk.CreateBrush(win32con.BS_SOLID,0,0)	
		dcc.FrameRectFromHandle((0, 0, w-1, h-1),br)
		Sdk.DeleteObject(br)
		self.renderSvgOn(svgdoc, dcc.GetSafeHdc(), (0, 0, w, h))
		dcc.SetViewportOrg((0, 0))
		dcc.SetWindowOrg((0,0))
		dcc.SetMapMode(win32con.MM_TEXT)
		dc.BitBlt((l,t),(w, h), dcc, (0, 0), win32con.SRCCOPY)
		dcc.SelectObject(oldBitmap)
		dcc.DeleteDC()
		del bmp
		if releaseDC:
			self._wnd.ReleaseDC(dc)

#################################
class HtmlRenderer(Renderer):
	def __init__(self,wnd,rc,baseURL=''):
		Renderer.__init__(self,wnd,rc,baseURL)
		self._htmlwnd=None
			
	def __del__(self):
		self.release()
	
	def release(self):
		if self._htmlwnd:
			self._htmlwnd.DestroyHtmlCtrl()
			self._htmlwnd.DestroyWindow()
			self._htmlwnd=None

	def isstatic(self):
		return 1

	def load(self,rurl):
		if not rurl:
			self.release()
			self.update()
			return
		url=self.urlqual(rurl)
		self.createHtmlWnd()
		if self._htmlwnd:	
			self._htmlwnd.Navigate(url)

	def createHtmlWnd(self):
		if self._htmlwnd: return
		self._htmlwnd=window.Wnd(win32ui.CreateHtmlWnd())
		self._brush=Sdk.CreateBrush(win32con.BS_SOLID,win32mu.RGB((255,255,255)),0)
		self._cursor=Afx.GetApp().LoadStandardCursor(win32con.IDC_ARROW)
		self._icon=0
		self._clstyle=0
		self._style=win32con.WS_CHILD | win32con.WS_CLIPSIBLINGS | win32con.WS_VISIBLE
		self._exstyle = 0 
		self._strclass=Afx.RegisterWndClass(self._clstyle,self._cursor,self._brush,self._icon)
		self._htmlwnd.CreateWindow(self._strclass,'untitled',self._style,
			self._rc,self._wnd,0)
		which =  settings.get('html_control')
		if not which: which = 0
		self._htmlwnd.UseHtmlCtrl(which)
		try:
			self._htmlwnd.CreateHtmlCtrl()
		except:
			msg = "Failed to create Browser control.\nCheck that the browser control you have selected is installed."
			win32dialog.showmessage(msg, parent=self._wnd._form)
		self._htmlwnd.SetWindowPos(0,self._rc,
			win32con.SWP_NOACTIVATE | win32con.SWP_NOSIZE)


#################################
class TextRenderer(Renderer):
	def __init__(self,wnd,rc,baseURL=''):
		Renderer.__init__(self,wnd,rc,baseURL)
		self._textwnd=None
			
	def __del__(self):
		self.release()
	
	def release(self):
		if self._textwnd:
			self._textwnd.DestroyWindow()
			self._textwnd=None

	def isstatic(self):
		return 1

	def load(self,rurl):
		if not rurl:
			self.release()
			self.update()
			return
		url=self.urlqual(rurl)
		f=self.urlretrieve(url)
		if not f or not self.isfile(f):
			self.release()
			self.update()
			return
		self.createTextWnd()
		if self._textwnd:
			fp = open(f, 'r')
			text = fp.read()
			fp.close()
			text = self.fixendl(text)
			self._textwnd.SetWindowText(text)
			self._textwnd.SendMessage(win32con.EM_SETREADONLY,1,0)

	def createTextWnd(self):
		if self._textwnd: return
		self._style=win32con.WS_CHILD | win32con.WS_CLIPSIBLINGS | win32con.WS_VISIBLE | win32con.WS_TABSTOP \
			| win32con.ES_MULTILINE | win32con.WS_VSCROLL | win32con.WS_HSCROLL
		self._exstyle = win32con.WS_EX_CONTROLPARENT| win32con.WS_EX_CLIENTEDGE
		self._strclass='EDIT'
		l,t,r,b=self._rc
		hwnd=Sdk.CreateWindowEx(self._exstyle,self._strclass,'',self._style,
			(l,t,r-l,b-t),self._wnd.GetSafeHwnd(),0)
		self._textwnd=window.Wnd(win32ui.CreateWindowFromHandle(hwnd))
		self._textwnd.SetWindowPos(0,self._rc,
			win32con.SWP_NOACTIVATE | win32con.SWP_NOSIZE)

	def fixendl(self,text):
		nl=string.split(text,'\n')
		rl=string.split(text,'\r')
		if len(nl)==len(rl):# line_separator='\r\n'
			return text
		if len(nl)>len(rl):	# line_separator='\n'
			return string.join(nl, '\r\n')
		if len(nl)<len(rl):	# line_separator='\r'
			return string.join(rl, '\r\n')


#################################
# DirectShow support
from win32dxm import GraphBuilder

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
			self._builder = GraphBuilder()
		except:
			self._builder=None

		if not self._builder:
			self.update()
			return
		url=self.urlqual(rurl)
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
		self._builder.Run()

	def pause(self):
		if not self._builder: return
		self._builder.Pause()

	def stop(self):
		if not self._builder: return
		self._builder.SetPosition(0)
		self._builder.Stop()

	def ismediaend(self):
		d=self._builder.GetDuration()
		t=self._builder.GetPosition()
		return t>=d


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
import winqt
import ddraw

class QtMediaRenderer(Renderer):
	def __init__(self,wnd,rc,baseURL=''):
		Renderer.__init__(self,wnd,rc,baseURL)
		self._player = None
		
		import __main__
		self._ostimer = __main__.toplevel
		self._timeresolution = 0.01
		self._timerid = None

		self._ddraw = None

	def __del__(self):
		self.release()
		self._clipper = None
		self._frontBuffer = None
		self._ddraw = None

	def isstatic(self):
		return 0

	def needswindow(self):
		return 1
			
	def release(self):
		if self._player:
			self.cancelTimer()
			self._player.stop()
			del self._player
			self._player = None

	def load(self,rurl):
		self.release()
		if winqt.HasQtSupport():
			self._player = winqt.QtPlayer()
		else:
			self.update()
			return

		import MMurl
		url = self.urlqual(rurl)
		try:
			fn = MMurl.urlretrieve(url)[0]
		except Exception, arg:
			print arg
			self._player = None
			if self.needswindow():
				self.update()
			return

		if not self._player.open(fn, asaudio = not self.needswindow()):
			self._player = None
			if self.needswindow():
				self.update()
			return

		if self.needswindow():
			if self._ddraw is None:
				hwnd = self._wnd._form.GetSafeHwnd()
				self._ddraw = ddraw.CreateDirectDraw()
				self._ddraw.SetCooperativeLevel(hwnd, ddraw.DDSCL_NORMAL)
		
				ddsd = ddraw.CreateDDSURFACEDESC()
				ddsd.SetFlags(ddraw.DDSD_CAPS)
				ddsd.SetCaps(ddraw.DDSCAPS_PRIMARYSURFACE)
				self._frontBuffer = self._ddraw.CreateSurface(ddsd)

				self._clipper = self._ddraw.CreateClipper(hwnd)
				self._frontBuffer.SetClipper(self._clipper)
				self._pxlfmt = self._frontBuffer.GetPixelFormat()

			videosize = self._player.getMovieRect()
			src_x, src_y, dest_x, dest_y, width, height,rcKeep = self.adjustSize(videosize[2:])
			self._player.setMovieRect((0, 0, width, height))
			self._player.createVideoDDS(self._ddraw)
			self._rc = dest_x, dest_y, width, height
			self._wnd.InvalidateRect(self._wnd.GetClientRect())
	
	def update(self):
		self._wnd.InvalidateRect(self.inflaterc(self._rc))

	def render(self, dc):
		if not self._player: 
			return
		if self.needswindow():
			x, y, w, h = self._rc
			if self._player._dds:
				dds = self._player._dds
				try:
					framehdc = dds.GetDC()
				except:
					print 'failed to get direct draw surface DC'
				else:
					framedc = win32ui.CreateDCFromHandle(framehdc)
					dc.BitBlt((x, y),(w, h), framedc, (0, 0), win32con.SRCCOPY)
					framedc.Detach()
					dds.ReleaseDC(framehdc)
			else:			
				br = Sdk.CreateBrush(win32con.BS_SOLID,0,0)	
				dc.FrameRectFromHandle((x, y, x + w, y + h), br)
				Sdk.DeleteObject(br)

	def play(self):
		if not self._player: return
		self.startTimer()
		self._player.run()

	def pause(self):
		if not self._player: return
		self.cancelTimer()
		self._player.stop()

	def stop(self):
		if not self._player: return
		self.cancelTimer()
		self._player.stop()
		self._player.seek(0)

	def ismediaend(self):
		d = self._player.getDuration()
		t = self._player.getTime()
		return t>=d

	def startTimer(self):
		if self._timerid is None:
			self._timerid = self._ostimer.settimer(self._timeresolution, (self.timerCallback, ()))

	def cancelTimer(self):
		if self._timerid is not None:
			self._ostimer.canceltimer(self._timerid)
			self._timerid = None
		
	def timerCallback(self):
		assert self._timerid is not None, 'timer protocol violation'
		self._timerid = None
		if self._player:
			running = self._player.update()
			if not running:
				self._player.stop()
			else:
				dc = self._wnd.GetDC()
				self.render(dc)
				self._wnd.ReleaseDC(dc)
				self._timerid = self._ostimer.settimer(self._timeresolution, (self.timerCallback, ()))

class QtVideoRenderer(QtMediaRenderer):
	def __init__(self,wnd,rc,baseURL=''):
		QtMediaRenderer.__init__(self,wnd,rc,baseURL)
	def needswindow(self):
		return 1

class QtAudioRenderer(QtMediaRenderer):
	def __init__(self,wnd,rc,baseURL=''):
		QtMediaRenderer.__init__(self,wnd,rc,baseURL)
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
		self._isstopped=0
		self._rurl=''

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
		self._rmaplayer = None
			
	def release(self):
		self._rmaplayer = None

	def isstatic(self):
		return 0

	def load(self,rurl):
		if self._rmaplayer and not self._isstopped:
			self._rmaplayer = None
		self._rurl=rurl
		self.do_init()
		if not self._rmaplayer:
			if self.needswindow():
				self.update()
			return
		if self.needswindow():
			self._rmaplayer.SetOsWindow(self._wnd.GetSafeHwnd())
		url=self.urlqual(rurl)
		import MMurl
		url = MMurl.canonURL(url)
		url = MMurl.unquote(url)
		self._rmaplayer.OpenURL(url)
		self._isstopped=0
		self._rmaplayer.SetStatusListener(self)

			
	def play(self):
		# play requires to recreate the player
		# in order to be confined
		if self._isstopped:
			self._rmaplayer = None
			self.load(self._rurl)
		if self._rmaplayer:
			self._isstopped=0
			self._rmaplayer.Begin()
			
	def pause(self):
		if self._rmaplayer:
			self._rmaplayer.Pause()

	def stop(self):
		if self._rmaplayer:
			self._rmaplayer.Stop()
			self._isstopped=1
					
	def OnStop(self):
		self._isstopped=1

	def ismediaend(self):
		return self._isstopped

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
		self.HookMessage(self.onFocus,win32con.WM_SETFOCUS)
		l,t,r,b=self.GetWindowRect()
		lr,tr,rr,br=self.GetParent().GetWindowRect()
		self._rectb = l-lr, t-tr, r-l, b-t
		self._box = None

	def onSize(self,params):
		if not self._box:
			x, y, w, h = self._rectb
			msg=win32mu.Win32Msg(params)
			wm, hm = msg.width(),msg.height()
			if wm>w or hm>h:
				scalex = w/float(wm)
				scaley = h/float(hm)
				if scalex < scaley: scale = scalex
				else: scale = scaley
				wm, hm = int(scale*wm+0.5), int(scale*hm+0.5)
			xm, ym = x + (w-wm)/2, y + (h-hm)/2
			self._box = xm, ym, wm, hm
		self.SetWindowPos(self.GetSafeHwnd(),self._box,
			win32con.SWP_NOACTIVATE | win32con.SWP_NOZORDER)

	# Fix strange rma focus attraction behavior
	# When the focus is set to the real window everything freezes
	def onFocus(self,params):
		self.GetParent().SetFocus()

#################################
class PreviewPage(AttrPage):
	dragaccept = 0
	def __init__(self,form,renderersig='null',aname='file'):
		AttrPage.__init__(self,form)
		self._prevrc=(20,20,100,100)
		self._aname=aname
		self._armed=0
		self._playing=0
		self._tid=0
		self._renderer = None
		if renderersig=='video':
			self._renderer=VideoRenderer(self,self._prevrc,self._form._baseURL)
		elif renderersig=='qtvideo':
			self._renderer=QtVideoRenderer(self,self._prevrc,self._form._baseURL)
		elif renderersig=='audio':
			self._renderer=AudioRenderer(self,self._prevrc,self._form._baseURL)
		elif renderersig=='qtaudio':
			self._renderer=QtAudioRenderer(self,self._prevrc,self._form._baseURL)
		elif renderersig=='realwnd':
			self._renderer=RealWndRenderer(self,self._prevrc,self._form._baseURL)
		elif renderersig=='realaudio':
			self._renderer=RealAudioRenderer(self,self._prevrc,self._form._baseURL)
		elif renderersig=='html':
			self._renderer=HtmlRenderer(self,self._prevrc,self._form._baseURL)
		elif renderersig=='text':
			self._renderer=TextRenderer(self,self._prevrc,self._form._baseURL)
		elif renderersig=='image':
			self._renderer=ImageRenderer(self,self._prevrc,self._form._baseURL)
		elif renderersig=='svg':
			self._renderer=SvgRenderer(self,self._prevrc,self._form._baseURL)
		else:
			self._renderer=Renderer(self,self._prevrc,self._form._baseURL)

	def OnInitDialog(self):
		if not AttrPage.OnInitDialog(self):
			return
		if PreviewPage.dragaccept:
			self.DragAcceptFiles(1)
			self.HookMessage(self.onDropFiles,win32con.WM_DROPFILES)
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
		self.OnStop()

	def OnSetActive(self):
		if self._initdialog and not self._armed:
			if self._renderer.isstatic():
				if self._renderer.needswindow():
					self.setRendererRc()
				c=self.getctrl(self._aname)
				rurl=string.strip(c.getvalue())
				self._renderer.load(rurl)
				self._armed=1
		return self._obj_.OnSetActive()

	def OnKillActive(self):
		if not self._renderer.isstatic() and self._playing:
			self.OnPause()
			c=self.getctrl(self._aname)
			c.setstate('pause')
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
		if not self._renderer.isstatic() and self._armed:
			self.canceltimer()
			self._renderer.stop()
			self._playing=0
			c=self.getctrl(self._aname)
			c.setstate('stop')
			self._renderer.release()
		self._armed = 0
##		c=self.getctrl(self._aname)
##		rurl=string.strip(c.getvalue())
##		self._renderer.load(rurl)
	
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
		self.settimer()

	def OnStop(self):
		if self._playing:
			self.canceltimer()
			self._renderer.stop()
			self._playing=0

	def OnPause(self):
		if self._playing:
			self.canceltimer()
			self._renderer.pause()
			self._playing=0

	def canceltimer(self):
		if self._tid:
			import __main__
			__main__.toplevel.canceltimer(self._tid)
			self._tid=0

	def settimer(self):
		self.canceltimer()
		import __main__
		self._tid=__main__.toplevel.settimer(1,(self.checkmediaend,()))

	def checkmediaend(self):
		self._tid=0
		if not self._renderer.isstatic():
			if self._renderer.ismediaend():
				self.OnStop()
				c=self.getctrl(self._aname)
				c.setstate('stop')
			else:
				self.settimer()

	# response to drop files
	def onDropFiles(self,params):
		ctrl=self.getctrl(self._aname)
		if not self._renderer.isstatic():
			self.canceltimer()
			self.OnStop()
			ctrl.setstate('stop')
		msg=win32mu.Win32Msg(params)	
		hDrop=msg._wParam
		inclient,point=Sdk.DragQueryPoint(hDrop)
		if inclient and hasattr(ctrl._attr,'setpathname'):
			filename=win32api.DragQueryFile(hDrop,0)
			ctrl._attr.setpathname(filename)
		win32api.DragFinish(hDrop)


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

class SvgPreviewPage(PreviewPage):
	def __init__(self,form):
		PreviewPage.__init__(self, form,'svg')	
	def OnDestroy(self,params):
		if self._renderer and self._renderer._svgplayer:
			self._renderer._svgplayer.stop()
			self._renderer._svgplayer = None

class VideoPreviewPage(PreviewPage):
	def __init__(self,form):
		PreviewPage.__init__(self, form,'video')	

class QtVideoPreviewPage(PreviewPage):
	def __init__(self,form):
		PreviewPage.__init__(self, form,'qtvideo')	

class AudioPreviewPage(PreviewPage):
	def __init__(self,form):
		PreviewPage.__init__(self, form,'audio')
			
class QtAudioPreviewPage(PreviewPage):
	def __init__(self,form):
		PreviewPage.__init__(self, form,'qtaudio')	

class RealAudioPreviewPage(PreviewPage):
	def __init__(self,form):
		PreviewPage.__init__(self, form,'realaudio')	

class RealWndPreviewPage(PreviewPage):
	def __init__(self,form):
		PreviewPage.__init__(self, form,'realwnd')
			
class HtmlPreviewPage(PreviewPage):
	def __init__(self,form):
		PreviewPage.__init__(self, form,'html')	

class TextPreviewPage(PreviewPage):
	def __init__(self,form):
		PreviewPage.__init__(self, form,'text')	

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

	def dont_show_anything(self):
		for attr in self._al:
			if attr.mustshow():
				return 0
		return 1

	def alnames(self):
		l=[]
		for a in self._al:
			l.append(a.getname())
		return l

	def getattr(self,aname):
		return self._al[0].attreditor._findattr(aname)

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
		}

	def getctrlclass(self,a):
		n = a.getname()
		if AttrGroup.special_attrcl.has_key(n):
			return AttrGroup.special_attrcl[n]
		t = a.gettype()
		if t=='option':return OptionsCtrl
		elif t=='bool': return OptionsCheckCtrl
		elif t=='file': return FileCtrl
		elif t=='color': return ColorCtrl
		else: return StringCtrl
	
	# part of page initialization
	# do whatever not default
	def oninitdialog(self,wnd):
		pass

	# resize labels and attr editors
	def resizelabels(self,wnd, labels, attrctrls, dw):
		hwnd = wnd.GetSafeHwnd()
		l,t,r,b = wnd.GetWindowRect()
		flags = win32con.SWP_NOACTIVATE | win32con.SWP_NOZORDER
		for id in attrctrls:
			ctrl=components.Control(wnd,id)
			ctrl.attach_to_parent()
			l1,t1,r1,b1=ctrl.getwindowrect()
			rc = l1-l+dw,t1-t, r1-l1-dw,b1-t1
			ctrl.setwindowpos(hwnd,rc,flags)
		for id in labels:
			ctrl=components.Control(wnd,id)
			ctrl.attach_to_parent()
			l1,t1,r1,b1=ctrl.getwindowrect()
			rc = l1-l,t1-t, r1-l1+dw,b1-t1
			ctrl.setwindowpos(hwnd,rc,flags)
	
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

class StringGroupNoTitle(StringGroup):
	def oninitdialog(self,wnd):
		ctrl=components.Control(wnd,grinsRC.IDC_GROUP1)
		ctrl.attach_to_parent()
		ctrl.settext('')

class InfoGroup(StringGroup):
	data=attrgrsdict['infogroup']

class DocInfoGroup(StringGroup):
	data=attrgrsdict['docinfo']

class InfoFileGroup(StringGroup):
	data=attrgrsdict['infofilegroup']

	def getpageresid(self):
		return grinsRC.IDD_EDITATTR_S7F

	def createctrls(self,wnd):
		cd={}
		for ix in range(len(self._al)-1):
			a=self._al[ix]
			cd[a]=StringCtrl(wnd,a,self.getctrlids(ix+1))
		a = self.getattr('file')
		cd[a] = FileCtrl(wnd, a, (grinsRC.IDC_81, grinsRC.IDC_82, grinsRC.IDC_83,))
		return cd

class InfoFile1Group(InfoFileGroup):
	data=attrgrsdict['infofile1group']

	def getpageresid(self):
		return grinsRC.IDD_EDITATTR_S4F

class QTPlayerPreferencesGroup(AttrGroup):
	data=attrgrsdict['qtpreferences']

	def __init__(self,data = None):
		AttrGroup.__init__(self,data or self.data)

	def createctrls(self,wnd):
		cd={}
		a = self.getattr('autoplay')
		cd[a] = OptionsCheckNolabelCtrl(wnd,a,(grinsRC.IDC_AUTOPLAY,))
		a = self.getattr('qtchaptermode')
		cd[a] = OptionsRadioNolabelCtrl(wnd,a,(grinsRC.IDC_QTCHAPTERLABEL,grinsRC.IDC_QTCHAPTERMODE1,grinsRC.IDC_QTCHAPTERMODE2))
		a = self.getattr('qttimeslider')
		cd[a] = OptionsCheckNolabelCtrl(wnd,a,(grinsRC.IDC_QTTIMESLIDER,))
		a = self.getattr('qtnext')
		cd[a] = FileCtrl(wnd,a,(grinsRC.IDC_QTNEXTLABEL,grinsRC.IDC_FIELD_QTNEXT,grinsRC.IDC_BUTTON_QTNEXT))
		a = self.getattr('immediateinstantiation')
		cd[a] = OptionsCheckNolabelCtrl(wnd,a,(grinsRC.IDC_IMMINST,))
		return cd

	def getpageresid(self):
		return grinsRC.IDD_EDITATTR_QTPREF

#	def oninitdialog(self,wnd):
#		ctrl=components.Control(wnd,grinsRC.IDC_GROUP1)
#		ctrl.attach_to_parent()
#		ctrl.settext(self._data['title'])

class QTPlayerMediaPreferencesGroup(AttrGroup):
	data=attrgrsdict['qtmediapreferences']

	def __init__(self,data = None):
		AttrGroup.__init__(self,data or self.data)

	def createctrls(self,wnd):
		cd={}
		a = self.getattr('immediateinstantiationmedia')
		cd[a] = OptionsRadioNolabelCtrl(wnd,a,(grinsRC.IDC_IMMINSTLABEL, grinsRC.IDC_IMMINSTMEDIA1, grinsRC.IDC_IMMINSTMEDIA2, grinsRC.IDC_IMMINSTMEDIA3))
		a = self.getattr('bitratenecessary')
		cd[a] = OptionsNolabelCtrl(wnd,a,(grinsRC.IDC_BITRATELABEL, grinsRC.IDC_BITRATENECESSARY))
		a = self.getattr('systemmimetypesupported')
		cd[a] = StringNolabelCtrl(wnd,a,(grinsRC.IDC_SYSTEMMIMELABEL, grinsRC.IDC_SYSTEMMIMETYPE,))	
		a = self.getattr('attachtimebase')
		cd[a] = OptionsCheckNolabelCtrl(wnd,a,(grinsRC.IDC_ATTACHTIMEBASE,))
		a = self.getattr('qtchapter')
		cd[a] = StringNolabelCtrl(wnd,a,(grinsRC.IDC_QTCHAPTERLABEL, grinsRC.IDC_QTCHAPTER,))	
		a = self.getattr('qtcompositemode')
		cd[a] = StringNolabelCtrl(wnd,a,(grinsRC.IDC_QTCOMPOSITELABEL, grinsRC.IDC_QTCOMPOSITEMODE,))	
		return cd

	def getpageresid(self):
		return grinsRC.IDD_EDITATTR_QTMEDIAPREF

class Misc2Group(AttrGroup):
	data=attrgrsdict['miscellaneous2']
	def __init__(self,data = None):
		AttrGroup.__init__(self, self.data)

	def getpageresid(self):
		return grinsRC.IDD_EDITATTR_REALEXTENSION

	def createctrls(self, wnd):
		cd = {}
		a = self.getattr('backgroundOpacity')
		cd[a] = StringNolabelCtrl(wnd,a,(grinsRC.IDC_BGOL, grinsRC.IDC_BGOV,))
		a = self.getattr('mediaOpacity')
		cd[a] = StringNolabelCtrl(wnd,a,(grinsRC.IDC_MDOL, grinsRC.IDC_MDOV,))
		a = self.getattr('chromaKey')
		cd[a] = ColorNolabelCtrl(wnd,a,(grinsRC.IDC_CKEYL,grinsRC.IDC_CKEYV,grinsRC.IDC_CKEYB))
		a = self.getattr('chromaKeyOpacity')
		cd[a] = StringNolabelCtrl(wnd,a,(grinsRC.IDC_CKOL, grinsRC.IDC_CKOV,))
		a = self.getattr('chromaKeyTolerance')
		cd[a] = IntTupleNolabelCtrl(wnd,a,(grinsRC.IDC_CKTL, grinsRC.IDC_CKTV1, grinsRC.IDC_CKTV2, grinsRC.IDC_CKTV3,))
		a = self.getattr('reliable')
		cd[a] = OptionsCheckNolabelCtrl(wnd,a,(grinsRC.IDC_RELIABLE,))
		a = self.getattr('sensitivity')
		cd[a] = StringNolabelCtrl(wnd,a,(grinsRC.IDC_SENSITIVITYL, grinsRC.IDC_SENSITIVITYV,))
		return cd

class MiscGroup(Misc2Group):
	data=attrgrsdict['miscellaneous']

	def getpageresid(self):
		return grinsRC.IDD_EDITATTR_REALEXTENSION2

	def createctrls(self, wnd):
		cd = Misc2Group.createctrls(self, wnd)
		a = self.getattr('strbitrate')
		cd[a] = StringNolabelCtrl(wnd,a,(grinsRC.IDC_BITRL, grinsRC.IDC_BITRV,))
		return cd

class PrioGroup(AttrGroup):
	data=attrgrsdict['prio']

	def __init__(self):
		AttrGroup.__init__(self,self.data)

	def getpageresid(self):
		return grinsRC.IDD_EDITATTR_PRIO

	def createctrls(self,wnd):
		cd = {}
		a = self.getattr('higher')
		cd[a] = OptionsRadioNolabelCtrl(wnd,a,(grinsRC.IDC_HIGHERL,grinsRC.IDC_HIGHERV1,grinsRC.IDC_HIGHERV2))
		a = self.getattr('peers')
		cd[a] = OptionsRadioNolabelCtrl(wnd,a,(grinsRC.IDC_PEERSL,grinsRC.IDC_PEERSV1,grinsRC.IDC_PEERSV2,grinsRC.IDC_PEERSV3,grinsRC.IDC_PEERSV4))
		a = self.getattr('lower')
		cd[a] = OptionsRadioNolabelCtrl(wnd,a,(grinsRC.IDC_LOWERL,grinsRC.IDC_LOWERV1,grinsRC.IDC_LOWERV2))
		a = self.getattr('pauseDisplay')
		cd[a] = OptionsRadioNolabelCtrl(wnd,a,(grinsRC.IDC_PAUSEL,grinsRC.IDC_PAUSEV1,grinsRC.IDC_PAUSEV2,grinsRC.IDC_PAUSEV3))
		return cd

class ServerGroup(StringGroup):
	data=attrgrsdict['server']

	def getpageresid(self):
		return grinsRC.IDD_EDITATTR_SERVER

	# override these two to not change any labels
	def createctrls(self,wnd):
		cd={}
		for ix in range(len(self._al)):
			a=self._al[ix]
			cd[a]=StringNolabelCtrl(wnd,a,self.getctrlids(ix+1))
		return cd

	def oninitdialog(self,wnd):
		pass

class WebserverGroup(StringGroup):
	data=attrgrsdict['webserver']

class MediaserverGroup(StringGroup):
	data=attrgrsdict['mediaserver']

class DurationGroup(StringGroup):
	data=attrgrsdict['timing1']
	
class ClipGroup(StringGroup):
	data=attrgrsdict['clip']
	def getpageresid(self):
		return grinsRC.IDD_EDITATTR_S2a
	def oninitdialog(self,wnd):pass

class BandwidthGroup(StringGroup):
	data=attrgrsdict['bandwidth']
	def oninitdialog(self,wnd):
		ctrl=components.Control(wnd,grinsRC.IDC_GROUP1)
		ctrl.attach_to_parent()
		ctrl.settext('')

class DurationSBGroup(StringGroup):
	data=attrgrsdict['timingsb']

class Duration2Group(AttrGroup):
	data=attrgrsdict['timing2']

	def __init__(self):
		AttrGroup.__init__(self,self.data)

	def getpageresid(self):
		return grinsRC.IDD_EDITATTR_T2

	def createctrls(self,wnd):
		cd = {}
		a = self.getattr('tag')
		cd[a] = OptionsNolabelCtrl(wnd,a,(grinsRC.IDC_11,grinsRC.IDC_12))
		a = self.getattr('start')
		cd[a] = StringNolabelCtrl(wnd,a,(grinsRC.IDC_21,grinsRC.IDC_22))
		return cd

class Duration3Group(Duration2Group):
	data=attrgrsdict['timing3']

	def getpageresid(self):
		return grinsRC.IDD_EDITATTR_T3

	def createctrls(self,wnd):
		cd = Duration2Group.createctrls(self,wnd)
		a = self.getattr('tduration')
		cd[a] = StringNolabelCtrl(wnd,a,(grinsRC.IDC_31,grinsRC.IDC_32))
		return cd

class Duration3cGroup(Duration2Group):
	data=attrgrsdict['timing3c']

	def getpageresid(self):
		return grinsRC.IDD_EDITATTR_T3C

	def createctrls(self,wnd):
		cd = Duration2Group.createctrls(self,wnd)
		a = self.getattr('color')
		cd[a] = ColorNolabelCtrl(wnd,a,(grinsRC.IDC_31,grinsRC.IDC_32,grinsRC.IDC_33))
		return cd

class Duration4Group(Duration3Group):
	data=attrgrsdict['timing4']

	def getpageresid(self):
		return grinsRC.IDD_EDITATTR_T4

	def createctrls(self,wnd):
		cd = Duration3Group.createctrls(self,wnd)
		a = self.getattr('color')
		cd[a] = ColorNolabelCtrl(wnd,a,(grinsRC.IDC_41,grinsRC.IDC_42,grinsRC.IDC_43))
		return cd

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

class SynchronizationGroup(AttrGroup):
	data=attrgrsdict['synchronization']
	def __init__(self):
		AttrGroup.__init__(self,self.data)

	def getpageresid(self):
		return grinsRC.IDD_EDITATTR_SYNC

	def createctrls(self,wnd):
		cd = {}
		a = self.getattr('syncMaster')
		cd[a] = OptionsCheckNolabelCtrl(wnd,a,(grinsRC.IDC_1,))
		a = self.getattr('syncBehavior')
		cd[a] = OptionsNolabelCtrl(wnd,a,(grinsRC.IDC_21, grinsRC.IDC_22))
		a = self.getattr('syncBehaviorDefault')
		cd[a] = OptionsNolabelCtrl(wnd,a,(grinsRC.IDC_31, grinsRC.IDC_32))
		a = self.getattr('syncTolerance')
		cd[a] = StringNolabelCtrl(wnd,a,(grinsRC.IDC_41, grinsRC.IDC_42))
		a = self.getattr('syncToleranceDefault')
		cd[a] = StringNolabelCtrl(wnd,a,(grinsRC.IDC_51, grinsRC.IDC_52))
		return cd
	
# base_winoff
class LayoutGroup(AttrGroup):
	data=attrgrsdict['base_winoff']
	def __init__(self,data=None):
		AttrGroup.__init__(self,self.data)

	def getpageresid(self):
		return grinsRC.IDD_EDITATTR_LS1

	def createctrls(self,wnd):
		cd={}
		a=self.getattr('base_winoff')
		cd[a]=FloatTupleCtrl(wnd,a,(grinsRC.IDC_11,grinsRC.IDC_12,grinsRC.IDC_13,grinsRC.IDC_14,grinsRC.IDC_15))
		a=self.getattr('z')
		cd[a]=StringNolabelCtrl(wnd,a,(grinsRC.IDC_21,grinsRC.IDC_22))
		return cd

	def getpageclass(self):
		return LayoutPage

	def islayoutattr(self,attr):
		return (attr.getname()=='base_winoff')

# base_winoff, units
class LayoutGroupWithUnits(LayoutGroup):
	data=attrgrsdict['base_winoff_and_units']
	def getpageresid(self):
		return grinsRC.IDD_EDITATTR_LS1O1

	def createctrls(self,wnd):
		cd={}
		a=self.getattr('base_winoff')
		cd[a]=FloatTupleNolabelCtrl(wnd,a,(grinsRC.IDC_11,grinsRC.IDC_12,grinsRC.IDC_13,grinsRC.IDC_14,grinsRC.IDC_15))
		a=self.getattr('units')
		cd[a]=OptionsNolabelCtrl(wnd,a,(grinsRC.IDC_21,grinsRC.IDC_22))
		a=self.getattr('z')
		cd[a]=StringNolabelCtrl(wnd,a,(grinsRC.IDC_31,grinsRC.IDC_32))
		return cd

class ImgregionGroup(AttrGroup):
	data=attrgrsdict['imgregion']
	_attrnames = {'xy':'imgcropxy',
		      'wh':'imgcropwh',
		      'full':'fullimage',
		      }
	__convert = None		# default

	def __init__(self):
		AttrGroup.__init__(self,self.data)

	def getpageresid(self):
		return grinsRC.IDD_EDITATTR_LS1O2

	def createctrls(self,wnd):
		cd={}
		a=self.getattr(self._attrnames['xy'])
		cd[a]=FloatTupleNolabelCtrl(wnd,a,(grinsRC.IDC_11,grinsRC.IDC_12,grinsRC.IDC_13))
		a=self.getattr(self._attrnames['wh'])
		cd[a]=FloatTupleNolabelCtrl(wnd,a,(grinsRC.IDC_11,grinsRC.IDC_14,grinsRC.IDC_15))
		a=self.getattr(self._attrnames['full'])
		cd[a]=OptionsCheckNolabelCtrl(wnd,a,(grinsRC.IDC_21,))
		if self._attrnames.has_key('anchor'):
			a=self.getattr(self._attrnames['anchor'])
			cd[a]=OptionsNolabelCtrl(wnd,a,(grinsRC.IDC_31,grinsRC.IDC_32))
		if 'project_convert' in self._data['attrs']:
			a=self.getattr('project_convert')
			cd[a]=OptionsCheckNolabelCtrl(wnd,a,(grinsRC.IDC_61,))
			self.__convert = cd[a]
			self.__cd = cd
		return cd

	def oninitdialog(self,wnd):
		ctrl=components.Control(wnd,grinsRC.IDC_11)
		ctrl.attach_to_parent()
		ctrl.settext(self._data['title'])
		if self.__convert is not None:
			self.__convert._check.hookcommand(wnd, self.__onconvert)

	def __onconvert(self, id, code):
		if code == win32con.BN_CLICKED:
			check = self.__convert._check.getcheck()
			a = self.getattr('project_quality')
			if a is not None:
				self.__cd[a].enable(check)
			self.__convert.enableApply()

	def getpageclass(self):
		return SubImgLayoutPage

	def islayoutattr(self,attr):
		return attr.getname() in (self._attrnames['xy'], self._attrnames['wh'])

class Subregion2Group(ImgregionGroup):
	data=attrgrsdict['subregion2']
	_attrnames = {'xy':'subregionxy',
		      'wh':'subregionwh',
		      'full':'displayfull',
		      }

	def getpageresid(self):
		return grinsRC.IDD_EDITATTR_LS1O3b

	def getpageclass(self):
		return PosSizeLayoutPage

class Subregion1Group(Subregion2Group):
	data=attrgrsdict['subregion1']

	def getpageresid(self):
		return grinsRC.IDD_EDITATTR_LS1O3a

	def createctrls(self,wnd):
		cd = Subregion2Group.createctrls(self,wnd)
		a = self.getattr('aspect')
		cd[a]=OptionsCheckNolabelCtrl(wnd,a,(grinsRC.IDC_41,))
		a = self.getattr('project_quality')
		cd[a]=OptionsNolabelCtrl(wnd,a,(grinsRC.IDC_51,grinsRC.IDC_52))
		return cd

class SubregionGroup(Subregion1Group):
	data=attrgrsdict['subregion']
	_attrnames = {'xy':'subregionxy',
		      'wh':'subregionwh',
		      'full':'displayfull',
		      }

	def getpageresid(self):
		return grinsRC.IDD_EDITATTR_LS1O3

class TransitionGroup(AttrGroup):
	data=attrgrsdict['transition']
	def __init__(self):
		AttrGroup.__init__(self,self.data)

	def getpageresid(self):
		return grinsRC.IDD_EDITATTR_TRANSITION

	def createctrls(self,wnd):
		cd = {}
		a = self.getattr('transIn')
		cd[a] = TransitionCtrl(wnd,a,(grinsRC.IDC_11, grinsRC.IDC_12, grinsRC.IDC_13))
		a = self.getattr('transOut')
		cd[a] = TransitionCtrl(wnd,a,(grinsRC.IDC_21, grinsRC.IDC_22, grinsRC.IDC_23))
		return cd

	def getpageclass(self):
		return AttrPage

class SnapSystemGroup(AttrGroup):
	data=attrgrsdict['snapsystem']
	def __init__(self):
		AttrGroup.__init__(self,self.data)

	def getpageresid(self):
		return grinsRC.IDD_EDITATTR_O2

	def createctrls(self,wnd):
		cd = {}
		a = self.getattr('system_bitrate')
		cd[a] = OptionsNolabelCtrl(wnd,a,(grinsRC.IDC_11, grinsRC.IDC_12))
		a = self.getattr('system_language')
		cd[a] = OptionsNolabelCtrl(wnd,a,(grinsRC.IDC_21, grinsRC.IDC_22))
		return cd

	def getpageclass(self):
		return AttrPage

class PreferencesGroup(SnapSystemGroup):
	data=attrgrsdict['preferences']
	nodefault = 1

	def getpageresid(self):
		return grinsRC.IDD_EDITATTR_S1R3S4

	def createctrls(self,wnd):
		cd = SnapSystemGroup.createctrls(self,wnd)
		a = self.getattr('system_captions')
		if self.nodefault:
			resids = (grinsRC.IDC_31,grinsRC.IDC_32,grinsRC.IDC_33)
		else:
			resids = (grinsRC.IDC_31,grinsRC.IDC_32,grinsRC.IDC_33,grinsRC.IDC_34x)
		cd[a] = OptionsRadioNolabelCtrl(wnd,a,resids)
		a = self.getattr('system_overdub_or_caption')
		if self.nodefault:
			resids = (grinsRC.IDC_41,grinsRC.IDC_42,grinsRC.IDC_43)
		else:
			resids = (grinsRC.IDC_41,grinsRC.IDC_42,grinsRC.IDC_43,grinsRC.IDC_44)
		cd[a] = OptionsRadioNolabelCtrl(wnd,a,resids)
		return cd

class Preferences2Group(PreferencesGroup):
	data=attrgrsdict['preferences2']

	def getpageresid(self):
		return grinsRC.IDD_EDITATTR_S1R3S7

	def createctrls(self,wnd):
		cd = PreferencesGroup.createctrls(self, wnd)
		a = self.getattr('system_audiodesc')
		resids = (grinsRC.IDC_SAUDIODESCL,grinsRC.IDC_SAUDIODESCV1,grinsRC.IDC_SAUDIODESCV2)
		cd[a] = OptionsRadioNolabelCtrl(wnd,a,resids)
		a = self.getattr('showhidden')
		resids = (grinsRC.IDC_SHOWHIDDENL,grinsRC.IDC_SHOWHIDDENV1,grinsRC.IDC_SHOWHIDDENV2)
		cd[a] = OptionsRadioNolabelCtrl(wnd,a,resids)
		return cd

class PreferencesProGroup(AttrGroup):
	data = attrgrsdict['preferencesPro']

	def __init__(self):
		AttrGroup.__init__(self, self.data)

	def getpageresid(self):
		return grinsRC.IDD_EDITATTR_PREFPRO

	def createctrls(self, wnd):
		cd = {}
		a = self.getattr('default_sync_behavior_locked')
		cd[a] = OptionsCheckCtrl(wnd, a, (grinsRC.IDC_1,))
		a = self.getattr('default_sync_tolerance')
		resids = (grinsRC.IDC_TOLLABEL, grinsRC.IDC_TOLVALUE)
		cd[a] = StringCtrl(wnd, a, resids)
		a = self.getattr('enable_template')
		cd[a] = OptionsCheckCtrl(wnd, a, (grinsRC.IDC_2,))
		a = self.getattr('saveopenviews')
		cd[a] = OptionsCheckCtrl(wnd, a, (grinsRC.IDC_3,))
		a = self.getattr('initial_dialog')
		cd[a] = OptionsCheckCtrl(wnd, a, (grinsRC.IDC_4,))
		return cd

	def getpageclass(self):
		return AttrPage
				

class SystemGroup(PreferencesGroup):
	data=attrgrsdict['system']
	nodefault = 0
	def getpageresid(self):
		return grinsRC.IDD_EDITATTR_S1R3S5

	def createctrls(self,wnd):
		cd = PreferencesGroup.createctrls(self,wnd)
		a = self.getattr('system_required')
		cd[a] = StringNolabelCtrl(wnd,a,(grinsRC.IDC_51,grinsRC.IDC_52))
		a = self.getattr('system_screen_depth')
		cd[a] = StringNolabelCtrl(wnd,a,(grinsRC.IDC_61,grinsRC.IDC_62))
		a = self.getattr('system_screen_size')
		cd[a] = StringNolabelCtrl(wnd,a,(grinsRC.IDC_71,grinsRC.IDC_72))
		return cd

class SystemGroup3(SnapSystemGroup):
	data=attrgrsdict['system3']
	nodefault = 0
	def getpageresid(self):
		return grinsRC.IDD_EDITATTR_S1R3S8

	def createctrls(self,wnd):
		cd = SnapSystemGroup.createctrls(self,wnd)
		a = self.getattr('system_captions')
		cd[a] = OptionsRadioNolabelCtrl(wnd,a,(grinsRC.IDC_31,grinsRC.IDC_32,grinsRC.IDC_33,grinsRC.IDC_34x), (grinsRC.IDC_GROUP3,))
		a = self.getattr('system_required')
		cd[a] = StringNolabelCtrl(wnd,a,(grinsRC.IDC_51,grinsRC.IDC_52))
		a = self.getattr('system_screen_depth')
		cd[a] = StringNolabelCtrl(wnd,a,(grinsRC.IDC_61,grinsRC.IDC_62), (grinsRC.IDC_GROUP7,))
		# different system screen crtl than SystemGroup
		a = self.getattr('system_screen_size')
		cd[a] = SystemScreenSizeCtrl(wnd,a,(grinsRC.IDC_GROUP8, grinsRC.IDC_WIDTHV,grinsRC.IDC_HEIGHTV))
		a = self.getattr('system_operating_system')
		cd[a] = OptionsNolabelCtrl(wnd,a,(grinsRC.IDC_SOPERATINGSYSTEML,grinsRC.IDC_SOPERATINGSYSTEMV))
		a = self.getattr('system_cpu')
		cd[a] = OptionsNolabelCtrl(wnd,a,(grinsRC.IDC_SCPUL,grinsRC.IDC_SCPUV))
		a = self.getattr('system_component')
		cd[a] = StringNolabelCtrl(wnd,a,(grinsRC.IDC_SCOMPONENTL,grinsRC.IDC_SCOMPONENTV))
		a = self.getattr('system_audiodesc')
		cd[a] = OptionsRadioNolabelCtrl(wnd,a,(grinsRC.IDC_SAUDIODESCL,grinsRC.IDC_SAUDIODESCV1, grinsRC.IDC_SAUDIODESCV2, grinsRC.IDC_SAUDIODESCV3), (grinsRC.IDC_GROUP6,))
		a = self.getattr('system_overdub_or_caption')
		cd[a] = OptionsRadioNolabelCtrl(wnd,a,(grinsRC.IDC_DUBSUBL,grinsRC.IDC_42,grinsRC.IDC_43,grinsRC.IDC_44), (grinsRC.IDC_GROUP2,))
		return cd

class SystemGroup2(SystemGroup3):
	data=attrgrsdict['system2']
	def getpageresid(self):
		return grinsRC.IDD_EDITATTR_S1R3S6

	def createctrls(self,wnd):
		cd = SystemGroup3.createctrls(self,wnd)
		a = self.getattr('u_group')
		cd[a] = StringNolabelCtrl(wnd,a,(grinsRC.IDC_SCUSTOMTESTSL,grinsRC.IDC_SCUSTOMTESTSV))
		return cd

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


class CNameGroup(StringGroup):
	data=attrgrsdict['.cname']

class CNameGroup2(StringGroup):
	data=attrgrsdict['.cname2']

class INameGroup(NameGroup):
	data=attrgrsdict['intname']
	def getpageresid(self):
		return grinsRC.IDD_EDITATTR_S1O2

class GeneralGroup(AttrGroup):
	data=attrgrsdict['general']
	def __init__(self):
		AttrGroup.__init__(self, self.data)
	def getpageresid(self):
		return grinsRC.IDD_EDITATTR_GENERAL
	def createctrls(self,wnd):
		cd = {}
		a = self.getattr('name')
		cd[a] = StringNolabelCtrl(wnd,a,(grinsRC.IDC_11,grinsRC.IDC_12))
##		a = self.getattr('.type')
##		cd[a] = OptionsNolabelCtrl(wnd,a,(grinsRC.IDC_21,grinsRC.IDC_22))
		a = self.getattr('title')
		cd[a] = StringNolabelCtrl(wnd,a,(grinsRC.IDC_31,grinsRC.IDC_32))
		a = self.getattr('alt')
		cd[a] = StringNolabelCtrl(wnd,a,(grinsRC.IDC_41,grinsRC.IDC_42))
		a = self.getattr('author')
		cd[a] = StringNolabelCtrl(wnd,a,(grinsRC.IDC_51,grinsRC.IDC_52))
		a = self.getattr('copyright')
		cd[a] = StringNolabelCtrl(wnd,a,(grinsRC.IDC_61,grinsRC.IDC_62))
		a = self.getattr('.begin1')
		cd[a] = StringNolabelCtrl(wnd,a,(grinsRC.IDC_71,grinsRC.IDC_72))
		a = self.getattr('duration')
		cd[a] = StringNolabelCtrl(wnd,a,(grinsRC.IDC_81,grinsRC.IDC_82))
		return cd

class FileGroup(AttrGroup):
	data=attrgrsdict['file']
	def __init__(self):
		AttrGroup.__init__(self,FileGroup.data)
		self._preview=-1

	def isStaticMedia(self, mtype):
		return mtype in ('image', 'svg', 'html', 'text')
	
	def canpreview(self):
		if self._preview>=0: 
			return self._preview
		self._preview=0 # init to no preview
		a=self.getattr('file')
		f=a.getcurrent()
		from winversion import osversion
		import urlcache
		mtype = urlcache.mimetype(f)
		if mtype is None: 
			return 0
		mtype, subtype = string.split(mtype, '/')
		# create media type sig for renderer
		if mtype=='image':
			if subtype == 'svg-xml':
				mtype='svg'	
				self._preview = osversion.isNT()
			else:				
				if string.find(subtype,'realpix')>=0:
					mtype='realwnd'
				self._preview=1
		elif mtype=='video':
			if string.find(subtype,'realvideo')>=0:
				mtype='realwnd'
			elif string.find(subtype,'quicktime')>=0:
				mtype='qtvideo'
			self._preview=1
		elif mtype=='audio':
			if string.find(subtype,'realaudio')>=0:
				mtype='realaudio'
			if string.find(subtype,'x-aiff')>=0 or string.find(subtype,'quicktime')>=0:
				mtype='qtaudio'
			self._preview=1
		elif mtype=='text':
			if subtype=='html':
				mtype='html'
				self._preview=1
			elif subtype=='plain':
				mtype='text'
				self._preview=1
			elif string.find(subtype,'realtext')>=0:
				mtype='realwnd'
				self._preview=1	
		elif mtype == 'application':
			if string.find(subtype,'real')>=0:
				self._preview=1
				mtype='realwnd'
			elif subtype == 'x-shockwave-flash':
				self._preview=1
				mtype='realwnd'
		self._mtypesig=mtype
		return self._preview

	def getpageresid(self):
		if self.canpreview():
			if self.isStaticMedia(self._mtypesig): 
				# static media
				return grinsRC.IDD_EDITATTR_PF1
			else: 
				# continous media i.e play,stop
				return grinsRC.IDD_EDITATTR_MF1	
		else:
			return grinsRC.IDD_EDITATTR_F1

	def getpageclass(self):
		if not self.canpreview():
			return AttrPage
		if self._mtypesig=='image':
			return ImagePreviewPage
		elif self._mtypesig=='svg':
			return SvgPreviewPage
		elif self._mtypesig=='html':
			return HtmlPreviewPage
		elif self._mtypesig=='video':
			return VideoPreviewPage
		elif self._mtypesig=='qtvideo':
			return QtVideoPreviewPage
		elif self._mtypesig=='audio':
			return AudioPreviewPage
		elif self._mtypesig=='qtaudio':
			return QtAudioPreviewPage
		elif self._mtypesig=='realwnd':
			return RealWndPreviewPage
		elif self._mtypesig=='realaudio':
			return RealAudioPreviewPage
		elif self._mtypesig=='text':
			return TextPreviewPage
		else:
			return PreviewPage

	def createctrls(self,wnd):
		cd={}
		a=self.getattr('file')
		if not self.canpreview():
			cd[a]=FileCtrl(wnd,a,(grinsRC.IDC_1,grinsRC.IDC_2,grinsRC.IDC_3))

		elif self._mtypesig in ('image', 'svg', 'html', 'text'):
			# static media
			cd[a]=FileCtrl(wnd,a,(grinsRC.IDC_1,grinsRC.IDC_2,grinsRC.IDC_3))

		else:
			# continous media
			cd[a]=FileMediaCtrl(wnd,a,(grinsRC.IDC_1,grinsRC.IDC_2,grinsRC.IDC_3,
				grinsRC.IDC_4,grinsRC.IDC_5,grinsRC.IDC_6))
		return	cd

class MediaGroup(FileGroup):
	data=attrgrsdict['media']
	def __init__(self):
		AttrGroup.__init__(self,MediaGroup.data)
		self._preview=-1

	def getpageresid(self):
		if self.canpreview():
			if self.isStaticMedia(self._mtypesig): 
				# static media
				return grinsRC.IDD_EDITATTR_PF2
			else: 
				# continous media i.e play,stop
				return grinsRC.IDD_EDITATTR_MF2	
		else:
			return grinsRC.IDD_EDITATTR_F2

	def createctrls(self,wnd):
		cd = FileGroup.createctrls(self,wnd)
		a = self.getattr('clipbegin')
		self.__clipbegin = cd[a] = StringNolabelCtrl(wnd,a,(grinsRC.IDC_CLIPBEGINL, grinsRC.IDC_CLIPBEGINV))
		a = self.getattr('clipend')
		self.__clipend = cd[a] = StringNolabelCtrl(wnd,a,(grinsRC.IDC_CLIPENDL, grinsRC.IDC_CLIPENDV))
		a = self.getattr('readIndex')
		cd[a] = StringNolabelCtrl(wnd,a,(grinsRC.IDC_READINDEXL, grinsRC.IDC_READINDEXV))
		a = self.getattr('sensitivity')
		cd[a] = StringNolabelCtrl(wnd,a,(grinsRC.IDC_EVENTSENSITIVITYL, grinsRC.IDC_EVENTSENSITIVITYV))
		a = self.getattr('erase')
		cd[a] = OptionsRadioNolabelCtrl(wnd,a,(grinsRC.IDC_ERASEL, grinsRC.IDC_ERASEV2, grinsRC.IDC_ERASEV1))
		return cd

	def oninitdialog(self,wnd):
		# disable ctrl which make no sense for static medias.
		# but even show if specified value from source since it's not an error in SMIL 2
		if not self.canpreview() or self.isStaticMedia(self._mtypesig):
			self.__clipbegin.enable(0)
			self.__clipend.enable(0)

class BrushGroup(AttrGroup):
	data=attrgrsdict['brush']
	def __init__(self):
		AttrGroup.__init__(self,BrushGroup.data)

	def getpageresid(self):
		return grinsRC.IDD_EDITATTR_BRUSH

	def createctrls(self,wnd):
		cd = {}
		a = self.getattr('fgcolor')
		cd[a] = ColorNolabelCtrl(wnd,a,(grinsRC.IDC_LABEL, grinsRC.IDC_COLORS, grinsRC.IDC_COLOR_PICK))
		a = self.getattr('readIndex')
		cd[a] = StringNolabelCtrl(wnd,a,(grinsRC.IDC_READINDEXL, grinsRC.IDC_READINDEXV))
		a = self.getattr('sensitivity')
		cd[a] = StringNolabelCtrl(wnd,a,(grinsRC.IDC_EVENTSENSITIVITYL, grinsRC.IDC_EVENTSENSITIVITYV))
		a = self.getattr('erase')
		cd[a] = OptionsRadioNolabelCtrl(wnd,a,(grinsRC.IDC_ERASEL, grinsRC.IDC_ERASEV2, grinsRC.IDC_ERASEV1))
		return cd
		
class TimingFadeoutGroup(AttrGroup):
	data=attrgrsdict['timingfadeout']

	def __init__(self):
		AttrGroup.__init__(self,self.data)

	def getpageresid(self):
		return grinsRC.IDD_EDITATTR_TF1

	def createctrls(self,wnd):
		cd = {}
		a = self.getattr('tduration')
		cd[a] = StringNolabelCtrl(wnd,a,(grinsRC.IDC_11,grinsRC.IDC_12))
		a = self.getattr('start')
		cd[a] = StringNolabelCtrl(wnd,a,(grinsRC.IDC_21,grinsRC.IDC_22))
		a = self.getattr('fadeout')
		cd[a] = OptionsRadioNolabelCtrl(wnd,a,(grinsRC.IDC_31,grinsRC.IDC_32,grinsRC.IDC_33))
		a = self.getattr('fadeouttime')
		cd[a] = StringNolabelCtrl(wnd,a,(grinsRC.IDC_41,grinsRC.IDC_42))
		a = self.getattr('fadeoutduration')
		cd[a] = StringNolabelCtrl(wnd,a,(grinsRC.IDC_51,grinsRC.IDC_52))
		a = self.getattr('fadeoutcolor')
		cd[a] = ColorNolabelCtrl(wnd,a,(grinsRC.IDC_61,grinsRC.IDC_62,grinsRC.IDC_63))
		a = self.getattr('tag')
		cd[a] = OptionsNolabelCtrl(wnd,a,(grinsRC.IDC_71,grinsRC.IDC_72))
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

class BeginListGroup(AttrGroup):
	data=attrgrsdict['beginlist']

	def __init__(self):
		AttrGroup.__init__(self,self.data)

	def getpageresid(self):
		return grinsRC.IDD_EDITATTR_EVENTLIST

	def createctrls(self,wnd):
		cd = {}
		#a = self.getattr('beginlist')
		#cd[a] = ListCtrl(wnd,a,(grinsRC.IDC_STATIC1, grinsRC.IDC_LIST4, grinsRC.IDC_BUTTON7, grinsRC.IDC_BUTTON8, grinsRC.IDC_BUTTON9))
		a = self.getattr('beginlist')
		cd[a] = BeginEventCtrl(wnd,a,())
		return cd

class BeginList2Group(BeginListGroup):
	data=attrgrsdict['beginlist2']

	def __init__(self):
		AttrGroup.__init__(self,self.data)

	def getpageresid(self):
		return grinsRC.IDD_EDITATTR_EVENTLIST2

	def createctrls(self,wnd):
		cd = BeginListGroup.createctrls(self, wnd)
		a = self.getattr('restart')
		cd[a] = OptionsNolabelCtrl(wnd,a,(grinsRC.IDC_RESTARTNODEL,grinsRC.IDC_RESTARTNODEV), (grinsRC.IDC_EVENTLASSOO2,))
		a = self.getattr('restartDefault')
		cd[a] = OptionsNolabelCtrl(wnd,a,(grinsRC.IDC_RESTARTDEFAULTL,grinsRC.IDC_RESTARTDEFAULTV))
		return cd

class EndListGroup(AttrGroup):
	data=attrgrsdict['endlist']

	def __init__(self):
		AttrGroup.__init__(self,self.data)

	def getpageresid(self):
		return grinsRC.IDD_EDITATTR_EVENTLIST

	def createctrls(self,wnd):
		cd = {}
		a = self.getattr('endlist')
		cd[a] = EndEventCtrl(wnd,a,())
		#a = self.getattr('endlist')
		#cd[a] = ListCtrl(wnd,a,(grinsRC.IDC_STATIC2, grinsRC.IDC_LIST3, grinsRC.IDC_BUTTON4, grinsRC.IDC_BUTTON5, grinsRC.IDC_BUTTON6))
		return cd

 
class Convert1Group(AttrGroup):
	data = attrgrsdict['convert1']

	def __init__(self):
		AttrGroup.__init__(self, self.data)

	def getpageresid(self):
		return grinsRC.IDD_EDITATTR_CONV1

	def createctrls(self, wnd):
		cd = {}
		a = self.getattr('project_convert')
		cd[a] = OptionsCheckNolabelCtrl(wnd,a,(grinsRC.IDC_11,))
		self.__convert = cd[a]
		a = self.getattr('project_quality')
		cd[a]=OptionsNolabelCtrl(wnd,a,(grinsRC.IDC_11,grinsRC.IDC_22))
		self.__cd = cd
		return cd
	
	def oninitdialog(self, wnd):
		AttrGroup.oninitdialog(self, wnd)
		self.__convert._check.hookcommand(wnd, self.__onconvert)

	def __onconvert(self, id, code):
		if code == win32con.BN_CLICKED:
			check = self.__convert._check.getcheck()
			for ctrl in self.__cd.values():
				if ctrl is not self.__convert:
					ctrl.enable(check)
			self.__convert.enableApply()

class Convert2Group(AttrGroup):
	data = attrgrsdict['convert2']

	def __init__(self):
		AttrGroup.__init__(self, self.data)

	def getpageresid(self):
		return grinsRC.IDD_EDITATTR_CONV2

	def createctrls(self, wnd):
		cd = {}
		a = self.getattr('project_targets')
		cd[a] = OptionsCheckMultipleNolabelCtrl(wnd,a,(grinsRC.IDC_11,grinsRC.IDC_12,grinsRC.IDC_13,grinsRC.IDC_14,grinsRC.IDC_15,grinsRC.IDC_16,grinsRC.IDC_17))
		a = self.getattr('project_audiotype')
		cd[a] = OptionsNolabelCtrl(wnd,a,(grinsRC.IDC_31,grinsRC.IDC_32))
		return cd

class Convert3Group(Convert2Group):
	data = attrgrsdict['convert3']

	def getpageresid(self):
		return grinsRC.IDD_EDITATTR_CONV3

	def createctrls(self, wnd):
		cd = Convert2Group.createctrls(self, wnd)
		a = self.getattr('project_videotype')
		cd[a] = OptionsNolabelCtrl(wnd,a,(grinsRC.IDC_21,grinsRC.IDC_22))
		return cd

class Convert4Group(Convert2Group):
	data = attrgrsdict['convert4']

	def getpageresid(self):
		return grinsRC.IDD_EDITATTR_CONV4

	def createctrls(self, wnd):
		cd = Convert2Group.createctrls(self, wnd)
		a = self.getattr('project_perfect')
		cd[a] = OptionsCheckNolabelCtrl(wnd,a,(grinsRC.IDC_41,))
		a = self.getattr('project_mobile')
		cd[a] = OptionsCheckNolabelCtrl(wnd,a,(grinsRC.IDC_51,))
		a = self.getattr('project_convert')
		cd[a] = OptionsCheckNolabelCtrl(wnd,a,(grinsRC.IDC_61,))
		self.__convert = cd[a]
		self.__cd = cd
		return cd

	def oninitdialog(self, wnd):
		Convert2Group.oninitdialog(self, wnd)
		self.__convert._check.hookcommand(wnd, self.__onconvert)
		self.__onconvert(0, win32con.BN_CLICKED)

	def __onconvert(self, id, code):
		if code == win32con.BN_CLICKED:
			check = self.__convert._check.getcheck()
			for ctrl in self.__cd.values():
				if ctrl is not self.__convert:
					ctrl.enable(check)
			self.__convert.enableApply()

class Convert5Group(Convert4Group):
	data = attrgrsdict['convert5']

	def getpageresid(self):
		return grinsRC.IDD_EDITATTR_CONV5

	def createctrls(self, wnd):
		cd = Convert4Group.createctrls(self, wnd)
		a = self.getattr('project_videotype')
		cd[a] = OptionsNolabelCtrl(wnd,a,(grinsRC.IDC_21,grinsRC.IDC_22))
		return cd

#

class ActiveDurationGroup(AttrGroup):
	data=attrgrsdict['activeduration']

	def __init__(self):
		AttrGroup.__init__(self, self.data)

	def getpageresid(self):
		return grinsRC.IDD_EDITATTR_ACTIVEDUR

	def createctrls(self, wnd):
		cd = {}
		a = self.getattr('duration')
		cd[a] = StringNolabelCtrl(wnd,a,(grinsRC.IDC_DURL,grinsRC.IDC_DURV))
		a = self.getattr('min')
		cd[a] = StringNolabelCtrl(wnd,a,(grinsRC.IDC_MINL,grinsRC.IDC_MINV))
		a = self.getattr('max')
		cd[a] = StringNolabelCtrl(wnd,a,(grinsRC.IDC_MAXL,grinsRC.IDC_MAXV))
		a = self.getattr('loop')
		cd[a] = StringNolabelCtrl(wnd,a,(grinsRC.IDC_LOOPL,grinsRC.IDC_LOOPV))
		a = self.getattr('repeatdur')
		cd[a] = StringNolabelCtrl(wnd,a,(grinsRC.IDC_REPDURL,grinsRC.IDC_REPDURV))
		return cd


class ActiveDuration2Group(ActiveDurationGroup):
	data=attrgrsdict['activeduration2']

	def __init__(self):
		AttrGroup.__init__(self, self.data)

	def getpageresid(self):
		return grinsRC.IDD_EDITATTR_ACTIVEDUR2

	def createctrls(self, wnd):
		cd = ActiveDurationGroup.createctrls(self, wnd)
		a = self.getattr('fill')
		cd[a] = OptionsNolabelCtrl(wnd,a,(grinsRC.IDC_FILLL, grinsRC.IDC_FILLV))
		a = self.getattr('fillDefault')
		cd[a] = OptionsNolabelCtrl(wnd,a,(grinsRC.IDC_FILLDEFL,grinsRC.IDC_FILLDEFV))
		return cd

class ActiveDuration3Group(ActiveDuration2Group):
	data=attrgrsdict['activeduration3']

	def getpageresid(self):
		return grinsRC.IDD_EDITATTR_ACTIVEDUR3

	def createctrls(self, wnd):
		cd = ActiveDuration2Group.createctrls(self, wnd)
		a = self.getattr('terminator')
		cd[a] = OptionsNolabelCtrl(wnd,a,(grinsRC.IDC_ENDSYNCL,grinsRC.IDC_ENDSYNCV))
		return cd

class ActiveDuration4Group(ActiveDuration3Group):
	data=attrgrsdict['activeduration4']

	def getpageresid(self):
		return grinsRC.IDD_EDITATTR_ACTIVEDUR4

	def createctrls(self, wnd):
		cd = ActiveDuration3Group.createctrls(self, wnd)
		a = self.getattr('erase')
		cd[a] = OptionsRadioNolabelCtrl(wnd,a,(grinsRC.IDC_ERASEL, grinsRC.IDC_ERASEV2, grinsRC.IDC_ERASEV1))
		return cd

class ActiveDuration1Group(ActiveDuration4Group):
	data=attrgrsdict['activeduration1']

	def getpageresid(self):
		return grinsRC.IDD_EDITATTR_ACTIVEDUR1

	def createctrls(self, wnd):
		cd = ActiveDuration4Group.createctrls(self, wnd)
		a = self.getattr('clipbegin')
		cd[a] = StringNolabelCtrl(wnd,a,(grinsRC.IDC_CLIPBL,grinsRC.IDC_CLIPBV))
		a = self.getattr('clipend')
		cd[a] = StringNolabelCtrl(wnd,a,(grinsRC.IDC_CLIPEL,grinsRC.IDC_CLIPEV))
		return cd

class AnimateTargetGroup(AttrGroup):
	data=attrgrsdict['animateTarget']
	def __init__(self):
		AttrGroup.__init__(self,self.data)
	def getpageresid(self):
		return grinsRC.IDD_EDITATTR_ANIMATETARGET
	def createctrls(self,wnd):
		cd = {}
		a = self.getattr('atag')
		cd[a] = OptionsNolabelCtrl(wnd,a,(grinsRC.IDC_ATAGL,grinsRC.IDC_ATAGV))
		a = self.getattr('targetElement')
		cd[a] = ElementSelNolabelCtrl(wnd,a,(grinsRC.IDC_TELEML, grinsRC.IDC_TELEMV, grinsRC.IDC_TELEMB))
		a = self.getattr('attributeName')
		cd[a] = StringNolabelCtrl(wnd,a,(grinsRC.IDC_TATTRL,grinsRC.IDC_TATTRV))
		a = self.getattr('attributeType')
		cd[a] = OptionsRadioNolabelCtrl(wnd,a,(grinsRC.IDC_ATYPEL,grinsRC.IDC_ATYPEV1,grinsRC.IDC_ATYPEV2,grinsRC.IDC_ATYPEV3))
		return cd

class AnimateTargetSetGroup(AnimateTargetGroup):
	data=attrgrsdict['animateTargetSet']
	def getpageresid(self):
		return grinsRC.IDD_EDITATTR_ANIMATETARGETSET
	def createctrls(self,wnd):
		cd = AnimateTargetGroup.createctrls(self,wnd)
		a = self.getattr('to')
		cd[a] = StringNolabelCtrl(wnd,a,(grinsRC.IDC_TOL,grinsRC.IDC_TOV))
		return cd

class AnimateTargetMotionGroup(AttrGroup):
	data=attrgrsdict['animateTargetMotion']
	def __init__(self):
		AttrGroup.__init__(self,self.data)
	def getpageresid(self):
		return grinsRC.IDD_EDITATTR_ANIMATETARGETMOTION
	def createctrls(self,wnd):
		cd = {}
		a = self.getattr('atag')
		cd[a] = OptionsNolabelCtrl(wnd,a,(grinsRC.IDC_ATAGL,grinsRC.IDC_ATAGV))
		a = self.getattr('targetElement')
		cd[a] = ElementSelNolabelCtrl(wnd,a,(grinsRC.IDC_TELEML, grinsRC.IDC_TELEMV, grinsRC.IDC_TELEMB))
		a = self.getattr('path')
		cd[a] = StringNolabelCtrl(wnd,a,(grinsRC.IDC_PATHL,grinsRC.IDC_PATHV))
		a = self.getattr('origin')
		cd[a] = OptionsRadioNolabelCtrl(wnd,a,(grinsRC.IDC_ORIGINL,grinsRC.IDC_ORIGINV1,grinsRC.IDC_ORIGINV2))
		return cd

class AnimateValuesGroup(AttrGroup):
	data=attrgrsdict['animateValues']
	def __init__(self):
		AttrGroup.__init__(self,self.data)
	def getpageresid(self):
		return grinsRC.IDD_EDITATTR_ANIMATEVALUES
	def createctrls(self,wnd):
		cd = {}
		a = self.getattr('from')
		cd[a] = StringNolabelCtrl(wnd,a,(grinsRC.IDC_FROML,grinsRC.IDC_FROMV))
		a = self.getattr('by')
		cd[a] = StringNolabelCtrl(wnd,a,(grinsRC.IDC_BYL,grinsRC.IDC_BYV))
		a = self.getattr('to')
		cd[a] = StringNolabelCtrl(wnd,a,(grinsRC.IDC_TOL,grinsRC.IDC_TOV))
		a = self.getattr('values')
		cd[a] = StringNolabelCtrl(wnd,a,(grinsRC.IDC_VALUESL,grinsRC.IDC_VALUESV))
		a = self.getattr('additive')
		cd[a] = OptionsRadioNolabelCtrl(wnd,a,(grinsRC.IDC_ADDITIVEL,grinsRC.IDC_ADDITIVEV1,grinsRC.IDC_ADDITIVEV2))
		a = self.getattr('accumulate')
		cd[a] = OptionsRadioNolabelCtrl(wnd,a,(grinsRC.IDC_ACCUMULATEL,grinsRC.IDC_ACCUMULATEV1,grinsRC.IDC_ACCUMULATEV2))
		return cd

#
class InlineTransitionGroup(AttrGroup):
	data=attrgrsdict['inlineTransition']
	def __init__(self):
		AttrGroup.__init__(self,self.data)
	def getpageresid(self):
		return grinsRC.IDD_EDITATTR_ITRANSITION
	def createctrls(self,wnd):
		cd = {}
		a = self.getattr('trtype')
		cd[a] = OptionsNolabelCtrl(wnd,a,(grinsRC.IDC_11,grinsRC.IDC_12))
		a = self.getattr('subtype')
		cd[a] = StringNolabelCtrl(wnd,a,(grinsRC.IDC_21,grinsRC.IDC_22))
		a = self.getattr('mode')
		cd[a] = OptionsRadioNolabelCtrl(wnd,a,(grinsRC.IDC_31,grinsRC.IDC_32, grinsRC.IDC_33))
		a = self.getattr('fadeColor')
		cd[a] = ColorNolabelCtrl(wnd,a,(grinsRC.IDC_41,grinsRC.IDC_42, grinsRC.IDC_43))
		return cd

#
class TimeManipulationGroup(AttrGroup):
	data=attrgrsdict['timeManipulation']
	def __init__(self):
		AttrGroup.__init__(self,self.data)
	def getpageresid(self):
		return grinsRC.IDD_EDITATTR_S3R2
	def createctrls(self,wnd):
		cd = {}
		a = self.getattr('speed')
		cd[a] = StringNolabelCtrl(wnd,a,(grinsRC.IDC_11,grinsRC.IDC_12))
		a = self.getattr('accelerate')
		cd[a] = StringNolabelCtrl(wnd,a,(grinsRC.IDC_21,grinsRC.IDC_22))
		a = self.getattr('decelerate')
		cd[a] = StringNolabelCtrl(wnd,a,(grinsRC.IDC_31,grinsRC.IDC_32))
		a = self.getattr('autoReverse')
		cd[a] = OptionsCheckNolabelCtrl(wnd,a,(grinsRC.IDC_41,))
		return cd

class CalcModeGroup(AttrGroup):
	data=attrgrsdict['calcMode']
	def __init__(self):
		AttrGroup.__init__(self,self.data)
	def getpageresid(self):
		return grinsRC.IDD_EDITATTR_O1S2
	def createctrls(self,wnd):
		cd = {}
		a = self.getattr('calcMode')
		cd[a] = OptionsCtrl(wnd,a,(grinsRC.IDC_11,grinsRC.IDC_12))
		a = self.getattr('keyTimes')
		cd[a] = StringCtrl(wnd,a,(grinsRC.IDC_21,grinsRC.IDC_22))
		a = self.getattr('keySplines')
		cd[a] = StringCtrl(wnd,a,(grinsRC.IDC_31,grinsRC.IDC_32))
		return cd

class CssBackgroundColorGroup(AttrGroup):
	data=attrgrsdict['CssBackgroundColor']
	def __init__(self):
		AttrGroup.__init__(self,self.data)
	def getpageresid(self):
		return grinsRC.IDD_EDITATTR_COLORSEL
	def createctrls(self,wnd):
		cd = {}
		a = self.getattr('cssbgcolor')
		cd[a] = RegionCssColorCtrl(wnd,a,(grinsRC.IDC_LABEL, grinsRC.IDC_COLORS, grinsRC.IDC_COLOR_PICK,
									grinsRC.IDC_CTYPES, grinsRC.IDC_CTYPET,
									grinsRC.IDC_CTYPEI))
		return cd

class GeomGroup(AttrGroup):
	def __init__(self):
		self.data=attrgrsdict['Geometry']
		AttrGroup.__init__(self,self.data)

	def getpageresid(self):
		return grinsRC.IDD_EDITATTR_GEOMETRY

	def createctrls(self, wnd):
		cd = {}
		self.creategeomctrls(wnd, cd)
		return cd

	def creategeomctrls(self, wnd, cd):
		a = self.getattr('left')
		cd[a] = CssPosCtrl(wnd,a,(grinsRC.IDC_LEFTL, grinsRC.IDC_LEFTV, grinsRC.IDC_LEFTU))
		a = self.getattr('width')
		cd[a] = CssPosCtrl(wnd,a,(grinsRC.IDC_WIDTHL, grinsRC.IDC_WIDTHV, grinsRC.IDC_WIDTHU))
		a = self.getattr('right')
		cd[a] = CssPosCtrl(wnd,a,(grinsRC.IDC_RIGHTL, grinsRC.IDC_RIGHTV, grinsRC.IDC_RIGHTU))
		a = self.getattr('top')
		cd[a] = CssPosCtrl(wnd,a,(grinsRC.IDC_TOPL, grinsRC.IDC_TOPV, grinsRC.IDC_TOPU))
		a = self.getattr('height')
		cd[a] = CssPosCtrl(wnd,a,(grinsRC.IDC_HEIGHTL, grinsRC.IDC_HEIGHTV, grinsRC.IDC_HEIGHTU))
		a = self.getattr('bottom')
		cd[a] = CssPosCtrl(wnd,a,(grinsRC.IDC_BOTTOML, grinsRC.IDC_BOTTOMV, grinsRC.IDC_BOTTOMU))

class Layout2Group(AttrGroup):
	data = attrgrsdict['Layout2']
	def __init__(self):
		AttrGroup.__init__(self,self.data)

	def getpageresid(self):
		return grinsRC.IDD_EDITATTR_LAYOUT2
	
	def createctrls(self,wnd):
		cd = {}
		a = self.getattr('cssbgcolor')
		cd[a] = NodeCssColorCtrl(wnd,a,(grinsRC.IDC_LABEL, grinsRC.IDC_COLORS, grinsRC.IDC_COLOR_PICK,
									grinsRC.IDC_CTYPES, grinsRC.IDC_CTYPET,
									grinsRC.IDC_CTYPEI))
		a = self.getattr('fit')
		cd[a] = OptionsNolabelCtrl(wnd,a,(grinsRC.IDC_FITL, grinsRC.IDC_FITV))
		a = self.getattr('z')
		cd[a] = StringNolabelCtrl(wnd,a,(grinsRC.IDC_ZL, grinsRC.IDC_ZV))
		a = self.getattr('soundLevel')
		cd[a] = StringNolabelCtrl(wnd,a,(grinsRC.IDC_SOUNDLEVELL, grinsRC.IDC_SOUNDLEVELV))
		a = self.getattr('showBackground')
		cd[a] = OptionsRadioNolabelCtrl(wnd,a,(grinsRC.IDC_SHOWBACKGROUNDL, grinsRC.IDC_SHOWBACKGROUNDV1, grinsRC.IDC_SHOWBACKGROUNDV2))
						   
		return cd

class LayoutRealGroup(Layout2Group):
	data = attrgrsdict['Layout2Real']
	def getpageresid(self):
		return grinsRC.IDD_EDITATTR_LAYOUT2REAL
	def createctrls(self,wnd):
		cd = Layout2Group.createctrls(self,wnd)
		a = self.getattr('opacity')
		cd[a] = StringNolabelCtrl(wnd,a,(grinsRC.IDC_OL, grinsRC.IDC_OV))
		return cd
	
class Layout1Group(AttrGroup):
	data=attrgrsdict['Layout1']
	def __init__(self):
		AttrGroup.__init__(self,self.data)

	def getpageresid(self):
		return grinsRC.IDD_EDITATTR_LAYOUT1

	def createctrls(self,wnd):
		cd = {}
		a = self.getattr('cssbgcolor')
		cd[a] = NodeCssColorCtrl(wnd,a,(grinsRC.IDC_LABEL, grinsRC.IDC_COLORS, grinsRC.IDC_COLOR_PICK,
									grinsRC.IDC_CTYPES, grinsRC.IDC_CTYPET,
									grinsRC.IDC_CTYPEI))
		a = self.getattr('fit')
		cd[a] = OptionsNolabelCtrl(wnd,a,(grinsRC.IDC_FITL, grinsRC.IDC_FITV))
		a = self.getattr('z')
		cd[a] = StringNolabelCtrl(wnd,a,(grinsRC.IDC_ZL, grinsRC.IDC_ZV))
		a = self.getattr('regPoint')
		cd[a] = OptionsNolabelCtrl(wnd,a,(grinsRC.IDC_REGPOINTL, grinsRC.IDC_REGPOINTV), (grinsRC.IDC_LABEL2,))
		a = self.getattr('regAlign')
		cd[a] = OptionsNolabelCtrl(wnd,a,(grinsRC.IDC_REGALIGNL, grinsRC.IDC_REGALIGNV))
		a = self.getattr('channel')
		cd[a] = ChannelNolabelCtrl(wnd,a,(grinsRC.IDC_REGIONL, grinsRC.IDC_REGIONV, grinsRC.IDC_REGIONB))

		return cd

class Layout3Group(AttrGroup):
	def __init__(self):
		self.data=attrgrsdict['Layout3']
		AttrGroup.__init__(self,self.data)

	def getpageresid(self):
		return grinsRC.IDD_EDITATTR_LAYOUT3
	
	def createctrls(self, wnd):
		cd = {}
		a = self.getattr('cssbgcolor')
		cd[a] = RegionCssColorCtrl(wnd,a,(grinsRC.IDC_LABEL, grinsRC.IDC_COLORS, grinsRC.IDC_COLOR_PICK,
									grinsRC.IDC_CTYPES, grinsRC.IDC_CTYPET,
									grinsRC.IDC_CTYPEI))
		a = self.getattr('width')
		cd[a] = StringNolabelCtrl(wnd,a,(grinsRC.IDC_WIDTHL, grinsRC.IDC_WIDTHV, grinsRC.IDC_WIDTHU), (grinsRC.IDC_GROUP1,))
		a = self.getattr('height')
		cd[a] = StringNolabelCtrl(wnd,a,(grinsRC.IDC_HEIGHTL, grinsRC.IDC_HEIGHTV, grinsRC.IDC_HEIGHTU))

		a = self.getattr('close')
		cd[a] = OptionsRadioNolabelCtrl(wnd,a,(grinsRC.IDC_CLOSEL, grinsRC.IDC_CLOSEV1, grinsRC.IDC_CLOSEV2))
		a = self.getattr('open')
		cd[a] = OptionsRadioNolabelCtrl(wnd,a,(grinsRC.IDC_OPENL, grinsRC.IDC_OPENV1, grinsRC.IDC_OPENV2))

		a = self.getattr('traceImage')
		cd[a] = FileCtrl(wnd,a,(grinsRC.IDC_TRACEIMAGEL,grinsRC.IDC_TRACEIMAGEV,grinsRC.IDC_TRACEIMAGEB))
						   						   
		return cd

class ContainerLayoutGroup(AttrGroup):
	data=attrgrsdict['containerlayout']
	def __init__(self,data=None):
		AttrGroup.__init__(self,self.data)

	def getpageresid(self):
		return grinsRC.IDD_EDITATTR_CH2

	def createctrls(self,wnd):
		cd={}
		a = self.getattr('project_default_region_image')
		cd[a] = RegionDefaultCtrl(wnd,a,(grinsRC.IDC_11,grinsRC.IDC_12,grinsRC.IDC_13))
		a = self.getattr('project_default_region_video')
		cd[a] = RegionDefaultCtrl(wnd,a,(grinsRC.IDC_21,grinsRC.IDC_22,grinsRC.IDC_23))
		a = self.getattr('project_default_region_sound')
		cd[a] = RegionDefaultCtrl(wnd,a,(grinsRC.IDC_31,grinsRC.IDC_32,grinsRC.IDC_33))
		a = self.getattr('project_default_region_text')
		cd[a] = RegionDefaultCtrl(wnd,a,(grinsRC.IDC_41,grinsRC.IDC_42,grinsRC.IDC_43))
		return cd

class RegionNameGroup(AttrGroup):
	data=attrgrsdict['regionname']
	def __init__(self):
		AttrGroup.__init__(self, self.data)
		
	def getpageresid(self):
		return grinsRC.IDD_EDITATTR_REGIONNAME
	
	def createctrls(self,wnd):
		cd = {}
		a = self.getattr('.cname')
		cd[a] = StringNolabelCtrl(wnd,a,(grinsRC.IDC_REGIONIDL,grinsRC.IDC_REGIONIDV))
		a = self.getattr('regionName')
		cd[a] = StringNolabelCtrl(wnd,a,(grinsRC.IDC_REGIONNAMEL,grinsRC.IDC_REGIONNAMEV))
		return cd

class ViewportNameGroup(AttrGroup):
	data=attrgrsdict['viewportname']
	def __init__(self):
		AttrGroup.__init__(self, self.data)
		
	def getpageresid(self):
		return grinsRC.IDD_EDITATTR_VIEWPORTNAME
	
	def createctrls(self,wnd):
		cd = {}
		a = self.getattr('.cname')
		cd[a] = StringNolabelCtrl(wnd,a,(grinsRC.IDC_TOPLAYOUTIDL,grinsRC.IDC_TOPLAYOUTIDV))
		return cd

#
class TransitionTypeGroup(NameGroup):
	data=attrgrsdict['transitionType']
	def getpageresid(self):
		return grinsRC.IDD_EDITATTR_S1O1

#
class TransitionRepeatGroup(StringGroupNoTitle):
	data=attrgrsdict['transitionRepeat']
#
class TransitionTimingGroup(StringGroupNoTitle):
	data=attrgrsdict['transitionTiming']

#
class MachineGroup(StringGroupNoTitle):
	data=attrgrsdict['machine']
	def oninitdialog(self,wnd):
		# enlarge labels by dwpx pixels
		dwpx = 32
		labels = (grinsRC.IDC_11, grinsRC.IDC_21)
		edits = (grinsRC.IDC_12, grinsRC.IDC_22)
		self.resizelabels(wnd, labels, edits, dwpx)
		return StringGroupNoTitle.oninitdialog(self, wnd)

class ForeignGroup(StringGroup):
	data = attrgrsdict['foreign']

class MiscAnchorGroup(AttrGroup):
	data=attrgrsdict['specanchor']
	def __init__(self):
		AttrGroup.__init__(self, self.data)
		
	def getpageresid(self):
		return grinsRC.IDD_EDITATTR_ANCHOR2
	
	def createctrls(self,wnd):
		cd = {}
		a = self.getattr('acoords')
		cd[a] = StringNolabelCtrl(wnd,a,(grinsRC.IDC_STATIC1,grinsRC.IDC_EDIT1))
		a = self.getattr('ashape')
		cd[a] = OptionsNolabelCtrl(wnd,a,(grinsRC.IDC_STATIC2, grinsRC.IDC_COMBO1))
		a = self.getattr('fragment')
		cd[a] = StringNolabelCtrl(wnd,a,(grinsRC.IDC_STATIC3,grinsRC.IDC_EDIT2))
		a = self.getattr('tabindex')
		cd[a] = StringNolabelCtrl(wnd,a,(grinsRC.IDC_STATIC4,grinsRC.IDC_EDIT3))
		a = self.getattr('external')
		cd[a] = OptionsCheckNolabelCtrl(wnd,a,(grinsRC.IDC_CHECK1,))
		a = self.getattr('sourceLevel')
		cd[a] = StringNolabelCtrl(wnd,a,(grinsRC.IDC_STATIC7,grinsRC.IDC_EDIT4))
		a = self.getattr('destinationLevel')
		cd[a] = StringNolabelCtrl(wnd,a,(grinsRC.IDC_STATIC8,grinsRC.IDC_EDIT5))
		a = self.getattr('target')
		cd[a] = StringNolabelCtrl(wnd,a,(grinsRC.IDC_STATIC9,grinsRC.IDC_EDIT6))
		return cd

class GeneralAnchorGroup(AttrGroup):
	data = attrgrsdict['genanchor']
	def __init__(self):
		AttrGroup.__init__(self, self.data)
		
	def getpageresid(self):
		return grinsRC.IDD_EDITATTR_ANCHOR1
	
	def createctrls(self,wnd):
		cd = {}
		a = self.getattr('.href')
		cd[a] = HrefCtrl(wnd,a,(grinsRC.IDC_STATIC0,grinsRC.IDC_RADIO1,grinsRC.IDC_RADIO2,grinsRC.IDC_RADIO3,grinsRC.IDC_BUTTON1,grinsRC.IDC_EDIT1,grinsRC.IDC_BUTTON2))
		a = self.getattr('show')
		cd[a] = OptionsNolabelCtrl(wnd,a,(grinsRC.IDC_STATIC1,grinsRC.IDC_COMBO1))
		a = self.getattr('sourcePlaystate')
		cd[a] = OptionsNolabelCtrl(wnd,a,(grinsRC.IDC_STATIC2,grinsRC.IDC_COMBO2))
		a = self.getattr('destinationPlaystate')
		cd[a] = OptionsNolabelCtrl(wnd,a,(grinsRC.IDC_STATIC3,grinsRC.IDC_COMBO3))
		a = self.getattr('accesskey')
		cd[a] = StringNolabelCtrl(wnd,a,(grinsRC.IDC_STATIC4,grinsRC.IDC_EDIT3))
		a = self.getattr('sendTo')
		cd[a] = OptionsNolabelCtrl(wnd,a,(grinsRC.IDC_STATIC5,grinsRC.IDC_COMBO4))
		a = self.getattr('actuate')
		cd[a] = OptionsNolabelCtrl(wnd,a,(grinsRC.IDC_STATIC6, grinsRC.IDC_COMBO5))
		return cd

class NonEmptyGroup(AttrGroup):
	data = attrgrsdict['nonempty']
	_attrnames = ('non_empty_icon',
		      'non_empty_text',
		      'non_empty_color',)
	_pageresid = grinsRC.IDD_EDITATTR_NONEMPTYGROUP

	def __init__(self):
		AttrGroup.__init__(self, self.data)
		
	def getpageresid(self):
		return self._pageresid
	
	def createctrls(self,wnd):
		cd = {}
		a = self.getattr(self._attrnames[0])
		cd[a] = FileNolabelCtrl(wnd, a, (grinsRC.IDC_STATIC1, grinsRC.IDC_EDIT2, grinsRC.IDC_BUTTON2,))
		a = self.getattr(self._attrnames[1])
		cd[a] = StringNolabelCtrl(wnd, a, (grinsRC.IDC_STATIC2, grinsRC.IDC_EDIT3,))
		a = self.getattr(self._attrnames[2])
		cd[a] = ColorNolabelCtrl(wnd, a, (grinsRC.IDC_STATIC3, grinsRC.IDC_EDIT4, grinsRC.IDC_BUTTON3,))
		if len(self._attrnames) > 3:
			a = self.getattr(self._attrnames[3])
			cd[a] = StringNolabelCtrl(wnd,a,(grinsRC.IDC_STATIC4,grinsRC.IDC_EDIT5))
		return cd

class EmptyGroup(NonEmptyGroup):
	data = attrgrsdict['empty']
	_attrnames = ('empty_icon',
		      'empty_text',
		      'empty_color',
		      'empty_duration')
	_pageresid = grinsRC.IDD_EDITATTR_EMPTYGROUP

class TemplateGroup(AttrGroup):
	data = attrgrsdict['template']
	_pageresid = grinsRC.IDD_EDITATTR_TEMPLATE0

	def __init__(self):
		AttrGroup.__init__(self, self.data)
		
	def getpageresid(self):
		return self._pageresid
	
	def createctrlscommon(self,wnd,dur):
		cd = {}
		a = self.getattr('thumbnail_icon')
		cd[a] = FileNolabelCtrl(wnd, a, (grinsRC.IDC_STATIC1, grinsRC.IDC_EDIT1, grinsRC.IDC_BUTTON1,))
		a = self.getattr('thumbnail_scale')
		cd[a] = OptionsCheckNolabelCtrl(wnd, a, (grinsRC.IDC_CHECK1,))
		a = self.getattr('dropicon')
		cd[a] = FileNolabelCtrl(wnd, a, (grinsRC.IDC_STATIC2, grinsRC.IDC_EDIT2, grinsRC.IDC_BUTTON2,))
		if dur:
			a = self.getattr('project_default_duration')
			cd[a] = StringNolabelCtrl(wnd,a,(grinsRC.IDC_STATIC4,grinsRC.IDC_EDIT3))
		return cd

	def createctrls(self,wnd):
		return self.createctrlscommon(wnd,0)

class Template1Group(TemplateGroup):
	data = attrgrsdict['template1']
	_pageresid = grinsRC.IDD_EDITATTR_TEMPLATE1

	def createctrls(self,wnd):
		cd = self.createctrlscommon(wnd,1)
		a = self.getattr('project_forcechild')
		cd[a] = OptionsNolabelCtrl(wnd,a,(grinsRC.IDC_STATIC3, grinsRC.IDC_COMBO1))
		return cd

class Template2Group(TemplateGroup):
	data = attrgrsdict['template2']
	_pageresid = grinsRC.IDD_EDITATTR_TEMPLATE2

	def createctrls(self,wnd):
		cd = self.createctrlscommon(wnd,1)
		a = self.getattr('project_autoroute')
		cd[a] = OptionsCheckNolabelCtrl(wnd, a, (grinsRC.IDC_CHECK2,))
		return cd

class DocTemplateGroup(AttrGroup):
	data = attrgrsdict['doctemplate']
	def __init__(self):
		AttrGroup.__init__(self, self.data)

	def getpageresid(self):
		return grinsRC.IDD_EDITATTR_DOCTEMPLATE

	def createctrls(self, wnd):
		cd = {}
		a = self.getattr('template_name')
		cd[a] = StringNolabelCtrl(wnd, a, (grinsRC.IDC_STATIC2,grinsRC.IDC_EDIT3,))
		a = self.getattr('template_description')
		cd[a] = StringNolabelCtrl(wnd, a, (grinsRC.IDC_STATIC3,grinsRC.IDC_EDIT4,))
		a = self.getattr('template_snapshot')
		cd[a] = FileNolabelCtrl(wnd, a, (grinsRC.IDC_STATIC1, grinsRC.IDC_EDIT2, grinsRC.IDC_BUTTON2,))
		return cd

############################
# platform dependent association
# what we have implemented, anything else goes as singleton
groupsui={
	'infogroup':InfoGroup,
	'infofilegroup':InfoFileGroup,
	'infofile1group':InfoFile1Group,
	'general':GeneralGroup,
	'docinfo':DocInfoGroup,

	'base_winoff':LayoutGroup,
	'base_winoff_and_units':LayoutGroupWithUnits,
	'CssBackgroundColor':CssBackgroundColorGroup,
	'Geometry':GeomGroup,
	'Layout1':Layout1Group,
	'Layout2':Layout2Group,
	'Layout2Real':LayoutRealGroup,
	'Layout3':Layout3Group,
	'containerlayout':ContainerLayoutGroup,
	'regionname':RegionNameGroup,
	'viewportname':ViewportNameGroup,
	'subregion':SubregionGroup,
	'imgregion':ImgregionGroup,
	'subregion1':Subregion1Group,
	'subregion2':Subregion2Group,

	'convert1':Convert1Group,
	'convert2':Convert2Group,
	'convert3':Convert3Group,
	'convert4':Convert4Group,
	'convert5':Convert5Group,

	'transition':TransitionGroup,
	'snapsystem':SnapSystemGroup,
	'system':SystemGroup,
	'system2':SystemGroup2,
	'system3':SystemGroup3,
	'preferences':PreferencesGroup,
	'preferences2':Preferences2Group,
	'preferencesPro':PreferencesProGroup,
	'name':NameGroup,
	'.cname':CNameGroup,
	'.cname2':CNameGroup2,
	'intname':INameGroup,

	'beginlist':BeginListGroup,
	'beginlist2':BeginList2Group,
	'endlist':EndListGroup,
	'timing1':DurationGroup,
	'timing2':Duration2Group,
	'timing3':Duration3Group,
	'timing3c':Duration3cGroup,
	'timing4':Duration4Group,
	'synchronization':SynchronizationGroup,
	'timingfadeout':TimingFadeoutGroup,
	'timingpar':DurationParGroup,
	'prio':PrioGroup,
	'server':ServerGroup,
	'webserver':WebserverGroup,
	'mediaserver':MediaserverGroup,
	'file':FileGroup,
	'media':MediaGroup,
	'brush':BrushGroup,
	'wipe':WipeGroup,
	'clip':ClipGroup,
	'bandwidth':BandwidthGroup,
	'activeduration':ActiveDurationGroup,
	'activeduration1':ActiveDuration1Group,
	'activeduration2':ActiveDuration2Group,
	'activeduration3':ActiveDuration3Group,
	'activeduration4':ActiveDuration4Group,
	'miscellaneous':MiscGroup,
	'miscellaneous2':Misc2Group,
	
	'qtpreferences':QTPlayerPreferencesGroup,
	'qtmediapreferences':QTPlayerMediaPreferencesGroup,

	'animateTarget':AnimateTargetGroup,
	'animateTargetSet':AnimateTargetSetGroup,
	'animateTargetMotion':AnimateTargetMotionGroup,
	'animateValues':AnimateValuesGroup,
	'timeManipulation':TimeManipulationGroup,
	'calcMode':CalcModeGroup,
	'timingsb':DurationSBGroup,
	'inlineTransition':InlineTransitionGroup,

	'transitionType': TransitionTypeGroup,
	'transitionRepeat':TransitionRepeatGroup,
	'transitionTiming':TransitionTimingGroup,

	'machine':MachineGroup,

	'foreign':ForeignGroup,

	'genanchor':GeneralAnchorGroup,
	'specanchor':MiscAnchorGroup,

	'empty':EmptyGroup,
	'nonempty':NonEmptyGroup,
	'template1':Template1Group,
	'template2':Template2Group,
	'template':TemplateGroup,
	'doctemplate':DocTemplateGroup,
	}

###########################
# already bound: &P, &B, &X, &Y, &W, &H

class TabShortcut:
	data={
		'&Audio type':grinsRC.ID_A,
		'Pe&ak bitrate':grinsRC.ID_A,

		'&Caption channel':grinsRC.ID_C,
		'Text &caption':grinsRC.ID_C,
		'&Content':grinsRC.ID_C,

		'&Destination region':grinsRC.ID_D,

		'K&eep aspect ratio':grinsRC.ID_E,
		'&Effect color':grinsRC.ID_E,

		'&Fadeout':grinsRC.ID_F,
		'Scale &factor':grinsRC.ID_F,

		'&General':grinsRC.ID_G,
		'Be&gin time':grinsRC.ID_G,

		'&Info':grinsRC.ID_I,

		'Bac&kground color':grinsRC.ID_K,
		'&Keep aspect ratio':grinsRC.ID_K,

		'Hyper&link':grinsRC.ID_L,

		'&Mediaserver':grinsRC.ID_M,
		'Preroll ti&me':grinsRC.ID_M,

		'z-i&ndex':grinsRC.ID_N,
		'Hyperli&nk destination':grinsRC.ID_N,

		'P&osition and size':grinsRC.ID_O,

		'Image &quality':grinsRC.ID_Q,

		'Ta&rget audience':grinsRC.ID_R,
		'Image &region':grinsRC.ID_R,

		'&System properties':grinsRC.ID_S,
		 'Tran&sition type':grinsRC.ID_S,
		'Web&server':grinsRC.ID_S,

		'&Timing':grinsRC.ID_T,
		'HTML &template':grinsRC.ID_T,

		'&URL':grinsRC.ID_U,
		'Base &URL':grinsRC.ID_U,

		'&Video type':grinsRC.ID_V,

		'&Z order':grinsRC.ID_Z,
		'Image si&ze':grinsRC.ID_Z,
		}

	def __init__(self,wnd,data=None):
		self._wnd=wnd	
		self._prsht=wnd._prsht
		self._pages = wnd._pages

		tabctrl=self._prsht.GetTabCtrl()
		n = tabctrl.GetItemCount()
		self._tabnames={}
		for i in range(n):
			text = tabctrl.GetItemText(i)
			self._tabnames[text]=i
		if len(self._tabnames)==1:
			return
		if data:
			self._data=data	
		else:
			self._data=TabShortcut.data
		self._tabctrl=tabctrl
		self._id2name={}
		self.hookcommands()

	def hookcommands(self):
		sbuf=''
		for s,id in self._data.items():
			shortcut,name=self.splitshortcutname(s)
			if shortcut and string.find(sbuf,shortcut)<0 \
				and self._tabnames.has_key(name):
				self._wnd.HookCommand(self.oncmd,id)
				self._id2name[id]=name
				sbuf=sbuf+shortcut
				ix = self._tabnames[name]
				self._tabctrl.SetItemText(ix,s)

	def oncmd(self,id,code):
		if self._id2name.has_key(id):
			self.setactivepage(self._id2name[id])

	def splitshortcutname(self,name):
		if name[0]=='&':
			return name[1],name[1:]
		l=string.split(name,'&')
		if len(l)==2:
			return l[1][0],l[0]+l[1]
		return None,name

	def setactivepage(self,name):
		if self._tabnames.has_key(name):
			i = self._tabnames[name]
			page = self._pages[i]
			self._prsht.SetActivePage(page)



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
		self._window_created = 0

	# Creates the actual OS window
	def createWindow(self, parent):
		self._parent=parent
		import __main__
		dll=__main__.resdll
		prsht=AttrSheet(self)
		prsht.EnableStackedTabs(1)
		self._prsht = prsht

		self.buildcontext()

		initindex = self.buildpages()

		if not self._window_created:
			self.CreateWindow(parent)
			self._window_created = 1
		prsht.CreateWindow(self,win32con.DS_CONTEXTHELP | win32con.DS_SETFONT | win32con.WS_CHILD | win32con.WS_VISIBLE)
		self.HookMessage(self.onSize,win32con.WM_SIZE)		
		rc=self.GetWindowRect()
		prsht.SetWindowPos(0,(0,0,0,0),
			win32con.SWP_NOACTIVATE | win32con.SWP_NOSIZE)

		self.finishbuildpages(initindex)

		# remove the next line to disable tabs shortcuts
##		self._tabshortcut = TabShortcut(self)

	def buildpages(self):
		prsht = self._prsht
		grattrl=[] # list of attr in groups (may be all)
		# create groups pages
		grattrl=self.creategrouppages()
		
		# create singletons not desrcibed by groups
		for i in range(len(self._attriblist)):
			a=self._attriblist[i]
			if a not in grattrl:
				if not a.mustshow():
					page = None
				else:
					page=SingleAttrPage(self,a)
					self._pages.append(page)
				self._a2p[a]=page

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

		# Create a dummy page if there is nothing there
		if not self._pages:
			page = EmptyAttrPage(self)
			self._pages.append(page)
			page.do_init()
			prsht.AddPage(page)
			page.settabix(0)
		return initindex
	
	def finishbuildpages(self, initindex):
		prsht = self._prsht
		tabctrl=prsht.GetTabCtrl()
		for page in self._pages:
			page.settabtext(tabctrl)

		prsht.SetActivePage(self._pages[initindex])
		prsht.RedrawWindow()

	def removepages(self):
		for p in self._pages:
			p.do_close()
		for p in self._pages:
			self._prsht.RemovePage(p)
##		self._prsht = None # XXX Should we close or something?
		self._pages = []

	def showAllAttributes(self, flag):
		previous = -1
		if self._prsht and self._prsht._showAll:
			previous = self._prsht._showAll.getcheck()
			if flag:
				if not previous:
					self.call('Showall')
			else:
				if previous:
					self.call('Showall')
		return previous
						
	def RecreateWindow(self):
		try:
			old_focus = win32ui.GetFocus()
		except win32ui.error:
			old_focus = None
		self.SetRedraw(0)
		self.removepages()
		self._attrchanged={}
##		self.createWindow(self._parent)
##		return
		self.buildcontext()

		initindex = self.buildpages()

		self._prsht.SetWindowPos(0,(0,0,0,0),
			win32con.SWP_NOACTIVATE | win32con.SWP_NOSIZE)

		self.finishbuildpages(initindex)
		self.SetRedraw(1)
		self.RedrawWindow()
		if old_focus:
			try:
				old_focus.SetFocus()
			except:
				print 'AttrEditForm.RecreateWindow: unexpected error on set focus'

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
		try:
			old_focus = win32ui.GetFocus()
		except win32ui.error:
			old_focus = None
		self._prsht.SetActivePage(p)
		if old_focus:
			old_focus.SetFocus()

	def setcurattrbyname(self,name):
		a = self.getattrbyname(name)
		if a: self.setcurattr(a)

	def creategrouppages(self):
		grattrl=[]	 # all attr in groups
		l=self._attriblist[:]
		for grdict in attrgrs:
			grname=grdict['name']
			if not groupsui.has_key(grname):
				print 'Attrgroup not in groupsui:', grname
				continue
			group=groupsui[grname]()
			group.visit(l)
			if group.matches():
				if group.dont_show_anything():
					grouppage = None
				else:
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
	def getunits(self):
		if self._channel:
			return self._channel.attrdict.get('units', appcon.UNIT_SCREEN)
		return appcon.UNIT_PXL
			
	def buildcontext(self):
		self._node = None
		self._channel = None

		if not self._attriblist:
			return

		a = self._attriblist[0]

		if hasattr(a.wrapper, 'context'):
			self._baseURL = a.wrapper.context.baseurl

		if hasattr(a.wrapper,'node'):
			self._node = a.wrapper.node
 			if hasattr(a.wrapper, 'toplevel') and a.wrapper.toplevel:
				try:
					chname = self.getchannel(self._node)
					if chname:
						self._channel =  a.wrapper.toplevel.root.context.channeldict[chname]
				except:
					self._channel =  None
		else:
 			self._node = None		
	
	def getchannel(self,node):
		import MMAttrdefs
		return MMAttrdefs.getattr(node, 'channel')
					
	def OnInitialUpdate(self):
		GenFormView.OnInitialUpdate(self)
		self._is_active = 0

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
		dh=3*win32api.GetSystemMetrics(win32con.SM_CYEDGE)
		frc=(rc[0],rc[1]%8,frc[2]-frc[0]+rc[0]+dw,frc[3]-frc[1] + dh + rc[1]%8)
		self._parent.MoveWindow(frc) 

	# Called when the view is activated 
	def activate(self):
		GenFormView.activate(self)
		childframe=self.GetParent()
		frame=childframe.GetMDIFrame()
		frame.LoadAccelTable(grinsRC.IDR_ATTR_EDIT)
		
	# Called when the view is deactivated 
	def deactivate(self):
		GenFormView.deactivate(self)
		childframe=self.GetParent()
		frame=childframe.GetMDIFrame()
		frame.LoadAccelTable(grinsRC.IDR_GRINSED)

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
		childframe = self.GetParent()
		frame = childframe.GetMDIFrame()
		frame.BringWindowToTop()
		childframe.ShowWindow(win32con.SW_SHOW)
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
		p = self._a2p.get(attrobj)
		if not p:
			# this causes the current value to be used
			raise AttributeError('attribute not available')
		return p.getvalue(attrobj)

	# Called by the core system to set a value on the list
	def setvalue(self,attrobj,newval):
		if attrobj not in self._attriblist:
			raise error, 'item not in list'
		p = self._a2p.get(attrobj)
		if not p:
			return
		p.setvalue(attrobj,newval)

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
		p = self._a2p.get(attrobj)
		if p:
			p.setoptions(attrobj,list,val)

	def onDirty(self):
		self._tid=None
		self.buildcontext()

	def OnDestroy(self,params):
		if self._tid:
			import __main__
			__main__.toplevel.canceltimer(self._tid)
 
 
