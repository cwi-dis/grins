__version__ = "$Id$"


#
#	Export interface 
# 
def WriteFileAsXhtmlSmil(root, filename, cleanSMIL = 0, grinsExt = 1, copyFiles = 0, evallicense = 0, progress = None, convertURLs = 0):
	fp = IndentedFile(open(filename, 'w'))
	try:
		writer = SMILXhtmlSmilWriter(root, fp, filename, cleanSMIL, grinsExt, copyFiles, evallicense, progress = progress, convertURLs = convertURLs)
	except Error, msg:
		from windowinterface import showmessage
		showmessage(msg, mtype = 'error')
		return
	writer.writeAsXhtmlSmil()


not_xhtml_smil_elements = ('prefetch', )

not_xhtml_smil_attrs = ('min', 'max',  'customTest', 'fillDefault', 
	'restartDefault', 'syncBehaviorDefault','syncToleranceDefault', 'repeat',
	#'regPoint', 'regAlign', # we take them into account indirectly
	'close', 'open', 'pauseDisplay',
	'showBackground',
	)

#
#	XHTML+SMIL DTD 
# 
class XHTML_SMIL:

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
#	SMILXhtmlSmilWriter
# 
from SMILTreeWrite import *

# imported by SMILTreeWrite:
# import string 
# from fmtfloat import fmtfloat 
# from nameencode import nameencode
from fmtfloat import round
import math
import Animators
import Duration
import tokenizer

# debug flags
debug = 1

class SMILXhtmlSmilWriter(SMIL):
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

		# remove next as soon as getRegionFromName becomes obsolete
		self.chnamedict = {} 

		self.ch2name = {}
		self.top_levels = []
		self.calcchnames1(node)
		self.hasMultiWindowLayout = (len(self.top_levels) > 1)
		self.regions_alias = {}

		self.uid2name = {}
		self.calcnames1(node)

		# second pass
		self.calcnames2(node)
		self.calcchnames2(node)

		self.syncidscheck(node)

		self.sensitivityList = []
		self.buildSensitivityList(self.root, self.sensitivityList)

		self.links_target2src = {}
		self.linkssources = {}
		self.animate_nodes = []
		self.animate_regions = []
		self.animate_motion_nodes = []
		self.animate_motion_regions = []
		self.buildTargets(node)

		self.freezeSyncDict = {}
		self.seqtimingfixes = {}
		
		self.currLayout = []
		self.node2layout = {}

		self.__isopen = 0
		self.__stack = []

		self.ids_written = {}
	
		self.__warnings = {}

	def showunsupported(self, key):
		from windowinterface import showmessage
		if not self.__warnings.has_key(key):
			msg = 'Not supported by XHTML+SMIL: %s' % key
			showmessage(msg, mtype = 'warning')
			self.__warnings[key]=1

	def writeAsXhtmlSmil(self):
		write = self.fp.write
		ctx = self.root.GetContext()
		import version
		write('<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0 Transitional//EN\">\n')
		if ctx.comment:
			write('<!--%s-->\n' % ctx.comment)

		self.writetag('html', [('xmlns:t', 'urn:schemas-microsoft-com:time'),])
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
		self.writetag('style')
		self.push()
		write(".time {behavior: url(#default#time2)}\n");
		self.pop() # style

		# style contents
		# Internet explorer style conventions for XHTML+SMIL support
		write("<?IMPORT namespace=\"t\" implementation=\"#default#time2\">\n")

		self.pop() # head

		# body
		self.writetag('body')
		self.push()
		
		# body contents
		self.writeToplayout()
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

	def pushviewport(self, viewport, moreattrs = None):
		style = self.getViewportStyle(viewport)
		name = self.registerRegionAlias(viewport)
		divlist = [('id', name), ('style', style),]
		if moreattrs: divlist= divlist + moreattrs
		self.writetag('div', divlist)
		self.push()
		self.currLayout = [viewport]
				
	def popviewport(self):
		self.pop()
		self.currLayout = []

	def writeToplayout(self):
		style = self.getLayoutStyle()
		self.writetag('div', [('id','xhtml_smil_export'), ('style', style),])
		self.push()
		if self.hasMultiWindowLayout:
			for v in self.top_levels:
				action = v.get('open', 'onStart')
				if action == 'onStart':
					style = self.getViewportStyle(v)
					self.writetag('div', [('style', style),])
					self.push()
					self.writeRegionBackground(v)
					self.pop()
		else:
			v = self.top_levels[0]
			style = self.getViewportStyle(v)
			name = self.ch2name[v]
			self.writetag('div', [('id',name), ('style', style),])
			self.push()
			self.writeRegionBackground(v)
			self.currLayout = [v]

	def writeRegionBackground(self, v):
		for reg in v.GetChildren():
			if reg.get('type') == 'layout':
				showBackground = reg.get('showBackground', 'always')
				transparent = reg.get('transparent', None)
				bgcolor = reg.get('bgcolor', None)
				if showBackground == 'always' and bgcolor and transparent==0:
					style = self.getRegionStyle(reg)
					name = self.registerRegionAlias(reg)
					self.ids_written[name] = 1
					self.writetag('div', [('id', name), ('style', style),])
					self.push()
					self.writeRegionBackground(reg)
					self.pop()

	def issensitive(self, node):
		return node in self.sensitivityList

	def writenode(self, x, root = 0):
		type = x.GetType()

		if type == 'comment':
			self.writecomment(x)
			return

		if type == 'animate':
			self.writeanimatenode(x, root)
			return

		####
		attrlist = []
		interior = (type in interiortypes)
		if interior:
			if type == 'prio':
				xtype = mtype = 'priorityClass'
			elif type == 'foreign':
				ns = x.GetRawAttrDef('namespace', '')
				tag = x.GetRawAttrDef('elemname', None)
				if ns:
					xtype = mtype = 'foreign:%s' % tag
					attrlist.append(('xmlns:foreign', ns))
				else:
					xtype = mtype = tag
			else:
				xtype = mtype = type
		else:
			chtype = x.GetChannelType()
			if not chtype:
				chtype = 'unknown'
			mtype, xtype = mediatype(x)
		
		# if node used as destination, make sure it's id is written
		uid = x.GetUID()
		name = self.uid2name[uid]
		if not self.ids_used[name] and self.hyperlinks.finddstlinks(x):
			self.ids_used[name] = 1

		####
		attributes = self._attributes.get(xtype, {})
		if type == 'prio':
			attrs = prio_attrs
		elif type == 'foreign':
			attrs = []
			extensions = {ns: 'foreign'}
			for attr, val in x.attrdict.items():
				if attr == 'namespace' or attr == 'elemname':
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

		####
		regionName = None
		nodeid = None
		transIn = None
		transOut = None
		fill = None
		hasfill = 0
		for name, func, keyToCheck in attrs:
			if keyToCheck is not None and not x.attrdict.has_key(keyToCheck):
				continue
			value = func(self, x)
			if value and attributes.has_key(name) and value != attributes[name]:				

				if name == 'fill':
					hasfill = 1
					fill = value
				
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
					if value: 
						value = event2xhtml(value)
						value = replacePrevShortcut(value, x)
					 
				if interior:
					if name == 'fillDefault':
						pass
					elif name == 'id':
						attrlist.append((name, value))
						self.ids_written[value] = 1
						nodeid = value
					else:
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
					elif name == 'fill':
						pass
					elif name == 'fit':
						pass
					elif name in ('regPoint', 'regAlign'):
						pass # taken into account indirectly
					elif not name in ('top','left','width','height','right','bottom'):
						attrlist.append((name, value))

		if not hasfill:
			# no fill attr, be explicit about fillDefault value
			fillDefault = MMAttrdefs.getattr(x, 'fillDefault')
			if fillDefault != 'inherit':
				hasfill = 1
				if interior:
					attrlist.append(('fill', fillDefault))
				else:
					fill = fillDefault

		if not nodeid:
			nodeid = 'm' + x.GetUID()
			if interior:
				attrlist.append(('id', nodeid))

		if self.links_target2src.has_key(x):
			self.fixBeginList(x, attrlist)

		# IE seq children must have an explicit dur or an explicit end condition
		parent = x.GetParent()
		if not root and parent.GetType() == 'seq':
			self.adjustSeqTiming(x, root, attrlist)
					
		####
		if interior:
			if mtype in not_xhtml_smil_elements:
				pass # self.showunsupported(mtype)
				
			if ':' in mtype:
				self.writetag(mtype, attrlist)
			else:
				# IE hack first please!
				# set fill = 'freeze' if last visible child has it
				if mtype == 'seq' and not hasfill:
					self.applyFillHint(x, attrlist)
				if mtype == 'seq' and not x.GetChildren():
					self.applyEmptySeqHint(x, attrlist)
				# normal
				self.writetag('t:' + mtype, attrlist)
			self.push()
			for child in x.GetChildren():
				self.writenode(child)
			if self.freezeSyncDict.has_key(x):
				transOut, trnodeid, trregionid = self.freezeSyncDict[x]
				self.writeTransition(None, transOut, trnodeid, nodeid)
			self.pop()

		elif type in ('imm', 'ext', 'brush'):
			if mtype in not_xhtml_smil_elements:
				self.showunsupported(mtype)
			self.writemedianode(x, nodeid, attrlist, mtype, regionName, transIn, transOut, fill)

		elif type != 'animpar':
			raise CheckError, 'bad node type in writenode'

	def writemedianode(self, node, nodeid, attrlist, mtype, regionName, transIn, transOut, fill):
		pushed, regionid = 0, nodeid
		
		if self.needsLayout(node, nodeid, attrlist, mtype, regionName, transIn, transOut, fill):
			# the normal smil path
			# write node layout
			pushed, regionid  = \
				self.writeMediaNodeLayout(node, nodeid, attrlist, mtype, regionName, transIn, transOut, fill)
			# and restrict node to its media rectangle
			self.applyMediaStyle(node, nodeid, attrlist, mtype)
		else:
			# shortcut: merge region and node
			self.applyRegionStyle(node, nodeid, attrlist, mtype, fill)
			regionid = nodeid
				
		# write anchors
		hasAnchors = self.writeAnchors(node, nodeid)
		if hasAnchors:
			attrlist.append(('usemap', '#'+nodeid+'map'))

		# write media node
		sensitive = self.issensitive(node)
		if mtype == 'brush':
			if sensitive:
				self.writetag('a', [('href', '#')])
				self.push()
				self.writetag('div', attrlist)
				self.closehtmltag()
				self.pop()
			elif hasAnchors:
				self.writetag('div', attrlist)
				self.closehtmltag()
			else:
				attrlist.append( ('class','time') )
				self.writetag('div', attrlist)
				self.closehtmltag()

		elif mtype == 'img':
			if sensitive:
				self.writetag('a', [('href', '#')])
				self.push()
				self.writetag(mtype, attrlist)
				self.pop()
			elif hasAnchors:
				self.writetag(mtype, attrlist)
			else:
				self.writetag('t:'+mtype, attrlist)

		elif mtype == 'text' and node.GetType() == 'imm':
			self.removeAttr(attrlist, 'src')
			attrlist.append( ('class','time') )
			self.writetag('div', attrlist)
			self.push()
			self.fp.write('<p>')
			text = string.join(node.GetValues(), '\n')
			if text:
				text = nameencode(text)
				self.fp.write(text[1:-1])
			self.fp.write('</p>')
			self.pop()

		else:
			self.writetag('t:'+mtype, attrlist)
					
		# write not anchors children (animations, etc)
		for child in node.GetChildren():
			type = child.GetType()
			if type != 'anchor':
				self.writenode(child)

		# write transition(s)
		if transIn or transOut:
			targetid = nodeid
			syncid = regionid or nodeid
			if transIn and not transOut:
				self.writeTransition(transIn, None, targetid, syncid)
			elif transOut:
				if transIn:
					self.writeTransition(transIn, None, targetid, syncid)
				freezeSync = None
				if fill == 'freeze':
					freezeSync = self.locateFreezeSyncNode(node)
				if freezeSync is None:
					self.writeTransition(None, transOut, targetid, syncid)
				else:
					self.freezeSyncDict[freezeSync] = transOut, targetid, syncid

		# restore stack
		while pushed:
			self.pop()
			pushed = pushed - 1

	# return true if the node needs its SMIL layout and can not be exported as standalone
	# currently returns true for most of the cases except the trivial ones (backgound image, audio)
	def needsLayout(self, node, nodeid, attrlist, mtype, regionName, transIn, transOut, fill):
		# first clean out cases we don't cover
		sensitive = self.issensitive(node)
		if self.hasTimeChildren(node) or transIn or transOut or mtype=='brush' or sensitive:
			return 1

		if self.hasMultiWindowLayout:
			return 1

		if self.linkssources.has_key(node):
			return 1

		if node in self.animate_nodes:
			return 1

		nodeRegion = node.GetChannel().GetLayoutChannel()
		path = self.getRegionPath(nodeRegion)
		
		# no hierachy deeper than 2
		if path and len(path) > 2:
			return 1

		for region in path:
			if region in self.animate_regions:
				return 1
			z = region.get('z', 0)
			if z > 0:
				return 1

		# check coordinates of region, subregion and mediaregion
		if mtype == 'audio':
			return 0
		region = node.GetChannel().GetLayoutChannel().getPxGeom()
		try:
			geoms = node.getPxGeomMedia()
		except:
			subregion, mediaregion = None, None
		else:
			subregion, mediaregion = geoms
		if subregion != mediaregion:
			return 1
		if region[2] != subregion[2] or region[3] != subregion[3]:
			return 1
		if subregion[0] != 0 or subregion[1] != 0:
			return 1

		return 0

	# translate and write a media node's SMIL layout to XHTML+SMIL
	def writeMediaNodeLayout(self, node, nodeid, attrlist, mtype, regionName, transIn, transOut, fill):
		pushed, regionid = 0, nodeid
		
		nodeRegion = node.GetChannel().GetLayoutChannel()
		path = self.getRegionPath(nodeRegion)
		if not path:
			print 'error: failed to get region path for', regionName
			return pushed, regionid
		assert len(path) > 1, 'logic error'

		# outmost div attr list
		divlist = []

		# outermost region
		currViewport, currMediaRegion = path[0], path[1]
		prevViewport, prevMediaRegion = None, None
		if self.currLayout:
			prevViewport = self.currLayout[0]
			if len(self.currLayout) > 1:
				prevMediaRegion = self.currLayout[1]
		if self.hasMultiWindowLayout:
			currMediaRegion = currViewport
			prevMediaRegion = prevViewport

		# find/compose/set region id
		regionid = self.registerRegionAlias(currMediaRegion)
		self.ids_written[regionid] = 1
		divlist.append(('id', regionid))
		self.node2layout[node] = {'outer':regionid}

		# apply region style
		ft = (prevMediaRegion == currMediaRegion or mtype == 'audio')
		regstyle = self.getRegionStyle(currMediaRegion, forcetransparent = ft)
		if regstyle is not None:
			divlist.append(('style', regstyle))
		divlist.append(('class', 'time'))

		# apply soundLevel
		volume = currMediaRegion.get('soundLevel', None)
		if volume is not None:
			volume = 100.0*string.atof(volume)
			volume = fmtfloat(volume)
			divlist.append(('volume', volume))

		# apply fill
		if fill:
			divlist.append(('fill', fill))
		
		# transfer timing attributes to container div and 
		# traslate SMIL timing rules to IE implementation
		self.resolveMediaNodeTiming(node, nodeid, attrlist, mtype, regionName, transIn, transOut, fill, divlist)
			
		# write outmost div
		self.writetag('div', divlist)
		self.push()
		pushed = pushed + 1

		# write inner hierarchy if it exists
		ix = path.index(currMediaRegion)
		for region in path[ix+1:]:
			id = self.registerRegionAlias(region)
			self.ids_written[id] = 1
			divlist = [('id', id)]
			ft = region in self.currLayout or mtype == 'audio'
			regstyle = self.getRegionStyle(region, forcetransparent = ft)
			divlist.append(('style', regstyle))
			volume = region.get('soundLevel', None)
			if volume is not None:
				volume = 100.0*string.atof(volume)
				volume = fmtfloat(volume)
				self.replaceAttrVal(divlist, 'volume', volume)
				divlist.append(('volume', volume))
			divlist.append(('class', 'time'))
			self.writetag('div', divlist)
			self.push()
			pushed = pushed + 1

		# write media subregion
		subRegGeom, mediaGeom = None, None
		try:
			geoms = node.getPxGeomMedia()
		except:
			geoms = None
		if geoms and mtype != 'audio':
			subRegGeom, mediaGeom = geoms
		if subRegGeom is not None and mediaGeom is not None:
			# possible overrides: fit, z-index, and backgroundColor 
			divlist = [('id', nodeid)]
			fit = MMAttrdefs.getattr(node, 'fit')
			if fit != 'hidden' and node not in self.animate_nodes and not self.hasTimeChildren(node):
				rcparent = nodeRegion.getPxGeom()
				regstyle = self.rc2style_relative(subRegGeom, rcparent, fit=fit)
			else:
				regstyle = self.rc2style(subRegGeom)
			bgcolor = getbgcoloratt(self, node, 'bgcolor')
			if bgcolor: regstyle = regstyle + 'background-color:%s;' % bgcolor
			z = self.removeAttr(attrlist, 'z-index')
			if z is not None: 
				regstyle = regstyle + 'z-index:%s;' % z
			divlist.append(('style', regstyle))
			divlist.append(('class', 'time'))
			self.writetag('div', divlist)
			self.push()
			pushed = pushed + 1
			attrlist.insert(0, ('id', nodeid + '_m'))
		else:
			attrlist.insert(0, ('id', nodeid))
			
		# save current layout and return
		self.currLayout = path
		return pushed, regionid
	
	def registerRegionAlias(self, region):
		name = self.ch2name[region]
		alias = self.regions_alias.get(region)
		if alias is None:
			regionid = name
			self.regions_alias[region] = [regionid,]
		else:
			counter = len(alias)+1
			regionid = name + '_%d' % counter
			self.regions_alias[region].append(regionid)
		return regionid
			
	# transfer timing attributes to container div and 
	# traslate SMIL timing rules to IE implementation
	def resolveMediaNodeTiming(self, node, nodeid, attrlist, mtype, regionName, transIn, transOut, fill, divlist):
		# first, transfer direct timing attributes to container div 
		pardur = None
		timing_spec = 0 				
		has_end = 0 				
		i = 0
		while i < len(attrlist):
			attr, val = attrlist[i]
			if attr in ('begin', 'dur', 'end', 'repeatDur'): 
				timing_spec = timing_spec + 1
				divlist.append((attr, val))
				del attrlist[i]
				if attr == 'dur' or  attr == 'repeatDur':
					pardur = val
				if attr == 'end':
					has_end = 1
			elif attr == 'repeatCount': 
				divlist.append((attr, val))
				del attrlist[i]
			else:
				i = i + 1

		# and second, traslate SMIL timing rules to IE implementation
		# XXX: this is far from complete yet
		parent = node.GetParent()
		if pardur is None and timing_spec < 2:
			parentDur = parent.GetRawAttrDef('duration', None)
			if parent.GetType() == 'par' and parentDur is not None and fill is None and mtype!='audio':
				# force smil default behavior in such cases
				divlist.append(('fill', 'freeze'))

		# when div has timing extent it to a time container
		divlist.append( ('timeContainer', 'par'))

	def adjustSeqTiming(self, x, root, attrlist):
		# XXX: IE seq children must have an explicit dur or an explicit end condition
		# XXX: must be done globally and correctly before start writing
		# this needs a custom scheduler/timing resolver to be implemented correctly
		# node.GetTimes() section implements one but seems not to be appropriate
		parent = x.GetParent()
		if not root and parent.GetType() == 'seq':
			d = x.attrdict
			hasendcond = d.get('duration') or d.get('repeatdur') or d.get('endlist')
			if not hasendcond:
				next = self.getNextSibling(x)
				if next:
					dur = self.getDurHint(x)
					if not dur or dur < 0.0: 
						if x.GetType() not in interiortypes:
							dur = 1.0
					if dur and dur > 0.0:
		 				dur = fmtfloat(dur, prec = 2)
						attrlist.append(('dur', dur))
						self.seqtimingfixes[x] = dur
			previous =  self.getPreviousSibling(x)
			fix = self.seqtimingfixes.get(previous)
			if previous and fix:
				# XXX: of course should be changed
				val = self.removeAttr(attrlist, 'begin')
				if val:
					try:
						diff = string.atof(val) - string.atof(fix)
					except:
						pass
					else:
						if diff > 0.0:
							attrlist.append(('begin', fmtfloat(diff, prec = 2)))

	def applyEmptySeqHint(self, x, attrlist):
		d = x.attrdict
		hasendcond = d.get('duration') or d.get('repeatdur') or d.get('endlist')
		if not hasendcond:
			attrlist.append(('dur', '0'))

	def applyMediaStyle(self, node, nodeid, attrlist, mtype):
		subRegGeom, mediaGeom = None, None
		try:
			geoms = node.getPxGeomMedia()
		except:
			geoms = None
		if geoms and mtype != 'audio':
			subRegGeom, mediaGeom = geoms
		if mediaGeom:
			fit = MMAttrdefs.getattr(node, 'fit')
			if fit == 'hidden':
				style = self.rc2style(mediaGeom)
			else: 
				style = self.rc2style_relative(mediaGeom, subRegGeom)
			if mtype == 'brush':
				color = self.removeAttr(attrlist, 'color')
				if color is not None:
					style = style + 'background-color:%s;' % color
			attrlist.append( ('style', style) )

	# used when no layout is needed for a media node
	def applyRegionStyle(self, node, nodeid, attrlist, mtype, fill):
		nodeRegion = node.GetChannel().GetLayoutChannel()
		
		if mtype != 'audio':
			fit = MMAttrdefs.getattr(node, 'fit')
			z = self.removeAttr(attrlist, 'z-index')
			style = self.getRegionStyle(nodeRegion, fit = fit, inczindex = (z is None))
			if z is not None:
				style = style + 'z-index:%s;' % z
			attrlist.append(('style', style))
			
		# apply soundLevel
		volume = nodeRegion.get('soundLevel', None)
		if volume is not None:
			volume = 100.0*string.atof(volume)
			volume = fmtfloat(volume)
			attrlist.append(('volume', volume))
			
		# apply fill
		if fill:
			attrlist.append(('fill', fill))
			
		# register nodeid as region alias
		id = self.registerRegionAlias(nodeRegion)
		attrlist.insert(0, ('id', nodeid))
		
	def getNodeMediaRect(self, node):
		subRegGeom, mediaGeom = None, None
		try:
			geoms = node.getPxGeomMedia()
		except:
			return 0, 0, 100, 100
		else:
			subRegGeom, mediaGeom = geoms
			x, y, w, h = subRegGeom
			xm, ym, wm, hm = mediaGeom
			return 0, 0, wm, hm

	def writeTransition(self, transIn, transOut, nodeid, regionid):
		transitions = self.root.GetContext().transitions
		quotedname = transIn or transOut
		try:
			name = self.name2transition[quotedname]
		except Exception, arg:
			print arg
			name = quotedname
		td = transitions.get(name)
		if not td:
			trtype = None
			subtype = None
			dur = 1.0
			direction = 'forward'
			startProgress = 0.0
			endProgress = 1.0
		else:
			trtype = td.get('trtype', 'barWipe')
			subtype = td.get('subtype')
			dur = td.get('dur', 1.0)
			direction = td.get('direction', 'forward')
			startProgress = td.get('startProgress', 0.0)
			endProgress = td.get('endProgress', 1.0)
		trtype, subtype = IETransition(trtype, subtype)
		if dur<=0: dur = 0.1
		trattrlist = []
		trattrlist.append( ('type', trtype) )
		if subtype is not None:
			trattrlist.append( ('subtype',subtype) )
		trattrlist.append( ('targetElement',nodeid) )
		trattrlist.append( ('dur','%s' % fmtfloat(dur)) )
		if transIn:
			trattrlist.append( ('begin', regionid + '.begin') )
			trattrlist.append( ('mode', 'in') )
		elif transOut:
			trattrlist.append( ('begin', regionid + '.end-%s' % fmtfloat(dur)) )
			trattrlist.append( ('mode', 'out') )
		sv1 = fmtfloat(startProgress)
		sv2 = fmtfloat(endProgress)
		if direction == 'reverse':
			trattrlist.append( ('from', sv2) )
			trattrlist.append( ('to', sv1) )
		else:
			trattrlist.append( ('from', sv1) )
			trattrlist.append( ('to', sv2) )
		self.writetag('t:transitionFilter', trattrlist)

	def hasTimeChildren(self, node):
		for child in node.GetChildren():
			type = child.GetType()
			if type != 'anchor':
				return 1
		return 0

	def hasAnimateMotionChildren(self, node):
		for child in node.GetChildren():
			if child.GetType() == 'animate' and child.attrdict.get('atag') == 'animateMotion':
				return 1
		return 0

	def removeAttr(self, attrlist, attrname):
		val = None
		i = 0
		while i < len(attrlist):
			a, v = attrlist[i]
			if a == attrname:
				val = v
				del attrlist[i]
				break
			i = i + 1
		return val

	def replaceAttrVal(self, attrlist, attrname, attrval):
		val = None
		for i in range(len(attrlist)):
			a, v = attrlist[i]
			if a == attrname:
				attrlist[i] = attrname, attrval
				val = v
				break
		if val is None:
			if attrname == 'id':
				attrlist.insert(0, (attrname, attrval))
			else:
				attrlist.append((attrname, attrval))	
		return val

	# set fill = 'freeze' if last visible child has it
	def applyFillHint(self, x, attrlist):
		if x.GetChildren():
			children = x.GetChildren()[:]
			children.reverse()
			for i in range(len(children)):
				last = children[i]
				if last.GetType() != 'audio':
					lastfill = MMAttrdefs.getattr(last, 'fill')
					if lastfill == 'freeze':
						attrlist.append( ('fill', 'freeze') )
					break

	def locateFreezeSyncNode(self, node):
		# XXX: find freeze sync
		parent = node.GetParent()
		if parent.GetType() == 'seq':
			return parent.GetParent()

 	def getDurHint(self, node):
		try:
 			t0, t1, t2, downloadlag, begindelay = node.GetTimes()
 			val = t1 - t0
 		except: 
 			return -1
		else:
 			return val

	def fixBeginList(self, node, attrlist):
		srcid = self.links_target2src.get(node)
		if srcid is None:
			return
		bl = self.removeAttr(attrlist, 'begin')
		if bl is None:
			parent = node.GetParent()
			if parent.GetType() == 'par':
				bl = '0;%s.click' % srcid
				attrlist.append(('begin', bl))
			elif parent.GetType() == 'seq':
				prev = self.getPreviousSibling(node)
				if prev is not None:
					previd = identify(self.getNodeId(prev))
					bl = '%s.end;%s.click' % (previd, srcid)
				else:
					bl = '0;%s.click' % srcid
				attrlist.append(('begin', bl))
		else:
			if bl[-1] != ';':
				bl = bl + ';'
			bl = bl = '%s.click' % srcid
			attrlist.append(('begin', bl))


	def toPxStr(self, c, d):
		if type(c) is type(0):
			# pixel coordinates
			return '%d' % c
		else:
			# relative coordinates
			return '%d' % round(c*d)

	def toPixelCoordsStrs(self, ashape, acoords, width, height):
		relative = 0
		coords = []
		for c in acoords:
			if type(c) is type(0):
				coords.append('%d' % c)
			else:
				relative = 1
				break
		if not relative:
			return coords
		toPxStr = self.toPxStr
		if ashape == 'rect' or ashape == 'rectangle':
			l, t, r, b = acoords
			coords = [toPxStr(l, width), toPxStr(t, height), toPxStr(r, width), toPxStr(b, height)]
		elif ashape == 'circ' or ashape == 'circle':
			xc, yc, r = acoords
			coords = [toPxStr(xc, width), toPxStr(yc, height), toPxStr(r, (width+height)/2)]
		else: # elif ashape == 'poly':
			i = 0
			while i < len(acoords)-1:
				x, y = toPxStr(acoords[i], width), toPxStr(acoords[i+1], height)
				coords.append(x)
				coords.append(y)
				i = i + 2
		return coords

	def fixurl(self, url):
		ctx = self.context
		if self.convertURLs:
			url = MMurl.canonURL(ctx.findurl(url))
			if url[:len(self.convertURLs)] == self.convertURLs:
				url = url[len(self.convertURLs):]
		return url
	
	def writeAnchors(self, node, name):
		hassrc = 0
		x, y, w, h = 0, 0, 1, 1
		for anchor in node.GetChildren():
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
				x, y, w, h = self.getNodeMediaRect(node)
				self.writetag('map', [('id', name+'map')])
				self.push()
			a1, a2, dir = links[0]
			attrlist = []
			id = getid(self, anchor)
			if id is None:
				id = 'a' + node.GetUID()
			attrlist.append(('id', id))
			if type(a2) is type(''):
				attrlist.append(('href', a2))
			else:
				target =  self.uid2name[a2.GetUID()]
				attrlist.append(('href', '#%s' % target))
				# attrlist.append(('onclick', '%s.beginElement();' % target))
			show = MMAttrdefs.getattr(anchor, 'show')
			if show != 'replace':
				attrlist.append(('show', show))
			sstate = MMAttrdefs.getattr(anchor, 'sourcePlaystate')
			if show != 'new' or sstate != 'play':
				attrlist.append(('sourcePlaystate', sstate))
			dstate = MMAttrdefs.getattr(anchor, 'destinationPlaystate')
			if dstate != 'play':
				attrlist.append(('destinationPlaystate', dstate))
			fragment = MMAttrdefs.getattr(anchor, 'fragment')
			if fragment:
				attrlist.append(('fragment', fragment))

			shape = MMAttrdefs.getattr(anchor, 'ashape')
			attrlist.append(('shape', shape))

			acoords =  MMAttrdefs.getattr(anchor, 'acoords')
			if not acoords:
				acoords = [x, y, x+w, y+h]
			coords = self.toPixelCoordsStrs(shape, acoords, w, h)
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
				attrlist.append(('accesskey', accesskey))

			self.writetag('area', attrlist)
			self.closehtmltag(0)

		if hassrc:
			self.pop()
		return hassrc
				
	def writeEmptyRegion(self, region):
		if region is None:
			return
		path = self.getRegionPath(region)
		if not path:
			print 'failed to get region path for', region
			return

		# region (div) attr list
		divlist = []

		# find/compose/set region id
		name = self.ch2name[region]
		self.ids_written[name] = 1
		self.regions_alias[region] = [name,]
		divlist.append(('id', name))

		# apply region style and fill attribute
		regstyle = self.getRegionStyle(region)
		if regstyle is not None:
			divlist.append(('style', regstyle))
		divlist.append(('class', 'time'))
							
		# finally write div
		self.writetag('div', divlist)
		self.closehtmltag()

	def writeanimatenode(self, node, root):
		attrlist = []
		animvalattrs = ('from', 'to', 'by', 'values', 'path')
		tag = node.GetAttrDict().get('atag')

		target = None
		targetElement = None
		attributeName = None
		hasid = 0
		hasfill = 0

		if tag == 'animateMotion':
			from Animators import AnimateElementParser
			aparser = AnimateElementParser(node, self.__animateContext)
			isAdditive = aparser.isAdditive()
			fromxy = aparser.toDOMOriginPosAttr('from')
			toxy = aparser.toDOMOriginPosAttr('to')
			values = aparser.toDOMOriginPosValues()
			path = aparser.toDOMOriginPath()
		elif tag == 'animateColor':
			from Animators import AnimateElementParser
			aparser = AnimateElementParser(node, self.__animateContext)
			fromcr = aparser.convertColorValue(node.attrdict.get('from'))
			tocr = aparser.convertColorValue(node.attrdict.get('to'))
			bycr = aparser.convertColorValue(node.attrdict.get('by'))
			valuescr = aparser.convertColorValues(node.attrdict.get('values'))
		attributes = self._attributes.get(tag, {})
		for name, func, gname in smil_attrs:
			if attributes.has_key(name):
				if name == 'type':
					value = node.GetRawAttrDef("trtype", None)
				else:
					value = func(self, node)
				if name == 'targetElement' and value and value != attributes[name]:
					target = node.targetnode
					if target:
						if target.getClassName() in ('Region', 'Viewport'):
							targetElement = self.ch2name[target]
						else:
							targetElement = self.getNodeId(target)
							if tag == 'transitionFilter':
								targetElement = targetElement + '_m'	
						value = targetElement
					else:
						targetElement = value
				if value and value != attributes[name]:
					if name in ('begin', 'end'):
						value = event2xhtml(value)
						value = replacePrevShortcut(value, node)
					elif name == 'keySplines':
						vals = value.split(';')
						value = ''
						for s in vals:
							l = tokenizer.splitlist(s)
							value = value + ' '.join(l) + ';'
					elif name == 'id':
						hasid = 1
					elif name == 'fill':
						hasfill = 1
					elif name == 'attributeName':
						attributeName = value
					elif name in animvalattrs and tag == 'animateMotion' and not isAdditive:
						if name == 'from': value = fromxy
						elif name == 'to': value = toxy
						elif name == 'values': value = values
						elif name == 'path': value = path
					elif name in animvalattrs and tag == 'animateColor':
						if name == 'from': value = fromcr
						elif name == 'to': value = tocr
						elif name == 'by': value = bycr
						elif name == 'values': value = valuescr
					attrlist.append((name, value))
		if not hasid:
			id = 'm' + node.GetUID()
			attrlist.insert(0, ('id', id))
		if not hasfill:
			# no fill attr, be explicit about fillDefault value
			fillDefault = MMAttrdefs.getattr(node, 'fillDefault')
			if fillDefault != 'inherit':
				attrlist.append(('fill', fillDefault))

		# write it
		if target is None or target.getClassName() not in ('Region', 'Viewport'):
			if attributeName == 'z-index':
				ld = self.node2layout.get(target)
				if ld is not None and ld.has_key('outer'):
					self.replaceAttrVal(attrlist, 'targetElement', ld.get('outer'))
			self.writetag('t:'+tag, attrlist)
		else:
			# region animation
			if not self.regions_alias.get(target):
				self.writeEmptyRegion(target)
			for name in self.regions_alias[target]:
				self.replaceAttrVal(attrlist, 'targetElement', name)				
				self.writetag('t:'+tag, attrlist)
	
	def getLayoutStyle(self):
		x, y = 20, 20
		xmargin, ymargin = 20, 20
		v = self.top_levels[0]
		tw, th = v.getPxGeom()
		for v in self.top_levels[1:]:
			tw = tw + xmargin
			w, h = v.getPxGeom()
			tw = tw + w
		style = 'position:absolute;overflow:hidden;left:%d;top:%d;width:%d;height:%d;' % (x, y, tw, th)
		return style
			
	def getViewportOffset(self, viewport):
		x, y = 0, 0
		xmargin, ymargin = 20, 20
		viewports = self.top_levels
		try:
			index = viewports.index(viewport)
		except:
			index = 0
		for i in range(index):
			v = viewports[0]
			w, h = v.getPxGeom()
			x = x + w + xmargin
		return x, y

	def getViewportStyle(self, viewport, forcetransparent = 0):
		x, y = self.getViewportOffset(viewport)
		w, h = viewport.getPxGeom()
		style = 'position:absolute;overflow:hidden;left:%d;top:%d;width:%d;height:%d;' % (x, y, w, h)
		if not forcetransparent:
			if viewport.has_key('bgcolor'):
				bgcolor = viewport['bgcolor']
			else:
				bgcolor = 255,255,255
			if colors.rcolors.has_key(bgcolor):
				bgcolor = colors.rcolors[bgcolor]
			else:
				bgcolor = '#%02x%02x%02x' % bgcolor
			style = style + 'background-color:%s;' % bgcolor
		return style

	# used by getRegionStyle
	def getRegionSizeSpecs(self, region, names):
		l, w, r = names
		specs = {}
		for name in names:
			s = ''
			value = region.GetAttrDef(name, None)
			if type(value) == type(0.0):
				s = '%d%%' % int(value * 100 + .5)
			elif type(value) == type(0):
				s = '%d' % value
			if s:
				specs[name] = s
			if len(specs) > 1:
				break;
		if len(specs) == 0:
			specs[l] = '0'
			specs[w] = '100%'
		elif len(specs) == 1:
			if specs.has_key(l):
				specs[r] = '0%'
			elif specs.has_key(r):
				specs[l] = '0'
			else:
				specs[l] = '0'
		return specs

	def getRegionStyle(self, region, forcetransparent = 0, fit='hidden',  inczindex = 1):
		if region in self.top_levels:
			return self.getViewportStyle(region, forcetransparent)
		style = 'position:absolute;overflow:%s;' % self.getoverflow(fit)
		if region in self.animate_regions or self.hasMultiWindowLayout:
			x, y, w, h = region.getPxGeom()
			style = style + 'left:%d;top:%d;width:%d;height:%d;' % (x, y, w, h)
		else:	
			specs = self.getRegionSizeSpecs(region, ('left', 'width', 'right'))	
			specs.update(self.getRegionSizeSpecs(region, ('top', 'height', 'bottom')))
			if specs.get('right') or specs.get('bottom'):
				# IE seems to have problems with 'right', 'bottom'
				x, y, w, h = region.getPxGeom()
				style = style + 'left:%d;top:%d;width:%d;height:%d;' % (x, y, w, h)
			else:
				for name in ('left', 'top', 'width', 'height', 'right', 'bottom'):
					value = specs.get(name)
					if value is not None:
						style = style + name + ':' + value + ';'
		transparent = region.get('transparent', None)
		bgcolor = region.get('bgcolor', None)
		if bgcolor and transparent==0 and not forcetransparent:
			if colors.rcolors.has_key(bgcolor):
				bgcolor = colors.rcolors[bgcolor]
			else:
				bgcolor = '#%02x%02x%02x' % bgcolor
			style = style + 'background-color:%s;' % bgcolor
		if inczindex:
			z = region.get('z', 0)
			if z > 0:
				style = style + 'z-index:%d;' % z
		return style

	def rc2style(self, rc, fit = 'hidden'):
		x, y, w, h = rc
		overflow = self.getoverflow(fit)
		return 'position:absolute;overflow:%s;left:%d;top:%d;width:%d;height:%d;' % (overflow, x, y, w, h)

	def rc2style_relative(self, rc, rcref, fit = 'hidden'):
		x, y, w, h = rc
		width, height = float(rcref[2]), float(rcref[3])
		if x:
			x = 100.0*(x/width)
			x = fmtfloat(x, prec = 2, suffix = '%')
		else:
			x = '0' 
		if y:
			y = 100.0*(y/height)
			y = fmtfloat(y, prec = 2, suffix = '%')
		else:
			y = '0' 
		w, h = 100.0*(w/width), 100.0*(h/height)
		w, h = fmtfloat(w, prec = 2, suffix = '%'), fmtfloat(h, prec = 2, suffix = '%')
		overflow = self.getoverflow(fit)
		return 'position:absolute;overflow:%s;left:%s;top:%s;width:%s;height:%s;' % (overflow, x, y, w, h)

	def rc2style_sizerelative(self, rc, rcref, fit = 'hidden'):
		x, y, w, h = rc
		width, height = float(rcref[2]), float(rcref[3])
		w, h = 100.0*(w/width), 100.0*(h/height)
		w, h = fmtfloat(w, prec = 2, suffix = '%'), fmtfloat(h, prec = 2, suffix = '%')
		overflow = self.getoverflow(fit)
		return 'position:absolute;overflow:%s;left:%d;top:%d;width:%s;height:%s;' % (overflow, x, y, w, h)

	def getoverflow(self, fit):
		# overflow in ('visible', 'scroll', 'hidden', 'auto')
		# valid for us are: 'hidden', 'auto'
		overflow = 'hidden'
		if fit == 'fill':
			overflow = 'hidden'
		elif fit == 'hidden':
			overflow = 'hidden'
		elif fit == 'meet':
			overflow = 'hidden'
		elif fit == 'scroll':
			overflow = 'auto'
		elif fit == 'slice':
			overflow = 'hidden'
		return overflow

	def getRegionPath(self, region):
		path = []
		while region:
			if region.get('type') == 'layout':
				path.insert(0, region)
			region = region.GetParent()
		return path
		
	def getRegionViewport(self, region):
		path = self.getRegionPath(region)
		if path:
			return path[0]
		return None

	def getNodeViewport(self, node):
		region = node.GetChannel().GetLayoutChannel()
		return self.getRegionViewport(region)

	# temporal for writing empty regions 
	# XXX: should be avoided 
	def getRegionFromName(self, regionName):
		region = self.context.getchannel(regionName)
		if region is None:
			regionName = self.chnamedict.get(regionName)
			region = self.context.getchannel(regionName)
		return region

	def getPreviousSibling(self, node):
		parent = node.GetParent()
		prev = None
		for child in parent.GetChildren():
			if child == node:
				break
			prev = child
		return prev

	def getNextSibling(self, node):
		parent = node.GetParent()
		next = None
		children = parent.GetChildren()
		n = len(children)
		for i in range(n-1):
			child = children[i]
			if child == node:
				next = children[i+1]
		return next

	def getNodeId(self, node):
		id = node.GetRawAttrDef('name', None)
		if not id:
			id = 'm' + node.GetUID()
		return id

	#
	#
	#
	def buildSensitivityList(self, parent, sensitivityList):
		for node in parent.children:
			for arc in node.attrdict.get('beginlist', []) + node.attrdict.get('endlist', []):
				if arc.event == 'activateEvent':
					sensitivityList.append(arc.srcnode)
			self.buildSensitivityList(node, sensitivityList)

	def buildTargets(self, node):
		ntype = node.GetType()
		interior = (ntype in interiortypes)
		if interior:
			for child in node.GetChildren():
				self.buildTargets(child)
		elif ntype in ('imm', 'ext', 'brush'):
			for anchor in node.GetChildren():
				if anchor.GetType() != 'anchor':
					continue
				links = self.hyperlinks.findsrclinks(anchor)
				if not links:
					continue
				a1, a2, dir = links[0]
				id = getid(self, anchor)
				if id is None:
					id = 'a' + node.GetUID()
				if type(a2) is not type(''):
					self.links_target2src[a2] = id
					self.linkssources[node] = 1
		elif ntype == 'animate':
			target = node.targetnode
			if target:
				motion = node.attrdict.get('atag') == 'animateMotion'
				if target.getClassName() in ('Region', 'Viewport'):
					self.animate_regions.append(target)			 
					if motion: self.animate_motion_regions.append(target)
				else:	
					if node.attrdict.get('attributeName') != 'z-index':
						self.animate_nodes.append(target)
					if motion: self.animate_motion_nodes.append(target)

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
				self.chnamedict[name] = ch.name
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
				self.chnamedict[name] = ch.name

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
	if not value: 
		return value
	for ev in smil20event2xhtml.keys():
		value = value.replace(ev, smil20event2xhtml[ev])
	return value

def replacePrevShortcut(value, node):
	if value.find('prev.') != 0:
		return value
	parent = node.GetParent()
	prev = parent
	for child in parent.GetChildren():
		if child == node:
			break
		prev = child
	id = prev.GetRawAttrDef('name', None)
	if not id:
		id = 'm' + prev.GetUID()
	return id + value[4:]
	
#
#  IE inline transitions 
#  implemented types, subtypes by IE
#  explicit mapping of non implemented to implemented
#
TRANSITIONDICT = {
	##################################
	# Edge Wipes - wipes occur along an edge
	('barWipe', None) : ('barWipe', 'leftToRight'),
	('barWipe', 'leftToRight') : ('barWipe', 'leftToRight'),
	('barWipe', 'topToBottom') : ('barWipe', 'topToBottom'),

	('barnDoorWipe', None) : ('barnDoorWipe', 'horizontal'),
	('barnDoorWipe', 'horizontal') : ('barnDoorWipe', 'horizontal'),
	('barnDoorWipe', 'vertical') : ('barnDoorWipe', 'vertical'),

	# Edge Wipes simulations
	('boxWipe', None) : ('barWipe', 'leftToRight'),
	('fourBoxWipe', None) : ('barWipe', 'leftToRight'),
	('diagonalWipe', None) : ('barWipe', 'leftToRight'),
	('bowTieWipe', None) : ('barWipe', 'leftToRight'),
	('miscDiagonalWipe', None) : ('barWipe', 'leftToRight'),
	('veeWipe', None) : ('barWipe', 'leftToRight'),
	('barnVeeWipe', None) : ('barWipe', 'leftToRight'),
	('zigZagWipe', None) : ('barWipe', 'leftToRight'),
	('barnZigZagWipe', None) : ('barWipe', 'leftToRight'),

	##################################
	# Iris Wipes - shapes expand from the center of the media	
	('irisWipe', None) : ('irisWipe', 'rectangle'),
	('irisWipe', 'rectangle') : ('irisWipe', 'rectangle'),
	('irisWipe', 'diamond') : ('irisWipe', 'diamond'),

	('starWipe', None) : ('starWipe', 'fivePoint'),
	('starWipe', 'fivePoint') : ('starWipe', 'fivePoint'),

	('ellipseWipe', None) : ('ellipseWipe', 'circle'),
	('ellipseWipe', 'circle') : ('ellipseWipe', 'circle'),

	# Iris Wipes simulations	
	('triangleWipe', None) : ('starWipe', 'fivePoint'),
	('arrowHeadWipe', None) : ('irisWipe', 'diamond'),
	('pentagonWipe', None) : ('starWipe', 'fivePoint'),
	('hexagonWipe', None) : ('starWipe', 'fivePoint'),
	('eyeWipe', None) : ('ellipseWipe', 'circle'),
	('roundRectWipe', None) : ('ellipseWipe', 'circle'),
	('miscShapeWipe', None) : ('irisWipe', 'rectangle'),

	##################################
	# Clock Wipes - rotate around a center point
	('clockWipe', None) : ('clockWipe', 'clockwiseTwelve'),
	('clockWipe', 'clockwiseTwelve') : ('clockWipe', 'clockwiseTwelve'),

	('fanWipe', None) : ('fanWipe', 'centerTop'),
	('fanWipe', 'centerTop') : ('fanWipe', 'centerTop'),

	# Clock Wipes simulations
	('pinWheelWipe', None) : ('fanWipe', 'centerTop'),
	('singleSweepWipe', None) : ('fanWipe', 'centerTop'),
	('doubleFanWipe', None) : ('fanWipe', 'centerTop'),
	('saloonDoorWipe', None) : ('fanWipe', 'centerTop'),
	('windshieldWipe', None) : ('fanWipe', 'centerTop'),
	
	##################################
	# Matrix Wipes - media is revealed in squares following a pattern
	('snakeWipe', None) : ('snakeWipe', 'topLeftHorizontal'),
	('snakeWipe', 'topLeftHorizontal') : ('snakeWipe', 'topLeftHorizontal'),

	('spiralWipe', None) : ('spiralWipe', 'topLeftClockwise'),
	('spiralWipe', 'topLeftClockwise') : ('spiralWipe', 'topLeftClockwise'),

	# Matrix Wipes simulations
	('parallelSnakesWipe', None) : ('snakeWipe', 'topLeftHorizontal'),
	('boxSnakesWipe', None) : ('snakeWipe', 'topLeftHorizontal'),
	('waterfallWipe', None) : ('snakeWipe', 'topLeftHorizontal'),

	##################################
	# Non-SMPTE Wipes
	('pushWipe', None) : ('pushWipe', 'fromLeft'),
	('pushWipe', 'fromLeft') : ('pushWipe', 'fromLeft'),

	('slideWipe', None) : ('slideWipe', 'fromLeft'),
	('slideWipe', 'fromLeft') : ('slideWipe', 'fromLeft'),

	('fade', None) : ('fade', 'crossfade'),
	('fade', 'crossfade') : ('fade', 'crossfade'),
	} # end TRANSITIONDICT

NullTransition  = 'fade', 'crossfade'

def IETransition(trtype, subtype):
	# Return the class that implements this transition. 
	if TRANSITIONDICT.has_key((trtype, subtype)):
		return TRANSITIONDICT[(trtype, subtype)]
	if TRANSITIONDICT.has_key((trtype, None)):
		return TRANSITIONDICT[(trtype, None)]
	return NullTransition

