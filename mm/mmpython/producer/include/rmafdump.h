/****************************************************************************
 * 
 *	rmafdump.h
 *
 *	$Id$
 *
 *	Copyright ©1998 RealNetworks.
 *	All rights reserved.
 *
 *	Definition of the Interfaces for the RMFF File Copy SDK.
 *
 */

#ifndef _RMAFDUMP_H_
#define _RMAFDUMP_H_

// Prototype to create instance of RMFFDump object and 
// typedef to get a pointer to this function from the dll
typedef PN_RESULT (PNEXPORT_PTR FPCREATEINSTANCE) (IUnknown** /*OUT*/ ppIUnknown);
STDAPI RMACreateRMFFDump(IUnknown**  /*OUT*/	ppIUnknown);


/****************************************************************************
 * 
 *  Interface:
 *
 *	IRMARMFFDump
 *
 *  Purpose:
 *
 *	Interface to rmff copy module
 *
 *  IRMARMFFDump
 *
 *  {59514C50-3129-11d2-A1C4-0060083BE563}
 *
 */

DEFINE_GUID(IID_IRMARMFFDump, 
0x59514c50, 0x3129, 0x11d2, 0xa1, 0xc4, 0x0, 0x60, 0x8, 0x3b, 0xe5, 0x63);




#define CLSID_IRMARMFFDump IID_IRMARMFFDump


#undef  INTERFACE
#define INTERFACE   IRMARMFFDump

DECLARE_INTERFACE_(IRMARMFFDump, IUnknown)
{
    /*
     *	IUnknown methods
     */
    STDMETHOD(QueryInterface)	(THIS_
				REFIID riid,
				void** ppvObj) PURE;

    STDMETHOD_(ULONG32,AddRef)	(THIS) PURE;

    STDMETHOD_(ULONG32,Release)	(THIS) PURE;

    // *** IRMARMFFDump methods ***
 
	// ***	Basic Interface ***
 
	// sets the specified .rm file as the input file
	STDMETHOD(SetInputFile) (THIS_
				const char* szFileName) PURE;  

	// sets the specified .txt file as the output file
	STDMETHOD(SetOutputFile) (THIS_
				const char* szFileName) PURE;  

	// sets the start time for the dump in milliseconds
	STDMETHOD(SetStartTime) (THIS_
				UINT32 ulStartTime) PURE;  

	// sets the end time for the dump in milliseconds. Use 0 to indicate EOF
	STDMETHOD(SetEndTime) (THIS_
				UINT32 ulEndTime) PURE;  

	// process the dump
	STDMETHOD(Process) (THIS) PURE;  
};


#endif //_RMAFDUMP_H_
