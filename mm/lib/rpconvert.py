__version__ = "$Id$"

import MMurl, realsupport
import posixpath
from MMNode import MMSyncArc
from Hlinks import DIR_1TO2, TYPE_FORK, A_SRC_PLAY, A_DEST_PLAY, ANCHOR2

def rpconvert(node, errorfunc = None):
	# convert a RealPix node into a par node with children,
	# together representing the RealPix node
	ctx = node.GetContext()
	# check that node is a RealPix node
	furl = node.GetAttr('file')
	if node.GetType() != 'ext' or not furl:
		if errorfunc is not None: errorfunc('not a RealPix node')
		return
	ch = node.GetChannel()
	if not ch:
		if errorfunc is not None: errorfunc('no region associated with node')
		return
	url = ctx.findurl(furl)
	if furl[:5] == 'data:':
		furl = ''
	try:
		f = MMurl.urlopen(url)
	except IOError:
		if errorfunc is not None: errorfunc('cannot open RealPix file')
		return
	head = f.read(4)
	if head != '<imf':
		if errorfunc is not None: errorfunc('not a RealPix file')
		f.close()
		return

	# parse the RealPix file, result in rp
	rp = realsupport.RPParser(url)
	rp.feed(head)
	rp.feed(f.read())
	f.close()
	rp.close()

	region = ch.GetLayoutChannel()
	regionname = region.name
	
	em = ctx.editmgr
	if not em.transaction():
		# not allowed to do it at this point
		return

	ctx.attributes['project_boston'] = 1 # It's definitely a SMIL 2.0 document now

	# convert the ext node to a par node
	em.setnodeattr(node, 'file', None)
	em.setnodetype(node, 'seq')
	em.setnodeattr(node, 'channel', None)
	em.setnodeattr(node, 'bgcolor', None)
	em.setnodeattr(node, 'transparent', None)
	if node.GetAttrDef('fill', 'default') == 'default' and node.GetInherAttrDef('fillDefault', 'inherit') == 'inherit':
		# make default fill behavior explicit
		em.setnodeattr(node, 'fill', node.GetFill())
	em.setnodeattr(node, 'fillDefault', 'hold')
	ndur = node.GetAttrDef('duration', None)
	if ndur is None:
		ndur = rp.duration
	else:
		ndur = min(ndur, rp.duration)
	em.setnodeattr(node, 'duration', ndur)
	em.setchannelattr(regionname, 'chsubtype', None)

	# First deal with fadein transitions that specify an
	# associated fadeout.  We just create an explicit fadeout for
	# these associated fadeouts, keeping the list of transitions
	# sorted (and the start attribute relative to the previous).
	# The result is a new list of transitions in tags.
	start = 0
	i = 0
	fadeouts = []
	tags = []
	for tagdict in rp.tags:
		prevstart = start
		start = start + tagdict['start']
		while fadeouts:
			fodict = fadeouts[0]
			if fodict['start'] < start:
				tags.append(fodict)
				fodict['start'], prevstart = fodict['start'] - prevstart, fodict['start']
				del fadeouts[0]
			else:
				break
		tagdict['start'] = start - prevstart
		tags.append(tagdict)
		if tagdict['tag'] == 'fadein' and tagdict.get('fadeout', 0):
			fodict = tagdict.copy()
			fodict['tag'] = 'fadeout'
			fodict['start'] = start + tagdict['fadeouttime']
			fodict['tduration'] = tagdict['fadeoutduration']
			fodict['color'] = tagdict['fadeoutcolor']
			del fodict['fadeouttime']
			del fodict['fadeoutduration']
			del fodict['fadeout']
			del fodict['fadeoutcolor']
			for j in range(len(fadeouts)):
				if fadeouts[j]['start'] > fodict['start']:
					fadeouts.insert(j, fodict)
					break
			else:
				fadeouts.append(fodict)
	prevstart = start
	for fodict in fadeouts:
		tags.append(fodict)
		fodict['start'], prevstart = fodict['start'] - prevstart, fodict['start']

	# width and height of the region
	# this had better be in pixels
	rw, rh = region.getPxGeom()[2:]
	i = 0				# used to create unique channel name
	start = 0
	for tagdict in tags:
		transition = tagdict['tag']
		start = tagdict.get('start', 0) + start
		if transition in ('viewchange', 'animate'):
			if errorfunc is not None: errorfunc("ignoring transition we can't convert")
			continue
		if transition in ('fadeout', 'fill'):
			chtype = 'brush'
			newnode = ctx.newnode('brush')
			em.addnode(node, -1, newnode)
			em.setnodeattr(newnode, 'fgcolor', tagdict['color'])
		else:
			chtype = 'image'
			newnode = ctx.newnode('ext')
			em.addnode(node, -1, newnode)
			em.setnodeattr(newnode, 'file', MMurl.basejoin(furl, tagdict['file']))
			if tagdict.get('aspect', rp.aspect == 'true'):
				em.setnodeattr(newnode, 'fit', 'meet')
			else:
				em.setnodeattr(newnode, 'fit', 'fill')
			base = posixpath.splitext(posixpath.split(tagdict['file'])[1])[0]
			em.setnodeattr(newnode, 'name', base)
			# As this item comes from a RealPix file it should
			# be ready for Real playback
			em.setnodeattr(newnode, 'project_convert', 0)

		# calculate subregion positioning
		# first work in source (RealPix) coordinates
		if tagdict.get('displayfull', 0):
			x, y, w, h = 0, 0, rp.width, rp.height
		else:
			x, y = tagdict.get('subregionxy', (0, 0))
			w, h = tagdict.get('subregionwh', (0, 0))
			# they really default to the size of the window
			if w == 0:
				w = rp.width
			if h == 0:
				h = rp.height
		# if size too big, reduce to RealPix size
		if w > rp.width:
			w = rp.width
		if h > rp.height:
			h = rp.height
		# if the destination area doesn't fit, it is shifted up and left to make it fit
		if x + w > rp.width:
			x = rp.width - w
		if y + h > rp.height:
			y = rp.height - h
		# convert to destination (SMIL 2.0) coordinates
		x = int((float(x) / rp.width) * rw + 0.5)
		w = int((float(w) / rp.width) * rw + 0.5)
		y = int((float(y) / rp.height) * rh + 0.5)
		h = int((float(h) / rp.height) * rh + 0.5)

		em.setnodeattr(newnode, 'left', x)
		em.setnodeattr(newnode, 'top', y)
		em.setnodeattr(newnode, 'width', w)
		em.setnodeattr(newnode, 'height', h)
		em.setnodeattr(newnode, 'regPoint', 'center')
		em.setnodeattr(newnode, 'regAlign', 'center')
		# XXX to be compatible with RealPix, the background
		# should not be transparent and be transitioned in
		# together with the image.  However, that's not so
		# easy in SMIL 2.0.  We'd need a coordinated
		# transition of a brush to represent the background
		# and the image.  For now, just use a transparent
		# background so that it isn't too ugly.
		em.setnodeattr(newnode, 'transparent', 1)
		em.setnodeattr(newnode, 'channel', regionname)
		em.addsyncarc(newnode, 'beginlist', MMSyncArc(newnode, 'begin', srcnode='syncbase', delay=start))
		start = 0
		if transition in ('fadein', 'fadeout', 'crossfade', 'wipe'):
			# the real transtions
			trdict = {'dur': tagdict.get('tduration', 0),
# defaults
##				  'direction': 'forward',
##				  'startProgress': 0.0,
##				  'endProgress': 1.0,
##				  'horzRepeat': 1,
##				  'vertRepeat': 1,
##				  'borderWidth': 0,
# removed from SMIL 2.0
##				  'coordinated': 0,
##				  'clipBoundary': 'children',
				  }
			if transition == 'wipe':
				dir = tagdict['direction']
				if tagdict['wipetype'] == 'normal':
					trdict['trtype'] = 'barWipe'
					if dir == 'left':
						trdict['subtype'] = 'leftToRight'
						trdict['direction'] = 'reverse'
					elif dir == 'right':
						trdict['subtype'] = 'leftToRight'
					elif dir == 'up':
						trdict['subtype'] = 'topToBottom'
						trdict['direction'] = 'reverse'
					elif dir == 'down':
						trdict['subtype'] = 'topToBottom'
				else:
					trdict['trtype'] = 'pushWipe'
					if dir == 'left':
						trdict['subtype'] = 'fromRight'
					elif dir == 'right':
						trdict['subtype'] = 'fromLeft'
					elif dir == 'up':
						trdict['subtype'] = 'fromBottom'
					elif dir == 'down':
						trdict['subtype'] = 'fromTop'
			else:
				trdict['trtype'] = 'fade'
			# no point in doing zero-duration transitions
			if trdict['dur'] > 0:
				for trname, trval in ctx.transitions.items():
					if trval == trdict:
						# found an existing transition that'll do
						break
				else:
					j = 0
					trname = '%s %d' % (transition, j)
					while ctx.transitions.has_key(trname):
						j = j + 1
						trname = '%s %d' % (transition, j)
					em.addtransition(trname, trdict)
				em.setnodeattr(newnode, 'transIn', [trname])

		if tagdict.get('href'):
			anchor = ctx.newnode('anchor')
			em.addnode(newnode, -1, anchor)
			em.setnodeattr(anchor, 'sourcePlaystate', 'play')
			em.setnodeattr(anchor, 'destinationPlaystate', 'play')
			em.setnodeattr(anchor, 'show', 'new')
			em.addlink((anchor, tagdict['href'], DIR_1TO2))
	em.commit()

def convertrp(node, errorfunc = None):
	# Convert a seq node into a RealPix node.  The seq's children
	# must all be images, playing to the same region, the images
	# must not have an effective fill value "transition" (other
	# values are ok), the images may only have zero or one begin
	# syncarc which specifies a simple offset, and only zero or
	# one end syncarc which specifies a simple offset.
	ctx = node.GetContext()
	hlinks = ctx.hyperlinks
	if node.GetType() != 'seq':
		if errorfunc is not None: errorfunc('not a seq node')
		return
	import realnode
	rp = realnode.DummyRP()
	rp.tags = []			# must make new copy
	start = 0
	rp.duration = 0
	region = None
	bgcolor = None
	fill = None
	for c in node.GetChildren():
		# first some checks
		ctype = c.GetType()
		if ctype not in ('ext', 'brush'):
			if errorfunc is not None: errorfunc('child not an external node')
			return
		if region is None:
			region = c.GetChannel()
			rp.width, rp.height = region.getPxGeom()[2:]
			if region.get('transparent', 1):
				bgcolor = (0, 0, 0)
			else:
				bgcolor = region.get('bgcolor')
				if bgcolor is None:
					bgcolor = (0, 0, 0)
		elif c.GetChannel() != region:
			if errorfunc is not None: errorfunc('different region')
			return
		tagdict = {}
		rp.tags.append(tagdict)
		# set the start time
		beginlist = c.GetAttrDef('beginlist', [])
		if beginlist:
			if len(beginlist) > 1:
				if errorfunc is not None: errorfunc('too many begin values')
				return
			if beginlist[0].srcnode != 'syncbase':
				if errorfunc is not None: errorfunc('begin not a syncbase value')
			start = start + beginlist[0].delay
		if fill == 'freeze':
			# need to update start of out transition
			rp.tags[-2]['start'] = start - rp.tags[-2]['tduration']
			start = rp.tags[-2]['tduration']
		tagdict['start'] = start
		rp.duration = rp.duration + start
		# figure out syncbase for next child
		start = 0
		endlist = c.GetAttrDef('endlist', [])
		if endlist:
			if len(endlist) > 1:
				if errorfunc is not None: errorfunc('too many end values')
				return
			if endlist[0].srcnode != 'syncbase':
				if errorfunc is not None: errorfunc('end not a syncbase value')
			start = endlist[0].delay
		dur = c.GetAttrDef('duration', None)
		if dur is not None:
			if not endlist or dur < start:
				start = dur

		if ctype == 'ext':
			# set file
			file = c.GetAttrDef('file', None)
			if not file:
				if errorfunc is not None: errorfunc('no file specified on image')
				return
			tagdict['file'] = file
		else:
			fgcolor = c.GetAttrDef('fgcolor', (0,0,0))

		# figure out the transition
		transIn = c.GetAttrDef('transIn', [])
		if transIn:
			for tr in transIn:
				trdict = ctx.transitions.get(tr)
				trtype = trdict.get('trtype', 'fade')
				if (ctype == 'brush' and trtype == 'fade') or \
				   (ctype != 'brush' and trtype in ('fade', 'barWipe', 'pushWipe')):
					break
			else:
				trdict = None
		if not transIn or trdict is None:
			# no transition
			if ctype == 'ext':
				tagdict['tag'] = 'fadein'
				tagdict['tduration'] = 0
			else:
				tagdict['tag'] = 'fill'
				tagdict['color'] = fgcolor
		else:
			if trdict.get('startProgress', 0.0) != 0 or \
			   trdict.get('endProgress', 1.0) != 1 or \
			   trdict.get('horzRepeat', 1) != 1 or \
			   trdict.get('vertRepeat', 1) != 1 or \
			   trdict.get('borderWidth', 0) != 0:
				if errorfunc is not None: errorfunc('translation of transition looses information')
			tagdict['tduration'] = trdict.get('dur', 1)
			trtype = tagdict.get('trtype', 'fade')
			if ctype == 'brush':
				tagdict['tag'] = 'fadeout'
				tagdict['color'] = fgcolor
			elif trtype == 'barWipe':
				tagdict['tag'] = 'wipe'
				tagdict['wipetype'] = 'normal'
				if trdict.get('subtype', 'leftToRight') == 'leftToRight':
					if trdict.get('direction', 'forward') == 'forward':
						tagdict['direction'] = 'right'
					else:
						# direction="reverse"
						tagdict['direction'] = 'left'
				else:
					# subtype="topToBottom"
					if trdict.get('direction', 'forward') == 'forward':
						tagdict['direction'] = 'down'
					else:
						# direction="reverse"
						tagdict['direction'] = 'up'
			elif trtype == 'pushWipe':
				tagdict['tag'] = 'wipe'
				tagdict['wipetype'] = 'push'
				subtype = trdict.get('subtype', 'fromLeft')
				if subtype == 'fromLeft':
					tagdict['direction'] = 'right'
				elif subtype == 'fromRight':
					tagdict['direction'] = 'left'
				elif subtype == 'fromBottom':
					tagdict['direction'] = 'up'
				else:
					# subtype="fromTop"
					tagdict['direction'] = 'down'
			elif trtype == 'fade':
				tagdict['tag'] = 'fadein'
			else:
				if errorfunc is not None: errorfunc('untranslatable transition')
				tagdict['tag'] = 'fadein'
				tagdict['tduration'] = 0

		subRegGeom, mediaGeom = c.getPxGeomMedia()
		effSubRegGeom = _intersect((0, 0, rp.width, rp.height), subRegGeom)
		effMediaGeom = _intersect(effSubRegGeom, mediaGeom)
		tagdict['displayfull'] = 0
		tagdict['subregionxy'] = effMediaGeom[:2]
		tagdict['subregionwh'] = effMediaGeom[2:]
		if effMediaGeom == mediaGeom:
			tagdict['fullimage'] = 1
		else:
			width, height = apply(c.GetDefaultMediaSize, mediaGeom[2:])
			tagdict['fullimage'] = 0
			tagdict['imgcropxy'] = int(width * effMediaGeom[0] / float(mediaGeom[2]) + .5), int(height * effMediaGeom[1] / float(mediaGeom[3]) + .5)
			tagdict['imgcropwh'] = int(width * effMediaGeom[2] / float(mediaGeom[2]) + .5), int(height * effMediaGeom[3] / float(mediaGeom[3]) + .5)
		tagdict['aspect'] = 0
		fill = c.GetFill()
		if fill == 'transition':
			fill = 'remove'
			if errorfunc is not None: errorfunc('fill="transition" replaced by fill="remove"')
		if fill != 'hold':
			tagdict = {}
			rp.tags.append(tagdict)
			transOut = c.GetAttrDef('transIn', [])
			if transOut:
				for tr in transOut:
					trdict = ctx.transitions.get(tr)
					if trdict.get('trtype', 'fade') == 'fade':
						break
				else:
					trdict = None
			# start value may be updated in next iteration if fill="freeze"
			if trdict and trdict.get('dur', 1) > 0:
				tagdict['tag'] = 'fadeout'
				tagdict['tduration'] = trdict.get('dur', 1)
				tagdict['start'] = start - tagdict['tduration']
				start = tagdict['tduration']
			else:
				tagdict['tag'] = 'fill'
				tagdict['tduration'] = 0
				tagdict['start'] = start
				start = 0
			tagdict['color'] = bgcolor
			tagdict['displayfull'] = 0
			tagdict['subregionxy'] = effMediaGeom[:2]
			tagdict['subregionwh'] = effMediaGeom[2:]

		# deal with hyperlinks from this node
		# we only do hyperlinks from whole-node anchors to external documents
		for a in c.GetChildren():
			if a.GetType() == 'anchor' and \
			   MMAttrdefs.getattr(a, 'actuate') == 'onRequest' and \
			   not MMAttrdefs.getattr(a, 'fragment') and \
			   MMAttrdefs.getattr(a, 'ashape') == 'rect' and \
			   not MMAttrdefs.getattr(a, 'acoords'):
				links = hlinks.finddstlinks(a)
				for l in links:
					if type(l[ANCHOR2]) is type(''):
						tagdict['href'] = l[ANCHOR2]
						break

	rp.duration = rp.duration + start
	if rp.tags:
		rp.duration = rp.duration + rp.tags[-1]['tduration']
	dur = node.GetAttrDef('duration', None)
	if dur is not None:
		# seq duration overrides calculated duration
		rp.duration = dur
	if fill == 'freeze':
		# need to update start of out transition
		rp.tags[-1]['start'] = start - rp.tags[-1]['tduration']
		start = rp.tags[-1]['tduration']
	import windowinterface
	windowinterface.FileDialog('File name for RealPix:', '.', ['image/vnd.rn-realpix'], '', lambda file,rp=rp,node=node,regionname=region.name:_convertrpfinish(file,rp,node,regionname), None)

def _convertrpfinish(filename, rp, node, regionname):
	if not filename:
		return
	em = node.GetContext().editmgr
	url = MMurl.pathname2url(filename)
	if not em.transaction():
		# not allowed to do it at this point
		return
	for c in node.GetChildren()[:]:
		em.delnode(c)
	em.setnodetype(node, 'ext')
	em.setnodeattr(node, 'channel', regionname)
	em.setnodeattr(node, 'file', url)
	realsupport.writeRP(filename, rp, node)
##	import base64
##	'data:image/vnd.rn-realpix;base64,' + ''.join(base64.encodestring(realsupport.writeRP('rp.rp', rp, node, tostring = 1)).split('\n'))
	em.commit()

def _intersect((left, top, width, height), (x,y,w,h)):
	# calculate the intersection of a parent region (width,height)
	# with a child region (x,y,w,h)
	if x < 0:
		x, w = 0, w + x
	if x + w > width:
		w = width - x
	if y < 0:
		y, h = 0, h + y
	if y + h > height:
		h = height - y
	if w <= 0 or h <= 0:
		x = y = w = h = 0
	return left+x,top+y,w,h
