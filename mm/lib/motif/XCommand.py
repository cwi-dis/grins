__version__ = "$Id$"

from types import ClassType
import ToolTip, string
from XTopLevel import toplevel

class _CommandSupport:
    def __init__(self):
        self.__commandlist = [] # list of currently valid command insts
        self.__commanddict = {} # mapping of command class to instance
        self.__widgetmap = {}   # mapping of command to list of widgets
        self.__accelmap = {}    # mapping of command to list of keys
        self.__togglelables = {}
        self.__delete_commands = []

    def close(self):
        del self.__commandlist
        del self.__commanddict
        self.__widgetmap = {}
        del self.__accelmap
        del self.__togglelables
        del self.__delete_commands

    def set_commandlist(self, list):
        oldlist = self.__commandlist
        olddict = self.__commanddict
        newlist = []
        newdict = {}
        for cmd in list:
            c = cmd.__class__
            newlist.append(c)
            newdict[c] = cmd
        if newlist != oldlist:
            # there are changes...
            # first remove old commands
            for c in oldlist:
                if not newdict.has_key(c):
                    for w in self.__widgetmap.get(c, []):
                        w.SetSensitive(0)
                        ToolTip.deltthandler(w)
            # then add new commands
            for cmd in list:
                c = cmd.__class__
                if not olddict.has_key(c):
                    for w in self.__widgetmap.get(c, []):
                        w.SetSensitive(1)
                        if cmd.help:
                            ToolTip.addtthandler(w, cmd.help)
        # reassign callbacks for accelerators
        for c in oldlist:
            for key in self.__accelmap.get(c, []):
                del self._accelerators[key]
        for cmd in list:
            for key in self.__accelmap.get(cmd.__class__, []):
                self._accelerators[key] = cmd.callback
        self.__commandlist = newlist
        self.__commanddict = newdict


    def set_toggle(self, command, onoff):
        for widget in self.__widgetmap.get(command, []):
            if widget.ToggleButtonGetState() != onoff:
                widget.ToggleButtonSetState(onoff, 0)
                label = self.__togglelables.get(widget)
                if label is not None:
                    widget.labelString = label[onoff]

    def __callback(self, widget, callback, call_data):
        ToolTip.rmtt()
        if type(callback) is ClassType:
            callback = self.__commanddict.get(callback)
            if callback is not None:
                callback = callback.callback
        label = self.__togglelables.get(widget)
        if label is not None:
            widget.labelString = label[widget.ToggleButtonGetState()]
        if callback is not None:
            apply(apply, callback)
            toplevel.setready()

    def __remove(self, widget, client_data, call_data):
        for list in self.__widgetmap.values():
            if widget in list:
                list.remove(widget)

    def _set_callback(self, widget, callbacktype, callback):
        if callbacktype:
            widget.AddCallback(callbacktype, self.__callback,
                               callback)
        if type(callback) is ClassType:
            if not self.__widgetmap.has_key(callback):
                self.__widgetmap[callback] = []
            self.__widgetmap[callback].append(widget)
            widget.AddCallback('destroyCallback', self.__remove, None)
            if self.__commanddict.has_key(callback):
                # Currently enabled. Add a tooltip
                widget.SetSensitive(1)
                if callback.help:
                    ToolTip.addtthandler(widget,
                                         callback.help)
            else:
                # Currently disabled.
                widget.SetSensitive(0)

    def _delete_callback(self, widget, client_data, call_data):
        for c in self.__delete_commands:
            cmd = self.__commanddict.get(c)
            if cmd is not None and cmd.callback is not None:
                apply(apply, cmd.callback)
                return 1
        return 0

    def _set_deletecommands(self, deletecommands):
        self.__delete_commands = deletecommands

    def _set_togglelabels(self, widget, labels):
        self.__togglelables[widget] = labels
        widget.labelString = labels[widget.ToggleButtonGetState()]
        widget.inidcatorOn = 0
        widget.fillOnSelect = 0

    def _get_acceleratortext(self, callback):
        if self.__accelmap.has_key(callback):
            return string.join(self.__accelmap[callback], '|')

    def _get_commandinstance(self, command):
        return self.__commanddict.get(command)

    def _get_commandwidgets(self, command):
        return self.__widgetmap.get(command, [])

    def _create_shortcuts(self, shortcuts):
        for key, c in shortcuts.items():
            if not self.__accelmap.has_key(c):
                self.__accelmap[c] = []
            self.__accelmap[c].append(key)
