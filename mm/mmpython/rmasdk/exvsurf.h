/****************************************************************************
 * 
 *  $Id$
 *  
 *  Copyright (C) 1995,1996,1997 Progressive Networks.
 *  All rights reserved.
 *
 *  This program contains proprietary 
 *  information of Progressive Networks, Inc, and is licensed
 *  subject to restrictions on use and distribution.
 *
 */


#ifndef _EXVSURF_H_
#define _EXVSURF_H_


// forward declares
class ExampleWindowlessSite;

// for PyObject
#ifndef Py_PYTHON_H
#include "Python.h"
#endif


class ExampleVideoSurface : IRMAVideoSurface
{
private:
    virtual ~ExampleVideoSurface();

protected:
    PRIVATE_DESTRUCTORS_ARE_NOT_A_CRIME

    LONG32		    m_lRefCount;
    IUnknown*		    m_pContext;
    RMABitmapInfoHeader*    m_pBitmapInfo;
    ExampleWindowlessSite*   m_pSiteWindowless;
    RMABitmapInfoHeader	    m_lastBitmapInfo;

   
public:

    ExampleVideoSurface(IUnknown* pContext, ExampleWindowlessSite* pSiteWindowless);

    PN_RESULT	Init();

	void SetPyVideoSurface(PyObject *obj);
	PyObject *m_pyVideoSurface;

    /*
     *	IUnknown methods
     */
    STDMETHOD(QueryInterface)	(THIS_
				REFIID riid,
				void** ppvObj);

    STDMETHOD_(ULONG32,AddRef)	(THIS);

    STDMETHOD_(ULONG32,Release)	(THIS);

    /*
     * IRMAVideoSurface methods usually called by renderers to
     * Draw on the surface
     */
    STDMETHOD(Blt)		(THIS_
				UCHAR*			/*IN*/	pImageData, 
				RMABitmapInfoHeader*    /*IN*/	pBitmapInfo, 
				REF(PNxRect)		/*IN*/	inDestRect,
				REF(PNxRect)		/*IN*/	inSrcRect);

    STDMETHOD(BeginOptimizedBlt)(THIS_ 
				RMABitmapInfoHeader*    /*IN*/	pBitmapInfo);
    
    STDMETHOD(OptimizedBlt)	(THIS_
				UCHAR*			/*IN*/	pImageBits,
				REF(PNxRect)		/*IN*/	rDestRect, 
				REF(PNxRect)		/*IN*/	rSrcRect);
    
    STDMETHOD(EndOptimizedBlt)	(THIS);

    STDMETHOD(GetOptimizedFormat)(THIS_
				  REF(RMA_COMPRESSION_TYPE) /*OUT*/ ulType);

    STDMETHOD(GetPreferredFormat)(THIS_
				  REF(RMA_COMPRESSION_TYPE) /*OUT*/ ulType);
};

#endif	// _EXVSURF_H_

