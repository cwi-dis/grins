#ifndef INC_DDBLTRV
#define INC_DDBLTRV

#ifdef _WIN32

#ifndef __DDRAW_INCLUDED__
#include <ddraw.h>
#endif

HRESULT InitDDBltRV(IDirectDrawSurface *pI);
HRESULT Blt_RGB32_On_RGB32(UCHAR* pImageBits, DWORD w, DWORD h, IDirectDrawSurface *surf);
HRESULT Blt_RGB24_On_RGB32(UCHAR* pImageBits, DWORD w, DWORD h, IDirectDrawSurface *surf);
HRESULT Blt_YUV420_On_RGB32(UCHAR* pImageBits, DWORD w, DWORD h, IDirectDrawSurface *surf);

#endif // _WIN32

#endif // INC_DDBLTRV

