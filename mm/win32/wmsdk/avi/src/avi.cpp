
/***********************************************************
Copyright 1991-1999 by Oratrix Development BV, Amsterdam, The Netherlands.

                        All Rights Reserved

******************************************************************/

#include "Python.h"

#include <windows.h>
#include <wtypes.h>
#include <mmsystem.h>
#include <vfw.h>
#include <assert.h>

#pragma comment (lib,"winmm.lib")


static PyObject *ErrorObject;


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
	IAVIFile *pI;
} AVIFileObject;

staticforward PyTypeObject AVIFileType;

static AVIFileObject *
newAVIFileObject()
{
	AVIFileObject *self;

	self = PyObject_NEW(AVIFileObject, &AVIFileType);
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
	IAVIStream *pI;
} AVIStreamObject;

staticforward PyTypeObject AVIStreamType;

static AVIStreamObject *
newAVIStreamObject()
{
	AVIStreamObject *self;

	self = PyObject_NEW(AVIStreamObject, &AVIStreamType);
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
	AVISTREAMINFO info;
} AVIStreamInfoObject;

staticforward PyTypeObject AVIStreamInfoType;

static AVIStreamInfoObject *
newAVIStreamInfoObject()
{
	AVIStreamInfoObject *self;

	self = PyObject_NEW(AVIStreamInfoObject, &AVIStreamInfoType);
	if (self == NULL)
		return NULL;
	/* XXXX Add your own initializers here */
	return self;
}

//
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
// AVIFile object 

static char AVIFile_GetStream_doc__[] =
""
;
static PyObject *
AVIFile_GetStream(AVIFileObject *self, PyObject *args)
{
	DWORD fccType = streamtypeAUDIO;
	if (!PyArg_ParseTuple(args, "|i",&fccType))
		return NULL;	
	HRESULT hr;
	AVIStreamObject *obj = newAVIStreamObject();
	Py_BEGIN_ALLOW_THREADS
	hr = AVIFileGetStream(self->pI,&obj->pI,fccType,0);
	Py_END_ALLOW_THREADS
	if (FAILED(hr)){
		Py_DECREF(obj);
		seterror("AVIFile_GetStream",hr);
		return NULL;
	}
	return (PyObject*)obj;
}


static struct PyMethodDef AVIFile_methods[] = {
	{"GetStream", (PyCFunction)AVIFile_GetStream, METH_VARARGS, AVIFile_GetStream_doc__},	
	{NULL, (PyCFunction)NULL, 0, NULL}		/* sentinel */
};

static void
AVIFile_dealloc(AVIFileObject *self)
{
	/* XXXX Add your own cleanup code here */
	if(self->pI)AVIFileRelease(self->pI);
	PyMem_DEL(self);
}

static PyObject *
AVIFile_getattr(AVIFileObject *self, char *name)
{
	/* XXXX Add your own getattr code here */
	return Py_FindMethod(AVIFile_methods, (PyObject *)self, name);
}

static char AVIFileType__doc__[] =
""
;

static PyTypeObject AVIFileType = {
	PyObject_HEAD_INIT(&PyType_Type)
	0,				/*ob_size*/
	"AVIFile",			/*tp_name*/
	sizeof(AVIFileObject),		/*tp_basicsize*/
	0,				/*tp_itemsize*/
	/* methods */
	(destructor)AVIFile_dealloc,	/*tp_dealloc*/
	(printfunc)0,		/*tp_print*/
	(getattrfunc)AVIFile_getattr,	/*tp_getattr*/
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
	AVIFileType__doc__ /* Documentation string */
};

// End of code for AVIFile object 
////////////////////////////////////////////

////////////////////////////////////////////
// AVIStream object 


static char AVIStream_FormatSize__doc__[] =
""
;
static PyObject *
AVIStream_FormatSize(AVIStreamObject *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args, ""))
		return NULL;
	HRESULT hr;
    LONG lsize;
	Py_BEGIN_ALLOW_THREADS
	hr = AVIStreamFormatSize(self->pI,0,&lsize);
	Py_END_ALLOW_THREADS
	if (FAILED(hr)) {
		seterror("AVIStream_FormatSize", hr);
		return NULL;
	}
    //if(lsize < sizeof(WAVEFORMATEX)) lsize = sizeof(WAVEFORMATEX);
	return Py_BuildValue("l",lsize);
}       

static char AVIStream_ReadFormat__doc__[] =
""
;
static PyObject *
AVIStream_ReadFormat(AVIStreamObject *self, PyObject *args)
{
	LONG cbFormat;
	if (!PyArg_ParseTuple(args,"l",&cbFormat))
		return NULL;
	WaveFormatExObject *obj = newWaveFormatExObject();
	HRESULT hr;
	LONG lPos=0;
	Py_BEGIN_ALLOW_THREADS
	hr = AVIStreamReadFormat(self->pI,lPos,obj->pbBuffer,&cbFormat);
	Py_END_ALLOW_THREADS
	if (FAILED(hr)) {
		Py_DECREF(obj);
		seterror("AVIStream_ReadFormat", hr);
		return NULL;
	}
	obj->cbSize = cbFormat;
	return (PyObject*)obj;
}       

static char AVIStream_ReadInfo__doc__[] =
""
;
static PyObject *
AVIStream_ReadInfo(AVIStreamObject *self, PyObject *args)
{
	DWORD fccType = streamtypeAUDIO;
	if (!PyArg_ParseTuple(args, "|i",&fccType))
		return NULL;	
	HRESULT hr;
	AVIStreamInfoObject *obj = newAVIStreamInfoObject();
	Py_BEGIN_ALLOW_THREADS
	hr = AVIStreamInfo(self->pI,&obj->info,sizeof(obj->info));
	Py_END_ALLOW_THREADS
	if (FAILED(hr)){
		Py_DECREF(obj);
		seterror("AVIStream_ReadInfo",hr);
		return NULL;
	}
	return (PyObject*)obj;

}       

static char AVIStream_Start__doc__[] =
""
;
static PyObject *
AVIStream_Start(AVIStreamObject *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args, ""))
		return NULL;
    LONG lCurrentSample;
	Py_BEGIN_ALLOW_THREADS
	lCurrentSample = AVIStreamStart(self->pI);
	Py_END_ALLOW_THREADS
	return Py_BuildValue("l",lCurrentSample);
}       

static char AVIStream_End__doc__[] =
""
;
static PyObject *
AVIStream_End(AVIStreamObject *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args, ""))
		return NULL;
    LONG lSamples;
	Py_BEGIN_ALLOW_THREADS
	lSamples = AVIStreamEnd(self->pI);
	Py_END_ALLOW_THREADS
	return Py_BuildValue("l",lSamples);
}       

static char AVIStream_CheckRead__doc__[] =
""
;
static PyObject *
AVIStream_CheckRead(AVIStreamObject *self, PyObject *args)
{
    LONG lStartSample;
	LONG lSamplesToRead = AVISTREAMREAD_CONVENIENT;
	if (!PyArg_ParseTuple(args, "l|l", &lStartSample, &lSamplesToRead))
		return NULL;
	HRESULT hr;
    LONG lBytes, lSamples;
    BYTE *pBuffer=NULL;
    LONG cbBuffer=0;
	Py_BEGIN_ALLOW_THREADS
	hr = AVIStreamRead(self->pI,lStartSample,lSamplesToRead,pBuffer,cbBuffer,&lBytes,&lSamples);
	Py_END_ALLOW_THREADS
	if (FAILED(hr)){
		seterror("AVIStream_CheckRead",hr);
		return NULL;
	}		
	return Py_BuildValue("(ll)",lBytes, lSamples);
}       

static char AVIStream_Read__doc__[] =
""
;
static PyObject *
AVIStream_Read(AVIStreamObject *self, PyObject *args)
{
    LONG lStartSample;
	LONG lSamplesToRead = AVISTREAMREAD_CONVENIENT;
	if (!PyArg_ParseTuple(args, "l|l", &lStartSample, &lSamplesToRead))
		return NULL;
	HRESULT hr;
    LONG lBytes, lSamples;
    BYTE *pBuffer=NULL;
    LONG cbBuffer=0;
	Py_BEGIN_ALLOW_THREADS
	hr = AVIStreamRead(self->pI,lStartSample,lSamplesToRead,pBuffer,cbBuffer,&lBytes,&lSamples);
	Py_END_ALLOW_THREADS
	if (FAILED(hr)){
		seterror("AVIStream_Read",hr);
		return NULL;
	}	
	pBuffer = new BYTE[lBytes];
	cbBuffer = lBytes;
	Py_BEGIN_ALLOW_THREADS
	hr = AVIStreamRead(self->pI,lStartSample,lSamplesToRead,pBuffer,cbBuffer,&lBytes,&lSamples);
	Py_END_ALLOW_THREADS
	if (FAILED(hr)){
		seterror("AVIStream_Read",hr);
		return NULL;
	}	
	PyObject *obj1 = PyString_FromStringAndSize((char*)pBuffer,(int)lBytes);
	if (obj1 == NULL) return NULL;
	delete []pBuffer;
	PyObject *obj2 = Py_BuildValue("(Oll)", obj1,lBytes, lSamples);
	Py_DECREF(obj1);
	return obj2;
}       

static struct PyMethodDef AVIStream_methods[] = {
	{"FormatSize", (PyCFunction)AVIStream_FormatSize, METH_VARARGS, AVIStream_FormatSize__doc__},
	{"ReadFormat", (PyCFunction)AVIStream_ReadFormat, METH_VARARGS, AVIStream_ReadFormat__doc__},
	{"ReadInfo", (PyCFunction)AVIStream_ReadInfo, METH_VARARGS, AVIStream_ReadInfo__doc__},
	{"Start", (PyCFunction)AVIStream_Start, METH_VARARGS, AVIStream_Start__doc__},
	{"End", (PyCFunction)AVIStream_End, METH_VARARGS, AVIStream_End__doc__},
	{"CheckRead", (PyCFunction)AVIStream_CheckRead, METH_VARARGS, AVIStream_CheckRead__doc__},
	{"Read", (PyCFunction)AVIStream_Read, METH_VARARGS, AVIStream_Read__doc__},
	{NULL, (PyCFunction)NULL, 0, NULL}		/* sentinel */
};

static void
AVIStream_dealloc(AVIStreamObject *self)
{
	/* XXXX Add your own cleanup code here */
	if(self->pI)AVIStreamRelease(self->pI);
	PyMem_DEL(self);
}

static PyObject *
AVIStream_getattr(AVIStreamObject *self, char *name)
{
	/* XXXX Add your own getattr code here */
	return Py_FindMethod(AVIStream_methods, (PyObject *)self, name);
}

static char AVIStreamType__doc__[] =
""
;

static PyTypeObject AVIStreamType = {
	PyObject_HEAD_INIT(&PyType_Type)
	0,				/*ob_size*/
	"AVIStream",			/*tp_name*/
	sizeof(AVIStreamObject),		/*tp_basicsize*/
	0,				/*tp_itemsize*/
	/* methods */
	(destructor)AVIStream_dealloc,	/*tp_dealloc*/
	(printfunc)0,		/*tp_print*/
	(getattrfunc)AVIStream_getattr,	/*tp_getattr*/
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
	AVIStreamType__doc__ /* Documentation string */
};

// End of code for AVIStream object 
////////////////////////////////////////////

////////////////////////////////////////////
// AVIStreamInfo object  (AVISTREAMINFO)

static char AVIStreamInfo_GetSampleSize__doc__[] =
"";
static PyObject *
AVIStreamInfo_GetSampleSize(AVIStreamInfoObject *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args, ""))return NULL;
	return Py_BuildValue("l",self->info.dwSampleSize);
}       

static struct PyMethodDef AVIStreamInfo_methods[] = {
	{"GetSampleSize", (PyCFunction)AVIStreamInfo_GetSampleSize, METH_VARARGS, AVIStreamInfo_GetSampleSize__doc__},
	{NULL, (PyCFunction)NULL, 0, NULL}		/* sentinel */
};

static void
AVIStreamInfo_dealloc(AVIStreamInfoObject *self)
{
	/* XXXX Add your own cleanup code here */
	PyMem_DEL(self);
}

static PyObject *
AVIStreamInfo_getattr(AVIStreamInfoObject *self, char *name)
{
	/* XXXX Add your own getattr code here */
	return Py_FindMethod(AVIStreamInfo_methods, (PyObject *)self, name);
}

static char AVIStreamInfoType__doc__[] =
""
;

static PyTypeObject AVIStreamInfoType = {
	PyObject_HEAD_INIT(&PyType_Type)
	0,				/*ob_size*/
	"AVIStreamInfo",			/*tp_name*/
	sizeof(AVIStreamInfoObject),		/*tp_basicsize*/
	0,				/*tp_itemsize*/
	/* methods */
	(destructor)AVIStreamInfo_dealloc,	/*tp_dealloc*/
	(printfunc)0,		/*tp_print*/
	(getattrfunc)AVIStreamInfo_getattr,	/*tp_getattr*/
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
	AVIStreamInfoType__doc__ /* Documentation string */
};

// End of code for AVIStreamInfo object 
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

static char AVIFileInit__doc__[] =
""
;
static PyObject*
AVIFileInit(PyObject *self, PyObject *args) 
	{
	if (!PyArg_ParseTuple(args, ""))
		return NULL;
	AVIFileInit();
	Py_INCREF(Py_None);
	return Py_None;	
	}

static char AVIFileExit__doc__[] =
""
;
static PyObject*
AVIFileExit(PyObject *self, PyObject *args) 
	{
	if (!PyArg_ParseTuple(args, ""))
		return NULL;
	AVIFileExit();
	Py_INCREF(Py_None);
	return Py_None;	
	}

static char AVIFileOpen__doc__[] =
""
;
static PyObject *
AVIFileOpen(PyObject *self, PyObject *args)
{
	char *psz;
	if (!PyArg_ParseTuple(args,"s",&psz))
		return NULL;
	
	AVIFileObject *obj = newAVIFileObject();
	if (obj == NULL)
		return NULL;
	
	HRESULT hr;
	Py_BEGIN_ALLOW_THREADS
	hr = AVIFileOpen(&obj->pI,psz,OF_SHARE_DENY_NONE,NULL);
	Py_END_ALLOW_THREADS
	if (FAILED(hr)){
		Py_DECREF(obj);
		seterror("AVIFileOpen", hr);
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

static struct PyMethodDef avi_methods[] = {
	{"AVIFileInit", (PyCFunction)AVIFileInit, METH_VARARGS, AVIFileInit__doc__},
	{"AVIFileExit", (PyCFunction)AVIFileExit, METH_VARARGS, AVIFileExit__doc__},
	{"AVIFileOpen", (PyCFunction)AVIFileOpen, METH_VARARGS, AVIFileOpen__doc__},
	{"CoInitialize", (PyCFunction)CoInitialize, METH_VARARGS, CoInitialize__doc__},
	{"CoUninitialize", (PyCFunction)CoUninitialize, METH_VARARGS, CoUninitialize__doc__},
	{NULL, (PyCFunction)NULL, 0, NULL}		/* sentinel */
};


static char avi_module_documentation[] =
"Video For Windows API"
;

extern "C" __declspec(dllexport)
void initavi()
{
	PyObject *m, *d;

	/* Create the module and add the functions */
	m = Py_InitModule4("avi", avi_methods,
		avi_module_documentation,
		(PyObject*)NULL,PYTHON_API_VERSION);

	/* Add some symbolic constants to the module */
	d = PyModule_GetDict(m);
	ErrorObject = PyString_FromString("avi.error");
	PyDict_SetItemString(d, "error", ErrorObject);

	/*
	#define streamtypeVIDEO         mmioFOURCC('v', 'i', 'd', 's')
	#define streamtypeAUDIO         mmioFOURCC('a', 'u', 'd', 's')
	#define streamtypeMIDI			mmioFOURCC('m', 'i', 'd', 's')
	#define streamtypeTEXT          mmioFOURCC('t', 'x', 't', 's')
	#define AVISTREAMREAD_CONVENIENT	(-1L)

	*/
	/* Check for errors */
	if (PyErr_Occurred())
		Py_FatalError("can't initialize module avi");
}



