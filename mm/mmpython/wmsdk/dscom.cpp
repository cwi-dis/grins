

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
			PyObject *arg = Py_BuildValue("()");
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
			PyObject *arg = Py_BuildValue("()");
			helper.call(arg);
			}
		}				
	return S_OK;
}

