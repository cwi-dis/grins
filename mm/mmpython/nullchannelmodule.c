#include "Python.h"
#include "modsupport.h"
#include "thread.h"
#include "mmmodule.h"

#ifdef MM_DEBUG
static int nullchannel_debug = 0;
#define dprintf(args)	(nullchannel_debug && printf args)
#else
#define dprintf(args)
#endif
#define denter(func)	dprintf(( # func "(%lx)\n", (long) self))

static void
null_armer(self)
	mmobject *self;
{
	denter(null_armer);
}

static void
null_player(self)
	mmobject *self;
{
	denter(null_player);
}

static int
null_resized(self)
	mmobject *self;
{
	denter(null_resized);
	return 1;
}

static int
null_arm(self, file, delay, duration, attrdict, anchorlist)
	mmobject *self;
	PyObject *file;
	int delay, duration;
	PyObject *attrdict, *anchorlist;
{
	denter(null_arm);
	return 1;
}

static int
null_armstop(self)
	mmobject *self;
{
	denter(null_armstop);
	return 1;
}

static int
null_play(self)
	mmobject *self;
{
	denter(null_play);
	return 1;
}

static int
null_playstop(self)
	mmobject *self;
{
	denter(null_playstop);
	return 1;
}

static int
null_finished(self)
	mmobject *self;
{
	denter(null_finished);
	return 1;
}

static int
null_setrate(self, rate)
	mmobject *self;
	double rate;
{
	denter(null_setrate);
	return 1;
}

static int
null_init(self)
	mmobject *self;
{
	denter(null_init);
	return 1;
}

static void
null_dealloc(self)
	mmobject *self;
{
	denter(null_dealloc);
	if (self->mm_private == NULL)
		return;
}

static struct mmfuncs null_channel_funcs = {
	null_armer,
	null_player,
	null_resized,
	null_arm,
	null_armstop,
	null_play,
	null_playstop,
	null_finished,
	null_setrate,
	null_init,
	null_dealloc,
};

static channelobject *null_chan_obj;

static void
nullchannel_dealloc(self)
	channelobject *self;
{
	if (self != null_chan_obj) {
		dprintf(("nullchannel_dealloc: arg != null_chan_obj\n"));
	}
	PyMem_DEL(self);
	null_chan_obj = NULL;
}

static PyObject *
nullchannel_getattr(self, name)
	channelobject *self;
	char *name;
{
	PyErr_SetString(PyExc_AttributeError, name);
	return NULL;
}

static PyTypeObject Nullchanneltype = {
	PyObject_HEAD_INIT(&PyType_Type)
	0,			/*ob_size*/
	"channel:null",		/*tp_name*/
	sizeof(channelobject),	/*tp_size*/
	0,			/*tp_itemsize*/
	/* methods */
	(destructor)nullchannel_dealloc, /*tp_dealloc*/
	0,			/*tp_print*/
	(getattrfunc)nullchannel_getattr, /*tp_getattr*/
	0,			/*tp_setattr*/
	0,			/*tp_compare*/
	0,			/*tp_repr*/
};

static PyObject *
nullchannel_init(self, args)
	channelobject *self;
	PyObject *args;
{
	channelobject *p;

	if (!PyArg_NoArgs(args))
		return NULL;
	if (null_chan_obj == NULL) {
		null_chan_obj = PyObject_NEW(channelobject, &Nullchanneltype);
		if (null_chan_obj == NULL)
			return NULL;
		null_chan_obj->chan_funcs = &null_channel_funcs;
	} else {
		Py_INCREF(null_chan_obj);
	}
	return (PyObject *) null_chan_obj;
}

static PyMethodDef nullchannel_methods[] = {
	{"init",		(PyCFunction)nullchannel_init},
	{NULL,			NULL}
};

void
initnullchannel()
{
#ifdef MM_DEBUG
	nullchannel_debug = getenv("NULLDEBUG") != 0;
#endif
	dprintf(("initnullchannel\n"));
	(void) Py_InitModule("nullchannel", nullchannel_methods);
}
