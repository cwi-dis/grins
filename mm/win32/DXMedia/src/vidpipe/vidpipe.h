#ifndef INC_VIDPIPE

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


class CVideoPipe;

class CVideoInputPin : public CRendererInputPin
{
    CVideoPipe *m_pRenderer;        // The renderer that owns us
    CCritSec *m_pInterfaceLock;         // Main filter critical section

public:

    // Constructor

    CVideoInputPin(
        TCHAR *pObjectName,             // Object string description
        CVideoPipe *pRenderer,			// Used to delegate locking
        CCritSec *pInterfaceLock,       // Main critical section
        HRESULT *phr,                   // OLE failure return code
        LPCWSTR pPinName);              // This pins identification

    // Manage DIBSECTION video allocator
    //STDMETHODIMP GetAllocator(IMemAllocator **ppAllocator);
    //STDMETHODIMP NotifyAllocator(IMemAllocator *pAllocator,BOOL bReadOnly);

}; // CVideoInputPin


// {788B79BD-3340-4893-9C4A-224BB133C3B8}
DEFINE_GUID(CLSID_VideoPipe,
0x788b79bd, 0x3340, 0x4893, 0x9c, 0x4a, 0x22, 0x4b, 0xb1, 0x33, 0xc3, 0xb8);


class CVideoPipe : 
	public CBaseVideoRenderer, 
	public IPipe
{
public:

    // Constructor and destructor
    static CUnknown * WINAPI CreateInstance(LPUNKNOWN, HRESULT *);
    CVideoPipe(TCHAR *pName,LPUNKNOWN pUnk,HRESULT *phr);
    ~CVideoPipe();

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

	// Implements IPipe
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
	ULONG m_sampleSize;
	IRendererAdviceSink *m_pAdviceSink;	
}; 

#endif

