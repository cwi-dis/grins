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
 *  exaukmgr.cpp
 *
 */

/****************************************************************************
 * Includes
 */
#include <ctype.h>

#include "pntypes.h"
#include "pncom.h"
#include "rmaauth.h"
#include "os.h"
#include "exaumgr.h"


/****************************************************************************
 *  ExampleAuthenticationManager::ExampleAuthenticationManager  ref:exaumgr.h
 *
 *  Constructor
 */
ExampleAuthenticationManager::ExampleAuthenticationManager() :
    m_lRefCount(0)
{
}


/****************************************************************************
 *  ExampleAuthenticationManager::~ExampleAuthenticationManager ref:exaumgr.h
 *
 *  Destructor
 */
ExampleAuthenticationManager::~ExampleAuthenticationManager()
{
}


// IRMAAuthenticationManager Interface Methods

/****************************************************************************
 *  IRMAAuthenticationManager::HandleAuthenticationRequest    ref:  rmaauth.h
 *
 */
STDMETHODIMP
ExampleAuthenticationManager::HandleAuthenticationRequest(IRMAAuthenticationManagerResponse* pResponse)
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
		c--)
		;
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
ExampleAuthenticationManager::AddRef()
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
ExampleAuthenticationManager::Release()
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
ExampleAuthenticationManager::QueryInterface(REFIID riid, void**ppvObj)
{
    if(IsEqualIID(riid, IID_IUnknown))
    {
        AddRef();
        *ppvObj = (IUnknown*)(IRMAAuthenticationManager*)this;
        return PNR_OK;
    }
    else if(IsEqualIID(riid, IID_IRMAAuthenticationManager))
    {
        AddRef();
        *ppvObj = (IRMAAuthenticationManager*)this;
        return PNR_OK;
    }
    *ppvObj = NULL;
    return PNR_NOINTERFACE;
}
