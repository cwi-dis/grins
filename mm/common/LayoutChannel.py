__version__ = "$Id$"

from Channel import *
#
# This rather boring channel is used for laying-out other channels
#
class LayoutChannel(ChannelWindow):

	def __init__(self, name, attrdict, scheduler, ui):
		ChannelWindow.__init__(self, name, attrdict, scheduler, ui)
		self.is_layout_channel = 1
		self._activeMediaNumber = 0
		self._wingeomInPixel = None
		
		if settings.activeFullSmilCss:
			parentChannel = self._get_parent_channel()
			if parentChannel == None:
				self.idCssNode = self.cssResolver.newRootNode()
			else:
				self.idCssNode = self.cssResolver.newRegion()

	# for now
	# get the parent window geometry in pixel
	# need for sub-region, registration point,...
	# WARNING: if the size of channel is dynamicly modify (for example from animation),
	# we have to invalidate the current value in self._wingeomInPixel
	def _getWingeomInPixel(self):
		parentChannel = self._get_parent_channel()

		if parentChannel == None:
			# top window 
			size = self._attrdict.get('winsize', (50, 50))
			w,h = size
			return 0,0,w,h

		units = self._attrdict['units']
		if units == windowinterface.UNIT_PXL:
			# The size in smil source is specified in pixel, we don't need to 
			# convert it and return directly it
			return self._attrdict['base_winoff']
		if self._wingeomInPixel != None:
			# The size is expressed in pourcent in smil source document, but
			# the size in pixel is already pre-calculate.
			return self._wingeomInPixel

		# The size is expressed in pourcent in smil source document, we don't determinate 
		# yet its size in pixel. For this, we need to know the parent size in pixel
		
		parentChannel = self._get_parent_channel()
		parentGeomInPixel = parentChannel._getWingeomInPixel()
		
		x,y,w,h = self._attrdict['base_winoff']
		px,py,pw,ph = parentGeomInPixel
		
		# we save the current size in pixel for the next request
		self._wingeomInPixel = x*pw, y*ph, w*pw, h*ph
		
		return self._wingeomInPixel

	def do_arm(self, node, same=0):
		print 'LayoutChannel: cannot play nodes on a layout channel'
		return 1

	def create_window(self, pchan, pgeom, units = None):
##		menu = []
		bgcolor = self._attrdict.get('bgcolor')
		if pchan:
##			if hasattr(self._player, 'editmgr'):
##				menu.append(('', 'raise', (self.popup, ())))
##				menu.append(('', 'lower', (self.popdown, ())))
##				menu.append(None)
##				menu.append(('', 'select in timeline view',
##					     (self.focuscall, ())))
##				menu.append(None)
##				menu.append(('', 'highlight',
##					     (self.highlight, ())))
##				menu.append(('', 'unhighlight',
##					     (self.unhighlight, ())))
			transparent = self._attrdict.get('transparent', 0)
			# print 'layout channel transparent : ',self,':',transparent
			# print 'layout channel bgcolor : ',self,':',bgcolor
			self._curvals['transparent'] = (transparent, 0)
			z = self._attrdict.get('z', 0)
			self._curvals['z'] = (z, 0)
			if self.want_default_colormap:
				self.window = pchan.window.newcmwindow(pgeom,
						transparent = transparent,
						z = z,
						type_channel = self._window_type,
						units = units,
						bgcolor = bgcolor)
			else:
				self.window = pchan.window.newwindow(pgeom,
						transparent = transparent,
						z = z,
						type_channel = self._window_type,
						units = units,
						bgcolor = bgcolor)
##			if hasattr(self._player, 'editmgr'):
##				menu.append(None)
##				menu.append(('', 'resize',
##					     (self.resize_window, (pchan,))))
		else:
			# no basewindow, create a top-level window
			adornments = self._player.get_adornments(self)
			if self._player._exporter:
				adornments['exporting'] = 1
			units = self._attrdict.get('units',
						   windowinterface.UNIT_MM)
			width, height = self._attrdict.get('winsize', (50, 50))
			
			if settings.activeFullSmilCss:
				self.cssResolver.setRootSize(self.idCssNode, width,height)
				units = windowinterface.UNIT_PXL
				
			self._curvals['winsize'] = ((width, height), (50,50))
			x, y = self._attrdict.get('winpos', (None, None))
			if self.want_default_colormap:
				self.window = windowinterface.newcmwindow(x, y,
					width, height, self._name,
					visible_channel = self._visible,
					type_channel = self._window_type,
					units = units, adornments = adornments,
					commandlist = self.commandlist,
					bgcolor = bgcolor)
			else:
				self.window = windowinterface.newwindow(x, y,
					width, height, self._name,
					visible_channel = self._visible,
					type_channel = self._window_type,
					units = units, adornments = adornments,
					commandlist = self.commandlist,
					bgcolor = bgcolor)
			if self._player._exporter:
				self._player._exporter.createWriter(self.window)
			self.event((self._attrdict, 'viewportOpenEvent'))
##			if hasattr(self._player, 'editmgr'):
##				menu.append(('', 'select in timeline view',
##					     (self.focuscall, ())))
 		if self._attrdict.has_key('fgcolor'):
			self.window.fgcolor(self._attrdict['fgcolor'])
		self._curvals['bgcolor'] = self._attrdict.get('bgcolor'), None
		self._curvals['fgcolor'] = self._attrdict.get('fgcolor'), None
		self.window.register(WMEVENTS.ResizeWindow, self.resize, None)
		self.window.register(WMEVENTS.Mouse0Press, self.mousepress, None)
		self.window.register(WMEVENTS.Mouse0Release, self.mouserelease,
				     None)
		self.window.register(WMEVENTS.KeyboardInput, self.keyinput, None)
##		if menu:
##			self.window.create_menu(menu, title = self._name)

	# notes:
	# unlike base ChannelWindow class, we can have pchan = None. It means that
	# it's the main window. In this case, we don't need to determinate self._wingeom because 
	# it not used in create_window. It's not a good design, but for now it works.
	def do_show(self, pchan):
		if debug:
			print 'ChannelLayout.do_show('+`self`+')'
	
		if pchan:
			# parent is not None, so it's not the main window
			if settings.activeFullSmilCss:
				# we create dynamicly a new css node instance
				self.cssResolver.setRawAttrPos(self.idCssNode,
									   self._attrdict.get('left'), self._attrdict.get('width'),
									   self._attrdict.get('right'), self._attrdict.get('top'),
									   self._attrdict.get('height'), self._attrdict.get('bottom'))
				self.cssResolver.link(self.idCssNode, pchan.idCssNode)
				self._wingeom = pgeom = self.cssResolver.getPxGeom(self.idCssNode)
			else:
				if self._attrdict.has_key('base_winoff'):
					self._wingeom = pgeom = self._attrdict['base_winoff']
				elif self._player.playing:
					windowinterface.showmessage(
						'No geometry for subchannel %s known' % self._name,
						mtype = 'error', grab = 1)
					pchan._subchannels.remove(self)
					pchan = None
				else:
##				pchan.window.create_box(
##					'Draw a subwindow for %s in %s' %
##						(self._name, pchan._name),
##					self._box_callback,
##					units = units)
##				return None
					#
					# Window without position/size. Set to whole parent, and remember
					# in the attributes. (Note: technically wrong, changing the attrdict
					# without using the edit mgr).
					# Or should I skip the curvals stuff below, to do this correctly?
					#
					self._wingeom = pgeom = (0.0, 0.0, 1.0, 1.0)
					units = windowinterface.UNIT_SCREEN
					self._attrdict['base_winoff'] = pgeom
					self._attrdict['units'] = units
			self._curvals['base_winoff'] = pgeom, None
		
		if settings.activeFullSmilCss:
			units = windowinterface.UNIT_PXL
		else:
			units = self._attrdict.get('units', windowinterface.UNIT_SCREEN)
		self.create_window(pchan, self._wingeom, units)
		
		return 1

	def do_hide(self):
		ChannelWindow.do_hide(self)
		if settings.activeFullSmilCss:
			self.cssResolver.unlink(self.idCssNode)			
				
	def play(self, node):
		print "can't play LayoutChannel"

	# A channel pass active (when one more media play inside).
	# We have to update the visibility of all channels 
	def childToActiveState(self):
		ch = self
		while ch != None:
			ch._activeMediaNumber = ch._activeMediaNumber+1
			ch.show(1)
			ch = ch._get_parent_channel()
			
	# A channel pass inactive (when one more media play inside).
	# We have to update the visibility of all channels 
	def childToInactiveState(self):
		ch = self
		while ch != None:
			ch._activeMediaNumber = ch._activeMediaNumber-1
			if ch._activeMediaNumber <= 0:
				ch.hide(0)
			ch = ch._get_parent_channel()
