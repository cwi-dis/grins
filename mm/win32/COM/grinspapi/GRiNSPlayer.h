#ifndef INC_GRINSPLAYER
#define INC_GRINSPLAYER

#ifndef INC_IGRINSPlayer
#include "IGRiNSPlayer.h"      
#endif

class GRiNSPlayer : 
	public IGRiNSPlayer,
	public ComInterfaceProvider<GRiNSPlayer,&CLSID_GRiNSPlayer>
	{
	public:
	GRiNSPlayer();
	~GRiNSPlayer();

	// IGRiNSPlayer
	virtual HRESULT __stdcall Open(wchar_t *szName);
	virtual HRESULT __stdcall Play();
	virtual HRESULT __stdcall Stop();
	virtual HRESULT __stdcall Pause();
	virtual HRESULT __stdcall OnEvent(wchar_t *wszEvent);	
	virtual HRESULT __stdcall SetAttribute(wchar_t *wszAttr);
	};

#endif

