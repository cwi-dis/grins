__version__ = "$Id$"

# MMWrite -- Multimedia tree writing interface


from MMExc import CheckError
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
import urlcache

from SMIL import *
from SMILTreeWriteBase import *

interiortypes = interiortypes + ['foreign']

from nameencode import nameencode

NSGRiNSprefix = 'GRiNS'
NSRP9prefix = 'rn'
NSQTprefix = 'qt'
NSPSS4prefix = 'pss4'

# This string is written at the start of a SMIL file.
##encoding = ' encoding="ISO-8859-1"'
encoding = ''				# Latin-1 (ISO-8859-1) coincides with lower part of Unicode
SMILdecl = '<?xml version="1.0"%s?>\n' % encoding
doctype = '<!DOCTYPE smil PUBLIC "%s"\n%s"%s">\n' % (SMILpubid,' '*22,SMILdtd)
doctype2 = '<!DOCTYPE smil PUBLIC "%s"\n%s"%s">\n' % (SMILBostonPubid,' '*22,SMILBostonDtd)
xmlnsGRiNS = 'xmlns:%s' % NSGRiNSprefix
xmlnsRP9 = 'xmlns:%s' % NSRP9prefix
xmlnsQT = 'xmlns:%s' % NSQTprefix
xmlnsPSS4 = 'xmlns:%s' % NSPSS4prefix



# Write a node to a CMF file, given by filename

cancel = 'cancel'

def WriteFile(root, filename, grinsExt = 1, qtExt = features.EXPORT_QT in features.feature_set,
	      rpExt = features.EXPORT_REAL in features.feature_set, pss4Ext = 0, copyFiles = 0, convertfiles = 1, convertURLs = 0,
	      evallicense = 0, progress = None, prune = 0, smil_one = 0, addattrs = 0):
	try:
		writer = SMILWriter(root, None, filename, grinsExt = grinsExt, qtExt = qtExt, rpExt = rpExt, pss4Ext = pss4Ext, copyFiles = copyFiles, convertfiles = convertfiles, convertURLs = convertURLs, evallicense = evallicense, progress = progress, prune = prune, smil_one = smil_one, addattrs = addattrs)
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
	     rpExt = features.EXPORT_REAL in features.feature_set, pss4Ext = 0, copyFiles = 0, convertfiles = 1, convertURLs = 0,
	     evallicense = 0, progress = None, prune = 0, smil_one = 0, weburl = None):
	host, user, passwd, dir = ftpparams
	try:
		conn = FtpWriter.FtpConnection(host, user=user, passwd=passwd, dir=dir)
		ftp = conn.Writer(filename, ascii=1)
		try:
			writer = SMILWriter(root, ftp, filename, tmpcopy = 1, grinsExt = grinsExt, qtExt = qtExt, rpExt = rpExt, pss4Ext = pss4Ext, copyFiles = copyFiles, convertfiles = convertfiles, convertURLs = convertURLs, evallicense = evallicense, progress = progress, prune = prune, smil_one = smil_one, weburl = weburl)
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

qt_context_attrs = {
	'qttimeslider':0,
	'qtchaptermode':0,
	'autoplay':0,
	'qtnext':0,
	'immediateinstantiation':0,
	}
from smil_mediatype import smil_mediatype

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
			x.tag_positions = x.tag_positions + ((end-2-len(self.__stack[-1][0]), end-2),)
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
		hasPSS4prefix = (self.__stack or 0) and self.__stack[-1][5]
		if not hasPSS4prefix and self.pss4Ext:
			for attr, val in attrs:
				if attr == xmlnsPSS4:
					hasPSS4prefix = 1
					break
				if attr[:len(NSPSS4prefix)] == NSPSS4prefix:
					attrs.insert(0, (xmlnsPSS4, PSS4ns))
					hasPSS4prefix = 1
					break
		if not hasPSS4prefix and tag[:len(NSPSS4prefix)] == NSPSS4prefix:
			# ignore this tag
			self.__ignoring = 1
			return
		hasGRiNSprefix = (self.__stack or 0) and self.__stack[-1][2]
		if not hasGRiNSprefix and (self.grinsExt or self.addattrs):
			for attr, val in attrs:
				if attr == xmlnsGRiNS:
					hasGRiNSprefix = 1
					break
				if attr[:len(NSGRiNSprefix)] == NSGRiNSprefix and (self.grinsExt or attr[len(NSGRiNSprefix)+1:] in addattrs):
					attrs.insert(0, (xmlnsGRiNS, GRiNSns))
					hasGRiNSprefix = 1
					break
		if (not hasGRiNSprefix or not self.grinsExt) and tag[:len(NSGRiNSprefix)] == NSGRiNSprefix:
			# ignore this tag
			self.__ignoring = 1
			return
		start, end = write('<' + tag)
		if self.set_char_pos and x is not None:
			x.char_positions = start, None
			x.tag_positions = ((end-len(tag), end), )
		for attr, val in attrs:
			if attr[:len(NSGRiNSprefix)] == NSGRiNSprefix and (not hasGRiNSprefix or (not self.grinsExt and attr[len(NSGRiNSprefix)+1:] not in addattrs)):
				continue
			if attr[:len(NSRP9prefix)] == NSRP9prefix and not hasRP9prefix:
				continue
			if attr[:len(NSQTprefix)] == NSQTprefix and not hasQTprefix:
				continue
			if attr[:len(NSPSS4prefix)] == NSPSS4prefix and not hasPSS4prefix:
				continue
			write(' %s=%s' % (attr, nameencode(val)))
		self.__isopen = 1
		self.__stack.append((tag, x, hasGRiNSprefix, hasQTprefix, hasRP9prefix, hasPSS4prefix))

class SMILWriter(SMIL, BaseSMILWriter, SMILWriterBase):
	def __init__(self, node, fp, filename, grinsExt = 1,
		     rpExt = features.EXPORT_REAL in features.feature_set,
		     qtExt = features.EXPORT_QT in features.feature_set,
		     pss4Ext = 0,
		     copyFiles = 0, evallicense = 0, tmpcopy = 0, progress = None,
		     convertURLs = 0, convertfiles = 1, set_char_pos = 0, prune = 0,
		     smil_one = 0, addattrs = 0, weburl = None):
		ctx = node.GetContext()
		SMILWriterBase.__init__(self, ctx, filename, copyFiles, tmpcopy, convertURLs, convertfiles, weburl, 0, progress)
		self.messages = []

		# remember params
		self.set_char_pos = set_char_pos
		self.grinsExt = grinsExt
		self.qtExt = qtExt
		self.rpExt = rpExt
		self.pss4Ext = pss4Ext
		self.evallicense = evallicense
		self.prune = prune
		self.progress = progress
		self.root = node
		self.addattrs = addattrs # add attributes to make processing faster

		# some abbreviations
		self.hyperlinks = ctx.hyperlinks

		self.__generate_number = 0
		if filename == '<string>':
			self.__generate_basename = 'grinstmp'
		else:
			self.__generate_basename = os.path.splitext(os.path.basename(filename))[0]

		self.uses_grins_namespace = grinsExt
		self.uses_qt_namespace = self.qtExt and self.checkQTattrs()
		self.uses_rp_namespace = self.rpExt
		self.uses_pss4_namespace = self.pss4Ext
		self.force_smil_1 = smil_one
		if smil_one:
			self.smilboston = 0
		else:
			self.smilboston = ctx.attributes.get('project_boston', 0)

		self.title = ctx.gettitle()
		assets = ctx.getassets()

		self.calcugrnames()

		self.layout2name = {}
		self.calclayoutnames()

		self.calctransitionnames()

		self.calcchnames1()

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
		if self.uses_pss4_namespace and self.smilboston:
			attrlist.append((xmlnsPSS4, PSS4ns))
			attrlist.append(('systemRequired', NSPSS4prefix))
		if self.smilboston:
			# test attributes are not allowed on the body element,
			# but they are allowed on the smil element, so that's
			# where they get moved
			sysreq = self.root.GetRawAttrDef('system_required', [])
			if sysreq:
				for i in range(len(sysreq)):
					if sysreq[i] == PSS4ns and self.uses_pss4_namespace:
						# already dealt with
						continue
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

		if self.title:
			self.writetag('meta', [('name', 'title'),
					       ('content', self.title)])
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
			# for export don't write attributes starting with project_ or template_, they are meant
			# for internal information-keeping only
			if not self.grinsExt and (key[:8] == 'project_' or key[:9] == 'template_'):
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

			previewShowOption = ch.GetAttrDef('previewShowOption', None)
			if previewShowOption is not None:
				attrlist.append(('%s:previewShowOption' % NSGRiNSprefix, previewShowOption))

			showEditBackground = ch.GetAttrDef('showEditBackground', None)
			if showEditBackground is not None:
				attrlist.append(('%s:showEditBackground' % NSGRiNSprefix, ['false','true'][showEditBackground]))
			editBackground = ch.GetAttrDef('editBackground', None)
			if editBackground is not None:
				attrlist.append(('%s:editBackground' % NSGRiNSprefix, translatecolor(editBackground)))

			# trace image
			traceImage = ch.get('traceImage')
			if traceImage != None:
				attrlist.append(('%s:traceImage' % NSGRiNSprefix, traceImage))

			if self.smilboston:
##				for key, val in ch.items():
##					if not cmif_chan_attrs_ignore.has_key(key):
##						attrlist.append(('%s:%s' % (NSGRiNSprefix, key), MMAttrdefs.valuerepr(key, val)))
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

		previewShowOption = ch.GetAttrDef('previewShowOption', None)
		if previewShowOption is not None:
			attrlist.append(('%s:previewShowOption' % NSGRiNSprefix, previewShowOption))

		showEditBackground = ch.GetAttrDef('showEditBackground', None)
		if showEditBackground is not None:
			attrlist.append(('%s:showEditBackground' % NSGRiNSprefix, ['false','true'][showEditBackground]))
		editBackground = ch.GetAttrDef('editBackground', None)
		if editBackground is not None:
			attrlist.append(('%s:editBackground' % NSGRiNSprefix, translatecolor(editBackground)))

##		for key, val in ch.items():
##			if not cmif_chan_attrs_ignore.has_key(key):
##				attrlist.append(('%s:%s' % (NSGRiNSprefix, key), MMAttrdefs.valuerepr(key, val)))
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

def intToEnumString(intValue, dict):
	if dict.has_key(intValue):
		return dict[intValue]
	else:
		return dict[0]
