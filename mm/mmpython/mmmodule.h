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

typedef struct {
	OB_HEAD
	int mm_wid;		/* window id */
	int mm_ev;		/* event number */
	int mm_flags;		/* flags */
	type_sema mm_flagsema;	/* semaphore to protect mm_flags */
	object *mm_attrdict;	/* channel attribute dictionary */
	type_sema mm_armsema;	/* semaphore for starting arm thread */
	type_sema mm_playsema;	/* semaphore for starting play thread */
	type_sema mm_exitsema;	/* semaphore used for exiting */
	type_sema mm_armwaitsema; /* semaphore to wait for synchronous arm */
	struct channelobject *mm_chanobj; /* pointers to the channel's functions */
	void *mm_private;	/* private pointer */
} mmobject;

struct mmfuncs {
	void (*armer) PROTO((mmobject *));
	void (*player) PROTO((mmobject *));
	int (*resized) PROTO((mmobject *));
	int (*arm) PROTO((mmobject *, object *, int, int, object *, object *));
	int (*armstop) PROTO((mmobject *));
	int (*play) PROTO((mmobject *));
	int (*playstop) PROTO((mmobject *));
	int (*finished) PROTO((mmobject *));
	int (*setrate) PROTO((mmobject *, double));
	int (*init) PROTO((mmobject *));
	void (*dealloc) PROTO((mmobject *));
	void (*do_display) PROTO((mmobject *));
};

typedef struct channelobject {
	OB_HEAD
	struct mmfuncs *chan_funcs;
} channelobject;

#define is_channelobject(op)	(strncmp((op)->ob_type->tp_name, "channel:", 8) == 0)
