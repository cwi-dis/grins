"""Fix faulty coords attributes in anchors"""

from xml.dom.transformer import *
from xml.dom.writer import XmlWriter
from xml.dom.dc_builder import DcBuilder
## For XML 0.5:
## from xml.dom.sax_builder import SaxBuilder
## from xml.dom.core import createDocument
## from xml.sax import saxexts

import sys
import urlparse
import urllib
import os
import posixpath
import getopt
import re

coordre = re.compile(r'^(?P<x>\d+%?),(?P<y>\d+%?),'
                     r'(?P<w>\d+%?),(?P<h>\d+%?)$')


class CoordsTransformer(Transformer):
    new_style = 0
    has_generator = 0
    did_anything = 0
    head = None

    def do_head(self, node):
        self.head = node
        return [node]

    def do_meta(self, node):
        if not node.attributes.has_key('name'):
            return [node]
        if not node.attributes.has_key('content'):
            return [node]
        name = node.attributes['name']
        content = node.attributes['content']
        if name != 'generator':
            return [node]
        self.has_generator = 1
        wanted = 'GRiNS editor 0.3'
        if content[:len(wanted)] == wanted:
            self.new_style = 1
        wanted = 'GRiNS fixcoords'
        if content[:len(wanted)] == wanted:
            self.new_style = 1
        node.attributes['content'] = 'GRiNS fixcoords 1.0'
        return [node]

    def add_generator(self):
        if self.has_generator or self.new_style or not self.head:
            return
        gnode = self.dom_factory.createElement('meta',
                  {'name':'generator',
                   'content':'GRiNS fixcoords 1.0'})
        self.head.insertBefore(gnode, None)

    def do_anchor(self, node):
        if not node.attributes.has_key('coords'):
            return [node]
        coords = node.attributes['coords']
        res = coordre.match(coords)
        x, y, w, h = res.group('x', 'y', 'w', 'h')
        if x[-1] != '%' or y[-1] != '%' or \
           w[-1] != '%' or h[-1] != '%':
            print 'Cannot convert non-percent coordinates', coords
            return [node]
        x = string.atoi(x[:-1])
        y = string.atoi(y[:-1])
        w = string.atoi(w[:-1])
        h = string.atoi(h[:-1])
        x1 = x+w
        y1 = y+h
        coords='%d%%,%d%%,%d%%,%d%%' % (x, y, x1, y1)
        node.attributes['coords'] = coords
        self.did_anything = self.did_anything + 1
        return [node]

def main():
    inputs, save = getargs(sys.argv)
    for iname in inputs:
        process(iname, save)

def process(input, save):
    data = open(input).read()

    parser = DcBuilder()
    parser.feed(data)
    document = parser.document

## For xml 0.5:
##     parser = saxexts.make_parser()
##     builder = SaxBuilder()
##     parser.setDocumentHandler(builder)
##     parser.parse(input)
##     parser.close()
##     document = builder.document

    transformer = CoordsTransformer()

    document = transformer.transform(document)
    transformer.add_generator()

    if transformer.new_style:
        msg = 'already has new-style coords'
        save = 0
    elif not transformer.did_anything:
        msg = 'no anchor coords to convert'
        save = 0
    elif not save:
        msg = '%d anchor coords need conversion' % \
              transformer.did_anything
    else:
        msg = '%d anchor coords converted'%transformer.did_anything

    print '%s: %s'%(input, msg)
    if save:
        os.rename(input, input+'~')
        fp = open(input, 'w')
        writer = XmlWriter(fp)
        writer.write(document)

def getargs(argv):
    inputs = []
    save = 0
    try:
        optlist, inputs = getopt.getopt(argv[1:], 'w')
    except getopt.error, arg:
        print "Error:", arg
        usage(argv[0])
        sys.exit(1)
    for option, value in optlist:
        if option == '-w':
            save=1
    return inputs, save

def usage(prog):
    print "Usage: %s [options] input ..."%prog
    print "  -w  Convert file (in place) if needed"

if __name__ == '__main__':
    main()
