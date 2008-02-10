__version__ = "$Id$"

# @win32doc|_LinkView
# This module contains the ui implementation of the LinkView.
# It is implemented as a Form view with dialog bars.
# The MFC CFormView is essentially a view that contains controls.
# These controls are laid out based on a dialog-template resource
# similar to a dialog box.
# Objects of this class are exported to Python through the win32ui pyd
# as objects of type PyCFormView.
# The _LayoutView extends the PyCFormView and uses a PyCDialogBar
# .
# The _LayoutView is created using the resource dialog template with identifier IDD_LINKS.
# To edit this template, open it using the resource editor.
# Like all resources it can be found in cmif\win32\src\GRiNSRes\GRiNSRes.rc.
# The resource project is cmif\win32\src\GRiNSRes\GRiNSRes.dsp which creates
# the run time GRiNSRes.dll

import win32ui,win32con
Sdk=win32ui.GetWin32Sdk()
Afx=win32ui.GetAfx()
import win32mu

import grinsRC,win32menu
import components, win32dialog
import usercmd
import win32mu

from pywinlib.mfc import window,object,docview
import afxres,commctrl

# This indermediate class based on the framework FormView class implements the
# std interface required by the core system. It is used to implement the LinkView


class LinkPropDlg(win32dialog.ResDialog):
    def __init__(self,cbd,dir,dirsens,parent=None):
        win32dialog.ResDialog.__init__(self,grinsRC.IDD_LINK_PROPERTY,parent)

        d0=components.RadioButton(self,grinsRC.IDC_RADIO1)
        d1=components.RadioButton(self,grinsRC.IDC_RADIO2)
        d2=components.RadioButton(self,grinsRC.IDC_RADIO3)
        self._dir_buttons = (d0, d1, d2)

        self._cbd = cbd
        self._dir = dir
        self._dirsens = dirsens

    def OnInitDialog(self):
        self.attach_handles_to_subwindows()
        # set initial data to dialog
        # ...
        self.linkdirsetchoice(self._dir)
        for i in range(len(self._dirsens)):
            self._dir_buttons[i].enable(self._dirsens[i])
        return win32dialog.ResDialog.OnInitDialog(self)

    def show(self):
        self.DoModal()

    def linkdirsetchoice(self, dir):
        for i in range(3):
            self._dir_buttons[i].setcheck(i==dir)

    def linkdirgetchoice(self):
        for i in range(3):
            if self._dir_buttons[i].getcheck():
                return i
        raise 'No dir button set!'

    def OnOK(self):
        # 1. Tell upper layer to come and collect data
        self.callcallback('LinkDir')

        # 2. close dlg
        self._obj_.OnOK()

        # 3. Tell upper layers we've done so
        self.callcallback('OK')

    def OnCancel(self):
        self._obj_.OnCancel()
        self.callcallback('Cancel')

    def callcallback(self, which):
        func, arg = self._cbd[which]
        apply(func, arg)


# This class implements the LinkView required by the core system
class _LinkView(docview.FormView,components.ControlsDict):
    # Class constructor. Initializes base class and associates controls to ids
    def __init__(self,doc,bgcolor=None):
        docview.FormView.__init__(self,doc,grinsRC.IDD_LINKS)
        components.ControlsDict.__init__(self)
        self._close_cmd_list=[]

        self['LeftList']=components.ListBox(self,grinsRC.IDC_LIST1)
        self['RightList']=components.ListBox(self,grinsRC.IDC_LIST2)
        self['LinkList']=components.ListBox(self,grinsRC.IDC_LIST_LINKS)

        self['LeftPushFocus']=components.Button(self,grinsRC.IDC_PUSH_FOCUS1)
        self['RightPushFocus']=components.Button(self,grinsRC.IDC_PUSH_FOCUS2)

        self['LeftAnchorEd']=components.Button(self,grinsRC.IDC_ANCHOR_EDITOR1)
        self['RightAnchorEd']=components.Button(self,grinsRC.IDC_ANCHOR_EDITOR2)

        self['AddExternal']=components.Button(self,grinsRC.IDC_ADD_EXTERNAL)

        self['AddLink']=components.Button(self,grinsRC.IDC_ADD_LINK)
        self['EditLink']=components.Button(self,grinsRC.IDC_EDIT_LINK)
        self['DeleteLink']=components.Button(self,grinsRC.IDC_DELETE_LINK)

        self['LeftLabel']=components.Static(self,grinsRC.IDC_STATIC_LEFT)
        self['RightLabel']=components.Static(self,grinsRC.IDC_STATIC_RIGHT)

        self['LeftMenu']=components.Button(self,grinsRC.IDC_LEFT_MENU)
        self['RightMenu']=components.Button(self,grinsRC.IDC_RIGHT_MENU)

        # cash lists
        self._lists_ids=(self['LeftList']._id,self['RightList']._id,self['LinkList']._id)

    def isResizeable(self):
        return 0

    # Creates the actual OS window
    def createWindow(self,parent):
        self._parent=parent
        self.CreateWindow(parent)

    def EnableCmd(self,strcmd,f):
        p=self._parent
        if f:
            self[strcmd].enable(1)
            p.HookCommandUpdate(p.OnUpdateCmdEnable,self[strcmd]._id)
        else:
            p.HookCommandUpdate(p.OnUpdateCmdDissable,self[strcmd]._id)
            self[strcmd].enable(0)

    # Called after the OS window has been created to initialize the view
    def OnInitialUpdate(self):
        frame=self.GetParent()
        self._mdiframe=frame.GetMDIFrame()
        self.fittemplate()
        frame.RecalcLayout()

        for ck in self.keys():
            self[ck].attach_to_parent()
            self.HookMessage(self.onCmd,win32con.WM_COMMAND)
            self.EnableCmd(ck,0)

        self.EnableCmd('LeftMenu',1)
        self.EnableCmd('RightMenu',1)
        self.EnableCmd('LeftLabel',1)
        self.EnableCmd('RightLabel',1)

        self._iconplay = win32ui.GetApp().LoadIcon(grinsRC.IDI_PLAY)
        self['LeftMenu'].seticon(self._iconplay)
        self['RightMenu'].seticon(self._iconplay)

        # temp patch
        #closecmd=usercmd.CLOSE_WINDOW(callback = (self.close_window_callback,()))
        #self._close_cmd_list.append(closecmd)
        #self.onActivate(1)

        self['LeftList'].recalchorizontalextent()
        self['RightList'].recalchorizontalextent()

    # Called when the view is activated
    def activate(self):
        pass

    # Called when the view is deactivated
    def deactivate(self):
        pass

    # Called by the frame work before closing this View
    def OnClose(self):
# UNCOMMENT NEXT LINES WHEN LinkEdit class is fixed
# so that it works the same way as the other views
#               if self._closecmdid>0:
#                       self.GetParent().GetMDIFrame().PostMessage(win32con.WM_COMMAND, self._closecmdid)
#               else:
        self.call('close')
##         self.GetParent().DestroyWindow()

    # Returns true if the OS window exists
    def is_oswindow(self):
        return (hasattr(self,'GetSafeHwnd') and self.GetSafeHwnd())

    # Adjust dimensions to fit resource template
    def fittemplate(self):
        frame=self.GetParent()
        rc=win32mu.DlgTemplate(grinsRC.IDD_LINKS).getRect()
        if not rc: return
        from sysmetrics import cycaption,cyborder,cxborder,cxframe
        h=rc.height() + 2*cycaption+ 2*cyborder
        w=rc.width()+2*cxframe+2*cxborder+8
        flags=win32con.SWP_NOZORDER|win32con.SWP_NOACTIVATE|win32con.SWP_NOMOVE
        frame.SetWindowPos(0, (0,0,w,h),flags)

    # Internal function to implement a close window mechanism
    def close_window_callback(self):
        self._mdiframe.SendMessage(win32con.WM_COMMAND, usercmdui.usercmd2id(usercmd.LINKVIEW))

    # Helper function that given the string id of the control calls the callback
    def call(self,strcmd):
        if self._callbacks.has_key(strcmd):
            apply(apply,self._callbacks[strcmd])

    # Reponse to the WM_COMMAND message
    def onCmd(self,params):
        msg=win32mu.Win32Msg(params)
        id=msg.cmdid()
        nmsg=msg.getnmsg()
        if self._mcb.has_key(id):
            self.menu_callback(id,0)
            return
        for key in self.keys():
            if id==self[key]._id:
                if id in self._lists_ids:
                    if nmsg==win32con.LBN_SELCHANGE:self.call(key)
                else:
                    self.call(key)
                break
    # Response to the user selection to display a popup menu
    def on_menu(self,menu,str):
        lc,tc,rc,bc=self[str].getwindowrect()
        try:
            menu.TrackPopupMenu((rc,tc),
                    win32con.TPM_LEFTALIGN|win32con.TPM_LEFTBUTTON,self)
        except 'x':
            print 'TrackPopupMenu failed'

    # Callback for commands from the popup menu
    def menu_callback(self,id,code):
        if self._mcb.has_key(id):
            apply(apply,self._mcb[id])

    # Called directly from cmif-core to close window
    def close(self):
        # 1. clean self contends
        if self._leftmenu:self._leftmenu.DestroyMenu()
        if self._rightmenu:self._rightmenu.DestroyMenu()
        del self._leftmenu
        del self._rightmenu

        # 2. destroy OS window if it exists
        if hasattr(self,'_obj_') and self._obj_:
            self.GetParent().DestroyWindow()

    # Return 1 if self is an os window
    def is_showing(self):
        if not hasattr(self,'GetSafeHwnd'):
            return 0
        return self.GetSafeHwnd()

    # Called by the core system to show this view
    def show(self):
        if hasattr(self,'GetSafeHwnd'):
            if self.GetSafeHwnd():
                self.GetParent().ShowWindow(win32con.SW_SHOW)
                self.GetParent().GetMDIFrame().MDIActivate(self.GetParent())

    # Called by the core system to hide this view
    def hide(self):
        self.close()


    #########################################
    # The actual initialization from the core system
    def do_init(self, title, menu1, cbarg1, menu2, cbarg2, adornments):
        self._title=title

        # hard res-coded values
        # ignore dirstr <- -> <->

        # menu callbacks dict
        self._mcb={}
        self._mid=grinsRC._APS_NEXT_RESOURCE_VALUE

        self._leftmenu=self.create_menu(menu1)
        self._left_data = cbarg1

        self._rightmenu=self.create_menu(menu2)
        self._right_data = cbarg2

        self._callbacks=adornments['callbacks']

        # add callbacks for show menu buttons
        self._callbacks['LeftMenu']=(self.on_menu,(self._leftmenu,'LeftMenu'))
        self._callbacks['RightMenu']=(self.on_menu,(self._rightmenu,'RightMenu'))

    # create a menu from a list of pairs (str,callback)
    def create_menu(self,mcl):
        from flags import FLAG_ALL
        list=[]
        for item in mcl:
            list.append((FLAG_ALL,0,item[0],None,self._mid))
            self._mcb[self._mid]=item[1]
            self._mid=self._mid+1
        menu=win32menu.Menu('popup')
        menu.create_from_menu_spec_list(list)
        return menu

    # Interface to the left list and associated buttons.
    def lefthide(self):
        # Hide the left list with associated buttons.
        self.EnableCmd('LeftList',0)
        self.EnableCmd('LeftPushFocus',0)
        self.EnableCmd('LeftAnchorEd',0)

    def leftshow(self):
        # Show the left list with associated buttons.
        self.EnableCmd('LeftList',1)

    def leftsetlabel(self, label):
        # Set the label for the left list.

        # Arguments (no defaults):
        # label -- string -- the label to be displayed
        self['LeftLabel'].settext(label)

    def leftdellistitems(self, poslist):
        # Delete items from left list.

        # Arguments (no defaults):
        # poslist -- list of integers -- the indices of the
        #       items to be deleted
        poslist = poslist[:]
        poslist.sort()
        poslist.reverse()
        l=self['LeftList']
        for pos in poslist:
            l.deletestring(pos)
        self['LeftList'].recalchorizontalextent()

    def leftdelalllistitems(self):
        # Delete all items from the left list.
        self['LeftList'].resetcontent()
        self['LeftList'].recalchorizontalextent()

    def leftaddlistitems(self, items, pos):
        # Add items to the left list.

        # Arguments (no defaults):
        # items -- list of strings -- the items to be added
        # pos -- integer -- the index of the item before which
        #       the items are to be added (-1: add at end)
        self['LeftList'].addlistitems(items, pos)
        self['LeftList'].recalchorizontalextent()

    def leftreplacelistitem(self, pos, newitem):
        # Replace an item in the left list.

        # Arguments (no defaults):
        # pos -- the index of the item to be replaced
        # newitem -- string -- the new item
        self['LeftList'].replace(pos, newitem)
        self['LeftList'].recalchorizontalextent()

    def leftselectitem(self, pos):
        # Select an item in the left list.

        # Arguments (no defaults):
        # pos -- integer -- the index of the item to be selected
        self['LeftList'].setcursel(pos)

    def leftgetselected(self):
        # Return the index of the currently selected item or None.
        return self['LeftList'].getcursel()

    def leftgetlist(self):
        # Return the left list as a list of strings.
        return self['LeftList'].getlist()

    def leftmakevisible(self, pos):
        # Maybe scroll list to make an item visible.

        # Arguments (no defaults):
        # pos -- index of item to be made visible.
        pass

    def leftbuttonssetsensitive(self, sensitive):
        # Make the left buttons (in)sensitive.

        # Arguments (no defaults):
        # sensitive -- boolean indicating whether to make
        #       sensitive or insensitive
        self.EnableCmd('LeftPushFocus',sensitive)
        self.EnableCmd('LeftAnchorEd',sensitive)

    # Interface to the right list and associated buttons.
    def righthide(self):
        # Hide the right list with associated buttons.
        self.EnableCmd('RightList',0)
        self.EnableCmd('RightPushFocus',0)
        self.EnableCmd('RightAnchorEd',0)
        self.EnableCmd('AddExternal',0)

    def rightshow(self):
        # Show the right list with associated buttons.
        self['RightList'].enable(1);self.EnableCmd('RightList',1)

    def rightsetlabel(self, label):
        # Set the label for the right list.

        # Arguments (no defaults):
        # label -- string -- the label to be displayed
        self['RightLabel'].settext(label)

    def rightdellistitems(self, poslist):
        # Delete items from right list.

        # Arguments (no defaults):
        # poslist -- list of integers -- the indices of the
        #       items to be deleted
        poslist = poslist[:]
        poslist.sort()
        poslist.reverse()
        for pos in poslist:
            self['RightList'].deletestring(pos)
        self['RightList'].recalchorizontalextent()

    def rightdelalllistitems(self):
        # Delete all items from the right list.
        self['RightList'].resetcontent()
        self['RightList'].recalchorizontalextent()

    def rightaddlistitems(self, items, pos):
        # Add items to the right list.

        # Arguments (no defaults):
        # items -- list of strings -- the items to be added
        # pos -- integer -- the index of the item before which
        #       the items are to be added (-1: add at end)
        self['RightList'].addlistitems(items,pos)
        self['RightList'].recalchorizontalextent()

    def rightreplacelistitem(self, pos, newitem):
        # Replace an item in the right list.

        # Arguments (no defaults):
        # pos -- the index of the item to be replaced
        # newitem -- string -- the new item
        self['RightList'].replace(pos, newitem)
        self['RightList'].recalchorizontalextent()

    def rightselectitem(self, pos):
        # Select an item in the right list.

        # Arguments (no defaults):
        # pos -- integer -- the index of the item to be selected
        self['RightList'].setcursel(pos)

    def rightgetselected(self):
        # Return the index of the currently selected item or None.
        return self['RightList'].getcursel()

    def rightgetlist(self):
        # Return the right list as a list of strings.
        return self['RightList'].getlist()

    def rightmakevisible(self, pos):
        # Maybe scroll list to make an item visible.

        # Arguments (no defaults):
        # pos -- index of item to be made visible.
        pass

    def rightbuttonssetsensitive(self, sensitive):
        # Make the right buttons (in)sensitive.

        # Arguments (no defaults):
        # sensitive -- boolean indicating whether to make
        #       sensitive or insensitive
        self.EnableCmd('RightPushFocus',sensitive)
        self.EnableCmd('RightAnchorEd',sensitive)

    def addexternalsetsensitive(self, sensitive):
        self.EnableCmd('AddExternal', sensitive)

    # Interface to the middle list and associated buttons.
    def middlehide(self):
        # Hide the middle list with associated buttons.
        self.EnableCmd('LinkList',0)
        self.EnableCmd('AddLink',0)
        self.EnableCmd('EditLink',0)
        self.EnableCmd('DeleteLink',0)
        return

        self['LinkList'].hide()
        self['AddLink'].hide()
        self['EditLink'].hide()
        self['DeleteLink'].hide()


    def middleshow(self):
        # Show the middle list with associated buttons.
        self.EnableCmd('LinkList',1)
        return

        self['AddLink'].show() ;self.EnableCmd('AddLink',0)
        self['EditLink'].show()  ;self.EnableCmd('EditLink',0)
        self['DeleteLink'].show() ;self.EnableCmd('DeleteLink',0)

    def middledelalllistitems(self):
        # Delete all items from the middle list.
        self['LinkList'].resetcontent()

    def middleaddlistitems(self, items, pos):
        # Add items to the middle list.

        # Arguments (no defaults):
        # items -- list of strings -- the items to be added
        # pos -- integer -- the index of the item before which
        #       the items are to be added (-1: add at end)
        self['LinkList'].addlistitems(items,pos)

    def middleselectitem(self, pos):
        # Select an item in the middle list.

        # Arguments (no defaults):
        # pos -- integer -- the index of the item to be selected
        self['LinkList'].setcursel(pos)

    def middlegetselected(self):
        # Return the index of the currently selected item or None.
        return self['LinkList'].getcursel()

    def middlemakevisible(self, pos):
        # Maybe scroll list to make an item visible.

        # Arguments (no defaults):
        # pos -- index of item to be made visible.
        pass

    def addsetsensitive(self, sensitive):
        # Make the Add button (in)sensitive.

        # Arguments (no defaults):
        # sensitive -- boolean indicating whether to make
        #       sensitive or insensitive
        self.EnableCmd('AddLink',sensitive)


    def editsetsensitive(self, sensitive):
        # Make the Edit button (in)sensitive.

        # Arguments (no defaults):
        # sensitive -- boolean indicating whether to make
        #       sensitive or insensitive
        self.EnableCmd('EditLink',sensitive)

    def deletesetsensitive(self, sensitive):
        # Make the Delete button (in)sensitive.

        # Arguments (no defaults):
        # sensitive -- boolean indicating whether to make
        #       sensitive or insensitive
        self.EnableCmd('DeleteLink',sensitive)


    def getgeometry(self, units = None):
        # Ignore units.
        placement = self.GetParent().GetWindowPlacement()
        outerrect = placement[4]
        out_l, out_t, out_r, out_b = outerrect
        out_w = out_r - out_l
        out_h = out_b - out_t
        in_w = out_w - 16
        in_h = out_h - 35
        return (out_l, out_t, in_w, in_h)
