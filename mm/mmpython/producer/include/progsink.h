/****************************************************************************
 * 
 *  Copyright (C) 1998 RealNetworks.
 *  All rights reserved.
 *  
 *  http://www.real.com/devzone
 *
 *  This program contains proprietary information of RealNetworks, Inc., 
 *  and is licensed subject to restrictions on use and distribution.
 *
 *
 *  Interfaces used for progress sink/control.
 */

#ifndef _PROGSINK_H_
#define _PROGSINK_H_

/*
 * Forward declarations of some interfaces defined here-in.
 */

typedef _INTERFACE IUnknown			IUnknown;
typedef _INTERFACE IRMAProgressSink		IRMAProgressSink;
typedef _INTERFACE IRMAProgressSinkControl      IRMAProgressSinkControl;
 
/****************************************************************************
 * 
 *  Interface:
 *
 *  IRMAProgressSink
 *
 *  Purpose:
 *
 *  Supports callback notification about a job's progress
 *
 *  IRMAProgressSink
 *
 *  {6F8C5FB0-C1D3-11d2-871B-00C0F031C266}
 *
 */
DEFINE_GUID(IID_IRMAProgressSink, 
    0x6f8c5fb0, 0xc1d3, 0x11d2, 0x87, 0x1b, 0x0, 0xc0, 0xf0, 0x31, 0xc2, 0x66);


#undef  INTERFACE
#define INTERFACE   IRMAProgressSink

DECLARE_INTERFACE_(IRMAProgressSink, IUnknown)
{
    /************************************************************************
    /*
     *	IUnknown methods
     */
    STDMETHOD(QueryInterface)	(THIS_
				REFIID riid,
				void** ppvObj) PURE;

    STDMETHOD_(UINT32,AddRef)	(THIS) PURE;

    STDMETHOD_(UINT32,Release)	(THIS) PURE;

    /************************************************************************
    /*
     *	IRMAProgressSink methods
     */
   
    /************************************************************************
     *	Method:
     *	    IRMAProgressSink::SetProgress
     *	Purpose:
     *	    Set the percent complete.
     *	Parameters:
     *	    ulPercentComplete - [in] Percent of the merge that is complete.
     */
    STDMETHOD(SetProgress)	    (THIS_ UINT32 ulPercentComplete) PURE;

    /************************************************************************
     *	Method:
     *	    IRMAProgressSink::NotifyStart
     *	Purpose:
     *	    Notification that the job is starting.
     */
    STDMETHOD(NotifyStart)	    (THIS) PURE;

    /************************************************************************
     *	Method:
     *	    IRMAProgressSink::NotifyFinish
     *	Purpose:
     *	    Notification that the job is complete.
     */
    STDMETHOD(NotifyFinish)	    (THIS) PURE;

};


/****************************************************************************
 * 
 *  Interface:
 *
 *  IRMAProgressSinkControl
 *
 *  Purpose:
 *
 *  Used to register progress callbacks
 *
 *  IRMAProgressSinkControl
 *
 *  {DC464800-C1D3-11d2-871B-00C0F031C266}
 *
 */
DEFINE_GUID(IID_IRMAProgressSinkControl, 
    0xdc464800, 0xc1d3, 0x11d2, 0x87, 0x1b, 0x0, 0xc0, 0xf0, 0x31, 0xc2, 0x66);


#undef  INTERFACE
#define INTERFACE   IRMAProgressSinkControl

DECLARE_INTERFACE_(IRMAProgressSinkControl, IUnknown)
{
    /************************************************************************
    /*
     *	IUnknown methods
     */
    STDMETHOD(QueryInterface)	(THIS_
				REFIID riid,
				void** ppvObj) PURE;

    STDMETHOD_(UINT32,AddRef)	(THIS) PURE;

    STDMETHOD_(UINT32,Release)	(THIS) PURE;

    /************************************************************************
    /*
     *	IRMAProgressSinkControl methods
     */

    /* Type of progress sink */
    enum SINK_TYPE
    {
        FILE_MERGE_PROGRESS	= 0
    };
   
    /************************************************************************
     *	Method:
     *	    IRMAProgressSinkControl::AddSink
     *	Purpose:
     *	    Adds sink.
     *	Parameters:
     *      nSinkType - [in] Type of progress sink 
     *	    pObj - [in] Object that supports the IRMAProgressSink interface.
     */
    STDMETHOD(AddSink)	    (THIS_ SINK_TYPE nSinkType, IRMAProgressSink* pObj) PURE;

    /************************************************************************
     *	Method:
     *	    IRMAProgressSinkControl::RemoveSink
     *	Purpose:
     *	    Removes sink.
     *	Parameters:
     *      nSinkType - [in] Type of progress sink 
     *	    pObj - [in] Object that supports the IRMAProgressSink interface.
     */
    STDMETHOD(RemoveSink)	    (THIS_ SINK_TYPE nSinkType, IRMAProgressSink* pObj) PURE;

};

#endif //_PROGSINK_H_
