

static PyObject *MovieCtlObj_MCIsPlayerEventWin(MovieControllerObject *_self, PyObject *_args)
{
	EventRecord e;
	if (!PyArg_ParseTuple(_args, "O&", ToEventRecord, &e))
		return NULL;
	ComponentResult _rv;
	Py_BEGIN_ALLOW_THREADS
	_rv = MCIsPlayerEvent(_self->ob_itself, &e);
	Py_END_ALLOW_THREADS
	return Py_BuildValue("l", _rv);
}

static PyObject *MovieCtlObj_MCDrawWin(MovieControllerObject *_self, PyObject *_args)
{
	PyObject *_res = NULL;
	ComponentResult _rv;
	int w;
	if (!PyArg_ParseTuple(_args, "i", &w))
		return NULL;
	Py_BEGIN_ALLOW_THREADS
	_rv = MCDraw(_self->ob_itself,
	             (GrafPtr)w);
	Py_END_ALLOW_THREADS
	_res = Py_BuildValue("l",
	                     _rv);
	return _res;
}


#define APPEND_WIN_MovieCtlObj_methods \
	{"MCIsPlayerEventWin", (PyCFunction)MovieCtlObj_MCIsPlayerEventWin, 1,\
	"(MSG msg) -> (ComponentResult _rv)"},\
	{"MCDrawWin", (PyCFunction)MovieCtlObj_MCDrawWin, 1,\
	"(GrafPtr ptr) -> (ComponentResult _rv)"},
