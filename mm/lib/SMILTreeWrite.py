__version__ = "$Id$"

# MMWrite -- Multimedia tree writing interface


from MMExc import *		# Exceptions
from MMTypes import mediatypes, interiortypes
import MMAttrdefs
import Hlinks
import ChannelMap
import colors
import features
import compatibility
import string
import os
import MMurl
import MMmimetypes
import re

from SMIL import *

interiortypes = interiortypes + ['foreign']

from nameencode import nameencode

NSGRiNSprefix = 'GRiNS'
NSRP9prefix = 'rn'
NSQTprefix = 'qt'

# This string is written at the start of a SMIL file.
##encoding = ' encoding="ISO-8859-1"'
encoding = ''				# Latin-1 (ISO-8859-1) coincides with lower part of Unicode
SMILdecl = '<?xml version="1.0"%s?>\n' % encoding
doctype = '<!DOCTYPE smil PUBLIC "%s"\n%s"%s">\n' % (SMILpubid,' '*22,SMILdtd)
doctype2 = '<!DOCTYPE smil PUBLIC "%s"\n%s"%s">\n' % (SMILBostonPubid,' '*22,SMILBostonDtd)
xmlnsGRiNS = 'xmlns:%s' % NSGRiNSprefix
xmlnsRP9 = 'xmlns:%s' % NSRP9prefix
xmlnsQT = 'xmlns:%s' % NSQTprefix

nonascii = re.compile('[\200-\377]')

isidre = re.compile('^[a-zA-Z_][-A-Za-z0-9._]*$')

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



# Write a node to a CMF file, given by filename

Error = 'Error'
cancel = 'cancel'

def WriteFile(root, filename, grinsExt = 1, qtExt = features.EXPORT_QT in features.feature_set,
	      rpExt = features.EXPORT_REAL in features.feature_set, copyFiles = 0, convertfiles = 1, convertURLs = 0,
	      evallicense = 0, progress = None, prune = 0, smil_one = 0):
	try:
		writer = SMILWriter(root, None, filename, grinsExt = grinsExt, qtExt = qtExt, rpExt = rpExt, copyFiles = copyFiles, convertfiles = convertfiles, convertURLs = convertURLs, evallicense = evallicense, progress = progress, prune = prune, smil_one = smil_one)
	except Error, msg:
		from windowinterface import showmessage
		showmessage(msg, mtype = 'error')
		return

	try:
		writer.write()
	except cancel:
		return

	if os.name == 'mac':
		import macfs
		import macostools
		fss = macfs.FSSpec(filename)
		if rpExt and not grinsExt:
			fss.SetCreatorType('PNst', 'PNRA')
		else:
			fss.SetCreatorType('GRIN', 'TEXT')
		macostools.touched(fss)

import FtpWriter
def WriteFTP(root, filename, ftpparams, wftpparams, grinsExt = 1, qtExt = features.EXPORT_QT in features.feature_set,
	     rpExt = features.EXPORT_REAL in features.feature_set, copyFiles = 0, convertfiles = 1, convertURLs = 0,
	     evallicense = 0, progress = None, prune = 0, smil_one = 0, weburl = None):
	host, user, passwd, dir = ftpparams
	try:
		conn = FtpWriter.FtpConnection(host, user=user, passwd=passwd, dir=dir)
		ftp = conn.Writer(filename, ascii=1)
		try:
			writer = SMILWriter(root, ftp, filename, tmpcopy = 1, grinsExt = grinsExt, qtExt = qtExt, rpExt = rpExt, copyFiles = copyFiles, convertfiles = convertfiles, convertURLs = convertURLs, evallicense = evallicense, progress = progress, prune = prune, smil_one = smil_one, weburl = weburl)
		except Error, msg:
			from windowinterface import showmessage
			showmessage(msg, mtype = 'error')
			return
		try:
			writer.write()
		except cancel:
			return
		#
		# Upload generated media items
		#
		srcdir, dstdir, filedict, webfiledict = writer.getcopyinfo()
		del writer
		del ftp
		if copyFiles and filedict:
			conn.chmkdir(dstdir)
			totfiles = len(filedict.keys())
			num = 0
			for filename in filedict.keys():
				num = num + 1
				binary = filedict[filename] # Either 'b' or '', or None for dummies
				if binary is None:
					continue
				ascii = not binary
				localfilename = os.path.join(srcdir, filename)
				remotefilename = os.path.split(filename)[1] # Remove the : for mac filenames
				ifp = open(localfilename, 'r'+binary)
				if progress:
					ifp.seek(0, 2)
					totsize = ifp.tell()
					ifp.seek(0, 0)
					progress("Uploading %s"%remotefilename, num, totfiles, 0, totsize)
				ofp = conn.Writer(remotefilename, ascii=ascii)
				while 1:
					data = ifp.read(16*1024)
					if not data:
						break
					ofp.write(data)
					if progress:
						progress("Uploading %s"%remotefilename, num, totfiles, ifp.tell(), totsize)
				ifp.close()
				ofp.close()
		if copyFiles and webfiledict:
			whost, wuser, wpasswd, wdir = wftpparams
			if host != whost or user != wuser:
				conn = FtpWriter.FtpConnection(whost, user=wuser, passwd=wpasswd, dir=wdir)
			else:
				conn.chmkdir(wdir)
			conn.chmkdir(dstdir)
			totfiles = len(webfiledict.keys())
			num = 0
			for filename in webfiledict.keys():
				num = num + 1
				binary = webfiledict[filename] # Either 'b' or '', or None for dummies
				if binary is None:
					continue
				ascii = not binary
				localfilename = os.path.join(srcdir, filename)
				remotefilename = os.path.split(filename)[1] # Remove the : for mac filenames
				ifp = open(localfilename, 'r'+binary)
				if progress:
					ifp.seek(0, 2)
					totsize = ifp.tell()
					ifp.seek(0, 0)
					progress("Uploading %s"%remotefilename, num, totfiles, 0, totsize)
				ofp = conn.Writer(remotefilename, ascii=ascii)
				while 1:
					data = ifp.read(16*1024)
					if not data:
						break
					ofp.write(data)
					if progress:
						progress("Uploading %s"%remotefilename, num, totfiles, ifp.tell(), totsize)
				ifp.close()
				ofp.close()
	except FtpWriter.all_errors, msg:
		from windowinterface import showmessage
		showmessage('Mediaserver upload failed: %s'%(msg,), mtype = 'error')
		return
	except IOError, arg:
		from windowinterface import showmessage
		showmessage('Mediaserver upload failed: %s'%(msg,), mtype = 'error')
		return

import StringIO
class MyStringIO(StringIO.StringIO):
	def close(self):
		pass

def WriteString(root, grinsExt = 1, evallicense = 0, set_char_pos = 0, prune = 0, smil_one = 0):
	fp = MyStringIO()
	writer = SMILWriter(root, fp, '<string>', grinsExt = grinsExt, evallicense = evallicense, set_char_pos = set_char_pos, prune = prune, smil_one = smil_one)
	try:
		writer.write()
	except cancel:
		return ''
	return fp.getvalue()

def WriteBareString(node, grinsExt = 1, prune = 0, smil_one = 0):
	fp = MyStringIO()
	writer = SMILWriter(node, fp, '<string>', grinsExt = grinsExt, prune = prune, smil_one = smil_one)
	try:
		writer.writebare()
	except cancel:
		return ''
	return fp.getvalue()

#
# Functions to encode data items
#
from fmtfloat import fmtfloat

def getid(writer, node):
	uid = node.GetUID()
	name = writer.uid2name[uid]
	if writer.ids_used[name]:
		return name

def getforcechild(writer, node):
	uid = getcmifattr(writer, node, "project_forcechild")
	if not uid:
		return
	id = writer.uid2name.get(uid)
	if not id:
		return
	writer.ids_used[id] = 1
	return id

def geturl(writer, node, attr):
	val = node.GetAttrDef(attr, None)
	if not val:
		return val
	return writer.fixurl(val)

def getsrc(writer, node):
	ntype = node.GetType()
	chtype = node.GetChannelType()
	if chtype == 'brush':
		return None
	elif ntype == 'ext':
		val = node.GetAttrDef('file', None)
	elif ntype == 'imm':
		if chtype == 'html':
			mime = 'text/html'
##		elif chtype == 'RealPix':
##			mime = 'image/vnd.rn-realpix'
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
##		'\r\n'.join(node.GetValues())
##		if data and data[-1] != '\n':
##			# end with newline if not empty
##			data = data + '\n'
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
##			return 'data:image/vnd.rn-realpix;charset=ISO-8859-1,' + \
##			       MMurl.quote(data)
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
	if chtype == 'text' and val[:5] == 'data:':
		# don't convert data: URLs to text files
		return val
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
	if not writer.copydir:
		return writer.fixurl(val)
	url = writer.context.findurl(val)
	return copysrc(writer, node, url, writer.copycache, writer.files_generated, writer.copydirurl)

def copysrc(writer, node, url, copycache, files_generated, copydirurl):
	if copycache.has_key(url):
		# already seen and copied
		nurl = MMurl.basejoin(copydirurl, MMurl.pathname2url(copycache[url]))
		if writer.rpExt and not writer.grinsExt:
			nurl = MMurl.unquote(nurl)
		return nurl
	import urlcache
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

def translatecolor(val, use_name = 1):
	if use_name and colors.rcolors.has_key(val):
		return colors.rcolors[val]
	else:
		return '#%02x%02x%02x' % val

def getfgcolor(writer, node):
	if node.GetChannelType() != 'brush':
		return None
	fgcolor = node.GetRawAttrDef('fgcolor', None)
	if fgcolor is None:
		return
	return translatecolor(fgcolor)

def getcolor(writer, node, attr, use_name = 1):
	color = node.GetRawAttrDef(attr, None)
	if color is None:
		return
	return translatecolor(color, use_name)

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

def getcmifattr(writer, node, attr, default = None):
	val = node.GetRawAttrDef(attr, default)
	if val is not None:
		if default is not None and val == default:
			return None
		val = str(val)
	return val

def getmimetype(writer, node):
	if node.GetType() not in mediatypes: # XXX or prefetch?
		return
	if writer.copydir:
		# MIME type may be changed by copying, so better not to return any
		return
	return node.GetRawAttrDef('mimetype', None)

def getdescr(writer, node, attr):
	return node.GetRawAttrDef(attr, None) or None

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

def getspeed(writer, node, attr = 'speed'):
	speed = node.GetRawAttrDef(attr, None)
	if speed is None:
		return None
	else:
		return fmtfloat(speed)

def getproportion(writer, node, attr):
	prop = node.GetRawAttrDef(attr, None)
	if prop is None:
		return None
	else:
		return fmtfloat(prop)

def getpercentage(writer, node, attr, default = None):
	prop = node.GetRawAttrDef(attr, None)
	if prop is None or prop == default:
		return None
	else:
		return fmtfloat(prop * 100, suffix = '%')

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

def escape_name(name, quote_initial = 1):
	name = '\\.'.join(name.split('.'))
	name = '\\-'.join(name.split('-'))
	if quote_initial and name in ['prev', 'wallclock', ]:
		name = '\\' + name
	return name

def wallclock2string(wallclock):
	# This code is used also in the EventEditor.
	yr,mt,dy,hr,mn,sc,tzsg,tzhr,tzmn = wallclock
	if yr is not None:
		date = '%04d-%02d-%02dT' % (yr, mt, dy)
	else:
		date = ''
	# time is optional if there is a date
	if date and hr == mn == sc == 0:
		time = ''
		date = date[:-1] # remove T at end
	elif sc == 0:
		# seconds are optional
		time = '%02d:%02d' % (hr, mn)
	elif int(sc) == sc:
		# fraction of seconds is optional
		time = '%02d:%02d:%02d' % (hr, mn, int(sc))
	else:
		time = '%02d:%02d:%05.2f' % (hr, mn, sc)
	if tzhr is not None:
		if tzsg == '+' and tzhr == tzmn == 0:
			# UTC/GMT can be abbreviated to just "Z"
			tz = 'Z'
		else:
			tz = '%s%02d:%02d' % (tzsg, tzhr, tzmn)
	else:
		tz = ''
	return 'wallclock(%s%s%s)' % (date, time, tz)


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

def getsysreq(writer, node, attr):
	sysreq = node.GetRawAttrDef('system_required', [])
	if sysreq:
		return ' + '.join(map(lambda i: 'ext%d' % i, range(len(sysreq))))
	return None

def getsyscomp(writer, node, attr):
	syscomp = node.GetRawAttrDef('system_component', [])
	if syscomp:
		return ' '.join(syscomp)
	return None

def getscreensize(writer, node):
	value = node.GetRawAttrDef('system_screen_size', None)
	if value is not None:
		return '%dX%d' % (value[1], value[0])

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
	layout = node.GetRawAttrDef('layout', 'undefined')
	if layout == 'undefined':
		return
	try:
		return writer.layout2name[layout]
	except KeyError:
		print '** Attempt to write unknown layout', layout
		return

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


def getautoreverse(writer, node):
	if not writer.smilboston:
		return
	if node.GetRawAttrDef('autoReverse', None):
		return 'true'
	return None

def getattributetype(writer, node):
	if not writer.smilboston:
		return
	atype = node.GetRawAttrDef('attributeType', 'XML')
	if atype == 'XML':
		return None
	return atype

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

def getorigin(writer, node):
	if not writer.smilboston:
		return
	origin = node.GetRawAttrDef('origin', 'parent')
	if origin == 'parent':
		return None
	return 'element'

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

def getinlinetrmode(writer, node):
	if not writer.smilboston:
		return
	mode = node.GetRawAttrDef('mode', 'in')
	if mode == 'in':
		return None
	return mode

def getallowedmimetypes(writer, node):
	mimetypes = node.GetRawAttrDef('allowedmimetypes', None)
	if not mimetypes:
		return None
	return ','.join(mimetypes)

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

#
# Mapping from SMIL attrs to functions to get them. Strings can be
# used as a shortcut for node.GetAttr
#
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
	("type", getmimetype, "mimetype"),
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

	("thumbnailIcon", lambda writer, node: geturl(writer, node, 'thumbnail_icon'), "thumbnail_icon"),
	("thumbnailScale", lambda writer, node: getboolean(writer, node, 'thumbnail_scale', 1), "thumbnail_scale"),
	("emptyIcon", lambda writer, node: geturl(writer, node, 'empty_icon'), "empty_icon"),
	("emptyText", lambda writer, node:getcmifattr(writer, node, "empty_text"), "empty_text"),
	("emptyColor", lambda writer, node: getcolor(writer, node, "empty_color"), "empty_color"),
	("emptyDur", lambda writer, node:getduration(writer, node, "empty_duration"), "empty_duration"),
	("nonEmptyIcon", lambda writer, node: geturl(writer, node, 'non_empty_icon'), "non_empty_icon"),
	("nonEmptyText", lambda writer, node:getcmifattr(writer, node, "non_empty_text"), "non_empty_text"),
	("nonEmptyColor", lambda writer, node: getcolor(writer, node, "non_empty_color"), "non_empty_color"),
	("dropIcon", lambda writer, node: geturl(writer, node, 'dropicon'), "dropicon"),
	("collapsed", getcollapsed, None),
	("showtime", getshowtime, None),
	("timezoom", gettimezoom, None),
	("allowedmimetypes", getallowedmimetypes, None),
	("project_autoroute", lambda writer, node:getboolean(writer, node, "project_autoroute", 1, 0), "project_autoroute"),
	("project_readonly", lambda writer, node:getboolean(writer, node, "project_readonly", 1, 0), "project_readonly"),
	("showAnimationPath", lambda writer, node:getboolean(writer, node, "showAnimationPath", 1, 1), "showAnimationPath"),
	("RTIPA-server", lambda writer, node:getcmifattr(writer, node, "RTIPA_server"), "RTIPA_server"),
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
	("thumbnailIcon", lambda writer, node: geturl(writer, node, 'thumbnail_icon'), "thumbnail_icon"),
	("thumbnailScale", lambda writer, node: getboolean(writer, node, 'thumbnail_scale', 1), "thumbnail_scale"),
	("emptyIcon", lambda writer, node: geturl(writer, node, 'empty_icon'), "empty_icon"),
	("emptyText", lambda writer, node:getcmifattr(writer, node, "empty_text"), "empty_text"),
	("emptyColor", lambda writer, node: getcolor(writer, node, "empty_color"), "empty_color"),
	("emptyDur", lambda writer, node:getduration(writer, node, "empty_duration"), "empty_duration"),
	("nonEmptyIcon", lambda writer, node: geturl(writer, node, 'non_empty_icon'), "non_empty_icon"),
	("nonEmptyText", lambda writer, node:getcmifattr(writer, node, "non_empty_text"), "non_empty_text"),
	("nonEmptyColor", lambda writer, node: getcolor(writer, node, "non_empty_color"), "non_empty_color"),
	("dropIcon", lambda writer, node: geturl(writer, node, 'dropicon'), "dropicon"),
	("collapsed", getcollapsed, None),
	("showtime", getshowtime, None),
	("timezoom", gettimezoom, None),
	("RTIPA-server", lambda writer, node:getcmifattr(writer, node, "RTIPA_server"), "RTIPA_server"),
	]
real_media_attrs = [
	("project_audiotype", lambda writer, node:getcmifattr(writer, node, "project_audiotype"), "project_audiotype"),
	("project_convert", lambda writer, node:getboolean(writer, node, "project_convert", 1, 1), "project_convert"),
	("project_ftp_dir", lambda writer, node:getcmifattr(writer, node, "project_ftp_dir"), "project_ftp_dir"),
	("project_ftp_dir_media", lambda writer, node:getcmifattr(writer, node, "project_ftp_dir_media"), "project_ftp_dir_media"),
	("project_ftp_host", lambda writer, node:getcmifattr(writer, node, "project_ftp_host"), "project_ftp_host"),
	("project_ftp_host_media", lambda writer, node:getcmifattr(writer, node, "project_ftp_host_media"), "project_ftp_host_media"),
	("project_ftp_user", lambda writer, node:getcmifattr(writer, node, "project_ftp_user"), "project_ftp_user"),
	("project_ftp_user_media", lambda writer, node:getcmifattr(writer, node, "project_ftp_user_media"), "project_ftp_user_media"),
	("project_html_page", lambda writer, node:getcmifattr(writer, node, "project_html_page"), "project_html_page"),
	("project_mobile", lambda writer, node:getboolean(writer, node, "project_mobile", 1, 0), "project_mobile"),
	("project_perfect", lambda writer, node:getboolean(writer, node, "project_perfect", 1, 1), "project_perfect"),
	("project_quality", lambda writer, node:getcmifattr(writer, node, "project_quality"), "project_quality"),
	("project_smil_url", lambda writer, node:getcmifattr(writer, node, "project_smil_url"), "project_smil_url"),
	("project_targets", lambda writer, node:getcmifattr(writer, node, "project_targets"), "project_targets"),
	("project_videotype", lambda writer, node:getcmifattr(writer, node, "project_videotype"), "project_videotype"),
	("backgroundOpacity", lambda writer, node: getpercentage(writer, node, 'backgroundOpacity', 1), "backgroundOpacity"),
	("chromaKey", lambda writer, node: getcolor(writer, node, "chromaKey"), "chromaKey"),
	("chromaKeyOpacity", lambda writer, node: getpercentage(writer, node, 'chromaKeyOpacity', 0), "chromaKeyOpacity"),
	("chromaKeyTolerance", lambda writer, node: getcolor(writer, node, "chromaKeyTolerance", 0), "chromaKeyTolerance"),
	("mediaOpacity", lambda writer, node: getpercentage(writer, node, 'mediaOpacity', 1), "mediaOpacity"),
]
qt_media_attrs = [
	('immediate-instantiation', lambda writer, node: getboolean(writer, node, 'immediateinstantiationmedia', 1), 'immediateinstantiationmedia'),
	('bitrate', lambda writer, node: getcmifattr(writer, node, 'bitratenecessary'), 'bitratenecessary'),
	('system-mime-type-supported', lambda writer, node: getcmifattr(writer, node, 'systemmimetypesupported'), 'systemmimetypesupported'),
	('attach-timebase', lambda writer, node: getboolean(writer, node, 'attachtimebase', 1, 1), 'attachtimebase'),
	('chapter', lambda writer, node: getcmifattr(writer, node, 'qtchapter'), 'qtchapter'),
	('composite-mode', lambda writer, node: getcmifattr(writer, node, 'qtcompositemode'), 'qtcompositemode'),
	]

# attributes that we know about and so don't write into the SMIL file using
# our namespace extension
cmif_chan_attrs_ignore = {
	'id':0, 'title':0, 'base_window':0, 'base_winoff':0, 'z':0, 'fit':0,
	'transparent':0, 'bgcolor':0, 'winpos':0, 'winsize':0, 'rect':0,
	'units':0,
	# new 03-07-2000
	# we can't save the chan type inside a region since a node may be associate to several nodes
	# the channel type is determinate according to the node type
	'type':0,
	# end new
	'showBackground':0,
	'traceImage':0,
	'soundLevel':0,
	'regAlign':0, 'regPoint':0, 'close':0, 'open':0, 'chsubtype':0,
	'left':0, 'top':0, 'width':0, 'height':0, 'right':0, 'bottom':0,
	'regionName':0,
	'resizeBehavior':0,
	}

qt_node_attrs = {
	'immediateinstantiationmedia':0,
	'bitratenecessary':0,
	'systemmimetypesupported':0,
	'attachtimebase':0,
	'qtchapter':0,
	'qtcompositemode':0,
	}
qt_context_attrs = {
	'qttimeslider':0,
	'qtchaptermode':0,
	'autoplay':0,
	'qtnext':0,
	'immediateinstantiation':0,
	}
# Mapping from CMIF channel types to smil media types
from smil_mediatype import smil_mediatype

def mediatype(x, error=0):
	chtype = x.GetChannelType()
	if not chtype:
		chtype = 'unknown'
	if chtype == 'video':
		url = x.GetAttrDef('file', None) or ''
		import urlcache
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

class BaseSMILWriter:
	def __init__(self, fp):
		self.fp = IndentedFile(fp)
		self.__isopen = 0
		self.__ignoring = 0	# whether we're ignoring a tag (see writetag())
		self.__stack = []

	def push(self):
		if self.__ignoring > 0:
			self.__ignoring = self.__ignoring + 1
			return
		if self.__isopen:
			self.fp.write('>\n')
			self.__isopen = 0
		self.fp.push()

	def pop(self):
		if self.__ignoring > 0:
			self.__ignoring = self.__ignoring - 1
			if self.__ignoring > 0:
				return
		fp = self.fp
		if self.__isopen:
			start, end = fp.write('/>\n')
			x = self.__stack[-1][1]
			if self.set_char_pos and x is not None:
				x.char_positions = x.char_positions[0], end
			self.__isopen = 0
			del self.__stack[-1]
		fp.pop()
		start, end = fp.write('</%s>\n' % self.__stack[-1][0])
		x = self.__stack[-1][1]
		if self.set_char_pos and x is not None:
			x.char_positions = x.char_positions[0], end
		del self.__stack[-1]

	def close(self):
		fp = self.fp
		if self.__isopen:
			start, end = fp.write('/>\n')
			x = self.__stack[-1][1]
			if self.set_char_pos and x is not None:
				x.char_positions = x.char_positions[0], end
			self.__isopen = 0
			del self.__stack[-1]
		while self.__stack:
			self.pop()
		fp.close()

	def writecomment(self, comment, x = None):
		write = self.fp.write
		if self.__isopen:
			start, end = write('/>\n')
			n = self.__stack[-1][1]
			if self.set_char_pos and n is not None:
				n.char_positions = n.char_positions[0], end
			self.__isopen = 0
			del self.__stack[-1]
		# -- not allowed in comment, so convert to - -
		comment = '- -'.join(comment.split('--'))
		start, end = write('<!--%s-->\n' % comment)
		if self.set_char_pos and x is not None:
			x.char_positions = start, end

	def writestring(self, str):
		self.fp.write(str)

	def writetag(self, tag, attrs = None, x = None):
		if self.__ignoring > 1:
			# ignoring ancestor, so ignore this as well
			return
		self.__ignoring = 0
		if attrs is None:
			attrs = []
		write = self.fp.write
		if self.__isopen:
			start, end = write('/>\n')
			n = self.__stack[-1][1]
			if self.set_char_pos and n is not None:
				n.char_positions = n.char_positions[0], end
			self.__isopen = 0
			del self.__stack[-1]
		# add xmlns if necessary or remove attr if no namespace allowed
		hasRP9prefix = (self.__stack or 0) and self.__stack[-1][4]
		if not hasRP9prefix and self.rpExt:
			for attr, val in attrs:
				if attr == xmlnsRP9:
					hasRP9prefix = 1
					break
				if attr[:len(NSRP9prefix)] == NSRP9prefix:
					attrs.insert(0, (xmlnsRP9, RP9ns))
					hasRP9prefix = 1
					break
		if not hasRP9prefix and tag[:len(NSRP9prefix)] == NSRP9prefix:
			# ignore this tag
			self.__ignoring = 1
			return
		hasQTprefix = (self.__stack or 0) and self.__stack[-1][3]
		if not hasQTprefix and self.qtExt:
			for attr, val in attrs:
				if attr == xmlnsQT:
					hasQTprefix = 1
					break
				if attr[:len(NSQTprefix)] == NSQTprefix:
					attrs.insert(0, (xmlnsQT, QTns))
					hasQTprefix = 1
					break
		if not hasQTprefix and tag[:len(NSQTprefix)] == NSQTprefix:
			# ignore this tag
			self.__ignoring = 1
			return
		hasGRiNSprefix = (self.__stack or 0) and self.__stack[-1][2]
		if not hasGRiNSprefix and self.grinsExt:
			for attr, val in attrs:
				if attr == xmlnsGRiNS:
					hasGRiNSprefix = 1
					break
				if attr[:len(NSGRiNSprefix)] == NSGRiNSprefix:
					attrs.insert(0, (xmlnsGRiNS, GRiNSns))
					hasGRiNSprefix = 1
					break
		if not hasGRiNSprefix and tag[:len(NSGRiNSprefix)] == NSGRiNSprefix:
			# ignore this tag
			self.__ignoring = 1
			return
		start, end = write('<' + tag)
		if self.set_char_pos and x is not None:
			x.char_positions = start, None
		for attr, val in attrs:
			if attr[:len(NSGRiNSprefix)] == NSGRiNSprefix and not hasGRiNSprefix:
				continue
			if attr[:len(NSRP9prefix)] == NSRP9prefix and not hasRP9prefix:
				continue
			if attr[:len(NSQTprefix)] == NSQTprefix and not hasQTprefix:
				continue
			write(' %s=%s' % (attr, nameencode(val)))
		self.__isopen = 1
		self.__stack.append((tag, x, hasGRiNSprefix, hasQTprefix, hasRP9prefix))

class SMILWriter(SMIL, BaseSMILWriter):
	def __init__(self, node, fp, filename, grinsExt = 1,
		     rpExt = features.EXPORT_REAL in features.feature_set,
		     qtExt = features.EXPORT_QT in features.feature_set,
		     copyFiles = 0, evallicense = 0, tmpcopy = 0, progress = None,
		     convertURLs = 0, convertfiles = 1, set_char_pos = 0, prune = 0,
		     smil_one = 0, weburl = None):
		self.messages = []

		# remember params
		self.set_char_pos = set_char_pos
		self.grinsExt = grinsExt
		self.qtExt = qtExt
		self.rpExt = rpExt
		self.evallicense = evallicense
		self.prune = prune
		self.progress = progress
		self.convert = convertfiles # we only convert if we have to copy
		self.root = node

		# some abbreviations
		self.context = ctx = node.GetContext()
		self.hyperlinks = ctx.hyperlinks

		if convertURLs:
			url = MMurl.canonURL(MMurl.pathname2url(filename))
			i = url.rfind('/')
			if i >= 0: url = url[:i+1]
			else: url = ''
			self.convertURLs = url
		else:
			self.convertURLs = None

		self.__generate_number = 0
		if filename == '<string>':
			self.__generate_basename = 'grinstmp'
		else:
			self.__generate_basename = os.path.splitext(os.path.basename(filename))[0]
		self.files_generated = {}
		self.webfiles_generated = {}
		self.bases_used = {}
		if copyFiles:
			dir, base = os.path.split(filename)
			base, ext = os.path.splitext(base)
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

		self.uses_grins_namespace = grinsExt
		self.uses_qt_namespace = self.qtExt and self.checkQTattrs()
		self.uses_rp_namespace = self.rpExt
		self.force_smil_1 = smil_one
		if smil_one:
			self.smilboston = 0
		else:
			self.smilboston = ctx.attributes.get('project_boston', 0)

		self.__title = ctx.gettitle()
		assets = ctx.getassets()

		self.ids_used = {}

		self.ugr2name = {}
		self.calcugrnames()

		self.layout2name = {}
		self.calclayoutnames()

		self.transition2name = {}
		self.calctransitionnames()

		self.ch2name = {}
		self.calcchnames1()

		self.uid2name = {}
		self.calcnames1(node)
		if assets:
			for anode in assets:
				self.calcnames1(anode)

		# second pass
		self.calcnames2(node)
		if assets:
			for anode in assets:
				self.calcnames2(anode)
		self.calcchnames2()

		self.syncidscheck(node)

		if fp is None:
			fp = open(filename, 'w')
		BaseSMILWriter.__init__(self, fp)

	def close(self):
		BaseSMILWriter.close(self)
		if self.messages:
			import windowinterface
			windowinterface.showmessage('\n'.join(self.messages))

	def warning(self, msg):
		self.messages.append(msg)

	def cancelwrite(self):
		raise cancel, 'user requested cancellation'

	def checkQTattrs(self):
		attributes = self.context.attributes
		for key in qt_context_attrs.keys():
			if attributes.has_key(key):
				return 1
		return 0

	def writeQTAttributeOnSmilElement(self, attrlist):
		attributes = self.context.attributes
		if attributes.has_key('qttimeslider'):
			val = attributes['qttimeslider']
			defvalue = MMAttrdefs.getdefattr(None, 'qttimeslider')
			if val != defvalue:
				attrlist.append(('%s:time-slider' % NSQTprefix, intToEnumString(val,{0:'false',1:'true'})))
		if attributes.has_key('qtchaptermode'):
			val = attributes['qtchaptermode']
			defvalue = MMAttrdefs.getdefattr(None, 'qtchaptermode')
			if val != defvalue:
				attrlist.append(('%s:chapter-mode' % NSQTprefix, intToEnumString(val,{0:'all',1:'clip'})))
		if attributes.has_key('autoplay'):
			val = attributes['autoplay']
			defvalue = MMAttrdefs.getdefattr(None, 'autoplay')
			if val != defvalue:
				attrlist.append(('%s:autoplay' % NSQTprefix, intToEnumString(val,{0:'false',1:'true'})))
		if attributes.has_key('qtnext'):
			attrlist.append(('%s:next' % NSQTprefix, attributes['qtnext']))
		if attributes.has_key('immediateinstantiation'):
			val = attributes['immediateinstantiation']
			defvalue = MMAttrdefs.getdefattr(None, 'immediateinstantiation')
			if val != defvalue:
				attrlist.append(('%s:immediate-instantiation' % NSQTprefix, intToEnumString(val,{0:'false',1:'true'})))

	def write(self):
		import version
		ctx = self.context

		# if the document is not valid, just write the raw source code
		# XXX this code should move to another location. I don't know where ?
		parseErrors = ctx.getParseErrors()
		if parseErrors != None:
			source = parseErrors.getSource()
			self.fp.write(source)
			self.fp.close()
			return

		self.writestring(SMILdecl) # MUST come first
		if self.evallicense:
			self.writecomment(EVALcomment)
		# write DOCTYPE only if no namespaces
		if not self.uses_grins_namespace and not self.uses_rp_namespace and not self.uses_qt_namespace:
			if self.smilboston:
				self.writestring(doctype2)
			else:
				self.writestring(doctype)
		if ctx.comment:
			self.writecomment(ctx.comment)
		attrlist = []
		if self.smilboston:
			attrlist.append(('xmlns', SMIL2ns[0]))
		if self.uses_grins_namespace:
			attrlist.append((xmlnsGRiNS, GRiNSns))
		if self.uses_rp_namespace and self.smilboston:
			attrlist.append((xmlnsRP9, RP9ns))
		if self.uses_qt_namespace:
			attrlist.append((xmlnsQT, QTns))
		if self.smilboston:
			# test attributes are not allowed on the body element,
			# but they are allowed on the smil element, so that's
			# where they get moved
			sysreq = self.root.GetRawAttrDef('system_required', [])
			if sysreq:
				for i in range(len(sysreq)):
					attrlist.append(('xmlns:ext%d' % i, sysreq[i]))
			for name, func, keyToCheck in smil_attrs:
				if keyToCheck is None or self.root.attrdict.has_key(keyToCheck):
					if name[:6] != 'system':
						continue
					value = func(self, self.root)
					if value is None:
						continue
					attrlist.append((name, value))
		if self.uses_qt_namespace:
			self.writeQTAttributeOnSmilElement(attrlist)
		self.writetag('smil', attrlist)
		self.push()
		self.writetag('head')
		self.push()
		if self.smilboston:
			self.writeusergroups()
			if ctx.metadata:
				self.writetag('metadata', [])
				self.push()
				self.writestring(ctx.metadata)
				self.pop()

		if self.__title:
			self.writetag('meta', [('name', 'title'),
					       ('content', self.__title)])
		if not self.convertURLs and ctx.baseurl:
			self.writetag('meta', [('name', 'base'),
					       ('content', ctx.baseurl)])
		self.writetag('meta', [('name', 'generator'),
				       ('content','GRiNS %s'%version.version)])
		if ctx.color_list and self.grinsExt:
			colors = []
			last = 0
			for color in ctx.color_list:
				if color is None:
					colors.append('')
				else:
					colors.append(translatecolor(color))
					last = len(colors)
			self.writetag('meta', [('name', 'customColors'),
					       ('content',','.join(colors[:last]))])
		for key, val in ctx.attributes.items():
			# for export don't write attributes starting with project_, they are meant
			# for internal information-keeping only
			if not self.grinsExt and key[:8] == 'project_':
				continue
			if qt_context_attrs.has_key(key):
				continue
			if key == 'project_boston':
				# never save project_boston
				continue
			self.writetag('meta', [('name', key),
					       ('content', val)])
		if self.grinsExt and ctx.externalanchors:
			links = []
			for link in ctx.externalanchors:
				links.append('%20'.join(link.split(' ')))
			self.writetag('meta', [('name', 'project_links'), ('content', ' '.join(links))])
		self.writelayout()
		if self.smilboston:
			self.writetransitions()
		self.writegrinslayout()
		self.writeviewinfo()
		self.pop()

		self.writenode(self.root, root = 1)

		self.close()

	def writebare(self):
		self.writenode(self.root, root = 1)
		self.close()

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

	def calclayoutnames(self):
		# Calculate unique names for layouts
		layouts = self.context.layouts
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

	def calcnames1(self, node):
		# Calculate unique names for nodes; first pass
		if self.prune and not node.WillPlay():
			# skip unplayable nodes when pruning
			return
		uid = node.GetUID()
		name = node.GetRawAttrDef('name', '')
		if name:
			name = identify(name)
			if not self.ids_used.has_key(name):
				self.ids_used[name] = 1
				self.uid2name[uid] = name
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
		for child in node.children:
			self.calcnames2(child)

	def calcchnames1(self):
		# Calculate unique names for channels; first pass
		channels = self.context.channels
		for ch in channels:
			name = identify(ch.name)
			if not self.ids_used.has_key(name):
				self.ids_used[name] = 0
				self.ch2name[ch] = name
			if ch.GetParent() is None and \
			   ChannelMap.isvisiblechannel(ch['type']):
				# top-level channel with window
				if not self.__title:
					self.__title = ch.name
			# also check if we need to use the CMIF extension
			if not self.uses_grins_namespace and \
			   not smil_mediatype.has_key(ch['type']) and \
			   ch['type'] != 'layout':
				self.uses_namespaces = 1
		if not self.__title and channels:
			# no channels with windows, so take very first channel
			self.__title = channels[0].name

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
				name = identify(ch.name)
				i = 0
				nn = '%s-%d' % (name, i)
				while self.ids_used.has_key(nn):
					i = i+1
					nn = '%s-%d' % (name, i)
				name = nn
				self.ids_used[name] = 0
				self.ch2name[ch] = name
			# check for SMIL 2.0 feature: hierarchical regions
			if not self.smilboston and \
			   ch.GetParent() is not None:
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

	def __writeRegPoint(self):
		for name, regpoint in self.context.regpoints.items():
			if regpoint.isdefault():
				continue

			attrlist = []
			attrlist.append(('id', name))

			for attr, val in regpoint.items():
				# for instance, we assume that a integer type value is a pixel value,
				# and a float type value is a relative value (%)
				if attr == 'top' or attr == 'bottom' or attr == 'left' or attr == 'right':
					if type(val) == type(0):
						attrlist.append((attr, '%d' % val))
					else:
						attrlist.append((attr, '%d%%' % int(val * 100 + .5)))
				else:
					attrlist.append((attr, val))

			self.writetag('regPoint', attrlist)

	def writelayout(self):
		# Write the layout section
		attrlist = []
		self.writetag('layout', attrlist)
		self.push()
		if self.smilboston:
			self.__writeRegPoint()
		viewports = self.context.getviewports()
		useRootLayout = len(viewports) == 1
		for ch in viewports:
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
			elif self.smilboston:
				bgcolor = 0,0,0
			else:
				bgcolor = 255,255,255
			bgcolor = translatecolor(bgcolor)
			if self.smilboston:
				attrlist.append(('backgroundColor', bgcolor))
			else:
				attrlist.append(('background-color', bgcolor))

			if self.smilboston:
				# write only non default value
				if ch.has_key('open'):
					val = ch['open']
					if val != 'onStart':
						attrlist.append(('open', val))
						useRootLayout = 0
				if ch.has_key('close'):
					val = ch['close']
					if val != 'onRequest':
						attrlist.append(('close', val))
						useRootLayout = 0

			for name in ['width', 'height']:
				value = ch.GetAttrDef(name, None)
				if type(value) == type(0.0):
					attrlist.append((name, '%d%%' % int(value * 100 + .5)))
				elif type(value) == type(0):
					attrlist.append((name, '%d' % value))

			# special case: collapse information
			if ch.collapsed == 1:
				attrlist.append(('%s:collapsed' % NSGRiNSprefix, 'true'))
			elif ch.collapsed == 0:
				attrlist.append(('%s:collapsed' % NSGRiNSprefix, 'false'))
			else:
				# default behavior. depend of the node
				pass

			# trace image
			traceImage = ch.get('traceImage')
			if traceImage != None:
				attrlist.append(('%s:traceImage' % NSGRiNSprefix, traceImage))

			if self.smilboston:
				for key, val in ch.items():
					if not cmif_chan_attrs_ignore.has_key(key):
						attrlist.append(('%s:%s' % (NSGRiNSprefix, key), MMAttrdefs.valuerepr(key, val)))
				resizeBehavior = ch.get('resizeBehavior', 'zoom')
				if resizeBehavior != 'zoom':
					attrlist.append(('%s:resizeBehavior' % NSRP9prefix, resizeBehavior))
				if useRootLayout:
					self.writetag('root-layout', attrlist, ch)
					self.writeregion(ch)
				else:
					self.writetag('topLayout', attrlist, ch)
					self.push()
					self.writeregion(ch)
					self.pop()
			else:
				# not smilboston implies one top-level
				self.writetag('root-layout', attrlist, ch)
				self.writeregion(ch)

		self.pop()

	def writeregion(self, ch):
		if ch['type'] == 'layout' and \
		   ch.GetParent() is None:
			# top-level layout channel has been handled
			for sch in ch.GetChildren():
				self.writeregion(sch)
			return

		# don't write the default region
		if ch.isDefault() and not self.context.hasDefaultRegion(self.root):
			return

		attrlist = [('id', self.ch2name[ch])]
		if ch.has_key('regionName'):
			attrlist.append(('regionName', ch['regionName']))
		title = ch.get('title')
		if title:
			attrlist.append(('title', title))
		elif self.ch2name[ch] != ch.name:
			attrlist.append(('title', ch.name))

		for name in ['left', 'width', 'right', 'top', 'height', 'bottom']:
			value = ch.GetAttrDef(name, None)
			# write only no auto values
			if value != None:
				if type(value) is type(0.0):
					value = fmtfloat(value*100, '%', prec=2)
				elif type(value) is type(0):
					value = '%d' % value
				attrlist.append((name, value))
		if ChannelMap.isvisiblechannel(ch['type']):
			z = ch.get('z', 0)
			if z > 0:
				attrlist.append(('z-index', "%d" % z))
			fit = ch.GetAttrDef('fit','hidden')
			if fit not in ('meet','slice','hidden','fill','scroll'):
				fit = None
				print '** Channel uses unsupported fit value', name
			if fit is not None and fit != 'hidden':
				attrlist.append(('fit', fit))

		#
		# Background color for SMIL before version 2:
		#

			# SMIL says: either background-color
			# or transparent; if different, set
			# GRiNS attributes
		# We have the following possibilities:
		#		no bgcolor	bgcolor set
		#transp -1	no attr		b-g="bg"
		#transp  0	GR:tr="0"	GR:tr="0" b-g="bg"
		#transp  1	b-g="trans"	b-g="trans" (ignore bg)

			if not self.smilboston:
				transparent = ch.get('transparent', 0)
				bgcolor = ch.get('bgcolor')
				if not transparent and bgcolor is not None:
					bgcolor = translatecolor(bgcolor)
					attrlist.append(('background-color', bgcolor))

		#
		# Background color for SMIL version 2:
		#
			# no transparent or bgcolor attribute : inherit value
			# transparent != 0 : transparent (default value)
			# otherwise : bgcolor
			else:
				transparent = ch.get('transparent')
				bgcolor = ch.get('bgcolor')
				if transparent is None:
					bgcolor = 'inherit'
				elif transparent:
					# default value
					bgcolor = None
				elif bgcolor is not None:
					bgcolor = translatecolor(bgcolor)

				if bgcolor is not None:
					attrlist.append(('backgroundColor', bgcolor))

			# we save the showBackground attribute only if it's not the default value
			showBackground = ch.get('showBackground', 'always')
			if showBackground != 'always':
				attrlist.append(('showBackground', showBackground))

			if self.smilboston:
				soundLevel = ch.get('soundLevel')
				# we only save the soundLevel attribute if it exists and different from default value
				if soundLevel != None and soundLevel != 1.0:
					attrlist.append(('soundLevel', fmtfloat(soundLevel * 100, '%', prec = 1)))

				regPoint = ch.get('regPoint')
				if regPoint != None:
					attrlist.append(('regPoint',regPoint))

				regAlign = ch.get('regAlign')
				if regAlign != None and regAlign != 'topLeft':
					attrlist.append(('regAlign',regAlign))

		# for layout channel the chsubtype attribute is translated to grins:type attribute
		subtype = ch.get('chsubtype')
		if subtype != None:
			attrlist.append(('%s:type' % NSGRiNSprefix, subtype))

		# special case: collapse information
		if ch.collapsed == 1:
			attrlist.append(('%s:collapsed' % NSGRiNSprefix, 'true'))
		elif ch.collapsed == 0:
			attrlist.append(('%s:collapsed' % NSGRiNSprefix, 'false'))
		else:
			# default behavior. depend of the node
			pass

		for key, val in ch.items():
			if not cmif_chan_attrs_ignore.has_key(key):
				attrlist.append(('%s:%s' % (NSGRiNSprefix, key), MMAttrdefs.valuerepr(key, val)))
		opacity = ch.get('opacity')
		if opacity is not None and 0 <= opacity < 1: # default is 100%
			attrlist.append(('%s:opacity' % NSRP9prefix, fmtfloat(opacity * 100, '%', prec = 0)))
		self.writetag('region', attrlist, ch)
		subchans = ch.GetChildren()

		# new 03-07-2000
		# cnt sub layoutchannel number --> to allow to close the tag if no element inside
		lcNumber = 0
		if subchans:
			for sch in subchans:
				if sch['type'] == 'layout':
					lcNumber = lcNumber + 1
		# end new

		if lcNumber > 0:
			self.push()
			for sch in subchans:
				# new 03-07-2000
				# save only the layout channels
				if sch['type'] == 'layout':
				# end new
					self.writeregion(sch)
			self.pop()

	def writeusergroups(self):
		u_groups = self.context.usergroups
		if not u_groups:
			return
		self.writetag('customAttributes')
		self.push()
		for key, val in u_groups.items():
			attrlist = []
			attrlist.append(('id', self.ugr2name[key]))
			title, u_state, override, uid = val
			if title:
				attrlist.append(('title', title))
			if u_state == 'RENDERED':
				attrlist.append(('defaultState', 'true'))
			if override == 'visible':
				attrlist.append(('override', 'visible'))
			if uid:
				attrlist.append(('uid', uid))
			self.writetag('customTest', attrlist)
		self.pop()

	def writetransitions(self):
		transitions = self.context.transitions
		if not transitions:
			return
		defaults = {
			'dur':'1',
			'startProgress':'0',
			'endProgress':'1',
			'fadeColor':'black',
			'direction':'forward',
			'vertRepeat':'1',
			'horzRepeat':'1',
			'borderWidth':'0',
			'borderColor':'black',
			'coordinated':'false',
			'clipBoundary':'children',
			}
		for key, val in transitions.items():
			attrlist = []
			attrlist.append(('id', self.transition2name[key]))
			for akey, aval in val.items():
				if akey == 'borderColor' and aval == (-1,-1,-1):
					aval = 'blend'
				elif akey in ('fadeColor', 'borderColor'):
					aval = translatecolor(aval)
				elif akey[:1] == '_':
					continue
				elif akey == 'coordinated':
					aval = ['false', 'true'][aval]
				elif akey != 'subtype':
					aval = MMAttrdefs.valuerepr(akey, aval)
					if akey == 'trtype':
						akey = 'type'
				if defaults.has_key(akey) and defaults[akey] == aval:
					continue
				attrlist.append((akey, aval))
			self.writetag('transition', attrlist)

	def writegrinslayout(self):
		if not self.grinsExt:
			return
		layouts = self.context.layouts
		if not layouts:
			return
		self.writetag('%s:layouts' % NSGRiNSprefix)
		self.push()
		for name, chans in layouts.items():
			channames = []
			for ch in chans:
				channames.append(self.ch2name[ch])
			self.writetag('%s:layout' % NSGRiNSprefix,
				      [('id', self.layout2name[name]),
				       ('regions', ' '.join(channames))])
		self.pop()

	def writeviewinfo(self):
		if not self.grinsExt:
			return
		viewinfo = self.context.getviewinfo()
		if not viewinfo:
			return
		for view, geometry in viewinfo:
			l, t, w, h = geometry
			self.writetag('%s:viewinfo' % NSGRiNSprefix, [
				('view', view),
				('top', `t`),
				('left', `l`),
				('width', `w`),
				('height', `h`)])

	def writenode(self, x, root = 0):
		# Write a node (possibly recursively)
		if self.prune and not x.WillPlay():
			# skip unplayable nodes when pruning
			return
		type = x.GetType()
		if not self.smilboston:
			if type in ('animate','animpar','prefetch','brush','excl','prio'):
				self.warning('Lost %s object' % type)
				return
		# XXX I don't like this special casing here --sjoerd
		if type=='animate':
			if root:
				self.writetag('body', [('%s:hidden' % NSGRiNSprefix, 'true')])
				self.push()
			self.writeanimatenode(x)
			return
		elif type == 'animpar':
			self.writeanimpar(x)
			return
		elif type=='prefetch':
			if root:
				self.writetag('body', [('%s:hidden' % NSGRiNSprefix, 'true')])
				self.push()
			self.writeprefetchnode(x)
			return
		elif type == 'anchor':
			self.writeanchor(x)
			return
		elif type == 'comment':
			self.writecomment('\n'.join(x.values), x)
			return
		
		attrlist = []

		interior = (type in interiortypes)
		if interior:
			if type == 'prio':
				xtype = mtype = 'priorityClass'
			elif type == 'seq' and root and self.smilboston:
				xtype = mtype = 'body'
			elif type == 'foreign':
				ns = x.GetRawAttrDef('namespace', '')
				tag = x.GetRawAttrDef('elemname', None)
				if ns:
					xtype = mtype = 'foreign:%s' % tag
					attrlist.append(('xmlns:foreign', ns))
				else:
					xtype = mtype = tag
			elif self.prune and type == 'switch':
				# special case: only at most one of the children will actually get written
				for c in x.GetChildren():
					self.writenode(c)
				return
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
					ans, attr = attr.split(' ', 1)
					if not extensions.has_key(ans):
						extensions[ans] = 'x%s' % len(extensions)
						attrlist.append(('xmlns:%s' % extensions[ans], ans))
					attr = '%s:%s' % (extensions[ans], attr)
				attrlist.append((attr, val))
		else:
			attrs = smil_attrs
			if xtype != 'body':
				# special case for systemRequired
				sysreq = x.GetRawAttrDef('system_required', [])
				for i in range(len(sysreq)):
					attrlist.append(('xmlns:ext%d' % i, sysreq[i]))

		for name, func, keyToCheck in attrs:
			if keyToCheck is not None and not x.attrdict.has_key(keyToCheck):
				continue
			value = func(self, x)
			# gname is the attribute name as recorded in attributes
			# name is the attribute name as recorded in SMIL file
			if value is None:
				continue
			gname = '%s %s' % (GRiNSns, name)
			if attributes.has_key(gname):
				name = '%s:%s' % (NSGRiNSprefix, name)
			else:
				gname = name

			# only write attributes that have a value and are
			# legal for the type of node
			# other attributes are caught below
			if (attributes.has_key(gname) or name[:6] == 'xmlns:'):
				attrlist.append((name, value))
		is_realpix = type == 'ext' and x.GetChannelType() == 'RealPix'
		if not interior and root:
			self.writetag('body', [('%s:hidden' % NSGRiNSprefix, 'true')])
			self.push()
		if interior:
			if type == 'seq' and self.copydir and not self.smilboston \
						and not x.GetChildren():
				# Warn the user for a bug in G2
				self.warning('Warning: some G2 versions crash on empty sequence nodes')
				x.set_infoicon('error', 'Warning: some G2 versions crash on empty sequence nodes')
			if root:
				if type != 'seq' or (not self.smilboston and attrlist):
					self.writetag('body', [('%s:hidden' % NSGRiNSprefix, 'true')])
					self.push()
				else:
					mtype = 'body'
			self.writetag(mtype, attrlist, x)
			if type != 'foreign' or root or x.GetChildren():
				self.push()
				for child in x.GetChildren():
					self.writenode(child)
				if root and self.grinsExt:
					assets = x.context.getassets()
					if assets:
						if type != 'seq' or (not self.smilboston and attrlist):
							self.pop()
						self.writetag(NSGRiNSprefix + ':assets', [('skip-content', 'true')])
						self.push()
						for child in assets:
							self.writenode(child)
						self.pop()
				self.pop()
		elif is_realpix and self.copydir:
			# If we are exporting handle RealPix specially: we might want
			# to convert it into a <par> containing a realpix node and a
			# realtext caption node
			self.writerealpixnode(x, attrlist, mtype)
		elif type in ('imm', 'ext', 'brush'):
			self.writemedianode(x, attrlist, mtype)
		else:
			raise CheckError, 'bad node type in writenode'

	def writerealpixnode(self, x, attrlist, mtype):
		# Special case for realpix, so we get a chance to write the RealText captions
		# if needed
		rturl, channel = self.getrealtextcaptions(x)
		if not rturl:
			self.writemedianode(x, attrlist, mtype)
			return
		region = self.ch2name[channel]
		parentattrlist = []
		for attr, val in attrlist:
			if attr in ('id', 'begin'):
				parentattrlist.append((attr, val))
		for item in parentattrlist:
			attrlist.remove(item)
		self.writetag('par', parentattrlist, x)
		self.push()
		self.writemedianode(x, attrlist, mtype)
		self.writetag('textstream', [('src', rturl), ('region', region)])
		self.pop()

	def getrealtextcaptions(self, node):
		# Return None or, only for RealPix nodes with captions, the source
		# for the realtext caption file and the channel to play it on
		ntype = node.GetType()
		chtype = node.GetChannelType()
		if ntype != 'ext' or chtype != 'RealPix':
			return None, None
		rtchannel = node.GetChannel(attrname='captionchannel')
		if not rtchannel or rtchannel == 'undefined':
			return None, None
		file = self.gen_rtfile()
		self.files_generated[file] = ''
		import realsupport
		realsupport.writeRT(os.path.join(self.copydir, file), node.slideshow.rp, node)
		val = MMurl.basejoin(self.copydirurl, MMurl.pathname2url(file))
		return val, rtchannel

	def writeQTAttributeOnMediaElement(self, node, attrlist):
		dict = node.GetAttrDict()
		for smilattr, func, grinsattr in qt_media_attrs:
			if not dict.has_key(grinsattr):
				continue
			val = func(self, node)
			if val is None:
				continue
			attrlist.append(('%s:%s' % (NSQTprefix, smilattr), val))

	def writeRPAttributeOnMediaElement(self, node, attrlist):
		dict = node.GetAttrDict()
		for smilattr, func, grinsattr in real_media_attrs:
			if not dict.has_key(grinsattr):
				continue
			val = func(self, node)
			if val is None:
				continue
			if smilattr[:8] == 'project_':
				attrlist.append(('%s:%s' % (NSGRiNSprefix, smilattr), val))
			else:
				attrlist.append(('%s:%s' % (NSRP9prefix, smilattr), val))

	def writemedianode(self, x, attrlist, mtype):
		# XXXX Not correct for imm
		pushed = 0

		if self.uses_qt_namespace:
			self.writeQTAttributeOnMediaElement(x,attrlist)

		if self.uses_rp_namespace:
			self.writeRPAttributeOnMediaElement(x,attrlist)

		self.writetag(mtype, attrlist, x)
		fg = x.GetRawAttrDef('fgcolor', None)
		if fg is not None and mtype == 'text':
			if not pushed:
				self.push()
				pushed = 1
			self.writetag('param', [('name','fgcolor'),('value',translatecolor(fg))])
		if self.uses_rp_namespace:
			bitrate = x.GetRawAttrDef('strbitrate', None)
			if bitrate is not None:
				if not pushed:
					self.push()
					pushed = 1
				self.writetag('param', [('name', 'bitrate'), ('value', `bitrate`)])
			reliable = x.GetRawAttrDef('reliable', None)
			if reliable is not None:
				if not pushed:
					self.push()
					pushed = 1
				self.writetag('param', [('name', 'reliable'), ('value', ['false', 'true'][reliable])])
		for child in x.GetChildren():
			if not pushed:
				self.push()
				pushed = 1
			self.writenode(child)
		if pushed:
			self.pop()

	def writeanimpar(self, node):
		animvals = node.attrdict.get('animvals', [])

		times = []
		posValues = []
		widthValues = []
		heightValues = []
		bgcolorValues = []

		for t, v in animvals:
			t = fmtfloat(t, prec = 4)
			times.append(t)
			for attr in v.keys():
				val = v[attr]
				if attr == 'left' and v.has_key('top'):
					val = val, v['top']
					if self.rpExt and not self.grinsExt:
						posValues.append('%d %d' % val)	# RealONE doesn't do parens (yet?)
					else:
						posValues.append('(%d %d)' % val)
				elif attr == 'width':
					widthValues.append('%d' % val)
				elif attr == 'height':
					heightValues.append('%d' % val)
				elif attr == 'bgcolor':
					import colors
					if colors.rcolors.has_key(val):
						bgcolorValues.append(colors.rcolors[val])
					else:
						bgcolorValues.append('#%02x%02x%02x' % val)

		timeLen = len(times)		
		posLen = len(posValues)
		widthLen = len(widthValues)
		heightLen = len(heightValues)
		bgcolorLen = len(bgcolorValues)

		if self.grinsExt:
			if posLen > 0 and posLen == timeLen:
				self.__writeanimparitem1('pos', posValues, times, node)
			if widthLen > 0 and widthLen == timeLen:
				self.__writeanimparitem1('width', widthValues, times, node)
			if heightLen > 0 and heightLen == timeLen:
				self.__writeanimparitem1('height', heightValues, times, node)
			if bgcolorLen > 0 and bgcolorLen == timeLen:
				self.__writeanimparitem1('bgcolor', bgcolorValues, times, node)
		else:
			if posLen > 0 and posLen == timeLen:
				self.__writeanimparitem2('pos', posValues, times, node)
			if widthLen > 0 and widthLen == timeLen:
				self.__writeanimparitem2('width', widthValues, times, node)
			if heightLen > 0 and heightLen == timeLen:
				self.__writeanimparitem2('height', heightValues, times, node)
			if bgcolorLen > 0 and bgcolorLen == timeLen:
				self.__writeanimparitem2('bgcolor', bgcolorValues, times, node)

	# use key times		
	def __writeanimparitem1(self, aname, values, times, node):
		attrlist = []
		if aname == 'pos':
			tag = 'animateMotion'
		elif aname == 'bgcolor':
			tag = 'animateColor'
			attrlist.append(('attributeName', 'backgroundColor'))
		else:
			tag = 'animate'
			attrlist.append(('attributeName', aname))

		attrlist.append(('values', ';'.join(values)))
		attrlist.append(('keyTimes', ';'.join(times)))
		attrlist.append(('fill', 'freeze'))

		# for now, the target node can only be the parent node
		targetNode = node.GetParent()
		
		attrlist.append(('%s:editGroup' % NSGRiNSprefix, targetNode.GetUID()))

		# duration
		duration = targetNode.GetDuration()
		if duration is not None and duration >= 0:
			dur = fmtfloat(duration, 's')
			attrlist.append(('dur', dur))
			
		self.writetag(tag, attrlist)

	# don't use key times
	def __writeanimparitem2(self, aname, values, times, node):
		ind = 0
		for ind in range(len(times)):
			attrlist = []
			if ind == len(times)-1:
				break
			if aname == 'pos':
				tag = 'animateMotion'
			elif aname == 'bgcolor':
				tag = 'animateColor'
				attrlist.append(('attributeName', 'backgroundColor'))
			else:
				tag = 'animate'
				attrlist.append(('attributeName', aname))

			v1 = values[ind]
			v2 = values[ind+1]
			
			if v1 != v2:
				attrlist.append(('from', v1))
				attrlist.append(('to', v2))
				attrlist.append(('fill', 'freeze'))
			
				# duration
				# for now, the target node can only be the parent node
				targetNode = node.GetParent()
				duration = targetNode.GetDuration()
				if duration is not None and duration >= 0:
					dur = (float(times[ind+1])-float(times[ind]))*duration
					dur = fmtfloat(dur, 's')
					attrlist.append(('dur', dur))
				
					begin = float(times[ind])*duration
					if begin > 0:
						begin = fmtfloat(begin, 's')
						attrlist.append(('begin', begin))
					
				self.writetag(tag, attrlist)

	def writeanimatenode(self, node):
		if node.attrdict.get('internal'):
			return
		attrlist = []
		tag = node.GetAttrDict().get('atag')
		attributes = self._attributes.get(tag, {})
		for name, func, keyToCheck in smil_attrs:
			if attributes.has_key(name):
				if name == 'type':
					value = node.GetRawAttrDef('trtype', None)
				elif keyToCheck is None or node.attrdict.has_key(keyToCheck):
					value = func(self, node)
				else:
					value = None
				if value is not None:
					if self.rpExt and not self.grinsExt and tag == 'animateMotion' and name in ('from','to','by','values'):
						# remove parentheses for RealONE
						value = ''.join(value.split('('))
						value = ''.join(value.split(')'))
					attrlist.append((name, value))
		self.writetag(tag, attrlist, node)

	def writeprefetchnode(self, node):
		attrlist = []
		attributes = self._attributes.get('prefetch', {})
		for name, func, keyToCheck in smil_attrs:
			if attributes.has_key(name) and (keyToCheck is None or node.attrdict.has_key(keyToCheck)):
				value = func(self, node)
				if value is not None:
					attrlist.append((name, value))
		self.writetag('prefetch', attrlist, node)

	def writeanchor(self, anchor):
		attrlist = []
		id = getid(self, anchor)
		if id is not None:
			attrlist.append(('id', id))

		links = self.hyperlinks.findsrclinks(anchor)
		if links:
			if len(links) > 1:
				print '** Multiple links on anchor', \
				      x.GetRawAttrDef('name', '<unnamed>'), \
				      x.GetUID()
			a1, a2, dir = links[0]
			if type(a2) is type(''):
				href = self.fixurl(a2)
				import urlparse
				utype, host, path, params, query, fragment = urlparse.urlparse(a2)
				if (not utype or utype == 'file') and (not host or host == 'localhost') and self.copydir:
					# link to local file
					href = copysrc(self, a1, self.context.findurl(a2), self.webcopycache, self.webfiles_generated, self.webcopydirurl)
			else:
				href = '#' + self.uid2name[a2.GetUID()]
			attrlist.append(('href', href))
		elif self.smilboston and (self.grinsExt or not self.rpExt):
			# RealONE doesn't deal with nohref
			attrlist.append(('nohref', 'nohref'))

		show = MMAttrdefs.getattr(anchor, 'show')
		if show != 'replace':
			attrlist.append(('show', show))
		sstate = MMAttrdefs.getattr(anchor, 'sourcePlaystate')
		if sstate != 'play':
			# if show == 'replace' or show == 'pause', sourcePlaystate is ignored
			# if show == 'new', sourcePlaystate == 'play' is default
			# so we write sourcePlaystate if it isn't 'play'
			if self.smilboston:
				attrlist.append(('sourcePlaystate', sstate))
		dstate = MMAttrdefs.getattr(anchor, 'destinationPlaystate')
		if dstate != 'play' and self.smilboston:
			attrlist.append(('destinationPlaystate', dstate))
		fragment = MMAttrdefs.getattr(anchor, 'fragment')
		if fragment and self.smilboston:
			attrlist.append(('fragment', fragment))

		target = MMAttrdefs.getattr(anchor, 'target')
		if target and self.smilboston:
			attrlist.append(('target', target))

		shape = MMAttrdefs.getattr(anchor, 'ashape')
		if shape != 'rect' and self.smilboston:
			attrlist.append(('shape', shape))
		coords = []
		for c in MMAttrdefs.getattr(anchor, 'acoords'):
			if type(c) is type(0):
				# pixel coordinates
				coords.append('%d' % c)
			else:
				# relative coordinates
				coords.append(fmtfloat(c*100, '%', prec = 2))
		if coords and (self.smilboston or shape == 'rect'):
			attrlist.append(('coords', ','.join(coords)))

		begin = getsyncarc(self, anchor, 0)
		if begin is not None:
			attrlist.append(('begin', begin))
		end = getsyncarc(self, anchor, 1)
		if end is not None:
			attrlist.append(('end', end))

		actuate = MMAttrdefs.getattr(anchor, 'actuate')
		if actuate != 'onRequest' and self.smilboston:
			attrlist.append(('actuate', actuate))

		accesskey = anchor.GetAttrDef('accesskey', None)
		if accesskey is not None and self.smilboston:
			attrlist.append(('accesskey', accesskey))

		external = anchor.GetAttrDef('external', 0)
		if external and self.smilboston:
			attrlist.append(('external', 'true'))

		tabindex = anchor.GetAttrDef('tabindex', None)
		if tabindex is not None and self.smilboston:
			attrlist.append(('tabindex', '%d' % tabindex))

		for attr in ('sourceLevel', 'destinationLevel'):
			val = anchor.GetAttrDef(attr, 1.0)
			if 0 <= val and val != 1 and self.smilboston:
				attrlist.append((attr, fmtfloat(100*val, '%', prec = 1)))

		if self.smilboston:
			sendTo = anchor.GetAttrDef('sendTo', None)
			if sendTo is not None:
				if sendTo in ('rpcontextwin', 'rpbrowser'):
					sendTo = '_' + sendTo
				attrlist.append(('%s:sendTo' % NSRP9prefix, sendTo))
			self.writetag('area', attrlist, anchor)
		else:
			self.writetag('anchor', attrlist, anchor)

	def fixurl(self, url):
		ctx = self.context
		if self.convertURLs:
			url = MMurl.canonURL(ctx.findurl(url))
			if url[:len(self.convertURLs)] == self.convertURLs:
				url = url[len(self.convertURLs):]
		return url

	def newfile(self, srcurl, files_generated):
		import posixpath, urlparse
		utype, host, path, params, query, fragment = urlparse.urlparse(srcurl)
		if utype == 'data':
			import urlcache
			mtype = urlcache.mimetype(srcurl)
			if mtype is None:
				mtype = 'text/plain'
			ext = MMmimetypes.guess_extension(mtype)
			base = 'data'
		else:
			file = MMurl.url2pathname(posixpath.basename(path))
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
				convert = node.GetRawAttrDef('project_convert', 1)
		else:
			convert = 0

		if convert and u.headers.maintype == 'audio' and \
		   u.headers.subtype.find('real') < 0:
			from realconvert import convertaudiofile
			# XXXX This is a hack. convertaudiofile may change the filename (and
			# will, currently, to '.ra').
			if self.progress:
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
			if node:
				node.set_infoicon('error', msg)
			import windowinterface
			windowinterface.showmessage(msg)
			u = MMurl.urlopen(srcurl)
		if convert and u.headers.maintype == 'video' and \
		   u.headers.subtype.find('real') < 0:
			from realconvert import convertvideofile
			# XXXX This is a hack. convertvideofile may change the filename (and
			# will, currently, to '.rm').
			if self.progress:
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
			if node:
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
			if self.progress:
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
			if node:
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
##			file = converttextfile(u, dstdir, file, node)
##			files_generated[file] = ''
##			return file
		if u.headers.maintype == 'text' or u.headers.subtype.find('xml') >= 0:
			binary = ''
		else:
			binary = 'b'
		files_generated[file] = binary
		if self.progress:
			self.progress("Copying %s"%os.path.split(file)[1], None, None, None, None)
		dstfile = os.path.join(dstdir, file)
#		print 'DBG verbatim copy', dstfile
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

	def getcopyinfo(self):
		return self.copydir, self.copydirname, self.files_generated, self.webfiles_generated

	def gen_rpfile(self):
		i = self.__generate_number
		self.__generate_number = self.__generate_number + 1
		return self.__generate_basename + `i` + '.rp'

	def gen_rtfile(self):
		i = self.__generate_number
		self.__generate_number = self.__generate_number + 1
		return self.__generate_basename + `i` + '.rt'

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

def intToEnumString(intValue, dict):
	if dict.has_key(intValue):
		return dict[intValue]
	else:
		return dict[0]
