
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

class AuthenticationManager : public IPyAuthenticationManager
	{
	public:
	AuthenticationManager();
	~AuthenticationManager();

	// IUnknown
    STDMETHOD (QueryInterface ) (THIS_ REFIID ID, void** ppInterfaceObj);
    STDMETHOD_(UINT32, AddRef ) (THIS);
    STDMETHOD_(UINT32, Release) (THIS);

    // IRMAAuthenticationManager
    STDMETHOD(HandleAuthenticationRequest) (IRMAAuthenticationManagerResponse* pResponse);
	
	private:
    LONG m_cRef;
	};

HRESULT STDMETHODCALLTYPE CreateAuthenticationManager(
			IPyAuthenticationManager **ppI)
	{
	*ppI = new AuthenticationManager();
	return S_OK;
	}


AuthenticationManager::AuthenticationManager()
:	m_cRef(1)
	{
	}

AuthenticationManager::~AuthenticationManager()
	{
	}

STDMETHODIMP
AuthenticationManager::QueryInterface(
    REFIID riid,
    void **ppvObject)
	{
	return E_NOINTERFACE;
	}

STDMETHODIMP_(UINT32)
AuthenticationManager::AddRef()
	{
    return  InterlockedIncrement(&m_cRef);
	}

STDMETHODIMP_(UINT32)
AuthenticationManager::Release()
	{
    ULONG uRet = InterlockedDecrement(&m_cRef);
	if(uRet==0) 
		{
		delete this;
		}
    return uRet;
	}

STDMETHODIMP 
AuthenticationManager::HandleAuthenticationRequest
	(
    IRMAAuthenticationManagerResponse* pResponse
	)
	{
	return PNR_OK;
	}

