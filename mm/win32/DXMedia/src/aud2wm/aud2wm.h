
/***********************************************************
Copyright 1991-2000 by Oratrix Development BV, Amsterdam, The Netherlands.

                        All Rights Reserved

******************************************************************/

// aud2wm.ax - A filter for converting audio to windows media using wmf sdk

#ifndef INC_AUD2WM


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
DEFINE_GUID(IID_IWMConverter,
0xbdbc884c, 0xfce, 0x414f, 0x99, 0x41, 0x3, 0x5f, 0x90, 0xe, 0x43, 0xb6);
interface IWMConverter : public IUnknown
	{
	virtual HRESULT __stdcall SetRendererAdviceSink(IRendererAdviceSink *pI) = 0;
	};


// {F19DA5C1-CA68-498d-9F01-7568E4F20C5E}
DEFINE_GUID(CLSID_Aud2wm,
0xf19da5c1, 0xca68, 0x498d, 0x9f, 0x1, 0x75, 0x68, 0xe4, 0xf2, 0xc, 0x5e);



class WMWriter;

class Aud2wmRenderer : 
	public CBaseRenderer,
	public IWMConverter
{
public:
    static CUnknown * WINAPI CreateInstance(LPUNKNOWN pUnk, HRESULT *phr);

    Aud2wmRenderer(LPUNKNOWN pUnk,HRESULT *phr);
    ~Aud2wmRenderer();
    STDMETHODIMP NonDelegatingQueryInterface(REFIID, void **);

    HRESULT BreakConnect();
    HRESULT CheckMediaType(const CMediaType *pmt);
	HRESULT DoRenderSample(IMediaSample *pMediaSample);
    HRESULT SetMediaType(const CMediaType *pmt);
    void OnReceiveFirstSample(IMediaSample *pMediaSample);
    HRESULT Active();
	HRESULT Inactive();


	// Implements IWMConverter
    DECLARE_IUNKNOWN
	HRESULT __stdcall SetRendererAdviceSink(IRendererAdviceSink *pI);
	
protected:
    CMediaType m_mtIn;                  // Source connection media type
	int m_ixsample;
	WMWriter *m_pWMWriter;
	IRendererAdviceSink *m_pAdviceSink;
}; 

#endif

