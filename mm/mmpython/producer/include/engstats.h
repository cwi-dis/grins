/****************************************************************************
 * 
 *  $Id$
 *
 *  engstats.h
 *
 *  Copyright ©1998 RealNetworks.
 *  All rights reserved.
 *
 *  http://www.real.com/devzone
 *
 *  This program contains proprietary information of RealNetworks, Inc., 
 *  and is licensed subject to restrictions on use and distribution.
 *
 *
 *  Definition of the interfaces for the statistics.
 * 
 */

#ifndef _ENGSTATS_H_
#define _ENGSTATS_H_

typedef _INTERFACE IUnknown			IUnknown;
typedef _INTERFACE IRMAEncodingStatisticsControl IRMAEncodingStatisticsControl;
typedef _INTERFACE IRMAEncodingStatisticsNotification IRMAEncodingStatisticsNotification;

#define ENC_STATISTICS_AT_END 0xFFFFFF

/****************************************************************************
 * 
 *  Interface:
 *
 *	IRMAEncodingStatisticsControl
 *
 *  Purpose:
 *
 *	Interface for setting up the encoding statistics
 *	Use this to add statistics notifications, change the update interval, force updates
 *
 *  IRMAEncodingStatisticsControl
 *
 *  {9E8C2351-1DBA-11d2-89C7-00C0F0177720}
 *
 */
DEFINE_GUID(IID_IRMAEncodingStatisticsControl, 
	    0x9e8c2351, 0x1dba, 0x11d2, 0x89, 0xc7, 0x0, 0xc0, 0xf0, 0x17, 0x77, 0x20);

#undef  INTERFACE
#define INTERFACE   IRMAEncodingStatisticsControl

DECLARE_INTERFACE_(IRMAEncodingStatisticsControl, IUnknown)
{
    /***********************************************************************/
    /*
     *	IUnknown methods
     */
    STDMETHOD(QueryInterface)		(THIS_
					 REFIID riid,
					 void** ppvObj) PURE;

    STDMETHOD_(UINT32,AddRef)		(THIS) PURE;

    STDMETHOD_(UINT32,Release)		(THIS) PURE;

    /***********************************************************************/
    /*
     * IRMAEncodingStatisticsControl methods
     */

    /************************************************************************
     *	Method:
     *	    IRMAEncodingStatisticsControl::AddStatisticsNotification
     *	Purpose:
     *	    Tells the statistics controller to notify the added statistics notification
     *	    when statistics are modified
     *	Parameters:
     *	    pStatsNotification - [in] pointer to a statistics notification that will be notified
     */
    STDMETHOD(AddStatisticsNotification)	(THIS_
	IRMAEncodingStatisticsNotification* pStatsNotification) PURE;

    /************************************************************************
     *	Method:
     *	    IRMAEncodingStatisticsControl::RemoveStatisticsNotification
     *	Purpose:
     *	    Call this method to remove a statistics notification
     *	Parameters:
     *	    pStatsNotification - [in] pointer to a statistics notification to remove from the list
     */
    STDMETHOD(RemoveStatisticsNotification)	(THIS_
	IRMAEncodingStatisticsNotification* pStatsNotification) PURE;

    /************************************************************************
     *	Method:
     *	    IRMAEncodingStatisticsControl::Get/SetUpdateInterval
     *	Purpose:
     *	    Set the interval at which statistics are recalculated and updated for notifications
     *	Parameters:
     *	    nInterval - [in/out] interval for updating (in milliseconds), default: 500
     *	Note: 
     *	    Use ENC_STATISTICS_AT_END if you only want a notification when the encoding is complete
     *	    Statistics will not be recalculated faster than every 500 ms 
     */
    STDMETHOD(GetUpdateInterval)	(THIS_
	UINT32* pnInterval) PURE;
    STDMETHOD(SetUpdateInterval)	(THIS_
	UINT32 nInterval) PURE;

    /************************************************************************
     *	Method:
     *	    IRMAEncodingStatisticsControl::UpdateStatistics
     *	Purpose:
     *	    Force an update of the statistics. Before encoding, this will cause the stream lists to be 
     *	    regenerated; during encoding, this will cause the stream statistics to be recalculated and
     *	    written to the registry
     *	Parameters:
     *	    pStatsNotification - [in] pointer to a statistics notification that will be notified
     */
    STDMETHOD(UpdateStatistics)	    (THIS) PURE;
};

/****************************************************************************
 * 
 *  Interface:
 *
 *	IRMAEncodingStatisticsNotification
 *
 *  Purpose:
 *
 *	Used to notify when statistics are changed
 *
 *  IRMAEncodingStatisticsNotification
 *
 *  {466629D1-1DBF-11d2-89C7-00C0F0177720}
 *
 */
DEFINE_GUID(IID_IRMAEncodingStatisticsNotification, 
	    0x466629d1, 0x1dbf, 0x11d2, 0x89, 0xc7, 0x0, 0xc0, 0xf0, 0x17, 0x77, 0x20);

#undef  INTERFACE
#define INTERFACE   IRMAEncodingStatisticsNotification

DECLARE_INTERFACE_(IRMAEncodingStatisticsNotification, IUnknown)
{
    /***********************************************************************/
    /*
     *	IUnknown methods
     */
    STDMETHOD(QueryInterface)		(THIS_
					 REFIID riid,
					 void** ppvObj) PURE;

    STDMETHOD_(UINT32,AddRef)		(THIS) PURE;

    STDMETHOD_(UINT32,Release)		(THIS) PURE;

    /***********************************************************************/
    /*
     * IRMAEncodingStatisticsNotification methods
     */

    /************************************************************************
     *	Method:
     *	    IRMAEncodingStatisticsNotification::OnStatisticsChanged
     *	Purpose:
     *	    After you have added your EncodingStatisticsNotification to the StatisticsControl,
     *	    OnStatisticsChanged will be called whenever the statistics are updated.
     *	    Here are the values that will be passed with the notification:
     *	    "StreamsChanged" - the stream lists have been updated
     *	    MIME_REALAUDIO - audio stream properties have been updated
     *	    MIME_REALVIDEO - video stream properties have been updated
     *	Parameters:
     *	    szNotification - [in] string notification of what was updated
     */
    STDMETHOD(OnStatisticsChanged)  (THIS_
	const char* szNotification) PURE;
};

#endif
