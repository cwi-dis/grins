#include <unistd.h>
#include <fcntl.h>
#include <stropts.h>
#include <poll.h>
#include "Python.h"
#include "modsupport.h"
#include "thread.h"
#include "mmmodule.h"
#include <sys/time.h>

/* these are inherited from the Makefile */
/* #define USE_GL			/* compile for use with GL */
/* #define USE_CL			/* support for Compression Library */
/* #define USE_XM			/* compile for use with X/Motif */

#ifdef USE_XM
#include "widgetobject.h"
#include "GCobject.h"
#include "XColor.h"
#endif
#ifdef USE_GL
#define X_H
#include <gl.h>			/* must come after the X include files */
#endif
#ifdef USE_CL
#include <cl.h>
#else
#error USE_CL must be defined
#endif

#ifdef MM_DEBUG
static int mpegchannel_debug = 0;
#define dprintf(args)	(mpegchannel_debug && printf args)
#else
#define dprintf(args)
#endif
#define denter(func)	dprintf(( # func "(%lx)\n", (long) self))

#define ERROR(func, errortype, msg)	{				   \
			dprintf((# func "(%lx): " msg "\n", (long) self)); \
			PyErr_SetString(errortype, msg);		   \
		    }


static int windowsystem;	/* which window system to use */
#define WIN_GL		1	/* only supported when USE_GL is defined */
#define WIN_X		2	/* only supported when USE_XM is defined */

/*
** All this stuff isn't needed, really, so ignore the next comment. It is
** always initialized to 24 bit RGBX. It is only kept here soa later X port
** can make use of it.
**
** The next three parameters are determined at init() time, in the following
** way:
** - On a 24bit machine, we ask cl for RGBX and display that in 24 bit RGBmode.
** - On an Entry with RGB332 support we ask for RGB332 and display that
**   in 8 bit RGB mode (this is a documented GL hack).
** - On any other machine we ask for RGB332 and display that in colormap
**   mode.
*/
int cl_format_wanted;
int rgb_mode;
int pixel_size;

static type_lock gl_lock;
extern type_lock getlocklock Py_PROTO((PyObject *));

struct mpeg_data {
	int m_width;		/* width of movie */
	int m_height;		/* height of movie */
	double m_scale;		/* movie scale (magnification) factor */
	PyObject *m_f;		/* file where movie comes from */
	int m_feof;		/* True if end-of-file */
	long m_timediff;	/* time between frames (millisecs) */
	char *m_frame;		/* one frame */
	CL_BufferHdl m_frameHdl; /* Handle to the above */
	char *m_inbuf;		/* The input buffer */
	CL_BufferHdl m_inbufHdl; /* Handle to the above */
	long m_bgcolor;		/* background color for window */
	CL_Handle m_decHdl;	/* decompressor for compressed movie */
#ifdef USE_GL
	int m_bgindex;		/* colormap index for background color */
#endif
#ifdef USE_XM
	XImage *m_image;	/* X image to put image in */
#endif
};
struct mpeg {
	int m_rect[4];		/* origin and size of window */
	int initial_clear_done;  /* True after initial clear */
	struct mpeg_data m_play; /* mpeg being played */
	struct mpeg_data m_arm; /* movie being armed */
	int m_pipefd[2];	/* pipe for synchronization with player */
#ifdef USE_GL
	int m_wid;		/* window ID */
#endif
#ifdef USE_XM
	GC m_gc;		/* graphics context to write images */
	Widget m_widget;	/* the window widget */
	Visual *m_visual;	/* the visual to use */
	int m_depth;		/* depth of the window */
#endif
};
#define X	0
#define Y	1
#define WIDTH	2
#define HEIGHT	3

#define PRIV	((struct mpeg *) self->mm_private)

/* Forward: */
static void mpeg_display_frame();

#ifdef USE_GL
static int
init_colormap(bgcolor)
    long bgcolor;
{
    int bgr, bgg, bgb;
    int r, g, b;
    int i;
    int diff, best_diff = 1000000, best_index = -1;

    bgr = bgcolor & 0xff;
    bgg = (bgcolor >> 8) & 0xff;
    bgb = (bgcolor >>16) & 0xff;
    for( i=0; i<256; i++) {
	/* Convert rrrbbggg to 3 8-bit values */
	r = (i >> 5) & 7;
	g = i & 7;
	b = (i >> 3) & 3;
	r = r * 255 / 7;
	g = g * 255 / 7;
	b = b * 255 / 3;
	/* See if it is the closest to the wanted background color */
	diff = abs(r-bgr) + abs(g-bgg) + abs(b-bgb);
	if ( diff < best_diff ) {
	    best_diff = diff;
	    best_index = i;
	}
	/* Map it */
	mapcolor(i, r, g, b);
    }
    gflush();	/* Send the updates to the X server */
    return best_index;
}
#endif /* USE_GL */

/*
** mpeg_free_old - Free all used fields in an mpeg_data struct.
*/
static void
mpeg_free_old(p, keepfile)
    struct mpeg_data *p;
{
    if ( !keepfile && p->m_f ){ Py_XDECREF(p->m_f); p->m_f = NULL; }
    if ( p->m_frameHdl ){ clDestroyBuf(p->m_frameHdl); p->m_frameHdl = NULL;}
    if ( p->m_frame )	{ free(p->m_frame); p->m_frame = NULL; }
    if ( p->m_inbufHdl ){ clDestroyBuf(p->m_inbufHdl); p->m_inbufHdl = NULL;}
    if ( p->m_decHdl )	{ clCloseDecompressor(p->m_decHdl); p->m_decHdl = NULL;}
#ifdef USE_XM
    if ( p->m_image )	{ XDestroyImage(p->m_image); p->m_image = NULL; }
#endif
}

static int
mpeg_init(self)
	mmobject *self;
{
	PyObject *v;

	denter(mpeg_init);
	self->mm_private = malloc(sizeof(struct mpeg));
	if (self->mm_private == NULL) {
		dprintf(("mpeg_init(%lx): malloc failed\n", (long) self));
		(void) PyErr_NoMemory();
		return 0;
	}
	bzero((char *)self->mm_private, sizeof(struct mpeg));
	if (pipe(PRIV->m_pipefd) < 0) {
		ERROR(mpeg_init, PyExc_RuntimeError, "cannot create pipe");
		goto error_return_no_close;
	}
#ifdef USE_GL
	PRIV->m_wid = -1;
	v = PyDict_GetItemString(self->mm_attrdict, "wid");
	if (v && PyInt_Check(v)) {
		if (windowsystem != 0 && windowsystem != WIN_GL) {
			ERROR(mpeg_init, PyExc_RuntimeError,
			      "cannot use two window systems simultaneously");
			goto error_return;
		}
		windowsystem = WIN_GL;
		PRIV->m_wid = PyInt_AsLong(v);
#ifndef sun_xyzzy
		v = PyDict_GetItemString(self->mm_attrdict, "gl_lock");
		if (v == NULL || (gl_lock = getlocklock(v)) == NULL) {
			ERROR(mpeg_init, PyExc_RuntimeError,
			      "no graphics lock specified\n");
			return 0;
		}
		dprintf(("mpeg_init(%lx): gl_lock = %lx\n",
			 (long) self, (long) gl_lock));
#endif
	}
#endif /* USE_GL */
#ifdef USE_XM
	v = PyDict_GetItemString(self->mm_attrdict, "widget");
	if (v && is_widgetobject(v)) {
		if (windowsystem != 0 && windowsystem != WIN_X) {
			ERROR(mpeg_init, PyExc_RuntimeError,
			      "cannot use two window systems simultaneously");
			goto error_return;
		}
		windowsystem = WIN_X;
		PRIV->m_widget = getwidgetvalue(v);
		v = PyDict_GetItemString(self->mm_attrdict, "gc");
		if (v && is_gcobject(v))
			PRIV->m_gc = PyGC_GetGC(v);
		else {
			ERROR(mpeg_init, PyExc_RuntimeError, "no gc specified");
			goto error_return;
		}
		v = PyDict_GetItemString(self->mm_attrdict, "visual");
		if (v && is_visualobject(v)) {
			XVisualInfo *vi = getvisualinfovalue(v);
			PRIV->m_visual = vi->visual;
			PRIV->m_depth = vi->depth;
		} else {
			ERROR(mpeg_init, PyExc_RuntimeError, "no visual specified");
			goto error_return;
		}
	}
#endif /* USE_XM */
	if (1
#ifdef USE_GL
	    && PRIV->m_wid < 0
#endif
#ifdef USE_XM
	    && PRIV->m_widget == NULL
#endif
	    ) {
		ERROR(mpeg_init, PyExc_RuntimeError, "no window specified");
		goto error_return;
	}
	v = PyDict_GetItemString(self->mm_attrdict, "rect");
	if (v && PyTuple_Check(v) && PyTuple_Size(v) == 4) {
		int i;
		PyObject *t;

		for (i = 0; i < 4; i++) {
			t = PyTuple_GetItem(v, i);
			if (!PyInt_Check(t)) {
				ERROR(mpeg_init, PyExc_RuntimeError, "bad size specification");
				goto error_return;
			}
			PRIV->m_rect[i] = PyInt_AsLong(t);
		}
	} else {
		ERROR(mpeg_init, PyExc_RuntimeError, "no size specified");
		goto error_return;
	}
	return 1;		/* normal return */

 error_return:
	(void) close(PRIV->m_pipefd[0]);
	(void) close(PRIV->m_pipefd[1]);
 error_return_no_close:
	free(self->mm_private);
	self->mm_private = NULL;
	return 0;
}

static void
mpeg_dealloc(self)
	mmobject *self;
{
	denter(mpeg_dealloc);
	if (self->mm_private == NULL)
		return;
	mpeg_free_old(&PRIV->m_play, 0);
	mpeg_free_old(&PRIV->m_arm, 0);
	(void) close(PRIV->m_pipefd[0]);
	(void) close(PRIV->m_pipefd[1]);
	free(self->mm_private);
	self->mm_private = NULL;
}


static int
mpeg_arm(self, file, delay, duration, attrdict, anchorlist)
	mmobject *self;
	PyObject *file;
	int delay, duration;
	PyObject *attrdict, *anchorlist;
{
	PyObject *v;
	char *format;
	PyObject *err_object = PyExc_RuntimeError;
        char *header;
	int headersize;
	int fd;
	CL_Handle decHandle;
	int cbufsize;
	int framesize;
	CL_BufferHdl bufHandle, frameHandle;
	char *inbuf;
	char *framebuf;


	denter(mpeg_arm);
	mpeg_free_old(&PRIV->m_arm, 0);

	/*
	** Get parameters passed from python: window-id, scale,
	** background color and the gl semaphore.
	*/
	v = PyDict_GetItemString(attrdict, "error");
	if (v && PyString_Check(v))
	  err_object = v;
	
	v = PyDict_GetItemString(attrdict, "scale");
	if (v && PyFloat_Check(v))
		PRIV->m_arm.m_scale = PyFloat_AsDouble(v);
	else {
		PyErr_SetString(PyExc_RuntimeError, "scale not specified");
		return 0;
	}
	v = PyDict_GetItemString(attrdict, "bgcolor");
	if (v && PyTuple_Check(v) && PyTuple_Size(v) == 3) {
		int i, c;
		PyObject *t;

		PRIV->m_arm.m_bgcolor = 0;
		for (i = 0; i < 3; i++) {
			t = PyTuple_GetItem(v, i);
			if (!PyInt_Check(t)) {
				PyErr_SetString(PyExc_RuntimeError, "bad color specification");
				return 0;
			}
			c = PyInt_AsLong(t);
			if (c < 0 || c > 255) {
				PyErr_SetString(PyExc_RuntimeError, "bad color specification");
				return 0;
			}
			PRIV->m_arm.m_bgcolor = (PRIV->m_arm.m_bgcolor << 8) | c;
		}
	} else {
		ERROR(mpeg_arm, PyExc_RuntimeError, "no background color specified");
		return 0;
	}
#ifdef USE_GL
	PRIV->m_arm.m_bgindex = -1;
#endif

	Py_XINCREF(file);
	PRIV->m_arm.m_f = file;
	/*
	** Read the MPEG file header and initialize the decompressor.
	** We do this here (in stead of in the armer thread) so we can
	** pass reasonable errors back to the CMIF mainline in case of errors
	** like unrecognized file type.
	*/
	fd = fileno(PyFile_AsFile(PRIV->m_arm.m_f));
	dprintf(("mpeg_arm(%lx): fd: %d\n", (long) self, fd));
	if ( (header=malloc(16)) == NULL ) {
	    ERROR(mpeg_arm, err_object, "not enough memory for header");
	    return 0;
	}
	lseek(fd, 0, SEEK_SET);
	headersize = read(fd, header, 16);
	if ( headersize != 16 ) {
	    ERROR(mpeg_arm, err_object, "cannot read header");
	    return 0;
	}
	if ( clQueryScheme(header) != CL_MPEG_VIDEO) {
	    ERROR(mpeg_arm, err_object, "Not an MPEG file");
	    return 0;
	}
	headersize = clQueryMaxHeaderSize(CL_MPEG_VIDEO);
	if ( (header=realloc(header, headersize)) == NULL ) {
	    ERROR(mpeg_arm, err_object, "not enough memory for header");
	    return 0;
	}
	headersize = read(fd, header+16, headersize-16) + 16;
	if ( headersize <= 16 ) {
	    ERROR(mpeg_arm, err_object, "cannot read header");
	    return 0;
	}
	clOpenDecompressor(CL_MPEG_VIDEO, &decHandle); /* XXXX Error chk */
	PRIV->m_arm.m_decHdl = decHandle;
	headersize = clReadHeader(decHandle, headersize, header); /* XXXX */
	dprintf(("mpeg_armer: headersize %d\n", headersize));
	free(header);
	lseek(fd, 0, SEEK_SET);

	/*
	** Get width/height/framerate, set rgb24 initialize buffering
	*/
        {
	    static int pbuf[][2] = {
	    { CL_IMAGE_WIDTH, 0},
	    { CL_IMAGE_HEIGHT, 0},
	    { CL_FRAME_RATE, 0},
	    { CL_COMPRESSED_BUFFER_SIZE, 0}};

	    clGetParams(decHandle, (int *)pbuf, sizeof(pbuf)/sizeof(int));
	    PRIV->m_arm.m_width = pbuf[0][1];
	    PRIV->m_arm.m_height = pbuf[1][1];
	    PRIV->m_arm.m_timediff = (int)(1000.0/CL_TypeIsFloat(pbuf[2][1]));
	    cbufsize = pbuf[3][1];
	}
        {
	    static int pbuf[][2] = {
		{ CL_ORIGINAL_FORMAT, CL_RGBX },
		{ CL_ORIENTATION, CL_BOTTOM_UP }};

	    framesize = PRIV->m_arm.m_width * PRIV->m_arm.m_height * sizeof(long);
#ifdef USE_XM
	    if (windowsystem == WIN_X) {
		if (PRIV->m_depth == 8) {
		    pbuf[0][1] = CL_RGB332;
		    framesize /= sizeof(long);
		}
		pbuf[1][1] = CL_TOP_DOWN;
	    }
#endif
	    clSetParams(decHandle, (int *)pbuf, sizeof(pbuf)/sizeof(int));
	}

	dprintf(("mpeg_arm: cbufsize=%d, dbufsize=%d\n", cbufsize, framesize));
	inbuf = malloc(cbufsize);
	framebuf = malloc(framesize);
	if ( inbuf == NULL || framebuf == NULL ) {
	    ERROR(mpeg_arm, err_object, "cannot allocate buffer");
	    mpeg_free_old(&PRIV->m_arm, 0);
	    return 0;
	}
	bufHandle = clCreateBuf(decHandle, CL_DATA, cbufsize, 1,
				(void **)&inbuf);
	frameHandle = clCreateBuf(decHandle, CL_FRAME, 1, framesize,
				  (void **)&framebuf);
	PRIV->m_arm.m_inbufHdl = bufHandle;
	PRIV->m_arm.m_inbuf = inbuf;
	PRIV->m_arm.m_frameHdl = frameHandle;
	PRIV->m_arm.m_frame = framebuf;
	PRIV->m_arm.m_decHdl = decHandle;
#ifdef USE_XM
	if (windowsystem == WIN_X) {
	    int depth = PRIV->m_depth == 8 ? 1 : 4;
	    PRIV->m_arm.m_image = XCreateImage(XtDisplay(PRIV->m_widget),
					       PRIV->m_visual,
					       PRIV->m_depth, ZPixmap, 0,
					       PRIV->m_arm.m_frame,
					       PRIV->m_arm.m_width,
					       PRIV->m_arm.m_height, depth * 8,
					       PRIV->m_arm.m_width * depth);
	}
#endif

	return 1;
}

static void
mpeg_armer(self)
	mmobject *self;
{
	denter(mpeg_armer);
#ifdef MM_DEBUG
	if ( PRIV->m_arm.m_inbufHdl || PRIV->m_arm.m_inbuf ||
	     PRIV->m_arm.m_frameHdl || PRIV->m_arm.m_frame )
	  dprintf(("mpeg_armer: PRIV->m_arm contains garbage\n"));
#endif

	PRIV->m_arm.m_feof = mpeg_fill_inbuffer(PRIV->m_arm.m_inbufHdl,
					fileno(PyFile_AsFile(PRIV->m_arm.m_f)));
	if ( !PRIV->m_arm.m_feof ) {
	    if ( clDecompress(PRIV->m_arm.m_decHdl, 1, 0, NULL, NULL) == FAILURE ) {
		printf("mpeg_armer: clDecompress failed\n");
		mpeg_free_old(&PRIV->m_arm, 0);
	    }
	}
}

static int
mpeg_play(self)
	mmobject *self;
{
	char c;

	denter(mpeg_play);
	mpeg_free_old(&PRIV->m_play, 0);
	PRIV->m_play = PRIV->m_arm;
	bzero((char *)&PRIV->m_arm, sizeof(PRIV->m_arm));
	if (PRIV->m_play.m_frame == NULL) {
		/* apparently the arm failed */
		ERROR(mpeg_play, PyExc_RuntimeError, "asynchronous arm failed");
		return 0;
	}
	/* empty the pipe */
	(void) fcntl(PRIV->m_pipefd[0], F_SETFL, FNDELAY);
	while (read(PRIV->m_pipefd[0], &c, 1) == 1)
		;
	(void) fcntl(PRIV->m_pipefd[0], F_SETFL, 0);

	switch (windowsystem) {
#ifdef USE_GL
	case WIN_GL:
		/* get the window size */
		/* DEBUG: should call:
		 * acquire_lock(gl_lock, WAIT_LOCK);
		 */
		winset(PRIV->m_wid);

		/* initialize window */
		winpop();		/* pop up the window */
		if ( rgb_mode )
			RGBmode();
		else {
			cmode();
			PRIV->m_play.m_bgindex = init_colormap(PRIV->m_play.m_bgcolor);
		}
		gconfig();
		if ( !PRIV->initial_clear_done ) {
			if ( rgb_mode )
				RGBcolor((PRIV->m_play.m_bgcolor >> 16) & 0xff,
					 (PRIV->m_play.m_bgcolor >>  8) & 0xff,
					 (PRIV->m_play.m_bgcolor      ) & 0xff);
			else
				color(PRIV->m_play.m_bgindex);
			clear();
			/*
			 ** Note: this is not correct in all cases. If a node
			 ** overrides the background color we should reset this
			 ** to 0 (but that's too much work for the moment).
			 */
			PRIV->initial_clear_done = 1;
		}
		pixmode(PM_SIZE, 32);
		/* DEBUG: should call:
		 * release_lock(gl_lock);
		 */
		break;
#endif /* USE_GL */
#ifdef USE_XM
	case WIN_X:
		/* clear the window */
		if ( !PRIV->initial_clear_done ) {
		    XFillRectangle(XtDisplay(PRIV->m_widget),
				   XtWindow(PRIV->m_widget), PRIV->m_gc, 0, 0,
				   PRIV->m_rect[WIDTH], PRIV->m_rect[HEIGHT]);
		    PRIV->initial_clear_done = 1;
		}
		break;
#endif /* USE_XM */
	}
	return 1;
}

static void
mpeg_player(self)
	mmobject *self;
{
	struct mpeg *mp = PRIV;
	struct timeval tm0, tm;
	long td;
	long timediff_actual, timediff_wanted;
	int fd;
	struct pollfd pollfd;
	int size, wrap, lastsize = 0;
	char *curdataptr;

	denter(mpeg_player);
	dprintf(("mpeg_player(%lx): width = %d, height = %d\n", (long) self, PRIV->m_play.m_width, PRIV->m_play.m_height));
	fd = fileno(PyFile_AsFile(PRIV->m_play.m_f));
	timediff_wanted = PRIV->m_play.m_timediff;
	while (1) {
	        /*
		** Remember the time and display the frame
		*/
	        if ( clQueryValid(PRIV->m_play.m_frameHdl, 1,
				  (void **)&curdataptr, &wrap) != 1 ) {
		    printf("mpeg_play: clQueryValid has no frames\n");
		    return;
		}
		if ( curdataptr != PRIV->m_play.m_frame ) {
		    printf("mpeg_play: clQueryValid returned wrong pointer\n");
		    return;
		}
		gettimeofday(&tm0, NULL);
		dprintf(("mpeg_player(%lx): writing image\n", (long) self));
		switch (windowsystem) {
#ifdef USE_GL
		case WIN_GL:
			acquire_lock(gl_lock, WAIT_LOCK);
			mpeg_display_frame(self);
			release_lock(gl_lock);
			break;
#endif
#ifdef USE_XM
		case WIN_X:
			my_qenter(self->mm_ev, 3);
			break;
#endif
		}
		clUpdateTail(PRIV->m_play.m_frameHdl, 1);
		dprintf(("mpeg_player: read/decode next\n"));

		/*
		** Ok, the data is on-screen. Refill the input buffer
		** and decode the next frame.
		*/
		if ( PRIV->m_play.m_feof ) {
		    /* EOF on input. Stop if buffer also empty */
		    size = clQueryValid(PRIV->m_play.m_inbufHdl, 1,
					(void **)&curdataptr, &wrap);
		    dprintf(("mpeg_player(%lx): valid: %d + %d\n", (long) self, size, wrap));
		    if ( size + wrap == 0 || wrap == 0 && size == lastsize )
		      break;
		    lastsize = size + wrap;
		} else {
		    PRIV->m_play.m_feof =
		      mpeg_fill_inbuffer(PRIV->m_play.m_inbufHdl, fd);
		}
		if ( clDecompress(PRIV->m_play.m_decHdl, 1, 0, NULL, NULL) ==
		     FAILURE ) {
		    printf("mpeg_player: clDecompress failed\n");
		    break;
		}

		/*
		** Check how much time (if any) we have before the next
		** frame is due, and sleep (while waiting for events from
		** the main thread).
		*/
		gettimeofday(&tm, NULL);
		timediff_actual = (tm.tv_sec-tm0.tv_sec)*1000 +
		  (tm.tv_usec-tm0.tv_usec)/1000;
		td = timediff_wanted - timediff_actual;
		if (td < 0)
			td = 0;
		pollfd.fd = PRIV->m_pipefd[0];
		pollfd.events = POLLIN;
		pollfd.revents = 0;
		dprintf(("mpeg_player(%lx): polling %d\n", (long) self, td));
		if (poll(&pollfd, 1, td) < 0) {
			perror("poll");
			break;
		}
		dprintf(("mpeg_player(%lx): polling done (%x)\n", (long) self, pollfd.revents));
		/*
		** Either the next event is due or we got a command from the
		** main thread. Check.
		*/
		if (pollfd.revents & POLLIN) {
			char c;

			dprintf(("pollin event!\n"));
			(void) read(PRIV->m_pipefd[0], &c, 1);
			dprintf(("mpeg_player(%lx): read %c\n", (long) self, c));
			if (c == 's') {
			    mpeg_free_old(&PRIV->m_play, 1);
			    break;
			}
			if (c == 'p') {
				struct timeval tm1;

				dprintf(("mpeg_player(%lx): waiting to continue\n", (long) self));
				(void) read(PRIV->m_pipefd[0], &c, 1);
				dprintf(("mpeg_player(%lx): continue playing, read %c\n", (long) self, c));
				gettimeofday(&tm0, NULL);
			}
		}
	}
}

static void
mpeg_display_frame(self)
    mmobject *self;
{
    int xorig, yorig;
    double scale;
    
    switch (windowsystem) {
#ifdef USE_GL
    case WIN_GL:
	scale = PRIV->m_play.m_scale;
	if (scale == 0) {
	    scale = PRIV->m_rect[WIDTH] / PRIV->m_play.m_width;
	    if (scale > PRIV->m_rect[HEIGHT] / PRIV->m_play.m_height)
		scale = PRIV->m_rect[HEIGHT] / PRIV->m_play.m_height;
	    if (scale < 1)
		scale = 1;
	}
	xorig = PRIV->m_rect[X] + (PRIV->m_rect[WIDTH] - PRIV->m_play.m_width * scale) / 2;
	yorig = PRIV->m_rect[Y] + (PRIV->m_rect[HEIGHT] - PRIV->m_play.m_height * scale) / 2;
	winset(PRIV->m_wid);
	pixmode(PM_SIZE, pixel_size);
	rectzoom(scale, scale);
	lrectwrite(xorig, yorig,
		   xorig + PRIV->m_play.m_width - 1,
		   yorig + PRIV->m_play.m_height - 1,
		   (unsigned long *)PRIV->m_play.m_frame);
	gflush();
	break;
#endif /* USE_GL */
#ifdef USE_XM
    case WIN_X:
	if (PRIV->m_play.m_image)
	    XPutImage(XtDisplay(PRIV->m_widget), XtWindow(PRIV->m_widget),
		      PRIV->m_gc, PRIV->m_play.m_image, 0, 0,
		      PRIV->m_rect[X] + (PRIV->m_rect[WIDTH] - PRIV->m_play.m_width) / 2,
		      PRIV->m_rect[Y] + (PRIV->m_rect[HEIGHT] - PRIV->m_play.m_height) / 2,
		      PRIV->m_play.m_width, PRIV->m_play.m_height);
	break;
#endif /* USE_XM */
    }
}

int
mpeg_fill_inbuffer(bufhdl, fd)
    CL_BufferHdl bufhdl;
    int fd;
{
    void *databuf;
    int wrap, n, first = 1;
    
    while (1) {
	n = clQueryFree(bufhdl, 0, &databuf, &wrap);
	dprintf(("mpeg_fill_inbuffer: wanted %d\n", n));
	if ( n <= 0 )
	  return 0;
	n = read(fd, databuf, n);
	if ( n > 0 ) {
	    clUpdateHead(bufhdl, n);
	    first = 0;
	} else {
	    dprintf(("mpeg_fill_inbuffer: eof\n"));
	    clDoneUpdatingHead(bufhdl);
	    return first;
	}
    }
}
	

static int
mpeg_resized(self, x, y, w, h)
	mmobject *self;
	int x, y, w, h;
{
	PRIV->m_rect[X] = x;
	PRIV->m_rect[Y] = y;
	PRIV->m_rect[WIDTH] = w;
	PRIV->m_rect[HEIGHT] = h;
	return 1;
}

static int
mpeg_armstop(self)
	mmobject *self;
{
	denter(mpeg_armstop);
	/* arming doesn't take long, so don't bother to actively stop it */
	return 1;
}

static int
mpeg_playstop(self)
	mmobject *self;
{
	denter(mpeg_playstop);
	if (write(PRIV->m_pipefd[1], "s", 1) < 0)
		perror("write");
	return 1;
}

static int
mpeg_finished(self)
	mmobject *self;
{
        int need_clear;

	/*
	** We don't need a clear if there's another node arming.
	*/
	need_clear = (PRIV->m_arm.m_decHdl == NULL);
	/* XXXX 405 CL bug workaround: see MpegChannel for details */
	/*need_clear = 0;*/
	if (need_clear) {
	    switch (windowsystem) {
#ifdef USE_GL
	    case WIN_GL:
		if (PRIV->m_wid >= 0) {
		    winset(PRIV->m_wid);
		    if (PRIV->m_play.m_bgindex >= 0)
			color(PRIV->m_play.m_bgindex);
		    else
			RGBcolor((PRIV->m_play.m_bgcolor >> 16) & 0xff,
				 (PRIV->m_play.m_bgcolor >>  8) & 0xff,
				 (PRIV->m_play.m_bgcolor      ) & 0xff);
		    clear();
		}
		break;
#endif /* USE_GL */
#ifdef USE_XM
	    case WIN_X:
		XFillRectangle(XtDisplay(PRIV->m_widget),
			       XtWindow(PRIV->m_widget), PRIV->m_gc,
			       PRIV->m_rect[X], PRIV->m_rect[Y],
			       PRIV->m_rect[WIDTH], PRIV->m_rect[HEIGHT]);
		break;
#endif /* USE_XM */
	    }
	}
	mpeg_free_old(&PRIV->m_play, 0);
	return 1;
}

static int
mpeg_setrate(self, rate)
	mmobject *self;
	double rate;
{
	char msg;

	denter(mpeg_setrate);
	if (rate == 0) {
		msg = 'p';
	} else {
		msg = 'r';
	}
	/* it can happen that the channel has already been stopped but the */
	/* player thread hasn't reacted yet.  Hence the check on STOPPLAY. */
	if ((self->mm_flags & (PLAYING | STOPPLAY)) == PLAYING) {
		dprintf(("mpeg_setrate(%lx): writing %c\n", (long) self, msg));
		if (write(PRIV->m_pipefd[1], &msg, 1) < 0)
			perror("write");
	}
	return 1;
}

static struct mmfuncs mpeg_channel_funcs = {
	mpeg_armer,
	mpeg_player,
	mpeg_resized,
	mpeg_arm,
	mpeg_armstop,
	mpeg_play,
	mpeg_playstop,
	mpeg_finished,
	mpeg_setrate,
	mpeg_init,
	mpeg_dealloc,
	mpeg_display_frame,
};

static channelobject *mpeg_chan_obj;

static void
mpegchannel_dealloc(self)
	channelobject *self;
{
	if (self != mpeg_chan_obj) {
		dprintf(("mpegchannel_dealloc: arg != mpeg_chan_obj\n"));
	}
	PyMem_DEL(self);
	mpeg_chan_obj = NULL;
}

static PyObject *
mpegchannel_getattr(self, name)
	channelobject *self;
	char *name;
{
	PyErr_SetString(PyExc_AttributeError, name);
	return NULL;
}

static PyTypeObject Mpegchanneltype = {
	PyObject_HEAD_INIT(&PyType_Type)
	0,			/*ob_size*/
	"channel:mpeg",	/*tp_name*/
	sizeof(channelobject),	/*tp_size*/
	0,			/*tp_itemsize*/
	/* methods */
	(destructor)mpegchannel_dealloc, /*tp_dealloc*/
	0,			/*tp_print*/
	(getattrfunc)mpegchannel_getattr, /*tp_getattr*/
	0,			/*tp_setattr*/
	0,			/*tp_compare*/
	0,			/*tp_repr*/
};

static PyObject *
mpegchannel_init(self, args)
	channelobject *self;
	PyObject *args;
{
	channelobject *p;

	if (!PyArg_NoArgs(args))
		return NULL;
	if (mpeg_chan_obj == NULL) {
		mpeg_chan_obj = PyObject_NEW(channelobject, &Mpegchanneltype);
		if (mpeg_chan_obj == NULL)
			return NULL;
		mpeg_chan_obj->chan_funcs = &mpeg_channel_funcs;
	} else {
		Py_INCREF(mpeg_chan_obj);
	}
	return (PyObject *) mpeg_chan_obj;
}

static PyMethodDef mpegchannel_methods[] = {
	{"init",		(PyCFunction)mpegchannel_init},
	{NULL,			NULL}
};

void
initmpegchannel()
{
	int nbr, nbg, nbb;
	char graphics_version[12]; /* gversion() output */
	int is_entry_indigo;

#ifdef MM_DEBUG
	mpegchannel_debug = getenv("MPEGDEBUG") != 0;
#endif
	dprintf(("initmpegchannel\n"));
	(void) Py_InitModule("mpegchannel", mpegchannel_methods);

	/* This always works: */
	cl_format_wanted = CL_RGBX;
	rgb_mode = 1;
	pixel_size = 32;
#ifdef NOTNEEDED
	/*
	** Determine format wanted.
	*/
	nbr = getgdesc(GD_BITS_NORM_SNG_RED);
	nbg = getgdesc(GD_BITS_NORM_SNG_GREEN);
	nbb = getgdesc(GD_BITS_NORM_SNG_BLUE);
	if ( nbr >= 8 && nbg >= 8 && nbb >= 8 ) {
	    /* It is at least a 24 bit machine. Fine. */
	    cl_format_wanted = CL_RGBX;
	    rgb_mode = 1;
	    pixel_size = 32;
	} else {
	    cl_format_wanted = CL_RGB332;
	    
	    (void) gversion(graphics_version);
	    is_entry_indigo = (getgdesc(GD_XPMAX) == 1024 &&
			       getgdesc(GD_YPMAX) == 768 &&
			       nbr == 3 && nbg == 3 && nbb == 2);
	    if ( is_entry_indigo &&
		           strcmp(graphics_version, "GL4DLG-4.0.") == 0 ) {
		/* Second-best: a 3:3:2 machine that can do 8bit rgb */
		rgb_mode = 1;
		pixel_size = 8;
	    } else {
		/* Worst: we have to use colormap mode */
		rgb_mode = 0;
		pixel_size = 8;
	    }
	}
	dprintf(("mpeg_init: format %d, rgb %d, size %d\n", cl_format_wanted, rgb_mode, pixel_size));
#endif
}
