

/**************************************************************************
Copyright 1991-2000 by Oratrix Development BV, Amsterdam, The Netherlands.

                        All Rights Reserved

***************************************************************************/

#include "Python.h"

#include <streams.h>
#include <objbase.h>

#include "dscom.h"

#include "mtpycall.h"

void seterror(const char *funcname, HRESULT hr);
void seterror(const char *msg);

////////////////////////////////////////
//
typedef struct {
	PyObject_HEAD
	IMediaSample *pI;
} MediaSampleObject;

staticforward PyTypeObject MediaSampleType;

static MediaSampleObject *newMediaSampleObject(IMediaSample *pMediaSample)
{
	MediaSampleObject *self;
	self = PyObject_NEW(MediaSampleObject, &MediaSampleType);
	if (self == NULL) return NULL;
	self->pI = pMediaSample;
	return self;
}


//
typedef struct {
	PyObject_HEAD
	const CMediaType *pmt;
} MediaTypeObject;

staticforward PyTypeObject MediaTypeType;

static MediaTypeObject *newMediaTypeObject(const CMediaType *pmt)
{
	MediaTypeObject *self;
	self = PyObject_NEW(MediaTypeObject, &MediaTypeType);
	if (self == NULL) return NULL;
	self->pmt = pmt;
	return self;
}


////////////////////////////////////////////
// MediaSample object 

static char MediaSample_GetData__doc__[] =
"() -> (PyString str)"
;
static PyObject *
MediaSample_GetData(MediaSampleObject *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args, ""))
		return NULL;
	BYTE *pBuffer = NULL;
	HRESULT hr = self->pI->GetPointer(&pBuffer);
	if(FAILED(hr))
		{
		seterror("MediaSample_GetData", hr);
		return NULL;
		}
	int nbytes = self->pI->GetActualDataLength();
	return PyString_FromStringAndSize((char*)pBuffer, nbytes);
}     

static char MediaSample_GetTime__doc__[] =
"() -> (PyInt beginTime, PyInt endTime)"
;
static PyObject *
MediaSample_GetTime(MediaSampleObject *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args, ""))
		return NULL;
	CRefTime tBegin, tEnd;
	HRESULT hr = self->pI->GetTime((REFERENCE_TIME*)&tBegin, (REFERENCE_TIME*)&tEnd);
	if(FAILED(hr))
		{
		seterror("MediaSample_GetTime", hr);
		return NULL;
		}
	return Py_BuildValue("ll", tBegin.Millisecs(), tEnd.Millisecs());
}     

static char MediaSample_GetMediaTime__doc__[] =
"() -> (PyInt beginMediaTime, PyInt endMediaTime)"
;
static PyObject *
MediaSample_GetMediaTime(MediaSampleObject *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args, ""))
		return NULL;
	CRefTime tBegin, tEnd;
	HRESULT hr = self->pI->GetMediaTime((REFERENCE_TIME*)&tBegin, (REFERENCE_TIME*)&tEnd);
	if(FAILED(hr))
		{
		seterror("MediaSample_GetMediaTime", hr);
		return NULL;
		}
	return Py_BuildValue("ll", tBegin.Millisecs(), tEnd.Millisecs());
}     

static char MediaSample_IsSyncPoint__doc__[] =
"() -> (PyInt isSyncPoint)"
;
static PyObject *
MediaSample_IsSyncPoint(MediaSampleObject *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args, ""))
		return NULL;
	HRESULT hr = self->pI->IsSyncPoint();
	if(hr != S_OK && hr != S_FALSE)
		{
		seterror("MediaSample_IsSyncPoint", hr);
		return NULL;
		}
	return Py_BuildValue("i", (hr==S_OK)?1:0);
}     

static char MediaSample_IsPreroll__doc__[] =
"() -> (PyInt isPreroll)"
;
static PyObject *
MediaSample_IsPreroll(MediaSampleObject *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args, ""))
		return NULL;
	HRESULT hr = self->pI->IsPreroll();
	if(hr != S_OK && hr != S_FALSE)
		{
		seterror("MediaSample_IsPreroll", hr);
		return NULL;
		}
	return Py_BuildValue("i", (hr==S_OK)?1:0);
}     

static char MediaSample_IsDiscontinuity__doc__[] =
"() -> (PyInt isDiscontinuity)"
;
static PyObject *
MediaSample_IsDiscontinuity(MediaSampleObject *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args, ""))
		return NULL;
	HRESULT hr = self->pI->IsDiscontinuity();
	if(hr != S_OK && hr != S_FALSE)
		{
		seterror("MediaSample_IsDiscontinuity", hr);
		return NULL;
		}
	return Py_BuildValue("i", (hr==S_OK)?1:0);
}     

static char MediaSample_GetMediaType__doc__[] =
"() -> (MediaType mt)"
;
static PyObject *
MediaSample_GetMediaType(MediaSampleObject *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args, ""))
		return NULL;
	const CMediaType *pmt = NULL;
	HRESULT hr = self->pI->GetMediaType((AM_MEDIA_TYPE**)&pmt);
	if(FAILED(hr))
		{
		seterror("MediaSample_GetMediaType", hr);
		return NULL;
		}
	return (PyObject*)newMediaTypeObject(pmt);
}     

static struct PyMethodDef MediaSample_methods[] = {
	{"GetData", (PyCFunction)MediaSample_GetData, METH_VARARGS, MediaSample_GetData__doc__},
	{"GetTime", (PyCFunction)MediaSample_GetTime, METH_VARARGS, MediaSample_GetTime__doc__},
	{"GetMediaTime", (PyCFunction)MediaSample_GetMediaTime, METH_VARARGS, MediaSample_GetMediaTime__doc__},
	{"IsSyncPoint", (PyCFunction)MediaSample_IsSyncPoint, METH_VARARGS, MediaSample_IsSyncPoint__doc__},
	{"IsPreroll", (PyCFunction)MediaSample_IsPreroll, METH_VARARGS, MediaSample_IsPreroll__doc__},
	{"IsDiscontinuity", (PyCFunction)MediaSample_IsDiscontinuity, METH_VARARGS, MediaSample_IsDiscontinuity__doc__},
	{"GetMediaType", (PyCFunction)MediaSample_GetMediaType, METH_VARARGS, MediaSample_GetMediaType__doc__},
	{NULL, (PyCFunction)NULL, 0, NULL}		/* sentinel */
};

static void
MediaSample_dealloc(MediaSampleObject *self)
{
	PyMem_DEL(self);
}

static PyObject *
MediaSample_getattr(MediaSampleObject *self, char *name)
{
	/* XXXX Add your own getattr code here */
	return Py_FindMethod(MediaSample_methods, (PyObject *)self, name);
}

static char MediaSampleType__doc__[] =
""
;

static PyTypeObject MediaSampleType = {
	PyObject_HEAD_INIT(&PyType_Type)
	0,				/*ob_size*/
	"MediaSample",			/*tp_name*/
	sizeof(MediaSampleObject),		/*tp_basicsize*/
	0,				/*tp_itemsize*/
	/* methods */
	(destructor)MediaSample_dealloc,	/*tp_dealloc*/
	(printfunc)0,		/*tp_print*/
	(getattrfunc)MediaSample_getattr,	/*tp_getattr*/
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
	MediaSampleType__doc__ /* Documentation string */
};

// End of code for MediaSample object 
////////////////////////////////////////////

////////////////////////////////////////////
// MediaType object (CMediaType)

static char MediaType_GetType__doc__[] =
"() -> (PyString majorType)"
;
static PyObject *
MediaType_GetType(MediaTypeObject *self, PyObject *args)
{
	if(!PyArg_ParseTuple(args, ""))
		return NULL;
	const GUID *pMajorType = self->pmt->Type();
	if(*pMajorType == MEDIATYPE_Video)
		return Py_BuildValue("s", "video");
	else if(*pMajorType == MEDIATYPE_Audio)
		return Py_BuildValue("s", "audio");
	else if(*pMajorType == MEDIATYPE_Text)
		return Py_BuildValue("s", "text");
	else if(*pMajorType == MEDIATYPE_Midi)
		return Py_BuildValue("s", "midi");
	//else if(*pMajorType == MEDIATYPE_Stream)
	//	return Py_BuildValue("s", "stream");
	else if(*pMajorType == MEDIATYPE_Interleaved)
		return Py_BuildValue("s", "interleaved");
	else if(*pMajorType == MEDIATYPE_ScriptCommand)
		return Py_BuildValue("s", "scriptcommand");
	else if(*pMajorType == MEDIATYPE_AUXLine21Data)
		return Py_BuildValue("s", "auxline21data");
	else if(*pMajorType == MEDIATYPE_Timecode)
		return Py_BuildValue("s", "timecode");
	else if(*pMajorType == MEDIATYPE_URL_STREAM)
		return Py_BuildValue("s", "url_stream");
	return Py_BuildValue("s", "unknown");
}     

static char MediaType_GetSubtype__doc__[] =
"() -> (PyString subtype)"
;
static PyObject *
MediaType_GetSubtype(MediaTypeObject *self, PyObject *args)
{
	if(!PyArg_ParseTuple(args, ""))
		return NULL;
	const GUID *pSubtype = self->pmt->Subtype();

	// XXX: Not a complete list 
	if(*pSubtype == MEDIASUBTYPE_Avi)
		return Py_BuildValue("s", "avi");
//	else if(*pSubtype == MEDIASUBTYPE_Asf)
//		return Py_BuildValue("s", "asf");
	else if(*pSubtype == MEDIASUBTYPE_QTMovie)
		return Py_BuildValue("s", "qtmovie");
	else if(*pSubtype == MEDIASUBTYPE_RGB1)
		return Py_BuildValue("s", "rgb1");
	else if(*pSubtype == MEDIASUBTYPE_RGB4)
		return Py_BuildValue("s", "rgb4");
	else if(*pSubtype == MEDIASUBTYPE_RGB8)
		return Py_BuildValue("s", "rgb8");
	else if(*pSubtype == MEDIASUBTYPE_RGB565)
		return Py_BuildValue("s", "rgb565");
	else if(*pSubtype == MEDIASUBTYPE_RGB555)
		return Py_BuildValue("s", "rgb555");
	else if(*pSubtype == MEDIASUBTYPE_RGB24)
		return Py_BuildValue("s", "rgb24");
	else if(*pSubtype == MEDIASUBTYPE_RGB32)
		return Py_BuildValue("s", "rgb32");
	else if(*pSubtype == MEDIASUBTYPE_Overlay)
		return Py_BuildValue("s", "overlay");

	else if(*pSubtype == MEDIASUBTYPE_PCM)
		return Py_BuildValue("s", "pcm");
	else if(*pSubtype == MEDIASUBTYPE_WAVE)
		return Py_BuildValue("s", "wave");
	else if(*pSubtype == MEDIASUBTYPE_AU)
		return Py_BuildValue("s", "au");
	else if(*pSubtype == MEDIASUBTYPE_AIFF)
		return Py_BuildValue("s", "aiff");
	
	return Py_BuildValue("s", "unknown");
}     

static char MediaType_GetVideoInfo__doc__[] =
"() -> (PyInt width, PyInt height, PyFloat rate, PyInt isRGB24)"
;
static PyObject *
MediaType_GetVideoInfo(MediaTypeObject *self, PyObject *args)
{
	if(!PyArg_ParseTuple(args, ""))
		return NULL;
	if(*self->pmt->Type() != MEDIATYPE_Video)
		{
		seterror("Not a video MediaType");
		return NULL;
		}
	VIDEOINFOHEADER *pVideoInfo = (VIDEOINFOHEADER*)self->pmt->Format();
	float rate = 15.0; // default for asf
	if(pVideoInfo->AvgTimePerFrame > 0)
		{
		CRefTime rt(pVideoInfo->AvgTimePerFrame);
		rate = 1000.0F / float(rt.Millisecs());
		}

	int width = pVideoInfo->bmiHeader.biWidth;
    int height = pVideoInfo->bmiHeader.biHeight;

	const GUID *pSubType = self->pmt->Subtype();
	BOOL isRGB24 = (*pSubType == MEDIASUBTYPE_RGB24)? TRUE: FALSE;
		
	return Py_BuildValue("iifi", width, height, rate, isRGB24);
}     

static char MediaType_GetAudioInfo__doc__[] =
"() -> (PyInt channels, PyInt samplesPerSec, PyInt bitsPerSample, PyInt isWaveFormat)"
;
static PyObject *
MediaType_GetAudioInfo(MediaTypeObject *self, PyObject *args)
{
	if(!PyArg_ParseTuple(args, ""))
		return NULL;
	if(*self->pmt->Type() != MEDIATYPE_Audio)
		{
		seterror("Not an audio MediaType");
		return NULL;
		}
	WAVEFORMATEX *pwfx = (WAVEFORMATEX*)self->pmt->Format();
 	BOOL isWaveFormat = (self->pmt->formattype == FORMAT_WaveFormatEx)? TRUE: FALSE;
	return Py_BuildValue("iiii", int(pwfx->nChannels), pwfx->nSamplesPerSec, int(pwfx->wBitsPerSample), isWaveFormat);
}     

static struct PyMethodDef MediaType_methods[] = {
	{"GetType", (PyCFunction)MediaType_GetType, METH_VARARGS, MediaType_GetType__doc__},
	{"GetSubtype", (PyCFunction)MediaType_GetSubtype, METH_VARARGS, MediaType_GetSubtype__doc__},
	{"GetVideoInfo", (PyCFunction)MediaType_GetVideoInfo, METH_VARARGS, MediaType_GetVideoInfo__doc__},
	{"GetAudioInfo", (PyCFunction)MediaType_GetAudioInfo, METH_VARARGS, MediaType_GetAudioInfo__doc__},
	{NULL, (PyCFunction)NULL, 0, NULL}		/* sentinel */
};

static void
MediaType_dealloc(MediaTypeObject *self)
{
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
	MediaTypeType__doc__ /* Documentation string */
};

// End of code for MediaType object 
////////////////////////////////////////////


////////////////////////////////////////

class PyRenderingListener : 
	public IPyListener,
	public IRendererAdviceSink
	{
public:
    PyRenderingListener(PyObject *pyobj);
    virtual ~PyRenderingListener();
    
// IUnknown
    virtual HRESULT STDMETHODCALLTYPE QueryInterface(
        REFIID riid,
        void **ppvObject );
    virtual ULONG STDMETHODCALLTYPE AddRef();
    virtual ULONG STDMETHODCALLTYPE Release();

// IRendererAdviceSink
	virtual HRESULT STDMETHODCALLTYPE OnSetMediaType(/* [in] */ const CMediaType *pmt);
	virtual HRESULT STDMETHODCALLTYPE OnActive();
	virtual HRESULT STDMETHODCALLTYPE OnInactive();
	virtual HRESULT STDMETHODCALLTYPE OnRenderSample(/* [in] */ IMediaSample *pMediaSample);

// IPyListener
	virtual HRESULT STDMETHODCALLTYPE SetPyListener( 
            /* [in] */		PyObject *pyobj);
protected:
    LONG    m_cRef;
	PyObject *m_pyobj;
	};


////////////////////////////////////////
	
HRESULT STDMETHODCALLTYPE CreatePyRenderingListener(
			PyObject *pyobj,
			IPyListener **ppI)
{
	*ppI = new PyRenderingListener(pyobj);
	return S_OK;
}


////////////////////////////////////////
// PyRendererListener

PyRenderingListener::PyRenderingListener(PyObject *pyobj)
:	m_cRef(1),
	m_pyobj(pyobj)
{
	Py_XINCREF(m_pyobj);	
}


PyRenderingListener::~PyRenderingListener()
{
	Py_XDECREF(m_pyobj);
}


HRESULT STDMETHODCALLTYPE PyRenderingListener::QueryInterface(
    REFIID riid,
    void **ppvObject)
{
	*ppvObject = NULL;
	if (riid == IID_IPyListener || riid == IID_IUnknown)
		{
        *ppvObject = (IPyListener*)this;
        }
	else if (riid == IID_IRendererAdviceSink)
		{
        *ppvObject = (IRendererAdviceSink*)this;
        }
	else
		{
		return E_NOINTERFACE;
		}
	AddRef();	
	return S_OK;
}

ULONG STDMETHODCALLTYPE PyRenderingListener::AddRef()
{
    return  InterlockedIncrement(&m_cRef);
}

ULONG STDMETHODCALLTYPE PyRenderingListener::Release()
{
    ULONG uRet = InterlockedDecrement(&m_cRef);
	if(uRet==0) 
		{
		delete this;
		}
    return uRet;
}

HRESULT STDMETHODCALLTYPE PyRenderingListener::SetPyListener(/* [in] */ PyObject *pyobj)
{
	Py_XDECREF(m_pyobj);
	m_pyobj = pyobj;
	Py_XINCREF(m_pyobj);
	return S_OK;
}

HRESULT STDMETHODCALLTYPE PyRenderingListener::OnSetMediaType(/* [in] */ const CMediaType *pmt)
{
	if(m_pyobj)
		{
		CallbackHelper helper("OnSetMediaType",m_pyobj);
		if(helper.cancall())
			{
			PyObject *obj = (PyObject*)newMediaTypeObject(pmt);
			PyObject *arg = Py_BuildValue("(O)",obj);
			Py_XDECREF(obj);
			helper.call(arg);
			}
		}	
	return S_OK;
}

HRESULT STDMETHODCALLTYPE PyRenderingListener::OnActive()
{
	if(m_pyobj)
		{
		CallbackHelper helper("OnActive",m_pyobj);
		if(helper.cancall())
			{
			PyObject *arg = Py_BuildValue("()");
			helper.call(arg);
			}
		}		
	return S_OK;
}

HRESULT STDMETHODCALLTYPE PyRenderingListener::OnInactive()
{
	if(m_pyobj)
		{
		CallbackHelper helper("OnInactive",m_pyobj);
		if(helper.cancall())
			{
			PyObject *arg = Py_BuildValue("()");
			helper.call(arg);
			}
		}			
	return S_OK;
}

HRESULT STDMETHODCALLTYPE PyRenderingListener::OnRenderSample(/* [in] */ IMediaSample *pMediaSample)
{
	if(m_pyobj)
		{
		CallbackHelper helper("OnRenderSample",m_pyobj);
		if(helper.cancall())
			{
			PyObject *obj = (PyObject*)newMediaSampleObject(pMediaSample);
			PyObject *arg = Py_BuildValue("(O)",obj);
			Py_XDECREF(obj);
			helper.call(arg);
			}
		}				
	return S_OK;
}


///////////////////////////////////////
