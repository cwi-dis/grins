

/**************************************************************************
Copyright 1991-2000 by Oratrix Development BV, Amsterdam, The Netherlands.

                        All Rights Reserved

***************************************************************************/

#include "Python.h"

#include <streams.h>
#include <objbase.h>

#include "dscom.h"

#include "mtpycall.h"


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

static struct PyMethodDef MediaSample_methods[] = {
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
// MediaType object 

static struct PyMethodDef MediaType_methods[] = {
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
