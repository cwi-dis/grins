#ifndef INC_VID2RM

class CVid2rmInputPin;
class CVid2rm;
class CVid2rmFilter;

// Main filter object

class CVid2rmFilter : public CBaseFilter
{
    CVid2rm * const m_pVid2rm;

public:

    // Constructor
    CVid2rmFilter(CVid2rm *pVid2rm,
                LPUNKNOWN pUnk,
                CCritSec *pLock,
                HRESULT *phr);
	~CVid2rmFilter();
    // Pin enumeration
    CBasePin * GetPin(int n);
    int GetPinCount();

    // Open and close the file as necessary
    STDMETHODIMP Run(REFERENCE_TIME tStart);
    STDMETHODIMP Pause();
    STDMETHODIMP Stop();


};


//  Pin object

class CVid2rmInputPin : public CRenderedInputPin
{
    CVid2rm    * const m_pVid2rm;           // Main renderer object
    CCritSec * const m_pReceiveLock;    // Sample critical section
    REFERENCE_TIME m_tLast;             // Last sample receive time

public:

    CVid2rmInputPin(CVid2rm *pVid2rm,
                  LPUNKNOWN pUnk,
                  CBaseFilter *pFilter,
                  CCritSec *pLock,
                  CCritSec *pReceiveLock,
                  HRESULT *phr);

    // Do something with this media sample
    STDMETHODIMP Receive(IMediaSample *pSample);
    STDMETHODIMP EndOfStream(void);
    STDMETHODIMP ReceiveCanBlock();
    HRESULT WriteStringInfo(IMediaSample *pSample);

    // Check if the pin can support this specific proposed type and format
    HRESULT CheckMediaType(const CMediaType *);
	HRESULT SetMediaType(const CMediaType *pmt);

    // Break connection
    HRESULT BreakConnect();

    // Track NewSegment
    STDMETHODIMP NewSegment(REFERENCE_TIME tStart,
                            REFERENCE_TIME tStop,
                            double dRate);
	CMediaType m_mtIn;
};


//  CVid2rm object which has filter and pin members

class CVid2rm : public CUnknown, public IFileSinkFilter
{
    friend class CVid2rmFilter;
    friend class CVid2rmInputPin;

    CVid2rmFilter *m_pFilter;         // Methods for filter interfaces
    CVid2rmInputPin *m_pPin;          // A simple rendered input pin
    CCritSec m_Lock;                // Main renderer critical section
    CCritSec m_ReceiveLock;         // Sublock for received samples
    CPosPassThru *m_pPosition;      // Renderer position controls
    HANDLE m_hFile;                 // Handle to file for Vid2rming
    LPOLESTR m_pFileName;           // The filename where we Vid2rm to

public:

    DECLARE_IUNKNOWN

    CVid2rm(LPUNKNOWN pUnk, HRESULT *phr);
    ~CVid2rm();

    static CUnknown * WINAPI CreateInstance(LPUNKNOWN punk, HRESULT *phr);

    // Write data streams to a file
    void WriteString(TCHAR *pString);
    HRESULT Write(PBYTE pbData,LONG lData);

    // Implements the IFileSinkFilter interface
    STDMETHODIMP SetFileName(LPCOLESTR pszFileName,const AM_MEDIA_TYPE *pmt);
    STDMETHODIMP GetCurFile(LPOLESTR * ppszFileName,AM_MEDIA_TYPE *pmt);

private:

    // Overriden to say what interfaces we support where
    STDMETHODIMP NonDelegatingQueryInterface(REFIID riid, void ** ppv);

    // Open and write to the file
    HRESULT OpenFile();
    HRESULT CloseFile();
};

// debug
#define BYTES_PER_LINE 20
#define FIRST_HALF_LINE "   %2x %2x %2x %2x %2x %2x %2x %2x %2x %2x"
#define SECOND_HALF_LINE " %2x %2x %2x %2x %2x %2x %2x %2x %2x %2x"

#endif

