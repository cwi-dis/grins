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
	def writeAsHtmlTime(self):
		write = self.fp.write
		writetag = SMILWriter.writetag

		write('<html xmlns:t =\"urn:schemas-microsoft-com:time\">\n')

		writetag(self,'head')
		self.push()

		writetag(self,'style')
		self.push()

		write('.time { behavior: url(#default#time2) }\n')
		self.writelayout()
		
		self.pop()

		write('<?IMPORT namespace=\"t\" implementation=\"#default#time2\">\n')

		self.pop()

		writetag(self,'body')
		self.push()
		
		self.writenode(self.root, root = 1)

		self.pop()
		write('</html>\n')

		self.close()


	def writetag(self, tag, attrs = None):
		if tag == 'layout': return
		elif tag == 'viewport': return
		elif tag == 'region':
			self.writeRegionClass(attrs)
			return;
		tag = 't:'+ tag
		attrscpy = attrs[:]
		attrs = []
		for attr, val in attrscpy:
			if attr == 'region':
				attr = 'class'
			attrs.append((attr, val))

		SMILWriter.writetag(self, tag, attrs)

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
			elif features.compatibility == features.G2:
				bgcolor = 0,0,0
			else:
				bgcolor = 255,255,255
			if colors.rcolors.has_key(bgcolor):
				bgcolor = colors.rcolors[bgcolor]
			else:
				bgcolor = '#%02x%02x%02x' % bgcolor
			if self.smilboston:
				attrlist.append(('backgroundColor', bgcolor))
			else:
				attrlist.append(('background-color', bgcolor))
				
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

			for ch in self.top_levels:
				self.writeregion(ch)

	def writeRegionClass(self, attrs):
		for attr, val in attrs:
			if attr=='id':
				self.fp.write('.'+val + ' {position: absolute;' )	
				break
		for attr, val in attrs:
			if attr=='id': continue
			if attr=='calcMode':
				self.fp.write('%s:%s; ' % (attr, val))	
			else:
				self.fp.write('%s:\"%s\"; ' % (attr, val))	
		self.fp.write(' }\n')	
				

		