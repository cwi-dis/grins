
/***********************************************************
Copyright 1991-2000 by Oratrix Development BV, Amsterdam, The Netherlands.

                        All Rights Reserved

******************************************************************/

#include "Std.h"


//////////////////////////////////////
// this source file has no meaning unless we windowless
#ifdef USE_WINDOWLESS_SITE

// this is a win32 only source file
#ifdef _WIN32



#pragma comment (lib,"ddraw.lib")
#include <ddraw.h>	


// XXX: default init only valid for 24 and 32 bpp
static WORD numREDbits=8, numGREENbits=8, numBLUEbits=8;
static WORD loREDbit=16, loGREENbit=8, loBLUEbit=0;
static PALETTEENTRY paletteEntry[256];

static WORD LowBitPos(DWORD dword)
	{
	DWORD test=1;
	for (WORD i=0;i<32;i++)
		{
		if ( dword & test )
			return i;
		test<<=1;
		}
	return 0;
	}
static WORD HighBitPos(DWORD dword)
	{
	DWORD test=1;
	test<<=31;
	for (WORD i=0;i<32;i++)
		{
		if ( dword & test )
			return (WORD)(31-i);
		test>>=1;
		}
	return 0;
	}

HRESULT InitDDBltRV(IDirectDrawSurface *pI)
	{
	DDPIXELFORMAT format;
	ZeroMemory(&format,sizeof(format));
	format.dwSize=sizeof(format);
	HRESULT hr = pI->GetPixelFormat(&format);
	if (FAILED(hr)) return hr;

	loREDbit = LowBitPos(format.dwRBitMask);
	WORD hiREDbit = HighBitPos(format.dwRBitMask);
	numREDbits=(WORD)(hiREDbit-loREDbit+1);

	loGREENbit = LowBitPos( format.dwGBitMask );
	WORD hiGREENbit = HighBitPos( format.dwGBitMask );
	numGREENbits=(WORD)(hiGREENbit-loGREENbit+1);

	loBLUEbit  = LowBitPos( format.dwBBitMask );
	WORD hiBLUEbit  = HighBitPos( format.dwBBitMask );
	numBLUEbits=(WORD)(hiBLUEbit-loBLUEbit+1);

	if(format.dwRGBBitCount==8)
		{
		HDC hdc = GetDC(NULL);
		GetSystemPaletteEntries(hdc, 0, 256, paletteEntry);
		ReleaseDC(NULL, hdc);
		}
	return S_OK;
	}	


HRESULT Blt_RGB32_On_RGB32(UCHAR* pImageBits, DWORD w, DWORD h, IDirectDrawSurface *surf)
	{
	DDSURFACEDESC desc;
	ZeroMemory(&desc, sizeof(desc));
	desc.dwSize=sizeof(desc);
	
	HRESULT hr;
	hr=surf->Lock(0,&desc, DDLOCK_WAIT, 0);
	if(hr!=DD_OK) return hr;
	
	for(int row=h-1;row>=0;row--)
		{
		RGBQUAD* surfpixel=(RGBQUAD*)((BYTE*)desc.lpSurface+row*desc.lPitch);
		for (DWORD col=0;col<w;col++)
			{
			DWORD b = *pImageBits++;
			DWORD g = *pImageBits++;
			DWORD r = *pImageBits++;
			*pImageBits++;
			
			r = r << loREDbit;
			g = g << loGREENbit;
			b = b << loBLUEbit;
			DWORD* data = (DWORD*)surfpixel;
			*data = r|g|b;
			
			surfpixel++;
			}
		}
	surf->Unlock(0);
	return hr;
	}

HRESULT Blt_RGB24_On_RGB32(UCHAR* pImageBits, DWORD w, DWORD h, IDirectDrawSurface *surf)
	{
	DDSURFACEDESC desc;
	ZeroMemory(&desc, sizeof(desc));
	desc.dwSize=sizeof(desc);
	
	HRESULT hr;
	hr=surf->Lock(0,&desc, DDLOCK_WAIT, 0);
	if(hr!=DD_OK) return hr;
	
	for(int row=h-1;row>=0;row--)
		{
		RGBQUAD* surfpixel=(RGBQUAD*)((BYTE*)desc.lpSurface+row*desc.lPitch);
		for (DWORD col=0;col<w;col++)
			{
			DWORD b = *pImageBits++;
			DWORD g = *pImageBits++;
			DWORD r = *pImageBits++;
			
			r = r << loREDbit;
			g = g << loGREENbit;
			b = b << loBLUEbit;
			DWORD* data = (DWORD*)surfpixel;
			*data = r|g|b;
			
			surfpixel++;
			}
		}
	surf->Unlock(0);
	return hr;
	}


// XXX: blt only Y plain for now (luma only image)
HRESULT Blt_YUV420_On_RGB32(UCHAR* pImageBits, DWORD w, DWORD h, IDirectDrawSurface *surf)
	{
	DDSURFACEDESC desc;
	ZeroMemory(&desc, sizeof(desc));
	desc.dwSize=sizeof(desc);
	
	HRESULT hr;
	hr=surf->Lock(0,&desc, DDLOCK_WAIT, 0);
	if(hr!=DD_OK) return hr;
	
	for(DWORD row=0;row<h;row++)
		{
		RGBQUAD* surfpixel=(RGBQUAD*)((BYTE*)desc.lpSurface+row*desc.lPitch);
		for (DWORD col=0;col<w;col++)
			{
			DWORD y = *pImageBits++;
			
			DWORD r = y;
			DWORD g = y;
			DWORD b = y;
			
			r = r << loREDbit;
			g = g << loGREENbit;
			b = b << loBLUEbit;
			DWORD* data = (DWORD*)surfpixel;
			*data = r|g|b;
			
			surfpixel++;
			}
		}
	surf->Unlock(0);
	return hr;
	}



#endif // _WIN32
#endif // USE_WINDOWLESS_SITE

///////////////////////////////////////
