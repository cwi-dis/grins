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


class SMILHtmlTimeWriter(SMILWriter):
	def __init__(self, node, fp, filename, cleanSMIL = 0, grinsExt = 1, copyFiles = 0,
		     evallicense = 0, tmpcopy = 0, progress = None,
		     convertURLs = 0):
		
		SMILWriter.__init__(self, node, fp, filename, cleanSMIL, grinsExt, copyFiles,
		     evallicense, tmpcopy, progress,
		     convertURLs )
		ctx = node.GetContext()
		self.__title = ctx.gettitle()
		self._viewportClass = ''

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

		self.pop() # </body>

		write('</html>\n')

		self.close()


	def basewritetag(self, tag, attrs = None):
		SMILWriter.writetag(self, tag, attrs)

	def writetag(self, tag, attrs = None):
		# layout
		if tag == 'layout': return
		elif tag == 'viewport':
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

		# media items in div
		attrscpy = attrs[:]
		classval = None
		idval = None
		styleval = ''
		attrs = []
		attrs.append(('class', 'time'))
		for attr, val in attrscpy:
			if attr == 'region':
				classval = val
			elif attr == 'id':
				idval = val
			elif attr in ('top','left','width','height','right','bottom'):
				if not styleval:
					styleval = 'position=absolute; '
				styleval = styleval + attr + "=" + val + "; "
			else:
				attrs.append((attr, val))
		if styleval:
			attrs.append(('style', styleval))

		if idval:
			SMILWriter.writetag(self, "div", [('class', classval),('id', idval),])
		else:
			SMILWriter.writetag(self, "div", [('class', classval),])
		self.push()
		SMILWriter.writetag(self, tag, attrs)
		self.pop()

	def writelayout(self):
		"""Write the layout section"""
		attrlist = []
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
			else:
				bgcolor = 255,255,255
			if colors.rcolors.has_key(bgcolor):
				bgcolor = colors.rcolors[bgcolor]
			else:
				bgcolor = '#%02x%02x%02x' % bgcolor
			attrlist.append(('background', bgcolor))
						
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

			self.writetag('viewport', attrlist)

			for ch in self.top_levels:
				self.writeregion(ch)

	def writeRegionClass(self, attrs):
		idval = None
		for attr, val in attrs:
			if attr=='id':
				idval = val
				self.fp.write('.'+val + ' {position:absolute;' )	
				break
		for attr, val in attrs:
			if attr=='id': continue
			if attr=='calcMode':
				self.fp.write('%s:%s; ' % (attr, val))	
			else:
				self.fp.write('%s:\"%s\"; ' % (attr, val))	
		self.fp.write(' }\n')	
		return idval		

		