
/***********************************************************
Copyright 1991-2001 by Oratrix Development BV, Amsterdam, The Netherlands.

                        All Rights Reserved

******************************************************************/

// vidpipe.ax - A filter for converting video

#include <streams.h>
#include <initguid.h>
#include <limits.h>

#include "vidpipe.h"

#include <wtypes.h>
#include <mmsystem.h>
#include <assert.h>

// Setup data
const AMOVIESETUP_MEDIATYPE sudPinTypes =
{
    &MEDIATYPE_Video,           // Major type
    &MEDIASUBTYPE_RGB24          // Minor type
};


const AMOVIESETUP_PIN psudPins[] =
{
	{
    L"Input",                   // Name of the pin
    FALSE,                      // Is pin rendered
    FALSE,                      // Is an output pin
    FALSE,                      // Ok for no pins
    FALSE,                      // Allowed many
    &CLSID_NULL,                // Connects to filter
    L"Output",                  // Connects to pin
    1,                          // Number of pin types
    &sudPinTypes             // Details for pins
	}
};

const AMOVIESETUP_FILTER sudFilter =
{
    &CLSID_VideoPipe,			// Filter CLSID
    L"Video Pipe",	// Filter name
    MERIT_DO_NOT_USE,           // Filter merit
    1,                          // Number pins
    psudPins                    // Pin details
};

// List of class IDs and creator functions for the class factory. This
// provides the link between the OLE entry point in the DLL and an object
// being created. The class factory will call the static CreateInstance

CFactoryTemplate g_Templates[] = {
    { L"Video Pipe"
    , &CLSID_VideoPipe
    , CVideoPipe::CreateInstance
    , NULL
    , &sudFilter }
};

int g_cTemplates = 1;


// This goes in the factory template table to create new filter instances
//
CUnknown * WINAPI CVideoPipe::CreateInstance(LPUNKNOWN pUnk, HRESULT *phr)
{
    return  new CVideoPipe(NAME("Video Pipe"), pUnk, phr);
} 


#pragma warning(disable:4355)


CVideoPipe::CVideoPipe(TCHAR *pName,
                               LPUNKNOWN pUnk,
                               HRESULT *phr) :

    CBaseVideoRenderer(CLSID_VideoPipe,pName,pUnk,phr),
    m_InputPin(NAME("Video Pin"),this,&m_InterfaceLock,phr,L"Input"),
    m_ImageAllocator(this,NAME("Video allocator"),phr),
	m_pAdviceSink(NULL)
	
{
    // Store the video input pin
    m_pInputPin = &m_InputPin;
    m_VideoSize.cx = 0;
    m_VideoSize.cy = 0;
	m_ixframe=0;
	m_pVideoImage=NULL;
	m_lastTimestamp=0;
} 


CVideoPipe::~CVideoPipe()
{
	if(m_pAdviceSink) m_pAdviceSink->Release();
    m_pInputPin = NULL;
} 


HRESULT CVideoPipe::CheckMediaType(const CMediaType *pmtIn)
{
    // Does this have a VIDEOINFOHEADER format block
    const GUID *pFormatType = pmtIn->FormatType();
    if (*pFormatType != FORMAT_VideoInfo) {
        NOTE("Format GUID not a VIDEOINFOHEADER");
        return E_INVALIDARG;
    }
    // Check the format looks reasonably ok
    ULONG Length = pmtIn->FormatLength();
    if (Length < SIZE_VIDEOHEADER) {
        NOTE("Format smaller than a VIDEOHEADER");
        return E_FAIL;
    }

    VIDEOINFO *pInput = (VIDEOINFO *) pmtIn->Format();

    // Check the major type is MEDIATYPE_Video
    const GUID *pMajorType = pmtIn->Type();
    if (*pMajorType != MEDIATYPE_Video) {
        NOTE("Major type not MEDIATYPE_Video");
        return E_INVALIDARG;
    }

    // Check we can identify the media subtype
    const GUID *pSubType = pmtIn->Subtype();
    if (GetBitCount(pSubType) == USHRT_MAX) {
        NOTE("Invalid video media subtype");
        return E_INVALIDARG;
    }

	// Accept/enforce only RGB24
	if(*pSubType != MEDIASUBTYPE_RGB24)
		return E_INVALIDARG;

	if (m_Display.CheckHeaderValidity(pInput) == FALSE) {
        return E_INVALIDARG;
    }
   return NOERROR;
}

CBasePin *CVideoPipe::GetPin(int n)
{
    ASSERT(n == 0);
    if (n != 0) {
        return NULL;
    }

    // Assign the input pin if not already done so

    if (m_pInputPin == NULL) {
        m_pInputPin = &m_InputPin;
    }
    return m_pInputPin;

} 


STDMETHODIMP CVideoPipe::NonDelegatingQueryInterface(REFIID riid,void **ppv)
{
    CheckPointer(ppv, E_POINTER);
	if(riid == IID_IPipe)
        return GetInterface((IPipe *) this, ppv);	
    return CBaseVideoRenderer::NonDelegatingQueryInterface(riid,ppv);

} 


HRESULT CVideoPipe::SetMediaType(const CMediaType *pmt)
{
	
    CAutoLock cInterfaceLock(&m_InterfaceLock);
    m_mtIn = *pmt;
    VIDEOINFO *pVideoInfo = (VIDEOINFO *) m_mtIn.Format();
	if(!pVideoInfo) return NOERROR;
    m_ImageAllocator.NotifyMediaType(&m_mtIn);
	m_sampleSize = pmt->GetSampleSize();
	if(m_pAdviceSink) m_pAdviceSink->OnSetMediaType(&m_mtIn);
    return NOERROR;
}



HRESULT CVideoPipe::BreakConnect()
{
    CAutoLock cInterfaceLock(&m_InterfaceLock);

    // Check we are in a valid state
    HRESULT hr = CBaseVideoRenderer::BreakConnect();
    if (FAILED(hr)) {
        return hr;
    }
    // The window is not used when disconnected
    IPin *pPin = m_InputPin.GetConnected();
    m_mtIn.ResetFormatBuffer();
    return NOERROR;

} 


HRESULT CVideoPipe::CompleteConnect(IPin *pReceivePin)
{
    CAutoLock cInterfaceLock(&m_InterfaceLock);
    CBaseVideoRenderer::CompleteConnect(pReceivePin);

    // Has the video size changed between connections
    VIDEOINFOHEADER *pVideoInfo = (VIDEOINFOHEADER *) m_mtIn.Format();
    if (pVideoInfo->bmiHeader.biWidth == m_VideoSize.cx) {
        if (pVideoInfo->bmiHeader.biHeight == m_VideoSize.cy) {
            return NOERROR;
        }
    }
    m_VideoSize.cx = pVideoInfo->bmiHeader.biWidth;
    m_VideoSize.cy = pVideoInfo->bmiHeader.biHeight;
    return NOERROR;

} 


void CVideoPipe::PrepareRender()
{
    // Realise the palette on this thread
	
} 
void CVideoPipe::OnReceiveFirstSample(IMediaSample *pMediaSample)
{
} 

HRESULT CVideoPipe::DoRenderSample(IMediaSample *pMediaSample)
{	
	if(m_pAdviceSink) m_pAdviceSink->OnRenderSample(pMediaSample);
    return NOERROR; 
} 


HRESULT CVideoPipe::Active()
{

	VIDEOINFOHEADER *pVideoInfo = (VIDEOINFOHEADER *)m_mtIn.Format();
	// fix rcSource
	pVideoInfo->rcSource.left = pVideoInfo->rcTarget.left = 0;
	pVideoInfo->rcSource.top = pVideoInfo->rcTarget.top = 0;
	pVideoInfo->rcSource.right = pVideoInfo->rcTarget.right = m_VideoSize.cx;
	pVideoInfo->rcSource.bottom = pVideoInfo->rcTarget.bottom = m_VideoSize.cy;
	if(m_pAdviceSink) m_pAdviceSink->OnActive();
	return CBaseVideoRenderer::Active();
} 

HRESULT CVideoPipe::Inactive()
{
	if(m_pAdviceSink) m_pAdviceSink->OnInactive();	
	return CBaseVideoRenderer::Inactive();
}

HRESULT CVideoPipe::GetImageHeader(BITMAPINFOHEADER *pbih,
                                    VIDEOINFOHEADER *pVideoInfo,
                                    RECT *pSourceRect)
{
    // Is the data format compatible
    if (pVideoInfo->bmiHeader.biCompression != BI_RGB) {
        if (pVideoInfo->bmiHeader.biCompression != BI_BITFIELDS) {
			//Log("Invalid biCompression ",pVideoInfo->bmiHeader.biCompression);
            return E_INVALIDARG;
        }
    }

    ASSERT(IsRectEmpty(pSourceRect) == FALSE);
    BITMAPINFOHEADER& bih=*pbih;
    CopyMemory((PVOID)pbih, (PVOID)&pVideoInfo->bmiHeader, sizeof(BITMAPINFOHEADER));
    bih.biWidth = WIDTH(pSourceRect);
    bih.biHeight = HEIGHT(pSourceRect);
    bih.biBitCount = pVideoInfo->bmiHeader.biBitCount;
    bih.biSizeImage = DIBSIZE(bih);
	return NOERROR;
}

HRESULT CVideoPipe::CopyImage(IMediaSample *pMediaSample,
                                     VIDEOINFOHEADER *pVideoInfo,
                                     LONG *pBufferSize,
                                     BYTE **ppVideoImage,
                                     RECT *pSourceRect)
{
	
    NOTE("Entering CopyImage");
    ASSERT(pSourceRect);
    BYTE *pCurrentImage;

    // Check we have an image to copy

    if (pMediaSample == NULL || pSourceRect == NULL ||
            pVideoInfo == NULL) {

		//Log("NULL arguments ");
        return E_UNEXPECTED;
    }

    // Is the data format compatible
    if (pVideoInfo->bmiHeader.biCompression != BI_RGB) {
        if (pVideoInfo->bmiHeader.biCompression != BI_BITFIELDS) {
			//Log("Invalid biCompression ",pVideoInfo->bmiHeader.biCompression);
            return E_INVALIDARG;
        }
    }

    ASSERT(IsRectEmpty(pSourceRect) == FALSE);

    BITMAPINFOHEADER bih;
    bih.biWidth = WIDTH(pSourceRect);
    bih.biHeight = HEIGHT(pSourceRect);
    bih.biBitCount = pVideoInfo->bmiHeader.biBitCount;
    LONG Size = GetBitmapFormatSize(HEADER(pVideoInfo)) - SIZE_PREHEADER;
    LONG Total = Size + DIBSIZE(bih);

	*ppVideoImage = new BYTE[Total];
	*pBufferSize=Total;
	BYTE *pVideoImage=*ppVideoImage;

    // Copy the BITMAPINFO

    CopyMemory((PVOID)pVideoImage, (PVOID)&pVideoInfo->bmiHeader, Size);
    ((BITMAPINFOHEADER *)pVideoImage)->biWidth = WIDTH(pSourceRect);
    ((BITMAPINFOHEADER *)pVideoImage)->biHeight = HEIGHT(pSourceRect);
    ((BITMAPINFOHEADER *)pVideoImage)->biSizeImage = DIBSIZE(bih);
    BYTE *pImageData = pVideoImage + Size;

    // Get the pointer to it's image data

    HRESULT hr = pMediaSample->GetPointer(&pCurrentImage);
    if (FAILED(hr)) {
		//Log("GetPointer failed");
        return hr;
    }

    // Now we are ready to start copying the source scan lines

    LONG ScanLine = (pVideoInfo->bmiHeader.biBitCount / 8) * WIDTH(pSourceRect);
    LONG LinesToSkip = pVideoInfo->bmiHeader.biHeight;
    LinesToSkip -= pSourceRect->top + HEIGHT(pSourceRect);
    pCurrentImage += LinesToSkip * DIBWIDTHBYTES(pVideoInfo->bmiHeader);
    pCurrentImage += pSourceRect->left * (pVideoInfo->bmiHeader.biBitCount / 8);

    // Even money on this GP faulting sometime...
    for (LONG Line = 0;Line < HEIGHT(pSourceRect);Line++) {
        CopyMemory((PVOID)pImageData, (PVOID)pCurrentImage, ScanLine);
        pImageData += DIBWIDTHBYTES(*(BITMAPINFOHEADER *)pVideoImage);
        pCurrentImage += DIBWIDTHBYTES(pVideoInfo->bmiHeader);
    }
    return NOERROR;
}


HRESULT CVideoPipe::SetRendererAdviceSink(IRendererAdviceSink *pI)
	{
	if(m_pAdviceSink) m_pAdviceSink->Release();
	m_pAdviceSink = pI;
	m_pAdviceSink->AddRef();
	return S_OK;
	}

////////////////////////////////////////////////
// CVideoInputPin

CVideoInputPin::CVideoInputPin(TCHAR *pObjectName,
                               CVideoPipe *pRenderer,
                               CCritSec *pInterfaceLock,
                               HRESULT *phr,
                               LPCWSTR pPinName) :

    CRendererInputPin(pRenderer,phr,pPinName),
    m_pRenderer(pRenderer),
    m_pInterfaceLock(pInterfaceLock)
{
    ASSERT(m_pRenderer);
    ASSERT(pInterfaceLock);

} 


////////////////////////////////////////////////
// Filter registration

STDAPI DllRegisterServer()
{
    return AMovieDllRegisterServer2(TRUE);
} 

STDAPI DllUnregisterServer()
{
    return AMovieDllRegisterServer2(FALSE);
} 
