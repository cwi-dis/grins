
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

class ClientContext : public IPyClientContext
	{
	public:
	ClientContext();
	~ClientContext();

	// IUnknown
    STDMETHOD (QueryInterface ) (THIS_ REFIID ID, void** ppInterfaceObj);
    STDMETHOD_(UINT32, AddRef ) (THIS);
    STDMETHOD_(UINT32, Release) (THIS);

	private:
    LONG m_cRef;
	};

HRESULT STDMETHODCALLTYPE CreateClientContext(
			IPyClientContext **ppI)
	{
	*ppI = new ClientContext();
	return S_OK;
	}


ClientContext::ClientContext()
:	m_cRef(1)
	{
	}

ClientContext::~ClientContext()
	{
	}

STDMETHODIMP
ClientContext::QueryInterface(
    REFIID riid,
    void **ppvObject)
	{
	return E_NOINTERFACE;
	}

STDMETHODIMP_(UINT32)
ClientContext::AddRef()
	{
    return  InterlockedIncrement(&m_cRef);
	}

STDMETHODIMP_(UINT32)
ClientContext::Release()
	{
    ULONG uRet = InterlockedDecrement(&m_cRef);
	if(uRet==0) 
		{
		delete this;
		}
    return uRet;
	}
