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

#include "Python.h"
#include "modsupport.h"
#include "pythread.h"
#include "pysema.h"
#include "mmmodule.h"
#include <sys/time.h>

#ifdef MM_DEBUG
static int mm_debug = 0;
#define dprintf(args)		(mm_debug && printf args)
#else
#define dprintf(args)
#endif
#define denter(func)		dprintf(( # func "(%lx)\n", (long) self))

static PyObject *MmError;		/* exception mm.error */

#define CheckMmObject(v)	if ((v)->mm_chanobj == NULL) { \
					PyErr_SetString(MmError, "object already closed"); \
					return NULL; \
				}
int qenter_sync_fd = -1;

void
my_qenter(ev, val)
	long ev, val;
{
	dprintf(("my_qenter(%d,%d) fd=%d\n", ev, val, qenter_sync_fd));
	if (qenter_sync_fd >= 0) {
		char c;

		c = (ev << 2) | val;
		write(qenter_sync_fd, &c, 1);
	}
}
      
static void
mm_armer(arg)
	void *arg;
{
	mmobject *self = (mmobject *) arg;

	denter(mm_armer);

	for (;;) {
		(void) PyThread_down_sema(self->mm_armsema, WAIT_SEMA);

		(void) PyThread_down_sema(self->mm_flagsema, WAIT_SEMA);
		if (self->mm_flags & EXIT) {
			/* we must tell them that we finished arming, */
			/* even if we didn't do a thing */
			if ((self->mm_flags & (ARMING|SYNCARM)) == ARMING)
				my_qenter(self->mm_ev, ARMDONE);
			break;
		}
		PyThread_up_sema(self->mm_flagsema);

		(*self->mm_chanobj->chan_funcs->armer)(self);

		(void) PyThread_down_sema(self->mm_flagsema, WAIT_SEMA);
		self->mm_flags &= ~(ARMING|STOPARM);
		self->mm_flags |= ARMED;
		if (self->mm_flags & SYNCARM) {
			dprintf(("mm_armer(%lx): done synchronous arm\n",
				 (long) self));
			PyThread_up_sema(self->mm_armwaitsema);
		} else {
			dprintf(("mm_armer(%lx): qenter(self->mm_ev, ARMDONE);\n",
				 (long) self));
			my_qenter(self->mm_ev, ARMDONE);
		}
#if 0
		if (self->mm_flags & EXIT)
			break;
#endif
		PyThread_up_sema(self->mm_flagsema);
	}
	PyThread_up_sema(self->mm_flagsema);
	PyThread_up_sema(self->mm_exitsema);
	PyThread_exit_thread();
	/*NOTREACHED*/
}

static void
mm_player(arg)
	void *arg;
{
	mmobject *self = (mmobject *) arg;

	denter(mm_player);

	for (;;) {
		(void) PyThread_down_sema(self->mm_playsema, WAIT_SEMA);

		(void) PyThread_down_sema(self->mm_flagsema, WAIT_SEMA);
		if (self->mm_flags & EXIT) {
			/* we must tell them that we finished playing, */
			/* even if we didn't do a thing */
			if (self->mm_flags & PLAYING)
				my_qenter(self->mm_ev, PLAYDONE);
			break;
		}
		PyThread_up_sema(self->mm_flagsema);

		(*self->mm_chanobj->chan_funcs->player)(self);

		(void) PyThread_down_sema(self->mm_flagsema, WAIT_SEMA);
		self->mm_flags &= ~(PLAYING|STOPPLAY);
		dprintf(("mm_player(%lx): qenter(self->mm_ev, PLAYDONE);\n",
			 (long) self));
		my_qenter(self->mm_ev, PLAYDONE);
#if 0
		if (self->mm_flags & EXIT)
			break;
#endif
		PyThread_up_sema(self->mm_flagsema);
	}
	PyThread_up_sema(self->mm_flagsema);
	PyThread_up_sema(self->mm_exitsema);
	PyThread_exit_thread();
	/*NOTREACHED*/
}

/*
 * resized()
 *	Called when the main loop notices that the window has changed
 *	size or has to be redrawn.
 */
static PyObject *
mm_resized(self, args)
	mmobject *self;
	PyObject *args;
{
	int x, y, w, h;
	CheckMmObject(self);
	denter(mm_resized);
	if (!PyArg_ParseTuple(args, "iiii", &x, &y, &w, &h))
		return NULL;
	if (!(*self->mm_chanobj->chan_funcs->resized)(self, x, y, w, h))
		return NULL;
	Py_INCREF(Py_None);
	return Py_None;
}

/*
 * arm(file, delay, duration, attrdict, anchorlist, syncarm)
 *	Prepare to play file 'file' next, and try to have it done
 *	within 'delay' seconds. 'duration' is an estimate of how long
 *	the arm operation will take. These parameters are only used to
 *	influence scheduling decisions. An arm may be scheduled before
 *	the previous play is finished. Attrdict is a dictionary of
 *	name to value mappings like in the init call. Anchorlist is a
 *	list of tuples where each tuple describes (in a channel
 *	dependent way) how and where to show an anchor.
 *	If 'syncarm' is set, the arm is synchronous, that is, when arm()
 *	returns, the arm is finished.  If 'syncarm' is not set, an
 *	ARMDONE event is generated when the arm finishes.
 *	('delay', 'duration', and 'anchorlist' are not yet implemented.)
 */
static PyObject *
mm_arm(self, args)
	mmobject *self;
	PyObject *args;
{
	int delay, duration, syncarm;
	PyObject *file, *attrdict, *anchorlist;

	CheckMmObject(self);
	denter(mm_arm);
	syncarm = 0;
	if (!PyArg_ParseTuple(args, "OiiOO|i", &file, &delay, &duration,
			      &attrdict, &anchorlist, &syncarm))
		return NULL;
	(void) PyThread_down_sema(self->mm_flagsema, WAIT_SEMA);
	if (self->mm_flags & ARMING) {
		PyThread_up_sema(self->mm_flagsema);
		PyErr_SetString(MmError, "already arming");
		return NULL;
	}
	self->mm_flags |= ARMING;
	self->mm_flags &= ~ARMED;
	if (syncarm)
		self->mm_flags |= SYNCARM;
	else
		self->mm_flags &= ~SYNCARM;
	PyThread_up_sema(self->mm_flagsema);
	if (!(*self->mm_chanobj->chan_funcs->arm)(self, file, delay, duration,
						  attrdict, anchorlist)) {
		(void) PyThread_down_sema(self->mm_flagsema, WAIT_SEMA);
		self->mm_flags &= ~ARMING;
		PyThread_up_sema(self->mm_flagsema);
		return NULL;
	}
	PyThread_up_sema(self->mm_armsema);
	if (syncarm)
		(void) PyThread_down_sema(self->mm_armwaitsema, WAIT_SEMA);
	Py_INCREF(Py_None);
	return Py_None;
}

/*
 * armtime = play()
 *	Start playing the armed node. The actual time needed for the
 *	arm is returned. Calling play before the ARMDONE event is
 *	received is an error, to help in detecting programming errors.
 *	(The return value is not implemented.)
 */
static PyObject *
mm_play(self, args)
	mmobject *self;
	PyObject *args;
{
	CheckMmObject(self);
	denter(mm_play);
	if (!PyArg_NoArgs(args))
		return NULL;
	(void) PyThread_down_sema(self->mm_flagsema, WAIT_SEMA);
	if (self->mm_flags & PLAYING) {
		PyThread_up_sema(self->mm_flagsema);
		PyErr_SetString(MmError, "already playing");
		return NULL;
	}
	if (!(self->mm_flags & ARMED)) {
		PyThread_up_sema(self->mm_flagsema);
		dprintf(("mm_play(%lx): node not armed\n", (long) self));
		PyErr_SetString(MmError, "not armed");
		return NULL;
	}
	self->mm_flags |= PLAYING;
	self->mm_flags &= ~ARMED;
	PyThread_up_sema(self->mm_flagsema);
	if (!(*self->mm_chanobj->chan_funcs->play)(self)) {
		(void) PyThread_down_sema(self->mm_flagsema, WAIT_SEMA);
		self->mm_flags &= ~PLAYING;
		PyThread_up_sema(self->mm_flagsema);
		return NULL;
	}
	PyThread_up_sema(self->mm_playsema);
	Py_INCREF(Py_None);
	return Py_None;
}

/*
 * do_stop()
 *	Stop playing or arming depending on args.
 */
static PyObject *
do_stop(self, args, busyflag, stopflag, func)
	mmobject *self;
	PyObject *args;
	int busyflag, stopflag;
	int (*func) Py_PROTO((mmobject *));
{
	struct timeval tv;

	CheckMmObject(self);
	if (args && !PyArg_NoArgs(args))
		return NULL;

	(void) PyThread_down_sema(self->mm_flagsema, WAIT_SEMA);
	if (self->mm_flags & busyflag) {
		self->mm_flags |= stopflag;
		PyThread_up_sema(self->mm_flagsema);
		if (!(*func)(self))
			return NULL;
		/*DEBUG: wait until player has actually stopped */
		for (;;) {
			(void) PyThread_down_sema(self->mm_flagsema, WAIT_SEMA);
			dprintf(("looping %x\n", self->mm_flags));
			if ((self->mm_flags & busyflag) == 0) {
				PyThread_up_sema(self->mm_flagsema);
				break;
			}
			PyThread_up_sema(self->mm_flagsema);
			tv.tv_sec = 0;
			tv.tv_usec = 5000;
			select(0, NULL, NULL, NULL, &tv);
		}
		dprintf(("exit loop\n"));
	} else {
		/* printf("mmmodule: mm_stop: already stopped\n"); */
		PyThread_up_sema(self->mm_flagsema);
	}
	Py_INCREF(Py_None);
	return Py_None;
}

/*
 * playstop()
 *	Stop playing.
 */
static PyObject *
mm_playstop(self, args)
	mmobject *self;
	PyObject *args;
{
	denter(mm_playstop);
	return do_stop(self, args, PLAYING, STOPPLAY,
		       self->mm_chanobj->chan_funcs->playstop);
}

/*
 * armstop()
 *	Stop arming.
 */
static PyObject *
mm_armstop(self, args)
	mmobject *self;
	PyObject *args;
{
	denter(mm_armstop);
	return do_stop(self, args, ARMING, STOPARM,
		       self->mm_chanobj->chan_funcs->armstop);
}

/*
 * finished()
 *	Called when the node is finished and any node-related data may
 *	be released.  This will also clear the window, if there is one.
 *	This can only be called when not playing anymore.
 */
static PyObject *
mm_finished(self, args)
	mmobject *self;
	PyObject *args;
{
	denter(mm_finished);
	(void) PyThread_down_sema(self->mm_flagsema, WAIT_SEMA);
	if (self->mm_flags & PLAYING) {
		PyThread_up_sema(self->mm_flagsema);
		PyErr_SetString(MmError, "still playing");
		return NULL;
	}
	PyThread_up_sema(self->mm_flagsema);
	if (!PyArg_NoArgs(args))
		return NULL;
	if (!(*self->mm_chanobj->chan_funcs->finished)(self))
		return NULL;
	Py_INCREF(Py_None);
	return Py_None;
}

/*
 * setrate(rate)
 *	Set the playing rate to the given value. Takes effect
 *	immediately.
 */
static PyObject *
mm_setrate(self, args)
	mmobject *self;
	PyObject *args;
{
	double rate;

	CheckMmObject(self);
	denter(mm_setrate);
	if (!PyArg_Parse(args, "d", &rate))
		return NULL;
	if (!(*self->mm_chanobj->chan_funcs->setrate)(self, rate))
		return NULL;
	Py_INCREF(Py_None);
	return Py_None;
}

static void
do_close(self)
	mmobject *self;
{
	int flags;

	/* tell other threads to exit */
	(void) PyThread_down_sema(self->mm_flagsema, WAIT_SEMA);
	flags = self->mm_flags;
	self->mm_flags |= EXIT;
	PyThread_up_sema(self->mm_flagsema);
	if (flags & ARMTHREAD) {
		do_stop(self, NULL, ARMING, STOPARM,
			self->mm_chanobj->chan_funcs->armstop);
		PyThread_up_sema(self->mm_armsema);
	}
	if (flags & PLAYTHREAD) {
		do_stop(self, NULL, PLAYING, STOPPLAY,
			self->mm_chanobj->chan_funcs->playstop);
		PyThread_up_sema(self->mm_playsema);
	}

	/* wait for other threads to exit */
	if (flags & ARMTHREAD)
		(void) PyThread_down_sema(self->mm_exitsema, WAIT_SEMA);
	if (flags & PLAYTHREAD)
		(void) PyThread_down_sema(self->mm_exitsema, WAIT_SEMA);

	/* give module a chance to do some cleanup */
	(*self->mm_chanobj->chan_funcs->dealloc)(self);

	/* now cleanup our own mess */
	Py_XDECREF(self->mm_attrdict);
	self->mm_attrdict = NULL;
	PyThread_free_sema(self->mm_armsema);
	self->mm_armsema = NULL;
	PyThread_free_sema(self->mm_playsema);
	self->mm_playsema = NULL;
	PyThread_free_sema(self->mm_flagsema);
	self->mm_flagsema = NULL;
	PyThread_free_sema(self->mm_exitsema);
	self->mm_exitsema = NULL;
	PyThread_free_sema(self->mm_armwaitsema);
	self->mm_armwaitsema = NULL;
	Py_DECREF(self->mm_chanobj);
	self->mm_chanobj = NULL;
}

/*
 * close()
 *	Stop arming and playing and free all resources.  After this
 *	call, the instance cannot be used anymore.
 */
static PyObject *
mm_close(self)
	mmobject *self;
{
	CheckMmObject(self);
	denter(mm_close);
	do_close(self);
	Py_INCREF(Py_None);
	return Py_None;
}

static PyObject *
mm_do_display(self, args)
	mmobject *self;
	PyObject *args;
{
	CheckMmObject(self);
	denter(mm_do_display);
	if (self->mm_chanobj->chan_funcs->do_display)
		(*self->mm_chanobj->chan_funcs->do_display)(self);
	else {
		PyErr_SetString(PyExc_AttributeError, "do_display");
		return NULL;
	}
	Py_INCREF(Py_None);
	return Py_None;
}

static PyMethodDef channel_methods[] = {
	{"arm",			(PyCFunction)mm_arm, 1},
	{"armstop",		(PyCFunction)mm_armstop},
	{"close",		(PyCFunction)mm_close},
	{"play",		(PyCFunction)mm_play},
	{"playstop",		(PyCFunction)mm_playstop},
	{"resized",		(PyCFunction)mm_resized},
	{"setrate",		(PyCFunction)mm_setrate},
	{"finished",		(PyCFunction)mm_finished},
	{"do_display",		(PyCFunction)mm_do_display},
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
	PyMem_DEL(self);
}

static PyObject *
mm_getattr(self, name)
	mmobject *self;
	char *name;
{
	if (strcmp(name, "armed") == 0)
		return PyInt_FromLong((self->mm_flags & ARMED) != 0);
	return Py_FindMethod(channel_methods, (PyObject *)self, name);
}

static PyTypeObject Mmtype = {
	PyObject_HEAD_INIT(&PyType_Type)
	0,			/*ob_size*/
	"mm",			/*tp_name*/
	sizeof(mmobject),	/*tp_size*/
	0,			/*tp_itemsize*/
	/* methods */
	(destructor)mm_dealloc,	/*tp_dealloc*/
	0,		/*tp_print*/
	(getattrfunc)mm_getattr, /*tp_getattr*/
	0,		/*tp_setattr*/
	0,		/*tp_compare*/
	0,		/*tp_repr*/
};

static mmobject *
newmmobject(ev, attrdict, armsema, playsema, flagsema, exitsema, armwaitsema, chanobj)
	int ev;
	PyObject *attrdict;
	PyThread_type_sema armsema, playsema, flagsema, exitsema, armwaitsema;
	channelobject *chanobj;
{
	mmobject *mmp;
	mmp = PyObject_NEW(mmobject, &Mmtype);
	if (mmp == NULL) {
		PyThread_free_sema(armsema);
		PyThread_free_sema(playsema);
		PyThread_free_sema(flagsema);
		PyThread_free_sema(exitsema);
		PyThread_free_sema(armwaitsema);
		return NULL;
	}
	mmp->mm_ev = ev;
	mmp->mm_flags = 0;
	Py_XINCREF(attrdict);
	mmp->mm_attrdict = attrdict;
	mmp->mm_armsema = armsema;
	mmp->mm_playsema = playsema;
	mmp->mm_flagsema = flagsema;
	mmp->mm_exitsema = exitsema;
	mmp->mm_armwaitsema = armwaitsema;
	Py_INCREF(chanobj);
	mmp->mm_chanobj = chanobj;
	mmp->mm_private = NULL;
	return mmp;
}

/*
 * obj = init(chanobj, ev, attrdict)
 *	Initialization routine.  Chanobj is a channel object which
 *	identifies the channel.
 *	Ev is an event number.  Whenever something 'interesting' happens
 *	the raw channel writes an event of this type onto the file
 *	descriptor that was specified using setsyncfd() to signal this
 *	fact to the main thread. The value of the event will be one of
 *	the following:
 *	ARMDONE - when the current arm is done
 *	PLAYDONE - when the current file has finished playing
 *
 *      Attrdict is a dictionary of attributename to value mappings
 *	specifying things like background color, etc.
 *	
 *	The reason for letting the main program specify the event
 *	number is that this allows the main program to use a different
 *	event number for each instantiation of a raw channel.
 */
static PyObject *
mm_init(self, args)
	PyObject *self;
	PyObject *args;
{
	int ev;
	PyObject *attrdict;
	mmobject *mmp = NULL;
	channelobject *chanobj;
	PyThread_type_sema armsema = NULL, playsema = NULL;
	PyThread_type_sema flagsema = NULL, exitsema = NULL, armwaitsema = NULL;
	int i;

	dprintf(("mm_init\n"));
	if (!PyArg_Parse(args, "(OiO)", &chanobj, &ev, &attrdict))
		return NULL;
	if (!is_channelobject(chanobj)) {
		PyErr_SetString(PyExc_RuntimeError, "first arg must be channel object");
		return NULL;
	}
	dprintf(("mm_init: chanobj = %lx (%s)\n", (long) chanobj,
		 chanobj->ob_type->tp_name));

	/* allocate necessary semaphores */
	if ((armsema = PyThread_allocate_sema(0)) == NULL ||
	    (playsema = PyThread_allocate_sema(0)) == NULL ||
	    (flagsema = PyThread_allocate_sema(1)) == NULL ||
	    (exitsema = PyThread_allocate_sema(0)) == NULL ||
	    (armwaitsema = PyThread_allocate_sema(0)) == NULL) {
		PyErr_SetString(PyExc_IOError, "could not allocate all semaphores");
		if (armsema) PyThread_free_sema(armsema);
		if (playsema) PyThread_free_sema(playsema);
		if (flagsema) PyThread_free_sema(flagsema);
		if (exitsema) PyThread_free_sema(exitsema);
		if (armwaitsema) PyThread_free_sema(armwaitsema);
		return NULL;
	}

	mmp = newmmobject(ev, attrdict, armsema, playsema, flagsema,
			  exitsema, armwaitsema, chanobj);
	dprintf(("newmmobject() --> %lx\n", (long) mmp));
	if (mmp == NULL)
		return NULL;
	if (!(*chanobj->chan_funcs->init)(mmp))
		goto error_return;
	if (!PyThread_start_new_thread(mm_armer, (void *) mmp)) {
		PyErr_SetString(PyExc_IOError, "could not start arm thread");
		goto error_return;
	}
	(void) PyThread_down_sema(mmp->mm_flagsema, WAIT_SEMA);
	mmp->mm_flags |= ARMTHREAD;
	PyThread_up_sema(mmp->mm_flagsema);
	if (!PyThread_start_new_thread(mm_player, (void *) mmp)) {
		PyErr_SetString(PyExc_IOError, "could not start play thread");
		goto error_return;
	}
	(void) PyThread_down_sema(mmp->mm_flagsema, WAIT_SEMA);
	mmp->mm_flags |= PLAYTHREAD;
	PyThread_up_sema(mmp->mm_flagsema);
	return (PyObject *) mmp;

 error_return:
	Py_DECREF(mmp);
	return NULL;
}

/*
 * setsyncfd()
 *	Set a file descriptor on which a byte is written every time
 *	qenter() is called. This enables us to use select() in the
 *	mainline thread and still be awoken even when we ourselves do a
 *	qenter() (which does not wake the select, unlike external
 *	events).
 */
static PyObject *
mm_setsyncfd(self, args)
	PyObject *self;
	PyObject *args;
{
	int fd;
    
	if (!PyArg_Parse(args, "i", &fd))
		return NULL;
	qenter_sync_fd = fd;
	Py_INCREF(Py_None);
	return Py_None;
}

static PyMethodDef mm_methods[] = {
	{"init",		(PyCFunction)mm_init},
	{"setsyncfd",		(PyCFunction)mm_setsyncfd},
	{NULL,		NULL}		/* sentinel */
};

void
initmm()
{
	PyObject *m, *d, *v;

#ifdef MM_DEBUG
	mm_debug = getenv("MMDEBUG") != 0;
#endif

	dprintf(("initmm\n"));

	m = Py_InitModule("mm", mm_methods);
	d = PyModule_GetDict(m);

	v = PyInt_FromLong((long) ARMDONE);
	if (v == NULL || PyDict_SetItemString(d, "armdone", v) != 0)
		Py_FatalError("can't define mm.armdone");

	v = PyInt_FromLong((long) PLAYDONE);
	if (v == NULL || PyDict_SetItemString(d, "playdone", v) != 0)
		Py_FatalError("can't define mm.playdone");

	MmError = PyString_FromString("mm.error");
	if (MmError == NULL || PyDict_SetItemString(d, "error", MmError) != 0)
		Py_FatalError("can't define mm.error");
}
