
/***********************************************************
Copyright 1991-2000 by Oratrix Development BV, Amsterdam, The Netherlands.

                        All Rights Reserved

******************************************************************/

#include "Python.h"

#include "rma.h" 

// our client context interfaces
#include "rmapyclient.h"

//
#include "fivemmap.h"

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
    STDMETHOD(SetSiteManager)(THIS_
		IRMASiteManager* p){
		m_pSiteManager=p;p->AddRef();return PNR_OK;
		} 
    STDMETHOD(SetCommonClassFactory)(THIS_
		IRMACommonClassFactory* p){
		m_pCCF=p;p->AddRef();return PNR_OK;
		} 
	
	private:
    LONG m_cRef;

    IRMASiteManager* m_pSiteManager;
    IRMACommonClassFactory* m_pCCF;
    FiveMinuteMap m_CreatedSites;
	
	PNxWindow m_PNxWindow;
	PyObject *m_pPythonWindow;
	BOOL m_WindowWasCreated;
	};

HRESULT STDMETHODCALLTYPE CreateSiteSupplier(
			IPySiteSupplier **ppI)
	{
	*ppI = new SiteSupplier();
	return S_OK;
	}


SiteSupplier::SiteSupplier()
:	m_cRef(1),
    m_pSiteManager(NULL),
    m_pCCF(NULL),
	m_pPythonWindow(NULL),
	m_WindowWasCreated(FALSE)
	{
    memset(&m_PNxWindow,0,sizeof(PNxWindow));	
	}

SiteSupplier::~SiteSupplier()
	{
	PN_RELEASE(m_pSiteManager);
	PN_RELEASE(m_pCCF);
	Py_XDECREF(m_pPythonWindow);
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
    /*
     * If there are no properties, then we can't really create a
     * site, because we have no idea what type of site is desired!
     */
    if (!pProps) return PNR_INVALID_PARAMETER;

    HRESULT		hres		= PNR_OK;
    IRMAValues*		pSiteProps	= NULL;
    IRMASiteWindowed*	pSiteWindowed	= NULL;
    IRMABuffer*		pValue		= NULL;
    UINT32		style		= 0;
    IRMASite*		pSite		= NULL;

    // Just let the RMA client core create a windowed site for us.
    hres = m_pCCF->CreateInstance(CLSID_IRMASiteWindowed,(void**)&pSiteWindowed);
    if (PNR_OK != hres)goto exit;

    hres = pSiteWindowed->QueryInterface(IID_IRMASite,(void**)&pSite);
    if (PNR_OK != hres)goto exit;

    hres = pSiteWindowed->QueryInterface(IID_IRMAValues,(void**)&pSiteProps);
    if (PNR_OK != hres)goto exit;

    /*
     * We need to figure out what type of site we are supposed to
     * to create. We need to "switch" between site user and site
     * properties. So look for the well known site user properties
     * that are mapped onto sites...
     */
    hres = pProps->GetPropertyCString("playto",pValue);
    if (PNR_OK == hres)
		{
		pSiteProps->SetPropertyCString("channel",pValue);
		PN_RELEASE(pValue);
		}
    else
		{
		hres = pProps->GetPropertyCString("name",pValue);
		if (PNR_OK == hres)
			{
			pSiteProps->SetPropertyCString("LayoutGroup",pValue);
    			PN_RELEASE(pValue);
			}
		}

#ifdef _WINDOWS
	if(m_PNxWindow.window)
		style = WS_CHILD | WS_VISIBLE | WS_CLIPCHILDREN;
	else
		style = WS_SYSMENU | WS_OVERLAPPED | WS_VISIBLE | WS_CLIPCHILDREN;
#endif

	if(!m_PNxWindow.window) {
		hres = pSiteWindowed->Create(m_PNxWindow.window,style);
		m_WindowWasCreated = 1;
	} else {
		hres=pSiteWindowed->AttachWindow(&m_PNxWindow);
	}

    if (PNR_OK != hres)goto exit;

    /*
     * We need to wait until we have set all the properties before
     * we add the site.
     */
    hres = m_pSiteManager->AddSite(pSite);
    if (PNR_OK != hres)goto exit;

    m_CreatedSites.SetAt((void*)uRequestID,pSite);
    pSite->AddRef();

exit:

    PN_RELEASE(pSiteProps);
    PN_RELEASE(pSiteWindowed);
    PN_RELEASE(pSite);

    return hres;
	}

STDMETHODIMP 
SiteSupplier::SitesNotNeeded
	(
	UINT32 uRequestID
	)
	{
    IRMASite* pSite = NULL;
    IRMASiteWindowed* pSiteWindowed = NULL;
    void* pVoid = NULL;

    if (!m_CreatedSites.Lookup((void*)uRequestID,pVoid))
		return PNR_INVALID_PARAMETER;
    pSite = (IRMASite*)pVoid;
    m_pSiteManager->RemoveSite(pSite);

	pSite->QueryInterface(IID_IRMASiteWindowed,(void**)&pSiteWindowed);
	if(m_WindowWasCreated) {
		pSiteWindowed->Destroy();
	} else {
		pSiteWindowed->DetachWindow();
#ifdef _WINDOWS
		::InvalidateRect((HWND)m_PNxWindow.window,NULL,TRUE);
#endif
		Py_XDECREF(m_pPythonWindow);
		m_pPythonWindow = NULL;
		memset(&m_PNxWindow,0,sizeof(PNxWindow));
	}
	pSiteWindowed->Release();

	// ref count = 1; deleted from this object's view!
    pSite->Release();

    m_CreatedSites.RemoveKey((void*)uRequestID);

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
	Py_XDECREF(m_pPythonWindow);
	m_pPythonWindow = pw;
	Py_XINCREF(m_pPythonWindow);
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
