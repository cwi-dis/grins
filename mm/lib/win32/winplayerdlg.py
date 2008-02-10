__version__ = "$Id$"

import win32con, win32ui, win32api

import afxres

import components

import grinsRC
import usercmd, usercmdui

from pywinlib.mfc import window


class Preferences:
    DEFAULT_TITLE = 'Previewer Control Panel'
    IDW_TOOLBAR_PLAYER_PANEL = 0xe805
    MIN_CTRL_WIDTH = 80
    CTRL_WIDTH = max(MIN_CTRL_WIDTH, 4*len(DEFAULT_TITLE))
    FRAME_WIDTH = (3*(CTRL_WIDTH+16))/2 + 2*win32api.GetSystemMetrics(win32con.SM_CXFRAME)
    ERASE_CLOSE = 1

class ResItem:
    classid = 0x0082
    style = win32con.WS_CHILD | win32con.WS_VISIBLE
    def __init__(self, name, width, height):
        self.name = name
        self.width = width
        self.height = height
        self.id = 0
    def getResourceList(self, x, y):
        return [self.classid, self.name, self.id, (x, y, self.width, self.height), self.style]

class Option(ResItem):
    classid = 0x0085
    style = win32con.WS_CHILD | win32con.WS_VISIBLE | win32con.CBS_DROPDOWNLIST | win32con.CBS_SORT | win32con.WS_VSCROLL | win32con.WS_BORDER
    def __init__(self, name, width=Preferences.CTRL_WIDTH, height=12):
        ResItem.__init__(self, name, width, height)
    def getResourceList(self, x, y):
        return [self.classid, self.name, self.id, (x, y, self.width, 128), self.style]

class Boolean(ResItem):
    classid = 0x0080
    style = win32con.WS_CHILD | win32con.WS_VISIBLE | win32con.BS_AUTOCHECKBOX
    def __init__(self, name, width=Preferences.CTRL_WIDTH, height=12):
        ResItem.__init__(self, name, width, height)

class Button(ResItem):
    classid = 0x0080
    style = win32con.WS_CHILD | win32con.WS_VISIBLE
    def __init__(self, name, width=None, height=12):
        if width is None:
            width = 4*(len(name)+2)
        ResItem.__init__(self, name, width, height)

class PlayerDlgBar(window.Wnd):
    iconplay = win32ui.GetApp().LoadIcon(grinsRC.IDI_PLAY)
    iconpause = win32ui.GetApp().LoadIcon(grinsRC.IDI_PAUSE)
    iconstop = win32ui.GetApp().LoadIcon(grinsRC.IDI_STOP)
    BUTTON = 0x0080
    EDIT = 0x0081
    STATIC = 0x0082
    LISTBOX = 0x0083
    SCROLLBAR = 0x0084
    COMBOBOX = 0x0085

    def __init__(self):
        window.Wnd.__init__(self, win32ui.CreateDialogBar())
        self._parent = None
        self._resitems = []
        self._ctrls = {}
        self._miniframetype = None
        self._lessAttributes = None
        self._moreAttributes = None

    def createWindow(self, parent, attributes):
        self._parent = parent
        WM_FLOATSTATUS  = 0x036D
        self._parent.HookMessage(self.OnFloatStatus, WM_FLOATSTATUS)
        self.createResourceItems(attributes)
        CBRS_GRIPPER = 0x00400000

        # width, height increments (for pixel level adjustments)
        default_size_incr = 0, 0

        self.CreateWindowIndirect(parent, self.makeTemplate(),
                afxres.CBRS_SIZE_DYNAMIC | CBRS_GRIPPER | afxres.CBRS_FLOAT_MULTI,
                Preferences.IDW_TOOLBAR_PLAYER_PANEL, default_size_incr)

        self.EnableDocking(afxres.CBRS_ALIGN_ANY);
        parent.EnableDocking(afxres.CBRS_ALIGN_ANY);
        self.ShowWindow(win32con.SW_HIDE)
        l, t, r, b = parent.GetMDIClient().GetWindowRect()
        parent.FloatControlBar(self, (r-Preferences.FRAME_WIDTH+1, t+2) )
        self._miniframetype = type(self.GetParent().GetParent())
        self.eraseClose()
        self.setButtonIcons()
        self.createComponents()
        self.hookCommands()
        self.hide()

    def setAttributes(self, attributes, moreAttributes=None):
        attrscpy = attributes[:]
        if moreAttributes is not None:
            self._lessAttributes = attributes
            self._moreAttributes = moreAttributes
            attrscpy.append(('button', 'More'))
        parent = self._parent
        visible = self.IsWindowVisible()
        miniframe = None
        try:
            frame = self.GetParent().GetParent()
        except:
            return
        if type(frame) == self._miniframetype:
            miniframe = frame
        if miniframe:
            l, t, r, b = miniframe.GetWindowRect()
        self.destroy()
        window.Wnd.__init__(self, win32ui.CreateDialogBar())
        self.createWindow(parent, attributes)
        if visible:
            self.ShowWindow(win32con.SW_SHOW)
        if miniframe:
            self.show((l,t))

    def OnFloatStatus(self, params):
        self.eraseClose()

    def destroy(self):
        self.DestroyWindow()
        self._parent = None
        self._resitems = []
        self._ctrls = {}

    def show(self, pt=None):
        self.ShowWindow(win32con.SW_SHOW)
        self._parent.DockControlBar(self)
        if pt is None:
            l, t, r, b = self._parent.GetMDIClient().GetWindowRect()
            pt = r-Preferences.FRAME_WIDTH+1, t+2
        self._parent.FloatControlBar(self, pt)
        self.eraseClose()

    def hide(self):
        self.ShowWindow(win32con.SW_HIDE)
        self._parent.DockControlBar(self)

    def eraseClose(self):
        if not Preferences.ERASE_CLOSE:
            return
        if not self._obj_ or not self.IsWindowVisible():
            return
        try:
            miniframe = self.GetParent().GetParent()
        except:
            return
        if type(miniframe) == self._miniframetype:
            menu = miniframe.GetSystemMenu()
            if menu:
                try:
                    menu.DeleteMenu(win32con.SC_CLOSE, win32con.MF_BYCOMMAND)
                except:
                    pass
                else:
                    miniframe.DrawMenuBar()

    def createResourceItems(self, attributes):
        id = 1
        for attr in attributes:
            attrtype, name = attr
            resitem = None
            if attrtype == 'option':
                resitem = Option(name)
            elif attrtype == 'boolean':
                resitem = Boolean(name)
            elif attrtype == 'button':
                resitem = Button(name)
            if resitem:
                resitem.id = id
                self._resitems.append(resitem)
                id = id + 1

    # item -> wndClass, text, id, rect, style, exstyle, extraData
    # dialog -> caption, rect, style, exstyle, font, menu, wndClass
    def makeTemplate(self):
        template = []
        cs = win32con.WS_CHILD | win32con.WS_VISIBLE
        x = 8
        y = 3
        if self._resitems:
            y = y + 3 # add some more place for horizontal gripper
        cmdid = usercmdui.usercmd2id

        # row 1
        template.append([self.BUTTON, "Play", cmdid(usercmd.PLAY), (x, y, 12, 12), cs | win32con.BS_ICON | win32con.BS_FLAT])
        template.append([self.BUTTON, "Pause", cmdid(usercmd.PAUSE), (x+16, y, 12, 12), cs | win32con.BS_ICON | win32con.BS_FLAT])
        template.append([self.BUTTON, "Stop", cmdid(usercmd.STOP), (x+32, y, 12, 12), cs | win32con.BS_ICON | win32con.BS_FLAT])
        y = y + 12 + 4

        maxWidth = 48 # The size needed for the play/stop/pause buttons
        for item in self._resitems:
            template.append(item.getResourceList(x, y))
            y = y + item.height + 4
            if item.width > maxWidth: maxWidth = item.width

        dlgStyle = win32con.DS_CONTROL | win32con.WS_CHILD | win32con.DS_SETFONT
        template. insert(0, [Preferences.DEFAULT_TITLE, (0, 0, maxWidth+16, y), dlgStyle, None, (8, "MS Sans Serif")])
        return template

    def setButtonIcons(self):
        cmdid = usercmdui.usercmd2id
        self._bplay = components.Button(self,cmdid(usercmd.PLAY))
        self._bpause = components.Button(self,cmdid(usercmd.PAUSE))
        self._bstop = components.Button(self,cmdid(usercmd.STOP))
        self._bplay.attach_to_parent()
        self._bpause.attach_to_parent()
        self._bstop.attach_to_parent()
        self._bplay.seticon(self.iconplay)
        self._bpause.seticon(self.iconpause)
        self._bstop.seticon(self.iconstop)

    def createComponents(self):
        for item in self._resitems:
            if isinstance(item, Option):
                self._ctrls[item.name] = components.ComboBox(self, item.id)
            elif isinstance(item, Boolean):
                self._ctrls[item.name] = components.CheckButton(self, item.id)
            elif isinstance(item, Button):
                self._ctrls[item.name] = components.Button(self, item.id)
        for ctrl in self._ctrls.values():
            ctrl.attach_to_parent()

    def setOptions(self, optionsdict):
        old_keys = self._ctrls.keys()
        new_keys = optionsdict.keys()
        old_keys.sort()
        new_keys.sort()
        if old_keys != new_keys:
            self._recreateDialog(optionsdict)
        for name, info in optionsdict.items():
            self.setOption(name, info)

    def setOption(self, name, info):
        ctrl = self._ctrls.get(name)
        if isinstance(ctrl,  components.ComboBox):
            optionlist = info[0]
            initoption = info[2]
            if not initoption in optionlist:
                optionlist.append(initoption)
            ctrl.initoptions(optionlist, optionlist.index(initoption))
            ctrl.setcb(info[1])
        elif isinstance(ctrl, components.CheckButton):
            initoption = info[2]
            ctrl.setcb(info[1])
            if initoption == 'on':
                ctrl.setcheck(1)
            elif initoption == 'off':
                ctrl.setcheck(0)
            else:
                print 'Unexpected value for "%s": "%s"'%(name, initoption)
        else:
            print 'Unexpected control:', name, ctrl

    def _recreateDialog(self, optionsdict):
        attrs = []
        for name, (values, cb, init) in optionsdict.items():
            if values == ['off', 'on']:
                attrs.append(('boolean', name))
            else:
                attrs.append(('option', name))
        self.setAttributes(attrs)

    def hookCommands(self):
        for ctrl in self._ctrls.values():
            if isinstance(ctrl, components.ComboBox):
                self._parent.HookCommand(self.onCombo, ctrl.getId())
            elif isinstance(ctrl, components.CheckButton):
                self._parent.HookCommand(self.onCheck, ctrl.getId())
            elif isinstance(ctrl, components.Button):
                self._parent.HookCommand(self.onButton, ctrl.getId())
            else:
                print 'Unexpected control for hookCommands', ctrl

    def onCombo(self, id, code):
        if code == win32con.CBN_SELCHANGE:
            for ctrl in self._ctrls.values():
                if ctrl._id == id:
                    if ctrl._cb:
                        arg = ctrl.getvalue()
                        if type(ctrl._cb) == type(()):
                            apply(ctrl._cb[0], (ctrl._cb[1], arg))
                        else:
                            ctrl._cb(arg)
                    break

    def onCheck(self, id, code):
        if code==win32con.BN_CLICKED:
            for ctrl in self._ctrls.values():
                if ctrl._id == id:
                    if ctrl._cb:
                        arg = ['off', 'on'][ctrl.getcheck()]
                        if type(ctrl._cb) == type(()):
                            apply(ctrl._cb[0], (ctrl._cb[1], arg))
                        else:
                            ctrl._cb(arg)
                    break

    def onButton(self, id, code):
        if code==win32con.BN_CLICKED:
            for ctrl in self._ctrls.values():
                if ctrl._id == id:
                    button = ctrl.gettext()
                    if button == 'Less':
                        attributes = self._lessAttributes[:]
                        attributes.append(('button', 'More'))
                        self.setAttributes(attributes)
                    elif button == 'More':
                        attributes = self._lessAttributes[:] + self._moreAttributes[:]
                        attributes.append(('button', 'Less'))
                        self.setAttributes(attributes)
                    break
