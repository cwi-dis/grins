__version__ = "$Id$"

import MMNode, EditableObjects
import marshal
import MMurl
from Owner import OWNER_DOCUMENT

_posattrs = ['left', 'width', 'right', 'top', 'height', 'bottom']
_alignattrs = ['regAlign', 'regPoint', 'fit']
_subregattrs = _posattrs + ['fit']

class QuickRead:
	def __init__(self, fp, baseurl, progress):
		self.__fp = fp
		self.__ctx = MMNode.MMNodeContext(EditableObjects.EditableMMNode)
		self.__ctx.setbaseurl(baseurl)
		self.__progress = progress
		if progress is not None:
			pos = fp.tell()
			fp.seek(0, 2)
			self.__size = fp.tell()
			fp.seek(pos, 0)
		self.__updateProgress()
		self.readusergroups()
		self.__updateProgress()
		self.readregpoints()
		self.__updateProgress()
		self.readlayout()
		self.__updateProgress()
		self.readtransitions()
		root = self.readnode()
		self.__updateProgress()
		root.addOwner(OWNER_DOCUMENT)
		self.fixarcs(root)
		self.readlinks()
		self.__updateProgress()
		self.root = root

	def __updateProgress(self):
		if self.__progress is None:
			return
		callback, interval = self.__progress
		callback(float(self.__fp.tell())/self.__size)

	def getdata(self):
		return self.__ctx, self.root

	def readusergroups(self):
		self.__ctx.usergroups = marshal.load(self.__fp)

	def readregpoints(self):
		ctx = self.__ctx
		nregpoints = marshal.load(self.__fp)
		for i in range(nregpoints):
			name, isdef, attrdict = marshal.load(self.__fp)
			ctx.addRegpoint(name, attrdict, isdef)

	def readlayout(self):
		ctx = self.__ctx
		nviewports = marshal.load(self.__fp)
		cssResolver = ctx.cssResolver
		for i in range(nviewports):
			name = marshal.load(self.__fp)
			attrdict = marshal.load(self.__fp)
			ctx.newviewport(name, -1, 'layout')
			v = ctx.channeldict[name]
			v.attrdict = attrdict
			v.addOwner(OWNER_DOCUMENT)
			self.readregions(v)
			cssResolver.setRawAttrs(v.getCssId(),
						[('width', v['width']),
						 ('height',v['height'])])

	def readregions(self, parent):
		self.__updateProgress()
		ctx = self.__ctx
		nregions = marshal.load(self.__fp)
		cssResolver = ctx.cssResolver
		for i in range(nregions):
			name = marshal.load(self.__fp)
			attrdict = marshal.load(self.__fp)
			ctx.newchannel(name, -1, 'layout')
			r = ctx.channeldict[name]
			r.attrdict = attrdict
			parent._addchild(r)
			attrList = []
			for attr in _subregattrs:
				if attrdict.has_key(attr):
					attrList.append((attr, attrdict[attr]))
			cssResolver.setRawAttrs(r.getCssId(), attrList)
			cssResolver.link(r.getCssId(), parent.getCssId())
			self.readregions(r)

	def readtransitions(self):
		self.__ctx.transitions = marshal.load(self.__fp)

	def readnode(self):
		self.__updateProgress()
		ctx = self.__ctx
		type, uid, values, collapsed, showtime, min_pxl_per_sec, nchildren = marshal.load(self.__fp)
		node = ctx.newnodeuid(type, uid)
		node.values = values
		node.collapsed = collapsed
		node.showtime = showtime
		if min_pxl_per_sec is not None:
			node.min_pxl_per_sec = min_pxl_per_sec
		attrdict = marshal.load(self.__fp)
		node.attrdict = attrdict
		for i in range(nchildren):
			c = self.readnode()
			node._addchild(c)
		if type in ('ext', 'imm'):
			cssResolver = ctx.cssResolver
			subRegCssId = node.getSubRegCssId()
			mediaCssId = node.getMediaCssId()
			regCssId = node.GetChannel().GetLayoutChannel().getCssId()

			attrList = []
			for attr in _posattrs:
				if attrdict.has_key(attr):
					attrList.append((attr, attrdict[attr]))
			cssResolver.setRawAttrs(subRegCssId, attrList)

			attrList = []
			for attr in _alignattrs:
				if attrdict.has_key(attr):
					attrList.append((attr, attrdict[attr]))
			cssResolver.setRawAttrs(mediaCssId, attrList)
		return node

	def fixsynclist(self, node, list):
		ctx = self.__ctx
		nlist = []
		for action, src, chan, event, marker, wallclock, accesskey, delay in list:
			if type(src) is type('') and src[:1] == '#':
				src = ctx.mapuid(src[1:])
			if type(chan) is type(''):
				chan = ctx.channeldict[chan]
			arc = MMNode.MMSyncArc(node, action, srcnode=src,
					       channel=chan, event=event,
					       marker=marker,
					       wallclock=wallclock,
					       accesskey=accesskey,
					       delay=delay)
			nlist.append(arc)
		return nlist

	def fixarcs(self, node):
		beginlist = node.attrdict.get('beginlist')
		if beginlist is not None:
			node.attrdict['beginlist'] = self.fixsynclist(node, beginlist)
		endlist = node.attrdict.get('endlist')
		if endlist is not None:
			node.attrdict['endlist'] = self.fixsynclist(node, endlist)
		for c in node.GetChildren():
			self.fixarcs(c)

	def readlinks(self):
		ctx = self.__ctx
		links = []
		for a1, a2, dir in marshal.load(self.__fp):
			if a1[:1] == '#':
				a1 = ctx.mapuid(a1[1:])
			if a2[:1] == '#':
				a2 = ctx.mapuid(a2[1:])
			links.append((a1, a2, dir))
		ctx.hyperlinks.addlinks(links)
		
def ReadFile(url, progressCallback = None):
	fn = MMurl.urlretrieve(url)[0]
	fp = open(fn, 'rb')
	q = QuickRead(fp, url, progressCallback)
	fp.close()
	context, root = q.getdata()
	return root
