#include <unistd.h>
#include <fcntl.h>
#include <gl.h>
#include <stropts.h>
#include <poll.h>
#include "thread.h"
#include "allobjects.h"
#include "modsupport.h"
#include "mmmodule.h"
#include <sys/time.h>
#include <cl.h>

#ifdef MM_DEBUG
static int mpegchannel_debug = 0;
#define dprintf(args)	(mpegchannel_debug && printf args)
#else
#define dprintf(args)
#endif
#define denter(func)	dprintf(( # func "(%lx)\n", (long) self))



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
extern type_lock getlocklock PROTO((object *));

struct mpeg_data {
	int m_width;		/* width of movie */
	int m_height;		/* height of movie */
	int m_wid;		/* window ID */
	double m_scale;		/* movie scale (magnification) factor */
	object *m_f;		/* file where movie comes from */
	int m_feof;		/* True if end-of-file */
	long m_timediff;	/* time between frames (millisecs) */
	char *m_frame;		/* one frame */
	CL_BufferHdl m_frameHdl; /* Handle to the above */
	char *m_inbuf;		/* The input buffer */
	CL_BufferHdl m_inbufHdl; /* Handle to the above */
	long m_bgcolor;		/* background color for window */
	int m_bgindex;		/* colormap index for background color */
	CL_Handle m_decHdl;	/* decompressor for compressed movie */
};
struct mpeg {
	long m_width, m_height;	/* width and height of window */
	struct mpeg_data m_play; /* mpeg being played */
	struct mpeg_data m_arm; /* movie being armed */
	int m_pipefd[2];	/* pipe for synchronization with player */
};

#define PRIV	((struct mpeg *) self->mm_private)

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

/*
** mpeg_free_old - Free all used fields in an mpeg_data struct.
*/
static void
mpeg_free_old(p, keepfile)
    struct mpeg_data *p;
{
    if ( !keepfile && p->m_f ){ XDECREF(p->m_f); p->m_f = NULL; }
    if ( p->m_frameHdl ){ clDestroyBuf(p->m_frameHdl); p->m_frameHdl = NULL;}
    if ( p->m_frame )	{ free(p->m_frame); p->m_frame = NULL; }
    if ( p->m_inbufHdl ){ clDestroyBuf(p->m_inbufHdl); p->m_inbufHdl = NULL;}
    if ( p->m_decHdl )	{ clCloseDecompressor(p->m_decHdl); p->m_decHdl = NULL;}
}

static int
mpeg_init(self)
	mmobject *self;
{
	denter(mpeg_init);
	self->mm_private = malloc(sizeof(struct mpeg));
	if (self->mm_private == NULL) {
		dprintf(("mpeg_init(%lx): malloc failed\n", (long) self));
		(void) err_nomem();
		return 0;
	}
	bzero((char *)self->mm_private, sizeof(struct mpeg));
	if (pipe(PRIV->m_pipefd) < 0) {
		dprintf(("mpeg_init(%lx): cannot create pipe\n", (long) self));
		err_setstr(RuntimeError, "cannot create pipe");
		free(self->mm_private);
		self->mm_private = NULL;
		return 0;
	}
	PRIV->m_play.m_wid = -1;
	PRIV->m_arm.m_wid = -1;
	return 1;
}

static void
mpeg_dealloc(self)
	mmobject *self;
{
	int i;

	denter(mpeg_dealloc);
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
	object *file;
	int delay, duration;
	object *attrdict, *anchorlist;
{
	object *v;
	char *format;
	object *err_object = RuntimeError;
        char *header;
	int headersize;
	int fd;
	CL_Handle decHandle;


	denter(mpeg_arm);
	mpeg_free_old(&PRIV->m_arm, 0);

	/*
	** Get parameters passed from python: window-id, scale,
	** background color and the gl semaphore.
	*/
	v = dictlookup(attrdict, "error");
	if (v && is_stringobject(v))
	  err_object = v;
	
	v = dictlookup(attrdict, "wid");
	if (v && is_intobject(v))
		PRIV->m_arm.m_wid = getintvalue(v);
	else {
		err_setstr(RuntimeError, "no wid specified");
		return 0;
	}

	v = dictlookup(attrdict, "scale");
	if (v && is_floatobject(v))
		PRIV->m_arm.m_scale = getfloatvalue(v);
	else {
		err_setstr(RuntimeError, "scale not specified");
		return 0;
	}
	v = dictlookup(attrdict, "bgcolor");
	if (v && is_tupleobject(v) && gettuplesize(v) == 3) {
		int i, c;
		object *t;

		PRIV->m_arm.m_bgcolor = 0;
		for (i = 0; i < 3; i++) {
			t = gettupleitem(v, i);
			if (!is_intobject(t)) {
				err_setstr(RuntimeError, "bad color specification");
				return 0;
			}
			c = getintvalue(t);
			if (c < 0 || c > 255) {
				err_setstr(RuntimeError, "bad color specification");
				return 0;
			}
			PRIV->m_arm.m_bgcolor = (PRIV->m_arm.m_bgcolor << 8) | c;
		}
	} else {
		err_setstr(RuntimeError, "no background color specified");
		return 0;
	}
	PRIV->m_arm.m_bgindex = -1;
	v = dictlookup(attrdict, "gl_lock");
	if (v == NULL || (gl_lock = getlocklock(v)) == NULL) {
		err_setstr(RuntimeError, "no graphics lock specified");
		return 0;
	}
	dprintf(("mpeg_arm(%lx): gl_lock = %lx\n", (long) self, (long) gl_lock));

	XINCREF(file);
	PRIV->m_arm.m_f = file;
	dprintf(("mpeg_arm(%lx): fd: %d\n", (long) self, fileno(getfilefile(PRIV->m_arm.m_f))));
	/*
	** Read the MPEG file header and initialize the decompressor.
	** We do this here (in stead of in the armer thread) so we can
	** pass reasonable errors back to the CMIF mainline in case of errors
	** like unrecognized file type.
	*/
	fd = fileno(getfilefile(PRIV->m_arm.m_f));
	headersize = clQueryMaxHeaderSize(CL_MPEG_VIDEO);
	if ( (header=malloc(headersize)) == NULL ) {
	    err_setstr(err_object, "mpeg: not enough memory for header");
	    return 0;
	}
	lseek(fd, 0, SEEK_SET);
	headersize = read(fd, header, headersize);
	if ( headersize <= 0 ) {
	    err_setstr(err_object, "mpeg: cannot read header");
	    return 0;
	}
	clOpenDecompressor(CL_MPEG_VIDEO, &decHandle); /* XXXX Error chk */
	PRIV->m_arm.m_decHdl = decHandle;
	headersize = clReadHeader(decHandle, headersize, header); /* XXXX */
	if ( headersize <= 0 ) {
	    err_setstr(err_object, "mpeg: Not an MPEG file");
	    return 0;
	}
	dprintf(("mpeg_armer: headersize %d\n", headersize));
	free(header);
	lseek(fd, 0, SEEK_SET);

	return 1;
}

static void
mpeg_armer(self)
	mmobject *self;
{
	int cbufsize;
	int framesize;
	int fd;
	CL_Handle decHandle;
	CL_BufferHdl bufHandle, frameHandle;
	char *inbuf;
	char *framebuf;

	denter(mpeg_armer);

	fd = fileno(getfilefile(PRIV->m_arm.m_f));
	decHandle = PRIV->m_arm.m_decHdl;
#ifdef MM_DEBUG
	if ( PRIV->m_arm.m_inbufHdl || PRIV->m_arm.m_inbuf ||
	     PRIV->m_arm.m_frameHdl || PRIV->m_arm.m_frame )
	  dprintf(("mpeg_armer: PRIV->m_arm contains garbage\n"));
#endif

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

	    clSetParams(decHandle, (int *)pbuf, sizeof(pbuf)/sizeof(int));
	}

	framesize = PRIV->m_arm.m_width * PRIV->m_arm.m_height * sizeof(long);
	inbuf = malloc(cbufsize);
	framebuf = malloc(framesize);
	if ( inbuf == NULL || framebuf == NULL ) {
	    printf("mpeg_armer: cannot allocate buffer\n");
	    mpeg_free_old(&PRIV->m_arm, 0);
	    return;
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
	
	PRIV->m_arm.m_feof = mpeg_fill_inbuffer(bufHandle, fd);
	if( clDecompress(decHandle, 1, 0, NULL, NULL) != 1) {
	    dprintf(("mpeg_armer: clDecompress failed\n"));
	    mpeg_free_old(&PRIV->m_arm, 0);
	    return;
	}
}

static int
mpeg_play(self)
	mmobject *self;
{
	char c;
	int i;

	denter(mpeg_play);
	mpeg_free_old(&PRIV->m_play, 0);
	PRIV->m_play = PRIV->m_arm;
	bzero((char *)&PRIV->m_arm, sizeof(PRIV->m_arm));
	if (PRIV->m_play.m_frame == NULL) {
		/* apparently the arm failed */
		dprintf(("mpeg_play(%lx): not playing because arm failed\n", (long) self));
		err_setstr(RuntimeError, "asynchronous arm failed");
		return 0;
	}
	/* empty the pipe */
	(void) fcntl(PRIV->m_pipefd[0], F_SETFL, FNDELAY);
	while (read(PRIV->m_pipefd[0], &c, 1) == 1)
		;
	(void) fcntl(PRIV->m_pipefd[0], F_SETFL, 0);

	/* get the window size */
	/* DEBUG: should call:
	 * acquire_lock(gl_lock, WAIT_LOCK);
	 */
	winset(PRIV->m_play.m_wid);
	getsize(&PRIV->m_width, &PRIV->m_height);

	/* initialize window */
	winpop();		/* pop up the window */
	if ( rgb_mode )
	  RGBmode();
	else {
	    cmode();
	    PRIV->m_play.m_bgindex = init_colormap(PRIV->m_play.m_bgcolor);
	}
	gconfig();
	if ( rgb_mode )
	  RGBcolor((PRIV->m_play.m_bgcolor >> 16) & 0xff,
		   (PRIV->m_play.m_bgcolor >>  8) & 0xff,
		   (PRIV->m_play.m_bgcolor      ) & 0xff);
	else
	  color(PRIV->m_play.m_bgindex);
	clear();
	pixmode(PM_SIZE, 32);
	/* DEBUG: should call:
	 * release_lock(gl_lock);
	 */
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
	int i;
	int size, wrap;
	char *curdataptr;

	denter(mpeg_player);
	dprintf(("mpeg_player(%lx): width = %d, height = %d\n", (long) self, PRIV->m_play.m_width, PRIV->m_play.m_height));
	fd = fileno(getfilefile(PRIV->m_play.m_f));
	timediff_wanted = PRIV->m_play.m_timediff;
	while (1) {
	        /*
		** Remember the time and display the frame
		*/
	        if ( clQueryValid(PRIV->m_play.m_frameHdl, 1,
				  (void **)&curdataptr, &wrap) != 1 ) {
		    dprintf(("mpeg_play: clQueryValid has no frames\n"));
		    return;
		}
		if ( curdataptr != PRIV->m_play.m_frame ) {
		    dprintf(("mpeg_play: clQueryValid returned wrong pointer\n"));
		    return;
		}
		gettimeofday(&tm0, NULL);
		dprintf(("mpeg_player(%lx): writing image\n", (long) self));
		acquire_lock(gl_lock, WAIT_LOCK);
		winset(PRIV->m_play.m_wid);
		pixmode(PM_SIZE, pixel_size);
		mpeg_display_frame(&PRIV->m_play,
				   PRIV->m_width, PRIV->m_height);
		clUpdateTail(PRIV->m_play.m_frameHdl, 1);
		gflush();
		release_lock(gl_lock);
		dprintf(("mpeg_player: read/decode next\n"));

		/*
		** Ok, the data is on-screen. Refill the input buffer
		** and decode the next frame.
		*/
		if ( PRIV->m_play.m_feof ) {
		    /* EOF on input. Stop if buffer also empty */
		    size = clQueryValid(PRIV->m_play.m_inbufHdl, 1,
					(void **)&curdataptr, &wrap);
		    if ( size + wrap == 0 )
		      break;
		} else {
		    PRIV->m_play.m_feof =
		      mpeg_fill_inbuffer(PRIV->m_play.m_inbufHdl, fd);
		}
		if( clDecompress(PRIV->m_play.m_decHdl, 1, 0, NULL, NULL) != 1) {
		    dprintf(("mpeg_player: end of movie\n"));
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
		dprintf(("mpeg_player(%lx): polling done\n", (long) self));
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

void
mpeg_display_frame(p, w, h)
    struct mpeg_data *p;
{
    int xorig, yorig;
    double scale;
    
    scale = p->m_scale;
    if (scale == 0) {
	scale = w / p->m_width;
	if (scale > h / p->m_height)
	  scale = h / p->m_height;
	if (scale < 1)
	  scale = 1;
    }
    xorig = (w - p->m_width * scale) / 2;
    yorig = (w - p->m_height * scale) / 2;
    rectzoom(scale, scale);
    lrectwrite(xorig, yorig,
	       xorig + p->m_width - 1,
	       yorig + p->m_height - 1,
	       (unsigned long *)p->m_frame);

}

int
mpeg_fill_inbuffer(bufhdl, fd)
    CL_BufferHdl bufhdl;
    int fd;
{
    void *databuf;
    int wrap, n;
    
    while (1) {
	n = clQueryFree(bufhdl, 0, &databuf, &wrap);
	dprintf(("mpeg_fill_inbuffer: wanted %d\n", n));
	if ( n <= 0 )
	  return 0;
	n = read(fd, databuf, n);
	if ( n > 0 ) {
	    clUpdateHead(bufhdl, n);
	} else {
	    dprintf(("mpeg_fill_inbuffer: eof\n"));
	    clDoneUpdatingHead(bufhdl);
	    return 1;
	}
    }
}
	

static int
mpeg_resized(self)
	mmobject *self;
{
#if 0
	long xorig, yorig;
	double scale;

	if (PRIV->m_play.m_wid < 0)
		return 1;
	denter(mpeg_resized);
	getsize(&PRIV->m_width, &PRIV->m_height);
	if (PRIV->m_play.m_frame) {
		winset(PRIV->m_play.m_wid);
		if (PRIV->m_play.m_bframe == NULL)
			pixmode(PM_SIZE, 8);
		if (PRIV->m_play.m_bgindex >= 0) {
			color(PRIV->m_play.m_bgindex);
			clear();
			writemask(0xff);
		} else {
			RGBcolor((PRIV->m_play.m_bgcolor >> 16) & 0xff,
				 (PRIV->m_play.m_bgcolor >>  8) & 0xff,
				 (PRIV->m_play.m_bgcolor      ) & 0xff);
			clear();
		}
		scale = PRIV->m_play.m_scale;
		if (scale == 0) {
			scale = PRIV->m_width / PRIV->m_play.m_width;
			if (scale > PRIV->m_height / PRIV->m_play.m_height)
				scale = PRIV->m_height / PRIV->m_play.m_height;
			if (scale < 1)
				scale = 1;
		}
		xorig = (PRIV->m_width - PRIV->m_play.m_width * scale) / 2;
		yorig = (PRIV->m_height - PRIV->m_play.m_height * scale) / 2;
		rectzoom(scale, scale);
		if (PRIV->m_play.m_bframe)
			lrectwrite(xorig, yorig,
				   xorig + PRIV->m_play.m_width - 1,
				   yorig + PRIV->m_play.m_height - 1,
				   PRIV->m_play.m_bframe);
		else
			lrectwrite(xorig, yorig,
				   xorig + PRIV->m_play.m_width - 1,
				   yorig + PRIV->m_play.m_height - 1,
				   PRIV->m_play.m_frame);
		if (PRIV->m_play.m_bgindex >= 0)
			writemask(0xffffffff);
		gflush();
	}
#endif
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
	if (PRIV->m_play.m_wid >= 0) {
		winset(PRIV->m_play.m_wid);
		if (PRIV->m_play.m_bgindex >= 0)
			color(PRIV->m_play.m_bgindex);
		else
			RGBcolor((PRIV->m_play.m_bgcolor >> 16) & 0xff,
				 (PRIV->m_play.m_bgcolor >>  8) & 0xff,
				 (PRIV->m_play.m_bgcolor      ) & 0xff);
		clear();
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
};

static channelobject *mpeg_chan_obj;

static void
mpegchannel_dealloc(self)
	channelobject *self;
{
	if (self != mpeg_chan_obj) {
		dprintf(("mpegchannel_dealloc: arg != mpeg_chan_obj\n"));
	}
	DEL(self);
	mpeg_chan_obj = NULL;
}

static object *
mpegchannel_getattr(self, name)
	channelobject *self;
	char *name;
{
	err_setstr(AttributeError, name);
	return NULL;
}

static typeobject Mpegchanneltype = {
	OB_HEAD_INIT(&Typetype)
	0,			/*ob_size*/
	"channel:mpeg",	/*tp_name*/
	sizeof(channelobject),	/*tp_size*/
	0,			/*tp_itemsize*/
	/* methods */
	mpegchannel_dealloc,	/*tp_dealloc*/
	0,			/*tp_print*/
	mpegchannel_getattr,	/*tp_getattr*/
	0,			/*tp_setattr*/
	0,			/*tp_compare*/
	0,			/*tp_repr*/
};

static object *
mpegchannel_init(self, args)
	channelobject *self;
	object *args;
{
	channelobject *p;

	if (!getnoarg(args))
		return NULL;
	if (mpeg_chan_obj == NULL) {
		mpeg_chan_obj = NEWOBJ(channelobject, &Mpegchanneltype);
		if (mpeg_chan_obj == NULL)
			return NULL;
		mpeg_chan_obj->chan_funcs = &mpeg_channel_funcs;
	} else {
		INCREF(mpeg_chan_obj);
	}
	return mpeg_chan_obj;
}

static struct methodlist mpegchannel_methods[] = {
	{"init",		mpegchannel_init},
	{NULL,			NULL}
};

void
initmpegchannel()
{
	int i, nbr, nbg, nbb;
	char graphics_version[12]; /* gversion() output */
	int is_entry_indigo;

#ifdef MM_DEBUG
	mpegchannel_debug = getenv("MPEGDEBUG") != 0;
#endif
	dprintf(("initmpegchannel\n"));
	(void) initmodule("mpegchannel", mpegchannel_methods);

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
