#ifndef INC_RCONVERT
#define INC_RCONVERT

#include <objbase.h>

DEFINE_GUID(IID_IRealConverter,
0xe8d61c44, 0xd313, 0x472a, 0x84, 0x68, 0x2b, 0x1e, 0xd5, 0xb0, 0x5c, 0xab);

struct IRealConverter : public IUnknown
	{
	virtual HRESULT __stdcall SetInterface(IUnknown *p,LPCOLESTR hint)=0;
	};

#endif

