#ifndef INC_IGRINSPLAYER
#define INC_IGRINSPLAYER


// {2F00D4D6-AB9E-4952-BF54-DB0630C93E5F}
DEFINE_GUID(CLSID_GRiNSPlayer, 
0x2f00d4d6, 0xab9e, 0x4952, 0xbf, 0x54, 0xdb, 0x6, 0x30, 0xc9, 0x3e, 0x5f);

// {698A27F32-35E3-4313-9EA5-9D66B691032E}
DEFINE_GUID(IID_IGRiNSPlayer, 
0x98a27f32, 0x35e3, 0x4313, 0x9e, 0xa5, 0x9d, 0x66, 0xb6, 0x91, 0x3, 0x2e);

interface IGRiNSPlayer : public IUnknown
	{
	virtual HRESULT __stdcall Open(wchar_t *szName)=0;
	virtual HRESULT __stdcall Play()=0;
	virtual HRESULT __stdcall Stop()=0;
	virtual HRESULT __stdcall Pause()=0;
	virtual HRESULT __stdcall OnEvent(wchar_t *wszEvent)=0;	
	virtual HRESULT __stdcall SetAttribute(wchar_t *wszAttr)=0;
	};

#endif
