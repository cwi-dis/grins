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
import getopt


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

    def do_ANY(self, node):
        # Grmpf, SMIL uses non-identifier tags.
        if node.tagName == 'root-layout':
            # G2 uses black default background, GRiNS white.
            if not node.attributes.has_key('background-color'):
                node.attributes['background-color'] = '#ffffff'
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
            newattrs.append((attr, value))
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
        new = cache.newfilename('immdata', None,
                                self.DEFAULT_MEDIA_TYPES[type])
        fp = cache.createurlfile(new)
        fp.write(urllib.urlopen(url).read())
        fp.close()
        return new

    def convert_unknown(self, url):
        print 'UNKNOWN:', url
        print
        return None

class G2UserConverter(DataConverter):
    DESCR="user (human-readable instructions on stdout)"

    def userconvert(self, url, filebase, ext):
        new = cache.exists(url)
        if new:
            print "   DONE:", url
            print
            return new
        new = cache.newfilename(url, filebase, ext)
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
    def __init__(self, fp, output):
        self.fp = fp
        self.out_comment("")
        self.out_comment("Media conversions for %s"%output)
        self.out_comment("")

    def filenames(self, url, filebase, ext):
        new = cache.exists(url)
        if new:
            self.out_comment("Used earlier: %s"%new)
            return None, None, new
        new = cache.newfilename(url, filebase, ext)
        old_pathname = self.url2pathname(url)
        if not old_pathname or not os.path.exists(old_pathname):
            self.out_comment("Not found: %s"% url)
            self.out_comment("You should do the conversion to %s"
                             % new)
        new_pathname = self.url2pathname(new)
        if os.path.exists(new_pathname):
            oldtime = os.stat(old_pathname)[8]
            newtime = os.stat(new_pathname)[8]
            if newtime > oldtime:
                self.out_comment("Appears up-to-date: %s"
                                 % new)
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
        self.out_comment("Appears G2-compatible: %s"%url)
        return 1

    def convert_image(self, url, filebase, ext):
        old, new, newurl = self.filenames(url, filebase, ext)
        if old and new:
            self.out_image(old, new)
        return newurl

    def convert_av(self, url, filebase, ext):
        old, new, newurl = self.filenames(url, filebase, ext)
        if old and new:
            self.out_av(old, new)
        return newurl

    def convert_text(self, url, filebase, ext):
        old, new, newurl = self.filenames(url, filebase, ext)
        if old and new:
            self.out_comment("Manually convert %s"%old)
            self.out_comment("to %s"%new)
        return newurl

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

class G2UnixBatchConverter(G2BatchConverter):
    DESCR="posix (Unix shell script)"

    def out_comment(self, comment):
        self.fp.write("# %s\n"%comment)

    def out_image(self, old, new):
        self.fp.write('echo %s:\n'%old)
        self.fp.write('cjpeg -restart 1B %s > %s\n' % (old, new))

    def out_av(self, old, new):
        self.fp.write('echo %s:\n'%old)
        self.fp.write('rmenc -I %s -O %s\n' % (old, new))

class G2WindowsBatchConverter(G2BatchConverter):
    DESCR="nt (Windows NT/95/98 .BAT file)"

    def out_comment(self, comment):
        self.fp.write("rem %s\n"%comment)

    def out_image(self, old, new):
        self.fp.write('cjpeg -restart 1B "%s" > "%s"\n' % (old, new))

    def out_av(self, old, new):
        self.fp.write('rmenc -I "%s" -O "%s"\n' % (old, new))

class G2MacBatchConverter(G2BatchConverter):
    DESCR="mac (Macintosh AppleScript file)"

    def out_comment(self, comment):
        if comment:
            self.fp.write("(* %s *)"%comment)
        self.fp.write('\n')

    def out_image(self, old, new):
        if not os.path.isabs(old):
            old = os.path.join(os.getcwd(), old)
        if not os.path.isabs(new):
            new = os.path.join(os.getcwd(), new)
        self.fp.write('tell application "JPEGView"\n')
        self.fp.write('    open "%s"\n'%old)
        self.fp.write('    save as JFIF in "%s"\n'%new)
        self.fp.write('    quit\n')
        self.fp.write('end tell\n')

    def out_av(self, old, new):
        if not os.path.isabs(old):
            old = os.path.join(os.getcwd(), old)
        if not os.path.isabs(new):
            new = os.path.join(os.getcwd(), new)
        self.fp.write('tell application "RVBatch"\n')
        self.fp.write('    with timeout of 99999 seconds\n')
        self.fp.write('        encode file "%s" \302\n'%old)
        self.fp.write('            audio true  \302\n')
        self.fp.write('            output as "%s"\n'%new)
        self.fp.write('    end timeout\n')
        self.fp.write('    quit\n')
        self.fp.write('end tell\n')

ALL_BATCH_CONVERTERS={
        'posix': G2UnixBatchConverter,
        'nt': G2WindowsBatchConverter,
        'mac': G2MacBatchConverter,
        'user': G2UserConverter,
}

BatchConverter = G2UserConverter
try:
    BatchConverter = ALL_BATCH_CONVERTERS[os.name]
except KeyError:
    pass

class FileCache:
    def __init__(self):
        self.old_to_new = {}
        self.used = {}

    def exists(self, oldurl):
        if self.old_to_new.has_key(oldurl):
            return self.old_to_new[oldurl]
        return None

    def newfilename(self, old, filebase, ext):
        newurl = 'g2cdata/%s%s'%(filebase, ext)
        if self.used.has_key(newurl):
            num = 1
            while 1:
                # XXXX This is not correct for all cases:
                # it may create duplicates on a second run.
                newurl = 'g2cdata/%s%03d%s'%(filebase, num, ext)
                if not self.used.has_key(newurl):
                    path = urllib.url2pathname(newurl)
                    dir, dummy = os.path.split(path)
                    if not os.path.exists(dir):
                        break
                    if not os.path.exists(path):
                        break
                num = num + 1
        self.used[newurl] = 1
        if old:
            self.old_to_new[old] = newurl
        return newurl

    def createurlfile(self, url):
        filename = urllib.url2pathname(url)
        dirname = os.path.split(filename)[0]
        if dirname and not os.path.exists(dirname):
            os.makedirs(dirname)
        return open(filename, 'w')

cache = FileCache()

def main():
    inputs, output, commands, ramprefix, switched = getargs(sys.argv)
    if commands:
        cfp = open(commands, 'w')
        if os.name == 'mac':
            import MacOS
            MacOS.SetCreatorAndType(commands, 'ToyS', 'TEXT')
    else:
        cfp = None
    for iname in inputs:
        if output:
            oname = output
        else:
            dirname, filename = os.path.split(iname)
            filename = 'g2_' + filename
            oname = os.path.join(dirname, filename)
        process(iname, oname, cfp, ramprefix, switched)
    cfp.close()
    if os.name == 'mac':
        sys.exit(1)             # So user can see the output

def process(input, output, script, ramprefix, switched):
    print '%s:'%input
    data = open(input).read()

    parser = DcBuilder()
    parser.feed(data)

    if script:
        converter = BatchConverter(script, output)
    else:
        converter = G2UserConverter()
    if switched:
        transformer = G2SwitchTransformer(converter)
    else:
        transformer = G2OnlyTransformer(converter)

    document = transformer.transform(parser.document)

    outfile = open(output, 'w')
    if os.name == 'mac':
        import MacOS
        MacOS.SetCreatorAndType(output, 'PNst', 'TEXT') # This is a guess...
    writer = XmlWriter(outfile)
    writer.write(document)
    if ramprefix:
        basename, dummy = os.path.splitext(output)
        ramname = basename + '.ram'
        if ramprefix[-1] != '/':
            ramprefix = ramprefix + '/'
        url = urllib.basejoin(ramprefix, output)
        fp = open(ramname, 'w')
        if os.name == 'mac':
            import MacOS
            MacOS.SetCreatorAndType(ramname, 'PNst', 'PNRM')
        fp.write(url+'\n')
        fp.close()

def unix_getargs(argv):
    global BatchConverter
    inputs = []
    output = None
    commands = None
    ramprefix = None
    switched = 0
    try:
        optlist, inputs = getopt.getopt(argv[1:], '?o:c:b:r:s',
                 ['help', 'output=', 'commands=',
                  'batchtype=', 'ramprefix=', 'switch'])
    except getopt.error, arg:
        print "Error:", arg
        usage(argv[0])
        sys.exit(1)
    for option, value in optlist:
        if option in ('-?', '--help'):
            usage(argv[0])
            sys.exit(0)
        if option in ('-o', '--output'):
            output = value
        elif option in ('-c', '--commands'):
            commands = value
        elif option in ('-r', '--ramprefix'):
            ramprefix = value
        elif option in ('-s', '--switch'):
            switched = 1
        elif option in ('-b', '--batchtype'):
            if ALL_BATCH_CONVERTERS.has_key(value):
                BatchConverter = ALL_BATCH_CONVERTERS[value]
            else:
                print "Unknown batchfile type"
                usage(argv[0])
                sys.exit(1)
    if output and len(inputs) > 1:
        print "Output file cannot be set for multiple input files"
        usage(argv[0])
        sys.exit(1)
    if not inputs:
        print "No input files specified"
        usage(argv[0])
        sys.exit(1)
    for inp in inputs:
        if os.path.split(inp)[0]:
            print "Sorry, can only convert in current directory"
            usage(argv[0])
            sys.exit(1)
    return inputs, output, commands, ramprefix, switched

def usage(prog):
    print "Usage: %s [options] input ..."%prog
    print "  --output file   Send output here. Default: input file name"
    print "   (or -o file)   with g2_ prepended."
    print "  --commands file Create script with media conversion commands"
    print "   (or -c file)   Default: explain conversions required on"
    print "                  stdout. Note that the script may need some"
    print "                  editing."
    print "  --switch        Create an output file that is G2-playable as"
    print "   (or -s)        well as GRiNS-playable. Default is G2-only."
    print "                  Note that this may not work for older G2"
    print "                  players (November 1998)."
    print " --batchtype type Type of batchfile to create with -c. Default:"
    print "   (or -b type)   %s"%BatchConverter.DESCR
    print "                  Supported values: ", string.join(
            ALL_BATCH_CONVERTERS.keys())
    print " --ramprefix url  Generate a .ram file pointing to the new"
    print "   (or -r url)    document. The url is how we should refer to"
    print "                  the current directory (i.e. this is prepended"
    print "                  to the filename of the converted document"

def mac_getargs(args):
    inputs = []
    output = None
    commands = None
    ramprefix = None
    switched = 0

    import macfs
    import EasyDialogs
    if args[1:]:
        inputs = args[1:]
    else:
        fss, ok = macfs.StandardGetFile()
        if not ok:
            sys.exit(0)
        inputs = [fss.as_pathname()]
    dir = os.path.split(inputs[0])[0]
    os.chdir(dir)
    for i in range(len(inputs)):
        filename = inputs[i]
        if filename[:len(dir)] == dir:
            inputs[i] = filename[len(dir):]
    if len(inputs) == 1:
        dft = 'g2_' + inputs[0][1:]
        fss, ok = macfs.StandardPutFile("G2 output file", dft)
        if not ok:
            sys.exit(0)
        output = fss.as_pathname()
    fss, ok = macfs.StandardPutFile("Script output (cancel for text)", "Conversion script")
    if ok:
        commands = fss.as_pathname()
    reply = EasyDialogs.AskString("URL prefix for use in .ram file (cancel for no ram file)")
    if reply:
        ramprefix = reply
    reply = EasyDialogs.AskYesNoCancel("Create G2/GRiNS switch statements?")
    if reply > 0:
        switched = 1
    return inputs, output, commands, ramprefix, switched



if os.name == 'mac':
    getargs = mac_getargs
else:
    getargs = unix_getargs

if __name__ == '__main__':
    main()
