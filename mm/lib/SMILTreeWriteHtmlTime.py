__version__ = "$Id$"


from SMILTreeWrite import *


def WriteFileAsHtmlTime(root, filename, cleanSMIL = 0, grinsExt = 1, copyFiles = 0, evallicense = 0, progress = None, convertURLs = 0):
	fp = IndentedFile(open(filename, 'w'))
	try:
		writer = SMILHtmlTimeWriter(root, fp, filename, cleanSMIL, grinsExt, copyFiles, evallicense, progress = progress, convertURLs = convertURLs)
	except Error, msg:
		from windowinterface import showmessage
		showmessage(msg, mtype = 'error')
		return
	writer.writeAsHtmlTime()

class _Node:
	def __init__(self, name, dict):
		self._name = name
		self._attrdict = dict

		self._parent = None
		self._children = []

	def _do_init(self, parent):
		self._parent = parent
		parent._children.append(self)

	def findNode(self, name):
		if self._name == name:
			return self
		ret = None
		for node in self._children:
			fn = node.findNode(name)
			if fn : 
				ret = fn
				break
		return ret

	def dump(self):
		print self._name, self._attrdict
		for node in self._children:
			node.dump()


class SMILHtmlTimeWriter(SMILWriter):
	def __init__(self, node, fp, filename, cleanSMIL = 0, grinsExt = 1, copyFiles = 0,
		     evallicense = 0, tmpcopy = 0, progress = None,
		     convertURLs = 0):
		SMILWriter.__init__(self, node, fp, filename, cleanSMIL, grinsExt, copyFiles,
		     evallicense, tmpcopy, progress,
		     convertURLs )
		ctx = node.GetContext()
		self.__title = ctx.gettitle()
		self.__cleanSMIL = cleanSMIL
		self.__subchans = self.getsubchans()
		self._viewportClass = ''
		self.__viewports = {}
		self.__buildLayoutTree(ctx)
		
	def writeAsHtmlTime(self):
		write = self.fp.write
		import version

		write('<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\">\n')
		write('<html xmlns:t =\"urn:schemas-microsoft-com:time\">\n')

		self.basewritetag('head')
		self.push()
		
		if self.__title:
			self.basewritetag('meta', [('name', 'title'),
					       ('content', self.__title)])
		self.basewritetag('meta', [('name', 'generator'),
				       ('content','GRiNS %s'%version.version)])

		self.basewritetag('style', [('type', 'text/css'),])
		self.push()

		# Internet explorer style conventions for HTML+TIME support
		write('.time {behavior: url(#default#time2);}\n')
		write('t\:* {behavior: url(#default#time2);}\n')
		
		self.writelayout()
		
		self.pop() # </style>

		#write('<?IMPORT namespace=\"t\" implementation=\"#default#time2\">\n')
		
		self.pop() # </head>
			
		self.basewritetag('body')
		self.push()

		if self._viewportClass:
			self.basewritetag('div', [('class', self._viewportClass),])
			self.push()

		self.writenode(self.root, root = 1)

		if self._viewportClass:
			self.pop()

		try : self.pop() # </body>
		except: pass

		write('</html>\n')

		self.close()

	def basewritetag(self, tag, attrs = None):
		SMILWriter.writetag(self, tag, attrs)

	def writetag(self, tag, attrs = None):
		# layout
		if tag == 'layout': return
		elif tag == 'viewport' or tag=='root-layout':
			attrs.append(('left','20'))
			attrs.append(('top','20'))
			#attrs.append(('border', 'solid gray'))
			self._viewportClass = self.writeRegionClass(attrs)
			return	
		elif tag == 'region':
			self.writeRegionClass(attrs)
			return;


		# containers
		if tag in ('seq', 'par', 'excl', 'switch'):
			tag = 't:'+ tag
			SMILWriter.writetag(self, tag, attrs)
			return
		
		# animate elements
		if tag in ('animate', 'animateMotion', 'animateColor', 'set'):
			tag = 't:'+ tag
			SMILWriter.writetag(self, tag, attrs)
			return

		if tag in ('area', 'anchor'):
			SMILWriter.writetag(self, tag, attrs)
			return

		# media items in div
		attrscpy = attrs[:]
		classval = None
		idval = None
		styleval = ''
		attrs = []
		if tag=='video':
			tag = 'media'
		tag = 't:'+tag
		#attrs.append(('class', 'time'))
		for attr, val in attrscpy:
			if attr == 'region':
				classval = val
			elif attr == 'id':
				idval = val
			elif attr in ('top','left','width','height','right','bottom', 'backgroundColor'):
				if not styleval:
					styleval = 'position=absolute; '
				if attr == 'backgroundColor':
					attr = 'background'
				styleval = styleval + attr + "=" + val + "; "
			else:
				attrs.append((attr, val))
		if styleval:
			attrs.append(('style', styleval))

		self.writeMediaLayout(classval, idval, tag, attrs)


	def writeMediaLayout(self, region, id, tag, attrs):
		parrgn = self.__getParentRegion(self._viewportClass, region)
		if parrgn:
			SMILWriter.writetag(self, "div", [('class', parrgn._name),])
			self.push()
			
		if id:
			SMILWriter.writetag(self, "div", [('class', region),('id', id),])
		else:
			SMILWriter.writetag(self, "div", [('class', region),])
		self.push()

		SMILWriter.writetag(self, tag, attrs)
		self.pop()
		
		if parrgn:
			self.pop()

	def writelayout(self):
		"""Write the layout section"""
		attrlist = []
		self.writetag('layout', attrlist)
		self.push()
		#if self.smilboston:
		#	self.__writeRegPoint()		
		channels = self.root.GetContext().channels
		for ch in self.top_levels:
			attrlist = []
			if ch['type'] == 'layout':
				attrlist.append(('id', self.ch2name[ch]))
			title = ch.get('title')
			if title:
				attrlist.append(('title', title))
			elif self.ch2name[ch] != ch.name:
				attrlist.append(('title', ch.name))
			if ch.has_key('bgcolor'):
				bgcolor = ch['bgcolor']
			elif features.compatibility == features.G2:
				bgcolor = 0,0,0
			else:
				bgcolor = 255,255,255
			if colors.rcolors.has_key(bgcolor):
				bgcolor = colors.rcolors[bgcolor]
			else:
				bgcolor = '#%02x%02x%02x' % bgcolor
			attrlist.append(('background', bgcolor))
				
			if self.smilboston:
				# write only not default value
				if ch.has_key('open'):
					val = ch['open']
					if val != 'always':
						attrlist.append(('open', val))
				if ch.has_key('close'):
					val = ch['close']
					if val != 'never':
						attrlist.append(('close', val))
		
			if ch.has_key('winsize'):
				units = ch.get('units', 0)
				w, h = ch['winsize']
				if units == 0:
					# convert mm to pixels
					# (assuming 100 dpi)
					w = int(w / 25.4 * 100.0 + .5)
					h = int(h / 25.4 * 100.0 + .5)
					units = 2
				if units == 1:
					attrlist.append(('width', '%d%%' % int(w * 100 + .5)))
					attrlist.append(('height', '%d%%' % int(h * 100 + .5)))
				else:
					attrlist.append(('width', '%d' % int(w + .5)))
					attrlist.append(('height', '%d' % int(h + .5)))

			if self.smilboston:
				for key, val in ch.items():
					if not cmif_chan_attrs_ignore.has_key(key):
						attrlist.append(('%s:%s' % (NSGRiNSprefix, key), MMAttrdefs.valuerepr(key, val)))
				self.writetag('viewport', attrlist)
				#self.push()
				self.writeregion(ch)
				#self.pop()
			else:
				self.writetag('root-layout', attrlist)
		if not self.smilboston:	# implies one top-level
			for ch in self.top_levels:
				self.writeregion(ch)
		#self.pop()

	def writeregion(self, ch):
		mtype, xtype = mediatype(ch['type'], error=1)
		if ch['type'] == 'layout' and \
		   not ch.has_key('base_window'):
			# top-level layout channel has been handled
			for sch in self.__subchans[ch.name]:
				self.writeregion(sch)
			return
		attrlist = [('id', self.ch2name[ch])]
		if ch.has_key('regionName'):
			attrlist.append(('regionName', ch['regionName']))
		title = ch.get('title')
		if title:
			attrlist.append(('title', title))
		elif self.ch2name[ch] != ch.name:
			attrlist.append(('title', ch.name))
		# if toplevel window, define a region elt, but
		# don't define coordinates (i.e., use defaults)
		if ch.has_key('base_window') and \
		   ch.has_key('base_winoff'):
			x, y, w, h = ch['base_winoff']
			units = ch.get('units', 2)
			if units == 0:		# UNIT_MM
				# convert mm to pixels (assuming 100 dpi)
				x = int(x / 25.4 * 100 + .5)
				y = int(y / 25.4 * 100 + .5)
				w = int(w / 25.4 * 100 + .5)
				h = int(h / 25.4 * 100 + .5)
			elif units == 1:	# UNIT_SCREEN
				if x+w >= 1.0: w = 0
				if y+h >= 1.0: h = 0
			elif units == 2:	# UNIT_PXL
				x = int(x)
				y = int(y)
				w = int(w)
				h = int(h)
			for name, value in [('left', x), ('top', y), ('width', w), ('height', h)]:
				if not value:
					continue
				if type(value) is type(0.0):
					value = '%d%%' % int(value*100)
				else:
					value = '%d' % value
				attrlist.append((name, value))
		if ChannelMap.isvisiblechannel(ch['type']):
			z = ch.get('z', 0)
			if z > 0:
				attrlist.append(('z-index', "%d" % z))
			scale = ch.get('scale', 0)
			if scale == 0:
				fit = 'meet'
			elif scale == -1:
				fit = 'slice'
			elif scale == 1:
				fit = 'hidden'
			elif scale == -3:
				fit = 'fill'
			else:
				fit = None
				print '** Channel uses unsupported scale value', name
			if fit is not None and fit != 'hidden':
				attrlist.append(('fit', fit))

			# SMIL says: either background-color
			# or transparent; if different, set
			# GRiNS attributes
		# We have the following possibilities:
		#		no bgcolor	bgcolor set
		#transp -1	no attr		b-g="bg"
		#transp  0	GR:tr="0"	GR:tr="0" b-g="bg"
		#transp  1	b-g="trans"	b-g="trans" (ignore bg)
			transparent = ch.get('transparent', 0)
			bgcolor = ch.get('bgcolor')
			if transparent == 0:
				if features.compatibility == features.G2:
					# in G2, setting a
					# background-color implies
					# transparent==never, so set
					# background-color if not
					# transparent
					if colors.rcolors.has_key(bgcolor or (0,0,0)):
						bgcolor = colors.rcolors[bgcolor or (0,0,0)]
					else:
						bgcolor = '#%02x%02x%02x' % (bgcolor or (0,0,0))
					if self.smilboston:
						attrlist.append(('background',
								 bgcolor))
					else:
						attrlist.append(('background',
								 bgcolor))
					bgcolor = None # skip below
				# non-SMIL extension:
				# permanently visible region
				if not self.smilboston:
					attrlist.append(('%s:transparent' % NSGRiNSprefix,
							 '0'))
			#
			# We write the background color only if it is not None.
			# We also refrain from writing it if we're in G2 compatability mode and
			# the color is the default (g2-compatible) color: white for text channels
			# and black for others.
			if bgcolor is not None and \
			   (features.compatibility != features.G2 or
			    ((ch['type'] not in ('text', 'RealText') or
			      bgcolor != (255,255,255)) and
			     bgcolor != (0,0,0))) and \
			     (not self.__cleanSMIL or ch['type'] != 'RealText'):
				if colors.rcolors.has_key(bgcolor):
					bgcolor = colors.rcolors[bgcolor]
				else:
					bgcolor = '#%02x%02x%02x' % bgcolor
				if self.smilboston:
					attrlist.append(('background',
							 bgcolor))
				else:
					attrlist.append(('background',
							 bgcolor))
			# Since background-color="transparent" is the
			# default, we don't need to actually write that
			if ch.get('center', 1):
				attrlist.append(('%s:center' % NSGRiNSprefix, '1'))
			if ch.get('drawbox', 1):
				attrlist.append(('%s:drawbox' % NSGRiNSprefix, '1'))
			
			# we save the showBackground attribute only if it's not the default value
			showBackground = ch.get('showBackground', 'always')
			if showBackground != 'always':
				attrlist.append(('showBackground', showBackground))
			
			if self.smilboston:
				soundLevel = ch.get('soundLevel')
			# we save only the soundLevel attribute if it exists and different of default value
				if soundLevel != None and soundLevel != 1.0:
					value = '%d%%' % int(soundLevel*100)
					attrlist.append(('soundLevel', value))
			
				regPoint = ch.get('regPoint')
				if regPoint != None:
					attrlist.append(('regPoint',regPoint))
				
				regAlign = ch.get('regAlign')
				if regAlign != None and regAlign != 'topLeft':
					attrlist.append(('regAlign',regAlign))
				
		# for layout channel the subtype attribute is translated to grins:type attribute
		subtype = ch.get('subtype')
		if subtype != None:
			attrlist.append(('%s:type' % NSGRiNSprefix, subtype))

		for key, val in ch.items():
			if not cmif_chan_attrs_ignore.has_key(key):
				attrlist.append(('%s:%s' % (NSGRiNSprefix, key), MMAttrdefs.valuerepr(key, val)))
		self.writetag('region', attrlist)
		subchans = self.__subchans.get(ch.name)
		
		# new 03-07-2000
		# cnt sub layoutchannel number --> to allow to close the tag if no element inside
		lcNumber = 0
		if subchans:
			for sch in subchans:
				if sch['type'] == 'layout':
					lcNumber = lcNumber + 1
		# end new
		
		if lcNumber > 0:
			#self.push()
			for sch in subchans:
				# new 03-07-2000
				# save only the layout channels
				if sch['type'] == 'layout':
				# end new
					self.writeregion(sch)
			#self.pop()

	def writeRegionClass(self, attrs):
		idval = None
		for attr, val in attrs:
			if attr=='id':
				idval = val
				self.fp.write('.'+val + ' {position:absolute;overflow:hidden;')
				break
		for attr, val in attrs:
			if attr=='id': continue
			if attr=='calcMode':
				self.fp.write('%s:%s; ' % (attr, val))	
			elif attr=='background':
				self.fp.write('%s:%s; ' % ('background', val))	
			else:
				self.fp.write('%s:%s; ' % (attr, val))	
		self.fp.write(' }\n')	
		return idval		

	def __buildLayoutTree(self, context):	
		# create viewports and build map id2parentid
		id2parentid = {}
		for chan in context.channels:
			if chan.attrdict.get('type')=='layout':
				if chan.attrdict.has_key('base_window'):
					# region
					id2parentid[chan.name] = chan.attrdict['base_window']
				else:
					# viewport
					vp = self.__viewports[chan.name] = _Node(chan.name, chan.attrdict)
					name = self.ch2name[chan]
					if name != chan.name:
						self.__viewports[self.ch2name[chan]] = vp

		# create all nodes
		nodes = self.__viewports.copy()
		for name in id2parentid.keys():
			chan = context.channeldict[name]
			nodes[name] = _Node(chan.name, chan.attrdict)

		# associate regions with their parent
		for id, parentid in id2parentid.items():
			nodes[id]._do_init(nodes[parentid])
		
	def __getParentRegion(self, vpname, rgnname):
		if not self.__viewports.has_key(vpname):
			print 'Warning: missing viewport', vpname
			return None
		viewport = self.__viewports[vpname]
		region = viewport.findNode(rgnname)
		if region and region._parent!=viewport:
			return region._parent
		return None


		