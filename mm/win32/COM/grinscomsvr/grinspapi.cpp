
/*************************************************************************
Copyright 1991-2000 by Oratrix Development BV, Amsterdam, The Netherlands.

                        All Rights Reserved

**************************************************************************/
#include "stdafx.h"

#include "Python.h"

#include "comobj.h"
#include "commod.h"

#include "mtpycall.h"

static PyObject *errorObject;

PyInterpreterState*
PyCallbackBlock::s_interpreterState = NULL;

void seterror(const char *msg){PyErr_SetString(errorObject, msg);}

/////////////////////

#define RELEASE(x) if(x) x->Release();x=NULL;

static void
seterror(const char *funcname, HRESULT hr)
{
	char* pszmsg;
	::FormatMessage( 
		 FORMAT_MESSAGE_ALLOCATE_BUFFER | FORMAT_MESSAGE_FROM_SYSTEM,
		 NULL,
		 hr,
		 MAKELANGID(LANG_NEUTRAL, SUBLANG_DEFAULT), // Default language
		 (LPTSTR) &pszmsg,
		 0,
		 NULL 
		);
	PyErr_Format(errorObject, "%s failed, error = %s", funcname, pszmsg);
	LocalFree(pszmsg);
}


///////////////////////////////////////////
// Objects declarations

typedef struct {
	PyObject_HEAD
	/* XXXX Add your own stuff here */
	GRiNSPlayerComModule *pModule;
} ComModuleObject;

staticforward PyTypeObject ComModuleType;

static ComModuleObject *
newComModuleObject()
{
	ComModuleObject *self = PyObject_NEW(ComModuleObject, &ComModuleType);
	if (self == NULL) return NULL;
	self->pModule = new GRiNSPlayerComModule(GetCurrentThreadId());
	return self;
}

static ComModuleObject *comModuleObject;

///////////////////////////////////////////
// Objects

////////////////////////////////////////////
// ComModule object 

static char ComModule_RegisterClassObjects__doc__[] =
""
;
static PyObject *
ComModule_RegisterClassObjects(ComModuleObject *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args, ""))
		return NULL;
	
	HRESULT hr = self->pModule->registerClassObjects();
	if (FAILED(hr)){
		seterror("RegisterClassObjects", hr);
		return NULL;
	}
	Py_INCREF(Py_None);
	return Py_None;
}

static char ComModule_Lock__doc__[] =
""
;
static PyObject *
ComModule_Lock(ComModuleObject *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args, ""))
		return NULL;
	self->pModule->lock();
	Py_INCREF(Py_None);
	return Py_None;
}

static char ComModule_Unlock__doc__[] =
""
;
static PyObject *
ComModule_Unlock(ComModuleObject *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args, ""))
		return NULL;
	self->pModule->unlock();
	Py_INCREF(Py_None);
	return Py_None;
}

static char ComModule_SetListener__doc__[] =
""
;
static PyObject *
ComModule_SetListener(ComModuleObject *self, PyObject *args)
{
	HWND hwnd;
	if (!PyArg_ParseTuple(args, "i", &hwnd))
		return NULL;
	self->pModule->setListenerHwnd(hwnd);
	Py_INCREF(Py_None);
	return Py_None;
}

static char ComModule_SetPyListener__doc__[] =
""
;
static PyObject *
ComModule_SetPyListener(ComModuleObject *self, PyObject *args)
{
	PyObject *obj;
	if (!PyArg_ParseTuple(args, "O", &obj))
		return NULL;
	self->pModule->setPyListener(obj);
	Py_INCREF(Py_None);
	return Py_None;
}


static char ComModule_AdviceNewPeerWnd__doc__[] =
""
;
static PyObject *
ComModule_AdviceNewPeerWnd(ComModuleObject *self, PyObject *args)
{
	int docid, wndid, w, h;
	char *pszTitle;
	if(!PyArg_ParseTuple(args, "iiiis", &docid, &wndid, &w, &h, &pszTitle))
		return NULL;
	self->pModule->adviceNewPeerWnd(docid, wndid, w, h, pszTitle);
	Py_INCREF(Py_None);
	return Py_None;
}

static char ComModule_AdviceClosePeerWnd__doc__[] =
""
;
static PyObject *
ComModule_AdviceClosePeerWnd(ComModuleObject *self, PyObject *args)
{
	int docid, wndid;
	if(!PyArg_ParseTuple(args, "ii", &docid, &wndid))
		return NULL;
	self->pModule->adviceClosePeerWnd(docid, wndid);
	Py_INCREF(Py_None);
	return Py_None;
}

static char ComModule_AdviceSetCursor__doc__[] =
""
;
static PyObject *
ComModule_AdviceSetCursor(ComModuleObject *self, PyObject *args)
{
	int id;
	char *cursor;
	if(!PyArg_ParseTuple(args, "is", &id, &cursor))
		return NULL;
	self->pModule->adviceSetCursor(id, cursor);
	Py_INCREF(Py_None);
	return Py_None;
}

static char ComModule_AdviceSetDur__doc__[] =
""
;
static PyObject *
ComModule_AdviceSetDur(ComModuleObject *self, PyObject *args)
{
	int id;
	double dur;
	if(!PyArg_ParseTuple(args, "id", &id, &dur))
		return NULL;
	self->pModule->adviceSetDur(id, dur);
	Py_INCREF(Py_None);
	return Py_None;
}

static char ComModule_AdviceSetFrameRate__doc__[] =
""
;
static PyObject *
ComModule_AdviceSetFrameRate(ComModuleObject *self, PyObject *args)
{
	int id;
	int fr;
	if(!PyArg_ParseTuple(args, "ii", &id, &fr))
		return NULL;
	self->pModule->adviceSetFrameRate(id, fr);
	Py_INCREF(Py_None);
	return Py_None;
}

static struct PyMethodDef ComModule_methods[] = {
	{"RegisterClassObjects", (PyCFunction)ComModule_RegisterClassObjects, METH_VARARGS, ComModule_RegisterClassObjects__doc__},
	{"Lock", (PyCFunction)ComModule_Lock, METH_VARARGS, ComModule_Lock__doc__},
	{"Unlock", (PyCFunction)ComModule_Unlock, METH_VARARGS, ComModule_Unlock__doc__},
	{"SetListener", (PyCFunction)ComModule_SetListener, METH_VARARGS, ComModule_SetListener__doc__},
	{"SetPyListener", (PyCFunction)ComModule_SetPyListener, METH_VARARGS, ComModule_SetPyListener__doc__},
	{"AdviceNewPeerWnd", (PyCFunction)ComModule_AdviceNewPeerWnd, METH_VARARGS, ComModule_AdviceNewPeerWnd__doc__},
	{"AdviceClosePeerWnd", (PyCFunction)ComModule_AdviceClosePeerWnd, METH_VARARGS, ComModule_AdviceClosePeerWnd__doc__},
	{"AdviceSetCursor", (PyCFunction)ComModule_AdviceSetCursor, METH_VARARGS, ComModule_AdviceSetCursor__doc__},
	{"AdviceSetDur", (PyCFunction)ComModule_AdviceSetDur, METH_VARARGS, ComModule_AdviceSetDur__doc__},
	{"AdviceSetFrameRate", (PyCFunction)ComModule_AdviceSetFrameRate, METH_VARARGS, ComModule_AdviceSetFrameRate__doc__},
	{NULL, (PyCFunction)NULL, 0, NULL}		/* sentinel */
};

static void
ComModule_dealloc(ComModuleObject *self)
{
	/* XXXX Add your own cleanup code here */
	if(self->pModule) delete self->pModule;
	PyMem_DEL(self);
}

static PyObject *
ComModule_getattr(ComModuleObject *self, char *name)
{
	/* XXXX Add your own getattr code here */
	return Py_FindMethod(ComModule_methods, (PyObject *)self, name);
}

static char ComModuleType__doc__[] =
""
;

static PyTypeObject ComModuleType = {
	PyObject_HEAD_INIT(&PyType_Type)
	0,				/*ob_size*/
	"ComModule",			/*tp_name*/
	sizeof(ComModuleObject),		/*tp_basicsize*/
	0,				/*tp_itemsize*/
	/* methods */
	(destructor)ComModule_dealloc,	/*tp_dealloc*/
	(printfunc)0,		/*tp_print*/
	(getattrfunc)ComModule_getattr,	/*tp_getattr*/
	(setattrfunc)0,	/*tp_setattr*/
	(cmpfunc)0,		/*tp_compare*/
	(reprfunc)0,		/*tp_repr*/
	0,			/*tp_as_number*/
	0,		/*tp_as_sequence*/
	0,		/*tp_as_mapping*/
	(hashfunc)0,		/*tp_hash*/
	(ternaryfunc)0,		/*tp_call*/
	(reprfunc)0,		/*tp_str*/

	/* Space for future expansion */
	0L,0L,0L,0L,
	ComModuleType__doc__ /* Documentation string */
};

// End of code for ComModule object 
////////////////////////////////////////////



///////////////////////////////////

static char CreateComModule__doc__[] =
""
;
static PyObject*
CreateComModule(PyObject *self, PyObject *args) 
	{
	if (!PyArg_ParseTuple(args, ""))
		return NULL;
	return (PyObject*) newComModuleObject();	
	}

static char RegisterServer__doc__[] =
""
;
static PyObject*
RegisterServer(PyObject *self, PyObject *args) 
	{
	if (!PyArg_ParseTuple(args, ""))
		return NULL;
	if(!RegisterGRiNSPlayerAutoServer()){
		seterror("RegisterServer failed");
		return NULL;
		}
	Py_INCREF(Py_None);
	return Py_None;
	}

static char UnregisterServer__doc__[] =
""
;
static PyObject*
UnregisterServer(PyObject *self, PyObject *args) 
	{
	if (!PyArg_ParseTuple(args, ""))
		return NULL;
	if(!UnregisterGRiNSPlayerAutoServer()){
		seterror("UnregisterServer failed");
		return NULL;
		}
	Py_INCREF(Py_None);
	return Py_None;
	}
	
static char CoInitialize__doc__[] =
""
;
static PyObject*
CoInitialize(PyObject *self, PyObject *args) 
	{
	if (!PyArg_ParseTuple(args, ""))
		return NULL;
	HRESULT hr=CoInitialize(NULL);
	int res=(hr==S_OK || hr==S_FALSE)?1:0;
	return Py_BuildValue("i",res);
	}

static char CoUninitialize__doc__[] =
""
;
static PyObject*
CoUninitialize(PyObject *self, PyObject *args) 
	{
	if (!PyArg_ParseTuple(args, ""))
		return NULL;
	CoUninitialize();
	Py_INCREF(Py_None);
	return Py_None;
	}

static char OleInitialize__doc__[] =
""
;
static PyObject*
OleInitialize(PyObject *self, PyObject *args) 
	{
	if (!PyArg_ParseTuple(args, ""))
		return NULL;
	HRESULT hr=OleInitialize(NULL);
	int res=(hr==S_OK || hr==S_FALSE)?1:0;
	return Py_BuildValue("i",res);
	}

static char OleUninitialize__doc__[] =
""
;
static PyObject*
OleUninitialize(PyObject *self, PyObject *args) 
	{
	if (!PyArg_ParseTuple(args, ""))
		return NULL;
	OleUninitialize();
	Py_INCREF(Py_None);
	return Py_None;
	}

static struct PyMethodDef grinspapi_methods[] = {
	{"CreateComModule", (PyCFunction)CreateComModule, METH_VARARGS, CreateComModule__doc__},
	{"RegisterServer", (PyCFunction)RegisterServer, METH_VARARGS, RegisterServer__doc__},
	{"UnregisterServer", (PyCFunction)UnregisterServer, METH_VARARGS, UnregisterServer__doc__},
	{"CoInitialize", (PyCFunction)CoInitialize, METH_VARARGS, CoInitialize__doc__},
	{"CoUninitialize", (PyCFunction)CoUninitialize, METH_VARARGS, CoUninitialize__doc__},
	{"OleInitialize", (PyCFunction)OleInitialize, METH_VARARGS, CoInitialize__doc__},
	{"OleUninitialize", (PyCFunction)OleUninitialize, METH_VARARGS, CoUninitialize__doc__},
	{NULL, (PyCFunction)NULL, 0, NULL}		/* sentinel */
};

///////////////////////////////////
static char grinspapi_module_documentation[] =
"GRiNS Player API"
;

extern "C" __declspec(dllexport)
void initgrinspapi()
	{
	// Create the module and add the functions
	PyObject *m = Py_InitModule4("grinspapi", grinspapi_methods,
		grinspapi_module_documentation,
		(PyObject*)NULL,PYTHON_API_VERSION);

	PyObject *d = PyModule_GetDict(m);

	// add 'error'
	errorObject = PyString_FromString("grinspapi.error");
	PyDict_SetItemString(d, "error", errorObject);

	PyCallbackBlock::init();	
	
	/* Check for errors */
	if (PyErr_Occurred())
		Py_FatalError("can't initialize module grinspapi");
	}

