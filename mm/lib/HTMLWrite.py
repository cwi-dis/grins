__version__ = "$Id$"

# HTMLWrite - Write out layout information in HTML for embedded G2 player


from MMExc import *		# Exceptions
from MMNode import alltypes, leaftypes, interiortypes
import MMCache
import MMAttrdefs
import Hlinks
from AnchorDefs import *
import string
import os
import MMurl
import regsub
import re
from cmif import findfile
import windowinterface
import MMurl


def nameencode(value):
	"""Quote a value"""
	value = string.join(string.split(value,'&'),'&amp;')
	value = string.join(string.split(value,'>'),'&gt;')
	value = string.join(string.split(value,'<'),'&lt;')
	value = string.join(string.split(value,'"'),'&quot;')
##	if '&' in value:
##		value = regsub.gsub('&', '&amp;', value)
##	if '>' in value:
##		value = regsub.gsub('>', '&gt;', value)
##	if '<' in value:
##		value = regsub.gsub('<', '&lt;', value)
##	if '"' in value:
##		value = regsub.gsub('"', '&quot;', value)
	return '"' + value + '"'

# CMIF channel types that have a visible representation
visible_channel_types={
	'text':1,
	'image':1,
	'video': 1,
	'movie':1,
	'mpeg':1,
	'html':1,
	'label':1,
	'RealPix':1,
	'RealText':1,
	'RealVideo':1,
}

# This string is written at the start of a SMIL file.
EVALcomment = '<!-- Created with an evaluation copy of GRiNS -->\n'

nonascii = re.compile('[\200-\377]')

isidre = re.compile('^[a-zA-Z_][-A-Za-z0-9._]*$')


Error = 'Error'

def WriteFile(root, filename, smilurl, oldfilename='', evallicense = 0):
	# XXXX If oldfilename set we should use that as a template
	import cmif
	templatedir = cmif.findfile('Templates')
	templatedir = MMurl.pathname2url(templatedir)
	#
	# This is a bit of a hack. G2 appears to want its URLs without
	# %-style quoting.
	#
	smilurl = MMurl.unquote(smilurl)
	fp = open(filename, 'w')
	ramfile = ramfilename(filename)
	try:
		open(ramfile, 'w').write(smilurl+'\n')
	except IOError, arg:
		showmessage('I/O Error writing %s: %s'%(ramfile, arg), mtype = 'error')
		return
	if os.name == 'mac':
		import macfs
		import macostools
		fss = macfs.FSSpec(ramfile)
		fss.SetCreatorType('PNst', 'PNRA')
		macostools.touched(fss)
	ramurl = MMurl.pathname2url(ramfile)
	ramurl = MMurl.unquote(ramurl)
	try:
		writer = HTMLWriter(root, fp, filename, ramurl, oldfilename, evallicense, templatedir)
		writer.write()
	except Error, msg:
		windowinterface.showmessage(msg, mtype = 'error')
		return
	if os.name == 'mac':
		fss = macfs.FSSpec(filename)
		fss.SetCreatorType('MOSS', 'TEXT')
		macostools.touched(fss)

import FtpWriter
def WriteFTP(root, filename, smilurl, ftpparams, oldfilename='', evallicense = 0):
	host, user, passwd, dir = ftpparams
	import settings
	templatedir = settings.get('templatedir_url')
	#
	# First create and upload the RAM file
	#
	smilurl = MMurl.unquote(smilurl)
	ramfile = ramfilename(filename)
	try:
		ftp = FtpWriter.FtpWriter(host, ramfile, user=user, passwd=passwd, dir=dir, ascii=1)
		ftp.write(smilurl+'\n')
		ftp.close()
	except FtpWriter.all_errors, msg:
		windowinterface.showmessage('Webserver upload failed:\n' + msg, mtype = 'error')
		return
	#
	# Now create and upload the webpage
	#
	ramurl = MMurl.pathname2url(ramfile)
	try:
		ftp = FtpWriter.FtpWriter(host, filename, user=user, passwd=passwd, dir=dir, ascii=1)
		try:
			writer = HTMLWriter(root, ftp, filename, ramurl, oldfilename, evallicense, templatedir)
			writer.write()
			ftp.close()
		except Error, msg:
			windowinterface.showmessage(msg, mtype = 'error')
			return
	except FtpWriter.all_errors, msg:
		windowinterface.showmessage('Webserver upload failed:\n' + msg, mtype = 'error')
		return

def ramfilename(htmlfilename):
	if htmlfilename[-4:] == '.htm':
		ramfilename = htmlfilename[:-4] + '.ram'
	elif htmlfilename[-5:] == '.html':
		ramfilename = htmlfilename[:-5] + '.ram'
	else:
		ramfilename = htmlfilename + '.ram'
	return ramfilename
	
class HTMLWriter:
	def __init__(self, node, fp, filename, ramurl, oldfilename='', evallicense = 0, templatedir_url=''):
		self.evallicense = evallicense
		self.ramurl = ramurl
		self.templatedir_url = templatedir_url

		self.root = node
		self.fp = fp
		self.__title = node.GetContext().gettitle()

		self.ids_used = {}

		self.ch2name = {}
		self.top_levels = []
		self.calcchnames1(node)

		if len(self.top_levels) > 1:
			print '** Document uses multiple toplevel channels'
			self.uses_cmif_extension = 1


	def outtag(self, tag, attrs = None):
		if attrs is None:
			attrs = []
		out = '<' + tag
		for attr, val in attrs:
			out = out + ' %s=%s' % (attr, nameencode(val))
		out = out + '>\n'
		return out
				
	def write(self):
		import version
		ctxa = self.root.GetContext().attributes
		#
		# Step one - Read the template data. This is an html file
		# with %(name)s constructs that will be filled in later
		#
		if not ctxa.has_key('project_html_page'):
			raise Error, 'Webpage generation skipped: No HTML template selected.'
		template_name = ctxa['project_html_page']
		templatedir = findfile('Templates')
		templatefile = os.path.join(templatedir, template_name)
		if not os.path.exists(templatefile):
			raise Error, 'HTML template file does not exist'
		try:
			template_data = open(templatefile).read()
		except IOError, arg:
			raise Error, 'HTML template %s: I/O error'%templatename
		
		#
		# Step two - Construct the dictionary for the %(name)s values
		#
		outdict = {}

		outdict['title'] = nameencode(self.__title)[1:-1]
		outdict['generator'] = '<meta name="generator" content="GRiNS %s">'%version.version
		outdict['generatorname'] = 'GRiNS %s'%version.version
		if self.evallicense:
			outdict['generator'] = outdict['generator'] + '\n' + EVALcomment
			outdict['generatorname'] = outdict['generatorname'] + ' (evaluation copy)'
		outdict['ramurl'] = self.ramurl
		outdict['unquotedramurl'] = MMurl.unquote(self.ramurl)
		outdict['templatedir'] = self.templatedir_url
		outdict['author'] = nameencode(ctxa.get('author', ''))[1:-1]
		outdict['copyright'] = nameencode(ctxa.get('copyright', ''))[1:-1]
		
		playername = 'clip_1'
		
		out = '<!-- START-GRINS-GENERATED-CODE multiregion -->\n'
		channels = self.get_visible_channels()
		for region, x, y, w, h, z in channels:
			if not w or not h:
				out = out+'<!-- Region %s used for non-visible media only, skipped-->\n'%region
				continue
			tmp2 = 'left:%dpx; top:%dpx; width:%dpx; height:%dpx;'%(x, y, w, h)
			if z > 0:
				tmp2 = tmp2+ ' z-index:%d'%z
			out = out + '<div layout="position:absolute; %s">\n'%tmp2
			
			out = out + self.outobject(w, h, [
				('controls', 'ImageWindow'),
				('console', playername),
				('autostart', 'false'),
				('region', region),
				('src', MMurl.unquote(self.ramurl))])
				
			out = out + '</div>\n'
		out = out + '<!-- END-GRINS-GENERATED-CODE multiregion -->\n'
		outdict['multiregion'] = out
		
		out = '<!-- START-GRINS-GENERATED-CODE singleregion -->\n'

		if self.top_levels:
			if len(self.top_levels) > 1:
				raise Error, "Multiple toplevel windows"
			w, h = self.top_channel_size(self.top_levels[0])
			if not w or not h:
				raise Error, "Zero-sized presentation window"

			out = out + '<div>\n'
			
			out = out + self.outobject(w, h, [
				('controls', 'ImageWindow'),
				('console', playername),
				('autostart', 'false'),
				('src', MMurl.unquote(self.ramurl))])
				
			out = out + '</div>\n'
			
		out = out + '<!-- END-GRINS-GENERATED-CODE singleregion -->\n'
		outdict['singleregion'] = out
		
		#
		# Step three - generate the output
		#
		try:
			output = template_data % outdict
		except:
			raise Error, "Error in HTML template %s"%templatefile
		#
		# Step four - Write it
		#
		self.fp.write(output)
		
	def get_visible_channels(self):
		if not self.top_levels:
			return []
		if len(self.top_levels) > 1:
			raise Error, "Multiple toplevel windows"
		top_w, top_h = self.top_channel_size(self.top_levels[0])
		if not top_w or not top_h:
			raise Error, "Zero-sized presentation window"
		rv = []
		for ch in self.root.GetContext().channels:
			if not visible_channel_types.has_key(ch['type']):
				continue
			name = self.ch2name[ch]
			x, y, w, h = self.channel_pos(ch, top_w, top_h)
			z = ch.get('z', 0)
			rv.append(name, x, y, w, h, z)
		return rv
		
	def outobject(self, width, height, arglist):
		out = self.outtag('object', [
			('classid', 'clsid:CFCDAA03-8BE4-11cf-B84B-0020AFBBCCFA'),
			('width', `width`),
			('height', `height`)])
		for arg, val in arglist:
			out = out + self.outtag('param', [('name', arg), ('value', val)])
		# Trick: if the browser understands the object tag but not the embed
		# tag (inside it) it will quietly skip it.
		arglist = arglist[:]
		arglist.append(('width', `width`))
		arglist.append(('height', `height`))
		arglist.append(('type', 'audio/x-pn-realaudio-plugin'))
		arglist.append(('nojava', 'true'))
		out = out + self.outtag('embed', arglist)
		out = out + '</object>\n'
		return out
		
	def calcchnames1(self, node):
		"""Calculate unique names for channels; first pass"""
		context = node.GetContext()
		channels = context.channels
		for ch in channels:
			name = identify(ch.name)
			if not self.ids_used.has_key(name):
				self.ids_used[name] = 0
				self.ch2name[ch] = name
			else:
				raise Error, "Duplicate region name"
			if not ch.has_key('base_window') and \
			   ch['type'] not in ('sound', 'shell', 'python',
					      'null', 'vcr', 'socket', 'cmif',
					      'midi', 'external'):
				# top-level channel with window
				self.top_levels.append(ch)
				if not self.__title:
					self.__title = ch.name
		if not self.__title and channels:
			# no channels with windows, so take very first channel
			self.__title = channels[0].name
			
	def channel_pos(self, ch, basewidth, baseheight):
		if not ch.has_key('base_winoff'):
			return None, None, None, None
		units = ch.get('units', 2)
		x, y, w, h = ch['base_winoff']
		if units == 0:
			# convert mm to pixels
			# (assuming 100 dpi)
			x = int(x / 25.4 * 100.0 + .5)
			y = int(y / 25.4 * 100.0 + .5)
			w = int(w / 25.4 * 100.0 + .5)
			h = int(h / 25.4 * 100.0 + .5)
		if units == 1:
			x = x * basewidth + .5
			y = y * baseheight + .5
			w = w * basewidth + .5
			h = h * baseheight + .5
		# else: units are already in pixels
		return int(x), int(y), int(w), int(h)

	def top_channel_size(self, ch):
		if not ch.has_key('winsize'):
			return None, None
		units = ch.get('units', 0)
		w, h = ch['winsize']
		if units == 0:
			# convert mm to pixels
			# (assuming 100 dpi)
			w = int(w / 25.4 * 100.0 + .5)
			h = int(h / 25.4 * 100.0 + .5)
		if units == 1:
			raise Error, "Cannot use relative coordinates for toplevel window"
		# else: units are already in pixels
		return int(w), int(h)

namechars = string.letters + string.digits + '_-.'

def identify(name):
	"""Turn a CMIF name into an identifier"""
	rv = []
	for ch in name:
		if ch in namechars:
			rv.append(ch)
		else:
			if rv and rv[-1] != '-':
				rv.append('-')
	# the first character must not be a digit
	if rv and rv[0] in string.digits:
		rv.insert(0, '_')
	return string.join(rv, '')
