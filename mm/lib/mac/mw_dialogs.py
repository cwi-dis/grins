__version__ = "$Id$"

from Carbon import Qd
from Carbon import Dlg
from Carbon import Ctl
from Carbon import Evt
from Carbon import Controls
from Carbon import ControlAccessor
import MacOS
import string
import sys
from types import *
import MMurl
import macfs
import os

#
# Stuff used from other mw_ modules
#
import WMEVENTS
import mw_globals
from mw_globals import FALSE, TRUE
from mw_resources import *
from mw_windows import DialogWindow
import mw_widgets

def _string2dialog(text):
    """Prepare a Python string for use in a dialog"""
    if '\n' in text:
        text = string.split(text, '\n')
        text = string.join(text, '\r')
    if len(text) > 253:
        text = text[:253] + '\311'
    return text

#
# XXXX Maybe the previous class should be combined with this one, or does that
# give too many stuff in one object (window, dialogwindow, per-dialog info, editor
# info)?
class MACDialog:
    def __init__(self, title, resid, allitems=[], default=None, cancel=None,
                            cmdbuttons=None):
        self._itemlist_shown = allitems[:]
        if not hasattr(self, 'last_geometry'):
            self.last_geometry = None
        self._window = DialogWindow(resid, title=title, default=default,
                cancel=cancel, cmdbuttons=cmdbuttons, geometry = self.last_geometry)
        self._dialog = self._window.getdialogwindowdialog()
        # Override event handler:
        self._window.set_itemhandler(self.do_itemhit)

    def get_geometry(self):
        if self._window and self._window.is_showing():
            self.last_geometry = self._window.getgeometry(mw_globals.UNIT_PXL)
            return self.last_geometry

    def do_itemhit(self, item, event):
        return 0

    def _showitemlist(self, itemlist):
        """Make sure the items in itemlist are visible and active. NOTE: obsolete"""
        for item in itemlist:
            if item in self._itemlist_shown:
                continue
            self._dialog.ShowDialogItem(item)
            tp, h, rect = self._dialog.GetDialogItem(item) # XXXX Is this still needed?
            if tp == 7:             # User control
                h.as_Control().ShowControl()
            self._itemlist_shown.append(item)

    def _hideitemlist(self, itemlist):
        """Make items in itemlist inactive and invisible. NOTE: obsolete"""
        for item in itemlist:
            if item not in self._itemlist_shown:
                continue
            self._dialog.HideDialogItem(item)
            tp, h, rect = self._dialog.GetDialogItem(item)
            if tp == 7:             # User control
                h.as_Control().HideControl()
            self._itemlist_shown.remove(item)

    def _showitemcontrols(self, itemlist):
        """Make sure item controls (plus any control embedded) are visible and active"""
        for item in itemlist:
##             if item in self._itemlist_shown:
##                 continue
            ctl = self._dialog.GetDialogItemAsControl(item)
            ctl.ShowControl()
##             self._itemlist_shown.append(item)

    def _hideitemcontrols(self, itemlist):
        """Make item controls (plus anything embedded) are invisible"""
        for item in itemlist:
##             if item not in self._itemlist_shown:
##                 continue
            ctl = self._dialog.GetDialogItemAsControl(item)
            ctl.HideControl()
##             self._itemlist_shown.remove(item)

    def _setsensitive(self, itemlist, sensitive):
        """Set or reset item sensitivity to user input"""
        for item in itemlist:
            ctl = self._dialog.GetDialogItemAsControl(item)
            if sensitive:
                ctl.ActivateControl()
            else:
                ctl.DeactivateControl()
        if sensitive:
            self._showitemlist(itemlist)

    def _setctlvisible(self, itemlist, visible):
        """Set or reset item visibility"""
        for item in itemlist:
            ctl = self._dialog.GetDialogItemAsControl(item)
            if visible:
                ctl.ShowControl()
            else:
                ctl.HideControl()

    def _settextsensitive(self, itemlist, sensitive):
        """Set or reset item sensitivity to user input"""
        for item in itemlist:
            tp, h, rect = self._dialog.GetDialogItem(item) # XXXX How to handle this?
            if sensitive:
                tp = tp & ~128
            else:
                tp = tp | 128
            self._dialog.SetDialogItem(item, tp, h, rect)
        if sensitive:
            self._showitemlist(itemlist)

    def _setlabel(self, item, text):
        """Set the text of a static text or edit text"""
        text = _string2dialog(text)
##         print 'DBG: setlabel', item, text
        h = self._dialog.GetDialogItemAsControl(item)
        Dlg.SetDialogItemText(h, text)

    def _getlabel(self, item):
        """Return the text of a static text or edit text"""
        h = self._dialog.GetDialogItemAsControl(item)
        text = Dlg.GetDialogItemText(h)
        if '\r' in text:
            text = string.split(text, '\r')
            text = string.join(text, '\n')
        return text

    def _settitle(self, item, text):
        """Set the title of a control item"""
        text = _string2dialog(text)
        ctl = self._dialog.GetDialogItemAsControl(item)
        ctl.SetControlTitle(text)

    def _selectinputfield(self, item):
        """Select all text in an input field"""
        self._dialog.SelectDialogItemText(item, 0, 32767)

    def _setbutton(self, item, value):
        ctl = self._dialog.GetDialogItemAsControl(item)
        ctl.SetControlValue(value)

    def _getbutton(self, item):
        ctl = self._dialog.GetDialogItemAsControl(item)
        return ctl.GetControlValue()

    def _togglebutton(self, item):
        ctl = self._dialog.GetDialogItemAsControl(item)
        value = ctl.GetControlValue()
        ctl.SetControlValue(not value)

    def close(self):
        """Close the dialog and free resources."""
        self._window.close()
        self._dialog = None

    def show(self):
        """Show the dialog."""
        self._window.show(geometry=self.last_geometry)
        self._window.pop()
        self._window.register(WMEVENTS.WindowExit, self.goaway, ())

    def pop(self):
        """Pop window to front"""
        self._window.pop()

    def goaway(self, *args):
        """Callback used when user presses go-away box of window"""
        self.hide()

    def hide(self):
        """Hide the dialog."""
        self._window.hide()

    def rungrabbed(self):
        self._window.rungrabbed()

    def settitle(self, title):
        """Set (change) the title of the window.

        Arguments (no defaults):
        title -- string to be displayed as new window title.
        """
        self._window.settitle(title)

    def is_showing(self):
        """Return whether dialog is showing."""
        return self._window.is_showing()

    def setcursor(self, cursor):
        """Set the cursor to a named shape.

        Arguments (no defaults):
        cursor -- string giving the name of the desired cursor shape
        """
        self._window.setcursor(cursor)

_dont_show_again_identities = {}

class _ModelessDialog(MACDialog):
    def __init__(self, title, dialogid, text, okcallback, cancelcallback=None, identity=None):
        MACDialog.__init__(self, title, dialogid, [], ITEM_QUESTION_OK, ITEM_QUESTION_CANCEL)
        self.okcallback = okcallback
        self.cancelcallback = cancelcallback
        self._setlabel(ITEM_QUESTION_TEXT, text)
        self.identity = identity
        if not identity:
            self._hideitemcontrols([ITEM_QUESTION_NOTAGAIN])
        self.show()

    def do_itemhit(self, item, event):
        if item == ITEM_QUESTION_OK:
##             self.close()
            if self.identity and self._getbutton(ITEM_QUESTION_NOTAGAIN):
                _dont_show_again_identities[self.identity] = 1
            if self.okcallback:
                func, arglist = self.okcallback
                apply(func, arglist)
        elif item == ITEM_QUESTION_CANCEL:
            self.close()
            if self.cancelcallback:
                func, arglist = self.cancelcallback
                apply(func, arglist)
        elif item == ITEM_QUESTION_NOTAGAIN:
            self._togglebutton(item)
        else:
            print 'Unknown modeless dialog event', item, event
        return 1

def _ModalDialog(title, dialogid, text, okcallback, cancelcallback=None, identity=None):
    d = Dlg.GetNewDialog(dialogid, -1)
    d.SetDialogDefaultItem(ITEM_QUESTION_OK)
    if cancelcallback:
        d.SetDialogCancelItem(ITEM_QUESTION_CANCEL)
    h = d.GetDialogItemAsControl(ITEM_QUESTION_TEXT)
    if not identity:
        d.HideDialogItem(ITEM_QUESTION_NOTAGAIN)
    text = _string2dialog(text)
    Dlg.SetDialogItemText(h, text)
    d.AutoSizeDialog()
    w = d.GetDialogWindow()
    w.ShowWindow()
    while 1:
        n = Dlg.ModalDialog(None)
        if n == ITEM_QUESTION_OK:
            if identity:
                ctl = d.GetDialogItemAsControl(ITEM_QUESTION_NOTAGAIN)
                if ctl.GetControlValue():
                    _dont_show_again_identities[identity] = 1
            del d
            del w
            if okcallback:
                func, arglist = okcallback
                apply(func, arglist)
            return
        elif n == ITEM_QUESTION_CANCEL:
            del d
            del w
            if cancelcallback:
                func, arglist = cancelcallback
                apply(func, arglist)
            return
        elif n == ITEM_QUESTION_NOTAGAIN:
            ctl = d.GetDialogItemAsControl(ITEM_QUESTION_NOTAGAIN)
            ctl.SetControlValue(not ctl.GetControlValue())
        else:
            print 'Unknown modal dialog item', n

def showmessage(text, mtype = 'message', grab = 1, callback = None,
                     cancelCallback = None, name = 'message',
                     title = 'message', parent = None, identity=None):
    if identity and _dont_show_again_identities.has_key(identity):
        if callback:
            func, arg = callback
            apply(func, arg)
        return
    if '\n' in text:
        text = string.join(string.split(text, '\n'), '\r')
    if mtype == 'question' or cancelCallback:
        dlgid = ID_QUESTION_DIALOG
    else:
        dlgid = ID_MESSAGE_DIALOG
    if grab:
        _ModalDialog(title, dlgid, text, callback, cancelCallback, identity)
    else:
        return _ModelessDialog(title, dlgid, text, callback, cancelCallback, identity)

# XXXX Do we need a control-window too?

class FileDialog:
    def __init__(self, prompt, directory, filter, file, cb_ok, cb_cancel,
                 existing=0):
        # We implement this modally for the mac.
        if directory:
            try:
                macfs.SetFolder(os.path.join(directory + ':placeholder'))
            except macfs.error:
                pass
        if existing:
            fss, ok = macfs.PromptGetFile(prompt)
        else:
            if filter and not file:
                # Guess a filename with correct extension
                if type(filter) == type([]) or type(filter) == type(()):
                    filter = filter[0]
                import MMmimetypes
                ext = MMmimetypes.guess_extension(filter)
                file = 'Untitled' + ext
            fss, ok = macfs.StandardPutFile(prompt, file)
        if ok:
            filename = fss.as_pathname()
            try:
                if cb_ok:
                    ret = cb_ok(filename)
            except 'xxx':
                showmessage("Internal error:\nexception %s"%`sys.exc_info()`)
                ret = None
            if ret:
                if type(ret) is StringType:
                    showmessage(ret)
        else:
            try:
                if cb_cancel:
                    ret = cb_cancel()
                else:
                    ret = None
            except:
                showmessage("Internal error:\nexception %s"%`sys.exc_info()`)
                ret = None
            if ret:
                if type(ret) is StringType:
                    showmessage(ret)

    def close(self):
        pass

    def setcursor(self, cursor):
        pass

    def is_closed(self):
        return 1

class ProgressDialog:
    # Placeholder

    def __init__(self, title, cancelcallback=None, parent=None):
        import EasyDialogs
        self.cancelcallback = cancelcallback
        self.progressbar = EasyDialogs.ProgressBar(title)
        self.oldlabel = ""
        self.oldvalues = (0, 0)

    def set(self, label, cur1=None, max1=None, cur2=None, max2=None):
        try:
            if cur1 != None:
                label = label + " (%d of %d)"%(cur1, max1)
            if label != self.oldlabel:
                self.progressbar.label(label)
                self.oldlabel = label
            if (cur2, max2) != self.oldvalues:
                if cur2 == None:
                    cur2 = 0
                if max2 == None:
                    max2 = 0
                self.progressbar.set(cur2, max2)
                self.oldvalues = (cur2, max2)
        except KeyboardInterrupt:
            if self.cancelcallback:
                self.cancelcallback()

class _SelectionDialog(DialogWindow):
    DIALOG_ID = ID_SELECT_DIALOG
    def __init__(self, listprompt, itemlist, default=None, hascancel=1, show=1, multi=0):
        # First create dialogwindow and set static items
        if hascancel:
            DialogWindow.__init__(self, self.DIALOG_ID,
                            default=ITEM_SELECT_OK, cancel=ITEM_SELECT_CANCEL)
        else:
            DialogWindow.__init__(self, self.DIALOG_ID, default=ITEM_SELECT_OK)
        if not hascancel:
            self._dlg.HideDialogItem(ITEM_SELECT_CANCEL)
        h = self._dlg.GetDialogItemAsControl(ITEM_SELECT_LISTPROMPT)
        Dlg.SetDialogItemText(h, _string2dialog(listprompt))

        # Now setup the scrolled list
        self._itemlist = itemlist
        self._listwidget = self.ListWidget(ITEM_SELECT_ITEMLIST, itemlist, multi=multi)
        self._listwidget.setkeyboardfocus()

        # And the default value and ok button
        ctl = self._dlg.GetDialogItemAsControl(ITEM_SELECT_OK)
        if multi:
            ctl.ActivateControl()
        elif default is None:
            ctl.DeactivateControl()
        else:
            ctl.ActivateControl()
            self._listwidget.select(default)

        # And show it
        if show:
            self.show()

    def do_itemhit(self, item, event):
        is_ok = 0
        if item == ITEM_SELECT_CANCEL:
            self.CancelCallback()
            self.close()
            return 1
        elif item == ITEM_SELECT_OK:
            is_ok = 1
        elif item == ITEM_SELECT_ITEMLIST:
            # XXXX is_ok = isdouble
            pass
        else:
            print 'Unknown item', self, item, event
        # Done a bit funny, because of double-clicking
        item = self._listwidget.getselect()
        ctl = self._dlg.GetDialogItemAsControl(ITEM_SELECT_OK)
        if item is None:
            ctl.DeactivateControl()
        else:
            ctl.ActivateControl()
        if is_ok:
            self.OkCallback(item)
            self.close()
        return 1

class TraceDialog(_SelectionDialog):
    DIALOG_ID = ID_TRACE_DIALOG
    def __init__(self):
        _SelectionDialog.__init__(self, "Stack", [], None, 0)
        self._dlg.HideDialogItem(ITEM_SELECT_OK)
        self.itemcount = 0
        self.lasttime = Evt.TickCount()/5

    def setitem(self, item, value, clear=0):
        oldport = Qd.GetPort()
        if item >= self.itemcount:
            self._listwidget.insert(-1, ['[untraced]']*(item-self.itemcount+1))
            self.itemcount = item+1
        self._listwidget.replace(item, value)
        if clear:
            for i in range(item+1, self.itemcount):
                self._listwidget.replace(i, '')
        self._listwidget.select(item, autoscroll=1)
        if Evt.TickCount()/5 != self.lasttime:
            self.lasttime = Evt.TickCount()/5
            self._dlg.DrawDialog()
        Qd.SetPort(oldport)

class _CallbackSelectionDialog(_SelectionDialog):
    def __init__(self, list, title, prompt):
        # XXXX ignore title for now
        self.__callbacklist = []
        hascancel = 0
        keylist = []
        for item in list:
            if item == None:
                continue
            if item == 'Cancel':
                hascancel = 1
            else:
                label, callback = item
                keylist.append(label)
                self.__callbacklist.append(callback)
        _SelectionDialog.__init__(self, prompt, keylist, hascancel=hascancel)

    def OkCallback(self, index):
        rtn, args = self.__callbacklist[index]
        apply(rtn, args)
        self.grabdone()

    def CancelCallback(self):
        self.grabdone()

class _ModalSelectionDialog(_SelectionDialog):
    def __init__(self, list, title, prompt, default):
        self._value = None
        _SelectionDialog.__init__(self, prompt, list, default=default)

    def OkCallback(self, index):
        self._value = index
        self.grabdone()

    def CancelCallback(self):
        self.grabdone()

    def getvalue(self):
        return self._value

class _ModalMultiSelectionDialog(_ModalSelectionDialog):
    def __init__(self, list, title, prompt, deflist):
        self._value = None
        _SelectionDialog.__init__(self, prompt, list, hascancel=1, show=0, multi=1)
        for item in deflist:
            self._listwidget.select(item)
        self.show()

    def OkCallback(self, item):
        # Ignore item: we want them all
        self._value = self._listwidget.getallselectvalues()
        self.grabdone()

class InputDialog(DialogWindow):
    DIALOG_ID=ID_INPUT_DIALOG

    def __init__(self, prompt, default, cb, cancelCallback = None,
                    passwd=0, parent=None):
        # XXXX passwd parameter to be implemted
        self._is_passwd_dialog = passwd
        # First create dialogwindow and set static items
        if passwd:
            dialog_id = ID_PASSWD_DIALOG
        else:
            dialog_id = self.DIALOG_ID
        DialogWindow.__init__(self, dialog_id, title=prompt,
                        default=ITEM_INPUT_OK, cancel=ITEM_INPUT_CANCEL)
        self._settext(default)
        self._cb = cb
        self._cancel = cancelCallback

        self.show()

    def _settext(self, text):
        text = _string2dialog(text)
        h = self._dlg.GetDialogItemAsControl(ITEM_INPUT_TEXT)
        if self._is_passwd_dialog:
            ControlAccessor.SetControlData(h, Controls.kControlEditTextPart,
                    Controls.kControlEditTextPasswordTag, text)
            Ctl.SetKeyboardFocus(self._onscreen_wid, h, Controls.kControlEditTextPart)
        else:
            Dlg.SetDialogItemText(h, text)
            self._dlg.SelectDialogItemText(ITEM_INPUT_TEXT, 0, 32767)

    def _gettext(self):
        h = self._dlg.GetDialogItemAsControl(ITEM_INPUT_TEXT)
        if self._is_passwd_dialog:
            rv = ControlAccessor.GetControlData(h, Controls.kControlEditTextPart,
                            Controls.kControlEditTextPasswordTag)
        else:
            rv = Dlg.GetDialogItemText(h)
        return rv

    def do_itemhit(self, item, event):
        if item == ITEM_INPUT_CANCEL:
            if self._cancel:
                apply(apply, self._cancel)
            self.close()
        elif item == ITEM_INPUT_OK:
            self.done()
        elif item == ITEM_INPUT_TEXT:
            pass
        else:
            print 'Unknown item', self, item, event
        return 1

    def done(self):
        ctl = self._dlg.GetDialogItemAsControl(ITEM_INPUT_TEXT)
        rv = self._gettext()
        if self._is_passwd_dialog:
            # For password dialogs make it disappear quickly
            ctl.HiliteControl(10)
            ctl.HiliteControl(0)
            self.close()
            self._cb(rv)
        else:
            ctl.HiliteControl(10)
            self._cb(rv)
            ctl.HiliteControl(0)
            self.close()

class InputURLDialog(InputDialog):
    DIALOG_ID=ID_INPUTURL_DIALOG

    def do_itemhit(self, item, event):
        if item == ITEM_INPUTURL_BROWSE:
            # XXXX This is an error in Python:
            ##fss, ok = macfs.StandardGetFile('TEXT')
            fss, ok = macfs.StandardGetFile()
            if ok:
                pathname = fss.as_pathname()
                url = MMurl.pathname2url(pathname)
                h = self._dlg.GetDialogItemAsControl(ITEM_INPUT_TEXT)
                Dlg.SetDialogItemText(h, _string2dialog(url))
                self._dlg.SelectDialogItemText(ITEM_INPUT_TEXT, 0, 32767)
            return 1
        return InputDialog.do_itemhit(self, item, event)

class NewChannelDialog(DialogWindow):
    DIALOG_ID= ID_NEWCHANNEL_DIALOG

    def __init__(self, prompt, default, types, cb, cancelCallback = None, parent=None):
        # First create dialogwindow and set static items
        DialogWindow.__init__(self, self.DIALOG_ID, title=prompt,
                        default=ITEM_INPUT_OK, cancel=ITEM_INPUT_CANCEL)
        h = self._dlg.GetDialogItemAsControl(ITEM_INPUT_TEXT)
        Dlg.SetDialogItemText(h, _string2dialog(default))
        self._dlg.SelectDialogItemText(ITEM_INPUT_TEXT, 0, 32767)
        self.type_select=self.SelectWidget(ITEM_NEWCHANNEL_TYPE, types)
        self._cb = cb
        self._cancel = cancelCallback

    def close(self):
        self.grabdone()
        self.type_select.delete()
        del self.type_select
        DialogWindow.close(self)

    def do_itemhit(self, item, event):
        if item == ITEM_INPUT_CANCEL:
            if self._cancel:
                self._cancel()
            self.close()
        elif item == ITEM_INPUT_OK:
            self.done()
        elif item == ITEM_INPUT_TEXT:
            pass
        elif item == ITEM_NEWCHANNEL_TYPE:
            pass
        else:
            print 'Unknown item', self, item, event
        return 1

    def done(self):
        h = self._dlg.GetDialogItemAsControl(ITEM_INPUT_TEXT)
        name = Dlg.GetDialogItemText(h)
        type = self.type_select.getselectvalue()
        ctl = self._dlg.GetDialogItemAsControl(ITEM_INPUT_OK)
        ctl.HiliteControl(10)
        self._cb(name, type)
        ctl.HiliteControl(0)
        self.close()

class TemplateDialog(DialogWindow):
    DIALOG_ID= ID_TEMPLATE_DIALOG

    def __init__(self, names, descriptions, cb, cancelCallback = None, parent=None):
        # names: list of template names
        # descriptions: list of (text, image, ...) parallel to names
        #
        # First create dialogwindow and set static items
        DialogWindow.__init__(self, self.DIALOG_ID, title="New Document",
                        default=ITEM_TEMPLATE_OK, cancel=ITEM_TEMPLATE_CANCEL)

        self.type_select=self.SelectWidget(ITEM_TEMPLATE_POPUP, names)
        self.snapshot = self.ImageWidget(ITEM_TEMPLATE_IMAGE)
        self._cb = cb
        self._cancel = cancelCallback
        self.descriptions = descriptions

        self.type_select.select(0)
        self._setdialoginfo(0)
##         self.settarget(ITEM_TEMPLATE_PLAYER)

        self.show()

    def close(self):
        self.grabdone()
        self.type_select.delete()
        del self.type_select
        del self.snapshot
        DialogWindow.close(self)

    def do_itemhit(self, item, event):
        if item == ITEM_INPUT_CANCEL:
            if self._cancel:
                self._cancel()
            self.close()
        elif item == ITEM_INPUT_OK:
            self.done()
        elif item == ITEM_TEMPLATE_POPUP:
            self._setdialoginfo(self.type_select.getselect())
##         elif item in (ITEM_TEMPLATE_PLAYER, ITEM_TEMPLATE_PLUGIN):
##             self.settarget(item)
        else:
            print 'Unknown item', self, item, event
        return 1

##     def settarget(self, item):
##         self._setbutton(ITEM_TEMPLATE_PLAYER, (item==ITEM_TEMPLATE_PLAYER))
##         self._setbutton(ITEM_TEMPLATE_PLUGIN, (item==ITEM_TEMPLATE_PLUGIN))

    def _setbutton(self, item, value):
        # Silly: this duplicates a method in MACDialog
        ctl = self._dlg.GetDialogItemAsControl(item)
        ctl.SetControlValue(value)

    def _getbutton(self, item):
        ctl = self._dlg.GetDialogItemAsControl(item)
        return ctl.GetControlValue()

    def done(self):
        which = self.type_select.getselect()
        if 0 <= which < len(self.descriptions):
            cbarg = self.descriptions[which]
            ctl = self._dlg.GetDialogItemAsControl(ITEM_INPUT_OK)
            ctl.HiliteControl(10)
            self._cb(cbarg)
            ctl.HiliteControl(0)
        self.close()

    def _setdialoginfo(self, idx):
        htext = self._dlg.GetDialogItemAsControl(ITEM_TEMPLATE_DESCRIPTION)
        if 0 <= idx < len(self.descriptions):
            text = self.descriptions[idx][0]
            image = self.descriptions[idx][1]
        else:
            text = ''
            image = None
        Dlg.SetDialogItemText(htext, text)
        self.snapshot.setfromfile(image)

class BandwidthComputeDialog(DialogWindow):
    def __init__(self, title, parent=None):
        DialogWindow.__init__(self, ID_DIALOG_BANDWIDTH,
                        default=ITEM_BANDWIDTH_OK, cancel=ITEM_BANDWIDTH_CANCEL)
        self._settext(ITEM_BANDWIDTH_MESSAGE, title)
        self._settext(ITEM_BANDWIDTH_ERRORS, 'Computing...')
        self._settext(ITEM_BANDWIDTH_STALLTIME,'Computing...')
        self._settext(ITEM_BANDWIDTH_STALLCOUNT, 'Computing...')
        self._settext(ITEM_BANDWIDTH_PREROLL, 'Computing...')
        self._settext(ITEM_BANDWIDTH_MESSAGE2, '')
        self.mustwait = 0
        self.calback = None
        ctl = self._dlg.GetDialogItemAsControl(ITEM_BANDWIDTH_OK)
        ctl.DeactivateControl()
        ctl = self._dlg.GetDialogItemAsControl(ITEM_BANDWIDTH_CANCEL)
        ctl.DeactivateControl()
        self.show()
        self._dlg.DrawDialog()

    def _settext(self, item, str):
        h = self._dlg.GetDialogItemAsControl(item)
        Dlg.SetDialogItemText(h, str)

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
        self._settext(ITEM_BANDWIDTH_ERRORS, errorcount)
        self._settext(ITEM_BANDWIDTH_STALLTIME,errorseconds)
        self._settext(ITEM_BANDWIDTH_STALLCOUNT, delaycount)
        self._settext(ITEM_BANDWIDTH_PREROLL, prerolltime)
        self._settext(ITEM_BANDWIDTH_MESSAGE2, msg)

    def done(self, callback=None, cancancel=0):
        if cancancel and self.mustwait == 0:
            # Continue without waiting
            self.close()
            if callback:
                callback()
            return
        self.callback = callback
        ctl = self._dlg.GetDialogItemAsControl(ITEM_BANDWIDTH_OK)
        ctl.ActivateControl()
        if cancancel:
            ctl.SetControlTitle('Continue')
            ctl = self._dlg.GetDialogItemAsControl(ITEM_BANDWIDTH_CANCEL)
            ctl.ActivateControl()

    def do_itemhit(self, item, event):
        if item == ITEM_BANDWIDTH_CANCEL:
            self.close()
        elif item == ITEM_BANDWIDTH_OK:
            self.close()
            if self.callback:
                self.callback()
        elif item == ITEM_BANDWIDTH_HELP:
            self.do_Help()
        else:
            print 'Bandwidth Dialog item: ', item
        return 1

    def do_Help(self):
        import Help
        Help.givehelp('bandwidth')

[TOP, CENTER, BOTTOM] = range(3)

def Dialog(list, title = '', prompt = None, grab = 1, vertical = 1,
           parent = None):
    w = _CallbackSelectionDialog(list, title, prompt)
    if grab:
        w.rungrabbed()
    return w

_end_loop = '_end_loop'                 # exception for ending a loop

class _Question:
    def __init__(self, text):
        self.looping = FALSE
        self.answer = None
        self.text = text

    def run(self):
        try:
            showmessage(self.text, mtype = 'question',
                callback = (self.callback, (TRUE,)),
                cancelCallback = (self.callback, (FALSE,)))
        except _end_loop:
            pass
        return self.answer

    def callback(self, answer):
        self.answer = answer
        if self.looping:
            raise _end_loop

def showquestion(text, parent = None):
    return _Question(text).run()

def multchoice(prompt, list, defindex, parent = None):
    w = _ModalSelectionDialog(list, '', prompt, default=defindex)
    w.rungrabbed()
    rv = w.getvalue()
    if rv is None:
        return -1
    return rv

def mmultchoice(prompt, list, deflist, parent=None):
    w = _ModalMultiSelectionDialog(list, '', prompt, deflist)
    w.rungrabbed()
    return w.getvalue()

def GetYesNoCancel(prompt, parent = None):
    import EasyDialogs
    rv = EasyDialogs.AskYesNoCancel(prompt, 1)
    if rv < 0: return 2
    if rv > 0: return 0
    return 1

# XXX to show or inactivate the cancel button
def GetYesNo(prompt, parent = None):
    import EasyDialogs
    rv = EasyDialogs.AskYesNoCancel(prompt, 1)
    if rv < 0: return 1
    if rv > 0: return 0
    return 1

def GetOKCancel(prompt, parent = None):
    import EasyDialogs
    rv = EasyDialogs.AskYesNoCancel(prompt, 1, yes='OK', no='')
    if rv > 0: return 0
    return 1
