/****************************************************************************
 * 
 *  $Id$
 *
 *  Copyright (C) 1995-1999 RealNetworks, Inc. All rights reserved.
 *  
 *  http://www.real.com/devzone
 *
 *  This program contains proprietary 
 *  information of Progressive Networks, Inc, and is licensed
 *  subject to restrictions on use and distribution.
 *
 *
 *  RealMedia Architecture Plug-in Interfaces.
 *
 */

#ifndef _RMAVALUE_H_
#define _RMAVALUE_H_

/*
 * Forward declarations of some interfaces defined or used here-in.
 */
typedef _INTERFACE  IUnknown			    IUnknown;
typedef _INTERFACE  IRMABuffer			    IRMABuffer;
typedef _INTERFACE  IRMAKeyedListIterator	    IRMAKeyedListIterator;
typedef _INTERFACE  IRMAUniquelyKeyedList	    IRMAUniquelyKeyedList;

/****************************************************************************
 * 
 *  Interface:
 *
 *	IRMAKeyedListIterator
 *
 *  Purpose:
 *
 *	Iterator for KeyedLists
 *	
 *
 *  IRMAKeyedListIterator:
 *
 *	{0x00003100-0901-11d1-8B06-00A024406D59}
 *
 */
DEFINE_GUID(IID_IRMAKeyedListIterator,   0x00003100, 0x901, 0x11d1, 0x8b, 0x6, 0x0, 0xa0, 0x24, 0x40, 0x6d, 0x59);

#undef  INTERFACE
#define INTERFACE   IRMAKeyedListIterator

DECLARE_INTERFACE_(IRMAKeyedListIterator, IUnknown)
{
    /*
     *	IUnknown methods
     */
    STDMETHOD(QueryInterface)	(THIS_
				REFIID riid,
				void** ppvObj) PURE;

    STDMETHOD_(ULONG32,AddRef)	(THIS) PURE;

    STDMETHOD_(ULONG32,Release)	(THIS) PURE;

    /************************************************************************
     *	Method:
     *	    IRMAKeyedListIterator::
     *	Purpose:
     *	    This function is called to set the context for the plugin.
     *
     */

    /* step forward */
    STDMETHOD(Next) (THIS) PURE;

    /* step backward */
    STDMETHOD(Previous) (THIS) PURE;

    /* find next matching key */
    STDMETHOD(FindNext) (THIS) PURE;

    /* return TRUE if iterator is at beginning of list */
    STDMETHOD_(BOOL, AtBeginning) (THIS) PURE;

    /* return TRUE if iterator is one past the last node in the list */
    STDMETHOD_(BOOL, AtEnd) (THIS) PURE;

    /* insert key/value pair before current position 
     * if the last parameter is not NULL it returns 
     * a new iterator set at the new value */
    STDMETHOD(Insert)
    (
	THIS_ 
	const char* pKey,
	IUnknown* pValue,
	IRMAKeyedListIterator** ppIteratorEnd
    ) PURE;

    /* insert the specified list of nodes from another list before 
     * current position in this list (includes pIteratorBegin through
     * the node before pIteratorEnd, since End always means one past
     * the last node) */
    STDMETHOD(InsertSpan)
    (
	THIS_ 
	IRMAKeyedListIterator* pIteratorBegin,
	IRMAKeyedListIterator* pIteratorEnd
    ) PURE;

    /* removes current node and its key */
    STDMETHOD(Remove) (THIS) PURE;

    /* Remove the nodes specified from this list. (includes 
     * the current node through the node before pIteratorEnd, 
     * since End always means one past the last node) */
    STDMETHOD(RemoveSpan)
    (
	THIS_ 
	IRMAKeyedListIterator* pIteratorEnd
    ) PURE;

    /* get current node key */
    STDMETHOD_(const char*, GetKey) (THIS) PURE;

    /* get current node key as a buffer */
    STDMETHOD(GetKeyAsBuffer) (THIS_ REF(IRMABuffer*) pKey) PURE;

    /* get current node value */
    STDMETHOD(GetValue) (THIS_ REF(IUnknown*) pValue) PURE;
    
    /* set current node value */
    STDMETHOD(SetValue) (THIS_ IUnknown* pValue) PURE;

    /* get current node key and value */
    STDMETHOD(GetCurrent)
    (
	THIS_ 
	REF(const char*) pKey,
	REF(IUnknown*) pValue
    ) PURE;

    /* return IUnknown of list being iterated */
    STDMETHOD(GetList) (THIS_ REF(IUnknown*) pList) PURE;

    /* return TRUE if iterator is at the same position of the 
      same list */
    STDMETHOD_(BOOL, AtSamePosition) (THIS_ IRMAKeyedListIterator*) PURE;

    /* return TRUE if iterator is at the same node of the same list
     * this private version is called by the public version.  The
     * UINT32 it passes in contains impl specific instance and position
     * data.  (ex. some hash of the current node pointer) 	*/
    STDMETHOD_(BOOL, _AtSamePositionPrivate) (THIS_ UINT32) PURE;

};

/****************************************************************************
 * 
 *  Interface:
 *
 *	IRMAUniquelyKeyedList
 *
 *  Purpose:
 *
 *	UniquelyKeyedList
 *	
 *
 *  IRMAUniquelyKeyedList:
 *
 *	{0x00003101-0901-11d1-8B06-00A024406D59}
 *
 */
DEFINE_GUID(IID_IRMAUniquelyKeyedList,   0x00003101, 0x901, 0x11d1, 0x8b, 0x6, 0x0, 0xa0, 0x24, 0x40, 0x6d, 0x59);

#define CLSID_IRMAUniquelyKeyedList IID_IRMAUniquelyKeyedList

#undef  INTERFACE
#define INTERFACE   IRMAUniquelyKeyedList

DECLARE_INTERFACE_(IRMAUniquelyKeyedList, IUnknown)
{
    /*
     *	IUnknown methods
     */
    STDMETHOD(QueryInterface)	(THIS_
				REFIID riid,
				void** ppvObj) PURE;

    STDMETHOD_(ULONG32,AddRef)	(THIS) PURE;

    STDMETHOD_(ULONG32,Release)	(THIS) PURE;


    /* returns number of nodes in list */
    STDMETHOD_(UINT32, GetSize)(THIS) PURE;

    /* return iterator set to the first node in the list */
    STDMETHOD(Begin) (THIS_ REF(IRMAKeyedListIterator*)) PURE;

    /* return iterator set to one past the last node in 
     * the list */
    STDMETHOD(End) (THIS_ REF(IRMAKeyedListIterator*)) PURE;

    /* return iterator set to first node of list 
     * with key == pKey */
    STDMETHOD(FindFirst)
    (
	THIS_
	const char* pKey,
	REF(IRMAKeyedListIterator*)
    ) PURE;

    /* remove all nodes with this key */
    STDMETHOD(Remove) (THIS_ const char* pKey) PURE;

};

/****************************************************************************
 * 
 *  Interface:
 *
 *	IRMAUniquelyKeyedIList
 *
 *  Purpose:
 *
 *	UniquelyKeyedList(CaseInsensitive)
 *	
 *
 *  IRMAUniquelyKeyedIList:
 *
 *	{0x00003102-0901-11d1-8B06-00A024406D59}
 *
 */
DEFINE_GUID(IID_IRMAUniquelyKeyedIList,   0x00003102, 0x901, 0x11d1, 0x8b, 0x6, 0x0, 0xa0, 0x24, 0x40, 0x6d, 0x59);

#define CLSID_IRMAUniquelyKeyedIList IID_IRMAUniquelyKeyedIList

#undef  INTERFACE
#define INTERFACE   IRMAUniquelyKeyedIList

DECLARE_INTERFACE_(IRMAUniquelyKeyedIList, IUnknown)
{
    /*
     *	IUnknown methods
     */
    STDMETHOD(QueryInterface)	(THIS_
				REFIID riid,
				void** ppvObj) PURE;

    STDMETHOD_(ULONG32,AddRef)	(THIS) PURE;

    STDMETHOD_(ULONG32,Release)	(THIS) PURE;


    /* returns number of nodes in list */
    STDMETHOD_(UINT32, GetSize)(THIS) PURE;

    /* return iterator set to the first node in the list */
    STDMETHOD(Begin) (THIS_ REF(IRMAKeyedListIterator*)) PURE;

    /* return iterator set to one past the last node in 
     * the list */
    STDMETHOD(End) (THIS_ REF(IRMAKeyedListIterator*)) PURE;

    /* return iterator set to first node of list 
     * with key == pKey */
    STDMETHOD(FindFirst)
    (
	THIS_
	const char* pKey,
	REF(IRMAKeyedListIterator*)
    ) PURE;

    /* remove all nodes with this key */
    STDMETHOD(Remove) (THIS_ const char* pKey) PURE;

};

/****************************************************************************
 * 
 *  Interface:
 *
 *	IRMAKeyedList
 *
 *  Purpose:
 *
 *	KeyedList(CaseSensitive)
 *	
 *
 *  IRMAKeyedList:
 *
 *	{0x00003103-0901-11d1-8B06-00A024406D59}
 *
 */
DEFINE_GUID(IID_IRMAKeyedList,   0x00003103, 0x901, 0x11d1, 0x8b, 0x6, 0x0, 0xa0, 0x24, 0x40, 0x6d, 0x59);

#define CLSID_IRMAKeyedList IID_IRMAKeyedList

#undef  INTERFACE
#define INTERFACE   IRMAKeyedList

DECLARE_INTERFACE_(IRMAKeyedList, IUnknown)
{
    /*
     *	IUnknown methods
     */
    STDMETHOD(QueryInterface)	(THIS_
				REFIID riid,
				void** ppvObj) PURE;

    STDMETHOD_(ULONG32,AddRef)	(THIS) PURE;

    STDMETHOD_(ULONG32,Release)	(THIS) PURE;


    /* returns number of nodes in list */
    STDMETHOD_(UINT32, GetSize)(THIS) PURE;

    /* return iterator set to the first node in the list */
    STDMETHOD(Begin) (THIS_ REF(IRMAKeyedListIterator*)) PURE;

    /* return iterator set to one past the last node in 
     * the list */
    STDMETHOD(End) (THIS_ REF(IRMAKeyedListIterator*)) PURE;

    /* return iterator set to first node of list 
     * with key == pKey */
    STDMETHOD(FindFirst)
    (
	THIS_
	const char* pKey,
	REF(IRMAKeyedListIterator*)
    ) PURE;

    /* remove all nodes with this key */
    STDMETHOD(Remove) (THIS_ const char* pKey) PURE;

};

/****************************************************************************
 * 
 *  Interface:
 *
 *	IRMAKeyedIList
 *
 *  Purpose:
 *
 *	KeyedList(CaseInsensitive)
 *	
 *
 *  IRMAKeyedIList:
 *
 *	{0x00003104-0901-11d1-8B06-00A024406D59}
 *
 */
DEFINE_GUID(IID_IRMAKeyedIList,   0x00003104, 0x901, 0x11d1, 0x8b, 0x6, 0x0, 0xa0, 0x24, 0x40, 0x6d, 0x59);

#define CLSID_IRMAKeyedIList IID_IRMAKeyedIList

#undef  INTERFACE
#define INTERFACE   IRMAKeyedIList

DECLARE_INTERFACE_(IRMAKeyedIList, IUnknown)
{
    /*
     *	IUnknown methods
     */
    STDMETHOD(QueryInterface)	(THIS_
				REFIID riid,
				void** ppvObj) PURE;

    STDMETHOD_(ULONG32,AddRef)	(THIS) PURE;

    STDMETHOD_(ULONG32,Release)	(THIS) PURE;


    /* returns number of nodes in list */
    STDMETHOD_(UINT32, GetSize)(THIS) PURE;

    /* return iterator set to the first node in the list */
    STDMETHOD(Begin) (THIS_ REF(IRMAKeyedListIterator*)) PURE;

    /* return iterator set to one past the last node in 
     * the list */
    STDMETHOD(End) (THIS_ REF(IRMAKeyedListIterator*)) PURE;

    /* return iterator set to first node of list 
     * with key == pKey */
    STDMETHOD(FindFirst)
    (
	THIS_
	const char* pKey,
	REF(IRMAKeyedListIterator*)
    ) PURE;

    /* remove all nodes with this key */
    STDMETHOD(Remove) (THIS_ const char* pKey) PURE;

};


/****************************************************************************
 * 
 *  Interface:
 *
 *	IRMAUtilities
 *
 *  Purpose:
 *
 *	Utilities
 *	
 *
 *  IRMAUtilities:
 *
 *	{0x00003105-0901-11d1-8B06-00A024406D59}
 *
 */
DEFINE_GUID(IID_IRMAUtilities,   0x00003105, 0x901, 0x11d1, 0x8b, 0x6, 0x0, 0xa0, 0x24, 0x40, 0x6d, 0x59);

#undef  INTERFACE
#define INTERFACE   IRMAUtilities

DECLARE_INTERFACE_(IRMAUtilities, IUnknown)
{
    /*
     *	IUnknown methods
     */
    STDMETHOD(QueryInterface)	(THIS_
				REFIID riid,
				void** ppvObj) PURE;

    STDMETHOD_(ULONG32,AddRef)	(THIS) PURE;

    STDMETHOD_(ULONG32,Release)	(THIS) PURE;

    /* IRMAUtilities methods */

    /* return a deep copy of this object initialized
     * to the same state (as close as possible) */
    STDMETHOD(Copy) (THIS_ REF(IUnknown*) pUnknown) PURE;

    /* return a Human readable CString describing
     * the current state of this object  
     * (per darrens request) */
    STDMETHOD(Dump) (THIS_ REF(IRMABuffer*) pBuffer) PURE;


};

/****************************************************************************
 * 
 *  Interface:
 *
 *	IRMAUINT32
 *
 *  Purpose:
 *
 *	Contain a UINT32
 *	
 *
 *  IRMAUINT32:
 *
 *	{0x00003106-0901-11d1-8B06-00A024406D59}
 *
 */
DEFINE_GUID(IID_IRMAUINT32,   0x00003106, 0x901, 0x11d1, 0x8b, 0x6, 0x0, 0xa0, 0x24, 0x40, 0x6d, 0x59);

#define CLSID_IRMAUINT32 IID_IRMAUINT32

#undef  INTERFACE
#define INTERFACE   IRMAUINT32

DECLARE_INTERFACE_(IRMAUINT32, IUnknown)
{
    /*
     *	IUnknown methods
     */
    STDMETHOD(QueryInterface)	(THIS_
				REFIID riid,
				void** ppvObj) PURE;

    STDMETHOD_(ULONG32,AddRef)	(THIS) PURE;

    STDMETHOD_(ULONG32,Release)	(THIS) PURE;

    /* IRMAUINT32 methods */

    /* set the UINT32 value of this object */
    STDMETHOD(Set)		(THIS_ const UINT32 ulValue) PURE;

    /* return the UINT32 value of this object */
    STDMETHOD_(UINT32, GetValue)	(THIS) PURE;

};

/****************************************************************************
 * 
 *  Interface:
 *
 *	IRMACString
 *
 *  Purpose:
 *
 *	Contain a IRMACString
 *	
 *
 *  IRMACString:
 *
 *	{0x00003107-0901-11d1-8B06-00A024406D59}
 *
 */
DEFINE_GUID(IID_IRMACString,   0x00003107, 0x901, 0x11d1, 0x8b, 0x6, 0x0, 0xa0, 0x24, 0x40, 0x6d, 0x59);

#define CLSID_IRMACString IID_IRMACString

#undef  INTERFACE
#define INTERFACE   IRMACString

DECLARE_INTERFACE_(IRMACString, IUnknown)
{
    /*
     *	IUnknown methods
     */
    STDMETHOD(QueryInterface)	(THIS_
				REFIID riid,
				void** ppvObj) PURE;

    STDMETHOD_(ULONG32,AddRef)	(THIS) PURE;

    STDMETHOD_(ULONG32,Release)	(THIS) PURE;

    /* IRMACString methods */

    /* set the CString value of this object */
    STDMETHOD(Set)		(THIS_ const char* pValue) PURE;

    /* return the CString value of this object */
    STDMETHOD_(const char*, GetValue)	(THIS) PURE;

    /* set the CString value of this object 
     * from a Buffer */
    STDMETHOD(FromBuffer)	(THIS_ IRMABuffer* pBuffer) PURE;

    /* return the CString value of this object 
     * in a Buffer */
    STDMETHOD(AsBuffer)	(THIS_ REF(IRMABuffer*) pBuffer) PURE;

};


#endif /* !_RMAVALUE_H_ */
