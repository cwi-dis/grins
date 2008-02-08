"""Check a GRiNS document for playability with G2"""

from xml.dom.transformer import *
from xml.dom.dc_builder import DcBuilder
from xml.dom.pyhtml import *
from xml.dom.writer import XmlWriter

import sys
import urlparse
import posixpath

MEDIA_NODES=('animation', 'audio', 'img', 'ref', 'text', 'textstream', 'video')
OK_EXTENSIONS=('.ra', '.rm', '.rt', '.rv', '.rp')
OK_SCHEMES=('', 'file', 'ftp', 'http', 'rtsp')

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
    return (ext in OK_EXTENSIONS)

def transform(document):
    ok = canhandle(document)
##     return document

def main():
    if len(sys.argv) < 2:
        print "Usage %s input [output]"%sys.argv[0]
        sys.exit(1)
    data = open(sys.argv[1]).read()

    parser = DcBuilder()
    parser.feed(data)

    document = transform(parser.document)

##     if len(sys.argv) > 2:
##         outfile = open(sys.argv[2], 'w')
##     else:
##         outfile = sys.stdout
##     writer = XmlWriter(outfile)
##     writer.write(document)

if __name__ == '__main__':
    main()
