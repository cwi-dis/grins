#include "thread.h"
#include "allobjects.h"
#include "modsupport.h"
#include "mmmodule.h"

#ifdef MM_DEBUG
static int imagechannel_debug = 0;
#define dprintf(args)	(imagechannel_debug && printf args)
#else
#define dprintf(args)
#endif

struct image {
	long winid;
};

#define PRIV	((struct image *) self->mm_private)

static int
image_init(self)
	mmobject *self;
{
	dprintf(("image_init\n"));
	self->mm_private = malloc(sizeof(struct image));
	if (self->mm_private == NULL) {
		(void) err_nomem();
		return 0;
	}
	foreground();
	prefposition(100,200,100,200);
	PRIV->winid = winopen("test image");
	grey(1.0);
	clear();
	return 1;
}

static void
image_dealloc(self)
	mmobject *self;
{
	dprintf(("image_dealloc\n"));
	winclose(PRIV->winid);
	free(self->mm_private);
}

static int
image_arm(self, file, delay, duration, attrlist, anchorlist)
	mmobject *self;
	object *file;
	int delay, duration;
	object *attrlist, *anchorlist;
{
	dprintf(("image_arm\n"));
	return 1;
}

static void
image_armer(self)
	mmobject *self;
{
	dprintf(("image_armer\n"));
}

static int
image_play(self)
	mmobject *self;
{
	dprintf(("image_play\n"));
	return 1;
}

static void
image_player(self)
	mmobject *self;
{
	dprintf(("image_player\n"));
	winset(PRIV->winid);
	grey(0.0);
	clear();
}

static int
image_done(self)
	mmobject *self;
{
	dprintf(("image_done\n"));
	return 1;
}

static int
image_resized(self)
	mmobject *self;
{
	dprintf(("image_resized\n"));
	return 1;
}

static int
image_stop(self)
	mmobject *self;
{
	dprintf(("image_stop\n"));
	return 1;
}

static int
image_setrate(self, rate)
	mmobject *self;
	double rate;
{
	dprintf(("image_setrate\n"));
	return 1;
}

static struct mmfuncs image_channel_funcs = {
	image_armer,
	image_player,
	image_done,
	image_resized,
	image_arm,
	image_play,
	image_stop,
	image_setrate,
	image_init,
	image_dealloc,
};

static channelobject *image_chan_obj;

static void
imagechannel_dealloc(self)
	channelobject *self;
{
	dprintf(("imagechannel_dealloc: called\n"));
	if (self != image_chan_obj) {
		dprintf(("imagechannel_dealloc: arg != image_chan_obj\n"));
	}
	DEL(self);
	image_chan_obj = NULL;
}

static object *
imagechannel_getattr(self, name)
	channelobject *self;
	char *name;
{
	err_setstr(AttributeError, name);
	return NULL;
}

static typeobject Imagechanneltype = {
	OB_HEAD_INIT(&Typetype)
	0,			/*ob_size*/
	"channel:image",	/*tp_name*/
	sizeof(channelobject),	/*tp_size*/
	0,			/*tp_itemsize*/
	/* methods */
	imagechannel_dealloc,	/*tp_dealloc*/
	0,			/*tp_print*/
	imagechannel_getattr,	/*tp_getattr*/
	0,			/*tp_setattr*/
	0,			/*tp_compare*/
	0,			/*tp_repr*/
};

static object *
imagechannel_init(self, args)
	channelobject *self;
	object *args;
{
	channelobject *p;

	if (!getnoarg(args))
		return NULL;
	if (image_chan_obj == NULL) {
		dprintf(("imagechannel_init: creating new object\n"));
		image_chan_obj = NEWOBJ(channelobject, &Imagechanneltype);
		if (image_chan_obj == NULL)
			return NULL;
		image_chan_obj->chan_funcs = &image_channel_funcs;
	} else {
		dprintf(("imagechannel_init: return old object\n"));
		INCREF(image_chan_obj);
	}
	return image_chan_obj;
}

static struct methodlist imagechannel_methods[] = {
	{"init",		imagechannel_init},
	{NULL,			NULL}
};

void
initimagechannel()
{
#ifdef MM_DEBUG
	imagechannel_debug = getenv("IMAGEDEBUG") != 0;
#endif
	(void) initmodule("imagechannel", imagechannel_methods);
}
