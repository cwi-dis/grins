/****************************************************************************
 * 
 *  $Id$
 *  
 *  Copyright (C) 1995,1996,1997 Progressive Networks.
 *  All rights reserved.
 *
 *  This program contains proprietary 
 *  information of Progressive Networks, Inc, and is licensed
 *  subject to restrictions on use and distribution.
 *
 */

#ifndef _EXNWSITE_H_
#define _EXNWSITE_H_

class	ExampleVideoSurface;

/****************************************************************************
 * 
 *  Class:
 *
 *	NonDelegatingUnknown
 *
 *  Purpose:
 *
 *	Same signature as IUnknown, allows an object to implement 
 *	aggregation.
 *
 */
class NonDelegatingUnknown
{
public:
    /*
     * DelegatingUnknown methods
     */
    STDMETHOD(NonDelegatingQueryInterface)	(THIS_
						REFIID riid,
						void** ppvObj) PURE;

    STDMETHOD_(ULONG32,NonDelegatingAddRef)	(THIS) PURE;

    STDMETHOD_(ULONG32,NonDelegatingRelease)	(THIS) PURE;
};

/****************************************************************************
 * 
 *  Class:
 *
 *	ExSiteInfo
 *
 *  Purpose:
 *
 *	helper class used to keep track of interface ptrs
 *
 */

class ExSiteInfo
{
public:
    ExSiteInfo(IRMASite* pSite, void* pThisPointer);
    ~ExSiteInfo();

    IRMASite*		m_pSite;
    IRMASiteWindowless*	m_pSiteWindowless;
    IRMASite2*		m_pSite2;
};


/****************************************************************************
 * 
 *  Class:
 *
 *	ExampleWindowlessSite
 *
 *  Purpose:
 *
 *	Implementation for IRMASite objects which are associated with
 *	platform specific window objects on Microsoft Windows and X-Windows.
 *
 */
class ExampleWindowlessSite : 
	public NonDelegatingUnknown,
	public IRMASite,
	public IRMASite2,
	public IRMASiteWindowless, 
	public IRMAValues
{
public:
    ExampleVideoSurface*	m_pVideoSurface;
private:
    LONG32			m_lRefCount;
    IRMASiteUser*		m_pUser;

    FiveMinuteList		m_Children;

    BOOL 			m_bDamaged;

    ExampleWindowlessSite*	m_pParentSite;
    IRMAValues*			m_pValues;    

    IRMACommonClassFactory*	m_pCCF;

    IUnknown*			m_pUnkOuter;
    IRMASiteWatcher*		m_pWatcher;
    IUnknown*			m_pContext;

    PNxSize			m_size;
    PNxPoint			m_position;
    INT32			m_lZOrder;
    FiveMinuteList		m_PassiveSiteWatchers;
    BOOL			m_bIsVisible;

    BOOL			m_bInDestructor;
    BOOL			m_bIsChildWindow;
    BOOL 			m_bInRedraw;


    ~ExampleWindowlessSite();
    PRIVATE_DESTRUCTORS_ARE_NOT_A_CRIME



    /* This private methods are used when CPNSiteWindowed are used
     * as child/parent site combinations.
     */
    void		SetParentSite(ExampleWindowlessSite* pParentSite);

    // private methods 
    void		ForwardUpdateEvent(PNxEvent* pEvent);

    BOOL MapSiteToSiteInfo(IRMASite* pChildSite, ExSiteInfo*& pSiteInfo, ListPosition& prevPos);



public:
    ExampleWindowlessSite*       GetParentSite()    {return m_pParentSite;}
    
    
public:
    ExampleWindowlessSite(IUnknown* pContext,
			 IUnknown* pUnkOuter = NULL);


    /* NonDelegatingUnknown methods */
    STDMETHOD(NonDelegatingQueryInterface)	(THIS_
						REFIID riid,
						void** ppvObj);

    STDMETHOD_(ULONG32,NonDelegatingAddRef)	(THIS);

    STDMETHOD_(ULONG32,NonDelegatingRelease)	(THIS);
    

    /* IUnknown methods */
    STDMETHOD(QueryInterface)	(THIS_
				REFIID riid,
				void** ppvObj);

    STDMETHOD_(ULONG32,AddRef)	(THIS);

    STDMETHOD_(ULONG32,Release)	(THIS);



    /*
     * IRMASiteWindowless methods called by owners of the site.
     */
    STDMETHOD(EventOccurred)	(THIS_
				PNxEvent* /*IN*/ pEvent);

    /*
     * IRMASiteWindowless method. Returns some parent window that
     * owns the windowless site. Useful for right-click menus and
     * dialog box calls.
     */
    STDMETHOD_(PNxWindow*,GetParentWindow)(THIS);


    /* IRMASite methods usually called by the "context" to 
     * associate users with the site, and to create child sites
     * as appropriate.
     */
    STDMETHOD(AttachUser)	(THIS_
				IRMASiteUser*	/*IN*/	pUser);

    STDMETHOD(DetachUser)	(THIS);

    STDMETHOD(GetUser)		(THIS_
				REF(IRMASiteUser*) /*OUT*/ pUser);

    STDMETHOD(CreateChild)	(THIS_
				REF(IRMASite*)	/*OUT*/ pChildSite);

    STDMETHOD(DestroyChild)	(THIS_
				IRMASite*	/*IN*/	pChildSite);



    /* IRMASite methods called by the the "context" in which the site
     * is displayed in order to manage its position. Site users should
     * not generally call these methods.
     */
    STDMETHOD(AttachWatcher)	(THIS_
				IRMASiteWatcher* /*IN*/	pWatcher);

    STDMETHOD(DetachWatcher)	(THIS);

    STDMETHOD(SetPosition)	(THIS_
				PNxPoint		position);

    STDMETHOD(GetPosition)	(THIS_
				REF(PNxPoint)		position);



    /* IRMASite methods called by the user of the site to get
     * information about the site, and to manipulate the site.
     */
    STDMETHOD(SetSize)		(THIS_
				PNxSize			size);

    STDMETHOD(GetSize)		(THIS_
				REF(PNxSize)		size);

    STDMETHOD(DamageRect)	(THIS_
				PNxRect			rect);

    STDMETHOD(DamageRegion)	(THIS_
				PNxRegion		region);

    STDMETHOD(ForceRedraw)	(THIS);


    /* IRMAValues methods */
    STDMETHOD(SetPropertyULONG32)	(THIS_
					const char*      pPropertyName,
					ULONG32          uPropertyValue);

    STDMETHOD(GetPropertyULONG32)	(THIS_
					const char*      pPropertyName,
					REF(ULONG32)     uPropertyName);

    STDMETHOD(GetFirstPropertyULONG32)	(THIS_
					REF(const char*) pPropertyName,
					REF(ULONG32)     uPropertyValue);

    STDMETHOD(GetNextPropertyULONG32)	(THIS_
					REF(const char*) pPropertyName,
					REF(ULONG32)     uPropertyValue);

    STDMETHOD(SetPropertyBuffer)	(THIS_
					const char*      pPropertyName,
					IRMABuffer*      pPropertyValue);

    STDMETHOD(GetPropertyBuffer)	(THIS_
					const char*      pPropertyName,
					REF(IRMABuffer*) pPropertyValue);
    
    STDMETHOD(GetFirstPropertyBuffer)	(THIS_
					REF(const char*) pPropertyName,
					REF(IRMABuffer*) pPropertyValue);

    STDMETHOD(GetNextPropertyBuffer)	(THIS_
					REF(const char*) pPropertyName,
					REF(IRMABuffer*) pPropertyValue);


    STDMETHOD(SetPropertyCString)	(THIS_
					const char*      pPropertyName,
					IRMABuffer*      pPropertyValue);

    STDMETHOD(GetPropertyCString)	(THIS_
					const char*      pPropertyName,
					REF(IRMABuffer*) pPropertyValue);

    STDMETHOD(GetFirstPropertyCString)	(THIS_
					REF(const char*) pPropertyName,
					REF(IRMABuffer*) pPropertyValue);

    STDMETHOD(GetNextPropertyCString)	(THIS_
					REF(const char*) pPropertyName,
					REF(IRMABuffer*) pPropertyValue);

    /*
     * IRMASite2 methods
     */

    /*
     * IRMASite2 method usually called by the "context" 
     * when window attributes (like the window handle) have changed.
     */
    STDMETHOD(UpdateSiteWindow)    	(THIS_
					PNxWindow* /*IN*/ pWindow);

    /*
     * IRMASite2 method usually called by the "context" to
     * to hide/show a site. This method will hide/show all
     * the site's children as well.
     */
    STDMETHOD(ShowSite)         	(THIS_
                                 	BOOL    bShow);
                                 
    STDMETHOD_(BOOL, IsSiteVisible)   	(THIS);

    /*
     * IRMASite2 method usually called by the "context" to
     * to set the site's Z order.
     */
    STDMETHOD(SetZOrder)         	(THIS_
					INT32 lZOrder);

    STDMETHOD(GetZOrder)		(THIS_
					REF(INT32) lZOrder);

    STDMETHOD(MoveSiteToTop)		(THIS);
                                 	
    STDMETHOD(GetVideoSurface)		(THIS_ 
					REF(IRMAVideoSurface*) pSurface);
    STDMETHOD_(UINT32,GetNumberOfChildSites) (THIS);

    /*
     * IRMASite2 methods to add/remove passive site watchers
     */
    STDMETHOD(AddPassiveSiteWatcher)	(THIS_
				        IRMAPassiveSiteWatcher* pWatcher);

    STDMETHOD(RemovePassiveSiteWatcher)	(THIS_
				        IRMAPassiveSiteWatcher* pWatcher);
    /*
     * IRMASite2 methods to change the cursor
     */
    STDMETHOD(SetCursor)		(THIS_
					PNxCursor cursor,
					REF(PNxCursor) oldCursor);
};

#endif // _EXNWSITE_H_








