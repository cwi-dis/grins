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

def userconvert(src, dst):
	print "CONVERT:", src
	print "     TO ", dst
	print
	return 1

def usercheck(src):
	print "  CHECK:", src
	print
	return 1

MEDIA_NODES=('animation', 'audio', 'img', 'ref', 'text', 'textstream', 'video')
OK_EXTENSIONS={
	'.ra': None,
	'.rm': None,
	'.rt': None,
	'.rv': None,
	'.rp': None,
	'.jpg': usercheck,
}
OK_SCHEMES=('', 'file', 'ftp', 'http', 'rtsp')
CONVERTERS={
	'.au': ('.ra', userconvert),
	'.aif': ('.ra', userconvert),
	'.aiff': ('.ra', userconvert),
	'.wav': ('.ra', userconvert),
	'.gif': ('.jpg', userconvert),
	'.txt': ('.rt', userconvert),
	'.htm': ('.rt', userconvert),
	'.html': ('.rt', userconvert),
	'.qt': ('.rv', userconvert),
	'.mov': ('.rv', userconvert),
	'.mpg': ('.rv', userconvert),
	'.mpv': ('.rv', userconvert),
}
G2_TYPES={
	'audio': '.ra',
	'img': '.jpg',
	'text': '.rt',
	'textstream': '.rt',
	'video': '.rv',
}

#
# An extension of the transformer class. The base class can only
# specify transformation of single nodes (with the do_* methods), this
# one can do whole subtrees (with subtree_* methods).
#
class MyTransformer(Transformer):
	def _transform_node(self, node):
		if node.NodeType == ELEMENT:
                        if hasattr(self, 'tree_' + node.tagName):
                                func = getattr(self, 'tree_' + node.tagName)
				return func(node)
		return Transformer._transform_node(self, node)

class G2Transformer(MyTransformer):
	within_switch = 0
	
	def do_ref(self, node):
		if node.attributes.has_key('src'):
			url = node.attributes['src']
			if not canhandleurl(url):
				node2 = self.convertnode(node)
				if node2:
					return [SWITCH('\n', node2,'\n',
						       node, '\n')]
				elif self.within_switch:
					return [node]
				else:
					return [SWITCH('\n', node, '\n')]
		return [node]
				
	do_animation = do_ref
	do_audio = do_ref
	do_img = do_ref
	do_text = do_ref
	do_textstream = do_ref
	do_video = do_ref

	def tree_switch(self, node):
		if canhandle(node):
			return [node]
		self.within_switch = self.within_switch + 1
		rv = Transformer._transform_node(self, node)
		self.within_switch = self.within_switch - 1
		return rv

	def convertnode(self, node):
		if not node.attributes.has_key('src'):
			return None
		url = node.attributes['src']
		tag = node.GI
		newurl = converturl(url, tag)
		if not newurl:
			return None
		newnode = self.dupnode(node)
		newnode.attributes['src'] = newurl
		return newnode

	def dupnode(self, node):
		if node.NodeType == ELEMENT:
			tag = node.GI
			attrs = node.attributes.items()
			newnode = self.dom_factory.createElement(tag, {})
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

def converturl(url, type):
	scheme, location, path, parameters, query, fragment = \
		urlparse.urlparse(url)
	if scheme == 'data':
		return savedata(url, type)
	if query or fragment:
		return None
	dummy, filename = posixpath.split(path)
	filebase, ext = posixpath.splitext(filename)
	if not CONVERTERS.has_key(ext):
		print 'UNKNOWN:', url
		print
		return None
	new = newfilename(filebase,CONVERTERS[ext][0])
	if CONVERTERS[ext][1](url, new):
		return new
	return None

def savedata(url, type):
	if not G2_TYPES.has_key(type):
		print 'UNKNOWN: immedeate data of type', type
		print
		return None
	new = newfilename('immdata', G2_TYPES[type])
	fp = createurlfile(new)
	fp.write(urllib.urlopen(url).read())
	fp.close()

USED={}
def newfilename(filebase, ext):
	filename = 'g2cdata/%s%s'%(filebase, ext)
	if USED.has_key(filename):
		num = 1
		while 1:
			filename = 'g2cdata/%s%03d%s'%(filebase, num, ext)
			if not USED.has_key(filename):
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

def canhandle(node):
	if node.NodeType == DOCUMENT:
		return canhandle(node.documentElement)
	ok = 1
	if node.NodeType == ELEMENT:
		if node.GI == 'switch':
			for child in node.getChildren():
				if canhandle(child):
					return 1
			return 0
		elif node.GI in MEDIA_NODES:
			if node.attributes.has_key('src'):
				url = node.attributes['src']
				if not canhandleurl(url):
					print 'cannot handle', url
					ok = 0
		for child in node.getChildren():
			if not canhandle(child):
				ok = 0
	return ok

def canhandleurl(url):
	scheme, location, path, parameters, query, fragment = \
		urlparse.urlparse(url)
	if not scheme in OK_SCHEMES:
		return 0
	dummy, ext = posixpath.splitext(path)
	if not OK_EXTENSIONS.has_key(ext):
		return 0
	if OK_EXTENSIONS[ext]:
		return OK_EXTENSIONS[ext](url)
	return 1
	
def transform(document):
	transformer = G2Transformer()
	return transformer.transform(document)

def main():
	if len(sys.argv) != 3:
		print "Usage %s input output"%sys.argv[0]
		sys.exit(1)
	data = open(sys.argv[1]).read()

	parser = DcBuilder()
	parser.feed(data)

	document = transform(parser.document)

	outfile = open(sys.argv[2], 'w')
	writer = XmlWriter(outfile)
	writer.write(document)

if __name__ == '__main__':
	main()
