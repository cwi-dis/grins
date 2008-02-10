# Dialog for the Attribute Editor.
#
# The Attribute editor dialog consists of four buttons that are always
# present (`Cancel', `Restore', `Apply', and `OK'), and a row of
# attribute editor fields.  The number and type of these fields are
# determined at run time, but there are only a limited number of
# different types.  The fields are represented by instances of
# sub-classes of the AttrEditorDialogField.  A list of these instances
# is passed to the constructor of the AttrEditorDialog class.

# Each of the attribute editor fields has a label with the name of the
# attribute, an interface to edit the value (the interface depends on
# the type of the value), and a `Reset' button.  There are two callbacks
# associated with an attribute editor field, one to get help, and one
# that is called when the `Reset' button is pressed.  There are also
# some methods to get and set the current value of the attribute.

# The base class of the AttrEditorDialogField class must provide some
# methods also.

__version__ = "$Id$"


# @win32doc|AttrEditorDialog
# This class represents the interface between the AttrEditor platform independent
# class and its implementation AttrEditorForm in lib/win32/AttrEditorForm.py which
# implements the actual dialog.

import windowinterface
import usercmd

class AttrEditorDialog:
    def __init__(self, title, attriblist, toplevel=None, initattr = None):
        # Create the AttrEditor dialog.

        # Create the dialog window (non-modal, so does not grab
        # the cursor) and pop it up (i.e. display it on the
        # screen).

        # Arguments (no defaults):
        # title -- string to be displayed as the window title
        # attriblist -- list of instances of subclasses of
        #       AttrEditorDialogField
        if hasattr(self, 'willreopen') and self.willreopen:
            # This is a reopen call.
            w = self.__window
            w._title=title
            w._attriblist=attriblist
            w._initattr = initattr
            for a in attriblist:
                a.attach_ui(w)
            w.RecreateWindow()
            self.fixbuttonstate()
            return
        formid='attr_edit'

        if toplevel:
            toplevel_window=self.wrapper.toplevel.window
        else:
            toplevel_window = windowinterface.getmainwnd()
        w=toplevel_window.newviewobj(formid)
        w._title=title
        w._attriblist=attriblist
        w._cbdict={
                'Cancel':(self.cancel_callback, ()),
                'Restore':(self.restore_callback, ()),
                'Apply':(self.apply_callback, ()),
                'OK':(self.ok_callback, ()),
                'Showall': (self.showall_callback, ()),
                'Followselection': (self.followselection_callback, ()),
                'SetCustomColors': self.setcustomcolors_callback,
                }
        if hasattr(self.wrapper, 'context') and hasattr(self.wrapper.context, 'color_list'):
            w._color_list = self.wrapper.context.color_list
        w._initattr = initattr
        # Not sure that this is the right way to pass this info
        # to AttrEditForm...
        w._has_showAll = 0
        w._has_followSelection = 0

        for a in attriblist:
            a.attach_ui(w)
        self.__window=w
        if self.wrapper.canhideproperties():
            # Not sure that this is the right way to pass this info
            # to AttrEditForm...
            w._has_showAll = 1

            w._showAll_initial = self.show_all_attributes
            commandlist = [
                    usercmd.SHOWALLPROPERTIES(callback = (self.showall_callback, ()))
            ]
            w.set_commandlist(commandlist)
            w.set_toggle(usercmd.SHOWALLPROPERTIES, self.show_all_attributes)
        w._has_followSelection = self.wrapper.canfollowselection()
        w._followSelection_initial = self.follow_selection
        toplevel_window.showview(w,formid)


    def setcustomcolors_callback(self, color_list):
        self.wrapper.context.color_list = color_list

    def close(self, willreopen=0):
        # Close the dialog and free resources.
        # XXXX To be done: if willreopen=1 we should not close the window but
        # reset it to the initial state. Also, in the init routine we should not
        # create __window if it already exists.
        self.willreopen = willreopen
        if willreopen:
            return
        if self.__window:
            self.__window.close()
        self.__window=None

    def getcurattr(self):
        return self.__window.getcurattr()

    def setcurattr(self, attr):
        self.__window.setcurattr(attr)

    def fixbuttonstate(self):
        # Fix the state of the floow selection and show all
        # buttons, apply/ok sensitivity and possibly labels.
        w = self.__window
        w._prsht.fixbuttonstate(
                self.show_all_attributes,
                self.follow_selection,
                self.is_changed())

    def pop(self):
        # Pop the dialog window to the foreground.
        if self.__window:
            self.__window.pop()

    def settitle(self, title):
        # Set (change) the title of the window.

        # Arguments (no defaults):
        # title -- string to be displayed as new window title
        if self.__window:
            self.__window.settitle(title)

    def showmessage(self, *args, **kw):
        apply(windowinterface.showmessage, args, kw)

    def askchannelname(self, default, cb):
        windowinterface.InputDialog('Name for new region',
                                    default,
                                    cb,
                                    cancelCallback = (cb, ()),
                                    parent = self.__window)

    # Callback functions.  These functions should be supplied by
    # the user of this class (i.e., the class that inherits from
    # this class).
    def cancel_callback(self):
        pass

    def restore_callback(self):
        pass

    def apply_callback(self):
        pass

    def ok_callback(self):
        pass

class AttrEditorDialogField:
    def attach_ui(self, form):
        # Set context for this attribute.  (internal method)

        # Arguments (no defaults):
        # form -- instance of AttrEditorForm
        self.__form=form

    def close(self):
        # Close the instance and free all resources.
        # nothing to free
        pass

    def getvalue(self):
        # Return the current value of the attribute.
##
        # The return value is a string giving the current value.
        try:
            return self.__form.getvalue(self)
        except AttributeError:
            return self.getcurrent()

    def setvalue(self, value):
        # Set the current value of the attribute.

        # Arguments (no defaults):
        # value -- string giving the new value
        self.__form.setvalue(self,value)

    def recalcoptions(self):
        # Recalculate the list of options and set the value.
        self.__form.setoptions(self,self.getoptions(), self.getcurrent())

    def askchannelname(self, default):
        self.attreditor.askchannelname(default, self.newchan_callback)


    # Methods to be overridden by the sub class.
    def gettype(self):
        # Return the type of the attribute as a string.

        # Valid types are:
        # option -- attribute value is one of a fixed set of
        #       values
        # file -- attribute is a file name (an interface to a
        #       file dialog is a good idea)
        # string -- attribute is a string
        # int -- attribute is a string representing an integer
        # float -- attribute is a string representing a float

        # `option' and `file' must be handled differently from
        # the others, the others can all be handled as a string.
        # An attribute field of type `option' must have a
        # getoptions method that returns a list of strings
        # giving all the possible values.
        # An attribute field of type `file' may invoke a
        # callback browser_callback that pops up a file browser.
        return 'type'

    def getlabel(self):
        # Return the label for the attribute field.
        return 'Button Label'

    def getcurrent(self):
        # Return the current value of the attribute as a string.
        return 'current value'

    def reset_callback(self):
        # Callback called when the `Reset' button is pressed.
        pass

    def help_callback(self):
        # Callback called when help is requested.
        pass
