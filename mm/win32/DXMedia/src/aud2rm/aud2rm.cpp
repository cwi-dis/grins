/***********************************************************
Copyright 1991-1999 by Oratrix Development BV, Amsterdam, The Netherlands.

                        All Rights Reserved

******************************************************************/

// aud2rm.ax - A filter for converting audio to real media through the real producer

#include <streams.h>
#include <initguid.h>
#include "aud2rm.h"

// options
#define LOG_ACTIVITY


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

const AMOVIESETUP_FILTER sudaud2rm =
{
    &CLSID_Aud2rm,               // Filter CLSID
    L"Audio Real Media Converter",// String name
    MERIT_DO_NOT_USE,              // Filter merit
    1,                            // Number of pins
    &sudAudPin                    // Pin details
};


CFactoryTemplate g_Templates[] = {
    { L"Audio Real Media Converter"
    , &CLSID_Aud2rm
    , Aud2rmRenderer::CreateInstance
    , NULL
    , &sudaud2rm },
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


Aud2rmRenderer::Aud2rmRenderer(LPUNKNOWN pUnk,HRESULT *phr) :
    CBaseRenderer(CLSID_Aud2rm, NAME("Audio Real Media Converter"), pUnk, phr)
{
#ifdef LOG_ACTIVITY
	logFile=fopen("audlog.txt","w");
#endif

} 

Aud2rmRenderer::~Aud2rmRenderer()
{
	if(logFile) fclose(logFile);
	m_ixsample=0;
}

CUnknown * WINAPI Aud2rmRenderer::CreateInstance(LPUNKNOWN pUnk, HRESULT *phr)
{
    return new Aud2rmRenderer(pUnk,phr);
} 


STDMETHODIMP
Aud2rmRenderer::NonDelegatingQueryInterface(REFIID riid,void **ppv)
{
    return CBaseRenderer::NonDelegatingQueryInterface(riid,ppv);
} 

HRESULT Aud2rmRenderer::BreakConnect()
{
    return NOERROR;
} 


HRESULT Aud2rmRenderer::CheckMediaType(const CMediaType *pmt)
{
	Log("CheckMediaType\n");
    if (pmt->majortype != MEDIATYPE_Audio) {
	return E_INVALIDARG;
    }
    return NOERROR;
} 

void Aud2rmRenderer::OnReceiveFirstSample(IMediaSample *pMediaSample)
{
	if(m_ixsample==0){
		DoRenderSample(pMediaSample);	
		Log("OnReceiveFirstSample\n");
	}
	m_ixsample=0;

} 

HRESULT Aud2rmRenderer::DoRenderSample(IMediaSample *pMediaSample)
{
	if(logFile)
		{
		char sz[256];
		sprintf(sz,"sample %d size=%d\n",m_ixsample,pMediaSample->GetActualDataLength());
		Log(sz);
		}
	EncodeSample(pMediaSample);
    return NOERROR;
} 

void Aud2rmRenderer::EncodeSample(IMediaSample *pMediaSample)
{
	m_ixsample++;
}

HRESULT Aud2rmRenderer::Active()
{
	Log("Active\n");
   return CBaseRenderer::Active();
} 

HRESULT Aud2rmRenderer::Inactive()
{
	Log("Inactive\n");
	return CBaseRenderer::Inactive();
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

