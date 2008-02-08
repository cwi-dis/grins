__version__ = "$Id$"

import Xm, Xmd
from types import ListType
from XTopLevel import toplevel
from XCommand import _CommandSupport
from XButtonSupport import _ButtonSupport
from XHelpers import _create_menu
from XConstants import error

class _AdornmentSupport(_CommandSupport, _ButtonSupport):
    def __init__(self):
        _CommandSupport.__init__(self)
        self.__dynamicmenu = {}
        self.__popupmenutemplate = None

    def close(self):
        _CommandSupport.close(self)
        del self.__dynamicmenu

    def set_dynamiclist(self, command, list):
        cmd = self._get_commandinstance(command)
        if cmd is None:
            return
        if not cmd.dynamiccascade:
            raise error, 'non-dynamic command in set_dynamiclist'
        callback = cmd.callback
        menu = []
        for entry in list:
            entry = (entry[0], (callback, entry[1])) + entry[2:]
            menu.append(entry)
        for widget in self._get_commandwidgets(command):
            if self.__dynamicmenu.get(widget) == menu:
                continue
            submenu = widget.subMenuId
            for w in submenu.children or []:
                w.DestroyWidget()
            if not list:
                if widget.sensitive:
                    widget.SetSensitive(0)
                continue
            if not widget.sensitive:
                widget.SetSensitive(1)
            _create_menu(submenu, menu,
                         toplevel._default_visual,
                         toplevel._default_colormap)
            self.__dynamicmenu[widget] = menu

    def _create_menu(self, menu, list, flags):
        if len(list) > 30:
            menu.numColumns = (len(list) + 29) / 30
            menu.packing = Xmd.PACK_COLUMN
        for entry in list:
            flag = entry[0]
            if (flag & flags) == 0:
                continue
            label = entry[1]
            if label is None:
                dummy = menu.CreateManagedWidget('separator',
                                 Xm.SeparatorGadget, {})
                continue
            callback = entry[2]
            if type(callback) is ListType or \
               callback.dynamiccascade:
                submenu = menu.CreatePulldownMenu('submenu',
                        {'colormap': toplevel._default_colormap,
                         'visual': toplevel._default_visual,
                         'depth': toplevel._default_visual.depth,
                         'orientation': Xmd.VERTICAL,
                         'tearOffModel': Xmd.TEAR_OFF_ENABLED})
                button = menu.CreateManagedWidget(
                        'submenuLabel', Xm.CascadeButton,
                        {'labelString': label,
                         'subMenuId': submenu})
                if label == 'Help':
                    menu.menuHelpWidget = button
                if type(callback) is ListType:
                    self._create_menu(submenu, callback, flags)
                else:
                    button.SetSensitive(0)
                    self._set_callback(button, None, callback)
            else:
                button = self._create_button(menu,
                        self._visual, self._colormap, entry[1:])

    def _create_toolbar(self, tb, list, vertical, flags):
        for entry in list:
            flag = entry[0]
            if (flag & flags) == 0:
                continue
            if entry[1] is None:
                if vertical:
                    orientation = Xmd.HORIZONTAL
                else:
                    orientation = Xmd.VERTICAL
                dummy = tb.CreateManagedWidget(
                        'tbSeparator',
                        Xm.SeparatorGadget,
                        {'orientation': orientation})
                continue
            button = self._create_button(tb, self._visual,
                                         self._colormap, entry[1:])

    def setpopupmenu(self, menutemplate, flags):
        # Menutemplate is a MenuTemplate-style menu template.
        # It should be turned into an menu and put
        # into self._popupmenu.
        #
        # First check that it is actually different
        #
        if self.__popupmenutemplate == menutemplate:
            return
        #
        # Delete the old menu
        #
        self._destroy_popupmenu()
        self.__popupmenutemplate = menutemplate
        menu = self._form.CreatePopupMenu('menu',
                        {'colormap': self._colormap,
                         'visual': self._visual,
                         'depth': self._visual.depth})
        if self._visual.depth == 8:
            # make sure menu is readable, even on Suns
            menu.foreground = self._convert_color((0,0,0))
            menu.background = self._convert_color((255,255,255))
        self._create_menu(menu, menutemplate, flags)
        self._popupmenu = menu

    def _destroy_popupmenu(self):
        # Free resources held by self._popupmenu and set it to None
        if self._popupmenu is not None:
            self._popupmenu.DestroyWidget()
        self._popupmenu = None
        self.__popupmenutemplate = None
