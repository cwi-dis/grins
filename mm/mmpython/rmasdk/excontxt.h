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
 *  excontxt.h
 *
 *  Example Client Context, Interfaces
 *
 */


/****************************************************************************
 * Forward declarations
 */
struct IUnknown;
class  ExampleClientAdviceSink;
class  ExampleErrorMessages;
class  ExampleAuthenticationManager;


/****************************************************************************
 *
 *  ExampleClientContext Class
 *
 */
class ExampleClientContext : public IUnknown
{
    public:
    /****** Public Class Methods ******************************************/
     ExampleClientContext();
    ~ExampleClientContext();
    void Init(IUnknown* /*IN*/ pUnknown);
    void Close();


   /************************************************************************
    *  IUnknown COM Interface Methods                          ref:  pncom.h
    */
    STDMETHOD (QueryInterface ) (THIS_ REFIID ID, void** ppInterfaceObj);
    STDMETHOD_(UINT32, AddRef ) (THIS);
    STDMETHOD_(UINT32, Release) (THIS);


    //private:
    /****** Private Class Variables ****************************************/
    INT32			    m_lRefCount;
    ExampleClientAdviceSink*	    m_pClientSink;
    ExampleErrorSink*		    m_pErrorSink;
    ExampleAuthenticationManager*   m_pAuthMgr;
    ExampleSiteSupplier*	    m_pSiteSupplier;
};
