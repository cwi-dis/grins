/****************************************************************************
 * 
 *  $Id$
 *  
 *  Copyright (C) 1995,1996,1997 Progressive Networks.
 *  All rights reserved.
 *  
 *  Progressive Networks Confidential and Proprietary information.
 *  Do not redistribute.
 *
 *  Basic PN implementation of the IRMASite classes.
 *
 *
 */

#include <stdio.h>

#ifdef _UNIX
#include <X11/Xlib.h>
#endif

#include "pncom.h"
#include "pntypes.h"
#include "pnwintyp.h"
#include "rmapckts.h"
#include "rmawin.h"
#include "rmaengin.h"
#include "rmasite2.h"
#include "rmaevent.h"
#include "rmacomm.h"

#include "fivemlist.h"

#include "rmavsurf.h"

#include "exvsurf.h"
#include "exnwsite.h"

#include "rmapckts.h"


/************************************************************************
 *  Method:
 *    Constructor
 */
ExampleWindowlessSite::ExampleWindowlessSite(IUnknown* pContext, 
					     IUnknown* pUnkOuter)
    : m_lRefCount(0)
    , m_pUser(NULL)
    , m_pParentSite(NULL)
    , m_pUnkOuter(pUnkOuter)
    , m_pWatcher(NULL)
    , m_pContext(pContext)
    , m_pVideoSurface(NULL)
    , m_bIsVisible(TRUE)
    , m_pValues(NULL)
    , m_lZOrder(0)
    , m_bInDestructor(FALSE)
    , m_pCCF(NULL)
    , m_bDamaged(FALSE)
    , m_bInRedraw(FALSE)
{
    // addref the context 
    m_pContext->AddRef();

    // get the CCF 
    m_pContext->QueryInterface(IID_IRMACommonClassFactory,
			       (void**)&m_pCCF);

    // addref CCF
    m_pCCF->CreateInstance(CLSID_IRMAValues,(void**)&m_pValues);

    /* If we are not being aggregated, then point our outer
     * unknown to our own implementation of a non-delegating
     * unknown... this is like aggregating ourselves<g>
     */
    if (pUnkOuter == NULL)
    {
	m_pUnkOuter = (IUnknown*)(NonDelegatingUnknown*) this;
    }

    m_size.cx = 0;
    m_size.cy = 0;
    m_position.x = 0;
    m_position.y = 0;

    // create video surface
    m_pVideoSurface = new ExampleVideoSurface(m_pContext, this);
    m_pVideoSurface->AddRef();

    m_bIsChildWindow = TRUE;
}


/************************************************************************
 *  Method:
 *    Destructor
 */
ExampleWindowlessSite::~ExampleWindowlessSite()
{
    m_bInDestructor = TRUE;

    // Clean up all child sites

    int n = 0;
    int count = m_Children.Count();
    for (n=0; n<count; n++)
    {
 	ExSiteInfo* pSiteInfo = (ExSiteInfo*) m_Children.GetFirst();
	DestroyChild(pSiteInfo->m_pSite);
	delete pSiteInfo;
	m_Children.RemoveHead();
    }

    // clean up passive site watchers 

    count = m_PassiveSiteWatchers.Count();
    for (n=0; n<count; n++)
    {
	IRMAPassiveSiteWatcher* pWatcher =
	    (IRMAPassiveSiteWatcher*) m_PassiveSiteWatchers.GetFirst();
	PN_RELEASE(pWatcher);
	m_PassiveSiteWatchers.RemoveHead();
    }

    // release intefaces
    PN_RELEASE(m_pValues);
    PN_RELEASE(m_pCCF);
    PN_RELEASE(m_pContext);
}


/************************************************************************
 *  Method:
 *    ExampleWindowlessSite::SetParentSite
 */
void		
ExampleWindowlessSite::SetParentSite(ExampleWindowlessSite* pParentSite)
{
    m_pParentSite = pParentSite;
}


/************************************************************************
 *  Method:
 *    IUnknown::QueryInterface
 */
STDMETHODIMP 
ExampleWindowlessSite::NonDelegatingQueryInterface(REFIID riid, void** ppvObj)
{
    if (IsEqualIID(riid, IID_IUnknown))
    {
	AddRef();
	*ppvObj = (IUnknown*)(IRMASite*)this;
	return PNR_OK;
    }
    else if (IsEqualIID(riid, IID_IRMAValues))
    {
	AddRef();
	*ppvObj = (IRMAValues*)this;
	return PNR_OK;
    }
    else if (IsEqualIID(riid, IID_IRMASite))
    {
	AddRef();
	*ppvObj = (IRMASite*)this;
	return PNR_OK;
    }
    else if (IsEqualIID(riid, IID_IRMASite2))
    {
	AddRef();
	*ppvObj = (IRMASite2*)this;
	return PNR_OK;
    }
    else if (IsEqualIID(riid, IID_IRMASiteWindowless))
    {
	AddRef();
	*ppvObj = (IRMASiteWindowless*)this;
	return PNR_OK;
    }

    *ppvObj = NULL;
    return PNR_NOINTERFACE;
}


/************************************************************************
 *  Method:
 *    IUnknown::AddRef
 */
STDMETHODIMP_(ULONG32) 
ExampleWindowlessSite::NonDelegatingAddRef()
{
    return InterlockedIncrement(&m_lRefCount);
}


/************************************************************************
 *  Method:
 *    IUnknown::Release
 */
STDMETHODIMP_(ULONG32) 
ExampleWindowlessSite::NonDelegatingRelease()
{
    if (InterlockedDecrement(&m_lRefCount) > 0)
    {
        return m_lRefCount;
    }

    delete this;
    return 0;
}


/************************************************************************
 *  Method:
 *    IUnknown::QueryInterface
 */
STDMETHODIMP 
ExampleWindowlessSite::QueryInterface(REFIID riid, void** ppvObj)
{
    return m_pUnkOuter->QueryInterface(riid,ppvObj);
}


/************************************************************************
 *  Method:
 *    IUnknown::AddRef
 */
STDMETHODIMP_(ULONG32) 
ExampleWindowlessSite::AddRef()
{
    return m_pUnkOuter->AddRef();
}


/************************************************************************
 *  Method:
 *    IUnknown::Release
 */
STDMETHODIMP_(ULONG32) 
ExampleWindowlessSite::Release()
{
    return m_pUnkOuter->Release();
}


/************************************************************************
 *  Method:
 *    IRMASite::AttachUser
 */
STDMETHODIMP 
ExampleWindowlessSite::AttachUser(IRMASiteUser* /*IN*/ pUser)
{
    HRESULT result = PNR_FAIL;

    if (m_pUser) return PNR_UNEXPECTED;

    IRMASite* pOuterSite;
    m_pUnkOuter->QueryInterface(IID_IRMASite, (void**)&pOuterSite);
    if (pOuterSite)
    {
	result = pUser->AttachSite(pOuterSite);

	pOuterSite->Release();
    }
    
    if (PNR_OK == result)
    {
	m_pUser = pUser;
	m_pUser->AddRef();
    }

    return result;
}

/************************************************************************
 *  Method:
 *    IRMASite::DetachUser
 */
STDMETHODIMP 
ExampleWindowlessSite::DetachUser()
{
    HRESULT result = PNR_OK;
    if (!m_pUser) return PNR_UNEXPECTED;

    result = m_pUser->DetachSite();
    
    if (PNR_OK == result)
    {
	m_pUser->Release();
	m_pUser = NULL;
    }

    return result;
}

/************************************************************************
 *  Method:
 *    IRMASite::GetUser
 */
STDMETHODIMP 
ExampleWindowlessSite::GetUser(REF(IRMASiteUser*) /*OUT*/ pUser)
{
    HRESULT result = PNR_OK;
    if (!m_pUser) return PNR_UNEXPECTED;

    pUser = m_pUser;
    pUser->AddRef();

    return result;
}


/************************************************************************
 *  Method:
 *    IRMASite::CreateChild
 */
STDMETHODIMP 
ExampleWindowlessSite::CreateChild(REF(IRMASite*) /*OUT*/ pChildSite)
{
    HRESULT result = PNR_OK;


    /* Create an instance of ExampleWindowlessSite, let it know it's
     * in child window mode.
     */
    ExampleWindowlessSite* pChildSiteWindowless = new ExampleWindowlessSite(m_pContext);
    pChildSiteWindowless->AddRef();
    pChildSiteWindowless->SetParentSite(this);

    /* Get the IRMASite interface from the child to return to the
     * outside world.
     */
    pChildSiteWindowless->QueryInterface(IID_IRMASite, (void**)&pChildSite);


    /*
     * Store the ExampleWindowlessSite in a list of child windows, always keep
     * a reference to it.
     * ExSiteInfo does an AddRef in constructor
     */    
     
    ExSiteInfo* pSiteInfo = new ExSiteInfo(pChildSite, (void*) pChildSiteWindowless);   
    m_Children.Add(pSiteInfo);

    return result;
}


/************************************************************************
 *  Method:
 *    IRMASite::DestroyChild
 */
STDMETHODIMP 
ExampleWindowlessSite::DestroyChild(IRMASite* /*IN*/ pChildSite)
{
    //fprintf(stdout, "ExampleWindowlessSite::DestroyChild()\n");

    /*
     * Verify that the site is actually a child site and find
     * its position in the list in the event that it is a child.
     */
    ListPosition prevPos;
    ExSiteInfo* pSiteInfo = NULL;
    MapSiteToSiteInfo(pChildSite, pSiteInfo, prevPos);
    if (!pSiteInfo) 
    {
	return PNR_UNEXPECTED;
    }

    /* 
     * Cleanup the list items for this child site.
     */
    if (!m_bInDestructor)
    {
        delete pSiteInfo;
	if (prevPos)
	{
	    m_Children.RemoveAfter(prevPos);
	}
	else
	{
	    m_Children.RemoveHead();
	}
    }

    return PNR_OK;
}

/************************************************************************
 *  Method:
 *    MapSiteToSiteInfo
 */
BOOL ExampleWindowlessSite::MapSiteToSiteInfo(IRMASite* pChildSite, ExSiteInfo*& pSiteInfo, ListPosition& prevPos)
{
    BOOL res = FALSE;

    // iterate child site list 
    pSiteInfo = NULL;
    ListPosition pos = m_Children.GetHeadPosition();
    prevPos = pos;
    while (pos)
    {
        pSiteInfo = (ExSiteInfo*) m_Children.GetAt(pos);
        if (pSiteInfo->m_pSite == pChildSite)
        {
            res = TRUE;

	    if (prevPos == m_Children.GetHeadPosition())
	    {
		prevPos = NULL;
	    }
		;
	    break;
        }
	
	prevPos = pos;
	pos = m_Children.GetNextPosition(pos);	
    }

    return res;
}

/************************************************************************
 *  Method:
 *    IRMASite::AttachWatcher
 */
STDMETHODIMP 
ExampleWindowlessSite::AttachWatcher(IRMASiteWatcher* /*IN*/ pWatcher)
{
    if (m_pWatcher) return PNR_UNEXPECTED;

    m_pWatcher = pWatcher;

    if (m_pWatcher)
    {
	m_pWatcher->AddRef();
	m_pWatcher->AttachSite(this);
    }

    return PNR_OK;
}

/************************************************************************
 *  Method:
 *    IRMASite::DetachWatcher
 */
STDMETHODIMP 
ExampleWindowlessSite::DetachWatcher()
{
    if (!m_pWatcher) return PNR_UNEXPECTED;

    m_pWatcher->DetachSite();
    PN_RELEASE(m_pWatcher);

    return PNR_OK;
}

/************************************************************************
 *  Method:
 *    IRMASite::SetSize
 */
STDMETHODIMP 
ExampleWindowlessSite::SetSize(PNxSize size)
{
    HRESULT hres = PNR_OK;

    /* before we do anything, we give the SiteWatcher a chance to 
     * influence this operation.
     */
    if (m_pWatcher)
    {
	hres = m_pWatcher->ChangingSize(m_size, size);
    }
    
    if (PNR_OK == hres && size.cx != 0 && size.cy != 0)
    {
	m_size = size;

	// iterate child site list 
	IRMAPassiveSiteWatcher* pWatcher = NULL;
	ListPosition pos = m_PassiveSiteWatchers.GetHeadPosition();
	while (pos)
	{
	    pWatcher = (IRMAPassiveSiteWatcher*) m_PassiveSiteWatchers.GetAt(pos);
	    pWatcher->SizeChanged(&m_size);

	    pos = m_PassiveSiteWatchers.GetNextPosition(pos);	
	}
    }

    return hres;
}

/************************************************************************
 *  Method:
 *    IRMASite::SetPosition
 */
STDMETHODIMP 
ExampleWindowlessSite::SetPosition(PNxPoint position)
{
    HRESULT hres = PNR_OK;

    /*
     * Before we do anything, we give the SiteWatcher a chance to 
     * influence this operation.
     */
    if (m_pWatcher)
    {
	hres = m_pWatcher->ChangingPosition(m_position, position);
    }
    
    if (PNR_OK == hres)
    {
	/* Record the position of posterity sake */
	m_position = position;

	// iterate child site list 
	IRMAPassiveSiteWatcher* pWatcher = NULL;
	ListPosition pos = m_PassiveSiteWatchers.GetHeadPosition();
	while (pos)
	{
	    pWatcher = (IRMAPassiveSiteWatcher*) m_PassiveSiteWatchers.GetAt(pos);
	    pWatcher->PositionChanged(&m_position);

	    pos = m_PassiveSiteWatchers.GetNextPosition(pos);	
	}
    }

    return hres;
}


/************************************************************************
 *  Method:
 *    IRMASite::GetSize
 */
STDMETHODIMP 
ExampleWindowlessSite::GetSize(REF(PNxSize) size)
{
    size = m_size;
    return PNR_OK;
}


/************************************************************************
 *  Method:
 *    IRMASite::GetPosition
 */
STDMETHODIMP 
ExampleWindowlessSite::GetPosition(REF(PNxPoint) position)
{
    position = m_position;
    return PNR_OK;
}


/************************************************************************
 *  Method:
 *    IRMASite::DamageRect
 */
STDMETHODIMP 
ExampleWindowlessSite::DamageRect(PNxRect rect)
{
    m_bDamaged = TRUE;
    return PNR_OK;
}


/************************************************************************
 *  Method:
 *    IRMASite::DamageRegion
 */
STDMETHODIMP 
ExampleWindowlessSite::DamageRegion(PNxRegion region)
{
    m_bDamaged = TRUE;
    return PNR_OK;
}


/************************************************************************
 *  Method:
 *    IRMASite::ForceRedraw
 */
STDMETHODIMP 
ExampleWindowlessSite::ForceRedraw()
{
    // make sure we have a visible window and are not re-enterering and we have damage
    if (!m_bInRedraw && m_bDamaged && m_bIsVisible)
    {
	AddRef();

	m_bInRedraw = TRUE;

	/*
	 * set up the event structure to simulate an X "Expose" event
	 */
	PNxEvent event;
	memset(&event,0,sizeof(event));

#if defined(_UNIX)
	event.event = Expose;
#elif defined(_WINDOWS)
	event.event = WM_PAINT;
#elif defined(_MACINTOSH)
	event.event = updateEvt;
#endif

	/*
	 * call our handy helper routine that takes care of everything
	 * else for us.
	 */
	ForwardUpdateEvent(&event);

	m_bInRedraw = FALSE;
	m_bDamaged = FALSE;

	Release();
    }

    return PNR_OK;
}


/************************************************************************
 *  Method:
 *	IRMASite::ForwardUpdateEvent
 *  Notes:
 *	This method is the main helpr function for handling update 
 *	events. It handles several things including setting the origin
 *	and the clipping region.
 */
void
ExampleWindowlessSite::ForwardUpdateEvent(PNxEvent* pEvent)
{
    BOOL bHandled = FALSE;

    AddRef();

    /* 
     * send the basic updateEvt event to the user
     */
    m_pUser->HandleEvent(pEvent);

    /*
     * If the user doesn't handle the standard update event then
     * send them the cross platform RMA_SURFACE_UPDATE event don't
     * damage the original event structure
     */
    if (!pEvent->handled && m_pUser)
    {
    	PNxEvent event;
	memset(&event, 0, sizeof(PNxEvent));
	event.event = RMA_SURFACE_UPDATE;
	event.param1 = m_pVideoSurface;
	event.result = 0;
	event.handled = FALSE;

	m_pUser->HandleEvent(&event);

	bHandled = event.handled;
    }
    else
    {
    	bHandled = TRUE;
    }

    Release();
}

/************************************************************************
 *  Method:
 *    IRMAValues::SetPropertyULONG32
 */
STDMETHODIMP 
ExampleWindowlessSite::SetPropertyULONG32
(
    const char*      pPropertyName,
    ULONG32          uPropertyValue
)
{
    if (!m_pValues) return PNR_UNEXPECTED;
    return m_pValues->SetPropertyULONG32
		    (
			pPropertyName,
			uPropertyValue
		    );
}


/************************************************************************
 *  Method:
 *    IRMAValues::SetPropertyULONG32
 */
STDMETHODIMP 
ExampleWindowlessSite::GetPropertyULONG32
(
    const char*      pPropertyName,
    REF(ULONG32)     uPropertyValue
)
{
    if (!m_pValues) return PNR_UNEXPECTED;
    return m_pValues->GetPropertyULONG32
		    (
			pPropertyName,
			uPropertyValue
		    );
}


/************************************************************************
 *  Method:
 *    IRMAValues::SetPropertyULONG32
 */
STDMETHODIMP 
ExampleWindowlessSite::GetFirstPropertyULONG32
(
				    REF(const char*) pPropertyName,
				    REF(ULONG32)     uPropertyValue
)
{
    if (!m_pValues) return PNR_UNEXPECTED;
    return m_pValues->GetPropertyULONG32
		    (
			pPropertyName,
			uPropertyValue
		    );
}


/************************************************************************
 *  Method:
 *    IRMAValues::SetPropertyULONG32
 */
STDMETHODIMP 
ExampleWindowlessSite::GetNextPropertyULONG32
(
				    REF(const char*) pPropertyName,
				    REF(ULONG32)     uPropertyValue
)
{
    if (!m_pValues) return PNR_UNEXPECTED;
    return m_pValues->GetNextPropertyULONG32
		    (
			pPropertyName,
			uPropertyValue
		    );
}


/************************************************************************
 *  Method:
 *    IRMAValues::SetPropertyULONG32
 */
STDMETHODIMP 
ExampleWindowlessSite::SetPropertyBuffer
(
    const char*      pPropertyName,
    IRMABuffer*      pPropertyValue
)
{
    if (!m_pValues) return PNR_UNEXPECTED;
    return m_pValues->SetPropertyBuffer
		    (
			pPropertyName,
			pPropertyValue
		    );
}


/************************************************************************
 *  Method:
 *    IRMAValues::SetPropertyULONG32
 */
STDMETHODIMP 
ExampleWindowlessSite::GetPropertyBuffer
(
    const char*      pPropertyName,
    REF(IRMABuffer*) pPropertyValue
)
{
    if (!m_pValues) return PNR_UNEXPECTED;
    return m_pValues->GetPropertyBuffer
		    (
			pPropertyName,
			pPropertyValue
		    );
}


/************************************************************************
 *  Method:
 *    IRMAValues::SetPropertyULONG32
 */
STDMETHODIMP 
ExampleWindowlessSite::GetFirstPropertyBuffer
(
    REF(const char*) pPropertyName,
    REF(IRMABuffer*) pPropertyValue
)
{
    if (!m_pValues) return PNR_UNEXPECTED;
    return m_pValues->GetFirstPropertyBuffer
		    (
			pPropertyName,
			pPropertyValue
		    );
}


/************************************************************************
 *  Method:
 *    IRMAValues::SetPropertyULONG32
 */
STDMETHODIMP 
ExampleWindowlessSite::GetNextPropertyBuffer
(
    REF(const char*) pPropertyName,
    REF(IRMABuffer*) pPropertyValue
)
{
    if (!m_pValues) return PNR_UNEXPECTED;
    return m_pValues->GetNextPropertyBuffer
		    (
			pPropertyName,
			pPropertyValue
		    );
}


/************************************************************************
 *  Method:
 *    IRMAValues::SetPropertyULONG32
 */
STDMETHODIMP 
ExampleWindowlessSite::SetPropertyCString
(
    const char*      pPropertyName,
    IRMABuffer*      pPropertyValue
)
{
    if (!m_pValues) return PNR_UNEXPECTED;
    return m_pValues->SetPropertyCString
		    (
			pPropertyName,
			pPropertyValue
		    );
}

/************************************************************************
 *  Method:
 *    IRMAValues::SetPropertyULONG32
 */
STDMETHODIMP 
ExampleWindowlessSite::GetPropertyCString
(
    const char*      pPropertyName,
    REF(IRMABuffer*) pPropertyValue
)
{
    if (!m_pValues) return PNR_UNEXPECTED;
    return m_pValues->GetPropertyCString
		    (
			pPropertyName,
			pPropertyValue
		    );
}

/************************************************************************
 *  Method:
 *    IRMAValues::SetPropertyULONG32
 */
STDMETHODIMP 
ExampleWindowlessSite::GetFirstPropertyCString
(
    REF(const char*) pPropertyName,
    REF(IRMABuffer*) pPropertyValue
)
{
    if (!m_pValues) return PNR_UNEXPECTED;
    return m_pValues->GetFirstPropertyCString
		    (
			pPropertyName,
			pPropertyValue
		    );
}

/************************************************************************
 *  Method:
 *    IRMAValues::SetPropertyULONG32
 */
STDMETHODIMP 
ExampleWindowlessSite::GetNextPropertyCString
(
    REF(const char*) pPropertyName,
    REF(IRMABuffer*) pPropertyValue
)
{
    if (!m_pValues) return PNR_UNEXPECTED;
    return m_pValues->GetNextPropertyCString
		    (
			pPropertyName,
			pPropertyValue
		    );
}


/************************************************************************
 *  Method:
 *    IRMASite2::UpdateSiteWindow
 *    	
 *	Not used on Windows platform
 */
STDMETHODIMP 
ExampleWindowlessSite::UpdateSiteWindow
(
    PNxWindow* /*IN*/ pWindow
)
{
    return PNR_OK;
}


/************************************************************************
 *  Method:
 *    IRMASite2::ShowSite
 */
STDMETHODIMP 
ExampleWindowlessSite::ShowSite
(
    BOOL    bShow
)
{
    m_bIsVisible = bShow;
    return PNR_OK;
}

/************************************************************************
 *  Method:
 *    IRMASite2::IsSiteVisible
 */
STDMETHODIMP_(BOOL) 
ExampleWindowlessSite::IsSiteVisible()
{
    BOOL bIsVisible = m_bIsVisible;
    if (m_pParentSite)
    {
        bIsVisible &= m_pParentSite->IsSiteVisible();
    }
    
    return bIsVisible;
}

/************************************************************************
 *  Method:
 *    IRMASite2::SetZOrder
 */
STDMETHODIMP
ExampleWindowlessSite::SetZOrder(INT32 lZOrder)
{
    if(!m_pParentSite) return PNR_UNEXPECTED;
    m_lZOrder = lZOrder;
    return PNR_OK;
}

/************************************************************************
 *  Method:
 *    IRMASite2::GetZOrder
 */
STDMETHODIMP
ExampleWindowlessSite::GetZOrder(REF(INT32) lZOrder)
{
    if(!m_pParentSite) return PNR_UNEXPECTED;
    lZOrder = m_lZOrder;
    return PNR_OK;
}

/************************************************************************
 *  Method:
 *    IRMASite2::MoveSiteToTop
 */
STDMETHODIMP
ExampleWindowlessSite::MoveSiteToTop()
{
    if(!m_pParentSite) return PNR_UNEXPECTED;
    return PNR_NOTIMPL;
}

/************************************************************************
 *  Method:
 *    IRMASite2::GetVideoSurface
 */
STDMETHODIMP
ExampleWindowlessSite::GetVideoSurface(REF(IRMAVideoSurface*) pSurface)
{
    PN_RESULT res = PNR_FAIL;

    if (m_pVideoSurface)
    {
	res = m_pVideoSurface->QueryInterface(IID_IRMAVideoSurface, 
					   (void**)&pSurface);
    }

    return res;
}

/************************************************************************
 *  Method:
 *    IRMASite2::GetNumberOfChildSites
 */
STDMETHODIMP_(UINT32)
ExampleWindowlessSite::GetNumberOfChildSites()
{
    return (UINT32)m_Children.Count();
}

/************************************************************************
 *  Method:
 *    IRMASite2::AddPassiveSiteWatcher
 */
STDMETHODIMP
ExampleWindowlessSite::AddPassiveSiteWatcher(IRMAPassiveSiteWatcher* pWatcher)
{
    pWatcher->AddRef();
    m_PassiveSiteWatchers.Add(pWatcher);
    return PNR_OK;
}

/************************************************************************
 *  Method:
 *    IRMASite2::RemovePassiveSiteWatcher
 */
STDMETHODIMP
ExampleWindowlessSite::RemovePassiveSiteWatcher(IRMAPassiveSiteWatcher* pWatcher)
{
    // iterate child site list 
    IRMAPassiveSiteWatcher* pThisWatcher = NULL;
    ListPosition pos = m_PassiveSiteWatchers.GetHeadPosition();
    ListPosition prevPos = pos;
    while (pos)
    {
	pThisWatcher = (IRMAPassiveSiteWatcher*) m_PassiveSiteWatchers.GetAt(pos);
	if(pWatcher == pThisWatcher)
	{
	    PN_RELEASE(pWatcher);

	    if (prevPos == m_PassiveSiteWatchers.GetHeadPosition())
	    {
		m_PassiveSiteWatchers.RemoveHead();
	    }
	    else
	    {
		m_PassiveSiteWatchers.RemoveAfter(prevPos);
	    }

	    break;
	}

	prevPos = pos;
	pos = m_PassiveSiteWatchers.GetNextPosition(pos);	
    }

    return PNR_OK;
}

/*
 * IRMASiteWindowless methods called by owners of the site.
 */

STDMETHODIMP
ExampleWindowlessSite::EventOccurred(PNxEvent* /*IN*/ pEvent)
{
    return PNR_OK;
}

/*
 * IRMASiteWindowless method. Returns some parent window that
 * owns the windowless site. Useful for right-click menus and
 * dialog box calls.
 */

PNxWindow*
ExampleWindowlessSite::GetParentWindow()
{
    return NULL;
}



/************************************************************************
 *  Method:
 *    IRMASite2::SetCursor
 */
STDMETHODIMP
ExampleWindowlessSite::SetCursor(PNxCursor cursor, REF(PNxCursor) oldCursor)
{
    return PNR_NOTIMPL;
}

/************************************************************************
 *  Method:
 *    ExSiteInfo - implementation
 *	
 */

ExSiteInfo::ExSiteInfo(IRMASite* pSite, void* pThisPointer)
{
    m_pSite = pSite;
    m_pSite->AddRef();

    pSite->QueryInterface(IID_IRMASiteWindowless, (void**) &m_pSiteWindowless);
    pSite->QueryInterface(IID_IRMASite2, (void**) &m_pSite2);
};

ExSiteInfo::~ExSiteInfo() 
{
    PN_RELEASE(m_pSite);
    PN_RELEASE(m_pSiteWindowless);
    PN_RELEASE(m_pSite2);
}

