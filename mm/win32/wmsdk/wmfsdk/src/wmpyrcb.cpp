
/***********************************************************
Copyright 1991-2000 by Oratrix Development BV, Amsterdam, The Netherlands.

                        All Rights Reserved

******************************************************************/

#include "Python.h"

#include <windows.h>
#include <wtypes.h>
#include "wmsdk.h"
#include <assert.h>

#include "wmpyrcb.h"

#include "pycbapi.h"

////////////////////////////////////////

class WMPyReaderCallback : 
	public IWMReaderCallback,
	public IWMPyReaderCallback
{
public:
    WMPyReaderCallback(PyObject *pyobj);
    virtual ~WMPyReaderCallback();
    
// IUnknown
    virtual HRESULT STDMETHODCALLTYPE QueryInterface(
        REFIID riid,
        void **ppvObject );
    virtual ULONG STDMETHODCALLTYPE AddRef();
    virtual ULONG STDMETHODCALLTYPE Release();

// IWMStatusCallback
    virtual HRESULT STDMETHODCALLTYPE OnStatus( 
        /* [in] */ WMT_STATUS Status,
        /* [in] */ HRESULT hr,
        /* [in] */ WMT_ATTR_DATATYPE dwType,
        /* [in] */ BYTE __RPC_FAR *pValue,
        /* [in] */ void __RPC_FAR *pvContext);

// IWMReaderCallback
    virtual HRESULT STDMETHODCALLTYPE OnSample( 
        /* [in] */ DWORD dwOutputNum,
        /* [in] */ QWORD cnsSampleTime,
        /* [in] */ QWORD cnsSampleDuration,
        /* [in] */ DWORD dwFlags,
        /* [in] */ INSSBuffer __RPC_FAR *pSample,
        /* [in] */ void __RPC_FAR *pvContext);

// IWMPyReaderCallback
	virtual HRESULT STDMETHODCALLTYPE SetListener( 
            /* [in] */		PyObject *pyobj);
	virtual HRESULT STDMETHODCALLTYPE WaitOpen(
            /* [in] */		DWORD dwMilliseconds,
			/* [out] */		DWORD *pdwWaitRes);				
	virtual HRESULT STDMETHODCALLTYPE WaitForCompletion(
            /* [in] */		DWORD dwMilliseconds,
			/* [out] */		DWORD *waitres);	

protected:
    LONG    m_cRef;
	
	PyObject *m_pyobj;

    HRESULT m_hrOpen;
    HANDLE m_hOpenEvent;

    BOOL    m_isEOF;
    HANDLE  m_hCompletionEvent;
};

////////////////////////////////////////
	
class WMPyReaderCallbackAdvanced : 
	public IWMReaderCallback,
	public IWMReaderCallbackAdvanced,
	public IWMPyReaderCallback
{
public:
    WMPyReaderCallbackAdvanced(PyObject *pyobj);
    virtual ~WMPyReaderCallbackAdvanced();
    
// IUnknown
    virtual HRESULT STDMETHODCALLTYPE QueryInterface(
        REFIID riid,
        void **ppvObject );
    virtual ULONG STDMETHODCALLTYPE AddRef();
    virtual ULONG STDMETHODCALLTYPE Release();

// IWMStatusCallback
    virtual HRESULT STDMETHODCALLTYPE OnStatus( 
        /* [in] */ WMT_STATUS Status,
        /* [in] */ HRESULT hr,
        /* [in] */ WMT_ATTR_DATATYPE dwType,
        /* [in] */ BYTE __RPC_FAR *pValue,
        /* [in] */ void __RPC_FAR *pvContext);

// IWMReaderCallback
    virtual HRESULT STDMETHODCALLTYPE OnSample( 
        /* [in] */ DWORD dwOutputNum,
        /* [in] */ QWORD cnsSampleTime,
        /* [in] */ QWORD cnsSampleDuration,
        /* [in] */ DWORD dwFlags,
        /* [in] */ INSSBuffer __RPC_FAR *pSample,
        /* [in] */ void __RPC_FAR *pvContext);

	
// IWMPyReaderCallbackAdvanced 
	virtual HRESULT STDMETHODCALLTYPE OnStreamSample( 
            /* [in] */ WORD wStreamNum,
            /* [in] */ QWORD cnsSampleTime,
            /* [in] */ QWORD cnsSampleDuration,
            /* [in] */ DWORD dwFlags,
            /* [in] */ INSSBuffer __RPC_FAR *pSample,
            /* [in] */ void __RPC_FAR *pvContext);
        
	virtual HRESULT STDMETHODCALLTYPE OnTime( 
            /* [in] */ QWORD cnsCurrentTime,
            /* [in] */ void __RPC_FAR *pvContext);
        
	virtual HRESULT STDMETHODCALLTYPE OnStreamSelection( 
            /* [in] */ WORD wStreamCount,
            /* [in] */ WORD __RPC_FAR *pStreamNumbers,
            /* [in] */ WMT_STREAM_SELECTION __RPC_FAR *pSelections,
            /* [in] */ void __RPC_FAR *pvContext);
        
	virtual HRESULT STDMETHODCALLTYPE OnOutputPropsChanged( 
            /* [in] */ DWORD dwOutputNum,
            /* [in] */ WM_MEDIA_TYPE __RPC_FAR *pMediaType,
            /* [in] */ void __RPC_FAR *pvContext);
        
	virtual HRESULT STDMETHODCALLTYPE AllocateForStream( 
            /* [in] */ WORD wStreamNum,
            /* [in] */ DWORD cbBuffer,
            /* [out] */ INSSBuffer __RPC_FAR *__RPC_FAR *ppBuffer,
            /* [in] */ void __RPC_FAR *pvContext);
        
	virtual HRESULT STDMETHODCALLTYPE AllocateForOutput( 
            /* [in] */ DWORD dwOutputNum,
            /* [in] */ DWORD cbBuffer,
            /* [out] */ INSSBuffer __RPC_FAR *__RPC_FAR *ppBuffer,
            /* [in] */ void __RPC_FAR *pvContext);

// IWMPyReaderCallback
	virtual HRESULT STDMETHODCALLTYPE SetListener( 
            /* [in] */		PyObject *pyobj);
	virtual HRESULT STDMETHODCALLTYPE WaitOpen(
            /* [in] */		DWORD dwMilliseconds,
			/* [out] */		DWORD *pdwWaitRes);				
	virtual HRESULT STDMETHODCALLTYPE WaitForCompletion(
            /* [in] */		DWORD dwMilliseconds,
			/* [out] */		DWORD *waitres);	

protected:
    LONG    m_cRef;
	
	PyObject *m_pyobj;

    HRESULT m_hrOpen;
    HANDLE m_hOpenEvent;

    BOOL    m_isEOF;
    HANDLE  m_hCompletionEvent;
			
};


////////////////////////////////////////
	
HRESULT STDMETHODCALLTYPE WMCreatePyReaderCallback(
			PyObject *pyobj,
			IWMPyReaderCallback **ppI)
{
	*ppI = new WMPyReaderCallback(pyobj);
	return S_OK;
}

HRESULT STDMETHODCALLTYPE WMCreatePyReaderCallbackAdvanced(
			PyObject *pyobj,
			IWMPyReaderCallback **ppI)
{
	*ppI = new WMPyReaderCallbackAdvanced(pyobj);
	return S_OK;
}


////////////////////////////////////////
// WMPyReaderCallback

WMPyReaderCallback::WMPyReaderCallback(PyObject *pyobj)
:	m_cRef(1),
	m_pyobj(pyobj),
	m_hrOpen(S_OK),
	m_isEOF(FALSE)
{
	Py_XINCREF(m_pyobj);	
    m_hOpenEvent = CreateEvent(NULL,TRUE,FALSE,NULL);
    m_hCompletionEvent = CreateEvent( NULL, TRUE, FALSE, NULL );
}


WMPyReaderCallback::~WMPyReaderCallback()
{
//	Py_XDECREF(m_pyobj);
    CloseHandle(m_hOpenEvent);
	CloseHandle(m_hCompletionEvent);
}


HRESULT STDMETHODCALLTYPE WMPyReaderCallback::QueryInterface(
    REFIID riid,
    void **ppvObject)
{
	if (riid == IID_IWMReaderCallback)
		{
        *ppvObject = (IWMReaderCallback*)this;
        }
	else if(riid == IID_IWMReaderCallbackAdvanced)
		{
		return E_NOINTERFACE;
        }
	else
		{
		return E_NOINTERFACE;
		}
	AddRef();	
	return S_OK;
}

ULONG STDMETHODCALLTYPE WMPyReaderCallback::AddRef()
{
    return  InterlockedIncrement(&m_cRef);
}

ULONG STDMETHODCALLTYPE WMPyReaderCallback::Release()
{
    ULONG uRet = InterlockedDecrement(&m_cRef);
	if(uRet==0) 
		{
		delete this;
		}
    return uRet;
}


HRESULT STDMETHODCALLTYPE WMPyReaderCallback::SetListener(
			/* [in] */ 	PyObject *pyobj)
{
	Py_XDECREF(m_pyobj);
	m_pyobj = NULL;
	if(pyobj && pyobj!=Py_None)
		{
		Py_INCREF(pyobj);
		m_pyobj=pyobj;
		}
	return S_OK;
}

HRESULT STDMETHODCALLTYPE WMPyReaderCallback::WaitOpen(
            /* [in] */		DWORD dwMilliseconds,
			/* [out] */		DWORD *pdwWaitRes)
{
	*pdwWaitRes = WaitForSingleObject(m_hOpenEvent,dwMilliseconds);
	return S_OK;
}

HRESULT STDMETHODCALLTYPE WMPyReaderCallback::WaitForCompletion(
            /* [in] */		DWORD dwMilliseconds,
			/* [out] */		DWORD *pdwWaitRes)
{
	*pdwWaitRes = 0;
	if(WaitForSingleObject(m_hCompletionEvent,dwMilliseconds)==WAIT_OBJECT_0)
		*pdwWaitRes = 1;
	return S_OK;
}


HRESULT STDMETHODCALLTYPE WMPyReaderCallback::OnStatus( 
        /* [in] */ WMT_STATUS Status, 
        /* [in] */ HRESULT hr,
        /* [in] */ WMT_ATTR_DATATYPE dwType,
        /* [in] */ BYTE __RPC_FAR *pValue,
        /* [in] */ VOID *pvContext )
{
	if(m_isEOF)
		{
		//PyCallbackBlock cb;
		//Py_XDECREF(m_pyobj);
		m_pyobj=NULL;
		}
	if(m_pyobj)
		{
		CallbackHelper helper("OnStatus",m_pyobj);
		if(helper.cancall())
			{
			PyObject *arg = Py_BuildValue("(i)",Status);
			helper.call(arg);
			}
		}
    switch( Status )
    {
    case WMT_OPENED:
        m_hrOpen = hr;
        SetEvent(m_hOpenEvent);
        break;

    case WMT_ERROR:
        printf( "OnStatus( WMT_ERROR )\n" );
        break;

    case WMT_STARTED:
        printf( "OnStatus( WMT_STARTED )\n" );
        break;

    case WMT_STOPPED:
        printf( "OnStatus( WMT_STOPPED )\n" );
        break;

    case WMT_BUFFERING_START:
        printf( "OnStatus( WMT_BUFFERING START)\n" );
        break;

    case WMT_BUFFERING_STOP:
        printf( "OnStatus( WMT_BUFFERING STOP)\n" );
        break;

    case WMT_EOF:
        printf( "OnStatus( WMT_EOF )\n" );
        m_isEOF = TRUE;		
        SetEvent(m_hCompletionEvent);
        break;

    case WMT_LOCATING:
        printf( "OnStatus( WMT_LOCATING )\n" );
        break;

    case WMT_CONNECTING:
        printf( "OnStatus( WMT_CONNECTING )\n" );
        break;

    case WMT_NO_RIGHTS:
        break;

    case WMT_MISSING_CODEC:
        break;
    };

    return	S_OK;
}

HRESULT STDMETHODCALLTYPE WMPyReaderCallback::OnSample( 
        /* [in] */ DWORD dwOutputNum,
        /* [in] */ QWORD cnsSampleTime,
        /* [in] */ QWORD cnsSampleDuration,
        /* [in] */ DWORD dwFlags,
        /* [in] */ INSSBuffer __RPC_FAR *pSample,
        /* [in] */ VOID *pvContext)
{
    HRESULT hr;
    BYTE *pData;
    DWORD cbData;

    hr = pSample->GetBufferAndLength(&pData,&cbData);
    if (FAILED(hr)) return E_UNEXPECTED;

	if(m_pyobj)
		{
		CallbackHelper helper("OnSample",m_pyobj);
		if(helper.cancall())
			{
			DWORD ms = (DWORD)cnsSampleTime/10000; // for small files
			PyObject *obj = PyString_FromStringAndSize((char*)pData,(int)cbData);
			PyObject *arg = Py_BuildValue("(iO)", ms,obj);
			Py_DECREF(obj);
			helper.call(arg);
			}
		}
    return S_OK;
}


////////////////////////////////////////
// WMPyReaderCallbackAdvanced

WMPyReaderCallbackAdvanced::WMPyReaderCallbackAdvanced(PyObject *pyobj)
:	m_cRef(1),
	m_pyobj(pyobj),
	m_hrOpen(S_OK),
	m_isEOF(FALSE)
{
	Py_XINCREF(m_pyobj);	
    m_hOpenEvent = CreateEvent(NULL,TRUE,FALSE,NULL);
    m_hCompletionEvent = CreateEvent( NULL, TRUE, FALSE, NULL );
}


WMPyReaderCallbackAdvanced::~WMPyReaderCallbackAdvanced()
{
//	Py_XDECREF(m_pyobj);
    CloseHandle(m_hOpenEvent);
	CloseHandle(m_hCompletionEvent);
}


HRESULT STDMETHODCALLTYPE WMPyReaderCallbackAdvanced::QueryInterface(
    REFIID riid,
    void **ppvObject)
{
	if (riid == IID_IWMReaderCallback)
		{
        *ppvObject = (IWMReaderCallback*)this;
        }
	else if(riid == IID_IWMReaderCallbackAdvanced)
		{
        *ppvObject = (IWMReaderCallbackAdvanced*)this;
        }
	else
		{
		return E_NOINTERFACE;
		}
	AddRef();
	return S_OK;
}

ULONG STDMETHODCALLTYPE WMPyReaderCallbackAdvanced::AddRef()
{
    return  InterlockedIncrement(&m_cRef);
}

ULONG STDMETHODCALLTYPE WMPyReaderCallbackAdvanced::Release()
{
    ULONG uRet = InterlockedDecrement(&m_cRef);
	if(uRet==0) 
		{
		delete this;
		}
    return uRet;
}

HRESULT STDMETHODCALLTYPE WMPyReaderCallbackAdvanced::SetListener(
			/* [in] */ 	PyObject *pyobj)
{
	Py_XDECREF(m_pyobj);
	m_pyobj = NULL;
	if(pyobj && pyobj!=Py_None)
		{
		Py_INCREF(pyobj);
		m_pyobj=pyobj;
		}
	return S_OK;
}

HRESULT STDMETHODCALLTYPE WMPyReaderCallbackAdvanced::WaitOpen(
            /* [in] */		DWORD dwMilliseconds,
			/* [out] */		DWORD *pdwWaitRes)
{
	*pdwWaitRes = WaitForSingleObject(m_hOpenEvent,dwMilliseconds);
	return S_OK;
}

HRESULT STDMETHODCALLTYPE WMPyReaderCallbackAdvanced::WaitForCompletion(
            /* [in] */		DWORD dwMilliseconds,
			/* [out] */		DWORD *pdwWaitRes)
{
	*pdwWaitRes = 0;
	if(WaitForSingleObject(m_hCompletionEvent,dwMilliseconds)==WAIT_OBJECT_0)
		*pdwWaitRes = 1;
	return S_OK;
}


HRESULT STDMETHODCALLTYPE WMPyReaderCallbackAdvanced::OnStatus( 
        /* [in] */ WMT_STATUS Status, 
        /* [in] */ HRESULT hr,
        /* [in] */ WMT_ATTR_DATATYPE dwType,
        /* [in] */ BYTE __RPC_FAR *pValue,
        /* [in] */ VOID *pvContext )
{
	if(m_isEOF)
		{
		//PyCallbackBlock cb;
		//Py_XDECREF(m_pyobj);
		m_pyobj=NULL;
		}
	if(m_pyobj)
		{
		CallbackHelper helper("OnStatus",m_pyobj);
		if(helper.cancall())
			{
			PyObject *arg = Py_BuildValue("(i)",Status);
			helper.call(arg);
			}
		}
    switch( Status )
    {
    case WMT_OPENED:
        m_hrOpen = hr;
        SetEvent(m_hOpenEvent);
        break;

    case WMT_ERROR:
        printf( "OnStatus( WMT_ERROR )\n" );
        break;

    case WMT_STARTED:
        printf( "OnStatus( WMT_STARTED )\n" );
        break;

    case WMT_STOPPED:
        printf( "OnStatus( WMT_STOPPED )\n" );
        break;

    case WMT_BUFFERING_START:
        printf( "OnStatus( WMT_BUFFERING START)\n" );
        break;

    case WMT_BUFFERING_STOP:
        printf( "OnStatus( WMT_BUFFERING STOP)\n" );
        break;

    case WMT_EOF:
        printf( "OnStatus( WMT_EOF )\n" );
        m_isEOF = TRUE;		
        SetEvent(m_hCompletionEvent);
        break;

    case WMT_LOCATING:
        printf( "OnStatus( WMT_LOCATING )\n" );
        break;

    case WMT_CONNECTING:
        printf( "OnStatus( WMT_CONNECTING )\n" );
        break;

    case WMT_NO_RIGHTS:
        break;

    case WMT_MISSING_CODEC:
        break;
    };

    return	S_OK;
}

HRESULT STDMETHODCALLTYPE WMPyReaderCallbackAdvanced::OnSample( 
        /* [in] */ DWORD dwOutputNum,
        /* [in] */ QWORD cnsSampleTime,
        /* [in] */ QWORD cnsSampleDuration,
        /* [in] */ DWORD dwFlags,
        /* [in] */ INSSBuffer __RPC_FAR *pSample,
        /* [in] */ VOID *pvContext)
{
    HRESULT hr;
    BYTE *pData;
    DWORD cbData;

    hr = pSample->GetBufferAndLength(&pData,&cbData);
    if (FAILED(hr)) return E_UNEXPECTED;

	if(m_pyobj)
		{
		CallbackHelper helper("OnSample",m_pyobj);
		if(helper.cancall())
			{
			DWORD ms = (DWORD)cnsSampleTime/10000; // for small files
			PyObject *obj = PyString_FromStringAndSize((char*)pData,(int)cbData);
			PyObject *arg = Py_BuildValue("(iO)", ms,obj);
			Py_DECREF(obj);
			helper.call(arg);
			}
		}
    return S_OK;
}


HRESULT STDMETHODCALLTYPE WMPyReaderCallbackAdvanced::OnStreamSample( 
            /* [in] */ WORD wStreamNum,
            /* [in] */ QWORD cnsSampleTime,
            /* [in] */ QWORD cnsSampleDuration,
            /* [in] */ DWORD dwFlags,
            /* [in] */ INSSBuffer __RPC_FAR *pSample,
            /* [in] */ void __RPC_FAR *pvContext)
	{
    printf ( "StreamSample: num=%d, time=%d, duration=%d, flags=%d.\n",
            wStreamNum, ( DWORD )cnsSampleTime, cnsSampleDuration, dwFlags );
	return S_OK;
    }

HRESULT STDMETHODCALLTYPE WMPyReaderCallbackAdvanced::OnTime( 
            /* [in] */ QWORD qwCurrentTime,
            /* [in] */ void __RPC_FAR *pvContext)
	{
	if(m_pyobj)
		{
		CallbackHelper helper("OnTime",m_pyobj);
		if(helper.cancall())
			{
			DWORD ms = (DWORD)qwCurrentTime/10000; // for small files
			PyObject *arg = Py_BuildValue("i", ms);
			helper.call(arg);
			}
		}	
	return S_OK;
	}

HRESULT STDMETHODCALLTYPE WMPyReaderCallbackAdvanced::OnStreamSelection( 
            /* [in] */ WORD wStreamCount,
            /* [in] */ WORD __RPC_FAR *pStreamNumbers,
            /* [in] */ WMT_STREAM_SELECTION __RPC_FAR *pSelections,
            /* [in] */ void __RPC_FAR *pvContext)
	{
	return S_OK;
	}

HRESULT STDMETHODCALLTYPE WMPyReaderCallbackAdvanced::OnOutputPropsChanged( 
            /* [in] */ DWORD dwOutputNum,
            /* [in] */ WM_MEDIA_TYPE __RPC_FAR *pMediaType,
            /* [in] */ void __RPC_FAR *pvContext )
	{
	return S_OK;
	}

HRESULT STDMETHODCALLTYPE WMPyReaderCallbackAdvanced::AllocateForOutput( 
            /* [in] */ DWORD dwOutputNum,
            /* [in] */ DWORD cbBuffer,
            /* [out] */ INSSBuffer __RPC_FAR *__RPC_FAR *ppBuffer,
            /* [in] */ void __RPC_FAR *pvContext)
	{
	return E_NOTIMPL;
	}

HRESULT STDMETHODCALLTYPE WMPyReaderCallbackAdvanced::AllocateForStream( 
            /* [in] */ WORD wStreamNum,
            /* [in] */ DWORD cbBuffer,
            /* [out] */ INSSBuffer __RPC_FAR *__RPC_FAR *ppBuffer,
            /* [in] */ void __RPC_FAR *pvContext)
	{
	return E_NOTIMPL;
	}



