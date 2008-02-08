__version__ = "$Id$"

import Xm, Xmd
from types import *
from XConstants import _def_useGadget
from XConstants import error
from XTopLevel import toplevel

def _setcursor(form, cursor):
    if not form.IsRealized():
        return
    if cursor == 'hand':
        form.DefineCursor(toplevel._handcursor)
    elif cursor == '':
        form.UndefineCursor()
    elif cursor == 'watch':
        form.DefineCursor(toplevel._watchcursor)
    elif cursor == 'channel':
        form.DefineCursor(toplevel._channelcursor)
    elif cursor == 'link':
        form.DefineCursor(toplevel._linkcursor)
    elif cursor == 'stop':
        form.DefineCursor(toplevel._stopcursor)
    else:
        raise error, 'unknown cursor glyph'

def _generic_callback(widget, callback, call_data):
    apply(apply, callback)
    toplevel.setready()

def _create_menu(menu, list, visual, colormap, acc = None, widgets = None):
    if widgets is None:
        widgets = {}
    if len(list) > 30:
        menu.numColumns = (len(list) + 29) / 30
        menu.packing = Xmd.PACK_COLUMN
    if _def_useGadget:
        separator = Xm.SeparatorGadget
        label = Xm.LabelGadget
        cascade = Xm.CascadeButtonGadget
        toggle = Xm.ToggleButtonGadget
        pushbutton = Xm.PushButtonGadget
    else:
        separator = Xm.Separator
        label = Xm.Label
        cascade = Xm.CascadeButton
        toggle = Xm.ToggleButton
        pushbutton = Xm.PushButton
    accelerator = None
    for entry in list:
        if entry is None:
            dummy = menu.CreateManagedWidget('separator',
                                             separator, {})
            continue
        if type(entry) is StringType:
            dummy = menu.CreateManagedWidget(
                    'menuLabel', label,
                    {'labelString': entry})
            widgets[entry] = dummy, None
            continue
        btype = 'p'             # default is pushbutton
        initial = 0
        if acc is None:
            labelString, callback = entry[:2]
            if len(entry) > 2:
                btype = entry[2]
                if len(entry) > 3:
                    initial = entry[3]
        else:
            accelerator, labelString, callback = entry[:3]
            if len(entry) > 3:
                btype = entry[3]
                if len(entry) > 4:
                    initial = entry[4]
        if type(callback) is ListType:
            submenu = menu.CreatePulldownMenu('submenu',
                    {'colormap': colormap,
                     'visual': visual,
                     'depth': visual.depth,
                     'orientation': Xmd.VERTICAL,
                     'tearOffModel': Xmd.TEAR_OFF_ENABLED})
            button = menu.CreateManagedWidget(
                    'submenuLabel', cascade,
                    {'labelString': labelString, 'subMenuId': submenu})
            subwidgets = {}
            widgets[labelString] = button, subwidgets
            _create_menu(submenu, callback, visual, colormap, acc,
                         subwidgets)
        else:
            if type(callback) is not TupleType:
                callback = (callback, (labelString,))
            attrs = {'labelString': labelString}
            if accelerator:
                if type(accelerator) is not StringType or \
                   len(accelerator) != 1:
                    raise error, 'menu accelerator must be single character'
                acc[accelerator] = callback
                attrs['acceleratorText'] = accelerator
            if btype == 't':
                attrs['set'] = initial
                button = menu.CreateManagedWidget('menuToggle',
                                toggle, attrs)
                cbfunc = 'valueChangedCallback'
            else:
                button = menu.CreateManagedWidget('menuLabel',
                                pushbutton, attrs)
                cbfunc = 'activateCallback'
            button.AddCallback(cbfunc, _generic_callback, callback)
            widgets[labelString] = button, None
