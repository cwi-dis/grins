/*
 * Convert an SGI image file to a format that is immediately usable
 * by lrectwrite.
 * The header of the file contains a description (in ASCII)
 * padded to 8196 byte for fast access of the rest of the file.
 *
 * Based upon "showimg.c" by Paul Haeberli.
 * --Guido van Rossum, CWI, Amsterdam
 */
#include <stdio.h>
#include <gl/gl.h>
#include <gl/device.h>
#include <gl/image.h>

unsigned short rs[8192];
unsigned short gs[8192];
unsigned short bs[8192];

IMAGE *image;
int xsize, ysize, zsize;
int ofd;

char header[100];

main(argc,argv)
int argc;
char **argv;
{
    FILE *fp;
    int y;
    if( argc != 3 ) {
	printf("usage: prepimg infile outfile\n");
	exit(1);
    } 
    if( (image=iopen(argv[1],"r")) == NULL ) {
	printf("prepimg: can't open input file %s\n",argv[1]);
	exit(1);
    }
    xsize = image->xsize;
    ysize = image->ysize;
    zsize = image->zsize;
    if ((fp = fopen(argv[2], "w")) == NULL) {
	printf("prepimg: can't open output file %s\n",argv[2]);
	exit(1);
    }
    fprintf(fp, "prepimg xsize=%d ysize=%d (zsize=%d==>3)\n",
	    xsize, ysize, zsize);
    fprintf(fp, "use lrectwrite(x, y, x+%d, y+%d, parray);\n",
	    xsize-1, ysize-1);
    fprintf(fp, "binary data for parray (%ld longs) follows at byte 8192\n",
	    (long)xsize * (long)ysize);
    fflush(fp);
    ofd = fileno(fp);
    lseek(ofd, 8192L, 0);
    for(y = 0; y < ysize; y++) {
		if(zsize<3) {
			getrow(image, rs, y, 0);
			writepacked(xsize, rs, rs, rs);
		} else {
			getrow(image, rs, y, 0);
			getrow(image, gs, y, 1);
			getrow(image, bs, y, 2);
			writepacked(xsize, rs, gs, bs);
		}
    }
    exit(0);
}

writepacked(n, rsptr, gsptr, bsptr)
	int n;
	short *rsptr, *gsptr, *bsptr;
{
	long parray[8192];
	long *pptr = parray;
	int i = n;
	while (--i >= 0) {
		*pptr++ = *rsptr++ | (*gsptr++<<8) | (*bsptr++<<16);
	}
	n *= sizeof(long);
	if (write(ofd, (char *) parray, n) != n) {
		perror("prepimg: write error (disk full?)");
		exit(1);
	}
}
