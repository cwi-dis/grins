#ifndef INC_VID2RM

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


class CVideoRenderer : 
	public CBaseVideoRenderer, 
	public IFileSinkFilter
{
public:

    // Constructor and destructor

    static CUnknown * WINAPI CreateInstance(LPUNKNOWN, HRESULT *);
    CVideoRenderer(TCHAR *pName,LPUNKNOWN pUnk,HRESULT *phr);
    ~CVideoRenderer();

	void SlowRender(IMediaSample *pMediaSample);
	HRESULT CopyImage(IMediaSample *pMediaSample,
                                     VIDEOINFOHEADER *pVideoInfo,
                                     LONG *pBufferSize,
                                     BYTE **ppVideoImage,
                                     RECT *pSourceRect);

    // Implement the ISpecifyPropertyPages interface

    DECLARE_IUNKNOWN
    STDMETHODIMP NonDelegatingQueryInterface(REFIID, void **);
    //STDMETHODIMP GetPages(CAUUID *pPages);

    // Implements the IFileSinkFilter interface
    STDMETHODIMP SetFileName(LPCOLESTR pszFileName,const AM_MEDIA_TYPE *pmt);
    STDMETHODIMP GetCurFile(LPOLESTR * ppszFileName,AM_MEDIA_TYPE *pmt);

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
    LPOLESTR m_pFileName;           // The filename where we Vid2rm to
	int m_ixframe;
}; 

#endif

