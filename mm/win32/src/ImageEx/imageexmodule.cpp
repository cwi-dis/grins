#define AM_STANDARD

#include <windowsx.h>
//#include <mmsystem.h>
#include <afxwin.h>
#include "gear.h"
#include "cmifex.h"
//#include "img.h"
#define WIDTHBYTES(i)   ((i+31)/32*4)
#define BFT_BITMAP 0x4d42   /* 'BM' */
#define SIZEOF_BITMAPFILEHEADER_PACKED  (   \
    sizeof(WORD) +      /* bfType      */   \
    sizeof(DWORD) +     /* bfSize      */   \
    sizeof(WORD) +      /* bfReserved1 */   \
    sizeof(WORD) +      /* bfReserved2 */   \
    sizeof(DWORD))      /* bfOffBits   */
#define MAXREAD  32768

static PyObject *ImageExError;

PyIMPORT CWnd *GetWndPtr(PyObject *);


static HIGEAR hIGear=NULL;
//static HWND hWND;
static BOOL fl;




#ifdef __cplusplus
extern "C" {
#endif
//***************************
//Things to do:
//	- built a LinkList with the used windows so as to preserve MemoryManagement
//	- use in a more clever way to cover every case
//***************************

//***************************************************
//					Gif Section
//***************************************************

static PyObject *format_map, *format_map_b2t, *format_choices, *format_xmap;
extern PyObject *getimgformat();		/* Get format by name */

struct gifobject{
	int width;
    int height;
    int top;
    int left;
    int aspect;
    int transparent;
	long *lmap;
	int	is_reader;	/* TRUE if this is a reader */
	char	*filename;	/* filename of the image file */
	FILE	*filep;
	int	interlaced;	/* TRUE if image is interlaced (for read) */
};

struct GIFwriterdata{
    unsigned char	*data;
    int		xpos, ypos, width, height, rowlen;
};

static PyObject *errobject;


/*
** NOTE: The GIF LWZ decompression routines are not safe in parallel
** programs. They use the ZeroDataBlock variable below to pass a flag around,
** and use statically allocated tables besides.
*/
#define MAX_LWZ_BITS 12
int ZeroDataBlock = 0;

static char doc_pgm[] = "This object reads/writes PGM files\n"
	"The 'width', 'height', 'top', 'left', 'aspect' and 'format'\n"
	"attributes describe the picture,\n"
	"'colormap' has the colormap object for the picture\n"
	"There may be a 'transparent' attribute given in index of the color\n"
	"to be treated as transparent.";



RGBQUAD *
GIFreadmap(FILE *filep, int& ncolors)
{
    RGBQUAD *map;
    int r, g, b, i;

    if ( (map=(RGBQUAD *)malloc(ncolors*sizeof(RGBQUAD))) == NULL ) {
	MessageBox(NULL, "Not enough memory.","Error",MB_OK);
	return NULL;
    }
    for(i=0; i<ncolors; i++) {
	r = fgetc(filep);
	g = fgetc(filep);
	b = fgetc(filep);
	map[i].rgbRed = (BYTE)r;
	map[i].rgbGreen = (BYTE)g;
	map[i].rgbBlue = (BYTE)b;
	map[i].rgbReserved = (BYTE)0;
	//map[i] = r | (g<<8) | (b<<16);
    }
	
    if ( feof(filep) || ferror(filep) ) {
	PyErr_SetString(errobject, "Truncated GIF file");
	free(map);
	return NULL;
    }
    
	return map;
}

int
GIFskipblock(FILE *filep)
{
    int i, count;

    if ( (count=fgetc(filep)) == EOF )
	return 0;
    for(i=0; i<count; i++)
	(void)fgetc(filep);
    return count;
}

int
GIFgettransparent(FILE *filep)
{
    int count;
    unsigned char value;

    if ( (count=fgetc(filep)) == EOF || count != 4 )
	return -1;
    (void)fgetc(filep);
    (void)fgetc(filep);
    (void)fgetc(filep);
    value = (unsigned char)fgetc(filep);
    return value;
}




int
GIFreadheader(RGBQUAD *lmap, FILE *filep, int& left, int& top, 
			  int& width, int& height, int& ncolors, int& aspect,
			  int& interlaced, int& bpp)
{
    char buf[6];
    int hasmap, bgnd;
    int ch;
    int atimagestart;
    RGBQUAD *gmap = NULL;
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
    if ( fread(buf, 1, 6, filep) != 6 ) goto EndOfFile;
    if ( strncmp(buf, "GIF87a", 6) != 0 &&
	 strncmp(buf, "GIF89a", 6) != 0 ) {
	MessageBox(NULL, "Not a GIF87 or GIF89 file.","Error",MB_OK);
	return 0;
    }
    /* We don't check for EOF each time, only when we start using data */
    ch = getc(filep);
    width = ch + (getc(filep) << 8);
    ch = getc(filep);
    height = ch + (getc(filep) << 8);
    ch = getc(filep);
    hasmap = (ch & 0x80);
    bpp = (ch & 7) + 1;
    ncolors = 1 << bpp;
    bgnd = getc(filep);
    aspect = getc(filep);
    if ( feof(filep) || ferror(filep) ) goto EndOfFile;

    if ( hasmap ) {
		if( (gmap = GIFreadmap(filep, ncolors)) == NULL )
		{
			MessageBox(NULL, "Unable to read the colormap.","Error",MB_OK);
			goto ErrorExit;
		}
    }
    if ( feof(filep) || ferror(filep) ) goto EndOfFile;


    atimagestart = 0;
    do {
	if( (ch = getc(filep)) == EOF ) goto EndOfFile;
	switch(ch) {
	case ';':	/* Terminator */
	    MessageBox(NULL, "No image found in file.","Error",MB_OK);
	    return 0;

	case '!':	/* Extension */
	    etype = (unsigned char)getc(filep);	/* Extension type */
	    if ( etype == 0xf9 )	/* Transparent extension */
		transparent = GIFgettransparent(filep);
	    while( GIFskipblock(filep) ) ;
	    break;

	case ',':
	    atimagestart = 1;
	    break;
	}
    } while ( !atimagestart );

    ch = getc(filep);
    left = ch + (getc(filep) << 8);
    ch = getc(filep);
    top = ch + (getc(filep) << 8);
    ch = getc(filep);
    width = ch + (getc(filep) << 8);
    ch = getc(filep);
    height = ch + (getc(filep) << 8);
    ch = getc(filep);
    hasmap = (ch & 0x80);
    interlaced = (ch & 0x40);
    if ( hasmap ) { /* Otherwise use values from header */
	bpp = (ch & 7) + 1;
	ncolors = 1 << bpp;
    }
    if ( feof(filep) || ferror(filep) ) goto EndOfFile;

    if ( hasmap ) {
		if( (lmap = GIFreadmap(filep, ncolors)) == NULL )
		{
			MessageBox(NULL, "Unable to read the colormap.","Error",MB_OK);
			goto ErrorExit;
		}
    }

    if ( feof(filep) || ferror(filep) ) goto EndOfFile;

    //if ( lmap )
	//free(lmap);
    if ( gmap )
	free(gmap);
    return 1;
    /*
    ** Yes! Labels!
    */
 EndOfFile:
    MessageBox(NULL, "Truncated GIF file.","Error",MB_OK);
 ErrorExit:
    if ( lmap )
	free(lmap);
    if ( gmap )
	free(gmap);
    return 0;
}



/*PyObject *
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
	
	//if ( !gifselfattr(self, "format", "O", &fmt, 1) ||
	//     !gifselfattr(self, "width", "i", &width, 1) ||
	//     !gifselfattr(self, "height", "i", &height, 1) )
	//    return NULL;

	unsigned char *datap;
	int b2t;
	int width, height, rowlen;
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
	    rowlen = (width+3) & ~3;	// SGI images 32bit aligned
	if( (rv=PyString_FromStringAndSize(NULL, rowlen*height)) == NULL )
	    return NULL;
	datap = (unsigned char *)PyString_AsString(rv);
	if ( b2t ) {
	    datap = datap + rowlen*(height-1);
	    rowlen = -rowlen;
	}

	if (GIFreadimage(self, (char*)datap, width, height, rowlen,
			 self->interlaced) == 0) {
	    Py_DECREF(rv);
	    return NULL;
	}
	return rv;
}*/

/*
** LWZ reader routines stolen from giftopnm.c
*/

int
LWZGetDataBlock(FILE *fd, unsigned char  *buf)
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

int
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

int
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

int
GIFreadimage(FILE *filep, unsigned char *datap, int width, int height, int rowlen, int interlace)
{
    int ch, v, xpos=0, ypos=0, pass=0;

    if ( (ch=getc(filep)) == EOF ) {
	PyErr_SetString(errobject, "Truncated GIF file");
	return 0;
    }
    if (LWZReadByte(filep, 1, ch) < 0 ) {
	PyErr_SetString(errobject, "Truncated GIF file");
	return 0;
    }
    while ((v=LWZReadByte(filep, 0, ch)) >= 0 ) {
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

void
GIFputword(int w, FILE* fp)
{
    fputc( w & 0xff, fp );
    fputc( (w>>8) & 0xff, fp );
}

int
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

staticforward void output(code_int);
staticforward void cl_block();
staticforward void cl_hash(register count_int);
staticforward void char_init();
staticforward void char_out(int);
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

void
GIFcompress( int init_bits, FILE* outfile,GIFwriterdata *gwdp)
{
    register long fcode;
    register code_int i /* = 0 */;
    register int c;
    register code_int ent;
    register code_int disp;
    register code_int hsize_reg;
    register int hshift;

    //GIFcompress_reinit();
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


WORD DibNumColors (VOID FAR * pv)
{
    INT                 bits;
    LPBITMAPINFOHEADER  lpbi;
    LPBITMAPCOREHEADER  lpbc;

    lpbi = ((LPBITMAPINFOHEADER)pv);
    lpbc = ((LPBITMAPCOREHEADER)pv);

    /*  With the BITMAPINFO format headers, the size of the palette
     *  is in biClrUsed, whereas in the BITMAPCORE - style headers, it
     *  is dependent on the bits per pixel ( = 2 raised to the power of
     *  bits/pixel).
     */
    if (lpbi->biSize != sizeof(BITMAPCOREHEADER)){
        if (lpbi->biClrUsed != 0)
            return (WORD)lpbi->biClrUsed;
        bits = lpbi->biBitCount;
    }
    else
        bits = lpbc->bcBitCount;

    switch (bits){
        case 1:
                return 2;
        case 4:
                return 16;
        case 8:
                return 256;
        default:
                /* A 24 bitcount DIB has no color table */
                return 0;
    }
}



HANDLE ReadDibBitmapInfo (long *lmap, int width, int height,
						  int ncolors, int bpp)
{
    HANDLE    hbi = NULL;
    INT       i;
    WORD      nNumColors;

    RGBQUAD FAR       *pRgb;
    BITMAPINFOHEADER   bi;
    LPBITMAPINFOHEADER lpbi;
    DWORD              dwWidth = (DWORD)width;
    DWORD              dwHeight = (DWORD)height;
    WORD               wPlanes = 1, wBitCount = (WORD)bpp;

    
    nNumColors = (WORD)ncolors;

    bi.biSize           = sizeof(BITMAPINFOHEADER);
    bi.biWidth              = dwWidth;
    bi.biHeight             = dwHeight;
	bi.biPlanes             = wPlanes;
    bi.biBitCount           = wBitCount;
    bi.biCompression        = BI_RGB;
	bi.biSizeImage          = 0;
    bi.biXPelsPerMeter      = 0;
    bi.biYPelsPerMeter      = 0;
    bi.biClrUsed            = nNumColors;
    bi.biClrImportant       = nNumColors;

    /*  Fill in some default values if they are zero */
    if (bi.biSizeImage == 0){
        bi.biSizeImage = WIDTHBYTES ((DWORD)bi.biWidth * bi.biBitCount)
                         * bi.biHeight;
    }
    
	if (bi.biClrUsed == 0)
        bi.biClrUsed = DibNumColors(&bi);

    /* Allocate for the BITMAPINFO structure and the color table. */
    hbi = GlobalAlloc (GHND, (LONG)bi.biSize + nNumColors * sizeof(RGBQUAD));
    if (!hbi)
        return NULL;
    
	lpbi = (LPBITMAPINFOHEADER)GlobalLock (hbi);
    *lpbi = bi;

    pRgb = (RGBQUAD FAR *)((LPSTR)lpbi + bi.biSize);
	//strcpy((LPSTR)pRgb,(LPSTR)lmap);
	MessageBox(NULL, "Test case.","Error",MB_OK);
	for (i = nNumColors - 1; i >= 0; i--){
         RGBQUAD rgb;

         rgb.rgbRed      = ((RGBTRIPLE FAR *)pRgb)[i].rgbtRed;
         rgb.rgbBlue     = ((RGBTRIPLE FAR *)pRgb)[i].rgbtBlue;
         rgb.rgbGreen    = ((RGBTRIPLE FAR *)pRgb)[i].rgbtGreen;
         rgb.rgbReserved = (BYTE)0;

         pRgb[i] = rgb;
      }
    

    GlobalUnlock(hbi);
    return hbi;
}


BOOL DibInfo (
    HANDLE hbi,
    LPBITMAPINFOHEADER lpbi)
{
    if (hbi){
        *lpbi = *(LPBITMAPINFOHEADER)GlobalLock (hbi);

        /* fill in the default fields */
        if (lpbi->biSize != sizeof (BITMAPCOREHEADER)){
            if (lpbi->biSizeImage == 0L)
                                lpbi->biSizeImage = WIDTHBYTES(lpbi->biWidth*lpbi->biBitCount) * lpbi->biHeight;

            if (lpbi->biClrUsed == 0L)
                                lpbi->biClrUsed = DibNumColors (lpbi);
    }
        GlobalUnlock (hbi);
        return TRUE;
    }
    return FALSE;
}


PBITMAPINFO CreateBitmapInfoStruct(HBITMAP hBmp) { 
    BITMAP bmp; 
    PBITMAPINFO pbmi; 
    WORD    cClrBits; 
 
    /* Retrieve the bitmap's color format, width, and height. */ 
 
    if (!GetObject(hBmp, sizeof(BITMAP), (LPSTR)&bmp)) 
        return NULL; 
 
 
    /* Convert the color format to a count of bits. */ 
 
    cClrBits = (WORD)(bmp.bmPlanes * bmp.bmBitsPixel); 
 
    if (cClrBits == 1) 
        cClrBits = 1; 
    else if (cClrBits <= 4) 
        cClrBits = 4; 
    else if (cClrBits <= 8) 
        cClrBits = 8; 
    else if (cClrBits <= 16) 
        cClrBits = 16; 
    else if (cClrBits <= 24) 
        cClrBits = 24; 
    else 
        cClrBits = 32; 
 
    /* 
     * Allocate memory for the BITMAPINFO structure. (This structure 
     * contains a BITMAPINFOHEADER structure and an array of RGBQUAD data 
     * structures.) 
     */ 
 
    if (cClrBits != 24) 
         pbmi = (PBITMAPINFO) LocalAlloc(LPTR, 
                    sizeof(BITMAPINFOHEADER) + 
                    sizeof(RGBQUAD) * (2^cClrBits)); 
 
    /* 
     * There is no RGBQUAD array for the 24-bit-per-pixel format. 
     */ 
 
    else 
         pbmi = (PBITMAPINFO) LocalAlloc(LPTR, 
                    sizeof(BITMAPINFOHEADER)); 
 
 
 
    /* Initialize the fields in the BITMAPINFO structure. */ 
 
    pbmi->bmiHeader.biSize = sizeof(BITMAPINFOHEADER); 
    pbmi->bmiHeader.biWidth = bmp.bmWidth; 
    pbmi->bmiHeader.biHeight = bmp.bmHeight; 
    pbmi->bmiHeader.biPlanes = bmp.bmPlanes; 
    pbmi->bmiHeader.biBitCount = bmp.bmBitsPixel; 
    if (cClrBits < 24) 
        pbmi->bmiHeader.biClrUsed = 2^cClrBits; 
 
 
    /* If the bitmap is not compressed, set the BI_RGB flag. */ 
 
    pbmi->bmiHeader.biCompression = BI_RGB; 
 
    /* 
     * Compute the number of bytes in the array of color 
     * indices and store the result in biSizeImage. 
     */ 
 
    pbmi->bmiHeader.biSizeImage = (pbmi->bmiHeader.biWidth + 7) /8 
                                  * pbmi->bmiHeader.biHeight 
                                  * cClrBits; 
 
    /* 
     * Set biClrImportant to 0, indicating that all of the 
     * device colors are important. 
     */ 
 
    pbmi->bmiHeader.biClrImportant = 0; 
 
    return pbmi; 
 
} 


DWORD PASCAL lwrite (
    INT      fh,
    VOID FAR     *pv,
    DWORD            ul)
{
    DWORD     ulT = ul;
    BYTE *hp = (BYTE*)pv;

    while (ul > MAXREAD) {
        if (_lwrite(fh, (LPSTR)hp, (UINT)MAXREAD) != MAXREAD)
                return 0;
        ul -= MAXREAD;
        hp += MAXREAD;
    }
    if (_lwrite(fh, (LPSTR)hp, (UINT)ul) != (UINT)ul)
        return 0;                 

    return ulT;
}


VOID WriteMapFileHeaderandConvertFromDwordAlignToPacked(HFILE fh, LPBITMAPFILEHEADER pbf)
{

        /* write bfType*/
    _lwrite(fh, (LPSTR)&pbf->bfType, (UINT)sizeof (WORD));
        /* now pass over extra word, and only write next 3 DWORDS!*/
        _lwrite(fh, (LPSTR)&pbf->bfSize, sizeof(DWORD) * 3);
}


BOOL WriteDIB (
    LPSTR szFile,
    PBITMAPINFO hdib,
	int rowlen, int height, int nColors,
	char *data)
{
    BITMAPFILEHEADER    hdr;
    LPBITMAPINFOHEADER  lpbi = &(hdib->bmiHeader);
    HFILE               fh;
    OFSTRUCT            of;

    if (!hdib)
        return FALSE;

    fh = OpenFile(szFile, &of, (UINT)OF_CREATE|OF_READWRITE);
    if (fh == -1)
        return FALSE;

    //lpbi = (VOID FAR *)GlobalLock (hdib);

    /* Fill in the fields of the file header */
    hdr.bfType          = BFT_BITMAP;
    hdr.bfSize          = (DWORD) (hdib->bmiHeader.biSize +rowlen*height+ nColors * sizeof(RGBQUAD)+ SIZEOF_BITMAPFILEHEADER_PACKED);
    hdr.bfReserved1     = 0;
    hdr.bfReserved2     = 0;
    hdr.bfOffBits       = (DWORD) (SIZEOF_BITMAPFILEHEADER_PACKED + hdib->bmiHeader.biSize +
                          nColors * sizeof(RGBQUAD));

    /* Write the file header */
#ifdef  FIXDWORDALIGNMENT
    _lwrite(fh, (LPSTR)&hdr, (UINT)(SIZEOF_BITMAPFILEHEADER_PACKED));
#else
        WriteMapFileHeaderandConvertFromDwordAlignToPacked(fh, &hdr);
#endif

        /* this struct already DWORD aligned!*/
    /* Write the DIB header and the bits */
    lwrite (fh, (LPSTR)lpbi, (DWORD) (hdib->bmiHeader.biSize));
	lwrite (fh, (LPSTR)hdib-> bmiColors, (DWORD) (nColors * sizeof(RGBQUAD)));
	lwrite (fh, (LPSTR)data, (DWORD) (rowlen*height));
	
    //GlobalUnlock (hdib);
    _lclose(fh);
    MessageBox(NULL, "End writing file.","Error",MB_OK);
	return TRUE;
}


BOOL DrawBitmap (
    HDC    hdc,
    INT    x,
    INT    y,
    HBITMAP    hbm,
    DWORD          rop)
{
    HDC       hdcBits;
    BITMAP    bm;
//    HPALETTE  hpalT;  
    BOOL      f;

    if (!hdc || !hbm)
        return FALSE;

    hdcBits = CreateCompatibleDC(hdc);
    GetObject(hbm,sizeof(BITMAP),(LPSTR)&bm);
    SelectObject(hdcBits,hbm);
    f = BitBlt(hdc,0,0,bm.bmWidth,bm.bmHeight,hdcBits,0,0,rop);
    DeleteDC(hdcBits);

    return f;
    UNREFERENCED_PARAMETER(y);
    UNREFERENCED_PARAMETER(x);
}
//***************************************************
//					End of Gif Section
//***************************************************
long reader(HWND hWND,LPSTR fname, float scale, RECT& rect, int center)
{
   AT_ERRCOUNT nError;
   //IG_image_delete(hIGear);
   nError=IG_load_file(fname,&hIGear);
   RECT r;
   
   ::GetClientRect(hWND,&r);
   
   if(nError!=0)
   {
	   TRACE("Error in Loading image %s\n", fname);
	   return 0;
   }

    //long x,y;
	AT_RECT rcImageRect;
	HIGEAR hBitmap =hIGear;
	AT_DIMENSION Width,Height;
	UINT BitsPerPixel;
	
	rcImageRect.top = r.top;
	rcImageRect.bottom = r.bottom;
	rcImageRect.left = r.left;
	rcImageRect.right = r.right;

	IG_image_dimensions_get (hBitmap, &Width, &Height,&BitsPerPixel);

	if(scale>0)
		{
			if (center==1)
			{
				rcImageRect.top = (long)((rcImageRect.bottom-scale*Height)/2);
				rcImageRect.bottom = (long)(rcImageRect.top + scale*Height);
				rcImageRect.left = (long)((rcImageRect.right-scale*Width)/2);
				rcImageRect.right = (long)(rcImageRect.left + scale*Width);
			}
			else
			{
				rcImageRect.top = 0;
				rcImageRect.bottom = (long)(rcImageRect.top + scale*Height);
				rcImageRect.left = 0;
				rcImageRect.right = (long)(rcImageRect.left + scale*Width);
			}
		}
	else
	{
		IG_display_adjust_aspect(hBitmap,&rcImageRect,IG_ASPECT_DEFAULT);
		if (center!=1)
		{
			rcImageRect.right = rcImageRect.right-rcImageRect.left;
			rcImageRect.bottom = rcImageRect.bottom-rcImageRect.top;
			rcImageRect.left = rcImageRect.top = 0;
		}
	}

	IG_device_rect_set(hBitmap,&rcImageRect);
	
	rect.top = rcImageRect.top;
	rect.bottom = rcImageRect.bottom;
	rect.left = rcImageRect.left;
	rect.right = rcImageRect.right;
	
   return((long)hBitmap);

}



void paintdll(HWND hWND,long bit,int r,int g,int b,float scale, int center)
{
	//PAINTSTRUCT ps;
	HDC dc=GetDC(hWND);
	
	//dc=BeginPaint(hWND, &ps); 
       
	CString str = "No file currently selected";
   
    RECT rect;
    
    AT_RECT rcRefRect;
	AT_RGB bcolor;//,fcolor;

	bcolor.r = r;
	bcolor.g = g;
	bcolor.b = b;
	
	//fcolor.r = 0;
	//fcolor.g = 0;
	//fcolor.b = 0;

    if (bit != 0)
     {
	  HIGEAR hBitmap =(HIGEAR) bit;

	  IG_display_desktop_pattern_set(hBitmap,NULL,NULL,NULL,FALSE);

	  GetClientRect(hWND,&rect);

      rcRefRect.right=rect.right;
	  rcRefRect.bottom=rect.bottom;
	  rcRefRect.top=rect.top;
	  rcRefRect.left=rect.left;

	  AT_DIMENSION Width,Height;
	  UINT BitsPerPixel;
	
	  IG_image_dimensions_get (hBitmap, &Width, &Height,&BitsPerPixel);

	  if(scale>0)
		{
			if (center==1)
			{
				rcRefRect.top = (long)((rcRefRect.bottom-scale*Height)/2);
				rcRefRect.bottom = (long)(rcRefRect.top + scale*Height);
				rcRefRect.left = (long)((rcRefRect.right-scale*Width)/2);
				rcRefRect.right = (long)(rcRefRect.left + scale*Width);
			}
			else
			{
				rcRefRect.top = 0;
				rcRefRect.bottom = (long)(rcRefRect.top + scale*Height);
				rcRefRect.left = 0;
				rcRefRect.right = (long)(rcRefRect.left + scale*Width);
			}
		}
	  else
		{
			IG_display_adjust_aspect(hBitmap,&rcRefRect,IG_ASPECT_DEFAULT);
			if (center!=1)
			{
				rcRefRect.right = rcRefRect.right-rcRefRect.left;
				rcRefRect.bottom = rcRefRect.bottom-rcRefRect.top;
				rcRefRect.left = rcRefRect.top = 0;
			}
		}
	  //IG_display_stretch_set(hBitmap,TRUE);
     //IG_display_fit_method(hBitmap,hWND,&rcRefRect,&nZoomLevel,IG_DISPLAY_FIT_TO_WINDOW);
	  IG_device_rect_set(hBitmap,&rcRefRect);
	  IG_display_image(hBitmap,dc);
	 
     }
   else 
   {
     DrawText(dc,str, -1, &rect, DT_SINGLELINE | DT_CENTER | DT_VCENTER);
	 fl=FALSE;
     
   }
   
   ReleaseDC(hWND,dc);
   
   //EndPaint(hWND, &ps); 
    
   //return 0L;
}


void destroyimage(long bit)
{
	if (bit != 0)
     {
	  HIGEAR hBitmap =(HIGEAR) bit;
	  if(IG_image_is_valid(hBitmap))
		  IG_image_delete(hBitmap);
     }
}



//-----------------------------------------------------

static PyObject* py_ImageEx_PutImage(PyObject *self, PyObject *args)
{
	HWND hW;
	CWnd *obWnd;
	long bit;
	PyObject *testOb = Py_None;
	int r,g,b,center=0;
	float scale;
	
	if(!PyArg_ParseTuple(args, "Oliiifi", &testOb, &bit, &r, &g, &b, &scale, &center))
		return NULL;
	
	obWnd = GetWndPtr(testOb);
	hW = obWnd->m_hWnd;

	paintdll(hW,bit,r,g,b,scale,center);
	Py_INCREF(Py_None);
	return Py_None;

}




static PyObject* py_ImageEx_Prepare(PyObject *self, PyObject *args)
{
	char *filename;
	HWND hW;
	CWnd *obWnd;
	long bit;
	PyObject *testOb = Py_None,*tmp;
	RECT rect;
	float scale;
	int center;
	int transp;

	//ASSERT(0);
	
	if(!PyArg_ParseTuple(args, "Osfii", &testOb, &filename, &scale, &center, &transp))
		return NULL;

	obWnd = GetWndPtr(testOb);
	hW = obWnd->m_hWnd;
	bit=reader(hW,filename,scale,rect,center);
	
	tmp = Py_BuildValue("lllll",bit,rect.left,rect.top,rect.right,rect.bottom);

	return tmp;
}



static PyObject* py_ImageEx_Destroy(PyObject *self, PyObject *args)
{
	long bit;
		
	if(!PyArg_ParseTuple(args, "l", &bit))
		return NULL;

	destroyimage(bit);
	
	Py_INCREF(Py_None);
	return Py_None;
}



static PyObject* py_ImageEx_SizeOfImage(PyObject *self, PyObject *args)
{
	char *filename;
	PyObject *tmp = Py_None;
	HIGEAR bit=NULL;
	AT_ERRCOUNT nError;
    
	if(!PyArg_ParseTuple(args, "s", &filename))
		return NULL;

	nError=IG_load_file(filename,&bit);
   
    if(nError!=0)
    {
	    Py_INCREF(Py_None);
		return Py_None;
    }
	
	AT_DIMENSION Width,Height;
	UINT BitsPerPixel;
	
	IG_image_dimensions_get (bit, &Width, &Height,&BitsPerPixel);
	
	if(IG_image_is_valid(bit))
		  IG_image_delete(bit);

	tmp = Py_BuildValue("ii", Width, Height);

	return tmp;
}


static PyObject* py_ImageEx_ImageRect(PyObject *self, PyObject *args)
{
	long k;
	PyObject *tmp = Py_None;
	HIGEAR bit=NULL;
	AT_RECT rcImageRect;
    
	if(!PyArg_ParseTuple(args, "l", &k))
		return NULL;

	bit = (HIGEAR)k;

	if(!IG_image_is_valid(bit))
	{
		Py_INCREF(Py_None);
		return Py_None;
	}
	
	IG_device_rect_get(bit,&rcImageRect);	

	tmp = Py_BuildValue("llll", rcImageRect.left, rcImageRect.top, rcImageRect.right, rcImageRect.bottom);

	return tmp;
}


static PyObject* py_ImageEx_ReadGIF(PyObject *self, PyObject *args)
{
	HWND hW;
	CWnd *obWnd;
	long bit;
	char *filename;
	PyObject *testOb = Py_None,*tmp = Py_None,*rv = Py_None;
	FILE *filep = NULL;
	RGBQUAD *lmap = NULL;
	int left,top,width,height,ncolors,aspect,interlaced,rowlen,b2t,bpp;
	unsigned char *datap;
			
	if(!PyArg_ParseTuple(args, "Os", &testOb, &filename))
		return NULL;

	if ((filep = fopen(filename, "rb")) == NULL) {
	    MessageBox(NULL, "Error reading the file.","Error",MB_OK);
	    Py_INCREF(Py_None);
		return Py_None;
	}
	 
	if ( !GIFreadheader(lmap,filep,left,top,width,height,ncolors,
						aspect,interlaced,bpp))
	{
		MessageBox(NULL, "Error executing GIFreadheader.","Error",MB_OK);
	}
	
	b2t = 0;
	rowlen = (width+3) & ~3;	// SGI images 32bit aligned
	
	if( (rv=PyString_FromStringAndSize(NULL, rowlen*height)) == NULL )
	    {
			MessageBox(NULL, "Error executing PyString_FromStringAndSize.","Error",MB_OK);
		}
	
	if(rv!=NULL)
	{
		datap = (unsigned char *)PyString_AsString(rv);
		if ( b2t ) {
			datap = datap + rowlen*(height-1);
			rowlen = -rowlen;
		}

		if (GIFreadimage(filep, datap, width, height, 
			rowlen,interlaced) == 0) {
			MessageBox(NULL, "Error executing GIFreadimage.","Error",MB_OK);
		}
		//datap = (unsigned char *)datap;
	}
	else rv = Py_None;
	
	obWnd = GetWndPtr(testOb);
	hW = obWnd->m_hWnd;
	char str[200];
	wsprintf(str, "left: %d,top: %d,width: %d,height: %d,ncolors: %d\naspect: %d,interlaced: %d,rowlen: %d,b2t: %d,bpp: %d\nimage size: %d",
					left,top,width,height,ncolors,
					aspect,interlaced,rowlen,b2t,bpp,strlen((char*)datap));
	MessageBox(NULL, str,"Debug",MB_OK);
	//BITMAPINFOHEADER    bi;
	PBITMAPINFO bi = NULL;
    //LPBITMAPINFOHEADER  lpbi;
    //HANDLE              hdib;
	HBITMAP Hbi = NULL;
    
    //hdib = ReadDibBitmapInfo(lmap,rowlen,height,ncolors,bpp);
    Hbi = CreateBitmap(rowlen,height,1,bpp,lmap);
	if (!Hbi)
	{
		MessageBox(NULL, "Can not create bitmap handle.","Error",MB_OK);
	}
	else if (!SetBitmapBits(Hbi,rowlen*height,datap))
		MessageBox(NULL, "Error executing SetBitmapBits.","Error",MB_OK);
	if((bi = CreateBitmapInfoStruct(Hbi))== NULL)
		MessageBox(NULL, "Error executing CreateBitmapInfoStruct.","Error",MB_OK);
	else
	{
		WriteDIB ("d:\\test.bmp",bi,rowlen,height,ncolors,(char*)datap);
	}
	//FILE* fil;
	//if ((fil = fopen("d:\\test.bin", "wb")) != NULL)
	//{
	//	fwrite(datap, sizeof(char),strlen((char*)datap),fil);
	//	fclose(fil);
	//}
	//else DibInfo(hdib,&bi);
	
	//AT_ERRCOUNT nError;
   
	//nError = IG_image_import_DDB(Hbi,NULL,&hIGear);
	
	//nError=IG_image_create_DIB(0, 0, 0, (LPAT_DIB)(char FAR*) &bi, &hIGear);
	
	//if(nError!=0)
    //{
	//   MessageBox(NULL, "Error in creating the image gear handle.","Error",MB_OK);
    //}
	
	//HDC hdc = GetDC(hW);
	//if(!DrawBitmap (hdc,0,0,Hbi,SRCCOPY))
	//	MessageBox(NULL, "Cannot Draw Bitmap.","Error",MB_OK);
	//HDC cdc = CreateCompatibleDC(hdc);
	//HBITMAP pOld1 = (HBITMAP)SelectObject(cdc,Hbi);
		
	//BitBlt(hdc,0, 0, rowlen,height, 
	//			cdc, 0,0, SRCCOPY);	
	//ReleaseDC(hW, hdc);
	//paintdll(hW,(long)hIGear,0,0,0,1,0);
	if ( filep != NULL )
		fclose(filep);

	if ( lmap != NULL )
		free(lmap);
	
	//Py_INCREF(Py_None);
	//return Py_None;
	tmp = Py_BuildValue("s", datap);

	return tmp;
}



static PyMethodDef ImageExMethods[] = 
{
	{ "PutImage", (PyCFunction)py_ImageEx_PutImage, 1},
    { "PrepareImage", (PyCFunction)py_ImageEx_Prepare, 1},
	{ "Destroy", (PyCFunction)py_ImageEx_Destroy, 1},
	{ "SizeOfImage", (PyCFunction)py_ImageEx_SizeOfImage, 1},
	{ "ImageRect", (PyCFunction)py_ImageEx_ImageRect, 1},
	{ "ReadGIF",	py_ImageEx_ReadGIF,	1},
	{ NULL, NULL }
};

PyEXPORT 
void initimageex()
{
	PyObject *m, *d;
	m = Py_InitModule("imageex", ImageExMethods);
	d = PyModule_GetDict(m);
	ImageExError = PyString_FromString("ImageEx.error");
	PyDict_SetItemString(d, "error", ImageExError);
}

#ifdef __cplusplus
}
#endif
