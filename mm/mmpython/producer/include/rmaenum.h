/****************************************************************************
 * 
 *  $Id$
 *
 *  rmaenum.h
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
 *  Definition of the Interfaces for an IUnknown iterator
 *
 */

#ifndef _RMAENUM_H_
#define _RMAENUM_H_
 
/****************************************************************************
 * 
 *  Interface:
 *
 *	IRMAEnumeratorIUnknown
 *
 *  Purpose:
 *
 *	Supports traversing a list of interface pointers.
 *
 *  IRMAEnumeratorIUnknown
 *
 *	{A549C3F9-AFDA-11d1-8950-00C0F0177720}
 *
 */
DEFINE_GUID(IID_IRMAEnumeratorIUnknown, 
	    0xa549c3f9, 0xafda, 0x11d1, 0x89, 0x50, 0x0, 0xc0, 0xf0, 0x17, 0x77, 0x20);

#define CLSID_IRMAEnumeratorIUnknown IID_IRMAEnumeratorIUnknown

#undef  INTERFACE
#define INTERFACE   IRMAEnumeratorIUnknown

DECLARE_INTERFACE_(IRMAEnumeratorIUnknown, IUnknown)
{
    /************************************************************************
    /*
     *	IUnknown methods
     */
    STDMETHOD(QueryInterface)	(THIS_
				REFIID riid,
				void** ppvObj) PURE;

    STDMETHOD_(ULONG32,AddRef)	(THIS) PURE;

    STDMETHOD_(ULONG32,Release)	(THIS) PURE;

    /************************************************************************
    /*
     *	IRMAEnumeratorIUnknown methods
     */
    
    /************************************************************************
     *	Method:
     *	    IRMAEnumeratorIUnknown::First
     *	Purpose:
     *	    Initializes the iterator to the first element in the list and 
     *	    returns the first element. Calls AddRef on the element before 
     *	    it is returned.
     *	Parameters:
     *	    ppValue - [out] pointer to an IUnknown to receive the element
     */
    STDMETHOD(First)	(THIS_
			IUnknown** ppValue) PURE;
    
    /************************************************************************
     *	Method:
     *	    IRMAEnumeratorIUnknown::Next
     *	Purpose:
     *	    Sets the iterator to the next element in the list and returns that element
     *	    Calls AddRef on each element before it is returned
     *	    If no more elements are found, this will set the value to NULL and return 
     *	    PNR_ELEMENT_NOT_FOUND  Note: this is not a failure error
     *	Parameters:
     *	    ppValue - [out] pointer to an IUnknown to receive the element
     */
    STDMETHOD(Next)	(THIS_
			IUnknown** ppValue) PURE;
    
    /************************************************************************
     *	Method:
     *	    IRMAEnumeratorIUnknown::GetCount
     *	Purpose:
     *	    Returns the count of the total number of elements in the list
     *	Parameters:
     *	    pnCount - [out] count of elements in the list
     */
    STDMETHOD(GetCount)	(THIS_
			UINT32* pnCount) PURE;
};

#endif // _RMAENUM_H_
