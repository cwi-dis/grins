__version__ = "$Id$"

# HierarchyView dialog - Version for standard windowinterface
# XXXX Note: the separation is not correct: there are still things in HierarchyView
# that really belong here...

# @win32doc|HierarchyViewDialog
# This class represents the interface between the HierarchyView platform independent
# class and its implementation class _HierarchyView in lib/win32/_HierarchyView.py which 
# implements the actual view.

import string
from ViewDialog import ViewDialog
import WMEVENTS
import MMNode
import windowinterface

from usercmd import *
import MenuTemplate

typemap = {
	DRAG_PAR: 'par',
	DRAG_SEQ: 'seq',
	DRAG_SWITCH: 'switch',
	DRAG_EXCL: 'excl',
	DRAG_PRIO: 'prio',
	DRAG_MEDIA: 'ext',
	DRAG_ANIMATE: 'animate',
	DRAG_BRUSH: 'brush',
	}

class HierarchyViewDialog(ViewDialog):
	adornments = {}
	interior_popupmenu = MenuTemplate.POPUP_HVIEW_STRUCTURE
	leaf_popupmenu = MenuTemplate.POPUP_HVIEW_LEAF
	slide_popupmenu = MenuTemplate.POPUP_HVIEW_SLIDE
	transition_popupmenu = MenuTemplate.POPUP_HVIEW_TRANS
	event_popupmenu_source = MenuTemplate.POPUP_EVENT_SOURCE
	event_popupmenu_dest = MenuTemplate.POPUP_EVENT_DEST
	multi_popupmenu = MenuTemplate.POPUP_MULTI # For multiple selections.

	def __init__(self):
		ViewDialog.__init__(self, 'hview_')
	
	def show(self):
		if self.is_showing():
			self.window.pop(poptop=1)
			return
		self.load_geometry()
		if self.last_geometry:
			x, y, w, h = self.last_geometry
		else:
			x, y, w, h = -1, -1, -1, -1
		toplevel_window=self.toplevel.window
		self.window = toplevel_window.newview(x, y, w, h, 'Structured Timeline',
				units=windowinterface.UNIT_PXL,
				adornments = self.adornments,
				canvassize = (w, h),
				commandlist = self.commands,strid='hview_')

		# By the way, it might be helpful to know that a window here is a _StructView.
		# the window.register method is in a base class, win23window.py:register()
		self.window.register(WMEVENTS.Mouse0Press, self.mouse, None)
		self.window.register(WMEVENTS.Mouse0Release, self.mouse0release, None)
		self.window.register(WMEVENTS.ResizeWindow, self.redraw, None)
		self.window.register(WMEVENTS.PasteFile, self.pastefile, None)
		self.window.register(WMEVENTS.DragFile, self.__dragfile, None)
		self.window.register(WMEVENTS.DropFile, self.__dropfile, None)
		self.window.register(WMEVENTS.DragURL, self.__dragfile, None)
		self.window.register(WMEVENTS.DropURL, self.__dropfile, None)

		self.window.register(WMEVENTS.DragNode, self.dragnode, None)
		self.window.register(WMEVENTS.DropNode, self.dropnode, None)
		self.window.register(WMEVENTS.MouseMove, self.mousemove, None)
		self.window.register(WMEVENTS.DragEnd, self.dragend, None)

		self.window.register(WMEVENTS.QueryNode, self.querynode, None)

	def getparentwindow(self):
		# Used by machine-independent code to pass as parent
		# parameter to dialogs
		##return self.window
		import windowinterface
		return windowinterface.getmainwnd()

	def hide(self, *rest):
		self.save_geometry()
		self.window.close()
		self.window = None
		self.displist = None
		self.new_displist = None

	def fixtitle(self):
		pass

	def settoggle(self, command, onoff):
		self.window.set_toggle(command, onoff)

	def setcommands(self, commandlist):
		self.window.set_dynamiclist(TRANSITION, self.translist or [])
		self.window.set_commandlist(commandlist)

	def setpopup(self, template):
		self.window.setpopupmenu(template)

	def setstate(self):
		w = self.window
		w.set_toggle(THUMBNAIL, self.thumbnails)
		w.set_toggle(PLAYABLE, self.showplayability)
		w.set_toggle(TIMESCALE, self.root.showtime == 'focus')
		if self.get_selected_widget() is None:
			w.set_toggle(LOCALTIMESCALE, 0)
			w.set_toggle(CORRECTLOCALTIMESCALE, 0)
		else:
			n = self.get_selected_node()
			w.set_toggle(LOCALTIMESCALE, n.showtime == 'focus')
			w.set_toggle(CORRECTLOCALTIMESCALE, n.showtime == 'cfocus')
		w.set_toggle(TOGGLE_BWSTRIP, self.root.showtime == 'bwstrip')

	def helpcall(self):
		import Help
		Help.givehelp('Hierarchy')

	def __dragfile(self, dummy, window, event, params):
		# event handler for mouse moves while dragging a file over the window.
		self.droppable_widget = None
		x, y, filename = params
		if not (0 <= x < 1 and 0 <= y < 1):
			self.draw()
			return windowinterface.DROPEFFECT_NONE
		x = x * self.mcanvassize[0]
		y = y * self.mcanvassize[1]		
		obj = self.whichhit(x, y)
		# On the grey area we fail
		if not obj:
			rv = windowinterface.DROPEFFECT_NONE
			self.draw()
			return
		obj = obj.get_mmwidget()
		node = obj.get_node()
		# If the node accepts only certain mimetypes
		# we check for that too.
		mimetypes = node.getAllowedMimeTypes()
		if mimetypes:
			if event == WMEVENTS.DropFile:
				url = MMurl.pathname2url(filename)
			else:
				url = filename
			import urlcache
			mimetype = urlcache.mimetype(url)
			if mimetype:
				mimetype = string.split(mimetype, '/')[0]
			if not mimetype in mimetypes:
				if __debug__:
					print 'Type', mimetype, 'not in', mimetypes
				self.draw()
				return windowinterface.DROPEFFECT_NONE
		# All seems fine. Return copy or link depending on
		# the node type.
		if node.GetType() in MMNode.playabletypes:
			self.droppable_widget = obj
			rv = windowinterface.DROPEFFECT_LINK
		else:
			self.droppable_widget = obj
			rv = windowinterface.DROPEFFECT_COPY
		self.draw()
		return rv

	def pastefile(self, maybenode, window, event, params):
		import MMurl
		x, y, filename = params
		url = MMurl.pathname2url(filename)
		params = (x, y, url)
		self.dropfile(maybenode, window, event, params)

	def querynode(self, dummy, window, event, params):
		srcx, srcy = params
		srcx = srcx * self.mcanvassize[0]
		srcy = srcy * self.mcanvassize[1]
		srcwidget = self.whichhit(srcx, srcy)
		if srcwidget:
			srcnode = srcwidget.get_node()
			return 'NodeUID', srcnode
		return None, None

	def __dragparams(self, dstx, dsty, ucmd, args):
		srcnode = None
		srctype = None
		if ucmd == DRAG_NODE:
			srcx, srcy = args
			srcx = srcx * self.mcanvassize[0]
			srcy = srcy * self.mcanvassize[1]
			srcwidget = self.whichhit(srcx, srcy)
			if srcwidget is not None:
				srcnode = srcwidget.get_node()
				srctype = srcnode.GetType()
		elif ucmd == DRAG_NODEUID:
			contextid, nodeuid = args
			if contextid != id(self.root.context):
				print "Cannot drag/drop between documents"
				windowinterface.beep()
				return None
			srcnode = self.root.context.mapuid(nodeuid)
			srctype = srcnode.GetType()
		else:
			srctype = typemap.get(ucmd)
		dstwidget = self.whichhit(dstx, dsty)
		if dstwidget is not None:
			dstwidget = dstwidget.get_mmwidget()
			dstnode = dstwidget.get_node()
			dsttype = dstnode.GetType()
		else:
			dstnode = dsttype = None
		return srcnode, srctype, dstwidget, dstnode, dsttype

	def dragnode(self, dummy, window, event, params):
		# event handler for dragging a node over the window.
		dstx, dsty, cmd, ucmd, args = params
		self.droppable_widget = None
		if not (0 <= dstx < 1 and 0 <= dsty < 1):
			self.draw()
			return windowinterface.DROPEFFECT_NONE
		dstx = dstx * self.mcanvassize[0]
		dsty = dsty * self.mcanvassize[1]
		res = self.__dragparams(dstx, dsty, ucmd, args)
		if res is None:
			return windowinterface.DROPEFFECT_NONE
		srcnode, srctype, dstwidget, dstnode, dsttype = res
		rv = windowinterface.DROPEFFECT_NONE
		if dstnode:
			if cmd == 'move':
				if srcnode is not None and srcnode.IsAncestorOf(dstnode):
					# not allowed to move to a descendant
					xrv = windowinterface.DROPEFFECT_NONE
				else:
					xrv = windowinterface.DROPEFFECT_MOVE
			else:
				xrv = windowinterface.DROPEFFECT_COPY
			if srctype in ('anchor', 'animpar'):
				# anchor and animpar can only be dropped on media nodes
				if dsttype in MMNode.mediatypes:
					rv = xrv
			elif srctype == 'prio':
				# priorityClass can only be dropped on excl nodes
				if dsttype == 'excl':
					rv = xrv
			elif dsttype in MMNode.interiortypes:
				rv = xrv
			if rv != windowinterface.DROPEFFECT_NONE:
				self.droppable_widget = dstwidget
		self.draw()
		return rv

	def dragend(self, dummy, window, event, params):
		self.droppable_widget = None
		self.draw()
			
	def dropnode(self, dummy, window, event, params):
		# event handler for dropping the node.
		dstx, dsty, cmd, ucmd, args = params
		self.droppable_widget = None
		if not (0 <= dstx < 1 and 0 <= dsty < 1):
			self.draw()
			return windowinterface.DROPEFFECT_NONE
		dstx = dstx * self.mcanvassize[0]
		dsty = dsty * self.mcanvassize[1]
		res = self.__dragparams(dstx, dsty, ucmd, args)
		if res is None:
			return windowinterface.DROPEFFECT_NONE
		srcnode, srctype, dstwidget, dstnode, dsttype = res
		# filter out disallowed drops
		if srctype in ('anchor', 'animpar') and dsttype not in MMNode.mediatypes:
			return windowinterface.DROPEFFECT_NONE
		if srctype == 'prio' and dsttype != 'excl':
			return windowinterface.DROPEFFECT_NONE
		if ucmd in (DRAG_PAR, DRAG_SEQ, DRAG_SWITCH, DRAG_EXCL,
				DRAG_PRIO, DRAG_MEDIA, DRAG_ANIMATE, DRAG_BRUSH):
			return self.dropnewstructnode(ucmd, (dstx, dsty))
		elif ucmd in (DRAG_NODE, DRAG_NODEUID):
			rv = self.dropexistingnode(cmd, (dstx, dsty), srcnode)
			if rv == 'copy':
				return windowinterface.DROPEFFECT_COPY
			elif rv == 'move':
				return windowinterface.DROPEFFECT_MOVE
			elif rv == 'link':
				return windowinterface.DROPEFFECT_LINK
			else:
				return windowinterface.DROPEFFECT_NONE
		elif ucmd in (DRAG_REGION, DRAG_TOPLAYOUT):
			return windowinterface.DROPEFFECT_NONE
		else:
			print "Unknown dragged usercmd:", ucmd
			return windowinterface.DROPEFFECT_NONE

	def __dropfile(self, maybenode, window, event, params):
		self.droppable_widget = None
		self.dropfile(maybenode, window, event, params)

	# this method is called when the mouse is dragged
	# begin != 0 means that you start the drag, otherwise, assume that the drag is finished
	# on some plateform (at least Windows), it allows to tell to the system to continue to
	# send the event even if the mouse go outside the window (during dragging)
	def mousedrag(self, begin):
		if begin == 1:
			self.window.SetCapture()
		else:
			self.window.ReleaseCapture()
