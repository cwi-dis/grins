
/***********************************************************
Copyright 1991-2001 by Oratrix Development BV, Amsterdam, The Netherlands.

                        All Rights Reserved

******************************************************************/

// audpipe.ax - A filter for converting audio

#ifndef INC_AUDPIPE


// {34F6B2C9-16AD-4454-A76D-2EB8EEA06C80}
DEFINE_GUID(IID_IRendererAdviceSink, 
0x34f6b2c9, 0x16ad, 0x4454, 0xa7, 0x6d, 0x2e, 0xb8, 0xee, 0xa0, 0x6c, 0x80);
interface IRendererAdviceSink : public IUnknown
	{
	virtual HRESULT __stdcall OnSetMediaType(const CMediaType *pmt) = 0;
	virtual HRESULT __stdcall OnActive() = 0;
	virtual HRESULT __stdcall OnInactive() = 0;
	virtual HRESULT __stdcall OnRenderSample(IMediaSample *pMediaSample) = 0; 
	};

// {BDBC884C-0FCE-414f-9941-035F900E43B6}
DEFINE_GUID(IID_IPipe,
0xbdbc884c, 0xfce, 0x414f, 0x99, 0x41, 0x3, 0x5f, 0x90, 0xe, 0x43, 0xb6);
interface IPipe : public IUnknown
	{
	virtual HRESULT __stdcall SetRendererAdviceSink(IRendererAdviceSink *pI) = 0;
	};

// {EE3807F2-D4F0-4af8-A1DB-A236425C62CC}
DEFINE_GUID(CLSID_AudioPipe,
0xee3807f2, 0xd4f0, 0x4af8, 0xa1, 0xdb, 0xa2, 0x36, 0x42, 0x5c, 0x62, 0xcc);


class CAudioPipe : 
	public CBaseRenderer,
	public IPipe
{
public:
    static CUnknown * WINAPI CreateInstance(LPUNKNOWN pUnk, HRESULT *phr);

    CAudioPipe(LPUNKNOWN pUnk,HRESULT *phr);
    ~CAudioPipe();
    STDMETHODIMP NonDelegatingQueryInterface(REFIID, void **);

    HRESULT BreakConnect();
    HRESULT CheckMediaType(const CMediaType *pmt);
	HRESULT DoRenderSample(IMediaSample *pMediaSample);
    HRESULT SetMediaType(const CMediaType *pmt);
    void OnReceiveFirstSample(IMediaSample *pMediaSample);
    HRESULT Active();
	HRESULT Inactive();


	// Implements IPipe
    DECLARE_IUNKNOWN
	HRESULT __stdcall SetRendererAdviceSink(IRendererAdviceSink *pI);
	
protected:
    CMediaType m_mtIn;                  // Source connection media type
	int m_ixsample;
	IRendererAdviceSink *m_pAdviceSink;
}; 

#endif

