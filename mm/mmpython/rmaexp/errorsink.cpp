
/***********************************************************
Copyright 1991-2000 by Oratrix Development BV, Amsterdam, The Netherlands.

                        All Rights Reserved

******************************************************************/

#include "Python.h"

#include "pntypes.h" 

#if defined(_ABIO32) && _ABIO32 != 0
typedef int bool;
enum { false, true, };
#endif


#include "pncom.h"
#include "pnresult.h"

#include "rmacore.h"

#include "pnwintyp.h"
#include "rmawin.h"
#include "rmaerror.h"
#include "rmaclsnk.h"
#include "rmaauth.h"

// our client context interfaces
#include "rmapyclient.h"

class ErrorSink : public IPyErrorSink
	{
	public:
	ErrorSink();
	~ErrorSink();

	// IUnknown
    STDMETHOD (QueryInterface ) (THIS_ REFIID ID, void** ppInterfaceObj);
    STDMETHOD_(UINT32, AddRef ) (THIS);
    STDMETHOD_(UINT32, Release) (THIS);

	// IRMAErrorSink
    STDMETHOD(ErrorOccurred)	(THIS_
				const UINT8	unSeverity,  
				const ULONG32	ulRMACode,
				const ULONG32	ulUserCode,
				const char*	pUserString,
				const char*	pMoreInfoURL
				);
	
	// ++ IPyErrorSink
    STDMETHOD(SetPyErrorSink)(THIS_
				PyObject *obj);
	
	private:
    LONG m_cRef;

	PyObject *m_pyErrorSink;	
	};

HRESULT STDMETHODCALLTYPE CreateErrorSink(
			IPyErrorSink **ppI)
	{
	*ppI = new ErrorSink();
	return S_OK;
	}


ErrorSink::ErrorSink()
:	m_cRef(1)
	{
	}

ErrorSink::~ErrorSink()
	{
	}

STDMETHODIMP
ErrorSink::QueryInterface(
    REFIID riid,
    void **ppvObject)
	{
    if (IsEqualIID(riid,IID_IUnknown))
		{
		AddRef();
		*ppvObject = this;
		return PNR_OK;
		}
	else if(IsEqualIID(riid,IID_IRMAErrorSink))
		{
		AddRef();
		*ppvObject = this;
		return PNR_OK;
		}
    *ppvObject = NULL;	
	return PNR_NOINTERFACE;
	}

STDMETHODIMP_(UINT32)
ErrorSink::AddRef()
	{
    return  InterlockedIncrement(&m_cRef);
	}

STDMETHODIMP_(UINT32)
ErrorSink::Release()
	{
    ULONG uRet = InterlockedDecrement(&m_cRef);
	if(uRet==0) 
		{
		delete this;
		}
    return uRet;
	}

STDMETHODIMP 
ErrorSink::ErrorOccurred
	(
	const UINT8	unSeverity,  
	const ULONG32	ulRMACode,
	const ULONG32	ulUserCode,
	const char*	pUserString,
	const char*	pMoreInfoURL
	)
	{
	return PNR_OK;
	}

STDMETHODIMP 
ErrorSink::SetPyErrorSink(PyObject *obj)
	{
	Py_XDECREF(m_pyErrorSink);
	if(obj==Py_None)m_pyErrorSink=NULL;
	else m_pyErrorSink=obj;
	Py_XINCREF(m_pyErrorSink);
	return PNR_OK;
	}
