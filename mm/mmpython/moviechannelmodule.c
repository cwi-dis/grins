#include <unistd.h>
#include <fcntl.h>
#include <stropts.h>
#include <poll.h>
#include "Python.h"
#include "modsupport.h"
#include "pythread.h"
#include "pysema.h"
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
		PyErr_SetString(errortype, msg);			\
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
	PyObject *m_index;	/* cached movie index */
	PyObject *m_f;		/* file where movie comes from */
	long m_offset;		/* offset in file before we go seeking */
	void *m_frame;		/* one frame */
	void *m_bframe;		/* one frame, converted to big format */
	int m_size;		/* size of input frame */
	long m_bgcolor;		/* background color for window */
#ifdef USE_GL
	int m_bgindex;		/* colormap index for background color */
#endif
#ifdef USE_CL
	CL_Handle m_decomp;	/* decompressor for compressed movie */
	PyObject *m_comphdr;	/* header info for compressed movie */
#endif
	int m_planes;		/* depth of the window in bits per pixel */
	int m_depth;		/* depth of the window in bytes per pixel */
};
struct movie {
	int m_rect[4];		/* origin and size of window */
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
	PyThread_type_sema m_dispsema;	/* semaphore for display synchronization */
};
#define X	0
#define Y	1
#define WIDTH	2
#define HEIGHT	3

#define PRIV	((struct movie *) self->mm_private)

#ifdef USE_GL
static char graphics_version[12]; /* gversion() output */
static int is_entry_indigo;	/* true iff we run on an Entry Indigo */
static int maxbits;		/* max # of bitplanes for color index */
static short colors[256][3];	/* saved color map entries */
static int colors_saved;	/* whether we've already saved the colors */
static int first_index;		/* used for restoring the colormap */
static PyThread_type_lock gl_lock;	/* interlock of window system */
extern PyThread_type_lock getlocklock Py_PROTO((PyObject *));
#endif /* USE_GL */

static unsigned long cv_8_to_32[256];

static int nplaying;		/* number of instances playing */

#ifdef USE_XM
static unsigned char cv_8_to_8[256];
static int cv_8_to_8_inited;

static void
colormask(mask, shiftp, maskp)
	unsigned long mask;
	int *shiftp;
	unsigned long *maskp;
{
	unsigned long shift = 0, width = 0;

	while ((mask & 1) == 0) {
		shift++;
		mask >>= 1;
	}
	while (mask != 0) {
		width++;
		mask >>= 1;
	}
	*shiftp = shift;
	*maskp = (1 << width) - 1;
}

static void
mkcolormap(rs, rm, gs, gm, bs, bm)
	int rs, gs, bs;
	unsigned long rm, gm, bm;
{
	int n;
	int r, g, b;

	if (rm != 7 || gm != 7 || bm != 3) {
		for (n = 0; n < 256; n ++) {
			r = ((n >> 5) & 7) / 7. * rm + .5;
			g = ((n     ) & 7) / 7. * gm + .5;
			b = ((n >> 3) & 3) / 3. * bm + .5;
			cv_8_to_8[n] = (r << rs) | (g << gs) | (b << bs);
		}
		cv_8_to_8_inited = 1;
	} else if (rs != 5 || gs != 0 || bs != 3) {
		for (n = 0; n < 256; n ++) {
			r = (n >> 5) & 7;
			g = (n     ) & 7;
			b = (n >> 3) & 3;
			cv_8_to_8[n] = (r << rs) | (g << gs) | (b << bs);
		}
		cv_8_to_8_inited = 1;
	}
}
#endif /* USE_XM */

static int
movie_init(self)
	mmobject *self;
{
	PyObject *v;

	denter(movie_init);
	self->mm_private = malloc(sizeof(struct movie));
	if (self->mm_private == NULL) {
		dprintf(("movie_init(%lx): malloc failed\n", (long) self));
		(void) PyErr_NoMemory();
		return 0;
	}
	if ((PRIV->m_dispsema = PyThread_allocate_sema(0)) == NULL) {
		ERROR(movie_init, PyExc_RuntimeError, "cannot create semaphore");
		goto error_return_no_close;
	}
	if (pipe(PRIV->m_pipefd) < 0) {
		ERROR(movie_init, PyExc_RuntimeError, "cannot create pipe");
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
	v = PyDict_GetItemString(self->mm_attrdict, "wid");
	if (v && PyInt_Check(v)) {
		if (windowsystem != 0 && windowsystem != WIN_GL) {
			ERROR(movie_init, PyExc_RuntimeError,
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
		PRIV->m_wid = PyInt_AsLong(v);
#ifndef sun_xyzzy
		v = PyDict_GetItemString(self->mm_attrdict, "gl_lock");
		if (v == NULL || (gl_lock = getlocklock(v)) == NULL) {
#if 0
			ERROR(movie_init, PyExc_RuntimeError,
			      "no graphics lock specified\n");
			return 0;
#endif
		}
		dprintf(("movie_init(%lx): gl_lock = %lx\n",
			 (long) self, (long) gl_lock));
#endif
#ifdef sun
		PRIV->m_arm.m_planes = 24;
		PRIV->m_arm.m_depth = 4;
#else
		PRIV->m_arm.m_planes = 8;
		PRIV->m_arm.m_depth = 1;
#endif
	}
#endif /* USE_GL */
#ifdef USE_XM
	v = PyDict_GetItemString(self->mm_attrdict, "widget");
	if (v && is_widgetobject(v)) {
		if (windowsystem != 0 && windowsystem != WIN_X) {
			ERROR(movie_init, PyExc_RuntimeError,
			      "cannot use two window systems simultaneously");
			goto error_return;
		}
		windowsystem = WIN_X;
		PRIV->m_widget = getwidgetvalue(v);
		v = PyDict_GetItemString(self->mm_attrdict, "gc");
		if (v && is_gcobject(v))
			PRIV->m_gc = PyGC_GetGC(v);
		else {
			ERROR(movie_init, PyExc_RuntimeError, "no gc specified");
			goto error_return;
		}
		v = PyDict_GetItemString(self->mm_attrdict, "visual");
		if (v && is_visualobject(v)) {
			XVisualInfo *vptr = getvisualinfovalue(v);
			PRIV->m_visual = vptr->visual;
			PRIV->m_arm.m_planes = vptr->depth;
			if (vptr->depth == 8) {
				unsigned long rm, gm, bm;
				int rs, gs, bs;
				colormask(vptr->red_mask, &rs, &rm);
				colormask(vptr->green_mask, &gs, &gm);
				colormask(vptr->blue_mask, &bs, &bm);
				mkcolormap(rs, rm, gs, gm, bs, bm);
			}
		} else {
			ERROR(movie_init, PyExc_RuntimeError, "no visual specified");
			goto error_return;
		}
		switch (PRIV->m_arm.m_planes) {
		case 8:
			PRIV->m_arm.m_depth = 1;
			break;
		case 24:
			PRIV->m_arm.m_depth = 4;
			break;
		default:
			ERROR(movie_init, PyExc_RuntimeError,
			      "unsupported visual depth");
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
		ERROR(movie_init, PyExc_RuntimeError, "no window specified");
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
#ifdef USE_CL
	PRIV->m_play.m_decomp = NULL;
	PRIV->m_arm.m_decomp = NULL;
	PRIV->m_play.m_comphdr = NULL;
	PRIV->m_arm.m_comphdr = NULL;
#endif
	PRIV->m_play.m_planes = PRIV->m_arm.m_planes;
	PRIV->m_play.m_depth = PRIV->m_arm.m_depth;
	return 1;

 error_return:
	(void) close(PRIV->m_pipefd[0]);
	(void) close(PRIV->m_pipefd[1]);
 error_return_no_close:
	if (PRIV->m_dispsema)
		PyThread_free_sema(PRIV->m_dispsema);
	free(self->mm_private);
	self->mm_private = NULL;
	return 0;
}

static int movie_finished Py_PROTO((mmobject *));

static void
movie_free_old(p)
	struct movie_data *p;
{
	Py_XDECREF(p->m_index);
	p->m_index = NULL;
	Py_XDECREF(p->m_f);
	p->m_f = NULL;
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
	Py_XDECREF(p->m_comphdr);
	p->m_comphdr = NULL;
#endif /* USE_CL */
}

static void
movie_dealloc(self)
	mmobject *self;
{
	int i;

	denter(movie_dealloc);
	if (self->mm_private == NULL)	/* apparantly not initialized yet */
		return;
	movie_free_old(&PRIV->m_play);
	movie_free_old(&PRIV->m_arm);
	PyThread_free_sema(PRIV->m_dispsema);
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
	PyObject *file;
	int delay, duration;
	PyObject *attrdict, *anchorlist;
{
	PyObject *v;
	char *format;

	denter(movie_arm);
	Py_XDECREF(PRIV->m_arm.m_index);
	PRIV->m_arm.m_index = NULL;
#ifdef USE_CL
	Py_XDECREF(PRIV->m_arm.m_comphdr);
	PRIV->m_arm.m_comphdr = NULL;
#endif
	v = PyDict_GetItemString(attrdict, "width");
	if (v && PyInt_Check(v))
		PRIV->m_arm.m_width = PyInt_AsLong(v);
	else {
		ERROR(movie_arm, PyExc_RuntimeError, "no width specified");
		return 0;
	}
	v = PyDict_GetItemString(attrdict, "height");
	if (v && PyInt_Check(v))
		PRIV->m_arm.m_height = PyInt_AsLong(v);
	else {
		ERROR(movie_arm, PyExc_RuntimeError, "no height specified");
		return 0;
	}
	v = PyDict_GetItemString(attrdict, "format");
	if (v && PyString_Check(v)) {
		format = PyString_AsString(v);
		if (strcmp(format, "rgb8") == 0)
			PRIV->m_arm.m_format = FORMAT_RGB8;
#ifdef USE_CL
		else if (strcmp(format, "compress") == 0) {
			PRIV->m_arm.m_format = FORMAT_CL;
			v = PyDict_GetItemString(attrdict, "compressheader");
			if (v && PyString_Check(v)) {
				PRIV->m_arm.m_comphdr = v;
				Py_INCREF(v);
			} else {
				ERROR(movie_arm, PyExc_RuntimeError,
				      "no compressheader specified");
				return 0;
			}
		}
#endif /* USE_CL */
		else {
			ERROR(movie_arm, PyExc_RuntimeError, "unrecognized format");
			return 0;
		}
	} else {
		ERROR(movie_arm, PyExc_RuntimeError, "no format specified");
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
		if (PRIV->m_arm.m_frame) {
			free(PRIV->m_arm.m_frame);
			PRIV->m_arm.m_frame = NULL;
		}
		PRIV->m_arm.m_size = PRIV->m_arm.m_width * PRIV->m_arm.m_height;
		PRIV->m_arm.m_bframe = malloc(PRIV->m_arm.m_size * PRIV->m_arm.m_depth);
		if (PRIV->m_arm.m_bframe == NULL) {
			ERROR(movie_arm, PyExc_RuntimeError, "malloc failed");
			return 0;
		}
		PRIV->m_arm.m_image = XCreateImage(XtDisplay(PRIV->m_widget),
						   PRIV->m_visual,
						   PRIV->m_arm.m_planes,
						   ZPixmap, 0,
						   PRIV->m_arm.m_bframe,
						   PRIV->m_arm.m_width,
						   PRIV->m_arm.m_height,
						   PRIV->m_arm.m_depth * 8,
						   PRIV->m_arm.m_width * PRIV->m_arm.m_depth);
	}
#endif /* USE_XM */
	v = PyDict_GetItemString(attrdict, "index");
	if (v && PyList_Check(v)) {
		PRIV->m_arm.m_index = v;
		Py_INCREF(v);
	} else {
		ERROR(movie_arm, PyExc_RuntimeError, "no index specified");
		return 0;
	}
	v = PyDict_GetItemString(attrdict, "c0bits");
	if (v && PyInt_Check(v))
		PRIV->m_arm.m_c0bits = PyInt_AsLong(v);
	else {
		ERROR(movie_arm, PyExc_RuntimeError, "c0bits not specified");
		return 0;
	}
	v = PyDict_GetItemString(attrdict, "c1bits");
	if (v && PyInt_Check(v))
		PRIV->m_arm.m_c1bits = PyInt_AsLong(v);
	else {
		ERROR(movie_arm, PyExc_RuntimeError, "c1bits not specified");
		return 0;
	}
	v = PyDict_GetItemString(attrdict, "c2bits");
	if (v && PyInt_Check(v))
		PRIV->m_arm.m_c2bits = PyInt_AsLong(v);
	else {
		ERROR(movie_arm, PyExc_RuntimeError, "c2bits not specified");
		return 0;
	}
	v = PyDict_GetItemString(attrdict, "offset");
	if (v && PyInt_Check(v))
		PRIV->m_arm.m_moffset = PyInt_AsLong(v);
	else {
		ERROR(movie_arm, PyExc_RuntimeError, "offset not specified");
		return 0;
	}
	v = PyDict_GetItemString(attrdict, "scale");
	if (v && PyFloat_Check(v))
		PRIV->m_arm.m_scale = PyFloat_AsDouble(v);
	else {
		ERROR(movie_arm, PyExc_RuntimeError, "scale not specified");
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
				ERROR(movie_arm, PyExc_RuntimeError,
				      "bad color specification");
				return 0;
			}
			c = PyInt_AsLong(t);
			if (c < 0 || c > 255) {
				ERROR(movie_arm, PyExc_RuntimeError,
				      "bad color specification");
				return 0;
			}
			PRIV->m_arm.m_bgcolor = (PRIV->m_arm.m_bgcolor << 8) | c;
		}
	} else {
		ERROR(movie_arm, PyExc_RuntimeError,
		      "no background color specified");
		return 0;
	}
#ifdef USE_GL
	PRIV->m_arm.m_bgindex = -1;
#endif
#ifdef MM_DEBUG
	if (PRIV->m_arm.m_index) {
		dprintf(("movie_arm(%lx): indexsize: %d\n",
			 (long) self, PyList_Size(PRIV->m_arm.m_index)));
	}
#endif
	Py_XDECREF(PRIV->m_arm.m_f);
	Py_XINCREF(file);
	PRIV->m_arm.m_f = file;
	dprintf(("movie_arm(%lx): fd: %d\n",
		 (long) self, fileno(PyFile_AsFile(PRIV->m_arm.m_f))));
	return 1;
}

static void
movie_readframe(self, ptr, fd)
	mmobject *self;
	struct movie_data *ptr;
	int fd;
{
	unsigned char *p;
	unsigned long *lp;
	int i;

	switch (windowsystem) {
#ifdef USE_XM
	case WIN_X:
#ifdef USE_CL
		if (ptr->m_format == FORMAT_CL) {
			if (ptr->m_frame == NULL) {
				ptr->m_frame = malloc(ptr->m_size);
				if (ptr->m_frame == NULL) {
					dprintf(("movie_readframe: malloc failed\n"));
					return;
				}
			}
			if (read(fd, ptr->m_frame, ptr->m_size)
			    != ptr->m_size)
				dprintf(("movie_readframe: read incorrect amount\n"));
		} else
#endif /* USE_CL */
		{
			/* read image upside down */
			if (ptr->m_depth == 1)
				p = (unsigned char *) ptr->m_bframe + ptr->m_size;
			else {
				if (ptr->m_frame == NULL) {
					ptr->m_frame = malloc(ptr->m_size);
					if (ptr->m_frame == NULL) {
						dprintf(("movie_readframe: malloc failed\n"));
						return;
					}
				}
				p = (unsigned char *) ptr->m_frame + ptr->m_size;
			}
			for (i = ptr->m_height; i > 0; i--) {
				p -= ptr->m_width;
				read(fd, p, ptr->m_width);
			}
		}
		break;
#endif /* USE_XM */
#ifdef USE_GL
	case WIN_GL:
		if (read(fd, ptr->m_frame, ptr->m_size)
		    != ptr->m_size)
			dprintf(("movie_readframe: read incorrect amount\n"));
		break;
#endif /* USE_GL */
	default:
		abort();
	}

#ifdef USE_CL
	if (ptr->m_format == FORMAT_CL) {
		if (clDecompress(ptr->m_decomp, 1, ptr->m_size,
				 ptr->m_frame, ptr->m_bframe)
		    == FAILURE)
			dprintf(("movie_readframe: decompress failed"));
	} else
#endif /* USE_CL */
	if (ptr->m_depth == 4 && ptr->m_format == FORMAT_RGB8) {
		if (ptr->m_bframe == NULL)
			ptr->m_bframe = malloc(ptr->m_size * ptr->m_depth);
		p = (unsigned char *) ptr->m_frame;
		lp = (unsigned long *) ptr->m_bframe;
		for (i = ptr->m_size; i > 0; i--)
			*lp++ = cv_8_to_32[*p++];
	}
#ifdef USE_XM
	if (ptr->m_depth == 1 && cv_8_to_8_inited && windowsystem == WIN_X) {
		for (p = (unsigned char *) ptr->m_bframe, i = ptr->m_size;
		     i > 0;
		     p++, i--)
			*p = cv_8_to_8[*p];
	}
#endif /* USE_XM */
}

static void
movie_armer(self)
	mmobject *self;
{
	PyObject *v, *t;
	long offset;
	int fd;

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
	v = PyList_GetItem(PRIV->m_arm.m_index, 0);
	if (v == NULL || !PyTuple_Check(v) || PyTuple_Size(v) < 2) {
		dprintf(("movie_armer(%lx): index[0] not a proper tuple\n",
			 (long) self));
		return;
	}
	t = PyTuple_GetItem(v, 0);
	if (t == NULL || !PyTuple_Check(t) || PyTuple_Size(t) < 1) {
		dprintf(("movie_armer(%lx): index[0][0] not a proper tuple\n",
			 (long) self));
		return;
	}
	t = PyTuple_GetItem(t, 1);
	if (t == NULL || !PyInt_Check(t)) {
		dprintf(("movie_armer(%lx): index[0][0][1] not an int\n",
			 (long) self));
		return;
	}
	PRIV->m_arm.m_size = PyInt_AsLong(t);
	t = PyTuple_GetItem(v, 1);
	if (t == NULL || !PyInt_Check(t)) {
		dprintf(("movie_armer(%lx): index[0][1] not an int\n",
			 (long) self));
		return;
	}
	offset = PyInt_AsLong(t);

#ifdef USE_CL
	if (PRIV->m_arm.m_format == FORMAT_CL) {
		int scheme;
		void *comphdr;
		int length;
		int params[6];

		length = PyString_Size(PRIV->m_arm.m_comphdr);
		comphdr = PyString_AsString(PRIV->m_arm.m_comphdr);
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
			if (PRIV->m_arm.m_planes == 8)
				params[1] = CL_RGB332;
			else
				params[1] = CL_RGBX;
			params[3] = CL_TOP_DOWN;
			break;
#endif
#ifdef USE_GL
		case WIN_GL:
			params[1] = CL_RGBX;
			params[3] = CL_BOTTOM_UP;
			PRIV->m_arm.m_planes = 24;
			PRIV->m_arm.m_depth = 4;
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
	fd = fileno(PyFile_AsFile(PRIV->m_arm.m_f));
	PRIV->m_arm.m_offset = lseek(fd, 0L, SEEK_CUR);
	(void) lseek(fd, offset, SEEK_SET);
	movie_readframe(self, &PRIV->m_arm, fd);
}

static int
movie_play(self)
	mmobject *self;
{
	char c;
	int i;

	denter(movie_play);
	Py_XDECREF(PRIV->m_play.m_index);
	Py_XDECREF(PRIV->m_play.m_f);
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
	Py_XDECREF(PRIV->m_play.m_comphdr);
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
		ERROR(movie_play, PyExc_RuntimeError, "asynchronous arm failed");
		return 0;
	}
	/* empty the pipe */
	(void) fcntl(PRIV->m_pipefd[0], F_SETFL, O_NONBLOCK);
	while (read(PRIV->m_pipefd[0], &c, 1) == 1)
		;
	(void) fcntl(PRIV->m_pipefd[0], F_SETFL, 0);

	while (PyThread_down_sema(PRIV->m_dispsema, NOWAIT_SEMA) > 0)
		;

	switch (windowsystem) {
#ifdef USE_GL
	case WIN_GL:
		/* DEBUG: should call:
		 * acquire_lock(gl_lock, WAIT_LOCK);
		 */
		winset(PRIV->m_wid);
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
		/* clear the window */
		XFillRectangle(XtDisplay(PRIV->m_widget),
			       XtWindow(PRIV->m_widget), PRIV->m_gc,
			       PRIV->m_rect[X], PRIV->m_rect[Y],
			       PRIV->m_rect[WIDTH], PRIV->m_rect[HEIGHT]);
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
			scale = PRIV->m_rect[WIDTH] / PRIV->m_play.m_width;
			if (scale > PRIV->m_rect[HEIGHT] / PRIV->m_play.m_height)
				scale = PRIV->m_rect[HEIGHT] / PRIV->m_play.m_height;
			if (scale < 1)
				scale = 1;
		}
		xorig = PRIV->m_rect[X] + (PRIV->m_rect[WIDTH] - PRIV->m_play.m_width * scale) / 2;
		yorig = PRIV->m_rect[Y] + (PRIV->m_rect[HEIGHT] - PRIV->m_play.m_height * scale) / 2;
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
				  PRIV->m_rect[X] + (PRIV->m_rect[WIDTH] - PRIV->m_play.m_width) / 2,
				  PRIV->m_rect[Y] + (PRIV->m_rect[HEIGHT] - PRIV->m_play.m_height) / 2,
				  PRIV->m_play.m_width, PRIV->m_play.m_height);
		break;
#endif /* USE_XM */
	default:
		abort();
	}
	PyThread_up_sema(PRIV->m_dispsema);
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
	PyObject *v, *t0, *t;
	struct pollfd pollfd;
	int i;
	int size;
	unsigned char *p;

	denter(movie_player);
	dprintf(("movie_player(%lx): width = %d, height = %d\n",
		 (long) self, PRIV->m_play.m_width, PRIV->m_play.m_height));
	gettimeofday(&tm0, NULL);
	fd = fileno(PyFile_AsFile(PRIV->m_play.m_f));
	index = 0;
	lastindex = PyList_Size(PRIV->m_play.m_index) - 1;
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
			(void) PyThread_down_sema(PRIV->m_dispsema, WAIT_SEMA);
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
			(void) PyThread_down_sema(PRIV->m_dispsema, WAIT_SEMA);
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
			v = PyList_GetItem(PRIV->m_play.m_index, index);
			if (v == NULL || !PyTuple_Check(v) || PyTuple_Size(v) < 2) {
				dprintf((
			"movie_player(%lx): index[%d] not a proper tuple\n",
					 (long) self, index));
				goto loop_exit;
			}
			t0 = PyTuple_GetItem(v, 0);
			if (t0 == NULL || !PyTuple_Check(t0) || PyTuple_Size(t0) < 1) {
				dprintf((
			"movie_player(%lx): index[%d][0] not a proper tuple\n",
					 (long) self, index));
				goto loop_exit;
			}
			t = PyTuple_GetItem(t0, 0);
			if (t == NULL || !PyInt_Check(t)) {
				dprintf((
			"movie_player(%lx): index[%d][0][0] not an int\n",
					 (long) self, index));
				goto loop_exit;
			}
			newtime = PyInt_AsLong(t);
			/*dprintf(("movie_player(%lx): td = %d, newtime = %d\n",
				 (long) self, td, newtime));*/
		} while (index < lastindex && newtime <= td);
		t = PyTuple_GetItem(v, 1);
		if (t == NULL || !PyInt_Check(t)) {
			dprintf((
				"movie_player(%lx): index[%d][1] not an int\n",
				 (long) self, index));
			break;
		}
		offset = PyInt_AsLong(t);
		lseek(fd, offset, SEEK_SET);
		t = PyTuple_GetItem(t0, 1);
		if (t == NULL || !PyInt_Check(t)) {
			dprintf((
			"movie_player(%lx): index[%d][0][1] not an int\n",
				 (long) self, index));
			break;
		}
		size = PyInt_AsLong(t);
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
		movie_readframe(self, &PRIV->m_play, fd);
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
movie_resized(self, x, y, w, h)
	mmobject *self;
	int x, y, w, h;
{
	denter(movie_resized);
	PRIV->m_rect[X] = x;
	PRIV->m_rect[Y] = y;
	PRIV->m_rect[WIDTH] = w;
	PRIV->m_rect[HEIGHT] = h;
	switch (windowsystem) {
#ifdef USE_GL
	case WIN_GL: {
		long width, height;

		if (gl_lock)
			acquire_lock(gl_lock, WAIT_LOCK);
		winset(PRIV->m_wid);
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
		}
		if (gl_lock)
			release_lock(gl_lock);
		break;
	}
#endif /* USE_GL */
#ifdef USE_XM
	case WIN_X: {
		Dimension width, height;

		if (PRIV->m_play.m_image) {
			XFillRectangle(XtDisplay(PRIV->m_widget),
				       XtWindow(PRIV->m_widget), PRIV->m_gc,
				       PRIV->m_rect[X], PRIV->m_rect[Y],
				       PRIV->m_rect[WIDTH],
				       PRIV->m_rect[HEIGHT]);
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
	/* in case they're waiting */
	PyThread_up_sema(PRIV->m_dispsema);
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
			       PRIV->m_rect[X], PRIV->m_rect[Y],
			       PRIV->m_rect[WIDTH], PRIV->m_rect[HEIGHT]);
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
	Py_XDECREF(PRIV->m_play.m_index);
	PRIV->m_play.m_index = NULL;
	Py_XDECREF(PRIV->m_play.m_f);
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
	Py_XDECREF(PRIV->m_play.m_comphdr);
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
	PyMem_DEL(self);
	movie_chan_obj = NULL;
}

static PyObject *
moviechannel_getattr(self, name)
	channelobject *self;
	char *name;
{
	PyErr_SetString(PyExc_AttributeError, name);
	return NULL;
}

static PyTypeObject Moviechanneltype = {
	PyObject_HEAD_INIT(&PyType_Type)
	0,			/*ob_size*/
	"channel:movie",	/*tp_name*/
	sizeof(channelobject),	/*tp_size*/
	0,			/*tp_itemsize*/
	/* methods */
	(destructor)moviechannel_dealloc, /*tp_dealloc*/
	0,			/*tp_print*/
	(getattrfunc)moviechannel_getattr, /*tp_getattr*/
	0,			/*tp_setattr*/
	0,			/*tp_compare*/
	0,			/*tp_repr*/
};

static PyObject *
moviechannel_init(self, args)
	channelobject *self;
	PyObject *args;
{
	channelobject *p;

	if (!PyArg_NoArgs(args))
		return NULL;
	if (movie_chan_obj == NULL) {
		movie_chan_obj = PyObject_NEW(channelobject, &Moviechanneltype);
		if (movie_chan_obj == NULL)
			return NULL;
		movie_chan_obj->chan_funcs = &movie_channel_funcs;
	} else {
		Py_INCREF(movie_chan_obj);
	}
	return (PyObject *) movie_chan_obj;
}

static PyMethodDef moviechannel_methods[] = {
	{"init",		(PyCFunction)moviechannel_init},
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
	(void) Py_InitModule("moviechannel", moviechannel_methods);
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
}
