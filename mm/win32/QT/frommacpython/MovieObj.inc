

static PyObject *MovieObj_SetMovieGWorldWin(MovieObject *_self, PyObject *_args)
{
	PyObject *_res = NULL;
	//CGrafPtr port;
	//GDHandle gdh;
	HWND hwnd;
	if (!PyArg_ParseTuple(_args, "i", &hwnd))
		return NULL;

	GrafPtr grafPtr = CreatePortAssociation((void*)hwnd, NULL, kQTMLHandlePortEvents);
	Py_BEGIN_ALLOW_THREADS
	SetMovieGWorld(_self->ob_itself,
	               CGrafPtr(grafPtr),
	               0);
	Py_END_ALLOW_THREADS
	DestroyPortAssociation(CGrafPtr(grafPtr));

	Py_INCREF(Py_None);
	_res = Py_None;
	return _res;
}

#define APPEND_WIN_MovieObj_methods \
	{"SetMovieGWorldWin", (PyCFunction)MovieObj_SetMovieGWorldWin, 1,\
	"(Rect rc, long flags) -> (ComponentResult _rv)"},
