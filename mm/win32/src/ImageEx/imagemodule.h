

typedef struct {
	PyObject_HEAD
	struct channelobject *gt_chanobj; /* pointers to the channel's functions */
	void *gt_private;	/* private pointer */
} gtobject;

struct gtfuncs {
	//void (*do_display) Py_PROTO((gtobject *));
};

typedef struct channelobject {
	PyObject_HEAD
	struct gtfuncs *chan_funcs;
} channelobject;

#define is_channelobject(op)	(strncmp((op)->ob_type->tp_name, "channel:", 8) == 0)

