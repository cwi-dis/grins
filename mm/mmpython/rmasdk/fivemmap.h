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
 *  fivemmap.h
 *
 *  Basic map class.
 */
#ifndef _FIVEMMAP_H_
#define _FIVEMMAP_H_

#ifndef _PNTYPES_H_
    #error FiveMinuteMap assumes pntypes.h.
#endif


/****************************************************************************
 *
 *  FiveMinuteMap Class
 *
 */
class FiveMinuteMap
{
    /****** Class Variables ***********************************************/
    const int AllocationSize;
    void**  m_pKeyArray;
    void**  m_pValueArray;
    int	    m_nMapSize;
    int	    m_nAllocSize;
    int     m_nCursor;

    public:
    /****** Public Class Methods ******************************************/
    FiveMinuteMap()
	: m_pKeyArray(NULL)
	, m_pValueArray(NULL)
	, m_nMapSize(0)
	, m_nAllocSize(0)
        , m_nCursor(0)
	, AllocationSize(10)
	{};

    ~FiveMinuteMap()
	{
	    delete [] m_pKeyArray;
	    delete [] m_pValueArray;
	};

    int   GetCount() {return m_nMapSize;}
    void* GetFirstValue();
    void* GetNextValue();
    BOOL  Lookup(void* Key, void*& Value) const;
    void  RemoveKey(void* Key);
    void  RemoveValue(void* Value);
    void  SetAt(void* Key, void* Value);
};

#endif /* _FIVEMMAP_H_ */
