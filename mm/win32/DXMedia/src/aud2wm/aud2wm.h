
/***********************************************************
Copyright 1991-2000 by Oratrix Development BV, Amsterdam, The Netherlands.

                        All Rights Reserved

******************************************************************/

// aud2wm.ax - A filter for converting audio to windows media using wmf sdk

#ifndef INC_AUD2WM

// {BDBC884C-0FCE-414f-9941-035F900E43B6}
DEFINE_GUID(IID_IWMConverter,
0xbdbc884c, 0xfce, 0x414f, 0x99, 0x41, 0x3, 0x5f, 0x90, 0xe, 0x43, 0xb6);
struct IWMConverter : public IUnknown
	{
	virtual HRESULT __stdcall SetInterface(IUnknown *p,LPCOLESTR hint)=0;
	};

// {F19DA5C1-CA68-498d-9F01-7568E4F20C5E}
DEFINE_GUID(CLSID_Aud2wm,
0xf19da5c1, 0xca68, 0x498d, 0x9f, 0x1, 0x75, 0x68, 0xe4, 0xf2, 0xc, 0x5e);


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
    HRESULT SetMediaType(const CMediaType *pmt);
    HRESULT DoRenderSample(IMediaSample *pMediaSample);
    void OnReceiveFirstSample(IMediaSample *pMediaSample);
    HRESULT Active();
	HRESULT Inactive();

	void EncodeSample(IMediaSample *pMediaSample);

	// Implements IWMConverter
    DECLARE_IUNKNOWN
	STDMETHODIMP SetInterface(IUnknown *p,LPCOLESTR hint);

protected:
    CMediaType m_mtIn;                  // Source connection media type
	int m_ixsample;

}; 

#endif

