__version__ = "$Id$"

import usercmd

from _PlayerView import _PlayerView
from _SourceView import _SourceView

usercmd.HIDE_PLAYERVIEW = usercmd.CLOSE
usercmd.HIDE_SOURCEVIEW = usercmd.SOURCEVIEW

# This is a list of classes that are instantiated for each particular view.
##### THIS IS ONLY USED WITHIN THE MainFrame MODULE #####
appview = {
        'pview_':{'cmd':usercmd.HIDE_PLAYERVIEW,'title':'Player','class':_PlayerView,},
        'sview_':{'cmd':usercmd.HIDE_SOURCEVIEW,'title':'Source','class':_SourceView},
        }
