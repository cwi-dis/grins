__version__ = "$Id$"

animateInsideMediaSupportted = 0

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
import Animators

class SMILHtmlTimeWriter(SMIL):
	def __init__(self, node, fp, filename, cleanSMIL = 0, grinsExt = 1, copyFiles = 0,
		     evallicense = 0, tmpcopy = 0, progress = None,
		     convertURLs = 0):
		self.smilboston = 1
		self.prune = 0
		self.cleanSMIL = 1

		# some abbreviations
		self.context = ctx = node.GetContext()
		self.hyperlinks = ctx.hyperlinks

		self.root = node
		self.fp = fp
		self.__title = ctx.gettitle()
		self.__animateContext = Animators.AnimateContext(node=node)
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
		self.name2transition = {}
		self.calctransitionnames(node)

		self.ch2name = {}
		self.top_levels = []
		self.calcchnames1(node)

		self.uid2name = {}
		self.calcnames1(node)

		# second pass
		self.calcnames2(node)
		self.calcchnames2(node)

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
			msg = 'Not supported by HTML+TIME: %s' % key
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
		
		# body contents
		# viewports
		self.__currViewport = None
		if len(self.top_levels)==1:
			self.__currViewport = ch = self.top_levels[0]
			name = self.ch2name[ch]
			self.writetag('div', [('id',name), ('class', 'reg'+ name ),])
			self.push()
			self.writenode(self.root, root = 1)
			self.pop()
		else:
			for viewport in self.top_levels:
				name = self.ch2name[viewport]
				self.writetag('div', [('id',name), ('class', 'reg'+name),])
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

	def writecomment(self, x):
		write = self.fp.write
		if self.__isopen:
			write('/>\n')
			self.__isopen = 0
			del self.__stack[-1]
		write('<!--%s-->\n' % string.join(x.values, '\n'))

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

	def closehtmltag(self, expl=1):
		write = self.fp.write
		if self.__isopen:
			if expl:
				write('></%s>\n' % self.__stack[-1])
			else:
				write('>\n')
			self.__isopen = 0
			del self.__stack[-1]

	def writenode(self, x, root = 0):
		type = x.GetType()

		if type == 'animate':
			self.writeanimatenode(x, root)
			return

		if type == 'comment':
			self.writecomment(x)
			return

		attrlist = []
		interior = (type in interiortypes)
		if interior:
			if type == 'prio':
				xtype = mtype = 'priorityClass'
			elif type == 'foreign':
				tag = x.GetRawAttrDef('tag', None)
				if ' ' in tag:
					ns, tag = string.split(tag, ' ', 1)
					xtype = mtype = 'foreign:%s' % tag
					attrlist.append(('xmlns:foreign', ns))
				else:
					ns = ''
					xtype = mtype = tag
			else:
				xtype = mtype = type
		else:
			chtype = x.GetChannelType()
			if not chtype:
				chtype = 'unknown'
			mtype, xtype = mediatype(x)
		
		regionName = None
		nodeid = None
		transIn = None
		transOut = None

		# if node used as destination, make sure it's id is written
		uid = x.GetUID()
		name = self.uid2name[uid]
		if not self.ids_used[name] and self.hyperlinks.finddstlinks(x):
			self.ids_used[name] = 1

		attributes = self.attributes.get(xtype, {})
		if type == 'prio':
			attrs = prio_attrs
		elif type == 'foreign':
			attrs = []
			extensions = {ns: 'foreign'}
			for attr, val in x.attrdict.items():
				if attr == 'tag':
					continue
				if ' ' in attr:
					ans, attr = string.split(attr, ' ', 1)
					if not extensions.has_key(ans):
						extensions[ans] = 'x%s' % len(extensions)
						attrlist.append(('xmlns:%s' % extensions[ans], ans))
					attr = '%s:%s' % (extensions[ans], attr)
				attrlist.append((attr, val))
		else:
			attrs = smil_attrs
			# special case for systemRequired
			sysreq = x.GetRawAttrDef('system_required', [])
			for i in range(len(sysreq)):
				attrlist.append(('ext%d' % i, sysreq[i]))

		hasfill = 0
		for name, func, keyToCheck in attrs:
			if keyToCheck is not None and not x.attrdict.has_key(keyToCheck):
				continue
			value = func(self, x)
			if value and attributes.has_key(name) and value != attributes[name]:				

				if name == 'fill':
					hasfill = 1
				# endsync translation
				if name == 'endsync' and value not in ('first' , 'last'):
					name = 'end'
					value = value + '.end'

				# activateEvent exception
				elif name == 'end' and value == 'activateEvent':
					name = 'onClick'
					value = 'endElement();'

				elif name == 'src' and value[:8] == 'file:///' and value[9:10] == '|':
					value = 'file:///' + value[8] + ':' + value[10:]
						
				# for the rest
				else:
					# convert event refs
					if value: value = event2xhtml(value)

				if interior:
					attrlist.append((name, value))
				else:	
					if name == 'region': 
						regionName = value
					elif name == 'id':
						self.ids_written[value] = 1
						nodeid = value
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

		if not hasfill:
			# no fill attr, be explicit about fillDefault value
			fillDefault = MMAttrdefs.getattr(x, 'fillDefault')
			if fillDefault != 'inherit':
				attrlist.append(('fill', fillDefault))
		
		if interior:
			if mtype in not_xhtml_time_elements:
				pass # self.showunsupported(mtype)

			if ':' in mtype:
				self.writetag(mtype, attrlist)
			else:
				self.writetag('t:'+mtype, attrlist)
			self.push()
			for child in x.GetChildren():
				self.writenode(child)
			self.pop()

		elif type in ('imm', 'ext', 'brush'):
			if mtype in not_xhtml_time_elements:
				self.showunsupported(mtype)
			self.writemedianode(x, nodeid, attrlist, mtype, regionName, transIn, transOut)
		elif type != 'animpar':
			raise CheckError, 'bad node type in writenode'


	def writemedianode(self, node, nodeid, attrlist, mtype, regionName, transIn, transOut):
		moveAnimationOutside = 0
		
		if not animateInsideMediaSupportted:
			# if the animate node is not supported inside a media element, put it outside the element
			# in a par container

			# first check if the node contain some animations node inside the media node
			for child in node.GetChildren():
				if child.GetType() == 'animate':
					moveAnimationOutside = 1
					break

		if moveAnimationOutside:			
			# move in the par node all timing attributes which are on the media node
			# XXX it's a first approximation
			attrsToMove = []
			attrlen = len(attrlist)
			indList = range(attrlen-1)
			indList.reverse()
			for ind in indList:
				attrName, attrValue = attrlist[ind]
				if attrName in ('begin', 'end', 'dur'):
					attrsToMove.append((attrName, attrValue))
					del attrlist[ind]

			self.writetag('t:par', attrsToMove)
			self.push()
					
		if mtype=='video':
			mtype = 'media'

		parents = []
		viewport = None
		pushed = 0
	
		lch = self.root.GetContext().getchannel(regionName)

		while lch:
			if lch.get('type') != 'layout':
				continue
			pch = lch.GetParent()
			if pch is None:
				viewport = lch
				break
			parents.insert(0, lch)
			lch = pch

		if parents and mtype != 'audio':
			lch = parents[0]
			name = self.ch2name[lch]
			divlist = []
			divlist.append(('id', name))
##			if node.GetParent().GetType() == 'seq' and not moveAnimationOutside:
##				divlist.append(('timeContainer', 'par'))
##				divlist.append(('class', 'time'))
##				regstyle = self.ch2style.get(lch)
##				if regstyle is not None:
##					divlist.append(('style', regstyle))
##			else:	
			divlist.append(('class', 'reg'+regionName))
			self.writetag('div', divlist)
			self.push()
			self.ids_written[name] = 1
			pushed = 1
	
		transitions = self.root.GetContext().transitions
		if not nodeid:
			nodeid = 'm' + node.GetUID()
		if transIn or transOut:
			subregid = nodeid + '_subReg'

		subRegGeom, mediaGeom = None, None
		try:
			geoms = node.getPxGeomMedia()
		except:
			geoms = None
		if geoms and mtype != 'audio':
			subRegGeom, mediaGeom = geoms
			x, y, w, h = subRegGeom
			xm, ym, wm, hm = mediaGeom
			mediarc = x, y, wm, hm
		else:
			mediarc = None

		if mediarc:
			style = self.rc2style(mediarc)

			if transIn or transOut:
				style = style + 'filter:'
			
			if transIn:
				td = transitions.get(self.name2transition[transIn])
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
				td = transitions.get(self.name2transition[transOut])
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
				#style = style + 'visibility=hidden;'
				trans = 'transIn(%s, \'%s\')' % (nodeid, transInName)
				attrlist.append( ('onbegin', trans) )

			if nodeid:
				attrlist.insert(0,('id', nodeid))
			
			if mtype == 'brush':
				l = []
				for a, v in attrlist:
					if a == 'color':
						style = style + 'background-color:%s;' % v
					else:
						l.append((a, v))
				attrlist = l
			attrlist.append( ('style',style) )

		if self.writeAnchors(node, nodeid):
			attrlist.append(('usemap', '#'+nodeid+'map'))

		if transOut:
			self.writetag('t:par')
			self.push()

		if mtype=='img':
			attrlist.append( ('class','time') )
			self.writetag('t:'+mtype, attrlist)
		elif mtype=='brush':
			attrlist.append( ('class','time') )
			self.writetag('div', attrlist)
			self.closehtmltag()
		else:
			self.writetag('t:'+mtype, attrlist)
		kids = 0
		for child in node.GetChildren():
			type = child.GetType()
			if type != 'anchor':
				if not kids:
					self.push()
					kids = 1
				if not moveAnimationOutside or type != 'animate':
					self.writenode(child)
		if kids:
			self.pop()

		if transOut:
			trans = 'transOut(%s, \'%s\')' % (nodeid, transOutName)
			self.writetag('t:set', [ ('begin','%s.end-%.1f' % (nodeid,transOutDur)), ('dur', '%.1f' % transOutDur), ('onbegin', trans), ])
			self.pop()
		
		if pushed:
			self.pop()

		if moveAnimationOutside:
			# write the animate nodes
			for child in node.GetChildren():
				if child.GetType() == 'animate':
					self.writeanimatenode(child, 0, targetElement=nodeid)
					
			self.pop()

	def writeAnchors(self, x, name):
		hassrc = 0
		for anchor in x.GetChildren():
			if anchor.GetType() != 'anchor':
				continue
			links = self.hyperlinks.findsrclinks(anchor)
			if not links:
				continue
			if len(links) > 1:
				print '** Multiple links on anchor', \
				      anchor.GetRawAttrDef('name', '<unnamed>'), \
				      anchor.GetUID()
			if not hassrc:
				hassrc = 1
				self.writetag('map', [('id', name+'map')])
				self.push()
			a1, a2, dir, ltype, stype, dtype = links[0]
			attrlist = []
			id = getid(self, anchor)
			if id is not None:
				attrlist.append(('id', id))
			attrlist.extend(self.linkattrs(a2, ltype, stype, dtype))
			fragment = MMAttrdefs.getattr(anchor, 'fragment')
			if fragment:
				attrlist.append(('fragment', fragment))

			shape = MMAttrdefs.getattr(anchor, 'ashape')
			if shape != 'rect':
				attrlist.append(('shape', shape))
			coords = []
			for c in MMAttrdefs.getattr(anchor, 'acoords'):
				if type(c) is type(0):
					# pixel coordinates
					coords.append('%d' % c)
				else:
					# relative coordinates
					coords.append(fmtfloat(c*100, '%', prec = 2))
			if coords:
				attrlist.append(('coords', ','.join(coords)))

			begin = getsyncarc(self, anchor, 0)
			if begin is not None:
				attrlist.append(('begin', begin))
			end = getsyncarc(self, anchor, 1)
			if end is not None:
				attrlist.append(('end', end))

			actuate = MMAttrdefs.getattr(anchor, 'actuate')
			if actuate != 'onRequest':
				attrlist.append(('actuate', actuate))

			accesskey = anchor.GetAttrDef('accesskey', None)
			if accesskey is not None:
				attrs.append(('accesskey', accesskey))

			self.writetag('area', attrlist)
			self.closehtmltag(0)

		if hassrc:
			self.pop()
		return hassrc
				
	def writeEmptyRegion(self, regionName):
		parents = []
		viewport = None
		lch = self.root.GetContext().getchannel(regionName)
		while lch:
			if lch.get('type') != 'layout':
				continue
			pch = lch.GetParent()
			if pch is None:
				viewport = lch
				break
			parents.insert(0, lch)
			lch = pch
		
		pushed = 0
		if parents:
			lch = parents[0]
			name = self.ch2name[lch]
			divlist = []
			divlist.append(('id', name ))
			divlist.append(('class', 'reg'+regionName))
			self.writetag('div', divlist)
			self.push()
			self.ids_written[name] = 1
			pushed = pushed + 1

		for i in range(pushed):
			self.pop()

	def writeanimatenode(self, node, root, targetElement=None):
		attrlist = []
		if targetElement is not None:
			attrlist.append(('targetElement', targetElement))
		tag = node.GetAttrDict().get('atag')

		if tag == 'animateMotion':
			from Animators import AnimateElementParser
			aparser = AnimateElementParser(node, self.__animateContext)
			isAdditive = aparser.isAdditive()
			fromxy = aparser.toDOMOriginPosAttr('from')
			toxy = aparser.toDOMOriginPosAttr('to')
			values = aparser.toDOMOriginPosValues()
			path = aparser.toDOMOriginPath()

		attributes = self.attributes.get(tag, {})
		for name, func, gname in smil_attrs:
			if attributes.has_key(name):
				if name == 'type':
					value = node.GetRawAttrDef("trtype", None)
				else:
					value = func(self, node)
				if targetElement is None and name == 'targetElement':
					targetElement = value
					value = value
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
		for ch in self.root.GetContext().getviewports():
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
			style = 'position:absolute;overflow:hidden;left:%d;top:%d;width:%d;height:%d;background-color:%s;' % (x, y, w, h, bgcolor)
			self.ch2style[ch] = style
			self.fp.write('.reg'+name + ' {' + style + '}\n')

			for sch in ch.GetChildren():
				self.writeregion(sch, x, y)

			x = x + w + xmargin

	def writeregion(self, ch, dx, dy):
		if ch['type'] != 'layout':
			return
		if len(self.top_levels)==1:
			dx=dy=0

		x, y, w, h = ch.getPxGeom()
		style = 'position:absolute;overflow:hidden;left:%d;top:%d;width:%d;height:%d;' % (dx+x, dy+y, w, h)
		
		transparent = ch.get('transparent', None)
		bgcolor = ch.get('bgcolor', None)
		if bgcolor and transparent==0:
			if colors.rcolors.has_key(bgcolor):
				bgcolor = colors.rcolors[bgcolor]
			else:
				bgcolor = '#%02x%02x%02x' % bgcolor
			style = style + 'background-color:%s;' % bgcolor
			
		z = ch.get('z', 0)
		if z > 0:
			style = style + 'z-index:%d;' % z

		self.ch2style[ch] = style

		name = self.ch2name[ch]
		self.fp.write('.reg'+name + ' {' + style + '}\n')
		
		for sch in ch.GetChildren():
			self.writeregion(sch, x+dx, y+dy)
		
	def rc2style(self, rc):
		x, y, w, h = rc
		return 'position:absolute;overflow:hidden;left:%d;top:%d;width:%d;height:%d;' % (x, y, w, h)

	def linkattrs(self, a2, ltype, stype, dtype):
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
		if type(a2) is type(''):
			attrs.append(('href', a2))
		else:
			attrs.append(('href', 'javascript:%s.beginElement()' % self.uid2name[a2.GetUID()]))

		return attrs

	#
	#
	#
	def calcugrnames(self, node):
		# Calculate unique names for usergroups
		usergroups = node.GetContext().usergroups
		if not usergroups:
			return
		for ugroup in usergroups.keys():
			name = identify(ugroup, html = 1)
			if self.ids_used.has_key(name):
				i = 0
				nn = '%s_%d' % (name, i)
				while self.ids_used.has_key(nn):
					i = i+1
					nn = '%s_%d' % (name, i)
				name = nn
			self.ids_used[name] = 1
			self.ugr2name[ugroup] = name

	def calclayoutnames(self, node):
		# Calculate unique names for layouts
		layouts = node.GetContext().layouts
		if not layouts:
			return
		self.uses_grins_namespaces = 1
		for layout in layouts.keys():
			name = identify(layout, html = 1)
			if self.ids_used.has_key(name):
				i = 0
				nn = '%s_%d' % (name, i)
				while self.ids_used.has_key(nn):
					i = i+1
					nn = '%s_%d' % (name, i)
				name = nn
			self.ids_used[name] = 1
			self.layout2name[layout] = name

	def calctransitionnames(self, node):
		# Calculate unique names for transitions
		transitions = node.GetContext().transitions
		if not transitions:
			return
		for transition in transitions.keys():
			name = identify(transition, html = 1)
			if self.ids_used.has_key(name):
				i = 0
				nn = '%s_%d' % (name, i)
				while self.ids_used.has_key(nn):
					i = i+1
					nn = '%s_%d' % (name, i)
				name = nn
			self.ids_used[name] = 1
			self.transition2name[transition] = name
			self.name2transition[name] = transition

	def calcnames1(self, node):
		# Calculate unique names for nodes; first pass
		uid = node.GetUID()
		name = node.GetRawAttrDef('name', '')
		if name:
			name = identify(name, html = 1)
			if not self.ids_used.has_key(name):
				self.ids_used[name] = 1
				self.uid2name[uid] = name
		ntype = node.GetType()
		if ntype in interiortypes:
			for child in node.children:
				self.calcnames1(child)
				for c in child.children:
					self.calcnames1(c)

	def calcnames2(self, node):
		# Calculate unique names for nodes; second pass
		uid = node.GetUID()
		name = node.GetRawAttrDef('name', '')
		if not self.uid2name.has_key(uid):
			isused = name != ''
			if isused:
				name = identify(name, html = 1)
			else:
				name = 'node'
			# find a unique name by adding a number to the name
			i = 0
			nn = '%s_%d' % (name, i)
			while self.ids_used.has_key(nn):
				i = i+1
				nn = '%s_%d' % (name, i)
			name = nn
			self.ids_used[name] = isused
			self.uid2name[uid] = name
		if node.GetType() in interiortypes:
			for child in node.children:
				self.calcnames2(child)
				for c in child.children:
					self.calcnames2(c)

	def calcchnames1(self, node):
		# Calculate unique names for channels; first pass
		context = node.GetContext()
		channels = context.channels
		for ch in channels:
			name = identify(ch.name, html = 1)
			if not self.ids_used.has_key(name):
				self.ids_used[name] = 0
				self.ch2name[ch] = name
			if ch.GetParent() is None and \
			   ChannelMap.isvisiblechannel(ch['type']):
				# top-level channel with window
				self.top_levels.append(ch)
				if not self.__title:
					self.__title = ch.name
		if not self.__title and channels:
			# no channels with windows, so take very first channel
			self.__title = channels[0].name

	def calcchnames2(self, node):
		# Calculate unique names for channels; second pass
		context = node.GetContext()
		channels = context.channels
		for ch in context.getviewports():
			if ChannelMap.isvisiblechannel(ch['type']):
				# first top-level channel
				top0 = ch.name
				break
		else:
			top0 = None
		for ch in channels:
			if not self.ch2name.has_key(ch):
				name = identify(ch.name, html = 1)
				i = 0
				nn = '%s_%d' % (name, i)
				while self.ids_used.has_key(nn):
					i = i+1
					nn = '%s_%d' % (name, i)
				name = nn
				self.ids_used[name] = 0
				self.ch2name[ch] = name

	# copied from SMILTreeWrite.py
	def syncidscheck(self, node):
		# make sure all nodes referred to in sync arcs get their ID written
		for arc in node.GetRawAttrDef('beginlist', []) + node.GetRawAttrDef('endlist', []):
			# see also getsyncarc() for similar code
			if arc.srcnode is None and arc.event is None and arc.marker is None and arc.wallclock is None and arc.accesskey is None:
				pass
			elif arc.wallclock is not None:
				pass
			elif arc.accesskey is not None:
				pass
			elif arc.marker is None:
				srcnode = arc.srcnode
				if type(srcnode) is type('') and srcnode not in ('prev', 'syncbase'):
					srcnode = arc.refnode()
					if srcnode is None:
						continue
				if arc.channel is not None:
					pass
				elif srcnode in ('syncbase', 'prev'):
					pass
				elif srcnode is not node:
					self.ids_used[self.uid2name[srcnode.GetUID()]] = 1
			else:
				self.ids_used[self.uid2name[arc.srcnode.GetUID()]] = 1
		for child in node.children:
			self.syncidscheck(child)


#
#   Util
#
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
	# Return the class that implements this transition. 
	if TRANSITIONDICT_OK.has_key((trtype, subtype)):
		return TRANSITIONDICT_OK[(trtype, subtype)]
	if TRANSITIONDICT_OK.has_key((trtype, None)):
		return TRANSITIONDICT_OK[(trtype, None)]

	if TRANSITIONDICT.has_key((trtype, subtype)):
		return TRANSITIONDICT[(trtype, subtype)]
	if TRANSITIONDICT.has_key((trtype, None)):
		return TRANSITIONDICT[(trtype, None)]

	return defaultTrans
