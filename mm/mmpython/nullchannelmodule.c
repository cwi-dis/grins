#include "thread.h"
#include "allobjects.h"
#include "modsupport.h"
#include "mmmodule.h"

#ifdef MM_DEBUG
static int nullchannel_debug = 0;
#define dprintf(args)	(nullchannel_debug && printf args)
#else
#define dprintf(args)
#endif

static int
null_init(self)
	mmobject *self;
{
	dprintf(("null_init\n"));
	return 1;
}

static void
null_dealloc(self)
	mmobject *self;
{
	dprintf(("null_dealloc\n"));
}

static int
null_arm(self, file, delay, duration, attrlist, anchorlist)
	mmobject *self;
	object *file;
	int delay, duration;
	object *attrlist, *anchorlist;
{
	dprintf(("null_arm\n"));
	return 1;
}

static void
null_armer(self)
	mmobject *self;
{
	dprintf(("null_armer\n"));
}

static int
null_play(self)
	mmobject *self;
{
	dprintf(("null_play\n"));
	return 1;
}

static void
null_player(self)
	mmobject *self;
{
	dprintf(("null_player\n"));
}

static int
null_done(self)
	mmobject *self;
{
	dprintf(("null_done\n"));
	return 1;
}

static int
null_resized(self)
	mmobject *self;
{
	dprintf(("null_resized\n"));
	return 1;
}

static int
null_stop(self)
	mmobject *self;
{
	dprintf(("null_stop\n"));
	return 1;
}

static int
null_setrate(self, rate)
	mmobject *self;
	double rate;
{
	dprintf(("null_setrate\n"));
	return 1;
}

static struct mmfuncs null_channel_funcs = {
	null_armer,
	null_player,
	null_done,
	null_resized,
	null_arm,
	null_play,
	null_stop,
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
	DEL(self);
	null_chan_obj = NULL;
}

static object *
nullchannel_getattr(self, name)
	channelobject *self;
	char *name;
{
	err_setstr(AttributeError, name);
	return NULL;
}

static typeobject Nullchanneltype = {
	OB_HEAD_INIT(&Typetype)
	0,			/*ob_size*/
	"channel:null",		/*tp_name*/
	sizeof(channelobject),	/*tp_size*/
	0,			/*tp_itemsize*/
	/* methods */
	nullchannel_dealloc,	/*tp_dealloc*/
	0,			/*tp_print*/
	nullchannel_getattr,	/*tp_getattr*/
	0,			/*tp_setattr*/
	0,			/*tp_compare*/
	0,			/*tp_repr*/
};

static object *
nullchannel_init(self, args)
	channelobject *self;
	object *args;
{
	channelobject *p;

	if (!getnoarg(args))
		return NULL;
	if (null_chan_obj == NULL) {
		null_chan_obj = NEWOBJ(channelobject, &Nullchanneltype);
		if (null_chan_obj == NULL)
			return NULL;
		null_chan_obj->chan_funcs = &null_channel_funcs;
	} else {
		INCREF(null_chan_obj);
	}
	return null_chan_obj;
}

static struct methodlist nullchannel_methods[] = {
	{"init",		nullchannel_init},
	{NULL,			NULL}
};

void
initnullchannel()
{
#ifdef MM_DEBUG
	nullchannel_debug = getenv("NULLDEBUG") != 0;
#endif
	(void) initmodule("nullchannel", nullchannel_methods);
}
