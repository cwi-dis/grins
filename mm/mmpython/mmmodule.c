/***********************************************************
Copyright 1991, 1992 by Stichting Mathematisch Centrum, Amsterdam, The
Netherlands.

                        All Rights Reserved

Permission to use, copy, modify, and distribute this software and its 
documentation for any purpose and without fee is hereby granted, 
provided that the above copyright notice appear in all copies and that
both that copyright notice and this permission notice appear in 
supporting documentation, and that the names of Stichting Mathematisch
Centrum or CWI not be used in advertising or publicity pertaining to
distribution of the software without specific, written prior permission.

STICHTING MATHEMATISCH CENTRUM DISCLAIMS ALL WARRANTIES WITH REGARD TO
THIS SOFTWARE, INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY AND
FITNESS, IN NO EVENT SHALL STICHTING MATHEMATISCH CENTRUM BE LIABLE
FOR ANY SPECIAL, INDIRECT OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT
OF OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.

******************************************************************/


/* Mm objects */

/*
 * For extensive comments on this code, see the file mmmodule.doc.
 */

#include <gl.h>
#include "thread.h"
#include "allobjects.h"
#include "modsupport.h"
#include "mmmodule.h"

#ifdef MM_DEBUG
static int mm_debug = 0;
#define dprintf(args)		(mm_debug && printf args)
#else
#define dprintf(args)
#endif
#define denter(func)		dprintf(( # func "(%lx)\n", (long) self))

extern typeobject Mmtype;	/* Really static, forward */

static object *MmError;		/* exception mm.error */

#define CheckMmObject(v)	if ((v)->mm_chanobj == NULL) { \
					err_setstr(MmError, "object already closed"); \
					return NULL; \
				}

static void
mm_armer(arg)
	void *arg;
{
	mmobject *self = (mmobject *) arg;

	denter(mm_armer);

	for (;;) {
		down_sema(self->mm_armsema);

		down_sema(self->mm_flagsema);
		if (self->mm_flags & EXIT)
			break;
		up_sema(self->mm_flagsema);

		(*self->mm_chanobj->chan_funcs->armer)(self);

		down_sema(self->mm_flagsema);
		if (self->mm_flags & EXIT)
			break;
		if (self->mm_flags & STOPPING) {
			dprintf(("mm_armer(%lx): qenter(self->mm_ev, STOPPED);\n", (long) self));
			qenter(self->mm_ev, STOPPED);
		} else {
			dprintf(("mm_armer(%lx): qenter(self->mm_ev, ARMDONE);\n", (long) self));
			qenter(self->mm_ev, ARMDONE);
		}
		self->mm_flags &= ~(ARMING|STOPPING);
		up_sema(self->mm_flagsema);
		/*DEBUG*/up_sema(self->mm_waitarm);
	}
	up_sema(self->mm_flagsema);
	up_sema(self->mm_exitsema);
	exit_thread();
	/*NOTREACHED*/
}

static void
mm_player(arg)
	void *arg;
{
	mmobject *self = (mmobject *) arg;

	denter(mm_player);

	for (;;) {
		down_sema(self->mm_playsema);

		down_sema(self->mm_flagsema);
		if (self->mm_flags & EXIT)
			break;
		up_sema(self->mm_flagsema);

		(*self->mm_chanobj->chan_funcs->player)(self);

		down_sema(self->mm_flagsema);
		if (self->mm_flags & EXIT)
			break;
		if (self->mm_flags & STOPPING) {
			dprintf(("mm_player(%lx): qenter(self->mm_ev, STOPPED);\n", (long) self));
			qenter(self->mm_ev, STOPPED);
		} else {
			dprintf(("mm_player(%lx): qenter(self->mm_ev, PLAYDONE);\n", (long) self));
			qenter(self->mm_ev, PLAYDONE);
		}
		self->mm_flags &= ~(PLAYING|STOPPING);
		up_sema(self->mm_flagsema);
	}
	up_sema(self->mm_flagsema);
	up_sema(self->mm_exitsema);
	exit_thread();
	/*NOTREACHED*/
}

/*
 * done()
 *	Stops the channel, closes the window.
 *	Note 1: disabling a channel is done through this mechanism as
 *	  well. The python wrapper will have to take care of timing
 *	  dependencies.
 */
static object *
mm_done(self, args)
	mmobject *self;
	object *args;
{
	CheckMmObject(self);
	denter(mm_done);
	if (!getnoarg(args))
		return NULL;
	if (!(*self->mm_chanobj->chan_funcs->done)(self))
		return NULL;
	INCREF(None);
	return None;
}

/*
 * resized()
 *	Called when the main loop notices that the window has changed
 *	size.
 */
static object *
mm_resized(self, args)
	mmobject *self;
	object *args;
{
	CheckMmObject(self);
	denter(mm_resized);
	if (!getnoarg(args))
		return NULL;
	if (!(*self->mm_chanobj->chan_funcs->resized)(self))
		return NULL;
	INCREF(None);
	return None;
}

/*
 * arm(file, delay, duration, attrlist, anchorlist)
 *	Prepare to play file 'file' next, and try to have it done
 *	within 'delay seconds. 'duration' is an estimate of how long
 *	the arm operation will take. These parameters are only used to
 *	influence scheduling decisions. An arm may be scheduled before
 *	the previous play is finished. Attrlist is again a list of
 *	(name, value) pairs like in the init call. Anchorlist is a
 *	list of tuples where each tuple describes (in a channel
 *	dependent way) how and where to show an anchor.
 */
static object *
mm_arm(self, args)
	mmobject *self;
	object *args;
{
	int delay, duration;
	object *file, *attrlist, *anchorlist;

	CheckMmObject(self);
	denter(mm_arm);
	if (!getargs(args, "(OiiOO)", &file, &delay, &duration, &attrlist, &anchorlist))
		return NULL;
	down_sema(self->mm_flagsema);
	if (self->mm_flags & ARMING) {
		up_sema(self->mm_flagsema);
		err_setstr(MmError, "already arming");
		return NULL;
	}
	self->mm_flags |= ARMING;
	self->mm_flags &= ~ARMED;
	up_sema(self->mm_flagsema);
	if (!(*self->mm_chanobj->chan_funcs->arm)(self, file, delay, duration, attrlist, anchorlist)) {
		down_sema(self->mm_flagsema);
		self->mm_flags &= ~ARMING;
		up_sema(self->mm_flagsema);
		return NULL;
	}
	down_sema(self->mm_flagsema);
	self->mm_flags |= ARMED;
	up_sema(self->mm_flagsema);
	up_sema(self->mm_armsema);
	/*DEBUG*/down_sema(self->mm_waitarm);
	INCREF(None);
	return None;
}

/*
 * armtime = play()
 *	Start playing the armed node. The actual time needed for the
 *	arm is returned. Calling play before the ARMDONE event is
 *	received is an error, to help in detecting programming errors.
 */
static object *
mm_play(self, args)
	mmobject *self;
	object *args;
{
	CheckMmObject(self);
	denter(mm_play);
	if (!getnoarg(args))
		return NULL;
	down_sema(self->mm_flagsema);
	if (self->mm_flags & PLAYING) {
		up_sema(self->mm_flagsema);
		err_setstr(MmError, "already playing");
		return NULL;
	}
	if (!(self->mm_flags & ARMED)) {
		up_sema(self->mm_flagsema);
		dprintf(("mm_play(%lx): node not armed\n", (long) self));
		err_setstr(MmError, "not armed");
		return NULL;
	}
	self->mm_flags |= PLAYING;
	up_sema(self->mm_flagsema);
	if (!(*self->mm_chanobj->chan_funcs->play)(self)) {
		down_sema(self->mm_flagsema);
		self->mm_flags &= ~PLAYING;
		up_sema(self->mm_flagsema);
		return NULL;
	}
	up_sema(self->mm_playsema);
	INCREF(None);
	return None;
}

/*
 * stop()
 *	Stop playing and arming. A STOPPED event is generated to help
 *	resynchronising. 
 */
static object *
mm_stop(self, args)
	mmobject *self;
	object *args;
{
	CheckMmObject(self);
	denter(mm_stop);
	if (!getnoarg(args))
		return NULL;
	down_sema(self->mm_flagsema);
	if (self->mm_flags & (ARMING|PLAYING)) {
		self->mm_flags |= STOPPING;
		up_sema(self->mm_flagsema);
		if (!(*self->mm_chanobj->chan_funcs->stop)(self))
			return NULL;
		/*DEBUG: wait until armer and player have actually stopped */
		for (;;) {
			down_sema(self->mm_flagsema);
			dprintf(("looping %x\n", self->mm_flags));
			if ((self->mm_flags & (ARMING|PLAYING)) == 0) {
				up_sema(self->mm_flagsema);
				break;
			}
			up_sema(self->mm_flagsema);
			sginap(5); /* release CPU for a bit */
		}
		dprintf(("exit loop\n"));
	} else {
		/* printf("mmmodule: mm_stop: already stopped\n"); */
		up_sema(self->mm_flagsema);
	}
	INCREF(None);
	return None;
}

/*
 * setrate(rate)
 *	Set the playing rate to the given value. Takes effect
 *	immedeately.
 */
static object *
mm_setrate(self, args)
	mmobject *self;
	object *args;
{
	double rate;

	CheckMmObject(self);
	denter(mm_setrate);
	if (!getargs(args, "d", &rate))
		return NULL;
	if (!(*self->mm_chanobj->chan_funcs->setrate)(self, rate))
		return NULL;
	INCREF(None);
	return None;
}

static void
do_close(self)
	mmobject *self;
{
	/* tell other threads to exit */
	down_sema(self->mm_flagsema);
	self->mm_flags |= EXIT;
	if ((self->mm_flags & ARMING) == 0)
		up_sema(self->mm_armsema);
	if ((self->mm_flags & PLAYING) == 0)
		up_sema(self->mm_playsema);
	up_sema(self->mm_flagsema);

	/* wait for other threads to exit */
	down_sema(self->mm_exitsema);
	down_sema(self->mm_exitsema);

	/* give module a chance to do some cleanup */
	(*self->mm_chanobj->chan_funcs->dealloc)(self);

	/* now cleanup our own mess */
	XDECREF(self->mm_attrlist);
	self->mm_attrlist = NULL;
	free_sema(self->mm_armsema);
	self->mm_armsema = NULL;
	free_sema(self->mm_playsema);
	self->mm_playsema = NULL;
	free_sema(self->mm_flagsema);
	self->mm_flagsema = NULL;
	free_sema(self->mm_exitsema);
	self->mm_exitsema = NULL;
	/*DEBUG*/free_sema(self->mm_waitarm);
	/*DEBUG*/self->mm_waitarm = NULL;
	DECREF(self->mm_chanobj);
	self->mm_chanobj = NULL;
}

static object *
mm_close(self)
	mmobject *self;
{
	CheckMmObject(self);
	denter(mm_close);
	do_close(self);
	INCREF(None);
	return None;
}

static struct methodlist channel_methods[] = {
	{"done",		mm_done},
	{"resized",		mm_resized},
	{"arm",			mm_arm},
	{"play",		mm_play},
	{"stop",		mm_stop},
	{"setrate",		mm_setrate},
	{"close",		mm_close},
	{NULL,			NULL}		/* sentinel */
};

/* Mm methods */

static void
mm_dealloc(self)
	mmobject *self;
{
	denter(mm_dealloc);
	if (self->mm_chanobj)
		do_close(self);
	DEL(self);
}

static object *
mm_getattr(self, name)
	mmobject *self;
	char *name;
{
	return findmethod(channel_methods, (object *)self, name);
}

static typeobject Mmtype = {
	OB_HEAD_INIT(&Typetype)
	0,			/*ob_size*/
	"mm",			/*tp_name*/
	sizeof(mmobject),	/*tp_size*/
	0,			/*tp_itemsize*/
	/* methods */
	mm_dealloc,	/*tp_dealloc*/
	0,		/*tp_print*/
	mm_getattr,	/*tp_getattr*/
	0,		/*tp_setattr*/
	0,		/*tp_compare*/
	0,		/*tp_repr*/
};

static object *
newmmobject(wid, ev, attrlist, armsema, playsema, flagsema, exitsema, waitarm, chanobj)
	int wid;
	int ev;
	object *attrlist;
	type_sema armsema, playsema, flagsema, exitsema, waitarm;
	channelobject *chanobj;
{
	mmobject *mmp;
	mmp = NEWOBJ(mmobject, &Mmtype);
	if (mmp == NULL)
		return NULL;
	mmp->mm_wid = wid;
	mmp->mm_ev = ev;
	mmp->mm_flags = 0;
	XINCREF(attrlist);
	mmp->mm_attrlist = attrlist;
	mmp->mm_armsema = armsema;
	mmp->mm_playsema = playsema;
	mmp->mm_flagsema = flagsema;
	mmp->mm_exitsema = exitsema;
	/*DEBUG*/mmp->mm_waitarm = waitarm;
	INCREF(chanobj);
	mmp->mm_chanobj = chanobj;
	mmp->mm_private = NULL;
	return (object *) mmp;
}

/*
 * obj = init(chanobj, wid, ev, attrlist)
 *	Initialization routine.  Chanobj is a channel object which identifies
 *	the channel.   Wid is the window-id of the GL window
 *	to render in (or ignored for windowless channels like audio).
 *	(if the channel has a window).  Ev is an event number.
 *	Whenever something 'interesting' happens the raw channel
 *	deposits an event of this type into the gl event queue to
 *	signal this fact to the main thread. The value of the event
 *	will be one of the following:
 *	ARMDONE - when the current arm is done
 *	PLAYDONE - when the current file has finished playing
 *	STOPPED - A stop command has been processed. This is needed to
 *		synchronize on the stop command (because there might still be
 *		old events in the event queue).
 *
 *	Attrlist is a list of (attributename, value) pairs specifying
 *	things like background color, etc.
 *	
 *	The reason for letting the main program specify the event
 *	number is that this allows the main program to use a different
 *	event number for each instantiation of a raw channel.
 */
static object *
mm_init(self, args)
	mmobject *self;
	object *args;
{
	int wid, ev;
	object *attrlist;
	object *mmp;
	channelobject *chanobj;
	type_sema armsema = NULL, playsema = NULL;
	type_sema flagsema = NULL, exitsema = NULL, waitarm = NULL;
	int i;

	dprintf(("mm_init\n"));
	wid = 0;
	ev = 0;
	attrlist = 0;
	if (!getargs(args, "(OiiO)", &mmp, &wid, &ev, &attrlist))
		return NULL;
	if (!is_channelobject(mmp)) {
		err_setstr(RuntimeError, "first arg must be channel object");
		return NULL;
	}
	dprintf(("mm_init: chanobj = %lx (%s)\n", (long) mmp, mmp->ob_type->tp_name));
	chanobj = (channelobject *) mmp;

	/* allocate necessary semaphores */
	if ((armsema = allocate_sema(0)) == NULL ||
	    (playsema = allocate_sema(0)) == NULL ||
	    (flagsema = allocate_sema(1)) == NULL ||
	    (exitsema = allocate_sema(0)) == NULL ||
	    (waitarm = allocate_sema(0)) == NULL) {
		err_setstr(IOError, "could not allocate all semaphores");
		if (armsema) free_sema(armsema);
		if (playsema) free_sema(playsema);
		if (flagsema) free_sema(flagsema);
		if (exitsema) free_sema(exitsema);
		if (waitarm) free_sema(waitarm);
		return NULL;
	}

	mmp = newmmobject(wid, ev, attrlist, armsema, playsema, flagsema, exitsema, waitarm, chanobj);
	dprintf(("newmmobject() --> %lx\n", (long) mmp));
	if (mmp == NULL ||
	    !(*chanobj->chan_funcs->init)((mmobject *) mmp) ||
	    !start_new_thread(mm_armer, (void *) mmp) ||
	    !start_new_thread(mm_player, (void *) mmp)) {
		/* only the start_thread() calls don't set the error */
		if (!err_occurred())
			err_setstr(IOError, "could not start threads");
		free_sema(armsema);
		free_sema(playsema);
		free_sema(flagsema);
		free_sema(exitsema);
		free_sema(waitarm);
		XDECREF(((mmobject *) mmp)->mm_attrlist);
		DECREF(((mmobject *) mmp)->mm_chanobj);
		DECREF(mmp);
		return NULL;
	}
	return mmp;
}

static struct methodlist mm_methods[] = {
	{"init",		mm_init},
	{NULL,		NULL}		/* sentinel */
};

void
initmm()
{
	object *m, *d, *v;

#ifdef MM_DEBUG
	mm_debug = getenv("MMDEBUG") != 0;
#endif

	dprintf(("initmm\n"));

	m = initmodule("mm", mm_methods);
	d = getmoduledict(m);

	v = newintobject((long) ARMDONE);
	if (v == NULL || dictinsert(d, "armdone", v) != 0)
		fatal("can't define mm.armdone");

	v = newintobject((long) PLAYDONE);
	if (v == NULL || dictinsert(d, "playdone", v) != 0)
		fatal("can't define mm.playdone");

	v = newintobject((long) STOPPED);
	if (v == NULL || dictinsert(d, "stopped", v) != 0)
		fatal("can't define mm.stopped");

	MmError = newstringobject("mm.error");
	if (MmError == NULL || dictinsert(d, "error", MmError) != 0)
		fatal("can't define mm.error");
}
