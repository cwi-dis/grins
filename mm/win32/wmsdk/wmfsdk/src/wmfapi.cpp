
/***********************************************************
Copyright 1991-2000 by Oratrix Development BV, Amsterdam, The Netherlands.

                        All Rights Reserved

******************************************************************/

#include "Python.h"

#include <windows.h>
#include <wtypes.h>
#include "wmsdk.h"
#include <mmsystem.h>
#include <assert.h>

#include "wmpyrcb.h"
#include "pycbapi.h"

#pragma comment (lib,"winmm.lib")

static PyObject *ErrorObject;

PyInterpreterState*
PyCallbackBlock::s_pPyThreadState = NULL;

void seterror(const char *msg){PyErr_SetString(ErrorObject, msg);}


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
	IWMReader* pI;
	HANDLE hEvent;
} WMReaderObject;

staticforward PyTypeObject WMReaderType;

static WMReaderObject *
newWMReaderObject()
{
	WMReaderObject *self;

	self = PyObject_NEW(WMReaderObject, &WMReaderType);
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
	IWMWriter* pI;
} WMWriterObject;

staticforward PyTypeObject WMWriterType;

static WMWriterObject *
newWMWriterObject()
{
	WMWriterObject *self;

	self = PyObject_NEW(WMWriterObject, &WMWriterType);
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
	IWMProfileManager* pI;
} WMProfileManagerObject;

staticforward PyTypeObject WMProfileManagerType;

static WMProfileManagerObject *
newWMProfileManagerObject()
{
	WMProfileManagerObject *self;

	self = PyObject_NEW(WMProfileManagerObject, &WMProfileManagerType);
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
	IWMProfile* pI;
} WMProfileObject;

staticforward PyTypeObject WMProfileType;

static WMProfileObject *
newWMProfileObject()
{
	WMProfileObject *self;

	self = PyObject_NEW(WMProfileObject, &WMProfileType);
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
	IWMInputMediaProps* pI;
} WMInputMediaPropsObject;

staticforward PyTypeObject WMInputMediaPropsType;

static WMInputMediaPropsObject *
newWMInputMediaPropsObject()
{
	WMInputMediaPropsObject *self;

	self = PyObject_NEW(WMInputMediaPropsObject, &WMInputMediaPropsType);
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
	IWMOutputMediaProps* pI;
} WMOutputMediaPropsObject;

staticforward PyTypeObject WMOutputMediaPropsType;

static WMOutputMediaPropsObject *
newWMOutputMediaPropsObject()
{
	WMOutputMediaPropsObject *self;

	self = PyObject_NEW(WMOutputMediaPropsObject, &WMOutputMediaPropsType);
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
	INSSBuffer* pI;
} NSSBufferObject;

staticforward PyTypeObject NSSBufferType;

static NSSBufferObject *
newNSSBufferObject()
{
	NSSBufferObject *self;
	self = PyObject_NEW(NSSBufferObject, &NSSBufferType);
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
    BYTE pbBuffer[1024];
    DWORD cbBuffer;
    WM_MEDIA_TYPE *pMediaType;		
} MediaTypeObject;

staticforward PyTypeObject MediaTypeType;

static MediaTypeObject *
newMediaTypeObject()
{
	MediaTypeObject *self;
	self = PyObject_NEW(MediaTypeObject, &MediaTypeType);
	if (self == NULL)
		return NULL;
	self->pMediaType=(WM_MEDIA_TYPE*)self->pbBuffer;
	self->cbBuffer=1024;
	/* XXXX Add your own initializers here */
	return self;
}

//
typedef struct {
	PyObject_HEAD
	/* XXXX Add your own stuff here */
    IWMHeaderInfo *pI;	
} WMHeaderInfoObject;

staticforward PyTypeObject WMHeaderInfoType;

static WMHeaderInfoObject *
newWMHeaderInfoObject()
{
	WMHeaderInfoObject *self;
	self = PyObject_NEW(WMHeaderInfoObject, &WMHeaderInfoType);
	if (self == NULL)
		return NULL;
	self->pI=NULL;
	/* XXXX Add your own initializers here */
	return self;
}

//++ our py callback interface object
typedef struct {
	PyObject_HEAD
	/* XXXX Add your own stuff here */
    IWMPyReaderCallback *pI;	
} WMPyReaderCallbackObject;

staticforward PyTypeObject WMPyReaderCallbackType;

static WMPyReaderCallbackObject *
newWMPyReaderCallbackObject()
{
	WMPyReaderCallbackObject *self;
	self = PyObject_NEW(WMPyReaderCallbackObject, &WMPyReaderCallbackType);
	if (self == NULL)
		return NULL;
	self->pI=NULL;
	/* XXXX Add your own initializers here */
	return self;
}

//(general but defined here for indepentance)
typedef struct {
	PyObject_HEAD
	/* XXXX Add your own stuff here */
	GUID guid;
} GUIDObject;

staticforward PyTypeObject GUIDType;

static GUIDObject *
newGUIDObject(const GUID *p=NULL)
{
	GUIDObject *self;
	self = PyObject_NEW(GUIDObject, &GUIDType);
	if (self == NULL)
		return NULL;
	self->guid=p?*p:IID_IUnknown;
	/* XXXX Add your own initializers here */
	return self;
}


///////////////////////////////////////////
///////////////////////////////////////////
// Objects definitions

////////////////////////////////////////////
// WMReader object 

static char WMReader_Open__doc__[] =
""
;
static PyObject *
WMReader_Open(WMReaderObject *self, PyObject *args)
{
	char *pszURL;
	WMPyReaderCallbackObject *obj;
	if (!PyArg_ParseTuple(args, "sO!",&pszURL,&WMPyReaderCallbackType,&obj))
		return NULL;
	
	HRESULT hr;
	WCHAR pwszURL[MAX_PATH];
	MultiByteToWideChar(CP_ACP,0,pszURL,-1,pwszURL,MAX_PATH);
	Py_BEGIN_ALLOW_THREADS
	hr = self->pI->Open(pwszURL,obj->pI,NULL);
	Py_END_ALLOW_THREADS
	if (FAILED(hr)){
		seterror("WMReader_Open", hr);
		return NULL;
	}
	Py_INCREF(Py_None);
	return Py_None;
}
  
static char WMReader_Close__doc__[] =
""
;
static PyObject *
WMReader_Close(WMReaderObject *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args, ""))
		return NULL;	
	HRESULT hr;
	Py_BEGIN_ALLOW_THREADS
	hr = self->pI->Close();
	Py_END_ALLOW_THREADS
		
	if (FAILED(hr)){
		seterror("WMReader_Close", hr);
		return NULL;
	}
	Py_INCREF(Py_None);
	return Py_None;
}
        
static char WMReader_GetOutputCount__doc__[] =
""
;
static PyObject *
WMReader_GetOutputCount(WMReaderObject *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args, ""))
		return NULL;	
	HRESULT hr;
	DWORD cOutputs=0;
	Py_BEGIN_ALLOW_THREADS
	hr = self->pI->GetOutputCount(&cOutputs);
	Py_END_ALLOW_THREADS
	if (FAILED(hr)){
		seterror("WMReader_GetOutputCount", hr);
		return NULL;
	}
	return Py_BuildValue("i",cOutputs);
}

static char WMReader_GetOutputProps__doc__[] =
""
;
static PyObject *
WMReader_GetOutputProps(WMReaderObject *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args, ""))
		return NULL;	
	HRESULT hr;
	DWORD dwOutputNum=0;
	WMOutputMediaPropsObject *obj = newWMOutputMediaPropsObject();
	Py_BEGIN_ALLOW_THREADS
	hr = self->pI->GetOutputProps(dwOutputNum,&obj->pI);
	Py_END_ALLOW_THREADS
	if (FAILED(hr)){
		Py_DECREF(obj);
		seterror("WMReader_GetOutputProps", hr);
		return NULL;
	}
	return (PyObject*)obj;
}
        
static char WMReader_SetOutputProps__doc__[] =
""
;
static PyObject *
WMReader_SetOutputProps(WMReaderObject *self, PyObject *args)
{
	DWORD dwOutputNum;
	WMOutputMediaPropsObject *obj;
	if (!PyArg_ParseTuple(args, "iO!", &dwOutputNum,&WMOutputMediaPropsType,&obj))
		return NULL;	
	HRESULT hr;
	Py_BEGIN_ALLOW_THREADS
	hr = self->pI->SetOutputProps(dwOutputNum,obj->pI);
	Py_END_ALLOW_THREADS
	if (FAILED(hr)){
		seterror("WMReader_SetOutputProps", hr);
		return NULL;
	}
	Py_INCREF(Py_None);
	return Py_None;
}
        
static char WMReader_GetOutputFormatCount__doc__[] =
""
;
static PyObject *
WMReader_GetOutputFormatCount(WMReaderObject *self, PyObject *args)
{
	DWORD dwOutputNumber;
	if (!PyArg_ParseTuple(args, "i", &dwOutputNumber))
		return NULL;	
	HRESULT hr;
	DWORD cFormats;
	Py_BEGIN_ALLOW_THREADS
	hr = self->pI->GetOutputFormatCount(dwOutputNumber,&cFormats);
	Py_END_ALLOW_THREADS
	if (FAILED(hr)){
		seterror("WMReader_GetOutputFormatCount", hr);
		return NULL;
	}
	return Py_BuildValue("i",cFormats);
}
        
static char WMReader_GetOutputFormat__doc__[] =
""
;
static PyObject *
WMReader_GetOutputFormat(WMReaderObject *self, PyObject *args)
{
	DWORD dwOutputNum;
	DWORD dwFormatNumber;
	if (!PyArg_ParseTuple(args, "ii",&dwOutputNum,&dwFormatNumber))
		return NULL;	
	HRESULT hr;
	WMOutputMediaPropsObject *obj = newWMOutputMediaPropsObject();	
	Py_BEGIN_ALLOW_THREADS
	hr = self->pI->GetOutputFormat(dwOutputNum,dwFormatNumber,&obj->pI);
	Py_END_ALLOW_THREADS
	if (FAILED(hr)){
		Py_DECREF(obj);
		seterror("WMReader_GetOutputFormat", hr);
		return NULL;
	}
	return (PyObject*) obj;
}
        
static char WMReader_Start__doc__[] =
""
;
static PyObject *
WMReader_Start(WMReaderObject *self, PyObject *args)
{
	DWORD msStart,msDuration;
	float fRate;
	if (!PyArg_ParseTuple(args, "iif",&msStart,&msDuration,&fRate))
		return NULL;	
	HRESULT hr;
	QWORD cnsStart=10000*msStart;
	QWORD cnsDuration=10000*msDuration;
	void *pvContext=NULL;
	Py_BEGIN_ALLOW_THREADS
	hr = self->pI->Start(cnsStart,cnsDuration,fRate,pvContext);
	Py_END_ALLOW_THREADS
	if (FAILED(hr)){
		seterror("WMReader_Start", hr);
		return NULL;
	}
	Py_INCREF(Py_None);
	return Py_None;
}
        
static char WMReader_Stop__doc__[] =
""
;
static PyObject *
WMReader_Stop(WMReaderObject *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args, ""))
		return NULL;	
	HRESULT hr;
	Py_BEGIN_ALLOW_THREADS
	hr = self->pI->Stop();
	Py_END_ALLOW_THREADS
	if (FAILED(hr)){
		seterror("WMReader_Stop", hr);
		return NULL;
	}
	Py_INCREF(Py_None);
	return Py_None;
}
        
static char WMReader_Pause__doc__[] =
""
;
static PyObject *
WMReader_Pause(WMReaderObject *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args, ""))
		return NULL;	
	HRESULT hr;
	Py_BEGIN_ALLOW_THREADS
	hr = self->pI->Pause();
	Py_END_ALLOW_THREADS
	if (FAILED(hr)){
		seterror("WMReader_Pause", hr);
		return NULL;
	}
	Py_INCREF(Py_None);
	return Py_None;
}
       
static char WMReader_Resume__doc__[] =
""
;
static PyObject *
WMReader_Resume(WMReaderObject *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args, ""))
		return NULL;	
	HRESULT hr;
	Py_BEGIN_ALLOW_THREADS
	hr = self->pI->Resume();
	Py_END_ALLOW_THREADS
	if (FAILED(hr)){
		seterror("WMReader_Resume", hr);
		return NULL;
	}
	Py_INCREF(Py_None);
	return Py_None;
}

static char WMReader_QueryIWMHeaderInfo__doc__[] =
""
;
static PyObject *
WMReader_QueryIWMHeaderInfo(WMReaderObject *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args, ""))
		return NULL;	
	HRESULT hr;
	WMHeaderInfoObject *obj = newWMHeaderInfoObject();	
	Py_BEGIN_ALLOW_THREADS
	hr = self->pI->QueryInterface(IID_IWMHeaderInfo,(void**)&obj->pI);
	Py_END_ALLOW_THREADS
	if (FAILED(hr)){
		Py_DECREF(obj);
		seterror("WMReader_QueryIWMHeaderInfo", hr);
		return NULL;
	}
	return (PyObject*) obj;
}

static struct PyMethodDef WMReader_methods[] = {
	{"Open", (PyCFunction)WMReader_Open, METH_VARARGS, WMReader_Open__doc__},
	{"Close", (PyCFunction)WMReader_Close, METH_VARARGS, WMReader_Close__doc__},
	{"GetOutputCount", (PyCFunction)WMReader_GetOutputCount, METH_VARARGS, WMReader_GetOutputCount__doc__},
	{"GetOutputProps", (PyCFunction)WMReader_GetOutputProps, METH_VARARGS, WMReader_GetOutputProps__doc__},
	{"SetOutputProps", (PyCFunction)WMReader_SetOutputProps, METH_VARARGS, WMReader_SetOutputProps__doc__},
	{"GetOutputFormatCount", (PyCFunction)WMReader_GetOutputFormatCount, METH_VARARGS, WMReader_GetOutputFormatCount__doc__},
	{"GetOutputFormat", (PyCFunction)WMReader_GetOutputFormat, METH_VARARGS, WMReader_GetOutputFormat__doc__},
	{"Start", (PyCFunction)WMReader_Start, METH_VARARGS, WMReader_Start__doc__},
	{"Stop", (PyCFunction)WMReader_Stop, METH_VARARGS, WMReader_Stop__doc__},
	{"Pause", (PyCFunction)WMReader_Pause, METH_VARARGS, WMReader_Pause__doc__},
	{"Resume", (PyCFunction)WMReader_Resume, METH_VARARGS, WMReader_Resume__doc__},
	{"QueryIWMHeaderInfo", (PyCFunction)WMReader_QueryIWMHeaderInfo, METH_VARARGS, WMReader_QueryIWMHeaderInfo__doc__},
	{NULL, (PyCFunction)NULL, 0, NULL}		/* sentinel */
};

static void
WMReader_dealloc(WMReaderObject *self)
{
	/* XXXX Add your own cleanup code here */
	RELEASE(self->pI);
	PyMem_DEL(self);
}

static PyObject *
WMReader_getattr(WMReaderObject *self, char *name)
{
	/* XXXX Add your own getattr code here */
	return Py_FindMethod(WMReader_methods, (PyObject *)self, name);
}

static char WMReaderType__doc__[] =
""
;

static PyTypeObject WMReaderType = {
	PyObject_HEAD_INIT(&PyType_Type)
	0,				/*ob_size*/
	"WMReader",			/*tp_name*/
	sizeof(WMReaderObject),		/*tp_basicsize*/
	0,				/*tp_itemsize*/
	/* methods */
	(destructor)WMReader_dealloc,	/*tp_dealloc*/
	(printfunc)0,		/*tp_print*/
	(getattrfunc)WMReader_getattr,	/*tp_getattr*/
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
	WMReaderType__doc__ /* Documentation string */
};

// End of code for WMReader object 
////////////////////////////////////////////


////////////////////////////////////////////
// IWMWriter object 

static char WMWriter_SetProfile__doc__[] =
""
;
static PyObject *
WMWriter_SetProfile(WMWriterObject *self, PyObject *args)
{
	WMProfileObject *obj;
	if (!PyArg_ParseTuple(args, "O!",&WMProfileType,&obj))
		return NULL;	
	HRESULT hr;
	Py_BEGIN_ALLOW_THREADS
	hr = self->pI->SetProfile(obj->pI);
	Py_END_ALLOW_THREADS
	if (FAILED(hr)){
		seterror("WMWriter_SetProfile", hr);
		return NULL;
	}
	Py_INCREF(Py_None);
	return Py_None;
}


static char WMWriter_GetInputCount__doc__[] =
""
;
static PyObject *
WMWriter_GetInputCount(WMWriterObject *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args, ""))
		return NULL;	
	HRESULT hr;
	DWORD cInputs;
	Py_BEGIN_ALLOW_THREADS
	hr = self->pI->GetInputCount(&cInputs);
	Py_END_ALLOW_THREADS
	if (FAILED(hr)){
		seterror("WMWriter_GetInputCount", hr);
		return NULL;
	}
	return Py_BuildValue("i",cInputs);
}

static char WMWriter_GetInputProps__doc__[] =
""
;
static PyObject *
WMWriter_GetInputProps(WMWriterObject *self, PyObject *args)
{
	DWORD dwInputNum;
	if (!PyArg_ParseTuple(args, "i",&dwInputNum))
		return NULL;	
	HRESULT hr;
	WMInputMediaPropsObject* obj = newWMInputMediaPropsObject();	
	Py_BEGIN_ALLOW_THREADS
	hr = self->pI->GetInputProps(dwInputNum,&obj->pI);
	Py_END_ALLOW_THREADS
	if (FAILED(hr)){
		Py_DECREF(obj);
		seterror("WMWriter_GetInputProps", hr);
		return NULL;
	}
	return (PyObject*)obj;
}

static char WMWriter_SetInputProps__doc__[] =
""
;
static PyObject *
WMWriter_SetInputProps(WMWriterObject *self, PyObject *args)
{
	DWORD dwInputNum;
	WMInputMediaPropsObject *obj;
	if (!PyArg_ParseTuple(args, "iO!",&dwInputNum,&WMInputMediaPropsType,&obj))
		return NULL;	
	HRESULT hr;
	Py_BEGIN_ALLOW_THREADS
	hr = self->pI->SetInputProps(dwInputNum,obj->pI);
	Py_END_ALLOW_THREADS
	if (FAILED(hr)){
		seterror("WMWriter_SetInputProps", hr);
		return NULL;
	}
	Py_INCREF(Py_None);
	return Py_None;
}

static char WMWriter_SetOutputFilename__doc__[] =
""
;
static PyObject *
WMWriter_SetOutputFilename(WMWriterObject *self, PyObject *args)
{
	char *psz;
	if (!PyArg_ParseTuple(args, "s",&psz))
		return NULL;	
	HRESULT hr;
	WCHAR pwsz[MAX_PATH];
	MultiByteToWideChar(CP_ACP,0,psz,-1,pwsz,MAX_PATH);	
	Py_BEGIN_ALLOW_THREADS
	hr = self->pI->SetOutputFilename(pwsz);
	Py_END_ALLOW_THREADS
	if (FAILED(hr)){
		seterror("WMWriter_SetOutputFilename", hr);
		return NULL;
	}
	Py_INCREF(Py_None);
	return Py_None;
}

static char WMWriter_BeginWriting__doc__[] =
""
;
static PyObject *
WMWriter_BeginWriting(WMWriterObject *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args, ""))
		return NULL;	
	HRESULT hr;
	Py_BEGIN_ALLOW_THREADS
	hr = self->pI->BeginWriting();
	Py_END_ALLOW_THREADS
	if (FAILED(hr)){
		seterror("WMWriter_BeginWriting", hr);
		return NULL;
	}
	Py_INCREF(Py_None);
	return Py_None;
}

static char WMWriter_EndWriting__doc__[] =
""
;
static PyObject *
WMWriter_EndWriting(WMWriterObject *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args, ""))
		return NULL;	
	HRESULT hr;
	Py_BEGIN_ALLOW_THREADS
	hr = self->pI->EndWriting();
	Py_END_ALLOW_THREADS
	if (FAILED(hr)){
		seterror("WMWriter_EndWriting", hr);
		return NULL;
	}
	Py_INCREF(Py_None);
	return Py_None;
}

static char WMWriter_Flush__doc__[] =
""
;
static PyObject *
WMWriter_Flush(WMWriterObject *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args, ""))
		return NULL;	
	HRESULT hr;
	Py_BEGIN_ALLOW_THREADS
	hr = self->pI->Flush();
	Py_END_ALLOW_THREADS
	if (FAILED(hr)){
		seterror("WMWriter_Flush", hr);
		return NULL;
	}
	Py_INCREF(Py_None);
	return Py_None;
}


static char WMWriter_AllocateSample__doc__[] =
""
;
static PyObject *
WMWriter_AllocateSample(WMWriterObject *self, PyObject *args)
{
	DWORD dwSampleSize;
	if (!PyArg_ParseTuple(args, "i",&dwSampleSize))
		return NULL;	
	HRESULT hr;
	NSSBufferObject *obj = newNSSBufferObject();
	Py_BEGIN_ALLOW_THREADS
	hr = self->pI->AllocateSample(dwSampleSize,&obj->pI);
	Py_END_ALLOW_THREADS
	if (FAILED(hr)){
		Py_DECREF(obj);
		seterror("WMWriter_AllocateSample", hr);
		return NULL;
	}
	return (PyObject*)obj;
}

static char WMWriter_WriteSample__doc__[] =
""
;
static PyObject *
WMWriter_WriteSample(WMWriterObject *self, PyObject *args)
{
	DWORD dwInputNum;
	NSSBufferObject *obj;
	DWORD msSampleTime, dwFlags;
	if (!PyArg_ParseTuple(args, "iiiO!",&dwInputNum,&msSampleTime,
		&dwFlags,&NSSBufferType,&obj))
		return NULL;	
	HRESULT hr;
	QWORD cnsSampleTime = 10000 * msSampleTime; // 100-ns units
	Py_BEGIN_ALLOW_THREADS
	hr = self->pI->WriteSample(dwInputNum,cnsSampleTime,dwFlags,obj->pI);
	Py_END_ALLOW_THREADS
	if (FAILED(hr)){
		seterror("WMWriter_WriteSample", hr);
		return NULL;
	}
	Py_INCREF(Py_None);
	return Py_None;
}


static struct PyMethodDef WMWriter_methods[] = {
	{"SetProfile", (PyCFunction)WMWriter_SetProfile, METH_VARARGS, WMWriter_SetProfile__doc__},
	{"GetInputCount", (PyCFunction)WMWriter_GetInputCount, METH_VARARGS, WMWriter_GetInputCount__doc__},
	{"GetInputProps", (PyCFunction)WMWriter_GetInputProps, METH_VARARGS, WMWriter_GetInputProps__doc__},
	{"SetInputProps", (PyCFunction)WMWriter_SetInputProps, METH_VARARGS, WMWriter_SetInputProps__doc__},
	{"SetOutputFilename", (PyCFunction)WMWriter_SetOutputFilename, METH_VARARGS, WMWriter_SetOutputFilename__doc__},
	{"BeginWriting", (PyCFunction)WMWriter_BeginWriting, METH_VARARGS, WMWriter_BeginWriting__doc__},
	{"EndWriting", (PyCFunction)WMWriter_EndWriting, METH_VARARGS, WMWriter_EndWriting__doc__},
	{"Flush", (PyCFunction)WMWriter_Flush, METH_VARARGS, WMWriter_Flush__doc__},
	{"AllocateSample", (PyCFunction)WMWriter_AllocateSample, METH_VARARGS, WMWriter_AllocateSample__doc__},
	{"WriteSample", (PyCFunction)WMWriter_WriteSample, METH_VARARGS, WMWriter_WriteSample__doc__},
	{NULL, (PyCFunction)NULL, 0, NULL}		/* sentinel */
};

static void
WMWriter_dealloc(WMWriterObject *self)
{
	/* XXXX Add your own cleanup code here */
	RELEASE(self->pI);
	PyMem_DEL(self);
}

static PyObject *
WMWriter_getattr(WMWriterObject *self, char *name)
{
	/* XXXX Add your own getattr code here */
	return Py_FindMethod(WMWriter_methods, (PyObject *)self, name);
}

static char WMWriterType__doc__[] =
""
;

static PyTypeObject WMWriterType = {
	PyObject_HEAD_INIT(&PyType_Type)
	0,				/*ob_size*/
	"WMWriter",			/*tp_name*/
	sizeof(WMWriterObject),		/*tp_basicsize*/
	0,				/*tp_itemsize*/
	/* methods */
	(destructor)WMWriter_dealloc,	/*tp_dealloc*/
	(printfunc)0,		/*tp_print*/
	(getattrfunc)WMWriter_getattr,	/*tp_getattr*/
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
	WMWriterType__doc__ /* Documentation string */
};

// End of code for WMWriter object 
////////////////////////////////////////////

////////////////////////////////////////////
// WMProfileManager object 

static char WMProfileManager_GetSystemProfileCount__doc__[] =
""
;
static PyObject *
WMProfileManager_GetSystemProfileCount(WMProfileManagerObject *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args, ""))
		return NULL;
	HRESULT hr;
    DWORD dwProfiles;
	Py_BEGIN_ALLOW_THREADS
	hr = self->pI->GetSystemProfileCount(&dwProfiles);
	Py_END_ALLOW_THREADS
	if (FAILED(hr)) {
		seterror("WMProfileManager_GetSystemProfileCount", hr);
		return NULL;
	}
	return Py_BuildValue("i",dwProfiles);
}


static char WMProfileManager_LoadSystemProfile__doc__[] =
""
;
static PyObject *
WMProfileManager_LoadSystemProfile(WMProfileManagerObject *self, PyObject *args)
{
	DWORD dwIndex;
	if (!PyArg_ParseTuple(args,"i",&dwIndex))
		return NULL;
	
	WMProfileObject *obj = newWMProfileObject();
	if (obj == NULL) return NULL;
	
	HRESULT hr;
	Py_BEGIN_ALLOW_THREADS
	hr = self->pI->LoadSystemProfile(dwIndex,&obj->pI);
	Py_END_ALLOW_THREADS
	if (FAILED(hr)){
		Py_DECREF(obj);
		seterror("WMProfileManager_LoadSystemProfile", hr);
		return NULL;
	}
	return (PyObject*)obj;
}

static struct PyMethodDef WMProfileManager_methods[] = {
	{"GetSystemProfileCount", (PyCFunction)WMProfileManager_GetSystemProfileCount, METH_VARARGS, WMProfileManager_GetSystemProfileCount__doc__},
	{"LoadSystemProfile", (PyCFunction)WMProfileManager_LoadSystemProfile, METH_VARARGS, WMProfileManager_LoadSystemProfile__doc__},
	{NULL, (PyCFunction)NULL, 0, NULL}		/* sentinel */
};

static void
WMProfileManager_dealloc(WMProfileManagerObject *self)
{
	/* XXXX Add your own cleanup code here */
	RELEASE(self->pI);
	PyMem_DEL(self);
}

static PyObject *
WMProfileManager_getattr(WMProfileManagerObject *self, char *name)
{
	/* XXXX Add your own getattr code here */
	return Py_FindMethod(WMProfileManager_methods, (PyObject *)self, name);
}

static char WMProfileManagerType__doc__[] =
""
;

static PyTypeObject WMProfileManagerType = {
	PyObject_HEAD_INIT(&PyType_Type)
	0,				/*ob_size*/
	"WMProfileManager",			/*tp_name*/
	sizeof(WMProfileManagerObject),		/*tp_basicsize*/
	0,				/*tp_itemsize*/
	/* methods */
	(destructor)WMProfileManager_dealloc,	/*tp_dealloc*/
	(printfunc)0,		/*tp_print*/
	(getattrfunc)WMProfileManager_getattr,	/*tp_getattr*/
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
	WMProfileManagerType__doc__ /* Documentation string */
};

// End of code for WMProfileManager object 
////////////////////////////////////////////

////////////////////////////////////////////
// WMProfile object 
static char WMProfile_GetName__doc__[] =
""
;
static PyObject *
WMProfile_GetName(WMProfileObject *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args,"")) 
		return NULL;
	HRESULT hr;
    WCHAR *pwszName=NULL;
    DWORD cchName = 0;
	Py_BEGIN_ALLOW_THREADS
	hr = self->pI->GetName(NULL, &cchName);
	if (SUCCEEDED(hr)){
		pwszName = new WCHAR[cchName];
		hr = self->pI->GetName(pwszName, &cchName);
		}
	Py_END_ALLOW_THREADS
	if (FAILED(hr)) {
		if(pwszName) delete [] pwszName;
		seterror("WMProfile_GetName", hr);
		return NULL;
	}
	char *pszName = new char[cchName+1];
	WideCharToMultiByte(CP_ACP,0,pwszName,cchName,pszName,cchName,NULL,NULL);
	pszName[cchName]='\0';
	PyObject *obj = Py_BuildValue("s",pszName);
	delete []pwszName;
	delete []pszName;
	return obj;
}


static struct PyMethodDef WMProfile_methods[] = {
	{"GetName", (PyCFunction)WMProfile_GetName, METH_VARARGS, WMProfile_GetName__doc__},
	{NULL, (PyCFunction)NULL, 0, NULL}		/* sentinel */
};

static void
WMProfile_dealloc(WMProfileObject *self)
{
	/* XXXX Add your own cleanup code here */
	RELEASE(self->pI);
	PyMem_DEL(self);
}

static PyObject *
WMProfile_getattr(WMProfileObject *self, char *name)
{
	/* XXXX Add your own getattr code here */
	return Py_FindMethod(WMProfile_methods, (PyObject *)self, name);
}

static char WMProfileType__doc__[] =
""
;

static PyTypeObject WMProfileType = {
	PyObject_HEAD_INIT(&PyType_Type)
	0,				/*ob_size*/
	"WMProfile",			/*tp_name*/
	sizeof(WMProfileObject),		/*tp_basicsize*/
	0,				/*tp_itemsize*/
	/* methods */
	(destructor)WMProfile_dealloc,	/*tp_dealloc*/
	(printfunc)0,		/*tp_print*/
	(getattrfunc)WMProfile_getattr,	/*tp_getattr*/
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
	WMProfileType__doc__ /* Documentation string */
};

// End of code for WMProfile object 
////////////////////////////////////////////


////////////////////////////////////////////
// WMInputMediaProps object 

static char WMInputMediaProps_GetType__doc__[] =
""
;
static PyObject *
WMInputMediaProps_GetType(WMInputMediaPropsObject *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args,"")) 
		return NULL;
	HRESULT hr;
	GUIDObject *obj = newGUIDObject();
	Py_BEGIN_ALLOW_THREADS
	hr = self->pI->GetType(&obj->guid);
	Py_END_ALLOW_THREADS	
	if (FAILED(hr)) {
		Py_DECREF(obj);		
		seterror("WMInputMediaProps_GetType", hr);
		return NULL;
	}
	return (PyObject*)obj;
}


static char WMInputMediaProps_GetMediaType__doc__[] =
""
;
static PyObject *
WMInputMediaProps_GetMediaType(WMInputMediaPropsObject *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args,"")) 
		return NULL;
	HRESULT hr;
	MediaTypeObject *obj = newMediaTypeObject();
	Py_BEGIN_ALLOW_THREADS
	hr = self->pI->GetMediaType(obj->pMediaType,&obj->cbBuffer);
	Py_END_ALLOW_THREADS	
	if (FAILED(hr)) {
		Py_DECREF(obj);		
		seterror("WMInputMediaProps_GetMediaType", hr);
		return NULL;
	}
	return (PyObject*)obj;
}
	
static char WMInputMediaProps_SetMediaType__doc__[] =
""
;
static PyObject *
WMInputMediaProps_SetMediaType(WMInputMediaPropsObject *self, PyObject *args)
{
	MediaTypeObject *obj;
	if (!PyArg_ParseTuple(args,"O!",&MediaTypeType,&obj)) 
		return NULL;
	HRESULT hr;
	Py_BEGIN_ALLOW_THREADS
	hr = self->pI->SetMediaType(obj->pMediaType);
	Py_END_ALLOW_THREADS	
	if (FAILED(hr)) {
		seterror("WMInputMediaProps_SetMediaType", hr);
		return NULL;
	}
	Py_INCREF(Py_None);
	return Py_None;	
}

static struct PyMethodDef WMInputMediaProps_methods[] = {
	{"GetType", (PyCFunction)WMInputMediaProps_GetType, METH_VARARGS, WMInputMediaProps_GetType__doc__},
	{"GetMediaType", (PyCFunction)WMInputMediaProps_GetMediaType, METH_VARARGS, WMInputMediaProps_GetMediaType__doc__},
	{"SetMediaType", (PyCFunction)WMInputMediaProps_SetMediaType, METH_VARARGS, WMInputMediaProps_SetMediaType__doc__},
	{NULL, (PyCFunction)NULL, 0, NULL}		/* sentinel */
};

static void
WMInputMediaProps_dealloc(WMInputMediaPropsObject *self)
{
	/* XXXX Add your own cleanup code here */
	RELEASE(self->pI);
	PyMem_DEL(self);
}

static PyObject *
WMInputMediaProps_getattr(WMInputMediaPropsObject *self, char *name)
{
	/* XXXX Add your own getattr code here */
	return Py_FindMethod(WMInputMediaProps_methods, (PyObject *)self, name);
}

static char WMInputMediaPropsType__doc__[] =
""
;

static PyTypeObject WMInputMediaPropsType = {
	PyObject_HEAD_INIT(&PyType_Type)
	0,				/*ob_size*/
	"WMInputMediaProps",			/*tp_name*/
	sizeof(WMInputMediaPropsObject),		/*tp_basicsize*/
	0,				/*tp_itemsize*/
	/* methods */
	(destructor)WMInputMediaProps_dealloc,	/*tp_dealloc*/
	(printfunc)0,		/*tp_print*/
	(getattrfunc)WMInputMediaProps_getattr,	/*tp_getattr*/
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
	WMInputMediaPropsType__doc__ /* Documentation string */
};

// End of code for WMInputMediaProps object 
////////////////////////////////////////////

////////////////////////////////////////////
// WMOutputMediaProps object 


static struct PyMethodDef WMOutputMediaProps_methods[] = {
	{NULL, (PyCFunction)NULL, 0, NULL}		/* sentinel */
};

static void
WMOutputMediaProps_dealloc(WMOutputMediaPropsObject *self)
{
	/* XXXX Add your own cleanup code here */
	RELEASE(self->pI);
	PyMem_DEL(self);
}

static PyObject *
WMOutputMediaProps_getattr(WMOutputMediaPropsObject *self, char *name)
{
	/* XXXX Add your own getattr code here */
	return Py_FindMethod(WMOutputMediaProps_methods, (PyObject *)self, name);
}

static char WMOutputMediaPropsType__doc__[] =
""
;

static PyTypeObject WMOutputMediaPropsType = {
	PyObject_HEAD_INIT(&PyType_Type)
	0,				/*ob_size*/
	"WMOutputMediaProps",			/*tp_name*/
	sizeof(WMOutputMediaPropsObject),		/*tp_basicsize*/
	0,				/*tp_itemsize*/
	/* methods */
	(destructor)WMOutputMediaProps_dealloc,	/*tp_dealloc*/
	(printfunc)0,		/*tp_print*/
	(getattrfunc)WMOutputMediaProps_getattr,	/*tp_getattr*/
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
	WMOutputMediaPropsType__doc__ /* Documentation string */
};

// End of code for WMOutputMediaProps object 
////////////////////////////////////////////

////////////////////////////////////////////
// NSSBuffer object 
			
static char NSSBuffer_GetLength__doc__[] =
""
;
static PyObject *
NSSBuffer_GetLength(NSSBufferObject *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args, ""))
		return NULL;
	HRESULT hr;
    DWORD dwLength;
	Py_BEGIN_ALLOW_THREADS
	hr = self->pI->GetLength(&dwLength);
	Py_END_ALLOW_THREADS
	if (FAILED(hr)) {
		seterror("NSSBuffer_GetLength", hr);
		return NULL;
	}
	return Py_BuildValue("i",dwLength);
}

static char NSSBuffer_SetLength__doc__[] =
""
;
static PyObject *
NSSBuffer_SetLength(NSSBufferObject *self, PyObject *args)
{
    DWORD dwLength;
	if (!PyArg_ParseTuple(args, "i",&dwLength))
		return NULL;
	HRESULT hr;
	Py_BEGIN_ALLOW_THREADS
	hr = self->pI->SetLength(dwLength);
	Py_END_ALLOW_THREADS
	if (FAILED(hr)) {
		seterror("NSSBuffer_SetLength", hr);
		return NULL;
	}
	Py_INCREF(Py_None);
	return Py_None;
}

static char NSSBuffer_GetMaxLength__doc__[] =
""
;
static PyObject *
NSSBuffer_GetMaxLength(NSSBufferObject *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args, ""))
		return NULL;
	HRESULT hr;
    DWORD dwLength;
	Py_BEGIN_ALLOW_THREADS
	hr = self->pI->GetMaxLength(&dwLength);
	Py_END_ALLOW_THREADS
	if (FAILED(hr)) {
		seterror("NSSBuffer_GetMaxLength", hr);
		return NULL;
	}
	return Py_BuildValue("i",dwLength);
}       

static char NSSBuffer_GetBuffer__doc__[] =
""
;
static PyObject *
NSSBuffer_GetBuffer(NSSBufferObject *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args, ""))
		return NULL;
	HRESULT hr;
    BYTE *pdwBuffer = NULL;
    DWORD dwLength;		
	Py_BEGIN_ALLOW_THREADS
	hr = self->pI->GetBufferAndLength(&pdwBuffer,&dwLength);
	Py_END_ALLOW_THREADS
	if (FAILED(hr)) {
		seterror("NSSBuffer_GetBuffer", hr);
		return NULL;
	}
	PyObject *obj1 = PyString_FromStringAndSize((char*)pdwBuffer,(int)dwLength);
	if (obj1 == NULL) return NULL;
	PyObject *obj2 = Py_BuildValue("O", obj1);
	Py_DECREF(obj1);
	return obj2;
}     

static char NSSBuffer_GetBufferAndLength__doc__[] =
""
;
static PyObject *
NSSBuffer_GetBufferAndLength(NSSBufferObject *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args, ""))
		return NULL;
	HRESULT hr;
    BYTE *pdwBuffer=NULL;
    DWORD dwLength;		
	Py_BEGIN_ALLOW_THREADS
	hr = self->pI->GetBufferAndLength(&pdwBuffer,&dwLength);
	Py_END_ALLOW_THREADS
	if (FAILED(hr)) {
		seterror("NSSBuffer_GetBufferAndLength", hr);
		return NULL;
	}
	PyObject *obj1 = PyString_FromStringAndSize((char*)pdwBuffer,(int)dwLength);
	if (obj1 == NULL) return NULL;
	PyObject *obj2 = Py_BuildValue("(Oi)", obj1,dwLength);
	Py_DECREF(obj1);
	return obj2;
}       

// Composite
static char NSSBuffer_SetBuffer__doc__[] =
""
;
static PyObject *
NSSBuffer_SetBuffer(NSSBufferObject *self, PyObject *args)
{
	PyObject *obj;
	if (!PyArg_ParseTuple(args,"S",&obj))
		return NULL;
	HRESULT hr;
    BYTE *pdwBuffer=NULL;
    DWORD dwLength;	
	hr = self->pI->GetBufferAndLength(&pdwBuffer,&dwLength);
	if (FAILED(hr)) {
		seterror("NSSBuffer_SetBuffer", hr);
		return NULL;
	}
	DWORD dw = PyString_GET_SIZE(obj);
	if(dw>dwLength) dw = dwLength;
	memcpy(pdwBuffer,PyString_AS_STRING(obj),dw);
	hr = self->pI->SetLength(dw);
	if (FAILED(hr)) {
		seterror("NSSBuffer_SetBuffer", hr);
		return NULL;
	}
	Py_INCREF(Py_None);
	return Py_None;
}


static struct PyMethodDef NSSBuffer_methods[] = {
	{"GetLength", (PyCFunction)NSSBuffer_GetLength, METH_VARARGS, NSSBuffer_GetLength__doc__},
	{"SetLength", (PyCFunction)NSSBuffer_GetLength, METH_VARARGS, NSSBuffer_SetLength__doc__},
	{"GetMaxLength", (PyCFunction)NSSBuffer_GetMaxLength, METH_VARARGS, NSSBuffer_GetMaxLength__doc__},
	{"GetBuffer", (PyCFunction)NSSBuffer_GetBuffer, METH_VARARGS, NSSBuffer_GetBuffer__doc__},
	{"GetBufferAndLength", (PyCFunction)NSSBuffer_GetBufferAndLength, METH_VARARGS, NSSBuffer_GetBufferAndLength__doc__},
	{"SetBuffer", (PyCFunction)NSSBuffer_SetBuffer, METH_VARARGS, NSSBuffer_SetBuffer__doc__},
	{NULL, (PyCFunction)NULL, 0, NULL}		/* sentinel */
};

static void
NSSBuffer_dealloc(NSSBufferObject *self)
{
	/* XXXX Add your own cleanup code here */
	RELEASE(self->pI);
	PyMem_DEL(self);
}

static PyObject *
NSSBuffer_getattr(NSSBufferObject *self, char *name)
{
	/* XXXX Add your own getattr code here */
	return Py_FindMethod(NSSBuffer_methods, (PyObject *)self, name);
}

static char NSSBufferType__doc__[] =
""
;

static PyTypeObject NSSBufferType = {
	PyObject_HEAD_INIT(&PyType_Type)
	0,				/*ob_size*/
	"NSSBuffer",			/*tp_name*/
	sizeof(NSSBufferObject),		/*tp_basicsize*/
	0,				/*tp_itemsize*/
	/* methods */
	(destructor)NSSBuffer_dealloc,	/*tp_dealloc*/
	(printfunc)0,		/*tp_print*/
	(getattrfunc)NSSBuffer_getattr,	/*tp_getattr*/
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
	NSSBufferType__doc__ /* Documentation string */
};

// End of code for NSSBuffer object 
////////////////////////////////////////////

////////////////////////////////////////////
// MediaType object 


static char MediaType_SetType__doc__[] =
""
;
static PyObject*
MediaType_SetType(MediaTypeObject *self, PyObject *args)
{
	GUIDObject *obj1,*obj2;
	if (!PyArg_ParseTuple(args,"O!O!",&GUIDType,&obj1,&GUIDType,&obj2)) 
		return NULL;
	self->pMediaType->majortype = obj1->guid;
	self->pMediaType->subtype = obj2->guid;
	Py_INCREF(Py_None);
	return Py_None;	
}

static char MediaType_SetMajorType__doc__[] =
""
;
static PyObject*
MediaType_SetMajorType(MediaTypeObject *self, PyObject *args)
{
	GUIDObject *obj;
	if (!PyArg_ParseTuple(args,"O!",&GUIDType,&obj)) 
		return NULL;
	self->pMediaType->majortype = obj->guid;
	Py_INCREF(Py_None);
	return Py_None;	
}
static char MediaType_SetSubType__doc__[] =
""
;
static PyObject*
MediaType_SetSubType(MediaTypeObject *self, PyObject *args)
{
	GUIDObject *obj;
	if (!PyArg_ParseTuple(args,"O!",&GUIDType,&obj)) 
		return NULL;
	self->pMediaType->subtype = obj->guid;
	Py_INCREF(Py_None);
	return Py_None;	
}

static char MediaType_SetSampleSize__doc__[] =
""
;
static PyObject*
MediaType_SetSampleSize(MediaTypeObject *self, PyObject *args)
{
    int fixedSizeSamples=1;
    int temporalCompression=0;
    ULONG lSampleSize;
	if (!PyArg_ParseTuple(args,"l|ii",&lSampleSize,&fixedSizeSamples,&temporalCompression)) 
		return NULL;
	self->pMediaType->bFixedSizeSamples = fixedSizeSamples?TRUE:FALSE;
	self->pMediaType->bTemporalCompression = temporalCompression?TRUE:FALSE;
 	self->pMediaType->lSampleSize = lSampleSize;
	Py_INCREF(Py_None);
	return Py_None;	
}

static char MediaType_SetFormat__doc__[] =
""
;
static PyObject*
MediaType_SetFormat(MediaTypeObject *self, PyObject *args)
{
	GUIDObject *obj;
	PyObject *pystr;
	if (!PyArg_ParseTuple(args,"O!S",&GUIDType,&obj,&pystr)) 
		return NULL;
	self->pMediaType->formattype = obj->guid;
	self->pMediaType->pUnk = NULL;
	self->pMediaType->cbFormat = PyString_GET_SIZE(pystr);
	self->pMediaType->pbFormat = (BYTE*)PyString_AS_STRING(pystr);
	Py_INCREF(Py_None);
	return Py_None;	
}

static struct PyMethodDef MediaType_methods[] = {
	{"SetType", (PyCFunction)MediaType_SetType, METH_VARARGS, MediaType_SetType__doc__},
	{"SetMajorType", (PyCFunction)MediaType_SetMajorType, METH_VARARGS, MediaType_SetMajorType__doc__},
	{"SetSubType", (PyCFunction)MediaType_SetSubType, METH_VARARGS, MediaType_SetSubType__doc__},
	{"SetSampleSize", (PyCFunction)MediaType_SetSampleSize, METH_VARARGS, MediaType_SetSampleSize__doc__},
	{"SetFormat", (PyCFunction)MediaType_SetFormat, METH_VARARGS, MediaType_SetFormat__doc__},
	{NULL, (PyCFunction)NULL, 0, NULL}		/* sentinel */
};

static void
MediaType_dealloc(MediaTypeObject *self)
{
	/* XXXX Add your own cleanup code here */
	PyMem_DEL(self);
}

static PyObject *
MediaType_getattr(MediaTypeObject *self, char *name)
{
	/* XXXX Add your own getattr code here */
	return Py_FindMethod(MediaType_methods, (PyObject *)self, name);
}

static char MediaTypeType__doc__[] =
""
;
static PyTypeObject MediaTypeType = {
	PyObject_HEAD_INIT(&PyType_Type)
	0,				/*ob_size*/
	"MediaType",			/*tp_name*/
	sizeof(MediaTypeObject),		/*tp_basicsize*/
	0,				/*tp_itemsize*/
	/* methods */
	(destructor)MediaType_dealloc,	/*tp_dealloc*/
	(printfunc)0,		/*tp_print*/
	(getattrfunc)MediaType_getattr,	/*tp_getattr*/
	(setattrfunc)0,	/*tp_setattr*/
	(cmpfunc)0, /*tp_compare*/
	(reprfunc)0,		/*tp_repr*/
	0,			/*tp_as_number*/
	0,		/*tp_as_sequence*/
	0,		/*tp_as_mapping*/
	(hashfunc)0,		/*tp_hash*/
	(ternaryfunc)0,		/*tp_call*/
	(reprfunc)0,		/*tp_str*/

	/* Space for future expansion */
	0L,0L,0L,0L,
	MediaTypeType__doc__ /* Documentation string */
};

// End of code for MediaType object 
////////////////////////////////////////////

////////////////////////////////////////////
// WMHeaderInfo object 

static char WMHeaderInfo_GetAttributeCount__doc__[] =
""
;
static PyObject *
WMHeaderInfo_GetAttributeCount(WMHeaderInfoObject *self, PyObject *args)
{
	WORD wStreamNum=0;
	if (!PyArg_ParseTuple(args, "|i",&wStreamNum))
		return NULL;
	HRESULT hr;
	WORD cAttributes;
	Py_BEGIN_ALLOW_THREADS
	hr = self->pI->GetAttributeCount(wStreamNum,&cAttributes);
	Py_END_ALLOW_THREADS
	if (FAILED(hr)) {
		seterror("WMHeaderInfo_GetAttributeCount", hr);
		return NULL;
	}
	return Py_BuildValue("i",cAttributes);
}

// XXX: placeholder
static char WMHeaderInfo_GetAttributeByIndex__doc__[] =
""
;
static PyObject *
WMHeaderInfo_GetAttributeByIndex(WMHeaderInfoObject *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args, ""))
		return NULL;
	HRESULT hr;
	WORD wIndex=0;
	WORD wStreamNum=0;
	WCHAR wszName[512];
	WORD cchNamelen = 512;
	WMT_ATTR_DATATYPE type;
	BYTE pValue[512];
	WORD cbLength = 512;
	Py_BEGIN_ALLOW_THREADS
	hr = self->pI->GetAttributeByIndex(wIndex,&wStreamNum,wszName,&cchNamelen,&type,pValue,&cbLength);
	Py_END_ALLOW_THREADS
	if (FAILED(hr)) {
		seterror("WMHeaderInfo_GetAttributeByIndex", hr);
		return NULL;
	}
	Py_INCREF(Py_None);
	return Py_None;	
}


static struct PyMethodDef WMHeaderInfo_methods[] = {
	{"GetAttributeCount", (PyCFunction)WMHeaderInfo_GetAttributeCount, METH_VARARGS, WMHeaderInfo_GetAttributeCount__doc__},
	{"GetAttributeByIndex", (PyCFunction)WMHeaderInfo_GetAttributeByIndex, METH_VARARGS, WMHeaderInfo_GetAttributeByIndex__doc__},
	{NULL, (PyCFunction)NULL, 0, NULL}		/* sentinel */
};

static void
WMHeaderInfo_dealloc(WMHeaderInfoObject *self)
{
	/* XXXX Add your own cleanup code here */
	RELEASE(self->pI);
	PyMem_DEL(self);
}

static PyObject *
WMHeaderInfo_getattr(WMHeaderInfoObject *self, char *name)
{
	/* XXXX Add your own getattr code here */
	return Py_FindMethod(WMHeaderInfo_methods, (PyObject *)self, name);
}

static char WMHeaderInfoType__doc__[] =
""
;
static PyTypeObject WMHeaderInfoType = {
	PyObject_HEAD_INIT(&PyType_Type)
	0,				/*ob_size*/
	"WMHeaderInfo",			/*tp_name*/
	sizeof(WMHeaderInfoObject),		/*tp_basicsize*/
	0,				/*tp_itemsize*/
	/* methods */
	(destructor)WMHeaderInfo_dealloc,	/*tp_dealloc*/
	(printfunc)0,		/*tp_print*/
	(getattrfunc)WMHeaderInfo_getattr,	/*tp_getattr*/
	(setattrfunc)0,	/*tp_setattr*/
	(cmpfunc)0, /*tp_compare*/
	(reprfunc)0,		/*tp_repr*/
	0,			/*tp_as_number*/
	0,		/*tp_as_sequence*/
	0,		/*tp_as_mapping*/
	(hashfunc)0,		/*tp_hash*/
	(ternaryfunc)0,		/*tp_call*/
	(reprfunc)0,		/*tp_str*/

	/* Space for future expansion */
	0L,0L,0L,0L,
	WMHeaderInfoType__doc__ /* Documentation string */
};

// End of code for WMHeaderInfo object 
////////////////////////////////////////////

////////////////////////////////////////////
// WMPyReaderCallback object 

static char WMPyReaderCallback_SetListener__doc__[] =
""
;
static PyObject *
WMPyReaderCallback_SetListener(WMPyReaderCallbackObject *self, PyObject *args)
{
	PyObject *obj=NULL;
	if (!PyArg_ParseTuple(args, "|O",&obj))
		return NULL;
	HRESULT hr;
	hr = self->pI->SetListener(obj);
	if (FAILED(hr)) {
		seterror("WMPyReaderCallback_SetListener", hr);
		return NULL;
	}
	Py_INCREF(Py_None);
	return Py_None;	
}
static char WMPyReaderCallback_WaitOpen__doc__[] =
""
;
static PyObject *
WMPyReaderCallback_WaitOpen(WMPyReaderCallbackObject *self, PyObject *args)
{
	DWORD msTimeout=INFINITE;
	if (!PyArg_ParseTuple(args, "|l",&msTimeout))
		return NULL;
	HRESULT hr;
	DWORD res;
	Py_BEGIN_ALLOW_THREADS
	hr=self->pI->WaitOpen(msTimeout,&res);
	Py_END_ALLOW_THREADS
	if (FAILED(hr)) {
		seterror("WMPyReaderCallback_WaitOpen", hr);
		return NULL;
	}		
	return Py_BuildValue("i", res);
}

static char WMPyReaderCallback_WaitForCompletion__doc__[] =
""
;
static PyObject *
WMPyReaderCallback_WaitForCompletion(WMPyReaderCallbackObject *self, PyObject *args)
{
	DWORD msTimeout=INFINITE;
	if (!PyArg_ParseTuple(args, "|l",&msTimeout))
		return NULL;
	HRESULT hr;
	DWORD res;
	Py_BEGIN_ALLOW_THREADS
	hr=self->pI->WaitForCompletion(msTimeout,&res);
	Py_END_ALLOW_THREADS
	if (FAILED(hr)) {
		seterror("WMPyReaderCallback_WaitForCompletion", hr);
		return NULL;
	}		
	return Py_BuildValue("i", res);
}

static struct PyMethodDef WMPyReaderCallback_methods[] = {
	{"SetListener", (PyCFunction)WMPyReaderCallback_SetListener, METH_VARARGS, WMPyReaderCallback_SetListener__doc__},
	{"WaitOpen", (PyCFunction)WMPyReaderCallback_WaitOpen, METH_VARARGS, WMPyReaderCallback_WaitOpen__doc__},
	{"WaitForCompletion", (PyCFunction)WMPyReaderCallback_WaitForCompletion, METH_VARARGS, WMPyReaderCallback_WaitForCompletion__doc__},
	{NULL, (PyCFunction)NULL, 0, NULL}		/* sentinel */
};

static void
WMPyReaderCallback_dealloc(WMPyReaderCallbackObject *self)
{
	/* XXXX Add your own cleanup code here */
	Py_BEGIN_ALLOW_THREADS
	RELEASE(self->pI);
	Py_END_ALLOW_THREADS	
	PyMem_DEL(self);
}

static PyObject *
WMPyReaderCallback_getattr(WMPyReaderCallbackObject *self, char *name)
{
	/* XXXX Add your own getattr code here */
	return Py_FindMethod(WMPyReaderCallback_methods, (PyObject *)self, name);
}

static char WMPyReaderCallbackType__doc__[] =
""
;

static PyTypeObject WMPyReaderCallbackType = {
	PyObject_HEAD_INIT(&PyType_Type)
	0,				/*ob_size*/
	"WMPyReaderCallback",			/*tp_name*/
	sizeof(WMPyReaderCallbackObject),		/*tp_basicsize*/
	0,				/*tp_itemsize*/
	/* methods */
	(destructor)WMPyReaderCallback_dealloc,	/*tp_dealloc*/
	(printfunc)0,		/*tp_print*/
	(getattrfunc)WMPyReaderCallback_getattr,	/*tp_getattr*/
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
	WMPyReaderCallbackType__doc__ /* Documentation string */
};
// End of code for WMPyReaderCallback object 
////////////////////////////////////////////


////////////////////////////////////////////
// GUID object (general but defined here for indepentance) 
			
static struct PyMethodDef GUID_methods[] = {
	{NULL, (PyCFunction)NULL, 0, NULL}		/* sentinel */
};

static void
GUID_dealloc(GUIDObject *self)
{
	/* XXXX Add your own cleanup code here */
	PyMem_DEL(self);
}

static PyObject *
GUID_getattr(GUIDObject *self, char *name)
{
	/* XXXX Add your own getattr code here */
	return Py_FindMethod(GUID_methods, (PyObject *)self, name);
}

static int
GUID_compare(GUIDObject *l, GUIDObject *r)
{
	int mr = memcmp((const void*)&l->guid,(const void*)&r->guid,sizeof(GUID));
	return (mr<0) ? -1 : ((mr>0) ? 1 : 0);
}

static char GUIDType__doc__[] =
""
;
static PyTypeObject GUIDType = {
	PyObject_HEAD_INIT(&PyType_Type)
	0,				/*ob_size*/
	"GUID",			/*tp_name*/
	sizeof(GUIDObject),		/*tp_basicsize*/
	0,				/*tp_itemsize*/
	/* methods */
	(destructor)GUID_dealloc,	/*tp_dealloc*/
	(printfunc)0,		/*tp_print*/
	(getattrfunc)GUID_getattr,	/*tp_getattr*/
	(setattrfunc)0,	/*tp_setattr*/
	(cmpfunc)GUID_compare, /*tp_compare*/
	(reprfunc)0,		/*tp_repr*/
	0,			/*tp_as_number*/
	0,		/*tp_as_sequence*/
	0,		/*tp_as_mapping*/
	(hashfunc)0,		/*tp_hash*/
	(ternaryfunc)0,		/*tp_call*/
	(reprfunc)0,		/*tp_str*/

	/* Space for future expansion */
	0L,0L,0L,0L,
	GUIDType__doc__ /* Documentation string */
};

// End of code for GUID object 
////////////////////////////////////////////


///////////////////////////////////////////
///////////////////////////////////////////
// MODULE
//

static char CreateReader__doc__[] =
""
;
static PyObject *
CreateReader(PyObject *self, PyObject *args)
{
	DWORD dwRights=0;
	if (!PyArg_ParseTuple(args,"|i",&dwRights))
		return NULL;
	
	WMReaderObject *obj = newWMReaderObject();
	if (obj == NULL)
		return NULL;
	
	HRESULT hr;
	Py_BEGIN_ALLOW_THREADS
	hr = WMCreateReader(NULL,dwRights,&obj->pI);
	Py_END_ALLOW_THREADS
	if (FAILED(hr)){
		Py_DECREF(obj);
		seterror("WMCreateReader", hr);
		return NULL;
	}
	return (PyObject*)obj;
}

//
static char CreateWriter__doc__[] =
""
;
static PyObject *
CreateWriter(PyObject *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args, ""))
		return NULL;
	
	WMWriterObject *obj = newWMWriterObject();
	if (obj == NULL)
		return NULL;
	
	HRESULT hr;
	Py_BEGIN_ALLOW_THREADS
	hr = WMCreateWriter(NULL,&obj->pI);
	Py_END_ALLOW_THREADS
	if (FAILED(hr)){
		Py_DECREF(obj);
		seterror("WMCreateWriter", hr);
		return NULL;
	}
	return (PyObject*)obj;
}


//
static char CreateProfileManager__doc__[] =
""
;
static PyObject *
CreateProfileManager(PyObject *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args, ""))
		return NULL;
	
	WMProfileManagerObject *obj = newWMProfileManagerObject();
	if (obj == NULL)
		return NULL;
	
	HRESULT hr;
	Py_BEGIN_ALLOW_THREADS
	hr = WMCreateProfileManager(&obj->pI);
	Py_END_ALLOW_THREADS
	if (FAILED(hr)){
		Py_DECREF(obj);
		seterror("WMCreateProfileManager", hr);
		return NULL;
	}
	return (PyObject*)obj;
}

static char CreatePyReaderCallback__doc__[] =
""
;
static PyObject *
CreatePyReaderCallback(PyObject *self, PyObject *args)
{
	PyObject *pycbobj;
	if (!PyArg_ParseTuple(args,"O",&pycbobj))
		return NULL;
	
	WMPyReaderCallbackObject *obj = newWMPyReaderCallbackObject();
	if (obj == NULL)
		return NULL;
	HRESULT hr;
	hr = WMCreatePyReaderCallback(pycbobj,&obj->pI);
	if (FAILED(hr)){
		Py_DECREF(obj);
		seterror("CreatePyReaderCallback", hr);
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
	//res=TlsAlloc()>=0?1:0;
	PyCallbackBlock::init();	
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
	//PyCallbackBlock::free();	
	CoUninitialize();
	Py_INCREF(Py_None);
	return Py_None;
	}

static struct PyMethodDef wmfapi_methods[] = {
	{"CreateReader", (PyCFunction)CreateReader, METH_VARARGS, CreateReader__doc__},
	{"CreateWriter", (PyCFunction)CreateWriter, METH_VARARGS, CreateWriter__doc__},
	{"CreateProfileManager", (PyCFunction)CreateProfileManager, METH_VARARGS, CreateProfileManager__doc__},
	{"CreatePyReaderCallback", (PyCFunction)CreatePyReaderCallback, METH_VARARGS, CreatePyReaderCallback__doc__},
	{"CoInitialize", (PyCFunction)CoInitialize, METH_VARARGS, CoInitialize__doc__},
	{"CoUninitialize", (PyCFunction)CoUninitialize, METH_VARARGS, CoUninitialize__doc__},
	{NULL, (PyCFunction)NULL, 0, NULL}		/* sentinel */
};

static struct {const GUID *p;char* s;} wmguids[] ={
	{&WMMEDIASUBTYPE_Base, "WMMEDIASUBTYPE_Base"},
	{&WMMEDIATYPE_Video, "WMMEDIATYPE_Video"},
	{&WMMEDIASUBTYPE_RGB1, "WMMEDIASUBTYPE_RGB1"},
	{&WMMEDIASUBTYPE_RGB4, "WMMEDIASUBTYPE_RGB4"},
	{&WMMEDIASUBTYPE_RGB8, "WMMEDIASUBTYPE_RGB8"},
	{&WMMEDIASUBTYPE_RGB565, "WMMEDIASUBTYPE_RGB565"}, 
	{&WMMEDIASUBTYPE_RGB555, "WMMEDIASUBTYPE_RGB555"}, 
	{&WMMEDIASUBTYPE_RGB24, "WMMEDIASUBTYPE_RGB24"}, 
	{&WMMEDIASUBTYPE_RGB32, "WMMEDIASUBTYPE_RGB32"}, 
	{&WMMEDIASUBTYPE_YV12, "WMMEDIASUBTYPE_YV12"}, 
	{&WMMEDIASUBTYPE_YUY2, "WMMEDIASUBTYPE_YUY2"}, 
	{&WMMEDIASUBTYPE_UYVY, "WMMEDIASUBTYPE_UYVY"}, 
	{&WMMEDIASUBTYPE_YVYU, "WMMEDIASUBTYPE_YVYU"}, 
	{&WMMEDIASUBTYPE_YVU9, "WMMEDIASUBTYPE_YVU9"}, 
	{&WMMEDIASUBTYPE_MP43, "WMMEDIASUBTYPE_MP43"}, 
	{&WMMEDIATYPE_Audio, "WMMEDIATYPE_Audio"}, 
	{&WMMEDIASUBTYPE_PCM, "WMMEDIASUBTYPE_PCM"}, 
	{&WMMEDIASUBTYPE_WMAudioV2, "WMMEDIASUBTYPE_WMAudioV2"}, 
	{&WMMEDIASUBTYPE_ACELPnet, "WMMEDIASUBTYPE_ACELPnet"}, 
	{&WMMEDIATYPE_Script, "WMMEDIATYPE_Script"}, 
	{&WMFORMAT_VideoInfo, "WMFORMAT_VideoInfo"}, 
	{&WMFORMAT_WaveFormatEx, "WMFORMAT_WaveFormatEx"}, 
	{&WMFORMAT_Script, "WMFORMAT_Script"}, 
	{NULL,NULL}
};

static struct {int n;char* s;} wmcon[] ={
//enum WMT_ATTR_DATATYPE
	{0, "WMT_TYPE_DWORD"},
	{1, "WMT_TYPE_STRING"},
	{2, "WMT_TYPE_BINARY"},
	{3, "WMT_TYPE_BOOL"},
	{4, "WMT_TYPE_QWORD"},
	{5, "WMT_TYPE_WORD"},
	{6, "WMT_TYPE_GUID"},
//enum WMT_STATUS
    {0,"WMT_ERROR"},
    {1,"WMT_OPENED"},
    {2,	"WMT_BUFFERING_START"},
    {3,	"WMT_BUFFERING_STOP"},
    {4,	"WMT_EOF"},
    {4,	"WMT_END_OF_FILE"},
	{5,	"WMT_END_OF_SEGMENT"},
    {6,	"WMT_END_OF_STREAMING"},
    {7,	"WMT_LOCATING"},
    {8,	"WMT_CONNECTING"},
	{9,	"WMT_NO_RIGHTS"},
    {10,"WMT_MISSING_CODEC"},
    {11,"WMT_STARTED"},
    {12,"WMT_STOPPED"},
    {13,"WMT_CLOSED"},
    {14,"WMT_STRIDING"},
    {15,"WMT_TIMER"},
    {16,"WMT_INDEX_PROGRESS"},
	{0,NULL}
	};

static char wmfapi_module_documentation[] =
"Windows Media Format API"
;

extern "C" __declspec(dllexport)
void initwmfapi()
{
	PyObject *m, *d, *x;

	/* Create the module and add the functions */
	m = Py_InitModule4("wmfapi", wmfapi_methods,
		wmfapi_module_documentation,
		(PyObject*)NULL,PYTHON_API_VERSION);

	/* Add some symbolic constants to the module */
	d = PyModule_GetDict(m);
	ErrorObject = PyString_FromString("wmfapi.error");
	PyDict_SetItemString(d, "error", ErrorObject);

	for(int i=0;wmguids[i].p && wmguids[i].s;i++)
		{
		x = (PyObject*)newGUIDObject(wmguids[i].p);
		if (x == NULL || PyDict_SetItemString(d, wmguids[i].s, x) < 0)
			{
			Py_FatalError("can't initialize module wmfapi");
			return;
			}
		Py_DECREF(x);
		}

	for(i=0;wmcon[i].s;i++)
		{
		x = PyInt_FromLong((long) wmcon[i].n);
		if (x == NULL || PyDict_SetItemString(d, wmcon[i].s, x) < 0)
			{
			Py_FatalError("can't initialize module wmfapi");
			return;
			}
		Py_DECREF(x);
		}
	
	/* Check for errors */
	if (PyErr_Occurred())
		Py_FatalError("can't initialize module wmfapi");
}



