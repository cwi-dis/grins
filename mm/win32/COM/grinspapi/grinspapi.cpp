
/***********************************************************
Copyright 1991-2000 by Oratrix Development BV, Amsterdam, The Netherlands.

                        All Rights Reserved

******************************************************************/
#include "stdafx.h"

#include "Python.h"

// for server
#include "stdlib/stdcom.h"
#include "stdlib/Registrar.h"

// for client
#include "IGRiNSPlayer.h"

static PyObject *errorObject;


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
	IGRiNSPlayer *pI;
} GRiNSPlayerObject;

staticforward PyTypeObject GRiNSPlayerType;

static GRiNSPlayerObject* newGRiNSPlayerObject()
{
	GRiNSPlayerObject *self;
	self = PyObject_NEW(GRiNSPlayerObject, &GRiNSPlayerType);
	if (self == NULL)
		return NULL;
	self->pI = NULL;
	return self;
}


//
typedef struct {
	PyObject_HEAD
	/* XXXX Add your own stuff here */
} ComModuleObject;

staticforward PyTypeObject ComModuleType;

static ComModuleObject *
newComModuleObject()
{
	ComModuleObject *self;

	self = PyObject_NEW(ComModuleObject, &ComModuleType);
	if (self == NULL)
		return NULL;
	module.init(GetModuleHandle(NULL),GetCurrentThreadId());
	/* XXXX Add your own initializers here */
	return self;
}

static ComModuleObject *comModuleObject;


////////////////////////////////////////////
// GRiNSPlayer object 

static char GRiNSPlayer_Open__doc__[] =
""
;
static PyObject *
GRiNSPlayer_Open(GRiNSPlayerObject *self, PyObject *args)
{
	char *pszFilename;
	if (!PyArg_ParseTuple(args, "s", &pszFilename))
		return NULL;
	WCHAR pwszURL[MAX_PATH];
	MultiByteToWideChar(CP_ACP,0,pszFilename,-1,pwszURL,MAX_PATH);
	HRESULT hr = self->pI->Open(pwszURL);
	if (FAILED(hr)){
		seterror("GRiNSPlayer_Open", hr);
		return NULL;
	}
	Py_INCREF(Py_None);
	return Py_None;
}

static char GRiNSPlayer_Play__doc__[] =
""
;
static PyObject *
GRiNSPlayer_Play(GRiNSPlayerObject *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args, ""))
		return NULL;
	HRESULT hr = self->pI->Play();
	if (FAILED(hr)){
		seterror("GRiNSPlayer_Play", hr);
		return NULL;
	}
	Py_INCREF(Py_None);
	return Py_None;
}

static char GRiNSPlayer_Stop__doc__[] =
""
;
static PyObject *
GRiNSPlayer_Stop(GRiNSPlayerObject *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args, ""))
		return NULL;
	HRESULT hr = self->pI->Stop();
	if (FAILED(hr)){
		seterror("GRiNSPlayer_Stop", hr);
		return NULL;
	}
	Py_INCREF(Py_None);
	return Py_None;
}

	
static struct PyMethodDef GRiNSPlayer_methods[] = {
	{"Open", (PyCFunction)GRiNSPlayer_Open, METH_VARARGS, GRiNSPlayer_Open__doc__},
	{"Play", (PyCFunction)GRiNSPlayer_Play, METH_VARARGS, GRiNSPlayer_Play__doc__},
	{"Stop", (PyCFunction)GRiNSPlayer_Stop, METH_VARARGS, GRiNSPlayer_Stop__doc__},
	{NULL, (PyCFunction)NULL, 0, NULL}		/* sentinel */
};

static void
GRiNSPlayer_dealloc(GRiNSPlayerObject *self)
{
	/* XXXX Add your own cleanup code here */
	RELEASE(self->pI);
	PyMem_DEL(self);
}

static PyObject *
GRiNSPlayer_getattr(GRiNSPlayerObject *self, char *name)
{
	/* XXXX Add your own getattr code here */
	return Py_FindMethod(GRiNSPlayer_methods, (PyObject *)self, name);
}

static char GRiNSPlayerType__doc__[] =
""
;

static PyTypeObject GRiNSPlayerType = {
	PyObject_HEAD_INIT(&PyType_Type)
	0,				/*ob_size*/
	"GRiNSPlayer",			/*tp_name*/
	sizeof(GRiNSPlayerObject),		/*tp_basicsize*/
	0,				/*tp_itemsize*/
	/* methods */
	(destructor)GRiNSPlayer_dealloc,	/*tp_dealloc*/
	(printfunc)0,		/*tp_print*/
	(getattrfunc)GRiNSPlayer_getattr,	/*tp_getattr*/
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
	GRiNSPlayerType__doc__ /* Documentation string */
};

// End of code for GRiNSPlayer object 
////////////////////////////////////////////

////////////////////////////////////////////
// ComModule object 

static char ComModule_RegisterClassObjects__doc__[] =
""
;
static PyObject *
ComModule_RegisterClassObjects(GRiNSPlayerObject *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args, ""))
		return NULL;
	module.registerClassObjects();
	Py_INCREF(Py_None);
	return Py_None;
}

static char ComModule_RevokeClassObjects__doc__[] =
""
;
static PyObject *
ComModule_RevokeClassObjects(GRiNSPlayerObject *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args, ""))
		return NULL;
	module.revokeClassObjects();
	Py_INCREF(Py_None);
	return Py_None;
}
	
static struct PyMethodDef ComModule_methods[] = {
	{"RegisterClassObjects", (PyCFunction)ComModule_RegisterClassObjects, METH_VARARGS, ComModule_RegisterClassObjects__doc__},
	{"RevokeClassObjects", (PyCFunction)ComModule_RevokeClassObjects, METH_VARARGS, ComModule_RevokeClassObjects__doc__},
	{NULL, (PyCFunction)NULL, 0, NULL}		/* sentinel */
};

static void
ComModule_dealloc(ComModuleObject *self)
{
	/* XXXX Add your own cleanup code here */
	module.term();
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


static char RegisterServer__doc__[] =
""
;
static PyObject*
RegisterServer(PyObject *self, PyObject *args) 
	{
	if (!PyArg_ParseTuple(args, ""))
		return NULL;
	if(RegisterServer()!=ERROR_SUCCESS){
		seterror("RegisterServer", GetLastError());
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
	if(UnregisterServer()!=ERROR_SUCCESS){
		seterror("UnregisterServer", GetLastError());
		return NULL;
	}
	Py_INCREF(Py_None);
	return Py_None;
	}

static char CreatePlayer__doc__[] =
""
;
static PyObject*
CreatePlayer(PyObject *self, PyObject *args) 
	{
	if (!PyArg_ParseTuple(args, ""))
		return NULL;
	GRiNSPlayerObject *obj = newGRiNSPlayerObject();
	if(obj==NULL) return NULL;

	DWORD dwClsContext = CLSCTX_LOCAL_SERVER;
	HRESULT hr = CoCreateInstance(CLSID_GRiNSPlayer,NULL,dwClsContext,IID_IGRiNSPlayer,(void**)&obj->pI);
	if (FAILED(hr)){
		Py_DECREF(obj);
		seterror("CreatePlayer", hr);
		return NULL;
	}
	return (PyObject*)obj;
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

static struct PyMethodDef grinspapi_methods[] = {
	{"RegisterServer", (PyCFunction)RegisterServer, METH_VARARGS, RegisterServer__doc__},
	{"UnregisterServer", (PyCFunction)UnregisterServer, METH_VARARGS, UnregisterServer__doc__},
	{"CreatePlayer", (PyCFunction)CreatePlayer, METH_VARARGS, CreatePlayer__doc__},
	{"CoInitialize", (PyCFunction)CoInitialize, METH_VARARGS, CoInitialize__doc__},
	{"CoUninitialize", (PyCFunction)CoUninitialize, METH_VARARGS, CoUninitialize__doc__},
	{NULL, (PyCFunction)NULL, 0, NULL}		/* sentinel */
};

///////////////////////////////////
static char grinspapi_module_documentation[] =
"GRiNS Player API"
;

extern "C" __declspec(dllexport)
void initgrinspapi()
{
	PyObject *m, *d;
	
	// Create the module and add the functions
	m = Py_InitModule4("grinspapi", grinspapi_methods,
		grinspapi_module_documentation,
		(PyObject*)NULL,PYTHON_API_VERSION);

	d = PyModule_GetDict(m);

	// add 'error'
	errorObject = PyString_FromString("grinspapi.error");
	PyDict_SetItemString(d, "error", errorObject);

	// add 'com module'
	RegisterComObjects();	
	comModuleObject = newComModuleObject();
	PyDict_SetItemString(d, "commodule", (PyObject*)comModuleObject);
	
	/* Check for errors */
	if (PyErr_Occurred())
		Py_FatalError("can't initialize module grinspapi");
}

