__version__ = "$Id$"

# Base class for SMILTreeWrite and SMILTreeWriteXhtmlSmil.

import os
import string
import MMurl
import MMAttrdefs
import MMmimetypes
from MMTypes import mediatypes, interiortypes
import ChannelMap
import urlcache
from fmtfloat import fmtfloat
from SMIL import ATTRIBUTES
import re
import colors

FORBIDDEN = ':'				# characters not allowed in file names

qt_node_attrs = {
	'immediateinstantiationmedia':0,
	'bitratenecessary':0,
	'systemmimetypesupported':0,
	'attachtimebase':0,
	'qtchapter':0,
	'qtcompositemode':0,
	}

Error = 'Error'

# A fileish object with indenting
class IndentedFile:
	def __init__(self, fp):
		self.fp = fp
		self.level = 0
		self.bol = 1
		self.charpos = 0

	def push(self):
		self.level = self.level + 2

	def pop(self):
		self.level = self.level - 2

	def write(self, data):
		lines = data.split('\n')
		if not lines:
			return self.charpos, self.charpos
		start = self.charpos
		for line in lines[:-1]:
			if self.bol:
				if self.level:
					self.fp.write(' '*self.level)
					self.charpos = self.charpos + self.level
				self.bol = 0
			if line:
				self.fp.write(line)
				self.charpos = self.charpos + len(line)
			self.fp.write('\n')
			self.charpos = self.charpos + 1
			self.bol = 1

		line = lines[-1]
		if line:
			if self.bol:
				if self.level:
					self.fp.write(' '*self.level)
					self.charpos = self.charpos + self.level
				self.bol = 0
			self.fp.write(line)
			self.charpos = self.charpos + len(line)
		return start, self.charpos

	def writeline(self, data):
		self.write(data)

	def writelines(self, data):
		self.write('\n'.join(data))

	def close(self):
		self.fp.close()

# Mapping from CMIF channel types to smil media types
from smil_mediatype import smil_mediatype
def mediatype(x, error=0):
	chtype = x.GetChannelType()
	if not chtype:
		chtype = 'unknown'
	if chtype == 'video':
		url = x.GetAttrDef('file', None) or ''
		mtype = urlcache.mimetype(x.GetContext().findurl(url))
		if mtype == 'image/vnd.rn-realpix':
			chtype = 'RealPix'
		elif mtype == 'application/x-shockwave-flash':
			return 'animation', 'animation'
	if smil_mediatype.has_key(chtype):
		return smil_mediatype[chtype], smil_mediatype[chtype]
	if error and chtype != 'layout':
		print '** Unimplemented channel type', chtype
	return '%s:%s' % (NSGRiNSprefix, chtype), '%s %s' % (GRiNSns, chtype)

def escape_name(name, quote_initial = 1):
	name = '\\.'.join(name.split('.'))
	name = '\\-'.join(name.split('-'))
	if quote_initial and name in ['prev', 'wallclock', ]:
		name = '\\' + name
	return name

htmlnamechars = string.letters + string.digits + '_'
namechars = htmlnamechars + '-.'

def identify(name, html = 0):
	# Turn a CMIF name into an identifier
	if html:
		minus = '_'
		nmchrs = htmlnamechars
	else:
		minus = '-'
		nmchrs = namechars
	rv = []
	for ch in name:
		if ch in nmchrs:
			rv.append(ch)
		else:
			if rv and rv[-1] != minus:
				rv.append(minus)
	# the first character must not be a digit
	if rv and rv[0] in string.digits:
		rv.insert(0, '_')
	name = ''.join(rv)
	if html:
		# certain names should not be used in XHTML+SMIL
		if ATTRIBUTES.has_key(name):
			name = '_'+name
	return name

def translatecolor(val, use_name = 1):
	if use_name and colors.rcolors.has_key(val):
		return colors.rcolors[val]
	else:
		return '#%02x%02x%02x' % val

def copysrc(writer, node, url, copycache, files_generated, copydirurl):
	if copycache.has_key(url):
		# already seen and copied
		nurl = MMurl.basejoin(copydirurl, MMurl.pathname2url(copycache[url]))
		if writer.rpExt and not writer.grinsExt:
			nurl = MMurl.unquote(nurl)
		return nurl
	if urlcache.mimetype(url) == 'image/vnd.rn-realpix':
		# special case code for RealPix file
		import realsupport
		if node and hasattr(node, 'slideshow'):
			rp = node.slideshow.rp
		else:
			f = MMurl.urlopen(url)
			head = f.read(4)
			if head != '<imf':
				f.close()
				# delete rptmpfile attr if it exists
				if node:
					node.rptmpfile = None
					del node.rptmpfile
				return url # ???
			rp = realsupport.RPParser(url)
			rp.feed(head)
			rp.feed(f.read())
			f.close()
			rp.close()
		otags = rp.tags
		ntags = []
		for i in range(len(otags)):
			attrs = otags[i].copy()
			ntags.append(attrs)
			if attrs.get('tag','fill') not in ('fadein', 'crossfade', 'wipe'):
				continue
			iurl = attrs.get('file')
			if not iurl:
				# XXX URL missing for transition
				if node:
					import windowinterface
					msg = 'No URL specified in transition'
					windowinterface.showmessage(msg + '\nThe document will not be playable.')
					if node.children:
						node.children[i].set_infoicon('error', msg)
					else:
						node.set_infoicon('error', msg)
				continue
			iurl = writer.context.findurl(iurl)
			if copycache.has_key(iurl):
				nfile = copycache[iurl]
			else:
				nfile = writer.copyfile(iurl, attrs, files_generated)
				copycache[iurl] = nfile
			attrs['file'] = MMurl.basejoin(copydirurl, MMurl.pathname2url(nfile))
		rp.tags = ntags
		file = writer.newfile(url, files_generated)
		nurl = MMurl.basejoin(copydirurl, MMurl.pathname2url(file))
		if node:
			ofile = node.GetRawAttrDef('file', None)
			node.SetAttr('file', nurl)
		realsupport.writeRP(os.path.join(writer.copydir, file), rp, node)
		if node:
			if ofile:
				node.SetAttr('file', ofile)
			else:
				node.DelAttr('file')
		files_generated[file] = ''
		rp.tags = otags
	else:
		try:
			file = writer.copyfile(url, node, files_generated)
		except IOError, msg:
			import windowinterface
			windowinterface.showmessage('Cannot copy %s: %s\n'%(url, msg)+'The URL is left unchanged; the document may not be playable.', cancelCallback = (writer.cancelwrite, ()))
			if node:
				node.set_infoicon('error', msg)
			return url
	copycache[url] = file
	nurl = MMurl.basejoin(copydirurl, MMurl.pathname2url(file))
	if writer.rpExt and not writer.grinsExt:
		nurl = MMurl.unquote(nurl)
	return nurl

class SMILWriterBase:
	def __init__(self, context, filename, copyFiles, tmpcopy, convertURLs, convertfiles, weburl, html, progress):
		self.context = context
		self.uid2name = {}
		self.ch2name = {}
		self.chnamedict = {}
		self.ugr2name = {}
		self.transition2name = {}
		self.name2transition = {}
		self.ids_used = {}
		self.smilboston = 0
		self.messages = []
		self.grinsExt = 0
		self.qtExt = 0
		self.rpExt = 0
		self.pss4Ext = 0
		self.uses_qt_namespace = 0
		self.prune = 0
		self.force_smil_1 = 0
		self.html = html
		if html:
			self.__sep = '_'
		else:
			self.__sep = '-'
		self.progress = progress
		self.addattrs = 0

		self.convert = convertfiles # we only convert if we have to copy
		if convertURLs:
			url = MMurl.canonURL(MMurl.pathname2url(filename))
			i = url.rfind('/')
			if i >= 0:
				url = url[:i+1]
			else:
				url = ''
			self.convertURLs = url
		else:
			self.convertURLs = None
		self.files_generated = {}
		self.webfiles_generated = {}
		self.bases_used = {}
		if copyFiles:
			dir, base = os.path.split(filename)
##			base, ext = os.path.splitext(base)
			if tmpcopy:
				newdir = base + '.tmpdata'
				self.copydir = os.path.join(dir, newdir)
				self.copydirurl = MMurl.pathname2url(base+'.data') + '/'
				self.copydirname = base + '.data'
			else:
				newdir = base + '.data'
				self.copydir = os.path.join(dir, newdir)
				self.copydirurl = MMurl.pathname2url(newdir) + '/'
				self.copydirname = newdir
			self.webcopydirurl = MMurl.basejoin(weburl or '', self.copydirurl)
			self.copycache = {}
			self.webcopycache = {}
			try:
				os.mkdir(self.copydir)
			except:
				# raise Error, 'Cannot create subdirectory for assets; document not saved'
				pass # Incorrect: may be because of failed permissions
		else:
			self.copydir = self.copydirurl = self.copydirname = None

	def calcugrnames(self):
		# Calculate unique names for usergroups
		usergroups = self.context.usergroups
		if not usergroups:
			return
		if self.force_smil_1:
			self.warning('Lost information about customTest')
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

	def calctransitionnames(self):
		# Calculate unique names for transitions
		transitions = self.context.transitions
		if not transitions:
			return
		if self.force_smil_1:
			self.warning('Lost information about transitions')
			return
		self.smilboston = 1
		for transition in transitions.keys():
			name = identify(transition, html = self.html)
			if self.ids_used.has_key(name):
				i = 0
				nn = '%s%s%d' % (name, self.__sep, i)
				while self.ids_used.has_key(nn):
					i = i+1
					nn = '%s%s%d' % (name, self.__sep, i)
				name = nn
			self.ids_used[name] = 1
			self.transition2name[transition] = name
			self.name2transition[name] = transition

	def calcnames1(self, node):
		# Calculate unique names for nodes; first pass
		if self.prune and not node.WillPlay():
			# skip unplayable nodes when pruning
			return
		uid = node.GetUID()
		name = node.GetRawAttrDef('name', '')
		if name:
			name = identify(name, html = self.html)
			if not self.ids_used.has_key(name):
				self.ids_used[name] = 1
				self.uid2name[uid] = name
				if self.prune:
					# if pruning, inherit id from switch down to child
					pnode = node.GetParent()
					if pnode is not None and pnode.GetType() == 'switch':
						self.uid2name[pnode.GetUID()] = name
		if self.qtExt and not self.uses_qt_namespace:
			for attr in qt_node_attrs.keys():
				if node.attrdict.has_key(attr):
					self.uses_qt_namespace = 1
					break
		for child in node.children:
			self.calcnames1(child)

	def calcnames2(self, node):
		# Calculate unique names for nodes; second pass
		if self.prune and not node.WillPlay():
			# skip unplayable nodes when pruning
			return
		uid = node.GetUID()
		name = node.GetRawAttrDef('name', '')
		if not self.uid2name.has_key(uid):
			pnode = node.GetParent()
			if not name and self.prune and pnode is not None and pnode.GetType() == 'switch':
				# if pruning, inherit id from switch down to child
				self.uid2name[uid] = self.uid2name[pnode.GetUID()]
			else:
				isused = name != ''
				if isused:
					name = identify(name, html = self.html)
				else:
					name = 'node'
				# find a unique name by adding a number to the name
				i = 0
				nn = '%s%s%d' % (name, self.__sep, i)
				while self.ids_used.has_key(nn):
					i = i+1
					nn = '%s%s%d' % (name, self.__sep, i)
				name = nn
				self.ids_used[name] = isused
				self.uid2name[uid] = name
				if self.prune:
					# if pruning, inherit id from switch down to child
					pnode = node.GetParent()
					if pnode is not None and pnode.GetType() == 'switch':
						self.uid2name[pnode.GetUID()] = name
		for child in node.children:
			self.calcnames2(child)

	def calcchnames1(self):
		# Calculate unique names for channels; first pass
		channels = self.context.channels
		for ch in channels:
			name = identify(ch.name, html = self.html)
			if not self.ids_used.has_key(name):
				self.ids_used[name] = 0
				self.ch2name[ch] = name
				self.chnamedict[name] = ch.name
			if ch.GetParent() is None and \
			   ChannelMap.isvisiblechannel(ch['type']):
				# top-level channel with window
				if not self.title:
					self.title = ch.name
			# also check if we need to use the CMIF extension
			if self.grinsExt and not self.uses_grins_namespace and \
			   not smil_mediatype.has_key(ch['type']) and \
			   ch['type'] != 'layout':
				self.uses_grins_namespace = 1
		if not self.title and channels:
			# no channels with windows, so take very first channel
			self.title = channels[0].name

	def calcchnames2(self):
		# Calculate unique names for channels; second pass
		top0 = None
		for ch in self.context.getviewports():
			if ChannelMap.isvisiblechannel(ch['type']):
				if top0 is None:
					# first top-level channel
					top0 = ch.name
				else:
					# second top-level, must be SMIL 2.0
					if self.force_smil_1:
						raise Error, 'Multiple topLevel windows'
					else:
						self.smilboston = 1
					break
		for ch in self.context.channels:
			if not self.ch2name.has_key(ch):
				name = identify(ch.name, html = self.html)
				i = 0
				nn = '%s%s%d' % (name, self.__sep, i)
				while self.ids_used.has_key(nn):
					i = i+1
					nn = '%s%s%d' % (name, self.__sep, i)
				name = nn
				self.ids_used[name] = 0
				self.ch2name[ch] = name
				self.chnamedict[name] = ch.name
			# check for SMIL 2.0 feature: hierarchical regions
			if not self.smilboston and ch.GetParent() is not None:
				for sch in ch.GetChildren():
					if sch['type'] == 'layout':
						if self.force_smil_1:
							raise Error, 'Lost information about hierarchical regions'
						else:
							self.smilboston = 1
						break

	def syncidscheck(self, node):
		# make sure all nodes referred to in sync arcs get their ID written
		if self.prune and not node.WillPlay():
			# skip unplayable nodes when pruning
			return
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
					if self.grinsExt:
						continue
					# XPath
					srcnode = arc.refnode()
					if srcnode is None:
						continue
				if arc.channel is not None:
					pass
				elif srcnode in ('syncbase', 'prev'):
					pass
				elif type(srcnode) is not type('') and srcnode.GetRoot() is not node.GetRoot():
					# srcnode not in document
					pass
				elif self.prune and srcnode is not None and not srcnode.WillPlay():
					pass
				elif srcnode is not node:
					self.ids_used[self.uid2name[srcnode.GetUID()]] = 1
			else:
				self.ids_used[self.uid2name[arc.srcnode.GetUID()]] = 1
		for child in node.children:
			self.syncidscheck(child)

	def newfile(self, srcurl, files_generated):
		import posixpath, urlparse
		utype, host, path, params, query, fragment = urlparse.urlparse(srcurl)
		if utype == 'data':
			mtype = urlcache.mimetype(srcurl)
			if mtype is None:
				mtype = 'text/plain'
			ext = MMmimetypes.guess_extension(mtype)
			base = 'data'
		else:
			file = posixpath.basename(path)
			# replace forbidden characters by something innocuous
			for c in FORBIDDEN:
				file = file.replace(c, '-')
			file = MMurl.url2pathname(file)
			base, ext = os.path.splitext(file)
		if self.bases_used.has_key(base):
			i = 1
			while self.bases_used.has_key(base + `i`):
				i = i + 1
			base = base + `i`
		self.bases_used[base] = None
		files_generated[base + ext] = None
		return base + ext

	def copyfile(self, srcurl, node, files_generated):
		dstdir = self.copydir
		file = self.newfile(srcurl, files_generated)
		u = MMurl.urlopen(srcurl)
		if not self.convert:
			convert = 0
		elif node is not None:
			if type(node) == type({}):
				convert = node.get('project_convert', 1)
			else:
				convert = MMAttrdefs.getattr(node, 'project_convert')
		else:
			convert = 0

		if convert and u.headers.maintype == 'audio' and \
		   u.headers.subtype.find('real') < 0:
			from realconvert import convertaudiofile
			# XXXX This is a hack. convertaudiofile may change the filename (and
			# will, currently, to '.ra').
			if self.progress is not None:
				self.progress("Converting %s"%os.path.split(file)[1], None, None, None, None)
				progress = (self.progress, ("Converting %s"%os.path.split(file)[1], None, None))
			else:
				progress = None
			try:
				cfile = convertaudiofile(u, srcurl, dstdir, file, node,
							 progress = progress)
			except:
				cfile = None
			if cfile:
				files_generated[cfile] = 'b'
				return cfile
			msg = "Cannot convert to RealAudio: %s\n\nUsing source material unconverted."%srcurl
			if node is not None and type(node) != type({}):
				node.set_infoicon('error', msg)
			import windowinterface
			windowinterface.showmessage(msg)
			u = MMurl.urlopen(srcurl)
		if convert and u.headers.maintype == 'video' and \
		   u.headers.subtype.find('real') < 0:
			from realconvert import convertvideofile
			# XXXX This is a hack. convertvideofile may change the filename (and
			# will, currently, to '.rm').
			if self.progress is not None:
				self.progress("Converting %s"%os.path.split(file)[1], None, None, None, None)
				progress = (self.progress, ("Converting %s"%os.path.split(file)[1], None, None))
			else:
				progress = None
			try:
				cfile = convertvideofile(u, srcurl, dstdir, file, node, progress = progress)
			except:
				cfile = None
			if cfile:
				files_generated[cfile] = 'b'
				return cfile
			msg = "Cannot convert to RealVideo: %s\n\nUsing source material unconverted."%srcurl
			if node is not None and type(node) != type({}):
				node.set_infoicon('error', msg)
			import windowinterface
			windowinterface.showmessage(msg)
			u = MMurl.urlopen(srcurl)
		if convert and u.headers.maintype == 'image' and \
		   u.headers.subtype != 'svg-xml' and \
		   u.headers.subtype.find('real') < 0:
			from realconvert import convertimagefile
			# XXXX This is a hack. convertimagefile may change the filename (and
			# will, currently, to '.jpg').
			if self.progress is not None:
				self.progress("Converting %s"%os.path.split(file)[1], None, None, None, None)
			try:
				cfile = convertimagefile(u, srcurl, dstdir, file, node)
			except:
				# XXXX Too many different errors can occur in convertimagefile:
				# I/O errors, image file errors, etc.
				cfile = None
			if cfile:
				files_generated[cfile] = 'b'
				return cfile
			msg = "Cannot convert to Real JPEG: %s\n\nUsing source material unconverted."%srcurl
			if node is not None and type(node) != type({}):
				node.set_infoicon('error', msg)
			import windowinterface
			windowinterface.showmessage(msg)
			u = MMurl.urlopen(srcurl)
##		if convert and u.headers.maintype == 'text' and \
##		   u.headers.subtype != 'html' and \
##		   u.headers.subtype.find('real') < 0:
##			from realconvert import converttextfile
##			# XXXX This is a hack. converttextfile may change the filename (and
##			# will, currently, to '.rt').
##			if self.progress:
##				self.progress("Converting %s"%os.path.split(file)[1], None, None, None, None)
##			file = converttextfile(u, srcurl, dstdir, file, node)
##			files_generated[file] = ''
##			return file
		if u.headers.maintype == 'text' or u.headers.subtype.find('xml') >= 0:
			binary = ''
		else:
			binary = 'b'
		files_generated[file] = binary
		if self.progress is not None:
			self.progress("Copying %s"%os.path.split(file)[1], None, None, None, None)
		dstfile = os.path.join(dstdir, file)
#		print 'DBG verbatim copy', dstfile
		from realconvert import identicalfiles
		if identicalfiles(srcurl, dstfile):
			# src and dst files are the same, don't do anything
			u.close()
			if __debug__:
				print 'src and dst files are identical',dstfile
			return file
		try:
			f = open(dstfile, 'w'+binary)
			while 1:
				data = u.read(10240)
				if not data:
					break
				f.write(data)
			f.close()
			u.close()
		except:
			import windowinterface
			windowinterface.showmessage("Copying %s failed; the document may not play" % srcurl)
		if os.name == 'mac':
			import ic, macfs, macostools
			try:
				icinfo = ic.mapfile(dstfile)
			except ic.error:
				if binary:
					tp = '????'
					cr = '????'
				else:
					tp = 'TEXT'
					cr = 'ttxt'
			else:
				tp = icinfo[1]
				cr = icinfo[2]
			fss = macfs.FSSpec(dstfile)
			fss.SetCreatorType(cr, tp)
			macostools.touched(fss)

		return file

	def fixurl(self, url):
		if self.convertURLs:
			url = MMurl.canonURL(self.context.findurl(url))
			if url[:len(self.convertURLs)] == self.convertURLs:
				url = url[len(self.convertURLs):]
		return url

	def warning(self, msg):
		self.messages.append(msg)

def getid(writer, node):
	uid = node.GetUID()
	name = writer.uid2name[uid]
	if writer.ids_used[name]:
		return name

def getcmifattr(writer, node, attr, default = None):
	val = node.GetRawAttrDef(attr, default)
	if val is not None:
		if default is not None and val == default:
			return None
		val = str(val)
	return val

def getregionname(writer, node):
	from MMTypes import mediatypes
	if node.type not in mediatypes:
		return None
	ch = node.GetChannel()
	return writer.ch2name[ch.GetLayoutChannel()]

def getdefaultregion(writer, node):
	chname = node.GetRawAttrDef('project_default_region', None)
	if not chname:
		return None
	ch = writer.context.getchannel(chname)
	if ch is None:
		return None
	return writer.ch2name[ch]

def getforcechild(writer, node):
	uid = getcmifattr(writer, node, "project_forcechild")
	if not uid:
		return
	id = writer.uid2name.get(uid)
	if not id:
		return
	writer.ids_used[id] = 1
	return id

def getpercentage(writer, node, attr, default = None):
	prop = node.GetRawAttrDef(attr, None)
	if prop is None or prop == default:
		return None
	else:
		return fmtfloat(prop * 100, suffix = '%')

def getmimetype(writer, node):
	if node.GetType() not in mediatypes: # XXX or prefetch?
		return
	if writer.copydir and writer.convert and MMAttrdefs.getattr(node, 'project_convert'):
		# MIME type may be changed by copying, so better not to return any
		return
	mtype = node.GetRawAttrDef('mimetype', None)
	if mtype is None and writer.addattrs:
		url = node.GetAttrDef('file', None) or ''
		if url:
			mtype = urlcache.mimetype(node.GetContext().findurl(url))
	return mtype

def getdescr(writer, node, attr):
	return node.GetRawAttrDef(attr, None) or None

def getsyncarc(writer, node, isend):
	if isend:
		attr = 'endlist'
	else:
		attr = 'beginlist'
	list = []
	for arc in node.GetRawAttrDef(attr, []):
		if arc.srcnode is None and arc.event is None and arc.marker is None and arc.delay is None and arc.wallclock is None:
			if writer.smilboston:
				list.append('indefinite')
			else:
				writer.warning('Lost information about indefinite time')
		elif arc.srcnode is None and arc.event is None and arc.marker is None and arc.wallclock is None and arc.accesskey is None:
			if not writer.smilboston and arc.delay < 0:
				writer.warning('Lost information about negative delay')
			else:
				list.append(fmtfloat(arc.delay, 's'))
		elif arc.wallclock is not None:
			if writer.smilboston:
				list.append(wallclock2string(arc.wallclock))
			else:
				writer.warning('Lost information about wallclock time')
		elif arc.accesskey is not None:
			if writer.smilboston:
				key = 'accesskey(%s)' % arc.accesskey
				if arc.delay:
					key = key + fmtfloat(arc.delay, withsign = 1)
				list.append(key)
			else:
				writer.warning('Lost information about accesskey time')
		elif arc.marker is None:
			srcnode = arc.srcnode
			if type(srcnode) is type('') and srcnode not in ('prev', 'syncbase') and not writer.grinsExt:
				# XPath
				srcnode = arc.refnode()
				if srcnode is None:
					continue
			if arc.channel is not None:
				if not writer.smilboston:
					writer.warning('Lost information about event timing')
					continue
				name = writer.ch2name[arc.channel]
			elif srcnode == 'syncbase':
				name = ''
			elif srcnode == 'prev':
				if not writer.smilboston:
					writer.warning('Lost information about prev time')
					continue
				name = 'prev'
			elif type(srcnode) is type(''):
				name = 'xpath(%s)' % srcnode
				refnode = arc.refnode()
				if writer.prune and refnode is not None and not arc.refnode().WillPlay():
					continue
			elif srcnode.GetRoot() is not node.GetRoot():
				# src node not in document
				continue
			elif writer.prune and srcnode is not None and not srcnode.WillPlay():
				continue
			elif srcnode is node:
				name = ''
			else:
				if not writer.smilboston:
					if srcnode.GetSchedParent() is not node.GetSchedParent():
						writer.warning('Lost information about out-of-scope syncarc')
						continue
					cont = 0
					for n in srcnode.GetPath():
						if n.GetType() in ('animate','animpar','prefetch','brush','excl','prio'):
							writer.warning('Lost informatio about syncarc from non-included object')
							cont = 1
							break
					if cont:
						continue
					name = writer.uid2name[srcnode.GetUID()]
				else:
					name = escape_name(writer.uid2name[srcnode.GetUID()])
			if arc.event is not None:
				if not writer.smilboston and arc.event not in ('begin', 'end'):
					writer.warning('Lost information about event timing')
					continue
				if writer.smilboston:
					if name:
						name = name + '.'
					name = name + escape_name(arc.event, 0)
				else:
					if arc.event == 'end':
						if arc.delay != 0:
							writer.warning('Lost information about delay')
							continue
						name = 'id(%s)(end)' % name
					elif arc.event == 'begin':
						if arc.delay < 0:
							writer.warning('Lost information about negative delay')
							continue
						if arc.delay == 0:
							name = 'id(%s)(begin)' % name
						else:
							name = 'id(%s)(%s)' % (name, fmtfloat(arc.delay))
					else:
						writer.warning('Lost information about event timing')
						continue
			if arc.delay or not name:
				if name:
					if writer.smilboston:
						name = name + fmtfloat(arc.delay, withsign = 1)
				else:
					if not writer.smilboston and arc.delay < 0:
						writer.warning('Lost information about negative delay')
						continue
					name = fmtfloat(arc.delay, withsign = 0)
			list.append(name)
		else:
			if not writer.smilboston:
				writer.warning('Lost information about marker timing')
			else:
				list.append('%s.marker(%s)' % (escape_name(writer.uid2name[arc.srcnode.GetUID()]), arc.marker))
	if not list:
		return
	if not writer.smilboston and len(list) > 1:
		writer.warning('Lost information about multiple %s times' % ['begin','end'][isend])
		return list[0]		# just return the first
	return ';'.join(list)

def getduration(writer, node, attr = 'duration'):
	duration = node.GetRawAttrDef(attr, None)
	if duration is None:		# no duration
		return None
	elif duration == -1:		# infinite duration...
		return 'indefinite'
	elif duration == -2:
		return 'media'
	else:
		return fmtfloat(duration, 's')

def getmin(writer, node):
	if not writer.smilboston:
		return
	min = node.GetRawAttrDef('min', None)
	if min == -2:
		return 'media'
	elif not min:
		return None		# 0 or None
	return fmtfloat(min, 's')

def getmax(writer, node):
	if not writer.smilboston:
		return
	max = node.GetRawAttrDef('max', None)
	if max is None:
		return None
	elif max == -1:
		return 'indefinite'
	elif max == -2:
		return 'media'
	return fmtfloat(max, 's')

def getterm(writer, node):
	if node.type in ('seq', 'prio', 'switch'):
		return
	if not writer.smilboston and node.type in mediatypes:
		return
	terminator = node.GetTerminator()
	ntype = node.GetType()
	if terminator == 'LAST':
		if ntype in ('par', 'excl'):
			return
		return 'last'
	if terminator == 'FIRST':
		return 'first'
	if terminator == 'ALL':
		return 'all'
	if terminator == 'MEDIA' and ntype in mediatypes:
		return
	for child in node.children:
		if child.GetRawAttrDef('name', '') == terminator:
			id = writer.uid2name[child.GetUID()]
			if writer.smilboston:
				if id in ('all', 'first', 'last', 'media'):
					return '\\' + id
				else:
					return id
			else:
				return 'id(%s)' % id
	print '** Terminator attribute refers to unknown child in', \
	      node.GetRawAttrDef('name', '<unnamed>'),\
	      node.GetUID()

def getrepeat(writer, node):
	value = node.GetAttrDef('loop', None)
	if value is None:
		return
	if value == 0:
		return 'indefinite'
	else:
		return fmtfloat(value)

nonascii = re.compile('[\200-\377]')
def getsrc(writer, node, attr = None):
	if attr is None:
		ntype = node.GetType()
		chtype = node.GetChannelType()
		if chtype == 'brush':
			return None
		elif ntype == 'ext':
			val = node.GetAttrDef('file', None)
		elif ntype == 'imm':
			if chtype == 'html':
				mime = 'text/html'
##			elif chtype == 'RealPix':
##				mime = 'image/vnd.rn-realpix'
			else:
				mime = ''
			# This funny way of handling empty lines is for
			# the benefit of RealONE, and it doesn't harm
			# GRiNS.
			data = ''
			for line in node.GetValues():
				if not line:
					data = data + '\n'
				else:
					data = data + line + '\r\n'
##			'\r\n'.join(node.GetValues())
##			if data and data[-1] != '\n':
##				# end with newline if not empty
##				data = data + '\n'
			if nonascii.search(data):
				mime = mime + ';charset=ISO-8859-1'
			val = 'data:%s,%s' % (mime, MMurl.quote(data))
		else:
			return None
		if chtype == 'RealPix':
			# special case for RealPix nodes, which we should write
			# sometimes, but don't want to write always
			do_write = 0
			tmp_file_name = 0
			if not val and not writer.copydir:
				# no URL and not exporting, save as data: URL
				import base64, realnode
				node.SetAttr('file', MMurl.basejoin(writer.convertURLs, 'dummy.rp'))
				data = realnode.writenode(node, tostring = 1)
				node.DelAttr('file')
				return 'data:image/vnd.rn-realpix;base64,' + \
				       ''.join(base64.encodestring(data).split('\n'))
##				return 'data:image/vnd.rn-realpix;charset=ISO-8859-1,' + \
##				       MMurl.quote(data)
			if not val:
				val = writer.gen_rpfile()
				do_write = 1
				tmp_file_name = 1
				node.SetAttr('file', val)
			if hasattr(node, 'tmpfile') and not writer.copydir:
				# Also save if the node has changed and we're saving (not exporting)
				do_write = 1
			if do_write:
				import realnode
				realnode.writenode(node)
			if tmp_file_name:
				node.DelAttr('file')
	else:
		val = node.GetAttrDef(attr, None)
		if not val:
			return None
	if not val:
		if writer.copydir:
			# Exporting without a URL is an error
			from windowinterface import showmessage
			node.set_infoicon('error', 'No media URL given.')
			nmsg = ''
			name = node.GetRawAttrDef('name', '')
			if name:
				nmsg = 'Media item %s: '
			showmessage(nmsg + 'No URL set, the document may not be playable.')
		else:
			# If not exporting we insert a placeholder
			val = '#'
		return val
	if val[:5] == 'data:':
		# don't convert data: URLs to text files
		return val
	if not writer.copydir:
		return writer.fixurl(val)
	url = writer.context.findurl(val)
	return copysrc(writer, node, url, writer.copycache, writer.files_generated, writer.copydirurl)

def getsensitivity(writer, node):
	if not writer.smilboston:
		return
	sensitivity = node.GetRawAttrDef('sensitivity', None)
	if sensitivity is None:
		return
	if sensitivity >= 100:
		return 'transparent'
	elif sensitivity <= 0:
		return			# 'opaque' is default
	elif 0 < sensitivity < 100:
		return '%d%%' % sensitivity

def getattributetype(writer, node):
	if not writer.smilboston:
		return
	atype = node.GetRawAttrDef('attributeType', 'XML')
	if atype != 'XML':
		return atype

def getspeed(writer, node, attr = 'speed'):
	speed = node.GetRawAttrDef(attr, None)
	if speed is not None:
		return fmtfloat(speed)

def getproportion(writer, node, attr):
	prop = node.GetRawAttrDef(attr, None)
	if prop is not None:
		return fmtfloat(prop)

def getautoreverse(writer, node):
	if not writer.smilboston:
		return
	if node.GetRawAttrDef('autoReverse', None):
		return 'true'
	return None

def getboolean(writer, node, attr, truefalse = 0, default = None):
	value = node.GetRawAttrDef(attr, None)
	if value is not None:
		if default is not None and value == default:
			return None
		if value:
			if truefalse:
				return 'true'
			return 'on'
		else:
			if truefalse:
				return 'false'
			return 'off'

def getscreensize(writer, node):
	value = node.GetRawAttrDef('system_screen_size', None)
	if value is not None:
		return '%dX%d' % (value[1], value[0])

def getsyscomp(writer, node, attr):
	syscomp = node.GetRawAttrDef('system_component', [])
	if syscomp:
		return ' '.join(syscomp)

def getsysreq(writer, node, attr):
	sysreq = node.GetRawAttrDef('system_required', [])
	if sysreq:
		return ' + '.join(map(lambda i: 'ext%d' % i, range(len(sysreq))))

def getugroup(writer, node):
	if not writer.smilboston:
		return
	if not writer.context.usergroups:
		return
	names = []
	for u_group in node.GetRawAttrDef('u_group', []):
		try:
			names.append(writer.ugr2name[u_group])
		except KeyError:
			print '** Attempt to write unknown usergroup', u_group
	if not names:
		return
	return ' + '.join(names)

def getlayout(writer, node):
	if not writer.context.layouts:
		return
	if writer.html:
		return
	layout = node.GetRawAttrDef('layout', 'undefined')
	if layout == 'undefined':
		return
	try:
		return writer.layout2name[layout]
	except KeyError:
		print '** Attempt to write unknown layout', layout
		return

def getfgcolor(writer, node):
	if node.GetChannelType() != 'brush':
		return None
	fgcolor = node.GetRawAttrDef('fgcolor', None)
	if fgcolor is None:
		return
	return translatecolor(fgcolor)

def getsubregionatt(writer, node, attr):
	from windowinterface import UNIT_PXL, UNIT_SCREEN

	val = node.GetRawAttrDef(attr, None)
	if val is not None:
		# save only if subregion positioning is different than region
		if val == 0:
			return None

		if type(val) == type (0.0):
			return fmtfloat(100*val, '%', prec = 2)
		else:
			return str(val)
	return None

def getbgcoloratt(writer, node, attr):
	if not ChannelMap.isvisiblechannel(node.GetChannelType()):
		return None
	# if transparent, there is no backgroundColor attribute
	transparent = node.GetRawAttrDef('transparent', None)
	if transparent is None:
		return 'inherit'
	elif transparent:
		return None
	
	bgcolor = node.GetRawAttrDef('bgcolor', None)
	if bgcolor is None:
		return None
	return translatecolor(bgcolor)

def getpath(writer, node):
	if not writer.smilboston:
		return
	attr = node.GetRawAttrDef('path', None)
	if attr is None:
		return
	# strange but IE manages only spaces
	# grins both spaces and commas
	# so use spaces at least for now
	attr = ' '.join(attr.split(','))
	# collapse multiple spaces to one
	attr = ' '.join(attr.split())
	return attr

def getorigin(writer, node):
	if not writer.smilboston:
		return
	origin = node.GetRawAttrDef('origin', 'parent')
	if origin == 'parent':
		return None
	return 'element'

def getaccumulate(writer, node):
	if not writer.smilboston:
		return
	accumulate = node.GetRawAttrDef('accumulate', 'none')
	if accumulate == 'none':
		return None
	return accumulate

def getadditive(writer, node):
	if not writer.smilboston:
		return
	additive = node.GetRawAttrDef('additive', 'replace')
	if additive == 'replace':
		return None
	return additive

def getcalcmode(writer, node):
	if not writer.smilboston:
		return
	mode = node.GetRawAttrDef('calcMode', 'linear')
	tag = node.GetRawAttrDef('atag', 'animate')
	if tag!='animateMotion' and mode == 'linear':
		return None
	elif tag=='animateMotion' and mode == 'paced':
		return None
	return mode

def getKeyTimes(writer, node):
	if not writer.smilboston:
		return
	keyTimes = node.GetRawAttrDef('keyTimes', [])
	if not keyTimes:
		return
	values = []
	for val in keyTimes:
		values.append(fmtfloat(val, prec = 3))
	return ';'.join(values)

def gettransition(writer, node, which):
	if not writer.context.transitions:
		return
	transition = node.GetRawAttrDef(which, None)
	if not transition:
		return
	list = []
	for tr in transition:
		try:
			list.append(writer.transition2name[tr])
		except KeyError:
			print '** Attempt to write unknown transition', tr
			list.append(tr)
	return ';'.join(list)

def getinlinetrmode(writer, node):
	if not writer.smilboston:
		return
	mode = node.GetRawAttrDef('mode', 'in')
	if mode == 'in':
		return None
	return mode

def getcolor(writer, node, attr, use_name = 1):
	color = node.GetRawAttrDef(attr, None)
	if color is None:
		return
	return translatecolor(color, use_name)

def getcollapsed(writer, node):
	ntype = node.GetType()
	if ntype in interiortypes:
		if node.collapsed:
			return 'true'
	elif ntype in mediatypes:
		if not node.collapsed:
			return 'false'

def getshowtime(writer, node):
	if node.showtime:
		return node.showtime

def gettimezoom(writer, node):
	try:
		scale = node.min_pxl_per_sec
	except:
		return
	return fmtfloat(scale)

def getallowedmimetypes(writer, node):
	mimetypes = node.GetRawAttrDef('allowedmimetypes', None)
	if not mimetypes:
		return None
	return ','.join(mimetypes)

def getintrinsicwidth(writer, node):
	if not writer.addattrs:
		return
	if node.GetType() != 'ext':
		return
	url = node.GetFile()
	if url:
		import Sizes
		width, height = Sizes.GetSize(url)
		if width:
			return `width`

def getintrinsicheight(writer, node):
	if not writer.addattrs:
		return
	if node.GetType() != 'ext':
		return
	url = node.GetFile()
	if url:
		import Sizes
		width, height = Sizes.GetSize(url)
		if height:
			return `height`

def getintrinsicduration(writer, node):
	if not writer.addattrs:
		return
	if node.GetType() != 'ext':
		return
	url = node.GetAttrDef('file', None) or ''
	if url:
		import Duration
		dur = Duration.getintrinsicduration(node, 0)
		if dur > 0:
			return fmtfloat(dur)

#
# Mapping from SMIL attrs to functions to get them. Strings can be
# used as a shortcut for node.GetAttr
#
addattrs = ['type', 'iwidth', 'iheight', 'idur']
smil_attrs=[
	("id", getid, None),
	("title", lambda writer, node:getcmifattr(writer, node, "title"), "title"),
	("region", getregionname, None),
	("project_default_region", getdefaultregion, "project_default_region"),
	("project_default_region_image", lambda writer, node:getcmifattr(writer, node, "project_default_region_image"), "project_default_region_image"),
	("project_default_region_video", lambda writer, node:getcmifattr(writer, node, "project_default_region_video"), "project_default_region_video"),
	("project_default_region_sound", lambda writer, node:getcmifattr(writer, node, "project_default_region_sound"), "project_default_region_sound"),
	("project_default_region_text", lambda writer, node:getcmifattr(writer, node, "project_default_region_text"), "project_default_region_text"),
	("project_forcechild", getforcechild, "project_forcechild"),
	("project_default_type", lambda writer, node:getcmifattr(writer, node, 'project_default_type'), "project_default_type"),
	("project_bandwidth_fraction", lambda writer, node:getpercentage(writer, node, 'project_bandwidth_fraction'), "project_bandwidth_fraction"),
	("type", getmimetype, None),
	("author", lambda writer, node:getcmifattr(writer, node, "author"), "author"),
	("copyright", lambda writer, node:getcmifattr(writer, node, "copyright"), "copyright"),
	("abstract", lambda writer, node:getcmifattr(writer, node, "abstract"), "abstract"),
	("alt", lambda writer, node: getdescr(writer, node, 'alt'), "alt"),
	("longdesc", lambda writer, node: getdescr(writer, node, 'longdesc'), "longdesc"),
	("readIndex", lambda writer, node:(writer.smilboston and getcmifattr(writer, node, "readIndex", 0)) or None, "readIndex"),
	("begin", lambda writer, node: getsyncarc(writer, node, 0), None),
	("dur", getduration, "duration"),
	("project_default_duration", lambda writer, node: getduration(writer, node, 'project_default_duration'), "project_default_duration"),
	("project_default_duration_image", lambda writer, node: getduration(writer, node, 'project_default_duration_image'), "project_default_duration_image"),
	("project_default_duration_text", lambda writer, node: getduration(writer, node, 'project_default_duration_text'), "project_default_duration_text"),
	("min", getmin, "min"),
	("max", getmax, "max"),
	("end", lambda writer, node: getsyncarc(writer, node, 1), None),
	("fill", lambda writer, node: getcmifattr(writer, node, 'fill', 'default'), "fill"),
	("fillDefault", lambda writer, node: (writer.smilboston and getcmifattr(writer, node, 'fillDefault', 'inherit')) or None, "fillDefault"),
	("erase", lambda writer, node:(writer.smilboston and getcmifattr(writer, node, 'erase', 'whenDone')) or None, "erase"),
	("syncBehavior", lambda writer, node: (writer.smilboston and getcmifattr(writer, node, 'syncBehavior', 'default')) or None, "syncBehavior"),
	("syncBehaviorDefault", lambda writer, node: (writer.smilboston and getcmifattr(writer, node, 'syncBehaviorDefault', 'inherit')) or None, "syncBehaviorDefault"),
	("endsync", getterm, None),
	("repeat", lambda writer, node:(not writer.smilboston and getrepeat(writer, node)) or None, "loop"),
	("repeatCount", lambda writer, node:(writer.smilboston and getrepeat(writer, node)) or None, "loop"),
	("repeatDur", lambda writer, node:(writer.smilboston and getduration(writer, node, "repeatdur")) or None, "repeatdur"),
	("restart", lambda writer, node: (writer.smilboston and getcmifattr(writer, node, 'restart', 'default')) or None, "restart"),
	("restartDefault", lambda writer, node: (writer.smilboston and getcmifattr(writer, node, 'restartDefault', 'inherit')) or None, "restartDefault"),
	("src", lambda writer, node:getsrc(writer, node), None),
	("clip-begin", lambda writer, node: (not writer.smilboston and getcmifattr(writer, node, 'clipbegin')) or None, "clipbegin"),
	("clip-end", lambda writer, node: (not writer.smilboston and getcmifattr(writer, node, 'clipend')) or None, "clipend"),
	("clipBegin", lambda writer, node: (writer.smilboston and getcmifattr(writer, node, 'clipbegin')) or None, "clipbegin"),
	("clipEnd", lambda writer, node: (writer.smilboston and getcmifattr(writer, node, 'clipend')) or None, "clipend"),
	("sensitivity", getsensitivity, "sensitivity"),
	("mediaRepeat", lambda writer, node: (writer.smilboston and getcmifattr(writer, node, 'mediaRepeat')) or None, "mediaRepeat"),
	("targetElement", lambda writer, node: (writer.smilboston and node.GetRawAttrDef("targetElement", None)) or None, "targetElement"),
	("attributeName", lambda writer, node: (writer.smilboston and node.GetRawAttrDef("attributeName", None)) or None, "attributeName"),
	("attributeType", getattributetype, "attributeType"),
	("speed", lambda writer, node: (writer.smilboston and getspeed(writer, node, "speed")) or None, "speed"),
	("accelerate", lambda writer, node: (writer.smilboston and getproportion(writer, node, "accelerate")) or None, "accelerate"),
	("decelerate", lambda writer, node: (writer.smilboston and getproportion(writer, node, "decelerate")) or None, "decelerate"),
	("autoReverse", getautoreverse, "autoReverse"),
	("system-bitrate", lambda writer, node:(not writer.prune and not writer.smilboston and getcmifattr(writer, node, "system_bitrate")) or None, "system_bitrate"),
	("system-captions", lambda writer, node:(not writer.prune and not writer.smilboston and getboolean(writer, node, 'system_captions')) or None, "system_captions"),
	("system-language", lambda writer, node:((not writer.prune or None) and (not writer.smilboston or None) and getcmifattr(writer, node, "system_language")), "system_language"),
	("system-overdub-or-caption", lambda writer, node:(not writer.prune and not writer.smilboston and {'overdub':'overdub','subtitle':'caption'}.get(getcmifattr(writer, node, "system_overdub_or_caption"))) or None, None),
	("system-required", lambda writer, node:(not writer.prune and not writer.smilboston and getcmifattr(writer, node, "system_required")) or None, "system_required"),
	("system-screen-size", lambda writer, node:(not writer.prune and not writer.smilboston and getscreensize(writer, node)) or None, "system_screen_size"),
	("system-screen-depth", lambda writer, node:(not writer.prune and not writer.smilboston and getcmifattr(writer, node, "system_screen_depth")) or None, "system_screen_depth"),
	("systemAudioDesc", lambda writer, node:(not writer.prune and writer.smilboston and getboolean(writer, node, 'system_audiodesc')) or None, "system_audiodesc"),
	("systemBitrate", lambda writer, node:(not writer.prune and writer.smilboston and getcmifattr(writer, node, "system_bitrate")) or None, "system_bitrate"),
	("systemCaptions", lambda writer, node:(not writer.prune and writer.smilboston and getboolean(writer, node, 'system_captions')) or None, "system_captions"),
	("systemComponent", lambda writer, node:(not writer.prune and writer.smilboston and getsyscomp(writer, node, 'system_component')) or None, "system_component"),
	("systemCPU", lambda writer, node:(not writer.prune and writer.smilboston and getcmifattr(writer, node, "system_cpu")) or None, "system_cpu"),
	("systemLanguage", lambda writer, node:((not writer.prune or None) and (writer.smilboston or None) and getcmifattr(writer, node, "system_language")), "system_language"),
	("systemOperatingSystem", lambda writer, node:(not writer.prune and writer.smilboston and getcmifattr(writer, node, "system_operating_system")) or None, "system_operating_system"),
	("systemOverdubOrSubtitle", lambda writer, node:(not writer.prune and writer.smilboston and getcmifattr(writer, node, "system_overdub_or_caption")) or None, "system_overdub_or_caption"),
	("systemRequired", lambda writer, node:(not writer.prune and writer.smilboston and getsysreq(writer, node, "system_required")) or None, "system_required"),
	("systemScreenSize", lambda writer, node:(not writer.prune and writer.smilboston and getscreensize(writer, node)) or None, "system_screen_size"),
	("systemScreenDepth", lambda writer, node:(not writer.prune and writer.smilboston and getcmifattr(writer, node, "system_screen_depth")) or None, "system_screen_depth"),
	("customTest", getugroup, "u_group"),
	("layout", getlayout, "layout"),
	("color", getfgcolor, "fgcolor"),		# only for brush element
	# subregion positioning
	("left", lambda writer, node: (writer.smilboston and getsubregionatt(writer, node, 'left')) or None, "left"),
	("right", lambda writer, node: (writer.smilboston and getsubregionatt(writer, node, 'right')) or None, "right"),
	("width", lambda writer, node: (writer.smilboston and getsubregionatt(writer, node, 'width')) or None, "width"),
	("top", lambda writer, node: (writer.smilboston and getsubregionatt(writer, node, 'top')) or None, "top"),
	("bottom", lambda writer, node: (writer.smilboston and getsubregionatt(writer, node, 'bottom')) or None, "bottom"),
	("height", lambda writer, node: (writer.smilboston and getsubregionatt(writer, node, 'height')) or None, "height"),
	("fit", lambda writer, node: (writer.smilboston and getcmifattr(writer, node, 'fit')) or None, "fit"),
	# registration points
	("regPoint", lambda writer, node: (writer.smilboston and getcmifattr(writer, node, "regPoint", 'topLeft')) or None, "regPoint"),
	("regAlign", lambda writer, node: (writer.smilboston and getcmifattr(writer, node, "regAlign", 'topLeft')) or None, "regAlign"),

	("backgroundColor", lambda writer, node: (writer.smilboston and getbgcoloratt(writer, node, "bgcolor")) or None, None),
	("z-index", lambda writer, node: (writer.smilboston and getcmifattr(writer, node, "z")) or None, "z"),
	("from", lambda writer, node: (writer.smilboston and node.GetRawAttrDef("from", None)) or None, "from"),
	("to", lambda writer, node: (writer.smilboston and node.GetRawAttrDef("to", None)) or None, "to"),
	("by", lambda writer, node: (writer.smilboston and node.GetRawAttrDef("by", None)) or None, "by"),
	("values", lambda writer, node: (writer.smilboston and node.GetRawAttrDef("values", None)) or None, "values"),
	("path", getpath, "path"),
	("origin", getorigin, "origin"),
	("accumulate", getaccumulate, "accumulate"),
	("additive", getadditive, "additive"),
	("calcMode", getcalcmode, None),
	("keyTimes", getKeyTimes, "keyTimes"),
	("keySplines", lambda writer, node: (writer.smilboston and node.GetRawAttrDef("keySplines", None)) or None, "keySplines"),
	("transIn", lambda writer, node: (writer.smilboston and gettransition(writer, node, "transIn")) or None, "transIn"),
	("transOut", lambda writer, node: (writer.smilboston and gettransition(writer, node, "transOut")) or None, "transOut"),
	("mode", getinlinetrmode, "mode"),
	("subtype", lambda writer, node: (writer.smilboston and node.GetRawAttrDef("subtype", None)) or None, "subtype"),

	("mediaSize", lambda writer, node: (writer.smilboston and node.GetRawAttrDef("mediaSize", None)) or None, "mediaSize"),
	("mediaTime", lambda writer, node: (writer.smilboston and node.GetRawAttrDef("mediaTime", None)) or None, "mediaTime"),
	("bandwidth", lambda writer, node: (writer.smilboston and node.GetRawAttrDef("bandwidth", None)) or None, "bandwidth"),

	("thumbnailIcon", lambda writer, node: (writer.grinsExt and getsrc(writer, node, 'thumbnail_icon')) or None, "thumbnail_icon"),
	("thumbnailScale", lambda writer, node: getboolean(writer, node, 'thumbnail_scale', 1), "thumbnail_scale"),
	("emptyIcon", lambda writer, node: (writer.grinsExt and getsrc(writer, node, 'empty_icon')) or None, "empty_icon"),
	("emptyText", lambda writer, node:getcmifattr(writer, node, "empty_text"), "empty_text"),
	("emptyColor", lambda writer, node: getcolor(writer, node, "empty_color"), "empty_color"),
	("emptyDur", lambda writer, node:getduration(writer, node, "empty_duration"), "empty_duration"),
	("nonEmptyIcon", lambda writer, node: (writer.grinsExt and getsrc(writer, node, 'non_empty_icon')) or None, "non_empty_icon"),
	("nonEmptyText", lambda writer, node:getcmifattr(writer, node, "non_empty_text"), "non_empty_text"),
	("nonEmptyColor", lambda writer, node: getcolor(writer, node, "non_empty_color"), "non_empty_color"),
	("dropIcon", lambda writer, node: (writer.grinsExt and getsrc(writer, node, 'dropicon')) or None, "dropicon"),
	("collapsed", getcollapsed, None),
	("showtime", getshowtime, None),
	("timezoom", gettimezoom, None),
	("previewShowOption", lambda writer, node:getcmifattr(writer, node, "previewShowOption"), "previewShowOption"),
	("allowedmimetypes", getallowedmimetypes, None),
	("project_autoroute", lambda writer, node:getboolean(writer, node, "project_autoroute", 1, 0), "project_autoroute"),
	("project_readonly", lambda writer, node:getboolean(writer, node, "project_readonly", 1, 0), "project_readonly"),
	("showAnimationPath", lambda writer, node:getboolean(writer, node, "showAnimationPath", 1, 1), "showAnimationPath"),
	("iwidth", getintrinsicwidth, None),
	("iheight", getintrinsicheight, None),
	("idur", getintrinsicduration, None),
]
prio_attrs = [
	("id", getid, None),
	("title", lambda writer, node:getcmifattr(writer, node, "title"), "title"),
	("author", lambda writer, node:getcmifattr(writer, node, "author"), "author"),
	("copyright", lambda writer, node:getcmifattr(writer, node, "copyright"), "copyright"),
	("abstract", lambda writer, node:getcmifattr(writer, node, "abstract"), "abstract"),
	('lower', lambda writer, node: getcmifattr(writer, node, 'lower', 'defer'), "lower"),
	('peers', lambda writer, node: getcmifattr(writer, node, 'peers', 'stop'), "peers"),
	('higher', lambda writer, node: getcmifattr(writer, node, 'higher', 'pause'), "higher"),
	('pauseDisplay', lambda writer, node: getcmifattr(writer, node, 'pauseDisplay', 'inherit'), "pauseDisplay"),
	("thumbnailIcon", lambda writer, node: (writer.grinsExt and getsrc(writer, node, 'thumbnail_icon')) or None, "thumbnail_icon"),
	("thumbnailScale", lambda writer, node: getboolean(writer, node, 'thumbnail_scale', 1), "thumbnail_scale"),
	("emptyIcon", lambda writer, node: (writer.grinsExt and getsrc(writer, node, 'empty_icon')) or None, "empty_icon"),
	("emptyText", lambda writer, node:getcmifattr(writer, node, "empty_text"), "empty_text"),
	("emptyColor", lambda writer, node: getcolor(writer, node, "empty_color"), "empty_color"),
	("emptyDur", lambda writer, node:getduration(writer, node, "empty_duration"), "empty_duration"),
	("nonEmptyIcon", lambda writer, node: (writer.grinsExt and getsrc(writer, node, 'non_empty_icon')) or None, "non_empty_icon"),
	("nonEmptyText", lambda writer, node:getcmifattr(writer, node, "non_empty_text"), "non_empty_text"),
	("nonEmptyColor", lambda writer, node: getcolor(writer, node, "non_empty_color"), "non_empty_color"),
	("dropIcon", lambda writer, node: (writer.grinsExt and getsrc(writer, node, 'dropicon')) or None, "dropicon"),
	("collapsed", getcollapsed, None),
	("showtime", getshowtime, None),
	("timezoom", gettimezoom, None),
	]
