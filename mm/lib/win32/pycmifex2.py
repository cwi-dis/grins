__version__ = "$Id$"


class Control(window.Wnd):
	def __init__(self,text,parent,x,y,cx,cy,id):
		window.Wnd.__init__(self,win32ui.CreateWnd())
		self._exstyle=WS_EX_CONTROLPARENT
		self._style=WS_CHILD | WS_CLIPSIBLINGS | WS_VISIBLE
		self._text=text
		self._parent=parent
		self._x=x
		self._y=y
		self._cx=cx
		self._cy=cy
	def create(self,strclass,id=0):
		self.CreateWindowEx(self._exstyle,strclass,self._text,self._style,
			(self._x,self._y,self._cx,self._cy),self._parent,id)

class Button(Control):
	def __init__(self,text,parent,x,y,cx,cy,type,justify,id=0):
		Control.__init__(self,text,parent,x,y,cx,cy)
		self._style = self._style | BS_NOTIFY
		if type=='b' or type == 'p':
			self._style = self._style | BS_PUSHBUTTON
		elif type== 'r':
			self._style = self._style | BS_RADIOBUTTON
		elif type=='t':
			self._style = self._style | BS_AUTOCHECKBOX
		if justify=='left':
			self._style = self._style | BS_LEFTTEXT
		self.create('BUTTON',id)

class Static(Control):
	def __init__(self,text,parent,x,y,cx,cy,type,justify,id=0):
		Control.__init__(self,text,parent,x,y,cx,cy)
		if justify=='left':
			self._style = self._style | SS_LEFT
		elif justify=='right':
			self._style = self._style | SS_RIGHT
		elif justify=='center':
			self._style = self._style | SS_CENTER
		self.create('STATIC')

class RCheckbox(Control):
	def __init__(self,text,parent,x,y,cx,cy,id=0):
		Control.__init__(self,text,parent,x,y,cx,cy)
		self._style = self._style | BS_NOTIFY | BS_CHECKBOX
		self.create('BUTTON',id)

class LCheckbox(Control):
	def __init__(self,text,parent,x,y,cx,cy,id=0):
		Control.__init__(self,text,parent,x,y,cx,cy)
		self._style = self._style | BS_NOTIFY | BS_CHECKBOX | BS_LEFTTEXT| BS_RIGHT
		self.create('BUTTON',id)

class RRadioButton(Control):
	def __init__(self,text,parent,x,y,cx,cy,id=0):
		Control.__init__(self,text,parent,x,y,cx,cy)
		self._style = self._style | BS_NOTIFY | BS_RADIOBUTTON
		self.create('BUTTON',id)

class LRadioButton(Control):
	def __init__(self,text,parent,x,y,cx,cy,id=0):
		Control.__init__(self,text,parent,x,y,cx,cy)
		self._style = self._style | BS_NOTIFY | BS_RADIOBUTTON | BS_LEFTTEXT | BS_RIGHT
		self.create('BUTTON',id)


class Group(Control):
	def __init__(self,text,parent,x,y,cx,cy,id=0):
		Control.__init__(self,text,parent,x,y,cx,cy)
		self._exstyle=self._exstyle | WS_EX_TRANSPARENT
		self._style = self._style | BS_GROUPBOX
		self.create('BUTTON',id)

class Separator(Control):
	def __init__(self,parent,x,y,cx,cy,vertical):
		self._exstyle=self._exstyle | WS_EX_TRANSPARENT
		self._style = self._style | BS_GROUPBOX
		if vertical: cx = 5
		else: cy = 5
		Control.__init__(self,'',parent,x,y,cx,cy)
		self.create('BUTTON')

class SEdit(Control):
	def __init__(self,text,parent,x,y,cx,cy,editable,id=0):
		Control.__init__(self,text,parent,x,y,cx,cy)
		self._exstyle=self._exstyle | WS_EX_CLIENTEDGE
		self._style = self._style | WS_BORDER | ES_AUTOHSCROLL
		if editable==0:
			self._style = self._style | ES_READONLY;
		self.create('EDIT',id)

class MEdit(Control):
	def __init__(self,text,parent,x,y,cx,cy,editable,id=0):
		Control.__init__(self,text,parent,x,y,cx,cy)
		self._exstyle=self._exstyle | WS_EX_CLIENTEDGE
		self._style = self._style | WS_BORDER | WS_VSCROLL | ES_AUTOVSCROLL | ES_MULTILINE | ES_WANTRETURN
		if editable==0:
			self._style = self._style | ES_READONLY;
		self.create('EDIT',id)


class Listbox(Control):
	def __init__(self,text,parent,x,y,cx,cy,sort,id=0):
		Control.__init__(self,text,parent,x,y,cx,cy)
		self._exstyle=self._exstyle | WS_EX_CLIENTEDGE
		self._style = self._style | WS_BORDER | WS_VSCROLL | WS_HSCROLL
		if sort==0:
			self._style = self._style | LBS_SORT
		self.create('LISTBOX',id)

class Combobox(Control):
	def __init__(self,text,parent,x,y,cx,cy,sort,drop,readonly,id=0):
		Control.__init__(self,text,parent,x,y,cx,cy)
		self._exstyle=self._exstyle | WS_EX_TRANSPARENT
		self._style = self._style | WS_BORDER | WS_VSCROLL | WS_HSCROLL | CBS_AUTOHSCROLL
		if sort==0:
			self._style = self._style | CBS_SORT
		if drop=='dr':
			if readonly==1:
				self._style = self._style | CBS_DROPDOWNLIST
			else:
				self._style = self._style | CBS_DROPDOWN
		else:
			self._style = self._style | CBS_SIMPLE
		self.create('COMBOBOX',id)

class Slider(Control):
	def __init__(self,text,parent,x,y,cx,cy,vertical,id=0):
		Control.__init__(self,text,parent,x,y,cx,cy)
		self._style = self._style | TBS_AUTOTICKS | TBS_ENABLESELRANGE
		if vertical:
			self._style = self._style | TBS_VERT | TBS_BOTH
		self.create(TRACKBAR_CLASS,id)
		self.SendMessage(TBM_SETRANGE,1)                  

class VSlider(Control):
	def __init__(self,text,parent,x,y,cx,cy,vertical,id=0):
		Control.__init__(self,text,parent,x,y,cx,cy)
		self._style = self._style | TBS_AUTOTICKS | TBS_ENABLESELRANGE |TBS_VERT | TBS_BOTH
		self.create(TRACKBAR_CLASS,id)
		self.SendMessage(TBM_SETRANGE,1)                  


class Dialogbox(window.Wnd):
	def __init__(self,text,parent,x,y,cx,cy,visible,grab):
		window.Wnd.__init__(self,win32ui.CreateWnd())
		self._exstyle=WS_EX_DLGMODALFRAME
		self._style=0
		self._text=text
		self._parent=parent
		self._x=x
		self._y=y
		self._cx=cx
		self._cy=cy
		if parent: 
			self._style = WS_POPUP
		if grab>0: 
			self._exstyle = self._exstyle | WS_EX_TOPMOST
		if visible==1:
			self._style = self._style|WS_CLIPCHILDREN|WS_VISIBLE|WS_SYSMENU|WS_CAPTION|WS_OVERLAPPED
		else:
			self._style = self._style|WS_CLIPCHILDREN|WS_CAPTION|WS_SYSMENU|WS_OVERLAPPED
		
		self._clstyle=CS_HREDRAW|CS_VREDRAW|CS_DBLCLKS
		self._icon=Afx.GetApp().LoadIcon(IDI_APPLICATION)
		self._cursor=Afx.GetApp().LoadStandardCursor(IDC_ARROW)
		self._brush=Sdk.GetStockObject(GRAY_BRUSH) # COLOR_BTNFACE

		strclass=Afx.RegisterWndClass(self._clstyle,self._cursor,self._brush,self._icon)
		self.CreateWindowEx(self._exstyle,strclass,self._text,self._style,
			(self._x,self._y,self._cx,self._cy),self._parent,0)

class Containerbox(window.Wnd):
	def __init__(self,parent,x,y,cx,cy):
		window.Wnd.__init__(self,win32ui.CreateWnd())
		self._exstyle=0
		self._style=WS_CHILD|WS_CLIPCHILDREN|WS_OVERLAPPED|WS_VISIBLE
		self._text=''
		self._parent=parent
		self._x=x
		self._y=y
		self._cx=cx
		self._cy=cy
		
		self._clstyle=CS_HREDRAW|CS_VREDRAW|CS_DBLCLKS
		self._icon=0
		self._cursor=Afx.GetApp().LoadStandardCursor(IDC_ARROW)
		self._brush=Sdk.GetStockObject(GRAY_BRUSH) # COLOR_BTNFACE

		strclass=Afx.RegisterWndClass(self._clstyle,self._cursor,self._brush,self._icon)
		self.CreateWindowEx(self._exstyle,strclass,self._text,self._style,
			(self._x,self._y,self._cx,self._cy),self._parent,0)


def SetWindowCaption(wnd,str):
	wnd.SetWindowText(str)

def CheckButton(wnd,i):
	wnd.SendMessage(BM_SETCHECK,i)

def GetCheck(wnd):
	return wnd.SendMessage(BM_GETCHECK)
CheckState=GetCheck # alias name in cmifex2
	
def GetText(wnd):
	return wnd.GetWindowText()
GetTextSize=GetText # alias name in cmifex2

def SetFont(wnd,facename,size):
	Ssk=win32ui.GetWin32Sdk()
	fd={'name':facename,'size':size,'weight':700}
	hfont=Sdk.CreateFontIndirect(fd)	
	wnd.SendMessage(WM_SETFONT,hfont,1)	
	Sdk.DeleteObject(hfont)

def GetModify(wnd)
	return wnd.SendMessage(EM_GETMODIFY)	
Changed=GetModify # cmifex2 alias

def Cut(wnd):
	wnd.SendMessage(WM_CUT)
def Copy(wnd):
	wnd.SendMessage(WM_COPY)
def Clear(wnd):
	wnd.SendMessage(WM_CLEAR)
def Past(wnd):
	wnd.SendMessage(WM_PASTE)
def Select(wnd,start,end):
	wnd.SendMessage(EM_SETSEL, start, end)
def Replace(wnd,str):
	print 'Replace not implemented',str
	#wnd.SendMessage(EM_REPLACESEL,0, str)
	
def AddString(wnd,str):
	print 'AddString not implemented',str
	#wnd.SendMessage(LB_ADDSTRING,0, str)
	#wnd.SendMessage(CB_ADDSTRING,0, str)
def DeleteString(wnd):
	wnd.SendMessage(LB_GETCURSEL)
	wnd.SendMessage(LB_DELETESTRING)
	#wnd.SendMessage(CB_GETCURSEL)
	#wnd.SendMessage(CB_DELETESTRING)
def DeleteToPos(wnd,ix):
	wnd.SendMessage(LB_DELETESTRING,ix)
	#wnd.SendMessage(CB_DELETESTRING,ix)
def ReplaceToPos(wnd,ix,str):
	print 'ReplaceToPos not implemented',ix,str
	#wnd.SendMessage(LB_DELETESTRING,ix)
	#wnd.SendMessage(LB_INSERTSTRING,ix,str)
	#wnd.SendMessage(CB_DELETESTRING,ix)
	#wnd.SendMessage(CB_INSERTSTRING,ix,str)
def InsertToPos(wnd,ix,str):
	print 'InsertToPos not implemented',ix,str
	#wnd.SendMessage(LB_INSERTSTRING,ix,str)
	#wnd.SendMessage(CB_INSERTSTRING,ix,str)
def Reset(wnd):
	wnd.SendMessage(LB_RESETCONTENT)
	#wnd.SendMessage(CB_RESETCONTENT)
	
def GetString(wnd):
	print 'GetString not implemented'
	#ix=wnd.SendMessage(LB_GETCURSEL)
	#return wnd.SendMessageReturnStr(LB_GETTEXT,ix)
	#ix=wnd.SendMessage(CB_GETCURSEL)
	#return wnd.SendMessageReturnStr(CB_GETLBTEXT,ix)

def GetPos(wnd):
	return wnd.SendMessage(LB_GETCURSEL)
def SetSelect(wnd,ix):
	wnd.SendMessage(LB_SETCURSEL,ix)

# TB not implemented here
# Menu operations not implemented here

def ResizeWindow(wnd,w,h):
	(flags,showCmd,ptMinPosition,ptMaxPosition,rcNormalPosition)=\
		=wnd.GetWindowPlacement()
	rcNormalPositionNew=(rcNormalPosition[0],rcNormalPosition[1],
		rcNormalPosition[2]-rcNormalPosition[0]+w,
		rcNormalPosition[3]-rcNormalPosition[1]+h)
	wnd.SetWindowPlacement((flags,showCmd,ptMinPosition,ptMaxPosition,rcNormalPositionNew))

