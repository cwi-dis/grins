#define ARMDONE		1
#define PLAYDONE	2
#define STOPPED		3

/* flags for mm_flags */
#define ARMING		0x0001
#define PLAYING		0x0002
#define EXIT		0x0004
#define PAUSING		0x0008
#define STOPPING	0x0010
#define ARMED		0x0020

typedef struct {
	OB_HEAD
	int mm_wid;		/* window id */
	int mm_ev;		/* event number */
	int mm_flags;		/* flags */
	type_sema mm_flagsema;	/* semaphore to protect mm_flags */
	object *mm_attrlist;	/* channel attribute list */
	type_sema mm_armsema;	/* semaphore for starting arm thread */
	type_sema mm_playsema;	/* semaphore for starting play thread */
	type_sema mm_exitsema;	/* semaphore used for exiting */
	struct channelobject *mm_chanobj; /* pointers to the channel's functions */
	void *mm_private;	/* private pointer */
	/*DEBUG*/type_sema mm_waitarm;
} mmobject;

struct mmfuncs {
	void (*armer) PROTO((mmobject *));
	void (*player) PROTO((mmobject *));
	int (*done) PROTO((mmobject *));
	int (*resized) PROTO((mmobject *));
	int (*arm) PROTO((mmobject *, object *, int, int, object *, object *));
	int (*play) PROTO((mmobject *));
	int (*stop) PROTO((mmobject *));
	int (*setrate) PROTO((mmobject *, double));
	int (*init) PROTO((mmobject *));
	void (*dealloc) PROTO((mmobject *));
};

typedef struct channelobject {
	OB_HEAD
	struct mmfuncs *chan_funcs;
} channelobject;

#define is_channelobject(op)	(strncmp((op)->ob_type->tp_name, "channel:", 8) == 0)
