
/*************************************************************************
Copyright 1991-1999 by Oratrix Development BV, Amsterdam, The Netherlands.

                        All Rights Reserved

**************************************************************************/

#include "Python.h"

#include <streams.h>
#include <objbase.h>
#include <stdio.h>
#include <UUIDS.H> // CLSID_FilterGraph,...

#pragma comment (lib,"winmm.lib")
#pragma comment (lib,"amstrmid.lib")
#pragma comment (lib,"guids.lib")
#pragma comment (lib,"strmbase.lib")

// ++ streams support
#include <amstream.h>

#define  OATRUE (-1)
#define  OAFALSE (0)

#include <initguid.h>
#include "dscom.h"

static PyObject *ErrorObject;

#define RELEASE(x) if(x) x->Release();x=NULL;

#include "mtpycall.h"
PyInterpreterState*
PyCallbackBlock::s_interpreterState = NULL;

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
	PyErr_Format(ErrorObject, "%s failed (code = %X).\n%s", 
		funcname, hr, pszmsg);
	LocalFree(pszmsg);
}

void seterror(const char *msg){PyErr_SetString(ErrorObject, msg);}


/* Declarations for objects of type GraphBuilder */

typedef struct {
	PyObject_HEAD
	/* XXXX Add your own stuff here */
	IGraphBuilder* pGraphBuilder;
} GraphBuilderObject;

staticforward PyTypeObject GraphBuilderType;

static GraphBuilderObject *
newGraphBuilderObject()
{
	GraphBuilderObject *self;

	self = PyObject_NEW(GraphBuilderObject, &GraphBuilderType);
	if (self == NULL)
		return NULL;
	self->pGraphBuilder = NULL;
	/* XXXX Add your own initializers here */
	return self;
}

typedef struct {
	PyObject_HEAD
	/* XXXX Add your own stuff here */
	IBasicVideo* pI;
} BasicVideoObject;

staticforward PyTypeObject BasicVideoType;

static BasicVideoObject *
newBasicVideoObject()
{
	BasicVideoObject *self = PyObject_NEW(BasicVideoObject, &BasicVideoType);
	if (self == NULL) return NULL;
	self->pI = NULL;
	/* XXXX Add your own initializers here */
	return self;
}


typedef struct {
	PyObject_HEAD
	/* XXXX Add your own stuff here */
	IBaseFilter* pFilter;
} BaseFilterObject;

staticforward PyTypeObject BaseFilterType;

static BaseFilterObject *
newBaseFilterObject()
{
	BaseFilterObject *self;

	self = PyObject_NEW(BaseFilterObject, &BaseFilterType);
	if (self == NULL)
		return NULL;
	self->pFilter = NULL;
	/* XXXX Add your own initializers here */
	return self;
}



typedef struct {
	PyObject_HEAD
	/* XXXX Add your own stuff here */
	IPin* pPin;
} PinObject;

staticforward PyTypeObject PinType;

static PinObject *
newPinObject()
{
	PinObject *self;

	self = PyObject_NEW(PinObject, &PinType);
	if (self == NULL)
		return NULL;
	self->pPin = NULL;
	/* XXXX Add your own initializers here */
	return self;
}


typedef struct {
	PyObject_HEAD
	/* XXXX Add your own stuff here */
	IEnumPins* pPins;
} EnumPinsObject;

staticforward PyTypeObject EnumPinsType;

static EnumPinsObject *
newEnumPinsObject()
{
	EnumPinsObject *self;

	self = PyObject_NEW(EnumPinsObject, &EnumPinsType);
	if (self == NULL)
		return NULL;
	self->pPins = NULL;
	/* XXXX Add your own initializers here */
	return self;
}


typedef struct {
	PyObject_HEAD
	/* XXXX Add your own stuff here */
	IFileSinkFilter* pFilter;
} FileSinkFilterObject;

staticforward PyTypeObject FileSinkFilterType;


static FileSinkFilterObject *
newFileSinkFilterObject()
{
	FileSinkFilterObject *self;

	self = PyObject_NEW(FileSinkFilterObject, &FileSinkFilterType);
	if (self == NULL)
		return NULL;
	self->pFilter = NULL;
	/* XXXX Add your own initializers here */
	return self;
}

//
typedef struct {
	PyObject_HEAD
	/* XXXX Add your own stuff here */
	IMediaControl* pCtrl;
} MediaControlObject;

staticforward PyTypeObject MediaControlType;


static MediaControlObject *
newMediaControlObject()
{
	MediaControlObject *self;

	self = PyObject_NEW(MediaControlObject, &MediaControlType);
	if (self == NULL)
		return NULL;
	self->pCtrl = NULL;
	/* XXXX Add your own initializers here */
	return self;
}
//


//
typedef struct {
	PyObject_HEAD
	/* XXXX Add your own stuff here */
	IVideoWindow* pI;
} VideoWindowObject;

staticforward PyTypeObject VideoWindowType;


static VideoWindowObject *
newVideoWindowObject()
{
	VideoWindowObject *self;

	self = PyObject_NEW(VideoWindowObject, &VideoWindowType);
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
	IMediaEventEx* pI;
} MediaEventExObject;

staticforward PyTypeObject MediaEventExType;


static MediaEventExObject *
newMediaEventExObject()
{
	MediaEventExObject *self;

	self = PyObject_NEW(MediaEventExObject, &MediaEventExType);
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
	IRealConverter* pRealConverter;
} RealConverterObject;

staticforward PyTypeObject RealConverterType;

static RealConverterObject *
newRealConverterObject()
{
	RealConverterObject *self;

	self = PyObject_NEW(RealConverterObject, &RealConverterType);
	if (self == NULL)
		return NULL;
	self->pRealConverter = NULL;
	/* XXXX Add your own initializers here */
	return self;
}

typedef struct {
	PyObject_HEAD
	/* XXXX Add your own stuff here */
	IWMConverter* pWMConverter;
} WMConverterObject;

staticforward PyTypeObject WMConverterType;

static WMConverterObject *
newWMConverterObject()
{
	WMConverterObject *self;

	self = PyObject_NEW(WMConverterObject, &WMConverterType);
	if (self == NULL)
		return NULL;
	self->pWMConverter = NULL;
	/* XXXX Add your own initializers here */
	return self;
}


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


typedef struct {
	PyObject_HEAD
	/* XXXX Add your own stuff here */
	IMediaPosition* pI;
} MediaPositionObject;

staticforward PyTypeObject MediaPositionType;

static MediaPositionObject *
newMediaPositionObject()
{
	MediaPositionObject *self;

	self = PyObject_NEW(MediaPositionObject, &MediaPositionType);
	if (self == NULL)
		return NULL;
	self->pI = NULL;
	/* XXXX Add your own initializers here */
	return self;
}

 
typedef struct {
	PyObject_HEAD
	/* XXXX Add your own stuff here */
	IEnumFilters* pI;
} EnumFiltersObject;

staticforward PyTypeObject EnumFiltersType;

static EnumFiltersObject *
newEnumFiltersObject()
{
	EnumFiltersObject *self;

	self = PyObject_NEW(EnumFiltersObject, &EnumFiltersType);
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
	IPyListener *pI;
} PyRenderingListenerObject;

staticforward PyTypeObject PyRenderingListenerType;

static PyRenderingListenerObject *
newPyRenderingListenerObject()
{
	PyRenderingListenerObject *self;
	self = PyObject_NEW(PyRenderingListenerObject, &PyRenderingListenerType);
	if (self == NULL) return NULL;
	self->pI = NULL;
	return self;
}

//////////////////
// Streams

typedef struct {
	PyObject_HEAD
	/* XXXX Add your own stuff here */
	// use a specialization of IMultiMediaStream
	IAMMultiMediaStream *pI; // 
} MultiMediaStreamObject;

staticforward PyTypeObject MultiMediaStreamType;

static MultiMediaStreamObject *
newMultiMediaStreamObject()
{
	MultiMediaStreamObject *self;

	self = PyObject_NEW(MultiMediaStreamObject, &MultiMediaStreamType);
	if (self == NULL)
		return NULL;
	self->pI = NULL;
	/* XXXX Add your own initializers here */
	return self;
}

typedef struct {
	PyObject_HEAD
	/* XXXX Add your own stuff here */
	IMediaStream *pI;
} MediaStreamObject;

staticforward PyTypeObject MediaStreamType;

static MediaStreamObject *
newMediaStreamObject()
{
	MediaStreamObject *self;
	self = PyObject_NEW(MediaStreamObject, &MediaStreamType);
	if (self == NULL)
		return NULL;
	self->pI = NULL;
	/* XXXX Add your own initializers here */
	return self;
}

typedef struct {
	PyObject_HEAD
	/* XXXX Add your own stuff here */
	IDirectDrawMediaStream *pI;
} DirectDrawMediaStreamObject;

staticforward PyTypeObject DirectDrawMediaStreamType;

static DirectDrawMediaStreamObject *
newDirectDrawMediaStreamObject()
{
	DirectDrawMediaStreamObject *self;
	self = PyObject_NEW(DirectDrawMediaStreamObject, &DirectDrawMediaStreamType);
	if (self == NULL)
		return NULL;
	self->pI = NULL;
	/* XXXX Add your own initializers here */
	return self;
}

typedef struct {
	PyObject_HEAD
	/* XXXX Add your own stuff here */
	IDirectDrawStreamSample *pI;
} DirectDrawStreamSampleObject;

staticforward PyTypeObject DirectDrawStreamSampleType;

static DirectDrawStreamSampleObject *
newDirectDrawStreamSampleObject()
{
	DirectDrawStreamSampleObject *self;
	self = PyObject_NEW(DirectDrawStreamSampleObject, &DirectDrawStreamSampleType);
	if (self == NULL)
		return NULL;
	self->pI = NULL;
	/* XXXX Add your own initializers here */
	return self;
}

typedef struct {
	PyObject_HEAD
	/* XXXX Add your own stuff here */
	DDSURFACEDESC sd;
} DDSURFACEDESCObject;


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


////////////////////////////////////////////////////

static char GraphBuilder_AddSourceFilter__doc__[] =
""
;


static PyObject *
GraphBuilder_AddSourceFilter(GraphBuilderObject *self, PyObject *args)
{
	HRESULT res;
	char *pszFile;
	BaseFilterObject *obj;
	if (!PyArg_ParseTuple(args, "s", &pszFile))
		return NULL;
	obj = newBaseFilterObject();
	WCHAR wPath[MAX_PATH];
	MultiByteToWideChar(CP_ACP,0,pszFile,-1,wPath,MAX_PATH);
	Py_BEGIN_ALLOW_THREADS
	res = self->pGraphBuilder->AddSourceFilter(wPath,L"File reader",&obj->pFilter);
	Py_END_ALLOW_THREADS
	if (FAILED(res)) {
		seterror("GraphBuilder_AddSourceFilter", res);
		obj->pFilter=NULL;
		Py_DECREF(obj);
		return NULL;
	}
	return (PyObject *) obj;
}

static char GraphBuilder_AddFilter__doc__[] =
""
;

static PyObject *
GraphBuilder_AddFilter(GraphBuilderObject *self, PyObject *args)
{
	HRESULT res;
	char *psz;
	BaseFilterObject *obj;
	if (!PyArg_ParseTuple(args, "Os", &obj, &psz))
		return NULL;

	WCHAR wsz[MAX_PATH];
	MultiByteToWideChar(CP_ACP,0,psz,-1,wsz,MAX_PATH);
	Py_BEGIN_ALLOW_THREADS
	res = self->pGraphBuilder->AddFilter(obj->pFilter,wsz);
	Py_END_ALLOW_THREADS
	if (FAILED(res)) {
		seterror("GraphBuilder_AddFilter", res);
		return NULL;
	}
	Py_INCREF(Py_None);
	return Py_None;
}


static char GraphBuilder_EnumFilters__doc__[] =
""
;

static PyObject *
GraphBuilder_EnumFilters(GraphBuilderObject *self, PyObject *args)
{
	HRESULT res;
	if (!PyArg_ParseTuple(args, ""))
		return NULL;
	EnumFiltersObject *obj = newEnumFiltersObject();
	Py_BEGIN_ALLOW_THREADS
	res = self->pGraphBuilder->EnumFilters(&obj->pI);
	Py_END_ALLOW_THREADS
	if (FAILED(res)) {
		seterror("GraphBuilder_EnumPins", res);
		Py_DECREF(obj);
		obj->pI=NULL;
		return NULL;
	}
	return (PyObject *) obj;
}


static char GraphBuilder_Render__doc__[] =
""
;

static PyObject *
GraphBuilder_Render(GraphBuilderObject *self, PyObject *args)
{
	HRESULT res;
	PinObject *obj;
	if (!PyArg_ParseTuple(args, "O", &obj))
		return NULL;
	Py_BEGIN_ALLOW_THREADS
	res = self->pGraphBuilder->Render(obj->pPin);
	Py_END_ALLOW_THREADS
	if (FAILED(res)) {
		seterror("GraphBuilder_Render", res);
		return NULL;
	}
	Py_INCREF(Py_None);
	return Py_None;
}

static char GraphBuilder_Connect__doc__[] =
""
;

static PyObject *
GraphBuilder_Connect(GraphBuilderObject *self, PyObject *args)
{
	HRESULT res;
	PinObject *pinOut,*pinIn;
	if (!PyArg_ParseTuple(args, "OO", &pinOut,&pinIn))
		return NULL;
	Py_BEGIN_ALLOW_THREADS
	res = self->pGraphBuilder->Connect(pinOut->pPin,pinIn->pPin);
	Py_END_ALLOW_THREADS
	if (FAILED(res)) {
		seterror("GraphBuilder_Connect", res);
		return NULL;
	}
	Py_INCREF(Py_None);
	return Py_None;
}



static char GraphBuilder_QueryIMediaControl__doc__[] =
""
;

static PyObject *
GraphBuilder_QueryIMediaControl(GraphBuilderObject *self, PyObject *args)
{
	HRESULT res;
	if (!PyArg_ParseTuple(args, ""))
		return NULL;
	MediaControlObject *obj = newMediaControlObject();
	Py_BEGIN_ALLOW_THREADS
	res = self->pGraphBuilder->QueryInterface(IID_IMediaControl, (void **) &obj->pCtrl);
	Py_END_ALLOW_THREADS
	if (FAILED(res)) {
		seterror("GraphBuilder_QueryIMediaControl", res);
		obj->pCtrl=NULL;
		Py_DECREF(obj);
		return NULL;
	}
	return (PyObject *) obj;
}


static char GraphBuilder_QueryIMediaPosition__doc__[] =
""
;
static PyObject *
GraphBuilder_QueryIMediaPosition(GraphBuilderObject *self, PyObject *args)
{
	HRESULT res;
	if (!PyArg_ParseTuple(args, ""))
		return NULL;
	MediaPositionObject *obj = newMediaPositionObject();
	Py_BEGIN_ALLOW_THREADS
	res = self->pGraphBuilder->QueryInterface(IID_IMediaPosition, (void **) &obj->pI);
	Py_END_ALLOW_THREADS
	if (FAILED(res)) {
		seterror("GraphBuilder_QueryIMediaPosition", res);
		obj->pI=NULL;
		Py_DECREF(obj);
		return NULL;
	}
	return (PyObject *) obj;
}

static char GraphBuilder_QueryIVideoWindow__doc__[] =
""
;
static PyObject *
GraphBuilder_QueryIVideoWindow(GraphBuilderObject *self, PyObject *args)
{
	HRESULT res;
	if (!PyArg_ParseTuple(args, ""))
		return NULL;
	VideoWindowObject *obj = newVideoWindowObject();
	Py_BEGIN_ALLOW_THREADS
	res = self->pGraphBuilder->QueryInterface(IID_IVideoWindow, (void **) &obj->pI);
	Py_END_ALLOW_THREADS
	if (FAILED(res)) {
		seterror("GraphBuilder_QueryIVideoWindow", res);
		obj->pI=NULL;
		Py_DECREF(obj);
		return NULL;
	}
	return (PyObject *) obj;
}

static char GraphBuilder_QueryIBasicVideo__doc__[] =
""
;
static PyObject *
GraphBuilder_QueryIBasicVideo(GraphBuilderObject *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args, ""))
		return NULL;
	HRESULT hr;
	BasicVideoObject *obj = newBasicVideoObject();
	Py_BEGIN_ALLOW_THREADS
	hr = self->pGraphBuilder->QueryInterface(IID_IBasicVideo, (void **)&obj->pI);
	Py_END_ALLOW_THREADS
	if (FAILED(hr)) {
		seterror("GraphBuilder_QueryIBasicVideo", hr);
		obj->pI = NULL;
		Py_DECREF(obj);
		return NULL;
	}
	return (PyObject *) obj;
}


static char GraphBuilder_QueryIMediaEventEx__doc__[] =
""
;
static PyObject *
GraphBuilder_QueryIMediaEventEx(GraphBuilderObject *self, PyObject *args)
{
	HRESULT res;
	if (!PyArg_ParseTuple(args, ""))
		return NULL;
	MediaEventExObject *obj = newMediaEventExObject();
	Py_BEGIN_ALLOW_THREADS
	res = self->pGraphBuilder->QueryInterface(IID_IMediaEventEx, (void **) &obj->pI);
	Py_END_ALLOW_THREADS
	if (FAILED(res)) {
		seterror("GraphBuilder_QueryIMediaEventEx", res);
		obj->pI=NULL;
		Py_DECREF(obj);
		return NULL;
	}
	return (PyObject *) obj;
}
	
	
static char GraphBuilder_WaitForCompletion__doc__[] =
""
;

static PyObject *
GraphBuilder_WaitForCompletion(GraphBuilderObject *self, PyObject *args)
{
	HRESULT res;
	long msTimeout=INFINITE;
	if (!PyArg_ParseTuple(args, "|l",&msTimeout))
		return NULL;

    IMediaEventEx *pME;
	res=self->pGraphBuilder->QueryInterface(IID_IMediaEventEx, (void **) &pME);
	if (FAILED(res)) {
		seterror("GraphBuilder_WaitForCompletion", res);
		return NULL;
	}
	long evCode=0;
	Py_BEGIN_ALLOW_THREADS
	res=pME->WaitForCompletion(msTimeout,&evCode);
	Py_END_ALLOW_THREADS
	pME->Release();
	
	// res is S_OK or E_ABORT 
	// evCode is:
	//		EC_COMPLETE  Operation completed.  
	//		EC_ERRORABORT  Error. Playback can't continue.  
	//		EC_USERABORT  User terminated the operation.  
	//		Zero Operation has not completed.  
	int ret=(res==S_OK && evCode!=0)?1:0; 
	return Py_BuildValue("i", ret);
}


//////////
// Convert some std file references to the windows media form
// 1. file:///D|/<filepath>
// 2. file:/D|/<filepath>
// 3. file:////<filepath>
// 4. file:////<drive>:\<filepat> 
static void ConvToWindowsMediaUrl(char *pszUrl)
	{
	int l = strlen(pszUrl);
	if(strncmp(pszUrl,"file:////",9)==0 && l>11 && pszUrl[10]==':')
		{
		char *ps = pszUrl+9;
		char *pd = pszUrl;
		while(*ps){
			if(*ps=='/'){*pd++='\\';ps++;}
			else {*pd++ = *ps++;}
			}
		*pd='\0';
		}
	else if(strncmp(pszUrl,"file:////",9)==0 && l>9 && strstr(pszUrl,"|")==NULL) // UNC
		{
		pszUrl[0]='\\';pszUrl[1]='\\';
		char *ps = pszUrl+9;
		char *pd = pszUrl+2;
		while(*ps){
			if(*ps=='/'){*pd++='\\';ps++;}
			else {*pd++ = *ps++;}
			}
		*pd='\0';
		}
	else if(strncmp(pszUrl,"file:///",8)==0 && l>10 && pszUrl[9]=='|')
		{
		pszUrl[0]=pszUrl[8];
		pszUrl[1]=':';
		char *ps = pszUrl+10;
		char *pd = pszUrl+2;
		while(*ps){
			if(*ps=='/'){*pd++='\\';ps++;}
			else {*pd++ = *ps++;}
			}
		*pd='\0';
		}
	else if(strncmp(pszUrl,"file:/",6)==0 && l>8 && pszUrl[7]=='|')
		{
		pszUrl[0]=pszUrl[6];
		pszUrl[1]=':';
		char *ps = pszUrl+8;
		char *pd = pszUrl+2;
		while(*ps){
			if(*ps=='/'){*pd++='\\';ps++;}
			else {*pd++ = *ps++;}
			}
		*pd='\0';
		}
	//else no change
	}

//////////
static char GraphBuilder_RenderFile__doc__[] =
""
;

static PyObject *
GraphBuilder_RenderFile(GraphBuilderObject *self, PyObject *args)
{
	HRESULT res;
	char *psz;
	if (!PyArg_ParseTuple(args, "s", &psz))
		return NULL;
	char buf[MAX_PATH];
	strcpy(buf,psz);
	ConvToWindowsMediaUrl(buf);
	WCHAR wsz[MAX_PATH];
	MultiByteToWideChar(CP_ACP,0,buf,-1,wsz,MAX_PATH);
	Py_BEGIN_ALLOW_THREADS
	res = self->pGraphBuilder->RenderFile(wsz,NULL);
	Py_END_ALLOW_THREADS
	if (FAILED(res)) {
		char sz[MAX_PATH+80]="GraphBuilder_RenderFile ";
		strcat(sz,buf);
		seterror(sz, res);
		return NULL;
	}
	Py_INCREF(Py_None);
	return Py_None;
}



static char GraphBuilder_FindFilterByName__doc__[] =
""
;

static PyObject *
GraphBuilder_FindFilterByName(GraphBuilderObject *self, PyObject *args)
{
	HRESULT res;
	char *psz;
	BaseFilterObject *obj;
	if (!PyArg_ParseTuple(args, "s", &psz))
		return NULL;
	obj = newBaseFilterObject();
	WCHAR wsz[MAX_PATH];
	MultiByteToWideChar(CP_ACP,0,psz,-1,wsz,MAX_PATH);
	Py_BEGIN_ALLOW_THREADS
	res = self->pGraphBuilder->FindFilterByName(wsz,&obj->pFilter);
	Py_END_ALLOW_THREADS
	if (FAILED(res)) {
		seterror("GraphBuilder_AddSourceFilter", res);
		obj->pFilter=NULL;
		Py_DECREF(obj);
		return NULL;
	}
	return (PyObject *) obj;
}



static char GraphBuilder_RemoveFilter__doc__[] =
""
;

static PyObject *
GraphBuilder_RemoveFilter(GraphBuilderObject *self, PyObject *args)
{
	HRESULT res;
	BaseFilterObject *obj;
	if (!PyArg_ParseTuple(args, "O", &obj))
		return NULL;
	Py_BEGIN_ALLOW_THREADS
	res = self->pGraphBuilder->RemoveFilter(obj->pFilter);
	Py_END_ALLOW_THREADS
	if (FAILED(res)) {
		seterror("GraphBuilder_RemoveFilter", res);
		return NULL;
	}
	Py_INCREF(Py_None);
	return Py_None;
}

static char GraphBuilder_Release__doc__[] =
""
;

static PyObject *
GraphBuilder_Release(GraphBuilderObject *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args, ""))
		return NULL;
	Py_BEGIN_ALLOW_THREADS
	RELEASE(self->pGraphBuilder);
	Py_END_ALLOW_THREADS
	Py_INCREF(Py_None);
	return Py_None;
}

static struct PyMethodDef GraphBuilder_methods[] = {
	{"AddSourceFilter", (PyCFunction)GraphBuilder_AddSourceFilter, METH_VARARGS, GraphBuilder_AddSourceFilter__doc__},
	{"AddFilter", (PyCFunction)GraphBuilder_AddFilter, METH_VARARGS, GraphBuilder_AddFilter__doc__},
	{"Render", (PyCFunction)GraphBuilder_Render, METH_VARARGS, GraphBuilder_Render__doc__},
	{"QueryIMediaControl", (PyCFunction)GraphBuilder_QueryIMediaControl, METH_VARARGS, GraphBuilder_QueryIMediaControl__doc__},
	{"WaitForCompletion", (PyCFunction)GraphBuilder_WaitForCompletion, METH_VARARGS, GraphBuilder_WaitForCompletion__doc__},
	{"RenderFile", (PyCFunction)GraphBuilder_RenderFile, METH_VARARGS, GraphBuilder_RenderFile__doc__},
	{"FindFilterByName", (PyCFunction)GraphBuilder_FindFilterByName, METH_VARARGS, GraphBuilder_FindFilterByName__doc__},
	{"RemoveFilter", (PyCFunction)GraphBuilder_RemoveFilter, METH_VARARGS, GraphBuilder_RemoveFilter__doc__},
	{"QueryIMediaPosition", (PyCFunction)GraphBuilder_QueryIMediaPosition, METH_VARARGS, GraphBuilder_QueryIMediaPosition__doc__},
	{"QueryIVideoWindow", (PyCFunction)GraphBuilder_QueryIVideoWindow, METH_VARARGS, GraphBuilder_QueryIVideoWindow__doc__},
	{"QueryIBasicVideo", (PyCFunction)GraphBuilder_QueryIBasicVideo, METH_VARARGS, GraphBuilder_QueryIBasicVideo__doc__},
	{"QueryIMediaEventEx", (PyCFunction)GraphBuilder_QueryIMediaEventEx, METH_VARARGS, GraphBuilder_QueryIMediaEventEx__doc__},
	{"EnumFilters", (PyCFunction)GraphBuilder_EnumFilters, METH_VARARGS, GraphBuilder_EnumFilters__doc__},
	{"Connect", (PyCFunction)GraphBuilder_Connect, METH_VARARGS, GraphBuilder_Connect__doc__},
	{"Release", (PyCFunction)GraphBuilder_Release, METH_VARARGS, GraphBuilder_Release__doc__},
	{NULL, (PyCFunction)NULL, 0, NULL}		/* sentinel */
};


static void
GraphBuilder_dealloc(GraphBuilderObject *self)
{
	/* XXXX Add your own cleanup code here */
	Py_BEGIN_ALLOW_THREADS
	RELEASE(self->pGraphBuilder);
	Py_END_ALLOW_THREADS
	PyMem_DEL(self);
}

static PyObject *
GraphBuilder_getattr(GraphBuilderObject *self, char *name)
{
	/* XXXX Add your own getattr code here */
	return Py_FindMethod(GraphBuilder_methods, (PyObject *)self, name);
}

static char GraphBuilderType__doc__[] =
"GraphBuilder"
;

static PyTypeObject GraphBuilderType = {
	PyObject_HEAD_INIT(&PyType_Type)
	0,				/*ob_size*/
	"GraphBuilder",			/*tp_name*/
	sizeof(GraphBuilderObject),		/*tp_basicsize*/
	0,				/*tp_itemsize*/
	/* methods */
	(destructor)GraphBuilder_dealloc,	/*tp_dealloc*/
	(printfunc)0,		/*tp_print*/
	(getattrfunc)GraphBuilder_getattr,	/*tp_getattr*/
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
	GraphBuilderType__doc__ /* Documentation string */
};

// End of code for GraphBuilder object 
/////////////////////////////////////////////////////////////


static char BaseFilter_FindPin__doc__[] =
""
;

static PyObject *
BaseFilter_FindPin(BaseFilterObject *self, PyObject *args)
{
	HRESULT res;
	char *psz;
	if (!PyArg_ParseTuple(args, "s", &psz))
		return NULL;
	PinObject *obj = newPinObject();
	WCHAR wsz[MAX_PATH];
	MultiByteToWideChar(CP_ACP,0,psz,-1,wsz,MAX_PATH);
	Py_BEGIN_ALLOW_THREADS
	res = self->pFilter->FindPin(wsz,&obj->pPin);
	Py_END_ALLOW_THREADS
	if (FAILED(res)) {
		seterror("BaseFilter_FindPin", res);
		Py_DECREF(obj);
		obj->pPin=NULL;
		return NULL;
	}
	return (PyObject *) obj;
}


static char BaseFilter_QueryIFileSinkFilter__doc__[] =
""
;

static PyObject *
BaseFilter_QueryIFileSinkFilter(BaseFilterObject *self, PyObject *args)
{
	HRESULT res;
	if (!PyArg_ParseTuple(args, ""))
		return NULL;

	FileSinkFilterObject *obj = newFileSinkFilterObject();
	Py_BEGIN_ALLOW_THREADS
	res = self->pFilter->QueryInterface(IID_IFileSinkFilter,(void**)&obj->pFilter);;
	Py_END_ALLOW_THREADS
	if (FAILED(res)) {
		seterror("BaseFilter_QueryIFileSinkFilter", res);
		Py_DECREF(obj);
		obj->pFilter=NULL;
		return NULL;
	}
	return (PyObject *) obj;
}

static char BaseFilter_QueryFilterName__doc__[] =
""
;

static PyObject *
BaseFilter_QueryFilterName(BaseFilterObject *self, PyObject *args)
{
	HRESULT res;
	if (!PyArg_ParseTuple(args, ""))
		return NULL;
	FILTER_INFO fi;
	Py_BEGIN_ALLOW_THREADS
	res = self->pFilter->QueryFilterInfo(&fi);
	Py_END_ALLOW_THREADS
	if (FAILED(res)) {
		seterror("BaseFilter_QueryFilterName", res);
		return NULL;
	}
	char buf[256];
	WideCharToMultiByte(CP_ACP,0,fi.achName,-1,buf,256,NULL,NULL);		
	return Py_BuildValue("s",buf);
}

static char BaseFilter_QueryIRealConverter__doc__[] =
""
;

static PyObject *
BaseFilter_QueryIRealConverter(BaseFilterObject *self, PyObject *args)
{
	HRESULT res;
	if (!PyArg_ParseTuple(args, ""))
		return NULL;

	RealConverterObject *obj = newRealConverterObject();
	Py_BEGIN_ALLOW_THREADS
	res = self->pFilter->QueryInterface(IID_IRealConverter,(void**)&obj->pRealConverter);
	Py_END_ALLOW_THREADS
	if (FAILED(res)) {
		seterror("BaseFilter_QueryIRealConverter", res);
		Py_DECREF(obj);
		obj->pRealConverter=NULL;
		return NULL;
	}
	return (PyObject *) obj;
}

static char BaseFilter_QueryIWMConverter__doc__[] =
""
;

static PyObject *
BaseFilter_QueryIWMConverter(BaseFilterObject *self, PyObject *args)
{
	HRESULT res;
	if (!PyArg_ParseTuple(args, ""))
		return NULL;

	WMConverterObject *obj = newWMConverterObject();
	Py_BEGIN_ALLOW_THREADS
	res = self->pFilter->QueryInterface(IID_IWMConverter,(void**)&obj->pWMConverter);
	Py_END_ALLOW_THREADS
	if (FAILED(res)) {
		seterror("BaseFilter_QueryIWMConverter", res);
		Py_DECREF(obj);
		obj->pWMConverter=NULL;
		return NULL;
	}
	return (PyObject *) obj;
}

static char BaseFilter_EnumPins__doc__[] =
""
;

static PyObject *
BaseFilter_EnumPins(BaseFilterObject *self, PyObject *args)
{
	HRESULT res;
	if (!PyArg_ParseTuple(args, ""))
		return NULL;
	EnumPinsObject *obj = newEnumPinsObject();
	Py_BEGIN_ALLOW_THREADS
	res = self->pFilter->EnumPins(&obj->pPins);
	Py_END_ALLOW_THREADS
	if (FAILED(res)) {
		seterror("BaseFilter_EnumPins", res);
		Py_DECREF(obj);
		obj->pPins=NULL;
		return NULL;
	}
	return (PyObject *) obj;
}

static struct PyMethodDef BaseFilter_methods[] = {
	{"FindPin", (PyCFunction)BaseFilter_FindPin, METH_VARARGS, BaseFilter_FindPin__doc__},
	{"QueryIFileSinkFilter", (PyCFunction)BaseFilter_QueryIFileSinkFilter, METH_VARARGS, BaseFilter_QueryIFileSinkFilter__doc__},
	{"QueryIRealConverter", (PyCFunction)BaseFilter_QueryIRealConverter, METH_VARARGS, BaseFilter_QueryIRealConverter__doc__},
	{"QueryIWMConverter", (PyCFunction)BaseFilter_QueryIWMConverter, METH_VARARGS, BaseFilter_QueryIWMConverter__doc__},
	{"QueryFilterName", (PyCFunction)BaseFilter_QueryFilterName, METH_VARARGS, BaseFilter_QueryFilterName__doc__},
	{"EnumPins", (PyCFunction)BaseFilter_EnumPins, METH_VARARGS, BaseFilter_EnumPins__doc__},
	{NULL, (PyCFunction)NULL, 0, NULL}		/* sentinel */
};

static void
BaseFilter_dealloc(BaseFilterObject *self)
{
	/* XXXX Add your own cleanup code here */
	RELEASE(self->pFilter);
	PyMem_DEL(self);
}

static PyObject *
BaseFilter_getattr(BaseFilterObject *self, char *name)
{
	/* XXXX Add your own getattr code here */
	return Py_FindMethod(BaseFilter_methods, (PyObject *)self, name);
}

static char BaseFilterType__doc__[] =
""
;

static PyTypeObject BaseFilterType = {
	PyObject_HEAD_INIT(&PyType_Type)
	0,				/*ob_size*/
	"BaseFilter",			/*tp_name*/
	sizeof(BaseFilterObject),		/*tp_basicsize*/
	0,				/*tp_itemsize*/
	/* methods */
	(destructor)BaseFilter_dealloc,	/*tp_dealloc*/
	(printfunc)0,		/*tp_print*/
	(getattrfunc)BaseFilter_getattr,	/*tp_getattr*/
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
	BaseFilterType__doc__ /* Documentation string */
};

// End of code for BaseFilter object 
////////////////////////////////////////////

static char Pin_ConnectedTo__doc__[] =
""
;

static PyObject *
Pin_ConnectedTo(PinObject *self, PyObject *args)
{
	HRESULT res;
	if (!PyArg_ParseTuple(args, ""))
		return NULL;
	PinObject *obj = newPinObject();
	Py_BEGIN_ALLOW_THREADS
	res=self->pPin->ConnectedTo(&obj->pPin);
	Py_END_ALLOW_THREADS
	if (FAILED(res)) {
		seterror("Pin_ConnectedTo", res);
		Py_DECREF(obj);
		obj->pPin=NULL;
		return NULL;
	}
	return (PyObject *) obj;
}


static struct PyMethodDef Pin_methods[] = {
	{"ConnectedTo", (PyCFunction)Pin_ConnectedTo, METH_VARARGS, Pin_ConnectedTo__doc__},
	{NULL, (PyCFunction)NULL, 0, NULL}		/* sentinel */
};

static void
Pin_dealloc(PinObject *self)
{
	/* XXXX Add your own cleanup code here */
	RELEASE(self->pPin);
	PyMem_DEL(self);
}

static PyObject *
Pin_getattr(PinObject *self, char *name)
{
	/* XXXX Add your own getattr code here */
	return Py_FindMethod(Pin_methods, (PyObject *)self, name);
}

static char PinType__doc__[] =
""
;

static PyTypeObject PinType = {
	PyObject_HEAD_INIT(&PyType_Type)
	0,				/*ob_size*/
	"Pin",			/*tp_name*/
	sizeof(PinObject),		/*tp_basicsize*/
	0,				/*tp_itemsize*/
	/* methods */
	(destructor)Pin_dealloc,	/*tp_dealloc*/
	(printfunc)0,		/*tp_print*/
	(getattrfunc)Pin_getattr,	/*tp_getattr*/
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
	PinType__doc__ /* Documentation string */
};

// End of code for Pin object 
////////////////////////////////////////////

/////////////////////////////////////////////
// FileSinkFilter


static char FileSinkFilter_SetFileName__doc__[] =
""
;

static PyObject *
FileSinkFilter_SetFileName(FileSinkFilterObject *self, PyObject *args)
{
	HRESULT res;
	char *psz;
	AM_MEDIA_TYPE *pmt=NULL;
	if (!PyArg_ParseTuple(args, "s", &psz))
		return NULL;
	WCHAR wsz[MAX_PATH];
	MultiByteToWideChar(CP_ACP,0,psz,-1,wsz,MAX_PATH);
	Py_BEGIN_ALLOW_THREADS
	res = self->pFilter->SetFileName(wsz,pmt);
	Py_END_ALLOW_THREADS
	if (FAILED(res)) {
		seterror("FileSinkFilter_SetFileName", res);
		return NULL;
	}
	Py_INCREF(Py_None);
	return Py_None;
}

static struct PyMethodDef FileSinkFilter_methods[] = {
	{"SetFileName", (PyCFunction)FileSinkFilter_SetFileName, METH_VARARGS, FileSinkFilter_SetFileName__doc__},
	{NULL, (PyCFunction)NULL, 0, NULL}		/* sentinel */
};

static void
FileSinkFilter_dealloc(FileSinkFilterObject *self)
{
	/* XXXX Add your own cleanup code here */
	RELEASE(self->pFilter);
	PyMem_DEL(self);
}

static PyObject *
FileSinkFilter_getattr(FileSinkFilterObject *self, char *name)
{
	/* XXXX Add your own getattr code here */
	return Py_FindMethod(FileSinkFilter_methods, (PyObject *)self, name);
}

static char FileSinkFilterType__doc__[] =
""
;

static PyTypeObject FileSinkFilterType = {
	PyObject_HEAD_INIT(&PyType_Type)
	0,				/*ob_size*/
	"FileSinkFilter",			/*tp_name*/
	sizeof(FileSinkFilterObject),		/*tp_basicsize*/
	0,				/*tp_itemsize*/
	/* methods */
	(destructor)FileSinkFilter_dealloc,	/*tp_dealloc*/
	(printfunc)0,		/*tp_print*/
	(getattrfunc)FileSinkFilter_getattr,	/*tp_getattr*/
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
	FileSinkFilterType__doc__ /* Documentation string */
};

// End of FileSinkFilter
////////////////////////////////////////////

/////////////////////////////////////////////////////////////
// BasicVideo object

static char BasicVideo_GetAvgTimePerFrame__doc__[] =
""
;
static PyObject *
BasicVideo_GetAvgTimePerFrame(BasicVideoObject *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args, ""))
		return NULL;
	REFTIME atpf;
	HRESULT hr;
	Py_BEGIN_ALLOW_THREADS
	hr = self->pI->get_AvgTimePerFrame(&atpf);
	Py_END_ALLOW_THREADS
	if (FAILED(hr)) {
		seterror("BasicVideo_GetAvgTimePerFrame", hr);
		return NULL;
	}
	return Py_BuildValue("d", atpf);
}


static char BasicVideo_GetBitRate__doc__[] =
""
;
static PyObject *
BasicVideo_GetBitRate(BasicVideoObject *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args, ""))
		return NULL;
	long bitRate;
	HRESULT hr;
	Py_BEGIN_ALLOW_THREADS
	hr = self->pI->get_BitRate(&bitRate);
	Py_END_ALLOW_THREADS
	if (FAILED(hr)) {
		seterror("BasicVideo_GetBitRate", hr);
		return NULL;
	}
	return Py_BuildValue("l", bitRate);
}

static char BasicVideo_GetVideoSize__doc__[] =
""
;
static PyObject *
BasicVideo_GetVideoSize(BasicVideoObject *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args, ""))
		return NULL;
	
	long width, height;
	HRESULT hr;
	
	hr = self->pI->get_VideoWidth(&width);
	if (FAILED(hr)) {
		seterror("get_VideoWidth", hr);
		return NULL;
	}

	hr = self->pI->get_VideoHeight(&height);
	if (FAILED(hr)) {
		seterror("get_VideoHeight", hr);
		return NULL;
	}
	return Py_BuildValue("ll", width, height);
}


static struct PyMethodDef BasicVideo_methods[] = {
	{"GetAvgTimePerFrame", (PyCFunction)BasicVideo_GetAvgTimePerFrame, METH_VARARGS, BasicVideo_GetAvgTimePerFrame__doc__},
	{"GetBitRate", (PyCFunction)BasicVideo_GetBitRate, METH_VARARGS, BasicVideo_GetBitRate__doc__},
	{"GetVideoSize", (PyCFunction)BasicVideo_GetVideoSize, METH_VARARGS, BasicVideo_GetVideoSize__doc__},
	{NULL, (PyCFunction)NULL, 0, NULL}		/* sentinel */
};

static void
BasicVideo_dealloc(BasicVideoObject *self)
{
	/* XXXX Add your own cleanup code here */
	RELEASE(self->pI);
	PyMem_DEL(self);
}

static PyObject *
BasicVideo_getattr(BasicVideoObject *self, char *name)
{
	/* XXXX Add your own getattr code here */
	return Py_FindMethod(BasicVideo_methods, (PyObject *)self, name);
}

static char BasicVideoType__doc__[] =
""
;

static PyTypeObject BasicVideoType = {
	PyObject_HEAD_INIT(&PyType_Type)
	0,				/*ob_size*/
	"BasicVideo",			/*tp_name*/
	sizeof(BasicVideoObject),		/*tp_basicsize*/
	0,				/*tp_itemsize*/
	/* methods */
	(destructor)BasicVideo_dealloc,	/*tp_dealloc*/
	(printfunc)0,		/*tp_print*/
	(getattrfunc)BasicVideo_getattr,	/*tp_getattr*/
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
	BasicVideoType__doc__ /* Documentation string */
};

// End of code for BasicVideo object 
////////////////////////////////////////////

/////////////////////////////////////////////
// MediaControl


static char MediaControl_Run__doc__[] =
""
;

static PyObject *
MediaControl_Run(MediaControlObject *self, PyObject *args)
{
	HRESULT res;
	if (!PyArg_ParseTuple(args, ""))
		return NULL;
	Py_BEGIN_ALLOW_THREADS
	res = self->pCtrl->Run();
	Py_END_ALLOW_THREADS
	if (FAILED(res)) {
		seterror("MediaControl_Run", res);
		return NULL;
	}
	Py_INCREF(Py_None);
	return Py_None;
}

static char MediaControl_Stop__doc__[] =
""
;

static PyObject *
MediaControl_Stop(MediaControlObject *self, PyObject *args)
{
	HRESULT res;
	if (!PyArg_ParseTuple(args, ""))
		return NULL;
	Py_BEGIN_ALLOW_THREADS
	res = self->pCtrl->Stop();
	Py_END_ALLOW_THREADS
	if (FAILED(res)) {
		seterror("MediaControl_Stop", res);
		return NULL;
	}
	Py_INCREF(Py_None);
	return Py_None;
}

static char MediaControl_Pause__doc__[] =
""
;

static PyObject *
MediaControl_Pause(MediaControlObject *self, PyObject *args)
{
	HRESULT res;
	if (!PyArg_ParseTuple(args, ""))
		return NULL;
	Py_BEGIN_ALLOW_THREADS
	res = self->pCtrl->Pause();
	Py_END_ALLOW_THREADS
	if (FAILED(res)) {
		seterror("MediaControl_Pause", res);
		return NULL;
	}
	Py_INCREF(Py_None);
	return Py_None;
}

static struct PyMethodDef MediaControl_methods[] = {
	{"Run", (PyCFunction)MediaControl_Run, METH_VARARGS, MediaControl_Run__doc__},
	{"Stop", (PyCFunction)MediaControl_Stop, METH_VARARGS, MediaControl_Stop__doc__},
	{"Pause", (PyCFunction)MediaControl_Pause, METH_VARARGS, MediaControl_Pause__doc__},
	{NULL, (PyCFunction)NULL, 0, NULL}		/* sentinel */
};

static void
MediaControl_dealloc(MediaControlObject *self)
{
	/* XXXX Add your own cleanup code here */
	RELEASE(self->pCtrl);
	PyMem_DEL(self);
}

static PyObject *
MediaControl_getattr(MediaControlObject *self, char *name)
{
	/* XXXX Add your own getattr code here */
	return Py_FindMethod(MediaControl_methods, (PyObject *)self, name);
}

static char MediaControlType__doc__[] =
""
;

static PyTypeObject MediaControlType = {
	PyObject_HEAD_INIT(&PyType_Type)
	0,				/*ob_size*/
	"MediaControl",			/*tp_name*/
	sizeof(MediaControlObject),		/*tp_basicsize*/
	0,				/*tp_itemsize*/
	/* methods */
	(destructor)MediaControl_dealloc,	/*tp_dealloc*/
	(printfunc)0,		/*tp_print*/
	(getattrfunc)MediaControl_getattr,	/*tp_getattr*/
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
	MediaControlType__doc__ /* Documentation string */
};

// End of MediaControl
////////////////////////////////////////////

////////////////////////////////////////////
// EnumPins object 


static char EnumPins_Next__doc__[] =
""
;

static PyObject *
EnumPins_Next(EnumPinsObject *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args, ""))
		return NULL;
	PinObject *obj = newPinObject();
	ULONG fetched=0;
	HRESULT res ;
	Py_BEGIN_ALLOW_THREADS
	res = self->pPins->Next(1,&obj->pPin,&fetched);
	Py_END_ALLOW_THREADS
	if (FAILED(res)) {
		seterror("EnumPins_Next", res);
		Py_DECREF(obj);
		obj->pPin=NULL;
		return NULL;
	}
	if(fetched==1)
		return (PyObject *) obj;
	Py_DECREF(obj);
	obj->pPin=NULL;
	Py_INCREF(Py_None);
	return Py_None;
}

static struct PyMethodDef EnumPins_methods[] = {
	{"Next", (PyCFunction)EnumPins_Next, METH_VARARGS, EnumPins_Next__doc__},
	{NULL, (PyCFunction)NULL, 0, NULL}		/* sentinel */
};

static void
EnumPins_dealloc(EnumPinsObject *self)
{
	/* XXXX Add your own cleanup code here */
	RELEASE(self->pPins);
	PyMem_DEL(self);
}

static PyObject *
EnumPins_getattr(EnumPinsObject *self, char *name)
{
	/* XXXX Add your own getattr code here */
	return Py_FindMethod(EnumPins_methods, (PyObject *)self, name);
}

static char EnumPinsType__doc__[] =
""
;

static PyTypeObject EnumPinsType = {
	PyObject_HEAD_INIT(&PyType_Type)
	0,				/*ob_size*/
	"EnumPins",			/*tp_name*/
	sizeof(EnumPinsObject),		/*tp_basicsize*/
	0,				/*tp_itemsize*/
	/* methods */
	(destructor)EnumPins_dealloc,	/*tp_dealloc*/
	(printfunc)0,		/*tp_print*/
	(getattrfunc)EnumPins_getattr,	/*tp_getattr*/
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
	EnumPinsType__doc__ /* Documentation string */
};

// End of code for EnumPins object 
////////////////////////////////////////////

////////////////////////////////////////////
// EnumFilters object 


static char EnumFilters_Next__doc__[] =
""
;

static PyObject *
EnumFilters_Next(EnumFiltersObject *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args, ""))
		return NULL;
	BaseFilterObject *obj = newBaseFilterObject();
	ULONG fetched=0;
	HRESULT res;
	Py_BEGIN_ALLOW_THREADS
	res = self->pI->Next(1,&obj->pFilter,&fetched);
	Py_END_ALLOW_THREADS
	if (FAILED(res)) {
		seterror("EnumFilters_Next", res);
		Py_DECREF(obj);
		obj->pFilter=NULL;
		return NULL;
	}
	if(fetched==1)
		return (PyObject*) obj;
	Py_DECREF(obj);
	obj->pFilter=NULL;
	Py_INCREF(Py_None);
	return Py_None;
}

static struct PyMethodDef EnumFilters_methods[] = {
	{"Next", (PyCFunction)EnumFilters_Next, METH_VARARGS, EnumFilters_Next__doc__},
	{NULL, (PyCFunction)NULL, 0, NULL}		/* sentinel */
};

static void
EnumFilters_dealloc(EnumFiltersObject *self)
{
	/* XXXX Add your own cleanup code here */
	RELEASE(self->pI);
	PyMem_DEL(self);
}

static PyObject *
EnumFilters_getattr(EnumFiltersObject *self, char *name)
{
	/* XXXX Add your own getattr code here */
	return Py_FindMethod(EnumFilters_methods, (PyObject *)self, name);
}

static char EnumFiltersType__doc__[] =
""
;

static PyTypeObject EnumFiltersType = {
	PyObject_HEAD_INIT(&PyType_Type)
	0,				/*ob_size*/
	"EnumFilters",			/*tp_name*/
	sizeof(EnumFiltersObject),		/*tp_basicsize*/
	0,				/*tp_itemsize*/
	/* methods */
	(destructor)EnumFilters_dealloc,	/*tp_dealloc*/
	(printfunc)0,		/*tp_print*/
	(getattrfunc)EnumFilters_getattr,	/*tp_getattr*/
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
	EnumFiltersType__doc__ /* Documentation string */
};

// End of code for EnumFilters object 
////////////////////////////////////////////

/////////////////////////////////////////////
// VideoWindow


static char VideoWindow_SetOwner__doc__[] =
""
;

static PyObject *
VideoWindow_SetOwner(VideoWindowObject *self, PyObject *args)
{
	HRESULT res;
	HWND hWnd;
	if (!PyArg_ParseTuple(args, "i",&hWnd))
		return NULL;
	Py_BEGIN_ALLOW_THREADS
	// temp batch intil split
	res = self->pI->put_Owner((OAHWND)hWnd);
	res = self->pI->put_MessageDrain((OAHWND)hWnd);
	res = self->pI->put_WindowStyle(WS_CHILD|WS_CLIPSIBLINGS|WS_CLIPCHILDREN);
	res = self->pI->put_AutoShow(OAFALSE);
	res = self->pI->SetWindowForeground(OAFALSE);
	Py_END_ALLOW_THREADS
	if (FAILED(res)) {
		seterror("VideoWindow_SetOwner", res);
		return NULL;
	}
	Py_INCREF(Py_None);
	return Py_None;
}


static char VideoWindow_SetWindowPosition__doc__[] =
""
;

static PyObject *
VideoWindow_SetWindowPosition(VideoWindowObject *self, PyObject *args)
{
	HRESULT res;
	long x,y,w,h;
	if (!PyArg_ParseTuple(args,"(llll):SetWindowPosition", &x,&y,&w,&h))
		return NULL;
	Py_BEGIN_ALLOW_THREADS
	res = self->pI->SetWindowPosition(x,y,w,h);
	Py_END_ALLOW_THREADS
	if (FAILED(res)) {
		seterror("VideoWindow_SetWindowPosition", res);
		return NULL;
	}
	Py_INCREF(Py_None);
	return Py_None;
}


static char VideoWindow_GetWindowPosition__doc__[] =
""
;

static PyObject *
VideoWindow_GetWindowPosition(VideoWindowObject *self, PyObject *args)
{
	HRESULT res;
	long x=0,y=0,w=0,h=0;
	if (!PyArg_ParseTuple(args,""))
		return NULL;
	Py_BEGIN_ALLOW_THREADS
	res = self->pI->GetWindowPosition(&x,&y,&w,&h);
	Py_END_ALLOW_THREADS
	if (FAILED(res)) {
		seterror("VideoWindow_GetWindowPosition", res);
		return NULL;
	}
	// Temp fix. We must find a better way
	long dh=GetSystemMetrics(SM_CYCAPTION)+2*GetSystemMetrics(SM_CYFRAME);
	long dw=2*GetSystemMetrics(SM_CXFRAME);
	return Py_BuildValue("(llll)",x,y,(w>0?w-dw:0),(h>0?h-dh:0));
}



static char VideoWindow_SetVisible__doc__[] =
""
;

static PyObject *
VideoWindow_SetVisible(VideoWindowObject *self, PyObject *args)
{
	HRESULT res;
	int flag; 
	if(!PyArg_ParseTuple(args,"i",&flag))
		return NULL;
	long visible=flag?-1:0; // OATRUE (-1),OAFALSE (0)	
	Py_BEGIN_ALLOW_THREADS
	res = self->pI->put_Visible(visible);
	Py_END_ALLOW_THREADS
	if (FAILED(res)) {
		seterror("VideoWindow_SetVisible", res);
		return NULL;
	}
	Py_INCREF(Py_None);
	return Py_None;
}

static struct PyMethodDef VideoWindow_methods[] = {
	{"SetOwner", (PyCFunction)VideoWindow_SetOwner, METH_VARARGS, VideoWindow_SetOwner__doc__},
	{"SetWindowPosition", (PyCFunction)VideoWindow_SetWindowPosition, METH_VARARGS, VideoWindow_SetWindowPosition__doc__},
	{"GetWindowPosition", (PyCFunction)VideoWindow_GetWindowPosition, METH_VARARGS, VideoWindow_GetWindowPosition__doc__},
	{"SetVisible", (PyCFunction)VideoWindow_SetVisible, METH_VARARGS, VideoWindow_SetVisible__doc__},
	{NULL, (PyCFunction)NULL, 0, NULL}		/* sentinel */
};

static void
VideoWindow_dealloc(VideoWindowObject *self)
{
	/* XXXX Add your own cleanup code here */
	RELEASE(self->pI);
	PyMem_DEL(self);
}

static PyObject *
VideoWindow_getattr(VideoWindowObject *self, char *name)
{
	/* XXXX Add your own getattr code here */
	return Py_FindMethod(VideoWindow_methods, (PyObject *)self, name);
}

static char VideoWindowType__doc__[] =
""
;

static PyTypeObject VideoWindowType = {
	PyObject_HEAD_INIT(&PyType_Type)
	0,				/*ob_size*/
	"VideoWindow",			/*tp_name*/
	sizeof(VideoWindowObject),		/*tp_basicsize*/
	0,				/*tp_itemsize*/
	/* methods */
	(destructor)VideoWindow_dealloc,	/*tp_dealloc*/
	(printfunc)0,		/*tp_print*/
	(getattrfunc)VideoWindow_getattr,	/*tp_getattr*/
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
	VideoWindowType__doc__ /* Documentation string */
};

// End of VideoWindow
////////////////////////////////////////////

/////////////////////////////////////////////
// MediaEventEx

static char MediaEventEx_SetNotifyWindow__doc__[] =
""
;

static PyObject *
MediaEventEx_SetNotifyWindow(MediaEventExObject *self, PyObject *args)
{
	HRESULT res;
	HWND hWnd;
	int msgid;
	if (!PyArg_ParseTuple(args, "ii",&hWnd,&msgid))
		return NULL;
	Py_BEGIN_ALLOW_THREADS
	res=self->pI->SetNotifyWindow((OAHWND)hWnd,msgid,0);
	Py_END_ALLOW_THREADS
	if (FAILED(res)) {
		seterror("MediaEventEx_SetOwner", res);
		return NULL;
	}
	Py_INCREF(Py_None);
	return Py_None;
}



static struct PyMethodDef MediaEventEx_methods[] = {
	{"SetNotifyWindow", (PyCFunction)MediaEventEx_SetNotifyWindow, METH_VARARGS, MediaEventEx_SetNotifyWindow__doc__},
	{NULL, (PyCFunction)NULL, 0, NULL}		/* sentinel */
};

static void
MediaEventEx_dealloc(MediaEventExObject *self)
{
	/* XXXX Add your own cleanup code here */
	RELEASE(self->pI);
	PyMem_DEL(self);
}

static PyObject *
MediaEventEx_getattr(MediaEventExObject *self, char *name)
{
	/* XXXX Add your own getattr code here */
	return Py_FindMethod(MediaEventEx_methods, (PyObject *)self, name);
}

static char MediaEventExType__doc__[] =
""
;

static PyTypeObject MediaEventExType = {
	PyObject_HEAD_INIT(&PyType_Type)
	0,				/*ob_size*/
	"MediaEventEx",			/*tp_name*/
	sizeof(MediaEventExObject),		/*tp_basicsize*/
	0,				/*tp_itemsize*/
	/* methods */
	(destructor)MediaEventEx_dealloc,	/*tp_dealloc*/
	(printfunc)0,		/*tp_print*/
	(getattrfunc)MediaEventEx_getattr,	/*tp_getattr*/
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
	MediaEventExType__doc__ /* Documentation string */
};

// End of MediaEventEx
////////////////////////////////////////////

////////////////////////////////////////////
// RealConverter object 

static char RealConverter_SetInterface__doc__[] =
""
;

static PyObject *
RealConverter_SetInterface(RealConverterObject *self, PyObject *args)
{
	UnknownObject *obj;
	char *hint;
	if (!PyArg_ParseTuple(args, "Os",&obj, &hint))
		return NULL;
	WCHAR wsz[MAX_PATH];
	MultiByteToWideChar(CP_ACP,0,hint,-1,wsz,MAX_PATH);
	Py_BEGIN_ALLOW_THREADS
	self->pRealConverter->SetInterface(obj->pI,wsz);
	Py_END_ALLOW_THREADS
	Py_INCREF(Py_None);
	return Py_None;
}

static struct PyMethodDef RealConverter_methods[] = {
	{"SetInterface", (PyCFunction)RealConverter_SetInterface, METH_VARARGS, RealConverter_SetInterface__doc__},
	{NULL, (PyCFunction)NULL, 0, NULL}		/* sentinel */
};

static void
RealConverter_dealloc(RealConverterObject *self)
{
	/* XXXX Add your own cleanup code here */
	RELEASE(self->pRealConverter);
	PyMem_DEL(self);
}

static PyObject *
RealConverter_getattr(RealConverterObject *self, char *name)
{
	/* XXXX Add your own getattr code here */
	return Py_FindMethod(RealConverter_methods, (PyObject *)self, name);
}

static char RealConverterType__doc__[] =
""
;

static PyTypeObject RealConverterType = {
	PyObject_HEAD_INIT(&PyType_Type)
	0,				/*ob_size*/
	"RealConverter",			/*tp_name*/
	sizeof(RealConverterObject),		/*tp_basicsize*/
	0,				/*tp_itemsize*/
	/* methods */
	(destructor)RealConverter_dealloc,	/*tp_dealloc*/
	(printfunc)0,		/*tp_print*/
	(getattrfunc)RealConverter_getattr,	/*tp_getattr*/
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
	RealConverterType__doc__ /* Documentation string */
};

// End of code for RealConverter object 
////////////////////////////////////////////

////////////////////////////////////////////
// WMConverter object 

static char WMConverter_SetAdviceSink__doc__[] =
""
;
static PyObject *
WMConverter_SetAdviceSink(WMConverterObject *self, PyObject *args)
{
	PyRenderingListenerObject *obj;
	if (!PyArg_ParseTuple(args, "O!",&PyRenderingListenerType,&obj))
		return NULL;
	IRendererAdviceSink *pI=NULL;
	HRESULT hr = obj->pI->QueryInterface(IID_IRendererAdviceSink,(void**)&pI);
	if (FAILED(hr)) {
		seterror("WMConverter_SetAdviceSink", hr);
		return NULL;
	}	
	self->pWMConverter->SetRendererAdviceSink(pI);
	pI->Release();
	Py_INCREF(Py_None);
	return Py_None;
}

static struct PyMethodDef WMConverter_methods[] = {
	{"SetAdviceSink", (PyCFunction)WMConverter_SetAdviceSink, METH_VARARGS, WMConverter_SetAdviceSink__doc__},
	{NULL, (PyCFunction)NULL, 0, NULL}		/* sentinel */
};

static void
WMConverter_dealloc(WMConverterObject *self)
{
	/* XXXX Add your own cleanup code here */
	RELEASE(self->pWMConverter);
	PyMem_DEL(self);
}

static PyObject *
WMConverter_getattr(WMConverterObject *self, char *name)
{
	/* XXXX Add your own getattr code here */
	return Py_FindMethod(WMConverter_methods, (PyObject *)self, name);
}

static char WMConverterType__doc__[] =
""
;

static PyTypeObject WMConverterType = {
	PyObject_HEAD_INIT(&PyType_Type)
	0,				/*ob_size*/
	"WMConverter",			/*tp_name*/
	sizeof(WMConverterObject),		/*tp_basicsize*/
	0,				/*tp_itemsize*/
	/* methods */
	(destructor)WMConverter_dealloc,	/*tp_dealloc*/
	(printfunc)0,		/*tp_print*/
	(getattrfunc)WMConverter_getattr,	/*tp_getattr*/
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
	WMConverterType__doc__ /* Documentation string */
};

// End of code for WMConverter object 
////////////////////////////////////////////

////////////////////////////////////////////
// Unknown object 


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
// MediaPosition object 

static char MediaPosition_GetDuration__doc__[] =
""
;

static PyObject *
MediaPosition_GetDuration(MediaPositionObject *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args, ""))
		return NULL;
	HRESULT res ;
    REFTIME tLength; // double in secs
	Py_BEGIN_ALLOW_THREADS
	res = self->pI->get_Duration(&tLength);
	Py_END_ALLOW_THREADS
	if (FAILED(res)) {
		seterror("MediaPosition_GetDuration", res);
		return NULL;
	}
	return Py_BuildValue("d",tLength); // in sec
}


static char MediaPosition_GetCurrentPosition__doc__[] =
""
;

static PyObject *
MediaPosition_GetCurrentPosition(MediaPositionObject *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args, ""))
		return NULL;
	HRESULT res ;
    REFTIME tLength=0; // double in secs
	Py_BEGIN_ALLOW_THREADS
	res = self->pI->get_CurrentPosition(&tLength);
	Py_END_ALLOW_THREADS
	if (FAILED(res)) {
		seterror("MediaPosition_GetCurrentPosition", res);
		return NULL;
	}
	return Py_BuildValue("d",tLength); // in sec
}


static char MediaPosition_SetCurrentPosition__doc__[] =
""
;

static PyObject *
MediaPosition_SetCurrentPosition(MediaPositionObject *self, PyObject *args)
{
	double tPos; // in sec
	if(!PyArg_ParseTuple(args,"d",&tPos))
		return NULL;
	HRESULT res ;
	Py_BEGIN_ALLOW_THREADS
	res = self->pI->put_CurrentPosition((REFTIME)tPos);
	Py_END_ALLOW_THREADS
	if (FAILED(res)) {
		seterror("MediaPosition_SetCurrentPosition", res);
		return NULL;
	}
	Py_INCREF(Py_None);
	return Py_None;
}

static char MediaPosition_GetStopTime__doc__[] =
""
;

static PyObject *
MediaPosition_GetStopTime(MediaPositionObject *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args, ""))
		return NULL;
	HRESULT res ;
    REFTIME tStop; // double in secs
	Py_BEGIN_ALLOW_THREADS
	res = self->pI->get_StopTime(&tStop);
	Py_END_ALLOW_THREADS
	if (FAILED(res)) {
		seterror("MediaPosition_GetStopTime", res);
		return NULL;
	}
	return Py_BuildValue("d",tStop); // in sec
}


static char MediaPosition_SetStopTime__doc__[] =
""
;

static PyObject *
MediaPosition_SetStopTime(MediaPositionObject *self, PyObject *args)
{
	double tPos; // in sec
	if(!PyArg_ParseTuple(args,"d",&tPos))
		return NULL;
	HRESULT res ;
	Py_BEGIN_ALLOW_THREADS
	res = self->pI->put_StopTime((REFTIME)tPos);
	Py_END_ALLOW_THREADS
	if (FAILED(res)) {
		seterror("MediaPosition_SetStopTime", res);
		return NULL;
	}
	Py_INCREF(Py_None);
	return Py_None;
}

static struct PyMethodDef MediaPosition_methods[] = {
	{"GetDuration", (PyCFunction)MediaPosition_GetDuration, METH_VARARGS, MediaPosition_GetDuration__doc__},
	{"GetCurrentPosition", (PyCFunction)MediaPosition_GetCurrentPosition, METH_VARARGS, MediaPosition_GetCurrentPosition__doc__},
	{"SetCurrentPosition", (PyCFunction)MediaPosition_SetCurrentPosition, METH_VARARGS, MediaPosition_SetCurrentPosition__doc__},
	{"GetStopTime", (PyCFunction)MediaPosition_GetStopTime, METH_VARARGS, MediaPosition_GetStopTime__doc__},
	{"SetStopTime", (PyCFunction)MediaPosition_SetStopTime, METH_VARARGS, MediaPosition_SetStopTime__doc__},
	{NULL, (PyCFunction)NULL, 0, NULL}		/* sentinel */
};

static void
MediaPosition_dealloc(MediaPositionObject *self)
{
	/* XXXX Add your own cleanup code here */
	RELEASE(self->pI);
	PyMem_DEL(self);
}

static PyObject *
MediaPosition_getattr(MediaPositionObject *self, char *name)
{
	/* XXXX Add your own getattr code here */
	return Py_FindMethod(MediaPosition_methods, (PyObject *)self, name);
}

static char MediaPositionType__doc__[] =
""
;

static PyTypeObject MediaPositionType = {
	PyObject_HEAD_INIT(&PyType_Type)
	0,				/*ob_size*/
	"MediaPosition",			/*tp_name*/
	sizeof(MediaPositionObject),		/*tp_basicsize*/
	0,				/*tp_itemsize*/
	/* methods */
	(destructor)MediaPosition_dealloc,	/*tp_dealloc*/
	(printfunc)0,		/*tp_print*/
	(getattrfunc)MediaPosition_getattr,	/*tp_getattr*/
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
	MediaPositionType__doc__ /* Documentation string */
};

// End of code for MediaPosition object 
////////////////////////////////////////////

/////////////////////////////////////////////
// MultiMediaStream object (IAMMultiMediaStream)

static char MultiMediaStream_Initialize__doc__[] =
""
;

static PyObject *
MultiMediaStream_Initialize(MultiMediaStreamObject *self, PyObject *args)
{
	GraphBuilderObject *obj=NULL;
	if (!PyArg_ParseTuple(args, "|O!",&GraphBuilderType,&obj))
		return NULL;
	IGraphBuilder* pGraphBuilder=obj?obj->pGraphBuilder:NULL;
	HRESULT hr = self->pI->Initialize(STREAMTYPE_READ,0,pGraphBuilder);
	if (FAILED(hr)) {
		seterror("MultiMediaStream_Initialize", hr);
		return NULL;
	}
	Py_INCREF(Py_None);
	return Py_None;
}

static char MultiMediaStream_AddPrimaryVideoMediaStream__doc__[] =
""
;
static PyObject *
MultiMediaStream_AddPrimaryVideoMediaStream(MultiMediaStreamObject *self, PyObject *args)
{
	UnknownObject *streamObject=NULL;
	if (!PyArg_ParseTuple(args, "|O",&streamObject))
		return NULL;
	IUnknown *pI=streamObject?streamObject->pI:NULL;
	HRESULT hr = self->pI->AddMediaStream(pI,&MSPID_PrimaryVideo,0,NULL);
	if (FAILED(hr)) {
		seterror("MultiMediaStream_AddPrimaryVideoMediaStream", hr);
		return NULL;
	}
	Py_INCREF(Py_None);
	return Py_None;
}

static char MultiMediaStream_AddPrimaryAudioMediaStream__doc__[] =
""
;
static PyObject *
MultiMediaStream_AddPrimaryAudioMediaStream(MultiMediaStreamObject *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args, ""))
		return NULL;
	HRESULT hr = self->pI->AddMediaStream(NULL,&MSPID_PrimaryAudio,AMMSF_ADDDEFAULTRENDERER,NULL);
	if (FAILED(hr)) {
		seterror("MultiMediaStream_AddPrimaryAudioMediaStream", hr);
		return NULL;
	}
	Py_INCREF(Py_None);
	return Py_None;
}

static char MultiMediaStream_OpenFile__doc__[] =
""
;
static PyObject *
MultiMediaStream_OpenFile(MultiMediaStreamObject *self, PyObject *args)
{
	char *psz;
	if (!PyArg_ParseTuple(args, "s", &psz))
		return NULL;
	char buf[MAX_PATH];
	strcpy(buf,psz);
	ConvToWindowsMediaUrl(buf);
	WCHAR wsz[MAX_PATH];
	MultiByteToWideChar(CP_ACP, 0, buf, -1, wsz, MAX_PATH);
	HRESULT hr;
	Py_BEGIN_ALLOW_THREADS	
	hr = self->pI->OpenFile(wsz, 0);
	Py_END_ALLOW_THREADS	
	if (FAILED(hr)) {
		char sz[MAX_PATH+80]="MultiMediaStream_OpenFile ";
		strcat(sz,psz);
		seterror("MultiMediaStream_OpenFile", hr);
		return NULL;
	}
	Py_INCREF(Py_None);
	return Py_None;
}

static char MultiMediaStream_Render__doc__[] =
""
;
static PyObject *
MultiMediaStream_Render(MultiMediaStreamObject *self, PyObject *args)
{
	DWORD dwFlags=AMMSF_NOCLOCK;
	if (!PyArg_ParseTuple(args, "|i", &dwFlags))
		return NULL;
	HRESULT hr = self->pI->Render(dwFlags);
	if (FAILED(hr)) {
		seterror("MultiMediaStream_Render", hr);
		return NULL;
	}
	Py_INCREF(Py_None);
	return Py_None;
}

static char MultiMediaStream_GetPrimaryVideoMediaStream__doc__[] =
""
;
static PyObject *
MultiMediaStream_GetPrimaryVideoMediaStream(MultiMediaStreamObject *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args, ""))
		return NULL;
	MediaStreamObject *obj = newMediaStreamObject();
	HRESULT hr = self->pI->GetMediaStream(MSPID_PrimaryVideo,&obj->pI);
	if (FAILED(hr)) {
		Py_DECREF(obj);
		seterror("MultiMediaStream_GetPrimaryVideoMediaStream", hr);
		return NULL;
	}
	return (PyObject*)obj;
}

static char MultiMediaStream_SetState__doc__[] =
""
;
static PyObject *
MultiMediaStream_SetState(MultiMediaStreamObject *self, PyObject *args)
{
	int state;
	if (!PyArg_ParseTuple(args, "i", &state))
		return NULL;
	HRESULT hr;
	Py_BEGIN_ALLOW_THREADS		
	hr = self->pI->SetState(state?STREAMSTATE_RUN:STREAMSTATE_STOP);
	Py_END_ALLOW_THREADS		
	if (FAILED(hr)) {
		seterror("MultiMediaStream_SetState", hr);
		return NULL;
	}
	Py_INCREF(Py_None);
	return Py_None;
}

static char MultiMediaStream_GetState__doc__[] =
""
;
static PyObject *
MultiMediaStream_GetState(MultiMediaStreamObject *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args, ""))
		return NULL;
	STREAM_STATE currentState;
	HRESULT hr;
	Py_BEGIN_ALLOW_THREADS		
	hr = self->pI->GetState(&currentState);
	Py_END_ALLOW_THREADS		
	if (FAILED(hr)) {
		seterror("MultiMediaStream_GetState", hr);
		return NULL;
	}
	return Py_BuildValue("i",currentState);
}

static char MultiMediaStream_GetDuration__doc__[] =
""
;
static PyObject *
MultiMediaStream_GetDuration(MultiMediaStreamObject *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args, ""))
		return NULL;
	STREAM_TIME duration;
	HRESULT hr;
	Py_BEGIN_ALLOW_THREADS		
	hr = self->pI->GetDuration(&duration);
	Py_END_ALLOW_THREADS		
	if (FAILED(hr)) {
		seterror("MultiMediaStream_GetDuration", hr);
		return NULL;
	}
	return (PyObject*)newLargeIntObject(duration);	
}


static char MultiMediaStream_GetTime__doc__[] =
""
;
static PyObject *
MultiMediaStream_GetTime(MultiMediaStreamObject *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args, ""))
		return NULL;
	STREAM_TIME currentTime;
	HRESULT hr;
	Py_BEGIN_ALLOW_THREADS		
	hr = self->pI->GetTime(&currentTime);
	Py_END_ALLOW_THREADS		
	if (FAILED(hr)) {
		seterror("MultiMediaStream_GetTime", hr);
		return NULL;
	}
	return (PyObject*)newLargeIntObject(currentTime);	
}

static char MultiMediaStream_Seek__doc__[] =
""
;
static PyObject *
MultiMediaStream_Seek(MultiMediaStreamObject *self, PyObject *args)
{
	LargeIntObject *liobj;
	if (!PyArg_ParseTuple(args,"O",&liobj))
		return NULL;
	STREAM_TIME seekTime = liobj->ob_ival;
	HRESULT hr;
	Py_BEGIN_ALLOW_THREADS		
	hr = self->pI->Seek(seekTime);
	Py_END_ALLOW_THREADS		
	if (FAILED(hr)) {
		seterror("MultiMediaStream_Seek", hr);
		return NULL;
	}
	Py_INCREF(Py_None);
	return Py_None;
}


static char MultiMediaStream_GetFilterGraph__doc__[] =
""
;
static PyObject *
MultiMediaStream_GetFilterGraph(MultiMediaStreamObject *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args,""))
		return NULL;
	
	GraphBuilderObject *obj = newGraphBuilderObject();
	if (obj == NULL) return NULL;
	HRESULT hr = self->pI->GetFilterGraph(&obj->pGraphBuilder);
	if(FAILED(hr))
		{
		Py_DECREF(obj);
		seterror("MultiMediaStream_GetFilterGraph", hr);
		return NULL;
		}
	return (PyObject*)obj;
}

static struct PyMethodDef MultiMediaStream_methods[] = {
	{"Initialize", (PyCFunction)MultiMediaStream_Initialize, METH_VARARGS, MultiMediaStream_Initialize__doc__},
	{"AddPrimaryVideoMediaStream", (PyCFunction)MultiMediaStream_AddPrimaryVideoMediaStream, METH_VARARGS, MultiMediaStream_AddPrimaryVideoMediaStream__doc__},
	{"AddPrimaryAudioMediaStream", (PyCFunction)MultiMediaStream_AddPrimaryAudioMediaStream, METH_VARARGS, MultiMediaStream_AddPrimaryAudioMediaStream__doc__},
	{"GetPrimaryVideoMediaStream", (PyCFunction)MultiMediaStream_GetPrimaryVideoMediaStream, METH_VARARGS, MultiMediaStream_GetPrimaryVideoMediaStream__doc__},
	{"OpenFile", (PyCFunction)MultiMediaStream_OpenFile, METH_VARARGS, MultiMediaStream_OpenFile__doc__},
	{"Render", (PyCFunction)MultiMediaStream_Render, METH_VARARGS, MultiMediaStream_Render__doc__},
	{"SetState", (PyCFunction)MultiMediaStream_SetState, METH_VARARGS, MultiMediaStream_SetState__doc__},
	{"GetState", (PyCFunction)MultiMediaStream_GetState, METH_VARARGS, MultiMediaStream_GetState__doc__},
	{"GetDuration", (PyCFunction)MultiMediaStream_GetDuration, METH_VARARGS, MultiMediaStream_GetDuration__doc__},
	{"GetTime", (PyCFunction)MultiMediaStream_GetTime, METH_VARARGS, MultiMediaStream_GetTime__doc__},
	{"Seek", (PyCFunction)MultiMediaStream_Seek, METH_VARARGS, MultiMediaStream_Seek__doc__},
	{"GetFilterGraph", (PyCFunction)MultiMediaStream_GetFilterGraph, METH_VARARGS, MultiMediaStream_GetFilterGraph__doc__},
	{NULL, (PyCFunction)NULL, 0, NULL}
};


static void
MultiMediaStream_dealloc(MultiMediaStreamObject *self)
{
	/* XXXX Add your own cleanup code here */
	Py_BEGIN_ALLOW_THREADS	
	RELEASE(self->pI);
	Py_END_ALLOW_THREADS	
	PyMem_DEL(self);
}

static PyObject *
MultiMediaStream_getattr(MultiMediaStreamObject *self, char *name)
{
	/* XXXX Add your own getattr code here */
	return Py_FindMethod(MultiMediaStream_methods, (PyObject *)self, name);
}

static char MultiMediaStreamType__doc__[] =
""
;

static PyTypeObject MultiMediaStreamType = {
	PyObject_HEAD_INIT(&PyType_Type)
	0,				/*ob_size*/
	"MultiMediaStream",			/*tp_name*/
	sizeof(MultiMediaStreamObject),		/*tp_basicsize*/
	0,				/*tp_itemsize*/
	/* methods */
	(destructor)MultiMediaStream_dealloc,	/*tp_dealloc*/
	(printfunc)0,		/*tp_print*/
	(getattrfunc)MultiMediaStream_getattr,	/*tp_getattr*/
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
	MultiMediaStreamType__doc__ /* Documentation string */
};

// End of code for MultiMediaStream object 
/////////////////////////////////////////////////////////////


/////////////////////////////////////////////
// MediaStream object

static char MediaStream_QueryIDirectDrawMediaStream__doc__[] =
""
;
static PyObject *
MediaStream_QueryIDirectDrawMediaStream(MediaStreamObject *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args, ""))
		return NULL;
	DirectDrawMediaStreamObject *obj = newDirectDrawMediaStreamObject();
	HRESULT hr = self->pI->QueryInterface(IID_IDirectDrawMediaStream,(void**)&obj->pI);
	if (FAILED(hr)) {
		Py_DECREF(obj);
		seterror("MediaStream_QueryIDirectDrawMediaStream", hr);
		return NULL;
	}
	return (PyObject*)obj;
}


static struct PyMethodDef MediaStream_methods[] = {
	{"QueryIDirectDrawMediaStream", (PyCFunction)MediaStream_QueryIDirectDrawMediaStream, METH_VARARGS, MediaStream_QueryIDirectDrawMediaStream__doc__},
	{NULL, (PyCFunction)NULL, 0, NULL}
};


static void
MediaStream_dealloc(MediaStreamObject *self)
{
	/* XXXX Add your own cleanup code here */
	RELEASE(self->pI);
	PyMem_DEL(self);
}

static PyObject *
MediaStream_getattr(MediaStreamObject *self, char *name)
{
	/* XXXX Add your own getattr code here */
	return Py_FindMethod(MediaStream_methods, (PyObject *)self, name);
}

static char MediaStreamType__doc__[] =
""
;

static PyTypeObject MediaStreamType = {
	PyObject_HEAD_INIT(&PyType_Type)
	0,				/*ob_size*/
	"MediaStream",			/*tp_name*/
	sizeof(MediaStreamObject),		/*tp_basicsize*/
	0,				/*tp_itemsize*/
	/* methods */
	(destructor)MediaStream_dealloc,	/*tp_dealloc*/
	(printfunc)0,		/*tp_print*/
	(getattrfunc)MediaStream_getattr,	/*tp_getattr*/
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
	MediaStreamType__doc__ /* Documentation string */
};

// End of code for MediaStream object 
/////////////////////////////////////////////////////////////

/////////////////////////////////////////////
// IDirectDrawMediaStream object

static char DirectDrawMediaStream_CreateSample__doc__[] =
""
;
static PyObject *
DirectDrawMediaStream_CreateSample(DirectDrawMediaStreamObject *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args, ""))
		return NULL;

    DDSURFACEDESC ddsd; 
	ZeroMemory(&ddsd,sizeof(ddsd));
    ddsd.dwSize = sizeof(ddsd);
	
    HRESULT hr = self->pI->GetFormat(&ddsd, NULL, NULL, NULL);
	if (FAILED(hr)) {
		seterror("DirectDrawMediaStream_CreateSample:GetFormat", hr);
		return NULL;
	}
	
	IDirectDraw *pDD = NULL;
	hr = self->pI->GetDirectDraw(&pDD);
	if (FAILED(hr)) {
		seterror("DirectDrawMediaStream_CreateSample:GetDirectDraw", hr);
		return NULL;
	}
	else if (pDD==NULL) {
		seterror("DirectDrawMediaStream_CreateSample:GetDirectDraw IDirectDrawMediaStream not initialized", hr);
		return NULL;
	}

	IDirectDrawSurface *pI=NULL;
	int nTrials=50; // sys may be temporary busy
	do	{
		hr = pDD->CreateSurface(&ddsd, &pI, NULL);
		if(FAILED(hr)) Sleep(10);
		nTrials--;
		} while(FAILED(hr) && nTrials>0);
	
	if (FAILED(hr)) {
		seterror("DirectDrawMediaStream_CreateSample:CreateSurface", hr);
		return NULL;
	}
	pDD->Release();

	DirectDrawStreamSampleObject *obj = newDirectDrawStreamSampleObject();
	hr = self->pI->CreateSample(pI, NULL, 0, &obj->pI);
	if (FAILED(hr)) {
		Py_DECREF(obj);
		seterror("DirectDrawMediaStream_CreateSample", hr);
		return NULL;
	}
	return (PyObject*)obj;
}


static char DirectDrawMediaStream_GetFormat__doc__[] =
""
;
static PyObject *
DirectDrawMediaStream_GetFormat(DirectDrawMediaStreamObject *self, PyObject *args)
{
	DDSURFACEDESCObject *obj;
	if (!PyArg_ParseTuple(args, "O",&obj))
		return NULL;
	HRESULT hr = self->pI->GetFormat(&obj->sd, NULL, NULL, NULL);
	if (FAILED(hr)) {
		seterror("DirectDrawMediaStream_GetFormat", hr);
		return NULL;
	}
	Py_INCREF(Py_None);
	return Py_None;
}

static struct PyMethodDef DirectDrawMediaStream_methods[] = {
	{"CreateSample", (PyCFunction)DirectDrawMediaStream_CreateSample, METH_VARARGS, DirectDrawMediaStream_CreateSample__doc__},
	{NULL, (PyCFunction)NULL, 0, NULL}
};


static void
DirectDrawMediaStream_dealloc(DirectDrawMediaStreamObject *self)
{
	/* XXXX Add your own cleanup code here */
	RELEASE(self->pI);
	PyMem_DEL(self);
}

static PyObject *
DirectDrawMediaStream_getattr(DirectDrawMediaStreamObject *self, char *name)
{
	/* XXXX Add your own getattr code here */
	return Py_FindMethod(DirectDrawMediaStream_methods, (PyObject *)self, name);
}

static char DirectDrawMediaStreamType__doc__[] =
""
;

static PyTypeObject DirectDrawMediaStreamType = {
	PyObject_HEAD_INIT(&PyType_Type)
	0,				/*ob_size*/
	"DirectDrawMediaStream",			/*tp_name*/
	sizeof(DirectDrawMediaStreamObject),		/*tp_basicsize*/
	0,				/*tp_itemsize*/
	/* methods */
	(destructor)DirectDrawMediaStream_dealloc,	/*tp_dealloc*/
	(printfunc)0,		/*tp_print*/
	(getattrfunc)DirectDrawMediaStream_getattr,	/*tp_getattr*/
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
	DirectDrawMediaStreamType__doc__ /* Documentation string */
};

// End of code for DirectDrawMediaStream object 
/////////////////////////////////////////////////////////////

/////////////////////////////////////////////
// DirectDrawStreamSample object (IDirectDrawStreamSample)


static char DirectDrawStreamSample_GetSurface__doc__[] =
""
;
static PyObject *
DirectDrawStreamSample_GetSurface(DirectDrawStreamSampleObject *self, PyObject *args)
{
	UnknownObject *directDrawSurface;
	if (!PyArg_ParseTuple(args, "O",&directDrawSurface))
		return NULL;
	RECT rc; // sample's clipping rectangle
	IDirectDrawSurface** ppDirectDrawSurface = (IDirectDrawSurface**)&directDrawSurface->pI;
	HRESULT hr = self->pI->GetSurface(ppDirectDrawSurface,&rc);
	if (FAILED(hr)) {
		seterror("DirectDrawStreamSample_GetSurface", hr);
		return NULL;
	}	
	(*ppDirectDrawSurface)->Release();
	
	return Py_BuildValue("iiii",rc.left,rc.top,rc.right,rc.bottom);
}

static char DirectDrawStreamSample_Update__doc__[] =
""
;
static PyObject *
DirectDrawStreamSample_Update(DirectDrawStreamSampleObject *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args, ""))
		return NULL;
	HRESULT hr;
	Py_BEGIN_ALLOW_THREADS
	hr = self->pI->Update(0,NULL,NULL,0);
	Py_END_ALLOW_THREADS
	if (FAILED(hr)) {
		seterror("DirectDrawStreamSample_Update", hr);
		return NULL;
	}
	int stillrunning = (hr!=S_OK)?0:1;
	return Py_BuildValue("i",stillrunning);
}

static struct PyMethodDef DirectDrawStreamSample_methods[] = {
	{"GetSurface", (PyCFunction)DirectDrawStreamSample_GetSurface, METH_VARARGS, DirectDrawStreamSample_GetSurface__doc__},
	{"Update", (PyCFunction)DirectDrawStreamSample_Update, METH_VARARGS, DirectDrawStreamSample_Update__doc__},
	{NULL, (PyCFunction)NULL, 0, NULL}
};


static void
DirectDrawStreamSample_dealloc(DirectDrawStreamSampleObject *self)
{
	/* XXXX Add your own cleanup code here */
	RELEASE(self->pI);
	PyMem_DEL(self);
}

static PyObject *
DirectDrawStreamSample_getattr(DirectDrawStreamSampleObject *self, char *name)
{
	/* XXXX Add your own getattr code here */
	return Py_FindMethod(DirectDrawStreamSample_methods, (PyObject *)self, name);
}

static char DirectDrawStreamSampleType__doc__[] =
""
;

static PyTypeObject DirectDrawStreamSampleType = {
	PyObject_HEAD_INIT(&PyType_Type)
	0,				/*ob_size*/
	"DirectDrawStreamSample",			/*tp_name*/
	sizeof(DirectDrawStreamSampleObject),		/*tp_basicsize*/
	0,				/*tp_itemsize*/
	/* methods */
	(destructor)DirectDrawStreamSample_dealloc,	/*tp_dealloc*/
	(printfunc)0,		/*tp_print*/
	(getattrfunc)DirectDrawStreamSample_getattr,	/*tp_getattr*/
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
	DirectDrawStreamSampleType__doc__ /* Documentation string */
};

// End of code for DirectDrawStreamSample object 
/////////////////////////////////////////////////////////////

////////////////////////////////////////////
// PyRenderingListener object 

static struct PyMethodDef PyRenderingListener_methods[] = {
	{NULL, (PyCFunction)NULL, 0, NULL}		/* sentinel */
};

static void
PyRenderingListener_dealloc(PyRenderingListenerObject *self)
{
	/* XXXX Add your own cleanup code here */
	RELEASE(self->pI);
	PyMem_DEL(self);
}

static PyObject *
PyRenderingListener_getattr(PyRenderingListenerObject *self, char *name)
{
	/* XXXX Add your own getattr code here */
	return Py_FindMethod(PyRenderingListener_methods, (PyObject *)self, name);
}

static char PyRenderingListenerType__doc__[] =
""
;

static PyTypeObject PyRenderingListenerType = {
	PyObject_HEAD_INIT(&PyType_Type)
	0,				/*ob_size*/
	"PyRenderingListener",			/*tp_name*/
	sizeof(PyRenderingListenerObject),		/*tp_basicsize*/
	0,				/*tp_itemsize*/
	/* methods */
	(destructor)PyRenderingListener_dealloc,	/*tp_dealloc*/
	(printfunc)0,		/*tp_print*/
	(getattrfunc)PyRenderingListener_getattr,	/*tp_getattr*/
	(setattrfunc)0,	/*tp_setattr*/
	(cmpfunc)0,		/*tp_compare*/
	(reprfunc)0,		/*tp_repr*/
	0,			/*tp_as_number*/
	0,		/*tp_as_sequence*/
	0,		/*tp_as_mapPyRenderingListenerg*/
	(hashfunc)0,		/*tp_hash*/
	(ternaryfunc)0,		/*tp_call*/
	(reprfunc)0,		/*tp_str*/

	/* Space for future expansion */
	0L,0L,0L,0L,
	PyRenderingListenerType__doc__ /* Documentation string */
};

// End of code for PyRenderingListener object 
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
// MODULE
//
static char CreateGraphBuilder__doc__[] =
""
;
static PyObject *
CreateGraphBuilder(PyObject *self, PyObject *args)
{
	HRESULT res;
	GraphBuilderObject *obj;

	if (!PyArg_ParseTuple(args, ""))
		return NULL;
	
	obj = newGraphBuilderObject();
	if (obj == NULL)
		return NULL;

    IGraphBuilder *pGraphBuilder=NULL;
	Py_BEGIN_ALLOW_THREADS
	res=CoCreateInstance(CLSID_FilterGraph,NULL,CLSCTX_INPROC_SERVER,
				 IID_IGraphBuilder,(void**)&pGraphBuilder);
	Py_END_ALLOW_THREADS
	if (!SUCCEEDED(res)) {
		Py_DECREF(obj);
		seterror("CoCreateInstance FilterGraph", res);
		return NULL;
	}
	else
		obj->pGraphBuilder=pGraphBuilder;
	return (PyObject *) obj;
}

static IBaseFilter* CreateDirectShowFilter(LPCTSTR strFilter,LPCTSTR strCat)
	{
	static const GUID CLSID_ActiveMovieFilterClassManager =
		{0x083863F1,0x70DE,0x11d0,{0xBD,0x40,0x00,0xA0,0xC9,0x11,0xCE,0x86}};

	static const GUID CLSID_AudioRendererCategory =
		{0xe0f158e1, 0xcb04, 0x11d0, {0xbd, 0x4e, 0x0, 0xa0, 0xc9, 0x11, 0xce, 0x86}};

	const GUID *pGUID;
	if(strCat && strCat[0] && strcmpi(strCat,"AudioRenderer")==0)
		pGUID=&CLSID_AudioRendererCategory;
	else
		pGUID=&CLSID_ActiveMovieFilterClassManager;

	HRESULT hr;
    ICreateDevEnum *pCreateDevEnum;
    hr = CoCreateInstance(CLSID_SystemDeviceEnum, NULL, CLSCTX_INPROC_SERVER,
			  IID_ICreateDevEnum, (void**)&pCreateDevEnum);
    if (hr != S_OK)
		{
		//cout << "Failed to create system device enumerator" << endl;
		return NULL;
		}
	else 
		;//cout << "System device enumerator created" << endl;


    IEnumMoniker *pEnMk;
    hr = pCreateDevEnum->CreateClassEnumerator(*pGUID,&pEnMk,0);
    pCreateDevEnum->Release();
    if (hr != S_OK)
		{
		//cout << "Failed to create class enumerator" << endl;
		return NULL;
		}
	else
		;//cout << "Class enumerator created" << endl;

    pEnMk->Reset();
    ULONG cFetched;
    IMoniker *pMk;
	IBaseFilter *pFilter=NULL;
	bool bFound=false;
	//cout << "Enumerating DirectShow filters" << endl;
    while(!bFound && pEnMk->Next(1,&pMk,&cFetched)==S_OK)
		{
		IPropertyBag *pBag;
		hr = pMk->BindToStorage(0,0,IID_IPropertyBag,(void **)&pBag);
		if(SUCCEEDED(hr)) 
			{
			VARIANT var;
			var.vt = VT_BSTR;
			hr = pBag->Read(L"FriendlyName",&var,NULL);
			if(SUCCEEDED(hr)) 
				{
				char achName[256];
				WideCharToMultiByte(CP_ACP, 0,var.bstrVal,-1,achName, 80,NULL, NULL);
				SysFreeString(var.bstrVal);
				if(lstrcmpi(strFilter,achName)==0)
					{
					//cout << "Requested filter "<< strFilter <<  " found!" << endl;
					IBindCtx *pbc=NULL;
					CreateBindCtx(0,&pbc);
					hr = pMk->BindToObject(pbc,NULL,IID_IBaseFilter, (void**)&pFilter);
					pbc->Release();
					bFound=true;
					if(FAILED(hr)) 
						{
						//cout << "BindToObject failed" << endl;
						//ErrorMessage(hr);
						pFilter=NULL;
						}
					}
				}
			pBag->Release();
			}
	    pMk->Release();
		}
    pEnMk->Release();
	return pFilter;
    }

static char CreateFilter__doc__[] =
""
;

static PyObject *
CreateFilter(PyObject *self, PyObject *args)
{
	BaseFilterObject *obj;
	char *psz;
	if (!PyArg_ParseTuple(args, "s", &psz))
		return NULL;
	obj = newBaseFilterObject();
	if (obj == NULL)
		return NULL;
	IBaseFilter *pFilter;
	Py_BEGIN_ALLOW_THREADS
	pFilter=CreateDirectShowFilter(psz,"ActiveMovieFilter");
	Py_END_ALLOW_THREADS
	if (!pFilter) {
		Py_DECREF(obj);
		seterror("CreateFilter", S_OK);
		return NULL;
	}
	else
		obj->pFilter=pFilter;
	return (PyObject *) obj;
	}

static char CreateMultiMediaStream__doc__[] =
""
;
static PyObject *
CreateMultiMediaStream(PyObject *self, PyObject *args)
{
	HRESULT hr;
	MultiMediaStreamObject *obj;

	if (!PyArg_ParseTuple(args, ""))
		return NULL;

	obj = newMultiMediaStreamObject();
	if (obj == NULL)
		return NULL;

	hr=CoCreateInstance(CLSID_AMMultiMediaStream,NULL,CLSCTX_INPROC_SERVER,
				 IID_IAMMultiMediaStream,(void**)&obj->pI);
	if (FAILED(hr)) {
		Py_DECREF(obj);
		seterror("CreateMultiMediaStream", hr);
		return NULL;
	}
	return (PyObject *) obj;
}

static char CreatePyRenderingListener__doc__[] =
""
;
static PyObject *
CreatePyRenderingListener(PyObject *self, PyObject *args)
{
	PyObject *listener;
	if (!PyArg_ParseTuple(args, "O", &listener))
		return NULL;

	PyRenderingListenerObject *obj = newPyRenderingListenerObject();
	if (obj == NULL)
		return NULL;

	HRESULT hr = CreatePyRenderingListener(listener, &obj->pI);
	if (FAILED(hr)) {
		Py_DECREF(obj);
		seterror("CreatePyRenderingListener", hr);
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

static struct PyMethodDef DShow_methods[] = {
	{"CreateGraphBuilder", (PyCFunction)CreateGraphBuilder, METH_VARARGS, CreateGraphBuilder__doc__},
	{"CreateFilter", (PyCFunction)CreateFilter, METH_VARARGS, CreateFilter__doc__},
	{"CreateMultiMediaStream", (PyCFunction)CreateMultiMediaStream, METH_VARARGS, CreateMultiMediaStream__doc__},
	{"CreatePyRenderingListener", (PyCFunction)CreatePyRenderingListener, METH_VARARGS, CreatePyRenderingListener__doc__},
	{"large_int", (PyCFunction)large_int, METH_VARARGS, large_int__doc__},
	{"CoInitialize", (PyCFunction)CoInitialize, METH_VARARGS, CoInitialize__doc__},
	{"CoUninitialize", (PyCFunction)CoUninitialize, METH_VARARGS, CoUninitialize__doc__},

	{NULL, (PyCFunction)NULL, 0, NULL}		/* sentinel */
};

static char dshow_module_documentation[] =
""
;

extern "C" __declspec(dllexport)
void initdshow()
{
	PyObject *m, *d;

	/* Create the module and add the functions */
	m = Py_InitModule4("dshow", DShow_methods,
		dshow_module_documentation,
		(PyObject*)NULL,PYTHON_API_VERSION);

	/* Add some symbolic constants to the module */
	d = PyModule_GetDict(m);
	ErrorObject = PyString_FromString("dshow.error");
	PyDict_SetItemString(d, "error", ErrorObject);

	PyCallbackBlock::init();	

	/* Check for errors */
	if (PyErr_Occurred())
		Py_FatalError("can't initialize module dshow");
}
