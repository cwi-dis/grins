# Common code factored out of TreeCtrl/ListCtrl
# and _AssetsView/__LayoutView

import grinsRC
import win32ui
import win32mu
import commctrl

# Default list of iconnames.
ICONNAME_TO_RESID={
	None: grinsRC.IDI_ICON_ASSET_BLANK,
	'ref': grinsRC.IDI_ICON_ASSET_BLANK,
	'text': grinsRC.IDI_ICON_ASSET_TEXT,
	'image': grinsRC.IDI_ICON_ASSET_IMAGE,
	'video': grinsRC.IDI_ICON_ASSET_VIDEO,
	'audio': grinsRC.IDI_ICON_ASSET_AUDIO,
	'sound': grinsRC.IDI_ICON_ASSET_AUDIO,
	'html': grinsRC.IDI_ICON_ASSET_TEXT,
	'animation': grinsRC.IDI_ANIMATION,
	'svg': grinsRC.IDI_ANIMATION,

	'node': grinsRC.IDI_ICON_NODE,
	'imm': grinsRC.IDI_ICON_NODE,
	'ext': grinsRC.IDI_ICON_NODE,
	'animate': grinsRC.IDI_ANIMATE,
	'brush': grinsRC.IDI_BRUSH,
	'par': grinsRC.IDI_ICON_PAROPEN,
	'seq': grinsRC.IDI_ICON_SEQOPEN,
	'excl': grinsRC.IDI_ICON_EXCLOPEN,
	'switch': grinsRC.IDI_ICON_SWITCHOPEN,
	'prio': grinsRC.IDI_ICON_PRIOOPEN,

	'viewport': grinsRC.IDI_VIEWPORT,
	'region': grinsRC.IDI_REGION,

	'properties': grinsRC.IDI_PROPERTIES,

	'linksrc': grinsRC.IDI_ICON_LINKSRC,
	'unknown': grinsRC.IDI_UNKNOWN,
}

# This mixin is for the control, it creates the image lists
# and binds them to the control
class CtrlMixin:
	def setIconLists(self, normalList, normalSize, smallList, smallSize):
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
			self.SetImageList(normalImageList, commctrl.LVSIL_NORMAL)
		if smallList:
			self.SetImageList(smallImageList, commctrl.LVSIL_SMALL)

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

	def seticonlist(self, ctrl):
		# For now we set the 16x16 icons for both small and large
		# this needs to be rethought at some point.
		ctrl.setIconLists(self.__iconlist_small, 16, self.__iconlist_small, 16)

	def geticonid(self, name):
		rv = self.__iconname_to_index.get(name)
		if rv is None:
			rv = self.__iconname_to_index[None]
		return rv