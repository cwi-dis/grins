__version__ = "$Id$"

import MMurl, realsupport
from MMNode import MMSyncArc, MMAnchor
from AnchorDefs import ATYPE_WHOLE
from Hlinks import DIR_1TO2, TYPE_FORK, A_SRC_PLAY, A_DEST_PLAY

def rpconvert(node):
	# convert a RealPix node into a par node with children,
	# together representing the RealPix node
	ctx = node.GetContext()
	# check that node is a RealPix node
	furl = node.GetAttr('file')
	if node.GetType() != 'ext' or not furl:
		print 'not a RealPix node'
		return
	ch = node.GetChannel()
	if not ch:
		print 'no region associated with node'
		return
	url = ctx.findurl(furl)
	if furl[:5] == 'data:':
		furl = ''
	try:
		f = MMurl.urlopen(url)
	except IOError:
		print 'cannot open RealPix file'
		return
	head = f.read(4)
	if head != '<imf':
		print 'not a RealPix file'
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
	em.setnodetype(node, 'par')
	em.setnodeattr(node, 'channel', None)
	em.setnodeattr(node, 'bgcolor', None)
	em.setnodeattr(node, 'transparent', None)
	if node.GetAttrDef('fill', 'default') == 'default' and node.GetInherAttrDef('fillDefault', 'inherit') == 'inherit':
		# make default fill behavior explicit
		em.setnodeattr(node, 'fill', node.GetFill())
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
	start = 0			# start time of last transition
	for tagdict in tags:
		transition = tagdict['tag']
		start = start + tagdict.get('start', 0)
		if transition in ('viewchange', 'animate'):
			print "ignoring transition we can't convert"
			continue
		newnode = ctx.newnode('ext')
		em.addnode(node, -1, newnode)
		if transition in ('fadeout', 'fill'):
			chtype = 'brush'
			em.setnodeattr(newnode, 'fgcolor', tagdict['color'])
		else:
			chtype = 'image'
			em.setnodeattr(newnode, 'file', MMurl.basejoin(furl, tagdict['file']))
			if tagdict.get('aspect', rp.aspect == 'true'):
				em.setnodeattr(newnode, 'scale', 0)
			else:
				em.setnodeattr(newnode, 'scale', -3)
		chname = ctx.newChannelName(regionname)
		em.addchannel(chname, -1, chtype)
		em.setchannelattr(chname, 'base_window', regionname)
		# XXX are these two correct?
		em.setchannelattr(chname, 'transparent', region.get('transparent', 0))
		em.setchannelattr(chname, 'bgcolor', region.get('bgcolor', (255,255,255)))
		em.setchannelattr(chname, 'center', 0)
		em.setchannelattr(chname, 'drawbox', 0)
		em.setchannelattr(chname, 'z', -1)

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
##		em.setnodeattr(newnode, 'bgcolor', (0,0,0))
##		em.setnodeattr(newnode, 'transparent', 0)
		em.setnodeattr(newnode, 'transparent', 1)
		em.setnodeattr(newnode, 'channel', chname)
		em.setnodeattr(newnode, 'beginlist', [MMSyncArc(newnode, 'begin', srcnode='syncbase', delay=start)])
		if transition in ('fadein', 'fadeout', 'crossfade', 'wipe'):
			# the real transtions
			trdict = {'dur': tagdict.get('tduration', 0),
				  'direction': 'forward',
				  'startProgress': 0.0,
				  'endProgress': 1.0,
				  'horzRepeat': 1,
				  'vertRepeat': 1,
				  'borderWidth': 0,
				  'coordinated': 0,
				  'clipBoundary': 'children',
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
			em.setnodeattr(newnode, 'anchorlist', [MMAnchor('0', ATYPE_WHOLE, [], (0, 0), None)])
			em.addlink(((newnode.GetUID(), '0'), tagdict['href'], DIR_1TO2, TYPE_FORK, A_SRC_PLAY, A_DEST_PLAY))
	em.commit()
