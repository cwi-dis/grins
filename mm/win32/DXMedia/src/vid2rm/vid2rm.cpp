/***********************************************************
Copyright 1991-1999 by Oratrix Development BV, Amsterdam, The Netherlands.

                        All Rights Reserved

******************************************************************/

// vid2rm.ax - A filter for converting video to real media through the real producer

#include <streams.h>
#include <initguid.h>
#include <limits.h>

#include "vid2rm.h"

#include <stdio.h>

// options
#define PREVIEW_VIDEO
#define LOG_ACTIVITY
//#define SAVE_FRAMES_AS_BMP

namespace RProducer {
bool HasEngine();
bool SetEngine(IUnknown *p);
bool SetInputPin(IUnknown *p);
bool CreateMediaSample();
bool SetVideoInfo(int w,int h,float rate);
bool EncodeSample(BYTE *p,DWORD size,DWORD msec,bool isSync,bool isLast);
void DoneEncoding();
void Release();
}

// Setup data

const AMOVIESETUP_MEDIATYPE sudVidPinTypes =
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
    &sudVidPinTypes             // Details for pins
	}
};

const AMOVIESETUP_FILTER sudSampVid =
{
    &CLSID_Vid2rm,				// Filter CLSID
    L"Video Real Media Converter",// Filter name
    MERIT_DO_NOT_USE,           // Filter merit
    1,                          // Number pins
    psudPins                    // Pin details
};

// List of class IDs and creator functions for the class factory. This
// provides the link between the OLE entry point in the DLL and an object
// being created. The class factory will call the static CreateInstance

CFactoryTemplate g_Templates[] = {
    { L"Video Real Media Converter"
    , &CLSID_Vid2rm
    , CVideoRenderer::CreateInstance
    , NULL
    , &sudSampVid }
};

int g_cTemplates = 1;

// Debug log
FILE *logFile;
#ifdef LOG_ACTIVITY
void Log(const char *psz)
{
	if(logFile){
		fwrite(psz,1,lstrlen(psz),logFile);
		fflush(logFile);
	}
}
void Log(const char *psz,int i)
	{
	Log(psz);
	char sz[16];
	sprintf(sz,"%d\n",i);
	Log(sz);
	}
#else
void Log(const char *psz){}
void Log(const char *psz,int i){}
#endif



// This goes in the factory template table to create new filter instances
//
CUnknown * WINAPI CVideoRenderer::CreateInstance(LPUNKNOWN pUnk, HRESULT *phr)
{
    return  new CVideoRenderer(NAME("Video Real Media Converter"),pUnk,phr);
} 


#pragma warning(disable:4355)


CVideoRenderer::CVideoRenderer(TCHAR *pName,
                               LPUNKNOWN pUnk,
                               HRESULT *phr) :

    CBaseVideoRenderer(CLSID_Vid2rm,pName,pUnk,phr),
    m_InputPin(NAME("Video Pin"),this,&m_InterfaceLock,phr,L"Input"),
    m_ImageAllocator(this,NAME("Video allocator"),phr)
{
    // Store the video input pin
    m_pInputPin = &m_InputPin;
    m_VideoSize.cx = 0;
    m_VideoSize.cy = 0;
	m_ixframe=0;
	m_pVideoImage=NULL;
#ifdef LOG_ACTIVITY
	logFile=fopen("log.txt","w");
#endif
} 


CVideoRenderer::~CVideoRenderer()
{
    m_pInputPin = NULL;
	if(logFile) fclose(logFile);
} 


HRESULT CVideoRenderer::CheckMediaType(const CMediaType *pmtIn)
{
    // Does this have a VIDEOINFOHEADER format block
    const GUID *pFormatType = pmtIn->FormatType();
    if (*pFormatType != FORMAT_VideoInfo) {
        NOTE("Format GUID not a VIDEOINFOHEADER");
        return E_INVALIDARG;
    }
    ASSERT(pmtIn->Format());

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

CBasePin *CVideoRenderer::GetPin(int n)
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


STDMETHODIMP CVideoRenderer::NonDelegatingQueryInterface(REFIID riid,void **ppv)
{
    CheckPointer(ppv,E_POINTER);
    if (riid == IID_IFileSinkFilter) {
        return GetInterface((IFileSinkFilter *) this, ppv);
		}
	else if(riid == IID_IRealConverter)
        return GetInterface((IRealConverter *) this, ppv);	
    return CBaseVideoRenderer::NonDelegatingQueryInterface(riid,ppv);

} 


HRESULT CVideoRenderer::SetMediaType(const CMediaType *pmt)
{
	
    CAutoLock cInterfaceLock(&m_InterfaceLock);
    CMediaType StoreFormat(m_mtIn);
    m_mtIn = *pmt;
    VIDEOINFO *pVideoInfo = (VIDEOINFO *) m_mtIn.Format();
	if(!pVideoInfo) return NOERROR;
    m_ImageAllocator.NotifyMediaType(&m_mtIn);
    return NOERROR;
}



HRESULT CVideoRenderer::BreakConnect()
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


HRESULT CVideoRenderer::CompleteConnect(IPin *pReceivePin)
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


void CVideoRenderer::PrepareRender()
{
    // Realise the palette on this thread
	
} 
void CVideoRenderer::OnReceiveFirstSample(IMediaSample *pMediaSample)
{
    DoRenderSample(pMediaSample);

} 

HRESULT CVideoRenderer::DoRenderSample(IMediaSample *pMediaSample)
{	
	if(logFile)
		{
		char sz[256];
		sprintf(sz,"frame %d size=%d\n",m_ixframe,pMediaSample->GetActualDataLength());
		Log(sz);
		}
	EncodeSample(pMediaSample);
    return NOERROR; 
} 

void CVideoRenderer::EncodeSample(IMediaSample *pMediaSample)
{
    // Get the BITMAPINFOHEADER for the connection
	VIDEOINFOHEADER *pVideoInfo = (VIDEOINFOHEADER *)m_mtIn.Format();

    // Get the image data buffer
    BYTE *pImage;
    HRESULT hr = pMediaSample->GetPointer(&pImage);
    if (FAILED(hr)) {
        return;
    }
	
	BITMAPINFOHEADER bih;
	int w=m_VideoSize.cx,h=m_VideoSize.cy;
	RECT rcSource={0,0,w,h};
	hr=GetImageHeader(&bih,pVideoInfo,&rcSource);
    if (FAILED(hr)) {
        return;
    }
	// or hr=CopyImage(pMediaSample,pVideoInfo,&bufferSize,&m_pVideoImage,&rcSource);

	CRefTime rt(pVideoInfo->AvgTimePerFrame);
	m_lastTimestamp=m_ixframe*rt.Millisecs();
	bool isSync=(pMediaSample->IsSyncPoint()==S_OK);
	if(RProducer::HasEngine() && SUCCEEDED(hr))
		RProducer::EncodeSample(pImage,pMediaSample->GetActualDataLength(),m_lastTimestamp,isSync,false);
	m_ixframe++;

#ifdef PREVIEW_VIDEO
	HDC hdc=GetDC(NULL);
    SetDIBitsToDevice(
            (HDC) hdc,                            // Target device HDC
            0,                      // X sink position
            0,                       // Y sink position
            w, // Destination width
            h, // Destination height
            0,                     // X source position
            0,                     // Adjusted Y source position
            (UINT) 0,                               // Start scan line
            h,         // Scan lines present
            pImage,      // Image data
            (BITMAPINFO*)&bih,                    // DIB header
            DIB_RGB_COLORS);                        // Type of palette
	ReleaseDC(NULL,hdc);
#endif

#ifdef SAVE_FRAMES_AS_BMP
	char szBmp[256];
	sprintf(szBmp,"frame%d.bmp",m_ixframe);
	FILE *bmpFile=fopen(szBmp,"wb");
	if(bmpFile){
	BITMAPFILEHEADER filehdr;	
	ZeroMemory(&filehdr,sizeof(filehdr));
	*((char*)&filehdr.bfType)='B';
	*(((char*)&filehdr.bfType)+1)='M';
	filehdr.bfOffBits =sizeof(BITMAPFILEHEADER)+sizeof(BITMAPINFOHEADER); 
	filehdr.bfSize=filehdr.bfOffBits+pMediaSample->GetActualDataLength();
	filehdr.bfSize=filehdr.bfOffBits+pMediaSample->GetActualDataLength();
	fwrite(&filehdr,1,sizeof(BITMAPFILEHEADER),bmpFile);
	fwrite(&bih,1,sizeof(BITMAPINFOHEADER),bmpFile);
	fwrite(pImage,1,pMediaSample->GetActualDataLength(),bmpFile);
	fclose(bmpFile);
	}
#endif
}


HRESULT CVideoRenderer::Active()
{
	Log("Active\n");
	VIDEOINFOHEADER *pVideoInfo = (VIDEOINFOHEADER *)m_mtIn.Format();
	CRefTime rt(pVideoInfo->AvgTimePerFrame);
	float rate=1000/float(rt.Millisecs());
	if(RProducer::HasEngine())
		RProducer::SetVideoInfo(m_VideoSize.cx,m_VideoSize.cy,rate);
	char sz[128];
	sprintf(sz,"Rate=%f fps  AvgTimePerFrame=%ld msec bpp=%d\n",rate,rt.Millisecs(),
		pVideoInfo->bmiHeader.biBitCount);
	Log(sz);
 	sprintf(sz,"Size %d x %d\n",m_VideoSize.cx,m_VideoSize.cy);
	Log(sz);
   return CBaseVideoRenderer::Active();
} 

HRESULT CVideoRenderer::Inactive()
{
	if(RProducer::HasEngine())
		{
		BITMAPINFOHEADER *pbih=(BITMAPINFOHEADER*)m_pVideoImage;
		if(m_pVideoImage)
			RProducer::EncodeSample((BYTE*)(pbih+1),pbih->biSizeImage,m_lastTimestamp,false,true);
		}
	if(m_pVideoImage){
		delete[] m_pVideoImage;
		m_pVideoImage=NULL;
	}
	m_ixframe=0;
	if(RProducer::HasEngine())
		RProducer::DoneEncoding();
	Log("Inactive\n");
	return CBaseVideoRenderer::Inactive();
}

HRESULT CVideoRenderer::GetImageHeader(BITMAPINFOHEADER *pbih,
                                    VIDEOINFOHEADER *pVideoInfo,
                                    RECT *pSourceRect)
{
    // Is the data format compatible
    if (pVideoInfo->bmiHeader.biCompression != BI_RGB) {
        if (pVideoInfo->bmiHeader.biCompression != BI_BITFIELDS) {
			Log("Invalid biCompression ",pVideoInfo->bmiHeader.biCompression);
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

HRESULT CVideoRenderer::CopyImage(IMediaSample *pMediaSample,
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

		Log("NULL arguments ");
        return E_UNEXPECTED;
    }

    // Is the data format compatible
    if (pVideoInfo->bmiHeader.biCompression != BI_RGB) {
        if (pVideoInfo->bmiHeader.biCompression != BI_BITFIELDS) {
			Log("Invalid biCompression ",pVideoInfo->bmiHeader.biCompression);
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
		Log("GetPointer failed");
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


HRESULT CVideoRenderer::SetInterface(IUnknown *p,LPCOLESTR hint)
	{
    char szHint[MAX_PATH];
    if(!WideCharToMultiByte(CP_ACP,0,hint,-1,szHint,MAX_PATH,0,0))
        return ERROR_INVALID_NAME;
	if(lstrcmpi(szHint,"IRMABuildEngine")==0){
		if(!RProducer::SetEngine(p)){
			Log("Failed setting engine\n");
			RProducer::Release();
		}
	}
	else if(lstrcmpi(szHint,"IRMAInputPin")==0){
		if(!RProducer::SetInputPin(p)){
			Log("Failed setting InputPin\n");
			RProducer::Release();
		}
	}
    return NOERROR;
	}

////////////////////////////////////////////////
// CVideoInputPin

CVideoInputPin::CVideoInputPin(TCHAR *pObjectName,
                               CVideoRenderer *pRenderer,
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
    return AMovieDllRegisterServer2( TRUE );
} 

STDAPI DllUnregisterServer()
{
    return AMovieDllRegisterServer2( FALSE );
} 
