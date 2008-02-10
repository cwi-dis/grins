__version__ = "$Id$"

from Carbon import Dlg

firsttime = 1
_dialog = None

RESOURCE_ID=513

ITEM_MSG=2
ITEM_USER=3
ITEM_ORG=4
ITEM_LICENSE=5
MESSAGE={
        'loadprog': "Loading program...",
        'loaddoc': "Loading document...",
        'initdoc': "Initialize document...",
}

def splash(arg=0, version=None):
    global firsttime, _dialog, _starttime
    if not firsttime:
        return
    if version and not arg:
        return
    if not arg:
        _dialog = None
        firsttime = 0
    else:
        if not _dialog:
            d = Dlg.GetNewDialog(RESOURCE_ID, -1)
            d.GetDialogWindow().ShowWindow()
            d.DrawDialog()
            _dialog = d
        setitem(ITEM_MSG, MESSAGE[arg])

def setuserinfo(user, org, license):
    if not _dialog:
        return
    setitem(ITEM_USER, user)
    setitem(ITEM_ORG, org)
    setitem(ITEM_LICENSE, license)

def setitem(item, value):
    htext = _dialog.GetDialogItemAsControl(item)
    Dlg.SetDialogItemText(htext, value)

def unsplash():
    pass
