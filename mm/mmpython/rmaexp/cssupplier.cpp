
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

class SiteSupplier : public IPySiteSupplier
	{
	public:
	SiteSupplier();
	~SiteSupplier();

	// IUnknown
    STDMETHOD (QueryInterface ) (THIS_ REFIID ID, void** ppInterfaceObj);
    STDMETHOD_(UINT32, AddRef ) (THIS);
    STDMETHOD_(UINT32, Release) (THIS);

    // IRMASiteSupplier
    STDMETHOD(SitesNeeded) (THIS_ UINT32 uRequestID, IRMAValues* pSiteProps);
    STDMETHOD(SitesNotNeeded) (THIS_ UINT32 uRequestID);
    STDMETHOD(BeginChangeLayout) (THIS);
    STDMETHOD(DoneChangeLayout) (THIS);

	// ++ IPySiteSupplier
    STDMETHOD(SetOsWindow)(THIS_
				void* p, 
				PyObject *pw);
    STDMETHOD(SetOsWindowPosSize)(THIS_
				PNxPoint p, 
				PNxSize s);
	
	private:
    LONG m_cRef;
	
	PNxWindow m_PNxWindow;
	PyObject *pPythonWindow;	
	};

HRESULT STDMETHODCALLTYPE CreateSiteSupplier(
			IPySiteSupplier **ppI)
	{
	*ppI = new SiteSupplier();
	return S_OK;
	}


SiteSupplier::SiteSupplier()
:	m_cRef(1)
	{
	}

SiteSupplier::~SiteSupplier()
	{
	}

STDMETHODIMP
SiteSupplier::QueryInterface(
    REFIID riid,
    void **ppvObject)
	{
    if (IsEqualIID(riid,IID_IUnknown))
		{
		AddRef();
		*ppvObject = this;
		return PNR_OK;
		}
	else if(IsEqualIID(riid,IID_IRMASiteSupplier))
		{
		AddRef();
		*ppvObject = this;
		return PNR_OK;
		}
    *ppvObject = NULL;	
	return PNR_NOINTERFACE;
	}

STDMETHODIMP_(UINT32)
SiteSupplier::AddRef()
	{
    return  InterlockedIncrement(&m_cRef);
	}

STDMETHODIMP_(UINT32)
SiteSupplier::Release()
	{
    ULONG uRet = InterlockedDecrement(&m_cRef);
	if(uRet==0) 
		{
		delete this;
		}
    return uRet;
	}


STDMETHODIMP 
SiteSupplier::SitesNeeded
	(
    UINT32	uRequestID,
    IRMAValues*	pProps
	)
	{
	return PNR_OK;
	}

STDMETHODIMP 
SiteSupplier::SitesNotNeeded
	(
	UINT32 uRequestID
	)
	{
	return PNR_OK;
	}

STDMETHODIMP 
SiteSupplier::BeginChangeLayout()
	{
    return PNR_OK;
	}

STDMETHODIMP 
SiteSupplier::DoneChangeLayout()
	{
    return PNR_OK;
	}


STDMETHODIMP
SiteSupplier::SetOsWindow(void* p, PyObject *pw) 
	{
	m_PNxWindow.window = p;
	Py_XDECREF(pPythonWindow);
	pPythonWindow = pw;
	Py_XINCREF(pPythonWindow);
    return PNR_OK;
	}
	
STDMETHODIMP
SiteSupplier::SetOsWindowPosSize(PNxPoint p, PNxSize s) 
	{
	m_PNxWindow.x = p.x;
	m_PNxWindow.y = p.y;
	m_PNxWindow.width = s.cx;
	m_PNxWindow.height = s.cy;
	m_PNxWindow.clipRect.left = p.x;
	m_PNxWindow.clipRect.top = p.y;
	m_PNxWindow.clipRect.right = p.x+s.cx;
	m_PNxWindow.clipRect.bottom = p.y+s.cy;
    return PNR_OK;
	}
