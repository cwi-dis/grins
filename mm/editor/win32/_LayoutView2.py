__version__ = "$Id$"

# Experimental layout view for light region view

# std win32 modules
import win32ui, win32con, win32api
Sdk = win32ui.GetWin32Sdk()
Afx=win32ui.GetAfx()

# atoi
import string

# win32 lib modules
import win32mu, components

# std mfc windows stuf
from pywinlib.mfc import window,object,docview,dialog
import afxres, commctrl

# UserCmds
from usercmd import *
from wndusercmd import *

from usercmdui import usercmd2id

# GRiNS resource ids
import grinsRC

# we need win32window.Window
# for coordinates transformations
# and other services
import win32window

#
from fmtfloat import fmtfloat

# units
from appcon import *

from GenFormView import GenFormView
import DropTarget
import IconMixin


HIDE_TOPSIBLING = 1

class _LayoutView2(GenFormView):
    def __init__(self,doc,bgcolor=None):
        GenFormView.__init__(self,doc,grinsRC.IDD_LAYOUT_T2)

        self._layout = None
        self._mmcontext = None
        self._slider = None

        self.__ctrlNames=n=('RegionX','RegionY','RegionW','RegionH','RegionZ','AnimateEnable','Fit', 'FitLabel')
        self.__animatedCtrlList=('RegionX','RegionY','RegionW','RegionH')

        self.__listeners = {}

        # save the current value.
        # useful to avoid to send to the listner an update information for each changement
        # it avoids some recursives pb and some crashed
        self.__values = {}
        self.__values['RegionX'] = None
        self.__values['RegionY'] = None
        self.__values['RegionW'] = None
        self.__values['RegionH'] = None
        self.__values['RegionZ'] = None
        self.__values['AnimateEnable'] = None
        self.__values['Fit'] = None

        i = 0
        self[n[i]]=components.Edit(self,grinsRC.IDC_LAYOUT_REGION_X); i=i+1
        self[n[i]]=components.Edit(self,grinsRC.IDC_LAYOUT_REGION_Y); i=i+1
        self[n[i]]=components.Edit(self,grinsRC.IDC_LAYOUT_REGION_W); i=i+1
        self[n[i]]=components.Edit(self,grinsRC.IDC_LAYOUT_REGION_H); i=i+1
        self[n[i]]=components.Edit(self,grinsRC.IDC_LAYOUT_REGION_Z); i=i+1
        self[n[i]]=components.CheckButton(self,grinsRC.IDC_ANIMATE_ENABLE); i=i+1
        self[n[i]]=components.ComboBox(self,grinsRC.IDC_LAYOUT_FITV); i=i+1
        self[n[i]]=components.ComboBox(self,grinsRC.IDC_LAYOUT_FITL); i=i+1

        # Initialize control objects whose command are activable as well from menu bar
        self[ATTRIBUTES]=components.Button(self,usercmd2id(ATTRIBUTES))

        self._activecmds={}

        # set this to 0 to suppress region names
        self._showRegionNames = 1

        # set to true while updating controls due to darwing
        self._mouse_update = 0

        # layout component
        self._previousHandler = None
        self._layout = LayoutManager(self)

        # tree component
        self._treeComponent = TreeManager()

        # allow to valid the field with the return key
        self.lastModifyCtrlField = None

        # org positions
        self.__orgctrlpos = {}

        # flag to request anchors page
        self._showAttributesPage = None

    # special initialization because previous control is not managed like any another component
    # allow to have a handle on previous component from an external module
    def getPreviousComponent(self):
        return self._layout

    # for now avoid to have one handler by dialog ctrl
    def getDialogComponent(self):
        return self

    def getKeyTimeSlider(self):
        return self._slider

    # returning true will make frame resizeable
    def isResizeable(self):
        return 1

    # define a handler for callbacks fnc
    def setListener(self, ctrlName, listener):
        self.__listeners[ctrlName] = listener

    # remove the handler for callback fnc
    def removeListener(self, ctrlName):
        if self.__listeners.has_key(ctrlName):
            del self.__listeners[ctrlName]

    # tree component
    def getTreeComponent(self):
        return self._treeComponent

    # override due to splitter
    def OnClose(self):
        childframe = self.GetParent().GetParent()
        if self._closecmdid>0:
            childframe.GetMDIFrame().PostMessage(win32con.WM_COMMAND, self._closecmdid)
        else:
            childframe.DestroyWindow()

    def close(self):
        self.deactivate()
        if hasattr(self,'_obj_') and self._obj_:
            # pypass splitter
            try:
                self.GetParent().GetParent().DestroyWindow()
            except:
                pass

    def activate(self):
        self._is_active=1
        frame = self.GetParent().GetParent().GetMDIFrame()
        frame.set_commandlist(self._commandlist,self._strid)
        self.set_menu_state()
        #frame.LoadAccelTable(grinsRC.IDR_SOURCE_EDIT)

    def deactivate(self):
        self._is_active=0
        frame = self.GetParent().GetParent().GetMDIFrame()
        frame.set_commandlist(None,self._strid)
        #frame.LoadAccelTable(grinsRC.IDR_SOURCE_EDIT)

    def OnDelete(self):
        splitter = self.GetParent()
        mainframe = splitter.GetParent().GetMDIFrame()
        mainframe.PostMessage(win32con.WM_COMMAND, usercmd2id(DELETE))

    def OnInitialUpdate(self):
        # we use a splitter so don't call GenFormView version
        #GenFormView.OnInitialUpdate(self)
        for ck in self.keys():
            self[ck].attach_to_parent()
            self.EnableCmd(ck,0)
        self.HookMessage(self.OnCmd,win32con.WM_COMMAND)

        # set frame size to 640x480
        self.getViewFrame().SetWindowPos(0, (0, 0, 640, 480),
                        win32con.SWP_NOACTIVATE | win32con.SWP_NOZORDER | win32con.SWP_NOMOVE)

        # enable all lists
        for name in self.__ctrlNames:
            self.EnableCmd(name,1)

        # create layout window
        preview = components.Control(self, grinsRC.IDC_LAYOUT_PREVIEW)
        preview.attach_to_parent()
        l1,t1,r1,b1 = self.GetWindowRect()
        l2,t2,r2,b2 = preview.getwindowrect()
        rc = l2-l1, t2-t1-2, r2-l2, b2-t2
        bgcolor = (255, 255, 255)
        self._layout.onInitialUpdate(self, rc, bgcolor)

        self._treeComponent.onInitialUpdate(self)

        #
        self._slider = components.KeyTimesSlider(self, grinsRC.IDC_LAYOUT_SLIDER)

        # resizing
        self.saveOrgCtrlPos()
        self.resizeCtrls(r1-l1, b1-t1)
        self.HookMessage(self.OnSize, win32con.WM_SIZE)

        # we have to notify layout if has capture
        self.HookMessage(self.onLButtonDown,win32con.WM_LBUTTONDOWN)
        self.HookMessage(self.onLButtonUp,win32con.WM_LBUTTONUP)
        self.HookMessage(self.onMouseMove,win32con.WM_MOUSEMOVE)
        self.HookMessage(self.onLButtonDblClk,win32con.WM_LBUTTONDBLCLK)

        self.addZoomButtons()
        self.addPreviewButtons()
        self.addFocusCtrl()

    #
    # setup the dialog control values
    #

    def fillSelecterCtrl(self, ctrlName, vList):
        # fill combos selecter
        if vList:
            self[ctrlName].resetcontent()
            for vname in vList:
                self[ctrlName].addstring(vname)
            self[ctrlName].setcursel(0)

    def fillMultiSelCtrl(self, ctrlName, vList):
        # fill combos selecter
        if vList:
            self[ctrlName].resetcontent()
            for vname in vList:
                self[ctrlName].addstring(0, vname)
#                       self[ctrlName].setcursel(0)

    def setMultiSelecterCtrl(self, ctrlName, vItem, bValue):
        # for now
        self[ctrlName].sendmessage(win32con.LB_SETSEL, bValue, vItem)

    def setSelecterCtrl(self, ctrlName, value):
        self[ctrlName].setcursel(value)

    def setCheckCtrl(self, ctrlName, bValue):
        self[ctrlName].setcheck(bValue)

    def setFieldCtrl(self, ctrlName, sValue):
        self[ctrlName].settext(sValue)
        value = self[ctrlName].gettext()
        self.__values[ctrlName] = value

    def setLabel(self, ctrlName, value):
        self[ctrlName].settext(value)

    def enable(self, ctrlName, bValue):
        self[ctrlName].enable(bValue)

    #
    # end setup the dialog control values
    #
    def onLButtonDown(self, params):
        if self._slider and self._slider.isEnabled():
            msg = win32mu.Win32Msg(params)
            point = msg.pos()
            flags = msg._wParam
            self._slider.onSelect(point, flags)
        if self._layout is not None and self._layout._drawContext.hasCapture():
            self._layout.onNCLButton(params)

    def onLButtonUp(self, params):
        if self._slider and self._slider.isEnabled():
            msg = win32mu.Win32Msg(params)
            point = msg.pos()
            flags = msg._wParam
            self._slider.onDeselect(point, flags)
        if self._layout is not None and self._layout._drawContext.hasCapture():
            self._layout.onNCLButton(params)

    def onMouseMove(self, params):
        if self._slider and self._slider.isEnabled():
            msg = win32mu.Win32Msg(params)
            point = msg.pos()
            flags = msg._wParam
            self._slider.onDrag(point, flags)
        if self._layout is not None and self._layout._drawContext.hasCapture():
            self._layout.onNCLButton(params)

    def onLButtonDblClk(self, params):
        if self._slider and self._slider.isEnabled():
            msg = win32mu.Win32Msg(params)
            point = msg.pos()
            flags = msg._wParam
            self._slider.onActivate(point, flags)

    # Sets the acceptable command list by delegating to its parent keeping a copy.
    def set_commandlist(self, list):
        GenFormView.set_commandlist(self, list)
        splitter = self.GetParent()
        mainframe = splitter.GetParent().GetMDIFrame()
        mainframe.set_commandlist(list, self._strid)
        self.set_localcommandlist(list)

    # Sets the acceptable commands.
    def set_localcommandlist(self,commandlist):
        frame=self.GetParent()
        contextcmds=self._activecmds
        for cl in self.keys():
            # only menu bar commands
            if type(cl)!=type(''):
                self.EnableCmd(cl,0)
        contextcmds.clear()
        if not commandlist: return
        for cmd in commandlist:
            if cmd.__class__== CLOSE_WINDOW:continue
            if not self.has_key(cmd.__class__):continue
            id=self[cmd.__class__]._id
            self.EnableCmd(cmd.__class__,1)
            contextcmds[id]=cmd

    # apply changement when the control lose the focus. As the 'KILLFOCUS' event may be called
    # too late, this method can be called by the high level code
    def flushChangement(self):
        if self.lastModifyCtrlField != None:
            value = self[self.lastModifyCtrlField].gettext()
            # update the listener only if the value has changed
            if self.__values[self.lastModifyCtrlField] != value:
                self.__values[self.lastModifyCtrlField] = value
                listener = self.__listeners.get(self.lastModifyCtrlField)
                if listener != None:
                    listener.onFieldCtrl(self.lastModifyCtrlField, value)
            self.lastModifyCtrlField = None

    #
    # User input dispatch method
    # i.e response to WM_COMMAND
    #
    def OnCmd(self, params):
        if self._mouse_update: return

        # crack message
        msg=win32mu.Win32Msg(params)
        id=msg.cmdid()
        nmsg=msg.getnmsg()

        if self.__playing and nmsg!=win32con.BN_CLICKED:
            # do nothing if animate previewing
            for ctrlName in self.__animatedCtrlList:
                if id == self[ctrlName]._id:
                    return

        if id==win32con.IDOK or nmsg == win32con.EN_KILLFOCUS:
            self.flushChangement()
            return

        # delegate combo box notifications to handler
        if nmsg==win32con.LBN_SELCHANGE:
            ctrlName = None

            if id == self['Fit']._id:
                ctrlName = 'Fit'

            if ctrlName != None:
                listener = self.__listeners.get(ctrlName)
                if listener != None:
                    value = self[ctrlName].getcursel()
                    listener.onSelecterChanged(ctrlName, value)
                return

        if nmsg==win32con.BN_CLICKED:
            ctrlName = None

            if id == self['AnimateEnable']._id:
                ctrlName = 'AnimateEnable'

            if ctrlName != None:
                value = self[ctrlName].getcheck()
                listener = self.__listeners.get(ctrlName)
                if listener != None:
                    listener.onCheckCtrl(ctrlName, value)
                return

            if ctrlName != None:
                listener = self.__listeners.get(ctrlName)
                if listener != None:
                    listener.onButtonClickCtrl(ctrlName)
                return

        if nmsg==win32con.EN_CHANGE:
            ctrlName = None

            if id == self['RegionX']._id:
                ctrlName = 'RegionX'
            elif id == self['RegionY']._id:
                ctrlName = 'RegionY'
            elif id == self['RegionW']._id:
                ctrlName = 'RegionW'
            elif id == self['RegionH']._id:
                ctrlName = 'RegionH'
            elif id == self['RegionZ']._id:
                ctrlName = 'RegionZ'

            if ctrlName != None:
                self.lastModifyCtrlField = ctrlName

            return

        # process rest
        self.onUserCmd(id, nmsg)

    def onUserCmd(self, id, code=0):
        cmd=None
        contextcmds = self._activecmds
        if contextcmds.has_key(id):
            cmd = contextcmds[id]
            if cmd is not None and cmd.callback is not None:
                apply(apply, cmd.callback)

    def showScale(self, d2lscale):
        t=components.Static(self,grinsRC.IDC_LAYOUT_SCALE)
        t.attach_to_parent()
        str = fmtfloat(d2lscale, prec=1)
        t.settext('Scale 1 : %s' % str)

    def openAttributesPage(self, attrname):
        self._parent.getMDIFrame().addViewCreationListener(self)
        self._showAttributesPage = attrname
        self.onUserCmd(usercmd2id(ATTRIBUTES))

    def onViewCreated(self, frame, view, strid):
        if strid == 'attr_edit':
            if self._showAttributesPage is not None:
                previous = view.showAllAttributes(1)
                view.setcurattrbyname(self._showAttributesPage)
                # restore?
                #if previous==0:
                #       previous = view.showAllAttributes(0)
            frame.removeViewCreationListener(self)
            self._showAttributesPage = None

    #
    # Zoom in/out
    #
    def addZoomButtons(self):
##         self._iconzoomin = win32ui.GetApp().LoadIcon(grinsRC.IDI_ZOOMIN)
##         self._iconzoomout = win32ui.GetApp().LoadIcon(grinsRC.IDI_ZOOMOUT)
##         self._bzoomin = components.Button(self, grinsRC.IDC_ZOOMIN)
##         self._bzoomout = components.Button(self, grinsRC.IDC_ZOOMOUT)
##         self._bzoomin.attach_to_parent()
##         self._bzoomout.attach_to_parent()
##         self._bzoomin.seticon(self._iconzoomin)
##         self._bzoomout.seticon(self._iconzoomout)
##         self._bzoomin.show()
##         self._bzoomout.show()
##         self._bzoomin.hookcommand(self, self.OnZoomIn)
##         self._bzoomout.hookcommand(self, self.OnZoomOut)
        pass

    def OnZoomIn(self, id, params):
        self.zoomIn()

    def OnZoomOut(self, id, params):
        self.zoomOut()

    def zoomIn(self, factor=None):
        if self._layout is None:
            return
        d2lscale = self._layout.getDeviceToLogicalScale()
        if factor == None:
            factor = 1.2
        d2lscale = d2lscale / float(factor)
##         d2lscale = d2lscale - 0.1
##         if d2lscale < 0.1 : d2lscale = 0.1
        self._layout.updateScale(d2lscale)

    def zoomOut(self, factor=None):
        if self._layout is None:
            return
        d2lscale = self._layout.getDeviceToLogicalScale()
        if factor == None:
            factor = 1.2
        d2lscale = d2lscale * factor
##         d2lscale = d2lscale + 0.1
##         if d2lscale>10.0: d2lscale = 10.0
        self._layout.updateScale(d2lscale)

    def zoomReset(self):
        if self._layout is None:
            return
        d2lscale = 1
        self._layout.updateScale(d2lscale)

    def addPreviewButtons(self):
        self._iconplay = win32ui.GetApp().LoadIcon(grinsRC.IDI_PLAY)
        self._iconstop = win32ui.GetApp().LoadIcon(grinsRC.IDI_STOP)
        self._bplay = components.Button(self, grinsRC.IDC_PLAY)
        self._bplay.attach_to_parent()
        self._bplay.seticon(self._iconplay)
        self._bplay.hookcommand(self, self.OnPlay)
        self._bplay.show()
        self._bplay.enable(0)
        self.__playing = 0

    def _play(self):
        self._slider.play()
        self._bplay.seticon(self._iconstop)
        self._bplay.enable(1)
        self.__playing = 1

    def _stop(self):
        self._slider.stop()
        self._bplay.seticon(self._iconplay)
        self._bplay.enable(1)
        self.__playing = 0

    def stop(self):
        if self.__playing:
            self._stop()

    def OnPlay(self, id, params):
        if self._slider and self._slider.isEnabled():
            if not self.__playing:
                self._play()
            else:
                self._stop()
        else:
            self.EnablePreview(0)

    def EnablePreview(self, flag):
        if flag:
            self._bplay.enable(flag)
        else:
            self.__playing = 0
            self._bplay.seticon(self._iconplay)
            self._bplay.enable(0)

    # on selection change call
    def StopPreview(self):
        if self._slider and self._slider.isEnabled():
            self.stop()
        else:
            self.EnablePreview(0)

    #
    # Focus adjustements
    #

    def addFocusCtrl(self):
        treeFocusCtrl = components.Control(self, grinsRC.IDC_TREEFOCUS)
        treeFocusCtrl.attach_to_parent()
        treeFocusCtrl.hookmessage(self.OnSetTreeFocusCtrl, win32con.WM_SETFOCUS)

        self.paneFocusCtrl = self.GetDlgItem(grinsRC.IDC_PANEFOCUS)
        self.paneFocusCtrl.HookMessage(self.OnSetPaneFocusCtrl, win32con.WM_SETFOCUS)
        self.paneFocusCtrl.HookMessage(self.OnKillPaneFocusCtrl, win32con.WM_KILLFOCUS)
        self.paneFocusCtrl.HookMessage(self.OnPaneFocusCtrlKey, win32con.WM_KEYDOWN)

    def OnSetPaneFocusCtrl(self, params):
        if self._layout is None:
            return
        # hilight the pane to simulate the focus
        self._layout.hilight(1)

    def OnKillPaneFocusCtrl(self, params):
        if self._layout is None:
            return
        focusReceiver =  params[2]
        if focusReceiver != self._layout.GetSafeHwnd():
            # remove the hilight from the pane
            self._layout.hilight(0)

    def OnPaneFocusCtrlKey(self, params):
        key = params[2]
        if key == win32con.VK_TAB or self._layout is None:
            # normal bevavior
            return 1
        else:
            # redirect the key to the pane
            return self._layout.onKeyDown(params)

    def OnSetTreeFocusCtrl(self, params):
        # redirect the focus to tree
        self.GetParent().GetPane(0,0).GetTreeCtrl().SetFocus()

    def OnChangeTreeFocus(self):
        # set the pane to the pane
        self.paneFocusCtrl.SetFocus()

    def OnSetPaneFocus(self):
        # redirect the focus to the pane focus ctrl
        self.paneFocusCtrl.SetFocus()

    #
    # Reposition controls on size
    #
    def getCtrlIdsToMoveDown(self):
        return (
                grinsRC.IDC_X, grinsRC.IDC_LAYOUT_REGION_X,
                grinsRC.IDC_Y, grinsRC.IDC_LAYOUT_REGION_Y,
                grinsRC.IDC_W, grinsRC.IDC_LAYOUT_REGION_W,
                grinsRC.IDC_H, grinsRC.IDC_LAYOUT_REGION_H,
                grinsRC.IDC_Z, grinsRC.IDC_LAYOUT_REGION_Z,
                grinsRC.IDC_LAYOUT_SLIDER,
                grinsRC.IDC_ANIMATE_GROUP,
                grinsRC.IDC_ANIMATE_ENABLE,
                grinsRC.IDC_PLAY,
                grinsRC.IDC_ANIMATE_P0L, grinsRC.IDC_ANIMATE_P50L, grinsRC.IDC_ANIMATE_P100L,
                grinsRC.IDC_LAYOUT_FITV, grinsRC.IDC_LAYOUT_FITL,
                grinsRC.IDUC_ATTRIBUTES
                )

    def resizeCtrls(self, w, h):
        if self._layout is None:
            return

        # move controls in their right position
        ctrlIDsToMove = self.getCtrlIdsToMoveDown()

        # controls margin + posibly scrollbar
        cm = 20
        ctrlList = []
        for id in ctrlIDsToMove:
            ctrl = components.Control(self,id)
            ctrl.attach_to_parent()
            ctrlList.append((ctrl,id))
            l,t,r,b = ctrl.getwindowrect()
            h = b-t
            if id in(grinsRC.IDC_LAYOUT_REGION_X, grinsRC.IDC_LAYOUT_REGION_W, grinsRC.IDC_LAYOUT_FITV):
                cm = cm+h
            elif id == grinsRC.IDC_LAYOUT_FITL:
                cm = cm+h*3 # take into acounts three labels


        if  self.GetStyle() & win32con.WS_HSCROLL:
            cm = cm+20

        lf, tf, rf, bf = self.GetWindowRect()

        # resize preview pane
        ll, tl, rl, bl = self._layout.GetWindowRect()
        previewWidth = rf - ll - 10
        previewHeight = bf - tl - cm
        newrc = 0, 0, previewWidth, previewHeight
        # just resize the control (set the flag NOMOVE not to affect the position)
        self._layout.SetWindowPos(self._layout.GetSafeHwnd(), newrc,
                        win32con.SWP_NOACTIVATE | win32con.SWP_NOZORDER | win32con.SWP_NOMOVE)

        flags = win32con.SWP_NOACTIVATE | win32con.SWP_NOZORDER | win32con.SWP_NOSIZE
        for ctrl,id in ctrlList:
            l1,t1,r1,b1 = ctrl.getwindowrect()

            offsetL, offsetR = self.__orgctrlpos[id]
            newrc = offsetL, tl-tf+previewHeight+offsetR, r1-l1, b1-t1

            # XXX we should take into account the scroll bar pos or disable the scroll bar
            # on the view. But how do this in Python ???
            ctrl.setwindowpos(ctrl._hwnd, newrc, flags)

    def saveOrgCtrlPos(self):
        lf, tf, rf, bf = self.GetWindowRect()
        ctrlIDs = self.getCtrlIdsToMoveDown()

        previewRight, previewBottom = self._layout.GetWindowRect()[2:]
        for id in ctrlIDs:
            ctrl = components.Control(self,id)
            ctrl.attach_to_parent()
            l1,t1,r1,b1 = ctrl.getwindowrect()
            # save relative position: first argument is relative to the dialog box left
            # second argument is relative to the preview pane bottom
            self.__orgctrlpos[id] = l1-lf, t1-previewBottom
        self.__orgctrlpos[-1] = self.GetClientRect()[2:]

    def OnSize(self, params):
        msg = win32mu.Win32Msg(params)
        w, h = msg.width(), msg.height()
        worg, horg = self.__orgctrlpos[-1]
        self.resizeCtrls(w, h)
        self.centerViewport()

    def getViewFrame(self):
        return self.GetParent().GetParent()

    def centerViewport(self):
        if self._layout and self._layout._viewport:
            self._layout._viewport.center()

    def OnPaint(self):
        dc, paintStruct = self.BeginPaint()
        if self._slider:
            self._slider.drawOn(dc)
        self.EndPaint(paintStruct)

###########################
# tree component management
# the tree component is based on the PyCTreeCtrl python class, which is itself based
# on MFC CTreeCtrl class. So it's not a lightweight component as Button, List,
# that we manage in componenent module

class TreeManager(IconMixin.ViewMixin):
    def __init__(self):
        self._listener = None
        self._popup = None

    def destroy(self):
        self.treeCtrl.removeExpandListener(self)
        self.treeCtrl.removeMultiSelListener(self)
        self.treeCtrl.removeDragdropListener(self)
        self.treeCtrl.removeStateListener(self)
        self.treeCtrl = None
        self._listener = None
        self._popup = None

    def setListener(self, listener):
        self._listener = listener

    def removeListener(self):
        self._listener = None

    def onInitialUpdate(self, parent):
        import TreeCtrl
        ctrl = None
        if 1:
            treeView = parent.GetParent().GetPane(0,0)
            ctrl = treeView.GetTreeCtrl()
        self.treeCtrl = TreeCtrl.TreeCtrl(parent, grinsRC.IDC_TREE1, ctrl, stateOption=1)
        self.treeCtrl.addMultiSelListener(self)
        self.treeCtrl.addExpandListener(self)
        self.treeCtrl.setDragdropListener(self)
        self.treeCtrl.addStateListener(self)

        # init the image list used in the tree
        import commctrl
        self.initicons()
        self.seticonlist(self.treeCtrl, commctrl.TVSIL_NORMAL, commctrl.TVSIL_NORMAL)
        self.initstateicons()
        self.setstateiconlist(self.treeCtrl, commctrl.TVSIL_STATE)

    def removeNode(self, item):
        self.treeCtrl.DeleteItem(item)

    def OnStateActivated(self, item, stateIndex):
        if self._listener != None:
            self._listener.onStateActivated(item, self.getstateiconname(stateIndex))

    def insertNode(self, parent, text, imageName, selectedImageName):
        iImage = self.geticonid(imageName)
        iSelectedImage = self.geticonid(selectedImageName)

        mask = int(commctrl.TVIF_TEXT|commctrl.TVIF_IMAGE|commctrl.TVIF_SELECTEDIMAGE)
        item = self.treeCtrl.InsertItem(mask,
                                        text, # text
                                        iImage, # iImage
                                        iSelectedImage, # iSelectedImage
                                        commctrl.TVIS_BOLD , # state
                                        0, #state mask
                                        None, #lParam
                                        parent, # parent
                                        commctrl.TVI_LAST)
        return item

    def updateNode(self, item, text, imageName, selectedImageName):
        iImage = self.geticonid(imageName)
        iSelectedImage = self.geticonid(selectedImageName)
        self.treeCtrl.SetItemText(item, text)
        self.treeCtrl.SetItemImage(item, iImage, iSelectedImage)

    # ExpandBranch - Expands a branch completely
    def expandBranch(self, item):
        treeCtrl = self.treeCtrl
        if treeCtrl.ItemHasChildren(item):
            treeCtrl.Expand( item, commctrl.TVE_EXPAND )
            child = treeCtrl.GetChildItem(item)
            while child != None:
                self.expandBranch(child)
                # XXX find the right method
                try:
                    child = treeCtrl.GetNextSiblingItem(child)
                except:
                    child = None

    def expand(self, item):
        try:
            self.treeCtrl.Expand(item, commctrl.TVE_EXPAND)
        except:
            # if the node has no child, it's an error in windows
            pass

    def destroyAllNodes(self):
        self.treeCtrl.DeleteAllItems()

    def selectNodeList(self, itemList):
        self.treeCtrl.SelectItemList(itemList)

    def setStateNodeList(self, itemList, state):
        self.treeCtrl.SetStateItemList(itemList, self.getstateiconid(state))

#       def _onSelect(self, std, extra):
#               action, itemOld, itemNew, ptDrag = extra
#               # XXX the field number doesn't correspond with API documention ???
#               item, field2, field3, field4, field5, field6, field7, field8 = itemNew
#               if self._handler != None:
#                       self._handler.onSelectTreeNodeCtrl(item)

    def OnMultiSelChanged(self):
        self.treeCtrl.GetParent().GetPane(0,1).StopPreview()
        if self._listener != None:
            self._listener.onSelectChanged(self.treeCtrl.getSelectedItems())

    def OnMultiSelUpdated(self, itemList, state):
        if self._listener != None:
            self._listener.onSelectUpdated(itemList, state)

    def OnExpandChanged(self, item, isExpanded):
        if self._listener != None:
            self._listener.onExpanded(item, isExpanded)

    #
    #  drag and drop support methods
    #

    def OnBeginDrag(self, item):
        if self._listener != None:
            self._listener.onBeginDrag(item)

    def beginDrag(self, type, objectId):
        self.treeCtrl.beginDrag(type, objectId)


    def OnDragOver(self, item, type, objectId):
        if self._listener != None:
            effect = self._listener.onDragOver(item, type, objectId)
            return DropTarget.Name2DragEffect(effect)

    def OnDrop(self, item, type, objectId):
        if self._listener != None:
            effect = self._listener.onDrop(item, type, objectId)
            return DropTarget.Name2DragEffect(effect)

    #
    #  popup menu
    #

    def setpopup(self, menutemplate):
        if self._popup:
            self._popup.DestroyMenu()
            self._popup = None
        if menutemplate != None:
            import win32menu
            popup = win32menu.Menu('popup')
            popup.create_popup_from_menubar_spec_list(menutemplate, usercmd2id)
            self._popup = popup
        else:
            self._popup = None
        self.treeCtrl.setpopup(self._popup)

###########################
debugPreview = 0

import winlayout

LayoutManagerBase = winlayout.LayoutScrollOsWnd
LayoutManagerDrawContext = winlayout.MSDrawContext

class LayoutManager(LayoutManagerBase):
    def __init__(self, parent):
        LayoutManagerBase.__init__(self, LayoutManagerDrawContext())
        self._drawContext.addListener(self)
        self._drawContext.setShapeContainer(self)

        self._listener = None
        self._viewport = None
        self._hasfocus = 0
        self._parent = parent

        self._popup = None

        self._selectedList = []

        # decor
        self._blackPen = Sdk.CreatePen(win32con.PS_SOLID, 1, win32api.RGB(0,0,0))
        self._hiddenPen = Sdk.CreatePen(win32con.PS_DOT, 1, win32api.RGB(0,0,0))
        self._hiddenSelectedPen = Sdk.CreatePen(win32con.PS_DOT, 1, win32api.RGB(0,0,255))
        self._selectedPen = Sdk.CreatePen(win32con.PS_SOLID, 1, win32api.RGB(0,0,255))
        self._pathPen = Sdk.CreatePen(win32con.PS_SOLID, 1, win32api.RGB(128,128,128))
        self._hiddenPathPen = Sdk.CreatePen(win32con.PS_DOT, 1, win32api.RGB(128,128,128))
        self._selectedPathPen = Sdk.CreatePen(win32con.PS_SOLID, 1, win32api.RGB(0,0,255))
        self._hiddenSelectedPathPen = Sdk.CreatePen(win32con.PS_DOT, 1, win32api.RGB(0,0,255))

        self._blackBrush = Sdk.CreateBrush(win32con.BS_SOLID, 0, 0)
        self._handlePathBrush = win32ui.CreateBrush(win32con.BS_SOLID, 0, 0)

        self.selInc = 0

    # allow to create a LayoutManager instance before the onInitialUpdate of dialog box
    def onInitialUpdate(self, parent, rc, bgcolor):
        self.createWindow(parent, rc, bgcolor, (0, 0, 1280, 1024))

    def OnCreate(self, cs):
        LayoutManagerBase.OnCreate(self, cs)
        self.HookMessage(self.onKeyDown, win32con.WM_KEYDOWN)
        self.HookMessage(self.OnSetFocus,win32con.WM_SETFOCUS)

        # popup menu
        self.HookMessage(self.OnRButtonDown, win32con.WM_RBUTTONDOWN)

    def OnDestroy(self, params):
        LayoutManagerBase.OnDestroy(self, params)

    #
    # winlayout.MSDrawContext listener interface
    #

    #
    # overrided methods to manage the mouse capture
    # used also to determinate whether the selection is incremental or not
    # XXX should be managed directly by the low level
    #
    def onLButtonDown(self, params):
        self.GetParent().StopPreview()
        msg=win32mu.Win32Msg(params)
        point, flags = msg.pos(), msg._wParam
        if (flags & win32con.MK_CONTROL):
            self.lastSel = self._selectedList
            self.selInc = 1

        self.SetCapture()
        LayoutManagerBase.onLButtonDown(self, params)

    def onLButtonUp(self, params):
        LayoutManagerBase.onLButtonUp(self, params)
        self.ReleaseCapture()

        self.selInc = 0

    #
    #
    #
    def onDSelChanged(self, selections):
        self._selectedList = selections
        if self._listener != None:
            if not self.selInc:
                self._listener.onSelectChanged(selections)
            else:
                # XXX find out the element which has changed
                # should be managed directly by the low level
                for lastItemSel in self.lastSel:
                    itemFound = None
                    for curItemSel in selections:
                        if lastItemSel is curItemSel:
                            itemFound = curItemSel
                            break
                    if not itemFound:
                        # lastItemSel disapear
                        self._listener.onSelectUpdated([lastItemSel], 0)
                        break
                for curItemSel in selections:
                    itemFound = None
                    for lastItemSel in self.lastSel:
                        if lastItemSel is curItemSel:
                            itemFound = curItemSel
                            break
                    if not itemFound:
                        # curItemSel is new
                        self._listener.onSelectUpdated([curItemSel], 1)
                        break


    def onDSelMove(self, selections):
        if self._listener != None:
            self._listener.onGeomChanging(selections)

    def onDSelResize(self, selection):
        if self._listener != None:
            self._listener.onGeomChanging([selection, ])

    def onDSelMoved(self, selections):
        if self._listener != None:
            self._listener.onGeomChanged(selections)

    def onDSelResized(self, selection):
        if self._listener != None:
            self._listener.onGeomChanged([selection, ])

    def onDSelProperties(self, selection):
        if not selection: return
        if isinstance(selection, Polyline):
            # do nothing for now
            pass
#                       index, prop = self._viewport._polyline.insertPoint(self.LPtoNP(self._lbuttondblclk))
#                       if index>0:
#                               self.GetParent()._slider.insertKeyTimeFromPoint(index, prop)
        else:
            selection.onProperties()

    #
    # winlayout.MSDrawContext ShapeContainer interface
    #
    def getMouseTarget(self, point):
        # point is in logical coordinates
        # convert it to natural coordinates
        point = self.LPtoNP(point)

        # check first for handles hit first
        for shape in self._selectedList:
            if shape.getDragHandleAt(point)>=0:
                return shape

        # if click in already a selected shape, don't change the selection
        for shape in self._selectedList:
            if shape.inside(point):
                return shape
            elif shape._relatedShape and shape._relatedShape.inside(point):
                return shape._relatedShape

        if self._viewport:
            shape = self._viewport.getMouseTarget(point)
            return shape

    #
    # interface implementation: function called from an external module
    #
    # define a handler for the layout component
    def setListener(self, listener):
        self._listener = listener

    def removeListener(self):
        self._listener = None

    # create a new viewport
    def newViewport(self, attrdict, name):
        x, y, w, h = attrdict.get('wingeom')
        self._cycaption = win32api.GetSystemMetrics(win32con.SM_CYCAPTION)
        if self._autoscale and not self._cancroll:
            d2lscale = self.findDeviceToLogicalScale(w, h + self._cycaption)
            self.setDeviceToLogicalScale(d2lscale)
        else:
            self.updateCanvasSize()
        self._viewport = Viewport(name, self, attrdict, self._device2logical)
        self._drawContext.reset()
        return self._viewport

    def destroy(self):
        self._drawContext.reset()
        self._viewport = None

        for pen in (self._blackBrush, self._blackPen, self._hiddenPen, self._selectedPen, self._hiddenSelectedPen, \
                                self._pathPen, self._hiddenPathPen, self._selectedPathPen, \
                                self._hiddenSelectedPathPen):
            if pen:
                Sdk.DeleteObject(pen)
        self._blackBrush = 0
        self._hiddenPen = 0
        self._selectedPen = 0
        self._hiddenSelectedPen = 0
        self._pathPen = 0
        self._hiddenPathPen = 0
        self._selectedPathPen = 0
        self._HiddenSelectedPathPen = 0
        self._handlePathBrush = 0

        self._drawContext.removeListener(self)
        self._drawContext.setShapeContainer(None)
        self._parent._layout = None
        self._parent = None

    # selection of a list of nodes
    def selectNodeList(self, shapeList):
        for shape in self._selectedList:
            shape.isSelected = 0
        self._selectedList = shapeList
        for shape in shapeList:
            shape.isSelected = 1
        self._drawContext.selectShapes(shapeList)

    def appendSelection(self, shapeList):
        for shape in shapeList:
            shape.isSelected = 1
            self._selectedList.append(shape)
        self._drawContext.selectShapes(self._selectedList)

    #
    #  Scaling related
    #
    def updateScale(self, d2lscale):
        self._device2logical = d2lscale
        if self._viewport:
            self._viewport.updateScale(d2lscale)
        self._parent.showScale(d2lscale)
        self.updateCanvasSize()
        self.InvalidateRect(self.GetClientRect())

    # override the base method to set the canvas size according to the showed viewport size
    def updateCanvasSize(self):
        if self._viewport is not None:
            wingeom = self._viewport._attrdict.get('wingeom')
            if wingeom is not None:
                x, y, w, h = wingeom
                # fix the canvas size 30% bigger than the viewport
                self._canvas = 0, 0, int((w*1.3)/self._device2logical+0.5), int((h*1.3)/self._device2logical+0.5)
                self.SetScrollSizes(win32con.MM_TEXT,self._canvas[2:])

    def getDeviceToLogicalScale(self):
        return self._device2logical

    def findDeviceToLogicalScale(self, wl, hl):
        wd, hd = self.GetClientRect()[2:]
        md = 32 # device margin
        xsc = wl/float(wd-md)
        ysc = hl/float(hd-md)
        if xsc>ysc: sc = xsc
        else: sc = ysc
        if sc<1.0: sc = 1
        return sc

    #  OnRButtonDown popup menu
    def OnRButtonDown(self, params):
        # simulate a left click to select the object
        self.onLButtonDown(params)
        self.onLButtonUp(params)

        msg = win32mu.Win32Msg(params)
        point = msg.pos()
        flags = msg._wParam
        point = self.ClientToScreen(point)
        flags = win32con.TPM_LEFTALIGN | win32con.TPM_RIGHTBUTTON | win32con.TPM_LEFTBUTTON

        if self._popup:
            # xxx to improve
            self._popup.TrackPopupMenu(point, flags, self.GetParent().GetParent().GetParent().GetMDIFrame())

    #
    #  popup menu
    #
    def setpopup(self, menutemplate):
        if self._popup:
            self._popup.DestroyMenu()
            self._popup = None
        if menutemplate != None:
            import win32menu
            popup = win32menu.Menu('popup')
            popup.create_popup_from_menubar_spec_list(menutemplate, usercmd2id)
            self._popup = popup
        else:
            self._popup = None

    #
    #  Painting
    #

    # win32window context update callback
    # rc is in win32window coordinates (N)
    def update(self, rc=None):
        if rc:
            x, y, w, h = rc
            rc = x, y, x+w, y+h
            # convert N (natural) coordinates to D (device)
            rc = self.NRtoDR(rc)
        try:
            self.InvalidateRect(rc or self.GetClientRect())
        except:
            # os window not alive
            pass


    # called by base class OnDraw or OnPaint
    def paintOn(self, dc):
        # fill background
        lc, tc, rc, bc = dc.GetClipBox()
        dc.FillSolidRect((lc, tc, rc, bc), win32mu.RGB(self._bgcolor or (255,255,255)))

        # draw objects on dc
        if self._viewport:
            self._viewport._draw3drect(dc, self._hasfocus)
            if HIDE_TOPSIBLING:
                self._viewport.computeExcludeRegion()
            self._viewport.paintContentOn(dc)
            self._viewport.paintBorderOn(dc, clipRgn=[])
            self.paintTrakersOn(dc)

    def paintTrakersOn(self, dc):
        for shape in self._drawContext._selections:
            shape.paintTrakersOn(dc)

    def hilight(self, f):
        self._hasfocus = f
        self.InvalidateRect(self.GetClientRect())

    def OnSetFocus(self, params):
        self._parent.OnSetPaneFocus()

# for now manage only on listener in the same time
# it should be enough
class UserEventMng:
    def __init__(self):
        self.listener = None

    def setListener(self, listener):
        self.listener = listener

    def removeListener(self, listener):
        self.listener = None

    def onProperties(self):
        self.listener.onProperties()

###########################

def intersect(rect1, rect2):
    rgn1 = win32ui.CreateRgn()
    rgn1.CreateRectRgn(rect1)
    rgn2 = win32ui.CreateRgn()
    rgn2.CreateRectRgn(rect2)
    rgn2.CombineRgn(rgn1,rgn2,win32con.RGN_AND)
    type, newRect = rgn2.GetRgnBox()
    rgn1.DeleteObject()
    rgn2.DeleteObject()
    return newRect

class Shape:
    def __init__(self, context):
        self._ctx = context
        self._relatedShape = None
        self._isTransparent = 1
        self._exclRgn  = []
        self._exclMediaRgn  = []
        self._mediadisplayrect = None
        self._parent = None

    def computeExcludeRegion(self, exclRgnTop=[]):
        self._exclRgn = exclRgnTop

        # XXX note: it would be probably more efficient to create a 'real' Windows region to
        # manage clipping. Unfortunaltly it doesn't work very well during painting (the UI is refreshed correctly only when
        # you release the mouse button) for a raison I don't know.

        exclRgnChildSum = []
        for child in self._subwindows:
            exclRgn = child.computeExcludeRegion(exclRgnTop+exclRgnChildSum)
            exclRgnChildSum = exclRgnChildSum+exclRgn

        sx, sy, sw, sh = self.LRtoDR(self.getwindowpos(), round=1)
        geom = (sx, sy, sx+sw, sy+sh)
        if not self._transparent:
            # the clipping area is the entire region
            return [geom]

        exclRgnRet = []
        if self._mediadisplayrect is not None:
            bx, by, bw, bh = self.LRtoDR(self.getwindowpos(), round=1)
            sx, sy, sw, sh = self.LRtoDR(self._mediadisplayrect, round=1)
            mediaGeom = (sx+bx, sy+by, sx+bx+sw, sy+by+sh)
            exclRgnRet.append(intersect(mediaGeom, geom))

        for childGeom in exclRgnChildSum:
            exclRgnRet.append(intersect(childGeom, geom))

        return exclRgnRet

    # method responsible to paint borders
    # that method paint first hidden borders, then visible borders
    def paintBorderOn(self, dc, rc=None, clipRgn=[], exclRgn=[]):
        self._isSelected = 0
        # XXX to optimize
        for shape in self._ctx._drawContext._selections:
            if shape is self:
                self._isSelected = 1
                break

        # XXX note: it would be probably more efficient to create a 'real' Windows region to
        # manage clipping. Unfortunaltly it doesn't work very well during painting (the UI is refreshed correctly only when
        # you release the mouse button) for a raison I don't know.
        newClipRgn = clipRgn[:]
        newClipRgn.append(self.getClipRect())

        newExclRgn = exclRgn[:]

        hsave = dc.SaveDC()
        self.paintHiddenBorderOn(dc, rc)
        dc.RestoreDC(hsave)

        hsave = dc.SaveDC()
        for rect in newClipRgn:
            dc.IntersectClipRect(rect)
        if HIDE_TOPSIBLING:
            for rect in self._exclRgn:
                dc.ExcludeClipRect(rect)
        self.paintVisibleBorderOn(dc, rc)
        dc.RestoreDC(hsave)

        for w in self._polyList:
            w.paintBorderOn(dc, None, newClipRgn, newExclRgn)

        L = self._subwindows[:]
        L.reverse()
        length = len(L)
        for index in range(length):
            L[index].paintBorderOn(dc, rc, newClipRgn, newExclRgn)

    # that method may be overrided. Just define it here for readibility issue
    def paintVisibleBorderOn(self, dc, rc=None):
        pass

    # that method may be overrided. Just define it here for readibility issue
    def paintHiddenBorderOn(self, dc, rc=None):
        pass

    # that method may be overrided. Just define it here for readibility issue
    def getClipRect(self):
        return (0, 0, 0, 0)

    def isTransparent(self, transparent, bgcolor):
        if transparent == None:
            if bgcolor != None:
                return 0
            else:
                return 1

        return transparent

class RectShape(win32window.Window, Shape, UserEventMng):
    def __init__(self, name, context, attrdict):
        self._attrdict = attrdict
        self._name = name
        self._polyList = []
        self.isSelected = 0
        self._showname = 0
        Shape.__init__(self, context)
        win32window.Window.__init__(self)
        UserEventMng.__init__(self)

    # add a sub region
    def addRegion(self, attrdict, name):
        rgn = Region(self, name, self._ctx, attrdict, self._device2logical)
        return rgn

    def addPolyline(self, pointList, relatedShape):
        poly = Polyline(self, self._ctx, self._device2logical, pointList)
        self._polyList.append(poly)
        if relatedShape is not None:
            relatedShape._relatedShape = poly
        poly._relatedShape = relatedShape
        return poly

    def destroy(self):
        if self._parent is not None:
            psubwindows = self._parent._subwindows
            # remove the link with the parent
            for ind in range(len(psubwindows)):
                if psubwindows[ind] is self:
                    del psubwindows[ind]
                    break
            self._parent = None

        # update the selection
        selectChanged = 0
        for ind in range(len(self._ctx._selectedList)):
            if self._ctx._selectedList[ind] is self:
                del self._ctx._selectedList[ind]
                selectChanged = 1
                break
        if selectChanged:
            self._ctx._drawContext.selectShapes(self._ctx._selectedList)

        self.close()

    # shape content. may be replaced by displaylist ???
    def showName(self, bv):
        self._showname = bv
        self._ctx.update()

    # overide the default newdisplaylist method defined in win32window
    def newdisplaylist(self, bgcolor = None):
        if bgcolor is None:
            if not self._transparent:
                bgcolor = self._bgcolor
        return win32window._ResizeableDisplayList(self, bgcolor)

    def initDisplayList(self):
        # disp list of this window
        # use shortcut instead of render
        self._active_displist = self.newdisplaylist()

    def hasmedia(self):
        displist = self._active_displist
        if displist:
            for entry in displist._list:
                if entry[0] == 'image':
                    return 1
        return 0

    def setImage(self, filename, fit, mediadisplayrect = None):
        self._mediadisplayrect = mediadisplayrect
        if self._active_displist != None:
            self._active_displist.newimage(filename, fit, mediadisplayrect)

    def updateImage(self, fit, mediadisplayrect = None):
        if self._active_displist != None:
            self._active_displist.updateimage(fit, mediadisplayrect)

    def drawbox(self, box):
        self._active_displist.drawbox(box, units=UNIT_PXL)

    def close(self):
        if self._active_displist:
            self._active_displist.close()

    def insideCaption(self, point):
        return 0

    def getMouseTarget(self, point):
        for w in self._polyList:
            target = w.getMouseTarget(point)
            if target:
                return target
        for w in self._subwindows:
            target = w.getMouseTarget(point)
            if target:
                return target
        if self.inside(point) or self.insideCaption(point):
            return self
        return None

    def updateScale(self, d2lscale):
        win32window.Window.setDeviceToLogicalScale(self, d2lscale)

        for w in self._subwindows:
            w.updateScale(d2lscale)
        for w in self._polyList:
            w.updateScale(d2lscale)

    def paintContentOn(self, dc, rc=None):
        x, y, w, h = self.LRtoDR(self.getwindowpos(), round=1)
        ltrb = l, t, r, b = x, y, x+w, y+h

        hsave = dc.SaveDC()
        dc.IntersectClipRect(ltrb)

        x0, y0 = dc.SetWindowOrg((-l,-t))
        if self._active_displist:
            self._active_displist._render(dc, rc)
        dc.SetWindowOrg((x0,y0))

        L = self._subwindows[:]
        L.reverse()
        for w in L:
            w.paintContentOn(dc, rc)

        dc.RestoreDC(hsave)

    # that method may be overrided. Just define it here for readibility issue
    def getClipRect(self):
        x, y, w, h = self.LRtoDR(self.getwindowpos(), round=1)
        return (x, y, x+w, y+h)

    # method responsible to paint border when visible state
    # in that case: the clipping region is correctly defined for the dc in parameter.
    # Note that the clipping region is set from Shape.painBorderOn method and may be complex
    def paintVisibleBorderOn(self, dc, rc=None):
        if self._isSelected:
            oldpen = dc.SelectObjectFromHandle(self._ctx._selectedPen)
        else:
            oldpen = dc.SelectObjectFromHandle(self._ctx._blackBrush)

        x, y, w, h = self.LRtoDR(self.getwindowpos(), round=1)
        l, t, r, b = x, y, x+w-1, y+h-1

        win32mu.DrawRectanglePath(dc, (l, t, r, b))
        dc.SelectObjectFromHandle(oldpen)

    # method responsible to paint border when hidden state
    # in that case: the clipping region is correctly defined for the dc in parameter
    # Note that the clipping region is set from Shape.painBorderOn method and may be complex
    def paintHiddenBorderOn(self, dc, rc=None):
        if self._isSelected:
            oldpen = dc.SelectObjectFromHandle(self._ctx._hiddenSelectedPen)
        else:
            oldpen = dc.SelectObjectFromHandle(self._ctx._hiddenPen)

        x, y, w, h = self.LRtoDR(self.getwindowpos(), round=1)
        l, t, r, b = x, y, x+w-1, y+h-1

        win32mu.DrawRectanglePath(dc, (l, t, r, b))
        dc.SelectObjectFromHandle(oldpen)

    def paintTrakersOn(self, dc):
        hsave = dc.SaveDC()
        nHandles = self.getDragHandleCount()
        for ix in range(nHandles):
            x, y, w, h = self.getDragHandleRect(ix)
            dc.FillSolidRect((x, y, x+w, y+h), win32api.RGB(255,127,80))
            dc.FrameRectFromHandle((x, y, x+w, y+h), self._ctx._blackBrush)
        dc.RestoreDC(hsave)

class Viewport(RectShape):
    def __init__(self, name, context, attrdict, d2lscale):
        RectShape.__init__(self, name, context, attrdict)
        self._uidx, self._uidy = 8, 8

        self._cycaption = 0 #win32api.GetSystemMetrics(win32con.SM_CYCAPTION)
        self._cycaptionlog = 0 # int(self._device2logical*self._cycaption+0.5)

        x, y, w, h = attrdict.get('wingeom')
        units = attrdict.get('units')
        z = 0
        transparent = attrdict.get('transparent')
        bgcolor = attrdict.get('bgcolor')

        self._isTransparent = self.isTransparent(transparent, bgcolor)

        self.create(None, (self._uidx, self._uidy, w, h), units, z, self._isTransparent, bgcolor)
        self.setDeviceToLogicalScale(d2lscale)

        # adjust some variables
        self._topwindow = self

        self.initDisplayList()

        self.center()

    def destroy(self):
        RectShape.destroy(self)
        self._topwindow = None

    def center(self):
        x, y, w, h = self._rectb
        layout = self._ctx
        vw, vh = layout.GetClientRect()[2:]
        vw, vh = self.DPtoLP((vw, vh))
        x = (vw - w)/2
        y = (vh - h)/2
        if x<8: x=8
        if y<8: y=8
        self._rectb = x, y, w, h

    #
    # interface implementation: function called from an external module
    #

    # return the current geometry
    def getGeom(self):
        x, y, w, h = self._rectb
        if w<1: w=1
        if h<1: h=1
        self._rectb = x,y,w,h
        return 0, 0, int(w+0.5), int(h+0.5)

    def setAttrdict(self, attrdict):
        # print 'setAttrdict', attrdict
        newBgcolor = attrdict.get('bgcolor')
        oldBgcolor = self._attrdict.get('bgcolor')
        newGeom = attrdict.get('wingeom')
        oldGeom = self._attrdict.get('wingeom')
        self._attrdict = attrdict

        self._isTransparent = self.isTransparent(None, newBgcolor)

        if oldGeom != newGeom:
            self.updatecoordinates(newGeom, units=UNIT_PXL)
            self._ctx.updateCanvasSize()
        if newBgcolor != oldBgcolor:
            if newBgcolor != None:
                self.updatebgcolor(newBgcolor)

        self._ctx.update()

    #
    #  end interface implementation
    #

    def getwindowpos(self, rel=None):
        x, y, w, h = self._rectb
        return int(x+0.5), int(y+0.5), int(w+0.5), int(h+0.5)

    def update(self, rc=None):
        self._ctx.update(rc)

    def pop(self, poptop=1):
        pass

    def updateScale(self, d2lscale):
        RectShape.updateScale(self, d2lscale)
        self.center()

    def insideCaption(self, point):
        x, y, w, h = self.getwindowpos()
        l, t, r, b = x, y-self._cycaptionlog, x+w, y
        xp, yp = point
        if xp>=l and xp<r and yp>=t and yp<b:
            return 1
        return 0

    def _draw3drect(self, dc, hilight=0):
        hsave = dc.SaveDC()
        x, y, w, h = self.LRtoDR(self.getwindowpos(), round=1)
        l, t, r, b = x, y-self._cycaption, x+w, y+h
        l, t, r, b = l-3, t-3, r+2, b+2
        c1, c2 = 180, 100
        if hilight:
            c1, c2 = 220, 150
        for i in range(3):
            if hilight:
                dc.Draw3dRect((l,t,r,b),win32api.RGB(c1, c1, 0), win32api.RGB(c2, c2, 0))
            else:
                dc.Draw3dRect((l,t,r,b),win32api.RGB(c1, c1, c1), win32api.RGB(c2, c2, c2))
            c1, c2 = c1-15, c2-15
            l, t, r, b = l+1, t+1, r-1, b-1
        dc.RestoreDC(hsave)

    def _drawcaption(self, dc):
        x, y, w, h = self.LRtoDR(self.getwindowpos(), round=1)
        l, t, r, b = x, y, x+w, y+h
        dc.FillSolidRect((l,t-self._cycaption,r, t) ,win32mu.RGB((128, 128, 255)))
        dc.SetBkMode(win32con.TRANSPARENT)
        dc.SetTextAlign(win32con.TA_BOTTOM)
        clr_org=dc.SetTextColor(win32api.RGB(255,255,255))
        dc.TextOut(l+4,t-2,self._name)
        dc.SetTextColor(clr_org)


###########################

class Region(RectShape):
    def __init__(self, parent, name, context, attrdict, d2lscale):
        RectShape.__init__(self, name, context, attrdict)

        self._parent = parent
        x, y, w, h = attrdict.get('wingeom')
        units = attrdict.get('units')
        z = attrdict.get('z')
        transparent = attrdict.get('transparent')
        bgcolor = attrdict.get('bgcolor')

        self._isTransparent = self.isTransparent(transparent, bgcolor)
        self.create(parent, (x, y, w, h), units, z, self._isTransparent, bgcolor)
        self.setDeviceToLogicalScale(d2lscale)

        self.initDisplayList()

        # allow to determinate if the region is moving
        self._isMoving = 0

        # allow to determinate if the region is resizing
        self._isResizing = 0

    #
    # interface implementation: function called from an external module
    #

    # return the current geometry
    def getGeom(self):
        x, y, w, h = self._rectb
        if w<1: w=1
        if h<1: h=1
        self._rectb = x,y,w,h
        if x < 0: x = x-0.5
        else: x = x+0.5
        if y < 0: y = y-0.5
        else: y = y+0.5
        return int(x), int(y), int(w+0.5), int(h+0.5)

    def setAttrdict(self, attrdict):
        newBgcolor = attrdict.get('bgcolor')
        oldBgcolor = self._attrdict.get('bgcolor')
        newGeom = attrdict.get('wingeom')
        oldGeom = self._attrdict.get('wingeom')
        newZ = attrdict.get('z')
        oldZ = self._attrdict.get('z')
        self._attrdict = attrdict
        transparent = attrdict.get('transparent')

        self._isTransparent = self.isTransparent(transparent, newBgcolor)

        if oldGeom != newGeom:
            self.updatecoordinates(newGeom, units=UNIT_PXL)
        if newBgcolor != oldBgcolor:
            if newBgcolor != None:
                self.updatebgcolor(newBgcolor)
        if newZ != oldZ:
            self.updatezindex(newZ)

        self._ctx.update()

class Polyline(winlayout.Polyline, Shape, UserEventMng):
    def __init__(self, parent, context, d2lscale, pointList):
        self._ctx = context
        self.isSelected = 0
        self._polyList = []
        self._subwindows = []
        self._name = 'poly'

        Shape.__init__(self, context)
        self._parent = parent
        winlayout.Polyline.__init__(self, self._parent, pointList)
        UserEventMng.__init__(self)
        self.setDeviceToLogicalScale(d2lscale)

    # remove a polyline
    def destroy(self):
        # update the selection
        selectChanged = 0
        for ind in range(len(self._ctx._selectedList)):
            if self._ctx._selectedList[ind] is self:
                del self._ctx._selectedList[ind]
                selectChanged = 1
                break
        if selectChanged:
            self._ctx._drawContext.selectShapes(self._ctx._selectedList)

        # remove the links
        if self._parent:
            polyList = self._parent._polyList
            for ind in range(len(polyList)):
                if polyList[ind] is self:
                    del polyList[ind]
                    break
            self._parent = None

        if self._relatedShape is not None:
            self._relatedShape._relatedShape = None
            self._relatedShape = None

    def updateScale(self, d2lscale):
        self.setDeviceToLogicalScale(d2lscale)

    # that method may be overrided. Just define it here for readibility issue
    def getClipRect(self):
        x, y, w, h = self.LRtoDR(self._parent.getwindowpos(), round=1)
        return (x, y, x+w, y+h)

    # that method may be overrided. Just define it here for readibility issue
    def paintVisibleBorderOn(self, dc, rc=None):
        if self._isSelected:
            oldpen = dc.SelectObjectFromHandle(self._ctx._selectedPathPen)
        else:
            oldpen = dc.SelectObjectFromHandle(self._ctx._pathPen)
        points = self.getDevicePoints()
        dc.Polyline(points)

        self.__paintPoints(dc)

    # that method may be overrided. Just define it here for readibility issue
    def paintHiddenBorderOn(self, dc, rc=None):
        if self._isSelected:
            oldpen = dc.SelectObjectFromHandle(self._ctx._hiddenSelectedPathPen)
        else:
            oldpen = dc.SelectObjectFromHandle(self._ctx._hiddenPathPen)
        points = self.getDevicePoints()
        dc.Polyline(points)

        self.__paintPoints(dc)

    def __paintPoints(self, dc):
        hsave = dc.SaveDC()
        nHandles = self.getDragHandleCount()
        dc.SelectObjectFromHandle(self._ctx._blackBrush)
        dc.SelectObjectFromHandle(self._ctx._blackPen)
        for ix in range(1,nHandles+1):
            x, y, w, h = self.getDragHandleRect(ix)
            dc.Ellipse((x+1, y+1, x+6, y+6))
        dc.RestoreDC(hsave)

    def paintTrakersOn(self, dc):
        hsave = dc.SaveDC()
        nHandles = self.getDragHandleCount()
        dc.SelectObject(self._ctx._handlePathBrush)
        for ix in range(1,nHandles+1):
            x, y, w, h = self.getDragHandleRect(ix)
            dc.FillSolidRect((x, y, x+w, y+h), win32api.RGB(0,0,0))
            dc.FrameRectFromHandle((x, y, x+w, y+h), self._ctx._blackBrush)
        dc.RestoreDC(hsave)

    def getMouseTarget(self, point):
        if self.inside(point):
            return self
        return None

    # return the current geometry
    def getGeom(self):
        pList = []
        pointList = self.getDevicePoints()
        px, py, pw, ph = self.LRtoDR(self._parent.getwindowpos(), round=1)
        for x,y in pointList:
            x,y = self.DPtoLP((x-px,y-py))
            pList.append((int(x+0.5),int(y+0.5)))
        return pList
