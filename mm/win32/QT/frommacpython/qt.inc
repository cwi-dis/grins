
static PyObject *Qt_InitializeQTML(PyObject *self, PyObject *args) 
	{
	long flag = kInitializeQTMLUseGDIFlag;
	if (!PyArg_ParseTuple(args, "|i", &flag))
		return NULL;
    InitializeQTML(flag);
	Py_INCREF(Py_None);
	return Py_None;
	}
static PyObject *Qt_TerminateQTML(PyObject *self, PyObject *args) 
	{
	if (!PyArg_ParseTuple(args, ""))
		return NULL;
	TerminateQTML();
	Py_INCREF(Py_None);
	return Py_None;
	}
static PyObject *Qt_FSMakeFSSpec(PyObject *self, PyObject *args) 
	{
	short theFile = 0;
	FSSpec fileSpec;
	char *psz;
	if (!PyArg_ParseTuple(args, "s", &psz))
		return NULL;
	FSMakeFSSpec (0, 0L, c2pstr(psz), &fileSpec);
	/* create and return FSSpec */
	Py_INCREF(Py_None);
	return Py_None;
	}

/* temporary until the above is complete*/
static PyObject *Qt_OpenMovieFileWin(PyObject *_self, PyObject *_args)
{
	PyObject *_res = NULL;
	OSErr _err;
	FSSpec fileSpec;
	short resRefNum;
	SInt8 permission;
	char *psz;
	if (!PyArg_ParseTuple(_args, "sb",
	                      &psz,
	                      &permission))
		return NULL;
	FSMakeFSSpec (0, 0L, c2pstr(psz), &fileSpec);
	_err = OpenMovieFile(&fileSpec,
	                     &resRefNum,
	                     permission);
	if (_err != noErr) return PyMac_Error(_err);
	_res = Py_BuildValue("h",
	                     resRefNum);
	return _res;
}

static PyObject* Qt_SetGWorld(PyObject *self, PyObject *args) 
	{
	HWND hwnd;
	if (!PyArg_ParseTuple(args, "i", &hwnd))
		return NULL;
	SetGWorld(CGrafPtr(GetNativeWindowPort(hwnd)), NULL); 
	Py_INCREF(Py_None);
	return Py_None;
	}
static PyObject* Qt_CreatePortAssociation(PyObject *self, PyObject *args) 
	{
	HWND hwnd;
	if (!PyArg_ParseTuple(args, "i", &hwnd))
		return NULL;
	GrafPtr grafPtr = CreatePortAssociation((void*)hwnd, NULL, kQTMLHandlePortEvents);
	return Py_BuildValue("i", int(grafPtr));
	}
static PyObject* Qt_DestroyPortAssociation(PyObject *self, PyObject *args) 
	{
	int grafPtr;
	if (!PyArg_ParseTuple(args, "i", &grafPtr))
		return NULL;
	DestroyPortAssociation((CGrafPtr)grafPtr);
	Py_INCREF(Py_None);
	return Py_None;
	}


#define APPEND_WIN_Qt_methods \
	{"InitializeQTML", (PyCFunction)Qt_InitializeQTML, 1,\
	"(long flags) -> None"},\
	{"TerminateQTML", (PyCFunction)Qt_TerminateQTML, 1,\
	"() -> None"},\
	{"FSMakeFSSpec", (PyCFunction)Qt_FSMakeFSSpec, 1,\
	"(ConstStr255Param) -> FSSpec fileSpec"},\
	{"OpenMovieFileWin", (PyCFunction)Qt_OpenMovieFileWin, 1,\
	"(FSSpec fileSpec, SInt8 permission) -> (short resRefNum)"},\
	{"SetGWorld", (PyCFunction)Qt_SetGWorld, 1,\
	"(HWND hwnd) -> ()"},\
	{"CreatePortAssociation", (PyCFunction)Qt_CreatePortAssociation, 1,\
	"(HWND hwnd) -> (GrafPtr ptr)"},\
	{"DestroyPortAssociation", (PyCFunction)Qt_DestroyPortAssociation, 1,\
	"(GrafPtr ptr) -> ()"},
