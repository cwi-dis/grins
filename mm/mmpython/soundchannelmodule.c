#include <audio.h>
#include <stropts.h>
#include <poll.h>
#include "thread.h"
#include "allobjects.h"
#include "modsupport.h"
#include "mmmodule.h"

#ifdef MM_DEBUG
static soundchannel_debug = 0;
#define dprintf(args)	(soundchannel_debug && printf args)
#else
#define dprintf(args)
#endif

struct sound_data {
	FILE *f;		/* file from which to read samples */
	int nchannels;		/* # of channels (mono or stereo) */
	int sampwidth;		/* size of samples in bytes */
	int nsampframes;	/* # of samples to play */
	int samprate;		/* sampling frequency */
	long offset;		/* offset in file of first sample */
	int bufsize;		/* size of sampbuf in samples */
	char *sampbuf;		/* buffer used for read/writing samples */
	int sampsread;		/* # of samples in sampbuf */
};
struct sound {
	type_lock s_lock;	/* lock to protect s_flag */
	int s_flag;
	ALport s_port;		/* audio port used for playing sound */
	double s_playrate;	/* speed with which to play samples */
	struct sound_data s_play;
	struct sound_data s_arm;
	int s_pipefd[2];
};
/* values for s_flag */
#define PORT_OPEN	0x01
#define STOP		0x02
#define PAUSE		0x04

#define PRIV	((struct sound *) self->mm_private)

/*
 * module-global variables
 */
static int port_open;
static long old_rate, sound_rate;

static int
sound_init(self)
	mmobject *self;
{
	long buf[2];

	dprintf(("sound_init\n"));
	self->mm_private = malloc(sizeof(struct sound));
	if (self->mm_private == NULL) {
		(void) err_nomem();
		return 0;
	}
	PRIV->s_play.sampbuf = NULL;
	PRIV->s_arm.sampbuf = NULL;
	PRIV->s_lock = allocate_lock();
	if (PRIV->s_lock == NULL) {
		err_setstr(RuntimeError, "cannot allocate lock");
		free(self->mm_private);
		self->mm_private = NULL;
		return 0;
	}
	PRIV->s_flag = 0;
	PRIV->s_port = NULL;
	if (pipe(PRIV->s_pipefd) < 0) {
		err_setstr(RuntimeError, "cannot create pipe");
		free_lock(PRIV->s_lock);
		free(self->mm_private);
		self->mm_private = NULL;
		return 0;
	}
	if (port_open++ == 0) {
		buf[0] = AL_OUTPUT_RATE;
		ALgetparams(AL_DEFAULT_DEVICE, buf, 2L);
		sound_rate = old_rate = buf[1];
	}
	return 1;
}

static void
sound_dealloc(self)
	mmobject *self;
{
	long buf[2];

	dprintf(("sound_dealloc\n"));
	if (self->mm_private == NULL)
		return;
	if (PRIV->s_play.sampbuf)
		free(PRIV->s_play.sampbuf);
	if (PRIV->s_arm.sampbuf)
		free(PRIV->s_arm.sampbuf);
	(void) close(PRIV->s_pipefd[0]);
	(void) close(PRIV->s_pipefd[1]);
	free(self->mm_private);
	/* On last dealloc, set output rate back */
	if (--port_open == 0) {
		buf[0] = AL_OUTPUT_RATE;
		buf[1] = old_rate;
		ALsetparams(AL_DEFAULT_DEVICE, buf, 2L);
	}
}

static int
sound_arm(self, file, delay, duration, attrlist, anchorlist)
	mmobject *self;
	object *file;
	int delay, duration;
	object *attrlist, *anchorlist;
{
	int length, value, i;
	char *name;
	object *n, *v;

	dprintf(("sound_arm\n"));
	if (!is_listobject(attrlist)) {
		err_setstr(RuntimeError, "attributes not a list");
		return 0;
	}
	length = getlistsize(attrlist);
	PRIV->s_arm.nchannels = 1;
	PRIV->s_arm.samprate = 8000;
	PRIV->s_arm.sampwidth = 1;
	PRIV->s_arm.offset = 0;
	PRIV->s_playrate = 1.0;
	for (i = 0; i < length; i++) {
		v = getlistitem(attrlist, i);
		if (!is_tupleobject(v) || gettuplesize(v) != 2) {
			err_setstr(RuntimeError, "attrlist not a proper list");
			return 0;
		}
		n = gettupleitem(v, 0);
		if (!is_stringobject(n)) {
			err_setstr(RuntimeError, "attrlist not a proper list");
			return 0;
		}
		name = getstringvalue(n);
		n = gettupleitem(v, 1);
		if (!is_intobject(n))
			continue;
		value = getintvalue(n);
		if (strcmp(name, "nchannels") == 0)
			PRIV->s_arm.nchannels = value;
		else if (strcmp(name, "nsampframes") == 0)
			PRIV->s_arm.nsampframes = value;
		else if (strcmp(name, "sampwidth") == 0)
			PRIV->s_arm.sampwidth = value;
		else if (strcmp(name, "samprate") == 0)
			PRIV->s_arm.samprate = value;
		else if (strcmp(name, "offset") == 0)
			PRIV->s_arm.offset = value;
	}
	PRIV->s_arm.f = getfilefile(file);
	return 1;
}

static void
sound_armer(self)
	mmobject *self;
{
	dprintf(("sound_armer\n"));

	if (PRIV->s_arm.sampbuf) {
		free(PRIV->s_arm.sampbuf);
		PRIV->s_arm.sampbuf = NULL;
	}
	PRIV->s_arm.bufsize = PRIV->s_arm.samprate * PRIV->s_arm.nchannels;
	if (PRIV->s_arm.bufsize > PRIV->s_arm.nsampframes)
		PRIV->s_arm.bufsize = PRIV->s_arm.nsampframes;
	PRIV->s_arm.sampbuf = malloc(PRIV->s_arm.bufsize*PRIV->s_arm.sampwidth);

	dprintf(("nchannels: %d, nsampframes: %d, sampwidth: %d, samprate: %d, offset: %d, file: %lx (fd= %d), bufsize = %d\n",
		 PRIV->s_arm.nchannels, PRIV->s_arm.nsampframes,
		 PRIV->s_arm.sampwidth, PRIV->s_arm.samprate,
		 PRIV->s_arm.offset, PRIV->s_arm.f, fileno(PRIV->s_arm.f),
		 PRIV->s_arm.bufsize));

	fseek(PRIV->s_arm.f, PRIV->s_arm.offset, 0);
	PRIV->s_arm.sampsread = fread(PRIV->s_arm.sampbuf, PRIV->s_arm.sampwidth, PRIV->s_arm.bufsize, PRIV->s_arm.f);
}

static int
sound_play(self)
	mmobject *self;
{
	dprintf(("sound_play\n"));
	PRIV->s_flag = 0;
	if (PRIV->s_play.sampbuf)
		free(PRIV->s_play.sampbuf);
	PRIV->s_play = PRIV->s_arm;
	PRIV->s_arm.sampbuf = NULL;
	return 1;
}

static void
sound_player(self)
	mmobject *self;
{
	long buf[2];
	ALconfig config;
	int nsamps = PRIV->s_play.nsampframes;
	int n;
	int rate;
	int portfd;
	struct pollfd pollfd[2];

	dprintf(("sound_player\n"));

	(void) acquire_lock(PRIV->s_lock, WAIT_LOCK);
	if (sound_rate != PRIV->s_play.samprate) {
		buf[0] = AL_OUTPUT_RATE;
		buf[1] = PRIV->s_play.samprate;
		ALsetparams(AL_DEFAULT_DEVICE, buf, 2L);
		sound_rate = PRIV->s_play.samprate;
	}
	config = ALnewconfig();
	ALsetwidth(config, PRIV->s_play.sampwidth);
	ALsetchannels(config, PRIV->s_play.nchannels);
	
	PRIV->s_port = ALopenport("sound channel", "w", config);
	PRIV->s_flag |= PORT_OPEN;
	portfd = ALgetfd(PRIV->s_port);
	release_lock(PRIV->s_lock);

	rate = 0;
	while (nsamps > 0 || ALgetfilled(PRIV->s_port) > 0) {
		if (PRIV->s_play.sampsread > 0) {
			n = PRIV->s_play.sampsread;
			PRIV->s_play.sampsread = 0;
		} else if (nsamps > 0) {
			n = nsamps;
			if (n > PRIV->s_play.bufsize)
				n = PRIV->s_play.bufsize;
			n = fread(PRIV->s_play.sampbuf, PRIV->s_play.sampwidth,
				  n, PRIV->s_play.f);
			if (n <= 0) {
				dprintf(("fread returned %d at %ld (nsamps = %d)\n", n, ftell(PRIV->s_play.f), nsamps));
			} else {
				dprintf(("fread %d samples\n", n));
			}
		} else
			n = 0;

		if (n == 0)
			ALsetfillpoint(PRIV->s_port, ALgetqueuesize(config));
		else
			ALsetfillpoint(PRIV->s_port, n);
		pollfd[0].fd = portfd;
		pollfd[0].events = POLLOUT;
		pollfd[0].revents = 0;
		pollfd[1].fd = PRIV->s_pipefd[0];
		pollfd[1].events = POLLIN;
		pollfd[1].revents = 0;
		dprintf(("polling\n"));
		if (poll(&pollfd, sizeof(pollfd)/sizeof(pollfd[0]), -1) < 0) {
			perror("poll");
			break;
		}
		dprintf(("poll returned\n"));
		if (pollfd[1].revents & POLLIN) {
			char c;
			long filled;
			dprintf(("reading from pipe\n"));
			(void) read(PRIV->s_pipefd[0], &c, 1);
			dprintf(("player: read %c\n", c));
			(void) acquire_lock(PRIV->s_lock, WAIT_LOCK);
			if (c == 'p' || c == 'r')
				filled = ALgetfilled(PRIV->s_port);
			ALcloseport(PRIV->s_port);
			if (c == 'p' || c == 'r') {
				fseek(PRIV->s_play.f, -(filled - n) * PRIV->s_play.sampwidth, 1);
				nsamps += filled;
				PRIV->s_play.nsampframes = nsamps;
			}
			if (c == 'p') {
				dprintf(("waiting to continue\n"));
				release_lock(PRIV->s_lock);
				(void) read(PRIV->s_pipefd[0], &c, 1);
				dprintf(("continue playing, read %c\n", c));
				(void) acquire_lock(PRIV->s_lock, WAIT_LOCK);
			}
			if (c == 'r') {
				PRIV->s_port = ALopenport("sound channel", "w", config);
				portfd = ALgetfd(PRIV->s_port);
				release_lock(PRIV->s_lock);
				continue;
			} else {
				PRIV->s_port = NULL;
				PRIV->s_flag &= ~PORT_OPEN;
				release_lock(PRIV->s_lock);
				dprintf(("stopping with playing\n"));
				return;
			}
		}
		if (pollfd[0].revents & (POLLERR|POLLHUP|POLLNVAL)) {
			dprintf(("pollfd[0].revents=%x\n",pollfd[0].revents));
			break;
		}
		if (n == 0)
			continue;
		nsamps -= n;
		if (PRIV->s_playrate > 1) {
			int s = PRIV->s_play.bufsize / 30;
			char *p = PRIV->s_play.sampbuf;
			while (n > 0) {
				if (s > n)
					s = n;
				if (rate == 0) {
					dprintf(("write %d samples\n", s));
					ALwritesamps(PRIV->s_port, p, s);
				}
				rate++;
				if (rate >= PRIV->s_playrate)
					rate = 0;
				n -= s;
				p += s * PRIV->s_play.sampwidth * PRIV->s_play.nchannels;
			}
		} else {
			dprintf(("write %d samples\n", n));
			ALwritesamps(PRIV->s_port, PRIV->s_play.sampbuf, n);
		}
	}
	(void) acquire_lock(PRIV->s_lock, WAIT_LOCK);
	ALcloseport(PRIV->s_port);
	PRIV->s_port = NULL;
	PRIV->s_flag &= ~PORT_OPEN;
	release_lock(PRIV->s_lock);
}

static int
sound_done(self)
	mmobject *self;
{
	dprintf(("sound_done\n"));
	return 1;
}

static int
sound_resized(self)
	mmobject *self;
{
	dprintf(("sound_resized\n"));
	return 1;
}

static int
sound_stop(self)
	mmobject *self;
{
	dprintf(("sound_stop\n"));
	(void) acquire_lock(PRIV->s_lock, WAIT_LOCK);
	if (PRIV->s_flag & PORT_OPEN) {
		PRIV->s_flag |= STOP;
		(void) write(PRIV->s_pipefd[1], "s", 1);
	}
	release_lock(PRIV->s_lock);
	return 1;
}

static int
sound_setrate(self, rate)
	mmobject *self;
	double rate;
{
	char msg;

	dprintf(("sound_setrate(%g)\n", rate));
	(void) acquire_lock(PRIV->s_lock, WAIT_LOCK);
	if (rate == 0) {
		PRIV->s_flag |= PAUSE;
		msg = 'p';
	} else {
		PRIV->s_flag &= ~PAUSE;
		msg = 'r';
		PRIV->s_playrate = rate;
	}
	if (self->mm_flags & PLAYING) {
		dprintf(("setrate: writing %c\n", msg));
		(void) write(PRIV->s_pipefd[1], &msg, 1);
	}
	release_lock(PRIV->s_lock);
	return 1;
}

static struct mmfuncs sound_channel_funcs = {
	sound_armer,
	sound_player,
	sound_done,
	sound_resized,
	sound_arm,
	sound_play,
	sound_stop,
	sound_setrate,
	sound_init,
	sound_dealloc,
};

static channelobject *sound_chan_obj;

static void
soundchannel_dealloc(self)
	channelobject *self;
{
	dprintf(("soundchannel_dealloc: called\n"));
	if (self != sound_chan_obj) {
		dprintf(("soundchannel_dealloc: arg != sound_chan_obj\n"));
	}
	DEL(self);
	sound_chan_obj = NULL;
}

static object *
soundchannel_getattr(self, name)
	channelobject *self;
	char *name;
{
	err_setstr(AttributeError, name);
	return NULL;
}

static typeobject Soundchanneltype = {
	OB_HEAD_INIT(&Typetype)
	0,			/*ob_size*/
	"channel:sound",	/*tp_name*/
	sizeof(channelobject),	/*tp_size*/
	0,			/*tp_itemsize*/
	/* methods */
	soundchannel_dealloc,	/*tp_dealloc*/
	0,			/*tp_print*/
	soundchannel_getattr,	/*tp_getattr*/
	0,			/*tp_setattr*/
	0,			/*tp_compare*/
	0,			/*tp_repr*/
};

static object *
soundchannel_init(self, args)
	channelobject *self;
	object *args;
{
	channelobject *p;

	if (!getnoarg(args))
		return NULL;
	if (sound_chan_obj == 0) {
		dprintf(("soundchannel_init: creating new object\n"));
		sound_chan_obj = NEWOBJ(channelobject, &Soundchanneltype);
		if (sound_chan_obj == NULL)
			return NULL;
		sound_chan_obj->chan_funcs = &sound_channel_funcs;
	} else {
		dprintf(("soundchannel_init: return old object\n"));
		INCREF(sound_chan_obj);
	}

	return sound_chan_obj;
}

static struct methodlist soundchannel_methods[] = {
	{"init",		soundchannel_init},
	{NULL,			NULL}
};

void
initsoundchannel()
{
#ifdef MM_DEBUG
	soundchannel_debug = getenv("SOUNDDEBUG") != 0;
#endif
	(void) initmodule("soundchannel", soundchannel_methods);
}
