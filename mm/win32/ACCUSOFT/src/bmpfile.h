

#define WIDTHBYTES(bits)    (((bits) + 31) / 32 * 4)
#define BMP_HEADERSIZE (3 * 2 + 4 * 12)
#define BMP_BYTESPERLINE (width, bits) ((((width) * (bits) + 31) / 32) * 4)
#define BMP_PIXELSIZE(width, height, bits) (((((width) * (bits) + 31) / 32) * 4) * height)

#ifndef INC_MFCSTRING
#include "mfcstring.h"
#endif

class BMPFile
{
public:
	// parameters
	String m_errorText;
	DWORD m_bytesRead;

public:

	// operations

	BMPFile();

	BYTE * LoadBMP(String fileName, UINT *width, UINT *height);

	void SaveBMP(String fileName,		// output path
							BYTE * buf,				// RGB buffer
							UINT width,				// size
							UINT height);
	BOOL BGRFromRGB(BYTE *buf, UINT widthPix, UINT height);
	BOOL VertFlipBuf(BYTE  * inbuf, 
					   UINT widthBytes, 
					   UINT height);

	BYTE *SaveBMP2Mem(BYTE * buf,UINT width,UINT height,DWORD *pdwSize);

	void SaveBMP(String fileName, 			// output path
							 BYTE * colormappedbuffer,	// one BYTE per pixel colomapped image
							 UINT width,
							 UINT height,
 							 int bitsperpixel,			// 1, 4, 8
							 int colors,				// number of colors (number of RGBQUADs)
							 RGBQUAD *colormap);			// array of RGBQUADs 

};