/***********************************************************
Copyright 1991, 1992, 1993, 1994 by Stichting Mathematisch Centrum,
Amsterdam, The Netherlands.

                        All Rights Reserved

Permission to use, copy, modify, and distribute this software and its 
documentation for any purpose and without fee is hereby granted, 
provided that the above copyright notice appear in all copies and that
both that copyright notice and this permission notice appear in 
supporting documentation, and that the names of Stichting Mathematisch
Centrum or CWI not be used in advertising or publicity pertaining to
distribution of the software without specific, written prior permission.

STICHTING MATHEMATISCH CENTRUM DISCLAIMS ALL WARRANTIES WITH REGARD TO
THIS SOFTWARE, INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY AND
FITNESS, IN NO EVENT SHALL STICHTING MATHEMATISCH CENTRUM BE LIABLE
FOR ANY SPECIAL, INDIRECT OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT
OF OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.

******************************************************************/
/*
** GIF file handling. Jack Jansen, CWI, June 1994.
**
** Part of this code was taken from giftopnm.c and ppmtogif.c,
** of which the copyright notices are below.
**
** giftopnm:
** +-------------------------------------------------------------------+
** | Copyright 1990, 1991, 1993, David Koblas.  (koblas@netcom.com)    |
** |   Permission to use, copy, modify, and distribute this software   |
** |   and its documentation for any purpose and without fee is hereby |
** |   granted, provided that the above copyright notice appear in all |
** |   copies and that both that copyright notice and this permission  |
** |   notice appear in supporting documentation.  This software is    |
** |   provided "as is" without express or implied warranty.           |
** +-------------------------------------------------------------------+
**
** ppmtogif:
** Based on GIFENCOD by David Rowley <mgardi@watdscu.waterloo.edu>.A
** Lempel-Zim compression based on "compress".
**
** Modified by Marcel Wijkstra <wijkstra@fwi.uva.nl>
**
**
** Copyright (C) 1989 by Jef Poskanzer.
**
** Permission to use, copy, modify, and distribute this software and its
** documentation for any purpose and without fee is hereby granted, provided
** that the above copyright notice appear in all copies and that both that
** copyright notice and this permission notice appear in supporting
** documentation.  This software is provided "as is" without express or
** implied warranty.
**
** The Graphics Interchange Format(c) is the Copyright property of
** CompuServe Incorporated.  GIF(sm) is a Service Mark property of
** CompuServe Incorporated.
*/


/* Gif objects */

#include "Python.h"
#ifdef macintosh
#include "macglue.h"
#endif

/* XXXX change this to the image formats we support */

static PyObject *format_map, *format_map_b2t, *format_choices, *format_xmap;
extern PyObject *getimgformat();		/* Get format by name */
static PyObject *(*makecolormap)();	/* Routine to make a colormap */

typedef struct {
	PyObject_HEAD
	PyObject	*dict;		/* Attributes dictionary */
	PyObject	*fileobj;	/* The Python file object */
	int	is_reader;	/* TRUE if this is a reader */
	char	*filename;	/* filename of the image file */
	FILE	*filep;
	int	interlaced;	/* TRUE if image is interlaced (for read) */
} gifobject;

typedef struct {
    unsigned char	*data;
    int		xpos, ypos, width, height, rowlen;
} GIFwriterdata;

static PyObject *errobject;

staticforward PyTypeObject Giftype;

staticforward int GIFreadheader();	/* Read everything but the data */
staticforward long *GIFreadmap();	/* Read a colormap */
staticforward int GIFskipblock();	/* Skip an extension block */
staticforward int GIFgettransparent();	/* Get transparent extension block */
staticforward int GIFreadimage();	/* Read the image data */
staticforward void GIFcompress();	/* Write and compress */
staticforward void GIFcompress_reinit();/* re-init compress data */
					/* structures */

/*
** NOTE: The GIF LWZ decompression routines are not safe in parallel
** programs. They use the ZeroDataBlock variable below to pass a flag around,
** and use statically allocated tables besides.
*/
#define MAX_LWZ_BITS 12
int ZeroDataBlock = 0;

#define is_gifobject(v)		((v)->ob_type == &Giftype)

static char doc_pgm[] = "This object reads/writes PGM files\n"
	"The 'width', 'height', 'top', 'left', 'aspect' and 'format'\n"
	"attributes describe the picture,\n"
	"'colormap' has the colormap object for the picture\n"
	"There may be a 'transparent' attribute given in index of the color\n"
	"to be treated as transparent.";

/* Routine to easily obtain C data from the dict python data */
int
gifselfattr( gifobject *self, char *name, char *fmt, void *ptr, int wanterr)
{
    PyObject *obj;
    char errbuf[100];

    obj = PyDict_GetItemString(self->dict, name);
    if ( obj == NULL ) {
	if ( wanterr ) {
	    sprintf(errbuf, "Required attribute '%s' not set", name);
	    PyErr_SetString(errobject, errbuf);
	    return 0;
	} else {
	    PyErr_Clear();
	    return 0;
	}
    }
    if ( !PyArg_Parse(obj, fmt, ptr) ) {
	if ( !wanterr )
	    PyErr_Clear();
	return 0;
    }
    return 1;
}

/* Routine to easily insert integer into dictionary */
gifsetintattr(gifobject *self, char *name, int value)
{
    PyObject *obj;
    int rv;

    obj = PyInt_FromLong(value);
    rv = PyDict_SetItemString(self->dict, name, obj);
    Py_DECREF(obj);
    return rv;
}

static gifobject *
newgifobject()
{
	gifobject *xp;
	xp = PyObject_NEW(gifobject, &Giftype);
	if (xp == NULL)
		return NULL;
	xp->dict = PyDict_New();
	xp->filename = NULL;
	xp->fileobj = NULL;
	/* XXXX Initialize other pointers here as well */
	return xp;
}

static int
initgifreader(gifobject *self, char *name, FILE *filep)
{
    char *name_copy;

    if( (name_copy=malloc(strlen(name)+1)) == NULL ) {
	PyErr_NoMemory();
	return 0;
    }
    strcpy(name_copy, name);
    self->filename = name_copy;
    self->is_reader = 1;
    if ( filep == 0 ) {
	if ((self->filep = fopen(self->filename, "rb")) == NULL) {
	    PyErr_SetFromErrno(PyExc_IOError);
	    return 0;
	}
    } else {
    	self->filep = filep;
    }
	   
    if ( !GIFreadheader(self) )
	return 0;
    /* XXXX Open image file, read header, put into dict: */
    PyDict_SetItemString(self->dict, "format", format_map);
    PyDict_SetItemString(self->dict, "format_choices", format_choices);
    if( PyErr_Occurred() )
	return 0;
    return 1;
}

static int
GIFreadheader(gifobject *self)
{
    char buf[6];
    int left, top, width, height, bpp, ncolors, hasmap, bgnd, aspect;
    int ch;
    int atimagestart;
    long *gmap = NULL, *lmap = NULL;
    PyObject *mapobj = NULL;
    unsigned char etype;
    int transparent = -1;

    /*
    ** The GIF header looks as follows:
    ** 0-5	"magic number", 'GIF87a' or 'GIF89a'
    ** 6,7	width (little-endian)
    ** 8,9	height
    ** 10       bitsperpixel, colormapflag, interlaceflag
    ** 11	ignored (background color)
    ** 12	aspect ratio
    ** Then a colormap (3 bytes per entry)
    ** Then a number of 'blocks'.
    ** Each block is either an extension (which we ignore) or an image.
    ** An image consists of
    **   0,1	left
    **	 2,3	top
    **   4,5	width
    **   6,7	height
    **   8	flag (like in file header)
    **   And then the LZW image data.
    **
    ** There may be more images in the file, but we ignore all but the
    ** first. Actually, we don't read on after the first image.
    */
    if ( fread(buf, 1, 6, self->filep) != 6 ) goto EndOfFile;
    if ( strncmp(buf, "GIF87a", 6) != 0 &&
	 strncmp(buf, "GIF89a", 6) != 0 ) {
	PyErr_SetString(errobject, "Not a GIF87 or GIF89 file");
	return 0;
    }
    /* We don't check for EOF each time, only when we start using data */
    ch = getc(self->filep);
    width = ch + (getc(self->filep) << 8);
    ch = getc(self->filep);
    height = ch + (getc(self->filep) << 8);
    ch = getc(self->filep);
    hasmap = (ch & 0x80);
    bpp = (ch & 7) + 1;
    ncolors = 1 << bpp;
    bgnd = getc(self->filep);
    aspect = getc(self->filep);
    if ( feof(self->filep) || ferror(self->filep) ) goto EndOfFile;

    if ( hasmap ) {
	if( (gmap = GIFreadmap(self, ncolors)) == NULL )
	    goto ErrorExit;
    }
    if ( feof(self->filep) || ferror(self->filep) ) goto EndOfFile;


    atimagestart = 0;
    do {
	if( (ch = getc(self->filep)) == EOF ) goto EndOfFile;
	switch(ch) {
	case ';':	/* Terminator */
	    PyErr_SetString(errobject, "No image found in file");
	    return 0;

	case '!':	/* Extension */
	    etype = (unsigned char)getc(self->filep);	/* Extension type */
	    if ( etype == 0xf9 )	/* Transparent extension */
		transparent = GIFgettransparent(self);
	    while( GIFskipblock(self) ) ;
	    break;

	case ',':
	    atimagestart = 1;
	    break;
	}
    } while ( !atimagestart );

    ch = getc(self->filep);
    left = ch + (getc(self->filep) << 8);
    ch = getc(self->filep);
    top = ch + (getc(self->filep) << 8);
    ch = getc(self->filep);
    width = ch + (getc(self->filep) << 8);
    ch = getc(self->filep);
    height = ch + (getc(self->filep) << 8);
    ch = getc(self->filep);
    hasmap = (ch & 0x80);
    self->interlaced = (ch & 0x40);
    if ( hasmap ) { /* Otherwise use values from header */
	bpp = (ch & 7) + 1;
	ncolors = 1 << bpp;
    }
    if ( feof(self->filep) || ferror(self->filep) ) goto EndOfFile;

    if ( hasmap ) {
	if( (lmap = GIFreadmap(self, ncolors)) == NULL )
	    goto ErrorExit;
    }
    if ( feof(self->filep) || ferror(self->filep) ) goto EndOfFile;

    gifsetintattr(self, "width", width);
    gifsetintattr(self, "height", height);
    gifsetintattr(self, "top", top);
    gifsetintattr(self, "left", left);
    gifsetintattr(self, "aspect", aspect);
    if ( transparent > 0 )
	gifsetintattr(self, "transparent", transparent);
    if ( PyErr_Occurred() ) {
	fprintf(stderr, "imggif: unexpected error\n");
	goto ErrorExit;
    }
    if ( lmap ) {
	if ( (mapobj=makecolormap(lmap, ncolors)) == NULL )
	    goto ErrorExit;
    } else if ( gmap ) {
	if ( (mapobj=makecolormap(gmap, ncolors)) == NULL )
	    goto ErrorExit;
    }
    if ( mapobj )
	PyDict_SetItemString(self->dict, "colormap", mapobj);

    if ( lmap )
	free(lmap);
    if ( gmap )
	free(gmap);
    return 1;
    /*
    ** Yes! Labels!
    */
 EndOfFile:
    PyErr_SetString(errobject, "Truncated GIF file");
 ErrorExit:
    if ( lmap )
	free(lmap);
    if ( gmap )
	free(gmap);
    return 0;
}

static long *
GIFreadmap(gifobject *self, int ncolors)
{
    long *map;
    int r, g, b, i;

    if ( (map=(long *)malloc(ncolors*sizeof(long))) == NULL ) {
	PyErr_NoMemory();
	return NULL;
    }
    for(i=0; i<ncolors; i++) {
	r = fgetc(self->filep);
	g = fgetc(self->filep);
	b = fgetc(self->filep);
	map[i] = r | (g<<8) | (b<<16);
    }
    if ( feof(self->filep) || ferror(self->filep) ) {
	PyErr_SetString(errobject, "Truncated GIF file");
	free(map);
	return NULL;
    }
    return map;
}

static int
GIFskipblock(gifobject *self)
{
    int i, count;

    if ( (count=fgetc(self->filep)) == EOF )
	return 0;
    for(i=0; i<count; i++)
	(void)fgetc(self->filep);
    return count;
}

static int
GIFgettransparent(gifobject *self)
{
    int count;
    unsigned char value;

    if ( (count=fgetc(self->filep)) == EOF || count != 4 )
	return -1;
    (void)fgetc(self->filep);
    (void)fgetc(self->filep);
    (void)fgetc(self->filep);
    value = (unsigned char)fgetc(self->filep);
    return value;
}

static int
initgifwriter(gifobject *self, char *name, FILE *filep)
{
    char *name_copy;

    if( (name_copy=malloc(strlen(name)+1)) == NULL ) {
	PyErr_NoMemory();
	return 0;
    }
    strcpy(name_copy, name);
    self->filename = name_copy;
    self->is_reader = 0;
    PyDict_SetItemString(self->dict, "format", format_map);
    PyDict_SetItemString(self->dict, "format_choices", format_choices);
    self->filep = filep;
    if( PyErr_Occurred())
	return 0;
    return 1;
}

/* Gif methods */

static void
gif_dealloc(gifobject *xp)
{
	Py_XDECREF(xp->dict);
	Py_XDECREF(xp->fileobj);
	if( xp->filename )
	    free(xp->filename);
	if( xp->filep )
	    fclose(xp->filep);
	PyMem_DEL(xp);
}

static char doc_read[] = "Read the actual data, returns a string";

static PyObject *
gif_read(gifobject *self, PyObject *args)
{
    PyObject *fmt;
	PyObject *rv;
	unsigned char *datap;
	int b2t;
	int width, height, rowlen;
	
	if (!PyArg_ParseTuple(args,""))
		return NULL;
	if (!self->is_reader) {
	    PyErr_SetString(errobject, "Cannot read() from writer object");
	    return NULL;
	}
	/* XXXX Get format (and other args), check, read data, return it */
	if ( !gifselfattr(self, "format", "O", &fmt, 1) ||
	     !gifselfattr(self, "width", "i", &width, 1) ||
	     !gifselfattr(self, "height", "i", &height, 1) )
	    return NULL;

	if ( fmt == format_map || fmt == format_xmap ) {
	    b2t = 0;
	} else if ( fmt == format_map_b2t ) {
	    b2t = 1;
	} else {
	    PyErr_SetString(errobject, "Unsupported image format");
	    return NULL;
	}

	if ( fmt == format_xmap )
	    rowlen = width;
	else
	    rowlen = (width+3) & ~3;	/* SGI images 32bit aligned */
	if( (rv=PyString_FromStringAndSize(NULL, rowlen*height)) == NULL )
	    return NULL;
	datap = (unsigned char *)PyString_AsString(rv);
	if ( b2t ) {
	    datap = datap + rowlen*(height-1);
	    rowlen = -rowlen;
	}

	if (GIFreadimage(self, datap, width, height, rowlen,
			 self->interlaced) == 0) {
	    Py_DECREF(rv);
	    return NULL;
	}
	return rv;
}

/*
** LWZ reader routines stolen from giftopnm.c
*/

static int
LWZGetDataBlock(fd, buf)
FILE           *fd;
unsigned char  *buf;
{
       unsigned char   count;

       if ( feof(fd) ) goto EndOfFile;
       count=(unsigned char)fgetc(fd);

       ZeroDataBlock = count == 0;

       if ((count != 0) && (fread(buf, 1, count, fd) != count))
	   goto EndOfFile;

       return count;
   EndOfFile:
       PyErr_SetString(errobject, "Truncated GIF file");
       return -1;
}

static int
LWZGetCode(FILE   *fd, int    code_size, int    flag)
{
       static unsigned char    buf[280];
       static int              curbit, lastbit, done, last_byte;
       int                     i, j, ret;
       int                     count;

       if (flag) {
               curbit = 0;
               lastbit = 0;
               done = 0;
               return 0;
       }

       if ( (curbit+code_size) >= lastbit) {
               if (done) {
                       if (curbit >= lastbit)
                               PyErr_SetString(errobject,
					  "ran off the end of my bits" );
                       return -1;
               }
               buf[0] = buf[last_byte-2];
               buf[1] = buf[last_byte-1];

               if ((count = LWZGetDataBlock(fd, &buf[2])) == 0)
                       done = 1;
	       if ( count < 0 ) return -1;

               last_byte = 2 + (unsigned char)count;
               curbit = (curbit - lastbit) + 16;
               lastbit = (2+(unsigned char)count)*8 ;
       }

       ret = 0;
       for (i = curbit, j = 0; j < code_size; ++i, ++j)
               ret |= ((buf[ i / 8 ] & (1 << (i % 8))) != 0) << j;

       curbit += code_size;

       return ret;
}

static int
LWZReadByte(FILE   *fd, int    flag, int    input_code_size)
{
       static int      fresh = 0;
       int             code, incode;
       static int      code_size, set_code_size;
       static int      max_code, max_code_size;
       static int      firstcode, oldcode;
       static int      clear_code, end_code;
       static int      table[2][(1<< MAX_LWZ_BITS)];
       static int      stack[(1<<(MAX_LWZ_BITS))*2], *sp;
       register int    i;

       if (flag) {
               set_code_size = input_code_size;
               code_size = set_code_size+1;
               clear_code = 1 << set_code_size ;
               end_code = clear_code + 1;
               max_code_size = 2*clear_code;
               max_code = clear_code+2;

               if ( LWZGetCode(fd, 0, 1) < 0 )
		   return -1;
               
               fresh = 1;

               for (i = 0; i < clear_code; ++i) {
                       table[0][i] = 0;
                       table[1][i] = i;
               }
               for (; i < (1<<MAX_LWZ_BITS); ++i)
                       table[0][i] = table[1][0] = 0;

               sp = stack;

               return 0;
       } else if (fresh) {
               fresh = 0;
               do {
                       firstcode = oldcode =
                               LWZGetCode(fd, code_size, 0);
		       if ( oldcode < 0 ) return -1;
               } while (firstcode == clear_code);
               return firstcode;
       }

       if (sp > stack)
               return *--sp;

       while ((code = LWZGetCode(fd, code_size, 0)) >= 0) {
               if (code == clear_code) {
                       for (i = 0; i < clear_code; ++i) {
                               table[0][i] = 0;
                               table[1][i] = i;
                       }
                       for (; i < (1<<MAX_LWZ_BITS); ++i)
                               table[0][i] = table[1][i] = 0;
                       code_size = set_code_size+1;
                       max_code_size = 2*clear_code;
                       max_code = clear_code+2;
                       sp = stack;
                       firstcode = oldcode =
                                       LWZGetCode(fd, code_size, 0);
                       return firstcode;
               } else if (code == end_code) {
                       int             count;
                       unsigned char   buf[260];

                       if (ZeroDataBlock)
                               return -2;

                       while ((count = LWZGetDataBlock(fd, buf)) > 0)
                               ;

                       if (count != 0)
                               PyErr_SetString(errobject,
					  "missing EOD in data stream");
                       return -2;
               }

               incode = code;

               if (code >= max_code) {
                       *sp++ = firstcode;
                       code = oldcode;
               }

               while (code >= clear_code) {
                       *sp++ = table[1][code];
                       if (code == table[0][code]) {
                               PyErr_SetString(errobject,
					  "circular table entry BIG ERROR");
			       return -1;
		       }
                       code = table[0][code];
               }

               *sp++ = firstcode = table[1][code];

               if ((code = max_code) <(1<<MAX_LWZ_BITS)) {
                       table[0][code] = oldcode;
                       table[1][code] = firstcode;
                       ++max_code;
                       if ((max_code >= max_code_size) &&
                               (max_code_size < (1<<MAX_LWZ_BITS))) {
                               max_code_size *= 2;
                               ++code_size;
                       }
               }

               oldcode = incode;

               if (sp > stack)
                       return *--sp;
       }
       return code;
}

static int
GIFreadimage(gifobject *self, char *datap, int width, int height, int rowlen, int interlace)
{
    int ch, v, xpos=0, ypos=0, pass=0;

    if ( (ch=getc(self->filep)) == EOF ) {
	PyErr_SetString(errobject, "Truncated GIF file");
	return 0;
    }
    if (LWZReadByte(self->filep, 1, ch) < 0 ) {
	PyErr_SetString(errobject, "Truncated GIF file");
	return 0;
    }
    while ((v=LWZReadByte(self->filep, 0, ch)) >= 0 ) {
	datap[ypos*rowlen+xpos] = v;
	xpos++;
	if ( xpos == width ) {
	    while(xpos < rowlen) {
		datap[ypos*rowlen+xpos] = 0;
		xpos++;
	    }
	    xpos = 0;
	    if( interlace ) {
		switch(pass) {
		case 0:
		case 1:
		    ypos += 8; break;
		case 2:
		    ypos += 4; break;
		case 3:
		    ypos += 2; break;
		}
		
		if (ypos >= height) {
		    pass++;
		    switch (pass) {
		    case 1:
			ypos = 4; break;
		    case 2:
			ypos = 2; break;
		    case 3:
			ypos = 1; break;
		    default:
			return 1; /* all done */
		    }
		}
	    } else {
		ypos++;
	    }
	}
	if (ypos >= height)
	    return 1; /* all done */
    }
    PyErr_SetString(errobject, "Truncated GIF file");
    return 0;
}

static void
GIFputword(int w, FILE* fp)
{
    fputc( w & 0xff, fp );
    fputc( (w>>8) & 0xff, fp );
}

GIFgetcompressbyte(GIFwriterdata *dp)
{
    int rv;
    
    if ( dp->ypos >= dp->height )
	return EOF;
    rv = dp->data[dp->ypos*dp->rowlen + dp->xpos];
    dp->xpos++;
    if ( dp->xpos >= dp->width ) {
	dp->xpos = 0;
	dp->ypos++;
    }
    return rv;
}

static char doc_write[] = "Write (string) data to the GIF file";

static PyObject *
gif_write(gifobject *self, PyObject *args)
{
        char *data;
	int datalen;
	int w, h, rowlen;
	PyObject *fmt, *colormap, *colormapstring;
	long *mapdata;
	GIFwriterdata dstr;
	int i;
	int ch;
	int transparent;
	FILE *filep;
	
	if (!PyArg_ParseTuple(args, "s#", &data, &datalen))
		return NULL;
	if (self->is_reader) {
	    PyErr_SetString(errobject, "Cannot write() to reader object");
	    return NULL;
	}
	/* XXXX Get args from self->dict and write the data */
	if ( !gifselfattr(self, "width", "i", &w, 1) ||
	     !gifselfattr(self, "height", "i", &h, 1) ||
	     !gifselfattr(self, "format", "O", &fmt, 1) ||
	     !gifselfattr(self, "colormap", "O", &colormap, 1) )
	    return NULL;

	if ( fmt == format_xmap )
	    rowlen = w;
	else
	    rowlen = (w+3) & ~3;	/* SGI formats are 32-bit aligned */

	if ( fmt != format_map && fmt != format_xmap &&
	     fmt != format_map_b2t ) {
	    PyErr_SetString(errobject, "Unsupported image format");
	    return NULL;
	}
	if( rowlen*h != datalen ) {
	    PyErr_SetString(errobject, "Incorrect datasize");
	    return NULL;
	}
	
	if ( colormap == Py_None ) {
	    mapdata = NULL;
	    colormapstring = NULL;
	} else {
	    if( (colormapstring=PyObject_GetAttrString(colormap,
					"_map_as_string")) == NULL ) {
		PyErr_SetString(errobject, "'colormap' attribute is no colormap");
		return NULL;
	    }
	    mapdata = (long *)PyString_AsString(colormapstring);
	}
	
	if ( fmt == format_map_b2t ) {
	    data = data + rowlen*(h-1);
	    rowlen = -rowlen;
	}

	/*
	** Open the file.
	*/
	if ( self->filep ) {
	    filep = self->filep;
	} else {
	    if ((filep = fopen(self->filename, "wb")) == NULL) {
	        PyErr_SetFromErrno(PyExc_IOError);
	        Py_XDECREF(colormapstring);
	        return NULL;
	    }
#ifdef macintosh
	    setfiletype(self->filename, '????', 'GIF ');
#endif
	}
	/*
	** Write the header.
	*/
	fwrite("GIF87a", 1, 6, filep);
	GIFputword(w, filep);
	GIFputword(h, filep);
	/* XXXX This might be incorrect */
	ch = 0x67;	/* XXXX Correct? bits per pixel -1 */
	if ( mapdata )
	    ch |= 0x80;
	fputc(ch, filep);
	fputc(0, filep);
	fputc(0, filep);
	if ( mapdata ) {
	    for(i=0; i<256; i++) {
		ch = mapdata[i] & 0xff;
		fputc(ch, filep);
		ch = (mapdata[i]>>8) & 0xff;
		fputc(ch, filep);
		ch = (mapdata[i]>>16) & 0xff;
		fputc(ch, filep);
	    }
	    /* Now we can free the map stuff */
	    Py_DECREF(colormapstring);
	}

	/* Write the (optional) transparency extension */
	if ( gifselfattr(self, "transparent", "i", &transparent, 0) ) {
	    fputc('!', filep);
	    fputc(0xf9, filep);
	    fputc(4, filep);
	    fputc(1, filep);
	    fputc(0, filep);
	    fputc(0, filep);
	    fputc((unsigned char)transparent, filep);
	    fputc(0, filep);
	}
	
	/* Now the image */
	fputc( ',', filep);
	GIFputword(0, filep);
	GIFputword(0, filep);
	GIFputword(w, filep);
	GIFputword(h, filep);
	fputc(0, filep);		/* We don't interlace */
	fputc(8, filep);		/* Initial code size */
	/*
	** Setup struct to pass writer args to compressor
	*/
	dstr.data = (unsigned char *)data;
	dstr.xpos = 0;
	dstr.ypos = 0;
	dstr.width = w;
	dstr.height = h;
	dstr.rowlen = rowlen;
	GIFcompress(9, filep, &dstr);
	fflush(filep);
	if ( ferror(filep) ) {
	    PyErr_SetFromErrno(PyExc_IOError);
	    fclose(filep);
	    return NULL;
	}
	/*
	** Trailer
	*/
	fputc(0, filep);
	fputc(';', filep);
	if (fclose(filep) != 0) {
	    PyErr_SetFromErrno(PyExc_IOError);
	    return NULL;
	}
	Py_INCREF(Py_None);
	return Py_None;
}

static struct PyMethodDef gif_methods[] = {
	{"read",	(PyCFunction)gif_read,	1,	doc_read},
	{"write",	(PyCFunction)gif_write,	1,	doc_write},
	{NULL,		NULL}		/* sentinel */
};

static PyObject *
gif_getattr(gifobject *xp, char *name)
{
        PyObject *v;
	
	if (xp->dict != NULL) {
	        if ( strcmp(name, "__dict__") == 0 ) {
		        Py_INCREF(xp->dict);
			return xp->dict;
		}
       		if ( strcmp(name, "__doc__") == 0 ) {
		        return PyString_FromString(doc_pgm);
		}
		v = PyDict_GetItemString(xp->dict, name);
		if (v != NULL) {
			Py_INCREF(v);
			return v;
		}
	}
	return Py_FindMethod(gif_methods, (PyObject *)xp, name);
}

static int
gif_setattr(gifobject *xp, char *name, PyObject *v)
{
	if (xp->dict == NULL) {
		xp->dict = PyDict_New();
		if (xp->dict == NULL)
			return -1;
	}
	if (v == NULL) {
		int rv = PyDict_DelItemString(xp->dict, name);
		if (rv < 0)
			PyErr_SetString(PyExc_AttributeError,
			        "delete non-existing imggif attribute");
		return rv;
	}
	else
		return PyDict_SetItemString(xp->dict, name, v);
}

static PyTypeObject Giftype = {
	0,//PyObject_HEAD_INIT(&PyType_Type)
	0,			/*ob_size*/
	"imggif",		/*tp_name*/
	sizeof(gifobject),	/*tp_basicsize*/
	0,			/*tp_itemsize*/
	/* methods */
	(destructor)gif_dealloc, /*tp_dealloc*/
	0,			/*tp_print*/
	(getattrfunc)gif_getattr, /*tp_getattr*/
	(setattrfunc)gif_setattr, /*tp_setattr*/
	0,			/*tp_compare*/
	0,			/*tp_repr*/
	0,			/*tp_as_number*/
	0,			/*tp_as_sequence*/
	0,			/*tp_as_mapping*/
	0,			/*tp_hash*/
};

static char doc_newreader[] =
	"Return an object that reads the GIF file passed as argument";

static PyObject *
gif_newreader(PyObject *self, PyObject *args)
{
        char *filename;
	gifobject *obj;
	PyObject *fileobj = NULL;
	FILE *fp = NULL;
	
	if (!PyArg_ParseTuple(args, "s", &filename)) {
	    PyErr_Clear();
	    if (!PyArg_ParseTuple(args, "O!", &PyFile_Type, &fileobj))
	        return NULL;
	    fp = PyFile_AsFile(fileobj);
	    filename = "<open file>";
	}
	if ((obj = newgifobject()) == NULL)
	    return NULL;
	if ( !initgifreader(obj, filename, fp) ) {
	    Py_DECREF(obj);
	    return NULL;
	}
	if (fileobj) {
		Py_INCREF(fileobj);
		obj->fileobj = fileobj;
	}
	return (PyObject *)obj;
}

static char doc_newwriter[] =
	"Return an object that writes the GIF file passed as argument";

static PyObject *
gif_newwriter(PyObject *self, PyObject *args)
{
        char *filename;
	gifobject *obj;
	PyObject *fileobj = NULL;
	FILE *fp = NULL;
	
	if (!PyArg_ParseTuple(args, "s", &filename)) {
	    PyErr_Clear();
	    if (!PyArg_ParseTuple(args, "O!", &PyFile_Type, &fileobj))
	        return NULL;
	    fp = PyFile_AsFile(fileobj);
	    filename = "<open file>";
	}
	if ((obj = newgifobject()) == NULL)
	    return NULL;
	if ( !initgifwriter(obj, filename, fp) ) {
	    Py_DECREF(obj);
	    return NULL;
	}
	if (fileobj) {
		Py_INCREF(fileobj);
		obj->fileobj = fileobj;
	}
	return (PyObject *)obj;
}


/* List of functions defined in the module */

static struct PyMethodDef gif_module_methods[] = {
	{"reader",	gif_newreader,	1,	doc_newreader},
	{"writer",	gif_newwriter,	1,	doc_newwriter},
	{NULL,		NULL}		/* sentinel */
};


/* Initialization function for the module (*must* be called initimggif) */
static char doc_imggif[] =
  "Module that reads and writes images to GIF files";


void
initimggif()
{
	PyObject *m, *d, *formatmodule, *formatdict, *o;

	/* Create the module and add the functions */
	m = Py_InitModule("imggif", gif_module_methods);

	/* Add some symbolic constants to the module */
	d = PyModule_GetDict(m);
	o = PyString_FromString(doc_imggif);
	PyDict_SetItemString(d, "__doc__", o);

	/* Get supported formats */
	if ((formatmodule = PyImport_ImportModule("imgformat")) == NULL)
	    Py_FatalError("imggif depends on imgformat");
	if ((formatdict = PyModule_GetDict(formatmodule)) == NULL)
	    Py_FatalError("imgformat has no dict");
	errobject = PyDict_GetItemString(formatdict,"error");

	format_map = PyDict_GetItemString(formatdict,"colormap");
	format_xmap = PyDict_GetItemString(formatdict,"xcolormap");
	format_map_b2t = PyDict_GetItemString(formatdict,"colormap_b2t");
	format_choices = Py_BuildValue("(OOO)", format_map, format_xmap,
				 format_map_b2t);

	/* Get pointer to colormap-creation routine. NOTE: this is a hack */
	if ((formatmodule = PyImport_ImportModule("imgcolormap")) == NULL)
	    Py_FatalError("imggif depends on imgcolormap");
	if ((formatdict = PyModule_GetDict(formatmodule)) == NULL)
	    Py_FatalError("imgcolormap has no dict");

	o = PyDict_GetItemString(formatdict, "_C_newmap");
	(void)PyArg_Parse(o, "l", (long *)&makecolormap);
	

	/* Check for errors */
	if (PyErr_Occurred())
		Py_FatalError("can't initialize module imggif");
}

/***************************************************************************
 *
 *  GIFCOMPR.C       - GIF Image compression routines
 *
 *  Lempel-Ziv compression based on 'compress'.  GIF modifications by
 *  David Rowley (mgardi@watdcsu.waterloo.edu)
 *
 ***************************************************************************/

/*
 * General DEFINEs
 */

#define BITS    12

#define HSIZE  5003            /* 80% occupancy */

#ifdef NO_UCHAR
 typedef char   char_type;
#else /*NO_UCHAR*/
 typedef        unsigned char   char_type;
#endif /*NO_UCHAR*/

/*
 *
 * GIF Image compression - modified 'compress'
 *
 * Based on: compress.c - File compression ala IEEE Computer, June 1984.
 *
 * By Authors:  Spencer W. Thomas       (decvax!harpo!utah-cs!utah-gr!thomas)
 *              Jim McKie               (decvax!mcvax!jim)
 *              Steve Davies            (decvax!vax135!petsd!peora!srd)
 *              Ken Turkowski           (decvax!decwrl!turtlevax!ken)
 *              James A. Woods          (decvax!ihnp4!ames!jaw)
 *              Joe Orost               (decvax!vax135!petsd!joe)
 *
 */
/*
 * a code_int must be able to hold 2**BITS values of type int, and also -1
 */
typedef int             code_int;

#ifdef SIGNED_COMPARE_SLOW
typedef unsigned long int count_int;
typedef unsigned short int count_short;
#else /*SIGNED_COMPARE_SLOW*/
typedef long int          count_int;
#endif /*SIGNED_COMPARE_SLOW*/

#include <ctype.h>

#define ARGVAL() (*++(*argv) || (--argc && *++argv))

staticforward void output();
staticforward void cl_block();
staticforward void cl_hash();
staticforward void char_init();
staticforward void char_out();
staticforward void flush_char();

static int n_bits;                        /* number of bits/code */
static int maxbits = BITS;                /* user settable max # bits/code */
static code_int maxcode;                  /* maximum code, given n_bits */
static code_int maxmaxcode = (code_int)1 << BITS; /* should NEVER generate this code */
#ifdef COMPATIBLE               /* But wrong! */
# define MAXCODE(n_bits)        ((code_int) 1 << (n_bits) - 1)
#else /*COMPATIBLE*/
# define MAXCODE(n_bits)        (((code_int) 1 << (n_bits)) - 1)
#endif /*COMPATIBLE*/

static count_int htab [HSIZE];
static unsigned short codetab [HSIZE];
#define HashTabOf(i)       htab[i]
#define CodeTabOf(i)    codetab[i]

static code_int hsize = HSIZE;                 /* for dynamic table sizing */

/*
 * To save much memory, we overlay the table used by compress() with those
 * used by decompress().  The tab_prefix table is the same size and type
 * as the codetab.  The tab_suffix table needs 2**BITS characters.  We
 * get this from the beginning of htab.  The output stack uses the rest
 * of htab, and contains characters.  There is plenty of room for any
 * possible stack (stack used to be 8000 characters).
 */

#define tab_prefixof(i) CodeTabOf(i)
#define tab_suffixof(i)        ((char_type*)(htab))[i]
#define de_stack               ((char_type*)&tab_suffixof((code_int)1<<BITS))

static code_int free_ent = 0;                  /* first unused entry */

/*
 * block compression parameters -- after all codes are used up,
 * and compression rate changes, start over.
 */
static int clear_flg = 0;

static long int in_count = 1;            /* length of input */
static long int out_count = 0;           /* # of codes output (for debugging) */

/*
 * compress stdin to stdout
 *
 * Algorithm:  use open addressing double hashing (no chaining) on the
 * prefix code / next character combination.  We do a variant of Knuth's
 * algorithm D (vol. 3, sec. 6.4) along with G. Knott's relatively-prime
 * secondary probe.  Here, the modular division first probe is gives way
 * to a faster exclusive-or manipulation.  Also do block compression with
 * an adaptive reset, whereby the code table is cleared when the compression
 * ratio decreases, but after the table fills.  The variable-length output
 * codes are re-sized at this point, and a special CLEAR code is generated
 * for the decompressor.  Late addition:  construct the table according to
 * file size for noticeable speed improvement on small files.  Please direct
 * questions about this implementation to ames!jaw.
 */

static int g_init_bits;
static FILE* g_outfile;

static int ClearCode;
static int EOFCode;

static void
GIFcompress( int init_bits, FILE* outfile,GIFwriterdata *gwdp)
{
    register long fcode;
    register code_int i /* = 0 */;
    register int c;
    register code_int ent;
    register code_int disp;
    register code_int hsize_reg;
    register int hshift;

    GIFcompress_reinit();
     /*
     * Set up the globals:  g_init_bits - initial number of bits
     *                      g_outfile   - pointer to output file
     */
    g_init_bits = init_bits;
    g_outfile = outfile;

    /*
     * Set up the necessary values
     */
    out_count = 0;
    clear_flg = 0;
    in_count = 1;
    maxcode = MAXCODE(n_bits = g_init_bits);

    ClearCode = (1 << (init_bits - 1));
    EOFCode = ClearCode + 1;
    free_ent = ClearCode + 2;

    char_init();

    ent = GIFgetcompressbyte(gwdp);

    hshift = 0;
    for ( fcode = (long) hsize;  fcode < 65536L; fcode *= 2L )
        ++hshift;
    hshift = 8 - hshift;                /* set hash code range bound */

    hsize_reg = hsize;
    cl_hash( (count_int) hsize_reg);            /* clear hash table */

    output( (code_int)ClearCode );
#ifdef SIGNED_COMPARE_SLOW
    while ( (c = GIFgetcompressbyte( gwdp )) != (unsigned) EOF ) {
#else /*SIGNED_COMPARE_SLOW*/
    while ( (c = GIFgetcompressbyte( gwdp )) != EOF ) {  /* } */
#endif /*SIGNED_COMPARE_SLOW*/
        ++in_count;

        fcode = (long) (((long) c << maxbits) + ent);
        i = (((code_int)c << hshift) ^ ent);    /* xor hashing */
        if ( HashTabOf (i) == fcode ) {
            ent = CodeTabOf (i);
            continue;
        } else if ( (long)HashTabOf (i) < 0 )      /* empty slot */
            goto nomatch;
        disp = hsize_reg - i;           /* secondary hash (after G. Knott) */
        if ( i == 0 )
            disp = 1;
probe:
        if ( (i -= disp) < 0 )
            i += hsize_reg;
        if ( HashTabOf (i) == fcode ) {
            ent = CodeTabOf (i);
            continue;
        }
        if ( (long)HashTabOf (i) > 0 )
            goto probe;
nomatch:
        output ( (code_int) ent );
        ++out_count;
        ent = c;
#ifdef SIGNED_COMPARE_SLOW
        if ( (unsigned) free_ent < (unsigned) maxmaxcode) {
#else /*SIGNED_COMPARE_SLOW*/
        if ( free_ent < maxmaxcode ) {  /* } */
#endif /*SIGNED_COMPARE_SLOW*/
            CodeTabOf (i) = free_ent++; /* code -> hashtable */
            HashTabOf (i) = fcode;
        } else
                cl_block();
    }
    /*
     * Put out the final code.
     */
    output( (code_int)ent );
    ++out_count;
    output( (code_int) EOFCode );
}

/*****************************************************************
 * TAG( output )
 *
 * Output the given code.
 * Inputs:
 *      code:   A n_bits-bit integer.  If == -1, then EOF.  This assumes
 *              that n_bits =< (long)wordsize - 1.
 * Outputs:
 *      Outputs code to the file.
 * Assumptions:
 *      Chars are 8 bits long.
 * Algorithm:
 *      Maintain a BITS character long buffer (so that 8 codes will
 * fit in it exactly).  Use the VAX insv instruction to insert each
 * code in turn.  When the buffer fills up empty it and start over.
 */

static unsigned long cur_accum = 0;
static int cur_bits = 0;

static unsigned long masks[] = { 0x0000, 0x0001, 0x0003, 0x0007, 0x000F,
                                  0x001F, 0x003F, 0x007F, 0x00FF,
                                  0x01FF, 0x03FF, 0x07FF, 0x0FFF,
                                  0x1FFF, 0x3FFF, 0x7FFF, 0xFFFF };

static void
output(code_int  code)
{
    cur_accum &= masks[ cur_bits ];

    if( cur_bits > 0 )
        cur_accum |= ((long)code << cur_bits);
    else
        cur_accum = code;

    cur_bits += n_bits;

    while( cur_bits >= 8 ) {
        char_out( (unsigned int)(cur_accum & 0xff) );
        cur_accum >>= 8;
        cur_bits -= 8;
    }

    /*
     * If the next entry is going to be too big for the code size,
     * then increase it, if possible.
     */
   if ( free_ent > maxcode || clear_flg ) {

            if( clear_flg ) {

                maxcode = MAXCODE (n_bits = g_init_bits);
                clear_flg = 0;

            } else {

                ++n_bits;
                if ( n_bits == maxbits )
                    maxcode = maxmaxcode;
                else
                    maxcode = MAXCODE(n_bits);
            }
        }

    if( code == EOFCode ) {
        /*
         * At EOF, write the rest of the buffer.
         */
        while( cur_bits > 0 ) {
                char_out( (unsigned int)(cur_accum & 0xff) );
                cur_accum >>= 8;
                cur_bits -= 8;
        }

        flush_char();

        fflush( g_outfile );

    }
}

/*
 * Clear out the hash table
 */
static void
cl_block ()             /* table clear for block compress */
{

        cl_hash ( (count_int) hsize );
        free_ent = ClearCode + 2;
        clear_flg = 1;

        output( (code_int)ClearCode );
}

static void
cl_hash(register count_int hsize)          /* reset code table */
{

        register count_int *htab_p = htab+hsize;

        register long i;
        register long m1 = -1;

        i = hsize - 16;
        do {                            /* might use Sys V memset(3) here */
                *(htab_p-16) = m1;
                *(htab_p-15) = m1;
                *(htab_p-14) = m1;
                *(htab_p-13) = m1;
                *(htab_p-12) = m1;
                *(htab_p-11) = m1;
                *(htab_p-10) = m1;
                *(htab_p-9) = m1;
                *(htab_p-8) = m1;
                *(htab_p-7) = m1;
                *(htab_p-6) = m1;
                *(htab_p-5) = m1;
                *(htab_p-4) = m1;
                *(htab_p-3) = m1;
                *(htab_p-2) = m1;
                *(htab_p-1) = m1;
                htab_p -= 16;
        } while ((i -= 16) >= 0);

        for ( i += 16; i > 0; --i )
                *--htab_p = m1;
}

/******************************************************************************
 *
 * GIF Specific routines
 *
 ******************************************************************************/

/*
 * Number of characters so far in this 'packet'
 */
static int a_count;

/*
 * Set up the 'byte output' routine
 */
static void
char_init()
{
        a_count = 0;
}

/*
 * Define the storage for the packet accumulator
 */
static char accum[ 256 ];

/*
 * Add a character to the end of the current packet, and if it is 254
 * characters, flush the packet to disk.
 */
static void
char_out(int c)
{
        accum[ a_count++ ] = c;
        if( a_count >= 254 )
                flush_char();
}

/*
 * Flush the packet to disk, and reset the accumulator
 */
static void
flush_char()
{
        if( a_count > 0 ) {
                fputc( a_count, g_outfile );
                fwrite( accum, 1, a_count, g_outfile );
                a_count = 0;
        }
}

/*
** Attempt by Jack at re-init
*/
static void
GIFcompress_reinit()
{
    memset((char *)htab, 0, sizeof(htab));
    memset((char *)codetab, 0, sizeof(codetab));
    hsize = HSIZE;
    free_ent = 0;
    clear_flg = 0;
    in_count = 1;
    out_count = 0;

    cur_accum = 0;
    cur_bits = 0;
}
/* The End */
