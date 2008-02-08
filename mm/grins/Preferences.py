__version__ = "$Id$"

# Preferences window (modeless dialog)

import windowinterface
from PreferencesDialog import PreferencesDialog, PreferencesDialogError
import settings

SPECIAL_NAMES={
        "system_overdub_or_caption": ["overdub", "subtitle"],
}

class Preferences(PreferencesDialog):

    _singleton = None

    def __init__(self, callback):
        if Preferences._singleton:
            raise 'Singleton recreated'
        Preferences._singleton = self
        title = "GRiNS Preferences"
        PreferencesDialog.__init__(self, title)
        self.bool_names = self.getboolnames()
        self.int_names = self.getintnames()
        self.string_names = self.getstringnames()
        if hasattr(self, 'getfloatnames'):
            self.float_names = self.getfloatnames()
        else:
            self.float_names = []
        self.callback = callback
        self.load_settings()
        self.show()

    def close(self):
        self.callback = None
        Preferences._singleton = None
        PreferencesDialog.close(self)

    def load_settings(self):
        for name in self.bool_names:
            value = settings.get(name)
            if SPECIAL_NAMES.has_key(name):
                allowed_values = SPECIAL_NAMES[name]
                if value in allowed_values:
                    value = allowed_values.index(value)
            if not value in (None, 0, 1):
                windowinterface.showmessage("Unexpected value '%s' for %s"
                                % (value, name))
                value = 0
            self.setboolitem(name, value)
        for name in self.string_names:
            value = settings.get(name)
            if value != None and type(value) != type(''):
                value = `value`
            self.setstringitem(name, value)
        for name in self.int_names:
            value = settings.get(name)
            if value != None and not type(value) == type(1):
                windowinterface.showmessage("Unexpected value '%s' for %s"
                                % (value, name))
                value = None
            self.setintitem(name, value)
        for name in self.float_names:
            value = settings.get(name)
            if value is not None and not type(value) in (type(0),type(0.0)):
                windowinterface.showmessage("Unexpected value '%s' for %s" % (value, name))
                value = None
            self.setfloatitem(name, value)

    def save_settings(self):
        values = {}
        for name in self.bool_names:
            try:
                value = self.getboolitem(name)
            except PreferencesDialogError, arg:
                windowinterface.showmessage(arg)
                return None
            if SPECIAL_NAMES.has_key(name) and value in (0,1):
                allowed_values = SPECIAL_NAMES[name]
                value = allowed_values[value]
            values[name] = value
        for name in self.int_names:
            try:
                value = self.getintitem(name)
            except PreferencesDialogError, arg:
                windowinterface.showmessage(arg)
                return None
            values[name] = value
        for name in self.float_names:
            try:
                value = self.getfloatitem(name)
            except PreferencesDialogError, arg:
                windowinterface.showmessage(arg)
                return None
            values[name] = value
        for name in self.string_names:
            try:
                value = self.getstringitem(name)
            except PreferencesDialogError, arg:
                windowinterface.showmessage(arg)
                return None
            values[name] = value
        return values


    # dialog callbacks

    def ok_callback(self):
        values = self.save_settings()
        if values is None:
            return
        for name, value in values.items():
            settings.set(name, value)
        settings.save()
        if self.callback:
            self.callback()

        self.close()

    def apply_callback(self):
        self.setvalues()

    def cancel_callback(self):
        self.close()

    def reset_callback(self):
        for name in self.bool_names + self.int_names + self.string_names + self.float_names:
            settings.set(name, None)
        self.load_settings()


def showpreferences(on, callback=None):
    if on:
        if Preferences._singleton:
            Preferences._singleton.pop()
        else:
            preferences = Preferences(callback)
    elif Preferences._singleton:
        Preferences._singleton.close()
