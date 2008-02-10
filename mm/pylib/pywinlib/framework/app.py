
import win32con
import win32api
import win32ui
import sys

# Helpers that should one day be removed!
def AddIdleHandler(handler):
    return win32ui.GetApp().AddIdleHandler(handler)
def DeleteIdleHandler(handler):
    return win32ui.GetApp().DeleteIdleHandler(handler)


# Helper for writing a Window position by name, and later loading it.
def SaveWindowSize(section,rect):
    """ Writes a rectangle to an INI file
    Args: section = section name in the applications INI file
          rect = a rectangle in a (cy, cx, y, x) tuple
                 (same format as CREATESTRUCT position tuples)."""
    left, top, right, bottom = rect
    win32ui.WriteProfileVal(section,"left",left)
    win32ui.WriteProfileVal(section,"top",top)
    win32ui.WriteProfileVal(section,"right",right)
    win32ui.WriteProfileVal(section,"bottom",bottom)

def LoadWindowSize(section):
    """ Loads a section from an INI file, and returns a rect in a tuple (see SaveWindowSize)"""
    left = win32ui.GetProfileVal(section,"left",0)
    top = win32ui.GetProfileVal(section,"top",0)
    right = win32ui.GetProfileVal(section,"right",0)
    bottom = win32ui.GetProfileVal(section,"bottom",0)
    return (left, top, right, bottom)

def RectToCreateStructRect(rect):
    return (rect[3]-rect[1], rect[2]-rect[0], rect[1], rect[0] )


def Win32RawInput(prompt=None):
    "Provide raw_input() for gui apps"
    # flush stderr/out first.
    try:
        sys.stdout.flush()
        sys.stderr.flush()
    except:
        pass
    if prompt is None: prompt = ""
    ret=dialog.GetSimpleInput(prompt)
    if ret==None:
        raise KeyboardInterrupt, "operation cancelled"
    return ret

def Win32Input(prompt=None):
    "Provide input() for gui apps"
    return eval(raw_input(prompt))

sys.modules['__builtin__'].raw_input=Win32RawInput
sys.modules['__builtin__'].input=Win32Input
