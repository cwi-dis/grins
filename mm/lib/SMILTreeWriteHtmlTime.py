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


class SMILHtmlTimeWriter(SMIL):
	def __init__(self, node, fp, filename, cleanSMIL = 0, grinsExt = 1, copyFiles = 0,
		     evallicense = 0, tmpcopy = 0, progress = None,
		     convertURLs = 0):
		ctx = node.GetContext()
		self.root = node
		self.fp = fp
		self.__title = ctx.gettitle()

		self.smilboston = ctx.attributes.get('project_boston', 0)
		self.copydir = self.copydirurl = self.copydirname = None
		self.convertURLs = None

		self.ids_used = {}

		self.ugr2name = {}
		self.calcugrnames(node)

		self.layout2name = {}
		self.calclayoutnames(node)
		
		self.transition2name = {}
		self.calctransitionnames(node)

		self.ch2name = {}
		self.top_levels = []
		self.__subchans = {}
		self.calcchnames1(node)

		self.uid2name = {}
		self.calcnames1(node)

		# second pass
		self.calcnames2(node)
		self.calcchnames2(node)

		self.__isopen = 0
		self.__stack = []

	def writeAsHtmlTime(self):
		write = self.fp.write
		import version
		write('<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\">\n')
		self.writetag('html', [('xmlns:t','urn:schemas-microsoft-com:time')])
		self.push()

		# head
		self.writetag('head')
		self.push()
		
		# head contents
		if self.__title:
			self.writetag('meta', [('name', 'title'),
					       ('content', self.__title)])
		self.writetag('meta', [('name', 'generator'),
				       ('content','GRiNS %s'%version.version)])
		
		# style
		self.writetag('style', [('type', 'text/css'),])
		self.push()

		# style contents
		# Internet explorer style conventions for HTML+TIME support part 1
		write('.time {behavior: url(#default#time2);}\n')
		self.writelayout()

		self.pop() # style

		# Internet explorer style conventions for HTML+TIME support part 2
		write('<?IMPORT namespace=\"t\" implementation=\"#default#time2\">\n')

		self.pop() # head

		# body
		self.writetag('body')
		self.push()
		
		# body contents

		# viewports
		ch = self.top_levels[0]
		name = self.ch2name[ch]
		self.writetag('div', [('class', name),])
		self.push()
		self.writenode(self.root, root = 1)
		self.pop()

		self.close()

	def push(self):
		if self.__isopen:
			self.fp.write('>\n')
			self.__isopen = 0
		self.fp.push()

	def pop(self):
		fp = self.fp
		if self.__isopen:
			fp.write('/>\n')
			self.__isopen = 0
			del self.__stack[-1]
		fp.pop()
		fp.write('</%s>\n' % self.__stack[-1])
		del self.__stack[-1]

	def close(self):
		fp = self.fp
		if self.__isopen:
			fp.write('/>\n')
			self.__isopen = 0
			del self.__stack[-1]
		while self.__stack:
			self.pop()
		fp.close()

	def writetag(self, tag, attrs = None):
		if attrs is None:
			attrs = []
		write = self.fp.write
		if self.__isopen:
			write('/>\n')
			self.__isopen = 0
			del self.__stack[-1]
		write('<' + tag)
		for attr, val in attrs:
			write(' %s=%s' % (attr, nameencode(val)))
		self.__isopen = 1
		self.__stack.append(tag)

	def writenode(self, x, root = 0):
		type = x.GetType()
		interior = (type in interiortypes)
		if interior:
			if type == 'alt':
				xtype = mtype = 'switch'
			elif type == 'prio':
				xtype = mtype = 'priorityClass'
			else:
				xtype = mtype = type
		else:
			chtype = x.GetChannelType()
			if not chtype:
				chtype = 'unknown'
			mtype, xtype = mediatype(chtype)
		
		attrlist = []

		# if node used as destination, make sure it's id is written
		uid = x.GetUID()
		name = self.uid2name[uid]
		if not self.ids_used[name]:
			alist = x.GetAttrDef('anchorlist', [])
			hlinks = x.GetContext().hyperlinks
			for id, atype, args, times in alist:
				if hlinks.finddstlinks((uid, id)):
					self.ids_used[name] = 1
					break

		attributes = self.attributes.get(xtype, {})
		if type == 'prio':
			attrs = prio_attrs
		else:
			attrs = smil_attrs
			# special case for systemRequired
			sysreq = x.GetRawAttrDef('system_required', [])
			for i in range(len(sysreq)):
				attrlist.append(('ext%d' % i, sysreq[i]))

		for name, func in attrs:
			value = func(self, x)
			# only write attributes that have a value and are
			# legal for the type of node
			# other attributes are caught below
			if value and attributes.has_key(name) and value != attributes[name]:
				if name not in ('top','left','width','height','right','bottom', 'backgroundColor', 'region'):
					attrlist.append((name, value))

		#print uid, self.uid2name[uid], mtype, xtype, x.getPxAbsGeomMedia(), attrlist
		
		if interior:
			if root and (attrlist or type != 'seq'):
				root = 0
			if not root:
				self.writetag('t:'+mtype, attrlist)
				self.push()
			for child in x.GetChildren():
				self.writenode(child)
			if not root:
				self.pop()
		elif type in ('imm', 'ext'):
			children = x.GetChildren()
			if not children:				
				self.writemedianode(x, attrlist, mtype)
			else:
				self.writetag(mtype, attrlist)
				self.push()
				for child in x.GetChildren():
					self.writenode(child)
				self.pop()
		else:
			raise CheckError, 'bad node type in writenode'


	def writemedianode(self, x, attrlist, mtype):
		if mtype=='video':
			mtype = 'media'
		geoms = x.getPxAbsGeomMedia()
		if geoms:
			subRegGeom, mediaGeom = geoms
			style = 'position=absolute;left=%d;top=%d;width=%d;height=%d;' % mediaGeom
			attrlist.append( ('style',style) )
		self.writetag('t:'+mtype, attrlist)


	def writelayout(self):
		x = xmargin = 20
		y = ymargin = 20
		for ch in self.top_levels:
			w, h = ch.getPxGeom()
			name = self.ch2name[ch]
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
			style = '{position:absolute;overflow:hidden;left=%d;top=%d;width=%d;height=%d;background-color=%s;}' % (x, y, w, h, bgcolor)
			self.fp.write('.'+name + style + '\n')
			x = x + w + xmargin

	#
	#
	#
	def calcugrnames(self, node):
		"""Calculate unique names for usergroups"""
		usergroups = node.GetContext().usergroups
		if not usergroups:
			return
		self.smilboston = 1
		for ugroup in usergroups.keys():
			name = identify(ugroup)
			if self.ids_used.has_key(name):
				i = 0
				nn = '%s-%d' % (name, i)
				while self.ids_used.has_key(nn):
					i = i+1
					nn = '%s-%d' % (name, i)
				name = nn
			self.ids_used[name] = 1
			self.ugr2name[ugroup] = name

	def calclayoutnames(self, node):
		"""Calculate unique names for layouts"""
		layouts = node.GetContext().layouts
		if not layouts:
			return
		self.uses_grins_namespaces = 1
		for layout in layouts.keys():
			name = identify(layout)
			if self.ids_used.has_key(name):
				i = 0
				nn = '%s-%d' % (name, i)
				while self.ids_used.has_key(nn):
					i = i+1
					nn = '%s-%d' % (name, i)
				name = nn
			self.ids_used[name] = 1
			self.layout2name[layout] = name

	def calctransitionnames(self, node):
		"""Calculate unique names for transitions"""
		transitions = node.GetContext().transitions
		if not transitions:
			return
		self.smilboston = 1
		for transition in transitions.keys():
			name = identify(transition)
			if self.ids_used.has_key(name):
				i = 0
				nn = '%s-%d' % (name, i)
				while self.ids_used.has_key(nn):
					i = i+1
					nn = '%s-%d' % (name, i)
				name = nn
			self.ids_used[name] = 1
			self.transition2name[transition] = name

	def calcnames1(self, node):
		"""Calculate unique names for nodes; first pass"""
		uid = node.GetUID()
		name = node.GetRawAttrDef('name', '')
		if name:
			name = identify(name)
			if not self.ids_used.has_key(name):
				self.ids_used[name] = 1
				self.uid2name[uid] = name
		ntype = node.GetType()
		if ntype in interiortypes:
			for child in node.children:
				self.calcnames1(child)
				for c in child.children:
					self.calcnames1(c)
		if ntype == 'bag':
			self.uses_grins_namespaces = 1

	def calcnames2(self, node):
		"""Calculate unique names for nodes; second pass"""
		uid = node.GetUID()
		name = node.GetRawAttrDef('name', '')
		if not self.uid2name.has_key(uid):
			isused = name != ''
			if isused:
				name = identify(name)
			else:
				name = 'node'
			# find a unique name by adding a number to the name
			i = 0
			nn = '%s-%d' % (name, i)
			while self.ids_used.has_key(nn):
				i = i+1
				nn = '%s-%d' % (name, i)
			name = nn
			self.ids_used[name] = isused
			self.uid2name[uid] = name
		if node.GetType() in interiortypes:
			for child in node.children:
				self.calcnames2(child)
				for c in child.children:
					self.calcnames2(c)

	def calcchnames1(self, node):
		"""Calculate unique names for channels; first pass"""
		context = node.GetContext()
		channels = context.channels
		for ch in channels:
			name = identify(ch.name)
			if not self.ids_used.has_key(name):
				self.ids_used[name] = 0
				self.ch2name[ch] = name
			if ch.has_key('base_window'):
				pch = ch['base_window']
				if not self.__subchans.has_key(pch):
					self.__subchans[pch] = []
				self.__subchans[pch].append(ch)
			if not ch.has_key('base_window') and \
			   ch['type'] not in ('sound', 'shell', 'python',
					      'null', 'vcr', 'socket', 'cmif',
					      'midi', 'external'):
				# top-level channel with window
				self.top_levels.append(ch)
				if not self.__subchans.has_key(ch.name):
					self.__subchans[ch.name] = []
				if not self.__title:
					self.__title = ch.name
			# also check if we need to use the CMIF extension
			#if not self.uses_grins_namespace and \
			#   not smil_mediatype.has_key(ch['type']) and \
			#   ch['type'] != 'layout':
			#	self.uses_namespaces = 1
		if not self.__title and channels:
			# no channels with windows, so take very first channel
			self.__title = channels[0].name

	def calcchnames2(self, node):
		"""Calculate unique names for channels; second pass"""
		context = node.GetContext()
		channels = context.channels
		if self.top_levels:
			top0 = self.top_levels[0].name
		else:
			top0 = None
		for ch in channels:
			if not self.ch2name.has_key(ch):
				name = identify(ch.name)
				i = 0
				nn = '%s-%d' % (name, i)
				while self.ids_used.has_key(nn):
					i = i+1
					nn = '%s-%d' % (name, i)
				name = nn
				self.ids_used[name] = 0
				self.ch2name[ch] = name
			if not ch.has_key('base_window') and \
			   ch['type'] in ('sound', 'shell', 'python',
					  'null', 'vcr', 'socket', 'cmif',
					  'midi', 'external') and top0:
				self.__subchans[top0].append(ch)
			# check for SMIL 2.0 feature: hierarchical regions
			if not self.smilboston and \
			   not ch in self.top_levels and \
			   self.__subchans.get(ch.name):
				for sch in self.__subchans[ch.name]:
					if sch['type'] == 'layout':
						self.smilboston = 1
						break

#
#########################













