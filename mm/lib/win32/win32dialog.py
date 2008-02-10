__version__ = "$Id$"


# @win32doc|win32dialog

import win32api, win32ui, win32con
import commctrl
import afxres
Sdk=win32ui.GetWin32Sdk()
import grinsRC
import win32mu
import string
import math
import compatibility

from pywinlib.mfc import window
from components import *

##############################
def dllFromDll(dllid):
    # given a 'dll' (maybe a dll, filename, etc), return a DLL object
    if dllid==None:
        return None
    elif type('')==type(dllid):
        return win32ui.LoadLibrary(dllid)
    else:
        try:
            dllid.GetFileName()
        except AttributeError:
            raise TypeError, "DLL parameter must be None, a filename or a dll object"
        return dllid

def loadBitmapFromResId(resid):
    import __main__, win32ui
    resdll=__main__.resdll
    bmp=win32ui.CreateBitmap()
    bmp.LoadBitmap(resid,resdll)
    return bmp

class DialogBase(window.Wnd):
    # Base class for a dialog
    def __init__( self, id, parent=None, dllid=None ):
        # id is the resource ID, or a template
        # dllid may be None, a dll object, or a string with a dll name
        # must take a reference to the DLL until InitDialog.
        self.dll=dllFromDll(dllid)
        if type(id)==type([]):  # a template
            dlg=win32ui.CreateDialogIndirect(id)
        else:
            dlg=win32ui.CreateDialog(id, self.dll,parent)
        window.Wnd.__init__(self, dlg)
        self.HookCommands()
        self.bHaveInit = None

    def HookCommands(self):
        pass

    def OnAttachedObjectDeath(self):
        self.data = self._obj_.data
        window.Wnd.OnAttachedObjectDeath(self)

    # provide virtuals.
    def OnOK(self):
        self._obj_.OnOK()
    def OnCancel(self):
        self._obj_.OnCancel()
    def OnInitDialog(self):
        self.bHaveInit = 1
        if self._obj_.data:
            self._obj_.UpdateData(0)
        return 1                # I did NOT set focus to a child window.
    def OnDestroy(self,msg):
        self.dll = None         # theoretically not needed if object destructs normally.
    # DDX support
    def AddDDX( self, *args ):
        self._obj_.datalist.append(args)
    # Make a dialog object look like a dictionary for the DDX support
    def __nonzero__(self):
        return 1
    def __len__(self): return len(self.data)
    def __getitem__(self, key): return self.data[key]
    def __setitem__(self, key, item): self._obj_.data[key] = item# self.UpdateData(0)
    def keys(self): return self.data.keys()
    def items(self): return self.data.items()
    def values(self): return self.data.values()
    def has_key(self, key): return self.data.has_key(key)
    def get(self, key, default): return self.data.get(key, default)

# Base class for dialogs created using a resource template
class ResDialog(DialogBase):
    def __init__(self,id,parent=None,resdll=None):
        if not resdll:
            import __main__
            resdll=__main__.resdll
        DialogBase.__init__(self,id,parent,resdll)
        self._subwndlist = [] # controls add thrmselves to this list

    # Get from the OS and set the window handles to the controls
    def attach_handles_to_subwindows(self):
        #if self._parent:self.SetParent(self._parent)
        hdlg = self.GetSafeHwnd()
        for ctrl in self._subwndlist:
            ctrl.attach(Sdk.GetDlgItem(hdlg,ctrl._id))
    # Call init method for each window
    def init_subwindows(self):
        for w in self._subwndlist:
            w.init()

    # Helper method that calls the callback given the event
    def onevent(self,event):
        try:
            func, arg = self._callbacks[event]
        except KeyError:
            pass
        else:
            apply(func,arg)

# A special class that it is both an MFC window and A LightWeightControl
class WndCtrl(LightWeightControl,window.Wnd):
    def create_wnd_from_handle(self):
        window.Wnd.__init__(self,win32ui.CreateWindowFromHandle(self._hwnd))

# Implementation of the splash screen
class SplashDlg(ResDialog):
    def __init__(self,arg,version):
        ResDialog.__init__(self,grinsRC.IDD_SPLASH)
        self._splash = WndCtrl(self,grinsRC.IDC_SPLASH)
        self._versionc = Static(self,grinsRC.IDC_VERSION_MSG)
        self._msgc = Static(self,grinsRC.IDC_MESSAGE)
        self._version=version
        self.loadbmp()
        self.CreateWindow()
        self.CenterWindow()
        self.ShowWindow(win32con.SW_SHOW)
        self.UpdateWindow()

    def OnInitDialog(self):
        self.attach_handles_to_subwindows()
        self._versionc.settext(self._version)
        self._splash.create_wnd_from_handle()
        self.HookMessage(self.OnDrawItem, win32con.WM_DRAWITEM)
        return ResDialog.OnInitDialog(self)

    def close(self):
        if self._bmp:
            self._bmp.DeleteObject()
            del self._bmp
        if hasattr(self,'DestroyWindow'):
            self.DestroyWindow()

    # draw splash
    def OnDrawItem(self,params):
        lParam=params[3]
        hdc=Sdk.ParseDrawItemStruct(lParam)
        dc=win32ui.CreateDCFromHandle(hdc)
        if self._bmp:
            w, h = self._bmp.GetSize()
            rct = 0, 0, w, h
            dcmem = dc.CreateCompatibleDC()
            old = dcmem.SelectObject(self._bmp)
            dc.BitBlt((0,0),(w,h),dcmem,(0,0),win32con.SRCCOPY)
            dcmem.SelectObject(old)
            dcmem.DeleteDC()
            br=Sdk.CreateBrush(win32con.BS_SOLID,0,0)
            dc.FrameRectFromHandle(rct,br)
            Sdk.DeleteObject(br)
        dc.Detach()

    # load splash
    def loadbmp(self):
        import splashbmp
        self._bmp = loadBitmapFromResId(splashbmp.getResId())

# Implementation of the about dialog
class AboutDlg(ResDialog):
    def __init__(self,arg,version,parent=None):
        ResDialog.__init__(self,grinsRC.IDD_ABOUT,parent)
        self._splash = WndCtrl(self,grinsRC.IDC_SPLASH)
        self._versionc = Static(self,grinsRC.IDC_VERSION_MSG)
        self._version=version

    def OnInitDialog(self):
        self.attach_handles_to_subwindows()
        self._splash.create_wnd_from_handle()
        self.SetWindowText("About Ambulant_G")
        self._versionc.settext(self._version)
        self.HookMessage(self.OnDrawItem,win32con.WM_DRAWITEM)
        self.loadbmp()
        return ResDialog.OnInitDialog(self)

    def OnOK(self):
        if self._bmp:
            self._bmp.DeleteObject()
            del self._bmp
        self._obj_.OnOK()

    # Response to the WM_DRAWITEM
    # draw splash
    def OnDrawItem(self,params):
        lParam=params[3]
        hdc=Sdk.ParseDrawItemStruct(lParam)
        dc=win32ui.CreateDCFromHandle(hdc)
        if self._bmp:
            w, h = self._bmp.GetSize()
            rct = 0, 0, w, h
            dcmem = dc.CreateCompatibleDC()
            old = dcmem.SelectObject(self._bmp)
            dc.BitBlt((0,0),(w,h),dcmem,(0,0),win32con.SRCCOPY)
            dcmem.SelectObject(old)
            dcmem.DeleteDC()
            br=Sdk.CreateBrush(win32con.BS_SOLID,0,0)
            dc.FrameRectFromHandle(rct,br)
            Sdk.DeleteObject(br)
        dc.Detach()

    # load splash bmp
    def loadbmp(self):
        import splashbmp
        self._bmp = loadBitmapFromResId(splashbmp.getResId())

# Implementation of a dialog with buttons dialog.
# To create dialogs that are similar to the YesNoCancel
# variety but more interesting:
# 1. Create the dialog resource
# 2. Add a subclass of _ModalButtonDlg
# 3. Add the _DIALOGID, _BUTTONLIST and _CANCEL
# 4. Add a boilerplate function calling show() and
#    returning the index of the button in _BUTTONLIST.
#
class _ButtonDlg(ResDialog):
    #_DIALOGID provided by subclass
    #_BUTTONLIST provided by subclass
    #_CANCEL provided by subclass
    def __init__(self,parent=None):
        ResDialog.__init__(self,self._DIALOGID,parent)
        self._buttons = []
        for b_id in self._BUTTONLIST:
            self._buttons.append(Button(self, b_id))
##         self._versionc = Static(self,grinsRC.IDC_VERSION_MSG)

    def OnInitDialog(self):
        self.attach_handles_to_subwindows()
        for b in self._buttons:
            b.hookcommand(self, self.OnButtonPressed)
        return ResDialog.OnInitDialog(self)

    # def OnButtonPressed provided by subclass

class _ModalButtonDlg(_ButtonDlg):
    def show(self):
        b_id = self.DoModal()
        if b_id == win32con.IDCANCEL:
            b_id = self._CANCEL
        return self._BUTTONLIST.index(b_id)

    def OnButtonPressed(self, id, code):
        self.EndDialog(id)

# class ModelessButtonDialog not implemented/needed yet

class _RegisterDialog(_ModalButtonDlg):
    _DIALOGID = grinsRC.IDD_REGISTER
    _BUTTONLIST = [
            grinsRC.IDC_REGISTER,
            grinsRC.IDC_DONTREGISTER,
            grinsRC.IDC_LATER,
            ]
    _CANCEL = grinsRC.IDC_LATER

def RegisterDialog():
    d = _RegisterDialog()
    return d.show()

# Implementation of the open loaction dialog
class OpenLocationDlg(ResDialog):
    def __init__(self,callbacks=None,parent=None, default='', recent_files = []):
        ResDialog.__init__(self,grinsRC.IDD_DIALOG_OPENLOCATION,parent)
        self._callbacks=callbacks
        self._default = default
        self._recent_files = recent_files

        self._text= ComboBox(self,grinsRC.IDC_EDIT_LOCATION)
        self._bcancel = Button(self,win32con.IDCANCEL)
        self._bopen = Button(self,win32con.IDOK)
        self._bbrowse= Button(self,grinsRC.IDC_BUTTON_BROWSE)

    def OnInitDialog(self):
        self.attach_handles_to_subwindows()
        #self._bopen.enable(0)
        #self._text.hookcommand(self,self.OnEditChange)
        self._bbrowse.hookcommand(self,self.OnBrowse)
        self.set_recentfiles()
        return ResDialog.OnInitDialog(self)

    def set_recentfiles(self):
        self._text.resetcontent()
        self._text.settext(self._default)
        for i in self._recent_files:
            shortname, more = i
            longname = more[0]
            self._text.addstring(longname)
        if self._default and len(self._default) > 0:
            self._text.setedittext(self._default)
        else:
            self._text.setcursel(0)

    def OnOK(self):
        self.onevent('Open')

    def OnCancel(self):
        self.onevent('Cancel')

    def close(self):
        self.EndDialog(win32con.IDOK)
    def show(self):
        self.DoModal()

    def OnBrowse(self,id,code):
        self.onevent('Browse')

##     def OnEditChange(self,id,code):
##         if self._text.hasid(id):
##             if code == win32con.CBN_EDITCHANGE:
##                 l=self._text.getedittextlength()
##                 self._bopen.enable(l)
##             elif code == win32con.CBN_SELCHANGE:
##                 self._bopen.enable(1)

    def gettext(self):
        # Returns whatever is in the combo box.
        return self._text.getedittext()

    def settext(self, text):
        self._text.settext(text)

##############################

class SelectElementDlg(ResDialog):
    tag2imgid = {'layout': grinsRC.IDI_PROPERTIES,
            'topLayout': grinsRC.IDI_VIEWPORT,
            'region': grinsRC.IDI_REGION,

            'body':  grinsRC.IDI_ICON_SEQOPEN,
            'par': grinsRC.IDI_ICON_PAROPEN,
            'seq': grinsRC.IDI_ICON_SEQOPEN,
            'excl': grinsRC.IDI_ICON_EXCLOPEN,
            'switch': grinsRC.IDI_ICON_SWITCHOPEN,
            'priority': grinsRC.IDI_ICON_PRIOOPEN,

            'img': grinsRC.IDI_ICON_ASSET_IMAGE,
            'text': grinsRC.IDI_ICON_ASSET_TEXT,
            'audio': grinsRC.IDI_ICON_ASSET_AUDIO,
            'video': grinsRC.IDI_ICON_ASSET_VIDEO,
            'ref': grinsRC.IDI_ICON_ASSET_BLANK,
            'textstream': grinsRC.IDI_ICON_ASSET_TEXT,
            'animation': grinsRC.IDI_ANIMATION,
            'brush': grinsRC.IDI_BRUSH,
            'animate': grinsRC.IDI_ANIMATE,
            'prefetch': grinsRC.IDI_ICON_ASSET_BLANK,
            'comment': grinsRC.IDI_ICON_ASSET_BLANK,
            'anchor': grinsRC.IDI_ICON_LINKSRC,
            }
    ICON_WIDTH, ICON_HEIGHT = 16, 16

    from smil_mediatype import smil_mediatype
    from MMTypes import mediatypes
    ctrlinteriortypes = ['switch', 'priority']

    # wrapper for MMChannel and MMNode (EditableMMNode) objects
    # each entry in the display tree is associated (1:1) with a wrapper object
    class MMObjWrapper:
        def __init__(self, mmobj, tag):
            if tag == 'prio': tag = 'priority'
            assert tag in SelectElementDlg.tag2imgid.keys(), 'invalid smil element %s' % tag
            self._mmobj = mmobj
            self._tag = tag
            self._display_id = 0

        def getTag(self):
            return self._tag

        def getMMObj(self):
            return self._mmobj

        def getDisplayId(self):
            return self._display_id

        def setDisplayId(self, id):
            self._display_id = id

        def isRegion(self):
            return self._mmobj.getClassName() in ('Region', 'Viewport')

        def getId(self):
            if self._mmobj is None: return ''
            if self._mmobj.getClassName() in ('Region', 'Viewport'):
                return self._mmobj.GetUID()
            else:
                return self._mmobj.GetRawAttrDef('name', '')

        def getSrc(self):
            if self._mmobj is None: return ''
            if self._mmobj.getClassName() == 'MMNode':
                if self._mmobj.GetType()=='ext':
                    return self._mmobj.GetRawAttr('file') or ''
                elif self._mmobj.GetType()=='imm':
                    return 'immediate'
            return ''

        def getMimetype(self):
            if self._mmobj is None: return ''
            if self._mmobj.getClassName() == 'MMNode' and self._mmobj.GetType() == 'ext':
                return self._mmobj.GetComputedMimeType() or ''
            return ''

        def getDisplayImgId(self):
            return SelectElementDlg.tag2imgid.get(self._tag) or grinsRC.IDB_IMAGE

        def getDisplayName(self):
            if self._mmobj is None:
                name = ''
            elif self._mmobj.getClassName() in ('Region', 'Viewport'):
                name = self._mmobj.GetUID()
            else:
                name = self._mmobj.GetRawAttrDef('name', '')
            return name or 'no name'

    def __init__(self, parent, root, selection=None, filter = '', title=''):
        ResDialog.__init__(self,grinsRC.IDD_SELECT_ELEMENT, parent)
        self._root = root
        self._filter = filter

        # selection refs
        self._selection = selection
        self._selwrapper = None

        # ui flags
        self.__isoswnd = 0
        self.__lockupdate = 0

        # create default dialog title
        if title:
            self._title = title
        elif not filter:
            self._title = 'Select element'
        elif filter == 'region':
            self._title = 'Select region'
        elif filter == 'node':
            self._title = 'Select node'
        elif filter == 'topLayout':
            self._title = 'Select topLayout'
        # self._title can be overriden from calling code
        # before the show or DoModal call

        # create controls
        self._bselect = Button(self,win32con.IDOK)
        self._bcancel = Button(self,win32con.IDCANCEL)
        self._editsel = Edit(self, grinsRC.IDC_EDIT1)
        self._msg = Edit(self, grinsRC.IDC_STATIC_MSG)
        self._msg2 = Edit(self, grinsRC.IDC_STATIC_MSG2)

        # tree and maps
        self._tree = None
        self._wrappers = {}
        self._mmid2wrapper = {}

        # image list
        self._tag2index = {}
        initsize = grow = len(self.tag2imgid)
        mask = 0
        self._imageList = win32ui.CreateImageList(self.ICON_WIDTH, self.ICON_HEIGHT, mask, initsize, grow)
        self._imageList.SetBkColor(win32api.RGB(255,255,255))
        index = 0
        for tag, id in self.tag2imgid.items():
            self.appendIcon(id)
            self._tag2index[tag] = index
            index = index + 1

    def appendIcon(self, resid):
        icon = win32ui.GetApp().LoadIcon(resid)
        self._imageList.Add(icon)

    def appendImage(self, resid):
        bitmap = loadBitmapFromResId(resid)
        self._imageList.Add(bitmap.GetHandle(), 0)

    def OnInitDialog(self):
        self.__isoswnd = 1

        # soft dialog title
        self.SetWindowText(self._title)

        # controls binding
        self.attach_handles_to_subwindows()

        # tree
        self._tree = self.GetDlgItem(grinsRC.IDC_TREE1)
        self._tree.SetImageList(self._imageList, commctrl.LVSIL_NORMAL)
        self.buildElementsTree() # also potentially sets self._selwrapper
        self.HookNotify(self.OnSelChanged, commctrl.TVN_SELCHANGED)

        # set initial tree selection
        if self._selwrapper is not None:
            self._tree.Select(self._selwrapper.getDisplayId(), commctrl.TVGN_CARET)
            self._editsel.settext(self._selwrapper.getDisplayName())
        else:
            self._editsel.settext('')
        return ResDialog.OnInitDialog(self)

    def OnOK(self):
        self.__isoswnd = 0
        self.__cleanup()
        return self._obj_.OnOK()

    def OnCancel(self):
        self.__isoswnd = 0
        self.__cleanup()
        return self._obj_.OnCancel()

    def __cleanup(self):
        del self._wrappers
        del self._mmid2wrapper
        del self._tag2index

    def __updateSelectEnable(self):
        enable = 1
        if self._selwrapper is not None:
            self._selection = self._selwrapper.getMMObj()
            if self._filter == 'topLayout' and self._selwrapper.getTag() != 'topLayout':
                enable = 0
            elif self._filter == 'region' and not self._selwrapper.isRegion():
                enable = 0
            elif self._filter == 'node' and self._selwrapper.isRegion():
                enable = 0
            elif self._filter == 'node' and self._selwrapper.getTag() in self.ctrlinteriortypes:
                enable = 0
        else:
            self._selection = None
            enable = 0
        self._bselect.enable(enable)

    # replacement of DoModal within a platform independent context
    # usage pattern without callbacks:
    # if dlg.show():
    #       use(dlg.gettext())
    def show(self):
        return self.DoModal() == win32con.IDOK

    def getmmobject(self):
        if self._selwrapper:
            return self._selwrapper.getMMObj()
        return None

    def settitle(self, text):
        self._title = text
        if self.__isoswnd:
            self.SetWindowText(text)

    # build browser tree (layout and/or body) appropriate for the filter specified
    def buildElementsTree(self):
        filter = self._filter
        if not filter or filter == 'region' or filter == 'topLayout':
            self.__buildLayoutTree()
        if not filter or filter == 'node':
            self.__buildBodyTree()

    # build layout tree
    def __buildLayoutTree(self):
        root = self._root
        ctx = root.GetContext()
        top_levels = ctx.getviewports()
        for top in top_levels:
            wrapper = self.MMObjWrapper(top, 'topLayout')
            itemid = self.insertMMObjWrapper(wrapper)
            self.__appendRegions(top, itemid)

    def __appendRegions(self, parent, itemid):
        for reg in parent.GetChildren():
            if reg.get('type') == 'layout':
                wrapper = self.MMObjWrapper(reg, 'region')
                citemid = self.insertMMObjWrapper(wrapper, itemid)
                self.__appendRegions(reg, citemid)

    # build body tree
    def __buildBodyTree(self):
        root = self._root
        wrapper = self.MMObjWrapper(root, 'body')
        rootid = self.insertMMObjWrapper(wrapper)
        self.__appendNodes(root, rootid)

    def __appendNodes(self, parent, itemid):
        for node in parent.children:
            ntype = node.GetType()
            if ntype in self.mediatypes:
                smiltype = self.smil_mediatype.get(node.GetChannelType(), 'ref')
                wrapper = self.MMObjWrapper(node, smiltype)
                citemid = self.insertMMObjWrapper(wrapper, itemid)
            elif ntype in ('animpar', 'animate'):
                # XXX for now, do not include animate nodes.
                # need to handle a special case for that.
                continue
            else:
                smiltype = node.GetType()
                wrapper = self.MMObjWrapper(node, smiltype)
                citemid = self.insertMMObjWrapper(wrapper, itemid)
            self.__appendNodes(node, citemid)

    # expand item branch helper
    def __expand(self, item):
        if self._tree.ItemHasChildren(item):
            self._tree.Expand(item, commctrl.TVE_EXPAND)
            item = self._tree.GetChildItem(item)
            while item:
                self.__expand(item)
                try: item = self._tree.GetNextSiblingItem(item)
                except: item = None

    # response on a tree selection change
    def OnSelChanged(self, std, extra):
        if self.__lockupdate: return
        nmsg = win32mu.Win32NotifyMsg(std, extra, 'tree')
        itemid = nmsg.itemNew[0]
        wrapper = self._wrappers.get(itemid)
        self._selwrapper = wrapper
        if wrapper is not None:
            self.__lockupdate = 1
            self._editsel.settext(wrapper.getDisplayName())
            self._msg.settext(wrapper.getSrc())
            self._msg2.settext(wrapper.getMimetype())
            self.__lockupdate = 0
        else:
            print 'missing wrapper for item', self._tree.GetItemText(itemid)
        self.__updateSelectEnable()

    # insert MMObjWrapper to the tree and update maps
    def insertMMObjWrapper(self, wrapper, parent = commctrl.TVI_ROOT, after = commctrl.TVI_LAST):
        mask = commctrl.TVIF_TEXT | commctrl.TVIF_PARAM |  commctrl.TVIF_IMAGE | commctrl.TVIF_SELECTEDIMAGE
        name = wrapper.getDisplayName()
        imageix = self._tag2index.get(wrapper.getTag(), 0)
        itemid = self._tree.InsertItem(mask, name, imageix, imageix, 0, 0, 0, parent, after)
        wrapper.setDisplayId(itemid)
        if not self._wrappers.has_key(itemid):
            self._wrappers[itemid] = wrapper
        else:
            print 'Warning: SelectElement: duplicate itemid', itemid
        if type(self._selection) == type(""):
            # XXX special case for region/viewport
            mmobj = wrapper.getMMObj()
            if hasattr(mmobj,'name'):
                if self._selection is not None and mmobj.name == self._selection:
                    self._selwrapper = wrapper
        else:
            if self._selection is not None and wrapper.getMMObj() is self._selection:
                self._selwrapper = wrapper
        return itemid

# Implementation of the Layout name dialog
class LayoutNameDlg(ResDialog):
    resource = grinsRC.IDD_LAYOUT_NAME
    def __init__(self,prompt,default_text,cb_ok,cancelCallback=None,parent=None):
        ResDialog.__init__(self, self.resource, parent)
        self._text= Edit(self, grinsRC.IDC_EDIT1)
        self._cb_ok=cb_ok
        self._cbd_cancel=cancelCallback
        self._default_text=default_text

    def OnInitDialog(self):
        self.attach_handles_to_subwindows()
        self._text.settext(self._default_text)
        return ResDialog.OnInitDialog(self)

    def show(self):
        self.DoModal()

    def OnOK(self):
        text=self._text.gettext()
        self._obj_.OnOK()
        if self._cb_ok:
            apply(self._cb_ok,(text,))

    def OnCancel(self):
        self._obj_.OnCancel()
        if self._cbd_cancel:
            apply(apply,self._cbd_cancel)

# Implementation of the new channel dialog
class NewChannelDlg(ResDialog):
    def __init__(self,title,default,grab=1,parent=None):
        ResDialog.__init__(self,grinsRC.IDD_NEW_CHANNEL,parent)
        self._default_name=default
        self._chantext= Edit(self,grinsRC.IDC_CHANNEL_NAME)
        self._chantype=ComboBox(self,grinsRC.IDC_CHANNEL_TYPE)
        self._cbd_ok=None
        self._cbd_cancel=None

    def OnInitDialog(self):
        self.attach_handles_to_subwindows()
        self.init_subwindows()
        self._chantext.settext(self._default_name)
        return ResDialog.OnInitDialog(self)

    def show(self):
        self.DoModal()

    def close(self):
        self.EndDialog(win32con.IDCANCEL)

    def OnOK(self):
        if self._cbd_ok:
            apply(apply,self._cbd_ok)

    def OnCancel(self):
        if self._cbd_cancel:
            apply(apply,self._cbd_cancel)

# Implementation of the select template dialog
class OpenAppDialog(ResDialog):
    def __init__(self, title, cb_new, cb_open, cb_never_again,
                 recentlist, cb_recent, parent=None):
        ResDialog.__init__(self,grinsRC.IDD_INIT_DIALOG,parent)
        self._title = title or 'Ambulant'
        self._cb_open = cb_open
        self._cb_new = cb_new
        self._cb_never_again = cb_never_again
        self._cb_recent = cb_recent
        self._recentlist = recentlist
        self._r_open = RadioButton(self, grinsRC.IDC_INIT_OPEN)
        self._r_new = RadioButton(self, grinsRC.IDC_INIT_NEW)
        self._r_recent = RadioButton(self, grinsRC.IDC_INIT_RECENT)
        self._c_recent = ComboBox(self, grinsRC.IDC_INIT_RECENT_COMBO)
        self._r_nothing = RadioButton(self, grinsRC.IDC_INIT_NOTHING)
        self._b_never_again = CheckButton(self, grinsRC.IDC_INIT_NEVER_AGAIN)

        self.show()

    def OnInitDialog(self):
        self.SetWindowText(self._title)
        self.attach_handles_to_subwindows()
        self.init_subwindows()
        self._r_new.setcheck(1)
        self._r_open.setcheck(0)
        self._r_recent.setcheck(0)
        self._r_nothing.setcheck(0)
        self._c_recent.hookcommand(self, self.OnChangeRecent)
        for i in range(len(self._recentlist)):
            self._c_recent.insertstring(i, self._recentlist[i][0])
        self._b_never_again.setcheck(0)
        if self._cb_never_again is None:
            self._b_never_again.hide()
        return ResDialog.OnInitDialog(self)

    def show(self):
        self.DoModal()

    def OnChangeRecent(self, id, code):
        # If the user changes the "recent file" we select the
        # radiobutton automatically.
        self._r_new.setcheck(0)
        self._r_open.setcheck(0)
        self._r_nothing.setcheck(0)
        self._r_recent.setcheck(1)

    def close(self):
        self.EndDialog(win32con.IDCANCEL)

    def OnOK(self):
        self.close()
        if self._b_never_again.getcheck():
            if self._cb_never_again:
                self._cb_never_again()
        if self._r_open.getcheck():
            self._cb_open()
        elif self._r_new.getcheck():
            self._cb_new()
        elif self._r_recent.getcheck():
            which = self._c_recent.getcursel()
            if 0 <= which <= len(self._recentlist):
                self._cb_recent(self._recentlist[which][1][0])

    def OnCancel(self):
        self.close()

# Implementation of the select template dialog
class TemplateDialog(ResDialog):
    def __init__(self,names, descriptions, cb,parent=None):
        ResDialog.__init__(self,grinsRC.IDD_TEMPLATE_DIALOG,parent)
        self._parent=parent
        self._names = names
        self._descriptions = descriptions
        self._cb = cb
        self._select=ComboBox(self,grinsRC.IDC_TEMPLATECOMBO)
        self._explanation = Static(self, grinsRC.IDC_EXPLANATION)
        self._picture = WndCtrl(self, grinsRC.IDC_PICTURE)
##         self._html_templates = (
##             RadioButton(self, grinsRC.IDC_TARGET_EXTERN),
##             RadioButton(self, grinsRC.IDC_TARGET_EMBEDDED))
        self._bmp = None

        self.show()

    def OnInitDialog(self):
        self.attach_handles_to_subwindows()
        self.init_subwindows()
        for i in range(len(self._names)):
            self._select.insertstring(i, self._names[i])
##         self._html_templates[0].setcheck(1)
##         self._html_templates[1].setcheck(0)
        self._select.setcursel(0)
        self._select.hookcommand(self, self.OnChangeTemplate)
        self._setdialoginfo()
        self._picture.create_wnd_from_handle()
        self.HookMessage(self.OnDrawItem,win32con.WM_DRAWITEM)
        return ResDialog.OnInitDialog(self)

    # Response to combo selection change
    def OnChangeTemplate(self,id,code):
        if code==win32con.CBN_SELCHANGE:
            self._setdialoginfo()

    def show(self):
        self.DoModal()

    # Response to the WM_DRAWITEM
    # draw splash
    def OnDrawItem(self,params):
        lParam=params[3]
        hdc=Sdk.ParseDrawItemStruct(lParam)
        dc=win32ui.CreateDCFromHandle(hdc)
        rct=self._picture.GetClientRect()
        # XXXX Should center the picture
##         print 'ondraw', rct, params, self._bmp
##         dc.FillSolidRect(rct, win32mu.RGB((255,255,255)))
        if self._bmp:
            win32mu.BitBltBmp(dc,self._bmp,rct)
        br=Sdk.CreateBrush(win32con.BS_SOLID,0,0)
        dc.FrameRectFromHandle(rct,br)
        Sdk.DeleteObject(br)
        dc.DeleteDC()

    # load splash bmp
    def _loadbmp(self, file):
        self._bmp = None
        if not file:
            return
        try:
            fp = open(file, 'rb')
        except IOError:
            return
        self._bmp=win32ui.CreateBitmap()
        self._bmp.LoadBitmapFile(fp)

    def close(self):
        self.EndDialog(win32con.IDCANCEL)

    def OnOK(self):
        which = self._select.getcursel()
        self.close()
        if 0 <= which <= len(self._descriptions):
            rv = self._descriptions[which]
            self._cb(rv)

    def OnCancel(self):
        self.close()

    def _setdialoginfo(self):
        which = self._select.getcursel()
        if 0 <= which <= len(self._descriptions):
            description = self._descriptions[which][0]
            picture = self._descriptions[which][1]
        else:
            description = ''
            picture = None
        self._explanation.settext(description)
        self._loadbmp(picture)
        self.InvalidateRect()

class BandwidthComputeDialog(ResDialog):
    def __init__(self, caption, parent=None, grab=0):
        self._caption = caption
        ResDialog.__init__(self, grinsRC.IDD_BANDWIDTH_DIALOG, parent)
        self._parent = parent
        self._message = Static(self, grinsRC.IDC_MESSAGE)
        self._preroll = Static(self, grinsRC.IDC_PREROLL)
        self._stalltime = Static(self, grinsRC.IDC_STALLTIME)
        self._stallcount = Static(self, grinsRC.IDC_STALLCOUNT)
        self._errorcount = Static(self, grinsRC.IDC_ERRORCOUNT)
        self._message2 = Static(self, grinsRC.IDC_MESSAGE2)
        self._ok = Button(self, win32con.IDOK)
        self._cancel = Button(self, grinsRC.IDC_CANCEL)
        self._help = Button(self, win32con.IDHELP)
        self.mustwait = 0
        if not grab:
            self.CreateWindow(parent)
            self.ShowWindow(win32con.SW_SHOW)
            self.UpdateWindow()
        self._grab=grab

    def show(self):
        if self._grab:
            self.DoModal()

    def OnInitDialog(self):
        self.attach_handles_to_subwindows()
        self._message.settext(self._caption)
        self._preroll.settext('Computing...')
        self._stalltime.settext('Computing...')
        self._stallcount.settext('Computing...')
        self._errorcount.settext('Computing...')
        self._message2.settext('')
        self._ok.settext('OK')
        self._help.hookcommand(self,self.OnHelp)
        self._cancel.hookcommand(self,self.onCancel)
        self.init_subwindows()
        self.CenterWindow()
        return ResDialog.OnInitDialog(self)

    def setinfo(self, prerolltime, errorseconds, delaycount, errorcount):
        msg = 'Everything appears to be fine.'
        if prerolltime or errorseconds or errorcount or delaycount:
            self.mustwait = 1
            msg = 'This is a minor problem.'
        if errorcount:
            msg = 'You should probably fix this.'
        if prerolltime == 0:
            prerolltime = '0 seconds'
        elif prerolltime < 1:
            prerolltime = 'less than a second'
        else:
            prerolltime = '%d seconds'%prerolltime
        if errorseconds == 0:
            errorseconds = '0 seconds'
        elif errorseconds < 1:
            errorseconds = 'less than a second'
        else:
            errorseconds = '%d seconds'%errorseconds
            msg = 'You should probably fix this.'
        if errorcount == 1:
            errorcount = '1 item'
        else:
            errorcount = '%d items'%errorcount
        if delaycount == 1:
            delaycount = '1 item'
        else:
            delaycount = '%d items'%delaycount
        self._preroll.settext(prerolltime)
        self._stalltime.settext(errorseconds)
        self._stallcount.settext(delaycount)
        self._errorcount.settext(errorcount)
        self._message2.settext(msg)

    def done(self, callback=None, cancancel=0):
        if cancancel and self.mustwait == 0:
            # Continue without waiting
            self.close()
            callback()
            return
        self.callback = callback
        self._ok.enable(1)
        if cancancel:
            self._ok.settext('Proceed...')
            self._cancel.show()
            self._cancel.enable(1)

    def close(self):
        self.EndDialog(win32con.IDCANCEL)

    def OnOK(self):
        self.close()
        if self.callback:
            self.callback()

    def OnCancel(self):
        self.close()
    def onCancel(self,id,code):
        self.close()

    def OnHelp(self, id, code):
        import Help
        Help.givehelp('bandwidth')

class ProgressDialog:
    # Workaround to make the dialog disappear when deleted
    def __init__(self, *args):
        self._dialog = apply(_ProgressDialog, args)

    def set(self, *args):
        apply(self._dialog.set, args)

    def __del__(self):
        self._dialog.close()
        del self._dialog

class _ProgressDialog(ResDialog):
    def __init__(self, title, cancelcallback=None, parent=None, delaycancel=1, percent=0):
        self.cancelcallback = cancelcallback
        self._title = title
        self.delaycancel = delaycancel
        self._percent = percent
        ResDialog.__init__(self,grinsRC.IDD_PROGRESS,parent)
        self._parent=parent
        self._progress = ProgressControl(self,grinsRC.IDC_PROGRESS1)
        self._message = Static(self, grinsRC.IDC_MESSAGE)
        self._curcur = None
        self._curmax = None
        self._cancel_pressed = 0
        self.CreateWindow(parent)
        self.ShowWindow(win32con.SW_SHOW)
        self.UpdateWindow()

    def __del__(self):
        self.close()

    def OnInitDialog(self):
        self.SetWindowText(self._title)
        self.attach_handles_to_subwindows()
        self.init_subwindows()
        # Grey out cancel if no cancelcallback
        if self.cancelcallback == None:
            button = self.GetDlgItem(win32con.IDCANCEL)
            Sdk.EnableWindow(button.GetSafeHwnd(),0)

        return ResDialog.OnInitDialog(self)

    def close(self):
        self.EndDialog(win32con.IDCANCEL)

    def OnCancel(self):
        # Don't call callback now, we are probably not in the
        # right thread. Remember for the next set call
        self._cancel_pressed = 1
        if not self.delaycancel and self.cancelcallback:
            self.cancelcallback()

    def set(self, label, cur1=None, max1=None, cur2=None, max2=None):
        if self._cancel_pressed and self.cancelcallback:
            self.cancelcallback()
        if cur1 != None:
            if self._percent:
                label = label + "    %.0f%s" % (cur1, '%')
            else:
                label = label + " (%d of %d)" % (cur1, max1)
        self._message.settext(label)
        if max2 == None:
            cur2 = None
        if max2 != self._curmax:
            self._curmax = max2
            if max2 == None:
                max2 = 0
            self._progress.setrange(0, max2)
        if cur2 != self._curcur:
            self._curcur = cur2
            if cur2 == None:
                cur2 = 0
            self._progress.set(cur2)

class SeekDialog(ResDialog):
    def __init__(self, title, parent):
        self._title = title
        ResDialog.__init__(self,grinsRC.IDD_SEEK, parent)
        self._parent=parent
        self.IDC_SLIDER = grinsRC.IDC_SLIDER_POS+1

        self.updateposcallback = None
        self.timefunction = None
        self.canusetimefunction = None

        self.__curpos = 0
        self.__timerid = 0
        self.__enableExternalUpdate = 1

        self._minind = Static(self, grinsRC.IDC_MIN)
        self._maxind = Static(self, grinsRC.IDC_MAX)

        self.CreateWindow(parent)
        self.ShowWindow(win32con.SW_SHOW)
        self.UpdateWindow()

    def OnInitDialog(self):
        self.SetWindowText(self._title)
        self.attach_handles_to_subwindows()

        l,t,r,b = self.GetWindowRect()
        placeholder = Control(self, grinsRC.IDC_SLIDER_POS)
        placeholder.attach_to_parent()
        rc = self.ScreenToClient(placeholder.getwindowrect())
        self.slider = win32ui.CreateSliderCtrl()
        style = win32con.WS_VISIBLE|win32con.WS_CHILD|commctrl.TBS_HORZ|commctrl.TBS_BOTH|commctrl.TBS_AUTOTICKS
        self.slider.CreateWindow(style, rc, self, self.IDC_SLIDER)

        self.slider.SetTicFreq(5)
        self.slider.SetLineSize(5)
        self.slider.SetPageSize(20)
        self.slider.SetRange(0, 100)

        self.HookNotify(self.OnNotify, commctrl.NM_RELEASEDCAPTURE)
        self.slider.HookMessage(self.OnSliderLButtonDown, win32con.WM_LBUTTONDOWN)

        self.HookMessage(self.OnTimer, win32con.WM_TIMER)
        self.__timerid = self.SetTimer(1,200)

        return ResDialog.OnInitDialog(self)

    def close(self):
        if self.__timerid:
            self.KillTimer(self.__timerid)
        if self.updateposcallback:
            self.updateposcallback(0, 0)
        self.EndDialog(win32con.IDCANCEL)

    def OnCancel(self):
        self.close()

    def setRange(self, min, max):
        imin = int(math.floor(min))
        imax = int(math.ceil(max))
        self._minind.settext('%d' % imin)
        self._maxind.settext('%d' % imax)
        self.slider.SetRange(imin, imax)

    def setPos(self, pos):
        self.slider.SetPos(int(pos+0.5))

    def OnNotify(self, std, extra):
        pos = self.slider.GetPos()
        if pos != self.__curpos:
            self.__curpos = pos
            if self.updateposcallback:
                self.updateposcallback(pos)
        self.__enableExternalUpdate = 1

    def OnSliderLButtonDown(self, params):
        self.__enableExternalUpdate = 0
        return 1 # continue normal processing

    def OnTimer(self, params):
        if self.__enableExternalUpdate and self.canusetimefunction and\
                self.canusetimefunction() and self.timefunction:
            self.setPos(self.timefunction())


# Implementation of the channel undefined dialog
class ChannelUndefDlg(ResDialog):
    def __init__(self,title,default,grab=1,parent=None):
        ResDialog.__init__(self,grinsRC.IDD_CHANNEL_UNDEF,parent)
        self._title=title
        self._default_name=default
        self._parent=parent
        self._chantext= Edit(self,grinsRC.IDC_CHANNEL_NAME)
        self._bcancel = Button(self,win32con.IDCANCEL)
        self._bundef= Button(self,grinsRC.IDC_LEAVE_UNDEF)
        self._bopen = Button(self,win32con.IDOK)
        self._icon=win32ui.GetApp().LoadIcon(grinsRC.IDI_GRINS_QUESTION)
        self._cb_ok=None
        self._cb_undef_ok=None
        self._cb_cancel=None

    def OnInitDialog(self):
        self.SetWindowText(self._title)
        self.attach_handles_to_subwindows()
        self.init_subwindows()
        self._chantext.settext(self._default_name)
        self._bundef.hookcommand(self,self.OnUndef)
        return ResDialog.OnInitDialog(self)

    def OnPaint(self):
        dc, paintStruct = self._obj_.BeginPaint()
        dc.DrawIcon(self.getIconPos(),self._icon)
        self._obj_.EndPaint(paintStruct)

    def getIconPos(self):
        rc=win32mu.Rect(self.GetWindowRect())
        wnd=self.GetDlgItem(grinsRC.IDC_STATIC_ICON)
        rc1=win32mu.Rect(wnd.GetWindowRect())
        x=rc1.left-rc.left;y=rc1.top-rc.top
        import sysmetrics
        cxframe,cyframe,cxborder,cyborder,cycaption = sysmetrics.GetSystemMetrics()
        y=y-cyframe-cyborder-cycaption
        return (x,y)

    def show(self):
        self.DoModal()

    def close(self):
        self.EndDialog(win32con.IDCANCEL)

    def OnOK(self):
        text=self._chantext.gettext()
        self.close()
        if self._cb_ok:
            apply(self._cb_ok,(text,))

    def OnCancel(self):
        self.close()

    def OnUndef(self,id,code):
        if self._cb_undef_ok:
            apply(self._cb_undef_ok,())
        self.close()

# Implementation of the channel undefined dialog
class EnterKeyDlg(ResDialog):
    def __init__(self,cb_ok,parent=None,user='',org='',license=''):
        ResDialog.__init__(self,grinsRC.IDD_ENTER_KEY,parent)
        self._cb_ok = cb_ok
        self._bok = Button(self,win32con.IDOK)
        self._bcancel = Button(self,win32con.IDCANCEL)
        self._tuser = Edit(self,grinsRC.IDC_NAME)
        self._torg = Edit(self,grinsRC.IDC_ORGANIZATION)
        self._tkey = Edit(self,grinsRC.IDC_KEY)
        self.params = user, org, license
        self.show()

    def OnInitDialog(self):
        self.attach_handles_to_subwindows()
        self._tuser.hookcommand(self,self.OnEditChange)
        self._torg.hookcommand(self,self.OnEditChange)
        self._tkey.hookcommand(self,self.OnEditChange)
        user, org, license = self.params
        self._tuser.settext(user)
        self._torg.settext(org)
        self._tkey.settext(license)
        if license:
            self._bok.enable(1)
        else:
            self._bok.enable(0)
        return ResDialog.OnInitDialog(self)

    def show(self):
        self.DoModal()

    def close(self):
        self.EndDialog(win32con.IDCANCEL)

    def OnEditChange(self, id, code):
        if code != win32con.EN_CHANGE:
            return
        ok = self._tkey.gettext()
        self._bok.enable(not not ok)

    def OnOK(self):
        user=self._tuser.gettext()
        org=self._torg.gettext()
        key=self._tkey.gettext()
        self.close()
        if self._cb_ok:
            apply(self._cb_ok,(key, user, org))

    def OnCancel(self):
        self.close()

# Implementation of a modeless message box
class ModelessMessageBox(ResDialog):
    def __init__(self,text,title,parent=None):
        ResDialog.__init__(self,grinsRC.IDD_MESSAGE_BOX,parent)
        self._text= Static(self,grinsRC.IDC_STATIC1)
        self.CreateWindow(parent)
        self._text.attach_to_parent()
        self.SetWindowText(title)
        self._text.settext(text)

# Implementation of the showmessage dialog needed by the core
class showmessage:
    def __init__(self, text, mtype = 'message', grab = 1, callback = None,
                 cancelCallback = None, name = 'message',
                 title = 'Ambulant', parent = None, identity = None):
        # XXXX If identity != None the user should have the option of not
        # showing this message again
        self._wnd=None
        if grab==0:
            self._wnd=ModelessMessageBox(text,title,parent)
            return
        if cancelCallback:
            style = win32con.MB_OKCANCEL
        else:
            style = win32con.MB_OK

        if mtype == 'error':
            style = style |win32con.MB_ICONERROR

        elif mtype == 'warning':
            style = style |win32con.MB_ICONWARNING

        elif mtype == 'information':
            style = style |win32con.MB_ICONINFORMATION

        elif mtype == 'message':
            style = style|win32con.MB_ICONINFORMATION

        elif mtype == 'question':
            style = win32con.MB_OKCANCEL|win32con.MB_ICONQUESTION

        if not parent or not hasattr(parent,'MessageBox'):
            self._res = win32ui.MessageBox(text,title,style)
        else:
            self._res = parent.MessageBox(text,title,style)
        if callback and self._res==win32con.IDOK:
            apply(apply,callback)
        elif cancelCallback and self._res==win32con.IDCANCEL:
            apply(apply,cancelCallback)

    # Returns user response
    def getresult(self):
        return self._res

# Implementation of a question message box
class _Question:
    def __init__(self, text, parent = None):
        self.answer = None
        showmessage(text, mtype = 'question',
                    callback = (self.callback, (1,)),
                    cancelCallback = (self.callback, (0,)),
                    parent = parent)
    def callback(self, answer):
        self.answer = answer

# Shows a question to the user and returns the response
def showquestion(text, parent = None):
    q=_Question(text, parent = parent)
    return q.answer


# A general one line modal input dialog implementation
# use DoModal
class InputDialog(DialogBase):
    def __init__(self, prompt, defValue, okCallback=None,cancelCallback=None,
                            parent=None, passwd=0):
        self.title=prompt
        dll=None
        if passwd:
            id = grinsRC.IDD_PASSWD_DIALOG
            idedit=grinsRC.IDC_EDIT1
            idprompt=grinsRC.IDC_PROMPT1
        else:
            id = win32ui.IDD_SIMPLE_INPUT
            idedit=win32ui.IDC_EDIT1
            idprompt=win32ui.IDC_PROMPT1
        DialogBase.__init__(self, id, parent, dll)
        self._parent=parent
        self.AddDDX(idedit,'result')
        self.AddDDX(idprompt, 'prompt')
        self._obj_.data['result']=defValue
        self._obj_.data['prompt']=prompt
        self._ok_callback=okCallback
        self._cancel_callback=cancelCallback
        self.DoModal()

    def OnInitDialog(self):
        self.SetWindowText(self.title)
        self.CenterWindow()
        return DialogBase.OnInitDialog(self)

    # close the dialog before calling back
    def OnOK(self):
        self._obj_.UpdateData(1) # do DDX
        res=self._obj_.OnOK()
        if self._ok_callback:
            self._ok_callback(self.data['result'])
        return res
    def OnCancel(self):
        res=self._obj_.OnCancel()
        if self._cancel_callback:
            apply(apply,self._cancel_callback)
        return res

#
# A general one line modeless input dialog implementation
# if not closed by def OK,Cancel call DestroyWindow()
# design decision: Dlg closes itself or the callback?
class ModelessInputDialog(InputDialog):
    def __init__(self, prompt, defValue, title):
        InputDialog.__init__(self, prompt, defValue, title)
        self._ok_callback=None
        self._cancel_callback=None
    def OnOK(self):
        self._obj_.UpdateData(1) # do DDX
        if self._ok_callback:
            self._ok_callback(self)
        return self._obj_.OnOK()
    def OnCancel(self):
        if self._cancel_callback:
            self._cancel_callback(self)
        return self._obj_.OnCancel()

# Displays a message and requests from the user to select Yes or No or Cancel
def GetYesNoCancel(prompt,parent=None,title='Ambulant'):
    if parent:m=parent
    else: m=win32ui
    res=m.MessageBox(prompt,title,win32con.MB_YESNOCANCEL|win32con.MB_ICONQUESTION)
    if res==win32con.IDYES:return 0
    elif res==win32con.IDNO:return 1
    else: return 2

# Displays a message and requests from the user to select OK or Cancel
def GetOKCancel(prompt,parent=None,title='Ambulant'):
    if parent:m=parent
    else: m=win32ui
    res=m.MessageBox(prompt,title,win32con.MB_OKCANCEL|win32con.MB_ICONQUESTION)
    if res==win32con.IDOK:return 0
    else: return 1

# Displays a message and requests from the user to select Yes or Cancel
def GetYesNo(prompt,parent=None,title='Ambulant'):
    if parent:m=parent
    else: m=win32ui
    res=m.MessageBox(prompt,title,win32con.MB_YESNO|win32con.MB_ICONQUESTION)
    if res==win32con.IDYES:return 0
    else: return 1

# The create box dialog implementation
class CreateBoxDlg(ResDialog):
    def __init__(self,text,callback,cancelCallback,parent=None):
        ResDialog.__init__(self,grinsRC.IDD_CREATE_BOX1,parent)
        self._text= Static(self,grinsRC.IDC_STATIC1)
        self.CreateWindow(parent)
        self._text.attach_to_parent()
        self._text.settext(text)
        self._callback=callback
        self._cancelCallback=cancelCallback
        self.ShowWindow(win32con.SW_SHOW)
        self.UpdateWindow()

    def OnOK(self):
        self._obj_.OnOK()
        if self._callback:
            apply(apply,self._callback)

    def OnCancel(self):
        self._obj_.OnCancel()
        if self._cancelCallback:
            apply(apply,self._cancelCallback)

# A general dialog that displays a combo with options for the user to select.
class SimpleSelectDlg(ResDialog):
    def __init__(self,list, title = '', prompt = None,parent = None,defaultindex=None):
        ResDialog.__init__(self,grinsRC.IDD_SELECT_ONE,parent)
        self._prompt_ctrl= Static(self,grinsRC.IDC_STATIC1)
        self._list_ctrl= ComboBox(self,grinsRC.IDC_COMBO1)
        self._list=list
        self._title=title
        self._prompt=prompt
        self._defaultindex=defaultindex
        self._result=None

    def OnInitDialog(self):
        DialogBase.OnInitDialog(self)

        self._prompt_ctrl.attach_to_parent()
        if not self._prompt:self._prompt='Select:'
#               self._prompt_ctrl.settext(self._prompt)

        if not self._title:
            if self._prompt:self._title=self._prompt
            else: self._title='Select'
        self.SetWindowText(self._title)

        self._list_ctrl.attach_to_parent()
        self._list_ctrl.setoptions_cb(self._list)
        if self._defaultindex:
            self._list_ctrl.setcursel(self._defaultindex)
        return ResDialog.OnInitDialog(self)

    def OnOK(self):
        self._result=win32con.IDOK
        ix=self._list_ctrl.getcursel()
        res=self._obj_.OnOK()
        if ix>=0:
            item=self._list[ix]
            if type(item)==type(()):
                apply(apply,item[1])
        return res

    def OnCancel(self):
        self._result=win32con.IDCANCEL
        # nothing
        return self._obj_.OnCancel()

    def hookKeyStroke(self,cb,key):
        if hasattr(self,'_obj_') and self._obj_:
            self.HookKeyStroke(cb,key)

# A general dialog that displays a combo with options for the user to select.
class MultiSelectDlg(ResDialog):
    def __init__(self,list, title = '', prompt = None,parent = None,defaultlist=None):
        ResDialog.__init__(self,grinsRC.IDD_SELECT_MULTI,parent)
        self._prompt_ctrl= Static(self,grinsRC.IDC_LABEL)
        self._list_ctrl= ListBox(self,grinsRC.IDC_LIST1)
        self._list=list
        self._title=title
        self._prompt=prompt
        self._defaultlist=defaultlist
        self._result=None

    def OnInitDialog(self):
        DialogBase.OnInitDialog(self)

        self._prompt_ctrl.attach_to_parent()
        if not self._prompt:self._prompt='Select:'
        self._prompt_ctrl.settext(self._prompt)

        if not self._title:
            if self._prompt:self._title=self._prompt
            else: self._title='Select'
        self.SetWindowText(self._title)

        self._list_ctrl.attach_to_parent()
        self._list_ctrl.delalllistitems()
        self._list_ctrl.addlistitems(self._list, 0)
        for i in self._defaultlist:
            self._list_ctrl.multiselect(i, 1)
        return ResDialog.OnInitDialog(self)

    def OnOK(self):
        # xxxx to be done
        self._result = self._list_ctrl.getselitems()
        res=self._obj_.OnOK()
        return res

    def OnCancel(self):
        self._result = None
        return self._obj_.OnCancel()

    def hookKeyStroke(self,cb,key):
        if hasattr(self,'_obj_') and self._obj_:
            self.HookKeyStroke(cb,key)

# Displays a dialog with options for the user to select
def Dialog(list, title = '', prompt = None, grab = 1, vertical = 1,
           parent = None,defaultindex=None):
    dlg=SimpleSelectDlg(list,title,prompt,parent,defaultindex)
    if grab==1:dlg.DoModal()
    else:dlg.CreateWindow(parent)
    return dlg


class _MultChoice:
    def __init__(self, prompt, msg_list, defindex, parent = None):
        self.answer = None
        self.msg_list = msg_list
        list = []
        for msg in msg_list:
            list.append((msg, (self.callback, (msg,))))
        self.dialog = Dialog(list, title = None, prompt = prompt,
                             grab = 1, vertical = 1,
                             parent = parent,defaultindex=defindex)

    def callback(self, msg):
        for i in range(len(self.msg_list)):
            if msg == self.msg_list[i]:
                self.answer = i
                break

def multchoice(prompt, list, defindex, parent = None):
    if len(list) == 3 and list == ['Yes', 'No', 'Cancel']:
        return GetYesNoCancel(prompt, parent)
    if len(list) == 2 and list == ['OK', 'Cancel']:
        return GetOKCancel(prompt, parent)
    mc=_MultChoice(prompt, list, defindex, parent = parent)
    if mc.dialog._result==win32con.IDOK:
        return mc.answer
    else:
        if 'Cancel' in list:
            return list.index('Cancel')
        else:
            return -1

def mmultchoice(prompt, list, deflist, parent = None):
    defindexlist = []
    for defvalue in deflist:
        try:
            i = list.index(defvalue)
        except IndexError:
            print "mmultchoice: unknown default:", defvalue
            continue
        defindexlist.append(i)
    dlg=MultiSelectDlg(list,'',prompt,parent,defindexlist)
    dlg.DoModal()
    if dlg._result is None:
        return None
    indexlist = dlg._result
    rv = []
    for i in indexlist:
        rv.append(list[i])
    return rv

# Base class for dialog bars
class DlgBar(window.Wnd,ControlsDict):
    AFX_IDW_DIALOGBAR=0xE805
    def __init__(self):
        ControlsDict.__init__(self)
        window.Wnd.__init__(self,win32ui.CreateDialogBar())
    def create(self,frame,resid,align=afxres.CBRS_ALIGN_BOTTOM):
        self._obj_.CreateWindow(frame,resid,
                align,self.AFX_IDW_DIALOGBAR)
    def show(self):
        self.ShowWindow(win32con.SW_SHOW)
    def hide(self):
        self.ShowWindow(win32con.SW_HIDE)

# A dialog bar with a message to be displayed while in the create box mode
class CreateBoxBar(DlgBar):
    def __init__(self,frame,text,callback=None,cancelCallback=None):
        DlgBar.__init__(self)
        DlgBar.create(self,frame,grinsRC.IDD_CREATE_BOX,afxres.CBRS_ALIGN_TOP)

        static= Static(self,grinsRC.IDC_STATIC1)
        cancel=Button(self,grinsRC.IDUC_CANCEL)
        ok=Button(self,grinsRC.IDUC_OK)

        static.attach_to_parent()
        cancel.attach_to_parent()
        ok.attach_to_parent()

        frame.HookCommand(self.onCancel,cancel._id)
        frame.HookCommand(self.onOK,ok._id)

        static.settext(text)
        self._callback=callback
        self._cancelCallback=cancelCallback

        self._frame=frame
        frame.RecalcLayout()

    def onOK(self,id,code):
        self.DestroyWindow()
        self._frame.RecalcLayout()
        if self._callback:
            apply(apply,self._callback)

    def onCancel(self,id,code):
        self.DestroyWindow()
        self._frame.RecalcLayout()
        if self._cancelCallback:
            apply(apply,self._cancelCallback)

MONTHS = [
        'January',
        'February',
        'March',
        'April',
        'May',
        'June',
        'July',
        'August',
        'September',
        'October',
        'November',
        'December'
        ]

class WallclockDialog(ResDialog):
    parent=ResDialog
    resource=grinsRC.IDD_WALLCLOCKPOPUP
    def __init__(self, parent=None):
        ResDialog.__init__(self, self.resource, parent)
        self.value = None
        self.return_value = 0

        # The widgets.
        self.w_yr = Edit(self, grinsRC.IDC_YR)
        self.w_mt = ComboBox(self, grinsRC.IDC_MT)
        self.w_dy = Edit(self, grinsRC.IDC_DY)
        self.w_hr = Edit(self, grinsRC.IDC_HR)
        self.w_mn = Edit(self, grinsRC.IDC_MN)
        self.w_sc = Edit(self, grinsRC.IDC_SC)
        self.w_tzsg = ComboBox(self, grinsRC.IDC_TZSG)
        self.w_tzhr = Edit(self, grinsRC.IDC_TZHR)
        self.w_tzmn = Edit(self, grinsRC.IDC_TZMN)
        self.w_cbdate = CheckButton(self, grinsRC.IDC_CBDATE) # checkbox to check date
        self.w_cbtz = CheckButton(self, grinsRC.IDC_CBTZ) # checkbox to check time.
        self.widgets = [self.w_yr, self.w_mt, self.w_dy, self.w_hr, self.w_mn, self.w_sc, self.w_tzsg, self.w_tzhr, self.w_tzmn, self.w_cbdate, self.w_cbtz]

    def OnInitDialog(self):
        for i in self.widgets:
            i.attach_to_parent()

        self.attach_handles_to_subwindows()

        self.w_cbdate.hookcommand(self, self.w_cbdate_callback)
        self.w_cbtz.hookcommand(self, self.w_cbtz_callback)

        yr,mt,dy,hr,mn,sc,tzsg,tzhr,tzmn = self.value
        self.__setwidget_asnum(self.w_yr, yr)
        self.w_mt.setoptions(MONTHS)
        if mt:
            mt = mt - 1
            self.w_mt.setcursel(mt)
        self.__setwidget_asnum(self.w_dy, dy)
        self.__setwidget_asnum(self.w_hr, hr)
        self.__setwidget_asnum(self.w_mn, mn)
        self.__setwidget_asnum(self.w_sc, sc)

        self.w_tzsg.setoptions(['East', 'West'])
        if tzsg == '+':
            self.w_tzsg.setcursel(0) # east
        else:
            self.w_tzsg.setcursel(1) # west
        self.__setwidget_asnum(self.w_tzhr, tzhr)
        self.__setwidget_asnum(self.w_tzmn, tzmn)
        if yr is None and mt is None and dy is None:
            self.w_cbdate.setcheck(0)
            self.disable_date()
        else:
            self.w_cbdate.setcheck(1) # doesn't this cause a callback?
            self.enable_date()
        if tzsg is None and tzhr is None and tzmn is None:
            self.w_cbtz.setcheck(0)
            self.disable_tz()
        else:
            self.w_cbtz.setcheck(1)
            self.enable_tz()

    def __setwidget_asnum(self, widget, number):
        # widget is a edit box that we are setting to number.
        if number is not None:
            widget.enable(1)
            widget.settext(`number`)
        else:
            widget.settext('')
            widget.enable(0)

    def __getwidget_asnum(self, widget):
        # returns whatever number that widget has.
        n = widget.gettext()
        try:
            return int(n)
        except ValueError:
            return None

    def show(self):
        return self.DoModal()

    def OnOK(self):
        errorMsg, value = self.get_value_from_widgets()
        if errorMsg is None:
            # save the new value only if no error
            self.value = value
            return self.parent.OnOK(self)
        else:
            # just show an error message
            showmessage(errorMsg, 'error', parent=self)

##     def OnCancel(self):
##         self.DestroyWindow()
##         self.return

    def setvalue(self, value):
        if isinstance(value, type(())):
            self.value = value

    def getvalue(self):
        return self.value

    def __checkDate(self, dy, mt, yr):
        # full checking
        if yr < 1900 or yr > 2200:
            return 'bad year'
        if mt < 1 or mt > 12:
            return 'bad month'
        if mt in (1, 3, 5, 7, 8, 10, 12):
            maxDy = 31
        elif mt in (4, 6, 9, 11):
            maxDy = 30
        elif mt == 2:
            # this check works until 2100. It should be enough !
            if yr % 4 == 0:
                maxDy = 29
            else:
                maxDy = 28
        if dy < 1 or dy > maxDy:
            return 'bad day'

        # no error
        return None

    def __checkHour(self, hr, mn, sc):
        # full checking
        if hr < 0 or hr > 23:
            return 'bad hours'
        if mn < 0 or mn > 59:
            return 'bad minutes'
        if sc is not None and (sc < 0 or sc >= 60.0):
            return 'bad seconds'

        # no error
        return None

    def get_value_from_widgets(self):
        errorMsg = None
        yr = mt = dy = hr = mn = sc = tzsg = tzhr = tzmn = None

        if self.w_cbdate.getcheck():
            yr = self.__getwidget_asnum(self.w_yr)
            mt = self.w_mt.getcursel()+1
            assert mt >= 1 and mt <= 12
            dy = self.__getwidget_asnum(self.w_dy)
            errorMsg = self.__checkDate(dy, mt, yr)
        if errorMsg is None:
            hr = self.__getwidget_asnum(self.w_hr)
            mn = self.__getwidget_asnum(self.w_mn)
            sc = self.__getwidget_asnum(self.w_sc)
            errorMsg = self.__checkHour(hr, mn, sc)

        if sc == None:
            sc = 0.0
        if errorMsg is None:
            if self.w_cbtz.getcheck():
                tzsg = self.w_tzsg.getcursel() # it's a combobox.
                if tzsg == 0:
                    tzsg = '+' # East - forwards towards china
                else:
                    tzsg = '-' # West - backwards to Tonga.
                tzhr = self.__getwidget_asnum(self.w_tzhr)
                tzmn = self.__getwidget_asnum(self.w_tzmn)
                if tzhr is None or tzhr < 0 or tzhr > 23:
                    errorMsg = 'bad tz hours'
                elif tzmn is None or tzmn < 0 or tzmn > 59:
                    errorMsg = 'bad tz minutes'

        return errorMsg, (yr, mt, dy, hr, mn, sc, tzsg, tzhr, tzmn)

    def w_cbdate_callback(self, id, value):
        c = self.w_cbdate.getcheck()
        if c:
            self.enable_date()
        else:
            self.disable_date()

    def w_cbtz_callback(self, id, value):
        c = self.w_cbtz.getcheck()
        if c:
            self.enable_tz()
        else:
            self.disable_tz()

    def enable_date(self):
        # initialize fields if empty
        # XXX: it would be probably better at some point to initialize with the current day
        if self.w_dy.gettext() == "":
            self.w_dy.settext("1")
        if self.w_mt.getcursel() < 0:
            self.w_mt.setcursel(0) # january
        if self.w_yr.gettext() == "":
            self.w_yr.settext("2001")

        self.w_yr.enable(1)
        self.w_mt.enable(1) # is a combo box.
        self.w_dy.enable(1)

    def disable_date(self):
        self.w_yr.enable(0)
        self.w_mt.enable(0) # is a combo box.
        self.w_dy.enable(0)

    def enable_tz(self):
        self.w_tzsg.enable(1)   # combo box
        self.w_tzhr.enable(1)
        self.w_tzmn.enable(1)

    def disable_tz(self):
        self.w_tzsg.enable(0)   # combo box
        self.w_tzhr.enable(0)
        self.w_tzmn.enable(0)

class FindDialog(ResDialog):
    resource=grinsRC.IDD_FIND
    def __init__(self, findNextCallback, text = None, options = None, parent=None):
        ResDialog.__init__(self, self.resource, parent)
        self._findNextCallback = findNextCallback
        self._options = options
        self._text = text
        self._parent = parent

        # The widgets.
        self._findNextBtn = Button(self, grinsRC.IDC_FINDNEXT)
        self._findWhat = Edit(self, grinsRC.IDC_FINDWHAT)
        self._matchWhole = CheckButton(self, grinsRC.IDC_MATCHWHOLE)
        self._matchCase = CheckButton(self, grinsRC.IDC_MATCHCASE)

    def OnInitDialog(self):
        # attach to the parent
        self._findNextBtn.attach_to_parent()
        self._findWhat.attach_to_parent()
        self._matchWhole.attach_to_parent()
        self._matchCase.attach_to_parent()

        # init control values
        if self._options != None:
            mw, mc = self._options
            self._matchWhole.setcheck(mw)
            self._matchCase.setcheck(mc)

        if self._text != None:
            self._findWhat.settext(self._text)

        # hook commands
        self._findNextBtn.hookcommand(self, self._onFindNext)
        self.HookMessage(self._onCommand, win32con.WM_COMMAND)
        self._isInit = 1

    def _onCommand(self, params):
        # crack win32 message
        msg=win32mu.Win32Msg(params)
        code = msg.HIWORD_wParam()
        hctrl = msg._lParam

        findWhatEmpty = self._findWhat.gettext() == ''

        # if the 'find what' field is empty, disable all buttons
        if findWhatEmpty:
            self._findNextBtn.enable(0)
        else:
            self._findNextBtn.enable(1)

        return 1

    def OnDestroy(self, id):
        self._isInit = 0
        return 1

    def _onFindNext(self, id, value):
        if self._findNextCallback != None:
            options = (self._matchWhole.getcheck(),
                               self._matchCase.getcheck())
            text = self._findWhat.gettext()
            self._findNextCallback(text, options)

    def show(self):
        self.CreateWindow(self._parent)
        self.ShowWindow(win32con.SW_SHOW)

    def enableReplace(self, f):
        pass

    def hide(self):
        if self._isInit:
            self.DestroyWindow()

class ReplaceDialog(FindDialog):
    resource=grinsRC.IDD_REPLACE
    def __init__(self, findNextCallback, replaceCallback, replaceAllCallback, text = None, replaceText = None, options = None, parent=None):
        FindDialog.__init__(self, findNextCallback, text, options, parent)
        self._replaceText = replaceText
        self._replaceCallback = replaceCallback
        self._replaceAllCallback = replaceAllCallback
        # The additional widgets.
        self._replaceBtn = Button(self, grinsRC.IDC_REPLACE)
        self._replaceAllBtn = Button(self, grinsRC.IDC_REPLACEALL)
        self._replaceWith = Edit(self, grinsRC.IDC_REPLACEWITH)

    def OnInitDialog(self):
        FindDialog.OnInitDialog(self)

        # attach the additional controls to the parent
        self._replaceBtn.attach_to_parent()
        self._replaceAllBtn.attach_to_parent()
        self._replaceWith.attach_to_parent()

        # init additional control values
        if self._replaceText != None:
            self._replaceWith.settext(self._replaceText)

        # disable by default the replace button
        self._replaceBtn.enable(0)

        # additional hook commands
        self._replaceBtn.hookcommand(self, self._onReplace)
        self._replaceAllBtn.hookcommand(self, self._onReplaceAll)

    def _onCommand(self, params):
        # crack win32 message
        msg=win32mu.Win32Msg(params)
        code = msg.HIWORD_wParam()
        hctrl = msg._lParam

        findWhatEmpty = self._findWhat.gettext() == ''

        if (code == win32con.EN_CHANGE and hctrl == self._findWhat.GetSafeHwnd()) or findWhatEmpty:
            # disable the replace button
            self.enableReplace(0)

        # if the 'find what' field is empty, disable all buttons
        if findWhatEmpty:
            self._replaceAllBtn.enable(0)
            self._findNextBtn.enable(0)
        else:
            self._replaceAllBtn.enable(1)
            self._findNextBtn.enable(1)

        return 1

    def _onReplace(self, id, value):
        if self._replaceCallback != None:
            options = (self._matchWhole.getcheck(),
                               self._matchCase.getcheck())
            text = self._findWhat.gettext()
            replaceText = self._replaceWith.gettext()
            self._replaceCallback(text, options, replaceText)

    def _onReplaceAll(self, id, value):
        if self._replaceAllCallback != None:
            options = (self._matchWhole.getcheck(),
                               self._matchCase.getcheck())
            text = self._findWhat.gettext()
            replaceText = self._replaceWith.gettext()
            self._replaceAllCallback(text, options, replaceText)

    def enableReplace(self, f):
        if self._isInit:
            self._replaceBtn.enable(f)
