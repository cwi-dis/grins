/****************************************************************************
 * 
 *	rmaflsnk.h
 *
 *	$Id$
 *
 *	Copyright ©1998 RealNetworks.
 *	All rights reserved.
 *
 *	Definition of the IRMARMFileSink interface
 *
 */

#ifndef _RMAFLSNK_H_
#define _RMAFLSNK_H_

struct	IRMAValues;
struct	IRMAPacket;

/****************************************************************************
 * 
 *  Interface:
 *
 *	IID_IRMARMFileSink
 *
 *  Purpose:
 *
 *	A sink interface that can be registered with the IRMARMFFEditor interface allowing the user
 *  to modify (encrypt) the RM file headers and packets before they are written to the file.
 *
 *  IID_IRMARMFileSink:
 *
 *  {19137680-377B-11d2-A1C4-0060083BE563}
 *	
 *
 */

// The IRMAValues parameter in the OnMediaHeader() callback allows you to access the following:
#define RM_MEDIA_PROP_STREAM_NUMBER			"RM_MEDIA_PROP_STREAM_NUMBER"
#define RM_MEDIA_PROP_MIMETYPE				"RM_MEDIA_PROP_MIMETYPE"
#define RM_MEDIA_PROP_TYPE_SPECIFIC_DATA	"RM_MEDIA_PROP_TYPE_SPECIFIC_DATA"

DEFINE_GUID(IID_IRMARMFileSink,
	    0x19137680, 0x377b, 0x11d2, 0xa1, 0xc4, 0x0, 0x60, 0x8, 0x3b, 0xe5, 0x63);

#undef INTERFACE
#define INTERFACE IRMARMFileSink

DECLARE_INTERFACE_(IRMARMFileSink, IUnknown)
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
     * IRMARMFileSink methods
     */
   
    /************************************************************************
     *	Method:
     *	    IRMARMFileSink::OnPacket
     *	Purpose:
     *	    After you have registered your IRMARMFileSink this method will be called every 
	 *		time that a packet is about to be written to .rm file. You will have the opportunity
	 *		to modify (encrypt) the data buffer of the packet before it is written to the file.
	 */

    STDMETHOD(OnPacket)	(THIS_
		IRMAPacket* pMediaPacket, BOOL bIsKeyFrame) PURE;

    /************************************************************************
     *	Method:
     *	    IRMARMFileSink::OnMediaPropertyHeader
     *	Purpose:
     *	    After you have registered your IRMARMFileSink sink on of these methods will be called every 
	 *		time that a header (Property, MediaProperty or Content) is about to be written to .rm file. You will have the
	 *		opportunity to modify (encrypt) the type specific data of the header or mimetype 
	 *		before it is written to the file.
	 */

    STDMETHOD(OnMediaPropertyHeader) (THIS_
		IRMAValues* pValues) PURE;

};

/****************************************************************************
 * 
 *  Interface:
 *
 *	IRMARMFileSinkControl
 *
 *  Purpose:
 *
 *	A control sink interface to add and remove the RM File Sink to modify 
 *	data as it is being written. Because the data is written after the sink
 *	is notified, there can only be one sink at a time.
 *
 *  IID_IRMARMFileSinkControl:
 *
 *  {0CB88B91-A444-11d2-8792-00C0F031938B}
 *	
 *
 */
DEFINE_GUID(IID_IRMARMFileSinkControl, 
	    0xcb88b91, 0xa444, 0x11d2, 0x87, 0x92, 0x0, 0xc0, 0xf0, 0x31, 0x93, 0x8b);

#undef INTERFACE
#define INTERFACE IRMARMFileSinkControl

DECLARE_INTERFACE_(IRMARMFileSinkControl, IUnknown)
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
     * IRMARMFileSinkControl methods
     */
   
    /************************************************************************
     *	Method:
     *	    IRMARMFileSinkControl::SetRMFileSink
     *	Purpose:
     *	    Set the active RMFileSink. There can only be one RM File Sink at a
     *	    time
     */
    STDMETHOD(SetRMFileSink)	(THIS_
				IRMARMFileSink* pRMFileSink) PURE;

    /************************************************************************
     *	Method:
     *	    IRMARMFileSinkControl::RemoveRMFileSink
     *	Purpose:
     *	    Remove this RMFileSink. The RMFileSink will be removed if it is the
     *	    active RM File Sink;
     */
    STDMETHOD(RemoveRMFileSink)	(THIS_
				IRMARMFileSink* pRMFileSink) PURE;
};

#endif //_RMAFLSNK_H_
