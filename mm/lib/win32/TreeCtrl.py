__version__ = "$Id$"

import win32ui

import win32con
import commctrl

from win32mu import Win32Msg

from pywin.mfc import window

debug = 0

EVENT_SRC_LButtonDown, EVENT_SRC_Expanded, EVENT_SRC_KeyDown = range(3)

class TreeCtrl(window.Wnd):
	def __init__ (self, dlg=None, resId=None ):
		# if the tree res is specified from a dialox box, we just create get the existing instance
		# if try to re-create it, the focus doesn't work, and you get some very unexpected behavior
		if resId != None:
			self.parent = dlg
			ctrl = dlg.GetDlgItem(resId)
		else:
			ctrl = win32ui.CreateTreeCtrl()
		window.Wnd.__init__(self, ctrl)
		self._selections = []
		self._multiSelListeners = []
		self._expandListeners = []
		self._selEventSource = None

		self.__selecting = 0
		if resId != None:		
			self._setEvents()
		
	# create a new instance of the tree ctrl.
	# Note: don't call this method, if the tree widget come from a dialog box
	def create(self, parent, rc, id):
		style = win32con.WS_VISIBLE | commctrl.TVS_HASBUTTONS |\
				commctrl.TVS_HASLINES | commctrl.TVS_SHOWSELALWAYS |\
				win32con.WS_BORDER | win32con.WS_TABSTOP\
				 | commctrl.TVS_LINESATROOT
		self.parent = parent
		self.CreateWindow(style, rc, parent, id)
		self._setEvents()
		
	# set the events that we manage in the tree widget
	def _setEvents(self):
		self.HookMessage(self.OnLButtonDown, win32con.WM_LBUTTONDOWN)
		self.HookMessage(self.OnKeyDown, win32con.WM_KEYDOWN)
		self.HookMessage(self.OnLButtonUp, win32con.WM_LBUTTONUP)
		self.parent.HookNotify(self.OnSelChanged, commctrl.TVN_SELCHANGED)
		self.HookMessage(self.OnDump, win32con.WM_USER+1)
		self.parent.HookNotify(self.OnExpanded,commctrl.TVN_ITEMEXPANDED)
		self.HookMessage(self.OnKillFocus,win32con.WM_KILLFOCUS)
		self.HookMessage(self.OnSetFocus,win32con.WM_SETFOCUS)
		
#	def createAsDlgItem(self, dlg, id):
#		wnd = dlg.GetDlgItem(id)
#		rc = wnd.GetWindowRect()
#		wnd.DestroyWindow()
#		rc = dlg.ScreenToClient(rc)
#		self.create(dlg, rc, id)

	def __clearMultiSelect(self, hititem):
		for item in self._selections:
			if item != hititem:
				try:
					self.SetItemState(item, 0, commctrl.TVIS_SELECTED)
				except:
					# the item may already be removed
					pass

		self._selections = [hititem]
		self.SetItemState(hititem, commctrl.TVIS_SELECTED, commctrl.TVIS_SELECTED)
		self.OnMultiSelChanged()

	#
	# handler methods for the standard windows events
	#
	
	def OnLButtonDown(self, params):
		msg = Win32Msg(params)
		point = msg.pos()
		flags = msg._wParam

		self._selEventSource = EVENT_SRC_LButtonDown

		hitflags, hititem = self.HitTest(point)
		if not (hitflags & commctrl.TVHT_ONITEM):
			if debug: self.scheduleDump()
			return 1

		if not (flags & win32con.MK_CONTROL):
			# remove multi-select mode
#			nsel = len(self._selections)
			self.__clearMultiSelect(hititem)

			# do a normal selection/deselection
			return 1
		
		# enter multi-select mode

		# if the focus is not set, set it. 
		self.SetFocus()
		
		# selected item on entry
		try: 
			selitem = self.GetSelectedItem()
			if selitem:
				selstate = self.GetItemState(selitem, commctrl.TVIS_SELECTED)
		except: 
			selitem = None
		nsel = len(self._selections)

		# select/deselect normally hit item the same way base would do
		hitstate = self.GetItemState(hititem, commctrl.TVIS_SELECTED)
		if hitstate & commctrl.TVIS_SELECTED:
			self.SetItemState(hititem, 0, commctrl.TVIS_SELECTED)
			self.removeSelection(hititem)
		else:
			self.SelectItem(hititem)
			self.SetItemState(hititem, commctrl.TVIS_SELECTED, commctrl.TVIS_SELECTED)
			self.appendSelection(hititem)
		
		# restore selection of previously selected item once not the hit item
		if nsel > 0:
			if selitem and selitem!=hititem and (selstate & commctrl.TVIS_SELECTED):
				self.SetItemState(selitem, commctrl.TVIS_SELECTED, commctrl.TVIS_SELECTED)

#		# keep always at least one selection
#		if not self._selections:
#			self.SetItemState(hititem, commctrl.TVIS_SELECTED, commctrl.TVIS_SELECTED)
#			self.appendSelection(hititem)
		
		# motify listeners
		if nsel != len(self._selections):
			self.OnMultiSelChanged()

		# absorb event		
		return 0

	def OnLButtonUp(self, params):
		return 1

	def OnExpanded(self, std, extra):
		self._selEventSource = EVENT_SRC_Expanded
		nsel = len(self._selections)
		action, itemOld, itemNew, ptDrag = extra
		# XXX the field number doesn't correspond with API documention ???
		item, field2, field3, field4, field5, field6, field7, field8 = itemNew

		self.__changed = 0
		if action == commctrl.TVE_COLLAPSE:
			# when a node is collapsed, unselect as well all these children which becomes unvisible.
			self.__unselectChildren(item)

			# when you collapse a node, the standard behavior change automaticly
			# the focus on the node wich is collapsed. So, according to the auto selecting
			# we have to update as well the multi-select variable state
			try: 
				selitem = self.GetSelectedItem()
				if selitem:
					# default state
					oldstate =  selitem in self._selections
					# new state
					selstate = self.GetItemState(selitem, commctrl.TVIS_SELECTED)
					if not oldstate and (selstate & commctrl.TVIS_SELECTED):
						self.__changed = 1
						self._selections.append(selitem)
			except:
				pass

		# update the listener
		for listener in self._expandListeners:
			listener.OnExpandChanged(item, action != commctrl.TVE_COLLAPSE)

		# if any changement, update the listeners			
		if self.__changed:
			self.OnMultiSelChanged()
		return 1

	def OnKeyDown(self, params):
		self._selEventSource = EVENT_SRC_KeyDown
		return 1
		
	def OnSelChanged(self, std, extra):
		nsel = len(self._selections)

		# Important note: these line allow to detect, if there is an auto select (by the system) due to an initial focus
		# in this case, we reset the selection
		if nsel == 0:
			try: 
				selitem = self.GetSelectedItem()
				if selitem:
					selstate = self.GetItemState(selitem, commctrl.TVIS_SELECTED)
			except: 
				selitem = None

			if selitem and (selstate & commctrl.TVIS_SELECTED):
				self.SetItemState(selitem, 0, commctrl.TVIS_SELECTED)
			return
		
		action, itemOld, itemNew, ptDrag = extra
		# XXX the field number doesn't correspond with API documention ???
		item, field2, field3, field4, field5, field6, field7, field8 = itemNew

		if self._selEventSource not in (EVENT_SRC_Expanded, EVENT_SRC_LButtonDown):
			self.__clearMultiSelect(item)

		self._selEventSource = None
		
		if debug:
			self.scheduleDump()

	def OnKillFocus(self, params):
		# update the selected items.
		# Note: the look is not the same when a item is selected or unselected
		self.__updateSelectedItems()

		# continu a normal processing		
		return 1

	def OnSetFocus(self, params):
			
		# update the selected items.
		# Note: the look is not the same when a item is selected or unselected
		self.__updateSelectedItems()

		# continu normal processing		
		return 1

	#
	# 
	#

	def SelectItemList(self, list):
		# don't update the listener when selecting
		self.__selecting = 1

		# remove items not selected anymore
		itemToRemove = []
		for cItem in self._selections:
			if cItem not in list:
				itemToRemove.append(cItem)
		for cItem in itemToRemove:	
			try:			
				self.SetItemState(cItem, 0, commctrl.TVIS_SELECTED)
			except:
				# the node may be already removed
				pass
			self.removeSelection(cItem)

		if len(list) > 0:				
			firstItemList = list[:-1]
			lastItem = list[-1]
			# for all items except the last, select/deselect with SetItemState
			for item in firstItemList:
				state = self.GetItemState(item, commctrl.TVIS_SELECTED)
				if not state & commctrl.TVIS_SELECTED:
					self.SetItemState(item, commctrl.TVIS_SELECTED, commctrl.TVIS_SELECTED)
					self.appendSelection(item)

			# remind the current item selected
			try: 
				selitem = self.GetSelectedItem()
				if selitem:
					selstate = self.GetItemState(selitem, commctrl.TVIS_SELECTED)
			except: 
				selitem = None

			# for the last item, select normally item the same way base would do
			self.SelectItem(lastItem)
			self.SetItemState(lastItem, commctrl.TVIS_SELECTED, commctrl.TVIS_SELECTED)
			self.appendSelection(lastItem)
		
			# restore selection of previously selected item once not the hit item
			if selitem and selitem!=lastItem and (selstate & commctrl.TVIS_SELECTED):
				self.SetItemState(selitem, commctrl.TVIS_SELECTED, commctrl.TVIS_SELECTED)	
				self.appendSelection(selitem)
			
		self.__selecting = 0
				
	# unselect all children of the item
	def __unselectChildren(self, item):
		try:
			child = self.GetChildItem(item)
		except:
			child = None			
		while child != None:
			if child in self._selections:
				self.SetItemState(child, 0, commctrl.TVIS_SELECTED)
				self._selections.remove(child)
				self.__changed = 1
			if child != None:
				self.__unselectChildren(child)
			try:
				child = self.GetNextSiblingItem(child)
			except:
				child = None

	def __updateSelectedItems(self):
		rc = self.GetWindowRect()
		rc = self.parent.ScreenToClient(rc)
		self.parent.InvalidateRect( rc )

	# update the listener				
	def OnMultiSelChanged(self):
		# don't update the listener when selecting
		# avoid some recursive problems
		if not self.__selecting:
			for listener in self._multiSelListeners:
				listener.OnMultiSelChanged()
			if debug:
				self.scheduleDump()

	# add an expand listener 
	def addExpandListener(self, listener):
		if hasattr(listener, 'OnExpandChanged') and\
			listener not in self._expandListeners:
			self._expandListeners.append(listener)

	# remove an expand listener
	def removeExpandListener(self, listener):
		if listener in self._expandListeners:
			self._expandListeners.remove(listener)
		
	# add a listener 
	def addMultiSelListener(self, listener):
		if hasattr(listener, 'OnMultiSelChanged') and\
			listener not in self._multiSelListeners:
			self._multiSelListeners.append(listener)

	# remove a listener
	def removeMultiSelListener(self, listener):
		if listener in self._multiSelListeners:
			self._multiSelListeners.remove(listener)

	def DeleteItem(self, item):
		state = self.GetItemState(item, commctrl.TVIS_SELECTED)
		# if this item is already selected, unselect it, and remove from selected list
		if state & commctrl.TVIS_SELECTED:
			self.SetItemState(item, 0, commctrl.TVIS_SELECTED)
		if item in self._selections:
			self._selections.remove(item)
		
		self._obj_.DeleteItem(item)
		
	def appendSelection(self, item):
		if item not in self._selections:
			self._selections.append(item)

	def removeSelection(self, item):
		if item in self._selections:
			self._selections.remove(item)

	def getSelectedItems(self):
		return self._selections

	# debug methods		
	def OnDump(self, params):
		print self.getSelectedItems()

	def scheduleDump(self):
		self.PostMessage(win32con.WM_USER+1)

	def insertLabel(self, text, parent, after):
		return self.InsertItem(commctrl.TVIF_TEXT, text, 0, 0, 0, 0, None, parent, after)
	
 