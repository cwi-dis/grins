/*
 *	showimg - 
 *		Display a color or black and white image on the iris.  Simple
 *	version for demo use.  This will only work on machines that support
 *	RGB mode.
 *	  		   	Paul Haeberli - 1988
 *
 *	changed for use from Python --Guido
 */
#include <stdio.h>
#include <gl/gl.h>
#include <gl/device.h>
#include <gl/image.h>

unsigned short rs[8192];
unsigned short gs[8192];
unsigned short bs[8192];

unsigned char rb[8192];
unsigned char gb[8192];
unsigned char bb[8192];

short colorbuff[4096]; 
IMAGE *image;
int x, y, xsize, ysize, zsize;

main(argc,argv)
int argc;
char **argv;
{
    int dev;
    short val;
    if( argc<2 ) {
	printf("usage: showimg infile [x y]\n");
	exit(1);
    } 
    if( (image=iopen(argv[1],"r")) == NULL ) {
	printf("showimg: can't open input file %s\n",argv[1]);
	exit(1);
    }
    xsize = image->xsize;
    ysize = image->ysize;
    zsize = image->zsize;
    if( xsize > (XMAXSCREEN+1) || ysize > (YMAXSCREEN+1)) {
	printf("showimg: input image is too big %d %d",xsize,ysize);
	exit(1);
    }
    foreground();
    if (argc >= 4) {
	    int xorg, yorg;
	    xorg = atoi(argv[2]);
	    yorg = atoi(argv[3]);
	    prefposition(xorg, xorg + xsize, yorg, yorg + ysize);
    }
    else
	    prefsize(xsize,ysize);
    noborder();
    winopen("showimg");
    RGBmode();
    gconfig();
    qdevice(ESCKEY);
    qdevice(WINSHUT);
    drawit();
    printf("%d\n", getpid());
    fflush(stdout);
    while(1) {
	if((dev = qread(&val)) == REDRAW)
	    drawit();
	else if (dev == ESCKEY || dev == WINSHUT)
	    break;
    }
}

drawit()
{
    reshapeviewport();
    viewport(0,xsize-1,0,ysize-1);
    ortho2(-0.5,(float)xsize-0.5,-0.5,(float)ysize-0.5);
    for(y=0; y<ysize; y++) {
	if(zsize<3) {
	    getrow(image,rs,y,0);
	    compress(rs,rb,xsize);
	    cmov2i(0,y);
	    writeRGB(xsize,rb,rb,rb); 
	} else {
	    getrow(image,rs,y,0);
	    compress(rs,rb,xsize);
	    getrow(image,gs,y,1);
	    compress(gs,gb,xsize);
	    getrow(image,bs,y,2);
	    compress(bs,bb,xsize);
	    cmov2i(0,y);
	    writeRGB(xsize,rb,gb,bb); 
	}
    }
}

compress(sptr,bptr,n)
register unsigned short *sptr;
register unsigned char *bptr;
short n;
{
    while(n--) 
	*bptr++ = *sptr++;
}
