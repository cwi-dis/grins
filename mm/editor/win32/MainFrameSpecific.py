__version__ = "$Id$"

import usercmd

from AttrEditForm import AttrEditForm
from _AssetsView import _AssetsView
from _ErrorsView import _ErrorsView
from _LayoutView import _LayoutView
from _LayoutView2 import _LayoutView2
from _LinkView import _LinkView
from _PlayerView import _PlayerView
from _SourceView import _SourceView
from _StructView import _StructView
from _TransitionView import _TransitionView
from _ParamgroupView import _ParamgroupView
from _UsergroupView import _UsergroupView

# This is a list of classes that are instantiated for each particular view.
##### THIS IS ONLY USED WITHIN THE MainFrame MODULE #####
appview = {
        'attr_edit':{'cmd':-1,'title':'Properties','class':AttrEditForm},
        'aview_':{'cmd':usercmd.HIDE_ASSETSVIEW,'title':'Assets','class':_AssetsView,},
        'erview_':{'cmd':usercmd.HIDE_ERRORSVIEW,'title':'Error messages','class':_ErrorsView},
        'hview_':{'cmd':usercmd.HIDE_HIERARCHYVIEW,'title':'Structured Timeline','class':_StructView,},
        'leview_':{'cmd':usercmd.HIDE_LINKVIEW,'title':'Hyperlinks', 'class':_LinkView},
        'lview2_':{'cmd':usercmd.HIDE_LAYOUTVIEW2,'title':'Layout','class':_LayoutView2},
        'lview_':{'cmd':usercmd.HIDE_LAYOUTVIEW,'title':'Layout', 'class':_LayoutView},
        'pview_':{'cmd':usercmd.HIDE_PLAYERVIEW,'title':'Previewer','class':_PlayerView,},
        'sview_':{'cmd':usercmd.HIDE_SOURCEVIEW,'title':'Source','class':_SourceView},
        'trview_':{'cmd':usercmd.HIDE_TRANSITIONVIEW,'title':'Transitions','class':_TransitionView},
        'pgview_':{'cmd':usercmd.HIDE_PARAMGROUPVIEW,'title':'Paramgroups','class':_ParamgroupView},
        'ugview_':{'cmd':usercmd.HIDE_USERGROUPVIEW,'title':'Custom Tests','class':_UsergroupView},
        }
