/****************************************************************************
 * 
 *	rmaedit2.h
 *
 *	$Id$
 *
 *  Copyright (C) 1998,1999 RealNetworks.
 *  All rights reserved.
 *  
 *  http://www.real.com/devzone
 *
 *  This program contains proprietary information of RealNetworks, Inc., 
 *  and is licensed subject to restrictions on use and distribution.
 *
 *
 *  Main interfaces used for the RealProducer G2 RMEditor2 SDK. This interface
 *  adds new functionality to the original RMEditor Interface.
 */

#ifndef _RMAEDIT2_H_
#define _RMAEDIT2_H_

struct IRMAValues;

/****************************************************************************
 *  Function:
 *		RMACreateRMEdit2
 *
 *  Purpose:
 *		Creates an instance of a G2 RMEditor2 object. 
 */
STDAPI RMACreateRMEdit2(IUnknown**  /*OUT*/	ppIUnknown);

typedef PN_RESULT (PNEXPORT_PTR FPCREATEINSTANCE) (IUnknown** /*OUT*/ ppIUnknown);

/****************************************************************************
 * 
 *  Interface:
 *
 *	IRMARMEdit2
 *
 *  Purpose:
 *
 *	Interface to rmeditor2 module
 *
 *  IRMARMEdit2
 *
 *  {D01CE590-B155-11d2-A1E7-0060083BE563}
 *
 */

DEFINE_GUID(IID_IRMARMEdit2, 
0xd01ce590, 0xb155, 0x11d2, 0xa1, 0xe7, 0x0, 0x60, 0x8, 0x3b, 0xe5, 0x63);

#define CLSID_IRMARMEdit2 IID_IRMARMEdit2

#undef  INTERFACE
#define INTERFACE   IRMARMEdit2

DECLARE_INTERFACE_(IRMARMEdit2, IUnknown)
{
    /***********************************************************************/
    /*
     *	IUnknown methods
     */
    STDMETHOD(QueryInterface)	(THIS_
				REFIID riid,
				void** ppvObj) PURE;

    STDMETHOD_(ULONG32,AddRef)	(THIS) PURE;

    STDMETHOD_(ULONG32,Release)	(THIS) PURE;

    /***********************************************************************/
    /*
     *	IRMARMEdit2 methods
     */
 
    /************************************************************************
     *	Method:
     *	    IRMARMEdit2::HasAudio
     *	Purpose:
     *	    returns if the current .rm file contains audio. 
     *
     *	Parameters:
     *	    pbHasAudio - [out] sets pbHasAudio to TRUE if the file contains audio
     */
	STDMETHOD(HasAudio) (THIS_
				BOOL* pbHasAudio) PURE;        

    /************************************************************************
     *	Method:
     *	    IRMARMEdit2::HasVideo
     *	Purpose:
     *	    returns if the current .rm file contains video. 
     *
     *	Parameters:
     *	    pbHasVideo - [out] sets pbHasVideo to TRUE if the file contains video
     */
	STDMETHOD(HasVideo) (THIS_
				BOOL* pbHasVideo) PURE;        

    /************************************************************************
     *	Method:
     *	    IRMARMEdit2::HasEvents
     *	Purpose:
     *	    returns if the current .rm file contains events. 
     *
     *	Parameters:
     *	    pbHasEvents - [out] sets pbHasEvents to TRUE if the file contains events
     */
	STDMETHOD(HasEvents) (THIS_
				BOOL* pbHasEvents) PURE;        

    /************************************************************************
     *	Method:
     *	    IRMARMEdit2::HasImageMaps
     *	Purpose:
     *	    returns if the current .rm file contains image maps. 
     *
     *	Parameters:
     *	    HasImageMaps - [out] sets HasImageMaps to TRUE if the file contains image maps
     */
	STDMETHOD(HasImageMaps) (THIS_
				BOOL* pbHasImageMaps) PURE;        

    /************************************************************************
     *	Method:
     *	    IRMARMEdit2::GetVideoSize
     *	Purpose:
     *	    returns the height and width of the video in pixels
     *
     *	Parameters:
     *	    pHeight - [out] contains the height of the video
     *	    pWidth - [out] contains the width of the video
     */
	STDMETHOD(GetVideoSize) (THIS_
				UINT16* pHeight, UINT16* pWidth) PURE;        

    /************************************************************************
     *	Method:
     *	    IRMARMMetaInformation::GetMetaInformation
     *	Purpose:
     *	    Get the Meta Information currently stored in the active input file
     *	    This returns a pointer to the IRMAValues that contains all of the 
     *	    properties. You can then change the meta information fields in the 
     *		returned IRMAValues. 
     *	Parameters:
     *	    ppValues - [out] IRMAValues pointer to get the existing values
     */
    STDMETHOD(GetMetaInformation) (THIS_
			IRMAValues** ppValues) PURE;
};


#endif //_RMAEDIT2_H_