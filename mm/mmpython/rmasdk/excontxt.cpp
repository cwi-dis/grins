/****************************************************************************
 * 
 *  $Id$
 *
 *  Copyright (C) 1995,1996,1997 RealNetworks, Inc.
 *  All rights reserved.
 *
 *  http://www.real.com/devzone
 *
 *  This program contains proprietary information of RealNetworks, Inc.,
 *  and is licensed subject to restrictions on use and distribution.
 * 
 *  excontxt.cpp
 *
 *  Sample Implementation of Client Context
 *
 */


/****************************************************************************
 * Includes
 */
#include "pntypes.h"
#include "pnwintyp.h"
#include "pncom.h"
#include "rmacomm.h"
#include "rmawin.h"
#include "rmaclsnk.h"
#include "rmaerror.h"

#include "os.h"
#include "fivemmap.h"
#include "exadvsnk.h"
#include "exerror.h"
#include "exsitsup.h"
#include "exaumgr.h"
#include "excontxt.h"


/****************************************************************************
 *  ExampleClientContext::ExampleClientContext               ref:  excontxt.h
 *
 *  Constructor
 */
ExampleClientContext::ExampleClientContext()
    : m_lRefCount(0)
    , m_pClientSink(NULL)
    , m_pErrorSink(NULL)
    , m_pAuthMgr(NULL)
    , m_pSiteSupplier(NULL)
{
}


/****************************************************************************
 *  ExampleClientContext::~ExampleClientContext              ref:  excontxt.h
 *
 *  Destructor
 */
ExampleClientContext::~ExampleClientContext()
{
    Close();
};


/****************************************************************************
 *  ExampleClientContext::Init                               ref:  excontxt.h
 *
 */
void ExampleClientContext::Init(IUnknown* /*IN*/ pUnknown)
{
    m_pErrorSink	= new ExampleErrorSink();
    m_pClientSink	= new ExampleClientAdviceSink(pUnknown);
    m_pAuthMgr          = new ExampleAuthenticationManager();
    m_pSiteSupplier	= new ExampleSiteSupplier(pUnknown);

    if (m_pClientSink)
    {
	m_pClientSink->AddRef();
    }
    
    if (m_pErrorSink)
    {
	m_pErrorSink->AddRef();
    }

    if(m_pAuthMgr)
    {
	m_pAuthMgr->AddRef();
    }

    if(m_pSiteSupplier)
    {
	m_pSiteSupplier->AddRef();
    }
}


/****************************************************************************
 *  ExampleClientContext::Close                              ref:  excontxt.h
 *
 */
void ExampleClientContext::Close()
{
    PN_RELEASE(m_pClientSink);
    PN_RELEASE(m_pErrorSink);
    PN_RELEASE(m_pAuthMgr);
    PN_RELEASE(m_pSiteSupplier);
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
STDMETHODIMP_(UINT32)
ExampleClientContext::AddRef()
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
STDMETHODIMP_(UINT32)
ExampleClientContext::Release()
{
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
ExampleClientContext::QueryInterface(REFIID riid, void** ppvObj)
{
    if (IsEqualIID(riid, IID_IUnknown))
    {
	AddRef();
	*ppvObj = this;
	return PNR_OK;
    }
    else if (m_pClientSink && 
	     m_pClientSink->QueryInterface(riid, ppvObj) == PNR_OK)
    {
	return PNR_OK;
    }
    else if (m_pErrorSink && 
	     m_pErrorSink->QueryInterface(riid, ppvObj) == PNR_OK)
    {
	return PNR_OK;
    }
    else if(m_pAuthMgr &&
	    m_pAuthMgr->QueryInterface(riid, ppvObj) == PNR_OK)
    {
	return PNR_OK;
    }
    else if(m_pSiteSupplier &&
	    m_pSiteSupplier->QueryInterface(riid, ppvObj) == PNR_OK)
    {
	return PNR_OK;
    }
    *ppvObj = NULL;
    return PNR_NOINTERFACE;
}
