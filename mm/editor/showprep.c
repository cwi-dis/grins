/*
 * Superfast way to write an image to a window, once it is converted
 * to the format needed for lrectwrite by prepimg.
 */
#include <stdio.h>
#include <gl/gl.h>
#include <gl/device.h>
#include <gl/image.h>

int xsize, ysize;
unsigned long *parray;

main(argc,argv)
int argc;
char **argv;
{
    FILE *fp;
    int c;
    int dev;
    short val;
    if (argc < 2) {
	printf("usage: showprep infile [x y]\n");
	exit(1);
    } 
    if ((fp = fopen(argv[1], "r")) == NULL) {
	printf("showprep: can't open input file %s\n",argv[1]);
	exit(1);
    }
    if ((c = getc(fp)) == 'C') {
	    char buf[256];
	    int pf;
	    fgets(buf, sizeof buf, fp);
	    if (fscanf(fp, "(%d, %d, %d)\n", &xsize, &ysize, &pf) != 0) {
		    printf("showprep: bad CMIF input file %s\n", argv[1]);
		    exit(1);
	    }
	    if (pf != 0) {
		    printf("showprep: cannot show packed CMIF file\n");
		    exit(1);
	    }
	    fgets(buf, sizeof buf, fp);
    }
    else {
	ungetc(c, fp);
        if (fscanf(fp, "prepimg xsize=%d ysize=%d", &xsize, &ysize) != 2) {
	    printf("showprep: bad input file %s\n", argv[1]);
	    exit(1);
        }
	fseek(fp, 8192L, 0);
    }
    readit(fp);
    foreground();
    if (argc >= 4) {
	    int xorg, yorg;
	    xorg = atoi(argv[2]);
	    yorg = atoi(argv[3]);
	    prefposition(xorg, xorg + xsize - 1, yorg, yorg + ysize - 1);
    }
    else
	    prefsize(xsize, ysize);
    noborder();
    winopen("showprep");
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

readit(fp)
	FILE *fp;
{
	int fd;
	unsigned int n = xsize * ysize * sizeof(long);
	if ((parray = (unsigned long *) malloc(n)) == NULL) {
		fprintf(stderr, "showprep: cannot alloc %d bytes\n", n);
		exit(1);
	}
	fd = fileno(fp);
	if (read(fd, (char *)parray, n) != n) {
		perror("showprep: read");
		exit(1);
	}
}

drawit()
{
	reshapeviewport();
	viewport(0, xsize-1, 0, ysize-1);
	ortho2(-0.5, (float)xsize-0.5, -0.5, (float)ysize-0.5);
	lrectwrite(0, 0, xsize-1, ysize-1, parray);
}
