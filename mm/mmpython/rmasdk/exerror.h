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
 *  exerror.h
 *
 *  Implementation of IRMAErrorMessages
 *
 */
#ifndef _EXAMPLEERRORMESSAGES_
#define _EXAMPLEERRORMESSAGES_


/****************************************************************************
 * Forward declarations
 */
struct IUnknown;
struct IRMAErrorMessages;


/****************************************************************************
 *
 *  ExampleErrorSink Class
 *
 */
class ExampleErrorSink : public IRMAErrorSink
{
    public:
    /****** Public Class Methods ******************************************/
     ExampleErrorSink();
    ~ExampleErrorSink();


   /************************************************************************
    *  IRMAErrorSink Interface Methods                      ref:  rmaerror.h
    */
    STDMETHOD(ErrorOccurred)
	(THIS_
	 const UINT8	unSeverity,  
	 const UINT32	ulRMACode,
	 const UINT32	ulUserCode,
	 const char*	pUserString,
	 const char*	pMoreInfoURL
	);


   /************************************************************************
    *  IUnknown COM Interface Methods                          ref:  pncom.h
    */
    STDMETHOD (QueryInterface ) (THIS_ REFIID ID, void** ppInterfaceObj);
    STDMETHOD_(UINT32, AddRef ) (THIS);
    STDMETHOD_(UINT32, Release) (THIS);


    protected:
    void   ConvertErrorToString (const ULONG32 ulRMACode, char* pszBuffer);

    /****** Protected Class Variables *************************************/
    INT32			m_lRefCount;
};


#endif /*_EXAMPLEERRORMESSAGES_*/
