/****************************************************************************
 * 
 *  $Id$
 *  
 *
 */

#include <stdio.h>

#include "pncom.h"
#include "pntypes.h"
#include "pntypes.h"
#include "pnwintyp.h"

///#include "cpnxtype.h"

#include "rmapckts.h"
#include "rmawin.h"
#include "rmasite2.h"
//#include "rmavctrl.h"
#include "rmavsurf.h"
#include "rmacomm.h"

#include "fivemlist.h"

#include "exvsurf.h"
#include "exnwsite.h"

// CallerHelper
#include "std.h"
#include "PyCppApi.h"

#ifdef _DEBUG
#undef PN_THIS_FILE		
static char PN_THIS_FILE[] = __FILE__;
#endif



ExampleVideoSurface::ExampleVideoSurface(IUnknown* pContext, ExampleWindowlessSite* pSiteWindowless)
    : m_lRefCount(0)
    , m_pContext(pContext)
    , m_pSiteWindowless(pSiteWindowless)
    , m_pBitmapInfo(NULL)
	, m_pyVideoSurface(NULL)

{ 
    if (m_pContext)
    {
	m_pContext->AddRef();
    }

    memset(&m_lastBitmapInfo, 0, sizeof(RMABitmapInfoHeader));
}

ExampleVideoSurface::~ExampleVideoSurface()
{
    PN_RELEASE(m_pContext);
}

void ExampleVideoSurface::SetPyVideoSurface(PyObject *obj)
	{
	Py_XDECREF(m_pyVideoSurface);
	if(obj==Py_None)m_pyVideoSurface=NULL;
	else m_pyVideoSurface=obj;
	Py_XINCREF(m_pyVideoSurface);
	}

// *** IUnknown methods ***

/////////////////////////////////////////////////////////////////////////
//  Method:
//      IUnknown::QueryInterface
//  Purpose:
//      Implement this to export the interfaces supported by your 
//      object.
//
STDMETHODIMP 
ExampleVideoSurface::QueryInterface(REFIID riid, void** ppvObj)
{
    if (IsEqualIID(riid, IID_IUnknown))
    {
        AddRef();
        *ppvObj = this;
        return PNR_OK;
    }
    else if (IsEqualIID(riid, IID_IRMAVideoSurface))
    {
        AddRef();
        *ppvObj = (IRMAVideoSurface*)this;
        return PNR_OK;
    }
    
    *ppvObj = NULL;
    return PNR_NOINTERFACE;
}

/////////////////////////////////////////////////////////////////////////
//  Method:
//      IUnknown::AddRef
//  Purpose:
//      Everyone usually implements this the same... feel free to use
//      this implementation.
//
STDMETHODIMP_(ULONG32) 
ExampleVideoSurface::AddRef()
{
	Py_XINCREF(m_pyVideoSurface);
    return InterlockedIncrement(&m_lRefCount);
}

/////////////////////////////////////////////////////////////////////////
//  Method:
//      IUnknown::Release
//  Purpose:
//      Everyone usually implements this the same... feel free to use
//      this implementation.
//
STDMETHODIMP_(ULONG32) 
ExampleVideoSurface::Release()
{
	if(m_pyVideoSurface && m_pyVideoSurface->ob_refcnt==1)
		{
		Py_XDECREF(m_pyVideoSurface);
		m_pyVideoSurface=NULL;
		}
	else Py_XDECREF(m_pyVideoSurface);

    if (InterlockedDecrement(&m_lRefCount) > 0)
    {
        return m_lRefCount;
    }

    delete this;
    return 0;
}


PN_RESULT	
ExampleVideoSurface::Init()
{
    return PNR_OK;
}


STDMETHODIMP
ExampleVideoSurface::Blt(UCHAR*		    pImageData,
			     RMABitmapInfoHeader*   pBitmapInfo,
			     REF(PNxRect)	    inDestRect,
			     REF(PNxRect)	    inSrcRect)
{
    BeginOptimizedBlt(pBitmapInfo);
    return OptimizedBlt(pImageData, inDestRect, inSrcRect);
}


STDMETHODIMP
ExampleVideoSurface::BeginOptimizedBlt(RMABitmapInfoHeader* pBitmapInfo)
{
    PN_RESULT res = PNR_FAIL;
                                                                                
    if (!pBitmapInfo)                                                           
    {                                                                           
        return res;
    }

    switch (pBitmapInfo->biCompression)
    {
      case RMA_RGB3_ID:
      case RMA_RGB555_ID:
      case RMA_RGB565_ID:
      case RMA_RGB24_ID:
      case RMA_8BIT_ID:
      case RMA_BITFIELDS: 
      case RMA_RGB:
      case RMA_YUV420_ID:
      {
        m_pBitmapInfo = pBitmapInfo;

	// see if we have new format 
	if (m_lastBitmapInfo.biWidth != pBitmapInfo->biWidth ||
	    m_lastBitmapInfo.biHeight != pBitmapInfo->biHeight ||
	    m_lastBitmapInfo.biBitCount != pBitmapInfo->biBitCount ||
	    m_lastBitmapInfo.biCompression != pBitmapInfo->biCompression)
	{
	    // format has changed since last blit...
	    //
	    //

	    // save settings for comparison next time 
	    m_lastBitmapInfo.biWidth = pBitmapInfo->biWidth;
	    m_lastBitmapInfo.biHeight = pBitmapInfo->biHeight;
	    m_lastBitmapInfo.biBitCount = pBitmapInfo->biBitCount;
	    m_lastBitmapInfo.biCompression = pBitmapInfo->biCompression;
	}

        res =  PNR_OK;
      }
    }

    return res;
}


STDMETHODIMP
ExampleVideoSurface::OptimizedBlt(UCHAR* pImageBits,			
				      REF(PNxRect) rDestRect, 
				      REF(PNxRect) rSrcRect)
{
    if (!m_pBitmapInfo)
    {
	return PNR_UNEXPECTED;
    }
	
	// For dev only, pass strings not ids 
	string s;
    switch (m_lastBitmapInfo.biCompression)
		{
		case RMA_RGB3_ID:s="RMA_RGB3_ID";break;
		case RMA_RGB555_ID:s="RMA_RGB555_ID";break;
		case RMA_RGB565_ID:s="RMA_RGB565_ID";break;
		case RMA_RGB24_ID:s="RMA_RGB24_ID";break;
		case RMA_8BIT_ID:s="RMA_8BIT_ID";break;
		case RMA_BITFIELDS:s="RMA_BITFIELDS";break; 
		case RMA_RGB:s="RMA_RGB";break;
		case RMA_YUV420_ID:s="RMA_YUV420_ID";break;
		}

	// Actual plot
	if(m_pyVideoSurface)
		{
		CallerHelper helper("Blt",m_pyVideoSurface);
		if(helper.HaveHandler())helper.call(m_lastBitmapInfo.biWidth,
			m_lastBitmapInfo.biHeight,
			m_lastBitmapInfo.biBitCount,
			s.c_str(),
			(void*)pImageBits);
		}


    //printf("ExampleVideoSurface::OptimizedBlt - yeah baby!\n");

    return PNR_OK;
 }


STDMETHODIMP
ExampleVideoSurface::EndOptimizedBlt(void)
{
    m_pBitmapInfo = NULL;

    return PNR_OK;
}


STDMETHODIMP
ExampleVideoSurface::GetOptimizedFormat(REF(RMA_COMPRESSION_TYPE) ulType)
{
    if (m_pBitmapInfo)
    {
        ulType =  m_pBitmapInfo->biCompression;
    }

    return PNR_NOTIMPL;
}


STDMETHODIMP
ExampleVideoSurface::GetPreferredFormat(REF(RMA_COMPRESSION_TYPE) ulType)
{
    ulType = RMA_RGB;
    return PNR_OK;
}
