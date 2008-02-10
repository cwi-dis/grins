__version__ = "$Id$"

import win32ui, win32api
Sdk = win32ui.GetWin32Sdk()

import win32con
import commctrl
import appcon

from win32mu import Win32Msg
import DropTarget
import IconMixin

from pywinlib.mfc import window
SHIFTBIT = 4096 # the image index for state icon is set in the bits 12-15

debug = 0

EVENT_SRC_LButtonDown, EVENT_SRC_Expanded, EVENT_SRC_KeyDown = range(3)

import MenuTemplate

class TreeCtrl(window.Wnd, IconMixin.CtrlMixin):
##     dropMap = {'Region': DropTarget.CF_REGION,
##         'Media': DropTarget.CF_MEDIA,
##         'FileName': DropTarget.CF_FILE,}

    def __init__ (self, dlg=None, resId=None, ctrl=None, stateOption=0):
        # if the tree res is specified from a dialox box, we just create get the existing instance
        # if try to re-create it, the focus doesn't work, and you get some very unexpected behavior
        self.parent = dlg
        self._stateOption = stateOption
        if not ctrl:
            if resId != None:
                ctrl = dlg.GetDlgItem(resId)
            else:
                ctrl = win32ui.CreateTreeCtrl()
        else:
            ctrl.SetWindowLong(win32con.GWL_STYLE,self.getStyle())

        window.Wnd.__init__(self, ctrl)
        self._selections = []
        self._multiSelListeners = []
        self._expandListeners = []
        self._dragdropListener = []
        self._stateListeners = []
        self._selEventSource = None

        self.__selecting = 0
        self.__deleting = 0
        if resId != None:
            self._setEvents()

        self._popup = None

        # register as a drop target
        self.RegisterDropTarget()

        self.__lastDragOverItem = None
        self.__selectedItem = None

    def getStyle(self):
        style = win32con.WS_VISIBLE | win32con.WS_CHILD | commctrl.TVS_HASBUTTONS |\
                        commctrl.TVS_HASLINES | commctrl.TVS_SHOWSELALWAYS |\
                        win32con.WS_BORDER | win32con.WS_TABSTOP\
                         | commctrl.TVS_LINESATROOT
        return style

    # create a new instance of the tree ctrl.
    # Note: don't call this method, if the tree widget come from a dialog box
    def create(self, parent, rc, id):
        self.parent = parent
        self.CreateWindow(self.getStyle(), rc, parent, id)
        self._setEvents()

    # set the events that we manage in the tree widget
    def _setEvents(self):
        self.HookMessage(self.OnLButtonDown, win32con.WM_LBUTTONDOWN)
        self.HookMessage(self.OnLButtonUp, win32con.WM_LBUTTONUP)
        #self.HookMessage(self.OnMouseMove, win32con.WM_MOUSEMOVE)
        self.HookMessage(self.OnKeyDown, win32con.WM_KEYDOWN)
        self.GetParent().HookNotify(self.OnSelChanged, commctrl.TVN_SELCHANGED)
        self.GetParent().HookNotify(self.OnExpanded,commctrl.TVN_ITEMEXPANDED)
        self.HookMessage(self.OnKillFocus,win32con.WM_KILLFOCUS)
        self.HookMessage(self.OnSetFocus,win32con.WM_SETFOCUS)

        self.GetParent().HookNotify(self.OnBeginDrag, commctrl.TVN_BEGINDRAG)

        # debug
        self.HookMessage(self.OnDump, win32con.WM_USER+1)

        # popup menu
        self.HookMessage(self.OnRButtonDown, win32con.WM_RBUTTONDOWN)
        self.GetParent().HookMessage(self.OnCommand,win32con.WM_COMMAND)

    # simulate dialog tab
    def OnKeyDown(self, params):
        key = params[2]

        if key == win32con.VK_TAB:
            self.parent.OnChangeTreeFocus()
            return 0
        elif key == win32con.VK_DELETE:
            if hasattr(self.parent, 'OnDelete'):
                self.parent.OnDelete()
        elif (win32api.GetKeyState(win32con.VK_SHIFT) & 0x8000) and key == win32con.VK_DOWN:
            if len(self._selections) <= 0:
                return
            lastSel = self._selections[-1]
            try:
                item = self.GetNextItem(lastSel, commctrl.TVGN_NEXTVISIBLE)
            except:
                return
            self._ShiftMultiSelect(item)
        elif (win32api.GetKeyState(win32con.VK_SHIFT) & 0x8000) and key == win32con.VK_UP:
            if len(self._selections) <= 0:
                return
            lastSel = self._selections[-1]
            try:
                item = self.GetNextItem(lastSel, commctrl.TVGN_PREVIOUSVISIBLE)
            except:
                return
            self._ShiftMultiSelect(item)
        else:
            self._selEventSource = EVENT_SRC_KeyDown
            return 1

    # create a dlg control replacing a placeholder
    def createAsDlgItem(self, dlg, id):
        wnd = dlg.GetDlgItem(id)
        rc = wnd.GetWindowRect()
        wnd.DestroyWindow()
        rc = dlg.ScreenToClient(rc)
        self.create(dlg, rc, id)

    def __setSingleSelect(self, hititem):
        for item in self._selections:
            if item != hititem:
                try:
                    self.SetItemState(item, 0, commctrl.TVIS_SELECTED)
                except:
                    # the item may already be removed
                    pass

        self._selections = [hititem]
        self.SetItemState(hititem, commctrl.TVIS_SELECTED, commctrl.TVIS_SELECTED)
        self.OnMultiSelChanged()

    #
    # handler methods for the standard windows events
    #

    def OnLButtonDown(self, params):
        msg = Win32Msg(params)
        point = msg.pos()
        flags = msg._wParam

        self._selEventSource = EVENT_SRC_LButtonDown

        hitflags, hititem = self.HitTest(point)
        # some informations about hitflags:
        # a item consists of different parts. The most important are:
        # - the button (the icon on the left which allows to expand/collapse a node)
        # - the state icon (the check box if the global option check box is activated, or a user defined state icon)
        # - the icon (the main icon)
        # - the label (the text on the right of the main icon
        # for each of these part, there is a defined mask specified in hiflags (in the same order):
        # TVHT_ONITEMBUTTON, TVHT_ONITEMSTATEICON, TVHT_ONITEMICON, TVHT_ONITEMLABEL
        # in addition, TVHT_ONITEM consists of three masks (three parts):
        # TVHT_ONITEM = TVHT_ONITEMSTATEICON, TVHT_ONITEMICON, TVHT_ONITEMLABEL
        if not (hitflags & commctrl.TVHT_ONITEM):
            if debug: self.scheduleDump()
            return 1
        if self._stateOption and hitflags & commctrl.TVHT_ONITEMSTATEICON:
            # special treatment if the user click on the state icon
            # don't leave the system automaticly handles this event. it doesn't do exactly the right things:
            # it selects as well the item, and we don't want that
            self.onStateIconClick(hititem)
            return 0

        if not (flags & win32con.MK_CONTROL) and not (flags & win32con.MK_SHIFT):
            # remove multi-select mode
#                       nsel = len(self._selections)
            self.__setSingleSelect(hititem)

            # do a normal selection/deselection
            return 1

        # enter multi-select mode

        # if the focus is not set, set it.
        self.SetFocus()

        if (flags & win32con.MK_SHIFT):
            self._ShiftMultiSelect(hititem)
        elif (flags & win32con.MK_CONTROL):
            self._CtrlMultiSelect(hititem)

        # absorb event
        return 0

    # do a shift multi select
    def _ShiftMultiSelect(self, hititem):
        # don't update the listener when selecting
        self.__selecting = 1

        hitItemIsBefore = 0
        # find out the first selected item
        try:
            firstSelectedItem = self.GetNextItem(0, commctrl.TVGN_ROOT)
        except:
            firstSelectedItem = None
        while firstSelectedItem and not firstSelectedItem in self._selections:
            try:
                if firstSelectedItem == hititem:
                    hitItemIsBefore = 1
                    break
                firstSelectedItem = self.GetNextVisibleItem(firstSelectedItem)
            except:
                break

        # find out the last selected item
        if firstSelectedItem and not hitItemIsBefore:
            lastSelectedItem = hititem
        elif firstSelectedItem and hitItemIsBefore:
            if not hititem in self._selections:
                count = 0
            else:
                count = 1
            lastSelectedItem = hititem
            while 1:
                if lastSelectedItem in self._selections:
                    count = count + 1
                if count >= len(self._selections):
                    break
                try:
                    lastSelectedItem = self.GetNextVisibleItem(lastSelectedItem)
                except:
                    # fail. Shouldn't happen
                    break
            # selecting
        if firstSelectedItem and lastSelectedItem:
            self.SelectItem(hititem)
            self.SetItemState(hititem, commctrl.TVIS_SELECTED, commctrl.TVIS_SELECTED)
            # select the rest until the last item selected
            curItem = firstSelectedItem
            while curItem != None:
                if curItem != hititem:
                    self.SetItemState(curItem, commctrl.TVIS_SELECTED, commctrl.TVIS_SELECTED)
                    if not curItem in self._selections:
                        self.appendSelection(curItem)
                if curItem == lastSelectedItem:
                    break
                curItem = self.GetNextVisibleItem(curItem)
                # select the last item normally hit item the same way base would do

            if hititem in self._selections:
                self.removeSelection(hititem)
            self.appendSelection(hititem)

        # un-selecting
        if lastSelectedItem and not hitItemIsBefore:
            try:
                curItem = self.GetNextVisibleItem(lastSelectedItem)
                while curItem != None:
                    if curItem in self._selections:
                        # unselect
                        self.SetItemState(curItem, 0, commctrl.TVIS_SELECTED)
                        self.removeSelection(curItem)
                    curItem = self.GetNextVisibleItem(curItem)
            except:
                # end
                pass

        # don't update the listener when selecting
        self.__selecting = 0
        # update the listener
        self.OnMultiSelChanged()

    # do a ctrl multi select
    def _CtrlMultiSelect(self, hititem):
        self.__selecting = 1
        # selected item on entry
        try:
            selitem = self.GetSelectedItem()
            if selitem:
                selstate = self.GetItemState(selitem, commctrl.TVIS_SELECTED)
        except:
            selitem = None
        nsel = len(self._selections)
            # select/deselect normally hit item the same way base would do
        hitstate = self.GetItemState(hititem, commctrl.TVIS_SELECTED)
        if hitstate & commctrl.TVIS_SELECTED:
            self.SetItemState(hititem, 0, commctrl.TVIS_SELECTED)
            self.removeSelection(hititem)
            # update the listener
            updateFl = 0
        else:
            self.SelectItem(hititem)
            self.SetItemState(hititem, commctrl.TVIS_SELECTED, commctrl.TVIS_SELECTED)
            self.appendSelection(hititem)
            # update the listener
            updateFl = 1

        # restore selection of previously selected item once not the hit item
        if nsel > 0:
            if selitem and selitem!=hititem and (selstate & commctrl.TVIS_SELECTED):
                self.SetItemState(selitem, commctrl.TVIS_SELECTED, commctrl.TVIS_SELECTED)
        self.__selecting = 0
        self.OnMultiSelUpdated(hititem, updateFl)

    def onStateIconClick(self, hititem):
        currentState = self.getState(hititem)

        # update the listeners
        for listener in self._stateListeners:
            listener.OnStateActivated(hititem, currentState)

    def getState(self, item):
        imageIndex = (self.GetItemState(item, commctrl.TVIS_STATEIMAGEMASK) & commctrl.TVIS_STATEIMAGEMASK) / SHIFTBIT
        return imageIndex

    def setState(self, item, state):
        self.SetItemState(item, SHIFTBIT*state , commctrl.TVIS_STATEIMAGEMASK)

    def OnLButtonUp(self, params):
        return 1

    #
    #  drag and drop support methods
    #

    def OnBeginDrag(self, std, extra):
        selectedItems = self.getSelectedItems()
        if len(selectedItems) != 1:
            # for now, support only single drag and drop
            return

        item = selectedItems[0]
        self.__toDragDropState(item)
        self.__lastDragOverItem = item

        if self._dragdropListener:
            self._dragdropListener.OnBeginDrag(item)

    def OnDragOver(self, dataobj, kbdstate, x, y):
        pt = win32api.GetCursorPos()
        pt = self.ScreenToClient(pt)

        #
        # Scroll Tree control depending on mouse position
        #

        RECT_BORDER = 10
        def MAKELONG(l,h): return int((l & 0xFFFF) | ((h << 16) & 0xFFFF0000))

        rc = self.GetClientRect()
        rcLeft, rcTop, rcRight, rcBottom = self.ClientToScreen(rc)
        ptX, ptY = self.ClientToScreen(pt)

        # vertical scroll
        nScrollDir = -1
        if ptY >= rcBottom - RECT_BORDER:
            nScrollDir = win32con.SB_LINEDOWN
        elif ptY <= (rcTop + RECT_BORDER):
            nScrollDir = win32con.SB_LINEUP

        if nScrollDir != -1:
            nScrollPos = self.GetScrollPos(win32con.SB_VERT)
            wParam = MAKELONG(nScrollDir, nScrollPos)
            Sdk.SendMessage(self.GetSafeHwnd(),win32con.WM_VSCROLL,wParam,0)

        # horizontal scroll
        nScrollDir = -1
        if ptX >= rcRight - RECT_BORDER:
            nScrollDir = win32con.SB_LINERIGHT
        elif ptX <= (rcLeft + RECT_BORDER):
            nScrollDir = win32con.SB_LINELEFT

        if nScrollDir != -1:
            nScrollPos = self.GetScrollPos(win32con.SB_HORZ)
            wParam = MAKELONG(nScrollDir, nScrollPos)
            Sdk.SendMessage(self.GetSafeHwnd(),win32con.WM_HSCROLL,wParam,0)

        #
        #
        #

        ret = appcon.DROPEFFECT_NONE
        if self.__lastDragOverItem != None:
            self.SetItemState(self.__lastDragOverItem, 0, commctrl.TVIS_SELECTED)
            self.__lastDragOverItem = None

        flags, item = self.HitTest(pt)
        if self._dragdropListener:
            flavor, data = DropTarget.DecodeDragData(dataobj)
            if flavor and data:
                ret = self._dragdropListener.OnDragOver(item, flavor, data)
                if ret != appcon.DROPEFFECT_NONE:
                    if item:
                        self.SetItemState(item, commctrl.TVIS_SELECTED, commctrl.TVIS_SELECTED)
                        self.__lastDragOverItem = item
                    else:
                        self.__lastDragOverItem = None

        return ret

    def OnDragEnter(self, dataobj, kbdstate, x, y):
        selectedItems = self.getSelectedItems()
        if len(selectedItems) != 1:
            # for now, support only single drag and drop
            return

        item = selectedItems[0]
        self.__toDragDropState(item)
        return self.OnDragOver(dataobj, kbdstate, x, y)

    def OnDrop(self, dataobj, effect, x, y):
        self.__toNormalState()
        pt = win32api.GetCursorPos()
        pt = self.ScreenToClient(pt)
        flags, item = self.HitTest(pt)
        if self._dragdropListener:
            flavor, data = DropTarget.DecodeDragData(dataobj)
            if flavor and data:
                return self._dragdropListener.OnDrop(item, flavor, data)
        return 0

    def OnDragLeave(self):
        self.__toNormalState()

    def __toDragDropState(self, item):
        self.__selectedItem = item
        self.SetItemState(item, 0, commctrl.TVIS_SELECTED)

    def __toNormalState(self):
        if self.__selectedItem != None:
            self.SetItemState(self.__selectedItem, commctrl.TVIS_SELECTED, commctrl.TVIS_SELECTED)
            if self.__lastDragOverItem != None:
                self.SetItemState(self.__lastDragOverItem, 0, commctrl.TVIS_SELECTED)
                self.__lastDragOverItem = None

    # set a drag and drop listener
    def setDragdropListener(self, listener):
        self._dragdropListener = listener

    # remove drag and drop listener
    def removeDragdropListener(self, listener):
        if listener is self._dragdropListener:
            self._dragdropListener = None

    # object id have to be a string
    def beginDrag(self, flavor, args):
        flavorid, str = DropTarget.EncodeDragData(flavor, args)
        if flavorid:
            self.DoDragDrop(flavorid, str)

    #
    #
    #

    def setpopup(self, popup):
        self._popup = popup

    def OnRButtonDown(self, params):
        # simulate a left click to select
        self.OnLButtonDown(params)
        self.OnLButtonUp(params)

        msg = Win32Msg(params)
        point = msg.pos()
        flags = msg._wParam
        point = self.ClientToScreen(point)
        flags = win32con.TPM_LEFTALIGN | win32con.TPM_RIGHTBUTTON | win32con.TPM_LEFTBUTTON

        if self._popup:
            # xxx to improve
            self._popup.TrackPopupMenu(point, flags, self.getLayoutView().GetParent().GetParent().GetMDIFrame())

    def OnDestroy(self, params):
        if self._popup:
            self._popup.DestroyMenu()
            self._popup = None

    def OnExpanded(self, std, extra):
        self._selEventSource = EVENT_SRC_Expanded
        nsel = len(self._selections)
        action, itemOld, itemNew, ptDrag = extra
        # XXX the field number doesn't correspond with API documention ???
        item, field2, field3, field4, field5, field6, field7, field8 = itemNew

        self.__changed = 0
        if action == commctrl.TVE_COLLAPSE:
            # when a node is collapsed, unselect as well all these children which becomes unvisible.
            self.__unselectChildren(item)

            # when you collapse a node, the standard behavior change automaticly
            # the focus on the node wich is collapsed. So, according to the auto selecting
            # we have to update as well the multi-select variable state
            try:
                selitem = self.GetSelectedItem()
                if selitem:
                    # default state
                    oldstate =  selitem in self._selections
                    # new state
                    selstate = self.GetItemState(selitem, commctrl.TVIS_SELECTED)
                    if not oldstate and (selstate & commctrl.TVIS_SELECTED):
                        self.__changed = 1
                        self._selections.append(selitem)
            except:
                pass

        # update the listener
        for listener in self._expandListeners:
            listener.OnExpandChanged(item, action != commctrl.TVE_COLLAPSE)

        # if any changement, update the listeners
        if self.__changed:
            self.OnMultiSelChanged()
        return 1

    def OnSelChanged(self, std, extra):
        if self.__selecting:
            return 0
        nsel = len(self._selections)
        # Important note: these line allow to detect, if there is an auto select (by the system) due to an initial focus
        # in this case, we reset the selection
        if nsel == 0:
            try:
                selitem = self.GetSelectedItem()
                if selitem:
                    selstate = self.GetItemState(selitem, commctrl.TVIS_SELECTED)
            except:
                selitem = None

            if selitem and (selstate & commctrl.TVIS_SELECTED):
                self.SetItemState(selitem, 0, commctrl.TVIS_SELECTED)
            return

        action, itemOld, itemNew, ptDrag = extra
        # XXX the field number doesn't correspond with API documention ???
        item, field2, field3, field4, field5, field6, field7, field8 = itemNew

        if self._selEventSource not in (EVENT_SRC_Expanded, EVENT_SRC_LButtonDown):
            self.__setSingleSelect(item)

        self._selEventSource = None

        if debug:
            self.scheduleDump()

    def OnKillFocus(self, params):
        # update the selected items.
        # Note: the look is not the same when a item is selected or unselected
        self.__updateSelectedItems()

        # continu a normal processing
        return 1

    def OnSetFocus(self, params):

        # update the selected items.
        # Note: the look is not the same when a item is selected or unselected
        self.__updateSelectedItems()

        # continu normal processing
        return 1

    #
    #
    #

    def SelectItemList(self, list):
        if self.__selecting:
            return
        # don't update the listener when selecting
        self.__selecting = 1

        # remove items not selected anymore
        itemToRemove = []
        for cItem in self._selections:
            if cItem not in list:
                itemToRemove.append(cItem)
        for cItem in itemToRemove:
            try:
                self.SetItemState(cItem, 0, commctrl.TVIS_SELECTED)
            except:
                # the node may be already removed
                pass
            self.removeSelection(cItem)

        if len(list) > 0:
            firstItemList = list[:-1]
            lastItem = list[-1]
            # for the last item, select normally item the same way base would do
            self.SelectItem(lastItem)
            self.SetItemState(lastItem, commctrl.TVIS_SELECTED, commctrl.TVIS_SELECTED)

            # for all items except the last, select/deselect with SetItemState
            for item in firstItemList:
                self.SetItemState(item, commctrl.TVIS_SELECTED, commctrl.TVIS_SELECTED)
                self.appendSelection(item)

            self.appendSelection(lastItem)

        self.__selecting = 0

    # change the state icon of a list of items
    def SetStateItemList(self, itemList, state):
        if self._stateOption:
            for item in itemList:
                self.setState(item, state)

    # unselect all children of the item
    def __unselectChildren(self, item):
        try:
            child = self.GetChildItem(item)
        except:
            child = None
        while child != None:
            if child in self._selections:
                self.SetItemState(child, 0, commctrl.TVIS_SELECTED)
                self._selections.remove(child)
                self.__changed = 1
            if child != None:
                self.__unselectChildren(child)
            try:
                child = self.GetNextSiblingItem(child)
            except:
                child = None

    def __updateSelectedItems(self):
        rc = self.GetWindowRect()
        rc = self.GetParent().ScreenToClient(rc)
        self.GetParent().InvalidateRect(rc)

    # update the listener
    def OnMultiSelChanged(self):
        # don't update the listener when selecting
        # avoid some recursive problems
        if self.__selecting or self.__deleting:
            return
        self.__selecting = 1
        for listener in self._multiSelListeners:
            listener.OnMultiSelChanged()
        if debug:
            self.scheduleDump()
        self.__selecting = 0

    # update the listener
    def OnMultiSelUpdated(self, item, state):
        # don't update the listener when selecting
        # avoid some recursive problems
        if self.__selecting:
            return
        self.__selecting = 1
        for listener in self._multiSelListeners:
            listener.OnMultiSelUpdated([item], state)
        if debug:
            self.scheduleDump()
        self.__selecting = 0

    # add an expand listener
    def addExpandListener(self, listener):
        if hasattr(listener, 'OnExpandChanged') and\
                listener not in self._expandListeners:
            self._expandListeners.append(listener)

    # remove an expand listener
    def removeExpandListener(self, listener):
        if listener in self._expandListeners:
            self._expandListeners.remove(listener)

    # add a listener
    def addMultiSelListener(self, listener):
        if hasattr(listener, 'OnMultiSelChanged') and \
                hasattr(listener, 'OnMultiSelUpdated') and \
                listener not in self._multiSelListeners:
            self._multiSelListeners.append(listener)

    # add a listener
    def addStateListener(self, listener):
        if hasattr(listener, 'OnStateActivated'):
            self._stateListeners.append(listener)

    # remove a listener
    def removeStateListener(self, listener):
        if listener in self._stateListeners:
            self._stateListeners.remove(listener)

    # remove a listener
    def removeMultiSelListener(self, listener):
        if listener in self._multiSelListeners:
            self._multiSelListeners.remove(listener)

    def DeleteItem(self, item):
        self.__deleting = 1
        state = self.GetItemState(item, commctrl.TVIS_SELECTED)
        # if this item is already selected, unselect it, and remove from selected list
        if state & commctrl.TVIS_SELECTED:
            self.SetItemState(item, 0, commctrl.TVIS_SELECTED)
        if item in self._selections:
            self._selections.remove(item)

        self._obj_.DeleteItem(item)
        self.__deleting = 0

    def appendSelection(self, item):
        if item not in self._selections:
            self._selections.append(item)

    def removeSelection(self, item):
        if item in self._selections:
            self._selections.remove(item)

    def getSelectedItems(self):
        return self._selections

    # debug methods
    def OnDump(self, params):
        print self.getSelectedItems()

    def scheduleDump(self):
        self.PostMessage(win32con.WM_USER+1)

    def insertLabel(self, text, parent, after):
        return self.InsertItem(commctrl.TVIF_TEXT, text, 0, 0, 0, 0, None, parent, after)

    #
    #  command responses
    #

    # delegate to what GRiNS thinks as the Layout view
    def OnCommand(self, params):
        msg = Win32Msg(params)
        self.getLayoutView().onUserCmd(msg.cmdid())

    #
    #  popup menu
    #

    # return what GRiNS thinks as the Layout view for command delegation
    def getLayoutView(self):
        return self.parent
