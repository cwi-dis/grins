
static PyObject *Qt_InitializeQTML(PyObject *self, PyObject *args) 
	{
	OSErr _err;
	long flag = kInitializeQTMLUseGDIFlag;
	if (!PyArg_ParseTuple(args, "|i", &flag))
		return NULL;
    _err = InitializeQTML(flag);
	if (_err != noErr)
		{
		PyErr_SetString(PyMac_GetOSErrException(), "InitializeQTML failed");
		return NULL;
		}
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
	OSErr _err;
	FSSpec fileSpec;
	short resRefNum;
	SInt8 permission;
	char *psz;
	if (!PyArg_ParseTuple(_args, "sb",
	                      &psz,
	                      &permission))
		return NULL;
	char sz[256];
	strcpy(sz, psz);
	FSMakeFSSpec(0, 0L, c2pstr(sz), &fileSpec);
	_err = OpenMovieFile(&fileSpec,
	                     &resRefNum,
	                     permission);
	if (_err != noErr)
		{
		PyErr_SetString(PyMac_GetOSErrException(), "OpenMovieFile failed");
		return NULL;
		}
	return Py_BuildValue("h", resRefNum);
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

static PyObject* Qt_GetHWNDPort(PyObject *self, PyObject *args) 
	{
	HWND hwnd;
	if (!PyArg_ParseTuple(args, "i", &hwnd))
		return NULL;
	GrafPtr grafPtr = GetHWNDPort((void*)hwnd);
	return Py_BuildValue("i", int(grafPtr));
	}

static PyObject* Qt_SetDDObject(PyObject *self, PyObject *args) 
	{
	OSErr _err;
	DirectDrawObject *pNewDDObject;
	if (!PyArg_ParseTuple(args, "O", &pNewDDObject))
		return NULL;
	_err = QTSetDDObject(pNewDDObject->pI);
	if (_err != noErr)
		{
		PyErr_SetString(PyMac_GetOSErrException(), "QTSetDDObject failed");
		return NULL;
		}
	Py_INCREF(Py_None);
	return Py_None;
	}

static PyObject* Qt_GetDDObject(PyObject *self, PyObject *args) 
	{
	OSErr _err;
	IDirectDraw *pI = NULL;
	if (!PyArg_ParseTuple(args, ""))
		return NULL;
	_err = QTGetDDObject((void**)&pI);
	if (_err != noErr)
		{
		PyErr_SetString(PyMac_GetOSErrException(), "QTGetDDObject failed");
		return NULL;
		}
	return Py_BuildValue("i", int(pI));
	}

static PyObject* Qt_SetDDPrimarySurface(PyObject *self, PyObject *args) 
	{
	OSErr _err;
	DirectDrawSurfaceObject *pNewDDSObject;
	unsigned long flags = 0;
	if (!PyArg_ParseTuple(args, "O|i", &pNewDDSObject, &flags))
		return NULL;
	_err = QTSetDDPrimarySurface(pNewDDSObject->pI, flags);
	if (_err != noErr)
		{
		PyErr_SetString(PyMac_GetOSErrException(), "SetDDPrimarySurface failed");
		return NULL;
		}
	Py_INCREF(Py_None);
	return Py_None;
	}

static PyObject* Qt_BuildOSType(PyObject *self, PyObject *args) 
	{
	char *psz;
	if (!PyArg_ParseTuple(args, "s", &psz))
		return NULL;
	DWORD t = MAKEFOURCC(psz[3], psz[2], psz[1], psz[0]);
	return PyString_FromStringAndSize((char*)&t, 4);
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
	"(GrafPtr ptr) -> ()"},\
	{"GetHWNDPort", (PyCFunction)Qt_GetHWNDPort, 1,\
	"(HWND hwnd) -> (GrafPtr ptr)"},\
	{"SetDDObject", (PyCFunction)Qt_SetDDObject, 1,\
	"(DirectDrawObject obj) -> ()"},\
	{"GetDDObject", (PyCFunction)Qt_GetDDObject, 1,\
	"() -> (IDirectDrawPtr ptr)"},\
	{"SetDDPrimarySurface", (PyCFunction)Qt_SetDDPrimarySurface, 1,\
	"(DirectDrawSurfaceObject obj) -> ()"},\
	{"BuildOSType", (PyCFunction)Qt_BuildOSType, 1,\
	"(FourCharCode s) -> (OSType)"},
