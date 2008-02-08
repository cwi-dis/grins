__version__ = "$Id$"

# License dialog
import windowinterface
import Xm, Xmd, X
import ToolTip

_dialog_widget = None

class LicenseDialog:
    def __init__(self):
        import splashimg, imgconvert
        global _dialog_widget
        fg = windowinterface.toplevel._convert_color((0,0,0), 0)
        bg = windowinterface.toplevel._convert_color((0x99,0x99,0x99), 0)
        visual = windowinterface.toplevel._visual
        w = windowinterface.toplevel._main.CreateFormDialog(
                'license',
                {'autoUnmanage': 0, 'foreground': fg, 'background': bg,
                 'visual': visual, 'depth': visual.depth,
                 'colormap': windowinterface.toplevel._colormap,
                 'horizontalSpacing': 10,
                 'verticalSpacing': 10})
        w.Parent().AddWMProtocolCallback(
                windowinterface.toplevel._delete_window,
                self.__callback, (self.cb_quit, ()))
        fmt = windowinterface.toplevel._imgformat
        rdr = imgconvert.stackreader(fmt, splashimg.reader())
        self.__imgsize = rdr.width, rdr.height
        xim = visual.CreateImage(visual.depth, X.ZPixmap, 0,
                                 rdr.read(), rdr.width, rdr.height,
                                 fmt.descr['align'], 0)
        xim.byte_order = windowinterface.toplevel._byteorder
        img = w.CreateDrawingArea('splash',
                                  {'width': rdr.width,
                                   'height': rdr.height,
##                        'foreground': fg, 'background': bg,
                                   'topAttachment': Xmd.ATTACH_FORM,
                                   'leftAttachment': Xmd.ATTACH_FORM,
                                   'rightAttachment': Xmd.ATTACH_FORM})
        img.AddCallback('exposeCallback', self.__expose,
                        (xim, rdr.width, rdr.height))
        sep = w.CreateSeparator('separator',
                                {'leftAttachment': Xmd.ATTACH_FORM,
                                 'rightAttachment': Xmd.ATTACH_FORM,
                                 'topAttachment': Xmd.ATTACH_WIDGET,
                                 'topWidget': img,
                                 'orientation': Xmd.HORIZONTAL})
        tryb = w.CreatePushButton('try',
                                  {'labelString': 'Try',
                                   'foreground': fg, 'background': bg,
                                   'topAttachment': Xmd.ATTACH_WIDGET,
                                   'topWidget': sep,
                                   'leftAttachment': Xmd.ATTACH_FORM})
        tryb.AddCallback('activateCallback', self.__callback,
                         (self.cb_try, ()))
        ToolTip.addtthandler(tryb, 'Try out his software')
        self.__try = tryb
        eval = w.CreatePushButton('eval',
                                  {'labelString': 'Get Evaluation License...',
                                   'foreground': fg, 'background': bg,
                                   'topAttachment': Xmd.ATTACH_WIDGET,
                                   'topWidget': sep,
                                   'leftAttachment': Xmd.ATTACH_WIDGET,
                                   'leftWidget': tryb})
        eval.AddCallback('activateCallback', self.__callback,
                         (self.cb_eval, ()))
        ToolTip.addtthandler(eval, 'Direct web browser to web site to get evaluation key')
        self.__eval = eval
        buy = w.CreatePushButton('buy',
                                 {'labelString': 'Buy now...',
                                  'foreground': fg, 'background': bg,
                                  'topAttachment': Xmd.ATTACH_WIDGET,
                                  'topWidget': sep,
                                  'leftAttachment': Xmd.ATTACH_WIDGET,
                                  'leftWidget': eval})
        buy.AddCallback('activateCallback', self.__callback,
                        (self.cb_buy, ()))
        ToolTip.addtthandler(buy, 'Direct web browser to web site to buy a copy')
        key = w.CreatePushButton('key',
                                 {'labelString': 'Enter key...',
                                  'foreground': fg, 'background': bg,
                                  'topAttachment': Xmd.ATTACH_WIDGET,
                                  'topWidget': sep,
                                  'leftAttachment': Xmd.ATTACH_WIDGET,
                                  'leftWidget': buy})
        key.AddCallback('activateCallback', self.__callback,
                        (self.cb_enterkey, ()))
        ToolTip.addtthandler(key, 'Enter a license key')
        self.__key = key
        quit = w.CreatePushButton('quit',
                                  {'labelString': 'Quit',
                                   'foreground': fg, 'background': bg,
                                   'topAttachment': Xmd.ATTACH_WIDGET,
                                   'topWidget': tryb,
                                   'leftAttachment': Xmd.ATTACH_FORM,
                                   'bottomAttachment': Xmd.ATTACH_FORM})
        quit.AddCallback('activateCallback', self.__callback,
                         (self.cb_quit, ()))
        ToolTip.addtthandler(quit, 'Exit the program')
        label = w.CreateLabel('label',
                              {'labelString': 'Or see http://www.oratrix.com/ for more information',
                               'foreground': fg, 'background': bg,
                               'topAttachment': Xmd.ATTACH_WIDGET,
                               'topWidget': eval,
                               'leftAttachment': Xmd.ATTACH_WIDGET,
                               'leftWidget': quit,
                               'rightAttachment': Xmd.ATTACH_FORM,
                               'bottomAttachment': Xmd.ATTACH_FORM})
        label.ManageChild()
        self.__gc = None
        self.__img = img
        self.__msg = None
        self.__window = w
        _dialog_widget = w
        img.ManageChild()
        sep.ManageChild()
        tryb.ManageChild()
        eval.ManageChild()
        buy.ManageChild()
        key.ManageChild()
        quit.ManageChild()

    def __expose(self, widget, (xim, width, height), call_data):
        if self.__gc is None:
            self.__gc = widget.CreateGC({})
        self.__gc.PutImage(xim, 0, 0, 0, 0, width, height)

    def show(self):
        self.__window.RealizeWidget()
        self.__window.ManageChild()

    def close(self):
        global _dialog_widget
        _dialog_widget = None
        self.__window.DestroyWidget()
        self.__window = None
        del self.__window
        del self.__try
        del self.__key
        del self.__eval
        del self.__img
        del self.__msg

    def setdialoginfo(self):
        if self.can_try:
            self.__try.showAsDefault = 1
            self.__window.defaultButton = self.__try
        else:
            self.__key.showAsDefault = 1
            self.__window.defaultButton = self.__key
        self.__try.SetSensitive(self.can_try)
        self.__eval.SetSensitive(self.can_eval)
        width, height = self.__imgsize
        if self.__msg is None:
            # first time, find colors
            self.__fg = windowinterface.toplevel._convert_color((0x06,0x14,0x40), 0)
            self.__bg = windowinterface.toplevel._convert_color((255,255,255), 0)
        else:
            self.__msg.DestroyWidget
        attrs = {'labelString': self.msg,
                 'alignment': Xmd.ALIGNMENT_CENTER,
                 'x': 10,
                 'y': height - 26,
                 'width': width - 20,
                 'background': self.__bg,
                 'foreground': self.__fg}
        try:
            import splash
            self.__img.LoadQueryFont(splash.splashfont)
        except:
            pass
        else:
            attrs['fontList'] = splash.splashfont
        self.__msg = self.__img.CreateManagedWidget('message',
                                                    Xm.Label, attrs)

    def __callback(self, w, callback, call_data):
        apply(apply, callback)

class EnterkeyDialog:
    def __init__(self, ok_callback, user='', org='', license=''):
        if _dialog_widget:
            parent = _dialog_widget
        else:
            parent = windowinterface.toplevel._main
        self.__ok_callback = ok_callback
        visual = windowinterface.toplevel._visual
        w = parent.CreateTemplateDialog('license',
                {'cancelLabelString': 'Cancel',
                 'okLabelString': 'OK',
##              'resizePolicy': Xmd.RESIZE_NONE,
                 'noResize': 1,
                 'dialogStyle': Xmd.DIALOG_FULL_APPLICATION_MODAL,
                 'visual': visual, 'depth': visual.depth,
                 'colormap': windowinterface.toplevel._colormap})
        w.AddCallback('cancelCallback', self.__cancel, None)
        w.AddCallback('okCallback', self.__ok, None)
        s = w.CreateForm('form', {})
        f1 = s.CreateForm('form1',
                          {'topAttachment': Xmd.ATTACH_FORM,
                           'leftAttachment': Xmd.ATTACH_FORM,
                           'rightAttachment': Xmd.ATTACH_FORM})
        l1 = f1.CreateLabel('label1',
                            {'topAttachment': Xmd.ATTACH_FORM,
                             'leftAttachment': Xmd.ATTACH_FORM,
                             'bottomAttachment': Xmd.ATTACH_FORM,
                             'labelString': 'Name:'})
        t1 = f1.CreateTextField('text1',
                                {'topAttachment': Xmd.ATTACH_FORM,
                                 'leftAttachment': Xmd.ATTACH_WIDGET,
                                 'leftWidget': l1,
                                 'rightAttachment': Xmd.ATTACH_FORM,
                                 'bottomAttachment': Xmd.ATTACH_FORM,
                                 'value': user})
        self.__name = t1
        t1.AddCallback('valueChangedCallback', self.__changed, None)
        f2 = s.CreateForm('form2',
                          {'topAttachment': Xmd.ATTACH_WIDGET,
                           'topWidget': f1,
                           'leftAttachment': Xmd.ATTACH_FORM,
                           'rightAttachment': Xmd.ATTACH_FORM})
        l2 = f2.CreateLabel('label2',
                            {'topAttachment': Xmd.ATTACH_FORM,
                             'leftAttachment': Xmd.ATTACH_FORM,
                             'bottomAttachment': Xmd.ATTACH_FORM,
                             'labelString': 'Organization:'})
        t2 = f2.CreateTextField('text2',
                                {'topAttachment': Xmd.ATTACH_FORM,
                                 'leftAttachment': Xmd.ATTACH_WIDGET,
                                 'leftWidget': l2,
                                 'rightAttachment': Xmd.ATTACH_FORM,
                                 'bottomAttachment': Xmd.ATTACH_FORM,
                                 'value': org})
        self.__org = t2
        t2.AddCallback('valueChangedCallback', self.__changed, None)
        f3 = s.CreateForm('form3',
                          {'topAttachment': Xmd.ATTACH_WIDGET,
                           'topWidget': f2,
                           'leftAttachment': Xmd.ATTACH_FORM,
                           'rightAttachment': Xmd.ATTACH_FORM,
                           'bottomAttachment': Xmd.ATTACH_FORM})
        l3 = f3.CreateLabel('label3',
                            {'topAttachment': Xmd.ATTACH_FORM,
                             'leftAttachment': Xmd.ATTACH_FORM,
                             'bottomAttachment': Xmd.ATTACH_FORM,
                             'labelString': 'License key:'})
        t3 = f3.CreateTextField('text3',
                                {'topAttachment': Xmd.ATTACH_FORM,
                                 'leftAttachment': Xmd.ATTACH_WIDGET,
                                 'leftWidget': l3,
                                 'rightAttachment': Xmd.ATTACH_FORM,
                                 'bottomAttachment': Xmd.ATTACH_FORM,
                                 'value': license})
        self.__key = t3
        t3.AddCallback('valueChangedCallback', self.__changed, None)
        f1.ManageChild()
        l1.ManageChild()
        t1.ManageChild()
        f2.ManageChild()
        l2.ManageChild()
        t2.ManageChild()
        f3.ManageChild()
        l3.ManageChild()
        t3.ManageChild()
        s.ManageChild()
        self.__ok = w.MessageBoxGetChild(Xmd.DIALOG_OK_BUTTON)
        self.__changed(None, None, None)
        w.ManageChild()

    def __cancel(self, w, client_data, call_data):
        del self.__ok
        del self.__name
        del self.__org
        del self.__key

    def __ok(self, w, client_data, call_data):
        name = self.__name.TextFieldGetString()
        org = self.__org.TextFieldGetString()
        key = self.__key.TextFieldGetString()
        self.__ok_callback(key, name, org)
        self.__cancel(w, client_data, call_data)

    def __changed(self, w, client_data, call_data):
        name = self.__name.TextFieldGetString()
        org = self.__org.TextFieldGetString()
        key = self.__key.TextFieldGetString()
        if (name or org) and key:
            self.__ok.SetSensitive(1)
        else:
            self.__ok.SetSensitive(0)
