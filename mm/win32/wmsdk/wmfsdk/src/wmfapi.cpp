
/**************************************************************************
Copyright 1991-2000 by Oratrix Development BV, Amsterdam, The Netherlands.

                        All Rights Reserved

***************************************************************************/

#include "Python.h"

#include <windows.h>
#include <wtypes.h>
#include "wmsdk.h"
#include <mmsystem.h>
#include <assert.h>

#include "wmpyrcb.h"

#include "mtpycall.h"

// guests
#include <ddraw.h>
#include <streams.h>

static PyObject *ErrorObject;

PyInterpreterState*
PyCallbackBlock::s_interpreterState = NULL;

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

static PyObject *
PyObjectFromWideChar(WCHAR *wsz,int cch)
	{
	char *psz = new char[cch+1];
	WideCharToMultiByte(CP_ACP,0,wsz,cch+1,psz,cch+1,NULL,NULL);
	psz[cch]='\0';
	PyObject *obj = Py_BuildValue("s",psz);
	delete []psz;
	return obj;
	}

static PyObject *
PyObjectFromLargeInt(LONGLONG l)
	{
	LARGE_INTEGER li;
	li.QuadPart = l;
	PyObject *obj = Py_BuildValue("(ii)",li.HighPart,li.LowPart);
	return obj;
	}

///////////////////////////////////////////
///////////////////////////////////////////
// Objects declarations

//
typedef struct {
	PyObject_HEAD
	/* XXXX Add your own stuff here */
	IWMReader* pI;
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

// Customized Writer object
typedef struct {
	PyObject_HEAD
	IWMWriter* pIWMWriter;
	
	DWORD dwAudioInputNum;
	IWMInputMediaProps *pIAudioInputProps;
	
	DWORD dwVideoInputNum;
	IWMInputMediaProps *pIVideoInputProps;
	
} DDWMWriterObject;

staticforward PyTypeObject DDWMWriterType;

static DDWMWriterObject *
newDDWMWriterObject()
{
	DDWMWriterObject *self;

	self = PyObject_NEW(DDWMWriterObject, &DDWMWriterType);
	if (self == NULL) return NULL;
	self->pIWMWriter = NULL;
	self->pIAudioInputProps = NULL;
	self->pIVideoInputProps = NULL;
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
	IWMMetadataEditor* pI;
} WMMetadataEditorObject;

staticforward PyTypeObject WMMetadataEditorType;

static WMMetadataEditorObject *
newWMMetadataEditorObject()
{
	WMMetadataEditorObject *self;

	self = PyObject_NEW(WMMetadataEditorObject, &WMMetadataEditorType);
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
	IWMIndexer* pI;
} WMIndexerObject;

staticforward PyTypeObject WMIndexerType;

static WMIndexerObject *
newWMIndexerObject()
{
	WMIndexerObject *self;

	self = PyObject_NEW(WMIndexerObject, &WMIndexerType);
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
	IWMWriterSink* pI;
} WMWriterSinkObject;

staticforward PyTypeObject WMWriterSinkType;

static WMWriterSinkObject *
newWMWriterSinkObject()
{
	WMWriterSinkObject *self;

	self = PyObject_NEW(WMWriterSinkObject, &WMWriterSinkType);
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
	IWMWriterFileSink* pI;
} WMWriterFileSinkObject;

staticforward PyTypeObject WMWriterFileSinkType;

static WMWriterFileSinkObject *
newWMWriterFileSinkObject()
{
	WMWriterFileSinkObject *self;

	self = PyObject_NEW(WMWriterFileSinkObject, &WMWriterFileSinkType);
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
	IWMWriterNetworkSink* pI;
} WMWriterNetworkSinkObject;

staticforward PyTypeObject WMWriterNetworkSinkType;

static WMWriterNetworkSinkObject *
newWMWriterNetworkSinkObject()
{
	WMWriterNetworkSinkObject *self;

	self = PyObject_NEW(WMWriterNetworkSinkObject, &WMWriterNetworkSinkType);
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
	IWMMediaProps* pI;
} WMMediaPropsObject;

staticforward PyTypeObject WMMediaPropsType;

static WMMediaPropsObject *
newWMMediaPropsObject()
{
	WMMediaPropsObject *self;
	self = PyObject_NEW(WMMediaPropsObject, &WMMediaPropsType);
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
	IWMVideoMediaProps* pI;
} WMVideoMediaPropsObject;

staticforward PyTypeObject WMVideoMediaPropsType;

static WMVideoMediaPropsObject *
newWMVideoMediaPropsObject()
{
	WMVideoMediaPropsObject *self;

	self = PyObject_NEW(WMVideoMediaPropsObject, &WMVideoMediaPropsType);
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
    BYTE pbBuffer[2048];
    WM_MEDIA_TYPE *pMediaType;		
    DWORD cbBuffer;
} WMMediaTypeObject;

staticforward PyTypeObject WMMediaTypeType;

static WMMediaTypeObject *
newWMMediaTypeObject()
{
	WMMediaTypeObject *self;
	self = PyObject_NEW(WMMediaTypeObject, &WMMediaTypeType);
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

//
typedef struct {
	PyObject_HEAD
	/* XXXX Add your own stuff here */
    WMVIDEOINFOHEADER vih;		
} WMVideoInfoHeaderObject;

staticforward PyTypeObject WMVideoInfoHeaderType;

static WMVideoInfoHeaderObject *
newWMVideoInfoHeaderObject()
{
	WMVideoInfoHeaderObject *self;
	self = PyObject_NEW(WMVideoInfoHeaderObject, &WMVideoInfoHeaderType);
	if (self == NULL)
		return NULL;
	memset(&self->vih,0,sizeof(WMVIDEOINFOHEADER));
	/* XXXX Add your own initializers here */
	return self;
}

//(general but defined here for indepentance)
typedef struct {
	PyObject_HEAD
	/* XXXX Add your own stuff here */
	IUnknown* pI;
} UnknownObject;

staticforward PyTypeObject UnknownType;

static UnknownObject *
newUnknownObject()
{
	UnknownObject *self;

	self = PyObject_NEW(UnknownObject, &UnknownType);
	if (self == NULL)
		return NULL;
	self->pI = NULL;
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

//
typedef struct {
	PyObject_HEAD
	/* XXXX Add your own stuff here */
	IWMReaderAdvanced* pI;
} WMReaderAdvancedObject;

staticforward PyTypeObject WMReaderAdvancedType;

static WMReaderAdvancedObject *
newWMReaderAdvancedObject()
{
	WMReaderAdvancedObject *self;

	self = PyObject_NEW(WMReaderAdvancedObject, &WMReaderAdvancedType);
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
	IWMWriterAdvanced* pI;
} WMWriterAdvancedObject;

staticforward PyTypeObject WMWriterAdvancedType;

static WMWriterAdvancedObject *
newWMWriterAdvancedObject()
{
	WMWriterAdvancedObject *self;

	self = PyObject_NEW(WMWriterAdvancedObject, &WMWriterAdvancedType);
	if (self == NULL)
		return NULL;
	self->pI = NULL;		
	/* XXXX Add your own initializers here */
	return self;
}

//
typedef struct {
	PyObject_HEAD
	IWMStreamConfig* pI;
} WMStreamConfigObject;

staticforward PyTypeObject WMStreamConfigType;

static WMStreamConfigObject *
newWMStreamConfigObject()
{
	WMStreamConfigObject *self;
	self = PyObject_NEW(WMStreamConfigObject, &WMStreamConfigType);
	if (self == NULL) return NULL;
	self->pI = NULL;		
	return self;
}

//
typedef struct {
	PyObject_HEAD
	IWMCodecInfo* pI;
} WMCodecInfoObject;

staticforward PyTypeObject WMCodecInfoType;

static WMCodecInfoObject *
newWMCodecInfoObject()
{
	WMCodecInfoObject *self;
	self = PyObject_NEW(WMCodecInfoObject, &WMCodecInfoType);
	if (self == NULL) return NULL;
	self->pI = NULL;		
	return self;
}

//
typedef struct {
	PyObject_HEAD
	/* XXXX Add your own stuff here */
	IWMStreamList* pI;
} WMStreamListObject;

staticforward PyTypeObject WMStreamListType;

static WMStreamListObject *
newWMStreamListObject()
{
	WMStreamListObject *self;

	self = PyObject_NEW(WMStreamListObject, &WMStreamListType);
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
	IWMReaderStreamClock* pI;
} WMReaderStreamClockObject;

staticforward PyTypeObject WMReaderStreamClockType;

static WMReaderStreamClockObject *
newWMReaderStreamClockObject()
{
	WMReaderStreamClockObject *self;

	self = PyObject_NEW(WMReaderStreamClockObject, &WMReaderStreamClockType);
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
	IWMMutualExclusion* pI;
} WMMutualExclusionObject;

staticforward PyTypeObject WMMutualExclusionType;

static WMMutualExclusionObject *
newWMMutualExclusionObject()
{
	WMMutualExclusionObject *self;

	self = PyObject_NEW(WMMutualExclusionObject, &WMMutualExclusionType);
	if (self == NULL)
		return NULL;
	self->pI = NULL;		
	/* XXXX Add your own initializers here */
	return self;
}

//
typedef struct {
	PyObject_HEAD
	LONGLONG ob_ival;
} LargeIntObject;

staticforward PyTypeObject LargeIntType;

static LargeIntObject *
newLargeIntObject(LONG HighPart,DWORD LowPart)
{
	LargeIntObject *self = PyObject_NEW(LargeIntObject, &LargeIntType);
	if (self == NULL)return NULL;
	LARGE_INTEGER li;
	li.HighPart = HighPart;		
	li.LowPart = LowPart;
	self->ob_ival=li.QuadPart;
	return self;
}
static LargeIntObject *
newLargeIntObject(LONGLONG val)
{
	LargeIntObject *self = PyObject_NEW(LargeIntObject, &LargeIntType);
	if (self == NULL)return NULL;
	self->ob_ival=val;
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
	IWMReaderCallback *pI=NULL;
	hr = obj->pI->QueryInterface(IID_IWMReaderCallback,(void**)&pI);
	if (FAILED(hr)){
		seterror("WMReader_Open-QueryInterface-IWMReaderCallback", hr);
		return NULL;
	}
	Py_BEGIN_ALLOW_THREADS
	hr = self->pI->Open(pwszURL,pI,NULL);
	Py_END_ALLOW_THREADS
	if (FAILED(hr)){
		seterror("WMReader_Open", hr);
		return NULL;
	}
	RELEASE(pI);
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
	DWORD dwOutputNum=0;
	if (!PyArg_ParseTuple(args, "|i",&dwOutputNum))
		return NULL;	
	HRESULT hr;
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
	LargeIntObject *linsStart,*linsDuration;
	float fRate;
	int context=0;
	if (!PyArg_ParseTuple(args, "O!O!f|i",&LargeIntType,&linsStart,
		&LargeIntType,&linsDuration,&fRate,&context))
		return NULL;	
	HRESULT hr;
	QWORD cnsStart=(QWORD)linsStart->ob_ival;
	QWORD cnsDuration=(QWORD)linsDuration->ob_ival;
	Py_BEGIN_ALLOW_THREADS
	hr = self->pI->Start(cnsStart,cnsDuration,fRate,(void*)context);
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

static char WMReader_QueryIWMReaderAdvanced__doc__[] =
""
;
static PyObject *
WMReader_QueryIWMReaderAdvanced(WMReaderObject *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args, ""))
		return NULL;	
	HRESULT hr;
	WMReaderAdvancedObject *obj = newWMReaderAdvancedObject();	
	Py_BEGIN_ALLOW_THREADS
	hr = self->pI->QueryInterface(IID_IWMReaderAdvanced,(void**)&obj->pI);
	Py_END_ALLOW_THREADS
	if (FAILED(hr)){
		Py_DECREF(obj);
		seterror("WMReader_QueryIWMReaderAdvanced", hr);
		return NULL;
	}
	return (PyObject*)obj;
}

static char WMReader_QueryIWMProfile__doc__[] =
""
;
static PyObject *
WMReader_QueryIWMProfile(WMReaderObject *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args, ""))
		return NULL;	
	HRESULT hr;
	WMProfileObject *obj = newWMProfileObject();	
	Py_BEGIN_ALLOW_THREADS
	hr = self->pI->QueryInterface(IID_IWMProfile,(void**)&obj->pI);
	Py_END_ALLOW_THREADS
	if (FAILED(hr)){
		Py_DECREF(obj);
		seterror("WMReader_QueryIWMProfile", hr);
		return NULL;
	}
	return (PyObject*)obj;
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
	{"QueryIWMReaderAdvanced", (PyCFunction)WMReader_QueryIWMReaderAdvanced, METH_VARARGS, WMReader_QueryIWMReaderAdvanced__doc__},
	{"QueryIWMProfile", (PyCFunction)WMReader_QueryIWMProfile, METH_VARARGS, WMReader_QueryIWMProfile__doc__},
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
	WMInputMediaPropsObject *obj=NULL;
	if (!PyArg_ParseTuple(args, "i|O!",&dwInputNum,&WMInputMediaPropsType,&obj))
		return NULL;	
	HRESULT hr;
	Py_BEGIN_ALLOW_THREADS
	hr = self->pI->SetInputProps(dwInputNum,(obj?obj->pI:NULL));
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
	LargeIntObject *linsSampleTime;
	DWORD dwFlags;
	if (!PyArg_ParseTuple(args, "iOiO!",&dwInputNum,&linsSampleTime,
		&dwFlags,&NSSBufferType,&obj))
		return NULL;	
	HRESULT hr;
	QWORD cnsSampleTime = linsSampleTime->ob_ival; // 100-ns units
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

static char WMWriter_WriteDSSample__doc__[] =
""
;
static PyObject *
WMWriter_WriteDSSample(DDWMWriterObject *self, PyObject *args)
{
	DWORD dwInputNum;
	PyObject *obj;
	DWORD dwFlags=0;
	if (!PyArg_ParseTuple(args, "iO|i",&dwInputNum,&obj,&dwFlags))
		return NULL;	
	
	typedef struct {
		PyObject_HEAD
		IMediaSample *pI;
	} MediaSampleObject;
	IMediaSample *pMediaSample = ((MediaSampleObject*)obj)->pI;

	REFERENCE_TIME tStart, tStop;
    HRESULT hr = pMediaSample->GetTime(&tStart,&tStop);
	if (FAILED(hr)){
		seterror("DDWMWriter_WriteDSSample:GetTime", hr);
		return NULL;
	}
	BYTE *pBuffer;
	hr = pMediaSample->GetPointer(&pBuffer);
	if (FAILED(hr)){
		seterror("DDWMWriter_WriteDSSample:GetPointer", hr);
		return NULL;
	}

	
	INSSBuffer *pINSSBuffer = NULL;
	hr = self->pIWMWriter->AllocateSample(pMediaSample->GetActualDataLength(),&pINSSBuffer);
	if (FAILED(hr)){
		seterror("DDWMWriter_WriteDSSample:AllocateSample", hr);
		return NULL;
	}

	BYTE *pbsBuffer;
	hr = pINSSBuffer->GetBuffer(&pbsBuffer);
	if (FAILED(hr)){
		pINSSBuffer->Release();
		seterror("DDWMWriter_WriteDSSample:GetBuffer", hr);
		return NULL;
	}
	CopyMemory(pbsBuffer,pBuffer,pMediaSample->GetActualDataLength());

	hr = self->pIWMWriter->WriteSample(dwInputNum, tStart, dwFlags, pINSSBuffer);
	pINSSBuffer->Release();
	
	if (FAILED(hr)){
		seterror("DDWMWriter_WriteDSSample:WriteSample", hr);
		return NULL;
	}
	Py_INCREF(Py_None);
	return Py_None;
}

static char WMWriter_WriteBuffer__doc__[] =
""
;
static PyObject *
WMWriter_WriteBuffer(WMWriterObject *self, PyObject *args)
{
	BYTE *pBuffer;
	DWORD dwInputNum;
	DWORD dwSampleSize;
	DWORD msec;
	DWORD dwFlags=0; // WM_SF_CLEANPOINT
	if (!PyArg_ParseTuple(args, "iiii|i", &dwInputNum, &msec, &pBuffer, &dwSampleSize, &dwFlags))
		return NULL;
	
	INSSBuffer *pSample=NULL;
	HRESULT hr = self->pI->AllocateSample(dwSampleSize,&pSample);
	if (FAILED(hr)){
		seterror("WMWriter_WriteBuffer:AllocateSample", hr);
		return NULL;
	}
	BYTE *pbsBuffer;
	DWORD cbBuffer;
	hr = pSample->GetBufferAndLength(&pbsBuffer,&cbBuffer);
	if (FAILED(hr)){
		pSample->Release();
		seterror("WMWriter_WriteBuffer:GetBufferAndLength", hr);
		return NULL;
	}
	CopyMemory(pbsBuffer,pBuffer,cbBuffer<dwSampleSize?cbBuffer:dwSampleSize);

	QWORD cnsec = QWORD(msec)*QWORD(10000);
	hr = self->pI->WriteSample(dwInputNum, cnsec, dwFlags, pSample);
	pSample->Release();
	if (FAILED(hr)){
		seterror("WMWriter_WriteBuffer:WriteSample", hr);
		return NULL;
	}
	Py_INCREF(Py_None);
	return Py_None;
}


static char WMWriter_QueryIWMWriterAdvanced__doc__[] =
""
;
static PyObject *
WMWriter_QueryIWMWriterAdvanced(WMWriterObject *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args, ""))
		return NULL;	
	HRESULT hr;
	WMWriterAdvancedObject *obj = newWMWriterAdvancedObject();	
	Py_BEGIN_ALLOW_THREADS
	hr = self->pI->QueryInterface(IID_IWMWriterAdvanced,(void**)&obj->pI);
	Py_END_ALLOW_THREADS
	if (FAILED(hr)){
		Py_DECREF(obj);
		seterror("WMWriter_QueryIWMWriterAdvanced", hr);
		return NULL;
	}
	return (PyObject*)obj;
}

static char WMWriter_QueryIUnknown__doc__[] =
""
;
static PyObject *
WMWriter_QueryIUnknown(WMWriterObject *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args, ""))
		return NULL;	
	HRESULT hr;
	UnknownObject *obj = newUnknownObject();	
	hr = self->pI->QueryInterface(IID_IUnknown,(void**)&obj->pI);
	if (FAILED(hr)){
		Py_DECREF(obj);
		seterror("WMWriter_QueryIUnknown", hr);
		return NULL;
	}
	return (PyObject*)obj;
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
	{"WriteDSSample", (PyCFunction)WMWriter_WriteDSSample, METH_VARARGS, WMWriter_WriteDSSample__doc__},
	{"WriteBuffer", (PyCFunction)WMWriter_WriteBuffer, METH_VARARGS, WMWriter_WriteBuffer__doc__},
	{"QueryIWMWriterAdvanced", (PyCFunction)WMWriter_QueryIWMWriterAdvanced, METH_VARARGS, WMWriter_QueryIWMWriterAdvanced__doc__},
	{"QueryIUnknown", (PyCFunction)WMWriter_QueryIUnknown, METH_VARARGS, WMWriter_QueryIUnknown__doc__},
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
// DDWMWriter object 

static char DDWMWriter_SetProfile__doc__[] =
""
;
static PyObject *
DDWMWriter_SetProfile(DDWMWriterObject *self, PyObject *args)
{
	WMProfileObject *obj;
	if (!PyArg_ParseTuple(args, "O!",&WMProfileType,&obj))
		return NULL;	
	HRESULT hr;
	Py_BEGIN_ALLOW_THREADS
	hr = self->pIWMWriter->SetProfile(obj->pI);
	Py_END_ALLOW_THREADS
	if (FAILED(hr)){
		seterror("DDWMWriter_SetProfile", hr);
		return NULL;
	}
	Py_INCREF(Py_None);
	return Py_None;
}


static char DDWMWriter_GetInputCount__doc__[] =
""
;
static PyObject *
DDWMWriter_GetInputCount(DDWMWriterObject *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args, ""))
		return NULL;	
	HRESULT hr;
	DWORD cInputs;
	Py_BEGIN_ALLOW_THREADS
	hr = self->pIWMWriter->GetInputCount(&cInputs);
	Py_END_ALLOW_THREADS
	if (FAILED(hr)){
		seterror("DDWMWriter_GetInputCount", hr);
		return NULL;
	}
	return Py_BuildValue("i",cInputs);
}

static char DDWMWriter_GetInputProps__doc__[] =
""
;
static PyObject *
DDWMWriter_GetInputProps(DDWMWriterObject *self, PyObject *args)
{
	DWORD dwInputNum;
	if (!PyArg_ParseTuple(args, "i",&dwInputNum))
		return NULL;	
	HRESULT hr;
	WMInputMediaPropsObject* obj = newWMInputMediaPropsObject();	
	Py_BEGIN_ALLOW_THREADS
	hr = self->pIWMWriter->GetInputProps(dwInputNum,&obj->pI);
	Py_END_ALLOW_THREADS
	if (FAILED(hr)){
		Py_DECREF(obj);
		seterror("DDWMWriter_GetInputProps", hr);
		return NULL;
	}
	return (PyObject*)obj;
}

static char DDWMWriter_SetInputProps__doc__[] =
""
;
static PyObject *
DDWMWriter_SetInputProps(DDWMWriterObject *self, PyObject *args)
{
	DWORD dwInputNum;
	WMInputMediaPropsObject *obj=NULL;
	if (!PyArg_ParseTuple(args, "i|O!",&dwInputNum,&WMInputMediaPropsType,&obj))
		return NULL;	
	HRESULT hr;
	Py_BEGIN_ALLOW_THREADS
	hr = self->pIWMWriter->SetInputProps(dwInputNum,(obj?obj->pI:NULL));
	Py_END_ALLOW_THREADS
	if (FAILED(hr)){
		seterror("DDWMWriter_SetInputProps", hr);
		return NULL;
	}
	Py_INCREF(Py_None);
	return Py_None;
}

static char DDWMWriter_SetOutputFilename__doc__[] =
""
;
static PyObject *
DDWMWriter_SetOutputFilename(DDWMWriterObject *self, PyObject *args)
{
	char *psz;
	if (!PyArg_ParseTuple(args, "s",&psz))
		return NULL;	
	HRESULT hr;
	WCHAR pwsz[MAX_PATH];
	MultiByteToWideChar(CP_ACP,0,psz,-1,pwsz,MAX_PATH);	
	Py_BEGIN_ALLOW_THREADS
	hr = self->pIWMWriter->SetOutputFilename(pwsz);
	Py_END_ALLOW_THREADS
	if (FAILED(hr)){
		seterror("DDWMWriter_SetOutputFilename", hr);
		return NULL;
	}
	Py_INCREF(Py_None);
	return Py_None;
}

static char DDWMWriter_BeginWriting__doc__[] =
""
;
static PyObject *
DDWMWriter_BeginWriting(DDWMWriterObject *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args, ""))
		return NULL;	
	HRESULT hr;
	Py_BEGIN_ALLOW_THREADS
	hr = self->pIWMWriter->BeginWriting();
	Py_END_ALLOW_THREADS
	if (FAILED(hr)){
		seterror("DDWMWriter_BeginWriting", hr);
		return NULL;
	}
	Py_INCREF(Py_None);
	return Py_None;
}

static char DDWMWriter_EndWriting__doc__[] =
""
;
static PyObject *
DDWMWriter_EndWriting(DDWMWriterObject *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args, ""))
		return NULL;	
	HRESULT hr;
	Py_BEGIN_ALLOW_THREADS
	hr = self->pIWMWriter->EndWriting();
	Py_END_ALLOW_THREADS
	if (FAILED(hr)){
		seterror("DDWMWriter_EndWriting", hr);
		return NULL;
	}
	Py_INCREF(Py_None);
	return Py_None;
}

static char DDWMWriter_Flush__doc__[] =
""
;
static PyObject *
DDWMWriter_Flush(DDWMWriterObject *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args, ""))
		return NULL;	
	HRESULT hr;
	Py_BEGIN_ALLOW_THREADS
	hr = self->pIWMWriter->Flush();
	Py_END_ALLOW_THREADS
	if (FAILED(hr)){
		seterror("DDWMWriter_Flush", hr);
		return NULL;
	}
	Py_INCREF(Py_None);
	return Py_None;
}


static char DDWMWriter_AllocateSample__doc__[] =
""
;
static PyObject *
DDWMWriter_AllocateSample(DDWMWriterObject *self, PyObject *args)
{
	DWORD dwSampleSize;
	if (!PyArg_ParseTuple(args, "i",&dwSampleSize))
		return NULL;	
	HRESULT hr;
	NSSBufferObject *obj = newNSSBufferObject();
	Py_BEGIN_ALLOW_THREADS
	hr = self->pIWMWriter->AllocateSample(dwSampleSize,&obj->pI);
	Py_END_ALLOW_THREADS
	if (FAILED(hr)){
		Py_DECREF(obj);
		seterror("DDWMWriter_AllocateSample", hr);
		return NULL;
	}
	return (PyObject*)obj;
}

static char DDWMWriter_WriteSample__doc__[] =
""
;
static PyObject *
DDWMWriter_WriteSample(DDWMWriterObject *self, PyObject *args)
{
	DWORD dwInputNum;
	NSSBufferObject *obj;
	LargeIntObject *linsSampleTime;
	DWORD dwFlags;
	if (!PyArg_ParseTuple(args, "iOiO!",&dwInputNum,&linsSampleTime,
		&dwFlags,&NSSBufferType,&obj))
		return NULL;	
	HRESULT hr;
	QWORD cnsSampleTime = linsSampleTime->ob_ival; // 100-ns units
	hr = self->pIWMWriter->WriteSample(dwInputNum, cnsSampleTime, dwFlags, obj->pI);
	if (FAILED(hr)){
		seterror("DDWMWriter_WriteSample", hr);
		return NULL;
	}
	Py_INCREF(Py_None);
	return Py_None;
}

static char DDWMWriter_WriteDSSample__doc__[] =
""
;
static PyObject *
DDWMWriter_WriteDSSample(DDWMWriterObject *self, PyObject *args)
{
	DWORD dwInputNum;
	PyObject *obj;
	DWORD dwFlags=0;
	if (!PyArg_ParseTuple(args, "iO|i",&dwInputNum,&obj,&dwFlags))
		return NULL;	
	
	typedef struct {
		PyObject_HEAD
		IMediaSample *pI;
	} MediaSampleObject;
	IMediaSample *pMediaSample = ((MediaSampleObject*)obj)->pI;

	REFERENCE_TIME tStart, tStop;
    HRESULT hr = pMediaSample->GetTime(&tStart,&tStop);
	if (FAILED(hr)){
		seterror("DDWMWriter_WriteDSSample:GetTime", hr);
		return NULL;
	}
	BYTE *pBuffer;
	hr = pMediaSample->GetPointer(&pBuffer);
	if (FAILED(hr)){
		seterror("DDWMWriter_WriteDSSample:GetPointer", hr);
		return NULL;
	}

	
	INSSBuffer *pINSSBuffer = NULL;
	hr = self->pIWMWriter->AllocateSample(pMediaSample->GetActualDataLength(),&pINSSBuffer);
	if (FAILED(hr)){
		seterror("DDWMWriter_WriteDSSample:AllocateSample", hr);
		return NULL;
	}

	BYTE *pbsBuffer;
	hr = pINSSBuffer->GetBuffer(&pbsBuffer);
	if (FAILED(hr)){
		seterror("DDWMWriter_WriteDSSample:GetBuffer", hr);
		return NULL;
	}
	CopyMemory(pbsBuffer,pBuffer,pMediaSample->GetActualDataLength());

	hr = self->pIWMWriter->WriteSample(dwInputNum, tStart, dwFlags, pINSSBuffer);
	pINSSBuffer->Release();
	
	if (FAILED(hr)){
		seterror("DDWMWriter_WriteDSSample:WriteSample", hr);
		return NULL;
	}
	Py_INCREF(Py_None);
	return Py_None;
}

static char DDWMWriter_WriteDSAudioSample__doc__[] =
""
;
static PyObject *
DDWMWriter_WriteDSAudioSample(DDWMWriterObject *self, PyObject *args)
{
	PyObject *obj;
	DWORD msecOffset=0;
	DWORD dwFlags=0;
	if (!PyArg_ParseTuple(args, "O|ii",&obj, &msecOffset, &dwFlags))
		return NULL;	
	
	typedef struct {
		PyObject_HEAD
		IMediaSample *pI;
	} MediaSampleObject;
	IMediaSample *pMediaSample = ((MediaSampleObject*)obj)->pI;

	REFERENCE_TIME tStart, tStop;
    HRESULT hr = pMediaSample->GetTime(&tStart,&tStop);
	if (FAILED(hr)){
		seterror("DDWMWriter_WriteDSAudioSample:GetTime", hr);
		return NULL;
	}
	BYTE *pBuffer;
	hr = pMediaSample->GetPointer(&pBuffer);
	if (FAILED(hr)){
		seterror("WriteDSAudioSample:GetPointer", hr);
		return NULL;
	}

	
	INSSBuffer *pINSSBuffer = NULL;
	hr = self->pIWMWriter->AllocateSample(pMediaSample->GetActualDataLength(),&pINSSBuffer);
	if (FAILED(hr)){
		seterror("WriteDSAudioSample:AllocateSample", hr);
		return NULL;
	}

	BYTE *pbsBuffer;
	hr = pINSSBuffer->GetBuffer(&pbsBuffer);
	if (FAILED(hr)){
		seterror("WriteDSAudioSample:GetBuffer", hr);
		return NULL;
	}
	CopyMemory(pbsBuffer,pBuffer,pMediaSample->GetActualDataLength());

	if(msecOffset>0)
		{
		QWORD cnsecOffset = QWORD(msecOffset)*QWORD(10000);
		tStart += cnsecOffset;
		}
	hr = self->pIWMWriter->WriteSample(self->dwAudioInputNum, tStart, dwFlags, pINSSBuffer);
	pINSSBuffer->Release();
	
	if (FAILED(hr)){
		seterror("DDWMWriter_WriteDSAudioSample:WriteSample", hr);
		return NULL;
	}
	Py_INCREF(Py_None);
	return Py_None;
}

static char DDWMWriter_QueryIWMWriterAdvanced__doc__[] =
""
;
static PyObject *
DDWMWriter_QueryIWMWriterAdvanced(DDWMWriterObject *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args, ""))
		return NULL;	
	HRESULT hr;
	WMWriterAdvancedObject *obj = newWMWriterAdvancedObject();	
	Py_BEGIN_ALLOW_THREADS
	hr = self->pIWMWriter->QueryInterface(IID_IWMWriterAdvanced,(void**)&obj->pI);
	Py_END_ALLOW_THREADS
	if (FAILED(hr)){
		Py_DECREF(obj);
		seterror("DDWMWriter_QueryIDDWMWriterAdvanced", hr);
		return NULL;
	}
	return (PyObject*)obj;
}

static char DDWMWriter_QueryIUnknown__doc__[] =
""
;
static PyObject *
DDWMWriter_QueryIUnknown(DDWMWriterObject *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args, ""))
		return NULL;	
	HRESULT hr;
	UnknownObject *obj = newUnknownObject();	
	hr = self->pIWMWriter->QueryInterface(IID_IUnknown,(void**)&obj->pI);
	if (FAILED(hr)){
		Py_DECREF(obj);
		seterror("DDWMWriter_QueryIUnknown", hr);
		return NULL;
	}
	return (PyObject*)obj;
}


static char DDWMWriter_SetVideoFormat__doc__[] =
""
;
static PyObject *
DDWMWriter_SetVideoFormat(DDWMWriterObject *self, PyObject *args)
{
	WMMediaTypeObject *obj;
	if (!PyArg_ParseTuple(args, "O!", &WMMediaTypeType, &obj))
		return NULL;	
	if(!self->pIVideoInputProps){
		seterror("Videoless profile");
		return NULL;	
	}

	HRESULT hr = self->pIVideoInputProps->SetMediaType(obj->pMediaType);
	if(FAILED(hr))
		{
		seterror("SetMediaType",hr);
		return NULL;
		}
	hr = self->pIWMWriter->SetInputProps(self->dwVideoInputNum, self->pIVideoInputProps);
	if(FAILED(hr))
		{
		seterror("SetInputProps",hr);
		return NULL;
		}
	Py_INCREF(Py_None);
	return Py_None;
	}

static char DDWMWriter_SetAudioFormat__doc__[] =
""
;
static PyObject *
DDWMWriter_SetAudioFormat(DDWMWriterObject *self, PyObject *args)
{
	WMMediaTypeObject *obj;
	if (!PyArg_ParseTuple(args, "O!", &WMMediaTypeType, &obj))
		return NULL;	
	if(!self->pIAudioInputProps){
		seterror("Audioless profile");
		return NULL;	
	}
	HRESULT hr = self->pIAudioInputProps->SetMediaType(obj->pMediaType);
	if(FAILED(hr))
		{
		seterror("SetMediaType",hr);
		return NULL;
		}
	hr = self->pIWMWriter->SetInputProps(self->dwAudioInputNum, self->pIAudioInputProps);
	if(FAILED(hr))
		{
		seterror("SetInputProps",hr);
		return NULL;
		}
	Py_INCREF(Py_None);
	return Py_None;
	}

static char DDWMWriter_SetDSAudioFormat__doc__[] =
""
;
static PyObject *
DDWMWriter_SetDSAudioFormat(DDWMWriterObject *self, PyObject *args)
{
	PyObject *obj;
	if (!PyArg_ParseTuple(args,"O",&obj)) 
		return NULL;

	typedef struct {
		PyObject_HEAD
		const CMediaType *pmt;
	} MediaTypeObject;
	const CMediaType *pmt = ((MediaTypeObject*)obj)->pmt;

	WM_MEDIA_TYPE mt;
	WM_MEDIA_TYPE *pType = &mt;
    pType->majortype = *pmt->Type();
    pType->subtype =  *pmt->Subtype();
    pType->bFixedSizeSamples = pmt->IsFixedSize();
    pType->bTemporalCompression = pmt->IsTemporalCompressed();
    pType->lSampleSize = pmt->GetSampleSize();
    pType->formattype = *pmt->FormatType();
    pType->pUnk = NULL;
    pType->cbFormat = pmt->FormatLength();
	pType->pbFormat = pmt->Format();
		
	HRESULT hr = self->pIAudioInputProps->SetMediaType(pType);
	if(FAILED(hr))
		{
		seterror("DDWMWriter_SetDSAudioFormat:SetMediaType",hr);
		return NULL;
		}
	hr = self->pIWMWriter->SetInputProps(self->dwAudioInputNum, self->pIAudioInputProps);
	if(FAILED(hr))
		{
		seterror("DDWMWriter_SetDSAudioFormat:SetInputProps",hr);
		return NULL;
		}
	Py_INCREF(Py_None);
	return Py_None;
	}

static char DDWMWriter_AllocateDDSample__doc__[] =
""
;
static PyObject *
DDWMWriter_AllocateDDSample(DDWMWriterObject *self, PyObject *args)
{
	PyObject *obj;
	if (!PyArg_ParseTuple(args, "O", &obj))
		return NULL;

	IDirectDrawSurface *surf = (IDirectDrawSurface *)((UnknownObject*)obj)->pI;
	DDSURFACEDESC desc;
	ZeroMemory(&desc, sizeof(desc));
	desc.dwSize=sizeof(desc);
	HRESULT hr;
	hr = surf->Lock(0,&desc,DDLOCK_WAIT | DDLOCK_READONLY, 0);
	if (FAILED(hr)){
		seterror("DDWMWriter_AllocateDDSample:Lock", hr);
		return NULL;
	}	

	BYTE *pBuffer=(BYTE*)desc.lpSurface;
	int nrows = int(desc.dwHeight);
	int pitch = int(desc.lPitch);

	NSSBufferObject *bufobj = newNSSBufferObject();
	hr = self->pIWMWriter->AllocateSample(nrows*pitch,&bufobj->pI);
	if (FAILED(hr)){
		surf->Unlock(0);
		Py_DECREF(bufobj);
		seterror("DDWMWriter_AllocateDDSample:AllocateSample", hr);
		return NULL;
	}

	BYTE *pbsBuffer;
	bufobj->pI->GetBuffer(&pbsBuffer);
	for(int row=nrows-1;row>=0;row--){
		CopyMemory(pbsBuffer, pBuffer + row*pitch, pitch);
		pbsBuffer += pitch;
	}
	surf->Unlock(0);
	
	return (PyObject*)bufobj;
}

static char DDWMWriter_SetDDSample__doc__[] =
""
;
static PyObject *
DDWMWriter_SetDDSample(DDWMWriterObject *self, PyObject *args)
{
	PyObject *obj;
	NSSBufferObject *bufobj;
	if (!PyArg_ParseTuple(args, "OO!", &obj,&NSSBufferType,&bufobj))
		return NULL;

	IDirectDrawSurface *surf = (IDirectDrawSurface *)((UnknownObject*)obj)->pI;
	DDSURFACEDESC desc;
	ZeroMemory(&desc, sizeof(desc));
	desc.dwSize=sizeof(desc);
	HRESULT hr;
	hr = surf->Lock(0,&desc,DDLOCK_WAIT | DDLOCK_READONLY, 0);
	if (FAILED(hr)){
		seterror("DDWMWriter_SetDDSample:Lock", hr);
		return NULL;
	}	

	BYTE *pBuffer=(BYTE*)desc.lpSurface;
	int nrows = int(desc.dwHeight);
	int pitch = int(desc.lPitch);
	BYTE *pbsBuffer;
	bufobj->pI->GetBuffer(&pbsBuffer);
	for(int row=nrows-1;row>=0;row--){
		CopyMemory(pbsBuffer, pBuffer + row*pitch, pitch);
		pbsBuffer += pitch;
	}
	surf->Unlock(0);
	Py_INCREF(Py_None);
	return Py_None;	
}

static char DDWMWriter_WriteVideoSample__doc__[] =
""
;
static PyObject *
DDWMWriter_WriteVideoSample(DDWMWriterObject *self, PyObject *args)
{
	DWORD msec;
	NSSBufferObject *obj;
	DWORD dwFlags=0; // WM_SF_CLEANPOINT
	if (!PyArg_ParseTuple(args, "iO!|i", &msec, &NSSBufferType, &obj, &dwFlags))
		return NULL;

	HRESULT hr;
	QWORD cnsec = QWORD(msec)*QWORD(10000);
	hr = self->pIWMWriter->WriteSample(self->dwVideoInputNum, cnsec, dwFlags, obj->pI);
	if (FAILED(hr)){
		seterror("DDWMWriter_WriteVideoSample", hr);
		return NULL;
	}
	Py_INCREF(Py_None);
	return Py_None;
}


static struct PyMethodDef DDWMWriter_methods[] = {
	{"SetProfile", (PyCFunction)DDWMWriter_SetProfile, METH_VARARGS, DDWMWriter_SetProfile__doc__},
	{"GetInputCount", (PyCFunction)DDWMWriter_GetInputCount, METH_VARARGS, DDWMWriter_GetInputCount__doc__},
	{"GetInputProps", (PyCFunction)DDWMWriter_GetInputProps, METH_VARARGS, DDWMWriter_GetInputProps__doc__},
	{"SetInputProps", (PyCFunction)DDWMWriter_SetInputProps, METH_VARARGS, DDWMWriter_SetInputProps__doc__},
	{"SetOutputFilename", (PyCFunction)DDWMWriter_SetOutputFilename, METH_VARARGS, DDWMWriter_SetOutputFilename__doc__},
	{"BeginWriting", (PyCFunction)DDWMWriter_BeginWriting, METH_VARARGS, DDWMWriter_BeginWriting__doc__},
	{"EndWriting", (PyCFunction)DDWMWriter_EndWriting, METH_VARARGS, DDWMWriter_EndWriting__doc__},
	{"Flush", (PyCFunction)DDWMWriter_Flush, METH_VARARGS, DDWMWriter_Flush__doc__},
	{"AllocateSample", (PyCFunction)DDWMWriter_AllocateSample, METH_VARARGS, DDWMWriter_AllocateSample__doc__},
	{"WriteSample", (PyCFunction)DDWMWriter_WriteSample, METH_VARARGS, DDWMWriter_WriteSample__doc__},
	{"WriteDSSample", (PyCFunction)DDWMWriter_WriteDSSample, METH_VARARGS, DDWMWriter_WriteDSSample__doc__},
	{"WriteDSAudioSample", (PyCFunction)DDWMWriter_WriteDSAudioSample, METH_VARARGS, DDWMWriter_WriteDSAudioSample__doc__},
	{"QueryIWMWriterAdvanced", (PyCFunction)DDWMWriter_QueryIWMWriterAdvanced, METH_VARARGS, DDWMWriter_QueryIWMWriterAdvanced__doc__},
	{"QueryIUnknown", (PyCFunction)DDWMWriter_QueryIUnknown, METH_VARARGS, DDWMWriter_QueryIUnknown__doc__},
	{"SetVideoFormat", (PyCFunction)DDWMWriter_SetVideoFormat, METH_VARARGS, DDWMWriter_SetVideoFormat__doc__},
	{"SetAudioFormat", (PyCFunction)DDWMWriter_SetAudioFormat, METH_VARARGS, DDWMWriter_SetAudioFormat__doc__},
	{"SetDSAudioFormat", (PyCFunction)DDWMWriter_SetDSAudioFormat, METH_VARARGS, DDWMWriter_SetDSAudioFormat__doc__},
	{"AllocateDDSample", (PyCFunction)DDWMWriter_AllocateDDSample, METH_VARARGS, DDWMWriter_AllocateDDSample__doc__},
	{"SetDDSample", (PyCFunction)DDWMWriter_SetDDSample, METH_VARARGS, DDWMWriter_SetDDSample__doc__},
	{"WriteVideoSample", (PyCFunction)DDWMWriter_WriteVideoSample, METH_VARARGS, DDWMWriter_WriteVideoSample__doc__},
	{NULL, (PyCFunction)NULL, 0, NULL}		/* sentinel */
};

static void
DDWMWriter_dealloc(DDWMWriterObject *self)
{
	/* XXXX Add your own cleanup code here */
	RELEASE(self->pIAudioInputProps);
	RELEASE(self->pIVideoInputProps);
	RELEASE(self->pIWMWriter);
	PyMem_DEL(self);
}

static PyObject *
DDWMWriter_getattr(DDWMWriterObject *self, char *name)
{
	/* XXXX Add your own getattr code here */
	return Py_FindMethod(DDWMWriter_methods, (PyObject *)self, name);
}

static char DDWMWriterType__doc__[] =
""
;

static PyTypeObject DDWMWriterType = {
	PyObject_HEAD_INIT(&PyType_Type)
	0,				/*ob_size*/
	"DDWMWriter",			/*tp_name*/
	sizeof(DDWMWriterObject),		/*tp_basicsize*/
	0,				/*tp_itemsize*/
	/* methods */
	(destructor)DDWMWriter_dealloc,	/*tp_dealloc*/
	(printfunc)0,		/*tp_print*/
	(getattrfunc)DDWMWriter_getattr,	/*tp_getattr*/
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
	DDWMWriterType__doc__ /* Documentation string */
};

// End of code for DDWMWriter object 
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

static char WMProfileManager_CreateEmptyProfile__doc__[] =
""
;
static PyObject *
WMProfileManager_CreateEmptyProfile(WMProfileManagerObject *self, PyObject *args)
{
	WMT_VERSION dwVersion = WMT_VER_7_0;
	if (!PyArg_ParseTuple(args,"|i",&dwVersion))
		return NULL;
	
	WMProfileObject *obj = newWMProfileObject();
	if (obj == NULL) return NULL;
	HRESULT hr;
	Py_BEGIN_ALLOW_THREADS
	hr = self->pI->CreateEmptyProfile(dwVersion,&obj->pI);
	Py_END_ALLOW_THREADS
	if (FAILED(hr)){
		Py_DECREF(obj);
		seterror("WMProfileManager_CreateEmptyProfile", hr);
		return NULL;
	}
	return (PyObject*)obj;
}


static char WMProfileManager_QueryIWMCodecInfo__doc__[] =
""
;
static PyObject *
WMProfileManager_QueryIWMCodecInfo(WMProfileManagerObject *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args,""))
		return NULL;
	
	WMCodecInfoObject *obj = newWMCodecInfoObject();
	if (obj == NULL) return NULL;
	
	HRESULT hr=self->pI->QueryInterface(IID_IWMCodecInfo, (void **)&obj->pI);
	if (FAILED(hr)){
		Py_DECREF(obj);
		seterror("WMProfileManager_QueryIWMCodecInfo", hr);
		return NULL;
	}
	return (PyObject*)obj;
}

static char WMProfileManager_SetSystemProfileVersion__doc__[] =
""
;
static PyObject *
WMProfileManager_SetSystemProfileVersion(WMProfileManagerObject *self, PyObject *args)
{
	WMT_VERSION dwVersion = WMT_VER_7_0;
	if (!PyArg_ParseTuple(args,"|i",&dwVersion))
		return NULL;

	IWMProfileManager2 *pI=NULL;
	HRESULT hr=self->pI->QueryInterface(IID_IWMProfileManager2, (void **)&pI);
	if (FAILED(hr)){
		seterror("WMProfileManager_QueryIWMProfileManager2", hr);
		return NULL;
	}
    hr = pI->SetSystemProfileVersion(dwVersion);
	if (FAILED(hr)){
		pI->Release();
		seterror("WMProfileManager_SetSystemProfileVersion", hr);
		return NULL;
	}
	pI->Release();
	Py_INCREF(Py_None);
	return Py_None;	
}

static struct PyMethodDef WMProfileManager_methods[] = {
	{"GetSystemProfileCount", (PyCFunction)WMProfileManager_GetSystemProfileCount, METH_VARARGS, WMProfileManager_GetSystemProfileCount__doc__},
	{"LoadSystemProfile", (PyCFunction)WMProfileManager_LoadSystemProfile, METH_VARARGS, WMProfileManager_LoadSystemProfile__doc__},
	{"CreateEmptyProfile", (PyCFunction)WMProfileManager_CreateEmptyProfile, METH_VARARGS, WMProfileManager_CreateEmptyProfile__doc__},
	{"QueryIWMCodecInfo", (PyCFunction)WMProfileManager_QueryIWMCodecInfo, METH_VARARGS, WMProfileManager_QueryIWMCodecInfo__doc__},
	{"SetSystemProfileVersion", (PyCFunction)WMProfileManager_SetSystemProfileVersion, METH_VARARGS, WMProfileManager_SetSystemProfileVersion__doc__},
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

static char WMProfile_GetVersion__doc__[] =
""
;
static PyObject *
WMProfile_GetVersion(WMProfileObject *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args,"")) 
		return NULL;
	HRESULT hr;
    WMT_VERSION dwVersion;
	Py_BEGIN_ALLOW_THREADS
	hr = self->pI->GetVersion(&dwVersion);
	Py_END_ALLOW_THREADS
	if (FAILED(hr)) {
		seterror("WMProfile_GetVersion", hr);
		return NULL;
	}
	return Py_BuildValue("i",dwVersion);	
}
       
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
	PyObject *obj = PyObjectFromWideChar(pwszName,cchName);
	delete []pwszName;
	return obj;
}
        
static char WMProfile_SetName__doc__[] =
""
;
static PyObject *
WMProfile_SetName(WMProfileObject *self, PyObject *args)
{
	char *pszName;
	if (!PyArg_ParseTuple(args,"s",&pszName)) 
		return NULL;
	HRESULT hr;
	int l=strlen(pszName);
	WCHAR *pwszName = new WCHAR[l+1];
	MultiByteToWideChar(CP_ACP,0,pszName,-1,pwszName,l+1);	
	hr = self->pI->SetName(pwszName);
	if (FAILED(hr)) {
		if(pwszName) delete [] pwszName;
		seterror("WMProfile_SetName", hr);
		return NULL;
	}
	if(pwszName) delete [] pwszName;
	Py_INCREF(Py_None);
	return Py_None;
}
        
static char WMProfile_GetDescription__doc__[] =
""
;
static PyObject *
WMProfile_GetDescription(WMProfileObject *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args,"")) 
		return NULL;
	HRESULT hr;
    WCHAR wszName[512];
    DWORD cchName = 512;
	Py_BEGIN_ALLOW_THREADS
	hr = self->pI->GetDescription(wszName, &cchName);
	Py_END_ALLOW_THREADS
	if (FAILED(hr)) {
		seterror("WMProfile_GetDescription", hr);
		return NULL;
	}
	return PyObjectFromWideChar(wszName,cchName);
}
       
static char WMProfile_SetDescription__doc__[] =
""
;
static PyObject *
WMProfile_SetDescription(WMProfileObject *self, PyObject *args)
{
	char *psz;
	if (!PyArg_ParseTuple(args,"s",&psz)) 
		return NULL;
	HRESULT hr;
	int l=strlen(psz);
	WCHAR *pwsz = new WCHAR[l+1];
	MultiByteToWideChar(CP_ACP,0,psz,-1,pwsz,l+1);	
	hr = self->pI->SetDescription(pwsz);
	if (FAILED(hr)) {
		if(pwsz) delete [] pwsz;
		seterror("WMProfile_SetDescription", hr);
		return NULL;
	}
	if(pwsz) delete [] pwsz;
	Py_INCREF(Py_None);
	return Py_None;
}
        
static char WMProfile_GetStreamCount__doc__[] =
""
;
static PyObject *
WMProfile_GetStreamCount(WMProfileObject *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args,"")) 
		return NULL;
	HRESULT hr;
    DWORD cStreams;
	Py_BEGIN_ALLOW_THREADS
	hr = self->pI->GetStreamCount(&cStreams);
	Py_END_ALLOW_THREADS
	if (FAILED(hr)) {
		seterror("WMProfile_GetStreamCount", hr);
		return NULL;
	}
	return Py_BuildValue("i",cStreams);	
}
        
static char WMProfile_GetStream__doc__[] =
""
;
static PyObject *
WMProfile_GetStream(WMProfileObject *self, PyObject *args)
{
	DWORD dwStreamIndex;
	if (!PyArg_ParseTuple(args,"i",&dwStreamIndex)) 
		return NULL;
	HRESULT hr;
	WMStreamConfigObject *obj = newWMStreamConfigObject();
	Py_BEGIN_ALLOW_THREADS
	hr = self->pI->GetStream(dwStreamIndex,&obj->pI);
	Py_END_ALLOW_THREADS
	if (FAILED(hr)) {
		Py_DECREF(obj);
		seterror("WMProfile_GetStream", hr);
		return NULL;
	}
	return (PyObject*)obj;	
}
        
static char WMProfile_GetStreamByNumber__doc__[] =
""
;
static PyObject *
WMProfile_GetStreamByNumber(WMProfileObject *self, PyObject *args)
{
	DWORD dwStreamNum;
	if (!PyArg_ParseTuple(args,"i",&dwStreamNum)) 
		return NULL;
	HRESULT hr;
	WMStreamConfigObject *obj = newWMStreamConfigObject();
	Py_BEGIN_ALLOW_THREADS
	hr = self->pI->GetStreamByNumber(WORD(dwStreamNum),&obj->pI);
	Py_END_ALLOW_THREADS
	if (FAILED(hr)) {
		Py_DECREF(obj);
		seterror("WMProfile_GetStreamByNumber", hr);
		return NULL;
	}
	return (PyObject*)obj;	
}
        
static char WMProfile_RemoveStream__doc__[] =
""
;
static PyObject *
WMProfile_RemoveStream(WMProfileObject *self, PyObject *args)
{
	WMStreamConfigObject *obj;
	if (!PyArg_ParseTuple(args,"O!",&WMStreamConfigType,&obj)) 
		return NULL;
	HRESULT hr;
	hr = self->pI->RemoveStream(obj->pI);
	if (FAILED(hr)) {
		seterror("WMProfile_RemoveStream", hr);
		return NULL;
	}
	Py_INCREF(Py_None);
	return Py_None;
}
       
static char WMProfile_RemoveStreamByNumber__doc__[] =
""
;
static PyObject *
WMProfile_RemoveStreamByNumber(WMProfileObject *self, PyObject *args)
{
	DWORD dwStreamNum;
	if (!PyArg_ParseTuple(args,"i",&dwStreamNum)) 
		return NULL;
	HRESULT hr;
	hr = self->pI->RemoveStreamByNumber(WORD(dwStreamNum));
	if (FAILED(hr)) {
		seterror("WMProfile_RemoveStreamByNumber", hr);
		return NULL;
	}
	Py_INCREF(Py_None);
	return Py_None;
}
        
static char WMProfile_AddStream__doc__[] =
""
;
static PyObject *
WMProfile_AddStream(WMProfileObject *self, PyObject *args)
{
	WMStreamConfigObject *obj;
	if (!PyArg_ParseTuple(args,"O!",&WMStreamConfigType,&obj)) 
		return NULL;
	HRESULT hr;
	hr = self->pI->AddStream(obj->pI);
	if (FAILED(hr)) {
		seterror("WMProfile_AddStream", hr);
		return NULL;
	}
	Py_INCREF(Py_None);
	return Py_None;
}
        
static char WMProfile_ReconfigStream__doc__[] =
""
;
static PyObject *
WMProfile_ReconfigStream(WMProfileObject *self, PyObject *args)
{
	WMStreamConfigObject *obj;
	if (!PyArg_ParseTuple(args,"O!",&WMStreamConfigType,&obj)) 
		return NULL;
	HRESULT hr;
	hr = self->pI->ReconfigStream(obj->pI);
	if (FAILED(hr)) {
		seterror("WMProfile_ReconfigStream", hr);
		return NULL;
	}
	Py_INCREF(Py_None);
	return Py_None;
}
        
static char WMProfile_CreateNewStream__doc__[] =
""
;
static PyObject *
WMProfile_CreateNewStream(WMProfileObject *self, PyObject *args)
{
	GUIDObject *guidobj;
	if (!PyArg_ParseTuple(args,"O!",&GUIDType,&guidobj)) 
		return NULL;
	HRESULT hr;
	WMStreamConfigObject *obj = newWMStreamConfigObject();
	Py_BEGIN_ALLOW_THREADS
	hr = self->pI->CreateNewStream(guidobj->guid,&obj->pI);
	Py_END_ALLOW_THREADS
	if (FAILED(hr)) {
		Py_DECREF(obj);
		seterror("WMProfile_CreateNewStream", hr);
		return NULL;
	}
	return (PyObject*)obj;	
}
			
static char WMProfile_GetMutualExclusionCount__doc__[] =
""
;
static PyObject *
WMProfile_GetMutualExclusionCount(WMProfileObject *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args,"")) 
		return NULL;
	HRESULT hr;
    DWORD cME;
	Py_BEGIN_ALLOW_THREADS
	hr = self->pI->GetMutualExclusionCount(&cME);
	Py_END_ALLOW_THREADS
	if (FAILED(hr)) {
		seterror("WMProfile_GetMutualExclusionCount", hr);
		return NULL;
	}
	return Py_BuildValue("i",cME);	
}
        
static char WMProfile_GetMutualExclusion__doc__[] =
""
;
static PyObject *
WMProfile_GetMutualExclusion(WMProfileObject *self, PyObject *args)
{
	DWORD dwMEIndex;
	if (!PyArg_ParseTuple(args,"i",&dwMEIndex)) 
		return NULL;
	HRESULT hr;
    WMMutualExclusionObject *obj = newWMMutualExclusionObject();
	Py_BEGIN_ALLOW_THREADS
	hr = self->pI->GetMutualExclusion(dwMEIndex,&obj->pI);
	Py_END_ALLOW_THREADS
	if (FAILED(hr)) {
		Py_DECREF(obj);
		seterror("WMProfile_GetMutualExclusion", hr);
		return NULL;
	}
	return (PyObject*)obj;	
}
        
static char WMProfile_RemoveMutualExclusion__doc__[] =
""
;
static PyObject *
WMProfile_RemoveMutualExclusion(WMProfileObject *self, PyObject *args)
{
	WMMutualExclusionObject *obj;
	if (!PyArg_ParseTuple(args,"O!",&WMMutualExclusionType,&obj)) 
		return NULL;
	HRESULT hr;
	hr = self->pI->RemoveMutualExclusion(obj->pI);
	if (FAILED(hr)) {
		seterror("WMProfile_RemoveMutualExclusion", hr);
		return NULL;
	}
	Py_INCREF(Py_None);
	return Py_None;
}
        
static char WMProfile_AddMutualExclusion__doc__[] =
""
;
static PyObject *
WMProfile_AddMutualExclusion(WMProfileObject *self, PyObject *args)
{
	WMMutualExclusionObject *obj;
	if (!PyArg_ParseTuple(args,"O!",&WMMutualExclusionType,&obj)) 
		return NULL;
	HRESULT hr;
	hr = self->pI->AddMutualExclusion(obj->pI);
	if (FAILED(hr)) {
		seterror("WMProfile_AddMutualExclusion", hr);
		return NULL;
	}
	Py_INCREF(Py_None);
	return Py_None;
}
        
static char WMProfile_CreateNewMutualExclusion__doc__[] =
""
;
static PyObject *
WMProfile_CreateNewMutualExclusion(WMProfileObject *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args,""))
		return NULL;
	HRESULT hr;
	WMMutualExclusionObject *obj = newWMMutualExclusionObject();
	hr = self->pI->CreateNewMutualExclusion(&obj->pI);
	if (FAILED(hr)) {
		Py_DECREF(obj);
		seterror("WMProfile_AddMutualExclusion", hr);
		return NULL;
	}
	return (PyObject*)obj;
}
       

static struct PyMethodDef WMProfile_methods[] = {
	{"GetVersion", (PyCFunction)WMProfile_GetVersion, METH_VARARGS, WMProfile_GetVersion__doc__},
	{"GetName", (PyCFunction)WMProfile_GetName, METH_VARARGS, WMProfile_GetName__doc__},
	{"SetName", (PyCFunction)WMProfile_SetName, METH_VARARGS, WMProfile_SetName__doc__},
	{"GetDescription", (PyCFunction)WMProfile_GetDescription, METH_VARARGS, WMProfile_GetDescription__doc__},
	{"SetDescription", (PyCFunction)WMProfile_SetDescription, METH_VARARGS, WMProfile_SetDescription__doc__},
	{"GetStreamCount", (PyCFunction)WMProfile_GetStreamCount, METH_VARARGS, WMProfile_GetStreamCount__doc__},
	{"GetStream", (PyCFunction)WMProfile_GetStream, METH_VARARGS, WMProfile_GetStream__doc__},
	{"GetStreamByNumber", (PyCFunction)WMProfile_GetStreamByNumber, METH_VARARGS, WMProfile_GetStreamByNumber__doc__},
	{"RemoveStream", (PyCFunction)WMProfile_RemoveStream, METH_VARARGS, WMProfile_RemoveStream__doc__},
	{"RemoveStreamByNumber", (PyCFunction)WMProfile_RemoveStreamByNumber, METH_VARARGS, WMProfile_RemoveStreamByNumber__doc__},
	{"AddStream", (PyCFunction)WMProfile_AddStream, METH_VARARGS, WMProfile_AddStream__doc__},
	{"ReconfigStream", (PyCFunction)WMProfile_ReconfigStream, METH_VARARGS, WMProfile_ReconfigStream__doc__},
	{"CreateNewStream", (PyCFunction)WMProfile_CreateNewStream, METH_VARARGS, WMProfile_CreateNewStream__doc__},
	{"GetMutualExclusionCount", (PyCFunction)WMProfile_GetMutualExclusionCount, METH_VARARGS, WMProfile_GetMutualExclusionCount__doc__},
	{"GetMutualExclusion", (PyCFunction)WMProfile_GetMutualExclusion, METH_VARARGS, WMProfile_GetMutualExclusion__doc__},
	{"RemoveMutualExclusion", (PyCFunction)WMProfile_RemoveMutualExclusion, METH_VARARGS, WMProfile_RemoveMutualExclusion__doc__},
	{"AddMutualExclusion", (PyCFunction)WMProfile_AddMutualExclusion, METH_VARARGS, WMProfile_AddMutualExclusion__doc__},
	{"CreateNewMutualExclusion", (PyCFunction)WMProfile_CreateNewMutualExclusion, METH_VARARGS, WMProfile_CreateNewMutualExclusion__doc__},
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
// WMMediaProps object 

static char WMMediaProps_GetType__doc__[] =
""
;
static PyObject *
WMMediaProps_GetType(WMMediaPropsObject *self, PyObject *args)
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
		seterror("WMMediaProps_GetType", hr);
		return NULL;
	}
	return (PyObject*)obj;
}


static char WMMediaProps_GetMediaType__doc__[] =
""
;
static PyObject *
WMMediaProps_GetMediaType(WMMediaPropsObject *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args,"")) 
		return NULL;
	HRESULT hr;
	WMMediaTypeObject *obj = newWMMediaTypeObject();
	Py_BEGIN_ALLOW_THREADS
	hr = self->pI->GetMediaType(obj->pMediaType,&obj->cbBuffer);
	Py_END_ALLOW_THREADS	
	if (FAILED(hr)) {
		Py_DECREF(obj);		
		seterror("WMMediaProps_GetMediaType", hr);
		return NULL;
	}
	return (PyObject*)obj;
}
	
static char WMMediaProps_SetMediaType__doc__[] =
""
;
static PyObject *
WMMediaProps_SetMediaType(WMMediaPropsObject *self, PyObject *args)
{
	WMMediaTypeObject *obj;
	if (!PyArg_ParseTuple(args,"O!",&WMMediaTypeType,&obj)) 
		return NULL;
	HRESULT hr;
	Py_BEGIN_ALLOW_THREADS
	hr = self->pI->SetMediaType(obj->pMediaType);
	Py_END_ALLOW_THREADS	
	if (FAILED(hr)) {
		seterror("WMMediaProps_SetMediaType", hr);
		return NULL;
	}
	Py_INCREF(Py_None);
	return Py_None;	
}

static struct PyMethodDef WMMediaProps_methods[] = {
	{"GetType", (PyCFunction)WMMediaProps_GetType, METH_VARARGS, WMMediaProps_GetType__doc__},
	{"GetMediaType", (PyCFunction)WMMediaProps_GetMediaType, METH_VARARGS, WMMediaProps_GetMediaType__doc__},
	{"SetMediaType", (PyCFunction)WMMediaProps_SetMediaType, METH_VARARGS, WMMediaProps_SetMediaType__doc__},
	{NULL, (PyCFunction)NULL, 0, NULL}		/* sentinel */
};

static void
WMMediaProps_dealloc(WMMediaPropsObject *self)
{
	/* XXXX Add your own cleanup code here */
	RELEASE(self->pI);
	PyMem_DEL(self);
}

static PyObject *
WMMediaProps_getattr(WMMediaPropsObject *self, char *name)
{
	/* XXXX Add your own getattr code here */
	return Py_FindMethod(WMMediaProps_methods, (PyObject *)self, name);
}

static char WMMediaPropsType__doc__[] =
""
;

static PyTypeObject WMMediaPropsType = {
	PyObject_HEAD_INIT(&PyType_Type)
	0,				/*ob_size*/
	"WMMediaProps",			/*tp_name*/
	sizeof(WMMediaPropsObject),		/*tp_basicsize*/
	0,				/*tp_itemsize*/
	/* methods */
	(destructor)WMMediaProps_dealloc,	/*tp_dealloc*/
	(printfunc)0,		/*tp_print*/
	(getattrfunc)WMMediaProps_getattr,	/*tp_getattr*/
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
	WMMediaPropsType__doc__ /* Documentation string */
};

// End of code for WMMediaProps object 
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
	WMMediaTypeObject *obj = newWMMediaTypeObject();
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
	WMMediaTypeObject *obj;
	if (!PyArg_ParseTuple(args,"O!",&WMMediaTypeType,&obj)) 
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

static char WMInputMediaProps_SetDSMediaType__doc__[] =
""
;
static PyObject *
WMInputMediaProps_SetDSMediaType(WMInputMediaPropsObject *self, PyObject *args)
{
	PyObject *obj;
	if (!PyArg_ParseTuple(args,"O",&obj)) 
		return NULL;

	typedef struct {
		PyObject_HEAD
		const CMediaType *pmt;
	} MediaTypeObject;
	const CMediaType *pmt = ((MediaTypeObject*)obj)->pmt;

	WM_MEDIA_TYPE mt;
	WM_MEDIA_TYPE *pType = &mt;
    pType->majortype = *pmt->Type();
    pType->subtype =  *pmt->Subtype();
    pType->bFixedSizeSamples = pmt->IsFixedSize();
    pType->bTemporalCompression = pmt->IsTemporalCompressed();
    pType->lSampleSize = pmt->GetSampleSize();
    pType->formattype = *pmt->FormatType();
    pType->pUnk = NULL;
    pType->cbFormat = pmt->FormatLength();
	pType->pbFormat = pmt->Format();
	
	HRESULT hr = self->pI->SetMediaType(pType);
	if (FAILED(hr)) {
		seterror("WMInputMediaProps_SetDSMediaType", hr);
		return NULL;
	}
	Py_INCREF(Py_None);
	return Py_None;	
}

static char WMInputMediaProps_GetConnectionName__doc__[] =
""
;
static PyObject *
WMInputMediaProps_GetConnectionName(WMInputMediaPropsObject *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args,"")) 
		return NULL;
	HRESULT hr;
    WCHAR wszName[512];
    WORD cchName = 512;
	hr = self->pI->GetConnectionName(wszName, &cchName);
	if (FAILED(hr)) {
		seterror("WMInputMediaProps_GetConnectionName", hr);
		return NULL;
	}
	return PyObjectFromWideChar(wszName,cchName);
}


static char WMInputMediaProps_GetGroupName__doc__[] =
""
;
static PyObject *
WMInputMediaProps_GetGroupName(WMInputMediaPropsObject *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args,"")) 
		return NULL;
	HRESULT hr;
    WCHAR wszName[512];
    WORD cchName = 512;
	Py_BEGIN_ALLOW_THREADS
	hr = self->pI->GetGroupName(wszName, &cchName);
	Py_END_ALLOW_THREADS
	if (FAILED(hr)) {
		seterror("WMInputMediaProps_GetGroupName", hr);
		return NULL;
	}
	return PyObjectFromWideChar(wszName,cchName);
}

static char WMInputMediaProps_QueryIUnknown__doc__[] =
""
;
static PyObject *
WMInputMediaProps_QueryIUnknown(WMInputMediaPropsObject *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args, ""))
		return NULL;	
	HRESULT hr;
	UnknownObject *obj = newUnknownObject();	
	hr = self->pI->QueryInterface(IID_IUnknown,(void**)&obj->pI);
	if (FAILED(hr)){
		Py_DECREF(obj);
		seterror("WMInputMediaProps_QueryIUnknown", hr);
		return NULL;
	}
	return (PyObject*)obj;
}

static struct PyMethodDef WMInputMediaProps_methods[] = {
	{"GetType", (PyCFunction)WMInputMediaProps_GetType, METH_VARARGS, WMInputMediaProps_GetType__doc__},
	{"GetMediaType", (PyCFunction)WMInputMediaProps_GetMediaType, METH_VARARGS, WMInputMediaProps_GetMediaType__doc__},
	{"SetMediaType", (PyCFunction)WMInputMediaProps_SetMediaType, METH_VARARGS, WMInputMediaProps_SetMediaType__doc__},
	{"SetDSMediaType", (PyCFunction)WMInputMediaProps_SetDSMediaType, METH_VARARGS, WMInputMediaProps_SetDSMediaType__doc__},
	{"GetConnectionName", (PyCFunction)WMInputMediaProps_GetConnectionName, METH_VARARGS, WMInputMediaProps_GetConnectionName__doc__},
	{"GetGroupName", (PyCFunction)WMInputMediaProps_GetGroupName, METH_VARARGS, WMInputMediaProps_GetGroupName__doc__},
	{"QueryIUnknown", (PyCFunction)WMInputMediaProps_QueryIUnknown, METH_VARARGS, WMInputMediaProps_QueryIUnknown__doc__},
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

static char WMOutputMediaProps_GetType__doc__[] =
""
;
static PyObject *
WMOutputMediaProps_GetType(WMOutputMediaPropsObject *self, PyObject *args)
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
		seterror("WMOutputMediaProps_GetType", hr);
		return NULL;
	}
	return (PyObject*)obj;
}


static char WMOutputMediaProps_GetMediaType__doc__[] =
""
;
static PyObject *
WMOutputMediaProps_GetMediaType(WMOutputMediaPropsObject *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args,"")) 
		return NULL;
	HRESULT hr;
	WMMediaTypeObject *obj = newWMMediaTypeObject();
	Py_BEGIN_ALLOW_THREADS
	hr = self->pI->GetMediaType(obj->pMediaType,&obj->cbBuffer);
	Py_END_ALLOW_THREADS	
	if (FAILED(hr)) {
		Py_DECREF(obj);		
		seterror("WWMOutputMediaProps_GetMediaType", hr);
		return NULL;
	}
	return (PyObject*)obj;
}
	
static char WMOutputMediaProps_SetMediaType__doc__[] =
""
;
static PyObject *
WMOutputMediaProps_SetMediaType(WMOutputMediaPropsObject *self, PyObject *args)
{
	WMMediaTypeObject *obj;
	if (!PyArg_ParseTuple(args,"O!",&WMMediaTypeType,&obj)) 
		return NULL;
	HRESULT hr;
	Py_BEGIN_ALLOW_THREADS
	hr = self->pI->SetMediaType(obj->pMediaType);
	Py_END_ALLOW_THREADS	
	if (FAILED(hr)) {
		seterror("WMOutputMediaProps_SetMediaType", hr);
		return NULL;
	}
	Py_INCREF(Py_None);
	return Py_None;	
}

static char WMOutputMediaProps_GetStreamGroupName__doc__[] =
""
;
static PyObject *
WMOutputMediaProps_GetStreamGroupName(WMOutputMediaPropsObject *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args,"")) 
		return NULL;
	HRESULT hr;
    WCHAR wszName[512];
    WORD cchName = 512;
	hr = self->pI->GetStreamGroupName(wszName, &cchName);
	if (FAILED(hr)) {
		seterror("WMOutputMediaProps_GetStreamGroupName", hr);
		return NULL;
	}
	return PyObjectFromWideChar(wszName,cchName);
}
        
static char WMOutputMediaProps_GetConnectionName__doc__[] =
""
;
static PyObject *
WMOutputMediaProps_GetConnectionName(WMOutputMediaPropsObject *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args,"")) 
		return NULL;
	HRESULT hr;
    WCHAR wszName[512];
    WORD cchName = 512;
	hr = self->pI->GetConnectionName(wszName, &cchName);
	if (FAILED(hr)) {
		seterror("WMOutputMediaProps_GetConnectionName", hr);
		return NULL;
	}
	return PyObjectFromWideChar(wszName,cchName);
}

static struct PyMethodDef WMOutputMediaProps_methods[] = {
	{"GetType", (PyCFunction)WMOutputMediaProps_GetType, METH_VARARGS, WMOutputMediaProps_GetType__doc__},
	{"GetMediaType", (PyCFunction)WMOutputMediaProps_GetMediaType, METH_VARARGS, WMOutputMediaProps_GetMediaType__doc__},
	{"SetMediaType", (PyCFunction)WMOutputMediaProps_SetMediaType, METH_VARARGS, WMOutputMediaProps_SetMediaType__doc__},
	{"GetStreamGroupName", (PyCFunction)WMOutputMediaProps_GetStreamGroupName, METH_VARARGS, WMOutputMediaProps_GetStreamGroupName__doc__},
	{"GetConnectionName", (PyCFunction)WMOutputMediaProps_GetConnectionName, METH_VARARGS, WMOutputMediaProps_GetConnectionName__doc__},
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
// WMVideoMediaProps object 

static char WMVideoMediaProps_GetType__doc__[] =
""
;
static PyObject *
WMVideoMediaProps_GetType(WMVideoMediaPropsObject *self, PyObject *args)
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
		seterror("WMVideoMediaProps_GetType", hr);
		return NULL;
	}
	return (PyObject*)obj;
}


static char WMVideoMediaProps_GetMediaType__doc__[] =
""
;
static PyObject *
WMVideoMediaProps_GetMediaType(WMVideoMediaPropsObject *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args,"")) 
		return NULL;
	HRESULT hr;
	WMMediaTypeObject *obj = newWMMediaTypeObject();
	Py_BEGIN_ALLOW_THREADS
	hr = self->pI->GetMediaType(obj->pMediaType,&obj->cbBuffer);
	Py_END_ALLOW_THREADS	
	if (FAILED(hr)) {
		Py_DECREF(obj);		
		seterror("WMVideoMediaProps_GetMediaType", hr);
		return NULL;
	}
	return (PyObject*)obj;
}
	
static char WMVideoMediaProps_SetMediaType__doc__[] =
""
;
static PyObject *
WMVideoMediaProps_SetMediaType(WMVideoMediaPropsObject *self, PyObject *args)
{
	WMMediaTypeObject *obj;
	if (!PyArg_ParseTuple(args,"O!",&WMMediaTypeType,&obj)) 
		return NULL;
	HRESULT hr;
	Py_BEGIN_ALLOW_THREADS
	hr = self->pI->SetMediaType(obj->pMediaType);
	Py_END_ALLOW_THREADS	
	if (FAILED(hr)) {
		seterror("WMVideoMediaProps_SetMediaType", hr);
		return NULL;
	}
	Py_INCREF(Py_None);
	return Py_None;	
}

static char WMVideoMediaProps_GetMaxKeyFrameSpacing__doc__[] =
""
;
static PyObject *
WMVideoMediaProps_GetMaxKeyFrameSpacing(WMVideoMediaPropsObject *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args,"")) 
		return NULL;
	HRESULT hr;
	LONGLONG llTime;
	hr = self->pI->GetMaxKeyFrameSpacing(&llTime);
	if (FAILED(hr)) {
		seterror("WMVideoMediaProps_GetMaxKeyFrameSpacing", hr);
		return NULL;
	}
	return (PyObject*)newLargeIntObject(llTime);	
}
       
static char WMVideoMediaProps_SetMaxKeyFrameSpacing__doc__[] =
""
;
static PyObject *
WMVideoMediaProps_SetMaxKeyFrameSpacing(WMVideoMediaPropsObject *self, PyObject *args)
{
	LargeIntObject *liobj;
	if (!PyArg_ParseTuple(args,"O",&liobj))
		return NULL;
	HRESULT hr;
	Py_BEGIN_ALLOW_THREADS
	hr = self->pI->SetMaxKeyFrameSpacing(liobj->ob_ival);
	Py_END_ALLOW_THREADS	
	if (FAILED(hr)) {
		seterror("WMVideoMediaProps_SetMaxKeyFrameSpacing", hr);
		return NULL;
	}
	Py_INCREF(Py_None);
	return Py_None;	
}
        
static char WMVideoMediaProps_GetQuality__doc__[] =
""
;
static PyObject *
WMVideoMediaProps_GetQuality(WMVideoMediaPropsObject *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args,"")) 
		return NULL;
	HRESULT hr;
	DWORD  dwQuality;
	hr = self->pI->GetQuality(&dwQuality);
	if (FAILED(hr)) {
		seterror("WMVideoMediaProps_GetQuality", hr);
		return NULL;
	}
	return Py_BuildValue("i",dwQuality);	
}
        
static char WMVideoMediaProps_SetQuality__doc__[] =
""
;
static PyObject *
WMVideoMediaProps_SetQuality(WMVideoMediaPropsObject *self, PyObject *args)
{
	DWORD dwQuality;
	if (!PyArg_ParseTuple(args,"i",&dwQuality)) 
		return NULL;
	HRESULT hr;
	hr = self->pI->SetQuality(dwQuality);
	if (FAILED(hr)) {
		seterror("WMVideoMediaProps_SetQuality", hr);
		return NULL;
	}
	Py_INCREF(Py_None);
	return Py_None;	
}

static struct PyMethodDef WMVideoMediaProps_methods[] = {
	{"GetType", (PyCFunction)WMVideoMediaProps_GetType, METH_VARARGS, WMVideoMediaProps_GetType__doc__},
	{"GetMediaType", (PyCFunction)WMVideoMediaProps_GetMediaType, METH_VARARGS, WMVideoMediaProps_GetMediaType__doc__},
	{"SetMediaType", (PyCFunction)WMVideoMediaProps_SetMediaType, METH_VARARGS, WMVideoMediaProps_SetMediaType__doc__},
	{"GetMaxKeyFrameSpacing", (PyCFunction)WMVideoMediaProps_GetMaxKeyFrameSpacing, METH_VARARGS, WMVideoMediaProps_GetMaxKeyFrameSpacing__doc__},
	{"SetMaxKeyFrameSpacing", (PyCFunction)WMVideoMediaProps_SetMaxKeyFrameSpacing, METH_VARARGS, WMVideoMediaProps_SetMaxKeyFrameSpacing__doc__},
	{"GetQuality", (PyCFunction)WMVideoMediaProps_GetQuality, METH_VARARGS, WMVideoMediaProps_GetQuality__doc__},
	{"SetQuality", (PyCFunction)WMVideoMediaProps_SetQuality, METH_VARARGS, WMVideoMediaProps_SetQuality__doc__},
	{NULL, (PyCFunction)NULL, 0, NULL}		/* sentinel */
};

static void
WMVideoMediaProps_dealloc(WMVideoMediaPropsObject *self)
{
	/* XXXX Add your own cleanup code here */
	RELEASE(self->pI);
	PyMem_DEL(self);
}

static PyObject *
WMVideoMediaProps_getattr(WMVideoMediaPropsObject *self, char *name)
{
	/* XXXX Add your own getattr code here */
	return Py_FindMethod(WMVideoMediaProps_methods, (PyObject *)self, name);
}

static char WMVideoMediaPropsType__doc__[] =
""
;

static PyTypeObject WMVideoMediaPropsType = {
	PyObject_HEAD_INIT(&PyType_Type)
	0,				/*ob_size*/
	"WMVideoMediaProps",			/*tp_name*/
	sizeof(WMVideoMediaPropsObject),		/*tp_basicsize*/
	0,				/*tp_itemsize*/
	/* methods */
	(destructor)WMVideoMediaProps_dealloc,	/*tp_dealloc*/
	(printfunc)0,		/*tp_print*/
	(getattrfunc)WMVideoMediaProps_getattr,	/*tp_getattr*/
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
	WMVideoMediaPropsType__doc__ /* Documentation string */
};

// End of code for WMVideoMediaProps object 
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
	Py_BEGIN_ALLOW_THREADS
	hr = self->pI->GetBuffer(&pdwBuffer);
	Py_END_ALLOW_THREADS
	if (FAILED(hr)) {
		seterror("NSSBuffer_GetBuffer", hr);
		return NULL;
	}
	return Py_BuildValue("i",int(pdwBuffer));
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
	hr = self->pI->GetBuffer(&pdwBuffer);
	if (FAILED(hr)) {
		seterror("NSSBuffer_SetBuffer", hr);
		return NULL;
	}
	DWORD dw = PyString_GET_SIZE(obj);
	memcpy(pdwBuffer,PyString_AS_STRING(obj),dw);
	if (FAILED(hr)) {
		seterror("NSSBuffer_SetBuffer", hr);
		return NULL;
	}
	Py_INCREF(Py_None);
	return Py_None;
}


static struct PyMethodDef NSSBuffer_methods[] = {
	{"GetLength", (PyCFunction)NSSBuffer_GetLength, METH_VARARGS, NSSBuffer_GetLength__doc__},
	{"SetLength", (PyCFunction)NSSBuffer_SetLength, METH_VARARGS, NSSBuffer_SetLength__doc__},
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
// WMMediaType object (WM_MEDIA_TYPE)


static char WMMediaType_SetType__doc__[] =
""
;
static PyObject*
WMMediaType_SetType(WMMediaTypeObject *self, PyObject *args)
{
	GUIDObject *obj1,*obj2;
	if (!PyArg_ParseTuple(args,"O!O!",&GUIDType,&obj1,&GUIDType,&obj2)) 
		return NULL;
	self->pMediaType->majortype = obj1->guid;
	self->pMediaType->subtype = obj2->guid;
	Py_INCREF(Py_None);
	return Py_None;	
}

static char WMMediaType_GetType__doc__[] =
""
;
static PyObject*
WMMediaType_GetType(WMMediaTypeObject *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args,"")) 
		return NULL;
	GUIDObject *major = newGUIDObject();
	major->guid = self->pMediaType->majortype;
	
	GUIDObject *subtype = newGUIDObject();
	subtype->guid = self->pMediaType->subtype;

	return Py_BuildValue("(OO)",major,subtype);
}


static char WMMediaType_SetMajorType__doc__[] =
""
;
static PyObject*
WMMediaType_SetMajorType(WMMediaTypeObject *self, PyObject *args)
{
	GUIDObject *obj;
	if (!PyArg_ParseTuple(args,"O!",&GUIDType,&obj)) 
		return NULL;
	self->pMediaType->majortype = obj->guid;
	Py_INCREF(Py_None);
	return Py_None;	
}
static char WMMediaType_SetSubType__doc__[] =
""
;
static PyObject*
WMMediaType_SetSubType(WMMediaTypeObject *self, PyObject *args)
{
	GUIDObject *obj;
	if (!PyArg_ParseTuple(args,"O!",&GUIDType,&obj)) 
		return NULL;
	self->pMediaType->subtype = obj->guid;
	Py_INCREF(Py_None);
	return Py_None;	
}

static char WMMediaType_SetSampleSize__doc__[] =
""
;
static PyObject*
WMMediaType_SetSampleSize(WMMediaTypeObject *self, PyObject *args)
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

static char WMMediaType_SetFormat__doc__[] =
""
;
static PyObject*
WMMediaType_SetFormat(WMMediaTypeObject *self, PyObject *args)
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

static char WMMediaType_GetAsWaveFormatEx__doc__[] =
""
;
static PyObject*
WMMediaType_GetAsWaveFormatEx(WMMediaTypeObject *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args,"")) 
		return NULL;
	WaveFormatExObject *obj = newWaveFormatExObject();
    WAVEFORMATEX *pwfx = (WAVEFORMATEX*)self->pMediaType->pbFormat;
    memcpy(obj->pWF,pwfx,sizeof(WAVEFORMATEX)+pwfx->cbSize);
	return (PyObject*)obj;
}

static struct PyMethodDef WMMediaType_methods[] = {
	{"SetType", (PyCFunction)WMMediaType_SetType, METH_VARARGS, WMMediaType_SetType__doc__},
	{"GetType", (PyCFunction)WMMediaType_GetType, METH_VARARGS, WMMediaType_GetType__doc__},
	{"SetMajorType", (PyCFunction)WMMediaType_SetMajorType, METH_VARARGS, WMMediaType_SetMajorType__doc__},
	{"SetSubType", (PyCFunction)WMMediaType_SetSubType, METH_VARARGS, WMMediaType_SetSubType__doc__},
	{"SetSampleSize", (PyCFunction)WMMediaType_SetSampleSize, METH_VARARGS, WMMediaType_SetSampleSize__doc__},
	{"SetFormat", (PyCFunction)WMMediaType_SetFormat, METH_VARARGS, WMMediaType_SetFormat__doc__},
	{"GetAsWaveFormatEx", (PyCFunction)WMMediaType_GetAsWaveFormatEx, METH_VARARGS, WMMediaType_GetAsWaveFormatEx__doc__},
	{NULL, (PyCFunction)NULL, 0, NULL}		/* sentinel */
};

static void
WMMediaType_dealloc(WMMediaTypeObject *self)
{
	/* XXXX Add your own cleanup code here */
	PyMem_DEL(self);
}

static PyObject *
WMMediaType_getattr(WMMediaTypeObject *self, char *name)
{
	/* XXXX Add your own getattr code here */
	return Py_FindMethod(WMMediaType_methods, (PyObject *)self, name);
}

static char WMMediaTypeType__doc__[] =
""
;
static PyTypeObject WMMediaTypeType = {
	PyObject_HEAD_INIT(&PyType_Type)
	0,				/*ob_size*/
	"WMMediaType",			/*tp_name*/
	sizeof(WMMediaTypeObject),		/*tp_basicsize*/
	0,				/*tp_itemsize*/
	/* methods */
	(destructor)WMMediaType_dealloc,	/*tp_dealloc*/
	(printfunc)0,		/*tp_print*/
	(getattrfunc)WMMediaType_getattr,	/*tp_getattr*/
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
	WMMediaTypeType__doc__ /* Documentation string */
};

// End of code for WMMediaType object 
////////////////////////////////////////////

////////////////////////////////////////////
// WMHeaderInfo object 

static char WMHeaderInfo_GetAttributeCount__doc__[] =
""
;
static PyObject *
WMHeaderInfo_GetAttributeCount(WMHeaderInfoObject *self, PyObject *args)
{
	DWORD dwStreamNum=0;
	if (!PyArg_ParseTuple(args, "|i",&dwStreamNum))
		return NULL;
	HRESULT hr;
	WORD cAttributes;
	Py_BEGIN_ALLOW_THREADS
	hr = self->pI->GetAttributeCount(WORD(dwStreamNum),&cAttributes);
	Py_END_ALLOW_THREADS
	if (FAILED(hr)) {
		seterror("WMHeaderInfo_GetAttributeCount", hr);
		return NULL;
	}
	return Py_BuildValue("i",int(cAttributes));
}

static char WMHeaderInfo_GetAttributeByIndex__doc__[] =
""
;
static PyObject *
WMHeaderInfo_GetAttributeByIndex(WMHeaderInfoObject *self, PyObject *args)
{
	int ix,ixstream;
	if (!PyArg_ParseTuple(args, "ii",&ix,&ixstream))
		return NULL;
	HRESULT hr;
	WORD wIndex=WORD(ix);
	WORD wStreamNum=WORD(ixstream);
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
	char szname[512],szbuf[512];
	sprintf(szname,"%S",wszName);
	PyObject *obj,*x;
	switch (type)
        {
        case WMT_TYPE_DWORD:
			obj = Py_BuildValue("(isi)",type,szname,*((DWORD*)pValue));
            break;
        case WMT_TYPE_STRING:
			sprintf(szbuf,"%S",(WCHAR *)pValue);
			obj = Py_BuildValue("(iss)",type,szname,szbuf);
            break;
        case WMT_TYPE_BINARY:
			x = PyString_FromStringAndSize((char*)pValue,(int)cbLength);			
			obj = Py_BuildValue("(isO)",type,szname,x);
			Py_DECREF(x);
            break;
        case WMT_TYPE_BOOL:
			obj = Py_BuildValue("(isi)",type,szname,*((BOOL*)pValue));
            break;
        case WMT_TYPE_QWORD:
			x = (PyObject*)newLargeIntObject(*(LONGLONG*)pValue);
			obj = Py_BuildValue("(isO)",type,szname,x);
			Py_DECREF(x);
            break;
        case WMT_TYPE_WORD:
			obj = Py_BuildValue("(isi)",type,szname,*((WORD*)pValue));
            break;
        case WMT_TYPE_GUID:
			x = (PyObject*)newGUIDObject((GUID*)pValue);
			obj = Py_BuildValue("(isi)",type,szname,x);
			Py_DECREF(x);
            break;
		default:
			obj = Py_BuildValue("(is)",type,szname);
			break;
        }	
	return obj;	
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
// WMVideoInfoHeader object  (WMVIDEOINFOHEADER)
   
static struct PyMethodDef WMVideoInfoHeader_methods[] = {
	{NULL, (PyCFunction)NULL, 0, NULL}		/* sentinel */
};

static void
WMVideoInfoHeader_dealloc(WMVideoInfoHeaderObject *self)
{
	/* XXXX Add your own cleanup code here */
	PyMem_DEL(self);
}

static PyObject *
WMVideoInfoHeader_getattr(WMVideoInfoHeaderObject *self, char *name)
{
	/* XXXX Add your own getattr code here */
	return Py_FindMethod(WMVideoInfoHeader_methods, (PyObject *)self, name);
}

static char WMVideoInfoHeaderType__doc__[] =
""
;

static PyTypeObject WMVideoInfoHeaderType = {
	PyObject_HEAD_INIT(&PyType_Type)
	0,				/*ob_size*/
	"WMVideoInfoHeader",			/*tp_name*/
	sizeof(WMVideoInfoHeaderObject),		/*tp_basicsize*/
	0,				/*tp_itemsize*/
	/* methods */
	(destructor)WMVideoInfoHeader_dealloc,	/*tp_dealloc*/
	(printfunc)0,		/*tp_print*/
	(getattrfunc)WMVideoInfoHeader_getattr,	/*tp_getattr*/
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
	WMVideoInfoHeaderType__doc__ /* Documentation string */
};

// End of code for WMVideoInfoHeader object 
////////////////////////////////////////////

////////////////////////////////////////////
// Unknown object (general but defined here for indepentance) 

static struct PyMethodDef Unknown_methods[] = {
	{NULL, (PyCFunction)NULL, 0, NULL}		/* sentinel */
};

static void
Unknown_dealloc(UnknownObject *self)
{
	/* XXXX Add your own cleanup code here */
	RELEASE(self->pI);
	PyMem_DEL(self);
}

static PyObject *
Unknown_getattr(UnknownObject *self, char *name)
{
	/* XXXX Add your own getattr code here */
	return Py_FindMethod(Unknown_methods, (PyObject *)self, name);
}

static char UnknownType__doc__[] =
""
;

static PyTypeObject UnknownType = {
	PyObject_HEAD_INIT(&PyType_Type)
	0,				/*ob_size*/
	"Unknown",			/*tp_name*/
	sizeof(UnknownObject),		/*tp_basicsize*/
	0,				/*tp_itemsize*/
	/* methods */
	(destructor)Unknown_dealloc,	/*tp_dealloc*/
	(printfunc)0,		/*tp_print*/
	(getattrfunc)Unknown_getattr,	/*tp_getattr*/
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
	UnknownType__doc__ /* Documentation string */
};

// End of code for Unknown object 
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

////////////////////////////////////////////
// WMReaderAdvanced object 


static char WMReaderAdvanced_SetUserProvidedClock__doc__[] =
""
;
static PyObject*
WMReaderAdvanced_SetUserProvidedClock(WMReaderAdvancedObject *self, PyObject *args)
{
	BOOL fUserClock=TRUE;
	if (!PyArg_ParseTuple(args,"|i",&fUserClock)) 
		return NULL;
	HRESULT hr;
	hr = self->pI->SetUserProvidedClock(fUserClock);
	if (FAILED(hr)) {
		seterror("WMReaderAdvanced_SetUserProvidedClock", hr);
		return NULL;
	}			
	Py_INCREF(Py_None);
	return Py_None;	
}

static char WMReaderAdvanced_SetManualStreamSelection__doc__[] =
""
;
static PyObject*
WMReaderAdvanced_SetManualStreamSelection(WMReaderAdvancedObject *self, PyObject *args)
{
	BOOL manual=TRUE;
	if (!PyArg_ParseTuple(args,"|i",&manual)) 
		return NULL;
	HRESULT hr;
	hr = self->pI->SetManualStreamSelection(manual);
	if (FAILED(hr)) {
		seterror("WMReaderAdvanced_SetManualStreamSelection", hr);
		return NULL;
	}			
	Py_INCREF(Py_None);
	return Py_None;	
}

static char WMReaderAdvanced_SetReceiveStreamSamples__doc__[] =
""
;
static PyObject*
WMReaderAdvanced_SetReceiveStreamSamples(WMReaderAdvancedObject *self, PyObject *args)
{
	int iStreamNum;
	BOOL fReceiveStreamSamples=TRUE;
	if (!PyArg_ParseTuple(args,"i|i",&iStreamNum,&fReceiveStreamSamples)) 
		return NULL;
	HRESULT hr;
	hr = self->pI->SetReceiveStreamSamples(WORD(iStreamNum),fReceiveStreamSamples);
	if (FAILED(hr)) {
		seterror("WMReaderAdvanced_SetReceiveStreamSamples", hr);
		return NULL;
	}			
	Py_INCREF(Py_None);
	return Py_None;	
}
			
static char WMReaderAdvanced_GetReceiveStreamSamples__doc__[] =
""
;
static PyObject*
WMReaderAdvanced_GetReceiveStreamSamples(WMReaderAdvancedObject *self, PyObject *args)
{
	int iStreamNum;
	if (!PyArg_ParseTuple(args,"i",&iStreamNum)) 
		return NULL;
	HRESULT hr;
	BOOL fReceiveStreamSamples;
	hr = self->pI->GetReceiveStreamSamples(WORD(iStreamNum),&fReceiveStreamSamples);
	if (FAILED(hr)) {
		seterror("WMReaderAdvanced_GetReceiveStreamSamples", hr);
		return NULL;
	}
	return Py_BuildValue("i",fReceiveStreamSamples);
}

static struct PyMethodDef WMReaderAdvanced_methods[] = {
	{"SetUserProvidedClock", (PyCFunction)WMReaderAdvanced_SetUserProvidedClock, METH_VARARGS, WMReaderAdvanced_SetUserProvidedClock__doc__},
	{"SetManualStreamSelection", (PyCFunction)WMReaderAdvanced_SetManualStreamSelection, METH_VARARGS, WMReaderAdvanced_SetManualStreamSelection__doc__},
	{"SetReceiveStreamSamples", (PyCFunction)WMReaderAdvanced_SetReceiveStreamSamples, METH_VARARGS, WMReaderAdvanced_SetReceiveStreamSamples__doc__},
	{"GetReceiveStreamSamples", (PyCFunction)WMReaderAdvanced_GetReceiveStreamSamples, METH_VARARGS, WMReaderAdvanced_GetReceiveStreamSamples__doc__},
	{NULL, (PyCFunction)NULL, 0, NULL}		/* sentinel */
};

static void
WMReaderAdvanced_dealloc(WMReaderAdvancedObject *self)
{
	/* XXXX Add your own cleanup code here */
	RELEASE(self->pI);
	PyMem_DEL(self);
}

static PyObject *
WMReaderAdvanced_getattr(WMReaderAdvancedObject *self, char *name)
{
	/* XXXX Add your own getattr code here */
	return Py_FindMethod(WMReaderAdvanced_methods, (PyObject *)self, name);
}

static char WMReaderAdvancedType__doc__[] =
""
;

static PyTypeObject WMReaderAdvancedType = {
	PyObject_HEAD_INIT(&PyType_Type)
	0,				/*ob_size*/
	"WMReaderAdvanced",			/*tp_name*/
	sizeof(WMReaderAdvancedObject),		/*tp_basicsize*/
	0,				/*tp_itemsize*/
	/* methods */
	(destructor)WMReaderAdvanced_dealloc,	/*tp_dealloc*/
	(printfunc)0,		/*tp_print*/
	(getattrfunc)WMReaderAdvanced_getattr,	/*tp_getattr*/
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
	WMReaderAdvancedType__doc__ /* Documentation string */
};

// End of code for WMReaderAdvanced object 
////////////////////////////////////////////

////////////////////////////////////////////
// WMWriterAdvanced object 

static struct PyMethodDef WMWriterAdvanced_methods[] = {
	{NULL, (PyCFunction)NULL, 0, NULL}		/* sentinel */
};

static void
WMWriterAdvanced_dealloc(WMWriterAdvancedObject *self)
{
	/* XXXX Add your own cleanup code here */
	RELEASE(self->pI);
	PyMem_DEL(self);
}

static PyObject *
WMWriterAdvanced_getattr(WMWriterAdvancedObject *self, char *name)
{
	/* XXXX Add your own getattr code here */
	return Py_FindMethod(WMWriterAdvanced_methods, (PyObject *)self, name);
}

static char WMWriterAdvancedType__doc__[] =
""
;

static PyTypeObject WMWriterAdvancedType = {
	PyObject_HEAD_INIT(&PyType_Type)
	0,				/*ob_size*/
	"WMWriterAdvanced",			/*tp_name*/
	sizeof(WMWriterAdvancedObject),		/*tp_basicsize*/
	0,				/*tp_itemsize*/
	/* methods */
	(destructor)WMWriterAdvanced_dealloc,	/*tp_dealloc*/
	(printfunc)0,		/*tp_print*/
	(getattrfunc)WMWriterAdvanced_getattr,	/*tp_getattr*/
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
	WMWriterAdvancedType__doc__ /* Documentation string */
};

// End of code for WMWriterAdvanced object 
////////////////////////////////////////////


////////////////////////////////////////////
// WMStreamConfig object 

static char WMStreamConfig_GetStreamType__doc__[] =
""
;
static PyObject *
WMStreamConfig_GetStreamType(WMStreamConfigObject *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args,"")) 
		return NULL;
	HRESULT hr;
	GUIDObject *obj = newGUIDObject();
	hr = self->pI->GetStreamType(&obj->guid);
	if (FAILED(hr)) {
		seterror("WMStreamConfig_GetStreamType", hr);
		return NULL;
	}
	return (PyObject*)obj;
}
      
static char WMStreamConfig_GetStreamNumber__doc__[] =
""
;
static PyObject *
WMStreamConfig_GetStreamNumber(WMStreamConfigObject *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args,"")) 
		return NULL;
	HRESULT hr;
	WORD wStreamNumber;
	hr = self->pI->GetStreamNumber(&wStreamNumber);
	if (FAILED(hr)) {
		seterror("WMStreamConfig_GetStreamNumber", hr);
		return NULL;
	}
	return Py_BuildValue("i",int(wStreamNumber));
}
        
static char WMStreamConfig_SetStreamNumber__doc__[] =
""
;
static PyObject *
WMStreamConfig_SetStreamNumber(WMStreamConfigObject *self, PyObject *args)
{
	DWORD dwStreamNum;
	if (!PyArg_ParseTuple(args,"i",&dwStreamNum)) 
		return NULL;
	HRESULT hr;
	hr = self->pI->SetStreamNumber(WORD(dwStreamNum));
	if (FAILED(hr)) {
		seterror("WMStreamConfig_SetStreamNumber", hr);
		return NULL;
	}
	Py_INCREF(Py_None);
	return Py_None;
}
       
static char WMStreamConfig_GetStreamName__doc__[] =
""
;
static PyObject *
WMStreamConfig_GetStreamName(WMStreamConfigObject *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args,"")) 
		return NULL;
	HRESULT hr;
	WCHAR wszStreamName[512];
	WORD cchStreamName=512;
	hr = self->pI->GetStreamName(wszStreamName,&cchStreamName);
	if (FAILED(hr)) {
		seterror("WMStreamConfig_GetStreamName", hr);
		return NULL;
	}
	char *szStreamName = new char[cchStreamName+1];
	WideCharToMultiByte(CP_ACP,0,wszStreamName,cchStreamName+1,szStreamName,cchStreamName+1,NULL,NULL);
	PyObject *obj = Py_BuildValue("s",szStreamName);
	delete [] szStreamName;
	return obj;
}


static char WMStreamConfig_SetStreamName__doc__[] =
""
;
static PyObject *
WMStreamConfig_SetStreamName(WMStreamConfigObject *self, PyObject *args)
{
	char *psz;
	if (!PyArg_ParseTuple(args,"i",&psz))
		return NULL;
	HRESULT hr;
	int len = strlen(psz);
	WCHAR *pwsz = new WCHAR[len+1];
	MultiByteToWideChar(CP_ACP,0,psz,-1,pwsz,len+1);
	hr = self->pI->SetStreamName(pwsz);
	if (FAILED(hr)) {
		delete [] pwsz;
		seterror("WMStreamConfig_SetStreamName", hr);
		return NULL;
	}
	delete [] pwsz;
	Py_INCREF(Py_None);
	return Py_None;
}
       
static char WMStreamConfig_GetConnectionName__doc__[] =
""
;
static PyObject *
WMStreamConfig_GetConnectionName(WMStreamConfigObject *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args,"")) 
		return NULL;
	HRESULT hr;
	WCHAR wsz[512];
	WORD cch=512;
	hr = self->pI->GetConnectionName(wsz,&cch);
	if (FAILED(hr)) {
		seterror("WMStreamConfig_GetConnectionName", hr);
		return NULL;
	}
	char *psz = new char[cch+1];
	WideCharToMultiByte(CP_ACP,0,wsz,cch+1,psz,cch+1,NULL,NULL);
	PyObject *obj = Py_BuildValue("s",psz);
	delete [] psz;
	return obj;
}

static char WMStreamConfig_SetConnectionName__doc__[] =
""
;
static PyObject *
WMStreamConfig_SetConnectionName(WMStreamConfigObject *self, PyObject *args)
{
	char *psz;
	if (!PyArg_ParseTuple(args,"i",&psz))
		return NULL;
	HRESULT hr;
	int len = strlen(psz);
	WCHAR *pwsz = new WCHAR[len+1];
	MultiByteToWideChar(CP_ACP,0,psz,-1,pwsz,len+1);
	hr = self->pI->SetConnectionName(pwsz);
	if (FAILED(hr)) {
		delete [] pwsz;
		seterror("WMStreamConfig_SetConnectionName", hr);
		return NULL;
	}
	delete [] pwsz;
	Py_INCREF(Py_None);
	return Py_None;
}

static char WMStreamConfig_GetBitrate__doc__[] =
""
;
static PyObject *
WMStreamConfig_GetBitrate(WMStreamConfigObject *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args,"")) 
		return NULL;
	HRESULT hr;
	DWORD dwBitrate;
	hr = self->pI->GetBitrate(&dwBitrate);
	if (FAILED(hr)) {
		seterror("WMStreamConfig_GetBitrate", hr);
		return NULL;
	}
	return Py_BuildValue("i",dwBitrate);
}

static char WMStreamConfig_SetBitrate__doc__[] =
""
;
static PyObject *
WMStreamConfig_SetBitrate(WMStreamConfigObject *self, PyObject *args)
{
	DWORD dwBitrate;
	if (!PyArg_ParseTuple(args,"i",&dwBitrate))
		return NULL;
	HRESULT hr;
	hr = self->pI->SetBitrate(dwBitrate);
	if (FAILED(hr)) {
		seterror("WMStreamConfig_SetBitrate", hr);
		return NULL;
	}
	Py_INCREF(Py_None);
	return Py_None;
}
static char WMStreamConfig_GetBufferWindow__doc__[] =
""
;
static PyObject *
WMStreamConfig_GetBufferWindow(WMStreamConfigObject *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args,"")) 
		return NULL;
	HRESULT hr;
	DWORD msBufferWindow;
	hr = self->pI->GetBufferWindow(&msBufferWindow);
	if (FAILED(hr)) {
		seterror("WMStreamConfig_GetBufferWindow", hr);
		return NULL;
	}
	return Py_BuildValue("i",msBufferWindow);
}

static char WMStreamConfig_SetBufferWindow__doc__[] =
""
;
static PyObject *
WMStreamConfig_SetBufferWindow(WMStreamConfigObject *self, PyObject *args)
{
	DWORD msBufferWindow;
	if (!PyArg_ParseTuple(args,"i",&msBufferWindow))
		return NULL;
	HRESULT hr;
	hr = self->pI->SetBufferWindow(msBufferWindow);
	if (FAILED(hr)) {
		seterror("WMStreamConfig_SetBufferWindow", hr);
		return NULL;
	}
	Py_INCREF(Py_None);
	return Py_None;
}

static char WMStreamConfig_QueryIWMVideoMediaProps__doc__[] =
""
;
static PyObject *
WMStreamConfig_QueryIWMVideoMediaProps(WMStreamConfigObject *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args,""))
		return NULL;
	HRESULT hr;
	WMVideoMediaPropsObject *obj = newWMVideoMediaPropsObject();
	hr = self->pI->QueryInterface(IID_IWMVideoMediaProps,(void**)obj->pI);
	if (FAILED(hr)) {
		Py_DECREF(obj);
		seterror("WMStreamConfig_QueryIWMVideoMediaProps", hr);
		return NULL;
	}
	return (PyObject*)obj;
}

static struct PyMethodDef WMStreamConfig_methods[] = {
	{"GetStreamType", (PyCFunction)WMStreamConfig_GetStreamType, METH_VARARGS, WMStreamConfig_GetStreamType__doc__},
	{"GetStreamNumber", (PyCFunction)WMStreamConfig_GetStreamNumber, METH_VARARGS, WMStreamConfig_GetStreamNumber__doc__},
	{"SetStreamNumber", (PyCFunction)WMStreamConfig_SetStreamNumber, METH_VARARGS, WMStreamConfig_SetStreamNumber__doc__},
	{"GetStreamName", (PyCFunction)WMStreamConfig_GetStreamName, METH_VARARGS, WMStreamConfig_GetStreamName__doc__},
	{"SetStreamName", (PyCFunction)WMStreamConfig_SetStreamName, METH_VARARGS, WMStreamConfig_SetStreamName__doc__},
	{"GetConnectionName", (PyCFunction)WMStreamConfig_GetConnectionName, METH_VARARGS, WMStreamConfig_GetConnectionName__doc__},
	{"SetConnectionName", (PyCFunction)WMStreamConfig_SetConnectionName, METH_VARARGS, WMStreamConfig_SetConnectionName__doc__},
	{"GetBitrate", (PyCFunction)WMStreamConfig_GetBitrate, METH_VARARGS, WMStreamConfig_GetBitrate__doc__},
	{"SetBitrate", (PyCFunction)WMStreamConfig_SetBitrate, METH_VARARGS, WMStreamConfig_SetBitrate__doc__},
	{"GetBufferWindow", (PyCFunction)WMStreamConfig_GetBufferWindow, METH_VARARGS, WMStreamConfig_GetBufferWindow__doc__},
	{"SetBufferWindow", (PyCFunction)WMStreamConfig_SetBufferWindow, METH_VARARGS, WMStreamConfig_SetBufferWindow__doc__},
	{"QueryIWMVideoMediaProps", (PyCFunction)WMStreamConfig_QueryIWMVideoMediaProps, METH_VARARGS, WMStreamConfig_QueryIWMVideoMediaProps__doc__},
	{NULL, (PyCFunction)NULL, 0, NULL}		/* sentinel */
};

static void
WMStreamConfig_dealloc(WMStreamConfigObject *self)
{
	/* XXXX Add your own cleanup code here */
	RELEASE(self->pI);
	PyMem_DEL(self);
}

static PyObject *
WMStreamConfig_getattr(WMStreamConfigObject *self, char *name)
{
	/* XXXX Add your own getattr code here */
	return Py_FindMethod(WMStreamConfig_methods, (PyObject *)self, name);
}

static char WMStreamConfigType__doc__[] =
""
;

static PyTypeObject WMStreamConfigType = {
	PyObject_HEAD_INIT(&PyType_Type)
	0,				/*ob_size*/
	"WMStreamConfig",			/*tp_name*/
	sizeof(WMStreamConfigObject),		/*tp_basicsize*/
	0,				/*tp_itemsize*/
	/* methods */
	(destructor)WMStreamConfig_dealloc,	/*tp_dealloc*/
	(printfunc)0,		/*tp_print*/
	(getattrfunc)WMStreamConfig_getattr,	/*tp_getattr*/
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
	WMStreamConfigType__doc__ /* Documentation string */
};

// End of code for WMStreamConfig object 
////////////////////////////////////////////

////////////////////////////////////////////
// WMCodecInfo object (IWMCodecInfo)

static char WMCodecInfo_GetCodecInfoCount__doc__[] =
""
;
static PyObject *
WMCodecInfo_GetCodecInfoCount(WMCodecInfoObject *self, PyObject *args)
{
	GUIDObject *obj;
	if (!PyArg_ParseTuple(args,"O!", &GUIDType, &obj)) 
		return NULL;
	DWORD cCodecs;
	HRESULT hr = self->pI->GetCodecInfoCount(obj->guid, &cCodecs);
	if (FAILED(hr)) {
		seterror("WMCodecInfo_GetCodecInfoCount", hr);
		return NULL;
	}
	return Py_BuildValue("i", cCodecs);
}
      
static char WMCodecInfo_GetCodecFormatCount__doc__[] =
""
;
static PyObject *
WMCodecInfo_GetCodecFormatCount(WMCodecInfoObject *self, PyObject *args)
{
	GUIDObject *obj;
	DWORD dwCodecIndex;
	if (!PyArg_ParseTuple(args,"O!i", &GUIDType, &obj, &dwCodecIndex)) 
		return NULL;
	DWORD cFormats;
	HRESULT hr = self->pI->GetCodecFormatCount(obj->guid, dwCodecIndex, &cFormats);
	if (FAILED(hr)) {
		seterror("WMCodecInfo_GetCodecFormatCount", hr);
		return NULL;
	}
	return Py_BuildValue("i", cFormats);
}

static char WMCodecInfo_GetCodecFormat__doc__[] =
""
;
static PyObject *
WMCodecInfo_GetCodecFormat(WMCodecInfoObject *self, PyObject *args)
{
	GUIDObject *guidobj;
	DWORD dwCodecIndex;
	DWORD dwFormatIndex;
	if (!PyArg_ParseTuple(args,"O!ii", &GUIDType, &guidobj, &dwCodecIndex, &dwFormatIndex)) 
		return NULL;
	WMStreamConfigObject *obj = newWMStreamConfigObject();
	if(obj==NULL) return NULL;
	
	HRESULT hr = self->pI->GetCodecFormat(guidobj->guid, dwCodecIndex, dwFormatIndex, &obj->pI);
	if (FAILED(hr)) {
		Py_DECREF(obj);
		seterror("WMCodecInfo_GetCodecFormat", hr);
		return NULL;
	}
	return (PyObject *)obj;
}

												  
static struct PyMethodDef WMCodecInfo_methods[] = {
	{"GetCodecInfoCount", (PyCFunction)WMCodecInfo_GetCodecInfoCount, METH_VARARGS, WMCodecInfo_GetCodecInfoCount__doc__},
	{"GetCodecFormatCount", (PyCFunction)WMCodecInfo_GetCodecFormatCount, METH_VARARGS, WMCodecInfo_GetCodecFormatCount__doc__},
	{"GetCodecFormat", (PyCFunction)WMCodecInfo_GetCodecFormat, METH_VARARGS, WMCodecInfo_GetCodecFormat__doc__},
	{NULL, (PyCFunction)NULL, 0, NULL}		/* sentinel */
};

static void
WMCodecInfo_dealloc(WMCodecInfoObject *self)
{
	/* XXXX Add your own cleanup code here */
	RELEASE(self->pI);
	PyMem_DEL(self);
}

static PyObject *
WMCodecInfo_getattr(WMCodecInfoObject *self, char *name)
{
	/* XXXX Add your own getattr code here */
	return Py_FindMethod(WMCodecInfo_methods, (PyObject *)self, name);
}

static char WMCodecInfoType__doc__[] =
""
;

static PyTypeObject WMCodecInfoType = {
	PyObject_HEAD_INIT(&PyType_Type)
	0,				/*ob_size*/
	"WMCodecInfo",			/*tp_name*/
	sizeof(WMCodecInfoObject),		/*tp_basicsize*/
	0,				/*tp_itemsize*/
	/* methods */
	(destructor)WMCodecInfo_dealloc,	/*tp_dealloc*/
	(printfunc)0,		/*tp_print*/
	(getattrfunc)WMCodecInfo_getattr,	/*tp_getattr*/
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
	WMCodecInfoType__doc__ /* Documentation string */
};

// End of code for WMCodecInfo object 
////////////////////////////////////////////

////////////////////////////////////////////
// WMStreamList object 
   
static struct PyMethodDef WMStreamList_methods[] = {
	{NULL, (PyCFunction)NULL, 0, NULL}		/* sentinel */
};

static void
WMStreamList_dealloc(WMStreamListObject *self)
{
	/* XXXX Add your own cleanup code here */
	RELEASE(self->pI);
	PyMem_DEL(self);
}

static PyObject *
WMStreamList_getattr(WMStreamListObject *self, char *name)
{
	/* XXXX Add your own getattr code here */
	return Py_FindMethod(WMStreamList_methods, (PyObject *)self, name);
}

static char WMStreamListType__doc__[] =
""
;

static PyTypeObject WMStreamListType = {
	PyObject_HEAD_INIT(&PyType_Type)
	0,				/*ob_size*/
	"WMStreamList",			/*tp_name*/
	sizeof(WMStreamListObject),		/*tp_basicsize*/
	0,				/*tp_itemsize*/
	/* methods */
	(destructor)WMStreamList_dealloc,	/*tp_dealloc*/
	(printfunc)0,		/*tp_print*/
	(getattrfunc)WMStreamList_getattr,	/*tp_getattr*/
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
	WMStreamListType__doc__ /* Documentation string */
};

// End of code for WMStreamList object 
////////////////////////////////////////////

////////////////////////////////////////////
// WMReaderStreamClock object 
   
static struct PyMethodDef WMReaderStreamClock_methods[] = {
	{NULL, (PyCFunction)NULL, 0, NULL}		/* sentinel */
};

static void
WMReaderStreamClock_dealloc(WMReaderStreamClockObject *self)
{
	/* XXXX Add your own cleanup code here */
	RELEASE(self->pI);
	PyMem_DEL(self);
}

static PyObject *
WMReaderStreamClock_getattr(WMReaderStreamClockObject *self, char *name)
{
	/* XXXX Add your own getattr code here */
	return Py_FindMethod(WMReaderStreamClock_methods, (PyObject *)self, name);
}

static char WMReaderStreamClockType__doc__[] =
""
;

static PyTypeObject WMReaderStreamClockType = {
	PyObject_HEAD_INIT(&PyType_Type)
	0,				/*ob_size*/
	"WMReaderStreamClock",			/*tp_name*/
	sizeof(WMReaderStreamClockObject),		/*tp_basicsize*/
	0,				/*tp_itemsize*/
	/* methods */
	(destructor)WMReaderStreamClock_dealloc,	/*tp_dealloc*/
	(printfunc)0,		/*tp_print*/
	(getattrfunc)WMReaderStreamClock_getattr,	/*tp_getattr*/
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
	WMReaderStreamClockType__doc__ /* Documentation string */
};

// End of code for WMReaderStreamClock object 
////////////////////////////////////////////

////////////////////////////////////////////
// WMMutualExclusion object 
   
static struct PyMethodDef WMMutualExclusion_methods[] = {
	{NULL, (PyCFunction)NULL, 0, NULL}		/* sentinel */
};

static void
WMMutualExclusion_dealloc(WMMutualExclusionObject *self)
{
	/* XXXX Add your own cleanup code here */
	RELEASE(self->pI);
	PyMem_DEL(self);
}

static PyObject *
WMMutualExclusion_getattr(WMMutualExclusionObject *self, char *name)
{
	/* XXXX Add your own getattr code here */
	return Py_FindMethod(WMMutualExclusion_methods, (PyObject *)self, name);
}

static char WMMutualExclusionType__doc__[] =
""
;

static PyTypeObject WMMutualExclusionType = {
	PyObject_HEAD_INIT(&PyType_Type)
	0,				/*ob_size*/
	"WMMutualExclusion",			/*tp_name*/
	sizeof(WMMutualExclusionObject),		/*tp_basicsize*/
	0,				/*tp_itemsize*/
	/* methods */
	(destructor)WMMutualExclusion_dealloc,	/*tp_dealloc*/
	(printfunc)0,		/*tp_print*/
	(getattrfunc)WMMutualExclusion_getattr,	/*tp_getattr*/
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
	WMMutualExclusionType__doc__ /* Documentation string */
};

// End of code for WMMutualExclusion object 
////////////////////////////////////////////

////////////////////////////////////////////
// WMMetadataEditor object 
   
static struct PyMethodDef WMMetadataEditor_methods[] = {
	{NULL, (PyCFunction)NULL, 0, NULL}		/* sentinel */
};

static void
WMMetadataEditor_dealloc(WMMetadataEditorObject *self)
{
	/* XXXX Add your own cleanup code here */
	RELEASE(self->pI);
	PyMem_DEL(self);
}

static PyObject *
WMMetadataEditor_getattr(WMMetadataEditorObject *self, char *name)
{
	/* XXXX Add your own getattr code here */
	return Py_FindMethod(WMMetadataEditor_methods, (PyObject *)self, name);
}

static char WMMetadataEditorType__doc__[] =
""
;

static PyTypeObject WMMetadataEditorType = {
	PyObject_HEAD_INIT(&PyType_Type)
	0,				/*ob_size*/
	"WMMetadataEditor",			/*tp_name*/
	sizeof(WMMetadataEditorObject),		/*tp_basicsize*/
	0,				/*tp_itemsize*/
	/* methods */
	(destructor)WMMetadataEditor_dealloc,	/*tp_dealloc*/
	(printfunc)0,		/*tp_print*/
	(getattrfunc)WMMetadataEditor_getattr,	/*tp_getattr*/
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
	WMMetadataEditorType__doc__ /* Documentation string */
};

// End of code for WMMetadataEditor object 
////////////////////////////////////////////

////////////////////////////////////////////
// WMIndexer object 
   
static struct PyMethodDef WMIndexer_methods[] = {
	{NULL, (PyCFunction)NULL, 0, NULL}		/* sentinel */
};

static void
WMIndexer_dealloc(WMIndexerObject *self)
{
	/* XXXX Add your own cleanup code here */
	RELEASE(self->pI);
	PyMem_DEL(self);
}

static PyObject *
WMIndexer_getattr(WMIndexerObject *self, char *name)
{
	/* XXXX Add your own getattr code here */
	return Py_FindMethod(WMIndexer_methods, (PyObject *)self, name);
}

static char WMIndexerType__doc__[] =
""
;

static PyTypeObject WMIndexerType = {
	PyObject_HEAD_INIT(&PyType_Type)
	0,				/*ob_size*/
	"WMIndexer",			/*tp_name*/
	sizeof(WMIndexerObject),		/*tp_basicsize*/
	0,				/*tp_itemsize*/
	/* methods */
	(destructor)WMIndexer_dealloc,	/*tp_dealloc*/
	(printfunc)0,		/*tp_print*/
	(getattrfunc)WMIndexer_getattr,	/*tp_getattr*/
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
	WMIndexerType__doc__ /* Documentation string */
};

// End of code for WMIndexer object 
////////////////////////////////////////////

////////////////////////////////////////////
// WMWriterSink object 
   
static struct PyMethodDef WMWriterSink_methods[] = {
	{NULL, (PyCFunction)NULL, 0, NULL}		/* sentinel */
};

static void
WMWriterSink_dealloc(WMWriterSinkObject *self)
{
	/* XXXX Add your own cleanup code here */
	RELEASE(self->pI);
	PyMem_DEL(self);
}

static PyObject *
WMWriterSink_getattr(WMWriterSinkObject *self, char *name)
{
	/* XXXX Add your own getattr code here */
	return Py_FindMethod(WMWriterSink_methods, (PyObject *)self, name);
}

static char WMWriterSinkType__doc__[] =
""
;

static PyTypeObject WMWriterSinkType = {
	PyObject_HEAD_INIT(&PyType_Type)
	0,				/*ob_size*/
	"WMWriterSink",			/*tp_name*/
	sizeof(WMWriterSinkObject),		/*tp_basicsize*/
	0,				/*tp_itemsize*/
	/* methods */
	(destructor)WMWriterSink_dealloc,	/*tp_dealloc*/
	(printfunc)0,		/*tp_print*/
	(getattrfunc)WMWriterSink_getattr,	/*tp_getattr*/
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
	WMWriterSinkType__doc__ /* Documentation string */
};

// End of code for WMWriterSink object 
////////////////////////////////////////////

////////////////////////////////////////////
// WMWriterFileSink object 
   
static struct PyMethodDef WMWriterFileSink_methods[] = {
	{NULL, (PyCFunction)NULL, 0, NULL}		/* sentinel */
};

static void
WMWriterFileSink_dealloc(WMWriterFileSinkObject *self)
{
	/* XXXX Add your own cleanup code here */
	RELEASE(self->pI);
	PyMem_DEL(self);
}

static PyObject *
WMWriterFileSink_getattr(WMWriterFileSinkObject *self, char *name)
{
	/* XXXX Add your own getattr code here */
	return Py_FindMethod(WMWriterFileSink_methods, (PyObject *)self, name);
}

static char WMWriterFileSinkType__doc__[] =
""
;

static PyTypeObject WMWriterFileSinkType = {
	PyObject_HEAD_INIT(&PyType_Type)
	0,				/*ob_size*/
	"WMWriterFileSink",			/*tp_name*/
	sizeof(WMWriterFileSinkObject),		/*tp_basicsize*/
	0,				/*tp_itemsize*/
	/* methods */
	(destructor)WMWriterFileSink_dealloc,	/*tp_dealloc*/
	(printfunc)0,		/*tp_print*/
	(getattrfunc)WMWriterFileSink_getattr,	/*tp_getattr*/
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
	WMWriterFileSinkType__doc__ /* Documentation string */
};

// End of code for WMWriterFileSink object 
////////////////////////////////////////////

////////////////////////////////////////////
// WMWriterNetworkSink object 
   
static struct PyMethodDef WMWriterNetworkSink_methods[] = {
	{NULL, (PyCFunction)NULL, 0, NULL}		/* sentinel */
};

static void
WMWriterNetworkSink_dealloc(WMWriterNetworkSinkObject *self)
{
	/* XXXX Add your own cleanup code here */
	RELEASE(self->pI);
	PyMem_DEL(self);
}

static PyObject *
WMWriterNetworkSink_getattr(WMWriterNetworkSinkObject *self, char *name)
{
	/* XXXX Add your own getattr code here */
	return Py_FindMethod(WMWriterNetworkSink_methods, (PyObject *)self, name);
}

static char WMWriterNetworkSinkType__doc__[] =
""
;

static PyTypeObject WMWriterNetworkSinkType = {
	PyObject_HEAD_INIT(&PyType_Type)
	0,				/*ob_size*/
	"WMWriterNetworkSink",			/*tp_name*/
	sizeof(WMWriterNetworkSinkObject),		/*tp_basicsize*/
	0,				/*tp_itemsize*/
	/* methods */
	(destructor)WMWriterNetworkSink_dealloc,	/*tp_dealloc*/
	(printfunc)0,		/*tp_print*/
	(getattrfunc)WMWriterNetworkSink_getattr,	/*tp_getattr*/
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
	WMWriterNetworkSinkType__doc__ /* Documentation string */
};

// End of code for WMWriterNetworkSink object 
////////////////////////////////////////////

////////////////////////////////////////////
// LargeInt object 
static char LargeInt_low__doc__[] =
""
;
static PyObject *
LargeInt_low(LargeIntObject *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args,""))return NULL;
	LARGE_INTEGER li;li.QuadPart = self->ob_ival;
	return Py_BuildValue("l",li.LowPart);
}

static char LargeInt_high__doc__[] =
""
;
static PyObject *
LargeInt_high(LargeIntObject *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args,""))return NULL;
	LARGE_INTEGER li;li.QuadPart = self->ob_ival;
	return Py_BuildValue("l",li.HighPart);
}

static struct PyMethodDef LargeInt_methods[] = {
	{"low", (PyCFunction)LargeInt_low, METH_VARARGS, LargeInt_low__doc__},
	{"high", (PyCFunction)LargeInt_high, METH_VARARGS, LargeInt_high__doc__},
	{NULL, (PyCFunction)NULL, 0, NULL}		/* sentinel */
};

static void
LargeInt_dealloc(LargeIntObject *self)
{
	/* XXXX Add your own cleanup code here */
	PyMem_DEL(self);
}

static PyObject *
LargeInt_getattr(LargeIntObject *self, char *name)
{
	/* XXXX Add your own getattr code here */
	return Py_FindMethod(LargeInt_methods, (PyObject *)self, name);
}

static int
LargeInt_compare(LargeIntObject *v, LargeIntObject *w)
{
	LONGLONG i = v->ob_ival;
	LONGLONG j = w->ob_ival;
	return (i < j) ? -1 : (i > j) ? 1 : 0;
}

static int
LargeInt_print(LargeIntObject *v, FILE *fp, int flags)
{
	fprintf(fp, "%I64d", v->ob_ival);
	return 0;
}

static PyObject *
LargeInt_repr(LargeIntObject *v)
{
	char buf[40];
	sprintf(buf, "%I64d", v->ob_ival);
	return PyString_FromString(buf);
}

static long
LargeInt_hash(LargeIntObject *v)
{
	LARGE_INTEGER li;li.QuadPart = v -> ob_ival;
	long x = li.LowPart;
	if (x == -1)
		x = -2;
	return x;
}

static PyObject *
LargeInt_add(LargeIntObject *v, LargeIntObject *w)
{
	LONGLONG a, b, x;
	a = v->ob_ival;
	b = w->ob_ival;
	x = a + b;
	return (PyObject*)newLargeIntObject(x);
}

static PyObject *
LargeInt_sub(LargeIntObject *v, LargeIntObject *w)
{
	LONGLONG a, b, x;
	a = v->ob_ival;
	b = w->ob_ival;
	x = a - b;
	return (PyObject*)newLargeIntObject(x);
}

static PyObject *
LargeInt_mul(LargeIntObject *v, LargeIntObject *w)
{
	LONGLONG a, b, x;
	a = v->ob_ival;
	b = w->ob_ival;
	x = a * b;
	return (PyObject*)newLargeIntObject(x);
}

static PyObject *
LargeInt_div(LargeIntObject *v, LargeIntObject *w)
{
	LONGLONG a, b, x;
	a = v->ob_ival;
	b = w->ob_ival;
	x = a / b;
	return (PyObject*)newLargeIntObject(x);
}

static PyObject *
LargeInt_mod(LargeIntObject *v, LargeIntObject *w)
{
	LONGLONG a, b, x;
	a = v->ob_ival;
	b = w->ob_ival;
	x = a % b;
	return (PyObject*)newLargeIntObject(x);
}

static PyObject *
LargeInt_divmod(LargeIntObject *v, LargeIntObject *w)
{
	LONGLONG a, b, x, y;
	a = v->ob_ival;
	b = w->ob_ival;
	x = a / b;
	y = a % b;
	LargeIntObject *d = newLargeIntObject(x);
	LargeIntObject *m = newLargeIntObject(y);
	PyObject *r = Py_BuildValue("(OO)", d, m);
	Py_DECREF(d);Py_DECREF(m);
	return r;
}

static PyObject *
LargeInt_neg(LargeIntObject *v)
{
	return (PyObject*)newLargeIntObject(-v->ob_ival);
}

static PyObject *
LargeInt_pos(LargeIntObject *v)
{
	Py_INCREF(v);
	return (PyObject *)v;
}

static PyObject *
LargeInt_abs(LargeIntObject *v)
{
	if (v->ob_ival >= 0)
		return LargeInt_pos(v);
	else
		return LargeInt_neg(v);
}

static int
LargeInt_nonzero(LargeIntObject *v)
{
	return v->ob_ival != 0;
}

static PyObject *
LargeInt_invert(LargeIntObject *v)
{
	return (PyObject*)newLargeIntObject(~v->ob_ival);
}

static PyObject *
LargeInt_lshift(LargeIntObject *v,PyIntObject *w)
{
	return (PyObject*)newLargeIntObject(v->ob_ival << w->ob_ival);
}

static PyObject *
LargeInt_rshift(LargeIntObject *v,PyIntObject *w)
{
	return (PyObject*)newLargeIntObject(v->ob_ival >> w->ob_ival);
}

static PyObject *
LargeInt_and(LargeIntObject *v, LargeIntObject *w)
{
	LONGLONG a, b;
	a = v->ob_ival;
	b = w->ob_ival;
	return (PyObject*)newLargeIntObject(a & b);
}

static PyObject *
LargeInt_xor(LargeIntObject *v, LargeIntObject *w)
{
	LONGLONG a, b;
	a = v->ob_ival;
	b = w->ob_ival;
	return (PyObject*)newLargeIntObject(a ^ b);
}

static PyObject *
LargeInt_or(LargeIntObject *v, LargeIntObject *w)
{
	LONGLONG a, b;
	a = v->ob_ival;
	b = w->ob_ival;
	return (PyObject*)newLargeIntObject(a | b);
}

static PyObject *
LargeInt_int(LargeIntObject *v)
{	
	return Py_BuildValue("i",int(v->ob_ival));
}

static PyObject *
LargeInt_long(LargeIntObject *v)
{
	return PyLong_FromLong(long(v->ob_ival));
}

static PyObject *
LargeInt_float(LargeIntObject *v)
{
	return PyFloat_FromDouble(double(v -> ob_ival));
}

static PyObject *
LargeInt_oct(LargeIntObject *v)
{
	char buf[100];
	LONGLONG x = v -> ob_ival;
	sprintf(buf, "O%I64o", x);
	return PyString_FromString(buf);
}

static PyObject *
LargeInt_hex(LargeIntObject *v)
{
	char buf[100];
	LONGLONG x = v -> ob_ival;
	sprintf(buf, "0x%I64x", x);
	return PyString_FromString(buf);
}

static PyNumberMethods LargeInt_as_number = {
	(binaryfunc)LargeInt_add, /*nb_add*/
	(binaryfunc)LargeInt_sub, /*nb_subtract*/
	(binaryfunc)LargeInt_mul, /*nb_multiply*/
	(binaryfunc)LargeInt_div, /*nb_divide*/
	(binaryfunc)LargeInt_mod, /*nb_remainder*/
	(binaryfunc)LargeInt_divmod, /*nb_divmod*/
	(ternaryfunc)0,//LargeInt_pow, /*nb_power*/
	(unaryfunc)LargeInt_neg, /*nb_negative*/
	(unaryfunc)LargeInt_pos, /*nb_positive*/
	(unaryfunc)LargeInt_abs, /*nb_absolute*/
	(inquiry)LargeInt_nonzero, /*nb_nonzero*/
	(unaryfunc)LargeInt_invert, /*nb_invert*/
	(binaryfunc)LargeInt_lshift, /*nb_lshift*/
	(binaryfunc)LargeInt_rshift, /*nb_rshift*/
	(binaryfunc)LargeInt_and, /*nb_and*/
	(binaryfunc)LargeInt_xor, /*nb_xor*/
	(binaryfunc)LargeInt_or, /*nb_or*/
	0,		/*nb_coerce*/
	(unaryfunc)LargeInt_int, /*nb_int*/
	(unaryfunc)LargeInt_long, /*nb_long*/
	(unaryfunc)LargeInt_float, /*nb_float*/
	(unaryfunc)LargeInt_oct, /*nb_oct*/
	(unaryfunc)LargeInt_hex, /*nb_hex*/
};

static char LargeIntType__doc__[] =
""
;

static PyTypeObject LargeIntType = {
	PyObject_HEAD_INIT(&PyType_Type)
	0,				/*ob_size*/
	"LargeInt",			/*tp_name*/
	sizeof(LargeIntObject),		/*tp_basicsize*/
	0,				/*tp_itemsize*/
	/* methods */
	(destructor)LargeInt_dealloc,	/*tp_dealloc*/
	(printfunc)LargeInt_print,		/*tp_print*/
	(getattrfunc)LargeInt_getattr,	/*tp_getattr*/
	(setattrfunc)0,	/*tp_setattr*/
	(cmpfunc)LargeInt_compare, /*tp_compare*/
	(reprfunc)LargeInt_repr,		/*tp_repr*/
	&LargeInt_as_number,/*tp_as_number*/
	0,		/*tp_as_sequence*/
	0,		/*tp_as_mapping*/
	(hashfunc)LargeInt_hash,/*tp_hash*/
	(ternaryfunc)0,		/*tp_call*/
	(reprfunc)0,		/*tp_str*/

	/* Space for future expansion */
	0L,0L,0L,0L,
	LargeIntType__doc__ /* Documentation string */
};

// End of code for LargeInt object 
////////////////////////////////////////////


///////////////////////////////////////////
///////////////////////////////////////////
// MODULE
//

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

static char CreateDDWriter__doc__[] =
""
;
static PyObject *
CreateDDWriter(PyObject *self, PyObject *args)
{
	WMProfileObject *profobj;
	if (!PyArg_ParseTuple(args, "O!",&WMProfileType,&profobj))
		return NULL;	
	
	DDWMWriterObject *obj = newDDWMWriterObject();
	if (obj == NULL)
		return NULL;
	
	HRESULT hr;
	Py_BEGIN_ALLOW_THREADS
	hr = WMCreateWriter(NULL,&obj->pIWMWriter);
	Py_END_ALLOW_THREADS
	if (FAILED(hr)){
		Py_DECREF(obj);
		seterror("CreateDDWriter:WMCreateWriter", hr);
		return NULL;
	}
	hr = obj->pIWMWriter->SetProfile(profobj->pI);
	DWORD cInputs;
	hr = obj->pIWMWriter->GetInputCount(&cInputs);
	for(DWORD i=0;i<cInputs;i++)
		{
		IWMInputMediaProps* pInputProps = NULL;
		hr = obj->pIWMWriter->GetInputProps(i,&pInputProps);
		if(FAILED(hr))
			{
			Py_DECREF(obj);
			seterror("CreateDDWriter:GetInputProps", hr);
			return NULL;
			}
		GUID guidInputType;
		hr = pInputProps->GetType( &guidInputType);
		if(FAILED(hr))
			{
			Py_DECREF(obj);
			seterror("CreateDDWriter:GetType", hr);
			return NULL;
			}
		if(guidInputType == WMMEDIATYPE_Audio)
			{
			obj->pIAudioInputProps = pInputProps;
			obj->dwAudioInputNum = i;
			}
		else if(guidInputType == WMMEDIATYPE_Video)
			{
			obj->pIVideoInputProps = pInputProps;
			obj->dwVideoInputNum = i;
			}
		}
	return (PyObject*)obj;
}


static WORD LowBitPos(DWORD dword)
	{
	DWORD test=1;
	for (WORD i=0;i<32;i++)
		{
		if ( dword & test )
			return i;
		test<<=1;
		}
	return 0;
	}
static WORD HighBitPos(DWORD dword)
	{
	DWORD test=1;
	test<<=31;
	for (WORD i=0;i<32;i++)
		{
		if ( dword & test )
			return (WORD)(31-i);
		test>>=1;
		}
	return 0;
	}

static char CreateDDVideoWMType__doc__[] =
""
;
static PyObject *
CreateDDVideoWMType(PyObject *self, PyObject *args)
{
	PyObject *ddsobj;
	int avgTimePerFrame = 100; // in msecs
	if (!PyArg_ParseTuple(args,"O|i",&ddsobj,&avgTimePerFrame))
		return NULL;
	IDirectDrawSurface *surf = (IDirectDrawSurface *)((UnknownObject*)ddsobj)->pI;

	DDPIXELFORMAT format;
	ZeroMemory(&format,sizeof(format));
	format.dwSize=sizeof(format);
	HRESULT hr = surf->GetPixelFormat(&format);
	if (FAILED(hr)){
		seterror("CreateDDVideoWMType:GetPixelFormat", hr);
		return NULL;
	}
	
	if(format.dwRGBBitCount!=32 && format.dwRGBBitCount!=24 && format.dwRGBBitCount!=16 && format.dwRGBBitCount!=8)
		{
		seterror("Format not supported");
		return NULL;
		}
	
	WORD loREDbit = LowBitPos(format.dwRBitMask);
	WORD hiREDbit = HighBitPos(format.dwRBitMask );
	WORD numREDbits=(WORD)(hiREDbit-loREDbit+1);

	WORD loGREENbit = LowBitPos(format.dwGBitMask);
	WORD hiGREENbit = HighBitPos(format.dwGBitMask);
	WORD numGREENbits=(WORD)(hiGREENbit-loGREENbit+1);

	WORD loBLUEbit  = LowBitPos(format.dwBBitMask);
	WORD hiBLUEbit  = HighBitPos(format.dwBBitMask);
	WORD numBLUEbits=(WORD)(hiBLUEbit-loBLUEbit+1);

	DDSURFACEDESC ddsd;
	ZeroMemory( &ddsd, sizeof(ddsd) );
	ddsd.dwSize = sizeof(ddsd);
	hr = surf->GetSurfaceDesc(&ddsd);
	if (FAILED(hr)){
		seterror("CreateDDVideoWMType:GetSurfaceDesc", hr);
		return NULL;
	}	
	int depth = format.dwRGBBitCount;
	int width = ddsd.dwWidth;
	int height = ddsd.dwHeight;
	int cbFormat = sizeof(WMVIDEOINFOHEADER);
	if(depth==16 && numREDbits==5 && numGREENbits==6 && numBLUEbits==5)
		cbFormat+=3*sizeof(RGBQUAD);
	else if(depth==8)
		cbFormat+=256*sizeof(RGBQUAD);
	
	WMMediaTypeObject *obj = newWMMediaTypeObject();
	if (obj == NULL) return NULL;
	WM_MEDIA_TYPE& mt = *obj->pMediaType;

	DWORD dwSampleSize=width*height*(depth/8);
	LONGLONG atpf=LONGLONG(avgTimePerFrame)*10000;
	double fps = 1000.0/double(avgTimePerFrame);
	DWORD rate = DWORD(fps*dwSampleSize*8.0);

	
	WMVIDEOINFOHEADER* pVideoInfo = (WMVIDEOINFOHEADER*) new BYTE[cbFormat];
	ZeroMemory(pVideoInfo,cbFormat);

	// fill bitmap info header
	BITMAPINFOHEADER* pbmih = &pVideoInfo->bmiHeader;
	pbmih->biSize = sizeof(BITMAPINFOHEADER);
	pbmih->biWidth    = width;
	pbmih->biHeight   = height;
	pbmih->biPlanes   = 1;
	pbmih->biBitCount = depth;
	pbmih->biCompression = BI_RGB;
	pbmih->biSizeImage = 0;
	pbmih->biClrUsed = 0;
	pbmih->biClrImportant = 0;
	if(depth==16 && numREDbits==5 && numGREENbits==6 && numBLUEbits==5)
		{
		pbmih->biCompression = BI_BITFIELDS;
		typedef struct {BITMAPINFOHEADER bmiHeader; DWORD bitMask[3];} _BITMAPINFO;
		_BITMAPINFO *p = (_BITMAPINFO*)&pVideoInfo->bmiHeader;
		p->bitMask[0] = format.dwRBitMask;
		p->bitMask[1] = format.dwGBitMask;
		p->bitMask[2] = format.dwBBitMask;
		}
	else if(depth==8)
		{
		pbmih->biClrUsed = 256;
		pbmih->biClrImportant = 256;
		typedef struct {BITMAPINFOHEADER bmiHeader; PALETTEENTRY bmiColors[256];} _BITMAPINFO;
		_BITMAPINFO *p = (_BITMAPINFO*)&pVideoInfo->bmiHeader;
		HDC hdc = GetDC(NULL);
		GetSystemPaletteEntries(hdc, 0, 256, p->bmiColors);
		ReleaseDC(NULL, hdc);		
		}
	// fill rest of video info
	pVideoInfo->rcSource.left	= 0;
	pVideoInfo->rcSource.top	= 0;
	pVideoInfo->rcSource.right	= width;
	pVideoInfo->rcSource.bottom = height;
	pVideoInfo->rcTarget		= pVideoInfo->rcSource;
	pVideoInfo->dwBitRate		= rate;
	pVideoInfo->dwBitErrorRate	= 0;
	pVideoInfo->AvgTimePerFrame = atpf;
	memcpy(obj->pbBuffer+sizeof(WM_MEDIA_TYPE),pVideoInfo,cbFormat);
	delete[] (BYTE*)pVideoInfo;
	
	mt.majortype = WMMEDIATYPE_Video;
	if(depth==32)
		mt.subtype = WMMEDIASUBTYPE_RGB32;
	else if(depth==24)
		mt.subtype = WMMEDIASUBTYPE_RGB24;
	else if(depth==16)
		{
		if(numREDbits==5 && numGREENbits==5 && numBLUEbits==5)
			mt.subtype = WMMEDIASUBTYPE_RGB555;
		else if(numREDbits==5 && numGREENbits==6 && numBLUEbits==5)
			mt.subtype = WMMEDIASUBTYPE_RGB565;
		}
	else if(depth==8)
		{
		mt.subtype = WMMEDIASUBTYPE_RGB8;
		}
	mt.bFixedSizeSamples = TRUE;
	mt.bTemporalCompression = TRUE;
	mt.lSampleSize = width*height*(depth/8);
	mt.formattype = WMFORMAT_VideoInfo;
	mt.pUnk = NULL;
	mt.cbFormat = cbFormat;
	mt.pbFormat = obj->pbBuffer+sizeof(WM_MEDIA_TYPE);
	
	return (PyObject*)obj;
}


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
static char CreateEditor__doc__[] =
""
;
static PyObject *
CreateEditor(PyObject *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args, ""))
		return NULL;
	
	WMMetadataEditorObject *obj = newWMMetadataEditorObject();
	if (obj == NULL) return NULL;
	
	HRESULT hr;
	Py_BEGIN_ALLOW_THREADS
	hr = WMCreateEditor(&obj->pI);
	Py_END_ALLOW_THREADS
	if (FAILED(hr)){
		Py_DECREF(obj);
		seterror("WMCreateEditor", hr);
		return NULL;
	}
	return (PyObject*)obj;
}

//
static char CreateIndexer__doc__[] =
""
;
static PyObject *
CreateIndexer(PyObject *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args, ""))
		return NULL;
	
	WMIndexerObject *obj = newWMIndexerObject();
	if (obj == NULL) return NULL;
	
	HRESULT hr;
	Py_BEGIN_ALLOW_THREADS
	hr = WMCreateIndexer(&obj->pI);
	Py_END_ALLOW_THREADS
	if (FAILED(hr)){
		Py_DECREF(obj);
		seterror("WMCreateIndexer", hr);
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

//
static char CreateWriterFileSink__doc__[] =
""
;
static PyObject *
CreateWriterFileSink(PyObject *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args, ""))
		return NULL;
	
	WMWriterFileSinkObject *obj = newWMWriterFileSinkObject();
	if (obj == NULL)
		return NULL;
	
	HRESULT hr;
	Py_BEGIN_ALLOW_THREADS
	hr = WMCreateWriterFileSink(&obj->pI);
	Py_END_ALLOW_THREADS
	if (FAILED(hr)){
		Py_DECREF(obj);
		seterror("WMCreateWriterFileSink", hr);
		return NULL;
	}
	return (PyObject*)obj;
}

//
static char CreateWriterNetworkSink__doc__[] =
""
;
static PyObject *
CreateWriterNetworkSink(PyObject *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args, ""))
		return NULL;
	
	WMWriterNetworkSinkObject *obj = newWMWriterNetworkSinkObject();
	if (obj == NULL)
		return NULL;
	
	HRESULT hr;
	Py_BEGIN_ALLOW_THREADS
	hr = WMCreateWriterNetworkSink(&obj->pI);
	Py_END_ALLOW_THREADS
	if (FAILED(hr)){
		Py_DECREF(obj);
		seterror("WMCreateWriterNetworkSink", hr);
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

static char CreatePyReaderCallbackAdvanced__doc__[] =
""
;
static PyObject *
CreatePyReaderCallbackAdvanced(PyObject *self, PyObject *args)
{
	PyObject *pycbobj;
	if (!PyArg_ParseTuple(args,"O",&pycbobj))
		return NULL;
	
	WMPyReaderCallbackObject *obj = newWMPyReaderCallbackObject();
	if (obj == NULL)
		return NULL;
	HRESULT hr;
	hr = WMCreatePyReaderCallbackAdvanced(pycbobj,&obj->pI);
	if (FAILED(hr)){
		Py_DECREF(obj);
		seterror("CreatePyReaderCallbackAdvanced", hr);
		return NULL;
	}
	return (PyObject*)obj;
}


static char large_int__doc__[] =
""
;
static PyObject *
large_int(PyObject *self, PyObject *args)
{
	char *psz;
	LONGLONG ll;
	if (!PyArg_ParseTuple(args,"s",&psz))
		{
		PyErr_Clear();
		long hi,low;
		if (!PyArg_ParseTuple(args,"ll",&hi,&low))
			{
			PyErr_Clear();
			long lv=0;
			if (!PyArg_ParseTuple(args,"l",&lv))
				return NULL;
			ll = (LONGLONG)lv;
			}
		else
			{
			LARGE_INTEGER li;li.HighPart=hi;li.LowPart=low;
			ll = li.QuadPart;
			}
		}
	else if(sscanf(psz,"%I64d",&ll)==EOF)
		{
		seterror("large_int_from_string failed");
		return NULL;
		}
	LargeIntObject *obj = newLargeIntObject(ll);
	if (obj == NULL)return NULL;
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
	//PyCallbackBlock::free();	
	CoUninitialize();
	Py_INCREF(Py_None);
	return Py_None;
	}

static struct PyMethodDef wmfapi_methods[] = {
	{"CreateWriter", (PyCFunction)CreateWriter, METH_VARARGS, CreateWriter__doc__},
	{"CreateDDWriter", (PyCFunction)CreateDDWriter, METH_VARARGS, CreateDDWriter__doc__},
	{"CreateDDVideoWMType", (PyCFunction)CreateDDVideoWMType, METH_VARARGS, CreateDDVideoWMType__doc__},
	{"CreateReader", (PyCFunction)CreateReader, METH_VARARGS, CreateReader__doc__},
	{"CreateEditor", (PyCFunction)CreateEditor, METH_VARARGS, CreateEditor__doc__},
	{"CreateIndexer", (PyCFunction)CreateIndexer, METH_VARARGS, CreateIndexer__doc__},
	{"CreateProfileManager", (PyCFunction)CreateProfileManager, METH_VARARGS, CreateProfileManager__doc__},
	{"CreateWriterFileSink", (PyCFunction)CreateWriterFileSink, METH_VARARGS, CreateWriterFileSink__doc__},
	{"CreateWriterNetworkSink", (PyCFunction)CreateWriterNetworkSink, METH_VARARGS, CreateWriterNetworkSink__doc__},
	{"CreatePyReaderCallback", (PyCFunction)CreatePyReaderCallback, METH_VARARGS, CreatePyReaderCallback__doc__},
	{"CreatePyReaderCallbackAdvanced", (PyCFunction)CreatePyReaderCallbackAdvanced, METH_VARARGS, CreatePyReaderCallbackAdvanced__doc__},
	{"large_int", (PyCFunction)large_int, METH_VARARGS, large_int__doc__},
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

struct enumentry {char* s;int n;};

static struct enumentry _wmt_attr_datatype[] ={
	{"WMT_TYPE_DWORD",WMT_TYPE_DWORD},
	{"WMT_TYPE_STRING",WMT_TYPE_STRING},
	{"WMT_TYPE_BINARY",WMT_TYPE_BINARY},
	{"WMT_TYPE_BOOL",WMT_TYPE_BOOL},
	{"WMT_TYPE_QWORD",WMT_TYPE_QWORD},
	{"WMT_TYPE_WORD",WMT_TYPE_WORD},
	{"WMT_TYPE_GUID",WMT_TYPE_GUID},
	{NULL,0}
	};

static struct enumentry _wmt_status[] ={
    {"WMT_ERROR",WMT_ERROR},
    {"WMT_OPENED",WMT_OPENED},
    {"WMT_BUFFERING_START",WMT_BUFFERING_START},
    {"WMT_BUFFERING_STOP",WMT_BUFFERING_STOP},
    {"WMT_EOF",WMT_EOF},
    {"WMT_END_OF_FILE",WMT_END_OF_FILE},
	{"WMT_END_OF_SEGMENT",WMT_END_OF_SEGMENT},
    {"WMT_END_OF_STREAMING",WMT_END_OF_STREAMING},
    {"WMT_LOCATING",WMT_LOCATING},
    {"WMT_CONNECTING",WMT_CONNECTING},
	{"WMT_NO_RIGHTS",WMT_NO_RIGHTS},
    {"WMT_MISSING_CODEC",WMT_MISSING_CODEC},
    {"WMT_STARTED",WMT_STARTED},
    {"WMT_STOPPED",WMT_STOPPED},
    {"WMT_CLOSED",WMT_CLOSED},
    {"WMT_STRIDING",WMT_STRIDING},
    {"WMT_TIMER",WMT_TIMER},
    {"WMT_INDEX_PROGRESS",WMT_INDEX_PROGRESS},
	{NULL,0}
	};

static struct enumentry _wmt_rights[] ={
    {"WMT_RIGHT_PLAYBACK", WMT_RIGHT_PLAYBACK},
	{"WMT_RIGHT_COPY_TO_NON_SDMI_DEVICE", WMT_RIGHT_COPY_TO_NON_SDMI_DEVICE},
	{"WMT_RIGHT_COPY_TO_CD",WMT_RIGHT_COPY_TO_CD},
	{"WMT_RIGHT_COPY_TO_SDMI_DEVICE", WMT_RIGHT_COPY_TO_SDMI_DEVICE},
	{"WMT_RIGHT_ONE_TIME", WMT_RIGHT_ONE_TIME},
	{NULL,0}
	};

static struct enumentry _wmt_stream_selection[] ={
    {"WMT_OFF", WMT_OFF},
	{"WMT_CLEANPOINT_ONLY", WMT_CLEANPOINT_ONLY},
	{"WMT_ON", WMT_ON},
	{NULL,0}
	};

static struct enumentry _wmt_version[] ={
    {"WMT_VER_4_0", WMT_VER_4_0},
    {"WMT_VER_7_0", WMT_VER_7_0},
	{NULL,0}
	};

static struct enumentry _wmt_net_protocol[] ={
    {"WMT_PROTOCOL_HTTP", WMT_PROTOCOL_HTTP},
	{NULL,0x0}
	};

// add symbolic constants of enum
static int 
SetItemEnum(PyObject *d,enumentry e[])
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

// add enum as a dictionary <number> -> <string>
static int 
SetItemEnumStrings(PyObject *dict,const char *szname, enumentry e[])
	{
	PyObject *x, *y;
	PyObject *d = PyDict_New();
	if(d == NULL) return -1;
	for(int i=0;e[i].s;i++)
		{
		x = PyInt_FromLong((long)e[i].n);
		y = PyString_FromString((char*)e[i].s);
		if (x == NULL || PyDict_SetItem(d, x, y) < 0)
			return -1;
		Py_DECREF(x);
		Py_DECREF(y);
		}
	int ix = PyDict_SetItemString(dict, (char*)szname, d);
	Py_DECREF(d);
	return ix;
	}

#define FATAL_ERROR_IF(exp) if(exp){Py_FatalError("can't initialize module wmfapi");return;}	

static char wmfapi_module_documentation[] =
"Windows Media Format API"
;

extern "C" __declspec(dllexport)
void initwmfapi()
{
	PyObject *m, *d, *x;
	bool bPyErrOccurred = false;
	
	// Create the module and add the functions
	m = Py_InitModule4("wmfapi", wmfapi_methods,
		wmfapi_module_documentation,
		(PyObject*)NULL,PYTHON_API_VERSION);

	/// add 'error'
	d = PyModule_GetDict(m);
	ErrorObject = PyString_FromString("wmfapi.error");
	PyDict_SetItemString(d, "error", ErrorObject);

	// add symbolic WM GUIDs
	for(int i=0;wmguids[i].p && wmguids[i].s && !bPyErrOccurred;i++)
		{
		x = (PyObject*)newGUIDObject(wmguids[i].p);
		FATAL_ERROR_IF(x == NULL || PyDict_SetItemString(d, wmguids[i].s, x) < 0)
		Py_DECREF(x);
		}
		
	// add symbolic constants of enum
	FATAL_ERROR_IF(SetItemEnum(d,_wmt_attr_datatype)<0)
	FATAL_ERROR_IF(SetItemEnum(d,_wmt_status)<0)
	FATAL_ERROR_IF(SetItemEnum(d,_wmt_rights)<0)
	FATAL_ERROR_IF(SetItemEnum(d,_wmt_stream_selection)<0)
	FATAL_ERROR_IF(SetItemEnum(d,_wmt_version)<0)
	FATAL_ERROR_IF(SetItemEnum(d,_wmt_net_protocol)<0)

	// add enum as a dictionary <number> -> <string>
	FATAL_ERROR_IF(SetItemEnumStrings(d,"wmt_attr_datatype_str",_wmt_attr_datatype)<0)
	FATAL_ERROR_IF(SetItemEnumStrings(d,"wmt_status_str",_wmt_status)<0)
	FATAL_ERROR_IF(SetItemEnumStrings(d,"wmt_rights_str",_wmt_rights)<0)

	PyCallbackBlock::init();	
	
	/* Check for errors */
	if (PyErr_Occurred())
		Py_FatalError("can't initialize module wmfapi");
}



