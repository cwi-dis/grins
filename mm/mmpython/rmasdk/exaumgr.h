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
 *  exaumgr.h
 *
 */
#ifndef _EXAUMGR_H_
#define _EXAUMGR_H_


/****************************************************************************
 * Includes
 */
#include "rmaauth.h"


/****************************************************************************
 *
 *  ExampleAuthenticationManager Class
 *
 */
class ExampleAuthenticationManager : public IRMAAuthenticationManager
{
    public:
    /****** Public Class Methods ******************************************/
    ExampleAuthenticationManager();


   /************************************************************************
    *  IRMAAuthenticationManager Interface Methods           ref:  rmaauth.h
    */
    STDMETHOD(HandleAuthenticationRequest) (IRMAAuthenticationManagerResponse* pResponse);

    
   /************************************************************************
    *  IUnknown COM Interface Methods                          ref:  pncom.h
    */
    STDMETHOD (QueryInterface ) (THIS_ REFIID ID, void** ppInterfaceObj);
    STDMETHOD_(UINT32, AddRef ) (THIS);
    STDMETHOD_(UINT32, Release) (THIS);


    private:
    /****** Private Class Variables ****************************************/
    INT32 m_lRefCount;

    /****** Private Class Methods ******************************************/
    ~ExampleAuthenticationManager();
    PRIVATE_DESTRUCTORS_ARE_NOT_A_CRIME      // Avoids GCC compiler warning
};


#endif /* _EXAUMGR_H_ */
