/****************************************************************************
 * 
 *  $Id$
 *  
 */



#include <stdio.h>

#include "pncom.h"
#include "pntypes.h"
#include "pntypes.h"
#include "pnwintyp.h"


#include "rmapckts.h"
#include "rmawin.h"
#include "rmasite2.h"
#include "rmavsurf.h"
#include "rmacomm.h"

#include "fivemlist.h"

#include "exvsurf.h"
#include "exnwsite.h"

#include "Std.h"
#include "PyCppApi.h"

#include "mtpycall.h"

#ifdef _DEBUG
#undef PN_THIS_FILE		
static char PN_THIS_FILE[] = __FILE__;
#endif



ExampleVideoSurface::ExampleVideoSurface(IUnknown* pContext, ExampleWindowlessSite* pSiteWindowless)
    : m_lRefCount(0)
    , m_pContext(pContext)
    , m_pSiteWindowless(pSiteWindowless)
    , m_pBitmapInfo(NULL)
	, m_pPyVideoRenderer(NULL)
{ 
    if (m_pContext)m_pContext->AddRef();
    memset(&m_lastBitmapInfo, 0, sizeof(RMABitmapInfoHeader));
}


ExampleVideoSurface::~ExampleVideoSurface()
{
	Py_XDECREF(m_pPyVideoRenderer);
    PN_RELEASE(m_pContext);
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
    if (!pBitmapInfo) return PNR_FAIL;                                                        

	// behind the scenes format negotiation
	// return PNR_FAIL for not supported formats
	switch(pBitmapInfo->biCompression){
		// what we can accept:
		case RMA_RGB:break;
		case RMA_YUV420_ID:break;
		case RMA_BITFIELDS:break;
		case RMA_RGB24_ID:break;
		case RMA_RGB555_ID:break;
		case RMA_RGB565_ID:break;
		case RMA_8BIT_ID:break;
		case RMA_RGB3_ID:break;
		default: return PNR_FAIL;
		}

	// see if we have new format 
	if(m_lastBitmapInfo.biWidth != pBitmapInfo->biWidth ||
	    m_lastBitmapInfo.biHeight != pBitmapInfo->biHeight ||
	    m_lastBitmapInfo.biBitCount != pBitmapInfo->biBitCount ||
	    m_lastBitmapInfo.biCompression != pBitmapInfo->biCompression)
		{
		m_pBitmapInfo = pBitmapInfo;
		
	    // format has changed since last blit...
		if(m_pPyVideoRenderer && pBitmapInfo->biCompression==BI_BITFIELDS)
			{
			CallbackHelper helper("OnFormatBitFields",m_pPyVideoRenderer);
			if(helper.cancall())
				{
				PyObject *arg = Py_BuildValue("(iii)", pBitmapInfo->rcolor,pBitmapInfo->gcolor,pBitmapInfo->bcolor);
				helper.call(arg);
				}
			}
		if(m_pPyVideoRenderer)
			{
			CallbackHelper helper("OnFormatChange",m_pPyVideoRenderer);
			if(helper.cancall())
				{
				PyObject *arg = Py_BuildValue("(iiii)", pBitmapInfo->biWidth,pBitmapInfo->biHeight,
					pBitmapInfo->biBitCount, pBitmapInfo->biCompression);
				helper.call(arg);
				}
			}
	    // save settings for comparison next time 
	    m_lastBitmapInfo.biWidth = pBitmapInfo->biWidth;
	    m_lastBitmapInfo.biHeight = pBitmapInfo->biHeight;
	    m_lastBitmapInfo.biHeight = pBitmapInfo->biHeight;
	    m_lastBitmapInfo.biBitCount = pBitmapInfo->biBitCount;
	    m_lastBitmapInfo.biCompression = pBitmapInfo->biCompression;
		}
    return PNR_OK;
}


STDMETHODIMP
ExampleVideoSurface::OptimizedBlt(UCHAR* pImageBits,			
				      REF(PNxRect) rDestRect, 
				      REF(PNxRect) rSrcRect)
{
    if (!m_pBitmapInfo) return PNR_UNEXPECTED;
	if(m_pPyVideoRenderer)
		{
		CallbackHelper helper("Blt",m_pPyVideoRenderer);
		if(helper.cancall())
			{
			PyObject *arg = Py_BuildValue("(i)", (int)pImageBits);
			helper.call(arg);
			}
		}
    return PNR_OK;
}	


STDMETHODIMP
ExampleVideoSurface::EndOptimizedBlt(void)
{
	if(m_pPyVideoRenderer)
		{
		CallbackHelper helper("EndBlt",m_pPyVideoRenderer);
		if(helper.cancall())
			{
			PyObject *arg = Py_BuildValue("()");
			helper.call(arg);
			}
		}
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
