/***********************************************************
Copyright 1991-1999 by Oratrix Development BV, Amsterdam, The Netherlands.

                        All Rights Reserved

******************************************************************/

// vid2rm.ax - A filter for converting video to real media through the real producer

#include <streams.h>
#include <initguid.h>
#include <limits.h>

#include "vid2rmuids.h"
#include "rconvert.h"
#include "vid2rm.h"

#include <stdio.h>

#define PREVIEW_VIDEO
//#define SAVE_FRAMES_AS_BMP

namespace RProducer {
bool HasEngine();
bool SetEngine(IUnknown *p);
bool SetInputPin(IUnknown *p);
bool CreateMediaSample();
void SetVideoInfo(int w,int h,float rate);
void EncodeSample(BYTE *p,int frame,bool isLast);
void DoneEncoding();
}

// Setup data

const AMOVIESETUP_MEDIATYPE sudPinTypes =
{
    &MEDIATYPE_Video,           // Major type
    &MEDIASUBTYPE_NULL          // Minor type
};

const AMOVIESETUP_PIN sudPins =
{
    L"Input",                   // Name of the pin
    FALSE,                      // Is pin rendered
    FALSE,                      // Is an output pin
    FALSE,                      // Ok for no pins
    FALSE,                      // Allowed many
    &CLSID_NULL,                // Connects to filter
    L"Output",                  // Connects to pin
    1,                          // Number of pin types
    &sudPinTypes                // Details for pins
};

const AMOVIESETUP_FILTER sudSampVid =
{
    &CLSID_Vid2rm,				// Filter CLSID
    L"Video Real Media Converter",// Filter name
    MERIT_DO_NOT_USE,           // Filter merit
    1,                          // Number pins
    &sudPins                    // Pin details
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
void Log(const char *psz)
{
	if(logFile){
		fwrite(psz,1,lstrlen(psz),logFile);
		fflush(logFile);
	}
}

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
	logFile=fopen("log.txt","w");
    m_VideoSize.cx = 0;
    m_VideoSize.cy = 0;
	m_ixframe=0;
	m_pVideoImage=NULL;
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
     if (m_Display.CheckHeaderValidity(pInput) == FALSE) {
        return E_INVALIDARG;
    }
   return NOERROR;
}

STDMETHODIMP CVideoRenderer::SetFileName(LPCOLESTR pszFileName,const AM_MEDIA_TYPE *pmt)
{
    // Is this a valid filename supplied

    CheckPointer(pszFileName,E_POINTER);
    if(wcslen(pszFileName) > MAX_PATH)
        return ERROR_FILENAME_EXCED_RANGE;

    // Take a copy of the filename

    m_pFileName = new WCHAR[1+lstrlenW(pszFileName)];
    if (m_pFileName == 0)
        return E_OUTOFMEMORY;
    lstrcpyW(m_pFileName,pszFileName);

    return NOERROR;

} 


STDMETHODIMP CVideoRenderer::GetCurFile(LPOLESTR * ppszFileName,AM_MEDIA_TYPE *pmt)
{
    CheckPointer(ppszFileName, E_POINTER);
    *ppszFileName = NULL;
    if (m_pFileName != NULL) {
        *ppszFileName = (LPOLESTR)
        QzTaskMemAlloc(sizeof(WCHAR) * (1+lstrlenW(m_pFileName)));
        if (*ppszFileName != NULL) {
            lstrcpyW(*ppszFileName, m_pFileName);
        }
    }

    if(pmt) {
        ZeroMemory(pmt, sizeof(*pmt));
        pmt->majortype = MEDIATYPE_NULL;
        pmt->subtype = MEDIASUBTYPE_NULL;
    }
    return S_OK;

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

HRESULT CVideoRenderer::DoRenderSample(IMediaSample *pMediaSample)
{	
    CRefTime m_StartSample;         // Start time for the current sample
    CRefTime m_EndSample;           // And likewise it's end sample time
    pMediaSample->GetMediaTime((REFERENCE_TIME*)&m_StartSample, (REFERENCE_TIME*)&m_EndSample);
    // Format the sample time stamps
	char szTimes[256];
    sprintf(szTimes,TEXT("%08d : %08d"),
             m_StartSample.Millisecs(),
             m_EndSample.Millisecs());


	if(logFile)
		{
		char sz[256];
		int n=sprintf(sz,"frame %d size=%d\n",m_ixframe,pMediaSample->GetActualDataLength());
		fwrite(sz,1,n,logFile);
		//n=sprintf(sz,"%s\n",m_DrawImage.IsUsingImageAllocator()? "IsUsingImageAllocator":"NOT UsingImageAllocator");
		//fwrite(sz,1,n,logFile);
		}
	 SlowRender(pMediaSample);
    return NOERROR; 

} 



void CVideoRenderer::PrepareRender()
{
    // Realise the palette on this thread
    // m_VideoText.DoRealisePalette();
	
} 




HRESULT CVideoRenderer::SetMediaType(const CMediaType *pmt)
{
    CAutoLock cInterfaceLock(&m_InterfaceLock);
    CMediaType StoreFormat(m_mtIn);
    HRESULT hr = NOERROR;

    m_mtIn = *pmt;
    VIDEOINFO *pVideoInfo = (VIDEOINFO *) m_mtIn.Format();
	if(!pVideoInfo) return hr;
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


void CVideoRenderer::OnReceiveFirstSample(IMediaSample *pMediaSample)
{
    ASSERT(m_pMediaType);
    DoRenderSample(pMediaSample);

} 

void CVideoRenderer::SlowRender(IMediaSample *pMediaSample)
{
    // Get the BITMAPINFOHEADER for the connection
	VIDEOINFOHEADER *pVideoInfo = (VIDEOINFOHEADER *)m_mtIn.Format();
    BITMAPINFOHEADER *pbmi = HEADER(pVideoInfo);

    // Get the image data buffer
    BYTE *pImage;
    HRESULT hr = pMediaSample->GetPointer(&pImage);
    if (FAILED(hr)) {
        return;
    }

	CRefTime rt(pVideoInfo->AvgTimePerFrame);

	// EncodeSample
	if(RProducer::HasEngine())
		{
		LONG bufferSize=0;
		if(m_pVideoImage){
			delete[] m_pVideoImage;
			m_pVideoImage=NULL;
		}
		int w=pVideoInfo->rcSource.right;
		int h=pVideoInfo->rcSource.bottom;
		RECT rcSource={0,0,w,h};
		hr=CopyImage(pMediaSample,pVideoInfo,&bufferSize,&m_pVideoImage,&rcSource);
		if(SUCCEEDED(hr))
			RProducer::EncodeSample(m_pVideoImage,m_ixframe*rt.Millisecs(),false);
		}
	m_ixframe++;

#ifdef PREVIEW_VIDEO
	HDC hdc=GetDC(NULL);
	int w=pVideoInfo->rcSource.right;
	int h=pVideoInfo->rcSource.bottom;
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
            pImage,                                 // Image data
            (BITMAPINFO *) pbmi,                    // DIB header
            DIB_RGB_COLORS);                        // Type of palette
	ReleaseDC(NULL,hdc);
#endif


#ifdef SAVE_FRAMES_AS_BMP
	char szBmp[256];
	sprintf(szBmp,"frame%d.bmp",ix);
	FILE *bmpFile=fopen(szBmp,"wb");
	if(bmpFile){
	BITMAPFILEHEADER filehdr;
	BITMAPINFOHEADER& infohdr=*pbmi;
	
	ZeroMemory(&filehdr,sizeof(filehdr));
	*((char*)&filehdr.bfType)='B';
	*(((char*)&filehdr.bfType)+1)='M';
	filehdr.bfOffBits =sizeof(BITMAPFILEHEADER)+infohdr.biSize; 
	filehdr.bfSize=filehdr.bfOffBits+pMediaSample->GetActualDataLength();

	fwrite(&filehdr,1,sizeof(BITMAPFILEHEADER),bmpFile);
	BYTE *pVideoImage;
	int w=pVideoInfo->rcSource.right;
	int h=pVideoInfo->rcSource.bottom; 
	RECT rcSource={0,0,w,h};
    hr=CopyImage(pMediaSample,pVideoInfo,&bufferSize,&pVideoImage,&rcSource);
	if(hr==NOERROR)
		fwrite(pVideoImage,1,bufferSize,bmpFile);
	delete [] pVideoImage;
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
		RProducer::SetVideoInfo(pVideoInfo->rcSource.right,
			pVideoInfo->rcSource.bottom,rate);
	char sz[128];
	sprintf(sz,"Rate=%f fps  AvgTimePerFrame=%ld msec\n",rate,rt.Millisecs());
	Log(sz);
    return CBaseVideoRenderer::Active();
} 

HRESULT CVideoRenderer::Inactive()
{
	if(RProducer::HasEngine())
		RProducer::EncodeSample(m_pVideoImage,m_ixframe++,true);
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

        return E_UNEXPECTED;
    }

    // Is the data format compatible

    if (pVideoInfo->bmiHeader.biCompression != BI_RGB) {
        if (pVideoInfo->bmiHeader.biCompression != BI_BITFIELDS) {
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
	if(lstrcmpi(szHint,"IRMABuildEngine")==0)
		{
		if(!RProducer::SetEngine(p))
			Log("Failed setting engine\n");
		}
	else if(lstrcmpi(szHint,"IRMAInputPin")==0)
		{
		if(!RProducer::SetInputPin(p))
			Log("Failed setting InputPin\n");
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
