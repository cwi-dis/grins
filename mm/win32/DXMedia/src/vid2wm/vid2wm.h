#ifndef INC_VID2WM

// {34F6B2C9-16AD-4454-A76D-2EB8EEA06C80}
DEFINE_GUID(IID_IRendererAdviceSink, 
0x34f6b2c9, 0x16ad, 0x4454, 0xa7, 0x6d, 0x2e, 0xb8, 0xee, 0xa0, 0x6c, 0x80);
interface IRendererAdviceSink : public IUnknown
	{
	virtual HRESULT __stdcall OnSetMediaType(const CMediaType *pmt) = 0;
	virtual HRESULT __stdcall OnActive()=0;
	virtual HRESULT __stdcall OnInactive()=0;
	virtual HRESULT __stdcall OnRenderSample(IMediaSample *pMediaSample) = 0;
	};

// {BDBC884C-0FCE-414f-9941-035F900E43B6}
DEFINE_GUID(IID_IWMConverter,
0xbdbc884c, 0xfce, 0x414f, 0x99, 0x41, 0x3, 0x5f, 0x90, 0xe, 0x43, 0xb6);
interface IWMConverter : public IUnknown
	{
	virtual HRESULT __stdcall SetWMWriter(IUnknown *pI) = 0;
	virtual HRESULT __stdcall SetRendererAdviceSink(IRendererAdviceSink *pI) = 0;
	};


class CVideoRenderer;

class CVideoInputPin : public CRendererInputPin
{
    CVideoRenderer *m_pRenderer;        // The renderer that owns us
    CCritSec *m_pInterfaceLock;         // Main filter critical section

public:

    // Constructor

    CVideoInputPin(
        TCHAR *pObjectName,             // Object string description
        CVideoRenderer *pRenderer,      // Used to delegate locking
        CCritSec *pInterfaceLock,       // Main critical section
        HRESULT *phr,                   // OLE failure return code
        LPCWSTR pPinName);              // This pins identification

    // Manage DIBSECTION video allocator
    //STDMETHODIMP GetAllocator(IMemAllocator **ppAllocator);
    //STDMETHODIMP NotifyAllocator(IMemAllocator *pAllocator,BOOL bReadOnly);

}; // CVideoInputPin


// {2E41AE53-E5F4-4209-9D2A-DDE1AB1BB07E}
DEFINE_GUID(CLSID_Vid2wm,
0x2e41ae53, 0xe5f4, 0x4209, 0x9d, 0x2a, 0xdd, 0xe1, 0xab, 0x1b, 0xb0, 0x7e);

class WMWriter;

class CVideoRenderer : 
	public CBaseVideoRenderer, 
	public IWMConverter
{
public:

    // Constructor and destructor
    static CUnknown * WINAPI CreateInstance(LPUNKNOWN, HRESULT *);
    CVideoRenderer(TCHAR *pName,LPUNKNOWN pUnk,HRESULT *phr);
    ~CVideoRenderer();

	void EncodeSample(IMediaSample *pMediaSample);

	HRESULT CopyImage(IMediaSample *pMediaSample,
                                     VIDEOINFOHEADER *pVideoInfo,
                                     LONG *pBufferSize,
                                     BYTE **ppVideoImage,
                                     RECT *pSourceRect);
	HRESULT GetImageHeader(BITMAPINFOHEADER *pbih,
                                     VIDEOINFOHEADER *pVideoInfo,
                                     RECT *pSourceRect);

    DECLARE_IUNKNOWN
    STDMETHODIMP NonDelegatingQueryInterface(REFIID, void **);

    CBasePin *GetPin(int n);

    // Override these from the filter and renderer classes
    void PrepareRender();
    HRESULT Active();
	HRESULT Inactive();

    HRESULT BreakConnect();
    HRESULT CompleteConnect(IPin *pReceivePin);
    HRESULT SetMediaType(const CMediaType *pmt);
    HRESULT CheckMediaType(const CMediaType *pmtIn);
    HRESULT CheckVideoType(const VIDEOINFO *pDisplay,const VIDEOINFO *pInput);
    HRESULT UpdateFormat(VIDEOINFO *pVideoInfo);
    HRESULT DoRenderSample(IMediaSample *pMediaSample);
    void OnReceiveFirstSample(IMediaSample *pMediaSample);

	// Implements IWMConverter
	HRESULT __stdcall  SetWMWriter(IUnknown *p);
	HRESULT __stdcall SetRendererAdviceSink(IRendererAdviceSink *pI);
	
public:

    CImageAllocator m_ImageAllocator;   // Our DIBSECTION allocator
    CVideoInputPin m_InputPin;          // IPin based interfaces
    CImageDisplay m_Display;            // Manages the video display type
    CMediaType m_mtIn;                  // Source connection media type
    SIZE m_VideoSize;                   // Size of the current video stream
	BYTE *m_pVideoImage;
	int m_ixframe;
	DWORD m_lastTimestamp;
	WMWriter *m_pWMWriter;
	ULONG m_sampleSize;
	IRendererAdviceSink *m_pAdviceSink;	
}; 

#endif

