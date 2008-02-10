__version__ = "$Id$"

# @win32doc|components
# The components defined in this module are a sufficient
# family of light-weight controls (Button,Edit,etc)
# The controls are not based on MFC but on win32 Sdk.
# They are at the same level as MFC is to the Sdk
# (a fact that justifies the name light weight)
# This is in contrast to all the objects exported by the
# win32ui pyd which exports inherited objects from MFC objects

import win32ui, win32con, win32api
import commctrl
import afxres
Sdk=win32ui.GetWin32Sdk()
import grinsRC
import win32mu
import string
import math

[FALSE, TRUE] = range(2)
from appcon import error

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
    def getId(self):
        return self._id
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
        # called when os wnd exists
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
    def gettextlength(self):
        return self.sendmessage(win32con.WM_GETTEXTLENGTH)
    def gettext(self):
        n=self.gettextlength()+1
        return self.sendmessage_rs(win32con.WM_GETTEXT,n,n)
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

# RadioButtons aren't very useful on their own..
# This makes them look like a ComboBox, except this looks like a dictionary.
# Hmm.. this could take some time to write and get working. I'll just do a quick
# hack for the meanwhile -mjvdg.
## class RadioButtonGroup:
##     def __init__(self, buttons = None):
##         self.set(buttons)
##     def setcursel(self, key):    # sets the current selection
##         print "TODO: RadioButtonGroup.setcursel"
##     def getcursel(self, key):    # returns the currently selected key

##     def resetcontent(self):        # sets the first radio button
##         return
##     def set(self, buttons):        # sets the buttons in this control (hard-wired)
##         # Buttons is a dicitonary of {grinsRC.xx : 'Name'}
##         self.buttons = buttons
##         self.selected = None
##         for k, v in buttons.items():
##             if not self.selected:
##                 self.selected = k
##             working here.
##     def getselected(self):        # returns the selected key
##         return self.getcursel()

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
    def getselitems(self, itemCount=None):
        if itemCount == None:
            itemCount = self.getselcount()
        return self.sendmessage_gt(win32con.LB_GETSELITEMS, itemCount)
    def multiselect(self, item, onoff):
        return self.sendmessage(win32con.LB_SETSEL, onoff, item)
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
    # XXXX Should this use DropTarget.EncodeDragData??

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
        self.__cancelindex = None
        Control.__init__(self,owner,id)
        self.__icmif()

    def setcursel(self,index):
        if index is None:
            index = -1
        if self.__cancelindex is not None:
            if index == self.__cancelindex:
                index = 0
            elif index > self.__cancelindex:
                index = index - 1
        self.sendmessage(win32con.CB_SETCURSEL,index)

    def getcursel(self):
        index = self.sendmessage(win32con.CB_GETCURSEL)
        if self.__cancelindex is not None and index >= self.__cancelindex:
            index = index + 1
        return index

    def getcount(self):
        return self.sendmessage(win32con.CB_GETCOUNT) + (self.__cancelindex is not None)

    def insertstring(self,index,str):
        if not str: str='---'
        if self.__cancelindex is not None and index > self.__cancelindex:
            index = index - 1
        self.sendmessage_ls(win32con.CB_INSERTSTRING,index,str)

    def addstring(self,str):
        if not str: str='---'
        return self.sendmessage_ls(win32con.CB_ADDSTRING,0,str)

    def gettextlen(self,index):
        if self.__cancelindex is not None and index > self.__cancelindex:
            index = index - 1
        return self.sendmessage(win32con.CB_GETLBTEXTLEN,index)

    def gettext(self,index):
        if self.__cancelindex is not None and index > self.__cancelindex:
            index = index - 1
        n = self.gettextlen(index) + 1
        return self.sendmessage_rs(win32con.CB_GETLBTEXT,index,n)

    def resetcontent(self):
        self.sendmessage(win32con.CB_RESETCONTENT)

    def deletestring(self,index):
        if self.__cancelindex is not None and index > self.__cancelindex:
            index = index - 1
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
        for i in range(len(optionlist)):
            item = optionlist[i]
            if type(item)==type(()):
                if item[0]=='Cancel' and self.__cancelindex is None:
                    self.__cancelindex = i
                    continue
                self.addstring(item[0])
                self._optionlist.append(item[0])
        self.setcursel(0)

    def setsensitive(self,pos,f):
        seloption=self.getcursel()
        opos = pos
        if self.__cancelindex is not None and pos > self.__cancelindex:
            pos = pos - 1
        str=self._optionlist[pos]
        if f:
            self.deletestring(opos)
            self.insertstring(opos,str) # add it
        else:
            self.deletestring(opos) # remove it
            str='['+str+']'
            self.insertstring(opos,str)
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

##############################
class KeyTimesSlider(window.Wnd):
    # how near key times can be
    # XXX we should use the same variable as the variable defined from LayoutView2
    DELTA = 0.01

    # depends on resource template slider
    TICKS_OFFSET = 12

    # marker triangle
    MARKER_WIDTH = 8
    MARKER_HEIGHT = 10

    def __init__(self, dlg, id):
        self._parent = dlg
        hwnd = Sdk.GetDlgItem(dlg.GetSafeHwnd(),id)
        window.Wnd.__init__(self, win32ui.CreateWindowFromHandle(hwnd))

        self._enabled = 0
        if not self._enabled:
            self.EnableWindow(0)

        self.SetTicFreq(5)
        self.SetLineSize(5)
        self.SetPageSize(20)
        self.SetRange(0, 100)

        self._keyTimes = [0.0, 1.0]
        self._copyKeyTime = None
        self._copyIndex = None

        self._markerColor = 0, 0, 0
        self._selectedMarkerColor = 255, 0, 0
        self._copingMarkerColor = 255, 150, 150

        dlg.HookMessage(self.OnHScroll, win32con.WM_HSCROLL)

        self._selected = -1
        self._dragging = None

        self._listener = None

        # preview support
        self.fiber = None
        self.previewdur = 5.0

    def setListener(self, listener):
        self._listener = listener

    def removeListener(self):
        self._listener = None

    def insertKeyTime(self, tp):
        index = 0
        for p in self._keyTimes:
            if tp<p: break
            index = index + 1

        self._keyTimes.insert(index, tp)
        self._selected = -1
        self.updateKeyTimes()
        return index

    def insertKeyTimeFromPoint(self, index, prop):
        tp = self._keyTimes[index-1] + prop*(self._keyTimes[index]-self._keyTimes[index-1])
        self._keyTimes.insert(index, tp)
        self._selected = -1
        self.updateKeyTimes()

    def pointToTime(self, point):
        l, t, r, b = self.GetWindowRect()
        l, t, r, b = self._parent.ScreenToClient( (l, t, r, b) )
        x0 = l + self.TICKS_OFFSET
        x, y = point
        range = float(self.getDeviceRange())
        tp = (x-x0)/range
        return tp

    def insertKeyTimeAtDevicePoint(self, point):
        tp = self.pointToTime(point)
        self.insertKeyTime(tp)

    def removeKeyTimeAtIndex(self, index):
        del self._keyTimes[index]
        if index == self._selected:
            self._selected = -1
        self.updateKeyTimes()

    def removeSelectedKeyTime(self, index):
        if self._selected>=0:
            self.removeKeyTimeAtIndex(self._selected)

    def updateKeyTimes(self):
        l, t, r, b = self.GetWindowRect()
        l, t, r, b = self._parent.ScreenToClient( (l, t, r, b) )
        rc = l, b, r, b+self.MARKER_HEIGHT
        self._parent.InvalidateRect(rc)

    def insideKeyTimes(self, point):
        l, t, r, b = self.GetWindowRect()
        l, t, r, b = self._parent.ScreenToClient( (l, t, r, b) )
        rc = l+self.TICKS_OFFSET+self.DELTA, b, r-self.TICKS_OFFSET-self.DELTA, b+self.MARKER_HEIGHT
        rect = win32mu.Rect(rc)
        return rect.isPtInRect(win32mu.Point(point))

    def getDeviceRange(self):
        l, t, r, b = self.GetWindowRect()
        return r-l-2*self.TICKS_OFFSET-2

    def drawOn(self, dc):
        if not self._enabled: return
        l, t, r, b = self.GetWindowRect()
        l, t, r, b = self._parent.ScreenToClient( (l, t, r, b) )
        x0 = l + self.TICKS_OFFSET # first tick in pixels or pos zero
        w = r-l-2*self.TICKS_OFFSET-2 # pixels range
        dw = self.MARKER_WIDTH/2
        index = 0
        if self._copyKeyTime is not None:
            keyTimesToDraw = self._keyTimes+[self._copyKeyTime]
        else:
            keyTimesToDraw = self._keyTimes
        for p in keyTimesToDraw:
            x = int(p*w + 0.5)
            pts = [(x0+x-dw, b+self.MARKER_HEIGHT), (x0+x, b), (x0+x+dw, b+self.MARKER_HEIGHT)]
            if self._copyKeyTime is not None and self._copyKeyTime == p:
                color = self._copingMarkerColor
            elif index == self._selected: color = self._selectedMarkerColor
            else: color = self._markerColor
            win32mu.FillPolygon(dc, pts, color)
            index = index + 1

    def OnHScroll(self, msg):
        self._parent.stop()

        pos = self.GetPos()
        if self._listener:
            self._listener.onCursorPosChanged(0.01*pos)

    def setCursorPos(self, t):
        self.SetPos(int(t*100+0.5))

    def setKeyTimes(self, keyTimes):
        self._keyTimes = keyTimes
        l, t, r, b = self.GetWindowRect()
        l, t, r, b = self._parent.ScreenToClient( (l, t, r, b) )
        self._parent.InvalidateRect( (l, b, r, b+8) )

    def getKeyTime(self, point):
        l, t, r, b = self.GetWindowRect()
        l, t, r, b = self._parent.ScreenToClient( (l, t, r, b) )
        x0 = l + self.TICKS_OFFSET # first tick in pixels or pos zero
        w = r-l-2*self.TICKS_OFFSET-2 # last tick in pixels or pos 100
        dw = self.MARKER_WIDTH/2
        index = 0
        point = win32mu.Point(point)
        for p in self._keyTimes:
            x = int(p*w + 0.5)
            rect = win32mu.Rect((x0+x-dw, b, x0+x+dw, b+self.MARKER_HEIGHT))
            if rect.isPtInRect(point):
                return index, rect.ltrb_tuple()
            index = index + 1
        return -1, None

    def getSelectedKeyTimeIndex(self):
        return self._selected

    def isDraggable(self):
        if self._shiftPressed:
            return 1
        return self._selected>0 and self._selected<len(self._keyTimes)-1

    def isRemovable(self, index):
        return index>0 and index<len(self._keyTimes)-1

    def onSelect(self, point, flags):
        self._parent.stop()

        # XXX update the shift pressed status
        self._shiftPressed = flags & win32con.MK_SHIFT

        # test hit on a key time
        index, rect = self.getKeyTime(point)
        if index >= 0:
            self._selected = index
            self._startDragging = 1
            if self.isDraggable():
                self._dragging = point
                self._dragfrom = self._keyTimes[index]
                self._parent.SetCapture()

            # move the current selection
            self.updateKeyTimes()
            if not self._shiftPressed:
                if self._listener:
                    self._listener.onSelected(index)

    def onDeselect(self, point, flags):
        if self._dragging:
            self._dragging = None
            self._parent.ReleaseCapture()
            if self._listener and not self._startDragging:
                if self._shiftPressed:
                    self._listener.onInsertKey(self._copyKeyTime, self._copyIndex)
                else:
                    self._listener.onKeyTimeChanged(self._selected, self._keyTimes[self._selected])
            self._copyKeyTime = None
            self.updateKeyTimes()
        self._startDragging = 0

    def selectKeyTime(self, index):
        self._selected = index
        self.updateKeyTimes()

    def __isValidDrag(self, draggedTime, draggedKey):
        if draggedTime <= 0 or draggedTime >= 1:
            return
        for keyTime in self._keyTimes:
            if not self._shiftPressed and keyTime == draggedKey:
                continue
            if draggedTime < (keyTime + self.DELTA) and \
                    draggedTime > (keyTime - self.DELTA):
                return 0
        return 1

    def onDrag(self, point, flags):
        if self._dragging:
            x1, y1 = self._dragging
            x2, y2 = point
            range = float(self.getDeviceRange())
            v = self._dragfrom + (x2-x1)/range
            # exclude all invalid positions
            if not self.__isValidDrag(v, self._selected):
                return

            if not self._startDragging:
                if not self._startDragging:
                    if self._shiftPressed:
                        self._copyKeyTime = v
                        self._listener.onKeyTimeChanging(v)
                        self.updateKeyTimes()
                    else:
                        n = self._selected
                        # for now don't allow to jump on another one key
                        if n > 0 and v > self._keyTimes[n-1] and \
                                ((n == len(self._keyTimes)-1) or v < self._keyTimes[n+1]):
                            self._keyTimes[n] = v
                            self._listener.onKeyTimeChanging(v)
                            self.updateKeyTimes()
            else:
                if self._shiftPressed:
                    self._copyIndex = self._selected
                    self._copyKeyTime = v
                else:
                    if self.__isValidDrag(v, self._selected):
                        self._keyTimes[self._selected] = v
                self.updateKeyTimes()
                self._startDragging = 0

    def onActivate(self, point, flags):
        if not self.insideKeyTimes(point):
            return
        # test hit on a key time
        index, rect = self.getKeyTime(point)
        if index >= 0:
            if self._listener:
                self._listener.onRemoveKey(index)
        else:
            if self._listener:
                tp = self.pointToTime(point)
                # insert only if the new key is far enough from any other keys
                for keyTime in self._keyTimes:
                    if tp < (keyTime + self.DELTA) and \
                            tp > (keyTime - self.DELTA):
                        return
                self._listener.onInsertKey(tp)

    def getKeyTimes(self):
        return self._keyTimes

    def enable(self, flag):
        if self._enabled == flag:
            return
        self._enabled = flag
        if not flag:
            self.EnableWindow(0)
            self.stop()
            self._parent.EnablePreview(0)
        else:
            self.EnableWindow(1)
            self._parent.EnablePreview(1)
        self.updateKeyTimes()

    def isEnabled(self):
        return self._enabled

    #
    #       preview support
    #
    def play(self, dur=5.0):
        if not self._enabled:
            self._parent.EnablePreview(0)
            return
        self.previewdur = dur
        currentpos = 0.01*self.GetPos()*self.previewdur
        import windowinterface, time
        if self.fiber is None:
            self.start = time.time() - currentpos
            self.fiber = windowinterface.setidleproc(self.onIdle)

    def stop(self):
        import windowinterface
        if self.fiber is not None:
            windowinterface.cancelidleproc(self.fiber)
            self.fiber = None
        if not self._enabled:
            self._parent.EnablePreview(0)
            return

    def onIdle(self):
        import time
        t_sec = time.time() - self.start
        if t_sec >= self.previewdur:
            self.start = time.time()
            t_sec = 0
        pos = t_sec/float(self.previewdur)
        self.setCursorPos(pos)
        if self._listener:
            self._listener.onCursorPosChanged(pos)

    def OnDestroy(self, msg):
        if self.fiber is not None:
            self.stop()
