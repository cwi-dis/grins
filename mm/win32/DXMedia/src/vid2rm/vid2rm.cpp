/***********************************************************
Copyright 1991-1999 by Oratrix Development BV, Amsterdam, The Netherlands.

                        All Rights Reserved

******************************************************************/

// vid2rm.ax - A filter for converting video to real media through the real producer

#include <windows.h>
#include <commdlg.h>
#include <streams.h>
#include <initguid.h>
#include "vid2rmuids.h"
#include "vid2rm.h"


// Setup data


const AMOVIESETUP_MEDIATYPE sudPinTypes =
{
    &MEDIATYPE_Video,           // Major type
    &MEDIASUBTYPE_NULL          // Minor type
};


const AMOVIESETUP_PIN sudPins[] =
{	
	{
    L"Input",                   // Pin string name
    FALSE,                      // Is it rendered
    FALSE,                      // Is it an output
    FALSE,                      // Allowed none
    FALSE,                      // Likewise many
    &CLSID_NULL,                // Connects to filter
    L"Output",                  // Connects to pin
    1,                          // Number of types
    &sudPinTypes                // Pin information
	}
};

const AMOVIESETUP_FILTER sudVid2rm =
{
    &CLSID_Vid2rm,                // Filter CLSID
    L"Video Real Media Converter", // String name
    MERIT_DO_NOT_USE,           // Filter merit
    2,                          // Number pins
    sudPins                     // Pin details
};


//
//  Object creation stuff
//
CFactoryTemplate g_Templates[]= {
    L"vid2rm", &CLSID_Vid2rm, CVid2rm::CreateInstance, NULL, &sudVid2rm
};
int g_cTemplates = 1;


// Constructor

CVid2rmFilter::CVid2rmFilter(CVid2rm *pVid2rm,
                         LPUNKNOWN pUnk,
                         CCritSec *pLock,
                         HRESULT *phr) :
    CBaseFilter(NAME("vid2rm filter"), pUnk, pLock, CLSID_Vid2rm),
    m_pVid2rm(pVid2rm)
{
}


//
// GetPin
//
CBasePin * CVid2rmFilter::GetPin(int n)
{
    if (n == 0 || n==1) {
        return m_pVid2rm->m_pPin;
    } else {
        return NULL;
    }
}


//
// GetPinCount
//
int CVid2rmFilter::GetPinCount()
{
    return 1;
}


//
// Stop
//
// Overriden to close the Vid2rm file
//
STDMETHODIMP CVid2rmFilter::Stop()
{
    CAutoLock cObjectLock(m_pLock);
    m_pVid2rm->CloseFile();
    return CBaseFilter::Stop();
}


//
// Pause
//
// Overriden to open the Vid2rm file
//
STDMETHODIMP CVid2rmFilter::Pause()
{
    CAutoLock cObjectLock(m_pLock);
    m_pVid2rm->OpenFile();
    return CBaseFilter::Pause();
}


//
// Run
//
// Overriden to open the Vid2rm file
//
STDMETHODIMP CVid2rmFilter::Run(REFERENCE_TIME tStart)
{
    CAutoLock cObjectLock(m_pLock);
    m_pVid2rm->OpenFile();
    return CBaseFilter::Run(tStart);
}


//
//  Definition of CVid2rmInputPin
//
CVid2rmInputPin::CVid2rmInputPin(CVid2rm *pVid2rm,
                             LPUNKNOWN pUnk,
                             CBaseFilter *pFilter,
                             CCritSec *pLock,
                             CCritSec *pReceiveLock,
                             HRESULT *phr) :

    CRenderedInputPin(NAME("CVid2rmInputPin"),
                  pFilter,                   // Filter
                  pLock,                     // Locking
                  phr,                       // Return code
                  L"Input"),                 // Pin name
    m_pReceiveLock(pReceiveLock),
    m_pVid2rm(pVid2rm),
    m_tLast(0)
{
}


//
// CheckMediaType
//
// Check if the pin can support this specific proposed type and format
//
HRESULT CVid2rmInputPin::CheckMediaType(const CMediaType *)
{
    return S_OK;
}


//
// BreakConnect
//
// Break a connection
//
HRESULT CVid2rmInputPin::BreakConnect()
{
    if (m_pVid2rm->m_pPosition != NULL) {
        m_pVid2rm->m_pPosition->ForceRefresh();
    }
    return CRenderedInputPin::BreakConnect();
}


//
// ReceiveCanBlock
//
// We don't hold up source threads on Receive
//
STDMETHODIMP CVid2rmInputPin::ReceiveCanBlock()
{
    return S_FALSE;
}


//
// Receive
//
// Do something with this media sample
//
STDMETHODIMP CVid2rmInputPin::Receive(IMediaSample *pSample)
{
    CAutoLock lock(m_pReceiveLock);
    PBYTE pbData;

    // Has the filter been stopped yet
    if (m_pVid2rm->m_hFile == INVALID_HANDLE_VALUE) {
        return NOERROR;
    }

    REFERENCE_TIME tStart, tStop;
    pSample->GetTime(&tStart, &tStop);
    DbgLog((LOG_TRACE, 1, TEXT("tStart(%s), tStop(%s), Diff(%d ms), Bytes(%d)"),
           (LPCTSTR) CDisp(tStart),
           (LPCTSTR) CDisp(tStop),
           (LONG)((tStart - m_tLast) / 10000),
           pSample->GetActualDataLength()));

    m_tLast = tStart;

    // Copy the data to the file

    HRESULT hr = pSample->GetPointer(&pbData);
    if (FAILED(hr)) {
        return hr;
    }
	WriteStringInfo(pSample);
	return NOERROR;
    //return m_pVid2rm->Write(pbData,pSample->GetActualDataLength());
}


//
// Vid2rmStringInfo
//
// Write to the file as text form
//
HRESULT CVid2rmInputPin::WriteStringInfo(IMediaSample *pSample)
{
    TCHAR FileString[256];
    PBYTE pbData;

    // Retrieve the time stamps from this sample

    REFERENCE_TIME tStart, tStop;
    pSample->GetTime(&tStart, &tStop);
    m_tLast = tStart;

    // Write the sample time stamps out

    wsprintf(FileString,"\r\nRenderer received sample (%dms)",timeGetTime());
    m_pVid2rm->WriteString(FileString);
    wsprintf(FileString,"   Start time (%s)",CDisp(tStart));
    m_pVid2rm->WriteString(FileString);
    wsprintf(FileString,"   End time (%s)",CDisp(tStop));
    m_pVid2rm->WriteString(FileString);

    // Display the media times for this sample

    HRESULT hr = pSample->GetMediaTime(&tStart, &tStop);
    if (hr == NOERROR) {
        wsprintf(FileString,"   Start media time (%s)",CDisp(tStart));
        m_pVid2rm->WriteString(FileString);
        wsprintf(FileString,"   End media time (%s)",CDisp(tStop));
        m_pVid2rm->WriteString(FileString);
    }

    // Is this a sync point sample

    hr = pSample->IsSyncPoint();
    wsprintf(FileString,"   Sync point (%d)",(hr == S_OK));
    m_pVid2rm->WriteString(FileString);

    // Is this a preroll sample

    hr = pSample->IsPreroll();
    wsprintf(FileString,"   Preroll (%d)",(hr == S_OK));
    m_pVid2rm->WriteString(FileString);

    // Is this a discontinuity sample

    hr = pSample->IsDiscontinuity();
    wsprintf(FileString,"   Discontinuity (%d)",(hr == S_OK));
    m_pVid2rm->WriteString(FileString);

    // Write the actual data length

    LONG DataLength = pSample->GetActualDataLength();
    wsprintf(FileString,"   Actual data length (%d)",DataLength);
    m_pVid2rm->WriteString(FileString);

    // Does the sample have a type change aboard

    AM_MEDIA_TYPE *pMediaType;
    pSample->GetMediaType(&pMediaType);
    wsprintf(FileString,"   Type changed (%d)",
        (pMediaType ? TRUE : FALSE));
    m_pVid2rm->WriteString(FileString);
    DeleteMediaType(pMediaType);

    // Copy the data to the file

    hr = pSample->GetPointer(&pbData);
    if (FAILED(hr)) {
        return hr;
    }

    // Write each complete line out in BYTES_PER_LINES groups
	/*
	TCHAR TempString[256];
    for (int Loop = 0;Loop < (DataLength / BYTES_PER_LINE);Loop++) {
        wsprintf(FileString,FIRST_HALF_LINE,pbData[0],pbData[1],pbData[2],
                 pbData[3],pbData[4],pbData[5],pbData[6],
                    pbData[7],pbData[8],pbData[9]);
        wsprintf(TempString,SECOND_HALF_LINE,pbData[10],pbData[11],pbData[12],
                 pbData[13],pbData[14],pbData[15],pbData[16],
                    pbData[17],pbData[18],pbData[19]);
        lstrcat(FileString,TempString);
        m_pVid2rm->WriteString(FileString);
        pbData += BYTES_PER_LINE;
    }

    // Write the last few bytes out afterwards

    wsprintf(FileString,"   ");
    for (Loop = 0;Loop < (DataLength % BYTES_PER_LINE);Loop++) {
        wsprintf(TempString,"%x ",pbData[Loop]);
        lstrcat(FileString,TempString);
    }
    m_pVid2rm->WriteString(FileString);
	*/
    return NOERROR;
}


//
// EndOfStream
//
STDMETHODIMP CVid2rmInputPin::EndOfStream(void)
{
    CAutoLock lock(m_pReceiveLock);
    return CRenderedInputPin::EndOfStream();

} // EndOfStream


//
// NewSegment
//
// Called when we are seeked
//
STDMETHODIMP CVid2rmInputPin::NewSegment(REFERENCE_TIME tStart,
                                       REFERENCE_TIME tStop,
                                       double dRate)
{
    m_tLast = 0;
    return S_OK;

} // NewSegment


//
//  CVid2rm class
//
CVid2rm::CVid2rm(LPUNKNOWN pUnk, HRESULT *phr) :
    CUnknown(NAME("CVid2rm"), pUnk),
    m_pFilter(NULL),
    m_pPin(NULL),
    m_pPosition(NULL),
    m_hFile(INVALID_HANDLE_VALUE),
    m_pFileName(0)
{
    m_pFilter = new CVid2rmFilter(this, GetOwner(), &m_Lock, phr);
    if (m_pFilter == NULL) {
        *phr = E_OUTOFMEMORY;
        return;
    }

    m_pPin = new CVid2rmInputPin(this,GetOwner(),
                               m_pFilter,
                               &m_Lock,
                               &m_ReceiveLock,
                               phr);
    if (m_pPin == NULL) {
        *phr = E_OUTOFMEMORY;
        return;
    }
}


//
// SetFileName
//
// Implemented for IFileSinkFilter support
//
STDMETHODIMP CVid2rm::SetFileName(LPCOLESTR pszFileName,const AM_MEDIA_TYPE *pmt)
{
    // Is this a valid filename supplied

    CheckPointer(pszFileName,E_POINTER);
    if(wcslen(pszFileName) > MAX_PATH)
        return ERROR_FILENAME_EXCED_RANGE;

    // Take a copy of the filename

    m_pFileName = new WCHAR[1+lstrlenW(pszFileName)];
    if (m_pFileName == 0)
        return E_OUTOFMEMORY;
    lstrcpyW(m_pFileName,pszFileName);

    // Create the file then close it

    HRESULT hr = OpenFile();
    CloseFile();
    return hr;

} // SetFileName


//
// GetCurFile
//
// Implemented for IFileSinkFilter support
//
STDMETHODIMP CVid2rm::GetCurFile(LPOLESTR * ppszFileName,AM_MEDIA_TYPE *pmt)
{
    CheckPointer(ppszFileName, E_POINTER);
    *ppszFileName = NULL;
    if (m_pFileName != NULL) {
        *ppszFileName = (LPOLESTR)
        QzTaskMemAlloc(sizeof(WCHAR) * (1+lstrlenW(m_pFileName)));
        if (*ppszFileName != NULL) {
            lstrcpyW(*ppszFileName, m_pFileName);
        }
    }

    if(pmt) {
        ZeroMemory(pmt, sizeof(*pmt));
        pmt->majortype = MEDIATYPE_NULL;
        pmt->subtype = MEDIASUBTYPE_NULL;
    }
    return S_OK;

} // GetCurFile


// Destructor

CVid2rm::~CVid2rm()
{
    CloseFile();
    delete m_pPin;
    delete m_pFilter;
    delete m_pPosition;
    delete m_pFileName;
}


//
// CreateInstance
//
// Provide the way for COM to create a Vid2rm filter
//
CUnknown * WINAPI CVid2rm::CreateInstance(LPUNKNOWN punk, HRESULT *phr)
{
    CVid2rm *pNewObject = new CVid2rm(punk, phr);
    if (pNewObject == NULL) {
        *phr = E_OUTOFMEMORY;
    }
    return pNewObject;

} // CreateInstance


//
// NonDelegatingQueryInterface
//
// Override this to say what interfaces we support where
//
STDMETHODIMP CVid2rm::NonDelegatingQueryInterface(REFIID riid, void ** ppv)
{
    CheckPointer(ppv,E_POINTER);
    CAutoLock lock(&m_Lock);

    // Do we have this interface

    if (riid == IID_IFileSinkFilter) {
        return GetInterface((IFileSinkFilter *) this, ppv);
    } else if (riid == IID_IBaseFilter || riid == IID_IMediaFilter || riid == IID_IPersist) {
	return m_pFilter->NonDelegatingQueryInterface(riid, ppv);
    } else if (riid == IID_IMediaPosition || riid == IID_IMediaSeeking) {
        if (m_pPosition == NULL) {

            HRESULT hr = S_OK;
            m_pPosition = new CPosPassThru(NAME("Vid2rm Pass Through"),
                                           (IUnknown *) GetOwner(),
                                           (HRESULT *) &hr, m_pPin);
            if (m_pPosition == NULL) {
                return E_OUTOFMEMORY;
            }

            if (FAILED(hr)) {
                delete m_pPosition;
                m_pPosition = NULL;
                return hr;
            }
        }
        return m_pPosition->NonDelegatingQueryInterface(riid, ppv);
    } else {
	return CUnknown::NonDelegatingQueryInterface(riid, ppv);
    }

} // NonDelegatingQueryInterface


//
// OpenFile
//
// Opens the file ready for Vid2rming
//
HRESULT CVid2rm::OpenFile()
{
    TCHAR *pFileName = NULL;

    // Is the file already opened
    if (m_hFile != INVALID_HANDLE_VALUE) {
        return NOERROR;
    }

    // Has a filename been set yet
    if (m_pFileName == NULL) {
        return ERROR_INVALID_NAME;
    }

    // Convert the UNICODE filename if necessary

#if defined(WIN32) && !defined(UNICODE)
    char convert[MAX_PATH];
    if(!WideCharToMultiByte(CP_ACP,0,m_pFileName,-1,convert,MAX_PATH,0,0))
        return ERROR_INVALID_NAME;
    pFileName = convert;
#else
    pFileName = m_pFileName;
#endif

    // Try to open the file

    m_hFile = CreateFile((LPCTSTR) pFileName,   // The filename
                         GENERIC_WRITE,         // File access
                         (DWORD) 0,             // Share access
                         NULL,                  // Security
                         CREATE_ALWAYS,         // Open flags
                         (DWORD) 0,             // More flags
                         NULL);                 // Template

    if (m_hFile == INVALID_HANDLE_VALUE) {
        DWORD dwErr = GetLastError();
        return HRESULT_FROM_WIN32(dwErr);
    }
    return S_OK;

} // Open


//
// CloseFile
//
// Closes any Vid2rm file we have opened
//
HRESULT CVid2rm::CloseFile()
{
    if (m_hFile == INVALID_HANDLE_VALUE) {
        return NOERROR;
    }

    CloseHandle(m_hFile);
    m_hFile = INVALID_HANDLE_VALUE;
    return NOERROR;

} // Open


//
// Write
//
// Write stuff to the file
//
HRESULT CVid2rm::Write(PBYTE pbData,LONG lData)
{
    DWORD dwWritten;

    if (!WriteFile(m_hFile,(PVOID)pbData,(DWORD)lData,&dwWritten,NULL)) {
        DWORD dwErr = GetLastError();
        return HRESULT_FROM_WIN32(dwErr);
    }
    return S_OK;
}


//
// WriteString
//
// Writes the given string into the file
//
void CVid2rm::WriteString(TCHAR *pString)
{
    DWORD dwWritten = lstrlen(pString);
    const TCHAR *pEndOfLine = "\r\n";

    WriteFile((HANDLE) m_hFile,
              (PVOID) pString,
              (DWORD) dwWritten,
              &dwWritten, NULL);

    dwWritten = lstrlen(pEndOfLine);
    WriteFile((HANDLE) m_hFile,
              (PVOID) pEndOfLine,
              (DWORD) dwWritten,
              &dwWritten, NULL);

} // WriteString


//
// DllRegisterSever
//
// Handle the registration of this filter
//
STDAPI DllRegisterServer()
{
    return AMovieDllRegisterServer2( TRUE );

} // DllRegisterServer


//
// DllUnregisterServer
//
STDAPI DllUnregisterServer()
{
    return AMovieDllRegisterServer2( FALSE );

} // DllUnregisterServer
