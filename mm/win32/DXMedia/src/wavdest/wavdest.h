//==========================================================================;
//
//  THIS CODE AND INFORMATION IS PROVIDED "AS IS" WITHOUT WARRANTY OF ANY
//  KIND, EITHER EXPRESSED OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE
//  IMPLIED WARRANTIES OF MERCHANTABILITY AND/OR FITNESS FOR A PARTICULAR
//  PURPOSE.
//
//  Copyright (c) 1992 - 1998  Microsoft Corporation.  All Rights Reserved.
//
//--------------------------------------------------------------------------;

/******************************Module*Header*******************************\
* Module Name: WavDest.h
*
* Sample filter for writing WAV files
*
*
\**************************************************************************/
#pragma warning(disable: 4097 4511 4512 4514 4705)

class CWavDestOutputPin : public CTransformOutputPin
{
public:
    CWavDestOutputPin(CTransformFilter *pFilter, HRESULT * phr);

    STDMETHODIMP EnumMediaTypes( IEnumMediaTypes **ppEnum );
    HRESULT CheckMediaType(const CMediaType* pmt);
};

class CWavDestFilter : public CTransformFilter
{

public:

    DECLARE_IUNKNOWN;
  
    CWavDestFilter(LPUNKNOWN pUnk, HRESULT *pHr);
    ~CWavDestFilter();
    static CUnknown *CreateInstance(LPUNKNOWN punk, HRESULT *pHr);

    HRESULT Transform(IMediaSample *pIn, IMediaSample *pOut);

    HRESULT CheckInputType(const CMediaType* mtIn) ;
    HRESULT CheckTransform(const CMediaType *mtIn,const CMediaType *mtOut);
    HRESULT GetMediaType(int iPosition, CMediaType *pMediaType) ;

    HRESULT DecideBufferSize(IMemAllocator *pAlloc,
                             ALLOCATOR_PROPERTIES *pProperties);

    HRESULT StartStreaming();
    HRESULT StopStreaming();

    HRESULT CompleteConnect(PIN_DIRECTION direction,IPin *pReceivePin) { return S_OK; }

private:

    HRESULT Copy(IMediaSample *pSource, IMediaSample *pDest) const;
    HRESULT Transform(IMediaSample *pMediaSample);
    HRESULT Transform(AM_MEDIA_TYPE *pType, const signed char ContrastLevel) const;

    ULONG m_cbWavData;
    ULONG m_cbHeader;
};
