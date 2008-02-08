__version__ = "$Id$"

import winuser
import win32con

class showmessage:
    def __init__(self, text, mtype = 'message', grab = 1, callback = None,
                 cancelCallback = None, name = 'message',
                 title = 'GRiNS', parent = None, identity = None):
        # XXXX If identity != None the user should have the option of not
        # showing this message again
        self._wnd = None
        if grab == 0:
            #self._wnd = ModelessMessageBox(text,title,parent)
            return
        if cancelCallback:
            style = win32con.MB_OKCANCEL
        else:
            style = win32con.MB_OK

        if mtype == 'error':
            style = style |win32con.MB_ICONERROR

        elif mtype == 'warning':
            style = style |win32con.MB_ICONWARNING

        elif mtype == 'information':
            style = style |win32con.MB_ICONINFORMATION

        elif mtype == 'message':
            style = style | win32con.MB_ICONINFORMATION

        elif mtype == 'question':
            style = win32con.MB_OKCANCEL|win32con.MB_ICONQUESTION

        if not parent or not hasattr(parent,'MessageBox'):
            self._res = winuser.MessageBox(text, title, style)
        else:
            self._res = parent.MessageBox(text, title, style)
        if callback and self._res == win32con.IDOK:
            apply(apply,callback)
        elif cancelCallback and self._res == win32con.IDCANCEL:
            apply(apply,cancelCallback)

    # Returns user response
    def getresult(self):
        return self._res

def showquestion(text, parent = None):
    print text
    return 1

class ProgressDialog:
    def __init__(self, *args):
        print 'ProgressDialog', args

    def set(self, *args):
        print 'ProgressDialog', args
