
/***********************************************************
Copyright 1991-2000 by Oratrix Development BV, Amsterdam, The Netherlands.

                        All Rights Reserved

******************************************************************/

// aud2wm.ax - A filter for converting audio to windows media using wmf sdk

#include <streams.h>
#include <initguid.h>
#include "aud2wm.h"

// options
// #define LOG_ACTIVITY


/*
namespace RProducer {
bool HasEngine();
bool SetEngine(IUnknown *p);
bool SetInputPin(IUnknown *p);
bool CreateMediaSample();
bool SetVideoInfo(int w,int h,float rate);
bool SetAudioInfo(int nchan,DWORD srate,int ssize);
bool EncodeSample(BYTE *p,DWORD size,DWORD msec,bool isSync,bool isLast);
void DoneEncoding();
void Release();
}*/


const AMOVIESETUP_MEDIATYPE sudAudPinTypes =
{
    &MEDIATYPE_Audio,             // MajorType
    &MEDIASUBTYPE_NULL            // MinorType
};

const AMOVIESETUP_PIN sudAudPin =
{
    L"Input",                     // The Pins name
    FALSE,                        // Is rendered
    FALSE,                        // Is an output pin
    FALSE,                        // Allowed none
    FALSE,                        // Allowed many
    &CLSID_NULL,                  // Connects to filter
    NULL,                         // Connects to pin
    1,                            // Number of types
    &sudAudPinTypes                // Pin details
};

const AMOVIESETUP_FILTER sudaud2wm =
{
    &CLSID_Aud2wm,               // Filter CLSID
    L"Audio Windows Media Converter",// String name
    MERIT_DO_NOT_USE,              // Filter merit
    1,                            // Number of pins
    &sudAudPin                    // Pin details
};


CFactoryTemplate g_Templates[] = {
    { L"Audio Windows Media Converter"
    , &CLSID_Aud2wm
    , Aud2wmRenderer::CreateInstance
    , NULL
    , &sudaud2wm },
};
int g_cTemplates = sizeof(g_Templates) / sizeof(g_Templates[0]);


// Debug log
#include <stdio.h>
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

#pragma warning(disable:4355)


Aud2wmRenderer::Aud2wmRenderer(LPUNKNOWN pUnk,HRESULT *phr) :
    CBaseRenderer(CLSID_Aud2wm, NAME("Audio Windows Media Converter"), pUnk, phr)
{
#ifdef LOG_ACTIVITY
	logFile=fopen("audlog.txt","w");
#endif

} 

Aud2wmRenderer::~Aud2wmRenderer()
{
	if(logFile) fclose(logFile);
}

CUnknown * WINAPI Aud2wmRenderer::CreateInstance(LPUNKNOWN pUnk, HRESULT *phr)
{
    return new Aud2wmRenderer(pUnk,phr);
} 


STDMETHODIMP
Aud2wmRenderer::NonDelegatingQueryInterface(REFIID riid,void **ppv)
{
	if(riid == IID_IWMConverter)
        return GetInterface((IWMConverter *) this, ppv);	
    return CBaseRenderer::NonDelegatingQueryInterface(riid,ppv);
} 

HRESULT Aud2wmRenderer::BreakConnect()
{
    return NOERROR;
} 


HRESULT Aud2wmRenderer::CheckMediaType(const CMediaType *pmt)
{
	Log("CheckMediaType\n");

    if (pmt->majortype != MEDIATYPE_Audio) {
		return E_INVALIDARG;
    }

    // Reject invalid format blocks
    if (pmt->formattype != FORMAT_WaveFormatEx) {
        return VFW_E_TYPE_NOT_ACCEPTED;
	}

    WAVEFORMATEX *pwfx = (WAVEFORMATEX *) pmt->Format();;

    // Reject compressed audio
    if (pwfx->wFormatTag != WAVE_FORMAT_PCM) {
        return VFW_E_TYPE_NOT_ACCEPTED;
    }

    // Accept only 8 or 16 bit
    if (pwfx->wBitsPerSample!=8 && pwfx->wBitsPerSample!=16) {
        return VFW_E_TYPE_NOT_ACCEPTED;
    }

    return NOERROR;
} 

HRESULT Aud2wmRenderer::SetMediaType(const CMediaType *pmt)
{
    CAutoLock cInterfaceLock(&m_InterfaceLock);
    m_mtIn = *pmt;
	WAVEFORMATEX *pwfx = (WAVEFORMATEX *)m_mtIn.Format();
	// set audio info cash
	Log("SetMediaType\n");
    return NOERROR;
}

void Aud2wmRenderer::OnReceiveFirstSample(IMediaSample *pMediaSample)
{
	if(m_ixsample==0){
		DoRenderSample(pMediaSample);	
		Log("OnReceiveFirstSample\n");
	}
	m_ixsample=0;

} 

HRESULT Aud2wmRenderer::DoRenderSample(IMediaSample *pMediaSample)
{
	if(logFile)
		{
		WAVEFORMATEX *pwfx = (WAVEFORMATEX *) m_mtIn.Format();
		int msec=1000*m_ixsample/pwfx->nSamplesPerSec;
		CRefTime tStart,tStop;
		if(SUCCEEDED(pMediaSample->GetTime((REFERENCE_TIME*)&tStart, (REFERENCE_TIME*)&tStop)))
			msec=tStart.Millisecs();
		char sz[256];
		sprintf(sz,"sample %d size=%d\n time=%d",m_ixsample,pMediaSample->GetActualDataLength(),msec);
		Log(sz);
		}
	EncodeSample(pMediaSample);
    return NOERROR;
} 

void Aud2wmRenderer::EncodeSample(IMediaSample *pMediaSample)
{
    BYTE *pBuffer;
    HRESULT hr = pMediaSample->GetPointer(&pBuffer);
    if (FAILED(hr)) {
        return;
    }
    int size = pMediaSample->GetActualDataLength();
	bool isSync=(pMediaSample->IsSyncPoint()==S_OK);
	WAVEFORMATEX *pwfx = (WAVEFORMATEX *)m_mtIn.Format();

	int msec=1000*m_ixsample/pwfx->nSamplesPerSec;
	CRefTime tStart,tStop;
    if(SUCCEEDED(pMediaSample->GetTime((REFERENCE_TIME*)&tStart, (REFERENCE_TIME*)&tStop)))
		msec=tStart.Millisecs();
	//if(RProducer::HasEngine())
	//	RProducer::EncodeSample(pBuffer,size,msec,isSync,false);
	m_ixsample++;
}

HRESULT Aud2wmRenderer::Active()
{
	Log("Active\n");
	WAVEFORMATEX *pwfx = (WAVEFORMATEX *)m_mtIn.Format();
	/*
	if(RProducer::HasEngine())
		RProducer::SetAudioInfo(pwfx->nChannels,
			pwfx->nSamplesPerSec,
			pwfx->wBitsPerSample);*/
	char sz[128];
	sprintf(sz,"Channels=%d fps  SamplesPerSec=%d  BitsPerSample=%d\n",
		pwfx->nChannels,
		pwfx->nSamplesPerSec,
		pwfx->wBitsPerSample);
	Log(sz);
   return CBaseRenderer::Active();
} 

HRESULT Aud2wmRenderer::Inactive()
{
	//if(RProducer::HasEngine())
	//	RProducer::DoneEncoding();
	Log("Inactive\n");
	return CBaseRenderer::Inactive();
}

HRESULT Aud2wmRenderer::SetInterface(IUnknown *p,LPCOLESTR hint)
	{
    char szHint[MAX_PATH];
    if(!WideCharToMultiByte(CP_ACP,0,hint,-1,szHint,MAX_PATH,0,0))
        return ERROR_INVALID_NAME;
	/*
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
	}*/
    return NOERROR;
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

