__version__ = "$Id$"

""" @win32doc|components
The components defined in this module are a sufficient 
family of light-weight controls (Button,Edit,etc)
The controls are not based on MFC but on win32 Sdk.
They are at the same level as MFC is to the Sdk 
(a fact that justifies the name light weight)
This is in contrast to all the objects exported by the 
win32ui pyd which exports inherited objects from MFC objects
"""

import win32ui, win32con, win32api
import commctrl
import afxres
Sdk=win32ui.GetWin32Sdk()
import grinsRC
import win32mu
import string
import features
import math

[FALSE, TRUE] = range(2)
error = 'lib.win32.components.error'

# Base class for SDK based controls
class LightWeightControl:
	def __init__(self,parent=None,id=-1,hwnd=None):
		self._id=id
		self._parent=parent
		if parent and hasattr(parent,'_subwndlist'):
			parent._subwndlist.append(self)
		self._hwnd=hwnd
		self._cb=None
		self._hfont = 0
	def __del__(self):
		if self._hfont:
			Sdk.DeleteObject(self._hfont)
	def sendmessage(self,msg,wparam=0,lparam=0):
		if not self._hwnd: raise error, 'os control has not been created'
		return Sdk.SendMessage(self._hwnd,msg,wparam,lparam)
	def sendmessage_ls(self,msg,wparam,lparam):
		if not self._hwnd: raise error, 'os control has not been created'
		return Sdk.SendMessageLS(self._hwnd,msg,wparam,lparam)
	def sendmessage_rs(self,msg,wparam,lparam):
		if not self._hwnd: raise error, 'os control has not been created'
		return Sdk.SendMessageRS(self._hwnd,msg,wparam,lparam)
	def sendmessage_ra(self,msg):
		if not self._hwnd: raise error, 'os control has not been created'
		return Sdk.SendMessageRA(self._hwnd,msg)
	def sendmessage_gl(self,msg,wparam,lparam=0):
		if not self._hwnd: raise error, 'os control has not been created'
		return Sdk.SendMessageGL(self._hwnd,msg,wparam,lparam)
	def sendmessage_gt(self,msg,wparam,lparam=0):
		if not self._hwnd: raise error, 'os control has not been created'
		return Sdk.SendMessageGT(self._hwnd,msg,wparam,lparam)	
	def sendmessage_getrect(self,msg,wparam,lparam=0):
		if not self._hwnd: raise error, 'os control has not been created'
		return Sdk.SendMessageGetRect(self._hwnd,msg,wparam,lparam)	
	def sendmessage_setrect(self, msg, wparam, rect):
		if not self._hwnd: raise error, 'os control has not been created'
		return Sdk.SendMessageGetRect(self._hwnd,msg,wparam,rect)	
	def sendmessage_ms(self, msg, wparam, lparam):
		if not self._hwnd: raise error, 'os control has not been created'
		return Sdk.SendMessageMS(self._hwnd, msg, wparam, lparam)
	def enable(self,f):
		if not self._hwnd: raise error, 'os control %d has not been created'
		if f==None:f=0
		Sdk.EnableWindow(self._hwnd,f)
	def show(self):
		if not self._hwnd: raise error, 'os control has not been created'
		Sdk.ShowWindow(self._hwnd,win32con.SW_SHOW)
	def hide(self):
		if not self._hwnd: raise error, 'os control has not been created'
		Sdk.ShowWindow(self._hwnd,win32con.SW_HIDE)
	def attach(self,hwnd):
		self._hwnd=hwnd
	def attach_to_parent(self):
		if not self._parent: raise error, 'attach_to_parent without parent'	
		hparent = self._parent.GetSafeHwnd()
		if not hparent: raise error, 'parent is not a window'
		self.attach(Sdk.GetDlgItem(hparent,self._id))
	def init(self):
		"""called when os wnd exists"""
		pass
	def detach(self):
		hwnd=self._hwnd
		self._hwnd=None
		return hwnd
	def fromhandle(self,hwnd):
		return self._class__(hwnd)
	def hookcommand(self,obj,cb):
		obj.HookCommand(cb,self._id)
	def hookmessage(self,cb,msgid):
		if not self._hwnd: raise error, 'os control has not been created'
		wnd=window.Wnd(win32ui.CreateWindowFromHandle(self._hwnd))
		wnd.HookMessage(cb,msgid)
	def hasid(self,id):
		return id==self._id
	def create(self, wc, rc, name=''):
		if hasattr(self._parent,'GetSafeHwnd'):
			hwnd=self._parent.GetSafeHwnd()
		else:
			hwnd=self._parent
		self._hwnd = Sdk.CreateWindowEx(wc.exstyle,wc.classid,name,wc.style,rc,hwnd,self._id)
	def destroy(self):
		if self._hwnd:
			return Sdk.DestroyWindow(self._hwnd)
		return 1
	def setwindowpos(self,hInsertAfter,rc,flags):
		if not self._hwnd: raise error, 'os control has not been created'
		Sdk.SetWindowPos(self._hwnd,hInsertAfter,rc,flags)
	def getwindowrect(self):
		if not self._hwnd: raise error, 'os control has not been created'
		return Sdk.GetWindowRect(self._hwnd)
	def getclientrect(self):
		if not self._hwnd: raise error, 'os control has not been created'
		l, t, r, b = Sdk.GetWindowRect(self._hwnd)
		return 0, 0, r-l, b-t 
	def movewindow(self, rc, repaint = 1):
		if not self._hwnd: raise error, 'os control has not been created'
		Sdk.MoveWindow(self._hwnd, rc, repaint)
	def setstyleflag(self,flag):
		if not self._hwnd: raise error, 'os control has not been created'
		style = Sdk.GetWindowLong(self._hwnd,win32con.GWL_STYLE)
		style = style | flag
		Sdk.SetWindowLong(self._hwnd,win32con.GWL_STYLE,style)
	def settext(self,str):
		self.sendmessage_ls(win32con.WM_SETTEXT,0,str)
	def seticon(self,icon):
		return self.sendmessage(win32con.BM_SETIMAGE,win32con.IMAGE_ICON,icon)
	# mimic mfc wnd method
	def GetSafeHwnd(self):
		return self._hwnd
	def setcb(self,cb):
		self._cb=cb
	def callcb(self):
		if self._cb: 
			apply(apply,self._cb)
	def setfont(self, lf=None):
		if self._hfont:
			Sdk.DeleteObject(self._hfont)
		if lf is None:
			lf = {'name':'MS San Serif', 'height': 11, 'weight': win32con.FW_NORMAL}
		self._hfont = Sdk.CreateFontIndirect(lf)
		if self._hfont:
			self.sendmessage(win32con.WM_SETFONT, self._hfont, 1)


# shortcut
Control = LightWeightControl

# Button control class
class Button(Control):
	def __init__(self,owner=None,id=-1):
		Control.__init__(self,owner,id)
	def setstate(self, f):
		self.sendmessage(win32con.BM_SETSTATE,f)
	def getstate(self):
		return self.sendmessage(win32con.BM_GETSTATE)
	def ispushed(self):
		return win32con.BST_PUSHED & self.getstate()

# RadioButton control class
class RadioButton(Control):
	def __init__(self,owner=None,id=-1):
		Control.__init__(self,owner,id)
	def setcheck(self,i):
		if i>0:f=win32con.BST_CHECKED
		elif i==0:f=win32con.BST_UNCHECKED
		else:f=win32con.BST_INDETERMINATE
		self.sendmessage(win32con.BM_SETCHECK,f)
	def getcheck(self):
		f=self.sendmessage(win32con.BM_GETCHECK)
		if f==win32con.BST_CHECKED:return 1
		elif f==win32con.BST_UNCHECKED:return 0
		return -1

# CheckButton control class
class CheckButton(Control):
	def __init__(self,owner=None,id=-1):
		Control.__init__(self,owner,id)
	def setcheck(self,i):
		if i>0:f=win32con.BST_CHECKED
		elif i==0:f=win32con.BST_UNCHECKED
		else:f=win32con.BST_INDETERMINATE
		self.sendmessage(win32con.BM_SETCHECK,i)
	def getcheck(self):
		i=self.sendmessage(win32con.BM_GETCHECK)
		if i==win32con.BST_CHECKED:return 1
		elif i==win32con.BST_UNCHECKED:return 0
		return -1

# Progress bar control
class ProgressControl(Control):
	def __init__(self,owner=None,id=-1):
		Control.__init__(self,owner,id)
	def set(self,i):
		self.sendmessage(commctrl.PBM_SETPOS,i)
	def setrange(self, min, max):
		i=self.sendmessage(commctrl.PBM_SETRANGE32, min, max)
	# The others like step and setstep and getrange, aren't needed at the moment

# Static control class
class Static(Control):
	def __init__(self,owner=None,id=-1):
		Control.__init__(self,owner,id)

# Edit control class 				
class Edit(Control):
	def __init__(self,owner=None,id=-1):
		Control.__init__(self,owner,id)
	def settext(self,str):
		self.sendmessage_ls(win32con.WM_SETTEXT,0,str)
	def gettextlength(self):
		return self.sendmessage(win32con.WM_GETTEXTLENGTH)
	def gettext(self):
		n=self.gettextlength()+1
		return self.sendmessage_rs(win32con.WM_GETTEXT,n,n)	
	def getlinecount(self):
		return self.sendmessage(win32con.EM_GETLINECOUNT)
	def getline(self,ix):
		return self.sendmessage_gl(win32con.EM_GETLINE,ix)
	def getmodify(self):
		return self.sendmessage(win32con.EM_GETMODIFY)
	def setmodify(self, flag):
		return self.sendmessage(win32con.EM_SETMODIFY, flag)
	def getsel(self):
		return self.sendmessage_ra(win32con.EM_GETSEL)[:2]
	def setsel(self, start, end):
		return self.sendmessage(win32con.EM_SETSEL, start, end)
	def setreadonly(self, readonly):
		return self.sendmessage(win32con.EM_SETREADONLY, readonly)
	def linescroll(self, nlines, nchars = 0):
		# note reversal of arguments
		return self.sendmessage(win32con.EM_LINESCROLL, nchars, nlines)
	def getfirstvisibleline(self):
		return self.sendmessage(win32con.EM_GETFIRSTVISIBLELINE)
	def getinspos(self):
		return self.sendmessage_ra(win32con.EM_GETSEL)[2]

	def getlines(self):
		if hasattr(self,'_textlines'):
			if self.getmodify()==0:
				return self._textlines
		self._textlines=[]
		nl=self.getlinecount()
		for ix in range(nl):
			line=self.getline(ix)
			self._textlines.append(line)
		return self._textlines

	def _getlines(self):
		textlines=[]
		nl=self.getlinecount()
		for ix in range(nl):
			line=self.getline(ix)
			textlines.append(line)
		return textlines

	# cmif interface
	# gettext
	# settext

# Listbox control class
class ListBox(Control):
	def __init__(self,owner=None,id=-1):
		Control.__init__(self,owner,id)
		self.__icmif() 
	def setcursel(self,index):
		if index==None: index=-1
		self.sendmessage(win32con.LB_SETCURSEL,index)
	def getcursel(self):
		return self.sendmessage(win32con.LB_GETCURSEL)
	def getcount(self):
		return self.sendmessage(win32con.LB_GETCOUNT)
	def deletestring(self,index):
		self.sendmessage(win32con.LB_DELETESTRING,index)
	def insertstring(self,ix,str):
		self.sendmessage_ls(win32con.LB_INSERTSTRING,ix,str)
	def addstring(self,ix,str):
		return self.sendmessage_ls(win32con.LB_ADDSTRING,0,str)
	def gettextlen(self,ix):
		return self.sendmessage(win32con.LB_GETTEXTLEN,ix)
	def gettext(self,ix):
		n = self.gettextlen(ix) + 1
		return self.sendmessage_rs(win32con.LB_GETTEXT,ix,n)
	def resetcontent(self):
		self.sendmessage(win32con.LB_RESETCONTENT)
	def sethorizontalextent(self,npixels):
		self.sendmessage(win32con.LB_SETHORIZONTALEXTENT,npixels)
	def getitemrect(self, index):
		return self.sendmessage_getrect(win32con.LB_GETITEMRECT ,index)

	# Multi-select list support
	def getselcount(self):
		return self.sendmessage(win32con.LB_GETSELCOUNT)
	def getselitems(self, itemNumber):
		return self.sendmessage_gt(win32con.LB_GETSELITEMS, itemNumber)
	
	# cmif interface
	# initialize cmif related part
	def __icmif(self):
		self.getlistitem=self.gettext
		self.selectitem=self.setcursel
		self.getselection=self.getcursel
		self.delalllistitems=self.resetcontent
	# Add a list item
	def addlistitem(self, item, pos):
		if pos < 0:
			pos = self.getcount()
		self.insertstring(pos,item)
	
	# Replace the item at position
	def replace(self, pos, newitem):
		self.deletestring(pos)
		self.insertstring(pos,newitem)
	
	# Return the list
	def getlist(self):
		l=[]
		for ix in range(self.getcount()):
			l.append(self.gettext(ix))
		return l

	# Add the list of entries
	def addlistitems(self,list,ix=0):
		if type(list)==type(''): 
			self.insertstring(ix,list)
			return
		if ix==-1:
			for pos in range(len(list)):
				self.insertstring(-1,list[pos])
		elif ix>=0:
			for pos in range(ix,len(list)):
				self.insertstring(pos,list[pos])

	# Return  the selection index				
	def getselected(self):
		pos = self.getselection()
		if pos<0:return None
		return pos

	# Return the item at the index
	def getlistitem(self,ix):
		return self.gettext(ix)

	def recalchorizontalextent(self):
		from Font import _Font
		font = _Font('MS Sans Serif',8)
		npixels = 0
		l = self.getlist()
		for s in l:
			np = font.gettextextent(s)[0]
			if np>npixels:
				npixels = np
		npixels = npixels + 8  # plus 8 pixel margin 
		self.sendmessage(win32con.LB_SETHORIZONTALEXTENT,npixels)


class DnDListBox(ListBox):
	def __init__(self,owner=None,id=-1):
		ListBox.__init__(self, owner, id)
		self._dragging = None
		self.CF_LISTBOX_ITEM = Sdk.RegisterClipboardFormat('ListBoxItem')

	def attach_to_parent(self):
		ListBox.attach_to_parent(self)
		wnd = win32ui.CreateWindowFromHandle(self._hwnd)
		wnd.SubclassDlgItem(self._id, self._parent)
		wnd.HookMessage(self.onLButtonDown,win32con.WM_LBUTTONDOWN)
		wnd.HookMessage(self.onLButtonUp,win32con.WM_LBUTTONUP)
		wnd.HookMessage(self.onMouseMove,win32con.WM_MOUSEMOVE)
		self._mfcwnd = wnd

	def isPtInRect(self, rc, pt):
		l, t, r, b = rc
		x, y = pt
		return (x >= l and x < r and y >= t and y < b)

	def getItemAt(self, pos):
		n = self.getcount()
		for ix in range(n):
			rc = self.getitemrect(ix)
			if self.isPtInRect(rc, pos):
				return ix
		return -1

	def onLButtonDown(self, params):
		msg=win32mu.Win32Msg(params)
		self._dragging = msg.pos()
		return 1

	def onLButtonUp(self, params):
		msg=win32mu.Win32Msg(params)
		if self._dragging: 
			self._dragging = None
		return 1

	def onMouseMove(self, params):
		msg=win32mu.Win32Msg(params)
		if self._dragging:
			xp, yp = self._dragging
			x, y = msg.pos()
			if math.fabs(xp-x)>4 or math.fabs(yp-y)>4:
				index = self.getItemAt(self._dragging)
				str = self.gettext(index)
				print 'dragging item:', str
				# start drag and drop
				self._mfcwnd.DoDragDrop(self.CF_LISTBOX_ITEM, str)
				self._dragging = None
		return 1


# ComboBox control class
class ComboBox(Control):
	def __init__(self,owner=None,id=-1):
		Control.__init__(self,owner,id)
		self.__icmif() 
	def setcursel(self,index):
		if index==None: index=-1
		self.sendmessage(win32con.CB_SETCURSEL,index)
	def getcursel(self):
		return self.sendmessage(win32con.CB_GETCURSEL)
	def getcount(self):
		return self.sendmessage(win32con.CB_GETCOUNT)
	def insertstring(self,ix,str):
		if not str: str='---'
		self.sendmessage_ls(win32con.CB_INSERTSTRING,ix,str)
	def addstring(self,str):
		if not str: str='---'
		return self.sendmessage_ls(win32con.CB_ADDSTRING,0,str)
	def gettextlen(self,ix):
		return self.sendmessage(win32con.CB_GETLBTEXTLEN,ix)
	def gettext(self,ix):
		n = self.gettextlen(ix) + 1
		return self.sendmessage_rs(win32con.CB_GETLBTEXT,ix,n)
	def resetcontent(self):
		self.sendmessage(win32con.CB_RESETCONTENT)
	def deletestring(self,index):
		self.sendmessage(win32con.CB_DELETESTRING,index)
	# edit box like interface
	def setedittext(self,str):
		self.sendmessage_ls(win32con.WM_SETTEXT,0,str)
	def getedittextlength(self):
		return self.sendmessage(win32con.WM_GETTEXTLENGTH)
	def getedittext(self):
		n=self.getedittextlength()+1
		return self.sendmessage_rs(win32con.WM_GETTEXT,n,n)	

	# cmif interface
	def __icmif(self):
		self._optionlist=[]
		
	# it is called when os wnd exists
	def init(self):
		for s in self._optionlist:
			self.addstring(s)
		self.setcursel(0)

	def getpos(self):
		'''Get the index of the currently selected option.'''
		return self.getcursel()
	def setpos(self,pos):
		'''Set the index of the selected option.'''
		self.setcursel(pos)

	def getvalue(self):
		'''Get the value of the currently selected option.'''
		sel=self.getcursel()
		return self.gettext(sel)

	def setoptions(self, optionlist, startpos=0):
		if not optionlist: return
		for pos in range(startpos,len(optionlist)):
			self.insertstring(pos,optionlist[pos])
			self._optionlist.append(optionlist[pos])
	def initoptions(self, optionlist,seloption=None):
		self.resetcontent()
		if not optionlist: return
		self.setoptions(optionlist)
		self.setcursel(seloption)	
	def setoptions_cb(self, optionlist):
		for item in optionlist:
			if type(item)==type(()):
				if item[0]=='Cancel':continue
				self.addstring(item[0])
				self._optionlist.append(item[0])
		self.setcursel(0)
	def setsensitive(self,pos,f):
		seloption=self.getcursel()
		str=self._optionlist[pos]
		if f:
			self.deletestring(pos)
			self.insertstring(pos,str) # add it
		else: 
			self.deletestring(pos) # remove it
			str='['+str+']'
			self.insertstring(pos,str)
		self.setcursel(seloption)
	

##################
# A special class that it is both an MFC window and A LightWeightControl

from pywinlib.mfc import window

class WndCtrl(LightWeightControl,window.Wnd):
	def create_wnd_from_handle(self):
		window.Wnd.__init__(self,win32ui.CreateWindowFromHandle(self._hwnd))

####################################################
# TAB CONTROL STUFF

# Tab control class
class TabCtrl(Control):
	TCM_FIRST  =            0x1300      # Tab control messages
	TCN_FIRST =-550       
	TCN_LAST=-580
	TCN_SELCHANGE  = TCN_FIRST - 1
	TCN_SELCHANGING= TCN_FIRST - 2

	def __init__(self,owner=None,id=-1):
		Control.__init__(self,owner,id)
	def insertitem(self,ix,text):
		mask,ixImage,mp_appdata,text=(commctrl.TCIF_TEXT,-1,0,text)
		mp=Sdk.New('TCITEM',(mask,ixImage,mp_appdata,text))
		self.sendmessage(commctrl.TCM_INSERTITEM,ix,mp)
		Sdk.Delete(mp)
	def setcursel(self,ix):
		self.sendmessage(commctrl.TCM_SETCURSEL,ix)
	def getcursel(self):
		return self.sendmessage(commctrl.TCM_GETCURSEL)

####################################################
# Tooltip control
class Tooltip(Control):
	def __init__(self, parent=None, id=-1):
		Control.__init__(self, parent, id)
		self._toolscounter = 0
		self._cptext = {}
		self._lbuttondown = 0

	def createWindow(self, rc=(0,0,0,0), title=''):
		#Sdk.InitCommonControlsEx()
		hwnd = self._parent.GetSafeHwnd()
		rcd = win32con.CW_USEDEFAULT, win32con.CW_USEDEFAULT, win32con.CW_USEDEFAULT, win32con.CW_USEDEFAULT
		self._hwnd = Sdk.CreateWindowEx(win32con.WS_EX_TOPMOST, 'tooltips_class32', title, win32con.WS_POPUP 
			 # | commctrl.TTS_ALWAYSTIP
			,rcd, hwnd, self._id)
		Sdk.SetWindowPos(self._hwnd, win32con.HWND_TOPMOST, (0,0,0,0),
			win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_NOACTIVATE)

	def destroy(self):
		Control.destroy(self)
		for cp in self._cptext.values():
			Sdk.GetWMString(cp)
		del self._cptext

	def __releasetoolres(self, toolid):
		cp = self._cptext.get(toolid)
		if cp: 
			Sdk.GetWMString(cp)
			del self._cptext[toolid]
		
	def addTool(self, toolid, rc, text):
		assert not self._cptext.has_key(toolid), 'tool already exists'
		hwnd = self._parent.GetSafeHwnd()
		cp = Sdk.AddTool(self._hwnd, hwnd, toolid, rc, text)
		self._cptext[toolid] = cp
		self._toolscounter = self._toolscounter + 1
	
	def delTool(self, toolid):
		assert self._cptext.has_key(toolid), 'tool does not exist'
		hwnd = self._parent.GetSafeHwnd()
		Sdk.DelTool(self._hwnd, hwnd, toolid)
		self._toolscounter = self._toolscounter - 1
		self.__releasetoolres(toolid)
		
	def relayEvent(self, params):
		assert self._hwnd>0, 'Tooltip control has not been created'
		if self._toolscounter == 0: 
			return
		hwnd, message, wParam, lParam, time, pt = params
		params = hwnd, message, wParam, lParam, 0, lParam
		self.sendmessage_ms(commctrl.TTM_RELAYEVENT, 0, params)

	def onLButtonDown(self, params):
		self.sendmessage(commctrl.TTM_ACTIVATE, 0, 0)
		self._lbuttondown = 1
		self.relayEvent(params)

	def onLButtonUp(self, params):
		if not self._lbuttondown:
			return
		self._lbuttondown = 0
		self.relayEvent(params)

	def onMouseMove(self, params):
		if self._lbuttondown:
			hwnd, message, wParam, lParam, time, pt = params
			newparams = hwnd, win32con.WM_LBUTTONUP, wParam, lParam, time, lParam
			self.onLButtonUp(params)
		self.relayEvent(params)

	def activate(self, flag):
		if flag: 
			flag = 1
		else: 
			flag = 0
		self.sendmessage(commctrl.TTM_ACTIVATE, flag, 0)

	def settoolrect(self, toolid, rc):
		hwnd = self._parent.GetSafeHwnd()
		Sdk.NewToolRect(self._hwnd, hwnd, toolid, rc)

	def updatetiptext(self, toolid, text):
		assert self._cptext.has_key(toolid), 'tool does not exist'
		cp = self._cptext[toolid]
		hwnd = self._parent.GetSafeHwnd()
		Sdk.UpdateTipText(self._hwnd, hwnd, toolid, text, cp)

	# removes a displayed tooltip window from view. 
	def pop(self):
		self.sendmessage(commctrl.TTM_POP, 0, 0)

	# forces the current tool to be redrawn. 
	def update(self):
		self.sendmessage(commctrl.TTM_UPDATE, 0, 0)

	# sets the top, left, bottom, and right margins for a tooltip window. 
	# a margin is the distance, in pixels, between the tooltip window border 
	# and the text contained within the tooltip window. 
	def setmargin(self, rc):
		self.sendmessage_setrect(commctrl.TTM_SETMARGIN, 0, rc)

	# set the maximum width for a tooltip window. 
	def setmaxtipwidth(self, w):
		self.sendmessage(commctrl.TTM_SETMAXTIPWIDTH, 0, w)

	def setdelay(self, which, msecs):
		whichid = None
		if which == 'autopop':
			whichid = commctrl.TTDT_AUTOPOP
		elif which == 'initial':
			whichid = commctrl.TTDT_INITIAL
		elif which == 'reshow':
			whichid = commctrl.TTDT_RESHOW
		if whichid is not None:
			self.sendmessage(commctrl.TTM_SETDELAYTIME, whichid, msecs)
	
	def settiptextcolor(self, color):
		r, g, b = color
		self.sendmessage(commctrl.TTM_SETTIPTEXTCOLOR, win32api.RGB(r, g, b), 0)

	def settipbgcolor(self, color):
		r, g, b = color
		self.sendmessage(commctrl.TTM_SETTIPBKCOLOR, win32api.RGB(r, g, b), 0)
	

##############################
# TipWindow (not lightweight)
# A window similar to the tip-popup the tooltip control uses
# The purpose is to have a comletely customizable tip window 
 
class TipWindow(window.Wnd):
	def __init__(self, parent):
		window.Wnd.__init__(self,win32ui.CreateWnd())
		self._parent = parent
		self._text = None
		self._bgcolor = 0xFF, 0xFF, 0xE0 # LightYellow
		self._rect = 20, 20, 112, 38
		self._margins = 2, 0, 2, 0
		self._dxoffset = 16
		self._blackbrush = Sdk.CreateBrush(win32con.BS_SOLID,0,0)
		fd = {'name':'Arial','height':10,'weight':500}
		self._hsmallfont = Sdk.CreateFontIndirect(fd)		

	def create(self):
		brush = Sdk.CreateBrush(win32con.BS_SOLID, win32mu.RGB(self._bgcolor), 0)
		strclass = win32ui.GetAfx().RegisterWndClass(0, 0, brush, 0)
		style = win32con.WS_POPUP
		self.CreateWindowEx(win32con.WS_EX_TOPMOST, strclass, '', style,
			self._rect, self._parent, 0)
	
	def OnDestroy(self, params):
		Sdk.DeleteObject(self._blackbrush)
		Sdk.DeleteObject(self._hsmallfont)

	def OnPaint(self):
		dc, paintStruct = self.BeginPaint()
		dc.SetBkMode(win32con.TRANSPARENT)
		l, t, r, b = self.GetClientRect()
		dc.FillSolidRect((l, t, r, b), win32mu.RGB(self._bgcolor or (255,255,255)))
		if self._text is not None:
			dl, dt, dr, db = self._margins
			hf = dc.SelectObjectFromHandle(self._hsmallfont)
			dc.DrawText(self._text, (l+dl, t+dt, r-dr, b-db))
			dc.SelectObjectFromHandle(hf)
		dc.FrameRectFromHandle(self.GetClientRect(), self._blackbrush)
		self.EndPaint(paintStruct)
	
	def OnEraseBkgnd(self,dc):
		return 1 # promise: we will paint our background

	def settext(self, text):
		self._text = text
		if Sdk.IsWindow(self.GetSafeHwnd()):
			self.InvalidateRect(self.GeClientRect())

	def moveTo(self, pos, text, show=1):
		self._text = text
		x, y = pos
		x =  x + self._dxoffset
		rc = self.GetWindowRect()
		Sdk.SetWindowPos(self.GetSafeHwnd(), win32con.HWND_TOPMOST, (x,y,0,0),
			win32con.SWP_NOSIZE | win32con.SWP_NOACTIVATE |  win32con.SWP_NOZORDER | win32con.SWP_NOREDRAW)
		if show and not self.IsWindowVisible():
			self.ShowWindow(win32con.SW_SHOW)
		self.__updatewnd(self._parent, rc)
		self.__updatewnd(self._parent.GetParent(), rc)
		self.InvalidateRect()

	def show(self):
		self.ShowWindow(win32con.SW_SHOW)
						
	def hide(self):
		self.ShowWindow(win32con.SW_HIDE)
			
	def __updatewnd(self, wnd, rc):
		rc = wnd.ScreenToClient(rc)
		wnd.InvalidateRect(rc)
		wnd.UpdateWindow()

##############################
# Base class for controls creation classes
class WndClass:
	classid = None
	style = 0
	exstyle = 0
	def __init__(self, **kwargs):
		for attr, val in kwargs.items():
			setattr(self, attr, val)

# Edit control creation class 
class EDIT(WndClass):
	def __init__(self,style=0,exstyle=0):
		WndClass.__init__(self,
			classid='EDIT',
			style=win32con.WS_CHILD | win32con.WS_CLIPSIBLINGS | win32con.WS_VISIBLE | win32con.WS_TABSTOP  | style,
			exstyle=win32con.WS_EX_CONTROLPARENT| win32con.WS_EX_CLIENTEDGE | exstyle)

# Button control creation class 
class BUTTON(WndClass):
	def __init__(self,style=0,exstyle=0):
		WndClass.__init__(self,
			classid='BUTTON',
			style=win32con.WS_CHILD | win32con.WS_CLIPSIBLINGS | win32con.WS_VISIBLE | win32con.WS_TABSTOP |  style,
			exstyle=win32con.WS_EX_CONTROLPARENT| exstyle)

# PushButton control creation class 
# for left justification init with style BS_LEFTTEXT
class PUSHBUTTON(BUTTON):
	def __init__(self,style=0,exstyle=0):
		BUTTON.__init__(self,win32con.BS_PUSHBUTTON | style,exstyle)

# RadioButton control creation class 
# to change order of text and control init with BS_RIGHT (BS_LEFT is the default)
class RADIOBUTTON(BUTTON):
	def __init__(self,style=0,exstyle=0):
		BUTTON.__init__(self,win32con.BS_RADIOBUTTON | style,exstyle)
# CheckBox control creation class 
class AUTOCHECKBOX(BUTTON):
	def __init__(self,style=0,exstyle=0):
		BUTTON.__init__(self,win32con.BS_AUTOCHECKBOX | style,exstyle)
CHECKBOX=AUTOCHECKBOX		

class COMBOBOX(WndClass):
	def __init__(self,style=0,exstyle=0):
		WndClass.__init__(self,
			classid='COMBOBOX',
			style=win32con.WS_CHILD | win32con.WS_VISIBLE | win32con.CBS_DROPDOWNLIST | win32con.WS_VSCROLL | style,
			exstyle=exstyle)
	
# Create a window from its control class
def createwnd(wc,name,pos,size,parent,id):
	if hasattr(parent,'GetSafeHwnd'):
		hwnd=parent.GetSafeHwnd()
	else:
		hwnd=parent
	pl=(pos[0],pos[1],size[0],size[1])
	return Sdk.CreateWindowEx(wc.exstyle,wc.classid,name,wc.style,
			pl,hwnd,id)


##############################
# Any class derved from this class behaves as a dictionary
# Deprecated: will be removed soon
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
	def get(self, key, default): return self._subwnddict.get(key, default)
