"""Check a GRiNS document for playability with G2"""

from pysmil import *
from xml.dom.transformer import *
from xml.dom.dc_builder import DcBuilder
from xml.dom.writer import XmlWriter

import sys
import urlparse
import urllib
import os
import posixpath


#
# An extension of the transformer class. The base class can only
# specify transformation of single nodes (with the do_* methods), this
# one can do whole subtrees (with subtree_* methods).
#
# This class also contains the canhandle and canhandleurl methods, which
# check nodes and urls for compatability. The actual data they use to
# make this check are set by the subclasses.

class MyTransformer(Transformer):
	MEDIA_NODES=('animation', 'audio', 'img', 'ref',
		     'text', 'textstream', 'video')

	def _transform_node(self, node):
		if node.NodeType == ELEMENT:
                        if hasattr(self, 'tree_' + node.tagName):
                                func = getattr(self, 'tree_' + node.tagName)
				return func(node)
		return Transformer._transform_node(self, node)

	def canhandle(self, node):
		if node.NodeType == DOCUMENT:
			return self.canhandle(node.documentElement)
		ok = 1
		if node.NodeType == ELEMENT:
			if node.GI == 'switch':
				for child in node.getChildren():
					if self.canhandle(child):
						return 1
				return 0
			elif node.GI in self.MEDIA_NODES:
				if node.attributes.has_key('src'):
					url = node.attributes['src']
					if not self.canhandleurl(url):
						print 'cannot handle', url
						ok = 0
			for child in node.getChildren():
				if not self.canhandle(child):
					ok = 0
		return ok

	def canhandleurl(self, url):
		scheme, location, path, parameters, query, fragment = \
			urlparse.urlparse(url)
		if not scheme in self.OK_SCHEMES:
			return 0
		dummy, ext = posixpath.splitext(path)
		if not self.OK_EXTENSIONS.has_key(ext):
			return 0
		#
		# If the value is non-zero we should call the dataconverter
		# check method to check actual validity.
		if self.OK_EXTENSIONS[ext]:
			return self.dataconverter.check(url)
		return 1
	

class G2CommonTransformer(MyTransformer):
	#
	# Extensions that are OK for G2 playback. A non-zero value
	# means we have to call the dataconverter check routine for
	# additional checks.
	#
	OK_EXTENSIONS={
		'.ra': 0,
		'.rm': 0,
		'.rt': 0,
		'.rv': 0,
		'.rp': 0,
		'.jpg': 1,
	}
	#
	# URL schemes that the G2 player understands.
	#
	OK_SCHEMES=('', 'file', 'ftp', 'http', 'rtsp')
	
	def __init__(self, dataconverter):
		self.dataconverter = dataconverter
		Transformer.__init__(self)


	def do_region(self, node):
		# G2 player needs width/height. Set to 100% if not specified
		# Affects GRiNS too, but this is not to be helped.
		#
		if not node.attributes.has_key('width'):
			node.attributes['width'] = '100%'
		if not node.attributes.has_key('height'):
			node.attributes['height'] = '100%'
		return [node]

	def other_g2_conversions(self, node):
		# Handles various other things G2 doesn't do.
		# These affect GRiNS too, but so be it...
		if node.attributes.has_key('dur'):
			dur = node.attributes['dur']
			if dur == 'indefinite':
				node.attributes['dur'] = '9999s'
				print 'WARNING: indefinite duration set to 9999'
				print

	def convertnode(self, node):
		"""Duplicate and convert a subtree, if possible"""
		if not node.attributes.has_key('src'):
			return None
		url = node.attributes['src']
		tag = node.GI
		newurl = self.dataconverter.converturl(url, tag)
		if not newurl:
			return None
		newnode = self.dupnode(node)
		newnode.attributes['src'] = newurl
		return newnode

	def dupnode(self, node):
		"""Duplicate a subtree"""
		if node.NodeType == ELEMENT:
			tag = node.GI
			attrs = node.attributes.items()
			newnode = self.dom_factory.createElement(tag, {})
			attrs = self.dupattrs(node, attrs)
			for attr, value in attrs:
				newnode.attributes[attr] = value
			for ch in node.getChildren():
				newch = self.dupnode(ch)
				newnode.insertBefore(newch, None)
			return newnode
		elif node.NodeType == TEXT:
			return self.dom_factory.createTextNode(node.data)
		elif node.NodeType == COMMENT:
			return self.dom_factory.createComment(node.data)
		else:
			raise 'dupnode: unimplemented NodeType', node.NodeType


	def dupattrs(self, node, attrs):
		return attrs
	
class G2SwitchTransformer(G2CommonTransformer):
	within_switch = 0

	def tree_switch(self, node):
		#
		# Within a switch we don't have to add additional switches
		#
		if self.canhandle(node):
			return [node]
		self.within_switch = self.within_switch + 1
		rv = Transformer._transform_node(self, node)
		self.within_switch = self.within_switch - 1
		return rv

	def dupattrs(self, node, attrs):
		newattrs = []
		for attr, value in attrs:
			if attr == 'id':
				value = 'g2_' + value
			newattrs.append(attr, value)
		return newattrs

	def do_ref(self, node):
		if node.attributes.has_key('src'):
			url = node.attributes['src']
			if not self.canhandleurl(url):
				node2 = self.convertnode(node)
				if node2:
					self.other_g2_conversions(node2)
					if node.attributes.has_key('id'):
						the_id = node.attributes['id']
						del node.attributes['id']
						del node2.attributes['id']
						return [SWITCH(
							'\n',node2,
							'\n',node,
							'\n',
							id=the_id)]
					else:
						return [SWITCH(
							'\n',node2,
							'\n',node,
							'\n')]
				elif self.within_switch:
					self.other_g2_conversions(node)
					return [node]
				else:
					self.other_g2_conversions(node)
					return [SWITCH('\n', node, '\n')]
		self.other_g2_conversions(node)
		return [node]

	do_animation = do_ref
	do_audio = do_ref
	do_img = do_ref
	do_text = do_ref
	do_textstream = do_ref
	do_video = do_ref
			
	
class G2OnlyTransformer(G2CommonTransformer):
	
	def do_ref(self, node):
		if node.attributes.has_key('src'):
			url = node.attributes['src']
			if not self.canhandleurl(url):
				node2 = self.convertnode(node)
				if node2:
					node = node2
		self.other_g2_conversions(node)
		return [node]
				
	do_animation = do_ref
	do_audio = do_ref
	do_img = do_ref
	do_text = do_ref
	do_textstream = do_ref
	do_video = do_ref

class DataConverter:
	def converturl(self, url, type):
		scheme, location, path, parameters, query, fragment = \
			urlparse.urlparse(url)
		if scheme == 'data':
			return self.savedata(url, type)
		if query or fragment:
			return None
		dummy, filename = posixpath.split(path)
		filebase, ext = posixpath.splitext(filename)
		if  self.CONVERTERS.has_key(ext):
			method, args = self.CONVERTERS[ext]
		else:
			method = self.convert_unknown
			args = ()
		new = apply(method, (self, url, filebase) + args)
		return new

	def savedata(self, url, type):
		if not self.DEFAULT_MEDIA_TYPES.has_key(type):
			print 'UNKNOWN: immedeate data of type', type
			print
			return None
		new = newfilename('immdata', self.DEFAULT_MEDIA_TYPES[type])
		fp = createurlfile(new)
		fp.write(urllib.urlopen(url).read())
		fp.close()
		return new

	def convert_unknown(self, url):
			print 'UNKNOWN:', url
			print
			return None

class G2UserConverter(DataConverter):
	def userconvert(self, url, filebase, ext):
		new = newfilename(filebase, ext)
		print "CONVERT:", url
		print "     TO ", new
		print
		return new
		
	def usercheck(self, url):
		print "  CHECK:", url
		print
		return 1

	CONVERTERS={
		'.au': (userconvert, ('.ra',)),
		'.aif': (userconvert, ('.ra',)),
		'.aiff': (userconvert, ('.ra',)),
		'.wav': (userconvert, ('.ra',)),
		'.gif': (userconvert, ('.jpg',)),
		'.txt': (userconvert, ('.rt',)),
		'.htm': (userconvert, ('.rt',)),
		'.html': (userconvert, ('.rt',)),
		'.qt': (userconvert, ('.rv',)),
		'.mov': (userconvert, ('.rv',)),
		'.mpg': (userconvert, ('.rv',)),
		'.mpv': (userconvert, ('.rv',)),
	}
	DEFAULT_MEDIA_TYPES={
		'audio': '.ra',
		'img': '.jpg',
		'text': '.rt',
		'textstream': '.rt',
		'video': '.rv',
	}

class G2BatchConverter(DataConverter):
	def __init__(self, fp):
		self.fp = fp
		
	def filenames(self, url, filebase, ext):
		new = newfilename(filebase, ext)
		old_pathname = self.url2pathname(url)
		if not old_pathname or not os.path.exists(old_pathname):
			print "CONVERT:", url
			print "     TO ", new
			print
			return None, None, new
		new_pathname = self.url2pathname(new)
		if os.path.exists(new_pathname):
			oldtime = os.stat(old_pathname)[8]
			newtime = os.stat(new_pathname)[8]
			if newtime > oldtime:
				print "UPTODATE:", new
				print
				return None, None, new
		return old_pathname, new_pathname, new

	def url2pathname(self, url):
		scheme, location, path, parameters, query, fragment = \
			urlparse.urlparse(url)
		if scheme and scheme != 'file':
			return None
		if location or parameters or query or fragment:
			return None
		return urllib.url2pathname(path)
	
	def usercheck(self, url):
		print "  CHECK:", url
		print
		return 1

class G2UnixBatchConverter(G2BatchConverter):

	def convert_image(self, url, filebase, ext):
		old, new, newurl = self.filenames(url, filebase, ext)
		if old and new:
			self.fp.write('cjpeg -restart 1B "%s" > "%s"\n' %
				        (old, new))
		return newurl

	def convert_av(self, url, filebase, ext):
		old, new, newurl = self.filenames(url, filebase, ext)
		if old and new:
			self.fp.write('rmenc -I "%s" -O "%s"\n' %
				        (old, new))
		return newurl

	def convert_text(self, url, filebase, ext):
		new = newfilename(filebase, ext)
		print "CONVERT:", url
		print "     TO ", new
		print
		return new
		
	CONVERTERS={
		'.au': (convert_av, ('.ra',)),
		'.aif': (convert_av, ('.ra',)),
		'.aiff': (convert_av, ('.ra',)),
		'.wav': (convert_av, ('.ra',)),
		'.gif': (convert_image, ('.jpg',)),
		'.txt': (convert_text, ('.rt',)),
		'.htm': (convert_text, ('.rt',)),
		'.html': (convert_text, ('.rt',)),
		'.qt': (convert_av, ('.rv',)),
		'.mov': (convert_av, ('.rv',)),
		'.mpg': (convert_av, ('.rv',)),
		'.mpv': (convert_av, ('.rv',)),
	}
	DEFAULT_MEDIA_TYPES={
		'audio': '.ra',
		'img': '.jpg',
		'text': '.rt',
		'textstream': '.rt',
		'video': '.rv',
	}

USED={}
def newfilename(filebase, ext):
	filename = 'g2cdata/%s%s'%(filebase, ext)
	if USED.has_key(filename):
		num = 1
		while 1:
			filename = 'g2cdata/%s%03d%s'%(filebase, num, ext)
			if not USED.has_key(filename):
				path = urllib.url2pathname(filename)
				dir, dummy = os.path.split(path)
				if not os.path.exists(dir):
					break
				if not os.path.exists(path):
					break
			num = num + 1
	USED[filename] = 1
	return filename

def createurlfile(url):
	filename = urllib.url2pathname(url)
	dirname = os.path.split(filename)[0]
	if dirname and not os.path.exists(dirname):
		os.makedirs(dirname)
	return open(filename, 'w')
	converter = G2UnixBatchConverter(open('@g2conf.sh', 'w'))


def main():
	if len(sys.argv) != 3:
		print "Usage %s input output"%sys.argv[0]
		sys.exit(1)
	data = open(sys.argv[1]).read()

	parser = DcBuilder()
	parser.feed(data)

	converter = G2UnixBatchConverter(open('@g2conf.sh', 'w'))
	transformer = G2OnlyTransformer(converter)

	document = transformer.transform(parser.document)

	outfile = open(sys.argv[2], 'w')
	writer = XmlWriter(outfile)
	writer.write(document)

if __name__ == '__main__':
	main()
