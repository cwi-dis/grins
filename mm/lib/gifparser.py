__version__ = "$Id$"

import struct

# partial GIF file parser
# the purpose of this function is merely to find out whether a GIF
# file is animated
def isanimatedgif(file):
    header = file.read(6)
    if header != 'GIF87a' and header != 'GIF89a':
        return 0
    width,height,flag,bgcolor,aspect = struct.unpack('<hhbbb', file.read(7))
    if flag & 0x80:
        cmapsize = 1 << ((flag & 0x7) + 1)
        cmap = file.read(3*cmapsize)
    else:
        cmap = None
    nimages = 0
    while 1:
        x = ord(file.read(1))
        if x == 0x2C:           # Image Descriptor
            if nimages > 0:
                return 1
            nimages = nimages + 1
            left,top,width,height,flag = struct.unpack('<hhhhb', file.read(9))
            if flag & 0x80:
                lmapsize = 1 << ((flag & 0x7) + 1)
                lmap = file.read(3*lmapsize)
            else:
                lmap = None
            csize = ord(file.read(1))
            while 1:
                size = ord(file.read(1))
                if size == 0:
                    break
                data = file.read(size)
        elif x == 0x21:         # Extension
            y = ord(file.read(1))
            if y == 0xF9:   # Graphic Control Extension
                bsize,flag,delay,transparent,term = struct.unpack('<bbhbb', file.read(6))
##                 if delay != 0:
##                     return 1
            elif y == 0xFE: # Comment Extension
                while 1:
                    size = ord(file.read(1))
                    if size == 0:
                        break
                    data = file.read(size)
            elif y == 0x01: # Plain Text Extension
                size,gleft,gtop,gwidth,gheight,cwidth,cheight,fg,bg = struct.unpack('<bhhhhbbbb', file.read(13))
                while 1:
                    size = ord(file.read(1))
                    if size == 0:
                        break
                    data = file.read(size)
            elif y == 0xFF:
                size = ord(file.read(1))
                data = file.read(size)
                while 1:
                    size = ord(file.read(1))
                    if size == 0:
                        break
                    data = file.read(size)
        elif x == 0x3B:         # Trailer
            return 0
