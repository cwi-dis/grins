
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

#define RELEASE(x) if(x) x->Release();x=NULL;
extern void seterror(const char *msg);

class WMPyReaderCallback : public IWMPyReaderCallback
{
public:
    WMPyReaderCallback(PyObject *pyobj);
    ~WMPyReaderCallback();
    
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

private:
    LONG    m_cRef;
	
	PyObject *m_pyobj;

    HRESULT m_hrOpen;
    HANDLE m_hOpenEvent;

    BOOL    m_isEOF;
    HANDLE  m_hCompletionEvent;
};

HRESULT STDMETHODCALLTYPE WMCreatePyReaderCallback(
			PyObject *pyobj,
			IWMPyReaderCallback **ppI)
{
	*ppI = new WMPyReaderCallback(pyobj);
	return S_OK;
}

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
    CloseHandle(m_hOpenEvent);
	CloseHandle(m_hCompletionEvent);
}


HRESULT STDMETHODCALLTYPE WMPyReaderCallback::QueryInterface(
    REFIID riid,
    void **ppvObject)
{
    return E_NOINTERFACE;
}

ULONG STDMETHODCALLTYPE WMPyReaderCallback::AddRef()
{
	Py_XINCREF(m_pyobj);	
    return  InterlockedIncrement(&m_cRef);
}

ULONG STDMETHODCALLTYPE WMPyReaderCallback::Release()
{
	Py_XDECREF(m_pyobj);	
    ULONG uRet = InterlockedDecrement(&m_cRef);
	if(uRet==0) delete this;
    return uRet;
}

HRESULT STDMETHODCALLTYPE WMPyReaderCallback::SetListener(
			/* [in] */ 	PyObject *pyobj)
{
	Py_XDECREF(m_pyobj);
	if(pyobj==Py_None) m_pyobj=NULL;
	else m_pyobj=pyobj;
	Py_XINCREF(m_pyobj);	
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
	*pdwWaitRes = WaitForSingleObject(m_hCompletionEvent,dwMilliseconds);
	return S_OK;
}

HRESULT STDMETHODCALLTYPE WMPyReaderCallback::OnStatus( 
        /* [in] */ WMT_STATUS Status, 
        /* [in] */ HRESULT hr,
        /* [in] */ WMT_ATTR_DATATYPE dwType,
        /* [in] */ BYTE __RPC_FAR *pValue,
        /* [in] */ VOID *pvContext )
{
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
    return S_OK;
}


