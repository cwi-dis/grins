
/***********************************************************
Copyright 1991-2001 by Oratrix Development BV, Amsterdam, The Netherlands.

                        All Rights Reserved

******************************************************************/

#include "Python.h"

#include <windows.h>
#include <wtypes.h>
#include <assert.h>

#include <mmsystem.h>
#include <mmreg.h>

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


//
typedef struct {
	PyObject_HEAD
	/* XXXX Add your own stuff here */
	IDirectSound3DBuffer* pI;
} DirectSound3DBufferObject;

staticforward PyTypeObject DirectSound3DBufferType;

static DirectSound3DBufferObject *
newDirectSound3DBufferObject()
{
	DirectSound3DBufferObject *self;

	self = PyObject_NEW(DirectSound3DBufferObject, &DirectSound3DBufferType);
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
	IDirectSound3DListener* pI;
} DirectSound3DListenerObject;

staticforward PyTypeObject DirectSound3DListenerType;

static DirectSound3DListenerObject *
newDirectSound3DListenerObject()
{
	DirectSound3DListenerObject *self;
	self = PyObject_NEW(DirectSound3DListenerObject, &DirectSound3DListenerType);
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
	DSBUFFERDESC d;
} DSBUFFERDESCObject;

staticforward PyTypeObject DSBUFFERDESCType;

static DSBUFFERDESCObject *
newDSBUFFERDESCObject()
{
	DSBUFFERDESCObject *self;
	self = PyObject_NEW(DSBUFFERDESCObject, &DSBUFFERDESCType);
	if (self == NULL)
		return NULL;
	memset(&self->d, 0, sizeof(self->d));
	self->d.dwSize = sizeof(self->d);
	/* XXXX Add your own initializers here */
	return self;
}

//
typedef struct {
	PyObject_HEAD
	/* XXXX Add your own stuff here */
	DSCAPS d;
} DSCAPSObject;

staticforward PyTypeObject DSCAPSType;

static DSCAPSObject *
newDSCAPSObject()
{
	DSCAPSObject *self;
	self = PyObject_NEW(DSCAPSObject, &DSCAPSType);
	if (self == NULL)
		return NULL;
	memset(&self->d, 0, sizeof(self->d));
	self->d.dwSize = sizeof(self->d);
	/* XXXX Add your own initializers here */
	return self;
}


//
typedef struct {
	PyObject_HEAD
	/* XXXX Add your own stuff here */
	DSBCAPS d;
} DSBCAPSObject;

staticforward PyTypeObject DSBCAPSType;

static DSBCAPSObject *
newDSBCAPSObject()
{
	DSBCAPSObject *self;
	self = PyObject_NEW(DSBCAPSObject, &DSBCAPSType);
	if (self == NULL)
		return NULL;
	memset(&self->d, 0, sizeof(self->d));
	self->d.dwSize = sizeof(self->d);
	/* XXXX Add your own initializers here */
	return self;
}

//
typedef struct {
	PyObject_HEAD
	/* XXXX Add your own stuff here */
	DS3DBUFFER d;
} DS3DBUFFERObject;

staticforward PyTypeObject DS3DBUFFERType;

static DS3DBUFFERObject *
newDS3DBUFFERObject()
{
	DS3DBUFFERObject *self;
	self = PyObject_NEW(DS3DBUFFERObject, &DS3DBUFFERType);
	if (self == NULL)return NULL;
	memset(&self->d, 0, sizeof(self->d));
	self->d.dwSize = sizeof(self->d);
	/* XXXX Add your own initializers here */
	return self;
}

//
typedef struct {
	PyObject_HEAD
	/* XXXX Add your own stuff here */
	DS3DLISTENER d;
} DS3DLISTENERObject;

staticforward PyTypeObject DS3DLISTENERType;

static DS3DLISTENERObject *
newDS3DLISTENERObject()
{
	DS3DLISTENERObject *self;
	self = PyObject_NEW(DS3DLISTENERObject, &DS3DLISTENERType);
	if (self == NULL) return NULL;
	memset(&self->d, 0, sizeof(self->d));
	self->d.dwSize = sizeof(self->d);
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
	DSBUFFERDESCObject *dsbdObj;
	if (!PyArg_ParseTuple(args, "O!",&DSBUFFERDESCType,&dsbdObj))
		return NULL;	
	HRESULT hr;
	DirectSoundBufferObject *obj = newDirectSoundBufferObject();
	if(!obj) return NULL;
	hr = self->pI->CreateSoundBuffer(&dsbdObj->d,&obj->pI,NULL);
	if (FAILED(hr)){
		Py_DECREF(obj);
		seterror("DirectSound_CreateSoundBuffer", hr);
		return NULL;
	}
	return (PyObject*) obj;
}

// TEMPORARY
IDirectSoundBuffer* CreateDSBufferFromFile(IDirectSound *pI, DSBUFFERDESC *pdsbd, char *pszFilename);
static char DirectSound_CreateSoundBufferFromFile__doc__[] =
""
;
static PyObject *
DirectSound_CreateSoundBufferFromFile(DirectSoundObject *self, PyObject *args)
{
	DSBUFFERDESCObject *dsbdObj;
	char *pszFilename;
	if (!PyArg_ParseTuple(args, "O!s",&DSBUFFERDESCType,&dsbdObj,&pszFilename))
		return NULL;	
	DirectSoundBufferObject *obj = newDirectSoundBufferObject();
	if(!obj) return NULL;

	obj->pI = CreateDSBufferFromFile(self->pI, &dsbdObj->d, pszFilename);
	if(obj->pI == NULL) return NULL;
	return (PyObject*) obj;
}

static struct PyMethodDef DirectSound_methods[] = {
	{"SetCooperativeLevel", (PyCFunction)DirectSound_SetCooperativeLevel, METH_VARARGS, DirectSound_SetCooperativeLevel__doc__},
	{"CreateSoundBuffer", (PyCFunction)DirectSound_CreateSoundBuffer, METH_VARARGS, DirectSound_CreateSoundBuffer__doc__},
	{"CreateSoundBufferFromFile", (PyCFunction)DirectSound_CreateSoundBufferFromFile, METH_VARARGS, DirectSound_CreateSoundBufferFromFile__doc__},
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
// IDirectSoundBuffer object 

static char DirectSoundBuffer_GetCaps__doc__[] =
""
;
static PyObject *
DirectSoundBuffer_GetCaps(DirectSoundBufferObject *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args, ""))
		return NULL;	
	DSBCAPSObject *obj = newDSBCAPSObject();
	HRESULT hr = self->pI->GetCaps(&obj->d);
	if (FAILED(hr)){
		seterror("DirectSoundBuffer_GetCaps", hr);
		return NULL;
	}
	return (PyObject *)obj;
}

static char DirectSoundBuffer_GetCurrentPosition__doc__[] =
""
;
static PyObject *
DirectSoundBuffer_GetCurrentPosition(DirectSoundBufferObject *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args, ""))
		return NULL;	
	DWORD dwCurrentPlayCursor;
	DWORD dwCurrentWriteCursor;
	HRESULT hr = self->pI->GetCurrentPosition(&dwCurrentPlayCursor,&dwCurrentWriteCursor);
	if (FAILED(hr)){
		seterror("DirectSoundBuffer_GetCurrentPosition", hr);
		return NULL;
	}
	return Py_BuildValue("ii",dwCurrentPlayCursor, dwCurrentWriteCursor);
}

static char DirectSoundBuffer_GetFormat__doc__[] =
""
;
static PyObject *
DirectSoundBuffer_GetFormat(DirectSoundBufferObject *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args, ""))
		return NULL;
	WaveFormatExObject *obj = newWaveFormatExObject();
	DWORD dwSizeAllocated = 512;
	DWORD dwSizeWritten = 0;
	HRESULT hr = self->pI->GetFormat(obj->pWF, dwSizeAllocated, &dwSizeWritten);
	if (FAILED(hr)){
		seterror("DirectSoundBuffer_GetFormat", hr);
		return NULL;
	}
	return (PyObject *)obj;
}

static char DirectSoundBuffer_GetVolume__doc__[] =
""
;
static PyObject *
DirectSoundBuffer_GetVolume(DirectSoundBufferObject *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args, ""))
		return NULL;
	long level;
	HRESULT hr = self->pI->GetVolume(&level);
	if (FAILED(hr)){
		seterror("DirectSoundBuffer_GetVolume", hr);
		return NULL;
	}
	return Py_BuildValue("l",level);
}

static char DirectSoundBuffer_GetPan__doc__[] =
""
;
static PyObject *
DirectSoundBuffer_GetPan(DirectSoundBufferObject *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args, ""))
		return NULL;	
	long pan;
	HRESULT hr = self->pI->GetPan(&pan);
	if (FAILED(hr)){
		seterror("DirectSoundBuffer_GetPan", hr);
		return NULL;
	}
	return Py_BuildValue("l", pan);
}

static char DirectSoundBuffer_GetFrequency__doc__[] =
""
;
static PyObject *
DirectSoundBuffer_GetFrequency(DirectSoundBufferObject *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args, ""))
		return NULL;	
	DWORD dwFrequency;
	HRESULT hr = self->pI->GetFrequency(&dwFrequency);
	if (FAILED(hr)){
		seterror("DirectSoundBuffer_GetFrequency", hr);
		return NULL;
	}
	return Py_BuildValue("i", dwFrequency);
}

static char DirectSoundBuffer_GetStatus__doc__[] =
""
;
static PyObject *
DirectSoundBuffer_GetStatus(DirectSoundBufferObject *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args, ""))
		return NULL;
	DWORD status;
	HRESULT hr = self->pI->GetStatus(&status);
	if (FAILED(hr)){
		seterror("DirectSoundBuffer_GetStatus", hr);
		return NULL;
	}
	return Py_BuildValue("i", status);
}

static char DirectSoundBuffer_Initialize__doc__[] =
""
;
static PyObject *
DirectSoundBuffer_Initialize(DirectSoundBufferObject *self, PyObject *args)
{
	DirectSoundObject *ds;
	DSBUFFERDESCObject *dsbd;
	if (!PyArg_ParseTuple(args, "O!O!", &DirectSoundType, &ds, &DSBUFFERDESCType, &dsbd))
		return NULL;	
	HRESULT hr = self->pI->Initialize(ds->pI, &dsbd->d);
	if (FAILED(hr)){
		seterror("DirectSoundBuffer_Initialize", hr);
		return NULL;
	}
	Py_INCREF(Py_None);
	return Py_None;
}

static char DirectSoundBuffer_Lock__doc__[] =
""
;
static PyObject *
DirectSoundBuffer_Lock(DirectSoundBufferObject *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args, ""))
		return NULL;
	seterror("DirectSoundBuffer_Lock not implemented");
	return NULL;
	DWORD dwWriteCursor = 0;   
	DWORD dwWriteBytes = 0;  
	BYTE *pvAudioPtr = NULL;  
	DWORD dwAudioBytes;  
	BYTE *pvWrapAudioPtr = NULL;  
	DWORD dwWrapAudioBytes;  
	DWORD dwFlags  = 0;          
	HRESULT hr = self->pI->Lock(dwWriteCursor, dwWriteBytes, (void**)&pvAudioPtr, 
		&dwAudioBytes, (void**)&pvWrapAudioPtr, &dwWrapAudioBytes, dwFlags);         
	if (FAILED(hr)){
		seterror("DirectSoundBuffer_Lock", hr);
		return NULL;
	}
	Py_INCREF(Py_None);
	return Py_None;
}

static char DirectSoundBuffer_Play__doc__[] =
""
;
static PyObject *
DirectSoundBuffer_Play(DirectSoundBufferObject *self, PyObject *args)
{
	DWORD dwPriority = 0;
	DWORD dwFlags = 0;
	if (!PyArg_ParseTuple(args, "|ii", dwPriority, dwFlags))
		return NULL;	
	DWORD dwReserved1 = 0;
	HRESULT hr = self->pI->Play(dwReserved1, dwPriority, dwFlags);
	if (FAILED(hr)){
		seterror("DirectSoundBuffer_Play", hr);
		return NULL;
	}
	Py_INCREF(Py_None);
	return Py_None;
}

static char DirectSoundBuffer_SetCurrentPosition__doc__[] =
""
;
static PyObject *
DirectSoundBuffer_SetCurrentPosition(DirectSoundBufferObject *self, PyObject *args)
{
	// New position, in bytes, from the beginning of the buffer that will 
	// be used when the sound buffer is played. 
	DWORD dwNewPosition = 0;
	if(!PyArg_ParseTuple(args, "i", &dwNewPosition))
		return NULL;	
	HRESULT hr = self->pI->SetCurrentPosition(dwNewPosition);
	if (FAILED(hr)){
		seterror("DirectSoundBuffer_SetCurrentPosition", hr);
		return NULL;
	}
	Py_INCREF(Py_None);
	return Py_None;
}

static char DirectSoundBuffer_SetFormat__doc__[] =
""
;
static PyObject *
DirectSoundBuffer_SetFormat(DirectSoundBufferObject *self, PyObject *args)
{	
	WaveFormatExObject *obj;
	if (!PyArg_ParseTuple(args, "O!", &WaveFormatExType, &obj))
		return NULL;	
	HRESULT hr = self->pI->SetFormat(obj->pWF);
	if (FAILED(hr)){
		seterror("DirectSoundBuffer_SetFormat", hr);
		return NULL;
	}
	Py_INCREF(Py_None);
	return Py_None;
}

static char DirectSoundBuffer_SetVolume__doc__[] =
""
;
static PyObject *
DirectSoundBuffer_SetVolume(DirectSoundBufferObject *self, PyObject *args)
{
	// The volume is specified in hundredths of decibels (dB) i.e. cdB
	// V = V_0 * 2^(cdb/1000)
    // cdb=-1000 -> V_0 / 2
	// cdb=-2000 -> V_0 / 4 etc
	LONG cdB;
	if(!PyArg_ParseTuple(args, "l", &cdB))
		return NULL;
	if(cdB>DSBVOLUME_MAX) cdB = DSBVOLUME_MAX; // 0 dB
	else if(cdB<DSBVOLUME_MIN) cdB = DSBVOLUME_MIN; // -10000 cdB = -100 dB
	HRESULT hr = self->pI->SetVolume(cdB);
	if (FAILED(hr)){
		seterror("DirectSoundBuffer_SetVolume", hr);
		return NULL;
	}
	Py_INCREF(Py_None);
	return Py_None;
}

static char DirectSoundBuffer_SetPan__doc__[] =
"Set relative volume between the left and right channels"
;
static PyObject *
DirectSoundBuffer_SetPan(DirectSoundBufferObject *self, PyObject *args)
{
	int pan;
	if (!PyArg_ParseTuple(args, "i", &pan))
		return NULL;	
	HRESULT hr = self->pI->SetPan(pan);
	if (FAILED(hr)){
		seterror("DirectSoundBuffer_SetPan", hr);
		return NULL;
	}
	Py_INCREF(Py_None);
	return Py_None;
}

static char DirectSoundBuffer_SetFrequency__doc__[] =
"Sets the frequency at which the audio samples are played (100Hz and 100kHz)"
;
static PyObject *
DirectSoundBuffer_SetFrequency(DirectSoundBufferObject *self, PyObject *args)
{
	DWORD dwFrequency; // New frequency, in hertz (Hz), at which to play the audio samples
	if (!PyArg_ParseTuple(args, "i", &dwFrequency))
		return NULL;
	if(dwFrequency<DSBFREQUENCY_MIN) dwFrequency = DSBFREQUENCY_MIN;
	if(dwFrequency>DSBFREQUENCY_MAX) dwFrequency = DSBFREQUENCY_MAX;
	HRESULT hr = self->pI->SetFrequency(dwFrequency);
	if (FAILED(hr)){
		seterror("DirectSoundBuffer_SetFrequency", hr);
		return NULL;
	}
	Py_INCREF(Py_None);
	return Py_None;
}

static char DirectSoundBuffer_Stop__doc__[] =
""
;
static PyObject *
DirectSoundBuffer_Stop(DirectSoundBufferObject *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args, ""))
		return NULL;	
	HRESULT hr = self->pI->Stop();
	if (FAILED(hr)){
		seterror("DirectSoundBuffer_Stop", hr);
		return NULL;
	}
	Py_INCREF(Py_None);
	return Py_None;
}

static char DirectSoundBuffer_Unlock__doc__[] =
""
;
static PyObject *
DirectSoundBuffer_Unlock(DirectSoundBufferObject *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args, ""))
		return NULL;
	seterror("DirectSoundBuffer_Unlock not implemented");
	return NULL;
	BYTE *pvAudioPtr;
	DWORD dwAudioBytes; 
	BYTE *pvWrapAudioPtr = NULL; 
	DWORD dwWrapAudioBytes = 0;  
	HRESULT hr = self->pI->Unlock(pvAudioPtr, dwAudioBytes, pvWrapAudioPtr, dwWrapAudioBytes);
	if (FAILED(hr)){
		seterror("DirectSoundBuffer_Unlock", hr);
		return NULL;
	}
	Py_INCREF(Py_None);
	return Py_None;
}

static char DirectSoundBuffer_Restore__doc__[] =
""
;
static PyObject *
DirectSoundBuffer_Restore(DirectSoundBufferObject *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args, ""))
		return NULL;	
	HRESULT hr = self->pI->Restore();
	if (FAILED(hr)){
		seterror("DirectSoundBuffer_Restore", hr);
		return NULL;
	}
	Py_INCREF(Py_None);
	return Py_None;
}

static char DirectSoundBuffer_QueryIDirectSound3DListener__doc__[] =
""
;
static PyObject *
DirectSoundBuffer_QueryIDirectSound3DListener(DirectSoundBufferObject *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args, ""))
		return NULL;	
	HRESULT hr;
	DirectSound3DListenerObject *obj = newDirectSound3DListenerObject();	
	hr = self->pI->QueryInterface(IID_IDirectSound3DListener,(void**)&obj->pI);
	if (FAILED(hr)){
		Py_DECREF(obj);
		seterror("DirectSoundBuffer_QueryIDirectSound3DListener", hr);
		return NULL;
	}
	return (PyObject*) obj;
}


static char DirectSoundBuffer_QueryIDirectSound3DBuffer__doc__[] =
""
;
static PyObject *
DirectSoundBuffer_QueryIDirectSound3DBuffer(DirectSoundBufferObject *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args, ""))
		return NULL;	
	HRESULT hr;
	DirectSound3DBufferObject *obj = newDirectSound3DBufferObject();	
	hr = self->pI->QueryInterface(IID_IDirectSound3DBuffer,(void**)&obj->pI);
	if (FAILED(hr)){
		Py_DECREF(obj);
		seterror("DirectSoundBuffer_QueryIDirectSound3DBuffer", hr);
		return NULL;
	}
	return (PyObject*) obj;
}

static struct PyMethodDef DirectSoundBuffer_methods[] = {
	{"GetCaps", (PyCFunction)DirectSoundBuffer_GetCaps, METH_VARARGS, DirectSoundBuffer_GetCaps__doc__},
	{"GetCurrentPosition", (PyCFunction)DirectSoundBuffer_GetCurrentPosition, METH_VARARGS, DirectSoundBuffer_GetCurrentPosition__doc__},
	{"GetFormat", (PyCFunction)DirectSoundBuffer_GetFormat, METH_VARARGS, DirectSoundBuffer_GetFormat__doc__},
	{"GetVolume", (PyCFunction)DirectSoundBuffer_GetVolume, METH_VARARGS, DirectSoundBuffer_GetVolume__doc__},
	{"GetPan", (PyCFunction)DirectSoundBuffer_GetPan, METH_VARARGS, DirectSoundBuffer_GetPan__doc__},
	{"GetFrequency", (PyCFunction)DirectSoundBuffer_GetFrequency, METH_VARARGS, DirectSoundBuffer_GetFrequency__doc__},
	{"GetStatus", (PyCFunction)DirectSoundBuffer_GetStatus, METH_VARARGS, DirectSoundBuffer_GetStatus__doc__},
	{"Initialize", (PyCFunction)DirectSoundBuffer_Initialize, METH_VARARGS, DirectSoundBuffer_Initialize__doc__},
	{"Lock", (PyCFunction)DirectSoundBuffer_Lock, METH_VARARGS, DirectSoundBuffer_Lock__doc__},
	{"Play", (PyCFunction)DirectSoundBuffer_Play, METH_VARARGS, DirectSoundBuffer_Play__doc__},
	{"SetCurrentPosition", (PyCFunction)DirectSoundBuffer_SetCurrentPosition, METH_VARARGS, DirectSoundBuffer_SetCurrentPosition__doc__},
	{"SetFormat", (PyCFunction)DirectSoundBuffer_SetFormat, METH_VARARGS, DirectSoundBuffer_SetFormat__doc__},
	{"SetVolume", (PyCFunction)DirectSoundBuffer_SetVolume, METH_VARARGS, DirectSoundBuffer_SetVolume__doc__},
	{"SetPan", (PyCFunction)DirectSoundBuffer_SetPan, METH_VARARGS, DirectSoundBuffer_SetPan__doc__},
	{"SetFrequency", (PyCFunction)DirectSoundBuffer_SetFrequency, METH_VARARGS, DirectSoundBuffer_SetFrequency__doc__},
	{"Stop", (PyCFunction)DirectSoundBuffer_Stop, METH_VARARGS, DirectSoundBuffer_Stop__doc__},
	{"Unlock", (PyCFunction)DirectSoundBuffer_Unlock, METH_VARARGS, DirectSoundBuffer_Unlock__doc__},
	{"Restore", (PyCFunction)DirectSoundBuffer_Restore, METH_VARARGS, DirectSoundBuffer_Restore__doc__},
	{"QueryIDirectSound3DListener", (PyCFunction)DirectSoundBuffer_QueryIDirectSound3DListener, METH_VARARGS, DirectSoundBuffer_QueryIDirectSound3DListener__doc__},
	{"QueryIDirectSound3DBuffer", (PyCFunction)DirectSoundBuffer_QueryIDirectSound3DBuffer, METH_VARARGS, DirectSoundBuffer_QueryIDirectSound3DBuffer__doc__},
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

////////////////////////////////////////////
// DirectSound3DBuffer object 

static char DirectSound3DBuffer_GetAllParameters__doc__[] =
""
;
static PyObject *
DirectSound3DBuffer_GetAllParameters(DirectSound3DBufferObject *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args, ""))
		return NULL;	
	HRESULT hr;
	DS3DBUFFERObject *obj = newDS3DBUFFERObject();
	hr = self->pI->GetAllParameters(&obj->d);
	if (FAILED(hr)){
		Py_DECREF(obj);		
		seterror("DirectSound3DBuffer_GetAllParameters", hr);
		return NULL;
	}
	return (PyObject*)obj;
}

static char DirectSound3DBuffer_SetAllParameters__doc__[] =
""
;
static PyObject *
DirectSound3DBuffer_SetAllParameters(DirectSound3DBufferObject *self, PyObject *args)
{
	DS3DBUFFERObject *obj;
	DWORD flags = DS3D_IMMEDIATE;
	if (!PyArg_ParseTuple(args, "O!|i",&DS3DBUFFERType,&obj))
		return NULL;	
	HRESULT hr;
	hr = self->pI->SetAllParameters(&obj->d, flags);
	if (FAILED(hr)){
		seterror("DirectSound3DBuffer_SetAllParameters", hr);
		return NULL;
	}
	Py_INCREF(Py_None);
	return Py_None;
}

 
static struct PyMethodDef DirectSound3DBuffer_methods[] = {
	{"GetAllParameters", (PyCFunction)DirectSound3DBuffer_GetAllParameters, METH_VARARGS, DirectSound3DBuffer_GetAllParameters__doc__},
	{"SetAllParameters", (PyCFunction)DirectSound3DBuffer_SetAllParameters, METH_VARARGS, DirectSound3DBuffer_SetAllParameters__doc__},
	{NULL, (PyCFunction)NULL, 0, NULL}		/* sentinel */
};

static void
DirectSound3DBuffer_dealloc(DirectSound3DBufferObject *self)
{
	/* XXXX Add your own cleanup code here */
	RELEASE(self->pI);
	PyMem_DEL(self);
}

static PyObject *
DirectSound3DBuffer_getattr(DirectSound3DBufferObject *self, char *name)
{
	/* XXXX Add your own getattr code here */
	return Py_FindMethod(DirectSound3DBuffer_methods, (PyObject *)self, name);
}

static char DirectSound3DBufferType__doc__[] =
""
;

static PyTypeObject DirectSound3DBufferType = {
	PyObject_HEAD_INIT(&PyType_Type)
	0,				/*ob_size*/
	"DirectSound3DBuffer",			/*tp_name*/
	sizeof(DirectSound3DBufferObject),		/*tp_basicsize*/
	0,				/*tp_itemsize*/
	/* methods */
	(destructor)DirectSound3DBuffer_dealloc,	/*tp_dealloc*/
	(printfunc)0,		/*tp_print*/
	(getattrfunc)DirectSound3DBuffer_getattr,	/*tp_getattr*/
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
	DirectSound3DBufferType__doc__ /* Documentation string */
};

// End of code for DirectSound3DBuffer object 
////////////////////////////////////////////


////////////////////////////////////////////
// DirectSound3DListener object 

static char DirectSound3DListener_GetAllParameters__doc__[] =
""
;
static PyObject *
DirectSound3DListener_GetAllParameters(DirectSound3DListenerObject *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args, ""))
		return NULL;	
	HRESULT hr;
	DS3DLISTENERObject *obj = newDS3DLISTENERObject();
	hr = self->pI->GetAllParameters(&obj->d);
	if (FAILED(hr)){
		Py_DECREF(obj);		
		seterror("DirectSound3DListener_GetAllParameters", hr);
		return NULL;
	}
	return (PyObject*)obj;
}

static char DirectSound3DListener_SetAllParameters__doc__[] =
""
;
static PyObject *
DirectSound3DListener_SetAllParameters(DirectSound3DListenerObject *self, PyObject *args)
{
	DS3DLISTENERObject *obj;
	DWORD flags = DS3D_IMMEDIATE;
	if (!PyArg_ParseTuple(args, "O!|i",&DS3DLISTENERType,&obj))
		return NULL;	
	HRESULT hr;
	hr = self->pI->SetAllParameters(&obj->d, flags);
	if (FAILED(hr)){
		seterror("DirectSound3DListener_SetAllParameters", hr);
		return NULL;
	}
	Py_INCREF(Py_None);
	return Py_None;
}

static struct PyMethodDef DirectSound3DListener_methods[] = {
	{"GetAllParameters", (PyCFunction)DirectSound3DListener_GetAllParameters, METH_VARARGS, DirectSound3DListener_GetAllParameters__doc__},
	{"SetAllParameters", (PyCFunction)DirectSound3DListener_SetAllParameters, METH_VARARGS, DirectSound3DListener_SetAllParameters__doc__},
	{NULL, (PyCFunction)NULL, 0, NULL}		/* sentinel */
};

static void
DirectSound3DListener_dealloc(DirectSound3DListenerObject *self)
{
	/* XXXX Add your own cleanup code here */
	RELEASE(self->pI);
	PyMem_DEL(self);
}

static PyObject *
DirectSound3DListener_getattr(DirectSound3DListenerObject *self, char *name)
{
	/* XXXX Add your own getattr code here */
	return Py_FindMethod(DirectSound3DListener_methods, (PyObject *)self, name);
}

static char DirectSound3DListenerType__doc__[] =
""
;

static PyTypeObject DirectSound3DListenerType = {
	PyObject_HEAD_INIT(&PyType_Type)
	0,				/*ob_size*/
	"DirectSound3DListener",			/*tp_name*/
	sizeof(DirectSound3DListenerObject),		/*tp_basicsize*/
	0,				/*tp_itemsize*/
	/* methods */
	(destructor)DirectSound3DListener_dealloc,	/*tp_dealloc*/
	(printfunc)0,		/*tp_print*/
	(getattrfunc)DirectSound3DListener_getattr,	/*tp_getattr*/
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
	DirectSound3DListenerType__doc__ /* Documentation string */
};

// End of code for DirectSound3DListener object 
////////////////////////////////////////////

////////////////////////////////////////////
// DSBUFFERDESC struct object 

static char DSBUFFERDESC_Clear__doc__[] =
"Clear DSBUFFERDESC struct for reuse"
;
static PyObject *
DSBUFFERDESC_Clear(DSBUFFERDESCObject *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args, ""))
		return NULL;	
	memset(&self->d, 0, sizeof(self->d));
	self->d.dwSize = sizeof(self->d);
	Py_INCREF(Py_None);
	return Py_None;
}

static char DSBUFFERDESC_SetFlags__doc__[] =
""
;
static PyObject*
DSBUFFERDESC_SetFlags(DSBUFFERDESCObject *self, PyObject *args)
{
	DWORD dwFlags;
	if (!PyArg_ParseTuple(args, "i",&dwFlags))
		return NULL;
	self->d.dwFlags = dwFlags;
	Py_INCREF(Py_None);
	return Py_None;
}
static char DSBUFFERDESC_GetFlags__doc__[] =
""
;
static PyObject*
DSBUFFERDESC_GetFlags(DSBUFFERDESCObject *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args, ""))
		return NULL;
	return Py_BuildValue("i",self->d.dwFlags);
}


static struct PyMethodDef DSBUFFERDESC_methods[] = {
	{"Clear", (PyCFunction)DSBUFFERDESC_Clear, METH_VARARGS, DSBUFFERDESC_Clear__doc__},
	{"SetFlags", (PyCFunction)DSBUFFERDESC_SetFlags, METH_VARARGS, DSBUFFERDESC_SetFlags__doc__},
	{"GetFlags", (PyCFunction)DSBUFFERDESC_GetFlags, METH_VARARGS, DSBUFFERDESC_GetFlags__doc__},
	{NULL, (PyCFunction)NULL, 0, NULL}		/* sentinel */
};

static void
DSBUFFERDESC_dealloc(DSBUFFERDESCObject *self)
{
	/* XXXX Add your own cleanup code here */
	PyMem_DEL(self);
}

static PyObject *
DSBUFFERDESC_getattr(DSBUFFERDESCObject *self, char *name)
{
	/* XXXX Add your own getattr code here */
	return Py_FindMethod(DSBUFFERDESC_methods, (PyObject *)self, name);
}

static char DSBUFFERDESCType__doc__[] =
""
;

static PyTypeObject DSBUFFERDESCType = {
	PyObject_HEAD_INIT(&PyType_Type)
	0,				/*ob_size*/
	"DSBUFFERDESC",			/*tp_name*/
	sizeof(DSBUFFERDESCObject),		/*tp_basicsize*/
	0,				/*tp_itemsize*/
	/* methods */
	(destructor)DSBUFFERDESC_dealloc,	/*tp_dealloc*/
	(printfunc)0,		/*tp_print*/
	(getattrfunc)DSBUFFERDESC_getattr,	/*tp_getattr*/
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
	DSBUFFERDESCType__doc__ /* Documentation string */
};

// End of code for DSBUFFERDESC object 
////////////////////////////////////////////

////////////////////////////////////////////
// DSCAPS struct object 

static char DSCAPS_Clear__doc__[] =
"Clear DSCAPS struct for reuse"
;
static PyObject *
DSCAPS_Clear(DSCAPSObject *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args, ""))
		return NULL;	
	memset(&self->d, 0, sizeof(self->d));
	self->d.dwSize = sizeof(self->d);
	Py_INCREF(Py_None);
	return Py_None;
}


static struct PyMethodDef DSCAPS_methods[] = {
	{"Clear", (PyCFunction)DSCAPS_Clear, METH_VARARGS, DSCAPS_Clear__doc__},
	{NULL, (PyCFunction)NULL, 0, NULL}		/* sentinel */
};

static void
DSCAPS_dealloc(DSCAPSObject *self)
{
	/* XXXX Add your own cleanup code here */
	PyMem_DEL(self);
}

static PyObject *
DSCAPS_getattr(DSCAPSObject *self, char *name)
{
	/* XXXX Add your own getattr code here */
	return Py_FindMethod(DSCAPS_methods, (PyObject *)self, name);
}

static char DSCAPSType__doc__[] =
""
;

static PyTypeObject DSCAPSType = {
	PyObject_HEAD_INIT(&PyType_Type)
	0,				/*ob_size*/
	"DSCAPS",			/*tp_name*/
	sizeof(DSCAPSObject),		/*tp_basicsize*/
	0,				/*tp_itemsize*/
	/* methods */
	(destructor)DSCAPS_dealloc,	/*tp_dealloc*/
	(printfunc)0,		/*tp_print*/
	(getattrfunc)DSCAPS_getattr,	/*tp_getattr*/
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
	DSCAPSType__doc__ /* Documentation string */
};

// End of code for DSCAPS object 
////////////////////////////////////////////

////////////////////////////////////////////
// DSBCAPS struct object 

static char DSBCAPS_Clear__doc__[] =
"Clear DSBCAPS struct for reuse"
;
static PyObject *
DSBCAPS_Clear(DSBCAPSObject *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args, ""))
		return NULL;	
	memset(&self->d, 0, sizeof(self->d));
	self->d.dwSize = sizeof(self->d);
	Py_INCREF(Py_None);
	return Py_None;
}


static struct PyMethodDef DSBCAPS_methods[] = {
	{"Clear", (PyCFunction)DSBCAPS_Clear, METH_VARARGS, DSBCAPS_Clear__doc__},
	{NULL, (PyCFunction)NULL, 0, NULL}		/* sentinel */
};

static void
DSBCAPS_dealloc(DSBCAPSObject *self)
{
	/* XXXX Add your own cleanup code here */
	PyMem_DEL(self);
}

static PyObject *
DSBCAPS_getattr(DSBCAPSObject *self, char *name)
{
	/* XXXX Add your own getattr code here */
	return Py_FindMethod(DSBCAPS_methods, (PyObject *)self, name);
}

static char DSBCAPSType__doc__[] =
""
;

static PyTypeObject DSBCAPSType = {
	PyObject_HEAD_INIT(&PyType_Type)
	0,				/*ob_size*/
	"DSBCAPS",			/*tp_name*/
	sizeof(DSBCAPSObject),		/*tp_basicsize*/
	0,				/*tp_itemsize*/
	/* methods */
	(destructor)DSBCAPS_dealloc,	/*tp_dealloc*/
	(printfunc)0,		/*tp_print*/
	(getattrfunc)DSBCAPS_getattr,	/*tp_getattr*/
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
	DSBCAPSType__doc__ /* Documentation string */
};

// End of code for DSBCAPS object 
////////////////////////////////////////////

////////////////////////////////////////////
// DS3DBUFFER struct object 

static char DS3DBUFFER_Clear__doc__[] =
"Clear DS3DBUFFER struct for reuse"
;
static PyObject *
DS3DBUFFER_Clear(DS3DBUFFERObject *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args, ""))
		return NULL;	
	memset(&self->d, 0, sizeof(self->d));
	self->d.dwSize = sizeof(self->d);
	Py_INCREF(Py_None);
	return Py_None;
}


static struct PyMethodDef DS3DBUFFER_methods[] = {
	{"Clear", (PyCFunction)DS3DBUFFER_Clear, METH_VARARGS, DS3DBUFFER_Clear__doc__},
	{NULL, (PyCFunction)NULL, 0, NULL}		/* sentinel */
};

static void
DS3DBUFFER_dealloc(DS3DBUFFERObject *self)
{
	/* XXXX Add your own cleanup code here */
	PyMem_DEL(self);
}

static PyObject *
DS3DBUFFER_getattr(DS3DBUFFERObject *self, char *name)
{
	/* XXXX Add your own getattr code here */
	return Py_FindMethod(DS3DBUFFER_methods, (PyObject *)self, name);
}

static char DS3DBUFFERType__doc__[] =
""
;

static PyTypeObject DS3DBUFFERType = {
	PyObject_HEAD_INIT(&PyType_Type)
	0,				/*ob_size*/
	"DS3DBUFFER",			/*tp_name*/
	sizeof(DS3DBUFFERObject),		/*tp_basicsize*/
	0,				/*tp_itemsize*/
	/* methods */
	(destructor)DS3DBUFFER_dealloc,	/*tp_dealloc*/
	(printfunc)0,		/*tp_print*/
	(getattrfunc)DS3DBUFFER_getattr,	/*tp_getattr*/
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
	DS3DBUFFERType__doc__ /* Documentation string */
};

// End of code for DS3DBUFFER object 
////////////////////////////////////////////

////////////////////////////////////////////
// DS3DLISTENER struct object 

static char DS3DLISTENER_Clear__doc__[] =
"Clear DS3DLISTENER struct for reuse"
;
static PyObject *
DS3DLISTENER_Clear(DS3DLISTENERObject *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args, ""))
		return NULL;	
	memset(&self->d, 0, sizeof(self->d));
	self->d.dwSize = sizeof(self->d);
	Py_INCREF(Py_None);
	return Py_None;
}


static struct PyMethodDef DS3DLISTENER_methods[] = {
	{"Clear", (PyCFunction)DS3DLISTENER_Clear, METH_VARARGS, DS3DLISTENER_Clear__doc__},
	{NULL, (PyCFunction)NULL, 0, NULL}		/* sentinel */
};

static void
DS3DLISTENER_dealloc(DS3DLISTENERObject *self)
{
	/* XXXX Add your own cleanup code here */
	PyMem_DEL(self);
}

static PyObject *
DS3DLISTENER_getattr(DS3DLISTENERObject *self, char *name)
{
	/* XXXX Add your own getattr code here */
	return Py_FindMethod(DS3DLISTENER_methods, (PyObject *)self, name);
}

static char DS3DLISTENERType__doc__[] =
""
;

static PyTypeObject DS3DLISTENERType = {
	PyObject_HEAD_INIT(&PyType_Type)
	0,				/*ob_size*/
	"DS3DLISTENER",			/*tp_name*/
	sizeof(DS3DLISTENERObject),		/*tp_basicsize*/
	0,				/*tp_itemsize*/
	/* methods */
	(destructor)DS3DLISTENER_dealloc,	/*tp_dealloc*/
	(printfunc)0,		/*tp_print*/
	(getattrfunc)DS3DLISTENER_getattr,	/*tp_getattr*/
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
	DS3DLISTENERType__doc__ /* Documentation string */
};

// End of code for DS3DLISTENER object 
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


static char CreateDSBufferDesc__doc__[] =
""
;
static PyObject *
CreateDSBufferDesc(PyObject *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args, "")) return NULL;
	DSBUFFERDESCObject *obj = newDSBUFFERDESCObject();
	if (obj == NULL) return NULL;
	return (PyObject*)obj;
}

// TEMPORARY
#include "riff.h"
IDirectSoundBuffer* CreateDSBufferFromFile(IDirectSound *pI, DSBUFFERDESC *pdsbd, char *pszFilename)
	{
	RIFFFile riff;
	if(!riff.open(pszFilename))
		{
		seterror("Failed opening wave file");
        return NULL;
		}

	if(!riff.seekToData())
		{
		seterror("Failed finding wave data");
        return NULL;
		}

	// fill DSBUFFERDESC with format
    DWORD dwDataSize = riff.ckIn.cksize;
    pdsbd->dwBufferBytes = dwDataSize;
    DWORD dw = riff.pwfxInfo->cbSize + sizeof(WAVEFORMATEX);
	pdsbd->lpwfxFormat = (WAVEFORMATEX*) new BYTE[dw];
	memcpy(pdsbd->lpwfxFormat, riff.pwfxInfo, dw);

	// create DS buffer
	IDirectSoundBuffer* lpDSB=NULL;
    if(pI->CreateSoundBuffer(pdsbd, &lpDSB, NULL) != 0)
		{
  		seterror("CreateSoundBuffer failed");
        return NULL;
        }

	// lock buffer
    LPBYTE lpData = NULL;
    DWORD dwBSize;
    DWORD dwWrapBSize;
    LPVOID lpWrapPtr;
	HRESULT hr = lpDSB->Lock(0, dwDataSize, (LPLPVOID)&lpData, &dwBSize, &lpWrapPtr, &dwWrapBSize, 0L);
	if(FAILED(hr))
		{
    	seterror("CreateDSBufferFromFile::Lock failed");
		return NULL;
		}
	
	// read data
	dwDataSize = dwBSize;
	UINT cbActualRead;
    if (!riff.readData(dwDataSize, lpData, &cbActualRead))
        {
        if(lpData != NULL) GlobalFree(lpData);
		lpDSB->Release();
    	seterror("CreateDSBufferFromFile::RIFF::readData failed");
		return NULL;
		} 

	// unlock buffer
    if (lpDSB != NULL)
        lpDSB->Unlock(lpData, cbActualRead,NULL, 0 );
    return lpDSB;
	}


static char GetWaveoutVolume__doc__[] =
""
;
static PyObject *
GetWaveoutVolume(PyObject *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args, "")) return NULL;
	bool found = false;
	DWORD dwLRV = 0;
	UINT uNumDevs = waveOutGetNumDevs();
	for(UINT uDeviceID=0; uDeviceID<uNumDevs; uDeviceID++)
		{	
		WAVEOUTCAPS waveCaps;
		int res = waveOutGetDevCaps(uDeviceID, &waveCaps, sizeof(WAVEOUTCAPS));
		if(res != MMSYSERR_NOERROR) continue;
		if(waveCaps.dwSupport & WAVECAPS_VOLUME)
			{
			res = waveOutGetVolume((HWAVEOUT)uDeviceID, &dwLRV);
			if(res == MMSYSERR_NOERROR) 
				{
				found = true;
				break;
				}
			}
		}
	if(!found)
		{
		seterror("No device found supporting volume");
		return NULL;
		}
	int lv = LOWORD(dwLRV);
	int rv = HIWORD(dwLRV);
	return Py_BuildValue("ii",lv, rv);
}

static char SetWaveoutVolume__doc__[] =
""
;
static PyObject *
SetWaveoutVolume(PyObject *self, PyObject *args)
{
	int lv, rv;
	if (!PyArg_ParseTuple(args, "ii", &lv, &rv)) return NULL;
	if(lv>0xFFFF || lv<0) lv = 0xFFFF;
	if(rv>0xFFFF || rv<0) rv = 0xFFFF;
	DWORD dwLRV = MAKELONG(WORD(lv),WORD(rv));
	bool found = false;
	UINT uNumDevs = waveOutGetNumDevs();
	for(UINT uDeviceID=0; uDeviceID<uNumDevs; uDeviceID++)
		{	
		WAVEOUTCAPS waveCaps;
		int res = waveOutGetDevCaps(uDeviceID, &waveCaps, sizeof(WAVEOUTCAPS));
		if(res != MMSYSERR_NOERROR) continue;
		if(waveCaps.dwSupport & WAVECAPS_VOLUME)
			{
			res = waveOutSetVolume((HWAVEOUT)uDeviceID, dwLRV);
			if(res == MMSYSERR_NOERROR)
				{
				found = true;
				break;
				}
			}
		}
	if(!found)
		{
		seterror("No device found supporting volume");
		return NULL;
		}
	Py_INCREF(Py_None);
	return Py_None;
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
	{"CreateDSBufferDesc", (PyCFunction)CreateDSBufferDesc, METH_VARARGS, CreateDSBufferDesc__doc__},
	{"GetWaveoutVolume", (PyCFunction)GetWaveoutVolume, METH_VARARGS, GetWaveoutVolume__doc__},
	{"SetWaveoutVolume", (PyCFunction)SetWaveoutVolume, METH_VARARGS, SetWaveoutVolume__doc__},
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

static struct constentry _dsscl[] ={
	{"DSSCL_NORMAL",DSSCL_NORMAL},
	{"DSSCL_PRIORITY",DSSCL_PRIORITY},
	{"DSSCL_EXCLUSIVE",DSSCL_EXCLUSIVE},
	{"DSSCL_WRITEPRIMARY",DSSCL_WRITEPRIMARY},
	{NULL,0}
	};

static struct constentry _dsbcaps[] ={
	{"DSBCAPS_PRIMARYBUFFER",DSBCAPS_PRIMARYBUFFER},
	{"DSBCAPS_STATIC",DSBCAPS_STATIC},
	{"DSBCAPS_LOCHARDWARE",DSBCAPS_LOCHARDWARE},
	{"DSBCAPS_LOCSOFTWARE",DSBCAPS_LOCSOFTWARE},
	{"DSBCAPS_CTRL3D",DSBCAPS_CTRL3D},
	{"DSBCAPS_CTRLFREQUENCY",DSBCAPS_CTRLFREQUENCY},
	{"DSBCAPS_CTRLPAN",DSBCAPS_CTRLPAN},
	{"DSBCAPS_CTRLVOLUME",DSBCAPS_CTRLVOLUME},
	{"DSBCAPS_CTRLPOSITIONNOTIFY",DSBCAPS_CTRLPOSITIONNOTIFY},
	{"DSBCAPS_CTRLDEFAULT",DSBCAPS_CTRLDEFAULT},
	{"DSBCAPS_CTRLALL",DSBCAPS_CTRLALL},
	{"DSBCAPS_STICKYFOCUS",DSBCAPS_STICKYFOCUS},
	{"DSBCAPS_GLOBALFOCUS",DSBCAPS_GLOBALFOCUS},
	{"DSBCAPS_GETCURRENTPOSITION2",DSBCAPS_GETCURRENTPOSITION2},
	{"DSBCAPS_MUTE3DATMAXDISTANCE",DSBCAPS_MUTE3DATMAXDISTANCE},
	{NULL,0}
	};

static struct constentry _dsbstatus[] ={
	{"DSBSTATUS_PLAYING",DSBSTATUS_PLAYING},
	{"DSBSTATUS_BUFFERLOST",DSBSTATUS_BUFFERLOST},
	{"DSBSTATUS_LOOPING",DSBSTATUS_LOOPING},
	{NULL,0}
	};

static struct constentry _dsbvolume[] ={
	{"DSBVOLUME_MAX",DSBVOLUME_MAX},
	{"DSBVOLUME_MIN",DSBVOLUME_MIN},
	{NULL,0}
	};

static struct constentry _ds3d[] ={
	{"DS3D_IMMEDIATE",DS3D_IMMEDIATE},
	{"DS3D_DEFERRED",DS3D_DEFERRED},
	{NULL,0}
	};

static struct constentry _ds3dmode[] ={
	{"DS3DMODE_NORMAL",DS3DMODE_NORMAL},
	{"DS3DMODE_HEADRELATIVE",DS3DMODE_HEADRELATIVE},
	{"DS3DMODE_DISABLE",DS3DMODE_DISABLE},
	{NULL,0}
	};

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
	FATAL_ERROR_IF(SetItemEnum(d,_dsscl)<0)
	FATAL_ERROR_IF(SetItemEnum(d,_dsbcaps)<0)
	FATAL_ERROR_IF(SetItemEnum(d,_dsbvolume)<0)
	FATAL_ERROR_IF(SetItemEnum(d,_dsbstatus)<0)
	FATAL_ERROR_IF(SetItemEnum(d,_ds3d)<0)
	FATAL_ERROR_IF(SetItemEnum(d,_ds3dmode)<0)

	// Check for errors
	if (PyErr_Occurred())
		Py_FatalError("can't initialize module dsound");
}
