

static PyObject *MovieCtlObj_MCIsPlayerEventWin(MovieControllerObject *_self, PyObject *_args)
{
	HWND hwnd;
	UINT message;
	WPARAM wParam;
	LPARAM lParam;
	long time;
	POINT pt;
	if (!PyArg_ParseTuple(_args, "(iiiii(ii))", &hwnd, &message,&wParam,&lParam, &time, &pt.x, &pt.y))
		return NULL;
	MSG msg;
    msg.hwnd = hwnd;
    msg.message = message;
    msg.wParam = wParam;
    msg.lParam = lParam;
    msg.time = time; 
	msg.pt = pt;

	PyObject *_res = NULL;
	ComponentResult _rv;
	EventRecord e;
	WinEventToMacEvent(&msg, &e);
	Py_BEGIN_ALLOW_THREADS
	_rv = MCIsPlayerEvent(_self->ob_itself, &e);
	Py_END_ALLOW_THREADS
	_res = Py_BuildValue("l", _rv);
	return _res;
}

static PyObject *MovieCtlObj_MCDrawWin(MovieControllerObject *_self, PyObject *_args)
{
	PyObject *_res = NULL;
	ComponentResult _rv;
	int w;
	if (!PyArg_ParseTuple(_args, "i", &w))
		return NULL;
	_rv = MCDraw(_self->ob_itself,
	             (GrafPtr)w);
	_res = Py_BuildValue("l",
	                     _rv);
	return _res;
}


#define APPEND_WIN_MovieCtlObj_methods \
	{"MCIsPlayerEventWin", (PyCFunction)MovieCtlObj_MCIsPlayerEventWin, 1,\
	"(MSG msg) -> (ComponentResult _rv)"},\
	{"MCDrawWin", (PyCFunction)MovieCtlObj_MCDrawWin, 1,\
	"(GrafPtr ptr) -> (ComponentResult _rv)"},
