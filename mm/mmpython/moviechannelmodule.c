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

#ifdef MM_DEBUG
static int moviechannel_debug = 0;
#define dprintf(args)	(moviechannel_debug && printf args)
#else
#define dprintf(args)
#endif
#define denter(func)	dprintf(( # func "(%lx)\n", (long) self))

#define MAXMAP		(4096 - 256) /* max nr. of colormap entries to use */

#define FORMAT_RGB8	1

static type_lock gl_lock;
extern type_lock getlocklock PROTO((object *));

struct movie_data {
	int m_width;		/* width of movie */
	int m_height;		/* height of movie */
	int m_format;		/* format of movie */
	int m_wid;		/* window ID */
	int m_c0bits, m_c1bits, m_c2bits; /* # of bits for rgb colors */
	int m_moffset;		/* offset in colormap */
	double m_scale;		/* movie scale (magnification) factor */
	object *m_index;	/* cached movie index */
	object *m_f;		/* file where movie comes from */
	long m_offset;		/* offset in file before we go seeking */
	void *m_frame;		/* one frame */
	int m_size;		/* size of frame */
	long m_bgcolor;		/* background color for window */
	int m_bgindex;		/* colormap index for background color */
};
struct movie {
	long m_width, m_height;	/* width and height of window */
	struct movie_data m_play; /* movie being played */
	struct movie_data m_arm; /* movie being armed */
	int m_pipefd[2];	/* pipe for synchronization with player */
};

#define PRIV	((struct movie *) self->mm_private)

static char graphics_version[12]; /* gversion() output */
static int is_entry_indigo;	/* true iff we run on an Entry Indigo */

static int
movie_init(self)
	mmobject *self;
{
	denter(movie_init);
	self->mm_private = malloc(sizeof(struct movie));
	if (self->mm_private == NULL) {
		(void) err_nomem();
		return 0;
	}
	if (pipe(PRIV->m_pipefd) < 0) {
		err_setstr(RuntimeError, "cannot create pipe");
		free(self->mm_private);
		self->mm_private = NULL;
		return 0;
	}
	PRIV->m_play.m_index = NULL;
	PRIV->m_play.m_frame = NULL;
	PRIV->m_play.m_f = NULL;
	PRIV->m_arm.m_index = NULL;
	PRIV->m_arm.m_frame = NULL;
	PRIV->m_arm.m_f = NULL;
	return 1;
}

static void
movie_dealloc(self)
	mmobject *self;
{
	denter(movie_dealloc);
	XDECREF(PRIV->m_play.m_index);
	XDECREF(PRIV->m_arm.m_index);
	XDECREF(PRIV->m_play.m_f);
	XDECREF(PRIV->m_arm.m_f);
	if (PRIV->m_play.m_frame)
		free(PRIV->m_play.m_frame);
	if (PRIV->m_arm.m_frame)
		free(PRIV->m_arm.m_frame);
	(void) close(PRIV->m_pipefd[0]);
	(void) close(PRIV->m_pipefd[1]);
	free(self->mm_private);
	self->mm_private = NULL;
}

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
	v = dictlookup(attrdict, "width");
	if (v && is_intobject(v))
		PRIV->m_arm.m_width = getintvalue(v);
	else {
		err_setstr(RuntimeError, "no width specified");
		return 0;
	}
	v = dictlookup(attrdict, "height");
	if (v && is_intobject(v))
		PRIV->m_arm.m_height = getintvalue(v);
	else {
		err_setstr(RuntimeError, "no height specified");
		return 0;
	}
	v = dictlookup(attrdict, "wid");
	if (v && is_intobject(v))
		PRIV->m_arm.m_wid = getintvalue(v);
	else {
		err_setstr(RuntimeError, "no wid specified");
		return 0;
	}
	v = dictlookup(attrdict, "format");
	if (v && is_stringobject(v)) {
		format = getstringvalue(v);
		if (strcmp(format, "rgb8") == 0)
			PRIV->m_arm.m_format = FORMAT_RGB8;
		else {
			err_setstr(RuntimeError, "unrecognized format");
			return 0;
		}
	} else {
		err_setstr(RuntimeError, "no format specified");
		return 0;
	}
	v = dictlookup(attrdict, "index");
	if (v && is_listobject(v)) {
		PRIV->m_arm.m_index = v;
		INCREF(v);
	} else {
		err_setstr(RuntimeError, "no index specified");
		return 0;
	}
	v = dictlookup(attrdict, "c0bits");
	if (v && is_intobject(v))
		PRIV->m_arm.m_c0bits = getintvalue(v);
	else {
		err_setstr(RuntimeError, "c0bits not specified");
		return 0;
	}
	v = dictlookup(attrdict, "c1bits");
	if (v && is_intobject(v))
		PRIV->m_arm.m_c1bits = getintvalue(v);
	else {
		err_setstr(RuntimeError, "c1bits not specified");
		return 0;
	}
	v = dictlookup(attrdict, "c2bits");
	if (v && is_intobject(v))
		PRIV->m_arm.m_c2bits = getintvalue(v);
	else {
		err_setstr(RuntimeError, "c2bits not specified");
		return 0;
	}
	v = dictlookup(attrdict, "offset");
	if (v && is_intobject(v))
		PRIV->m_arm.m_moffset = getintvalue(v);
	else {
		err_setstr(RuntimeError, "offset not specified");
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
	dprintf(("movie_arm(%lx): gl_lock = %lx\n", (long) self, (long) gl_lock));
#ifdef MM_DEBUG
	if (PRIV->m_arm.m_index)
		dprintf(("movie_arm(%lx): indexsize: %d\n", (long) self, getlistsize(PRIV->m_arm.m_index)));
#endif
	XDECREF(PRIV->m_arm.m_f);
	PRIV->m_arm.m_f = file;
	XINCREF(PRIV->m_arm.m_f);
	dprintf(("movie_arm(%lx): fd: %d\n", (long) self, fileno(getfilefile(PRIV->m_arm.m_f))));
	return 1;
}

static void
movie_armer(self)
	mmobject *self;
{
	object *v, *t;
	long offset;
	int fd;

	denter(movie_armer);
	v = getlistitem(PRIV->m_arm.m_index, 0);
	t = gettupleitem(v, 0);
	t = gettupleitem(t, 1);
	PRIV->m_arm.m_size = getintvalue(t);
	t = gettupleitem(v, 1);
	offset = getintvalue(t);

	if (PRIV->m_arm.m_frame)
		free(PRIV->m_arm.m_frame);
	PRIV->m_arm.m_frame = malloc(PRIV->m_arm.m_size);
	fd = fileno(getfilefile(PRIV->m_arm.m_f));
	PRIV->m_arm.m_offset = lseek(fd, 0L, SEEK_CUR);
	(void) lseek(fd, offset, SEEK_SET);
	if (read(fd, PRIV->m_arm.m_frame, PRIV->m_arm.m_size) != PRIV->m_arm.m_size)
		dprintf(("movie_armer: read incorrect amount\n"));
}

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
	int bgr, bgg, bgb;
	int d, dist = 3 * 256;	/* bigger than it can be */
	int index;
	int offset = PRIV->m_play.m_moffset;
	double c0v, c1v, c2v;
	void (*convcolor)(double, double, double, int *, int *, int *);

	switch (PRIV->m_play.m_format) {
	case FORMAT_RGB8:
		convcolor = conv_rgb8;
		break;
	}
	bgr = (PRIV->m_play.m_bgcolor >> 16) & 0xff;
	bgg = (PRIV->m_play.m_bgcolor >>  8) & 0xff;
	bgb = (PRIV->m_play.m_bgcolor      ) & 0xff;
	maxc0 = 1 << c0bits;
	maxc1 = 1 << c1bits;
	maxc2 = 1 << PRIV->m_play.m_c2bits;
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
					(*convcolor)(c0v, c1v, c2v, &r, &g, &b);
					dprintf(("mapcolor(%d,%d,%d,%d)\n", index, r, g, b));
					mapcolor(index, r, g, b);
					if (index == offset)
						color(index);
					d = abs(r - bgr) + abs(g - bgg) + abs(b - bgb);
					if (d < dist) {
						PRIV->m_play.m_bgindex = index;
						dist = d;
					}
				}
			}
		}
	}
	gflush();
}

static int
movie_play(self)
	mmobject *self;
{
	char c;

	denter(movie_play);
	XDECREF(PRIV->m_play.m_index);
	XDECREF(PRIV->m_play.m_f);
	if (PRIV->m_play.m_frame)
		free(PRIV->m_play.m_frame);
	PRIV->m_play = PRIV->m_arm;
	PRIV->m_arm.m_index = NULL;
	PRIV->m_arm.m_frame = NULL;
	PRIV->m_arm.m_f = NULL;
	/* empty the pipe */
	(void) fcntl(PRIV->m_pipefd[0], F_SETFL, FNDELAY);
	while (read(PRIV->m_pipefd[0], &c, 1) == 1)
		;
	(void) fcntl(PRIV->m_pipefd[0], F_SETFL, 0);
	/* get the window size */
	winset(PRIV->m_play.m_wid);
	getsize(&PRIV->m_width, &PRIV->m_height);
	/* initialize color map */
	if (PRIV->m_arm.m_format == FORMAT_RGB8 && is_entry_indigo &&
	    strcmp(graphics_version, "GL4DLG-4.0.") == 0) {
		/* only on entry-level Indigo running IRIX 4.0.5 */
		RGBmode();
		gconfig();
		RGBcolor((PRIV->m_play.m_bgcolor >> 16) & 0xff,
			 (PRIV->m_play.m_bgcolor >>  8) & 0xff,
			 (PRIV->m_play.m_bgcolor      ) & 0xff);
		/* RGBcolor(200, 200, 200); /* XXX rather light grey */
		clear();
		pixmode(PM_SIZE, 8);
	} else {
		cmode();
		gconfig();
		init_colormap(self);
		color(PRIV->m_play.m_bgindex);
		clear();
	}
	return 1;
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
	object *v;
	long xorig, yorig;
	struct pollfd pollfd;

	denter(movie_player);
	dprintf(("movie_player(%lx): width = %d, height = %d\n", (long) self, PRIV->m_play.m_width, PRIV->m_play.m_height));
	gettimeofday(&tm0, NULL);
	fd = fileno(getfilefile(PRIV->m_play.m_f));
	index = 0;
	lastindex = getlistsize(PRIV->m_play.m_index) - 1;
	nplayed = 0;
	while (index <= lastindex) {
		/*dprintf(("movie_player(%lx): writing image %d\n", (long) self, index));*/
		acquire_lock(gl_lock, 1);
		winset(PRIV->m_play.m_wid);
		pixmode(PM_SIZE, 8);
		xorig = (PRIV->m_width - PRIV->m_play.m_width * PRIV->m_play.m_scale) / 2;
		yorig = (PRIV->m_height - PRIV->m_play.m_height * PRIV->m_play.m_scale) / 2;
		rectzoom(PRIV->m_play.m_scale, PRIV->m_play.m_scale);
		lrectwrite(xorig, yorig, xorig + PRIV->m_play.m_width - 1,
			   yorig + PRIV->m_play.m_height - 1,
			   PRIV->m_play.m_frame);
		gflush();
		release_lock(gl_lock);
		nplayed++;
		if (index == lastindex)
			break;
		gettimeofday(&tm, NULL);
		td = (tm.tv_sec - tm0.tv_sec) * 1000 +
			(tm.tv_usec - tm0.tv_usec) / 1000 - timediff;
		do {
			index++;
			v = getlistitem(PRIV->m_play.m_index, index);
			newtime = getintvalue(gettupleitem(gettupleitem(v, 0), 0));
			/*dprintf(("movie_player(%lx): td = %d, newtime = %d\n", (long) self, td, newtime));*/
		} while (index < lastindex && newtime <= td);
		offset = getintvalue(gettupleitem(v, 1));
		lseek(fd, offset, SEEK_SET);
		read(fd, PRIV->m_play.m_frame,
		     PRIV->m_play.m_size);
		gettimeofday(&tm, NULL);
		td = (tm.tv_sec - tm0.tv_sec) * 1000 +
			(tm.tv_usec - tm0.tv_usec) / 1000 - timediff;
		td = newtime - td;
		/*dprintf(("movie_player(%lx): td = %d\n", (long) self, td));*/
		if (td < 0)
			td = 0;
		pollfd.fd = PRIV->m_pipefd[1];
		pollfd.events = POLLIN;
		pollfd.revents = 0;
		if (poll(&pollfd, 1, td) < 0) {
			perror("poll");
			break;
		}
		if (pollfd.revents & POLLIN) {
			char c;

			dprintf(("pollin event!\n"));
			(void) read(PRIV->m_pipefd[0], &c, 1);
			dprintf(("movie_player(%lx): read %c\n", (long) self, c));
			if (c == 's')
				break;
			if (c == 'p') {
				struct timeval tm1;

				gettimeofday(&tm, NULL);
				dprintf(("movie_player(%lx): waiting to continue\n", (long) self));
				(void) read(PRIV->m_pipefd[0], &c, 1);
				dprintf(("movie_player(%lx): continue playing, read %c\n", (long) self, c));
				gettimeofday(&tm1, NULL);
				timediff += (tm1.tv_sec - tm.tv_sec) * 1000 +
					(tm1.tv_usec - tm.tv_usec) / 1000;
			}
		}
	}
	printf("played %d out of %d frames\n", nplayed, lastindex + 1);
	lseek(fd, PRIV->m_play.m_offset, SEEK_SET);
}

static int
movie_done(self)
	mmobject *self;
{
	denter(movie_done);
	return 1;
}

static int
movie_resized(self)
	mmobject *self;
{
	long xorig, yorig;

	denter(movie_resized);
	getsize(&PRIV->m_width, &PRIV->m_height);
	if (PRIV->m_play.m_frame) {
		winset(PRIV->m_play.m_wid);
		pixmode(PM_SIZE, 8);
		if (PRIV->m_play.m_bgindex >= 0)
			color(PRIV->m_play.m_bgindex);
		else
			RGBcolor((PRIV->m_play.m_bgcolor >> 16) & 0xff,
				 (PRIV->m_play.m_bgcolor >>  8) & 0xff,
				 (PRIV->m_play.m_bgcolor      ) & 0xff);
		clear();
		xorig = (PRIV->m_width - PRIV->m_play.m_width * PRIV->m_play.m_scale) / 2;
		yorig = (PRIV->m_height - PRIV->m_play.m_height * PRIV->m_play.m_scale) / 2;
		rectzoom(PRIV->m_play.m_scale, PRIV->m_play.m_scale);
		lrectwrite(xorig, yorig, xorig + PRIV->m_play.m_width - 1,
			   yorig + PRIV->m_play.m_height - 1,
			   PRIV->m_play.m_frame);
		gflush();
	}
	return 1;
}

static int
movie_stop(self)
	mmobject *self;
{
	denter(movie_stop);
	if (write(PRIV->m_pipefd[1], "s", 1) < 0)
		perror("write");
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
	/* player thread hasn't reacted yet.  Hence the check on STOPPING. */
	if ((self->mm_flags & (PLAYING | STOPPING)) == PLAYING) {
		dprintf(("movie_setrate(%lx): writing %c\n", (long) self, msg));
		if (write(PRIV->m_pipefd[1], &msg, 1) < 0)
			perror("write");
	}
	return 1;
}

static struct mmfuncs movie_channel_funcs = {
	movie_armer,
	movie_player,
	movie_done,
	movie_resized,
	movie_arm,
	movie_play,
	movie_stop,
	movie_setrate,
	movie_init,
	movie_dealloc,
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
	return movie_chan_obj;
}

static struct methodlist moviechannel_methods[] = {
	{"init",		moviechannel_init},
	{NULL,			NULL}
};

void
initmoviechannel()
{
#ifdef MM_DEBUG
	moviechannel_debug = getenv("MOVIEDEBUG") != 0;
#endif
	dprintf(("initmoviechannel\n"));
	(void) initmodule("moviechannel", moviechannel_methods);
	(void) gversion(graphics_version);
	is_entry_indigo = (getgdesc(GD_XPMAX) == 1024 &&
			   getgdesc(GD_YPMAX) == 768 &&
			   getgdesc(GD_BITS_NORM_SNG_RED) == 3 &&
			   getgdesc(GD_BITS_NORM_SNG_GREEN) == 3 &&
			   getgdesc(GD_BITS_NORM_SNG_BLUE) == 2);
}
