
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

class ClientAdviseSink : public IPyClientAdviseSink
	{
	public:
	ClientAdviseSink();
	~ClientAdviseSink();

	// IUnknown
    STDMETHOD (QueryInterface ) (THIS_ REFIID ID, void** ppInterfaceObj);
    STDMETHOD_(UINT32, AddRef ) (THIS);
    STDMETHOD_(UINT32, Release) (THIS);

    // IRMAClientAdviseSink
    STDMETHOD (OnPosLength)  (THIS_ UINT32 ulPosition, UINT32 ulLength);
    STDMETHOD (OnPresentationOpened) (THIS);
    STDMETHOD (OnPresentationClosed) (THIS);
    STDMETHOD (OnStatisticsChanged)  (THIS);
    STDMETHOD (OnPreSeek)    (THIS_ UINT32 ulOldTime, UINT32 ulNewTime);
    STDMETHOD (OnPostSeek)   (THIS_ UINT32 ulOldTime, UINT32 ulNewTime);
    STDMETHOD (OnStop)       (THIS);
    STDMETHOD (OnPause)      (THIS_ UINT32 ulTime);
    STDMETHOD (OnBegin)	     (THIS_ UINT32 ulTime);
    STDMETHOD (OnBuffering)  (THIS_ UINT32 ulFlags, UINT16 unPercentComplete);
    STDMETHOD (OnContacting) (THIS_ const char* pHostName);
	
	// ++ IPyClientAdviseSink
    STDMETHOD(SetPyAdviceSink)(THIS_
				PyObject *obj);
	
	private:
    LONG m_cRef;

	PyObject *m_pyAdviceSink;	
	};

HRESULT STDMETHODCALLTYPE CreateClientAdviseSink(
			IPyClientAdviseSink **ppI)
	{
	*ppI = new ClientAdviseSink();
	return S_OK;
	}


ClientAdviseSink::ClientAdviseSink()
:	m_cRef(1)
	{
	}

ClientAdviseSink::~ClientAdviseSink()
	{
	}

STDMETHODIMP
ClientAdviseSink::QueryInterface(
    REFIID riid,
    void **ppvObject)
	{
	return E_NOINTERFACE;
	}

STDMETHODIMP_(UINT32)
ClientAdviseSink::AddRef()
	{
    return  InterlockedIncrement(&m_cRef);
	}

STDMETHODIMP_(UINT32)
ClientAdviseSink::Release()
	{
    ULONG uRet = InterlockedDecrement(&m_cRef);
	if(uRet==0) 
		{
		delete this;
		}
    return uRet;
	}

STDMETHODIMP
ClientAdviseSink::OnPosLength(UINT32 ulPosition, UINT32 ulLength)
	{
	return PNR_OK;
	}

STDMETHODIMP
ClientAdviseSink::OnPresentationOpened()
	{
	return PNR_OK;
	}

STDMETHODIMP
ClientAdviseSink::OnPresentationClosed()
	{
	return PNR_OK;
	}

STDMETHODIMP
ClientAdviseSink::OnStatisticsChanged()
	{
	return PNR_OK;
	}

STDMETHODIMP
ClientAdviseSink::OnPreSeek(UINT32 ulOldTime, UINT32 ulNewTime)
	{
	return PNR_OK;
	}

STDMETHODIMP
ClientAdviseSink::OnPostSeek(UINT32 ulOldTime, UINT32 ulNewTime)
	{
	return PNR_OK;
	}

STDMETHODIMP
ClientAdviseSink::OnStop()
	{
	return PNR_OK;
	}

STDMETHODIMP
ClientAdviseSink::OnPause(UINT32 ulTime)
	{
	return PNR_OK;
	}

STDMETHODIMP
ClientAdviseSink::OnBegin(UINT32 ulTime)
	{
	return PNR_OK;
	}

STDMETHODIMP
ClientAdviseSink::OnBuffering(UINT32 ulFlags, UINT16 unPercentComplete)
	{
	return PNR_OK;
	}

STDMETHODIMP
ClientAdviseSink::OnContacting(const char* pHostName)
	{
	return PNR_OK;
	}


STDMETHODIMP 
ClientAdviseSink::SetPyAdviceSink(PyObject *obj)
	{
	Py_XDECREF(m_pyAdviceSink);
	if(obj==Py_None)m_pyAdviceSink=NULL;
	else m_pyAdviceSink=obj;
	Py_XINCREF(m_pyAdviceSink);
	return PNR_OK;
	}
