__version__ = "$Id$"


#
#	Export interface 
# 
def WriteFileAsHtmlTime(root, filename, cleanSMIL = 0, grinsExt = 1, copyFiles = 0, evallicense = 0, progress = None, convertURLs = 0):
	fp = IndentedFile(open(filename, 'w'))
	try:
		writer = SMILHtmlTimeWriter(root, fp, filename, cleanSMIL, grinsExt, copyFiles, evallicense, progress = progress, convertURLs = convertURLs)
	except Error, msg:
		from windowinterface import showmessage
		showmessage(msg, mtype = 'error')
		return
	writer.writeAsHtmlTime()


not_xhtml_time_elements = ('prefetch', )

not_xhtml_time_attrs = ('min', 'max',  'customTest', 'fillDefault', 
	'restartDefault', 'syncBehaviorDefault','syncToleranceDefault', 'repeat',
	#'regPoint', 'regAlign', # we take them into account indirectly
	'close', 'open', 'pauseDisplay',
	'showBackground',
	)


#
#	XHTML+TIME DTD 
# 
class XHTML_TIME:

	__Core = {'class':None,
		'id':None,
	}

	__basicTiming = {'begin':None,
		'dur':None,
		'end':None,
		'repeatCount':None,
		'repeatDur':None,
	}

	__Timing = {'restart':None,
		'syncBehavior':None,
		'syncMaster':None,
		'syncTolerance':None,
		'timeAction':'visibility'
	}
	__Timing.update(__basicTiming)


	__TimeManipulators = {'speed':None,
		    'accelerate':None,
		    'decelerate':None,
		    'autoReverse':None,
	}

	__Media = {'abstract':'',
		'author':'',
		'copyright':'',
		'title': '',
		'clipBegin':None,
		'clipEnd':None,
		'fill':None,
		'src':None,
		'type':None,
		'player':None,
		'mute':'false',
		'volume':'1.0',
	}

	__animate_attrs_core = {'attributeName':None,
				'attributeType':None,
				'autoReverse':'false',
				'fill':None,
				'targetElement': None,
				'to':None,
				}

	__animate_attrs_extra = {'accumulate':'none',
				 'additive':'replace',
				 'by':None,
				 'calcMode':'linear',
				 'from':None,
				 'keySplines':None,
				 'keyTimes':None,
				 'values':None,
				 }

	# Elements

	__media_object = ['audio', 'video', 'img', 'animation', 'media', 'ref']

	__animate_elements = ['animate', 'animateMotion', 'animateColor', 'set']

	__containers = ['par', 'seq', 'switch', 'excl''priorityClass', ]



	#
	__allElements = __media_object + __animate_elements + __containers


	def hasElement(self, element):
		return element in __allElements


#
#	SMILHtmlTimeWriter
# 
from SMILTreeWrite import *
import math

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
		if convertURLs:
			url = MMurl.canonURL(MMurl.pathname2url(filename))
			i = string.rfind(url, '/')
			if i >= 0: url = url[:i+1]
			else: url = ''
			self.convertURLs = url
		else:
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

		# must come after second pass
		self.aid2name = {}
		self.anchortype = {}
		self.calcanames(node)

		self.syncidscheck(node)

		self.__isopen = 0
		self.__stack = []

		self.__currViewport = None
		self.__currRegion = None

		self.ch2style = {}
		self.ids_written = {}
	
		self.__warnings = {}

	def showunsupported(self, key):
		from windowinterface import showmessage
		if not self.__warnings.has_key(key):
			msg = '%s: not supported by XHTML+TIME' % key
			showmessage(msg, mtype = 'warning')
			self.__warnings[key]=1

	def writeAsHtmlTime(self):
		write = self.fp.write
		ctx = self.root.GetContext()
		import version
		write('<!DOCTYPE HTML PUBLIC \"-//W3C//DTD W3 HTML//EN\">\n')
		if ctx.comment:
			write('<!--%s-->\n' % ctx.comment)
		#self.writetag('html', [('xmlns:t','urn:schemas-microsoft-com:time')])
		self.writetag('html')
		self.push()

		# head
		self.writetag('head')
		self.push()
		
		# head contents
		self.writetag('meta', [('http-equiv', 'content-type'), 
			('content', 'text/html; charset=ISO-8859-1')])
		if self.__title:
			self.writetag('meta', [('name', 'title'),
					       ('content', self.__title)])
		self.writetag('meta', [('name', 'generator'),
				       ('content','GRiNS %s'%version.version)])

		#
		self.writetag('XML:namespace', [('prefix','t'),])

		# style
		self.writetag('style', [('type', 'text/css'),])
		self.push()

		# style contents

		# Internet explorer style conventions for HTML+TIME support
		write('.time {behavior: url(#default#time2); }\n')
		write('t\:*  {behavior: url(#default#time2); }\n') # or part 2 below
		
		self.writelayout()

		self.pop() # style

		# Internet explorer style conventions for HTML+TIME support part 2
		#write('<?IMPORT namespace=\"t\" implementation=\"#default#time2\">\n')

		if ctx.transitions:
			write(transScript)

		self.pop() # head

		# body
		self.writetag('body')
		self.push()
		self.writetag('t:seq')
		self.push()
		
		# body contents
		# viewports
		self.__currViewport = None
		if len(self.top_levels)==1:
			self.__currViewport = ch = self.top_levels[0]
			name = self.ch2name[ch]
			self.writetag('div', [('id',scriptid(name)), ('class', 'reg'+ scriptid(name) ),])
			self.push()
			self.writenode(self.root, root = 1)
			self.pop()
		else:
			for viewport in self.top_levels:
				name = self.ch2name[viewport]
				self.writetag('div', [('id',scriptid(name)), ('class', 'reg'+scriptid(name)),])
				self.push()
				self.pop()
			self.writenode(self.root, root = 1)
			
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

	def closehtmltag(self):
		write = self.fp.write
		if self.__isopen:
			write('></%s>\n' % self.__stack[-1])
			self.__isopen = 0
			del self.__stack[-1]

	def writenode(self, x, root = 0):
		type = x.GetType()

		if type=='animate':
			self.writeanimatenode(x, root)
			return

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
		regionName = None
		src = None
		nodeid = None
		transIn = None
		transOut = None

		# if node used as destination, make sure it's id is written
		uid = x.GetUID()
		name = self.uid2name[uid]
		if not self.ids_used[name]:
			alist = x.GetAttrDef('anchorlist', [])
			hlinks = x.GetContext().hyperlinks
			for a in alist:
				if hlinks.finddstlinks((uid, a.aid)):
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
			if value and attributes.has_key(name) and value != attributes[name]:				

				# endsync translation
				if name == 'endsync' and value not in ('first' , 'last'):
					name = 'end'
					if value[:3] == 'id(':
						value = scriptid(value[3:-1]) + '.end'
					else:
						value = scriptid(value) + '.end'

				# activateEvent exception
				elif name == 'end' and value == 'activateEvent':
					name = 'onClick'
					value = 'endElement();'

				# for the rest
				else:
					# scriptify ids of known refs
					if value: value = scriptidref(value)
				
					# convert event refs
					if value: value = event2xhtml(value)

				if interior:
					if name == 'id':
						value = scriptid(value)
					attrlist.append((name, value))
				else:	
					if name == 'region': 
						regionName = value
					elif name == 'src': 
						src = value
					elif name == 'id':
						self.ids_written[value] = 1
						nodeid = value
						value = scriptid(value)
					elif name == 'transIn':
						transIn = value
					elif name == 'transOut':
						transOut = value
					elif name == 'backgroundColor':
						pass
					elif name in ('regPoint', 'regAlign'):
						pass # taken into account indirectly
					elif not name in ('top','left','width','height','right','bottom'):
						attrlist.append((name, value))
		
		if interior:
			if mtype in not_xhtml_time_elements:
				pass # self.showunsupported(mtype)

			if not root:
				self.writetag('t:'+mtype, attrlist)
				self.push()
			for child in x.GetChildren():
				self.writenode(child)
			if not root:
				self.pop()

		elif type in ('imm', 'ext'):
			if mtype in not_xhtml_time_elements:
				self.showunsupported(mtype)

			children = x.GetChildren()
			if not children:				
				self.writemedianode(x, nodeid, attrlist, mtype, regionName, src, transIn, transOut)
			else:
				self.writetag(mtype, attrlist)
				self.push()
				for child in x.GetChildren():
					self.writenode(child)
				self.pop()
		else:
			raise CheckError, 'bad node type in writenode'


	def writemedianode(self, x, nodeid, attrlist, mtype, regionName, src, transIn, transOut):
		if mtype=='video':
			mtype = 'media'

		if src:
			if self.convertURLs:
				src = MMurl.canonURL(x.GetContext().findurl(src))
				if src[:len(self.convertURLs)] == self.convertURLs:
					src = src[len(self.convertURLs):]
			attrlist.append(('src', src))
					
		if mtype == 'audio':
			if nodeid:
				attrlist.insert(0,('id', scriptid(nodeid)))
			self.writetag('t:'+mtype, attrlist)
			return	

		parents = []
		viewport = None
		pushed = 0
	
		lch = self.root.GetContext().getchannel(regionName)

		while lch:
			if lch.get('type') != 'layout':
				continue
			if lch in self.top_levels:
				viewport = lch
				break
			parents.insert(0, lch)
			lch = lch.__parent
	
		if parents:
			lch = parents[0]
			name = self.ch2name[lch]
			divlist = []
			divlist.append(('id', scriptid(name)))
			divlist.append(('class', 'reg'+scriptid(regionName)))
			self.writetag('div', divlist)
			self.push()
			self.ids_written[name] = 1
			pushed = pushed + 1

					
		transitions = self.root.GetContext().transitions
		if not nodeid:
			nodeid = 'm' + x.GetUID()
		if transIn or transOut:
			subregid = nodeid + '_subReg'

		subRegGeom, mediaGeom = None, None
		try:
			geoms = x.getPxGeomMedia()
		except:
			geoms = None
		if geoms:
			subRegGeom, mediaGeom = geoms

		if subRegGeom:
			divlist = []
			style = self.rc2style(subRegGeom)

			if transIn or transOut:
				divlist.append(('id', scriptid(subregid)))
				style = style + 'filter:'
			
			if transIn:
				td = transitions.get(transIn)
				if not td:
					trtype = 'barWipe'
					subtype = None
					dur = 1
				else:
					trtype = td.get('trtype')
					subtype = td.get('subtype')
					dur = td.get('dur')
				if not dur: dur = 1
				elif dur<=0: dur = 0.1
				transInName, properties = TransitionFactory(trtype, subtype)
				if properties:
					trans = '%s.%s(%s,dur=%.1f)' % (msfilter, transInName, properties, dur)
				else:
					trans = '%s.%s(dur=%.1f)' % (msfilter, transInName, dur)
				style = style + trans

			if transOut:
				td = transitions.get(transOut)
				if not td:
					trtype = 'barWipe'
					subtype = None
					transOutDur = 1
				else:
					trtype = td.get('trtype')
					subtype = td.get('subtype')
					transOutDur = td.get('dur')
				if not transOutDur: transOutDur = 1
				elif transOutDur<=0: transOutDur = 0.1
				transOutName, properties = TransitionFactory(trtype, subtype)
				if properties:
					trans = '%s.%s(%s,dur=%.1f)' % (msfilter, transOutName, properties, transOutDur)
				else:
					trans = '%s.%s(dur=%.1f)' % (msfilter, transOutName, transOutDur)
				style = style + trans
				
			if transIn or transOut:
				style = style + ';'

			if transIn:
				style = style + 'visibility=hidden;'
				trans = 'transIn(%s, \'%s\')' % (scriptid(subregid), transInName)
				attrlist.append( ('onbegin', trans) )

			divlist.append(('style', style))
			self.writetag('div', divlist)
			self.push()
			pushed = pushed + 1

		if mediaGeom:
			if nodeid:
				attrlist.insert(0,('id', scriptid(nodeid)))
			style = 'position=absolute;left=%d;top=%d;width=%d;height=%d;' % mediaGeom
			if mtype == 'brush':
				l = []
				for a, v in attrlist:
					if a == 'color':
						style = style + 'background-color=%s;' % v
					else:
						l.append((a, v))
				attrlist = l
			attrlist.append( ('style',style) )

		if self.writeAnchors(x, nodeid):
			attrlist.append(('usemap', '#'+scriptid(nodeid)+'map'))

		if transOut:
			self.writetag('t:par')
			self.push()
			pushed = pushed + 1

		if mtype=='img':
			attrlist.append( ('class','time') )
			self.writetag(mtype, attrlist)
		elif mtype=='brush':
			attrlist.append( ('class','time') )
			self.writetag('div', attrlist)
			self.closehtmltag()
		else:
			self.writetag('t:'+mtype, attrlist)

		if transOut:
			trans = 'transOut(%s, \'%s\')' % (scriptid(subregid), transOutName)
			self.writetag('t:set', [ ('begin','%s.end-%.1f' % (scriptid(nodeid),transOutDur)), ('dur', '%.1f' % transOutDur), ('onbegin', trans), ])
			self.pop()
			pushed = pushed - 1
		
		for i in range(pushed):
			self.pop()

	def writeAnchors(self, x, name):
		alist = MMAttrdefs.getattr(x, 'anchorlist')
		hassrc = 0		# 1 if has source anchors
		for a in alist:
			if a.atype in SourceAnchors:
				hassrc = 1
				break
		if hassrc:
			self.writetag('map', [('id', scriptid(name)+'map'),])
			self.push()
			for a in alist:
				if a.atype in SourceAnchors:
					self.writelink(x, a)
			self.pop()
			return 1
		return 0

				
	def writeEmptyRegion(self, regionName):
		parents = []
		viewport = None
		lch = self.root.GetContext().getchannel(regionName)
		while lch:
			if lch.get('type') != 'layout':
				continue
			if lch in self.top_levels:
				viewport = lch
				break
			parents.insert(0, lch)
			lch = lch.__parent
		
		pushed = 0
		if parents:
			lch = parents[0]
			name = self.ch2name[lch]
			divlist = []
			divlist.append(('id', scriptid(name) ))
			divlist.append(('class', 'reg'+scriptid(regionName)))
			self.writetag('div', divlist)
			self.push()
			self.ids_written[name] = 1
			pushed = pushed + 1

		for i in range(pushed):
			self.pop()

	def writeanimatenode(self, node, root):
		attrlist = []
		targetElement = None
		tag = node.GetAttrDict().get('atag')

		if tag == 'animateMotion':
			from Animators import AnimateElementParser
			aparser = AnimateElementParser(node)
			isAdditive = aparser.isAdditive()
			fromxy = aparser.toDOMOriginPosAttr('from')
			toxy = aparser.toDOMOriginPosAttr('to')
			values = aparser.toDOMOriginPosValues()
			path = aparser.toDOMOriginPath()

		attributes = self.attributes.get(tag, {})
		for name, func in smil_attrs:
			if attributes.has_key(name):
				value = func(self, node)
				if value: value = scriptidref(value)
				if name == 'targetElement':
					targetElement = value
					value = scriptid(value)
				if tag == 'animateMotion' and not isAdditive:
					if name == 'from':value = fromxy
					elif name == 'to':value = toxy
					elif name == 'values':value = values
					elif name == 'path': value = path
				if value and value != attributes[name]:
					attrlist.append((name, value))

		if not self.ids_written.has_key(targetElement):
			self.writeTargetElement(targetElement)
		self.writetag('t:'+tag, attrlist)

	def writeTargetElement(self, uid):
		lch = self.root.GetContext().getchannel(uid)
		if lch:
			self.writeEmptyRegion(uid)
			

	def writelayout(self):
		x = xmargin = 20
		y = ymargin = 20
		for ch in self.top_levels:
			w, h = ch.getPxGeom()
			name = self.ch2name[ch]
			if ch.has_key('bgcolor'):
				bgcolor = ch['bgcolor']
			else:
				bgcolor = 255,255,255
			if colors.rcolors.has_key(bgcolor):
				bgcolor = colors.rcolors[bgcolor]
			else:
				bgcolor = '#%02x%02x%02x' % bgcolor
			style = 'position:absolute;overflow:hidden;left=%d;top=%d;width=%d;height=%d;background-color=%s;' % (x, y, w, h, bgcolor)
			self.ch2style[ch] = style
			self.fp.write('.reg'+scriptid(name) + ' {' + style + '}\n')

			if self.__subchans.has_key(ch.name):
				for sch in self.__subchans[ch.name]:
					self.writeregion(sch, x, y)

			x = x + w + xmargin

	def writeregion(self, ch, dx, dy):
		if ch['type'] != 'layout':
			return
		if len(self.top_levels)==1:
			dx=dy=0

		x, y, w, h = ch.getPxGeom()
		style = 'position:absolute;overflow:hidden;left=%d;top=%d;width=%d;height=%d;' % (dx+x, dy+y, w, h)
		
		transparent = ch.get('transparent', None)
		bgcolor = ch.get('bgcolor', None)
		if bgcolor and transparent==0:
			if colors.rcolors.has_key(bgcolor):
				bgcolor = colors.rcolors[bgcolor]
			else:
				bgcolor = '#%02x%02x%02x' % bgcolor
			style = style + 'background-color=%s;' % bgcolor
			
		z = ch.get('z', 0)
		if z > 0:
			style = style + 'z-index=%d;' % z

		self.ch2style[ch] = style

		name = self.ch2name[ch]
		self.fp.write('.reg'+scriptid(name) + ' {' + style + '}\n')
		
		if self.__subchans.has_key(ch.name):
			for sch in self.__subchans[ch.name]:
				self.writeregion(sch, x+dx, y+dy)
		
	def rc2style(self, rc):
		x, y, w, h = rc
		return 'position:absolute;overflow:hidden;left=%d;top=%d;width=%d;height=%d;' % (x, y, w, h)

	def writelink(self, x, a):
		attrlist = []
		aid = (x.GetUID(), a.aid)
		attrlist.append(('id', scriptid(self.aid2name[aid])))

		links = x.GetContext().hyperlinks.findsrclinks(aid)
		if links:
			if len(links) > 1:
				print '** Multiple links on anchor', \
				      x.GetRawAttrDef('name', '<unnamed>'), \
				      x.GetUID()
			a1, a2, dir, ltype, stype, dtype = links[0]
			attrlist[len(attrlist):] = self.linkattrs(a2, ltype, stype, dtype, a.aaccess)
		if a.atype == ATYPE_NORMAL:
			ok = 0
			# WARNING HACK HACK HACK : How know if it's a shape or a fragment ?
			try:
				shapeType = a.aargs[0]
				if shapeType == A_SHAPETYPE_RECT or shapeType == A_SHAPETYPE_POLY or \
						shapeType == A_SHAPETYPE_CIRCLE:
					coords = []
					for c in a.aargs[1:]:
						if type(c) == type(0):
							# pixel coordinates
							coords.append('%d' % c)
						else:
							# relative coordinates
							coords.append(fmtfloat(c*100, '%', prec = 2))
					coords = string.join(coords, ',')
					ok = 1
				elif shapeType == A_SHAPETYPE_ALLREGION:
					rc = x.getPxGeomMedia()[1]
					for c in rc:
						coords.append('%d' % c)
					coords = string.join(coords, ',')
					ok = 1
			except:
				pass						
			if ok:
				if shapeType == A_SHAPETYPE_POLY:
					attrlist.append(('shape', 'poly'))
				elif shapeType == A_SHAPETYPE_CIRCLE:
					attrlist.append(('shape', 'circle'))
				elif shapeType == A_SHAPETYPE_RECT:
					attrlist.append(('shape', 'rect'))
					
				#if shapeType != A_SHAPETYPE_ALLREGION:
				attrlist.append(('coords', coords))
			else:
				attrlist.append(('fragment', id))						
		elif a.atype == ATYPE_AUTO:
			attrlist.append(('actuate', 'onLoad'));
		else:
			coords = []
			rc = x.getPxGeomMedia()[1]
			for c in rc:
				coords.append('%d' % c)
			coords = string.join(coords, ',')
			attrlist.append(('coords', coords))
				
		begin, end = a.atimes
		if begin:
			attrlist.append(('begin', fmtfloat(begin, 's')))
		if end:
			attrlist.append(('end', fmtfloat(end, 's')))
		self.writetag('area', attrlist)

	def linkattrs(self, a2, ltype, stype, dtype, accesskey):
		attrs = []
		if ltype == Hlinks.TYPE_JUMP:
			# default value, so we don't need to write it
			pass
		elif ltype == Hlinks.TYPE_FORK:
			attrs.append(('show', 'new'))
			if stype == Hlinks.A_SRC_PLAY:
				# default sourcePlaystate value
				pass
			elif stype == Hlinks.A_SRC_PAUSE:
				attrs.append(('sourcePlaystate', 'pause'))			
			elif stype == Hlinks.A_SRC_STOP:
				attrs.append(('sourcePlaystate', 'stop'))
		
		if dtype == Hlinks.A_DEST_PLAY:
			# default value, so we don't need to write it
			pass
		elif dtype == Hlinks.A_DEST_PAUSE:
				attrs.append(('destinationPlaystate', 'pause'))
							
		# else show="replace" (default)
		if type(a2) is type(()):
			uid2, aid2 = a2
			if '/' in uid2:
				if aid2:
					href, tag = a2
				else:
					lastslash = string.rfind(uid2, '/')
					href, tag = uid2[:lastslash], uid2[lastslash+1:]
					if tag == '1':
						tag = None
			else:
				href = ''
				if self.anchortype.get(a2) == ATYPE_NORMAL and \
				   self.aid2name.has_key(a2):
					tag = self.aid2name[a2]
				else:
					tag = self.uid2name[uid2]
			if tag:
				href = href + '#' + tag
		else:
			href = a2

		if href[:1] == '#':
			withinhref = scriptid(href[1:])
			attrs.append(('href', '#'+withinhref))
			attrs.append(('onClick', withinhref + '.beginElement();'))
		else:
			attrs.append(('href', href))

		if accesskey is not None:
			attrs.append(('accesskey', accesskey))

		return attrs

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

		# enable bottom up search
		for ch in channels:
			ch.__parent = None
		for parentName, childs in self.__subchans.items():
			parchan = self.root.GetContext().getchannel(parentName)
			for ch in childs:
				ch.__parent = parchan

	def calcanames(self, node):
		"""Calculate unique names for anchors"""
		uid = node.GetUID()
		alist = MMAttrdefs.getattr(node, 'anchorlist')
		for a in alist:
			aid = (uid, a.aid)
			self.anchortype[aid] = a.atype
			if a.atype in SourceAnchors:
				if isidre.match(a.aid) is None or \
				   self.ids_used.has_key(a.aid):
					aname = '%s-%s' % (self.uid2name[uid], a.aid)
					aname = identify(aname)
				else:
					aname = a.aid
				if self.ids_used.has_key(aname):
					i = 0
					nn = '%s-%d' % (aname, i)
					while self.ids_used.has_key(nn):
						i = i+1
						nn = '%s-%d' % (aname, i)
					aname = nn
				self.aid2name[aid] = aname
				self.ids_used[aname] = 0
		if node.GetType() in interiortypes:
			for child in node.children:
				self.calcanames(child)

	def syncidscheck(self, node):
		# make sure all nodes referred to in sync arcs get their ID written
		for srcuid, srcside, delay, dstside in node.GetRawAttrDef('synctolist', []):
			self.ids_used[self.uid2name[srcuid]] = 1
		if node.GetType() in interiortypes:
			for child in node.children:
				self.syncidscheck(child)

#
#   Util
#
def scriptid(name):
	if not name: return name
	l = []
	for ch in name:
		if ch=='-': ch = '_'
		l.append(ch)
	return string.join(l, '')

smil20suffix = ('.begin', '.end', '.activateEvent', '.beginEvent', '.endEvent')

def scriptidref(value):
	if not value: return value
	for suffix in smil20suffix:	
		ix = string.find(value, suffix)
		if ix>0: 
			return scriptid(value[:ix]) + value[ix:]
	return value

smil20event2xhtml = {'.activateEvent':'.click', '.beginEvent':'.begin', '.endEvent':'.end'}
def event2xhtml(value):
	if not value: return value
	for ev in smil20event2xhtml.keys():	
		l = string.split(value, ev)
		if len(l)==2:
			return l[0]+smil20event2xhtml[ev] + l[1]
	return value
		
	
#
#	Transitions
# 
transInScript="function transIn(obj, name){\n  var fname=\"DXImageTransform.Microsoft.\" + name;\n  var filter=obj.filters[fname];\n  if(filter!=null) filter.Apply();\n  obj.style.visibility = \"visible\";\n  if(filter!=null) filter.Play();\n}\n"
transOutScript="function transOut(obj, name){\n  var fname=\"DXImageTransform.Microsoft.\" + name;\n  var filter=obj.filters[fname];\n  if(filter!=null) filter.Play();\n}\n"
transScript = "<script language=JavaScript>\n%s%s</script>\n" % (transInScript, transOutScript)

msfilter = 'progid:DXImageTransform.Microsoft'

#defaultTrans = ('Iris', 'irisStyle=circle, motion=out')

#defaultTrans = ('Blinds', 'direction=up, bands=1')

#defaultTrans = ('Strips', 'motion=leftdown')

#defaultTrans = ('Barn', 'orientation=vertical, motion=out')

#defaultTrans = ('RandomBars', 'orientation=horizontal')

#defaultTrans = ('CheckerBoard', 'direction=right')

#defaultTrans = ('RandomDissolve', '')

#defaultTrans = ('CrStretch', 'stretchStyle=push')

defaultTrans = ( 'Wipe', 'GradientSize=.50, wipeStyle=0, motion=forward', )

TRANSITIONDICT_OK = {
	("irisWipe", "rectangle") : ('Iris', 'irisStyle=rectangle, motion=out'),
	("irisWipe", "diamond") : ('Iris', 'irisStyle=diamond, motion=out'),
	("irisWipe", None) : ('Iris', 'irisStyle=rectangle, motion=out'),

	("ellipseWipe", "circle") : ('Iris', 'irisStyle=circle, motion=out'),
	("ellipseWipe", None) : ('Iris', 'irisStyle=circle, motion=out'),
	
	("starWipe", None) : ('Iris', 'irisStyle=star, motion=out'),

	("fade", 'crossfade') : ('Fade', ''),
	("fade", None) : ('Fade', ''),
}



TRANSITIONDICT = {
	("barWipe", "leftToRight") : ( 'Wipe', 'GradientSize=.50, wipeStyle=0, motion=forward'),
	("barWipe", None) : ( 'Wipe', 'GradientSize=.50, wipeStyle=0, motion=forward'),
	("boxWipe", "topLeft") : defaultTrans,
	("boxWipe", None) : defaultTrans,
	("fourBoxWipe", "cornersIn") : defaultTrans,
	("fourBoxWipe", None) : defaultTrans,
	("barnDoorWipe", "vertical") : defaultTrans,
	("barnDoorWipe", None) : defaultTrans,
	("diagonalWipe", "topLeft") : defaultTrans,
	("diagonalWipe", None) : defaultTrans,
	("bowTieWipe", "vertical") : defaultTrans,
	("bowTieWipe", None) : defaultTrans,
	("miscDiagonalWipe", "doubleBarnDoor") : defaultTrans,
	("miscDiagonalWipe", None) : defaultTrans,
	("veeWipe", "down") : defaultTrans,
	("veeWipe", None) : defaultTrans,
	("barnVeeWipe", "down") : defaultTrans,
	("barnVeeWipe", None) : defaultTrans,
	("zigZagWipe", "leftToRight") : ('Strips','Motion=rightup'),
	("zigZagWipe", None) : ('Strips','Motion=rightup'),
	("barnZigZagWipe", "vertical") : ('Zigzag', 'GridSizeX=8,GridSizeY=8'),
	("barnZigZagWipe", None) : ('Zigzag', 'GridSizeX=8,GridSizeY=8'),
	("irisWipe", "rectangle") : ('Iris', 'irisStyle=rectangle, motion=out'),
	("irisWipe", None) : ('Iris', 'irisStyle=circle, motion=out'),
	("triangleWipe", "up") : ('Iris', 'irisStyle=diamond, motion=out'),
	("triangleWipe", None) : ('Iris', 'irisStyle=diamond, motion=out'),
	("arrowHeadWipe", "up") : ('Iris', 'irisStyle=diamond, motion=out'),
	("arrowHeadWipe", None) : ('Iris', 'irisStyle=diamond, motion=out'),
	("pentagonWipe", "up") : ('Iris', 'irisStyle=diamond, motion=out'),
	("pentagonWipe", None) : ('Iris', 'irisStyle=diamond, motion=out'),
	("hexagonWipe", "up") : ('Iris', 'irisStyle=diamond, motion=out'),
	("hexagonWipe", None) : ('Iris', 'irisStyle=diamond, motion=out'),
	("ellipseWipe", "circle") : ('Iris', 'irisStyle=circle, motion=out'),
	("ellipseWipe", None) : ('Iris', 'irisStyle=circle, motion=out'),
	("eyeWipe", "horizontal") : ('Iris', 'irisStyle=circle, motion=out'),
	("eyeWipe", None) : ('Iris', 'irisStyle=circle, motion=out'),
	("roundRectWipe", "horizontal") : ('Iris', 'irisStyle=circle, motion=out'),
	("roundRectWipe", None) : ('Iris', 'irisStyle=circle, motion=out'),
	("starWipe", "fourPoint") : ('Iris', 'irisStyle=star, motion=out'),
	("starWipe", None) : ('Iris', 'irisStyle=star, motion=out'),
	("clockWipe", "clockwiseTwelve") : ('RadialWipe', 'wipeStyle=clock'),
	("clockWipe", None) : ('RadialWipe', 'wipeStyle=clock'),
	("pinWheelWipe", "twoBladeVertical") : ('RadialWipe', 'wipeStyle=wedge'),
	("pinWheelWipe", None) : ('CrRadialWipe', 'wipeStyle=wedge'),
	("singleSweepWipe", "clockwiseTop") : ('Wipe','GradientSize=.50, wipeStyle=0, motion=forward') ,
	("singleSweepWipe", None) : ( 'Wipe', 'GradientSize=.50, wipeStyle=0, motion=forward') ,
	("fanWipe", "centerTop") : ('CrWheel', 'spokes=4'),
	("fanWipe", None) : ('CrWheel', 'spokes=8'),
	("doubleFanWipe", "fanOutVertical") : ('CrWheel', 'spokes=4'),
	("doubleFanWipe", None) : ('CrWheel', 'spokes=8'),
	("doubleSweepWipe", "parallelVertical") : defaultTrans,
	("doubleSweepWipe", None) : defaultTrans,
	("saloonDoorWipe", "top") : ( 'Barn', 'orientation=horizontal, motion=out'),
	("saloonDoorWipe", None) : ( 'Barn', 'orientation=vertical, motion=out'),
	("windshieldWipe", "right") : ('RadialWipe', 'wipeStyle=wedge'),
	("windshieldWipe", None) :  ('RadialWipe', 'wipeStyle=wedge'),
	("snakeWipe", "topLeftHorizontal") : ('Zigzag', 'GridSizeX=8,GridSizeY=8'),
	("snakeWipe", None) : ('Zigzag', 'GridSizeX=8,GridSizeY=8'),
	("spiralWipe", "topLeftClockwise") : ('CrSpiral', 'GridSizeX=8,GridSizeY=8'), 
	("spiralWipe", None) : ('CrSpiral', 'GridSizeX=8,GridSizeY=8'),	# OK
	("parallelSnakesWipe", "verticalTopSame") : ('Zigzag', 'GridSizeX=8,GridSizeY=8'),
	("parallelSnakesWipe", None) : ('Zigzag', 'GridSizeX=8,GridSizeY=8'),
	("boxSnakesWipe", "twoBoxTop") : ('Zigzag', 'GridSizeX=8,GridSizeY=8'),
	("boxSnakesWipe", None) : ('Zigzag', 'GridSizeX=8,GridSizeY=8'),
	("waterfallWipe", "verticalLeft") : ('Strips','Motion=rightdown'),
	("waterfallWipe", None) : ('Strips','Motion=rightdown'),
	("pushWipe", "fromLeft") : ('CrSlide', 'slideStyle=push, bands=1'),
	("pushWipe", None) : ('CrSlide', 'slideStyle=push, bands=1'),
	("slideWipe", "fromLeft") : ('CrSlide', 'slideStyle=push, bands=1'), # OK
	("slideWipe", None) : ('CrSlide', 'slideStyle=push, bands=1'), # OK
	("fade", "crossFade") : ('Fade', ''), # OK
	("fade", None) : ('Fade', ''), # OK
}

def TransitionFactory(trtype, subtype):
	"""Return the class that implements this transition. """
	if TRANSITIONDICT_OK.has_key((trtype, subtype)):
		return TRANSITIONDICT_OK[(trtype, subtype)]
	if TRANSITIONDICT_OK.has_key((trtype, None)):
		return TRANSITIONDICT_OK[(trtype, None)]

	if TRANSITIONDICT.has_key((trtype, subtype)):
		return TRANSITIONDICT[(trtype, subtype)]
	if TRANSITIONDICT.has_key((trtype, None)):
		return TRANSITIONDICT[(trtype, None)]

	return defaultTrans

#
#########################













 
 
