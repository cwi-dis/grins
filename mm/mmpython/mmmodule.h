#define ARMDONE		1
#define PLAYDONE	2

/* flags for mm_flags */
#define ARMING		0x0001	/* channel is arming */
#define PLAYING		0x0002	/* channel is playing */
#define EXIT		0x0004	/* channel must exit */
#define PAUSING		0x0008	/* channel is pausing */
#define STOPPLAY	0x0010	/* channel must stop playing */
#define STOPARM		0x0020	/* channel must stop arming */
#define ARMED		0x0040	/* channel finished arming */
#define SYNCARM		0x0080	/* arm synchronously */
#define ARMTHREAD	0x0100	/* an arm thread exists */
#define PLAYTHREAD	0x0200	/* a play thread exists */

typedef struct {
	PyObject_HEAD
	int mm_ev;		/* event number */
	int mm_flags;		/* flags */
	type_sema mm_flagsema;	/* semaphore to protect mm_flags */
	PyObject *mm_attrdict;	/* channel attribute dictionary */
	type_sema mm_armsema;	/* semaphore for starting arm thread */
	type_sema mm_playsema;	/* semaphore for starting play thread */
	type_sema mm_exitsema;	/* semaphore used for exiting */
	type_sema mm_armwaitsema; /* semaphore to wait for synchronous arm */
	struct channelobject *mm_chanobj; /* pointers to the channel's functions */
	void *mm_private;	/* private pointer */
} mmobject;

struct mmfuncs {
	void (*armer) Py_PROTO((mmobject *));
	void (*player) Py_PROTO((mmobject *));
	int (*resized) Py_PROTO((mmobject *, int, int, int, int));
	int (*arm) Py_PROTO((mmobject *, PyObject *, int, int, PyObject *, PyObject *));
	int (*armstop) Py_PROTO((mmobject *));
	int (*play) Py_PROTO((mmobject *));
	int (*playstop) Py_PROTO((mmobject *));
	int (*finished) Py_PROTO((mmobject *));
	int (*setrate) Py_PROTO((mmobject *, double));
	int (*init) Py_PROTO((mmobject *));
	void (*dealloc) Py_PROTO((mmobject *));
	void (*do_display) Py_PROTO((mmobject *));
};

typedef struct channelobject {
	PyObject_HEAD
	struct mmfuncs *chan_funcs;
} channelobject;

#define is_channelobject(op)	(strncmp((op)->ob_type->tp_name, "channel:", 8) == 0)

extern void my_qenter Py_PROTO((long, long));
