
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

	// ++ IPyClientContext
    STDMETHOD (AddInterface) (THIS_ IUnknown* pIUnknown);

	private:
    LONG m_cRef;

	IUnknown *m_aInterfaces[8];
	int m_nInterfaces;
	};

HRESULT STDMETHODCALLTYPE CreateClientContext(
			IPyClientContext **ppI)
	{
	*ppI = new ClientContext();
	return S_OK;
	}


ClientContext::ClientContext()
:	m_cRef(1),
	m_nInterfaces(0)
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
    if (IsEqualIID(riid,IID_IUnknown))
		{
		AddRef();
		*ppvObject = this;
		return PNR_OK;
		}
	for(int i=0;i<m_nInterfaces;i++)
		{
		if(m_aInterfaces[i]->QueryInterface(riid, ppvObject) == PNR_OK)
			return PNR_OK;
		}
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
STDMETHODIMP
ClientContext::AddInterface(
    IUnknown* pIUnknown)
	{
	if(m_nInterfaces<8)
		{
		m_aInterfaces[m_nInterfaces++]=pIUnknown;
		pIUnknown->AddRef();
		return PNR_OK;
		}
	return PNR_OUTOFMEMORY;
	}