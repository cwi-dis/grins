/****************************************************************************
 * 
 *  $Id$
 *  
 */

/****************************************************************************
 * Includes
 */
#include "pncom.h"
#include "pntypes.h"
#include "pnwintyp.h"
#include "rmawin.h"
#include "rmapckts.h"
#include "rmacomm.h"
#include "fivemmap.h"
#include "exsitsup.h"


/****************************************************************************
 *  ExampleSiteSupplier::ExampleSiteSupplier                  ref:  exsitup.h
 *
 *  Constructor
 */
ExampleSiteSupplier::ExampleSiteSupplier(IUnknown* pUnkPlayer)
    : m_lRefCount(0)
    , m_pSiteManager(NULL)
    , m_pCCF(NULL)
    , m_pUnkPlayer(pUnkPlayer)

	,m_showInNewWnd(FALSE)
	{
    if (m_pUnkPlayer)
		{
		m_pUnkPlayer->QueryInterface(IID_IRMASiteManager,
			(void**)&m_pSiteManager);

		m_pUnkPlayer->QueryInterface(IID_IRMACommonClassFactory,
			(void**)&m_pCCF);

		m_pUnkPlayer->AddRef();
		}
	memset(&m_PNxWindow,0,sizeof(PNxWindow));
	};


/****************************************************************************
 *  ExampleSiteSupplier::ExampleSiteSupplier                  ref:  exsitup.h
 *
 *  Destructor
 */
ExampleSiteSupplier::~ExampleSiteSupplier()
	{
    PN_RELEASE(m_pSiteManager);
    PN_RELEASE(m_pCCF);
    PN_RELEASE(m_pUnkPlayer);
	}


// IRMASiteSupplier Interface Methods

/****************************************************************************
 *  IRMASiteSupplier::SitesNeeded                              ref:  rmawin.h
 *
 */

STDMETHODIMP 
ExampleSiteSupplier::SitesNeeded
	(
    UINT32	uRequestID,
    IRMAValues*	pProps
	)
	{
    /*
     * If there are no properties, then we can't really create a
     * site, because we have no idea what type of site is desired!
     */
    if (!pProps)return PNR_INVALID_PARAMETER;

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

	if(m_showInNewWnd || !m_PNxWindow.window)
		hres = pSiteWindowed->Create(m_PNxWindow.window,style);
	else
		hres=pSiteWindowed->AttachWindow(&m_PNxWindow);

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


/****************************************************************************
 *  IRMASiteSupplier::SitesNotNeeded                           ref:  rmawin.h
 *
 */
STDMETHODIMP 
ExampleSiteSupplier::SitesNotNeeded(UINT32 uRequestID)
	{
    IRMASite* pSite = NULL;
    IRMASiteWindowed* pSiteWindowed = NULL;
    void* pVoid = NULL;

    if (!m_CreatedSites.Lookup((void*)uRequestID,pVoid))
		return PNR_INVALID_PARAMETER;
    pSite = (IRMASite*)pVoid;
    m_pSiteManager->RemoveSite(pSite);

	pSite->QueryInterface(IID_IRMASiteWindowed,(void**)&pSiteWindowed);
	if(m_showInNewWnd)
		pSiteWindowed->Destroy();
	else 
		{
		pSiteWindowed->DetachWindow();
#ifdef _WINDOWS
		::InvalidateRect((HWND)m_PNxWindow.window,NULL,TRUE);
#endif
		}
	pSiteWindowed->Release();

	// ref count = 1; deleted from this object's view!
    pSite->Release();

    m_CreatedSites.RemoveKey((void*)uRequestID);

    return PNR_OK;
	}


/****************************************************************************
 *  IRMASiteSupplier::BeginChangeLayout                        ref:  rmawin.h
 *
 */
STDMETHODIMP 
ExampleSiteSupplier::BeginChangeLayout()
	{
    return PNR_OK;
	}


/****************************************************************************
 *  IRMASiteSupplier::DoneChangeLayout                         ref:  rmawin.h
 *
 */
STDMETHODIMP 
ExampleSiteSupplier::DoneChangeLayout()
	{
    return PNR_OK;
	}


// IUnknown COM Interface Methods

/****************************************************************************
 *  IUnknown::AddRef                                            ref:  pncom.h
 *
 *  This routine increases the object reference count in a thread safe
 *  manner. The reference count is used to manage the lifetime of an object.
 *  This method must be explicitly called by the user whenever a new
 *  reference to an object is used.
 */
STDMETHODIMP_(ULONG32) 
ExampleSiteSupplier::AddRef()
	{
    return InterlockedIncrement(&m_lRefCount);
	}


/****************************************************************************
 *  IUnknown::Release                                           ref:  pncom.h
 *
 *  This routine decreases the object reference count in a thread safe
 *  manner, and deletes the object if no more references to it exist. It must
 *  be called explicitly by the user whenever an object is no longer needed.
 */
STDMETHODIMP_(ULONG32) 
ExampleSiteSupplier::Release()
	{
    if (InterlockedDecrement(&m_lRefCount) > 0)
        return m_lRefCount;
    delete this;
    return 0;
	}


/****************************************************************************
 *  IUnknown::QueryInterface                                    ref:  pncom.h
 *
 *  This routine indicates which interfaces this object supports. If a given
 *  interface is supported, the object's reference count is incremented, and
 *  a reference to that interface is returned. Otherwise a NULL object and
 *  error code are returned. This method is called by other objects to
 *  discover the functionality of this object.
 */
STDMETHODIMP 
ExampleSiteSupplier::QueryInterface(REFIID riid, void** ppvObj)
	{
    if (IsEqualIID(riid, IID_IUnknown))
		{
		AddRef();
		*ppvObj = (IUnknown*)(IRMASiteSupplier*)this;
		return PNR_OK;
		}
    else if (IsEqualIID(riid, IID_IRMASiteSupplier))
		{
		AddRef();
		*ppvObj = (IRMASiteSupplier*)this;
		return PNR_OK;
		}
    *ppvObj = NULL;
    return PNR_NOINTERFACE;
	}

