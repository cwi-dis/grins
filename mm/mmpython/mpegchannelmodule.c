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

#ifdef USE_XM
#include "widgetobject.h"
#include "GCobject.h"
#include "XColor.h"
#define BOOLEAN_TYPE_EXISTS
#endif

#include <video.h>
#include <mpeg.h>
extern unsigned long wpixel[];

#ifdef MM_DEBUG
static int mpegchannel_debug = 0;
#define dprintf(args)	(mpegchannel_debug && printf args)
#define denter(func)	struct mpeg_data *ptrA = &PRIV->arm, *ptrP = &PRIV->play; dprintf(( # func "(%lx)\n", (long) self))
#else
#define dprintf(args)
#define denter(func)	dprintf(( # func "(%lx)\n", (long) self))
#endif
#define ERROR(func, errortype, msg)	{				\
		dprintf((# func "(%lx): " msg "\n", (long) self));	\
		PyErr_SetString(errortype, msg);				\
		}

struct mpeg_data {
	ImageDesc imagedesc;	/* descriptor of image */
	long bgcolor;		/* background color for node */
	int center;		/* whether to center the video */
	PyObject *file;		/* file being played */
#ifdef USE_XM
	XImage *image;		/* X image to put image in */
#endif
	int moreframes;		/* more frames to play */
};

struct mpeg {
	struct mpeg_data arm, play;/* info for nodes being armed and played */
	int rect[4];		/* origin and size of window */
	int pipefd[2];		/* pipe for synchronization with player */
	PyThread_type_sema dispsema;	/* semaphore for display synchronization */
#ifdef USE_XM
	Widget widget;		/* the widget in which to draw */
	Visual *visual;		/* the visual of the window */
	int planes;		/* depth of window in bits per pixel */
	int depth;		/* depth of window in bytes per pixel */
	GC gc;			/* the graphics context with which to draw */
#endif
};
#define X	0
#define Y	1
#define WIDTH	2
#define HEIGHT	3

#define PRIV	((struct mpeg *) self->mm_private)

static int windowsystem;	/* which window system to use */
#define WIN_GL		1	/* only supported when USE_GL is defined */
#define WIN_X		2	/* only supported when USE_XM is defined */

static unsigned char ctab[128];

static void
do_display(self)
	mmobject *self;
{
	int x, y, w, h;

	denter(do_display);
	w = PRIV->play.imagedesc.Width;
	h = PRIV->play.imagedesc.Height;
	if (PRIV->play.center) {
		x = PRIV->rect[X] + (PRIV->rect[WIDTH] - w) / 2;
		y = PRIV->rect[Y] + (PRIV->rect[HEIGHT] - h) / 2;
	} else {
		x = PRIV->rect[X];
		y = PRIV->rect[Y];
	}
	switch (windowsystem) {
#ifdef USE_XM
	case WIN_X:
		if (PRIV->play.image == NULL)
			break;
		XPutImage(XtDisplay(PRIV->widget), XtWindow(PRIV->widget),
			  PRIV->gc, PRIV->play.image, 0, 0,
			  x, y, w, h);
		XFlush(XtDisplay(PRIV->widget));
		break;
#endif
	default:
		abort();
	}
}

static void
mpeg_display(self)
	mmobject *self;
{
	denter(mpeg_display);
	do_display(self);
	PyThread_up_sema(PRIV->dispsema);
}

static void
mpeg_armer(self)
	mmobject *self;
{
	denter(mpeg_armer);
	PRIV->arm.moreframes = GetMPEGFrame(&PRIV->arm.imagedesc,
					    PRIV->arm.image->data);
}

/* Video rates table */
/* Cheat on Vid rates, round to 30, and use 30 if illegal value 
   Except for 9, where Xing means 15, and given their popularity, we'll
   be nice and do it */
static int VidRateNum[16]={30, 24, 24, 25, 30, 30, 50, 60, 
                         60, 15, 30, 30, 30, 30, 30, 30};

static void
mpeg_player(self)
	mmobject *self;
{
	struct timeval tm0, tm1;
	long timediff_wanted, timediff_actual;
	long td;
	struct pollfd pollfd;

	denter(mpeg_player);
	if (PRIV->play.imagedesc.PictureRate >= 0)
		timediff_wanted = 1000 / VidRateNum[PRIV->play.imagedesc.PictureRate];
	else
		timediff_wanted = 1000 / 30;
	while (PRIV->play.moreframes) {
		gettimeofday(&tm0, NULL);
		my_qenter(self->mm_ev, 3);
		/* mpeg_display(self); */
		(void) PyThread_down_sema(PRIV->dispsema, WAIT_SEMA);
		PRIV->play.moreframes = GetMPEGFrame(&PRIV->play.imagedesc,
						     PRIV->play.image->data);
		gettimeofday(&tm1, NULL);
		timediff_actual = (tm1.tv_sec - tm0.tv_sec) * 1000 +
			(tm1.tv_usec - tm0.tv_usec) / 1000;
		td = timediff_wanted - timediff_actual;
		if (td < 0)
			td = 0;
		pollfd.fd = PRIV->pipefd[0];
		pollfd.events = POLLIN;
		pollfd.revents = 0;
		dprintf(("mpeg_player(%lx): polling %d\n", (long) self, td));
		if (poll(&pollfd, 1, td) < 0) {
			perror("poll");
			break;
		}
		/*
		** Either the next event is due or we got a command from the
		** main thread. Check.
		*/
		if (pollfd.revents & POLLIN) {
			char c;

			dprintf(("pollin event!\n"));
			(void) read(PRIV->pipefd[0], &c, 1);
			dprintf(("mpeg_player(%lx): read %c\n", (long) self, c));
			if (c == 'p') {
				/* pause */
				struct timeval tm1;

				dprintf(("mpeg_player(%lx): waiting to continue\n", (long) self));
				(void) read(PRIV->pipefd[0], &c, 1);
				dprintf(("mpeg_player(%lx): continue playing, read %c\n", (long) self, c));
			}
			if (c == 's') {
				/* stop */
				break;
			}
		}
	}
}

static int
mpeg_resized(self, x, y, w, h)
	mmobject *self;
	int x, y, w, h;
{
	denter(mpeg_resized);
	PRIV->rect[X] = x;
	PRIV->rect[Y] = y;
	PRIV->rect[WIDTH] = w;
	PRIV->rect[HEIGHT] = h;
	do_display(self);
	return 1;
}

static int
mpeg_arm(self, file, delay, duration, attrdict, anchorlist)
	mmobject *self;
	PyObject *file;
	int delay, duration;
	PyObject *attrdict, *anchorlist;
{
	PyObject *v;

	denter(mpeg_arm);
	v = PyDict_GetItemString(attrdict, "bgcolor");
	if (v && PyTuple_Check(v) && PyTuple_Size(v) == 3) {
		int i, c;
		PyObject *t;

		PRIV->arm.bgcolor = 0;
		for (i = 0; i < 3; i++) {
			t = PyTuple_GetItem(v, i);
			if (!PyInt_Check(t)) {
				ERROR(mpeg_arm, PyExc_RuntimeError,
				      "bad color specification");
				return 0;
			}
			c = PyInt_AsLong(t);
			if (c < 0 || c > 255) {
				ERROR(mpeg_arm, PyExc_RuntimeError, "bad color specification");
				return 0;
			}
			PRIV->arm.bgcolor = (PRIV->arm.bgcolor << 8) | c;
		}
	} else {
		ERROR(mpeg_arm, PyExc_RuntimeError, "no background color specified");
		return 0;
	}
	v = PyDict_GetItemString(attrdict, "center");
	if (v && PyInt_Check(v)) {
		PRIV->arm.center = PyInt_AsLong(v);
	} else if (v) {
		ERROR(mpeg_arm, PyExc_RuntimeError, "bad center value");
		return 0;
	} else {
		PRIV->arm.center = 0;
	}
	Py_INCREF(file);
	PRIV->arm.file = file;
	switch (PRIV->depth) {
	case 1:
		SetMPEGOption(&PRIV->arm.imagedesc, MPEG_DITHER, (int) &MBOrderedDitherInfo);
		break;
	case 2:
		SetMPEGOption(&PRIV->arm.imagedesc, MPEG_DITHER, (int) &FullColor16DitherInfo);
		break;
	case 4:
		SetMPEGOption(&PRIV->arm.imagedesc, MPEG_DITHER, (int) &FullColor32DitherInfo);
		break;
	}
	rewind(PyFile_AsFile(file));
	if (!OpenMPEG(PyFile_AsFile(file), &PRIV->arm.imagedesc)) {
		ERROR(mpeg_arm, PyExc_RuntimeError, "opening MPEG stream failed");
		return 0;
	}
	if (PRIV->depth == 1)
		SetMPEGOption(&PRIV->arm.imagedesc, MPEG_CMAP_INDEX, (int) ctab);
	dprintf(("mpeg_arm(%lx): width=%d, height=%d, rate=%d\n", (long) self,
		 PRIV->arm.imagedesc.Width, PRIV->arm.imagedesc.Height,
		 PRIV->arm.imagedesc.PictureRate));
#ifdef USE_XM
	if (windowsystem == WIN_X) {
		char *data = malloc(PRIV->arm.imagedesc.Width *
				    PRIV->arm.imagedesc.Height *
				    PRIV->arm.imagedesc.BitmapPad / 8);
		PRIV->arm.image = XCreateImage(XtDisplay(PRIV->widget),
					       PRIV->visual, PRIV->planes,
					       ZPixmap, 0,
					       data,
					       PRIV->arm.imagedesc.Width,
					       PRIV->arm.imagedesc.Height,
					       PRIV->arm.imagedesc.BitmapPad,
					       PRIV->arm.imagedesc.Width * PRIV->arm.imagedesc.BitmapPad / 8);
		if (PRIV->arm.image == NULL) {
			ERROR(mpeg_arm, PyExc_RuntimeError, "Create X Image failed");
			CloseMPEG(&PRIV->arm.imagedesc);
			return 0;
		}
	}
#endif /* USE_XM */
	return 1;
}

static int
mpeg_armstop(self)
	mmobject *self;
{
	denter(mpeg_armstop);
	return 1;
}

static int
mpeg_play(self)
	mmobject *self;
{
	char c;

	denter(mpeg_play);
	if (PRIV->play.image) {
		if (PRIV->play.moreframes)
			CloseMPEG(&PRIV->play.imagedesc);
		PRIV->play.image->data = NULL;
		XDestroyImage(PRIV->play.image);
		PRIV->play.image = NULL;
	}
	Py_XDECREF(PRIV->play.file);
	PRIV->play.file = NULL;
	PRIV->play = PRIV->arm;
	PRIV->arm.image = NULL;
	PRIV->arm.file = NULL;
	PRIV->arm.imagedesc.vid_stream = NULL;
	PRIV->arm.imagedesc.Colormap = NULL;

	/* empty the pipe */
	(void) fcntl(PRIV->pipefd[0], F_SETFL, O_NONBLOCK);
	while (read(PRIV->pipefd[0], &c, 1) == 1)
		;
	(void) fcntl(PRIV->pipefd[0], F_SETFL, 0);

	while (PyThread_down_sema(PRIV->dispsema, NOWAIT_SEMA) > 0)
		;

	switch (windowsystem) {
#ifdef USE_XM
	case WIN_X:
		/* clear the window */
		XFillRectangle(XtDisplay(PRIV->widget),
			       XtWindow(PRIV->widget), PRIV->gc,
			       PRIV->rect[X], PRIV->rect[Y],
			       PRIV->rect[WIDTH], PRIV->rect[HEIGHT]);
		break;
#endif /* USE_XM */
	}

	return 1;
}

static int
mpeg_playstop(self)
	mmobject *self;
{
	denter(mpeg_playstop);
	if (write(PRIV->pipefd[1], "s", 1) < 0)
		perror("write");
	/* in case they're waiting */
	PyThread_up_sema(PRIV->dispsema);
	return 1;
}

static int
mpeg_finished(self)
	mmobject *self;
{
	denter(mpeg_finished);
	switch (windowsystem) {
#ifdef USE_XM
	case WIN_X:
		XFillRectangle(XtDisplay(PRIV->widget), XtWindow(PRIV->widget),
			       PRIV->gc,
			       PRIV->rect[X], PRIV->rect[Y],
			       PRIV->rect[WIDTH], PRIV->rect[HEIGHT]);
		if (PRIV->play.image) {
			CloseMPEG(&PRIV->play.imagedesc);
			PRIV->play.image->data = NULL;
			XDestroyImage(PRIV->play.image);
			PRIV->play.image = NULL;
		}
		break;
#endif
	default:
		abort();
	}
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
		if (write(PRIV->pipefd[1], &msg, 1) < 0)
			perror("write");
	}
	return 1;
}

static void
colormask(mask, shiftp, widthp)
	long mask;
	int *shiftp, *widthp;
{
	int shift = 0;
	int width;

	while ((mask & 1) == 0) {
		shift++;
		mask >>= 1;
	}
	if (mask < 0)
		width = sizeof(long)*8 - shift;
	else {
		width = 0;
		while (mask != 0) {
			width++;
			mask >>= 1;
		}
	}
	*widthp = width;
	*shiftp = shift;
}

#define LUM_RANGE	8
#define CR_RANGE	4
#define CB_RANGE	4

static void
init_colortab(vptr)
	XVisualInfo *vptr;
{
	int red_width, red_shift;
	int green_width, green_shift;
	int blue_width, blue_shift;
	int r, g, b;
	int lum, cr, cb;
	int i;
	double fred, fgreen, fblue;

	if (vptr->depth != 8) {
		/* we need to fill in 3 wpixel values since they are misused
                   by the MPEG library to transmit the RGB color masks */
		wpixel[0] = vptr->red_mask;
		wpixel[1] = vptr->green_mask;
		wpixel[2] = vptr->blue_mask;
		return;
	}
	if (vptr->class == PseudoColor) {
		/* we know the colormap is set up like this */
		vptr->red_mask = 0xE0;
		vptr->blue_mask = 0x18;
		vptr->green_mask = 0x07;
	}
	colormask(vptr->red_mask, &red_shift, &red_width);
	colormask(vptr->green_mask, &green_shift, &green_width);
	colormask(vptr->blue_mask, &blue_shift, &blue_width);
	fred = (1 << red_width) - 1;
	fgreen = (1 << green_width) - 1;
	fblue = (1 << blue_width) - 1;

	for (i = 0; i < 128; i++) {
		lum = (i / (CR_RANGE * CB_RANGE)) % LUM_RANGE;
		cr = (i / CB_RANGE) % CR_RANGE;
		cb = i % CB_RANGE;

		lum = (lum*256/LUM_RANGE + 128/LUM_RANGE);

		r = lum + 1.366 * ((cr * 256/CR_RANGE + 128/CR_RANGE) - 128.0);
		g = lum - 0.700 * ((cr * 256/CR_RANGE + 128/CR_RANGE) - 128.0)
			- 0.334 * ((cb * 256/CB_RANGE + 128/CB_RANGE) - 128.0);
		b = lum + 1.732 * ((cb * 256/CB_RANGE + 128/CB_RANGE) - 128.0);
		if (r < 0) r = 0;
		if (r > 255) r = 255;
		if (g < 0) g = 0;
		if (g > 255) g = 255;
		if (b < 0) b = 0;
		if (b > 255) b = 255;

		r = (int) (r / 255. * fred + .5);
		g = (int) (g / 255. * fgreen + .5);
		b = (int) (b / 255. * fblue + .5);

		ctab[i] = (r << red_shift) | (g << green_shift) | (b << blue_shift);
	}
}

static int
mpeg_init(self)
	mmobject *self;
{
	PyObject *v;

	denter(mpeg_init);
	self->mm_private = malloc(sizeof(struct mpeg));
	if (self->mm_private == NULL) {
		(void) PyErr_NoMemory();
		return 0;
	}
#ifdef USE_XM
	PRIV->widget = NULL;
	PRIV->visual = NULL;
	PRIV->gc = NULL;
	PRIV->arm.image = PRIV->play.image = NULL;
#endif /* USE_XM */
	PRIV->arm.file = PRIV->play.file = NULL;
	PRIV->arm.imagedesc.vid_stream = NULL;
	PRIV->arm.imagedesc.Colormap = NULL;
	if ((PRIV->dispsema = PyThread_allocate_sema(0)) == NULL) {
		ERROR(mpeg_init, PyExc_RuntimeError, "cannot create semaphore");
		goto error_return_no_close;
	}
	if (pipe(PRIV->pipefd) < 0) {
		ERROR(mpeg_init, PyExc_RuntimeError, "cannot create pipe");
		goto error_return_no_close;
	}

#ifdef USE_XM
	v = PyDict_GetItemString(self->mm_attrdict, "widget");
	if (v && is_widgetobject(v)) {
		if (windowsystem != 0 && windowsystem != WIN_X) {
			ERROR(mpeg_init, PyExc_RuntimeError,
			      "cannot use two window systems simultaneously");
			goto error_return;
		}
		windowsystem = WIN_X;
		dprintf(("mpeg_init(%lx): using X window system\n", (long) self));
		PRIV->widget = getwidgetvalue(v);
		v = PyDict_GetItemString(self->mm_attrdict, "gc");
		if (v && is_gcobject(v))
			PRIV->gc = PyGC_GetGC(v);
		else {
			ERROR(mpeg_init, PyExc_RuntimeError, "no gc specified");
			goto error_return;
		}
		v = PyDict_GetItemString(self->mm_attrdict, "visual");
		if (v && is_visualobject(v)) {
			XVisualInfo *vptr = getvisualinfovalue(v);
			init_colortab(vptr);
			PRIV->visual = vptr->visual;
			PRIV->planes = vptr->depth;
			dprintf(("mpeg_init(%lx): using visual of depth %d and type %d\n", (long) self, vptr->depth, vptr->class));
		} else {
			ERROR(mpeg_init, PyExc_RuntimeError, "no visual specified");
			goto error_return;
		}
		switch (PRIV->planes) {
		case 8:
			PRIV->depth = 1;
			break;
		case 15:
		case 16:
			PRIV->depth = 2;
			break;
		case 24:
		case 32:
			PRIV->depth = 4;
			break;
		default:
			ERROR(mpeg_init, PyExc_RuntimeError,
			      "unsupported visual depth");
			goto error_return;
		}
	}
#endif /* USE_XM */

	if (1
#ifdef USE_XM
	    && PRIV->widget == NULL
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
			PRIV->rect[i] = PyInt_AsLong(t);
		}
	} else {
		ERROR(mpeg_init, PyExc_RuntimeError, "no size specified");
		goto error_return;
	}
	return 1;		/* normal return */

error_return:
	(void) close(PRIV->pipefd[0]);
	(void) close(PRIV->pipefd[1]);
error_return_no_close:
	if (PRIV->dispsema)
		PyThread_free_sema(PRIV->dispsema);
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
	PyThread_free_sema(PRIV->dispsema);
	(void) close(PRIV->pipefd[0]);
	(void) close(PRIV->pipefd[1]);
	free(self->mm_private);
	self->mm_private = NULL;
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
	mpeg_display,
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
	dprintf(("mpegchannel_getattr(%lx): %s\n", (long) self, name));
	PyErr_SetString(PyExc_AttributeError, name);
	return NULL;
}

static PyTypeObject Mpegchanneltype = {
	PyObject_HEAD_INIT(&PyType_Type)
	0,			/*ob_size*/
	"channel:mpeg",		/*tp_name*/
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
#ifdef MM_DEBUG
	mpegchannel_debug = getenv("MPEGDEBUG") != 0;
#endif
	dprintf(("initmpegchannel\n"));
	(void) Py_InitModule("mpegchannel", mpegchannel_methods);
}
