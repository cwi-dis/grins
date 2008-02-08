__version__ = "$Id$"

# Common code factored out of TreeCtrl/ListCtrl
# and _AssetsView/__LayoutView

import grinsRC
import win32ui
import win32mu
import commctrl

# Default list of state iconnames.
STATEICONNAME_TO_RESID={
        'reserved': grinsRC.IDI_ICON_ASSET_BLANK, # don't change this one (special case)

        'hidden': grinsRC.IDI_CLOSEDEYE,
        'showed': grinsRC.IDI_OPENEDEYE,
        'locked': grinsRC.IDI_OPENEDEYEKEY,
}

# Default list of iconnames.
ICONNAME_TO_RESID={
        None: grinsRC.IDI_ICON_ASSET_BLANK,

        # Media types:
        'ref': grinsRC.IDI_ICON_ASSET_BLANK,
        'text': grinsRC.IDI_ICON_ASSET_TEXT,
        'image': grinsRC.IDI_ICON_ASSET_IMAGE,
        'video': grinsRC.IDI_ICON_ASSET_VIDEO,
        'audio': grinsRC.IDI_ICON_ASSET_AUDIO,
        'sound': grinsRC.IDI_ICON_ASSET_AUDIO,
        'html': grinsRC.IDI_ICON_ASSET_TEXT,
        'animation': grinsRC.IDI_ANIMATION,
        'svg': grinsRC.IDI_ANIMATION,
        'anchor': grinsRC.IDI_ICON_LINKSRC,
        'browseranchor': grinsRC.IDI_ICON_BROWSER,
        'contextanchor': grinsRC.IDI_ICON_CONTEXT,

        # Node types:
        'node': grinsRC.IDI_ICON_NODE,
        'imm': grinsRC.IDI_ICON_NODE,
        'ext': grinsRC.IDI_ICON_NODE,
        'animate': grinsRC.IDI_ANIMATE,
        'brush': grinsRC.IDI_BRUSH,
        'media': grinsRC.IDI_ICON_MEDIAOPEN,
        'mediaopen': grinsRC.IDI_ICON_MEDIAOPEN,
        'mediaclosed': grinsRC.IDI_ICON_MEDIACLOSED,
        'par': grinsRC.IDI_ICON_PAROPEN,
        'paropen': grinsRC.IDI_ICON_PAROPEN,
        'parclosed': grinsRC.IDI_ICON_PARCLOSED,
        'seq': grinsRC.IDI_ICON_SEQOPEN,
        'seqopen': grinsRC.IDI_ICON_SEQOPEN,
        'seqclosed': grinsRC.IDI_ICON_SEQCLOSED,
        'excl': grinsRC.IDI_ICON_EXCLOPEN,
        'exclopen': grinsRC.IDI_ICON_EXCLOPEN,
        'exclclosed': grinsRC.IDI_ICON_EXCLCLOSED,
        'switch': grinsRC.IDI_ICON_SWITCHOPEN,
        'switchopen': grinsRC.IDI_ICON_SWITCHOPEN,
        'switchclosed': grinsRC.IDI_ICON_SWITCHCLOSED,
        'prio': grinsRC.IDI_ICON_PRIOOPEN,
        'prioopen': grinsRC.IDI_ICON_PRIOOPEN,
        'prioclosed': grinsRC.IDI_ICON_PRIOCLOSED,

        # Region types:
        'viewport': grinsRC.IDI_VIEWPORT,
        'region': grinsRC.IDI_REGION,

        # These were block-copied from win32displaylist.
        # We need to check whether they're all still used.
        'closed': grinsRC.IDI_ICON_CLOSED,
        'open': grinsRC.IDI_ICON_OPEN,
        'bandwidthgood': grinsRC.IDI_ICON_BANDWIDTHGOOD,
        'bandwidthbad': grinsRC.IDI_ICON_BANDWIDTHBAD,
        'error': grinsRC.IDI_ICON_ERROR,
        'linksrc': grinsRC.IDI_ICON_LINKSRC,
        'linkdst': grinsRC.IDI_ICON_LINKDST,
        'danglingevent': grinsRC.IDI_DANGLINGEVENT,
        'danglinganchor': grinsRC.IDI_DANGLINGANCHOR,
##     'linksrcdst': grinsRC.IDI_ICON_LINKSRCDST,
        'transin': grinsRC.IDI_ICON_TRANSIN,
        'transout': grinsRC.IDI_ICON_TRANSOUT,
        'beginevent' : grinsRC.IDI_EVENTIN,
        'endevent' : grinsRC.IDI_EVENTOUT,
        'activateevent' : grinsRC.IDI_ACTIVATEEVENT,
        'causeevent' : grinsRC.IDI_CAUSEEVENT,
        'duration' : grinsRC.IDI_DURATION,
        'focusin' : grinsRC.IDI_FOCUSIN,
        'happyface' : grinsRC.IDI_HAPPYFACE,
        'repeat' : grinsRC.IDI_REPEAT,
        'spaceman': grinsRC.IDI_SPACEMAN,
        'wallclock': grinsRC.IDI_WALLCLOCK,
        'pausing': grinsRC.IDI_PAUSING,
        'playing': grinsRC.IDI_PLAYING,
        'waitstop': grinsRC.IDI_WAITSTOP,
        'idle': grinsRC.IDI_IDLE,
        'properties': grinsRC.IDI_PROPERTIES,
        'unknown': grinsRC.IDI_UNKNOWN,
}

# This mixin is for the control, it creates the image lists
# and binds them to the control
class CtrlMixin:
    def setIconLists(self, normalList, normalSize, normalType, smallList, smallSize, smallType):
        app = win32ui.GetApp()
        mask = 0

        # normal icons image list
        if normalList:
            initcount = len(normalList)
            growby = initcount
            normalImageList = win32ui.CreateImageList(normalSize, normalSize, mask, initcount, growby)
            normalImageList.SetBkColor(win32mu.RGB((255,255,255)))
            # populate normal image list
            for id in normalList:
                normalImageList.Add(app.LoadIcon(id))

        # smal icons image list
        if smallList:
            initcount = len(smallList)
            growby = initcount
            smallImageList = win32ui.CreateImageList(smallSize, smallSize, mask, initcount, growby)
            smallImageList.SetBkColor(win32mu.RGB((255,255,255)))
            # populate small image list
            for id in normalList:
                smallImageList.Add(app.LoadIcon(id))

        # finally set image list
        if normalList:
            self.SetImageList(normalImageList, normalType)
        if smallList:
            self.SetImageList(smallImageList, smallType)

# This mixin is for the view. It fills the name->id dictionary
# and returns the values to be passed to the control

class ViewMixin:

    def initicons(self, icon2resid=None):
        if icon2resid is None:
            icon2resid = ICONNAME_TO_RESID
        self.__iconlist_small = []
        self.__iconname_to_index = {}
        for k, v in icon2resid.items():
            if v is None:
                self.__iconname_to_index[k] = None
                continue
            if not v in self.__iconlist_small:
                self.__iconlist_small.append(v)
            self.__iconname_to_index[k] = self.__iconlist_small.index(v)

    def initstateicons(self, icon2resid=None):
        if icon2resid is None:
            icon2resid = STATEICONNAME_TO_RESID
        self.__stateiconlist_small = []
        self.__stateiconname_to_index = {}

        # special case for the first index, see windows api
        for k, v in icon2resid.items():
            if k == 'reserved':
                self.__stateiconlist_small.append(v)
                self.__stateiconname_to_index[k] = self.__stateiconlist_small.index(v)
                break
        for k, v in icon2resid.items():
            if k == 'reserved':
                continue
            if v is None:
                self.__stateiconname_to_index[k] = None
                continue
            elif not v in self.__stateiconlist_small:
                self.__stateiconlist_small.append(v)
            self.__stateiconname_to_index[k] = self.__stateiconlist_small.index(v)

    def seticonlist(self, ctrl, icontype_normal=commctrl.LVSIL_NORMAL, icontype_small=commctrl.LVSIL_SMALL):
        # For now we set the 16x16 icons for both small and large
        # this needs to be rethought at some point.
        ctrl.setIconLists(self.__iconlist_small, 16, icontype_normal, self.__iconlist_small, 16, icontype_small)

    def setstateiconlist(self, ctrl, icontype_normal=commctrl.TVSIL_STATE):
        # For the tree control, you can also specify a separated state icon list
        ctrl.setIconLists(self.__stateiconlist_small, 16, icontype_normal, None, 0, 0)

    def geticonid(self, name):
        rv = self.__iconname_to_index.get(name)
        if rv is None:
            rv = self.__iconname_to_index[None]
        return rv

    def getstateiconid(self, name):
        rv = self.__stateiconname_to_index.get(name)
        if rv is None:
            rv = self.__stateiconname_to_index[None]
        return rv

    def getstateiconname(self, index):
        for iconname, id in self.__stateiconname_to_index.items():
            if id == index:
                return iconname
        return None
