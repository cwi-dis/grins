
/***********************************************************
Copyright 1991-2000 by Oratrix Development BV, Amsterdam, The Netherlands.

                        All Rights Reserved

******************************************************************/

#include "Python.h"

#include <windows.h>
#include <wtypes.h>
#include <assert.h>

#include <mmsystem.h>
#include <mmreg.h>
#include <msacm.h>

#include <dsound.h>

#pragma comment (lib,"winmm.lib")
#pragma comment (lib,"dsound.lib")
#pragma comment (lib,"dxguid.lib")


static PyObject *ErrorObject;

void seterror(const char *msg){PyErr_SetString(ErrorObject, msg);}

/////////////////////

#define RELEASE(x) if(x) x->Release();x=NULL;

static void
seterror(const char *funcname, HRESULT hr)
{
	char* pszmsg;
	FormatMessage( 
		 FORMAT_MESSAGE_ALLOCATE_BUFFER | FORMAT_MESSAGE_FROM_SYSTEM,
		 NULL,
		 hr,
		 MAKELANGID(LANG_NEUTRAL, SUBLANG_DEFAULT), // Default language
		 (LPTSTR) &pszmsg,
		 0,
		 NULL 
		);
	PyErr_Format(ErrorObject, "%s failed, error = %s", funcname, pszmsg);
	LocalFree(pszmsg);
}


///////////////////////////////////////////
///////////////////////////////////////////
// Objects declarations

//
typedef struct {
	PyObject_HEAD
	/* XXXX Add your own stuff here */
	IDirectSound* pI;
} DirectSoundObject;

staticforward PyTypeObject DirectSoundType;

static DirectSoundObject *
newDirectSoundObject()
{
	DirectSoundObject *self;

	self = PyObject_NEW(DirectSoundObject, &DirectSoundType);
	if (self == NULL)
		return NULL;
	self->pI = NULL;
	/* XXXX Add your own initializers here */
	return self;
}


//
typedef struct {
	PyObject_HEAD
	/* XXXX Add your own stuff here */
	IDirectSoundBuffer* pI;
} DirectSoundBufferObject;

staticforward PyTypeObject DirectSoundBufferType;

static DirectSoundBufferObject *
newDirectSoundBufferObject()
{
	DirectSoundBufferObject *self;

	self = PyObject_NEW(DirectSoundBufferObject, &DirectSoundBufferType);
	if (self == NULL)
		return NULL;
	self->pI = NULL;
	/* XXXX Add your own initializers here */
	return self;
}


///////////////////////////////////////////
///////////////////////////////////////////
// Objects definitions


////////////////////////////////////////////
// DirectSound object 

static char DirectSound_SetCooperativeLevel__doc__[] =
""
;
static PyObject *
DirectSound_SetCooperativeLevel(DirectSoundObject *self, PyObject *args)
{
	HWND hWnd;
	DWORD dwFlags = DSSCL_NORMAL;
	if (!PyArg_ParseTuple(args, "i|i",&hWnd,&dwFlags))
		return NULL;	
	HRESULT hr;
	hr = self->pI->SetCooperativeLevel(hWnd, dwFlags);
	if (FAILED(hr)){
		seterror("DirectSound_SetCooperativeLevel", hr);
		return NULL;
	}
	Py_INCREF(Py_None);
	return Py_None;
}


static char DirectSound_CreateSoundBuffer__doc__[] =
""
;
static PyObject *
DirectSound_CreateSoundBuffer(DirectSoundObject *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args, ""))
		return NULL;	
	HRESULT hr;
    DSBUFFERDESC dsbd;  // buffer description struct
    memset(&dsbd, 0, sizeof(DSBUFFERDESC));
    dsbd.dwSize = sizeof(DSBUFFERDESC);
    dsbd.dwFlags = DSBCAPS_PRIMARYBUFFER;
    dsbd.dwBufferBytes = 0;
    dsbd.lpwfxFormat = NULL;

	DirectSoundBufferObject *obj = newDirectSoundBufferObject();
	if(!obj) return NULL;

	hr = self->pI->CreateSoundBuffer(&dsbd,&obj->pI,NULL);
	if (FAILED(hr)){
		Py_DECREF(obj);
		seterror("DirectSound_CreateSoundBuffer", hr);
		return NULL;
	}
	return (PyObject*) obj;
}


static struct PyMethodDef DirectSound_methods[] = {
	{"SetCooperativeLevel", (PyCFunction)DirectSound_SetCooperativeLevel, METH_VARARGS, DirectSound_SetCooperativeLevel__doc__},
	{"CreateSoundBuffer", (PyCFunction)DirectSound_CreateSoundBuffer, METH_VARARGS, DirectSound_CreateSoundBuffer__doc__},
	{NULL, (PyCFunction)NULL, 0, NULL}		/* sentinel */
};

static void
DirectSound_dealloc(DirectSoundObject *self)
{
	/* XXXX Add your own cleanup code here */
	RELEASE(self->pI);
	PyMem_DEL(self);
}

static PyObject *
DirectSound_getattr(DirectSoundObject *self, char *name)
{
	/* XXXX Add your own getattr code here */
	return Py_FindMethod(DirectSound_methods, (PyObject *)self, name);
}

static char DirectSoundType__doc__[] =
""
;

static PyTypeObject DirectSoundType = {
	PyObject_HEAD_INIT(&PyType_Type)
	0,				/*ob_size*/
	"DirectSound",			/*tp_name*/
	sizeof(DirectSoundObject),		/*tp_basicsize*/
	0,				/*tp_itemsize*/
	/* methods */
	(destructor)DirectSound_dealloc,	/*tp_dealloc*/
	(printfunc)0,		/*tp_print*/
	(getattrfunc)DirectSound_getattr,	/*tp_getattr*/
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
	DirectSoundType__doc__ /* Documentation string */
};

// End of code for DirectSound object 
////////////////////////////////////////////

////////////////////////////////////////////
// DirectSoundBuffer object 

static struct PyMethodDef DirectSoundBuffer_methods[] = {
	{NULL, (PyCFunction)NULL, 0, NULL}		/* sentinel */
};

static void
DirectSoundBuffer_dealloc(DirectSoundBufferObject *self)
{
	/* XXXX Add your own cleanup code here */
	RELEASE(self->pI);
	PyMem_DEL(self);
}

static PyObject *
DirectSoundBuffer_getattr(DirectSoundBufferObject *self, char *name)
{
	/* XXXX Add your own getattr code here */
	return Py_FindMethod(DirectSoundBuffer_methods, (PyObject *)self, name);
}

static char DirectSoundBufferType__doc__[] =
""
;

static PyTypeObject DirectSoundBufferType = {
	PyObject_HEAD_INIT(&PyType_Type)
	0,				/*ob_size*/
	"DirectSoundBuffer",			/*tp_name*/
	sizeof(DirectSoundBufferObject),		/*tp_basicsize*/
	0,				/*tp_itemsize*/
	/* methods */
	(destructor)DirectSoundBuffer_dealloc,	/*tp_dealloc*/
	(printfunc)0,		/*tp_print*/
	(getattrfunc)DirectSoundBuffer_getattr,	/*tp_getattr*/
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
	DirectSoundBufferType__doc__ /* Documentation string */
};

// End of code for DirectSoundBuffer object 
////////////////////////////////////////////


///////////////////////////////////////////
///////////////////////////////////////////
// MODULE
//

//
static char CreateDirectSound__doc__[] =
""
;
static PyObject *
CreateDirectSound(PyObject *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args, ""))
		return NULL;
	
	DirectSoundObject *obj = newDirectSoundObject();
	if (obj == NULL)
		return NULL;
	
	HRESULT hr;
	hr = DirectSoundCreate(NULL, &obj->pI, NULL);
	if (FAILED(hr)){
		Py_DECREF(obj);
		seterror("CreateDirectSound", hr);
		return NULL;
	}
	return (PyObject*)obj;
}

// std com stuff for independance
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

// std com stuff for independance
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

static struct PyMethodDef dsound_methods[] = {
	{"CreateDirectSound", (PyCFunction)CreateDirectSound, METH_VARARGS, CreateDirectSound__doc__},
	{"CoInitialize", (PyCFunction)CoInitialize, METH_VARARGS, CoInitialize__doc__},
	{"CoUninitialize", (PyCFunction)CoUninitialize, METH_VARARGS, CoUninitialize__doc__},
	{NULL, (PyCFunction)NULL, 0, NULL}		/* sentinel */
};


struct constentry {char* s;int n;};

// add symbolic constants of enum
static int 
SetItemEnum(PyObject *d,constentry e[])
	{
	PyObject *x;
	for(int i=0;e[i].s;i++)
		{
		x = PyInt_FromLong((long) e[i].n);
		if (x == NULL || PyDict_SetItemString(d, e[i].s, x) < 0)
			return -1;
		Py_DECREF(x);
		}
	return 0;
	}


#define FATAL_ERROR_IF(exp) if(exp){Py_FatalError("can't initialize module dsound");return;}	

static char dsound_module_documentation[] =
"DirectSound module"
;

extern "C" __declspec(dllexport)
void initdsound()
{
	PyObject *m, *d;
	bool bPyErrOccurred = false;
	
	// Create the module and add the functions
	m = Py_InitModule4("dsound", dsound_methods,
		dsound_module_documentation,
		(PyObject*)NULL,PYTHON_API_VERSION);

	// add 'error'
	d = PyModule_GetDict(m);
	ErrorObject = PyString_FromString("dsound.error");
	PyDict_SetItemString(d, "error", ErrorObject);

	// add symbolic constants
	// ...

	// Check for errors
	if (PyErr_Occurred())
		Py_FatalError("can't initialize module dsound");
}
