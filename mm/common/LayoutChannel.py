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
                
	# for now
	# get the parent window geometry in pixel
	# need for sub-region, registration point,...
	def _getWingeomInPixel(self):
	        parentChannel = self._get_parent_channel()
	        # top window
	        if parentChannel == None:
	                size = self._attrdict.get('winsize', (50, 50))
	                w,h = size
	                return 0,0,w,h
	                
		units = self._attrdict['units']
		if units != windowinterface.UNIT_SCREEN:
			return self._attrdict['base_winoff']
		if self._wingeomInPixel != None:
			return self._wingeomInPixel
		
		parentChannel = self._get_parent_channel()
		parentGeomInPixel = parentChannel._getWingeomInPixel()
		
		x,y,w,h = self._attrdict['base_winoff']
		px,py,pw,ph = parentGeomInPixel
		
		self._wingeomInPixel = x*pw, y*ph, w*pw, h*ph
		
		return self._wingeomInPixel

	def do_arm(self, node, same=0):
		print 'LayoutChannel: cannot play nodes on a layout channel'
		return 1

	def create_window(self, pchan, pgeom, units = None):
##		menu = []
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
			self._curvals['transparent'] = (transparent, 0)
			z = self._attrdict.get('z', 0)
			self._curvals['z'] = (z, 0)
			if self.want_default_colormap:
				self.window = pchan.window.newcmwindow(pgeom,
						transparent = transparent,
						z = z,
						type_channel = self._window_type,
						units = units)
			else:
				self.window = pchan.window.newwindow(pgeom,
						transparent = transparent,
						z = z,
						type_channel = self._window_type,
						units = units)
##			if hasattr(self._player, 'editmgr'):
##				menu.append(None)
##				menu.append(('', 'resize',
##					     (self.resize_window, (pchan,))))
		else:
			# no basewindow, create a top-level window
			adornments = self._player.get_adornments(self)
			units = self._attrdict.get('units',
						   windowinterface.UNIT_MM)
			width, height = self._attrdict.get('winsize', (50, 50))
			self._curvals['winsize'] = ((width, height), (50,50))
			x, y = self._attrdict.get('winpos', (None, None))
			if self.want_default_colormap:
				self.window = windowinterface.newcmwindow(x, y,
					width, height, self._name,
					visible_channel = self._visible,
					type_channel = self._window_type,
					units = units, adornments = adornments,
					commandlist = self.commandlist)
			else:
				self.window = windowinterface.newwindow(x, y,
					width, height, self._name,
					visible_channel = self._visible,
					type_channel = self._window_type,
					units = units, adornments = adornments,
					commandlist = self.commandlist)
##			if hasattr(self._player, 'editmgr'):
##				menu.append(('', 'select in timeline view',
##					     (self.focuscall, ())))
		if self._attrdict.has_key('bgcolor'):
			self.window.bgcolor(self._attrdict['bgcolor'])
 		if self._attrdict.has_key('fgcolor'):
			self.window.fgcolor(self._attrdict['fgcolor'])
		self._curvals['bgcolor'] = self._attrdict.get('bgcolor'), None
		self._curvals['fgcolor'] = self._attrdict.get('fgcolor'), None
		self.window.register(WMEVENTS.ResizeWindow, self.resize, None)
		self.window.register(WMEVENTS.Mouse0Press, self.mousepress, None)
		self.window.register(WMEVENTS.Mouse0Release, self.mouserelease,
				     None)
##		if menu:
##			self.window.create_menu(menu, title = self._name)

	def do_show(self, pchan):
		if debug:
			print 'ChannelLayout.do_show('+`self`+')'
	
		# create a window for this channel
		pgeom = None
		units = self._attrdict.get('units',
					   windowinterface.UNIT_SCREEN)
		if pchan:
			#
			# Find the base window offsets, or ask for them.
			#
			if self._played_node:
				try:
					pgeom = MMAttrdefs.getattr(self._played_node, 'base_winoff')
				except KeyError:
					pass
			if pgeom:
				self._wingeom = pgeom
			elif self._attrdict.has_key('base_winoff'):
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
		
		units = self._attrdict.get('units',
					   windowinterface.UNIT_SCREEN)
		self.create_window(self._get_parent_channel(), self._wingeom, units)
		
		return 1
		
	def play(self, node):
		print 'can''t play LayoutChannel'

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
			
			