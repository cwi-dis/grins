__version__ = "$Id$"

import MMAttrdefs, windowinterface, urlparse, MMurl
from MMExc import NoSuchAttrError

class DummyRP:
	# used when parsing the RealPix file failed for some reason
	aspect = 'true'
	author = None
	width = height = 0
	duration = 0
	copyright = None
	maxfps = None
	preroll = None
	title = None
	url = None
	tags = []

	def __init__(self):
		import settings
		bitrate = settings.get('system_bitrate')
		if bitrate >= 112000:
			bitrate = 80000
		elif bitrate >= 64000:
			bitrate = 45000
		elif bitrate >= 56000:
			bitrate = 34000
		elif bitrate >= 28800:
			bitrate = 20000
		elif bitrate >= 14400:
			bitrate = 10000
		else:
			bitrate = bitrate * 0.7
		self.bitrate = bitrate

class SlideShow:
	__callback_added = 0
	tmpfiles = []

	def __init__(self, node, new_file = 0):
		if node is None:
			# special case, only used in copy method
			return
		if node.GetType() != 'ext' or \
		   node.GetChannelType() != 'RealPix':
			raise RuntimeError("shouldn't happen")
		update = 0
		self.node = node
		import realsupport
		ctx = node.GetContext()
		url = MMAttrdefs.getattr(node, 'file')
		if not url:
			name = MMAttrdefs.getattr(node, 'name') or '<unnamed>'
			cname = node.GetChannelName()
			windowinterface.showmessage('No URL specified for slideshow node %s on channel %s' % (name, cname), mtype = 'warning')
			rp = DummyRP()
		else:
			ourl = url
			url = ctx.findurl(url)
			utype, host, path, params, query, tag = urlparse.urlparse(url)
			url = urlparse.urlunparse((utype, host, path, params, query, ''))
			self.url = url
			fp = None
			if new_file and type(new_file) == type(''):
				url = MMurl.basejoin(new_file, ourl)
				try:
					fn, hdr = MMurl.urlretrieve(url)
					fp = open(fn)
					rp = realsupport.RPParser(url, baseurl = url, printfunc = self.printfunc)
					rp.feed(fp.read())
					rp.close()
					update = 1
					# zap the URL so that the
					# template doesn't get
					# overwritten
					try:
						node.DelAttr('file')
					except NoSuchAttrError:
						pass
					url = self.url = ''
				except:
					pass
				url = self.url
			else:
				try:
					fn, hdr = MMurl.urlretrieve(url)
					fp = open(fn)
					rp = realsupport.RPParser(url, baseurl = ourl, printfunc = self.printfunc)
					rp.feed(fp.read())
					rp.close()
				except:
					rp = None
					if rp is None:
						windowinterface.showmessage('Cannot read slideshow file with URL %s in node %s on channel %s' % (url, MMAttrdefs.getattr(node, 'name') or '<unnamed>', node.GetChannelName()), mtype = 'warning')
						rp = DummyRP()
			if fp is not None:
				fp.close()
		self.url = url
		self.rp = rp
		attrdict = node.GetAttrDict()
		attrdict['bitrate'] = rp.bitrate
		if rp.width == 0 and rp.height == 0:
			# no size specified, initialize with channel size
			rp.width, rp.height = node.GetChannel().get('base_winoff',(0,0,256,256))[2:4]
		attrdict['size'] = rp.width, rp.height
		attrdict['duration'] = rp.duration
		if rp.aspect != 'true':
			attrdict['aspect'] = 0
		if rp.author is not None:
			attrdict['author'] = rp.author
		if rp.copyright is not None:
			attrdict['copyright'] = rp.copyright
		if rp.maxfps is not None:
			attrdict['maxfps'] = rp.maxfps
		if rp.preroll is not None:
			attrdict['preroll'] = rp.preroll
		if rp.title is not None:
			attrdict['title'] = rp.title
		if rp.url is not None:
			attrdict['href'] = rp.url
		ctx.register(self) # *must* come first
		if update:
			self.update(changed = 1)

	def destroy(self):
		em = self.node.GetContext().geteditmgr()
		# EditMgr may have been reset so check whether still valid
		if em is not None and em.is_registered(self):
			em.unregister(self)
		del self.node
		del self.rp

	def copy(self, newnode):
		import MMNode		# _valuedeepcopy
		new = SlideShow(None)
		new.node = newnode
		newnode.slideshow = new
		new.rp = DummyRP()
		new.url = ''
		new.rp.aspect = self.rp.aspect
		new.rp.author = self.rp.author
		new.rp.width = self.rp.width
		new.rp.height = self.rp.height
		new.rp.duration = self.rp.duration
		new.rp.copyright = self.rp.copyright
		new.rp.maxfps = self.rp.maxfps
		new.rp.preroll = self.rp.preroll
		new.rp.title = self.rp.title
		new.rp.url = self.rp.url
		new.rp.tags = MMNode._valuedeepcopy(self.rp.tags)
		self.node.GetContext().register(new)
		return new

	def printfunc(self, msg):
		windowinterface.showmessage('While reading %s:\n\n' % self.url + msg)

	def transaction(self):
		return 1

	def rollback(self):
		pass

	def commit(self):
		self.update()

	def update(self, changed = 0):
		node = self.node
		oldrp = self.rp
		if node.GetType() != 'ext' or \
		   node.GetChannelType() != 'RealPix':
			# not a RealPix node anymore
			if hasattr(node, 'expanded'):
				import HierarchyView
				HierarchyView.collapsenode(node)
			del node.slideshow
			self.destroy()
			# XXX what to do with node.tmpfile?
			if hasattr(node, 'tmpfile'):
				import os
				try:
					os.unlink(node.tmpfile)
				except:
					pass
				del node.tmpfile
			return
		if oldrp is None:
			return
		ctx = node.GetContext()
		url = MMAttrdefs.getattr(node, 'file')
		ourl = url
		if url:
			url = ctx.findurl(url)
			utype, host, path, params, query, tag = urlparse.urlparse(url)
			url = urlparse.urlunparse((utype, host, path, params, query, ''))
		if url != self.url:
			# different URL specified
			try:
				if not url:
					raise IOError
				fn, hdr = MMurl.urlretrieve(url)
			except IOError:
				# new file does not exist, keep content
				rp = self.rp
			else:
				# new file exists, use it
				import realsupport
				fp = open(fn)
				self.filename = url
				rp = realsupport.RPParser(url, baseurl = ourl, printfunc = self.printfunc)
				try:
					rp.feed(fp.read())
					rp.close()
				except:
					import sys
					tp, vl, tb = sys.exc_info()
					msg = 'Error reading RealPix file %s:\n%s' % (url, vl)
					windowinterface.showmessage(msg, mtype = 'warning')
					self.node.set_infoicon('error', msg)
					rp = DummyRP()
				fp.close()
			if rp is not self.rp and hasattr(node, 'tmpfile'):
				# new content, delete temp file
##				windowinterface.showmessage('You have edited the content of the slideshow file in node %s on channel %s' % (MMAttrdefs.getattr(node, 'name') or '<unnamed>', node.GetChannelName()), mtype = 'warning')
				choice = self.asksavechanges()
				if choice == 2:
					# cancel
					node.SetAttr('file', self.url)
					self.update()
					return
				if choice == 0:
					# yes, save file
					node.SetAttr('file', self.url)
					writenode(node)
					node.SetAttr('file', url)
				else:
					# no, discard changes
					import os
					try:
						os.unlink(node.tmpfile)
					except:
						pass
					del node.tmpfile
			self.url = url
			self.rp = rp
		rp = self.rp
		attrdict = node.GetAttrDict()
		if attrdict['bitrate'] != rp.bitrate:
			if rp is oldrp:
				rp.bitrate = attrdict['bitrate']
				changed = 1
			else:
				attrdict['bitrate'] = rp.bitrate
		size = attrdict.get('size', (256, 256))
		if size != (rp.width, rp.height):
			if rp is oldrp:
				rp.width, rp.height = size
				changed = 1
			else:
				if rp.width == 0 and rp.height == 0:
					rp.width, rp.height = node.GetChannel().get('base_winoff',(0,0,256,256))[2:4]
				attrdict['size'] = rp.width, rp.height
		if attrdict['duration'] != rp.duration:
			if rp is oldrp:
				rp.duration = attrdict['duration']
				changed = 1
			else:
				attrdict['duration'] = rp.duration
		aspect = attrdict.get('aspect', 1)
		if (rp.aspect == 'true') != aspect:
			if rp is oldrp:
				rp.aspect = ['false','true'][aspect]
				changed = 1
			else:
				attrdict['aspect'] = rp.aspect == 'true'
		if attrdict.get('author') != rp.author:
			if rp is oldrp:
				rp.author = attrdict.get('author')
				changed = 1
			elif rp.author is not None:
				attrdict['author'] = rp.author
			else:
				del attrdict['author']
		if attrdict.get('copyright') != rp.copyright:
			if rp is oldrp:
				rp.copyright = attrdict.get('copyright')
				changed = 1
			elif rp.copyright is not None:
				attrdict['copyright'] = rp.copyright
			else:
				del attrdict['copyright']
		if attrdict.get('title') != rp.title:
			if rp is oldrp:
				rp.title = attrdict.get('title')
				changed = 1
			elif rp.title is not None:
				attrdict['title'] = rp.title
			else:
				del attrdict['title']
		if attrdict.get('href') != rp.url:
			if rp is oldrp:
				rp.url = attrdict.get('href')
				changed = 1
			elif rp.url is not None:
				attrdict['href'] = rp.url
			else:
				del attrdict['href']
		if attrdict.get('maxfps') != rp.maxfps:
			if rp is oldrp:
				rp.maxfps = attrdict.get('maxfps')
				changed = 1
			elif rp.maxfps is not None:
				attrdict['maxfps'] = rp.maxfps
			else:
				del attrdict['maxfps']
		if attrdict.get('preroll') != rp.preroll:
			if rp is oldrp:
				rp.preroll = attrdict.get('preroll')
				changed = 1
			elif rp.preroll is not None:
				attrdict['preroll'] = rp.preroll
			else:
				del attrdict['preroll']
		if hasattr(node, 'expanded'):
			if oldrp is rp:
				i = 0
				children = node.children
				nchildren = len(children)
				taglist = rp.tags
				ntags = len(taglist)
				rp.tags = []
				nnodes = max(ntags, nchildren)
				while i < nnodes:
					if i < nchildren:
						childattrs = children[i].attrdict
						rp.tags.append(childattrs.copy())
					else:
						changed = 1
						childattrs = None
					if i < ntags:
						attrs = taglist[i]
					else:
						changed = 1
						attrs = None
					if childattrs != attrs:
						changed = 1
					i = i + 1
			else:
				# re-create children
				import HierarchyView
				HierarchyView.collapsenode(node)
				HierarchyView.expandnode(node)
		if changed:
			if not hasattr(node, 'tmpfile'):
				url = MMAttrdefs.getattr(node, 'file')
				url = node.context.findurl(url)
##				if not url:
##					windowinterface.showmessage('specify a location for this node')
##					return
				utype, host, path, params, query, fragment = urlparse.urlparse(url)
				if (utype and utype != 'file') or \
				   (host and host != 'localhost'):
					windowinterface.showmessage('cannot edit remote RealPix files')
					return
				import tempfile, os
				pre = tempfile.gettempprefix()
				dir = os.path.dirname(MMurl.url2pathname(path))
				while 1:
					tempfile.counter = tempfile.counter + 1
					file = os.path.join(dir, pre+`tempfile.counter`+'.rp')
					if not os.path.exists(file):
						break
				node.tmpfile = file
				if not SlideShow.__callback_added:
					windowinterface.addclosecallback(
						deltmpfiles, ())
					SlideShow.__callback_added = 1
				SlideShow.tmpfiles.append(file)
##			import realsupport
##			realsupport.writeRP(node.tmpfile, rp, node)
			MMAttrdefs.flushcache(node)

	def printfunc(self, msg):
		windowinterface.showmessage('while reading %s\n\n' % self.filename + msg)

	def kill(self):
		pass
		
	def asksavechanges(self):
		if self.url:
			return windowinterface.multchoice('Save changes to %s?' % self.url, 
						['Yes', 'No', 'Cancel'], 2)
		# User wants to save, but we have no url.
		answer = windowinterface.multchoice('Discard old contents of RealPix node?',
			['OK', 'Cancel'], 1)
		if answer == 0:
			# Discard, return as "don't save"
			return 1
		# Cancel and don't discard are both returned as "cancel"
		return 2


	def computebandwidth(self):
		"""See whether bandwidth usage of our (slide) children is OK"""
		import Bandwidth
		seconds_extra = 0
		errorcount = 0
		urls_done = {}
		ctx = self.node.GetContext()
		bandwidth = self.rp.bitrate
		if self.rp.preroll:
			preload_cur_time = -self.rp.preroll
		else:
			preload_cur_time = 0
		playout_cur_time = 0
		index = 0
		for index in range(len(self.rp.tags)):
			slide = self.rp.tags[index]
			if index < len(self.node.children):
				slide_node = self.node.children[index]
			else:
				slide_node = None
			start = slide.get('start', 0)
			playout_cur_time = playout_cur_time + start		# The time the data should be loaded
			if not slide['tag'] in ('fadein', 'crossfade', 'wipe'):
				continue	# For non-image nodes we're done
			url = slide.get('file', None)
			if not url:
				if slide_node:
					slide_node.set_infoicon('error', 'Image file not set')
				continue	# If there is no image we're also done
			if urls_done.has_key(url):
				if slide_node:
					slide_node.set_infoicon('bandwidthgood')
				continue	# And if we saw it before we're done too
			try:
				filesize = Bandwidth.GetSize(ctx.findurl(url), target=1, attrs=slide)
			except Bandwidth.Error, arg:
				if slide_node:
					slide_node.set_infoicon('error', arg)
				continue
			if filesize == None:
				# Unknown (probably remote url)
				continue
			urls_done[url] = 1
			preload_cur_time = preload_cur_time + (filesize*8/bandwidth)
			if preload_cur_time > playout_cur_time:
				toolate = preload_cur_time - playout_cur_time
				seconds_extra = seconds_extra + toolate
				errorcount = errorcount + 1
				if slide_node:
					slide_node.set_infoicon('bandwidthbad', 'This image needs %d seconds extra to load'%toolate)
				preload_cur_time = playout_cur_time # So rest of checks makes sense
			else:
				if slide_node:
					slide_node.set_infoicon('bandwidthgood')
		return seconds_extra, errorcount

def deltmpfiles():
	import os
	for file in SlideShow.tmpfiles:
		try:
			os.unlink(file)
		except:
			pass
	SlideShow.tmpfiles = []

def writenode(node, evallicense = 0):
	if not hasattr(node, 'tmpfile'):
		return
	import realsupport
	realsupport.writeRP(node.tmpfile, node.slideshow.rp, node, savecaptions=1)
	url = MMAttrdefs.getattr(node, 'file')
	url = node.GetContext().findurl(url)
	utype, host, path, params, query, tag = urlparse.urlparse(url)
	if (not utype or utype == 'file') and \
	   (not host or host == 'localhost'):
		try:
			f = open(MMurl.url2pathname(path), 'w')
			f.write(open(node.tmpfile).read())
			f.close()
		except:
			windowinterface.showmessage("cannot write `%s' for node `%s'" % (url, MMAttrdefs.getattr(node, 'name') or '<unnamed>'))
		else:
			del node.tmpfile
	else:
		windowinterface.showmessage("cannot write remote file for node `%s'" % (MMAttrdefs.getattr(node, 'name') or '<unnamed>'))
