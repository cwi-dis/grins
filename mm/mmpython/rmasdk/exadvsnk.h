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
 *  exadvsnk.h
 *
 *  Client Advise Sink Interfaces
 *
 */
#ifndef _EXAMPLECLSNK_
#define _EXAMPLECLSNK_


/****************************************************************************
 * Forward declarations
 */
struct IRMAClientAdviseSink;
struct IUnknown;
struct IRMAPNRegistry;


/****************************************************************************
 *
 *  ExampleClientAdviceSink Class
 *
 */
class ExampleClientAdviceSink : public IRMAClientAdviseSink
{
    public:
    /****** Public Class Methods ******************************************/
    ExampleClientAdviceSink(IUnknown* /*IN*/ pUnknown);


   /************************************************************************
    *  IRMAClientAdviseSink Interface Methods               ref:  rmaclsnk.h
    */
    STDMETHOD (OnPosLength)  (THIS_ UINT32 ulPosition, UINT32 ulLength);
    STDMETHOD (OnPresentationOpened) (THIS);
    STDMETHOD (OnPresentationClosed) (THIS);
    STDMETHOD (OnStatisticsChanged)  (THIS);
    STDMETHOD (OnPreSeek)    (THIS_ UINT32 ulOldTime, UINT32 ulNewTime);
    STDMETHOD (OnPostSeek)   (THIS_ UINT32 ulOldTime, UINT32 ulNewTime);
    STDMETHOD (OnStop)       (THIS);
    STDMETHOD (OnPause)      (THIS_ UINT32 ulTime);
    STDMETHOD (OnBegin)	     (THIS_ UINT32 ulTime);
    STDMETHOD (OnBuffering)  (THIS_ UINT32 ulFlags, UINT16 unPercentComplete);
    STDMETHOD (OnContacting) (THIS_ const char* pHostName);


   /************************************************************************
    *  IUnknown COM Interface Methods                          ref:  pncom.h
    */
    STDMETHOD (QueryInterface ) (THIS_ REFIID ID, void** ppInterfaceObj);
    STDMETHOD_(UINT32, AddRef ) (THIS);
    STDMETHOD_(UINT32, Release) (THIS);


private:
    /****** Private Class Variables ****************************************/
    INT32			m_lRefCount;
    IUnknown*			m_pUnknown;
    IRMAPNRegistry*		m_pRegistry;

    /****** Private Class Methods ******************************************/
    ~ExampleClientAdviceSink();
    void ShowMeTheStatistics (char* /*IN*/ pszRegistryKey);
    
    PRIVATE_DESTRUCTORS_ARE_NOT_A_CRIME      // Avoids GCC compiler warning
};


#endif /* _EXAMPLECLSNK_ */
