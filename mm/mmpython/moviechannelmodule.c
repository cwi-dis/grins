#include <unistd.h>
#include <fcntl.h>
#include <stropts.h>
#include <poll.h>
#include "allobjects.h"
#include "modsupport.h"
#include "thread.h"
#include "mmmodule.h"
#include <sys/time.h>
#include <errno.h>

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
#endif

#ifdef MM_DEBUG
static int moviechannel_debug = 0;
#define dprintf(args)	(moviechannel_debug && printf args)
#else
#define dprintf(args)
#endif
#define denter(func)	dprintf(( # func "(%lx)\n", (long) self))
#define ERROR(func, errortype, msg)	{				\
		dprintf((# func "(%lx): " msg "\n", (long) self));	\
		err_setstr(errortype, msg);				\
		}


#define MAXMAP		(4096 - 256) /* max nr. of colormap entries to use */

/* formats of movie files */
#define FORMAT_RGB8	1
#define FORMAT_CL	2	/* only supported when USE_CL is defined */

static int windowsystem;	/* which window system to use */
#define WIN_GL		1	/* only supported when USE_GL is defined */
#define WIN_X		2	/* only supported when USE_XM is defined */

struct movie_data {
	int m_width;		/* width of movie */
	int m_height;		/* height of movie */
	int m_format;		/* format of movie */
#ifdef USE_XM
	XImage *m_image;	/* X image to put image in */
#endif
	int m_c0bits, m_c1bits, m_c2bits; /* # of bits for rgb colors */
	int m_moffset;		/* offset in colormap */
	double m_scale;		/* movie scale (magnification) factor */
	object *m_index;	/* cached movie index */
	object *m_f;		/* file where movie comes from */
	long m_offset;		/* offset in file before we go seeking */
	void *m_frame;		/* one frame */
	void *m_bframe;		/* one frame, converted to big format */
	int m_size;		/* size of frame */
	long m_bgcolor;		/* background color for window */
#ifdef USE_GL
	int m_bgindex;		/* colormap index for background color */
#endif
#ifdef USE_CL
	CL_Handle m_decomp;	/* decompressor for compressed movie */
	object *m_comphdr;	/* header info for compressed movie */
#endif
};
struct movie {
	int m_width, m_height;	/* width and height of window */
	struct movie_data m_play; /* movie being played */
	struct movie_data m_arm; /* movie being armed */
	int m_pipefd[2];	/* pipe for synchronization with player */
#ifdef USE_GL
	int m_wid;		/* window ID */
#endif
#ifdef USE_XM
	GC m_gc;		/* graphics context to write images */
	Widget m_widget;	/* the window widget */
	Visual *m_visual;	/* the visual to use */
#endif
};

#define PRIV	((struct movie *) self->mm_private)

#ifdef sun
#define CONVERT_32
#endif

#ifdef USE_GL
static char graphics_version[12]; /* gversion() output */
static int is_entry_indigo;	/* true iff we run on an Entry Indigo */
static int maxbits;		/* max # of bitplanes for color index */
static short colors[256][3];	/* saved color map entries */
static int colors_saved;	/* whether we've already saved the colors */
static int first_index;		/* used for restoring the colormap */
static type_lock gl_lock;	/* interlock of window system */
extern type_lock getlocklock PROTO((object *));
#ifdef CONVERT_32
static unsigned long cv_8_to_32[256];
#endif
#endif /* USE_GL */

static int nplaying;		/* number of instances playing */

static int
movie_init(self)
	mmobject *self;
{
	object *v;

	denter(movie_init);
	self->mm_private = malloc(sizeof(struct movie));
	if (self->mm_private == NULL) {
		dprintf(("movie_init(%lx): malloc failed\n", (long) self));
		(void) err_nomem();
		return 0;
	}
	if (pipe(PRIV->m_pipefd) < 0) {
		ERROR(movie_init, RuntimeError, "cannot create pipe");
		goto error_return_no_close;
	}
	PRIV->m_play.m_index = NULL;
	PRIV->m_arm.m_index = NULL;
	PRIV->m_play.m_frame = NULL;
	PRIV->m_arm.m_frame = NULL;
	PRIV->m_play.m_bframe = NULL;
	PRIV->m_arm.m_bframe = NULL;
	PRIV->m_play.m_f = NULL;
	PRIV->m_arm.m_f = NULL;
#ifdef USE_XM
	PRIV->m_widget = NULL;
	PRIV->m_gc = NULL;
	PRIV->m_visual = NULL;
	PRIV->m_play.m_image = NULL;
	PRIV->m_arm.m_image = NULL;
#endif
#ifdef USE_GL
	PRIV->m_wid = -1;
	v = dictlookup(self->mm_attrdict, "wid");
	if (v && is_intobject(v)) {
		if (windowsystem != 0 && windowsystem != WIN_GL) {
			ERROR(movie_init, RuntimeError,
			      "cannot use two window systems simultaneously");
			goto error_return;
		}
		if (windowsystem == 0) {
			/* initialize some globals */
			(void) gversion(graphics_version);
			is_entry_indigo = (getgdesc(GD_XPMAX) == 1024 &&
					   getgdesc(GD_YPMAX) == 768 &&
					   getgdesc(GD_BITS_NORM_SNG_RED) == 3 &&
					   getgdesc(GD_BITS_NORM_SNG_GREEN) == 3 &&
					   getgdesc(GD_BITS_NORM_SNG_BLUE) == 2);
			maxbits = getgdesc(GD_BITS_NORM_SNG_CMODE);
			if (maxbits > 11)
				maxbits = 11;
		}
		windowsystem = WIN_GL;
		PRIV->m_wid = getintvalue(v);
#ifndef sun_xyzzy
		v = dictlookup(self->mm_attrdict, "gl_lock");
		if (v == NULL || (gl_lock = getlocklock(v)) == NULL) {
			ERROR(movie_init, RuntimeError,
			      "no graphics lock specified\n");
			return 0;
		}
		dprintf(("movie_init(%lx): gl_lock = %lx\n",
			 (long) self, (long) gl_lock));
#endif
	}
#endif /* USE_GL */
#ifdef USE_XM
	v = dictlookup(self->mm_attrdict, "widget");
	if (v && is_widgetobject(v)) {
		if (windowsystem != 0 && windowsystem != WIN_X) {
			ERROR(movie_init, RuntimeError,
			      "cannot use two window systems simultaneously");
			goto error_return;
		}
		windowsystem = WIN_X;
		PRIV->m_widget = getwidgetvalue(v);
		v = dictlookup(self->mm_attrdict, "gc");
		if (v && is_gcobject(v))
			PRIV->m_gc = PyGC_GetGC(v);
		else {
			ERROR(movie_init, RuntimeError, "no gc specified");
			goto error_return;
		}
		v = dictlookup(self->mm_attrdict, "visual");
		if (v && is_visualobject(v))
			PRIV->m_visual = getvisualinfovalue(v)->visual;
		else {
			ERROR(movie_init, RuntimeError, "no visual specified");
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
		ERROR(movie_init, RuntimeError, "no window specified");
		goto error_return;
	}
#ifdef USE_CL
	PRIV->m_play.m_decomp = NULL;
	PRIV->m_arm.m_decomp = NULL;
	PRIV->m_play.m_comphdr = NULL;
	PRIV->m_arm.m_comphdr = NULL;
#endif
	return 1;

 error_return:
	(void) close(PRIV->m_pipefd[0]);
	(void) close(PRIV->m_pipefd[1]);
 error_return_no_close:
	free(self->mm_private);
	self->mm_private = NULL;
	return 0;
}

static int movie_finished PROTO((mmobject *));

static void
movie_free_old(p)
	struct movie_data *p;
{
	XDECREF(p->m_index);
	XDECREF(p->m_f);
#ifdef USE_XM
	if (p->m_image) {
		XDestroyImage(p->m_image);
		p->m_bframe = NULL;
	}
	p->m_image = NULL;
#endif /* USE_XM */
	if (p->m_frame)
		free(p->m_frame);
	p->m_frame = NULL;
	if (p->m_bframe)
		free(p->m_bframe);
	p->m_bframe = NULL;
#ifdef USE_CL
	if (p->m_decomp)
		clCloseDecompressor(p->m_decomp);
	p->m_decomp = NULL;
	XDECREF(p->m_comphdr);
	p->m_comphdr = NULL;
#endif /* USE_CL */
}

static void
movie_dealloc(self)
	mmobject *self;
{
	int i;

	denter(movie_dealloc);
	(void) movie_finished(self);
	movie_free_old(&PRIV->m_play);
	movie_free_old(&PRIV->m_arm);
	(void) close(PRIV->m_pipefd[0]);
	(void) close(PRIV->m_pipefd[1]);
	free(self->mm_private);
	self->mm_private = NULL;
}

#ifdef USE_GL
static void
conv_rgb8(double rgb, double d1, double d2, int *rp, int *gp, int *bp)
{
	int rgb_i = rgb * 255.0;

	*rp = ((rgb_i >> 5) & 0x07) / 7.0 * 255.0;
	*gp = ((rgb_i     ) & 0x07) / 7.0 * 255.0;
	*bp = ((rgb_i >> 3) & 0x03) / 3.0 * 255.0;
}

static void
init_colormap(self)
	mmobject *self;
{
	int c0, c1, c2;
	int c0bits = PRIV->m_play.m_c0bits;
	int c1bits = PRIV->m_play.m_c1bits;
	int maxc0, maxc1, maxc2;
	int r, g, b;
	int bgr, bgg, bgb;	/* background Red, Green, Blue */
	int d, dist = 3 * 256;	/* bigger than it can be */
	int index;
	int i;
	int offset = PRIV->m_play.m_moffset;
	double c0v, c1v, c2v;
	void (*convcolor)(double, double, double, int *, int *, int *);

	switch (PRIV->m_play.m_format) {
	case FORMAT_RGB8:
		if (PRIV->m_play.m_bframe) /* RGB mode; don't setup colormap */
			return;
		convcolor = conv_rgb8;
		break;
	case FORMAT_CL:
		return;		/* uses RGB mode */
	}

	denter(init_colormap);

	bgr = (PRIV->m_play.m_bgcolor >> 16) & 0xff;
	bgg = (PRIV->m_play.m_bgcolor >>  8) & 0xff;
	bgb = (PRIV->m_play.m_bgcolor      ) & 0xff;
	maxc0 = 1 << c0bits;
	maxc1 = 1 << c1bits;
	maxc2 = 1 << PRIV->m_play.m_c2bits;
	if (offset == 0 && maxbits == 11)
		offset = 2048;
	if (maxbits != 11)
		offset &= (1 << maxbits) - 1;
	i = 0;
	for (c0 = 0; c0 < maxc0; c0++) {
		c0v = c0 / (double) (maxc0 - 1);
		for (c1 = 0; c1 < maxc1; c1++) {
			if (maxc1 == 1)
				c1v = 0;
			else
				c1v = c1 / (double) (maxc1 - 1);
			for (c2 = 0; c2 < maxc2; c2++) {
				if (maxc2 == 1)
					c2v = 0;
				else
					c2v = c2 / (double) (maxc2 - 1);
				index = offset + c0 + (c1<<c0bits) +
					(c2 << (c0bits+c1bits));
				if (index < MAXMAP) {
					if (c0 == 0 && c1 == 0 && c2 == 0)
						first_index = index;
					(*convcolor)(c0v, c1v, c2v, &r, &g, &b);
					/*dprintf(("mapcolor(%d,%d,%d,%d)\n",
						 index, r, g, b));*/
					if (!colors_saved && i < 256)
						getmcolor(index, &colors[i][0],
							  &colors[i][1],
							  &colors[i][2]);
					i++;
					mapcolor(index, r, g, b);
					if (index == offset)
						color(index);

					/* find nearest color to background */
					d = abs(r - bgr) + abs(g - bgg) + abs(b - bgb);
					if (d < dist) {
						PRIV->m_play.m_bgindex = index;
						dist = d;
					}
				}
			}
		}
	}
	colors_saved = 1;
	gflush();
}
#endif /* USE_GL */

static int
movie_arm(self, file, delay, duration, attrdict, anchorlist)
	mmobject *self;
	object *file;
	int delay, duration;
	object *attrdict, *anchorlist;
{
	object *v;
	char *format;

	denter(movie_arm);
	XDECREF(PRIV->m_arm.m_index);
	PRIV->m_arm.m_index = NULL;
#ifdef USE_CL
	XDECREF(PRIV->m_arm.m_comphdr);
	PRIV->m_arm.m_comphdr = NULL;
#endif
	v = dictlookup(attrdict, "width");
	if (v && is_intobject(v))
		PRIV->m_arm.m_width = getintvalue(v);
	else {
		ERROR(movie_arm, RuntimeError, "no width specified");
		return 0;
	}
	v = dictlookup(attrdict, "height");
	if (v && is_intobject(v))
		PRIV->m_arm.m_height = getintvalue(v);
	else {
		ERROR(movie_arm, RuntimeError, "no height specified");
		return 0;
	}
	v = dictlookup(attrdict, "format");
	if (v && is_stringobject(v)) {
		format = getstringvalue(v);
		if (strcmp(format, "rgb8") == 0)
			PRIV->m_arm.m_format = FORMAT_RGB8;
#ifdef USE_CL
		else if (strcmp(format, "compress") == 0) {
			PRIV->m_arm.m_format = FORMAT_CL;
			v = dictlookup(attrdict, "compressheader");
			if (v && is_stringobject(v)) {
				PRIV->m_arm.m_comphdr = v;
				INCREF(v);
			} else {
				ERROR(movie_arm, RuntimeError,
				      "no compressheader specified");
				return 0;
			}
		}
#endif /* USE_CL */
		else {
			ERROR(movie_arm, RuntimeError, "unrecognized format");
			return 0;
		}
	} else {
		ERROR(movie_arm, RuntimeError, "no format specified");
		return 0;
	}
#ifdef USE_XM
	if (windowsystem == WIN_X) {
		if (PRIV->m_arm.m_image) {
			XDestroyImage(PRIV->m_arm.m_image);
			PRIV->m_arm.m_image = NULL;
			PRIV->m_arm.m_bframe = NULL;
		}
		if (PRIV->m_arm.m_bframe) {
			free(PRIV->m_arm.m_bframe);
			PRIV->m_arm.m_bframe = NULL;
		}
		PRIV->m_arm.m_size = PRIV->m_arm.m_width * PRIV->m_arm.m_height;
		PRIV->m_arm.m_bframe = malloc(PRIV->m_arm.m_size);
		if (PRIV->m_arm.m_bframe == NULL) {
			ERROR(movie_arm, RuntimeError, "malloc failed");
			return 0;
		}
		PRIV->m_arm.m_image = XCreateImage(XtDisplay(PRIV->m_widget),
						   PRIV->m_visual,
						   8, ZPixmap, 0,
						   PRIV->m_arm.m_bframe,
						   PRIV->m_arm.m_width,
						   PRIV->m_arm.m_height, 8, 0);
	}
#endif /* USE_XM */
	v = dictlookup(attrdict, "index");
	if (v && is_listobject(v)) {
		PRIV->m_arm.m_index = v;
		INCREF(v);
	} else {
		ERROR(movie_arm, RuntimeError, "no index specified");
		return 0;
	}
	v = dictlookup(attrdict, "c0bits");
	if (v && is_intobject(v))
		PRIV->m_arm.m_c0bits = getintvalue(v);
	else {
		ERROR(movie_arm, RuntimeError, "c0bits not specified");
		return 0;
	}
	v = dictlookup(attrdict, "c1bits");
	if (v && is_intobject(v))
		PRIV->m_arm.m_c1bits = getintvalue(v);
	else {
		ERROR(movie_arm, RuntimeError, "c1bits not specified");
		return 0;
	}
	v = dictlookup(attrdict, "c2bits");
	if (v && is_intobject(v))
		PRIV->m_arm.m_c2bits = getintvalue(v);
	else {
		ERROR(movie_arm, RuntimeError, "c2bits not specified");
		return 0;
	}
	v = dictlookup(attrdict, "offset");
	if (v && is_intobject(v))
		PRIV->m_arm.m_moffset = getintvalue(v);
	else {
		ERROR(movie_arm, RuntimeError, "offset not specified");
		return 0;
	}
	v = dictlookup(attrdict, "scale");
	if (v && is_floatobject(v))
		PRIV->m_arm.m_scale = getfloatvalue(v);
	else {
		ERROR(movie_arm, RuntimeError, "scale not specified");
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
				ERROR(movie_arm, RuntimeError,
				      "bad color specification");
				return 0;
			}
			c = getintvalue(t);
			if (c < 0 || c > 255) {
				ERROR(movie_arm, RuntimeError,
				      "bad color specification");
				return 0;
			}
			PRIV->m_arm.m_bgcolor = (PRIV->m_arm.m_bgcolor << 8) | c;
		}
	} else {
		ERROR(movie_arm, RuntimeError,
		      "no background color specified");
		return 0;
	}
#ifdef USE_GL
	PRIV->m_arm.m_bgindex = -1;
#endif
#ifdef MM_DEBUG
	if (PRIV->m_arm.m_index) {
		dprintf(("movie_arm(%lx): indexsize: %d\n",
			 (long) self, getlistsize(PRIV->m_arm.m_index)));
	}
#endif
	XDECREF(PRIV->m_arm.m_f);
	XINCREF(file);
	PRIV->m_arm.m_f = file;
	dprintf(("movie_arm(%lx): fd: %d\n",
		 (long) self, fileno(getfilefile(PRIV->m_arm.m_f))));
	return 1;
}

static void
movie_armer(self)
	mmobject *self;
{
	object *v, *t;
	long offset;
	int fd;
	int i;
	unsigned char *p;

	denter(movie_armer);
	if (PRIV->m_arm.m_frame) {
		free(PRIV->m_arm.m_frame);
		PRIV->m_arm.m_frame = NULL;
	}
#ifndef USE_XM
	if (windowsystem == WIN_X && PRIV->m_arm.m_bframe) {
		free(PRIV->m_arm.m_bframe);
		PRIV->m_arm.m_bframe = NULL;
	}
#endif
#ifdef USE_CL
	if (PRIV->m_arm.m_decomp) {
		clCloseDecompressor(PRIV->m_arm.m_decomp);
		PRIV->m_arm.m_decomp = NULL;
	}
#endif /* USE_CL */
	v = getlistitem(PRIV->m_arm.m_index, 0);
	if (v == NULL || !is_tupleobject(v) || gettuplesize(v) < 2) {
		dprintf(("movie_armer(%lx): index[0] not a proper tuple\n",
			 (long) self));
		return;
	}
	t = gettupleitem(v, 0);
	if (t == NULL || !is_tupleobject(t) || gettuplesize(t) < 1) {
		dprintf(("movie_armer(%lx): index[0][0] not a proper tuple\n",
			 (long) self));
		return;
	}
	t = gettupleitem(t, 1);
	if (t == NULL || !is_intobject(t)) {
		dprintf(("movie_armer(%lx): index[0][0][1] not an int\n",
			 (long) self));
		return;
	}
	PRIV->m_arm.m_size = getintvalue(t);
	t = gettupleitem(v, 1);
	if (t == NULL || !is_intobject(t)) {
		dprintf(("movie_armer(%lx): index[0][1] not an int\n",
			 (long) self));
		return;
	}
	offset = getintvalue(t);

#ifdef USE_CL
	if (PRIV->m_arm.m_format == FORMAT_CL) {
		int scheme;
		void *comphdr;
		int length;
		int params[6];

		length = getstringsize(PRIV->m_arm.m_comphdr);
		comphdr = getstringvalue(PRIV->m_arm.m_comphdr);
		scheme = clQueryScheme(comphdr);
		if (scheme < 0) {
			dprintf(("movie_armer: unknown compression scheme"));
			return;
		}
		if (clOpenDecompressor(scheme, &PRIV->m_arm.m_decomp) == FAILURE) {
			dprintf(("movie_armer: cannot open decompressor"));
			return;
		}
		(void) clReadHeader(PRIV->m_arm.m_decomp, length, comphdr);
		PRIV->m_arm.m_width = clGetParam(PRIV->m_arm.m_decomp,
						 CL_IMAGE_WIDTH);
		PRIV->m_arm.m_height = clGetParam(PRIV->m_arm.m_decomp,
						  CL_IMAGE_HEIGHT);
		params[0] = CL_ORIGINAL_FORMAT;
		params[2] = CL_ORIENTATION;
		params[4] = CL_FRAME_BUFFER_SIZE;
		switch (windowsystem) {
#ifdef USE_XM
		case WIN_X:
			params[1] = CL_RGB332;
			params[3] = CL_TOP_DOWN;
			break;
#endif
#ifdef USE_GL
		case WIN_GL:
			params[1] = CL_RGBX;
			params[3] = CL_BOTTOM_UP;
			break;
#endif
		default:
			abort();
		}
		params[5] = PRIV->m_arm.m_width * PRIV->m_arm.m_height * CL_BytesPerPixel(params[1]);
		if (PRIV->m_arm.m_bframe == NULL) { /* only for GL, really */
			PRIV->m_arm.m_bframe = malloc(params[5]);
			if (PRIV->m_arm.m_bframe == NULL) {
				dprintf(("movie_armer: malloc bframe failed"));
				return;
			}
		}
		clSetParams(PRIV->m_arm.m_decomp, params, 6);
	}
#endif /* USE_CL */

#ifdef USE_GL
	if (windowsystem == WIN_GL) {
		PRIV->m_arm.m_frame = malloc(PRIV->m_arm.m_size);
		if (PRIV->m_arm.m_frame == NULL) {
			dprintf(("movie_armer: malloc failed\n"));
			return;
		}
	}
#endif
	fd = fileno(getfilefile(PRIV->m_arm.m_f));
	PRIV->m_arm.m_offset = lseek(fd, 0L, SEEK_CUR);
	(void) lseek(fd, offset, SEEK_SET);
	switch (windowsystem) {
#ifdef USE_XM
	case WIN_X:
#ifdef USE_CL
		if (PRIV->m_arm.m_format == FORMAT_CL) {
			PRIV->m_arm.m_frame = malloc(PRIV->m_arm.m_size);
			if (PRIV->m_arm.m_frame == NULL) {
				dprintf(("movie_armer: malloc failed\n"));
				return;
			}
			if (read(fd, PRIV->m_arm.m_frame, PRIV->m_arm.m_size)
			    != PRIV->m_arm.m_size)
				dprintf(("movie_armer: read incorrect amount\n"));
		} else
#endif /* USE_CL */
		{
			/* read image upside down */
			p = (unsigned char *) PRIV->m_arm.m_bframe + PRIV->m_arm.m_size;
			for (i = PRIV->m_arm.m_height; i > 0; i--) {
				p -= PRIV->m_arm.m_width;
				read(fd, p, PRIV->m_arm.m_width);
			}
		}
		break;
#endif /* USE_XM */
#ifdef USE_GL
	case WIN_GL:
		if (read(fd, PRIV->m_arm.m_frame, PRIV->m_arm.m_size)
		    != PRIV->m_arm.m_size)
			dprintf(("movie_armer: read incorrect amount\n"));
#ifdef CONVERT_32
		if (PRIV->m_arm.m_format == FORMAT_RGB8) {
			unsigned long *lp;
			PRIV->m_arm.m_bframe = malloc(sizeof(long)*PRIV->m_arm.m_size);
			p = (unsigned char *) PRIV->m_arm.m_frame;
			lp = (unsigned long *) PRIV->m_arm.m_bframe;
			for (i = PRIV->m_arm.m_size; i > 0; i--)
				*lp++ = cv_8_to_32[*p++];
		}
#endif /* CONVERT_32 */
		break;
#endif /* USE_GL */
	default:
		abort();
	}

#ifdef USE_CL
	if (PRIV->m_arm.m_format == FORMAT_CL) {
		if (clDecompress(PRIV->m_arm.m_decomp, 1, PRIV->m_arm.m_size,
				 PRIV->m_arm.m_frame, PRIV->m_arm.m_bframe)
		    == FAILURE)
			dprintf(("movie_armer: decompress failed"));
	}
#endif /* USE_CL */
}

static int
movie_play(self)
	mmobject *self;
{
	char c;
	int i;

	denter(movie_play);
	XDECREF(PRIV->m_play.m_index);
	XDECREF(PRIV->m_play.m_f);
#ifdef USE_XM
	if (PRIV->m_play.m_image) {
		XDestroyImage(PRIV->m_play.m_image);
		PRIV->m_play.m_bframe = NULL;
	}
#endif
	if (PRIV->m_play.m_frame)
		free(PRIV->m_play.m_frame);
	if (PRIV->m_play.m_bframe)
		free(PRIV->m_play.m_bframe);
#ifdef USE_CL
	XDECREF(PRIV->m_play.m_comphdr);
	if (PRIV->m_play.m_decomp)
		clCloseDecompressor(PRIV->m_play.m_decomp);
#endif
	PRIV->m_play = PRIV->m_arm;
	PRIV->m_arm.m_index = NULL;
	PRIV->m_arm.m_frame = NULL;
	PRIV->m_arm.m_bframe = NULL;
	PRIV->m_arm.m_f = NULL;
#ifdef USE_CL
	PRIV->m_arm.m_comphdr = NULL;
	PRIV->m_arm.m_decomp = NULL;
#endif
#ifdef USE_XM
	PRIV->m_arm.m_image = NULL;
#endif
	if (PRIV->m_play.m_frame == NULL && PRIV->m_play.m_bframe == NULL) {
		/* apparently the arm failed */
		ERROR(movie_play, RuntimeError, "asynchronous arm failed");
		return 0;
	}
	/* empty the pipe */
	(void) fcntl(PRIV->m_pipefd[0], F_SETFL, O_NONBLOCK);
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
		{
			long width, height;

			getsize(&width, &height);
			PRIV->m_width = width;
			PRIV->m_height = height;
		}
		/* initialize color map */
		winpop();	/* pop up the window */
		if ((PRIV->m_play.m_format == FORMAT_RGB8 && is_entry_indigo &&
		     strcmp(graphics_version, "GL4DLG-4.0.") == 0) ||
		    PRIV->m_play.m_format == FORMAT_CL ||
		    PRIV->m_play.m_bframe) {
			/* only on entry-level Indigo running IRIX 4.0.5 */
			RGBmode();
			gconfig();
			RGBcolor((PRIV->m_play.m_bgcolor >> 16) & 0xff,
				 (PRIV->m_play.m_bgcolor >>  8) & 0xff,
				 (PRIV->m_play.m_bgcolor      ) & 0xff);
			clear();
			if (PRIV->m_play.m_bframe ||
			    PRIV->m_play.m_format == FORMAT_CL)
				pixmode(PM_SIZE, 32);
			else
				pixmode(PM_SIZE, 8);
		} else {
			cmode();
			gconfig();
			init_colormap(self);
			color(PRIV->m_play.m_bgindex);
			clear();
		}
		/* DEBUG: should call:
		 * release_lock(gl_lock);
		 */
		break;
#endif /* USE_GL */
#ifdef USE_XM
	case WIN_X:
		/* get the window size */
		{
			Dimension width, height;

			XtVaGetValues(PRIV->m_widget,
				      "width", &width, "height", &height,
				      NULL);
			PRIV->m_width = width;
			PRIV->m_height = height;
		}
		/* pop up the window */
		XRaiseWindow(XtDisplay(PRIV->m_widget),
			     XtWindow(PRIV->m_widget));
		/* clear the window */
		XFillRectangle(XtDisplay(PRIV->m_widget),
			       XtWindow(PRIV->m_widget), PRIV->m_gc, 0, 0,
			       PRIV->m_width, PRIV->m_height);
		break;
#endif /* USE_XM */
	default:
		abort();
	}
	nplaying++;		/* one more instance playing */
	return 1;
}

static void
movie_do_display(self)
	mmobject *self;
{
#ifdef USE_GL
	long xorig, yorig;
	double scale;
#endif

	denter(movie_do_display);
	switch (windowsystem) {
#ifdef USE_GL
	case WIN_GL:
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
		winset(PRIV->m_wid);
		rectzoom(scale, scale);
		if (PRIV->m_play.m_bframe) {
			pixmode(PM_SIZE, 32);
			lrectwrite(xorig, yorig,
				   xorig + PRIV->m_play.m_width - 1,
				   yorig + PRIV->m_play.m_height - 1,
				   PRIV->m_play.m_bframe);
		} else {
			pixmode(PM_SIZE, 8);
			if (PRIV->m_play.m_bgindex >= 0)
				writemask(0xff);
			lrectwrite(xorig, yorig,
				   xorig + PRIV->m_play.m_width - 1,
				   yorig + PRIV->m_play.m_height - 1,
				   PRIV->m_play.m_frame);
			if (PRIV->m_play.m_bgindex >= 0)
				writemask(0xffffffff);
		}
		gflush();
		break;
#endif /* USE_GL */
#ifdef USE_XM
	case WIN_X:
		if (PRIV->m_play.m_image)
			XPutImage(XtDisplay(PRIV->m_widget),
				  XtWindow(PRIV->m_widget),
				  PRIV->m_gc, PRIV->m_play.m_image, 0, 0,
				  (PRIV->m_width - PRIV->m_play.m_width) / 2,
				  (PRIV->m_height - PRIV->m_play.m_height) / 2,
				  PRIV->m_play.m_width, PRIV->m_play.m_height);
		break;
#endif /* USE_XM */
	default:
		abort();
	}
}

static void
movie_player(self)
	mmobject *self;
{
	struct movie *mp = PRIV;
	int index, lastindex, nplayed;
	struct timeval tm0, tm;
	long td;
	long timediff = 0;
	long newtime;
	long offset;
	int fd;
	object *v, *t0, *t;
	struct pollfd pollfd;
	int i;
	int size;
	unsigned char *p;

	denter(movie_player);
	dprintf(("movie_player(%lx): width = %d, height = %d\n",
		 (long) self, PRIV->m_play.m_width, PRIV->m_play.m_height));
	gettimeofday(&tm0, NULL);
	fd = fileno(getfilefile(PRIV->m_play.m_f));
	index = 0;
	lastindex = getlistsize(PRIV->m_play.m_index) - 1;
	nplayed = 0;
	while (index <= lastindex) {
		/*dprintf(("movie_player(%lx): writing image %d\n",
			 (long) self, index));*/
		switch (windowsystem) {
#ifdef USE_GL
		case WIN_GL:
			dprintf(("movie_player(%lx): window id = %d\n",
				 (long) self, PRIV->m_wid));
#ifdef sun_xyzzy
			my_qenter(self->mm_ev, 3);
#else
			if (gl_lock)
				acquire_lock(gl_lock, WAIT_LOCK);
			movie_do_display(self);
			if (gl_lock)
				release_lock(gl_lock);
#endif
			break;
#endif /* USE_GL */
#ifdef USE_XM
		case WIN_X:
#ifdef X_asynchronous_display
			if (gl_lock)
				acquire_lock(gl_lock, WAIT_LOCK);
			movie_do_display(self);
			if (gl_lock)
				release_lock(gl_lock);
#else
			my_qenter(self->mm_ev, 3);
#endif
			break;
#endif /* USE_XM */
		default:
			abort();
		}
		nplayed++;
		if (index == lastindex)
			break;
		gettimeofday(&tm, NULL);
		td = (tm.tv_sec - tm0.tv_sec) * 1000 +
			(tm.tv_usec - tm0.tv_usec) / 1000 - timediff;
		do {
			index++;
			v = getlistitem(PRIV->m_play.m_index, index);
			if (v == NULL || !is_tupleobject(v) || gettuplesize(v) < 2) {
				dprintf((
			"movie_player(%lx): index[%d] not a proper tuple\n",
					 (long) self, index));
				goto loop_exit;
			}
			t0 = gettupleitem(v, 0);
			if (t0 == NULL || !is_tupleobject(t0) || gettuplesize(t0) < 1) {
				dprintf((
			"movie_player(%lx): index[%d][0] not a proper tuple\n",
					 (long) self, index));
				goto loop_exit;
			}
			t = gettupleitem(t0, 0);
			if (t == NULL || !is_intobject(t)) {
				dprintf((
			"movie_player(%lx): index[%d][0][0] not an int\n",
					 (long) self, index));
				goto loop_exit;
			}
			newtime = getintvalue(t);
			/*dprintf(("movie_player(%lx): td = %d, newtime = %d\n",
				 (long) self, td, newtime));*/
		} while (index < lastindex && newtime <= td);
		t = gettupleitem(v, 1);
		if (t == NULL || !is_intobject(t)) {
			dprintf((
				"movie_player(%lx): index[%d][1] not an int\n",
				 (long) self, index));
			break;
		}
		offset = getintvalue(t);
		lseek(fd, offset, SEEK_SET);
		t = gettupleitem(t0, 1);
		if (t == NULL || !is_intobject(t)) {
			dprintf((
			"movie_player(%lx): index[%d][0][1] not an int\n",
				 (long) self, index));
			break;
		}
		size = getintvalue(t);
		if (PRIV->m_play.m_frame && size > PRIV->m_play.m_size) {
			PRIV->m_play.m_frame = realloc(PRIV->m_play.m_frame,
						       size);
			if (PRIV->m_play.m_frame == NULL) {
				dprintf(("movie_player(%lx): realloc failed\n",
					 (long) self));
				break;
			}
			PRIV->m_play.m_size = size;
		}
		switch (windowsystem) {
#ifdef USE_XM
		case WIN_X:
#ifdef USE_CL
			if (PRIV->m_play.m_format == FORMAT_CL) {
				if (read(fd, PRIV->m_play.m_frame, size)
				    != PRIV->m_play.m_size)
					dprintf((
				"movie_player: read incorrect amount\n"));
			} else
#endif
			{
				p = (unsigned char *) PRIV->m_play.m_bframe + PRIV->m_play.m_size;
				for (i = PRIV->m_play.m_height; i > 0; i--) {
					p -= PRIV->m_play.m_width;
					read(fd, p, PRIV->m_play.m_width);
				}
			}
			break;
#endif /* USE_XM */
#ifdef USE_GL
		case WIN_GL:
			if (read(fd, PRIV->m_play.m_frame, size) != size)
				dprintf((
				"movie_player: read incorrect amount\n"));
#ifdef CONVERT_32
			if (PRIV->m_play.m_format == FORMAT_RGB8) {
				unsigned long *lp;
				p = (unsigned char *) PRIV->m_play.m_frame;
				lp = (unsigned long *) PRIV->m_play.m_bframe;
				for (i = PRIV->m_play.m_size; i > 0; i--)
					*lp++ = cv_8_to_32[*p++];
			}
#endif
			break;
#endif /* USE_GL */
		default:
			abort();
		}
#ifdef USE_CL
		if (PRIV->m_play.m_format == FORMAT_CL) {
			(void) clDecompress(PRIV->m_play.m_decomp, 1, size,
					    PRIV->m_play.m_frame,
					    PRIV->m_play.m_bframe);
		}
#endif
		do {
			gettimeofday(&tm, NULL);
			td = (tm.tv_sec - tm0.tv_sec) * 1000 +
				(tm.tv_usec - tm0.tv_usec) / 1000 - timediff;
			td = newtime - td;
			/*dprintf(("movie_player(%lx): td = %d\n",
				 (long) self, td));*/
			if (td < 0)
				td = 0;
			pollfd.fd = PRIV->m_pipefd[0];
			pollfd.events = POLLIN;
			pollfd.revents = 0;
			dprintf(("movie_player(%lx): polling %d\n",
				 (long) self, td));
		} while (poll(&pollfd, 1, td) < 0 && errno == EINTR);
		dprintf(("movie_player(%lx): polling done\n", (long) self));
		if (pollfd.revents & POLLIN) {
			char c;

			dprintf(("pollin event!\n"));
			(void) read(PRIV->m_pipefd[0], &c, 1);
			dprintf(("movie_player(%lx): read %c\n",
				 (long) self, c));
			if (c == 's') {
#ifdef USE_XM
				if (PRIV->m_play.m_image) {
					XDestroyImage(PRIV->m_play.m_image);
					PRIV->m_play.m_image = NULL;
					PRIV->m_play.m_bframe = NULL;
				}
#endif
				if (PRIV->m_play.m_frame) {
					free(PRIV->m_play.m_frame);
					PRIV->m_play.m_frame = NULL;
				}
				if (PRIV->m_play.m_bframe) {
					free(PRIV->m_play.m_bframe);
					PRIV->m_play.m_bframe = NULL;
				}
				break;
			}
			if (c == 'p') {
				struct timeval tm1;

				gettimeofday(&tm, NULL);
				dprintf((
				"movie_player(%lx): waiting to continue\n",
					 (long) self));
				(void) read(PRIV->m_pipefd[0], &c, 1);
				dprintf((
			"movie_player(%lx): continue playing, read %c\n",
					 (long) self, c));
				gettimeofday(&tm1, NULL);
				timediff += (tm1.tv_sec - tm.tv_sec) * 1000 +
					(tm1.tv_usec - tm.tv_usec) / 1000;
			}
		}
	}
 loop_exit:
	printf("played %d out of %d frames\n", nplayed, lastindex + 1);
	lseek(fd, PRIV->m_play.m_offset, SEEK_SET);
}

static int
movie_resized(self)
	mmobject *self;
{
	denter(movie_resized);
	switch (windowsystem) {
#ifdef USE_GL
	case WIN_GL: {
		long width, height;

		if (gl_lock)
			acquire_lock(gl_lock, WAIT_LOCK);
		winset(PRIV->m_wid);
		getsize(&width, &height);
		PRIV->m_width = width;
		PRIV->m_height = height;
		dprintf(("movie_resized(%lx): size %d x %d\n", (long) self,
			 width, height));
		if (PRIV->m_play.m_frame) {
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
			movie_do_display(self);
		}
		if (gl_lock)
			release_lock(gl_lock);
		break;
	}
#endif /* USE_GL */
#ifdef USE_XM
	case WIN_X: {
		Dimension width, height;

		XtVaGetValues(PRIV->m_widget,
			      "width", &width, "height", &height, NULL);
		PRIV->m_width = width;
		PRIV->m_height = height;
		if (PRIV->m_play.m_image) {
			XFillRectangle(XtDisplay(PRIV->m_widget),
				       XtWindow(PRIV->m_widget), PRIV->m_gc,
				       0, 0, PRIV->m_width, PRIV->m_height);
			movie_do_display(self);
		}
		break;
	}
#endif /* USE_XM */
	default:
		abort();
	}
	return 1;
}

static int
movie_armstop(self)
	mmobject *self;
{
	denter(movie_armstop);
	/* arming doesn't take long, so don't bother to actively stop it */
	return 1;
}

static int
movie_playstop(self)
	mmobject *self;
{
	denter(movie_playstop);
	if (write(PRIV->m_pipefd[1], "s", 1) < 0)
		perror("write");
	return 1;
}

static int
movie_finished(self)
	mmobject *self;
{
	nplaying--;		/* one fewer instance playing */
	switch (windowsystem) {
#ifdef USE_GL
	case WIN_GL:
		winset(PRIV->m_wid);
		if (colors_saved && nplaying <= 0) {
			int i, index;

			for (i = 0, index = first_index; i < 256; i++, index++)
				mapcolor(index, colors[i][0], colors[i][1],
					 colors[i][2]);
		}
		RGBmode();
		gconfig();
		RGBcolor((PRIV->m_play.m_bgcolor >> 16) & 0xff,
			 (PRIV->m_play.m_bgcolor >>  8) & 0xff,
			 (PRIV->m_play.m_bgcolor      ) & 0xff);
		clear();
		if (PRIV->m_play.m_frame) {
			free(PRIV->m_play.m_frame);
			PRIV->m_play.m_frame = NULL;
		}
		if (PRIV->m_play.m_bframe) {
			free(PRIV->m_play.m_bframe);
			PRIV->m_play.m_bframe = NULL;
		}
		break;
#endif
#ifdef USE_XM
	case WIN_X:
		XFillRectangle(XtDisplay(PRIV->m_widget),
			       XtWindow(PRIV->m_widget), PRIV->m_gc,
			       0, 0, PRIV->m_width, PRIV->m_height);
		if (PRIV->m_play.m_image) {
			XDestroyImage(PRIV->m_play.m_image);
			PRIV->m_play.m_image = NULL;
			PRIV->m_play.m_bframe = NULL;
		}
		break;
#endif
	default:
		/* let it pass--initialization may have failed */
		break;
	}
	XDECREF(PRIV->m_play.m_index);
	PRIV->m_play.m_index = NULL;
	XDECREF(PRIV->m_play.m_f);
	PRIV->m_play.m_f = NULL;
	if (PRIV->m_play.m_frame) {
		free(PRIV->m_play.m_frame);
		PRIV->m_play.m_frame = NULL;
	}
	if (PRIV->m_play.m_bframe) {
		free(PRIV->m_play.m_bframe);
		PRIV->m_play.m_bframe = NULL;
	}
#ifdef USE_CL
	XDECREF(PRIV->m_play.m_comphdr);
	PRIV->m_play.m_comphdr = NULL;
	if (PRIV->m_play.m_decomp) {
		clCloseDecompressor(PRIV->m_play.m_decomp);
		PRIV->m_play.m_decomp = NULL;
	}
#endif
	return 1;
}

static int
movie_setrate(self, rate)
	mmobject *self;
	double rate;
{
	char msg;

	denter(movie_setrate);
	if (rate == 0) {
		msg = 'p';
	} else {
		msg = 'r';
	}
	/* it can happen that the channel has already been stopped but the */
	/* player thread hasn't reacted yet.  Hence the check on STOPPLAY. */
	if ((self->mm_flags & (PLAYING | STOPPLAY)) == PLAYING) {
		dprintf(("movie_setrate(%lx): writing %c\n",
			 (long) self, msg));
		if (write(PRIV->m_pipefd[1], &msg, 1) < 0)
			perror("write");
	}
	return 1;
}

static struct mmfuncs movie_channel_funcs = {
	movie_armer,
	movie_player,
	movie_resized,
	movie_arm,
	movie_armstop,
	movie_play,
	movie_playstop,
	movie_finished,
	movie_setrate,
	movie_init,
	movie_dealloc,
	movie_do_display,
};

static channelobject *movie_chan_obj;

static void
moviechannel_dealloc(self)
	channelobject *self;
{
	if (self != movie_chan_obj) {
		dprintf(("moviechannel_dealloc: arg != movie_chan_obj\n"));
	}
	DEL(self);
	movie_chan_obj = NULL;
}

static object *
moviechannel_getattr(self, name)
	channelobject *self;
	char *name;
{
	err_setstr(AttributeError, name);
	return NULL;
}

static typeobject Moviechanneltype = {
	OB_HEAD_INIT(&Typetype)
	0,			/*ob_size*/
	"channel:movie",	/*tp_name*/
	sizeof(channelobject),	/*tp_size*/
	0,			/*tp_itemsize*/
	/* methods */
	moviechannel_dealloc,	/*tp_dealloc*/
	0,			/*tp_print*/
	moviechannel_getattr,	/*tp_getattr*/
	0,			/*tp_setattr*/
	0,			/*tp_compare*/
	0,			/*tp_repr*/
};

static object *
moviechannel_init(self, args)
	channelobject *self;
	object *args;
{
	channelobject *p;

	if (!getnoarg(args))
		return NULL;
	if (movie_chan_obj == NULL) {
		movie_chan_obj = NEWOBJ(channelobject, &Moviechanneltype);
		if (movie_chan_obj == NULL)
			return NULL;
		movie_chan_obj->chan_funcs = &movie_channel_funcs;
	} else {
		INCREF(movie_chan_obj);
	}
	return (object *) movie_chan_obj;
}

static struct methodlist moviechannel_methods[] = {
	{"init",		moviechannel_init},
	{NULL,			NULL}
};

void
initmoviechannel()
{
	int r, g, b;

#ifdef MM_DEBUG
	moviechannel_debug = getenv("MOVIEDEBUG") != 0;
#endif
	dprintf(("initmoviechannel\n"));
	(void) initmodule("moviechannel", moviechannel_methods);
#if defined(USE_GL) && defined(CONVERT_32)
	for (r = 0; r < 8; r++) {
		int R = (int) ((double) r / 7.0 * 255.0);
		for (g = 0; g < 8; g++) {
			int G = (int) ((double) g / 7.0 * 255.0);
			for (b = 0; b < 4; b++) {
				int B = (int) ((double) b / 3.0 * 255.0);
				cv_8_to_32[(r<<5)|(b<<3)|(g)] =
					(B << 16) | (G << 8) | (R);
			}
		}
	}
#endif
}
