
/***********************************************************
Copyright 1991-2000 by Oratrix Development BV, Amsterdam, The Netherlands.

                        All Rights Reserved

******************************************************************/

// aud2wm.ax - A filter for converting audio to windows media using wmf sdk

#include <streams.h>
#include <initguid.h>
#include "aud2wm.h"

#include <wtypes.h>
#include "wmsdk.h"
#include <mmsystem.h>
#include <assert.h>


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


#pragma warning(disable:4355)


Aud2wmRenderer::Aud2wmRenderer(LPUNKNOWN pUnk,HRESULT *phr) :
    CBaseRenderer(CLSID_Aud2wm, NAME("Audio Windows Media Converter"), pUnk, phr),
	m_pAdviceSink(NULL)
{
} 

Aud2wmRenderer::~Aud2wmRenderer()
{
	if(m_pAdviceSink) m_pAdviceSink->Release();
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
	if(m_pAdviceSink) m_pAdviceSink->OnSetMediaType(pmt);
    return NOERROR;
}

void Aud2wmRenderer::OnReceiveFirstSample(IMediaSample *pMediaSample)
{
} 

HRESULT Aud2wmRenderer::DoRenderSample(IMediaSample *pMediaSample)
{
	if(m_pAdviceSink) m_pAdviceSink->OnRenderSample(pMediaSample);
    return NOERROR;
}


HRESULT Aud2wmRenderer::Active()
{
	if(m_pAdviceSink) m_pAdviceSink->OnActive();
	return CBaseRenderer::Active();
} 

HRESULT Aud2wmRenderer::Inactive()
{
	if(m_pAdviceSink) m_pAdviceSink->OnInactive();
	return CBaseRenderer::Inactive();
}

HRESULT Aud2wmRenderer::SetRendererAdviceSink(IRendererAdviceSink *pI)
{
	if(m_pAdviceSink) m_pAdviceSink->Release();
	m_pAdviceSink = pI;
	m_pAdviceSink->AddRef();
	return S_OK;
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

