/****************************************************************************
 * 
 *  $Id$
 *  
 *  Copyright (C) 1995,1996,1997 RealNetworks.
 *  All rights reserved.
 *
 *  This program contains proprietary information of RealNetworks, Inc.,
 *  and is licensed subject to restrictions on use and distribution.
 *
 */
#ifndef _EXSITSUP_H_
#define _EXSITSUP_H_


// forward declares
class ExampleWindowlessSite;


/****************************************************************************
 *
 *  ExampleSiteSupplier Class
 *
 *  Implementation for ragui's IRMASiteSupplier.
 */
class ExampleSiteSupplier :  public IRMASiteSupplier
{
    public:
    /****** Public Class Methods ******************************************/
    ExampleSiteSupplier(IUnknown* pUnkPlayer);
    

    /************************************************************************
     *  IRMASiteSupplier Interface Methods                     ref:  rmawin.h
     */
    STDMETHOD(SitesNeeded) (THIS_ UINT32 uRequestID, IRMAValues* pSiteProps);
    STDMETHOD(SitesNotNeeded) (THIS_ UINT32 uRequestID);
    STDMETHOD(BeginChangeLayout) (THIS);
    STDMETHOD(DoneChangeLayout) (THIS);


    /************************************************************************
     *  IUnknown COM Interface Methods                          ref:  pncom.h
     */
    STDMETHOD (QueryInterface ) (THIS_ REFIID ID, void** ppInterfaceObj);
    STDMETHOD_(UINT32, AddRef ) (THIS);
    STDMETHOD_(UINT32, Release) (THIS);


    private:
    /****** Private Class Variables ****************************************/
    INT32		    m_lRefCount;
    IRMASiteManager*	    m_pSiteManager;
    IRMACommonClassFactory* m_pCCF;
    IUnknown*		    m_pUnkPlayer;
    FiveMinuteMap	    m_CreatedSites;

    // our windowless site
    ExampleWindowlessSite*  m_pWindowlessSite;

    /****** Private Class Methods ******************************************/
    ~ExampleSiteSupplier();
    
    PRIVATE_DESTRUCTORS_ARE_NOT_A_CRIME       // Avoids GCC compiler warning
};


#endif /* _EXSITSUP_H_ */

