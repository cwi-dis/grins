#include <windows.h>
#include <wtypes.h>
#include "wmsdk.h"
#include <mmsystem.h>
#include <assert.h>

#include <streams.h>
#include <mtype.h>

#include "wmwriter.h"


WMWriter::WMWriter()
:	m_pIWMWriter(NULL),
	m_pIAudioInputProps(NULL),
	m_pIVideoInputProps(NULL),
	m_bWriting(false)
	{
	}

WMWriter::~WMWriter()
	{
	RELEASE(m_pIAudioInputProps);
	RELEASE(m_pIVideoInputProps);
	RELEASE(m_pIWMWriter);
	}

HRESULT __stdcall WMWriter::SetWMWriter(IUnknown *pI)
	{
	HRESULT hr = pI->QueryInterface(IID_IWMWriter,(void**)&m_pIWMWriter);
	if(FAILED(hr))
		{
		LogError("SetWMWriter",hr);
		return E_NOINTERFACE;
		}
	
    DWORD cInputs;
    hr = m_pIWMWriter->GetInputCount(&cInputs);
    for(DWORD i=0;i<cInputs;i++)
		{
		IWMInputMediaProps* pInputProps = NULL;
        hr = m_pIWMWriter->GetInputProps(i,&pInputProps);
        if(FAILED(hr))
			{
			LogError("GetInputProps",hr);
            return hr;
			}
		GUID guidInputType;
		hr = pInputProps->GetType( &guidInputType);
		if(FAILED(hr))
			{
			LogError("GetType",hr);
            return hr;
			}
		if(guidInputType == WMMEDIATYPE_Audio)
			{
            m_pIAudioInputProps = pInputProps;
            m_dwAudioInputNum = i;
			}
		else if( guidInputType == WMMEDIATYPE_Video )
			{
            m_pIVideoInputProps = pInputProps;
            m_dwVideoInputNum = i;
			}
		}
	return S_OK;
	}

HRESULT __stdcall WMWriter::SetAudioFormat(const CMediaType *pmt)
	{
	if(!m_pIAudioInputProps)
		{
		Log("Unexpected SetAudioFormat");
		return E_UNEXPECTED;
		}
	WM_MEDIA_TYPE mt;
	WM_MEDIA_TYPE *pType = &mt;
    pType->majortype = *pmt->Type();
    pType->subtype =  *pmt->Subtype();
    pType->bFixedSizeSamples = pmt->IsFixedSize();
    pType->bTemporalCompression = pmt->IsTemporalCompressed();
    pType->lSampleSize = pmt->GetSampleSize();
    pType->formattype = *pmt->FormatType();
    pType->pUnk = NULL;
    pType->cbFormat = pmt->FormatLength();
	pType->pbFormat = pmt->Format();
	HRESULT hr = m_pIAudioInputProps->SetMediaType(pType);
	if(FAILED(hr))
		{
		LogError("SetMediaType",hr);
		return hr;
		}
	hr = m_pIWMWriter->SetInputProps(m_dwAudioInputNum, m_pIAudioInputProps);
	if(FAILED(hr))
		{
		LogError("SetMediaType",hr);
		return hr;
		}
	return S_OK;
	}

HRESULT __stdcall WMWriter::SetVideoFormat(const CMediaType *pmt)
	{
	if(!m_pIVideoInputProps)
		{
		Log("Unexpected SetVideoFormat");
		return E_UNEXPECTED;
		}
	WM_MEDIA_TYPE mt;
	WM_MEDIA_TYPE *pType = &mt;
    pType->majortype = *pmt->Type();
    pType->subtype =  *pmt->Subtype();
    pType->bFixedSizeSamples = pmt->IsFixedSize();
    pType->bTemporalCompression = TRUE; // pmt->IsTemporalCompressed();
    pType->lSampleSize = pmt->GetSampleSize();
    pType->formattype = *pmt->FormatType();
    pType->pUnk = NULL;
    pType->cbFormat = pmt->FormatLength();
	pType->pbFormat = pmt->Format();
	HRESULT hr = m_pIVideoInputProps->SetMediaType(pType);
	if(FAILED(hr))
		{
		LogError("SetMediaType",hr);
		return hr;
		}
	hr = m_pIWMWriter->SetInputProps(m_dwVideoInputNum, m_pIVideoInputProps);
	if(FAILED(hr))
		{
		LogError("SetMediaType",hr);
		return hr;
		}
	return S_OK;
	}

HRESULT __stdcall WMWriter::BeginWriting()
	{
	if(!m_pIWMWriter) return E_UNEXPECTED;
	HRESULT hr = m_pIWMWriter->BeginWriting();
	if(FAILED(hr))
		LogError("BeginWriting",hr);
	else m_bWriting = true;
	return hr;
	}

HRESULT __stdcall WMWriter::EndWriting()
	{
	if(!m_pIWMWriter || !m_bWriting)
		{
		Log("Unexpected EndWriting");
		return E_UNEXPECTED;
		}
	HRESULT hr = m_pIWMWriter->EndWriting();
	if(FAILED(hr))
		LogError("EndWriting",hr);
	m_bWriting = false;
	return hr;
	}

HRESULT __stdcall WMWriter::Flush()
	{
	if(!m_pIWMWriter || !m_bWriting)
		{
		Log("Unexpected Flush");
		return E_UNEXPECTED;
		}
	HRESULT hr = m_pIWMWriter->Flush();
	if(FAILED(hr))
		LogError("Flush",hr);
	return hr;
	}
HRESULT __stdcall WMWriter::WriteAudioSample(BYTE *pBuffer,DWORD dwSampleSize, REFERENCE_TIME cnsec)
	{
	if(!m_pIWMWriter || !m_bWriting) 
		{
		Log("WriteAudioSample while not writing");
		return E_UNEXPECTED;
		}
	
	INSSBuffer *pSample=NULL;
	HRESULT hr = m_pIWMWriter->AllocateSample(dwSampleSize,&pSample);
	if(FAILED(hr)) 
		{
		LogError("AllocateSample",hr);
		return hr;
		}
	BYTE *pbsBuffer;
	DWORD cbBuffer;
	hr = pSample->GetBufferAndLength(&pbsBuffer,&cbBuffer);
	if(FAILED(hr)) 
		{
		LogError("GetBufferAndLength",hr);
		pSample->Release();
		return hr;
		}
	CopyMemory(pbsBuffer,pBuffer,cbBuffer<dwSampleSize?cbBuffer:dwSampleSize);
	
	DWORD dwFlags = 0; // WM_SF_CLEANPOINT;
	hr = m_pIWMWriter->WriteSample(m_dwAudioInputNum,cnsec,dwFlags,pSample);
	pSample->Release();
	if(FAILED(hr)) LogError("WriteSample",hr);
	return S_OK;
	}

HRESULT __stdcall WMWriter::WriteVideoSample(BYTE *pBuffer,DWORD dwSampleSize, REFERENCE_TIME cnsec)
	{	
	if(!m_pIWMWriter || !m_bWriting) 
		{
		Log("Unexpected WriteVideoSample");
		return E_UNEXPECTED;
		}
	
	INSSBuffer *pSample=NULL;
	HRESULT hr = m_pIWMWriter->AllocateSample(dwSampleSize,&pSample);
	if(FAILED(hr)) 
		{
		LogError("AllocateSample",hr);
		return hr;
		}
	BYTE *pbsBuffer;
	DWORD cbBuffer;
	hr = pSample->GetBufferAndLength(&pbsBuffer,&cbBuffer);
	if(FAILED(hr)) 
		{
		LogError("GetBufferAndLength",hr);
		pSample->Release();
		return hr;
		}
	if(cbBuffer!=dwSampleSize) Log("cbBuffer!=dwSampleSize");
	CopyMemory(pbsBuffer,pBuffer,cbBuffer<dwSampleSize?cbBuffer:dwSampleSize);

	DWORD dwFlags = 0;//WM_SF_CLEANPOINT;
	hr = m_pIWMWriter->WriteSample(m_dwVideoInputNum,cnsec,dwFlags,pSample);
	pSample->Release();

	if(FAILED(hr)) LogError("WriteSample",hr);

	return S_OK;
	}


void WMWriter::LogError(const char *funcname, HRESULT hr)
	{
	char* pszmsg;
	::FormatMessage( 
		 FORMAT_MESSAGE_ALLOCATE_BUFFER | FORMAT_MESSAGE_FROM_SYSTEM,
		 NULL,
		 hr,
		 MAKELANGID(LANG_NEUTRAL, SUBLANG_DEFAULT), // Default language
		 (LPTSTR) &pszmsg,
		 0,
		 NULL 
		);
	Log("%s failed, error = %s", funcname, pszmsg);
	LocalFree(pszmsg);
	}
