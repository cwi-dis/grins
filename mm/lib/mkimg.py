__version__ = "$Id$"

import sys, os, img, imgformat, getopt, struct, string, pprint

bigendian = struct.pack('i', 1)[0] == '\0'

def mkimg(file, format):
    try:
        rdr = img.reader(format, file)
    except:
        print 'error opening image file',file
        return

    # figure out the name of the format
    for fmt in dir(imgformat):
        if getattr(imgformat, fmt) is rdr.format:
            break
    else:
        print 'internal error: unknown format'
        sys.exit(1)

    descr = rdr.format.descr
    byteorder = 0                   # whether we deal with byte order
    if descr['size'] > 8:
        byteorder = 1
        # must deal with little-endian / big-endian difference
        comp = descr['comp']
        for c in comp:
            if c[0] % 8 != 0 or c[1] != 8:
                print 'format must use whole-byte pixels/colors'
                sys.exit(1)
        size = descr['size']
        align = descr['align']
        for altname in dir(imgformat):
            altfmt = getattr(imgformat, altname)
            if type(altfmt) is not type(rdr.format):
                continue
            descr1 = altfmt.descr
            if descr1['size'] != size or \
               descr1['align'] != align or \
               len(descr1['comp']) != len(comp):
                continue
            comp1 = descr1['comp']
            for i in range(len(comp)):
                if comp1[i][0] != size - comp[i][1] - comp[i][0]:
                    break
            else:
                # success
                break
        else:
            print 'cannot find format for other byte order'
            sys.exit(1)

    f = open(os.path.splitext(os.path.basename(file))[0] + '.py', 'w')
    f.write('''\
__version__ = "$''' 'Id' '''$"
''')
    if byteorder:
        f.write('''\
import struct

_bigendian = struct.pack('i', 1)[0] == '\\0'
''')
    f.write('''
class reader:
    def __init__(self):
            self.width = %(width)d
            self.height = %(height)d
            import imgformat
''' % {'width': rdr.width, 'height': rdr.height})
    if byteorder:
        f.write('''\
        if _bigendian == %(bigendian)d:
                format = imgformat.%(format)s
        else:
                format = imgformat.%(altformat)s
''' % {'bigendian': bigendian, 'format': fmt, 'altformat': altname})
    else:
        f.write('''\
        format = imgformat.%s
''' % fmt)
    f.write('''\
            self.format = format
            self.format_choices = (format,)
''')
    if hasattr(rdr, 'colormap'):
        colormaple = []
        colormapbe = []
        colormap = rdr.colormap.getmapdata()
        f.write('\t\timport imgcolormap\n')
        f.write('\t\tself.colormap = imgcolormap.colormap(')
        pprint.pprint(colormap, f)
        f.write(')\n')
    if hasattr(rdr, 'transparent'):
        f.write('\t\tself.transparent = %d\n' % rdr.transparent)
    if hasattr(rdr, 'top'):
        f.write('\t\tself.top = %d\n' % rdr.top)
    if hasattr(rdr, 'left'):
        f.write('\t\tself.left = %d\n' % rdr.left)
    if hasattr(rdr, 'aspect'):
        f.write('\t\tself.aspect = %d\n' % rdr.aspect)
    if hasattr(rdr, 'name'):
        f.write('\t\tself.name = ')
        writedata(f.write, rdr.name)
        f.write('\n')
    f.write('\n\tdef read(self):\n')
    f.write('\t\treturn ')
    writedata(f.write, rdr.read())
    f.write('\n')

def writedata(fwrite, data):
    fwrite("'''\\\n")
    n = 0
    for i in xrange(len(data)):
        c = data[i]
        if c >= '\200':
            c = '\\%03o' % ord(c)
        elif c == "'":
            c = "\\'"
        elif c == '\\':
            c = '\\\\'
        elif c >= ' ':
            c = c
        elif c == '\n':
            c = '\\n'
        elif c == '\f':
            c = '\\f'
        elif c == '\b':
            c = '\\b'
        elif c == '\t':
            c = '\\t'
        elif c == '\r':
            c = '\\r'
        else:
            nc = data[i+1:i+2]
            if '0' <= nc <= '7':
                c = '\\%03o' % ord(c)
            else:
                c = '\\%o' % ord(c)
        fwrite(c)
        n = n + len(c)
        if n >= 72:
            fwrite('\\\n')
            n = 0
    fwrite("'''")

def main():
    if len(sys.argv) < 2:
        print 'Usage:',sys.argv[0] or 'python mkimg.py','img-file ...'
        sys.exit(1)

    opts, args = getopt.getopt(sys.argv[1:], 'f:')
    format = None                   # native format is default
    for o, a in opts:
        if o == '-f':
            if not hasattr(imgformat, a):
                print 'unknown format',a
                sys.exit(1)
            format = getattr(imgformat, a)
            if type(format) is not type(imgformat.rgb):
                print 'unknown format',a
                sys.exit(1)

    for file in args:
        mkimg(file, format)

if __name__ == '__main__':
    main()
