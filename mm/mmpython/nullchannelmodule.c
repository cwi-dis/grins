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
null_arm(self, file, delay, duration, attrlist, anchorlist)
	mmobject *self;
	object *file;
	int delay, duration;
	object *attrlist, *anchorlist;
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
	dprintf(("initnullchannel\n"));
	(void) initmodule("nullchannel", nullchannel_methods);
}
