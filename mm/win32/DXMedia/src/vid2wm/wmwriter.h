#ifndef INC_WMWRITER
#define INC_WMWRITER

class WMWriter
	{
	public:
	WMWriter();
	~WMWriter();
	HRESULT __stdcall SetWMWriter(IUnknown *pI);
	HRESULT __stdcall SetAudioInputProps(DWORD dwInputNum,IUnknown *pI);
	HRESULT __stdcall SetVideoInputProps(DWORD dwInputNum,IUnknown *pI);

	HRESULT __stdcall SetAudioFormat(WAVEFORMATEX *pWFX);
	HRESULT __stdcall SetVideoFormat(WMVIDEOINFOHEADER *pVIH);
	
	HRESULT __stdcall BeginWriting();
	HRESULT __stdcall EndWriting();

	HRESULT __stdcall WriteAudioSample(BYTE *pBuffer,DWORD dwSampleSize, DWORD msec);
	HRESULT __stdcall WriteVideoSample(BYTE *pBuffer,DWORD dwSampleSize, DWORD msec);

	private:
	void LogError(const char *funcname, HRESULT hr);
	
	IWMWriter *m_pIWMWriter;
	
	DWORD m_dwAudioInputNum;
	IWMInputMediaProps *m_pIAudioInputProps;
	
	DWORD m_dwVideoInputNum;
	IWMInputMediaProps *m_pIVideoInputProps;
	
	bool m_bWriting;
	};

extern void Log(LPCTSTR lpszFormat, ...);
#define RELEASE(x) if(x) x->Release();x=NULL


#endif

