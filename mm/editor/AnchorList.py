__version__ = "$Id$"

import AnchorDefs

class AnchorList:
	# the following attributes are expected to exist:
	# _list - list control
	# _new - button control
	# _rename - button control
	# _delete - button control
	# _link - button control
	# _type - check button control
	# _xywh - control for x,y,w,h coordinates (may include visual aspect)
	# _se - control for start,end times
	# _bplay, _bpause,_bstop - play control buttons
	# 
	# All controls are expected to support the method enable which takes
	# one argument: 0 to disable (make insensitive), 1 to enable.
	# The _xywh and _se controls have the following methods:
	# clear() - clear the control (empty text, remove box in _xywh)
	# getval() - return list/tuple of values (integers for _xywh, floats for _se)
	# setval(list) - set new values, arg is list of ints (_xywh) or floats (_se)
	# _list has the following additional methods:
	# resetcontent() - remove all elements in the list (always
	#	immediately followed by addlistitems)
	# addlistitems(list) - add items in list to the list control
	#	(always preceded by resetcontent)
	# setcursel(index) - set the current selection to the element
	#	with the given index (zero-based), None for no current
	#	selection.
	#
	# _type has the following additional method:
	# setcheck(onoff) - set or clear the check mark
	# getcheck() - get current value for check mark
	#
	# The base class is expected to implement the following methods:
	# create_box(getbox) - create/remove the anchor box.  If
	#	getbox==0, no box should be drawn but it should be
	#	possible to start drawing one, if getbox!=0, an
	#	initial box should be drawn based on the value of
	#	_xywh.getval()
	# askanchorname() - pop up a dialog to ask for an anchor name.
	#	This calls the callback newanchor with the name
	#	(possibly empty) and partial=1.
	# enableApply() - enable the Apply button
	#
	# Extra behavior:
	# The New button pops up a dialog to ask for an anchor name.
	#	The callback for this dialog calls newanchor with the
	#	anchor name (possibly empty) and partial=0 (default).
	#
	# The Hyperlink button calls linkcb with the
	#	AttrEdit.AnchorlistAttrEditorField instance as
	#	argument.
	#
	# The Type check button callback is typecb(). The machine-dependent
	# code may have to call editcb() first to obtain xywh values.
	#
	# The Rename button pops up a dialog asking for a new anchor
	#	name.  The dialog callback is renamecb with the name
	#	as argument.
	#
	# The Edit button callback is editcb(). The machine dependent code
	# is responsible for calling fill() to update the visual box.
	#
	# Setbox is the callback to set a new box through the visual area.
	# The machine dependent code should call fill() afterwards to copy
	# the new data to the other fields.
	#
	# The callback when an item in the list of anchors is selected
	#	is listcb(index) where index is the (zero-based) index
	#	of the item selected or None if no item is selected.

	def __init__(self):
		self.__curanchor = None

	def getcurrent(self):
		return self.__curanchor

	def setvalue(self, anchors):
		self.__anchorlinks = anchors

	def getvalue(self):
		return self.__anchorlinks

	def enable(self, enable):
		if enable:
			self._list.enable(1)
			self.fill()	# enables the rest
		else:
			self._list.enable(0)
			self._new.enable(0)
			self._rename.enable(0)
			self._delete.enable(0)
			self._link.enable(0)
			self._type.enable(0)
			self._xywh.enable(0)
			self._se.enable(0)
			self._bplay.enable(0)
			self._bpause.enable(0)
			self._bstop.enable(0)

	def fill(self, newlist = 1, nocreatebox = 0):
		if newlist:
			self.__anchors = self.__anchorlinks.keys()
			self.__anchors.sort()
			self._list.resetcontent()
			self._list.addlistitems(self.__anchors)
		if self.__curanchor is not None and not self.__anchorlinks.has_key(self.__curanchor):
			self.__curanchor = None
		if not nocreatebox:
			self.create_box(0)
		if self.__curanchor is None:
			self._list.setcursel(None)
			self._type.enable(0)
			self._rename.enable(0)
			self._delete.enable(0)
			self._link.enable(0)
			self._xywh.clear()
			self._xywh.enable(0)
			self._se.clear()
			self._se.enable(0)
		else:
			a = self.__anchorlinks[self.__curanchor]
			i = self.__anchors.index(self.__curanchor)
			self._list.setcursel(i)
			atype, aargs, times, access = a[:4]
			self._rename.enable(1)
			self._delete.enable(1)
			self._link.enable(len(a) == 5)
			self._type.enable(1)
			if (atype not in AnchorDefs.WholeAnchors) and aargs[0] == AnchorDefs.A_SHAPETYPE_RECT:
				# Warning: this statement work for now only for rect shape.
				# it shouldn't be called for any other shape type
				
				# for now, keep the compatibility with old structure
				aargs = [aargs[1], aargs[2], aargs[3] - aargs[1], aargs[4] - aargs[2]]
				
				self._type.setcheck(1)
				self._xywh.enable(1)
				self._se.enable(1)
				self._se.setval(times)
				if aargs:
					# maybe convert to pixel values
					naargs = self.__convert(aargs)
				self.setbox(naargs or None)
				if not nocreatebox:
					self.create_box(1)
			else:
				self._type.setcheck(0)
				self._xywh.clear()
				self._xywh.enable(0)
				self._se.clear()
				self._se.enable(0)

	def listcb(self, i):
		if i is None:
			self.__curanchor = None
		else:
			self.__curanchor = self.__anchors[i]
		self.fill(newlist = 0)

	def getbox(self, saved):
		if self.__curanchor is None:
			return None
		atype, aargs = self.__anchorlinks[self.__curanchor][:2]
		
		# for now keep the compatibility with old structure
		if aargs[0] ==  AnchorDefs.A_SHAPETYPE_RECT:
			aargs = [aargs[1], aargs[2], aargs[3] - aargs[1], aargs[4] - aargs[2]]
		else:
			aargs = [0, 0, 0, 0]

		if atype not in AnchorDefs.WholeAnchors:
			if saved:
				return aargs or None
			return self._xywh.getval()
		return None

	# Warning: this method work for now only for rect shape.
	# it shouldn't be called for any other shape type
	def setbox(self, box = None):
		if self.__curanchor is None:
			if box is not None:
				# new anchor, ask for name
				self.__box = box
				self.askanchorname()
			return None
		atype, aargs = self.__anchorlinks[self.__curanchor][:2]
		
		# for now keep the compatibility with old structure
		if aargs[0] ==  AnchorDefs.A_SHAPETYPE_RECT:
			aargs = [aargs[1], aargs[2], aargs[3] - aargs[1], aargs[4] - aargs[2]]
		else:
			aargs = [0, 0, 0, 0]

		if atype not in AnchorDefs.WholeAnchors:
			if box:
				while len(aargs) < len(box):
					aargs.append(0)
				for i in range(4):
					aargs[i] = int(box[i] + .5)
				self._xywh.setval(aargs)
			else:
				aargs[:] = []
				self._xywh.clear()
			self.enableApply()

	def newanchor(self, name, partial = 0):
		if partial:
			box = self.__box
			del self.__box
		if not name:
			# no name, do we want to give an error message?
##			self.showmessage('No name given', mtype = 'error')
			return
		if self.__anchorlinks.has_key(name):
			# not unique, so don't change
			self.showmessage('Name should be unique', mtype = 'error')
			return
		if partial:
			atype = AnchorDefs.ATYPE_NORMAL
		else:
			atype = AnchorDefs.ATYPE_WHOLE
		self.__anchorlinks[name] = atype, [], (0,0), None, [], ''
		self.__curanchor = name
		self.fill()
		if partial:
			self.setbox(box)
			self.fill()

	def renamecb(self, name):
		if name == self.__curanchor:
			# no change, so do nothing
			return
		if not name:
			# no name, do we want to give an error message?
##			self.showmessage('No name given', mtype = 'error')
			return
		if self.__anchorlinks.has_key(name):
			# not unique, so don't change
			self.showmessage('Name should be unique', mtype = 'error')
			return
		a = self.__anchorlinks[self.__curanchor]
		if len(a) == 5:
			# remember original name
			a = a + (self.__curanchor,)
		self.__anchorlinks[name] = a
		del self.__anchorlinks[self.__curanchor]
		self.__curanchor = name
		self.fill()

	def deletecb(self):
		if self.__curanchor is None:
			return
		del self.__anchorlinks[self.__curanchor]
		self.__curanchor = None
		self.fill()
		self.enableApply()

	def fixtype(self):
		if self.__curanchor is None:
			return
		a = self.__anchorlinks[self.__curanchor]
		if self._type.getcheck():
			atype = AnchorDefs.ATYPE_NORMAL
		else:
			atype = AnchorDefs.ATYPE_WHOLE
		self.__anchorlinks[self.__curanchor] = (atype,) + a[1:]

	def typecb(self):
		if self.__curanchor is None:
			return
		self.fixtype()
		self.fill(newlist = 0)
		self.enableApply()

	def linkcb(self, attr):
		if self.__curanchor is None:
			return
		attr.wrapper.toplevel.links.show(attr.wrapper.node,
						 self.__curanchor)

	def editcb(self):
		if self.__curanchor is None:
			return
		a = self.__anchorlinks[self.__curanchor]
		aargs = self._xywh.getval()
		
		# for now keep the compatibility with old structure
		if aargs == [0,0,0,0]:
			aargs = [AnchorDefs.A_SHAPETYPE_ALLREGION]
		else:
			aargs = [AnchorDefs.A_SHAPETYPE_RECT,aargs[0],aargs[1],aargs[0]+aargs[2],
					aargs[1]+aargs[3]]
			
		times = self._se.getval()
		self.__anchorlinks[self.__curanchor] = (a[0], aargs, tuple(times)) + a[3:]
		self.enableApply()

	# Warning: this method work for now only for rect shape.
	# it shouldn't be called for any other shape type
	def __convert(self, aargs):
		need_conversion = 0
		for a in aargs:
			if a != int(a): # any floating point number
				need_conversion = 1
				break
		if not need_conversion and tuple(aargs) != (0,0,1,1):
			return aargs
		xsize, ysize = self._wnd._imagesize
		return [int(float(aargs[0]) * xsize + .5),
			    int(float(aargs[1]) * ysize + .5),
			    int(float(aargs[2]) * xsize + .5),
			    int(float(aargs[3]) * ysize + .5)]
