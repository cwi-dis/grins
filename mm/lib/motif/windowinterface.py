__version__ = "$Id$"

import Xt
from WMEVENTS import *

from XConstants import *

from XTopLevel import *                 # toplevel and various functions

from XFont import *
from XDialog import *
from XFormWindow import Window
from XTemplate import TemplateDialog

def beep():
    dpy = toplevel._main.Display()
    dpy.Bell(100)
    dpy.Flush()

def sleep(sec):
    pass                            # for now

def lopristarting():
    pass

def Dialog(list, title = '', prompt = None, grab = 1, vertical = 1,
           parent = None):
    w = Window(title, grab = grab, parent = parent)
    options = {'top': None, 'left': None, 'right': None}
    if prompt:
        l = apply(w.Label, (prompt,), options)
        options['top'] = l
    options['vertical'] = vertical
    if grab:
        options['callback'] = (lambda w: w.close(), (w,))
    b = apply(w.ButtonRow, (list,), options)
    w.buttons = b
    w.show()
    return w

class _Question:
    def __init__(self, text, parent = None):
        self.looping = FALSE
        self.answer = None
        showmessage(text, mtype = 'question',
                    callback = (self.callback, (TRUE,)),
                    cancelCallback = (self.callback, (FALSE,)),
                    parent = parent)

    def run(self):
# Not needed anymore, now that showmessage() is truly modal.
#               self.looping = TRUE
#               toplevel.setready()
#               while self.looping:
#                       Xt.DispatchEvent(Xt.NextEvent())
        return self.answer

    def callback(self, answer):
        self.answer = answer
        self.looping = FALSE

def showquestion(text, parent = None):
    return _Question(text, parent = parent).run()

class _MultChoice:
    def __init__(self, prompt, msg_list, defindex, parent = None):
        self.looping = FALSE
        self.answer = None
        self.msg_list = msg_list
        list = []
        for msg in msg_list:
            list.append((msg, (self.callback, (msg,))))
        self.dialog = Dialog(list, title = None, prompt = prompt,
                             grab = TRUE, vertical = FALSE,
                             parent = parent)

    def run(self):
        self.looping = TRUE
        toplevel.setready()
        while self.looping:
            Xt.DispatchEvent(Xt.NextEvent())
        return self.answer

    def callback(self, msg):
        for i in range(len(self.msg_list)):
            if msg == self.msg_list[i]:
                self.answer = i
                self.looping = FALSE
                return

def multchoice(prompt, list, defindex, parent = None):
    return _MultChoice(prompt, list, defindex, parent = parent).run()

def GetYesNoCancel(prompt, parent = None):
    return multchoice(prompt, ["Yes", "No", "Cancel"], 0)

def GetOKCancel(prompt, parent = None):
    return 1 - showquestion(prompt, parent)

def RegisterDialog():
    return multchoice("""\
You must register this product with Oratrix to be eligible for
extended technical support, updates and discounts on
upgrades.

Do you want to register now?""", ["Register", "Don't register", "Remind me later"], 0)

class textwindow:
    def __init__(self, text, readonly = 1, closeCallback = None):
        w = Window('Source', resizable = 1, deleteCallback = closeCallback or 'hide')
        b = w.ButtonRow([('Close', (w.hide, ()))],
                        top = None, left = None, right = None,
                        vertical = 0)
        t = w.TextEdit(text, None, editable = not readonly,
                       top = b, left = None, right = None,
                       bottom = None, rows = 30, columns = 80)
        w.show()
        self.__window = w
        self.__text = t

    def settext(self, text, colors=[]):
        self.__text.settext(text)

    def gettext(self):
        return self.__text.gettext()

    def getLineNumber(self):
        return 1                # XXX for now

    def getCurrentCharIndex(self):
        return 1                # XXX for now

    def is_changed(self):
        return 0                # XXX for now

    def select_chars(self, start, end):
        pass                    # XXX for now

    def close(self):
        self.__window.close()
        self.__window = None
        self.__text = None

## class htmlwindow:
##     def __init__(self, url):
##         w = Window('Help', resizable = 1, deleteCallback = 'hide')
##         b = w.ButtonRow([('Close', (w.hide, ()))],
##                 top = None, left = None, right = None,
##                 vertical = 0)
##         h = w.Html(url, top = b, left = None, right = None, bottom = None)
##         w.show()
##         self.__window = w
##         self.__htmlw = h

##     def goto_url(self, url):
##         self.__htmlw.goto_url(url)
##         self.__window.pop()

##     def is_closed(self):
##         return self.__window.is_closed()

def htmlwindow(url):
    import os
    browser = os.environ.get('WEBBROWSER', 'netscape')
    if browser == 'netscape':
        # special case code for netscape
        cmd = 'netscape -remote "openURL(%s)" 2>/dev/null || netscape %s &' % (url, url)
    else:
        cmd = '%s %s &' % (browser, url)
    os.system(cmd)
    # don't return a value!

# open an external application in order to manage the media specified in url
# verb is the action executed by the external application. may be print, ... (for now ignore)
def shell_execute(url,verb='open'):
    htmlwindow(url)

class ProgressDialog:
    # Placeholder

    def __init__(self, title, cancelcallback=None):
        self.cancelcallback = cancelcallback

    def set(self, label, cur1=None, max1=None, cur2=None, max2=None):
        if cur1 != None:
            label = label + " (%d of %d)"%(cur1, max1)
        if cur2 != None:
            label = label + ": %d%%"%(cur2*100/max2)
##         print label

from imgimagesize import GetImageSize
def GetVideoSize(url):
    try:
        import mv               # SGI?
    except ImportError:
        import MPEGVideoSize
        return MPEGVideoSize.getsize(url)
    try:
        import MMurl
        try:
            file = MMurl.urlretrieve(url)[0]
        except IOError:
            return 0, 0
        movie = mv.OpenFile(file, mv.MV_MPEG1_PRESCAN_OFF)
        track = movie.FindTrackByMedium(mv.DM_IMAGE)
        return track.GetImageWidth(), track.GetImageHeight()
    except:
        pass
    import MPEGVideoSize
    return MPEGVideoSize.getsize(file)

# complicated mess to prevent calls to RemoveWorkProc while inside the workproc
# we assume no nested calls to workprocs
_in_idle = None
_cancel_idle = None
_idleprocdict = {}
def _idleproc(f):
    global _in_idle, _cancel_idle
    _in_idle = f
    try:
        exit = f()
    finally:
        _in_idle = None
        if exit or (_cancel_idle is not None and _cancel_idle is f):
            _cancel_idle = None
            return 1

def setidleproc(f):
    id = Xt.AddWorkProc(_idleproc, f)
    _idleprocdict[id] = f
    return id

def cancelidleproc(id):
    global _in_idle, _cancel_idle
    if _in_idle is not None and _idleprocdict[id] is _in_idle:
        _cancel_idle = _in_idle
    else:
        Xt.RemoveWorkProc(id)
