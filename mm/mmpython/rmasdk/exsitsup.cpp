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

#ifdef _WIN16
    #include <windows.h>
#endif

#include "fivemmap.h"
#include "exsitsup.h"


#include "rmasite2.h"
#include "fivemlist.h"
#include "rmavsurf.h"
#include "exvsurf.h"
#include "exnwsite.h"


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
    , m_pWindowlessSite(NULL)
	, m_pyVideoSurface(NULL)
{
    if (m_pUnkPlayer)
    {
	m_pUnkPlayer->QueryInterface(IID_IRMASiteManager,
			(void**)&m_pSiteManager);

	m_pUnkPlayer->QueryInterface(IID_IRMACommonClassFactory,
			(void**)&m_pCCF);

	m_pUnkPlayer->AddRef();
    }
};


/****************************************************************************
 *  ExampleSiteSupplier::ExampleSiteSupplier                  ref:  exsitup.h
 *
 *  Destructor
 */
ExampleSiteSupplier::~ExampleSiteSupplier()
{
	Py_XDECREF(m_pyVideoSurface);
    PN_RELEASE(m_pSiteManager);
    PN_RELEASE(m_pCCF);
    PN_RELEASE(m_pUnkPlayer);
}

void ExampleSiteSupplier::SetPyVideoSurface(PyObject *obj)
	{
	Py_XDECREF(m_pyVideoSurface);
	if(obj==Py_None)m_pyVideoSurface=NULL;
	else m_pyVideoSurface=obj;
	Py_XINCREF(m_pyVideoSurface);
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
    if (!pProps)
    {
	return PNR_INVALID_PARAMETER;
    }

    HRESULT		hres		= PNR_OK;
    IRMAValues*		pSiteProps	= NULL;
    IRMABuffer*		pValue		= NULL;
    UINT32		style		= 0;
    IRMASite*		pSite		= NULL;


    // instead of using the CCF to create a IRMASiteWindowed, create our windowless
    // site here...
    m_pWindowlessSite = new ExampleWindowlessSite(m_pUnkPlayer);
    if (!m_pWindowlessSite)
    {
	goto exit;
    }
    m_pWindowlessSite->AddRef();
	m_pWindowlessSite->m_pVideoSurface->SetPyVideoSurface(m_pyVideoSurface);
    hres = m_pWindowlessSite->QueryInterface(IID_IRMASite,(void**)&pSite);
    if (PNR_OK != hres)
    {
	goto exit;
    }

    hres = m_pWindowlessSite->QueryInterface(IID_IRMAValues,(void**)&pSiteProps);
    if (PNR_OK != hres)
    {
	goto exit;
    }

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

    /*
     * We need to wait until we have set all the properties before
     * we add the site.
     */
    hres = m_pSiteManager->AddSite(pSite);
    if (PNR_OK != hres)
    {
	goto exit;
    }

    m_CreatedSites.SetAt((void*)uRequestID,pSite);
    pSite->AddRef();

exit:

    PN_RELEASE(pSiteProps);
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
    IRMASite*		pSite = NULL;
    void*		pVoid = NULL;

    if (!m_CreatedSites.Lookup((void*)uRequestID,pVoid))
    {
	return PNR_INVALID_PARAMETER;
    }
    pSite = (IRMASite*)pVoid;

    m_pSiteManager->RemoveSite(pSite);

    // delete our windowless site now (sets to NULL)
    PN_RELEASE(m_pWindowlessSite);

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
	Py_XINCREF(m_pyVideoSurface);
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
	if(m_pyVideoSurface && m_pyVideoSurface->ob_refcnt==1)
		{
		Py_XDECREF(m_pyVideoSurface);
		m_pyVideoSurface=NULL;
		}
	else Py_XDECREF(m_pyVideoSurface);

    if (InterlockedDecrement(&m_lRefCount) > 0)
    {
        return m_lRefCount;
    }

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
