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
#define denter(func)	dprintf(( # func "(%lx)\n", (long) self))

struct sound_data {
	FILE *f;		/* file from which to read samples */
	int nchannels;		/* # of channels (mono or stereo) */
	int sampwidth;		/* size of samples in bytes */
	int nsamples;	/* # of samples to play */
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
static int device_used;
static long old_rate, sound_rate;
static type_lock device_lock;

static int
sound_init(self)
	mmobject *self;
{
	long buf[2];

	denter(sound_init);
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
	return 1;
}

static void
sound_dealloc(self)
	mmobject *self;
{
	long buf[2];

	denter(sound_dealloc);
	if (self->mm_private == NULL)
		return;
	if (PRIV->s_play.sampbuf)
		free(PRIV->s_play.sampbuf);
	if (PRIV->s_arm.sampbuf)
		free(PRIV->s_arm.sampbuf);
	(void) close(PRIV->s_pipefd[0]);
	(void) close(PRIV->s_pipefd[1]);
	free(self->mm_private);
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

	denter(sound_arm);
	if (!is_dictobject(attrlist)) {
		err_setstr(RuntimeError, "attributes not a dictionary");
		return 0;
	}
	PRIV->s_arm.nchannels = 1;
	PRIV->s_arm.samprate = 8000;
	PRIV->s_arm.sampwidth = 1;
	PRIV->s_arm.offset = 0;
	PRIV->s_playrate = 1.0;
	v = dictlookup(attrlist, "nchannels");
	if (v && is_intobject(v))
		PRIV->s_arm.nchannels = getintvalue(v);
	v = dictlookup(attrlist, "nsampframes");
	if (v && is_intobject(v))
		PRIV->s_arm.nsamples = getintvalue(v) * PRIV->s_arm.nchannels;
	v = dictlookup(attrlist, "sampwidth");
	if (v && is_intobject(v))
		PRIV->s_arm.sampwidth = getintvalue(v);
	v = dictlookup(attrlist, "samprate");
	if (v && is_intobject(v))
		PRIV->s_arm.samprate = getintvalue(v);
	v = dictlookup(attrlist, "offset");
	if (v && is_intobject(v))
		PRIV->s_arm.offset = getintvalue(v);
	PRIV->s_arm.f = getfilefile(file);
	return 1;
}

static void
sound_armer(self)
	mmobject *self;
{
	denter(sound_armer);

	if (PRIV->s_arm.sampbuf) {
		free(PRIV->s_arm.sampbuf);
		PRIV->s_arm.sampbuf = NULL;
	}
	PRIV->s_arm.bufsize = PRIV->s_arm.samprate * PRIV->s_arm.nchannels;
	if (PRIV->s_arm.bufsize > PRIV->s_arm.nsamples)
		PRIV->s_arm.bufsize = PRIV->s_arm.nsamples;
	PRIV->s_arm.sampbuf = malloc(PRIV->s_arm.bufsize*PRIV->s_arm.sampwidth);

	dprintf(("sound_armer(%lx): nchannels: %d, nsamples: %d, nframes: %d, sampwidth: %d, samprate: %d, offset: %d, file: %lx (fd= %d), bufsize = %d\n",
		 (long) self,
		 PRIV->s_arm.nchannels, PRIV->s_arm.nsamples,
		 PRIV->s_arm.nsamples / PRIV->s_arm.nchannels,
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
	denter(sound_play);
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
	int nsamps = PRIV->s_play.nsamples;
	int n;
	int rate;
	int portfd;
	struct pollfd pollfd[2];

	denter(sound_player);

	(void) acquire_lock(device_lock, WAIT_LOCK);
	if (device_used++ == 0) {
		/* first one to open the device */
		buf[0] = AL_OUTPUT_RATE;
		ALgetparams(AL_DEFAULT_DEVICE, buf, 2L);
		sound_rate = old_rate = buf[1];
	}
	if (sound_rate != PRIV->s_play.samprate) {
		if (device_used > 1)
			printf("Warning: two channels with different sampling rates active\n");
		buf[0] = AL_OUTPUT_RATE;
		buf[1] = PRIV->s_play.samprate;
		ALsetparams(AL_DEFAULT_DEVICE, buf, 2L);
		sound_rate = PRIV->s_play.samprate;
	}
	release_lock(device_lock);
	(void) acquire_lock(PRIV->s_lock, WAIT_LOCK);
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
				dprintf(("sound_player(%lx): fread returned %d at %ld (nsamps = %d)\n", (long) self, n, ftell(PRIV->s_play.f), nsamps));
				n = 0;
			} else {
				dprintf(("sound_player(%lx): fread %d samples\n", (long) self, n));
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
		dprintf(("sound_player(%lx): polling\n", (long) self));
		if (poll(&pollfd, sizeof(pollfd)/sizeof(pollfd[0]), -1) < 0) {
			perror("poll");
			break;
		}
		dprintf(("sound_player(%lx): poll returned\n", (long) self));
		if (pollfd[1].revents & POLLIN) {
			char c;
			long filled;
			dprintf(("sound_player(%lx): reading from pipe\n", (long) self));
			(void) read(PRIV->s_pipefd[0], &c, 1);
			dprintf(("sound_player(%lx): read %c\n", (long) self, c));
			(void) acquire_lock(PRIV->s_lock, WAIT_LOCK);
			if (c == 'p' || c == 'r')
				filled = ALgetfilled(PRIV->s_port);
			ALcloseport(PRIV->s_port);
			if (c == 'p' || c == 'r') {
				fseek(PRIV->s_play.f, -(filled + n) * PRIV->s_play.sampwidth, 1);
				dprintf(("sound_player(%lx): filled = %ld, nsamps before = %ld\n", (long) self, filled, nsamps));
				nsamps += filled;
			}
			if (c == 'p') {
				dprintf(("sound_player(%lx): waiting to continue\n", (long) self));
				release_lock(PRIV->s_lock);
				(void) read(PRIV->s_pipefd[0], &c, 1);
				dprintf(("sound_player(%lx): continue playing, read %c\n", (long) self, c));
				(void) acquire_lock(PRIV->s_lock, WAIT_LOCK);
			}
			if (c == 'r') {
				PRIV->s_port = ALopenport("sound channel", "w", config);
				portfd = ALgetfd(PRIV->s_port);
				release_lock(PRIV->s_lock);
				continue;
			} else {
				dprintf(("sound_player(%lx): stopping with playing\n", (long) self));
				goto cleanup;
			}
		}
		if (pollfd[0].revents & (POLLERR|POLLHUP|POLLNVAL)) {
			dprintf(("sound_player(%lx): pollfd[0].revents=%x\n", (long) self, pollfd[0].revents));
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
					dprintf(("sound_player(%lx): write %d samples\n", (long) self, s));
					ALwritesamps(PRIV->s_port, p, s);
				}
				rate++;
				if (rate >= PRIV->s_playrate)
					rate = 0;
				n -= s;
				p += s * PRIV->s_play.sampwidth * PRIV->s_play.nchannels;
			}
		} else {
			dprintf(("sound_player(%lx): write %d samples\n", (long) self, n));
			ALwritesamps(PRIV->s_port, PRIV->s_play.sampbuf, n);
		}
	}
	(void) acquire_lock(PRIV->s_lock, WAIT_LOCK);
	ALcloseport(PRIV->s_port);
 cleanup:
	PRIV->s_port = NULL;
	PRIV->s_flag &= ~PORT_OPEN;
	release_lock(PRIV->s_lock);
	(void) acquire_lock(device_lock, WAIT_LOCK);
	if (--device_used == 0) {
		/* last one to close the audio port */
		buf[0] = AL_OUTPUT_RATE;
		buf[1] = old_rate;
		ALsetparams(AL_DEFAULT_DEVICE, buf, 2L);
	}
	release_lock(device_lock);
}

static int
sound_done(self)
	mmobject *self;
{
	denter(sound_done);
	return 1;
}

static int
sound_resized(self)
	mmobject *self;
{
	denter(sound_resized);
	return 1;
}

static int
sound_stop(self)
	mmobject *self;
{
	denter(sound_stop);
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

	dprintf(("sound_setrate(%lx,%g)\n", (long) self, rate));
	(void) acquire_lock(PRIV->s_lock, WAIT_LOCK);
	if (rate == 0) {
		PRIV->s_flag |= PAUSE;
		msg = 'p';
	} else {
		PRIV->s_flag &= ~PAUSE;
		msg = 'r';
		PRIV->s_playrate = rate;
	}
	/* it can happen that the channel has already been stopped but the */
	/* player thread hasn't reacted yet.  Hence the check on STOPPING. */
	if ((self->mm_flags & (PLAYING | STOPPING)) == PLAYING) {
		dprintf(("sound_setrate(%lx): writing %c\n", (long) self, msg));
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
	dprintf(("initsoundchannel\n"));
	(void) initmodule("soundchannel", soundchannel_methods);
	device_lock = allocate_lock();
	if (device_lock == NULL)
		fatal("soundchannelmodule: can't allocate lock");
}
