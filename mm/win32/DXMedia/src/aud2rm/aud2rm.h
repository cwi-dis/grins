/***********************************************************
Copyright 1991-1999 by Oratrix Development BV, Amsterdam, The Netherlands.

                        All Rights Reserved

******************************************************************/

// aud2rm.ax - A filter for converting audio to real media through the real producer

#ifndef INC_AUD2RM

DEFINE_GUID(IID_IRealConverter,
0xe8d61c44, 0xd313, 0x472a, 0x84, 0x68, 0x2b, 0x1e, 0xd5, 0xb0, 0x5c, 0xab);
struct IRealConverter : public IUnknown
	{
	virtual HRESULT __stdcall SetInterface(IUnknown *p,LPCOLESTR hint)=0;
	};


DEFINE_GUID(CLSID_Aud2rm,
0xe8d61c45, 0xd313, 0x472a, 0x84, 0x68, 0x2b, 0x1e, 0xd5, 0xb0, 0x5c, 0xab);


class Aud2rmRenderer : 
	public CBaseRenderer,
	public IRealConverter
{
public:
    static CUnknown * WINAPI CreateInstance(LPUNKNOWN pUnk, HRESULT *phr);

    Aud2rmRenderer(LPUNKNOWN pUnk,HRESULT *phr);
    ~Aud2rmRenderer();
    STDMETHODIMP NonDelegatingQueryInterface(REFIID, void **);

    HRESULT BreakConnect();
    HRESULT CheckMediaType(const CMediaType *pmt);
    HRESULT SetMediaType(const CMediaType *pmt);
    HRESULT DoRenderSample(IMediaSample *pMediaSample);
    void OnReceiveFirstSample(IMediaSample *pMediaSample);
    HRESULT Active();
	HRESULT Inactive();

	void EncodeSample(IMediaSample *pMediaSample);

	// Implements IRealConverter
    DECLARE_IUNKNOWN
	STDMETHODIMP SetInterface(IUnknown *p,LPCOLESTR hint);

protected:
    CMediaType m_mtIn;                  // Source connection media type
	int m_ixsample;

}; 

#endif

