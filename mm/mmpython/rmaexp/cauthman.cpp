
/***********************************************************
Copyright 1991-2000 by Oratrix Development BV, Amsterdam, The Netherlands.

                        All Rights Reserved

******************************************************************/

#include "Python.h"

#include "rma.h" 

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
    if (IsEqualIID(riid,IID_IUnknown))
		{
		AddRef();
		*ppvObject = this;
		return PNR_OK;
		}
	else if(IsEqualIID(riid,IID_IRMAAuthenticationManager))
		{
		AddRef();
		*ppvObject = this;
		return PNR_OK;
		}
    *ppvObject = NULL;	
	return PNR_NOINTERFACE;
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
    char username[1024];
    char password[1024];

    fprintf(stderr, "Authorization needed for this content.\n");
    fprintf(stderr, "Username: ");
    fflush(stderr);
    if(fgets(username, 1024, stdin))
		{
		char* c;
		for(c = username + strlen(username) - 1; 
			c > username && isspace(*c);
			c--)
			;
		if(c <= username)
			return PNR_FAIL;
		*(c+1) = 0;

		fprintf(stderr, "Password: ");
		fflush(stderr);
		if(fgets(password, 1024, stdin))
			{
			for(c = password + strlen(password) - 1; 
			c > password && isspace(*c);
			c--);
			if(c <= password)
			return PNR_FAIL;
			*(c+1) = 0;
			pResponse->AuthenticationRequestDone(PNR_OK, username, password);
			return PNR_OK;
			}
		}
    return pResponse->AuthenticationRequestDone(PNR_NOT_AUTHORIZED, 
						NULL, 
						NULL);
	}

