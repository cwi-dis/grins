# This file contains a list of standard widgets used in the
# HierarchyView. I tried to keep them view-independant, but
# I can't promise anything!!

__version__ = "$Id$"

import Widgets
import MMurl, MMAttrdefs, MMmimetypes, MMNode, MMTypes
import features
import os, windowinterface
import settings
import TimeMapper
from AppDefaults import *
from fmtfloat import fmtfloat
import Duration

TIMELINE_AT_TOP = 1
TIMELINE_IN_FOCUS = 1
NAMEDISTANCE = 150
SPACEWIDTH = f_title.strsizePXL(' ')[0]

ICONSIZE = windowinterface.ICONSIZE_PXL
ARROWCOLOR = (0,255,0)

EPSILON = GAPSIZE

######################################################################
# Create new widgets

def create_MMNode_widget(node, mother, parent = None):
	assert mother != None
	ntype = node.GetType()
	if mother.usetimestripview:
		# We handle toplevel, second-level and third-level nodes differently
		# in snap
		pnode = node.GetParent()
		if pnode is None and ntype == 'seq':
			# Don't show toplevel root (actually the <body> in SMIL)
			return UnseenVerticalWidget(node, mother, parent)
		gpnode = pnode.GetParent() # grand parent node
		if pnode is not None and gpnode is None and ntype == 'par':
			# Don't show second-level par either
			return UnseenVerticalWidget(node, mother, parent)
		if pnode is not None and gpnode is not None and gpnode.GetParent() is None and ntype == 'seq':
			# And show secondlevel seq as a timestrip
			return TimeStripSeqWidget(node, mother, parent)
	if ntype == 'seq':
		return SeqWidget(node, mother, parent)
	elif ntype == 'par':
		return ParWidget(node, mother, parent)
	elif ntype == 'switch':
		return SwitchWidget(node, mother, parent)
	elif ntype == 'ext':
		return MediaWidget(node, mother, parent)
	elif ntype == 'imm':
		return MediaWidget(node, mother, parent)
	elif ntype == 'excl':
		return ExclWidget(node, mother, parent)
	elif ntype == 'prio':
		return PrioWidget(node, mother, parent)
	elif ntype == 'brush':
		return MediaWidget(node, mother, parent)
	elif ntype == 'animate':
		return MediaWidget(node, mother, parent)
	elif ntype == 'prefetch':
		return MediaWidget(node, mother, parent)
	elif ntype == 'comment':
		return CommentWidget(node, mother, parent)
	elif ntype == 'foreign':
		return ForeignWidget(node, mother, parent)
	else:
		raise "Unknown node type", ntype
		return None



##############################################################################
# Abstract Base classes
##############################################################################

#
# The MMNodeWidget represents any widget which is representing an MMNode
# It also handles callbacks from the window interface.
#
class MMNodeWidget(Widgets.Widget):  # Aka the old 'HierarchyView.Object', and the base class for a MMNode view.
	# View of every MMNode within the Hierarchy view
	def __init__(self, node, mother, parent):
		assert isinstance(node, MMNode.MMNode)
		assert mother is not None
		Widgets.Widget.__init__(self, mother)
		self.node = node			   # : MMNode
		self.name = MMAttrdefs.getattr(node, 'name')
		self.node.views['struct_view'] = self
		self.old_pos = None	# used for recalc optimisations.
		self.dont_draw_children = 0

		self.timemapper = None
		self.timeline = None
		self.need_draghandles = None

		# Holds little icons..
		self.iconbox = IconBox(self, self.mother)
		self.cause_event_icon = None
		self.infoicon = None
		if node.infoicon:
			self.infoicon = self.iconbox.add_icon(node.infoicon, callback = self.show_mesg)
		if node.GetType() == 'comment':
			self.playicon = None
		else:
			# XXXX Comment by Jack: Why is this not done through the IconBox?
			# XXXX Answer by Jack: it may be doable now, now that IconBox semantics
			#      don't move things around anymore.
			self.playicon = Icon(self, self.mother)
			self.playicon.set_properties(selectable=0, callbackable=0)
		# these 5 are never set in this class but are provided for the benefit of subclasses
		# this means we also don't destroy these
		self.collapsebutton = None
		self.transition_in = None
		self.transition_out = None
		self.dropbox = None
		self.channelbox = None

		linkicons = self.getlinkicons()
		for icon in linkicons:
			self.iconbox.add_icon(icon)

	def __repr__(self):
		return '<%s instance, name="%s", node=%s, id=%X>' % (self.__class__.__name__, self.name, `self.node`, id(self))

	def destroy(self):
		# Prevent cyclic dependancies.
		node = self.node
		if self.playicon is not None:
			self.playicon.destroy()
			self.playicon = None
		self.cause_event_icon = None
		self.infoicon = None
		if self.iconbox is not None:
			self.iconbox.destroy()
			self.iconbox = None
		if self.timeline is not None:
			self.timeline.destroy()
			self.timeline = None
		if self.timemapper is not None:
			self.timemapper = None
		if node is not None:
			node.views['struct_view'] = None
			del node.views['struct_view']
			node.set_armedmode = None
			del node.set_armedmode
			node.set_infoicon = None
			del node.set_infoicon
			self.node = None
		Widgets.Widget.destroy(self)

	def set_armedmode(self, mode, redraw = 1):
		if not mode:
			mode = 'idle'
		if self.playicon.icon == mode:
			# nothing to do
			return
		self.playicon.set_icon(mode)
		if redraw:
			self.mother.playicons.append(self)
			if self.mother.extra_displist is not None:
				d = self.mother.extra_displist.clone()
			else:
				d = self.mother.base_display_list.clone()
			self.playicon.draw(d)
			d.render()
			if self.mother.extra_displist is not None:
				self.mother.extra_displist.close()
			self.mother.extra_displist = d

	def remove_set_armedmode(self):
		pass

	def add_set_armedmode(self):
		pass

	def get_node(self):
		return self.node

	def add_event_icons(self):
		self.__add_events_helper('beginevent', 'beginlist')
		self.__add_events_helper('endevent', 'endlist')

	def __add_events_helper(self, iconname, attr):
		icon = None
		for arc in MMAttrdefs.getattr(self.node, attr):
			othernode = arc.refnode()
			if othernode:
				if not othernode.views.has_key('struct_view'):
					print "DEBUG: Node is not in the structure view: ", othernode
					continue
				otherwidget = othernode.views['struct_view'].get_cause_event_icon()
				if icon is None:
					icon = self.iconbox.add_icon(iconname, arrowto = otherwidget).set_properties(arrowable=1,initattr=attr).set_contextmenu(self.mother.event_popupmenu_dest)
				else:
					icon.add_arrow(otherwidget)
				otherwidget.add_arrow(icon)
			else: # no arrow.
				if icon is None:
					icon = self.iconbox.add_icon(iconname).set_properties(arrowable=1,initattr=attr).set_contextmenu(self.mother.event_popupmenu_dest)

	def uncollapse_all(self):
		# Placeholder for a recursive function.
		return

	def collapse_all(self):		  # Is this doable using a higher-order function?
		return

	def isvisible(self):
		# a node is visible if none of its ancestors is collapsed
		for node in self.node.GetPath()[:-1]:
			if node.collapsed:
				return 0
		return 1

	def makevisible(self):
		for node in self.node.GetPath()[:-1]:
			if node.collapsed:
				node.views['struct_view'].uncollapse()
		#self.mother.need_redraw = 1

	def adddependencies(self, timemapper):
		t0, t1, t2, download, begindelay = self.GetTimes('virtual')
		w, h = self.get_minsize()
		if t0 != t2:
			timemapper.adddependency(t0, t2, w)

	def addcollisions(self, mastert0, mastertend, timemapper, mytimes = None):
		edge = 0
		if mytimes is not None:
			t0, t1, t2, download, begindelay = mytimes
		else:
			t0, t1, t2, download, begindelay = self.GetTimes('virtual')
		tend = t2
		if mastertend is not None and tend > mastertend:
			tend = mastertend
		if download:
			# Slightly special case. We register a collision on t0, and then continue
			# computing with t0 minus the delays
			timemapper.addcollision(t0, edge)
			t0 = t0 - (download)
		ledge = redge = edge
		if isinstance(self, MediaWidget):
			dur = Duration.get(self.node, ignoreloop = 1, wanterror = 0)	# what gets repeated
			ad = Duration.get(self.node, wanterror = 0)
			if ad > t2 - t0:
				ad = t2 - t0
			if dur > ad:
				dur = ad
			if dur == 0 < tend - t0:
				timemapper.addcollision(t0, 4*HEDGSIZE)
				ledge = ledge + 4*HEDGSIZE
		if t0 == tend:
			w, h = self.get_minsize()
			if t0 == mastertend:
				redge = redge + w
			elif t0 == mastert0:
				ledge = ledge + w
			else:
				timemapper.addcollision(t0, w+2*edge)
		elif t0 == t1:
			ledge = 4*HEDGSIZE
			timemapper.addcollision(t0, ledge)
		if t0 != mastert0:
			timemapper.addcollision(t0, ledge)
			ledge = 0
		if tend != mastertend:
			timemapper.addcollision(tend, redge)
			redge = 0
		return ledge, redge

	def init_timemapper(self, timemapper):
		if not self.node.WillPlay():
			return None
		if timemapper is None and self.node.showtime:
			if self.node.GetType() in ('excl', 'prio'):
				showtime = self.node.showtime
				self.node.showtime = 0
				for c in self.children:
					c.node.showtime = showtime
			else:
				timemapper = TimeMapper.TimeMapper()
				if self.timeline is None:
					self.timeline = TimelineWidget(self, self.mother)
				self.timemapper = timemapper
		else:
			if self.timeline is not None:
				self.timeline.destroy()
				self.timeline = None
			if self.timemapper is not None:
				self.timemapper = None
		return timemapper

	def fix_timemapper(self, timemapper):
		if timemapper is not None:
			self.adddependencies(timemapper)
			if self.timemapper is not None:
				t0, t1, t2, download, begindelay = self.GetTimes('virtual')
				p0, p1 = self.addcollisions(t0, t2, timemapper, (t0, t1, t2, download, begindelay))
				self.timemapper.addcollision(t0, p0)
				self.timemapper.addcollision(t2, p1)
				min_pxl_per_sec = 0
				if self.timeline is None or self.timeline.minwidth == 0:
					try:
						min_pxl_per_sec = self.node.__min_pxl_per_sec
					except AttributeError:
						pass
				self.node.__min_pxl_per_sec = timemapper.calculate(self.node.showtime == 'cfocus', min_pixels_per_second = min_pxl_per_sec)
				t0, t1, t2, dummy, dummy = self.GetTimes('virtual')
				w = timemapper.time2pixel(t2, align='right') - timemapper.time2pixel(t0)
				if w > self.boxsize[0]:
					self.boxsize = w, self.boxsize[1]

	def pixel2time(self, pxl, side, timemapper):
		t0, t1, t2, download, begindelay = self.GetTimes('virtual')
		# duration = t1 - t0
		if timemapper is not None:
			t = timemapper.pixel2time(pxl)
			if side == 'left':
				return t - t0 + begindelay
			else:
				return t - t0 # == t - t1 + duration
		# else there is no timemapper, use pixel==second
		l,t,r,b = self.pos_abs
		if t1 > t0:
			factor = float(t1 - t0) / (r - l)
		elif t2 > t0:
			factor = float(t2 - t0) / (r - l)
		else:
			factor = 1.0
		if side == 'left':
			begindelay = self.node.GetBeginDelay()
			return float(pxl - l) * factor + begindelay
		else:			# 'right'
			return float(pxl - r) * factor + t1 - t0

	def GetTimes(self, which='virtual'):
		t0, t1, t2, downloadlag, begindelay = self.node.GetTimes(which)
		if self.timemapper and t0 == t1 == t2:
			t2 = t0 + 10
		return t0, t1, t2, downloadlag, begindelay

	def get_minpos(self):
		# Returns the leftmost position where this node can be placed
		pnode = self.node.GetParent()
		if pnode is None:
			return 0
		pwidget = pnode.views['struct_view']
		return pwidget.get_minpos() + pwidget.get_child_relminpos(self)

	def moveto(self, newpos):
		self.old_pos = self.pos_abs
		Widgets.Widget.moveto(self, newpos)

	def calculate_minsize(self, timemapper):
		# return the minimum size of this node, in pixels.
		# Called to work out the size of the canvas.
		xsize = MINSIZE
		node = self.node
		if self.dropbox is not None:
			xsize = xsize  + GAPSIZE + self.dropbox.recalc_minsize()[0]
		if node.infoicon and self.infoicon is None:
			self.infoicon = self.iconbox.add_icon(node.infoicon, callback = self.show_mesg)
		elif not node.infoicon and self.infoicon is not None:
			self.iconbox.del_icon(self.infoicon)
			self.infoicon.destroy()
			self.infoicon = None
		if not isinstance(self, CommentWidget):
			node.set_infoicon = self.set_infoicon
			node.set_armedmode = self.set_armedmode
			self.set_armedmode(node.armedmode, redraw = 0)
		ixsize = self.iconbox.recalc_minsize()[0]
		if self.collapsebutton is not None:
			ixsize = ixsize + self.collapsebutton.recalc_minsize()[0]
		if self.playicon is not None:
			ixsize = ixsize + self.playicon.recalc_minsize()[0]
		if self.name:
			ixsize = ixsize + f_title.strsizePXL(self.name)[0]
		xsize = min(max(xsize, ixsize), MAXSIZE)
		ysize = MINSIZE# + TITLESIZE
		if self.timeline is not None:
			w, h = self.timeline.recalc_minsize()
			if w > xsize:
				xsize = w
			ysize = ysize + h
		if timemapper is not None:
			t0, t1, t2, downloadlag, begindelay = self.GetTimes('virtual')
			if t0 == t2:
				# very special case--zero duration element
				return ICONSIZE+2*HEDGSIZE, MINSIZE
		return xsize, ysize

	def recalc_minsize(self, timemapper = None):
		timemapper = self.init_timemapper(timemapper)
		self.boxsize = self.calculate_minsize(timemapper)
		self.fix_timemapper(timemapper)
		return self.boxsize

	def get_minsize(self):
		# recalc_minsize must have been called before
		return self.boxsize

	def draw(self, displist):
		displist.fgcolor(CTEXTCOLOR)
		displist.usefont(f_title)
		l,t,r,b = self.pos_abs
		b = t + TITLESIZE + VEDGSIZE
		if self.collapsebutton is not None:
			l = l + ICONSIZE # move it past the icon.
			if l <= r:
				self.collapsebutton.draw(displist)
		if self.playicon is not None:
			l = l + ICONSIZE # move it past the icon.
			if l <= r:
				self.playicon.draw(displist)
		if self.iconbox is not None:
			self.iconbox.moveto((l,t+2,r,b))
			l = l + self.iconbox.get_minsize()[0]
			if l <= r:
				self.iconbox.draw(displist)
		if l < r and self.name:
			x, y = l, t+displist.baselinePXL()+2
			displist.setpos(x, y)
			namewidth = displist.strsizePXL(self.name)[0]
			liney = y-displist.baselinePXL()/2
			r = r - HEDGSIZE
			if namewidth <= r-l:
				# name fits fully
				# number of repeats
				n = (r-l-namewidth) / (namewidth + NAMEDISTANCE)
				# distance between repeats (including name itself)
				distance = namewidth + NAMEDISTANCE
				if n > 0:
					distance = (r-l-namewidth) / n
				while x + namewidth <= r:
					displist.writestr(self.name)
##					if x + distance + namewidth < r:
##						# there'll be a next name, draw a line between the names
##						displist.drawline((150,150,150),[(x+namewidth+SPACEWIDTH,liney),(x+distance-SPACEWIDTH,liney)])
					x = x + distance
					displist.setpos(x, y)
			else:
				# name doesn't fit fully; fit as much as we can
				for c in self.name:
					cw = displist.strsizePXL(c)[0]
					if x + cw >= r:
						break
					displist.writestr(c)
					x = x + cw
		if self.timeline is not None:
			self.timeline.draw(displist)
		# Draw the silly transitions.
		if self.transition_in is not None:
			self.transition_in.draw(displist)
		if self.transition_out is not None:
			self.transition_out.draw(displist)
		displist.draw3dbox(FOCUSLEFT, FOCUSTOP, FOCUSRIGHT, FOCUSBOTTOM, self.get_box())
		self.draw_draghandles(displist)

	def draw_draghandles(self, displist):
		if self.need_draghandles is None:
			return
		l,r,t = self.need_draghandles
		displist.drawfbox((0,0,0), (l,t,DRAGHANDLESIZE,DRAGHANDLESIZE))
		displist.drawfbox((0,0,0), (r-DRAGHANDLESIZE,t,DRAGHANDLESIZE,DRAGHANDLESIZE))

	# used by MediaWidget and CommentWidget
	def do_draw_image(self, image_filename, (x,y,w,h), displist):
		if not image_filename or w <= 0 or h <= 0:
			return
		r = x + w - MINSIZE/12
		x = x + MINSIZE/12
		imw = 5*(w/6)
		imh = 4*(h/6)
		coordinates = (x, y, imw, imh)
		displist.fgcolor(TEXTCOLOR)
		if coordinates[2] > 4 and coordinates[3] > 4:
			try:
				box = displist.display_image_from_file(
					image_filename,
					center = 0,
					coordinates = coordinates,
					fit = 'icon')
			except windowinterface.error:
				# some error displaying image, forget it
				pass
			else:
				displist.drawbox(box)
				# calculate number of copies that'll fit in the remaining space
				n = (w-box[2]-MINSIZE/12-MINSIZE/12)/(box[2]+NAMEDISTANCE)
				if n <= 0:
					return
				# calculate distance between left edges to get copies equidistant
				distance = (w-box[2]-MINSIZE/12-MINSIZE/12)/n
				while x + distance + box[2] <= r:
					x = x + distance
					# draw line between copies
					displist.drawline((150,150,150), [(box[0]+box[2],box[1]+box[3]-1),(x,box[1]+box[3]-1)])
					coordinates = (x, y, imw, imh)
					box = displist.display_image_from_file(
						image_filename,
						center = 0,
						coordinates = coordinates,
						fit = 'icon')
					displist.drawbox(box)

	#
	# These a fillers to make this behave like the old 'Object' class.
	#
	def select(self):
		self.dont_draw_children = 1 # I'm selected.
		self.makevisible()
		Widgets.Widget.select(self)

	def deselect(self):
		self.dont_draw_children = 1 # I'm deselected.
		self.unselect()

	def cleanup(self):
		self.destroy()

	def set_infoicon(self, icon, msg=None):
		# Sets the information icon to this icon.
		# icon is a string, msg is a string.
		# XXXX This is wrong.
		changed = self.node.infoicon != icon
		if not changed and self.node.errormessage == msg:
			# nothing to do
			return
		self.node.infoicon = icon
		self.node.errormessage = msg
		if self.infoicon is None:
			# create a new info icon
			self.infoicon = self.iconbox.add_icon(icon, callback = self.show_mesg)
			self.mother.need_resize = 1
			self.mother.draw()
			return
		if not icon:
			# remove the info icon
			self.iconbox.del_icon(self.infoicon)
			self.infoicon.destroy()
			self.infoicon = None
			self.mother.need_resize = 1
			self.mother.draw()
			return
		# change the info icon
		self.infoicon.set_icon(icon)
		if changed:
			if self.mother.extra_displist is not None:
				d = self.mother.extra_displist.clone()
			else:
				d = self.mother.base_display_list.clone()
			self.infoicon.draw(d)
			d.render()
			if self.mother.extra_displist is not None:
				self.mother.extra_displist.close()
			self.mother.extra_displist = d

	def get_cause_event_icon(self):
		# Returns the start position of an event arrow.
		# Note that the "dangling" event icon overrides this one
		if self.cause_event_icon is None:
			self.cause_event_icon = self.iconbox.add_icon('causeevent').set_properties(arrowable = 1, arrowdirection=1).set_contextmenu(self.mother.event_popupmenu_source)
		return self.cause_event_icon

	def set_dangling_event(self):
		if self.cause_event_icon:
			self.iconbox.del_icon(self.cause_event_icon)
		self.cause_event_icon = self.iconbox.add_icon('danglingevent')

	def clear_dangling_event(self):
		# XXXX Note that this is not really correct: if there was a causeevent icon before
		# we installed the dangling icon we now lose it.
		if self.cause_event_icon:
			self.iconbox.del_icon(self.cause_event_icon)
		self.cause_event_icon = None

	def getlinkicons(self):
		# Returns the icon to show for incoming and outgiong hyperlinks.
		links = self.node.context.hyperlinks
		is_src, is_dst = links.findnodelinks(self.node)
		is_dangling = links.nodehasdanglinganchor(self.node)
##		print 'DBG: getlinkicon', node, is_src, is_dst
		rv = []
		if is_dangling:
			rv.append('danglinganchor')
		elif is_src:
			rv.append('linksrc')
		if is_dst:
			rv.append('linkdst')
		return rv

	def get_obj_near(self, (x, y), timemapper = None, timeline = None):
		return None

	def get_nearest_node_index(a):
		# This is only for seqs and verticals.
		return -1

	def expandcall(self):
		# 'Expand' the view of this node.
		# Also, if this node is expanded, collapse it!
		# Doesn't appear to be called.
		if isinstance(self, StructureObjWidget):
			if self.iscollapsed():
				self.uncollapse()
			else:
				self.collapse()
			self.mother.need_redraw = 1

	def expandallcall(self, expand):
		# Expand the view of this node and all kids.
		# if expand is 1, expand. Else, collapse.
		if isinstance(self, StructureObjWidget):
			if expand:
				self.uncollapse_all()
			else:
				self.collapse_all()
			self.mother.need_redraw = 1

	def playcall(self):
		top = self.mother.toplevel
		top.setwaiting()
		top.player.playsubtree(self.node)

	def playfromcall(self):
		top = self.mother.toplevel
		top.setwaiting()
		top.player.playfrom(self.node)

	def attrcall(self, initattr = None):
		self.mother.toplevel.setwaiting()
		import AttrEdit
		AttrEdit.showattreditor(self.mother.toplevel, self.node, initattr=initattr)

	def editcall(self):
		self.mother.toplevel.setwaiting()
		import NodeEdit
		NodeEdit.showeditor(self.node)
	def _editcall(self):
		self.mother.toplevel.setwaiting()
		import NodeEdit
		NodeEdit._showeditor(self.node)
	def _opencall(self):
		self.mother.toplevel.setwaiting()
		import NodeEdit
		NodeEdit._showviewer(self.node)

	def anchorcall(self):
		self.mother.toplevel.setwaiting()
		import AnchorEdit
		AnchorEdit.showanchoreditor(self.mother.toplevel, self.node)

	def createanchorcall(self):
		self.mother.toplevel.links.wholenodeanchor(self.node)

	def hyperlinkcall(self):
		self.mother.toplevel.links.finish_link(self.node)

	def rpconvertcall(self):
		import rpconvert
		rpconvert.rpconvert(self.node, self.show_mesg)

	def convertrpcall(self):
		import rpconvert
		rpconvert.convertrp(self.node, self.show_mesg)

# not called anymore.
#	def deletecall(self):
#		self.mother.deletefocus(0)

	def cutcall(self):
		self.mother.deletefocus(1)

	def copycall(self):
		mother = self.mother
		mother.toplevel.setwaiting()
		mother.copyfocus()

	def createbeforecall(self, chtype=None):
		self.mother.create(-1, chtype=chtype)

	def createbeforeintcall(self, ntype):
		self.mother.create(-1, ntype=ntype)

	def createaftercall(self, chtype=None):
		self.mother.create(1, chtype=chtype)

	def createafterintcall(self, ntype):
		self.mother.create(1, ntype=ntype)

	def createundercall(self, chtype=None):
		self.mother.create(0, chtype=chtype)

	def createunderintcall(self, ntype):
		self.mother.create(0, ntype=ntype)

	def createseqcall(self):
		self.mother.insertparent('seq')

	def createparcall(self):
		self.mother.insertparent('par')

	def createaltcall(self):
		self.mother.insertparent('switch')

	def pastebeforecall(self):
		self.mother.paste(-1)

	def pasteaftercall(self):
		self.mother.paste(1)

	def pasteundercall(self):
		self.mother.paste(0)

	def show_mesg(self, msg = None):
		if msg is None:
			msg = self.node.errormessage
		if msg:
			windowinterface.showmessage(msg, parent=self.mother.window)


#
# The StructureObjWidget represents any node which has children,
# and is thus collapsable.
#
class StructureObjWidget(MMNodeWidget):
	# A view of a seq, par, excl or any internal structure node.
	HAS_COLLAPSE_BUTTON = 1
	def __init__(self, node, mother, parent):
		MMNodeWidget.__init__(self, node, mother, parent)
		assert self is not None
		# Create more nodes under me if there are any.
		self.children = []
		if self.HAS_COLLAPSE_BUTTON and not self.mother.usetimestripview:
			if self.node.collapsed:
				icon = 'closed'
			else:
				icon = 'open'
			ntype = node.GetType()
			if ntype not in ('par', 'seq', 'switch', 'prio', 'excl'):
				ntype = ''
			icon = ntype + icon
			self.collapsebutton = Icon(self, self.mother)
			self.collapsebutton.set_properties(callbackable=1, selectable=0)
			self.collapsebutton.set_icon(icon)
			self.collapsebutton.set_callback(self.toggle_collapsed)
		self.parent_widget = parent # This is the parent node. Used for recalcing optimisations.
		for i in self.node.children:
			bob = create_MMNode_widget(i, mother, self)
			if bob is not None:
				self.children.append(bob)
		self.dont_draw_children = 0
		if parent is None:
			self.add_event_icons()

	def destroy(self):
		if self.children:
			for i in self.children:
				i.destroy()
		self.children = None
		if self.collapsebutton is not None:
			self.collapsebutton.destroy()
			self.collapsebutton = None
		self.parent_widget = None
		MMNodeWidget.destroy(self)

	def add_event_icons(self):
		MMNodeWidget.add_event_icons(self)
		for c in self.children:
			c.add_event_icons()

	def collapse(self):
		# remove_set_armedmode must be done before collapsed bit is set
		for c in self.children:
			c.remove_set_armedmode()
		self.node.collapsed = 1
		ntype = self.node.GetType()
		if ntype not in ('par', 'seq', 'switch', 'prio', 'excl'):
			ntype = ''
		if self.collapsebutton is not None:
			self.collapsebutton.icon = ntype + 'closed'
		self.mother.need_redraw = 1
		self.mother.need_resize = 1
		self.set_need_resize()

	def remove_set_armedmode(self):
		self.node.set_armedmode = None
		del self.node.set_armedmode
		self.node.set_infoicon = None
		del self.node.set_infoicon
		if not self.iscollapsed():
			for c in self.children:
				c.remove_set_armedmode()

	def uncollapse(self):
		self.node.collapsed = 0
		ntype = self.node.GetType()
		if ntype not in ('par', 'seq', 'switch', 'prio', 'excl'):
			ntype = ''
		if self.collapsebutton is not None:
			self.collapsebutton.icon = ntype + 'open'
		self.mother.need_redraw = 1
		self.mother.need_resize = 1
		self.set_need_resize()
		for c in self.children:
			c.add_set_armedmode()

	def add_set_armedmode(self):
		if self.playicon is not None:
			self.node.set_armedmode = self.set_armedmode
			self.set_armedmode(self.node.armedmode, redraw = 0)
			self.node.set_infoicon = self.set_infoicon
		if not self.iscollapsed():
			for c in self.children:
				c.add_set_armedmode()

	def toggle_collapsed(self):
		if self.iscollapsed():
			self.uncollapse()
		else:
			self.collapse()

	def iscollapsed(self):
		return self.node.collapsed

	def uncollapse_all(self):
		self.uncollapse()
		for i in self.children:
			i.uncollapse_all()

	def collapse_all(self):
		for i in self.children:
			i.collapse_all()
		self.collapse()

	def get_obj_near(self, (x, y), timemapper = None, timeline = None):
		if self.timemapper is not None:
			timemapper = self.timemapper
		if self.timeline is not None:
			timeline = self.timeline
		# first check self
		if self.need_draghandles is not None:
			l,r,t = self.need_draghandles
			if t <= y <= t+DRAGHANDLESIZE:
				if l <= x < l + DRAGHANDLESIZE:
					return self, 'left', timemapper, timeline
				if r - DRAGHANDLESIZE <= x < r:
					return self, 'right', timemapper, timeline
		# then check children
		l,t,r,b = self.pos_abs
		if l <= x <= r and t <= y <= b:
			for c in self.children:
				rv = c.get_obj_near((x, y), timemapper, timeline)
				if rv is not None:
					return rv

	def get_obj_at(self, pos):
		# Return the MMNode widget at position x,y
		# Oh, how I love recursive methods :-). Nice. -mjvdg.
		#if self.collapsebutton and self.collapsebutton.is_hit(pos):
		#	return self.collapsebutton

		if self.is_hit(pos):
			if self.iscollapsed():
				return self
			for i in self.children:
				ob = i.get_obj_at(pos)
				if ob is not None:
					return ob
			return self
		else:
			return None

	def get_clicked_obj_at(self, pos):
		# Returns an object which reacts to a click() event.
		# This is duplicated code, so it's getting a bit hacky again.
		if self.collapsebutton is not None and self.collapsebutton.is_hit(pos):
			return self.collapsebutton
		if self.is_hit(pos):
			if self.iconbox.is_hit(pos):
				return self.iconbox.get_clicked_obj_at(pos)
			elif self.iscollapsed():
				return self
			for i in self.children:
				ob = i.get_clicked_obj_at(pos)
				if ob is not None:
					return ob
			return self
		else:
			return None

	def get_collapse_icon(self):
		return self.collapsebutton

	def recalc(self, timemapper):
		# One optimisation that could be done is to have a dirty flag
		# for recalculating the relative sizes of all the nodes.
		# If the node sizes don't need to be changed, then don't
		# change them.
		# For the meanwhile, this is too difficult.
		l,t,r,b = self.pos_abs
		if self.timeline is not None:
			tl_w, tl_h = self.timeline.get_minsize()
			if TIMELINE_AT_TOP:
				self.timeline.moveto((l, t+VEDGSIZE+TITLESIZE, r, t+VEDGSIZE+TITLESIZE+tl_h), timemapper)
			else:
				self.timeline.moveto((l, b-VEDGSIZE-tl_h, r, b-VEDGSIZE), timemapper)
		if self.collapsebutton is not None:
			#l = l + self.get_relx(1)
			#t = t + self.get_rely(2)
			self.collapsebutton.moveto((l+1,t+2,0,0))
			l = l + ICONSIZE
		if self.playicon is not None:
			self.playicon.moveto((l+1,t+2,0,0))
			l = l + ICONSIZE
		self.need_resize = 0
		if timemapper is None:
			self.need_draghandles = None
		else:
			l,t,r,b = self.pos_abs
			if self.timeline is not None:
				y = self.timeline.params[0]
				self.need_draghandles = l,r,y-DRAGHANDLESIZE/2
			else:
				self.need_draghandles = l,r,b-8

	def set_need_resize(self):
		# Sets the need_resize attribute.
		p = self
		while p is not None:
			p.need_resize = 1
			p = p.parent_widget

	def draw_selected(self, displist):
		# Called from self.draw or from the mother when selection is changed.
		displist.draw3dbox(FOCUSRIGHT, FOCUSBOTTOM, FOCUSLEFT, FOCUSTOP, self.get_box())
		self.draw_draghandles(displist)

	def draw_unselected(self, displist):
		# Called from self.draw or from the mother when selection is changed.
		displist.draw3dbox(FOCUSLEFT, FOCUSTOP, FOCUSRIGHT, FOCUSBOTTOM, self.get_box())
		self.draw_draghandles(displist)

	def draw_box(self, displist):
		displist.draw3dbox(DROPCOLOR, DROPCOLOR, DROPCOLOR, DROPCOLOR, self.get_box())

	def draw(self, displist):
		# This is a base class for other classes.. this code only gets
		# called once the aggregating node has been called.
		# Draw only the children.
		if not self.iscollapsed():
			for i in self.children:
				i.draw(displist)

		MMNodeWidget.draw(self, displist)


#
# The HorizontalWidget is any sideways-drawn StructureObjWidget.
#
class HorizontalWidget(StructureObjWidget):
	# All widgets drawn horizontally; e.g. sequences.
	def draw(self, displist):
		# Draw those funny vertical lines.
		if self.iscollapsed() and self.timeline is None:
			l,t,r,b = self.pos_abs
			i = l + HEDGSIZE
			t = t + VEDGSIZE + TITLESIZE
			b = b - VEDGSIZE
			step = 8
			if r > l:
				while i < r:
					displist.drawline(TEXTCOLOR, [(i, t),(i, b)])
					i = i + step
		StructureObjWidget.draw(self, displist)

	def get_nearest_node_index(self, pos):
		# Return the index of the node at the specific drop position.

		if self.iscollapsed():
			return -1

		assert self.is_hit(pos)
		x,y = pos
		# Working from left to right:
		for i in range(len(self.children)):
			l,t,w,h = self.children[i].get_box()
			if x <= l+(w/2.0):
				return i
		return -1

	def recalc_minsize(self, timemapper = None):
		if self.iscollapsed():
			return MMNodeWidget.recalc_minsize(self, timemapper)

		if not self.children and self.channelbox is None:
			return MMNodeWidget.recalc_minsize(self, timemapper)

		timemapper = self.init_timemapper(timemapper)

		mw=0
		mh=0
		if self.channelbox is not None:
			mw, mh = self.channelbox.recalc_minsize()
			mw = mw + GAPSIZE

		is_excl = self.node.GetType() in ('excl', 'prio')
		if is_excl:
			tm = None
			if timemapper is not None:
				n = self.node
				while n is not None and not n.showtime:
					n = n.GetParent()
				showtime = n.showtime
		else:
			tm = timemapper

		minwidth, minheight = self.calculate_minsize(tm)

		delays = 0
		tottime = 0
		lt2 = 0
		for i in self.children:
			pushover = 0
			if timemapper is not None:
				if is_excl:
					i.node.showtime = showtime
				elif i.node.WillPlay():
					t0, t1, t2, download, begindelay = i.GetTimes('virtual')
					tottime = tottime + t2 - t0
					if lt2 > t0:
						# compensate for double counting
						tottime = tottime - lt2 + t0
					elif t0 > lt2:
						delays = delays + t0 - lt2
					lt2 = t2
			w,h = i.recalc_minsize(tm)
			if h > mh: mh=h
			mw = mw + w + pushover
		if timemapper is not None and tottime > 0:
			# reserve space for delays between nodes in addition to the nodes themselves
			t0, t1, t2, download, begindelay = self.GetTimes('virtual')
			mw = mw + int(mw * delays / float(tottime) + .5)
		mw = mw + GAPSIZE*(len(self.children)-1) + 2*HEDGSIZE

		if self.dropbox is not None:
			mw = mw + self.dropbox.recalc_minsize()[0] + GAPSIZE

		mh = mh + 2*VEDGSIZE
		# Add the title box.
		mh = mh + TITLESIZE
		if self.timeline is not None:
			w, h = self.timeline.recalc_minsize()
			if w > mw:
				mw = w
			mh = mh + h
		if mw < minwidth:
			mw = minwidth
		if mh < minheight:
			mh = minheight
		self.boxsize = mw, mh
		self.fix_timemapper(timemapper)
		return self.boxsize

	def get_child_relminpos(self, child):
		minpos = HEDGSIZE
		for ch in self.children:
			if ch is child:
				return minpos
			minpos = minpos + ch.get_minsize()[0] + GAPSIZE
		raise 'Unknown child node'

	def recalc(self, timemapper = None):
		# Recalculate the position of all the contained boxes.
		# Algorithm: Iterate through each of the MMNodes children's views and find their minsizes.
		# Apportion free space equally, based on the size of self.
		# TODO: This does not test for maxheight()
		l, t, r, b = self.pos_abs

		if self.timemapper is not None:
			timemapper = self.timemapper
			timemapper.setoffset(l, r - l)
		if not self.node.WillPlay():
			timemapper = None

		if self.iscollapsed():
			StructureObjWidget.recalc(self, timemapper)
			return

		if self.timeline is not None and not TIMELINE_AT_TOP:
			tl_w, tl_h = self.timeline.get_minsize()
			b = b - tl_h
		min_width, min_height = self.get_minsize()

		free_width = (r-l) - min_width

		t = t + TITLESIZE
		min_height = min_height - TITLESIZE

		# Add the timeline, if it is at the top
		if self.timeline is not None and TIMELINE_AT_TOP:
			tl_w, tl_h = self.timeline.get_minsize()
			self.timeline.moveto((l, t, r, t+tl_h), timemapper)
			t = t + tl_h
			min_height = min_height - tl_h

		# Umm.. Jack.. the free width for each child isn't proportional to their size doing this..
		freewidth_per_child = free_width / max(1, len(self.children))

		l = l + HEDGSIZE
		t = t + VEDGSIZE
		b = b - VEDGSIZE

		if self.channelbox is not None:
			w, h = self.channelbox.get_minsize()
			self.channelbox.moveto((l, t, l+w, b))
			l = l + w + GAPSIZE
		is_excl = self.node.GetType() in ('excl', 'prio')
		if is_excl:
			tm = None
		else:
			tm = timemapper
		for chindex in range(len(self.children)):
			medianode = self.children[chindex]
			# Compute rightmost position we may draw
			if chindex == len(self.children)-1:
				max_r = self.pos_abs[2] - HEDGSIZE
			elif tm is None:
				# XXXX Should do this more intelligently
				max_r = self.pos_abs[2] - HEDGSIZE
			else:
				# max_r is set below
				pass
			w,h = medianode.get_minsize()
			thisnode_free_width = freewidth_per_child
			# First compute pushback bar position
			if tm is not None:
				t0, t1, t2, download, begindelay, neededpixel0, neededpixel1 = self.childrentimes[chindex]
				tend = t2
				# tend may be t2, the fill-time, so for fill=hold it may extend past
				# the begin of the next child. We have to truncate in that
				# case.
				if chindex < len(self.children)-1:
					nextt = self.childrentimes[chindex+1][0]
					if tend > nextt:
						tend = nextt
				lmin = tm.time2pixel(t0)
				if l < lmin:
					l = lmin
				r = tm.time2pixel(tend) + neededpixel1
				if t0 == tend:
					r = min(r + neededpixel0 + neededpixel1, tm.time2pixel(tend, 'right'), l + w)
				max_r = min(r, self.pos_abs[2]-HEDGSIZE)
			else:
				r = l + w + thisnode_free_width
				if chindex == len(self.children)-1:
					# The last child is extended the whole way to the end
					r = max_r
			if r > max_r:
				r = max_r
			if l > r:
				l = r
			medianode.moveto((l,t,r,b))
			medianode.recalc(tm)
			l = r + GAPSIZE

		if self.dropbox is not None:
			w,h = self.dropbox.get_minsize()
			# The dropbox takes up the rest of the free width.
			r = self.pos_abs[2]-HEDGSIZE

			self.dropbox.moveto((l,t,r,b))

		if self.timeline is not None and not TIMELINE_AT_TOP:
			l, t, r, b = self.pos_abs
			tl_w, tl_h = self.timeline.get_minsize()
			self.timeline.moveto((l, b-tl_h, r, b), timemapper)

		StructureObjWidget.recalc(self, timemapper)

	def addcollisions(self, mastert0, mastertend, timemapper, mytimes = None):
		if not self.children or self.iscollapsed() or not self.node.WillPlay():
			return MMNodeWidget.addcollisions(self, mastert0, mastertend, timemapper, mytimes)

		self.childrentimes = []
		if mytimes is not None:
			t0, t1, t2, download, begindelay = mytimes
		else:
			t0, t1, t2, download, begindelay = self.GetTimes('virtual')
		tend = t2
		myt0, myt1, myt2, mytend = t0, t1, t2, tend
		maxneededpixel0 = HEDGSIZE
		maxneededpixel1 = HEDGSIZE
		if self.channelbox is not None:
			mw, mh = self.channelbox.get_minsize()
			maxneededpixel0 = maxneededpixel0 + mw + GAPSIZE
		if self.dropbox is not None:
			mw, mw =self.dropbox.get_minsize()
			maxneededpixel1 = maxneededpixel1 + mw + GAPSIZE
		for i in range(len(self.children)):
			if self.children[i].node.WillPlay():
				nextt0, nextt1, nextt2, nextdownload, nextbegindelay = self.children[i].GetTimes('virtual')
				break
		else:
			# no playable children
			nextt0 = t0
		thist0 = myt0
		for i in range(len(self.children)):
			if not self.children[i].node.WillPlay():
				thist0 = thist1 = thist2 = nextt0
				thisdownload = thisbegindelay = 0
			else:
				thist0, thist1, thist2, thisdownload, thisbegindelay = nextt0, nextt1, nextt2, nextdownload, nextbegindelay
				for j in range(i+1, len(self.children)):
					if self.children[j].node.WillPlay():
						nextt0, nextt1, nextt2, nextdownload, nextbegindelay = self.children[j].GetTimes('virtual')
						break
				else:
					# no more playable children
					nextt0 = tend
			thistend = min(thist2, nextt0)
			neededpixel0, neededpixel1 = self.children[i].addcollisions(t0, nextt0, timemapper, (thist0, thist1, thist2, thisdownload, thisbegindelay))
			self.childrentimes.append((thist0, thist1, thist2, thisdownload, thisbegindelay, neededpixel0, neededpixel1))
			if thist0 == mastert0:
				maxneededpixel0 = neededpixel0 = neededpixel0 + maxneededpixel0
			elif i > 0:
				neededpixel0 = neededpixel0 + GAPSIZE
			if thistend == mastertend:
				maxneededpixel1 = neededpixel1 = neededpixel1 + maxneededpixel1
			timemapper.addcollision(thist0, neededpixel0)
			timemapper.addcollision(thistend, neededpixel1)
			t0 = nextt0
		if myt0 != mastert0:
			timemapper.addcollision(myt0, maxneededpixel0)
			maxneededpixel0 = 0
		if mytend != mastertend:
			timemapper.addcollision(mytend, maxneededpixel1)
			maxneededpixel1 = 0
		return maxneededpixel0, maxneededpixel1

#
# The Verticalwidget is any vertically-drawn StructureObjWidget.
#
class VerticalWidget(StructureObjWidget):
	# Any node which is drawn vertically

	def recalc_minsize(self, timemapper = None):
		if not self.children or self.iscollapsed():
			return MMNodeWidget.recalc_minsize(self, timemapper)

		timemapper = self.init_timemapper(timemapper)

		mw=0
		mh=0

		if self.timeline is not None:
			w, h = self.timeline.recalc_minsize()
			if w > mw:
				mw = w
			mh = mh + h

		is_excl = self.node.GetType() in ('excl', 'prio')
		if is_excl:
			tm = None
			if timemapper is not None:
				n = self.node
				while n is not None and not n.showtime:
					n = n.GetParent()
				showtime = n.showtime
		else:
			tm = timemapper

		minwidth, minheight = self.calculate_minsize(tm)

		for i in self.children:
			if timemapper is not None:
				if is_excl:
					i.node.showtime = showtime
			w,h = i.recalc_minsize(tm)
			if timemapper is not None and not is_excl and i.node.WillPlay():
				t0, t1, t2, download, begindelay = i.GetTimes('virtual')
				# reserve space for begin delay
				if download + begindelay > 0:
					if t2 - t0 > 0:
						w = w + int(w * (download + begindelay) / float(t2 - t0) + .5)
					else:
						w = w + 10
			if w > mw: mw=w
			mh=mh+h
		mh = mh + GAPSIZE*(len(self.children)-1) + 2*VEDGSIZE

		# Add the titleheight
		mh = mh + TITLESIZE
		mw = mw + 2*HEDGSIZE
		if mw < minwidth:
			mw = minwidth
		if mh < minheight:
			mh = minheight
		self.boxsize = mw, mh
		self.fix_timemapper(timemapper)
		return self.boxsize

	def get_child_relminpos(self, child):
		return HEDGSIZE

	def get_nearest_node_index(self, pos):
		# Return the index of the node at the specific drop position.
		if self.iscollapsed():
			return -1

		assert self.is_hit(pos)
		x,y = pos
		# Working from left to right:
		for i in range(len(self.children)):
			l,t,w,h = self.children[i].get_box()
			if y <= t+(h/2.0):
				return i
		return -1

	def recalc(self, timemapper = None):
		# Recalculate the position of all the contained boxes.
		# Algorithm: Iterate through each of the MMNodes children's views and find their minsizes.
		# Apportion free space equally, based on the size of self.
		# TODO: This does not test for maxheight()
		if self.timemapper is not None:
			timemapper = self.timemapper
			timemapper.setoffset(self.pos_abs[0], self.pos_abs[2] - self.pos_abs[0])
		if not self.node.WillPlay():
			timemapper = None

		if self.iscollapsed():
			StructureObjWidget.recalc(self, timemapper)
			return

		l, t, r, b = self.pos_abs
		# Add the titlesize
		t = t + TITLESIZE

		# Add the timeline, if it is at the top
		if self.timeline is not None and TIMELINE_AT_TOP:
			tl_w, tl_h = self.timeline.get_minsize()
			t = t + tl_h

		min_width, min_height = self.get_minsize()
		min_height = min_height - TITLESIZE

		overhead_height = 2*VEDGSIZE + len(self.children)-1*GAPSIZE
		free_height = (b-t) - min_height

		if free_height < 0:
			free_height = 0

		l_par = l + HEDGSIZE
		r = r - HEDGSIZE
		t = t + VEDGSIZE

		is_excl = self.node.GetType() in ('excl', 'prio')
		if is_excl:
			tm = None
		else:
			tm = timemapper
		for medianode in self.children: # for each MMNode:
			w,h = medianode.get_minsize()
			l = l_par
			if h > (b-t):			  # If the node needs to be bigger than the available space...
				pass				   # TODO!!!!!
			# Take a portion of the free available width, fairly.
			if free_height == 0:
				thisnode_free_height = 0
			else:
				thisnode_free_height = int(h/(min_height-overhead_height) * free_height)
			# Give the node the free width.
			b = t + h + thisnode_free_height
			this_l = l
			this_r = r
			if tm is not None and medianode.node.WillPlay():
				t0, t1, t2, download, begindelay = medianode.GetTimes('virtual')
				tend = t2
				lmin = tm.time2pixel(t0)
				if this_l < lmin:
					this_l = lmin
##				rmin = tm.time2pixel(tend)
##				if this_r < rmin:
##					this_r = rmin
##				else:
				rmax = tm.time2pixel(tend, align='right')
				if this_r > rmax:
					this_r = rmax
				if this_l > this_r:
					this_l = this_r

			medianode.moveto((this_l,t,this_r,b))
			medianode.recalc(tm)
			t = b + GAPSIZE
		if self.timeline is not None and not TIMELINE_AT_TOP:
			l, t, r, b = self.pos_abs
			tl_w, tl_h = self.timeline.get_minsize()

		StructureObjWidget.recalc(self, timemapper)

	def draw(self, displist):
		if self.iscollapsed() and self.timeline is None:
			l,t,r,b = self.pos_abs
			i = t + VEDGSIZE + TITLESIZE
			l = l + HEDGSIZE
			r = r - HEDGSIZE
			step = 8
			if r > l:
				while i < b:
					displist.drawline(TEXTCOLOR, [(l, i),(r, i)])
					i = i + step
		StructureObjWidget.draw(self, displist)

	def addcollisions(self, mastert0, mastertend, timemapper, mytimes = None):
		if not self.children or self.iscollapsed() or not self.node.WillPlay():
			return MMNodeWidget.addcollisions(self, mastert0, mastertend, timemapper, mytimes)

		if mytimes is not None:
			t0, t1, t2, download, begindelay = mytimes
		else:
			t0, t1, t2, download, begindelay = self.GetTimes('virtual')
		tend = t2
		maxneededpixel0 = 0
		maxneededpixel1 = 0
		for ch in self.children:
			if ch.node.WillPlay():
				chtimes = ch.GetTimes('virtual')
			else:
				chtimes = t0, t2, t2, 0, 0
			neededpixel0, neededpixel1 = ch.addcollisions(t0, tend, timemapper, chtimes)
			if neededpixel0 > maxneededpixel0:
				maxneededpixel0 = neededpixel0
			if neededpixel1 > maxneededpixel1:
				maxneededpixel1 = neededpixel1
		maxneededpixel0 = maxneededpixel0 + HEDGSIZE
		maxneededpixel1 = maxneededpixel1 + HEDGSIZE
		if t0 == tend == mastert0:
			maxneededpixel0 = maxneededpixel0 + maxneededpixel1
			maxneededpixel1 = 0
		elif t0 == tend == mastertend:
			maxneededpixel1 = maxneededpixel0 + maxneededpixel1
			maxneededpixel0 = 0
		if t0 != mastert0:
			timemapper.addcollision(t0, maxneededpixel0)
			maxneededpixel0 = 0
		if tend != mastertend:
			timemapper.addcollision(tend, maxneededpixel1)
			maxneededpixel1 = 0
		return maxneededpixel0, maxneededpixel1


######################################################################
# Concrete widget classes.
######################################################################


######################################################################
# Structure widgets

#
# The SeqWidget represents a sequence node.
#
class SeqWidget(HorizontalWidget):
	# Any sequence node.
	HAS_CHANNEL_BOX = 0
	def __init__(self, node, mother, parent):
		HorizontalWidget.__init__(self, node, mother, parent)
		has_drop_box = not MMAttrdefs.getattr(node, 'project_readonly')
		if mother.usetimestripview and has_drop_box:
			self.dropbox = DropBoxWidget(self, mother)
		if self.HAS_CHANNEL_BOX:
			self.channelbox = ChannelBoxWidget(self, node, mother)

	def destroy(self):
		if self.dropbox is not None:
			self.dropbox.destroy()
			self.dropbox = None
		if self.channelbox is not None:
			self.channelbox.destroy()
			self.channelbox = None
		HorizontalWidget.destroy(self)

	def get_obj_at(self, pos):
		if self.channelbox is not None and self.channelbox.is_hit(pos):
			return self.channelbox
		return HorizontalWidget.get_obj_at(self, pos)

	def draw(self, displist):
		willplay = not self.mother.showplayability or self.node.WillPlay()
		if willplay:
			color = SEQCOLOR
		else:
			color = SEQCOLOR_NOPLAY

		displist.drawfbox(color, self.get_box())

		if self.channelbox is not None and not self.iscollapsed():
			self.channelbox.draw(displist)

		# Uncomment to redraw pushback bars.
		#for i in self.children:
		#	if isinstance(i, MediaWidget) and i.pushbackbar:
		#		i.pushbackbar.draw(displist)

		if self.dropbox is not None and not self.iscollapsed():
			self.dropbox.draw(displist)
		HorizontalWidget.draw(self, displist)

#
# The UnseenVerticalWidget is only ever a single top-level widget
#
class UnseenVerticalWidget(StructureObjWidget):
	# The top level par that doesn't get drawn.
	HAS_COLLAPSE_BUTTON = 0

	def recalc_minsize(self, timemapper = None):
		if not self.children or self.iscollapsed():
			return MMNodeWidget.recalc_minsize(self, timemapper)

		timemapper = self.init_timemapper(timemapper)

		minwidth, minheight = self.calculate_minsize(timemapper)

		mw=0
		mh=0

		for i in self.children:
			w,h = i.recalc_minsize(timemapper)
			if w > mw: mw=w
			mh=mh+h
		if self.timeline is not None:
			w, h = self.timeline.recalc_minsize()
			if w > mw:
				mw = w
			mh = mh + h
		if mw < minwidth:
			mw = minwidth
		if mh < minheight:
			mh = minheight
		self.boxsize = mw, mh
		self.fix_timemapper(timemapper)
		return self.boxsize

	def get_child_relminpos(self, child):
		return 0

	def get_nearest_node_index(self, pos):
		# Return the index of the node at the specific drop position.
		if self.iscollapsed():
			return -1

		assert self.is_hit(pos)
		x,y = pos
		# Working from left to right:
		for i in range(len(self.children)):
			l,t,w,h = self.children[i].get_box()
			if y <= t+(h/2.0):
				return i
		return -1

	def recalc(self, timemapper = None):
		# Recalculate the position of all the contained boxes.
		# Algorithm: Iterate through each of the MMNodes children's views and find their minsizes.
		# Apportion free space equally, based on the size of self.
		# TODO: This does not test for maxheight()
		if self.timemapper is not None:
			timemapper = self.timemapper
			timemapper.setoffset(self.pos_abs[0], self.pos_abs[2] - self.pos_abs[0])
		if not self.node.WillPlay():
			timemapper = None

		if self.iscollapsed():
			StructureObjWidget.recalc(self, timemapper)
			return

		l, t, r, b = self.pos_abs
		my_b = b
		# Add the titlesize
		min_width, min_height = self.get_minsize()

		overhead_height = 0
		free_height = (b-t) - min_height

		if self.timeline and not TIMELINE_AT_TOP:
			tl_w, tl_h = self.timeline.get_minsize()
			t = t + tl_h
			free_height = free_height - tl_h

		if free_height < 0:
			free_height = 0.0

		for medianode in self.children: # for each MMNode:
			w,h = medianode.get_minsize()
			if h > (b-t):			  # If the node needs to be bigger than the available space...
				pass				   # TODO!!!!!
			# Take a portion of the free available width, fairly.
			if free_height == 0.0:
				thisnode_free_height = 0.0
			else:
				thisnode_free_height = int((float(h)/(min_height-overhead_height)) * free_height)
			# Give the node the free width.
			b = t + h + thisnode_free_height
			# r = l + w # Wrap the node to it's minimum size.
			this_l = l
			this_r = r
			if timemapper is not None and medianode.node.WillPlay():
				t0, t1, t2, download, begindelay = medianode.GetTimes('virtual')
				tend = t2
				lmin = timemapper.time2pixel(t0)
				if this_l < lmin:
					this_l = lmin
##				rmin = timemapper.time2pixel(tend)
##				if this_r < rmin:
##					this_r = rmin
##				else:
				rmax = timemapper.time2pixel(tend, align='right')
				if this_r > rmax:
					this_r = rmax
				if this_l > this_r:
					this_l = this_r
			medianode.moveto((this_l,t,this_r,b))
			medianode.recalc(timemapper)
			t = b #  + self.get_rely(GAPSIZE)
		StructureObjWidget.recalc(self, timemapper)

	def draw(self, displist):
		# We want to draw this even if pushback bars are disabled.
		for i in self.children:
			#if isinstance(i, MediaWidget):
			#	i.pushbackbar.draw(displist)
			i.draw(displist)

	def addcollisions(self, mastert0, mastertend, timemapper, mytimes = None):
		if mytimes is not None:
			t0, t1, t2, download, begindelay = mytimes
		else:
			t0, t1, t2, download, begindelay = self.GetTimes('virtual')
		for ch in self.children:
			ch.addcollisions(t0, t2, timemapper)

#
# A ParWidget represents a Par node.
#
class ParWidget(VerticalWidget):
	# Parallel node
	def draw(self, displist):
		willplay = not self.mother.showplayability or self.node.WillPlay()
		if willplay:
			color = PARCOLOR
		else:
			color = PARCOLOR_NOPLAY
		displist.drawfbox(color, self.get_box())
		VerticalWidget.draw(self, displist)

# and so forth..
class ExclWidget(SeqWidget):
	# Exclusive node.
	def draw(self, displist):
		willplay = not self.mother.showplayability or self.node.WillPlay()
		if willplay:
			color = EXCLCOLOR
		else:
			color = EXCLCOLOR_NOPLAY
		displist.drawfbox(color, self.get_box())
		StructureObjWidget.draw(self, displist)


class PrioWidget(SeqWidget):
	# Prio node (?!) - I don't know what they are, but here is the code I wrote! :-)
	def draw(self, displist):
		willplay = not self.mother.showplayability or self.node.WillPlay()
		if willplay:
			color = PRIOCOLOR
		else:
			color = PRIOCOLOR_NOPLAY
		displist.drawfbox(color, self.get_box())
		StructureObjWidget.draw(self, displist)


class SwitchWidget(VerticalWidget):
	# Switch Node
	def draw(self, displist):
		willplay = not self.mother.showplayability or self.node.WillPlay()
		if willplay:
			color = ALTCOLOR
		else:
			color = ALTCOLOR_NOPLAY
		displist.drawfbox(color, self.get_box())
		VerticalWidget.draw(self, displist)


##############################################################################
# The Media objects (images, videos etc) in the Structure view.
##############################################################################

#
# A MediaWidget represents most leaf nodes.
# This should really be an abstract base class, but that isn't necessary until
# the implementation changes.
#
class MediaWidget(MMNodeWidget):
	# A view of an object which is a playable media type.
	# NOT the structure nodes.

	# TODO: this has some common code with the two functions above - should they
	# have a common ancester?

	# TODO: This class can be broken down into various different node types (img, video)
	# if the drawing code is different enough to warrent this.

	def __init__(self, node, mother, parent):
		MMNodeWidget.__init__(self, node, mother, parent)
		if mother.transboxes:
			self.transition_in = TransitionWidget(self, mother, 'in')
			self.transition_out = TransitionWidget(self, mother, 'out')

		self.pushbackbar = None
		self.downloadtime = 0.0		# not used??
		self.downloadtime_lag = 0.0	# Distance to push this node to the right - relative coords. Not pixels.
		self.downloadtime_lag_errorfraction = 1.0
		self.__timemapper = None

	def destroy(self):
		# Remove myself from the MMNode view{} dict.
		self.__timemapper = None
		if self.transition_in is not None:
			self.transition_in.destroy()
			self.transition_in = None
		if self.transition_out is not None:
			self.transition_out.destroy()
			self.transition_out = None
		if self.pushbackbar is not None:
			self.pushbackbar.destroy()
			self.pushbackbar = None
		MMNodeWidget.destroy(self)

	def init_timemapper(self, timemapper):
		if not self.node.WillPlay():
			return None
		return timemapper

	def remove_set_armedmode(self):
		self.node.set_armedmode = None
		del self.node.set_armedmode
		self.node.set_infoicon = None
		del self.node.set_infoicon

	def add_set_armedmode(self):
		if self.playicon is not None:
			self.node.set_armedmode = self.set_armedmode
			self.set_armedmode(self.node.armedmode, redraw = 0)
			self.node.set_infoicon = self.set_infoicon

	def is_hit(self, pos):
		hit = (self.transition_in is not None and self.transition_in.is_hit(pos)) or \
		      (self.transition_out is not None and self.transition_out.is_hit(pos)) or \
		      (self.pushbackbar is not None and self.pushbackbar.is_hit(pos)) or \
		      MMNodeWidget.is_hit(self, pos)
		return hit


	def recalc(self, timemapper = None):
		self.need_draghandles = None
		if self.timemapper is not None:
			timemapper = self.timemapper
			timemapper.setoffset(self.pos_abs[0], self.pos_abs[2] - self.pos_abs[0])
		if not self.node.WillPlay():
			timemapper = None
		self.__timemapper = timemapper
		l,t,r,b = self.pos_abs
		w = 0
		if self.playicon is not None:
			self.playicon.moveto((l+1, t+2,0,0))
			w = ICONSIZE

		self.iconbox.moveto((l+w+1, t+2,0,0))
		# First compute pushback bar position
		if self.pushbackbar is not None:
			self.pushbackbar.destroy()
			self.pushbackbar = None
		if timemapper is not None:
			t0, t1, t2, download, begindelay = self.GetTimes('virtual')
			self.__times = t0,t1,t2
			if download > 0:
				self.downloadtime_lag_errorfraction = 1 ## download / (download + begindelay)
				if self.pushbackbar is None:
					self.pushbackbar = PushBackBarWidget(self, self.mother)
				pbb_left = timemapper.time2pixel(t0-download, align='right')
				self.pushbackbar.moveto((pbb_left, t, l, t+12))

		t = t + TITLESIZE

		# Add the timeline
		if self.timeline is not None:
			tl_w, tl_h = self.timeline.get_minsize()
			if TIMELINE_AT_TOP:
				self.timeline.moveto((l, t, r, t+tl_h), timemapper)
				t = t + tl_h
			else:
				self.timeline.moveto((l, b-tl_h, r, b), timemapper)
				b = b - tl_h

		pix16x = 16
		pix16y = 16
		if self.transition_in is not None:
			self.transition_in.moveto((l,b-pix16y,l+pix16x, b))
		if self.transition_out is not None:
			self.transition_out.moveto((r-pix16x,b-pix16y,r, b))

	def get_maxsize(self):
		return MAXSIZE, MAXSIZE

	def __draw_box(self, displist, color):
		x,y,w,h = self.get_box()
		timemapper = self.__timemapper
		if timemapper is None:
			displist.drawfbox(color, (x,y,w,h))
			return

		node = self.node
		t0, t1, t2 = self.__times
		dur = Duration.get(node, ignoreloop = 1, wanterror = 0)	# what gets repeated
		ad = Duration.get(node, wanterror = 0)
		if dur > ad:
			dur = ad

		displist.drawfbox(color, (x,y,w,16)) # top bar
		if dur >= 0 and t2 > t0:
			if dur == 0:
				align = 'right'
			else:
				align = 'left'
			dw = timemapper.interptime2pixel(t0+min(dur, t2-t0), align) - x
			if dw < 0: dw = 0
			if dw > w: dw = w
		else:
			dw = w
		self.need_draghandles = x,x+dw,y+h-8
		if dw > 0:
			displist.drawfbox(color, (x, y+16, dw, h-16))
		if dw < w:
			if ad > dur:
##				adw = min(int(w*float(ad-dur)/(t2-t0) + .5), w-dw)
				adw = timemapper.interptime2pixel(t0+min(ad, t2-t0)) - x - dw
				if adw < 0: adw = 0
				if adw > w-dw: adw = w-dw
			else:
				adw = 0
			if adw > 0:
				displist.drawfbox(REPEATCOLOR, (x+dw, y+16, adw, h-16))
			if dw+adw < w:
				displist.drawfbox(FREEZECOLOR, (x+dw+adw, y+16, w-dw-adw, h-16))
		if dur > t2-t0:
			# duration truncated
			displist.drawfbox(TRUNCCOLOR, (x+w-TRUNCSIZE,y,TRUNCSIZE,h))

	def draw_selected(self, displist):
		self.__draw_box(displist, (255,255,255))
		self.__draw(displist)
		displist.draw3dbox(FOCUSRIGHT, FOCUSBOTTOM, FOCUSLEFT, FOCUSTOP, self.get_box())
		self.draw_draghandles(displist)

	def draw_unselected(self, displist):
		self.draw(displist)

	def draw_box(self, displist):
		displist.draw3dbox(DROPCOLOR, DROPCOLOR, DROPCOLOR, DROPCOLOR, self.get_box())

	def draw(self, displist):
		# Only draw unselected.
		willplay = not self.mother.showplayability or self.node.WillPlay()
		if willplay:
			color = LEAFCOLOR
		else:
			color = LEAFCOLOR_NOPLAY
		self.__draw_box(displist, color)
		displist.draw3dbox(FOCUSLEFT, FOCUSTOP, FOCUSRIGHT, FOCUSBOTTOM, self.get_box())
		self.__draw(displist)
		if self.pushbackbar is not None:
			self.pushbackbar.draw(displist)
		self.draw_draghandles(displist)

	def __draw(self, displist):
		l,t,r,b = self.pos_abs
		t = t + TITLESIZE

		# Add the timeline
		if self.timeline is not None:
			if TIMELINE_AT_TOP:
				t = self.timeline.pos_abs[3]
			else:
				b = self.timeline.pos_abs[1]
		x = l
		y = t
		w = r - l
		h = b - t

		ntype = self.node.GetType()

		# Draw the image.
		if self.node.GetChannelType() == 'brush':
			displist.drawfbox(MMAttrdefs.getattr(self.node, 'fgcolor'), (x+w/12, y+h/6, 5*(w/6), 4*(h/6)))
			displist.fgcolor(TEXTCOLOR)
			displist.drawbox((x+w/12, y+h/6, 5*(w/6), 4*(h/6)))
		elif w > 0 and h > 0:
			self.do_draw_image(self.__get_image_filename(), (x,y,w,h), displist)
		MMNodeWidget.draw(self, displist)

	def __get_image_filename(self):
		# return a file name for a thumbnail image
		url = self.node.GetAttrDef('file', None)
		if not url:
			# no file attr, so no thumbnail
			return None

		media_type = MMmimetypes.guess_type(url)[0]

		channel_type = self.node.GetChannelType()
		if self.mother.thumbnails and channel_type == 'image':
			url = self.node.context.findurl(url)
			try:
				return MMurl.urlretrieve(url)[0]
			except IOError, arg:
				self.set_infoicon('error', 'Cannot load image: %s'%`url`)
		# either not an image, or image couldn't be found
		return os.path.join(self.mother.datadir, '%s.tiff'%channel_type)

	def get_obj_near(self, (x, y), timemapper = None, timeline = None):
		if self.need_draghandles is not None:
			l,r,t = self.need_draghandles
			if t <= y <= t+DRAGHANDLESIZE:
				if self.timemapper is not None:
					timemapper = self.timemapper
				if self.timeline is not None:
					timeline = self.timeline
				if l <= x < l + DRAGHANDLESIZE:
					return self, 'left', timemapper, timeline
				if r - DRAGHANDLESIZE <= x < r:
					return self, 'right', timemapper, timeline

	def get_obj_at(self, pos):
		# Returns an MMWidget at pos. Compare get_clicked_obj_at()
		if self.is_hit(pos):
			return self
		else:
			return None

	def get_clicked_obj_at(self, pos):
		# Returns any object which can be clicked().
		if self.is_hit(pos):
			if self.transition_in is not None and self.transition_in.is_hit(pos):
				return self.transition_in
			elif self.transition_out is not None and self.transition_out.is_hit(pos):
				return self.transition_out
			elif self.iconbox is not None and self.iconbox.is_hit(pos):
				return self.iconbox.get_clicked_obj_at(pos)
			elif self.pushbackbar is not None and self.pushbackbar.is_hit(pos):
				return self.pushbackbar
			else:
				return self
		else:
			return None


class CommentWidget(MMNodeWidget):
	# A view of an object which is a comment type.

	def recalc(self, timemapper = None):
		l,t,r,b = self.pos_abs
		self.iconbox.moveto((l+1, t+2,0,0))

##	def recalc_minsize(self, timemapper = None):
##		# return the minimum size of this node, in pixels.
##		# Called to work out the size of the canvas.
##		timemapper = self.init_timemapper(timemapper)
##		xsize = MINSIZE + self.iconbox.recalc_minsize()[0]
##		ysize = MINSIZE# + TITLESIZE
##		self.boxsize = xsize, ysize
##		self.fix_timemapper(timemapper)
##		return self.boxsize

	def get_maxsize(self):
		return MAXSIZE, MAXSIZE

	def draw_selected(self, displist):
		displist.drawfbox((255,255,255), self.get_box())
		displist.draw3dbox(FOCUSRIGHT, FOCUSBOTTOM, FOCUSLEFT, FOCUSTOP, self.get_box())
		self.__draw(displist)

	def draw_unselected(self, displist):
		self.draw(displist)

	def draw_box(self, displist):
		displist.draw3dbox(DROPCOLOR, DROPCOLOR, DROPCOLOR, DROPCOLOR, self.get_box())

	def draw(self, displist):
		# Only draw unselected.
		color = COMMENTCOLOR
		displist.drawfbox(color, self.get_box())
		displist.draw3dbox(FOCUSLEFT, FOCUSTOP, FOCUSRIGHT, FOCUSBOTTOM, self.get_box())
		self.__draw(displist)

	def __draw(self, displist):
		x,y,w,h = self.get_box()
		y = y + TITLESIZE
		h = h - TITLESIZE

		ntype = self.node.GetType()

		# Draw the image.
		image_filename = os.path.join(self.mother.datadir, 'comment.tiff')
		if w > 0 and h > 0:
			self.do_draw_image(image_filename, (x,y,w,h), displist)

		# Draw the icon box.
		self.iconbox.draw(displist)

	def get_obj_at(self, pos):
		# Returns an MMWidget at pos. Compare get_clicked_obj_at()
		if self.is_hit(pos):
			return self
		else:
			return None

	def get_clicked_obj_at(self, pos):
		# Returns any object which can be clicked().
		if self.is_hit(pos):
			if self.iconbox.is_hit(pos):
				return self.iconbox.get_clicked_obj_at(pos)
			else:
				return self
		else:
			return None


class ForeignWidget(HorizontalWidget):
	# Any foreign node.
	HAS_CHANNEL_BOX = 0
	def draw(self, displist):
		willplay = not self.mother.showplayability or self.node.WillPlay()
		if willplay:
			color = FOREIGNCOLOR
		else:
			color = FOREIGNCOLOR_NOPLAY
		displist.drawfbox(color, self.get_box())
		HorizontalWidget.draw(self, displist)


#
# An MMWidgetDecoration is a decoration on a widget - and has no particular
# binding to an MMNode, but rather to a parent MMWidget.
#
class MMWidgetDecoration(Widgets.Widget):
	# This is a base class for anything that an MMNodeWidget has on it, but which isn't
	# actually the MMWidget.
	def __init__(self, mmwidget, mother):
		assert isinstance(mmwidget, MMNodeWidget)

		Widgets.Widget.__init__(self, mother)
		self.mmwidget = mmwidget
	def __repr__(self):
		return '<%s instance, node=%s, id=%X>' % (self.__class__.__name__, `self.mmwidget`, id(self))

	def destroy(self):
		self.mmwidget = None
		Widgets.Widget.destroy(self)
	def get_mmwidget(self):
		return self.mmwidget
	def get_node(self):
		return self.mmwidget.get_node()
	def get_minsize(self):
		# recalc_minsize must have been called before
		return self.boxsize
	def attrcall(self, initattr=None):
		self.mmwidget.attrcall(initattr=initattr)

class TransitionWidget(MMWidgetDecoration):
	# This is a box at the bottom of a node that represents the in or out transition.
	def __init__(self, parent, mother, inorout):
		MMWidgetDecoration.__init__(self, parent, mother)
		self.in_or_out = inorout
		self.parent = parent

	def destroy(self):
		self.parent = None
		MMWidgetDecoration.destroy(self)

	def select(self):
		# XXXX Note: this code assumes the select() is done on mousedown, and
		# that we can still post a menu at this time.
		self.parent.select()
		self.mother.need_redraw = 1

	def unselect(self):
		self.parent.unselect()

	def draw(self, displist):
		if self.in_or_out is 'in':
			displist.drawicon(self.get_box(), 'transin')
		else:
			displist.drawicon(self.get_box(), 'transout')

	def attrcall(self, initattr=None):
		self.mother.toplevel.setwaiting()
		import AttrEdit
		if self.in_or_out == 'in':
			AttrEdit.showattreditor(self.mother.toplevel, self.node, 'transIn')
		else:
			AttrEdit.showattreditor(self.mother.toplevel, self.node, 'transOut')

	def posttransitionmenu(self):
		transitionnames = self.node.context.transitions.keys()
		transitionnames.sort()
		transitionnames.insert(0, 'No transition')
		if self.in_or_out == 'in':
			which = 'transIn'
		else:
			which = 'transOut'
		curtransition = MMAttrdefs.getattr(self.node, which)
		if not curtransition:
			curtransition = 'No transition'
		if curtransition in transitionnames:
			transitionnames.remove(curtransition)
		transitionnames.insert(0, curtransition)
		return which, transitionnames

	def transition_callback(self, which, new):
		curtransition = MMAttrdefs.getattr(self.node, which)
		if not curtransition:
			curtransition = 'No transition'
		if new == curtransition:
			return
		if new == 'No transition':
			new = ''
		editmgr = self.mother.editmgr
		if not editmgr.transaction():
			return # Not possible at this time
		editmgr.setnodeattr(self.node, which, new)
		editmgr.commit()


######################################################################
# Widget decorations.
######################################################################

class PushBackBarWidget(MMWidgetDecoration):
	# This is a push-back bar between nodes.
	def __init__(self, parent, mother):
		MMWidgetDecoration.__init__(self, parent, mother)
		self.node = parent.node
		self.parent = parent

	def draw(self, displist):
		# TODO: draw color based on something??
		redfraction = self.parent.downloadtime_lag_errorfraction
		x, y, w, h = self.get_box()
		displist.fgcolor(TEXTCOLOR)
		displist.drawfbox(COLCOLOR, (x, y, w*redfraction, h))
		displist.drawfbox(LEAFCOLOR, (x+w*redfraction, y, w*(1-redfraction), h))
		displist.draw3dbox(FOCUSLEFT, FOCUSTOP, COLCOLOR, FOCUSBOTTOM, self.get_box())

	def draw_selected(self, displist):
		redfraction = self.parent.downloadtime_lag_errorfraction
		x, y, w, h = self.get_box()
		displist.fgcolor(TEXTCOLOR)
		displist.drawfbox(COLCOLOR, (x, y, w*redfraction, h))
		displist.drawfbox(LEAFCOLOR, (x+redfraction, y, w*(1-redfraction), h))
		displist.drawbox(self.get_box())

	def draw_unselected(self, displist):
		self.draw(displist)

	def draw_box(self, displist):
		self.parent.draw_box(displist)

	def select(self):
		self.parent.select()

	def unselect(self):
		self.parent.unselect()

	def attrcall(self, initattr=None):
		self.mother.toplevel.setwaiting()
		import AttrEdit
		AttrEdit.showattreditor(self.mother.toplevel, self.node, '.begin1')


class TimelineWidget(MMWidgetDecoration):
	# A widget showing the timeline
	def __init__(self, mmwidget, mother):
		MMWidgetDecoration.__init__(self, mmwidget, mother)
		self.minwidth = 0
		mmwidget.GetTimes('virtual')

	def recalc_minsize(self):
		minheight = 2*TITLESIZE
		if self.minwidth:
			self.boxsize = self.minwidth, minheight
		else:
			self.boxsize = f_timescale.strsizePXL(' 000:00 000:00 000:00 ')[0], minheight
		return self.boxsize

	def setminwidth(self, width):
		self.minwidth = width

	def moveto(self, coords, timemapper):
		MMWidgetDecoration.moveto(self, coords)
		self.timemapper = timemapper
		x, y, w, h = self.get_box()
		if self.minwidth:
			# remember updated minimum width
			self.minwidth = w
		if TIMELINE_AT_TOP:
			line_y = y + (h/2)
			tick_top = line_y
			tick_bot = y+h-(h/3)
			longtick_top = line_y
			longtick_bot = y + h - (h/6)
			midtick_top = line_y
			midtick_bot = (tick_bot+longtick_bot)/2
			endtick_top = line_y - (h/3)
			endtick_bot = longtick_bot
			label_top = y
			label_bot = y + (h/2)
		else:
			line_y = y + (h/2)
			tick_top = y + (h/3)
			tick_bot = line_y
			longtick_top = y + (h/6)
			longtick_bot = line_y
			midtick_top = (tick_top+longtick_top)/2
			midtick_bot = line_y
			endtick_top = longtick_top
			endtick_bot = line_y + (h/6)
			label_top = y + (h/2)
			label_bot = y + h
		self.params = line_y, tick_top, tick_bot, longtick_top, longtick_bot, midtick_top, midtick_bot, endtick_top, endtick_bot, label_top, label_bot

	def draw(self, displist):
		# this method is way too complex.
		x, y, w, h = self.get_box()
		line_y, tick_top, tick_bot, longtick_top, longtick_bot, midtick_top, midtick_bot, endtick_top, endtick_bot, label_top, label_bot = self.params
		timemapper = self.timemapper
		t0, t1, t2, download, begindelay = self.get_mmwidget().GetTimes('virtual')
		min = timemapper.time2pixel(t0, 'left')
		max = timemapper.time2pixel(t2, 'right')
		displist.drawline(TEXTCOLOR, [(min, line_y), (max, line_y)])
		length = max - min	# length of real timeline
		for time, left, right in timemapper.gettimesegments(range=(t0, t2)):
			if left != right:
				displist.drawline(COLCOLOR, [(left, line_y), (right, line_y)])
				length = length - (right - left)
		displist.usefont(f_timescale)
		if t0 == t2:
			if t0 < 60:
				label = fmtfloat(t0)
			else:
				label = '%02d:%02.2d'%(int(t0)/60, int(t0)%60)
			displist.centerstring(min, label_top, max, label_bot, label)
			return
		labelwidth = displist.strsizePXL('000:00 ')[0]
		halflabelwidth = labelwidth / 2
		lastlabelpos = x - halflabelwidth - 1
		lb, ub, quantum, factor = setlim(t0, t2)
		length = length * (ub-lb) / (factor * (t2-t0))
		maxnlabel = length / labelwidth
		qf = qr = 1
		while quantum >= 10:
			qf = qf * 10
			quantum = quantum / 10
		prev = qf, qr, quantum
		while qf * quantum >= 3 * qr * (ub-lb) / length:
			prev = qf, qr, quantum
			if quantum == 5:
				quantum = 2
			elif quantum == 2:
				quantum = 1
			else: # quantum == 1
				quantum = 5
				if qf == 1:
					qr = qr * 10
				else:
					qf = qf / 10
		qf, qr, quantum = prev
		quantum = qf * quantum
		factor = factor * qr
		lb = lb * qr
		ub = ub * qr
		nticks = (int(ub+.5) - int(lb+.5)) / quantum
		mod = nticks / maxnlabel
		i = 1
		while i < mod:
			i = i * 10
		if i / 5 > mod:
			mod = i / 5
		elif i / 2 > mod:
			mod = i / 2
		else:
			mod = i
##		if i / 2 <= mod:
##			mod = i / 2
##		elif i / 5 <= mod:
##			mod = i / 5
##		else:
##			mod = i / 10
		mod = mod * quantum
		for t in range(int(lb+.5), int(ub+.5) + quantum, quantum):
			time = float(t) / factor
			if time < t0:
				continue
			if time > t2:
				break
			tick_x = timemapper.interptime2pixel(time)
			tick_x2 = timemapper.interptime2pixel(time, align='right')
			tick_x_mid = (tick_x + tick_x2) / 2
			# Check whether it is time for a tick
			if t % mod == 0: # and tick_x > lastlabelpos + halflabelwidth:
				lastlabelpos = tick_x_mid + halflabelwidth
				cur_tick_top = longtick_top
				cur_tick_bot = longtick_bot
				if time < 60:
					label = fmtfloat(time)
				else:
					label = '%02d:%02.2d'%(int(time)/60, int(time)%60)
				lw = displist.strsizePXL(label)[0]
				if tick_x_mid-lw/2 < x + HEDGSIZE:
					displist.setpos(x + HEDGSIZE, (label_top + label_bot + displist.fontheightPXL()) / 2)
					displist.writestr(label)
				elif tick_x_mid+lw/2 > x + w - HEDGSIZE:
					displist.setpos(x + w - lw - HEDGSIZE, (label_top + label_bot + displist.fontheightPXL()) / 2)
					displist.writestr(label)
				else:
					displist.centerstring(tick_x_mid-lw/2-1, label_top,
							      tick_x_mid+lw/2+1, label_bot, label)
			elif t % 10 == 0:
				cur_tick_top = midtick_top
				cur_tick_bot = midtick_bot
			else:
				cur_tick_top = tick_top
				cur_tick_bot = tick_bot
			displist.drawline(TEXTCOLOR, [(tick_x, cur_tick_top), (tick_x, cur_tick_bot)])
			if tick_x != tick_x2:
				displist.drawline(COLCOLOR, [(tick_x2, cur_tick_top), (tick_x2, cur_tick_bot)])
# to also draw a horizontal line between the tips of the two ticks, use the following instead
##				displist.drawline(COLCOLOR, [(tick_x, cur_tick_top), (tick_x2, cur_tick_top), (tick_x2, cur_tick_bot), (tick_x, cur_tick_bot)])
	draw_selected = draw

# A box with icons in it.
# Comes before the node's name.
class IconBox(MMWidgetDecoration):
	def __init__(self, mmwidget, mother):
		MMWidgetDecoration.__init__(self, mmwidget, mother)
		self._iconlist = []

	def destroy(self):
		for icon in self._iconlist:
			icon.destroy()
		self._iconlist = []
		MMWidgetDecoration.destroy(self)

	def add_icon(self, iconname=None, callback=None, contextmenu=None, arrowto=None):
		# iconname - name of an icon, decides which icon to use.
		# callback - function to call when icon is clicked on.
		# contextmenu - pop-up menu to use.
		# arrowto - Draw an arrow to another icon on the screen.
		icon = Icon(self.mmwidget, self.mother)
		icon.set_icon(iconname)
		if callback:
			icon.set_callback(callback)
		if contextmenu:
			icon.set_contextmenu(contextmenu)
		if arrowto:
			icon.add_arrow(arrowto)
		i = 0
		for n in ('error',
			  'danglingevent', 'danglinganchor',
			  'linkdst', 'beginevent',
			  'linksrc','causeevent',
			  'endevent',  # Not sure where this one should go....
			  ):
			if iconname == n:
				self._iconlist.insert(i, icon)
				break
			if i < len(self._iconlist) and self._iconlist[i].icon == n:
				i = i + 1
		else:
			print 'Icon has no fixed position:', iconname
			self._iconlist.append(icon)
		self.recalc_minsize()
		return icon

	def del_icon(self, icon):
		self._iconlist.remove(icon)
		self.recalc_minsize()

	def recalc_minsize(self):
		# Always the number of icons.
		self.boxsize = (len(self._iconlist) * ICONSIZE), ICONSIZE
		return self.boxsize

	def get_clicked_obj_at(self, coords):
		x,y = coords
		return self.__get_icon_at_position(x)

	def is_hit(self, pos):
		l,t,a,b = self.pos_abs
		x,y = pos
		if l < x < l+(len(self._iconlist)*ICONSIZE) and t < y < t+ICONSIZE:
			return 1
		else:
			return 0

	def draw(self, displist):
		l,t,r,b = self.pos_abs
		for icon in self._iconlist:
			icon.moveto((l,t,r,b))
			icon.draw(displist)
			l = l + ICONSIZE

	draw_selected = draw

	def __get_icon_at_position(self, x):
		l,t,r,b = self.pos_abs
		if len(self._iconlist) > 0:
			index = int((x-l)/ICONSIZE)
			if index >= 0 and index < len(self._iconlist):
				return self._iconlist[index]
		else:
			return None

	def mouse0release(self, coords):
		x,y = coords
		l,t,r,b = self.pos_abs
		icon = self.__get_icon_at_position(x)
		if icon:
			icon.mouse0release(coords)
		else:
			return

		#if self.callback:
		#	apply(apply, self.callback)


class Icon(MMWidgetDecoration):
	# Display an icon which can be clicked on. This can be used for
	# any icon on screen.

	def __init__(self, mmwidget, mother):
		MMWidgetDecoration.__init__(self, mmwidget, mother)
		self.callback = None
		self.arrowto = []	# a list of other MMWidgets.
		self.icon = ""
		self.contextmenu = None
		self.initattr = None	# this is the attribute that gets selected in the

		self.set_properties()

	def __repr__(self):
		return '<%s instance, icon="%s", node=%s, id=%X>' % (self.__class__.__name__, self.icon, `self.mmwidget`, id(self))

	def destroy(self):
		self.callback = None
		self.arrowto = None
		self.contextmenu = None
		self.initattr = None
		MMWidgetDecoration.destroy(self)

	def recalc_minsize(self):
		self.boxsize = ICONSIZE, ICONSIZE
		return self.boxsize

	def set_icon(self, iconname):
		self.icon = iconname
		return self

	def set_properties(self, selectable=1, callbackable=1, arrowable=0, arrowdirection=0, initattr=None):
		self.selectable = selectable
		self.callbackable = callbackable
		self.arrowable = arrowable
		self.arrowdirection = arrowdirection
		self.initattr = initattr
		return self

	def select(self):
		if self.selectable:
			MMWidgetDecoration.select(self)

	def unselect(self):
		if self.selectable:
			MMWidgetDecoration.unselect(self)

	def set_callback(self, callback, args=()):
		self.callback = callback, args
		return self

	def mouse0release(self, coords):
		if self.callback is not None and self.icon:
			apply(apply, self.callback)

	def moveto(self, pos):
		l,t,r,b = pos
		iconsizex = ERRSIZE
		iconsizey = ERRSIZE
		MMWidgetDecoration.moveto(self, (l, t, l+iconsizex, t+iconsizey))
		return self

	def draw_selected(self, displist):
		if not self.selectable:
			self.draw(displist)
			return
##		displist.drawfbox((0,0,0),self.get_box())
		self.draw(displist)
		if self.arrowable:	# The arrows get drawn by the Hierarchyview at a later stage.
			for arrow in self.arrowto:
				p = arrow.get_node().GetCollapsedParent()
				if p:
					l,t,r,b = p.views['struct_view'].get_collapse_icon().pos_abs
				else:
					l,t,r,b = arrow.pos_abs
				if l == 0:
					return
				xd = (l+r)/2
				yd = (t+b)/2
				l,t,r,b = self.pos_abs
				xs = (l+r)/2
				ys = (t+b)/2
				if self.arrowdirection:
					self.mother.add_arrow(self, ARROWCOLOR, (xs,ys),(xd,yd))
				else:
					self.mother.add_arrow(self, ARROWCOLOR, (xd,yd),(xs,ys))

	def draw_unselected(self, displist):
		self.draw(displist)

	def draw(self, displist):
		if self.icon is not None:
			displist.drawicon(self.get_box(), self.icon)

	def set_contextmenu(self, foobar):
		self.contextmenu = foobar			# TODO.
		return self
	def get_contextmenu(self):
		return self.contextmenu

	def add_arrow(self, dest):
		# dest can be any MMWidget.
		if dest and dest not in self.arrowto:
			self.arrowto.append(dest)
		return self

	def is_selectable(self):
		return self.selectable

	def attrcall(self, initattr=None):
		self.get_mmwidget().attrcall(initattr=self.initattr)

# Maybe one day.
##class CollapseIcon(Icon):
##	# For collapsing and uncollapsing nodes
##	def __init__(self, mmwidget, mother):
##		Icon.__init__(self, mmwidget, mother)
##		self.selectable = 0
##		self.callbackable = 1
##		self.arrowable = 0
##		self.contextmenu = None

##class EventSourceIcon(Icon):
##	# Is the source of an event
##	def __init__(self, mmwidget, mother):
##		Icon.__init__(self, mmwidget, mother)
##		self.selectable = 1
##		self.callbackable = 1
##		self.arrowable = 1
##		self.arrowdirection = 1
##		self.contextmenu = None

##class EventIcon(Icon):
##	# Is the actual event.
##	pass




##############################################################################
			# Crap at the end of the file.

class BrushWidget(MMNodeWidget):
	def __init__(self):
		print "TODO: BrushWidget"

class TimeStripSeqWidget(SeqWidget):
	# A sequence that has a channel widget at the start of it.
	# This only exists at the second level from the root, assuming the root is a
	# par.
	# Wow. I like this sort of code. If only the rest of the classes were this easy. -mjvdg
	HAS_COLLAPSE_BUTTON = 0
	HAS_CHANNEL_BOX = 1

class ImageBoxWidget(MMWidgetDecoration):
	# Common baseclass for dropbox and channelbox
	# This is only for images shown as part of the sequence views. This
	# is not used for any image on screen.

	def recalc_minsize(self):
		self.boxsize = MINSIZE, MINSIZE
		return self.boxsize

	def draw(self, displist):
		x,y,w,h = self.get_box()

		# Draw the image.
		image_filename = self._get_image_filename()
		if image_filename != None:
			try:
				sx = DROPAREASIZE
				sy = sx
				cx = x + w/2 # center
				cy = y + h/2
				box = displist.display_image_from_file(
					image_filename,
					center = 1,
					# The coordinates should all be floating point numbers.
					# Wrong - now they are pixels -mjvdg.
					#coordinates = (float(x+w)/12, float(y+h)/6, 5*(float(w)/6), 4*(float(h)/6)),
					coordinates = (cx - sx/2, cy - sy/2, sx, sy),
					fit = 'icon'
					)
#				print "TODO: fix those 32x32 hard-coded sizes."
			except windowinterface.error:
				pass
			else:
				displist.fgcolor(TEXTCOLOR)
				displist.drawbox(box)


class DropBoxWidget(ImageBoxWidget):
	# This is the stupid drop-box at the end of a sequence. Looks like a
	# MediaWidget, acts like a MediaWidget, but isn't a MediaWidget.

	def _get_image_filename(self):
		f = os.path.join(self.mother.datadir, 'dropbox.tiff')
		return f


class ChannelBoxWidget(ImageBoxWidget):
	# This is the box at the start of a Sequence which represents which channel it 'owns'
	def __init__(self, parent, node, mother):
		Widgets.Widget.__init__(self, mother)
		self.node = node
		self.parent = parent

	def draw(self, displist):
		ImageBoxWidget.draw(self, displist)
		x, y, w, h = self.get_box()
		texth = TITLESIZE
		texty = y + h - texth
		availbw  = settings.get('system_bitrate')
		bwfraction = MMAttrdefs.getattr(self.node, 'project_bandwidth_fraction')
		if bwfraction <= 0:
			return
		bandwidth = availbw * bwfraction
		if bandwidth < 1000:
			label = '%d bps'%int(bandwidth)
		elif bandwidth < 10000:
			label = '%3.1f Kbps'%(bandwidth / 1000.0)
		elif bandwidth < 1000000:
			label = '%3d Kbps' % int(bandwidth / 1000)
		elif bandwidth < 10000000:
			label = '%3.1f Mbps'%(bandwidth / 1000000.0)
		else:
			label = '%d Mbps'%int(bandwidth / 1000000)
		displist.fgcolor(CTEXTCOLOR)
		displist.usefont(f_title)
		displist.centerstring(x, texty, x+w, texty+texth, label)

	def recalc_minsize(self):
		self.boxsize = MINSIZE, MINSIZE + TITLESIZE
		return self.boxsize

	def _get_image_filename(self):
		channel_type = MMAttrdefs.getattr(self.node, 'project_default_type')
		if not channel_type:
			channel_type = 'null'
		f = os.path.join(self.mother.datadir, '%s.tiff'%channel_type)
		if not os.path.exists(f):
			f = os.path.join(self.mother.datadir, 'null.tiff')
		return f

	def select(self):
		self.parent.select()

	def unselect(self):
		self.parent.unselect()

	def attrcall(self, initattr=None):
		self.mother.toplevel.setwaiting()
		chname = MMAttrdefs.getattr(self.node, 'project_default_region')
		if not chname:
			self.parent.attrcall(initattr=initattr)
		channel = self.mother.toplevel.context.getchannel(chname)
		if not channel:
			self.parent.attrcall(initattr=initattr)
		import AttrEdit
		AttrEdit.showchannelattreditor(self.mother.toplevel, channel)

def setlim(lb, ub):
	from math import ceil, floor
	while 1:
		delta = ub - lb
		# scale up by r, a power of 10, so range (delta) exceeds 1
		# find power of 10 quantum, s, such that delta/10 <= s < delta
		r = s = 1
		while delta * r < 10:
			r = r * 10
		delta = delta * r
		while s * 10 < delta:
			s = s * 10
		lb = lb * r
		ub = ub * r
		# set s = (1,2,5)*10**n so that 3-5 quanta cover range
		if s >= delta / 2:
## 		if s >= delta / 3:
			s = s / 2
		elif s < delta / 5:
			s = s * 2
		ub = abs(s) * ceil(float(ub) / abs(s))
		lb = abs(s) * floor(float(lb) / abs(s))
		if 0 < lb <= s:
			lb = 0
		elif -s <= ub < 0:
			ub = 0
		else:
			return (lb, ub, s, r)
