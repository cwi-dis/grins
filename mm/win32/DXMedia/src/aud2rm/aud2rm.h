/***********************************************************
Copyright 1991-1999 by Oratrix Development BV, Amsterdam, The Netherlands.

                        All Rights Reserved

******************************************************************/

// aud2rm.ax - A filter for converting audio to real media through the real producer

DEFINE_GUID(CLSID_Aud2rm,
0xe8d61c45, 0xd313, 0x472a, 0x84, 0x68, 0x2b, 0x1e, 0xd5, 0xb0, 0x5c, 0xab);


class Aud2rmRenderer : public CBaseRenderer
{
public:
    static CUnknown * WINAPI CreateInstance(LPUNKNOWN pUnk, HRESULT *phr);

    Aud2rmRenderer(LPUNKNOWN pUnk,HRESULT *phr);
    ~Aud2rmRenderer();
    STDMETHODIMP NonDelegatingQueryInterface(REFIID, void **);

    HRESULT BreakConnect();
    HRESULT CheckMediaType(const CMediaType *pmt);
    HRESULT DoRenderSample(IMediaSample *pMediaSample);
    void OnReceiveFirstSample(IMediaSample *pMediaSample);
    HRESULT Active();
	HRESULT Inactive();

	void EncodeSample(IMediaSample *pMediaSample);

protected:
	int m_ixsample;

}; 

