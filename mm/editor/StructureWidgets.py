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
import BandwidthCompute
from AppDefaults import *
from fmtfloat import fmtfloat
import Duration
import ArmStates
from Hlinks import ANCHOR1, ANCHOR2

TIMELINE_AT_TOP = 1
TIMELINE_IN_FOCUS = 1
NAMEDISTANCE = 150
SPACEWIDTH = f_title.strsizePXL(' ')[0]

ICONXSIZE = ICONYSIZE = windowinterface.ICONSIZE_PXL
EVENTARROWCOLOR = (0,255,0)
LINKARROWCOLOR = (0,0,255)

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
		self.__image_size = None

		self.timemapper = None
		self.timeline = None
		self.greyout = None
		self.bwstrip = None
		self.need_draghandles = None

		# Holds little icons..
		if isinstance(self, CommentWidget):
			self.iconbox = None
		else:
			self.iconbox = IconBox(self, self.mother, vertical = settings.get('vertical_icons'))
		self.cause_event_icon = None
		self.linksrc_icon = None
		self.linkdst_icon = None
		self.infoicon = None
		if self.iconbox is not None and node.infoicon:
			self.infoicon = self.iconbox.add_icon(node.infoicon, callback = self.show_mesg)
		if self.iconbox is None or node.GetType() == 'comment':
			self.playicon = None
		else:
			self.playicon = self.iconbox.add_icon(node.armedmode or 'idle')
			self.playicon.set_properties(selectable=0, callbackable=0)
		# these 5 are never set in this class but are provided for the benefit of subclasses
		# this means we also don't destroy these
		self.collapsebutton = None
		self.transition_in = None
		self.transition_out = None
		self.dropbox = None
		self.channelbox = None

	def __repr__(self):
		return '<%s instance, name="%s", node=%s, id=%X>' % (self.__class__.__name__, self.name, `self.node`, id(self))

	def destroy(self):
		# Prevent cyclic dependancies.
		node = self.node
		self.playicon = None
		self.cause_event_icon = None
		self.linksrc_icon = None
		self.linkdst_icon = None
		self.infoicon = None
		if self.iconbox is not None:
			self.iconbox.destroy()
			self.iconbox = None
		if self.dropbox is not None:
			self.dropbox.destroy()
			self.dropbox = None
		if self.channelbox is not None:
			self.channelbox.destroy()
			self.channelbox = None
		if self.timeline is not None:
			self.timeline.destroy()
			self.timeline = None
		if self.greyout is not None:
			self.greyout.destroy()
			self.greyout = None
		if self.bwstrip is not None:
			self.bwstrip.destroy()
			self.bwstrip = None
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
		assert self.node is not None
		return self.node

	def add_link_icons(self):
		node = self.node
		dangling = None
		hlinks = node.GetContext().hyperlinks
		nodes = filter(lambda x: x.GetType() == 'anchor', node.GetChildren())
		for x in [node] + nodes:
			links = hlinks.findsrclinks(x)
			if x is not node and dangling is None and not links:
				dangling = self.iconbox.add_icon('danglinganchor')
			for l in links:
				# we're the hyperlink source
				otherwidget = None
				if type(l[ANCHOR2]) is not type(''):
					othernode = l[ANCHOR2]
					while othernode is not None and not othernode.views.has_key('struct_view'):
						othernode = othernode.GetParent()
					if othernode is not None:
						otherwidget = othernode.views['struct_view'].get_linkdst_icon()
				if self.linksrc_icon is None:
					self.linksrc_icon = self.iconbox.add_icon('linksrc', arrowto = otherwidget, arrowcolor = LINKARROWCOLOR)
					self.linksrc_icon.set_properties(issrc=1)
				else:
					self.linksrc_icon.add_arrow(otherwidget, LINKARROWCOLOR)
			for l in hlinks.finddstlinks(x):
				# we're the hyperlink destination
				otherwidget = None
				if type(l[ANCHOR1]) is not type(''):
					othernode = l[ANCHOR1]
					while othernode is not None and not othernode.views.has_key('struct_view'):
						othernode = othernode.GetParent()
					if othernode is not None:
						otherwidget = othernode.views['struct_view'].get_linksrc_icon()
				if self.linkdst_icon is None:
					self.linkdst_icon = self.iconbox.add_icon('linkdst', arrowto = otherwidget, arrowcolor = LINKARROWCOLOR)
					self.linkdst_icon.set_properties(issrc=0)
				else:
					self.linkdst_icon.add_arrow(otherwidget, LINKARROWCOLOR)

	def add_event_icons(self):
		if self.node.GetType() != 'comment':
			self.__add_events_helper('beginevent', 'beginlist')
			self.__add_events_helper('endevent', 'endlist')

	def __add_events_helper(self, iconname, attr):
		icon = None
		for arc in MMAttrdefs.getattr(self.node, attr):
			othernode = arc.refnode()
			while othernode is not None and not othernode.views.has_key('struct_view'):
				othernode = othernode.GetParent()
			if othernode is not None:
				otherwidget = othernode.views['struct_view'].get_cause_event_icon()
				if icon is None:
					icon = self.iconbox.add_icon(iconname, arrowto = otherwidget, arrowcolor = EVENTARROWCOLOR)
					icon.set_properties(initattr=attr)
					icon.set_contextmenu(self.mother.event_popupmenu_dest)
				else:
					icon.add_arrow(otherwidget, EVENTARROWCOLOR)
				otherwidget.add_arrow(icon, EVENTARROWCOLOR)
			else: # no arrow.
				if icon is None:
					icon = self.iconbox.add_icon(iconname)
					icon.set_properties(initattr=attr)
					icon.set_contextmenu(self.mother.event_popupmenu_dest)

	def uncollapse_all(self):
		# Placeholder for a recursive function.
		return

	def collapse_all(self):		  # Is this doable using a higher-order function?
		return

	def iscollapsed(self):
		return 0

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

	def init_timemapper(self, timemapper, ignore_time = 0):
		if not self.node.WillPlay():
			return None
		if timemapper is None and self.node.showtime and not ignore_time:
			if self.node.GetType() in ('excl', 'prio'):
				showtime = self.node.showtime
				self.node.showtime = 0
				for c in self.children:
					c.node.showtime = showtime
			else:
				timemapper = TimeMapper.TimeMapper()
				# Hack by Jack - if we already have a timemapper
				# we copy the stalls. This is probably not a good
				# idea, but I don't know why we reallocate a timemapper
				# anyway. Sjoerd?
				if self.timemapper:
					stalllist = self.timemapper.getallstalls()
					for stalltime, (stalldur, stalltype) in stalllist:
						timemapper.addstalltime(stalltime, stalldur, stalltype)

				if self.timeline is None:
					self.timeline = TimelineWidget(self, self.mother)
				self.timemapper = timemapper
		elif self.node.showtime and not ignore_time:
			if self.timeline is None:
				self.timeline = TimelineWidget(self, self.mother)
			if self.timemapper is not None:
				self.timemapper = None
		else:
			if self.timeline is not None:
				self.timeline.destroy()
				self.timeline = None
			if self.timemapper is not None:
				self.timemapper = None
		self.greyout = None
		if self.timeline:
			self.greyout = GreyoutWidget(self, self.mother)
		if self.node.showtime == 'bwstrip' and not ignore_time:
			if self.bwstrip is None:
				self.bwstrip = BandWidthWidget(self, self.mother)
				maxbandwidth, prerolltime, delaycount, errorseconds, errorcount, stalls = \
					BandwidthCompute.compute_bandwidth(self.node)
				if timemapper:
					if prerolltime:
						timemapper.addstalltime(0, prerolltime, 'preroll')
					for stalltime, stallduration, stalltype in stalls:
						timemapper.addstalltime(stalltime, stallduration, stalltype)
		else:
			if self.bwstrip:
				self.bwstrip.destroy()
				self.bwstrip = None
		return timemapper

	def fix_timemapper(self, timemapper):
		if timemapper is not None:
			self.adddependencies(timemapper)
			if self.timemapper is not None:
				t0, t1, t2, download, begindelay = self.GetTimes('virtual')
				p0, p1 = self.addcollisions(t0, t2, timemapper, (t0, t1, t2, download, begindelay))
				self.timemapper.addcollision(t0, p0)
				self.timemapper.addcollision(t2, p1)
				min_pxl_per_sec = MIN_PXL_PER_SEC_DEFAULT
				if self.timeline is None or self.timeline.minwidth == 0:
					try:
						min_pxl_per_sec = self.node.min_pxl_per_sec
					except AttributeError:
						pass
				pxl_per_sec = timemapper.calculate(self.node.showtime in ('cfocus', 'bwstrip'), min_pixels_per_second = min_pxl_per_sec)
				if not hasattr(self.node, 'min_pxl_per_sec'):
					self.node.min_pxl_per_sec = pxl_per_sec
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
		node = self.node

		# iconbox is displayed at top or left
		if self.iconbox is not None and node.infoicon and self.infoicon is None:
			self.infoicon = self.iconbox.add_icon(node.infoicon, callback = self.show_mesg)
		elif not node.infoicon and self.infoicon is not None:
			# self.infoicon is not None implies self.iconbox is not None
			self.iconbox.del_icon(self.infoicon)
			self.infoicon.destroy()
			self.infoicon = None
		if self.iconbox is not None:
			node.set_infoicon = self.set_infoicon
			node.set_armedmode = self.set_armedmode
			self.set_armedmode(node.armedmode, redraw = 0)
		if self.iconbox is not None:
			ibxsize, ibysize = self.iconbox.recalc_minsize()
		else:
			ibxsize = ibysize = 0

		# thumbnail
		icon = None
		if not node.GetChildren() and not self.iscollapsed():
			# use empty_icon if no children and it exists
			icon = node.GetAttrDef('empty_icon', None)
		if icon is None:
			# use thumbnail icon if defined (and we're not using empty_icon)
			icon = node.GetAttrDef('thumbnail_icon', None)
		imxsize = imysize = 24
		if not MMAttrdefs.getattr(node, 'thumbnail_scale'):
			import Sizes
			if icon is not None:
				icon = node.context.findurl(icon)
				try:
					icon = MMurl.urlretrieve(icon)[0]
				except:
					icon = None
			elif node.GetType() in MMTypes.mediatypes and node.GetType() != 'brush':
				icon = self.__get_image_filename(node, image = 0)

			if icon:
				try:
					imxsize, imysize = Sizes.GetImageSize(icon)
				except:
					pass
				if imxsize > 0 and imysize > 0:
					self.__image_size = imxsize, imysize

		text = None
		if not node.GetChildren():
			text = node.GetAttrDef('empty_text', None)
		if text:
			txxsize, txysize = f_title.strsizePXL(text)
		elif self.name:
			txxsize, txysize = f_title.strsizePXL(self.name)
		else:
			txxsize = txysize = 0

		# put things together
		if self.iconbox is not None and self.iconbox.vertical:
			# icons on the left, then thumbnail, then text
			# if text var not empty, text is required, else optional
			xsize = ibxsize + imxsize + 2*HEDGSIZE
			if text:
				xsize = xsize + 2 + txxsize
			if icon and self.name and isinstance(self, StructureObjWidget):
				imysize = imysize + TITLESIZE
			ysize = max(ibysize, imysize, txysize) + 2*VEDGSIZE
			xsize = max(xsize, MINSIZE)
			ysize = max(ysize, MINSIZE)
			if not text:
				xsize = min(xsize, MAXSIZE)
		else:
			# icons at the top with text next to it
			xsize1 = ibxsize
			if not text:
				xsize1 = xsize1 + txxsize
			xsize2 = imxsize
			if text:
				xsize2 = xsize2 + 2 + txxsize
			xsize = max(xsize1, xsize2) + 2*HEDGSIZE
			ysize = ibysize + imysize + 2*VEDGSIZE
			xsize = max(xsize, MINSIZE)
			ysize = max(ysize, MINSIZE)
			if not text:
				xsize = min(xsize, MAXSIZE)

		# add ons
		if self.dropbox is not None:
			dbxsize, dbysize = self.dropbox.recalc_minsize()
			xsize = xsize  + GAPSIZE + dbxsize
			if dbysize + 2*VEDGSIZE > ysize:
				ysize = dbysize + 2*VEDGSIZE

		if self.timeline is not None:
			w, h = self.timeline.recalc_minsize()
			if w > xsize:
				xsize = w
			ysize = ysize + h
		if self.bwstrip is not None:
			w, h = self.bwstrip.recalc_minsize(self.node, timemapper)
			if w > xsize:
				xsize = w
			ysize = ysize + h
##		if timemapper is not None and not text:
##			t0, t1, t2, downloadlag, begindelay = self.GetTimes('virtual')
##			if t0 == t2:
##				# very special case--zero duration element
##				return ICONXSIZE+2*HEDGSIZE, MINSIZE
		return xsize, ysize

	def recalc_minsize(self, timemapper = None, ignore_time = 0):
		timemapper = self.init_timemapper(timemapper, ignore_time)
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
		t = t + VEDGSIZE
		b = t + TITLESIZE
		l = l + HEDGSIZE
		r = r - HEDGSIZE
		if self.iconbox is not None:
			self.iconbox.moveto((l,t,r,b))
			iw, ih = self.iconbox.get_minsize()
			l = l + iw
			if l <= r:
				self.iconbox.draw(displist)
		if l < r and self.name and (self.iconbox is None or not self.iconbox.vertical or isinstance(self, StructureObjWidget)):
			x, y = l, t+displist.baselinePXL()
			displist.setpos(x, y)
			namewidth = displist.strsizePXL(self.name)[0]
##			liney = y-displist.baselinePXL()/2
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
				# name doesn't fit fully; fit as much as we can with ... appended
				for i in range(len(self.name)-1,-1,-1):
					if x + displist.strsizePXL(self.name[:i]+'...')[0] <= r:
						displist.writestr(self.name[:i]+'...')
						break
		if self.timeline is not None:
			self.timeline.draw(displist)
		if self.bwstrip is not None:
			self.bwstrip.draw(displist)
		# Draw the silly transitions.
		if self.transition_in is not None:
			self.transition_in.draw(displist)
		if self.transition_out is not None:
			self.transition_out.draw(displist)
		displist.draw3dbox(FOCUSLEFT, FOCUSTOP, FOCUSRIGHT, FOCUSBOTTOM, self.get_box())
		self.draw_draghandles(displist)
		if self.greyout is not None:
			self.greyout.draw(displist)

	def draw_draghandles(self, displist):
		if self.need_draghandles is None:
			return
		l,r,t = self.need_draghandles
		displist.drawfbox((0,0,0), (l,t,DRAGHANDLESIZE,DRAGHANDLESIZE))
		displist.drawfbox((0,0,0), (r-DRAGHANDLESIZE,t,DRAGHANDLESIZE,DRAGHANDLESIZE))

	def drawnodecontent(self, displist, (x,y,w,h), node):
		icon = self.node.GetAttrDef('thumbnail_icon', None)
		if icon is not None:
			icon = self.node.context.findurl(icon)
			try:
				icon = MMurl.urlretrieve(icon)[0]
			except:
				icon = None
			self.do_draw_image(icon, self.name, (x,y,w,h), displist)
		elif node.GetChannelType() == 'brush':
			displist.drawfbox(MMAttrdefs.getattr(node, 'fgcolor'), (x+w/12, y+h/6, 5*(w/6), 4*(h/6)))
			displist.fgcolor(TEXTCOLOR)
			displist.drawbox((x+w/12, y+h/6, 5*(w/6), 4*(h/6)))
		elif w > 0 and h > 0:
			self.do_draw_image(self.__get_image_filename(node), self.name, (x,y,w,h), displist)

	def __get_image_filename(self, node, image = 1):
		# return a file name for a thumbnail image
		ntype = node.GetType()
		if ntype not in ('ext', 'imm'):
			return os.path.join(self.mother.datadir, '%s.tiff' % ntype)

		url = node.GetAttrDef('file', None)
		if not url:
			# no file attr, so no thumbnail
			return None

		media_type = MMmimetypes.guess_type(url)[0]

		channel_type = node.GetChannelType()
		if self.mother.thumbnails and channel_type == 'image':
			if not image:
				return None
			url = node.context.findurl(url)
			try:
				return MMurl.urlretrieve(url)[0]
			except IOError, arg:
				self.set_infoicon('error', 'Cannot load image: %s'%`url`)
		# either not an image, or image couldn't be found
		return os.path.join(self.mother.datadir, '%s.tiff'%channel_type)

	# used by MediaWidget and CommentWidget
	def do_draw_image(self, image_filename, name, (x,y,w,h), displist, forcetext = 0, image_size = None):
		if w <= 0 or h <= 0:
			return
		r = x + w
		b = y + h
		imw = w
		imh = h
		if image_size is not None:
			imw, imh = image_size
		elif self.__image_size is not None:
			imw, imh = self.__image_size
		coordinates = (x, y, imw, imh)
		displist.fgcolor(TEXTCOLOR)
		box = x, y, 0, h	# default if no image
		if image_filename and coordinates[2] > 4 and coordinates[3] > 4:
			try:
				box = displist.display_image_from_file(
					image_filename,
					center = 0,
					coordinates = coordinates,
					fit = 'icon')
			except windowinterface.error:
				# some error displaying image
				box = x, y, 0, h
			else:
				displist.drawbox(box)
		box2 = (0,0,0,0)
		if forcetext or (self.iconbox is not None and self.iconbox.vertical):
			# draw name next to image
			displist.fgcolor(CTEXTCOLOR)
			displist.usefont(f_title)
			nx = box[0] + box[2] + 2
			ny = box[1] + box[3] - 2
			displist.setpos(nx, ny)
			namewidth = displist.strsizePXL(name)[0]
			if nx + namewidth <= r:
				# name fits fully
				box2 = displist.writestr(name)
			else:
				for i in range(len(name)-1,-1,-1):
					if nx + displist.strsizePXL(name[:i]+'...')[0] <= r:
						box2 = displist.writestr(name[:i]+'...')
						break
		# calculate number of copies that'll fit in the remaining space
		n = (w-box[2]-box2[2]-HEDGSIZE-HEDGSIZE)/(box[2]+box2[2]+NAMEDISTANCE)
		if n <= 0:
			return
		# calculate distance between left edges to get copies equidistant
		distance = (w-box[2]-box2[2]-HEDGSIZE-HEDGSIZE)/n
		while x + distance + box[2] + box2[2] <= r:
			x = x + distance
			# draw line between copies
			displist.drawline((150,150,150), [(box[0]+box[2],box[1]+box[3]-1),(x,box[1]+box[3]-1)])
			coordinates = (x, y, imw, imh)
			if image_filename:
				box = displist.display_image_from_file(
					image_filename,
					center = 0,
					coordinates = coordinates,
					fit = 'icon')
				displist.drawbox(box)
			else:
				box = (x, y, 0, imh)
			if forcetext or (self.iconbox is not None and self.iconbox.vertical):
				displist.setpos(box[0] + box[2] + 2, box[1] + box[3] - 2)
				displist.writestr(name)

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
			self.cause_event_icon = icon = self.iconbox.add_icon('causeevent')
			icon.set_properties(issrc=1)
			icon.set_contextmenu(self.mother.event_popupmenu_source)
		return self.cause_event_icon

	def get_linksrc_icon(self):
		if self.linksrc_icon is None:
			self.linksrc_icon = icon = self.iconbox.add_icon('linksrc')
			icon.set_properties(issrc=1)
		return self.linksrc_icon

	def get_linkdst_icon(self):
		if self.linkdst_icon is None:
			self.linkdst_icon = icon = self.iconbox.add_icon('linkdst')
			icon.set_properties(issrc=0)
		return self.linkdst_icon

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

#	def cutcall(self):
#		self.mother.deletefocus(1)

#	def copycall(self):
#		mother = self.mother
#		mother.toplevel.setwaiting()
#		mother.copyfocus()

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

##	def pastebeforecall(self):
##		self.mother.paste(-1)

##	def pasteaftercall(self):
##		self.mother.paste(1)

##	def pasteundercall(self):
##		self.mother.paste(0)

	def show_mesg(self, msg = None):
		if msg is None:
			msg = self.node.errormessage
		if msg:
			windowinterface.showmessage(msg, parent=self.mother.window)

	def get_popupmenu(self):
		return []

#
# The StructureObjWidget represents any node which has children,
# and is thus collapsable.
#
class StructureObjWidget(MMNodeWidget):
	# A view of a seq, par, excl or any internal structure node.
	HAS_COLLAPSE_BUTTON = 1
	DRAWCOLLAPSEDMEDIACHILD = 0

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
			self.collapsebutton = self.iconbox.add_icon(icon, self.toggle_collapsed)
			self.collapsebutton.set_properties(callbackable=1, selectable=0)
		self.parent_widget = parent # This is the parent node. Used for recalcing optimisations.
		for i in self.node.children:
			bob = create_MMNode_widget(i, mother, self)
			if bob is not None:
				self.children.append(bob)
		self.dont_draw_children = 0
		if parent is None:
			self.add_event_icons()
			self.add_link_icons()
		self.previewchild = None
		self.subiconnames = []
		self.subicons = []
		if MMAttrdefs.getattr(self.node, 'project_autoroute'):
			self._setpreviewandsubicons()
		if self.node.GetAttrDef('dropicon', None):
			self.dropbox = DropIconWidget(self, mother)
		elif self.node.children and self.node.GetAttrDef('empty_nonempty', 0):
			self.dropbox = EmptyWidget(self, mother)

	def destroy(self):
		if self.children:
			for i in self.children:
				i.destroy()
		self.children = None
		self.collapsebutton = None
		self.parent_widget = None
		self.previewchild = None
		MMNodeWidget.destroy(self)

	def _setpreviewandsubicons(self):
		# Set preview node and icons for other children iff
		# this is an autorouting node.
		for ch in self.node.children:
			tp = ch.GetType()
			# Skip all non-media types
			if tp not in MMTypes.mediatypes:
				continue
			# Brushes are fine
			if tp == 'brush':
				if not self.previewchild:
					self.previewchild = ch
				continue
			# Skip all empty items
			if tp == 'imm' and not ch.GetValues():
				continue
			if tp == 'ext' and not MMAttrdefs.getattr(ch, 'file'):
				continue
			# If we have no preview node yet this may be a
			# candidate
			mimetypes = MMAttrdefs.getattr(ch, 'allowedmimetypes')
			if not self.previewchild:
				# XXXX Is this the correct test??
				if  'image' in mimetypes or 'video' in mimetypes: # XXXX Maybe more?
					self.previewchild = ch
					continue
			# If we get here this node has information and it
			# isn't used as the preview node. We post an icon.
			iconname = ch.getIconName(wantmedia=1)
			self.subiconnames.append(iconname)

	def recalc_subicons(self):
		# Called on resize, (un)collapse to recalculate
		# whether we show the child node icons
		if self.iscollapsed():
			# We should show them
			if len(self.subiconnames) != len(self.subicons):
				for n in self.subiconnames:
					self.subicons.append(self.iconbox.add_icon(n))
		else:
			# We should remove them
			for icon in self.subicons:
				self.iconbox.del_icon(icon)
			self.subicons = []


	def add_event_icons(self):
		MMNodeWidget.add_event_icons(self)
		for c in self.children:
			c.add_event_icons()

	def add_link_icons(self):
		MMNodeWidget.add_link_icons(self)
		for c in self.children:
			c.add_link_icons()

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
		#if self.collapsebutton and self.collapsebutton.is_hit(pos):
		#	return self.collapsebutton

		if self.channelbox is not None and self.channelbox.is_hit(pos):
			return self.channelbox

		if self.is_hit(pos):
			if self.bwstrip and self.bwstrip.is_hit(pos):
				return self.bwstrip
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
		if self.is_hit(pos):
			if self.collapsebutton is not None and self.collapsebutton.is_hit(pos):
				return self.collapsebutton
			elif self.iconbox.is_hit(pos):
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

	def recalc(self, timemapper = None, bwstrip = None):
		# Recalculate the position of all the contained boxes.
		# Algorithm: Iterate through each of the MMNodes children's views and find their minsizes.
		# Apportion free space equally, based on the size of self.
		# TODO: This does not test for maxheight()
		self.need_resize = 0

		my_l, my_t, my_r, my_b = self.pos_abs

		# account for edges
		my_l = my_l + HEDGSIZE
		my_t = my_t + VEDGSIZE
		my_b = my_b - VEDGSIZE
		my_r = my_r - HEDGSIZE

		if not self.node.WillPlay():
			timemapper = None

		min_width, min_height = self.get_minsize()
		min_width = min_width - 2*HEDGSIZE
		min_height = min_height - 2*VEDGSIZE

		if self.iconbox is not None and self.iconbox.vertical:
			iconboxwidth = self.iconbox.get_minsize()[0]
			my_l = my_l + iconboxwidth
			min_width = min_width - iconboxwidth
			if self.name:
				my_t = my_t + TITLESIZE
				min_height = min_height - TITLESIZE
		else:
			my_t = my_t + TITLESIZE
			min_height = min_height - TITLESIZE

		if self.timemapper is not None:
			timemapper = self.timemapper
			timemapper.setoffset(my_l, my_r - my_l)
			
		if self.bwstrip:
			bwstrip = self.bwstrip

		# Add the timeline, the bandwidth strip and the greyout
		# widget. The greyout widget covers both the timeline and
		# the bandwidth strip.
		if self.timeline is not None:
			tl_w, tl_h = self.timeline.get_minsize()
			if TIMELINE_AT_TOP:
				self.timeline.moveto((my_l, my_t, my_r, my_t+tl_h), timemapper)
				# Tricky.... We know where the line in the timeline
				# widget is
				greyout_t = my_t + tl_h/2
				my_t = my_t + tl_h
				greyout_b = my_t
			else:
				self.timeline.moveto((my_l, my_b-tl_h, my_r, my_b), timemapper)
				greyout_b = my_b
				my_b = my_b - tl_h
				greyout_t = my_b - tl_h/2
			y = self.timeline.params[0]
			self.need_draghandles = my_l,my_r,y-DRAGHANDLESIZE/2
			min_height = min_height - tl_h

		if self.bwstrip is not None:
			bw_w, bw_h = self.bwstrip.get_minsize()
			if TIMELINE_AT_TOP:
				self.bwstrip.moveto((my_l, my_t, my_r, my_t + bw_h), self.node, timemapper)
				my_t = my_t + bw_h
				greyout_b = my_t
			else:
				self.bwstrip.moveto((my_l, my_b - bw_h, my_r, my_b), self.node, timemapper)
				my_b = my_b - bw_h
				greyout_t = my_b
		if self.greyout is not None:
			self.greyout.moveto((my_l, greyout_t, my_r, greyout_b), timemapper)

		if timemapper is None:
			self.need_draghandles = None
		else:
			l,t,r,b = self.pos_abs
			if self.timemapper is None or self.timeline is None:
##				self.need_draghandles = l,r,(t+b)/2
				self.need_draghandles = l,r,b-8

		if self.iscollapsed():
			return

		if self.channelbox is not None:
			this_w, this_h = self.channelbox.get_minsize()
			self.channelbox.moveto((my_l, my_t, my_l+this_w, my_b))
			my_l = my_l + this_w + GAPSIZE
			min_width = min_width - this_w - GAPSIZE

		if self.dropbox is not None:
			this_w,this_h = self.dropbox.get_minsize()
			if self.HORIZONTAL:
				self.dropbox.moveto((my_r-this_w,my_t,my_r,my_b))
				my_r = my_r - this_w - GAPSIZE
				min_width = min_width - this_w - GAPSIZE
			else:
				self.dropbox.moveto((my_l,my_b-this_h,my_r,my_b))
				my_b = my_b - this_h - GAPSIZE
				min_height = min_height - this_h - GAPSIZE

		free_width = (my_r-my_l) - min_width
		if vertical_spread:
			free_height = (my_b-my_t) - min_height
		else:
			free_height = 0

		if self.HORIZONTAL:
			freewidth_per_child = free_width / max(1, len(self.children))
			freeheigt_per_child = 0
		else:
			freeheight_per_child = free_height / max(1, len(self.children))
			freewidth_per_child = 0

		is_excl = self.node.GetType() in ('excl', 'prio')
		if is_excl:
			tm = None
		else:
			tm = timemapper

		this_l = my_l
		this_t = my_t
		this_r = my_r
		this_b = my_b

		for chindex in range(len(self.children)):
			medianode = self.children[chindex]
			# Compute rightmost position we may draw
			if chindex == len(self.children)-1:
				max_r = my_r
			elif tm is None:
				# XXXX Should do this more intelligently
				max_r = my_r
			else:
				# max_r is set below
				pass
			this_w, this_h = medianode.get_minsize()
			if not self.HORIZONTAL:
				this_b = this_t + this_h + freeheight_per_child

			# First compute pushback bar position
			if tm is not None and medianode.node.WillPlay():
				t0, t1, t2, download, begindelay, neededpixel0, neededpixel1 = self.childrentimes[chindex]
				tend = t2
				# tend may be t2, the fill-time, so for fill=hold it may extend past
				# the begin of the next child. We have to truncate in that
				# case.
				if self.HORIZONTAL and chindex < len(self.children)-1:
					nextt = self.childrentimes[chindex+1][0]
					if tend > nextt:
						tend = nextt
				lmin = tm.time2pixel(t0)
				if this_l < lmin:
					this_l = lmin
				this_r = tm.time2pixel(tend) + neededpixel1
				if t0 == tend:
					this_r = min(this_l + neededpixel0 + neededpixel1, tm.time2pixel(tend, 'right'), this_l + this_w)
				if not self.HORIZONTAL:
					this_r = min(tm.time2pixel(tend, 'right'), my_r)
				max_r = min(this_r, my_r)
			else:
				this_r = this_l + this_w + freewidth_per_child
				if not self.HORIZONTAL or chindex == len(self.children)-1:
					# The last child is extended the whole way to the end
					this_r = max_r = my_r
				else:
					max_r = my_r
					for i in range(chindex+1, len(self.children)):
						max_r = max_r - self.children[i].get_minsize()[0] - GAPSIZE
			if this_r > max_r:
				this_r = max_r
			if this_l > this_r:
				this_l = this_r
			medianode.moveto((this_l,this_t,this_r,this_b))
			medianode.recalc(tm, bwstrip)
			if self.HORIZONTAL:
				this_l = this_r + GAPSIZE
			else:
				this_t = this_b + GAPSIZE

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
		willplay = not self.mother.showplayability or self.node.WillPlay()
		if willplay:
			color = self.PLAYCOLOR
		else:
			color = self.NOPLAYCOLOR
		displist.drawfbox(color, self.get_box())

		if self.channelbox is not None and not self.iscollapsed():
			self.channelbox.draw(displist)

		# Uncomment to redraw pushback bars.
		#for i in self.children:
		#	if isinstance(i, MediaWidget) and i.pushbackbar:
		#		i.pushbackbar.draw(displist)

		if self.dropbox is not None and not self.iscollapsed():
			self.dropbox.draw(displist)

		l,t,r,b = self.pos_abs
		l = l + HEDGSIZE
		t = t + VEDGSIZE
		r = r - HEDGSIZE
		b = b - VEDGSIZE
		if self.iconbox is not None and self.iconbox.vertical:
			l = l + self.iconbox.get_minsize()[0]
			if self.name:
				 t = t + TITLESIZE
		else:
			t = t + TITLESIZE
		if self.timeline is not None:
			if TIMELINE_AT_TOP:
				t = t + self.timeline.get_minsize()[1]
			else:
				b = b - self.timeline.get_minsize()[1]
		if self.bwstrip is not None:
			if TIMELINE_AT_TOP:
				t = t + self.bwstrip.get_minsize()[1]
			else:
				b = b - self.bwstrip.get_minsize()[1]
		if self.iscollapsed():
			children = self.node.GetChildren()
			icon = self.node.GetAttrDef('thumbnail_icon', None)
			if icon is not None:
				icon = self.node.context.findurl(icon)
				try:
					icon = MMurl.urlretrieve(icon)[0]
				except:
					icon = None
				self.do_draw_image(icon, self.name, (l,t,r-l,b-t), displist)
##			elif self.DRAWCOLLAPSEDMEDIACHILD and children and children[0].GetType() in MMTypes.mediatypes:
##				self.drawnodecontent(displist, (l,t,r-l,b-t), children[0])
			elif self.previewchild:
				self.drawnodecontent(displist, (l,t,r-l,b-t), self.previewchild)
			elif self.HORIZONTAL:
				# draw vertical lines
				while l < r:
					displist.drawline(TEXTCOLOR, [(l, t),(l, b)])
					l = l + self.HSTEP
			else:
				# draw horizontal lines
				while t < b:
					displist.drawline(TEXTCOLOR, [(l, t),(r, t)])
					t = t + self.VSTEP
		else:
			if self.children:
				for i in self.children:
					i.draw(displist)
					l = i.pos_abs[2] + GAPSIZE
			else:
				self.draw_empty(displist, l, t, r, b)

		MMNodeWidget.draw(self, displist)

	def draw_empty(self, displist, l, t, r, b):
		icon = self.node.GetAttrDef('empty_icon', None)
		if icon is not None:
			icon = self.node.context.findurl(icon)
			try:
				icon = MMurl.urlretrieve(icon)[0]
			except:
				icon = None
		text = self.node.GetAttrDef('empty_text', self.name)
		color = self.node.GetAttrDef('empty_color', None)
		if color is not None:
			displist.drawfbox(color, (l,t,r-l,b-t))
		if icon or text:
			self.do_draw_image(icon, text, (l,t,r-l,b-t), displist, 1)

	def get_popupmenu(self):
		return self.mother.interior_popupmenu

#
# The HorizontalWidget is any sideways-drawn StructureObjWidget.
#
class HorizontalWidget(StructureObjWidget):
	VSTEP = 0
	HSTEP = 4
	HORIZONTAL = 1
	# All widgets drawn horizontally; e.g. sequences.

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

	def recalc_minsize(self, timemapper = None, ignore_time = 0):
		self.recalc_subicons()
		if self.iscollapsed():
			return MMNodeWidget.recalc_minsize(self, timemapper, ignore_time)

		if not self.children and self.channelbox is None:
			return MMNodeWidget.recalc_minsize(self, timemapper, ignore_time)

		timemapper = self.init_timemapper(timemapper, ignore_time)

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
			w,h = i.recalc_minsize(tm, ignore_time)
			if h > mh: mh=h
			mw = mw + w + pushover
		if timemapper is not None and tottime > 0:
			# reserve space for delays between nodes in addition to the nodes themselves
			t0, t1, t2, download, begindelay = self.GetTimes('virtual')
			mw = mw + int(mw * delays / float(tottime) + .5)
		mw = mw + GAPSIZE*(len(self.children)-1) + 2*HEDGSIZE

		if self.dropbox is not None:
			dbxsize, dbysize = self.dropbox.recalc_minsize()
			mw = mw + dbxsize + GAPSIZE
			if dbysize > mh:
				mh = dbysize

		mh = mh + 2*VEDGSIZE
		if self.timeline is not None:
			w, h = self.timeline.recalc_minsize()
			if w > mw:
				mw = w
			mh = mh + h
		if self.bwstrip is not None:
			w, h = self.bwstrip.recalc_minsize(self.node, timemapper)
			if w > mw:
				mw = w
			mh = mh + h
		if self.iconbox is not None and self.iconbox.vertical:
			mw = mw + self.iconbox.get_minsize()[0]
			if self.name:
				mh = mh + TITLESIZE
		else:
			mh = mh + TITLESIZE
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
		if self.timemapper is None:
			maxneededpixel0 = HEDGSIZE
		else:
			maxneededpixel0 = 0
		if self.iconbox is not None and self.iconbox.vertical and self.timemapper is None:
			maxneededpixel0 = maxneededpixel0 + self.iconbox.get_minsize()[0]
		maxneededpixel1 = HEDGSIZE
		if self.channelbox is not None:
			mw, mh = self.channelbox.get_minsize()
			maxneededpixel0 = maxneededpixel0 + mw + GAPSIZE
		if self.dropbox is not None:
			mw, mh = self.dropbox.get_minsize()
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
	VSTEP = 4
	HSTEP = 0
	HORIZONTAL = 0

	# Any node which is drawn vertically

	def recalc_minsize(self, timemapper = None, ignore_time = 0):
		self.recalc_subicons()
		if not self.children or self.iscollapsed():
			return MMNodeWidget.recalc_minsize(self, timemapper, ignore_time)

		timemapper = self.init_timemapper(timemapper, ignore_time)

		mw=0
		mh=0

		if self.timeline is not None:
			w, h = self.timeline.recalc_minsize()
			if w > mw:
				mw = w
			mh = mh + h
		if self.bwstrip is not None:
			w, h = self.bwstrip.recalc_minsize(self.node, timemapper)
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
			w,h = i.recalc_minsize(tm, ignore_time)
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

		if self.dropbox is not None:
			dbxsize, dbysize = self.dropbox.recalc_minsize()
			mh = mh + dbysize + GAPSIZE
			if dbxsize > mw:
				mw = dbxsize

		if self.iconbox is not None and self.iconbox.vertical:
			mw = mw + self.iconbox.get_minsize()[0]
			if self.name:
				mh = mh + TITLESIZE
		else:
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

	def addcollisions(self, mastert0, mastertend, timemapper, mytimes = None):
		if not self.children or self.iscollapsed() or not self.node.WillPlay():
			return MMNodeWidget.addcollisions(self, mastert0, mastertend, timemapper, mytimes)

		self.childrentimes = []
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
			self.childrentimes.append(chtimes + (neededpixel0, neededpixel1))
			if neededpixel0 > maxneededpixel0:
				maxneededpixel0 = neededpixel0
			if neededpixel1 > maxneededpixel1:
				maxneededpixel1 = neededpixel1
		if self.timemapper is None:
			maxneededpixel0 = maxneededpixel0 + HEDGSIZE
		if self.iconbox is not None and self.iconbox.vertical and self.timemapper is None:
			maxneededpixel0 = maxneededpixel0 + self.iconbox.get_minsize()[0]
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
	PLAYCOLOR = SEQCOLOR
	NOPLAYCOLOR = SEQCOLOR_NOPLAY

	def __init__(self, node, mother, parent):
		HorizontalWidget.__init__(self, node, mother, parent)
		if mother.usetimestripview and \
		   not MMAttrdefs.getattr(node, 'project_readonly') and \
		   seld.dropbox is None:
			self.dropbox = DropBoxWidget(self, mother)

#
# The UnseenVerticalWidget is only ever a single top-level widget
#
class UnseenVerticalWidget(StructureObjWidget):
	# The top level par that doesn't get drawn.
	HAS_COLLAPSE_BUTTON = 0

	def recalc_minsize(self, timemapper = None, ignore_time = 0):
		if not self.children or self.iscollapsed():
			return MMNodeWidget.recalc_minsize(self, timemapper, ignore_time)

		timemapper = self.init_timemapper(timemapper, ignore_time)

		minwidth, minheight = self.calculate_minsize(timemapper)

		mw=0
		mh=0

		for i in self.children:
			w,h = i.recalc_minsize(timemapper, ignore_time)
			if w > mw: mw=w
			mh=mh+h
		if self.timeline is not None:
			w, h = self.timeline.recalc_minsize()
			if w > mw:
				mw = w
			mh = mh + h
		if self.bwstrip is not None:
			w, h = self.bwstrip.recalc_minsize(self.node, timemapper)
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

	def recalc(self, timemapper = None, bwstrip = None):
		# Recalculate the position of all the contained boxes.
		# Algorithm: Iterate through each of the MMNodes children's views and find their minsizes.
		# Apportion free space equally, based on the size of self.
		# TODO: This does not test for maxheight()
		if self.timemapper is not None:
			timemapper = self.timemapper
			timemapper.setoffset(self.pos_abs[0], self.pos_abs[2] - self.pos_abs[0])
			
		if self.bwstrip:
			bwstrip = self.bwstrip
			
		if not self.node.WillPlay():
			timemapper = None

		if self.iscollapsed():
			StructureObjWidget.recalc(self, timemapper, bwstrip)
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

		if self.bwstrip and not TIMELINE_AT_TOP:
			bw_w, bw_h = self.bwstrip.get_minsize()
			t = t + bw_h
			free_height = free_height - bw_h

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
			medianode.recalc(timemapper, bwstrip)
			t = b #  + self.get_rely(GAPSIZE)
		StructureObjWidget.recalc(self, timemapper, bwstrip)

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
	PLAYCOLOR = PARCOLOR
	NOPLAYCOLOR = PARCOLOR_NOPLAY
	DRAWCOLLAPSEDMEDIACHILD = 1

# and so forth..
class ExclWidget(SeqWidget):
	# Exclusive node.
	PLAYCOLOR = EXCLCOLOR
	NOPLAYCOLOR = EXCLCOLOR_NOPLAY


class PrioWidget(SeqWidget):
	PLAYCOLOR = PRIOCOLOR
	NOPLAYCOLOR = PRIOCOLOR_NOPLAY


class SwitchWidget(VerticalWidget):
	PLAYCOLOR = ALTCOLOR
	NOPLAYCOLOR = ALTCOLOR_NOPLAY


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

	def init_timemapper(self, timemapper, ignore_time = 0):
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


	def recalc(self, timemapper = None, bwstrip = None):
		self.need_draghandles = None
		if self.timemapper is not None:
			timemapper = self.timemapper
			timemapper.setoffset(self.pos_abs[0], self.pos_abs[2] - self.pos_abs[0])
		if self.bwstrip:
			bwstrip = self.bwstrip
			
##		if bwstrip:
##			bwstrip.addbandwidthinfo(self.node, self.node.get_bandwidthboxes(), self.selected, timemapper)
			
		if not self.node.WillPlay():
			timemapper = None
		self.__timemapper = timemapper
		l,t,r,b = self.pos_abs

		self.iconbox.moveto((l+HEDGSIZE, t+VEDGSIZE, 0, 0))
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

		if self.iconbox.vertical:
			l = l + self.iconbox.get_minsize()[0]
		else:
			t = t + TITLESIZE

		# Add the timeline and the bandwidth strip
		if self.timeline is not None:
			tl_w, tl_h = self.timeline.get_minsize()
			if TIMELINE_AT_TOP:
				self.timeline.moveto((l, t, r, t+tl_h), timemapper)
				t = t + tl_h
			else:
				self.timeline.moveto((l, b-tl_h, r, b), timemapper)
				b = b - tl_h
		if self.bwstrip is not None:
			bw_w, bw_h = self.timeline.get_minsize()
			if TIMELINE_AT_TOP:
				self.bwstrip.moveto((l, t, r, t+bw_h), self.node, timemapper)
				t = t + bw_h
			else:
				self.bwstrip.moveto((l, b-bw_h, r, b), self.node, timemapper)
				b = b - bw_h
		# XXXX Support for greyout widget not added, because timelines
		# on media nodes isn't used anyway nowadays.
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
##		self.need_draghandles = x,x+dw,y+h/2
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
		if self.iconbox is not None and self.iconbox.vertical:
			l = l + self.iconbox.get_minsize()[0]
			t = t + VEDGSIZE
		else:
			t = t + TITLESIZE
		l = l + HEDGSIZE
		b = b - VEDGSIZE
		r = r - HEDGSIZE

		# Add the timeline
		if self.timeline is not None:
			if TIMELINE_AT_TOP:
				t = self.timeline.pos_abs[3]
			else:
				b = self.timeline.pos_abs[1]
		# XXXX Should we cater for a bandwidth strip here too?
		if self.need_draghandles is not None:
			b = b - 8	# leave space for draghandles
		# Draw the image.
		self.drawnodecontent(displist, (l,t,r-l,b-t), self.node)
		MMNodeWidget.draw(self, displist)

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

	def get_popupmenu(self):
		return self.mother.leaf_popupmenu


class CommentWidget(MMNodeWidget):
	# A view of an object which is a comment type.

	def recalc(self, timemapper = None, bwstrip = None):
		l,t,r,b = self.pos_abs
##		if self.iconbox is not None:
##			self.iconbox.moveto((l+HEDGSIZE, t+VEDGSIZE, 0, 0))

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
		x = x + HEDGSIZE
		w = w - 2*HEDGSIZE
		y = y + VEDGSIZE
		h = h - 2*VEDGSIZE

		ntype = self.node.GetType()

		# Draw the image.
		image_filename = os.path.join(self.mother.datadir, 'comment.tiff')
		if w > 0 and h > 0:
			self.do_draw_image(image_filename, self.name, (x,y,w,h), displist)

		if self.iconbox is not None:
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
			if self.iconbox is not None and self.iconbox.is_hit(pos):
				return self.iconbox.get_clicked_obj_at(pos)
			else:
				return self
		else:
			return None


class ForeignWidget(HorizontalWidget):
	# Any foreign node.
	PLAYCOLOR = FOREIGNCOLOR
	NOPLAYCOLOR = FOREIGNCOLOR_NOPLAY


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

class GreyoutWidget(MMWidgetDecoration):
	# A widget greying out timeline/bandwidth areas that
	# are meaningless
	def __init__(self, mmwidget, mother):
		MMWidgetDecoration.__init__(self, mmwidget, mother)
		self.greyout_ranges = []

	def recalc_minsize(self):
		return 0, 0

	def moveto(self, coords, timemapper):
		MMWidgetDecoration.moveto(self, coords)
		self.__timemapper = timemapper
		self.greyout_ranges = []
		self._recalc_ranges()

	def _recalc_ranges(self):
		t0, t1, t2, download, begindelay = self.get_mmwidget().GetTimes('virtual')
		timemapper = self.__timemapper
		for time, left, right in timemapper.gettimesegments(range=(t0, t2)):
			if left != right:
				stalltime, stalltype = timemapper.getstall(time)
				if not stalltime:
					self.greyout_ranges.append((left+1, right))

	def draw(self, displist):
		x, y, w, h = self.get_box()
		for left, right in self.greyout_ranges:
			displist.drawstipplebox(self.mmwidget.PLAYCOLOR, (left, y, right-left+1, h))

	def redraw_partial(self, displist, left, right):
		x, y, w, h = self.get_box()
		for rl, rr in self.greyout_ranges:
			if left <= rr and right >= rl:
				displist.drawstipplebox(self.mmwidget.PLAYCOLOR, (rl, y, rr-rl+1, h))
			if right < rl:
				break

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
		self.__timemapper = timemapper
		x, y, w, h = self.get_box()
		if self.minwidth:
			# remember updated minimum width
			self.minwidth = w
		if TIMELINE_AT_TOP:
			line_y = y + (h/2)
			tick_top = line_y
			tick_bot = y+h-(h/3)
			longtick_top = line_y - 3
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
			longtick_bot = line_y + 3
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
		timemapper = self.__timemapper
		t0, t1, t2, download, begindelay = self.get_mmwidget().GetTimes('virtual')
		min = timemapper.time2pixel(t0, 'left')
		max = timemapper.time2pixel(t2, 'right')
		displist.drawline(TEXTCOLOR, [(min, line_y), (max, line_y)])
		length = max - min	# length of real timeline
		displist.usefont(f_timescale)
		for time, left, right in timemapper.gettimesegments(range=(t0, t2)):
			if left != right:
				stalltime, stalltype = timemapper.getstall(time)
				if stalltime:
					if stalltype == 'preroll':
						color = BWPREROLLCOLOR
					elif stalltype == 'stall?':
						color = BWMAYSTALLCOLOR
					else:
						color = BWSTALLCOLOR
					displist.fgcolor(color)
					label = '%ds %s'%(stalltime, stalltype)
					lw = displist.strsizePXL(label)[0]
					if lw > right-left:
						# It doesn't fit. Try something smaller
						label = '%ds'%stalltime
						lw = displist.strsizePXL(label)[0]
					if lw < right-left:
						displist.centerstring(left, longtick_top, right, longtick_bot, label)
					displist.drawline(color, [(left, line_y), (right, line_y)])
				length = length - (right - left)
		displist.fgcolor(TEXTCOLOR)
		if t0 >= t2:
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
##			tick_x = timemapper.interptime2pixel(time)
			tick_x2 = timemapper.interptime2pixel(time, align='right')
##			tick_x_mid = (tick_x + tick_x2) / 2
			tick_x = tick_x_mid = tick_x2
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
##			if tick_x != tick_x2:
##				displist.drawline(COLCOLOR, [(tick_x2, cur_tick_top), (tick_x2, cur_tick_bot)])
# to also draw a horizontal line between the tips of the two ticks, use the following instead
##				displist.drawline(COLCOLOR, [(tick_x, cur_tick_top), (tick_x2, cur_tick_top), (tick_x2, cur_tick_bot), (tick_x, cur_tick_bot)])
		displist.fgcolor((255, 0, 0))
	draw_selected = draw

class BandWidthWidget(MMWidgetDecoration):
	# A widget showing the timeline
	def __init__(self, mmwidget, mother):
		MMWidgetDecoration.__init__(self, mmwidget, mother)
		import settings
		self.maxbandwidth = settings.get('system_bitrate')

	def destroy(self):
		self.okboxes = None
		self.notokboxes = None
		self.okfocusboxes = None
		self.notokfocusboxes = None
		MMWidgetDecoration.destroy(self)

	def recalc_minsize(self, node, timemapper):
		import settings
		self.maxbandwidth = settings.get('system_bitrate')
		minheight = 2*TITLESIZE
		self.boxsize = 0, minheight
		return self.boxsize

	def moveto(self, coords, node, timemapper):
		MMWidgetDecoration.moveto(self, coords)
		self.okboxes = []
		self.notokboxes = []
		self.maybeokboxes = []
		self.okfocusboxes = []
		self.notokfocusboxes = []
		self.maybeokfocusboxes = []
		self._addallbandwidthinfo(node, timemapper)

	def _addallbandwidthinfo(self, node, timemapper):
		self._addbandwidthinfo(node, timemapper)
		for ch in node.GetChildren():
			self._addallbandwidthinfo(ch, timemapper)

	def _addbandwidthinfo(self, node, timemapper):
		# For now we ignore node
		boxes = node.get_bandwidthboxes()
		if not boxes:
			return
		my_x, my_y, my_w, my_h = self.get_box()
		my_y = my_y + 3
		my_h = my_h - 6
		my_b = my_y + my_h
		bwfactor = float(my_h)/float(self.maxbandwidth)
		for box in boxes:
			t0, t1, bwlo, bwhi, status = box
			x0 = timemapper.interptime2pixel(t0, align='right')
			if t1 > 0:
				x1 = timemapper.interptime2pixel(t1, align='left')
			else:
				x1 = timemapper.interptime2pixel(t1, align='right')
			y0 = my_b - int(bwfactor*bwhi)
			y1 = my_b - int(bwfactor*bwlo)
			box = (x0, y0, x1-x0, y1-y0)
			if status == 'preroll':
				self.maybeokboxes.append((node, box))
			elif status:
				self.notokboxes.append((node, box))
			else:
				self.okboxes.append((node, box))

##	def moveto(self, coords):
##		return # XXXX
##		MMWidgetDecoration.moveto(self, coords)
##		self.__timemapper = timemapper
##		x, y, w, h = self.get_box()
##		if self.minwidth:
##			# remember updated minimum width
##			self.minwidth = w
##		if TIMELINE_AT_TOP:
##			line_y = y + (h/2)
##			tick_top = line_y
##			tick_bot = y+h-(h/3)
##			longtick_top = line_y
##			longtick_bot = y + h - (h/6)
##			midtick_top = line_y
##			midtick_bot = (tick_bot+longtick_bot)/2
##			endtick_top = line_y - (h/3)
##			endtick_bot = longtick_bot
##			label_top = y
##			label_bot = y + (h/2)
##		else:
##			line_y = y + (h/2)
##			tick_top = y + (h/3)
##			tick_bot = line_y
##			longtick_top = y + (h/6)
##			longtick_bot = line_y
##			midtick_top = (tick_top+longtick_top)/2
##			midtick_bot = line_y
##			endtick_top = longtick_top
##			endtick_bot = line_y + (h/6)
##			label_top = y + (h/2)
##			label_bot = y + h
##		self.params = line_y, tick_top, tick_bot, longtick_top, longtick_bot, midtick_top, midtick_bot, endtick_top, endtick_bot, label_top, label_bot

	def draw(self, displist):
		x, y, w, h = self.get_box()
		y = y + 3
		h = h - 6
		displist.fgcolor(TEXTCOLOR)
		displist.drawbox((x-1, y-1, w+2, h+2))
		displist.drawfbox(BANDWIDTH_FREE_COLOR, (x, y, w, h))
		self._drawboxes(displist, BANDWIDTH_OK_COLOR, self.okboxes)
		self._drawboxes(displist, BANDWIDTH_NOTOK_COLOR, self.notokboxes)
		self._drawboxes(displist, BANDWIDTH_MAYBEOK_COLOR, self.maybeokboxes)
		self._drawboxes(displist, BANDWIDTH_OKFOCUS_COLOR, self.okfocusboxes)
		self._drawboxes(displist, BANDWIDTH_NOTOKFOCUS_COLOR, self.notokfocusboxes)
		self._drawboxes(displist, BANDWIDTH_MAYBEOKFOCUS_COLOR, self.maybeokfocusboxes)

	def _drawboxes(self, displist, color, boxes):
		for node, box in boxes:
			displist.drawfbox(color, box)
			# This draws a line around the box. I'm not
			# sure I like it.
			x, y, w, h = box
			if w > 1 and h > 1:
				displist.drawbox((x, y, w+1, h+1))

	def focuschanged(self, displist, focusnodes):
		# This is gross. This method is called by HierarchyView
		# to let us redraw. It should be done distributed.
		took = []
		tonotok = []
		tomaybeok = []
		tookfocus = []
		tonotokfocus = []
		tomaybeokfocus = []
		redrawareas = []
		for n, box in self.okboxes:
			if n in focusnodes:
				tookfocus.append((n, box))
				redrawareas.append((box[0], box[0]+box[2]))
		for nb in tookfocus:
			self.okboxes.remove(nb)
		for n, box in self.notokboxes:
			if n in focusnodes:
				tonotokfocus.append((n, box))
				redrawareas.append((box[0], box[0]+box[2]))
		for nb in tonotokfocus:
			self.notokboxes.remove(nb)
		for n, box in self.maybeokboxes:
			if n in focusnodes:
				tomaybeokfocus.append((n, box))
				redrawareas.append((box[0], box[0]+box[2]))
		for nb in tomaybeokfocus:
			self.maybeokboxes.remove(nb)
		for n, box in self.okfocusboxes:
			if not n in focusnodes:
				took.append((n, box))
				redrawareas.append((box[0], box[0]+box[2]))
		for nb in took:
			self.okfocusboxes.remove(nb)
		for n, box in self.notokfocusboxes:
			if not n in focusnodes:
				tonotok.append((n, box))
				redrawareas.append((box[0], box[0]+box[2]))
		for nb in tonotok:
			self.notokfocusboxes.remove(nb)
		for n, box in self.maybeokfocusboxes:
			if not n in focusnodes:
				tomaybeok.append((n, box))
				redrawareas.append((box[0], box[0]+box[2]))
		for nb in tomaybeok:
			self.maybeokfocusboxes.remove(nb)
		for nb in took:
			self.okboxes.append(nb)
		for nb in tonotok:
			self.notokboxes.append(nb)
		for nb in tomaybeok:
			self.maybeokboxes.append(nb)
		for nb in tookfocus:
			self.okfocusboxes.append(nb)
		for nb in tonotokfocus:
			self.notokfocusboxes.append(nb)
		for nb in tomaybeokfocus:
			self.maybeokfocusboxes.append(nb)
		displist.fgcolor(TEXTCOLOR)
		self._drawboxes(displist, BANDWIDTH_OK_COLOR, took)
		self._drawboxes(displist, BANDWIDTH_NOTOK_COLOR, tonotok)
		self._drawboxes(displist, BANDWIDTH_MAYBEOK_COLOR, tomaybeok)
		self._drawboxes(displist, BANDWIDTH_OKFOCUS_COLOR, tookfocus)
		self._drawboxes(displist, BANDWIDTH_NOTOKFOCUS_COLOR, tonotokfocus)
		self._drawboxes(displist, BANDWIDTH_MAYBEOKFOCUS_COLOR, tomaybeokfocus)
		if self.mmwidget.greyout:
			for left, right in redrawareas:
				self.mmwidget.greyout.redraw_partial(displist, left, right)

# A box with icons in it.
# Comes before the node's name.
class IconBox(MMWidgetDecoration):
	def __init__(self, mmwidget, mother, vertical = 1):
		MMWidgetDecoration.__init__(self, mmwidget, mother)
		self._iconlist = []
		self.vertical = vertical

	def destroy(self):
		for icon in self._iconlist:
			icon.destroy()
		self._iconlist = []
		MMWidgetDecoration.destroy(self)

	iconorder = []
	for ntype in ('par', 'seq', 'switch', 'prio', 'excl', ''):
		for coll in ('open', 'closed'):
			iconorder.append(ntype + coll)
	del ntype, coll
	iconorder = tuple(iconorder)

	def add_icon(self, iconname=None, callback=None, contextmenu=None, arrowto=None, arrowcolor=None):
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
			icon.add_arrow(arrowto, arrowcolor)
		i = 0
		for n in self.iconorder + \
			 ('idle', ArmStates.ARM_NONE, ArmStates.ARM_SCHEDULED,
			  ArmStates.ARM_ARMING, ArmStates.ARM_ARMED,
			  ArmStates.ARM_PLAYING, ArmStates.ARM_WAITSTOP,
			  'error',
			  'bandwidthgood', 'bandwidthbad',
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
		if self.vertical:
			self.boxsize = ICONXSIZE, len(self._iconlist) * ICONYSIZE
		else:
			self.boxsize = len(self._iconlist) * ICONXSIZE, ICONYSIZE
		return self.boxsize

	def get_clicked_obj_at(self, coords):
		x,y = coords
		return self.__get_icon_at_position(x,y)

	def is_hit(self, pos):
		l,t,a,b = self.pos_abs
		x,y = pos
		if self.vertical:
			return l < x < l+ICONXSIZE and t < y < t+(len(self._iconlist)*ICONYSIZE)
		else:
			return l < x < l+(len(self._iconlist)*ICONXSIZE) and t < y < t+ICONYSIZE

	def draw(self, displist):
		l,t,r,b = self.pos_abs
		for icon in self._iconlist:
			icon.moveto((l,t,l+ICONXSIZE,t+ICONYSIZE))
			icon.draw(displist)
			if self.vertical:
				t = t + ICONYSIZE
			else:
				l = l + ICONXSIZE

	draw_selected = draw

	def __get_icon_at_position(self, x, y):
		l,t,r,b = self.pos_abs
		if self.vertical:
			index = int((y-t)/ICONYSIZE)
		else:
			index = int((x-l)/ICONXSIZE)
		if 0 <= index < len(self._iconlist):
			return self._iconlist[index]

	def mouse0release(self, coords):
		x,y = coords
		l,t,r,b = self.pos_abs
		icon = self.__get_icon_at_position(x,y)
		if icon:
			icon.mouse0release(coords)
		else:
			return

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
		self.boxsize = ICONXSIZE, ICONYSIZE
		return self.boxsize

	def set_icon(self, iconname):
		self.icon = iconname

	def set_properties(self, selectable=1, callbackable=1, issrc=0, initattr=None):
		self.selectable = selectable
		self.callbackable = callbackable
		self.issrc = issrc
		self.initattr = initattr

	def select(self):
		if self.selectable:
			MMWidgetDecoration.select(self)

	def unselect(self):
		if self.selectable:
			MMWidgetDecoration.unselect(self)

	def set_callback(self, callback, args=()):
		self.callback = callback, args

	def mouse0release(self, coords):
		if self.callback is not None and self.icon:
			apply(apply, self.callback)

	def moveto(self, pos):
		l,t,r,b = pos
		MMWidgetDecoration.moveto(self, (l, t, l+ICONXSIZE, t+ICONYSIZE))

	def draw_selected(self, displist):
		if not self.selectable:
			self.draw(displist)
			return
##		displist.drawfbox((0,0,0),self.get_box())
		self.draw(displist)
		for arrow, color in self.arrowto:
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
			if self.issrc:
				self.mother.add_arrow(self, color, (xs,ys),(xd,yd))
			else:
				self.mother.add_arrow(self, color, (xd,yd),(xs,ys))

	def draw_unselected(self, displist):
		self.draw(displist)

	def draw(self, displist):
		if self.icon is not None:
			displist.drawicon(self.get_box(), self.icon)

	def set_contextmenu(self, foobar):
		self.contextmenu = foobar			# TODO.

	def get_contextmenu(self):
		return self.contextmenu

	def add_arrow(self, dest, color):
		# dest can be any MMWidget.
		if dest and dest not in self.arrowto:
			self.arrowto.append((dest, color))

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
##		self.issrc = 1
##		self.contextmenu = None

##class EventIcon(Icon):
##	# Is the actual event.
##	pass




##############################################################################
			# Crap at the end of the file.

class TimeStripSeqWidget(SeqWidget):
	# A sequence that has a channel widget at the start of it.
	# This only exists at the second level from the root, assuming the root is a
	# par.
	# Wow. I like this sort of code. If only the rest of the classes were this easy. -mjvdg
	HAS_COLLAPSE_BUTTON = 0

	def __init__(self, node, mother, parent):
		SeqWidget.__init__(self, node, mother, parent)
		self.channelbox = ChannelBoxWidget(self, node, mother)

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

class EmptyWidget(ImageBoxWidget):
	def recalc_minsize(self):
		node = self.mmwidget.node
		icon = node.GetAttrDef('empty_icon', None)
		imxsize = imysize = 0
		if icon and not MMAttrdefs.getattr(node, 'thumbnail_scale'):
			import Sizes
			icon = node.context.findurl(icon)
			try:
				icon = MMurl.urlretrieve(icon)[0]
				imxsize, imysize = Sizes.GetImageSize(icon)
			except:
				pass
		self.__image_size = imxsize, imysize

		text = node.GetAttrDef('empty_text', None)
		if text:
			txxsize, txysize = f_title.strsizePXL(text)
		else:
			txxsize = txysize = 0
		if imxsize == imysize == txxsize == txysize == 0:
			self.boxsize = 0, 0
		else:
			self.boxsize = imxsize + 2 + txxsize, max(imysize, txysize)
		return self.boxsize

	def draw(self, displist):
		if self.boxsize == (0, 0):
			# nothing to draw
			return

		l,t,r,b = self.pos_abs
		node = self.mmwidget.node
		icon = node.GetAttrDef('empty_icon', None)
		if icon is not None:
			icon = node.context.findurl(icon)
			try:
				icon = MMurl.urlretrieve(icon)[0]
			except:
				icon = None
		text = node.GetAttrDef('empty_text', self.name)
		color = node.GetAttrDef('empty_color', None)
		if color is not None:
			displist.drawfbox(color, (l,t,r-l,b-t))
		if icon or text:
			self.mmwidget.do_draw_image(icon, text, (l,t,r-l,b-t), displist, 1, self.__image_size)

class DropIconWidget(ImageBoxWidget):
	def recalc_minsize(self):
		node = self.mmwidget.node
		import Sizes
		icon = node.GetAttrDef('dropicon', None)
		icon = node.context.findurl(icon)
		try:
			icon = MMurl.urlretrieve(icon)[0]
			imxsize, imysize = Sizes.GetImageSize(icon)
		except:
			imxsize = imysize = 0
##		if self.mmwidget.HORIZONTAL:
##			imysize = 1
##		else:
##			imxsize = 1
		self.boxsize = imxsize, imysize
		return self.boxsize

	def draw(self, displist):
		if self.boxsize == (0, 0):
			return
		x,y,w,h = self.get_box()
		l,t,r,b = self.pos_abs
		node = self.mmwidget.node
		icon = node.GetAttrDef('dropicon', None)
		icon = node.context.findurl(icon)
		try:
			icon = MMurl.urlretrieve(icon)[0]
		except:
			return
		while x < r and y < b:
			try:
				box = displist.display_image_from_file(icon, center = 0, fit = 'hidden', coordinates = (x,y,w,h), clip = (x,y,w,h))
			except:
				return
			if self.mmwidget.HORIZONTAL:
				y = y + box[3]
				h = h - box[3]
			else:
				x = x + box[2]
				w = w - box[2]

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
