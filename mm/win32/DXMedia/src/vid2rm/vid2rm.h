#ifndef INC_VID2RM

DEFINE_GUID(IID_IRealConverter,
0xe8d61c44, 0xd313, 0x472a, 0x84, 0x68, 0x2b, 0x1e, 0xd5, 0xb0, 0x5c, 0xab);
struct IRealConverter : public IUnknown
	{
	virtual HRESULT __stdcall SetInterface(IUnknown *p,LPCOLESTR hint)=0;
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


DEFINE_GUID(CLSID_Vid2rm,
0xe8d61c43, 0xd313, 0x472a, 0x84, 0x68, 0x2b, 0x1e, 0xd5, 0xb0, 0x5c, 0xab);

class CVideoRenderer : 
	public CBaseVideoRenderer, 
	public IRealConverter
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

	// Implements IRealConverter
	STDMETHODIMP SetInterface(IUnknown *p,LPCOLESTR hint);

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

public:

    CImageAllocator m_ImageAllocator;   // Our DIBSECTION allocator
    CVideoInputPin m_InputPin;          // IPin based interfaces
    CImageDisplay m_Display;            // Manages the video display type
    CMediaType m_mtIn;                  // Source connection media type
    SIZE m_VideoSize;                   // Size of the current video stream
	BYTE *m_pVideoImage;
	int m_ixframe;
	DWORD m_lastTimestamp;
}; 

#endif

