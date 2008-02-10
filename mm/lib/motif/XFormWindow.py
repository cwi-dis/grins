__version__ = "$Id$"

import Xt, Xm, X, Xmd, Xtdefs
from types import *
import string
import ToolTip
from XTopLevel import toplevel
from XCommand import _CommandSupport
from XButtonSupport import _ButtonSupport
from XConstants import error, TRUE, FALSE, TOP, BOTTOM, CENTER, \
     _def_useGadget, _WAITING_CURSOR, _READY_CURSOR
from XHelpers import _create_menu, _setcursor

class _MenuSupport:
    '''Support methods for a pop up menu.'''
    def __init__(self):
        self.__menu = None

    def close(self):
        '''Close the menu.'''
        self.destroy_menu()

    def destroy_menu(self):
        '''Destroy the pop up menu.

        This function is called automatically when a new menu
        is created using create_menu, or when the window
        object is closed.'''

        menu = self.__menu
        self.__menu = None
        if menu:
            self._form.RemoveEventHandler(X.ButtonPressMask, FALSE,
                                          self.__post_menu, None)
            menu.DestroyWidget()

    # support methods, only used by derived classes
    def __post_menu(self, w, client_data, call_data):
        if not self.__menu:
            return
        if call_data.button == X.Button3:
            self.__menu.MenuPosition(call_data)
            self.__menu.ManageChild()

    def _destroy(self):
        self.__menu = None

class _Widget(_MenuSupport):
    '''Support methods for all window objects.'''
    def __init__(self, parent, widget, tooltip = None):
        self._parent = parent
        parent._children.append(self)
        self._showing = TRUE
        self._form = widget
        widget.ManageChild()
        _MenuSupport.__init__(self)
        self._form.AddCallback('destroyCallback', self._destroy, None)
        if tooltip is not None:
            ToolTip.addtthandler(widget, tooltip)

    def __repr__(self):
        return '<_Widget instance at %x>' % id(self)

    def close(self):
        '''Close the window object.'''
        try:
            form = self._form
        except AttributeError:
            pass
        else:
            del self._form
            ToolTip.deltthandler(form)
            _MenuSupport.close(self)
            form.DestroyWidget()
        if self._parent:
            self._parent._children.remove(self)
        self._parent = None

    def is_closed(self):
        '''Returns true if the window is already closed.'''
        return not hasattr(self, '_form')

    def _showme(self, w):
        self._parent._showme(w)

    def _hideme(self, w):
        self._parent._hideme(w)

    def show(self):
        '''Make the window visible.'''
        self._parent._showme(self)
        self._showing = TRUE

    def hide(self):
        '''Make the window invisible.'''
        self._parent._hideme(self)
        self._showing = FALSE

    def is_showing(self):
        '''Returns true if the window is visible.'''
        return self._showing

    # support methods, only used by derived classes
    def _attachments(self, attrs, options):
        '''Calculate the attachments for this window.'''
        for pos in ['left', 'top', 'right', 'bottom']:
            widget = options.get(pos, ())
            if widget != ():
                if type(widget) in (FloatType, IntType):
                    attrs[pos + 'Attachment'] = \
                            Xmd.ATTACH_POSITION
                    attrs[pos + 'Position'] = \
                            int(widget * 100 + .5)
                elif widget:
                    attrs[pos + 'Attachment'] = \
                              Xmd.ATTACH_WIDGET
                    attrs[pos + 'Widget'] = widget._form
                else:
                    attrs[pos + 'Attachment'] = \
                              Xmd.ATTACH_FORM
            offset = options.get(pos + 'Offset')
            if offset is None:
                offset = options.get('offset')
            if offset is not None:
                attrs[pos + 'Offset'] = offset

    def _callback(self, widget, callback, call_data):
        '''Generic callback.'''
        ToolTip.rmtt()
        if self.is_closed():
            return
        apply(apply, callback)
        toplevel.setready()

    def _get_acceleratortext(self, callback):
        return self._parent._get_acceleratortext(callback)

    def _set_callback(self, widget, callbacktype, callback):
        self._parent._set_callback(widget, callbacktype, callback)

    def _set_togglelabels(self, widget, labels):
        self._parent._set_togglelabels(widget, labels)

    def _destroy(self, widget, client_data, call_data):
        '''Destroy callback.'''
        try:
            del self._form
        except AttributeError:
            return
        if self._parent:
            self._parent._children.remove(self)
        self._parent = None
        _MenuSupport._destroy(self)

class Label(_Widget):
    '''Label window object.'''
    def __init__(self, parent, text, useGadget = _def_useGadget,
                 name = 'windowLabel', tooltip = None, **options):
        '''Create a Label subwindow.

        PARENT is the parent window, TEXT is the text for the
        label.  OPTIONS is an optional dictionary with
        options.  The only options recognized are the
        attachment options.'''
        attrs = {}
        self._attachments(attrs, options)
        if useGadget and tooltip is None:
            label = Xm.LabelGadget
        else:
            label = Xm.Label
        label = parent._form.CreateManagedWidget(name, label, attrs)
        label.labelString = text
        self._text = text
        _Widget.__init__(self, parent, label, tooltip)

    def __repr__(self):
        return '<Label instance at %x, text=%s>' % (id(self), self._text)

    def setlabel(self, text):
        '''Set the text of the label to TEXT.'''
        self._form.labelString = text
        self._text = text

class Button(_Widget):
    '''Button window object.'''
    def __init__(self, parent, label, callback, useGadget = _def_useGadget,
                 name = 'windowButton', tooltip = None, **options):
        '''Create a Button subwindow.

        PARENT is the parent window, LABEL is the label on the
        button, CALLBACK is the callback function that is
        called when the button is activated.  The callback is
        a tuple consiting of a callable object and an argument
        tuple.'''
        self.__text = label
        attrs = {'labelString': label}
        self._attachments(attrs, options)
        if useGadget and tooltip is None:
            button = Xm.PushButtonGadget
        else:
            button = Xm.PushButton
        button = parent._form.CreateManagedWidget(name, button, attrs)
        if callback:
            button.AddCallback('activateCallback',
                               self._callback, callback)
        _Widget.__init__(self, parent, button, tooltip)

    def __repr__(self):
        return '<Button instance at %x, text=%s>' % (id(self), self.__text)

    def setlabel(self, text):
        self._form.labelString = text
        self.__text = text

    def setsensitive(self, sensitive):
        self._form.SetSensitive(sensitive)

class OptionMenu(_Widget):
    '''Option menu window object.'''
    def __init__(self, parent, label, optionlist, startpos, cb,
                 useGadget = _def_useGadget, name = 'windowOptionMenu',
                 tooltip = None, **options):
        '''Create an option menu window object.

        PARENT is the parent window, LABEL is a label for the
        option menu, OPTIONLIST is a list of options, STARTPOS
        gives the initial selected option, CB is the callback
        that is to be called when the option is changed,
        OPTIONS is an optional dictionary with options.
        If label is None, the label is not shown, otherwise it
        is shown to the left of the option menu.
        The optionlist is a list of strings.  Startpos is the
        index in the optionlist of the initially selected
        option.  The callback is either None, or a tuple of
        two elements.  If None, no callback is called when the
        option is changed, otherwise the the first element of
        the tuple is a callable object, and the second element
        is a tuple giving the arguments to the callable
        object.'''

        if 0 <= startpos < len(optionlist):
            pass
        else:
            raise error, 'startpos out of range'
        self._useGadget = useGadget
        self._buttons = []
        self._optionlist = []
        self._value = -1
        menu = parent._form.CreatePulldownMenu('windowOption',
                        {'colormap': toplevel._default_colormap,
                         'visual': toplevel._default_visual,
                         'depth': toplevel._default_visual.depth,
                         'orientation': Xmd.VERTICAL})
        self._omenu = menu
        attrs = {'subMenuId': menu,
                 'colormap': toplevel._default_colormap,
                 'visual': toplevel._default_visual,
                 'depth': toplevel._default_visual.depth}
        self._attachments(attrs, options)
        option = parent._form.CreateOptionMenu(name, attrs)
        if label is None:
            option.OptionLabelGadget().UnmanageChild()
            self._text = '<None>'
        else:
            option.labelString = label
            self._text = label
        self._callback = cb
        _Widget.__init__(self, parent, option, tooltip)
        self.setoptions(optionlist, startpos)

    def __repr__(self):
        return '<OptionMenu instance at %x, label=%s>' % (id(self), self._text)

    def close(self):
        _Widget.close(self)
        self._callback = self._value = self._optionlist = \
                         self._buttons = None

    def getpos(self):
        '''Get the index of the currently selected option.'''
        return self._value

    def getvalue(self):
        '''Get the value of the currently selected option.'''
        return self._optionlist[self._value]

    def setpos(self, pos):
        '''Set the currently selected option to the index given by POS.'''
        if pos == self._value:
            return
        if 0 <= pos < len(self._optionlist):
            pass
        else:
            raise error, 'pos out of range'
        if self._optionlist[pos] is None:
            raise error, 'pos points to separator'
        self._form.menuHistory = self._buttons[pos]
        self._value = pos

    def setsensitive(self, pos, sensitive):
        if 0 <= pos < len(self._buttons):
            self._buttons[pos].SetSensitive(sensitive)
        else:
            raise error, 'pos out of range'

    def setvalue(self, value):
        '''Set the currently selected option to VALUE.'''
        self.setpos(self._optionlist.index(value))

    def setoptions(self, optionlist, startpos):
        '''Set new options.

        OPTIONLIST and STARTPOS are as in the __init__ method.'''

        if 0 <= startpos < len(optionlist):
            pass
        else:
            raise error, 'startpos out of range'
        if optionlist[startpos] is None:
            raise error, 'startpos points to separator'
        if optionlist != self._optionlist:
            menu = self._omenu
            for b in self._buttons:
                b.DestroyWidget()
            self._buttons = []
            if len(optionlist) > 30:
                menu.numColumns = (len(optionlist) + 29) / 30
                menu.packing = Xmd.PACK_COLUMN
            else:
                menu.numColumns = 1
                menu.packing = Xmd.PACK_TIGHT
            if self._useGadget:
                cbutton = menu.CreatePushButtonGadget
                cseparator = menu.CreateSeparatorGadget
            else:
                cbutton = menu.CreatePushButton
                cseparator = menu.CreateSeparator
            for i in range(len(optionlist)):
                item = optionlist[i]
                if item is None:
                    button = cseparator(
                            'windowOptionSeparator', {})
                else:
                    button = cbutton('windowOptionButton',
                                     {'labelString': item})
                    button.AddCallback('activateCallback',
                                       self._cb, i)
                button.ManageChild()
                self._buttons.append(button)
            self._optionlist = optionlist
        # set the start position
        self._value = -1
        self.setpos(startpos)

    def _cb(self, widget, value, call_data):
        ToolTip.rmtt()
        if self.is_closed():
            return
        self._value = value
        if self._callback:
            apply(apply, self._callback)
            toplevel.setready()

    def _destroy(self, widget, value, call_data):
        _Widget._destroy(self, widget, value, call_data)
        del self._omenu
        del self._optionlist
        del self._buttons
        del self._callback

class PulldownMenu(_Widget):
    '''Menu bar window object.'''
    def __init__(self, parent, menulist, useGadget = _def_useGadget,
                 name = 'menuBar', **options):
        '''Create a menu bar window object.

        PARENT is the parent window, MENULIST is a list giving
        the definition of the menubar, OPTIONS is an optional
        dictionary of options.
        The menulist is a list of tuples.  The first elements
        of the tuples is the name of the pulldown menu, the
        second element is a list with the definition of the
        pulldown menu.'''

        attrs = {}
        self._attachments(attrs, options)
        if useGadget:
            cascade = Xm.CascadeButtonGadget
        else:
            cascade = Xm.CascadeButton
        menubar = parent._form.CreateMenuBar(name, attrs)
        buttons = []
        widgets = []
        for item, list in menulist:
            menu = menubar.CreatePulldownMenu('windowMenu',
                    {'colormap': toplevel._default_colormap,
                     'visual': toplevel._default_visual,
                     'depth': toplevel._default_visual.depth})
            button = menubar.CreateManagedWidget(
                    'windowMenuButton', cascade,
                    {'labelString': item,
                     'subMenuId': menu})
            widgets.append({})
            _create_menu(menu, list, toplevel._default_visual,
                         toplevel._default_colormap,
                         widgets = widgets[-1])
            buttons.append(button)
        _Widget.__init__(self, parent, menubar)
        self._buttons = buttons
        self._widgets = widgets

    def __repr__(self):
        return '<PulldownMenu instance at %x>' % id(self)

    def close(self):
        _Widget.close(self)
        self._buttons = None

    def setmenu(self, pos, list):
        if not 0 <= pos < len(self._buttons):
            raise error, 'position out of range'
        button = self._buttons[pos]
        menu = self._form.CreatePulldownMenu('windowMenu',
                        {'colormap': toplevel._default_colormap,
                         'visual': toplevel._default_visual,
                         'depth': toplevel._default_visual.depth})
        widgets = {}
        _create_menu(menu, list, toplevel._default_visual,
                     toplevel._default_colormap, widgets = widgets)
        self._widgets[pos] = widgets
        omenu = button.subMenuId
        button.subMenuId = menu
        omenu.DestroyWidget()

    def setmenuentry(self, pos, path, onoff = None, sensitive = None):
        if not 0 <= pos < len(self._buttons):
            raise error, 'position out of range'
        dict = self._widgets[pos]
        for p in path:
            w = dict.get(p, (None, None))[0]
            while w is None:
                w = dict.get(p, (None, None))[0]
        if onoff is not None:
            w.set = onoff
        if sensitive is not None:
            w.SetSensitive(sensitive)

    def _destroy(self, widget, value, call_data):
        _Widget._destroy(self, widget, value, call_data)
        self._buttons = None
        self._widgets = None

# super class for Selection and List
class _List:
    def __init__(self, list, itemlist, initial, sel_cb):
        self._list = list
        list.ListAddItems(itemlist, 1)
        self._itemlist = itemlist
        if type(sel_cb) is ListType:
            if len(sel_cb) >= 1 and sel_cb[0] is not None:
                list.AddCallback('singleSelectionCallback',
                                 self._callback, sel_cb[0])
            if len(sel_cb) >= 2 and sel_cb[1] is not None:
                list.AddCallback('defaultActionCallback',
                                 self._callback, sel_cb[1])
        elif sel_cb is not None:
            list.AddCallback('singleSelectionCallback',
                             self._callback, sel_cb)
        if itemlist:
            self.selectitem(initial)

    def close(self):
        self._itemlist = None
        self._list = None

    def getselected(self):
        pos = self._list.ListGetSelectedPos()
        if pos:
            return pos[0] - 1
        else:
            return None

    def getlistitem(self, pos):
        return self._itemlist[pos]

    def getselection(self):
        pos = self.getselected()
        if pos is None:
            return None
        return self.getlistitem(pos)

    def getlist(self):
        return self._itemlist

    def addlistitem(self, item, pos):
        if pos < 0:
            pos = len(self._itemlist)
        self._list.ListAddItem(item, pos + 1)
        self._itemlist.insert(pos, item)

    def addlistitems(self, items, pos):
        if pos < 0:
            pos = len(self._itemlist)
        self._list.ListAddItems(items, pos + 1)
        self._itemlist[pos:pos] = items

    def dellistitem(self, pos):
        del self._itemlist[pos]
        self._list.ListDeletePos(pos + 1)

    def dellistitems(self, poslist):
        self._list.ListDeletePositions(map(lambda x: x+1, poslist))
        list = poslist[:]
        list.sort()
        list.reverse()
        for pos in list:
            del self._itemlist[pos]

    def replacelistitem(self, pos, newitem):
        self.replacelistitems(pos, [newitem])

    def replacelistitems(self, pos, newitems):
        self._itemlist[pos:pos+len(newitems)] = newitems
        self._list.ListReplaceItemsPos(newitems, pos + 1)

    def delalllistitems(self):
        self._itemlist = []
        self._list.ListDeleteAllItems()

    def selectitem(self, pos):
        if pos is None:
            self._list.ListDeselectAllItems()
            return
        if pos < 0:
            pos = len(self._itemlist) - 1
        self._list.ListSelectPos(pos + 1, 0)

    def is_visible(self, pos):
        if pos < 0:
            pos = len(self._itemlist) - 1
        top = self._list.topItemPosition - 1
        vis = self._list.visibleItemCount
        return top <= pos < top + vis

    def scrolllist(self, pos, where):
        if pos < 0:
            pos = len(self._itemlist) - 1
        if where == TOP:
            self._list.ListSetPos(pos + 1)
        elif where == BOTTOM:
            self._list.ListSetBottomPos(pos + 1)
        elif where == CENTER:
            vis = self._list.visibleItemCount
            toppos = pos - vis / 2 + 1
            if toppos + vis > len(self._itemlist):
                toppos = len(self._itemlist) - vis + 1
            if toppos <= 0:
                toppos = 1
            self._list.ListSetPos(toppos)
        else:
            raise error, 'bad argument for scrolllist'

    def _destroy(self):
        del self._itemlist
        del self._list

class Selection(_Widget, _List):
    def __init__(self, parent, listprompt, itemprompt, itemlist, initial,
                 sel_cb, name = 'windowSelection', **options):
        attrs = {}
        self._attachments(attrs, options)
        selection = parent._form.CreateSelectionBox(name, attrs)
        for widget in Xmd.DIALOG_APPLY_BUTTON, \
            Xmd.DIALOG_CANCEL_BUTTON, Xmd.DIALOG_DEFAULT_BUTTON, \
            Xmd.DIALOG_HELP_BUTTON, Xmd.DIALOG_OK_BUTTON, \
            Xmd.DIALOG_SEPARATOR:
            selection.SelectionBoxGetChild(widget).UnmanageChild()
        w = selection.SelectionBoxGetChild(Xmd.DIALOG_LIST_LABEL)
        if listprompt is None:
            w.UnmanageChild()
            self._text = '<None>'
        else:
            w.labelString = listprompt
            self._text = listprompt
        w = selection.SelectionBoxGetChild(Xmd.DIALOG_SELECTION_LABEL)
        if itemprompt is None:
            w.UnmanageChild()
        else:
            w.labelString = itemprompt
        list = selection.SelectionBoxGetChild(Xmd.DIALOG_LIST)
        list.selectionPolicy = Xmd.SINGLE_SELECT
        list.listSizePolicy = Xmd.CONSTANT
        txt = selection.SelectionBoxGetChild(Xmd.DIALOG_TEXT)
        self._text = txt
        if options.has_key('enterCallback'):
            cb = options['enterCallback']
            txt.AddCallback('activateCallback', self._callback, cb)
        if options.has_key('changeCallback'):
            cb = options['changeCallback']
            txt.AddCallback('valueChangedCallback', self._callback, cb)
        _List.__init__(self, list, itemlist, initial, sel_cb)
        _Widget.__init__(self, parent, selection)

    def __repr__(self):
        return '<Selection instance at %x; label=%s>' % (id(self), self._text)

    def close(self):
        _List.close(self)
        _Widget.close(self)

    def setlabel(self, label):
        w = self._form.SelectionBoxGetChild(Xmd.DIALOG_LIST_LABEL)
        w.labelString = label

    def getselection(self):
        if hasattr(self._text, 'TextFieldGetString'):
            return self._text.TextFieldGetString()
        else:
            return self._text.TextGetString()

    def seteditable(self, editable):
        if hasattr(self._text, 'TextFieldSetEditable'):
            self._text.TextFieldSetEditable(editable)
        else:
            self._text.TextSetEditable(editable)

    def selectitem(self, pos):
        _List.selectitem(self, pos)
        pos = self.getselected()
        if pos is None:
            text = ''
        else:
            text = self.getlistitem(pos)
        self._text.TextFieldSetString(text)
        if text:
            self._text.TextFieldSetSelection(0, len(text), 0)

    def _destroy(self, widget, value, call_data):
        _Widget._destroy(self, widget, value, call_data)
        _List._destroy(self)
        del self._text

class List(_Widget, _List):
    def __init__(self, parent, listprompt, itemlist, sel_cb,
                 rows = 10, useGadget = _def_useGadget,
                 name = 'windowList', tooltip = None, **options):
        attrs = {'resizePolicy': parent.resizePolicy}
        self._attachments(attrs, options)
        if listprompt is not None:
            if useGadget:
                labelwidget = Xm.LabelGadget
            else:
                labelwidget = Xm.Label
            form = parent._form.CreateManagedWidget(
                    'windowListForm', Xm.Form, attrs)
            label = form.CreateManagedWidget(name + 'Label',
                            labelwidget,
                            {'topAttachment': Xmd.ATTACH_FORM,
                             'leftAttachment': Xmd.ATTACH_FORM,
                             'rightAttachment': Xmd.ATTACH_FORM})
            self._label = label
            label.labelString = listprompt
            attrs = {'topAttachment': Xmd.ATTACH_WIDGET,
                     'topWidget': label,
                     'leftAttachment': Xmd.ATTACH_FORM,
                     'rightAttachment': Xmd.ATTACH_FORM,
                     'bottomAttachment': Xmd.ATTACH_FORM,
                     'visibleItemCount': rows,
                     'selectionPolicy': Xmd.SINGLE_SELECT}
            if options.has_key('width'):
                attrs['width'] = options['width']
            if parent.resizePolicy == Xmd.RESIZE_ANY:
                attrs['listSizePolicy'] = \
                                        Xmd.RESIZE_IF_POSSIBLE
            else:
                attrs['listSizePolicy'] = Xmd.CONSTANT
            list = form.CreateScrolledList(name, attrs)
            list.ManageChild()
            widget = form
            self._text = listprompt
        else:
            attrs['visibleItemCount'] = rows
            attrs['selectionPolicy'] = Xmd.SINGLE_SELECT
            if parent.resizePolicy == Xmd.RESIZE_ANY:
                attrs['listSizePolicy'] = \
                                        Xmd.RESIZE_IF_POSSIBLE
            else:
                attrs['listSizePolicy'] = Xmd.CONSTANT
            if options.has_key('width'):
                attrs['width'] = options['width']
            list = parent._form.CreateScrolledList(name, attrs)
            widget = list
            self._text = '<None>'
        _List.__init__(self, list, itemlist, 0, sel_cb)
        _Widget.__init__(self, parent, widget, tooltip)

    def __repr__(self):
        return '<List instance at %x; label=%s>' % (id(self), self._text)

    def close(self):
        _List.close(self)
        _Widget.close(self)

    def setlabel(self, label):
        try:
            self._label.labelString = label
        except AttributeError:
            raise error, 'List created without label'
        else:
            self._text = label

    def _destroy(self, widget, value, call_data):
        try:
            del self._label
        except AttributeError:
            pass
        _Widget._destroy(self, widget, value, call_data)
        _List._destroy(self)

class TextInput(_Widget):
    def __init__(self, parent, prompt, inittext, chcb, accb,
                 useGadget = _def_useGadget, name = 'windowTextfield',
                 modifyCB = None, tooltip = None, **options):
        attrs = {}
        self._attachments(attrs, options)
        if prompt is not None:
            if useGadget:
                labelwidget = Xm.LabelGadget
            else:
                labelwidget = Xm.Label
            form = parent._form.CreateManagedWidget(
                    name + 'Form', Xm.Form, attrs)
            label = form.CreateManagedWidget(
                    name + 'Label', labelwidget,
                    {'topAttachment': Xmd.ATTACH_FORM,
                     'leftAttachment': Xmd.ATTACH_FORM,
                     'bottomAttachment': Xmd.ATTACH_FORM})
            self._label = label
            label.labelString = prompt
            attrs = {'topAttachment': Xmd.ATTACH_FORM,
                     'leftAttachment': Xmd.ATTACH_WIDGET,
                     'leftWidget': label,
                     'bottomAttachment': Xmd.ATTACH_FORM,
                     'rightAttachment': Xmd.ATTACH_FORM}
            widget = form
        else:
            form = parent._form
            widget = None
        if options.has_key('columns'):
            attrs['columns'] = options['columns']
        attrs['value'] = inittext
        editable = options.get('editable', 1)
        if not editable:
            attrs['editable'] = 0
        self._text = text = form.CreateTextField(name, attrs)
        text.ManageChild()
        if widget is None:
            widget = text
        if chcb:
            text.AddCallback('valueChangedCallback',
                             self._callback, chcb)
        if accb:
            text.AddCallback('activateCallback',
                             self._callback, accb)
        if modifyCB:
            text.AddCallback('modifyVerifyCallback',
                             self._modifyCB, modifyCB)
        _Widget.__init__(self, parent, widget, tooltip)

    def __repr__(self):
        return '<TextInput instance at %x>' % id(self)

    def close(self):
        _Widget.close(self)
        self._text = None

    def setlabel(self, label):
        if not hasattr(self, '_label'):
            raise error, 'TextInput create without label'
        self._label.labelString = label

    def gettext(self):
        return self._text.TextFieldGetString()

    def settext(self, text):
        self._text.value = text

    def setfocus(self):
        self._text.ProcessTraversal(Xmd.TRAVERSE_CURRENT)

    def _modifyCB(self, w, func, call_data):
        text = func(call_data.text)
        if text is not None:
            call_data.text = text
        toplevel.setready()

    def _destroy(self, widget, value, call_data):
        _Widget._destroy(self, widget, value, call_data)
        try:
            del self._label
        except AttributeError:
            pass
        del self._text

class TextEdit(_Widget):
    def __init__(self, parent, inittext, cb, name = 'windowText',
                 tooltip = None, **options):
        attrs = {'editMode': Xmd.MULTI_LINE_EDIT,
                 'editable': TRUE,
                 'rows': 10}
        for option in ['editable', 'rows', 'columns']:
            if options.has_key(option):
                attrs[option] = options[option]
        if not attrs['editable']:
            attrs['cursorPositionVisible'] = FALSE
        self._attachments(attrs, options)
        text = parent._form.CreateScrolledText(name, attrs)
        if cb:
            text.AddCallback('activateCallback', self._callback,
                             cb)
        _Widget.__init__(self, parent, text, tooltip)
        self.settext(inittext)

    def __repr__(self):
        return '<TextEdit instance at %x>' % id(self)

    def settext(self, text):
        if type(text) is ListType:
            text = string.join(text, '\n')
        self._form.TextSetString(text)
        self._linecache = None

    def gettext(self):
        return self._form.TextGetString()

    def getlines(self):
        text = self.gettext()
        text = string.split(text, '\n')
        if len(text) > 0 and text[-1] == '':
            del text[-1]
        return text

    def _mklinecache(self):
        text = self.getlines()
        self._linecache = c = []
        pos = 0
        for line in text:
            c.append(pos)
            pos = pos + len(line) + 1

    def getline(self, line):
        lines = self.getlines()
        if line < 0 or line >= len(lines):
            line = len(lines) - 1
        return lines[line]

    def scrolltext(self, line, where):
        if not self._linecache:
            self._mklinecache()
        if line < 0 or line >= len(self._linecache):
            line = len(self._linecache) - 1
        if where == TOP:
            pass
        else:
            rows = self._form.rows
            if where == BOTTOM:
                line = line - rows + 1
            elif where == CENTER:
                line = line - rows/2 + 1
            else:
                raise error, 'bad argument for scrolltext'
            if line < 0:
                line = 0
        self._form.TextSetTopCharacter(self._linecache[line])

    def selectchars(self, line, start, end):
        if not self._linecache:
            self._mklinecache()
        if line < 0 or line >= len(self._linecache):
            line = len(self._linecache) - 1
        pos = self._linecache[line]
        self._form.TextSetSelection(pos + start, pos + end, 0)

    def _destroy(self, widget, value, call_data):
        _Widget._destroy(self, widget, value, call_data)
        del self._linecache

class ListEdit(_Widget):
    def __init__(self, parent, prompt, inittext, cb, itemlist, useGadget = _def_useGadget, name = 'listEdit', **options):
        attrs = {}
        self._attachments(attrs, options)
        listedit = parent._form.CreateManagedWidget(name, Xm.Form, attrs)
        if not inittext:
            inittext = ''
        arrow = listedit.CreateManagedWidget(
                name + 'Arrow', Xm.ArrowButton,
                {'arrowDirection': Xmd.ARROW_DOWN,
                 'rightAttachment': Xmd.ATTACH_FORM,
                 'bottomAttachment': Xmd.ATTACH_FORM,
                 'topAttachment': Xmd.ATTACH_FORM})
        arrow.AddCallback('activateCallback', self.__arrowcb, None)
        attrs = {'topAttachment': Xmd.ATTACH_FORM,
                 'bottomAttachment': Xmd.ATTACH_FORM,
                 'leftAttachment': Xmd.ATTACH_FORM,
                 'rightAttachment': Xmd.ATTACH_WIDGET,
                 'rightWidget': arrow,
##              'rightOffset': 20,
                 'value': inittext}
        if prompt is not None:
            label = listedit.CreateManagedWidget(
                    name + 'Label', Xm.Label,
                    {'topAttachment': Xmd.ATTACH_FORM,
                     'bottomAttachment': Xmd.ATTACH_FORM,
                     'leftAttachment': Xmd.ATTACH_FORM})
            label.labelString = prompt
            attrs['leftAttachment'] = Xmd.ATTACH_WIDGET
            attrs['leftWidget'] = label
        textfield = listedit.CreateManagedWidget(name + 'TextField',
                                                 Xm.TextField, attrs)
        if cb:
            textfield.AddCallback('activateCallback',
                                  self._callback, cb)
        popup = toplevel._main.CreatePopupShell(
                name + 'Shell', Xt.OverrideShell,
                {'colormap': toplevel._default_colormap,
                 'visual': toplevel._default_visual,
                 'depth': toplevel._default_visual.depth})
        list = popup.CreateScrolledList(name + 'List',
                                {'selectionPolicy': Xmd.BROWSE_SELECT,
                                 'listSizePolicy': Xmd.CONSTANT,
                                 'scrollingPolicy': Xmd.AUTOMATIC,
                                 'scrollBarDisplayPolicy': Xmd.STATIC,
                                 'visibleItemCount': 5, 'width': 250})
        list.AddCallback('browseSelectionCallback', self.__listcb, None)
        list.ManageChild()
        list.ListAddItems(itemlist, 1)

        _Widget.__init__(self, parent, listedit)
        self.__popped = 0
        self.__arrow = arrow
        self.__textfield = textfield
        self.__list = list
        self.__itemlist = itemlist
        self.__popup = popup
        self.__cursor = None

    def _destroy(self, widget, client_data, call_data):
        del self.__arrow
        del self.__textfield
        del self.__list
        del self.__itemlist
        self.__popup.DestroyWidget()
        del self.__popup
        _Widget._destroy(self, widget, client_data, call_data)
        del self.__cursor

    def __arrowcb(self, widget, client_data, call_data):
        if self.__popped:
            self.__popup.Popdown()
            self.__popped = 0
            self.__arrow.arrowDirection = Xmd.ARROW_DOWN
            return
        self.__arrow.arrowDirection = Xmd.ARROW_LEFT
        x, y = widget.TranslateCoords(0, 0)
        width = self.__popup.width or self.__list.width
        self.__popup.SetValues({'x': x - width, 'y': y - 10})
        self.__list.ManageChild()
        self.__popup.Popup(Xtdefs.XtGrabExclusive)
        if self.__cursor is None:
            # default cursor is an X which is not very convenient
            import Xcursorfont
            self.__cursor = self.__popup.Display().CreateFontCursor(Xcursorfont.arrow)
            self.__popup.DefineCursor(self.__cursor)
        self.__arrow.AddGrab(0, 0)
        self.__popped = 1

    def __listcb(self, widget, client_data, call_data):
        self.__popup.Popdown()
        self.__arrow.arrowDirection = Xmd.ARROW_DOWN
        pos = self.__list.ListGetSelectedPos()
        if not pos:
            return
        pos = pos[0] - 1
        self.__textfield.TextFieldSetString(self.__itemlist[pos])

    def setlist(self, itemlist):
        self.__list.ListDeleteAllItems()
        self.__list.ListAddItems(itemlist, 1)
        self.__itemlist = itemlist

    def settext(self, text):
        self.__textfield.TextFieldSetString(text)

    def gettext(self):
        return self.__textfield.TextFieldGetString()

class Html(_Widget):
    # This class implements an extremely simplistic HTML browser.
    # When following a link, the html widget is re-created.  This
    # is a kludge to get around the problem that the View widget
    # doesn't seem to get any events anymore when a new page is
    # loaded.  This resulted in the impossibility to scroll the
    # window and follow links.
    def __init__(self, parent, url, name = 'windowHtml', **options):
        self.__name = name
        self.url = None
        attrs = {'width': 600, 'height': 400,
                 'borderWidth': 0, 'marginWidth': 0,
                 'borderHeight': 0, 'marginHeight': 0}
        self._attachments(attrs, options)
        form = parent._form.CreateManagedWidget(name+'Form',
                                                Xm.DrawingArea, attrs)
        self.__htmlw = None
        _Widget.__init__(self, parent, form)
        form.AddCallback('resizeCallback', self.__resize, None)
        if url:
            self.goto_url(url)

    def __resize(self, form, client_data, call_data):
        if self.__htmlw is not None:
            self.__htmlw.SetValues(
                    form.GetValues(['width', 'height']))

    def __cblink(self, htmlw, client_data, call_data):
        href = call_data.href
        if href:
            self.url = href

    def __cbanchor(self, htmlw, client_data, call_data):
        self.goto_url(call_data.href)

    def __resolveImage(self, htmlw, src, noload = 0):
        from MMurl import basejoin
        from XHtml import resolveImage
        src = basejoin(self.url, src)
        return resolveImage(htmlw, src, noload)

    def __destroy(self, htmlw, client_data, call_data):
        htmlw.FreeImageInfo()

    def goto_url(self, url):
        import MMurl, HTML
        if self.url:
            url = MMurl.basejoin(self.url, url)
        self.url, tag = MMurl.splittag(url)
        try:
            fn, hdrs = MMurl.urlretrieve(self.url)
        except IOError:
            import sys
            text = '<H1>Cannot Open</H1><P>'+ \
                      'Cannot open '+self.url+':<P>'+ \
                      `(sys.exc_type, sys.exc_value)`+ \
                      '<P>\n'
        else:
            if hdrs.has_key('Content-Location'):
                self.url = hdrs['Content-Location']
            text = open(fn, 'rb').read()
        if self.__htmlw is not None:
            self.__htmlw.DestroyWidget()
        attrs = {'x': 0, 'y': 0,
                 'resolveImageFunction': self.__resolveImage,
                 'resolveDelayedImage': self.__resolveImage}
        attrs.update(self._form.GetValues(['width', 'height']))
        html = self._form.CreateManagedWidget(self.__name, HTML.html,
                                              attrs)
        html.AddCallback('anchorCallback', self.__cbanchor, None)
        html.AddCallback('linkCallback', self.__cblink, None)
        html.AddCallback('destroyCallback', self.__destroy, None)
        self.__htmlw = html
        html.SetText(text, '', '', 0, tag)

class Separator(_Widget):
    def __init__(self, parent, useGadget = _def_useGadget,
                 name = 'windowSeparator', vertical = 0,
                 tooltip = None, **options):
        attrs = {}
        if vertical:
            attrs['orientation'] = Xmd.VERTICAL
        else:
            attrs['orientation'] = Xmd.HORIZONTAL
        self._attachments(attrs, options)
        if useGadget and tooltip is None:
            separator = Xm.SeparatorGadget
        else:
            separator = Xm.Separator
        separator = parent._form.CreateManagedWidget(name, separator,
                                                     attrs)
        _Widget.__init__(self, parent, separator, tooltip)

    def __repr__(self):
        return '<Separator instance at %x>' % id(self)

class ButtonRow(_Widget, _ButtonSupport):
    def __init__(self, parent, buttonlist,
                 vertical = 1, callback = None,
                 useGadget = _def_useGadget,
                 name = 'windowRowcolumn', **options):
        attrs = {'entryAlignment': Xmd.ALIGNMENT_CENTER,
                 'traversalOn': FALSE}
        if not vertical:
            attrs['orientation'] = Xmd.HORIZONTAL
        if options.get('tight', 0):
            attrs['packing'] = Xmd.PACK_COLUMN
        if useGadget:
            separator = Xm.SeparatorGadget
        else:
            separator = Xm.Separator
        self._attachments(attrs, options)
        rowcolumn = parent._form.CreateManagedWidget(name,
                                                Xm.RowColumn, attrs)
        _Widget.__init__(self, parent, rowcolumn)
        self._buttons = []
        for entry in buttonlist:
            if entry is None:
                if vertical:
                    attrs = {'orientation': Xmd.HORIZONTAL}
                else:
                    attrs = {'orientation': Xmd.VERTICAL}
                dummy = rowcolumn.CreateManagedWidget(
                        'buttonSeparator', separator, attrs)
                continue
            if type(entry) is TupleType and len(entry) > 3:
                entry = entry[0], entry[1], entry[2:]
            button = self._create_button(rowcolumn, toplevel.
                    _default_visual, toplevel._default_colormap,
                    entry, callback)
            self._buttons.append(button)

    def __repr__(self):
        return '<ButtonRow instance at %x>' % id(self)

    def close(self):
        _Widget.close(self)
        self._buttons = None

    def hide(self, button = None):
        if button is None:
            _Widget.hide(self)
            return
        if not 0 <= button < len(self._buttons):
            raise error, 'button number out of range'
        self._buttons[button].UnmanageChild()

    def show(self, button = None):
        if button is None:
            _Widget.show(self)
            return
        if not 0 <= button < len(self._buttons):
            raise error, 'button number out of range'
        self._buttons[button].ManageChild()

    def getbutton(self, button):
        if not 0 <= button < len(self._buttons):
            raise error, 'button number out of range'
        return self._buttons[button].set

    def setbutton(self, button, onoff = 1):
        if not 0 <= button < len(self._buttons):
            raise error, 'button number out of range'
        button = self._buttons[button]
        button.set = onoff

    def setsensitive(self, button, sensitive):
        if not 0 <= button < len(self._buttons):
            raise error, 'button number out of range'
        self._buttons[button].SetSensitive(sensitive)

    def _popup(self, widget, submenu, call_data):
        submenu.ManageChild()

    def _destroy(self, widget, value, call_data):
        _Widget._destroy(self, widget, value, call_data)
        del self._buttons

class Slider(_Widget):
    def __init__(self, parent, prompt, minimum, initial, maximum, cb,
                 vertical = 0, showvalue = 1, name = 'windowScale',
                 tooltip = None, **options):
        if vertical:
            orientation = Xmd.VERTICAL
        else:
            orientation = Xmd.HORIZONTAL
        self._orientation = orientation
        direction, minimum, initial, maximum, decimal, factor = \
                   self._calcrange(minimum, initial, maximum)
        attrs = {'minimum': minimum,
                 'maximum': maximum,
                 'processingDirection': direction,
                 'decimalPoints': decimal,
                 'orientation': orientation,
                 'showValue': showvalue,
                 'value': initial}
        self._attachments(attrs, options)
        scale = parent._form.CreateScale(name, attrs)
        if cb:
            scale.AddCallback('valueChangedCallback',
                              self._callback, cb)
        if prompt is None:
            for w in scale.GetChildren():
                if w.Name() == 'Title':
                    w.UnmanageChild()
                    break
        else:
            scale.titleString = prompt
        _Widget.__init__(self, parent, scale, tooltip)

    def __repr__(self):
        return '<Slider instance at %x>' % id(self)

    def getvalue(self):
        return self._form.ScaleGetValue() / self._factor

    def setvalue(self, value):
        value = int(value * self._factor + .5)
        self._form.ScaleSetValue(value)

    def setrange(self, minimum, maximum):
        direction, minimum, initial, maximum, decimal, factor = \
                   self._calcrange(minimum, self.getvalue(), maximum)
        self._form.SetValues({'minimum': minimum,
                              'maximum': maximum,
                              'processingDirection': direction,
                              'decimalPoints': decimal,
                              'value': initial})

    def getrange(self):
        return self._minimum, self._maximum

    def _calcrange(self, minimum, initial, maximum):
        self._minimum, self._maximum = minimum, maximum
        range = maximum - minimum
        if range < 0:
            if self._orientation == Xmd.VERTICAL:
                direction = Xmd.MAX_ON_BOTTOM
            else:
                direction = Xmd.MAX_ON_LEFT
            range = -range
            minimum, maximum = maximum, minimum
        else:
            if self._orientation == Xmd.VERTICAL:
                direction = Xmd.MAX_ON_TOP
            else:
                direction = Xmd.MAX_ON_RIGHT
        decimal = 0
        factor = 1
        if FloatType in [type(minimum), type(maximum)]:
            factor = 1.0
        while 0 < range <= 10:
            range = range * 10
            decimal = decimal + 1
            factor = factor * 10
        self._factor = factor
        return direction, int(minimum * factor + .5), \
               int(initial * factor + .5), \
               int(maximum * factor + .5), decimal, factor

class _WindowHelpers:
    def __init__(self):
        self._fixkids = []
        self._fixed = FALSE
        self._children = []

    def close(self):
        self._fixkids = None
        for w in self._children[:]:
            w.close()

    # items with which a window can be filled in
    def Label(self, text, **options):
        return apply(Label, (self, text), options)
    def Button(self, label, callback, **options):
        return apply(Button, (self, label, callback), options)
    def OptionMenu(self, label, optionlist, startpos, cb, **options):
        return apply(OptionMenu,
                     (self, label, optionlist, startpos, cb),
                     options)
    def PulldownMenu(self, menulist, **options):
        return apply(PulldownMenu, (self, menulist), options)
    def Selection(self, listprompt, itemprompt, itemlist, initial, sel_cb,
                  **options):
        return apply(Selection,
                     (self, listprompt, itemprompt, itemlist, initial,
                      sel_cb),
                     options)
    def List(self, listprompt, itemlist, sel_cb, **options):
        return apply(List,
                     (self, listprompt, itemlist, sel_cb), options)
    def TextInput(self, prompt, inittext, chcb, accb, **options):
        return apply(TextInput,
                     (self, prompt, inittext, chcb, accb), options)
    def TextEdit(self, inittext, cb, **options):
        return apply(TextEdit, (self, inittext, cb), options)
    def ListEdit(self, prompt, inittext, cb, itemlist, **options):
        return apply(ListEdit, (self, prompt, inittext, cb, itemlist),
                     options)
    def Html(self, url, **options):
        return apply(Html, (self, url), options)
    def Separator(self, **options):
        return apply(Separator, (self,), options)
    def ButtonRow(self, buttonlist, **options):
        return apply(ButtonRow, (self, buttonlist), options)
    def Slider(self, prompt, minimum, initial, maximum, cb, **options):
        return apply(Slider,
                     (self, prompt, minimum, initial, maximum, cb),
                     options)
    def ScrolledWindow(self, **options):
        return apply(ScrolledWindow, (self,), options)
    def SubWindow(self, **options):
        return apply(SubWindow, (self,), options)
    def AlternateSubWindow(self, **options):
        return apply(AlternateSubWindow, (self,), options)

class ScrolledWindow(_Widget, _WindowHelpers):
    def __init__(self, parent, name = 'windowScrolledWindow', **options):
        attrs = {'resizePolicy': parent.resizePolicy}
        self.resizePolicy = parent.resizePolicy
        self._attachments(attrs, options)
        self._attrs(attrs, options,
                    ['clipWindow', 'horizontalScrollBar', 'scrollBarDisplayPolicy',
                     'scrollBarPlacement', 'scrolledWindowMarginHeight',
                     'scrolledWindowMarginWidth', 'scrollingPolicy',
                     'spacing', 'traverseObscuredCallback',
                     'verticalScrollBar', 'visualPolicy',
                     'workWindow'
                    ])
        if not attrs.has_key('visualPolicy'):
            attrs['visualPolicy'] = Xmd.CONSTANT
        if not attrs.has_key('scrollingpolicy'):
            attrs['scrollingPolicy'] = Xmd.AUTOMATIC
        form = parent._form.CreateManagedWidget(name,
                                                Xm.ScrolledWindow,
                                                attrs)
        _Widget.__init__(self, parent, form)
        parent._fixkids.append(self)
        self._fixkids = []
        self._children = []

    def __repr__(self):
        return '<ScrolledWindow instance at %x>' % id(self)

    def close(self):
        _Widget.close(self)
        _WindowHelpers.close(self)

    def fix(self):
        for w in self._fixkids:
            w.fix()
        self._form.ManageChild()
        self._fixed = TRUE

    def show(self):
        _Widget.show(self)
        if self._fixed:
            for w in self._fixkids:
                if w.is_showing():
                    w.show()
                else:
                    w.hide()
            self._fixkids = []

    def _attrs(self, attr, options, lst):
        for name in lst:
            if options.has_key(name):
                attr[name] = options[name]

class SubWindow(_Widget, _WindowHelpers):
    def __init__(self, parent, name = 'windowSubwindow', **options):
        attrs = {'resizePolicy': parent.resizePolicy}
        horizontalSpacing = options.get('horizontalSpacing')
        if horizontalSpacing is not None:
            attrs['horizontalSpacing'] = horizontalSpacing
        verticalSpacing = options.get('verticalSpacing')
        if verticalSpacing is not None:
            attrs['verticalSpacing'] = verticalSpacing
        self.resizePolicy = parent.resizePolicy
        self._attachments(attrs, options)
        form = parent._form.CreateManagedWidget(name, Xm.Form, attrs)
        _WindowHelpers.__init__(self)
        _Widget.__init__(self, parent, form)
        parent._fixkids.append(self)

    def __repr__(self):
        return '<SubWindow instance at %x>' % id(self)

    def close(self):
        _Widget.close(self)
        _WindowHelpers.close(self)

    def fix(self):
        for w in self._fixkids:
            w.fix()
        self._form.ManageChild()
        self._fixed = TRUE

    def show(self):
        _Widget.show(self)
        if self._fixed:
            for w in self._fixkids:
                if w.is_showing():
                    w.show()
                else:
                    w.hide()
            self._fixkids = []

class _AltSubWindow(SubWindow):
    def __init__(self, parent, name):
        self._parent = parent
        SubWindow.__init__(self, parent, left = None, right = None,
                           top = None, bottom = None, name = name)

    def show(self):
        for w in self._parent._windows:
            w.hide()
        SubWindow.show(self)

class AlternateSubWindow(_Widget):
    def __init__(self, parent, name = 'windowAlternateSubwindow',
                 **options):
        attrs = {'resizePolicy': parent.resizePolicy,
                 'allowOverlap': TRUE}
        self.resizePolicy = parent.resizePolicy
        self._attachments(attrs, options)
        form = parent._form.CreateManagedWidget(name, Xm.Form, attrs)
        self._windows = []
        _Widget.__init__(self, parent, form)
        parent._fixkids.append(self)
        self._fixkids = []
        self._children = []

    def __repr__(self):
        return '<AlternateSubWindow instance at %x>' % id(self)

    def close(self):
        _Widget.close(self)
        self._windows = None
        self._fixkids = None

    def SubWindow(self, name = 'windowSubwindow'):
        widget = _AltSubWindow(self, name = name)
        for w in self._windows:
            w.hide()
        self._windows.append(widget)
        return widget

    def fix(self):
        for w in self._fixkids:
            w.fix()
        for w in self._windows:
            w._form.ManageChild()

class Window(_WindowHelpers, _MenuSupport, _CommandSupport):
    _cursor = ''
    def __init__(self, title, resizable = 0, grab = 0,
                 Name = 'windowShell', Class = None, **options):
        _CommandSupport.__init__(self)
        if not resizable:
            self.resizePolicy = Xmd.RESIZE_NONE
        else:
            self.resizePolicy = Xmd.RESIZE_ANY
        if not title:
            title = ''
        self._title = title
        wattrs = {'title': title,
                  'minWidth': 60, 'minHeight': 60,
                  'colormap': toplevel._default_colormap,
                  'visual': toplevel._default_visual,
                  'depth': toplevel._default_visual.depth}
        width = options.get('width')
        if width is not None:
            wattrs['width'] = int(float(width) * toplevel._hmm2pxl + 0.5)
        height = options.get('height')
        if height is not None:
            wattrs['height'] = int(float(height) * toplevel._vmm2pxl + 0.5)
        x = options.get('x')
        y = options.get('y')
        if x is not None and y is not None:
            wattrs['geometry'] = '+%d+%d' % (int(float(x) * toplevel._hmm2pxl + 0.5), int(float(y) * toplevel._vmm2pxl + 0.5))
        attrs = {'allowOverlap': FALSE,
                 'resizePolicy': self.resizePolicy}
        if not resizable:
            attrs['noResize'] = TRUE
            attrs['resizable'] = FALSE
        horizontalSpacing = options.get('horizontalSpacing')
        if horizontalSpacing is not None:
            attrs['horizontalSpacing'] = horizontalSpacing
        verticalSpacing = options.get('verticalSpacing')
        if verticalSpacing is not None:
            attrs['verticalSpacing'] = verticalSpacing
        if grab:
            attrs['dialogStyle'] = \
                                 Xmd.DIALOG_FULL_APPLICATION_MODAL
            parent = options.get('parent')
            if parent is None:
                parent = toplevel
            while 1:
                if hasattr(parent, '_shell'):
                    parent = parent._shell
                    break
                if hasattr(parent, '_main'):
                    parent = parent._main
                    break
                if hasattr(parent, '_parent'):
                    parent = parent._parent
                else:
                    parent = toplevel
            for key, val in wattrs.items():
                attrs[key] = val
            self._form = parent.CreateFormDialog('grabDialog', attrs)
            self._main = self._form
        else:
            wattrs['iconName'] = title
            self._shell = toplevel._main.CreatePopupShell(Name,
                    Xt.ApplicationShell, wattrs)
            self._form = self._shell.CreateManagedWidget(
                    'windowForm', Xm.Form, attrs)
            if options.has_key('deleteCallback'):
                deleteCallback = options['deleteCallback']
                if type(deleteCallback) is ListType:
                    self._set_deletecommands(deleteCallback)
                    deleteCallback = None
                self._shell.AddWMProtocolCallback(
                        toplevel._delete_window,
                        self._delete_callback,
                        deleteCallback)
                self._shell.deleteResponse = Xmd.DO_NOTHING
        self._showing = FALSE
        self._not_shown = []
        self._shown = []
        _WindowHelpers.__init__(self)
        _MenuSupport.__init__(self)
        toplevel._subwindows.append(self)
        self.setcursor(_WAITING_CURSOR)

    def __repr__(self):
        s = '<Window instance at %x' % id(self)
        if hasattr(self, '_title'):
            s = s + ', title=' + `self._title`
        if self.is_closed():
            s = s + ' (closed)'
        elif self._showing:
            s = s + ' (showing)'
        s = s + '>'
        return s

    def close(self):
        try:
            form = self._form
        except AttributeError:
            return
        _CommandSupport.close(self)
        try:
            shell = self._shell
        except AttributeError:
            shell = None
            del self._main
        toplevel._subwindows.remove(self)
        del self._form
        form.DestroyWidget()
        del form
        if shell:
            shell.UnmanageChild()
            shell.DestroyWidget()
            del self._shell
            del shell
        _WindowHelpers.close(self)
        _MenuSupport.close(self)

    def is_closed(self):
        return not hasattr(self, '_form')

    def setcursor(self, cursor):
        if cursor == _WAITING_CURSOR:
            cursor = 'watch'
        elif cursor == _READY_CURSOR:
            cursor = self._cursor
        else:
            self._cursor = cursor
        if toplevel._waiting:
            cursor = 'watch'
        _setcursor(self._form, cursor)

    def fix(self):
        for w in self._fixkids:
            w.fix()
        self._form.ManageChild()
        try:
            self._shell.RealizeWidget()
        except AttributeError:
            pass
        self._fixed = TRUE

    def _showme(self, w):
        if self.is_closed():
            return
        if self.is_showing():
            if not w._form.IsSubclass(Xm.Gadget):
                w._form.MapWidget()
        elif w in self._not_shown:
            self._not_shown.remove(w)
        elif w not in self._shown:
            self._shown.append(w)

    def _hideme(self, w):
        if self.is_closed():
            return
        if self.is_showing():
            if not w._form.IsSubclass(Xm.Gadget):
                w._form.UnmapWidget()
        elif w in self._shown:
            self._shown.remove(w)
        elif w not in self._not_shown:
            self._not_shown.append(w)

    def show(self):
        if not self._fixed:
            self.fix()
        try:
            self._shell.Popup(Xtdefs.XtGrabNone)
        except AttributeError:
            pass
        self._showing = TRUE
        for w in self._not_shown:
            if not w.is_closed() and \
               not w._form.IsSubclass(Xm.Gadget):
                w._form.UnmapWidget()
        for w in self._shown:
            if not w.is_closed() and \
               not w._form.IsSubclass(Xm.Gadget):
                w._form.MapWidget()
        self._not_shown = []
        self._shown = []
        for w in self._fixkids:
            if w.is_showing():
                w.show()
            else:
                w.hide()
        self._fixkids = []

    def hide(self):
        try:
            self._shell.Popdown()
        except AttributeError:
            pass
        self._showing = FALSE

    def is_showing(self):
        return self._showing

    def settitle(self, title):
        if self._title != title:
            try:
                self._shell.title = title
                self._shell.iconName = title
            except AttributeError:
                self._form.dialogTitle = title
            self._title = title

    def getgeometry(self):
        if self.is_closed():
            raise error, 'window already closed'
        x, y  = self._form.TranslateCoords(0, 0)
        val = self._form.GetValues(['width', 'height'])
        w = val['width']
        h = val['height']
        return x / toplevel._hmm2pxl, y / toplevel._vmm2pxl, \
               w / toplevel._hmm2pxl, h / toplevel._vmm2pxl

    def pop(self):
        try:
            self._shell.Popup(0)
        except AttributeError:
            pass

    def _delete_callback(self, widget, client_data, call_data):
        if type(client_data) is StringType:
            if client_data == 'hide':
                self.hide()
            elif client_data == 'close':
                self.close()
            else:
                raise error, 'bad deleteCallback argument'
            return
        if not _CommandSupport._delete_callback(self, widget,
                                        client_data, call_data):
            apply(apply, client_data)
        toplevel.setready()
