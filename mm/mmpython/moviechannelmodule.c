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
	void *m_bframe;		/* one frame, converted to big format */
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
static int maxbits;		/* max # of bitplanes for color index */
static short colors[256][3];	/* saved color map entries */
static int colormap[256];	/* rgb8 -> rgb24 conversion */
static int window_used, initialized;

static int
movie_init(self)
	mmobject *self;
{
	denter(movie_init);
	self->mm_private = malloc(sizeof(struct movie));
	if (self->mm_private == NULL) {
		dprintf(("movie_init(%lx): malloc failed\n", (long) self));
		(void) err_nomem();
		return 0;
	}
	if (pipe(PRIV->m_pipefd) < 0) {
		dprintf(("movie_init(%lx): cannot create pipe\n", (long) self));
		err_setstr(RuntimeError, "cannot create pipe");
		free(self->mm_private);
		self->mm_private = NULL;
		return 0;
	}
	PRIV->m_play.m_index = NULL;
	PRIV->m_play.m_frame = NULL;
	PRIV->m_play.m_bframe = NULL;
	PRIV->m_play.m_f = NULL;
	PRIV->m_play.m_wid = -1;
	PRIV->m_arm.m_index = NULL;
	PRIV->m_arm.m_frame = NULL;
	PRIV->m_arm.m_bframe = NULL;
	PRIV->m_arm.m_f = NULL;
	PRIV->m_arm.m_wid = -1;
	window_used++;
	return 1;
}

static void
movie_dealloc(self)
	mmobject *self;
{
	int i;

	denter(movie_dealloc);
#if 0
	if (--window_used == 0 && gl_lock) {
		if (maxbits < 11 && !is_entry_indigo) {
			acquire_lock(gl_lock, WAIT_LOCK);
			winset(PRIV->m_play.m_wid);
			for (i = 0; i < 256; i++) {
				mapcolor(i, colors[i][0], colors[i][1],
					 colors[i][2]);
				/*
				dprintf(("movie_player(%lx): colors %d %d %d\n",
					 (long) self, colors[i][0],
					 colors[i][1], colors[i][2]));
				*/
			}
			release_lock(gl_lock);
		}
	}
#endif
	XDECREF(PRIV->m_play.m_index);
	XDECREF(PRIV->m_arm.m_index);
	XDECREF(PRIV->m_play.m_f);
	XDECREF(PRIV->m_arm.m_f);
	if (PRIV->m_play.m_frame)
		free(PRIV->m_play.m_frame);
	if (PRIV->m_play.m_bframe)
		free(PRIV->m_play.m_bframe);
	if (PRIV->m_arm.m_frame)
		free(PRIV->m_arm.m_frame);
	if (PRIV->m_arm.m_bframe)
		free(PRIV->m_arm.m_bframe);
	(void) close(PRIV->m_pipefd[0]);
	(void) close(PRIV->m_pipefd[1]);
	free(self->mm_private);
	self->mm_private = NULL;
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
init_colorconv()
{
	int r, g, b;
	int index;

	for (index = 0; index < 256; index++) {
		conv_rgb8(index / 255.0, 0.0, 0.0, &r, &g, &b);
		colormap[index] = (b<<16)|(g<<8)|r;
		dprintf(("%d %d %d %d\n", index, r, g, b));
	}
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

	denter(init_colormap);

	switch (PRIV->m_play.m_format) {
	case FORMAT_RGB8:
		convcolor = conv_rgb8;
		if (PRIV->m_play.m_bframe)
			return;
		break;
	}
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
					/*dprintf(("mapcolor(%d,%d,%d,%d)\n", index, r, g, b));*/
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
	gflush();
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
	if (PRIV->m_arm.m_index) {
		dprintf(("movie_arm(%lx): indexsize: %d\n", (long) self, getlistsize(PRIV->m_arm.m_index)));
	}
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
	if (PRIV->m_arm.m_frame) {
		free(PRIV->m_arm.m_frame);
		PRIV->m_arm.m_frame = NULL;
	}
	if (PRIV->m_arm.m_bframe) {
		free(PRIV->m_arm.m_bframe);
		PRIV->m_arm.m_bframe = NULL;
	}
	v = getlistitem(PRIV->m_arm.m_index, 0);
	if (v == NULL || !is_tupleobject(v) || gettuplesize(v) < 2) {
		dprintf(("movie_armer(%lx): index[0] not a proper tuple\n", (long) self));
		return;
	}
	t = gettupleitem(v, 0);
	if (t == NULL || !is_tupleobject(t) || gettuplesize(t) < 1) {
		dprintf(("movie_armer(%lx): index[0][0] not a proper tuple\n", (long) self));
		return;
	}
	t = gettupleitem(t, 1);
	if (t == NULL || !is_intobject(t)) {
		dprintf(("movie_armer(%lx): index[0][0][1] not an int\n", (long) self));
		return;
	}
	PRIV->m_arm.m_size = getintvalue(t);
	t = gettupleitem(v, 1);
	if (t == NULL || !is_intobject(t)) {
		dprintf(("movie_armer(%lx): index[0][1] not an int\n", (long) self));
		return;
	}
	offset = getintvalue(t);

	PRIV->m_arm.m_frame = malloc(PRIV->m_arm.m_size);
	if (!is_entry_indigo && maxbits < 11)
		PRIV->m_arm.m_bframe = malloc(PRIV->m_arm.m_size * 4);
	fd = fileno(getfilefile(PRIV->m_arm.m_f));
	PRIV->m_arm.m_offset = lseek(fd, 0L, SEEK_CUR);
	(void) lseek(fd, offset, SEEK_SET);
	if (read(fd, PRIV->m_arm.m_frame, PRIV->m_arm.m_size) != PRIV->m_arm.m_size)
		dprintf(("movie_armer: read incorrect amount\n"));
	if (PRIV->m_arm.m_bframe) {
		long *lp;
		unsigned char *p;
		int i;

		lp = (long *) PRIV->m_arm.m_bframe;
		p = (unsigned char *) PRIV->m_arm.m_frame;
		for (i = PRIV->m_arm.m_size; i > 0; i--)
			*lp++ = colormap[*p++];
	}
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
	if (PRIV->m_play.m_frame)
		free(PRIV->m_play.m_frame);
	if (PRIV->m_play.m_bframe)
		free(PRIV->m_play.m_bframe);
	PRIV->m_play = PRIV->m_arm;
	PRIV->m_arm.m_index = NULL;
	PRIV->m_arm.m_frame = NULL;
	PRIV->m_arm.m_bframe = NULL;
	PRIV->m_arm.m_f = NULL;
	if (PRIV->m_play.m_frame == NULL) {
		/* apparently the arm failed */
		dprintf(("movie_play(%lx): not playing because arm failed\n", (long) self));
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
	/* initialize color map */
	if (initialized == 0) {
		initialized = 1;
		if (maxbits < 11 && !is_entry_indigo) {
			for (i = 0; i < 256; i++) {
				getmcolor(i, &colors[i][0], &colors[i][1],
					  &colors[i][2]);
				/*
				dprintf(("movie_play(%lx): colors %d %d %d\n",
					 (long) self, colors[i][0],
					 colors[i][1], colors[i][2]));
				*/
			}
		}
	}
	winpop();		/* pop up the window */
	if ((PRIV->m_arm.m_format == FORMAT_RGB8 && is_entry_indigo &&
	     strcmp(graphics_version, "GL4DLG-4.0.") == 0) ||
	    PRIV->m_play.m_bframe) {
		/* only on entry-level Indigo running IRIX 4.0.5 */
		RGBmode();
		gconfig();
		RGBcolor((PRIV->m_play.m_bgcolor >> 16) & 0xff,
			 (PRIV->m_play.m_bgcolor >>  8) & 0xff,
			 (PRIV->m_play.m_bgcolor      ) & 0xff);
		clear();
		if (PRIV->m_play.m_bframe)
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
	object *v, *t;
	long xorig, yorig;
	struct pollfd pollfd;
	int i;
	double scale;

	denter(movie_player);
	dprintf(("movie_player(%lx): width = %d, height = %d\n", (long) self, PRIV->m_play.m_width, PRIV->m_play.m_height));
	gettimeofday(&tm0, NULL);
	fd = fileno(getfilefile(PRIV->m_play.m_f));
	index = 0;
	lastindex = getlistsize(PRIV->m_play.m_index) - 1;
	nplayed = 0;
	while (index <= lastindex) {
		/*dprintf(("movie_player(%lx): writing image %d\n", (long) self, index));*/
		acquire_lock(gl_lock, WAIT_LOCK);
		winset(PRIV->m_play.m_wid);
		if (PRIV->m_play.m_bframe) {
			pixmode(PM_SIZE, 32);
		} else {
			pixmode(PM_SIZE, 8);
			if (PRIV->m_play.m_bgindex >= 0)
				writemask(0xff);
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
			if (v == NULL || !is_tupleobject(v) || gettuplesize(v) < 2) {
				dprintf(("movie_player(%lx): index[%d] not a proper tuple\n", (long) self, index));
				goto loop_exit;
			}
			t = gettupleitem(v, 0);
			if (t == NULL || !is_tupleobject(t) || gettuplesize(t) < 1) {
				dprintf(("movie_player(%lx): index[%d][0] not a proper tuple\n", (long) self, index));
				goto loop_exit;
			}
			t = gettupleitem(t, 0);
			if (t == NULL || !is_intobject(t)) {
				dprintf(("movie_player(%lx): index[%d][0][0] not an int\n", (long) self, index));
				goto loop_exit;
			}
			newtime = getintvalue(t);
			/*dprintf(("movie_player(%lx): td = %d, newtime = %d\n", (long) self, td, newtime));*/
		} while (index < lastindex && newtime <= td);
		t = gettupleitem(v, 1);
		if (t == NULL || !is_intobject(t)) {
			dprintf(("movie_player(%lx): index[%d][1] not an int\n", (long) self, index));
			break;
		}
		offset = getintvalue(t);
		lseek(fd, offset, SEEK_SET);
		read(fd, PRIV->m_play.m_frame, PRIV->m_play.m_size);
		if (PRIV->m_play.m_bframe) {
			long *lp;
			unsigned char *p;
			int i;

			lp = (long *) PRIV->m_play.m_bframe;
			p = (unsigned char *) PRIV->m_play.m_frame;
			for (i = PRIV->m_play.m_size; i > 0; i--)
				*lp++ = colormap[*p++];
		}
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
		dprintf(("movie_player(%lx): polling %d\n", (long) self, td));
		if (poll(&pollfd, 1, td) < 0) {
			perror("poll");
			break;
		}
		dprintf(("movie_player(%lx): polling done\n", (long) self));
		if (pollfd.revents & POLLIN) {
			char c;

			dprintf(("pollin event!\n"));
			(void) read(PRIV->m_pipefd[0], &c, 1);
			dprintf(("movie_player(%lx): read %c\n", (long) self, c));
			if (c == 's') {
				if (PRIV->m_play.m_frame)
					free(PRIV->m_play.m_frame);
				PRIV->m_play.m_frame = NULL;
				if (PRIV->m_play.m_bframe)
					free(PRIV->m_play.m_bframe);
				PRIV->m_play.m_bframe = NULL;
				break;
			}
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
 loop_exit:
	printf("played %d out of %d frames\n", nplayed, lastindex + 1);
	lseek(fd, PRIV->m_play.m_offset, SEEK_SET);
}

static int
movie_resized(self)
	mmobject *self;
{
	long xorig, yorig;
	double scale;

	if (PRIV->m_play.m_wid < 0)
		return 1;
	denter(movie_resized);
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
	if (PRIV->m_play.m_wid >= 0) {
		winset(PRIV->m_play.m_wid);
		if (PRIV->m_play.m_bgindex >= 0) {
			RGBcolor((PRIV->m_play.m_bgcolor >> 16) & 0xff,
				 (PRIV->m_play.m_bgcolor >>  8) & 0xff,
				 (PRIV->m_play.m_bgcolor      ) & 0xff);
			clear();
		} else {
			color(PRIV->m_play.m_bgindex);
			clear();
		}
	}
	XDECREF(PRIV->m_play.m_index);
	XDECREF(PRIV->m_play.m_f);
	if (PRIV->m_play.m_frame)
		free(PRIV->m_play.m_frame);
	if (PRIV->m_play.m_bframe)
		free(PRIV->m_play.m_bframe);
	PRIV->m_play.m_wid = -1;
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
		dprintf(("movie_setrate(%lx): writing %c\n", (long) self, msg));
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
	int i;

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
	maxbits = getgdesc(GD_BITS_NORM_SNG_CMODE);
	if (maxbits > 11)
		maxbits = 11;
	/*DEBUG*/maxbits=8;
	init_colorconv();
}
