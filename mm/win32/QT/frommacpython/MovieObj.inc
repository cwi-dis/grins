
static PyObject *MovieObj_NewMovieControllerWin(MovieObject *_self, PyObject *_args)
{
	PyObject *_res = NULL;
	MovieController _rv;
	Rect movieRect;
	int l, t, r, b;
	long someFlags = mcTopLeftMovie | mcWithFrame;
	if (!PyArg_ParseTuple(_args, "(iiii)|l",
	                      &l, &t, &r, &b,
	                      &someFlags))
		return NULL;
	movieRect.left = short(l); movieRect.top = short(t); 
	movieRect.right = short(r); movieRect.bottom = short(b); 
	_rv = NewMovieController(_self->ob_itself,
	                         &movieRect,
	                         someFlags);
	_res = Py_BuildValue("O&",
	                     MovieCtlObj_New, _rv);
	return _res;
}

#define APPEND_WIN_MovieObj_methods \
	{"NewMovieControllerWin", (PyCFunction)MovieObj_NewMovieControllerWin, 1,\
	"(Rect rc, long flags) -> (ComponentResult _rv)"},
