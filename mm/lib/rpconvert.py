__version__ = "$Id$"

import MMurl, realsupport, MMNode

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

	regionname = ch.GetLayoutChannel().name
	
	em = ctx.editmgr
	if not em.transaction():
		return
	# convert the ext node to a par node
	em.setnodeattr(node, 'file', None)
	em.setnodetype(node, 'par')

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
	rw, rh = ctx.channeldict[regionname].getPxGeom()[2:]
	i = 0				# used to create unique channel name
	start = 0			# start time of last transition
	for tagdict in tags:
		transition = tagdict['tag']
		if transition in ('viewchange', 'animate'):
			print "ignoring transition we can't convert"
			continue
		newnode = ctx.newnode('ext')
		em.addnode(node, -1, newnode)
		if transition in ('fadeout', 'fill'):
			chtype = 'brush'
		else:
			chtype = 'image'
		chname = '%s %d' % (regionname, i)
		while ctx.channeldict.has_key(chname):
			i = i + 1
			chname = '%s %d' % (regionname, i)
		em.addchannel(chname, len(ctx.channelnames), chtype)
		em.setchannelattr(chname, 'base_window', regionname)
		if tagdict.get('displayfull', 0):
			x, y, w, h = 0, 0, rw, rh
		else:
			x, y = tagdict.get('subregionxy', (0, 0))
			w, h = tagdict.get('subregionwh', (0, 0))
			if w == 0:
				w = rw - x
			if h == 0:
				h = rh - y
		em.setnodeattr(newnode, 'left', x)
		em.setnodeattr(newnode, 'top', y)
		em.setnodeattr(newnode, 'width', w)
		em.setnodeattr(newnode, 'height', h)
		em.setnodeattr(newnode, 'channel', chname)
		if tagdict.get('aspect', rp.aspect == 'true'):
			em.setnodeattr(newnode, 'scale', 0)
		else:
			em.setnodeattr(newnode, 'scale', -3)
		start = start + tagdict.get('start', 0)
		em.setnodeattr(newnode, 'beginlist', [MMNode.MMSyncArc(node, 'begin', srcnode='syncbase', delay=start)])
		if transition in ('fadein', 'crossfade', 'wipe'):
			em.setnodeattr(newnode, 'file', MMurl.basejoin(furl, tagdict['file']))
		elif transition in ('fill', 'fadeout'):
			em.setnodeattr(newnode, 'fgcolor', tagdict['color'])
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
				if tagdict['wipetype'] == 'normal':
					trdict['trtype'] = 'barWipe'
				else:
					trdict['trtype'] = 'pushWipe'
				dir = tagdict['direction']
				if dir == 'left':
					trdict['subtype'] = 'leftToRight'
				elif dir == 'right':
					trdict['subtype'] = 'leftToRight'
					trdict['direction'] = 'reverse'
				elif dir == 'down':
					trdict['subtype'] = 'topToBottom'
				elif dir == 'down':
					trdict['subtype'] = 'topToBottom'
					trdict['direction'] = 'reverse'
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
	em.commit()
