
/***********************************************************
Copyright 1991-2000 by Oratrix Development BV, Amsterdam, The Netherlands.

                        All Rights Reserved

******************************************************************/

#include "Python.h"

#include <windows.h>
#include <wtypes.h>
#include <mmsystem.h>
#include <assert.h>

#pragma comment (lib, "winmm.lib")

static PyObject *ErrorObject;

struct errors {
	MMRESULT mmr;
	char *name;
} errorlist [] = {
	{MMSYSERR_NOERROR, "no error"},	
	{MMSYSERR_ERROR, "unspecified error"},	
	{MMSYSERR_BADDEVICEID, "device ID out of range"},
	{MMSYSERR_NOTENABLED, "driver failed enable"},
	{MMSYSERR_ALLOCATED, "device already allocated"},
	{MMSYSERR_INVALHANDLE, "device handle is invalid"},
	{MMSYSERR_NODRIVER, "no device driver present"},
	{MMSYSERR_NOMEM, "memory allocation error"},
	{MMSYSERR_NOTSUPPORTED, "function isn't supported"},
	{MMSYSERR_BADERRNUM, "error value out of range"},
	{MMSYSERR_INVALFLAG, "invalid flag passed"},
	{MMSYSERR_INVALPARAM, "invalid parameter passed"},
	{MMSYSERR_HANDLEBUSY, "handle being used"},
	{MMSYSERR_INVALIDALIAS, "specified alias not found"},
	{MMSYSERR_BADDB, "bad registry database"},
	{MMSYSERR_KEYNOTFOUND , "registry key not found"},
	{MMSYSERR_READERROR, "registry read error"},
	{MMSYSERR_WRITEERROR, "registry write error"},
	{MMSYSERR_DELETEERROR, "registry delete error"},
	{MMSYSERR_VALNOTFOUND, "registry value not found"},
	{MMSYSERR_NODRIVERCB, "driver does not call DriverCallback"},
	0};
	
static void
seterror(const char *funcname, MMRESULT mmr)
{
	struct errors *p;

	for (p = errorlist; p->name; p++)
		if (p->mmr == mmr) {
			PyErr_Format(ErrorObject, "%s failed, error = %s", funcname, p->name);
			return;
		}
	PyErr_Format(ErrorObject, "%s failed, error = %x", funcname, mmr);
}


///////////////////////////////////////////
///////////////////////////////////////////
// Objects declarations


typedef struct {
	PyObject_HEAD
	/* XXXX Add your own stuff here */
	HWAVEOUT hwo;
} WaveOutObject;

staticforward PyTypeObject WaveOutType;

static WaveOutObject *
newWaveOutObject()
{
	WaveOutObject *self;

	self = PyObject_NEW(WaveOutObject, &WaveOutType);
	if (self == NULL)
		return NULL;
	self->hwo = 0;
	/* XXXX Add your own initializers here */
	return self;
}

//
typedef struct {
	PyObject_HEAD
	/* XXXX Add your own stuff here */
	LPWAVEHDR pwh;
} WaveHdrObject;

staticforward PyTypeObject WaveHdrType;

static WaveHdrObject *
newWaveHdrObject()
{
	WaveHdrObject *self;

	self = PyObject_NEW(WaveHdrObject, &WaveHdrType);
	if (self == NULL)
		return NULL;
	self->pwh = NULL;
	/* XXXX Add your own initializers here */
	return self;
}

typedef struct {
	PyObject_HEAD
	/* XXXX Add your own stuff here */
    BYTE pbBuffer[512];	
	WAVEFORMATEX *pWF;
	int cbSize;
} WaveFormatExObject;

staticforward PyTypeObject WaveFormatExType;

static WaveFormatExObject *
newWaveFormatExObject()
{
	WaveFormatExObject *self;

	self = PyObject_NEW(WaveFormatExObject, &WaveFormatExType);
	if (self == NULL)
		return NULL;
	self->pWF=(WAVEFORMATEX*)self->pbBuffer;
	self->cbSize=0;
	/* XXXX Add your own initializers here */
	return self;
}

///////////////////////////////////////////
///////////////////////////////////////////
// Objects definitions

////////////////////////////////////////////
// WaveOut object

static char WaveOut_Close__doc__[] =
""
;
static PyObject*
WaveOut_Close(WaveOutObject *self, PyObject *args) 
{
	if (!PyArg_ParseTuple(args, ""))
		return NULL;
    MMRESULT mmr = MMSYSERR_NOERROR;
	mmr = waveOutClose(self->hwo);
	if(mmr != MMSYSERR_NOERROR){
		seterror("waveOutClose", mmr);
		return NULL;
	}
	Py_INCREF(Py_None);
	return Py_None;		
}

static char WaveOut_PrepareHeader__doc__[] =
""
;
static PyObject*
WaveOut_PrepareHeader(WaveOutObject *self, PyObject *args) 
{
	PyObject *strobj;
	if (!PyArg_ParseTuple(args,"S",&strobj))
		return NULL;
	DWORD cbData = PyString_GET_SIZE(strobj);	
    LPWAVEHDR pwh = (LPWAVEHDR) new BYTE[ sizeof(WAVEHDR) + cbData ];
	if(!pwh)
		return NULL;
    pwh->lpData = (LPSTR)&pwh[1];
    pwh->dwBufferLength = cbData;
    pwh->dwBytesRecorded = cbData;
    pwh->dwUser = 0;
    pwh->dwLoops = 0;
    pwh->dwFlags = 0;
    CopyMemory(pwh->lpData, PyString_AS_STRING(strobj), cbData);
    MMRESULT mmr = MMSYSERR_NOERROR;
	mmr = waveOutPrepareHeader(self->hwo,pwh,sizeof(WAVEHDR));
	if(mmr != MMSYSERR_NOERROR){
		seterror("waveOutPrepareHeader", mmr);
		return NULL;
	}
	WaveHdrObject *obj = newWaveHdrObject();
	obj->pwh = pwh;
	return (PyObject*)obj;
}

static char WaveOut_Write__doc__[] =
""
;
static PyObject*
WaveOut_Write(WaveOutObject *self, PyObject *args) 
{
	WaveHdrObject *obj;
	if (!PyArg_ParseTuple(args, "O!",&WaveHdrType,&obj))
		return NULL;
    MMRESULT mmr = MMSYSERR_NOERROR;
	mmr = waveOutWrite(self->hwo,obj->pwh,sizeof(WAVEHDR));
	if(mmr != MMSYSERR_NOERROR){
		seterror("waveOutWrite", mmr);
		return NULL;
	}
	Py_INCREF(Py_None);
	return Py_None;		
}
	

static struct PyMethodDef WaveOut_methods[] = {
	{"Close", (PyCFunction)WaveOut_Close, METH_VARARGS, WaveOut_Close__doc__},
	{"PrepareHeader", (PyCFunction)WaveOut_PrepareHeader, METH_VARARGS, WaveOut_PrepareHeader__doc__},
	{"Write", (PyCFunction)WaveOut_Write, METH_VARARGS, WaveOut_Write__doc__},
	{NULL, (PyCFunction)NULL, 0, NULL}		/* sentinel */
};

static void
WaveOut_dealloc(WaveOutObject *self)
{
	/* XXXX Add your own cleanup code here */
	if(self->hwo)waveOutClose(self->hwo);
	PyMem_DEL(self);
}

static PyObject *
WaveOut_getattr(WaveOutObject *self, char *name)
{
	/* XXXX Add your own getattr code here */
	return Py_FindMethod(WaveOut_methods, (PyObject *)self, name);
}

static char WaveOutType__doc__[] =
""
;

static PyTypeObject WaveOutType = {
	PyObject_HEAD_INIT(&PyType_Type)
	0,				/*ob_size*/
	"WaveOut",			/*tp_name*/
	sizeof(WaveOutObject),		/*tp_basicsize*/
	0,				/*tp_itemsize*/
	/* methods */
	(destructor)WaveOut_dealloc,	/*tp_dealloc*/
	(printfunc)0,		/*tp_print*/
	(getattrfunc)WaveOut_getattr,	/*tp_getattr*/
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
	WaveOutType__doc__ /* Documentation string */
};

// End of code for WaveOut object 
////////////////////////////////////////////

////////////////////////////////////////////
// WaveHdr object

static struct PyMethodDef WaveHdr_methods[] = {
	{NULL, (PyCFunction)NULL, 0, NULL}		/* sentinel */
};

static void
WaveHdr_dealloc(WaveHdrObject *self)
{
	/* XXXX Add your own cleanup code here */
	PyMem_DEL(self);
}

static PyObject *
WaveHdr_getattr(WaveHdrObject *self, char *name)
{
	/* XXXX Add your own getattr code here */
	return Py_FindMethod(WaveHdr_methods, (PyObject *)self, name);
}

static char WaveHdrType__doc__[] =
""
;

static PyTypeObject WaveHdrType = {
	PyObject_HEAD_INIT(&PyType_Type)
	0,				/*ob_size*/
	"WaveHdr",			/*tp_name*/
	sizeof(WaveHdrObject),		/*tp_basicsize*/
	0,				/*tp_itemsize*/
	/* methods */
	(destructor)WaveHdr_dealloc,	/*tp_dealloc*/
	(printfunc)0,		/*tp_print*/
	(getattrfunc)WaveHdr_getattr,	/*tp_getattr*/
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
	WaveHdrType__doc__ /* Documentation string */
};

// End of code for WaveHdr object 
////////////////////////////////////////////


////////////////////////////////////////////
// WaveFormatEx object  (WAVEFORMATEX)

static char WaveFormatEx_GetMembers__doc__[] =
"";
static PyObject *
WaveFormatEx_GetMembers(WaveFormatExObject *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args, ""))return NULL;
	return Py_BuildValue("(iiiiiii)",
		self->pWF->wFormatTag,
		self->pWF->nChannels,
		self->pWF->nSamplesPerSec,
		self->pWF->nAvgBytesPerSec,
		self->pWF->nBlockAlign,
		self->pWF->wBitsPerSample,
		self->pWF->cbSize
		);
}   

static char WaveFormatEx_GetBuffer__doc__[] =
"";

static PyObject *
WaveFormatEx_GetBuffer(WaveFormatExObject *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args, ""))return NULL;
	PyObject *obj1 = PyString_FromStringAndSize((char*)self->pbBuffer,(int)self->cbSize);
	if (obj1 == NULL) return NULL;
	PyObject *obj2 = Py_BuildValue("O", obj1);
	Py_DECREF(obj1);
	return obj2;
	
}

static struct PyMethodDef WaveFormatEx_methods[] = {
	{"GetMembers", (PyCFunction)WaveFormatEx_GetMembers, METH_VARARGS, WaveFormatEx_GetMembers__doc__},
	{"GetBuffer", (PyCFunction)WaveFormatEx_GetBuffer, METH_VARARGS, WaveFormatEx_GetBuffer__doc__},
	{NULL, (PyCFunction)NULL, 0, NULL}		/* sentinel */
};

static void
WaveFormatEx_dealloc(WaveFormatExObject *self)
{
	/* XXXX Add your own cleanup code here */
	PyMem_DEL(self);
}

static PyObject *
WaveFormatEx_getattr(WaveFormatExObject *self, char *name)
{
	/* XXXX Add your own getattr code here */
	return Py_FindMethod(WaveFormatEx_methods, (PyObject *)self, name);
}

static char WaveFormatExType__doc__[] =
""
;

static PyTypeObject WaveFormatExType = {
	PyObject_HEAD_INIT(&PyType_Type)
	0,				/*ob_size*/
	"WaveFormatEx",			/*tp_name*/
	sizeof(WaveFormatExObject),		/*tp_basicsize*/
	0,				/*tp_itemsize*/
	/* methods */
	(destructor)WaveFormatEx_dealloc,	/*tp_dealloc*/
	(printfunc)0,		/*tp_print*/
	(getattrfunc)WaveFormatEx_getattr,	/*tp_getattr*/
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
	WaveFormatExType__doc__ /* Documentation string */
};

// End of code for WaveFormatEx object 
////////////////////////////////////////////


///////////////////////////////////////////
///////////////////////////////////////////
// Module definition

void CALLBACK WaveProc( 
	HWAVEOUT hwo, 
	UINT uMsg, 
	DWORD dwInstance, 
	DWORD dwParam1, 
	DWORD dwParam2 )
{
    PyObject *obj = (PyObject*)dwInstance;
}

static char WaveOutOpen__doc__[] =
""
;
static PyObject*
WaveOutOpen(PyObject *self, PyObject *args) 
{
	WaveFormatExObject *wfxobj;
	PyObject *cbobj=NULL;
	if (!PyArg_ParseTuple(args, "O|O",&wfxobj,&cbobj))
		return NULL;
	WaveOutObject *obj = newWaveOutObject();
    MMRESULT mmr = MMSYSERR_NOERROR;
	HWAVEOUT hwo=0;
	UINT uDeviceID= WAVE_MAPPER;
	DWORD dwCallback = (DWORD)WaveProc;
	DWORD dwInstance = (DWORD)cbobj;
	DWORD fdwOpen = CALLBACK_FUNCTION;
	mmr = waveOutOpen(&obj->hwo,uDeviceID,wfxobj->pWF,dwCallback,
		dwInstance,fdwOpen);
	if(mmr != MMSYSERR_NOERROR){
		Py_DECREF(obj);
		seterror("waveOutOpen", mmr);
		return NULL;
	}
	return (PyObject*)obj;
}

	

static struct PyMethodDef winmmapi_methods[] = {
	{"WaveOutOpen", (PyCFunction)WaveOutOpen, METH_VARARGS, WaveOutOpen__doc__},
	{NULL, (PyCFunction)NULL, 0, NULL}		/* sentinel */
};


static char winmmapi_module_documentation[] =
""
;

extern "C" __declspec(dllexport)
void initwinmmapi()
{
	PyObject *m, *d;

	/* Create the module and add the functions */
	m = Py_InitModule4("winmmapi", winmmapi_methods,
		winmmapi_module_documentation,
		(PyObject*)NULL,PYTHON_API_VERSION);

	/* Add some symbolic constants to the module */
	d = PyModule_GetDict(m);
	ErrorObject = PyString_FromString("winmmapi.error");
	PyDict_SetItemString(d, "error", ErrorObject);

	/* Check for errors */
	if (PyErr_Occurred())
		Py_FatalError("can't initialize module winmmapi");
}



