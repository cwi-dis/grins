#include <windows.h>
#include <wtypes.h>
#include "wmsdk.h"
#include <mmsystem.h>
#include <assert.h>

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
	return S_OK;
	}

HRESULT __stdcall WMWriter::SetAudioInputProps(DWORD dwInputNum, IUnknown *pI)
	{
	m_dwAudioInputNum = dwInputNum;	
	HRESULT hr = pI->QueryInterface(IID_IWMInputMediaProps,(void**)&m_pIAudioInputProps);
	if(FAILED(hr))
		{
		LogError("SetAudioInputProps",hr);
		m_pIAudioInputProps = NULL;
		return hr;
		}
	return S_OK;
	}

HRESULT __stdcall WMWriter::SetVideoInputProps(DWORD dwInputNum, IUnknown *pI)
	{
	m_dwVideoInputNum = dwInputNum;
	HRESULT hr = pI->QueryInterface(IID_IWMInputMediaProps,(void**)&m_pIAudioInputProps);
	if(FAILED(hr))
		{
		LogError("SetAudioInputProps",hr);
		m_pIAudioInputProps = NULL;
		return hr;
		}
	return S_OK;
	}

HRESULT __stdcall WMWriter::SetAudioFormat(WAVEFORMATEX *pWFX)
	{
	if(!m_pIAudioInputProps) return E_UNEXPECTED;
	DWORD cbType = 512;
	char buf[512];
	WM_MEDIA_TYPE *pType=(WM_MEDIA_TYPE *)buf;
	HRESULT hr = m_pIAudioInputProps->GetMediaType(pType,&cbType);
	if(FAILED(hr))
		{
		LogError("GetMediaType",hr);
		return hr;
		}
    pType->majortype = WMMEDIATYPE_Audio;
    pType->subtype = WMMEDIASUBTYPE_PCM;
    pType->bFixedSizeSamples=TRUE;
    pType->bTemporalCompression=FALSE;
    pType->lSampleSize = pWFX->nBlockAlign;
    pType->formattype = WMFORMAT_WaveFormatEx;
    pType->pUnk = NULL;
    pType->cbFormat = sizeof(WAVEFORMATEX)+pWFX->cbSize;
	pType->pbFormat = (BYTE*)pWFX;
	hr = m_pIAudioInputProps->SetMediaType(pType);
	delete [] (BYTE*)pType;
	if(FAILED(hr))
		{
		LogError("SetMediaType",hr);
		return hr;
		}
	hr = m_pIWMWriter->SetInputProps(m_dwAudioInputNum,m_pIAudioInputProps);
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
	if(!m_pIWMWriter) return E_UNEXPECTED;
	HRESULT hr = m_pIWMWriter->EndWriting();
	if(FAILED(hr))
		LogError("EndWriting",hr);
	else m_bWriting = false;
	return hr;
	}

HRESULT __stdcall WMWriter::WriteAudioSample(BYTE *pBuffer,DWORD dwSampleSize, DWORD msec)
	{
	if(!m_pIWMWriter || !m_bWriting) return E_UNEXPECTED;
	
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
		return hr;
		}
	CopyMemory(pbsBuffer,pBuffer,cbBuffer<dwSampleSize?cbBuffer:dwSampleSize);
	
	QWORD cnsec = (QWORD)msec*10000;
	hr = m_pIWMWriter->WriteSample(m_dwAudioInputNum,cnsec,0,pSample);
	if(FAILED(hr)) LogError("WriteSample",hr);
	return S_OK;
	}

HRESULT __stdcall WMWriter::WriteVideoSample(BYTE *pBuffer,DWORD dwSampleSize, DWORD msec)
	{
	if(!m_pIWMWriter || !m_bWriting) return E_UNEXPECTED;
	
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
		return hr;
		}
	CopyMemory(pbsBuffer,pBuffer,cbBuffer<dwSampleSize?cbBuffer:dwSampleSize);
	
	QWORD cnsec = (QWORD)msec*10000;
	hr = m_pIWMWriter->WriteSample(m_dwVideoInputNum,cnsec,0,pSample);
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
