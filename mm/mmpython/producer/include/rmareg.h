/****************************************************************************
 * 
 *  rmareg.h
 *
 *  Copyright (C) 1999 RealNetworks.
 *  All rights reserved.
 *  
 *  http://www.real.com/devzone
 *
 *  This program contains proprietary information of RealNetworks, Inc., 
 *  and is licensed subject to restrictions on use and distribution.
 *
 *
 *  Interface used for the registration of RealMedia files.
 */

#ifndef _RMAREG_H_
#define _RMAREG_H_

/*
 * Forward declarations of some interfaces defined here-in.
 */

typedef _INTERFACE IRMARealMediaRegistration		IRMARealMediaRegistration;

/****************************************************************************
 *  Function:
 *		RMACreateRealMediaRegistration
 *  Purpose:
 *		Creates an instance of a RealMedia Registration object. 
 */
STDAPI RMACreateRealMediaRegistration(IUnknown**  /*OUT*/	ppIUnknown);

typedef PN_RESULT (PNEXPORT_PTR FPCREATEINSTANCE) (IUnknown** /*OUT*/ ppIUnknown);

/****************************************************************************
 * 
 *  Interface:
 *
 *	IRMARealMediaRegistration
 *
 *  Purpose:
 *
 *	Interface to G2 RMEditor module
 *
 *  IRMARealMediaRegistration
 *
 *  {9C28D5F0-F1C4-11d2-8751-00C0F031C266}
 *
 */

DEFINE_GUID(IID_IRMARealMediaRegistration, 
0x9c28d5f0, 0xf1c4, 0x11d2, 0x87, 0x51, 0x0, 0xc0, 0xf0, 0x31, 0xc2, 0x66);

#define CLSID_IRMARealMediaRegistration IID_IRMARealMediaRegistration

enum RegFileType
{
    REG_RM_FILE = 0,
    REG_SMIL_FILE,
    REG_RP_FILE
};

#undef  INTERFACE
#define INTERFACE   IRMARealMediaRegistration

DECLARE_INTERFACE_(IRMARealMediaRegistration, IUnknown)
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
     *	IRMARealMediaRegistration methods
     */
 
    /************************************************************************
     *	Method:
     *	    IRMARealMediaRegistration::LaunchRegistrationWebPage
     *	Purpose:
     *	    Registers a file with Project Janus.
     *	Parameters:
     *	    szPathname - [in] Full pathname to the file being registered.
     */
	STDMETHOD(LaunchRegistrationWebPage) (THIS_
				const char* szPathname, RegFileType nFileType, const char* szWebPageUrl=NULL, const char* szMetaFileUrl=NULL, BOOL bRequireFileId=FALSE) PURE;                   
};

#endif //_RMAREG_H_
