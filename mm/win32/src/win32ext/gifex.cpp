/************************************************************
**Copyright 1998 Epsilon S.A

** Part of this code was taken from imagemodule.c,
** of which the copyright notices are below.

/************************************************************
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

#include "stdafx.h"

//Win32 Header Files
#include <process.h>


#include "moddef.h"
DECLARE_PYMODULECLASS(Gifex);
IMPLEMENT_PYMODULECLASS(Gifex,GetGifex,"Gifex Module Wrapper Object");


#define BFT_BITMAP 0x4d42   /* 'BM' */

static PyObject *gifexError;

//***************************
//Things to do:
//	- built a LinkList with the used windows so as to preserve MemoryManagement
//	- use in a more clever way to cover every case
//***************************

//***************************************************
//					Gif Section
//***************************************************


static PyObject *errobject;


/*
** NOTE: The GIF LWZ decompression routines are not safe in parallel
** programs. They use the ZeroDataBlock variable below to pass a flag around,
** and use statically allocated tables besides.
*/
#define MAX_LWZ_BITS 12
int ZeroDataBlock = 0;

RGBQUAD *
GIFreadmap(FILE *filep, int& ncolors)
{
    RGBQUAD *map;
    int r, g, b, i;

    if ( (map=(RGBQUAD *)malloc(ncolors*sizeof(RGBQUAD))) == NULL ) 
		return NULL;

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




RGBQUAD *
GIFreadheader( FILE *filep, int& left, int& top, 
			  int& width, int& height, int& ncolors, int& aspect,
			  int& interlaced, int& bpp, int& transparent,BOOL& ok)
{
    char buf[6];
    int hasmap, bgnd;
    int ch;
    int atimagestart;
    RGBQUAD *lmap = NULL;
	unsigned char etype;
    //int transparent = -1;

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
	ok = FALSE;
	return NULL;
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
		lmap = GIFreadmap(filep, ncolors);
		
		if( lmap == NULL )
			goto ErrorExit;
    }

    if ( feof(filep) || ferror(filep) ) goto EndOfFile;


    atimagestart = 0;
    do {
	if( (ch = getc(filep)) == EOF ) goto EndOfFile;
	switch(ch) {
	case ';':	/* Terminator */
	    return NULL;

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
		if (lmap != NULL)
		{
			free(lmap);
			lmap = NULL;
		}
		
		lmap = GIFreadmap(filep, ncolors);
		
		if( lmap == NULL )
			goto ErrorExit;
    }

    if ( feof(filep) || ferror(filep) ) goto EndOfFile;

    ok = TRUE;
	return lmap;
    /*
    ** Yes! Labels!
    */
 EndOfFile:
    //MessageBox(NULL, "Truncated GIF file.","Error",MB_OK);
 ErrorExit:
    if ( lmap )
	free(lmap);
    ok = FALSE;
	return NULL;
}





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


//***************************************************
//					End of Gif Section
//***************************************************

static PyObject* py_gifex_ReadGIF(PyObject *self, PyObject *args)
{
	char *filename, *tofile;
	PyObject *tmp = Py_None,*rv = Py_None;
	FILE *filep = NULL;
	RGBQUAD *lmap = NULL;
	int left,top,width,height,ncolors,aspect,interlaced,rowlen,b2t,bpp, transp = -1;
	unsigned char *datap;
	BOOL ok = TRUE;
			
	if(!PyArg_ParseTuple(args, "ss", &filename, &tofile))
		return NULL;

	if ((filep = fopen(filename, "rb")) == NULL)
	    RETURN_ERR("Cannot open file");
	
	
	lmap = GIFreadheader(filep,left,top,width,height,ncolors,
						aspect,interlaced,bpp,transp,ok);
	if ( lmap == NULL)
		return NULL;

	b2t = 0;
	rowlen = (width+3) & ~3;	// SGI images 32bit aligned
	
	if( (rv=PyString_FromStringAndSize(NULL, rowlen*height)) == NULL )
		return NULL;
	
	if(rv!=NULL)
	{
		char temp;
		datap = (unsigned char *)PyString_AsString(rv);
		
		if (GIFreadimage(filep, datap, width, height, 
			rowlen,interlaced) == 0) {
			Py_INCREF(Py_None);
			return Py_None;
		}
		
		long i,x,z = 0, y = 0;
				
		for(i=0;i<=y;i += rowlen)
		{
			y = rowlen*(height-1)-z*rowlen;
			for(x=0;x<rowlen;x++)
			{
				temp = datap[i+x];
				datap[i+x] = datap[y+x];
				datap[y+x] = temp;
			}
			z++;
		}

		for(i=13;i>=0;i--)
		{
			temp = datap[i];
			for(x=i;x<rowlen*height-1;x++)
			{
				datap[x] = datap[x+1];
			}
			datap[rowlen*height-1] = temp;
		}


	}
	else rv = Py_None;
		
	if ( filep != NULL )
		fclose(filep);

	BITMAPFILEHEADER    hdr;
	BITMAPINFOHEADER	bhdr;
	LPBITMAPFILEHEADER	lphdr = NULL;
	LPBITMAPINFOHEADER  lpbhdr = NULL;

	hdr.bfType          = BFT_BITMAP;
    hdr.bfSize          = (DWORD) (sizeof(BITMAPFILEHEADER) +rowlen*height+ ncolors * sizeof(RGBQUAD)+ sizeof(BITMAPINFOHEADER));
    hdr.bfReserved1     = 0;
    hdr.bfReserved2     = 0;
    hdr.bfOffBits       = (DWORD) (ncolors * sizeof(RGBQUAD)+ sizeof(BITMAPINFOHEADER));
	
	bhdr.biSize = (DWORD)sizeof(BITMAPINFOHEADER); 
	bhdr.biWidth = (LONG)rowlen; 
	bhdr.biHeight = (LONG)height; 
	bhdr.biPlanes = (WORD)1; 
	bhdr.biBitCount = (WORD)8;
	bhdr.biCompression = (DWORD)BI_RGB; 
	bhdr.biSizeImage = (DWORD)0; 
	bhdr.biXPelsPerMeter = (LONG)0; 
	bhdr.biYPelsPerMeter = (LONG)0; 
	bhdr.biClrUsed = (DWORD)0; 
	bhdr.biClrImportant = (DWORD)0; 

	lphdr = &hdr;
	lpbhdr = &bhdr;
	
	FILE* fil;
	if ((fil = fopen(tofile, "wb")) != NULL)
	{
		fwrite(lphdr, sizeof(BITMAPFILEHEADER),1,fil);
		fwrite(lpbhdr, sizeof(BITMAPINFOHEADER),1,fil);
		if (lmap != NULL)
			fwrite(lmap, sizeof(RGBQUAD), ncolors, fil);
		else 
		{
			fclose(fil);
			Py_INCREF(Py_None);
			return Py_None;
		}
		if (datap != NULL)
			fwrite((LPSTR)datap, sizeof(char),rowlen*height,fil);
		else 
		{
			fclose(fil);
			Py_INCREF(Py_None);
			return Py_None;
		}
		fclose(fil);
	}
		
	if ( lmap != NULL )
		free(lmap);
	
	return Py_BuildValue("i", 1);
}



static PyObject* py_gifex_TestGIF(PyObject *self, PyObject *args)
{
	char *filename;
	PyObject *tmp = Py_None;
	FILE *filep = NULL;
	RGBQUAD *lmap = NULL;
	int left,top,width,height,ncolors,aspect,interlaced,bpp,transp = -1;
	BOOL ok = TRUE;
			
	if(!PyArg_ParseTuple(args, "s", &filename))
		return NULL;

	if ((filep = fopen(filename, "rb")) == NULL)
		RETURN_ERR("Cannot open file");
	
	
	lmap = GIFreadheader(filep,left,top,width,height,ncolors,
						aspect,interlaced,bpp,transp,ok);
	
	if ( filep != NULL )
		fclose(filep);

		
	if ( lmap != NULL )
		free(lmap);
	
	if (ok)
	{
		tmp = Py_BuildValue("ii", 1, transp);
		return tmp;
	}
	else
	{
		tmp = Py_BuildValue("ii", 0, transp);
		return tmp;
	}
}


BEGIN_PYMETHODDEF(Gifex)
	{ "ReadGIF",	py_gifex_ReadGIF,	1},
	{ "TestGIF",	py_gifex_TestGIF,	1},
END_PYMETHODDEF()


DEFINE_PYMODULETYPE("PyGifex",Gifex);
